#!/usr/bin/env python3
"""Run the acceptance suite and assemble an offline submission bundle."""
from __future__ import annotations
import datetime as dt
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import sys
import tempfile
import time
import tomllib
import zipfile

ROOT = Path(__file__).resolve().parents[1]
REPORTS = (
    'host-tests.json', 'cli-tests.json', 'file-fault-tests.json',
    'distribution-tests.json', 'consumer-tests.json', 'numeric-tests.json',
    'crosscheck.json', 'measured-files.json', 'browser-tests.json',
    'numeric-browser-tests.json', 'package-check.json',
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_identity() -> str:
    if not (ROOT/'.git').exists():
        return 'local-uncommitted'
    proc = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=ROOT, check=True,
                          capture_output=True, text=True, encoding='utf-8')
    return proc.stdout.strip()


def ensure_clean_checkout() -> None:
    if not (ROOT/'.git').exists():
        return
    proc = subprocess.run(['git', 'status', '--porcelain', '--untracked-files=normal'],
                          cwd=ROOT, check=True, capture_output=True,
                          text=True, encoding='utf-8')
    if proc.stdout.strip():
        raise RuntimeError('Commit or move working-tree changes before preparing a versioned submission:\n'
                           + proc.stdout)


def verified_reports() -> dict:
    data = {}
    for name in REPORTS:
        report = json.loads((ROOT/'verification'/name).read_text(encoding='utf-8'))
        if report.get('status') != 'passed':
            raise RuntimeError('Verification did not pass: ' + name)
        data[name] = report
    for name in ('browser-tests.json', 'numeric-browser-tests.json'):
        if data[name].get('mode') != 'file':
            raise RuntimeError('Submission requires actual file-mode browser checks: ' + name)
    return data


