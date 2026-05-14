#!/usr/bin/env python3
"""Collect repository and resume evidence for project-to-resume drafting."""

from __future__ import annotations

import argparse
import datetime as _dt
import os
import re
import subprocess
import sys
import textwrap
from collections import Counter
from pathlib import Path
from typing import Iterable

from lib.resume_text import redact_private_info, redact_secrets, safe_slug, source_resume_text

SKIP_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".idea",
    ".vscode",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "node_modules",
    "dist",
    "build",
    "target",
    "bin",
    "obj",
    ".next",
    ".nuxt",
    "coverage",
    "vendor",
}

SKIP_FILES = {
    ".env",
    ".env.local",
    ".env.production",
    ".env.development",
    "id_rsa",
    "id_dsa",
}

MANIFEST_NAMES = {
    "package.json",
    "pyproject.toml",
    "requirements.txt",
    "poetry.lock",
    "Pipfile",
    "Cargo.toml",
    "go.mod",
    "pom.xml",
    "build.gradle",
    "settings.gradle",
    "composer.json",
    "Gemfile",
    "Web.config",
    "web.config",
    "Dockerfile",
    "docker-compose.yml",
    "docker-compose.yaml",
    ".github/workflows",
}

TEXT_EXTENSIONS = {
    ".md",
    ".txt",
    ".rst",
    ".json",
    ".toml",
    ".yaml",
    ".yml",
    ".xml",
    ".csproj",
    ".sln",
    ".config",
}

SUPPORTING_NOTE_KEYWORDS = {
    "dev-log",
    "development-log",
    "career",
    "retrospective",
    "reflection",
    "journal",
    "chat",
    "conversation",
    "prompt",
    "issue",
    "pr",
    "pull-request",
    "开发日志",
    "复盘",
    "记录",
}

LANGUAGE_BY_EXT = {
    ".md": "Markdown",
    ".py": "Python",
    ".js": "JavaScript",
    ".jsx": "JavaScript/React",
    ".ts": "TypeScript",
    ".tsx": "TypeScript/React",
    ".java": "Java",
    ".cs": "C#",
    ".aspx": "ASP.NET Web Forms",
    ".php": "PHP",
    ".go": "Go",
    ".rs": "Rust",
    ".rb": "Ruby",
    ".cpp": "C++",
    ".cc": "C++",
    ".c": "C",
    ".h": "C/C++",
    ".html": "HTML",
    ".css": "CSS",
    ".scss": "SCSS",
    ".sql": "SQL",
    ".vue": "Vue",
    ".svelte": "Svelte",
    ".dart": "Dart",
}

PROJECT_TYPE_RULES = {
    "frontend-web": {
        "languages": {"HTML", "CSS", "SCSS", "JavaScript/React", "TypeScript/React", "Vue", "Svelte"},
        "keywords": {"vite", "react", "vue", "svelte", "next", "nuxt", "tailwind", "webpack"},
    },
    "backend-api": {
        "languages": {"Python", "Java", "C#", "Go", "PHP", "Ruby", "JavaScript", "TypeScript"},
        "keywords": {"express", "fastapi", "flask", "django", "spring", "asp.net", "api", "controller", "route"},
    },
    "full-stack": {
        "languages": {"HTML", "CSS", "SQL"},
        "keywords": {"frontend", "backend", "database", "server", "client", "api", "web.config", "docker-compose"},
    },
    "ai-application": {
        "languages": {"Python", "TypeScript", "JavaScript"},
        "keywords": {"openai", "anthropic", "deepseek", "qwen", "doubao", "llm", "rag", "embedding", "prompt", "agent"},
    },
    "data-or-ml": {
        "languages": {"Python", "SQL"},
        "keywords": {"pandas", "numpy", "sklearn", "tensorflow", "torch", "matplotlib", "notebook", "model", "dataset"},
    },
    "cli-or-automation": {
        "languages": {"Python", "Go", "Rust", "JavaScript", "TypeScript"},
        "keywords": {"argparse", "click", "typer", "commander", "cli", "automation", "script"},
    },
    "codex-skill-or-plugin": {
        "languages": {"Python", "Markdown"},
        "keywords": {"skill.md", "codex", "openai.yaml", "agents/", "references/", "scripts/"},
    },
}

