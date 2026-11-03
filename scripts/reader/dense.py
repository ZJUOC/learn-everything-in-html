"""密集词语荧光：在手工词语荧光（mark.kw）之外，按分句自动给正文加浅一档的荧光（mark.kw2），让每句话隔几个词就有落点，便于跳读。

不追求严格的语义，只求“每个分句都有一两个抓手”：
- 分句：按中文标点切开文本节点，公式、加粗、已有词语荧光不动；句子荧光（mark.hl，定义/定理块整块都是）里面照常标，
  否则这些句子只有一层底色、没有落点；
- 挑词：jieba 词性分词，名词、动名词、实义动词、成语优先，相邻名词合并（“复合函数”）；
  加粗术语、概念关系里的概念名、手工荧光词作为词典并加分；
- 密度：分句每约 6 个汉字一个，最多 4 个；紧挨已加粗/已荧光处的短分句少标一个。
derive.py 在手工荧光之后调用 apply()；页面“词”菜单里可切换“密集/只标重点”。
单独试跑：python3 dense.py 课程  只打印统计和几段样例，不写文件。
"""
import re, sys, logging
from bs4 import NavigableString
from common import REC

import jieba, jieba.posseg as pseg
jieba.setLogLevel(logging.WARNING)

PUNCT = re.compile(r'([，。；：、！？,;:（）()“”「」《》\[\]—…\n])')
CJK = re.compile(r'[一-鿿]')
STOP = set('''我们 你们 他们 它们 这个 那个 这些 那些 这里 那里 这样 那样 这种 那种 一个 一种 一些 什么 怎么 为什么 怎样
就是 也是 还是 只是 都是 不是 可以 可能 能够 应该 需要 进行 得到 叫做 称为 所以 因为 如果 但是 然后 而且 并且 或者 以及
其中 时候 时间 已经 没有 同样 只要 只有 部分 方面 情况 地方 东西 一样 是否 之后 之前 以后 以前 现在 这时 此时 那么 于是
注意 看到 来看 来说 知道 觉得 发现 出现 表示 说明 意思 关系 一下 起来 下来 出来 过来 继续 直接 必须 一定 不能 不会 不要
正是 仍然 尤其 只需 只能 总是 同时 分别 相应 对应地 显然 容易 立刻 马上 再次 最后 首先 其次 所谓 本身 自身 也就是 换句话说
所有 每个 各个 任何 全部 两个 几个 本节 上面 下面 前面 后面 左边 右边 第一 第二 一般 通常 自然 当然 其实 实际上'''.split())
GOOD = ('n', 'vn', 'nz', 'l', 'i', 'j', 'an', 'nr', 'ns')


def _plain(t):
    return re.sub(r'\s+', '', t)


def domain_terms(soup, course):
    terms = {_plain(s.get_text()) for s in soup.main.find_all(['strong', 'mark']) if 'kw2' not in (s.get('class') or [])}
    f = REC / '概念关系' / f'{course}.txt'
    if f.exists():
        for ln in f.read_text().splitlines():
            if ln.strip() and not ln.startswith(('@', '#', '用到')):
                terms.add(_plain(ln.split('|')[0]))
    return {t for t in terms if 2 <= len(t) <= 8 and CJK.search(t) and '$' not in t}


def pick(seg, dom, n, cut=None):
    """在一个分句里挑 n 个不重叠的词，返回 [(start, end)]。"""
    toks, i = [], 0
    for w, f in (cut or pseg.cut)(seg):
        toks.append([w, f, i]); i += len(w)
    # 相邻名词合并
    merged = []
    for w, f, s in toks:
        if merged and f[0] == 'n' and merged[-1][1][0] == 'n' and w not in STOP and merged[-1][0] not in STOP and len(merged[-1][0]) + len(w) <= 6:
            merged[-1][0] += w
        else:
            merged.append([w, f, s])
    cand = []
    for w, f, s in merged:
        if len(w) < 2 or w in STOP or not CJK.search(w):
            continue
        if w in dom:
            sc = 10 + len(w)
        elif f.startswith(GOOD):
            sc = 4 + min(len(w), 4)
        elif f.startswith('v') and len(w) >= 2:
            sc = 2 + min(len(w), 3)
        elif f.startswith('a') and len(w) >= 2:
            sc = 1 + len(w)
        else:
            continue
        cand.append((sc, s, s + len(w)))
    out = []
    for sc, a, b in sorted(cand, key=lambda x: (-x[0], x[1])):
        if len(out) >= n:
            break
        if all(b + 2 <= x or a >= y + 2 for x, y in out):  # 不重叠、不紧挨
            out.append((a, b))
    return sorted(out)


