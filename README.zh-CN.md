# project-to-resume

`project-to-resume` 是一个工具无关的项目转简历工作流，用来把真实的代码项目转化成高质量、可信的求职材料。

它既可以作为 Codex Skill 使用，也可以被 Claude Code、Gemini CLI、Cursor、GitHub Copilot、Aider 等 AI Coding 工具直接调用。只要工具能读取文件并运行本地 Python 脚本，就可以使用这套工作流。

GitHub：<https://github.com/zq673808264/project-to-resume>

核心目标：

> 把项目过程中的真实技术含量，转化成招聘语言，而不是凭空包装。

## 可以生成什么

- 中文简历项目经历
- 英文简历项目经历
- 前端 / 后端 / 全栈 / AI 工程 / 数据岗位版本
- 校招 / 实习 / 社招版本
- STAR 格式面试讲述
- 面试官可能追问的问题与回答思路
- LinkedIn 或作品集项目介绍
- GitHub README 展示文案优化建议
- 技术博客大纲
- 单个项目的完整求职材料包

## 为什么需要它

项目刚完成时，最有价值的细节通常还很清楚：

- 项目目标是什么
- 解决了什么问题
- 实现了哪些模块
- 做过哪些技术决策
- 遇到了哪些 bug、难点和取舍
- AI 工具帮了哪些部分
- 用户自己负责了哪些需求拆解、代码审查、调试、集成和验证工作

但很多人会等到真正投简历时才开始回忆，结果最有技术含量的细节已经模糊了。

这个 Skill 的思路是：**项目过程中持续记录，项目结束后自动汇总成简历和面试材料。**

## 文件结构

```text
project-to-resume/
├── SKILL.md
├── agents/
│   └── openai.yaml
├── examples/
│   ├── sample-evidence-pack.md
│   └── sample-output.zh.md
├── references/
│   ├── career_artifact_outputs.md
│   └── resume_entry_style.md
├── resume/
│   └── 原始简历放在这里
├── career-output/
│   └── <人员名>/
│       └── 生成的简历和求职材料放在这里
├── templates/
│   ├── interview-qa.md
│   ├── linkedin-post.md
│   ├── portfolio-page.md
│   ├── resume-entry.en.md
│   └── resume-entry.zh.md
├── scripts/
    ├── lib/
    │   └── resume_text.py
    ├── collect_project_context.py
    ├── draft_career_artifacts.py
    ├── export_resume_docx.py
    ├── prepare_resume_workspace.py
    └── update_dev_log.py
└── tests/
    ├── fixtures/
    └── test_workflow.py
```

## 安装方式

### Codex Skill

克隆仓库：

```bash
git clone https://github.com/zq673808264/project-to-resume.git
```

如果希望 Codex 自动发现这个 Skill，可以把整个文件夹放到 Codex 的 skills 目录：

```text
~/.codex/skills/project-to-resume
```

Windows 通常是：

```text
C:\Users\<你的用户名>\.codex\skills\project-to-resume
```

如果只是本地开发和测试，也可以在提示词中直接引用这个 Skill 所在路径。

### 其他 AI Coding 工具

Claude Code、Gemini CLI、Cursor、GitHub Copilot、Aider 等工具可以直接使用本仓库，并让 AI 助手按照 README 的流程运行脚本。核心脚本都是普通 Python 脚本，不依赖 Codex 专属 API。

最小提示词：

```text
请按照这个仓库 README 中的 workflow，把我的项目整理成真实可信的简历和面试材料。不要编造指标或没有证据的经历。
```

## 使用方法

### 1. 准备项目文件夹

在其他项目里使用这个 workflow 时，先在目标项目里创建输入/输出文件夹：

```bash
python /path/to/project-to-resume/scripts/prepare_resume_workspace.py --project /path/to/project
```

这会创建：

```text
/path/to/project/resume/
/path/to/project/career-output/
```

然后询问用户是否要添加已有简历或目标岗位 JD。如果需要，就让用户把文件放进 `/path/to/project/resume/`；如果不需要，就继续走空白简历路径，并生成新的简历输出文件。

### 2. 收集项目证据

对某个项目运行证据收集脚本：

```bash
python scripts/collect_project_context.py --project /path/to/project --out project_resume_evidence.md
```

如果有已有简历，可以一起传入：

```bash
python scripts/collect_project_context.py --project /path/to/project --resume /path/to/resume.pdf --out project_resume_evidence.md
```

如果有目标岗位 JD，也可以一起传入：

```bash
python scripts/collect_project_context.py --project /path/to/project --job-description /path/to/jd.md --out project_resume_evidence.md
```

如果要同时处理多个人的简历，建议按人员分目录输出：

```bash
python scripts/collect_project_context.py \
  --project /path/to/project \
  --resume resume/alice.pdf \
  --job-description /path/to/jd.md \
  --out-dir career-output \
  --person-name "Alice Zhang" \
  --out evidence.md
```

会输出到 `career-output/Alice-Zhang/evidence.md`。

生成的证据包会包含：

- 项目目录结构
- 检测到的语言和技术栈信号
- 检测到的项目类型信号
- README 和文档片段
- 配置文件和依赖文件信息
- git 分支、状态和近期 commit
- 开发日志、聊天记录、PR 记录、issue 记录
- 可提取的已有简历文本
- 目标岗位 JD 文本
- JD 关键词匹配分析

### 3. 持续记录开发过程

项目开发过程中，可以随时追加开发日志：

```bash
python scripts/update_dev_log.py --project /path/to/project
```

也可以直接传入本次开发记录：

