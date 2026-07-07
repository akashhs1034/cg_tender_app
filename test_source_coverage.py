"""Focused regression tests for the CG source-coverage fixes."""
from __future__ import annotations

import json
import os
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import requests

import core
import data_engine
import ingest
from scrapers import (
    cg_dept_sites,
    cg_jobs,
    cgwrd,
    cspdcl,
    generic_ai,
    newspapers,
    pwd_cg,
    res_cg,
)


class SourceCoverageTests(unittest.TestCase):
    def test_res_live_tender_table(self):
        html = """
        <table>
          <tr>
            <th>S.No.</th><th>Division</th><th>Work Name</th>
            <th>Tender No.</th><th>Tender Cost(In Rs)</th>
            <th>Earnest Money Deposit(In Rs)</th>
            <th>Last Date of Purchaising Tender</th>
            <th>Date of Opening Tender</th><th>Tender Download</th>
          </tr>
          <tr>
            <td>1</td><td>KANKER</td><td>Construction of community hall</td>
            <td>17/2026-27</td><td>914000</td><td>6900</td>
            <td>09-Jul-2026</td><td>10-Jul-2026</td>
            <td><a href="/DownloadTender.aspx?id=1">Download</a></td>
          </tr>
        </table>
        """
        rows = res_cg.parse(html)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["district"], "Kanker")
        self.assertEqual(rows[0]["deadline"], "2026-07-09")
        self.assertEqual(rows[0]["tender_no"], "17/2026-27")

    def test_cgwrd_keeps_rfp_and_rejects_non_opportunity(self):
        html = """
        <ul>
          <li>Publication of Request for Proposal (RFP) for watershed mapping
            Uploaded On : 01-07-2026
            <a href="/files/watershed-rfp.pdf">Download</a>
          </li>
          <li>Assistant Engineer appointment order
            <a href="/files/order.pdf">Download</a>
          </li>
        </ul>
        """
        rows = cgwrd.parse(html, "https://cgwrd.in/")
        self.assertEqual(len(rows), 1)
        self.assertIn("Request for Proposal", rows[0]["title"])
        self.assertEqual(rows[0]["published_date"], "2026-07-01")
        self.assertEqual(rows[0]["source_url"], rows[0]["document_url"])

    def test_pwd_does_not_turn_every_pdf_into_a_tender(self):
        html = """
        <ul>
          <li><a href="/Doc/RTIReport.pdf">RTI Report</a></li>
          <li><a href="/CurrentEvents/NIT-12.pdf">
            Notice Inviting Tender for bridge consultancy
          </a></li>
          <li><a href="/CurrentEvents/Road-SOR.pdf">Road SOR 2026</a></li>
        </ul>
        """
        rows = pwd_cg._parse_table(html, "https://pwd.cg.nic.in/")
        self.assertEqual(len(rows), 1)
        self.assertIn("bridge consultancy", rows[0]["title"])

    def test_pwd_rows_without_documents_keep_unique_identity(self):
        html = """
        <table>
          <tr>
            <th>Tender No.</th><th>Work Description</th>
            <th>Last Date</th>
          </tr>
          <tr><td>NIT-1</td><td>Bridge repair at Kanker</td><td>20/07/2026</td></tr>
          <tr><td>NIT-2</td><td>Road renewal at Durg</td><td>21/07/2026</td></tr>
        </table>
        """
        rows = pwd_cg._parse_table(html, "https://pwd.cg.nic.in/tenders")
        merged = core.merge_duplicate_records(rows, "tender")

        self.assertEqual(len(merged), 2)
        self.assertNotEqual(rows[0]["document_url"], rows[1]["document_url"])

    def test_cspdcl_grid_row_parser(self):
        empty = "<td></td>"
        html = f"""
        <table id="MainContent_GVTenderDetails"><tbody>
          <tr>
            <td>1</td><td>SE Raipur</td><td>NIT-42</td>
            <td>Replacement of distribution transformer</td>
            <td>525600</td><td>24/07/2026 02:30PM</td>
            {empty}{empty}{empty}{empty}{empty}
            <td><a href="javascript:__doPostBack(
              'ctl00$MainContent$GVTenderDetails$ctl02$lb/42/A. NIT/NIT.pdf',''
            )">NIT</a></td>
          </tr>
        </tbody></table>
        """
        rows = cspdcl._parse_grid(
            html,
            "https://cspdcl.co.in/cseb/frmViewTenderesNEW.aspx?paramflag=2",
        )
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["deadline"], "2026-07-24")
        self.assertEqual(rows[0]["description"], "Tender Notice No. NIT-42")

    def test_cspdcl_follows_grid_pagination(self):
        def page(number: int, with_next: bool) -> str:
            titles = {
                1: "Supply of high-capacity power transformers",
                2: "Construction of a regional control room",
            }
            pager = (
                """<a href="javascript:__doPostBack('ctl00$MainContent$GVTenderDetails','Page$2')">2</a>"""
                if with_next else ""
            )
            return f"""
            <form>
              <input type="hidden" name="__VIEWSTATE" value="state-{number}">
              <table id="MainContent_GVTenderDetails"><tbody>
                <tr>
                  <td>{number}</td><td>SE Raipur</td><td>NIT-{number}</td>
                  <td>{titles[number]}</td>
                  <td>100000</td><td>{23 + number}/07/2026 02:30PM</td>
                  <td></td><td></td><td></td><td></td><td></td><td></td>
                </tr>
                <tr><td colspan="12">{pager}</td></tr>
              </tbody></table>
            </form>
            """

        responses = [
            SimpleNamespace(text=page(1, True), url="https://cspdcl.test/feed"),
            SimpleNamespace(text=page(2, False), url="https://cspdcl.test/feed"),
        ]
        with (
            mock.patch.object(cspdcl, "_FLAGS", (1,)),
            mock.patch.object(cspdcl, "_request", side_effect=responses) as request,
        ):
            rows = cspdcl.scrape()

        self.assertEqual(request.call_count, 2)
        self.assertEqual(len(rows), 2)
        self.assertEqual(request.call_args_list[1].args[1], "POST")
        self.assertEqual(
            request.call_args_list[1].kwargs["data"]["__EVENTARGUMENT"],
            "Page$2",
        )

    def test_cgpsc_upload_date_is_not_a_deadline(self):
        html = """
        <a href="pdf/SES-2026.pdf">
          STATE_ENGINEERING_SERVICE_EXAM-2026_ADVERTISEMENT (08-05-2026)
        </a>
        <a href="pdf/old.pdf">
          OLD_EXAM-2021_ADVERTISEMENT (08-05-2021)
        </a>
        """
        rows = cg_jobs._parse_advertisements(html)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["published_date"], "2026-05-08")
        self.assertIsNone(rows[0]["deadline"])

    def test_balrampur_wrapper_does_not_duplicate_wrd_or_res(self):
        with mock.patch.object(
            cg_dept_sites,
            "_scrape_site",
            side_effect=lambda site: [{"source_id": site["source_id"]}],
        ) as scrape_site:
            rows = cg_dept_sites.scrape_balrampur()

        self.assertEqual(rows, [{"source_id": "balrampur_cg"}])
        self.assertEqual(scrape_site.call_count, 1)
        self.assertEqual(
            scrape_site.call_args.args[0]["source_id"],
            "balrampur_cg",
        )

    def test_newspaper_registry_enables_full_haribhoomi_coverage(self):
        path = Path(__file__).with_name("newspaper_sources.json")
        sources = json.loads(path.read_text(encoding="utf-8"))
        haribhoomi = next(
            source for source in sources
            if source["source_id"] == "newspaper-haribhoomi-epaper"
        )
        self.assertEqual(haribhoomi["max_assets"], 240)

    def test_newspaper_registry_uses_live_and_honest_sources(self):
        path = Path(__file__).with_name("newspaper_sources.json")
        sources = {
            source["source_id"]: source
            for source in json.loads(path.read_text(encoding="utf-8"))
        }

        rihand = sources["newspaper-rihand-times"]
        self.assertEqual(rihand["state"], "Chhattisgarh")
        self.assertEqual(rihand["epaper_fn"], "rihand")
        self.assertIn("rihandtimes.in", rihand["url"])
        self.assertFalse(sources["newspaper-navbharat-times"]["active"])
        self.assertFalse(sources["newspaper-ghatti-ghatna"]["active"])
        self.assertFalse(sources["newspaper-haribhoomi"]["active"])
        self.assertEqual(
            sources["newspaper-cg-frontline"]["collector"],
            "generic_ai",
        )

    def test_rihand_discovers_public_drive_pdf(self):
        home = """
        <a href="/e-paper/rihand-times/">Rihand Times</a>
        <a href="/e-paper/rihand-times-04-07-2026/">Older issue</a>
        """
        current = """
        <iframe src="https://drive.google.com/file/d/1234567890ABCDEFGHIJK/preview"></iframe>
        """

        def fetch(url, **_kwargs):
            if url == newspapers._RIHAND_HOME:
                return home, "text/html", "ok"
            if url.endswith("/e-paper/rihand-times/"):
                return current, "text/html", "ok"
            return "", "text/html", "ok"

        with mock.patch.object(newspapers, "_fetch", side_effect=fetch):
            assets = newspapers._rihand_epaper_assets()

        self.assertEqual(len(assets), 1)
        self.assertEqual(assets[0][2], "pdf")
        self.assertIn(
            "id=1234567890ABCDEFGHIJK",
            assets[0][0],
        )

    def test_newspaper_retry_coordinator_can_limit_inner_attempts(self):
        response = mock.Mock(status_code=429, headers={})
        response.raise_for_status.side_effect = requests.HTTPError("429")
        with (
            mock.patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}),
            mock.patch.object(data_engine, "_wait_for_vision_slot"),
            mock.patch("requests.post", return_value=response) as post,
        ):
            payload, status = data_engine._gemini_vision_json(
                b"page",
                "image/jpeg",
                max_attempts=1,
            )
        core.clear_ai_error()

        self.assertIsNone(payload)
        self.assertEqual(status, "error:HTTPError")
        self.assertEqual(post.call_count, 1)

    def test_generic_ai_rows_keep_unique_listing_identity(self):
        source = {
            "source_id": "test-ai-source",
            "name": "Test AI source",
            "url": "https://example.gov.in/tenders",
            "state": "Chhattisgarh",
        }
        rows = generic_ai._to_tenders([
            {"title": "Construction of district hospital", "tender_no": "NIT-1"},
            {"title": "Supply of laboratory equipment", "tender_no": "NIT-2"},
        ], source)

        self.assertEqual(
            len(core.merge_duplicate_records(rows, "tender")),
            2,
        )
        self.assertNotEqual(rows[0]["source_url"], rows[1]["source_url"])

    def test_generic_ai_skips_fallback_when_primary_is_healthy(self):
        source = {
            "source_id": "generic-ai-cspdcl",
            "fallback_for": "cspdcl",
            "name": "CSPDCL fallback",
            "url": "https://example.gov.in/tenders",
        }
        with (
            mock.patch.object(generic_ai, "_load_config", return_value=[source]),
            mock.patch.object(generic_ai, "_extract") as extract,
            mock.patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}),
        ):
            result = generic_ai.collect(primary_report={
                "cspdcl": {"count": 10, "status": "healthy"},
            })

        extract.assert_not_called()
        self.assertEqual(
            result["report"]["generic-ai-cspdcl"]["status"],
            "skipped_primary_healthy",
        )

    def test_strict_health_blocks_multi_source_outage(self):
        healthy = {
            source_id: {"count": 1, "status": "healthy"}
            for source_id in ingest._CRITICAL_DAILY_SOURCES
        }
        self.assertEqual(ingest.strict_health_problems(healthy), [])

        for source_id in ("cg_eproc", "cspdcl", "gem", "pwd_cg"):
            healthy[source_id] = {"count": 0, "status": "no_records"}
        problems = ingest.strict_health_problems(healthy)
        self.assertEqual(len(problems), 2)
        self.assertIn("high-volume anchors unavailable", problems[0])


if __name__ == "__main__":
    unittest.main()
