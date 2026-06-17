import streamlit as st
import pandas as pd
from datetime import datetime

# 1. Page Configuration
st.set_page_config(
    page_title="Opporta | Every Opportunity. One Platform.",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Linear/Stripe Inspired Minimalist CSS
st.markdown("""
    <style>
    /* Global Clean Canvas */
    .stApp { background-color: #ffffff; color: #0f172a; font-family: 'Inter', -apple-system, sans-serif; }
    
    /* Modern Deep Navy Sidebar */
    [data-testid="stSidebar"] { background-color: #0f172a !important; border-right: 1px solid #e2e8f0; }
    [data-testid="stSidebar"] * { color: #f8fafc !important; }
    [data-testid="stSidebar"] hr { border-color: #1e293b; }
    
    /* Hide top header bar gap */
    .st-emotion-cache-18ni7ap { display: none; }
    
    /* Premium Cards & Containers */
    div[data-testid="stContainer"] {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 16px;
        box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.05);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    div[data-testid="stContainer"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.08);
        border-color: #cbd5e1;
    }
    
    /* Metric Cards */
    div[data-testid="stMetric"] { background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 16px; }
    div[data-testid="stMetricLabel"] p { color: #64748b !important; font-size: 13px !important; font-weight: 500; }
    div[data-testid="stMetricValue"] div { color: #0f172a !important; font-weight: 700 !important; font-size: 28px !important; }
    div[data-testid="stMetricDelta"] div { font-size: 12px !important; }
    
    /* Clean Inputs */
    div[data-testid="stTextInput"] input { border-radius: 8px; border: 1px solid #cbd5e1; background-color: #f8fafc; color: #0f172a !important; font-weight: 500; }
    
    /* Elegant Typography */
    h1, h2, h3 { color: #0f172a !important; font-weight: 700 !important; letter-spacing: -0.5px; }
    .brand-title { color: #0f172a; font-size: 24px; font-weight: 800; letter-spacing: -1px; margin-bottom: 2px;}
    .brand-dot { color: #10b981; }
    
    /* Opportunity Card Elements */
    .opp-title { font-size: 18px; font-weight: 700; color: #0f172a; margin-bottom: 4px; }
    .opp-org { font-size: 14px; color: #64748b; font-weight: 500; margin-bottom: 16px; }
    .opp-label { font-size: 12px; color: #64748b; margin-bottom: 2px; }
    .opp-value { font-size: 16px; font-weight: 700; color: #0f172a; }
    
    /* Status Badges */
    .badge-eligible { background-color: #ecfdf5; color: #10b981; padding: 4px 10px; border-radius: 20px; font-size: 12px; font-weight: 600; display: inline-block; border: 1px solid #a7f3d0;}
    .badge-review { background-color: #fffbeb; color: #d97706; padding: 4px 10px; border-radius: 20px; font-size: 12px; font-weight: 600; display: inline-block; border: 1px solid #fde68a;}
    
    /* Alert / Panel Styling */
    .side-panel { background-color: #f8fafc; border: 1px dashed #cbd5e1; border-radius: 12px; padding: 20px; text-align: center; }
    </style>
""", unsafe_allow_html=True)

# 3. Load Data
try:
    df = pd.read_csv("master_leads.csv")
except FileNotFoundError:
    st.error("Database missing.")
    st.stop()

# Dynamic Greeting Logic
current_hour = datetime.now().hour
if current_hour < 12:
    greeting = "Good Morning"
elif 12 <= current_hour < 17:
    greeting = "Good Afternoon"
else:
    greeting = "Good Evening"

# 4. Sidebar Navigation
with st.sidebar:
    st.markdown("<div class='brand-title'>OPPORTA<span class='brand-dot'>.</span></div>", unsafe_allow_html=True)
    st.caption("Every Opportunity. One Platform.")
    st.write("---")
    st.radio("Navigation", ["🏠 Dashboard", "🔍 Opportunities", "🤖 AI Eligibility Check", "🔔 Alerts", "❤️ Saved", "💼 Government Jobs", "📊 Reports"], label_visibility="collapsed")
    st.write("---")
    
    # Premium Badge Widget
    st.markdown("""
        <div style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); padding: 16px; border-radius: 12px; color: white;">
            <div style="font-weight: 700; font-size: 14px;">👑 Premium Plan</div>
            <div style="font-size: 12px; opacity: 0.9; margin-top: 4px;">Valid till 24 Jun 2026</div>
        </div>
    """, unsafe_allow_html=True)
    st.write("<br><br><br>", unsafe_allow_html=True)
    st.markdown("👤 **Akash Singh**<br><span style='color:#94a3b8; font-size:12px;'>⚙️ Settings</span>", unsafe_allow_html=True)

# 5. Top Header & Search
head_col1, head_col2, head_col3 = st.columns([2, 2, 1])
with head_col1:
    st.markdown(f"<h2>{greeting}, Akash! 👋</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color: #64748b; margin-top: -10px;'>Find, track, and win the right opportunities instantly.</p>", unsafe_allow_html=True)
with head_col2:
    search_query = st.text_input("Global Search", placeholder="🔍 Search opportunities, departments, locations...", label_visibility="collapsed")
with head_col3:
    st.markdown("<div style='text-align: right; padding-top: 10px; font-size: 18px;'>💬 &nbsp;&nbsp; 🔔 <span style='background-color:#ef4444; color:white; border-radius:50%; padding:2px 6px; font-size:10px;'>5</span></div>", unsafe_allow_html=True)

# 6. Core Metrics Dashboard
m1, m2, m3, m4 = st.columns(4)
m1.metric("Opportunities Found", f"{len(df)}", "🟢 +12 new this week")
m2.metric("Matching Your Profile", len(df[df['ai_score'].str.rstrip('%').astype(int) > 90]), "🎯 High match index")
m3.metric("Closing Soon", "4", "⏳ Within next 7 days")
m4.metric("Saved Opportunities", "12", "❤️ Saved by you")

st.write("")

# 7. One-Click Horizontal Category Chips (Replacing the clunky multi-selects)
categories = ["All Opportunities"] + list(df['category'].unique())
selected_category = st.radio("Quick Filters", categories, horizontal=True, label_visibility="collapsed")

# 8. Advanced Filters (Hidden behind Expander)
with st.expander("⚙️ Advanced Filters & Location Preferences"):
    f_col1, f_col2, f_col3 = st.columns(3)
    with f_col1:
        st.selectbox("State", ["All India"] + list(df['state'].unique()))
    with f_col2:
        st.selectbox("Contractor Class", ["All"] + list(df['contractor_class'].unique()))
    with f_col3:
        st.selectbox("Experience Match", ["Any", "No Experience", "1-3 Years", "3+ Years"])

st.write("---")

# 9. Main Opportunity Feed & AI Sidebar Split
feed_col, right_col = st.columns([2.5, 1])

# Filter Logic
view_df = df if selected_category == "All Opportunities" else df[df['category'] == selected_category]
if search_query:
    view_df = view_df[view_df['title'].str.contains(search_query, case=False) | view_df['organization'].str.contains(search_query, case=False)]

with feed_col:
    st.markdown("### Recommended Opportunities")
    
    if view_df.empty:
        st.info("No opportunities match this specific filter right now.")
    else:
        for _, row in view_df.iterrows():
            with st.container():
                c1, c2, c3, c4 = st.columns([3, 1.2, 1.2, 1.5])
                
                with c1:
                    st.markdown(f"<div class='opp-title'>{row['title']}</div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='opp-org'>🏢 {row['organization']} &nbsp; | &nbsp; 📍 {row['state']}</div>", unsafe_allow_html=True)
                    st.markdown(f"<span style='background:#f1f5f9; color:#475569; padding:4px 8px; border-radius:4px; font-size:11px; font-weight:600;'>{row['category']}</span>", unsafe_allow_html=True)
                
                with c2:
                    st.markdown("<div class='opp-label'>Project Value</div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='opp-value'>{row['project_value']}</div>", unsafe_allow_html=True)
                    
                with c3:
                    st.markdown("<div class='opp-label'>Deadline</div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='opp-value' style='color:#ef4444;'>{row['deadline']}</div>", unsafe_allow_html=True)
                    
                with c4:
                    status_class = "badge-eligible" if row['eligibility'] == "Eligible" else "badge-review"
                    st.markdown(f"<div style='text-align:right;'><span class='{status_class}'>✓ {row['eligibility']}</span></div>", unsafe_allow_html=True)
                    st.markdown(f"<div style='text-align:right; font-size:12px; font-weight:700; color:#10b981; margin-top:4px;'>🤖 {row['ai_score']} Match</div>", unsafe_allow_html=True)
                    st.write("")
                    c4_1, c4_2 = st.columns(2)
                    c4_1.button("❤️ Save", key=f"save_{row['id']}", use_container_width=True)
                    c4_2.link_button("View Details", row['direct_url'], use_container_width=True)

with right_col:
    st.markdown("### AI Eligibility Check")
    with st.container():
        st.markdown("<div class='side-panel'>", unsafe_allow_html=True)
        st.markdown("<div style='font-size:32px;'>☁️</div>", unsafe_allow_html=True)
        st.markdown("**Upload tender document / PDF**")
        st.caption("Get AI-powered eligibility summary instantly in under 10 seconds.")
        st.file_uploader("Upload", label_visibility="collapsed")
        st.button("Upload & Check", type="primary", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
    st.write("")
    st.markdown("### Recent Alerts")
    with st.container():
        st.markdown("🟢 **New tender matching your profile**")
        st.markdown("<div style='font-size:13px; color:#0284c7;'>Supply of Coal (500 MT) - SECL</div>", unsafe_allow_html=True)
        st.caption("10 mins ago")
        st.write("---")
        st.markdown("🟡 **Bid closing soon**")
        st.markdown("<div style='font-size:13px; color:#0284c7;'>Medical Equipment Supply - GMCH</div>", unsafe_allow_html=True)
        st.caption("1 hour ago")