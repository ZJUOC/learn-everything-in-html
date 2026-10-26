---
name: learn-everything-in-html
description: Learn everything in HTML：把学习材料做成可独立自学的桌面 HTML 讲义，每个主题一个页面：分色荧光，右栏切换概念关系图/大纲/荧光地图，右下给 Mac 触控板手写小窗让位。三种输入：课堂转写（含嵌图 DOCX）+ 课件 + 教材；只有一本教材（含扫描版 PDF）；一个领域或科研方向（论文、综述、网页，或只给主题）。开工前问用户要哪种主线：课程类有例题驱动（覆盖全部教材例题习题与理论）、概念体系、课堂顺序、题型归纳；领域类有问题驱动、发展脉络、概念体系、论文精读。用户说“做讲义/把这本书做成讲义/我想学某个领域或方向/更新讲义/接着做某门课/资料齐了可以做了/改荧光/改概念关系/重建讲义”或提到 高效讲义、转写、课件、教材、手写区 时使用。流程以脚本为主，按“省 token 规则”执行。
---

# Learn everything in HTML · 讲义制作

S = 本 Skill 的 `scripts/`。ROOT = 讲义项目目录，按顺序取：环境变量 `LECTURE_ROOT` → 当前目录或其上级中含 `制作记录/构建/` 的目录 → `~/Library/Mobile Documents/com~apple~CloudDocs/Academic/高效讲义/`（作者本人的项目）。新项目用 `new_project.py` 创建。

已有项目开工前只读 ROOT 的 `AGENTS.md` 和**本课程**的制作记录。写正文前读 `references/standards.md`（约 3k token）和 `references/mainlines.md`；输入不是课堂转写（单本教材、领域 / 科研方向）时读 `references/inputs.md`；改阅读页面（荧光、概念关系、智慧区、面板）前读 `references/reader.md`。大活（整门课重写、补多次课、复习页、题库）想省主模型额度时，按 `references/collaboration.md` 的协作模式分工；有历年卷时先按 `references/exam-bank.md` 整理真题题库。

项目目录：根目录只放 `开始阅读.html`、`AGENTS.md`、`00 阅读指南.md`（可选）和每门课一个 `NN 课程.html`；图片字体在 `资源/`；源稿 `制作记录/正文/`，构建配置与底稿 `制作记录/构建/`，核验 `制作记录/核验/`，旧东西进 `制作记录/归档/`。不要在根目录新建别的版本文件。

## 省 token 规则（先于一切）

1. **脚本代替探索**：新材料用 `new_materials.py <材料目录>`，只打印没处理过的文件；不要 `ls`、`shasum`、翻记录去比对。处理完用 `--mark` 登记。
2. **每份材料只读一遍**：转写、教材页按顺序读完，边读边记要点；之后引用自己的笔记，不回头重读。
3. **图先看总览**：contact sheet 一张 20 图，只放大关键帧或关键页。
4. **写一次，查摘要**：正文每块一次 Write；构建、核验、QA 都看脚本打印的摘要和 json 中的计数，不重读成品 HTML。改错用 `grep -n` 定位后 Edit，不整文件重读。
5. **概念关系看骨架**：`reader/concept_map.py skeleton` 只列小节 id、标题、加粗词，起草概念图用它，不读整页。
   词语荧光同理：读一行一段的纯文本导出，`keywords.py` 只看匹配数和问题。
6. **验收看数字不看图**：桌面 QA 用 `desktop_qa.py` 的 PASS，格式用 `format_check.py`；浏览器里用 DOM 读数代替截图。用户说过“验收不用做”时，跳过可选的浏览器检查。
7. **正文、看图、自绘图不交给弱模型**（禁止用 Haiku 等小模型）。单干时不派子代理；用协作模式时，正文交给强模型主笔，弱子代理只做能用脚本验收的杂活，见 `references/collaboration.md`。
8. 版面改动先给草图；不在读者正在用的文件上改，生成新文件。

## 流程（按顺序，每步都有脚本）

0. **定输入、范围和主线（新课必做）**：
   - 判断输入类型：课堂转写、单本教材，还是领域 / 科研方向（`references/inputs.md`）。
   - 只有教材时先 `python3 $S/textbook.py toc <pdf>`，范围没说清就把目录给用户选。领域类先定主题边界和书单（inputs.md）。
   - **问用户要哪种主线**（`references/mainlines.md`），只列这种输入可选的：课程类是例题驱动 / 真题驱动（有历年卷时）/ 概念体系 / 课堂顺序 / 题型归纳，领域类是问题驱动 / 发展脉络 / 概念体系 / 论文精读（领域类不提供例题驱动、真题驱动和题型归纳）。用 AskUserQuestion，可以和范围放在同一次提问里。用户以前说过偏好就把它列为推荐项，否则课程类推荐“例题驱动”、领域类推荐“问题驱动”。配置里已有 `mainline` 就不再问。
   - `python3 $S/new_project.py <ROOT> <NN> <课程名> <简称> --mainline <主线> --input <输入类型> --source "<书名/课程与范围>"`：建目录、构建配置、制作记录、目录页；已有项目里加一门课也用它。
