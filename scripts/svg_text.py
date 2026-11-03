#!/usr/bin/env python3
"""自绘 SVG 图里的公式文字：把 e^(iπ/n)、e^z、1^√2 这类脱字符写法换成真正的上标（tspan）。

SVG 的 <text> 不认 LaTeX，也不认 ^：直接写进去，读者看到的就是源码。上标用 tspan 的 dy 抬高、缩小字号，
之后再用 dy 落回基线（不用 baseline-shift，Firefox 不支持）。下标继续用 Unicode 下标字符（zₙ、S₁）。

用法：
  画图脚本里： from svg_text import sup;  text 元素内容写 sup(t)（sup 会先做 XML 转义）
  修已有文件： python3 svg_text.py 图.svg...          原地改，打印改了几处
  只检查：     python3 svg_text.py --check 图.svg...   列出 <text> 里残留的 ^、\\frac、_{ 、$，有就退出码 1
"""
import html, re, sys

SUP = re.compile(r'\^(\((?:[^()]|\([^()]*\))*\)|[A-Za-z0-9√π]+)')
LEFT = re.compile(r'\^|\\[A-Za-z]+|_\{|\$')
RISE, SMALL = 0.36, 0.72   # 抬高 0.36 个字高，上标字号 72%


def esc(t):
    return str(t).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def sup(t, size=12):
    """纯文字 → 可放进 <text> 的内容（已转义）；size 是所在 <text> 的字号（px）。"""
    t, out, last, up = str(t), [], 0, False
    dy = round(RISE * size, 1)
    for m in SUP.finditer(t):
        body = m.group(1)
        if body.startswith('('):
            body = body[1:-1]
        before = t[last:m.start()]
        if before:
            out.append(f'<tspan dy="{dy}">{esc(before)}</tspan>' if up else esc(before))
            up = False
        out.append(f'<tspan dy="{-dy if not up else 0}" font-size="{round(size * SMALL, 1)}">{esc(body)}</tspan>')
        up, last = True, m.end()
    rest = t[last:]
    if up:
        out.append(f'<tspan dy="{dy}">{esc(rest) if rest else "&#8203;"}</tspan>')
    else:
        out.append(esc(rest))
    return ''.join(out)


TEXT = re.compile(r'(<text\b[^>]*>)(.*?)(</text>)', re.S)


def fix_svg(s):
    n = 0

    def one(m):
        nonlocal n
        head, body, tail = m.groups()
        if '<' in body or not SUP.search(html.unescape(body)):
            return m.group(0)
        size = float((re.search(r'font-size="([\d.]+)', head) or [0, 12])[1])
        n += len(SUP.findall(html.unescape(body)))
        return head + sup(html.unescape(body), size) + tail
    return TEXT.sub(one, s), n


def leftovers(s):
    return [html.unescape(re.sub(r'<[^>]+>', '', b)) for _, b, _ in TEXT.findall(s)
            if LEFT.search(html.unescape(re.sub(r'<[^>]+>', '', b)))]


if __name__ == '__main__':
    check = '--check' in sys.argv
    bad = 0
    for f in [a for a in sys.argv[1:] if a != '--check']:
        s = open(f, encoding='utf-8').read()
        if check:
            for x in leftovers(s):
                bad += 1
                print(f, '|', x[:80])
            continue
        s2, n = fix_svg(s)
        if n:
            open(f, 'w', encoding='utf-8').write(s2)
            print(f, f'上标 {n} 处')
    sys.exit(1 if bad else 0)
