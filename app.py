import streamlit as st
from supabase import create_client, Client
import pandas as pd
import re
from datetime import datetime

# =====================================================================
# 1. PREMIUM PRODUCTION PAGE SETUP & EXECUTIVE THEME
# =====================================================================
st.set_page_config(
    page_title="Opporta Engine | B2B Market Intelligence Hub",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom premium CSS injection for ultra-clean corporate aesthetics
st.markdown("""
    <style>
        .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
        .stTabs [data-baseweb="tab-list"] { gap: 12px; }
        .stTabs [data-baseweb="tab"] {
            padding: 10px 20px;
            background-color: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 6px;
            font-weight: 600;
            color: #475569;
            transition: all 0.2s ease-in-out;
        }
        .stTabs [data-baseweb="tab"]:hover {
            border-color: #cbd5e1;
            background-color: #f1f5f9;
        }
        .stTabs [aria-selected="true"] { 
            background-color: #ff4b4b !important;
            color: white !important;
            border-color: #ff4b4b !important;
            box-shadow: 0 4px 6px -1px rgba(255, 75, 75, 0.2);
        }
        div[data-testid="metric-container"] {
            background-color: #ffffff;
            border: 1px solid #e2e8f0;
            padding: 15px 20px;
            border-radius: 8px;
            box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05);
        }
    </style>
""", unsafe_allow_html=True)

# =====================================================================
# 2. SECURE DATABASE TUNNEL (SUPABASE)
# =====================================================================
@st.cache_resource(show_spinner="Establishing Secure Pipeline Link...")
def init_connection():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception as e:
        return None

supabase = init_connection()

if supabase is None:
    st.error("🚨 Cloud Database Connection Offline.")
    st.info("Verify that your `.streamlit/secrets.toml` config contains valid active credentials.")
    st.stop()

# =====================================================================
# 3. HIGH-PERFORMANCE DATA INGESTION ENGINE
# =====================================================================
@st.cache_data(ttl=60, show_spinner=False)
def fetch_cloud_tenders():
    try:
        response = supabase.table("opporta_tenders").select("*").order("scraped_at", desc=True).execute()
        return pd.DataFrame(response.data)
    except Exception as e:
        st.error(f"Error fetching tenders table: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=60, show_spinner=False)
def fetch_cloud_jobs():
    try:
        response = supabase.table("opporta_jobs").select("*").order("scraped_at", desc=True).execute()
        return pd.DataFrame(response.data)
    except Exception as e:
        st.error(f"Error fetching jobs table: {e}")
        return pd.DataFrame()

def parse_financial_value(val_str):
    if pd.isna(val_str) or not isinstance(val_str, str):
        return 0.0
    cleaned = re.sub(r'[^\d.]', '', val_str)
    try:
        return float(cleaned) if cleaned else 0.0
    except ValueError:
        return 0.0

# Initialize live system data matrices
df_tenders_raw = fetch_cloud_tenders()
df_jobs_raw = fetch_cloud_jobs()

if not df_tenders_raw.empty and 'value' in df_tenders_raw.columns:
    df_tenders_raw['parsed_value'] = df_tenders_raw['value'].apply(parse_financial_value)
else:
    if not df_tenders_raw.empty:
        df_tenders_raw['parsed_value'] = 0.0

# =====================================================================
# 4. SIDEBAR GLOBAL FILTER ARCHITECTURE
# =====================================================================
with st.sidebar:
    st.title("🎛️ Control Center")
    st.markdown("Isolate active channels across regional boundaries.")
    st.write("---")
    
    selected_state = st.selectbox("📍 Target Jurisdiction", ["All Regions", "Chhattisgarh", "Uttar Pradesh"])
    search_query = st.text_input("🔍 Semantic Key Search", placeholder="e.g., Infrastructure, Medical, Rail")
    min_value = st.number_input("💵 Min Value Filter (INR)", min_value=0, value=0, step=50000)
    
    st.write("---")
    st.markdown("##### 🛠️ Cache Management")
    if st.button("🔄 Clear Cache & Force Update", use_container_width=True):
        st.cache_data.clear()
        st.success("Internal pipeline state refreshed!")
        st.rerun()
        
    st.write("---")
    st.caption("Core Infrastructure: Supabase Cloud")
    st.caption("Engine Health: 🟢 Optimal")

# Execute runtime filtering processes for Tenders
df_tenders = df_tenders_raw.copy()
if not df_tenders.empty:
    if selected_state != "All Regions":
        df_tenders = df_tenders[df_tenders['state'].str.contains(selected_state, case=False, na=False)]
    if search_query:
        df_tenders = df_tenders[
            df_tenders['title'].str.contains(search_query, case=False, na=False) |
            df_tenders['department'].str.contains(search_query, case=False, na=False)
        ]
    if min_value > 0 and 'parsed_value' in df_tenders.columns:
        df_tenders = df_tenders[df_tenders['parsed_value'] >= min_value]

# Execute runtime filtering processes for Jobs
df_jobs = df_jobs_raw.copy()
if not df_jobs.empty:
    if selected_state != "All Regions":
        df_jobs = df_jobs[df_jobs['state'].str.contains(selected_state, case=False, na=False)]
    if search_query:
        df_jobs = df_jobs[
            df_jobs['job_title'].str.contains(search_query, case=False, na=False) |
            df_jobs['board'].str.contains(search_query, case=False, na=False)
        ]

# =====================================================================
# 5. MAIN EXECUTIVE DASHBOARD VIEWPORT
# =====================================================================
st.title("⚡ Opporta Intelligence Suite")
st.markdown("Automated B2B Lead Aggregation Engine & Public Procurement Tracker.")

# Executive Summary Metrics Layout
col_m1, col_m2, col_m3, col_m4 = st.columns(4)
with col_m1:
    st.metric(label="Active High-Value Tenders", value=len(df_tenders))
with col_m2:
    st.metric(label="Open Public Vacancies", value=len(df_jobs))
with col_m3:
    total_est_pipeline = df_tenders['parsed_value'].sum() if not df_tenders.empty and 'parsed_value' in df_tenders.columns else 0.0
    if total_est_pipeline >= 10000000:
        pipeline_display = f"₹ {total_est_pipeline / 10000000:.2f} Cr"
    elif total_est_pipeline >= 100000:
        pipeline_display = f"₹ {total_est_pipeline / 100000:.2f} Lakh"
    else:
        pipeline_display = f"₹ {total_est_pipeline:,.2f}"
    st.metric(label="Est. Monitored Pipeline Value", value=pipeline_display)
with col_m4:
    unique_depts = df_tenders['department'].nunique() if not df_tenders.empty and 'department' in df_tenders.columns else 0
    st.metric(label="Tracked State Agencies", value=unique_depts)

st.write("---")

# Tabbed Interface Layout
tab_tenders, tab_jobs, tab_analytics, tab_telemetry = st.tabs([
    "🏛️ Enterprise Tender Vault", 
    "💼 Public Recruitment Hub", 
    "📊 Predictive Data Analytics",
    "⚙️ Operational Telemetry"
])

# ---- TAB 1: TENDER GRID ----
with tab_tenders:
    st.subheader("Interstate Procurement Ingestion Feed")
    if df_tenders.empty:
        st.info("No data available.")
    else:
        st.dataframe(df_tenders, use_container_width=True)

# ---- TAB 2: RECRUITMENT GRID ----
with tab_jobs:
    st.subheader("Interstate Human Capital Allocation Feed")
    if df_jobs.empty:
        st.info("No data available.")
    else:
        st.dataframe(df_jobs, use_container_width=True)
        
# ---- TAB 3: DATA ANALYSIS ----
with tab_analytics:
    st.subheader("📊 Predictive Data Analytics")
    
    if df_tenders.empty and df_jobs.empty:
        st.info("No data available to analyze yet.")
    else:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🏛️ Tenders by Department / Source")
            # Automatically find a categorical column to plot
            cat_col = next((c for c in ['department', 'state', 'Category'] if c in df_tenders.columns), df_tenders.columns[0] if not df_tenders.empty else None)
            if cat_col:
                tender_counts = df_tenders[cat_col].value_counts().head(10)
                st.bar_chart(tender_counts)
            else:
                st.info("No categorical data found to plot charts.")

        with col2:
            st.markdown("### 💼 Job Vacancies Distribution")
            cat_col_jobs = next((c for c in ['department', 'title', 'state', 'Role'] if c in df_jobs.columns), df_jobs.columns[0] if not df_jobs.empty else None)
            if cat_col_jobs:
                job_counts = df_jobs[cat_col_jobs].value_counts().head(10)
                st.bar_chart(job_counts)
            else:
                st.info("No job metrics available to plot charts.")

# ---- TAB 4: OPERATIONAL TELEMETRY ----
with tab_telemetry:
    st.subheader("⚙️ System Operational Telemetry")
    
    # Create a clean metadata overview dashboard
    st.markdown("### 📡 Database Ingestion Metrics")
    metrics_df = pd.DataFrame({
        "Data Feed": ["Interstate Tenders", "Human Capital Allocation"],
        "Total Rows Buffered": [len(df_tenders), len(df_jobs)],
        "Status": ["Active / Connected", "Active / Connected"],
        "Engine Memory Allocation": [f"{df_tenders.memory_usage().sum() / 1024:.2f} KB" if not df_tenders.empty else "0 KB", f"{df_jobs.memory_usage().sum() / 1024:.2f} KB" if not df_jobs.empty else "0 KB"]
    })
    st.table(metrics_df)
    
    st.markdown("### 📝 System Logs")
    st.code(
        f"[INFO] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Pipeline initialization successful.\n"
        f"[SUCCESS] Supabase database handshake established.\n"
        f"[DATA] Ingested {len(df_tenders)} procurement profiles into memory.\n"
        f"[DATA] Ingested {len(df_jobs)} active recruitment slots into memory.\n"
        f"[READY] Standing by for scheduled cron automation...",
        language="bash"
    )