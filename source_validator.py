"""Conservative scoring and classification for OPPORTA source discovery.

This module never fetches URLs.  It evaluates public-link metadata collected by
``source_discovery.py`` and returns review-queue records only.
"""

from __future__ import annotations

import ipaddress
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


ROOT = Path(__file__).resolve().parent
QUERY_FILE = ROOT / "discovery_queries.json"

DOCUMENT_EXTENSIONS = {".pdf", ".doc", ".docx", ".xls", ".xlsx"}
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tif", ".tiff"}
SOCIAL_DOMAINS = {
    "facebook.com",
    "instagram.com",
    "linkedin.com",
    "t.me",
    "telegram.me",
    "twitter.com",
    "wa.me",
    "whatsapp.com",
    "x.com",
    "youtube.com",
}

CAPTCHA_MARKERS = (
    "captcha",
    "recaptcha",
    "hcaptcha",
    "verify you are human",
    "security code",
    "कैप्चा",
)
LOGIN_MARKERS = (
    "authentication required",
    "login required",
    "log in to continue",
    "sign in to continue",
    "password",
)
PAYWALL_MARKERS = (
    "paywall",
    "premium content",
    "subscribe to continue",
    "subscription required",
)
ARCHIVE_MARKERS = ("archive", "archived", "old notice", "पुरालेख")
RECENT_DATE_PATTERN = re.compile(r"\b(?:202[4-9]|20[3-9]\d)\b")


def load_discovery_queries(path: Path = QUERY_FILE) -> dict[str, list[str]]:
    """Load discovery terms, returning empty groups when the file is absent."""
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return {
        str(key): [str(value).strip() for value in values if str(value).strip()]
        for key, values in raw.items()
        if isinstance(values, list)
    }


def normalize_url(url: str) -> str:
    """Return a stable HTTP(S) URL while retaining meaningful query strings."""
    try:
        parts = urlsplit(str(url).strip())
    except ValueError:
        return ""
    if parts.scheme.lower() not in {"http", "https"} or not parts.hostname:
        return ""
    if parts.username or parts.password:
        return ""
    host = parts.hostname.lower().rstrip(".")
    try:
        port = parts.port
    except ValueError:
        return ""
    netloc = host
    if port and not (
        (parts.scheme.lower() == "http" and port == 80)
        or (parts.scheme.lower() == "https" and port == 443)
    ):
        netloc = f"{host}:{port}"
    path = re.sub(r"/{2,}", "/", parts.path or "/")
    query = urlencode(parse_qsl(parts.query, keep_blank_values=True), doseq=True)
    return urlunsplit((parts.scheme.lower(), netloc, path, query, ""))


def is_private_or_local_url(url: str) -> bool:
    """Reject loopback, private-network, link-local, and credentialed URLs."""
    try:
        parts = urlsplit(url)
        host = (parts.hostname or "").lower().rstrip(".")
    except ValueError:
        return True
    if parts.username or parts.password or not host:
        return True
    if host == "localhost" or host.endswith(".local"):
        return True
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        return False
    return bool(
        address.is_private
        or address.is_loopback
        or address.is_link_local
        or address.is_reserved
        or address.is_unspecified
    )


def is_social_url(url: str) -> bool:
    host = (urlsplit(url).hostname or "").lower()
    return any(host == domain or host.endswith(f".{domain}") for domain in SOCIAL_DOMAINS)


def url_extension(url: str) -> str:
    return Path(urlsplit(url).path).suffix.lower()


def is_document_url(url: str) -> bool:
    return url_extension(url) in DOCUMENT_EXTENSIONS


def _matches(text: str, terms: Iterable[str]) -> list[str]:
    folded = text.casefold()
    matched: set[str] = set()
    for term in terms:
        clean = term.strip()
        if not clean:
            continue
        needle = clean.casefold()
        if clean.isascii():
            # Short terms such as UP, CG, and NIT must be complete tokens. This
            # avoids classifying "group" as UP or "unit" as NIT.
            pattern = rf"(?<![a-z0-9]){re.escape(needle)}(?![a-z0-9])"
            if re.search(pattern, folded):
                matched.add(clean)
        elif needle in folded:
            matched.add(clean)
    return sorted(matched, key=str.casefold)


def _location(
    text: str, queries: dict[str, list[str]]
) -> tuple[str, str, list[str]]:
    state_matches = _matches(text, queries.get("states", []))
    district_matches = _matches(text, queries.get("districts", []))
    folded_states = {item.casefold() for item in state_matches}

    state = ""
    if {"chhattisgarh", "cg", "छत्तीसगढ़"} & folded_states:
        state = "Chhattisgarh"
    elif {"uttar pradesh", "up", "उत्तर प्रदेश"} & folded_states:
        state = "Uttar Pradesh"

    district = district_matches[0] if district_matches else ""
    return state, district, state_matches + district_matches


def detect_restricted_access(text: str) -> tuple[bool, bool, bool]:
    folded = text.casefold()
    return (
        any(marker.casefold() in folded for marker in CAPTCHA_MARKERS),
        any(marker.casefold() in folded for marker in LOGIN_MARKERS),
        any(marker.casefold() in folded for marker in PAYWALL_MARKERS),
    )


