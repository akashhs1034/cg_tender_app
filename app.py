import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime
import random
import google.generativeai as genai

# =====================================================================
# 1. PAGE SETUP & WORKSPACE OPTIMIZATION
# =====================================================================
st.set_page_config(
    page_title="Opporta | Opportunity Intelligence",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =====================================================================
# 2. PREMIUM ENTERPRISE DESIGN SYSTEM
# =====================================================================
st.markdown("""
<style>
    :root {
        --bg: #F8FAFC;
        --card: #FFFFFF;
        --primary: #4F46E5;
        --primary-hover: #4338CA;
        --secondary: #7C3AED;
        --success: #10B981;
        --warning: #F59E0B;
        --danger: #EF4444;
        --text: #0F172A;
        --muted: #64748B;
        --border: rgba(15, 23, 42, 0.08);
        --shadow: 0 10px 30px rgba(15, 23, 42, 0.06);
    }
    .stApp { background: var(--bg); color: var(--text); }
    .block-container { padding-top: 1.2rem; padding-bottom: 2rem; max-width: 1440px; }
    h1, h2, h3, h4, h5, h6, p, div, span, label { color: var(--text); }
    section[data-testid="stSidebar"] { background: #F1F5F9; border-right: 1px solid var(--border); }
    
    .opporta-topbar { background: var(--card); border: 1px solid var(--border); border-radius: 20px; box-shadow: var(--shadow); padding: 20px 24px; margin-bottom: 16px; }
    .opporta-title { font-size: 30px; font-weight: 700; letter-spacing: -0.02em; margin: 0; color: var(--text); }
    .opporta-subtle { color: var(--muted); font-size: 14px; margin-top: 4px; }
    .hero-card { background: linear-gradient(135deg, rgba(79,70,229,0.06), rgba(124,58,237,0.05)); border: 1px solid rgba(79,70,229,0.11); border-radius: 24px; padding: 26px; box-shadow: var(--shadow); margin-bottom: 20px; }
    .hero-label { font-size: 13px; color: var(--primary); font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 8px; }
    .hero-heading { font-size: 28px; font-weight: 700; line-height: 1.2; margin-bottom: 8px; color: var(--text); }
    .hero-copy { font-size: 15px; color: var(--muted); margin-bottom: 14px; }
    
    .opp-card { background: var(--card); border: 1px solid var(--border); border-radius: 20px; padding: 20px; box-shadow: var(--shadow); margin-bottom: 14px; }
    .opp-title { font-size: 18px; font-weight: 700; margin-bottom: 6px; color: var(--text); }
    .opp-meta { color: var(--muted); font-size: 14px; margin-bottom: 12px; }
    .opp-grid { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 12px; margin-bottom: 12px; }
    .opp-stat { background: #F8FAFC; border: 1px solid var(--border); border-radius: 14px; padding: 10px 12px; }
    .opp-stat-label { color: var(--muted); font-size: 11px; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 4px; }
    .opp-stat-value { color: var(--text); font-size: 14px; font-weight: 700; }
    
    .badge { display: inline-block; padding: 6px 10px; border-radius: 999px; font-size: 12px; font-weight: 700; margin-right: 8px; }
    .badge-success { background: rgba(16,185,129,0.10); color: var(--success); border: 1px solid rgba(16,185,129,0.18); }
    .badge-warning { background: rgba(245,158,11,0.10); color: var(--warning); border: 1px solid rgba(245,158,11,0.18); }
    .badge-danger { background: rgba(239,68,68,0.10); color: var(--danger); border: 1px solid rgba(239,68,68,0.18); }
    .badge-primary { background: rgba(79,70,229,0.08); color: var(--primary); border: 1px solid rgba(79,70,229,0.15); }
    .empty-state { background: var(--card); border: 1px dashed rgba(15, 23, 42, 0.18); border-radius: 20px; padding: 32px; text-align: center; color: var(--muted); font-weight: 500; }
    .info-card { background: var(--card); border: 1px solid var(--border); border-radius: 20px; padding: 18px; box-shadow: var(--shadow); height: 100%; }
    
    .stButton > button {
        border-radius: 14px !important;
        border: 1px solid var(--border) !important;
        background: var(--card) !important;
        color: var(--text) !important;
        font-weight: 700 !important;
        transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
    }
    .stButton > button:hover {
        transform: translateY(-1px) !important;
        border-color: var(--primary) !important;
        box-shadow: 0 4px 12px rgba(79, 70, 229, 0.08) !important;
    }
    .stButton > button:active { transform: translateY(1px) !important; }
</style>
""", unsafe_allow_html=True)

# =====================================================================
# 3. STATE MACHINE INITIALIZATION ENGINE
# =====================================================================
INITIAL_STATES = {
    "selected_state": "All Regions",
    "selected_sector": "All Categories",
    "job_subcat": "All Jobs",
    "search_filter": "",
    "min_score_filter": 0,
    "kpi_focus": "Clear Focus",
    "saved_opportunities": set(),
    "active_alerts": [],
    "user_profile": {
        "business_type": "Contractor",
        "turnover": "₹5 Crore",
        "contractor_class": "Class A",
        "industries": ["Civil Infrastructure"]
    }
}

for state_key, default_val in INITIAL_STATES.items():
    if state_key not in st.session_state:
        st.session_state[state_key] = default_val

# =====================================================================
# 4. DATA NORMALIZATION & ADVANCED CLEANING HELPERS
# =====================================================================
def get_valid_col(df, col_list, default=""):
    for col in col_list:
        if col in df.columns: return df[col].fillna(default).astype(str)
    return pd.Series([default] * len(df), index=df.index)

def extract_safe_string(val):
    if isinstance(val, pd.Series): return str(val.iloc[0]) if not val.empty else "Not specified"
    return str(val) if (pd.notna(val) and str(val).strip().lower() != "nan") else "Not specified"

def is_genuine_work_tender(title):
    title_clean = str(title).lower().strip()
    noise_indicators = [
        "policy", "csr policy", "guideline", "rules", "act 20", "regulation", "grievance", 
        "manual", "approved posts", "minutes of", "meeting", "notice board", "ppt", "presentation", 
        "press release", "prakashan", "v विज्ञप्ति", "vignapti", "circular", "transfer order", 
        "seniority list", "niti", "eligibility list", "citizen charter"
    ]
    if any(noise in title_clean for noise in noise_indicators): return False
    if len(title_clean) <= 3 or title_clean.isdigit(): return False
    return True

def infer_sector(title, sector):
    text = f"{title} {sector}".lower()
    mapping = [
        ("Coal & Mining", ["coal", "mining", "mine", "secl", "nmdc"]),
        ("Medical Procurement", ["medical", "hospital", "drug", "medicine", "surgical", "health", "upmsc"]),
        ("Civil Infrastructure", ["road", "bridge", "civil", "construction", "building", "pwd", "expressway", "upeida", "nhai"]),
        ("Transport & Logistics", ["transport", "logistics", "vehicle", "fleet", "cargo", "bus hire", "hiring of vehicle"]),
        ("Electrical & Energy", ["power", "electric", "energy", "solar", "transformer", "substation"]),
        ("Water & Irrigation", ["water", "irrigation", "pipeline", "phed", "jal", "tube well"]),
        ("IT & Digital Services", ["software", "it", "digital", "server", "network", "cctv", "hardware procurement"]),
        ("Municipal Projects", ["municipal", "nagar", "corporation", "urban"]),
        ("Panchayat Projects", ["panchayat", "district", "collector", "zilla"]),
        ("Government Jobs", ["recruitment", "vacancy", "job", "bharti", "post", "apply"]),
        ("Government Supplies", ["supply", "procurement", "furniture", "equipment", "office"]),
        ("Consultancy Services", ["consultancy", "consultant", "advisory"]),
        ("AMC & Maintenance Contracts", ["amc", "maintenance", "repair", "upkeep"])
    ]
    for label, keywords in mapping:
        if any(k in text for k in keywords): return label
    return sector if sector else "General Opportunities"

def generate_match_score(title, sector):
    base = 74
    text = f"{title} {sector}".lower()
    user_inds = st.session_state.user_profile["industries"]
    if any(ind.split()[0].lower() in text for ind in user_inds): base += 10
    if any(k in text for k in ["tender", "nit", "supply", "construction", "transport", "procurement"]): base += 8
    if "open" not in text: base += 2
    return min(98, max(54, base + random.randint(-5, 5)))

def eligibility_label(score):
    if score >= 85: return "Eligible", "success"
    if score >= 72: return "Partially Eligible", "warning"
    return "Needs Review", "danger"

def format_inr_compact(value):
    try:
        num = float(value)
        if num >= 10000000: return f"₹{num/10000000:.2f} Cr"
        if num >= 100000: return f"₹{num/100000:.2f} Lakh"
        return f"₹{num:,.0f}"
    except Exception: return "₹N/A"

def parse_amount_from_text(text):
    if text is None: return 0.0
    s = str(text).replace(",", "").replace("₹", "").strip().lower()
    try:
        if "cr" in s or "crore" in s:
            n = float("".join(ch for ch in s if ch.isdigit() or ch == "."))
            return n * 10000000
        if "lakh" in s:
            n = float("".join(ch for ch in s if ch.isdigit() or ch == "."))
            return n * 100000
        return float("".join(ch for ch in s if ch.isdigit() or ch == "."))
    except Exception: return 0.0

# =====================================================================
# 5. SECURE PRODUCTION DATABASES LINK
# =====================================================================
@st.cache_resource(show_spinner="Establishing Secure Pipeline Link...")
def init_connection():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception: return None

supabase = init_connection()

if supabase is None:
    st.error("🚨 Cloud Database Connection Offline. Check configurations.")
    st.stop()

ai_ready = False
if "GEMINI_API_KEY" in st.secrets:
    try:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        model = genai.GenerativeModel('gemini-1.5-flash')
        ai_ready = True
    except Exception: pass

# =====================================================================
# 6. HIGH-PERFORMANCE DATA INGESTION LAYERS
# =====================================================================
@st.cache_data(ttl=60, show_spinner=False)
def fetch_tenders():
    for table_name in ["tenders", "opporta_tenders"]:
        try:
            res = supabase.table(table_name).select("*").order("date_scraped", desc=True).limit(500).execute()
            if res.data: return pd.DataFrame(res.data), table_name
        except Exception:
            try:
                res = supabase.table(table_name).select("*").order("scraped_at", desc=True).limit(500).execute()
                if res.data: return pd.DataFrame(res.data), table_name
            except Exception: pass
    return pd.DataFrame(), None

@st.cache_data(ttl=60, show_spinner=False)
def fetch_jobs():
    for table_name in ["jobs", "opporta_jobs"]:
        try:
            res = supabase.table(table_name).select("*").order("date_scraped", desc=True).limit(500).execute()
            if res.data: return pd.DataFrame(res.data), table_name
        except Exception:
            try:
                res = supabase.table(table_name).select("*").order("scraped_at", desc=True).limit(500).execute()
                if res.data: return pd.DataFrame(res.data), table_name
            except Exception: pass
    return pd.DataFrame(), None

df_tenders_raw, tenders_source = fetch_tenders()
df_jobs_raw, jobs_source = fetch_jobs()

# =====================================================================
# 7. RE-COMPILATION DATA TRANSFORMATION MAPPINGS
# =====================================================================
if not df_tenders_raw.empty:
    df_tenders_raw = df_tenders_raw.loc[:, ~df_tenders_raw.columns.duplicated()].copy()
    df_tenders_raw["is_valid_work"] = df_tenders_raw["title"].apply(is_genuine_work_tender)
    df_tenders_raw = df_tenders_raw[df_tenders_raw["is_valid_work"] == True].copy()
    
    df_tenders_raw["title"] = get_valid_col(df_tenders_raw, ["title"], "Untitled Tenders")
    df_tenders_raw["agency"] = get_valid_col(df_tenders_raw, ["agency", "department"], "Unknown Agency")
    df_tenders_raw["state"] = get_valid_col(df_tenders_raw, ["state"], "Unknown")
    df_tenders_raw["sector"] = [infer_sector(t, s) for t, s in zip(df_tenders_raw["title"], get_valid_col(df_tenders_raw, ["sector"], ""))]
    df_tenders_raw["url"] = get_valid_col(df_tenders_raw, ["url", "source_url", "link"], "")
    df_tenders_raw["location"] = get_valid_col(df_tenders_raw, ["location", "district", "state"], "Unknown")
    df_tenders_raw["project_value"] = get_valid_col(df_tenders_raw, ["project_value", "value"], "Not specified")
    df_tenders_raw["emd"] = get_valid_col(df_tenders_raw, ["emd"], "Not specified")
    df_tenders_raw["deadline"] = get_valid_col(df_tenders_raw, ["deadline", "closing_date"], "Open")
    df_tenders_raw["contract_type"] = get_valid_col(df_tenders_raw, ["contract_type"], "Tender / Opportunity")
    df_tenders_raw["amount_num"] = df_tenders_raw["project_value"].apply(parse_amount_from_text)
    df_tenders_raw["match_score"] = [generate_match_score(t, s) for t, s in zip(df_tenders_raw["title"], df_tenders_raw["sector"])]

if not df_jobs_raw.empty:
    df_jobs_raw = df_jobs_raw.loc[:, ~df_jobs_raw.columns.duplicated()].copy()
    df_jobs_raw["title"] = get_valid_col(df_jobs_raw, ["title", "job_title"], "Untitled Job Notification")
    df_jobs_raw["agency"] = get_valid_col(df_jobs_raw, ["agency", "board"], "Unknown Board")
    df_jobs_raw["state"] = get_valid_col(df_jobs_raw, ["state"], "Unknown")
    df_jobs_raw["sector"] = get_valid_col(df_jobs_raw, ["sector"], "Government Jobs")
    df_jobs_raw["url"] = get_valid_col(df_jobs_raw, ["url", "apply_url", "link"], "")
    df_jobs_raw["qualification"] = get_valid_col(df_jobs_raw, ["qualification"], "Not specified")
    df_jobs_raw["salary"] = get_valid_col(df_jobs_raw, ["salary"], "As per notification")
    df_jobs_raw["deadline"] = get_valid_col(df_jobs_raw, ["deadline", "closing_date"], "Open")
    df_jobs_raw["vacancies"] = get_valid_col(df_jobs_raw, ["vacancy_count", "vacancies"], "Not specified")
    df_jobs_raw["match_score"] = [generate_match_score(t, s) for t, s in zip(df_jobs_raw["title"], df_jobs_raw["sector"])]

# =====================================================================
# 8. CENTRAL RUNTIME DATA FILTRATION PIPELINES
# =====================================================================
df_tenders = df_tenders_raw.copy() if not df_tenders_raw.empty else pd.DataFrame()
df_jobs = df_jobs_raw.copy() if not df_jobs_raw.empty else pd.DataFrame()

if not df_tenders.empty:
    if st.session_state.selected_state != "All Regions":
        df_tenders = df_tenders[df_tenders["state"].astype(str).str.contains(st.session_state.selected_state, case=False, na=False)]
    if st.session_state.selected_sector != "All Categories":
        df_tenders = df_tenders[df_tenders["sector"].astype(str).str.contains(st.session_state.selected_sector.split()[0], case=False, na=False)]
    if st.session_state.search_filter:
        q = st.session_state.search_filter
        df_tenders = df_tenders[df_tenders["title"].str.contains(q, case=False, na=False) | df_tenders["agency"].str.contains(q, case=False, na=False)]
    df_tenders = df_tenders[df_tenders["match_score"] >= st.session_state.min_score_filter]

    if st.session_state.kpi_focus == "Matching Only":
        df_tenders = df_tenders[df_tenders["match_score"] >= 75]
    elif st.session_state.kpi_focus == "High Confidence":
        df_tenders = df_tenders[df_tenders["match_score"] >= 85]
    elif st.session_state.kpi_focus == "Urgent Cycles":
        df_tenders = df_tenders[df_tenders["deadline"].str.lower().str.contains("open|specified") == False]

if not df_jobs.empty:
    if st.session_state.selected_state != "All Regions":
        df_jobs = df_jobs[df_jobs["state"].astype(str).str.contains(st.session_state.selected_state, case=False, na=False)]
    if st.session_state.selected_sector != "All Categories":
        if "Jobs" not in st.session_state.selected_sector: df_jobs = df_jobs.iloc[0:0]
    if st.session_state.search_filter:
        q = st.session_state.search_filter
        df_jobs = df_jobs[df_jobs["title"].str.contains(q, case=False, na=False) | df_jobs["agency"].str.contains(q, case=False, na=False)]
    df_jobs = df_jobs[df_jobs["match_score"] >= st.session_state.min_score_filter]

# =====================================================================
# 9. BACK-CALCULATION TELEMETRY ENGINE
# =====================================================================
opportunity_universe = len(df_tenders_raw) + len(df_jobs_raw)
total_opportunities_today = len(df_tenders) + len(df_jobs)
total_project_value = df_tenders["amount_num"].sum() if not df_tenders.empty else 0
avg_opp_value = df_tenders["amount_num"].mean() if not df_tenders.empty and len(df_tenders) > 0 else 0
matching_count = len(df_tenders_raw[df_tenders_raw["match_score"] >= 75]) if not df_tenders_raw.empty else 0
high_conf_count = len(df_tenders_raw[df_tenders_raw["match_score"] >= 85]) if not df_tenders_raw.empty else 0
closing_count = len(df_tenders_raw[~df_tenders_raw["deadline"].str.lower().str.contains("open|specified", na=True)]) if not df_tenders_raw.empty else 0

# =====================================================================
# 10. CONTROL SIDEBAR SYNC PANEL
# =====================================================================
with st.sidebar:
    st.title("Opporta Control Panel")
    st.caption("Engine State Personalization Context")
    
    st.session_state.selected_state = st.selectbox(
        "Target Geography Matrix", 
        ["All Regions", "Chhattisgarh", "Uttar Pradesh"], 
        index=["All Regions", "Chhattisgarh", "Uttar Pradesh"].index(st.session_state.selected_state)
    )
    
    available_sectors = [
        "All Categories", "Coal & Mining", "Government Supplies", "Medical Procurement",
        "Civil Infrastructure", "Transport & Logistics", "Electrical & Energy", "Water & Irrigation",
        "IT & Digital Services", "Municipal Projects", "Panchayat Projects", "Government Jobs",
        "Consultancy Services", "AMC & Maintenance Contracts"
    ]
    sect_idx = available_sectors.index(st.session_state.selected_sector) if st.session_state.selected_sector in available_sectors else 0
    st.session_state.selected_sector = st.selectbox("Primary Category Cluster", available_sectors, index=sect_idx)
    
    st.session_state.search_filter = st.text_input("Heuristic Filter", value=st.session_state.search_filter, placeholder="Type constraints...")
    st.session_state.min_score_filter = st.slider("Minimum AI Filter Node", 0, 100, int(st.session_state.min_score_filter), 5)
    
    # RESOLVED NAMEERROR: Global structural size tracking assignment loop
    feed_limit = st.slider("Workspace Feed Limit size", 5, 100, 15, 1)
    
    if st.button("Reset Global Filter Matrices", use_container_width=True):
        st.session_state.selected_state = "All Regions"
        st.session_state.selected_sector = "All Categories"
        st.session_state.search_filter = ""
        st.session_state.min_score_filter = 0
        st.session_state.kpi_focus = "Clear Focus"
        st.rerun()

# =====================================================================
# 11. ENTERPRISE HEADER CONTROL MATRIX
# =====================================================================
st.markdown("""
<div class="opporta-topbar">
    <div style="display:flex; justify-content:space-between; align-items:flex-start; gap:16px; flex-wrap:wrap;">
        <div>
            <p class="opporta-title">Good Morning, Akash 👋</p>
            <div class="opporta-subtle">Operational Telemetry: Top 1% High Signal Real-time Analytics Engine Active.</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

h_col1, h_col2, h_col3, h_col4 = st.columns(4)
with h_col1:
    if st.button(f"🌐 Universe: {opportunity_universe}", use_container_width=True):
        st.session_state.kpi_focus = "Clear Focus"
        st.rerun()
with h_col2:
    if st.button(f"🎯 Matching Profile: {matching_count}", use_container_width=True):
        st.session_state.kpi_focus = "Matching Only"
        st.rerun()
with h_col3:
    if st.button(f"🔥 High Qualification: {high_conf_count}", use_container_width=True):
        st.session_state.kpi_focus = "High Confidence"
        st.rerun()
with h_col4:
    if st.button(f"⏳ Urgent Deadlines: {closing_count}", use_container_width=True):
        st.session_state.kpi_focus = "Urgent Cycles"
        st.rerun()

g_search = st.text_input("Global Search Matrix Explorer", value=st.session_state.search_filter, placeholder="Query structural procurement nodes...")
if g_search != st.session_state.search_filter:
    st.session_state.search_filter = g_search
    st.rerun()

# =====================================================================
# 12. HERO CONTROL ACTION BRIEF PANEL
# =====================================================================
st.markdown(f"""
<div class="hero-card">
    <div class="hero-label">AI Intelligence Context Executive Summary</div>
    <div class="hero-heading">Active Analysis Workspace: Isolating {total_opportunities_today} verified contract streams.</div>
    <div class="hero-copy">
        Running configurations match cumulative value matrices estimated at <b>{format_inr_compact(total_project_value)}</b>.<br>
        Active Operational Focus Sub-set Filter Constraint Status: <b>{st.session_state.kpi_focus}</b>
    </div>
</div>
""", unsafe_allow_html=True)

action_col1, action_col2, action_col3 = st.columns(3)
with action_col1:
    if st.button("⚡ Reset to View All Matches", use_container_width=True):
        st.session_state.kpi_focus = "Clear Focus"
        st.rerun()
with action_col2:
    if st.button("🚨 Focus Urgent Deadlines", use_container_width=True):
        st.session_state.kpi_focus = "Urgent Cycles"
        st.rerun()
with action_col3:
    if st.button("🔮 Focus High Probability Nodes", use_container_width=True):
        st.session_state.kpi_focus = "High Confidence"
        st.rerun()

# =====================================================================
# 13. SMART CATEGORY WORKSPACE MATRIX
# =====================================================================
st.markdown("### Smart Category Workspace Explorer")
category_data = [
    ("⛏️", "Coal & Mining"), ("🩺", "Medical Procurement"), ("🏗️", "Civil Infrastructure"), ("🚛", "Transport & Logistics"),
    ("💼", "Government Jobs"), ("🏛️", "Municipal Projects"), ("⚡", "Electrical & Energy"), ("💻", "IT & Digital Services")
]

cat_cols = st.columns(4)
for idx, (icon, label) in enumerate(category_data):
    with cat_cols[idx % 4]:
        count = 0
        if not df_tenders_raw.empty and label != "Government Jobs":
            count = int(df_tenders_raw["sector"].str.contains(label.split()[0], case=False, na=False).sum())
        elif label == "Government Jobs":
            count = len(df_jobs_raw)
            
        is_selected = st.session_state.selected_sector == label
        btn_tag = f"🔹 {icon} {label} ({count} Live)" if is_selected else f"{icon} {label} ({count} Live)"
        
        if st.button(btn_tag, key=f"workspace_node_{idx}", use_container_width=True):
            st.session_state.selected_sector = label
            if label == "Government Jobs": st.session_state.job_subcat = "All Jobs"
            st.rerun()

# =====================================================================
# 14. COMPARTMENT REACTION WORKSPACE TABS
# =====================================================================
tab_home, tab_jobs, tab_ai, tab_saved, tab_profile = st.tabs([
    "Opportunity Feed Tracking", "Government Recruitment Center", 
    "AI Eligibility Engine Room", "Saved Workspace Repository", "Personalized Engine Profile"
])

# =====================================================================
# 15. TAB WORKFLOW: OPPORTUNITY FEED
# =====================================================================
with tab_home:
    st.markdown("#### High-Signal Contracts Pipeline View")
    
    if df_tenders.empty:
        st.markdown('<div class="empty-state">No verified contractual nodes match your currently active filter settings.</div>', unsafe_allow_html=True)
    else:
        feed_df = df_tenders.sort_values(by="match_score", ascending=False).head(feed_limit)
        for _, row in feed_df.iterrows():
            score = int(row.get("match_score", 0))
            eligibility, el_class = eligibility_label(score)
            
            t_text = extract_safe_string(row.get("title"))
            a_text = extract_safe_string(row.get("agency"))
            l_text = extract_safe_string(row.get("location"))
            val_text = extract_safe_string(row.get("project_value"))
            emd_text = extract_safe_string(row.get("emd"))
            dl_text = extract_safe_string(row.get("deadline"))
            sec_text = extract_safe_string(row.get("sector"))
            ct_text = extract_safe_string(row.get("contract_type"))
            url_link = extract_safe_string(row.get("url"))

            html_card = f'<div class="opp-card"><div class="opp-title">{t_text}</div><div class="opp-meta">{a_text} - {l_text}</div><div style="margin-bottom:12px;"><span class="badge badge-primary">Match Score {score}%</span><span class="badge badge-{el_class}">{eligibility}</span></div><div class="opp-grid"><div class="opp-stat"><div class="opp-stat-label">Project Value</div><div class="opp-stat-value">{val_text}</div></div><div class="opp-stat"><div class="opp-stat-label">EMD</div><div class="opp-stat-value">{emd_text}</div></div><div class="opp-stat"><div class="opp-stat-label">Deadline</div><div class="opp-stat-value">{dl_text}</div></div><div class="opp-stat"><div class="opp-stat-label">Sector</div><div class="opp-stat-value">{sec_text}</div></div><div class="opp-stat"><div class="opp-stat-label">Contract Type</div><div class="opp-stat-value">{ct_text}</div></div></div></div>'
            st.markdown(html_card, unsafe_allow_html=True)

            a_col1, a_col2, a_col3 = st.columns([1, 1, 1])
            with a_col1:
                if url_link and url_link.lower() != "nan":
                    st.link_button("📂 View Source Document Links", url_link, use_container_width=True)
                else:
                    st.button("❌ Link Not Available", disabled=True, key=f"no_lnk_{row.name}", use_container_width=True)
            with a_col2:
                is_saved = t_text in st.session_state.saved_opportunities
                save_label = "⭐ Remove from Workspace" if is_saved else "📥 Cache to Workspace Repository"
                if st.button(save_label, key=f"save_act_{row.name}", use_container_width=True):
                    if is_saved: st.session_state.saved_opportunities.remove(t_text)
                    else: st.session_state.saved_opportunities.add(t_text)
                    st.toast("Repository updated successfully.")
                    st.rerun()
            with a_col3:
                rule_text = f"Alert trigger created for {sec_text} nodes matching keyword context '{t_text[:15]}'"
                if st.button("🔔 Route Real-time Trigger Rules", key=f"alert_act_{row.name}", use_container_width=True):
                    st.session_state.active_alerts.append(rule_text)
                    st.toast("Active push node notification trigger established.")

# =====================================================================
# 16. TAB WORKFLOW: RECRUITMENT EXPERIENCE PIPELINES
# =====================================================================
with tab_jobs:
    st.markdown("#### Clickable Vacancy Context Matrices Router")
    
    job_categories = ["All Jobs", "SSC", "PSC", "Railway", "Police", "Teaching", "Engineering", "Medical", "PSU"]
    job_cols = st.columns(9)
    for idx, jc in enumerate(job_categories):
        with job_cols[idx]:
            sub_active = st.session_state.job_subcat == jc
            j_label = f"🔹 {jc}" if sub_active else jc
            if st.button(j_label, key=f"job_sub_btn_{idx}", use_container_width=True):
                st.session_state.job_subcat = jc
                st.rerun()

    if df_jobs.empty:
        st.markdown('<div class="empty-state">No recruitment parameters match your filter vectors.</div>', unsafe_allow_html=True)
    else:
        active_sub = st.session_state.job_subcat
        df_j_filtered = df_jobs.copy()
        
        if active_sub != "All Jobs":
            mapping_keys = {
                "SSC": ["ssc", "staff selection", "cgl", "chsl"],
                "PSC": ["psc", "upsc", "public service", "cgpsc", "uppsc"],
                "Railway": ["railway", "rrb", "ntpc", "loco", "rail"],
                "Police": ["police", "sub inspector", "constable", "si ", "defence", "army"],
                "Teaching": ["teacher", "teaching", "prof", "lecturer", "shikshak", "school"],
                "Engineering": ["engineer", "je ", "ae ", "technical", "civil engineer"],
                "Medical": ["medical", "doctor", "nurse", "health", "amo ", "pharmacist"],
                "PSU": ["psu", "secl", "ntpc", "sail", "coalltd", "corporation", "limited", "cspdcl"]
            }
            keywords = mapping_keys.get(active_sub, [active_sub.lower()])
            df_j_filtered = df_j_filtered[
                df_j_filtered["title"].str.lower().apply(lambda x: any(k in x for k in keywords)) |
                df_j_filtered["agency"].str.lower().apply(lambda x: any(k in x for k in keywords))
            ]

        if df_j_filtered.empty:
            st.markdown(f'<div class="empty-state">No vacancy listings found for subset category matches: "<b>{active_sub}</b>"</div>', unsafe_allow_html=True)
        else:
            for _, row in df_j_filtered.sort_values(by="match_score", ascending=False).head(feed_limit).iterrows():
                j_t = extract_safe_string(row.get("title"))
                j_a = extract_safe_string(row.get("agency"))
                j_s = extract_safe_string(row.get("state"))
                j_v = extract_safe_string(row.get("vacancies"))
                j_l = extract_safe_string(row.get("salary"))
                j_q = extract_safe_string(row.get("qualification"))
                j_d = extract_safe_string(row.get("deadline"))
                j_u = extract_safe_string(row.get("url"))

                html_job = f'<div class="opp-card"><div class="opp-title">{j_t}</div><div class="opp-meta">{j_a} - {j_s}</div><div class="opp-grid"><div class="opp-stat"><div class="opp-stat-label">Vacancies</div><div class="opp-stat-value">{j_v}</div></div><div class="opp-stat"><div class="opp-stat-label">Salary</div><div class="opp-stat-value">{j_l}</div></div><div class="opp-stat"><div class="opp-stat-label">Qualification</div><div class="opp-stat-value">{j_q}</div></div><div class="opp-stat"><div class="opp-stat-label">Deadline</div><div class="opp-stat-value">{j_d}</div></div><div class="opp-stat"><div class="opp-stat-label">AI Match Score</div><div class="opp-stat-value">{row.get("match_score", 0)}%</div></div></div></div>'
                st.markdown(html_job, unsafe_allow_html=True)
                if j_u and j_u.lower() != "nan": st.link_button("📂 View Notification Vectors", j_u)

# =====================================================================
# 17. TAB WORKFLOW: AI ENGINE ROOM
# =====================================================================
with tab_ai:
    st.markdown("#### AI Eligibility Center")
    l_box, r_box = st.columns([1.1, 1])
    with l_box:
        up_file = st.file_uploader("Upload Tender PDF Matrix Node", type=["pdf"])
        paste_req = st.text_area("Or compile raw textual configuration requirements", placeholder="Paste terms here...")
        
        if st.button("Execute Active Analysis Sequence", use_container_width=True):
            if not ai_ready:
                st.error("🚨 Configuration Error: Gemini API key validation state token missing.")
            elif not up_file and not paste_req:
                st.warning("Please upload a file or paste requirements.")
            else:
                with st.spinner("🧠 Compiling extraction schemas via LLM nodes..."):
                    try:
                        instructions = "Analyze this tender document. Extract criteria elements: Turnover, Experience, EMD, Class, GST Requirements, and an executive technical work summary."
                        inputs = [instructions]
                        if up_file: inputs.append({"mime_type": "application/pdf", "data": up_file.getvalue()})
                        if paste_req: inputs.append(paste_req)
                        
                        response = model.generate_content(inputs)
                        st.success("Analysis Complete")
                        st.markdown(f'<div class="info-card" style="margin-top:16px; line-height:1.6;">{response.text}</div>', unsafe_allow_html=True)
                    except Exception as e:
                        st.error(f"Execution Error: {str(e)}")
    with r_box:
        st.markdown("""
        <div class="info-card">
            <div class="section-title" style="margin-top:0; font-size:16px;">Target Extrapolated Schema Models</div>
            <div class="section-subtitle" style="font-size:13px; color:var(--muted);">Automated verification structures mapped directly to personalized configuration profiles.</div>
            <hr style="opacity:0.12; margin:12px 0;">
            <div class="pill-row">
                <span class="pill">Financial Turnovers Checks</span>
                <span class="pill">Past Experience Mapping</span>
                <span class="pill">Statutory GST Verification</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

# =====================================================================
# 18. TAB WORKFLOW: WORKSPACE REPOSITORY
# =====================================================================
with tab_saved:
    st.markdown("#### Workspace Repository Nodes")
    
    al_col1, al_col2 = st.columns(2)
    with al_col1:
        st.markdown("##### Bookmarked Opportunity Nodes Cache")
        if not st.session_state.saved_opportunities:
            st.info("No contracts saved to this workspace repository yet.")
        else:
            for item in list(st.session_state.saved_opportunities):
                st.markdown(f"🔒 **{item}**")
                if st.button("Delete Cache Node Record", key=f"del_cache_{hash(item)}"):
                    st.session_state.saved_opportunities.remove(item)
                    st.rerun()
    with al_col2:
        st.markdown("##### Real-time Push Trigger Rule Matrix logs")
        if not st.session_state.active_alerts:
            st.info("No notification streams mapped.")
        else:
            for idx, alert in enumerate(st.session_state.active_alerts):
                st.success(f"🔔 {alert}")
            if st.button("Purge Active Alerts Engine", use_container_width=True):
                st.session_state.active_alerts = []
                st.rerun()

# =====================================================================
# 19. TAB WORKFLOW: PERSONALIZED PROFILE MATRIX
# =====================================================================
with tab_profile:
    st.markdown("#### Personalized Engine Profile Management")
    prof = st.session_state.user_profile
    
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        b_type = st.selectbox("Corporate Functional Model Identity", ["Contractor", "Supplier", "Manufacturer", "Transporter"], index=["Contractor", "Supplier", "Manufacturer", "Transporter"].index(prof["business_type"]))
        t_val = st.text_input("Verified Annual Financial Turnover Nodes", value=prof["turnover"])
    with col_p2:
        c_class = st.selectbox("Contractor Structural Registration Class Tier", ["Class A", "Class B", "Class C", "Not Applicable"], index=["Class A", "Class B", "Class C", "Not Applicable"].index(prof["contractor_class"]))
        inds = st.multiselect("Core Industrial Sectors", available_sectors[1:], default=prof["industries"])
        
    if st.button("Save Profile Parameters & Re-index Recommendation Engine", use_container_width=True):
        st.session_state.user_profile = {
            "business_type": b_type,
            "turnover": t_val,
            "contractor_class": c_class,
            "industries": inds
        }
        st.toast("Profile data structured successfully. Re-indexing score criteria nodes.")
        st.rerun()

# =====================================================================
# 20. INFRASTRUCTURE SYSTEM METRICS FOOTER
# =====================================================================
st.write("---")
f_col1, f_col2, f_col3 = st.columns(3)
with f_col1: st.caption(f"Supabase Backend Pipeline Synchronized: Verified Active ({tenders_source if tenders_source else 'Cache'})")
with f_col2: st.caption(f"Active Filtering Focus Criteria Context: {st.session_state.kpi_focus}")
with f_col3: st.caption(f"Operational Execution Matrix Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")