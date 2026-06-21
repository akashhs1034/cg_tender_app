"""
app.py -- OPPORTA  ·  Every Opportunity. One Platform.
Elite Intelligence OS for CG & UP Government Tenders & Jobs.
"""
from __future__ import annotations
import json, os
from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st
import core, accounts, evaluator
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
    "authenticated": False, "email": "", "sb_token": "",
    "current_page": "🏠  Dashboard",
    "explore_search": "", "explore_category": "All",
    "explore_state": "All", "explore_district": "All",
    "bid_tender": None,
    "entered_platform": False,
    "auth_mode": "login",       # "login" | "register" | "verify"
    "otp_email": "",
}.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v

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

/* AI Workspace */
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

/* Stray Streamlit cleanup */
div[data-testid="metric-container"]{background:#080F22;border:1px solid rgba(255,255,255,.06);border-radius:14px;padding:16px 20px}
div[data-testid="metric-container"] [data-testid="stMetricValue"]{color:#F1F5F9!important;font-weight:900!important;font-size:1.7rem!important}
div[data-testid="metric-container"] [data-testid="stMetricLabel"]{color:#7C8AA0!important;font-size:.7rem!important;text-transform:uppercase!important;letter-spacing:.08em!important}

/* ── Responsive Breakpoints ── */
@media (max-width:1200px){
  .kpi-grid{grid-template-columns:repeat(3,1fr)!important}
  .metric-row{grid-template-columns:repeat(2,1fr)!important}
}

/* ── Tablet (768px) ── */
@media (max-width:768px){
  .block-container{padding:0 .75rem 5rem!important}
  .kpi-grid{grid-template-columns:repeat(2,1fr)!important;gap:10px!important}
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
.google-btn{display:flex;align-items:center;justify-content:center;gap:10px;width:100%;padding:12px;background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.1);border-radius:12px;color:#E2E8F0;font-size:.85rem;font-weight:600;margin-bottom:16px;text-decoration:none;transition:all .2s}
.google-btn:hover{background:rgba(255,255,255,.09);border-color:rgba(255,255,255,.2)}
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

# ── HELPERS ───────────────────────────────────────────────────────────────────
def _secret(k):
    if k in os.environ: return os.environ[k]
    try: return st.secrets[k]
    except: return None

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
        except Exception as e:
            st.error(f"Supabase error on {name}: {e}")
    else:
        st.error(f"Supabase secrets not found. URL={'set' if url else 'MISSING'} KEY={'set' if key else 'MISSING'}")
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

def _render_ai_error(fallback: str = "AI service is unavailable right now — please try again.") -> None:
    """Show WHY the last AI call failed (quota vs. key vs. network) — not a generic error."""
    info = core.ai_error_message()
    if info:
        sev, txt = info
        (st.warning if sev == "warning" else st.error)(txt)
    else:
        st.error(fallback)

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
    t = _v(text, "Untitled")
    return t[:length] + ("..." if len(t) > length else "")

import re as _re, html as _html
def _esc(val, fallback="—") -> str:
    """Return HTML-escaped version of _v() — safe to embed in HTML templates."""
    return _html.escape(_v(val, fallback))

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
    df_t["category_bucket"] = df_t["category"].map(core.normalize_category)
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

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    _limg = f'<img src="{_LOGO_URI}" style="width:72px;height:72px;display:block;margin:0 auto 8px;border-radius:14px;box-shadow:0 0 24px rgba(0,196,255,.35)">' if _LOGO_URI else ''
    st.markdown(f"""
    <div class="sb-logo" style="text-align:center;padding:16px 16px 14px">
      {_limg}
      <div class="sb-brand"><span>Opporta</span></div>
      <div class="sb-tagline">Every Opportunity · One Platform</div>
    </div>""", unsafe_allow_html=True)

    if not st.session_state.authenticated:
        st.markdown('<div class="auth-panel">', unsafe_allow_html=True)
        st.markdown('<div class="auth-label">Secure Sign In</div>', unsafe_allow_html=True)
        auth_email = st.text_input("Email", key="auth_e",
                                   label_visibility="collapsed",
                                   placeholder="contractor@firm.com")
        auth_pw = st.text_input("Password", type="password", key="auth_pw",
                                label_visibility="collapsed",
                                placeholder="Password")
        c1, c2 = st.columns(2)
        if c1.button("Login", width="stretch"):
            ok, msg, token = accounts.login_user(auth_email, auth_pw)
            if ok:
                st.session_state.authenticated = True
                st.session_state.email    = auth_email.strip().lower()
                st.session_state.sb_token = token or ""
                st.rerun()
            elif msg in ("EMAIL_NOT_CONFIRMED", "RATE_LIMIT"):
                st.warning("📧 Please confirm your email (check inbox/spam), then log in — or wait a moment and retry.")
            else:
                st.error(msg)
        if c2.button("Register", width="stretch"):
            ok, msg = accounts.register_user(auth_email, auth_pw)
            if ok:
                lok, _lm, token = accounts.login_user(auth_email, auth_pw)
                if lok:
                    st.session_state.authenticated = True
                    st.session_state.email    = auth_email.strip().lower()
                    st.session_state.sb_token = token or ""
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
        st.markdown('<div class="sb-nav-label">Operational Modules</div>', unsafe_allow_html=True)
        # Exactly 5 primary modules. Analytics + Alerts fold into Dashboard,
        # the AI Workspace opens from a tender's detail, the Vault lives under Profile.
        pages = [
            "👤  Profile", "🏠  Dashboard", "🔍  Explore",
            "📄  Tenders", "💼  Jobs",
        ]
        for p in pages:
            is_active = st.session_state.current_page == p
            if st.button(p, width="stretch",
                         type="primary" if is_active else "secondary"):
                st.session_state.current_page = p
                st.rerun()

        st.markdown(f"""
        <div class="session-badge">
          <div class="session-live"><span class="live-dot"></span>SECURE SESSION</div>
          <div class="session-email">{st.session_state.email}</div>
        </div>""", unsafe_allow_html=True)

        if st.button("⏏  Log Out", width="stretch"):
            st.session_state.authenticated  = False
            st.session_state.email          = ""
            st.session_state.sb_token       = ""
            st.session_state.entered_platform = False
            st.session_state.auth_mode      = "login"
            st.rerun()

# ── GLOBAL CONTEXT ────────────────────────────────────────────────────────────
email    = st.session_state.email
_token   = st.session_state.get("sb_token", "")
profile  = accounts.get_profile(email, token=_token) if email else dict(core.DEFAULT_PROFILE)
if profile is None:
    profile = dict(core.DEFAULT_PROFILE)
cname = profile.get("company_name") or profile.get("full_name") or (
    email.split("@")[0].title() if email else "Guest")

# ── PROFILE READINESS GATE ────────────────────────────────────────────────────
# The matching engine must never hallucinate a score against empty telemetry.
# We only compute personalized scores once the user has real profile data OR at
# least one document in the secure vault. Until then every match = 0 / empty.
_vault_count = 0
if st.session_state.authenticated and email:
    try:
        _vault_count = len(accounts.list_documents(email, token=_token))
    except Exception:
        _vault_count = 0
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
                "title": f"New high-match ({s}%) — {safe_str(rec.get('title'), 62)}",
                "detail": (f"Clears your qualification bar · {_v(rec.get('category'),'General')}"
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
_scored_needed = ("Dashboard" in _cur_page) or ("Alerts" in _cur_page)
scored          = get_scored(df_t, profile) if (PROFILE_READY and _scored_needed) else []
eligible_count  = sum(1 for _, e, _, _ in scored if e)
high_conf_count = sum(1 for s, _, _, _ in scored if s >= 80)
closing_soon    = sum(1 for _, _, _, r in scored
                      if (dl := days_left(r.get("deadline"))) is not None and 0 <= dl <= 7)
total_value     = df_t["value_lakhs"].fillna(0).sum() if not df_t.empty and "value_lakhs" in df_t else 0

page = st.session_state.current_page

# ── MOBILE BOTTOM TAB BAR (fixed, thumb-friendly — visible only on phones) ─────
# Scoped via st.container(key=…) → wrapper gets class .st-key-mobilenav, which we
# pin to the bottom of the viewport in CSS. Hidden on desktop (sidebar takes over).
if st.session_state.authenticated:
    _bottom_items = [
        ("🏠", "Home",    "🏠  Dashboard"),
        ("🔍", "Explore", "🔍  Explore"),
        ("📄", "Tenders", "📄  Tenders"),
        ("💼", "Jobs",    "💼  Jobs"),
        ("👤", "You",     "👤  Profile"),
    ]
    _mnav = st.container(key="mobilenav")
    with _mnav:
        _mcols = st.columns(len(_bottom_items))
        for _col, (_icon, _lbl, _pg) in zip(_mcols, _bottom_items):
            _is_active = st.session_state.current_page == _pg
            # two trailing spaces + newline → markdown hard break → icon over label
            if _col.button(f"{_icon}  \n{_lbl}", key=f"bnav_{_pg}",
                           width="stretch",
                           type="primary" if _is_active else "secondary"):
                st.session_state.current_page = _pg
                st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# ── DASHBOARD ─────────────────────────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════
if "Dashboard" in page:
    if not st.session_state.authenticated:

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
              <div class="hero-eyebrow"><span class="hero-pulse"></span>OPPORTA INTELLIGENCE</div>
              <h1 class="hero-h1" style="font-size:clamp(1.8rem,4vw,3rem)">
                Welcome to Opporta
              </h1>
              <p class="hero-sub" style="margin-bottom:0">
                {len(df_t)} live tenders · {len(df_j)} open jobs today
              </p>
            </div>""", unsafe_allow_html=True)

            _ac, _sp = st.columns([1.4, 1])
            with _ac:
                # Google Sign-In is temporarily disabled while Google reviews/
                # verifies the app. Email + password (instant, no OTP) is the
                # active method. Re-enable Google once verification is approved.

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
                            ok, msg, token = accounts.login_user(_le, _lp)
                            if ok:
                                st.session_state.authenticated = True
                                st.session_state.email = _le.strip().lower()
                                st.session_state.sb_token = token or ""
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
                                lok, lmsg, token = accounts.login_user(_re, _rp)
                                if lok:
                                    st.session_state.authenticated = True
                                    st.session_state.email = _re.strip().lower()
                                    st.session_state.sb_token = token or ""
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

        # ── Briefing Banner ──
        st.markdown(f"""
        <div class="brief">
          <div class="brief-row">
            <div>
              <div class="brief-greeting">Good day, {cname} 👋</div>
              <div class="brief-sub">Intelligence briefing · {today_str}</div>
              <div class="brief-stats">
                <div class="bstat"><span class="live-dot"></span> Live Feed</div>
                <div class="bstat">🎯 <b>{len(scored)}</b> matched to you</div>
                <div class="bstat">✅ <b>{eligible_count}</b> you qualify for</div>
                <div class="bstat">🔥 <b>{high_conf_count}</b> high confidence</div>
                <div class="bstat">⏰ <b>{closing_soon}</b> closing in 7 days</div>
                <div class="bstat">💰 Total ₹<b>{total_value/100:.1f}Cr</b></div>
              </div>
            </div>
          </div>
        </div>""", unsafe_allow_html=True)

        # ── TELEMETRY GATE — no fabricated matches until profile/vault is set ──
        if not PROFILE_READY:
            st.markdown(f"""
            <div class="brief" style="border-color:rgba(245,158,11,.35);
                 background:linear-gradient(135deg,rgba(245,158,11,.06),rgba(0,196,255,.02))">
              <div class="brief-greeting" style="color:#F59E0B">⚠ Awaiting System Telemetry</div>
              <div class="brief-sub" style="margin-top:6px;max-width:640px">
                Opporta Intelligence has <b>not</b> generated match scores yet — your profile is empty.
                We never fabricate a fit score against missing data. Add your contractor class,
                sectors &amp; districts (or upload a document to the Vault) and the engine will
                calibrate every match to your verified capacity.
              </div>
            </div>""", unsafe_allow_html=True)
            _gt1, _gt2, _gt3 = st.columns([1, 1, 1])
            if _gt1.button("👤  Complete Profile Setup", width="stretch", key="gate_profile"):
                st.session_state.current_page = "👤  Profile"
                st.rerun()
            if _gt2.button("📄  Upload to Vault", width="stretch", key="gate_vault"):
                st.session_state.current_page = "👤  Profile"
                st.session_state["profile_tab"] = "vault"
                st.rerun()
            if _gt3.button("🔍  Browse Tenders Anyway", width="stretch", key="gate_browse"):
                st.session_state.current_page = "📄  Tenders"
                st.rerun()

        # ══════════════════════════════════════════════════════════════════════
        # SECTION 1 (already above): Greeting / Briefing banner
        # SECTION 2: Active-tender general information + live list
        # ══════════════════════════════════════════════════════════════════════

        # ── KPI Grid (general information) ──
        kpi_data = [
            (str(len(df_t)),           "Active Tenders",     "Live listings",       "📋", False),
            (str(len(df_j)),           "Open Jobs",          "Across CG + UP",      "💼", False),
            (str(eligible_count),      "You Qualify",        "Hard criteria pass",  "✅", False),
            (str(high_conf_count),     "High Confidence",    "Score ≥ 80",          "🎯", False),
            (str(closing_soon),        "Closing Soon",       "Within 7 days",       "⏰", True),
            (f"₹{total_value/100:.1f}Cr","Market Value",    "All active tenders",  "💰", False),
        ]
        cols = st.columns(6)
        for col, (num, lbl, sub, icon, warn) in zip(cols, kpi_data):
            sub_cls = "warn" if warn and int(closing_soon) > 0 else ""
            col.markdown(f"""<div class="kpi">
              <div class="kpi-icon">{icon}</div>
              <div class="kpi-num">{num}</div>
              <div class="kpi-lbl">{lbl}</div>
              <div class="kpi-sub {sub_cls}">{sub}</div>
            </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Active Tenders · Top matches list ──
        st.markdown("""<div class="sec-hd">
          <span class="sec-title">📋 Active Tenders</span>
          <span class="sec-badge-green">🎯 Matched to your profile</span>
          <div class="sec-divider"></div>
        </div>""", unsafe_allow_html=True)

        if scored:
            for s, eligible, reasons, rec in scored[:8]:
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
                      <div class="ocard-title">{safe_str(rec.get('title'))}</div>
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
                    if st.button("➕ Save to Pipeline", key=f"d_save_{rec.get('source_id')}"):
                        accounts.save_tender(email, rec.get("source_id"), token=_token)
                        st.toast("✓ Saved to pipeline")

            if st.button("📄  See all active tenders  →", width="stretch",
                         key="dash_see_all_tenders"):
                st.session_state.current_page = "📄  Tenders"
                st.rerun()
        elif not PROFILE_READY:
            st.markdown("""<div class="ocard" style="text-align:center;padding:36px">
              <div style="font-size:2rem;margin-bottom:12px">📡</div>
              <div style="font-size:.9rem;font-weight:700;color:#94A3B8">Awaiting profile telemetry</div>
              <div style="font-size:.78rem;color:#64748B;margin-top:6px;line-height:1.6">Match scores are intentionally blank until you configure your profile.<br>No data in → no fabricated scores out.</div>
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
            for _al in _alerts[:6]:
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
        if _tl2.button("⚡  AI Tender Analyzer", width="stretch", key="dash_open_ws"):
            st.session_state.current_page = "⚡  Opporta Workspace"
            st.rerun()
        if _tl3.button("📄  My Document Vault", width="stretch", key="dash_open_vault"):
            st.session_state.current_page = "👤  Profile"
            st.session_state["profile_tab"] = "vault"
            st.rerun()

        # ══════════════════════════════════════════════════════════════════════
        # SECTION 4: Latest Government Jobs
        # ══════════════════════════════════════════════════════════════════════
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""<div class="sec-hd">
          <span class="sec-title">💼 Latest Government Jobs</span>
          <span class="sec-badge">CG + UP</span>
          <div class="sec-divider"></div>
        </div>""", unsafe_allow_html=True)

        if not df_j.empty:
            for _jr in df_j.head(6).to_dict("records"):
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
        # SECTION 5: BID WORKSHOP — upload firm docs + tender doc → ready-to-bid file
        # ══════════════════════════════════════════════════════════════════════
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""<div class="sec-hd">
          <span class="sec-title">🛠 Bid Workshop</span>
          <span class="sec-badge-green">Ready-to-Bid File Generator</span>
          <div class="sec-divider"></div>
        </div>""", unsafe_allow_html=True)

        with st.expander("⚡  Generate a Ready-to-Bid file  —  upload your firm documents + the tender document", expanded=False):
            _ws_ai = bool(
                os.getenv("GEMINI_API_KEY") or _secret("GEMINI_API_KEY") or
                os.getenv("ANTHROPIC_API_KEY") or _secret("ANTHROPIC_API_KEY"))
            if not _ws_ai:
                st.warning("⚡ Opporta Intelligence needs GEMINI_API_KEY (or ANTHROPIC_API_KEY) to read the tender and draft the bid. Add it to your secrets to enable generation.")

            st.markdown("**Step 1 — Tender document** (the NIT / tender notice PDF)")
            _ws_tender = st.file_uploader("Tender document", type=["pdf", "jpg", "jpeg", "png"],
                                          key="ws_tender_doc", label_visibility="collapsed")

            st.markdown("**Step 2 — Your firm documents** (GST, registration, experience, turnover — optional but recommended)")
            _ws_firm = st.file_uploader("Firm documents", type=["pdf", "txt", "jpg", "jpeg", "png"],
                                        accept_multiple_files=True, key="ws_firm_docs",
                                        label_visibility="collapsed")

            if st.button("⚡  Generate Ready-to-Bid File", width="stretch", key="ws_generate"):
                if not _ws_tender:
                    st.warning("Upload the tender document first.")
                elif not _ws_ai:
                    st.error("AI key not configured — cannot read the tender. Add GEMINI_API_KEY to secrets.")
                else:
                    import bid_engine
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
                    with st.spinner("Opporta Intelligence is reading the tender, checking your readiness & drafting the bid…"):
                        _ws_t   = bid_engine.extract_tender(_ws_tender.read(),
                                                            _ws_tender.type or "application/pdf")
                        _ws_chk = bid_engine.readiness_check(_ws_t, profile, _ws_firm_texts)
                        _ws_bid = bid_engine.generate_bid_content(_ws_t, profile, _ws_firm_texts)
                        _ws_docx = bid_engine.build_docx(_ws_bid, _ws_t, profile) if _ws_bid else None

                    if _ws_t.get("_extraction_failed"):
                        # Show the precise reason (quota / key / network) when we have it.
                        if core.ai_error_message():
                            _render_ai_error()
                        else:
                            st.error("Could not read the tender document automatically. Try a clearer PDF, or use the AI Tender Analyzer to enter details manually.")
                    else:
                        st.success(f"✓ Bid drafted for: {safe_str(_ws_t.get('title'), 90)}")
                        # Readiness summary (uses real profile + uploaded firm docs only)
                        _rp = _ws_chk.get("overall_pct", 0)
                        st.markdown(
                            f'<div class="elig-{"yes" if _rp>=70 else "partial" if _rp>=40 else "no"}" '
                            f'style="margin:8px 0 12px">Readiness {_rp}% · '
                            f'{len(_ws_chk.get("met",[]))} met · {len(_ws_chk.get("missing",[]))} missing</div>',
                            unsafe_allow_html=True)
                        for _w in _ws_chk.get("warnings", [])[:4]:
                            st.caption(f"⚠ {_w}")
                        if _ws_docx:
                            st.download_button(
                                "📥  Download Ready-to-Bid File (.docx)",
                                data=_ws_docx,
                                file_name=f"OPPORTA_Bid_{safe_str(_ws_t.get('tender_no') or _ws_t.get('title'),'tender')[:30].replace(' ','_')}.docx",
                                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                width="stretch", key="ws_download")
                        else:
                            _render_ai_error("Bid drafting did not return content — please try again.")

# ══════════════════════════════════════════════════════════════════════════════
# ── EXPLORE — general system discovery (unified search: tenders + jobs) ────────
# ══════════════════════════════════════════════════════════════════════════════
elif "Explore" in page:
    st.markdown("""<div class="sec-hd">
      <span class="sec-title">🔍 Explore</span>
      <span class="sec-badge">Unified discovery</span>
      <div class="sec-divider"></div>
    </div>""", unsafe_allow_html=True)

    _xq = st.text_input("Search everything", value="",
                        placeholder="Search across all tenders & jobs — keyword, organisation, district…",
                        label_visibility="collapsed", key="explore_global_q")
    _xql = _xq.strip().lower()

    _t_hits, _j_hits = [], []
    if _xql:
        if not df_t.empty:
            for _, _r in df_t.iterrows():
                _rec = _r.to_dict()
                _hay = (f"{_v(_rec.get('title'))} {_v(_rec.get('organization'))} "
                        f"{_v(_rec.get('district'))} {_v(_rec.get('category'))} "
                        f"{_v(_rec.get('state'))}").lower()
                if _xql in _hay:
                    _t_hits.append(_rec)
        if not df_j.empty:
            for _, _r in df_j.iterrows():
                _rec = _r.to_dict()
                _hay = (f"{_v(_rec.get('title'))} {_v(_rec.get('department'))} "
                        f"{_v(_rec.get('category'))} {_v(_rec.get('state'))}").lower()
                if _xql in _hay:
                    _j_hits.append(_rec)

    if _xql:
        st.markdown(
            f'<div class="brief-stats" style="margin:4px 0 18px">'
            f'<div class="bstat">📄 <b>{len(_t_hits)}</b> tenders</div>'
            f'<div class="bstat">💼 <b>{len(_j_hits)}</b> jobs</div>'
            f'</div>', unsafe_allow_html=True)

        if _t_hits:
            st.markdown('<div class="profile-section-title">📄 Tender matches</div>', unsafe_allow_html=True)
            for _rec in _t_hits[:6]:
                _val = _v(_rec.get("value_text")) or (
                    f"₹{float(_rec.get('value_lakhs',0)):.0f}L" if _rec.get("value_lakhs") else "—")
                st.markdown(
                    f'<div class="ocard"><div class="ocard-title">{_html.escape(safe_str(_rec.get("title"),100))}</div>'
                    f'<div class="ocard-org">🏛 {_esc(_rec.get("organization"))} · {_esc(_rec.get("state"))}</div>'
                    f'<div class="ocard-tags"><span class="tag tag-val">💰 {_html.escape(_val)}</span>'
                    f'<span class="tag tag-loc">📍 {_esc(_rec.get("district"),"State-wide")}</span>'
                    f'<span class="tag tag-cat">{_esc(_rec.get("category"),"General")}</span></div></div>',
                    unsafe_allow_html=True)
            if st.button("📄  Open full Tender Portal  →", width="stretch", key="exp_to_tenders"):
                st.session_state.explore_search = _xql
                st.session_state.current_page = "📄  Tenders"
                st.rerun()

        if _j_hits:
            st.markdown('<div class="profile-section-title" style="margin-top:18px">💼 Job matches</div>', unsafe_allow_html=True)
            for _rec in _j_hits[:6]:
                _vac = _v(_rec.get("vacancies"))
                _vb = f'<div class="jvac">{_vac} posts</div>' if _vac not in ("—","") else ''
                st.markdown(
                    f'<div class="jcard"><div class="jcard-row"><div class="jcard-body">'
                    f'<div class="jcard-title">{_html.escape(safe_str(_rec.get("title"),95))}</div>'
                    f'<div class="jcard-dept">🏛 {_esc(_rec.get("department"))} · {_esc(_rec.get("state"))}</div>'
                    f'</div>{_vb}</div></div>', unsafe_allow_html=True)
            if st.button("💼  Open full Job Board  →", width="stretch", key="exp_to_jobs"):
                st.session_state.current_page = "💼  Jobs"
                st.rerun()

        if not _t_hits and not _j_hits:
            st.info("No tenders or jobs match that search. Try a broader keyword.")
    else:
        # No query → discovery shortcuts built from the REAL top categories,
        # so every chip is guaranteed to return tenders.
        st.caption("Jump straight into a category, or open a dedicated portal.")
        _disc = [(_emoji_for(_c), _c) for _c in TENDER_CATS_BY_FREQ[:8]]
        if _disc:
            _dc = st.columns(4)
            for _i, (_em, _nm) in enumerate(_disc):
                if _dc[_i % 4].button(f"{_em}  {_nm}", width="stretch", key=f"disc_{_nm}"):
                    st.session_state.explore_category = _nm
                    st.session_state.current_page = "📄  Tenders"
                    st.rerun()
        st.markdown("<br>", unsafe_allow_html=True)
        _pc1, _pc2 = st.columns(2)
        if _pc1.button("📄  Tender Portal", width="stretch", key="exp_portal_t"):
            st.session_state.current_page = "📄  Tenders"; st.rerun()
        if _pc2.button("💼  Job Board", width="stretch", key="exp_portal_j"):
            st.session_state.current_page = "💼  Jobs"; st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# ── TENDERS — dedicated portal w/ multi-tier cascading filters ─────────────────
# ══════════════════════════════════════════════════════════════════════════════
elif "Tenders" in page:
    st.markdown("""<div class="sec-hd">
      <span class="sec-title">📄 Tender Portal</span>
      <span class="sec-badge">Category › State › District</span>
      <div class="sec-divider"></div>
    </div>""", unsafe_allow_html=True)

    # Category options = clean buckets present in the data (by frequency).
    all_cats = ["All"] + [c for c in TENDER_CATS_BY_FREQ]

    # Filters
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
        # Dynamic district list based on selected state
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
    st.markdown('</div>', unsafe_allow_html=True)

    # Apply filters
    q    = st.session_state.explore_search
    fcat = st.session_state.explore_category
    fst  = st.session_state.explore_state
    fdst = st.session_state.explore_district

    rows = []
    for _, r in df_t.iterrows():
        rec      = r.to_dict()
        haystack = f"{_v(rec.get('title'))} {_v(rec.get('organization'))} {_v(rec.get('district'))} {_v(rec.get('description'))}".lower()
        if q and q not in haystack: continue
        if fst  != "All" and _v(rec.get("state")) != fst: continue
        if fcat != "All" and rec.get("category_bucket") != fcat: continue
        if fdst != "All" and _v(rec.get("district","")).lower() != fdst.lower(): continue
        if PROFILE_READY:
            s, _, eligible = core.score_tender_for_user(rec, profile)
            rows.append((s, eligible, rec))
        else:
            # No verified telemetry → show neutral market score, never a fit verdict.
            rows.append((int(rec.get("ai_score") or 0), None, rec))

    rows.sort(key=lambda x: x[0], reverse=True)

    # Results header
    count_col, _ = st.columns([1, 3])
    with count_col:
        st.markdown(f'<div class="sec-badge" style="display:inline-block;margin-bottom:18px">{len(rows)} results found</div>',
                    unsafe_allow_html=True)

    if not st.session_state.authenticated:
        st.info("🔐 Sign in to see your personalized Opporta Intelligence fit score for each tender.")
    elif not PROFILE_READY:
        st.info("📡 Showing neutral market scores. Complete your Profile (or upload a vault document) to unlock personalized eligibility & fit scoring.")

    if not rows:
        st.markdown("""<div class="ocard" style="text-align:center;padding:40px;color:#7C8AA0">
          <div style="font-size:2rem;margin-bottom:12px">🔍</div>
          <div style="font-size:.9rem;font-weight:600;color:#64748B">No tenders match your filters</div>
          <div style="font-size:.77rem;color:#566179;margin-top:6px">Try broadening your search or changing the state/district</div>
        </div>""", unsafe_allow_html=True)

    for s, eligible, rec in rows[:80]:
        rc       = ring_cls(s)
        dl       = days_left(rec.get("deadline"))
        dl_txt   = f"⏱ {dl}d left" if dl is not None and dl >= 0 else ("⚠ Expired" if dl is not None else "No deadline")
        val      = _v(rec.get("value_text")) or (f"₹{float(rec.get('value_lakhs',0)):.0f}L" if rec.get("value_lakhs") else "—")
        district = _v(rec.get("district"), "State-wide")
        color    = score_color(s)
        if eligible is None:
            # No profile/resume → STRICTLY no percentage shown at all.
            elig_cls, elig_txt = "tag-cat", "🔒 Complete profile for fit score"
            ring_html = ""
        else:
            elig_cls, elig_txt = ("tag-green", "✅ Eligible") if eligible else ("tag-warn", "⚠ Review")
            ring_html = f'<div class="ring {rc}" style="color:{color};border-color:{color}">{s}</div>'

        st.markdown(f"""<div class="ocard">
          <div class="ocard-row">
            <div class="ocard-body">
              <div class="ocard-title">{safe_str(rec.get('title'), 115)}</div>
              <div class="ocard-org">🏛 {safe_str(rec.get('organization'), 55)} &nbsp;·&nbsp; {_v(rec.get('state'))}</div>
              <div class="ocard-tags">
                <span class="tag tag-val">💰 {val}</span>
                <span class="tag tag-dl">{dl_txt}</span>
                <span class="tag tag-loc">📍 {district}</span>
                <span class="tag tag-cat">{_v(rec.get('category'), 'General')}</span>
                <span class="tag {elig_cls}">{elig_txt}</span>
              </div>
            </div>
            {ring_html}
          </div>
        </div>""", unsafe_allow_html=True)

        with st.expander(f"Details · Save — {safe_str(rec.get('title'), 55)}"):
            dc1, dc2 = st.columns(2)
            dc1.write(f"**Organization:** {_v(rec.get('organization'))}")
            dc1.write(f"**Category:** {_v(rec.get('category'))}")
            dc1.write(f"**District:** {district}")
            dc1.write(f"**State:** {_v(rec.get('state'))}")
            dc2.write(f"**Estimated Value:** {val}")
            dc2.write(f"**Deadline:** {_v(rec.get('deadline'))}")
            dc2.write(f"**Contractor Class:** {_v(rec.get('contractor_class'))}")
            if rec.get("description"):
                st.write(_v(rec.get("description")))
            doc_url = rec.get("document_url")
            if doc_url and str(doc_url) not in ("nan","None","—",""):
                _pdf_widget(doc_url, rec.get("source_id",""), ctx="exp")
            if st.session_state.authenticated:
                _sv, _an = st.columns(2)
                if _sv.button("➕ Save to Pipeline", key=f"e_save_{rec.get('source_id')}"):
                    accounts.save_tender(email, rec.get("source_id"), token=_token)
                    st.toast("✓ Saved to your pipeline")
                if _an.button("⚡ Analyze with AI", key=f"e_an_{rec.get('source_id')}"):
                    st.session_state["ws_prefill"] = safe_str(rec.get("title"), 110)
                    st.session_state.current_page = "⚡  Opporta Workspace"
                    st.rerun()

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
# ── AI WORKSPACE ──────────────────────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════
elif "Workspace" in page:
    if not st.session_state.authenticated:
        st.markdown("""<div class="ocard" style="text-align:center;padding:40px">
          <div style="font-size:2rem;margin-bottom:12px">🔐</div>
          <div style="font-size:.9rem;font-weight:600;color:#64748B">Sign in to access Opporta Workspace</div>
        </div>""", unsafe_allow_html=True)
        st.stop()

    # Prefill the evaluator search when arriving from a tender's "Analyze with AI".
    if "ws_prefill" in st.session_state:
        st.session_state["eval_search_q"] = st.session_state.pop("ws_prefill")

    has_ai = bool(
        os.getenv("GEMINI_API_KEY") or _secret("GEMINI_API_KEY") or
        os.getenv("ANTHROPIC_API_KEY") or _secret("ANTHROPIC_API_KEY")
    )

    st.markdown("""<div class="terminal-hd">
      <div class="terminal-label">⚡ OPPORTA WORKSPACE · Opporta Intelligence</div>
      <div class="terminal-title">Tender Evaluator · Resume Analyzer · Bid Drafter</div>
      <div class="terminal-sub">We evaluate your documents, score eligibility, and draft bid paperwork — accurate analysis, no outcome guarantees.</div>
    </div>""", unsafe_allow_html=True)

    st.markdown(
        '<div style="background:rgba(0,196,255,.05);border:1px solid rgba(0,196,255,.15);border-radius:10px;'
        'padding:10px 16px;font-size:.75rem;color:#64748B;margin-bottom:18px;line-height:1.6">'
        '&#9432;&nbsp; <b style="color:#38BDF8">What Opporta Workspace does:</b> evaluates tender documents against '
        'your profile, scores 6 key dimensions, checks document readiness, drafts bid paperwork. &nbsp;'
        '<b style="color:#F59E0B">What it does not do:</b> predict award outcomes or guarantee you will win the tender. '
        'Final award decisions are made solely by the government authority.'
        '</div>',
        unsafe_allow_html=True)

    if not has_ai:
        st.info("⚡ Add GEMINI_API_KEY to .env to enable Opporta Intelligence document reading. Rule-based scoring is active.")

    tab1, tab2, tab3 = st.tabs(["🔍  Tender Evaluator", "📄  Resume Analyzer", "📝  Bid Drafter"])

    # ── Tab 1: AI Tender Evaluator ─────────────────────────────────────────────
    with tab1:
        st.markdown("""<div class="sec-hd">
          <span class="sec-title">Tender Document Evaluator</span>
          <span class="sec-badge">Eligibility &amp; Document Scoring</span>
          <div class="sec-divider"></div>
        </div>""", unsafe_allow_html=True)

        if df_t.empty:
            st.warning("No tender data available. Run ingest.py first.")
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
            st.warning("No job data available. Run ingest.py first.")
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
            st.warning("⚡ Add GEMINI_API_KEY to .env to enable Opporta Intelligence extraction and bid generation.")

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
                st.info("Add GEMINI_API_KEY to .env to enable Opporta Intelligence bid drafting.")
            else:
                st.caption("⚠️ This drafts a bid document template based on your inputs. Review, verify, and sign before official submission. Opporta does not guarantee tender award.")
                if st.button("📝 Draft Bid Document (.docx)", width="stretch", key="bid_gen"):
                    core.clear_ai_error()
                    with st.spinner("Drafting bid document — this takes ~30 seconds..."):
                        bid_content = bid_engine.generate_bid_content(
                            st.session_state.bid_tender, profile, vault_texts)
                    if bid_content:
                        with st.spinner("Compiling Word document..."):
                            docx_bytes = bid_engine.build_docx(
                                bid_content, st.session_state.bid_tender, profile)
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
    st.markdown("""<div class="sec-hd">
      <span class="sec-title">💼 Government Job Board</span>
      <div class="sec-divider"></div>
    </div>""", unsafe_allow_html=True)

    jtab1, jtab2 = st.tabs(["💼  Active Job Board", "🏛  Upcoming Exams & Study Matrix"])

    # ── TAB 1: Active Job Board (live grid + filters) ──
    with jtab1:
        if df_j.empty:
            st.markdown("""<div class="ocard" style="text-align:center;padding:40px">
              <div style="font-size:2rem;margin-bottom:12px">💼</div>
              <div style="font-size:.9rem;color:#64748B">No job data. Run ingest.py to fetch live listings.</div>
            </div>""", unsafe_allow_html=True)
        else:
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

            # Job filters
            st.markdown('<div class="filter-row">', unsafe_allow_html=True)
            jf1, jf2, jf3 = st.columns([3, 1.5, 1.5])
            with jf1:
                jsearch = st.text_input("Search jobs", placeholder="Title, department, qualification...",
                                        label_visibility="collapsed", key="jsearch").lower()
            with jf2:
                jstates = ["All", "Chhattisgarh", "Uttar Pradesh"]
                jstate  = st.selectbox("State", jstates, label_visibility="collapsed", key="jstate")
            with jf3:
                jcats = ["All"] + sorted(df_j["category"].dropna().unique().tolist()) if "category" in df_j else ["All"]
                jcat  = st.selectbox("Category", jcats, label_visibility="collapsed", key="jcat")
            st.markdown('</div>', unsafe_allow_html=True)

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
                jobs_filtered.append(rec)

            st.markdown(f'<div class="sec-badge" style="display:inline-block;margin-bottom:16px">{len(jobs_filtered)} postings</div>',
                        unsafe_allow_html=True)

            # Strict: show a match % ONLY when a real job-seeker profile exists.
            _job_prof_text = (_profile_to_resume_text(profile)
                              if (st.session_state.authenticated and _has_job_profile(profile))
                              else "")
            if st.session_state.authenticated and not _job_prof_text:
                st.info("📡 Add your qualification, degree or skills in Profile → Job Seeker to unlock your match % for every job.")

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
                    f'{sal_tag}'
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

                        # Optional resume upload for deeper AI analysis
                        resume_up = st.file_uploader("Upload resume for Opporta Intelligence analysis (optional)",
                                                     type=["pdf","txt"],
                                                     key=f"jr_{rec.get('source_id')}")
                        if resume_up:
                            rtext = (_read_pdf_text(resume_up)
                                     if resume_up.name.lower().endswith(".pdf")
                                     else resume_up.read().decode("utf-8", errors="ignore"))
                            if st.button("⚡ Deep Analysis", key=f"jra_{rec.get('source_id')}"):
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

    # ── TAB 2: Upcoming Exams & Study Matrix (verified authorities) ──
    with jtab2:
        st.markdown(
            '<div class="portal-intro"><b>Official commissions, exam calendars &amp; study material.</b> '
            '<span>Every recruitment authority below is the authoritative source for exam '
            'notifications, schedules, admit cards, syllabi, previous papers and results. Each '
            'link opens the official portal in a new browser tab.</span></div>', unsafe_allow_html=True)
        for _region, _items in RECRUITMENT_AUTHORITIES.items():
            _portal_region(_region, "Notifications · schedules · admit cards · results", _items, cols=2)

# ══════════════════════════════════════════════════════════════════════════════
# ── DOCUMENTS ─────────────────────────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════
elif "Documents" in page:
    if not st.session_state.authenticated:
        st.warning("Sign in to access your secure document vault.")
        st.stop()

    st.markdown("""<div class="sec-hd">
      <span class="sec-title">📄 Secure Document Vault</span>
      <span class="sec-badge-green">Encrypted</span>
      <div class="sec-divider"></div>
    </div>""", unsafe_allow_html=True)

    with st.expander("⬆️ Upload New Document", expanded=True):
        up1, up2 = st.columns(2)
        with up1:
            doc_name = st.text_input("Document label",
                                     placeholder="e.g. GST Registration, Experience Certificate")
        with up2:
            doc_file = st.file_uploader("Select file", type=["pdf","jpg","jpeg","png","txt"],
                                        key="vault_upload")
        if st.button("⬆️ Upload to Vault", width="stretch") and doc_file and doc_name:
            with st.spinner("Uploading securely..."):
                doc_id = accounts.save_document(email, doc_name, doc_file.name,
                                                doc_file.read(), doc_file.type or "application/octet-stream",
                                                token=_token)
            if doc_id:
                st.success(f"✓ '{doc_name}' uploaded successfully.")
                st.rerun()
            else:
                st.error("Upload failed. Check console logs.")

    st.markdown("""<div class="sec-hd" style="margin-top:28px">
      <span class="sec-title">My Documents</span>
      <div class="sec-divider"></div>
    </div>""", unsafe_allow_html=True)

    docs = accounts.list_documents(email, token=_token)
    if docs:
        st.markdown(f'<div class="sec-badge" style="display:inline-block;margin-bottom:14px">{len(docs)} documents</div>',
                    unsafe_allow_html=True)
        for doc in docs:
            size_kb = round(doc.get("size_bytes", 0) / 1024, 1)
            mime    = doc.get("mime_type","")
            icon    = "📄" if "pdf" in mime else "🖼️" if "image" in mime else "📁"
            uploaded = str(doc.get("uploaded_at",""))[:10]
            st.markdown(f"""<div class="doc-card">
              <div class="doc-icon">{icon}</div>
              <div style="flex:1;min-width:0">
                <div class="doc-name">{doc.get('name','—')}</div>
                <div class="doc-meta">{doc.get('filename','—')} &nbsp;·&nbsp; {size_kb} KB &nbsp;·&nbsp; {uploaded}</div>
              </div>
              <span class="tag tag-cat" style="flex-shrink:0">{mime.split('/')[-1].upper()[:8]}</span>
            </div>""", unsafe_allow_html=True)
    else:
        st.markdown("""<div class="ocard" style="text-align:center;padding:36px">
          <div style="font-size:2rem;margin-bottom:12px">📂</div>
          <div style="font-size:.88rem;color:#64748B">No documents uploaded yet</div>
          <div style="font-size:.76rem;color:#566179;margin-top:6px">
            Upload your GST cert, experience proofs, contractor registration, and bid documents above.
          </div>
        </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# ── ALERTS ────────────────────────────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════
elif "Alerts" in page:
    if not st.session_state.authenticated:
        st.warning("Sign in to view your alert history.")
        st.stop()

    st.markdown("""<div class="sec-hd">
      <span class="sec-title">🔔 Smart Pipeline Alerts</span>
      <span class="sec-badge">Deadlines &amp; new high-matches only</span>
      <div class="sec-divider"></div>
    </div>""", unsafe_allow_html=True)

    # Live, calibrated alerts (same engine as the Dashboard panel).
    _live = compute_smart_alerts(email, _token, scored, df_t)
    if _live:
        for _al in _live:
            st.markdown(
                f'<div class="alert-item" style="border-left-color:{_al["color"]}">'
                f'<div class="alert-title">{_al["icon"]} {_html.escape(_al["title"])}</div>'
                f'<div class="alert-meta" style="color:#94A3B8">{_html.escape(_al["detail"])}</div>'
                f'</div>', unsafe_allow_html=True)
    else:
        st.markdown("""<div class="ocard" style="text-align:center;padding:26px">
          <div style="font-size:1.5rem;margin-bottom:6px">🔕</div>
          <div style="font-size:.84rem;color:#94A3B8;font-weight:600">No critical alerts right now</div>
          <div style="font-size:.74rem;color:#7C8AA0;margin-top:4px">Save tenders to your pipeline and complete your profile to receive deadline & high-match alerts.</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("""<div class="sec-hd" style="margin-top:30px">
      <span class="sec-title">📧 Dispatch History</span>
      <div class="sec-divider"></div>
    </div>""", unsafe_allow_html=True)

    log_path = Path(__file__).parent / "data" / "alert_log.json"
    user_logs = []
    if log_path.exists():
        try:
            all_logs  = json.loads(log_path.read_text(encoding="utf-8"))
            user_logs = [e for e in all_logs if e.get("email","").lower() == email.lower()]
        except Exception: pass

    if user_logs:
        tender_lookup = ({r["source_id"]: r for _, r in df_t.iterrows()}
                         if not df_t.empty else {})
        st.markdown(f'<div class="sec-badge" style="display:inline-block;margin-bottom:16px">{len(user_logs)} alerts dispatched</div>',
                    unsafe_allow_html=True)

        for entry in sorted(user_logs, key=lambda x: x.get("sent_at",""), reverse=True)[:50]:
            sid    = entry.get("source_id","")
            tender = tender_lookup.get(sid, {})
            title  = safe_str(tender.get("title") or sid, 90)
            sent   = str(entry.get("sent_at",""))[:10]
            org    = _v(tender.get("organization"))
            rtype  = entry.get("record_type","tender").title()
            st.markdown(f"""<div class="alert-item">
              <div class="alert-title">{title}</div>
              <div style="font-size:.73rem;color:#7C8AA0;margin:4px 0 8px">{org}</div>
              <div class="ocard-tags">
                <span class="tag tag-dl">📧 Sent {sent}</span>
                <span class="tag tag-cat">{rtype}</span>
              </div>
            </div>""", unsafe_allow_html=True)
    else:
        st.markdown("""<div class="ocard" style="text-align:center;padding:40px">
          <div style="font-size:2rem;margin-bottom:12px">🔔</div>
          <div style="font-size:.9rem;color:#64748B;font-weight:600">No alerts sent yet</div>
          <div style="font-size:.77rem;color:#566179;margin-top:8px;line-height:1.6">
            Alerts are emailed each time the pipeline runs and finds new matches for your profile.<br>
            Complete your Profile → add RESEND_API_KEY to .env → run: <code>python ingest.py</code>
          </div>
        </div>""", unsafe_allow_html=True)

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
        st.markdown(f'<div class="chart-card"><div class="chart-title">{title}</div></div>',
                    unsafe_allow_html=True)
        st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})

    st.markdown("""<div class="sec-hd">
      <span class="sec-title">📊 Market Intelligence</span>
      <div class="sec-divider"></div>
    </div>""", unsafe_allow_html=True)

    if df_t.empty:
        st.warning("No data available. Run ingest.py first.")
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
            st.markdown('</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# ── PROFILE ───────────────────────────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════
elif "Profile" in page:
    if not st.session_state.authenticated:
        st.warning("Sign in to access your profile.")
        st.stop()

    st.markdown("""<div class="sec-hd">
      <span class="sec-title">👤 My Profile</span>
      <div class="sec-divider"></div>
    </div>""", unsafe_allow_html=True)

    if not PROFILE_READY:
        st.info("📡 Your profile is empty — Opporta Intelligence is holding all match scores at 0 until you save real data here or upload a document to the Vault.")

    ptab1, ptab2, ptab3 = st.tabs(
        ["🏢  Contractor Profile", "👤  Job Seeker Profile", "📄  Document Vault"])

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
                   "Uploaded files are parsed and fed into Opporta Intelligence to calibrate your match scores.")

        _vc1, _vc2 = st.columns([2, 1])
        with _vc1:
            _vault_label = st.text_input("Document label", key="vault_label",
                                         placeholder="e.g. Contractor License (Class A), GST Certificate, Resume")
        with _vc2:
            _vault_kind = st.selectbox("Type", ["License", "Capacity Cert", "Resume",
                                                "Tax / Turnover", "Other"], key="vault_kind")
        _vault_file = st.file_uploader("Select file", type=["pdf", "jpg", "jpeg", "png", "txt", "docx"],
                                       key="vault_file_up")

        if st.button("⬆️  Upload to Vault & Index", width="stretch", key="vault_do_upload"):
            if _vault_file and _vault_label:
                _raw = _vault_file.read()
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
                        _raw, _vault_file.type or "application/octet-stream", token=_token)
                if _did:
                    if _parsed.strip():
                        st.success(f"✓ Uploaded & parsed {len(_parsed):,} characters — "
                                   f"telemetry unlocked, match scoring is now active.")
                    else:
                        st.success("✓ Uploaded. Telemetry unlocked — match scoring is now active.")
                    st.rerun()
                else:
                    st.error("Upload failed. Check logs.")
            else:
                st.warning("Add a label and choose a file first.")

        st.markdown('<div class="profile-section-title" style="margin-top:22px">Stored Documents</div>',
                    unsafe_allow_html=True)
        _docs = accounts.list_documents(email, token=_token)
        if _docs:
            st.markdown(f'<div class="sec-badge" style="display:inline-block;margin-bottom:12px">{len(_docs)} documents · feeding the engine</div>',
                        unsafe_allow_html=True)
            for _doc in _docs:
                _kb   = round(_doc.get("size_bytes", 0) / 1024, 1)
                _mime = _doc.get("mime_type", "")
                _icon = "📄" if "pdf" in _mime else "🖼️" if "image" in _mime else "📁"
                _up   = str(_doc.get("uploaded_at", ""))[:10]
                st.markdown(
                    f'<div class="doc-card"><div class="doc-icon">{_icon}</div>'
                    f'<div style="flex:1;min-width:0">'
                    f'<div class="doc-name">{_esc(_doc.get("name"))}</div>'
                    f'<div class="doc-meta">{_esc(_doc.get("filename"))} · {_kb} KB · {_up}</div></div>'
                    f'<span class="tag tag-cat" style="flex-shrink:0">{_mime.split("/")[-1].upper()[:8]}</span>'
                    f'</div>', unsafe_allow_html=True)
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

      <h2 style="font-size:1rem;color:#E2E8F0;font-weight:700;margin:24px 0 8px">4. Google Sign-In</h2>
      <p style="color:#64748B;font-size:.85rem;line-height:1.75">
        If you sign in with Google, we receive your name and email address from Google. We do not
        access your Google contacts, Gmail, Drive, or any other Google data.
      </p>

      <h2 style="font-size:1rem;color:#E2E8F0;font-weight:700;margin:24px 0 8px">5. Your Rights</h2>
      <p style="color:#64748B;font-size:.85rem;line-height:1.75">
        You may request deletion of your account and all associated data at any time by contacting
        us at <span style="color:#00C4FF">support@opporta.in</span>. You can also delete your
        uploaded documents directly from the Documents section.
      </p>

      <h2 style="font-size:1rem;color:#E2E8F0;font-weight:700;margin:24px 0 8px">6. Contact</h2>
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
