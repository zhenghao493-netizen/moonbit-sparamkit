#!/usr/bin/env python3
"""Package compiled MoonBit bridge with a network-free UI; never reimplement parser."""
from pathlib import Path
import hashlib
import html
import tomllib
import json
import math
import os
import shutil
import stat

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / 'dist'

def examples():
    # Analytic shunt series-RLC two-port, equal real 50-ohm reference impedances.
    # Z=R+j(wL-1/wC), S11=S22=-Z0/(2Z+Z0), S21=S12=2Z/(2Z+Z0).
    two = ['! Synthetic shunt series-RLC circuit. NOT instrument measurements.', '# GHz S RI R 50']
    c = 1e-12
    l = 1 / ((2 * math.pi * 2.4e9) ** 2 * c)
    for i in range(291):
        f = (0.2 + i * 0.02) * 1e9
        w = 2 * math.pi * f
        z = complex(1.5, w * l - 1 / (w * c))
        r, t = -50 / (2*z+50), 2*z / (2*z+50)
        fields = [f'{f/1e9:.12g}']
        for value in (r, t, t, r):
            fields.extend([f'{value.real:.16g}', f'{value.imag:.16g}'])
        two.append(' '.join(fields))
    # Series-RC load: reflection=(Z-Z0)/(Z+Z0).
    one = ['! Synthetic series-RC load. NOT instrument measurements.', '# MHz S RI R 50']
    for i in range(161):
        f = (50 + 10*i) * 1e6
        z = complex(45, -1/(2*math.pi*f*5e-12))
        r = (z-50)/(z+50)
        one.append(f'{f/1e6:.12g} {r.real:.16g} {r.imag:.16g}')
    return {
        'two': {'name': 'synthetic_notch.s2p', 'ports': 2, 'text': '\n'.join(two)+'\n'},
        'one': {'name': 'synthetic_rc.s1p', 'ports': 1, 'text': '\n'.join(one)+'\n'},
        'error': {'name': 'invalid_example.s2p', 'ports': 2, 'text': '# GHz S RI R 50\n1 0.1 0 0.8 0\n'},
    }


def check_output_directory(expected: set[str]) -> None:
    """Refuse unrelated files before writing; never delete a user's local results."""
    directories = {Path(name).parent.as_posix() for name in expected} - {'.'}
    if DIST.is_symlink():
        raise ValueError('Output directory is a symlink: dist')
    if not DIST.exists():
        return
    if not DIST.is_dir():
        raise ValueError('Output path is not a directory: dist')
    for path in DIST.rglob('*'):
        name = path.relative_to(DIST).as_posix()
        mode = path.lstat().st_mode
        if stat.S_ISLNK(mode):
            raise ValueError('Output contains a symlink: ' + name)
        if stat.S_ISDIR(mode) and name in directories:
            continue
        if stat.S_ISREG(mode) and name in expected:
            continue
        raise ValueError('Unexpected output entry: ' + name +
                         '. Move local results out of dist before rebuilding; nothing was removed.')

def main():
    compiled = ROOT/'_build/js/release/build/bridge/bridge.js'
    if not compiled.is_file():
        raise FileNotFoundError('Missing current compiled bridge; run moon build bridge --target js --release --deny-warn first. Refusing stale dist/core.cjs.')
    sample_files = sorted((ROOT/'samples').glob('*.s?p'))
    for sample in sample_files:
        if sample.is_symlink() or not sample.is_file():
            raise ValueError('Sample must be a regular file: ' + sample.name)
    expected = {'core.cjs', 'cli.cjs', 'index.html', 'LICENSE', 'READ_ME.txt',
                'verify_download.py', 'manifest.json', 'samples/synthetic_notch.s2p',
                'samples/synthetic_rc.s1p'} | {'samples/' + p.name for p in sample_files}
    check_output_directory(expected)
    core = compiled.read_text(encoding='utf-8')
    if 'SParamKit' not in core:
        raise RuntimeError('Missing compiled bridge; run moon build bridge --target js --release --deny-warn')
    version = tomllib.loads((ROOT/'moon.mod').read_text(encoding='utf-8'))['version']
    if not (ROOT/'LICENSE').is_file():
        raise FileNotFoundError('LICENSE is required in the runtime package')
    DIST.mkdir(exist_ok=True)
    # Invalidate the old manifest first: an interrupted build cannot look verified.
    (DIST/'manifest.json').unlink(missing_ok=True)
    shutil.copyfile(compiled,DIST/'core.cjs')
    demo = examples()
    demo_dir = DIST/'samples'; demo_dir.mkdir(exist_ok=True)
    for key in ('two','one'):
        (demo_dir/demo[key]['name']).write_text(demo[key]['text'],encoding='utf-8',newline='\n')
    if (ROOT/'samples').exists():
        for file in sample_files:
            shutil.copyfile(file,demo_dir/file.name)
    template = (ROOT/'web/index.html').read_text(encoding='utf-8')
    replacements = {
        '/*__STYLE__*/': (ROOT/'web/style.css').read_text(encoding='utf-8'),
        '/*__CORE__*/': core.replace('</script', '<\\/script'),
        '/*__DEMOS__*/': json.dumps(demo,ensure_ascii=False).replace('<','\\u003c'),
        '/*__APP__*/': (ROOT/'web/app.js').read_text(encoding='utf-8'),
        '__VERSION__': html.escape(version),
        '__BUILD__': os.getenv('GITHUB_SHA','local')[:12],
    }
    for marker, content in replacements.items():
        assert template.count(marker)==1, marker
        template=template.replace(marker,content)
    (DIST/'index.html').write_text(template,encoding='utf-8',newline='\n')
    shutil.copyfile(ROOT/'tools/cli.cjs',DIST/'cli.cjs')
    if (ROOT/'LICENSE').exists(): shutil.copyfile(ROOT/'LICENSE',DIST/'LICENSE')
    (DIST/'READ_ME.txt').write_text('SParamKit\n\nOpen index.html in a modern browser (Chrome/Edge recommended).\nThe single HTML file works offline; it does not send data over the network.\nBuilt-in examples are synthetic, not instrument measurements.\n\nCLI: node cli.cjs samples/synthetic_notch.s2p --format json\nCSV: node cli.cjs samples/synthetic_notch.s2p --format csv\n\nStrict Touchstone 1.x S-parameter subset, 1/2 ports, positive real reference impedance.\nLimits: UTF-8 input file <=2 MiB, <=20000 frequency samples.\nFormat details: see docs/COMPATIBILITY.md in the source repository.\n\nCore SHA256: '+hashlib.sha256(core.encode()).hexdigest()+'\n',encoding='utf-8',newline='\n')
    shutil.copyfile(ROOT/'tools/verify_download.py',DIST/'verify_download.py')
    manifest = {
        'schema_version':1, 'project':'SParamKit', 'version':version,
        'source_commit':os.getenv('GITHUB_SHA','local-uncommitted'),
        'sha256':{p.relative_to(DIST).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
                  for p in (DIST/name for name in sorted(expected - {'manifest.json'}))},
    }
    (DIST/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    print('Built offline HTML, compiled MoonBit core, CLI and synthetic examples.')
    print('Core SHA256:',hashlib.sha256(core.encode()).hexdigest())

if __name__=='__main__': main()
