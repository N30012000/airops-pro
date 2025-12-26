# seed_data.py
import os
import random
import uuid
import json
from datetime import datetime, timedelta, date
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Supabase
url = os.environ.get("SUPABASE_URL") or os.environ.get("SUPABASE_URL", "")
key = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_KEY", "")

if not url or not key:
    print("❌ Error: SUPABASE_URL or SUPABASE_KEY not found. Check your .env or secrets.")
    exit()

supabase: Client = create_client(url, key)

print("🚀 Initializing AirOps Pro Data Seeder...")

# ==============================================================================
# CONSTANTS & LOOKUPS (Mirrored from app.py for consistency)
# ==============================================================================

AIRPORTS = ["OPSK", "OPKC", "OPLA", "OPIS", "OPPS", "OPQT", "OPFA", "OPMT", "OMDB", "OMSJ", "OMAA", "OERK", "OEJN", "OTHH"]
AIRCRAFT_REGS = ["AP-BMA", "AP-BMB", "AP-BMC", "AP-BMD", "AP-BME", "AP-BMF", "AP-BMH", "AP-BMI", "AP-BMJ"]
DEPARTMENTS = ["Flight Operations", "Engineering", "Ground Operations", "Cabin Services", "Safety", "Security"]
FLIGHT_PHASES = ["Taxi Out", "Takeoff", "Climb", "Cruise", "Descent", "Approach", "Landing", "Taxi In"]
RISK_LEVELS = ["Low", "Medium", "High", "Extreme"]
STATUSES = ["Open", "Under Investigation", "Closed", "Pending Review", "Submitted"]

# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

def random_date(days_back=30):
    """Generate a random date within the last N days."""
    return (datetime.now() - timedelta(days=random.randint(0, days_back))).isoformat()

def random_time():
    """Generate a random time HH:MM."""
    return f"{random.randint(0, 23):02d}:{random.randint(0, 59):02d}"

def random_flight():
    return f"PF-{random.randint(100, 999)}"

def get_risk_matrix(risk_level):
    """Return realistic likelihood/severity for a given risk level."""
    if risk_level == "Extreme": return (5, "A")
    if risk_level == "High": return (4, "B")
    if risk_level == "Medium": return (3, "C")
    return (2, "D")

# ==============================================================================
# GENERATORS FOR EACH REPORT TYPE
# ==============================================================================

def seed_bird_strikes(count=5):
    print(f"\n🐦 Generating {count} Bird Strike Reports...")
    for _ in range(count):
        risk = random.choices(RISK_LEVELS, weights=[40, 30, 20, 10])[0]
        dt = random_date()
        rid = f"BS-{dt[:10].replace('-', '')}-{random.randint(100,999)}"
        
        data = {
            "report_number": rid,
            "type": "Bird Strike",
            "date": dt,
            "time": random_time(),
            "flight_number": random_flight(),
            "aircraft_reg": random.choice(AIRCRAFT_REGS),
            "origin": random.choice(AIRPORTS),
            "destination": random.choice(AIRPORTS),
            "flight_phase": random.choice(["Takeoff", "Approach", "Landing"]),
            "bird_species": random.choice(["Kite", "Crow", "Pigeon", "Unknown", "Eagle"]),
            "bird_size": random.choice(["Small", "Medium", "Large"]),
            "number_struck": random.randint(1, 10),
            "damage_level": "None" if risk == "Low" else "Minor" if risk == "Medium" else "Substantial",
            "risk_level": risk,
            "status": random.choice(STATUSES),
            "narrative": "Bird strike encountered during flight phase. Standard operating procedures followed.",
            "created_at": dt
        }
        try:
            supabase.table("bird_strikes").insert(data).execute()
            print(f"   ✅ Added {rid} ({risk})")
        except Exception as e:
            print(f"   ❌ Failed {rid}: {e}")

def seed_laser_strikes(count=5):
    print(f"\n🔦 Generating {count} Laser Strike Reports...")
    for _ in range(count):
        risk = random.choices(RISK_LEVELS, weights=[50, 30, 15, 5])[0]
        dt = random_date()
        rid = f"LS-{dt[:10].replace('-', '')}-{random.randint(100,999)}"
        
        data = {
            "report_number": rid,
            "type": "Laser Strike",
            "date": dt,
            "time": random_time(),
            "flight_number": random_flight(),
            "aircraft_reg": random.choice(AIRCRAFT_REGS),
            "location_description": f"{random.randint(3, 10)}nm Final",
            "laser_color": random.choice(["Green", "Blue", "Red"]),
            "intensity": "High" if risk in ["High", "Extreme"] else "Medium",
            "crew_effects": ["Distraction", "Glare"] if risk == "High" else ["None"],
            "risk_level": risk,
            "status": random.choice(STATUSES),
            "narrative": "Laser illumination observed from ground source. ATC notified.",
            "created_at": dt
        }
        try:
            supabase.table("laser_strikes").insert(data).execute()
            print(f"   ✅ Added {rid} ({risk})")
        except Exception as e:
            print(f"   ❌ Failed {rid}: {e}")

def seed_tcas_reports(count=5):
    print(f"\n✈️ Generating {count} TCAS Reports...")
    for _ in range(count):
        risk = random.choices(RISK_LEVELS, weights=[60, 20, 15, 5])[0]
        dt = random_date()
        rid = f"TCAS-{dt[:10].replace('-', '')}-{random.randint(100,999)}"
        alert = "RA - Climb" if risk in ["High", "Extreme"] else "TA Only"
        
        data = {
            "report_number": rid,
            "type": "TCAS Report",
            "date": dt,
            "time": random_time(),
            "flight_number": random_flight(),
            "aircraft_reg": random.choice(AIRCRAFT_REGS),
            "altitude_fl": random.randint(100, 380) * 100,
            "tcas_alert_type": alert,
            "ra_complied": "Yes" if "RA" in alert else "N/A",
            "risk_level": risk,
            "status": random.choice(STATUSES),
            "narrative": f"Received {alert}. Traffic visually acquired. Clear of conflict.",
            "created_at": dt
        }
        try:
            supabase.table("tcas_reports").insert(data).execute()
            print(f"   ✅ Added {rid} ({risk})")
        except Exception as e:
            print(f"   ❌ Failed {rid}: {e}")

