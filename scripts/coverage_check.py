#!/usr/bin/env python3
"""核对覆盖表：教材的每个例题、习题、定义、定理……都在讲义里有位置，且这个位置真的存在。
用法：coverage_check.py <制作记录.md> <底稿.html>
覆盖表格式见 references/mainlines.md“例题驱动”：表头含“处理”“讲义位置”，每行一个来源条目（课件题、作业、教材例题、习题、定义、定理……）。
讲义位置写块标题的“类别 编号”（例 3、习题 5、P 2、定义 1、定理 2、结论 4）或小节 id（#fermat），可写多个。
处理：讲解 / 习题 / 折叠 / 带过 / 同类。折叠、带过写所在小节 #id；同类写所依据的例题、结论（讲义里不出现）。
打印 json：rows、by_type、by_handling、problems（必须为空）、length（篇幅提醒，不影响 PASS）。
知识点要从五种独立来源列行（mainlines.md“知识点清单”）：类型 术语 / 对比 / 方法 / 课堂讨论 / 思考题 各至少一行，
确实没有的在覆盖表一节写一行“不适用来源：对比（理由）”。类型为“术语”的行，术语本身（条目里“（”之前的部分）必须在讲义里加粗出现。
覆盖表只保证不漏；讲义要紧凑：每小节例题不超过 2 道、小节习题不超过 3 道，边缘题折叠或带过。
"""
import json, re, sys
from collections import Counter
from pathlib import Path
from bs4 import BeautifulSoup

HANDLING = ('讲解', '习题', '折叠', '带过', '同类')
SOURCES = ('术语', '对比', '方法', '课堂讨论', '思考题')   # 知识点清单的五种独立来源
LABEL = re.compile(r'(例|习题|P|定义|定理|结论)\s*(\d+)')


def cells_of(ln):
    """按未转义、不在 $…$ 和 `…` 里的竖线切分表格行；单元格里的 \\| 还原成 |。"""
    ln = ln.strip()
    ln = ln[1:] if ln.startswith('|') else ln
    ln = ln[:-1] if ln.endswith('|') and not ln.endswith('\\|') else ln
    cells, cur, inmath, incode, i = [], '', False, False, 0
    while i < len(ln):
        ch = ln[i]
        if ch == '\\' and i + 1 < len(ln) and ln[i + 1] == '|':
            cur += '|'; i += 2; continue
        if ch == '`' and not inmath:
            incode = not incode
        elif ch == '$' and not incode:
            inmath = not inmath
        if ch == '|' and not inmath and not incode:
            cells.append(cur.strip()); cur = ''
        else:
            cur += ch
        i += 1
    cells.append(cur.strip())
    return cells


def table(md):
    """记录里“## 覆盖表”一节的表格 → [(条目, 类型, 位置)]。"""
    sec = re.search(r'^## 覆盖表\s*$(.*?)(?=^## |\Z)', md, re.M | re.S)
    if not sec:
        return None
    rows, head = [], None
    for ln in sec.group(1).splitlines():
        if not ln.strip().startswith('|'):
            continue
        cells = cells_of(ln)
        if head is None:
            head = cells
            continue
        if set(''.join(cells)) <= set('-: '):
            continue
        d = dict(zip(head, cells))
        rows.append((d.get('来源条目', d.get('教材条目', cells[0])), d.get('类型', ''), d.get('讲义位置', ''), d.get('处理', '')))
    return rows


def targets(m):
    """讲义里存在的位置：块标题与练习标题的“类别 编号”，以及所有 id。"""
    have = {f'#{t["id"]}' for t in m.find_all(id=True)}
    titles = [t.get_text(' ', strip=True) for t in m.select('.block-title')]
    titles += [h.get_text(' ', strip=True) for h in m.find_all(['h3', 'h4']) if h.get('id', '').startswith('practice-')]
    for t in titles:
        x = re.match(r'(例|习题|P|定义|定理|结论)\s*(\d+)', t)
        if x:
            have.add(f'{x.group(1)} {x.group(2)}')
    return have


