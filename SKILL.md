---
name: project-to-resume
description: "Convert completed or in-progress AI coding projects into truthful career artifacts: project retrospectives, resume bullets, bilingual entries, STAR stories, interview Q&A, LinkedIn or portfolio copy, GitHub README positioning, and job-targeted project descriptions. Use when Codex, Claude Code, Cursor, GitHub Copilot, Aider, or another AI coding workflow has produced code, commits, README files, PRs, issues, chat logs, development notes, or user explanations that should be transformed into resume-ready project experience without inventing metrics or impact."
---

# Project to Resume

Use this skill to turn a coding project into career-facing material grounded in repository evidence and user-confirmed facts.

## Core Rule

Do not invent technologies, metrics, business impact, team size, users, revenue, deployment status, or personal responsibility. If evidence is missing, either omit the claim or mark it as a question for the user.

## Workflow

1. Identify the target project directory. Default to the current repository unless the user names another path.
2. Immediately prepare project-local folders:

```bash
python path/to/project-to-resume/scripts/prepare_resume_workspace.py --project <project-dir>
```

This creates `<project-dir>/resume/` for optional user inputs and `<project-dir>/career-output/` for generated files.

3. Ask the user whether they want to provide an existing resume and/or a target job description. Keep the question short:

`Do you want to add an existing resume or target JD? If yes, put the files in <project-dir>/resume/ and tell me when ready. If not, I will generate a blank-resume draft from this project.`

Wait for a clear answer when possible.

4. If the user says yes, inspect `<project-dir>/resume/` and use available files:
   - Existing resume: prefer `.docx`, then `.md`, `.txt`, `.pdf`.
   - Job description: prefer filenames containing `jd`, `job`, `岗位`, or `职位` with `.md` or `.txt`.
   - If files are missing after the user says they are ready, ask once more or continue with the blank-resume path if they prefer.
5. If the user says no or provides no files, continue without `--resume` or `--job-description`. Generate a new resume draft from a blank structure plus the project entry.
6. If the project is still in progress and the user wants continuous recording, append a development log:

```bash
python path/to/project-to-resume/scripts/update_dev_log.py --project <project-dir>
```

7. For completed or review-ready work, run `scripts/collect_project_context.py` to create an evidence pack in the target project's output folder:

```bash
python path/to/project-to-resume/scripts/collect_project_context.py --project <project-dir> --resume <resume-file> --out-dir <project-dir>/career-output --person-name <person> --out evidence.md
```

If there is no resume:

```bash
python path/to/project-to-resume/scripts/collect_project_context.py --project <project-dir> --out-dir <project-dir>/career-output --person-name blank-resume --out evidence.md
```

For a target job description:

```bash
python path/to/project-to-resume/scripts/collect_project_context.py --project <project-dir> --resume <resume-file> --job-description <jd.md> --out-dir <project-dir>/career-output --person-name <person> --out evidence.md
```

8. Generate conservative template-based first drafts before LLM refinement:

```bash
python path/to/project-to-resume/scripts/draft_career_artifacts.py --evidence <project-dir>/career-output/<person>/evidence.md --out-dir <project-dir>/career-output --person-name <person> --mode career-pack
```

Treat generated files as first drafts, not final resume prose. Refine them with the evidence pack before sending.

9. Always export deliverable Markdown and Word files, even when no original resume exists:

```bash
python path/to/project-to-resume/scripts/export_resume_docx.py --entry <project-dir>/career-output/<person>/resume-entry.zh.md --resume <resume-file> --out-dir <project-dir>/career-output --person-name <person>
```

If there is no resume, omit `--resume`; the script creates a new Word resume draft from a blank resume structure plus the project entry. If the source resume is `.docx`, append the project entry to a copy of the original resume. If the source resume is `.pdf`, `.md`, or `.txt`, extract text and generate a new Word resume from the extracted content plus the project entry.

10. Read the evidence pack and the relevant reference:
   - `references/resume_entry_style.md` for resume bullets and project entries.
   - `references/career_artifact_outputs.md` for LinkedIn, portfolio, README, blog, and interview material.
   - `templates/` for reusable output structures.
   - `examples/` for a minimal input/output demonstration.
