"""
scrapers/district_notices.py — district-collectorate "offline" tender scraper.

The genuinely-offline tenders (physical bid submission, issued by district
offices — Collector, PWD division, Nagar Nigam, Janpad, RES…) are advertised in
local newspapers AND posted on each district's official S3WaaS website at:

    CG :  https://<district>.gov.in/en/notice_category/tenders/
    UP :  https://<district>.nic.in/notice_category/tenders/

These pages are plain HTML (WordPress/S3WaaS), CAPTCHA-free, and carry a clean
table:  Title | Description | Start Date | End Date | File(PDF).  They are NOT
on the central e-procurement portals we already scrape, so this closes the
"offline / district NIT" gap honestly — real data, no fabrication.

Output rows feed the `offline_tenders` table (see data_engine.offline_tender_record).

Standalone:  python -m scrapers.district_notices
"""

from __future__ import annotations

import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).parent.parent))
import core            # noqa: E402
import data_engine     # noqa: E402

_UA = {"User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/124.0.0.0 Safari/537.36")}

# District -> domain slug. Slugs follow the official DISTRICT (not HQ city), which
# is how the S3WaaS sites are named (e.g. Jagdalpur city -> bastar.gov.in).
_CG = {
    "Raipur": "raipur", "Bilaspur": "bilaspur", "Durg": "durg", "Korba": "korba",
    "Raigarh": "raigarh", "Rajnandgaon": "rajnandgaon", "Mahasamund": "mahasamund",
    "Dhamtari": "dhamtari", "Kanker": "kanker", "Dantewada": "dantewada",
    "Balod": "balod", "Bemetara": "bemetara", "Gariaband": "gariaband",
    "Jashpur": "jashpur", "Mungeli": "mungeli", "Narayanpur": "narayanpur",
    "Sukma": "sukma", "Surajpur": "surajpur", "Surguja": "surguja",
    "Balrampur": "balrampur", "Bastar": "bastar", "Kondagaon": "kondagaon",
    "Bijapur": "bijapur", "Kabirdham": "kawardha", "Janjgir-Champa": "janjgirchampa",
    "Koriya": "korea", "Baloda Bazar": "balodabazar", "Sarangarh-Bilaigarh": "sarangarh",
    "Sakti": "sakti", "Khairagarh": "kcg", "Mohla-Manpur": "manpur",
}
_UP = {
    "Lucknow": "lucknow", "Kanpur Nagar": "kanpurnagar", "Kanpur Dehat": "kanpurdehat",
    "Prayagraj": "prayagraj", "Varanasi": "varanasi", "Agra": "agra", "Meerut": "meerut",
    "Gorakhpur": "gorakhpur", "Bareilly": "bareilly", "Aligarh": "aligarh",
    "Moradabad": "moradabad", "Saharanpur": "saharanpur", "Jhansi": "jhansi",
    "Ayodhya": "ayodhya", "Mathura": "mathura", "Banda": "banda", "Gonda": "gonda",
    "Bahraich": "bahraich", "Amroha": "amroha", "Azamgarh": "azamgarh", "Ballia": "ballia",
    "Barabanki": "barabanki", "Basti": "basti", "Bijnor": "bijnor", "Budaun": "budaun",
    "Bulandshahr": "bulandshahar", "Chandauli": "chandauli", "Chitrakoot": "chitrakoot",
    "Deoria": "deoria", "Etah": "etah", "Etawah": "etawah", "Farrukhabad": "farrukhabad",
    "Fatehpur": "fatehpur", "Firozabad": "firozabad", "Gautam Buddha Nagar": "gbnagar",
    "Ghazipur": "ghazipur", "Ghaziabad": "ghaziabad", "Hapur": "hapur", "Hardoi": "hardoi",
    "Hathras": "hathras", "Jalaun": "jalaun", "Jaunpur": "jaunpur", "Amethi": "amethi",
    "Kannauj": "kannauj", "Kasganj": "kasganj", "Kaushambi": "kaushambi",
    "Kushinagar": "kushinagar", "Lakhimpur Kheri": "kheri", "Lalitpur": "lalitpur",
    "Maharajganj": "maharajganj", "Mahoba": "mahoba", "Mainpuri": "mainpuri",
    "Mirzapur": "mirzapur", "Pilibhit": "pilibhit", "Pratapgarh": "pratapgarh",
    "Rae Bareli": "raebareli", "Rampur": "rampur", "Sambhal": "sambhal",
    "Shahjahanpur": "shahjahanpur", "Shamli": "shamli", "Shravasti": "shravasti",
    "Siddharthnagar": "siddharthnagar", "Sitapur": "sitapur", "Sonbhadra": "sonbhadra",
    "Sultanpur": "sultanpur", "Unnao": "unnao", "Mau": "mau", "Bhadohi": "bhadohi",
    "Muzaffarnagar": "muzaffarnagar", "Sant Kabir Nagar": "sknagar",
}

