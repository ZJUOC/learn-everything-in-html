/* 讲义阅读器（唯一来源：Skill assets/reader/）。一门课只有一个页面，右栏可切换三种视图：
   概念（手工整理的概念关系图，数据在 #concept-data）/ 大纲（当前章的定义、定理、结论、例题、关键词）/ 地图（全部句子荧光的卡片）。
   右上：目录 + 视图；右下：公式区（默认本单元的定义、定理、结论公式，可切全览），关闭公式区时显示智慧区（#wisdom-data）。
   “原文”去掉全部荧光；“×”收起面板，回到原讲义的左侧目录版面。 */
(()=>{
const KEY='lecture:'+location.pathname;
const OLD='adhd-concept:'+location.pathname.replace(/\.html$/,encodeURIComponent('（ADHD概念图版）')+'.html');
const load=()=>{try{return JSON.parse(localStorage.getItem(KEY)||localStorage.getItem(OLD)||'{}')}catch(e){return{}}};
const save=s=>{try{localStorage.setItem(KEY,JSON.stringify(s))}catch(e){}};
const CD=document.getElementById('concept-data');
const DATA=CD?JSON.parse(CD.textContent):{};
const HAS_CONCEPT=Object.keys(DATA).length>0;
const st=Object.assign({off:[],fx:true},load());
if(!st.view||(st.view==='concept'&&!HAS_CONCEPT))st.view=HAS_CONCEPT?'concept':'outline';
const root=document.documentElement,main=document.querySelector('main');
const CATS=[['thesis','结论','var(--hl-thesis-ink)','var(--hl-thesis)'],['claim','方法','var(--hl-claim-ink)','var(--hl-claim)'],
 ['evidence','例子','var(--hl-evidence-ink)','var(--hl-evidence)'],['counter','易错','var(--hl-counter-ink)','var(--hl-counter)'],['term','概念','var(--hl-term-ink)','var(--hl-term)']];
const norm=s=>s.replace(/\s+/g,'');
const txt=el=>{const c=el.cloneNode(true);c.querySelectorAll('math').forEach(m=>{const a=m.querySelector('annotation');m.replaceWith(a?a.textContent:'')});return c.textContent.replace(/\s+/g,' ').trim()};
const vis=el=>{const c=el.cloneNode(true);c.querySelectorAll('annotation').forEach(a=>a.remove());return c.textContent.replace(/\s+/g,' ').trim()};
root.classList.add('cmap-on');

/* 1. 标题与小节范围 */
const heads=[...main.querySelectorAll('h2[id],h3[id]')];
const secOf=new Map();   // 概念名 → 小节 id
for(const [sid,s] of Object.entries(DATA))for(const n of s.nodes)secOf.set(n.n,sid);
const chapters=[];
for(const h of heads){if(h.tagName==='H2'||!chapters.length)chapters.push({h,subs:[]});else chapters[chapters.length-1].subs.push(h)}
const chapOf=new Map();chapters.forEach((c,i)=>{chapOf.set(c.h,i);c.subs.forEach(s=>chapOf.set(s,i))});
function range(sid){const h=document.getElementById(sid);const out=[];let n=h&&h.nextElementSibling;
  while(n&&!/^H[23]$/.test(n.tagName)){out.push(n);n=n.nextElementSibling}return [h,out]}
function locate(sid,word){
  const [h,els]=range(sid);if(!h)return null;const w=norm(word);
  for(const sel of ['strong','.block-title','mark','li','p','figcaption','td']){
    for(const e of els){const cands=e.matches(sel)?[e,...e.querySelectorAll(sel)]:e.querySelectorAll(sel);
      for(const c of cands)if(norm(txt(c)).includes(w)||norm(vis(c)).includes(w))return c}}
  return h;
}
function jump(el){if(!el)return;const d=el.closest('details');if(d)d.open=true;
  el.scrollIntoView({behavior:'smooth',block:/^H/.test(el.tagName)?'start':'center'});
  el.classList.add('flash');setTimeout(()=>el.classList.remove('flash'),1600)}
const goConcept=name=>{const hd=[...main.querySelectorAll('.cpt-head')].find(e=>e.dataset.c===name);if(hd&&!root.classList.contains('plain'))return jump(hd);const sid=secOf.get(name);if(!sid)return;const n=DATA[sid].nodes.find(x=>x.n===name);jump(locate(sid,n.at))};

/* 2. 面板骨架 */
const box=document.createElement('div');box.id='cmap';
box.innerHTML=`<nav class="toc" aria-label="目录"><a class="back" href="开始阅读.html">← 课程讲义</a><div class="tl"></div></nav>
<section class="map" aria-label="阅读面板"><header><span class="tabs" role="tablist"><button data-v="concept" title="概念关系：A → B 表示 B 用到 A">概念</button><button data-v="outline" title="本章概念大纲">大纲</button><button data-v="map" title="全部荧光句子">地图</button></span><span class="chap"></span>
<button class="fxbtn" title="右下角显示公式区">公式</button><button class="x" title="收起面板，回到原讲义版面" aria-label="收起面板">×</button></header>
<div class="body"></div><footer><span class="dots"></span><span class="hint">A → B：B 用到 A</span></footer></section>`;
const reopen=document.createElement('button');reopen.id='cmap-open';reopen.textContent='阅读面板';
document.body.append(box,reopen);
if(!HAS_CONCEPT)box.querySelector('[data-v=concept]').hidden=true;
/* 智慧区（可选）：每个单元一棵括号树，在右下显示；打开公式区时收起 */
const WD=document.getElementById('wisdom-data'),WZ=WD?JSON.parse(WD.textContent):null;let wzBody=null,wzCur;
if(WZ){root.classList.add('wz-on');const w=document.createElement('div');w.id='wisdom';
  w.innerHTML='<header><b>智慧</b><span>这一单元的大局，打开公式区时收起</span></header><div class="body"></div>';
  document.body.append(w);wzBody=w.querySelector('.body')}
function wisdom(id){if(!wzBody||id===wzCur)return;wzCur=id;const u=WZ[id];
  wzBody.innerHTML=u?(u.path?'<div class="wz-path">'+u.path+'</div>':'')+u.html:'<p class="empty">这一单元还没有整理。</p>';wzBody.scrollTop=0}
const tl=box.querySelector('.tl'),body=box.querySelector('.body'),chapLab=box.querySelector('.chap');
const back=document.querySelector('aside a[href]');if(back)box.querySelector('.back').href=back.getAttribute('href');

/* 3. 目录 */
const tocItems=new Map();
for(const c of chapters){
  const a=document.createElement('a');a.href='#'+c.h.id;a.className='c';a.textContent=txt(c.h);tl.append(a);tocItems.set(c.h,a);
  const sub=document.createElement('div');sub.className='subs';a.after(sub);a.sub=sub;
  for(const s of c.subs){const b=document.createElement('a');b.href='#'+s.id;b.className='s';b.textContent=txt(s);sub.append(b);tocItems.set(s,b)}
}
tl.addEventListener('click',e=>{const a=e.target.closest('a');if(!a)return;e.preventDefault();jump(document.getElementById(decodeURIComponent(a.hash.slice(1))))});

/* 4a. 概念视图 */
const chip=(name,cls)=>{const b=document.createElement('button');b.className='nd '+(cls||'');b.textContent=name;b.onclick=e=>{e.stopPropagation();goConcept(name)};return b};
function graph(sid){
  const s=DATA[sid],wrap=document.createElement('div');wrap.className='graph';
  const inner=new Set(s.nodes.map(n=>n.n)),layer=new Map();
  const L=n=>{if(layer.has(n.n))return layer.get(n.n);layer.set(n.n,0);
    let v=0;for(const [d] of n.d)if(inner.has(d))v=Math.max(v,1+L(s.nodes.find(x=>x.n===d)));layer.set(n.n,v);return v};
  s.nodes.forEach(L);
  const rows=[];for(const n of s.nodes){const l=layer.get(n.n);(rows[l]=rows[l]||[]).push(n)}
  const svg=document.createElementNS('http://www.w3.org/2000/svg','svg');wrap.append(svg);
  const el=new Map();
  for(const r of rows){if(!r)continue;const row=document.createElement('div');row.className='row';
    for(const n of r){const cell=document.createElement('div');cell.className='cell';const b=chip(n.n,'cur');cell.append(b);el.set(n.n,b);
      const ext=n.d.filter(([d])=>!inner.has(d));
      if(ext.length){const x=document.createElement('div');x.className='ext';x.append('← ');
        ext.forEach(([d,lab],i)=>{if(i)x.append('、');const a=document.createElement('button');a.textContent=d;a.title=lab||'';a.onclick=e=>{e.stopPropagation();goConcept(d)};x.append(a)});cell.append(x)}
      row.append(cell)}
    wrap.append(row)}
  // 内部依赖画箭头
  wrap.draw=()=>{const W=wrap.getBoundingClientRect();svg.setAttribute('width',W.width);svg.setAttribute('height',W.height);svg.innerHTML='<defs><marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0,0L10,5L0,10z" fill="#9b87c9"/></marker></defs>';
    for(const n of s.nodes)for(const [d,lab] of n.d){if(!inner.has(d))continue;
      const a=el.get(d).getBoundingClientRect(),ac=el.get(d).parentNode.getBoundingClientRect(),b=el.get(n.n).getBoundingClientRect();
      let x1=a.left+a.width/2-W.left,y1=ac.bottom-W.top+1,x2=b.left+b.width/2-W.left,y2=b.top-W.top-2;
      if(Math.abs(a.top-b.top)<4){y1=a.top+a.height/2-W.top;y2=y1;x1=a.right-W.left;x2=b.left-W.left-2}
      const p=document.createElementNS('http://www.w3.org/2000/svg','path');
      const my=(y1+y2)/2;p.setAttribute('d',Math.abs(y1-y2)<1?`M${x1},${y1}L${x2},${y2}`:`M${x1},${y1}C${x1},${my} ${x2},${my} ${x2},${y2}`);
      p.setAttribute('marker-end','url(#ah)');svg.append(p);
      if(lab){const t=document.createElementNS('http://www.w3.org/2000/svg','text');t.setAttribute('x',(x1+x2)/2+4);t.setAttribute('y',(y1+y2)/2+4);t.textContent=lab;svg.append(t)}}};
  return wrap;
}
let shownChap=-1,curSid=null,curGraph=null;
function renderConcept(i){
  const c=chapters[i];
  for(const h of [c.h,...c.subs]){const s=DATA[h.id];if(!s||(!s.nodes.length&&!s.use.length))continue;
    const sec=document.createElement('div');sec.className='sec';sec.dataset.sid=h.id;
    const t=document.createElement('button');t.className='st';t.textContent=h===c.h?'本章导入':txt(h);t.onclick=()=>jump(h);sec.append(t);
    const brief=document.createElement('div');brief.className='brief';
    if(s.nodes.length)s.nodes.forEach(n=>brief.append(chip(n.n)));
    else{brief.classList.add('use');brief.append('用到 ');s.use.forEach(u=>brief.append(chip(u)))}
    sec.append(brief);body.append(sec)}
  if(!body.children.length)body.innerHTML='<p class="empty">这一章没有需要单独梳理的概念。</p>';
  curGraph=null;markConcept(curSid,true);
}
function markConcept(sid,force){
  if(sid===curSid&&!force)return;curSid=sid;
  body.querySelectorAll('.sec').forEach(sec=>{
    const on=sec.dataset.sid===sid;sec.classList.toggle('cur',on);
    const g=sec.querySelector('.graph');if(g&&!on)g.remove();
    if(on&&!g&&DATA[sid].nodes.length){curGraph=graph(sid);sec.append(curGraph);setTimeout(()=>curGraph&&curGraph.draw(),0)}});
  keepVisible(body.querySelector('.sec.cur'));
}
new ResizeObserver(()=>curGraph&&curGraph.draw()).observe(body);
const keepVisible=c=>{if(c){const r=c.getBoundingClientRect(),R=body.getBoundingClientRect();if(r.top<R.top||r.bottom>R.bottom)body.scrollTop+=r.top-R.top-6}};

/* 4b. 大纲视图：按文档顺序把语义块、加粗术语、结论句、带框公式归到最近的标题下 */
const KIND={definition:['定义','term'],theorem:['定理','thesis'],result:['结论','thesis'],warning:['易错','counter'],example:['例题','evidence'],question:['思考','claim']};
let OL=null;
function outlineData(){
  const secs=new Map();let cur=null;
  for(const el of main.querySelectorAll('h2,h3,div.block,strong.kt,mark.hl-thesis,mark.hl-claim,mark.hl-counter,.math.display')){
    if(el.tagName==='H2'||el.tagName==='H3'){if(!el.id)continue;cur={h:el,blocks:[],terms:[],pts:[],eqs:[]};secs.set(el,cur);continue}
    if(!cur)continue;
    if(el.tagName==='MARK'){if(!el.closest('div.block')&&!el.closest('details'))cur.pts.push({t:txt(el),el,c:el.dataset.cat});continue}
    if(el.classList.contains('display')){const a=el.querySelector('annotation');if(a&&/\\boxed/.test(a.textContent)&&!el.closest('details'))cur.eqs.push(el);continue}
    if(el.tagName==='STRONG'){const t=txt(el);if(t&&!cur.terms.some(x=>x.t===t))cur.terms.push({t,el});continue}
    const kind=[...el.classList].find(c=>KIND[c]);if(!kind)continue;
    const tt=el.querySelector('.block-title');if(!tt)continue;
    let name=txt(tt).replace(/^[^·]*·\s*/,'');if(!name)name=txt(tt);   // “定义 3 · n 次方根” → “n 次方根”
    cur.blocks.push({kind,name,el});
  }
  return secs;
}
const node=(cls,label,text,el)=>{const b=document.createElement('button');b.className='n '+cls;
  if(label){const t=document.createElement('span');t.className='k';t.textContent=label;b.append(t)}
  b.append(document.createTextNode(text));b.onclick=e=>{e.stopPropagation();jump(el)};return b};
function kids(s){
  const wrap=document.createElement('div');wrap.className='kids';
  for(const b of s.blocks){const [lab,cat]=KIND[b.kind];wrap.append(node('c-'+cat+(b.kind==='example'||b.kind==='question'?' ex':''),lab,b.name,b.el))}
  for(const e of s.eqs.slice(0,2)){const b=node('c-thesis eq','结果','',e);const m=e.querySelector('math').cloneNode(true);m.setAttribute('display','inline');b.append(m);wrap.append(b)}
  // 没有定义、定理时，用结论句补位；再没有就用方法、易错句
  if(!s.blocks.some(b=>KIND[b.kind][1]!=='evidence'&&b.kind!=='warning')){
    const lab={thesis:'要点',claim:'方法',counter:'易错'};
    let ps=s.pts.filter(p=>p.c==='thesis').slice(0,3);
    if(!ps.length&&!s.eqs.length)ps=s.pts.slice(0,2);
    for(const p of ps)wrap.append(node('c-'+p.c+' pt',lab[p.c],p.t.length>46?p.t.slice(0,46)+'…':p.t,p.el));
  }
  const used=new Set(s.blocks.map(b=>b.name));
  const terms=s.terms.filter(t=>!used.has(t.t)).slice(0,12);
  if(terms.length){const r=document.createElement('div');r.className='terms';
    for(const t of terms){const b=document.createElement('button');b.className='chip';b.textContent=t.t;b.onclick=e=>{e.stopPropagation();jump(t.el)};r.append(b)}
    wrap.append(r)}
  return wrap;
}
function renderOutline(i){
  OL=OL||outlineData();const c=chapters[i],wrap=document.createElement('div');wrap.className='ol';
  for(const h of [c.h,...c.subs]){const s=OL.get(h);if(!s)continue;
    if(h===c.h&&!s.blocks.length&&!s.terms.length&&!s.pts.length&&!s.eqs.length)continue;
    const li=document.createElement('div');li.className='sec';li.dataset.sid=h.id;
    const t=document.createElement('button');t.className='st';t.textContent=h===c.h?'本章导入':txt(h);t.onclick=()=>jump(h);li.append(t);
    const b=s.blocks.filter(b=>b.kind==='definition'||b.kind==='theorem').map(b=>b.name).join('、');
    if(b){const p=document.createElement('div');p.className='brief';p.textContent=b;li.append(p)}
    li.append(kids(s));wrap.append(li)}
  body.append(wrap);
}
const markOutline=sid=>{body.querySelectorAll('.ol .sec').forEach(li=>li.classList.toggle('cur',li.dataset.sid===sid));keepVisible(body.querySelector('.ol .sec.cur'))};

/* 4c. 地图视图：全部句子荧光和加粗术语的卡片，点卡片跳到原文 */
function renderMap(){
  const items=[...main.querySelectorAll('[data-cat]')];
  const wrap=document.createElement('div');wrap.className='rm';
  const sum=document.createElement('div');sum.className='sum';sum.textContent=items.length+' 处标注 · 底部按类开关，双击只看一类';wrap.append(sum);
  let h=null;const where=new Map();
  for(const el of main.querySelectorAll('h2,h3,[data-cat]')){if(/^H/.test(el.tagName))h=el;else where.set(el,h?txt(h):'')}
  for(const el of items){
    const meta=CATS.find(x=>x[0]===el.dataset.cat);if(!meta)continue;
    const t=txt(el),card=document.createElement('button');card.className='card';card.dataset.c=meta[0];
    card.innerHTML=`<span class="tag" style="color:${meta[2]};background:${meta[3]}">${meta[1]}</span><br>`;
    card.append(document.createTextNode(t.length>110?t.slice(0,110)+'…':t));
    const w=document.createElement('span');w.className='where';w.textContent=where.get(el);card.append(w);
    card.onclick=()=>jump(el);wrap.append(card);
  }
  body.append(wrap);filterCards();
}
const filterCards=()=>body.querySelectorAll('.rm .card').forEach(k=>k.hidden=st.off.includes(k.dataset.c));

/* 4d. 公式区：定义、定理、结论块里的行间公式（块里没有行间公式时取含“=”的行内公式，最多两个），加上正文里的带框公式；
   折叠栏、例题、习题里的不收。默认只显示当前单元，“全览”显示全书并定位到当前单元。 */
const fx=document.createElement('section');fx.id='formula';fx.setAttribute('aria-label','公式区');
fx.innerHTML='<header><b>公式</b><span class="scope"></span><button class="all"></button></header><div class="body"></div>';
document.body.append(fx);
const fxBody=fx.querySelector('.body'),fxScope=fx.querySelector('.scope'),fxAll=fx.querySelector('.all');
let FX=null,fxShown=null,fxSid=null;
// 标题原样克隆（保留公式排版），去掉 id 和链接
const rich=el=>{const c=el.cloneNode(true);c.querySelectorAll('[id]').forEach(x=>x.removeAttribute('id'));c.querySelectorAll('a').forEach(a=>a.replaceWith(...a.childNodes));return [...c.childNodes]};
function fxData(){
  const secs=new Map();let cur=null;
  for(const el of main.querySelectorAll('h2,h3,div.block,math[display=block]')){
    if(/^H[23]$/.test(el.tagName)){if(!el.id)continue;cur={h:el,items:[]};secs.set(el,cur);continue}
    if(!cur||el.closest('details'))continue;
    if(el.tagName==='DIV'){
      if(!/\b(definition|theorem|result)\b/.test(el.className))continue;
      const tt=el.querySelector('.block-title');if(!tt)continue;
      let ms=[...el.querySelectorAll('math[display=block]')].filter(m=>!m.closest('details'));
      if(!ms.length)ms=[...el.querySelectorAll('math')].filter(m=>{const a=m.querySelector('annotation');return a&&a.textContent.includes('=')&&!m.closest('details')}).slice(0,2);
      if(ms.length)cur.items.push({lab:tt,el,ms});continue}
    if(el.closest('div.block'))continue;
    const a=el.querySelector('annotation');if(a&&/\\boxed/.test(a.textContent))cur.items.push({lab:'',el,ms:[el]});
  }
  return secs;
}
function fxSec(h,isChap){
  const s=FX.get(h);if(!s||!s.items.length)return null;
  const d=document.createElement('div');d.className='fsec';d.dataset.sid=h.id;
  const t=document.createElement('button');t.className='st';if(isChap)t.textContent='本章导入';else t.append(...rich(h));t.onclick=()=>jump(h);d.append(t);
  for(const it of s.items){const b=document.createElement('button');b.className='fi';b.onclick=()=>jump(it.el);
    if(it.lab){const k=document.createElement('span');k.className='k';k.append(...rich(it.lab));b.append(k)}
    for(const m of it.ms){const c=m.cloneNode(true);c.setAttribute('display','block');const w=document.createElement('span');w.className='fm';w.append(c);b.append(w)}
    d.append(b)}
  return d;
}
function fxChap(i){
  const c=chapters[i],w=document.createElement('div');w.className='fchap';w.dataset.ci=i;
  for(const h of [c.h,...c.subs]){const d=fxSec(h,h===c.h);if(d)w.append(d)}
  return w;
}
function formulas(i,sid){
  if(!st.fx)return;FX=FX||fxData();
  const key=st.fxall?'all':i;
  if(fxShown!==key){fxShown=key;fxSid=null;fxBody.textContent='';
    if(st.fxall){chapters.forEach((c,j)=>{const w=fxChap(j);if(!w.children.length)return;
      const t=document.createElement('button');t.className='ch';t.append(...rich(c.h));t.onclick=()=>jump(c.h);w.prepend(t);fxBody.append(w)})}
    else{const w=fxChap(i);if(w.children.length)fxBody.append(w);else fxBody.innerHTML='<p class="empty">这一单元没有定义、定理或结论公式。</p>'}
    fxScope.textContent='';if(st.fxall)fxScope.textContent='全书';else fxScope.append(...rich(chapters[i].h));
    fxAll.textContent=st.fxall?'本单元':'全览';fxAll.title=st.fxall?'只看当前单元':'显示全书公式';
    if(st.fxall){const w=fxBody.querySelector(`.fchap[data-ci="${i}"]`);fxBody.scrollTop=w?w.offsetTop-fxBody.offsetTop:0}else fxBody.scrollTop=0}
  if(sid===fxSid)return;fxSid=sid;
  fxBody.querySelectorAll('.fchap').forEach(w=>w.classList.toggle('cur',+w.dataset.ci===i));
  let on=null;fxBody.querySelectorAll('.fsec').forEach(d=>{const x=d.dataset.sid===sid;d.classList.toggle('cur',x);if(x)on=d});
  if(on&&!st.fxall){const r=on.getBoundingClientRect(),R=fxBody.getBoundingClientRect();if(r.top<R.top||r.bottom>R.bottom)fxBody.scrollTop+=r.top-R.top-6}
}
fxAll.onclick=()=>{st.fxall=!st.fxall;save(st);fxShown=null;spy()};

/* 5. 跟随阅读位置 */
function render(i){
  shownChap=i;body.textContent='';chapLab.textContent=st.view==='map'?'全部':txt(chapters[i].h);
  if(st.view==='concept')renderConcept(i);else if(st.view==='outline')renderOutline(i);else renderMap();
}
function spy(){
  if(!heads.length)return;
  let h=heads[0];for(const x of heads){if(x.getBoundingClientRect().top<160)h=x;else break}
  const i=chapOf.get(h);
  if(st.view==='map'){if(shownChap<0)render(i)}else if(i!==shownChap)render(i);
  wisdom(chapters[i].h.id);formulas(i,h.id);
  // 当前小节：本身有数据就用它，否则退到本章导入
  if(st.view==='concept')markConcept(DATA[h.id]?h.id:chapters[i].h.id);
  else if(st.view==='outline')markOutline(h.id);
  tocItems.forEach((a,k)=>a.classList.toggle('on',k===h||k===chapters[i].h));
  tl.querySelectorAll('.subs').forEach(s=>s.classList.toggle('open',s===tocItems.get(chapters[i].h).sub));
  const a=tocItems.get(h);if(a){const r=a.getBoundingClientRect(),R=tl.getBoundingClientRect();if(r.top<R.top||r.bottom>R.bottom)tl.scrollTop+=r.top-R.top-R.height/3}
}
let tick=false;addEventListener('scroll',()=>{if(!tick){tick=true;setTimeout(()=>{tick=false;spy()},60)}},{passive:true});
// 平滑滚动结束、页面加载完（图片撑开高度）后再校正一次
addEventListener('scrollend',spy);addEventListener('load',()=>setTimeout(spy,50));
box.querySelectorAll('.tabs button').forEach(b=>b.onclick=()=>{st.view=b.dataset.v;shownChap=-1;curSid=null;apply();spy()});

/* 6. 荧光开关、原文、公式区、收起 */
const dots=box.querySelector('.dots');
for(const [c,n] of CATS){const b=document.createElement('button');b.className='dot hl-'+c;b.dataset.c=c;b.textContent=n;b.title='点击开关'+n+'荧光；双击只看这一类';
  b.onclick=()=>{const i=st.off.indexOf(c);i<0?st.off.push(c):st.off.splice(i,1);st.only=null;apply()};
  b.ondblclick=()=>{st.only=st.only===c?null:c;st.off=st.only?CATS.map(x=>x[0]).filter(x=>x!==c):[];apply()};dots.append(b)}
/* 词语荧光（mark.kw 手工挑选的句子骨架词；mark.kw2 按分句自动补的浅一档荧光）：可选荧光颜色，或只加粗、加大，或关闭；“密”按钮开关 kw2 */
const KW=[['amber','琥珀'],['coral','橙红'],['green','青绿'],['blue','天蓝'],['pink','粉紫'],['bold','加粗'],['big','加大'],['off','关闭']];
const hasKw=!!document.querySelector('main mark.kw, main mark.kw2'),hasKw2=!!document.querySelector('main mark.kw2');
if(hasKw){
  const w=document.createElement('span');w.className='kwpick';
  w.innerHTML='<button class="kwbtn" title="词语荧光样式">词</button><span class="kwmenu" hidden></span>';
  const menu=w.querySelector('.kwmenu');
  for(const [k,n] of KW){const b=document.createElement('button');b.dataset.k=k;b.className='kwopt kw-'+k;b.textContent=n;
    b.onclick=()=>{st.kw=k;menu.hidden=true;apply()};menu.append(b)}
  w.querySelector('.kwbtn').onclick=e=>{e.stopPropagation();menu.hidden=!menu.hidden};
  document.addEventListener('click',e=>{if(!w.contains(e.target))menu.hidden=true});
  if(hasKw2){const b=document.createElement('button');b.className='kwdbtn';b.textContent='密';
    b.title='密集荧光：每句隔几个词自动补一处浅荧光（点一下开关）';
    b.onclick=()=>{st.kwd=st.kwd==='sparse'?'dense':'sparse';apply()};w.append(b)}
  dots.prepend(w);
}
const plainBtn=document.createElement('button');plainBtn.className='plainbtn';plainBtn.textContent='原文';plainBtn.title='去掉全部荧光和概念小标题';
plainBtn.onclick=()=>{st.plain=!st.plain;apply()};dots.append(plainBtn);
function apply(){
  for(const [c] of CATS)root.classList.toggle('off-'+c,st.off.includes(c));
  if(hasKw){const k=st.kw||'amber';root.dataset.kw=k;
    dots.querySelector('.kwbtn').className='kwbtn kw-'+k;
    dots.querySelectorAll('.kwopt[data-k]').forEach(b=>b.classList.toggle('on',b.dataset.k===k));
    const d=st.kwd||'dense';root.dataset.kwd=d;const t=dots.querySelector('.kwdbtn');
    if(t){t.setAttribute('aria-pressed',String(d==='dense'));t.classList.toggle('on',d==='dense')}}
  dots.querySelectorAll('.dot[data-c]').forEach(b=>{b.setAttribute('aria-pressed',String(!st.off.includes(b.dataset.c)));b.classList.toggle('only',st.only===b.dataset.c)});
  root.classList.toggle('plain',!!st.plain);plainBtn.classList.toggle('on',!!st.plain);plainBtn.setAttribute('aria-pressed',String(!!st.plain));
  for(const v of ['concept','outline','map'])root.classList.toggle('v-'+v,st.view===v);
  box.querySelectorAll('.tabs button').forEach(b=>{b.classList.toggle('on',b.dataset.v===st.view);b.setAttribute('aria-selected',String(b.dataset.v===st.view))});
  root.classList.toggle('panel-closed',!!st.closed);root.classList.toggle('cmap-on',!st.closed);
  root.classList.toggle('fx-on',!!st.fx&&!st.closed);box.querySelector('.fxbtn').classList.toggle('on',!!st.fx);
  filterCards();save(st);curGraph&&setTimeout(()=>curGraph.draw(),0);
}
box.querySelector('.fxbtn').onclick=()=>{st.fx=!st.fx;fxShown=null;apply();spy()};
box.querySelector('.x').onclick=()=>{st.closed=true;apply()};
reopen.onclick=()=>{st.closed=false;apply();shownChap=-1;spy()};
apply();spy();
})();
