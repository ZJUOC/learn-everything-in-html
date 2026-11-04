"""由讲义底稿生成读者打开的唯一页面 ROOT/NN 课程.html，只打印摘要（省 token）。

python3 derive.py [课程...]   默认全部课程
步骤：同步 assets → 句子荧光（highlight.py）→ 词语荧光（keywords.py，有 txt 才做）→ 密集荧光（dense.py，LECTURE_DENSE=0 关闭）
      → 概念小标题与智慧区（wisdom.py）→ 图片懒加载、按章包 section.lz（perf）→ 嵌入概念关系数据（concept_map.py）。
右栏三种视图（概念 / 大纲 / 地图）、右下公式区与智慧区、原文模式、收起面板都由 assets/reader/reader.js 在页面里完成。
"""
import hashlib, json, os, re, sys
from common import ROOT, REC, TOOLS, COURSES, sync_assets
from highlight import process
from concept_map import build
from keywords import apply as kw_apply
from dense import apply as dense_apply, uncovered
from wisdom import apply as wisdom_apply
from bs4 import BeautifulSoup
from common import base
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mathglue import glue, unglue   # 行内公式和紧贴的标点不分行

DENSE = os.environ.get('LECTURE_DENSE', '1') != '0'


def perf(soup):
    """省内存：正文图片懒加载；每章（h2 到下一个 h2）包进 section.lz，reader.css 用 content-visibility 跳过屏幕外章节的样式和排版。"""
    for img in soup.select('main img[src]'):
        img['loading'], img['decoding'] = 'lazy', 'async'
    for h in soup.main.find_all('h2', recursive=False):
        nxt = h.find_next_sibling()
        if nxt is not None and nxt.name == 'section' and 'lz' in (nxt.get('class') or []):
            continue
        items, n = [], h.next_sibling
        while n is not None and getattr(n, 'name', None) not in ('h2', 'footer'):
            items.append(n)
            n = n.next_sibling
        sec = soup.new_tag('section', attrs={'class': 'lz'})
        h.insert_after(sec)
        for x in items:
            sec.append(x.extract())
print('ROOT', ROOT, '课程', len(COURSES))
sync_assets()
ver = hashlib.sha1(b''.join((TOOLS / f).read_bytes() for f in ('reader.css', 'reader.js'))).hexdigest()[:8]
report, missing = {}, []
for c in sys.argv[1:] or COURSES:
    soup = BeautifulSoup(unglue(base(c).read_text()), 'html.parser')
    st = {}
    n = process(soup, st)
    report[c] = {'total': n, **{k: v for k, v in st.items() if k != '_samples'}, 'samples': st.get('_samples', {})}
    msg = [f'句子荧光 {n} 处']
    data = {}
    if (REC / '概念关系' / f'{c}.txt').exists():
        data, probs = build(c)
        hard = [p for p in probs if '定位词' not in p]
        if hard:
            print(c, '概念关系有错：', *hard, sep='\n  ')
            sys.exit(1)
        if probs:
            msg.append(f'{len(probs)} 处定位退回标题')
    else:
        missing.append(c)
    if (REC / '词语荧光' / f'{c}.txt').exists():
        done, bold, miss = kw_apply(soup, c)
        msg.append(f'词语荧光 {done} 处' + (f'，{len(miss)} 个问题：' + '；'.join(miss) if miss else ''))
    if DENSE:
        msg.append(f'密集荧光 {dense_apply(soup, c)} 处')
        bare = uncovered(soup)
        if bare:
            msg.append(f'⚠ {len(bare)} 段没有词语荧光：' + '；'.join(bare[:3]))
    if data:
        nh, nw, wp = wisdom_apply(soup, c)
        if nh or nw or wp:
            msg.append(f'概念小标题 {nh} 个  智慧 {nw} 个单元' + (f'，{len(wp)} 个问题：' + '；'.join(wp) if wp else ''))
    perf(soup)
    blob = BeautifulSoup('<script id="concept-data" type="application/json"></script>', 'html.parser').script
    blob.string = json.dumps(data, ensure_ascii=False).replace('</', '<\\/')
    soup.head.append(soup.new_tag('link', rel='stylesheet', href=f'资源/阅读器/reader.css?v={ver}'))
    soup.body.append(blob)
    soup.body.append(soup.new_tag('script', src=f'资源/阅读器/reader.js?v={ver}'))
    (ROOT / f'{c}.html').write_text(glue(str(soup)))
    print(c, 'ok ', '  '.join(msg))
(REC / '构建' / '荧光标注报告.json').write_text(json.dumps(report, ensure_ascii=False, indent=1))
if missing:
    print('⚠ 以下课程没有概念关系，页面只有“大纲”“地图”两种视图：', '、'.join(missing))
    print('  先跑 concept_map.py skeleton "<课程>" 看小节骨架，写 ROOT/制作记录/概念关系/<课程>.txt（格式见 references/reader.md），再跑 derive.py')
