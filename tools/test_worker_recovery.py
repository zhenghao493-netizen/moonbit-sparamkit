#!/usr/bin/env python3
"""Inject worker transport faults; successful requests still use the MoonBit core."""
from __future__ import annotations
import csv
import io
import json
import os
from pathlib import Path
import shutil
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]
SOURCE = '# Hz S RI R 50\n1 .3 -.4\n2 0 0\n'
HOOKS = r'''(() => {
  const NativeWorker = window.Worker;
  const nativeSet = window.setTimeout, nativeClear = window.clearTimeout;
  const create = URL.createObjectURL.bind(URL), revoke = URL.revokeObjectURL.bind(URL);
  const h = window.__workerFaults = {
    construct: 0, startup: 0, send: 0, hold: false, attempts: 0,
    workers: [], held: [], timers: new Map(), blobs: new Set(), retired: 0
  };
  URL.createObjectURL = blob => { const url = create(blob); h.blobs.add(url); return url; };
  URL.revokeObjectURL = url => { h.blobs.delete(url); return revoke(url); };
  window.setTimeout = (fn, delay, ...args) => {
    const id = nativeSet(() => { h.timers.delete(id); fn(...args); }, delay);
    if (delay === 15000) h.timers.set(id, () => fn(...args));
    return id;
  };
  window.clearTimeout = id => { h.timers.delete(id); nativeClear(id); };
  window.Worker = class extends NativeWorker {
    constructor(url, options) {
      h.attempts++;
      if (h.construct > 0) {
        h.construct--;
        throw new DOMException('Injected constructor failure', 'SecurityError');
      }
      if (h.startup > 0) {
        h.startup--;
        const bad = create(new Blob(["throw new Error('Injected worker startup failure')"], {type:'text/javascript'}));
        super(bad, options); revoke(bad);
      } else { super(url, options); }
      h.workers.push(this);
    }
    postMessage(...args) {
      if (h.send > 0) { h.send--; throw new DOMException('Injected send failure', 'DataCloneError'); }
      if (h.hold) { h.held.push([this, args]); return; }
      return super.postMessage(...args);
    }
    terminate() { h.retired++; return super.terminate(); }
  };
  h.release = () => {
    h.hold = false;
    const held = h.held.splice(0);
    for (const [target, args] of held) NativeWorker.prototype.postMessage.apply(target, args);
  };
  h.expire = () => {
    const entries = [...h.timers];
    for (const [id, fn] of entries) { window.clearTimeout(id); fn(); }
  };
})();'''


def load_small(page):
    expect(page.locator('#count')).to_have_text('291')
    page.locator('#source').fill(SOURCE)
    page.locator('#ports').select_option('1')
    page.locator('#analyze').click()
    small_ok(page)


def small_ok(page):
    expect(page.locator('#count')).to_have_text('2')
    expect(page.locator('#status-title')).to_have_text('解析完成')
    expect(page.locator('#read-re')).to_have_text('0.3')
    expect(page.locator('#read-im')).to_have_text('-0.4')
    expect(page.locator('#analyze')).to_be_enabled()


def analysis_failed(page):
    expect(page.locator('#status-title')).to_have_text('计算失败')
    expect(page.locator('#count')).to_have_text('—')
    expect(page.locator('#csv')).to_be_disabled()
    expect(page.locator('#json')).to_be_disabled()
    expect(page.locator('#analyze')).to_be_enabled()


def constructor_recovery(page):
    analysis_failed(page)
    assert page.evaluate('__workerFaults.blobs.size') == 0
    assert page.evaluate('__workerFaults.timers.size') == 0
    text = page.locator('#source').input_value()
    page.locator('#analyze').click()
    expect(page.locator('#count')).to_have_text('291')
    assert page.locator('#source').input_value() == text
    assert page.evaluate('__workerFaults.attempts') == 2


def startup_recovery(page):
    analysis_failed(page)
    assert page.evaluate('__workerFaults.retired') == 1
    page.locator('#analyze').click()
    expect(page.locator('#count')).to_have_text('291')
    assert page.evaluate('__workerFaults.attempts') == 2


def send_recovery(page):
    load_small(page)
    page.evaluate('__workerFaults.send = 1')
    page.locator('#analyze').click()
    analysis_failed(page)
    assert page.evaluate('__workerFaults.timers.size') == 0
    assert page.locator('#source').input_value() == SOURCE
    page.locator('#analyze').click()
    small_ok(page)


def csv_recovery(page):
    load_small(page)
    page.evaluate('__workerFaults.send = 1')
    page.locator('#csv').click()
    expect(page.locator('#status-title')).to_have_text('导出失败')
    expect(page.locator('#csv')).to_be_enabled()
    expect(page.locator('#count')).to_have_text('2')
    assert page.evaluate('__workerFaults.timers.size') == 0
    with page.expect_download() as download:
        page.locator('#csv').click()
    rows = list(csv.DictReader(io.StringIO(Path(download.value.path()).read_text(encoding='utf-8'))))
    assert len(rows) == 2 and float(rows[0]['re']) == .3 and float(rows[0]['im']) == -.4
    with page.expect_download() as download:
        page.locator('#json').click()
    report = json.loads(Path(download.value.path()).read_text(encoding='utf-8'))
    assert report['sample_count'] == 2 and report['samples'][0]['values'][0]['magnitude'] == .5


