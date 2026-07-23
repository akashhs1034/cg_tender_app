"""Focused tests for approved-source storage compatibility."""

from __future__ import annotations

import unittest

from approved_source_scanner import load_approved_sources, sync_findings_to_supabase


class _Response:
    def __init__(self, data):
        self.data = data


class _MissingTableError(Exception):
    code = "PGRST205"


class _Query:
    def __init__(self, table: str, rows: list[dict]):
        self.table = table
        self.rows = rows

    def select(self, *_args, **_kwargs):
        return self

    def eq(self, *_args, **_kwargs):
        return self

    def order(self, *_args, **_kwargs):
        return self

    def range(self, *_args, **_kwargs):
        return self

    def execute(self):
        if self.table == "approved_sources":
            raise _MissingTableError("table not present")
        return _Response(self.rows)


class _Client:
    def __init__(self, rows: list[dict]):
        self.rows = rows
        self.requested_tables: list[str] = []

    def table(self, name: str):
        self.requested_tables.append(name)
        return _Query(name, self.rows)


class _MissingDiscoveredFilesClient:
    def table(self, name: str):
        return _Query("approved_sources", [])


class ApprovedSourceCompatibilityTests(unittest.TestCase):
    def test_missing_approved_table_uses_reviewed_discovery_rows(self):
        client = _Client(
            [
                {
                    "url": "https://example.gov.in/tenders",
                    "title": "Example tenders",
                    "status": "approved",
                    "approved_source_id": "approved-example",
                    "source_type": "department",
                    "requires_captcha": False,
                }
            ]
        )

        sources, backend, error = load_approved_sources(client=client)

        self.assertIsNone(error)
        self.assertEqual(backend, "supabase discovery compatibility")
        self.assertEqual(
            client.requested_tables,
            ["approved_sources", "discovered_sources"],
        )
        self.assertEqual(len(sources), 1)
        self.assertEqual(sources[0]["source_id"], "approved-example")
        self.assertEqual(sources[0]["status"], "active")

    def test_missing_source_id_is_derived_stably(self):
        client = _Client(
            [
                {
                    "url": "https://example.gov.in/jobs",
                    "status": "approved",
                    "requires_captcha": False,
                }
            ]
        )

        first, _, _ = load_approved_sources(client=client)
        second, _, _ = load_approved_sources(client=_Client(client.rows))

        self.assertTrue(first[0]["source_id"].startswith("approved-"))
        self.assertEqual(first[0]["source_id"], second[0]["source_id"])

    def test_missing_discovered_files_table_uses_artifact_fallback(self):
        status, count, detail = sync_findings_to_supabase(
            [], client=_MissingDiscoveredFilesClient()
        )

        self.assertEqual(status, "missing_table")
        self.assertEqual(count, 0)
        self.assertIn("phase4b_discovered_files.sql", detail)


if __name__ == "__main__":
    unittest.main()
