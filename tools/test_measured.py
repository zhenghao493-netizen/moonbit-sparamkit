#!/usr/bin/env python3
"""Check unchanged upstream-labelled measured fixtures; no hardware claims."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import sys
import skrf
import skrf.data
from crosscheck import verify

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = [
    ('ring slot measured.s1p', '094aee842edea2e16af6003e5186406b0bccc9f1'),
    ('ind.s2p', '70234dfc515caaf98bd050da97520f1e0eb91b01'),
]

def main() -> int:
    report = {'status': 'failed', 'scikit_rf': skrf.__version__, 'files': [],
              'scope': 'Two unchanged upstream-labelled measured examples; not new laboratory measurements or instrument-wide certification.'}
    try:
        if skrf.__version__ != '1.8.0':
            raise RuntimeError('This provenance-locked test requires scikit-rf==1.8.0')
        directory = Path(skrf.data.__file__).parent
        for name, expected_blob in FIXTURES:
            path = directory / name
            data = path.read_bytes()
            blob = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
            if blob != expected_blob:
                raise RuntimeError(f'{name}: upstream fixture content differs from pinned Git blob')
            count, error = verify(path)
            report['files'].append({'file': name, 'git_blob': blob,
                                    'sha256': hashlib.sha256(data).hexdigest(),
                                    'complex_values': count, 'max_abs_error': error,
                                    'source': 'scikit-rf/scikit-rf@v1.8.0/skrf/data/' + name})
        report['cases'] = len(report['files'])
        report['complex_values'] = sum(x['complex_values'] for x in report['files'])
        report['max_abs_complex_error'] = max(x['max_abs_error'] for x in report['files'])
        report['status'] = 'passed'
    except Exception as exc:
        report['error'] = f'{type(exc).__name__}: {exc}'
    out = ROOT / 'verification' / 'measured-files.json'
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2))
    return 0 if report['status'] == 'passed' else 1

if __name__ == '__main__':
    sys.exit(main())
