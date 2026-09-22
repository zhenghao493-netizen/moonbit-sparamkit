#!/usr/bin/env python3
"""Independent synthetic conformance corpus; no source copied from scikit-rf."""
from __future__ import annotations
import csv
import io
import json
import math
from pathlib import Path
import random
import subprocess
import tempfile
import numpy as np
import skrf

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / 'dist' / 'cli.cjs'
SEED = 20260922

def run_cli(path: Path, fmt: str = 'json') -> str:
    p = subprocess.run(['node', str(CLI), str(path), '--format', fmt],
                       text=True, capture_output=True, timeout=20, check=False)
    if p.returncode != 0:
        raise AssertionError(f'{path.name}: exit {p.returncode}\n{p.stdout}\n{p.stderr}')
    return p.stdout

def verify(path: Path) -> tuple[int, float]:
    actual = json.loads(run_cli(path))
    assert actual['ok'] and actual['schema_version'] == 1
    reference = skrf.Network(str(path))
    freq = np.array([s['frequency_hz'] for s in actual['samples']])
    np.testing.assert_allclose(freq, reference.f, rtol=1e-12, atol=1e-9)
    np.testing.assert_allclose(actual['reference_ohms'], reference.z0.real, rtol=1e-12)
    assert len(actual['samples']) == len(reference.f)
    assert actual['ports'] == reference.nports
    count, maximum = 0, 0.0
    for index, sample in enumerate(actual['samples']):
        assert len(sample['values']) == actual['ports'] ** 2
        for item in sample['values']:
            out, inp = item['output_port'] - 1, item['input_port'] - 1
            assert item['parameter'] == f'S{out+1}{inp+1}'
            expected = reference.s[index, out, inp]
            value = complex(item['re'], item['im'])
            np.testing.assert_allclose([value.real, value.imag], [expected.real, expected.imag],
                                       rtol=1e-10, atol=1e-12)
            maximum = max(maximum, abs(value - expected))
            np.testing.assert_allclose(item['magnitude'], abs(expected), rtol=1e-10, atol=1e-12)
            if abs(expected) == 0:
                assert item['db'] is None and item['phase_degrees'] is None
            else:
                np.testing.assert_allclose(item['db'], reference.s_db[index, out, inp], atol=1e-9)
                difference = (item['phase_degrees'] - reference.s_deg[index, out, inp] + 180) % 360 - 180
                assert abs(difference) < 1e-9
            count += 1
    rows = list(csv.DictReader(io.StringIO(run_cli(path, 'csv'))))
    assert len(rows) == count
    for row in rows:
        f = float(row['frequency_hz'])
        index = int(np.argmin(abs(reference.f - f)))
        out, inp = int(row['output_port']) - 1, int(row['input_port']) - 1
        value = complex(float(row['re']), float(row['im']))
        np.testing.assert_allclose(value, reference.s[index, out, inp], rtol=1e-10, atol=1e-12)
    return count, maximum

def corpus(directory: Path) -> list[Path]:
    rng = random.Random(SEED)
    paths = []
    for ports in (1, 2):
        for fmt in ('RI', 'MA', 'DB'):
            for unit, scale in [('Hz', 1), ('kHz', 1e3), ('MHz', 1e6), ('GHz', 1e9)]:
                for impedance in (25, 50, 75):
                    lines = ['! Deterministic synthetic data, not instrument measurements',
                             f'# {unit} S {fmt} R {impedance}']
                    for index in range(17):
                        fields = [f'{(1e6 + index * 2.5e6) / scale:.16e}']
                        for _ in range(ports * ports):
                            magnitude = 10 ** rng.uniform(-4, 0.2)
                            phase = rng.uniform(-179, 179)
                            if fmt == 'RI':
                                a = magnitude * math.cos(math.radians(phase))
                                b = magnitude * math.sin(math.radians(phase))
                            elif fmt == 'MA':
                                a, b = magnitude, phase
                            else:
                                a, b = 20 * math.log10(magnitude), phase
                            fields.extend([f'{a:+.16e}', f'{b:+.16e}'])
                        if ports == 2 and index % 3 == 0:
                            lines.extend(['\t'.join(fields[:5]), '! continued record', ' '.join(fields[5:])])
                        else:
                            lines.append(' '.join(fields) + ' ! sample')
                    path = directory / f'{ports}_{fmt}_{unit}_{impedance}.s{ports}p'
                    path.write_bytes(('\r\n'.join(lines) + '\r\n').encode('ascii'))
                    paths.append(path)
    return paths

def main() -> None:
    reports = []
    with tempfile.TemporaryDirectory() as tmp:
        paths = corpus(Path(tmp))
        paths.extend(sorted((ROOT / 'samples').glob('*.s?p')))
        paths.extend(sorted((ROOT / 'dist' / 'samples').glob('synthetic*.s?p')))
        for path in paths:
            values, error = verify(path)
            reports.append({'file': path.name, 'complex_values': values, 'max_abs_error': error})
    result = {
        'status': 'passed', 'seed': SEED, 'scikit_rf': skrf.__version__, 'numpy': np.__version__,
        'cases': len(reports), 'complex_values': sum(r['complex_values'] for r in reports),
        'max_abs_complex_error': max(r['max_abs_error'] for r in reports),
        'relative_tolerance': 1e-10, 'absolute_tolerance': 1e-12,
        'scope': 'synthetic common subset only; not full conformance or measured-hardware validation',
        'results': reports,
    }
    target = ROOT / 'verification' / 'crosscheck.json'
    target.parent.mkdir(exist_ok=True)
    target.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'results'}, indent=2))

if __name__ == '__main__':
    main()
