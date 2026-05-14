#!/usr/bin/env python3
"""Create template-based career artifact drafts from an evidence pack."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from lib.resume_text import infer_person_name, safe_slug


SECTION_RE = re.compile(r"^## (?P<title>.+)$", re.MULTILINE)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def section(text: str, title: str) -> str:
    matches = list(SECTION_RE.finditer(text))
    for index, match in enumerate(matches):
        if match.group("title").strip() != title:
            continue
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        return text[start:end].strip()
    return ""


def bullet_items(section_text: str) -> list[str]:
    items = []
    for line in section_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("- `") and stripped.endswith("`"):
            items.append(stripped[3:-1])
        elif stripped.startswith("- "):
            items.append(stripped[2:])
    return items


def infer_project_name(evidence: str, project_path: str) -> str:
    if project_path and project_path != "unknown":
        return Path(project_path).name
    heading = re.search(r"#\s+(.+)", evidence)
    return heading.group(1).strip() if heading else "Project Name"


def meta_value(evidence: str, key: str) -> str:
    match = re.search(rf"^- {re.escape(key)}: `(.+?)`$", evidence, re.MULTILINE)
    return match.group(1).strip() if match else "unknown"


def detected_stack(evidence: str) -> list[str]:
    languages = []
    for item in bullet_items(section(evidence, "Detected Languages and Framework Signals")):
        languages.append(item.split(":", 1)[0])
    return languages[:8]


def detected_types(evidence: str) -> list[str]:
    return bullet_items(section(evidence, "Detected Project Type Signals"))[:4]


def jd_keywords(evidence: str) -> list[str]:
    jd = section(evidence, "Target Job Description").lower()
    if not jd:
        return []
    candidates = [
        "python",
        "java",
        "javascript",
        "typescript",
        "react",
        "vue",
        "sql",
        "llm",
        "rag",
        "agent",
        "api",
        "backend",
        "frontend",
        "full-stack",
        "data",
        "machine learning",
        "docker",
        "testing",
        "git",
    ]
    return [word for word in candidates if word in jd][:12]


def jd_match_lines(evidence: str) -> dict[str, str]:
    match_section = section(evidence, "JD Keyword Match")
    result = {"matched": "None found", "gaps": "None found", "strengths": "None found"}
    for line in match_section.splitlines():
        stripped = line.strip()
        if stripped.startswith("- Matched:"):
            result["matched"] = stripped.split(":", 1)[1].strip()
        elif stripped.startswith("- JD-only gaps:"):
            result["gaps"] = stripped.split(":", 1)[1].strip()
        elif stripped.startswith("- Project-only strengths:"):
            result["strengths"] = stripped.split(":", 1)[1].strip()
    return result


def write_file(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.strip() + "\n", encoding="utf-8")


def resume_zh(project_name: str, stack: list[str], project_types: list[str], keywords: list[str], match: dict[str, str]) -> str:
    stack_text = "、".join(stack) if stack else "待确认技术栈"
    type_text = "、".join(project_types) if project_types else "待确认项目类型"
    keyword_text = "、".join(keywords) if keywords else "无 JD 或待提取"
    return f"""
# 中文简历项目经历初稿

> 说明：这是基于证据包生成的保守 first draft，需要 Codex 或人工结合真实项目细节继续润色。

## {project_name} | {stack_text}

角色：开发者 / AI 辅助开发工作流设计者
时间：YYYY.MM - YYYY.MM
项目类型：{type_text}
JD 关键词参考：{keyword_text}
JD 匹配关键词：{match["matched"]}

- 基于 {stack_text} 构建项目核心功能，围绕「待补充项目目标」完成代码实现、调试验证与文档整理。
- 结合 README、配置文件、开发日志与 git 记录沉淀项目证据，支持将真实技术实现转化为简历项目经历。
- 设计项目复盘与多版本输出流程，可生成中文/英文简历、面试问答、作品集介绍和技术博客大纲。
- 使用 AI Coding 工具辅助实现初版代码与方案探索，个人负责需求拆解、代码审查、集成调试和结果验证。

### 技术亮点

- 项目类型识别：{type_text}
- 技术栈证据：{stack_text}
- 输出资产：简历 bullet、STAR 故事、面试 Q&A、LinkedIn/作品集文案、博客大纲。

### 待确认

- 项目真实目标、目标用户、部署状态和可量化结果。
- 是否有测试覆盖率、响应速度、用户数量、准确率或节省时间等可信指标。
- JD 仍需补强但项目证据暂未覆盖的关键词：{match["gaps"]}。
"""


def resume_en(project_name: str, stack: list[str], project_types: list[str], keywords: list[str], match: dict[str, str]) -> str:
    stack_text = ", ".join(stack) if stack else "stack to confirm"
    type_text = ", ".join(project_types) if project_types else "project type to confirm"
    keyword_text = ", ".join(keywords) if keywords else "none or not provided"
    return f"""