def seed_incidents(count=5):
    print(f"\n🔶 Generating {count} Aircraft Incidents...")
    for _ in range(count):
        risk = random.choices(RISK_LEVELS, weights=[30, 40, 20, 10])[0]
        dt = random_date()
        rid = f"INC-{dt[:10].replace('-', '')}-{random.randint(100,999)}"
        
        data = {
            "report_number": rid,
            "type": "Aircraft Incident",
            "notification_type": "Accident" if risk == "Extreme" else "Incident",
            "date": dt,
            "time": random_time(),
            "flight_number": random_flight(),
            "aircraft_reg": random.choice(AIRCRAFT_REGS),
            "incident_category": random.choice(INCIDENT_CATEGORIES),
            "risk_level": risk,
            "status": random.choice(STATUSES),
            "description": "Operational irregularity encountered. Investigation initiated.",
            "narrative": "Detailed narrative of the event goes here...",
            "created_at": dt
        }
        try:
            supabase.table("aircraft_incidents").insert(data).execute()
            print(f"   ✅ Added {rid} ({risk})")
        except Exception as e:
            print(f"   ❌ Failed {rid}: {e}")

def seed_hazards(count=5):
    print(f"\n📝 Generating {count} Hazard Reports...")
    for _ in range(count):
        risk = random.choices(RISK_LEVELS, weights=[50, 30, 15, 5])[0]
        dt = random_date()
        rid = f"HAZ-{dt[:10].replace('-', '')}-{random.randint(100,999)}"
        
        data = {
            "report_number": rid,
            "type": "Hazard Report",
            "title": f"Hazard: {random.choice(['FOD on Ramp', 'Lighting Issue', 'Procedural Gap', 'Equipment Failure'])}",
            "hazard_category": random.choice(HAZARD_CATEGORIES),
            "risk_level": risk,
            "status": random.choice(STATUSES),
            "description": "Observed potential hazard during routine operations.",
            "created_at": dt
        }
        try:
            supabase.table("hazard_reports").insert(data).execute()
            print(f"   ✅ Added {rid} ({risk})")
        except Exception as e:
            print(f"   ❌ Failed {rid}: {e}")

def seed_fsr_reports(count=5):
    print(f"\n👨‍✈️ Generating {count} Flight Services Reports (FSR)...")
    for _ in range(count):
        risk = "Low" # Mostly operational/quality
        dt = random_date()
        rid = f"FSR-{dt[:10].replace('-', '')}-{random.randint(100,999)}"
        
        # JSON Ratings
        ratings = {
            "catering": random.randint(1,5),
            "cleanliness": random.randint(1,5),
            "crew": random.randint(3,5)
        }
        
        data = {
            "id": rid, # Note: FSR uses 'id' as column in app.py logic
            "type": "Flight Services Report",
            "date": dt,
            "flight_number": random_flight(),
            "aircraft_reg": random.choice(AIRCRAFT_REGS),
            "ratings": ratings,
            "issues": random.choice([["Catering Delay"], ["Cleaning Issue"], ["None"]]),
            "risk_level": risk,
            "status": random.choice(["Open", "Closed"]),
            "remarks": "Routine flight report.",
            "created_at": dt
        }
        try:
            supabase.table("fsr_reports").insert(data).execute()
            print(f"   ✅ Added {rid}")
        except Exception as e:
            print(f"   ❌ Failed {rid}: {e}")

def seed_captain_debriefs(count=5):
    print(f"\n👨‍✈️ Generating {count} Captain's Debriefs (DBR)...")
    for _ in range(count):
        risk = random.choices(["Low", "Medium"], weights=[80, 20])[0]
        dt = random_date()
        rid = f"DBR-{dt[:10].replace('-', '')}-{random.randint(100,999)}"
        
        data = {
            "id": rid, # Note: DBR uses 'id' as column in app.py logic
            "type": "Captain's Debrief",
            "date": dt,
            "flight_number": random_flight(),
            "aircraft_reg": random.choice(AIRCRAFT_REGS),
            "overall_assessment": random.choice(["Normal", "Minor Issues", "Uneventful"]),
            "risk_level": risk,
            "status": "Closed",
            "safety": {"observations": "Nil significant observations."},
            "created_at": dt
        }
        try:
            supabase.table("captain_dbr").insert(data).execute()
            print(f"   ✅ Added {rid}")
        except Exception as e:
            print(f"   ❌ Failed {rid}: {e}")

# ==============================================================================
# MAIN EXECUTION
# ==============================================================================

# Categories for context
INCIDENT_CATEGORIES = ["Ground Handling", "Technical", "Weather", "Security", "Operations"]
HAZARD_CATEGORIES = ["FOD", "Equipment", "Environment", "Procedure", "Personnel"]

if __name__ == "__main__":
    print("--- Starting Bulk Seed ---")
    seed_bird_strikes(5)
    seed_laser_strikes(5)
    seed_tcas_reports(5)
    seed_incidents(5)
    seed_hazards(5)
    seed_fsr_reports(5)
    seed_captain_debriefs(5)
    print("\n🎉 All dummy data generated successfully!")
    print("👉 Refresh your Dashboard to see the new metrics.")
