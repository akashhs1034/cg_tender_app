"""
app.py — Opporta Enterprise Web Console.
Fully custom-styled dashboard implementation optimized for desktop web view.
"""

from __future__ import annotations

import io
import os
from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st

import core
import accounts
import evaluator

ROOT = Path(__file__).parent
DATA = ROOT / "data"
SECTORS = ["Civil Works", "Civil Infrastructure", "Electrical & Energy", "Coal & Mining",
           "Medical Procurement", "Water & Irrigation", "Municipal Projects",
           "Transport", "Manufacturing", "IT Services"]
DISTRICTS = ["Raipur", "Bilaspur", "Durg", "Bhilai", "Korba", "Bastar", "Raigarh",
             "Lucknow", "Kanpur", "Prayagraj", "Varanasi", "Gorakhpur", "Gonda"]

# Set page to wide layout for maximum screen real estate utilization
st.set_page_config(page_title="Opporta Console", page_icon="⚡", layout="wide")

# =====================================================================
# CUSTOM CORPORATE CSS SHELL INJECTION
# =====================================================================
st.markdown("""
    <style>
        /* General Canvas Tidy-up */
        .block-container {
            padding-top: 2rem !important;
            padding-bottom: 2rem !important;
        }
        
        /* Premium Core Value Cards */
        .kpi-container {
            display: flex;
            gap: 1rem;
            margin-bottom: 1.5rem;
        }
        .kpi-box {
            flex: 1;
            background-color: #FFFFFF;
            padding: 1.25rem;
            border-radius: 10px;
            border: 1px solid #E2E8F0;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
            text-align: left;
        }
        .kpi-value {
            font-size: 1.75rem;
            font-weight: 700;
            color: #1E293B;
            line-height: 1.2;
        }
        .kpi-label {
            font-size: 0.85rem;
            color: #64748B;
            font-weight: 500;
            margin-top: 0.25rem;
        }
        
        /* Dynamic Opportunity Feeds */
        .custom-card {
            background-color: #FFFFFF;
            padding: 1.5rem;
            border-radius: 12px;
            border: 1px solid #E2E8F0;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
            margin-bottom: 1rem;
        }
        
        /* Metric Badges Alignment */
        .score-badge {
            display: inline-block;
            padding: 0.35rem 0.65rem;
            border-radius: 6px;
            font-size: 0.85rem;
            font-weight: 700;
            text-align: center;
        }
        .fit-high { background-color: #DCFCE7; color: #15803D; }
        .fit-mid { background-color: #FEF3C7; color: #B45309; }
        .fit-low { background-color: #FEE2E2; color: #B91C1C; }
        
        .eligibility-tag {
            font-size: 0.8rem;
            font-weight: 600;
            padding: 0.2rem 0.5rem;
            border-radius: 4px;
            text-transform: uppercase;
        }
        .eligible-true { background-color: #E0F2FE; color: #0369A1; }
        .eligible-false { background-color: #FFEDD5; color: #C2410C; }
    </style>
""", unsafe_allow_html=True)

def _secret(name):
    if name in os.environ:
        return os.environ[name]
    try:
        return st.secrets[name]
    except Exception:
        return None

@st.cache_data(ttl=600)
def load_table(name):
    url, key = _secret("SUPABASE_URL"), _secret("SUPABASE_KEY")
    if url and key:
        try:
            from supabase import create_client
            sb = create_client(url, key)
            rows = sb.table(name).select("*").execute().data
            if rows:
                return pd.DataFrame(rows)
        except Exception:
            pass
    local = DATA / f"{name}.csv"
    return pd.read_csv(local) if local.exists() else pd.DataFrame()

def days_left(d):
    dd = core.parse_date(d)
    return (dd - date.today()).days if dd else None

def extract_text(uploaded_files) -> str:
    chunks = []
    for f in uploaded_files or []:
        name = f.name.lower()
        try:
            if name.endswith(".pdf"):
                import pdfplumber
                with pdfplumber.open(f) as pdf:
                    chunks += [(p.extract_text() or "") for p in pdf.pages]
            else:
                chunks.append(f.read().decode("utf-8", errors="ignore"))
        except Exception as e:
            chunks.append(f"[could not read {f.name}: {e}]")
    return "\n".join(chunks)


