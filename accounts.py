"""
accounts.py — Secure User Profiles, Auth & Document Vault.

Handles secure interactions with Supabase Auth (GoTrue), database, and storage buckets.
Includes a highly resilient local filesystem fallback for offline development.

Security model:
  - After login, the caller receives a Supabase JWT access_token.
  - Pass that token to every user-data function so all PostgREST queries
    carry `Authorization: Bearer <token>`.
  - Supabase RLS policies enforce auth.jwt()->>'email' = email, so a user
    can only ever read/write their own rows — even the app owner cannot.
  - Without a token (local fallback / offline) functions use the anon key
    but still scope all queries to the caller's email.
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

logging.basicConfig(level=logging.INFO, format="[Accounts] %(levelname)s: %(message)s")

load_dotenv()
DATA = Path(__file__).parent / "data"
DATA.mkdir(exist_ok=True)
LOCAL_PROFILES = DATA / "profiles.json"
LOCAL_SAVED    = DATA / "saved_tenders.json"
LOCAL_DOCS     = DATA / "documents.json"
LOCAL_USERS    = DATA / "local_users.json"
VAULT_DIR      = DATA / "vault"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _sb():
    """Anon Supabase client — for public data only."""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if not (url and key):
        return None
    try:
        from supabase import create_client
        return create_client(url, key)
    except Exception as e:
        logging.error(f"Supabase init failed: {e}")
        return None


def _sb_user(token: str | None = None):
    """
    Supabase client scoped to the logged-in user's JWT.
    When token is present, PostgREST sends Authorization: Bearer <token>,
    so RLS policies (auth.jwt()->>'email' = email) are enforced at DB level.
    """
    client = _sb()
    if client and token:
        try:
            client.postgrest.auth(token)
        except Exception:
            pass
    return client


def _load_json(path: Path) -> dict | list:
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception as e:
            logging.error(f"Corrupt JSON at {path.name}: {e}")
            return {} if "json" in str(path) else []
    return {}


def _save_json(path: Path, obj) -> None:
    path.write_text(json.dumps(obj, indent=2, default=str), encoding="utf-8")


def _now_iso() -> str:
    return datetime.utcnow().isoformat()


# ===========================================================================
# 1. AUTHENTICATION
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
    """Create an account. Returns (ok, message).

    message is a stable code on failure so the UI can react:
      'RATE_LIMIT'        -> Supabase mailer / signup rate exceeded
      'ALREADY_EXISTS'    -> email already registered
    """
    email = email.strip().lower()
    sb = _sb()
    if sb:
        try:
            sb.auth.sign_up({"email": email, "password": password})
            return True, "Account created."
        except Exception as e:
            low = str(e).lower()
            if any(s in low for s in ("rate", "limit", "exceed", "429", "too many")):
                return False, "RATE_LIMIT"
            if any(s in low for s in ("already", "registered", "exists", "duplicate")):
                return False, "ALREADY_EXISTS"
            logging.warning(f"Supabase register failed ({e}), using local fallback.")
    return _local_register(email, password)


def send_otp(email: str) -> tuple[bool, str]:
    """Send a 6-digit OTP to the email for verification."""
    email = email.strip().lower()
    sb = _sb()
    if sb:
        try:
            sb.auth.sign_in_with_otp({"email": email, "options": {"should_create_user": True}})
            return True, "Verification code sent to your email."
        except Exception as e:
            return False, f"Could not send code: {e}"
    return False, "Not connected to Supabase."


def verify_otp(email: str, token: str) -> tuple[bool, str, str | None]:
    """Verify the OTP code — returns (success, message, access_token)."""
    email = email.strip().lower()
    sb = _sb()
    if sb:
        try:
            resp = sb.auth.verify_otp({"email": email, "token": token, "type": "email"})
            access_token = resp.session.access_token if (resp and resp.session) else None
            return True, "Email verified.", access_token
        except Exception as e:
            return False, f"Invalid or expired code: {e}", None
    return False, "Not connected to Supabase.", None


def get_google_oauth_url(redirect_to: str = "") -> str | None:
    """Returns the Google OAuth redirect URL from Supabase."""
    sb = _sb()
    if sb:
        try:
            opts = {"redirect_to": redirect_to} if redirect_to else {}
            resp = sb.auth.sign_in_with_oauth({"provider": "google", "options": opts})
            return resp.url if resp else None
        except Exception as e:
            logging.warning(f"Google OAuth URL failed: {e}")
    return None


def login_user(email: str, password: str) -> tuple[bool, str, str | None]:
    """
    Returns (success, message, access_token).
    access_token is the Supabase JWT — store it in session state and pass it
    to every user-data call so RLS is enforced.
    Returns None token on local fallback (offline dev mode).
    """
    email = email.strip().lower()
    sb = _sb()
    if sb:
        try:
            resp  = sb.auth.sign_in_with_password({"email": email, "password": password})
            token = resp.session.access_token if (resp and resp.session) else None
            return True, "Login successful.", token
        except Exception as e:
            low = str(e).lower()
            # Surface the real reason instead of masking it as "invalid password".
            if "not confirmed" in low or "confirm" in low:
                return False, "EMAIL_NOT_CONFIRMED", None
            if any(s in low for s in ("rate", "limit", "429", "too many")):
                return False, "RATE_LIMIT", None
            if any(s in low for s in ("invalid", "credential", "password")):
                return False, "Invalid email or password.", None
            logging.warning(f"Supabase login failed ({e}), trying local fallback.")
    ok, msg = _local_login(email, password)
    return ok, msg, None


# ===========================================================================
# 2. PROFILES
# ===========================================================================

def get_profile(email: str, token: str | None = None) -> dict | None:
    email = email.strip().lower()
    sb = _sb_user(token)
    if sb:
        try:
            rows = sb.table("profiles").select("*").eq("email", email).execute().data
            return rows[0] if rows else None
        except Exception as e:
            logging.error(f"Profile fetch failed: {e}")
    return _load_json(LOCAL_PROFILES).get(email)


def save_profile(email: str, profile: dict, token: str | None = None) -> None:
    email  = email.strip().lower()
    record = {**core.DEFAULT_PROFILE, **profile, "email": email}
    sb = _sb_user(token)
    if sb:
        try:
            sb.table("profiles").upsert(record, on_conflict="email").execute()
            return
        except Exception as e:
            logging.error(f"Profile save failed: {e}")
    store = _load_json(LOCAL_PROFILES)
    store[email] = record
    _save_json(LOCAL_PROFILES, store)


# ===========================================================================
# 3. SAVED TENDER PIPELINE
# ===========================================================================

def list_saved(email: str, token: str | None = None) -> list[dict]:
    email = email.strip().lower()
    sb = _sb_user(token)
    if sb:
        try:
            return sb.table("saved_tenders").select("*").eq("email", email).execute().data
        except Exception as e:
            logging.error(f"Fetch saved pipeline failed: {e}")
    return _load_json(LOCAL_SAVED).get(email, [])


def save_tender(email: str, source_id: str, status="interested", note="",
                token: str | None = None) -> None:
    email = email.strip().lower()
    rec   = {"email": email, "source_id": source_id, "status": status, "note": note}
    sb    = _sb_user(token)
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
# 4. SECURE DOCUMENT VAULT
# ===========================================================================

def _vault_dir(email: str) -> Path:
    safe = hashlib.md5(email.encode()).hexdigest()[:16]
    d = VAULT_DIR / safe
    d.mkdir(parents=True, exist_ok=True)
    return d


def list_documents(email: str, token: str | None = None) -> list[dict]:
    email = email.strip().lower()
    sb = _sb_user(token)
    if sb:
        try:
            return (sb.table("documents").select("*")
                    .eq("email", email).order("uploaded_at", desc=True).execute().data)
        except Exception as e:
            logging.error(f"Document list fetch failed: {e}")
    return list(reversed(_load_json(LOCAL_DOCS).get(email, [])))


def save_document(email: str, name: str, filename: str, content: bytes,
                  mime_type: str = "application/pdf",
                  token: str | None = None) -> str | None:
    """Store a document securely in Supabase Storage + metadata table."""
    email  = email.strip().lower()
    doc_id = uuid.uuid4().hex[:16]
    meta   = {
        "doc_id":      doc_id,
        "email":       email,
        "name":        name,
        "filename":    filename,
        "mime_type":   mime_type,
        "size_bytes":  len(content),
        "uploaded_at": _now_iso(),
    }
    sb = _sb_user(token)
    if sb:
        try:
            path = f"{email}/{doc_id}/{filename}"
            sb.storage.from_("vault").upload(
                path, content, file_options={"content-type": mime_type}
            )
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


def get_document_bytes(email: str, doc_id: str,
                       token: str | None = None) -> bytes | None:
    email = email.strip().lower()
    sb = _sb_user(token)
    if sb:
        try:
            rows = (sb.table("documents").select("filename")
                    .eq("email", email).eq("doc_id", doc_id).execute().data)
            if rows:
                path = f"{email}/{doc_id}/{rows[0]['filename']}"
                return sb.storage.from_("vault").download(path)
        except Exception as e:
            logging.error(f"Cloud vault download failed: {e}")
    f = _vault_dir(email) / f"{doc_id}.bin"
    return f.read_bytes() if f.exists() else None


def delete_document(email: str, doc_id: str, token: str | None = None) -> None:
    email = email.strip().lower()
    sb = _sb_user(token)
    if sb:
        try:
            rows = (sb.table("documents").select("filename")
                    .eq("email", email).eq("doc_id", doc_id).execute().data)
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
