#!/usr/bin/env python3
"""Prepare per-project folders for project-to-resume inputs and outputs."""

from __future__ import annotations

import argparse
from pathlib import Path


RESUME_README = """# Resume Inputs

Put optional source files here before running project-to-resume:

- Existing resume: `.docx`, `.pdf`, `.md`, or `.txt`
- Target job description: `.md` or `.txt`

If no resume is provided, project-to-resume will generate a new resume draft from a blank resume structure plus the project entry.
If no job description is provided, project-to-resume will generate a general-purpose version.
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", default=".", help="Target project directory.")
    parser.add_argument("--output-dir-name", default="career-output", help="Output folder name inside the target project.")
    parser.add_argument("--resume-dir-name", default="resume", help="Input resume folder name inside the target project.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    project = Path(args.project).resolve()
    if not project.exists() or not project.is_dir():
        raise SystemExit(f"Project directory not found: {project}")

    resume_dir = project / args.resume_dir_name
    output_dir = project / args.output_dir_name
    resume_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    readme = resume_dir / "README.md"
    if not readme.exists():
        readme.write_text(RESUME_README, encoding="utf-8")

    print(resume_dir)
    print(output_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
