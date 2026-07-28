"""Emit a deterministic, secret-safe inventory of the OPPORTA repository.

The script reads only Git-tracked source/configuration files and prints JSON.
It extracts environment-variable *names*, never their configured values.

Run from the repository root:

    python scripts/baseline_inventory.py
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlsplit


TEXT_SUFFIXES = {
    ".css",
    ".dart",
    ".example",
    ".html",
    ".js",
    ".json",
    ".md",
    ".mjs",
    ".ps1",
    ".py",
    ".sh",
    ".sql",
    ".toml",
    ".ts",
    ".tsx",
    ".yaml",
    ".yml",
}

ENV_PATTERNS = (
    re.compile(
        r"""(?:os\.getenv|_env_(?:int|float|bool|str)|_positive_env_int)"""
        r"""\(\s*["']([A-Z][A-Z0-9_]*)"""
    ),
    re.compile(r"""(?:os\.)?environ\.get\(\s*["']([A-Z][A-Z0-9_]*)"""),
    re.compile(r"""process\.env\.([A-Z][A-Z0-9_]*)"""),
    re.compile(r"""Deno\.env\.get\(\s*["']([A-Z][A-Z0-9_]*)"""),
    re.compile(r"""\b(?:secrets|vars)\.([A-Z][A-Z0-9_]*)"""),
)

CLIENT_TABLE_PATTERN = re.compile(
    r"""\.(?:from|table)\(\s*["']([a-z_][a-z0-9_]*)["']""",
    re.IGNORECASE,
)
STORAGE_BUCKET_PATTERN = re.compile(
    r"""\.storage\.from\(\s*["']([a-z_][a-z0-9_-]*)["']""",
    re.IGNORECASE,
)
SQL_TABLE_PATTERN = re.compile(
    r"""\bcreate\s+table\s+if\s+not\s+exists\s+(?:public\.)?"""
    r"""([a-z_][a-z0-9_]*)""",
    re.IGNORECASE,
)
URL_PATTERN = re.compile(r"""https?://[A-Za-z0-9._-]+""")
HTTP_METHOD_PATTERN = re.compile(
    r"""export\s+(?:async\s+)?function\s+(GET|POST|PUT|PATCH|DELETE|OPTIONS)\b"""
)


def _git(root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return completed.stdout.strip()


def _tracked_files(root: Path) -> list[Path]:
    output = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=root,
        check=True,
        capture_output=True,
    ).stdout
    return [
        root / item.decode("utf-8", errors="replace")
        for item in output.split(b"\0")
        if item
    ]


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def extract_env_names(text: str) -> set[str]:
    """Return environment-variable names found in source/config text."""
    names: set[str] = set()
    for pattern in ENV_PATTERNS:
        names.update(pattern.findall(text))
    return names


def extract_env_assignment_names(text: str) -> set[str]:
    """Return KEY names from an environment-file template."""
    names: set[str] = set()
    for line in text.splitlines():
        match = re.match(r"^\s*([A-Z][A-Z0-9_]*)\s*=", line)
        if match:
            names.add(match.group(1))
    return names


def extract_sql_tables(text: str) -> set[str]:
    """Return tables created by version-controlled SQL text."""
    return {name.lower() for name in SQL_TABLE_PATTERN.findall(text)}


def extract_client_tables(text: str) -> tuple[set[str], set[str]]:
    """Return literal Data API tables and Storage buckets from source text."""
    buckets = {
        name.lower() for name in STORAGE_BUCKET_PATTERN.findall(text)
    }
    tables = {
        name.lower() for name in CLIENT_TABLE_PATTERN.findall(text)
    } - buckets
    return tables, buckets


def _route_from_file(app_root: Path, path: Path) -> str:
    parts = list(path.relative_to(app_root).parts[:-1])
    return "/" + "/".join(parts) if parts else "/"


def _feature_files(relative_files: Iterable[str], token: str) -> list[str]:
    token = token.lower()
    return sorted(path for path in relative_files if token in path.lower())