def extract_bytes_text(filename: str, content: bytes) -> str:
    """Extract plain text from raw bytes (used for vault documents)."""
    try:
        if filename.lower().endswith(".pdf"):
            import pdfplumber
            with pdfplumber.open(io.BytesIO(content)) as pdf:
                return "\n".join(p.extract_text() or "" for p in pdf.pages)
        return content.decode("utf-8", errors="ignore")
    except Exception as e:
        return f"[could not read {filename}: {e}]"

# =====================================================================
# SIDEBAR CONSOLE NAVIGATION & CONTROLS
# =====================================================================
st.sidebar.title("⚡ Opporta OS")
st.sidebar.caption("Hyper-local Procurement Console · CG + UP")
st.sidebar.markdown("---")

if "email" not in st.session_state:
    st.session_state.email = ""

email = st.sidebar.text_input("Administrative Session Sign-in", st.session_state.email,
                              placeholder="operator@firm.com")
if email:
    st.session_state.email = email.strip().lower()

if not st.session_state.email:
    st.title("⚡ Enterprise Tender Sourcing Console")
    st.markdown(
        "Welcome to your centralized intelligence hub. Opporta constantly scans corporate, "
        "municipal, and panchayat data nodes across **Chhattisgarh** and **Uttar Pradesh** to score "
        "and isolate critical infrastructure opportunities calibrated to your exact operational parameters.\n\n"
        "👈 **Provide an authorized session email in the workspace console sidebar to load the target engine matrix.**")
    st.info("System Notification: Current session gate is active in developer mode.")
    st.stop()

email = st.session_state.email
profile = accounts.get_profile(email)

# Onboarding Profile Configuration Sidebar Module
new_user = profile is None
if new_user:
    profile = dict(core.DEFAULT_PROFILE)

with st.sidebar.expander("💼 Contractor Sourcing Profile", expanded=new_user):
    company = st.text_input("Corporate Identity", profile.get("company_name", ""))
    turnover = st.number_input("Audited Annual Turnover (₹ Lakhs)", min_value=0.0,
                               value=float(profile.get("turnover_lakhs") or 0), step=10.0)
    classes = ["Class A", "Class B", "Class C", "Class D", "Open"]
    cls = st.selectbox("Contractor Compliance Classification", classes,
                       index=classes.index(profile.get("contractor_class", "Class C")))
    exp = st.number_input("Verified Sourcing Experience (Years)", min_value=0,
                          value=int(profile.get("experience_years") or 0))
    sectors = st.multiselect("Active Target Sectors", SECTORS, profile.get("sectors", []))
    states = st.multiselect("Territorial Jurisdictions", ["Chhattisgarh", "Uttar Pradesh"],
                            profile.get("states", ["Chhattisgarh", "Uttar Pradesh"]))
    target_districts = st.multiselect("Hyper-Local Target Nodes (Optional)", DISTRICTS,
                                      profile.get("districts", []))
    if st.button("💾 Commit Sourcing Profile Changes"):
        profile = {"company_name": company, "turnover_lakhs": turnover,
                   "contractor_class": cls, "experience_years": exp,
                   "sectors": sectors, "states": states, "districts": target_districts}
        accounts.save_profile(email, profile)
        st.success("Profile parameters synced with local system configuration.")
        st.rerun()

st.sidebar.markdown("---")
query = st.sidebar.text_input("🔎 Workspace Global Filter").strip().lower()
synced = "Supabase Cloud Database" if (_secret("SUPABASE_URL") and _secret("SUPABASE_KEY")) else "Local Offline Cache Engine"
st.sidebar.caption(f"System Linkageage: {synced}")

# Load tables for global performance index calculation
df_t = load_table("tenders")
df_j = load_table("jobs")

# =====================================================================
# HEADER WORKSPACE PERFORMANCE STATS MATRIX
# =====================================================================
cname = profile.get("company_name")
company_header = f" | {cname}" if cname else ""
st.subheader(f"Workspace Console Dashboard{company_header}")

