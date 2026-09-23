#!/usr/bin/env python3
"""Package, inspect and rebuild in an isolated directory. Does not publish."""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
import subprocess
import sys
import tempfile
import tomllib
import zipfile

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'verification'
OUT.mkdir(exist_ok=True)
REPORT: dict = {'status': 'failed', 'commands': []}

def run(args: list[str], cwd: Path) -> str:
    proc = subprocess.run(args, cwd=cwd, text=True, encoding='utf-8', errors='replace',
                          capture_output=True, timeout=180, check=False)
    REPORT['commands'].append({'command': args, 'isolated': cwd != ROOT,
                               'exit_code': proc.returncode,
                               'stdout': proc.stdout, 'stderr': proc.stderr})
    if proc.returncode:
        raise RuntimeError(f'{args}: exit {proc.returncode}\n{proc.stderr}\n{proc.stdout}')
    return proc.stdout

def main() -> int:
    try:
        run(['moon', 'fmt', '--check'], ROOT)
        api_paths = [ROOT / 'pkg.generated.mbti', ROOT / 'cmd/main/pkg.generated.mbti']
        before = {str(p.relative_to(ROOT)): p.read_bytes() for p in api_paths}
        run(['moon', 'info', '--target', 'wasm-gc'], ROOT)
        if any((ROOT / p).read_bytes() != data for p, data in before.items()):
            raise RuntimeError('Generated public API is stale; run moon info and commit changes')
        config = tomllib.loads((ROOT / 'moon.mod').read_text(encoding='utf-8'))
        stem = config['name'].replace('/', '-') + '-' + config['version'] + '.zip'
        archive = ROOT / '_build' / 'publish' / stem
        if archive.exists():
            archive.unlink()  # A stale archive must never satisfy this test.
        run(['moon', 'package', '--list'], ROOT)
        if not archive.is_file():
            raise RuntimeError('moon package did not produce the expected fresh archive')
        archive_hash = hashlib.sha256(archive.read_bytes()).hexdigest()
        with zipfile.ZipFile(archive) as z:
            names = z.namelist()
            if len(names) != len(set(names)):
                raise RuntimeError('Duplicate archive entry')
            required = {'.moonignore', '.gitignore', '.gitattributes', 'moon.mod', 'moon.pkg', 'LICENSE', 'README.md', 'parser.mbt',
                        'pkg.generated.mbti', 'compatibility_wbtest.mbt', 'api_test.mbt',
                        'docs/COMPATIBILITY.md', 'docs/TEST_DATA.md',
                        'tools/build_web.py', 'tools/cli.cjs', 'tools/test_cli.py',
                        'tools/prepare_submission.py', 'tools/test_distribution.py', 'docs/SUBMISSION.md',
                        'tools/test_consumer.py', 'tools/test_file_faults.py', 'tools/test_numeric.py', 'numeric_wbtest.mbt', 'tools/test_numeric_browser.py', 'web/index.html'}
            if not required.issubset(names):
                raise RuntimeError('Package missing required files: ' + str(required - set(names)))
            for info in z.infolist():
                p = PurePosixPath(info.filename)
                if p.is_absolute() or '..' in p.parts or '\\' in info.filename:
                    raise RuntimeError('Unsafe archive path: ' + info.filename)
                if stat.S_ISLNK(info.external_attr >> 16):
                    raise RuntimeError('Unexpected symlink in source package')
                if any(x in {'.git', '.github', '_build', 'target', 'dist', '.mooncakes', '__pycache__'} for x in p.parts):
                    raise RuntimeError('Build/cache content leaked into package: ' + info.filename)
                if any(x.startswith('.env') or x.endswith(('.pem', '.key')) for x in p.parts):
                    raise RuntimeError('Potential credential path in package: ' + info.filename)
                if p.suffix in {'.log', '.png'} or p.name in {'crosscheck.json', 'measured-files.json', 'browser-tests.json', 'package-check.json', 'host-tests.json', 'cli-tests.json', 'consumer-tests.json', 'numeric-tests.json', 'numeric-browser-tests.json', 'file-fault-tests.json', 'distribution-tests.json'}:
                    raise RuntimeError('Generated verification output leaked into source package')
            if z.read('LICENSE') != (ROOT / 'LICENSE').read_bytes():
                raise RuntimeError('LICENSE differs in package')
            with tempfile.TemporaryDirectory(prefix='sparamkit-package-') as tmp:
                directory = Path(tmp)
                z.extractall(directory)
                run(['moon', 'fmt', '--check'], directory)
                for target in ('js', 'wasm-gc'):
                    for verb in ('check', 'build', 'test'):
                        run(['moon', verb, '--target', target, '--deny-warn'], directory)
                run(['moon', 'build', 'bridge', '--target', 'js', '--release', '--deny-warn'], directory)
                run([sys.executable, 'tools/build_web.py'], directory)
                example = json.loads(run(['node', 'dist/cli.cjs', 'dist/samples/synthetic_notch.s2p', '--format', 'json'], directory))
                if not example.get('ok') or example.get('sample_count') != 291:
                    raise RuntimeError('Packaged CLI produced unexpected sample output')
                run([sys.executable, 'tools/test_distribution.py'], directory)
                REPORT['distribution'] = json.loads((directory / 'verification/distribution-tests.json').read_text(encoding='utf-8'))
                run([sys.executable, 'tools/test_cli.py'], directory)
                run([sys.executable, 'tools/test_file_faults.py'], directory)
                REPORT['file_faults'] = json.loads((directory / 'verification/file-fault-tests.json').read_text(encoding='utf-8'))
                run([sys.executable, 'tools/test_consumer.py'], directory)
                run([sys.executable, 'tools/test_numeric.py'], directory)
                REPORT['numeric'] = json.loads((directory / 'verification/numeric-tests.json').read_text(encoding='utf-8'))
                REPORT['cli'] = json.loads((directory / 'verification/cli-tests.json').read_text(encoding='utf-8'))
                REPORT['external_consumer'] = json.loads((directory / 'verification/consumer-tests.json').read_text(encoding='utf-8'))
                run(['moon', 'package', '--list'], directory)
                with zipfile.ZipFile(directory / '_build/publish' / stem) as repacked:
                    if set(repacked.namelist()) != set(names):
                        raise RuntimeError('Repackaged source file list differs after isolated tests')
                    if any(repacked.read(name) != z.read(name) for name in names):
                        raise RuntimeError('Repackaged source bytes differ after isolated tests')
                REPORT['repackaged_source_matches'] = True
        REPORT.update(status='passed', archive=stem, sha256=archive_hash,
                      files=len(names), fresh_extraction_rebuilt=True,
                      publication='not attempted')
    except Exception as exc:
        REPORT['error'] = f'{type(exc).__name__}: {exc}'
    (OUT / 'package-check.json').write_text(json.dumps(REPORT, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in REPORT.items() if k != 'commands'}, indent=2))
    return 0 if REPORT['status'] == 'passed' else 1

if __name__ == '__main__':
    sys.exit(main())
