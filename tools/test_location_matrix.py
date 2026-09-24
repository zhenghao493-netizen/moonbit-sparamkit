#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Exercise pattern composition and Unicode locations before/after each fix.

Uses temporary upstream clones. Does not modify the supplied checkout or snapshots.
"""
from __future__ import annotations
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
from location_cases import generate_cases, expected_pass

ROOT = Path(__file__).resolve().parents[1]
ENGINES = ('handrolled', 'moonyacc', 'cst')
VARIANTS = (
    ('baseline', False, False), ('sign_only', True, False),
    ('group_only', False, True), ('combined', True, True),
)
PATCHES = ('0001-negative-pattern-locations.patch', '0002-grouped-constraint-locations.patch')


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def first_difference(left, right, path='$'):
    if type(left) is not type(right):
        return {'path': path, 'expected': left, 'actual': right}
    if isinstance(left, dict):
        if left.keys() != right.keys():
            return {'path': path, 'expected_keys': sorted(left), 'actual_keys': sorted(right)}
        for key in left:
            delta = first_difference(left[key], right[key], path+'.'+key)
            if delta:
                return delta
    elif isinstance(left, list):
        if len(left) != len(right):
            return {'path': path, 'expected_length': len(left), 'actual_length': len(right)}
        for i, (a, b) in enumerate(zip(left, right)):
            delta = first_difference(a, b, f'{path}[{i}]')
            if delta:
                return delta
    elif left != right:
        return {'path': path, 'expected': left, 'actual': right}
    return None


def without_locations(value):
    # Separate semantic-invariance assertion only. Raw location-aware AST comparison
    # and source-slice checks above remain mandatory; this never changes the oracle.
    if isinstance(value, dict):
        return {k: without_locations(v) for k, v in value.items() if k != 'loc'}
    if isinstance(value, list):
        return [without_locations(v) for v in value]
    return value


def assess(cases: list[dict], outputs: list[dict], sign: bool, group: bool) -> list[dict]:
    if len(outputs) != len(cases):
        raise RuntimeError('Unexpected result count')
    checked = []
    for case, output in zip(cases, outputs, strict=True):
        if output['name'] != case['name'] or set(output['parses']) != set(ENGINES):
            raise RuntimeError('Missing, reordered or duplicate parser output')
        parses = output['parses']
        oracle = parses['moonyacc']['ast']
        errors = []
        for engine in ENGINES:
            actual = parses[engine]
            if actual['diagnostics']:
                errors.append({'engine': engine, 'field': 'diagnostics', 'actual': actual['diagnostics']})
            for field in ('constants', 'constraints'):
                if actual[field] != case[field]:
                    errors.append({'engine': engine, 'field': field,
                                   'expected': case[field], 'actual': actual[field]})
            delta = first_difference(oracle, actual['ast'])
            if delta:
                errors.append({'engine': engine, 'field': 'location_ast', 'difference': delta})
            if without_locations(oracle) != without_locations(actual['ast']):
                raise RuntimeError('Unexpected AST-content difference: '+case['name']+'/'+engine)
        checked.append({'name': case['name'], 'matches': not errors,
                        'expected_match': expected_pass(case, sign, group), 'differences': errors})
    return checked


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('upstream', type=Path)
    args = ap.parse_args()
    source = args.upstream.resolve()
    lock = json.loads((ROOT/'upstream.review.lock.json').read_text(encoding='utf-8'))
    root = ROOT/'reports/location-matrix'; root.mkdir(parents=True, exist_ok=True)
    out = Path(tempfile.mkdtemp(prefix='run-', dir=root))
    (out/'logs').mkdir(); (out/'reference').mkdir()
    cases = generate_cases()
    corpus = out/'cases.json'
    corpus.write_text(json.dumps(cases, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    report = {'status': 'failed', 'upstream_commit': lock['commit'], 'cases': len(cases),
              'corpus_sha256': digest(corpus), 'steps': [], 'variants': {},
              'started_utc': dt.datetime.now(dt.timezone.utc).isoformat()}
    print('Output:', out, flush=True)

    def run(label, command, cwd, *, timeout=240, stdin=None, json_output=None):
        print('['+label+'] '+' '.join(command), flush=True)
        start = time.monotonic(); log = out/'logs'/(label+'.log')
        try:
            p = subprocess.run(command, cwd=cwd, input=stdin, capture_output=True,
                               text=True, encoding='utf-8', timeout=timeout)
        except subprocess.TimeoutExpired as exc:
            def text(v):
                return v.decode('utf-8', 'replace') if isinstance(v, bytes) else (v or '')
            log.write_text(text(exc.stdout)+text(exc.stderr)+'\nTIMEOUT\n', encoding='utf-8')
            raise
        if json_output:
            json_output.write_text(p.stdout, encoding='utf-8')
        log.write_text('$ '+' '.join(command)+'\n'+
                       (f'stdout: {json_output.name}\n' if json_output else p.stdout)+p.stderr,
                       encoding='utf-8')
        report['steps'].append({'name': label, 'exit_code': p.returncode,
                                'seconds': round(time.monotonic()-start, 3),
                                'log': 'logs/'+log.name, 'sha256': digest(log)})
        if p.returncode:
            raise RuntimeError(label+' failed; see '+str(log))
        return p.stdout

    try:
        if run('source-clean', ['git', 'status', '--porcelain'], source).strip():
            raise RuntimeError('Supplied upstream checkout must be clean')
        if run('source-head', ['git', 'rev-parse', 'HEAD'], source).strip() != lock['commit']:
            raise RuntimeError('Unexpected upstream revision')
        compiler = run('compiler', ['moonc', '-v'], source)
        if lock['compiler'] not in compiler:
            raise RuntimeError('Unexpected compiler version')
        run('toolchain', ['moon', 'version', '--all'], source)
        # Validate every exact generated source, including its original CRLF bytes.
        for i, case in enumerate(cases):
            inp = out/'reference'/(case['name']+'.mbt')
            inp.write_bytes(case['source'].encode('utf-8'))
            ref = inp.with_suffix('.json')
            run(f'reference-{i:03}', ['mooninfo', '-dump-ast', str(inp), '-o', str(ref)], source)
            result = json.loads(ref.read_text(encoding='utf-8'))
            if result['has_parse_error'] or result['has_deprecated_syntax']:
                raise RuntimeError('Invalid or deprecated matrix input: '+case['name'])
        report['valid_reference_inputs'] = len(cases)
        with tempfile.TemporaryDirectory(prefix='parsercheck-matrix-') as temporary:
            work = Path(temporary)/'upstream'
            run('clone', ['git', 'clone', '--quiet', '--no-hardlinks', str(source), str(work)], source)
            run('checkout', ['git', 'checkout', '--detach', lock['commit']], work)
            run('dependencies', ['moon', 'update'], work)
            probe = work/'parsercheck_matrix_probe'
            if probe.exists():
                raise RuntimeError('Probe path already exists upstream')
            shutil.copytree(ROOT/'matrix_probe', probe)
            run('format-probe', ['moon', 'fmt', 'parsercheck_matrix_probe'], work)
            shutil.copytree(probe, out/'formatted-probe')
            run('probe-unit-tests', ['moon', 'test', 'parsercheck_matrix_probe', '--target', 'js', '--deny-warn'], work, timeout=600)
            baseline_semantics = None
            for variant, sign, group in VARIANTS:
                selected = [name for name, use in zip(PATCHES, (sign, group)) if use]
                for name in selected:
                    run(variant+'-apply-'+name[:4], ['git', 'apply', str(ROOT/'patches/current'/name)], work)
                # Remove only a previous probe build in this disposable clone.
                for old in (work/'_build').rglob('parsercheck_matrix_probe.js'):
                    old.unlink()
                run(variant+'-build', ['moon', 'build', 'parsercheck_matrix_probe', '--target', 'js',
                                      '--release', '--deny-warn'], work, timeout=600)
                compiled = list((work/'_build').rglob('parsercheck_matrix_probe.js'))
                if len(compiled) != 1:
                    raise RuntimeError('Expected exactly one newly compiled probe')
                node_output = out/(variant+'.raw.json')
                run(variant+'-execute', ['node', str(ROOT/'tools/location_matrix.cjs'), str(compiled[0])],
                    work, stdin=json.dumps(cases, ensure_ascii=False), json_output=node_output)
                outputs = json.loads(node_output.read_text(encoding='utf-8'))
                checks = assess(cases, outputs, sign, group)
                comparison = out/(variant+'.comparisons.json')
                comparison.write_text(json.dumps(checks, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
                # Check each parser's own AST content is unchanged by either fix.
                semantics = [{e: without_locations(o['parses'][e]['ast']) for e in ENGINES} for o in outputs]
                if baseline_semantics is None:
                    baseline_semantics = semantics
                elif semantics != baseline_semantics:
                    raise RuntimeError('A location fix changed non-location AST content')
                unexpected = [c['name'] for c in checks if c['matches'] != c['expected_match']]
                report['variants'][variant] = {
                    'matched': sum(c['matches'] for c in checks),
                    'mismatched': sum(not c['matches'] for c in checks),
                    'unexpected_cases': unexpected,
                    'raw': node_output.name, 'raw_sha256': digest(node_output),
                    'comparisons': comparison.name, 'compiled_sha256': digest(compiled[0]),
                }
                if unexpected:
                    raise RuntimeError('Unexpected matrix results: '+', '.join(unexpected[:8]))
                for name in reversed(selected):
                    run(variant+'-reverse-'+name[:4], ['git', 'apply', '--reverse', str(ROOT/'patches/current'/name)], work)
                run(variant+'-restored', ['git', 'diff', '--exit-code', 'HEAD'], work)
            run('source-unchanged', ['git', 'diff', '--exit-code', 'HEAD'], source)
            if run('source-status', ['git', 'status', '--porcelain'], source).strip():
                raise RuntimeError('Supplied checkout was changed')
        report.update(status='passed', supplied_checkout_unchanged=True,
                      distinct_inputs=240, parser_calls=240*3*4,
                      non_location_ast_unchanged=True,
                      patch_sha256={name: digest(ROOT/'patches/current'/name) for name in PATCHES})
    except Exception as exc:
        report['error'] = f'{type(exc).__name__}: {exc}'
    report['completed_utc'] = dt.datetime.now(dt.timezone.utc).isoformat()
    (out/'result.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='steps'}, indent=2))
    return 0 if report['status']=='passed' else 1


if __name__ == '__main__':
    sys.exit(main())
