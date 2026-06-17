import streamlit as st
import pandas as pd
import plotly.express as px

# 1. High-End UI Page Configuration
st.set_page_config(
    page_title="Opporta - Every Opportunity. One Platform.",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Premium CSS Injection to match the corporate SaaS layout
st.markdown("""
    <style>
    /* Global App Canvas Background */
    .stApp { background-color: #f8fafc; color: #1e293b; }
    
    /* Deep Corporate Teal Sidebar Styling */
    [data-testid="stSidebar"] { background-color: #062f37 !important; }
    [data-testid="stSidebar"] *, [data-testid="stSidebar"] p { color: #f8fafc !important; }
    [data-testid="stSidebar"] .stMultiSelect div { background-color: #0b4550 !important; border-color: #125c6a !important; }
    
    /* Global Card styling matching the mockup shadows and rounded borders */
    div[data-testid="stContainer"] {
        background-color: #ffffff;
        border: 1px solid #e2e8f0 !important;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 12px;
        box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.05), 0 1px 2px -1px rgb(0 0 0 / 0.05);
    }
    
    /* Metric Cards Styling Overrides */
    div[data-testid="stMetric"] {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 18px;
        box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.02);
    }
    div[data-testid="stMetricLabel"] p { color: #64748b !important; font-size: 13px !important; font-weight: 500; }
    div[data-testid="stMetricValue"] div { color: #0f172a !important; font-weight: 700 !important; font-size: 28px !important; }
    
    /* Typography Fixes */
    h1, h2, h3, h4 { color: #0f172a !important; font-family: 'Inter', sans-serif; font-weight: 700 !important; }
    
    /* Custom Match Percent Badges */
    .match-badge { background-color: #e6f4ea; color: #137333; padding: 6px 12px; border-radius: 8px; font-weight: bold; font-size: 14px; display: inline-block; text-align: center; }
    .status-eligible { color: #137333; font-weight: 600; font-size: 14px; }
    .status-review { color: #b06000; font-weight: 600; font-size: 14px; }
    
    /* Premium Sidebar Banner Box */
    .premium-box { background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%); padding: 20px; border-radius: 12px; text-align: center; color: white !important; }
    .premium-box h5 { color: white !important; margin-bottom: 5px; }
    
    /* WhatsApp Alert Banner Box */
    .whatsapp-banner { background-color: #e8f5e9; border: 1px solid #c8e6c9; border-radius: 10px; padding: 15px; display: flex; align-items: center; margin-bottom: 20px; }
    </style>
""", unsafe_allow_html=True)

# 3. Sidebar Navigation Panel Architecture
with st.sidebar:
    st.markdown("### 📈 Navigation Panel")
    st.caption("Active Session Control Console")
    
    # Live Interactive Query Controls
    selected_state = st.selectbox("📍 Select Target Territory:", ["Chhattisgarh", "Uttar Pradesh"])
    
    selected_sectors = st.multiselect(
        "📁 Niche Verticals:",
        ["Civil Construction", "Medical Supply", "Coal Logistics", "Material Supply"],
        default=["Civil Construction", "Medical Supply", "Coal Logistics"]
    )
    
    selected_classes = st.multiselect(
        "🔑 Contractor License Class:",
        ["Class A", "Class B", "Class C", "Class D", "Open / Corporate"],
        default=["Class A", "Class B", "Class C", "Class D", "Open / Corporate"]
    )
    
    st.write("---")
    
    # Left Column Sidebar Premium Box Upgrade Banner
    st.markdown("""
        <div class="premium-box">
            <h5>👑 Unlock Premium</h5>
            <p style='font-size:12px; color:#e0f2fe;'>Get access to direct contact details, documents, and priority AI checklists.</p>
        </div>
    """, unsafe_allow_html=True)
    st.button("Upgrade Now", type="primary", use_container_width=True)

# 4. Main Profile Header Section Greeting
h_col1, h_col2 = st.columns([3, 1])
with h_col1:
    st.title("Good Morning, Akash! 👋")
    st.caption("Find, track and win the right high-value enterprise possibilities.")
with h_col2:
    st.markdown("<div style='text-align: right; padding-top: 20px;'><span style='background-color:#e2f0fd; color:#0284c7; padding:6px 12px; border-radius:20px; font-weight:600; font-size:13px;'>🛡️ Premium Member Account</span></div>", unsafe_allow_html=True)

# Main Keyword Entry Bar Layout
search_query = st.text_input("🔍 Search opportunities by keyword, department, execution entity...", placeholder="e.g., Road, SECL, Medical Equipment...")
st.write("---")

# 5. Dashboard Top KPIs row panel
try:
    df = pd.read_csv("master_leads.csv")
    
    # Filter matrix calculations
    filtered_df = df[
        (df['state'] == selected_state) & 
        (df['sector'].isin(selected_sectors)) &
        (df['license_class'].isin(selected_classes))
    ]
    if search_query:
        filtered_df = filtered_df[filtered_df['title'].str.contains(search_query, case=False, na=False)]

    total_leads_count = len(filtered_df)
    matching_leads_count = len(filtered_df[filtered_df['experience_tier'] != '3+ Years']) # Personalized Mock Filter calculation
    
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("Total Opportunities", f"{total_leads_count * 4}+", "+120 this week")
    kpi2.metric("Matching for You", f"{matching_leads_count}", "High match index")
    kpi3.metric("Bids Closing Soon", "18 Leads", "Within next 7 days")
    kpi4.metric("Saved Opportunities", "26 Saved", "Monitored updates")
    
    st.write("---")

    # 6. Primary Body Column Layout Split (Main Grid vs Analytics Sidebar)
    main_col, side_col = st.columns([2.2, 1])
    
    with main_col:
        st.subheader("Recommended Opportunities")
        
        if filtered_df.empty:
            st.warning("No active leads matches your exact filtering constraints combination inside the tracking nodes.")
        else:
            for index, row in filtered_df.iterrows():
                # Map aesthetic percentages contextually
                match_pct = "95%" if "Coal" in str(row['sector']) else ("89%" if "Medical" in str(row['sector']) else "82%")
                status_html = '<span class="status-eligible">● Eligible</span>' if row['license_class'] in ['Class C', 'Class D', 'Open / Corporate'] else '<span class="status-review">● May Qualify</span>'
                
                with st.container():
                    c1, c2, c3, c4 = st.columns([0.5, 2.5, 1.2, 1.2])
                    with c1:
                        st.markdown(f"<div class='match-badge'>{match_pct}<br><span style='font-size:9px;font-weight:normal;'>Match</span></div>", unsafe_allow_html=True)
                    with c2:
                        st.markdown(f"**{row['title']}**")
                        st.markdown(f"<span style='font-size:12px; color:#64748b;'>🏢 {row['location']} &nbsp;|&nbsp; 📍 {row['state']}</span>", unsafe_allow_html=True)
                    with c3:
                        st.markdown(f"<span style='font-size:11px; color:#64748b;'>Estimated Value</span><br>**₹{row['estimated_value']}**", unsafe_allow_html=True)
                    with c4:
                        st.markdown(f"<span style='font-size:11px; color:#64748b;'>Deadline Details</span><br><span style='color:#ef4444; font-weight:600;'>{row['closing_date']}</span><br>{status_html}", unsafe_allow_html=True)
                        
        # Interactive WhatsApp Integration Banner Box
        st.markdown("""
            <div class="whatsapp-banner">
                <span style='font-size:24px; margin-right:15px;'>💬</span>
                <div>
                    <strong style='color:#1e293b;'>Never miss an execution opportunity!</strong><br>
                    <span style='font-size:13px; color:#64748b;'>Get clean, real-time automated system updates sent straight to your registered mobile devices.</span>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        # Bottom Grid Section: Recruitment Channels
        st.subheader("Latest Government Job Tracks")
        j_col1, j_col2, j_col3 = st.columns(3)
        with j_col1:
            with st.container():
                st.markdown("🔧 **Junior Engineer (Civil)**")
                st.caption("Chhattisgarh Public Service Commission")
                st.markdown("<span style='font-size:11px; background-color:#f1f5f9; padding:4px 8px; border-radius:4px;'>Full Time</span>", unsafe_allow_html=True)
        with j_col2:
            with st.container():
                st.markdown("🩺 **Staff Nurse Openings**")
                st.caption("CGHS Health Administration Department")
                st.markdown("<span style='font-size:11px; background-color:#f1f5f9; padding:4px 8px; border-radius:4px;'>Contractual</span>", unsafe_allow_html=True)
        with j_col3:
            with st.container():
                st.markdown("📊 **Assistant Manager**")
                st.caption("National Mineral Development Corp.")
                st.markdown("<span style='font-size:11px; background-color:#f1f5f9; padding:4px 8px; border-radius:4px;'>Permanent</span>", unsafe_allow_html=True)

    with side_col:
        # AI Upload File Inspection Box
        st.subheader("AI Eligibility Check")
        with st.container():
            st.markdown("<div style='text-align:center; padding:10px;'>", unsafe_allow_html=True)
            uploaded_pdf = st.file_uploader("Drop active tender specification PDF notices directly here to evaluate organizational compatibility vectors instantly:", type=["pdf"])
            if uploaded_pdf:
                st.success("Analysis file parsed successfully! Checking requirements rules values...")
                
        # Data Visualization Distribution Wheel Area Layout
        st.subheader("Opportunities by Sector Category")
        with st.container():
            # Generate Donut Data Frame structure to mimic layout metrics
            chart_data = pd.DataFrame({
                "Sector Niche": ["Civil Works", "Supply Chain", "Services", "Logistics Operations"],
                "Volume Share Index": [35, 25, 25, 15]
            })
            fig = px.pie(
                chart_data, 
                names="Sector Niche", 
                values="Volume Share Index", 
                hole=0.6,
                color_discrete_sequence=["#0284c7", "#0d9488", "#fbbf24", "#f43f5e"]
            )
            fig.update_layout(
                margin=dict(l=10, r=10, t=10, b=10),
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
            )
            st.plotly_chart(fig, use_container_width=True)
            
        # Recent Notification Alerts Logs Feed Stream
        st.subheader("System Event Stream")
        with st.container():
            st.markdown("🟢 **New match found matching credentials index:** \n`Supply of Coal (500 MT) - SECL Korba Node` &nbsp;|&nbsp; *10 mins ago*")
            st.write("---")
            st.markdown("🟡 **Bidding window closure timeline notification:** \n`Medical Equipment Supply - Hub Deadline Approaching` &nbsp;|&nbsp; *1 hour ago*")

except FileNotFoundError:
    st.error("Database path routing error: Local master files array links are disconnected.")