def message_recovery(page):
    load_small(page)
    page.evaluate('__workerFaults.hold = true')
    page.locator('#analyze').click()
    page.evaluate("__workerFaults.workers.at(-1).dispatchEvent(new MessageEvent('messageerror'))")
    analysis_failed(page)
    assert page.evaluate('__workerFaults.timers.size') == 0
    page.evaluate('__workerFaults.release()')
    page.locator('#analyze').click()
    small_ok(page)


def timeout_recovery(page):
    load_small(page)
    page.evaluate('__workerFaults.hold = true')
    page.locator('#analyze').click()
    attempts = page.evaluate('__workerFaults.attempts')
    # Expire the actual deadline callback without a 15-second wall-clock wait.
    page.evaluate('__workerFaults.construct = 1; __workerFaults.expire()')
    analysis_failed(page)
    assert page.evaluate('__workerFaults.attempts') == attempts
    assert page.evaluate('__workerFaults.timers.size') == 0
    page.locator('#analyze').click()  # Constructor still fails, but no uncaught error.
    analysis_failed(page)
    assert page.evaluate('__workerFaults.blobs.size') == 0
    page.evaluate('__workerFaults.release()')
    page.locator('#analyze').click()
    small_ok(page)


def stale_error(page):
    load_small(page)
    page.evaluate('''__workerFaults.oldError = __workerFaults.workers.at(-1).onerror;
      __workerFaults.hold = true;''')
    page.locator('#analyze').click()
    page.evaluate("__workerFaults.oldError(new Event('error', {cancelable:true}))")
    analysis_failed(page)
    page.locator('#analyze').click()  # Replacement request remains held.
    retired = page.evaluate('__workerFaults.retired')
    page.evaluate("__workerFaults.oldError(new Event('error', {cancelable:true}))")
    expect(page.locator('#status-title')).to_have_text('正在解析')
    expect(page.locator('#analyze')).to_be_disabled()
    assert page.evaluate('__workerFaults.retired') == retired
    assert page.evaluate('__workerFaults.timers.size') == 1
    page.evaluate('__workerFaults.release()')
    small_ok(page)


def repeated_failure(page):
    analysis_failed(page)
    for _ in range(2):
        page.locator('#analyze').click()
        analysis_failed(page)
    assert page.evaluate('__workerFaults.attempts') == 3
    assert page.evaluate('__workerFaults.timers.size') == 0
    assert page.evaluate('__workerFaults.blobs.size') == 0
    page.locator('#analyze').click()
    expect(page.locator('#count')).to_have_text('291')
    assert page.evaluate('__workerFaults.attempts') == 4


def main():
    engine = os.environ.get('BROWSER_NAME', 'chromium')
    if engine not in ('chromium', 'firefox', 'webkit'):
        raise ValueError('Unsupported browser')
    scenarios = [
        ('constructor failure releases URL and allows retry', {'construct': 1}, constructor_recovery),
        ('real worker startup error recovers without page reload', {'startup': 1}, startup_recovery),
        ('failed postMessage clears deadline and preserves input', {}, send_recovery),
        ('failed CSV transport can retry and exports the original values', {}, csv_recovery),
        ('messageerror cancels pending work and allows retry', {}, message_recovery),
        ('timeout and failed restart are both recoverable', {}, timeout_recovery),
        ('retired worker error cannot cancel replacement request', {}, stale_error),
        ('repeated constructor failures do not leak URLs or auto-loop', {'construct': 3}, repeated_failure),
    ]
    results = []
    with sync_playwright() as p:
        options = {'headless': True}
        if engine == 'chromium':
            executable = os.environ.get('CHROMIUM_PATH') or shutil.which('chromium')
            if executable:
                options['executable_path'] = executable
            options['args'] = ['--no-sandbox']
        browser = getattr(p, engine).launch(**options)
        version = browser.version
        for name, flags, test in scenarios:
            page = browser.new_page(accept_downloads=True)
            errors, requests = [], []
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.on('request', lambda req: requests.append(req.url)
                    if req.url.startswith(('http://', 'https://')) else None)
            item = {'name': name, 'status': 'failed'}
            try:
                init = HOOKS + '\nObject.assign(__workerFaults, ' + json.dumps(flags) + ');'
                if os.environ.get('TEST_CONTENT'):
                    page.evaluate(init + '\nvoid 0;')
                    page.set_content((ROOT/'dist/index.html').read_text(encoding='utf-8'))
                else:
                    page.add_init_script(init)
                    page.goto((ROOT/'dist/index.html').as_uri())
                test(page)
                assert page.evaluate('__workerFaults.timers.size') == 0
                assert not errors and not requests, (errors, requests)
                item['status'] = 'passed'
            except Exception as exc:
                item['error'] = f'{type(exc).__name__}: {exc}'
            finally:
                page.close()
            results.append(item)
        browser.close()
    report = {'status': 'passed' if all(x['status'] == 'passed' for x in results) else 'failed',
              'browser': engine, 'browser_version': version,
              'mode': 'injected-local-document' if os.environ.get('TEST_CONTENT') else 'file',
              'checks': len(results), 'details': results,
              'fault_model': 'Worker creation/send/events/deadlines only; successful replies use compiled MoonBit'}
    (ROOT/'verification').mkdir(exist_ok=True)
    (ROOT/'verification/worker-tests.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(report, indent=2))
    return 0 if report['status'] == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
