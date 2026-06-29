"""
District S3WaaS notice discovery for Chhattisgarh and Uttar Pradesh.

The scanner covers tenders, recruitment, jobs, advertisements and general
notices. Every district/category request is isolated, and discovered results,
admit cards and unrelated notices are classified but not published.

Standalone:  python -m scrapers.district_notices
"""

from __future__ import annotations

import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).parent.parent))
import core            # noqa: E402
import data_engine     # noqa: E402

_UA = {"User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/124.0.0.0 Safari/537.36")}

NOTICE_PATHS = (
    "/notice_category/tenders/",
    "/notice_category/recruitment/",
    "/notice_category/jobs/",
    "/notice_category/advertisement/",
    "/notice_category/notices/",
)

_RESULT_HINTS = (
    "result", "merit list", "selection list", "selected candidates",
    "परिणाम", "चयन सूची", "मेरिट सूची",
)
_ADMIT_HINTS = ("admit card", "hall ticket", "प्रवेश पत्र")
_CORRIGENDUM_HINTS = (
    "corrigendum", "correction", "amendment", "शुद्धिपत्र", "संशोधन",
)
_TENDER_HINTS = (
    "tender", "e-tender", "nit", "notice inviting", "quotation", "rfp", "eoi",
    "auction", "bid", "निविदा", "टेंडर", "कोटेशन", "नीलामी",
)
_JOB_HINTS = (
    "recruitment", "vacancy", "appointment", "walk-in", "application invited",
    "job", "भर्ती", "रिक्ति", "नियुक्ति", "आवेदन आमंत्रित",
)
_DATE_RE = re.compile(
    r"\b(?:\d{1,2}[-/.]\d{1,2}[-/.]\d{2,4}|"
    r"\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)"
    r"[a-z]*\s+\d{2,4})\b", re.I)
_TENDER_NO_RE = re.compile(
    r"\b(?:NIT|Tender|Bid|EOI|RFP)\s*(?:No\.?|Number|#)?\s*[:\-]?\s*"
    r"([A-Z0-9][A-Z0-9/._\-]{2,})", re.I)

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
    # Added to complete UP coverage — verified live S3WaaS tender pages
    # (<slug>.nic.in/notice_category/tenders/). UP Balrampur is .nic.in, distinct
    # from CG Balrampur (.gov.in) above.
    "Ambedkar Nagar": "ambedkarnagar", "Auraiya": "auraiya", "Baghpat": "bagpat",
    "Balrampur": "balrampur", "Hamirpur": "hamirpur",
}

# Districts whose tender page does NOT fit the default slug pattern
# (<slug>.gov.in/en/notice_category/tenders/). Chhattisgarh's two newest
# districts (created 2020 & 2022) are hosted under <slug>.cg.gov.in, and GPM
# additionally omits the /en/ path prefix — so they are listed with their exact
# tenders-page URL and parsed with the same district table parser. Verified live.
_EXTRA_DISTRICT_SITES = [
    ("Gaurela-Pendra-Marwahi", "Chhattisgarh",
     "https://gaurela-pendra-marwahi.cg.gov.in/notice_category/tenders/"),
    ("Manendragarh-Chirmiri-Bharatpur", "Chhattisgarh",
     "https://manendragarh-chirmiri-bharatpur.cg.gov.in/en/notice_category/tenders/"),
]

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


def district_site_catalog() -> list[dict]:
    """Return the complete district source inventory used by the registry."""
    sites = []
    for district, slug in _CG.items():
        sites.append({
            "source_id": f"district-cg-{slug}",
            "source_name": f"{district} District Website",
            "state": "Chhattisgarh", "district": district,
            "base_url": f"https://{slug}.gov.in/en",
        })
    for district, slug in _UP.items():
        sites.append({
            "source_id": f"district-up-{slug}",
            "source_name": f"{district} District Website",
            "state": "Uttar Pradesh", "district": district,
            "base_url": f"https://{slug}.nic.in",
        })
    for district, state, tender_url in _EXTRA_DISTRICT_SITES:
        base_url = tender_url.split("/notice_category/", 1)[0].rstrip("/")
        sites.append({
            "source_id": f"district-cg-{core.make_source_id(district)[:10]}",
            "source_name": f"{district} District Website",
            "state": state, "district": district, "base_url": base_url,
        })
    return sites


