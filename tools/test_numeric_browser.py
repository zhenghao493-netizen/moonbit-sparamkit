#!/usr/bin/env python3
"""Exercise numerical edge-case readouts and full exports with the real core."""
import csv
import json
import os
from pathlib import Path
import shutil
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]
SOURCE = '# Hz S RI R 50\n1 1.7e308 1.7e308\n2 5e-324 5e-324\n3 0 0\n'


def main():
    engine = os.environ.get('BROWSER_NAME', 'chromium')
    if engine not in ('chromium', 'firefox', 'webkit'):
        raise ValueError('Unsupported browser')
    with sync_playwright() as p:
        options = {'headless': True}
        if engine == 'chromium':
            executable = os.environ.get('CHROMIUM_PATH') or shutil.which('chromium')
            if executable:
                options['executable_path'] = executable
            options['args'] = ['--no-sandbox']
        browser = getattr(p, engine).launch(**options)
        version = browser.version
        page = browser.new_page(accept_downloads=True)
        errors, requests = [], []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.on('request', lambda request: requests.append(request.url)
                if request.url.startswith(('http://', 'https://')) else None)
        if os.environ.get('TEST_CONTENT'):
            page.set_content((ROOT/'dist/index.html').read_text(encoding='utf-8'))
        else:
            page.goto((ROOT/'dist/index.html').as_uri())
        expect(page.locator('#count')).to_have_text('291')
        page.locator('#source').fill(SOURCE)
        page.locator('#ports').select_option('1')
        page.locator('#analyze').click()
        expect(page.locator('#count')).to_have_text('3')
        expect(page.locator('#status-title')).to_have_text('解析完成')
        expect(page.locator('#read-mag')).to_have_text('—')
        assert abs(float(page.locator('#read-db').inner_text())-6167.619278384205)<1e-5
        expect(page.locator('#read-phase')).to_have_text('45')
        page.locator('#sample-index').evaluate("el=>{el.value='1';el.dispatchEvent(new Event('input'))}")
        assert abs(float(page.locator('#read-db').inner_text())+6463.114006905676)<1e-5
        trace = page.locator('#magnitude .trace').get_attribute('d')
        assert trace and 'NaN' not in trace and 'Infinity' not in trace
        with page.expect_download() as download:
            page.locator('#json').click()
        report = json.loads(Path(download.value.path()).read_text(encoding='utf-8'))
        values = [row['values'][0] for row in report['samples']]
        assert values[0]['magnitude'] is None and abs(values[0]['db']-6167.619278384205)<1e-10
        assert values[1]['re']==5e-324 and abs(values[1]['db']+6463.114006905676)<1e-10
        assert values[2]['db'] is None and values[2]['phase_degrees'] is None
        with page.expect_download() as download:
            page.locator('#csv').click()
        with Path(download.value.path()).open(encoding='utf-8', newline='') as stream:
            rows = list(csv.DictReader(stream))
        assert len(rows)==3 and float(rows[0]['re'])==1.7e308 and float(rows[1]['im'])==5e-324
        assert not errors and not requests, (errors, requests)
        browser.close()
    result = {'status':'passed', 'browser':engine, 'browser_version':version,
              'mode':'injected-local-document' if os.environ.get('TEST_CONTENT') else 'file',
              'scenario':'overflow/subnormal/zero readouts with matching JSON and raw CSV export'}
    (ROOT/'verification').mkdir(exist_ok=True)
    (ROOT/'verification/numeric-browser-tests.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2))


if __name__ == '__main__':
    main()
