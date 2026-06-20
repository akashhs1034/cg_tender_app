"""alerts.py -- email digest of matching tenders for each contractor profile.

Called by ingest.py after every pipeline run. Skipped when RESEND_API_KEY is
not set, so local dev and --no-alerts runs are silent.

Flow:
  1. Load all profiles (Supabase or data/profiles.json)
  2. Load alert_log to skip already-emailed (email, source_id) pairs
  3. For each profile: score every live tender, keep those above the threshold
  4. Send one digest email per profile (via Resend)
  5. Append sent pairs to alert_log so they are never re-sent
"""
from __future__ import annotations

import json
import logging
import os
from datetime import date, datetime
from pathlib import Path

from dotenv import load_dotenv

import core
import accounts

load_dotenv()
logger = logging.getLogger(__name__)

DATA = Path(__file__).parent / "data"
LOCAL_ALERT_LOG = DATA / "alert_log.json"

SCORE_THRESHOLD = int(os.getenv("ALERT_SCORE_THRESHOLD", "55"))
FROM_EMAIL      = os.getenv("FROM_EMAIL", "alerts@opporta.in")
APP_URL         = os.getenv("APP_URL", "https://opporta.streamlit.app")


# ---------------------------------------------------------------------------
# Supabase helpers
# ---------------------------------------------------------------------------
def _sb():
    url, key = os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY")
    if url and key:
        try:
            from supabase import create_client
            return create_client(url, key)
        except Exception:
            return None
    return None


# ---------------------------------------------------------------------------
# Alert log (dedup guard)
# ---------------------------------------------------------------------------
def _load_alert_log() -> set[tuple[str, str]]:
    sb = _sb()
    if sb:
        try:
            rows = sb.table("alert_log").select("email,source_id").execute().data
            return {(r["email"], r["source_id"]) for r in rows}
        except Exception:
            pass
    if LOCAL_ALERT_LOG.exists():
        try:
            return {(r["email"], r["source_id"])
                    for r in json.loads(LOCAL_ALERT_LOG.read_text())}
        except Exception:
            pass
    return set()


def _save_alert_log(entries: list[dict]) -> None:
    sb = _sb()
    if sb:
        try:
            sb.table("alert_log").upsert(entries, on_conflict="email,source_id").execute()
            return
        except Exception:
            pass
    existing = []
    if LOCAL_ALERT_LOG.exists():
        try:
            existing = json.loads(LOCAL_ALERT_LOG.read_text())
        except Exception:
            pass
    existing.extend(entries)
    LOCAL_ALERT_LOG.write_text(json.dumps(existing, indent=2, default=str))


# ---------------------------------------------------------------------------
# Profile loader
# ---------------------------------------------------------------------------
def _all_profiles() -> list[dict]:
    sb = _sb()
    if sb:
        try:
            return sb.table("profiles").select("*").execute().data or []
        except Exception:
            pass
    if accounts.LOCAL_PROFILES.exists():
        try:
            store = json.loads(accounts.LOCAL_PROFILES.read_text())
            return list(store.values())
        except Exception:
            pass
    return []


# ---------------------------------------------------------------------------
# HTML digest builder
# ---------------------------------------------------------------------------
def _score_color(score: int) -> str:
    if score >= 70:
        return "#27ae60"   # green
    if score >= 50:
        return "#e67e22"   # amber
    return "#e74c3c"       # red


