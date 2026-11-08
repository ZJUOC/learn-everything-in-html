#!/usr/bin/env python3
"""把 Markdown 构建源编译成桌面 HTML 讲义。用法：build_lecture.py config.json

config 字段（路径相对 config 所在目录，除非为绝对路径）：
  sources: [md,...]      按顺序拼接的构建源
  merged: md             拼接结果（内部构建源，便于核查）
  output: html           构建输出。讲义写到 ROOT/制作记录/构建/底稿/NN 课程.html，再由 reader/derive.py 生成 ROOT/NN 课程.html；
                         不需要阅读器的独立页面（如题型池）直接写到 ROOT
  root: 目录              讲义成品所在的目录（ROOT），默认 output 所在目录；下面两个字体路径相对它
  pagetitle, course, coursesub, crumb, kicker, footer, footerlink
  latinfontdir: 拉丁字体目录（含 AnthropicSerif/Sans.woff2），如 资源/物理字体
  cjkfont: 中文子集字体路径（脚本会生成），如 资源/复变字体/SourceHanSerifCN-Subset.woff2
  cjk_source_font: 本机完整中文字体路径（默认思源宋体 VF）
  report: json           构建报告
约定：::: {.block .definition|theorem|result|example|warning} 语义块，首段 **标题**；
  练习用 ### 或 #### 标题 {#practice-xxx}，题干段落、公式和题图都会装进练习块，答案放 <details>；并排图用 <div class="figure-row"> 或 "figure-row three"。
  Pandoc 关闭 fancy_lists，"(1) " 开头的段落不会被当成列表。
  图片路径写 资源/<课程>原图/xx.png（相对 ROOT）。整理全部课程：python3 build_all.py
"""
import sys,json,re,subprocess,shutil,os
from pathlib import Path
from bs4 import BeautifulSoup
from fontTools import subset
cfg_path=Path(sys.argv[1]).resolve();base=cfg_path.parent;c=json.load(open(cfg_path))
P=lambda s:(Path(s) if Path(s).is_absolute() else base/s)
out=P(c['output']);merged=P(c['merged']);site=P(c['root']) if c.get('root') else out.parent
out.parent.mkdir(parents=True,exist_ok=True)
text='\n\n'.join(P(s).read_text() for s in c['sources'])
text=re.sub(r'\n(\((\d)\) )',lambda m:'\n\n'+m.group(1) if m.group(2)!='1' else '\n'+m.group(1),text)
merged.write_text(text)
tpl=Path(__file__).resolve().parent.parent/'assets/lecture-template.html'
# 中文字体子集
# 本机没有中文源字体或拉丁字体时不报错：去掉对应 @font-face，页面回退到系统字体（见 notes）
notes=[]
cjk=site/c['cjkfont'];cjk.parent.mkdir(parents=True,exist_ok=True)
src_font=Path(os.path.expanduser(c.get('cjk_source_font','~/Library/Fonts/SourceHanSerifCN-VF.ttf')))
if src_font.exists():
    o=subset.Options();o.flavor='woff2';o.recalc_timestamp=False
    f=subset.load_font(str(src_font),o);ss=subset.Subsetter(options=o)
    extra=''.join(str(c.get(k,'')) for k in ('pagetitle','course','coursesub','crumb','footer'))+'目录课程讲义展开答案与拓展收起打印保存关闭点击图片放大定义定理结论例题易错练习先独立作答提示解析核对'
    ss.populate(unicodes={ord(ch) for ch in text+extra if ord(ch)>=0x2E80});ss.subset(f);subset.save_font(f,str(cjk),o)
