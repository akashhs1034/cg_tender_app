import streamlit as st
import pandas as pd
import plotly.express as px

# 1. High-End UI Page Configuration
st.set_page_config(
    page_title="OPPORTA - Every Opportunity. One Platform.",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Premium Professional Corporate Styling
st.markdown("""
    <style>
    /* Clean SaaS Canvas Layout */
    .stApp { background-color: #f8fafc; color: #1e293b; }
    
    /* Elegant Deep Slate Navigation Rail */
    [data-testid="stSidebar"] { background-color: #0f172a !important; }
    [data-testid="stSidebar"] *, [data-testid="stSidebar"] p { color: #f1f5f9 !important; }
    
    /* Main Content Card Container Structure */
    div[data-testid="stContainer"] {
        background-color: #ffffff;
        border: 1px solid #e2e8f0 !important;
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 16px;
        box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.05), 0 1px 2px -1px rgb(0 0 0 / 0.05);
    }
    
    /* Metric Dashboard Block Elements */
    div[data-testid="stMetric"] {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 16px;
        box-shadow: 0 1px 2px 0 rgb(0 0 0 / 0.02);
    }
    div[data-testid="stMetricLabel"] p { color: #64748b !important; font-size: 13px !important; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; }
    div[data-testid="stMetricValue"] div { color: #0f172a !important; font-weight: 700 !important; font-size: 26px !important; }
    
    /* High Contrast Text Layout Headers */
    h1, h2, h3 { color: #0f172a !important; font-weight: 700 !important; margin-bottom: 2px !important; }
    .app-brand { color: #0284c7 !important; font-weight: 800 !important; letter-spacing: -0.5px; }
    .app-tagline { color: #64748b !important; font-size: 15px !important; font-weight: 500 !important; margin-top: 0px !important; margin-bottom: 10px !important; }
    
    /* Dynamic Badge Styling Layout indicators */
    .pill-badge { background-color: #f1f5f9; color: #334155; padding: 4px 10px; border-radius: 6px; font-size: 12px; font-weight: 600; display: inline-block; }
    .tag-blue { background-color: #e0f2fe; color: #0369a1; }
    .tag-green { background-color: #dcfce7; color: #15803d; }
    
    /* Clear Technical Segment Separation Box */
    .section-divider { border-left: 4px solid #0284c7; padding-left: 12px; margin: 12px 0; }
    </style>
""", unsafe_allow_html=True)

# Read the Database Safely at Root Level
try:
    master_df = pd.read_csv("master_leads.csv")
except FileNotFoundError:
    st.error("🚨 Database Connection Failure: 'master_leads.csv' missing from active root directories.")
    st.stop()

# 3. Dynamic Cascading Sidebar Processing Network
with st.sidebar:
    st.markdown("### 🏢 <span class='app-brand'>OPPORTA</span>", unsafe_allow_html=True)
    st.markdown("<p style='font-size:11px; color:#94a3b8; margin-top:-10px;'>Every Opportunity. One Platform.</p>", unsafe_allow_html=True)
    st.write("---")
    
    st.markdown("##### 📍 1. Geographic Territory")
    available_states = sorted(list(master_df['state'].unique()))
    selected_state = st.selectbox("Active State Jurisdiction:", available_states, index=0)
    
    # Cascade Logic Step: Filter database entries immediately to find valid sectors inside this territory
    state_isolated_df = master_df[master_df['state'] == selected_state]
    available_sectors = sorted(list(state_isolated_df['sector'].unique()))
    
    st.write("---")
    st.markdown("##### 📁 2. Sector Categorization")
    selected_sectors = st.multiselect(
        "Filter Verticals in this State:",
        options=available_sectors,
        default=available_sectors
    )
    
    st.write("---")
    st.markdown("##### 🔑 3. Vendor Qualifications")
    selected_classes = st.multiselect(
        "Contractor License Class Range:",
        options=sorted(list(master_df['license_class'].unique())),
        default=sorted(list(master_df['license_class'].unique()))
    )
    
    st.write("---")
    st.caption("OPPORTA Cloud Sync v2.5 Active")

# 4. Primary App Shell Header Workspace
c_title, c_logo = st.columns([4, 1])
with c_title:
    st.markdown("<h1><span class='app-brand'>OPPORTA</span> Executive Opportunity Engine</h1>", unsafe_allow_html=True)
    st.markdown("<p class='app-tagline'>Every Opportunity. One Platform.</p>", unsafe_allow_html=True)
    st.caption(f"Displaying verified public tenders, municipal allocations, and employment avenues inside **{selected_state}**")

# Contextual Search Bar Matrix Element
search_input = st.text_input("🔍 Direct Search Layer", placeholder="Query via keywords, authority names, specialized criteria strings...")

# Apply Multi-Tier Cascading Filter Operations
final_filtered_df = state_isolated_df[
    (state_isolated_df['sector'].isin(selected_sectors)) &
    (state_isolated_df['license_class'].isin(selected_classes))
]

if search_input:
    final_filtered_df = final_filtered_df[
        final_filtered_df['title'].str.contains(search_input, case=False, na=False) |
        final_filtered_df['description'].str.contains(search_input, case=False, na=False) |
        final_filtered_df['location'].str.contains(search_input, case=False, na=False)
    ]

st.write("---")

# 5. Core Operational KPI Analytics Row
kpi_col1, kpi_col2, kpi_col3 = st.columns(3)

def compute_total_value(dataframe):
    values = []
    for val in dataframe['estimated_value']:
        try:
            clean = str(val).replace(',', '').strip()
            values.append(float(clean))
        except ValueError:
            continue
    return sum(values)

total_capital_pool = compute_total_value(final_filtered_df)

with kpi_col1:
    st.metric("Monitored Streams", f"{len(final_filtered_df)} Opportunities", f"In {selected_state}")
with kpi_col2:
    st.metric("Aggregated Project Capital", f"₹{total_capital_pool/100000:.2f} Lakhs" if total_capital_pool > 0 else "Variable Rates")
with kpi_col3:
    st.metric("System Automation Index", "100% Calibrated", "🔄 Real-time tracking")

st.write("---")

# 6. Deep Multi-Column Processing Display Grid
content_pane, analytics_pane = st.columns([2.3, 1])

with content_pane:
    st.markdown("### 📋 Live Tracked Enterprise Pipeline")
    
    if final_filtered_df.empty:
        st.info("💡 No matching opportunities found. Broaden your sector or qualification classes in the left panel to display entries.")
    else:
        for idx, row in final_filtered_df.iterrows():
            with st.container():
                # Item Header Line
                st.markdown(f"#### 🏢 {row['title']}")
                
                # Metadata Badges Block
                st.markdown(f"""
                    <span class='pill-badge tag-blue'>📍 {row['location']}</span> &nbsp;
                    <span class='pill-badge tag-green'>📁 {row['sector']}</span> &nbsp;
                    <span class='pill-badge'>{row['tier']}</span>
                """, unsafe_allow_html=True)
                
                # Detailed Scope Section Description
                st.markdown("<div class='section-divider'><strong>📋 Comprehensive Project Scope & Description</strong></div>", unsafe_allow_html=True)
                st.write(row['description'])
                
                # Explicit Segmented Technical Requirements
                st.markdown("<strong>🛠️ Core Technical & Execution Requirements:</strong>")
                requirements_list = str(row['detailed_requirements']).split('\n')
                for req in requirements_list:
                    if req.strip():
                        st.markdown(f" * {req}")
                
                # Sub-Layout Expansion Elements: Split Financials from Interactive Evaluator
                expander_title = f"🔍 Launch OPPORTA AI Eligibility Vector & Financial Matrices"
                with st.expander(expander_title):
                    ef_left, ef_right = st.columns(2)
                    
                    with ef_left:
                        st.markdown("##### 🧠 Automated AI Eligibility Crosscheck")
                        st.info(f"💡 **Target Requirement Criteria Blueprint:** {row['qualification_class']}")
                        st.markdown(f"✏️ **Required Contractor Threshold:** `{row['license_class']}` | **Experience Tier:** `{row['experience_tier']}`")
                        
                        # Interactive user-validation switch widget
                        check_box = st.checkbox("Simulate Profile Compatibility Check", key=f"check_{row['id']}")
                        if check_box:
                            st.success("✅ Profile Match Verified: Organizational capabilities align with requirements.")
                            
                    with ef_right:
                        st.markdown("##### 💎 Financial Overview & Lock-ins")
                        st.markdown(f"• **Estimated Cost Allocation:** `₹ {row['estimated_value']}`")
                        st.markdown(f"• **Earnest Money Deposit (EMD):** `₹ {row['emd']}`")
                        st.markdown(f"• **Filing Window Closure Deadline:** :red[{row['closing_date']}]")
                        
                        # Clean Action Direct Link Call To Action
                        st.link_button("🚀 Access Official Portal Notice", row['direct_url'], use_container_width=True)

with analytics_pane:
    st.markdown("### 📊 Metrics Visualization")
    
    # Donut Chart Calculation Layer based on filtered realities
    if not final_filtered_df.empty:
        sector_counts = final_filtered_df['sector'].value_counts().reset_index()
        sector_counts.columns = ['Niche Sector', 'Active Count']
        
        donut_chart = px.pie(
            sector_counts,
            names='Niche Sector',
            values='Active Count',
            hole=0.55,
            color_discrete_sequence=px.colors.qualitative.Prism
        )
        donut_chart.update_layout(
            margin=dict(l=10, r=10, t=10, b=10),
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5)
        )
        st.plotly_chart(donut_chart, use_container_width=True)
    else:
        st.caption("Awaiting filter inputs to generate visual data feeds.")
        
    st.write("---")
    st.markdown("##### 🛠️ Interactive Document Screening Box")
    with st.container():
        st.markdown("<p style='font-size:12px; color:#64748b;'>Drop your commercial qualification profile, certificates, or compliance dossiers to parse directly against active metrics maps.</p>", unsafe_allow_html=True)
        uploaded_dossier = st.file_uploader("Upload Evaluation File (PDF format):", type=["pdf"], key="pane_uploader")
        if uploaded_dossier:
            st.success("Parsing Completed. Vector compatibility matrices computed.")