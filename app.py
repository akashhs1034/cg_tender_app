import streamlit as st
import pandas as pd
import os
from datetime import datetime

# ==========================================
# 1. VISUAL INTERFACE THEME CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="Interstate B2B & Jobs Intelligence Portal", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom High-Contrast Styling Matrices
st.markdown("""
    <style>
    .main { background-color: #fcfcfc; }
    div[data-testid="stMetricValue"] { font-size: 2.2rem; font-weight: 700; color: #0f172a; }
    .stTabs [data-baseweb="tab"] { font-size: 1.1rem; font-weight: 600; padding: 14px 28px; }
    .stTabs [aria-selected="true"] { border-bottom-color: #0284c7 !important; color: #0284c7 !important; }
    .stAlert { border-radius: 8px; }
    </style>
""", unsafe_allow_html=True)

def calculate_days_left(deadline_str):
    try:
        current_date = datetime.now().date()
        deadline_date = datetime.strptime(str(deadline_str).strip(), '%Y-%m-%d').date()
        delta = (deadline_date - current_date).days
        if delta < 0: return "❌ Expired"
        elif delta == 0: return "🚨 Closing TODAY"
        elif delta == 1: return "⏳ 1 Day Left"
        else: return f"📅 {delta} Days Left"
    except Exception:
        return "⏱️ Active Notification"

# ==========================================
# 2. CACHED PRODUCTION DATA PIPELINE OPERATORS
# ==========================================
@st.cache_data(ttl=60)
def load_clean_tender_data():
    if os.path.exists("master_tenders.csv") and os.path.getsize("master_tenders.csv") > 10:
        df = pd.read_csv("master_tenders.csv")
    else:
        df = pd.DataFrame({
            'tender_id': ['NIT-SECL-2026-889', 'UP-PWD-2026-E09'],
            'state': ['Chhattisgarh', 'Uttar Pradesh'],
            'department': ['SECL (Govt PSU)', 'UP PWD (Govt)'],
            'location_district': ['Korba', 'Lucknow'],
            'work_category': ['Mining', 'Civil'],
            'estimated_value_lakhs': [450.00, 1450.00],
            'closing_deadline': ['2026-07-10', '2026-07-25']
        })
        
    df['state'] = df['state'].fillna('Not Specified').astype(str).str.strip()
    df = df.dropna(subset=['tender_id'])
    df['estimated_value_lakhs'] = pd.to_numeric(df['estimated_value_lakhs'], errors='coerce').fillna(0.0)
    df['Status / Deadline'] = df['closing_deadline'].apply(calculate_days_left)

    # Core Segment Parsing Logic
    df['is_coal'] = df['work_category'].str.contains('Coal|Mining|Mines|Evacuation', case=False, na=False) | df['department'].str.contains('SECL|NMDC', case=False, na=False)
    df['is_supply'] = df['work_category'].str.contains('Supply|Material|Equipment|Purchase|Goods', case=False, na=False)
    df['is_private'] = df['department'].str.contains('Jindal|JSP|Balco|Adani|Tata|Private|Ltd', case=False, na=False)
    df['is_civil'] = df['work_category'].str.contains('Civil|Road|Bridge|Building|Construction|Highway', case=False, na=False)
    return df

@st.cache_data(ttl=60)
def load_clean_job_data():
    if os.path.exists("master_jobs.csv") and os.path.getsize("master_jobs.csv") > 10:
        df = pd.read_csv("master_jobs.csv")
    else:
        df = pd.DataFrame({
            'job_title': ['Assistant Professor', 'UP Subordinate Services Recruitment'],
            'state': ['Chhattisgarh', 'Uttar Pradesh'],
            'department': ['CGPSC (Govt)', 'UPPSC (Govt)'],
            'vacancies': [140, 450],
            'qualification': ['Post Graduate', 'Graduate Degree'],
            'deadline': ['2026-07-10', '2026-07-18']
        })
    df['state'] = df['state'].fillna('Not Specified').astype(str).str.strip()
    df['vacancies'] = pd.to_numeric(df['vacancies'], errors='coerce').fillna(0).astype(int)
    df['Status / Urgency'] = df['deadline'].apply(calculate_days_left)
    return df

df_tenders = load_clean_tender_data()
df_jobs = load_clean_job_data()

# ==========================================
# 3. CONTROL FILTER PANEL MATRIX (SIDEBAR)
# ==========================================
st.sidebar.header("🌍 Central Navigation Engine")

# Master Regional Intersection Logic
all_available_states = sorted(list(set(df_tenders['state'].unique()).union(set(df_jobs['state'].unique()))))
selected_state = st.sidebar.selectbox("Target Regional Feed:", ["All Regions"] + all_available_states)

st.sidebar.markdown("---")
st.sidebar.subheader("🔍 Advanced Core Text Filtering")
search_query = st.sidebar.text_input("Search Across Records:", "", placeholder="Type keywords (e.g. Civil, Korba)")

# Apply Regional Intersections Instantly
if selected_state != "All Regions":
    df_tenders = df_tenders[df_tenders['state'] == selected_state]
    df_jobs = df_jobs[df_jobs['state'] == selected_state]

# Apply Real-Time Text Query Intersections Instantly
if search_query:
    q = search_query.lower()
    df_tenders = df_tenders[
        df_tenders['tender_id'].str.lower().str.contains(q) | 
        df_tenders['department'].str.lower().str.contains(q) | 
        df_tenders['work_category'].str.lower().str.contains(q)
    ]
    df_jobs = df_jobs[
        df_jobs['job_title'].str.lower().str.contains(q) | 
        df_jobs['department'].str.lower().str.contains(q)
    ]

