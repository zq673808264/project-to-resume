#!/usr/bin/env python3
"""Run the full project-to-resume workflow with one command."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from lib.resume_text import infer_person_name, safe_slug, source_resume_text


RESUME_EXTS = {".docx", ".md", ".txt", ".pdf"}
JD_HINTS = ("jd", "job", "岗位", "职位")
SCRIPT_ROOT = Path(__file__).resolve().parents[1]


def find_resume(resume_dir: Path) -> Path | None:
    candidates = [path for path in resume_dir.iterdir() if path.is_file() and path.suffix.lower() in RESUME_EXTS]
    non_jd = [path for path in candidates if not any(hint in path.stem.lower() for hint in JD_HINTS)]
    candidates = non_jd or candidates
    preferred = {".docx": 0, ".md": 1, ".txt": 2, ".pdf": 3}
    return sorted(candidates, key=lambda path: (preferred.get(path.suffix.lower(), 9), path.name.lower()))[0] if candidates else None


def find_jd(resume_dir: Path) -> Path | None:
    candidates = [
        path
        for path in resume_dir.iterdir()
        if path.is_file()
        and path.suffix.lower() in {".md", ".txt"}
        and any(hint in path.stem.lower() for hint in JD_HINTS)
    ]
    return sorted(candidates, key=lambda path: path.name.lower())[0] if candidates else None


def run(args: list[str], cwd: Path) -> None:
    subprocess.run([sys.executable, *args], cwd=cwd, check=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", default=".", help="Project directory to summarize.")
    parser.add_argument("--workspace-root", default=Path(__file__).resolve().parents[1], type=Path)
    parser.add_argument("--person-name", help="Person name for output folder.")
    parser.add_argument("--project-name", help="Project name for output folder.")
    parser.add_argument("--resume", help="Explicit resume file. Defaults to auto-detecting from workspace resume/.")
    parser.add_argument("--job-description", help="Explicit JD file. Defaults to auto-detecting from workspace resume/.")
    parser.add_argument("--allow-first-draft", action="store_true", help="Allow export even if obvious placeholders remain.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    workspace = args.workspace_root.resolve()
    project = Path(args.project).resolve()
    resume_dir = workspace / "resume"
    output_dir = workspace / "career-output"

    run(["scripts/prepare_resume_workspace.py", "--project", str(project), "--workspace-root", str(workspace)], SCRIPT_ROOT)

    resume = Path(args.resume).resolve() if args.resume else find_resume(resume_dir)
    jd = Path(args.job_description).resolve() if args.job_description else find_jd(resume_dir)
    resume_text = source_resume_text(resume) if resume else ""
    person = safe_slug(args.person_name or infer_person_name(resume, resume_text, "blank-resume"))
    project_name = safe_slug(args.project_name or project.name)
    project_output = output_dir / person / project_name
    evidence = project_output / "evidence.md"

    collect = [
        "scripts/collect_project_context.py",
        "--project",
        str(project),
        "--out-dir",
        str(output_dir),
        "--person-name",
        person,
        "--project-name",
        project_name,
        "--out",
        "evidence.md",
    ]
    if resume:
        collect.extend(["--resume", str(resume)])
    if jd:
        collect.extend(["--job-description", str(jd)])
    run(collect, SCRIPT_ROOT)

    run(
        [
            "scripts/draft_career_artifacts.py",
            "--evidence",
            str(evidence),
            "--out-dir",
            str(output_dir),
            "--person-name",
            person,
            "--project-name",
            project_name,
            "--mode",
            "career-pack",
        ],
        SCRIPT_ROOT,
    )

    export = [
        "scripts/export_resume_docx.py",
        "--entry",
        str(project_output / "resume-entry.zh.md"),
        "--out-dir",
        str(output_dir),
        "--person-name",
        person,
        "--project-name",
        project_name,
    ]
    if resume:
        export.extend(["--resume", str(resume)])
    if args.allow_first_draft:
        export.append("--allow-first-draft")
    run(export, SCRIPT_ROOT)

    print(project_output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
