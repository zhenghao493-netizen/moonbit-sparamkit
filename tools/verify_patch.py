#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Verify a narrow patch in a disposable, pinned upstream checkout."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('upstream', type=Path)
    args = ap.parse_args()
    upstream = args.upstream.resolve()
    out = ROOT/'reports/negative-patterns'; out.mkdir(parents=True, exist_ok=True)
    report = {'status': 'failed', 'steps': []}

    def run(name, command, timeout=180):
        start = time.monotonic()
        proc = subprocess.run(command, cwd=upstream, capture_output=True,
                              text=True, encoding='utf-8', timeout=timeout)
        log = '$ ' + ' '.join(command) + '\n' + proc.stdout + proc.stderr
        (out/(name+'.log')).write_text(log, encoding='utf-8')
        report['steps'].append({'name': name, 'command': command,
                                'exit_code': proc.returncode,
                                'seconds': round(time.monotonic()-start, 3)})
        return proc

    def checked(name, command, timeout=180):
        proc = run(name, command, timeout)
        if proc.returncode:
            raise RuntimeError(name + ' failed; inspect its log')
        return proc

    try:
        lock = json.loads((ROOT/'upstream.lock.json').read_text(encoding='utf-8'))
        actual = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=upstream, text=True).strip()
        if actual != lock['commit']:
            raise RuntimeError('Upstream does not match lock')
        checked('clean', ['git', 'diff', '--exit-code'])
        report['upstream_commit'] = actual
        name = 'test/manual_test/negative_pattern_loc_test.mbt'
        if (upstream/name).exists():
            raise RuntimeError('Refusing to overwrite an existing regression file')
        shutil.copyfile(ROOT/'regressions/negative_pattern_loc_test.mbt', upstream/name)
        checked('format-regression', ['moon', 'fmt', name])
        checked('compile-regression', ['moon', 'test', name, '--target', 'js', '--build-only', '--deny-warn'])
        red = run('before-patch', ['moon', 'test', name, '--target', 'js', '--deny-warn'])
        text = red.stdout + red.stderr
        match = re.search(r'Total tests:\s*(\d+), passed:\s*(\d+), failed:\s*(\d+)', text)
        if red.returncode == 0 or not match or tuple(map(int, match.groups())) != (7, 1, 6):
            raise RuntimeError('Expected six assertion failures and one positive control before the patch')
        report['before'] = {'tests': 7, 'passed': 1, 'failed': 6}
        patch = ROOT/'patches/0001-negative-pattern-locations.patch'
        report['patch_sha256'] = hashlib.sha256(patch.read_bytes()).hexdigest()
        checked('patch-check', ['git', 'apply', '--check', str(patch)])
        checked('apply', ['git', 'apply', str(patch)])
        checked('format-check', ['moon', 'fmt', '--check'])
        checked('after-patch', ['moon', 'test', name, '--target', 'js', '--deny-warn'])
        checked('check', ['moon', 'check', '--deny-warn'])
        full = checked('full-suite', ['moon', 'test', '--target', 'all'], timeout=900)
        report['full_totals'] = [dict(zip(('tests', 'passed', 'failed'), map(int, m)))
                                 for m in re.findall(r'Total tests:\s*(\d+), passed:\s*(\d+), failed:\s*(\d+)', full.stdout+full.stderr)]
        if len(report['full_totals']) != 4 or any(x['failed'] for x in report['full_totals']):
            raise RuntimeError('Missing one or more backend summaries')
        paths = subprocess.check_output(['git', 'diff', '--name-only'], cwd=upstream, text=True).splitlines()
        if set(paths) != {'handrolled_parser/parser.mbt', 'untyped_cst/lower.mbt'}:
            raise RuntimeError('Unexpected tracked upstream changes: ' + str(paths))
        shutil.copyfile(upstream/name, out/'negative_pattern_loc_test.mbt')
        (out/'tracked.patch').write_text(subprocess.check_output(['git', 'diff'], cwd=upstream, text=True), encoding='utf-8')
        report.update(status='passed', after={'tests': 7, 'passed': 7, 'failed': 0}, changed_files=paths)
    except Exception as error:
        report['error'] = str(error)
    (out/'result.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(report, indent=2))
    return 0 if report['status']=='passed' else 1


if __name__ == '__main__':
    sys.exit(main())