def classify_notice(text: str, category_path: str = "") -> str:
    """Classify one discovery without promoting result/admit-card noise."""
    blob = f" {text or ''} {category_path or ''} ".lower()
    if any(h in blob for h in _ADMIT_HINTS):
        return "admit_card"
    if any(h in blob for h in _RESULT_HINTS):
        return "result"
    if any(h in blob for h in _CORRIGENDUM_HINTS):
        return "corrigendum"
    if any(h in blob for h in _JOB_HINTS):
        return "job"
    if any(h in blob for h in _TENDER_HINTS):
        return "tender"
    if "/recruitment/" in category_path or "/jobs/" in category_path:
        return "job"
    if "/tenders/" in category_path:
        return "tender"
    return "irrelevant"


def _notice_rows(html: str) -> list:
    """Find the repeatable content nodes used by common S3WaaS templates."""
    soup = BeautifulSoup(html, "html.parser")
    rows = [tr for table in soup.find_all("table") for tr in table.find_all("tr")
            if tr.find("td")]
    if rows:
        return rows
    selectors = (
        ".notice-item", ".views-row", ".list-view li", ".list-group-item",
        "article",
    )
    found = []
    for selector in selectors:
        found.extend(soup.select(selector))
    return found


def _dates_from(text: str) -> list[str]:
    return list(dict.fromkeys(_DATE_RE.findall(text or "")))


def _parse_notice_page(html: str, source: dict, page_url: str,
                       category_path: str) -> tuple[list[dict], list[dict], list[dict]]:
    tenders: list[dict] = []
    jobs: list[dict] = []
    discovered: list[dict] = []
    seen: set[tuple] = set()

    for node in _notice_rows(html):
        cells = [td.get_text(" ", strip=True) for td in node.find_all("td")]
        links = []
        for anchor in node.find_all("a", href=True):
            href = urljoin(page_url, anchor.get("href", "").strip())
            if href.startswith(("http://", "https://")):
                links.append((anchor.get_text(" ", strip=True), href))
        node_text = " ".join(cells) if cells else node.get_text(" ", strip=True)
        link_title = next((text for text, _ in links if text), "")
        title = (cells[0] if cells and cells[0] else link_title or node_text).strip()
        if not title or len(title) < 4:
            continue
        document_url = next(
            (href for _, href in links
             if href.lower().split("?", 1)[0].endswith(
                 (".pdf", ".jpg", ".jpeg", ".png", ".webp"))),
            links[0][1] if links else page_url,
        )
        identity = (title.lower(), document_url.lower())
        if identity in seen:
            continue
        seen.add(identity)

        kind = classify_notice(node_text, category_path)
        dates = _dates_from(node_text)
        published = dates[0] if dates else None
        deadline = dates[-1] if len(dates) > 1 else None
        discovered.append({
            "title": title[:300], "classification": kind,
            "state": source["state"], "district": source["district"],
            "source_url": page_url, "document_url": document_url,
        })
        if kind in {"result", "admit_card", "irrelevant"}:
            continue

        source_name = source["source_name"]
        if kind in {"tender", "corrigendum"}:
            number_match = _TENDER_NO_RE.search(node_text)
            tenders.append(core.tender_record(
                title=title, state=source["state"], district=source["district"],
                organization=_office_for(node_text, source["district"]),
                department=_office_for(node_text, source["district"]),
                category=None, deadline=deadline, published_date=published,
                document_url=document_url, source_url=page_url,
                source_name=source_name, source_portal="district-collectorate",
                source_type="district_site",
                tender_no=(number_match.group(1) if number_match else None),
                description=(cells[1] if len(cells) > 1 else node_text)[:1000],
                online_or_offline="offline", is_corrigendum=(kind == "corrigendum"),
                language=("Hindi" if re.search(r"[\u0900-\u097f]", node_text)
                          else "English"),
            ))
        else:
            jobs.append(core.job_record(
                title=title, state=source["state"], district=source["district"],
                department=_office_for(node_text, source["district"]),
                deadline=deadline, application_end_date=deadline,
                description=(cells[1] if len(cells) > 1 else node_text)[:1000],
                document_url=document_url, apply_link=document_url,
                source_url=page_url, source_name=source_name,
                source_portal="district-collectorate",
                source_type="district_site", online_or_offline="offline",
                language=("Hindi" if re.search(r"[\u0900-\u097f]", node_text)
                          else "English"),
            ))
    return tenders, jobs, discovered


