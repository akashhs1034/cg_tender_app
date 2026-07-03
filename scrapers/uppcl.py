"""
scrapers/uppcl.py — UP Power Corporation Limited tender scraper.

Sources tried in order:
  1. https://www.uppclonline.com/uppcl/NIT/Default.aspx  (main e-tendering)
  2. https://uppcl.org/uppcl/NIT/Default.aspx
  3. https://uppcl.org/tender  (alternate)
  4. https://www.uppclonline.com/tender

UPPCL and its subsidiaries (PVVNL, DVVNL, MVVNL, PuVVNL) publish distribution
and transmission tenders: transformers, cable, meters, substation works, and
vehicle/logistics contracts.

DOM structure (ASP.NET WebForms, typical NIC pattern):
  table#ctl00_ContentPlaceHolder1_GridView1 or similar
  Columns: S.No | NIT No | Description | Last Date | EMD | Link

Standalone:  python -m scrapers.uppcl
"""

from __future__ import annotations

import re
import ssl
import sys
import warnings
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.poolmanager import PoolManager
from urllib3.util.ssl_ import create_urllib3_context

sys.path.insert(0, str(Path(__file__).parent.parent))
import core  # noqa: E402


class _LegacyTLSAdapter(HTTPAdapter):
    """Allow handshakes with old ASP.NET/IIS servers that OpenSSL 3 rejects.

    UPPCL's portals negotiate legacy TLS renegotiation and weak cipher
    suites; modern OpenSSL refuses these with
    ``SSLV3_ALERT_HANDSHAKE_FAILURE`` before certificate validation even
    runs (so ``verify=False`` alone does not help). We build a context that
    lowers the security level and re-enables legacy server connect.
    """

    def _ctx(self) -> ssl.SSLContext:
        ctx = create_urllib3_context()
        # SECLEVEL=1 permits the older ciphers/keys these servers offer.
        try:
            ctx.set_ciphers("DEFAULT@SECLEVEL=1")
        except ssl.SSLError:
            pass
        # 0x4 == OP_LEGACY_SERVER_CONNECT (not always exposed as a constant).
        ctx.options |= getattr(ssl, "OP_LEGACY_SERVER_CONNECT", 0x4)
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        return ctx

    def init_poolmanager(self, connections, maxsize, block=False, **kw):
        kw["ssl_context"] = self._ctx()
        self.poolmanager = PoolManager(
            num_pools=connections, maxsize=maxsize, block=block, **kw)

_PORTALS = [
    "https://www.uppclonline.com/uppcl/NIT/Default.aspx",
    "https://uppcl.org/uppcl/NIT/Default.aspx",
    "https://uppcl.org/tender",
    "https://www.uppclonline.com/tender",
    "https://upenergy.in/uppcl/tenders",
    "https://www.uppcl.org/uppcl/NIT/Default.aspx",
]
_BASE_ORG = "UP Power Corporation Limited (UPPCL)"

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept":          "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

_SECTOR_MAP = {
    "Electrical & Energy": [
        "transformer", "cable", "substation", "meter", "distribution", "solar",
        "capacitor", "conductor", "lt ab", "inverter", "electrical", "electric",
        "power", "dtr", "transmission", "crgo", "bess", "battery", "ups",
        "generator", "feeder", "pole", "insulator",
    ],
    "Civil Infrastructure": [
        "road", "building", "construction", "civil", "compound wall", "fencing",
        "repair", "maintenance", "cleaning", "boundary",
    ],
    "Transport": [
        "vehicle", "car", "jeep", "pool vehicle", "hiring", "transport",
    ],
    "IT Services": [
        "software", "it ", "computer", "server", "network", "erp", "portal",
        "application", "amu", "consumer app",
    ],
    "Manpower Supply": [
        "manpower", "security", "guard", "housekeeping", "labour",
    ],
}

_UP_DISTRICTS = [
    "lucknow", "kanpur", "agra", "varanasi", "prayagraj", "meerut", "ghaziabad",
    "noida", "mathura", "aligarh", "bareilly", "moradabad", "saharanpur",
    "gorakhpur", "jhansi", "faizabad", "ayodhya", "muzaffarnagar",
    "rampur", "shahjahanpur", "firozabad", "jaunpur", "mirzapur",
    "bulandshahr", "sambhal", "sultanpur", "azamgarh", "unnao", "lakhimpur",
    "bahraich", "gonda", "basti", "deoria", "kushinagar", "maharajganj",
    "sitapur", "hardoi", "fatehpur", "hamirpur", "mahoba", "banda",
    "chitrakoot", "lalitpur", "jalaun", "etawah", "mainpuri", "etah",
    "firozabad", "hathras", "kasganj", "sambhal", "amroha",
]


def _infer_category(text: str) -> str:
    t = text.lower()
    for cat, kws in _SECTOR_MAP.items():
        if any(k in t for k in kws):
            return cat
    return "Electrical & Energy"  # default: power company


def _infer_district(text: str) -> str | None:
    t = text.lower()
    for d in _UP_DISTRICTS:
        if re.search(r"\b" + re.escape(d) + r"\b", t):
            return d.title()
    return None


def _legacy_session() -> requests.Session:
    s = requests.Session()
    s.mount("https://", _LegacyTLSAdapter())
    return s