def section_of(m, sid):
    """小节 id → 该小节到下一个 h2/h3 为止的节点。"""
    h = m.find(id=sid)
    out = []
    for n in (h.find_next_siblings() if h else []):
        if n.name in ('h2', 'h3'):
            break
        out.append(n)
    return out


def length(m):
    """篇幅提醒：例题、小节习题过多的小节。"""
    warn = []
    for h in m.find_all('h3'):
        if h.get('id', '').startswith('practice-'):
            continue
        nodes = section_of(m, h.get('id')) if h.get('id') else []
        ex = sum(1 for n in nodes for b in ([n] if 'block' in (n.get('class') or []) else n.select('div.block') if hasattr(n, 'select') else [])
                 if 'example' in b['class'] and not (b.find(class_='block-title') or b).get_text().strip().startswith('练习'))
        pr = sum(1 for n in nodes if n.name == 'h4' and n.get('id', '').startswith('practice-'))
        if ex > 2 or pr > 3:
            warn.append(f'{h.get_text(" ", strip=True)[:20]}：例题 {ex} 道、小节习题 {pr} 道（建议 ≤2、≤3，其余折叠或带过）')
    return warn


def check(record, html):
    rows = table(Path(record).read_text())
    if rows is None:
        return {'PASS': False, 'problems': ['记录里没有“## 覆盖表”一节']}
    m = BeautifulSoup(Path(html).read_text(), 'html.parser').main
    have = targets(m)
    probs = []
    for item, kind, loc, how in rows:
        if loc.startswith('同类'):          # 旧写法“同类：例 6”
            how, loc = how or '同类', loc.partition('：')[2] or loc[2:]
        refs = [f'{a} {b}' for a, b in LABEL.findall(loc)] + re.findall(r'#[A-Za-z0-9_-]+', loc)
        if how and how not in HANDLING:
            probs.append(f'处理应为 {"/".join(HANDLING)}：{item} → {how}')
        if not loc:
            probs.append(f'没有讲义位置：{item}')
        elif not refs:
            probs.append(f'看不出讲义位置（应写 例 k / 习题 k / 定理 k / #id）：{item} → {loc}')
        for r in refs:
            if r not in have:
                probs.append(f'讲义里找不到 {r}：{item}')
        if how == '折叠':
            ids = [r[1:] for r in refs if r.startswith('#')]
            if not ids:
                probs.append(f'折叠的题要写所在小节 #id：{item}')
            elif not any(d.summary and d.summary.get_text().strip().startswith(('更多课本习题', '教材思考题'))
                         for i in ids for n in section_of(m, i) for d in ([n] if n.name == 'details' else n.find_all('details') if hasattr(n, 'find_all') else [])):
                probs.append(f'{ids[0]} 小节里没有“更多课本习题”或“教材思考题”折叠栏：{item}')
    # 知识点来源：只从定义、定理块抄出来的理论行会漏掉方法、术语、对比和课堂讨论
    md = Path(record).read_text()
    waived = {s for ln in re.findall(r'^不适用来源[:：](.+)$', md, re.M) for s in SOURCES if s in ln}
    kinds = {r[1] for r in rows}
    for s in SOURCES:
        if s not in kinds and s not in waived:
            probs.append(f'覆盖表没有“{s}”类的行：按 mainlines.md“知识点清单”补列，确实没有就写“不适用来源：{s}（理由）”')
    bold = {b.get_text(' ', strip=True) for b in m.find_all('strong')}
    bold |= {t.get_text(' ', strip=True) for t in m.select('.block-title')}
    for item, kind, loc, how in rows:
        term = re.split(r'[（(]', item)[0].strip()
        if kind == '术语' and not any(term in b for b in bold):
            probs.append(f'术语没有在讲义里加粗给出：{term}')
    return {'PASS': not probs and bool(rows), 'rows': len(rows),
            'by_type': dict(Counter(r[1] or '未写类型' for r in rows)),
            'by_handling': dict(Counter(r[3] or ('同类' if r[2].startswith('同类') else '未写处理') for r in rows)),
            'problems': probs or ([] if rows else ['覆盖表是空的']),
            'length': length(m)}


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    r = check(*sys.argv[1:])
    print(json.dumps(r, ensure_ascii=False, indent=1))
    sys.exit(0 if r['PASS'] else 1)