# English Resume First Draft

> Note: This is a conservative first draft generated from the evidence pack. Refine it with Codex or manual review before using it.

## {project_name} | {stack_text}

Role: Developer / AI-assisted workflow designer
Time: YYYY.MM - YYYY.MM
Project type: {type_text}
JD keyword reference: {keyword_text}
Matched JD keywords: {match["matched"]}

- Built core project functionality with {stack_text}, covering implementation, debugging, validation, and documentation for the confirmed project goal.
- Created an evidence-based project review workflow that extracts signals from README files, configs, development logs, and git history.
- Designed a multi-output career artifact flow for resume bullets, STAR stories, interview Q&A, portfolio copy, and technical blog outlines.
- Used AI coding tools to accelerate implementation exploration while owning requirement breakdown, code review, integration, debugging, and validation.

### Open Questions

- Confirm project goal, target users, deployment status, and measurable results.
- Confirm any reliable metrics such as test coverage, latency, users, accuracy, or time saved.
- JD gaps not yet supported by project evidence: {match["gaps"]}.
"""


def interview(project_name: str, stack: list[str]) -> str:
    stack_text = ", ".join(stack) if stack else "the confirmed stack"
    return f"""
# Interview Q&A Draft

## {project_name}

1. What did you build?
   - I built a project based on {stack_text}. The final answer should mention the verified project goal and core workflow.

2. What was your personal contribution?
   - I handled requirement breakdown, implementation review, debugging, integration, validation, and final project storytelling.

3. How did AI tools help?
   - AI tools helped accelerate first-pass implementation and exploration. I remained responsible for checking correctness, adapting the code, and validating the result.

4. How did you verify correctness?
   - Mention tests, manual checks, demos, logs, or code review evidence that actually exists.

5. What was the hardest technical decision?
   - Choose a real tradeoff from the evidence pack, such as architecture, data model, API design, prompt design, or reliability.

6. What would you improve next?
   - Mention practical next steps: tests, deployment, error handling, performance, UI polish, documentation, or evaluation.
"""


def portfolio(project_name: str, stack: list[str], project_types: list[str]) -> str:
    stack_text = ", ".join(stack) if stack else "the confirmed stack"
    type_text = ", ".join(project_types) if project_types else "software project"
    return f"""
# Portfolio / LinkedIn Draft

I built **{project_name}**, a {type_text} project using {stack_text}.

The project focuses on turning real implementation evidence into clear career-facing material. It collects signals from code structure, README files, configuration, development logs, and git history, then organizes them into resume entries, interview talking points, and portfolio-ready descriptions.

AI coding tools helped speed up implementation exploration, while the engineering work still required requirement design, code review, debugging, integration, and validation.
"""


def blog_outline(project_name: str) -> str:
    return f"""
# Technical Blog Outline

## {project_name}

1. Background and motivation
2. Problem decomposition
3. Architecture and workflow
4. Evidence collection from project files
5. Template-based career artifact drafting
6. AI-assisted coding workflow
7. Validation and truthfulness guardrails
8. Lessons learned
9. Future improvements
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", required=True, help="Evidence pack generated by collect_project_context.py.")
    parser.add_argument("--out-dir", default="career-artifacts", help="Directory for generated drafts.")
    parser.add_argument("--person-name", help="Person name for output subfolder. Defaults to resume filename in the evidence pack.")
    parser.add_argument("--flat", action="store_true", help="Write directly to --out-dir instead of <out-dir>/<person-name>.")
    parser.add_argument("--mode", choices=["resume", "career-pack"], default="career-pack")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    evidence_path = Path(args.evidence).resolve()
    evidence = read(evidence_path)
    resume_path = meta_value(evidence, "Resume")
    person = safe_slug(args.person_name or infer_person_name(Path(resume_path) if resume_path != "not provided" else None))
    out_dir = Path(args.out_dir).resolve() if args.flat else Path(args.out_dir).resolve() / person

    project_path = meta_value(evidence, "Project")
    project_name = infer_project_name(evidence, project_path)
    stack = detected_stack(evidence)
    project_types = detected_types(evidence)
    keywords = jd_keywords(evidence)
    match = jd_match_lines(evidence)

    write_file(out_dir / "resume-entry.zh.md", resume_zh(project_name, stack, project_types, keywords, match))
    write_file(out_dir / "resume-entry.en.md", resume_en(project_name, stack, project_types, keywords, match))

    if args.mode == "career-pack":
        write_file(out_dir / "interview-qa.md", interview(project_name, stack))
        write_file(out_dir / "portfolio-linkedin.md", portfolio(project_name, stack, project_types))
        write_file(out_dir / "technical-blog-outline.md", blog_outline(project_name))

    print(out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
