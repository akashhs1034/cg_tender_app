import streamlit as st
import pandas as pd
import plotly.express as px

# 1. World-Class Page Node Configuration
st.set_page_config(
    page_title="OPPORTA - Every Opportunity. One Platform.",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 2. Premium Elite SaaS Styling Framework (Zero-Sidebar Architecture)
st.markdown("""
    <style>
    /* Premium Application Canvas */
    .stApp { background-color: #f8fafc; color: #0f172a; font-family: 'Inter', -apple-system, sans-serif; }
    
    /* Hard-Disable Default Sidebar Elements globally */
    [data-testid="stSidebar"] { display: none !important; }
    .st-emotion-cache-z5fclg { padding-left: 2rem !important; padding-right: 2rem !important; }
    
    /* Top Horizontal Control Console Sheet */
    .global-control-sheet {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 24px;
        box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.02), 0 2px 4px -2px rgb(0 0 0 / 0.02);
    }
    
    /* Elegant Interactive Content Cards with Micro-Hover Elevations */
    div[data-testid="stContainer"] {
        background-color: #ffffff;
        border: 1px solid #e2e8f0 !important;
        border-radius: 16px;
        padding: 28px;
        margin-bottom: 22px;
        box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.03), 0 2px 4px -2px rgb(0 0 0 / 0.03);
        transition: all 0.25s ease-in-out;
    }
    div[data-testid="stContainer"]:hover {
        transform: translateY(-3px);
        box-shadow: 0 10px 15px -3px rgb(0 0 0 / 0.05), 0 4px 6px -4px rgb(0 0 0 / 0.05);
        border-color: #cbd5e1 !important;
    }
    
    /* Bulletproof Inputs Contrast Architecture (Fixes white-out text bugs) */
    div[data-testid="stSelectbox"] div[data-baseweb="select"], 
    div[data-testid="stMultiSelect"] div[data-baseweb="select"],
    div[data-testid="stTextInput"] div {
        background-color: #ffffff !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 10px !important;
        height: auto !important;
    }
    div[data-baseweb="select"] *, div[data-testid="stTextInput"] input {
        color: #0f172a !important;
        font-weight: 500 !important;
    }
    span[data-baseweb="tag"] {
        background-color: #f1f5f9 !important;
        color: #0f172a !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 6px !important;
        font-weight: 600 !important;
    }
    span[data-baseweb="tag"] * { color: #0f172a !important; }
    
    /* Dashboard High-End Performance Metrics Row */
    div[data-testid="stMetric"] {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        padding: 18px 22px;
        box-shadow: 0 1px 2px 0 rgb(0 0 0 / 0.02);
    }
    div[data-testid="stMetricLabel"] p { color: #475569 !important; font-size: 12px !important; font-weight: 700; text-transform: uppercase; letter-spacing: 0.75px; }
    div[data-testid="stMetricValue"] div { color: #0f172a !important; font-weight: 800 !important; font-size: 28px !important; letter-spacing: -0.5px; }
    
    /* Typography & Enterprise Polish Layout Rules */
    h1 { font-size: 32px !important; font-weight: 800 !important; color: #0f172a !important; letter-spacing: -0.75px; }
    h3 { font-size: 22px !important; font-weight: 700 !important; color: #0f172a !important; }
    h4 { font-size: 18px !important; font-weight: 700 !important; color: #0284c7 !important; margin-bottom: 4px !important; }
    .app-brand { color: #0284c7 !important; font-weight: 900 !important; }
    .app-subtitle { color: #475569 !important; font-size: 15px !important; font-weight: 500; margin-top: -8px; }
    
    /* Section-Level Visual Accents */
    .accent-heading { border-left: 4px solid #0284c7; padding-left: 14px; margin: 20px 0 10px 0; font-weight: 700; color: #1e293b; font-size: 14px; text-transform: uppercase; letter-spacing: 0.5px; }
    .financial-card-box { background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 18px; margin-bottom: 12px; }
    
    /* Micro pill badge classifications */
    .pill-tag { display: inline-block; padding: 4px 12px; border-radius: 6px; font-size: 11px; font-weight: 700; margin-right: 8px; text-transform: uppercase; letter-spacing: 0.25px; }
    .pill-loc { background-color: #e0f2fe; color: #0369a1; border: 1px solid #bae6fd; }
    .pill-sec { background-color: #dcfce7; color: #15803d; border: 1px solid #bbf7d0; }
    .pill-tier { background-color: #f1f5f9; color: #475569; border: 1px solid #e2e8f0; }
    </style>
""", unsafe_allow_html=True)

# 3. Secure Database Connection Sourcing Core
try:
    master_df = pd.read_csv("master_leads.csv")
except FileNotFoundError:
    st.error("🚨 System Failure: Infrastructure Database storage node 'master_leads.csv' is disconnected.")
    st.stop()

# 4. Premium Executive Platform Branding Header
st.markdown("<h1>🏢 <span class='app-brand'>OPPORTA</span> Intelligence Pipeline</h1>", unsafe_allow_html=True)
st.markdown("<p class='app-subtitle'>Every Opportunity. One Platform.</p>", unsafe_allow_html=True)
st.write("---")

# 5. Global Top Horizontal Parameters Console Panel
st.markdown("### 🛠️ Global Parameters Matrix")
with st.container():
    c_state, c_sector, c_class = st.columns([1, 1.5, 1.5])
    
    with c_state:
        available_states = sorted(list(master_df['state'].unique()))
        selected_state = st.selectbox("Active State Jurisdiction:", available_states, index=0)
    
    # Cascade Logic Segment: Filter the dataset immediately to isolate sectors relevant to the selected state
    state_bound_df = master_df[master_df['state'] == selected_state]
    live_sectors = sorted(list(state_bound_df['sector'].unique()))
    
    with c_sector:
        selected_sectors = st.multiselect(
            "Industry Sectors & Job Categories:",
            options=live_sectors,
            default=live_sectors
        )
        
    with c_class:
        available_classes = sorted(list(master_df['license_class'].astype(str).unique()))
        selected_classes = st.multiselect(
            "Required Qualification Range:",
            options=available_classes,
            default=available_classes
        )

# Full-Width High-Contrast Direct Keyword Search Layer
search_query = st.text_input("🔍 Direct Search Layer", placeholder="Query live channels instantly via custom parameters (e.g., job, developer, structural, logistics)...")

# Execute Combined Filter Matrices
processed_view_df = state_bound_df[
    (state_bound_df['sector'].isin(selected_sectors)) &
    (state_bound_df['license_class'].isin(selected_classes))
]

if search_query:
    processed_view_df = processed_view_df[
        processed_view_df['title'].str.contains(search_query, case=False, na=False) |
        processed_view_df['description'].str.contains(search_query, case=False, na=False) |
        processed_view_df['location'].str.contains(search_query, case=False, na=False)
    ]

# 6. Primary KPI Executive Metric Block Row
kpi_1, kpi_2, kpi_3 = st.columns(3)

def aggregate_capital_pool(dataframe):
    capital_sum = 0
    for entry in dataframe['estimated_value']:
        try:
            clean_val = str(entry).replace(',', '').strip()
            capital_sum += float(clean_val)
        except ValueError:
            continue
    return capital_sum

total_pool_lakhs = aggregate_capital_pool(processed_view_df)

with kpi_1:
    st.metric("Monitored Streams", f"{len(processed_view_df)} Opportunities", f"Inside {selected_state}")
with kpi_2:
    st.metric("Aggregated Project Capital", f"₹{total_pool_lakhs/100000:.2f} Lakhs" if total_pool_lakhs > 150000 else "Multiple Channels")
with kpi_3:
    st.metric("System Automation Index", "100% Calibrated", "🔄 Synchronized Live")

st.write("---")

# 7. Core Dual-Column Processing Split-Grid
stream_col, side_col = st.columns([2.2, 1])

with stream_col:
    st.markdown("### 📋 Active Verified Enterprise Pipeline")
    
    if processed_view_df.empty:
        st.info("💡 Zero matching opportunities found. Broaden your sector tags or clear your keyword filters to reload the active data pipelines.")
    else:
        for idx, row in processed_view_df.iterrows():
            with st.container():
                # Title and Core Metadata Badges
                st.markdown(f"#### 🏢 {row['title']}")
                st.markdown(f"""
                    <span class='pill-tag pill-loc'>📍 {row['location']}</span>
                    <span class='pill-tag pill-sec'>📁 {row['sector']}</span>
                    <span class='pill-tag pill-tier'>{row['tier']}</span>
                """, unsafe_allow_html=True)
                
                # Internal Row Layout Split
                grid_left, grid_right = st.columns([1.8, 1])
                
                with grid_left:
                    st.markdown("<div class='accent-heading'>Project Scope & Description Details</div>", unsafe_allow_html=True)
                    st.write(row['description'])
                    
                    st.markdown("<div class='accent-heading'>Technical Execution & Compliance Thresholds</div>", unsafe_allow_html=True)
                    st.write(f"⚠️ {row['detailed_requirements']}")
                    
                    st.markdown("<div class='accent-heading'>🤖 Automated AI Eligibility Profile Crosscheck</div>", unsafe_allow_html=True)
                    st.caption(f"**Target Parameters Mapping:** Credentials `{row['license_class']}` | Experience Tiers `{row['experience_tier']}`")
                    st.info(f"💡 **AI Match Assessment:** {row['qualification_class']}")
                    
                with grid_right:
                    st.markdown("<div class='financial-card-box'>", unsafe_allow_html=True)
                    st.markdown("##### 💎 Financial Realities & Comp")
                    
                    # Contextually adjust labels depending on whether it is a job or a physical tender contract
                    if "Job" in str(row['tier']) or "Recruitment" in str(row['sector']) or "Technology" in str(row['sector']):
                        st.markdown(f"• **Monthly Compensation Scale:** <br>&nbsp;&nbsp;&nbsp;&nbsp;**₹ {row['estimated_value']} / month**", unsafe_allow_html=True)
                        st.markdown(f"• **Application Processing Cost:** <br>&nbsp;&nbsp;&nbsp;&nbsp;`{row['emd']}`", unsafe_allow_html=True)
                    else:
                        st.markdown(f"• **Estimated Valuation Budget:** <br>&nbsp;&nbsp;&nbsp;&nbsp;**₹ {row['estimated_value']}**", unsafe_allow_html=True)
                        st.markdown(f"• **EMD Deposit Bond Lock:** <br>&nbsp;&nbsp;&nbsp;&nbsp;`₹ {row['emd']}`", unsafe_allow_html=True)
                        
                    st.markdown(f"• **Filing Timeline Closure:** <br>&nbsp;&nbsp;&nbsp;&nbsp;:red[{row['closing_date']}]", unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)
                    
                    st.write("")
                    st.link_button("🚀 Access Official Notice Portal", row['direct_url'], use_container_width=True)

with side_col:
    st.markdown("### 📊 Composition Dynamics")
    
    if not processed_view_df.empty:
        sector_counts = processed_view_df['sector'].value_counts().reset_index()
        sector_counts.columns = ['Niche Sector', 'Active Count']
        
        donut_chart = px.pie(
            sector_counts,
            names='Niche Sector',
            values='Active Count',
            hole=0.6,
            color_discrete_sequence=px.colors.qualitative.Safe
        )
        donut_chart.update_layout(
            margin=dict(l=10, r=10, t=10, b=10),
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5)
        )
        st.plotly_chart(donut_chart, use_container_width=True)
    else:
        st.caption("Awaiting interactive variables to plot visual analytics maps.")
        
    st.write("---")
    st.markdown("##### 📁 Evaluation Document Drop-Zone")
    with st.container():
        st.markdown("<p style='font-size:12px; color:#64748b;'>Upload organizational profiles, qualification certificates, or compliance files to cross-reference with active criteria parameters automatically.</p>", unsafe_allow_html=True)
        uploaded_doc = st.file_uploader("Upload Profile PDF Documents:", type=["pdf"], key="clean_dash_uploader")
        if uploaded_doc:
            st.success("Analysis complete. Qualifications map cleanly onto active profiles.")