def _html_digest(profile: dict, matches: list[tuple[int, dict]]) -> str:
    today  = date.today().strftime("%d %b %Y")
    name   = profile.get("company_name") or profile.get("email", "Contractor")
    email  = profile.get("email", "")
    top    = matches[:10]

    rows = ""
    for score, t in top:
        deadline = t.get("deadline") or "N/A"
        value = (t.get("value_text")
                 or (f"Rs {float(t['value_lakhs']):.1f}L" if t.get("value_lakhs") else "N/A"))
        doc_url = t.get("document_url") or APP_URL
        org     = t.get("organization") or ""
        state   = t.get("state") or ""
        cat     = t.get("category") or ""
        title   = (t.get("title") or "")[:120]
        color   = _score_color(score)
        rows += (
            f'<tr>'
            f'<td style="padding:8px;border-bottom:1px solid #eee">'
            f'<a href="{doc_url}" style="color:#1a5276;font-weight:bold;text-decoration:none">'
            f'{title}</a><br>'
            f'<small style="color:#777">{org} &bull; {state} &bull; {cat}</small>'
            f'</td>'
            f'<td style="padding:8px;border-bottom:1px solid #eee;white-space:nowrap">{value}</td>'
            f'<td style="padding:8px;border-bottom:1px solid #eee;white-space:nowrap">{deadline}</td>'
            f'<td style="padding:8px;border-bottom:1px solid #eee;text-align:center">'
            f'<span style="background:{color};color:white;padding:2px 8px;border-radius:3px;'
            f'font-size:12px">{score}</span></td>'
            f'</tr>'
        )

    n = len(top)
    return (
        '<html><body style="font-family:Arial,sans-serif;color:#333;max-width:680px;margin:auto">'
        '<div style="background:#1a5276;padding:16px 24px">'
        '<h2 style="color:white;margin:0">Opporta</h2>'
        '<p style="color:#aed6f1;margin:4px 0 0">Tender &amp; Job Intelligence</p>'
        '</div>'
        '<div style="padding:20px 24px">'
        f'<p>Hi {name},</p>'
        f'<p>We found <strong>{n} new tender{"s" if n > 1 else ""}</strong> '
        f'matching your profile as of {today}.</p>'
        '<table width="100%" cellspacing="0" style="border-collapse:collapse;font-size:14px">'
        '<tr style="background:#eaf2f8">'
        '<th style="padding:8px;text-align:left">Tender</th>'
        '<th style="padding:8px;text-align:left">Value</th>'
        '<th style="padding:8px;text-align:left">Deadline</th>'
        '<th style="padding:8px;text-align:center">Score</th>'
        '</tr>'
        f'{rows}'
        '</table>'
        f'<p style="margin-top:20px">'
        f'<a href="{APP_URL}" style="background:#1a5276;color:white;padding:10px 20px;'
        f'text-decoration:none;border-radius:4px">View All on Opporta</a>'
        f'</p>'
        '<hr style="border:none;border-top:1px solid #eee;margin:20px 0">'
        f'<p style="font-size:12px;color:#999">You are receiving this because you have an '
        f'Opporta profile ({email}). To stop alerts, update your profile preferences.</p>'
        '</div></html>'
    )


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------
def send_alerts(tenders: list[dict], dry_run: bool = False) -> int:
    """Match tenders against all profiles and send digest emails.

    Returns number of emails sent (or that would be sent in dry_run mode).
    Skips silently if RESEND_API_KEY is unset and dry_run is False.
    """
    api_key = os.getenv("RESEND_API_KEY", "")
    if not api_key and not dry_run:
        logger.warning("alerts: RESEND_API_KEY not set -- skipping email alerts")
        return 0

    profiles = _all_profiles()
    if not profiles:
        logger.info("alerts: no contractor profiles found -- nothing to alert")
        return 0

    already_sent = _load_alert_log()
    today        = date.today()
    now_iso      = datetime.utcnow().isoformat()
    sent_count   = 0
    new_log      : list[dict] = []

    for profile in profiles:
        email = (profile.get("email") or "").strip().lower()
        if not email:
            continue

        matches: list[tuple[int, dict]] = []
        for t in tenders:
            sid = t.get("source_id")
            if not sid:
                continue
            if (email, sid) in already_sent:
                continue
            if not core.state_match(t, profile):
                continue
            d = core.parse_date(t.get("deadline"))
            if d and d < today:
                continue   # skip expired
            score, _, _ = core.score_tender_for_user(t, profile)
            if score < SCORE_THRESHOLD:
                continue
            matches.append((score, t))

        if not matches:
            continue

        matches.sort(key=lambda x: -x[0])

        if dry_run:
            logger.info("alerts [DRY RUN]: would email %s -- %d tender(s)", email, len(matches))
            for score, t in matches[:3]:
                logger.info("  score=%d  %s", score, (t.get("title") or "")[:80])
            sent_count += 1
            continue

        html    = _html_digest(profile, matches)
        n       = min(len(matches), 10)
        subject = f"Opporta: {n} new tender{'s' if n > 1 else ''} match your profile today"

        try:
            import resend as _resend
            _resend.api_key = api_key
            _resend.Emails.send({
                "from": FROM_EMAIL,
                "to": [email],
                "subject": subject,
                "html": html,
            })
            logger.info("alerts: sent digest to %s (%d tenders)", email, n)
            sent_count += 1
            for _, t in matches[:10]:
                new_log.append({
                    "email": email,
                    "source_id": t["source_id"],
                    "record_type": "tender",
                    "sent_at": now_iso,
                })
        except Exception as exc:
            logger.warning("alerts: failed to email %s -- %s", email, exc)

    if new_log:
        _save_alert_log(new_log)

    return sent_count
