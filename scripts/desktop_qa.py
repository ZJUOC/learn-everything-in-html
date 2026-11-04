#!/usr/bin/env python3
"""桌面验收：本地起 HTTP 服务（file:// 预览不加载字体图片），用本机 Chrome 检查讲义。
用法：desktop_qa.py <html 文件> <输出目录> [锚点id ...]
检查：1440/1280 宽无横向溢出、MathML 无 merror、图片与字体加载、站内锚点有效、放大框（图注公式原样显示）、答案全开/全收；
有阅读器面板（#cmap）时，检查概念/大纲/地图三种视图、原文模式、收起与重新打开；
并对每个锚点截图（已开启 reduced motion，避免平滑滚动造成空白截图）。"""
import sys,json,asyncio,threading,functools,http.server,socketserver,urllib.parse
from pathlib import Path
from playwright.async_api import async_playwright
html=Path(sys.argv[1]).resolve();outdir=Path(sys.argv[2]).resolve();outdir.mkdir(parents=True,exist_ok=True);anchors=sys.argv[3:]
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*a):pass
class S(socketserver.ThreadingTCPServer):request_queue_size=256;daemon_threads=True   # 几十张图并发请求时默认队列 5 会丢连接
srv=S(('127.0.0.1',0),functools.partial(Q,directory=str(html.parent)));port=srv.server_address[1]
threading.Thread(target=srv.serve_forever,daemon=True).start()
url=f'http://127.0.0.1:{port}/'+urllib.parse.quote(html.name)
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(channel='chrome');pg=await b.new_page(viewport={'width':1440,'height':1000});err=[]
        pg.on('pageerror',lambda e:err.append(str(e)));await pg.emulate_media(reduced_motion='reduce')
        await pg.goto(url)
        # 页面图片是懒加载（屏幕外 0×0、不下载），验收要检查全部图片，先改成立即加载
        await pg.evaluate("document.querySelectorAll('img[loading=lazy]').forEach(i=>i.loading='eager')");await pg.evaluate('document.fonts.ready')
        # 等图片全部加载（大页面 800ms 不够），最多 15 秒
        await pg.evaluate("()=>Promise.race([Promise.all([...document.images].map(i=>i.complete?0:new Promise(r=>{i.onload=i.onerror=r}))),new Promise(r=>setTimeout(r,15000))])");await pg.wait_for_timeout(300)
        r=await pg.evaluate('''()=>({width:innerWidth,scrollWidth:document.documentElement.scrollWidth,mathErrors:document.querySelectorAll('merror').length,figures:document.querySelectorAll('main figure').length,brokenImages:[...document.querySelectorAll('main figure img')].filter(i=>!(i.complete&&i.naturalWidth>0)).map(i=>i.getAttribute('src')),fonts:[...document.fonts].map(f=>f.family+':'+f.status),blocks:document.querySelectorAll('.block').length,details:document.querySelectorAll('details').length,badAnchors:[...document.querySelectorAll('a[href^="#"]')].filter(a=>!document.getElementById(decodeURIComponent(a.hash.slice(1)))).map(a=>a.hash),rawDollar:[...document.querySelectorAll('main p,main li,main td,main figcaption')].filter(e=>/\\$/.test(e.textContent)).length})''')
        await pg.screenshot(path=str(outdir/'top.png'))
        for a in anchors:
            await pg.locator(f'[id="{a}"]').evaluate('e=>e.scrollIntoView({block:"start"})');await pg.wait_for_timeout(150);await pg.screenshot(path=str(outdir/f'{a}.png'))
        if r['figures']:
            await pg.locator('main figure img').first.click();r['lightbox']=await pg.locator('dialog').evaluate('e=>e.open');await pg.locator('dialog .close').click()
            # 放大框里的图注要是原样的公式：用 textContent 复制会把 MathML 压成纯文字并带出 LaTeX 源码
            r['mathGlue']=await pg.evaluate(r"""()=>{const O='（(「“【《',C='，。、；：！？）」”】》';let n=0;for(const m of document.querySelectorAll('main math:not([display=block])')){if(m.closest('.mg'))continue;const a=m.previousSibling,b=m.nextSibling;if((a&&a.nodeType===3&&O.includes(a.data.slice(-1)))||(b&&b.nodeType===3&&C.includes(b.data[0])))n++}return n}""")
            r['lightboxMath']=await pg.evaluate("""()=>{const f=[...document.querySelectorAll('main figure')].find(f=>f.querySelector('figcaption math'));if(!f)return true;f.querySelector('.figure-open').click();const d=document.querySelector('dialog'),ok=d.querySelectorAll('p math').length===f.querySelectorAll('figcaption math').length;d.close();return ok}""")
        await pg.locator('#toggle').click();r['allExpanded']=await pg.locator('details').evaluate_all('ds=>ds.every(d=>d.open)')
        r['expandedOverflow']=await pg.evaluate('document.documentElement.scrollWidth>innerWidth')
        await pg.locator('#toggle').click();r['allCollapsed']=await pg.locator('details').evaluate_all('ds=>ds.every(d=>!d.open)')
        if await pg.locator('#cmap').count():
            # 阅读器：三种视图都有内容、原文模式去掉荧光、收起面板回到左侧目录版面；测完清掉页面状态
            rd={}
            await pg.evaluate("()=>{const h=[...document.querySelectorAll('main h2[id]')];h[Math.floor(h.length/2)].scrollIntoView({block:'start'});dispatchEvent(new Event('scroll'))}");await pg.wait_for_timeout(300)
            for v,sel in (('concept','#cmap .body .sec'),('outline','#cmap .ol .sec'),('map','#cmap .rm .card')):
                t=pg.locator(f'#cmap .tabs [data-v={v}]')
                if await t.is_hidden():rd[v]='无数据';continue
                await t.click();await pg.wait_for_timeout(250);rd[v]=await pg.locator(sel).count();await pg.screenshot(path=str(outdir/f'view-{v}.png'))
            await pg.locator('#cmap .plainbtn').click()
            rd['plain']=await pg.evaluate("()=>{const m=document.querySelector('main mark.hl');return document.documentElement.classList.contains('plain')&&(!m||getComputedStyle(m).backgroundImage==='none')}")
            await pg.locator('#cmap .plainbtn').click()
            await pg.locator('#cmap .x').click()
            rd['closed']=await pg.evaluate("()=>getComputedStyle(document.querySelector('#cmap')).display==='none'&&getComputedStyle(document.querySelector('aside')).display!=='none'")
            await pg.locator('#cmap-open').click()
            rd['reopened']=await pg.evaluate("()=>getComputedStyle(document.querySelector('#cmap')).display!=='none'")
            await pg.evaluate('localStorage.clear()');r['reader']=rd
        await pg.set_viewport_size({'width':1280,'height':900});r['narrowDesktop']=await pg.evaluate('({w:innerWidth,sw:document.documentElement.scrollWidth})')
        r['errors']=err;await b.close();return r
r=asyncio.run(main());srv.shutdown()
ok=r['scrollWidth']<=r['width'] and not r['mathErrors'] and not r['brokenImages'] and all(s.endswith('loaded') for s in r['fonts']) and not r['badAnchors'] and not r['rawDollar'] and r.get('lightbox',True) and r.get('lightboxMath',True) and not r.get('mathGlue',0) and r['allExpanded'] and not r['expandedOverflow'] and r['allCollapsed'] and r['narrowDesktop']['sw']<=r['narrowDesktop']['w'] and not r['errors'] and all(v not in (0,False) for v in r.get('reader',{}).values())
r['PASS']=ok
(outdir/'qa.json').write_text(json.dumps(r,ensure_ascii=False,indent=1));print(json.dumps(r,ensure_ascii=False))
