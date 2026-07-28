"""Parse every GitHub Actions workflow with a safe YAML loader."""

from __future__ import annotations

import argparse
from pathlib import Path

import yaml


def validate_workflows(root: Path) -> tuple[list[str], int]:
    root = root.resolve()
    workflow_dir = root / ".github" / "workflows"
    files = sorted((*workflow_dir.glob("*.yml"), *workflow_dir.glob("*.yaml")))
    errors: list[str] = []

    if not files:
        return ["no GitHub Actions workflows found"], 0

    for workflow in files:
        display_path = workflow.relative_to(root).as_posix()
        try:
            parsed = yaml.safe_load(workflow.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            errors.append(f"{display_path}: {exc}")
            continue
        if not isinstance(parsed, dict):
            errors.append(f"{display_path}: top level is not a mapping")

    return errors, len(files)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Repository root (defaults to the parent of scripts/).",
    )
    args = parser.parse_args()

    errors, checked = validate_workflows(args.root)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    print(f"Workflow YAML validation passed: {checked} files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
