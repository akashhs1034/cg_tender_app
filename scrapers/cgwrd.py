"""Public tender/RFP/EOI notices from the Chhattisgarh WRD website.

Most WRD e-tenders are published on CG e-Procurement and are collected there.
This source covers departmental announcements and manual RFP/EOI documents that
appear only on cgwrd.in.
"""
from __future__ import annotations

import os
import re
from datetime import date
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

import core

_PAGES = ("https://cgwrd.in/", "https://cgwrd.in/announcement")
_HEADERS = {"User-Agent": "Mozilla/5.0 AppleWebKit/537.36 Chrome/124 Safari/537.36"}
_MAX_AGE_DAYS = int(os.getenv("CGWRD_MAX_AGE_DAYS", "365"))
_DATE_RE = re.compile(
    r"\b(?:\d{1,2}[-/.]\d{1,2}[-/.]\d{2,4}|"
    r"\d{4}[-/.]\d{1,2}[-/.]\d{1,2})\b"
)
_TENDER_HINTS = (
    "tender", "notice inviting", "invitation for bid", "rfp", "eoi",
    "expression of interest", "quotation", "निविदा", "ई-निविदा", "कोटेशन",
)
_EXCLUDE_HINTS = (
    "pre-qualification certificate", "pre qualification certificate",
    "पूर्व अहर्ता प्रमाण", "appointment order", "नियुक्ति आदेश", "result",
    "परिणाम", "sor ", "schedule of rates",
)
_GENERIC_LINK_TEXT = {"download", "डाउनलोड करें", "view", "click here", ""}


def _candidate_title(anchor) -> tuple[str, str]:
    label = anchor.get_text(" ", strip=True)
    parent = anchor.find_parent(["li", "article", "tr", "div", "p"])
    context = parent.get_text(" ", strip=True) if parent else label
    if label.lower() in _GENERIC_LINK_TEXT or len(label) < 8:
        title = context
    else:
        title = label
    title = re.sub(r"\bUploaded\s+On\s*:\s*.*$", "", title, flags=re.I).strip()
    title = re.sub(r"\s+", " ", title)
    return title[:500], context


def parse(html: str, page_url: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    records: list[dict] = []
    for anchor in soup.find_all("a", href=True):
        title, context = _candidate_title(anchor)
        blob = f"{title} {context}".lower()
        if not any(hint in blob or hint in f"{title} {context}"
                   for hint in _TENDER_HINTS):
            continue
        if any(hint in blob or hint in f"{title} {context}"
               for hint in _EXCLUDE_HINTS):
            continue

        href = urljoin(page_url, anchor["href"].strip())
        if urlparse(href).scheme not in {"http", "https"}:
            continue
        dates = _DATE_RE.findall(context)
        published = core.parse_date(dates[-1]) if dates else None
        if published and (date.today() - published).days > _MAX_AGE_DAYS:
            continue
        if len(title) < 8:
            continue

        records.append(core.tender_record(
            title=title,
            state="Chhattisgarh",
            organization="Water Resources Department, Chhattisgarh",
            department="Water Resources Department",
            category="Water & Irrigation",
            published_date=published.isoformat() if published else None,
            document_url=href,
            source_name="Chhattisgarh Water Resources Department",
            source_portal="cgwrd.in",
            source_type="department_site",
        ))
    return records


def scrape() -> list[dict]:
    records: list[dict] = []
    errors: list[str] = []
    for url in _PAGES:
        try:
            response = requests.get(url, headers=_HEADERS, timeout=30)
            response.raise_for_status()
            records.extend(parse(response.text, response.url))
        except Exception as exc:
            errors.append(f"{url}: {type(exc).__name__}: {exc}")

    merged = core.merge_duplicate_records(records, "tender")
    print(f"   cgwrd: {len(merged)} current departmental tender/RFP/EOI notices")
    if not merged and errors:
        print(f"   cgwrd: fetch failed safely — {'; '.join(errors)[:500]}")
    return merged


if __name__ == "__main__":
    for item in scrape():
        print(item.get("published_date"), item["title"][:100], item["document_url"])
