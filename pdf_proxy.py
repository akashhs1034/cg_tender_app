"""
pdf_proxy.py — fetch tender PDFs from government portals server-side.

Strategy:
  1. If document_url already ends in .pdf / .doc / .docx / .xls → fetch directly.
  2. If it's a portal page → load the page and extract the first file link from it.
  3. Return (bytes, mime_type, filename) so the caller can pass to st.download_button.

Returns (None, "", "") when the document cannot be retrieved — caller should
fall back to showing the portal link.
"""

from __future__ import annotations

import re
import warnings
from urllib.parse import urljoin, urlparse, unquote

import requests
from bs4 import BeautifulSoup

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,"
        "application/pdf,application/msword,*/*;q=0.8"
    ),
    "Accept-Language": "en-IN,en;q=0.9",
}

_FILE_EXTS = (".pdf", ".doc", ".docx", ".xls", ".xlsx", ".zip", ".rar")


def _is_direct_file(url: str) -> bool:
    path = urlparse(url).path.lower().split("?")[0]
    return any(path.endswith(e) for e in _FILE_EXTS)


def _filename_from_url(url: str, fallback: str = "tender_document.pdf") -> str:
    path = unquote(urlparse(url).path)
    name = path.rstrip("/").split("/")[-1]
    if not name or not any(name.lower().endswith(e) for e in _FILE_EXTS):
        name = fallback
    # Sanitise
    name = re.sub(r'[<>:"/\\|?*]', "_", name)
    return name[:120]


def _get(url: str, timeout: int = 20) -> requests.Response | None:
    """GET with SSL fallback and error handling."""
    try:
        r = requests.get(url, headers=_HEADERS, timeout=timeout,
                         verify=True, allow_redirects=True)
        r.raise_for_status()
        return r
    except requests.exceptions.SSLError:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            try:
                r = requests.get(url, headers=_HEADERS, timeout=timeout,
                                 verify=False, allow_redirects=True)
                r.raise_for_status()
                return r
            except Exception:
                return None
    except Exception:
        return None


def find_direct_link(portal_url: str) -> str | None:
    """
    Load a portal page and return the first downloadable file link found.
    Returns None if no file link found.
    """
    resp = _get(portal_url, timeout=15)
    if not resp:
        return None

    ct = resp.headers.get("Content-Type", "")
    # If the response itself is a file, the URL was already direct
    if any(x in ct for x in ("pdf", "msword", "octet-stream", "excel", "zip")):
        return portal_url

    soup = BeautifulSoup(resp.text, "html.parser")

    # Priority 1: links whose href ends in a file extension
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if not href or href.startswith("javascript"):
            continue
        full = urljoin(portal_url, href)
        if _is_direct_file(full):
            return full

    # Priority 2: links whose visible text suggests a document
    doc_words = ("download", "nit", "tender document", "pdf", "view document",
                 "bid document", "notice", "corrigendum")
    for a in soup.find_all("a", href=True):
        text = a.get_text(strip=True).lower()
        href = a["href"].strip()
        if not href or href.startswith("javascript"):
            continue
        if any(w in text or w in href.lower() for w in doc_words):
            full = urljoin(portal_url, href)
            if full != portal_url:
                return full

    # Priority 3: iframe / embed src pointing to a file
    for tag in soup.find_all(["iframe", "embed", "object"], src=True):
        src = tag["src"].strip()
        if _is_direct_file(src):
            return urljoin(portal_url, src)

    return None


def fetch_pdf(url: str, timeout: int = 25) -> tuple[bytes | None, str, str]:
    """
    Fetch a tender document and return (bytes, mime_type, filename).
    bytes is None when the document cannot be retrieved.
    """
    if not url:
        return None, "", ""

    # Step 1: resolve to a direct file link if needed
    if _is_direct_file(url):
        target = url
    else:
        target = find_direct_link(url)
        if not target:
            return None, "", ""

    # Step 2: download the file
    resp = _get(target, timeout=timeout)
    if not resp or not resp.content:
        return None, "", ""

    ct = resp.headers.get("Content-Type", "application/octet-stream")

    # Reject HTML error pages masquerading as downloads
    if "text/html" in ct.lower() and len(resp.content) < 30_000:
        return None, "", ""

    # Step 3: determine filename
    cd = resp.headers.get("Content-Disposition", "")
    if "filename=" in cd:
        raw = cd.split("filename=")[-1].strip().strip('"').strip("'")
        fname = re.sub(r'[<>:"/\\|?*]', "_", unquote(raw))[:120]
        if not fname:
            fname = _filename_from_url(target)
    else:
        fname = _filename_from_url(target)

    return resp.content, ct, fname


def mime_to_ext(mime: str) -> str:
    """Return a file extension for a MIME type (with leading dot)."""
    m = mime.lower().split(";")[0].strip()
    return {
        "application/pdf":                      ".pdf",
        "application/msword":                   ".doc",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
        "application/vnd.ms-excel":             ".xls",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
        "application/zip":                      ".zip",
        "application/x-zip-compressed":        ".zip",
        "application/octet-stream":             ".pdf",  # assume PDF for govt portals
    }.get(m, ".pdf")
