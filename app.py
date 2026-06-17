import streamlit as st
import pandas as pd
from supabase import create_client, Client

# 1. Page Configuration
st.set_config(page_title="Opporta | Dual-Engine", layout="wide")

# 2. Premium CSS
st.markdown("""
    <style>
    .stApp { background-color: #ffffff; color: #0f172a; font-family: 'Inter', sans-serif; }
    [data-testid="stSidebar"] { background-color: #0f172a !important; }
    .req-box { background-color: #f8fafc; border-left: 4px solid #10b981; padding: 20px; border-radius: 8px; margin: 15px 0; }
    .job-box { background-color: #f8fafc; border-left: 4px solid #3b82f6; padding: 20px; border-radius: 8px; margin: 15px 0; }
    </style>
""", unsafe_allow_html=True)

# 3. Database Connection
@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_connection()

# Fetch Data from Cloud
@st.cache_data(ttl=300)
def fetch_data(table_name):
    response = supabase.table(table_name).select("*").order('scraped_at', desc=True).execute()
    return pd.DataFrame(response.data)

# 4. Auth State
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

# Sidebar
with st.sidebar:
    st.markdown("### OPPORTA.")
    if not st.session_state.logged_in:
        with st.form("login"):
            if st.text_input("Email") == "admin@opporta.in" and st.text_input("Password", type="password") == "admin123":
                if st.form_submit_button("Sign In"): 
                    st.session_state.logged_in = True
                    st.rerun()
    else:
        st.success("👑 Premium Active")
        if st.button("Logout"): 
            st.session_state.logged_in = False
            st.rerun()

# 5. UI Master Toggle
st.title("Good Morning, Akash! 👋")
st.write("---")

engine_mode = st.radio("Select Intelligence Module:", ["🏢 Government Tenders (B2B)", "🎓 Government Jobs (B2C)"], horizontal=True)

st.write("---")

# =====================================================================
# MODULE 1: TENDERS
# =====================================================================
if engine_mode == "🏢 Government Tenders (B2B)":
    try:
        df_tenders = fetch_data("opporta_tenders")
        if not df_tenders.empty:
            col1, col2 = st.columns([1, 2])
            selected_state = col1.selectbox("📍 State Jurisdiction", ["All"] + list(df_tenders['state'].unique()))
            selected_cat = col2.selectbox("🏗️ Sector", ["All"] + list(df_tenders['sector'].unique()))

            view_df = df_tenders if selected_state == "All" else df_tenders[df_tenders['state'] == selected_state]
            if selected_cat != "All": view_df = view_df[view_df['sector'] == selected_cat]

            for i, row in view_df.iterrows():
                with st.container():
                    st.subheader(row['title'])
                    st.write(f"🏢 **{row['department']}** | 💰 **{row['value']}** | ⏳ Deadline: {row['deadline']}")
                    
                    if st.session_state.logged_in:
                        st.markdown(f"<div class='req-box'><b>Sector:</b> {row['sector']}<br><b>State:</b> {row['state']}</div>", unsafe_allow_html=True)
                        st.link_button("Access Portal", str(row['source_url']))
                    else:
                        st.warning("🔒 Login to view portal links and automated bid drafting features.")
                    st.write("---")
        else:
            st.info("No tender data available yet. Waiting for pipeline execution.")
    except Exception as e:
        st.error("Database connection pending. Please configure Supabase.")

# =====================================================================
# MODULE 2: JOBS
# =====================================================================
elif engine_mode == "🎓 Government Jobs (B2C)":
    try:
        df_jobs = fetch_data("opporta_jobs")
        if not df_jobs.empty:
            col1, col2 = st.columns([1, 2])
            selected_state = col1.selectbox("📍 State", ["All"] + list(df_jobs['state'].unique()))
            selected_board = col2.selectbox("🏛️ Recruitment Board", ["All"] + list(df_jobs['board'].unique()))

            view_df = df_jobs if selected_state == "All" else df_jobs[df_jobs['state'] == selected_state]
            if selected_board != "All": view_df = view_df[view_df['board'] == selected_board]

            for i, row in view_df.iterrows():
                with st.container():
                    st.subheader(row['job_title'])
                    st.write(f"🏛️ **{row['board']}** | 👥 Vacancies: **{row['vacancy_count']}**")
                    
                    if st.session_state.logged_in:
                        st.markdown(f"<div class='job-box'><b>Qualification Required:</b> {row['qualification']}</div>", unsafe_allow_html=True)
                        st.link_button("1-Click Apply (RPA)", str(row['apply_url']), type="primary")
                    else:
                        st.warning("🔒 Login to view qualifications and unlock 1-Click Apply.")
                    st.write("---")
        else:
            st.info("No job data available yet. Waiting for pipeline execution.")
    except Exception as e:
        st.error("Database connection pending. Please configure Supabase.")