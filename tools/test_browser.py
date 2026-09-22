#!/usr/bin/env python3
"""Exercise the shipped offline HTML with an actual compiled core."""
from pathlib import Path
import json
import os
import shutil
from playwright.sync_api import sync_playwright, expect

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'verification'; OUT.mkdir(exist_ok=True)

def main():
    checks=[]
    engine=os.environ.get('BROWSER_NAME','chromium')
    if engine not in ('chromium','firefox','webkit'): raise ValueError('Unsupported BROWSER_NAME')
    url=os.environ.get('TEST_URL') or (ROOT/'dist/index.html').as_uri()
    with sync_playwright() as p:
        options={'headless':True}
        if engine=='chromium':
            executable=os.environ.get('CHROMIUM_PATH') or shutil.which('chromium')
            if executable: options['executable_path']=executable
            options['args']=['--no-sandbox']
        browser=getattr(p,engine).launch(**options)
        context=browser.new_context(viewport={'width':1440,'height':1160},accept_downloads=True)
        page=context.new_page(); errors=[]; requests=[]
        page.on('pageerror',lambda e: errors.append(str(e)))
        page.on('request',lambda r: requests.append(r.url) if r.url.startswith(('http://','https://')) and r.url != url else None)
        # Hold transport, not computation: responses still use the actual core.
        harness="""(() => {
          const RealWorker=window.Worker;
          window.__holdWorker=false; window.__heldWorkerRequests=[]; window.__workerReplies=0;
          window.Worker=class extends RealWorker {
            constructor(...args) {
              super(...args);
              this.addEventListener('message',()=>window.__workerReplies++);
            }
            postMessage(message,...rest) {
              if(window.__holdWorker) window.__heldWorkerRequests.push(()=>super.postMessage(message,...rest));
              else super.postMessage(message,...rest);
            }
          };
        })();"""
        def release(order='shift'):
            before=page.evaluate('window.__workerReplies')
            page.evaluate(f'window.__heldWorkerRequests.{order}()()')
            page.wait_for_function('(n)=>window.__workerReplies===n',arg=before+1)
        page.add_init_script(harness)
        if os.environ.get('TEST_CONTENT'):
            page.evaluate(harness)
            page.set_content((ROOT/'dist/index.html').read_text(encoding='utf-8'))
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
        result=json.loads(Path(info.value.path()).read_text(encoding='utf-8'))
        assert result['ok'] and result['sample_count']==291
        checks.append('JSON export all 291 samples')
        with page.expect_download() as info: page.locator('#csv').click()
        lines=Path(info.value.path()).read_text(encoding='utf-8').splitlines()
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
        result=json.loads(Path(info.value.path()).read_text(encoding='utf-8'))
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
        page.locator('#file').set_input_files({'name':'impedance_conflict.s1p','mimeType':'text/plain','buffer':b'# Hz S RI R 50\n1 .1 0\n! Port Impedance 75 0\n'})
        expect(page.locator('#status-title')).to_have_text('输入未通过检查')
        expect(page.locator('#status-detail')).to_contain_text('UnsupportedMetadata')
        expect(page.locator('#csv')).to_be_disabled()
        expect(page.locator('#json')).to_be_disabled()
        expect(page.locator('#magnitude .trace')).to_have_count(0)
        expect(page.locator('#impedance')).to_have_text('—')
        checks.append('conflicting vendor impedance refuses misleading display and exports')
        page.locator('#demo-one').click()
        expect(page.locator('#status-title')).to_have_text('解析完成')
        expect(page.locator('#count')).to_have_text('161')
        checks.append('successful recovery after errors')
        # A cleared input permits selecting the very same file after editing.
        upload = str(ROOT/'dist/samples/synthetic_rc.s1p')
        page.locator('#file').set_input_files(upload)
        expect(page.locator('#status-title')).to_have_text('解析完成')
        expect(page.locator('#file')).to_have_value('')
        page.locator('#source').fill('# Hz S RI R 50\n1 .1 0\n')
        page.locator('#file').set_input_files(upload)
        expect(page.locator('#status-title')).to_have_text('解析完成')
        expect(page.locator('#count')).to_have_text('161')
        checks.append('same file can be selected again after editing')
        page.evaluate(r"""() => {
          const data=new DataTransfer();
          data.items.add(new File(['# Hz S RI R 50\n1 .3 -.4\n'],'天线.s1p',{type:'text/plain'}));
          document.getElementById('drop').dispatchEvent(new DragEvent('drop',{dataTransfer:data,bubbles:true}));
        }""")
        expect(page.locator('#status-title')).to_have_text('解析完成')
        expect(page.locator('#count')).to_have_text('1')
        with page.expect_download() as info: page.locator('#json').click()
        assert info.value.suggested_filename == '天线.json'
        assert json.loads(Path(info.value.path()).read_text(encoding='utf-8'))['samples'][0]['values'][0]['im'] == -.4
        checks.append('drag-drop and Unicode download filename preserve data')
        page.evaluate("window.__holdWorker=true")
        page.locator('#demo-two').click()
        page.locator('#demo-one').click()
        release()
        expect(page.locator('#analyze')).to_be_disabled()
        expect(page.locator('#csv')).to_be_disabled()
        expect(page.locator('#status-title')).to_have_text('正在解析')
        release()
        expect(page.locator('#status-title')).to_have_text('解析完成',timeout=5000)
        expect(page.locator('#count')).to_have_text('161')
        checks.append('older completion cannot unlock newer pending analysis')
        page.locator('#demo-two').click()
        page.locator('#demo-one').click()
        release('pop')
        expect(page.locator('#status-title')).to_have_text('解析完成')
        release()
        expect(page.locator('#count')).to_have_text('161')
        checks.append('out-of-order response cannot replace the most recent data')
        downloads=[]
        def record_download(download): downloads.append(download)
        page.on('download',record_download)
        page.locator('#csv').click()
        expect(page.locator('#csv')).to_be_disabled()
        page.locator('#source').fill('# Hz S RI R 50\n1 .2 0\n')
        release()
        page.wait_for_timeout(150)
        assert not downloads, 'Obsolete CSV was downloaded after input changed'
        expect(page.locator('#csv')).to_be_disabled()
        expect(page.locator('#json')).to_be_disabled()
        expect(page.locator('#analyze')).to_be_enabled()
        page.remove_listener('download',record_download)
        page.evaluate('window.__holdWorker=false')
        checks.append('pending CSV disables duplicate exports and is discarded after editing')
        # Inspect original frequency samples without resampling the numerical data.
        probe='# Hz S RI R 50\n1 .1 0 .2 .1 .3 -.2 .4 .3\n10 .2 0 .3 .2 .4 -.3 .5 .4\n100 .3 0 .4 .3 .5 -.4 .6 .5\n'
        page.locator('#file').set_input_files({'name':'readout.s2p','mimeType':'text/plain','buffer':probe.encode()})
        expect(page.locator('#status-title')).to_have_text('解析完成')
        expect(page.locator('#sample-index')).to_be_enabled()
        expect(page.locator('#read-f')).to_have_text('1')
        page.locator('#sample-index').focus()
        page.locator('#sample-index').press('ArrowRight')
        expect(page.locator('#read-f')).to_have_text('10')
        expect(page.locator('#sample-position')).to_contain_text('2 / 3')
        page.locator('#sample-index').press('End')
        expect(page.locator('#read-f')).to_have_text('100')
        page.locator('#sample-index').press('Home')
        expect(page.locator('#read-f')).to_have_text('1')
        checks.append('keyboard slider selects exact original frequency samples')
        page.locator('#sample-index').evaluate("el=>{el.value='1';el.dispatchEvent(new Event('input'))}")
        page.locator('#parameter').select_option('S12')
        expect(page.locator('#read-f')).to_have_text('10')
        expect(page.locator('#read-re')).to_have_text('0.4')
        expect(page.locator('#read-im')).to_have_text('-0.3')
        with page.expect_download() as info: page.locator('#json').click()
        reference=json.loads(Path(info.value.path()).read_text(encoding='utf-8'))
        v=next(v for v in reference['samples'][1]['values'] if v['parameter']=='S12')
        for id,key in [('read-mag','magnitude'),('read-db','db'),('read-phase','phase_degrees')]:
            assert float(page.locator('#'+id).get_attribute('title'))==v[key]
        checks.append('parameter switch preserves selected sample and readout matches exported MoonBit values')
        def point_at(fraction, action='move'):
            # Convert from the SVG's viewBox to the real viewport, including CSS scaling.
            xy=page.locator('#magnitude').evaluate('''(svg,fraction)=>{
              const width=svg.viewBox.baseVal.width;
              const L=width<520?48:66, R=width-22;
              const p=svg.createSVGPoint();p.x=L+(R-L)*fraction;p.y=60;
              const q=p.matrixTransform(svg.getScreenCTM());return {x:q.x,y:q.y};
            }''',fraction)
            getattr(page.mouse,action)(xy['x'],xy['y'])
        page.locator('#magnitude').scroll_into_view_if_needed()
        page.locator('#scale').select_option('log'); point_at(.62)
        expect(page.locator('#read-f')).to_have_text('10')
        page.locator('#scale').select_option('linear'); point_at(.62,'click')
        expect(page.locator('#read-f')).to_have_text('100')
        expect(page.locator('#magnitude .cursor-dot')).to_have_count(1)
        expect(page.locator('#phase .cursor-dot')).to_have_count(1)
        checks.append('pointer readout chooses nearest screen-position sample on linear and log axes')
        page.locator('#source').fill('# Hz S RI R 50\n0 0 0\n1 .3 -.4\n')
        expect(page.locator('#sample-index')).to_be_disabled()
        expect(page.locator('#read-f')).to_have_text('—')
        expect(page.locator('.cursor-dot')).to_have_count(0)
        page.locator('#parameter').select_option('S11')
        page.locator('#scale').select_option('log')
        page.locator('#ports').select_option('1');page.locator('#analyze').click()
        expect(page.locator('#status-title')).to_have_text('解析完成')
        page.locator('#scale').select_option('log')
        expect(page.locator('#read-f')).to_have_text('0')
        expect(page.locator('#read-mag')).to_have_text('0')
        expect(page.locator('#read-db')).to_have_text('—')
        expect(page.locator('#read-phase')).to_have_text('—')
        expect(page.locator('#sample-position')).to_contain_text('0 Hz 不在对数轴显示')
        expect(page.locator('.cursor-dot')).to_have_count(0)
        checks.append('undefined values and log-zero readouts stay distinct; edits clear selection')
        # The textarea normalizes CR endings; source offsets still handle Unicode and BOM.
        diagnostic_text='\ufeff! 中文 🔬\r# Hz S RI R 50\r1 .1 bad\r'
        page.locator('#file').set_input_files({'name':'diagnostic.s1p','mimeType':'text/plain','buffer':diagnostic_text.encode()})
        expect(page.locator('#status-title')).to_have_text('输入未通过检查')
        expect(page.locator('#locate-error')).to_be_visible()
        page.locator('#locate-error').click()
        expect(page.locator('#source')).to_be_focused()
        selection=page.locator('#source').evaluate('el=>({selected:el.value.slice(el.selectionStart,el.selectionEnd),value:el.value})')
        assert selection['selected']=='bad',selection
        assert selection['value']==diagnostic_text.replace('\r','\n')
        page.locator('#source').fill('# Hz S RI R 50\n1 .1 0\n')
        expect(page.locator('#locate-error')).to_be_hidden()
        checks.append('error locator focuses exact field in BOM/CR/Unicode input without editing text')
        # An upper-limit two-port file exercises UI, full exports and the pagination fast path.
        large='# Hz S RI R 50\n'+''.join(f'{i} .1 0 .8 0 .7 0 .2 0\n' for i in range(1,20001))
        page.locator('#file').set_input_files({'name':'20000.s2p','mimeType':'text/plain','buffer':large.encode()})
        expect(page.locator('#status-title')).to_have_text('解析完成',timeout=30000)
        assert page.locator('#count').inner_text().replace(',','')=='20000'
        page.evaluate("window.__curve=document.querySelector('#magnitude .trace')")
        page.locator('#next').click()
        assert page.evaluate("window.__curve===document.querySelector('#magnitude .trace')")
        page.locator('#sample-index').evaluate("el=>{el.value='19999';el.dispatchEvent(new Event('input'))}")
        expect(page.locator('#read-f')).to_have_text('20000')
        expect(page.locator('#table-note')).to_contain_text('19993–20000')
        expect(page.locator('#rows tr.selected')).to_have_count(1)
        assert page.evaluate("window.__curve===document.querySelector('#magnitude .trace')")
        checks.append('20000-point readout and pagination preserve the existing plot instead of rebuilding it')
        with page.expect_download(timeout=30000) as info: page.locator('#json').click()
        data=json.loads(Path(info.value.path()).read_text(encoding='utf-8'))
        assert data['sample_count']==20000 and len(data['samples'])==20000
        assert data['samples'][-1]['frequency_hz']==20000 and len(data['samples'][-1]['values'])==4
        with page.expect_download(timeout=30000) as info: page.locator('#csv').click()
        lines=Path(info.value.path()).read_text(encoding='utf-8').splitlines()
        assert len(lines)==80001 and lines[-1].startswith('20000,50,2,2,')
        checks.append('upper-limit JSON and CSV exports retain all 20000 frequencies and 80000 parameter rows')
        over=large+'20001 .1 0 .8 0 .7 0 .2 0\n'
        page.locator('#file').set_input_files({'name':'20001.s2p','mimeType':'text/plain','buffer':over.encode()})
        expect(page.locator('#status-title')).to_have_text('输入未通过检查',timeout=30000)
        expect(page.locator('#status-detail')).to_contain_text('SampleLimit')
        expect(page.locator('#sample-index')).to_be_disabled()
        expect(page.locator('#csv')).to_be_disabled()
        expect(page.locator('#read-f')).to_have_text('—')
        checks.append('20001 frequencies reject with SampleLimit and clear the upper-limit result')
        page.locator('#demo-one').click()
        expect(page.locator('#status-title')).to_have_text('解析完成')
        page.set_viewport_size({'width':390,'height':844})
        page.wait_for_timeout(100)
        assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
        page.screenshot(path=str(OUT/'ui-mobile.png'),full_page=True)
        checks.append('390px mobile layout without horizontal page overflow')
        assert not errors,errors
        assert not requests,requests
        checks.append('no page exceptions and no network requests')
        browser.close()
    summary={'status':'passed','browser':engine,'browser_version':browser.version,'mode': 'injected-local-document' if os.environ.get('TEST_CONTENT') else ('file' if url.startswith('file:') else 'served'),'checks':len(checks),'details':checks}
    (OUT/'browser-tests.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
