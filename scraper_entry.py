import os
import re
from datetime import datetime, timezone
from supabase import create_client

# =====================================================================
# 1. ESTABLISH CLOUD WORKSPACE PIPELINE ACCESS
# =====================================================================
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("ℹ️ System Context: Local environment variables not detected.")
    print("🧠 Attempting to pull safe fallback keys from Streamlit configuration...")
    try:
        import streamlit as st
        SUPABASE_URL = st.secrets["SUPABASE_URL"]
        SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
        print("🟢 Fallback success: Connected via Streamlit secrets.")
    except Exception:
        print("❌ Critical Failure: Ingestion Pipeline credentials missing entirely.")
        exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# =====================================================================
# 2. ADVANCED PARSING HEURISTICS
# =====================================================================
def clean_and_parse_financials(text_node):
    if not text_node or text_node.lower() in ["not specified", "nan", "nil"]:
        return "Not specified"
    clean_str = str(text_node).replace(",", "").replace("₹", "").strip().lower()
    try:
        if "cr" in clean_str or "crore" in clean_str:
            num = float("".join(c for c in clean_str if c.isdigit() or c == "."))
            return f"₹{num:.2f} Cr"
        if "lakh" in clean_str or "lac" in clean_str:
            num = float("".join(c for c in clean_str if c.isdigit() or c == "."))
            return f"₹{num:.2f} Lakh"
        extracted_num = float("".join(c for c in clean_str if c.isdigit() or c == "."))
        if extracted_num >= 10_000_000:
            return f"₹{extracted_num/10_000_000:.2f} Cr"
        if extracted_num >= 100_000:
            return f"₹{extracted_num/100_000:.2f} Lakh"
        return f"₹{extracted_num:,.0f}"
    except Exception:
        return "Not specified"

def extract_standard_deadline(date_str):
    date_clean = str(date_str).strip()
    date_match = re.search(r"(\d{2})[-/](\d{2})[-/](\d{4})", date_clean)
    if date_match:
        return date_match.group(0)
    if any(k in date_clean.lower() for k in ["open", "extended", "live"]):
        return "Open"
    return "Not specified"

def is_genuine_record(title_str):
    t_clean = str(title_str).lower().strip()
    noise_signatures = [
        "policy", "guideline", "rules", "act 20", "regulation", "grievance", "manual", 
        "approved posts", "minutes", "meeting", "ppt", "circular", "transfer order", 
        "seniority list", "niti", "eligibility list", "citizen charter", "press release"
    ]
    if any(sig in t_clean for sig in noise_signatures):
        return False
    if len(t_clean) <= 5 or t_clean.isdigit():
        return False
    return True

def infer_sector(title, sector):
    text = f"{title} {sector}".lower()
    mapping = [
        ("Coal & Mining", ["coal", "mining", "mine", "secl", "nmdc"]),
        ("Medical Procurement", ["medical", "hospital", "drug", "medicine", "surgical", "health"]),
        ("Civil Infrastructure", ["road", "bridge", "civil", "construction", "building", "pwd", "nhai"]),
        ("Transport & Logistics", ["transport", "logistics", "vehicle", "fleet", "cargo", "bus hire"]),
        ("Electrical & Energy", ["power", "electric", "energy", "solar", "transformer"]),
        ("Water & Irrigation", ["water", "irrigation", "pipeline", "phed", "jal"])
    ]
    for label, keywords in mapping:
        if any(k in text for k in keywords): return label
    return "General Opportunities"

