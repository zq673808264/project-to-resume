#!/usr/bin/env python3
"""Export a resume project entry to Markdown and Word.

Supports:
- Writing a Markdown copy of the project entry.
- Appending the entry to an existing .docx resume.
- Creating a new .docx resume from a PDF, text, Markdown, or no source resume.

This script uses only the Python standard library so the skill works in small
local environments without requiring python-docx.
"""

from __future__ import annotations

import argparse
import re
import sys
import tempfile
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

from lib.resume_text import SECTION_TITLES, infer_person_name, read_text, safe_slug, source_resume_text


W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"

ET.register_namespace("w", W_NS)
ET.register_namespace("r", R_NS)


def qn(name: str) -> str:
    prefix, tag = name.split(":", 1)
    namespaces = {"w": W_NS, "r": R_NS}
    return f"{{{namespaces[prefix]}}}{tag}"


def markdown_blocks(markdown: str) -> list[tuple[str, str]]:
    blocks: list[tuple[str, str]] = []
    in_code = False
    for raw_line in markdown.splitlines():
        line = raw_line.rstrip()
        if line.strip().startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("# "):
            blocks.append(("title", stripped[2:].strip()))
        elif stripped.startswith("## "):
            blocks.append(("heading1", stripped[3:].strip()))
        elif stripped.startswith("### "):
            blocks.append(("heading2", stripped[4:].strip()))
        elif stripped.startswith("- "):
            blocks.append(("bullet", stripped[2:].strip()))
        elif re.match(r"^\d+\.\s+", stripped):
            blocks.append(("number", re.sub(r"^\d+\.\s+", "", stripped)))
        else:
            blocks.append(("paragraph", stripped))
    return blocks


def plain_text_blocks(text: str) -> list[tuple[str, str]]:
    blocks: list[tuple[str, str]] = []
    for line in text.splitlines():
        stripped = line.strip()
        compact = stripped.replace(" ", "")
        if not stripped:
            continue
        if compact in SECTION_TITLES or stripped in SECTION_TITLES:
            blocks.append(("heading1", compact))
        elif re.match(r"^\d{4}\.\d{2}\s*[-–—]\s*\d{4}\.\d{2}", compact):
            blocks.append(("heading2", stripped))
        elif re.search(r"[（(][^)）]{1,40}[)）]$", stripped) and len(stripped) <= 80:
            blocks.append(("heading2", stripped))
        else:
            blocks.append(("paragraph", stripped))
    return blocks


def make_text_run(text: str, bold: bool = False, size: int = 21, color: str | None = None) -> ET.Element:
    run = ET.Element(qn("w:r"))
    props = ET.SubElement(run, qn("w:rPr"))
    fonts = ET.SubElement(props, qn("w:rFonts"))
    fonts.set(qn("w:ascii"), "Calibri")
    fonts.set(qn("w:eastAsia"), "Microsoft YaHei")
    fonts.set(qn("w:hAnsi"), "Calibri")
    sz = ET.SubElement(props, qn("w:sz"))
    sz.set(qn("w:val"), str(size))
    sz_cs = ET.SubElement(props, qn("w:szCs"))
    sz_cs.set(qn("w:val"), str(size))
    if bold:
        ET.SubElement(props, qn("w:b"))
    if color:
        color_el = ET.SubElement(props, qn("w:color"))
        color_el.set(qn("w:val"), color)
    t = ET.SubElement(run, qn("w:t"))
    t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    t.text = text
    return run


def paragraph(text: str, style: str = "paragraph") -> ET.Element:
    p = ET.Element(qn("w:p"))
    p_pr = ET.SubElement(p, qn("w:pPr"))

    if style == "title":
        jc = ET.SubElement(p_pr, qn("w:jc"))
        jc.set(qn("w:val"), "center")
        spacing = ET.SubElement(p_pr, qn("w:spacing"))
        spacing.set(qn("w:after"), "160")
        p.append(make_text_run(text, bold=True, size=32, color="1F4E79"))
        return p

    if style in {"heading1", "heading2"}:
        spacing = ET.SubElement(p_pr, qn("w:spacing"))
        spacing.set(qn("w:before"), "180" if style == "heading1" else "120")
        spacing.set(qn("w:after"), "80")
        if style == "heading1":
            border = ET.SubElement(p_pr, qn("w:pBdr"))
            bottom = ET.SubElement(border, qn("w:bottom"))
            bottom.set(qn("w:val"), "single")
            bottom.set(qn("w:sz"), "4")
            bottom.set(qn("w:color"), "D9EAF7")
        p.append(make_text_run(text, bold=True, size=25 if style == "heading1" else 22, color="1F4E79" if style == "heading1" else None))
        return p

    if style == "bullet":
        ind = ET.SubElement(p_pr, qn("w:ind"))
        ind.set(qn("w:left"), "360")
        p.append(make_text_run(f"- {text}", size=21))
        return p

    if style == "number":
        ind = ET.SubElement(p_pr, qn("w:ind"))
        ind.set(qn("w:left"), "360")
        p.append(make_text_run(f"1. {text}", size=21))
        return p

    spacing = ET.SubElement(p_pr, qn("w:spacing"))
    spacing.set(qn("w:after"), "60")
    p.append(make_text_run(text, size=21))
    return p


