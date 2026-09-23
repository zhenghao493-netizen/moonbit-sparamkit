#!/usr/bin/env python3
"""Build and exercise the offline entry page inside a staged submission bundle."""
from __future__ import annotations
import argparse
from html import escape
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import shutil
import sys
import tomllib
from urllib.parse import unquote, urlsplit


class LocalLinks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        for key, value in attrs:
            if tag == 'a' and key == 'href' and value:
                self.links.append(value)


def render(stage: Path) -> tuple[str, str, int]:
    version = tomllib.loads((stage/'source/moon.mod').read_text(encoding='utf-8'))['version']
    manifest = json.loads((stage/'workbench/manifest.json').read_text(encoding='utf-8'))
    if manifest['version'] != version:
        raise ValueError('Workbench and source versions differ')
    rows = []
    for target in ('js', 'wasm-gc'):
        text = (stage/f'reports/logs/test-{target}.log').read_text(encoding='utf-8')
        matches = re.findall(r'Total tests: (\d+), passed: (\d+), failed: (\d+)\.', text)
        if len(matches) != 1 or int(matches[0][0]) <= 0 or matches[0][0] != matches[0][1] or matches[0][2] != '0':
            raise ValueError('Missing successful core test summary: ' + target)
        total, passed, _ = matches[0]
        rows.append((f'MoonBit / {target}', f'{passed} / {total}', f'reports/logs/test-{target}.log'))
    for name, label, describe in (
        ('browser-tests.json', '离线交互', lambda r: f"{r['checks']} 项通过"),
        ('worker-tests.json', '异常恢复', lambda r: f"{r['checks']} 项通过"),
        ('crosscheck.json', '独立数值对照', lambda r: f"{r['cases']} 份合成文件"),
        ('measured-files.json', '公开文件对照', lambda r: f"{len(r['files'])} 份文件"),
        ('documentation-tests.json', '文档示例', lambda r: f"{r['distinct_examples']} 份示例 × {len(r['executed_targets'])} 个后端"),
        ('package-check.json', '源码包重建', lambda r: '通过'),
    ):
        report = json.loads((stage/'reports'/name).read_text(encoding='utf-8'))
        if report.get('status') != 'passed':
            raise ValueError('A report has not passed: ' + name)
        if name in ('browser-tests.json', 'worker-tests.json') and report.get('mode') != 'file':
            raise ValueError('Reviewer page requires file-mode browser evidence')
        rows.append((label, describe(report), 'reports/' + name))
    table = ''.join(f'<tr><th scope="row">{escape(label)}</th><td>{escape(result)}</td>'
                    f'<td><a href="{escape(link)}">查看记录</a></td></tr>' for label, result, link in rows)
    page = '''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>SParamKit · 项目演示</title><style>
:root{color-scheme:light;font-family:system-ui,-apple-system,"Segoe UI",sans-serif;color:#1e3038;background:#f4f6f5;line-height:1.7}*{box-sizing:border-box}body{margin:0}main{max-width:1000px;margin:auto;padding:48px 28px}header{padding:28px 0}h1{font-size:clamp(30px,5vw,48px);line-height:1.2;margin:12px 0}h2{font-size:22px;margin:0 0 12px}p{margin:10px 0}.eyebrow{color:#126e60;font-weight:650;letter-spacing:.1em}.version{display:inline-block;border:1px solid #c4d7d0;border-radius:30px;padding:3px 12px;font-size:14px}a{color:#096b5c;text-underline-offset:3px}a:focus-visible{outline:3px solid #244dd8;outline-offset:4px}.button{display:inline-block;background:#126e60;color:white;text-decoration:none;padding:13px 24px;border-radius:9px;font-weight:650;margin:12px 0}section{background:white;border:1px solid #dee5e1;border-radius:12px;padding:24px;margin:20px 0}.meta{color:#506068;font-size:14px}.grid{display:grid;grid-template-columns:1fr 1fr;gap:20px}.grid section{margin:0}li{margin:8px 0}ol,ul{padding-left:24px}table{border-collapse:collapse;width:100%;font-size:15px}th,td{text-align:left;padding:10px 8px;border-bottom:1px solid #e4e9e6}th{font-weight:550}code{font-size:.92em;overflow-wrap:anywhere}footer{padding-top:20px;overflow-wrap:anywhere}details{margin-top:16px}summary{cursor:pointer;font-weight:600}@media(max-width:600px){main{padding:20px 16px}.grid{grid-template-columns:1fr}section{padding:18px}th,td{padding:9px 4px;font-size:13px}.button{display:block;text-align:center}}
</style></head><body><main>
<header><div class="eyebrow">MOONBIT · 数据处理</div><h1>SParamKit</h1>
<span class="version">__VERSION__</span><p>导入 Touchstone 文件，检查数据、读取曲线并导出 CSV / JSON。</p>
<a class="button" id="open-workbench" href="workbench/index.html">打开离线工作台 →</a>
<p class="meta">直接用桌面浏览器打开，无需安装开发环境或启动服务器。请先完整解压验收包。</p></header>
<div class="grid"><section><h2>五分钟演示</h2><ol>
<li>查看默认双端口陷波样例，切换 S21 / S11 和频率轴。</li>
<li>用曲线、滑块或方向键读取某个频点，切换参数进行对比。</li>
<li>导入自己的 <code>.s1p</code> / <code>.s2p</code>，导出 CSV 和 JSON。</li>
<li>打开错误样例，定位字段，再切回正常输入。</li></ol>
<p class="meta">内置 RC / RLC 样例为合成电路数据。</p></section>
<section><h2>阅读与复现</h2><ul>
<li><a href="source/README.md">项目说明与快速上手</a></li>
<li><a href="source/docs/SUBMISSION.md">申报功能与实现位置</a></li>
<li><a href="source/docs/ARCHITECTURE.md">架构与关键设计</a></li>
<li><a href="source/docs/ACCEPTANCE.md">完整测试与构建命令</a></li>
<li><a href="source/docs/COMPATIBILITY.md">支持的格式与输入限制</a></li></ul>
<p class="meta">Markdown 文档可用文本编辑器阅读。核心计算由 MoonBit 实现，浏览器和 CLI 共用同一核心库。</p></section></div>
<section><h2>本包检查结果</h2><p class="meta">以下摘要读取本次构建的报告；点击记录可核对详细结果。</p>
<table><thead><tr><th scope="col">检查项</th><th scope="col">结果</th><th scope="col">详情</th></tr></thead><tbody>__TABLE__</tbody></table>
<details><summary>从源码复现</summary><p>进入 <code>source/</code>，按验收指南安装 MoonBit、Node.js、Python 和测试依赖，再执行：</p>
<pre><code>python tools/prepare_submission.py</code></pre>
<p>只使用工作台时不需要这些依赖。修改源码前可在解压根目录执行 <code>python verify_download.py</code> 核对文件清单。</p></details></section>
<footer class="meta">MIT License · 源码标识 <code>__COMMIT__</code></footer>
</main></body></html>'''
    page = page.replace('__VERSION__', escape(version)).replace('__TABLE__', table).replace('__COMMIT__', escape(manifest['source_commit']))
    links = LocalLinks(); links.feed(page)
    for link in links.links:
        parsed = urlsplit(link)
        target = (stage/unquote(parsed.path)).resolve()
        if parsed.scheme or parsed.netloc or not target.is_relative_to(stage) or not target.is_file():
            raise ValueError('Broken or external review-page link: ' + link)
    (stage/'index.html').write_text(page, encoding='utf-8', newline='\n')
    return page, version, len(links.links)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('stage', type=Path)
    parser.add_argument('--build-only', action='store_true')
    args = parser.parse_args()
    stage = args.stage.resolve()
    report = {'status': 'failed', 'mode': 'file', 'details': []}
    try:
        page_text, version, count = render(stage)
        report['local_links'] = count
        if args.build_only:
            print(json.dumps({'status':'generated', 'page': str(stage/'index.html'), 'browser_test': 'not run'}))
            return 0
        from playwright.sync_api import sync_playwright, expect
        with sync_playwright() as playwright:
            options = {'headless': True, 'args': ['--no-sandbox']}
            executable = os.environ.get('CHROMIUM_PATH') or shutil.which('chromium')
            if executable:
                options['executable_path'] = executable
            browser = playwright.chromium.launch(**options)
            report['browser_version'] = browser.version
            page = browser.new_page(viewport={'width': 1280, 'height': 900})
            errors, requests = [], []
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.on('request', lambda request: requests.append(request.url) if request.url.startswith(('http:', 'https:')) else None)
            try:
                page.goto((stage/'index.html').as_uri())
                expect(page.locator('.version')).to_have_text(version)
                expect(page.locator('tbody tr')).to_have_count(8)
                report['details'].append('review page displays the bundle version and eight report summaries')
                page.screenshot(path=str(stage/'reports/review-desktop.png'), full_page=True)
                page.locator('#open-workbench').focus()
                page.keyboard.press('Enter')
                expect(page.locator('#count')).to_have_text('291')
                expect(page.locator('#status-title')).to_have_text('解析完成')
                report['details'].append('keyboard navigation opens the real bundled MoonBit workbench')
                page.go_back()
                page.set_viewport_size({'width':390, 'height':844})
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
                page.screenshot(path=str(stage/'reports/review-mobile.png'), full_page=True)
                report['details'].append('390px review page has no horizontal overflow')
                assert not errors and not requests, (errors, requests)
                report['details'].append('review and workbench navigation have no page errors or network requests')
            finally:
                browser.close()
        report.update(status='passed', checks=len(report['details']))
    except Exception as exc:
        report['error'] = f'{type(exc).__name__}: {exc}'
    (stage/'reports/review-index-tests.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report['status'] == 'passed' else 1


if __name__ == '__main__':
    sys.exit(main())
