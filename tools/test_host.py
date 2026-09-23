#!/usr/bin/env python3
"""Integration checks for CLI input and stale-build handling; stdlib only."""
from pathlib import Path
import json
import shutil
import subprocess
import tempfile
import sys
import tomllib

ROOT = Path(__file__).resolve().parents[1]

def main() -> None:
    checks = []
    def call(args, code):
        p = subprocess.run(['node', str(ROOT/'dist/cli.cjs'), *map(str, args)],
                           capture_output=True, text=True, encoding='utf-8', timeout=20)
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
        bad = td/'bad.s1p'; bad.write_text('# Hz S RI R 50\n1 nan 0\n', encoding='utf-8')
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
        guarded = td/'metadata.s1p'
        for declaration in ('75 0', '50 .01', '50', 'nan 0', '50 0 50 0'):
            guarded.write_text('# Hz S RI R 50\n1 .1 0\n! Port Impedance ' + declaration + '\n', encoding='utf-8')
            for mode in ('json', 'csv'):
                error = json.loads(call([guarded, '--format', mode], 1).stdout)
                assert not error['ok'] and error['error']['code'] == 'UnsupportedMetadata'
        checks.append('both CLI exports reject conflicting or malformed impedance metadata')
        guarded.write_text('# Hz S RI R 75\n1 .1 -.2\n! Port Impedance 75 0\n', encoding='utf-8')
        result = json.loads(call([guarded], 0).stdout)
        assert result['reference_ohms'] == 75 and result['samples'][0]['values'][0]['im'] == -.2
        checks.append('redundant matching impedance metadata preserves S values')
        assert 'Usage:' in call(['--help'], 0).stdout
        checks.append('help is usable without input')
        named = td/'中文目录 with spaces'; named.mkdir()
        chinese = named/'天线测量.S1P'
        chinese.write_text('! 中文注释\n# Hz S RI R 50\n1 .3 -.4\n', encoding='utf-8')
        assert json.loads(call([chinese], 0).stdout)['sample_count'] == 1
        chinese.write_text('# Hz S RI R 50\n1 错误 0\n', encoding='utf-8')
        assert '错误' in json.loads(call([chinese], 1).stdout)['error']['message']
        checks.append('Unicode/spaced paths and UTF-8 diagnostics round-trip without locale defaults')
        delivered = td/'delivered'; shutil.copytree(ROOT/'dist', delivered)
        def integrity(code):
            proc = subprocess.run([sys.executable, str(delivered/'verify_download.py')],
                                  text=True, encoding='utf-8', capture_output=True, timeout=20)
            assert proc.returncode == code, (proc.stdout, proc.stderr)
            return proc
        assert json.loads(integrity(0).stdout)['version'] == tomllib.loads((ROOT/'moon.mod').read_text(encoding='utf-8'))['version']
        checks.append('download manifest verifies all delivered file bytes')
        core = delivered/'core.cjs'; original = core.read_bytes()
        core.write_bytes(original+b'// modified')
        assert 'changed file' in integrity(1).stderr
        core.write_bytes(original)
        extra = delivered/'unexpected.txt'; extra.write_bytes(b'extra')
        assert 'Unlisted files' in integrity(1).stderr
        extra.unlink(); integrity(0)
        checks.append('manifest detects modified core and unexpected files, then recovers')
        manifest_file = delivered/'manifest.json'; original_manifest = manifest_file.read_bytes()
        manifest = json.loads(original_manifest)
        manifest['sha256']['../outside'] = '0'*64
        manifest_file.write_text(json.dumps(manifest), encoding='utf-8')
        assert 'Unsafe manifest path' in integrity(1).stderr
        manifest_file.write_text('{"project":"SParamKit","project":"SParamKit"}', encoding='utf-8')
        assert 'Duplicate manifest key' in integrity(1).stderr
        manifest_file.write_bytes(original_manifest)
        integrity(0)
        checks.append('manifest refuses traversal paths and duplicate JSON keys')
        # Isolate builder with only stale output. The original project is untouched.
        (td/'tools').mkdir(); (td/'dist').mkdir()
        shutil.copyfile(ROOT/'tools/build_web.py', td/'tools/build_web.py')
        stale = td/'dist/core.cjs'; stale.write_text('globalThis.SParamKit = {};', encoding='utf-8')
        p = subprocess.run([sys.executable, str(td/'tools/build_web.py')], text=True, encoding='utf-8', capture_output=True, timeout=20)
        assert p.returncode != 0 and 'Refusing stale' in p.stderr
        assert not (td/'dist/index.html').exists()
        checks.append('builder refuses stale core.cjs when compiled bridge is absent')
    subprocess.run([sys.executable, str(ROOT/'tools/test_cli.py')], check=True, timeout=180)
    subprocess.run([sys.executable, str(ROOT/'tools/test_file_faults.py')], check=True, timeout=180)
    result = {'status':'passed', 'checks':len(checks), 'details':checks}
    (ROOT/'verification/host-tests.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    main()
