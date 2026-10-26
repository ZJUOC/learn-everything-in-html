#!/usr/bin/env python3
"""汇总真题题库：拼接分卷 md，运行各卷验算脚本，统计范围与知识点。

用法：exam_bank.py <简称>
分卷      ROOT/制作记录/工作资料/<简称>题库分卷/<key>.md
卷序与头  ROOT/制作记录/工作资料/<简称>题库分卷/题库配置.json  {"order": [...], "header": "..."}
          （没有配置时按文件名排序，头只写一行标题）
验算脚本  ROOT/制作记录/核验/<简称>题库/<key>.py，运行后写同名 .json：{"total", "passed", "items": [{"id", "pass", ...}]}
输出      ROOT/制作记录/工作资料/<简称>真题题库.md（拼接稿，不要直接改）与 ROOT/制作记录/核验/<简称>真题题库核验.json
分卷格式见 references/exam-bank.md。ROOT 同 reader/common.py（环境变量 LECTURE_ROOT）。
"""
import json
import re
import subprocess
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent / 'reader'))
from common import REC

ITEM = re.compile(r"^- .*?题干：")
TAIL = re.compile(r"^## (答案卷问题|存疑)", re.M)
SCOPE = re.compile(r"\*\*范围\*\*：(范围内|部分范围内|后续)")
TOPIC = re.compile(r"\*\*知识点\*\*：([^；\n]+)")


def run_check(checks_dir: Path, key: str) -> dict:
    script = checks_dir / f"{key}.py"
    if not script.exists():
        return {"key": key, "error": "缺少验算脚本"}
    proc = subprocess.run([sys.executable, script.name], cwd=checks_dir,
                          capture_output=True, text=True, timeout=1800)
    out = checks_dir / f"{key}.json"
    if proc.returncode != 0 or not out.exists():
        return {"key": key, "error": (proc.stderr or proc.stdout)[-800:]}
    data = json.loads(out.read_text(encoding="utf-8"))
    failed = [i["id"] for i in data.get("items", []) if not i.get("pass")]
    return {"key": key, "total": data.get("total"), "passed": data.get("passed"), "failed": failed}


def main(course: str) -> int:
    parts = REC / "工作资料" / f"{course}题库分卷"
    if not parts.is_dir():
        sys.exit(f"找不到分卷目录 {parts}")
    cfg_path = parts / "题库配置.json"
    cfg = json.loads(cfg_path.read_text(encoding="utf-8")) if cfg_path.exists() else {}
    order = cfg.get("order") or sorted(p.stem for p in parts.glob("*.md"))
    header = cfg.get("header") or f"# {course} 真题题库\n\n由 exam_bank.py 从 `工作资料/{course}题库分卷/` 拼接生成，不要直接修改。\n"
    checks_dir = REC / "核验" / f"{course}题库"
    bank = REC / "工作资料" / f"{course}真题题库.md"
    report_path = REC / "核验" / f"{course}真题题库核验.json"
    body, stats, checks = [header], [], []
    scope_total: dict[str, int] = {}
    topics: dict[str, int] = {}
    for key in order:
        md = parts / f"{key}.md"
        if not md.exists():
            stats.append({"key": key, "error": "缺少分卷"})
            continue
        text = md.read_text(encoding="utf-8").strip()
        # 分卷的各级标题统一降一级，嵌入总库
        body.append(re.sub(r"^(#{1,5}) ", r"#\1 ", text, flags=re.M))
        main = TAIL.split(text, maxsplit=1)[0]
        n_items = sum(1 for l in main.splitlines() if ITEM.match(l))
        scopes = SCOPE.findall(main)
        for s in scopes:
            scope_total[s] = scope_total.get(s, 0) + 1
        for t in TOPIC.findall(text):
            for tid in re.split(r"\s*/\s*", t.strip()):
                topics[tid] = topics.get(tid, 0) + 1
        stats.append({"key": key, "items": n_items, "scope_tags": len(scopes)})
        checks.append(run_check(checks_dir, key))
    bank.write_text("\n\n".join(body) + "\n", encoding="utf-8")
    total = sum(c.get("total") or 0 for c in checks)
    passed = sum(c.get("passed") or 0 for c in checks)
    problems = [c for c in checks if c.get("error") or c.get("failed")]
    problems += [s for s in stats if s.get("error") or s.get("items") != s.get("scope_tags")]
    report = {"小题": sum(s.get("items", 0) for s in stats), "范围": scope_total,
              "知识点": dict(sorted(topics.items(), key=lambda kv: -kv[1])),
              "验算": {"total": total, "passed": passed}, "分卷": stats, "脚本": checks,
              "问题": problems}
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"小题 {report['小题']}，范围 {scope_total}，验算 {passed}/{total}，问题 {len(problems)}")
    return 0 if not problems else 1


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    raise SystemExit(main(sys.argv[1]))