# Issuing-office detection from the tender title (else falls back to collectorate).
_OFFICE_HINTS = [
    ("pwd", "Public Works Department (PWD)"), ("public works", "Public Works Department (PWD)"),
    ("nagar nigam", "Nagar Nigam"), ("nagar palika", "Nagar Palika"),
    ("municipal", "Municipal Corporation"), ("nagar panchayat", "Nagar Panchayat"),
    ("janpad", "Janpad Panchayat"), ("gram panchayat", "Gram Panchayat"),
    ("jal nigam", "Jal Nigam"), ("jal sansadhan", "Water Resources Dept"),
    ("health", "Health Department"), ("cmho", "Chief Medical & Health Office"),
    ("education", "Education Department"), ("forest", "Forest Department"),
    ("irrigation", "Irrigation Department"), ("rural", "Rural Engineering Service"),
    ("res ", "Rural Engineering Service"), ("electric", "Electricity Department"),
]


def _office_for(title: str, district: str) -> str:
    low = (title or "").lower()
    for kw, office in _OFFICE_HINTS:
        if kw in low:
            return f"{office}, {district}"
    return f"District Administration / Collectorate, {district}"


def _url(state: str, slug: str) -> str:
    if state == "Chhattisgarh":
        return f"https://{slug}.gov.in/en/notice_category/tenders/"
    return f"https://{slug}.nic.in/notice_category/tenders/"


def _parse(html: str, district: str, state: str, page_url: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    out: list[dict] = []
    for table in soup.find_all("table"):
        heads = " ".join(th.get_text(strip=True).lower() for th in table.find_all("th"))
        if "title" not in heads:
            continue
        for tr in table.find_all("tr"):
            tds = tr.find_all("td")
            if len(tds) < 4:
                continue
            cells = [td.get_text(" ", strip=True) for td in tds]
            title = cells[0] or (cells[1] if len(cells) > 1 else "")
            if not title:
                continue
            # Columns: Title | Description | Start Date | End Date | File
            start = cells[2] if len(cells) > 2 else None
            end   = cells[3] if len(cells) > 3 else None
            link  = None
            for a in tr.find_all("a"):
                href = a.get("href") or ""
                if href.lower().endswith(".pdf") or "uploads" in href or "s3waas" in href:
                    link = href
                    break
            out.append(data_engine.offline_tender_record(
                title=title,
                organization=_office_for(title, district),
                district=district,
                state=state,
                value_text=None,
                published_date=start,
                closing_date=end,
                document_url=link or page_url,
                description=(cells[1] if len(cells) > 1 else title),
                newspaper=None,
            ))
        if out:
            break
    return out


def _fetch_one(district: str, state: str, slug: str) -> list[dict]:
    url = _url(state, slug)
    try:
        r = requests.get(url, headers=_UA, timeout=15)
        if r.status_code != 200:
            return []
        r.encoding = "utf-8"
        recs = _parse(r.text, district, state, url)
        # mark origin so these are distinguishable from newspaper uploads
        for rec in recs:
            rec["source_portal"] = "district-collectorate"
        return recs
    except Exception:
        return []


def scrape() -> list[dict]:
    """Fetch all CG + UP district collectorate tender pages (parallel)."""
    jobs = ([(d, "Chhattisgarh", s) for d, s in _CG.items()] +
            [(d, "Uttar Pradesh", s) for d, s in _UP.items()])
    records: list[dict] = []
    seen: set[str] = set()
    with ThreadPoolExecutor(max_workers=16) as ex:
        futs = {ex.submit(_fetch_one, d, st, s): d for d, st, s in jobs}
        for fut in as_completed(futs):
            for rec in fut.result():
                if rec["source_id"] not in seen:
                    seen.add(rec["source_id"])
                    records.append(rec)
    print(f"   district_notices: {len(records)} CG/UP district-collectorate "
          f"tenders from {len(jobs)} district sites")
    if not records:
        print("   district_notices: WARNING — 0 records; site template may have changed")
    return records


if __name__ == "__main__":
    import io as _io
    sys.stdout = _io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    t0 = time.time()
    found = scrape()
    print(f"\n{'-'*70}\n  {len(found)} district tenders in {time.time()-t0:.1f}s\n{'-'*70}")
    from collections import Counter
    by_state = Counter(r["state"] for r in found)
    print("  by state:", dict(by_state))
    for r in found[:8]:
        print(f"\n  [{r['state']} · {r['district']}] {r['title'][:70]}")
        print(f"     {r['organization']}  | closes {r['deadline']}  | {r.get('document_url','')[:60]}")
