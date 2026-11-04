#!/usr/bin/env python3
"""行内公式和紧贴的标点不分行：把 “（” + <math> + “）/，/。” 包进（公式紧跟左括号再跟公式时连成一串） <span class="mg">（white-space:nowrap）。

Chrome 把行内 <math> 当成一个整体，却允许在它和中文括号、逗号之间换行：
窄表格里会出现 “fᵏ（” / “k≥1” / “）” 三行，或者一行以 “，” 开头。
不可见的禁止换行字符（U+2060）在 Chrome 里不起作用，只能用 nowrap 包起来。

只处理字符串里与 <math> 直接相邻的标点；先拆掉旧的 span.mg 再包，可以反复运行。
用法：
  脚本里：  from mathglue import glue, unglue;  html = glue(html)
  修已有页面：python3 mathglue.py 页面.html...   原地改，打印包了几处；页面 <style> 没有 .mg 规则时补上
"""
import re, sys

OPEN = '（(「『“‘【《〔['
CLOSE = '，。、；：！？）」』”’】》〕,.;:!?)]'
CSS = '.mg{white-space:nowrap}'
OLD = re.compile(r'<span class="mg">((?:(?!</span>).)*?)</span>', re.S)
M = r'<math\b(?![^>]*display="block")[^>]*>.*?</math>'
O, C = '[%s]' % re.escape(OPEN), '[%s]' % re.escape(CLOSE)
# 公式后直接跟左括号再跟公式（fᵏ（k≥1））时连成一串；逗号隔开的公式不连，免得正文出现过长的不换行段
TAIL = re.compile(rf'(</math>)((?:</(?:mark|strong|em|a)>)+)({C}+)')
PAT = re.compile(rf'({O}*)({M}{C}*(?:{O}+{M}{C}*)*)()', re.S)


def unglue(s):
    return OLD.sub(r'\1', s)


def glue(s, count=False):
    n = 0

    def one(m):
        nonlocal n
        x = m.group(2)
        if not m.group(1) and x.endswith('</math>') and x.count('<math') == 1:   # 两边都没有标点，不用包
            return m.group(0)
        n += 1
        return f'<span class="mg">{m.group(0)}</span>'
    s = TAIL.sub(r'\1\3\2', unglue(s))   # 公式在荧光/加粗末尾、逗号在标签外：把逗号挪进标签，才能和公式包在一起
    parts = re.split(r'(<script\b.*?</script>)', s, flags=re.S)   # 跳过脚本（concept-data 里的 JSON）
    s = ''.join(x if x.startswith('<script') else PAT.sub(one, x) for x in parts)
    if CSS not in s and '</style>' in s:
        s = s.replace('</style>', CSS + '</style>', 1)
    return (s, n) if count else s


if __name__ == '__main__':
    for f in sys.argv[1:]:
        s = open(f, encoding='utf-8').read()
        s2, n = glue(s, count=True)
        if s2 != s:
            open(f, 'w', encoding='utf-8').write(s2)
        print(f, n)
