#!/usr/bin/env python3
"""Integration checks for CLI input and stale-build handling; stdlib only."""
from pathlib import Path
import json
import shutil
import subprocess
import tempfile
import sys

ROOT = Path(__file__).resolve().parents[1]

def main() -> None:
    checks = []
    def call(args, code):
        p = subprocess.run(['node', str(ROOT/'dist/cli.cjs'), *map(str, args)],
                           capture_output=True, text=True, timeout=20)
        assert p.returncode == code, (args, p.returncode, p.stdout, p.stderr)
        return p
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        file = td/'sample.S1P'
        file.write_bytes(b'\xef\xbb\xbf# Hz S RI R 50\r1 .3 -.4\r2 0 0\r')
        result = json.loads(call([file], 0).stdout)
        assert result['sample_count'] == 2 and result['samples'][0]['values'][0]['im'] == -.4
        checks.append('CLI accepts upper-case suffix, BOM and CR-only file')
        csv = call([file, '--format', 'csv'], 0).stdout
        assert len(csv.splitlines()) == 3
        checks.append('CSV exports all CR-only samples')
        bad = td/'bad.s1p'; bad.write_text('# Hz S RI R 50\n1 nan 0\n')
        parsed = json.loads(call([bad], 1).stdout)
        assert not parsed['ok'] and parsed['error']['code'] == 'InvalidNumber'
        checks.append('invalid network returns exit 1 with structured JSON')
        invalid = td/'invalid.s1p'; invalid.write_bytes(b'\xff\xfe')
        call([invalid], 2); checks.append('invalid UTF-8 returns exit 2')
        big = td/'big.s1p'; big.write_bytes(b'!' * (2*1024*1024+1))
        call([big], 2); checks.append('oversized file returns exit 2')
        for args in ([td/'missing.s1p'], [td], [file, '--ports', '3'], [file, '--format', 'no'], [file, '--ports'], [file, '--nope'], [file, file]):
            call(args, 2)
        checks.append('seven path and argument failures return exit 2')
        assert 'Usage:' in call(['--help'], 0).stdout
        checks.append('help is usable without input')
        # Isolate builder with only stale output. The original project is untouched.
        (td/'tools').mkdir(); (td/'dist').mkdir()
        shutil.copyfile(ROOT/'tools/build_web.py', td/'tools/build_web.py')
        stale = td/'dist/core.cjs'; stale.write_text('globalThis.SParamKit = {};')
        p = subprocess.run([sys.executable, str(td/'tools/build_web.py')], text=True, capture_output=True, timeout=20)
        assert p.returncode != 0 and 'Refusing stale' in p.stderr
        assert not (td/'dist/index.html').exists()
        checks.append('builder refuses stale core.cjs when compiled bridge is absent')
    result = {'status':'passed', 'checks':len(checks), 'details':checks}
    (ROOT/'verification/host-tests.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    main()