def build_document_xml(blocks: list[tuple[str, str]]) -> bytes:
    document = ET.Element(qn("w:document"))
    body = ET.SubElement(document, qn("w:body"))
    for style, text in blocks:
        body.append(paragraph(text, style))
    sect_pr = ET.SubElement(body, qn("w:sectPr"))
    pg_sz = ET.SubElement(sect_pr, qn("w:pgSz"))
    pg_sz.set(qn("w:w"), "11906")
    pg_sz.set(qn("w:h"), "16838")
    pg_mar = ET.SubElement(sect_pr, qn("w:pgMar"))
    pg_mar.set(qn("w:top"), "1134")
    pg_mar.set(qn("w:right"), "1134")
    pg_mar.set(qn("w:bottom"), "1134")
    pg_mar.set(qn("w:left"), "1134")
    return ET.tostring(document, encoding="utf-8", xml_declaration=True)


def content_types_xml() -> bytes:
    return b"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>
"""


def root_rels_xml() -> bytes:
    return b"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>
"""


def word_rels_xml() -> bytes:
    return b"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"/>
"""


def create_docx(output: Path, blocks: list[tuple[str, str]]) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", content_types_xml())
        zf.writestr("_rels/.rels", root_rels_xml())
        zf.writestr("word/_rels/document.xml.rels", word_rels_xml())
        zf.writestr("word/document.xml", build_document_xml(blocks))


def append_to_docx(source: Path, output: Path, entry_markdown: str, heading: str) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        with zipfile.ZipFile(source) as zf:
            zf.extractall(temp_path)

        document_path = temp_path / "word" / "document.xml"
        root = ET.fromstring(document_path.read_bytes())
        body = root.find(qn("w:body"))
        if body is None:
            raise ValueError("Invalid DOCX: missing document body")

        sect_pr = body.find(qn("w:sectPr"))
        insert_index = list(body).index(sect_pr) if sect_pr is not None else len(body)
        new_blocks = [("heading1", heading), *markdown_blocks(entry_markdown)]
        for offset, (style, text) in enumerate(new_blocks):
            body.insert(insert_index + offset, paragraph(text, style))

        document_path.write_bytes(ET.tostring(root, encoding="utf-8", xml_declaration=True))

        with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for file_path in temp_path.rglob("*"):
                if file_path.is_file():
                    zf.write(file_path, file_path.relative_to(temp_path).as_posix())


def build_new_resume_blocks(resume_text: str, entry_markdown: str, source_name: str) -> list[tuple[str, str]]:
    blocks: list[tuple[str, str]] = []
    if resume_text:
        blocks.extend(plain_text_blocks(resume_text))
    else:
        blocks.append(("title", "Resume"))
        blocks.append(("paragraph", "Original resume content was not provided. Add personal information, education, experience, and skills here."))

    blocks.append(("heading1", "项目经历"))
    blocks.extend(markdown_blocks(entry_markdown))
    blocks.append(("heading2", "生成说明"))
    blocks.append(("paragraph", f"This resume was generated from source resume: {source_name or 'not provided'}. Review formatting and private information before sending."))
    return blocks


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--entry", required=True, help="Markdown project entry to export.")
    parser.add_argument("--resume", help="Optional original resume: .docx, .pdf, .md, or .txt.")
    parser.add_argument("--out-md", help="Markdown output path. Defaults to <out-dir>/<person>/resume-entry.md.")
    parser.add_argument("--out-docx", help="DOCX output path. Defaults to <out-dir>/<person>/resume-with-project.docx.")
    parser.add_argument("--out-dir", default="career-output", help="Output root used when --out-md or --out-docx is omitted.")
    parser.add_argument("--person-name", help="Person name for the output subfolder. Defaults to the resume filename or detected resume text.")
    parser.add_argument("--project-name", default="project", help="Project name for the output subfolder.")
    parser.add_argument("--append-heading", default="项目经历补充", help="Heading used when appending to an existing DOCX.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    entry_path = Path(args.entry).resolve()
    resume_path = Path(args.resume).resolve() if args.resume else None

    if not entry_path.exists():
        print(f"Entry file not found: {entry_path}", file=sys.stderr)
        return 2

    entry_markdown = read_text(entry_path)
    resume_text = source_resume_text(resume_path) if resume_path and resume_path.exists() and resume_path.suffix.lower() != ".docx" else ""
    person = safe_slug(args.person_name or infer_person_name(resume_path, resume_text))
    person_dir = Path(args.out_dir).resolve() / person / safe_slug(args.project_name)
    out_md = Path(args.out_md).resolve() if args.out_md else person_dir / "resume-entry.md"
    out_docx = Path(args.out_docx).resolve() if args.out_docx else person_dir / "resume-with-project.docx"

    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text(entry_markdown, encoding="utf-8")

    if resume_path and resume_path.exists() and resume_path.suffix.lower() == ".docx":
        append_to_docx(resume_path, out_docx, entry_markdown, args.append_heading)
    else:
        blocks = build_new_resume_blocks(resume_text, entry_markdown, resume_path.name if resume_path else "")
        create_docx(out_docx, blocks)

    print(out_md)
    print(out_docx)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
