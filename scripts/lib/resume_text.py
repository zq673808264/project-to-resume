from __future__ import annotations

import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


SECTION_TITLES = {
    "教育背景",
    "实习经历",
    "项目经历",
    "技能奖项",
    "技能证书",
    "荣誉奖项",
    "自我评价",
    "工作经历",
    "校园经历",
    "个人信息",
    "求职意向",
    "专业技能",
    "Education",
    "Experience",
    "Projects",
    "Skills",
    "Awards",
    "Summary",
}

LABEL_PREFIXES = (
    "民族",
    "民 族",
    "现居",
    "现 居",
    "联系电话",
    "出生年月",
    "政治面貌",
    "电子邮箱",
    "主修课程",
    "技能证书",
    "荣誉奖项",
    "Email",
    "Phone",
    "Location",
)

SECRET_PATTERNS = [
    re.compile(r"(?i)(api[_-]?key|secret|token|password)\s*[:=]\s*['\"]?[^'\"\s]{8,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----", re.S),
]

PRIVATE_PATTERNS = [
    re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)"),
    re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
    re.compile(r"\b\d{17}[\dXx]\b"),
]


def qn(name: str) -> str:
    prefix, tag = name.split(":", 1)
    namespaces = {"w": W_NS}
    return f"{{{namespaces[prefix]}}}{tag}"


def read_text(path: Path, limit: int | None = None) -> str:
    data = path.read_bytes()
    if limit is not None:
        data = data[:limit]
    return data.decode("utf-8", errors="replace")


def redact_secrets(text: str) -> str:
    redacted = text
    for pattern in SECRET_PATTERNS:
        redacted = pattern.sub("[REDACTED_SECRET]", redacted)
    return redacted


def redact_private_info(text: str) -> str:
    redacted = redact_secrets(text)
    for pattern in PRIVATE_PATTERNS:
        redacted = pattern.sub("[REDACTED_PRIVATE]", redacted)
    return redacted


def extract_pdf_text(path: Path, max_pages: int | None = None) -> str:
    for module_name in ("pypdf", "PyPDF2"):
        try:
            module = __import__(module_name)
            reader_cls = getattr(module, "PdfReader")
            reader = reader_cls(str(path))
            pages = reader.pages if max_pages is None else reader.pages[:max_pages]
            return "\n".join(page.extract_text() or "" for page in pages).strip()
        except Exception:
            continue
    return ""


def extract_docx_text(path: Path) -> str:
    try:
        with zipfile.ZipFile(path) as zf:
            xml = zf.read("word/document.xml")
    except Exception:
        return ""
    root = ET.fromstring(xml)
    paragraphs = []
    for paragraph in root.iter(qn("w:p")):
        runs = [text.text or "" for text in paragraph.iter(qn("w:t"))]
        line = "".join(runs).strip()
        if line:
            paragraphs.append(line)
    return "\n".join(paragraphs)


def normalize_pdf_resume_text(text: str) -> str:
    if not text.strip():
        return text

    section_pattern = "|".join(re.escape(title) for title in sorted(SECTION_TITLES, key=len, reverse=True))
    label_pattern = "|".join(re.escape(label) for label in sorted(LABEL_PREFIXES, key=len, reverse=True))

    text = re.sub(r"\s+", " ", text)
    text = re.sub(rf"({section_pattern})", r"\n\1\n", text)
    text = re.sub(rf"({label_pattern})\s*[:：]", r"\n\1：", text)
    text = re.sub(r"(\d{4}\.\d{2}\s*[-–—]\s*\d{4}\.\d{2})", r"\n\1", text)
    text = re.sub(r"([^\n]{2,60}[（(][^）)]{1,40}[）)])(?=[\u4e00-\u9fff])", r"\1\n", text)

    raw_lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines()]
    raw_lines = [line for line in raw_lines if line]
    logical_lines: list[str] = []
    current = ""

    def is_section(line: str) -> bool:
        return line.replace(" ", "") in SECTION_TITLES or line.strip() in SECTION_TITLES

    def starts_new_item(line: str) -> bool:
        compact = line.replace(" ", "")
        return (
            is_section(line)
            or any(compact.startswith(prefix.replace(" ", "")) for prefix in LABEL_PREFIXES)
            or bool(re.match(r"^\d{4}\.\d{2}\s*[-–—]\s*\d{4}\.\d{2}", compact))
            or bool(re.search(r"[（(][^)）]{1,40}[)）]$", line) and len(line) <= 80)
        )

    def should_join(prev: str, line: str) -> bool:
        if not prev:
            return False
        if re.search(r"[（(][^)）]{1,40}[)）]$", prev) and len(prev) <= 80:
            return False
        if starts_new_item(line):
            return False
        if prev.endswith(("。", "；", ";", "：", ":", "！", "!", "？", "?")):
            return False
        return True

    for line in raw_lines:
        if is_section(line):
            if current:
                logical_lines.append(current)
                current = ""
            logical_lines.append(line.replace(" ", ""))
            continue
        if should_join(current, line):
            current += line
        else:
            if current:
                logical_lines.append(current)
            current = line
    if current:
        logical_lines.append(current)

    cleaned = []
    for line in logical_lines:
        compact = line.replace(" ", "")
        if compact in SECTION_TITLES or line in SECTION_TITLES:
            cleaned.append(compact)
            continue
        line = re.sub(r"\s*([，。；：、,.!?！？])\s*", r"\1", line)
        line = re.sub(r"([A-Za-z])\s+([A-Za-z])", r"\1 \2", line)
        line = re.sub(r"([A-Za-z])\s+(\d)", r"\1 \2", line)
        line = re.sub(r"(\d)\s+([A-Za-z])", r"\1 \2", line)
        line = re.sub(r"([\u4e00-\u9fff])\s+([\u4e00-\u9fff])", r"\1\2", line)
        cleaned.append(line.strip())

    final_text = "\n".join(cleaned)
    final_text = re.sub(r"([\u4e00-\u9fff])\s+([\u4e00-\u9fff])", r"\1\2", final_text)
    final_text = re.sub(rf"({section_pattern})", r"\n\1\n", final_text)
    final_text = re.sub(rf"({label_pattern})：", r"\n\1：", final_text)
    final_text = re.sub(r"(?<=[。；;])\s*([^\n。；;]{2,50}[（(][^）)]{1,40}[）)])\s*", r"\n\1\n", final_text)
    final_text = re.sub(r"\n{3,}", "\n\n", final_text)
    return final_text.strip()


def source_resume_text(path: Path | None, max_pdf_pages: int | None = None) -> str:
    if not path:
        return ""
    suffix = path.suffix.lower()
    if suffix in {".md", ".txt"}:
        return read_text(path)
    if suffix == ".pdf":
        text = extract_pdf_text(path, max_pages=max_pdf_pages)
        return normalize_pdf_resume_text(text) if text else ""
    if suffix == ".docx":
        return extract_docx_text(path)
    return ""


def infer_person_name(resume_path: Path | None, resume_text: str = "", fallback: str = "default") -> str:
    if resume_path and resume_path.stem:
        return resume_path.stem
    for line in resume_text.splitlines():
        stripped = line.strip()
        if 2 <= len(stripped) <= 20 and not any(char in stripped for char in ":：/@\\"):
            return stripped
    return fallback


def safe_slug(value: str) -> str:
    value = value.strip() or "default"
    value = re.sub(r"[^\w\u4e00-\u9fff.-]+", "-", value, flags=re.UNICODE)
    value = value.strip("-_.")
    return value or "default"
