import streamlit as st
import pandas as pd
from supabase import create_client, Client

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Opporta | Enterprise Engine", page_icon="⚡", layout="wide")

# --- DATABASE CONNECTION ---
@st.cache_resource
def init_connection() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_connection()

# --- SIDEBAR: HYPER-LOCAL FILTERS ---
st.sidebar.image("https://via.placeholder.com/300x100.png?text=OPPORTA+ENGINE", use_container_width=True)
st.sidebar.markdown("---")
st.sidebar.header("📍 Hyper-Local Targeting")

selected_state = st.sidebar.selectbox(
    "Select State", 
    ["All States", "Chhattisgarh", "Madhya Pradesh", "Maharashtra"]
)

selected_district = st.sidebar.selectbox(
    "Select District", 
    ["All Districts", "State-wide", "Raipur", "Bilaspur", "Durg", "Bhilai", "Korba", "Bastar"]
)
st.sidebar.markdown("---")
st.sidebar.info("Data is synced daily at 07:30 AM IST via Opporta Cloud Pipeline.")

# --- MAIN DASHBOARD UI ---
st.title("⚡ Opporta Intelligence Dashboard")
st.markdown("Discover, analyze, and win hyper-local government opportunities.")

tab1, tab2 = st.tabs(["🏗️ Government Tenders", "🏛️ Government Jobs"])

# ==========================================
# TAB 1: GOVERNMENT TENDERS
# ==========================================
with tab1:
    st.subheader("Live Government Contracts")
    
    # Fetch Data
    try:
        response = supabase.table("tenders").select("*").execute()
        df_tenders = pd.DataFrame(response.data)
    except Exception as e:
        st.error(f"Failed to fetch tenders: {e}")
        df_tenders = pd.DataFrame()

    if not df_tenders.empty:
        # Apply Filters
        if selected_state != "All States":
            df_tenders = df_tenders[df_tenders['state'] == selected_state]
        if selected_district != "All Districts":
            df_tenders = df_tenders[df_tenders['district'] == selected_district]

        if df_tenders.empty:
            st.warning("No tenders match your current local filters. Try expanding your search.")
        else:
            # Display Tenders
            for index, row in df_tenders.iterrows():
                with st.expander(f"📌 {row.get('title', 'Untitled Tender')} | Location: {row.get('district', 'N/A')}"):
                    st.write("**Details:**")
                    st.write(row.get('details', 'No details provided.'))
                    
                    st.markdown("---")
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        # Document Link Feature
                        doc_link = row.get("document_link")
                        if doc_link and str(doc_link).startswith("http"):
                            st.link_button("🔗 View Official Document", doc_link)
                        else:
                            st.button("🔗 Document Not Provided", disabled=True, key=f"doc_{index}")
                            
                    with col2:
                        if st.button("🤖 AI Win Predictor", key=f"win_{index}"):
                            st.info("AI Analysis: Based on standard parameters, this looks like a solid match. (Connect to Gemini backend for live prediction)")
                            
                    with col3:
                        if st.button("📝 Auto-Draft Bid", key=f"bid_{index}"):
                            st.success("Drafting proposal... (Connect to Gemini backend for text generation)")
    else:
        st.info("Awaiting initial data sync. The autopilot will populate this shortly.")

# ==========================================
# TAB 2: GOVERNMENT JOBS
# ==========================================
with tab2:
    st.subheader("Open Government Positions")
    
    # Categorized Job Hub (Pill Navigation)
    job_categories = ["All", "Health", "Police", "Education", "Administration", "Engineering", "General"]
    selected_category = st.radio("Filter strictly by industry:", job_categories, horizontal=True)
    
    st.markdown("---")

    # Fetch Data
    try:
        response_jobs = supabase.table("jobs").select("*").execute()
        df_jobs = pd.DataFrame(response_jobs.data)
    except Exception as e:
        st.error(f"Failed to fetch jobs: {e}")
        df_jobs = pd.DataFrame()

    if not df_jobs.empty:
        # Apply Location Filters
        if selected_state != "All States":
            df_jobs = df_jobs[df_jobs['state'] == selected_state]
        if selected_district != "All Districts":
            df_jobs = df_jobs[df_jobs['district'] == selected_district]
            
        # Apply Category Filter
        if selected_category != "All":
            df_jobs = df_jobs[df_jobs['category'] == selected_category]

        if df_jobs.empty:
            st.warning(f"No {selected_category} jobs currently available in your selected location.")
        else:
            # Display Jobs
            for index, row in df_jobs.iterrows():
                with st.expander(f"💼 {row.get('title', 'Untitled Position')} | {row.get('category', 'General')}"):
                    st.write("**Eligibility & Details:**")
                    st.write(row.get('details', 'No details provided.'))
                    st.write(f"**Location:** {row.get('district', 'State-wide')}, {row.get('state', 'Chhattisgarh')}")
    else:
        st.info("Awaiting initial data sync. The autopilot will populate this shortly.")