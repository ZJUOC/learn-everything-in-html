# Learn everything in HTML · 讲义 Skill

把学习材料整合成能独立自学的桌面 HTML 讲义（原名 course-lecture-notes）。目前支持三种输入：

- **课堂转写（含嵌图 DOCX）+ 课件 PDF + 教材**；
- **只有一本教材**（扫描版也行）：按目录选章节，逐页看图读书，例题和章末习题都整理进讲义；
- **一个领域或科研方向**：论文、综述、网页，或者只给一个主题（代理先列书单给你确认）。这是真实学习，不是应试。

动笔前，代理会问你要哪种**主线**把讲义串起来，见 [`references/mainlines.md`](references/mainlines.md)。选定后写进构建配置，以后不再问。

- 学一门课：**例题驱动**（默认推荐：例题从老师课件里的题、教材例题和习题里挑（课件题优先），每节先讲题、再讲结论和理论、最后附习题；保证读完能做出范围内全部课件题、作业、教材例题和习题，全部概念定义定理证明应用都讲到。边缘的题折叠或一句带过，同型题不重复，讲义不被题目淹没。由覆盖表和 `coverage_check.py` 核对）、概念体系、课堂顺序、题型归纳。
- 学一个领域：**问题驱动**（默认推荐）、发展脉络、概念体系、论文精读；不提供以题目为中心的主线。