def collect_inventory(root: Path) -> dict[str, Any]:
    """Collect a deterministic repository inventory without secret values."""
    root = root.resolve()
    tracked = _tracked_files(root)
    tracked_pairs = [
        (path, path.relative_to(root).as_posix())
        for path in tracked
        if path.is_file()
    ]
    relative_files = [relative for _, relative in tracked_pairs]

    text_by_file: dict[str, str] = {}
    for path, relative in tracked_pairs:
        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        if relative.endswith(("package-lock.json", "pnpm-lock.yaml", "pubspec.lock")):
            continue
        text_by_file[relative] = _read_text(path)

    env_names: set[str] = set()
    created_tables: set[str] = set()
    referenced_tables: set[str] = set()
    storage_buckets: set[str] = set()
    external_hosts: set[str] = set()

    for relative, text in text_by_file.items():
        env_names.update(extract_env_names(text))
        if relative.endswith(".env.example"):
            env_names.update(extract_env_assignment_names(text))
        tables, buckets = extract_client_tables(text)
        referenced_tables.update(tables)
        storage_buckets.update(buckets)
        if relative.endswith(".sql"):
            created_tables.update(extract_sql_tables(text))
        for url in URL_PATTERN.findall(text):
            host = urlsplit(url).hostname
            if host and host not in {"localhost", "127.0.0.1"}:
                external_hosts.add(host.lower())

    app_root = root / "frontend" / "app"
    pages = sorted(
        _route_from_file(app_root, path)
        for path in app_root.rglob("page.tsx")
    ) if app_root.is_dir() else []

    http_routes: list[dict[str, Any]] = []
    if app_root.is_dir():
        for path in sorted(app_root.rglob("route.ts")):
            text = _read_text(path)
            http_routes.append(
                {
                    "route": _route_from_file(app_root, path),
                    "methods": sorted(set(HTTP_METHOD_PATTERN.findall(text))),
                    "file": path.relative_to(root).as_posix(),
                }
            )

    python_entry_points = sorted(
        relative
        for relative, text in text_by_file.items()
        if relative.endswith(".py")
        and (
            re.search(r"""if\s+__name__\s*==\s*["']__main__["']""", text)
            or re.search(r"""^def\s+main\s*\(""", text, re.MULTILINE)
        )
    )

    workflows: list[dict[str, str]] = []
    for relative, text in text_by_file.items():
        if not relative.startswith(".github/workflows/"):
            continue
        name_match = re.search(r"^name:\s*(.+?)\s*$", text, re.MULTILINE)
        workflows.append(
            {
                "file": relative,
                "name": name_match.group(1) if name_match else "(unnamed)",
            }
        )

    missing_tables = sorted(referenced_tables - created_tables)
    sql_files = sorted(
        relative for relative in relative_files if relative.endswith(".sql")
    )

    return {
        "git": {
            "branch": _git(root, "branch", "--show-current"),
            "commit": _git(root, "rev-parse", "HEAD"),
        },
        "frontend": {
            "pages": pages,
            "http_routes": http_routes,
            "admin_files": _feature_files(relative_files, "admin"),
            "ai_files": _feature_files(relative_files, "/ai/"),
            "payment_files": _feature_files(relative_files, "payment"),
        },
        "python": {
            "entry_points": python_entry_points,
            "scrapers": sorted(
                relative
                for relative in relative_files
                if relative.startswith("scrapers/") and relative.endswith(".py")
            ),
        },
        "database": {
            "sql_files": sql_files,
            "created_tables": sorted(created_tables),
            "literal_client_tables": sorted(referenced_tables),
            "referenced_but_not_created": missing_tables,
            "storage_buckets": sorted(storage_buckets),
            "has_supabase_config": (root / "supabase" / "config.toml").is_file(),
            "has_migrations_directory": (
                root / "supabase" / "migrations"
            ).is_dir(),
        },
        "operations": {
            "workflows": sorted(workflows, key=lambda item: item["file"]),
            "environment_variable_names": sorted(env_names),
            "external_hosts": sorted(external_hosts),
        },
    }


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    print(json.dumps(collect_inventory(root), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
