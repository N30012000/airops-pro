# seed_deep.py
import os
import random
from datetime import datetime, timedelta
from supabase import create_client, Client
from dotenv import load_dotenv

# 1. Setup
load_dotenv()
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

if not url or not key:
    print("❌ Error: Secrets missing.")
    exit()

supabase: Client = create_client(url, key)

print("🚀 Starting Deep Seed...")

# 2. Generators
def get_date(): return (datetime.now() - timedelta(days=random.randint(0, 30))).isoformat()
def get_time(): return f"{random.randint(0,23):02d}:{random.randint(0,59):02d}"

# 3. Data Inserters (Matched to your app.py Schema)

def seed_bird_strikes(n=5):
    print(f"   🐦 Bird Strikes ({n})...")
    for _ in range(n):
        dt = get_date()
        rid = f"BS-{random.randint(1000,9999)}"
        data = {
            "report_number": rid, "type": "Bird Strike", "date": dt, "time": get_time(),
            "flight_number": "PF-123", "aircraft_reg": "AP-BMA", "origin": "OPSK", "destination": "OPKC",
            "flight_phase": "Landing", "bird_species": "Kite", "damage_level": "Minor",
            "risk_level": "Medium", "status": "Open", "narrative": "Bird strike on nose gear.",
            "created_at": dt, "department": "Flight Operations"
        }
        supabase.table("bird_strikes").insert(data).execute()

def seed_laser_strikes(n=5):
    print(f"   🔴 Laser Strikes ({n})...")
    for _ in range(n):
        dt = get_date()
        rid = f"LS-{random.randint(1000,9999)}"
        data = {
            "report_number": rid, "type": "Laser Strike", "date": dt, "time": get_time(),
            "flight_number": "PF-456", "aircraft_reg": "AP-BMJ", "location_description": "5nm Final",
            "laser_color": "Green", "intensity": "High", "crew_effects": ["Distraction"],
            "risk_level": "High", "status": "Under Investigation", "narrative": "Green laser from ground.",
            "created_at": dt, "department": "Flight Operations"
        }
        supabase.table("laser_strikes").insert(data).execute()

def seed_tcas(n=5):
    print(f"   ✈️ TCAS ({n})...")
    for _ in range(n):
        dt = get_date()
        rid = f"TCAS-{random.randint(1000,9999)}"
        data = {
            "report_number": rid, "type": "TCAS Report", "date": dt, "time": get_time(),
            "flight_number": "PF-789", "aircraft_reg": "AP-BME", "tcas_alert_type": "RA - Climb",
            "risk_level": "Extreme", "status": "Closed", "narrative": "RA Climb received due to conflicting traffic.",
            "created_at": dt, "department": "Flight Operations"
        }
        supabase.table("tcas_reports").insert(data).execute()

def seed_incidents(n=5):
    print(f"   ⚠️ Incidents ({n})...")
    for _ in range(n):
        dt = get_date()
        rid = f"INC-{random.randint(1000,9999)}"
        data = {
            "report_number": rid, "type": "Aircraft Incident", "notification_type": "Incident",
            "date": dt, "time": get_time(), "flight_number": "PF-101", "aircraft_reg": "AP-BMH",
            "incident_category": "Technical", "description": "Hydraulic leak.",
            "risk_level": "Medium", "status": "Open", "narrative": "Hydraulic fluid observed on landing gear.",
            "created_at": dt, "department": "Engineering"
        }
        supabase.table("aircraft_incidents").insert(data).execute()

def seed_hazards(n=5):
    print(f"   🔶 Hazards ({n})...")
    for _ in range(n):
        dt = get_date()
        rid = f"HAZ-{random.randint(1000,9999)}"
        data = {
            "report_number": rid, "type": "Hazard Report", "title": "Loose FOD",
            "hazard_category": "Ground Operations", "risk_level": "Low", "status": "Open",
            "description": "Plastic debris on ramp.", "created_at": dt, "department": "Ground Ops"
        }
        supabase.table("hazard_reports").insert(data).execute()

def seed_fsr(n=5):
    print(f"   📝 FSR ({n})...")
    for _ in range(n):
        dt = get_date()
        rid = f"FSR-{random.randint(1000,9999)}"
        data = {
            "id": rid, "type": "Flight Services Report", "date": dt, "flight_number": "PF-202",
            "ratings": {"overall": 4}, "issues": ["None"], "risk_level": "Low", "status": "Closed",
            "created_at": dt, "department": "Cabin Services"
        }
        supabase.table("fsr_reports").insert(data).execute()

def seed_dbr(n=5):
    print(f"   👨‍✈️ Captain DBR ({n})...")
    for _ in range(n):
        dt = get_date()
        rid = f"DBR-{random.randint(1000,9999)}"
        data = {
            "id": rid, "type": "Captain's Debrief", "date": dt, "flight_number": "PF-303",
            "overall_assessment": "Normal", "risk_level": "Low", "status": "Closed",
            "created_at": dt, "department": "Flight Operations"
        }
        supabase.table("captain_dbr").insert(data).execute()

# Run
try:
    seed_bird_strikes()
    seed_laser_strikes()
    seed_tcas()
    seed_incidents()
    seed_hazards()
    seed_fsr()
    seed_dbr()
    print("\n✅ DONE. Refresh App now.")
except Exception as e:
    print(f"\n❌ Error: {e}")