def main() -> int:
    config = tomllib.loads((ROOT/'moon.mod').read_text(encoding='utf-8'))
    version = config['version']
    if not re.fullmatch(r'[0-9A-Za-z][0-9A-Za-z.+-]*', version):
        raise ValueError('Invalid package version')
    output = ROOT/'_build/submission'
    output.mkdir(parents=True, exist_ok=True)
    archive = output/f'SParamKit-{version}-submission.zip'
    archive.unlink(missing_ok=True)  # Never leave an old successful bundle after a failed run.
    status_file = output/'submission-check.json'
    summary = {'status': 'failed', 'version': version,
               'started_utc': dt.datetime.now(dt.timezone.utc).isoformat(), 'steps': []}
    try:
        ensure_clean_checkout()
        identity = git_identity()
        summary['source_commit'] = identity
        env = dict(os.environ, GITHUB_SHA=identity)
        # A local injected document or external URL cannot satisfy acceptance.
        for key in ('TEST_CONTENT', 'TEST_URL'):
            env.pop(key, None)
        verification = ROOT/'verification'; verification.mkdir(exist_ok=True)
        for name in (*REPORTS, 'ui-desktop.png', 'ui-mobile.png'):
            (verification/name).unlink(missing_ok=True)
        with tempfile.TemporaryDirectory(prefix='sparamkit-submission-') as temporary:
            stage = Path(temporary)/f'SParamKit-{version}'
            logs = stage/'reports/logs'; logs.mkdir(parents=True)

            def run(label: str, command: list[str]) -> None:
                start = time.monotonic()
                path = logs/f'{label}.log'
                print(f'[{label}] {" ".join(command)}', flush=True)
                with path.open('w', encoding='utf-8', newline='\n') as handle:
                    handle.write('$ ' + ' '.join(command) + '\n'); handle.flush()
                    proc = subprocess.run(command, cwd=ROOT, env=env, stdout=handle,
                                          stderr=subprocess.STDOUT, timeout=600, check=False)
                record = {'name': label, 'command': command, 'exit_code': proc.returncode,
                          'seconds': round(time.monotonic()-start, 3),
                          'log': 'reports/logs/' + path.name, 'sha256': digest(path)}
                summary['steps'].append(record)
                if proc.returncode:
                    # Keep the actual failing command output outside the temporary directory.
                    shutil.copyfile(path, output/'failed-step.log')
                    raise RuntimeError(f'{label} failed (exit {proc.returncode}); see _build/submission/failed-step.log')

            run('toolchain', ['moon', 'version', '--all'])
            run('format', ['moon', 'fmt', '--check'])
            for target in ('js', 'wasm-gc'):
                for verb in ('check', 'build', 'test'):
                    run(f'{verb}-{target}', ['moon', verb, '--target', target, '--deny-warn'])
                run(f'example-{target}', ['moon', 'run', 'cmd/main', '--target', target, '--deny-warn'])
            run('bridge', ['moon', 'build', 'bridge', '--target', 'js', '--release', '--deny-warn'])
            run('workbench', [sys.executable, 'tools/build_web.py'])
            for label, script in (
                ('host', 'test_host.py'), ('distribution', 'test_distribution.py'),
                ('consumer', 'test_consumer.py'), ('numeric', 'test_numeric.py'),
                ('scikit-rf', 'crosscheck.py'), ('public-files', 'test_measured.py'),
                ('browser', 'test_browser.py'), ('numeric-browser', 'test_numeric_browser.py'),
                ('source-package', 'check_package.py'),
            ):
                run(label, [sys.executable, 'tools/' + script])
            reports = verified_reports()
            package = reports['package-check.json']
            source_archive = ROOT/'_build/publish'/package['archive']
            if digest(source_archive) != package['sha256']:
                raise RuntimeError('Source archive changed after verification')
            # Check all source members against this checkout, not a previous archive.
            with zipfile.ZipFile(source_archive) as source:
                for name in source.namelist():
                    path = PurePosixPath(name)
                    if path.is_absolute() or '..' in path.parts or '\\' in name:
                        raise RuntimeError('Unsafe source archive path')
                    if source.read(name) != (ROOT/name).read_bytes():
                        raise RuntimeError('Source changed during verification: ' + name)
            ensure_clean_checkout()
            run('runtime-integrity', [sys.executable, 'dist/verify_download.py'])
            tool_manifest = json.loads((ROOT/'dist/manifest.json').read_text(encoding='utf-8'))
            if tool_manifest['source_commit'] != identity or tool_manifest['version'] != version:
                raise RuntimeError('Runtime version or commit does not match the submission')
            # Copy only named outputs. No proposal, local attachments or arbitrary report files.
            shutil.copytree(ROOT/'dist', stage/'workbench')
            with zipfile.ZipFile(source_archive) as source:
                source.extractall(stage/'source')
            shutil.copyfile(ROOT/'LICENSE', stage/'LICENSE')
            for name in REPORTS:
                shutil.copyfile(verification/name, stage/'reports'/name)
            for name in ('ui-desktop.png', 'ui-mobile.png'):
                shutil.copyfile(verification/name, stage/'reports'/name)
            summary.update(status='passed', completed_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
                           source_archive_sha256=package['sha256'],
                           core_sha256=tool_manifest['sha256']['core.cjs'],
                           reports=list(REPORTS), browser_mode='file')
            (stage/'reports/submission-check.json').write_text(
                json.dumps(summary, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
            readme = f'''# SParamKit {version} 验收包

直接打开 `workbench/index.html` 即可使用离线工作台，不需要安装开发环境。

| 目录 / 文件 | 内容 |
| --- | --- |
| `workbench/` | 离线 HTML、文件 CLI、合成样例和完整性清单 |
| `source/` | 已在新目录中重建并测试的完整 MoonBit 源码 |
| `source/docs/SUBMISSION.md` | 申报功能与实现、演示、测试的对应关系 |
| `source/docs/ACCEPTANCE.md` | 评审演示顺序和完整复现命令 |
| `reports/` | 本次执行的 JSON 报告、命令日志和界面截图 |
| `source/README.md` | 仓库项目说明 |

## 建议演示顺序

打开工作台，切换双端口 / 单端口样例，导入文件并读数，查看错误定位，然后导出 CSV 和 JSON。详细步骤见 `source/docs/ACCEPTANCE.md`。

## 核对与重建

在解压目录执行 `python verify_download.py` 可核对整个提交包。需要修改和重建时，进入 `source/`，按 `docs/ACCEPTANCE.md` 准备开发依赖并执行 `python tools/prepare_submission.py`。

版本：`{version}`。源码标识：`{identity}`。

各报告对应本次执行；跨平台历史测试记录保存在源码包的 `verification/` 中。本包由自动化验收流程生成，主办方审核在赛事提交渠道进行。
'''
            (stage/'README.md').write_text(readme, encoding='utf-8', newline='\n')
            shutil.copyfile(ROOT/'tools/verify_download.py', stage/'verify_download.py')
            manifest = {'schema_version': 1, 'project': 'SParamKit', 'version': version,
                        'source_commit': identity, 'kind': 'submission',
                        'sha256': {p.relative_to(stage).as_posix(): digest(p)
                                   for p in sorted(stage.rglob('*')) if p.is_file()}}
            (stage/'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
            subprocess.run([sys.executable, str(stage/'verify_download.py')], check=True,
                           env=env, capture_output=True, timeout=30)
            with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as bundle:
                for path in sorted(stage.rglob('*')):
                    if path.is_file():
                        bundle.write(path, path.relative_to(stage.parent).as_posix())
            summary['archive'] = archive.name
            summary['archive_sha256'] = digest(archive)
            # Verify the delivered archive after extraction, not only the staging folder.
            with tempfile.TemporaryDirectory(prefix='sparamkit-delivered-') as unpack:
                with zipfile.ZipFile(archive) as bundle:
                    bundle.extractall(unpack)
                subprocess.run([sys.executable, str(Path(unpack)/stage.name/'verify_download.py')],
                               check=True, env=env, capture_output=True, timeout=30)
            summary['delivered_archive_verified'] = True
    except Exception as exc:
        summary.update(status='failed', error=f'{type(exc).__name__}: {exc}')
        archive.unlink(missing_ok=True)
    status_file.write_text(json.dumps(summary, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in summary.items() if k != 'steps'}, ensure_ascii=False, indent=2))
    return 0 if summary['status'] == 'passed' else 1


if __name__ == '__main__':
    sys.exit(main())
