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
import time
import uuid
import base64
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


def _auth_email(token: str | None) -> str | None:
    """Return the email the JWT *actually* belongs to (verified with Supabase Auth).

    Never trust the email string a caller passes — validate it against this.
    Returns the lower-cased verified email, or None if the token is missing or
    can't be validated."""
    if not token:
        return None
    client = _sb()
    if not client:
        return None
    try:
        resp = client.auth.get_user(token)
        user = getattr(resp, "user", None)
        email = getattr(user, "email", None) if user else None
        return email.strip().lower() if email else None
    except Exception as e:
        logging.warning(f"Token validation failed: {e}")
        return None


def _identity_ok(email: str, token: str | None) -> bool:
    """Defense-in-depth identity gate for cloud user-data operations.

    With a token present, the requested email MUST equal the token's verified
    identity or we refuse — so a bug/forged email can never act on another user's
    rows even before RLS sees the query. (DB RLS enforces the same rule.) With no
    token we allow the email-scoped LOCAL fallback (offline dev), which carries no
    cross-user exposure and is blocked from the cloud by RLS anyway."""
    if not token:
        return True
    verified = _auth_email(token)
    if verified is None:
        logging.warning("Rejecting cloud op: token could not be validated.")
        return False
    if verified != email.strip().lower():
        logging.warning("Rejecting cloud op: requested email != token identity.")
        return False
    return True


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


def get_google_oauth_url(redirect_to: str = "",
                         supabase_url: str | None = None,
                         supabase_key: str | None = None) -> str | None:
    """Return the Google sign-in URL via Supabase, using the IMPLICIT OAuth flow.

    Why implicit (not the SDK's default PKCE): this Streamlit app is stateless
    across the OAuth redirect — the user comes back in a brand-new server session.
    PKCE stores a one-time `code_verifier` inside the client that built the URL and
    requires that SAME client to exchange the returned `?code=…`; by the time the
    user returns, that client (and the verifier) is gone, so PKCE can NEVER
    complete here and would bounce the user straight back to the login screen.

    The implicit flow instead returns the access + refresh tokens directly in the
    URL fragment (#access_token=…&refresh_token=…). The app's fragment handler
    lifts those into the session and restore_session() locks them in (set_session),
    so the user stays signed in across the redirect and later reconnects.
    """
    # Prefer credentials passed by the caller (app.py resolves them from env OR
    # st.secrets); fall back to env vars for non-Streamlit callers.
    url = supabase_url or os.getenv("SUPABASE_URL")
    key = supabase_key or os.getenv("SUPABASE_KEY")
    if not (url and key):
        return None
    try:
        from supabase import create_client
        # create_client expects SyncClientOptions (has the storage/httpx fields);
        # fall back across versions that name it differently.
        try:
            from supabase.lib.client_options import SyncClientOptions as _Opts
        except Exception:
            try:
                from supabase.lib.client_options import ClientOptions as _Opts  # type: ignore
            except Exception:
                from supabase import ClientOptions as _Opts  # type: ignore
        client = create_client(url, key, options=_Opts(flow_type="implicit"))
        opts = {"redirect_to": redirect_to} if redirect_to else {}
        resp = client.auth.sign_in_with_oauth({"provider": "google", "options": opts})
        return resp.url if resp else None
    except Exception as e:
        logging.warning(f"Google OAuth URL failed: {e}")
        return None


def login_user(email: str, password: str) -> tuple[bool, str, str | None, str | None]:
    """
    Returns (success, message, access_token, refresh_token).
    access_token is the short-lived (≈1h) Supabase JWT — store it in session
    state and pass it to every user-data call so RLS is enforced.
    refresh_token is long-lived; persist it so the session can be transparently
    renewed (see restore_session) instead of logging the user out after an hour.
    Both tokens are None on the local fallback (offline dev mode).
    """
    email = email.strip().lower()
    sb = _sb()
    if sb:
        try:
            resp    = sb.auth.sign_in_with_password({"email": email, "password": password})
            sess    = getattr(resp, "session", None)
            token   = getattr(sess, "access_token", None) if sess else None
            refresh = getattr(sess, "refresh_token", None) if sess else None
            return True, "Login successful.", token, refresh
        except Exception as e:
            low = str(e).lower()
            # Surface the real reason instead of masking it as "invalid password".
            if "not confirmed" in low or "confirm" in low:
                return False, "EMAIL_NOT_CONFIRMED", None, None
            if any(s in low for s in ("rate", "limit", "429", "too many")):
                return False, "RATE_LIMIT", None, None
            if any(s in low for s in ("invalid", "credential", "password")):
                return False, "Invalid email or password.", None, None
            logging.warning(f"Supabase login failed ({e}), trying local fallback.")
    ok, msg = _local_login(email, password)
    return ok, msg, None, None


def _decode_jwt_unverified(token: str | None) -> dict | None:
    """Decode a JWT's payload WITHOUT verifying its signature. Returns dict or None.

    Used only to read `email`/`exp` for fast local session restoration. This is
    safe: the token is the user's own (kept in their own browser), and every real
    data request still sends it to Supabase where RLS re-validates it — a tampered
    token simply returns no rows, never another user's data.
    """
    try:
        parts = str(token).split(".")
        if len(parts) < 2:
            return None
        payload = parts[1] + "=" * (-len(parts[1]) % 4)        # pad to base64 multiple
        return json.loads(base64.urlsafe_b64decode(payload).decode("utf-8"))
    except Exception:
        return None


