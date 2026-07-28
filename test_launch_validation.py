from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.validate_launch_docs import validate_launch_docs
from scripts.validate_workflows import validate_workflows


class LaunchDocumentationValidationTests(unittest.TestCase):
    def test_repository_launch_documents_and_links_are_valid(self) -> None:
        root = Path(__file__).resolve().parent
        errors, checked = validate_launch_docs(root)
        self.assertEqual(errors, [])
        self.assertGreater(checked, 0)

    def test_missing_required_document_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch(
                "scripts.validate_launch_docs.REQUIRED_DOCUMENTS",
                ("docs/required.md",),
            ):
                errors, checked = validate_launch_docs(root)
        self.assertEqual(checked, 0)
        self.assertEqual(errors, ["missing required document: docs/required.md"])

    def test_broken_local_link_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            document = root / "docs" / "required.md"
            document.parent.mkdir(parents=True)
            document.write_text("[missing](other.md)\n", encoding="utf-8")
            with patch(
                "scripts.validate_launch_docs.REQUIRED_DOCUMENTS",
                ("docs/required.md",),
            ):
                errors, checked = validate_launch_docs(root)
        self.assertEqual(checked, 1)
        self.assertEqual(
            errors,
            ["docs/required.md: missing link target: other.md"],
        )


class WorkflowValidationTests(unittest.TestCase):
    def test_repository_workflows_parse(self) -> None:
        root = Path(__file__).resolve().parent
        errors, checked = validate_workflows(root)
        self.assertEqual(errors, [])
        self.assertGreater(checked, 0)

    def test_invalid_workflow_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            workflows = root / ".github" / "workflows"
            workflows.mkdir(parents=True)
            (workflows / "invalid.yml").write_text("jobs: [\n", encoding="utf-8")
            errors, checked = validate_workflows(root)
        self.assertEqual(checked, 1)
        self.assertEqual(len(errors), 1)
        self.assertTrue(errors[0].startswith(".github/workflows/invalid.yml:"))


if __name__ == "__main__":
    unittest.main()
