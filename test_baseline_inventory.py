from __future__ import annotations

import unittest

from scripts.baseline_inventory import (
    extract_client_tables,
    extract_env_assignment_names,
    extract_env_names,
    extract_sql_tables,
)


class BaselineInventoryTests(unittest.TestCase):
    def test_environment_inventory_returns_names_not_values(self) -> None:
        text = """
        const key = process.env.GEMINI_API_KEY
        token = os.getenv("SUPABASE_SERVICE_KEY", "must-not-appear")
        """
        names = extract_env_names(text)

        self.assertEqual(
            names,
            {
                "GEMINI_API_KEY",
                "SUPABASE_SERVICE_KEY",
            },
        )
        self.assertNotIn("must-not-appear", names)

        assignments = extract_env_assignment_names(
            "NEXT_PUBLIC_SUPABASE_URL=https://example.invalid\n"
        )
        self.assertEqual(assignments, {"NEXT_PUBLIC_SUPABASE_URL"})

    def test_table_inventory_separates_storage_buckets(self) -> None:
        source = """
        client.from('tenders').select('*')
        client.table("saved_jobs").insert({})
        client.storage.from('vault').uploadBinary(path, bytes)
        """
        sql = """
        create table if not exists public.tenders (id bigint primary key);
        CREATE TABLE IF NOT EXISTS saved_jobs (id bigint primary key);
        """

        tables, buckets = extract_client_tables(source)

        self.assertEqual(tables, {"saved_jobs", "tenders"})
        self.assertEqual(buckets, {"vault"})
        self.assertEqual(extract_sql_tables(sql), {"saved_jobs", "tenders"})


if __name__ == "__main__":
    unittest.main()
