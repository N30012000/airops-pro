import os
import random
import uuid
import json
import time
from datetime import datetime, timedelta, date
from supabase import create_client, Client
from dotenv import load_dotenv

# Load secrets
load_dotenv()
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

if not url or not key:
    print("❌ Error: SUPABASE_URL or SUPABASE_KEY missing.")
    exit()

supabase: Client = create_client(url, key)

print("🚀 Starting Deep Seed for Air Sial SMS v3.0...")

# ==============================================================================
# 1. EXTRACTED LOOKUPS (Direct from app.py)
# ==============================================================================

AIRPORTS = ["OPSK", "OPKC", "OPLA", "OPIS", "OPPS", "OPQT", "OPFA", "OPMT", "OMDB", "OMSJ", "OMAA", "OERK", "OEJN", "OTHH"]
AIRCRAFT_REGS = ["AP-BMA", "AP-BMB", "AP-BMC", "AP-BMD", "AP-BME", "AP-BMF", "AP-BMH", "AP-BMI", "AP-BMJ"]
FLIGHT_PHASES = ["Taxi Out", "Takeoff", "Climb", "Cruise", "Descent", "Approach", "Landing", "Taxi In"]
DEPARTMENTS = ["Flight Operations", "Engineering", "Ground Operations", "Cabin Services", "Safety", "Security"]
RISK_LEVELS = ["Low", "Medium", "High", "Extreme"]
STATUSES = ["Open - Pending Review", "Open - Under Investigation", "Closed - No Further Action", "Closed - Corrective Actions Implemented"]

# ==============================================================================
# 2. GENERATORS
# ==============================================================================

def get_random_date():
    return (datetime.now() - timedelta(days=random.randint(0, 60))).isoformat()

def get_random_time():
    return f"{random.randint(0, 23):02d}:{random.randint(0, 59):02d}"

def generate_flight_num():
    return f"PF-{random.randint(100, 999)}"

# --- ENTITY 1: BIRD STRIKES ---
def seed_bird_strikes(count=5):
    print(f"   🐦 Seeding {count} Bird Strikes...")
    for _ in range(count):
        dt = get_random_date()
        rid = f"BS-{dt[:10].replace('-', '')}-{random.randint(100,999)}"
        
        data = {
            "report_number": rid,
            "type": "Bird Strike",
            "date": dt,
            "time": get_random_time(),
            "time_of_day": random.choice(["Dawn", "Day", "Dusk", "Night"]),
            "reported_by": "Capt. Seed Data",
            "flight_number": generate_flight_num(),
            "aircraft_reg": random.choice(AIRCRAFT_REGS),
            "aircraft_type": "A320-200",
            "origin": random.choice(AIRPORTS),
            "destination": random.choice(AIRPORTS),
            "flight_phase": random.choice(FLIGHT_PHASES),
            "strike_location": random.choice(AIRPORTS),
            "altitude_agl": random.randint(0, 5000),
            "indicated_speed": random.randint(140, 250),
            "bird_species": random.choice(["Kite", "Pigeon", "Crow", "Unknown"]),
            "number_struck": random.randint(1, 5),
            "damage_level": random.choice(["None", "Minor", "Substantial"]),
            "parts_struck": ["Windshield", "Nose"] if random.random() > 0.5 else ["Engine"],
            "risk_level": random.choice(RISK_LEVELS),
            "status": random.choice(STATUSES),
            "narrative": "Bird strike encountered during flight phase.",
            "created_at": dt,
            "department": "Flight Operations"
        }
        supabase.table("bird_strikes").insert(data).execute()

# --- ENTITY 2: LASER STRIKES ---
def seed_laser_strikes(count=5):
    print(f"   🔴 Seeding {count} Laser Strikes...")
    for _ in range(count):
        dt = get_random_date()
        rid = f"LS-{dt[:10].replace('-', '')}-{random.randint(100,999)}"
        
        data = {
            "report_number": rid,
            "type": "Laser Strike",
            "date": dt,
            "time": get_random_time(),
            "flight_number": generate_flight_num(),
            "aircraft_reg": random.choice(AIRCRAFT_REGS),
            "location_description": f"{random.randint(3,10)}nm Final",
            "laser_color": random.choice(["Green", "Blue", "Red"]),
            "intensity": "High",
            "crew_effects": ["Distraction", "Glare"],
            "risk_level": random.choice(RISK_LEVELS),
            "status": random.choice(STATUSES),
            "narrative": "Laser illumination from ground source.",
            "created_at": dt,
            "department": "Flight Operations"
        }
        supabase.table("laser_strikes").insert(data).execute()

