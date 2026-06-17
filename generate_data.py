import pandas as pd
import random
from datetime import datetime, timedelta

# Realistic variables for our two target states
states = ["Chhattisgarh", "Uttar Pradesh"]
categories = ["Civil Works", "Electrical", "Coal Supply", "Medical Supply", "Government Jobs", "IT Services", "Transport", "Manufacturing"]

cg_orgs = ["PWD Raipur", "SECL Bilaspur", "CGMSC", "Nagar Nigam Durg", "CHiPS", "Bhilai Steel Plant"]
up_orgs = ["UP PWD Gonda", "Lucknow Nagar Nigam", "NCL Singrauli", "NIC Lucknow", "UP Jal Nigam", "Kanpur Municipal Corp"]

data = []

print("🚀 Generating 500 realistic tenders for Opporta...")

for i in range(1, 501):
    state = random.choice(states)
    org = random.choice(cg_orgs) if state == "Chhattisgarh" else random.choice(up_orgs)
    category = random.choice(categories)
    
    # Random realistic values
    val_num = round(random.uniform(10, 500), 2)
    val_type = random.choice(["L", "Cr"])
    project_value = f"₹ {val_num} {val_type}" if category != "Government Jobs" else f"₹ {random.randint(25, 80)},000 /mo"
    
    deadline = (datetime.now() + timedelta(days=random.randint(5, 60))).strftime("%d %b %Y")
    ai_score = f"{random.randint(70, 99)}%"
    eligibility = "Eligible" if int(ai_score[:2]) > 85 else "Review Required"
    
    data.append({
        "id": i,
        "state": state,
        "category": category,
        "organization": org,
        "title": f"High-Value {category} Contract - {org} Sector {random.randint(1,99)}",
        "project_value": project_value,
        "deadline": deadline,
        "ai_score": ai_score,
        "eligibility": eligibility,
        "emd": f"₹ {random.randint(10000, 500000)}",
        "contractor_class": random.choice(["Class A", "Class B", "Class C", "Class D", "Open"]),
        "experience": random.choice(["No Experience", "1-3 Years", "3-5 Years", "5+ Years"]),
        "description": f"Comprehensive and verified opportunity for {category} operations managed by {org}.",
        "detailed_requirements": "Must hold valid state registration, clear financial turnover for the past 2 fiscal years, and submit EMD prior to the deadline.",
        "direct_url": "https://opporta.in/apply"
    })

# Save to the CSV your app reads
df = pd.DataFrame(data)
df.to_csv("master_leads.csv", index=False)
print("✅ Successfully generated 500 rows in master_leads.csv!")