# ==========================================
# 4. BUSINESS INTELLIGENCE INTERFACE LAYOUT
# ==========================================
st.title("💼 B2B Interstate Intelligence & Career Portal")
st.caption("Production Data Viewport | Automated Multi-State Aggregator System Node")
st.markdown("---")

tab_tenders, tab_jobs, tab_charts = st.tabs(["📈 Commercial Procurement Leases", "🎓 Corporate & Civil Careers", "📊 Analytical Market Overviews"])

# ==========================================
# 5. TAB 1: B2B TENDERS DATA LEDGER
# ==========================================
with tab_tenders:
    st.markdown("### 🔍 Target Segment Screening Matrix")
    c1, c2 = st.columns([1, 2])
    
    with c1:
        sector_filter = st.selectbox(
            "Filter Sector Profiles:",
            ["Show All Active Industries", "Coal & Mineral Ingestion Only", "Material Logistics & Supply Only", "Private Enterprise Pipeline", "Infrastructure & Civil Works Only"]
        )
    with c2:
        max_val = float(df_tenders['estimated_value_lakhs'].max()) if not df_tenders.empty else 100.0
        min_slider = st.slider("Filter Minimum Contract Volume Allocation (In Lakhs):", 0.0, max_val, 0.0, step=5.0)

    filtered_tenders = df_tenders[df_tenders['estimated_value_lakhs'] >= min_slider]
    
    if sector_filter == "Coal & Mineral Ingestion Only":
        filtered_tenders = filtered_tenders[filtered_tenders['is_coal'] == True]
    elif sector_filter == "Material Logistics & Supply Only":
        filtered_tenders = filtered_tenders[filtered_tenders['is_supply'] == True]
    elif sector_filter == "Private Enterprise Pipeline":
        filtered_tenders = filtered_tenders[filtered_tenders['is_private'] == True]
    elif sector_filter == "Infrastructure & Civil Works Only":
        filtered_tenders = filtered_tenders[filtered_tenders['is_civil'] == True]

    # Render Macro Analytical Operational Summary Metric Rows
    m1, m2, m3, m4 = st.columns(4)
    with m1: st.metric("Selected B2B Records", f"{len(filtered_tenders)} Contracts")
    with m2: st.metric("Heavy Energy/Coal Pipeline", f"{df_tenders['is_coal'].sum()} Leads")
    with m3: st.metric("Corporate Private Activity", f"{df_tenders['is_private'].sum()} Portals")
    with m4: st.metric("Gross Pipeline Value Pool", f"₹ {filtered_tenders['estimated_value_lakhs'].sum():,.2f} L")

    st.markdown("### 📊 Verified Operational Business Transaction Leads Ledger")
    if filtered_tenders.empty:
        st.info("No corporate asset descriptions currently match the configured filtering criteria.")
    else:
        display_tenders = filtered_tenders[['tender_id', 'state', 'department', 'work_category', 'estimated_value_lakhs', 'Status / Deadline']].copy()
        display_tenders.columns = ['Tender Contract Reference ID', 'Target State Domain', 'Issuing Authority / Enterprise', 'Industrial Domain Profile', 'Estimated CapEx Volume (Lakhs)', 'Temporal Operational Status']
        st.dataframe(display_tenders, use_container_width=True, hide_index=True)
        
        # Download Button Element
        csv_data = display_tenders.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Export Selected Commercial Leads Dataset (.CSV)", data=csv_data, file_name="Filtered_Commercial_Tenders.csv", mime="text/csv")

# ==========================================
# 6. TAB 2: LIVE CAREER OPENINGS MATRIX
# ==========================================
with tab_jobs:
    st.markdown("### 🎓 State-Level Strategic Employment Systems Viewport")
    
    j1, j2 = st.columns(2)
    with j1: st.metric("Active Corporate & Civil Employment Records", f"{len(df_jobs)} Postings")
    with j2: st.metric("Aggregated Human Resource Gross Capacities", f"{df_jobs['vacancies'].sum()} Listed Seats")
        
    st.markdown("### 📄 Operational Carrier Structural Position Ledger")
    if df_jobs.empty:
        st.info("No strategic vocational data segments found matching the input matrix coordinates.")
    else:
        display_jobs = df_jobs[['job_title', 'state', 'department', 'vacancies', 'qualification', 'Status / Urgency']].copy()
        display_jobs.columns = ['Vocation System Title Designation', 'Target State Domain', 'Deploying Department Board', 'Human Capacity Seats', 'Prerequisite Qualifications', 'Temporal Horizon Status']
        st.dataframe(display_jobs, use_container_width=True, hide_index=True)
        
        csv_job_data = display_jobs.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Export Selected Human Resource Capacities Dataset (.CSV)", data=csv_job_data, file_name="Filtered_Human_Resource_Vacancies.csv", mime="text/csv")

# ==========================================
# 7. TAB 3: EXECUTIVE MARKET ANALYTICS VIEW
# ==========================================
with tab_charts:
    st.markdown("### 📊 Automated Multi-State Market Intelligence Insights")
    
    if not df_tenders.empty:
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            st.markdown("**CapEx Distribution Breakdown Across Target Regions (Lakhs)**")
            state_spending = df_tenders.groupby('state')['estimated_value_lakhs'].sum()
            st.bar_chart(state_spending)
        with col_c2:
            st.markdown("**Procurement Transaction Count Density Map Across Sectors**")
            sector_counts = df_tenders.groupby('work_category').size()
            st.bar_chart(sector_counts)
    else:
        st.warning("Insufficient multi-state statistical transactional arrays to compute layout visual metrics.")