11. Produce the requested artifact. If unspecified, produce a Chinese resume entry, a short project retrospective, and interview follow-up questions.
12. For resume output, use this order:
   - Project name
   - Role or responsibility line
   - Time period if known, otherwise leave a placeholder
   - Tech stack supported by repository evidence
   - 3-5 resume bullets
   - Technical highlights
   - Interview talking points
   - Open questions for claims that need user confirmation
13. Do not overwrite the user's original resume. For Word output, write a new `.docx` file instead of modifying the source resume in place.

## Output Modes

Choose the mode requested by the user. If unspecified, produce Chinese resume bullets plus a concise evidence summary.

- `retro`: project retrospective covering goal, problem, stack, responsibilities, modules, tradeoffs, difficulty, and verified outcomes.
- `zh-resume`: Chinese resume project entry.
- `en-resume`: English resume project entry.
- `bilingual`: Chinese and English entries.
- `frontend`, `backend`, `fullstack`, `ai-engineer`, `data`: role-targeted versions.
- `campus`, `internship`, `experienced`: career-stage-targeted versions.
- `star`: STAR-form project explanation for interviews.
- `interview`: interviewer questions, answer outlines, AI-coding disclosure answer, and optimization ideas.
- `ats`: keyword-aware version for a named job description.
- `merge-suggestion`: instructions for where the new entry likely fits in the existing resume.
- `career-pack`: resume entry, GitHub/portfolio copy, LinkedIn post, interview story, and technical blog outline.
- `export`: write Markdown and Word files; append to a copied `.docx` resume or generate a new `.docx` from a PDF/text resume.

## Project Type Detection

Use detected project type signals to choose the right angle, but do not treat them as proof by themselves. Supported signals include:

- `frontend-web`
- `backend-api`
- `full-stack`
- `ai-application`
- `data-or-ml`
- `cli-or-automation`
- `codex-skill-or-plugin`

## Evidence Priority

Use stronger evidence before weaker evidence:

1. Source code, manifests, lockfiles, route definitions, database schemas, tests, CI, deployment configs.
2. README, docs, architecture notes, issue templates.
3. Development logs created by this skill, chat summaries, PR descriptions, issues, and user-provided explanations.
4. Git commit history and changed-file patterns.
5. Existing resume wording and user-provided claims.
6. Inferences from project structure. Label these as inferences when they matter.

## JD Matching

When a job description is provided, use `JD Keyword Match` as a prioritization guide:

- Matched keywords can be emphasized if supported by project evidence.
- JD-only gaps should become open questions or improvement suggestions.
- Project-only strengths can be used to differentiate the project.
- Never add a JD keyword to a bullet unless the project evidence supports it.

## Writing Constraints

- Keep bullets concrete: action + technical method + outcome.
- Prefer measurable outcomes only when the repository or user provides numbers.
- For student, portfolio, or demo projects, frame outcomes as capability, implementation completeness, reliability, or engineering quality instead of fake business impact.
- Keep one bullet to one main idea.
- Use the user's existing resume tone when the resume text is extractable.
- Redact private contact details in evidence packs unless the user explicitly needs them in the final resume output.
- Preserve truthful scope: "implemented", "built", "designed", "integrated", "optimized", "refactored", "tested", or "deployed" only when supported.
- Explicitly distinguish the user's engineering decisions from AI tool assistance when the project was AI-assisted.
- If asked "was this written by AI?", prepare an honest answer: name the AI tools used, explain the user's requirements, review, debugging, integration, testing, and design decisions.

## Project Retrospective Questions

Use these questions to extract missing context:

- What was the project goal and who was it for?
- What problem did it solve?
- Which modules did the user personally design, modify, or verify?
- What technical decisions, tradeoffs, or debugging work mattered?
- What did AI tools generate, and what did the user review or change?
- How was correctness verified?
- Are there verified metrics such as users, latency, accuracy, automation time saved, deployment uptime, or test coverage?

## Continuous Logging

When a project is ongoing, create or append `career/project-dev-log.md` in the target repository. Keep entries factual and short:

- Date
- Completed work
- Bugs or blockers
- AI tool assistance
- User decisions
- Validation or result
- Resume-worthy signal

## Useful Follow-Ups

Ask only when needed:

- Which role is this resume targeting?
- Should the entry be conservative, balanced, or more achievement-oriented?
- Are there verified metrics, deployment links, user counts, or performance improvements?
- Should Codex update a specific resume file or only create a separate draft?
