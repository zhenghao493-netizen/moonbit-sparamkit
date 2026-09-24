#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Verify the exact standalone #188 mail patch in a disposable upstream clone."""
from __future__ import annotations
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
SUMMARY = re.compile(r'Total tests:\s*(\d+), passed:\s*(\d+), failed:\s*(\d+)')
IMPLEMENTATION = ('handrolled_parser/parser.mbt', 'untyped_cst/internal/lower/pattern.mbt')
REGRESSION = 'test/manual_test/negative_pattern_loc_test.mbt'
PATCH_SHA256 = '537eb21b6786a8724f58c90816a67d6ff561779a3d846798e7c7ffca26a7ce87'


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('upstream', type=Path, help='Clean checkout; left unchanged')
    source = parser.parse_args().upstream.resolve()
    root = ROOT/'reports/issue188'; root.mkdir(parents=True, exist_ok=True)
    out = Path(tempfile.mkdtemp(prefix='run-', dir=root)); (out/'logs').mkdir()
    report = {'status': 'failed', 'issue': 188, 'steps': [],
              'started_utc': dt.datetime.now(dt.timezone.utc).isoformat()}

    def run(name: str, command: list[str], cwd: Path, *, timeout=180, ok=True):
        print('['+name+'] '+' '.join(command), flush=True)
        start = time.monotonic(); log = out/'logs'/(name+'.log')
        try:
            proc = subprocess.run(command, cwd=cwd, capture_output=True, text=True,
                                  encoding='utf-8', timeout=timeout)
        except subprocess.TimeoutExpired as exc:
            def text(value):
                return value.decode('utf-8', errors='replace') if isinstance(value, bytes) else (value or '')
            log.write_text(text(exc.stdout)+text(exc.stderr)+'\nTIMEOUT\n', encoding='utf-8')
            report['steps'].append({'name': name, 'exit_code': None, 'timeout': True,
                                    'log': 'logs/'+log.name, 'sha256': digest(log)})
            raise
        log.write_text('$ '+' '.join(command)+'\n'+proc.stdout+proc.stderr, encoding='utf-8')
        report['steps'].append({'name': name, 'exit_code': proc.returncode,
                                'seconds': round(time.monotonic()-start, 3),
                                'log': 'logs/'+log.name, 'sha256': digest(log)})
        if ok and proc.returncode:
            raise RuntimeError(name+' failed; inspect its log')
        return proc

    def totals(proc):
        return [tuple(map(int, row)) for row in SUMMARY.findall(proc.stdout+proc.stderr)]

    try:
        lock = json.loads((ROOT/'upstream.review.lock.json').read_text(encoding='utf-8'))
        base = lock['commit']; patch = ROOT/'review/issue-188.patch'
        report.update(upstream_commit=base, patch_sha256=digest(patch))
        if report['patch_sha256'] != PATCH_SHA256:
            raise RuntimeError('The reviewed standalone patch has changed')
        if run('source-status', ['git', 'status', '--porcelain'], source).stdout.strip():
            raise RuntimeError('Input checkout must be clean')
        if run('source-head', ['git', 'rev-parse', 'HEAD'], source).stdout.strip() != base:
            raise RuntimeError('Input checkout does not match the review lock')
        with tempfile.TemporaryDirectory(prefix='parsercheck-issue188-') as temp:
            work = Path(temp)/'upstream'
            run('clone', ['git', 'clone', '--quiet', '--no-hardlinks', str(source), str(work)], Path(temp))
            run('checkout', ['git', 'checkout', '--detach', base], work)
            run('author', ['git', 'config', 'user.name', 'zhenghao493-netizen'], work)
            run('email', ['git', 'config', 'user.email', '294042204+zhenghao493-netizen@users.noreply.github.com'], work)
            run('toolchain', ['moon', 'version', '--all'], work)
            compiler = run('compiler', ['moonc', '-v'], work)
            if lock['compiler'] not in compiler.stdout+compiler.stderr:
                raise RuntimeError('Compiler differs from the reviewed environment')
            run('dependencies', ['moon', 'update'], work)
            originals = {name: (work/name).read_bytes() for name in IMPLEMENTATION}
            run('apply-delivered-patch', ['git', 'am', str(patch)], work)
            changed = run('changed-files', ['git', 'diff', '--name-only', base], work).stdout.splitlines()
            if set(changed) != {*IMPLEMENTATION, REGRESSION}:
                raise RuntimeError('Patch changes files outside the standalone #188 scope')
            fixed = {name: (work/name).read_bytes() for name in changed}
            # Keep the delivered test file, but restore the original implementations.
            for name, content in originals.items():
                (work/name).write_bytes(content)
            cmd = ['moon', 'test', REGRESSION, '--target', 'js', '--deny-warn']
            run('regression-compile-before', cmd+['--build-only'], work)
            before = run('regression-before', cmd, work, ok=False)
            if before.returncode == 0 or totals(before) != [(7, 1, 6)]:
                raise RuntimeError('Expected six assertion failures and one control before the fix')
            report['before'] = {'tests': 7, 'passed': 1, 'failed': 6}
            for name in IMPLEMENTATION:
                (work/name).write_bytes(fixed[name])
            after = run('regression-after', cmd, work)
            if totals(after) != [(7, 7, 0)]:
                raise RuntimeError('Unexpected post-fix regression summary')
            run('format', ['moon', 'fmt', '--check'], work)
            run('check', ['moon', 'check', '--deny-warn'], work)
            full = run('standalone-full-suite', ['moon', 'test', '--target', 'all'], work, timeout=1200)
            counts = totals(full)
            if len(counts) != 4 or any(t < 7 or t != passed or failed for t, passed, failed in counts):
                raise RuntimeError('Missing successful full-suite results for four backends')
            run('tested-tree-clean', ['git', 'diff', '--exit-code', 'HEAD'], work)
            if any((work/name).read_bytes() != content for name, content in fixed.items()):
                raise RuntimeError('Testing changed a delivered file')
            run('original-still-clean', ['git', 'diff', '--exit-code', 'HEAD'], source)
            if run('original-status-after', ['git', 'status', '--porcelain'], source).stdout.strip():
                raise RuntimeError('Input checkout changed')
            shutil.copyfile(patch, out/'issue-188.patch')
            shutil.copyfile(work/REGRESSION, out/Path(REGRESSION).name)
            report.update(status='passed', after={'tests': 7, 'passed': 7, 'failed': 0},
                          full_totals=[dict(zip(('tests', 'passed', 'failed'), row)) for row in counts],
                          changed_files=changed, excludes_issue189=True, source_checkout_unchanged=True,
                          tested_files_sha256={name: hashlib.sha256(data).hexdigest() for name, data in fixed.items()})
    except Exception as exc:
        report['error'] = f'{type(exc).__name__}: {exc}'
    report['completed_utc'] = dt.datetime.now(dt.timezone.utc).isoformat()
    (out/'result.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in report.items() if k != 'steps'}, indent=2))
    return 0 if report['status'] == 'passed' else 1


if __name__ == '__main__':
    sys.exit(main())
