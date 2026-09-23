'use strict';
(() => {
  const $ = id => document.getElementById(id);
  const NS = 'http://www.w3.org/2000/svg';
  const demos = JSON.parse($('demo-data').textContent);
  const limit = 2 * 1024 * 1024, pageSize = 8;
  let worker = null, serial = 0, generation = 0, report = null, page = 0, sourceName = 'input';
  let accepted = null, diagnostic = null, plotData = [], selectedIndex = 0;
  const plotGeometry = new Map();
  const pending = new Map();
  function status(title, detail, state = '') {
    $('status').className = `status ${state}`;
    $('status-title').textContent = title;
    $('status-detail').textContent = detail;
    $('status').querySelector('.status-symbol').textContent = state === 'error' ? '!' : state === 'dirty' ? '·' : '✓';
  }
  function discardWorker(current, error) {
    // A delayed event from a retired worker must not cancel its replacement.
    if (worker !== current) return;
    worker = null;
    current.onmessage = current.onerror = null;
    current.terminate();
    for (const item of pending.values()) {
      clearTimeout(item.timer); item.reject(error);
    }
    pending.clear();
  }
  function startWorker() {
    const code = $('moonbit-core').textContent + `\nself.onmessage = ({data}) => {
      try {
        if (!['analyze','csv'].includes(data.op) || typeof data.text !== 'string' || ![1,2].includes(data.ports)) throw new Error('Invalid worker request');
        self.postMessage({id:data.id,result:JSON.parse(SParamKit[data.op](data.text,data.ports))});
      } catch(error) { self.postMessage({id:data.id,error:String(error.message || error)}); }
    };`;
    const url = URL.createObjectURL(new Blob([code], {type:'text/javascript'}));
    let current;
    try { current = new Worker(url); }
    finally { URL.revokeObjectURL(url); }
    worker = current;
    current.onmessage = ({data}) => {
      if (worker !== current) return;
      const item = pending.get(data.id);
      if (!item) return;
      pending.delete(data.id); clearTimeout(item.timer);
      data.error ? item.reject(new Error(data.error)) : item.resolve(data.result);
    };
    current.onerror = event => {
      event.preventDefault();
      discardWorker(current, new Error('工作线程出错，请重新解析。输入内容已保留。'));
    };
    current.addEventListener('messageerror', () => {
      discardWorker(current, new Error('无法读取工作线程的响应，请重新解析。'));
    });
    return current;
  }
  function request(op, text, ports) {
    return new Promise((resolve, reject) => {
      // Create lazily: a failed start or timeout is retried by the next action.
      const current = worker || startWorker();
      const id = ++serial;
      const timer = setTimeout(() => {
        discardWorker(current, new Error('计算超时，请缩小输入后重新解析。'));
      }, 15000);
      pending.set(id, {resolve, reject, timer});
      try { current.postMessage({id,op,text,ports}); }
      catch (error) { discardWorker(current, error); }
    });
  }
  function svgNode(name, attrs, text) {
    const node = document.createElementNS(NS, name);
    for (const [key, value] of Object.entries(attrs)) node.setAttribute(key, value);
    if (text !== undefined) node.textContent = text;
    return node;
  }
  function emptyPlot(id, text) {
    const svg = $(id); svg.replaceChildren(); svg.setAttribute('viewBox','0 0 900 220');
    svg.append(svgNode('text', {x:450,y:110,'text-anchor':'middle'}, text));
  }
  function invalidate() {
    generation++; report = null; accepted = null; diagnostic = null; page = 0;
    plotData = []; selectedIndex = 0; plotGeometry.clear();
    $('locate-error').hidden = true;
    $('source').removeAttribute('aria-invalid');
    $('sample-index').disabled = true; $('sample-index').value = '0';
    $('sample-position').textContent = '等待数据';
    $('sample-index').removeAttribute('aria-valuetext');
    for (const id of ['read-f','read-re','read-im','read-mag','read-db','read-phase']) {
      $(id).textContent = '—'; $(id).removeAttribute('title');
    }
    $('analyze').disabled = false;
    $('plot-note').textContent = '图中展示原始采样点，不进行插值或平滑。';
    $('csv').disabled = $('json').disabled = true;
    $('prev').disabled = $('next').disabled = true;
    $('count').textContent = $('range').textContent = $('impedance').textContent = '—';
    $('format-note').textContent = '输入表示';
    $('rows').replaceChildren(); $('table-note').textContent = '等待数据';
    emptyPlot('magnitude', '解析后显示幅度曲线'); emptyPlot('phase', '解析后显示相位曲线');
  }
  function dirty() {
    invalidate(); status('输入已修改', '请重新解析。旧曲线和导出已清除，避免混用结果。', 'dirty');
  }
  function number(value, digits = 6) {
    if (value === null || !Number.isFinite(value)) return '—';
    if (value === 0) return '0';
    const a = Math.abs(value);
    return a >= 1e7 || a < 1e-4 ? value.toExponential(digits - 1) : Number(value.toPrecision(digits)).toString();
  }
  function frequency(value) {
    if (value >= 1e9 && value < 1e13) return `${number(value/1e9,4)} GHz`;
    if (value >= 1e6 && value < 1e9) return `${number(value/1e6,4)} MHz`;
    if (value >= 1e3 && value < 1e6) return `${number(value/1e3,4)} kHz`;
    return `${number(value,4)} Hz`;
  }
  function selectParameter() {
    if (!report) { plotData=[]; return; }
    const parameter = $('parameter').value;
    plotData = report.samples.map(s => ({f:s.frequency_hz, ...s.values.find(v=>v.parameter===parameter)}));
  }
  function showReadout() {
    if (!report) return;
    const point = plotData[selectedIndex];
    const fields = {'read-f':point.f, 'read-re':point.re, 'read-im':point.im,
      'read-mag':point.magnitude, 'read-db':point.db, 'read-phase':point.phase_degrees};
    for (const [id, value] of Object.entries(fields)) {
      $(id).textContent = id === 'read-f' ? String(value) : number(value, 9);
      $(id).title = value === null ? '未定义' : String(value);
    }
    const omitted = $('scale').value === 'log' && point.f === 0;
    $('sample-index').value = String(selectedIndex);
    $('sample-index').setAttribute('aria-valuetext', `第 ${selectedIndex+1} 个频点，${point.f} Hz`);
    $('sample-position').textContent = `${$('parameter').value} · ${selectedIndex+1} / ${plotData.length}${omitted ? ' · 0 Hz 不在对数轴显示' : ''}`;
    for (const [id, geometry] of plotGeometry) {
      const layer = $(id).querySelector('.cursor');
      if (!layer) continue;
      layer.replaceChildren();
      if (omitted) continue;
      const xx = geometry.x(point.f);
      layer.append(svgNode('line', {x1:xx,y1:geometry.T,x2:xx,y2:geometry.B,class:'cursor-line'}));
      const value = point[geometry.key];
      if (value !== null && Number.isFinite(value)) {
        layer.append(svgNode('circle',{cx:xx,cy:geometry.y(value),r:4,class:'cursor-dot'}));
      }
    }
    for (const row of $('rows').children) row.classList.toggle('selected', Number(row.dataset.index) === selectedIndex);
  }
  function selectSample(index, reveal = true) {
    if (!report || !Number.isFinite(index)) return;
    selectedIndex = Math.max(0, Math.min(plotData.length-1, Math.trunc(index)));
    if (reveal && page !== Math.floor(selectedIndex/pageSize)) {
      page = Math.floor(selectedIndex/pageSize); table(plotData);
    }
    showReadout();
  }
  function inspectPlot(event) {
    if (!report || (event.type === 'pointermove' && event.pointerType !== 'mouse')) return;
    const svg = event.currentTarget, geometry = plotGeometry.get(svg.id);
    if (!geometry) return;
    const matrix = svg.getScreenCTM();
    if (!matrix) return;
    const position = svg.createSVGPoint(); position.x = event.clientX; position.y = event.clientY;
    const local = position.matrixTransform(matrix.inverse());
    if (local.y < geometry.T || local.y > geometry.B || local.x < geometry.L || local.x > geometry.R) return;
    // Search screen positions, so nearest-point selection also follows a log axis.
    let low = geometry.first, high = plotData.length-1;
    while (low < high) {
      const mid = low + Math.floor((high-low)/2);
      if (geometry.x(plotData[mid].f) < local.x) low = mid+1;
      else high = mid;
    }
    if (low > geometry.first && local.x - geometry.x(plotData[low-1].f) <= geometry.x(plotData[low].f) - local.x) low--;
    if (low !== selectedIndex) selectSample(low, event.type === 'pointerdown');
    else if (event.type === 'pointerdown') selectSample(low);
  }
  function locateError() {
    if (!diagnostic) return;
    const source = $('source'), text = source.value;
    let start = 0;
    for (let line=1; line<diagnostic.line; line++) {
      const end = text.indexOf('\n', start);
      if (end === -1) { start=text.length; break; }
      start = end+1;
    }
    // Parser columns count Unicode characters; textarea selection uses UTF-16 offsets.
    for (let column=1; column<diagnostic.column && start<text.length && text[start]!=='\n'; column++) {
      start += text.codePointAt(start)>0xffff ? 2 : 1;
    }
    let end = start;
    while (end<text.length && !/[\s!]/u.test(text[end])) end++;
    source.focus(); source.setSelectionRange(start,end);
    const lineHeight = parseFloat(getComputedStyle(source).lineHeight) || 18;
    source.scrollTop = Math.max(0,(diagnostic.line-1)*lineHeight-source.clientHeight/2);
    source.scrollIntoView({block:'center'});
  }
  function draw(id, data, key, height) {
    const svg = $(id); svg.replaceChildren(); plotGeometry.delete(id); svg.classList.toggle('phase', key === 'phase_degrees');
    const width=Math.max(320,Math.min(900,svg.getBoundingClientRect().width));
    svg.setAttribute('viewBox',`0 0 ${width} ${height}`);
    const log = $('scale').value === 'log';
    const visible = data.filter(p => !log || p.f > 0);
    if (!visible.length) { emptyPlot(id, '对数轴不能显示 0 Hz，请切换线性轴'); return; }
    const divisor = log ? 1 : Math.max(visible[visible.length-1].f, 1);
    const tx = f => log ? Math.log10(f) : f / divisor;
    let xlo = tx(visible[0].f), xhi = tx(visible[visible.length-1].f);
    if (xlo === xhi) { xlo -= log ? 0.5 : 0.05; xhi += log ? 0.5 : 0.05; }
    const valid = visible.map(p=>p[key]).filter(v=>v!==null && Number.isFinite(v));
    if (!valid.length) { emptyPlot(id, '该参数没有有限值（例如零幅度的 dB / 相位未定义）'); return; }
    let lo = Math.min(...valid), hi = Math.max(...valid);
    if (key === 'phase_degrees') { lo = -180; hi = 180; }
    else { const pad = Math.max((hi-lo)*0.12, 1); lo -= pad; hi += pad; }
    const L=width<520?48:66, R=width-22, T=20, B=height-38;
    const x = f => L+(tx(f)-xlo)/(xhi-xlo)*(R-L);
    const y = v => B-(v-lo)/(hi-lo)*(B-T);
    for (let i=0;i<=4;i++) {
      const yy = T+(B-T)*i/4, yyVal=hi-(hi-lo)*i/4;
      svg.append(svgNode('line',{x1:L,y1:yy,x2:R,y2:yy,class:'grid'}));
      svg.append(svgNode('text',{x:L-10,y:yy+3,'text-anchor':'end'},number(yyVal,4)));
    }
    const ticks=width<520?3:5;
    for (let i=0;i<=ticks;i++) {
      const xx=L+(R-L)*i/ticks, v=xlo+(xhi-xlo)*i/ticks;
      const f=log ? 10**v : v*divisor;
      svg.append(svgNode('line',{x1:xx,y1:T,x2:xx,y2:B,class:'grid'}));
      svg.append(svgNode('text',{x:xx,y:B+22,'text-anchor':'middle'},frequency(f)));
    }
    svg.append(svgNode('line',{x1:L,y1:B,x2:R,y2:B,class:'axis'}));
    let path='', previous=null;
    for (const point of visible) {
      const value=point[key];
      if (value === null || !Number.isFinite(value)) { previous=null; continue; }
      const breakPhase=key === 'phase_degrees' && previous!==null && Math.abs(value-previous)>180;
      path += `${previous===null || breakPhase ? 'M':'L'}${x(point.f).toFixed(2)},${y(value).toFixed(2)} `;
      previous=value;
    }
    svg.append(svgNode('path',{d:path,class:'trace'}));
    svg.append(svgNode('g',{class:'cursor','aria-hidden':'true'}));
    plotGeometry.set(id,{x,y,L,R,T,B,key,first:log && data[0].f === 0 ? 1 : 0});
    if (visible.length<=24) for (const point of visible) {
      if (point[key] !== null && Number.isFinite(point[key])) {
        const circle=svgNode('circle',{cx:x(point.f),cy:y(point[key]),r:3,fill:key==='phase_degrees'?'#4165aa':'#137c70'});
        circle.append(svgNode('title',{},`${frequency(point.f)} : ${number(point[key])}`)); svg.append(circle);
      }
    }
  }
  function table(data) {
    const begin=page*pageSize, end=Math.min(begin+pageSize,data.length);
    $('rows').replaceChildren();
    for (const point of data.slice(begin,end)) {
      const row=document.createElement('tr'); row.dataset.index=String(begin + $('rows').children.length);
      row.classList.toggle('selected',Number(row.dataset.index)===selectedIndex);
      for (const value of [point.f,point.re,point.im,point.db,point.phase_degrees]) {
        const cell=document.createElement('td'); cell.textContent=number(value); row.append(cell);
      }
      $('rows').append(row);
    }
    $('table-note').textContent=`${$('parameter').value} · 第 ${begin+1}–${end} 条 / 共 ${data.length} 条；导出包含全部参数。`;
    $('prev').disabled=page===0; $('next').disabled=end>=data.length;
  }
  function render() {
    if (!report) return;
    const data=plotData;
    draw('magnitude',data,'db',255); draw('phase',data,'phase_degrees',220); table(data); showReadout();
    const absent=data.filter(p=>p.db===null || p.phase_degrees===null).length;
    const omitted=$('scale').value==='log'?data.filter(p=>p.f===0).length:0;
    $('plot-note').textContent=`${$('parameter').value} · 原始采样点，无插值或平滑。${absent ? ` ${absent} 个点含未定义值，以空缺表示。`:''}${omitted ? ` 对数轴省略 ${omitted} 个 0 Hz 点；表格和导出保留。`:''}`;
  }
  async function analyze() {
    invalidate(); const ticket=generation, text=$('source').value, ports=Number($('ports').value);
    $('analyze').disabled=true; status('正在解析', 'MoonBit 工作线程正在检查并转换数据。');
    try {
      const start=performance.now(); const data=await request('analyze',text,ports);
      if (ticket!==generation) return;
      if (!data.ok) {
        diagnostic=data.error; $('locate-error').hidden=false;
        $('source').setAttribute('aria-invalid','true');
        status('输入未通过检查', `${data.error.code} · 第 ${data.error.line} 行，第 ${data.error.column} 列：${data.error.message}`, 'error');
        return;
      }
      report=data; accepted={text,ports};
      $('parameter').replaceChildren(...(data.ports===1?['S11']:['S21','S11','S12','S22']).map(value=>new Option(value,value)));
      selectParameter();
      $('sample-index').max=String(data.sample_count-1); $('sample-index').disabled=false;
      $('count').textContent=data.sample_count.toLocaleString();
      $('range').textContent=`${frequency(data.samples[0].frequency_hz)} – ${frequency(data.samples.at(-1).frequency_hz)}`;
      $('impedance').textContent=`${number(data.reference_ohms)} Ω`;
      $('format-note').textContent=`${data.source_format} → 复数归一化`;
      $('csv').disabled=$('json').disabled=false;
      status('解析完成', `${sourceName} · ${data.ports} 端口 · ${data.sample_count} 个频点 · ${Math.round(performance.now()-start)} ms（含通信）`);
      render();
    } catch(error) { if(ticket===generation) status('计算失败',error.message,'error'); }
    finally { if(ticket===generation) $('analyze').disabled=false; }
  }
  async function loadFile(file) {
    if (!file) return;
    invalidate(); const ticket=generation;
    const match=/\.s([12])p$/i.exec(file.name);
    if (file.size>limit) { status('文件过大','请选择不超过 2 MiB 的文件。','error'); return; }
    try {
      const bytes=await file.arrayBuffer(); if(ticket!==generation) return;
      const text=new TextDecoder('utf-8',{fatal:true,ignoreBOM:true}).decode(bytes);
      $('source').value=text; if(match) $('ports').value=match[1];
      sourceName=file.name; $('input-note').textContent=`${file.name} · ${(file.size/1024).toFixed(1)} KiB · 本地文件`;
      await analyze();
    } catch(error) { if(ticket===generation) status('文件读取失败',error.message,'error'); }
  }
  function loadDemo(key) {
    const demo=demos[key]; $('source').value=demo.text; $('ports').value=String(demo.ports);
    sourceName=demo.name; $('input-note').textContent=`${demo.name} · 合成数据（非实测）`; analyze();
  }
  function download(content, extension, mime) {
    const filename=sourceName.replace(/\.[^.]*$/,'').replace(/[^a-zA-Z0-9_\-\u4e00-\u9fff]/g,'_').slice(0,80)||'sparamkit';
    const url=URL.createObjectURL(new Blob([content],{type:mime}));
    const link=document.createElement('a'); link.href=url; link.download=`${filename}.${extension}`; link.click();
    setTimeout(()=>URL.revokeObjectURL(url),30000);
  }
  $('analyze').onclick=analyze;
  $('locate-error').onclick=locateError;
  $('sample-index').oninput=event=>selectSample(Number(event.target.value));
  for (const id of ['magnitude','phase']) {
    $(id).addEventListener('pointermove',inspectPlot);
    $(id).addEventListener('pointerdown',inspectPlot);
  }
  $('source').oninput=()=>{sourceName='已编辑文本'; $('input-note').textContent='文本已编辑 · 等待重新解析'; dirty();};
  $('ports').onchange=dirty;
  $('file').onchange=event=>{
    const file=event.target.files[0];
    // Clear the chooser so reselecting the same file triggers a fresh import.
    event.target.value=''; loadFile(file);
  };
  $('drop').ondragover=event=>{event.preventDefault(); $('drop').classList.add('drag');};
  $('drop').ondragleave=()=>$('drop').classList.remove('drag');
  $('drop').ondrop=event=>{event.preventDefault(); $('drop').classList.remove('drag'); loadFile(event.dataTransfer.files[0]);};
  $('parameter').onchange=()=>{selectParameter();render();}; $('scale').onchange=render;
  $('prev').onclick=()=>{if(page>0){page--;table(plotData);showReadout();}}; $('next').onclick=()=>{if(report && (page+1)*pageSize<report.samples.length){page++;table(plotData);showReadout();}};
  $('demo-two').onclick=()=>loadDemo('two'); $('demo-one').onclick=()=>loadDemo('one'); $('demo-error').onclick=()=>loadDemo('error');
  $('json').onclick=()=>{if(report) download(JSON.stringify(report,null,2),'json','application/json;charset=utf-8');};
  $('csv').onclick=async()=>{
    if(!accepted) return; const ticket=generation;
    $('csv').disabled=true;
    try { const data=await request('csv',accepted.text,accepted.ports); if(ticket!==generation)return;
      if(data.ok) download(data.csv,'csv','text/csv;charset=utf-8'); else status('导出失败',data.error.message,'error');
    } catch(error) { if(ticket===generation)status('导出失败',error.message,'error'); }
    finally { if(ticket===generation && accepted) $('csv').disabled=false; }
  };
  let resizeFrame;
  window.addEventListener('resize',()=>{cancelAnimationFrame(resizeFrame);resizeFrame=requestAnimationFrame(render);});
  try { loadDemo('two'); } catch(error) { invalidate(); status('无法启动','需要支持 Web Worker 的现代浏览器：'+error.message,'error'); }
})();
