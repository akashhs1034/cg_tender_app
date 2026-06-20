"""
accounts.py — Secure User Profiles, Auth & Document Vault.

Handles secure interactions with Supabase Auth (GoTrue), database, and storage buckets.
Includes a highly resilient local filesystem fallback for offline development.
"""

from __future__ import annotations

import os
import json
import uuid
import hashlib
import logging
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
import core

# Set up basic logging so we stop "silently failing" when cloud errors occur
logging.basicConfig(level=logging.INFO, format="[Accounts] %(levelname)s: %(message)s")

load_dotenv()
DATA = Path(__file__).parent / "data"
DATA.mkdir(exist_ok=True)
LOCAL_PROFILES = DATA / "profiles.json"
LOCAL_SAVED = DATA / "saved_tenders.json"
LOCAL_DOCS = DATA / "documents.json"
LOCAL_USERS = DATA / "local_users.json" # Fallback for offline auth
VAULT_DIR = DATA / "vault"

def _sb():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if not (url and key):
        return None
    try:
        from supabase import create_client
        return create_client(url, key)
    except Exception as e:
        logging.error(f"Failed to initialize Supabase client: {e}")
        return None

def _load_json(path: Path) -> dict | list:
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception as e:
            logging.error(f"Corrupt JSON at {path.name}: {e}")
            return {} if "json" in str(path) else []
    return {}

def _save_json(path: Path, obj: any) -> None:
    path.write_text(json.dumps(obj, indent=2, default=str), encoding="utf-8")

def _now_iso() -> str:
    return datetime.utcnow().isoformat()

# ===========================================================================
# 1. AUTHENTICATION ENGINE (New Production Security)
# ===========================================================================

def _local_register(email: str, password: str) -> tuple[bool, str]:
    store = _load_json(LOCAL_USERS)
    if not isinstance(store, dict):
        store = {}
    if email in store:
        return False, "User already exists. Try logging in."
    store[email] = {"password": hashlib.sha256(password.encode()).hexdigest(),
                    "created_at": _now_iso()}
    _save_json(LOCAL_USERS, store)
    return True, "Account created. You can now log in."

def _local_login(email: str, password: str) -> tuple[bool, str]:
    store = _load_json(LOCAL_USERS)
    if not isinstance(store, dict):
        store = {}
    hashed = hashlib.sha256(password.encode()).hexdigest()
    if store.get(email, {}).get("password") == hashed:
        return True, "Login successful."
    return False, "Invalid email or password."

def register_user(email: str, password: str) -> tuple[bool, str]:
    email = email.strip().lower()
    sb = _sb()
    if sb:
        try:
            sb.auth.sign_up({"email": email, "password": password})
            return True, "Account created. You can now log in."
        except Exception as e:
            logging.warning(f"Supabase register failed ({e}), using local fallback.")
    return _local_register(email, password)

def login_user(email: str, password: str) -> tuple[bool, str]:
    email = email.strip().lower()
    sb = _sb()
    if sb:
        try:
            sb.auth.sign_in_with_password({"email": email, "password": password})
            return True, "Login successful."
        except Exception as e:
            logging.warning(f"Supabase login failed ({e}), trying local fallback.")
    return _local_login(email, password)


# ===========================================================================
# 2. PROFILES & PIPELINE
# ===========================================================================

def get_profile(email: str) -> dict | None:
    email = email.strip().lower()
    sb = _sb()
    if sb:
        try:
            rows = sb.table("profiles").select("*").eq("email", email).execute().data
            return rows[0] if rows else None
        except Exception as e:
            logging.error(f"Profile fetch failed: {e}")
    return _load_json(LOCAL_PROFILES).get(email)

def save_profile(email: str, profile: dict) -> None:
    email = email.strip().lower()
    record = {**core.DEFAULT_PROFILE, **profile, "email": email}
    sb = _sb()
    if sb:
        try:
            sb.table("profiles").upsert(record, on_conflict="email").execute()
            return
        except Exception as e:
            logging.error(f"Profile save failed: {e}")
            
    store = _load_json(LOCAL_PROFILES)
    store[email] = record
    _save_json(LOCAL_PROFILES, store)

