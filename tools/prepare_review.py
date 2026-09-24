#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Test two independent patches against a locked upstream and prepare review commits.

All source changes take place in temporary clones. The supplied checkout is read-only.
"""
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
TOTAL = re.compile(r'Total tests:\s*(\d+), passed:\s*(\d+), failed:\s*(\d+)')
CASES = (
    (188, '0001-negative-pattern-locations.patch', 'negative_pattern_loc_test.mbt', 7, 1, 6,
     'fix: include the minus sign in negative-pattern locations',
     ('handrolled_parser/parser.mbt', 'untyped_cst/internal/lower/pattern.mbt')),
    (189, '0002-grouped-constraint-locations.patch', 'grouped_constraint_loc_test.mbt', 10, 3, 7,
     'fix: preserve inner constraint locations through redundant grouping',
     ('untyped_cst/internal/lower/pattern.mbt',)),
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('upstream', type=Path, help='Clean checkout of upstream.review.lock.json revision')
    args = ap.parse_args()
    source = args.upstream.resolve()
    lock = json.loads((ROOT/'upstream.review.lock.json').read_text(encoding='utf-8'))
    # A separate run directory never overwrites previous evidence or marks it current.
    root = ROOT/'reports/current-review'; root.mkdir(parents=True, exist_ok=True)
    out = Path(tempfile.mkdtemp(prefix='run-', dir=root))
    (out/'logs').mkdir(); (out/'inputs').mkdir()
    report = {'status': 'failed', 'upstream_commit': lock['commit'], 'steps': [],
              'started_utc': dt.datetime.now(dt.timezone.utc).isoformat()}
    print('Report directory:', out, flush=True)

    def run(label: str, argv: list[str], cwd: Path, timeout: int = 180):
        start = time.monotonic()
        print('['+label+'] '+' '.join(argv), flush=True)
        log = out/'logs'/(label+'.log')
        try:
            p = subprocess.run(argv, cwd=cwd, capture_output=True, text=True,
                               encoding='utf-8', errors='strict', timeout=timeout)
        except subprocess.TimeoutExpired as exc:
            def text(x):
                return x.decode('utf-8', errors='replace') if isinstance(x, bytes) else (x or '')
            log.write_text('$ '+' '.join(argv)+'\n'+text(exc.stdout)+text(exc.stderr)+'\nTIMEOUT\n', encoding='utf-8')
            report['steps'].append({'name': label, 'exit_code': None, 'timeout': True,
                                    'log': 'logs/'+log.name, 'sha256': sha(log)})
            raise
        log.write_text('$ '+' '.join(argv)+'\n'+p.stdout+p.stderr, encoding='utf-8')
        report['steps'].append({'name': label, 'exit_code': p.returncode,
                                'seconds': round(time.monotonic()-start, 3),
                                'log': 'logs/'+log.name, 'sha256': sha(log)})
        return p

    def checked(label, argv, cwd, timeout=180):
        p = run(label, argv, cwd, timeout)
        if p.returncode:
            raise RuntimeError(label+' failed; inspect its log')
        return p

    def totals(p):
        return [tuple(map(int, row)) for row in TOTAL.findall(p.stdout+p.stderr)]

    def assert_totals(p, expected):
        if totals(p) != [expected]:
            raise RuntimeError('Unexpected test summary: '+str(totals(p)))

    try:
        original_status = checked('source-clean', ['git', 'status', '--porcelain'], source).stdout
        if original_status.strip():
            raise RuntimeError('The supplied upstream checkout is not clean')
        head = checked('source-revision', ['git', 'rev-parse', 'HEAD'], source).stdout.strip()
        if head != lock['commit']:
            raise RuntimeError('Unexpected upstream revision: '+head)
        with tempfile.TemporaryDirectory(prefix='parsercheck-review-') as temporary:
            temp = Path(temporary)

            def clone(label):
                dest = temp/label
                checked(label+'-clone', ['git', 'clone', '--quiet', '--no-hardlinks', str(source), str(dest)], temp)
                checked(label+'-checkout', ['git', 'checkout', '--detach', lock['commit']], dest)
                checked(label+'-identity', ['git', 'config', 'user.name', 'zhenghao493-netizen'], dest)
                checked(label+'-email', ['git', 'config', 'user.email',
                        '294042204+zhenghao493-netizen@users.noreply.github.com'], dest)
                return dest

            work = clone('test')
            checked('toolchain', ['moon', 'version', '--all'], work)
            compiler = checked('compiler', ['moonc', '-v'], work).stdout
            if lock['compiler'] not in compiler:
                raise RuntimeError('Compiler differs from the reviewed version: '+compiler)
            checked('dependencies', ['moon', 'update'], work)
            checked('baseline-check', ['moon', 'check', '--deny-warn'], work)
            original_blobs = {path: sha(work/path) for path in {p for c in CASES for p in c[7]}}
            report['baseline_implementation_sha256'] = original_blobs
            results = []; formatted = {}; inputs = []
            for issue, patch_name, test_name, count, passed, failed, message, paths in CASES:
                prefix = 'issue-'+str(issue)
                target = work/'test/manual_test'/test_name
                if target.exists():
                    raise RuntimeError('Regression filename already exists in upstream: '+test_name)
                contents = (ROOT/'regressions'/test_name).read_text(encoding='utf-8')
                values = [json.loads('"'+v+'"') for v in re.findall(r'"(fn f\(x(?:\\.|[^"\\])*)"', contents)]
                if len(values) != count:
                    raise RuntimeError('Regression source input count changed: '+test_name)
                for i, value in enumerate(values):
                    inp = out/'inputs'/f'{issue}-{i}.mbt'; inp.write_text(value, encoding='utf-8')
                    ref = inp.with_suffix('.json')
                    checked(f'{prefix}-syntax-{i}', ['mooninfo', '-dump-ast', str(inp), '-o', str(ref)], work)
                    reference = json.loads(ref.read_text(encoding='utf-8'))
                    if reference['has_parse_error'] or reference['has_deprecated_syntax']:
                        raise RuntimeError('Invalid or deprecated regression input: '+inp.name)
                    inputs.append(inp.name)
                shutil.copyfile(ROOT/'regressions'/test_name, target)
                checked(prefix+'-format', ['moon', 'fmt', str(target.relative_to(work))], work)
                formatted[test_name] = target.read_bytes()
                cmd = ['moon', 'test', str(target.relative_to(work)), '--target', 'js', '--deny-warn']
                checked(prefix+'-compile', cmd+['--build-only'], work)
                red = run(prefix+'-before', cmd, work)
                if red.returncode == 0:
                    raise RuntimeError('Problem no longer reproduces against the new upstream')
                assert_totals(red, (count, passed, failed))
                patch = ROOT/'patches/current'/patch_name
                checked(prefix+'-patch-check', ['git', 'apply', '--check', str(patch)], work)
                checked(prefix+'-patch-apply', ['git', 'apply', str(patch)], work)
                green = checked(prefix+'-after', cmd, work)
                assert_totals(green, (count, count, 0))
                checked(prefix+'-format-check', ['moon', 'fmt', '--check'], work)
                changed = checked(prefix+'-changed', ['git', 'diff', '--name-only', 'HEAD'], work).stdout.splitlines()
                if set(changed) != set(paths):
                    raise RuntimeError('Unexpected implementation changes: '+str(changed))
                results.append({'issue': issue, 'before': {'tests': count, 'passed': passed, 'failed': failed},
                                'after': {'tests': count, 'passed': count, 'failed': 0},
                                'patch_sha256': sha(patch), 'implementation_files': list(paths)})
                checked(prefix+'-revert', ['git', 'apply', '--reverse', str(patch)], work)
                target.unlink()  # Only our newly created file, inside a temporary clone.
                checked(prefix+'-restored', ['git', 'diff', '--exit-code', 'HEAD'], work)
            report.update(independent_fixes=results, reference_valid_inputs=len(inputs))
            # Apply both fixes, keep test expectations unchanged, and run the entire suite.
            for issue, patch_name, test_name, *_ in CASES:
                checked(f'combined-apply-{issue}', ['git', 'apply', str(ROOT/'patches/current'/patch_name)], work)
                (work/'test/manual_test'/test_name).write_bytes(formatted[test_name])
            checked('combined-format', ['moon', 'fmt', '--check'], work)
            checked('combined-check', ['moon', 'check', '--deny-warn'], work)
            full = checked('combined-all-targets', ['moon', 'test', '--target', 'all'], work, timeout=1200)
            summary = totals(full)
            if len(summary) != 4 or any(f or t != p for t, p, f in summary):
                raise RuntimeError('Missing a successful test summary for one of four backends')
            report['combined_full_totals'] = [dict(zip(('tests', 'passed', 'failed'), x)) for x in summary]
            report['new_tests'] = sum(c[3] for c in CASES)
            changed = checked('combined-files', ['git', 'diff', '--name-only', 'HEAD'], work).stdout.splitlines()
            if set(changed) != set(original_blobs):
                raise RuntimeError('Full suite changed other tracked files')
            final_paths = sorted(set(changed) | {'test/manual_test/'+c[2] for c in CASES})
            tested_bytes = {path: (work/path).read_bytes() for path in final_paths}
            # Each review commit starts from the upstream base, not from the other fix.
            ready = out/'ready'; ready.mkdir()
            commits = []
            for issue, patch_name, test_name, _, _, _, message, paths in CASES:
                review = clone('review-'+str(issue))
                checked(f'prepare-{issue}', ['git', 'apply', str(ROOT/'patches/current'/patch_name)], review)
                (review/'test/manual_test'/test_name).write_bytes(formatted[test_name])
                review_paths = [*paths, 'test/manual_test/'+test_name]
                checked(f'stage-{issue}', ['git', 'add', '--', *review_paths], review)
                checked(f'check-diff-{issue}', ['git', 'diff', '--cached', '--check'], review)
                checked(f'commit-{issue}', ['git', 'commit', '-m', message+'\n\nRefs #'+str(issue)], review)
                commit = checked(f'commit-id-{issue}', ['git', 'rev-parse', 'HEAD'], review).stdout.strip()
                export = checked(f'export-{issue}', ['git', 'format-patch', '-1', '--stdout'], review).stdout
                patchfile = ready/f'issue-{issue}.patch'; patchfile.write_text(export, encoding='utf-8')
                commits.append({'issue': issue, 'commit': commit, 'base': head,
                                'file': patchfile.name, 'sha256': sha(patchfile)})
            # Test the actual mail patches delivered to a maintainer, not just raw diffs.
            replay = clone('replay')
            for item in commits:
                checked('am-'+str(item['issue']), ['git', 'am', str(ready/item['file'])], replay)
            replay_paths = checked('replay-files', ['git', 'diff', '--name-only', head], replay).stdout.splitlines()
            if set(replay_paths) != set(final_paths):
                raise RuntimeError('Delivered patch files differ from the tested change set')
            if any((replay/path).read_bytes() != content for path, content in tested_bytes.items()):
                raise RuntimeError('Delivered patches do not reconstruct the tested source bytes')
            checked('source-unchanged', ['git', 'diff', '--exit-code', 'HEAD'], source)
            final_status = checked('source-status', ['git', 'status', '--porcelain'], source).stdout
            if final_status != original_status:
                raise RuntimeError('Input checkout was changed during verification')
            report.update(status='passed', review_commits=commits,
                          git_am_reconstructs_tested_files=True, supplied_checkout_unchanged=True,
                          tested_files_sha256={p: hashlib.sha256(v).hexdigest() for p, v in tested_bytes.items()})
    except Exception as exc:
        report['error'] = f'{type(exc).__name__}: {exc}'
    report['completed_utc'] = dt.datetime.now(dt.timezone.utc).isoformat()
    (out/'result.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='steps'}, indent=2))
    return 0 if report['status'] == 'passed' else 1


if __name__ == '__main__':
    sys.exit(main())
