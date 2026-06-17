import streamlit as st
import pandas as pd
from datetime import datetime
import time
import requests
import feedparser 

# 1. Page Configuration
st.set_page_config(
    page_title="Opporta | Every Opportunity. One Platform.",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Premium SaaS CSS (Added Blur & Freemium Lock Styles)
st.markdown("""
    <style>
    .stApp { background-color: #ffffff; color: #0f172a; font-family: 'Inter', -apple-system, sans-serif; }
    [data-testid="stSidebar"] { background-color: #0f172a !important; border-right: 1px solid #e2e8f0; }
    [data-testid="stSidebar"] * { color: #f8fafc !important; }
    [data-testid="stSidebar"] hr { border-color: #1e293b; }
    .st-emotion-cache-18ni7ap { display: none; }
    div[data-testid="stContainer"] { background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 24px; margin-bottom: 20px; box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.05); transition: transform 0.2s ease, box-shadow 0.2s ease; }
    div[data-testid="stContainer"]:hover { transform: translateY(-2px); box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.08); border-color: #cbd5e1; }
    div[data-testid="stMetric"] { background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 16px; }
    div[data-testid="stMetricLabel"] p { color: #64748b !important; font-size: 13px !important; font-weight: 500; }
    div[data-testid="stMetricValue"] div { color: #0f172a !important; font-weight: 700 !important; font-size: 28px !important; }
    h1, h2, h3 { color: #0f172a !important; font-weight: 700 !important; letter-spacing: -0.5px; }
    .brand-title { color: #0f172a; font-size: 24px; font-weight: 800; letter-spacing: -1px; margin-bottom: 2px;}
    .brand-dot { color: #10b981; }
    .opp-title { font-size: 18px; font-weight: 700; color: #0f172a; margin-bottom: 4px; }
    .opp-org { font-size: 14px; color: #64748b; font-weight: 500; margin-bottom: 16px; }
    .opp-label { font-size: 12px; color: #64748b; margin-bottom: 2px; }
    .opp-value { font-size: 16px; font-weight: 700; color: #0f172a; }
    .badge-eligible { background-color: #ecfdf5; color: #10b981; padding: 4px 10px; border-radius: 20px; font-size: 12px; font-weight: 600; display: inline-block; border: 1px solid #a7f3d0;}
    .badge-review { background-color: #fffbeb; color: #d97706; padding: 4px 10px; border-radius: 20px; font-size: 12px; font-weight: 600; display: inline-block; border: 1px solid #fde68a;}
    .req-box { background-color: #f8fafc; border-left: 3px solid #10b981; padding: 14px 16px; margin-top: 16px; margin-bottom: 16px; border-radius: 4px 8px 8px 4px; font-size: 13px; color: #334155; }
    .req-title { font-weight: 700; color: #0f172a; margin-bottom: 4px; }
    .side-panel { background-color: #f8fafc; border: 1px dashed #cbd5e1; border-radius: 12px; padding: 20px; text-align: center; }
    
    /* THE MAGIC BLUR CLASSES */
    .blurred-text { 
        color: transparent !important; 
        text-shadow: 0 0 8px rgba(15, 23, 42, 0.6); 
        user-select: none; 
    }
    .paywall-overlay {
        background: linear-gradient(0deg, rgba(248,250,252,1) 0%, rgba(248,250,252,0.8) 50%, rgba(248,250,252,0) 100%);
        text-align: center;
        padding-top: 20px;
        margin-top: -40px;
        position: relative;
        z-index: 10;
        font-weight: 700;
        color: #0f172a;
    }
    </style>
""", unsafe_allow_html=True)

# 3. Session State Initialization
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# 4. Data Engine (RSS + CSV)
@st.cache_data(ttl=300) 
def load_and_fetch_data():
    try:
        base_df = pd.read_csv("master_leads.csv")
    except FileNotFoundError:
        base_df = pd.DataFrame()
    try:
        rss_url = "https://feeds.feedburner.com/Tendersinfo" 
        feed = feedparser.parse(rss_url)
        live_tenders = []
        for index, entry in enumerate(feed.entries[:3]):
            live_tenders.append({
                "id": f"RSS_{index}",
                "state": "Live Global Radar",
                "category": "Auto-Fetched Data",
                "organization": "Global Procurement",
                "title": f"⚡ LIVE: {entry.title[:65]}...",
                "project_value": "₹ Dynamic",
                "deadline": entry.get('published', 'Check Portal')[:16],
                "ai_score": "95%",
                "eligibility": "Review Required",
                "emd": "See Portal",
                "contractor_class": "Open",
                "experience": "Any",
                "description": entry.get('summary', 'Detailed description available on the official portal.')[:150] + "...",
                "detailed_requirements": "This is a live opportunity pulled from an active RSS feed. Login to view complete evaluation criteria.",
                "direct_url": entry.link
            })
        api_df = pd.DataFrame(live_tenders)
        combined_df = pd.concat([api_df, base_df], ignore_index=True)
        return combined_df
    except Exception as e:
        return base_df

df = load_and_fetch_data()
safe_ai_scores = pd.to_numeric(df['ai_score'].astype(str).str.replace('%', '', regex=False), errors='coerce').fillna(0)

current_hour = datetime.now().hour
greeting = "Good Morning" if current_hour < 12 else "Good Afternoon" if 12 <= current_hour < 17 else "Good Evening"

# =====================================================================
# 5. THE SIDEBAR (DYNAMIC LOGIN VS PROFILE)
# =====================================================================
with st.sidebar:
    st.markdown("<div class='brand-title'>OPPORTA<span class='brand-dot'>.</span></div>", unsafe_allow_html=True)
    st.caption("Every Opportunity. One Platform.")
    st.write("---")
    
    nav_selection = st.radio("Navigation", ["🏠 Dashboard", "🔍 Opportunities", "🤖 AI Eligibility Check", "🔔 Alerts", "❤️ Saved"], label_visibility="collapsed")
    st.write("---")
    
    if not st.session_state.logged_in:
        # Show Login Box in Sidebar
        st.markdown("### 🔐 Contractor Portal")
        st.caption("Login to unlock official links and unblur requirements.")
        with st.form("sidebar_login"):
            email = st.text_input("Email", placeholder="admin@opporta.in")
            password = st.text_input("Password", type="password", placeholder="••••••••")
            if st.form_submit_button("Sign In", use_container_width=True):
                if email == "admin@opporta.in" and password == "admin123":
                    st.session_state.logged_in = True
                    st.rerun()
                else:
                    st.error("Invalid credentials.")
    else:
        # Show Premium Profile in Sidebar
        st.markdown("""
            <div style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); padding: 16px; border-radius: 12px; color: white;">
                <div style="font-weight: 700; font-size: 14px;">👑 Premium Plan</div>
                <div style="font-size: 12px; opacity: 0.9; margin-top: 4px;">Valid till 24 Jun 2026</div>
            </div>
        """, unsafe_allow_html=True)
        st.write("<br>", unsafe_allow_html=True)
        st.markdown("👤 **Akash Singh**<br><span style='color:#94a3b8; font-size:12px;'>⚙️ Settings</span>", unsafe_allow_html=True)
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()

# =====================================================================
# 6. MAIN DASHBOARD ENGINE
# =====================================================================
if nav_selection == "🏠 Dashboard":
    head_col1, head_col2, head_col3 = st.columns([2, 2, 1])
    with head_col1:
        st.markdown(f"<h2>{greeting}! 👋</h2>", unsafe_allow_html=True)
        st.markdown("<p style='color: #64748b; margin-top: -10px;'>Find, track, and win the right opportunities instantly.</p>", unsafe_allow_html=True)
    with head_col2:
        search_query = st.text_input("Global Search", placeholder="🔍 Search opportunities...", label_visibility="collapsed")
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Opportunities Found", f"{len(df)}", "🟢 Live Radar Active")
    m2.metric("Matching Profile", len(df[safe_ai_scores > 90]), "🎯 High match index")
    m3.metric("Closing Soon", len(df[df['deadline'].astype(str).str.contains('Jul 2026', na=False)]), "⏳ Due this month")
    m4.metric("Saved Leads", "12", "❤️ Saved by you")
    st.write("")

    categories = ["All Opportunities"] + list(df['category'].dropna().unique())
    selected_category = st.radio("Quick Filters", categories, horizontal=True, label_visibility="collapsed")

    feed_col, right_col = st.columns([2.5, 1])
    view_df = df if selected_category == "All Opportunities" else df[df['category'] == selected_category]
    if search_query:
        view_df = view_df[view_df['title'].astype(str).str.contains(search_query, case=False, na=False)]

    with feed_col:
        st.markdown("### Recommended Opportunities")
        for loop_index, (idx, row) in enumerate(view_df.iterrows()):
            with st.container():
                c1, c2, c3, c4 = st.columns([3, 1.2, 1.2, 1.5])
                with c1:
                    st.markdown(f"<div class='opp-title'>{row['title']}</div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='opp-org'>🏢 {row['organization']} &nbsp; | &nbsp; 📍 {row['state']}</div>", unsafe_allow_html=True)
                with c2:
                    st.markdown("<div class='opp-label'>Project Value</div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='opp-value'>{row['project_value']}</div>", unsafe_allow_html=True)
                with c3:
                    st.markdown("<div class='opp-label'>Deadline</div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='opp-value' style='color:#ef4444; font-size:12px;'>{row['deadline']}</div>", unsafe_allow_html=True)
                with c4:
                    st.markdown(f"<div style='text-align:right; font-size:12px; font-weight:700; color:#10b981; margin-top:4px;'>🤖 {row['ai_score']} Match</div>", unsafe_allow_html=True)
                
                # ==========================================
                # THE FREEMIUM LOGIC: Show Data OR Show Blur
                # ==========================================
                if st.session_state.logged_in:
                    # PREMIUM VIEW: Show Everything
                    st.markdown(f"""
                        <div class='req-box'>
                            <div class='req-title'>📋 Project Scope</div>
                            <div style='margin-bottom: 8px;'>{row['description']}</div>
                            <div class='req-title'>⚠️ Key Requirements & Eligibility</div>
                            <div>{row['detailed_requirements']}</div>
                            <hr style='margin: 10px 0; border-color: #cbd5e1;'>
                            <div><strong>Required Tier:</strong> `{row['contractor_class']}` &nbsp;|&nbsp; <strong>EMD:</strong> `{row['emd']}`</div>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    c4_1, c4_2, c4_3 = st.columns([1, 1, 2])
                    c4_1.button("❤️ Save", key=f"save_btn_{loop_index}", use_container_width=True)
                    c4_2.button("📤 Share", key=f"share_btn_{loop_index}", use_container_width=True)
                    c4_3.link_button("🚀 View Official Notice", str(row['direct_url']), use_container_width=True)
                
                else:
                    # GUEST VIEW: Blur the good stuff
                    st.markdown(f"""
                        <div class='req-box'>
                            <div class='req-title'>📋 Project Scope</div>
                            <div style='margin-bottom: 8px;'>{row['description']}</div>
                            <div class='req-title'>⚠️ Key Requirements & Eligibility</div>
                            <div class='blurred-text'>This text is deliberately blurred. You must possess a valid Class-C or higher civil registration. To view the exact financial turnover requirements, EMD deposits, and official links, you need a premium account.</div>
                            <div class='paywall-overlay'>🔒 Login to unlock EMD, Requirements & Links</div>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    st.button("🔒 Upgrade to Premium to Apply", key=f"upgrade_btn_{loop_index}", use_container_width=True, type="primary")

    with right_col:
        st.markdown("### AI Eligibility Check")
        with st.container():
            st.markdown("<div class='side-panel'><div style='font-size:32px;'>☁️</div>**Upload tender document**<br><span style='font-size:12px;color:#64748b;'>Get AI-powered eligibility summary.</span><br><br><span style='background:#f1f5f9; padding:4px 8px; border-radius:4px; font-size:11px;'>🔒 Premium Only</span></div>", unsafe_allow_html=True)

else:
    st.markdown(f"<h2>{nav_selection} Module</h2>", unsafe_allow_html=True)
    if not st.session_state.logged_in:
        st.warning("🔒 Please sign in via the sidebar to access this module.")
    else:
        st.info("Module under active development.")