```bash
python scripts/update_dev_log.py \
  --project /path/to/project \
  --completed "实现了从 README 和配置文件中收集项目证据的功能。" \
  --blockers "PDF 提取依赖当前 Python 环境中可用的 PDF 库。" \
  --ai-help "Codex 辅助生成了第一版实现。" \
  --decisions "保留证据优先原则，不直接覆盖用户原始简历。" \
  --validation "在示例简历上运行收集脚本，并检查生成的 Markdown。" \
  --signal "体现了构建 AI 辅助开发工具和真实性约束工作流的能力。"
```

默认会生成或更新：

```text
career/project-dev-log.md
```

### 4. 生成模板化初稿

基于证据包生成保守的第一版求职材料草稿：

```bash
python scripts/draft_career_artifacts.py \
  --evidence career-output/Alice-Zhang/evidence.md \
  --out-dir career-output \
  --person-name "Alice Zhang" \
  --mode career-pack
```

默认生成：

- `resume-entry.zh.md`
- `resume-entry.en.md`
- `interview-qa.md`
- `portfolio-linkedin.md`
- `technical-blog-outline.md`

这些初稿只是 first draft，不建议直接投递。适合再交给 Codex 根据证据包和目标岗位继续润色。

### 5. 同时导出 Markdown 和 Word

把生成好的项目经历同时导出为 Markdown 和 Word：

```bash
python scripts/export_resume_docx.py \
  --entry career-output/Alice-Zhang/resume-entry.zh.md \
  --resume resume/original-resume.docx \
  --out-dir career-output \
  --person-name "Alice Zhang"
```

处理逻辑：

- 如果原始简历是 `.docx`，脚本会复制原简历，并把项目经历追加到新的 Word 文件中。
- 如果原始简历是 `.pdf`，脚本会自动提取 PDF 文本，再按模板生成一份新的 Word 简历。
- PDF 提取后会先做重排清洗，尽量合并被 PDF 切碎的换行，并识别常见简历栏目。
- 如果原始简历是 `.md` 或 `.txt`，脚本会用原文本加项目经历生成新的 Word 简历。
- 不会覆盖原始简历文件。
- 默认会输出到 `career-output/<人员名>/`，避免多个人的简历混在一起。

## 测试

运行完整工作流测试：

```bash
python tests/test_workflow.py
```

测试使用的是 `tests/fixtures/` 下的虚构项目、虚构简历和虚构 JD。

### 6. 在 Codex 中调用 Skill

示例提示词：

```text
Use $project-to-resume to turn this completed project into a Chinese resume project entry.
```

```text
Use $project-to-resume to generate a career pack for this AI-assisted coding project, including resume bullets, interview Q&A, LinkedIn copy, and a blog outline.
```

```text
Use $project-to-resume to create frontend, backend, full-stack, and AI engineering versions of this project experience.
```

中文也可以这样说：

```text
使用 $project-to-resume，把这个项目整理成中文简历项目经历，并补充面试追问和回答思路。
```

## 真实性原则

这个 Skill 的重点不是“夸项目”，而是把真实完成的内容讲清楚。

它不应该虚构：

- 用户数量
- 收入或商业结果
- 团队规模
- 性能提升比例
- 准确率
- 生产环境部署
- 业务影响
- 项目中不存在的技术栈

如果某个有价值的说法没有代码、文档、日志、commit 或用户确认支撑，就应该标记为待确认，而不是直接写进简历。

例如，不要在没有证据时写：

```text
将开发效率提升 80%。
```

可以写成：

```text
优化项目复盘与简历整理流程，降低手动回忆和反复改写成本。
```

## AI 辅助编码项目怎么表达

对于 AI 辅助开发项目，建议诚实表达，不回避 AI，也不抹掉用户自己的工程能力。

可以表达为：

```text
使用 Codex / Claude Code 等 AI 工具辅助生成初版代码和探索实现方案，个人负责需求拆解、技术选型、代码审查、调试验证、模块集成与结果评估。
```

这个角度适合回答面试中的问题：

- 这个项目是不是 AI 写的？
- 你自己具体做了什么？
- 你如何验证 AI 生成代码的正确性？
- 项目最大的技术难点是什么？
- 如果继续优化，你会怎么做？

## 示例输出结构

```md
## 项目名称 | 技术栈

角色：开发者 / AI 辅助开发工作流设计者
时间：YYYY.MM - YYYY.MM

- 基于 xxx 设计并实现 xxx，支持 xxx 流程。
- 封装 xxx 模块，统一 xxx 逻辑，降低重复维护成本。
- 集成 xxx 工具 / API / 模型，实现 xxx 自动化能力。
- 通过 xxx 测试 / 日志 / 校验机制，保障 xxx 的可靠性。

### 技术亮点

- ...

### 面试讲述要点

- ...

### 待确认问题

- 是否有可量化指标，如部署地址、用户数量、测试覆盖率、响应速度、准确率或节省时间？
```

更多示例：

- `examples/sample-evidence-pack.md`
- `examples/sample-output.zh.md`

## 当前状态

当前仓库已经包含第一版可用 Skill：

- Skill 主说明
- 简历写作风格参考
- Career Artifact 输出规范
- 项目证据收集脚本
- 模板化初稿生成脚本
- Markdown 和 Word 导出脚本
- 持续开发日志脚本
- 输出模板
- 示例证据包和示例输出
- Codex UI 元数据

下一步适合拿几个真实项目测试，例如教学管理系统、仓库管理系统、聊天机器人或 AI 应用项目，然后根据生成效果继续优化表达模板和证据提取能力。
