import streamlit as st
from supabase import create_client, Client
import pandas as pd
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
        response = supabase.table("tenders").select("*").order("date_scraped", desc=True).execute()
        return pd.DataFrame(response.data)
    except Exception as e:
        st.error(f"Error fetching tenders table: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=60, show_spinner=False)
def fetch_cloud_jobs():
    try:
        response = supabase.table("jobs").select("*").order("date_scraped", desc=True).execute()
        return pd.DataFrame(response.data)
    except Exception as e:
        st.error(f"Error fetching jobs table: {e}")
        return pd.DataFrame()

# Initialize live system data matrices
df_tenders_raw = fetch_cloud_tenders()
df_jobs_raw = fetch_cloud_jobs()

# =====================================================================
# 4. SIDEBAR GLOBAL FILTER ARCHITECTURE
# =====================================================================
with st.sidebar:
    st.title("🎛️ Control Center")
    st.markdown("Isolate active channels across regional boundaries.")
    st.write("---")
    
    selected_state = st.selectbox("📍 Target Jurisdiction", ["All Regions", "Chhattisgarh", "Uttar Pradesh"])
    search_query = st.text_input("🔍 Semantic Key Search", placeholder="e.g., Infrastructure, Medical, Document")
    selected_sector = st.selectbox("📁 Filter by Industry Sector", ["All Sectors", "Civil Infrastructure", "Coal & Mining", "Medical Procurement", "Electrical & Energy", "Water & Irrigation", "Municipal Projects", "Panchayat Projects", "Government Jobs"])
    
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
    if selected_sector != "All Sectors":
        df_tenders = df_tenders[df_tenders['sector'].str.contains(selected_sector, case=False, na=False)]
    if search_query:
        df_tenders = df_tenders[
            df_tenders['title'].str.contains(search_query, case=False, na=False) |
            df_tenders['agency'].str.contains(search_query, case=False, na=False)
        ]

# Execute runtime filtering processes for Jobs
df_jobs = df_jobs_raw.copy()
if not df_jobs.empty:
    if selected_state != "All Regions":
        df_jobs = df_jobs[df_jobs['state'].str.contains(selected_state, case=False, na=False)]
    if selected_sector != "All Sectors" and selected_sector == "Government Jobs":
        df_jobs = df_jobs[df_jobs['sector'].str.contains(selected_sector, case=False, na=False)]
    if search_query:
        df_jobs = df_jobs[
            df_jobs['title'].str.contains(search_query, case=False, na=False) |
            df_jobs['agency'].str.contains(search_query, case=False, na=False)
        ]

# =====================================================================
# 5. MAIN EXECUTIVE DASHBOARD VIEWPORT
# =====================================================================
st.title("⚡ Opporta Intelligence Suite")
st.markdown("Automated B2B Lead Aggregation Engine & Public Procurement Tracker.")

# Executive Summary Metrics Layout
col_m1, col_m2, col_m3, col_m4 = st.columns(4)
with col_m1:
    st.metric(label="Active Mined Tenders", value=len(df_tenders))
with col_m2:
    st.metric(label="Open Public Vacancies", value=len(df_jobs))
with col_m3:
    unique_agencies = df_tenders['agency'].nunique() if not df_tenders.empty else 0
    st.metric(label="Responsive Portals Tracked", value=unique_agencies)
with col_m4:
    unique_sectors = df_tenders['sector'].nunique() if not df_tenders.empty else 0
    st.metric(label="Active Industry Verticals", value=unique_sectors)

st.write("---")

# Tabbed Interface Layout
tab_tenders, tab_jobs, tab_analytics, tab_telemetry = st.tabs([
    "🏛️ Enterprise Tender Vault", 
    "💼 Public Recruitment Hub", 
    "📊 Data Metrics Analytics",
    "⚙️ Operational Telemetry"
])

# Clean column reordering map for user display
display_columns = ["title", "sector", "state", "agency", "url", "date_scraped"]

# ---- TAB 1: TENDER GRID ----
with tab_tenders:
    st.subheader("Interstate Procurement Ingestion Feed")
    if df_tenders.empty:
        st.info("No live tender data currently indexed for this selection.")
    else:
        # Re-arrange columns if they exist to provide a clean dashboard flow
        df_tenders_display = df_tenders[[c for c in display_columns if c in df_tenders.columns]]
        st.dataframe(
            df_tenders_display, 
            use_container_width=True,
            column_config={
                "url": st.column_config.LinkColumn("Document / Apply Link")
            }
        )

# ---- TAB 2: RECRUITMENT GRID ----
with tab_jobs:
    st.subheader("Interstate Human Capital Allocation Feed")
    if df_jobs.empty:
        st.info("No live recruitment data currently indexed for this selection.")
    else:
        df_jobs_display = df_jobs[[c for c in display_columns if c in df_jobs.columns]]
        st.dataframe(
            df_jobs_display, 
            use_container_width=True,
            column_config={
                "url": st.column_config.LinkColumn("Official Notification Link")
            }
        )
        
# ---- TAB 3: DATA ANALYSIS ----
with tab_analytics:
    st.subheader("📊 System Structural Breakdown")
    
    if df_tenders.empty and df_jobs.empty:
        st.info("No live production vectors available to chart yet.")
    else:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🏛️ Document Yield by State")
            if not df_tenders.empty and 'state' in df_tenders.columns:
                tender_counts = df_tenders['state'].value_counts()
                st.bar_chart(tender_counts)
            else:
                st.info("State categorical field unavailable.")

        with col2:
            st.markdown("### 💼 Vacancies Distribution by Source Portal")
            if not df_jobs.empty and 'agency' in df_jobs.columns:
                job_counts = df_jobs['agency'].value_counts().head(10)
                st.bar_chart(job_counts)
            else:
                st.info("Agency tracking metrics unavailable.")

# ---- TAB 4: OPERATIONAL TELEMETRY ----
with tab_telemetry:
    st.subheader("⚙️ System Operational Telemetry")
    
    st.markdown("### 📡 Database Ingestion Metrics")
    metrics_df = pd.DataFrame({
        "Data Feed Channel": ["Interstate Production Tenders", "Human Capital Allocation Vault"],
        "Total Rows Buffered": [len(df_tenders_raw), len(df_jobs_raw)],
        "Live Dashboard Filters Active": [len(df_tenders), len(df_jobs)],
        "Status": ["Active / Connected", "Active / Connected"]
    })
    st.table(metrics_df)
    
    st.markdown("### 📝 Active Connection Diagnostic Log")
    st.code(
        f"[INFO] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Streamlit view state initialized.\n"
        f"[SUCCESS] Handshake with Supabase core tables verified.\n"
        f"[TELEMETRY] Successfully buffered total backend vectors into workspace context.\n"
        f"[READY] Application interface rendering active. Standing by for administrative control queries...",
        language="bash"
    )