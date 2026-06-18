import os
import asyncio
import aiohttp
from bs4 import BeautifulSoup
from datetime import datetime
import json
from supabase import create_client, Client

# =====================================================================
# 1. CLOUD SECURITY & CONFIGURATION
# =====================================================================
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not all([SUPABASE_URL, SUPABASE_KEY]):
    print("⚠️ WARNING: Cloud Database Keys missing. Ensure GitHub Secrets are set.")
    supabase = None
else:
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        print(f"🚨 Initialization Error: {e}")
        supabase = None

# =====================================================================
# 2. THE ASYNC MATRIX WORKERS
# =====================================================================
async def fetch_portal(session, portal_config):
    url = portal_config.get("url")
    sector = portal_config.get("sector")
    state = portal_config.get("state")
    timeout = aiohttp.ClientTimeout(total=15)
    
    try:
        async with session.get(url, timeout=timeout) as response:
            if response.status == 200:
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                page_title = soup.title.string.strip() if soup.title else "No Title Found"
                
                all_links = soup.find_all('a', href=True)
                valuable_links = []
                
                for link in all_links:
                    href = link['href'].lower()
                    text = link.text.strip()
                    if '.pdf' in href or 'apply' in href or 'advt' in href:
                        valuable_links.append({
                            "title": text[:200] if text else "Document Link", # Truncated for DB safety
                            "url": href if href.startswith('http') else f"{url.rstrip('/')}/{href.lstrip('/')}"
                        })
                
                return {
                    "url": url,
                    "status": "Success",
                    "sector": sector,
                    "state": state,
                    "page_title": page_title,
                    "documents_found": len(valuable_links),
                    "extracted_docs": valuable_links[:15], # Hard cap at top 15 docs per site
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {"url": url, "status": f"Failed: HTTP {response.status}", "sector": sector}
    except asyncio.TimeoutError:
         return {"url": url, "status": "Error: Timeout (Site Dead)", "sector": sector}
    except Exception as e:
        return {"url": url, "status": f"Error: {str(e)}", "sector": sector}

async def matrix_scanner(portals):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    async with aiohttp.ClientSession(headers=headers) as session:
        tasks = [fetch_portal(session, portal) for portal in portals]
        return await asyncio.gather(*tasks)

# =====================================================================
# 3. PIPELINE EXECUTION & DATABASE INJECTION
# =====================================================================
def run_real_pipeline():
    print(f"\n=== ⚡ OPPORTA DATA EXTRACTOR WAKING UP: {datetime.now()} ===")
    
    try:
        with open('config.json', 'r') as f:
            portals = json.load(f).get("portals", [])
    except Exception:
        print("🚨 Error loading config.json.")
        return

    loop = asyncio.get_event_loop()
    scan_results = loop.run_until_complete(matrix_scanner(portals))
    
    tenders_batch = []
    jobs_batch = []
    
    print("\n=== 📊 EXTRACTION REPORT ===")
    for result in scan_results:
        if result['status'] == 'Success':
            print(f"✅ {result['url']} | Found: {result['documents_found']} links")
            
            # Map data for Supabase
            for doc in result.get('extracted_docs', []):
                record = {
                    "title": doc['title'],
                    "agency": result['url'],
                    "state": result['state'],
                    "sector": result['sector'],
                    "url": doc['url'],
                    "date_scraped": result['timestamp']
                }
                if "Jobs" in result['sector'] or "Recruitment" in result['sector']:
                    jobs_batch.append(record)
                else:
                    tenders_batch.append(record)
        else:
            print(f"❌ {result['url']} | {result['status']}")

    # --- SUPABASE INJECTION ---
    print("\n=== 💾 PUSHING TO CLOUD DATABASE ===")
    if not supabase:
        print("🚨 Skipping Database Push: Supabase Client Not Connected.")
    else:
        try:
            if tenders_batch:
                print(f"📦 Pushing {len(tenders_batch)} Tenders...")
                supabase.table('tenders').insert(tenders_batch).execute()
                print("✅ Tenders Synced Successfully.")
            
            if jobs_batch:
                print(f"📦 Pushing {len(jobs_batch)} Jobs...")
                supabase.table('jobs').insert(jobs_batch).execute()
                print("✅ Jobs Synced Successfully.")
                
        except Exception as e:
            print(f"🚨 DATABASE INJECTION FAILED: {str(e)}")

    print("\n=== 🟢 PIPELINE CYCLE COMPLETION SUCCESSFUL ===\n")

if __name__ == "__main__":
    run_real_pipeline()