def _marked(n):
    return n is not None and getattr(n, 'name', None) in ('strong', 'mark', 'math')


def _skip(t):
    return t.find_parent(['math', 'strong', 'a', 'code']) is not None or \
        t.find_parent(lambda x: x.name == 'mark' and {'kw', 'kw2'} & set(x.get('class') or [])) is not None


def apply(soup, course, only_hl=False):
    """only_hl=True 只补句子荧光里面的文字（给已生成、外面已有密集荧光的页面补漏，不动其余）。"""
    dom = domain_terms(soup, course)
    # 每门课一个新词典：同一进程里先后处理几门课时，前一门的概念词不会漏进后一门（否则单跑一门和全部重建结果不同）
    tk = jieba.Tokenizer()
    for t in dom:
        tk.add_word(t, 2000)
    cut = pseg.POSTokenizer(tk).cut
    paras = [p for p in soup.main.find_all(['p', 'li'])
             if not p.find_parent(['figcaption', 'table', 'nav', 'summary']) and not p.find(['p', 'li'])]
    total = 0
    for p in paras:
        for t in list(p.find_all(string=True)):
            if _skip(t) or (only_hl and t.find_parent('mark', class_='hl') is None):
                continue
            s = str(t)
            if len(CJK.findall(s)) < 3:
                continue
            parts = PUNCT.split(s)
            spans, off = [], 0
            for k, seg in enumerate(parts):
                if seg and not PUNCT.fullmatch(seg):
                    m = len(CJK.findall(seg))
                    n = min(4, max(1, round(m / 6))) if m >= 3 else 0
                    # 紧挨加粗/荧光（中间没有标点）的分句少标一个
                    if n and ((k == 0 and _marked(t.previous_sibling)) or (k == len(parts) - 1 and _marked(t.next_sibling))):
                        n -= 1 if m < 9 else 0
                    for a, b in pick(seg, dom, n, cut) if n else []:
                        spans.append((off + a, off + b))
                off += len(seg)
            if not spans:
                continue
            nodes, last = [], 0
            for a, b in spans:
                nodes.append(NavigableString(s[last:a]))
                k = soup.new_tag('mark', attrs={'class': 'kw2'}); k.string = s[a:b]; nodes.append(k)
                last = b
            nodes.append(NavigableString(s[last:]))
            t.replace_with(*nodes)
            total += len(spans)
    return total


def uncovered(soup, least=12):
    """验收：正文里汉字不少于 least、却没有任何词语荧光（kw/kw2）或加粗的段落，返回 [(前 30 字)]。"""
    out = []
    for p in soup.main.find_all(['p', 'li']):
        if p.find_parent(['figcaption', 'table', 'nav', 'summary']) or p.find(['p', 'li']) or 'block-title' in (p.get('class') or []):
            continue
        txt = ''.join(t for t in p.find_all(string=True) if not t.find_parent('math'))
        if len(CJK.findall(txt)) >= least and not p.select('mark.kw, mark.kw2, strong'):
            out.append(_plain(txt)[:30])
    return out


if __name__ == '__main__':
    from bs4 import BeautifulSoup
    from common import ROOT
    c = sys.argv[1]
    soup = BeautifulSoup((ROOT / f'{c}.html').read_text(), 'html.parser')
    n = apply(soup, c)
    chars = sum(len(CJK.findall(p.get_text())) for p in soup.main.find_all('p'))
    print(c, f'密集荧光 {n} 处，约每 {chars // max(n, 1)} 个汉字一处')
    for p in soup.main.find_all('p')[40:46]:
        print('  ', ''.join(f'【{x.get_text()}】' if getattr(x, 'name', '') == 'mark' and 'kw2' in x.get('class', [])
                            else f'〖{x.get_text()}〗' if getattr(x, 'name', '') in ('mark', 'strong') else x.get_text()
                            for x in p.children)[:200])
