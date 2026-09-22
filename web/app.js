'use strict';
(() => {
  const $ = id => document.getElementById(id);
  const NS = 'http://www.w3.org/2000/svg';
  const demos = JSON.parse($('demo-data').textContent);
  const limit = 2 * 1024 * 1024, pageSize = 8;
  let worker, serial = 0, generation = 0, report = null, page = 0, sourceName = 'input';
  let accepted = null;
  const pending = new Map();
  function status(title, detail, state = '') {
    $('status').className = `status ${state}`;
    $('status-title').textContent = title;
    $('status-detail').textContent = detail;
    $('status').querySelector('.status-symbol').textContent = state === 'error' ? '!' : state === 'dirty' ? '·' : '✓';
  }
  function startWorker() {
    const code = $('moonbit-core').textContent + `\nself.onmessage = ({data}) => {
      try {
        if (!['analyze','csv'].includes(data.op) || typeof data.text !== 'string' || ![1,2].includes(data.ports)) throw new Error('Invalid worker request');
        self.postMessage({id:data.id,result:JSON.parse(SParamKit[data.op](data.text,data.ports))});
      } catch(error) { self.postMessage({id:data.id,error:String(error.message || error)}); }
    };`;
    const url = URL.createObjectURL(new Blob([code], {type:'text/javascript'}));
    worker = new Worker(url);
    URL.revokeObjectURL(url);
    worker.onmessage = ({data}) => {
      const item = pending.get(data.id);
      if (!item) return;
      pending.delete(data.id); clearTimeout(item.timer);
      data.error ? item.reject(new Error(data.error)) : item.resolve(data.result);
    };
    worker.onerror = event => {
      event.preventDefault();
      for (const item of pending.values()) { clearTimeout(item.timer); item.reject(new Error('MoonBit 工作线程启动或执行失败，请重新打开页面。')); }
      pending.clear();
    };
  }
  function request(op, text, ports) {
    return new Promise((resolve, reject) => {
      const id = ++serial;
      const timer = setTimeout(() => {
        for (const item of pending.values()) { clearTimeout(item.timer); item.reject(new Error('计算超时，工作线程已重置。请缩小输入后重试。')); }
        pending.clear(); worker.terminate(); startWorker();
      }, 15000);
      pending.set(id, {resolve, reject, timer});
      worker.postMessage({id,op,text,ports});
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
    generation++; report = null; accepted = null; page = 0;
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
    return a >= 1e7 || a < 1e-4 ? value.toExponential(3) : Number(value.toPrecision(digits)).toString();
  }
  function frequency(value) {
    if (value >= 1e9 && value < 1e13) return `${number(value/1e9,4)} GHz`;
    if (value >= 1e6 && value < 1e9) return `${number(value/1e6,4)} MHz`;
    if (value >= 1e3 && value < 1e6) return `${number(value/1e3,4)} kHz`;
    return `${number(value,4)} Hz`;
  }
  function selectedValues() {
    const parameter = $('parameter').value;
    return report.samples.map(s => ({f:s.frequency_hz, ...s.values.find(v=>v.parameter===parameter)}));
  }
  function draw(id, data, key, height) {
    const svg = $(id); svg.replaceChildren(); svg.classList.toggle('phase', key === 'phase_degrees');
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
      const row=document.createElement('tr');
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
    const data=selectedValues();
    draw('magnitude',data,'db',255); draw('phase',data,'phase_degrees',220); table(data);
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
        status('输入未通过检查', `${data.error.code} · 第 ${data.error.line} 行，第 ${data.error.column} 列：${data.error.message}`, 'error');
        return;
      }
      report=data; accepted={text,ports};
      $('parameter').replaceChildren(...(data.ports===1?['S11']:['S21','S11','S12','S22']).map(value=>new Option(value,value)));
      $('count').textContent=data.sample_count.toLocaleString();
      $('range').textContent=`${frequency(data.samples[0].frequency_hz)} – ${frequency(data.samples.at(-1).frequency_hz)}`;
      $('impedance').textContent=`${number(data.reference_ohms)} Ω`;
      $('format-note').textContent=`${data.source_format} → 复数归一化`;
      $('csv').disabled=$('json').disabled=false;
      status('解析完成', `${sourceName} · ${data.ports} 端口 · ${data.sample_count} 个频点 · ${Math.round(performance.now()-start)} ms（含通信）`);
      render();
    } catch(error) { if(ticket===generation) status('计算失败',error.message,'error'); }
    finally { $('analyze').disabled=false; }
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
  $('source').oninput=()=>{sourceName='已编辑文本'; $('input-note').textContent='文本已编辑 · 等待重新解析'; dirty();};
  $('ports').onchange=dirty;
  $('file').onchange=event=>loadFile(event.target.files[0]);
  $('drop').ondragover=event=>{event.preventDefault(); $('drop').classList.add('drag');};
  $('drop').ondragleave=()=>$('drop').classList.remove('drag');
  $('drop').ondrop=event=>{event.preventDefault(); $('drop').classList.remove('drag'); loadFile(event.dataTransfer.files[0]);};
  $('parameter').onchange=()=>{page=0;render();}; $('scale').onchange=render;
  $('prev').onclick=()=>{if(page>0){page--;render();}}; $('next').onclick=()=>{if(report && (page+1)*pageSize<report.samples.length){page++;render();}};
  $('demo-two').onclick=()=>loadDemo('two'); $('demo-one').onclick=()=>loadDemo('one'); $('demo-error').onclick=()=>loadDemo('error');
  $('json').onclick=()=>{if(report) download(JSON.stringify(report,null,2),'json','application/json;charset=utf-8');};
  $('csv').onclick=async()=>{
    if(!accepted) return; const ticket=generation;
    try { const data=await request('csv',accepted.text,accepted.ports); if(ticket!==generation)return;
      if(data.ok) download(data.csv,'csv','text/csv;charset=utf-8'); else status('导出失败',data.error.message,'error');
    } catch(error) { if(ticket===generation)status('导出失败',error.message,'error'); }
  };
  let resizeFrame;
  window.addEventListener('resize',()=>{cancelAnimationFrame(resizeFrame);resizeFrame=requestAnimationFrame(render);});
  try { startWorker(); loadDemo('two'); } catch(error) { invalidate(); status('无法启动','需要支持 Web Worker 的现代浏览器：'+error.message,'error'); }
})();
