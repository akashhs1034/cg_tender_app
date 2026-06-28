"""
app.py -- OPPORTA  ·  Every Opportunity. One Platform.
Elite Intelligence OS for CG & UP Government Tenders & Jobs.
"""
from __future__ import annotations
import json, os
from datetime import date, datetime
from pathlib import Path
from urllib.parse import quote

import pandas as pd
import streamlit as st
import streamlit.components.v1 as _stc
import core, accounts, evaluator, i18n
import base64 as _b64

# ── LOGO ─────────────────────────────────────────────────────────────────────
# Cache the base64 data-URI so the 1.2 MB PNG is read + encoded ONCE, not on
# every Streamlit rerun (every click re-executes module-level code).
_logo_path = Path(__file__).parent / "assets" / "logo.png"

@st.cache_data(show_spinner=False)
def _logo_data_uri(path_str: str) -> str | None:
    p = Path(path_str)
    if not p.exists():
        return None
    return "data:image/png;base64," + _b64.b64encode(p.read_bytes()).decode()

_LOGO_URI = _logo_data_uri(str(_logo_path))
try:
    from PIL import Image as _PILImg
    _page_icon = _PILImg.open(_logo_path) if _logo_path.exists() else "⚡"
except Exception:
    _page_icon = "⚡"

st.set_page_config(
    page_title="Opporta · Intelligence Platform",
    page_icon=_page_icon,
    layout="wide",
    initial_sidebar_state="auto",
)

# ── SESSION STATE ─────────────────────────────────────────────────────────────
for _k, _v in {
    "authenticated": False, "email": "", "sb_token": "", "sb_refresh": "",
    "lang": "en",               # UI language: 'en' | 'hi'
    "show_pw_reset": False, "pw_reset_token": "", "pw_reset_refresh": "",
    "current_page": "🏠  Dashboard",
    "explore_search": "", "explore_category": "All",
    "explore_state": "All", "explore_district": "All",
    "explore_value": "All values", "explore_deadline": "Any deadline",
    "bid_tender": None,
    "entered_platform": False,
    "auth_mode": "login",       # "login" | "register" | "verify"
    "otp_email": "",
    "_ls_checked": False,       # True after the localStorage recovery probe fires once
}.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v

# ── SESSION RECOVERY FROM LOCALSTORAGE ───────────────────────────────────────
# Streamlit sessions are in-memory only. A WebSocket drop (mobile browser
# backgrounding, network glitch, Streamlit Cloud restart) wipes all server-side
# state and bounces the user to the login screen even with a valid JWT.
# Fix: persist email + token in browser localStorage; on a fresh session the JS
# below relays them back via query params which we validate here and use to
# silently restore the session. Params are cleared immediately so the JWT
# does not linger in the URL bar or browser history.
_QP_EMAIL   = st.query_params.get("_rce", "")
_QP_TOKEN   = st.query_params.get("_rct", "")
_QP_REFRESH = st.query_params.get("_rcr", "")
_QP_PWRESET = st.query_params.get("_pwreset", "")
if _QP_TOKEN:
    # Strip the recovery params out of the URL immediately so the JWT never
    # lingers in the address bar / browser history.
    for _p in ("_rce", "_rct", "_rcr", "_pwreset"):
        try:
            st.query_params.pop(_p, None)
        except Exception:
            pass
    if _QP_PWRESET:
        # Arrived from a password-reset email link (type=recovery): collect a new
        # password instead of logging straight in.
        st.session_state.show_pw_reset    = True
        st.session_state.pw_reset_token   = _QP_TOKEN
        st.session_state.pw_reset_refresh = _QP_REFRESH or ""
        st.session_state._ls_checked      = True
        st.rerun()
    elif not st.session_state.authenticated:
        _rec = None
        try:
            # Uses the refresh token to mint a fresh access token when the stored
            # one has expired, so the user survives >1h sessions and reconnects.
            # Also covers the Google-OAuth return (token present, email derived).
            _rec = accounts.restore_session(_QP_TOKEN, _QP_REFRESH or None)
        except Exception:
            _rec = None
        # localStorage recovery carries an explicit email (must match); the OAuth
        # return carries only the token, so we accept the token's verified email.
        if _rec and (not _QP_EMAIL or _rec.get("email") == _QP_EMAIL.strip().lower()):
            st.session_state.authenticated = True
            st.session_state.email         = _rec["email"]
            st.session_state.sb_token      = _rec.get("access_token") or _QP_TOKEN
            st.session_state.sb_refresh    = _rec.get("refresh_token") or ""
            st.session_state._ls_checked   = True
            st.session_state.current_page  = "🏠  Dashboard"
            st.rerun()
        else:
            # Recovery did not succeed THIS time. Do NOT wipe the saved
            # credentials — a transient network blip during refresh must never
            # permanently log the user out. We only mark the probe as done for
            # this session (which prevents a redirect loop); the next page load /
            # reconnect retries recovery, and the long-lived refresh token keeps
            # working. Credentials are cleared only on an explicit Log Out.
            st.session_state._ls_checked = True

# ── SESSION BOOTSTRAP — read browser state via bidirectional component ────────
# The component iframe sandbox blocks ALL navigation, so we cannot move tokens
# into the URL (every redirect just hangs). Instead we read the browser state
# directly with streamlit-js-eval — Streamlit's component VALUE channel, which is
# sandbox-safe — and restore the session in Python. One read covers BOTH:
#   • the Google-OAuth return  (tokens in the parent page's #fragment), and
#   • reconnect recovery        (tokens we saved in localStorage).
# `parent.location.hash` (not window.*) is used because the OAuth fragment lives
# on the top app window, not inside the component's own iframe.
# BOUNDED so it can NEVER infinite-loop. streamlit-js-eval re-reports its value on
# each render, which would otherwise rerun forever for a fresh (not-signed-in)
# visitor who has no session to restore — showing as a frozen / "not responding"
# desktop page. We read the browser state at most a few times, then mark it done
# and stop rendering the component entirely.
if (not st.session_state.authenticated
        and not st.session_state.get("show_pw_reset")
        and not st.session_state.get("_boot_done")
        and st.session_state.get("_boot_tries", 0) < 4):
    st.session_state["_boot_tries"] = st.session_state.get("_boot_tries", 0) + 1
    try:
        from streamlit_js_eval import streamlit_js_eval as _sje
        # Each browser access is wrapped in its own try/catch so the read NEVER
        # throws — strict-privacy browsers / ad-blockers / corporate policies block
        # localStorage in an iframe, and an unhandled throw there made the component
        # churn (reruns) and the page feel frozen for those users. Now it always
        # returns a clean value immediately and stabilises in one cycle.
        _boot = _sje(
            js_expressions=(
                "(function(){var h='',e='',t='',r='';"
                "try{h=parent.location.hash||''}catch(x){}"
                "try{e=localStorage.getItem('_op_e')||''}catch(x){}"
                "try{t=localStorage.getItem('_op_t')||''}catch(x){}"
                "try{r=localStorage.getItem('_op_r')||''}catch(x){}"
                "return JSON.stringify({h:h,e:e,t:t,r:r});})()"),
            key="op_session_boot")
        if _boot:
            st.session_state["_boot_done"] = True              # got the state → stop
            import json as _json2, urllib.parse as _up2
            _bd    = _json2.loads(_boot) if isinstance(_boot, str) else (_boot or {})
            _hash  = _bd.get("h") or ""
            _rec2  = None
            if "access_token=" in _hash:                       # ── Google OAuth return
                _fp   = _up2.parse_qs(_hash.lstrip("#"))
                _o_at = (_fp.get("access_token") or [""])[0]
                _o_rt = (_fp.get("refresh_token") or [""])[0]
                _o_ty = (_fp.get("type") or [""])[0]
                if _o_at and _o_ty == "recovery":              # password-reset link
                    st.session_state.show_pw_reset    = True
                    st.session_state.pw_reset_token   = _o_at
                    st.session_state.pw_reset_refresh = _o_rt or ""
                    st.rerun()
                elif _o_at:
                    _rec2 = accounts.restore_session(_o_at, _o_rt or None)
                    if _rec2:
                        st.session_state.current_page = "🏠  Dashboard"
            elif _bd.get("e") and _bd.get("t"):                # ── reconnect recovery
                _rec2 = accounts.restore_session(_bd.get("t"), _bd.get("r") or None)
                if _rec2 and _rec2.get("email") != (_bd.get("e") or "").strip().lower():
                    _rec2 = None                               # email/token mismatch
            if _rec2:
                st.session_state.authenticated = True
                st.session_state.email         = _rec2["email"]
                st.session_state.sb_token      = _rec2.get("access_token") or ""
                st.session_state.sb_refresh    = _rec2.get("refresh_token") or ""
                st.session_state._ls_checked   = True
                st.rerun()
    except Exception:
        st.session_state["_boot_done"] = True                  # never retry on error

# ── DESIGN SYSTEM CSS ─────────────────────────────────────────────────────────
st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;600&display=swap');