每门课只出**一个页面**：正文带分色荧光，右侧阅读面板可切换概念关系图、概念大纲、荧光地图，并给 [Mac 触控板手写笔记](https://github.com/chinayuren2022-2025/mac-trackpad-notes) 的小窗留了位置：边看讲义，边在触控板上手写。

这是一个 [Claude Code](https://claude.com/claude-code) Skill（也适用于读 `SKILL.md` 的其他代理）。

## 能做什么

| 阶段 | 脚本 | 作用 |
|---|---|---|
| 建项目 | `scripts/new_project.py` | 新建项目或加一门课：目录、构建配置（含主线）、制作记录、目录页 |
| 读教材 | `scripts/textbook.py` | 看书签目录、判断有无文字层；按页渲染成图，附文字层或 OCR 供检索 |
| 盘点 | `scripts/new_materials.py` | 只列出还没处理过的材料（按 SHA-256 前 12 位比对记录） |
| 抽取 | `scripts/extract_docx.py` | 转写 DOCX 拆成约 1 万 token 的文字块，并抽出全部嵌图（DrawingML 和 VML 两种） |
| 看图 | `scripts/contact_sheet.py` | 20 图一张总览、坐标网格、按清单裁原图 |
| 构建 | `scripts/build_lecture.py` | Markdown → HTML 底稿（MathML 公式、语义块、练习折叠答案、中文字体子集） |
| 阅读器 | `scripts/reader/derive.py` | 底稿 → 读者打开的页面（荧光、概念关系、智慧区、手写区） |
| 全部重建 | `scripts/build_all.py` | 一条命令从源稿重建所有课程，用来验证可复现 |
| 题库 | `scripts/exam_bank.py` | 历年卷分卷拼成真题题库，运行每卷的独立验算脚本，统计范围与知识点（见 [`references/exam-bank.md`](references/exam-bank.md)） |
| 覆盖 | `scripts/coverage_check.py` | 核对覆盖表：教材每个例题、习题、定义、定理都有讲义位置，且位置真实存在 |
| 格式 | `scripts/format_check.py` | 检查不随主线变化的格式（学习路线、块标题、例题编号、练习与概念检查）；多份对照时列出结构画像 |
| 验收 | `scripts/desktop_qa.py` | Playwright 桌面截图，检查公式解析错误、残留 `$`、图片、锚点和阅读面板三种视图 |

### 阅读页面

- **荧光**：按句子作用分色：结论、方法、例子、易错、概念；另有手工挑的**词语荧光**（数据在 `制作记录/词语荧光/<课程>.txt`）和 `dense.py` 按分句自动补的浅一档**密集荧光**（约每 6 个汉字一处，只给视线落点）。底部按钮可换颜色、开关各类，“原文”一键去掉全部荧光。
- **右栏三种视图**：**概念**——当前小节的概念关系图，A → B 表示 B 用到 A，点概念跳到原文；概念关系是**手工整理**的文本文件，格式见 [`examples/概念关系示例.txt`](examples/概念关系示例.txt) 和 [`references/reader.md`](references/reader.md)，没有这个文件的课程只有另外两种视图。**大纲**——当前章的定义、定理、结论、例题、带框公式和关键词。**地图**——全部荧光句子的卡片。
- **手写区与智慧区**：右下虚线框给手写小窗让位；关掉手写区时显示本单元的“智慧”括号树（`制作记录/智慧/<课程>.txt`）。
- “×”收起面板，回到原讲义的左侧目录版面。

## 协作模式：省主模型额度

整门课从头写到尾，最贵的模型会烧掉大量额度。[`references/collaboration.md`](references/collaboration.md) 把活拆成三种角色：

- **总领**：和你对话的会话。负责写任务说明、审核、发布。
- **主笔**：能用的最强模型，可以是另一个 CLI 的无头模式（oh-my-pi、Claude Code、Codex），也可以是指定强模型的子代理。负责写正文。
- **杂工**：便宜的子代理。负责抽图、查页、写验算脚本、构建、QA。

只有比主模型弱的子代理时，文档写了怎么切分：要判断的部分留给强模型；交给弱模型的活要小、带证据、能用脚本验收；每个中间式都要数值核验。文档还附了任务说明模板和审核清单。

有历年卷时，先按 [`references/exam-bank.md`](references/exam-bank.md) 整理真题题库：

1. 收集、命名、归档原卷；
2. 分卷转写，回忆卷的存疑单独列出；
3. 每卷写独立验算脚本；
4. `exam_bank.py` 汇总；
5. 复核答案卷错误。

题库整理好后，再用它做真题驱动讲义、期末复习页和小测题型池。

## 和 Mac 触控板手写笔记的联动

生成页面时，`scripts/reader/trackpad_ink.py` 会从 Trackpad Studio 手写 App 的系统偏好设置里读出小窗尺寸（键名 `NSWindow Frame FloatingNotePanel`），作为手写区的默认大小。所以在 App 里调好小窗（⌃⌥N 呼出），重跑 `derive.py`，讲义的避让区就和小窗一样大。没装 App 时默认 750×470；也可以在页面上拖虚线框左上角的紫点手动校准。

```bash
python3 scripts/reader/trackpad_ink.py   # 打印 747×470（local.macwriting.trackpadstudio）
```

## 省 token 的设计

做一门课的讲义，最贵的是读材料和反复确认。这个 Skill 把能脚本化的步骤都脚本化，每一步只打印摘要：

- 新材料用 `new_materials.py` 一次列出，不用逐个查哈希、翻记录；
- 每份转写只读一遍，看图先看 20 图一张的总览；
- 整理概念关系时看 `concept_map.py skeleton` 打印的小节骨架（id、标题、加粗词），不用读整页 HTML；
- 构建、核验、验收都看 json 报告里的数字，不重读成品；
- 阅读页面一条命令生成，概念关系校验不过不写文件；`build_all.py` 一条命令从源稿重建全部课程。

具体规则写在 [`SKILL.md`](SKILL.md) 的“省 token 规则”一节，代理每次开工都会读到。

## 安装

```bash
git clone https://github.com/chinayuren2022-2025/learn-everything-in-html ~/.claude/skills/learn-everything-in-html
python3 ~/.claude/skills/learn-everything-in-html/scripts/new_project.py ~/讲义 01 光学 光学 --mainline 例题驱动 --input 单本教材
# 之后在 ~/讲义 里运行脚本即可；也可以 export LECTURE_ROOT=~/讲义
```

依赖：Python 3（`beautifulsoup4`、`fonttools`、`Pillow`、`playwright`、`jieba`、`pymupdf`）、[Pandoc](https://pandoc.org)；扫描版教材的检索用 `tesseract`（含 chi_sim）。中文字体默认 `~/Library/Fonts/SourceHanSerifCN-VF.ttf`（可在构建配置里改），没有时页面用系统宋体。

## 项目目录约定

```
ROOT/
├── 开始阅读.html、00 阅读指南.md
├── NN 课程名.html                 # 读者打开的唯一页面（derive.py 生成）
├── 资源/
│   ├── <课程>原图/、<课程>字体/
│   └── 阅读器/                     # derive.py 从 assets/reader 同步过来
└── 制作记录/
    ├── NN 记录.md                   # 决策、重构记录
    ├── 正文/<课程>正文N.md          # Markdown 源稿，图片写 资源/<课程>原图/xx.png
    ├── 构建/<课程>构建配置.json      # 输出到 构建/底稿/NN 课程名.html
    ├── 核验/validate_<课程>.py
    ├── 荧光标注修订.json
    ├── 概念关系/<课程>.txt、词语荧光/<课程>.txt、智慧/<课程>.txt
    └── 修订前备份/、归档/
```

## 许可

MIT
