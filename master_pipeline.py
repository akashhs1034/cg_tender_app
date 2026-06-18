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

try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    print(f"🚨 Initialization Error: {e}")

# =====================================================================
# 2. THE ASYNC MATRIX WORKERS WITH DATA EXTRACTION
# =====================================================================
async def fetch_portal(session, portal_config):
    """Worker hits a URL, reads the HTML, and extracts the crucial data."""
    url = portal_config.get("url")
    sector = portal_config.get("sector")
    state = portal_config.get("state")
    
    # STRICT KILL SWITCH: 15 seconds max wait time.
    timeout = aiohttp.ClientTimeout(total=15)
    
    try:
        async with session.get(url, timeout=timeout) as response:
            if response.status == 200:
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # --- THE EXTRACTION ZONE ---
                page_title = soup.title.string.strip() if soup.title else "No Title Found"
                
                # Universal Link Radar (Looking for PDFs and Apply Links)
                all_links = soup.find_all('a', href=True)
                valuable_links = []
                
                for link in all_links:
                    href = link['href'].lower()
                    text = link.text.strip()
                    if '.pdf' in href or 'apply' in href or 'advt' in href:
                        valuable_links.append({
                            "text": text if text else "Document Link",
                            "url": href if href.startswith('http') else f"{url.rstrip('/')}/{href.lstrip('/')}"
                        })
                
                return {
                    "url": url,
                    "status": "Success",
                    "sector": sector,
                    "state": state,
                    "page_title": page_title,
                    "documents_found": len(valuable_links),
                    "sample_links": valuable_links[:3], 
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {"url": url, "status": f"Failed: HTTP {response.status}", "sector": sector}
    except asyncio.TimeoutError:
         return {"url": url, "status": "Error: Timeout (Site Dead)", "sector": sector}
    except Exception as e:
        return {"url": url, "status": f"Error: {str(e)}", "sector": sector}

async def matrix_scanner(portals):
    """The central router that fires all workers simultaneously."""
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    async with aiohttp.ClientSession(headers=headers) as session:
        tasks = [fetch_portal(session, portal) for portal in portals]
        results = await asyncio.gather(*tasks)
        return results

# =====================================================================
# 3. PIPELINE EXECUTION & DATA REVIEW
# =====================================================================
def run_real_pipeline():
    print(f"\n=== ⚡ OPPORTA DATA EXTRACTOR WAKING UP: {datetime.now()} ===")
    
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
            portals = config.get("portals", [])
    except Exception as e:
        print("🚨 Error loading config.json. Ensure the file exists.")
        return

    if not portals:
        print("⚠️ No portals found in config.json. Exiting.")
        return

    loop = asyncio.get_event_loop()
    scan_results = loop.run_until_complete(matrix_scanner(portals))
    
    print("\n=== 📊 EXTRACTION REPORT ===")
    for result in scan_results:
        if result['status'] == 'Success':
            print(f"\n✅ [SUCCESS] {result['url']}")
            print(f"   Page Title: {result['page_title']}")
            print(f"   Valuable Links Found: {result['documents_found']}")
            for link in result.get('sample_links', []):
                print(f"   - {link['text']}: {link['url']}")
        else:
            print(f"\n❌ [FAILED] {result['url']} | Reason: {result['status']}")

    print("\n=== 🟢 PIPELINE CYCLE COMPLETION SUCCESSFUL ===\n")

if __name__ == "__main__":
    run_real_pipeline()