# --- ENTITY 3: TCAS REPORTS ---
def seed_tcas(count=5):
    print(f"   ✈️ Seeding {count} TCAS Reports...")
    for _ in range(count):
        dt = get_random_date()
        rid = f"TCAS-{dt[:10].replace('-', '')}-{random.randint(100,999)}"
        
        data = {
            "report_number": rid,
            "type": "TCAS Report",
            "date": dt,
            "time": get_random_time(),
            "flight_number": generate_flight_num(),
            "aircraft_reg": random.choice(AIRCRAFT_REGS),
            "tcas_alert_type": "RA - Climb",
            "ra_complied": "Yes - Fully",
            "vertical_separation": 400,
            "risk_level": "High",
            "status": random.choice(STATUSES),
            "narrative": "TCAS RA generated due to conflicting traffic.",
            "created_at": dt,
            "department": "Flight Operations"
        }
        supabase.table("tcas_reports").insert(data).execute()

# --- ENTITY 4: AIRCRAFT INCIDENTS ---
def seed_incidents(count=5):
    print(f"   ⚠️ Seeding {count} Incidents...")
    for _ in range(count):
        dt = get_random_date()
        rid = f"INC-{dt[:10].replace('-', '')}-{random.randint(100,999)}"
        
        data = {
            "report_number": rid,
            "type": "Aircraft Incident",
            "notification_type": "Incident",
            "date": dt,
            "time": get_random_time(),
            "flight_number": generate_flight_num(),
            "aircraft_reg": random.choice(AIRCRAFT_REGS),
            "incident_category": "Technical",
            "description": "Minor hydraulic leak detected.",
            "injuries": {"crew_fatal": 0, "pax_fatal": 0}, # Nested JSON required by app.py
            "risk_level": "Medium",
            "status": random.choice(STATUSES),
            "narrative": "Hydraulic system pressure fluctuation observed.",
            "created_at": dt,
            "department": "Safety Department"
        }
        supabase.table("aircraft_incidents").insert(data).execute()

# --- ENTITY 5: HAZARD REPORTS ---
def seed_hazards(count=5):
    print(f"   🔶 Seeding {count} Hazard Reports...")
    for _ in range(count):
        dt = get_random_date()
        rid = f"HAZ-{dt[:10].replace('-', '')}-{random.randint(100,999)}"
        
        data = {
            "report_number": rid,
            "type": "Hazard Report",
            "report_date": dt,
            "title": "FOD on Ramp",
            "hazard_category": "Ground Operations",
            "risk_level": "Low",
            "status": "Open",
            "description": "Loose plastic found on taxiway.",
            "likelihood": 3,
            "severity": "D",
            "created_at": dt,
            "department": "Ground Operations"
        }
        supabase.table("hazard_reports").insert(data).execute()

# --- ENTITY 6: FSR REPORTS (Complex JSON) ---
def seed_fsr(count=5):
    print(f"   📝 Seeding {count} Flight Service Reports...")
    for _ in range(count):
        dt = get_random_date()
        rid = f"FSR-{dt[:10].replace('-', '')}-{random.randint(100,999)}"
        
        data = {
            "id": rid,
            "type": "Flight Services Report",
            "date": dt,
            "flight_number": generate_flight_num(),
            "aircraft_reg": random.choice(AIRCRAFT_REGS),
            "origin": "OPKC",
            "destination": "OPLA",
            "ratings": {
                "boarding": 4, "catering": 3, "cleanliness": 5, 
                "ife": 2, "crew_service": 5, "overall": 4
            },
            "issues": ["Catering - Late delivery"],
            "complaints": 1,
            "risk_level": "Low",
            "status": "Closed",
            "created_at": dt,
            "department": "Cabin Services"
        }
        supabase.table("fsr_reports").insert(data).execute()

# --- ENTITY 7: CAPTAIN DEBRIEF (Complex JSON) ---
def seed_dbr(count=5):
    print(f"   👨‍✈️ Seeding {count} Captain Debriefs...")
    for _ in range(count):
        dt = get_random_date()
        rid = f"DBR-{dt[:10].replace('-', '')}-{random.randint(100,999)}"
        
        data = {
            "id": rid,
            "type": "Captain's Debrief",
            "date": dt,
            "flight_number": generate_flight_num(),
            "aircraft_reg": random.choice(AIRCRAFT_REGS),
            "times": {"off_blocks": "08:00", "takeoff": "08:15", "landing": "09:45", "on_blocks": "10:00"},
            "fuel": {"departure": 5000, "arrival": 2500, "burn": 2500},
            "weather": {"departure": "Clear", "arrival": "Haze"},
            "technical": {"issues": "No issues", "mel_items": "No"},
            "safety": {"observations": "Nil significant observations"},
            "overall_assessment": "Normal - Routine flight",
            "risk_level": "Low",
            "status": "Closed",
            "created_at": dt,
            "department": "Flight Operations"
        }
        supabase.table("captain_dbr").insert(data).execute()

# ==============================================================================
# EXECUTION
# ==============================================================================
if __name__ == "__main__":
    try:
        seed_bird_strikes(5)
        seed_laser_strikes(5)
        seed_tcas(5)
        seed_incidents(5)
        seed_hazards(5)
        seed_fsr(5)
        seed_dbr(5)
        print("\n✅ SEEDING COMPLETE! Refresh your dashboard.")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print("💡 Hint: Did you run the 'DROP TABLE' SQL script I gave you earlier?")
