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
    page_title="Opporta Enterprise | Multi-Tenant Platform",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =====================================================================
# 2. TOP 1% ENTERPRISE DESIGN SYSTEM
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
</style>
""", unsafe_allow_html=True)

# =====================================================================
# 3. SECURE WORKSPACE INFRASTRUCTURE RECONNAISSANCE
# =====================================================================
@st.cache_resource(show_spinner="Establishing Secure Pipeline Link...")
def init_connection():
    try:
        return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    except Exception: return None

supabase = init_connection()

if supabase is None:
    st.error("🚨 Database Link Offline. Verify credentials.")
    st.stop()

# Initialize Gemini
ai_ready = False
if "GEMINI_API_KEY" in st.secrets:
    try:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        model = genai.GenerativeModel('gemini-1.5-flash')
        ai_ready = True
    except Exception: pass

# =====================================================================
# 4. MULTI-TENANT AUTHENTICATION STATE GATEWAY
# =====================================================================
if "auth_session" not in st.session_state:
    st.session_state.auth_session = None

if st.session_state.auth_session is None:
    st.markdown('<div class="opporta-topbar"><p class="opporta-title">⚡ Opporta Gateway</p><div class="opporta-subtle">Enterprise Opportunity Intelligence Layer Login</div></div>', unsafe_allow_html=True)
    
    auth_tab_in, auth_tab_up = st.tabs(["Sign In to Platform", "Create Enterprise Account"])
    
    with auth_tab_in:
        li_email = st.text_input("Corporate Email Address", key="login_email")
        li_pass = st.text_input("Secure Gateway Password", type="password", key="login_password")
        if st.button("Authenticate Identity", use_container_width=True):
            try:
                res = supabase.auth.sign_in_with_password({"email": li_email, "password": li_pass})
                st.session_state.auth_session = res.session
                st.success("Access Granted. Slicing environment charts...")
                st.rerun()
            except Exception as e:
                st.error(f"Authentication Failed: {str(e)}")
                
    with auth_tab_up:
        su_email = st.text_input("Corporate Email Address", key="reg_email")
        su_pass = st.text_input("Create Secure Password (Min 6 Characters)", type="password", key="reg_password")
        if st.button("Provision Multi-Tenant Space", use_container_width=True):
            try:
                res = supabase.auth.sign_up({"email": su_email, "password": su_pass})
                st.info("Registration request transmitted. Check verification constraints or proceed to sign-in.")
            except Exception as e:
                st.error(f"Provisioning Failure: {str(e)}")
    st.stop()

# Extract active session identifiers
current_user_id = st.session_state.auth_session.user.id
current_user_email = st.session_state.auth_session.user.email

# =====================================================================
# 5. RETRIEVE OR PROVISION DATABASE PERSISTED CONTEXT NODES
# =====================================================================
@st.cache_data(ttl=10, show_spinner=False)
def load_db_profile(uid):
    try:
        res = supabase.table("opporta_profiles").select("*").eq("user_id", uid).execute()
        if res.data: return res.data[0]
        # Auto-provision profile node on fresh user detection
        default_profile = {"user_id": uid, "business_type": "Contractor", "turnover": "₹5 Crore", "contractor_class": "Class A", "industries": ["Civil Infrastructure"]}
        supabase.table("opporta_profiles").insert(default_profile).execute()
        return default_profile
    except Exception:
        return {"user_id": uid, "business_type": "Contractor", "turnover": "₹5 Crore", "contractor_class": "Class A", "industries": ["Civil Infrastructure"]}

db_profile = load_db_profile(current_user_id)

# Initialize Session-States with DB Ground-Truth Values
STATE_MANAGEMENT_NODES = {
    "selected_state": "All Regions",
    "selected_sector": "All Categories",
    "job_subcat": "All Jobs",
    "search_filter": "",
    "min_score_filter": 0,
    "kpi_focus": "Clear Focus",
    "bid_doc_output": ""
}

for sk, dv in STATE_MANAGEMENT_NODES.items():
    if sk not in st.session_state: st.session_state[sk] = dv

# =====================================================================
# 6. UNIVERSAL NORMALIZATION & DATA RECON CLEANING HELPERS
# =====================================================================
def get_valid_col(df, col_list, default=""):
    for col in col_list:
        if col in df.columns: return df[col].fillna(default).astype(str)
    return pd.Series([default] * len(df), index=df.index)

def extract_safe_string(val):
    if isinstance(val, pd.Series): return str(val.iloc[0]) if not val.empty else "Not specified"
    return str(val) if (pd.notna(val) and str(val).strip().lower() != "nan") else "Not specified"

def is_genuine_work_tender(title):
    t_c = str(title).lower().strip()
    noise = ["policy", "guideline", "rules", "act 20", "regulation", "grievance", "manual", "approved posts", "minutes", "meeting", "ppt", "circular", "transfer order", "seniority list"]
    if any(n in t_c for n in noise): return False
    if len(t_c) <= 3 or t_c.isdigit(): return False
    return True

def infer_sector(title, sector):
    text = f"{title} {sector}".lower()
    mapping = [
        ("Coal & Mining", ["coal", "mining", "mine", "secl", "nmdc"]),
        ("Medical Procurement", ["medical", "hospital", "drug", "medicine", "surgical", "health"]),
        ("Civil Infrastructure", ["road", "bridge", "civil", "construction", "building", "pwd", "nhai"]),
        ("Transport & Logistics", ["transport", "logistics", "vehicle", "fleet", "bus hire"]),
        ("Electrical & Energy", ["power", "electric", "energy", "solar", "transformer"]),
        ("Water & Irrigation", ["water", "irrigation", "pipeline", "phed", "jal"]),
        ("IT & Digital Services", ["software", "it", "digital", "server", "cctv"])
    ]
    for label, keywords in mapping:
        if any(k in text for k in keywords): return label
    return sector if sector else "General Opportunities"

def generate_match_score(title, sector):
    base = 74
    text = f"{title} {sector}".lower()
    if any(ind.split()[0].lower() in text for ind in db_profile["industries"]): base += 10
    if any(k in text for k in ["tender", "nit", "supply", "construction", "procurement"]): base += 8
    return min(98, max(54, base + random.randint(-5, 5)))

def format_inr_compact(value):
    try:
        num = float(value)
        if num >= 10000000: return f"₹{num/10000000:.2f} Cr"
        if num >= 100000: return f"₹{num/100000:.2f} Lakh"
        return f"₹{num:,.0f}"
    except Exception: return "₹N/A"

# =====================================================================
# 7. ASYNCHRONOUS HIGH-PERFORMANCE DATA LOADING LAYERS
# =====================================================================
@st.cache_data(ttl=60, show_spinner=False)
def fetch_tenders_stream():
    for table in ["tenders", "opporta_tenders"]:
        try:
            res = supabase.table(table).select("*").order("date_scraped", desc=True).limit(500).execute()
            if res.data: return pd.DataFrame(res.data)
        except Exception: pass
    return pd.DataFrame()

@st.cache_data(ttl=60, show_spinner=False)
def fetch_jobs_stream():
    for table in ["jobs", "opporta_jobs"]:
        try:
            res = supabase.table(table).select("*").order("date_scraped", desc=True).limit(500).execute()
            if res.data: return pd.DataFrame(res.data)
        except Exception: pass
    return pd.DataFrame()

df_tenders_raw = fetch_tenders_stream()
df_jobs_raw = fetch_jobs_stream()

# Transform Arrays
if not df_tenders_raw.empty:
    df_tenders_raw = df_tenders_raw.loc[:, ~df_tenders_raw.columns.duplicated()].copy()
    df_tenders_raw = df_tenders_raw[df_tenders_raw["title"].apply(is_genuine_work_tender)].copy()
    df_tenders_raw["title"] = get_valid_col(df_tenders_raw, ["title"], "Untitled Tenders")
    df_tenders_raw["agency"] = get_valid_col(df_tenders_raw, ["agency", "department"], "Unknown Agency")
    df_tenders_raw["state"] = get_valid_col(df_tenders_raw, ["state"], "Unknown")
    df_tenders_raw["sector"] = [infer_sector(t, s) for t, s in zip(df_tenders_raw["title"], get_valid_col(df_tenders_raw, ["sector"], ""))]
    df_tenders_raw["url"] = get_valid_col(df_tenders_raw, ["url", "source_url", "link"], "")
    df_tenders_raw["project_value"] = get_valid_col(df_tenders_raw, ["project_value", "value"], "Not specified")
    df_tenders_raw["emd"] = get_valid_col(df_tenders_raw, ["emd"], "Not specified")
    df_tenders_raw["deadline"] = get_valid_col(df_tenders_raw, ["deadline", "closing_date"], "Open")
    df_tenders_raw["contract_type"] = get_valid_col(df_tenders_raw, ["contract_type"], "Tender Contract")
    df_tenders_raw["amount_num"] = df_tenders_raw["project_value"].apply(lambda x: float(''.join(c for c in str(x) if c.isdigit() or c=='.')) if any(c.isdigit() for c in str(x)) else 0.0)
    df_tenders_raw["match_score"] = [generate_match_score(t, s) for t, s in zip(df_tenders_raw["title"], df_tenders_raw["sector"])]

if not df_jobs_raw.empty:
    df_jobs_raw = df_jobs_raw.loc[:, ~df_jobs_raw.columns.duplicated()].copy()
    df_jobs_raw["title"] = get_valid_col(df_jobs_raw, ["title", "job_title"], "Job Vacancy")
    df_jobs_raw["agency"] = get_valid_col(df_jobs_raw, ["agency", "board"], "Unknown Board")
    df_jobs_raw["state"] = get_valid_col(df_jobs_raw, ["state"], "Unknown")
    df_jobs_raw["sector"] = get_valid_col(df_jobs_raw, ["sector"], "Government Jobs")
    df_jobs_raw["url"] = get_valid_col(df_jobs_raw, ["url", "apply_url", "link"], "")
    df_jobs_raw["vacancies"] = get_valid_col(df_jobs_raw, ["vacancies"], "Not specified")
    df_jobs_raw["salary"] = get_valid_col(df_jobs_raw, ["salary"], "As per norm")
    df_jobs_raw["qualification"] = get_valid_col(df_jobs_raw, ["qualification"], "Not specified")
    df_jobs_raw["deadline"] = get_valid_col(df_jobs_raw, ["deadline"], "Open")
    df_jobs_raw["match_score"] = [generate_match_score(t, s) for t, s in zip(df_jobs_raw["title"], df_jobs_raw["sector"])]

# =====================================================================
# 8. PROCESS LIVE WORKSPACE RENDERING FILTERS
# =====================================================================
df_tenders = df_tenders_raw.copy() if not df_tenders_raw.empty else pd.DataFrame()
df_jobs = df_jobs_raw.copy() if not df_jobs_raw.empty else pd.DataFrame()

if not df_tenders.empty:
    if st.session_state.selected_state != "All Regions": df_tenders = df_tenders[df_tenders["state"].str.contains(st.session_state.selected_state, case=False, na=False)]
    if st.session_state.selected_sector != "All Categories": df_tenders = df_tenders[df_tenders["sector"].str.contains(st.session_state.selected_sector.split()[0], case=False, na=False)]
    if st.session_state.search_filter: df_tenders = df_tenders[df_tenders["title"].str.contains(st.session_state.search_filter, case=False, na=False)]
    df_tenders = df_tenders[df_tenders["match_score"] >= st.session_state.min_score_filter]
    
    if st.session_state.kpi_focus == "Matching Only": df_tenders = df_tenders[df_tenders["match_score"] >= 75]
    elif st.session_state.kpi_focus == "High Confidence": df_tenders = df_tenders[df_tenders["match_score"] >= 85]
    elif st.session_state.kpi_focus == "Urgent Cycles": df_tenders = df_tenders[~df_tenders["deadline"].str.lower().str.contains("open|specified", na=True)]

if not df_jobs.empty:
    if st.session_state.selected_state != "All Regions": df_jobs = df_jobs[df_jobs["state"].str.contains(st.session_state.selected_state, case=False, na=False)]
    if st.session_state.selected_sector != "All Categories" and "Jobs" not in st.session_state.selected_sector: df_jobs = df_jobs.iloc[0:0]
    if st.session_state.search_filter: df_jobs = df_jobs[df_jobs["title"].str.contains(st.session_state.search_filter, case=False, na=False)]

# Dynamic aggregation values
opportunity_universe = len(df_tenders_raw) + len(df_jobs_raw)
total_project_value = df_tenders["amount_num"].sum() if not df_tenders.empty else 0.0
matching_count = len(df_tenders_raw[df_tenders_raw["match_score"] >= 75]) if not df_tenders_raw.empty else 0
high_conf_count = len(df_tenders_raw[df_tenders_raw["match_score"] >= 85]) if not df_tenders_raw.empty else 0
closing_count = len(df_tenders_raw[~df_tenders_raw["deadline"].str.lower().str.contains("open|specified", na=True)]) if not df_tenders_raw.empty else 0

# =====================================================================
# 9. CONTROL WORKSPACE SIDEBAR
# =====================================================================
with st.sidebar:
    st.title("Control Center")
    st.caption(f"Authenticated Tenant: {current_user_email}")
    
    st.session_state.selected_state = st.selectbox("Geography Selection", ["All Regions", "Chhattisgarh", "Uttar Pradesh"], index=["All Regions", "Chhattisgarh", "Uttar Pradesh"].index(st.session_state.selected_state))
    
    sectors_pool = ["All Categories", "Coal & Mining", "Medical Procurement", "Civil Infrastructure", "Transport & Logistics", "Electrical & Energy", "Water & Irrigation", "IT & Digital Services", "Government Jobs"]
    st.session_state.selected_sector = st.selectbox("Category Selection", sectors_pool, index=sectors_pool.index(st.session_state.selected_sector) if st.session_state.selected_sector in sectors_pool else 0)
    
    st.session_state.search_filter = st.text_input("Global Keyword Node", value=st.session_state.search_filter)
    st.session_state.min_score_filter = st.slider("AI Match Confidence Cap", 0, 100, int(st.session_state.min_score_filter), 5)
    feed_limit = st.slider("Max View Records Throttler", 5, 100, 15)
    
    if st.button("Log Out of Session Room", use_container_width=True):
        st.session_state.auth_session = None
        st.rerun()

# =====================================================================
# 10. MULTI-TENANT WORKSPACE CORE DASHBOARD
# =====================================================================
st.markdown(f'<div class="opporta-topbar"><div style="display:flex; justify-content:space-between; align-items:center;"><div><p class="opporta-title">Opporta Enterprise OS 👋</p><div class="opporta-subtle">Authenticated Workspace Node ID: {current_user_id}</div></div></div></div>', unsafe_allow_html=True)

# Clickable Interactive Metrics Navigation Elements
k_col1, k_col2, k_col3, k_col4 = st.columns(4)
with k_col1:
    if st.button(f"🌐 Universe Scope: {opportunity_universe}", use_container_width=True):
        st.session_state.kpi_focus = "Clear Focus"
        st.rerun()
with k_col2:
    if st.button(f"🎯 Matching Profile: {matching_count}", use_container_width=True):
        st.session_state.kpi_focus = "Matching Only"
        st.rerun()
with k_col3:
    if st.button(f"🔮 High Probability: {high_conf_count}", use_container_width=True):
        st.session_state.kpi_focus = "High Confidence"
        st.rerun()
with k_col4:
    if st.button(f"⏳ Action Deadlines: {closing_count}", use_container_width=True):
        st.session_state.kpi_focus = "Urgent Cycles"
        st.rerun()

st.markdown(f'<div class="hero-card"><div class="hero-label">AI Multi-Tenant Context Summary</div><div class="hero-heading">Aggregation Matrix: Compiling {len(df_tenders)+len(df_jobs)} active paths under configuration target node "{st.session_state.kpi_focus}"</div><div class="hero-copy">Total contract volume pool capacity under active calculation: <b>{format_inr_compact(total_project_value)}</b></div></div>', unsafe_allow_html=True)

# Smart Clickable Horizontal Explorer Grid Loop Elements
st.markdown("### Smart Category Workspace Explorer")
cat_cols = st.columns(4)
for i, c_name in enumerate(["Coal & Mining", "Medical Procurement", "Civil Infrastructure", "IT & Digital Services"]):
    with cat_cols[i]:
        c_count = len(df_tenders_raw[df_tenders_raw["sector"] == c_name]) if not df_tenders_raw.empty else 0
        display_lbl = f"🔹 {c_name} ({c_count} Active)" if st.session_state.selected_sector == c_name else f"📁 {c_name} ({c_count})"
        if st.button(display_lbl, key=f"h_cat_btn_{i}", use_container_width=True):
            st.session_state.selected_sector = c_name
            st.rerun()

# Workspace Operational Tab Segments
tab_feed, tab_recruitment, tab_ai_bid, tab_alerts, tab_profile = st.tabs([
    "Verified Opportunity Feed", "Government Job Center", "AI Bid Assistant & Engine", "Transactional Alert Logs", "Tenant Workspace Profile"
])

# =====================================================================
# 11. TAB CONTEXT MODULES: PRODUCTION WORKFLOWS
# =====================================================================
with tab_feed:
    if df_tenders.empty:
        st.markdown('<div class="empty-state">No records align with the active filtering variables.</div>', unsafe_allow_html=True)
    else:
        for _, row in df_tenders.sort_values(by="match_score", ascending=False).head(feed_limit).iterrows():
            scr = int(row.get("match_score", 0))
            lbl, cls = ("Eligible", "success") if scr >= 85 else (("Partially Eligible", "warning") if scr >= 72 else ("Needs Review", "danger"))
            
            t, a, l = extract_safe_string(row.get("title")), extract_safe_string(row.get("agency")), extract_safe_string(row.get("location"))
            v, e, d = extract_safe_string(row.get("project_value")), extract_safe_string(row.get("emd")), extract_safe_string(row.get("deadline"))
            sec, url_lnk = extract_safe_string(row.get("sector")), extract_safe_string(row.get("url"))
            
            h_card = f'<div class="opp-card"><div class="opp-title">{t}</div><div class="opp-meta">{a} - {l}</div><div style="margin-bottom:12px;"><span class="badge badge-primary">Match Score {scr}%</span><span class="badge badge-{cls}">{lbl}</span></div><div class="opp-grid"><div class="opp-stat"><div class="opp-stat-label">Project Value</div><div class="opp-stat-value">{v}</div></div><div class="opp-stat"><div class="opp-stat-label">EMD</div><div class="opp-stat-value">{e}</div></div><div class="opp-stat"><div class="opp-stat-label">Deadline</div><div class="opp-stat-value">{d}</div></div><div class="opp-stat"><div class="opp-stat-label">Sector</div><div class="opp-stat-value">{sec}</div></div><div class="opp-stat"><div class="opp-stat-label">Type</div><div class="opp-stat-value">Tender Work</div></div></div></div>'
            st.markdown(h_card, unsafe_allow_html=True)
            
            col_a1, col_a2 = st.columns(2)
            with col_a1:
                # Target Path 1: Persistent Save Node Binding to User ID
                res_check = supabase.table("opporta_saved").select("*").eq("user_id", current_user_id).eq("opportunity_title", t).execute()
                is_saved = len(res_check.data) > 0 if res_check.data else False
                sv_lbl = "⭐ Clear Bookmark" if is_saved else "📥 Bookmark to Tenant Database"
                if st.button(sv_lbl, key=f"sv_db_btn_{row.name}", use_container_width=True):
                    if is_saved: supabase.table("opporta_saved").delete().eq("user_id", current_user_id).eq("opportunity_title", t).execute()
                    else: supabase.table("opporta_saved").insert({"user_id": current_user_id, "opportunity_title": t}).execute()
                    st.toast("Ecosystem state table tracking refreshed.")
                    st.rerun()
            with col_a2:
                # Target Path 2: Production Real-time Trigger Rules Injection Array Link
                if st.button("🔔 Queue Real-time WhatsApp Alert Gateway Rule", key=f"al_db_btn_{row.name}", use_container_width=True):
                    rule_payload = f"Immediate notification alert schema dispatched for profile alignment constraints: {t[:30]}..."
                    supabase.table("opporta_alerts").insert({"user_id": current_user_id, "alert_rule": rule_payload, "channel": "whatsapp"}).execute()
                    st.toast("Dispatched rule row block directly onto cloud alert queuing schema.")

with tab_recruitment:
    # Sub-tags
    sub_j_cols = st.columns(4)
    for index, name in enumerate(["All Jobs", "Railway", "Engineering", "Medical"]):
        with sub_j_cols[index]:
            if st.button(f"🔹 {name}" if st.session_state.job_subcat == name else name, key=f"rec_sub_{index}", use_container_width=True):
                st.session_state.job_subcat = name
                st.rerun()
                
    if df_jobs.empty:
        st.markdown('<div class="empty-state">No live jobs loaded.</div>', unsafe_allow_html=True)
    else:
        df_j_view = df_jobs.copy()
        if st.session_state.job_subcat != "All Jobs":
            df_j_view = df_j_view[df_j_view["title"].str.lower().str.contains(st.session_state.job_subcat.lower(), na=False)]
            
        for _, row in df_j_view.sort_values(by="match_score", ascending=False).head(feed_limit).iterrows():
            html_job = f'<div class="opp-card"><div class="opp-title">{row["title"]}</div><div class="opp-meta">{row["agency"]} - {row["state"]}</div><div class="opp-grid"><div class="opp-stat"><div class="opp-stat-label">Vacancies</div><div class="opp-stat-value">{row["vacancies"]}</div></div><div class="opp-stat"><div class="opp-stat-label">Salary</div><div class="opp-stat-value">{row["salary"]}</div></div><div class="opp-stat"><div class="opp-stat-label">Qualification</div><div class="opp-stat-value">{row["qualification"]}</div></div><div class="opp-stat"><div class="opp-stat-label">Deadline</div><div class="opp-stat-value">{row["deadline"]}</div></div><div class="opp-stat"><div class="opp-stat-label">Match Confidence</div><div class="opp-stat-value">{row["match_score"]}%</div></div></div></div>'
            st.markdown(html_job, unsafe_allow_html=True)

# =====================================================================
# 12. TARGET DRIVEN: AI COGNITIVE BID DOCUMENT GENERATOR MODULE
# =====================================================================
with tab_ai_bid:
    st.markdown("#### AI Bid Assistant Room")
    st.caption("Generate optimized procurement and technical documentation arrays instantly.")
    
    l_pdf, r_output = st.columns([1, 1.2])
    with l_pdf:
        doc_file = st.file_uploader("Upload Target Technical Matrix PDF", type=["pdf"], key="bid_pdf_uploader")
        doc_context = st.text_area("Or specify direct contextual tender guidelines", placeholder="Paste analytical context elements here...")
        
        if st.button("🚀 Compile Optimized Bid Documentation Framework", use_container_width=True):
            if not ai_ready:
                st.error("AI Node offline. Provide configuration tokens.")
            elif not doc_file and not doc_context:
                st.warning("Provide documentation nodes or contextual elements to execute.")
            else:
                with st.spinner("🧠 Generating world-class response layouts via Gemini..."):
                    try:
                        generation_blueprint = f"""
                        You are a world-class legal bid coordinator and procurement specialist. 
                        Draft an official corporate Tender Application Cover Letter and EMD Exemption Declaration Request Letter.
                        Align this response precisely to an enterprise operations structure running a {db_profile['business_type']} profile with an active verified financial turnover status estimated at {db_profile['turnover']}.
                        Ensure the formatting incorporates clean professional spaces, headers, and reference elements based on the document text provided.
                        """
                        inputs = [generation_blueprint]
                        if doc_file: inputs.append({"mime_type": "application/pdf", "data": doc_file.getvalue()})
                        if doc_context: inputs.append(doc_context)
                        
                        response = model.generate_content(inputs)
                        st.session_state.bid_doc_output = response.text
                        st.success("Compilation Pipeline Secure.")
                    except Exception as e: st.error(f"Error: {str(e)}")
                    
    with r_output:
        if st.session_state.bid_doc_output:
            st.markdown("##### Compiled Document Preview Output")
            st.text_area("Generated Technical Draft Structure", value=st.session_state.bid_doc_output, height=450)
            st.download_button("📥 Export Compiled Asset Node Text", data=st.session_state.bid_doc_output, file_name="opporta_bid_package.txt")
        else:
            st.markdown('<div class="empty-state">Documentation queue empty. Execute compilation sequence to generate drafts.</div>', unsafe_allow_html=True)

with tab_alerts:
    st.markdown("#### Persisted System Notification Log Channels")
    
    log_c1, log_c2 = st.columns(2)
    with log_c1:
        st.markdown("##### Bookmarked Active Relational Tracks")
        res_saved = supabase.table("opporta_saved").select("opportunity_title").eq("user_id", current_user_id).execute()
        if res_saved.data:
            for item in res_saved.data:
                st.markdown(f"🔖 `Persisted Row Node` - **{item['opportunity_title']}**")
        else: st.info("Ecosystem bookmark repository empty.")
    with log_c2:
        st.markdown("##### Outbound Rule Gateway Alerts Log Queue")
        res_alerts = supabase.table("opporta_alerts").select("alert_rule", "channel").eq("user_id", current_user_id).execute()
        if res_alerts.data:
            for alert in res_alerts.data:
                st.success(f"📱 Channel [{alert['channel'].upper()}] Rule Outflow -> {alert['alert_rule']}")
        else: st.info("Alert rule queues empty.")

with tab_profile:
    st.markdown("#### Cloud Relational Table Profile Node Configurations")
    
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        new_b_type = st.selectbox("Corporate Model Identity Structure", ["Contractor", "Supplier", "Manufacturer", "Transporter"], index=["Contractor", "Supplier", "Manufacturer", "Transporter"].index(db_profile["business_type"]))
        new_turnover = st.text_input("Verified Account Balance Node Turnover Capabilities", value=db_profile["turnover"])
    with col_p2:
        new_class = st.selectbox("Registration Class Tier Alignment Profile", ["Class A", "Class B", "Class C", "Not Applicable"], index=["Class A", "Class B", "Class C", "Not Applicable"].index(db_profile["contractor_class"]))
        new_inds = st.multiselect("Core Domain Focus Clusters", sectors_pool[1:], default=db_profile["industries"])
        
    if st.button("Commit Parameter Configurations Directly to Cloud Infrastructure", use_container_width=True):
        updated_payload = {"business_type": new_b_type, "turnover": new_turnover, "contractor_class": new_class, "industries": new_inds}
        supabase.table("opporta_profiles").update(updated_payload).eq("user_id", current_user_id).execute()
        st.cache_data.clear()
        st.toast("Database schema parameters synchronized successfully.")
        st.rerun()

# =====================================================================
# 13. SYSTEMS INFRASTRUCTURE TELEMETRY FOOTER
# =====================================================================
st.write("---")
st.caption(f"Ecosystem Multi-Tenant Connection Verification Sequence: Connected 🟢 | Secure Active User Session Session ID Node: {current_user_id}")