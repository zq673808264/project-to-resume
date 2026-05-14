from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable


class WorkflowTest(unittest.TestCase):
    def run_script(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [PYTHON, *args],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )

    def test_collect_draft_and_export_by_person_folder(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            evidence_root = temp_path / "evidence"
            draft_root = temp_path / "drafts"
            export_root = temp_path / "exports"

            self.run_script(
                "scripts/collect_project_context.py",
                "--project",
                "tests/fixtures/sample-project",
                "--resume",
                "tests/fixtures/sample-resume.md",
                "--job-description",
                "tests/fixtures/sample-jd.md",
                "--out-dir",
                str(evidence_root),
                "--person-name",
                "Alice Zhang",
                "--out",
                "evidence.md",
            )
            evidence = evidence_root / "Alice-Zhang" / "evidence.md"
            self.assertTrue(evidence.exists())
            evidence_text = evidence.read_text(encoding="utf-8")
            self.assertIn("## JD Keyword Match", evidence_text)
            self.assertIn("python", evidence_text.lower())
            self.assertNotIn("alice@example.com", evidence_text)

            self.run_script(
                "scripts/draft_career_artifacts.py",
                "--evidence",
                str(evidence),
                "--out-dir",
                str(draft_root),
                "--person-name",
                "Alice Zhang",
            )
            draft = draft_root / "Alice-Zhang" / "resume-entry.zh.md"
            self.assertTrue(draft.exists())
            self.assertIn("first draft", draft.read_text(encoding="utf-8").lower())

            self.run_script(
                "scripts/export_resume_docx.py",
                "--entry",
                str(draft),
                "--resume",
                "tests/fixtures/sample-resume.md",
                "--out-dir",
                str(export_root),
                "--person-name",
                "Alice Zhang",
            )
            self.assertTrue((export_root / "Alice-Zhang" / "resume-entry.md").exists())
            docx = export_root / "Alice-Zhang" / "resume-with-project.docx"
            self.assertTrue(docx.exists())
            self.assertGreater(docx.stat().st_size, 1000)


if __name__ == "__main__":
    unittest.main()