JD_KEYWORD_GROUPS = {
    "languages": {"python", "java", "javascript", "typescript", "c#", "go", "rust", "sql"},
    "frontend": {"react", "vue", "svelte", "next", "nuxt", "html", "css", "tailwind", "responsive"},
    "backend": {"api", "rest", "graphql", "fastapi", "flask", "django", "spring", "asp.net", "database", "auth"},
    "ai": {"llm", "rag", "agent", "prompt", "embedding", "openai", "deepseek", "qwen", "model", "evaluation"},
    "data": {"pandas", "numpy", "sklearn", "machine learning", "visualization", "etl", "analytics"},
    "engineering": {"docker", "git", "testing", "ci", "cd", "deployment", "logging", "monitoring", "automation"},
    "soft": {"communication", "collaboration", "ownership", "documentation", "problem solving"},
}

def should_skip(path: Path) -> bool:
    if any(part in SKIP_DIRS for part in path.parts):
        return True
    return path.name in SKIP_FILES


def read_text(path: Path, limit: int = 12000) -> str:
    try:
        data = path.read_bytes()
    except OSError:
        return ""
    text = data[:limit].decode("utf-8", errors="replace")
    return redact_secrets(text)


def rel(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def iter_files(root: Path) -> Iterable[Path]:
    for current, dirs, files in os.walk(root):
        current_path = Path(current)
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not should_skip(current_path / d)]
        for file_name in files:
            path = current_path / file_name
            if not should_skip(path):
                yield path


def collect_tree(root: Path, max_entries: int = 160) -> list[str]:
    entries: list[str] = []
    for path in sorted(iter_files(root), key=lambda p: rel(p, root).lower()):
        parts = rel(path, root).split("/")
        if len(parts) <= 4:
            entries.append(rel(path, root))
        if len(entries) >= max_entries:
            entries.append("...")
            break
    return entries


def collect_languages(root: Path) -> Counter[str]:
    counts: Counter[str] = Counter()
    for path in iter_files(root):
        language = LANGUAGE_BY_EXT.get(path.suffix.lower())
        if language:
            counts[language] += 1
    return counts


def detect_project_types(root: Path, languages: Counter[str], manifests: list[tuple[str, str]], docs: list[tuple[str, str]], notes: list[tuple[str, str]]) -> list[str]:
    tree_text = "\n".join(rel(path, root).lower() for path in iter_files(root))
    evidence_text = "\n".join(text.lower() for _, text in [*manifests, *docs, *notes])
    found: list[tuple[str, int]] = []
    language_set = set(languages)
    for project_type, rule in PROJECT_TYPE_RULES.items():
        score = len(language_set & rule["languages"])
        for keyword in rule["keywords"]:
            if keyword in tree_text or keyword in evidence_text:
                score += 2
        if score:
            found.append((project_type, score))
    found.sort(key=lambda item: (-item[1], item[0]))
    return [name for name, _ in found[:4]]


def collect_manifests(root: Path) -> list[tuple[str, str]]:
    results: list[tuple[str, str]] = []
    for path in iter_files(root):
        relative = rel(path, root)
        if path.name in MANIFEST_NAMES or any(relative.startswith(name + "/") for name in MANIFEST_NAMES):
            if path.is_file() and (path.suffix in TEXT_EXTENSIONS or path.name in MANIFEST_NAMES):
                results.append((relative, read_text(path, 8000)))
    return sorted(results)


def collect_docs(root: Path) -> list[tuple[str, str]]:
    doc_names = {"readme", "architecture", "design", "overview", "开发文档", "说明"}
    docs: list[tuple[str, str]] = []
    for path in iter_files(root):
        stem = path.stem.lower()
        if path.suffix.lower() in {".md", ".txt", ".rst"} and (stem in doc_names or "readme" in stem):
            docs.append((rel(path, root), read_text(path, 10000)))
    return sorted(docs)


def collect_supporting_notes(root: Path) -> list[tuple[str, str]]:
    notes: list[tuple[str, str]] = []
    for path in iter_files(root):
        relative = rel(path, root)
        searchable = f"{relative.lower()} {path.stem.lower()}"
        if path.suffix.lower() not in {".md", ".txt"}:
            continue
        if any(keyword in searchable for keyword in SUPPORTING_NOTE_KEYWORDS):
            notes.append((relative, read_text(path, 10000)))
    return sorted(notes)


