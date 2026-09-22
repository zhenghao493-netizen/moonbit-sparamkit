#!/usr/bin/env python3
"""File/stdin/output integration tests against the compiled MoonBit CLI."""
from __future__ import annotations
import json
from pathlib import Path
import subprocess
import tempfile
import tomllib

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / 'dist/cli.cjs'
SOURCE = b'! UTF-8 input\n# Hz S RI R 50\n1 .3 -.4\n2 0 0\n'


def main() -> None:
    checks, skipped = [], []
    def call(args, code=0, data=None, cwd=ROOT):
        p = subprocess.run(['node', str(CLI), *map(str, args)], input=data,
                           capture_output=True, cwd=cwd, timeout=20)
        assert p.returncode == code, (args, p.returncode, p.stdout[:500], p.stderr[:500])
        return p
    with tempfile.TemporaryDirectory(prefix='sparamkit-cli-') as folder:
        td = Path(folder)
        source = td / '输入 with spaces.S1P'; source.write_bytes(SOURCE)
        expected = call([source]).stdout
        assert call(['-', '--ports', '1'], data=SOURCE).stdout == expected
        checks.append('stdin JSON matches file JSON')
        expected_csv = call([source, '--format', 'csv']).stdout
        assert call(['-', '--ports', '1', '--format', 'csv'], data=SOURCE).stdout == expected_csv
        checks.append('stdin CSV matches file CSV')
        p = call(['-'], 2, SOURCE)
        assert b'stdin requires --ports' in p.stderr and not p.stdout
        checks.append('stdin requires explicit ports')
        p = call(['-', '--ports', '1'], 1, b'')
        assert json.loads(p.stdout)['error']['code'] == 'NoData'
        checks.append('empty stdin returns structured data error')
        call(['-', '--ports', '1'], 2, b'\xff')
        checks.append('stdin rejects invalid UTF-8')
        call(['-', '--ports', '1'], 2, b'!' * (2 * 1024 * 1024 + 1))
        checks.append('stdin enforces byte limit')
        padded = SOURCE + b'!' + b'x' * (2 * 1024 * 1024 - len(SOURCE) - 1)
        assert call(['-', '--ports', '1'], data=padded).stdout == expected
        checks.append('exact byte-limit stdin accepted')
        marked = b'\xef\xbb\xbf# Hz S RI R 50\r1 .3 -.4\r2 0 0\r'
        assert call(['-', '--ports', '1'], data=marked).stdout == expected
        checks.append('stdin preserves BOM and CR semantics')
        output = td / '结果 with spaces.json'
        p = call([source, '--output', output]); assert not p.stdout and not p.stderr
        assert output.read_bytes() == expected
        checks.append('new JSON output is UTF-8 and stdout stays empty')
        csv = td / 'result.csv'
        call(['-', '--ports', '1', '--format', 'csv', '-o', csv], data=SOURCE)
        assert csv.read_bytes() == expected_csv
        checks.append('stdin writes complete CSV to a new file')
        assert call([source, '-o', '-']).stdout == expected
        checks.append('output dash selects stdout')
        keep = b'previous analysis\x00\xff'; output.write_bytes(keep)
        p = call([source, '-o', output], 2)
        assert not p.stdout and output.read_bytes() == keep
        checks.append('existing output is not overwritten')
        call([source, '-o', source], 2)
        assert source.read_bytes() == SOURCE
        checks.append('input file is never overwritten by output')
        destination = td / 'invalid-result.json'
        p = call(['-', '--ports', '1', '-o', destination], 1, b'# Hz S RI R 50\n1 bad 0\n')
        assert not p.stdout and not destination.exists()
        assert json.loads(p.stderr)['error']['code'] == 'InvalidNumber'
        checks.append('invalid input creates no output and diagnoses on stderr')
        p = call(['-', '--ports', '1', '-o', output], 1, b'# Hz S RI R 50\n1 bad 0\n')
        assert output.read_bytes() == keep and not p.stdout
        checks.append('invalid input preserves pre-existing output')
        call([source, '-o', td/'missing'/'result.csv'], 2)
        call([source, '-o', td], 2)
        checks.append('unwritable output paths return I/O errors')
        dash = td/'--antenna.s1p'; dash.write_bytes(SOURCE)
        assert call(['--', dash.name], cwd=td).stdout == expected
        checks.append('option separator permits dash-prefixed input filename')
        literal_help = td/'--help'; literal_help.write_bytes(SOURCE)
        assert call(['--ports', '1', '--', '--help'], cwd=td).stdout == expected
        checks.append('literal help filename is not treated as a help flag')
        for args in ([source, '--ports', '1', '--ports', '2'],
                     [source, '--format', 'json', '--format', 'csv'],
                     [source, '-o', output, '--output', csv],
                     [source, '-o'], [source, '-o', '--format'],
                     [source, '-x'], [source, '--format'], [source, source]):
            call(args, 2)
        checks.append('duplicate, incomplete and unknown arguments rejected')
        for args in ([], ['--help'], ['-h']):
            assert b'Usage:' in call(args).stdout
        version = tomllib.loads((ROOT/'moon.mod').read_text(encoding='utf-8'))['version']
        assert call(['--version']).stdout.decode().strip() == f'SParamKit {version}'
        checks.append('help and packaged version are available without input')
        # Both symlink targets and hard links must retain their previous bytes.
        hard = td/'hard.json'
        hard.hardlink_to(output)
        call([source, '-o', hard], 2); assert output.read_bytes() == keep
        checks.append('hard-linked output is protected')
        link = td/'symbolic.json'
        # Windows runners do not necessarily grant symlink creation privileges.
        try:
            link.symlink_to(output)
        except OSError:
            skipped.append('symlink creation unavailable on this host')
        else:
            call([source, '-o', link], 2)
            assert output.read_bytes() == keep and link.is_symlink()
            checks.append('symbolic-link output is protected')
        # A real closed pipe must yield a controlled exit, not an uncaught stack trace.
        large = td/'large.s2p'
        large.write_text('# Hz S RI R 50\n' + ''.join(f'{i} .1 0 .2 0 .3 0 .4 0\n' for i in range(20000)), encoding='utf-8')
        p = subprocess.Popen(['node', str(CLI), str(large)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        p.stdout.close(); p.stdout = None
        _, error = p.communicate(timeout=20)
        assert p.returncode == 2 and b'Output pipe closed' in error and b'Unhandled' not in error, error
        checks.append('closed stdout pipe returns a controlled I/O error')
    result = {'status':'passed', 'checks':len(checks), 'details':checks, 'skipped':skipped}
    (ROOT/'verification').mkdir(exist_ok=True)
    (ROOT/'verification/cli-tests.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