/* ── Base Reset ── */
html,body,.stApp{background:#020B18!important;color:#F1F5F9;font-family:'Inter',sans-serif;-webkit-font-smoothing:antialiased}
#MainMenu,footer,header,[data-testid="stToolbar"]{visibility:hidden}
.block-container{padding:0 2.5rem 3rem!important;max-width:1600px!important}

/* ── Sidebar ── */
section[data-testid="stSidebar"]{background:linear-gradient(180deg,#040E22 0%,#030D20 100%)!important;border-right:1px solid rgba(0,196,255,.12)!important}
section[data-testid="stSidebar"] .stButton>button{background:transparent!important;border:1px solid rgba(255,255,255,.06)!important;color:#94A3B8!important;font-size:.78rem!important;font-weight:500!important;border-radius:8px!important;text-align:left!important;justify-content:flex-start!important;padding:8px 12px!important;margin-bottom:2px}
section[data-testid="stSidebar"] .stButton>button:hover{background:rgba(0,196,255,.08)!important;border-color:rgba(0,196,255,.3)!important;color:#F1F5F9!important}
section[data-testid="stSidebar"] .stButton>button[kind="primary"]{background:linear-gradient(135deg,rgba(0,196,255,.2),rgba(27,108,247,.15))!important;border-color:rgba(0,196,255,.4)!important;color:#BAE6FD!important;font-weight:600!important}

/* ── Scrollbar ── */
::-webkit-scrollbar{width:4px;height:4px}
::-webkit-scrollbar-track{background:#020B18}
::-webkit-scrollbar-thumb{background:#1E293B;border-radius:4px}
::-webkit-scrollbar-thumb:hover{background:#00C4FF}

/* ── Global Inputs ── */
.stTextInput>div>div>input,.stNumberInput>div>div>input{background:#0B1329!important;border:1px solid rgba(0,196,255,.2)!important;border-radius:10px!important;color:#F1F5F9!important;font-size:.85rem!important;padding:10px 14px!important}
.stTextInput>div>div>input:focus,.stNumberInput>div>div>input:focus{border-color:rgba(0,196,255,.6)!important;box-shadow:0 0 0 3px rgba(0,196,255,.08)!important}
.stSelectbox>div>div{background:#0B1329!important;border:1px solid rgba(0,196,255,.2)!important;border-radius:10px!important;color:#F1F5F9!important}
.stMultiSelect>div>div{background:#0B1329!important;border:1px solid rgba(0,196,255,.2)!important;border-radius:10px!important}
.stTextArea>div>textarea{background:#0B1329!important;border:1px solid rgba(0,196,255,.2)!important;border-radius:10px!important;color:#F1F5F9!important;font-size:.84rem!important}
.stTextArea>div>textarea:focus{border-color:rgba(0,196,255,.5)!important;box-shadow:0 0 0 3px rgba(0,196,255,.06)!important}
label,.stSelectbox label,.stTextInput label,.stTextArea label,.stNumberInput label,.stMultiSelect label{color:#64748B!important;font-size:.75rem!important;font-weight:500!important;letter-spacing:.04em!important;text-transform:uppercase!important}

/* ── Main Buttons ── */
.stButton>button{background:linear-gradient(135deg,#00C4FF,#1B6CF7)!important;border:none!important;border-radius:10px!important;color:#fff!important;font-weight:600!important;font-size:.83rem!important;letter-spacing:.02em!important;transition:all .2s!important}
.stButton>button:hover{transform:translateY(-1px)!important;box-shadow:0 8px 24px rgba(0,196,255,.35)!important}
.stButton>button[kind="secondary"]{background:rgba(255,255,255,.04)!important;border:1px solid rgba(255,255,255,.08)!important;color:#94A3B8!important}
.stButton>button[kind="secondary"]:hover{background:rgba(0,196,255,.08)!important;border-color:rgba(0,196,255,.3)!important;color:#F1F5F9!important}

/* Language switcher (English | हिंदी): BOTH buttons share ONE identical design —
   same size AND same look (the subtle outlined pill). The active one is only
   gently tinted, not switched to a different bright gradient style. */
.st-key-lang_switch_top .stButton>button{
  box-sizing:border-box!important;
  width:100%!important;                            /* equal width for both */
  background:rgba(255,255,255,.04)!important;
  border:1px solid rgba(0,196,255,.30)!important;
  color:#94A3B8!important;font-weight:600!important;
  height:40px!important;min-height:40px!important;padding:0 12px!important;
  border-radius:999px!important;line-height:1!important;   /* same oval/pill shape */
  display:flex!important;align-items:center!important;justify-content:center!important;}
.st-key-lang_switch_top .stButton>button[kind="primary"]{
  background:rgba(0,196,255,.16)!important;       /* gentle highlight for active */
  border-color:rgba(0,196,255,.55)!important;color:#BAE6FD!important;}
.st-key-lang_switch_top .stButton>button:hover{
  border-color:rgba(0,196,255,.5)!important;color:#F1F5F9!important;transform:none!important;}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"]{background:rgba(11,19,41,.6);border:1px solid rgba(0,196,255,.12);border-radius:12px;padding:5px;gap:4px;backdrop-filter:blur(10px)}
.stTabs [data-baseweb="tab"]{border-radius:8px;color:#64748B!important;font-size:.82rem!important;font-weight:500!important;padding:8px 18px!important;border:none!important}
.stTabs [aria-selected="true"]{background:linear-gradient(135deg,#00C4FF,#1B6CF7)!important;color:#fff!important;font-weight:600!important;box-shadow:0 4px 12px rgba(0,196,255,.3)!important}

/* ── Expander ── */
div[data-testid="stExpander"]{background:#080F22!important;border:1px solid rgba(0,196,255,.1)!important;border-radius:12px!important}
div[data-testid="stExpander"] summary{color:#94A3B8!important;font-size:.8rem!important}

/* ── File Uploader ── */
[data-testid="stFileUploader"]{border:1.5px dashed rgba(0,196,255,.25)!important;border-radius:12px!important;background:rgba(11,19,41,.4)!important;padding:12px!important}

/* ── ──────────────────────────────────────────── ── */
/* ── COMPONENT LIBRARY                           ── */
/* ── ──────────────────────────────────────────── ── */

/* Hero */
.hero{text-align:center;padding:72px 20px 56px;position:relative}
.hero::before{content:'';position:absolute;top:0;left:50%;transform:translateX(-50%);width:600px;height:400px;background:radial-gradient(ellipse at center,rgba(0,196,255,.08) 0%,transparent 70%);pointer-events:none}
.hero-eyebrow{display:inline-flex;align-items:center;gap:7px;background:rgba(0,196,255,.08);border:1px solid rgba(0,196,255,.22);border-radius:100px;padding:6px 16px;font-size:.72rem;color:#38BDF8;font-weight:600;letter-spacing:.06em;text-transform:uppercase;margin-bottom:28px}
.hero-pulse{width:7px;height:7px;border-radius:50%;background:#00C4FF;animation:pulse 2s infinite}
@keyframes pulse{0%,100%{opacity:1;transform:scale(1)}50%{opacity:.5;transform:scale(.8)}}
.hero-h1{font-size:clamp(2.8rem,6vw,4.8rem);font-weight:900;line-height:1.05;color:#F1F5F9;letter-spacing:-.04em;margin-bottom:18px}
.hero-h1 em{font-style:normal;background:linear-gradient(135deg,#00C4FF 0%,#1B6CF7 50%,#06B6D4 100%);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}
.hero-sub{font-size:1rem;color:#7C8AA0;max-width:520px;margin:0 auto 40px;line-height:1.75;font-weight:400}
.hero-cta-row{display:flex;gap:14px;justify-content:center;align-items:center;flex-wrap:wrap}
.hero-pill{display:inline-flex;align-items:center;gap:8px;background:rgba(16,185,129,.07);border:1px solid rgba(16,185,129,.2);border-radius:100px;padding:8px 18px;font-size:.78rem;color:#10B981;font-weight:600}

/* KPI Cards */
.kpi-grid{display:grid;grid-template-columns:repeat(6,1fr);gap:14px;margin-bottom:32px}
.kpi{background:linear-gradient(145deg,#0B1329,#0D1A35);border:1px solid rgba(0,196,255,.14);border-radius:18px;padding:22px 20px 18px;position:relative;overflow:hidden;cursor:default;transition:transform .2s,box-shadow .2s,border-color .2s}
.kpi::before{content:'';position:absolute;top:0;left:0;right:0;height:2px;background:linear-gradient(90deg,#00C4FF,#1B6CF7,#93C5FD,transparent);opacity:.8}
.kpi::after{content:'';position:absolute;top:-30px;right:-20px;width:80px;height:80px;background:radial-gradient(circle,rgba(0,196,255,.06),transparent 70%);pointer-events:none}
.kpi:hover{transform:translateY(-3px);box-shadow:0 20px 48px rgba(0,196,255,.1);border-color:rgba(0,196,255,.28)}
.kpi-icon{font-size:1.1rem;margin-bottom:14px;opacity:.7}
.kpi-num{font-size:1.9rem;font-weight:900;color:#F1F5F9;line-height:1;letter-spacing:-.03em}
.kpi-lbl{font-size:.65rem;font-weight:700;color:#7C8AA0;text-transform:uppercase;letter-spacing:.1em;margin-top:7px}
.kpi-sub{font-size:.7rem;color:#10B981;margin-top:5px;font-weight:500;display:flex;align-items:center;gap:4px}
.kpi-sub.warn{color:#F59E0B}

/* Briefing Banner */
.brief{background:linear-gradient(135deg,rgba(0,196,255,.06),rgba(27,108,247,.04),rgba(16,185,129,.02));border:1px solid rgba(0,196,255,.18);border-radius:20px;padding:26px 30px;margin-bottom:28px;position:relative;overflow:hidden}
.brief::before{content:'';position:absolute;right:-50px;top:-50px;width:200px;height:200px;background:radial-gradient(circle,rgba(0,196,255,.05),transparent 70%)}
.brief-row{display:flex;align-items:center;justify-content:space-between;gap:20px;flex-wrap:wrap}
.brief-greeting{font-size:1.3rem;font-weight:800;color:#F1F5F9;letter-spacing:-.02em;margin-bottom:4px}
.brief-sub{font-size:.83rem;color:#64748B;line-height:1.5}
.brief-stats{display:flex;gap:8px;flex-wrap:wrap;margin-top:14px}
.bstat{display:inline-flex;align-items:center;gap:6px;background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.07);border-radius:100px;padding:6px 14px;font-size:.75rem;color:#CBD5E1;font-weight:500}
.bstat b{color:#F1F5F9;font-weight:700}
.live-dot{width:6px;height:6px;border-radius:50%;background:#10B981;display:inline-block;box-shadow:0 0 8px rgba(16,185,129,.6);animation:pulse 2s infinite}

/* Section Header */
.sec-hd{display:flex;align-items:center;gap:10px;margin-bottom:18px;padding-top:4px}
.sec-title{font-size:.92rem;font-weight:700;color:#F1F5F9;letter-spacing:-.01em}
.sec-badge{background:rgba(0,196,255,.1);color:#38BDF8;border:1px solid rgba(0,196,255,.2);border-radius:100px;padding:3px 12px;font-size:.67rem;font-weight:700;letter-spacing:.06em;text-transform:uppercase}
.sec-badge-green{background:rgba(16,185,129,.08);color:#10B981;border:1px solid rgba(16,185,129,.2);border-radius:100px;padding:3px 12px;font-size:.67rem;font-weight:700}
.sec-divider{flex:1;height:1px;background:linear-gradient(90deg,rgba(0,196,255,.12),transparent)}

/* Official Government Data Source Network — regional portal directory */
.portal-intro{background:linear-gradient(135deg,rgba(16,185,129,.06),rgba(2,4,10,0));border:1px solid rgba(16,185,129,.18);border-radius:14px;padding:14px 18px;margin-bottom:8px}
.portal-intro b{color:#10B981}
.portal-intro span{color:#94A3B8;font-size:.8rem;line-height:1.6}
.portal-region{display:flex;align-items:baseline;gap:10px;margin:18px 0 10px;padding-bottom:7px;border-bottom:1px solid rgba(16,185,129,.18)}
.portal-region-dot{width:7px;height:7px;border-radius:50%;background:#10B981;box-shadow:0 0 8px rgba(16,185,129,.6);flex-shrink:0;align-self:center}
.portal-region-title{font-size:.78rem;font-weight:800;color:#10B981;text-transform:uppercase;letter-spacing:.09em}
.portal-region-sub{font-size:.68rem;color:#64748B;font-weight:500}

/* Opportunity Cards */
.ocard{background:linear-gradient(145deg,#080F22,#0A1428);border:1px solid rgba(255,255,255,.06);border-radius:16px;padding:18px 20px;margin-bottom:10px;transition:border-color .2s,box-shadow .2s,transform .15s;position:relative;overflow:hidden}
.ocard::before{content:'';position:absolute;left:0;top:0;bottom:0;width:3px;background:linear-gradient(180deg,#00C4FF,#1B6CF7);opacity:0;transition:opacity .2s}
.ocard:hover{border-color:rgba(0,196,255,.25);box-shadow:0 8px 32px rgba(0,196,255,.07);transform:translateX(2px)}
.ocard:hover::before{opacity:1}
.ocard-row{display:flex;justify-content:space-between;align-items:flex-start;gap:16px}
.ocard-body{flex:1;min-width:0}
.ocard-title{font-size:.9rem;font-weight:700;color:#E2E8F0;line-height:1.45;margin-bottom:5px;letter-spacing:-.01em}
.ocard-link{color:inherit;text-decoration:none;cursor:pointer}
.ocard-link:hover{color:#00C4FF}
.ocard-link .ext{color:#00C4FF;font-size:.78em;font-weight:700;white-space:nowrap}
.ocard-org{font-size:.73rem;color:#7C8AA0;margin-bottom:12px;display:flex;align-items:center;gap:6px}
.ocard-tags{display:flex;gap:6px;flex-wrap:wrap}

/* Tags */
.tag{display:inline-flex;align-items:center;gap:4px;padding:3px 9px;border-radius:100px;font-size:.67rem;font-weight:600;white-space:nowrap;letter-spacing:.02em}
.tag-val{background:rgba(16,185,129,.08);color:#10B981;border:1px solid rgba(16,185,129,.18)}
.tag-dl{background:rgba(245,158,11,.08);color:#F59E0B;border:1px solid rgba(245,158,11,.18)}
.tag-loc{background:rgba(0,196,255,.08);color:#38BDF8;border:1px solid rgba(0,196,255,.18)}
.tag-cat{background:rgba(27,108,247,.08);color:#93C5FD;border:1px solid rgba(27,108,247,.18)}
.tag-green{background:rgba(16,185,129,.1);color:#10B981;border:1px solid rgba(16,185,129,.25)}
.tag-warn{background:rgba(245,158,11,.1);color:#F59E0B;border:1px solid rgba(245,158,11,.25)}
.tag-red{background:rgba(239,68,68,.08);color:#F87171;border:1px solid rgba(239,68,68,.2)}

/* Score Ring */
.ring{width:54px;height:54px;border-radius:50%;flex-shrink:0;display:flex;align-items:center;justify-content:center;font-size:.78rem;font-weight:900;letter-spacing:-.02em}
.ring-hi{background:rgba(16,185,129,.1);color:#10B981;border:2.5px solid #10B981;box-shadow:0 0 14px rgba(16,185,129,.15)}
.ring-md{background:rgba(245,158,11,.1);color:#F59E0B;border:2.5px solid #F59E0B;box-shadow:0 0 14px rgba(245,158,11,.15)}
.ring-lo{background:rgba(239,68,68,.08);color:#F87171;border:2.5px solid #F87171;box-shadow:0 0 14px rgba(239,68,68,.1)}

/* Job Cards */
.jcard{background:linear-gradient(145deg,#080F22,#0A1428);border:1px solid rgba(255,255,255,.06);border-radius:14px;padding:16px 20px;margin-bottom:9px;transition:border-color .2s,box-shadow .2s;position:relative;overflow:hidden}
.jcard:hover{border-color:rgba(0,196,255,.22);box-shadow:0 6px 24px rgba(0,196,255,.06)}
.jcard::before{content:'';position:absolute;left:0;top:0;bottom:0;width:3px;background:linear-gradient(180deg,#06B6D4,#00C4FF);opacity:0;transition:opacity .2s}
.jcard:hover::before{opacity:1}
.jcard-row{display:flex;justify-content:space-between;align-items:flex-start;gap:14px}
.jcard-body{flex:1;min-width:0}
.jcard-title{font-size:.88rem;font-weight:700;color:#E2E8F0;letter-spacing:-.01em;margin-bottom:4px}
.jcard-dept{font-size:.72rem;color:#7C8AA0;margin-bottom:11px}
.jvac{background:rgba(6,182,212,.08);color:#06B6D4;border:1px solid rgba(6,182,212,.2);border-radius:8px;padding:4px 10px;font-size:.72rem;font-weight:700;flex-shrink:0}

/* Opporta Intelligence Workspace */
.terminal-hd{background:linear-gradient(135deg,#080F22,#0B1329);border:1px solid rgba(0,196,255,.15);border-radius:16px;padding:20px 24px;margin-bottom:16px;position:relative;overflow:hidden}
.terminal-hd::before{content:'';position:absolute;top:0;left:0;right:0;height:1px;background:linear-gradient(90deg,transparent,#00C4FF,#1B6CF7,transparent)}
.terminal-label{font-family:'JetBrains Mono',monospace;font-size:.7rem;color:#00C4FF;font-weight:500;letter-spacing:.1em;text-transform:uppercase;margin-bottom:6px;display:flex;align-items:center;gap:8px}
.terminal-label::before{content:'>';color:#10B981}
.terminal-title{font-size:1rem;font-weight:700;color:#F1F5F9;letter-spacing:-.01em}
.terminal-sub{font-size:.8rem;color:#7C8AA0;margin-top:4px}

.res-panel{background:#080F22;border:1px solid rgba(0,196,255,.12);border-radius:14px;padding:20px 24px;margin-top:14px;position:relative;overflow:hidden}
.res-panel::before{content:'';position:absolute;top:0;left:0;right:0;height:1px;background:linear-gradient(90deg,transparent,rgba(0,196,255,.3),transparent)}
.res-score{font-size:3rem;font-weight:900;line-height:1;letter-spacing:-.05em}
.res-label{font-size:.62rem;color:#7C8AA0;font-weight:700;text-transform:uppercase;letter-spacing:.12em;margin-top:6px}
.res-verdict{font-size:.85rem;color:#94A3B8;line-height:1.65}

/* Doc Cards */
.doc-card{background:#080F22;border:1px solid rgba(255,255,255,.06);border-radius:12px;padding:14px 18px;margin-bottom:8px;display:flex;align-items:center;gap:14px;transition:border-color .2s}
.doc-card:hover{border-color:rgba(0,196,255,.2)}
.doc-icon{font-size:1.5rem;flex-shrink:0}
.doc-name{font-size:.86rem;font-weight:600;color:#E2E8F0;letter-spacing:-.01em}
.doc-meta{font-size:.7rem;color:#7C8AA0;margin-top:3px;font-family:'JetBrains Mono',monospace}

/* Profile Form */
.profile-card{background:linear-gradient(145deg,#080F22,#0B1329);border:1px solid rgba(0,196,255,.14);border-radius:18px;padding:24px 26px;margin-bottom:16px;position:relative;overflow:hidden}
.profile-card::before{content:'';position:absolute;top:0;left:0;right:0;height:1.5px;background:linear-gradient(90deg,#00C4FF,#1B6CF7,transparent);opacity:.7}
.profile-section-title{font-size:.72rem;font-weight:700;color:#00C4FF;text-transform:uppercase;letter-spacing:.1em;margin-bottom:16px;display:flex;align-items:center;gap:8px}
.profile-section-title::after{content:'';flex:1;height:1px;background:linear-gradient(90deg,rgba(0,196,255,.2),transparent)}

/* Pipeline Card */
.pipe-card{background:#080F22;border:1px solid rgba(255,255,255,.06);border-radius:13px;padding:15px 18px;margin-bottom:8px;display:flex;align-items:center;gap:14px;transition:border-color .2s}
.pipe-card:hover{border-color:rgba(0,196,255,.2)}
.pipe-status{font-size:.67rem;font-weight:700;text-transform:uppercase;letter-spacing:.07em;padding:3px 9px;border-radius:100px}

/* Stat Metric */
.stat-card{background:linear-gradient(145deg,#080F22,#0B1329);border:1px solid rgba(255,255,255,.06);border-radius:14px;padding:18px 20px;text-align:center}
.stat-num{font-size:1.8rem;font-weight:900;color:#F1F5F9;letter-spacing:-.04em;line-height:1}
.stat-lbl{font-size:.67rem;color:#7C8AA0;font-weight:600;text-transform:uppercase;letter-spacing:.1em;margin-top:6px}

/* Alert Item */
.alert-item{background:#080F22;border:1px solid rgba(0,196,255,.1);border-left:3px solid #00C4FF;border-radius:0 12px 12px 0;padding:14px 18px;margin-bottom:8px}
.alert-title{font-size:.86rem;font-weight:600;color:#E2E8F0;margin-bottom:4px}
.alert-meta{font-size:.7rem;color:#7C8AA0;font-family:'JetBrains Mono',monospace}

/* Readiness Bar */
.readiness-bar{background:#0B1329;border-radius:100px;height:6px;margin-top:8px;overflow:hidden}
.readiness-fill{height:100%;border-radius:100px;transition:width .5s ease}

/* Score Grid (6-dimension panel) */
.score-grid{display:grid;grid-template-columns:repeat(6,1fr);gap:10px;margin-bottom:18px}
.score-card{background:#080F22;border:1px solid rgba(255,255,255,.06);border-radius:12px;padding:12px 10px;text-align:center;position:relative;overflow:hidden}
.score-card::before{content:'';position:absolute;top:0;left:0;right:0;height:2px}
.score-card.hi::before{background:linear-gradient(90deg,#10B981,#059669)}
.score-card.md::before{background:linear-gradient(90deg,#F59E0B,#D97706)}
.score-card.lo::before{background:linear-gradient(90deg,#EF4444,#DC2626)}
.score-val{font-size:1.5rem;font-weight:900;line-height:1;letter-spacing:-.04em}
.score-lbl{font-size:.58rem;color:#7C8AA0;font-weight:700;text-transform:uppercase;letter-spacing:.08em;margin-top:5px}
.score-bar{height:3px;border-radius:2px;background:rgba(255,255,255,.06);margin-top:7px;overflow:hidden}
.score-bar-fill{height:100%;border-radius:2px;transition:width .5s ease}

/* HIGH PRIORITY badge */
.hp-badge{display:inline-flex;align-items:center;gap:6px;background:linear-gradient(135deg,rgba(245,158,11,.15),rgba(239,68,68,.1));border:1px solid rgba(245,158,11,.35);border-radius:8px;padding:6px 14px;font-size:.72rem;font-weight:800;color:#F59E0B;letter-spacing:.05em;text-transform:uppercase;margin-bottom:14px}

/* Eligibility badge */
.elig-yes{background:rgba(16,185,129,.1);color:#10B981;border:1px solid rgba(16,185,129,.25);border-radius:8px;padding:8px 18px;font-size:.78rem;font-weight:700;display:inline-flex;align-items:center;gap:6px}
.elig-no{background:rgba(239,68,68,.1);color:#F87171;border:1px solid rgba(239,68,68,.25);border-radius:8px;padding:8px 18px;font-size:.78rem;font-weight:700;display:inline-flex;align-items:center;gap:6px}
.elig-partial{background:rgba(245,158,11,.1);color:#F59E0B;border:1px solid rgba(245,158,11,.25);border-radius:8px;padding:8px 18px;font-size:.78rem;font-weight:700;display:inline-flex;align-items:center;gap:6px}

/* Profit panel */
.profit-panel{background:#080F22;border:1px solid rgba(255,255,255,.06);border-radius:14px;padding:18px 20px;margin-bottom:14px}
.profit-row{display:flex;justify-content:space-between;align-items:center;padding:7px 0;border-bottom:1px solid rgba(255,255,255,.04);font-size:.8rem}
.profit-row:last-child{border-bottom:none}
.profit-label{color:#7C8AA0;font-weight:500}
.profit-val{color:#E2E8F0;font-weight:700;font-family:'JetBrains Mono',monospace;font-size:.78rem}
.profit-rating{font-size:.8rem;font-weight:800;padding:6px 14px;border-radius:8px;display:inline-block;margin-top:12px}

/* Checklist */
.checklist-item{display:flex;align-items:center;gap:10px;padding:7px 0;border-bottom:1px solid rgba(255,255,255,.04);font-size:.8rem;color:#94A3B8}
.checklist-item:last-child{border-bottom:none}
.chk-icon{font-size:.85rem;flex-shrink:0;width:18px;text-align:center}
.chk-label{flex:1}
.chk-status{font-size:.65rem;font-weight:700;text-transform:uppercase;letter-spacing:.05em;padding:2px 7px;border-radius:4px}
.chk-req{background:rgba(0,196,255,.08);color:#38BDF8}
.chk-opt{background:rgba(71,85,105,.08);color:#7C8AA0}

/* Step list */
.step-item{display:flex;gap:12px;padding:8px 0;border-bottom:1px solid rgba(255,255,255,.04);font-size:.79rem;color:#94A3B8;line-height:1.5}
.step-item:last-child{border-bottom:none}
.step-num{background:rgba(0,196,255,.1);color:#38BDF8;border-radius:6px;padding:2px 8px;font-size:.68rem;font-weight:800;flex-shrink:0;height:fit-content;margin-top:2px}

@media (max-width:900px){.score-grid{grid-template-columns:repeat(3,1fr)!important}}
@media (max-width:480px){.score-grid{grid-template-columns:repeat(2,1fr)!important}}

/* Filter Row */
.filter-row{background:linear-gradient(135deg,#040E22,#080F22);border:1px solid rgba(0,196,255,.1);border-radius:14px;padding:14px 18px;margin-bottom:20px}

/* Auth Panel */
.auth-panel{padding:16px 14px}
.auth-label{font-size:.67rem;font-weight:700;color:#00C4FF;text-transform:uppercase;letter-spacing:.1em;margin-bottom:12px;display:flex;align-items:center;gap:6px}
.auth-label::before{content:'';width:6px;height:6px;border-radius:50%;background:#00C4FF;display:inline-block}
.session-badge{margin:8px 14px;padding:10px 14px;background:rgba(16,185,129,.05);border:1px solid rgba(16,185,129,.12);border-radius:10px}
.session-live{font-size:.62rem;color:#10B981;font-weight:700;text-transform:uppercase;letter-spacing:.08em;display:flex;align-items:center;gap:5px;margin-bottom:3px}
.session-email{font-size:.74rem;color:#64748B;font-family:'JetBrains Mono',monospace}

/* Quick Filter Buttons */
.qfbtn{background:rgba(11,19,41,.8)!important;border:1px solid rgba(0,196,255,.1)!important;border-radius:10px!important;color:#64748B!important;font-size:.75rem!important;font-weight:500!important;padding:9px 14px!important}
.qfbtn:hover{border-color:rgba(0,196,255,.3)!important;color:#F1F5F9!important;background:rgba(0,196,255,.06)!important}

/* Analytics */
.chart-card{background:#080F22;border:1px solid rgba(255,255,255,.06);border-radius:14px;padding:20px;margin-bottom:16px}
.chart-title{font-size:.78rem;font-weight:700;color:#94A3B8;text-transform:uppercase;letter-spacing:.07em;margin-bottom:16px;display:flex;align-items:center;gap:8px}
.chart-title::before{content:'';width:3px;height:12px;border-radius:2px;background:#00C4FF;display:inline-block}

/* Divider */
.glass-divider{border:none;border-top:1px solid rgba(255,255,255,.05);margin:20px 0}

/* Sidebar logo */
.sb-logo{padding:20px 16px 16px;border-bottom:1px solid rgba(255,255,255,.04);margin-bottom:14px}
.sb-brand{font-size:1.15rem;font-weight:900;color:#F1F5F9;letter-spacing:-.03em;margin-bottom:3px}
.sb-brand span{background:linear-gradient(180deg,#FFFFFF 0%,#E2E8F0 55%,#CBD5E1 100%);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;text-shadow:0 0 18px rgba(255,255,255,.12);letter-spacing:.02em;font-weight:900}
.sb-tagline{font-size:.6rem;color:#566179;font-weight:600;text-transform:uppercase;letter-spacing:.1em}
.sb-nav-label{font-size:.6rem;font-weight:700;color:#566179;text-transform:uppercase;letter-spacing:.1em;padding:0 14px;margin:10px 0 6px}

/* Metric Grid */
.metric-row{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:24px}

/* Enterprise page shells */
.page-kicker{font-family:'JetBrains Mono',monospace;font-size:.66rem;font-weight:700;
  color:#38BDF8;letter-spacing:.12em;text-transform:uppercase;margin-bottom:7px}
.page-title{font-size:1.55rem;font-weight:850;color:#F8FAFC;letter-spacing:-.035em;line-height:1.15}
.page-sub{font-size:.8rem;color:#7C8AA0;line-height:1.6;margin-top:6px}
.intelligence-grid{display:grid;grid-template-columns:repeat(7,minmax(0,1fr));gap:11px;margin:0 0 24px}
.action-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:11px;margin:0 0 24px}
.action-card{background:linear-gradient(145deg,#080F22,#0B1329);border:1px solid rgba(255,255,255,.07);
  border-radius:15px;padding:16px 17px;min-height:108px;position:relative;overflow:hidden}
.action-card::before{content:'';position:absolute;left:0;top:0;bottom:0;width:2px;background:var(--accent,#00C4FF)}
.action-icon{font-size:1.15rem;margin-bottom:10px}.action-value{font-size:1.35rem;font-weight:850;color:#F8FAFC}
.action-label{font-size:.69rem;color:#94A3B8;font-weight:650;margin-top:4px}.action-note{font-size:.64rem;color:#566179;margin-top:4px}
.health-strip{display:flex;align-items:center;gap:14px;flex-wrap:wrap;background:rgba(8,15,34,.78);
  border:1px solid rgba(0,196,255,.13);border-radius:14px;padding:12px 16px;margin-bottom:24px}
.health-stat{font-size:.72rem;color:#94A3B8}.health-stat b{color:#E2E8F0}.health-link{margin-left:auto;color:#38BDF8;font-size:.72rem;font-weight:700}
.source-card{background:linear-gradient(145deg,#080F22,#0B1329);border:1px solid rgba(255,255,255,.07);
  border-radius:14px;padding:15px 17px;margin-bottom:9px}
.source-row{display:grid;grid-template-columns:minmax(160px,1.5fr) minmax(120px,.9fr) 90px 95px;gap:14px;align-items:center}
.source-name{font-size:.83rem;font-weight:700;color:#E2E8F0}.source-meta{font-size:.67rem;color:#64748B;margin-top:3px}
.source-count{font-family:'JetBrains Mono',monospace;font-size:.78rem;color:#CBD5E1}
.status-pill{display:inline-flex;align-items:center;justify-content:center;border-radius:999px;padding:4px 9px;
  font-size:.62rem;font-weight:800;letter-spacing:.05em;text-transform:uppercase}
.status-ok{color:#34D399;background:rgba(16,185,129,.1);border:1px solid rgba(16,185,129,.25)}
.status-warn{color:#FBBF24;background:rgba(245,158,11,.1);border:1px solid rgba(245,158,11,.25)}
.status-fail{color:#F87171;background:rgba(239,68,68,.1);border:1px solid rgba(239,68,68,.25)}
.st-key-hidden_job_intelligence{display:none!important}

/* Stray Streamlit cleanup */
div[data-testid="metric-container"]{background:#080F22;border:1px solid rgba(255,255,255,.06);border-radius:14px;padding:16px 20px}
div[data-testid="metric-container"] [data-testid="stMetricValue"]{color:#F1F5F9!important;font-weight:900!important;font-size:1.7rem!important}
div[data-testid="metric-container"] [data-testid="stMetricLabel"]{color:#7C8AA0!important;font-size:.7rem!important;text-transform:uppercase!important;letter-spacing:.08em!important}

/* ── Responsive Breakpoints ── */
@media (max-width:1200px){
  .kpi-grid{grid-template-columns:repeat(3,1fr)!important}
  .intelligence-grid{grid-template-columns:repeat(4,1fr)!important}
  .metric-row{grid-template-columns:repeat(2,1fr)!important}
}

/* ── Tablet (768px) ── */
@media (max-width:768px){
  .block-container{padding:0 .75rem 5rem!important}
  .kpi-grid{grid-template-columns:repeat(2,1fr)!important;gap:10px!important}
  .intelligence-grid{grid-template-columns:repeat(2,1fr)!important;gap:9px!important}
  .action-grid{grid-template-columns:repeat(2,1fr)!important;gap:9px!important}
  .source-row{grid-template-columns:1fr auto!important;gap:7px 12px!important}
  .source-row .source-last{grid-column:1/-1!important}
  .metric-row{grid-template-columns:repeat(2,1fr)!important}
  .hero{padding:36px 12px 28px!important}
  .hero-h1{font-size:2rem!important;letter-spacing:-.03em!important}
  .hero-sub{font-size:.85rem!important}
  .brief{padding:16px 18px!important}
  .brief-row{flex-direction:column!important;gap:10px!important}
  .brief-stats{gap:5px!important}
  .bstat{padding:5px 10px!important;font-size:.7rem!important}
  .ocard-row{flex-direction:column!important;gap:8px!important}
  .jcard-row{flex-direction:column!important;gap:8px!important}
  .ring{width:40px!important;height:40px!important;font-size:.68rem!important}
  .jvac{align-self:flex-start!important}
  .filter-row>div{flex-direction:column!important}
  section[data-testid="stSidebar"]{min-width:200px!important}
  .score-grid{grid-template-columns:repeat(3,1fr)!important}
  .kpi-num{font-size:1.6rem!important}
  .ocard{padding:14px 16px!important}
  .jcard{padding:13px 16px!important}
  .profile-card{padding:18px 16px!important}
  .terminal-hd{padding:16px 18px!important}
}

/* ── Mobile (480px) ── */
@media (max-width:480px){
  .block-container{padding:0 .5rem 5rem!important}
  .kpi-grid{grid-template-columns:1fr 1fr!important;gap:8px!important}
  .intelligence-grid{grid-template-columns:1fr 1fr!important;gap:8px!important}
  .action-grid{grid-template-columns:1fr 1fr!important;gap:8px!important}
  .action-card{padding:14px 13px!important;min-height:102px!important}
  .score-grid{grid-template-columns:repeat(2,1fr)!important}
  .metric-row{grid-template-columns:1fr 1fr!important;gap:8px!important}
  .hero{padding:28px 8px 20px!important}
  .hero-eyebrow{font-size:.62rem!important;padding:5px 12px!important}
  .hero-h1{font-size:1.7rem!important;line-height:1.1!important}
  .hero-sub{font-size:.8rem!important;margin-bottom:24px!important}
  .kpi-num{font-size:1.4rem!important}
  .kpi{padding:16px 14px 14px!important;border-radius:14px!important}
  .ocard{padding:12px 14px!important;margin-bottom:8px!important}
  .jcard{padding:12px 14px!important}
  .ocard-title{font-size:.84rem!important}
  .jcard-title{font-size:.83rem!important}
  .brief{padding:14px!important;border-radius:14px!important}
  .brief-greeting{font-size:1.1rem!important}
  .ring{width:38px!important;height:38px!important;font-size:.66rem!important}
  .profile-card{padding:14px 12px!important;border-radius:14px!important}
  .terminal-hd{padding:14px!important}
  .res-panel{padding:16px!important}
  .res-score{font-size:2.4rem!important}
  .doc-card{padding:12px 14px!important}
  .stTabs [data-baseweb="tab"]{font-size:.75rem!important;padding:7px 12px!important}
  .stButton>button{font-size:.8rem!important;padding:10px 14px!important;min-height:44px!important}
  .stTextInput>div>div>input,.stNumberInput>div>div>input{font-size:.88rem!important;padding:12px 12px!important;min-height:44px!important}
  .stSelectbox>div>div{min-height:44px!important}
  label{font-size:.7rem!important}
}

/* ── Tab scrolling on all small screens ── */
@media (max-width:768px){
  .stTabs [data-baseweb="tab-list"]{
    overflow-x:auto!important;
    overflow-y:hidden!important;
    flex-wrap:nowrap!important;
    -webkit-overflow-scrolling:touch!important;
    scrollbar-width:none!important;
    padding:4px!important;
    gap:3px!important;
  }
  .stTabs [data-baseweb="tab-list"]::-webkit-scrollbar{display:none!important}
  .stTabs [data-baseweb="tab"]{
    white-space:nowrap!important;
    flex-shrink:0!important;
    font-size:.76rem!important;
    padding:7px 14px!important;
  }
}

/* ── Bottom safe area for mobile browsers ── */
@media (max-width:768px){
  .block-container{padding-bottom:6rem!important}
}

/* ── Touch-friendly minimum tap targets ── */
@media (hover:none) and (pointer:coarse){
  .stButton>button{min-height:44px!important;font-size:.85rem!important}
  .stSelectbox>div>div{min-height:44px!important}
  .stTextInput>div>div>input{min-height:44px!important;font-size:16px!important}
  .stTextArea>div>textarea{font-size:16px!important}
  .stNumberInput>div>div>input{min-height:44px!important;font-size:16px!important}
  section[data-testid="stSidebar"] .stButton>button{min-height:48px!important;font-size:.85rem!important}
}

/* ── Plotly dark theme overrides ── */
.js-plotly-plot .plotly,.js-plotly-plot .plotly div{color:#94A3B8!important}
.stPlotlyChart{border-radius:12px;overflow:hidden}

/* ── Enter button glow ── */
@keyframes glow-pulse{0%,100%{box-shadow:0 0 20px rgba(0,196,255,.5),0 0 40px rgba(27,108,247,.3)}50%{box-shadow:0 0 40px rgba(0,196,255,.8),0 0 80px rgba(27,108,247,.5),0 0 120px rgba(6,182,212,.2)}}
.enter-btn{display:inline-flex;align-items:center;gap:12px;background:linear-gradient(135deg,#00C4FF,#1B6CF7,#06B6D4);border:none;border-radius:100px;padding:18px 48px;font-size:1.05rem;font-weight:800;color:#fff;cursor:pointer;letter-spacing:-.01em;animation:glow-pulse 2.5s ease-in-out infinite;transition:transform .2s;text-decoration:none}
.enter-btn:hover{transform:scale(1.04)}
.enter-arrow{font-size:1.3rem;transition:transform .2s}
.enter-btn:hover .enter-arrow{transform:translateX(5px)}

/* ── Auth card ── */
.auth-card{max-width:440px;margin:0 auto;background:linear-gradient(145deg,#080F22,#0B1329);border:1px solid rgba(0,196,255,.2);border-radius:24px;padding:32px;position:relative;overflow:hidden}
.auth-card::before{content:'';position:absolute;top:0;left:0;right:0;height:2px;background:linear-gradient(90deg,#00C4FF,#1B6CF7,#06B6D4)}
.auth-tab-row{display:flex;gap:4px;background:rgba(0,0,0,.3);border-radius:12px;padding:4px;margin-bottom:24px}
.auth-tab{flex:1;padding:10px;text-align:center;border-radius:9px;font-size:.82rem;font-weight:600;cursor:pointer;color:#7C8AA0;transition:all .2s;border:none;background:none}
.auth-tab.active{background:linear-gradient(135deg,#00C4FF,#1B6CF7);color:#fff}
.auth-divider{display:flex;align-items:center;gap:12px;margin:16px 0;color:#566179;font-size:.72rem;font-weight:600;letter-spacing:.05em}
.auth-divider::before,.auth-divider::after{content:'';flex:1;height:1px;background:rgba(255,255,255,.06)}
.otp-hint{font-size:.75rem;color:#7C8AA0;text-align:center;margin-top:10px}

/* ── Nav slide cards ── */
.nav-cards-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:24px 0}
.nav-card{background:linear-gradient(145deg,#080F22,#0B1329);border:1px solid rgba(0,196,255,.12);border-radius:16px;padding:20px 16px;text-align:center;cursor:pointer;transition:all .2s;position:relative;overflow:hidden}
.nav-card::before{content:'';position:absolute;top:0;left:0;right:0;height:2px;background:linear-gradient(90deg,#00C4FF,#1B6CF7);opacity:0;transition:opacity .2s}
.nav-card:hover{border-color:rgba(0,196,255,.3);transform:translateY(-3px);box-shadow:0 12px 32px rgba(0,196,255,.1)}
.nav-card:hover::before{opacity:1}
.nav-card-icon{font-size:1.6rem;margin-bottom:8px}
.nav-card-label{font-size:.72rem;font-weight:700;color:#94A3B8;text-transform:uppercase;letter-spacing:.06em}
@media(max-width:768px){.nav-cards-grid{grid-template-columns:repeat(2,1fr)!important;gap:10px!important}}
@media(max-width:480px){.nav-cards-grid{grid-template-columns:repeat(2,1fr)!important}}

/* ── Sidebar toggle arrow — prominent purple pill on mobile ── */
[data-testid="collapsedControl"]{
  background:linear-gradient(135deg,#00C4FF,#1B6CF7)!important;
  border-radius:0 14px 14px 0!important;
  width:28px!important;height:60px!important;
  box-shadow:4px 0 20px rgba(0,196,255,.5)!important;
  display:flex!important;align-items:center!important;justify-content:center!important;
}
[data-testid="collapsedControl"] svg{color:#fff!important;width:16px!important;height:16px!important}

/* ── ══════════════════════════════════════════════════════════ ── */
/* ── MOBILE BOTTOM TAB BAR — fixed, native-app style              ── */
/* ── ══════════════════════════════════════════════════════════ ── */
/* Desktop: hide entirely (sidebar handles nav). */
@media (min-width:769px){ .st-key-mobilenav{display:none!important} }

/* Phone/tablet: pin to bottom of the viewport as a frosted tab bar. */
@media (max-width:768px){
  .st-key-mobilenav{
    position:fixed!important;
    bottom:0!important; left:0!important; right:0!important;
    z-index:99990!important;
    background:rgba(3,10,24,.94)!important;
    backdrop-filter:blur(18px)!important;
    -webkit-backdrop-filter:blur(18px)!important;
    border-top:1px solid rgba(0,196,255,.22)!important;
    box-shadow:0 -8px 32px rgba(0,0,0,.5)!important;
    padding:6px 4px calc(6px + env(safe-area-inset-bottom)) 4px!important;
    margin:0!important;
  }
  .st-key-mobilenav [data-testid="stHorizontalBlock"]{
    gap:2px!important; flex-wrap:nowrap!important;
  }
  .st-key-mobilenav [data-testid="column"]{
    min-width:0!important; flex:1 1 0!important;
  }
  /* Each tab = stacked icon over short label, no box. */
  .st-key-mobilenav .stButton>button{
    background:transparent!important;
    border:none!important;
    box-shadow:none!important;
    color:#7C8AA0!important;
    line-height:1.35!important;
    font-weight:600!important;
    padding:3px 0 2px!important;
    min-height:52px!important;
    border-radius:12px!important;
    transition:none!important;
  }
  .st-key-mobilenav .stButton>button:hover{
    background:rgba(0,196,255,.06)!important;
    transform:none!important;
  }
  /* emoji (line 1) + label (line 2) share one <p> → one balanced size */
  .st-key-mobilenav .stButton>button p{
    font-size:.92rem!important; line-height:1.35!important; margin:0!important;
    font-weight:600!important;
  }
  /* Active tab — cyan glow pill. */
  .st-key-mobilenav .stButton>button[kind="primary"]{
    background:rgba(0,196,255,.12)!important;
    color:#38BDF8!important;
    box-shadow:0 0 0 1px rgba(0,196,255,.25) inset!important;
  }
  .st-key-mobilenav .stButton>button[kind="primary"] p{
    color:#38BDF8!important; font-weight:700!important;
  }
  /* Reserve space so the fixed bar never hides the last content. */
  .block-container{padding-bottom:84px!important}
}
</style>""", unsafe_allow_html=True)

# The public landing page has one deliberate, centered sign-in experience.
# Hide the sidebar copy until authentication so users never face duplicate forms.
if not st.session_state.authenticated:
    st.markdown(
        """<style>
        section[data-testid="stSidebar"],[data-testid="collapsedControl"]{display:none!important}
        @media(max-width:768px){
          .hero{padding-top:18px!important}
          [data-testid="stHorizontalBlock"]{gap:.45rem!important}
        }
        </style>""",
        unsafe_allow_html=True)

# ── CONSTANTS ─────────────────────────────────────────────────────────────────
# Tender sectors now come from core.CATEGORY_BUCKETS (the normalized buckets),
# so the old hardcoded SECTORS list was removed.

CG_DISTRICTS = sorted([
    "Raipur","Bilaspur","Durg","Bhilai","Korba","Raigarh","Rajnandgaon",
    "Jagdalpur","Ambikapur","Mahasamund","Dhamtari","Kanker","Dantewada",
    "Balod","Bemetara","Baloda Bazar","Gariaband","Jashpur","Kabirdham",
    "Kondagaon","Mungeli","Narayanpur","Sukma","Surajpur","Surguja",
    "Balrampur","Gaurela-Pendra-Marwahi","Manendragarh-Chirmiri-Bharatpur",
    "Mohla-Manpur-Ambagarh Chowki","Sarangarh-Bilaigarh","Shakti",
])

UP_DISTRICTS = sorted([
    "Lucknow","Kanpur","Prayagraj","Varanasi","Noida","Ghaziabad","Agra",
    "Meerut","Gorakhpur","Bareilly","Aligarh","Moradabad","Saharanpur",
    "Jhansi","Ayodhya","Muzaffarnagar","Mathura","Banda","Gonda","Bahraich",
    "Amroha","Azamgarh","Ballia","Balrampur","Barabanki","Basti","Bijnor",
    "Budaun","Bulandshahr","Chandauli","Chitrakoot","Deoria","Etah","Etawah",
    "Farrukhabad","Fatehpur","Firozabad","Gautam Buddha Nagar","Ghazipur",
    "Hapur","Hardoi","Hathras","Jalaun","Jaunpur","Amethi","Kannauj",
    "Kanpur Dehat","Kasganj","Kaushambi","Kushinagar","Lakhimpur Kheri",
    "Lalitpur","Maharajganj","Mahoba","Mainpuri","Mirzapur","Pilibhit",
    "Pratapgarh","Rae Bareli","Rampur","Sant Kabir Nagar","Bhadohi",
    "Sambhal","Shahjahanpur","Shamli","Shravasti","Siddharthnagar",
    "Sitapur","Sonbhadra","Sultanpur","Unnao",
])

STATE_DISTRICTS = {
    "Chhattisgarh":  CG_DISTRICTS,
    "Uttar Pradesh": UP_DISTRICTS,
}

# Display labels are separate from the stable internal route names. This keeps
# all existing page branches and session-state deep links working while exposing
# the full enterprise navigation requested by the product.
NAV_ITEMS = [
    ("START HERE", "Profile", "प्रोफ़ाइल", "👤  Profile"),
    ("OPPORTUNITIES", "Tender Portal", "निविदा पोर्टल", "📄  Tenders"),
    ("OPPORTUNITIES", "Government Jobs", "सरकारी नौकरियाँ", "💼  Jobs"),
    ("OVERVIEW", "Dashboard", "डैशबोर्ड", "🏠  Dashboard"),
    ("TENDER TOOLS", "Tender Intelligence", "निविदा इंटेलिजेंस", "⚡  Opporta Tender Intelligence"),
    ("TENDER TOOLS", "Bid Workspace", "बिड कार्यक्षेत्र", "🧠  Opporta Bid Workspace"),
    ("INSIGHTS", "Analytics", "विश्लेषण", "📊  Analytics"),
    ("ACCOUNT", "Document Vault", "दस्तावेज़ वॉल्ट", "🗂️  Document Vault"),
    ("ACCOUNT", "Alerts", "अलर्ट", "🔔  Alerts"),
    ("ACCOUNT", "Settings", "सेटिंग्स", "⚙️  Settings"),
]


def _nav_text(item: tuple, ui_lang: str) -> str:
    return item[2] if ui_lang == "hi" else item[1]

# ── HELPERS ───────────────────────────────────────────────────────────────────
def _secret(k):
    if k in os.environ: return os.environ[k]
    try: return st.secrets[k]
    except: return None


def _app_redirect_url() -> str:
    """Where Supabase sends the user back after Google sign-in / password reset.

    Resolution order:
      1. APP_URL (env var or Streamlit secret) — an explicit override always wins.
      2. The REAL origin the browser is on (st.context.url) — so it is
         http://localhost:8501 when run locally and https://opporta.streamlit.app
         on the deployed app, automatically, with no hard-coding.
      3. The deployed URL as a safe last resort.

    Whatever value is produced MUST also be listed in Supabase →
    Authentication → URL Configuration → Redirect URLs.
    """
    explicit = os.getenv("APP_URL") or _secret("APP_URL")
    if explicit:
        return explicit.rstrip("/")
    try:
        from urllib.parse import urlparse
        _u = urlparse(st.context.url)          # actual browser URL (Streamlit ≥1.40)
        if _u.scheme and _u.netloc:
            return f"{_u.scheme}://{_u.netloc}"
    except Exception:
        pass
    return "https://opporta.streamlit.app"


def _google_signin_button(lang: str, key: str) -> None:
    """Render 'Continue with Google' as a NATIVE link (st.link_button).

    Critical: a JS redirect from inside a Streamlit component iframe is blocked by
    the iframe sandbox (it lacks `allow-top-navigation`), so the old approach just
    hung on 'Redirecting…' and never reached Google. st.link_button renders a real
    <a> in the MAIN page DOM, which navigates the top window normally. The Supabase
    OAuth URL (implicit flow) is built once per session and cached.

    Supabase returns a URL only when the Google provider is enabled in the project.
    If it isn't, we guide the admin instead of failing silently."""
    _url = st.session_state.get("_g_oauth_url")
    if not _url:
        try:
            _url = accounts.get_google_oauth_url(
                _app_redirect_url(),
                supabase_url=_secret("SUPABASE_URL") or _secret("supabase_url"),
                supabase_key=_secret("SUPABASE_KEY") or _secret("supabase_key")) or ""
        except Exception:
            _url = ""
        st.session_state["_g_oauth_url"] = _url
    if _url:
        st.link_button("◉  " + i18n.t("continue_google", lang), _url,
                       key=key, use_container_width=True)
    else:
        if st.button("◉  " + i18n.t("continue_google", lang), key=key + "_warn",
                     width="stretch"):
            st.warning(
                "Google sign-in isn't enabled yet. Admin: in Supabase → "
                "Authentication → Providers → Google, add a Google Cloud OAuth "
                "Client ID & Secret, then add this app's URL to the allowed "
                "redirect list. Email/password sign-in works in the meantime.")


def _forgot_password_ui(lang: str, key_prefix: str) -> None:
    """A compact 'Forgot password?' expander: emails a Supabase reset link."""
    with st.expander("🔑  " + i18n.t("forgot_password", lang)):
        _fpe = st.text_input(i18n.t("reset_email_label", lang),
                             key=f"{key_prefix}_fp_email", placeholder="you@gmail.com")
        if st.button(i18n.t("send_reset_link", lang), key=f"{key_prefix}_fp_send",
                     width="stretch"):
            if not _fpe.strip():
                st.warning(i18n.t("reset_email_label", lang))
            else:
                _ok, _msg = accounts.send_password_reset(_fpe, _app_redirect_url())
                if _ok:
                    st.success(_msg)
                elif _msg == "RATE_LIMIT":
                    st.warning("⏳ Too many requests right now — please wait a few minutes and retry.")
                else:
                    st.error(_msg)

@st.cache_data(ttl=300)
def load_table(name: str) -> pd.DataFrame:
    url = _secret("SUPABASE_URL") or _secret("supabase_url")
    key = _secret("SUPABASE_KEY") or _secret("supabase_key")
    if url and key:
        try:
            from supabase import create_client
            client = create_client(url, key)
            # Paginate in batches of 1000 (Supabase default cap).
            # ORDER BY a stable key (source_id) is required: range pagination
            # without a deterministic order can return duplicate/missing rows
            # because PostgREST's row order is otherwise not guaranteed.
            all_rows, offset, batch = [], 0, 1000
            while True:
                chunk = (client.table(name).select("*")
                         .order("source_id")
                         .range(offset, offset + batch - 1).execute().data)
                if not chunk:
                    break
                all_rows.extend(chunk)
                if len(chunk) < batch:
                    break
                offset += batch
            if all_rows:
                return _drop_expired(pd.DataFrame(all_rows))
            return pd.DataFrame()
        except Exception:
            st.warning("Live data is temporarily unavailable. Showing the latest saved results.")
    else:
        st.caption("Showing the latest saved opportunity data.")
    local = Path(__file__).parent / "data" / f"{name}.csv"
    if local.exists():
        return _drop_expired(pd.read_csv(local))
    return pd.DataFrame()

def _drop_expired(df: pd.DataFrame) -> pd.DataFrame:
    """Remove rows whose deadline has passed. Rows with no deadline are kept."""
    if "deadline" not in df.columns:
        return df
    today = pd.Timestamp(date.today())
    dl = pd.to_datetime(df["deadline"], errors="coerce")
    keep = dl.isna() | (dl >= today)
    return df[keep].reset_index(drop=True)

def days_left(d) -> int | None:
    dd = core.parse_date(d)
    return (dd - date.today()).days if dd else None

# ── Vault document expiry helpers ─────────────────────────────────────────────
def _doc_expiry_status(doc: dict):
    """Return (label, color, badge_text, days) for a vault doc's validity, or
    None when no expiry is tracked. days < 0 ⇒ already expired."""
    exp = core.parse_date(doc.get("expiry_date"))
    if not exp:
        return None
    dd  = (exp - date.today()).days
    iso = exp.isoformat()
    if dd < 0:
        return ("EXPIRED", "#F87171", f"⛔ Expired {iso}", dd)
    if dd <= 30:
        return ("EXPIRING", "#F59E0B", f"⚠ Expires in {dd}d · {iso}", dd)
    return ("VALID", "#10B981", f"✅ Valid until {iso}", dd)

def _doc_expiry_alerts(docs) -> list[dict]:
    """Opporta-Intelligence document alerts (expired / expiring ≤30d), shaped
    like compute_smart_alerts() output so they slot into the 'For you' strip."""
    out = []
    for d in (docs or []):
        stt = _doc_expiry_status(d)
        if not stt:
            continue
        label, color, _badge, dd = stt
        name = safe_str(d.get("name"), 58)
        if label == "EXPIRED":
            out.append({"icon": "⛔", "color": color,
                        "title": f"Document expired — {name}",
                        "detail": f"Expired {abs(dd)} day(s) ago · upload a renewed copy to stay bid-ready",
                        "sort": (0, dd)})
        elif label == "EXPIRING":
            out.append({"icon": "📄", "color": color,
                        "title": f"Document expiring soon — {name}",
                        "detail": f"{dd} day(s) left · renew before your next bid",
                        "sort": (0, dd)})
    return out

def save_offline_tenders(records: list[dict]) -> int:
    """Upsert extracted offline (newspaper) tenders to the shared store.

    Returns the number saved. Uses the anon key (the offline_tenders table has a
    public insert policy); upsert on source_id de-duplicates re-uploads.
    """
    if not records:
        return 0
    url = _secret("SUPABASE_URL") or _secret("supabase_url")
    key = _secret("SUPABASE_KEY") or _secret("supabase_key")
    if not (url and key):
        st.error("Saving is temporarily unavailable. Please try again later.")
        return 0
    try:
        from supabase import create_client
        client = create_client(url, key)
        client.table("offline_tenders").upsert(records, on_conflict="source_id").execute()
        return len(records)
    except Exception as e:
        st.error(f"Could not save offline tenders: {e}")
        return 0

def _clickable_title(text, url, length: int = 115) -> str:
    """Render a tender title as a tappable link (opens the official portal / PDF
    in a new tab) when a usable URL exists, else plain escaped text. This is what
    makes every card directly clickable — no 'view details' tap needed first."""
    t = _html.escape(safe_str(text, length))
    u = str(url or "").strip()
    if u and u.lower() not in ("nan", "none", "—", "") and (u.startswith("http") or u.startswith("/")):
        return (f'<a href="{_html.escape(u)}" target="_blank" rel="noopener" '
                f'class="ocard-link">{t} <span class="ext">↗ open</span></a>')
    return t

def _render_offline_card(r: dict) -> None:
    """Render one newspaper/offline tender as a card (no fit score — these are
    raw newspaper extractions, so we show the printed facts honestly)."""
    _t     = _clickable_title(r.get("title"), r.get("document_url"), 120)
    _org   = _esc(r.get("organization"))
    _dist  = _esc(r.get("district"))
    _nit   = _v(r.get("nit_no"))
    _val   = _v(r.get("value_text")) or (f"₹{float(r.get('value_lakhs')):.0f}L"
                                         if r.get("value_lakhs") else "—")
    _close = _v(r.get("deadline"))
    _paper = _v(r.get("newspaper"))
    _meta  = " &nbsp;·&nbsp; ".join(x for x in [
        (f"🧾 NIT {_html.escape(_nit)}" if _nit != "—" else ""),
        (f"💰 {_html.escape(_val)}"     if _val != "—" else ""),
        (f"⏰ closes {_html.escape(_close)}" if _close != "—" else ""),
        (f"🗞 {_html.escape(_paper)}"   if _paper != "—" else ""),
    ] if x)
    st.markdown(
        f'<div class="ocard"><div class="ocard-title">📰 {_t}</div>'
        f'<div class="ocard-org">🏛 {_org} &nbsp;·&nbsp; 📍 {_dist}</div>'
        + (f'<div class="alert-meta" style="color:#94A3B8;margin-top:4px">{_meta}</div>'
           if _meta else "")
        + '</div>', unsafe_allow_html=True)
    if r.get("document_url"):
        st.link_button("🌐 Open Official Procurement Portal", r["document_url"],
                       width="stretch")

def _profile_to_resume_text(p: dict) -> str:
    """Build a keyword-matchable text blob from job seeker profile fields."""
    parts = []
    for f in ("full_name", "qualification", "degree_type", "job_category"):
        v = p.get(f, "")
        if v: parts.append(str(v))
    for lst in ("job_skills", "languages"):
        parts.extend(p.get(lst) or [])
    yrs = p.get("job_experience_years") or 0
    if yrs:
        parts.append(f"{yrs} years experience")
    return " ".join(parts)

def _has_job_profile(p: dict) -> bool:
    """True only if the user entered REAL job-seeker data (a resume's worth).

    job_category ('General') and the default languages are NOT real signals, so
    a blank profile returns False and NO match percentage is shown anywhere.
    """
    return bool(
        str(p.get("full_name") or "").strip()
        or str(p.get("qualification") or "").strip()
        or str(p.get("degree_type") or "").strip()
        or list(p.get("job_skills") or [])
        or int(p.get("job_experience_years") or 0) > 0
    )

def _render_ai_error(fallback: str = "Opporta Intelligence is unavailable right now — please try again.") -> None:
    """Show a public-safe message without exposing provider configuration."""
    st.error(fallback)

def _render_study_plan(plan: dict) -> None:
    """Render a suggested study plan dict with phases, topics, resources + disclaimer."""
    exam = _esc(plan.get("exam", "Exam"))
    days = plan.get("days_left", 0)
    _ai  = plan.get("ai", True)
    st.markdown(
        f'<div class="brief" style="margin:10px 0 14px">'
        f'<div class="brief-greeting">🧭 Suggested Study Plan · {exam}</div>'
        f'<div class="brief-sub" style="margin-top:5px;max-width:680px">{_esc(plan.get("overview",""))}</div>'
        f'<div class="brief-stats"><div class="bstat">⏳ <b>{days}</b> days to exam</div>'
        f'<div class="bstat">{"⚡ Opporta Intelligence" if _ai else "📋 General template"}</div></div>'
        f'</div>', unsafe_allow_html=True)

    for _ph in plan.get("phases", []):
        _topics = "".join(f'<span class="tag tag-cat">{_esc(_t)}</span>' for _t in _ph.get("topics", []))
        st.markdown(
            f'<div class="ocard"><div class="ocard-title">{_esc(_ph.get("name"))} '
            f'<span style="color:#10B981;font-size:.72rem;font-weight:600">· {_esc(_ph.get("duration"))}</span></div>'
            f'<div class="ocard-org" style="margin-bottom:9px">{_esc(_ph.get("focus"))}</div>'
            f'<div class="ocard-tags">{_topics}</div></div>', unsafe_allow_html=True)

    if plan.get("high_priority_topics"):
        st.markdown('<div class="profile-section-title" style="margin-top:14px">🔥 High-Priority Topics</div>',
                    unsafe_allow_html=True)
        st.markdown('<div class="ocard-tags" style="margin-bottom:8px">'
                    + "".join(f'<span class="tag tag-warn">{_esc(_t)}</span>'
                              for _t in plan["high_priority_topics"]) + '</div>',
                    unsafe_allow_html=True)

    _cc1, _cc2 = st.columns(2)
    with _cc1:
        if plan.get("daily_routine"):
            st.markdown("**🕒 Suggested Daily Routine**")
            for _x in plan["daily_routine"]:
                st.caption("• " + str(_x))
        if plan.get("tips"):
            st.markdown("**💡 Tips**")
            for _x in plan["tips"]:
                st.caption("• " + str(_x))
    with _cc2:
        if plan.get("free_resources"):
            st.markdown("**📚 Free Resources to Use**")
            for _x in plan["free_resources"]:
                st.caption("• " + str(_x))

    st.markdown(
        '<div style="background:rgba(245,158,11,.06);border:1px solid rgba(245,158,11,.25);'
        'border-radius:10px;padding:10px 14px;margin-top:12px;font-size:.74rem;color:#F59E0B;line-height:1.6">'
        '⚠ <b>Suggested study plan — guidance only.</b> This is an Opporta Intelligence (automated) suggestion, '
        'not official, not affiliated with any commission, and not a guarantee of syllabus coverage, '
        'difficulty or results. Always confirm the official syllabus, exam pattern and dates on the '
        'recruitment authority’s portal before relying on it.</div>', unsafe_allow_html=True)

def ring_cls(s) -> str:
    try: s = int(s)
    except: return "ring-lo"
    return "ring-hi" if s >= 75 else "ring-md" if s >= 50 else "ring-lo"

def _v(val, fallback="—") -> str:
    if val is None: return fallback
    try:
        if val != val: return fallback
    except Exception: pass
    s = str(val).strip()
    return s if s and s.lower() not in ("nan","none","nat","") else fallback

def safe_str(text, length=90) -> str:
    """Truncate any value to a display string — never raises.

    `text` is cast through _v() (None / NaN -> 'Untitled'). `length` is
    coerced to a positive int so a stray non-int (e.g. a fallback string
    accidentally passed in this slot) degrades to the default instead of
    crashing the whole page with a TypeError on Streamlit Cloud.
    """
    t = _v(text, "Untitled")
    try:
        length = int(length)
        if length <= 0:
            length = 90
    except (TypeError, ValueError):
        length = 90
    return t[:length] + ("..." if len(t) > length else "")

import re as _re, html as _html
def _esc(val, fallback="—") -> str:
    """Return HTML-escaped version of _v() — safe to embed in HTML templates."""
    return _html.escape(_v(val, fallback))


# ── Bid Workshop helpers ──────────────────────────────────────────────────────
# Physical / legal documents that genuinely cannot be auto-compiled and must be
# arranged by the contractor. Surfaced as a manual checklist in the workshop.
_MANUAL_BID_TASKS = [
    ("Non-blacklisting Affidavit (₹100 stamp paper, notarized)",
     "Sworn affidavit that your firm isn't blacklisted by any govt body. Must be on "
     "judicial stamp paper and notarized — cannot be produced digitally."),
    ("Bank Solvency Certificate",
     "Issued by your banker on letterhead certifying solvency for the tender value. "
     "Request it from your branch."),
    ("CA-Audited Net-Worth Certificate (with UDIN)",
     "Latest net-worth / turnover certificate signed by a Chartered Accountant, "
     "carrying a valid UDIN for online verification."),
    ("EMD — Demand Draft / Bank Guarantee / FDR",
     "Earnest Money Deposit in the exact instrument and amount the tender specifies, "
     "in favour of the named authority."),
    ("Class-3 Digital Signature Certificate (DSC)",
     "Needed to sign & upload the bid on the e-procurement portal. Must be valid "
     "(not expired) on submission day."),
    ("Sealed hard-copy set (if offline submission)",
     "Some tenders still need a physical sealed set in the tender box — check the "
     "NIT's submission mode."),
]


def _compose_cover_letter(cl: dict, tender: dict, profile: dict) -> str:
    """Flatten the generated cover-letter JSON into editable plain text."""
    cl = cl or {}
    cname = _v(profile.get("company_name") or profile.get("full_name"), "Our Firm")
    out = [_v(cl.get("to"), f"To,\nThe Tender Committee,\n{_v(tender.get('organization'))}"), ""]
    if _v(cl.get("subject"), "") != "":
        out.append(_v(cl.get("subject")))
    if _v(cl.get("ref"), "") != "":
        out.append(_v(cl.get("ref")))
    out += ["", _v(cl.get("salutation"), "Respected Sir/Madam,"), ""]
    for para in (cl.get("body_paragraphs") or []):
        p = _v(para, "")
        if p and p != "—":
            out += [p, ""]
    if _v(cl.get("closing"), "") != "":
        out += [_v(cl.get("closing")), ""]
    out += ["Yours faithfully,", f"\nFor {cname}\nAuthorized Signatory"]
    return "\n".join(out).strip()


def _compliance_csv(bid, elig) -> bytes:
    """Compliance / deviation spreadsheet from the gate + intelligence matrix."""
    import csv as _csv, io as _io2
    buf = _io2.StringIO()
    w = _csv.writer(buf)
    w.writerow(["Requirement", "Our Response / Status", "Compliance"])
    for c in (elig or {}).get("checks", []):
        ok = c.get("ok")
        status = "Compliant" if ok is True else "Deviation" if ok is False else "To verify"
        w.writerow([_v(c.get("label")), _v(c.get("detail")), status])
    if isinstance(bid, dict):
        for m in (bid.get("compliance_matrix") or []):
            w.writerow([_v(m.get("requirement")), _v(m.get("our_response")),
                        _v(m.get("status"), "Compliant")])
    return buf.getvalue().encode("utf-8-sig")   # BOM so Excel opens it cleanly


def _render_bid_workshop(*, standalone: bool = False) -> None:
    """Ready-to-Bid generator: upload tender + firm docs -> eligibility verdict,
    editable cover letter, compliance sheet, .docx and a manual-actions checklist.
    Uses module globals (profile, email, _token)."""
    st.markdown("""<div class="sec-hd">
      <span class="sec-title">🧠 Opporta Bid Workspace</span>
      <span class="sec-badge-green">Ready-to-Bid File Generator</span>
      <div class="sec-divider"></div>
    </div>""", unsafe_allow_html=True)

    with st.expander("⚡  Build a Ready-to-Bid package — tender + firm documents",
                     expanded=standalone):
        _ws_ai = bool(
            os.getenv("GEMINI_API_KEY") or _secret("GEMINI_API_KEY") or
            os.getenv("ANTHROPIC_API_KEY") or _secret("ANTHROPIC_API_KEY"))
        if not _ws_ai:
            st.warning("Opporta Intelligence document generation is temporarily unavailable. You can still review tender details and your saved documents.")

        _upload_panel, _readiness_panel = st.columns([1.1, .9], gap="large")
        with _upload_panel:
            st.markdown('<div class="profile-section-title">01 · Source documents</div>',
                        unsafe_allow_html=True)
            st.markdown("**Tender document** · NIT / tender notice")
            _ws_tender = st.file_uploader(
                "Tender document", type=["pdf", "jpg", "jpeg", "png"],
                key="ws_tender_doc", label_visibility="collapsed")
            st.markdown("**Firm documents** · GST, registration, experience, turnover")
            _ws_firm = st.file_uploader(
                "Firm documents", type=["pdf", "txt", "jpg", "jpeg", "png"],
                accept_multiple_files=True, key="ws_firm_docs",
                label_visibility="collapsed")
        with _readiness_panel:
            st.markdown('<div class="profile-section-title">02 · Readiness output</div>',
                        unsafe_allow_html=True)
            st.markdown(
                '<div class="res-panel" style="margin-top:0">'
                '<div class="terminal-label">Deterministic eligibility gate</div>'
                '<div class="res-verdict">Your profile and Vault documents are checked against '
                'the tender. The workspace then returns blockers, missing-document checks, an '
                'editable cover letter, compliance sheet and bid draft.</div></div>',
                unsafe_allow_html=True)

        _wlang = st.session_state.get("lang", "en")
        st.markdown(f"**03 · {i18n.t('bid_language', _wlang)}**")
        _ws_lang_lbl = st.radio(i18n.t("bid_language", _wlang), ["English", "हिंदी"],
                                index=(1 if _wlang == "hi" else 0), horizontal=True,
                                key="ws_bid_lang", label_visibility="collapsed")
        _ws_lang = "hi" if _ws_lang_lbl == "हिंदी" else "en"

        if st.button("⚡  Generate Ready-to-Bid File", width="stretch", key="ws_generate"):
            if not _ws_tender:
                st.warning("Upload the tender document first.")
            elif not _ws_ai:
                st.error("Opporta Intelligence could not start document generation. Please try again later.")
            else:
                import bid_engine, vault_evaluator as _ve
                _ws_firm_texts: list[str] = []
                for _ff in (_ws_firm or []):
                    try:
                        _txt = (_read_pdf_text(_ff) if _ff.name.lower().endswith(".pdf")
                                else _ff.read().decode("utf-8", errors="ignore"))
                        if _txt.strip():
                            _ws_firm_texts.append(_txt)
                    except Exception:
                        pass
                core.clear_ai_error()
                with st.spinner("Opporta Intelligence is reading the tender, checking your eligibility & drafting the bid…"):
                    _ws_t   = bid_engine.extract_tender(_ws_tender.read(),
                                                        _ws_tender.type or "application/pdf")
                    _ws_chk = bid_engine.readiness_check(_ws_t, profile, _ws_firm_texts)
                    _ws_bid = bid_engine.generate_bid_content(_ws_t, profile, _ws_firm_texts,
                                                              language=_ws_lang)
                    _ws_docx = bid_engine.build_docx(_ws_bid, _ws_t, profile,
                                                     language=_ws_lang) if _ws_bid else None

                if _ws_t.get("_extraction_failed"):
                    st.session_state.pop("ws_result", None)
                    if core.ai_error_message():
                        _render_ai_error()
                    else:
                        st.error("Could not read the tender document automatically. Try a clearer PDF.")
                else:
                    _vault_docs = _cached_vault_docs(email, _token) if email else []
                    _elig = _ve.evaluate(_ws_t, profile, _vault_docs)
                    _slug = safe_str(_ws_t.get('tender_no') or _ws_t.get('title') or 'tender', 30)
                    _slug = _re.sub(r'[^A-Za-z0-9]+', '_', _slug).strip('_') or 'tender'
                    _cl   = _ws_bid.get("cover_letter", {}) if isinstance(_ws_bid, dict) else {}
                    st.session_state["ws_result"] = {
                        "title":    safe_str(_ws_t.get("title"), 90),
                        "slug":     _slug,
                        "elig":     _elig,
                        "vault_n":  len(_vault_docs),
                        "cover":    _compose_cover_letter(_cl, _ws_t, profile),
                        "csv":      _compliance_csv(_ws_bid, _elig),
                        "docx":     _ws_docx,
                        "warnings": [w for w in (_ws_chk.get("warnings") or []) if "deadline" in w.lower()][:2],
                        "no_docx":  _ws_docx is None,
                    }

        _wr = st.session_state.get("ws_result")
        if _wr:
            import vault_evaluator as _ve
            st.divider()
            st.success(f"✓ Bid package ready for: {_wr['title']}")
            _verd = _wr["elig"]["verdict"]
            _vc   = ("yes" if _verd == _ve.ELIGIBLE
                     else "no" if _verd == _ve.NOT_ELIGIBLE else "partial")
            _vi   = {"yes": "✅", "no": "⛔", "partial": "🔎"}[_vc]
            st.markdown(
                f'<div class="elig-{_vc}" style="margin:6px 0 4px;font-size:.95rem;'
                f'padding:12px 20px">{_vi}&nbsp; {_verd} &nbsp;·&nbsp; '
                f'{_html.escape(_wr["elig"]["summary"])}</div>', unsafe_allow_html=True)
            st.caption(
                f"Checked against your profile + {_wr['vault_n']} vault document(s). "
                "Always confirm against the official tender PDF before bidding.")
            for _b in _wr["elig"].get("blockers", [])[:3]:
                st.caption(f"⛔ {_b}")
            if _wr["elig"].get("missing_docs"):
                st.caption("📎 Not in your vault: " + ", ".join(_wr["elig"]["missing_docs"]))
            for _w in _wr.get("warnings", []):
                st.caption(f"⏳ {_w}")

            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
            _colA, _colB = st.columns(2)
            with _colA:
                st.markdown('<div class="profile-section-title">📦 Auto-Generated Package</div>', unsafe_allow_html=True)
                st.caption("Ready to copy / download for the online submission.")
                _ck = f"ws_cover_{_wr['slug']}"
                if _ck not in st.session_state:
                    st.session_state[_ck] = _wr["cover"]
                st.text_area("Technical cover letter (editable)", key=_ck, height=230)
                st.download_button(
                    "📊  Compliance / Deviation sheet (.csv)",
                    data=_wr["csv"], file_name=f"OPPORTA_Compliance_{_wr['slug']}.csv",
                    mime="text/csv", width="stretch", key="ws_csv")
                if not _wr["no_docx"]:
                    st.download_button(
                        "📄  Full Bid Document (.docx)",
                        data=_wr["docx"], file_name=f"OPPORTA_Bid_{_wr['slug']}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        width="stretch", key="ws_download")
                else:
                    st.info("Full .docx draft unavailable — the cover letter + compliance "
                            "sheet above are still ready to use.")
            with _colB:
                st.markdown('<div class="profile-section-title">✍️ Manual Actions Required</div>', unsafe_allow_html=True)
                st.caption("Physical / legal papers you must arrange yourself — tick as you go:")
                _done = 0
                for _i, (_lbl, _hint) in enumerate(_MANUAL_BID_TASKS):
                    if st.checkbox(_lbl, key=f"ws_manual_{_i}", help=_hint):
                        _done += 1
                _all = len(_MANUAL_BID_TASKS)
                st.markdown(
                    f'<div class="elig-{"yes" if _done == _all else "partial"}" '
                    f'style="margin-top:10px">{_done}/{_all} manual items ready</div>',
                    unsafe_allow_html=True)


def _plain(val) -> str:
    """Strip HTML tags from scraped text so st.write() doesn't show raw markup."""
    s = _v(val, "")
    return _re.sub(r"<[^>]+>", " ", s).strip()

def score_color(pct: int) -> str:
    return "#10B981" if pct >= 70 else "#F59E0B" if pct >= 40 else "#EF4444"

def _read_pdf_text(file) -> str:
    try:
        import pdfplumber
        with pdfplumber.open(file) as pdf:
            return " ".join(p.extract_text() or "" for p in pdf.pages)
    except Exception:
        return ""

def _pdf_widget(doc_url: str, source_id: str, compact: bool = False, ctx: str = ""):
    """Outbound link routing — opens the official source in a new browser tab.

    The old in-app fetch/parse/download proxy was removed: many government
    portals block server-side fetches or serve session-bound links, which led
    to broken downloads. We now always route the user to the authoritative
    source via st.link_button (opens in a new tab), so links never break.
    """
    if not doc_url or str(doc_url) in ("nan", "None", "—", ""):
        return
    st.link_button(
        "🌐 Open Official Procurement Portal",
        url=str(doc_url),
        width=("stretch" if not compact else "content"),
    )

def _districts_for_state(state: str) -> list[str]:
    return STATE_DISTRICTS.get(state, CG_DISTRICTS + UP_DISTRICTS)

# ── LOAD DATA ─────────────────────────────────────────────────────────────────
df_t = load_table("tenders")
df_j = load_table("jobs")

# Fold the 45+ raw scraped categories into ~10 clean buckets (core.normalize_category)
# and use those everywhere — filters, chips, the Profile sector picker, scoring —
# so the vocabulary is consistent and every option returns results.
if not df_t.empty and "category" in df_t:
    # Classify on title + organisation + category so police / collectorate /
    # printing work surfaces as its own sector (it never shows in 'category').
    df_t["category_bucket"] = df_t.apply(
        lambda r: core.classify_sector(r.get("title"), r.get("organization"), r.get("category")),
        axis=1)
    TENDER_CATS_BY_FREQ = df_t["category_bucket"].value_counts().index.tolist()
else:
    TENDER_CATS_BY_FREQ = list(core.CATEGORY_BUCKETS)

_CAT_EMOJI = {
    "Civil & Construction": "🏗️", "Water & Irrigation": "💧",
    "Electrical & Energy": "💡", "Medical & Healthcare": "🏥",
    "IT & Technology": "💻", "Transport & Logistics": "🚛",
    "Manufacturing & Goods": "🏭", "Municipal Projects": "🏙️",
    "Consultancy & Survey": "📐", "Miscellaneous": "📋",
}
def _emoji_for(cat: str) -> str:
    return _CAT_EMOJI.get(cat, "📋")

def _rec_key(prefix: str, rec: dict) -> str:
    """Stable, collision-safe Streamlit widget key for a tender/job row.

    source_id is the unique upsert key (NOT NULL in the DB), but scraped rows can
    occasionally arrive with a missing/NaN id; falling back to a hash of the
    identifying fields keeps widget keys unique so the page never crashes."""
    sid = rec.get("source_id")
    if sid is None or str(sid).strip().lower() in ("", "nan", "none", "nat"):
        sid = abs(hash((rec.get("title"), rec.get("organization"), rec.get("deadline"))))
    return f"{prefix}_{sid}"

# ── OFFICIAL GOVERNMENT DATA SOURCE NETWORK ───────────────────────────────────
# Authoritative fallback / direct-routing directory. All links open in a new tab
# via st.link_button. Grouped by region so they stay clean and never collide
# with the dynamic filtering above them.
PROCUREMENT_PORTALS = {
    "National": [
        ("🏛 Central Public Procurement (CPPP)", "https://eprocure.gov.in"),
        ("🛒 Government e-Marketplace (GeM)",     "https://gem.gov.in"),
    ],
    "Uttar Pradesh Network": [
        ("UP e-Procurement Portal",        "https://etender.up.nic.in"),
        ("UP Government Tenders Archive",  "http://tenders.up.nic.in"),
    ],
    "Chhattisgarh Network": [
        ("CG Integrated e-Procurement",    "https://eproc.cgstate.gov.in"),
        ("CG Government Tenders Portal",    "http://tenders.cg.gov.in"),
        ("CG Public Works Dept (PWD)",     "https://pwd.cg.nic.in"),
    ],
}

RECRUITMENT_AUTHORITIES = {
    "Uttar Pradesh Network": [
        ("UPPSC — Public Service Commission", "https://uppsc.up.nic.in"),
        ("UPSSSC — Subordinate Services",     "http://upsssc.gov.in"),
        ("UPPRPB — Police Recruitment",       "https://www.upprpb.in"),
        ("UP Basic Education Board",          "http://upbasiceduboard.gov.in"),
    ],
    "Chhattisgarh Network": [
        ("CGPSC — Public Service Commission", "https://psc.cg.gov.in"),
        ("CGPSC — Alternative Portal",        "https://ecgpsc.cgstate.gov.in"),
        ("CG Vyapam Board",                   "https://vyapam.cgstate.gov.in"),
        ("CG Employment Exchange (Rojgar)",   "https://erojgar.cg.gov.in"),
        ("CG Police Headquarters",            "https://cgpolice.gov.in"),
        ("CG Directorate of Medical Education","https://cgdme.in"),
    ],
}

# Free, official study material — verified live government / education platforms.
# (Exam-specific syllabi & previous papers live on each authority's own portal
#  above; these are the free prep resources to actually study from.)
STUDY_RESOURCES = {
    "Free Learning Platforms": [
        ("📘 SWAYAM — Free Govt Courses",        "https://swayam.gov.in"),
        ("🎓 NPTEL — Engineering & Science",      "https://nptel.ac.in"),
        ("📗 NCERT — Free Textbooks",             "https://ncert.nic.in"),
        ("📚 National Digital Library",           "https://ndl.iitkgp.ac.in"),
    ],
    "Current Affairs & General Knowledge": [
        ("📰 PIB — Govt Press / Current Affairs", "https://pib.gov.in"),
        ("🗞 Yojana / Kurukshetra (Publications)", "https://www.publicationsdivision.nic.in"),
        ("🏛 Chhattisgarh State Portal (CG GK)",  "https://cgstate.gov.in"),
        ("🏛 Uttar Pradesh State Portal (UP GK)", "https://up.gov.in"),
    ],
}

def _portal_region(title: str, subtitle: str, items: list, cols: int = 2) -> None:
    """Render one titled regional block of official-portal link buttons."""
    st.markdown(
        f'<div class="portal-region"><span class="portal-region-dot"></span>'
        f'<span class="portal-region-title">{title}</span>'
        f'<span class="portal-region-sub">{subtitle}</span></div>',
        unsafe_allow_html=True)
    _cols = st.columns(cols)
    for _i, (_label, _url) in enumerate(items):
        _cols[_i % cols].link_button(_label, _url, width="stretch")


def _source_health_snapshot(tenders: pd.DataFrame, jobs: pd.DataFrame) -> dict:
    """Load the last persisted ingest report; derive an honest CSV snapshot when
    an older pipeline has not written one yet. No source status is invented."""
    report_path = Path(__file__).parent / "data" / "source_health.json"
    if report_path.exists():
        try:
            payload = json.loads(report_path.read_text(encoding="utf-8"))
            if isinstance(payload, dict) and isinstance(payload.get("sources"), list):
                return payload
        except (OSError, ValueError, TypeError):
            pass

    frames = []
    for frame, kind in ((tenders, "Tender"), (jobs, "Job")):
        if not frame.empty and "source_portal" in frame:
            counts = frame["source_portal"].fillna("Unspecified source").astype(str).value_counts()
            frames.extend({
                "source": str(source),
                "display_name": str(source),
                "kind": kind,
                "record_count": int(count),
                "status": "snapshot",
                "error": None,
            } for source, count in counts.items())

    mtimes = []
    for filename in ("tenders.csv", "jobs.csv"):
        path = Path(__file__).parent / "data" / filename
        if path.exists():
            mtimes.append(path.stat().st_mtime)
    generated = (datetime.fromtimestamp(max(mtimes)).astimezone().isoformat()
                 if mtimes else None)
    return {
        "generated_at": generated,
        "mode": "csv_snapshot",
        "sources": frames,
        "note": ("Pipeline health telemetry has not been written yet. Counts below "
                 "are derived from the current persisted dataset."),
    }


def render_source_health(tenders: pd.DataFrame, jobs: pd.DataFrame,
                         *, compact: bool = False) -> None:
    """Render actual ingest telemetry without probing scrapers from the UI."""
    snapshot = _source_health_snapshot(tenders, jobs)
    sources = snapshot.get("sources") or []
    ok_n = sum(1 for item in sources
               if str(item.get("status", "")).lower() in ("healthy", "ok", "snapshot"))
    warn_n = sum(1 for item in sources
                 if str(item.get("status", "")).lower() in ("warning", "no_records"))
    fail_n = sum(1 for item in sources
                 if str(item.get("status", "")).lower() in ("failed", "error"))
    total_n = sum(int(item.get("record_count") or item.get("count") or 0)
                  for item in sources)
    generated = str(snapshot.get("generated_at") or "Not reported")
    generated_short = generated.replace("T", " ")[:19]

    if compact:
        st.markdown(
            f'<div class="health-strip"><span class="live-dot"></span>'
            f'<span class="health-stat"><b>{ok_n}</b> reporting sources</span>'
            f'<span class="health-stat"><b>{total_n:,}</b> source records</span>'
            f'<span class="health-stat"><b>{fail_n}</b> failures</span>'
            f'<span class="health-stat">Last ingest · {generated_short}</span>'
            f'<span class="health-link">Source health →</span></div>',
            unsafe_allow_html=True)
        return

    st.markdown(
        '<div class="page-kicker">Operations · Ingestion observability</div>'
        '<div class="page-title">Source Health Dashboard</div>'
        '<div class="page-sub">The last pipeline report for every tender and job source. '
        'This page reads persisted telemetry and never launches scrapers from a user session.</div>',
        unsafe_allow_html=True)
    h1, h2, h3, h4 = st.columns(4)
    h1.metric("Reporting sources", len(sources))
    h2.metric("Healthy / available", ok_n)
    h3.metric("Needs attention", warn_n + fail_n)
    h4.metric("Records reported", f"{total_n:,}")
    st.caption(f"Last pipeline report: {generated_short}")
    if snapshot.get("note"):
        st.info(snapshot["note"])
    if not sources:
        st.warning("No administrator telemetry is available.")
        return

    for item in sources:
        status = str(item.get("status") or "unknown").lower()
        status_class = ("status-ok" if status in ("healthy", "ok", "snapshot")
                        else "status-fail" if status in ("failed", "error")
                        else "status-warn")
        label = str(item.get("display_name") or item.get("source") or "Unnamed source")
        kind = str(item.get("kind") or "Tender / Job")
        count = int(item.get("record_count") or item.get("count") or 0)
        error = str(item.get("error") or "")
        error_html = (f'<div class="source-meta" style="color:#F87171">{_html.escape(error)}</div>'
                      if error else "")
        st.markdown(
            f'<div class="source-card"><div class="source-row">'
            f'<div><div class="source-name">{_html.escape(label)}</div>'
            f'<div class="source-meta">{_html.escape(kind)} source</div>{error_html}</div>'
            f'<div class="source-last"><div class="source-meta">Last run</div>'
            f'<div class="source-count">{_html.escape(generated_short)}</div></div>'
            f'<div><div class="source-meta">Records</div><div class="source-count">{count:,}</div></div>'
            f'<div><span class="status-pill {status_class}">{_html.escape(status.replace("_", " "))}</span></div>'
            f'</div></div>',
            unsafe_allow_html=True)


def render_job_intelligence(jobs: pd.DataFrame) -> None:
    """Job-only resume matching. Tender and bid controls never appear here."""
    st.markdown(
        '<div class="terminal-hd"><div class="terminal-label">OPPORTA JOB INTELLIGENCE</div>'
        '<div class="terminal-title">Resume Match & Eligibility Review</div>'
        '<div class="terminal-sub">Compare your experience, education and skills with one '
        'government job notification. Results are guidance, not a selection guarantee.</div></div>',
        unsafe_allow_html=True)
    if jobs.empty:
        st.info("No active job notifications are available right now.")
        return

    _jq = st.text_input(
        "Find a job notification",
        placeholder="Search title, department, qualification or state…",
        key="job_intel_search")
    _search = _jq.strip().lower()
    _filtered = jobs
    if _search:
        _mask = jobs.apply(
            lambda row: _search in (
                f"{row.get('title','')} {row.get('department','')} "
                f"{row.get('qualification','')} {row.get('state','')}"
            ).lower(),
            axis=1)
        _filtered = jobs[_mask]
    if _filtered.empty:
        st.warning("No job notification matches that search.")
        return

    _records = _filtered.reset_index(drop=True)
    _pick = st.selectbox(
        "Select job notification", range(len(_records)),
        format_func=lambda idx: safe_str(_records.iloc[idx].get("title"), 100),
        key="job_intel_pick")
    _job = _records.iloc[_pick].to_dict()
    st.markdown(
        f'<div class="jcard"><div class="jcard-title">{_esc(_job.get("title"))}</div>'
        f'<div class="jcard-dept">{_esc(_job.get("department"))} · '
        f'{_esc(_job.get("state"))}</div><div class="ocard-tags">'
        f'<span class="tag tag-cat">{_esc(_job.get("category"), "General")}</span>'
        f'<span class="tag tag-dl">Deadline · {_esc(_job.get("deadline"))}</span>'
        f'</div></div>',
        unsafe_allow_html=True)

    _profile_resume = _profile_to_resume_text(profile)
    _resume_file = st.file_uploader(
        "Upload resume for a deeper match (PDF or TXT)",
        type=["pdf", "txt"], key="job_intel_resume")
    _resume_text = _profile_resume
    if _resume_file:
        _resume_text = (_read_pdf_text(_resume_file)
                        if _resume_file.name.lower().endswith(".pdf")
                        else _resume_file.read().decode("utf-8", errors="ignore"))
        st.caption(f"Resume ready · {len(_resume_text):,} characters read")
    elif _has_job_profile(profile):
        st.caption("Using your saved Job Seeker Profile. Upload a resume for a deeper review.")
    else:
        st.info("Complete your Job Seeker Profile or upload a resume to begin.")

    if st.button("⚡ Check My Job Match", width="stretch", key="job_intel_analyze"):
        if not _resume_text.strip():
            st.warning("Add your Job Seeker Profile or upload a resume first.")
        else:
            with st.spinner("Opporta Intelligence is comparing your profile with the notification…"):
                _result = evaluator.evaluate_resume_for_job(_job, _resume_text)
            _pct = int(_result.get("readiness_pct") or 0)
            _color = score_color(_pct)
            st.markdown(
                f'<div class="res-panel"><div style="display:flex;align-items:center;gap:24px">'
                f'<div><div class="res-score" style="color:{_color}">{_pct}%</div>'
                f'<div class="res-label">Job Match</div></div>'
                f'<div class="res-verdict">{_esc(_result.get("verdict"))}</div>'
                f'</div></div>',
                unsafe_allow_html=True)
            _r1, _r2, _r3 = st.columns(3)
            with _r1:
                st.success("Matched")
                for _item in (_result.get("met") or []):
                    st.caption(f"• {_item}")
            with _r2:
                st.error("Missing")
                for _item in (_result.get("missing") or []):
                    st.caption(f"• {_item}")
            with _r3:
                st.warning("Verify")
                for _item in (_result.get("unknown") or []):
                    st.caption(f"• {_item}")

# ── LOCALSTORAGE SESSION LOCK ─────────────────────────────────────────────────
# When authenticated, mirror the session credentials into browser localStorage so
# they survive a server-side session drop (the SESSION BOOTSTRAP block near the
# top reads them back via streamlit-js-eval on the next fresh load). Also strip
# any leftover OAuth #access_token from the URL — history.replaceState is allowed
# in the iframe sandbox (it's not navigation), so the token never lingers.
def _sync_session_storage() -> None:
    if st.session_state.authenticated:
        _stc.html(
            "<script>try{"
            f"localStorage.setItem('_op_e',{json.dumps(st.session_state.email)});"
            f"localStorage.setItem('_op_t',{json.dumps(st.session_state.get('sb_token',''))});"
            f"localStorage.setItem('_op_r',{json.dumps(st.session_state.get('sb_refresh',''))});"
            "var w=(window.parent!==window)?window.parent:window;"
            "if(w.location.hash.indexOf('access_token=')>=0){"
            "w.history.replaceState({},'',w.location.pathname+w.location.search);}"
            "}catch(x){}</script>",
            height=0)

# ── PASSWORD-RESET SCREEN ────────────────────────────────────────────────────
# Shown when the user arrives from a Supabase password-reset email link
# (type=recovery, captured by the OAuth fragment handler above → _pwreset flag).
# We collect a new password, set it via the recovery token, then send the user
# back to a normal login. Gated with st.stop() so nothing else renders meanwhile.
if st.session_state.get("show_pw_reset"):
    _rlang = st.session_state.get("lang", "en")
    _rlogo = (f'<img src="{_LOGO_URI}" style="width:64px;height:64px;display:block;'
              f'margin:0 auto 14px;border-radius:14px">' if _LOGO_URI else '')
    st.markdown(
        f'<div style="max-width:460px;margin:6vh auto 0;text-align:center">{_rlogo}'
        f'<h2 style="color:#F1F5F9;margin-bottom:18px">{i18n.t("set_new_password", _rlang)}</h2>'
        f'</div>', unsafe_allow_html=True)
    _rc = st.columns([1, 2, 1])[1]
    with _rc:
        _np1 = st.text_input(i18n.t("new_password", _rlang), type="password", key="pwr_np1")
        _np2 = st.text_input(i18n.t("confirm_password", _rlang), type="password", key="pwr_np2")
        if st.button(i18n.t("update_password", _rlang), width="stretch", key="pwr_btn"):
            if not _np1 or len(_np1) < 6:
                st.error(i18n.t("pw_min_len", _rlang))
            elif _np1 != _np2:
                st.error(i18n.t("passwords_no_match", _rlang))
            else:
                _ok, _msg = accounts.update_password(
                    _np1, st.session_state.get("pw_reset_token", ""),
                    st.session_state.get("pw_reset_refresh", ""))
                if _ok:
                    st.session_state.show_pw_reset    = False
                    st.session_state.pw_reset_token   = ""
                    st.session_state.pw_reset_refresh = ""
                    st.success(_msg)
                    st.balloons()
                else:
                    st.error(_msg)
        if st.button(i18n.t("back_to_login", _rlang), key="pwr_cancel"):
            st.session_state.show_pw_reset    = False
            st.session_state.pw_reset_token   = ""
            st.session_state.pw_reset_refresh = ""
            st.rerun()
    st.stop()

_sync_session_storage()

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    _limg = f'<img src="{_LOGO_URI}" style="width:72px;height:72px;display:block;margin:0 auto 8px;border-radius:14px;box-shadow:0 0 24px rgba(0,196,255,.35)">' if _LOGO_URI else ''
    st.markdown(f"""
    <div class="sb-logo" style="text-align:center;padding:16px 16px 14px">
      {_limg}
      <div class="sb-brand"><span>Opporta</span></div>
      <div class="sb-tagline">Every Opportunity · One Platform</div>
    </div>""", unsafe_allow_html=True)

    # Language is controlled by the single prominent "English | हिंदी" switch at the
    # top of the page (one source of truth: st.session_state.lang). Here we only
    # READ it for the sidebar nav labels — writing it here too would fight the top
    # switch on every rerun and snap the choice back.
    lang = st.session_state.get("lang", "en")

    if not st.session_state.authenticated:
        st.markdown('<div class="auth-panel">', unsafe_allow_html=True)
        st.markdown('<div class="auth-label">Secure Sign In</div>', unsafe_allow_html=True)
        _google_signin_button(lang, key="g_signin_sidebar")
        st.markdown(
            f"<div style='text-align:center;color:#64748B;font-size:.7rem;margin:8px 0'>— {i18n.t('or', lang)} —</div>",
            unsafe_allow_html=True)
        auth_email = st.text_input("Email", key="auth_e",
                                   label_visibility="collapsed",
                                   placeholder="contractor@firm.com")
        auth_pw = st.text_input("Password", type="password", key="auth_pw",
                                label_visibility="collapsed",
                                placeholder="Password")
        c1, c2 = st.columns(2)
        if c1.button("Login", width="stretch"):
            ok, msg, token, refresh = accounts.login_user(auth_email, auth_pw)
            if ok:
                st.session_state.authenticated = True
                st.session_state.email    = auth_email.strip().lower()
                st.session_state.sb_token = token or ""
                st.session_state.sb_refresh = refresh or ""
                st.session_state.current_page = "🏠  Dashboard"
                st.rerun()
            elif msg in ("EMAIL_NOT_CONFIRMED", "RATE_LIMIT"):
                st.warning("📧 Please confirm your email (check inbox/spam), then log in — or wait a moment and retry.")
            else:
                st.error(msg)
        _forgot_password_ui(lang, "sb")
        if c2.button("Register", width="stretch"):
            ok, msg = accounts.register_user(auth_email, auth_pw)
            if ok:
                lok, _lm, token, refresh = accounts.login_user(auth_email, auth_pw)
                if lok:
                    st.session_state.authenticated = True
                    st.session_state.email    = auth_email.strip().lower()
                    st.session_state.sb_token = token or ""
                    st.session_state.sb_refresh = refresh or ""
                    st.session_state.current_page = "🏠  Dashboard"
                    st.rerun()
                else:
                    st.success("✅ Account created — click Login.")
            elif msg == "ALREADY_EXISTS":
                st.info("Already registered — click Login.")
            elif msg == "RATE_LIMIT":
                st.warning("⏳ Email server busy — please wait a minute and try again.")
            else:
                st.error(msg)
        st.caption("Tip: signup is instant — no verification code needed.")
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        _nav_group = None
        for _group, _en, _hi, _route in NAV_ITEMS:
            if _group != _nav_group:
                st.markdown(f'<div class="sb-nav-label">{_group}</div>', unsafe_allow_html=True)
                _nav_group = _group
            _active = st.session_state.current_page == _route
            if st.button(_nav_text((_group, _en, _hi, _route), lang),
                         key=f"nav_{_route}", width="stretch",
                         type="primary" if _active else "secondary"):
                st.session_state.current_page = _route
                st.rerun()

        st.markdown(f"""
        <div class="session-badge">
          <div class="session-live"><span class="live-dot"></span>SECURE SESSION</div>
          <div class="session-email">{st.session_state.email}</div>
        </div>""", unsafe_allow_html=True)

        if st.button("⏏  " + i18n.t("logout", lang), width="stretch"):
            st.session_state.authenticated    = False
            st.session_state.email            = ""
            st.session_state.sb_token         = ""
            st.session_state.sb_refresh       = ""
            st.session_state.entered_platform = False
            st.session_state.auth_mode        = "login"
            st.session_state._ls_checked      = False
            _stc.html(
                "<script>try{"
                "localStorage.removeItem('_op_e');"
                "localStorage.removeItem('_op_t');"
                "localStorage.removeItem('_op_r');"
                "}catch(x){}</script>",
                height=0)
            st.rerun()

# ── GLOBAL CONTEXT ────────────────────────────────────────────────────────────
# These fetch the user's profile + vault count from Supabase. Without caching
# they fire on EVERY rerun (every click), adding 2 network round-trips of lag to
# every interaction. Cache per (email, token); invalidated explicitly on save.
email    = st.session_state.email
_token   = st.session_state.get("sb_token", "")

# NOTE: params must NOT start with "_" — Streamlit excludes underscore-prefixed
# args from the cache key, which would make every user share one cache entry
# (i.e. leak the first user's profile to everyone). These names are hashed.
@st.cache_data(ttl=300, show_spinner=False)
def _cached_profile(user_email: str, user_token: str):
    return accounts.get_profile(user_email, token=user_token)

@st.cache_data(ttl=300, show_spinner=False)
def _cached_vault_docs(user_email: str, user_token: str) -> list:
    try:
        return accounts.list_documents(user_email, token=user_token) or []
    except Exception:
        return []

@st.cache_data(ttl=300, show_spinner=False)
def _cached_vault_count(user_email: str, user_token: str) -> int:
    try:
        return len(_cached_vault_docs(user_email, user_token))
    except Exception:
        return 0

def _bust_user_cache():
    """Call after saving profile or uploading a document so reads refresh."""
    _cached_profile.clear()
    _cached_vault_docs.clear()
    _cached_vault_count.clear()

profile  = _cached_profile(email, _token) if email else dict(core.DEFAULT_PROFILE)
if profile is None:
    profile = dict(core.DEFAULT_PROFILE)
cname = (str(profile.get("company_name") or "").strip()
         or str(profile.get("full_name") or "").strip()
         or (email.split("@")[0].title() if email else "Guest"))

# ── PROFILE READINESS GATE ────────────────────────────────────────────────────
# The matching engine must never hallucinate a score against empty telemetry.
# We only compute personalized scores once the user has real profile data OR at
# least one document in the secure vault. Until then every match = 0 / empty.
_vault_count = _cached_vault_count(email, _token) if (st.session_state.authenticated and email) else 0
PROFILE_READY = (st.session_state.authenticated
                 and core.profile_is_configured(profile, _vault_count > 0))

def get_scored(df: pd.DataFrame, prof: dict) -> list:
    if df.empty: return []
    out = []
    for _, r in df.iterrows():
        rec = r.to_dict()
        if not core.state_match(rec, prof): continue
        s, reasons, eligible = core.score_tender_for_user(rec, prof)
        out.append((s, eligible, reasons, rec))
    return sorted(out, key=lambda x: (x[1], x[0]), reverse=True)

def compute_smart_alerts(email, token, scored_list, df_tenders) -> list[dict]:
    """Two mission-critical triggers only — no generic announcements.

    (1) Active pipeline tracking — saved tenders whose deadline is approaching.
    (2) Proactive matching — newly-surfaced tenders that clear the user's
        qualification bar (eligible & score >= 80) and aren't already tracked.
    """
    alerts: list[dict] = []
    try:
        saved = accounts.list_saved(email, token=token) if email else []
    except Exception:
        saved = []
    lookup = ({r["source_id"]: r for _, r in df_tenders.iterrows()}
              if not df_tenders.empty else {})
    saved_ids = set()

    for s in saved:
        sid = s.get("source_id", "")
        saved_ids.add(sid)
        rec = lookup.get(sid)
        if not rec:
            continue
        dl = days_left(rec.get("deadline"))
        if dl is not None and 0 <= dl <= 10:
            alerts.append({
                "icon": "⏰", "color": "#F87171" if dl <= 3 else "#F59E0B",
                "title": f"Deadline approaching — {safe_str(rec.get('title'), 68)}",
                "detail": f"Closes in {dl} day{'s' if dl != 1 else ''} · {_v(rec.get('organization'))}",
                "sort": (0, dl),
            })

    for s, eligible, reasons, rec in scored_list:
        if s >= 80 and eligible and rec.get("source_id") not in saved_ids:
            alerts.append({
                "icon": "🎯", "color": "#10B981",
                "title": f"New eligible tender — {safe_str(rec.get('title'), 62)}",
                "detail": (f"You meet this tender's criteria · {_v(rec.get('category'),'General')}"
                           f" · {_v(rec.get('district'),'State-wide')}"),
                "sort": (1, 100 - s),
            })

    alerts.sort(key=lambda a: a["sort"])
    return alerts

# No verified telemetry → no scores. This is the airtight default state.
# get_scored() is an O(n) Python loop over every tender; only run it on the
# pages that actually consume `scored` (Dashboard KPIs/matches + Alerts panel)
# instead of on every rerun of every page.
_cur_page = st.session_state.current_page
_scored_needed = (("Dashboard" in _cur_page) or ("Alerts" in _cur_page)
                  or ("Tenders" in _cur_page))   # Tenders now hosts the alert strip
scored          = get_scored(df_t, profile) if (PROFILE_READY and _scored_needed) else []
eligible_count  = sum(1 for _, e, _, _ in scored if e)
high_conf_count = sum(1 for s, _, _, _ in scored if s >= 80)
closing_soon    = sum(1 for _, _, _, r in scored
                      if (dl := days_left(r.get("deadline"))) is not None and 0 <= dl <= 7)
total_value     = df_t["value_lakhs"].fillna(0).sum() if not df_t.empty and "value_lakhs" in df_t else 0

page = st.session_state.current_page

# Redirect stale "Explore" page references to Tenders.
if st.session_state.authenticated and ("Explore" in page):
    st.session_state.current_page = "📄  Tenders"
    page = "📄  Tenders"

# Source diagnostics are an administrator concern, not a public product page.
# Redirect any stale session left over from older navigation versions.
if st.session_state.authenticated and ("Source Health" in page):
    st.session_state.current_page = "🏠  Dashboard"
    page = "🏠  Dashboard"

# ── UNIVERSAL ☰ MENU — jump to any section from phone OR web ──────────────────
# A single hamburger menu that works everywhere (popover on desktop & mobile),
# in addition to the sidebar (desktop) and bottom bar (phone).
if st.session_state.authenticated:
    _menu_lbl = "☰  " + i18n.t("nav_menu", lang)
    try:
        _hmenu = st.popover(_menu_lbl, use_container_width=False)
    except Exception:
        _hmenu = st.expander(_menu_lbl)
    with _hmenu:
        st.markdown(f"**{i18n.t('go_to', lang)}**")
        for _group, _en, _hi, _route in NAV_ITEMS:
            if st.button(_nav_text((_group, _en, _hi, _route), lang),
                         key=f"hm_{_route}", width="stretch",
                         type="primary" if st.session_state.current_page == _route else "secondary"):
                st.session_state.current_page = _route
                st.rerun()
        st.divider()
        if st.button("⏏  " + i18n.t("logout", lang), key="hm_logout", width="stretch"):
            st.session_state.authenticated    = False
            st.session_state.email            = ""
            st.session_state.sb_token         = ""
            st.session_state.sb_refresh       = ""
            st.session_state.entered_platform = False
            st.session_state.auth_mode        = "login"
            st.session_state._ls_checked      = False
            _stc.html(
                "<script>try{"
                "localStorage.removeItem('_op_e');"
                "localStorage.removeItem('_op_t');"
                "localStorage.removeItem('_op_r');"
                "}catch(x){}</script>",
                height=0)
            st.rerun()

# ── MOBILE BOTTOM TAB BAR (fixed, thumb-friendly — visible only on phones) ─────
# Scoped via st.container(key=…) → wrapper gets class .st-key-mobilenav, which we
# pin to the bottom of the viewport in CSS. Hidden on desktop (sidebar takes over).
if st.session_state.authenticated:
    _bottom_items = [
        ("👤", "Profile",   "👤  Profile"),
        ("📄", "Tenders",   "📄  Tenders"),
        ("💼", "Jobs",      "💼  Jobs"),
        ("🏠", "Home",      "🏠  Dashboard"),
        ("🔔", "Alerts",    "🔔  Alerts"),
    ]
    _bnav_keys = {"Home": "nav_home", "Profile": "nav_profile", "Tenders": "nav_tenders",
                  "Jobs": "nav_jobs", "Alerts": "Alerts"}
    _mnav = st.container(key="mobilenav")
    with _mnav:
        _mcols = st.columns(len(_bottom_items))
        for _col, (_icon, _lbl, _pg) in zip(_mcols, _bottom_items):
            _is_active = st.session_state.current_page == _pg
            _lbl_t = i18n.t(_bnav_keys.get(_lbl, _lbl), lang)
            # two trailing spaces + newline → markdown hard break → icon over label
            if _col.button(f"{_icon}  \n{_lbl_t}", key=f"bnav_{_pg}",
                           width="stretch",
                           type="primary" if _is_active else "secondary"):
                st.session_state.current_page = _pg
                st.rerun()

# ── PROMINENT LANGUAGE SWITCHER (top of every page; visible on mobile too) ────
# The sidebar toggle is hidden behind the hamburger on phones, so we also show a
# clear English | हिंदी switch at the top of the main area for everyone.
_lang_now = st.session_state.get("lang", "en")
with st.container(key="lang_switch_top"):
    _lsp, _len_btn, _lhi_btn = st.columns([6, 1.4, 1.4])
    with _len_btn:
        if st.button("English", key="lang_en_top", width="stretch",
                     type="primary" if _lang_now == "en" else "secondary"):
            st.session_state.lang = "en"
            st.rerun()
    with _lhi_btn:
        if st.button("हिंदी", key="lang_hi_top", width="stretch",
                     type="primary" if _lang_now == "hi" else "secondary"):
            st.session_state.lang = "hi"
            st.rerun()
lang = st.session_state.lang

# ══════════════════════════════════════════════════════════════════════════════
# ── DASHBOARD ─────────────────────────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════
if "Dashboard" in page:
    if not st.session_state.authenticated:
        # Keep the legacy state key for session compatibility, but show the
        # landing and secure sign-in together without an unnecessary first click.
        st.session_state.entered_platform = True

        # ── STEP 1: Hero landing — show intro + Enter button ──────────────────
        if not st.session_state.entered_platform:
            _hero_logo = f'<img src="{_LOGO_URI}" style="width:110px;height:110px;display:block;margin:0 auto 24px;border-radius:20px;box-shadow:0 0 48px rgba(0,196,255,.4),0 0 96px rgba(27,108,247,.2)">' if _LOGO_URI else ''
            st.markdown(f"""
            <div class="hero" style="padding:60px 20px 50px">
              {_hero_logo}
              <div class="hero-eyebrow">
                <span class="hero-pulse"></span>
                LIVE · Opporta Intelligence · CG + UP · Real-Time
              </div>
              <h1 class="hero-h1">Every Opportunity.<br><em>One Platform.</em></h1>
              <p class="hero-sub">
                India's most advanced government tender & job intelligence system
                for Chhattisgarh &amp; Uttar Pradesh. {len(df_t)} live tenders,
                {len(df_j)} open jobs — updated every morning.
              </p>
              <div class="hero-cta-row" style="margin-bottom:48px">
                <div class="hero-pill">📋 {len(df_t)} Active Tenders</div>
                <div class="hero-pill">💼 {len(df_j)} Open Jobs</div>
                <div class="hero-pill">🌏 CG &amp; UP Coverage</div>
                <div class="hero-pill">⚡ Daily Auto-Update</div>
              </div>
            </div>""", unsafe_allow_html=True)

            _ec, _spacer1, _spacer2 = st.columns([1,1,1])
            with _ec:
                if st.button("⚡  Enter Dashboard  →", width="stretch",
                             key="enter_platform"):
                    st.session_state.entered_platform = True
                    st.rerun()
            st.markdown("""
            <style>
            [data-testid="stMainBlockContainer"] div:has(> [data-testid="stButton"]) button[kind="secondary"]:first-child,
            div[data-testid="stBaseButton-secondary"]{
              background:linear-gradient(135deg,#00C4FF,#1B6CF7,#06B6D4)!important;
              border:none!important;color:#fff!important;font-size:1rem!important;
              font-weight:800!important;padding:18px 32px!important;border-radius:100px!important;
              animation:glow-pulse 2.5s ease-in-out infinite!important;
              letter-spacing:-.01em!important;
            }
            </style>""", unsafe_allow_html=True)

        # ── STEP 2: Auth card — Login / Register / OTP ────────────────────────
        else:
            _auth_logo = f'<img src="{_LOGO_URI}" style="width:80px;height:80px;display:block;margin:0 auto 16px;border-radius:14px;box-shadow:0 0 32px rgba(0,196,255,.35)">' if _LOGO_URI else ''
            st.markdown(f"""
            <div class="hero" style="padding:32px 20px 20px">
              {_auth_logo}
              <div class="hero-eyebrow"><span class="hero-pulse"></span>LIVE · CG + UP GOVERNMENT INTELLIGENCE</div>
              <h1 class="hero-h1" style="font-size:clamp(1.8rem,4vw,3rem)">
                Every Tender. Every Job.<br><em>One Intelligence Platform.</em>
              </h1>
              <p class="hero-sub" style="margin-bottom:18px">
                Discover, qualify and act on verified government opportunities across
                Chhattisgarh and Uttar Pradesh.
              </p>
              <div class="hero-cta-row" style="margin-bottom:8px">
                <div class="hero-pill">📋 {len(df_t):,} active tenders</div>
                <div class="hero-pill">💼 {len(df_j):,} open jobs</div>
                <div class="hero-pill">🌏 CG + UP coverage</div>
                <div class="hero-pill">⚡ Daily auto-update</div>
              </div>
            </div>""", unsafe_allow_html=True)

            # Symmetric gutters keep the login card centered on desktop; Streamlit
            # stacks the center column cleanly on narrow mobile screens.
            _left_auth, _ac, _right_auth = st.columns([1, 1.45, 1])
            with _ac:
                # ── Auth mode tabs ──
                _t1, _t2 = st.columns(2)
                if _t1.button("🔑  Login", width="stretch",
                              type="primary" if st.session_state.auth_mode == "login" else "secondary",
                              key="tab_login"):
                    st.session_state.auth_mode = "login"
                    st.rerun()
                if _t2.button("✨  Create Account", width="stretch",
                              type="primary" if st.session_state.auth_mode != "login" else "secondary",
                              key="tab_reg"):
                    st.session_state.auth_mode = "register"
                    st.rerun()

                st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

                # ── Continue with Google (works for both login & register) ──
                _google_signin_button(lang, key="g_signin_hero")
                st.markdown(
                    f"<div style='text-align:center;color:#64748B;font-size:.72rem;"
                    f"letter-spacing:.08em;margin:10px 0 6px'>— {i18n.t('or', lang)} —</div>",
                    unsafe_allow_html=True)

                # ── LOGIN ──
                if st.session_state.auth_mode == "login":
                    _le = st.text_input("Email", key="li_email",
                                        placeholder="you@gmail.com",
                                        label_visibility="collapsed")
                    _lp = st.text_input("Password", type="password", key="li_pw",
                                        placeholder="Password",
                                        label_visibility="collapsed")
                    if st.button("Login  →", width="stretch", key="do_login"):
                        if _le and _lp:
                            ok, msg, token, refresh = accounts.login_user(_le, _lp)
                            if ok:
                                st.session_state.authenticated = True
                                st.session_state.email = _le.strip().lower()
                                st.session_state.sb_token = token or ""
                                st.session_state.sb_refresh = refresh or ""
                                st.session_state.entered_platform = False
                                st.rerun()
                            elif msg == "EMAIL_NOT_CONFIRMED":
                                st.warning("📧 This email isn't confirmed yet. Check your inbox (and spam) for the confirmation link, then log in.")
                            elif msg == "RATE_LIMIT":
                                st.warning("⏳ The login server is busy right now. Please wait a minute and try again.")
                            else:
                                st.error(msg)
                        else:
                            st.warning("Enter email and password.")
                    _forgot_password_ui(lang, "hero")

                # ── REGISTER: direct signup (no OTP email — instant) ──
                elif st.session_state.auth_mode == "register":
                    st.caption("Create your account below — instant, no verification code needed.")
                    _re = st.text_input("Email", key="reg_email",
                                        placeholder="you@gmail.com",
                                        label_visibility="collapsed")
                    _rp = st.text_input("Choose password", type="password", key="reg_pw",
                                        placeholder="Choose a password (min 6 chars)",
                                        label_visibility="collapsed")
                    if st.button("Create Account  →", width="stretch", key="do_register"):
                        if not (_re and _rp):
                            st.warning("Enter your email and choose a password.")
                        elif len(_rp) < 6:
                            st.error("Password must be at least 6 characters.")
                        else:
                            ok, msg = accounts.register_user(_re, _rp)
                            if ok:
                                # Immediately log in — no email round-trip.
                                lok, lmsg, token, refresh = accounts.login_user(_re, _rp)
                                if lok:
                                    st.session_state.authenticated = True
                                    st.session_state.email = _re.strip().lower()
                                    st.session_state.sb_token = token or ""
                                    st.session_state.sb_refresh = refresh or ""
                                    st.session_state.entered_platform = False
                                    st.rerun()
                                elif lmsg == "EMAIL_NOT_CONFIRMED":
                                    st.success("✅ Account created. Please check your email for a confirmation link, then log in. (Tip: ask the admin to turn off 'Confirm email' in Supabase for instant access.)")
                                else:
                                    st.success("✅ Account created — switch to **Login** and sign in.")
                            elif msg == "ALREADY_EXISTS":
                                st.info("This email is already registered. Switch to **Login** above.")
                            elif msg == "RATE_LIMIT":
                                st.warning("⏳ Too many signups on the email server right now. Please wait a few minutes and try again.")
                            else:
                                st.error(msg)

    else:
        today_str = date.today().strftime("%A, %d %B %Y")
        _hour = datetime.now().hour
        _greeting = ("Good morning" if _hour < 12
                     else "Good afternoon" if _hour < 17 else "Good evening")
        if lang == "hi":
            _greeting = "नमस्ते"

        # ── Greeting ──
        st.markdown(f"""
        <div class="brief" style="padding:18px 26px;margin-bottom:20px">
          <div class="brief-row">
            <div>
              <div class="page-kicker">Today's Intelligence Briefing</div>
              <div class="brief-greeting">{_greeting}, {_html.escape(cname)} 👋</div>
              <div class="brief-sub"><span class="live-dot"></span> Live opportunity command center · {today_str}</div>
            </div>
          </div>
        </div>""", unsafe_allow_html=True)

        # ── HERO: big counts (center) + mini analytics (beside) ───────────────
        def _big_stat(icon, num, label, color):
            return (
                f'<div style="background:linear-gradient(145deg,#0B1329,#0D1A35);'
                f'border:1px solid rgba(0,196,255,.18);border-radius:20px;padding:22px 14px;'
                f'text-align:center;box-shadow:0 12px 40px rgba(0,196,255,.07);position:relative;overflow:hidden">'
                f'<div style="position:absolute;top:0;left:0;right:0;height:3px;'
                f'background:linear-gradient(90deg,{color},transparent)"></div>'
                f'<div style="font-size:1.6rem;margin-bottom:2px">{icon}</div>'
                f'<div style="font-size:2.9rem;font-weight:900;color:{color};line-height:1.05;letter-spacing:-.03em">{num}</div>'
                f'<div style="font-size:.7rem;font-weight:700;color:#94A3B8;text-transform:uppercase;'
                f'letter-spacing:.1em;margin-top:6px">{label}</div></div>')

        _h1, _h2, _h3, _h4 = st.columns([1.15, 1.15, 1.45, 1.45])
        with _h1:
            st.markdown(_big_stat("📋", len(df_t), i18n.tr("Active Tenders", lang), "#00C4FF"),
                        unsafe_allow_html=True)
            if st.button("📄  " + i18n.tr("Browse Tenders", lang) + "  →",
                         width="stretch", key="hero_go_tenders"):
                st.session_state.current_page = "📄  Tenders"; st.rerun()
        with _h2:
            st.markdown(_big_stat("💼", len(df_j), i18n.tr("Open Jobs", lang), "#10B981"),
                        unsafe_allow_html=True)
            if st.button("💼  " + i18n.tr("Browse Jobs", lang) + "  →",
                         width="stretch", key="hero_go_jobs"):
                st.session_state.current_page = "💼  Jobs"; st.rerun()
        with _h3:
            try:
                import plotly.graph_objects as _go
                _sc = (df_t["state"].dropna().value_counts().head(4)
                       if "state" in df_t and not df_t.empty else None)
                if _sc is not None and not _sc.empty:
                    _fig = _go.Figure(_go.Pie(
                        labels=_sc.index.tolist(), values=_sc.values.tolist(), hole=.62,
                        marker=dict(colors=["#00C4FF", "#1B6CF7", "#10B981", "#F59E0B"]),
                        textinfo="none", hovertemplate="%{label}: %{value}<extra></extra>"))
                    _fig.update_layout(
                        height=200, margin=dict(l=0, r=0, t=28, b=0),
                        paper_bgcolor="rgba(0,0,0,0)",
                        title=dict(text=i18n.tr("Tenders by State", lang),
                                   font=dict(color="#94A3B8", size=12), x=0.5, y=0.97),
                        showlegend=True, legend=dict(orientation="h", y=-0.04,
                                   font=dict(color="#94A3B8", size=10)))
                    st.plotly_chart(_fig, use_container_width=True, config={"displayModeBar": False})
            except Exception:
                pass
        with _h4:
            try:
                import plotly.graph_objects as _go
                _cc = (df_t["category_bucket"].dropna().value_counts().head(5)
                       if "category_bucket" in df_t and not df_t.empty else None)
                if _cc is not None and not _cc.empty:
                    _fig2 = _go.Figure(_go.Bar(
                        x=_cc.values[::-1].tolist(), y=_cc.index[::-1].tolist(),
                        orientation="h", marker=dict(color="#1B6CF7"),
                        hovertemplate="%{y}: %{x}<extra></extra>"))
                    _fig2.update_layout(
                        height=200, margin=dict(l=0, r=0, t=28, b=0),
                        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                        title=dict(text=i18n.tr("Top Sectors", lang),
                                   font=dict(color="#94A3B8", size=12), x=0.5, y=0.97),
                        xaxis=dict(visible=False),
                        yaxis=dict(tickfont=dict(color="#94A3B8", size=9)))
                    st.plotly_chart(_fig2, use_container_width=True, config={"displayModeBar": False})
            except Exception:
                pass

        # ── Secondary KPI strip ──
        _cg_tenders = int((df_t["state"] == "Chhattisgarh").sum()) if "state" in df_t else 0
        _up_tenders = int((df_t["state"] == "Uttar Pradesh").sum()) if "state" in df_t else 0
        _kcols = st.columns(6)
        _kpi_strip = [
            (_kcols[0], str(_cg_tenders), "CG Tenders", "📍", False),
            (_kcols[1], str(_up_tenders), "UP Tenders", "📍", False),
            (_kcols[2], str(eligible_count), i18n.tr("You Qualify", lang), "✅", False),
            (_kcols[3], str(high_conf_count), i18n.tr("High Confidence", lang), "🎯", False),
            (_kcols[4], str(closing_soon), i18n.tr("Closing in 7 days", lang), "⏰", True),
            (_kcols[5], f"₹{total_value/100:.1f}Cr", i18n.tr("Market Value", lang), "💰", False),
        ]
        for _col, _n, _l, _ic, _warn in _kpi_strip:
            _scls = "warn" if _warn and int(closing_soon) > 0 else ""
            _col.markdown(
                f'<div class="kpi" style="padding:16px 14px">'
                f'<div class="kpi-icon">{_ic}</div>'
                f'<div class="kpi-num" style="font-size:1.55rem">{_n}</div>'
                f'<div class="kpi-lbl">{_l}</div>'
                f'<div class="kpi-sub {_scls}"></div></div>', unsafe_allow_html=True)

        _vault_docs_dash = _cached_vault_docs(email, _token) if email else []
        _document_alert_n = len(_doc_expiry_alerts(_vault_docs_dash))
        _high_value_n = (int((pd.to_numeric(df_t["value_lakhs"], errors="coerce") >= 100).sum())
                         if "value_lakhs" in df_t else 0)
        st.markdown("""<div class="sec-hd">
          <span class="sec-title">Urgent Actions</span>
          <span class="sec-badge">Prioritized today</span>
          <div class="sec-divider"></div>
        </div>""", unsafe_allow_html=True)
        st.markdown(
            f'<div class="action-grid">'
            f'<div class="action-card" style="--accent:#F59E0B"><div class="action-icon">⏰</div>'
            f'<div class="action-value">{closing_soon}</div><div class="action-label">Closing soon</div>'
            f'<div class="action-note">Deadlines within 7 days</div></div>'
            f'<div class="action-card" style="--accent:#10B981"><div class="action-icon">🎯</div>'
            f'<div class="action-value">{high_conf_count}</div><div class="action-label">New matches</div>'
            f'<div class="action-note">High-confidence opportunities</div></div>'
            f'<div class="action-card" style="--accent:#8B5CF6"><div class="action-icon">💎</div>'
            f'<div class="action-value">{_high_value_n}</div><div class="action-label">High-value tenders</div>'
            f'<div class="action-note">Estimated value ₹1 crore+</div></div>'
            f'<div class="action-card" style="--accent:#F87171"><div class="action-icon">📄</div>'
            f'<div class="action-value">{_document_alert_n}</div><div class="action-label">Document alerts</div>'
            f'<div class="action-note">Expired or expiring soon</div></div></div>',
            unsafe_allow_html=True)

        # ── Quick links to the rest of the app ──
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        _q1, _q2, _q3 = st.columns(3)
        if _q1.button("📊  " + i18n.t("nav_analytics", lang), width="stretch", key="hero_go_analytics"):
            st.session_state.current_page = "📊  Analytics"; st.rerun()
        if _q2.button("👤  " + i18n.t("nav_profile", lang), width="stretch", key="hero_go_profile"):
            st.session_state.current_page = "👤  Profile"; st.rerun()
        if _q3.button("⚡  " + i18n.tr("Tender Intelligence", lang), width="stretch", key="hero_go_ws"):
            st.session_state.current_page = "⚡  Opporta Tender Intelligence"; st.rerun()

        # ── Gentle prompt until a profile is set ──
        if not PROFILE_READY:
            st.markdown(f"""
            <div class="brief" style="border-color:rgba(0,196,255,.2);margin-top:16px">
              <div class="brief-greeting" style="font-size:1.05rem">👋 {i18n.tr("Complete your profile to unlock personalised matches", lang)}</div>
              <div class="brief-sub" style="margin-top:6px;max-width:640px">
                Add your contractor class, sectors &amp; districts (or upload a document to your Vault)
                and Opporta Intelligence will show personalized fit scores and suggested tenders for you.
              </div>
            </div>""", unsafe_allow_html=True)
            _gt1, _gt2 = st.columns(2)
            if _gt1.button("👤  " + i18n.t("nav_profile", lang), width="stretch", key="gate_profile"):
                st.session_state.current_page = "👤  Profile"
                st.rerun()
            if _gt2.button("📄  Vault", width="stretch", key="gate_vault"):
                st.session_state.current_page = "👤  Profile"
                st.session_state["profile_tab"] = "vault"
                st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Active Tenders · Top matches list ──
        st.markdown(f"""<div class="sec-hd">
          <span class="sec-title">{i18n.tr("📋 Active Tenders", lang)}</span>
          <span class="sec-badge-green">🎯 Matched to your profile</span>
          <div class="sec-divider"></div>
        </div>""", unsafe_allow_html=True)

        if scored:
            for s, eligible, reasons, rec in scored[:4]:
                rc     = ring_cls(s)
                dl     = days_left(rec.get("deadline"))
                dl_txt = f"⏱ {dl}d left" if dl is not None and dl >= 0 else ("⚠ Expired" if dl is not None else "No deadline")
                val    = _v(rec.get("value_text")) or (
                    f"₹{float(rec.get('value_lakhs',0)):.0f}L" if rec.get("value_lakhs") else "—")
                elig_cls   = "tag-green" if eligible else "tag-warn"
                elig_txt   = "✅ Eligible" if eligible else "⚠ Review"
                district   = _v(rec.get("district"), "State-wide")
                color      = score_color(s)

                st.markdown(f"""<div class="ocard">
                  <div class="ocard-row">
                    <div class="ocard-body">
                      <div class="ocard-title">{_clickable_title(rec.get('title'), rec.get('document_url'))}</div>
                      <div class="ocard-org">🏛 {safe_str(rec.get('organization'), 60)} &nbsp;·&nbsp; {_v(rec.get('state'))}</div>
                      <div class="ocard-tags">
                        <span class="tag tag-val">💰 {val}</span>
                        <span class="tag tag-dl">{dl_txt}</span>
                        <span class="tag tag-loc">📍 {district}</span>
                        <span class="tag tag-cat">{_v(rec.get('category'), 'General')}</span>
                        <span class="tag {elig_cls}">{elig_txt}</span>
                      </div>
                    </div>
                    <div class="ring {rc}" style="color:{color};border-color:{color}">{s}</div>
                  </div>
                </div>""", unsafe_allow_html=True)

                with st.expander(f"Details — {safe_str(rec.get('title'), 50)}"):
                    dc1, dc2 = st.columns(2)
                    dc1.write(f"**Organization:** {_v(rec.get('organization'))}")
                    dc1.write(f"**Category:** {_v(rec.get('category'))}")
                    dc1.write(f"**District:** {district}")
                    dc1.write(f"**State:** {_v(rec.get('state'))}")
                    dc2.write(f"**Value:** {val}")
                    dc2.write(f"**Deadline:** {_v(rec.get('deadline'))}")
                    dc2.write(f"**Source ID:** {_v(rec.get('source_id'))}")
                    if reasons:
                        st.markdown("**Match reasons:**")
                        for r in reasons:
                            st.caption(f"• {r}")
                    doc_url = rec.get("document_url")
                    if doc_url and str(doc_url) not in ("nan","None","—"):
                        _pdf_widget(doc_url, rec.get("source_id",""), ctx="dash")
                    if st.button("➕ Save to Pipeline", key=_rec_key("d_save", rec)):
                        accounts.save_tender(email, rec.get("source_id"), token=_token)
                        st.toast("✓ Saved to pipeline")

            if st.button("📄  See all active tenders  →", width="stretch",
                         key="dash_see_all_tenders"):
                st.session_state.current_page = "📄  Tenders"
                st.rerun()
        elif not PROFILE_READY:
            st.markdown("""<div class="ocard" style="text-align:center;padding:36px">
              <div style="font-size:2rem;margin-bottom:12px">👤</div>
              <div style="font-size:.9rem;font-weight:700;color:#94A3B8">Complete your profile to see suggested matches</div>
              <div style="font-size:.78rem;color:#64748B;margin-top:6px;line-height:1.6">Add your contractor class, sectors &amp; districts and your personalized fit scores will appear here.</div>
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown("""<div class="ocard" style="text-align:center;padding:32px">
              <div style="font-size:2rem;margin-bottom:12px">📋</div>
              <div style="font-size:.88rem;font-weight:600;color:#94A3B8">No tenders currently match your criteria</div>
              <div style="font-size:.77rem;color:#64748B;margin-top:6px">Try widening your sectors or target districts in Profile</div>
            </div>""", unsafe_allow_html=True)

        # ══════════════════════════════════════════════════════════════════════
        # SECTION 3: Smart Pipeline Alerts  (folded into Dashboard)
        #   Only two mission-critical triggers — no generic announcements:
        #   (1) approaching deadlines on tenders the user is tracking
        #   (2) newly-surfaced high-match tenders above their qualification bar
        # ══════════════════════════════════════════════════════════════════════
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""<div class="sec-hd">
          <span class="sec-title">🔔 Smart Pipeline Alerts</span>
          <span class="sec-badge">Deadlines &amp; new high-matches only</span>
          <div class="sec-divider"></div>
        </div>""", unsafe_allow_html=True)

        _alerts = compute_smart_alerts(email, _token, scored, df_t)
        if _alerts:
            for _al in _alerts[:4]:
                st.markdown(
                    f'<div class="alert-item" style="border-left-color:{_al["color"]}">'
                    f'<div class="alert-title">{_al["icon"]} {_html.escape(_al["title"])}</div>'
                    f'<div class="alert-meta" style="color:#94A3B8">{_html.escape(_al["detail"])}</div>'
                    f'</div>',
                    unsafe_allow_html=True)
        else:
            st.markdown("""<div class="ocard" style="text-align:center;padding:24px">
              <div style="font-size:1.5rem;margin-bottom:6px">🔕</div>
              <div style="font-size:.82rem;color:#94A3B8;font-weight:600">No critical alerts</div>
              <div style="font-size:.74rem;color:#64748B;margin-top:4px">You'll be alerted on approaching deadlines for saved tenders and brand-new high-match opportunities.</div>
            </div>""", unsafe_allow_html=True)

        # ── Tools launcher (folded modules) ──
        st.markdown("<br>", unsafe_allow_html=True)
        _tl1, _tl2, _tl3 = st.columns(3)
        if _tl1.button("📊  Market Analytics", width="stretch", key="dash_open_analytics"):
            st.session_state.current_page = "📊  Analytics"
            st.rerun()
        if _tl2.button("⚡  Tender Intelligence", width="stretch", key="dash_open_ws"):
            st.session_state.current_page = "⚡  Opporta Tender Intelligence"
            st.rerun()
        if _tl3.button("📄  My Document Vault", width="stretch", key="dash_open_vault"):
            st.session_state.current_page = "👤  Profile"
            st.session_state["profile_tab"] = "vault"
            st.rerun()

        # ══════════════════════════════════════════════════════════════════════
        # SECTION 4: Latest Government Jobs
        # ══════════════════════════════════════════════════════════════════════
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(f"""<div class="sec-hd">
          <span class="sec-title">{i18n.tr("💼 Latest Government Jobs", lang)}</span>
          <span class="sec-badge">CG + UP</span>
          <div class="sec-divider"></div>
        </div>""", unsafe_allow_html=True)

        if not df_j.empty:
            for _jr in df_j.head(4).to_dict("records"):
                _jtitle = _html.escape(safe_str(_jr.get("title"), 95))
                _jdept  = _esc(_jr.get("department"))
                _jstate = _esc(_jr.get("state"))
                _jvac   = _v(_jr.get("vacancies"))
                _vac_badge = f'<div class="jvac">{_jvac} posts</div>' if _jvac not in ("—", "") else ''
                st.markdown(
                    f'<div class="jcard"><div class="jcard-row"><div class="jcard-body">'
                    f'<div class="jcard-title">{_jtitle}</div>'
                    f'<div class="jcard-dept">🏛 {_jdept} &nbsp;&middot;&nbsp; {_jstate}</div>'
                    f'</div>{_vac_badge}</div></div>',
                    unsafe_allow_html=True,
                )
            if st.button("💼  See all government jobs  →", width="stretch",
                         key="dash_see_all_jobs"):
                st.session_state.current_page = "💼  Jobs"
                st.rerun()
        else:
            st.markdown("""<div class="jcard" style="text-align:center;padding:28px;color:#7C8AA0">
              <div style="font-size:1.6rem;margin-bottom:8px">💼</div>
              <div style="font-size:.84rem;font-weight:600;color:#64748B">No open jobs right now — check back tomorrow</div>
            </div>""", unsafe_allow_html=True)

        # ══════════════════════════════════════════════════════════════════════
        # SECTION 5: compact route to the dedicated bid workspace
        # ══════════════════════════════════════════════════════════════════════
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""<div class="sec-hd">
          <span class="sec-title">🛠 Opporta Bid Workspace</span>
          <span class="sec-badge-green">Dedicated tender tool</span>
          <div class="sec-divider"></div>
        </div>""", unsafe_allow_html=True)

        if st.button("Open Bid Workspace →", width="stretch", key="dash_bid_workspace"):
            st.session_state.current_page = "🧠  Opporta Bid Workspace"
            st.rerun()

        # Retain the previous inline implementation as unreachable compatibility
        # code while the dedicated page becomes the single public experience.
        if False:
            _ws_ai = bool(
                os.getenv("GEMINI_API_KEY") or _secret("GEMINI_API_KEY") or
                os.getenv("ANTHROPIC_API_KEY") or _secret("ANTHROPIC_API_KEY"))
            if not _ws_ai:
                st.warning("Opporta Intelligence document generation is temporarily unavailable.")

            st.markdown("**Step 1 — Tender document** (the NIT / tender notice PDF)")
            _ws_tender = st.file_uploader("Tender document", type=["pdf", "jpg", "jpeg", "png"],
                                          key="ws_tender_doc", label_visibility="collapsed")

            st.markdown("**Step 2 — Your firm documents** (GST, registration, experience, turnover — optional but recommended)")
            _ws_firm = st.file_uploader("Firm documents", type=["pdf", "txt", "jpg", "jpeg", "png"],
                                        accept_multiple_files=True, key="ws_firm_docs",
                                        label_visibility="collapsed")

            _wlang = st.session_state.get("lang", "en")
            st.markdown(f"**Step 3 — {i18n.t('bid_language', _wlang)}**")
            _ws_lang_lbl = st.radio(i18n.t("bid_language", _wlang), ["English", "हिंदी"],
                                    index=(1 if _wlang == "hi" else 0), horizontal=True,
                                    key="ws_bid_lang_dash", label_visibility="collapsed")
            _ws_lang = "hi" if _ws_lang_lbl == "हिंदी" else "en"

            if st.button("⚡  Generate Ready-to-Bid File", width="stretch", key="ws_generate"):
                if not _ws_tender:
                    st.warning("Upload the tender document first.")
                elif not _ws_ai:
                    st.error("Opporta Intelligence could not read this document. Please try again later.")
                else:
                    import bid_engine, vault_evaluator as _ve
                    # Parse firm documents into text for the readiness + bid context.
                    _ws_firm_texts: list[str] = []
                    for _ff in (_ws_firm or []):
                        try:
                            _txt = (_read_pdf_text(_ff) if _ff.name.lower().endswith(".pdf")
                                    else _ff.read().decode("utf-8", errors="ignore"))
                            if _txt.strip():
                                _ws_firm_texts.append(_txt)
                        except Exception:
                            pass
                    core.clear_ai_error()
                    with st.spinner("Opporta Intelligence is reading the tender, checking your eligibility & drafting the bid…"):
                        _ws_t   = bid_engine.extract_tender(_ws_tender.read(),
                                                            _ws_tender.type or "application/pdf")
                        _ws_chk = bid_engine.readiness_check(_ws_t, profile, _ws_firm_texts)
                        _ws_bid = bid_engine.generate_bid_content(_ws_t, profile, _ws_firm_texts,
                                                                  language=_ws_lang)
                        _ws_docx = bid_engine.build_docx(_ws_bid, _ws_t, profile,
                                                         language=_ws_lang) if _ws_bid else None

                    if _ws_t.get("_extraction_failed"):
                        st.session_state.pop("ws_result", None)
                        # Show the precise reason (quota / key / network) when we have it.
                        if core.ai_error_message():
                            _render_ai_error()
                        else:
                            st.error("Could not read the tender document automatically. Try a clearer PDF, or use the Opporta Intelligence Analyzer to enter details manually.")
                    else:
                        # Binary eligibility gate — reads profile + the user's Vault
                        # REGISTRY (file metadata), so it still works when a scanned
                        # document can't be OCR'd. Never raises.
                        _vault_docs = _cached_vault_docs(email, _token) if email else []
                        _elig = _ve.evaluate(_ws_t, profile, _vault_docs)
                        _slug = safe_str(_ws_t.get('tender_no') or _ws_t.get('title') or 'tender', 30)
                        _slug = _re.sub(r'[^A-Za-z0-9]+', '_', _slug).strip('_') or 'tender'
                        _cl   = _ws_bid.get("cover_letter", {}) if isinstance(_ws_bid, dict) else {}
                        # Stash everything so the workspace below survives reruns
                        # (checkbox toggles / text edits / downloads don't wipe it).
                        st.session_state["ws_result"] = {
                            "title":    safe_str(_ws_t.get("title"), 90),
                            "slug":     _slug,
                            "elig":     _elig,
                            "vault_n":  len(_vault_docs),
                            "cover":    _compose_cover_letter(_cl, _ws_t, profile),
                            "csv":      _compliance_csv(_ws_bid, _elig),
                            "docx":     _ws_docx,
                            "warnings": [w for w in (_ws_chk.get("warnings") or []) if "deadline" in w.lower()][:2],
                            "no_docx":  _ws_docx is None,
                        }

            # ── Persistent dual-workspace (renders from session_state, so it
            #    stays put across reruns: ticking a box or editing the letter
            #    no longer makes the whole package disappear) ─────────────────
            _wr = st.session_state.get("ws_result")
            if _wr:
                import vault_evaluator as _ve
                st.divider()
                st.success(f"✓ Bid package ready for: {_wr['title']}")

                _verd = _wr["elig"]["verdict"]
                _vc   = ("yes" if _verd == _ve.ELIGIBLE
                         else "no" if _verd == _ve.NOT_ELIGIBLE else "partial")
                _vi   = {"yes": "✅", "no": "⛔", "partial": "🔎"}[_vc]
                st.markdown(
                    f'<div class="elig-{_vc}" style="margin:6px 0 4px;font-size:.95rem;'
                    f'padding:12px 20px">{_vi}&nbsp; {_verd} &nbsp;·&nbsp; '
                    f'{_html.escape(_wr["elig"]["summary"])}</div>', unsafe_allow_html=True)
                st.caption(
                    f"Checked against your profile + {_wr['vault_n']} vault document(s). "
                    "Always confirm against the official tender PDF before bidding.")
                for _b in _wr["elig"].get("blockers", [])[:3]:
                    st.caption(f"⛔ {_b}")
                if _wr["elig"].get("missing_docs"):
                    st.caption("📎 Not in your vault: " + ", ".join(_wr["elig"]["missing_docs"]))
                for _w in _wr.get("warnings", []):
                    st.caption(f"⏳ {_w}")

                st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
                _colA, _colB = st.columns(2)

                # Column 1 — auto-generated online package
                with _colA:
                    st.markdown('<div class="profile-section-title">📦 Auto-Generated Package</div>',
                                unsafe_allow_html=True)
                    st.caption("Ready to copy / download for the online submission.")
                    _ck = f"ws_cover_{_wr['slug']}"
                    if _ck not in st.session_state:
                        st.session_state[_ck] = _wr["cover"]
                    st.text_area("Technical cover letter (editable)", key=_ck, height=230)
                    st.download_button(
                        "📊  Compliance / Deviation sheet (.csv)",
                        data=_wr["csv"], file_name=f"OPPORTA_Compliance_{_wr['slug']}.csv",
                        mime="text/csv", width="stretch", key="ws_csv")
                    if not _wr["no_docx"]:
                        st.download_button(
                            "📄  Full Bid Document (.docx)",
                            data=_wr["docx"], file_name=f"OPPORTA_Bid_{_wr['slug']}.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            width="stretch", key="ws_download")
                    else:
                        st.info("Full .docx draft unavailable — the cover letter + compliance "
                                "sheet above are still ready to use.")

                # Column 2 — manual actions the user must do physically
                with _colB:
                    st.markdown('<div class="profile-section-title">✍️ Manual Actions Required</div>',
                                unsafe_allow_html=True)
                    st.caption("Physical / legal papers you must arrange yourself — tick as you go:")
                    _done = 0
                    for _i, (_lbl, _hint) in enumerate(_MANUAL_BID_TASKS):
                        if st.checkbox(_lbl, key=f"ws_manual_{_i}", help=_hint):
                            _done += 1
                    _all = len(_MANUAL_BID_TASKS)
                    st.markdown(
                        f'<div class="elig-{"yes" if _done == _all else "partial"}" '
                        f'style="margin-top:10px">{_done}/{_all} manual items ready</div>',
                        unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# ── TENDERS — dedicated portal w/ multi-tier cascading filters ─────────────────
# ══════════════════════════════════════════════════════════════════════════════
elif "Tenders" in page:
    st.markdown(
        f'<div class="page-kicker">Procurement · CG + UP</div>'
        f'<div class="page-title">{i18n.tr("Tender Portal", lang)}</div>'
        f'<div class="page-sub">Discover opportunities, check tender eligibility with '
        f'Opporta Intelligence, and prepare bid documents in one tender-only workflow.</div>',
        unsafe_allow_html=True)
    _tf1, _tf2, _tf3 = st.columns(3)
    _tf1.button("📄 Browse Tenders", width="stretch", disabled=True,
                key="tender_feature_browse")
    if _tf2.button("⚡ Tender Intelligence", width="stretch",
                   key="tender_feature_intelligence"):
        st.session_state.current_page = "⚡  Opporta Tender Intelligence"
        st.rerun()
    if _tf3.button("🧠 Bid Workspace", width="stretch", key="tender_feature_bid"):
        st.session_state.current_page = "🧠  Opporta Bid Workspace"
        st.rerun()

    # ── Bid Workshop at the TOP — easy to find (ready-to-bid + eligibility) ──
    _render_bid_workshop()

    # ── Personalised alert strip — deadlines, new high-fit, document expiry ──
    # Document-expiry alerts show whenever signed in (an expired licence matters
    # regardless of profile completeness); match nudges need a configured profile.
    if st.session_state.authenticated:
        _vdocs  = _cached_vault_docs(email, _token) if email else []
        _doc_al = _doc_expiry_alerts(_vdocs)
        _alerts = compute_smart_alerts(email, _token, scored, df_t) if PROFILE_READY else []
        _all_al = _doc_al + _alerts          # documents first (expired = most urgent)
        if _all_al:
            _n_doc = len(_doc_al)
            _n_dl  = sum(1 for _a in _alerts if _a["icon"] == "⏰")
            _n_hi  = sum(1 for _a in _alerts if _a["icon"] == "🎯")
            _summary = " · ".join(x for x in [
                (f"⛔ {_n_doc} document alert{'s' if _n_doc != 1 else ''}" if _n_doc else ""),
                (f"⏰ {_n_dl} closing soon" if _n_dl else ""),
                (f"🎯 {_n_hi} new eligible" if _n_hi else ""),
            ] if x)
            with st.expander(f"🔔 For you — {_summary}", expanded=bool(_n_dl or _n_doc)):
                for _a in _all_al[:8]:
                    st.markdown(
                        f'<div class="alert-item" style="border-left-color:{_a["color"]}">'
                        f'<div class="alert-title">{_a["icon"]} {_html.escape(_a["title"])}</div>'
                        f'<div class="alert-meta" style="color:#94A3B8">{_html.escape(_a["detail"])}</div>'
                        f'</div>', unsafe_allow_html=True)

    # ── FILTERS (on top — users filter first) ────────────────────────────────
    all_cats = ["All"] + [c for c in TENDER_CATS_BY_FREQ]
    st.markdown('<div class="filter-row">', unsafe_allow_html=True)
    f1, f2, f3, f4 = st.columns([3, 1.5, 1.5, 1.5])
    with f1:
        new_search = st.text_input("Search", value=st.session_state.explore_search,
                                   placeholder="Search title, org, district, scope of work...",
                                   label_visibility="collapsed", key="ex_search")
        st.session_state.explore_search = new_search.lower()
    with f2:
        if st.session_state.explore_category not in all_cats:
            st.session_state.explore_category = "All"
        st.session_state.explore_category = st.selectbox(
            "Category", all_cats,
            index=all_cats.index(st.session_state.explore_category),
            label_visibility="collapsed", key="ex_cat")
    with f3:
        states_opts = ["All", "Chhattisgarh", "Uttar Pradesh"]
        if st.session_state.explore_state not in states_opts:
            st.session_state.explore_state = "All"
        prev_state = st.session_state.explore_state
        st.session_state.explore_state = st.selectbox(
            "State", states_opts,
            index=states_opts.index(st.session_state.explore_state),
            label_visibility="collapsed", key="ex_state")
        if st.session_state.explore_state != prev_state:
            st.session_state.explore_district = "All"
    with f4:
        sel_state = st.session_state.explore_state
        if sel_state == "All":
            dist_opts = ["All"] + sorted(set(CG_DISTRICTS + UP_DISTRICTS))
        else:
            dist_opts = ["All"] + _districts_for_state(sel_state)
        if st.session_state.explore_district not in dist_opts:
            st.session_state.explore_district = "All"
        st.session_state.explore_district = st.selectbox(
            "District", dist_opts,
            index=dist_opts.index(st.session_state.explore_district),
            label_visibility="collapsed", key="ex_dist")
    f5, f6, _filter_space = st.columns([1.5, 1.5, 4.5])
    with f5:
        _value_options = ["All values", "Under ₹10L", "₹10L–₹50L",
                          "₹50L–₹1Cr", "₹1Cr–₹5Cr", "₹5Cr+"]
        if st.session_state.explore_value not in _value_options:
            st.session_state.explore_value = "All values"
        st.session_state.explore_value = st.selectbox(
            "Estimated value", _value_options,
            index=_value_options.index(st.session_state.explore_value),
            label_visibility="collapsed", key="ex_value")
    with f6:
        _deadline_options = ["Any deadline", "Closing in 7 days", "Closing in 15 days",
                             "Closing in 30 days", "No deadline listed"]
        if st.session_state.explore_deadline not in _deadline_options:
            st.session_state.explore_deadline = "Any deadline"
        st.session_state.explore_deadline = st.selectbox(
            "Deadline", _deadline_options,
            index=_deadline_options.index(st.session_state.explore_deadline),
            label_visibility="collapsed", key="ex_deadline")
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Tender Amendments (Corrigendums) — closes the "missed amendment" gap ──
    df_corrig = load_table("corrigendums")
    if not df_corrig.empty:
        _crows = df_corrig.to_dict("records")
        # Newest first by published date
        _crows.sort(key=lambda r: str(r.get("published_date") or ""), reverse=True)
        with st.expander(f"⚠  Recent Tender Amendments (Corrigendums) · {len(_crows)} — dates/specs changed, don't miss these",
                         expanded=False):
            st.caption("A corrigendum changes a live tender (new closing date, specs or EMD). "
                       "Missing one can disqualify a bid — verify before you submit.")
            for _cr in _crows[:25]:
                _ctitle = _html.escape(safe_str(_cr.get("title"), 110))
                _cstate = _esc(_cr.get("state"))
                _cclose = _esc(_cr.get("closing_date"))
                _cpub   = _esc(_cr.get("published_date"))
                st.markdown(
                    f'<div class="alert-item" style="border-left-color:#F59E0B">'
                    f'<div class="alert-title">⚠ {_ctitle}</div>'
                    f'<div class="alert-meta" style="color:#94A3B8">📍 {_cstate} &nbsp;·&nbsp; '
                    f'🔁 amended {_cpub} &nbsp;·&nbsp; ⏰ new closing {_cclose}</div></div>',
                    unsafe_allow_html=True)
                _cc1, _cc2 = st.columns(2)
                if _cr.get("corrigendum_url"):
                    _cc1.link_button("📄 View Corrigendum", _cr["corrigendum_url"], width="stretch")
                if _cr.get("tender_url"):
                    _cc2.link_button("🌐 View Tender", _cr["tender_url"], width="stretch")

    # ── Offline / Newspaper Tenders — district-wise NITs printed only in papers ──
    # Many small offices (PWD divisions, Collector, Nagar Nigam, Gram Panchayat)
    # advertise tenders ONLY in local newspapers, never on e-procurement portals.
    # This captures them district-wise: browse what's collected, add tenders by
    # letting Opporta Intelligence read an e-paper page, or open district papers.
    _off_n = len(load_table("offline_tenders"))
    with st.expander(f"📰  Offline / Newspaper Tenders · {_off_n} collected — district-wise NITs printed in CG/UP papers",
                     expanded=True):
        st.caption("Government offices (PWD, Collector, Nagar Nigam, Gram Panchayat, Jal Sansadhan…) "
                   "often publish tenders only in local newspapers. Browse them district-wise, add "
                   "tenders from an e-paper page, or open your district's papers directly.")
        _ot1, _ot2, _ot3 = st.tabs(["📂 Browse (district-wise)",
                                    "➕ Add from e-paper",
                                    "🗞 Newspaper directory"])

        # ---- Tab 1: browse the shared offline-tender store, grouped by district
        with _ot1:
            df_off = load_table("offline_tenders")
            if df_off.empty:
                st.info("No offline tenders captured yet. Use **➕ Add from e-paper** to extract them "
                        "from a newspaper page, or open your district's papers under **🗞 Newspaper directory**.")
            else:
                _orows = df_off.to_dict("records")
                _ob1, _ob2 = st.columns(2)
                _of_state = _ob1.selectbox("State", ["All", "Chhattisgarh", "Uttar Pradesh"], key="off_b_state")
                # Build the district list from the standard set UNION the districts
                # actually present in the data (so official names like Bastar /
                # Surguja that aren't in the city-based standard list still appear).
                _std = (CG_DISTRICTS + UP_DISTRICTS if _of_state == "All"
                        else _districts_for_state(_of_state))
                _present = {_v(r.get("district")) for r in _orows
                            if r.get("district")
                            and (_of_state == "All" or _v(r.get("state")) == _of_state)}
                _of_dlist = ["All"] + sorted({d for d in _std} | {d for d in _present if d != "—"})
                _of_dist = _ob2.selectbox("District", _of_dlist, key="off_b_dist")
                _ofilt = [r for r in _orows
                          if (_of_state == "All" or _v(r.get("state")) == _of_state)
                          and (_of_dist == "All"
                               or _v(r.get("district", "")).lower() == _of_dist.lower())]
                st.markdown(f'<div class="sec-badge" style="display:inline-block;margin:6px 0 12px">'
                            f'{len(_ofilt)} offline tenders</div>', unsafe_allow_html=True)
                from collections import defaultdict as _dd
                _bydist = _dd(list)
                for r in _ofilt:
                    _bydist[_v(r.get("district"), "Unspecified district")].append(r)
                if not _ofilt:
                    st.caption("None for this filter yet.")
                for _dname in sorted(_bydist):
                    st.markdown(f'<div class="profile-section-title">📍 {_html.escape(_dname)} · '
                                f'{len(_bydist[_dname])}</div>', unsafe_allow_html=True)
                    for r in _bydist[_dname][:40]:
                        _render_offline_card(r)

        # ---- Tab 2: add offline tenders by reading an e-paper page (Vision) ----
        with _ot2:
            _ep_ai = bool(os.getenv("GEMINI_API_KEY") or _secret("GEMINI_API_KEY"))
            if not _ep_ai:
                st.warning("Opporta Intelligence e-paper reading is temporarily unavailable.")
            st.caption("Upload one or more newspaper / e-paper PAGES (photo, screenshot or PDF). "
                       "Opporta Intelligence reads each page and pulls out every government tender "
                       "notice printed on it — tagged district-wise.")
            _ec1, _ec2, _ec3 = st.columns(3)
            _ep_state = _ec1.selectbox("State", ["Chhattisgarh", "Uttar Pradesh"], key="ep_state")
            _ep_dist  = _ec2.selectbox("District (optional)",
                                       ["(auto-detect)"] + _districts_for_state(_ep_state), key="ep_dist")
            _ep_paper = _ec3.text_input("Newspaper (optional)", placeholder="e.g. Dainik Bhaskar", key="ep_paper")
            _ep_files = st.file_uploader("E-paper page(s)", type=["jpg", "jpeg", "png", "pdf"],
                                         accept_multiple_files=True, key="ep_files",
                                         label_visibility="collapsed")
            if st.button("🔎  Extract offline tenders from page(s)", width="stretch",
                         key="ep_extract", disabled=not _ep_ai):
                if not _ep_files:
                    st.warning("Upload at least one e-paper page first.")
                else:
                    import data_engine as _de
                    core.clear_ai_error()
                    _all, _ok_pages = [], 0
                    with st.spinner("Opporta Intelligence is reading the page(s) and extracting tender notices…"):
                        for _f in _ep_files:
                            try:
                                _recs, _stt = _de.extract_tenders_from_epaper(
                                    _f.read(), _f.type or "image/jpeg",
                                    district_hint=(None if _ep_dist == "(auto-detect)" else _ep_dist),
                                    state_hint=_ep_state,
                                    newspaper_hint=(_ep_paper.strip() or None),
                                    added_by=(email or None))
                                if _stt == "ok":
                                    _ok_pages += 1
                                _all += _recs
                            except Exception:
                                pass
                    # de-dup by source_id across pages
                    _seen, _ded = set(), []
                    for r in _all:
                        if r["source_id"] not in _seen:
                            _seen.add(r["source_id"]); _ded.append(r)
                    st.session_state["offline_extracted"] = _ded
                    if not _ded:
                        if core.ai_error_message():
                            _render_ai_error()
                        else:
                            st.info("No government tender notices were found on the uploaded page(s). "
                                    "Try a clearer scan of the tenders / classifieds page.")

            _ext = st.session_state.get("offline_extracted")
            if _ext:
                st.success(f"✓ Found {len(_ext)} tender notice(s). Review, then save them district-wise.")
                for r in _ext:
                    _render_offline_card(r)
                if st.button(f"💾  Save these {len(_ext)} to Offline Tenders", width="stretch", key="ep_save"):
                    _n = save_offline_tenders(_ext)
                    if _n:
                        load_table.clear()   # refresh the cached Browse table
                        st.session_state.pop("offline_extracted", None)
                        st.success(f"Saved {_n} offline tender(s) — they now appear under "
                                   "**📂 Browse (district-wise)** for everyone.")
                        st.rerun()

        # ---- Tab 3: real district-wise newspaper e-paper directory ------------
        with _ot3:
            import data_engine as _de
            _nd1, _nd2 = st.columns(2)
            _nd_state = _nd1.selectbox("State", ["Chhattisgarh", "Uttar Pradesh"], key="np_state")
            _nd_dist  = _nd2.selectbox("District", _districts_for_state(_nd_state), key="np_dist")
            st.caption(f"Open each paper's e-paper, choose the **{_nd_dist}** edition, then scan the "
                       "tender / classifieds pages for निविदा सूचना · NIT notices.")
            for _paper in _de.NEWSPAPER_DIRECTORY.get(_nd_state, []):
                st.markdown(f'**{_paper["name"]}** — <span style="color:#94A3B8">{_paper.get("note","")}</span>',
                            unsafe_allow_html=True)
                st.link_button(f'🗞 Open {_paper["name"]} e-paper', _paper["url"], width="stretch")

    # Apply filters (widgets are rendered at the top of the page)
    q    = st.session_state.explore_search
    fcat = st.session_state.explore_category
    fst  = st.session_state.explore_state
    fdst = st.session_state.explore_district
    fval = st.session_state.explore_value
    fddl = st.session_state.explore_deadline

    rows = []
    for _, r in df_t.iterrows():
        rec      = r.to_dict()
        haystack = f"{_v(rec.get('title'))} {_v(rec.get('organization'))} {_v(rec.get('district'))} {_v(rec.get('description'))}".lower()
        if q and q not in haystack: continue
        if fst  != "All" and _v(rec.get("state")) != fst: continue
        if fcat != "All" and rec.get("category_bucket") != fcat: continue
        if fdst != "All" and _v(rec.get("district","")).lower() != fdst.lower(): continue
        _raw_value = rec.get("value_lakhs")
        if _raw_value is None or (isinstance(_raw_value, float) and pd.isna(_raw_value)):
            _raw_value = rec.get("value_text")
        _value_lakhs = core.parse_value_to_lakhs(_raw_value)
        if fval == "Under ₹10L" and (_value_lakhs is None or _value_lakhs >= 10): continue
        if fval == "₹10L–₹50L" and (_value_lakhs is None or not 10 <= _value_lakhs < 50): continue
        if fval == "₹50L–₹1Cr" and (_value_lakhs is None or not 50 <= _value_lakhs < 100): continue
        if fval == "₹1Cr–₹5Cr" and (_value_lakhs is None or not 100 <= _value_lakhs < 500): continue
        if fval == "₹5Cr+" and (_value_lakhs is None or _value_lakhs < 500): continue
        _days = days_left(rec.get("deadline"))
        if fddl == "No deadline listed" and _days is not None: continue
        if fddl == "Closing in 7 days" and (_days is None or not 0 <= _days <= 7): continue
        if fddl == "Closing in 15 days" and (_days is None or not 0 <= _days <= 15): continue
        if fddl == "Closing in 30 days" and (_days is None or not 0 <= _days <= 30): continue
        if PROFILE_READY:
            s, _, eligible = core.score_tender_for_user(rec, profile)
            rows.append((s, eligible, rec))
        else:
            # No verified telemetry → show neutral market score, never a fit verdict.
            rows.append((int(rec.get("ai_score") or 0), None, rec))

    # Eligible tenders float to the top (score kept only as a hidden tiebreaker).
    rows.sort(key=lambda x: (1 if x[1] else 0, x[0]), reverse=True)

    # Results header
    count_col, _ = st.columns([1, 3])
    with count_col:
        st.markdown(f'<div class="sec-badge" style="display:inline-block;margin-bottom:18px">{len(rows)} results found</div>',
                    unsafe_allow_html=True)

    if not st.session_state.authenticated:
        st.info("🔐 Sign in and complete your profile to see which tenders you're eligible for.")
    elif not PROFILE_READY:
        st.info("ℹ️ Update your profile (contractor class, turnover, experience) to see which tenders you're eligible for.")

    if not rows:
        st.markdown("""<div class="ocard" style="text-align:center;padding:40px;color:#7C8AA0">
          <div style="font-size:2rem;margin-bottom:12px">🔍</div>
          <div style="font-size:.9rem;font-weight:600;color:#64748B">No tenders match your filters</div>
          <div style="font-size:.77rem;color:#566179;margin-top:6px">Try broadening your search or changing the state/district</div>
        </div>""", unsafe_allow_html=True)

    for s, eligible, rec in rows[:80]:
        dl       = days_left(rec.get("deadline"))
        dl_txt   = f"⏱ {dl}d left" if dl is not None and dl >= 0 else ("⚠ Expired" if dl is not None else "No deadline")
        val      = _v(rec.get("value_text")) or (f"₹{float(rec.get('value_lakhs',0)):.0f}L" if rec.get("value_lakhs") else "—")
        district = _v(rec.get("district"), "State-wide")
        # Binary verdict only — no percentage score. Eligible / Not Eligible
        # is decided from the user's profile (class, turnover, experience).
        if eligible is None:
            elig_html = '<span class="tag tag-cat">🔒 Complete profile to check eligibility</span>'
        elif eligible:
            elig_html = '<span class="tag tag-green">✅ Eligible</span>'
        else:
            elig_html = ('<span class="tag" style="background:rgba(239,68,68,.1);color:#F87171;'
                         'border:1px solid rgba(239,68,68,.25)">❌ Not Eligible</span>')
        score_html = (f'<div class="ring {ring_cls(s)}" title="Opporta Intelligence match score">{s}%</div>'
                      if PROFILE_READY else
                      '<div class="ring ring-md" title="Complete profile for a match score">—</div>')

        st.markdown(f"""<div class="ocard">
          <div class="ocard-row">
            <div class="ocard-body">
              <div class="ocard-title">{_clickable_title(rec.get('title'), rec.get('document_url'), 115)}</div>
              <div class="ocard-org">🏛 {safe_str(rec.get('organization'), 55)} &nbsp;·&nbsp; {_v(rec.get('state'))}</div>
              <div class="ocard-tags">
                <span class="tag tag-val">💰 {val}</span>
                <span class="tag tag-dl">{dl_txt}</span>
                <span class="tag tag-loc">📍 {district}</span>
                <span class="tag tag-cat">{_v(rec.get('category'), 'General')}</span>
                {elig_html}
              </div>
            </div>
            {score_html}
          </div>
        </div>""", unsafe_allow_html=True)

        with st.expander(f"View details · Analyze · Save · Share"):
            _lang = st.session_state.get("lang", "en")
            _exp  = i18n.tender_explainer(rec, _lang)

            # ── Plain-language: what this tender is about ──
            st.markdown(f"**📋 {i18n.t('about_this_tender', _lang)}**")
            st.write(_exp["about"])

            # ── Key facts (two compact columns) ──
            if _exp["facts"]:
                _fc1, _fc2 = st.columns(2)
                for _i, (_flabel, _fval) in enumerate(_exp["facts"]):
                    (_fc1 if _i % 2 == 0 else _fc2).markdown(f"**{_flabel}:** {_fval}")

            # ── How to take part (simple numbered steps) ──
            st.markdown(f"**🪜 {i18n.t('how_to_take_part', _lang)}**")
            for _i, _step in enumerate(_exp["steps"], 1):
                st.markdown(f"{_i}. {_step}")

            # ── Money & deposits you will need (EMD/TDR · solvency · form fee) ──
            st.markdown(f"**💰 {i18n.t('money_requirements', _lang)}**")
            for _m in i18n.tender_money_reqs(rec, _lang):
                st.markdown(
                    f"- **{_m['label']}** — {_m['value']}  \n"
                    f"  <span style='color:#7C8AA0;font-size:.85em'>{_m['meaning']}</span>",
                    unsafe_allow_html=True)
            st.caption("ℹ️ " + i18n.t("official_doc_note", _lang))

            if rec.get("description"):
                st.write(_v(rec.get("description")))
            doc_url = rec.get("document_url")
            if doc_url and str(doc_url) not in ("nan","None","—",""):
                _pdf_widget(doc_url, rec.get("source_id",""), ctx="exp")
            _act1, _act2, _act3, _act4 = st.columns(4)
            _doc_url = str(rec.get("document_url") or "").strip()
            if _doc_url.startswith("http"):
                _act1.link_button("View official", _doc_url,
                                  key=_rec_key("official", rec), width="stretch")
            else:
                _act1.button("Details shown", key=_rec_key("details", rec),
                             width="stretch", disabled=True)
            if _act2.button("Analyze", key=_rec_key("analyze", rec), width="stretch"):
                st.session_state["ws_prefill"] = str(rec.get("title") or "")
                st.session_state.current_page = "⚡  Opporta Tender Intelligence"
                st.rerun()
            if st.session_state.authenticated:
                if _act3.button("Save", key=_rec_key("e_save", rec), width="stretch"):
                    accounts.save_tender(email, rec.get("source_id"), token=_token)
                    st.toast("✓ Saved to your pipeline")
            else:
                _act3.button("Sign in to save", key=_rec_key("save_locked", rec),
                             width="stretch", disabled=True)
            _share_text = quote(
                f"{safe_str(rec.get('title'), 120)}\n{_doc_url or 'Shared from OPPORTA'}")
            _act4.link_button("Share", f"https://wa.me/?text={_share_text}",
                              key=_rec_key("share", rec), width="stretch")

    # ── Direct Portals: Official State Procurement Pipelines (bottom of page) ──
    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("🌐  Official State Procurement Pipelines — verified government portals", expanded=False):
        st.markdown(
            '<div class="portal-intro"><b>Authoritative data source network.</b> '
            '<span>Route directly to the official government procurement portals to verify a '
            'tender at source or browse listings we may not have ingested yet. Every link opens '
            'the live portal in a new browser tab.</span></div>', unsafe_allow_html=True)
        for _region, _items in PROCUREMENT_PORTALS.items():
            _sub = ("Pan-India procurement" if _region == "National"
                    else "State e-procurement & tenders")
            _portal_region(_region, _sub, _items, cols=2)

# ══════════════════════════════════════════════════════════════════════════════
# ── OPPORTA BID WORKSPACE ────────────────────────────────────────────────────
# Dedicated route for the ready-to-bid workflow. The same generator remains
# available as a compact expander in Tender Portal for backwards compatibility.
elif "Bid Workspace" in page:
    if not st.session_state.authenticated:
        st.warning("Sign in to access the Opporta Bid Workspace.")
        st.stop()
    st.markdown(
        '<div class="page-kicker">Bid intelligence · English / हिन्दी</div>'
        '<div class="page-title">Opporta Bid Workspace</div>'
        '<div class="page-sub">Upload the tender and your firm evidence, check deterministic '
        'eligibility, resolve missing documents and generate a ready-to-edit bid package.</div>',
        unsafe_allow_html=True)
    _render_bid_workshop(standalone=True)

# ── OPPORTA TENDER INTELLIGENCE ───────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════
elif "Workspace" in page or "Tender Intelligence" in page:
    if not st.session_state.authenticated:
        st.markdown("""<div class="ocard" style="text-align:center;padding:40px">
          <div style="font-size:2rem;margin-bottom:12px">🔐</div>
          <div style="font-size:.9rem;font-weight:600;color:#64748B">Sign in to access Tender Intelligence</div>
        </div>""", unsafe_allow_html=True)
        st.stop()

    # Prefill the evaluator search when arriving from Tender Portal.
    if "ws_prefill" in st.session_state:
        st.session_state["eval_search_q"] = st.session_state.pop("ws_prefill")

    has_ai = bool(
        os.getenv("GEMINI_API_KEY") or _secret("GEMINI_API_KEY") or
        os.getenv("ANTHROPIC_API_KEY") or _secret("ANTHROPIC_API_KEY")
    )

    st.markdown("""<div class="terminal-hd">
      <div class="terminal-label">⚡ OPPORTA TENDER INTELLIGENCE</div>
      <div class="terminal-title">Tender Eligibility · Evidence Readiness · Bid Drafting</div>
      <div class="terminal-sub">Evaluate tender requirements against your profile and documents, then prepare bid paperwork — with no outcome guarantees.</div>
    </div>""", unsafe_allow_html=True)

    st.markdown(
        '<div style="background:rgba(0,196,255,.05);border:1px solid rgba(0,196,255,.15);border-radius:10px;'
        'padding:10px 16px;font-size:.75rem;color:#64748B;margin-bottom:18px;line-height:1.6">'
        '&#9432;&nbsp; <b style="color:#38BDF8">What Tender Intelligence does:</b> evaluates tender documents against '
        'your profile, scores 6 key dimensions, checks document readiness, drafts bid paperwork. &nbsp;'
        '<b style="color:#F59E0B">What it does not do:</b> predict award outcomes or guarantee you will win the tender. '
        'Final award decisions are made solely by the government authority.'
        '</div>',
        unsafe_allow_html=True)

    if not has_ai:
        st.info("Opporta Intelligence document reading is temporarily unavailable. Profile-based eligibility scoring remains active.")

    tab1, tab3 = st.tabs(["🔍  Tender Eligibility", "📝  Bid Drafter"])
    # Resume matching belongs exclusively to Government Jobs. Keep the existing
    # implementation mounted but hidden here to avoid changing evaluator logic.
    tab2 = st.container(key="hidden_job_intelligence")

    # ── Tab 1: Opporta Tender Evaluator ────────────────────────────────────────
    with tab1:
        st.markdown("""<div class="sec-hd">
          <span class="sec-title">Tender Document Evaluator</span>
          <span class="sec-badge">Eligibility &amp; Document Scoring</span>
          <div class="sec-divider"></div>
        </div>""", unsafe_allow_html=True)

        if df_t.empty:
            st.warning("Tender data is being refreshed. Please check again shortly.")
        else:
            # ── Searchable tender picker ──────────────────────────────────────
            eval_q = st.text_input(
                "Search tender by name, organisation or district",
                placeholder="e.g. road construction, CSPDCL, Raipur...",
                key="eval_search_q",
                label_visibility="collapsed",
            )
            search_lower = eval_q.strip().lower()

            # Filter rows
            if search_lower:
                mask = df_t.apply(
                    lambda r: search_lower in f"{r.get('title','')} {r.get('organization','')} {r.get('district','')}".lower(),
                    axis=1,
                )
                df_filtered = df_t[mask].reset_index(drop=True)
            else:
                df_filtered = df_t.reset_index(drop=True)

            match_count = len(df_filtered)
            st.caption(f"{match_count} tender{'s' if match_count != 1 else ''} match — select one below")

            if df_filtered.empty:
                st.warning("No tenders match your search. Try different keywords.")
            else:
                titles_f = df_filtered["title"].fillna("Untitled").tolist()
                sel_idx  = st.selectbox(
                    "Pick tender",
                    range(len(titles_f)),
                    format_func=lambda i: safe_str(titles_f[i], 110),
                    key="eval_sel",
                    label_visibility="collapsed",
                )
                selected_tender = df_filtered.iloc[sel_idx].to_dict()

                val_t = _v(selected_tender.get("value_text")) or (
                    f"₹{float(selected_tender.get('value_lakhs',0)):.0f}L"
                    if selected_tender.get("value_lakhs") else "—")
                doc_url = _v(selected_tender.get("document_url"), "")
                pdf_tag = '<span class="tag tag-green">&#128196; PDF Available</span>' if doc_url else ""

                _title_e  = _html.escape(safe_str(selected_tender.get('title'), 130))
                _org_e    = _html.escape(_v(selected_tender.get('organization')))
                _state_e  = _html.escape(_v(selected_tender.get('state')))
                _cat_e    = _html.escape(_v(selected_tender.get('category')))
                _dl_e     = _html.escape(_v(selected_tender.get('deadline')))
                _dist_e   = _html.escape(_v(selected_tender.get('district'), 'State-wide'))
                _val_e    = _html.escape(val_t)
                tcard_html = (
                    f'<div class="ocard" style="margin:10px 0 12px">'
                    f'<div class="ocard-title">{_title_e}</div>'
                    f'<div class="ocard-org">&#127963; {_org_e} &nbsp;&middot;&nbsp; {_state_e} &nbsp;&middot;&nbsp; {_cat_e}</div>'
                    f'<div class="ocard-tags" style="margin-bottom:6px">'
                    f'<span class="tag tag-val">&#x20B9; {_val_e}</span>'
                    f'<span class="tag tag-dl">&#128197; Deadline: {_dl_e}</span>'
                    f'<span class="tag tag-loc">&#128205; {_dist_e}</span>'
                    f'{pdf_tag}'
                    f'</div></div>'
                )
                st.markdown(tcard_html, unsafe_allow_html=True)
                if doc_url:
                    _pdf_widget(doc_url, selected_tender.get("source_id","eval"), compact=True, ctx="ev")

                uploaded_docs = st.file_uploader(
                    "Upload your firm documents for compliance check (GST, registration, certs) — optional",
                    type=["pdf","txt","png","jpg","jpeg"],
                    accept_multiple_files=True, key="eval_docs")

                doc_text = ""
                if uploaded_docs:
                    for f in uploaded_docs:
                        if f.name.lower().endswith(".pdf"):
                            doc_text += " " + _read_pdf_text(f)
                        else:
                            try: doc_text += " " + f.read().decode("utf-8", errors="ignore")
                            except Exception: pass
                    st.caption(f"✓ Parsed {len(doc_text):,} chars from {len(uploaded_docs)} file(s)")

                if st.button("📊 Evaluate Documents & Score Eligibility", width="stretch", key="eval_btn"):
                    with st.spinner("Scoring documents across 6 dimensions — profitability, eligibility, document readiness..."):
                        _t_clean = evaluator._clean(selected_tender)
                        result   = evaluator.evaluate_tender(_t_clean, profile, doc_text)
                        scores   = evaluator.score_opportunity(_t_clean, profile)
                        profit   = evaluator.profitability_analysis(_t_clean, profile)
                        checklist = evaluator.submission_checklist(_t_clean, doc_text)
                        hi_pri   = evaluator.is_high_priority(_t_clean)

                    # ── HIGH PRIORITY badge ───────────────────────────────
                    if hi_pri:
                        st.markdown('<div class="hp-badge">&#9889; HIGH PRIORITY OPPORTUNITY — Coal / Logistics / Transport Sector</div>', unsafe_allow_html=True)

                    # ── Eligibility verdict ───────────────────────────────
                    pct   = result["readiness_pct"]
                    color = score_color(pct)
                    n_missing = len(result["missing"])
                    n_unknown = len(result["unknown"])
                    if n_missing == 0 and n_unknown == 0:
                        elig_cls  = "elig-yes"
                        elig_txt  = "✅ DOCUMENTS COMPLETE — All stated criteria appear satisfied in your profile"
                    elif n_missing == 0:
                        elig_cls  = "elig-partial"
                        elig_txt  = f"⚠ UNVERIFIED ITEMS ({n_unknown}) — Upload firm documents above to confirm these criteria"
                    elif n_missing <= 2:
                        elig_cls  = "elig-partial"
                        elig_txt  = f"⚠ GAPS FOUND — {n_missing} criterion/criteria not satisfied based on your current profile"
                    else:
                        elig_cls  = "elig-no"
                        elig_txt  = f"❌ SIGNIFICANT GAPS — {n_missing} requirements not met; review before applying"

                    ev_verdict_e = _html.escape(result["verdict"])
                    st.markdown(
                        f'<div class="{elig_cls}" style="margin-bottom:16px">{elig_txt}</div>'
                        f'<div style="font-size:.82rem;color:#64748B;margin-bottom:18px">{ev_verdict_e}</div>',
                        unsafe_allow_html=True)

                    # ── 6-Dimension Score Grid ────────────────────────────
                    _SCORE_META = [
                        ("lead",          "Lead Score",        "Overall opportunity quality"),
                        ("profit",        "Profit Score",      "Margin & revenue potential"),
                        ("qualification", "Qualify Score",     "Probability you qualify"),
                        ("competition",   "Competition Risk",  "Higher = more competition"),
                        ("payment",       "Payment Trust",     "Dept. payment reliability"),
                        ("strategic",     "Strategic Value",   "Long-term business value"),
                    ]
                    score_cards = ""
                    for key, lbl, _ in _SCORE_META:
                        sv, _ = scores[key]
                        cls  = "hi" if sv >= 70 else "md" if sv >= 45 else "lo"
                        col_s = "#10B981" if sv >= 70 else "#F59E0B" if sv >= 45 else "#F87171"
                        score_cards += (
                            f'<div class="score-card {cls}">'
                            f'<div class="score-val" style="color:{col_s}">{sv}</div>'
                            f'<div class="score-lbl">{lbl}</div>'
                            f'<div class="score-bar"><div class="score-bar-fill" style="width:{sv}%;background:{col_s}"></div></div>'
                            f'</div>'
                        )
                    st.markdown(f'<div class="score-grid">{score_cards}</div>', unsafe_allow_html=True)

                    # ── Score reasoning in expander ───────────────────────
                    with st.expander("View score reasoning"):
                        for key, lbl, desc in _SCORE_META:
                            sv, reasons = scores[key]
                            st.markdown(f"**{lbl}** — {sv}/100 _{desc}_")
                            for r in reasons: st.caption(f"  • {r}")

                    st.markdown('<hr class="glass-divider">', unsafe_allow_html=True)

                    # ── Profitability Analysis ────────────────────────────
                    st.markdown('<div class="chart-title">&#x1F4B0; Profitability Analysis</div>', unsafe_allow_html=True)
                    pr = profit
                    if pr["revenue"] > 0:
                        p_html = (
                            f'<div class="profit-panel">'
                            f'<div class="profit-row"><span class="profit-label">Potential Revenue</span><span class="profit-val">&#x20B9;{pr["revenue"]:.1f}L</span></div>'
                            f'<div class="profit-row"><span class="profit-label">Est. Operating Cost</span><span class="profit-val">&#x20B9;{pr["op_cost"]:.1f}L</span></div>'
                            f'<div class="profit-row"><span class="profit-label">Gross Margin ({pr["margin_pct"]}%)</span><span class="profit-val" style="color:{pr["color"]}">&#x20B9;{pr["gross_margin"]:.1f}L</span></div>'
                            f'<div class="profit-row"><span class="profit-label">Working Capital Needed</span><span class="profit-val">&#x20B9;{pr["working_cap"]:.1f}L</span></div>'
                            f'<div class="profit-row"><span class="profit-label">Cash Flow Risk</span><span class="profit-val">{_html.escape(pr["cf_risk"])}</span></div>'
                            f'<div style="margin-top:12px"><span class="profit-rating" style="background:{pr["color"]}22;color:{pr["color"]};border:1px solid {pr["color"]}44">{pr["rating"]}</span></div>'
                            f'</div>'
                        )
                        st.markdown(p_html, unsafe_allow_html=True)
                    else:
                        st.caption("Tender value not available — profitability estimate not possible.")

                    st.markdown('<hr class="glass-divider">', unsafe_allow_html=True)

                    # ── Document Checklist ────────────────────────────────
                    cl1, cl2 = st.columns(2)
                    with cl1:
                        st.markdown('<div class="chart-title">&#x1F4CB; Required Documents</div>', unsafe_allow_html=True)
                        chk_html = '<div class="profit-panel">'
                        for item in checklist["always"]:
                            icon  = "✅" if item["status"] == "present" else "❓" if item["status"] == "unknown" else "❌"
                            color_i = "#10B981" if item["status"] == "present" else "#64748B" if item["status"] == "unknown" else "#F87171"
                            chk_html += (
                                f'<div class="checklist-item">'
                                f'<span class="chk-icon">{icon}</span>'
                                f'<span class="chk-label">{_html.escape(item["label"])}</span>'
                                f'<span class="chk-status chk-req" style="color:{color_i}">Required</span>'
                                f'</div>'
                            )
                        chk_html += '</div>'
                        st.markdown(chk_html, unsafe_allow_html=True)

                    with cl2:
                        st.markdown('<div class="chart-title">&#x1F4CC; Conditional Documents</div>', unsafe_allow_html=True)
                        cond_html = '<div class="profit-panel">'
                        for item in checklist["conditional"]:
                            icon  = "✅" if item["status"] == "present" else "❓" if item["status"] in ("unknown","check") else "❌"
                            color_i = "#10B981" if item["status"] == "present" else "#7C8AA0"
                            badge_cls = "chk-req" if item["required"] else "chk-opt"
                            badge_txt = "Required" if item["required"] else "Optional"
                            cond_html += (
                                f'<div class="checklist-item">'
                                f'<span class="chk-icon">{icon}</span>'
                                f'<span class="chk-label">{_html.escape(item["label"])}</span>'
                                f'<span class="chk-status {badge_cls}">{badge_txt}</span>'
                                f'</div>'
                            )
                        cond_html += '</div>'
                        st.markdown(cond_html, unsafe_allow_html=True)

                    if not uploaded_docs:
                        st.caption("Upload your firm documents above to verify ✅ which items you already have.")

                    st.markdown('<hr class="glass-divider">', unsafe_allow_html=True)

                    # ── Submission Steps ──────────────────────────────────
                    st.markdown('<div class="chart-title">&#x1F9FE; Ready-to-Submit Checklist</div>', unsafe_allow_html=True)
                    steps_html = '<div class="profit-panel">'
                    for step in checklist["steps"]:
                        num, text = step.split(". ", 1)
                        steps_html += (
                            f'<div class="step-item">'
                            f'<span class="step-num">{num}</span>'
                            f'<span>{_html.escape(text)}</span>'
                            f'</div>'
                        )
                    steps_html += '</div>'
                    st.markdown(steps_html, unsafe_allow_html=True)

    # ── Tab 2: Resume Analyzer ─────────────────────────────────────────────────
    with tab2:
        st.markdown("""<div class="sec-hd">
          <span class="sec-title">Resume Analyzer</span>
          <span class="sec-badge">Job Match Check</span>
          <div class="sec-divider"></div>
        </div>""", unsafe_allow_html=True)

        if df_j.empty:
            st.warning("Job data is being refreshed. Please check again shortly.")
        else:
            job_list = df_j["title"].fillna("Untitled").tolist()
            job_idx  = st.selectbox("Select job posting",
                                    range(len(job_list)),
                                    format_func=lambda i: safe_str(job_list[i], 100),
                                    key="ra_job")
            selected_job = df_j.iloc[job_idx].to_dict()

            st.markdown(f"""<div class="jcard" style="margin:10px 0 18px">
              <div class="jcard-title">{safe_str(selected_job.get('title'), 100)}</div>
              <div class="jcard-dept">{_v(selected_job.get('department'))} &nbsp;·&nbsp;
                {_v(selected_job.get('state'))} &nbsp;·&nbsp;
                Vacancies: {_v(selected_job.get('vacancies'))}</div>
              <div style="font-size:.77rem;color:#7C8AA0;line-height:1.5">
                {safe_str(selected_job.get('qualification'), 220)}
              </div>
            </div>""", unsafe_allow_html=True)

            resume_file = st.file_uploader(
                "Upload your resume (PDF or TXT)",
                type=["pdf","txt"], key="ra_resume")
            resume_text = ""
            if resume_file:
                resume_text = (_read_pdf_text(resume_file)
                               if resume_file.name.lower().endswith(".pdf")
                               else resume_file.read().decode("utf-8", errors="ignore"))
                st.caption(f"✓ Parsed {len(resume_text):,} characters from resume")

            if st.button("⚡ Analyze Resume Match", width="stretch", key="ra_btn"):
                if not resume_text:
                    st.warning("Please upload your resume first.")
                else:
                    with st.spinner("Opporta Intelligence is matching your resume against job requirements..."):
                        result = evaluator.evaluate_resume_for_job(selected_job, resume_text)

                    pct   = result["readiness_pct"]
                    color = score_color(pct)
                    st.markdown(f"""<div class="res-panel">
                      <div style="display:flex;align-items:center;gap:24px">
                        <div style="text-align:center;flex-shrink:0">
                          <div class="res-score" style="color:{color}">{pct}%</div>
                          <div class="res-label">Resume Match</div>
                          <div class="readiness-bar" style="width:70px;margin:8px auto 0">
                            <div class="readiness-fill" style="width:{pct}%;background:{color}"></div>
                          </div>
                        </div>
                        <div class="res-verdict">{result['verdict']}</div>
                      </div>
                    </div>""", unsafe_allow_html=True)

                    st.markdown("<br>", unsafe_allow_html=True)
                    r1, r2, r3 = st.columns(3)
                    with r1:
                        if result["met"]:
                            st.success(f"✅ Matched ({len(result['met'])})")
                            for item in result["met"]: st.caption(f"• {item}")
                    with r2:
                        if result["missing"]:
                            st.error(f"❌ Missing ({len(result['missing'])})")
                            for item in result["missing"]: st.caption(f"• {item}")
                    with r3:
                        if result["unknown"]:
                            st.warning(f"⚠️ Could not verify ({len(result['unknown'])})")
                            for item in result["unknown"]: st.caption(f"• {item}")

    # ── Tab 3: Bid Generator ──────────────────────────────────────────────────
    with tab3:
        st.markdown("""<div class="sec-hd">
          <span class="sec-title">Bid Document Drafter</span>
          <span class="sec-badge">Prepares Paperwork Only</span>
          <div class="sec-divider"></div>
        </div>""", unsafe_allow_html=True)

        if not has_ai:
            st.warning("Opporta Intelligence document generation is temporarily unavailable.")

        b1, b2 = st.columns(2)
        with b1:
            st.markdown("**Step 1 — Select or upload tender document**")

            # Option A: pick from live data (has document URL)
            bid_q = st.text_input("Search from live tenders (by name/org)",
                                  placeholder="e.g. road, CSPDCL, Raipur...",
                                  key="bid_search_q",
                                  label_visibility="collapsed")
            bid_q_lower = bid_q.strip().lower()
            if not df_t.empty:
                df_bid_f = df_t[df_t.apply(
                    lambda r: bid_q_lower in f"{r.get('title','')} {r.get('organization','')} {r.get('district','')}".lower(),
                    axis=1,
                )].reset_index(drop=True) if bid_q_lower else df_t.reset_index(drop=True)

                if not df_bid_f.empty:
                    bid_titles = df_bid_f["title"].fillna("Untitled").tolist()
                    bid_pick   = st.selectbox("Select a tender", range(len(bid_titles)),
                                              format_func=lambda i: safe_str(bid_titles[i], 100),
                                              key="bid_from_list",
                                              label_visibility="collapsed")
                    picked_rec    = df_bid_f.iloc[bid_pick].to_dict()
                    picked_url    = _v(picked_rec.get("document_url"), "")
                    picked_title  = safe_str(picked_rec.get("title"), 80)

                    if picked_url:
                        _pdf_widget(picked_url, picked_rec.get("source_id","bid"), ctx="bid")
                        if st.button("✅ Use this tender for bid generation", key="bid_use_live",
                                     width="stretch"):
                            st.session_state.bid_tender = picked_rec
                            st.toast(f"✓ Loaded: {picked_title}")
                    else:
                        st.caption("No document URL for this tender — upload PDF manually below.")

            st.markdown("**— or upload PDF manually —**")
            tender_pdf = st.file_uploader(
                "Tender notice / NIT document",
                type=["pdf","jpg","jpeg","png"], key="bid_tender_pdf",
                label_visibility="collapsed")

        with b2:
            st.markdown("**Step 2 — Add your firm documents** (optional)")
            vault_files = st.file_uploader(
                "GST cert, registration, experience certs",
                type=["pdf","txt","jpg","jpeg","png"],
                accept_multiple_files=True, key="bid_vault_docs",
                label_visibility="collapsed")

        vault_texts: list[str] = []
        for vf in (vault_files or []):
            t = (_read_pdf_text(vf) if vf.name.lower().endswith(".pdf")
                 else vf.read().decode("utf-8", errors="ignore"))
            if t.strip(): vault_texts.append(t)

        if tender_pdf and st.button("🔍 Extract Tender Details", width="stretch", key="bid_extract"):
            core.clear_ai_error()
            with st.spinner("Opporta Intelligence reading tender document..."):
                import bid_engine
                st.session_state.bid_tender = bid_engine.extract_tender(
                    tender_pdf.read(), tender_pdf.type or "application/pdf")
            if not st.session_state.bid_tender.get("_extraction_failed"):
                st.success("✓ Extraction complete — review and edit below.")

        if st.session_state.get("bid_tender"):
            t = st.session_state.bid_tender
            if t.get("_extraction_failed"):
                if core.ai_error_message():
                    _render_ai_error()
                else:
                    st.error("Opporta Intelligence extraction failed — fill in the details below manually.")

            st.markdown("---")
            st.markdown("**Step 3 — Confirm extracted tender details**")
            with st.form("bid_tender_form"):
                bc1, bc2 = st.columns(2)
                with bc1:
                    t["title"]        = st.text_input("Tender Title",      _v(t.get("title"),""))
                    t["tender_no"]    = st.text_input("Tender Number",     _v(t.get("tender_no"),""))
                    t["organization"] = st.text_input("Issuing Authority", _v(t.get("organization"),""))
                    t["state"]        = st.text_input("State",             _v(t.get("state"),""))
                    t["district"]     = st.text_input("District",          _v(t.get("district"),""))
                    t["category"]     = st.text_input("Work Category",     _v(t.get("category"),""))
                with bc2:
                    t["value_text"]   = st.text_input("Estimated Value",   _v(t.get("value_text"),""))
                    t["deadline"]     = st.text_input("Deadline (YYYY-MM-DD)", _v(t.get("deadline"),""))
                    t["emd"]          = st.text_input("EMD Amount",        _v(t.get("emd"),""))
                    t["contractor_class"]        = st.text_input("Required Class", _v(t.get("contractor_class"),""))
                    t["required_turnover_lakhs"] = st.text_input("Required Turnover (Lakhs)", str(t.get("required_turnover_lakhs") or ""))
                    t["required_experience_years"] = st.text_input("Required Experience (Years)", str(t.get("required_experience_years") or ""))
                t["scope_of_work"]        = st.text_area("Scope of Work", _v(t.get("scope_of_work"),""), height=80)
                t["eligibility_criteria"] = st.text_area("Eligibility / Qualification", _v(t.get("eligibility_criteria"),""), height=70)
                docs_raw = st.text_area("Required Documents (one per line)", "\n".join(t.get("required_documents") or []), height=80)
                if st.form_submit_button("✅ Confirm Details", width="stretch"):
                    t["required_documents"] = [d.strip() for d in docs_raw.splitlines() if d.strip()]
                    st.session_state.bid_tender = t
                    st.success("✓ Details confirmed.")

            # Readiness
            st.markdown("---")
            st.markdown("**Step 4 — Readiness Check**")
            import bid_engine
            readiness = bid_engine.readiness_check(st.session_state.bid_tender, profile, vault_texts)
            pct   = readiness["overall_pct"]
            color = score_color(pct)

            st.markdown(f"""<div class="res-panel" style="margin-bottom:18px">
              <div style="display:flex;align-items:center;gap:24px">
                <div style="text-align:center;flex-shrink:0">
                  <div class="res-score" style="color:{color}">{pct}%</div>
                  <div class="res-label">Bid Ready</div>
                  <div class="readiness-bar" style="width:70px;margin:8px auto 0">
                    <div class="readiness-fill" style="width:{pct}%;background:{color}"></div>
                  </div>
                </div>
                <div class="res-verdict">
                  {'All stated requirements met — proceed to generate your bid.' if readiness['ready']
                   else f"{len(readiness['missing'])} requirement(s) need attention before submission."}
                </div>
              </div>
            </div>""", unsafe_allow_html=True)

            rr1, rr2, rr3 = st.columns(3)
            with rr1:
                if readiness["met"]:
                    st.success(f"✅ Met ({len(readiness['met'])})")
                    for item in readiness["met"]: st.caption(f"• {item}")
            with rr2:
                if readiness["missing"]:
                    st.error(f"❌ Missing ({len(readiness['missing'])})")
                    for item in readiness["missing"]: st.caption(f"• {item}")
            with rr3:
                if readiness["warnings"]:
                    st.warning(f"⚠️ Warnings ({len(readiness['warnings'])})")
                    for item in readiness["warnings"]: st.caption(f"• {item}")

            st.markdown("---")
            st.markdown("**Step 5 — Draft Bid Document**")
            if not has_ai:
                st.info("Opporta Intelligence bid drafting is temporarily unavailable.")
            else:
                st.caption("⚠️ This drafts a bid document template based on your inputs. Review, verify, and sign before official submission. Opporta does not guarantee tender award.")
                _wk_lang0 = st.session_state.get("lang", "en")
                _wk_lang_lbl = st.radio(i18n.t("bid_language", _wk_lang0), ["English", "हिंदी"],
                                        index=(1 if _wk_lang0 == "hi" else 0), horizontal=True,
                                        key="wk_bid_lang")
                _wk_lang = "hi" if _wk_lang_lbl == "हिंदी" else "en"
                if st.button("📝 Draft Bid Document (.docx)", width="stretch", key="bid_gen"):
                    core.clear_ai_error()
                    with st.spinner("Drafting bid document — this takes ~30 seconds..."):
                        bid_content = bid_engine.generate_bid_content(
                            st.session_state.bid_tender, profile, vault_texts, language=_wk_lang)
                    if bid_content:
                        with st.spinner("Compiling Word document..."):
                            docx_bytes = bid_engine.build_docx(
                                bid_content, st.session_state.bid_tender, profile, language=_wk_lang)
                        title_raw = st.session_state.bid_tender.get("title") or "bid"
                        safe_name = "".join(c if c.isalnum() or c in " _-" else "_"
                                            for c in title_raw[:40]).strip()
                        st.success("✓ Draft ready — review all details before official submission.")
                        st.download_button(
                            "⬇️ Download Bid Document (.docx)",
                            data=docx_bytes,
                            file_name=f"Bid_{safe_name}.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            width="stretch")
                    else:
                        _render_ai_error("Generation failed — please try again.")

# ══════════════════════════════════════════════════════════════════════════════
# ── JOBS ──────────────────────────────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════
elif "Jobs" in page:
    st.markdown(
        f'<div class="page-kicker">Government careers · CG + UP</div>'
        f'<div class="page-title">{i18n.tr("Government Jobs", lang)}</div>'
        f'<div class="page-sub">Find active notifications, check your profile match with '
        f'Opporta Intelligence, and prepare for upcoming exams.</div>',
        unsafe_allow_html=True)

    jtab1, jtab2, jtab3 = st.tabs([
        "💼  Job Opportunities",
        "⚡  Opporta Job Intelligence",
        "🏛  Exam Planner",
    ])

    # ── TAB 1: Active Job Board (live grid + filters) ──
    with jtab1:
        if df_j.empty:
            st.markdown("""<div class="ocard" style="text-align:center;padding:40px">
              <div style="font-size:2rem;margin-bottom:12px">💼</div>
              <div style="font-size:.9rem;color:#64748B">No job data. Run ingest.py to fetch live listings.</div>
            </div>""", unsafe_allow_html=True)
        else:
            # Job filters (on top — users filter first)
            st.markdown('<div class="filter-row">', unsafe_allow_html=True)
            jf1, jf2, jf3, jf4 = st.columns([2.6, 1.3, 1.3, 1.5])
            with jf1:
                jsearch = st.text_input("Search jobs", placeholder="Title, department, qualification...",
                                        label_visibility="collapsed", key="jsearch").lower()
            with jf2:
                jstates = ["All", "Chhattisgarh", "Uttar Pradesh"]
                jstate  = st.selectbox("State", jstates, label_visibility="collapsed", key="jstate")
            with jf3:
                jcats = ["All"] + sorted(df_j["category"].dropna().unique().tolist()) if "category" in df_j else ["All"]
                jcat  = st.selectbox("Category", jcats, label_visibility="collapsed", key="jcat")
            with jf4:
                jsrc = st.selectbox("Source", ["All sources", "📰 Newspaper jobs", "🌐 Online portals"],
                                    label_visibility="collapsed", key="jsrc")
            st.markdown('</div>', unsafe_allow_html=True)

            # A job is an "offline / newspaper" posting when its source portal says so.
            def _is_newspaper_job(rec) -> bool:
                return str(rec.get("source_portal", "")).lower().startswith(("newspaper", "offline"))

            # Job KPIs
            jk1, jk2, jk3, jk4 = st.columns(4)
            jk1.markdown(f'<div class="stat-card"><div class="stat-num">{len(df_j)}</div><div class="stat-lbl">Total Jobs</div></div>', unsafe_allow_html=True)
            cg_jobs = int((df_j["state"] == "Chhattisgarh").sum()) if "state" in df_j else 0
            up_jobs = int((df_j["state"] == "Uttar Pradesh").sum()) if "state" in df_j else 0
            jk2.markdown(f'<div class="stat-card"><div class="stat-num">{cg_jobs}</div><div class="stat-lbl">CG Jobs</div></div>', unsafe_allow_html=True)
            jk3.markdown(f'<div class="stat-card"><div class="stat-num">{up_jobs}</div><div class="stat-lbl">UP Jobs</div></div>', unsafe_allow_html=True)
            total_vac = 0
            try:
                total_vac = int(pd.to_numeric(df_j["vacancies"], errors="coerce").fillna(0).sum())
            except Exception: pass
            jk4.markdown(f'<div class="stat-card"><div class="stat-num">{total_vac:,}</div><div class="stat-lbl">Total Vacancies</div></div>', unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            jobs_filtered = []
            for _, r in df_j.iterrows():
                rec = r.to_dict()
                dl_check = days_left(rec.get("deadline"))
                if dl_check is not None and dl_check < 0:
                    continue  # skip expired
                hay = f"{_v(rec.get('title'))} {_v(rec.get('department'))} {_v(rec.get('qualification'))} {_v(rec.get('description'))}".lower()
                if jsearch and jsearch not in hay: continue
                if jstate != "All" and _v(rec.get("state")) != jstate: continue
                if jcat   != "All" and jcat.lower() not in _v(rec.get("category","")).lower(): continue
                if jsrc == "📰 Newspaper jobs" and not _is_newspaper_job(rec): continue
                if jsrc == "🌐 Online portals" and _is_newspaper_job(rec): continue
                jobs_filtered.append(rec)

            st.markdown(f'<div class="sec-badge" style="display:inline-block;margin-bottom:16px">{len(jobs_filtered)} postings</div>',
                        unsafe_allow_html=True)

            # Strict: show a match % ONLY when a real job-seeker profile exists.
            _job_prof_text = (_profile_to_resume_text(profile)
                              if (st.session_state.authenticated and _has_job_profile(profile))
                              else "")
            if st.session_state.authenticated and not _job_prof_text:
                st.info("ℹ️ Add your qualification, degree or skills in Profile → Job Seeker to see your suggested match % for every job.")

            for rec in jobs_filtered[:100]:
                dl     = days_left(rec.get("deadline"))
                dl_txt = f"⏱ {dl}d left" if dl is not None and dl >= 0 else "Open"
                vac    = _v(rec.get("vacancies"))
                try:
                    vac_num = int(float(vac))
                    vac_txt = f"{vac_num:,} posts"
                except Exception:
                    vac_txt = vac if vac != "—" else ""

                salary_v  = _esc(rec.get("salary"))
                cat_v     = _esc(rec.get("category"), "General")
                dept_v    = _esc(rec.get("department"))
                state_v   = _esc(rec.get("state"))
                title_v   = _html.escape(safe_str(rec.get("title"), 100))

                vac_tag   = f'<span class="tag tag-loc">&#128101; {vac_txt}</span>' if vac_txt else ""
                sal_tag   = f'<span class="tag tag-val">&#x20B9; {salary_v}</span>' if salary_v != "—" else ""
                jvac_div  = f'<div class="jvac">{vac_txt}</div>' if vac_txt else ""
                news_tag  = ('<span class="tag tag-green">&#128240; Newspaper</span>'
                             if _is_newspaper_job(rec) else "")

                # Auto eligibility badge from profile
                match_div = ""
                if _job_prof_text:
                    _m = evaluator._keyword_resume_eval(rec, _job_prof_text)
                    _p = _m["readiness_pct"]
                    _c = score_color(_p)
                    match_div = (f'<div style="text-align:center;flex-shrink:0;min-width:48px;margin-left:8px">'
                                 f'<div style="font-size:.95rem;font-weight:700;color:{_c}">{_p}%</div>'
                                 f'<div style="font-size:.6rem;color:#64748B">match</div></div>')

                card_html = (
                    f'<div class="jcard"><div class="jcard-row"><div class="jcard-body">'
                    f'<div class="jcard-title">{title_v}</div>'
                    f'<div class="jcard-dept">{dept_v} &nbsp;&middot;&nbsp; {state_v}</div>'
                    f'<div class="ocard-tags">'
                    f'<span class="tag tag-dl">{dl_txt}</span>'
                    f'{vac_tag}'
                    f'<span class="tag tag-cat">{cat_v}</span>'
                    f'{sal_tag}{news_tag}'
                    f'</div></div>{match_div}{jvac_div}</div></div>'
                )
                st.markdown(card_html, unsafe_allow_html=True)

                with st.expander(f"Details · Resume Match — {safe_str(rec.get('title'), 55)}"):
                    jd1, jd2 = st.columns(2)
                    jd1.write(f"**Department:** {_plain(rec.get('department'))}")
                    jd1.write(f"**Qualification:** {_plain(rec.get('qualification'))}")
                    jd1.write(f"**Category:** {_plain(rec.get('category'))}")
                    jd2.write(f"**Salary:** {_plain(rec.get('salary'))}")
                    jd2.write(f"**Deadline:** {_v(rec.get('deadline'))}")
                    jd2.write(f"**Vacancies:** {_v(rec.get('vacancies'))}")
                    desc = _plain(rec.get("description"))
                    if desc:
                        st.caption(desc[:600] + ("…" if len(desc) > 600 else ""))
                    doc_url = _v(rec.get("document_url") or rec.get("apply_link"))
                    if doc_url != "—":
                        _pdf_widget(doc_url, rec.get("source_id","j"), compact=True, ctx="job")

                    if st.session_state.authenticated:
                        st.markdown('<hr class="glass-divider">', unsafe_allow_html=True)
                        st.markdown("**Job Eligibility Check**")

                        # Auto-match from saved profile (instant, no upload needed)
                        _prof_resume = _profile_to_resume_text(profile)
                        if _prof_resume.strip():
                            _auto = evaluator._keyword_resume_eval(rec, _prof_resume)
                            _apct = _auto["readiness_pct"]
                            _acol = score_color(_apct)
                            st.markdown(
                                f'<div class="res-panel" style="padding:10px 16px">'
                                f'<b style="color:{_acol};font-size:1.3rem">{_apct}%</b>'
                                f'&nbsp; <span style="color:#94A3B8;font-size:.82rem">Profile match · {_auto["verdict"]}</span>'
                                f'</div>', unsafe_allow_html=True)
                            if _auto["met"]:
                                st.success("✅ Met: " + " · ".join(_auto["met"][:4]))
                            if _auto["missing"]:
                                st.error("❌ Missing: " + " · ".join(_auto["missing"][:4]))
                            st.caption("Auto-scored from your Job Seeker Profile. Upload resume below for deeper Opporta Intelligence analysis.")
                        else:
                            st.caption("Complete your **Job Seeker Profile** (Profile → Job Seeker Profile tab) for auto-scoring.")

                        # Optional resume upload for deeper Opporta Intelligence analysis
                        resume_up = st.file_uploader("Upload resume for Opporta Intelligence analysis (optional)",
                                                     type=["pdf","txt"],
                                                     key=_rec_key("jr", rec))
                        if resume_up:
                            rtext = (_read_pdf_text(resume_up)
                                     if resume_up.name.lower().endswith(".pdf")
                                     else resume_up.read().decode("utf-8", errors="ignore"))
                            if st.button("⚡ Deep Analysis", key=_rec_key("jra", rec)):
                                with st.spinner("Opporta Intelligence analyzing resume..."):
                                    res = evaluator.evaluate_resume_for_job(rec, rtext)
                                pct   = res["readiness_pct"]
                                color = score_color(pct)
                                st.markdown(f"""<div class="res-panel">
                                  <b style="color:{color};font-size:1.5rem">{pct}%</b>
                                  &nbsp; <span style="color:#94A3B8;font-size:.85rem">{res['verdict']}</span>
                                </div>""", unsafe_allow_html=True)
                                if res["met"]:    st.success("Met: " + " · ".join(res["met"]))
                                if res["missing"]:st.error("Missing: " + " · ".join(res["missing"]))

    # ── TAB 2: job-only Opporta Intelligence ──────────────────────────────────
    with jtab2:
        render_job_intelligence(df_j)

    # ── TAB 3: Upcoming Exams & Study Matrix (verified authorities + resources) ──
    with jtab3:
        st.markdown(
            '<div class="portal-intro"><b>Recruitment authorities + free study resources.</b> '
            '<span>The commissions below publish exam notifications, schedules, admit cards, '
            'official syllabi, previous papers and results on their own portals. Below them are '
            'free government learning platforms to actually prepare from. Every link opens in a '
            'new browser tab.</span></div>', unsafe_allow_html=True)

        # ── Opporta Intelligence Study Plan Generator ──
        st.markdown('<div class="profile-section-title" style="margin-top:6px">🧭 Opporta Intelligence Study Plan</div>',
                    unsafe_allow_html=True)
        st.caption("Pick your exam and its date — get a suggested, time-aware preparation plan with priority topics and resources.")
        _common_exams = [
            "UPPSC PCS (Prelims)", "UPSSSC PET", "UP Police Constable", "UP Super TET / TET",
            "UPPSC RO/ARO", "CGPSC State Service", "CG Vyapam (Patwari / Assistant)",
            "CG Police Constable", "CG TET", "CGPSC Medical (DME)", "Other (type below)",
        ]
        _sc1, _sc2, _sc3 = st.columns([2, 1.2, 1])
        with _sc1:
            _exam_sel = st.selectbox("Exam", _common_exams, key="sp_exam_sel",
                                     label_visibility="collapsed")
            _exam_custom = ""
            if _exam_sel == "Other (type below)":
                _exam_custom = st.text_input("Exam name", key="sp_exam_custom",
                                             placeholder="Type your exam name",
                                             label_visibility="collapsed")
        with _sc2:
            _exam_dt = st.date_input("Exam date", key="sp_date",
                                     min_value=date.today(), format="DD/MM/YYYY")
        with _sc3:
            _sp_hours = st.number_input("Hrs/day", min_value=1, max_value=16, value=4, key="sp_hours")

        if st.button("🧭  Generate Suggested Study Plan", width="stretch", key="sp_generate"):
            _exam_final = (_exam_custom.strip() or "Government Exam") if _exam_sel == "Other (type below)" else _exam_sel
            core.clear_ai_error()
            with st.spinner("Building your time-aware study plan…"):
                st.session_state["study_plan"] = evaluator.generate_study_plan(
                    _exam_final, str(_exam_dt), int(_sp_hours))
        if st.session_state.get("study_plan"):
            _render_study_plan(st.session_state["study_plan"])
            if st.button("✕  Clear plan", key="sp_clear"):
                st.session_state.pop("study_plan", None)
                st.rerun()

        st.markdown('<hr class="glass-divider">', unsafe_allow_html=True)

        st.markdown('<div class="profile-section-title" style="margin-top:6px">🏛 Official Recruitment Authorities</div>',
                    unsafe_allow_html=True)
        for _region, _items in RECRUITMENT_AUTHORITIES.items():
            _portal_region(_region, "Notifications · syllabi · admit cards · results", _items, cols=2)

        st.markdown('<div class="profile-section-title" style="margin-top:26px">📚 Free Study Resources</div>',
                    unsafe_allow_html=True)
        st.caption("Verified free government & education platforms — courses, textbooks, current affairs.")
        for _region, _items in STUDY_RESOURCES.items():
            _portal_region(_region, "Free · official · open-access", _items, cols=2)

# ══════════════════════════════════════════════════════════════════════════════
# ── ALERTS ────────────────────────────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════
elif "Alerts" in page:
    st.markdown(
        '<div class="page-kicker">Action center · Personalized monitoring</div>'
        '<div class="page-title">Alerts</div>'
        '<div class="page-sub">Deadline risk, new high-confidence matches and document '
        'renewals that can affect your next submission.</div>',
        unsafe_allow_html=True)
    _alert_docs = _cached_vault_docs(email, _token) if email else []
    _page_alerts = _doc_expiry_alerts(_alert_docs)
    if PROFILE_READY:
        _page_alerts += compute_smart_alerts(email, _token, scored, df_t)
    if _page_alerts:
        for _alert in _page_alerts:
            st.markdown(
                f'<div class="alert-item" style="border-left-color:{_alert["color"]}">'
                f'<div class="alert-title">{_alert["icon"]} {_html.escape(_alert["title"])}</div>'
                f'<div class="alert-meta">{_html.escape(_alert["detail"])}</div></div>',
                unsafe_allow_html=True)
    else:
        st.success("No urgent alerts. Saved-tender deadlines and Vault expiry dates are being monitored.")

# ══════════════════════════════════════════════════════════════════════════════
# ── SOURCE HEALTH ─────────────────────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════
elif "Source Health" in page:
    render_source_health(df_t, df_j)

# ══════════════════════════════════════════════════════════════════════════════
# ── SETTINGS ──────────────────────────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════
elif "Settings" in page:
    st.markdown(
        '<div class="page-kicker">Account · Platform preferences</div>'
        '<div class="page-title">Settings</div>'
        '<div class="page-sub">Manage your language, opportunity coverage and privacy preferences.</div>',
        unsafe_allow_html=True)
    _set1, _set2 = st.columns(2)
    with _set1:
        st.markdown('<div class="profile-section-title">Language</div>',
                    unsafe_allow_html=True)
        st.write("Use the English / हिन्दी switch at the top of every page.")
        st.caption("Your selected language stays active while you use the platform.")
    with _set2:
        st.markdown('<div class="profile-section-title">Opportunity coverage</div>',
                    unsafe_allow_html=True)
        st.write("Chhattisgarh and Uttar Pradesh")
        st.caption("Tender and government-job results are organized by state and district.")
    st.markdown('<div class="profile-section-title" style="margin-top:24px">Privacy</div>',
                unsafe_allow_html=True)
    st.info("Your profile and Vault documents are used only to personalize eligibility and readiness guidance.")

# ══════════════════════════════════════════════════════════════════════════════
# ── ANALYTICS ─────────────────────────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════
elif "Analytics" in page:
    import plotly.express as px
    import plotly.graph_objects as go

    # Shared dark layout for every chart
    _LAYOUT = dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(8,15,34,0.6)",
        font=dict(family="Inter, sans-serif", color="#94A3B8", size=11),
        margin=dict(l=8, r=8, t=8, b=8),
        hoverlabel=dict(bgcolor="#0B1329", bordercolor="#00C4FF",
                        font=dict(color="#F1F5F9", size=12)),
        showlegend=False,
    )
    _AXIS = dict(gridcolor="rgba(255,255,255,0.04)", tickfont=dict(color="#64748B"))

    def _bar(series, color="#00C4FF", horizontal=False):
        df_p = series.reset_index()
        df_p.columns = ["label", "count"]
        if horizontal:
            fig = px.bar(df_p, x="count", y="label", orientation="h",
                         color_discrete_sequence=[color])
            fig.update_layout(**_LAYOUT,
                              yaxis=dict(autorange="reversed", **_AXIS),
                              xaxis=dict(**_AXIS))
        else:
            fig = px.bar(df_p, x="label", y="count", color_discrete_sequence=[color])
            fig.update_layout(**_LAYOUT, yaxis=dict(**_AXIS))
        fig.update_traces(marker_line_width=0, hovertemplate="%{y}<extra></extra>" if horizontal
                          else "%{x}: <b>%{y}</b><extra></extra>")
        return fig

    def _chart_card(title, fig):
        _chart_notes = {
            "Tenders by Category": "Where procurement demand is concentrated.",
            "Jobs by Category": "Current recruitment demand by role family.",
            "Tenders by State": "Live opportunity coverage across CG and UP.",
            "Deadline Distribution (Next 60 Days)": "Upcoming submission pressure by week.",
            "Top Districts by Tender Count": "Districts with the strongest current activity.",
            "Top Organizations by Tender Count": "Most active procuring authorities.",
        }
        with st.container(border=True):
            st.markdown(f'<div class="chart-title">{title}</div>', unsafe_allow_html=True)
            st.caption(_chart_notes.get(title, "Current market distribution."))
            st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})

    st.markdown(f"""<div class="sec-hd">
      <span class="sec-title">{i18n.tr("📊 Market Intelligence", lang)}</span>
      <div class="sec-divider"></div>
    </div>""", unsafe_allow_html=True)

    if df_t.empty:
        st.warning("Market data is being refreshed. Please check again shortly.")
    else:
        # ── KPI row ──
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Tenders", len(df_t))
        m2.metric("Total Jobs",    len(df_j))
        m3.metric("CG Tenders",   int((df_t["state"] == "Chhattisgarh").sum()) if "state" in df_t else 0)
        m4.metric("UP Tenders",   int((df_t["state"] == "Uttar Pradesh").sum()) if "state" in df_t else 0)

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Row 1: category charts ──
        a1, a2 = st.columns(2)
        with a1:
            if "category_bucket" in df_t:
                _chart_card("Tenders by Category",
                            _bar(df_t["category_bucket"].value_counts().head(10),
                                 color="#00C4FF", horizontal=True))
        with a2:
            if not df_j.empty and "category" in df_j:
                _chart_card("Jobs by Category",
                            _bar(df_j["category"].fillna("General").value_counts().head(10),
                                 color="#06B6D4", horizontal=True))

        # ── Row 2: state + deadline ──
        a3, a4 = st.columns(2)
        with a3:
            if "state" in df_t:
                state_counts = df_t["state"].fillna("Unknown").value_counts()
                colors = ["#00C4FF" if s == "Chhattisgarh" else "#10B981"
                          for s in state_counts.index]
                fig_s = go.Figure(go.Bar(
                    x=state_counts.index.tolist(),
                    y=state_counts.values.tolist(),
                    marker_color=colors,
                    hovertemplate="%{x}: <b>%{y}</b><extra></extra>",
                ))
                fig_s.update_layout(**_LAYOUT)
                _chart_card("Tenders by State", fig_s)

        with a4:
            if "deadline" in df_t:
                df_dl = df_t[["deadline"]].copy()
                df_dl["deadline"] = pd.to_datetime(df_dl["deadline"], errors="coerce")
                today_dt = pd.Timestamp(date.today())
                cutoff   = today_dt + pd.Timedelta(days=60)
                df_dl    = df_dl[(df_dl["deadline"] >= today_dt) & (df_dl["deadline"] <= cutoff)]
                if not df_dl.empty:
                    df_dl["week"] = df_dl["deadline"].dt.to_period("W").astype(str)
                    _chart_card("Deadline Distribution (Next 60 Days)",
                                _bar(df_dl["week"].value_counts().sort_index(),
                                     color="#F59E0B"))
                else:
                    st.info("No tenders closing in the next 60 days.")

        # ── Row 3: districts + orgs ──
        st.markdown("<br>", unsafe_allow_html=True)
        a5, a6 = st.columns(2)
        with a5:
            if "district" in df_t:
                dist_counts = df_t["district"].dropna().value_counts().head(15)
                if not dist_counts.empty:
                    _chart_card("Top Districts by Tender Count",
                                _bar(dist_counts, color="#10B981", horizontal=True))
        with a6:
            if "organization" in df_t:
                org_counts = df_t["organization"].dropna().value_counts().head(10)
                _chart_card("Top Organizations by Tender Count",
                            _bar(org_counts, color="#1B6CF7", horizontal=True))

# ══════════════════════════════════════════════════════════════════════════════
# ── PROFILE ───────────────────────────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════
elif "Profile" in page or "Document Vault" in page:
    if not st.session_state.authenticated:
        st.warning("Sign in to access your profile.")
        st.stop()

    _profile_heading = "📄 Document Vault" if "Document Vault" in page else i18n.tr("👤 My Profile", lang)
    st.markdown(f"""<div class="sec-hd">
      <span class="sec-title">{_profile_heading}</span>
      <div class="sec-divider"></div>
    </div>""", unsafe_allow_html=True)

    if not PROFILE_READY:
        st.info("ℹ️ Update your profile below to see suggested matches and personalized fit scores. Your saved details power the recommendations.")

    _profile_tabs = ["🏢  Contractor Profile", "👤  Job Seeker Profile", "📄  Document Vault"]
    _profile_default = _profile_tabs[2] if "Document Vault" in page else _profile_tabs[0]
    ptab1, ptab2, ptab3 = st.tabs(
        _profile_tabs, default=_profile_default,
        key="profile_sections_vault" if "Document Vault" in page else "profile_sections")

    # ── Tab 1: Contractor Profile ──────────────────────────────────────────────
    with ptab1:
      with st.form("profile_form"):
        st.markdown('<div class="profile-section-title">Company Identity</div>', unsafe_allow_html=True)
        pf1, pf2 = st.columns(2)
        with pf1:
            company  = st.text_input("Company / Firm Name",
                                     value=_v(profile.get("company_name"),""),
                                     placeholder="Sharma Constructions Pvt. Ltd.")
            turnover = st.number_input("Annual Turnover (₹ Lakhs)", min_value=0.0, step=10.0,
                                       value=float(profile.get("turnover_lakhs") or 0))
        with pf2:
            classes = ["Class A", "Class B", "Class C", "Class D", "Open"]
            cur_cls = _v(profile.get("contractor_class"), "Class C")
            idx_cls = classes.index(cur_cls) if cur_cls in classes else 2
            cls = st.selectbox("Contractor Registration Class", classes, index=idx_cls)
            exp = st.number_input("Years of Experience", min_value=0, step=1,
                                  value=int(profile.get("experience_years") or 0))

        st.markdown('<div class="profile-section-title" style="margin-top:16px">Sector & Geography Targeting</div>',
                    unsafe_allow_html=True)
        ps1, ps2 = st.columns(2)
        with ps1:
            # Clean ~10 buckets that match the live data and the scoring engine.
            _sector_opts = list(core.CATEGORY_BUCKETS)
            for _s in (profile.get("sectors") or []):
                if _s not in _sector_opts:
                    _sector_opts.append(_s)
            sectors = st.multiselect("Sectors you bid in", _sector_opts,
                                     default=[s for s in (profile.get("sectors") or []) if s in _sector_opts])
            target_states = st.multiselect("Target States",
                                           ["Chhattisgarh", "Uttar Pradesh"],
                                           default=profile.get("states", ["Chhattisgarh", "Uttar Pradesh"]))
        with ps2:
            # Dynamic district list based on selected target states
            avail_dists: list[str] = []
            for ts in target_states:
                avail_dists.extend(_districts_for_state(ts))
            avail_dists = sorted(set(avail_dists)) if avail_dists else sorted(set(CG_DISTRICTS + UP_DISTRICTS))

            saved_dists = [d for d in (profile.get("districts") or []) if d in avail_dists]
            districts = st.multiselect("Target Districts (leave blank = all districts)",
                                       avail_dists, default=saved_dists)

        st.markdown("<br>", unsafe_allow_html=True)
        if st.form_submit_button("💾 Save Contractor Profile", width="stretch"):
            accounts.save_profile(email, {
                "company_name":     company,
                "turnover_lakhs":   turnover,
                "contractor_class": cls,
                "experience_years": exp,
                "sectors":          sectors,
                "states":           target_states,
                "districts":        districts,
            }, token=_token)
            _bust_user_cache()
            st.success("✓ Profile saved. Opporta Intelligence scores will update on next page load.")
            st.rerun()

      # ── Saved Pipeline (inside Contractor tab) ──
      st.markdown("""<div class="sec-hd" style="margin-top:36px">
        <span class="sec-title">📋 My Saved Tender Pipeline</span>
        <div class="sec-divider"></div>
      </div>""", unsafe_allow_html=True)

      saved = accounts.list_saved(email, token=_token)
      if saved:
          tender_lookup = ({r["source_id"]: r for _, r in df_t.iterrows()}
                           if not df_t.empty else {})
          st.markdown(f'<div class="sec-badge" style="display:inline-block;margin-bottom:14px">{len(saved)} saved</div>',
                      unsafe_allow_html=True)
          for s in saved:
              rec    = tender_lookup.get(s.get("source_id",""), {})
              title  = safe_str(rec.get("title", s.get("source_id","—")), 80)
              org    = _v(rec.get("organization"))
              status = _v(s.get("status"), "interested")
              val    = _v(rec.get("value_text"))
              dl     = days_left(rec.get("deadline"))
              dl_txt   = f"&#9201; {dl}d left" if dl is not None and dl >= 0 else ""
              val_tag  = f'<span class="tag tag-val">{_html.escape(val)}</span>' if val != "—" else ""
              dl_tag   = f'<span class="tag tag-dl">{dl_txt}</span>' if dl_txt else ""
              pcard_html = (
                  f'<div class="pipe-card"><div style="flex:1;min-width:0">'
                  f'<div style="font-size:.87rem;font-weight:600;color:#E2E8F0;margin-bottom:3px">&#128204; {_html.escape(title)}</div>'
                  f'<div style="font-size:.72rem;color:#7C8AA0">{_html.escape(org)}</div>'
                  f'<div class="ocard-tags" style="margin-top:8px">'
                  f'<span class="tag tag-cat">Status: {_html.escape(status)}</span>'
                  f'{val_tag}{dl_tag}'
                  f'</div></div></div>'
              )
              st.markdown(pcard_html, unsafe_allow_html=True)
      else:
          st.markdown("""<div class="ocard" style="text-align:center;padding:32px">
            <div style="font-size:2rem;margin-bottom:10px">📋</div>
            <div style="font-size:.86rem;color:#64748B">No saved tenders yet</div>
            <div style="font-size:.75rem;color:#566179;margin-top:6px">
              Use the Tenders portal to save tenders to your pipeline.
            </div>
          </div>""", unsafe_allow_html=True)

    # ── Tab 2: Job Seeker Profile ──────────────────────────────────────────────
    with ptab2:
        st.markdown('<div class="profile-section-title">Personal & Academic Details</div>',
                    unsafe_allow_html=True)

        _DEGREE_OPTIONS = [
            "B.Tech / B.E. (Engineering)", "MBA / PGDM", "MCA",
            "M.Tech / M.E.", "B.Ed (Teacher Training)", "MBBS / Medical Degree",
            "GNM / B.Sc Nursing", "12th / Intermediate", "Diploma",
            "B.Sc / B.A. / B.Com (Graduate)", "Ph.D / Post-Graduate (Other)",
        ]
        _CATEGORY_OPTIONS = ["General", "OBC", "SC", "ST", "EWS"]
        _LANG_OPTIONS     = ["Hindi", "English", "Chhattisgarhi", "Awadhi", "Bhojpuri", "Urdu"]

        with st.form("job_seeker_form"):
            js1, js2 = st.columns(2)
            with js1:
                full_name = st.text_input("Full Name",
                    value=_v(profile.get("full_name"), ""),
                    placeholder="Rajesh Kumar Sharma")
                cur_deg = _v(profile.get("degree_type"), "")
                deg_idx = _DEGREE_OPTIONS.index(cur_deg) if cur_deg in _DEGREE_OPTIONS else 0
                degree_type = st.selectbox("Highest Degree / Qualification",
                    _DEGREE_OPTIONS, index=deg_idx)
                job_exp = st.number_input("Total Work Experience (years)", min_value=0,
                    step=1, value=int(profile.get("job_experience_years") or 0))
            with js2:
                cur_cat = _v(profile.get("job_category"), "General")
                cat_idx = _CATEGORY_OPTIONS.index(cur_cat) if cur_cat in _CATEGORY_OPTIONS else 0
                job_cat = st.selectbox("Reservation Category", _CATEGORY_OPTIONS, index=cat_idx)
                saved_langs = [l for l in (profile.get("languages") or []) if l in _LANG_OPTIONS]
                languages   = st.multiselect("Languages Known", _LANG_OPTIONS,
                    default=saved_langs if saved_langs else ["Hindi", "English"])
                skills_raw = st.text_input("Key Skills (comma-separated)",
                    value=", ".join(profile.get("job_skills") or []),
                    placeholder="e.g. AutoCAD, MS Office, Tally, Python")

            qualification = st.text_area("Qualification Details",
                value=_v(profile.get("qualification"), ""),
                placeholder="e.g. B.Tech Civil Engineering, NIT Raipur, 2018, 75%\nAlso list any diploma, certificate courses, or training",
                height=90)

            st.markdown("<br>", unsafe_allow_html=True)
            if st.form_submit_button("💾 Save Job Seeker Profile", width="stretch"):
                skills_list = [s.strip() for s in skills_raw.split(",") if s.strip()]
                accounts.save_profile(email, {
                    "full_name":            full_name,
                    "qualification":        qualification,
                    "degree_type":          degree_type,
                    "job_experience_years": job_exp,
                    "job_skills":           skills_list,
                    "job_category":         job_cat,
                    "languages":            languages,
                }, token=_token)
                _bust_user_cache()
                st.success("✓ Job seeker profile saved. The Jobs page will now auto-score your eligibility.")
                st.rerun()

        # ── Auto Job Eligibility Preview ── (only with a real job-seeker profile)
        _js_resume = _profile_to_resume_text(profile)
        if _has_job_profile(profile):
            st.markdown('<div class="profile-section-title" style="margin-top:24px">Your Job Eligibility (from profile)</div>',
                        unsafe_allow_html=True)
            st.caption("Based on your saved profile — upload a resume in the Jobs tab for deeper Opporta Intelligence analysis.")
            if not df_j.empty:
                _preview_jobs = df_j.head(15).to_dict("records")
                for _j in _preview_jobs:
                    _res = evaluator._keyword_resume_eval(_j, _js_resume)
                    _pct = _res["readiness_pct"]
                    _col = score_color(_pct)
                    _ttl = safe_str(_j.get("title"), 70)
                    _dept = _v(_j.get("department"))
                    st.markdown(
                        f'<div class="jcard" style="padding:10px 16px">'
                        f'<div class="jcard-row"><div class="jcard-body">'
                        f'<div class="jcard-title" style="font-size:.82rem">{_html.escape(_ttl)}</div>'
                        f'<div class="jcard-dept">{_html.escape(_dept)}</div></div>'
                        f'<div style="text-align:center;flex-shrink:0;min-width:52px">'
                        f'<div style="font-size:1.1rem;font-weight:700;color:{_col}">{_pct}%</div>'
                        f'<div style="font-size:.62rem;color:#64748B">match</div>'
                        f'</div></div></div>',
                        unsafe_allow_html=True)
        else:
            st.info("Fill in your qualification, degree type, skills and save above — the app will automatically score your eligibility for every job.")

    # ── Tab 3: Document Vault ──────────────────────────────────────────────────
    with ptab3:
        st.markdown('<div class="profile-section-title">Secure Document Vault</div>',
                    unsafe_allow_html=True)
        st.caption("Contractor licenses, capacity certificates, resumes, GST / turnover statements. "
                   "Uploaded files help Opporta Intelligence decide which tenders you're eligible for.")

        _vc1, _vc2 = st.columns([2, 1])
        with _vc1:
            _vault_label = st.text_input("Document label", key="vault_label",
                                         placeholder="e.g. Contractor License (Class A), GST Certificate, Resume")
        with _vc2:
            _vault_kind = st.selectbox("Type", ["License", "Capacity Cert", "Resume",
                                                "Tax / Turnover", "Other"], key="vault_kind")
        _vault_file = st.file_uploader("Select file", type=["pdf", "jpg", "jpeg", "png", "txt", "docx"],
                                       key="vault_file_up")

        # ── Validity / expiry tracking → powers Opporta Intelligence renewal alerts ──
        import datetime as _dt
        _ex1, _ex2 = st.columns([1.5, 1])
        _exp_val = None
        with _ex1:
            _track_exp = st.checkbox(
                "This document has a validity / expiry date",
                key="vault_track_exp",
                value=bool(st.session_state.get("vault_ai_expiry")))
            if _track_exp:
                _ai_exp = st.session_state.get("vault_ai_expiry")
                _def_d  = core.parse_date(_ai_exp) if _ai_exp else _dt.date.today()
                _exp_d  = st.date_input("Valid until", value=_def_d, key="vault_exp_date",
                                        min_value=_dt.date(2000, 1, 1),
                                        max_value=_dt.date(2100, 12, 31))
                _exp_val = _exp_d.isoformat() if _exp_d else None
        with _ex2:
            st.caption("Let Opporta Intelligence read the file & find its expiry date:")
            if st.button("🔎  Auto-detect expiry", width="stretch", key="vault_ai_detect"):
                if _vault_file:
                    import data_engine as _de
                    with st.spinner("Opporta Intelligence is reading the document…"):
                        _info = _de.extract_document_expiry(
                            _vault_file.getvalue(), _vault_file.type or "application/pdf")
                    if _info.get("expiry_date"):
                        st.session_state["vault_ai_expiry"] = _info["expiry_date"]
                        st.rerun()
                    elif _info.get("status") == "ok":
                        st.info("No expiry date found — this document may not have one.")
                    elif _info.get("status") == "no_key":
                        st.warning("Automatic expiry detection is temporarily unavailable — set the date manually.")
                    else:
                        st.warning("Couldn't read it automatically — set the date manually.")
                else:
                    st.warning("Choose a file first.")

        if st.button("⬆️  Upload to Vault & Index", width="stretch", key="vault_do_upload"):
            if _vault_file and _vault_label:
                _raw = _vault_file.getvalue()
                # Extraction parser → feed text into the Intelligence core.
                _parsed = ""
                try:
                    if _vault_file.name.lower().endswith(".pdf"):
                        import io as _io
                        _parsed = _read_pdf_text(_io.BytesIO(_raw))
                    elif _vault_file.name.lower().endswith(".txt"):
                        _parsed = _raw.decode("utf-8", errors="ignore")
                except Exception:
                    _parsed = ""
                with st.spinner("Uploading securely & indexing for match scoring…"):
                    _did = accounts.save_document(
                        email, f"[{_vault_kind}] {_vault_label}", _vault_file.name,
                        _raw, _vault_file.type or "application/octet-stream", token=_token,
                        expiry_date=_exp_val, doc_type=_vault_kind)
                if _did:
                    _bust_user_cache()
                    st.session_state.pop("vault_ai_expiry", None)
                    _msg = "✓ Uploaded. Suggested match scoring is now active."
                    if _exp_val:
                        _msg += f"  Validity tracked ({_exp_val}) — we'll alert you before it expires."
                    st.success(_msg)
                    st.rerun()
                else:
                    st.error("Upload failed. Check logs.")
            else:
                st.warning("Add a label and choose a file first.")

        st.markdown('<div class="profile-section-title" style="margin-top:22px">Stored Documents</div>',
                    unsafe_allow_html=True)
        _docs = accounts.list_documents(email, token=_token)

        # ── Opporta Intelligence vault-health banner (expired / expiring soon) ──
        _expired_n  = sum(1 for _d in _docs if (_s := _doc_expiry_status(_d)) and _s[0] == "EXPIRED")
        _expiring_n = sum(1 for _d in _docs if (_s := _doc_expiry_status(_d)) and _s[0] == "EXPIRING")
        if _expired_n or _expiring_n:
            _hc = "#F87171" if _expired_n else "#F59E0B"
            _parts = ([f"⛔ {_expired_n} expired"] if _expired_n else []) + \
                     ([f"⚠ {_expiring_n} expiring within 30 days"] if _expiring_n else [])
            st.markdown(
                f'<div class="alert-item" style="border-left-color:{_hc};margin-bottom:14px">'
                f'<div class="alert-title">🔔 Opporta Intelligence — document attention needed</div>'
                f'<div class="alert-meta" style="color:#94A3B8">{" · ".join(_parts)} — '
                f'upload renewed copies below so your bids stay valid.</div></div>',
                unsafe_allow_html=True)

        if _docs:
            st.markdown(f'<div class="sec-badge" style="display:inline-block;margin-bottom:12px">{len(_docs)} documents · feeding the engine</div>',
                        unsafe_allow_html=True)
            for _doc in _docs:
                _kb   = round(_doc.get("size_bytes", 0) / 1024, 1)
                _mime = _doc.get("mime_type", "")
                _icon = "📄" if "pdf" in _mime else "🖼️" if "image" in _mime else "📁"
                _up   = str(_doc.get("uploaded_at", ""))[:10]
                _dtype = str(_doc.get("doc_type") or "").lower()
                _usefulness = (
                    "Contractor eligibility evidence" if "license" in _dtype
                    else "Financial capacity evidence" if "capacity" in _dtype or "turnover" in _dtype or "tax" in _dtype
                    else "Job eligibility & resume matching" if "resume" in _dtype
                    else "Supporting bid evidence"
                )
                _stt  = _doc_expiry_status(_doc)
                if _stt:
                    _badge = (f'<span class="tag" style="flex-shrink:0;background:{_stt[1]}1a;'
                              f'color:{_stt[1]};border:1px solid {_stt[1]}55">{_stt[2]}</span>')
                else:
                    _badge = f'<span class="tag tag-cat" style="flex-shrink:0">{_mime.split("/")[-1].upper()[:8]}</span>'
                st.markdown(
                    f'<div class="doc-card"><div class="doc-icon">{_icon}</div>'
                    f'<div style="flex:1;min-width:0">'
                    f'<div class="doc-name">{_esc(_doc.get("name"))}</div>'
                    f'<div class="doc-meta">{_esc(_doc.get("filename"))} · {_kb} KB · {_up}</div>'
                    f'<div class="doc-meta" style="color:#38BDF8">Used for: {_usefulness}</div></div>'
                    f'{_badge}</div>', unsafe_allow_html=True)
        else:
            st.markdown("""<div class="ocard" style="text-align:center;padding:30px">
              <div style="font-size:1.8rem;margin-bottom:8px">📂</div>
              <div style="font-size:.86rem;color:#94A3B8;font-weight:600">Vault is empty</div>
              <div style="font-size:.76rem;color:#7C8AA0;margin-top:6px">Upload one document above to unlock personalized match scoring.</div>
            </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# ── FOOTER ────────────────────────────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""<div style="text-align:center;padding:48px 0 24px;color:#1E293B;font-size:.65rem;
  letter-spacing:.15em;font-weight:600;text-transform:uppercase;font-family:'JetBrains Mono',monospace">
  ⚡ OPPORTA · EVERY OPPORTUNITY · ONE PLATFORM · CG + UP<br>
  <a href="?page=privacy" style="color:#566179;text-decoration:none;font-size:.6rem">Privacy Policy</a>
  &nbsp;·&nbsp;
  <a href="?page=privacy" style="color:#566179;text-decoration:none;font-size:.6rem">Terms of Use</a>
</div>""", unsafe_allow_html=True)

# ── PRIVACY POLICY PAGE (accessible via ?page=privacy) ────────────────────────
_qp = st.query_params.get("page", "")
if _qp == "privacy":
    st.markdown("""
    <div style="max-width:800px;margin:0 auto;padding:40px 20px">
      <div style="font-size:.7rem;color:#00C4FF;font-weight:700;text-transform:uppercase;
           letter-spacing:.1em;margin-bottom:12px">⚡ Opporta</div>
      <h1 style="font-size:2rem;font-weight:900;color:#F1F5F9;margin-bottom:8px">Privacy Policy</h1>
      <p style="color:#7C8AA0;font-size:.8rem;margin-bottom:32px">Last updated: June 2026</p>

      <h2 style="font-size:1rem;color:#E2E8F0;font-weight:700;margin:24px 0 8px">1. What We Collect</h2>
      <p style="color:#64748B;font-size:.85rem;line-height:1.75">
        Opporta collects your email address and profile information (company name, qualifications,
        skills) that you voluntarily provide. We also collect documents you upload for job/tender
        eligibility analysis. Government tender and job data is sourced from public portals.
      </p>

      <h2 style="font-size:1rem;color:#E2E8F0;font-weight:700;margin:24px 0 8px">2. How We Use Your Data</h2>
      <p style="color:#64748B;font-size:.85rem;line-height:1.75">
        Your data is used solely to personalise your tender and job recommendations, score your
        eligibility, and send you alerts about matching opportunities. We do not sell, share, or
        disclose your personal information to third parties.
      </p>

      <h2 style="font-size:1rem;color:#E2E8F0;font-weight:700;margin:24px 0 8px">3. Data Security</h2>
      <p style="color:#64748B;font-size:.85rem;line-height:1.75">
        All data is stored securely in Supabase with Row Level Security (RLS) enforced at the
        database level. Only you can access your own profile, saved tenders, and uploaded documents —
        even Opporta administrators cannot view your private data.
      </p>

      <h2 style="font-size:1rem;color:#E2E8F0;font-weight:700;margin:24px 0 8px">4. Your Rights</h2>
      <p style="color:#64748B;font-size:.85rem;line-height:1.75">
        You may request deletion of your account and all associated data at any time by contacting
        us at <span style="color:#00C4FF">support@opporta.in</span>. You can also delete your
        uploaded documents directly from your Profile vault.
      </p>

      <h2 style="font-size:1rem;color:#E2E8F0;font-weight:700;margin:24px 0 8px">5. Contact</h2>
      <p style="color:#64748B;font-size:.85rem;line-height:1.75">
        For any privacy concerns, email us at
        <span style="color:#00C4FF">support@opporta.in</span>
      </p>

      <div style="margin-top:40px;padding-top:20px;border-top:1px solid rgba(255,255,255,.05);
           color:#566179;font-size:.7rem">
        © 2026 Opporta · Every Opportunity, One Platform · CG + UP
      </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()