tenders_indexed = len(df_t) if not df_t.empty else 0
jobs_indexed = len(df_j) if not df_j.empty else 0
active_class = profile.get('contractor_class', 'Open')
active_turnover = float(profile.get('turnover_lakhs') or 0)

# Render Custom Clean KPI Grid Block
st.markdown(f"""
    <div class="kpi-container">
        <div class="kpi-box">
            <div class="kpi-value">{tenders_indexed}</div>
            <div class="kpi-label">Active Tenders Monitored</div>
        </div>
        <div class="kpi-box">
            <div class="kpi-value">{jobs_indexed}</div>
            <div class="kpi-label">Live Strategic Positions</div>
        </div>
        <div class="kpi-box">
            <div class="kpi-value">{active_class}</div>
            <div class="kpi-label">Target Bidding Designation</div>
        </div>
        <div class="kpi-box">
            <div class="kpi-value">₹{active_turnover:.0f} Lakhs</div>
            <div class="kpi-label">Calibrated Capital Capacity</div>
        </div>
    </div>
""", unsafe_allow_html=True)

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🎯 Prioritized Sourcing Feed",
    "🏛️ Institutional Positions",
    "📋 Saved Bid Pipeline",
    "🧮 AI Qualification Evaluator",
    "📁 My Documents",
])

# =====================================================================
# TAB 1: RADAR TARGET FEED (TENDERS)
# =====================================================================
with tab1:
    if df_t.empty:
        st.info("Sourcing Matrix Empty. Run the data synchronization system pipeline (`python ingest.py`).")
    else:
        scored = []
        for _, r in df_t.iterrows():
            rec = r.to_dict()
            if not core.state_match(rec, profile):
                continue
            if query and query not in f"{rec.get('title','')} {rec.get('organization','')}".lower():
                continue
            s, reasons, eligible = core.score_tender_for_user(rec, profile)
            scored.append((s, eligible, reasons, rec))
        scored.sort(key=lambda x: (x[1], x[0]), reverse=True)

        hide_ineligible = st.checkbox("Apply Strict Exclusion Filter (Hide Disqualified Opportunities)", value=False)
        shown = 0
        
        for s, eligible, reasons, rec in scored:
            if hide_ineligible and not eligible:
                continue
            shown += 1
            
            # Setup score css classes
            score_class = "fit-high" if s >= 80 else ("fit-mid" if s >= 60 else "fit-low")
            eligibility_text = "Qualified" if eligible else "Review Disqualification"
            eligibility_class = "eligible-true" if eligible else "eligible-false"
            dl = days_left(rec.get("deadline"))
            dl_txt = f" · ⏳ {dl} days remaining" if dl is not None else ""

            # Beautiful, uniform collapsible expander block simulating modern list cards
            with st.expander(f"💼 Match Assessment: {s}% · {rec.get('title','Untitled Opportunity')} ({rec.get('organization','Global Feed Node')}{dl_txt})"):
                # Structural columns inside the expander
                st.markdown(f"""
                <div style="margin-bottom: 1rem;">
                    <span class="score-badge {score_class}">Match Score: {s}%</span>
                    <span class="eligibility-tag {eligibility_class}">{eligibility_text}</span>
                </div>
                """, unsafe_allow_html=True)
                
                c1, c2, c3 = st.columns(3)
                val = rec.get("value_text") or (f"₹ {rec.get('value_lakhs')} Lakhs" if pd.notna(rec.get('value_lakhs')) else "Not Stated")
                c1.metric("Estimated Engagement Value", val)
                c2.metric("Closing Deadline", rec.get('deadline','—'))
                c3.metric("Required Compliance Class", rec.get('contractor_class') or 'Open Market')
                
                if rec.get("description"):
                    st.markdown("**Procurement Scope Summary:**")
                    st.caption(rec["description"])
                
                st.markdown("**Engine Evaluation Signals:**")
                for reason in reasons:
                    st.markdown(f"  • {reason}")
                
                st.markdown("---")
                b1, b2 = st.columns([1, 1])
                if b1.button("➕ Stage to Bid Pipeline", key=f"save_{rec.get('source_id')}"):
                    accounts.save_tender(email, rec.get("source_id"))
                    st.toast("Record pinned to project tracking pipeline dashboard.")
                url = rec.get("document_url")
                if isinstance(url, str) and url.startswith("http"):
                    b2.link_button("🔗 Launch Official Procurement Source", url)
                    
        if shown == 0:
            st.warning("No procurement matches found. Broaden your active sector selection framework or district limits.")

