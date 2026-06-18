import os
import re
from datetime import datetime, timezone
from supabase import create_client

# =====================================================================
# 1. PRODUCTION ACCESS LAYER
# =====================================================================
# Extracted from your provided dashboard URL and secret key
SUPABASE_URL = "https://iujzepmdnkawbmpupuzk.supabase.co"
SUPABASE_KEY = "sb_secret_HylsWx7Ucrgig6B6glpySQ_B6FP-w6M"

# Connectivity Verification
print(f"🔗 Attempting connection to: {SUPABASE_URL}")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# =====================================================================
# 2. AI EVALUATOR LOGIC
# =====================================================================
MY_TURNOVER = 50_000_000  # 5 Crore

def calculate_win_probability(sector, project_value_str):
    score = 50
    if sector != "General Opportunities": score += 20
    try:
        val_str = "".join(c for c in project_value_str if c.isdigit())
        val_num = float(val_str) if val_str else 0
        if 0 < val_num < (MY_TURNOVER * 0.5): score += 30
        elif val_num > (MY_TURNOVER * 2): score -= 20
    except: score -= 10
    return min(max(score, 0), 100)

# =====================================================================
# 3. DUAL-STREAM INGESTION ENGINE
# =====================================================================
def run_ingestion_cycle():
    print(f"⚡ Starting Ingestion: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # STREAM A: TENDERS
    raw_tenders = [{"title": "SECL Coal Transport", "sector": "Coal & Mining", "project_value": "₹4,500,000", "agency": "SECL", "state": "CG", "url": "url1"}]
    cleaned_tenders = []
    for item in raw_tenders:
        score = calculate_win_probability(item['sector'], item['project_value'])
        rich_title = f"{item['title']} | Win Score: {score}%"
        cleaned_tenders.append({
            "title": rich_title, "agency": item['agency'], "state": item['state'],
            "sector": item['sector'], "url": item['url'], "date_scraped": datetime.now(timezone.utc).isoformat()
        })
    if cleaned_tenders: supabase.table("tenders").insert(cleaned_tenders).execute()

    # STREAM B: JOBS
    raw_jobs = [{"title": "CGPSC Assistant Professor", "vacancies": "412", "salary": "₹57,700", "agency": "CGPSC", "url": "url2"}]
    cleaned_jobs = []
    for job in raw_jobs:
        rich_title = f"{job['title']} | Vacancies: {job['vacancies']} | Salary: {job['salary']}"
        cleaned_jobs.append({
            "title": rich_title, "agency": job['agency'], "sector": "Government Jobs",
            "url": job['url'], "date_scraped": datetime.now(timezone.utc).isoformat()
        })
    if cleaned_jobs: supabase.table("jobs").insert(cleaned_jobs).execute()

    print("✅ Dual-Stream Ingestion Complete.")

if __name__ == "__main__":
    run_ingestion_cycle()