1. **盘点材料**：`python3 $S/new_materials.py <材料目录>`。课程是否每周只上一次、中间有没有缺课，要从转写的正文日期推断。
2. **读材料**：
   - 课堂转写：`python3 $S/extract_docx.py <scratchpad>/x <docx...>`，看输出里的 `head` 核对教师和正文日期；逐个 Read `chunk_K.txt`（每块约 1 万 token），**必须读完**，课间闲聊和噪声段快速略过，记下讲解思路、例题、口误和错误、作业线索；课件里的每道例题和练习记下页码，它们是讲义例题的首选来源。再 `python3 $S/contact_sheet.py sheets <x>/<stem>/index.json <scratchpad>/s`（最后一个参数是输出文件名前缀，生成 s_0.jpg…）看图，手写推导、作业页面要放大看清。
   - 教材（单独输入或作补充）：`python3 $S/textbook.py pages <pdf> <首页> <末页> <scratchpad>/tb`，逐页看图；文字层和 OCR **只做检索和定位**，题干、公式和图以页面图为准。细则见 `references/inputs.md`。
3. **定范围、建覆盖表**：只写范围内的内容（课堂：已授课；教材：用户选的章节；领域：定好的主题和书单）；作业或例题需要的前置概念可少量补充，并在记录里说明。覆盖表写在本课制作记录的“## 覆盖表”：范围内每道课件题（例题和练习）、教材例题、章末习题、作业题，以及每个定义、定理、证明、应用各占一行，格式见 mainlines.md“例题驱动”。覆盖表保证不漏，不等于每道题都写进讲义：边缘题折叠或一句带过，同型题只记“同类”。
4. **备份**：改已有讲义前，把旧的页面、正文 md 和入口页复制到 `ROOT/制作记录/修订前备份/<课程>v<N>/`。
5. **裁图**：`contact_sheet.py grid` 叠坐标网格定裁切框，再 `contact_sheet.py crop spec.json ROOT/资源/<简称>原图`。正文里图片写 `资源/<简称>原图/xx.png`。
6. **写正文**：按配置里的 `mainline` 组织（`references/mainlines.md` 有每种主线的小节顺序），格式按 standards；写到 `ROOT/制作记录/正文/<简称>正文N.md`，每块不超过约 25k 字符、一次写入。
7. **构建**：`python3 $S/build_all.py`（在 ROOT 里运行）。它对每个 `制作记录/构建/*构建配置.json` 跑 `build_lecture.py` 出底稿，再 `reader/derive.py` 生成根目录页面。只改了某一门课时也可以 `build_lecture.py <config>` + `reader/derive.py "<NN 课程>"`。改了 Skill 脚本时全部重建，并按 standards“复现”在副本里比对。本机没有思源宋体或 Anthropic 字体时会自动回退到系统字体，摘要里会提示。
8. **格式与覆盖检查**：`python3 $S/format_check.py "ROOT/制作记录/构建/底稿/NN 课程.html"`，要求 `PASS`；它检查 mainlines.md 末尾“不随主线变化的格式”。再 `python3 $S/coverage_check.py "ROOT/制作记录/NN <简称>制作记录.md" "ROOT/制作记录/构建/底稿/NN 课程.html"`，要求 `PASS`：覆盖表每行都有讲义位置，且位置真实存在。
9. **数学核验**（每个中间式，不只是最终答案）：写 `ROOT/制作记录/核验/validate_<简称>.py`，用 fractions/sympy/枚举/模拟独立复核**每个数值结论和练习答案**，输出 json 报告。
10. **阅读页面数据**：先 `python3 $S/reader/concept_map.py skeleton "<NN 课程>"`，按骨架**手工写** `ROOT/制作记录/概念关系/<NN 课程>.txt`（3 栏；没有它页面就没有“概念”视图，derive.py 会打印 ⚠）；再写 `词语荧光/<NN 课程>.txt`；用户要概念小标题、智慧区时才写第 4 栏和 `智慧/<NN 课程>.txt`（格式见 reader.md）。然后 `python3 $S/reader/derive.py "<NN 课程>"`（密集荧光自动补，不用写数据）。
11. **桌面验收**：`python3 $S/desktop_qa.py "ROOT/NN 课程.html" <scratchpad>/qa/<简称> <锚点id...>`，要求 `PASS: true`（含阅读面板三种视图、原文、收起；长公式需要横向滚动不算问题）；只抽看 3—4 张截图。
12. **收尾**：
    - 更新 `开始阅读.html`（`new_project.py` 生成的目录页会自动刷新）和 `00 阅读指南.md` 中该课程那一行。
    - 写本课制作记录：材料哈希前 12 位、范围、主线、纠错、练习与来源题号对照、核验结果、新经验。
    - 作者本人的项目还要在 `03 决策与修订日志.md` 末尾追加一段，并更新 `AGENTS.md` 的课程状态。
    - 新经验同时补进本 Skill 的 references。Skill 改完在 Skill 目录 commit 并 `git push`（作者本机一次推到个人仓库和 ZJUOC 两个远端）。

## 交付说明

用中文告诉用户：覆盖范围，主线，练习数量，核验结果，发现的材料错误（最重要的两三条），缺失的材料（例如作业清单），下一次课的日期（课堂转写时）。文件链接用绝对路径，空格写成 `%20`。
