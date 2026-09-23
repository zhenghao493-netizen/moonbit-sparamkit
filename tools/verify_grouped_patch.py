#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Reproduce grouped-constraint spans, then verify both independent fixes together."""
from pathlib import Path
import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
TOTAL = re.compile(r'Total tests:\s*(\d+), passed:\s*(\d+), failed:\s*(\d+)')


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('upstream', type=Path, help='Disposable clean checkout; changes are retained')
    args = ap.parse_args()
    upstream = args.upstream.resolve()
    out = ROOT/'reports/grouped-constraints'
    out.mkdir(parents=True, exist_ok=True)
    report = {'status': 'failed', 'steps': []}

    def run(name: str, command: list[str], timeout: int = 180):
        start = time.monotonic()
        proc = subprocess.run(command, cwd=upstream, capture_output=True,
                              text=True, encoding='utf-8', timeout=timeout)
        (out/(name+'.log')).write_text('$ '+' '.join(command)+'\n'+proc.stdout+proc.stderr,
                                     encoding='utf-8')
        report['steps'].append({'name': name, 'command': command,
                                'exit_code': proc.returncode,
                                'seconds': round(time.monotonic()-start, 3)})
        return proc

    def checked(name: str, command: list[str], timeout: int = 180):
        proc = run(name, command, timeout)
        if proc.returncode:
            raise RuntimeError(name+' failed; inspect its log')
        return proc

    def totals(proc):
        return [tuple(map(int, m)) for m in TOTAL.findall(proc.stdout+proc.stderr)]

    def apply(name: str):
        patch = ROOT/'patches'/name
        checked(name+'-check', ['git', 'apply', '--check', str(patch)])
        checked(name+'-apply', ['git', 'apply', str(patch)])
        report.setdefault('patch_sha256', {})[name] = hashlib.sha256(patch.read_bytes()).hexdigest()

    try:
        lock = json.loads((ROOT/'upstream.lock.json').read_text(encoding='utf-8'))
        head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=upstream, text=True).strip()
        if head != lock['commit']:
            raise RuntimeError('Upstream does not match upstream.lock.json')
        checked('clean', ['git', 'diff', '--exit-code', 'HEAD'])
        report['upstream_commit'] = head
        # Verify the actual test inputs, not a separately maintained approximation.
        test_name = 'test/manual_test/grouped_constraint_loc_test.mbt'
        test_source = (ROOT/'regressions/grouped_constraint_loc_test.mbt').read_text(encoding='utf-8')
        inputs = [json.loads('"'+m+'"') for m in re.findall(r'"(fn f\(x\).*?)"', test_source)]
        if len(inputs) != 10:
            raise RuntimeError('Expected ten source strings in the regression file')
        for i, source in enumerate(inputs):
            path = out/f'case-{i}.mbt'
            path.write_text(source, encoding='utf-8')
            target = path.with_suffix('.reference.json'); target.unlink(missing_ok=True)
            checked(f'reference-{i}', ['mooninfo', '-dump-ast', str(path), '-o', str(target)])
            ast = json.loads(target.read_text(encoding='utf-8'))
            if ast['has_parse_error'] or ast['has_deprecated_syntax']:
                raise RuntimeError(f'case-{i} is not eligible for a valid-syntax regression')
        report['reference_valid_inputs'] = len(inputs)
        for name in (test_name, 'test/manual_test/negative_pattern_loc_test.mbt'):
            if (upstream/name).exists():
                raise RuntimeError('Refusing to overwrite '+name)
        shutil.copyfile(ROOT/'regressions/grouped_constraint_loc_test.mbt', upstream/test_name)
        checked('format-regression', ['moon', 'fmt', test_name])
        checked('compile-regression', ['moon', 'test', test_name, '--target', 'js', '--build-only', '--deny-warn'])
        before = run('before-patch', ['moon', 'test', test_name, '--target', 'js', '--deny-warn'])
        if before.returncode == 0 or totals(before) != [(10, 3, 7)]:
            raise RuntimeError('Expected seven failing assertions and three passing controls before the fix')
        report['before'] = {'tests': 10, 'passed': 3, 'failed': 7}
        apply('0002-grouped-constraint-locations.patch')
        after = checked('after-independent-patch', ['moon', 'test', test_name, '--target', 'js', '--deny-warn'])
        if totals(after) != [(10, 10, 0)]:
            raise RuntimeError('Expected all ten grouped-constraint cases to pass')
        report['after_independent_patch'] = {'tests': 10, 'passed': 10, 'failed': 0}
        # Verify the patches compose; no snapshot changes or weakened expectations.
        apply('0001-negative-pattern-locations.patch')
        old_test = 'test/manual_test/negative_pattern_loc_test.mbt'
        shutil.copyfile(ROOT/'regressions/negative_pattern_loc_test.mbt', upstream/old_test)
        checked('format-negative-regression', ['moon', 'fmt', old_test])
        checked('format-check', ['moon', 'fmt', '--check'])
        checked('check', ['moon', 'check', '--deny-warn'])
        full = checked('combined-full-suite', ['moon', 'test', '--target', 'all'], timeout=900)
        report['combined_full_totals'] = [dict(zip(('tests', 'passed', 'failed'), t)) for t in totals(full)]
        if len(totals(full)) != 4 or any(t[2] for t in totals(full)):
            raise RuntimeError('Missing a successful backend summary')
        paths = subprocess.check_output(['git', 'diff', '--name-only', 'HEAD'], cwd=upstream, text=True).splitlines()
        if set(paths) != {'handrolled_parser/parser.mbt', 'untyped_cst/lower.mbt'}:
            raise RuntimeError('Unexpected upstream changes: '+str(paths))
        for name in (test_name, old_test):
            shutil.copyfile(upstream/name, out/Path(name).name)
        (out/'combined.patch').write_text(subprocess.check_output(['git', 'diff', 'HEAD'], cwd=upstream, text=True), encoding='utf-8')
        report.update(status='passed', changed_implementation_files=paths, new_tests_combined=17)
    except Exception as exc:
        report['error'] = f'{type(exc).__name__}: {exc}'
    (out/'result.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(report, indent=2))
    return 0 if report['status'] == 'passed' else 1


if __name__ == '__main__':
    sys.exit(main())
