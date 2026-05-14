# project-to-resume

`project-to-resume` is a tool-agnostic workflow for turning real coding projects into truthful career artifacts.

It works as a Codex Skill, and it can also be used with Claude Code, Gemini CLI, Cursor, GitHub Copilot, Aider, or any AI coding assistant that can read files and run local commands.

GitHub: <https://github.com/zq673808264/project-to-resume>

The core idea:

> Transform the real technical substance of a project into recruiting language without inventing metrics, scale, or impact.

## What It Generates

- Chinese resume project entries
- English resume project entries
- Frontend, backend, full-stack, AI engineering, and data-oriented versions
- Campus, internship, and experienced-candidate versions
- STAR interview stories
- Interview Q&A and answer outlines
- LinkedIn or portfolio project copy
- GitHub README positioning suggestions
- Technical blog outlines
- A complete career artifact pack for one project

## Why This Exists

After finishing a coding project, the best details are usually fresh:

- what the project solved
- which modules were implemented
- which technical decisions mattered
- what bugs or tradeoffs appeared
- how AI tools helped
- what the user personally reviewed, debugged, integrated, and validated

Most people wait until they need a resume, then forget the strongest details. This skill encourages continuous project logging and then turns that evidence into polished, truthful career material.

## Files

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
│   └── original resumes live here
├── career-output/
│   └── <person-name>/
│       └── generated resume outputs live here
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

## Installation

### Codex Skill

Clone the repository:

```bash
git clone https://github.com/zq673808264/project-to-resume.git
```

To make Codex discover this skill automatically, place or clone the folder in your Codex skills directory:

```text
~/.codex/skills/project-to-resume
```

On Windows, this is usually:

```text
C:\Users\<you>\.codex\skills\project-to-resume
```

If you are developing the skill locally, you can also reference it by path while testing.

### Other AI Coding Tools

For Claude Code, Gemini CLI, Cursor, GitHub Copilot, Aider, or other tools, use this repository directly and ask the assistant to follow the README workflow. The scripts are plain Python and do not depend on Codex-specific APIs.

Minimal prompt:

```text
Use this repository's README workflow to turn my project into truthful resume artifacts. Do not invent metrics or unsupported claims.
```

## Usage

### 1. Prepare Project Folders

When using this workflow inside another project, first create project-local input/output folders:

```bash
python /path/to/project-to-resume/scripts/prepare_resume_workspace.py --project /path/to/project
```

This creates:

```text
/path/to/project/resume/
/path/to/project/career-output/
```

Ask the user whether they want to add an existing resume or a target JD. If yes, put those files in `/path/to/project/resume/`. If not, continue without them and generate a blank-resume draft.

### 2. Collect Project Evidence

Run the context collector against a project:

```bash
python scripts/collect_project_context.py --project /path/to/project --out project_resume_evidence.md
```

With an existing resume:

```bash
python scripts/collect_project_context.py --project /path/to/project --resume /path/to/resume.pdf --out project_resume_evidence.md
```

With a target job description:

```bash
python scripts/collect_project_context.py --project /path/to/project --job-description /path/to/jd.md --out project_resume_evidence.md
```

For multiple people, write into a person-specific folder:

```bash
python scripts/collect_project_context.py \
  --project /path/to/project \
  --resume resume/alice.pdf \
  --job-description /path/to/jd.md \
  --out-dir career-output \
  --person-name "Alice Zhang" \
  --out evidence.md
```

This writes `career-output/Alice-Zhang/evidence.md`.

The generated evidence pack includes:

- project tree
- detected languages and framework signals
- detected project type signals
- README and documentation excerpts
- manifest and config evidence
- git branch, status, and recent commits
- development logs, chat notes, PR notes, and issue notes
- existing resume text when extractable
- target job description text when provided
- JD keyword match analysis

### 3. Keep a Development Log

During a project, append factual progress notes:

```bash
python scripts/update_dev_log.py --project /path/to/project
```

Or provide details directly:

