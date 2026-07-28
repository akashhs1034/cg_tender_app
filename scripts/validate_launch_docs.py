"""Validate required launch-readiness files and their local Markdown links."""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from urllib.parse import unquote, urlsplit


REQUIRED_DOCUMENTS = (
    "docs/launch-readiness/README.md",
    "docs/launch-readiness/MILESTONE_STATUS.md",
    "docs/launch-readiness/RISK_REGISTER.md",
    "docs/launch-readiness/DECISION_LOG.md",
    "docs/launch-readiness/VALIDATION_LOG.md",
    "docs/launch-readiness/PRODUCTION_CHECKLIST.md",
    "docs/launch-readiness/milestones/M0_BASELINE.md",
    "docs/launch-readiness/milestones/M0_1_LAUNCH_GATES.md",
    "docs/security/HISTORICAL_CREDENTIAL_RESPONSE.md",
    "docs/security/SECRET_SCANNING.md",
)

MARKDOWN_LINK = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
EXTERNAL_SCHEMES = {"http", "https", "mailto", "tel"}


def _local_target(document: Path, raw_target: str) -> Path | None:
    target = raw_target.strip()
    if target.startswith("<") and ">" in target:
        target = target[1 : target.index(">")]
    else:
        target = target.split(maxsplit=1)[0]

    parsed = urlsplit(target)
    if parsed.scheme.lower() in EXTERNAL_SCHEMES or parsed.netloc:
        return None
    if not parsed.path:
        return None

    return (document.parent / unquote(parsed.path)).resolve()


def validate_launch_docs(root: Path) -> tuple[list[str], int]:
    """Return validation errors and the number of local links checked."""

    root = root.resolve()
    errors: list[str] = []
    documents: list[Path] = []

    for relative in REQUIRED_DOCUMENTS:
        document = root / relative
        if not document.is_file():
            errors.append(f"missing required document: {relative}")
        else:
            documents.append(document)

    checked = 0
    for document in documents:
        text = document.read_text(encoding="utf-8")
        display_path = document.relative_to(root).as_posix()
        for raw_target in MARKDOWN_LINK.findall(text):
            target = _local_target(document, raw_target)
            if target is None:
                continue
            checked += 1
            try:
                target.relative_to(root)
            except ValueError:
                errors.append(
                    f"{display_path}: link leaves repository: {raw_target}"
                )
                continue
            if not target.exists():
                errors.append(
                    f"{display_path}: missing link target: {raw_target}"
                )

    return errors, checked


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Repository root (defaults to the parent of scripts/).",
    )
    args = parser.parse_args()

    errors, checked = validate_launch_docs(args.root)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    print(
        f"Launch documentation validation passed: "
        f"{len(REQUIRED_DOCUMENTS)} required files, {checked} local links."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
