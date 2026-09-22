#!/usr/bin/env python3
"""Exercise the shipped offline HTML in Chromium, not a mock renderer."""
from pathlib import Path
import json
import os
import shutil
from playwright.sync_api import sync_playwright, expect

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'verification'; OUT.mkdir(exist_ok=True)

def main():
    checks=[]
    url=os.environ.get('TEST_URL') or (ROOT/'dist/index.html').as_uri()
    with sync_playwright() as p:
        executable=os.environ.get('CHROMIUM_PATH') or shutil.which('chromium')
        browser=p.chromium.launch(executable_path=executable,headless=True,args=['--no-sandbox'])
        context=browser.new_context(viewport={'width':1440,'height':1160},accept_downloads=True)
        page=context.new_page(); errors=[]; requests=[]
        page.on('pageerror',lambda e: errors.append(str(e)))
        page.on('request',lambda r: requests.append(r.url) if r.url.startswith(('http://','https://')) and r.url != url else None)
        if os.environ.get('TEST_CONTENT'):
            page.set_content((ROOT/'dist/index.html').read_text())
        else:
            page.goto(url)
        expect(page.locator('#status-title')).to_have_text('解析完成')
        expect(page.locator('#count')).to_have_text('291')
        expect(page.locator('#magnitude .trace')).to_have_count(1)
        expect(page.locator('#phase .trace')).to_have_count(1)
        checks.append('compiled-core 291-point synthetic two-port startup')
        page.screenshot(path=str(OUT/'ui-desktop.png'),full_page=True)
        page.locator('#parameter').select_option('S12')
        expect(page.locator('#table-note')).to_contain_text('S12')
        checks.append('parameter switching')
        page.locator('#scale').select_option('log')
        expect(page.locator('#magnitude .trace')).to_have_count(1)
        checks.append('log frequency axis')
        page.locator('#next').click(); expect(page.locator('#table-note')).to_contain_text('9–16')
        page.locator('#prev').click(); expect(page.locator('#table-note')).to_contain_text('1–8')
        checks.append('table pagination')
        with page.expect_download() as info: page.locator('#json').click()
        result=json.loads(Path(info.value.path()).read_text())
        assert result['ok'] and result['sample_count']==291
        checks.append('JSON export all 291 samples')
        with page.expect_download() as info: page.locator('#csv').click()
        lines=Path(info.value.path()).read_text().splitlines()
        assert lines[0]=='frequency_hz,reference_ohms,output_port,input_port,re,im'
        assert len(lines)==1+291*4
        checks.append('MoonBit CSV export all four S parameters')
        page.locator('#source').fill('# Hz S RI R 50\n0 0 0\n1 .3 -.4\n')
        expect(page.locator('#csv')).to_be_disabled()
        expect(page.locator('#magnitude .trace')).to_have_count(0)
        page.locator('#ports').select_option('1'); page.locator('#analyze').click()
        expect(page.locator('#status-title')).to_have_text('解析完成')
        expect(page.locator('#count')).to_have_text('2')
        expect(page.locator('#plot-note')).to_contain_text('省略 1 个 0 Hz')
        checks.append('edit invalidates old data, zero Hz omitted only on log axis')
        with page.expect_download() as info: page.locator('#json').click()
        result=json.loads(Path(info.value.path()).read_text())
        assert result['samples'][0]['values'][0]['db'] is None
        assert result['samples'][0]['values'][0]['phase_degrees'] is None
        checks.append('undefined zero-magnitude metrics remain JSON null')
        page.locator('#demo-error').click()
        expect(page.locator('#status-title')).to_have_text('输入未通过检查')
        expect(page.locator('#status-detail')).to_contain_text('IncompleteRecord')
        expect(page.locator('#csv')).to_be_disabled()
        expect(page.locator('#json')).to_be_disabled()
        expect(page.locator('#magnitude .trace')).to_have_count(0)
        checks.append('malformed input produces diagnostic and clears stale curves/exports')
        page.locator('#file').set_input_files(str(ROOT/'dist/samples/synthetic_rc.s1p'))
        expect(page.locator('#status-title')).to_have_text('解析完成')
        expect(page.locator('#count')).to_have_text('161')
        expect(page.locator('#ports')).to_have_value('1')
        expect(page.locator('#parameter option')).to_have_count(1)
        checks.append('actual .s1p file input auto-selects one port')
        page.locator('#file').set_input_files({'name':'bom_cr.s1p','mimeType':'text/plain','buffer':b'\xef\xbb\xbf# Hz S RI R 50\r1 .3 -.4\r2 0 0\r'})
        expect(page.locator('#status-title')).to_have_text('解析完成')
        expect(page.locator('#count')).to_have_text('2')
        checks.append('actual BOM and CR-only file input')
        page.locator('#file').set_input_files({'name':'large.s2p','mimeType':'text/plain','buffer':b'!'*(2*1024*1024+1)})
        expect(page.locator('#status-title')).to_have_text('文件过大')
        expect(page.locator('#csv')).to_be_disabled()
        checks.append('oversize input rejected before parse')
        page.locator('#file').set_input_files({'name':'invalid_utf8.s1p','mimeType':'text/plain','buffer':b'\xff\xfe\x00'})
        expect(page.locator('#status-title')).to_have_text('文件读取失败')
        checks.append('invalid UTF-8 rejected')
        page.locator('#demo-one').click()
        expect(page.locator('#status-title')).to_have_text('解析完成')
        expect(page.locator('#count')).to_have_text('161')
        checks.append('successful recovery after errors')
        page.set_viewport_size({'width':390,'height':844})
        page.wait_for_timeout(100)
        assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
        page.screenshot(path=str(OUT/'ui-mobile.png'),full_page=True)
        checks.append('390px mobile layout without horizontal page overflow')
        assert not errors,errors
        assert not requests,requests
        checks.append('no page exceptions and no network requests')
        browser.close()
    summary={'status':'passed','mode': 'injected-local-document' if os.environ.get('TEST_CONTENT') else ('file' if url.startswith('file:') else 'served'),'checks':len(checks),'details':checks}
    (OUT/'browser-tests.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(summary,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