# =====================================================================
# TAB 2: LIVE INSTITUTIONAL JOBS INDEX
# =====================================================================
with tab2:
    st.caption("Browse direct government human capital opportunities indexed from target administrative sectors.")
    if df_j.empty:
        st.info("System Data Layer Empty. Run the data ingestion engine pipeline.")
    else:
        fj = df_j[df_j["state"].isin(profile.get("states", []))] if "state" in df_j else df_j
        cats = ["All"] + sorted(fj.get("category", pd.Series(dtype=str)).dropna().unique())
        c1, c2 = st.columns(2)
        sel_cat = c1.selectbox("Filter by Category Verticals", cats)
        dlist = ["All"] + sorted(fj.get("district", pd.Series(dtype=str)).dropna().unique())
        sel_d = c2.selectbox("Filter by Local Administrative Node", dlist)
        
        if sel_cat != "All":
            fj = fj[fj["category"] == sel_cat]
        if sel_d != "All" and "district" in fj:
            fj = fj[fj["district"] == sel_d]
            
        if fj.empty:
            st.warning("No active career listings match the selected tracking parameters.")
            
        for _, r in fj.iterrows():
            vac = f" · 👥 {int(r['vacancies'])} Open Openings" if pd.notna(r.get("vacancies")) else ""
            with st.expander(f"💼 {r.get('title','Position Profile')} · {r.get('category','General Pool')}{vac}"):
                a, b = st.columns(2)
                a.markdown(f"**Deploying Institution/Department:**\n\n`{r.get('department','—')}`")
                a.markdown(f"**Closing Application Window:**\n\n`{r.get('deadline','—')}`")
                b.markdown(f"**Target Allocation Base:**\n\n`{r.get('district') or 'State-wide Vector'}, {r.get('state','')}`")
                if r.get("qualification"):
                    st.info(f"🎓 Mandatory Criteria: {r['qualification']}")

    # -----------------------------------------------------------------
    # RESUME ANALYZER
    # -----------------------------------------------------------------
    if not df_j.empty:
        st.markdown("---")
        st.markdown("### 📄 Match My Resume")
        st.caption(
            "Upload your resume and pick a job — we'll check how well your "
            "qualifications match the stated requirements."
        )

        ru_col, rd_col = st.columns([1, 1])
        with ru_col:
            resume_file = st.file_uploader(
                "Resume (PDF or TXT)",
                type=["pdf", "txt"],
                key="resume_upload_jobs",
            )
        with rd_col:
            all_jobs_list = [r.to_dict() for _, r in df_j.iterrows()]
            job_display = [
                f"{r.get('title','Untitled')[:55]} · {(r.get('department') or '')[:35]}"
                for r in all_jobs_list
            ]
            resume_job_idx = st.selectbox(
                "Job to check against",
                range(len(all_jobs_list)),
                format_func=lambda i: job_display[i],
                key="resume_job_sel",
            ) if all_jobs_list else None

        check_resume = st.button("🔍 Check Match", type="primary", key="resume_check")

        if check_resume:
            if resume_file is None:
                st.error("Please upload your resume first.")
            elif resume_job_idx is None:
                st.error("No jobs available to match against.")
            else:
                with st.spinner("Analysing resume…"):
                    _rt = extract_text([resume_file])
                    _rjob = all_jobs_list[resume_job_idx]
                    _rr = evaluator.evaluate_resume_for_job(_rjob, _rt)
                st.session_state["_resume_result"] = _rr
                st.session_state["_resume_job"]    = _rjob

        rr   = st.session_state.get("_resume_result")
        rjob = st.session_state.get("_resume_job")
        if rr and rjob:
            pct = rr["match_pct"]
            n_met   = len(rr["met"])
            n_total = n_met + len(rr["missing"]) + len(rr["unknown"])

            if pct >= 75:
                bg, fg = "#DCFCE7", "#15803D"
            elif pct >= 50:
                bg, fg = "#FEF3C7", "#B45309"
            else:
                bg, fg = "#FEE2E2", "#B91C1C"

            st.markdown(f"""
            <div style="text-align:center;padding:1.5rem;background:{bg};
                        border-radius:12px;margin:1rem 0">
                <div style="font-size:3.5rem;font-weight:900;color:{fg};
                            line-height:1">{pct}%</div>
                <div style="font-size:1rem;color:{fg};margin-top:0.5rem">
                    Resume Match Score</div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown(
                f"**Your resume matches {n_met} of {n_total} requirements** "
                f"for *{rjob.get('title','')}*."
            )
            st.write(rr["verdict"])

            if rr["met"]:
                st.markdown("**Requirements satisfied:**")
                for item in rr["met"]:
                    st.success(f"✅  {item}")

            if rr["missing"]:
                st.markdown("**Not found in resume:**")
                for item in rr["missing"]:
                    st.error(f"❌  {item}")

            if rr["unknown"]:
                st.markdown("**Could not verify:**")
                for item in rr["unknown"]:
                    st.warning(f"❔  {item}")

            st.caption(
                "⚠️  This checks stated qualifications only, not a selection guarantee. "
                "Always verify eligibility against the official notification."
            )

            apply_url = rjob.get("document_url")
            if isinstance(apply_url, str) and apply_url.startswith("http"):
                st.link_button("📋 Apply Now / View Official Notification", apply_url)

# =====================================================================
# TAB 3: STRATEGIC PROJECT MANAGEMENT PIPELINE
# =====================================================================
with tab3:
    saved = accounts.list_saved(email)
    if not saved:
        st.info("Your active bid staging vault is empty. Pin items to this pipeline from the main sourcing feed.")
    else:
        lookup = {r["source_id"]: r for _, r in df_t.iterrows()} if not df_t.empty else {}
        st.success(f"Pipeline Management System: Tracking **{len(saved)}** operational targets.")
        for s in saved:
            rec = lookup.get(s["source_id"], {})
            title = rec.get("title", s["source_id"])
            with st.expander(f"📌 Staged Bid Target: {title} · Status Tracking Flag: [{s.get('status','Interested Mode')}]"):
                if rec.get("deadline"):
                    st.markdown(f"**Submissions Envelope Window Deadline:** `{rec['deadline']}`")
                url = rec.get("document_url")
                if isinstance(url, str) and url.startswith("http"):
                    st.link_button("🔗 Direct Procurement Source Gateway", url)

# =====================================================================
# TAB 4: ADVANCED CRITERIA MATRIX CHECKER (AI EVALUATOR)
# =====================================================================
with tab4:
    st.caption("Cross-examine current credential packages against complex mandatory tender requirements.")
    kind = st.radio("Select Target Examination Scope Profile:", ["Tender", "Job"], horizontal=True)
    source = df_t if kind == "Tender" else df_j

    if source.empty:
        st.info("No active profiles loaded to initialize checking matrix.")
    else:
        in_state = source[source["state"].isin(profile.get("states", []))] if "state" in source else source
        in_state = in_state.reset_index(drop=True)
        labels = [f"{r.get('title','Untitled Opportunity')} · {r.get('organization', r.get('department',''))}"
                  for _, r in in_state.iterrows()]
        pick = st.selectbox(f"Select Target Evaluation Node:", range(len(labels)),
                            format_func=lambda i: labels[i]) if labels else None

        # --- Vault document pre-inclusion ---
        vault_docs = accounts.list_documents(email)
        if vault_docs:
            st.markdown("**📁 Include from Document Vault:**")
            vault_sel = st.multiselect(
                "vault_pick",
                options=[d["doc_id"] for d in vault_docs],
                default=[d["doc_id"] for d in vault_docs],
                format_func=lambda did: next(
                    (f"{d['name']}  ·  {d['filename']}" for d in vault_docs if d["doc_id"] == did), did
                ),
                label_visibility="collapsed",
            )
        else:
            vault_sel = []
            st.caption("💡 Upload certificates in **📁 My Documents** to auto-include them here.")

        uploads = st.file_uploader(
            "Additional credentials (PDF / TXT) — supplements your vault:",
            type=["pdf", "txt"], accept_multiple_files=True)

        if pick is not None and st.button("🧮 Execute High-Fidelity Readiness Evaluation"):
            rec = in_state.iloc[pick].to_dict()
            vault_text = "\n".join(
                extract_bytes_text(
                    next(d["filename"] for d in vault_docs if d["doc_id"] == did),
                    accounts.get_document_bytes(email, did) or b"",
                )
                for did in vault_sel
            )
            doc_text = vault_text + "\n" + extract_text(uploads)
            if kind == "Tender":
                result = evaluator.evaluate_tender(rec, profile, doc_text)
            else:
                result = evaluator.evaluate_job(rec, profile, doc_text)

            pct = result["readiness_pct"]
            color = "🟢" if pct >= 80 else ("🟡" if pct >= 50 else "🔴")
            st.metric("Corporate Mandatory Readiness Index", f"{pct}%")
            st.progress(pct / 100)
            st.markdown(f"### {color} Analysis Output")
            st.write(result['verdict'])

            if result["met"]:
                st.markdown("**✅ Verified / Satisfied Conditions:**")
                for x in result["met"]:
                    st.success(x)
            if result["missing"]:
                st.markdown("**❌ Missing / Unfulfilled Sourcing Gaps:**")
                for x in result["missing"]:
                    st.error(x)
            if result["unknown"]:
                st.markdown("**❔ Unverified Assertions (Upload supplemental balance sheets or logs to clarify):**")
                for x in result["unknown"]:
                    st.warning(x)

# =====================================================================
# TAB 5: DOCUMENT VAULT
# =====================================================================
_VAULT_LABELS = [
    "GST Registration",
    "Contractor Registration / License",
    "PAN Card",
    "ISO Certification",
    "Turnover / Financial Statement",
    "Experience / Completion Certificate",
    "EMD / Bank Guarantee",
    "Safety / DGMS Pass",
    "Drug / Equipment License",
    "Other",
]

with tab5:
    st.caption(
        "Upload your certificates once — they are auto-included in every eligibility evaluation. "
        "Labels map directly to the criteria the evaluator checks."
    )

    vault_all = accounts.list_documents(email)
    total_kb = sum(d.get("size_bytes", 0) for d in vault_all) / 1024

    m1, m2 = st.columns(2)
    m1.metric("Documents Stored", len(vault_all))
    m2.metric("Total Size", f"{total_kb:.1f} KB")

    st.markdown("---")
    st.markdown("**Upload New Document**")

    with st.form("vault_upload_form", clear_on_submit=True):
        fc1, fc2 = st.columns([1, 2])
        label_pick = fc1.selectbox("Document Type", _VAULT_LABELS)
        custom_label = fc1.text_input("Custom label (overrides above)", placeholder="e.g. MSME Certificate")
        vault_file = fc2.file_uploader(
            "Certificate / Document file",
            type=["pdf", "txt"],
            help="PDF or plain-text format accepted.",
        )
        if st.form_submit_button("💾 Add to Vault"):
            if vault_file is None:
                st.error("Please select a file before saving.")
            else:
                final_label = custom_label.strip() if custom_label.strip() else label_pick
                accounts.save_document(
                    email,
                    name=final_label,
                    filename=vault_file.name,
                    content=vault_file.read(),
                    mime_type=vault_file.type or "application/octet-stream",
                )
                st.success(f"'{final_label}' saved to your vault.")
                st.rerun()

    st.markdown("---")
    if not vault_all:
        st.info("Your vault is empty. Upload certificates above and they will be auto-included in evaluations.")
    else:
        st.markdown(f"**{len(vault_all)} document(s) in vault**")
        for doc in vault_all:
            size_kb = doc.get("size_bytes", 0) / 1024
            date_str = (doc.get("uploaded_at") or "")[:10]
            with st.expander(f"📄 {doc['name']}  ·  {doc['filename']}  ·  {size_kb:.1f} KB  ·  {date_str}"):
                if st.button("🗑️ Remove from Vault", key=f"del_{doc['doc_id']}"):
                    accounts.delete_document(email, doc["doc_id"])
                    st.toast(f"'{doc['name']}' removed.")
                    st.rerun()