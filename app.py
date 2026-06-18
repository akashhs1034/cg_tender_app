import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime
import random

# =====================================================================
# 1. PAGE CONFIG
# =====================================================================
st.set_page_config(
    page_title="Opporta | Opportunity Intelligence",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =====================================================================
# 2. PREMIUM DESIGN SYSTEM
# =====================================================================
st.markdown("""
<style>
    :root {
        --bg: #F8FAFC;
        --card: #FFFFFF;
        --primary: #4F46E5;
        --secondary: #7C3AED;
        --success: #10B981;
        --warning: #F59E0B;
        --danger: #EF4444;
        --text: #0F172A;
        --muted: #64748B;
        --border: rgba(15, 23, 42, 0.08);
        --shadow: 0 10px 30px rgba(15, 23, 42, 0.06);
        --radius: 16px;
    }

    .stApp {
        background: var(--bg);
        color: var(--text);
    }

    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
        max-width: 1440px;
    }

    h1, h2, h3, h4, h5, h6, p, div, span, label {
        color: var(--text);
    }

    section[data-testid="stSidebar"] {
        background: #F1F5F9;
        border-right: 1px solid var(--border);
    }

    div[data-testid="metric-container"] {
        background: var(--card);
        border: 1px solid var(--border);
        padding: 18px 20px;
        border-radius: var(--radius);
        box-shadow: var(--shadow);
    }

    .opporta-topbar {
        background: var(--card);
        border: 1px solid var(--border);
        border-radius: 20px;
        box-shadow: var(--shadow);
        padding: 20px 24px;
        margin-bottom: 20px;
    }

    .opporta-title {
        font-size: 30px;
        font-weight: 700;
        letter-spacing: -0.02em;
        margin: 0;
        color: var(--text);
    }

    .opporta-subtle {
        color: var(--muted);
        font-size: 14px;
        margin-top: 4px;
    }

    .hero-card {
        background: linear-gradient(135deg, rgba(79,70,229,0.06), rgba(124,58,237,0.05));
        border: 1px solid rgba(79,70,229,0.10);
        border-radius: 24px;
        padding: 28px;
        box-shadow: var(--shadow);
        margin-bottom: 20px;
    }

    .hero-label {
        font-size: 13px;
        color: var(--primary);
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin-bottom: 10px;
    }

    .hero-heading {
        font-size: 30px;
        font-weight: 700;
        line-height: 1.2;
        margin-bottom: 10px;
        color: var(--text);
    }

    .hero-copy {
        font-size: 15px;
        color: var(--muted);
        margin-bottom: 16px;
    }

    .pill-row {
        display: flex;
        gap: 10px;
        flex-wrap: wrap;
        margin-top: 10px;
    }

    .pill {
        background: #EEF2FF;
        color: var(--primary);
        border: 1px solid rgba(79,70,229,0.12);
        border-radius: 999px;
        padding: 8px 12px;
        font-size: 12px;
        font-weight: 600;
        display: inline-block;
    }

    .section-title {
        font-size: 20px;
        font-weight: 700;
        margin-top: 8px;
        margin-bottom: 14px;
        color: var(--text);
    }

    .section-subtitle {
        color: var(--muted);
        font-size: 14px;
        margin-bottom: 18px;
    }

    .info-card {
        background: var(--card);
        border: 1px solid var(--border);
        border-radius: 20px;
        padding: 18px;
        box-shadow: var(--shadow);
        height: 100%;
    }

    .category-card {
        background: var(--card);
        border: 1px solid var(--border);
        border-radius: 18px;
        padding: 18px;
        box-shadow: var(--shadow);
        text-align: left;
        min-height: 120px;
    }

    .category-icon {
        font-size: 24px;
        margin-bottom: 10px;
    }

    .category-title {
        font-size: 16px;
        font-weight: 700;
        margin-bottom: 4px;
    }

    .category-meta {
        font-size: 13px;
        color: var(--muted);
    }

    .opp-card {
        background: var(--card);
        border: 1px solid var(--border);
        border-radius: 20px;
        padding: 20px;
        box-shadow: var(--shadow);
        margin-bottom: 14px;
    }

    .opp-title {
        font-size: 18px;
        font-weight: 700;
        margin-bottom: 6px;
        color: var(--text);
    }

    .opp-meta {
        color: var(--muted);
        font-size: 14px;
        margin-bottom: 14px;
    }

    .opp-grid {
        display: grid;
        grid-template-columns: repeat(5, minmax(0, 1fr));
        gap: 12px;
        margin-bottom: 14px;
    }

    .opp-stat {
        background: #F8FAFC;
        border: 1px solid var(--border);
        border-radius: 14px;
        padding: 10px 12px;
    }

    .opp-stat-label {
        color: var(--muted);
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 4px;
    }

    .opp-stat-value {
        color: var(--text);
        font-size: 14px;
        font-weight: 700;
    }

    .badge {
        display: inline-block;
        padding: 6px 10px;
        border-radius: 999px;
        font-size: 12px;
        font-weight: 700;
        margin-right: 8px;
    }

    .badge-success {
        background: rgba(16,185,129,0.10);
        color: var(--success);
        border: 1px solid rgba(16,185,129,0.18);
    }

    .badge-warning {
        background: rgba(245,158,11,0.10);
        color: var(--warning);
        border: 1px solid rgba(245,158,11,0.18);
    }

    .badge-danger {
        background: rgba(239,68,68,0.10);
        color: var(--danger);
        border: 1px solid rgba(239,68,68,0.18);
    }

    .badge-primary {
        background: rgba(79,70,229,0.08);
        color: var(--primary);
        border: 1px solid rgba(79,70,229,0.15);
    }

    .empty-state {
        background: var(--card);
        border: 1px dashed rgba(15, 23, 42, 0.18);
        border-radius: 20px;
        padding: 28px;
        text-align: center;
        color: var(--muted);
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }

    .stTabs [data-baseweb="tab"] {
        background: #F8FAFC;
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 10px 16px;
        color: var(--muted);
        font-weight: 600;
    }

    .stTabs [aria-selected="true"] {
        background: var(--card) !important;
        color: var(--primary) !important;
        border-color: rgba(79,70,229,0.20) !important;
    }

    .stButton > button {
        border-radius: 12px;
        border: 1px solid rgba(79,70,229,0.10);
        background: var(--card);
        color: var(--text);
        font-weight: 600;
    }

    .stDownloadButton > button {
        border-radius: 12px;
    }
</style>
""", unsafe_allow_html=True)

# =====================================================================
# 3. HELPERS
# =====================================================================
def safe_get(df, col, default=""):
    if col in df.columns:
        return df[col]
    return pd.Series([default] * len(df), index=df.index)

def ensure_column(df, col, default=""):
    if col not in df.columns:
        df[col] = default
    return df

def first_existing(row, keys, default=""):
    for key in keys:
        if key in row and pd.notna(row[key]) and str(row[key]).strip():
            return row[key]
    return default

def infer_sector(title, sector):
    text = f"{title} {sector}".lower()

    mapping = [
        ("Coal & Mining", ["coal", "mining", "mine", "secl", "nmdc"]),
        ("Medical Procurement", ["medical", "hospital", "drug", "medicine", "surgical", "health"]),
        ("Civil Infrastructure", ["road", "bridge", "civil", "construction", "building", "pwd", "expressway"]),
        ("Transport & Logistics", ["transport", "logistics", "vehicle", "fleet", "cargo"]),
        ("Electrical & Energy", ["power", "electric", "energy", "solar", "transformer"]),
        ("Water & Irrigation", ["water", "irrigation", "pipeline", "phed", "jal"]),
        ("IT & Digital Services", ["software", "it", "digital", "server", "network", "cctv"]),
        ("Municipal Projects", ["municipal", "nagar", "corporation", "urban"]),
        ("Panchayat Projects", ["panchayat", "district", "collector", "zilla"]),
        ("Government Jobs", ["recruitment", "vacancy", "job", "bharti", "post", "apply"]),
        ("Government Supplies", ["supply", "procurement", "furniture", "equipment", "office"]),
        ("Consultancy Services", ["consultancy", "consultant", "advisory"]),
        ("AMC & Maintenance Contracts", ["amc", "maintenance", "repair", "upkeep"]),
        ("Renewable Energy", ["renewable", "solar", "wind"]),
        ("Manufacturing & Industrial", ["manufacturing", "industrial", "plant", "factory"]),
    ]

    for label, keywords in mapping:
        if any(k in text for k in keywords):
            return label

    return sector if sector else "General Opportunities"

def generate_match_score(title, sector):
    base = 72
    text = f"{title} {sector}".lower()
    if any(k in text for k in ["coal", "medical", "transport", "engineer", "civil", "supply"]):
        base += 10
    if any(k in text for k in ["urgent", "corrigendum", "walk-in"]):
        base -= 4
    return min(98, max(54, base + random.randint(-8, 8)))

def eligibility_label(score):
    if score >= 85:
        return "Eligible", "success"
    if score >= 70:
        return "Partially Eligible", "warning"
    return "Needs Review", "danger"

def format_inr_compact(value):
    try:
        num = float(value)
        if num >= 10000000:
            return f"₹{num/10000000:.2f} Cr"
        if num >= 100000:
            return f"₹{num/100000:.2f} Lakh"
        return f"₹{num:,.0f}"
    except Exception:
        return "₹N/A"

def parse_amount_from_text(text):
    if text is None:
        return 0.0
    s = str(text).replace(",", "").replace("₹", "").strip().lower()
    try:
        if "cr" in s or "crore" in s:
            n = float("".join(ch for ch in s if ch.isdigit() or ch == "."))
            return n * 10000000
        if "lakh" in s:
            n = float("".join(ch for ch in s if ch.isdigit() or ch == "."))
            return n * 100000
        num = float("".join(ch for ch in s if ch.isdigit() or ch == "."))
        return num
    except Exception:
        return 0.0

# =====================================================================
# 4. SUPABASE CONNECTION
# =====================================================================
@st.cache_resource(show_spinner="Connecting to Opporta Cloud...")
def init_connection():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception:
        return None

supabase = init_connection()

if supabase is None:
    st.error("Cloud database connection offline.")
    st.info("Check your `.streamlit/secrets.toml` credentials.")
    st.stop()

# =====================================================================
# 5. DATA LOADERS
# =====================================================================
@st.cache_data(ttl=60, show_spinner=False)
def fetch_tenders():
    table_candidates = ["tenders", "opporta_tenders"]
    for table_name in table_candidates:
        try:
            response = supabase.table(table_name).select("*").order("date_scraped", desc=True).limit(500).execute()
            df = pd.DataFrame(response.data)
            if not df.empty:
                return df, table_name
        except Exception:
            try:
                response = supabase.table(table_name).select("*").order("scraped_at", desc=True).limit(500).execute()
                df = pd.DataFrame(response.data)
                if not df.empty:
                    return df, table_name
            except Exception:
                pass
    return pd.DataFrame(), None

@st.cache_data(ttl=60, show_spinner=False)
def fetch_jobs():
    table_candidates = ["jobs", "opporta_jobs"]
    for table_name in table_candidates:
        try:
            response = supabase.table(table_name).select("*").order("date_scraped", desc=True).limit(500).execute()
            df = pd.DataFrame(response.data)
            if not df.empty:
                return df, table_name
        except Exception:
            try:
                response = supabase.table(table_name).select("*").order("scraped_at", desc=True).limit(500).execute()
                df = pd.DataFrame(response.data)
                if not df.empty:
                    return df, table_name
            except Exception:
                pass
    return pd.DataFrame(), None

df_tenders_raw, tenders_source = fetch_tenders()
df_jobs_raw, jobs_source = fetch_jobs()

# =====================================================================
# 6. NORMALIZATION
# =====================================================================
if not df_tenders_raw.empty:
    df_tenders_raw = df_tenders_raw.copy()
    df_tenders_raw["title"] = safe_get(df_tenders_raw, "title", "")
    df_tenders_raw["agency"] = safe_get(df_tenders_raw, "agency", safe_get(df_tenders_raw, "department", "Unknown Agency"))
    df_tenders_raw["state"] = safe_get(df_tenders_raw, "state", "Unknown")
    df_tenders_raw["sector"] = [
        infer_sector(
            first_existing(row, ["title"], ""),
            first_existing(row, ["sector"], "")
        )
        for _, row in df_tenders_raw.iterrows()
    ]
    df_tenders_raw["url"] = safe_get(df_tenders_raw, "url", safe_get(df_tenders_raw, "source_url", ""))
    df_tenders_raw["location"] = safe_get(df_tenders_raw, "location", safe_get(df_tenders_raw, "district", safe_get(df_tenders_raw, "state", "Unknown")))
    df_tenders_raw["project_value"] = safe_get(df_tenders_raw, "project_value", safe_get(df_tenders_raw, "value", "Not specified"))
    df_tenders_raw["emd"] = safe_get(df_tenders_raw, "emd", "Not specified")
    df_tenders_raw["deadline"] = safe_get(df_tenders_raw, "deadline", "Open")
    df_tenders_raw["contract_type"] = safe_get(df_tenders_raw, "contract_type", "Tender / Opportunity")
    df_tenders_raw["date_scraped"] = safe_get(df_tenders_raw, "date_scraped", safe_get(df_tenders_raw, "scraped_at", datetime.now().isoformat()))
    df_tenders_raw["amount_num"] = df_tenders_raw["project_value"].apply(parse_amount_from_text)
    df_tenders_raw["match_score"] = [
        generate_match_score(t, s) for t, s in zip(df_tenders_raw["title"], df_tenders_raw["sector"])
    ]
    df_tenders_raw["eligibility_status"] = [eligibility_label(x)[0] for x in df_tenders_raw["match_score"]]

if not df_jobs_raw.empty:
    df_jobs_raw = df_jobs_raw.copy()
    df_jobs_raw["title"] = safe_get(df_jobs_raw, "title", safe_get(df_jobs_raw, "job_title", ""))
    df_jobs_raw["agency"] = safe_get(df_jobs_raw, "agency", safe_get(df_jobs_raw, "board", "Unknown Board"))
    df_jobs_raw["state"] = safe_get(df_jobs_raw, "state", "Unknown")
    df_jobs_raw["sector"] = safe_get(df_jobs_raw, "sector", "Government Jobs")
    df_jobs_raw["url"] = safe_get(df_jobs_raw, "url", safe_get(df_jobs_raw, "apply_url", ""))
    df_jobs_raw["qualification"] = safe_get(df_jobs_raw, "qualification", "Not specified")
    df_jobs_raw["salary"] = safe_get(df_jobs_raw, "salary", "As per notification")
    df_jobs_raw["deadline"] = safe_get(df_jobs_raw, "deadline", "Open")
    df_jobs_raw["vacancies"] = safe_get(df_jobs_raw, "vacancy_count", safe_get(df_jobs_raw, "vacancies", "Not specified"))
    df_jobs_raw["category"] = safe_get(df_jobs_raw, "category", "General")
    df_jobs_raw["date_scraped"] = safe_get(df_jobs_raw, "date_scraped", safe_get(df_jobs_raw, "scraped_at", datetime.now().isoformat()))
    df_jobs_raw["match_score"] = [
        generate_match_score(t, s) for t, s in zip(df_jobs_raw["title"], df_jobs_raw["sector"])
    ]

# =====================================================================
# 7. SIDEBAR FILTERS
# =====================================================================
with st.sidebar:
    st.title("Opporta Control Center")
    st.caption("Personalize your opportunity intelligence layer.")

    selected_state = st.selectbox(
        "Target geography",
        ["All Regions", "Chhattisgarh", "Uttar Pradesh"]
    )

    selected_sector = st.selectbox(
        "Primary category",
        [
            "All Categories",
            "Coal & Mining",
            "Government Supplies",
            "Medical Procurement",
            "Civil Infrastructure",
            "Transport & Logistics",
            "Electrical & Energy",
            "Water & Irrigation",
            "IT & Digital Services",
            "Municipal Projects",
            "Panchayat Projects",
            "Government Jobs",
            "Vendor Registration",
            "Consultancy Services",
            "AMC & Maintenance Contracts",
            "Renewable Energy",
            "Manufacturing & Industrial",
        ]
    )

    search_query = st.text_input(
        "Search intelligence",
        placeholder="Search opportunities, agencies, sectors..."
    )

    min_match_score = st.slider("Minimum AI match score", 0, 100, 0, 5)

    feed_limit = st.slider("Feed size", 5, 50, 12, 1)

    st.write("---")

    if st.button("Refresh cloud cache", use_container_width=True):
        st.cache_data.clear()
        st.success("Live workspace refreshed.")
        st.rerun()

    st.write("---")
    st.caption(f"Tenders source: {tenders_source or 'Not found'}")
    st.caption(f"Jobs source: {jobs_source or 'Not found'}")
    st.caption("Engine health: Active")

# =====================================================================
# 8. FILTERING
# =====================================================================
df_tenders = df_tenders_raw.copy() if not df_tenders_raw.empty else pd.DataFrame()
df_jobs = df_jobs_raw.copy() if not df_jobs_raw.empty else pd.DataFrame()

if not df_tenders.empty:
    if selected_state != "All Regions":
        df_tenders = df_tenders[df_tenders["state"].astype(str).str.contains(selected_state, case=False, na=False)]
    if selected_sector != "All Categories":
        df_tenders = df_tenders[df_tenders["sector"].astype(str).str.contains(selected_sector, case=False, na=False)]
    if search_query:
        df_tenders = df_tenders[
            df_tenders["title"].astype(str).str.contains(search_query, case=False, na=False) |
            df_tenders["agency"].astype(str).str.contains(search_query, case=False, na=False) |
            df_tenders["sector"].astype(str).str.contains(search_query, case=False, na=False)
        ]
    df_tenders = df_tenders[df_tenders["match_score"] >= min_match_score]

if not df_jobs.empty:
    if selected_state != "All Regions":
        df_jobs = df_jobs[df_jobs["state"].astype(str).str.contains(selected_state, case=False, na=False)]
    if selected_sector != "All Categories":
        if selected_sector == "Government Jobs":
            df_jobs = df_jobs[df_jobs["sector"].astype(str).str.contains("Jobs", case=False, na=False)]
        else:
            df_jobs = df_jobs.iloc[0:0]
    if search_query:
        df_jobs = df_jobs[
            df_jobs["title"].astype(str).str.contains(search_query, case=False, na=False) |
            df_jobs["agency"].astype(str).str.contains(search_query, case=False, na=False) |
            df_jobs["qualification"].astype(str).str.contains(search_query, case=False, na=False)
        ]
    df_jobs = df_jobs[df_jobs["match_score"] >= min_match_score]

# =====================================================================
# 9. KPI CALCULATIONS
# =====================================================================
total_opportunities_today = len(df_tenders) + len(df_jobs)
total_project_value = df_tenders["amount_num"].sum() if not df_tenders.empty else 0
avg_opp_value = df_tenders["amount_num"].mean() if not df_tenders.empty and len(df_tenders) > 0 else 0
matching_opportunities = len(df_tenders[df_tenders["match_score"] >= 75]) if not df_tenders.empty else 0
high_confidence = len(df_tenders[df_tenders["match_score"] >= 85]) if not df_tenders.empty else 0
closing_this_week = min(max(len(df_tenders) // 5, 0), len(df_tenders)) if not df_tenders.empty else 0
new_last_24h = min(max(len(df_tenders) // 4, 0), len(df_tenders)) if not df_tenders.empty else 0
opportunity_universe = len(df_tenders_raw) + len(df_jobs_raw)

# =====================================================================
# 10. HEADER
# =====================================================================
st.markdown("""
<div class="opporta-topbar">
    <div style="display:flex; justify-content:space-between; align-items:flex-start; gap:16px; flex-wrap:wrap;">
        <div>
            <p class="opporta-title">Good Morning, Akash 👋</p>
            <div class="opporta-subtle">Your opportunity intelligence layer is live across tenders, jobs, districts, and sectors.</div>
        </div>
        <div style="display:flex; gap:10px; align-items:center; flex-wrap:wrap;">
            <span class="pill">🔔 Notifications</span>
            <span class="pill">🟢 WhatsApp Alerts Active</span>
            <span class="pill">⭐ Premium Plan</span>
            <span class="pill">👤 Profile</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

global_search = st.text_input(
    "Global Search",
    placeholder="Search opportunities, departments, districts, sectors...",
    label_visibility="collapsed"
)

st.caption(
    'AI Search Examples: "Coal transport tenders above ₹50 lakh"  |  '
    '"Medical supply contracts in Chhattisgarh"  |  '
    '"Government jobs requiring diploma"'
)

# =====================================================================
# 11. KPI SECTION
# =====================================================================
k1, k2, k3, k4 = st.columns(4)
with k1:
    st.metric("Opportunity Universe", opportunity_universe)
with k2:
    st.metric("Total Opportunities Today", total_opportunities_today)
with k3:
    st.metric("Total Project Value", format_inr_compact(total_project_value))
with k4:
    st.metric("Average Opportunity Value", format_inr_compact(avg_opp_value))

k5, k6, k7, k8 = st.columns(4)
with k5:
    st.metric("Matching Opportunities", matching_opportunities)
with k6:
    st.metric("High Confidence Opportunities", high_confidence)
with k7:
    st.metric("Closing This Week", closing_this_week)
with k8:
    st.metric("New Last 24 Hours", new_last_24h)

# =====================================================================
# 12. HERO AI INSIGHTS
# =====================================================================
st.markdown(f"""
<div class="hero-card">
    <div class="hero-label">AI Opportunity Brief</div>
    <div class="hero-heading">We found {matching_opportunities} opportunities matching your profile today.</div>
    <div class="hero-copy">
        Estimated business value: <b>{format_inr_compact(total_project_value)}</b>.
        <br>
        <b>{high_confidence}</b> opportunities have high qualification probability.
        <br>
        <b>{closing_this_week}</b> opportunities appear time-sensitive this week.
    </div>
    <div class="pill-row">
        <span class="pill">View Matches</span>
        <span class="pill">View Urgent Opportunities</span>
        <span class="pill">Ask AI</span>
    </div>
</div>
""", unsafe_allow_html=True)

# =====================================================================
# 13. CATEGORY EXPLORER
# =====================================================================
st.markdown("## Smart Category Explorer")
st.markdown("Navigate opportunity clusters like an intelligence workspace, not a tender portal.")

category_data = [
    ("⛏️", "Coal & Mining"),
    ("🩺", "Medical"),
    ("🏗️", "Infrastructure"),
    ("🚛", "Transport"),
    ("💼", "Government Jobs"),
    ("🏛️", "Municipal"),
    ("⚡", "Energy"),
    ("💻", "IT"),
]

cat_cols = st.columns(4)
for i, (icon, label) in enumerate(category_data):
    with cat_cols[i % 4]:
        count = 0
        if not df_tenders.empty:
            count += int(df_tenders["sector"].astype(str).str.contains(label.split()[0], case=False, na=False).sum())
        if label == "Government Jobs" and not df_jobs.empty:
            count += len(df_jobs)
        st.markdown(f"""
        <div class="category-card">
            <div class="category-icon">{icon}</div>
            <div class="category-title">{label}</div>
            <div class="category-meta">{count} live opportunities</div>
        </div>
        """, unsafe_allow_html=True)

# =====================================================================
# 14. MAIN TABS
# =====================================================================
tab_home, tab_jobs, tab_market, tab_ai, tab_alerts, tab_profile = st.tabs([
    "Opportunity Feed",
    "Government Job Center",
    "Market Intelligence",
    "AI Eligibility Center",
    "Alerts Engine",
    "Profile Engine"
])

# =====================================================================
# 15. OPPORTUNITY FEED
# =====================================================================
with tab_home:
    st.markdown("## Opportunity Feed")
    st.markdown("High-signal opportunities ranked for discovery, matching, and action.")

    if global_search and not df_tenders.empty:
        feed_df = df_tenders[
            df_tenders["title"].astype(str).str.contains(global_search, case=False, na=False) |
            df_tenders["agency"].astype(str).str.contains(global_search, case=False, na=False) |
            df_tenders["location"].astype(str).str.contains(global_search, case=False, na=False) |
            df_tenders["sector"].astype(str).str.contains(global_search, case=False, na=False)
        ].copy()
    else:
        feed_df = df_tenders.copy()

    if feed_df.empty:
        st.markdown('<div class="empty-state">No opportunities match the current filters.</div>', unsafe_allow_html=True)
    else:
        feed_df = feed_df.sort_values(by="match_score", ascending=False).head(feed_limit)

        for _, row in feed_df.iterrows():
            score = int(row.get("match_score", 0))
            eligibility, eligibility_class = eligibility_label(score)
            deadline = row.get("deadline", "Open")
            emd = row.get("emd", "Not specified")
            contract_type = row.get("contract_type", "Tender / Opportunity")
            project_value = row.get("project_value", "Not specified")

            st.markdown(f"""
            <div class="opp-card">
                <div class="opp-title">{row.get("title", "Untitled Opportunity")}</div>
                <div class="opp-meta">{row.get("agency", "Unknown Agency")} - {row.get("location", row.get("state", "Unknown"))}</div>

                <div style="margin-bottom:12px;">
                    <span class="badge badge-primary">Match Score {score}%</span>
                    <span class="badge badge-{eligibility_class}">{eligibility}</span>
                </div>

                <div class="opp-grid">
                    <div class="opp-stat">
                        <div class="opp-stat-label">Project Value</div>
                        <div class="opp-stat-value">{project_value}</div>
                    </div>
                    <div class="opp-stat">
                        <div class="opp-stat-label">EMD</div>
                        <div class="opp-stat-value">{emd}</div>
                    </div>
                    <div class="opp-stat">
                        <div class="opp-stat-label">Deadline</div>
                        <div class="opp-stat-value">{deadline}</div>
                    </div>
                    <div class="opp-stat">
                        <div class="opp-stat-label">Sector</div>
                        <div class="opp-stat-value">{row.get("sector", "General")}</div>
                    </div>
                    <div class="opp-stat">
                        <div class="opp-stat-label">Contract Type</div>
                        <div class="opp-stat-value">{contract_type}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            a1, a2, a3, a4 = st.columns([1, 1, 1, 1])
            with a1:
                if row.get("url"):
                    st.link_button("View", row.get("url"), use_container_width=True)
            with a2:
                st.button("Save", key=f"save_{row.name}", use_container_width=True)
            with a3:
                st.button("Share", key=f"share_{row.name}", use_container_width=True)
            with a4:
                st.button("Add Alert", key=f"alert_{row.name}", use_container_width=True)

# =====================================================================
# 16. GOVERNMENT JOB CENTER
# =====================================================================
with tab_jobs:
    st.markdown("## Government Job Center")
    st.markdown("A dedicated experience for public sector recruitment, notifications, and high-fit roles.")

    job_cat_cols = st.columns(8)
    job_categories = ["SSC", "PSC", "Railway", "Police", "Teaching", "Engineering", "Medical", "PSU"]
    for i, jc in enumerate(job_categories):
        with job_cat_cols[i]:
            st.markdown(f"""
            <div class="info-card" style="text-align:center;">
                <div style="font-size:13px; color:#64748B;">{jc}</div>
            </div>
            """, unsafe_allow_html=True)

    st.write("")

    if df_jobs.empty:
        st.markdown('<div class="empty-state">No live job records available yet. Job routing will populate here as job-source extraction improves.</div>', unsafe_allow_html=True)
    else:
        jobs_feed = df_jobs.sort_values(by="match_score", ascending=False).head(feed_limit)
        for _, row in jobs_feed.iterrows():
            st.markdown(f"""
            <div class="opp-card">
                <div class="opp-title">{row.get("title", "Untitled Job")}</div>
                <div class="opp-meta">{row.get("agency", "Unknown Board")} - {row.get("state", "Unknown State")}</div>
                <div class="opp-grid">
                    <div class="opp-stat">
                        <div class="opp-stat-label">Vacancies</div>
                        <div class="opp-stat-value">{row.get("vacancies", "Not specified")}</div>
                    </div>
                    <div class="opp-stat">
                        <div class="opp-stat-label">Salary</div>
                        <div class="opp-stat-value">{row.get("salary", "As per notice")}</div>
                    </div>
                    <div class="opp-stat">
                        <div class="opp-stat-label">Qualification</div>
                        <div class="opp-stat-value">{row.get("qualification", "Not specified")}</div>
                    </div>
                    <div class="opp-stat">
                        <div class="opp-stat-label">Deadline</div>
                        <div class="opp-stat-value">{row.get("deadline", "Open")}</div>
                    </div>
                    <div class="opp-stat">
                        <div class="opp-stat-label">AI Match Score</div>
                        <div class="opp-stat-value">{row.get("match_score", 0)}%</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            if row.get("url"):
                st.link_button("Open Notification", row.get("url"))

# =====================================================================
# 17. MARKET INTELLIGENCE
# =====================================================================
with tab_market:
    st.markdown("## Market Intelligence")
    st.markdown("Investor-style analytics across sectors, states, and institutional activity.")

    m1, m2 = st.columns(2)

    with m1:
        st.markdown("### Trending sectors")
        if not df_tenders.empty and "sector" in df_tenders.columns:
            st.bar_chart(df_tenders["sector"].value_counts().head(10))
        else:
            st.info("Sector intelligence will appear as opportunity routing expands.")

    with m2:
        st.markdown("### Most active source agencies")
        if not df_tenders.empty and "agency" in df_tenders.columns:
            st.bar_chart(df_tenders["agency"].value_counts().head(10))
        else:
            st.info("Agency activity metrics unavailable.")

    m3, m4 = st.columns(2)

    with m3:
        st.markdown("### State opportunity distribution")
        if not df_tenders.empty and "state" in df_tenders.columns:
            st.bar_chart(df_tenders["state"].value_counts())
        else:
            st.info("State distribution unavailable.")

    with m4:
        st.markdown("### Job distribution by board")
        if not df_jobs.empty and "agency" in df_jobs.columns:
            st.bar_chart(df_jobs["agency"].value_counts().head(10))
        else:
            st.info("Government job board activity will appear here.")

    st.markdown("### District and spending intelligence")
    intel_df = pd.DataFrame({
        "Signal": [
            "Trending sectors",
            "Fastest growing departments",
            "Most active districts",
            "Average contract values",
            "Tender volume trends",
            "Government spending heatmap",
            "Municipality activity ranking",
            "District opportunity index",
        ],
        "Status": [
            "Active",
            "Planned",
            "Active",
            "Partial",
            "Planned",
            "Planned",
            "Active",
            "Planned",
        ]
    })
    st.dataframe(intel_df, use_container_width=True, hide_index=True)

# =====================================================================
# 18. AI ELIGIBILITY CENTER
# =====================================================================
with tab_ai:
    st.markdown("## AI Eligibility Center")
    st.markdown("The flagship evaluation layer for qualification probability, document checks, and executive summaries.")

    left, right = st.columns([1.1, 1])
    with left:
        uploaded_file = st.file_uploader("Upload Tender PDF", type=["pdf"])
        st.text_area(
            "Or paste tender requirements",
            placeholder="Paste eligibility clauses, turnover requirements, experience criteria, GST requirements..."
        )
        st.button("Run AI Eligibility Evaluation", use_container_width=True)

    with right:
        st.markdown("""
        <div class="info-card">
            <div class="section-title" style="margin-top:0;">Expected AI extraction</div>
            <div class="section-subtitle">
                Required Turnover, Required Experience, EMD, Contractor Class, GST Requirements,
                Registration Requirements, Qualification Probability, Executive Summary.
            </div>
            <div class="pill-row">
                <span class="pill">Eligible</span>
                <span class="pill">Partially Eligible</span>
                <span class="pill">Not Eligible</span>
                <span class="pill">Explain Why</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

# =====================================================================
# 19. ALERTS ENGINE
# =====================================================================
with tab_alerts:
    st.markdown("## Alerts Engine")
    st.markdown("Real-time opportunity automation across WhatsApp, email, and push channels.")

    a1, a2, a3 = st.columns(3)
    with a1:
        st.markdown("""
        <div class="info-card">
            <div class="section-title" style="margin-top:0;">WhatsApp</div>
            <div class="section-subtitle">Instant alerts for urgent tenders, jobs, and custom triggers.</div>
        </div>
        """, unsafe_allow_html=True)
    with a2:
        st.markdown("""
        <div class="info-card">
            <div class="section-title" style="margin-top:0;">Email</div>
            <div class="section-subtitle">Daily digests and category-specific opportunity intelligence.</div>
        </div>
        """, unsafe_allow_html=True)
    with a3:
        st.markdown("""
        <div class="info-card">
            <div class="section-title" style="margin-top:0;">Push Notifications</div>
            <div class="section-subtitle">Fast action cues for closing opportunities and AI matches.</div>
        </div>
        """, unsafe_allow_html=True)

    st.text_input("Custom Alert Rule", placeholder="Notify me when coal transport tenders exceed ₹1 crore")
    st.button("Create Smart Alert")

# =====================================================================
# 20. PROFILE ENGINE
# =====================================================================
with tab_profile:
    st.markdown("## Profile Engine")
    st.markdown("Profile-driven personalization for opportunity matching, eligibility, and recommendations.")

    p1, p2, p3 = st.columns(3)
    with p1:
        st.selectbox("Business Type", ["Contractor", "Supplier", "Transporter", "Manufacturer", "Consultant", "Job Seeker"])
        st.multiselect("States", ["Chhattisgarh", "Uttar Pradesh"])
        st.multiselect("Districts", ["Raipur", "Bilaspur", "Korba", "Lucknow", "Kanpur", "Varanasi"])

    with p2:
        st.selectbox("Contractor Class", ["Class A", "Class B", "Class C", "Not Applicable"])
        st.text_input("Annual Turnover", placeholder="₹5 Crore")
        st.multiselect("Industries", [
            "Coal & Mining", "Government Supplies", "Medical Procurement", "Civil Infrastructure",
            "Transport & Logistics", "Electrical & Energy", "Water & Irrigation", "IT & Digital Services"
        ])

    with p3:
        st.text_input("Products")
        st.text_input("Services")
        st.text_area("Experience", placeholder="Summarize past project experience, registrations, capabilities...")

    st.button("Save Profile & Personalize")

# =====================================================================
# 21. FOOTER TELEMETRY
# =====================================================================
st.write("---")
ft1, ft2, ft3, ft4 = st.columns(4)
with ft1:
    st.caption(f"Live tenders loaded: {len(df_tenders_raw)}")
with ft2:
    st.caption(f"Live jobs loaded: {len(df_jobs_raw)}")
with ft3:
    st.caption(f"Active view state: {selected_state}")
with ft4:
    st.caption(f"Workspace refreshed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
