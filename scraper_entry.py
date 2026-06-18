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
# 2. HEURISTIC PARSING FUNCTIONS
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

def is_genuine_contract_node(title_str):
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
    print(f"⚡ Starting Ingestion Loop: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    target_table = "tenders"
    
    # TOP 1% DEDUPLICATION GUARD: Fetch existing titles from database to avoid duplicate errors locally
    existing_titles = set()
    try:
        db_check = supabase.table(target_table).select("title").execute()
        if db_check.data:
            existing_titles = {row["title"] for row in db_check.data}
            print(f"📡 Cached {len(existing_titles)} existing contract signatures from database to prevent conflicts.")
    except Exception as e:
        print(f"⚠️ Notice: Pre-ingestion check skipped. Proceeding blindly. Detail: {e}")

    raw_scraped_feed = [
        {"title": "SECL Coal Evacuation and Transport Work Phase 4", "agency": "South Eastern Coalfields Limited", "location": "Korba", "state": "Chhattisgarh", "project_value": "₹4.50 Crore", "emd": "₹4,50,000", "deadline": "28-07-2026", "url": "https://janjgir-champa.gov.in"},
        {"title": "Procurement of Critical ICU Emergency Medical Supplies", "agency": "Directorate of Health Services", "location": "Raipur", "state": "Chhattisgarh", "project_value": "45 Lakhs", "emd": "Not specified", "deadline": "15/08/2026", "url": "https://gariaband.gov.in"},
        {"title": "Internal Departmental Promotion Policies and PPT Presentation Guidelines", "agency": "Zilla Panchayat Office", "location": "Durg", "state": "Chhattisgarh", "project_value": "Not specified", "emd": "Not specified", "deadline": "Open", "url": "https://durg.gov.in"}
    ]
    
    cleaned_batch_payload = []
    
    for item in raw_scraped_feed:
        if not is_genuine_contract_node(item["title"]):
            print(f"🗑️ Dropped Administrative Noise: {item['title'][:40]}...")
            continue
            
        val_formatted = clean_and_parse_financials(item["project_value"])
        emd_formatted = clean_and_parse_financials(item["emd"])
        valid_deadline = extract_standard_deadline(item["deadline"])
        inferred_sec = infer_sector(item["title"], "")
        
        combined_title = f"{item['title']} (Value: {val_formatted} | EMD: {emd_formatted} | Deadline: {valid_deadline})"
        
        # Checking logic to ensure we don't try to insert something that is already inside the table
        if combined_title in existing_titles:
            print(f"⏩ Skipping Duplicate Row: {item['title'][:40]}... already exists.")
            continue
            
        normalized_row = {
            "title": combined_title,
            "agency": f"{item['agency']} - {item['location']}",
            "state": item["state"],
            "sector": inferred_sec,
            "url": item["url"],
            "date_scraped": datetime.now(timezone.utc).isoformat()
        }
        cleaned_batch_payload.append(normalized_row)
        
    if cleaned_batch_payload:
        try:
            # FIXED: Removed the upsert constraint and swapped with standard insert tracking block
            supabase.table(target_table).insert(cleaned_batch_payload).execute()
            print(f"✅ Ingestion Successful! Uploaded {len(cleaned_batch_payload)} fresh high-signal records to '{target_table}' securely.")
        except Exception as e:
            print(f"❌ Supabase Ingestion Upload Failure: {str(e)}")
    else:
        print("ℹ️ Cycle complete. No new, non-duplicate high-signal records detected.")

if __name__ == "__main__":
    run_ingestion_cycle()