def run_git(root: Path, args: list[str]) -> str:
    try:
        completed = subprocess.run(
            ["git", *args],
            cwd=root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            timeout=8,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return ""
    return completed.stdout.strip()


def collect_git(root: Path) -> dict[str, str]:
    return {
        "branch": run_git(root, ["branch", "--show-current"]),
        "status": run_git(root, ["status", "--short"]),
        "recent_commits": run_git(root, ["log", "--oneline", "--decorate", "-n", "20"]),
        "changed_files": run_git(root, ["diff", "--name-only", "HEAD"]),
        "tracked_summary": run_git(root, ["ls-files"]),
    }


def extract_resume(path: Path | None) -> tuple[str, str]:
    if not path:
        return "", ""
    if not path.exists():
        return path.as_posix(), "Resume file not found."
    text = source_resume_text(path, max_pdf_pages=6)
    if text:
        return path.as_posix(), redact_private_info(text)
    return path.as_posix(), "Unsupported resume format or text extraction unavailable. Prefer .md, .txt, .docx, or text-extractable .pdf."


def extract_job_description(path: Path | None) -> tuple[str, str]:
    if not path:
        return "", ""
    if not path.exists():
        return path.as_posix(), "Job description file not found."
    if path.suffix.lower() not in {".md", ".txt"}:
        return path.as_posix(), "Unsupported job description format. Prefer .md or .txt."
    return path.as_posix(), read_text(path, 16000)


def analyze_jd_match(jd_text: str, evidence_text: str) -> dict[str, list[str]]:
    if not jd_text:
        return {"matched": [], "jd_only": [], "project_only": []}
    jd_lower = jd_text.lower()
    evidence_lower = evidence_text.lower()
    all_keywords = sorted({keyword for words in JD_KEYWORD_GROUPS.values() for keyword in words}, key=lambda x: (len(x), x))
    jd_keywords = [keyword for keyword in all_keywords if keyword in jd_lower]
    project_keywords = [keyword for keyword in all_keywords if keyword in evidence_lower]
    matched = [keyword for keyword in jd_keywords if keyword in project_keywords]
    jd_only = [keyword for keyword in jd_keywords if keyword not in project_keywords]
    project_only = [keyword for keyword in project_keywords if keyword not in jd_keywords]
    return {"matched": matched[:24], "jd_only": jd_only[:24], "project_only": project_only[:24]}


def auto_resume(project: Path) -> Path | None:
    candidates = []
    for path in project.iterdir():
        if path.is_file() and path.suffix.lower() in {".md", ".txt", ".docx", ".pdf"}:
            name = path.name.lower()
            if "resume" in name or "cv" in name or "简历" in name:
                candidates.append(path)
    return sorted(candidates, key=lambda p: (p.suffix.lower() == ".pdf", p.name.lower()))[0] if candidates else None


def write_section(lines: list[str], title: str, body: str | list[str]) -> None:
    lines.append(f"## {title}")
    if isinstance(body, list):
        if body:
            lines.extend(f"- `{item}`" for item in body)
        else:
            lines.append("None found.")
    else:
        lines.append(body.strip() if body.strip() else "None found.")
    lines.append("")


def render(args: argparse.Namespace) -> str:
    project = Path(args.project).resolve()
    resume_path = Path(args.resume).resolve() if args.resume else auto_resume(project)
    languages = collect_languages(project)
    manifests = collect_manifests(project)
    docs = collect_docs(project)
    notes = collect_supporting_notes(project)
    project_types = detect_project_types(project, languages, manifests, docs, notes)
    git = collect_git(project)
    resume_name, resume_text = extract_resume(resume_path)
    jd_path = Path(args.job_description).resolve() if args.job_description else None
    jd_name, jd_text = extract_job_description(jd_path)
    evidence_for_jd = "\n".join(
        [
            "\n".join(collect_tree(project, max_entries=240)),
            "\n".join(f"{name}: {count}" for name, count in languages.items()),
            "\n".join(text for _, text in [*manifests, *docs, *notes]),
        ]
    )
    jd_match = analyze_jd_match(jd_text, evidence_for_jd)

    lines: list[str] = [
        "# Project Resume Evidence Pack",
        "",
        f"- Generated: {_dt.datetime.now().isoformat(timespec='seconds')}",
        f"- Project: `{project}`",
        f"- Resume: `{resume_name or 'not provided'}`",
        f"- Job description: `{jd_name or 'not provided'}`",
        "",
    ]

    write_section(lines, "Top-Level Project Tree", collect_tree(project))

    language_lines = [f"{name}: {count} files" for name, count in languages.most_common()]
    write_section(lines, "Detected Languages and Framework Signals", language_lines)

    write_section(lines, "Detected Project Type Signals", project_types)

    git_summary = textwrap.dedent(
        f"""
        Branch: {git['branch'] or 'unknown'}

        Recent commits:
        ```text
        {git['recent_commits'] or 'No git history found.'}
        ```

        Working tree status:
        ```text
        {git['status'] or 'Clean or not a git repository.'}
        ```
        """
    )
    write_section(lines, "Git Evidence", git_summary)

    if docs:
        lines.append("## README and Docs Evidence")
        for path, text in docs:
            lines.append(f"### `{path}`")
            lines.append("```text")
            lines.append(text[:6000])
            lines.append("```")
        lines.append("")

    if manifests:
        lines.append("## Manifest and Config Evidence")
        for path, text in manifests[:16]:
            lines.append(f"### `{path}`")
            lines.append("```text")
            lines.append(text[:5000])
            lines.append("```")
        lines.append("")

    if notes:
        lines.append("## Development Logs, Chat Notes, Issues, and PR Evidence")
        for path, text in notes[:18]:
            lines.append(f"### `{path}`")
            lines.append("```text")
            lines.append(text[:6000])
            lines.append("```")
        lines.append("")

    if resume_text:
        lines.append("## Existing Resume Text")
        lines.append("Use this for tone matching and positioning. Do not copy private contact details into drafts unless needed.")
        lines.append("```text")
        lines.append(resume_text[:12000])
        lines.append("```")
        lines.append("")

    if jd_text:
        lines.append("## Target Job Description")
        lines.append("Use this to select relevant keywords and produce role-targeted versions. Do not invent project experience to match the JD.")
        lines.append("```text")
        lines.append(jd_text[:12000])
        lines.append("```")
        lines.append("")

        lines.append("## JD Keyword Match")
        lines.append("Use matched keywords as prioritization hints only. Do not add unsupported experience to satisfy the JD.")
        lines.append(f"- Matched: {', '.join(jd_match['matched']) or 'None found'}")
        lines.append(f"- JD-only gaps: {', '.join(jd_match['jd_only']) or 'None found'}")
        lines.append(f"- Project-only strengths: {', '.join(jd_match['project_only']) or 'None found'}")
        lines.append("")

    lines.append("## Drafting Checklist")
    lines.extend(
        [
            "- Extract project purpose from README, manifests, routes, or directory names.",
            "- Name only technologies that appear in evidence.",
            "- Convert implementation details into 3-5 resume bullets.",
            "- Put unverified metrics, deployment status, and business impact under open questions.",
        ]
    )
    lines.append("")
    return "\n".join(lines)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", default=".", help="Project directory to inspect.")
    parser.add_argument("--resume", help="Optional resume file (.md, .txt, .docx, .pdf).")
    parser.add_argument("--job-description", help="Optional target job description file (.md, .txt).")
    parser.add_argument("--out", default="project_resume_evidence.md", help="Markdown output path.")
    parser.add_argument("--out-dir", help="Optional output root. When provided, writes under <out-dir>/<person-name>/<out filename>.")
    parser.add_argument("--person-name", help="Person name used for output subfolder when --out-dir is provided.")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    project = Path(args.project).resolve()
    if not project.exists() or not project.is_dir():
        print(f"Project directory not found: {project}", file=sys.stderr)
        return 2
    output = Path(args.out)
    if args.out_dir:
        resume_path = Path(args.resume) if args.resume else auto_resume(project)
        person = args.person_name or (resume_path.stem if resume_path else "default")
        output = Path(args.out_dir) / safe_slug(person) / output.name
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render(args), encoding="utf-8")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
