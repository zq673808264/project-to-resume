#!/usr/bin/env python3
"""Append a factual project development log for later resume generation."""

from __future__ import annotations

import argparse
import datetime as dt
from pathlib import Path


TEMPLATE = """## {date}

### Completed work
- {completed}

### Bugs or blockers
- {blockers}

### AI tool assistance
- {ai_help}

### User decisions
- {decisions}

### Validation or result
- {validation}

### Resume-worthy signal
- {signal}

"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", default=".", help="Project directory.")
    parser.add_argument("--date", default=dt.date.today().isoformat(), help="Entry date.")
    parser.add_argument("--completed", default="TODO: summarize implemented features or changes.")
    parser.add_argument("--blockers", default="TODO: note bugs, blockers, or 'None'.")
    parser.add_argument("--ai-help", default="TODO: note which AI tools helped and how.")
    parser.add_argument("--decisions", default="TODO: note user-owned design, review, debugging, or integration decisions.")
    parser.add_argument("--validation", default="TODO: note tests, manual checks, demos, metrics, or review results.")
    parser.add_argument("--signal", default="TODO: note why this work matters for a resume or interview.")
    parser.add_argument("--out", default="career/project-dev-log.md", help="Log path relative to project.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    project = Path(args.project).resolve()
    if not project.exists() or not project.is_dir():
        raise SystemExit(f"Project directory not found: {project}")

    output = project / args.out
    output.parent.mkdir(parents=True, exist_ok=True)

    entry = TEMPLATE.format(
        date=args.date,
        completed=args.completed,
        blockers=args.blockers,
        ai_help=args.ai_help,
        decisions=args.decisions,
        validation=args.validation,
        signal=args.signal,
    )

    if output.exists() and output.read_text(encoding="utf-8").strip():
        with output.open("a", encoding="utf-8") as handle:
            handle.write("\n" + entry)
    else:
        output.write_text("# Project Development Log\n\n" + entry, encoding="utf-8")

    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