elif not cjk.exists():notes.append(f'没有中文源字体 {src_font}，用系统宋体')
latin_ok=(site/c.get('latinfontdir','')/'AnthropicSerif.woff2').exists()
if not latin_ok:notes.append('latinfontdir 下没有 AnthropicSerif/Sans.woff2，用系统字体')
args=['pandoc',str(merged),'-f','markdown-fancy_lists+tex_math_dollars+raw_html','-t','html5','--mathml','--standalone','--toc','--toc-depth=2','--template',str(tpl),'-o',str(out)]
for k in ('pagetitle','course','coursesub','crumb','kicker','footer','footerlink','latinfontdir','cjkfont'):args+=['-V',f'{k}={c.get(k,"")}']
pd=c.get('pandoc') or shutil.which('pandoc') or os.path.expanduser('~/anaconda3/bin/pandoc');args[0]=pd
p=subprocess.run(args,capture_output=True,text=True,check=True)
html=re.sub(r'<colgroup>.*?</colgroup>','',out.read_text(),flags=re.S)
if not latin_ok:html=re.sub(r'@font-face\{font-family:"Anthropic (Serif|Sans)";[^}]*\}','',html)
if not cjk.exists():html=re.sub(r'@font-face\{font-family:"Lecture Song";[^}]*\}','',html)
html=re.sub(r'<p>(<math display="block".*?</math>)</p>',r'<div class="display math">\1</div>',html,flags=re.S)
# \bar / \overline：Chrome 的 MathML 横线紧贴字母（\overline 还缩成一小段），换成 CSS 上边框，宽度随内容、留出间隙
# \bar（pandoc 记作 ‾）左右各缩 0.07em：相邻的 \bar A\bar B\bar C 横线分开，不会看成 \overline{ABC}
OVL='<mrow style="border-top:0.065em solid;padding-top:0.18em;margin-top:0.05em">'
BAR='<mrow style="border-top:0.065em solid;padding-top:0.18em;margin:0.05em 0.07em 0">'
def overline(h):
    pat=re.compile(r'<mo accent="true">([‾¯])</mo></mover>')
    while (m:=pat.search(h)):
        d=0
        for t in reversed(list(re.finditer(r'<mover>|</mover>',h[:m.start()]))):
            if t.group()=='</mover>':d+=1
            elif d:d-=1
            else:h=h[:t.start()]+(BAR if m.group(1)=='‾' else OVL)+h[t.end():m.start()]+'</mrow>'+h[m.end():];break
        else:raise ValueError('unbalanced mover')
    return h
html=overline(html)
soup=BeautifulSoup(html,'html.parser');main=soup.main
legend=BeautifulSoup('<div class="legend" aria-label="内容颜色说明"><span class="definition">定义</span><span class="theorem">定理</span><span class="result">结论</span><span class="example">例题</span><span class="warning">易错</span></div>','html.parser').div
main.find('h1').find_next_sibling('p').insert_after(legend)
counts={}
for block in main.select('div.block'):
    kind=[x for x in block['class'] if x!='block'][0];counts[kind]=counts.get(kind,0)+1
    q=block.find('p',recursive=False)
    if q and q.find('strong') and q.get_text().strip()==q.find('strong').get_text().strip():q['class']=['block-title']
for h in main.find_all(['h3','h4']):
    if not h.get('id','').startswith('practice-'):continue
    nodes=[]
    for n in h.find_next_siblings():
        if n.name not in ('p','ol','ul','div','figure') or (n.name=='div' and not {'display','figure-row'}&set(n.get('class',[]))):break
        nodes.append(n)
    if nodes:
        b=soup.new_tag('div',attrs={'class':'block example'});lab=soup.new_tag('div',attrs={'class':'block-title'});lab.string='练习 · 先独立作答';b.append(lab)
        nodes[0].insert_before(b)
        for n in nodes:b.append(n.extract())
        counts['practice']=counts.get('practice',0)+1
for fig in main.find_all('figure'):
    im=fig.find('img');b=soup.new_tag('button',attrs={'class':'figure-open','type':'button','aria-label':'放大：'+im.get('alt','配图')});im.wrap(b)
from mathglue import glue  # 行内公式和紧贴的标点不分行（见 mathglue.py）
out.write_text(glue(str(soup)))
r={'output':str(out),'source_chars':len(text),'html_bytes':out.stat().st_size,'math':len(main.find_all('math')),'figures':len(main.find_all('figure')),'details':len(main.find_all('details')),'blocks':counts,'pandoc_warnings':p.stderr,'notes':notes}
if c.get('report'):P(c['report']).write_text(json.dumps(r,ensure_ascii=False,indent=2))
print(json.dumps(r,ensure_ascii=False))