def _scan_page(source: dict, category_path: str) -> dict:
    url = source["base_url"].rstrip("/") + category_path
    try:
        response = requests.get(url, headers=_UA, timeout=15)
        if response.status_code != 200:
            return {
                "source_id": source["source_id"], "url": url,
                "tenders": [], "jobs": [], "discovered": [],
                "error": f"HTTP {response.status_code}",
            }
        response.encoding = "utf-8"
        tenders, jobs, discovered = _parse_notice_page(
            response.text, source, url, category_path)
        return {
            "source_id": source["source_id"], "url": url,
            "tenders": tenders, "jobs": jobs, "discovered": discovered,
            "error": None,
        }
    except Exception as exc:
        return {
            "source_id": source["source_id"], "url": url,
            "tenders": [], "jobs": [], "discovered": [],
            "error": f"{type(exc).__name__}: {exc}"[:300],
        }


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


def _fetch_url(district: str, state: str, url: str) -> list[dict]:
    """Fetch + parse one district tenders page at an explicit URL. Never raises."""
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


def _fetch_one(district: str, state: str, slug: str) -> list[dict]:
    return _fetch_url(district, state, _url(state, slug))


# ── State authorities / corporations with their own tender tables ─────────────
# Different layout: S.No | Tender No | Title | Uploaded | Submission | Opening [| Cat]
# PDF links are relative -> urljoin against the page URL.
_AUTHORITY_SITES = [
    ("Noida Authority", "Uttar Pradesh", "Gautam Buddha Nagar",
     "https://noidaauthorityonline.in/en/tenders/"),
    ("UP State Road Transport Corp (UPSRTC)", "Uttar Pradesh", None,
     "https://upsrtc.up.gov.in/en/tenders/"),
]


def authority_site_catalog() -> list[dict]:
    return [
        {
            "source_id": f"authority-{core.make_source_id(name)}",
            "source_name": name, "state": state, "district": district,
            "url": url,
        }
        for name, state, district, url in _AUTHORITY_SITES
    ]


def _first_date(s):
    if not s:
        return None
    return re.split(r"[&]", str(s))[0].strip() or None


def _parse_authority(html, name, state, district, page_url) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    out: list[dict] = []
    for table in soup.find_all("table"):
        heads = [th.get_text(strip=True).lower() for th in table.find_all("th")]
        hjoin = " ".join(heads)
        if "title" not in hjoin or "tender" not in hjoin:
            continue

        def idx(key, default):
            return next((i for i, h in enumerate(heads) if key in h), default)
        i_no, i_ti = idx("tender no", 1), idx("title", 2)
        i_up, i_sub, i_op = idx("upload", 3), idx("submission", 4), idx("opening", 5)

        for tr in table.find_all("tr"):
            tds = tr.find_all("td")
            if len(tds) <= i_ti:
                continue
            cells = [td.get_text(" ", strip=True) for td in tds]
            title = cells[i_ti] if i_ti < len(cells) else ""
            if not title:
                continue
            nit = cells[i_no] if i_no < len(cells) else None
            if nit:
                nit = re.split(r"\[", nit)[0].strip()   # drop "[2 MB] Language: .."
            link = None
            for a in tr.find_all("a"):
                href = a.get("href") or ""
                if href.lower().endswith(".pdf") or "tender" in href.lower():
                    link = urljoin(page_url, href)
                    break
            out.append(data_engine.offline_tender_record(
                title=title, organization=name, district=district, state=state,
                nit_no=nit,
                published_date=_first_date(cells[i_up] if i_up < len(cells) else None),
                closing_date=_first_date(cells[i_sub] if i_sub < len(cells) else None),
                opening_date=_first_date(cells[i_op] if i_op < len(cells) else None),
                document_url=link or page_url, description=title, newspaper=None))
        if out:
            break
    return out


def _fetch_authority(item) -> list[dict]:
    name, state, district, url = item
    try:
        r = requests.get(url, headers=_UA, timeout=15)
        if r.status_code != 200:
            return []
        r.encoding = "utf-8"
        recs = _parse_authority(r.text, name, state, district, url)
        for rec in recs:
            rec["source_portal"] = "govt-authority"
        return recs
    except Exception:
        return []


