#!/usr/bin/env python3
"""Check binary64 edge cases against a 100-digit Decimal oracle and CSV output."""
from __future__ import annotations
import csv
from decimal import Decimal, localcontext
import io
import json
import math
from pathlib import Path
import random
import shutil
import struct
import subprocess
import sys
import tempfile
import tomllib

ROOT = Path(__file__).resolve().parents[1]
SEED = 20260923
DB_TOLERANCE = 1e-10


def corpus() -> list[tuple[float, float]]:
    tiny, normal, huge = math.ulp(0.0), sys.float_info.min, sys.float_info.max
    pairs = [(0., 0.), (.3, -.4), (1.7e308, 1.7e308),
             (tiny, tiny), (1e-320, 1e-320), (1., 1e-8)]
    for x in (tiny, 2*tiny, 3*tiny, 1e-320, 1e-308, normal,
              1e-200, 1e-100, 1., 1e100, 1e200, 1e308, huge):
        pairs.extend([(x, 0.), (0., -x), (x, x), (-x, x), (x, tiny)])
    rng = random.Random(SEED)
    while len(pairs) < 1024:
        x, y = (struct.unpack('>d', rng.getrandbits(64).to_bytes(8, 'big'))[0]
                for _ in range(2))
        if math.isfinite(x) and math.isfinite(y):
            pairs.append((x, y))
    return pairs


def expected_metrics(x: float, y: float) -> tuple[float, float | None]:
    # Decimal.from_float preserves the exact binary64 inputs. This oracle does
    # not use the production scaled-log formula or binary64 hypot/log10.
    with localcontext() as ctx:
        ctx.prec = 100
        a, b = Decimal.from_float(x), Decimal.from_float(y)
        power = a*a + b*b
        if not power:
            return 0., None
        return float(power.sqrt()), float(Decimal(10) * power.log10())


