"""讲义页面的两样手工内容（都可选）：

1. 概念小标题：概念关系 txt 的概念行写第 4 栏“注解”时，正文里该小节下插一个小标题（概念名）和一行注解。
   每节第一个概念紧跟小节标题；其余插在定位词第一次出现的块之前，顺序不倒退。
     概念名 | 依赖 | 定位词 | 一行注解（可含 $tex$）
2. 智慧区（只在有概念关系 txt 的课程生效）：ROOT/制作记录/智慧/<课程>.txt，每个单元（h2）一棵括号树，右下显示，打开公式区时收起。
     @单元id
     路径: 复积分 › 闭合曲线 › 存在奇点      ← 可省，显示在树上方
     根节点
       子节点（两空格一层）

apply(soup, course) 由 derive.py 在荧光之后调用；返回 (小标题数, 智慧单元数, 问题列表)。
"""
import json, re, subprocess, shutil, os
from bs4 import BeautifulSoup
from common import REC as R
from concept_map import parse

norm = lambda x: re.sub(r'\s+', '', x)


def md2html(items):
    """一次 pandoc，把若干行 markdown 转成 MathML 片段。"""
    if not items:
        return []
    sep = 'SEPSEPSEP'
    pd = shutil.which('pandoc') or os.path.expanduser('~/anaconda3/bin/pandoc')
    r = subprocess.run([pd, '-f', 'markdown-fancy_lists+tex_math_dollars', '-t', 'html5', '--mathml'],
                       input=f'\n\n{sep}\n\n'.join(items), capture_output=True, text=True, check=True).stdout
    parts = r.split(f'<p>{sep}</p>')
    assert len(parts) == len(items), (len(parts), len(items))
    return [re.sub(r'^\s*<p>|</p>\s*$', '', p.strip()) for p in parts]


def parse_wisdom(path):
    units, cur = {}, None
    for raw in path.read_text().splitlines():
        if not raw.strip() or raw.lstrip().startswith('#'):
            continue
        if raw.startswith('@'):
            cur = raw[1:].strip()
            units[cur] = {'path': '', 'lines': []}
        elif raw.startswith('路径:'):
            units[cur]['path'] = raw[3:].strip()
        else:
            ind = len(raw) - len(raw.lstrip(' '))
            units[cur]['lines'].append((ind // 2, raw.strip()))
    return units


def tree(nodes):
    def build(i, depth):
        out = []
        while i < len(nodes) and nodes[i][0] == depth:
            lab, j = nodes[i][1], i + 1
            if j < len(nodes) and nodes[j][0] > depth:
                kids, j = build(j, depth + 1)
                out.append(f'<div class="wz-br"><div class="wz-lab">{lab}</div><div class="wz-kids">{kids}</div></div>')
            else:
                out.append(f'<div class="wz-leaf">{lab}</div>')
            i = j
        return ''.join(out), i
    return build(0, 0)[0]


def apply(soup, course):
    probs = []
    secs, order = parse(R / '概念关系' / f'{course}.txt')
    noted = [(sid, k, nd) for sid in order for k, nd in enumerate(secs[sid]['nodes']) if nd.get('note')]
    wpath = R / '智慧' / f'{course}.txt'
    units = parse_wisdom(wpath) if wpath.exists() else {}
    wl = [lab for u in units.values() for _, lab in u['lines']]
    html = md2html([nd['note'] for *_, nd in noted] + wl)
    notes, wl = html[:len(noted)], html[len(noted):]

    # 1. 概念小标题
    n_head, last = 0, {}
    for (sid, k, nd), note in zip(noted, notes):
        h = soup.find(['h2', 'h3'], id=sid)
        if h is None:
            probs.append(f'找不到小节 #{sid}')
            continue
        sibs = []
        for el in h.find_next_siblings():
            if el.name in ('h2', 'h3'):
                break
            if 'cpt-head' not in (el.get('class') or []):
                sibs.append(el)
        if not sibs:
            continue
        lo = last.get(sid, -1)
        if k == 0:
            idx = 0
        else:
            idx = next((i for i, el in enumerate(sibs) if i > lo and norm(nd['at']) in norm(el.get_text())), None)
            if idx is None:
                idx = next((i for i, el in enumerate(sibs) if i >= max(lo, 0) and norm(nd['at']) in norm(el.get_text())), None)
            if idx is None:
                probs.append(f'#{sid} {nd["n"]}：定位词不在本节或在前一个概念之前，接在前一个概念后')
                idx = max(lo, 0)
        last[sid] = idx
        head = BeautifulSoup(f'<div class="cpt-head" data-c="{nd["n"]}"><div class="cpt-name">{nd["n"]}</div>'
                             f'<div class="cpt-note">{note}</div></div>', 'html.parser')
        sibs[idx].insert_before(head)
        n_head += 1

    # 2. 智慧区数据
    ids = {h.get('id') for h in soup.find_all('h2')}
    data, i = {}, 0
    for uid, u in units.items():
        labs = wl[i:i + len(u['lines'])]
        i += len(u['lines'])
        if uid not in ids:
            probs.append(f'智慧：找不到单元 #{uid}')
            continue
        data[uid] = {'path': u['path'], 'html': tree([(d, lab) for (d, _), lab in zip(u['lines'], labs)])}
    if data:
        blob = json.dumps(data, ensure_ascii=False).replace('</', '<\\/')
        tag = BeautifulSoup(f'<script id="wisdom-data" type="application/json">{blob}</script>', 'html.parser')
        cd = soup.find('script', id='concept-data')
        cd.insert_before(tag) if cd else soup.body.append(tag)
    return n_head, len(data), probs