_LAST_COLLECTION: dict = {}


def collect(max_workers: int = 24) -> dict:
    """Scan every common category path and return records plus district health."""
    sources = district_site_catalog()
    tenders: list[dict] = []
    jobs: list[dict] = []
    discovered: list[dict] = []
    failures: list[dict] = []
    report = {
        source["source_id"]: {
            "source_id": source["source_id"],
            "source_name": source["source_name"],
            "state": source["state"], "district": source["district"],
            "count": 0, "tenders": 0, "jobs": 0, "errors": [],
            "status": "no_records",
        }
        for source in sources
    }
    for authority in authority_site_catalog():
        report[authority["source_id"]] = {
            **authority, "count": 0, "tenders": 0, "jobs": 0,
            "errors": [], "status": "no_records",
        }

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_map = {
            executor.submit(_scan_page, source, path): (source, path)
            for source in sources for path in NOTICE_PATHS
        }
        for future in as_completed(future_map):
            source, path = future_map[future]
            try:
                result = future.result()
            except Exception as exc:  # defensive: a district must never stop the run
                result = {
                    "tenders": [], "jobs": [], "discovered": [],
                    "url": source["base_url"].rstrip("/") + path,
                    "error": f"{type(exc).__name__}: {exc}"[:300],
                }
            source_report = report[source["source_id"]]
            if result.get("error"):
                failure = {
                    "source_id": source["source_id"],
                    "source_name": source["source_name"],
                    "state": source["state"], "district": source["district"],
                    "url": result.get("url"), "error": result["error"],
                    "at": core._now_iso(),
                }
                failures.append(failure)
                source_report["errors"].append({
                    "url": result.get("url"), "error": result["error"]})
            tenders.extend(result.get("tenders") or [])
            jobs.extend(result.get("jobs") or [])
            discovered.extend(result.get("discovered") or [])
            source_report["tenders"] += len(result.get("tenders") or [])
            source_report["jobs"] += len(result.get("jobs") or [])

    # State-authority tender tables do not use the district S3WaaS paths.
    with ThreadPoolExecutor(max_workers=len(_AUTHORITY_SITES)) as executor:
        authority_futures = {
            executor.submit(_fetch_authority, authority): authority
            for authority in _AUTHORITY_SITES
        }
        for future in as_completed(authority_futures):
            name, state, district, url = authority_futures[future]
            authority_id = f"authority-{core.make_source_id(name)}"
            try:
                authority_records = future.result() or []
            except Exception as exc:
                authority_records = []
                failure = {
                    "source_id": authority_id,
                    "source_name": name, "state": state, "district": district,
                    "url": url, "error": f"{type(exc).__name__}: {exc}"[:300],
                    "at": core._now_iso(),
                }
                failures.append(failure)
                report[authority_id]["errors"].append({
                    "url": url, "error": failure["error"]})
            tenders.extend(core.canonicalize_tender_record(r)
                           for r in authority_records)
            report[authority_id]["tenders"] += len(authority_records)

    tenders = core.merge_duplicate_records(tenders, "tender")
    jobs = core.merge_duplicate_records(jobs, "job")
    for source_report in report.values():
        source_report["count"] = source_report["tenders"] + source_report["jobs"]
        if source_report["count"]:
            source_report["status"] = "healthy"
        elif source_report["errors"] and len(source_report["errors"]) >= len(NOTICE_PATHS):
            source_report["status"] = "failed"
        elif source_report["errors"]:
            source_report["status"] = "warning"

    payload = {
        "tenders": tenders, "jobs": jobs, "discovered": discovered,
        "report": report, "failures": failures,
        "generated_at": core._now_iso(),
    }
    _LAST_COLLECTION.clear()
    _LAST_COLLECTION.update(payload)
    print(
        f"   district_notices: {len(tenders)} tenders, {len(jobs)} jobs "
        f"from {len(sources)} district sites; {len(failures)} path failures")
    return payload


def scrape() -> list[dict]:
    """Legacy ingest hook: return canonical district tender records."""
    return collect()["tenders"]


def scrape_jobs() -> list[dict]:
    """Legacy ingest hook: return canonical district recruitment records."""
    return collect()["jobs"]


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