def main() -> int:
    pairs = corpus()
    expected = [expected_metrics(*pair) for pair in pairs]
    result = {'status': 'failed', 'seed': SEED, 'precision_digits': 100,
              'pairs': len(pairs), 'db_absolute_tolerance': DB_TOLERANCE,
              'targets': [], 'commands': [], 'failures': [], 'failure_count': 0}

    def require(ok: bool, message: str):
        if not ok:
            result['failure_count'] += 1
            if len(result['failures']) < 20:
                result['failures'].append(message)

    def run(args, cwd, data=None):
        p = subprocess.run(args, cwd=cwd, input=data, text=True, encoding='utf-8',
                           capture_output=True, timeout=180)
        result['commands'].append({'command': list(map(str, args)), 'exit_code': p.returncode,
                                   'stderr': p.stderr[-6000:]})
        if p.returncode:
            raise RuntimeError(f'{args}: {p.stderr}\n{p.stdout[:1000]}')
        return p.stdout

    def text_for(ports):
        lines = ['# Hz S RI R 50']
        width = ports * ports
        for start in range(0, len(pairs), width):
            fields = [str(start // width + 1)]
            for pair in pairs[start:start+width]:
                fields.extend(format(value, '.17g') for value in pair)
            lines.append(' '.join(fields))
        return '\n'.join(lines) + '\n'

    def check(report, csv_report, ports, target):
        label = f'{target}/{ports}-port'
        require(report.get('ok') is True and csv_report.get('ok') is True, label+' parse')
        if not report.get('ok') or not csv_report.get('ok'):
            return None
        require(report['ports'] == ports and report['reference_ohms'] == 50, label+' metadata')
        require(report['sample_count'] == len(pairs)//(ports*ports), label+' count')
        require(len(report['samples']) == report['sample_count'], label+' samples')
        rows = list(csv.DictReader(io.StringIO(csv_report['csv'])))
        require(len(rows) == len(pairs), label+' CSV count')
        maximum = 0.
        for index, ((x, y), (magnitude, db)) in enumerate(zip(pairs, expected)):
            sample_index, slot = divmod(index, ports * ports)
            out, inp = slot % ports + 1, slot // ports + 1
            sample = report['samples'][sample_index]
            value = sample['values'][slot]
            require(sample['frequency_hz'] == sample_index + 1, label+' frequency')
            require((value['output_port'], value['input_port'], value['parameter']) ==
                    (out, inp, f'S{out}{inp}'), label+' indexing')
            require(float(value['re']) == x and float(value['im']) == y, f'{label}/{index} RI round-trip')
            actual_db = value['db']
            if db is None:
                require(actual_db is None and value['phase_degrees'] is None,
                        label+' zero metrics')
            else:
                finite_db = isinstance(actual_db, (float, int)) and math.isfinite(actual_db)
                require(finite_db, f'{label}/{index} missing finite dB for {x!r}, {y!r}')
                if finite_db:
                    delta = abs(actual_db-db)
                    maximum = max(maximum, delta)
                    require(delta <= DB_TOLERANCE,
                            f'{label}/{index} dB error {delta!r}: {actual_db!r} != {db!r}')
                angle = value['phase_degrees']
                phase = math.degrees(math.atan2(y, x))
                require(angle is not None and abs((angle-phase+180)%360-180) < 1e-10,
                        f'{label}/{index} phase')
            if math.isinf(magnitude):
                require(value['magnitude'] is None, label+' unrepresentable magnitude')
            else:
                actual_mag = value['magnitude']
                require(actual_mag is not None and math.isfinite(actual_mag) and
                        abs(actual_mag-magnitude) <= 2*math.ulp(magnitude),
                        f'{label}/{index} magnitude outside 2 ulps')
            row = rows[index]
            require((float(row['frequency_hz']), float(row['reference_ohms']),
                     int(row['output_port']), int(row['input_port'])) ==
                    (sample_index+1, 50, out, inp), label+' CSV labels')
            require(float(row['re']) == x and float(row['im']) == y,
                    f'{label}/{index} CSV RI round-trip')
        return maximum

    try:
        version = tomllib.loads((ROOT/'moon.mod').read_text(encoding='utf-8'))['version']
        with tempfile.TemporaryDirectory(prefix='sparamkit-numeric-') as folder:
            work = Path(folder)
            library, probe = work/'library', work/'probe'
            library.mkdir(); probe.mkdir()
            for file in ROOT.glob('*.mbt'):
                if not file.name.endswith(('_test.mbt', '_wbtest.mbt')):
                    shutil.copyfile(file, library/file.name)
            for name in ('moon.mod', 'moon.pkg'):
                shutil.copyfile(ROOT/name, library/name)
            (work/'moon.work').write_text('members = ["library", "probe"]\n', encoding='utf-8')
            (probe/'moon.mod').write_text('name = "example/numeric-probe"\nimport { "ttxiangshang/sparamkit@'+version+'" }\n', encoding='utf-8')
            (probe/'moon.pkg').write_text('import { "ttxiangshang/sparamkit" @sparam }\npkgtype(kind: "executable")\n', encoding='utf-8')
            source = ['fn main {']
            for ports in (1, 2):
                source += [f'  let source{ports} = '+json.dumps(text_for(ports)),
                           f'  println(@sparam.analyze_touchstone_json(source{ports}, {ports}))',
                           f'  println(@sparam.export_touchstone_csv_json(source{ports}, {ports}))']
            (probe/'main.mbt').write_text('\n'.join(source+['}', '']), encoding='utf-8')
            for target in ('js', 'wasm-gc'):
                lines = run(['moon','run','.','--target',target,'--deny-warn'], probe).splitlines()
                if len(lines) != 4:
                    raise RuntimeError('Expected four JSON reports from numeric probe')
                reports = list(map(json.loads, lines))
                errors = [check(reports[2*(p-1)], reports[2*p-1], p, target) for p in (1,2)]
                result['targets'].append({'target': target, 'parameter_values': len(pairs)*2,
                                          'max_db_absolute_error': max(x for x in errors if x is not None)})
                if target == 'js':
                    for p in (1,2):
                        for mode, offset in (('json',0),('csv',1)):
                            output = run(['node',str(ROOT/'dist/cli.cjs'),'-','--ports',str(p),'--format',mode],
                                         ROOT, text_for(p))
                            same = json.loads(output) == reports[2*(p-1)] if mode == 'json' else output == reports[2*(p-1)+offset]['csv']
                            require(same, f'CLI/{p}-port/{mode} differs from current MoonBit source')
        result['status'] = 'passed' if result['failure_count'] == 0 else 'failed'
    except Exception as exc:
        result['error'] = f'{type(exc).__name__}: {exc}'
    (ROOT/'verification').mkdir(exist_ok=True)
    (ROOT/'verification/numeric-tests.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n', encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k != 'commands'},ensure_ascii=False,indent=2))
    return 0 if result['status'] == 'passed' else 1


if __name__ == '__main__':
    sys.exit(main())
