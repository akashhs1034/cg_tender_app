import streamlit as st
import pandas as pd

# Page Configuration
st.set_page_config(
    page_title="Enterprise B2B Lead Hub", 
    page_icon="🏛️", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Premium Styling (Dark Slate Background with neon cyber-blue highlights)
st.markdown("""
    <style>
    .stApp { background-color: #0f172a; color: #f8fafc; }
    .stMetric { background-color: #1e293b; padding: 18px; border-radius: 12px; border: 1px solid #334155; }
    div[data-testid="stContainer"] { background-color: #1e293b; border: 1px solid #475569 !important; border-radius: 14px; padding: 24px; margin-bottom: 18px; box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1); }
    h1, h2, h3 { color: #38bdf8 !important; font-family: 'Inter', sans-serif; }
    .badge { background-color: #0284c7; color: white; padding: 4px 10px; border-radius: 6px; font-size: 12px; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# Main Navigation Hub Header
st.title("🏛️ Enterprise B2B Intelligence Hub")
st.caption("Real-Time Hyper-Local Tenders, Sourcing Logistics, Municipal Leases & Employment Streams")
st.write("---")

# State Switch Segments
selected_state = st.segmented_control(
    "Active Administrative Territory:", 
    ["Chhattisgarh", "Uttar Pradesh"], 
    default="Chhattisgarh"
)

# Sidebar Deep-Filtering Control Panels
st.sidebar.header("🎯 Deep Filtering Matrix")
st.sidebar.write("Configure parameters to target winnable leads instantly.")

selected_tiers = st.sidebar.multiselect(
    "Administrative Tiers:",
    ["State e-Tenders", "Nagar Palika (Municipal)", "Gramin Yojna (Rural)", "Employment Portal"],
    default=["State e-Tenders", "Nagar Palika (Municipal)", "Gramin Yojna (Rural)", "Employment Portal"]
)

selected_sectors = st.sidebar.multiselect(
    "Industry Verticals & Niches:",
    ["Civil Construction", "Medical Supply", "Coal Logistics", "Material Supply", "Government Job", "Private Job"],
    default=["Civil Construction", "Medical Supply", "Coal Logistics", "Material Supply", "Government Job", "Private Job"]
)

st.sidebar.write("---")
st.sidebar.subheader("🔑 Your Credentials Check")

selected_classes = st.sidebar.multiselect(
    "Your Contractor License Class:",
    ["Class A", "Class B", "Class C", "Class D", "Open / Corporate", "Not Applicable"],
    default=["Class A", "Class B", "Class C", "Class D", "Open / Corporate", "Not Applicable"]
)

selected_experience = st.sidebar.multiselect(
    "Your Verified Experience Level:",
    ["No Experience", "1-3 Years", "3+ Years"],
    default=["No Experience", "1-3 Years", "3+ Years"]
)

search_query = st.sidebar.text_input("🔍 Direct Keyword Search:", placeholder="e.g., Road, SECL, Hospital...")

# Core Query Filtering Logic Layer
try:
    df = pd.read_csv("master_leads.csv")
    
    # Process inputs against data columns
    filtered_df = df[
        (df['state'] == selected_state) & 
        (df['tier'].isin(selected_tiers)) & 
        (df['sector'].isin(selected_sectors)) &
        (df['license_class'].isin(selected_classes)) &
        (df['experience_tier'].isin(selected_experience))
    ]
    
    # Apply keyword filtering if active
    if search_query:
        filtered_df = filtered_df[filtered_df['title'].str.contains(search_query, case=False, na=False) | 
                                  filtered_df['location'].str.contains(search_query, case=False, na=False)]

    # Calculate Summary KPI Metrics Safely
    total_leads = len(filtered_df)
    
    def clean_val(val):
        try:
            return float(str(val).replace(',', '').strip())
        except ValueError:
            return 0.0
            
    total_val = filtered_df['estimated_value'].apply(clean_val).sum()
    
    # Render Top Analytics Row
    m_col1, m_col2, m_col3 = st.columns(3)
    with m_col1:
        st.metric(label=f"Active Filtered Matches ({selected_state})", value=f"{total_leads} Leads Ready")
    with m_col2:
        st.metric(label="Tracked Capital Pool", value=f"₹{total_val/100000:.2f} Lakhs" if total_val > 0 else "Varies by Project")
    with m_col3:
        st.metric(label="Cloud Automation Engine", value="Sync Active", delta="🔄 2 Hour Intervals")
        
    st.write("---")

    # Render Lead Opportunities Flow
    if filtered_df.empty:
        st.warning("⚠️ No records match your active filtering configuration. Broaden your sidebar criteria to reveal hidden entries.")
    else:
        for index, row in filtered_df.iterrows():
            with st.container():
                col_left, col_right = st.columns([3, 1])
                
                with col_left:
                    st.subheader(f"🏢 {row['title']}")
                    st.markdown(f"📍 **Issuing Authority:** `{row['location']}` | 📁 **Sector Sector:** `{row['sector']}`")
                    
                    # Custom Badges indicators for scannability
                    st.markdown(f"<span class='badge'>{row['tier']}</span> &nbsp; <span class='badge' style='background-color:#10b981;'>License: {row['license_class']}</span> &nbsp; <span class='badge' style='background-color:#f59e0b;'>Experience: {row['experience_tier']}</span>", unsafe_allow_html=True)
                    
                    # Core Competitive Advantage Feature: Deep AI Eligibility Box
                    st.markdown("<div style='margin-top:15px;'></div>", unsafe_allow_html=True)
                    st.markdown("##### 📋 Extracted AI Eligibility Snapshot")
                    st.info(f"💡 **Detailed Criteria:** {row['qualification_class']}")
                
                with col_right:
                    st.write("### 💎 Financial Overview")
                    st.metric("Estimated Cost", f"₹{row['estimated_value']}")
                    st.metric("EMD Deposit Lock", f"₹{row['emd']}")
                    st.error(f"⏳ Deadline: {row['closing_date']}")
                    
                    # Direct Deep-Link Call to Action Button
                    st.link_button("🚀 Apply / View Notice", row['direct_url'], use_container_width=True)

except FileNotFoundError:
    st.error("⚠️ Database Initializing: `master_leads.csv` missing from repository storage nodes.")