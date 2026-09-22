#!/usr/bin/env python3
"""Package compiled MoonBit bridge with a network-free UI; never reimplement parser."""
from pathlib import Path
import hashlib
import json
import math
import os
import shutil

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

def main():
    DIST.mkdir(exist_ok=True)
    compiled = ROOT/'_build/js/release/build/bridge/bridge.js'
    if not compiled.is_file():
        raise FileNotFoundError('Missing current compiled bridge; run moon build bridge --target js --release --deny-warn first. Refusing stale dist/core.cjs.')
    core = compiled.read_text(encoding='utf-8')
    shutil.copyfile(compiled,DIST/'core.cjs')
    if 'SParamKit' not in core:
        raise RuntimeError('Missing compiled bridge; run moon build bridge --target js --release --deny-warn')
    demo = examples()
    demo_dir = DIST/'samples'; demo_dir.mkdir(exist_ok=True)
    for key in ('two','one'):
        (demo_dir/demo[key]['name']).write_text(demo[key]['text'])
    if (ROOT/'samples').exists():
        for file in (ROOT/'samples').glob('*.s?p'):
            shutil.copyfile(file,demo_dir/file.name)
    template = (ROOT/'web/index.html').read_text()
    replacements = {
        '/*__STYLE__*/': (ROOT/'web/style.css').read_text(),
        '/*__CORE__*/': core.replace('</script', '<\\/script'),
        '/*__DEMOS__*/': json.dumps(demo,ensure_ascii=False).replace('<','\\u003c'),
        '/*__APP__*/': (ROOT/'web/app.js').read_text(),
        '__BUILD__': os.getenv('GITHUB_SHA','local')[:12],
    }
    for marker, content in replacements.items():
        assert template.count(marker)==1, marker
        template=template.replace(marker,content)
    (DIST/'index.html').write_text(template)
    shutil.copyfile(ROOT/'tools/cli.cjs',DIST/'cli.cjs')
    if (ROOT/'LICENSE').exists(): shutil.copyfile(ROOT/'LICENSE',DIST/'LICENSE')
    (DIST/'READ_ME.txt').write_text('SParamKit development preview\n\nOpen index.html in a modern browser (Chrome/Edge recommended).\nThe single HTML file works offline; it does not send data over the network.\nBuilt-in examples are synthetic, not instrument measurements.\n\nCLI: node cli.cjs samples/synthetic_notch.s2p --format json\nCSV: node cli.cjs samples/synthetic_notch.s2p --format csv\n\nStrict Touchstone 1.x S-parameter subset, 1/2 ports, positive real reference impedance.\nLimits: UTF-8 input file <=2 MiB, <=20000 frequency samples.\nThis is not an instrument calibration or full standards-conformance tool.\n\nCore SHA256: '+hashlib.sha256(core.encode()).hexdigest()+'\n')
    print('Built offline HTML, compiled MoonBit core, CLI and synthetic examples.')
    print('Core SHA256:',hashlib.sha256(core.encode()).hexdigest())

if __name__=='__main__': main()
