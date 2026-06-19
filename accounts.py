"""
accounts.py — per-contractor profiles + saved-tender pipeline.

Works with Supabase when configured, else a local JSON file so the MVP runs
with no backend. Auth here is a simple email gate (MVP only). For production,
swap to Supabase Auth (magic link / password) and per-user RLS — the data
model below stays the same.
"""

from __future__ import annotations

import os
import json
import uuid
import hashlib
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
import core

load_dotenv()
DATA = Path(__file__).parent / "data"
DATA.mkdir(exist_ok=True)
LOCAL_PROFILES = DATA / "profiles.json"
LOCAL_SAVED = DATA / "saved_tenders.json"
LOCAL_DOCS = DATA / "documents.json"
VAULT_DIR = DATA / "vault"


def _sb():
    url, key = os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY")
    if url and key:
        try:
            from supabase import create_client
            return create_client(url, key)
        except Exception:
            return None
    return None


def _load_json(path):
    if path.exists():
        try:
            return json.loads(path.read_text())
        except Exception:
            return {}
    return {}


def _save_json(path, obj):
    path.write_text(json.dumps(obj, indent=2, default=str))


# --- Profiles ---------------------------------------------------------------
def get_profile(email: str) -> dict | None:
    email = email.strip().lower()
    sb = _sb()
    if sb:
        try:
            rows = sb.table("profiles").select("*").eq("email", email).execute().data
            return rows[0] if rows else None
        except Exception:
            pass
    return _load_json(LOCAL_PROFILES).get(email)


def save_profile(email: str, profile: dict) -> None:
    email = email.strip().lower()
    record = {**core.DEFAULT_PROFILE, **profile, "email": email}
    sb = _sb()
    if sb:
        try:
            sb.table("profiles").upsert(record, on_conflict="email").execute()
            return
        except Exception:
            pass
    store = _load_json(LOCAL_PROFILES)
    store[email] = record
    _save_json(LOCAL_PROFILES, store)


# --- Saved-tender pipeline --------------------------------------------------
def list_saved(email: str) -> list[dict]:
    email = email.strip().lower()
    sb = _sb()
    if sb:
        try:
            return sb.table("saved_tenders").select("*").eq("email", email).execute().data
        except Exception:
            pass
    return _load_json(LOCAL_SAVED).get(email, [])


def save_tender(email: str, source_id: str, status="interested", note="") -> None:
    email = email.strip().lower()
    rec = {"email": email, "source_id": source_id, "status": status, "note": note}
    sb = _sb()
    if sb:
        try:
            sb.table("saved_tenders").upsert(rec, on_conflict="email,source_id").execute()
            return
        except Exception:
            pass
    store = _load_json(LOCAL_SAVED)
    items = [s for s in store.get(email, []) if s.get("source_id") != source_id]
    items.append(rec)
    store[email] = items
    _save_json(LOCAL_SAVED, store)


# --- Document vault ---------------------------------------------------------

def _vault_dir(email: str) -> Path:
    """Per-user local storage directory (email hashed to stay filesystem-safe)."""
    safe = hashlib.md5(email.encode()).hexdigest()[:16]
    d = VAULT_DIR / safe
    d.mkdir(parents=True, exist_ok=True)
    return d


def _now_iso() -> str:
    return datetime.utcnow().isoformat()


def list_documents(email: str) -> list[dict]:
    """Return metadata list for the user's vault, newest first."""
    email = email.strip().lower()
    sb = _sb()
    if sb:
        try:
            return (sb.table("documents").select("*")
                    .eq("email", email)
                    .order("uploaded_at", desc=True)
                    .execute().data)
        except Exception:
            pass
    return list(reversed(_load_json(LOCAL_DOCS).get(email, [])))


def save_document(email: str, name: str, filename: str,
                  content: bytes, mime_type: str = "application/octet-stream") -> str:
    """Store a document. Returns the new doc_id."""
    email = email.strip().lower()
    doc_id = uuid.uuid4().hex[:16]
    meta = {
        "doc_id": doc_id,
        "email": email,
        "name": name,
        "filename": filename,
        "mime_type": mime_type,
        "size_bytes": len(content),
        "uploaded_at": _now_iso(),
    }
    sb = _sb()
    if sb:
        try:
            sb.storage.from_("vault").upload(
                f"{email}/{doc_id}/{filename}", content, {"content-type": mime_type}
            )
            sb.table("documents").insert(meta).execute()
            return doc_id
        except Exception:
            pass
    # Local fallback — raw bytes in vault dir, metadata in documents.json
    (_vault_dir(email) / f"{doc_id}.bin").write_bytes(content)
    store = _load_json(LOCAL_DOCS)
    store.setdefault(email, []).append(meta)
    _save_json(LOCAL_DOCS, store)
    return doc_id


def get_document_bytes(email: str, doc_id: str) -> bytes | None:
    """Fetch raw bytes for a vault document. Returns None if not found."""
    email = email.strip().lower()
    sb = _sb()
    if sb:
        try:
            rows = (sb.table("documents").select("filename")
                    .eq("email", email).eq("doc_id", doc_id).execute().data)
            if rows:
                return sb.storage.from_("vault").download(
                    f"{email}/{doc_id}/{rows[0]['filename']}")
        except Exception:
            pass
    f = _vault_dir(email) / f"{doc_id}.bin"
    return f.read_bytes() if f.exists() else None


def delete_document(email: str, doc_id: str) -> None:
    """Remove a document from the vault (storage + metadata)."""
    email = email.strip().lower()
    sb = _sb()
    if sb:
        try:
            rows = (sb.table("documents").select("filename")
                    .eq("email", email).eq("doc_id", doc_id).execute().data)
            if rows:
                sb.storage.from_("vault").remove(
                    [f"{email}/{doc_id}/{rows[0]['filename']}"])
            sb.table("documents").delete().eq("email", email).eq("doc_id", doc_id).execute()
            return
        except Exception:
            pass
    f = _vault_dir(email) / f"{doc_id}.bin"
    if f.exists():
        f.unlink()
    store = _load_json(LOCAL_DOCS)
    store[email] = [d for d in store.get(email, []) if d.get("doc_id") != doc_id]
    _save_json(LOCAL_DOCS, store)