def _fetch(url: str) -> str | None:
    try:
        r = requests.get(url, headers=_HEADERS, timeout=25, verify=True)
        r.raise_for_status()
        if len(r.text) < 500:
            return None
        return r.text
    except requests.exceptions.SSLError:
        # Legacy-TLS retry: many UPPCL/DISCOM servers need SECLEVEL=1 +
        # legacy renegotiation, which a plain verify=False does not enable.
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            try:
                r = _legacy_session().get(
                    url, headers=_HEADERS, timeout=25, verify=False)
                r.raise_for_status()
                if len(r.text) < 500:
                    return None
                return r.text
            except Exception as e:
                print(f"   uppcl: SSL fetch failed {url} — {e}")
                return None
    except Exception as e:
        print(f"   uppcl: fetch failed {url} — {e}")
        return None


def _find_table(soup: BeautifulSoup):
    # ASP.NET GridView by partial ID
    for table in soup.find_all("table"):
        tid = table.get("id", "")
        if any(x in tid for x in ("Grid", "GridView", "Tender", "NIT")):
            return table

    # Table with tender-related headers
    for table in soup.find_all("table"):
        header_text = " ".join(th.get_text(strip=True).lower() for th in table.find_all("th"))
        if any(kw in header_text for kw in ("tender", "nit", "description", "work")):
            return table

    return None


def _doc_link(cell, base: str) -> str | None:
    for a in cell.find_all("a", href=True):
        href = a["href"]
        if href.lower().endswith((".pdf", ".doc", ".docx", ".zip", ".xls")):
            return urljoin(base, href)
        text = a.get_text(strip=True).lower()
        if any(kw in text or kw in href.lower() for kw in ("download", "nit", "tender", "pdf", "view")):
            return urljoin(base, href)
    return None


def _parse_page(html: str, source_url: str) -> list[dict]:
    soup  = BeautifulSoup(html, "html.parser")
    table = _find_table(soup)

    if not table:
        return []

    headers = [th.get_text(strip=True).lower() for th in table.find_all("th")]
    col: dict[str, int] = {}
    for i, h in enumerate(headers):
        if re.search(r"\bs\.?no\.?\b|sr\.?\b|#$", h):
            col.setdefault("sr", i)
        elif re.search(r"nit\s*no|tender\s*no|ref", h):
            col.setdefault("ref", i)
        elif re.search(r"description|title|name|work|scope", h):
            col.setdefault("title", i)
        elif re.search(r"value|amount|estimated|cost", h):
            col.setdefault("value", i)
        elif re.search(r"last\s*date|closing|deadline|submission|validity", h):
            col.setdefault("deadline", i)
        elif re.search(r"emd|earnest", h):
            col.setdefault("emd", i)
        elif re.search(r"download|document|pdf|link|view", h):
            col.setdefault("doc", i)
        elif re.search(r"division|discom|unit|circle|zone|office", h):
            col.setdefault("division", i)

    if not col:
        col = {"sr": 0, "ref": 1, "title": 2, "deadline": 3, "emd": 4, "doc": 5}

    records: list[dict] = []
    tbody = table.find("tbody") or table
    for row in tbody.find_all("tr"):
        cells = row.find_all("td")
        if len(cells) < 2:
            continue

        def _c(key: str) -> str:
            idx = col.get(key)
            return cells[idx].get_text(" ", strip=True) if idx is not None and idx < len(cells) else ""

        title    = _c("title") or _c("ref")
        deadline = _c("deadline")
        value    = _c("value")
        emd      = _c("emd")
        ref      = _c("ref")
        division = _c("division")

        if not title or len(title.strip()) < 5:
            continue
        if not any(c.isalpha() for c in title):
            continue  # pure numbers = not a title

        doc_idx = col.get("doc")
        doc_url = _doc_link(cells[doc_idx], source_url) if doc_idx is not None and doc_idx < len(cells) else None
        if not doc_url:
            for cell in cells:
                doc_url = _doc_link(cell, source_url)
                if doc_url:
                    break
        if not doc_url:
            doc_url = source_url

        combined = f"{title} {division}"
        org = f"UPPCL — {division}" if division else _BASE_ORG

        records.append(core.tender_record(
            title=title.strip(),
            state="Uttar Pradesh",
            organization=org,
            category=_infer_category(combined),
            district=_infer_district(combined),
            value_text=value or None,
            emd=emd or None,
            deadline=deadline or None,
            description=f"NIT No: {ref}" if ref else None,
            document_url=doc_url,
            source_portal=source_url,
        ))

    return records


def scrape() -> list[dict]:
    for url in _PORTALS:
        html = _fetch(url)
        if not html:
            continue
        records = _parse_page(html, url)
        if records:
            print(f"   uppcl: {len(records)} core.tender_record() objects ready (source: {url})")
            return records

    print("   uppcl: WARNING — 0 records returned; portal may be down or restructured")
    return []


if __name__ == "__main__":
    import io as _io
    sys.stdout = _io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

    found = scrape()
    print(f"\n{'-'*70}")
    print(f"  {len(found)} total records — UPPCL")
    print(f"{'-'*70}")
    for r in found[:5]:
        print()
        for k, v in r.items():
            if v not in (None, ""):
                print(f"  {k:<14}: {v}")
    print()
