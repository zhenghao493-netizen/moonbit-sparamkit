#!/usr/bin/env python3
"""Final review of the already delivered RC3 ZIP, without changing its payload."""
import argparse
import csv
import hashlib
import io
import json
import math
import os
from pathlib import Path, PurePosixPath
import shutil
import stat
import subprocess
import sys
import tempfile
import time
import zipfile
from playwright.sync_api import sync_playwright, expect

ZIP_SHA = '5df833a1120e009b388a665eb4634781c5ab1ce8b1cde84e0ed7e828e7fb1555'
VERSION = '0.1.0-rc.3'

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def walkthrough(bundle, out, injected=False):
    checks, errors, requests = [], [], []
    expected = [(complex(.3,-.4), complex(0,1), complex(-.2,0), complex(.1,.1)),
                (complex(.2,.2), complex(.6,-.8), complex(.1,0), complex(-.3,.4))]
    with sync_playwright() as p:
        options = {'headless': True, 'args': ['--no-sandbox']}
        executable = os.getenv('CHROMIUM_PATH') or shutil.which('chromium')
        if executable: options['executable_path'] = executable
        browser = p.chromium.launch(**options)
        context = browser.new_context(accept_downloads=True, offline=True,
                                      viewport={'width':1440, 'height':1100})
        page = context.new_page()
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.on('request', lambda req: requests.append(req.url) if req.url.startswith(('http:', 'https:')) else None)
        try:
            if injected:
                page.set_content((bundle/'workbench/index.html').read_text(encoding='utf-8'))
            else:
                page.goto((bundle/'index.html').as_uri())
                expect(page.locator('.version')).to_have_text(VERSION)
                page.screenshot(path=str(out/'review-home.png'), full_page=True)
                page.locator('#open-workbench').focus(); page.keyboard.press('Enter')
                checks.append('offline review homepage opens the delivered workbench with keyboard')
            expect(page.locator('#count')).to_have_text('291')
            page.locator('#demo-one').click(); expect(page.locator('#count')).to_have_text('161')
            page.locator('#demo-two').click(); expect(page.locator('#count')).to_have_text('291')
            checks.append('both bundled demonstrations load without a network connection')
            for representation in ('RI', 'MA', 'DB'):
                lines = [f'# MHz S {representation} R 75']
                for frequency, values in enumerate(expected, 1):
                    fields = [str(frequency)]
                    for z in values:
                        pair = (z.real,z.imag) if representation == 'RI' else (
                            abs(z) if representation == 'MA' else 20*math.log10(abs(z)),
                            math.degrees(math.atan2(z.imag,z.real)))
                        fields.extend(format(v,'.17g') for v in pair)
                    lines.append(' '.join(fields))
                input_file = out/f'非对称 双端口-{representation}.s2p'
                input_file.write_text('\n'.join(lines)+'\n',encoding='utf-8')
                page.locator('#file').set_input_files(str(input_file))
                expect(page.locator('#status-title')).to_have_text('解析完成')
                expect(page.locator('#impedance')).to_have_text('75 Ω')
                page.locator('#sample-index').focus(); page.keyboard.press('End')
                expect(page.locator('#read-f')).to_have_text('2000000')
                page.locator('#parameter').select_option('S12')
                assert math.isclose(float(page.locator('#read-re').get_attribute('title')), .1, abs_tol=1e-12)
                page.locator('#parameter').select_option('S21')
                assert math.isclose(float(page.locator('#read-im').get_attribute('title')), -.8, abs_tol=1e-12)
                with page.expect_download() as download: page.locator('#json').click()
                json_file = out/f'{representation}-export.json'; download.value.save_as(json_file)
                report = json.loads(json_file.read_text(encoding='utf-8'))
                assert report['ok'] and report['ports'] == 2 and report['sample_count'] == 2
                assert report['reference_ohms'] == 75
                for i, sample in enumerate(report['samples']):
                    assert sample['frequency_hz'] == (i+1)*1e6
                    for parameter, z in zip(('S11','S21','S12','S22'),expected[i]):
                        value = next(v for v in sample['values'] if v['parameter']==parameter)
                        assert math.isclose(value['re'],z.real,abs_tol=1e-12)
                        assert math.isclose(value['im'],z.imag,abs_tol=1e-12)
                with page.expect_download() as download: page.locator('#csv').click()
                csv_file = out/f'{representation}-export.csv'; download.value.save_as(csv_file)
                rows = list(csv.DictReader(io.StringIO(csv_file.read_text(encoding='utf-8'))))
                assert len(rows) == 8
                for row in rows:
                    i = int(float(row['frequency_hz'])/1e6)-1
                    k = (int(row['input_port'])-1)*2+int(row['output_port'])-1
                    assert float(row['reference_ohms']) == 75
                    assert math.isclose(float(row['re']),expected[i][k].real,abs_tol=1e-12)
                    assert math.isclose(float(row['im']),expected[i][k].imag,abs_tol=1e-12)
                checks.append(representation+' import, 75-ohm reference, S12/S21 readout and complete JSON/CSV agree')
            page.locator('#source').fill('# Hz S RI R 50\n1 .3 nope\n')
            expect(page.locator('#csv')).to_be_disabled()
            page.locator('#ports').select_option('1'); page.locator('#analyze').click()
            expect(page.locator('#status-title')).to_have_text('输入未通过检查')
            page.locator('#locate-error').click()
            selected = page.locator('#source').evaluate('(e)=>e.value.slice(e.selectionStart,e.selectionEnd)')
            assert selected == 'nope'
            expect(page.locator('#json')).to_be_disabled()
            checks.append('malformed field is selected precisely and stale exports are disabled')
            page.locator('#source').fill('# Hz S RI R 50\n0 0 0\n1 .3 -.4\n')
            page.locator('#analyze').click(); expect(page.locator('#count')).to_have_text('2')
            page.locator('#scale').select_option('log')
            with page.expect_download() as download: page.locator('#json').click()
            report = json.loads(Path(download.value.path()).read_text(encoding='utf-8'))
            assert report['samples'][0]['frequency_hz'] == 0
            assert report['samples'][0]['values'][0]['db'] is None
            assert report['samples'][0]['values'][0]['phase_degrees'] is None
            checks.append('repair succeeds; log-axis zero remains in export and undefined values stay null')
            conflict = '# Hz S RI R 50\n1 .3 -.4\n! Port Impedance 75 0\n'
            page.locator('#source').fill(conflict); page.locator('#analyze').click()
            expect(page.locator('#status-detail')).to_contain_text('UnsupportedMetadata')
            expect(page.locator('#impedance')).to_have_text('—')
            expect(page.locator('#csv')).to_be_disabled()
            page.locator('#demo-two').click(); expect(page.locator('#count')).to_have_text('291')
            checks.append('conflicting impedance is rejected and a normal demonstration recovers')
            page.screenshot(path=str(out/'workbench-desktop.png'),full_page=True)
            page.set_viewport_size({'width':390,'height':844})
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
            page.screenshot(path=str(out/'workbench-390px.png'),full_page=True)
            checks.append('390px viewport has no horizontal overflow')
            assert not errors and not requests, (errors, requests)
            checks.append('no page exceptions or HTTP(S) requests in the walkthrough')
            return {'status':'passed','mode':'injected-local-document' if injected else 'file',
                    'browser':browser.version,'checks':checks}
        finally:
            context.close(); browser.close()

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('archive',type=Path)
    parser.add_argument('--out',type=Path,default=Path('review-results'))
    parser.add_argument('--walkthrough-only',action='store_true')
    parser.add_argument('--injected',action='store_true')
    args=parser.parse_args(); out=args.out.resolve(); out.mkdir(parents=True,exist_ok=True)
    report={'status':'failed','version':VERSION,'archive_sha256':digest(args.archive),'stages':[]}
    try:
        assert report['archive_sha256']==ZIP_SHA, 'Unexpected candidate ZIP'
        with tempfile.TemporaryDirectory(prefix='sparamkit-final-') as temp:
            root=Path(temp)/'终检 with spaces'; root.mkdir()
            with zipfile.ZipFile(args.archive) as archive:
                names=archive.namelist(); assert len(names)==len(set(names))
                for item in archive.infolist():
                    name=PurePosixPath(item.filename)
                    assert not name.is_absolute() and '..' not in name.parts and '\\' not in item.filename
                    assert not stat.S_ISLNK(item.external_attr>>16)
                archive.extractall(root)
            bundle=root/f'SParamKit-{VERSION}'
            original={p.relative_to(bundle).as_posix():digest(p) for p in bundle.rglob('*') if p.is_file()}
            env=dict(os.environ)
            for name in ('TEST_URL','TEST_CONTENT'): env.pop(name,None)
            def run(label,args,cwd):
                start=time.monotonic()
                proc=subprocess.run(args,cwd=cwd,env=env,text=True,encoding='utf-8',errors='replace',
                                    capture_output=True,timeout=360)
                (out/f'{label}.log').write_text(proc.stdout+'\n'+proc.stderr,encoding='utf-8')
                report['stages'].append({'name':label,'exit_code':proc.returncode,'seconds':round(time.monotonic()-start,2)})
                assert proc.returncode==0, label+' failed; inspect its log'
                return proc.stdout
            integrity=json.loads(run('delivered-integrity',[sys.executable,'verify_download.py'],bundle))
            report['payload_files_verified']=integrity['files_checked']
            report['walkthrough']=walkthrough(bundle,out,args.injected)
            if not args.walkthrough_only:
                source=root/'rebuild'; shutil.copytree(bundle/'source',source)
                shutil.copytree(bundle/'workbench',source/'dist')
                for label,script in [('original-browser','test_browser.py'),('original-worker','test_worker_recovery.py'),
                                     ('original-numeric-browser','test_numeric_browser.py')]:
                    run(label,[sys.executable,'tools/'+script],source)
                run('toolchain',['moon','version','--all'],source)
                run('core',['bash','tools/verify.sh'],source)
                run('bridge',['moon','build','bridge','--target','js','--release','--deny-warn'],source)
                report['original_core_sha256']=digest(bundle/'workbench/core.cjs')
                report['rebuilt_core_sha256']=digest(source/'_build/js/release/build/bridge/bridge.js')
                report['rebuilt_core_matches_delivery']=report['original_core_sha256']==report['rebuilt_core_sha256']
                for label,script in [('host','test_host.py'),('documentation','test_documentation.py'),
                    ('numeric','test_numeric.py'),('synthetic','crosscheck.py'),('public-files','test_measured.py'),
                    ('source-package','check_package.py')]:
                    run(label,[sys.executable,'tools/'+script],source)
                for path in (source/'verification').glob('*.json'):
                    shutil.copyfile(path,out/path.name)
            assert original=={p.relative_to(bundle).as_posix():digest(p) for p in bundle.rglob('*') if p.is_file()}
            report['original_payload_unchanged']=True
            report['status']='passed'
    except Exception as exc:
        report['error']=type(exc).__name__+': '+str(exc)
    (out/'final-review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))
    return 0 if report['status']=='passed' else 1

if __name__=='__main__': sys.exit(main())
