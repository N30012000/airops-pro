import os
import random
from datetime import datetime, timedelta
from supabase import create_client, Client
from dotenv import load_dotenv

# Setup
load_dotenv()
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

if not url or not key:
    print("❌ Error: Secrets missing in .env")
    exit()

supabase: Client = create_client(url, key)
print("🚀 Seeding Data...")

# Generators
def get_date(): return (datetime.now() - timedelta(days=random.randint(0, 30))).isoformat()

# 1. Bird Strikes
print("   🐦 Seeding Bird Strikes...")
for i in range(5):
    supabase.table("bird_strikes").insert({
        "report_number": f"BS-2025-{100+i}",
        "type": "Bird Strike",
        "date": get_date(),
        "flight_number": f"PF-{random.randint(100,900)}",
        "risk_level": random.choice(["Low", "Medium", "High"]),
        "status": "Open",
        "investigation_status": "Under Investigation",
        "narrative": "Bird strike on approach.",
        "created_at": get_date()
    }).execute()

# 2. Hazards (Crucial for Dashboard Risk Pie Chart)
print("   🔶 Seeding Hazards...")
for i in range(5):
    supabase.table("hazard_reports").insert({
        "report_number": f"HAZ-2025-{100+i}",
        "type": "Hazard Report",
        "hazard_title": f"Hazard Example {i+1}",
        "risk_level": random.choice(["High", "Extreme", "Medium"]),
        "status": "New",
        "investigation_status": "Open",
        "description": "FOD found on ramp.",
        "created_at": get_date(),
        "reporter_department": "Ground Ops"
    }).execute()

# 3. Incidents
print("   ⚠️ Seeding Incidents...")
for i in range(5):
    supabase.table("aircraft_incidents").insert({
        "report_number": f"INC-2025-{100+i}",
        "type": "Aircraft Incident",
        "flight_number": f"PF-{random.randint(100,900)}",
        "risk_level": "Medium",
        "status": "Open",
        "investigation_status": "In Progress",
        "description": "Hydraulic leak detected.",
        "created_at": get_date()
    }).execute()

# 4. FSR
print("   📝 Seeding FSR...")
for i in range(5):
    supabase.table("fsr_reports").insert({
        "id": f"FSR-2025-{100+i}",
        "type": "Flight Services Report",
        "flight_number": f"PF-{random.randint(100,900)}",
        "risk_level": "Low",
        "status": "Closed",
        "created_at": get_date(),
        "overall_rating": 4
    }).execute()

# 5. Captain Debrief
print("   👨‍✈️ Seeding Debriefs...")
for i in range(5):
    supabase.table("captain_dbr").insert({
        "id": f"DBR-2025-{100+i}",
        "type": "Captain Debrief",
        "flight_number": f"PF-{random.randint(100,900)}",
        "risk_level": "Low",
        "status": "Closed",
        "created_at": get_date(),
        "overall_assessment": "Normal"
    }).execute()

# 6. Laser Strikes
print("   🔴 Seeding Laser Strikes...")
for i in range(5):
    supabase.table("laser_strikes").insert({
        "report_number": f"LS-2025-{100+i}",
        "type": "Laser Strike",
        "flight_number": f"PF-{random.randint(100,900)}",
        "risk_level": "High",
        "status": "Open",
        "investigation_status": "Open",
        "created_at": get_date()
    }).execute()

# 7. TCAS
print("   ✈️ Seeding TCAS...")
for i in range(5):
    supabase.table("tcas_reports").insert({
        "report_number": f"TCAS-2025-{100+i}",
        "type": "TCAS Report",
        "flight_number": f"PF-{random.randint(100,900)}",
        "risk_level": "Extreme",
        "status": "Closed",
        "investigation_status": "Closed",
        "created_at": get_date()
    }).execute()

print("✅ DONE! Data injected.")
