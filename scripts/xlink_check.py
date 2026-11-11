#!/usr/bin/env python3
"""跨讲义跳转落点检查。
用法：xlink_check.py <ROOT> [网站根 URL]
收集 ROOT 下所有页面里指向其他页面的 `xxx.html#锚点` 链接，逐个“带 #锚点 全新打开”（与读者点跨讲义链接时一样），
等 4.5 s 排版稳定后读目标离视口顶部的距离，要求在 −5～600 px。不给 URL 时本地起 HTTP 服务测 ROOT；给 URL（如
https://yeshuangxixue.cn/notes/）时测线上网站。全部通过退出码 0，否则 1。

为什么需要：主讲义的章节是 section.lz（content-visibility + 估高），浏览器默认的一次性锚点跳转会被途经章节的真实高度挤偏，
2026-11-11 网站上 107 个跨讲义链接偏了 94 个（几百到上万像素）。reader.js 的 settle() 负责反复对位；改了 reader.js、
derive.py 的 perf()、reader.css 的 content-visibility，或新增带跨讲义链接的页面后都要跑。"""
import sys,re,json,asyncio,threading,functools,http.server,socketserver,urllib.parse
from pathlib import Path
from playwright.async_api import async_playwright
root=Path(sys.argv[1]).resolve(); base=sys.argv[2] if len(sys.argv)>2 else None
if base and not base.endswith('/'): base+='/'
pairs=set()
for f in root.glob('*.html'):
    for href,a in re.findall(r'href="([^"#:]+\.html)#([^"]+)"',f.read_text(encoding='utf-8')):
        tgt=urllib.parse.unquote(href)
        if tgt!=f.name and (root/tgt).exists(): pairs.add((tgt,urllib.parse.unquote(a)))
pairs=sorted(pairs)
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*a):pass
class S(socketserver.ThreadingTCPServer):request_queue_size=256;daemon_threads=True
if not base:
    srv=S(('127.0.0.1',0),functools.partial(Q,directory=str(root)));threading.Thread(target=srv.serve_forever,daemon=True).start()
    base=f'http://127.0.0.1:{srv.server_address[1]}/'
async def one(b,sem,page,a,out):
    async with sem:
        top='打不开'
        for _ in range(3):   # 线上测试偶尔遇到网络抖动（ERR_NETWORK_CHANGED 等），重试两次
            pg=await b.new_page(viewport={'width':1440,'height':1000})
            try:
                await pg.goto(base+urllib.parse.quote(page)+'#'+urllib.parse.quote(a),wait_until='load',timeout=60000)
                await pg.wait_for_timeout(4500)
                top=await pg.evaluate("a=>{const e=document.getElementById(a);return e?Math.round(e.getBoundingClientRect().top):null}",a);break
            except Exception as e:top='打不开：'+str(e).split('\n')[0][:80]
            finally:await pg.close()
        out.append((page,a,top))
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(channel='chrome');sem=asyncio.Semaphore(6);out=[]
        await asyncio.gather(*[one(b,sem,pg,a,out) for pg,a in pairs]);await b.close();return out
out=asyncio.run(main())
bad=[x for x in out if not isinstance(x[2],int) or not (-5<=x[2]<=600)]
print(json.dumps({'base':base,'links':len(out),'bad':len(bad),'PASS':not bad,'badList':bad[:30]},ensure_ascii=False))
sys.exit(1 if bad else 0)