```bash
python scripts/update_dev_log.py \
  --project /path/to/project \
  --completed "Implemented resume evidence collection from README and manifests." \
  --blockers "PDF extraction depends on available Python PDF libraries." \
  --ai-help "Codex helped draft the first implementation." \
  --decisions "Kept output evidence-based and avoided overwriting the original resume." \
  --validation "Ran the collector on a sample resume and checked the generated Markdown." \
  --signal "Shows ability to build AI-assisted developer tooling with truthfulness guardrails."
```

This creates or updates:

```text
career/project-dev-log.md
```

### 4. Generate Template-Based Drafts

Create a conservative first-pass career artifact package from an evidence pack:

```bash
python scripts/draft_career_artifacts.py \
  --evidence career-output/Alice-Zhang/evidence.md \
  --out-dir career-output \
  --person-name "Alice Zhang" \
  --mode career-pack
```

Generated files:

- `resume-entry.zh.md`
- `resume-entry.en.md`
- `interview-qa.md`
- `portfolio-linkedin.md`
- `technical-blog-outline.md`

These drafts are intentionally conservative first drafts. Use Codex to refine them against the evidence pack and your target role before sending.

### 5. Export Markdown and Word

Export a generated project entry to both Markdown and Word:

```bash
python scripts/export_resume_docx.py \
  --entry career-output/Alice-Zhang/resume-entry.zh.md \
  --resume resume/original-resume.docx \
  --out-dir career-output \
  --person-name "Alice Zhang"
```

Behavior:

- If the source resume is `.docx`, the script appends the project entry to a new copy of the original resume.
- If the source resume is `.pdf`, the script extracts text and generates a new Word resume using the extracted content plus the project entry.
- PDF extraction is reflowed before Word generation to reduce broken lines and rebuild common resume sections.
- If the source resume is `.md` or `.txt`, the script creates a new Word resume from that text plus the project entry.
- The original resume file is never overwritten.
- By default outputs are written under `career-output/<person-name>/`.

## Tests

Run the workflow test suite:

```bash
python tests/test_workflow.py
```

The tests use fictional fixtures under `tests/fixtures/`.

### 6. Ask Codex to Use the Skill

Example prompts:

```text
Use $project-to-resume to turn this completed project into a Chinese resume project entry.
```

```text
Use $project-to-resume to generate a career pack for this AI-assisted coding project, including resume bullets, interview Q&A, LinkedIn copy, and a blog outline.
```

```text
Use $project-to-resume to create frontend, backend, full-stack, and AI engineering versions of this project experience.
```

## Truthfulness Principles

This skill should not exaggerate a project.

It should not invent:

- users
- revenue
- team size
- performance numbers
- accuracy numbers
- production deployment
- business impact
- technologies not present in the project

If a useful claim is not supported by code, docs, logs, commits, or user confirmation, the skill should mark it as a question instead of pretending it is true.

## AI-Assisted Coding Positioning

For AI-assisted projects, the goal is honest framing:

```text
AI tools accelerated implementation and exploration, while the user was responsible for requirements, architecture choices, code review, debugging, integration, and validation.
```

This is especially useful for interview questions like:

- Was this project written by AI?
- What did you personally contribute?
- How did you verify the generated code?
- What was the hardest technical decision?
- What would you improve next?

## Example Output Shape

```md
## Project Name | Tech Stack

Role: Developer / AI-assisted workflow designer
Time: YYYY.MM - YYYY.MM

- Built ...
- Designed ...
- Integrated ...
- Refactored ...

### Technical Highlights

- ...

### Interview Talking Points

- ...

### Open Questions

- Confirm whether there are verified metrics such as deployment link, user count, test coverage, latency, accuracy, or time saved.
```

See also:

- `examples/sample-evidence-pack.md`
- `examples/sample-output.zh.md`

## Current Status

This repository contains the first working version of the skill:

- skill instructions
- writing references
- evidence collection script
- template-based draft generator
- Markdown and Word export script
- continuous development log script
- output templates
- sample evidence and sample output
- Codex UI metadata

The next useful step is to test it on several real projects and refine the generated resume entries based on actual interview and job-application needs.