def list_saved(email: str) -> list[dict]:
    email = email.strip().lower()
    sb = _sb()
    if sb:
        try:
            return sb.table("saved_tenders").select("*").eq("email", email).execute().data
        except Exception as e:
            logging.error(f"Fetch saved pipeline failed: {e}")
    return _load_json(LOCAL_SAVED).get(email, [])

def save_tender(email: str, source_id: str, status="interested", note="") -> None:
    email = email.strip().lower()
    rec = {"email": email, "source_id": source_id, "status": status, "note": note}
    sb = _sb()
    if sb:
        try:
            sb.table("saved_tenders").upsert(rec, on_conflict="email,source_id").execute()
            return
        except Exception as e:
            logging.error(f"Save tender failed: {e}")
            
    store = _load_json(LOCAL_SAVED)
    items = [s for s in store.get(email, []) if s.get("source_id") != source_id]
    items.append(rec)
    store[email] = items
    _save_json(LOCAL_SAVED, store)


# ===========================================================================
# 3. SECURE DOCUMENT VAULT
# ===========================================================================

def _vault_dir(email: str) -> Path:
    safe = hashlib.md5(email.encode()).hexdigest()[:16]
    d = VAULT_DIR / safe
    d.mkdir(parents=True, exist_ok=True)
    return d

def list_documents(email: str) -> list[dict]:
    email = email.strip().lower()
    sb = _sb()
    if sb:
        try:
            return (sb.table("documents").select("*")
                    .eq("email", email).order("uploaded_at", desc=True).execute().data)
        except Exception as e:
            logging.error(f"Document list fetch failed: {e}")
    return list(reversed(_load_json(LOCAL_DOCS).get(email, [])))

def save_document(email: str, name: str, filename: str, content: bytes, mime_type: str = "application/pdf") -> str | None:
    """Store a document securely. Uses explicit file_options for Supabase Storage API."""
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
            # Correct Supabase Py SDK Storage syntax
            path = f"{email}/{doc_id}/{filename}"
            sb.storage.from_("vault").upload(path, content, file_options={"content-type": mime_type})
            sb.table("documents").insert(meta).execute()
            return doc_id
        except Exception as e:
            logging.error(f"Cloud vault upload failed: {e}")
            
    # Local fallback
    (_vault_dir(email) / f"{doc_id}.bin").write_bytes(content)
    store = _load_json(LOCAL_DOCS)
    store.setdefault(email, []).append(meta)
    _save_json(LOCAL_DOCS, store)
    return doc_id

def get_document_bytes(email: str, doc_id: str) -> bytes | None:
    email = email.strip().lower()
    sb = _sb()
    if sb:
        try:
            rows = sb.table("documents").select("filename").eq("email", email).eq("doc_id", doc_id).execute().data
            if rows:
                path = f"{email}/{doc_id}/{rows[0]['filename']}"
                return sb.storage.from_("vault").download(path)
        except Exception as e:
            logging.error(f"Cloud vault download failed: {e}")
            
    f = _vault_dir(email) / f"{doc_id}.bin"
    return f.read_bytes() if f.exists() else None

def delete_document(email: str, doc_id: str) -> None:
    email = email.strip().lower()
    sb = _sb()
    if sb:
        try:
            rows = sb.table("documents").select("filename").eq("email", email).eq("doc_id", doc_id).execute().data
            if rows:
                path = f"{email}/{doc_id}/{rows[0]['filename']}"
                sb.storage.from_("vault").remove([path])
            sb.table("documents").delete().eq("email", email).eq("doc_id", doc_id).execute()
            return
        except Exception as e:
            logging.error(f"Cloud vault delete failed: {e}")
            
    f = _vault_dir(email) / f"{doc_id}.bin"
    if f.exists():
        f.unlink()
    store = _load_json(LOCAL_DOCS)
    if email in store:
        store[email] = [d for d in store[email] if d.get("doc_id") != doc_id]
        _save_json(LOCAL_DOCS, store)