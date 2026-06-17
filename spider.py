from playwright.sync_api import sync_playwright
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from bs4 import BeautifulSoup

FILE_ID = "1JEqF997YS2bwI_NyOJMU5dKjnoanuBR5BA7LiqffRB4"
KEY_FILE = "client_secret.json"

def get_google_sheet():
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name(KEY_FILE, scope)
    client = gspread.authorize(creds)
    return client.open_by_key(FILE_ID).sheet1

def scout_cg_tenders():
    print("🤖 Launching Opporta Scout (Stealth Mode)...")
    with sync_playwright() as p:
        # Use a more realistic browser context
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 720}
        )
        page = context.new_page()
        
        # Go to home and wait
        page.goto("https://eproc.cgstate.gov.in/nicgep/app", wait_until="domcontentloaded")
        
        # Sometimes there is a 'Proceed' or 'Welcome' screen, let's wait a moment
        page.wait_for_timeout(5000) 
        
        # Try to find the link using a more flexible selector
        try:
            print("🔍 Looking for 'Tenders by Organisation'...")
            page.wait_for_selector("a:has-text('Tenders by Organisation')", timeout=15000)
            page.click("a:has-text('Tenders by Organisation')")
            
            page.wait_for_load_state("networkidle")
            
            print("🔍 Selecting Public Works Department...")
            page.wait_for_selector("a:has-text('Public Works Department')", timeout=15000)
            page.click("a:has-text('Public Works Department')")
            
            page.wait_for_selector("table#table", timeout=15000)
            content = page.content()
        except Exception as e:
            print(f"❌ Navigation Error: {e}")
            browser.close()
            return []
            
        browser.close()
        
        # Parse data
        soup = BeautifulSoup(content, 'html.parser')
        table = soup.find('table', {'id': 'table'})
        scraped_data = []
        if table:
            for row in table.find_all('tr')[1:6]:
                cols = row.find_all('td')
                if len(cols) > 3:
                    scraped_data.append([
                        "SCRAPED", "Chhattisgarh", "Civil Works", "PWD",
                        cols[1].text.strip(), cols[3].text.strip(), cols[4].text.strip(),
                        "Pending", "N/A", "N/A", "N/A", "N/A", "Stealth-Scrape", "N/A", "eproc.cgstate.gov.in"
                    ])
        return scraped_data

if __name__ == "__main__":
    try:
        new_tenders = scout_cg_tenders()
        if new_tenders:
            sheet = get_google_sheet()
            for tender in new_tenders:
                sheet.append_row(tender)
            print(f"🚀 Success: {len(new_tenders)} tenders added!")
        else:
            print("⚠️ No data captured.")
    except Exception as e:
        print(f"❌ Script Error: {e}")