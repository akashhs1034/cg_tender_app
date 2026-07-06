"""Official Chhattisgarh Rural Engineering Services manual-tender scraper.

The RES "Live Tender" selector separates manual tenders from e-tenders. The
e-tenders are already covered by ``cg_eproc``; this module collects the manual
table that was previously missing from OPPORTA.
"""
from __future__ import annotations

import re
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

import core

_URL = "https://res.cg.gov.in/Tender_test_report.aspx"
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"
    )
}


def _normalise_header(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def _column(headers: list[str], *needles: str) -> int | None:
    for index, header in enumerate(headers):
        if all(needle in header for needle in needles):
            return index
    return None


def _document_url(cell, page_url: str) -> str | None:
    if cell is None:
        return None
    links = cell.find_all("a", href=True)
    preferred = next(
        (
            anchor for anchor in links
            if any(word in anchor.get_text(" ", strip=True).lower()
                   for word in ("tender", "nit", "download"))
        ),
        links[0] if links else None,
    )
    return urljoin(page_url, preferred["href"]) if preferred else None


def parse(html: str, page_url: str = _URL) -> list[dict]:
    """Parse the public RES live-manual-tender table."""
    soup = BeautifulSoup(html, "html.parser")
    table = next(
        (
            candidate for candidate in soup.find_all("table")
            if "work name" in _normalise_header(
                " ".join(cell.get_text(" ", strip=True)
                         for cell in (
                             candidate.find("tr").find_all(["th", "td"])
                             if candidate.find("tr") else []
                         )))
            and "division" in _normalise_header(
                " ".join(cell.get_text(" ", strip=True)
                         for cell in (
                             candidate.find("tr").find_all(["th", "td"])
                             if candidate.find("tr") else []
                         )))
        ),
        None,
    )
    if table is None:
        return []

    header_row = table.find("tr")
    if header_row is None:
        return []
    headers = [
        _normalise_header(cell.get_text(" ", strip=True))
        for cell in header_row.find_all(["th", "td"])
    ]

    indexes = {
        "division": _column(headers, "division"),
        "title": _column(headers, "work", "name"),
        "tender_no": _column(headers, "tender", "no"),
        "value": _column(headers, "tender", "cost"),
        "emd": _column(headers, "money", "deposit"),
        "deadline": _column(headers, "last", "date"),
        "opening": _column(headers, "date", "opening"),
    }
    records: list[dict] = []

    for row in table.find_all("tr"):
        if row is header_row:
            continue
        cells = row.find_all("td", recursive=False)
        if not cells:
            continue

        def text(name: str) -> str:
            index = indexes.get(name)
            if index is None or index >= len(cells):
                return ""
            return cells[index].get_text(" ", strip=True)

        title = re.sub(r"^\(\d+\)\s*", "", text("title")).strip()
        if len(title) < 5:
            continue
        division_raw = text("division")
        division = re.sub(r"\s*\(\d+\)\s*$", "", division_raw).strip()
        tender_no = text("tender_no")
        document = None
        for cell in cells:
            candidate = _document_url(cell, page_url)
            if candidate:
                document = candidate
                if "download" in candidate.lower() or "tender" in candidate.lower():
                    break

        fallback_id = tender_no or core.make_source_id(
            division, title, text("deadline"))
        records.append(core.tender_record(
            title=title,
            state="Chhattisgarh",
            organization=(
                f"Rural Engineering Services, {division}"
                if division else "Rural Engineering Services, Chhattisgarh"
            ),
            department="Rural Engineering Services",
            category="Civil Infrastructure",
            district=division.title() if division else None,
            tender_no=tender_no or None,
            value_text=text("value") or None,
            emd=text("emd") or None,
            deadline=text("deadline") or None,
            opening_date=text("opening") or None,
            description=f"Official RES manual tender{f' {tender_no}' if tender_no else ''}",
            document_url=(
                document or f"{page_url}?opporta_tender={fallback_id}"
            ),
            source_name="Chhattisgarh Rural Engineering Services",
            source_portal="res.cg.gov.in",
            source_type="department_site",
        ))

    return core.merge_duplicate_records(records, "tender")


def scrape() -> list[dict]:
    try:
        response = requests.get(_URL, headers=_HEADERS, timeout=30)
        response.raise_for_status()
        response.encoding = "utf-8"
        records = parse(response.text, response.url)
    except Exception as exc:
        print(f"   res_cg: fetch failed safely — {type(exc).__name__}: {exc}")
        return []

    print(f"   res_cg: {len(records)} live manual tenders")
    if not records:
        print("   res_cg: WARNING — live tender table returned 0 records")
    return records


if __name__ == "__main__":
    for item in scrape():
        print(item["deadline"], item["district"], item["title"][:100])
