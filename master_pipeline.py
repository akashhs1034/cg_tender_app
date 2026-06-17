import os
import json
import time
import random
import pandas as pd
from datetime import datetime
from bs4 import BeautifulSoup
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from supabase import create_client, Client

# =====================================================================
# 1. CLOUD SECURITY & CONFIGURATION
# =====================================================================
# Keys are pulled securely from GitHub Secrets or Local Environment
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not all([GEMINI_API_KEY, SUPABASE_URL, SUPABASE_KEY]):
    raise ValueError("❌ CRITICAL: Missing API Keys. Ensure environment variables are set.")

# Initialize Cloud Clients
gemini_client = genai.Client(api_key=GEMINI_API_KEY)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

class TenderSchema(BaseModel):
    tender_id: str
    department: str
    work_category: str = Field(description="Civil, Electrical, IT, Road, Mining, or Other")
    estimated_value_lakhs: float
    deadline_date: str

class TenderBatchSchema(BaseModel):
    tenders: list[TenderSchema]

# =====================================================================
# 2. DATA CRAWLERS (CG & UP Focus)
# =====================================================================
def scrape_cg_up_tenders():
    print("📡 Querying CG & UP Tender parameters...")
    # Simulated extraction for architectural demonstration
    return [
        {
            'state': 'Chhattisgarh', 'sector': 'Civil',
            'department': 'PWD Raipur', 'title': 'Construction of 4-Lane Highway bypass',
            'value': '₹ 14.5 Cr', 'deadline': '2026-07-15', 'source_url': 'https://eproc.cgstate.gov.in'
        },
        {
            'state': 'Uttar Pradesh', 'sector': 'Electrical',
            'department': 'UP Power Corp', 'title': 'Installation of 500kW Solar Grid',
            'value': '₹ 2.1 Cr', 'deadline': '2026-07-20', 'source_url': 'https://etender.up.nic.in'
        }
    ]

def scrape_cg_up_jobs():
    print("📡 Querying CG & UP Recruitment Boards...")
    return [
        {
            'state': 'Chhattisgarh', 'board': 'CGPSC',
            'job_title': 'Assistant Engineer (Civil)', 'vacancy_count': '85',
            'qualification': 'B.E. / B.Tech Civil', 'apply_url': 'https://psc.cg.gov.in/'
        },
        {
            'state': 'Uttar Pradesh', 'board': 'UPSSSC',
            'job_title': 'Junior Engineer (Water Resources)', 'vacancy_count': '210',
            'qualification': 'Diploma in Engineering', 'apply_url': 'http://upsssc.gov.in/'
        }
    ]

# =====================================================================
# 3. SUPABASE INTEGRATION PIPELINE
# =====================================================================
def run_centralized_pipeline():
    print(f"\n=== CLOUD PIPELINE INITIALIZED: {datetime.now()} ===")
    
    # 1. Fetch Data
    tenders_data = scrape_cg_up_tenders()
    jobs_data = scrape_cg_up_jobs()
    
    # 2. Push to Supabase Tenders Table
    if tenders_data:
        print(f"📦 Pushing {len(tenders_data)} Tenders to Cloud DB...")
        supabase.table("opporta_tenders").insert(tenders_data).execute()
        
    # 3. Push to Supabase Jobs Table
    if jobs_data:
        print(f"📦 Pushing {len(jobs_data)} Jobs to Cloud DB...")
        supabase.table("opporta_jobs").insert(jobs_data).execute()

    print("=== PIPELINE CYCLE COMPLETION SUCCESSFUL ===\n")

if __name__ == "__main__":
    run_centralized_pipeline()