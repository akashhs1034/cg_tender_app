import os
import random
from datetime import datetime, timedelta
from supabase import create_client, Client

# =====================================================================
# 1. CLOUD SECURITY & CONFIGURATION
# =====================================================================
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not all([SUPABASE_URL, SUPABASE_KEY]):
    print("⚠️ WARNING: Cloud Database Keys missing. Ensure GitHub Secrets are set.")
    # Fallback logic can be placed here if running locally without env vars

# Initialize Secure Cloud Tunnel
try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    print(f"🚨 Initialization Error: {e}")

# =====================================================================
# 2. HIGH-VOLUME ENTERPRISE DATA ENGINE (SYNTHETIC SCALER)
# =====================================================================
# This engine generates massive payloads of realistic data to test dashboard 
# load limits, financial value parsing, and geographic bar charting.

def generate_tenders(count=80):
    print(f"📡 Generating {count} high-fidelity Tender records...")
    tenders = []
    
    states = ["Chhattisgarh", "Uttar Pradesh"]
    cg_depts = ["PWD Raipur", "CG Water Board", "NRDA", "CSPDCL", "CG Health Dept"]
    up_depts = ["UP Power Corp", "UP PWD", "Jal Nigam", "UP Housing Board", "Medical Ed UP"]
    sectors = ["Civil", "Electrical", "IT Infrastucture", "Roads & Highways", "Healthcare", "Consulting"]
    
    for i in range(count):
        state = random.choice(states)
        dept = random.choice(cg_depts) if state == "Chhattisgarh" else random.choice(up_depts)
        sector = random.choice(sectors)
        
        # Generate realistic financial values (e.g., "₹ 14.5 Cr" or "₹ 85 Lakh")
        val_type = random.choice(["Cr", "Lakh"])
        if val_type == "Cr":
            val_num = round(random.uniform(1.0, 50.0), 2)
        else:
            val_num = random.randint(10, 99)
            
        deadline_date = (datetime.now() + timedelta(days=random.randint(5, 90))).strftime('%Y-%m-%d')
        
        tenders.append({
            'state': state,
            'department': dept,
            'title': f"{sector} Project Phase {random.randint(1,4)}: {random.choice(['Expansion', 'Upgradation', 'New Construction', 'Maintenance'])}",
            'value': f"₹ {val_num} {val_type}",
            'deadline': deadline_date,
            'source_url': 'https://eproc.cgstate.gov.in' if state == "Chhattisgarh" else 'https://etender.up.nic.in',
            'scraped_at': datetime.now().isoformat()
        })
    return tenders

def generate_jobs(count=70):
    print(f"📡 Generating {count} high-fidelity Recruitment records...")
    jobs = []
    
    cg_boards = ["CGPSC", "CG Vyapam", "Police Recruitment Board CG", "Health Dept CG"]
    up_boards = ["UPSSSC", "UPPSC", "UP Police Board", "UP Education Dept"]
    qualifications = ["B.E. / B.Tech", "Diploma in Engineering", "Any Graduate", "MBBS", "12th Pass + ITI"]
    titles = ["Assistant Engineer", "Junior Engineer", "Medical Officer", "Technical Consultant", "Project Manager"]
    
    for i in range(count):
        state = random.choice(["Chhattisgarh", "Uttar Pradesh"])
        board = random.choice(cg_boards) if state == "Chhattisgarh" else random.choice(up_boards)
        
        jobs.append({
            'state': state,
            'board': board,
            'job_title': f"{random.choice(titles)} ({random.choice(['Civil', 'Electrical', 'IT', 'General'])})",
            'vacancy_count': str(random.randint(5, 500)),
            'qualification': random.choice(qualifications),
            'apply_url': 'https://psc.cg.gov.in/' if state == "Chhattisgarh" else 'http://upsssc.gov.in/',
            'scraped_at': datetime.now().isoformat()
        })
    return jobs

# =====================================================================
# 3. SUPABASE SECURE UPLOAD PIPELINE
# =====================================================================
def run_centralized_pipeline():
    print(f"\n=== ⚡ OPPORTA ENGINE WAKING UP: {datetime.now()} ===")
    
    # 1. Harvest Data Payload
    tenders_data = generate_tenders(count=120) # Generating 120 Tenders
    jobs_data = generate_jobs(count=85)        # Generating 85 Jobs
    
    # 2. Push Tenders to Cloud (In chunks to prevent payload limits)
    if tenders_data:
        print(f"📦 Pushing {len(tenders_data)} Tenders to Cloud DB...")
        try:
            # Pushing in blocks of 50
            for i in range(0, len(tenders_data), 50):
                chunk = tenders_data[i:i+50]
                supabase.table("opporta_tenders").insert(chunk).execute()
            print("✅ Tenders Pipeline Sync Complete.")
        except Exception as e:
            print(f"🚨 Failed to push tenders: {e}")
            
    # 3. Push Jobs to Cloud
    if jobs_data:
        print(f"📦 Pushing {len(jobs_data)} Jobs to Cloud DB...")
        try:
            for i in range(0, len(jobs_data), 50):
                chunk = jobs_data[i:i+50]
                supabase.table("opporta_jobs").insert(chunk).execute()
            print("✅ Vacancies Pipeline Sync Complete.")
        except Exception as e:
            print(f"🚨 Failed to push jobs: {e}")

    print("=== 🟢 PIPELINE CYCLE COMPLETION SUCCESSFUL ===\n")

if __name__ == "__main__":
    run_centralized_pipeline()