# =====================================================================
# 3. CORE RUNTIME PIPELINE EXECUTION
# =====================================================================
def run_ingestion_cycle():
    print(f"⚡ Starting Dual-Stream Ingest: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # -----------------------------------------------------------------
    # STREAM A: PROCUREMENT TENDERS PIPELINE
    # -----------------------------------------------------------------
    tenders_table = "tenders"
    existing_tenders = set()
    try:
        db_check = supabase.table(tenders_table).select("title").execute()
        if db_check.data:
            for row in db_check.data:
                existing_tenders.add(row["title"])
            print(f"📡 Cached {len(existing_tenders)} active tender keys.")
    except Exception as e:
        pass

    raw_tenders_feed = [
        {"title": "SECL Coal Evacuation and Transport Work Phase 4", "agency": "South Eastern Coalfields Limited", "location": "Korba", "state": "Chhattisgarh", "project_value": "₹4.50 Crore", "emd": "₹4,50,000", "deadline": "28-07-2026", "url": "https://janjgir-champa.gov.in"},
        {"title": "Procurement of Critical ICU Emergency Medical Supplies", "agency": "Directorate of Health Services", "location": "Raipur", "state": "Chhattisgarh", "project_value": "45 Lakhs", "emd": "Not specified", "deadline": "15/08/2026", "url": "https://gariaband.gov.in"},
        {"title": "Internal Departmental Promotion Policies and PPT Guidelines", "agency": "Zilla Panchayat", "location": "Durg", "state": "Chhattisgarh", "project_value": "Not specified", "emd": "Not specified", "deadline": "Open", "url": "https://durg.gov.in"}
    ]
    
    cleaned_tenders = []
    for item in raw_tenders_feed:
        if not is_genuine_record(item["title"]):
            continue
            
        val_formatted = clean_and_parse_financials(item["project_value"])
        emd_formatted = clean_and_parse_financials(item["emd"])
        valid_deadline = extract_standard_deadline(item["deadline"])
        inferred_sec = infer_sector(item["title"], "")
        
        combined_title = f"{item['title']} (Value: {val_formatted} | EMD: {emd_formatted} | Deadline: {valid_deadline})"
        
        if combined_title in existing_tenders:
            continue
            
        cleaned_tenders.append({
            "title": combined_title,
            "agency": f"{item['agency']} - {item['location']}",
            "state": item["state"],
            "sector": inferred_sec,
            "url": item["url"],
            "date_scraped": datetime.now(timezone.utc).isoformat()
        })
        
    if cleaned_tenders:
        try:
            supabase.table(tenders_table).insert(cleaned_tenders).execute()
            print(f"✅ Successful: Ingested {len(cleaned_tenders)} procurement records.")
        except Exception as e: 
            print(f"❌ Tenders Upload Failure: {str(e)}")
    else:
        print("ℹ️ Tenders clean: No fresh records found.")

    # -----------------------------------------------------------------
    # STREAM B: GOVERNMENT RECRUITMENT REPOSITORY PIPELINE
    # -----------------------------------------------------------------
    jobs_table = "jobs"
    existing_jobs = set()
    
    try:
        db_all_jobs = supabase.table(jobs_table).select("title").execute()
        if db_all_jobs.data:
            existing_jobs = {r["title"] for r in db_all_jobs.data}
        print(f"📡 Cached {len(existing_jobs)} active recruitment keys.")
    except Exception as e:
        print(f"⚠️ Jobs cache skipped: {e}")

    raw_jobs_feed = [
        {"title": "CGPSC Assistant Professor Technical Recruitment Notification 2026", "agency": "Chhattisgarh Public Service Commission", "state": "Chhattisgarh", "vacancies": "412 Posts", "salary": "Level 10 (₹57,700 - ₹1,82,400)", "qualification": "B.E / B.Tech / M.Tech in respective domains", "deadline": "30-08-2026", "url": "https://psc.cg.gov.in"},
        {"title": "Railway RRB Junior Engineer Civil Executive Vacancy Roster", "agency": "Railway Recruitment Board", "state": "All India", "vacancies": "1,205 Posts", "salary": "₹35,400 - ₹1,12,400", "qualification": "Diploma or Degree in Civil Engineering", "deadline": "12-09-2026", "url": "https://rrbbilaspur.gov.in"},
        {"title": "Draft Notification for Internal Transfer Rules of Grade-4 Clerical Staff Members", "agency": "Department of Revenue", "state": "Chhattisgarh", "vacancies": "N/A", "salary": "N/A", "qualification": "Internal Only", "deadline": "Open", "url": "https://cg.nic.in"}
    ]
    
    cleaned_jobs = []
    for job in raw_jobs_feed:
        if not is_genuine_record(job["title"]):
            print(f"🗑️ Dropped Job Noise: {job['title'][:40]}...")
            continue
            
        valid_dl = extract_standard_deadline(job["deadline"])
        
        # TOP 1% SCHEMA COMPRESSION: Packing rich data into guaranteed safe core columns
        rich_title = f"{job['title']} (Vacancies: {job['vacancies']} | Salary: {job['salary']} | Deadline: {valid_dl})"
        
        if rich_title in existing_jobs:
            print(f"⏩ Skipping Existing Job: {job['title'][:40]}...")
            continue
            
        job_record = {
            "title": rich_title,
            "agency": f"{job['agency']} (Req: {job['qualification']})",
            "state": job["state"],
            "sector": "Government Jobs",
            "url": job["url"],
            "date_scraped": datetime.now(timezone.utc).isoformat()
        }
            
        cleaned_jobs.append(job_record)
        
    if cleaned_jobs:
        try:
            supabase.table(jobs_table).insert(cleaned_jobs).execute()
            print(f"✅ Successful: Ingested {len(cleaned_jobs)} recruitment updates cleanly.")
        except Exception as e: 
            print(f"❌ Jobs Upload Failure: {str(e)}")
    else:
        print("ℹ️ Job repository clean: No new notifications.")

if __name__ == "__main__":
    run_ingestion_cycle()