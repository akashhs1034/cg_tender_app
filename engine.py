import json
import time
import random
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import pandas as pd
from supabase import create_client, Client

# =====================================================================
# 1. CLOUD DATABASE TUNNEL
# =====================================================================
def get_supabase_client():
    url, key = "", ""
    try:
        # Securely read your existing Streamlit keys so you don't have to re-type them
        with open(".streamlit/secrets.toml", "r") as f:
            for line in f:
                if "SUPABASE_URL" in line:
                    url = line.split("=")[1].strip().strip('"').strip("'")
                if "SUPABASE_KEY" in line:
                    key = line.split("=")[1].strip().strip('"').strip("'")
        return create_client(url, key)
    except Exception as e:
        print(f"🚨 Cloud Key Error: {e}")
        return None

supabase = get_supabase_client()

# =====================================================================
# 2. THE UNIVERSAL PARSING MODULE
# =====================================================================
def load_pipeline_config(config_path="config.json"):
    with open(config_path, "r") as file:
        return json.load(file)

def execute_safe_crawl(portal_meta):
    state = portal_meta["state"]
    name = portal_meta["portal_name"]
    url = portal_meta["target_url"]
    selectors = portal_meta["selectors"]
    
    print(f"📡 Connecting to: [{state}] {name}...")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept-Language": "en-US,en;q=0.9"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            print(f"⚠️ {state} Portal returned status code: {response.status_code}")
            return []
            
        soup = BeautifulSoup(response.text, "html.parser")
        extracted_records = []
        
        container_table = soup.find(id=selectors["table_id"])
        rows = container_table.find_all(selectors["row_tag"]) if container_table else soup.find_all(selectors["row_tag"])
            
        for row in rows:
            cols = row.find_all("td")
            max_col_index = max(selectors["columns"].values())
            
            if len(cols) > max_col_index:
                record = {
                    "state": state,
                    "department": cols[selectors["columns"]["department"]].text.strip(),
                    "title": cols[selectors["columns"]["title"]].text.strip(),
                    "value": cols[selectors["columns"]["value"]].text.strip(),
                    "deadline": cols[selectors["columns"]["deadline"]].text.strip(),
                    "source_url": url,
                    "scraped_at": datetime.now().isoformat()
                }
                extracted_records.append(record)
                
        print(f"✅ Extracted {len(extracted_records)} live records from {state}.")
        return extracted_records

    except Exception as e:
        print(f"🚨 Network link failure for {state}: {e}")
        return []

# =====================================================================
# 3. PIPELINE ORCHESTRATION & DATABASE PUSH
# =====================================================================
def run_global_pipeline():
    config = load_pipeline_config()
    master_dataset = []
    
    for portal in config["portals"]:
        portal_data = execute_safe_crawl(portal)
        master_dataset.extend(portal_data)
        
        cooldown = random.uniform(3.0, 6.0)
        print(f"💤 Cooling down for {cooldown:.2f} seconds to avoid IP block...")
        time.sleep(cooldown)
        
    print(f"\n📦 Preparing to push {len(master_dataset)} total rows to Supabase Cloud...")
    
    if master_dataset and supabase:
        try:
            # Push the real data into the cloud!
            supabase.table("opporta_tenders").insert(master_dataset).execute()
            print("🟢 SUCCESS: Live data perfectly synced to Cloud Database!")
        except Exception as e:
            print(f"🚨 Cloud Upload Failed: {e}")
    else:
        print("⚠️ No data extracted or Cloud offline. Upload skipped.")

if __name__ == "__main__":
    print("🚀 Live Ingestion Engine Online.")
    run_global_pipeline()