def _category(
    url: str,
    source_type: str,
    matches: dict[str, list[str]],
) -> str:
    if matches["tender"]:
        return "tender"
    if matches["job"]:
        return "job"
    if source_type.casefold() in {"newspaper", "epaper"}:
        return "newspaper"
    if matches["news"]:
        return "news"
    if is_document_url(url):
        return "document"
    return "unknown"


def validate_candidate(
    *,
    url: str,
    title: str = "",
    context_text: str = "",
    page_text: str = "",
    discovered_from: str = "",
    source_type: str = "",
    source_state: str = "",
    source_district: str = "",
    source_name: str = "",
    robots_allowed: bool = True,
    requires_playwright: bool = False,
    duplicate: bool = False,
    queries: dict[str, list[str]] | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Score a candidate and return the complete queue-record shape."""
    queries = queries or load_discovery_queries()
    normalized = normalize_url(url)
    now = now or datetime.now(timezone.utc)
    timestamp = now.isoformat()
    domain = (urlsplit(normalized).hostname or "") if normalized else ""
    searchable = " ".join(
        part for part in (normalized, title, context_text, page_text, source_name) if part
    )
    restricted_text = " ".join(
        part for part in (title, context_text, page_text) if part
    )
    captcha, login, paywall = detect_restricted_access(restricted_text)

    grouped_matches = {
        "tender": _matches(searchable, queries.get("tender", [])),
        "job": _matches(searchable, queries.get("job", [])),
        "news": _matches(searchable, queries.get("news", [])),
    }
    state, district, location_matches = _location(searchable, queries)
    state = state or source_state
    district = district or source_district
    matched_keywords = sorted(
        {
            *grouped_matches["tender"],
            *grouped_matches["job"],
            *grouped_matches["news"],
            *location_matches,
        },
        key=str.casefold,
    )

    category = _category(normalized, source_type, grouped_matches)
    extension = url_extension(normalized)
    requires_ocr = bool(
        extension in IMAGE_EXTENSIONS
        or (
            extension == ".pdf"
            and source_type.casefold() in {"newspaper", "epaper"}
        )
    )

    score = 0
    reasons: list[str] = []
    if domain.endswith(".gov.in") or domain.endswith(".nic.in"):
        score += 30
        reasons.append("official government domain")
    elif any(token in domain for token in ("gov", "nic", "nigam", "authority")):
        score += 14
        reasons.append("likely official authority domain")

    if source_type.casefold() in {
        "authority",
        "department",
        "district",
        "job_portal",
        "tender_portal",
    }:
        score += 12
        reasons.append("known registry source")

    topical_count = sum(len(grouped_matches[group]) for group in grouped_matches)
    if topical_count:
        score += min(30, 8 + (topical_count * 3))
        reasons.append("matched opportunity keywords")
    if is_document_url(normalized):
        score += 15
        reasons.append("links to a public document")
    if RECENT_DATE_PATTERN.search(searchable):
        score += 8
        reasons.append("contains a recent date")
    if state:
        score += 8
        reasons.append(f"matches {state}")
    if district:
        score += 5
        reasons.append(f"matches district {district}")

    folded = searchable.casefold()
    if any(marker.casefold() in folded for marker in ARCHIVE_MARKERS):
        score -= 18
        reasons.append("appears to be an archive")
    if category == "unknown":
        score -= 18
        reasons.append("no tender, job, news, or document signal")

    status = "pending_review"
    rejection_reason = ""
    if not normalized or is_private_or_local_url(normalized):
        status = "rejected"
        rejection_reason = "Invalid, credentialed, local, or private-network URL"
    elif is_social_url(normalized):
        status = "rejected"
        rejection_reason = "Social/private platform is outside safe discovery scope"
    elif not robots_allowed:
        status = "rejected"
        rejection_reason = "robots.txt does not allow discovery"
    elif captcha:
        status = "captcha_required"
        rejection_reason = "CAPTCHA detected; not fetched or bypassed"
    elif login:
        status = "rejected"
        rejection_reason = "Login or authentication appears to be required"
    elif paywall:
        status = "rejected"
        rejection_reason = "Paywalled or subscription-only content detected"
    elif duplicate:
        status = "rejected"
        rejection_reason = "Duplicate of a known or queued URL"
    elif score < 25:
        status = "rejected"
        rejection_reason = "Insufficient relevant public-source signals"

    score = max(0, min(100, score))
    reason = rejection_reason or "; ".join(reasons[:5]) or "Pending admin review"
    return {
        "url": normalized or str(url).strip(),
        "title": title.strip() or source_name.strip() or normalized,
        "domain": domain,
        "state": state,
        "district": district,
        "source_type": source_type or "web",
        "category": category,
        "matched_keywords": matched_keywords,
        "confidence_score": score,
        "discovered_from": discovered_from,
        "first_seen_at": timestamp,
        "last_seen_at": timestamp,
        "robots_allowed": bool(robots_allowed),
        "requires_ocr": requires_ocr,
        "requires_playwright": bool(requires_playwright),
        "requires_captcha": bool(captcha),
        "status": status,
        "reason": reason,
    }


__all__ = [
    "DOCUMENT_EXTENSIONS",
    "detect_restricted_access",
    "is_document_url",
    "is_private_or_local_url",
    "is_social_url",
    "load_discovery_queries",
    "normalize_url",
    "url_extension",
    "validate_candidate",
]