def restore_session(access_token: str | None,
                    refresh_token: str | None = None) -> dict | None:
    """Rehydrate a Supabase session from stored tokens. Never raises.

    Streamlit sessions are in-memory, so a WebSocket drop (mobile backgrounding,
    network blip, Cloud restart) wipes the session and would normally bounce the
    user to the login screen. We persist the tokens in the browser and call this
    on a fresh load to silently restore the user.

    When a refresh_token is supplied we call set_session(), which transparently
    mints a NEW access_token if the stored one has expired — so the user stays
    signed in for as long as the long-lived refresh token is valid, not just the
    1-hour access-token window. Falls back to validating the access_token alone.

    Returns {"email", "access_token", "refresh_token"} on success, else None.
    """
    if not access_token:
        return None

    # ── Fast path: the access token is still valid → trust it LOCALLY, with no
    # network call at all. This is what keeps a user signed in while navigating:
    # a flaky connection or a slow Supabase response on reconnect can no longer
    # bounce them to the login screen, because we don't depend on the network for
    # a token that hasn't expired yet. (Safe: the token is the user's own and every
    # real data call still re-validates it against Supabase RLS.)
    claims = _decode_jwt_unverified(access_token)
    if claims:
        email = (claims.get("email") or "").strip().lower()
        exp   = claims.get("exp") or 0
        if email and exp and exp > time.time() + 60:        # 60s safety margin
            return {"email": email, "access_token": access_token,
                    "refresh_token": refresh_token}

    sb = _sb()
    # ── Expired / unreadable token → mint a fresh one with the refresh token.
    if sb and refresh_token:
        try:
            resp  = sb.auth.set_session(access_token, refresh_token)
            sess  = getattr(resp, "session", None)
            user  = getattr(resp, "user", None) or (getattr(sess, "user", None) if sess else None)
            email = getattr(user, "email", None) if user else None
            if email and sess:
                return {
                    "email":         email.strip().lower(),
                    "access_token":  getattr(sess, "access_token", access_token) or access_token,
                    "refresh_token": getattr(sess, "refresh_token", refresh_token) or refresh_token,
                }
        except Exception as e:
            logging.warning(f"Session refresh failed: {e}")
    # ── Last resort: validate the access token over the network.
    if sb:
        email = _auth_email(access_token)
        if email:
            return {"email": email, "access_token": access_token,
                    "refresh_token": refresh_token}
    return None


def send_password_reset(email: str, redirect_to: str = "") -> tuple[bool, str]:
    """Email the user a password-reset link via Supabase. Returns (ok, message).

    The message is the literal code 'RATE_LIMIT' when the mail server is
    throttling, so the UI can show a friendly wait-and-retry note. For privacy we
    return the same success text whether or not the email exists.
    """
    email = email.strip().lower()
    sb = _sb()
    if not sb:
        return False, "Not connected to the server right now. Please try again later."
    try:
        if redirect_to:
            sb.auth.reset_password_for_email(email, {"redirect_to": redirect_to})
        else:
            sb.auth.reset_password_for_email(email)
        return True, ("If that email has an account, a password-reset link is on "
                      "its way. Check your inbox (and spam).")
    except Exception as e:
        low = str(e).lower()
        if any(s in low for s in ("rate", "limit", "429", "too many")):
            return False, "RATE_LIMIT"
        logging.warning(f"Password reset email failed: {e}")
        return False, f"Could not send the reset link: {e}"


def update_password(new_password: str, access_token: str,
                    refresh_token: str | None = None) -> tuple[bool, str]:
    """Set a new password using the recovery session tokens from the reset link.

    Returns (ok, message). Never raises.
    """
    if not access_token:
        return False, ("Your reset session is missing — open the latest reset "
                       "link from your email again.")
    if not new_password or len(new_password) < 6:
        return False, "Password must be at least 6 characters."
    sb = _sb()
    if not sb:
        return False, "Not connected to the server right now. Please try again later."
    try:
        # Establish the recovery session, then change the password on it.
        sb.auth.set_session(access_token, refresh_token or access_token)
        sb.auth.update_user({"password": new_password})
        return True, "Your password has been updated. Please log in with your new password."
    except Exception as e:
        low = str(e).lower()
        if "expired" in low or "invalid" in low:
            return False, "This reset link has expired. Please request a new one."
        logging.warning(f"Password update failed: {e}")
        return False, f"Could not update password: {e}"


# ===========================================================================
# 2. PROFILES
# ===========================================================================

def get_profile(email: str, token: str | None = None) -> dict | None:
    email = email.strip().lower()
    if not _identity_ok(email, token):
        return None
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
    if not _identity_ok(email, token):
        raise PermissionError("Identity check failed — cannot save another user's profile.")
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
    if not _identity_ok(email, token):
        return []
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
    if not _identity_ok(email, token):
        raise PermissionError("Identity check failed — cannot modify another user's pipeline.")
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
    if not _identity_ok(email, token):
        return []
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
                  token: str | None = None,
                  expiry_date: str | None = None,
                  doc_type: str | None = None) -> str | None:
    """Store a document securely in Supabase Storage + metadata table.

    expiry_date (ISO 'YYYY-MM-DD') powers proactive renewal alerts.
    """
    email  = email.strip().lower()
    if not _identity_ok(email, token):
        raise PermissionError("Identity check failed — cannot upload to another user's vault.")
    doc_id = uuid.uuid4().hex[:16]
    meta   = {
        "doc_id":      doc_id,
        "email":       email,
        "name":        name,
        "filename":    filename,
        "mime_type":   mime_type,
        "size_bytes":  len(content),
        "uploaded_at": _now_iso(),
        "expiry_date": (expiry_date or None),
        "doc_type":    (doc_type or None),
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
    if not _identity_ok(email, token):
        return None
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
    if not _identity_ok(email, token):
        raise PermissionError("Identity check failed — cannot delete another user's document.")
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
