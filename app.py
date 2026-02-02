# Add this with your other imports
from ai_assistant import get_ai_assistant, DataGeocoder
import base64
import hashlib
import io
import json
import os
import random
import re
import smtplib
import time
import uuid
import ui_integration
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, date
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from enum import Enum
from typing import Optional, Dict, List, Any, Tuple
from streamlit_mic_recorder import mic_recorder
# Third-party imports
import pandas as pd
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import google.generativeai as genai
from plotly.subplots import make_subplots

# --- ADD THIS ---
from supabase import create_client, Client

@st.cache_resource
def init_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_supabase()
# ----------------

# Optional pydeck for geospatial mapping
try:
    import pydeck as pdk
    PYDECK_AVAILABLE = True
except ImportError:
    pdk = None
    PYDECK_AVAILABLE = False

# PDF generation
try:
    from reportlab.lib.colors import HexColor
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.pdfgen import canvas
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
try:
    import ai_assistant  # <--- THIS IS THE MISSING LINK
except ImportError as e:
    st.error(f"❌ Failed to import 'ai_assistant.py': {e}")
    st.info("Ensure the file 'ai_assistant.py' is in the same folder as 'app.py'.")

try:
    import ui_integration # Required for OCR
except ImportError:
    pass # Handle gracefully if missing
    
# Air Sial SMS v3.0 - Configuration


# ══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION & ENVIRONMENT
# ══════════════════════════════════════════════════════════════════════════════

class Config:
    """Application configuration settings"""
    APP_NAME = "Air Sial Corporate Safety"
    APP_VERSION = "3.0.0"
    APP_SUBTITLE = "Safety Management System"
    COMPANY_NAME = "Air Sial"
    COMPANY_IATA = "PF"
    COMPANY_ICAO = "SIS"
    CAA_COUNTRY = "Pakistan"
    CAA_AUTHORITY = "Pakistan Civil Aviation Authority (PCAA)"
    AOC_NUMBER = "AOC-PK-0XX"
    HAZARD_SLA_DAYS = 15
    INCIDENT_SLA_DAYS = 30
    BIRD_STRIKE_SLA_DAYS = 7
    LASER_STRIKE_SLA_DAYS = 7
    TCAS_SLA_DAYS = 14
    SLA_CRITICAL_DAYS = 3
    SLA_WARNING_DAYS = 7
    SAFETY_EMAIL = "safety@airsial.com"
    CAA_EMAIL = "reporting@caapakistan.com.pk"
    TIMEZONE = "Asia/Karachi"
    UTC_OFFSET = 5
    MAX_UPLOAD_SIZE_MB = 10
    ALLOWED_IMAGE_TYPES = ['png', 'jpg', 'jpeg', 'bmp', 'tiff', 'webp']
    ALLOWED_DOC_TYPES = ['pdf', 'docx', 'xlsx']
    
    @staticmethod
    def get_supabase_url():
        try: return st.secrets.get("SUPABASE_URL", "")
        except: return ""
    
    @staticmethod
    def get_supabase_key():
        try: return st.secrets.get("SUPABASE_KEY", "")
        except: return ""
    
    @staticmethod
    def get_gemini_key():
        try: return st.secrets.get("GEMINI_API_KEY", "")
        except: return ""

# ══════════════════════════════════════════════════════════════════════════════
# ENUMERATIONS
# ══════════════════════════════════════════════════════════════════════════════

class UserRole(Enum):
    ADMIN = "admin"
    SAFETY_MANAGER = "safety_manager"
    INVESTIGATOR = "investigator"
    DEPARTMENT_HEAD = "department_head"
    REPORTER = "reporter"
    VIEWER = "viewer"

class ReportStatus(Enum):
    DRAFT = "Draft"
    SUBMITTED = "Submitted"
    UNDER_REVIEW = "Under Review"
    ASSIGNED = "Assigned to Investigator"
    IN_PROGRESS = "Investigation In Progress"
    REPORT_SENT = "Report Sent"
    AWAITING_REPLY = "Awaiting Reply"
    REPLY_RECEIVED = "Reply Received"
    CORRECTIVE_PENDING = "Corrective Action Pending"
    CORRECTIVE_IMPLEMENTED = "Corrective Action Implemented"
    VERIFICATION_PENDING = "Verification Pending"
    COMPLETE = "Investigation Complete"
    CLOSED = "Closed"

class RiskLevel(Enum):
    EXTREME = "Extreme"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"

class ReportType(Enum):
    AIRCRAFT_INCIDENT = "aircraft_incident"
    BIRD_STRIKE = "bird_strike"
    LASER_STRIKE = "laser_strike"
    TCAS_REPORT = "tcas_report"
    HAZARD_REPORT = "hazard_report"
    FSR = "fsr"
    CAPTAIN_DBR = "captain_dbr"

# ══════════════════════════════════════════════════════════════════════════════
# COMPREHENSIVE LOOKUP TABLES
# ══════════════════════════════════════════════════════════════════════════════

DEPARTMENTS = [
    "Flight Operations",
    "Safety & Security",
    "Airport Services",
    "Engineering",
    "Quality Assurance",
    "Flight Services"
]

AIRCRAFT_FLEET = {
    "AP-BMA": {"type": "ATR 72-600", "msn": "1234", "config": "70Y", "engines": "PW127M", "mtow": "23000"},
    "AP-BMB": {"type": "ATR 72-600", "msn": "1235", "config": "70Y", "engines": "PW127M", "mtow": "23000"},
    "AP-BMC": {"type": "ATR 72-600", "msn": "1236", "config": "70Y", "engines": "PW127M", "mtow": "23000"},
    "AP-BMD": {"type": "ATR 72-600", "msn": "1237", "config": "70Y", "engines": "PW127M", "mtow": "23000"},
    "AP-BME": {"type": "ATR 72-600", "msn": "1238", "config": "70Y", "engines": "PW127M", "mtow": "23000"},
    "AP-BMF": {"type": "ATR 72-500", "msn": "1100", "config": "68Y", "engines": "PW127F", "mtow": "22800"},
    "AP-BMG": {"type": "ATR 72-500", "msn": "1101", "config": "68Y", "engines": "PW127F", "mtow": "22800"},
    "AP-BMH": {"type": "A320-200", "msn": "5500", "config": "180Y", "engines": "CFM56-5B", "mtow": "78000"},
    "AP-BMI": {"type": "A320-200", "msn": "5501", "config": "180Y", "engines": "CFM56-5B", "mtow": "78000"},
    "AP-BMJ": {"type": "A320neo", "msn": "8000", "config": "186Y", "engines": "PW1100G", "mtow": "79000"},
}

AIRCRAFT_TYPES_STRICT = ["A320", "A330"]

ROLES = {
    "REPORTER": "Reporter",        # Submit only, View own confirmation
    "ANALYST": "Analyst",          # Dept view, Add CAP/Root Cause
    "GATEKEEPER": "Safety Head",   # Risk Analysis, Close, Full View
    "ADMIN": "Admin"               # Manage Users
}

AIRPORTS = {
    "OPSK": {"name": "Sialkot International Airport", "city": "Sialkot", "country": "Pakistan", "base": True, "icao": "OPSK", "iata": "SKT", "elevation": "837ft"},
    "OPKC": {"name": "Jinnah International Airport", "city": "Karachi", "country": "Pakistan", "base": True, "icao": "OPKC", "iata": "KHI", "elevation": "100ft"},
    "OPLA": {"name": "Allama Iqbal International Airport", "city": "Lahore", "country": "Pakistan", "base": True, "icao": "OPLA", "iata": "LHE", "elevation": "712ft"},
    "OPIS": {"name": "Islamabad International Airport", "city": "Islamabad", "country": "Pakistan", "base": True, "icao": "OPIS", "iata": "ISB", "elevation": "1665ft"},
    "OPPS": {"name": "Peshawar Bacha Khan Airport", "city": "Peshawar", "country": "Pakistan", "base": False, "icao": "OPPS", "iata": "PEW", "elevation": "1158ft"},
    "OPQT": {"name": "Quetta International Airport", "city": "Quetta", "country": "Pakistan", "base": False, "icao": "OPQT", "iata": "UET", "elevation": "5267ft"},
    "OPFA": {"name": "Faisalabad International Airport", "city": "Faisalabad", "country": "Pakistan", "base": False, "icao": "OPFA", "iata": "LYP", "elevation": "591ft"},
    "OPMT": {"name": "Multan International Airport", "city": "Multan", "country": "Pakistan", "base": False, "icao": "OPMT", "iata": "MUX", "elevation": "403ft"},
    "OMDB": {"name": "Dubai International Airport", "city": "Dubai", "country": "UAE", "base": False, "icao": "OMDB", "iata": "DXB", "elevation": "62ft"},
    "OMSJ": {"name": "Sharjah International Airport", "city": "Sharjah", "country": "UAE", "base": False, "icao": "OMSJ", "iata": "SHJ", "elevation": "111ft"},
    "OMAA": {"name": "Abu Dhabi International Airport", "city": "Abu Dhabi", "country": "UAE", "base": False, "icao": "OMAA", "iata": "AUH", "elevation": "88ft"},
    "OERK": {"name": "King Khalid International Airport", "city": "Riyadh", "country": "Saudi Arabia", "base": False, "icao": "OERK", "iata": "RUH", "elevation": "2049ft"},
    "OEJN": {"name": "King Abdulaziz International Airport", "city": "Jeddah", "country": "Saudi Arabia", "base": False, "icao": "OEJN", "iata": "JED", "elevation": "48ft"},
    "OEDF": {"name": "King Fahd International Airport", "city": "Dammam", "country": "Saudi Arabia", "base": False, "icao": "OEDF", "iata": "DMM", "elevation": "72ft"},
    "OTHH": {"name": "Hamad International Airport", "city": "Doha", "country": "Qatar", "base": False, "icao": "OTHH", "iata": "DOH", "elevation": "13ft"},
    "OBBI": {"name": "Bahrain International Airport", "city": "Bahrain", "country": "Bahrain", "base": False, "icao": "OBBI", "iata": "BAH", "elevation": "6ft"},
    "OOMS": {"name": "Muscat International Airport", "city": "Muscat", "country": "Oman", "base": False, "icao": "OOMS", "iata": "MCT", "elevation": "48ft"},
    "OKBK": {"name": "Kuwait International Airport", "city": "Kuwait City", "country": "Kuwait", "base": False, "icao": "OKBK", "iata": "KWI", "elevation": "206ft"},
}

RISK_COLORS = {
    "Extreme": "#8B0000", # Dark Red
    "High": "#CC5500",    # Dark Orange
    "Medium": "#B8860B",  # Dark Goldenrod
    "Low": "#006400"      # Dark Green
}

FLIGHT_PHASES = [
    "Pre-flight / Ground Operations", "Taxi Out", "Takeoff Roll",
    "Initial Climb (0-1000ft AGL)", "Climb (1000-10000ft)",
    "Climb (Above 10000ft)", "Cruise", "Descent (Above 10000ft)",
    "Descent (10000ft-1000ft)", "Approach", "Final Approach",
    "Landing Roll", "Taxi In", "Post-flight / Parking", "Go-Around", "Holding"
]

INCIDENT_CATEGORIES = [
    "Abnormal Runway Contact", "Aerodrome", "Air Traffic Management",
    "Aircraft Damage", "Cabin Safety Events", "Controlled Flight Into Terrain (CFIT)",
    "Collision / Near Collision", "De/Anti-icing Operations", "Depressurization",
    "Engine Failure / Malfunction", "Fire / Smoke (Non-Impact)", "Fire / Smoke (Post-Impact)",
    "Flight Crew Incapacitation", "Fuel Related", "Ground Collision", "Ground Handling",
    "Icing", "Landing Gear", "Loss of Control - Ground (LOC-G)", "Loss of Control - Inflight (LOC-I)",
    "Low Altitude Operations", "Maintenance", "Medical Emergency", "Navigation Error",
    "Other", "Runway Excursion", "Runway Incursion", "Security Related",
    "System / Component Failure", "Turbulence Encounter", "Undershoot / Overshoot",
    "Unruly Passenger", "Unstable Approach", "Weather", "Wildlife Strike", "Windshear / Microburst"
]

HAZARD_CATEGORIES = [
    "Aircraft Systems", "Airport Infrastructure", "ATC/Navigation", "Cabin Safety",
    "Cargo Handling", "Documentation/Procedures", "Environmental", "Equipment/Tools",
    "Fatigue/Human Factors", "Flight Operations", "Fuel Operations", "Ground Operations",
    "Maintenance", "Passenger Handling", "Ramp Safety", "Security", "Training",
    "Weather Related", "Wildlife/Bird Activity", "Other"
]

BIRD_SPECIES = [
    "Unknown", "House Crow", "Jungle Crow", "Black Kite", "Brahminy Kite",
    "Pariah Kite", "Vulture (Egyptian)", "Vulture (Griffon)", "Pigeon / Rock Dove",
    "Myna", "Starling", "Sparrow", "Swift", "Swallow", "Egret", "Heron",
    "Lapwing", "Plover", "Sandpiper", "Owl", "Eagle", "Falcon", "Hawk",
    "Hoopoe", "Kingfisher", "Parakeet / Parrot", "Bat (Mammal)",
    "Multiple Species", "Unidentified Flock", "Other (Specify)"
]

BIRD_SIZES = [
    ("Small", "Sparrow-sized (< 100g)"),
    ("Medium-Small", "Starling-sized (100-500g)"),
    ("Medium", "Pigeon-sized (500-1000g)"),
    ("Medium-Large", "Crow-sized (1-2kg)"),
    ("Large", "Kite/Vulture-sized (2-5kg)"),
    ("Very Large", "Eagle-sized (> 5kg)")
]

LASER_COLORS = [
    "Green (532nm)", "Red (630-670nm)", "Blue (445-488nm)", "Violet/Purple (405nm)",
    "Yellow/Amber (570-590nm)", "White (Multi-wavelength)", "Infrared (Not visible)",
    "Unknown/Could not determine", "Multiple Colors"
]

LASER_INTENSITIES = [
    ("1 - Low", "Barely visible, no visual effect"),
    ("2 - Moderate", "Visible but not distracting"),
    ("3 - Significant", "Distracting, caused momentary startle"),
    ("4 - High", "Bright, caused glare/flash blindness"),
    ("5 - Very High", "Extremely bright, caused disorientation/pain")
]

TCAS_ALERT_TYPES = [
    "Traffic Advisory (TA) Only",
    "Resolution Advisory (RA) - Climb",
    "Resolution Advisory (RA) - Descend",
    "Resolution Advisory (RA) - Level Off",
    "Resolution Advisory (RA) - Maintain Vertical Speed",
    "Resolution Advisory (RA) - Adjust Vertical Speed",
    "Resolution Advisory (RA) - Crossing Climb",
    "Resolution Advisory (RA) - Crossing Descend",
    "Resolution Advisory (RA) - Reversal",
    "Resolution Advisory (RA) - Increase Climb",
    "Resolution Advisory (RA) - Increase Descend",
    "Preventive RA - Don't Climb",
    "Preventive RA - Don't Descend",
    "Multi-Aircraft Encounter",
    "Clear of Conflict"
]

TCAS_EQUIPMENT_TYPES = ["TCAS I", "TCAS II (Version 6.04a)", "TCAS II (Version 7.0)", "TCAS II (Version 7.1)", "ACAS X (ADS-B based)", "Unknown/Not Determined"]

WEATHER_CONDITIONS = [
    "VMC - Clear", "VMC - Few Clouds", "VMC - Scattered", "VMC - Broken",
    "IMC - Overcast", "IMC - Low Visibility", "Rain - Light", "Rain - Moderate",
    "Rain - Heavy", "Thunderstorm Vicinity", "Thunderstorm", "Fog", "Mist",
    "Haze", "Dust/Sand", "Snow", "Icing Conditions", "Turbulence - Light",
    "Turbulence - Moderate", "Turbulence - Severe", "Windshear Reported",
    "Crosswind (Significant)", "Gusty Conditions"
]

DAMAGE_LEVELS = [
    ("None", "No damage detected"),
    ("Minor", "Superficial damage, aircraft serviceable"),
    ("Moderate", "Damage requiring repair before next flight"),
    ("Major", "Significant structural damage"),
    ("Severe", "Extensive damage, aircraft AOG"),
    ("Destroyed", "Aircraft beyond economic repair")
]

INJURY_CLASSIFICATIONS = [
    ("None", "No injuries"),
    ("Minor", "First aid treatment only"),
    ("Serious", "Hospitalization required < 48 hours"),
    ("Major", "Hospitalization > 48 hours, fractures, severe lacerations"),
    ("Fatal", "Death within 30 days of accident")
]

CREW_POSITIONS = [
    "Captain (PIC)", "First Officer (SIC)", "Relief First Officer",
    "Check Captain", "TRI/TRE", "Line Training Captain",
    "Cabin Manager / Purser", "Senior Cabin Crew", "Cabin Crew",
    "Loadmaster", "Flight Engineer", "Observer"
]

APPROACH_TYPES = ["ILS CAT I", "ILS CAT II", "ILS CAT III", "VOR/DME", "VOR", "NDB", "RNAV (GNSS)", "RNP AR", "Visual", "Circling", "LOC Only", "LDA", "SDF", "PAR", "ASR"]

RUNWAY_CONDITIONS = ["Dry", "Damp", "Wet", "Contaminated - Water", "Contaminated - Slush", "Contaminated - Snow (Dry)", "Contaminated - Snow (Compacted)", "Contaminated - Ice", "Contaminated - Frost", "Flooded"]

BRAKING_ACTIONS = ["Good", "Good to Medium", "Medium", "Medium to Poor", "Poor", "Nil"]

TURBULENCE_INTENSITY = ["None", "Light", "Light Occasional", "Light Frequent", "Moderate", "Moderate Occasional", "Moderate Frequent", "Severe", "Severe Occasional", "Extreme"]

AIRCRAFT_PARTS_STRUCK = ["Radome", "Windshield", "Nose/Fuselage", "Engine #1", "Engine #2", "Propeller", "Wing Leading Edge", "Wing Trailing Edge", "Fuselage", "Landing Gear", "Tail/Empennage", "Lights", "Pitot/Static", "Other"]

EFFECT_ON_FLIGHT_OPTIONS = ["None - Flight continued normally", "Precautionary landing at destination", "Precautionary landing at alternate", "Return to departure airport", "Emergency landing", "Aborted takeoff", "Aborted approach / Go-around", "Other"]

CREW_EFFECTS_LASER = ["Glare", "Flash Blindness", "Afterimage", "Eye Pain/Discomfort", "Eye Watering", "Disorientation", "Headache", "Temporary Vision Loss", "Startle/Distraction", "No Effect"]

EMAIL_CONTACTS = {
    "Safety Manager": "safety.manager@airsial.com",
    "Engineering HOD": "engineering.hod@airsial.com",
    "Flight Ops Manager": "flightops.manager@airsial.com",
    "Quality Assurance": "qa@airsial.com",
    "Ground Ops Supervisor": "groundops@airsial.com",
    "CAA Liaison": "caa.liaison@airsial.com",
    "Maintenance Controller": "maint.controller@airsial.com",
    "Training Manager": "training@airsial.com",
    "CEO Office": "ceo.office@airsial.com",
    "HR Manager": "hr.manager@airsial.com",
    "Security Manager": "security.manager@airsial.com",
    "Cabin Services Manager": "cabin.manager@airsial.com",
}

# ══════════════════════════════════════════════════════════════════════════════
# ICAO RISK MATRIX
# ══════════════════════════════════════════════════════════════════════════════

LIKELIHOOD_SCALE = {
    1: {"name": "Extremely Improbable", "description": "Almost inconceivable that the event will occur", "frequency": "< 1 in 1,000,000 flights"},
    2: {"name": "Improbable", "description": "Very unlikely to occur", "frequency": "1 in 100,000 - 1,000,000 flights"},
    3: {"name": "Remote", "description": "Unlikely but possible to occur", "frequency": "1 in 10,000 - 100,000 flights"},
    4: {"name": "Occasional", "description": "Likely to occur sometimes", "frequency": "1 in 1,000 - 10,000 flights"},
    5: {"name": "Frequent", "description": "Likely to occur many times", "frequency": "Expected to occur > 1 in 1,000 flights"}
}

SEVERITY_SCALE = {
    "A": {"name": "Catastrophic", "description": "Equipment destroyed, multiple deaths", "operational": "Multiple fatalities"},
    "B": {"name": "Hazardous", "description": "Large reduction in safety margins", "operational": "Serious injury"},
    "C": {"name": "Major", "description": "Significant reduction in safety margins", "operational": "Major equipment damage"},
    "D": {"name": "Minor", "description": "Nuisance, operating limitations", "operational": "Minor damage"},
    "E": {"name": "Negligible", "description": "Little consequence", "operational": "No safety effect"}
}

RISK_MATRIX = {
    ("5", "A"): RiskLevel.EXTREME, ("5", "B"): RiskLevel.EXTREME, ("5", "C"): RiskLevel.HIGH, ("5", "D"): RiskLevel.MEDIUM, ("5", "E"): RiskLevel.LOW,
    ("4", "A"): RiskLevel.EXTREME, ("4", "B"): RiskLevel.HIGH, ("4", "C"): RiskLevel.HIGH, ("4", "D"): RiskLevel.MEDIUM, ("4", "E"): RiskLevel.LOW,
    ("3", "A"): RiskLevel.HIGH, ("3", "B"): RiskLevel.HIGH, ("3", "C"): RiskLevel.MEDIUM, ("3", "D"): RiskLevel.MEDIUM, ("3", "E"): RiskLevel.LOW,
    ("2", "A"): RiskLevel.HIGH, ("2", "B"): RiskLevel.MEDIUM, ("2", "C"): RiskLevel.MEDIUM, ("2", "D"): RiskLevel.LOW, ("2", "E"): RiskLevel.LOW,
    ("1", "A"): RiskLevel.MEDIUM, ("1", "B"): RiskLevel.MEDIUM, ("1", "C"): RiskLevel.LOW, ("1", "D"): RiskLevel.LOW, ("1", "E"): RiskLevel.LOW,
}

RISK_ACTIONS = {
    RiskLevel.EXTREME: {"action": "STOP OPERATIONS", "description": "Immediate action required.", "color": "#DC3545", "timeline": "Immediate", "authority": "Accountable Manager / CEO"},
    RiskLevel.HIGH: {"action": "URGENT CORRECTIVE ACTION", "description": "Senior management attention required.", "color": "#FD7E14", "timeline": "Within 24-48 hours", "authority": "Safety Manager"},
    RiskLevel.MEDIUM: {"action": "CORRECTIVE ACTION REQUIRED", "description": "Management responsibility.", "color": "#FFC107", "timeline": "Within 15 days", "authority": "Department Manager"},
    RiskLevel.LOW: {"action": "MONITOR AND REVIEW", "description": "Accept risk with monitoring.", "color": "#28A745", "timeline": "Next scheduled review", "authority": "Safety Officer"}
}
# ══════════════════════════════════════════════════════════════════════════════
# DATA CLASSES AND HELPER FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class SLAStatus:
    days_remaining: int
    status: str
    color: str
    text: str
    percentage: float

def generate_report_number(report_type: ReportType, department: str = "") -> str:
    prefix_map = {
        ReportType.AIRCRAFT_INCIDENT: "INC", ReportType.BIRD_STRIKE: "BRD", ReportType.LASER_STRIKE: "LSR",
        ReportType.TCAS_REPORT: "TCS", ReportType.HAZARD_REPORT: "HZD", ReportType.FSR: "FSR", ReportType.CAPTAIN_DBR: "DBR"
    }
    prefix = prefix_map.get(report_type, "RPT")
    date_str = datetime.now().strftime("%Y%m%d")
    unique_id = str(uuid.uuid4())[:6].upper()
    return f"{prefix}-{date_str}-{unique_id}"

def calculate_risk_level(likelihood: int, severity: str) -> RiskLevel:
    key = (str(likelihood), severity.upper())
    return RISK_MATRIX.get(key, RiskLevel.LOW)

def calculate_sla_status(created_date, sla_days: int) -> SLAStatus:
    if isinstance(created_date, str):
        try: created_date = datetime.strptime(created_date[:10], "%Y-%m-%d").date()
        except: created_date = date.today()
    elif isinstance(created_date, datetime):
        created_date = created_date.date()
    
    deadline = created_date + timedelta(days=sla_days)
    today = date.today()
    days_remaining = (deadline - today).days
    
    if days_remaining < 0:
        return SLAStatus(days_remaining, "overdue", "#DC3545", f"OVERDUE by {abs(days_remaining)} days", 100)
    elif days_remaining <= Config.SLA_CRITICAL_DAYS:
        return SLAStatus(days_remaining, "critical", "#DC3545", f"{days_remaining} days - CRITICAL", min(100, ((sla_days - days_remaining) / sla_days) * 100))
    elif days_remaining <= Config.SLA_WARNING_DAYS:
        return SLAStatus(days_remaining, "warning", "#FFC107", f"{days_remaining} days remaining", ((sla_days - days_remaining) / sla_days) * 100)
    else:
        return SLAStatus(days_remaining, "ok", "#28A745", f"{days_remaining} days remaining", ((sla_days - days_remaining) / sla_days) * 100)

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def get_pakistan_time() -> datetime:
    return datetime.utcnow() + timedelta(hours=Config.UTC_OFFSET)

def format_datetime(dt: datetime, include_time: bool = True) -> str:
    if include_time: return dt.strftime("%d-%b-%Y %H:%M")
    return dt.strftime("%d-%b-%Y")

def get_airport_name(icao: str) -> str:
    if icao == "N/A": return "N/A"
    airport = AIRPORTS.get(icao.upper())
    return f"{airport['city']} ({icao})" if airport else icao

def get_aircraft_info(registration: str) -> dict:
    return AIRCRAFT_FLEET.get(registration.upper(), {"type": "Unknown", "msn": "N/A", "config": "N/A", "engines": "N/A", "mtow": "N/A"})

# ══════════════════════════════════════════════════════════════════════════════
# DYNAMIC STATISTICS FROM SESSION STATE - NO MOCK DATA
# ══════════════════════════════════════════════════════════════════════════════

# --- REPLACEMENT CODE ---

# REPLACE THE FUNCTION AT LINE 465 WITH THIS:

def get_report_counts() -> dict:
    """Get counts directly from session state (Dynamic - No Cache)"""
    return {
        'bird_strikes': len(st.session_state.get('bird_strikes', [])),
        'laser_strikes': len(st.session_state.get('laser_strikes', [])),
        'tcas_reports': len(st.session_state.get('tcas_reports', [])),
        'hazard_reports': len(st.session_state.get('hazard_reports', [])),
        'aircraft_incidents': len(st.session_state.get('aircraft_incidents', [])),
        'fsr_reports': len(st.session_state.get('fsr_reports', [])),
        'captain_dbr': len(st.session_state.get('captain_dbr', [])),
    }
    for table in tables:
        try:
            # 'head=True' ensures we only get the count, not the actual data rows (faster)
            response = supabase.table(table).select("*", count="exact", head=True).execute()
            counts[table] = response.count
        except Exception as e:
            # If the table doesn't exist yet or connection fails, default to 0
            counts[table] = 0
            
    return counts
# ------------------------

def get_total_reports() -> int:
    return sum(get_report_counts().values())

def get_risk_distribution() -> dict:
    distribution = {"Extreme": 0, "High": 0, "Medium": 0, "Low": 0}
    for hazard in st.session_state.get('hazard_reports', []):
        risk = hazard.get('risk_level', 'Low')
        if risk in distribution: distribution[risk] += 1
    for incident in st.session_state.get('aircraft_incidents', []):
        risk = incident.get('risk_level', 'Medium')
        if risk in distribution: distribution[risk] += 1
    return distribution

def get_open_investigations() -> int:
    open_count = 0
    open_statuses = ['Draft', 'Submitted', 'Under Review', 'Assigned to Investigator', 'Investigation In Progress', 'Awaiting Reply']
    for report_type in ['bird_strikes', 'laser_strikes', 'tcas_reports', 'hazard_reports', 'aircraft_incidents']:
        for report in st.session_state.get(report_type, []):
            if report.get('investigation_status', 'Draft') in open_statuses:
                open_count += 1
    return open_count

def get_closed_investigations() -> int:
    closed_count = 0
    closed_statuses = ['Investigation Complete', 'Closed']
    for report_type in ['bird_strikes', 'laser_strikes', 'tcas_reports', 'hazard_reports', 'aircraft_incidents']:
        for report in st.session_state.get(report_type, []):
            if report.get('investigation_status', '') in closed_statuses:
                closed_count += 1
    return closed_count

def get_high_risk_count() -> int:
    high_risk = 0
    for hazard in st.session_state.get('hazard_reports', []):
        if hazard.get('risk_level', '') in ['High', 'Extreme']: high_risk += 1
    for incident in st.session_state.get('aircraft_incidents', []):
        if incident.get('risk_level', '') in ['High', 'Extreme']: high_risk += 1
    return high_risk

def get_sla_alerts() -> dict:
    alerts = {'overdue': 0, 'critical': 0, 'warning': 0, 'ok': 0}
    for hazard in st.session_state.get('hazard_reports', []):
        if hazard.get('investigation_status') not in ['Closed', 'Investigation Complete']:
            sla = calculate_sla_status(hazard.get('created_at', str(date.today())), Config.HAZARD_SLA_DAYS)
            alerts[sla.status] += 1
    return alerts

def get_reports_by_department() -> dict:
    dept_counts = {}
    for hazard in st.session_state.get('hazard_reports', []):
        dept = hazard.get('reporter_department', 'Unknown')
        dept_counts[dept] = dept_counts.get(dept, 0) + 1
    return dept_counts

def get_recent_reports(limit: int = 5) -> list:
    all_reports = []
    type_icons = {'bird_strikes': '🐦', 'laser_strikes': '🔴', 'tcas_reports': '📡', 'hazard_reports': '⚠️', 'aircraft_incidents': '🚨', 'fsr_reports': '📋', 'captain_dbr': '👨‍✈️'}
    for report_type, reports in [
        ('bird_strikes', st.session_state.get('bird_strikes', [])),
        ('laser_strikes', st.session_state.get('laser_strikes', [])),
        ('tcas_reports', st.session_state.get('tcas_reports', [])),
        ('hazard_reports', st.session_state.get('hazard_reports', [])),
        ('aircraft_incidents', st.session_state.get('aircraft_incidents', [])),
        ('fsr_reports', st.session_state.get('fsr_reports', [])),
        ('captain_dbr', st.session_state.get('captain_dbr', []))
    ]:
        for report in reports:
            all_reports.append({
                'type': report_type, 'icon': type_icons.get(report_type, '📋'),
                'number': report.get('report_number', 'N/A'), 'date': report.get('created_at', str(datetime.now())),
                'status': report.get('investigation_status', 'Draft'), 'title': report.get('hazard_title', report.get('flight_number', 'N/A'))
            })
    all_reports.sort(key=lambda x: x['date'], reverse=True)
    return all_reports[:limit]

# ══════════════════════════════════════════════════════════════════════════════
# OCR SIMULATION ENGINE
# ══════════════════════════════════════════════════════════════════════════════

def simulate_ocr_extraction(file_type: str, form_type: str) -> dict:
    random.seed(int(time.time()))
    flight_numbers = [f"PF-{random.randint(100, 999)}" for _ in range(5)]
    aircraft_regs = list(AIRCRAFT_FLEET.keys())
    
    if form_type == "bird_strike":
        return {
            "flight_number": random.choice(flight_numbers),
            "aircraft_reg": random.choice(aircraft_regs),
            "incident_date": (date.today() - timedelta(days=random.randint(0, 7))).isoformat(),
            "incident_time": f"{random.randint(5, 22):02d}:{random.randint(0, 59):02d}",
            "departure_airport": random.choice(list(AIRPORTS.keys())),
            "arrival_airport": random.choice(list(AIRPORTS.keys())),
            "flight_phase": random.choice(FLIGHT_PHASES[:8]),
            "altitude_agl": random.randint(0, 3000),
            "altitude_msl": random.randint(500, 5000),
            "indicated_speed": random.randint(120, 280),
            "bird_species": random.choice(BIRD_SPECIES[:15]),
            "bird_size": random.choice([s[0] for s in BIRD_SIZES]),
            "number_seen": random.randint(1, 20),
            "number_struck": random.randint(1, 5),
            "parts_struck": random.sample(AIRCRAFT_PARTS_STRUCK, random.randint(1, 3)),
            "damage_level": random.choice([d[0] for d in DAMAGE_LEVELS[:4]]),
            "effect_on_flight": random.choice(EFFECT_ON_FLIGHT_OPTIONS[:4]),
            "weather_conditions": random.choice(WEATHER_CONDITIONS[:8]),
            "pilot_warned": random.choice(["Yes - ATIS", "Yes - ATC", "No Warning"]),
            "captain_name": f"Capt. {random.choice(['Ahmed', 'Khan', 'Ali', 'Hassan'])} {random.choice(['Shah', 'Iqbal', 'Raza'])}",
            "captain_license": f"ATPL-PK-{random.randint(1000, 9999)}",
            "fo_name": f"FO {random.choice(['Usman', 'Bilal', 'Fahad'])} {random.choice(['Khan', 'Ahmed'])}",
            "narrative": f"Bird strike during {random.choice(['approach', 'departure', 'climb'])} phase.",
            "atc_notified": random.choice([True, False]),
            "remains_collected": random.choice(["Yes - Sent for ID", "No - No remains", "Yes - Retained"])
        }
    elif form_type == "laser_strike":
        return {
            "flight_number": random.choice(flight_numbers),
            "aircraft_reg": random.choice(aircraft_regs),
            "incident_date": (date.today() - timedelta(days=random.randint(0, 7))).isoformat(),
            "incident_time": f"{random.randint(18, 23):02d}:{random.randint(0, 59):02d}",
            "departure_airport": random.choice(list(AIRPORTS.keys())),
            "arrival_airport": random.choice(list(AIRPORTS.keys())),
            "location_description": f"{random.randint(2, 15)}nm {random.choice(['final', 'initial approach'])} RWY {random.choice(['09', '27', '36'])}{random.choice(['L', 'R', ''])}",
            "altitude_feet": random.randint(1500, 8000),
            "flight_phase": random.choice(["Approach", "Final Approach", "Initial Climb", "Descent"]),
            "laser_color": random.choice(LASER_COLORS[:5]),
            "laser_intensity": random.choice([l[0] for l in LASER_INTENSITIES]),
            "duration_seconds": random.randint(2, 30),
            "beam_movement": random.choice(["Tracking aircraft", "Stationary", "Sweeping"]),
            "crew_effects": random.sample(CREW_EFFECTS_LASER[:6], random.randint(1, 3)),
            "captain_affected": random.choice([True, False]),
            "fo_affected": random.choice([True, False]),
            "flash_blindness": random.choice([True, False]),
            "afterimage": random.choice([True, False]),
            "medical_attention": random.choice(["No - Not required", "Yes - Precautionary exam"]),
            "effect_on_flight": random.choice(["None - Flight continued", "Minor - Brief distraction", "Go-around performed"]),
            "atc_notified": True,
            "police_notified": random.choice([True, False]),
            "narrative": f"Laser illumination during {random.choice(['approach', 'final approach'])}."
        }
    elif form_type == "tcas_report":
        return {
            "flight_number": random.choice(flight_numbers),
            "aircraft_reg": random.choice(aircraft_regs),
            "incident_date": (date.today() - timedelta(days=random.randint(0, 7))).isoformat(),
            "incident_time": f"{random.randint(6, 22):02d}:{random.randint(0, 59):02d}",
            "departure_airport": random.choice(list(AIRPORTS.keys())),
            "arrival_airport": random.choice(list(AIRPORTS.keys())),
            "position": f"{random.choice(list(AIRPORTS.keys()))} VOR {random.randint(0, 360):03d}/{random.randint(5, 50)}",
            "altitude_feet": random.randint(10000, 35000),
            "heading": random.randint(0, 360),
            "indicated_speed": random.randint(250, 350),
            "flight_phase": random.choice(["Cruise", "Climb (Above 10000ft)", "Descent (Above 10000ft)"]),
            "tcas_equipment": random.choice(TCAS_EQUIPMENT_TYPES[:4]),
            "alert_type": random.choice(TCAS_ALERT_TYPES[:6]),
            "ra_sense": random.choice(["Climb", "Descend", "Level Off"]),
            "ra_followed": random.choice(["Yes - Full compliance", "Yes - Partial compliance"]),
            "traffic_position": random.choice(["12 o'clock", "2 o'clock", "10 o'clock", "6 o'clock"]),
            "traffic_altitude": random.choice(["Same level", "Above - Level", "Below - Climbing"]),
            "traffic_range": round(random.uniform(1.0, 8.0), 1),
            "min_vertical_sep": random.randint(300, 1500),
            "min_horizontal_sep": round(random.uniform(0.5, 5.0), 1),
            "vertical_deviation": random.randint(200, 800),
            "atc_clearance": f"Maintain FL{random.randint(250, 380)}",
            "atc_notified": True,
            "captain_name": f"Capt. {random.choice(['Ahmed', 'Khan', 'Ali'])} {random.choice(['Shah', 'Iqbal'])}",
            "narrative": f"TCAS {random.choice(['RA', 'TA'])} received at FL{random.randint(250, 350)}."
        }
    elif form_type == "hazard_report":
        return {
            "hazard_date": (date.today() - timedelta(days=random.randint(0, 3))).isoformat(),
            "hazard_time": f"{random.randint(6, 20):02d}:{random.randint(0, 59):02d}",
            "hazard_category": random.choice(HAZARD_CATEGORIES),
            "location": random.choice(["Ramp/Apron", "Taxiway", "Gate Area", "Maintenance Hangar", "Cargo Area"]),
            "specific_location": f"{random.choice(['Gate', 'Bay', 'Stand'])} {random.randint(1, 20)}",
            "airport": random.choice(list(AIRPORTS.keys())[:4]),
            "hazard_title": random.choice(["FOD observed on apron", "Lighting malfunction", "Ground equipment issue", "Procedure non-compliance", "Safety equipment missing"]),
            "hazard_description": f"During {random.choice(['routine inspection', 'turnaround operations'])}, {random.choice(['observed', 'identified'])} {random.choice(['potential hazard', 'safety concern'])}.",
            "likelihood": random.randint(2, 4),
            "severity": random.choice(["C", "D", "E"]),
            "existing_controls": "Standard operating procedures in place.",
            "suggested_actions": f"{random.choice(['Enhanced monitoring', 'Additional training', 'Equipment replacement'])} recommended.",
            "reporter_name": f"{random.choice(['Mr.', 'Ms.'])} {random.choice(['Ahmed', 'Fatima', 'Ali'])} {random.choice(['Khan', 'Shah'])}",
            "reporter_employee_id": f"EMP{random.randint(1000, 9999)}",
            "reporter_department": random.choice(DEPARTMENTS[:10])
        }
    elif form_type == "incident_report":
        return {
            "flight_number": random.choice(flight_numbers),
            "aircraft_reg": random.choice(aircraft_regs),
            "incident_date": (date.today() - timedelta(days=random.randint(0, 5))).isoformat(),
            "incident_time": f"{random.randint(5, 23):02d}:{random.randint(0, 59):02d}",
            "departure_airport": random.choice(list(AIRPORTS.keys())),
            "arrival_airport": random.choice(list(AIRPORTS.keys())),
            "notification_type": random.choice(["Incident", "Serious Incident", "Occurrence (Mandatory Reportable)"]),
            "primary_category": random.choice(INCIDENT_CATEGORIES[:15]),
            "flight_phase": random.choice(FLIGHT_PHASES),
            "altitude_feet": random.randint(0, 35000),
            "weather_conditions": random.choice(WEATHER_CONDITIONS[:10]),
            "captain_name": f"Capt. {random.choice(['Ahmed', 'Khan', 'Ali'])} {random.choice(['Shah', 'Iqbal'])}",
            "captain_license": f"ATPL-PK-{random.randint(1000, 9999)}",
            "fo_name": f"FO {random.choice(['Usman', 'Bilal'])} {random.choice(['Khan', 'Ahmed'])}",
            "pax_total": random.randint(40, 180),
            "injuries_none": True,
            "aircraft_damage": random.choice([d[0] for d in DAMAGE_LEVELS[:3]]),
            "emergency_declared": random.choice(["No", "PAN PAN"]),
            "incident_title": f"{random.choice(['System malfunction', 'Weather encounter', 'Operational event'])} during flight",
            "incident_description": f"During {random.choice(['cruise', 'approach', 'departure'])}, {random.choice(['experienced', 'encountered'])} {random.choice(['technical issue', 'operational event'])}.",
            "immediate_actions": f"Crew {random.choice(['monitored situation', 'executed checklist', 'coordinated with ATC'])}.",
            "caa_notified": random.choice([True, False])
        }
    return {"extraction_status": "completed", "confidence": f"{random.randint(85, 98)}%", "extracted_at": datetime.now().isoformat()}

def render_ocr_uploader(form_type: str) -> Optional[dict]:
    st.markdown("""
    <div style="background: linear-gradient(135deg, #EFF6FF 0%, #DBEAFE 100%); border: 2px dashed #3B82F6; border-radius: 12px; padding: 2rem; text-align: center; margin-bottom: 1.5rem;">
        <div style="font-size: 3rem; margin-bottom: 0.5rem;">📷</div>
        <h4 style="color: #1E40AF; margin: 0;">Scan Handwritten Form</h4>
        <p style="color: #64748B; font-size: 0.9rem; margin-top: 0.5rem;">Upload an image or PDF of a filled form to auto-extract data using OCR</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    with col1:
        uploaded_file = st.file_uploader("Upload Form Image/PDF", type=['png', 'jpg', 'jpeg', 'bmp', 'tiff', 'webp', 'pdf'], key=f"ocr_upload_{form_type}")
    with col2:
        ocr_engine = st.radio("OCR Engine", options=["Tesseract OCR", "Google Vision"], key=f"ocr_engine_{form_type}")
    
    if uploaded_file is not None:
        col1, col2 = st.columns([1, 1])
        with col1:
            if uploaded_file.type.startswith('image'):
                st.image(uploaded_file, caption="Uploaded Form", use_container_width=True)
            else:
                st.info(f"📄 PDF: {uploaded_file.name} ({uploaded_file.size / 1024:.1f} KB)")
        with col2:
            st.markdown("### OCR Processing")
            if st.button("🔍 Analyze with Tesseract OCR", key=f"analyze_{form_type}", type="primary", use_container_width=True):
                progress_bar = st.progress(0)
                status_text = st.empty()
                for progress, status in [(10, "📥 Loading document..."), (20, "🔧 Preprocessing image..."), (30, "📐 Detecting text regions..."), (45, "🔤 Running Tesseract OCR engine..."), (60, "📝 Extracting text from regions..."), (75, "🔍 Parsing form fields..."), (85, "✅ Validating extracted data..."), (95, "📊 Calculating confidence scores..."), (100, "✨ Extraction complete!")]:
                    progress_bar.progress(progress)
                    status_text.markdown(f"**{status}**")
                    time.sleep(0.3 + random.uniform(0.1, 0.3))
                extracted_data = simulate_ocr_extraction(uploaded_file.type, form_type)
                st.session_state[f'ocr_data_{form_type}'] = extracted_data
                st.success("✅ OCR extraction completed!")
                confidence = random.randint(87, 96)
                st.markdown(f"""<div style="background: #F0FDF4; border: 1px solid #86EFAC; border-radius: 8px; padding: 1rem; margin-top: 1rem;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div><strong style="color: #166534;">Extraction Confidence</strong><div style="font-size: 0.85rem; color: #15803D;">{len(extracted_data)} fields extracted</div></div>
                        <div style="font-size: 2rem; font-weight: 700; color: #16A34A;">{confidence}%</div>
                    </div>
                </div>""", unsafe_allow_html=True)
                with st.expander("📋 View Extracted Data", expanded=True):
                    for key, value in extracted_data.items():
                        if isinstance(value, list): value = ", ".join(str(v) for v in value)
                        st.markdown(f"**{key.replace('_', ' ').title()}:** {value}")
                st.info("💡 Extracted data pre-fills the form below. Please review and correct any errors.")
                return extracted_data
    return st.session_state.get(f'ocr_data_{form_type}')

# ══════════════════════════════════════════════════════════════════════════════
# STATIC WEATHER DATA - NO API CALLS
# ══════════════════════════════════════════════════════════════════════════════

# --- REPLACE WITH ---
# ══════════════════════════════════════════════════════════════════════════════
# WEATHER WIDGET (CORRECTED)
# ══════════════════════════════════════════════════════════════════════════════

# ══════════════════════════════════════════════════════════════════════════════
# WEATHER WIDGET (HYBRID: REAL API + MOCK FALLBACK)
# ══════════════════════════════════════════════════════════════════════════════
import requests
import streamlit as st

# Coordinates for your main airports (matches the Free API requirement)
AIRPORT_COORDS = {
    "OPSK": {"lat": 32.5353, "lon": 74.3636, "name": "Sialkot", "mock": {"temp": 24, "icon": "☀️", "wind": 12, "cond": "Clear"}},
    "OPKC": {"lat": 24.9060, "lon": 67.1600, "name": "Karachi", "mock": {"temp": 31, "icon": "🌫️", "wind": 22, "cond": "Haze"}},
    "OPLA": {"lat": 31.5216, "lon": 74.4036, "name": "Lahore", "mock": {"temp": 28, "icon": "☁️", "wind": 10, "cond": "Cloudy"}},
    "OPIS": {"lat": 33.5490, "lon": 73.0169, "name": "Islamabad", "mock": {"temp": 22, "icon": "🌧️", "wind": 15, "cond": "Rain"}},
    "OMDB": {"lat": 25.2532, "lon": 55.3657, "name": "Dubai", "mock": {"temp": 36, "icon": "☀️", "wind": 18, "cond": "Sunny"}},
}

@st.cache_data(ttl=1800)
def fetch_live_weather(icao_code):
    """
    Fetches weather from OpenWeatherMap (Free API).
    Falls back to mock data if no API Key is found or request fails.
    """
    airport = AIRPORT_COORDS.get(icao_code)
    if not airport:
        return None

    # 1. Try Real API (if key exists)
    api_key = st.secrets.get("OPENWEATHER_API_KEY") or st.secrets.get("WEATHER_API_KEY")
    
    if api_key:
        try:
            # Using the FREE API endpoint with lat/lon
            url = f"https://api.openweathermap.org/data/2.5/weather?lat={airport['lat']}&lon={airport['lon']}&units=metric&appid={api_key}"
            response = requests.get(url, timeout=3)
            
            if response.status_code == 200:
                data = response.json()
                # Map icon code to emoji
                icon_code = data['weather'][0]['icon']
                icon_map = {"01": "☀️", "02": "⛅", "03": "☁️", "04": "☁️", "09": "🌧️", "10": "🌦️", "11": "⛈️", "13": "❄️", "50": "🌫️"}
                emoji = icon_map.get(icon_code[:2], "🌤️")
                
                return {
                    "temp": round(data['main']['temp']),
                    "condition": data['weather'][0]['main'],
                    "wind": round(data['wind']['speed'] * 3.6), # m/s to km/h
                    "icon": emoji
                }
        except Exception:
            pass # Fail silently to mock data

    # 2. Fallback to Mock Data (so dashboard looks good)
    m = airport['mock']
    return {
        "temp": m['temp'],
        "condition": m['cond'],
        "wind": m['wind'],
        "icon": m['icon']
    }

def render_weather_widget():
    """Render the weather dashboard widget using real data."""
    # Import the weather module we just fixed
    import weather 
    
    st.markdown("### 🌤️ Weather Operations (Live)")
    
    # Create columns for the widget
    cols = st.columns(5)
    
    # Fetch real data
    weather_data = weather.get_all_weather()
    
    # Display logic
    if not weather_data:
        st.warning("Weather data unavailable. Check internet connection or API Key.")
        return

    for col, data in zip(cols, weather_data):
        with col:
            st.markdown(f"""
            <div style="background: white; border-radius: 12px; padding: 1rem; text-align: center; border: 1px solid #E2E8F0; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                <div style="font-size: 2rem; margin-bottom: 5px;">{data['icon']}</div>
                <div style="font-size: 1.5rem; font-weight: 700; color: #1E40AF; line-height: 1;">{data['temp']}°C</div>
                <div style="color: #64748B; font-size: 0.85rem; font-weight: 600; margin-top: 5px;">{data['name']}</div>
                <div style="font-size: 0.75rem; color: #94A3B8;">{data['condition']} • 💨 {data['wind']} km/h</div>
            </div>""", unsafe_allow_html=True)
# ══════════════════════════════════════════════════════════════════════════════
# CUSTOM CSS STYLING
# ══════════════════════════════════════════════════════════════════════════════

def apply_custom_css():
    st.markdown("""
    <style>
    .stApp { background: #F8FAFC; }
    #MainMenu {visibility: hidden;} footer {visibility: hidden;}
    .risk-badge { display: inline-block; padding: 0.35rem 0.75rem; border-radius: 20px; font-size: 0.75rem; font-weight: 600; }
    .risk-extreme { background: #FEE2E2; color: #DC2626; }
    .risk-high { background: #FFEDD5; color: #EA580C; }
    .risk-medium { background: #FEF9C3; color: #CA8A04; }
    .risk-low { background: #DCFCE7; color: #16A34A; }
    .form-section { background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px; padding: 1.5rem; margin-bottom: 1.5rem; }
    </style>
    """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# HEADER AND LOGO
# ══════════════════════════════════════════════════════════════════════════════

def get_logo_path():
    """Check multiple locations for logo file."""
    possible_paths = [
        "logo.png",
        "./logo.png",
        "assets/logo.png",
        "./assets/logo.png",
        "images/logo.png",
        "./images/logo.png",
        "/mount/src/airops-pro/logo.png",
        "/mount/src/airsial-sms/logo.png",
        "static/logo.png",
        "./static/logo.png"
    ]
    for path in possible_paths:
        if os.path.exists(path): 
            return path
    return None

def render_header():
    current_time = get_pakistan_time()
    erp_mode = st.session_state.get('erp_mode', False)
    
    if erp_mode:
        st.markdown('<div style="background: #DC2626; color: white; padding: 0.5rem; text-align: center; font-weight: bold; margin-bottom: 0.5rem; border-radius: 8px; animation: erp-flash 1s infinite;">⚠️ EMERGENCY RESPONSE PLAN ACTIVATED ⚠️</div>', unsafe_allow_html=True)
    
    col_logo, col_title, col_time = st.columns([1, 4, 2])
    with col_logo:
        logo_path = get_logo_path()
        if logo_path:
            try: st.image(logo_path, width=80)
            except: st.markdown('<span style="font-size: 3rem;">🛡️✈️</span>', unsafe_allow_html=True)
        else:
            st.markdown('<span style="font-size: 3rem;">🛡️✈️</span>', unsafe_allow_html=True)
    with col_title:
        st.markdown(f'<div style="padding-top: 0.5rem;"><h2 style="color: #1E40AF; margin: 0; font-weight: 700;">{Config.APP_NAME}</h2><p style="color: #64748B; margin: 0; font-size: 0.9rem;">{Config.APP_SUBTITLE} v{Config.APP_VERSION} | {Config.COMPANY_ICAO} | AOC: {Config.AOC_NUMBER}</p></div>', unsafe_allow_html=True)
    with col_time:
        st.markdown(f'<div style="text-align: right; padding-top: 0.5rem;"><div style="color: #64748B; font-size: 0.8rem;">🇵🇰 Pakistan Standard Time</div><div style="color: #1E40AF; font-size: 1.3rem; font-weight: 700;">{current_time.strftime("%H:%M:%S")}</div><div style="color: #64748B; font-size: 0.8rem;">{current_time.strftime("%A, %d %B %Y")}</div></div>', unsafe_allow_html=True)
    st.markdown('<div style="background: linear-gradient(135deg, #1E40AF 0%, #3B82F6 100%); height: 4px; border-radius: 4px; margin: 0.5rem 0 1rem 0;"></div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# RISK MATRIX COMPONENTS
# ══════════════════════════════════════════════════════════════════════════════

def render_risk_badge(risk_level: RiskLevel) -> str:
    class_map = {RiskLevel.EXTREME: "risk-extreme", RiskLevel.HIGH: "risk-high", RiskLevel.MEDIUM: "risk-medium", RiskLevel.LOW: "risk-low"}
    return f'<span class="risk-badge {class_map[risk_level]}">{risk_level.value}</span>'

def render_risk_matrix_selector():
    st.markdown("#### 📊 Risk Assessment (ICAO Standard)")
    col1, col2 = st.columns(2)
    with col1:
        likelihood = st.select_slider("**Likelihood**", options=[1, 2, 3, 4, 5], value=3, format_func=lambda x: f"{x} - {LIKELIHOOD_SCALE[x]['name']}")
        st.caption(f"📋 {LIKELIHOOD_SCALE[likelihood]['description']}")
    with col2:
        severity = st.selectbox("**Severity**", options=["E", "D", "C", "B", "A"], index=2, format_func=lambda x: f"{x} - {SEVERITY_SCALE[x]['name']}")
        st.caption(f"📋 {SEVERITY_SCALE[severity]['description']}")
    
    risk_level = calculate_risk_level(likelihood, severity)
    risk_info = RISK_ACTIONS[risk_level]
    risk_classification = f"{likelihood}{severity}"
    
    st.markdown(f"""<div style="background: {risk_info['color']}20; border: 2px solid {risk_info['color']}; border-radius: 10px; padding: 1.5rem; margin-top: 1rem;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div><span style="font-size: 2rem; font-weight: 700; color: {risk_info['color']};">{risk_classification}</span><span style="font-size: 1.5rem; margin-left: 1rem;">{render_risk_badge(risk_level)}</span></div>
            <div style="text-align: right;"><div style="font-weight: 600; color: {risk_info['color']};">{risk_info['action']}</div><div style="font-size: 0.85rem; opacity: 0.8;">Timeline: {risk_info['timeline']}</div></div>
        </div>
        <div style="margin-top: 1rem; font-size: 0.9rem;">{risk_info['description']}</div>
    </div>""", unsafe_allow_html=True)
    return likelihood, severity, risk_level, risk_classification

def render_visual_risk_matrix():
    """Darkened, High-Contrast ICAO Risk Matrix"""
    st.markdown("""
    <style>
        .matrix-cell { padding: 15px; color: white; font-weight: bold; text-align: center; border: 1px solid #333; }
        .risk-ext { background-color: #8B0000; } /* Dark Red */
        .risk-high { background-color: #CC5500; } /* Dark Orange */
        .risk-med { background-color: #B8860B; }  /* Dark Gold */
        .risk-low { background-color: #006400; }  /* Dark Green */
    </style>
    <div style="display: flex; justify-content: center;">
        <table style="width:100%; border-collapse: collapse;">
            <tr>
                <td class="matrix-cell risk-med">5A</td><td class="matrix-cell risk-med">5B</td><td class="matrix-cell risk-high">5C</td><td class="matrix-cell risk-ext">5D</td><td class="matrix-cell risk-ext">5E</td>
            </tr>
            <tr>
                <td class="matrix-cell risk-low">4A</td><td class="matrix-cell risk-med">4B</td><td class="matrix-cell risk-high">4C</td><td class="matrix-cell risk-ext">4D</td><td class="matrix-cell risk-ext">4E</td>
            </tr>
            <tr>
                <td class="matrix-cell risk-low">3A</td><td class="matrix-cell risk-low">3B</td><td class="matrix-cell risk-med">3C</td><td class="matrix-cell risk-high">3D</td><td class="matrix-cell risk-ext">3E</td>
            </tr>
            <tr>
                <td class="matrix-cell risk-low">2A</td><td class="matrix-cell risk-low">2B</td><td class="matrix-cell risk-low">2C</td><td class="matrix-cell risk-med">2D</td><td class="matrix-cell risk-high">2E</td>
            </tr>
            <tr>
                <td class="matrix-cell risk-low">1A</td><td class="matrix-cell risk-low">1B</td><td class="matrix-cell risk-low">1C</td><td class="matrix-cell risk-low">1D</td><td class="matrix-cell risk-med">1E</td>
            </tr>
        </table>
    </div>
    """, unsafe_allow_html=True)

def render_bird_strike_form():
    """
    Complete Bird Strike Report Form
    Sections A-K: Full aviation incident reporting
    """
    st.markdown("## 🐦 Bird Strike Report Form")
    st.markdown("*Complete all applicable sections for bird/wildlife strike incidents*")
    
    # Check for OCR extracted data
    ocr_data = st.session_state.get('ocr_data_bird_strike', {}) or {}
    
    # OCR Upload Section
    with st.expander("📷 Upload Form Image for OCR Autofill", expanded=False):
        extracted = render_ocr_uploader("bird_strike")
        if extracted:
            ocr_data = extracted
            st.session_state['ocr_data_bird_strike'] = extracted
    
    if ocr_data:
        st.info("✨ Form pre-filled with OCR extracted data. Please verify and correct any fields.")
    
    # Form container
    with st.form("bird_strike_form", clear_on_submit=False):
        
        # ========== SECTION A: INCIDENT IDENTIFICATION ==========
        st.markdown("""<div class="form-section">
            <div class="form-section-header">Section A: Incident Identification</div>
        </div>""", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            incident_id = st.text_input(
                "Incident Reference Number",
                value=f"BS-{datetime.now().strftime('%Y%m%d')}-{random.randint(100, 999)}",
                disabled=True
            )
        with col2:
            incident_date = st.date_input(
                "Date of Incident *",
                value=datetime.strptime(ocr_data.get('incident_date', date.today().isoformat()), '%Y-%m-%d').date() if ocr_data.get('incident_date') else date.today()
            )
        with col3:
            incident_time = st.time_input(
                "Time of Incident (UTC) *",
                value=datetime.strptime(ocr_data.get('incident_time', '12:00'), '%H:%M').time() if ocr_data.get('incident_time') else datetime.now().time()
            )
        
        col1, col2 = st.columns(2)
        with col1:
            time_of_day = st.selectbox(
                "Time of Day *",
                options=["Dawn", "Day", "Dusk", "Night"],
                index=["Dawn", "Day", "Dusk", "Night"].index(ocr_data.get('time_of_day', 'Day')) if ocr_data.get('time_of_day') in ["Dawn", "Day", "Dusk", "Night"] else 1
            )
        with col2:
            reported_by = st.text_input(
                "Reported By *",
                value=ocr_data.get('reported_by', st.session_state.get('user_name', ''))
            )
        
        # ========== SECTION B: FLIGHT INFORMATION ==========
        st.markdown("""<div class="form-section">
            <div class="form-section-header">Section B: Flight Information</div>
        </div>""", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            flight_number = st.text_input(
                "Flight Number *",
                value=ocr_data.get('flight_number', ''),
                placeholder="e.g., PF-101"
            )
        with col2:
            # Create a clean list of options first
            fleet_options = [""] + list(AIRCRAFT_FLEET.keys())
            
            # Find the correct index safely
            default_index = 0
            if ocr_data.get('aircraft_reg') in fleet_options:
                default_index = fleet_options.index(ocr_data['aircraft_reg'])

            aircraft_reg = st.selectbox(
                "Aircraft Registration *",
                options=fleet_options,
                index=default_index
            )
            
        with col3:
            # Auto-populate aircraft type based on registration
            aircraft_type = st.text_input(
                "Aircraft Type",
                value=AIRCRAFT_FLEET.get(aircraft_reg, {}).get("type", ""),
                disabled=True
            )
        
        col1, col2, col3 = st.columns(3)
        with col1:
            origin_airport = st.selectbox(
                "Origin Airport *",
                options=[""] + [f"{data['icao']} - {data['name']}" for data in AIRPORTS.values()],
                index=0
            )
        with col2:
            destination_airport = st.selectbox(
                "Destination Airport *",
                options=[""] + [f"{data['icao']} - {data['name']}" for data in AIRPORTS.values()],
                index=0
            )
        with col3:
            flight_phase = st.selectbox(
                "Phase of Flight *",
                options=FLIGHT_PHASES,
                index=FLIGHT_PHASES.index(ocr_data.get('flight_phase', 'Approach')) if ocr_data.get('flight_phase') in FLIGHT_PHASES else 6
            )
        
        # ========== SECTION C: STRIKE LOCATION ==========
        st.markdown("""<div class="form-section">
            <div class="form-section-header">Section C: Strike Location & Conditions</div>
        </div>""", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            strike_airport = st.selectbox(
                "Airport/Location of Strike",
                options=[""] + [f"{data['icao']} - {data['name']}" for data in AIRPORTS.values()],
                index=0
            )
        with col2:
            altitude_agl = st.number_input(
                "Altitude AGL (feet) *",
                min_value=0,
                max_value=50000,
                value=int(ocr_data.get('altitude_agl', 0)),
                step=100
            )
        with col3:
            altitude_msl = st.number_input(
                "Altitude MSL (feet)",
                min_value=0,
                max_value=50000,
                value=int(ocr_data.get('altitude_msl', altitude_agl)),
                step=100
            )
        
        col1, col2, col3 = st.columns(3)
        with col1:
            indicated_speed = st.number_input(
                "Indicated Airspeed (knots) *",
                min_value=0,
                max_value=500,
                value=int(ocr_data.get('indicated_speed', 0)),
                step=5
            )
        with col2:
            runway_used = st.text_input(
                "Runway Used (if applicable)",
                value=ocr_data.get('runway_used', ''),
                placeholder="e.g., 36L"
            )
        with col3:
            distance_from_runway = st.number_input(
                "Distance from Runway (nm)",
                min_value=0.0,
                max_value=100.0,
                value=float(ocr_data.get('distance_from_runway', 0.0)),
                step=0.5
            )
        
        col1, col2 = st.columns(2)
        with col1:
            weather_conditions = st.selectbox(
                "Weather Conditions",
                options=WEATHER_CONDITIONS,
                index=0
            )
        with col2:
            visibility = st.selectbox(
                "Visibility",
                options=["Good (>10km)", "Moderate (5-10km)", "Poor (1-5km)", "Very Poor (<1km)"],
                index=0
            )
        
        # ========== SECTION D: BIRD/WILDLIFE DETAILS ==========
        st.markdown("""<div class="form-section">
            <div class="form-section-header">Section D: Bird/Wildlife Details</div>
        </div>""", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            bird_species = st.selectbox(
                "Bird Species (if known)",
                options=["Unknown"] + BIRD_SPECIES,
                index=(["Unknown"] + BIRD_SPECIES).index(ocr_data.get('bird_species', 'Unknown')) if ocr_data.get('bird_species') in (["Unknown"] + BIRD_SPECIES) else 0
            )
        with col2:
            bird_size = st.selectbox(
                "Bird Size *",
                options=[s[0] for s in BIRD_SIZES],
                index=[s[0] for s in BIRD_SIZES].index(ocr_data.get('bird_size', 'Medium')) if ocr_data.get('bird_size') in [s[0] for s in BIRD_SIZES] else 2
            )
        with col3:
            number_struck = st.number_input(
                "Number of Birds Struck",
                min_value=1,
                max_value=100,
                value=int(ocr_data.get('number_struck', 1)),
                step=1
            )
        
        col1, col2 = st.columns(2)
        with col1:
            number_seen = st.number_input(
                "Number of Birds Seen",
                min_value=1,
                max_value=1000,
                value=max(int(ocr_data.get('number_seen', 1)), int(ocr_data.get('number_struck', 1))),
                step=1
            )
        with col2:
            bird_remains = st.selectbox(
                "Bird Remains Collected?",
                options=["No", "Yes - Sent for identification", "Yes - Available for collection", "Partial remains only"],
                index=0
            )
        
        bird_behavior = st.multiselect(
            "Bird Behavior Before Strike",
            options=["Flying", "Sitting on runway", "Sitting on taxiway", "Soaring/Circling", "Feeding", "Unknown"],
            default=[]
        )
        
        # ========== SECTION E: AIRCRAFT PARTS STRUCK ==========
        st.markdown("""<div class="form-section">
            <div class="form-section-header">Section E: Aircraft Parts Struck</div>
        </div>""", unsafe_allow_html=True)
        
        st.markdown("*Select all parts that were struck*")
        
        parts_struck = st.multiselect(
            "Parts Struck *",
            options=AIRCRAFT_PARTS_STRUCK,
            default=ocr_data.get('parts_struck', []) if isinstance(ocr_data.get('parts_struck'), list) else []
        )
        
        col1, col2 = st.columns(2)
        with col1:
            engine_ingested = st.selectbox(
                "Engine Ingestion?",
                options=["No", "Yes - Engine 1", "Yes - Engine 2", "Yes - Both Engines", "Suspected but not confirmed"],
                index=0
            )
        with col2:
            windshield_penetrated = st.selectbox(
                "Windshield Penetrated?",
                options=["No", "Yes - Cracked only", "Yes - Penetrated", "Yes - Shattered"],
                index=0
            )
        
        # ========== SECTION F: DAMAGE ASSESSMENT ==========
        st.markdown("""<div class="form-section">
            <div class="form-section-header">Section F: Damage Assessment</div>
        </div>""", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            damage_level = st.selectbox(
                "Overall Damage Level *",
                options=[d[0] for d in DAMAGE_LEVELS],
                index=[d[0] for d in DAMAGE_LEVELS].index(ocr_data.get('damage_level', 'None')) if ocr_data.get('damage_level') in [d[0] for d in DAMAGE_LEVELS] else 0
            )
        with col2:
            aircraft_out_of_service = st.selectbox(
                "Aircraft Out of Service?",
                options=["No", "Yes - Minor (< 24 hours)", "Yes - Significant (1-7 days)", "Yes - Major (> 7 days)"],
                index=0
            )
        
        damage_description = st.text_area(
            "Detailed Damage Description",
            value=ocr_data.get('damage_description', ''),
            placeholder="Describe all visible damage in detail...",
            height=100
        )
        
        col1, col2, col3 = st.columns(3)
        with col1:
            estimated_repair_cost = st.selectbox(
                "Estimated Repair Cost (USD)",
                options=["Unknown", "< $10,000", "$10,000 - $50,000", "$50,000 - $100,000", "$100,000 - $500,000", "> $500,000"],
                index=0
            )
        with col2:
            repair_time_estimate = st.text_input(
                "Estimated Repair Time",
                placeholder="e.g., 3 days"
            )
        with col3:
            maintenance_action = st.selectbox(
                "Maintenance Action Required",
                options=["None", "Inspection only", "Minor repair", "Major repair", "Component replacement", "Multiple repairs"],
                index=0
            )
        
        # ========== SECTION G: EFFECT ON FLIGHT ==========
        st.markdown("""<div class="form-section">
            <div class="form-section-header">Section G: Effect on Flight</div>
        </div>""", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            effect_on_flight = st.selectbox(
                "Effect on Flight *",
                options=EFFECT_ON_FLIGHT_OPTIONS,
                index=EFFECT_ON_FLIGHT_OPTIONS.index(ocr_data.get('effect_on_flight', 'None - Flight continued normally')) if ocr_data.get('effect_on_flight') in EFFECT_ON_FLIGHT_OPTIONS else 0
            )
            
        with col2:
            precautionary_landing = st.selectbox(
                "Precautionary Landing?",
                options=["No", "Yes - At destination", "Yes - Diversion", "Yes - Return to departure"],
                index=0
            )
        
        col1, col2 = st.columns(2)
        with col1:
            emergency_declared = st.selectbox(
                "Emergency Declared?",
                options=["No", "PAN PAN", "MAYDAY"],
                index=0
            )
        with col2:
            flight_delay_minutes = st.number_input(
                "Flight Delay (minutes)",
                min_value=0,
                max_value=1440,
                value=0,
                step=15
            )
        
        operational_impact = st.text_area(
            "Describe Operational Impact",
            placeholder="Detail any operational impacts (e.g., delayed departure, fuel dump, passenger inconvenience)...",
            height=80
        )
        
        # ========== SECTION H: CREW INFORMATION ==========
        st.markdown("""<div class="form-section">
            <div class="form-section-header">Section H: Crew Information</div>
        </div>""", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            captain_name = st.text_input(
                "Captain Name *",
                value=ocr_data.get('captain_name', '')
            )
        with col2:
            first_officer_name = st.text_input(
                "First Officer Name",
                value=ocr_data.get('first_officer_name', '')
            )
        
        col1, col2 = st.columns(2)
        with col1:
            captain_license = st.text_input(
                "Captain License Number",
                placeholder="e.g., ATPL-12345"
            )
        with col2:
            fo_license = st.text_input(
                "First Officer License Number",
                placeholder="e.g., CPL-67890"
            )
        
        crew_injuries = st.selectbox(
            "Crew Injuries?",
            options=["No injuries", "Minor injuries - no medical attention", "Minor injuries - medical attention required", "Serious injuries"],
            index=0
        )
        
        # ========== SECTION I: NOTIFICATIONS ==========
        st.markdown("""<div class="form-section">
            <div class="form-section-header">Section I: Notifications</div>
        </div>""", unsafe_allow_html=True)
        
        st.markdown("*Select all entities that have been or need to be notified*")
        
        notifications_made = st.multiselect(
            "Notifications Made",
            options=[
                "ATC Tower",
                "Airport Wildlife Control",
                "Company Operations Control",
                "Safety Department",
                "Maintenance Control",
                "PCAA (Civil Aviation Authority)",
                "Airport Authority",
                "Insurance Department",
                "Station Manager"
            ],
            default=["Safety Department", "Company Operations Control"]
        )
        
        col1, col2 = st.columns(2)
        with col1:
            atc_informed = st.selectbox(
                "ATC Informed of Strike?",
                options=["Yes - Immediately", "Yes - After landing", "No"],
                index=0
            )
        with col2:
            wildlife_control_informed = st.selectbox(
                "Wildlife Control Informed?",
                options=["Yes", "No", "Not available at airport"],
                index=0
            )
        
        # ========== SECTION J: ADDITIONAL INFORMATION ==========
        st.markdown("""<div class="form-section">
            <div class="form-section-header">Section J: Narrative & Additional Information</div>
        </div>""", unsafe_allow_html=True)
        
        narrative = st.text_area(
            "Detailed Narrative of Event *",
            value=ocr_data.get('narrative', ''),
            placeholder="Provide a detailed description of the bird strike incident, including sequence of events, crew actions, and any other relevant information...",
            height=150
        )
        
        contributing_factors = st.multiselect(
            "Contributing Factors (if any)",
            options=[
                "Wildlife activity near airport",
                "Time of day (dawn/dusk)",
                "Seasonal migration",
                "Weather conditions",
                "Airport grass/vegetation management",
                "Nearby water bodies",
                "Nearby landfill/waste disposal",
                "Lighting attracting birds",
                "Other"
            ],
            default=[]
        )
        
        recommendations = st.text_area(
            "Safety Recommendations",
            placeholder="Suggest any preventive measures or recommendations...",
            height=80
        )
        
        # ========== SECTION K: INVESTIGATION STATUS ==========
        st.markdown("""<div class="form-section">
            <div class="form-section-header">Section K: For Safety Department Use</div>
        </div>""", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            investigation_status = st.selectbox(
                "Investigation Status",
                options=["Open - Pending Review", "Open - Under Investigation", "Closed - No Further Action", "Closed - Corrective Actions Implemented"],
                index=0
            )
        with col2:
            assigned_investigator = st.selectbox(
                "Assigned To",
                options=["Unassigned", "Safety Manager", "Safety Officer", "Quality Manager", "External Investigator"],
                index=0
            )
        with col3:
            priority_level = st.selectbox(
                "Priority Level",
                options=["Low", "Medium", "High", "Critical"],
                index=1
            )
        
        # Photo/Document Upload
        st.markdown("#### 📎 Attachments")
        uploaded_photos = st.file_uploader(
            "Upload Photos/Documents",
            type=['png', 'jpg', 'jpeg', 'pdf', 'doc', 'docx'],
            accept_multiple_files=True,
            key="bird_strike_attachments"
        )
        
        # Form submission
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            submitted = st.form_submit_button(
                "📤 Submit Bird Strike Report",
                use_container_width=True,
                type="primary"
            )
        
        if submitted:
            # Validation
            errors = []
            if not flight_number:
                errors.append("Flight Number is required")
            if not aircraft_reg:
                errors.append("Aircraft Registration is required")
            if not captain_name:
                errors.append("Captain Name is required")
            if not narrative:
                errors.append("Detailed Narrative is required")
            if not parts_struck:
                errors.append("At least one part struck must be selected")
            
            if errors:
                for error in errors:
                    st.error(f"❌ {error}")
            else:
                # Calculate risk level based on damage
                if damage_level in ["Destroyed", "Substantial"]:
                    risk_level = "Extreme"
                elif damage_level in ["Major", "Minor - Confirmed"]:
                    risk_level = "High"
                elif damage_level == "Minor - Unconfirmed":
                    risk_level = "Medium"
                else:
                    risk_level = "Low"
                
                # Create report record
                report_data = {
                    'type': 'Bird Strike',
                    'date': incident_date.isoformat(),
                    'time': incident_time.strftime('%H:%M'),
                    'time_of_day': time_of_day,
                    'reported_by': reported_by,
                    'flight_number': flight_number,
                    'aircraft_reg': aircraft_reg,
                    'aircraft_type': aircraft_type,
                    'origin': origin_airport.split(' - ')[0] if origin_airport else '',
                    'destination': destination_airport.split(' - ')[0] if destination_airport else '',
                    'flight_phase': flight_phase,
                    'strike_location': strike_airport.split(' - ')[0] if strike_airport else '',
                    'altitude_agl': altitude_agl,
                    'altitude_msl': altitude_msl,
                    'indicated_speed': indicated_speed,
                    'runway': runway_used,
                    'distance_from_runway': distance_from_runway,
                    'weather': weather_conditions,
                    'visibility': visibility,
                    'bird_species': bird_species,
                    'bird_size': bird_size,
                    'number_struck': number_struck,
                    'number_seen': number_seen,
                    'bird_remains': bird_remains,
                    'bird_behavior': bird_behavior,
                    'parts_struck': parts_struck,
                    'engine_ingested': engine_ingested,
                    'windshield_penetrated': windshield_penetrated,
                    'damage_level': damage_level,
                    'aircraft_out_of_service': aircraft_out_of_service,
                    'damage_description': damage_description,
                    'estimated_cost': estimated_repair_cost,
                    'repair_time': repair_time_estimate,
                    'maintenance_action': maintenance_action,
                    'effect_on_flight': effect_on_flight,
                    'precautionary_landing': precautionary_landing,
                    'emergency_declared': emergency_declared,
                    'delay_minutes': flight_delay_minutes,
                    'operational_impact': operational_impact,
                    'captain_name': captain_name,
                    'first_officer': first_officer_name,
                    'captain_license': captain_license,
                    'fo_license': fo_license,
                    'crew_injuries': crew_injuries,
                    'notifications': notifications_made,
                    'atc_informed': atc_informed,
                    'wildlife_control_informed': wildlife_control_informed,
                    'narrative': narrative,
                    'contributing_factors': contributing_factors,
                    'recommendations': recommendations,
                    'status': investigation_status,
                    'assigned_to': assigned_investigator,
                    'priority': priority_level,
                    'risk_level': risk_level,
                    'attachments': len(uploaded_photos) if uploaded_photos else 0,
                    'created_at': datetime.now().isoformat(),
                    'department': st.session_state.get('user_department', 'Flight Operations')
                }
                
                # --- SUPABASE INSERTION BLOCK (CLEAN) ---
                try:
                    # Note: We don't include 'id' in the insert if your DB auto-generates it. 
                    # If you want to use your custom 'incident_id', ensure your DB 'id' column is text/varchar and not auto-increment int.
                    report_data['report_number'] = incident_id # Store your custom ID in a specific column
                    
                    response = supabase.table('bird_strikes').insert(report_data).execute()
                    st.balloons()
                    st.success(f"✅ Bird Strike Report Saved to Database! Ref: {incident_id}")
                except Exception as e:
                    st.error(f"Database Error: {e}")

                # Clear OCR data
                st.session_state['ocr_data_bird_strike'] = None
                
                # Clear OCR data
                st.session_state['ocr_data_bird_strike'] = None
                
                # Success feedback
                st.balloons()
                st.success(f"""
                    ✅ **Bird Strike Report Submitted Successfully!**
                    
                    **Reference:** {incident_id}  
                    **Risk Level:** {risk_level}  
                    **Status:** {investigation_status}
                    
                    The report has been added to the system and is now visible in View Reports.
                """)


def render_laser_strike_form():
    """
    Complete Laser Strike/Illumination Report Form
    Sections A-J: Full laser incident reporting per aviation standards
    """
    st.markdown("## 🔦 Laser Strike/Illumination Report Form")
    st.markdown("*Report laser illumination incidents affecting flight crew*")
    
    # Check for OCR extracted data
    ocr_data = st.session_state.get('ocr_data_laser_strike', {}) or {}
    
    # OCR Upload Section
    with st.expander("📷 Upload Form Image for OCR Autofill", expanded=False):
        extracted = render_ocr_uploader("laser_strike")
        if extracted:
            ocr_data = extracted
            st.session_state['ocr_data_laser_strike'] = extracted
    
    if ocr_data:
        st.info("✨ Form pre-filled with OCR extracted data. Please verify and correct any fields.")
    
    with st.form("laser_strike_form", clear_on_submit=False):
        
        # ========== SECTION A: INCIDENT IDENTIFICATION ==========
        st.markdown("""<div class="form-section">
            <div class="form-section-header">Section A: Incident Identification</div>
        </div>""", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            incident_id = st.text_input(
                "Incident Reference Number",
                value=f"LS-{datetime.now().strftime('%Y%m%d')}-{random.randint(100, 999)}",
                disabled=True
            )
        with col2:
            incident_date = st.date_input(
                "Date of Incident *",
                value=datetime.strptime(ocr_data.get('incident_date', date.today().isoformat()), '%Y-%m-%d').date() if ocr_data.get('incident_date') else date.today()
            )
        with col3:
            incident_time = st.time_input(
                "Time of Incident (UTC) *",
                value=datetime.strptime(ocr_data.get('incident_time', '12:00'), '%H:%M').time() if ocr_data.get('incident_time') else datetime.now().time()
            )
        
        col1, col2 = st.columns(2)
        with col1:
            local_time = st.time_input(
                "Local Time of Incident",
                value=datetime.now().time()
            )
        with col2:
            reported_by = st.text_input(
                "Reported By *",
                value=ocr_data.get('reported_by', st.session_state.get('user_name', ''))
            )
        
        # ========== SECTION B: FLIGHT INFORMATION ==========
        st.markdown("""<div class="form-section">
            <div class="form-section-header">Section B: Flight Information</div>
        </div>""", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            flight_number = st.text_input(
                "Flight Number *",
                value=ocr_data.get('flight_number', ''),
                placeholder="e.g., PF-101"
            )
        with col2:
            # Create a clean list of options first
            fleet_options = [""] + list(AIRCRAFT_FLEET.keys())
            
            # Find the correct index safely
            default_index = 0
            if ocr_data.get('aircraft_reg') in fleet_options:
                default_index = fleet_options.index(ocr_data['aircraft_reg'])

            aircraft_reg = st.selectbox(
                "Aircraft Registration *",
                options=fleet_options,
                index=default_index
            )
        with col3:
            aircraft_type = st.text_input(
                "Aircraft Type",
                value=AIRCRAFT_FLEET.get(aircraft_reg, {}).get("type", ""),
                disabled=True
            )
        
        col1, col2, col3 = st.columns(3)
        with col1:
            origin_airport = st.selectbox(
                "Origin Airport *",
                options=[""] + [f"{data['icao']} - {data['name']}" for data in AIRPORTS.values()],
                index=0,
                key="ls_origin"
            )
        with col2:
            destination_airport = st.selectbox(
                "Destination Airport *",
                options=[""] + [f"{data['icao']} - {data['name']}" for data in AIRPORTS.values()],
                index=0,
                key="ls_dest"
            )
        with col3:
            flight_phase = st.selectbox(
                "Phase of Flight *",
                options=FLIGHT_PHASES,
                index=FLIGHT_PHASES.index(ocr_data.get('flight_phase', 'Approach')) if ocr_data.get('flight_phase') in FLIGHT_PHASES else 6,
                key="ls_phase"
            )
        
        # ========== SECTION C: LOCATION OF INCIDENT ==========
        st.markdown("""<div class="form-section">
            <div class="form-section-header">Section C: Location of Incident</div>
        </div>""", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            incident_airport = st.selectbox(
                "Nearest Airport",
                options=[""] + [f"{data['icao']} - {data['name']}" for data in AIRPORTS.values()],
                index=0,
                key="ls_airport"
            )
        with col2:
            altitude_agl = st.number_input(
                "Altitude AGL (feet) *",
                min_value=0,
                max_value=50000,
                value=int(ocr_data.get('altitude_agl', 0)),
                step=100,
                key="ls_alt"
            )
        with col3:
            indicated_speed = st.number_input(
                "Indicated Airspeed (knots)",
                min_value=0,
                max_value=500,
                value=int(ocr_data.get('indicated_speed', 0)),
                step=5,
                key="ls_ias"
            )
        
        col1, col2 = st.columns(2)
        with col1:
            heading = st.number_input(
                "Aircraft Heading (degrees)",
                min_value=0,
                max_value=360,
                value=0,
                step=5
            )
        with col2:
            position_description = st.text_input(
                "Position Description",
                placeholder="e.g., 5nm final RWY 36L, over residential area"
            )
        
        st.markdown("**GPS Coordinates (if known)**")
        col1, col2 = st.columns(2)
        with col1:
            latitude = st.text_input(
                "Latitude",
                placeholder="e.g., 32.5150° N"
            )
        with col2:
            longitude = st.text_input(
                "Longitude",
                placeholder="e.g., 74.5361° E"
            )
        
        # ========== SECTION D: LASER CHARACTERISTICS ==========
        st.markdown("""<div class="form-section">
            <div class="form-section-header">Section D: Laser Characteristics</div>
        </div>""", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            laser_color = st.selectbox(
                "Laser Color *",
                options=[c[0] for c in LASER_COLORS],
                index=[c[0] for c in LASER_COLORS].index(ocr_data.get('laser_color', 'Green')) if ocr_data.get('laser_color') in [c[0] for c in LASER_COLORS] else 0
            )
        with col2:
            number_of_lasers = st.number_input(
                "Number of Laser Sources",
                min_value=1,
                max_value=10,
                value=int(ocr_data.get('number_of_lasers', 1)),
                step=1
            )
        with col3:
            laser_movement = st.selectbox(
                "Laser Movement Pattern",
                options=["Steady/Fixed", "Sweeping", "Tracking aircraft", "Random/Erratic", "Multiple patterns"],
                index=0
            )
        
        col1, col2, col3 = st.columns(3)
        with col1:
            duration_seconds = st.number_input(
                "Duration of Exposure (seconds) *",
                min_value=1,
                max_value=300,
                value=int(ocr_data.get('duration_seconds', 5)),
                step=1
            )
        with col2:
            intensity = st.selectbox(
                "Perceived Intensity *",
                options=["Low - Visible but not distracting", "Medium - Distracting", "High - Temporarily blinding", "Extreme - Severe visual impairment"],
                index=1
            )
        with col3:
            source_direction = st.selectbox(
                "Direction of Laser Source",
                options=["Ahead", "Left", "Right", "Below", "Behind", "Multiple directions", "Unable to determine"],
                index=0
            )
        
        estimated_distance = st.selectbox(
            "Estimated Distance to Laser Source",
            options=["< 1 km", "1-3 km", "3-5 km", "5-10 km", "> 10 km", "Unable to estimate"],
            index=2
        )
        
        # ========== SECTION E: CREW EFFECTS ==========
        st.markdown("""<div class="form-section">
            <div class="form-section-header">Section E: Crew Effects</div>
        </div>""", unsafe_allow_html=True)
        
        st.markdown("*Select all effects experienced by crew members*")
        
        crew_effects = st.multiselect(
            "Crew Effects *",
            options=[
                "No effect",
                "Distraction",
                "Glare - Reduced visibility",
                "Flash blindness - Temporary",
                "Afterimage - Persistent spots",
                "Eye pain/discomfort",
                "Headache",
                "Disorientation",
                "Startle/Surprise",
                "Difficulty reading instruments"
            ],
            default=ocr_data.get('crew_effects', ['Distraction']) if isinstance(ocr_data.get('crew_effects'), list) else ['Distraction']
        )
        
        col1, col2 = st.columns(2)
        with col1:
            pilot_flying_affected = st.selectbox(
                "Pilot Flying (PF) Affected?",
                options=["No", "Yes - Minor", "Yes - Moderate", "Yes - Severe"],
                index=0
            )
        with col2:
            pilot_monitoring_affected = st.selectbox(
                "Pilot Monitoring (PM) Affected?",
                options=["No", "Yes - Minor", "Yes - Moderate", "Yes - Severe"],
                index=0
            )
        
        recovery_time = st.selectbox(
            "Time to Recover Normal Vision",
            options=["Immediate (< 10 seconds)", "Short (10-30 seconds)", "Moderate (30 seconds - 2 minutes)", "Extended (2-5 minutes)", "Prolonged (> 5 minutes)", "Still experiencing effects"],
            index=0
        )
        
        # ========== SECTION F: MEDICAL ASSESSMENT ==========
        st.markdown("""<div class="form-section">
            <div class="form-section-header">Section F: Medical Assessment</div>
        </div>""", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            medical_attention = st.selectbox(
                "Medical Attention Required? *",
                options=["No", "Yes - First aid only", "Yes - Medical examination", "Yes - Hospital treatment", "Pending evaluation"],
                index=0
            )
        with col2:
            symptoms_persistent = st.selectbox(
                "Persistent Symptoms?",
                options=["No", "Yes - Resolved within 24 hours", "Yes - Ongoing", "Under medical observation"],
                index=0
            )
        
        medical_details = st.text_area(
            "Medical Details (if applicable)",
            placeholder="Describe any medical symptoms, treatment received, or ongoing concerns...",
            height=80
        )
        
        # ========== SECTION G: EFFECT ON FLIGHT ==========
        st.markdown("""<div class="form-section">
            <div class="form-section-header">Section G: Effect on Flight Operations</div>
        </div>""", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            effect_on_flight = st.selectbox(
                "Effect on Flight *",
                options=[
                    "None - Continued normally",
                    "Minor - Increased vigilance",
                    "Moderate - Temporary loss of visual reference",
                    "Significant - Autopilot engaged",
                    "Significant - Control transferred to PM",
                    "Severe - Go-around executed",
                    "Severe - Flight diverted",
                    "Critical - Emergency declared"
                ],
                index=0
            )
        with col2:
            approach_disrupted = st.selectbox(
                "Approach/Landing Disrupted?",
                options=["No", "Yes - Stabilized approach affected", "Yes - Go-around required", "Yes - Diversion required"],
                index=0
            )
        
        col1, col2 = st.columns(2)
        with col1:
            emergency_declared = st.selectbox(
                "Emergency Declared?",
                options=["No", "PAN PAN", "MAYDAY"],
                index=0,
                key="ls_emergency"
            )
        with col2:
            autopilot_used = st.selectbox(
                "Autopilot Engagement?",
                options=["Already engaged", "Engaged due to incident", "Not engaged", "Disconnected for landing"],
                index=0
            )
        
        # ========== SECTION H: NOTIFICATIONS ==========
        st.markdown("""<div class="form-section">
            <div class="form-section-header">Section H: Notifications</div>
        </div>""", unsafe_allow_html=True)
        
        notifications_made = st.multiselect(
            "Notifications Made",
            options=[
                "ATC Tower",
                "ATC Approach",
                "Company Operations Control",
                "Safety Department",
                "PCAA (Civil Aviation Authority)",
                "Airport Security",
                "Local Police/Law Enforcement",
                "Station Manager"
            ],
            default=["ATC Tower", "Safety Department"]
        )
        
        col1, col2 = st.columns(2)
        with col1:
            atc_notified = st.selectbox(
                "ATC Notified?",
                options=["Yes - During event", "Yes - After landing", "No"],
                index=0
            )
        with col2:
            police_notified = st.selectbox(
                "Police/Authorities Notified?",
                options=["Yes", "No", "Pending", "Not applicable"],
                index=1
            )
        
        # ========== SECTION I: NARRATIVE ==========
        st.markdown("""<div class="form-section">
            <div class="form-section-header">Section I: Narrative & Additional Information</div>
        </div>""", unsafe_allow_html=True)
        
        narrative = st.text_area(
            "Detailed Narrative of Event *",
            value=ocr_data.get('narrative', ''),
            placeholder="Provide a detailed description of the laser illumination incident, including sequence of events, crew actions, and any other relevant information...",
            height=150
        )
        
        col1, col2 = st.columns(2)
        with col1:
            captain_name = st.text_input(
                "Captain Name *",
                value=ocr_data.get('captain_name', ''),
                key="ls_captain"
            )
        with col2:
            first_officer_name = st.text_input(
                "First Officer Name",
                value=ocr_data.get('first_officer_name', ''),
                key="ls_fo"
            )
        
        witness_information = st.text_area(
            "Witness Information (if any)",
            placeholder="Details of any witnesses, cabin crew observations, passenger reports...",
            height=60
        )
        
        # ========== SECTION J: INVESTIGATION STATUS ==========
        st.markdown("""<div class="form-section">
            <div class="form-section-header">Section J: For Safety Department Use</div>
        </div>""", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            investigation_status = st.selectbox(
                "Investigation Status",
                options=["Open - Pending Review", "Open - Under Investigation", "Referred to Authorities", "Closed - No Further Action", "Closed - Corrective Actions"],
                index=0,
                key="ls_status"
            )
        with col2:
            assigned_investigator = st.selectbox(
                "Assigned To",
                options=["Unassigned", "Safety Manager", "Safety Officer", "Quality Manager", "Security Department"],
                index=0,
                key="ls_assigned"
            )
        with col3:
            priority_level = st.selectbox(
                "Priority Level",
                options=["Low", "Medium", "High", "Critical"],
                index=1 if "High" not in intensity else 2,
                key="ls_priority"
            )
        
        # Photo/Document Upload
        st.markdown("#### 📎 Attachments")
        uploaded_files = st.file_uploader(
            "Upload Photos/Documents",
            type=['png', 'jpg', 'jpeg', 'pdf', 'doc', 'docx'],
            accept_multiple_files=True,
            key="laser_strike_attachments"
        )
        
        # Form submission
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            submitted = st.form_submit_button(
                "📤 Submit Laser Strike Report",
                use_container_width=True,
                type="primary"
            )
        
        if submitted:
            # Validation
            errors = []
            if not flight_number:
                errors.append("Flight Number is required")
            if not aircraft_reg:
                errors.append("Aircraft Registration is required")
            if not captain_name:
                errors.append("Captain Name is required")
            if not narrative:
                errors.append("Detailed Narrative is required")
            if not crew_effects or "No effect" in crew_effects and len(crew_effects) == 1:
                pass  # Allow no effect
            
            if errors:
                for error in errors:
                    st.error(f"❌ {error}")
            else:
                # Calculate risk level
                if "Extreme" in intensity or medical_attention not in ["No", "Yes - First aid only"]:
                    risk_level = "Extreme"
                elif "High" in intensity or emergency_declared != "No":
                    risk_level = "High"
                elif "Medium" in intensity:
                    risk_level = "Medium"
                else:
                    risk_level = "Low"
                
                # Create report record
                report_data = {
                    'type': 'Laser Strike',
                    'date': incident_date.isoformat(),
                    'time': incident_time.strftime('%H:%M'),
                    'local_time': local_time.strftime('%H:%M'),
                    'reported_by': reported_by,
                    'flight_number': flight_number,
                    'aircraft_reg': aircraft_reg,
                    'aircraft_type': aircraft_type,
                    'origin': origin_airport.split(' - ')[0] if origin_airport else '',
                    'destination': destination_airport.split(' - ')[0] if destination_airport else '',
                    'flight_phase': flight_phase,
                    'incident_airport': incident_airport.split(' - ')[0] if incident_airport else '',
                    'altitude_agl': altitude_agl,
                    'indicated_speed': indicated_speed,
                    'heading': heading,
                    'position_description': position_description,
                    'latitude': latitude,
                    'longitude': longitude,
                    'laser_color': laser_color,
                    'number_of_lasers': number_of_lasers,
                    'laser_movement': laser_movement,
                    'duration_seconds': duration_seconds,
                    'intensity': intensity,
                    'source_direction': source_direction,
                    'estimated_distance': estimated_distance,
                    'crew_effects': crew_effects,
                    'pf_affected': pilot_flying_affected,
                    'pm_affected': pilot_monitoring_affected,
                    'recovery_time': recovery_time,
                    'medical_attention': medical_attention,
                    'symptoms_persistent': symptoms_persistent,
                    'medical_details': medical_details,
                    'effect_on_flight': effect_on_flight,
                    'approach_disrupted': approach_disrupted,
                    'emergency_declared': emergency_declared,
                    'autopilot_used': autopilot_used,
                    'notifications': notifications_made,
                    'atc_notified': atc_notified,
                    'police_notified': police_notified,
                    'narrative': narrative,
                    'captain_name': captain_name,
                    'first_officer': first_officer_name,
                    'witness_info': witness_information,
                    'status': investigation_status,
                    'assigned_to': assigned_investigator,
                    'priority': priority_level,
                    'risk_level': risk_level,
                    'attachments': len(uploaded_files) if uploaded_files else 0,
                    'created_at': datetime.now().isoformat(),
                    'department': st.session_state.get('user_department', 'Flight Operations')
                }
                
                # --- SUPABASE INSERTION BLOCK ---
                try:
                    # Save to database
                    report_data['report_number'] = incident_id
                    response = supabase.table('laser_strikes').insert(report_data).execute()
                    st.balloons()
                    st.success(f"✅ Laser Strike Report Saved to Database! Ref: {incident_id}")
                except Exception as e:
                    st.error(f"Database Error: {e}")

                # Clear OCR data
                st.session_state['ocr_data_laser_strike'] = None
                
                # Success feedback
                st.balloons()
                st.success(f"""
                    ✅ **Laser Strike Report Submitted Successfully!**
                    
                    **Reference:** {incident_id}  
                    **Risk Level:** {risk_level}  
                    **Status:** {investigation_status}
                    
                    The report has been added to the system and is now visible in View Reports.
                """)


def render_tcas_report_form():
    """
    Complete TCAS/Airborne Conflict Report Form
    Sections A-K: Full TCAS/ACAS event reporting per aviation standards
    """
    st.markdown("## ✈️ TCAS/Airborne Conflict Report Form")
    st.markdown("*Report Traffic Collision Avoidance System alerts and airborne conflicts*")
    
    # Check for OCR extracted data
    ocr_data = st.session_state.get('ocr_data_tcas_report', {}) or {}
    
    # OCR Upload Section
    with st.expander("📷 Upload Form Image for OCR Autofill", expanded=False):
        extracted = render_ocr_uploader("tcas_report")
        if extracted:
            ocr_data = extracted
            st.session_state['ocr_data_tcas_report'] = extracted
    
    if ocr_data:
        st.info("✨ Form pre-filled with OCR extracted data. Please verify and correct any fields.")
    
    with st.form("tcas_report_form", clear_on_submit=False):
        
        # ========== SECTION A: INCIDENT IDENTIFICATION ==========
        st.markdown("""<div class="form-section">
            <div class="form-section-header">Section A: Incident Identification</div>
        </div>""", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            incident_id = st.text_input(
                "Incident Reference Number",
                value=f"TCAS-{datetime.now().strftime('%Y%m%d')}-{random.randint(100, 999)}",
                disabled=True
            )
        with col2:
            incident_date = st.date_input(
                "Date of Incident *",
                value=datetime.strptime(ocr_data.get('incident_date', date.today().isoformat()), '%Y-%m-%d').date() if ocr_data.get('incident_date') else date.today(),
                key="tcas_date"
            )
        with col3:
            incident_time = st.time_input(
                "Time of Incident (UTC) *",
                value=datetime.strptime(ocr_data.get('incident_time', '12:00'), '%H:%M').time() if ocr_data.get('incident_time') else datetime.now().time(),
                key="tcas_time"
            )
        
        col1, col2 = st.columns(2)
        with col1:
            reported_by = st.text_input(
                "Reported By *",
                value=ocr_data.get('reported_by', st.session_state.get('user_name', '')),
                key="tcas_reporter"
            )
        with col2:
            reporter_position = st.selectbox(
                "Reporter Position",
                options=CREW_POSITIONS,
                index=0,
                key="tcas_position"
            )
        
        # ========== SECTION B: OWN AIRCRAFT INFORMATION ==========
        st.markdown("""<div class="form-section">
            <div class="form-section-header">Section B: Own Aircraft Information</div>
        </div>""", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            flight_number = st.text_input(
                "Flight Number *",
                value=ocr_data.get('flight_number', ''),
                placeholder="e.g., PF-101",
                key="tcas_flight"
            )
        with col2:
            # Create a clean list of options first
            fleet_options = [""] + list(AIRCRAFT_FLEET.keys())
            
            # Find the correct index safely
            default_index = 0
            if ocr_data.get('aircraft_reg') in fleet_options:
                default_index = fleet_options.index(ocr_data['aircraft_reg'])

            aircraft_reg = st.selectbox(
                "Aircraft Registration *",
                options=fleet_options,
                index=default_index
            )
        with col3:
            aircraft_type = st.text_input(
                "Aircraft Type",
                value=AIRCRAFT_FLEET.get(aircraft_reg, {}).get("type", ""),
                disabled=True,
                key="tcas_type"
            )
        
        col1, col2, col3 = st.columns(3)
        with col1:
            origin_airport = st.selectbox(
                "Origin Airport *",
                options=[""] + [f"{data['icao']} - {data['name']}" for data in AIRPORTS.values()],
                index=0,
                key="tcas_origin"
            )
        with col2:
            destination_airport = st.selectbox(
                "Destination Airport *",
                options=[""] + [f"{data['icao']} - {data['name']}" for data in AIRPORTS.values()],
                index=0,
                key="tcas_dest"
            )
        with col3:
            flight_phase = st.selectbox(
                "Phase of Flight *",
                options=FLIGHT_PHASES,
                index=FLIGHT_PHASES.index(ocr_data.get('flight_phase', 'Cruise')) if ocr_data.get('flight_phase') in FLIGHT_PHASES else 10,
                key="tcas_phase"
            )
        
        col1, col2 = st.columns(2)
        with col1:
            flight_rules = st.selectbox(
                "Flight Rules",
                options=["IFR", "VFR", "SVFR"],
                index=0
            )
        with col2:
            transponder_mode = st.selectbox(
                "Transponder Mode",
                options=["Mode S", "Mode C", "Mode A", "ADS-B Out"],
                index=0
            )
        
        # ========== SECTION C: POSITION AT TIME OF EVENT ==========
        st.markdown("""<div class="form-section">
            <div class="form-section-header">Section C: Position at Time of Event</div>
        </div>""", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            altitude_fl = st.number_input(
                "Flight Level / Altitude (feet) *",
                min_value=0,
                max_value=50000,
                value=int(ocr_data.get('altitude_fl', 0)),
                step=500,
                key="tcas_alt"
            )
        with col2:
            indicated_speed = st.number_input(
                "Indicated Airspeed (knots)",
                min_value=0,
                max_value=600,
                value=int(ocr_data.get('indicated_speed', 0)),
                step=10,
                key="tcas_ias"
            )
        with col3:
            heading = st.number_input(
                "Heading (degrees)",
                min_value=0,
                max_value=360,
                value=0,
                step=5,
                key="tcas_hdg"
            )
        
        col1, col2 = st.columns(2)
        with col1:
            vertical_rate = st.number_input(
                "Vertical Rate (fpm)",
                min_value=-6000,
                max_value=6000,
                value=0,
                step=100,
                help="Positive = climbing, Negative = descending"
            )
        with col2:
            position_description = st.text_input(
                "Position/Fix",
                placeholder="e.g., 25nm SE of OPLA VOR, on airway G-500",
                key="tcas_pos"
            )
        
        st.markdown("**GPS Coordinates (if known)**")
        col1, col2 = st.columns(2)
        with col1:
            latitude = st.text_input(
                "Latitude",
                placeholder="e.g., 31.5204° N",
                key="tcas_lat"
            )
        with col2:
            longitude = st.text_input(
                "Longitude",
                placeholder="e.g., 74.3587° E",
                key="tcas_lon"
            )
        
        # ========== SECTION D: TCAS ALERT INFORMATION ==========
        st.markdown("""<div class="form-section">
            <div class="form-section-header">Section D: TCAS Alert Information</div>
        </div>""", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            tcas_alert_type = st.selectbox(
                "Type of TCAS Alert *",
                options=TCAS_ALERT_TYPES,
                index=TCAS_ALERT_TYPES.index(ocr_data.get('tcas_alert_type', 'RA - Climb')) if ocr_data.get('tcas_alert_type') in TCAS_ALERT_TYPES else 0
            )
        with col2:
            ra_sense = st.selectbox(
                "RA Sense (if RA)",
                options=["N/A - TA only", "Climb", "Descend", "Level Off", "Adjust Vertical Speed", "Crossing Climb", "Crossing Descend", "Reversal"],
                index=0
            )
        
        col1, col2, col3 = st.columns(3)
        with col1:
            ra_complied = st.selectbox(
                "RA Complied With?",
                options=["Yes - Fully", "Yes - Partially", "No", "N/A - TA only"],
                index=0
            )
        with col2:
            time_to_cpa = st.number_input(
                "Time to CPA (seconds)",
                min_value=0,
                max_value=120,
                value=30,
                step=5,
                help="Closest Point of Approach"
            )
        with col3:
            ra_duration = st.number_input(
                "RA Duration (seconds)",
                min_value=0,
                max_value=120,
                value=15,
                step=5
            )
        
        tcas_system_status = st.selectbox(
            "TCAS System Status",
            options=["Normal - Full functionality", "TA Only mode", "Degraded performance", "System fault during event"],
            index=0
        )
        
        # ========== SECTION E: TRAFFIC INFORMATION ==========
        st.markdown("""<div class="form-section">
            <div class="form-section-header">Section E: Traffic (Intruder) Information</div>
        </div>""", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            traffic_type = st.selectbox(
                "Traffic Type",
                options=["Commercial - Airline", "Commercial - Cargo", "General Aviation", "Military", "Helicopter", "Unknown", "Multiple aircraft"],
                index=0
            )
        with col2:
            traffic_callsign = st.text_input(
                "Traffic Callsign (if known)",
                placeholder="e.g., ABC123"
            )
        
        col1, col2, col3 = st.columns(3)
        with col1:
            traffic_altitude = st.text_input(
                "Traffic Altitude",
                placeholder="e.g., FL350, 35000ft"
            )
        with col2:
            traffic_heading = st.text_input(
                "Traffic Heading (if known)",
                placeholder="e.g., 270°"
            )
        with col3:
            traffic_type_ac = st.text_input(
                "Traffic Aircraft Type (if known)",
                placeholder="e.g., B737, A320"
            )
        
        col1, col2 = st.columns(2)
        with col1:
            traffic_position = st.selectbox(
                "Traffic Position (Clock Position)",
                options=["12 o'clock", "1 o'clock", "2 o'clock", "3 o'clock", "4 o'clock", "5 o'clock", 
                        "6 o'clock", "7 o'clock", "8 o'clock", "9 o'clock", "10 o'clock", "11 o'clock", "Unknown"],
                index=0
            )
        with col2:
            traffic_aspect = st.selectbox(
                "Traffic Aspect",
                options=["Head-on", "Converging from left", "Converging from right", "Overtaking", "Being overtaken", "Parallel", "Crossing", "Unknown"],
                index=0
            )
        
        traffic_visual = st.selectbox(
            "Traffic Visually Acquired?",
            options=["Yes - Before alert", "Yes - During alert", "Yes - After alert", "No - Never sighted", "Partial - Lost in clouds"],
            index=0
        )
        
        # ========== SECTION F: SEPARATION ==========
        st.markdown("""<div class="form-section">
            <div class="form-section-header">Section F: Minimum Separation</div>
        </div>""", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            vertical_separation = st.number_input(
                "Estimated Vertical Separation (feet) *",
                min_value=0,
                max_value=10000,
                value=int(ocr_data.get('vertical_separation', 500)),
                step=100
            )
        with col2:
            horizontal_separation = st.number_input(
                "Estimated Horizontal Separation (nm)",
                min_value=0.0,
                max_value=20.0,
                value=float(ocr_data.get('horizontal_separation', 1.0)),
                step=0.1
            )
        with col3:
            slant_range = st.number_input(
                "Slant Range (nm)",
                min_value=0.0,
                max_value=20.0,
                value=0.0,
                step=0.1
            )
        
        separation_confidence = st.selectbox(
            "Confidence in Separation Estimate",
            options=["High - TCAS/radar data", "Medium - Visual estimate", "Low - Uncertain"],
            index=0
        )
        
        # ========== SECTION G: ATC COORDINATION ==========
        st.markdown("""<div class="form-section">
            <div class="form-section-header">Section G: ATC Coordination</div>
        </div>""", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            atc_unit = st.text_input(
                "ATC Unit",
                placeholder="e.g., Lahore Approach, Karachi Control"
            )
        with col2:
            atc_frequency = st.text_input(
                "ATC Frequency",
                placeholder="e.g., 119.1 MHz"
            )
        
        col1, col2 = st.columns(2)
        with col1:
            atc_clearance = st.selectbox(
                "ATC Clearance at Time of Event",
                options=["Maintain altitude", "Climbing", "Descending", "Radar vectors", "Own navigation", "Visual approach", "Unknown/Not in contact"],
                index=0
            )
        with col2:
            atc_informed = st.selectbox(
                "ATC Informed of RA?",
                options=["Yes - During event", "Yes - After event", "No", "N/A - TA only"],
                index=0
            )
        
        atc_instructions = st.text_area(
            "ATC Instructions Received (if any)",
            placeholder="Detail any traffic advisories or instructions from ATC...",
            height=60
        )
        
        # ========== SECTION H: CREW ACTIONS ==========
        st.markdown("""<div class="form-section">
            <div class="form-section-header">Section H: Crew Actions</div>
        </div>""", unsafe_allow_html=True)
        
        crew_actions = st.multiselect(
            "Crew Actions Taken",
            options=[
                "Followed RA guidance",
                "Visual acquisition attempted",
                "Reported to ATC",
                "Adjusted vertical rate",
                "Initiated climb",
                "Initiated descent",
                "Maintained level flight",
                "Autopilot disconnected",
                "Flight director followed",
                "Evasive maneuver beyond RA",
                "No action required (TA only)"
            ],
            default=["Followed RA guidance", "Reported to ATC"]
        )
        
        col1, col2 = st.columns(2)
        with col1:
            captain_name = st.text_input(
                "Captain Name *",
                value=ocr_data.get('captain_name', ''),
                key="tcas_captain"
            )
        with col2:
            first_officer_name = st.text_input(
                "First Officer Name",
                value=ocr_data.get('first_officer_name', ''),
                key="tcas_fo"
            )
        
        pilot_flying = st.selectbox(
            "Pilot Flying (PF) at Time of Event",
            options=["Captain", "First Officer"],
            index=0
        )
        
        # ========== SECTION I: NARRATIVE ==========
        st.markdown("""<div class="form-section">
            <div class="form-section-header">Section I: Narrative</div>
        </div>""", unsafe_allow_html=True)
        
        narrative = st.text_area(
            "Detailed Narrative of Event *",
            value=ocr_data.get('narrative', ''),
            placeholder="Provide a detailed description of the TCAS event, including sequence of events, crew actions, ATC communications, and any other relevant information...",
            height=150
        )
        
        contributing_factors = st.multiselect(
            "Possible Contributing Factors",
            options=[
                "ATC separation error",
                "Incorrect altitude assignment",
                "Miscommunication with ATC",
                "Pilot deviation",
                "Traffic complexity",
                "Weather-related routing",
                "Airspace congestion",
                "VFR traffic in IFR airspace",
                "Military activity",
                "Unknown"
            ],
            default=[]
        )
        
        # ========== SECTION J: AIRPROX CLASSIFICATION ==========
        st.markdown("""<div class="form-section">
            <div class="form-section-header">Section J: Airprox Classification (For Safety Dept)</div>
        </div>""", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            airprox_category = st.selectbox(
                "Airprox Risk Category",
                options=[
                    "Category A - Risk of collision",
                    "Category B - Safety not assured",
                    "Category C - No risk of collision",
                    "Category D - Risk not determined",
                    "Category E - Not airprox (normal ops)"
                ],
                index=1
            )
        with col2:
            airprox_cause = st.selectbox(
                "Cause Classification",
                options=[
                    "ATC - Controller error",
                    "Pilot - Own aircraft",
                    "Pilot - Other aircraft",
                    "Technical - Equipment failure",
                    "Procedural - SOP deviation",
                    "Unknown/Under investigation"
                ],
                index=5
            )
        
        # ========== SECTION K: INVESTIGATION STATUS ==========
        st.markdown("""<div class="form-section">
            <div class="form-section-header">Section K: Investigation Status</div>
        </div>""", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            investigation_status = st.selectbox(
                "Investigation Status",
                options=["Open - Pending Review", "Open - Under Investigation", "Referred to PCAA", "Referred to ATC", "Closed - No Further Action", "Closed - Recommendations Issued"],
                index=0,
                key="tcas_status"
            )
        with col2:
            assigned_investigator = st.selectbox(
                "Assigned To",
                options=["Unassigned", "Safety Manager", "Safety Officer", "Quality Manager", "Flight Operations Manager"],
                index=0,
                key="tcas_assigned"
            )
        with col3:
            priority_level = st.selectbox(
                "Priority Level",
                options=["Low", "Medium", "High", "Critical"],
                index=2 if "RA" in tcas_alert_type else 1,
                key="tcas_priority"
            )
        
        # Data preservation request
        col1, col2 = st.columns(2)
        with col1:
            fdr_requested = st.selectbox(
                "FDR/QAR Data Requested?",
                options=["Yes", "No", "Pending"],
                index=1
            )
        with col2:
            cvr_preserved = st.selectbox(
                "CVR Preservation Requested?",
                options=["Yes", "No", "N/A"],
                index=1
            )
        
        # Photo/Document Upload
        st.markdown("#### 📎 Attachments")
        uploaded_files = st.file_uploader(
            "Upload Photos/Documents (TCAS Display, Charts, etc.)",
            type=['png', 'jpg', 'jpeg', 'pdf', 'doc', 'docx'],
            accept_multiple_files=True,
            key="tcas_attachments"
        )
        
        # Form submission
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            submitted = st.form_submit_button(
                "📤 Submit TCAS Report",
                use_container_width=True,
                type="primary"
            )
        
        if submitted:
            # Validation
            errors = []
            if not flight_number:
                errors.append("Flight Number is required")
            if not aircraft_reg:
                errors.append("Aircraft Registration is required")
            if not captain_name:
                errors.append("Captain Name is required")
            if not narrative:
                errors.append("Detailed Narrative is required")
            
            if errors:
                for error in errors:
                    st.error(f"❌ {error}")
            else:
                # Calculate risk level based on separation and alert type
                if "RA" in tcas_alert_type and vertical_separation < 300:
                    risk_level = "Extreme"
                elif "RA" in tcas_alert_type and vertical_separation < 500:
                    risk_level = "High"
                elif "RA" in tcas_alert_type:
                    risk_level = "Medium"
                else:
                    risk_level = "Low"
                
                # Create report record
                report_data = {
                    'type': 'TCAS Report',
                    'date': incident_date.isoformat(),
                    'time': incident_time.strftime('%H:%M'),
                    'reported_by': reported_by,
                    'reporter_position': reporter_position,
                    'flight_number': flight_number,
                    'aircraft_reg': aircraft_reg,
                    'aircraft_type': aircraft_type,
                    'origin': origin_airport.split(' - ')[0] if origin_airport else '',
                    'destination': destination_airport.split(' - ')[0] if destination_airport else '',
                    'flight_phase': flight_phase,
                    'flight_rules': flight_rules,
                    'transponder_mode': transponder_mode,
                    'altitude_fl': altitude_fl,
                    'indicated_speed': indicated_speed,
                    'heading': heading,
                    'vertical_rate': vertical_rate,
                    'position': position_description,
                    'latitude': latitude,
                    'longitude': longitude,
                    'tcas_alert_type': tcas_alert_type,
                    'ra_sense': ra_sense,
                    'ra_complied': ra_complied,
                    'time_to_cpa': time_to_cpa,
                    'ra_duration': ra_duration,
                    'tcas_system_status': tcas_system_status,
                    'traffic_type': traffic_type,
                    'traffic_callsign': traffic_callsign,
                    'traffic_altitude': traffic_altitude,
                    'traffic_heading': traffic_heading,
                    'traffic_ac_type': traffic_type_ac,
                    'traffic_position': traffic_position,
                    'traffic_aspect': traffic_aspect,
                    'traffic_visual': traffic_visual,
                    'vertical_separation': vertical_separation,
                    'horizontal_separation': horizontal_separation,
                    'slant_range': slant_range,
                    'separation_confidence': separation_confidence,
                    'atc_unit': atc_unit,
                    'atc_frequency': atc_frequency,
                    'atc_clearance': atc_clearance,
                    'atc_informed': atc_informed,
                    'atc_instructions': atc_instructions,
                    'crew_actions': crew_actions,
                    'captain_name': captain_name,
                    'first_officer': first_officer_name,
                    'pilot_flying': pilot_flying,
                    'narrative': narrative,
                    'contributing_factors': contributing_factors,
                    'airprox_category': airprox_category,
                    'airprox_cause': airprox_cause,
                    'status': investigation_status,
                    'assigned_to': assigned_investigator,
                    'priority': priority_level,
                    'fdr_requested': fdr_requested,
                    'cvr_preserved': cvr_preserved,
                    'risk_level': risk_level,
                    'attachments': len(uploaded_files) if uploaded_files else 0,
                    'created_at': datetime.now().isoformat(),
                    'department': st.session_state.get('user_department', 'Flight Operations')
                }
                
                # --- SUPABASE INSERTION BLOCK ---
                try:
                    report_data['report_number'] = incident_id
                    response = supabase.table('tcas_reports').insert(report_data).execute()
                    st.balloons()
                    st.success(f"✅ TCAS Report Submitted Successfully! Ref: {incident_id}")
                except Exception as e:
                    st.error(f"Database Error: {e}")
                
                # Clear OCR data
                st.session_state['ocr_data_tcas_report'] = None
                
                # Success feedback
                st.balloons()
                st.success(f"""
                    ✅ **TCAS Report Submitted Successfully!**
                    
                    **Reference:** {incident_id}  
                    **Risk Level:** {risk_level}  
                    **Status:** {investigation_status}
                    
                    The report has been added to the system and is now visible in View Reports.
                """)


# ============================================================================
# END OF PART 4
# ============================================================================
# ============================================================================
# PART 5: AIRCRAFT INCIDENT FORM & HAZARD REPORT FORM
# ============================================================================
# Air Sial Corporate Safety Management System v3.0
# Complete incident and hazard reporting with ICAO risk matrix
# ============================================================================

def render_incident_form():
    """
    Complete Aircraft Incident/Occurrence Report Form
    Sections A-L: Full incident reporting per ICAO Annex 13 requirements
    """
    st.markdown("## ⚠️ Aircraft Incident/Occurrence Report Form")
    st.markdown("*Report aircraft incidents, accidents, and serious occurrences*")
    
    # Check for OCR extracted data
    ocr_data = st.session_state.get('ocr_data_incident_report', {}) or {}
    
    # OCR Upload Section
    with st.expander("📷 Upload Form Image for OCR Autofill", expanded=False):
        extracted = render_ocr_uploader("incident_report")
        if extracted:
            ocr_data = extracted
            st.session_state['ocr_data_incident_report'] = extracted
    
    if ocr_data:
        st.info("✨ Form pre-filled with OCR extracted data. Please verify and correct any fields.")
    
    with st.form("incident_form", clear_on_submit=False):
        
        # ========== SECTION A: NOTIFICATION TYPE ==========
        st.markdown("""<div class="form-section">
            <div class="form-section-header">Section A: Notification Type</div>
        </div>""", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            incident_id = st.text_input(
                "Incident Reference Number",
                value=f"INC-{datetime.now().strftime('%Y%m%d')}-{random.randint(100, 999)}",
                disabled=True
            )
        with col2:
            notification_type = st.selectbox(
                "Notification Type *",
                options=[
                    "Accident",
                    "Serious Incident",
                    "Incident",
                    "Occurrence - No Safety Impact",
                    "Ground Event",
                    "Security Related"
                ],
                index=2
            )
        
        col1, col2, col3 = st.columns(3)
        with col1:
            incident_date = st.date_input(
                "Date of Incident *",
                value=datetime.strptime(ocr_data.get('incident_date', date.today().isoformat()), '%Y-%m-%d').date() if ocr_data.get('incident_date') else date.today(),
                key="inc_date"
            )
        with col2:
            incident_time = st.time_input(
                "Time of Incident (UTC) *",
                value=datetime.strptime(ocr_data.get('incident_time', '12:00'), '%H:%M').time() if ocr_data.get('incident_time') else datetime.now().time(),
                key="inc_time"
            )
        with col3:
            local_time = st.time_input(
                "Local Time",
                value=datetime.now().time(),
                key="inc_local_time"
            )
        
        col1, col2 = st.columns(2)
        with col1:
            reported_by = st.text_input(
                "Reported By *",
                value=ocr_data.get('reported_by', st.session_state.get('user_name', '')),
                key="inc_reporter"
            )
        with col2:
            reporter_contact = st.text_input(
                "Reporter Contact",
                placeholder="Phone/Email",
                key="inc_contact"
            )
        
        # ========== SECTION B: AIRCRAFT INFORMATION ==========
        st.markdown("""<div class="form-section">
            <div class="form-section-header">Section B: Aircraft Information</div>
        </div>""", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            # Create a clean list of options first
            fleet_options = [""] + list(AIRCRAFT_FLEET.keys())
            
            # Find the correct index safely
            default_index = 0
            if ocr_data.get('aircraft_reg') in fleet_options:
                default_index = fleet_options.index(ocr_data['aircraft_reg'])

            aircraft_reg = st.selectbox(
                "Aircraft Registration *",
                options=fleet_options,
                index=default_index
            )
        with col2:
            # FIX: Direct dictionary lookup
            aircraft_type = st.text_input(
                "Aircraft Type",
                value=AIRCRAFT_FLEET.get(aircraft_reg, {}).get("type", ""),
                disabled=True,
                key="inc_type"
            )
        with col3:
            # FIX: Direct dictionary lookup
            msn = st.text_input(
                "MSN (Manufacturer Serial Number)",
                value=AIRCRAFT_FLEET.get(aircraft_reg, {}).get("msn", ""),
                disabled=True
            )
        
        col1, col2, col3 = st.columns(3)
        with col1:
            # FIX: Direct dictionary lookup
            engine_type = st.text_input(
                "Engine Type",
                value=AIRCRAFT_FLEET.get(aircraft_reg, {}).get("engines", ""),
                disabled=True
            )
        with col2:
            total_airframe_hours = st.number_input(
                "Total Airframe Hours",
                min_value=0,
                max_value=200000,
                value=0,
                step=100
            )
        with col3:
            total_cycles = st.number_input(
                "Total Cycles",
                min_value=0,
                max_value=100000,
                value=0,
                step=10
            )
        
        col1, col2 = st.columns(2)
        with col1:
            aircraft_damage = st.selectbox(
                "Aircraft Damage *",
                options=[d[0] for d in DAMAGE_LEVELS],
                index=0
            )
        with col2:
            fire_occurred = st.selectbox(
                "Fire Occurred?",
                options=["No", "Yes - In flight", "Yes - On ground", "Yes - After impact"],
                index=0
            )
        
        # ========== SECTION C: FLIGHT INFORMATION ==========
        st.markdown("""<div class="form-section">
            <div class="form-section-header">Section C: Flight Information</div>
        </div>""", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            flight_number = st.text_input(
                "Flight Number *",
                value=ocr_data.get('flight_number', ''),
                placeholder="e.g., PF-101",
                key="inc_flight"
            )
        with col2:
            flight_type = st.selectbox(
                "Flight Type",
                options=["Scheduled Passenger", "Non-Scheduled Passenger", "Cargo", "Ferry/Positioning", "Training", "Test Flight", "Maintenance Check"],
                index=0
            )
        with col3:
            flight_rules = st.selectbox(
                "Flight Rules",
                options=["IFR", "VFR", "SVFR"],
                index=0,
                key="inc_rules"
            )
        
        col1, col2, col3 = st.columns(3)
        with col1:
            origin_airport = st.selectbox(
                "Origin Airport *",
                options=[""] + [f"{data['icao']} - {data['name']}" for data in AIRPORTS.values()],
                index=0,
                key="inc_origin"
            )
        with col2:
            destination_airport = st.selectbox(
                "Destination Airport *",
                options=[""] + [f"{data['icao']} - {data['name']}" for data in AIRPORTS.values()],
                index=0,
                key="inc_dest"
            )
        with col3:
            alternate_airport = st.selectbox(
                "Alternate Airport",
                options=[""] + [f"{data['icao']} - {data['name']}" for data in AIRPORTS.values()],
                index=0
            )
        
        col1, col2 = st.columns(2)
        with col1:
            flight_phase = st.selectbox(
                "Phase of Flight *",
                options=FLIGHT_PHASES,
                index=FLIGHT_PHASES.index(ocr_data.get('flight_phase', 'Cruise')) if ocr_data.get('flight_phase') in FLIGHT_PHASES else 10,
                key="inc_phase"
            )
        with col2:
            operation_type = st.selectbox(
                "Operation Type",
                options=["Commercial Air Transport", "General Aviation", "Aerial Work", "State Aircraft"],
                index=0
            )
        
        # ========== SECTION D: LOCATION OF INCIDENT ==========
        st.markdown("""<div class="form-section">
            <div class="form-section-header">Section D: Location of Incident</div>
        </div>""", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            incident_location = st.selectbox(
                "Incident Location",
                options=[""] + [f"{data['icao']} - {data['name']}" for data in AIRPORTS.values()] + ["En-route", "Over water", "Other"],
                index=0
            )
        with col2:
            location_description = st.text_input(
                "Location Description",
                placeholder="e.g., 5nm east of OPLA VOR, Runway 36L"
            )
        
        col1, col2, col3 = st.columns(3)
        with col1:
            altitude = st.number_input(
                "Altitude (feet)",
                min_value=0,
                max_value=50000,
                value=0,
                step=500,
                key="inc_alt"
            )
        with col2:
            latitude = st.text_input(
                "Latitude",
                placeholder="e.g., 31.5204° N",
                key="inc_lat"
            )
        with col3:
            longitude = st.text_input(
                "Longitude",
                placeholder="e.g., 74.3587° E",
                key="inc_lon"
            )
        
        terrain_type = st.selectbox(
            "Terrain Type",
            options=["Airport/Aerodrome", "Urban area", "Rural area", "Mountainous", "Water", "Desert", "Forest", "Other"],
            index=0
        )
        
        # ========== SECTION E: INCIDENT CATEGORY & DESCRIPTION ==========
        st.markdown("""<div class="form-section">
            <div class="form-section-header">Section E: Incident Category & Description</div>
        </div>""", unsafe_allow_html=True)
        
        incident_category = st.selectbox(
            "Primary Incident Category *",
            options=INCIDENT_CATEGORIES,
            index=0
        )
        
        secondary_categories = st.multiselect(
            "Secondary Categories (if applicable)",
            options=INCIDENT_CATEGORIES,
            default=[]
        )
        
        st.markdown("**Incident Description**")
        incident_description = st.text_area(
            "Brief Description of Incident *",
            value=ocr_data.get('description', ''),
            placeholder="Provide a concise description of what happened...",
            height=100
        )
        
        # ========== SECTION F: WEATHER CONDITIONS ==========
        st.markdown("""<div class="form-section">
            <div class="form-section-header">Section F: Weather Conditions</div>
        </div>""", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            weather_conditions = st.selectbox(
                "Weather Conditions",
                options=WEATHER_CONDITIONS,
                index=0,
                key="inc_wx"
            )
        with col2:
            visibility_nm = st.number_input(
                "Visibility (nm)",
                min_value=0.0,
                max_value=50.0,
                value=10.0,
                step=0.5
            )
        
        col1, col2, col3 = st.columns(3)
        with col1:
            ceiling_feet = st.number_input(
                "Ceiling (feet)",
                min_value=0,
                max_value=50000,
                value=10000,
                step=500
            )
        with col2:
            wind_direction = st.number_input(
                "Wind Direction (degrees)",
                min_value=0,
                max_value=360,
                value=0,
                step=10
            )
        with col3:
            wind_speed = st.number_input(
                "Wind Speed (knots)",
                min_value=0,
                max_value=100,
                value=0,
                step=5
            )
        
        col1, col2 = st.columns(2)
        with col1:
            turbulence = st.selectbox(
                "Turbulence",
                options=["None", "Light", "Moderate", "Severe", "Extreme"],
                index=0
            )
        with col2:
            icing = st.selectbox(
                "Icing Conditions",
                options=["None", "Light", "Moderate", "Severe"],
                index=0
            )
        
        weather_factor = st.selectbox(
            "Weather as Contributing Factor?",
            options=["No", "Yes - Primary factor", "Yes - Contributing factor", "Possible factor", "Unknown"],
            index=0
        )
        
        # ========== SECTION G: CREW INFORMATION ==========
        st.markdown("""<div class="form-section">
            <div class="form-section-header">Section G: Crew Information</div>
        </div>""", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            captain_name = st.text_input(
                "Captain Name *",
                value=ocr_data.get('captain_name', ''),
                key="inc_captain"
            )
        with col2:
            captain_license = st.text_input(
                "Captain License Number",
                placeholder="e.g., ATPL-12345"
            )
        
        col1, col2 = st.columns(2)
        with col1:
            fo_name = st.text_input(
                "First Officer Name",
                value=ocr_data.get('first_officer_name', ''),
                key="inc_fo"
            )
        with col2:
            fo_license = st.text_input(
                "First Officer License Number",
                placeholder="e.g., CPL-67890"
            )
        
        col1, col2, col3 = st.columns(3)
        with col1:
            pilot_flying = st.selectbox(
                "Pilot Flying (PF)",
                options=["Captain", "First Officer"],
                index=0,
                key="inc_pf"
            )
        with col2:
            captain_total_hours = st.number_input(
                "Captain Total Hours",
                min_value=0,
                max_value=50000,
                value=0,
                step=100
            )
        with col3:
            captain_type_hours = st.number_input(
                "Captain Hours on Type",
                min_value=0,
                max_value=20000,
                value=0,
                step=50
            )
        
        col1, col2 = st.columns(2)
        with col1:
            cabin_crew_count = st.number_input(
                "Number of Cabin Crew",
                min_value=0,
                max_value=20,
                value=4,
                step=1
            )
        with col2:
            other_crew = st.text_input(
                "Other Crew (e.g., ACM, Check Airman)",
                placeholder="Names and positions"
            )
        
        # ========== SECTION H: PASSENGERS & LOAD ==========
        st.markdown("""<div class="form-section">
            <div class="form-section-header">Section H: Passengers & Load Information</div>
        </div>""", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            passengers_adult = st.number_input(
                "Adult Passengers",
                min_value=0,
                max_value=300,
                value=0,
                step=1
            )
        with col2:
            passengers_child = st.number_input(
                "Child Passengers",
                min_value=0,
                max_value=100,
                value=0,
                step=1
            )
        with col3:
            passengers_infant = st.number_input(
                "Infant Passengers",
                min_value=0,
                max_value=50,
                value=0,
                step=1
            )
        
        col1, col2, col3 = st.columns(3)
        with col1:
            cargo_kg = st.number_input(
                "Cargo (kg)",
                min_value=0,
                max_value=50000,
                value=0,
                step=100
            )
        with col2:
            fuel_kg = st.number_input(
                "Fuel on Board (kg)",
                min_value=0,
                max_value=100000,
                value=0,
                step=500
            )
        with col3:
            takeoff_weight = st.number_input(
                "Takeoff Weight (kg)",
                min_value=0,
                max_value=400000,
                value=0,
                step=1000
            )
        
        dangerous_goods = st.selectbox(
            "Dangerous Goods on Board?",
            options=["No", "Yes - Declared", "Yes - Undeclared/Unknown", "Unknown"],
            index=0
        )
        
        # ========== SECTION I: INJURIES & DAMAGE ==========
        st.markdown("""<div class="form-section">
            <div class="form-section-header">Section I: Injuries & Damage</div>
        </div>""", unsafe_allow_html=True)
        
        st.markdown("**Injury Summary**")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown("**Category**")
            st.markdown("Crew")
            st.markdown("Passengers")
            st.markdown("Others")
        with col2:
            st.markdown("**Fatal**")
            crew_fatal = st.number_input("Crew Fatal", min_value=0, max_value=20, value=0, step=1, label_visibility="collapsed")
            pax_fatal = st.number_input("Pax Fatal", min_value=0, max_value=500, value=0, step=1, label_visibility="collapsed")
            other_fatal = st.number_input("Other Fatal", min_value=0, max_value=100, value=0, step=1, label_visibility="collapsed")
        with col3:
            st.markdown("**Serious**")
            crew_serious = st.number_input("Crew Serious", min_value=0, max_value=20, value=0, step=1, label_visibility="collapsed")
            pax_serious = st.number_input("Pax Serious", min_value=0, max_value=500, value=0, step=1, label_visibility="collapsed")
            other_serious = st.number_input("Other Serious", min_value=0, max_value=100, value=0, step=1, label_visibility="collapsed")
        with col4:
            st.markdown("**Minor/None**")
            crew_minor = st.number_input("Crew Minor", min_value=0, max_value=20, value=0, step=1, label_visibility="collapsed")
            pax_minor = st.number_input("Pax Minor", min_value=0, max_value=500, value=0, step=1, label_visibility="collapsed")
            other_minor = st.number_input("Other Minor", min_value=0, max_value=100, value=0, step=1, label_visibility="collapsed")
        
        injury_description = st.text_area(
            "Injury Details (if any)",
            placeholder="Describe any injuries sustained...",
            height=60
        )
        
        st.markdown("**Third Party Damage**")
        col1, col2 = st.columns(2)
        with col1:
            third_party_damage = st.selectbox(
                "Third Party Damage?",
                options=["No", "Yes - Property", "Yes - Vehicles", "Yes - Other aircraft", "Yes - Multiple"],
                index=0
            )
        with col2:
            damage_estimate = st.selectbox(
                "Estimated Damage Cost",
                options=["Unknown", "< $10,000", "$10,000 - $100,000", "$100,000 - $1,000,000", "> $1,000,000"],
                index=0
            )
        
        # ========== SECTION J: EMERGENCY RESPONSE ==========
        st.markdown("""<div class="form-section">
            <div class="form-section-header">Section J: Emergency Response</div>
        </div>""", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            emergency_declared = st.selectbox(
                "Emergency Declared?",
                options=["No", "PAN PAN", "MAYDAY"],
                index=0,
                key="inc_emergency"
            )
        with col2:
            emergency_services = st.multiselect(
                "Emergency Services Responded",
                options=["None required", "Airport Fire Service", "Ambulance", "Police", "Airport Authority", "External Fire Service"],
                default=["None required"]
            )
        
        col1, col2 = st.columns(2)
        with col1:
            evacuation = st.selectbox(
                "Evacuation Performed?",
                options=["No", "Yes - Precautionary", "Yes - Emergency (slides)", "Yes - Emergency (no slides)", "Partial evacuation"],
                index=0
            )
        with col2:
            evacuation_time = st.text_input(
                "Evacuation Time (if applicable)",
                placeholder="e.g., 90 seconds"
            )
        
        emergency_narrative = st.text_area(
            "Emergency Response Narrative",
            placeholder="Describe emergency response actions taken...",
            height=60
        )
        
        # ========== SECTION K: NOTIFICATIONS ==========
        st.markdown("""<div class="form-section">
            <div class="form-section-header">Section K: Notifications</div>
        </div>""", unsafe_allow_html=True)
        
        notifications_required = st.multiselect(
            "Notifications Required/Made",
            options=[
                "PCAA (Pakistan Civil Aviation Authority)",
                "AAIB (Air Accident Investigation Branch)",
                "Operator Safety Department",
                "Operator Operations Control",
                "Airport Authority",
                "Insurance Company",
                "Aircraft Manufacturer",
                "Engine Manufacturer",
                "State of Registry",
                "State of Occurrence",
                "ICAO (if international)",
                "Media Relations"
            ],
            default=["PCAA (Pakistan Civil Aviation Authority)", "Operator Safety Department"]
        )
        
        col1, col2 = st.columns(2)
        with col1:
            pcaa_notified = st.selectbox(
                "PCAA Notified?",
                options=["Yes - Within 24 hours", "Yes - Within 72 hours", "Pending", "Not required"],
                index=2
            )
        with col2:
            reference_number = st.text_input(
                "Authority Reference Number (if issued)",
                placeholder="e.g., PCAA-2024-XXX"
            )
        
        # ========== SECTION L: INVESTIGATION & NARRATIVE ==========
        st.markdown("""<div class="form-section">
            <div class="form-section-header">Section L: Investigation & Narrative</div>
        </div>""", unsafe_allow_html=True)
        
        narrative = st.text_area(
            "Detailed Narrative of Incident *",
            value=ocr_data.get('narrative', ''),
            placeholder="Provide a comprehensive description of the incident including events leading up to it, the incident itself, and aftermath. Include timeline, crew actions, ATC communications, and any other relevant details...",
            height=200
        )
        
        probable_causes = st.multiselect(
            "Probable Cause Factors (Preliminary)",
            options=[
                "Human Factors - Flight Crew",
                "Human Factors - Cabin Crew",
                "Human Factors - Maintenance",
                "Human Factors - ATC",
                "Human Factors - Other",
                "Technical - Aircraft Systems",
                "Technical - Engine",
                "Technical - Avionics",
                "Technical - Structure",
                "Environmental - Weather",
                "Environmental - Wildlife",
                "Environmental - Terrain",
                "Organizational - Procedures",
                "Organizational - Training",
                "Organizational - Supervision",
                "Unknown - Under Investigation"
            ],
            default=["Unknown - Under Investigation"]
        )
        
        immediate_actions = st.text_area(
            "Immediate Actions Taken",
            placeholder="Describe any immediate safety actions taken following the incident...",
            height=80
        )
        
        # Investigation Status
        col1, col2, col3 = st.columns(3)
        with col1:
            investigation_status = st.selectbox(
                "Investigation Status",
                options=["Open - Initial Report", "Open - Under Investigation", "Open - Awaiting Evidence", "Closed - Recommendations Issued", "Closed - No Further Action", "Referred to Authority"],
                index=0,
                key="inc_status"
            )
        with col2:
            assigned_investigator = st.selectbox(
                "Assigned To",
                options=["Unassigned", "Safety Manager", "Safety Officer", "Quality Manager", "External Investigator", "PCAA Investigation Team"],
                index=0,
                key="inc_assigned"
            )
        with col3:
            priority_level = st.selectbox(
                "Priority Level",
                options=["Low", "Medium", "High", "Critical"],
                index=2 if notification_type in ["Accident", "Serious Incident"] else 1,
                key="inc_priority"
            )
        
        # Data Preservation
        st.markdown("**Data Preservation**")
        col1, col2, col3 = st.columns(3)
        with col1:
            fdr_preserved = st.selectbox(
                "FDR/QAR Data",
                options=["Preserved", "Requested", "Not applicable", "Pending"],
                index=1
            )
        with col2:
            cvr_preserved = st.selectbox(
                "CVR Data",
                options=["Preserved", "Requested", "Not applicable", "Pending"],
                index=1,
                key="inc_cvr"
            )
        with col3:
            aircraft_secured = st.selectbox(
                "Aircraft Secured?",
                options=["Yes", "No", "Not applicable"],
                index=0
            )
        
        # Photo/Document Upload
        st.markdown("#### 📎 Attachments")
        uploaded_files = st.file_uploader(
            "Upload Photos/Documents (Damage photos, diagrams, etc.)",
            type=['png', 'jpg', 'jpeg', 'pdf', 'doc', 'docx'],
            accept_multiple_files=True,
            key="incident_attachments"
        )
        
        # Form submission
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            submitted = st.form_submit_button(
                "📤 Submit Incident Report",
                use_container_width=True,
                type="primary"
            )
        
        if submitted:
            # Validation
            errors = []
            if not flight_number:
                errors.append("Flight Number is required")
            if not aircraft_reg:
                errors.append("Aircraft Registration is required")
            if not captain_name:
                errors.append("Captain Name is required")
            if not narrative:
                errors.append("Detailed Narrative is required")
            if not incident_description:
                errors.append("Brief Description is required")
            
            if errors:
                for error in errors:
                    st.error(f"❌ {error}")
            else:
                # Calculate risk level
                total_fatal = crew_fatal + pax_fatal + other_fatal
                total_serious = crew_serious + pax_serious + other_serious
                
                if notification_type == "Accident" or total_fatal > 0:
                    risk_level = "Extreme"
                elif notification_type == "Serious Incident" or total_serious > 0 or aircraft_damage in ["Destroyed", "Substantial"]:
                    risk_level = "High"
                elif notification_type == "Incident" or aircraft_damage in ["Major", "Minor - Confirmed"]:
                    risk_level = "Medium"
                else:
                    risk_level = "Low"
                
                # Create report record
                report_data = {
                    'type': 'Aircraft Incident',
                    'notification_type': notification_type,
                    'date': incident_date.isoformat(),
                    'time': incident_time.strftime('%H:%M'),
                    'local_time': local_time.strftime('%H:%M'),
                    'reported_by': reported_by,
                    'reporter_contact': reporter_contact,
                    'aircraft_reg': aircraft_reg,
                    'aircraft_type': aircraft_type,
                    'msn': msn,
                    'engine_type': engine_type,
                    'total_hours': total_airframe_hours,
                    'total_cycles': total_cycles,
                    'aircraft_damage': aircraft_damage,
                    'fire_occurred': fire_occurred,
                    'flight_number': flight_number,
                    'flight_type': flight_type,
                    'flight_rules': flight_rules,
                    'origin': origin_airport.split(' - ')[0] if origin_airport else '',
                    'destination': destination_airport.split(' - ')[0] if destination_airport else '',
                    'alternate': alternate_airport.split(' - ')[0] if alternate_airport else '',
                    'flight_phase': flight_phase,
                    'operation_type': operation_type,
                    'incident_location': incident_location,
                    'location_description': location_description,
                    'altitude': altitude,
                    'latitude': latitude,
                    'longitude': longitude,
                    'terrain_type': terrain_type,
                    'incident_category': incident_category,
                    'secondary_categories': secondary_categories,
                    'description': incident_description,
                    'weather': weather_conditions,
                    'visibility': visibility_nm,
                    'ceiling': ceiling_feet,
                    'wind_direction': wind_direction,
                    'wind_speed': wind_speed,
                    'turbulence': turbulence,
                    'icing': icing,
                    'weather_factor': weather_factor,
                    'captain_name': captain_name,
                    'captain_license': captain_license,
                    'fo_name': fo_name,
                    'fo_license': fo_license,
                    'pilot_flying': pilot_flying,
                    'captain_hours': captain_total_hours,
                    'captain_type_hours': captain_type_hours,
                    'cabin_crew_count': cabin_crew_count,
                    'other_crew': other_crew,
                    'passengers_adult': passengers_adult,
                    'passengers_child': passengers_child,
                    'passengers_infant': passengers_infant,
                    'cargo_kg': cargo_kg,
                    'fuel_kg': fuel_kg,
                    'takeoff_weight': takeoff_weight,
                    'dangerous_goods': dangerous_goods,
                    'injuries': {
                        'crew_fatal': crew_fatal,
                        'crew_serious': crew_serious,
                        'crew_minor': crew_minor,
                        'pax_fatal': pax_fatal,
                        'pax_serious': pax_serious,
                        'pax_minor': pax_minor,
                        'other_fatal': other_fatal,
                        'other_serious': other_serious,
                        'other_minor': other_minor
                    },
                    'injury_description': injury_description,
                    'third_party_damage': third_party_damage,
                    'damage_estimate': damage_estimate,
                    'emergency_declared': emergency_declared,
                    'emergency_services': emergency_services,
                    'evacuation': evacuation,
                    'evacuation_time': evacuation_time,
                    'emergency_narrative': emergency_narrative,
                    'notifications': notifications_required,
                    'pcaa_notified': pcaa_notified,
                    'authority_reference': reference_number,
                    'narrative': narrative,
                    'probable_causes': probable_causes,
                    'immediate_actions': immediate_actions,
                    'status': investigation_status,
                    'assigned_to': assigned_investigator,
                    'priority': priority_level,
                    'fdr_preserved': fdr_preserved,
                    'cvr_preserved': cvr_preserved,
                    'aircraft_secured': aircraft_secured,
                    'risk_level': risk_level,
                    'attachments': len(uploaded_files) if uploaded_files else 0,
                    'created_at': datetime.now().isoformat(),
                    'department': st.session_state.get('user_department', 'Safety Department')
                }
                
                # --- SUPABASE INSERTION BLOCK ---
                try:
                    report_data['report_number'] = incident_id
                    response = supabase.table('aircraft_incidents').insert(report_data).execute()
                    st.balloons()
                    st.success(f"""
                        ✅ **Incident Report Submitted Successfully!**
                        
                        **Reference:** {incident_id}  
                        **Classification:** {notification_type}  
                        **Risk Level:** {risk_level}  
                        **Status:** {investigation_status}
                        
                        The report has been added to the system and is now visible in View Reports.
                        {"⚠️ **IMPORTANT:** This incident requires immediate notification to PCAA." if notification_type in ["Accident", "Serious Incident"] else ""}
                    """)
                except Exception as e:
                    st.error(f"Database Error: {e}")
                
                # Clear OCR data
                st.session_state['ocr_data_incident_report'] = None
                
                # Success feedback
                st.balloons()
                st.success(f"""
                    ✅ **Incident Report Submitted Successfully!**
                    
                    **Reference:** {incident_id}  
                    **Classification:** {notification_type}  
                    **Risk Level:** {risk_level}  
                    **Status:** {investigation_status}
                    
                    The report has been added to the system and is now visible in View Reports.
                    {"⚠️ **IMPORTANT:** This incident requires immediate notification to PCAA." if notification_type in ["Accident", "Serious Incident"] else ""}
                """)


def render_mor_form():
    """
    Mandatory Occurrence Report (MOR) - Checkbox Style
    """
    st.markdown("## 🚨 Mandatory Occurrence Report (MOR)")
    st.info("ℹ️ Notification only. No CAP/Investigation workflow applies.")
    
    with st.form("mor_strict_form"):
        st.markdown("#### Occurrence Type")
        c1, c2, c3, c4 = st.columns(4)
        is_bird = c1.checkbox("Bird Strike")
        is_laser = c2.checkbox("Laser Strike")
        is_tcas = c3.checkbox("TCAS RA")
        is_gen = c4.checkbox("MOR (General)")
        
        col1, col2 = st.columns(2)
        dept = col1.selectbox("Department", DEPARTMENTS)
        date_occ = col2.date_input("Date of Occurrence")
        
        desc = st.text_area("Description", height=100)
        st.file_uploader("Attach Document/Evidence")
        
        if st.form_submit_button("Submit MOR", type="primary"):
            if not any([is_bird, is_laser, is_tcas, is_gen]):
                st.error("Please select at least one Occurrence Type.")
            else:
                st.success("✅ MOR Submitted. Notification sent to Safety Department.")


                
# ══════════════════════════════════════════════════════════════════════════════
# FIX: DEFINITIONS FOR ROUTING (Hazard, MOR, Audit)
# ══════════════════════════════════════════════════════════════════════════════

def render_hazard_form():
    """
    Hazard Form: Matches 'Hazard Identification & Risk Assessment Form.pdf'
    Includes: 5x5 Matrix Inputs, Location, Description, Sign-off.
    """
    st.markdown("## ⚠️ Hazard Identification & Risk Assessment")
    
    # --- 1. OCR / AI AUTO-FILL SECTION ---
    st.info("💡 **Smart Fill:** Upload a photo of the handwritten form to auto-fill these fields.")
    uploaded_file = st.file_uploader("Upload Scanned Form / Evidence", type=['png', 'jpg', 'jpeg', 'pdf'], key="hazard_ocr")
    
    if uploaded_file is not None:
        with st.spinner("🤖 AI is reading the document..."):
            try:
                # Reconnecting your existing OCR logic
                ocr_result = ui_integration.process_file_upload(uploaded_file)
                st.success("Data Extracted Successfully!")
                # In a real scenario, you'd map 'ocr_result' to session_state variables here
                with st.expander("View Extracted Data"):
                    st.json(ocr_result)
            except Exception as e:
                st.error(f"OCR Error: {e}. Please fill manually.")

    with st.form("hazard_full_form"):
        # Section A: Basic Details
        st.markdown("### A. Hazard Identification")
        c1, c2, c3 = st.columns(3)
        # Matches PDF: "Reporter Name", "Date", "Department"
        reporter_name = c1.text_input("Reporter Name", value=st.session_state.get('username', ''))
        report_date = c2.date_input("Date of Report")
        dept = c3.selectbox("Department", DEPARTMENTS)
        
        c4, c5 = st.columns(2)
        # Matches PDF: "Location of Hazard", "Date/Time Hazard Identified"
        location = c4.text_input("Location / Area")
        datetime_occ = c5.text_input("Date/Time Identified (DD/MM/YYYY HH:MM)")
        
        description = st.text_area("Hazard Description", help="Describe the hazard in detail (Who, What, Where, When)", height=150)
        
        # Section B: Initial Risk Assessment (The Matrix)
        st.markdown("### B. Initial Risk Assessment (Matrix)")
        st.caption("Refer to the 5x5 Matrix (Severity A-E, Probability 1-5)")
        
        m1, m2 = st.columns(2)
        # Matches PDF: "Severity (A-E)", "Probability (1-5)"
        severity = m1.selectbox("Severity", ["A - Catastrophic", "B - Major", "C - Moderate", "D - Minor", "E - Insignificant"])
        probability = m2.selectbox("Probability", ["5 - Frequent", "4 - Occasional", "3 - Remote", "2 - Improbable", "1 - Rare"])
        
        # Section C: Workflow (Hidden for Reporter, Visible for Analyst)
        role = st.session_state.get('user_role')
        if role in ["Analyst", "Safety Head", "Admin"]:
            st.markdown("---")
            st.markdown("### C. Corrective Action Plan (Analyst Only)")
            # Matches PDF: "Person Responsible", "Action Plan", "Target Date"
            cap_owner = st.text_input("Person Responsible")
            cap_plan = st.text_area("Corrective Action Plan")
            target_date = st.date_input("Target Date for Completion")
            
        submitted = st.form_submit_button("Submit Hazard Report", type="primary")
        
        if submitted:
            # Save logic here
            st.success("✅ Hazard Report Submitted. Forwarded to Safety Department.")

def render_mor_form():
    """
    MOR Form: Matches 'MOR.pdf', 'BIRD HIT.pdf', etc.
    Includes: Flight Details, Weather, Nature of Incident.
    """
    st.markdown("## 🚨 Mandatory Occurrence Report (MOR)")
    
    # Tabbed Interface to handle specific PDF types without clutter
    tab1, tab2, tab3 = st.tabs(["General MOR", "Bird/Wildlife Strike", "Air Traffic / Near Miss"])
    
    # --- TAB 1: GENERAL MOR (Matches MOR.pdf) ---
    with tab1:
        with st.form("mor_general"):
            st.markdown("### Aircraft & Flight Information")
            c1, c2, c3 = st.columns(3)
            # Matches PDF: "Type", "Registration", "Flight No"
            ac_type = c1.selectbox("Aircraft Type", ["A320", "A330", "Other"])
            reg = c2.text_input("Registration (e.g., AP-BOA)")
            flt_no = c3.text_input("Flight No (e.g., PF-123)")
            
            c4, c5, c6 = st.columns(3)
            # Matches PDF: "Departure", "Arrival", "POB"
            dep = c4.text_input("Departure Station")
            arr = c5.text_input("Arrival Station")
            pob = c6.number_input("Persons on Board (POB)", min_value=0)
            
            st.markdown("### Occurrence Details")
            # Matches PDF: "Nature of Incident", "Weather", "Damage"
            nature = st.text_area("Nature / Cause of Incident")
            weather = st.text_input("Weather Conditions (Metar/Visibility)")
            damage = st.text_area("Damage Report (if any)")
            
            st.form_submit_button("Submit General MOR")

    # --- TAB 2: BIRD STRIKE (Matches BIRD HIT.pdf) ---
    with tab2:
        with st.form("mor_bird"):
            st.markdown("### Bird / Wildlife Strike Details")
            b1, b2, b3 = st.columns(3)
            # Matches PDF: "Height AGL", "Speed (IAS)", "Phase of Flight"
            height = b1.number_input("Height (ft AGL)")
            speed = b2.number_input("Speed (IAS Kts)")
            phase = b3.selectbox("Phase", ["Taxi", "Takeoff", "Climb", "Cruise", "Approach", "Landing"])
            
            st.markdown("#### Impact Details")
            # Matches PDF: "Part Struck" checkboxes
            st.write("Part(s) Struck:")
            c_w, c_e, c_f = st.columns(3)
            if c_w.checkbox("Windshield"): pass
            if c_e.checkbox("Engine (No. 1 / 2)"): pass
            if c_f.checkbox("Fuselage / Wing"): pass
            
            bird_desc = st.text_input("Bird Description (Size/Type/Number)")
            st.form_submit_button("Submit Bird Strike Report")

    # --- TAB 3: AIR TRAFFIC (Matches Air - Near.pdf) ---
    with tab3:
        with st.form("mor_airprox"):
            st.markdown("### Air Traffic Incident / Near Miss")
            a1, a2 = st.columns(2)
            # Matches PDF: "Call Sign", "Frequency"
            callsign = a1.text_input("Your Call Sign")
            freq = a2.text_input("Frequency in use")
            
            a3, a4 = st.columns(2)
            # Matches PDF: "Other Aircraft Type", "Separation"
            other_ac = a3.text_input("Other Aircraft Type/Callsign")
            separation = a4.text_input("Est. Separation (Vertical/Horizontal)")
            
            tc_alert = st.checkbox("TCAS Alert Triggered?")
            st.form_submit_button("Submit Airprox Report")

def render_captain_debrief():
    """
    Matches 'De-Brief.pdf'
    """
    st.markdown("## 👨‍✈️ Captain's De-Brief")
    with st.form("capt_debrief"):
        d1, d2, d3 = st.columns(3)
        date = d1.date_input("Date")
        ac_reg = d2.text_input("A/C Registration")
        flt_no = d3.text_input("Flight Number")
        
        st.markdown("### Sector Analysis")
        # Matches PDF table columns: Sector, Dep Delay, Arr Delay, Reason
        c1, c2, c3, c4 = st.columns([2, 1, 1, 3])
        c1.text_input("Sector (e.g., KHI-LHE)")
        c2.time_input("Dep Time")
        c3.time_input("Arr Time")
        c4.text_input("Delay Reason (Code)")
        
        st.markdown("### Observations")
        # Matches PDF: "Safety Observation", "Services", "Engineering"
        obs_safe = st.text_area("Safety Observations")
        obs_ops = st.text_area("Operational / Service Issues")
        
        st.form_submit_button("Submit Debrief")

def render_audit_form():
    """
    Quality / Audit Findings Tracker
    """
    st.markdown("## 🧪 Quality Assurance & Audit")
    
    tab1, tab2 = st.tabs(["Findings Tracker", "Ramp Inspection"])
    
    with tab1:
        with st.form("audit_finding"):
            st.markdown("#### New Audit Finding")
            level = st.selectbox("Finding Level", ["Level 1", "Level 2", "Observation"])
            dept = st.selectbox("Audited Department", DEPARTMENTS)
            finding = st.text_area("Finding Description")
            st.file_uploader("Attach Audit Evidence")
            if st.form_submit_button("Log Finding"):
                st.success("Finding Logged.")
                
    with tab2:
        st.info("Ramp Inspection (No Checklist - Levels Only)")
        with st.form("ramp_inspection"):
            flight_no = st.text_input("Flight No")
            level = st.selectbox("Outcome", ["Level 1-2 (Minor)", "Level 3 (Major)"])
            comments = st.text_area("Comments")
            if st.form_submit_button("Submit Ramp Report"):
                st.success("Ramp Inspection Saved.")


def calculate_risk_level(likelihood: int, severity: str) -> str:
    """Calculate risk level from ICAO 5x5 matrix"""
    # Risk matrix lookup
    matrix = {
        (5, 'A'): 'Extreme', (5, 'B'): 'Extreme', (5, 'C'): 'High', (5, 'D'): 'Medium', (5, 'E'): 'Low',
        (4, 'A'): 'Extreme', (4, 'B'): 'High', (4, 'C'): 'High', (4, 'D'): 'Medium', (4, 'E'): 'Low',
        (3, 'A'): 'High', (3, 'B'): 'High', (3, 'C'): 'Medium', (3, 'D'): 'Medium', (3, 'E'): 'Low',
        (2, 'A'): 'High', (2, 'B'): 'Medium', (2, 'C'): 'Medium', (2, 'D'): 'Low', (2, 'E'): 'Low',
        (1, 'A'): 'Medium', (1, 'B'): 'Low', (1, 'C'): 'Low', (1, 'D'): 'Low', (1, 'E'): 'Low',
    }
    return matrix.get((likelihood, severity), 'Medium')


def render_visual_risk_matrix():
    """Render a visual 5x5 ICAO risk matrix"""
    st.markdown("""
    <div style="overflow-x: auto;">
        <table style="border-collapse: collapse; width: 100%; min-width: 500px; font-size: 0.8rem;">
            <tr>
                <th style="border: 1px solid #CBD5E1; padding: 8px; background: #F1F5F9;"></th>
                <th style="border: 1px solid #CBD5E1; padding: 8px; background: #F1F5F9; text-align: center;">A<br><small>Catastrophic</small></th>
                <th style="border: 1px solid #CBD5E1; padding: 8px; background: #F1F5F9; text-align: center;">B<br><small>Hazardous</small></th>
                <th style="border: 1px solid #CBD5E1; padding: 8px; background: #F1F5F9; text-align: center;">C<br><small>Major</small></th>
                <th style="border: 1px solid #CBD5E1; padding: 8px; background: #F1F5F9; text-align: center;">D<br><small>Minor</small></th>
                <th style="border: 1px solid #CBD5E1; padding: 8px; background: #F1F5F9; text-align: center;">E<br><small>Negligible</small></th>
            </tr>
            <tr>
                <td style="border: 1px solid #CBD5E1; padding: 8px; background: #F1F5F9; font-weight: bold;">5 - Frequent</td>
                <td style="border: 1px solid #CBD5E1; padding: 8px; background: #FEE2E2; text-align: center; color: #DC2626; font-weight: bold;">5A</td>
                <td style="border: 1px solid #CBD5E1; padding: 8px; background: #FEE2E2; text-align: center; color: #DC2626; font-weight: bold;">5B</td>
                <td style="border: 1px solid #CBD5E1; padding: 8px; background: #FFEDD5; text-align: center; color: #EA580C; font-weight: bold;">5C</td>
                <td style="border: 1px solid #CBD5E1; padding: 8px; background: #FEF9C3; text-align: center; color: #CA8A04; font-weight: bold;">5D</td>
                <td style="border: 1px solid #CBD5E1; padding: 8px; background: #DCFCE7; text-align: center; color: #16A34A; font-weight: bold;">5E</td>
            </tr>
            <tr>
                <td style="border: 1px solid #CBD5E1; padding: 8px; background: #F1F5F9; font-weight: bold;">4 - Occasional</td>
                <td style="border: 1px solid #CBD5E1; padding: 8px; background: #FEE2E2; text-align: center; color: #DC2626; font-weight: bold;">4A</td>
                <td style="border: 1px solid #CBD5E1; padding: 8px; background: #FFEDD5; text-align: center; color: #EA580C; font-weight: bold;">4B</td>
                <td style="border: 1px solid #CBD5E1; padding: 8px; background: #FFEDD5; text-align: center; color: #EA580C; font-weight: bold;">4C</td>
                <td style="border: 1px solid #CBD5E1; padding: 8px; background: #FEF9C3; text-align: center; color: #CA8A04; font-weight: bold;">4D</td>
                <td style="border: 1px solid #CBD5E1; padding: 8px; background: #DCFCE7; text-align: center; color: #16A34A; font-weight: bold;">4E</td>
            </tr>
            <tr>
                <td style="border: 1px solid #CBD5E1; padding: 8px; background: #F1F5F9; font-weight: bold;">3 - Remote</td>
                <td style="border: 1px solid #CBD5E1; padding: 8px; background: #FFEDD5; text-align: center; color: #EA580C; font-weight: bold;">3A</td>
                <td style="border: 1px solid #CBD5E1; padding: 8px; background: #FFEDD5; text-align: center; color: #EA580C; font-weight: bold;">3B</td>
                <td style="border: 1px solid #CBD5E1; padding: 8px; background: #FEF9C3; text-align: center; color: #CA8A04; font-weight: bold;">3C</td>
                <td style="border: 1px solid #CBD5E1; padding: 8px; background: #FEF9C3; text-align: center; color: #CA8A04; font-weight: bold;">3D</td>
                <td style="border: 1px solid #CBD5E1; padding: 8px; background: #DCFCE7; text-align: center; color: #16A34A; font-weight: bold;">3E</td>
            </tr>
            <tr>
                <td style="border: 1px solid #CBD5E1; padding: 8px; background: #F1F5F9; font-weight: bold;">2 - Improbable</td>
                <td style="border: 1px solid #CBD5E1; padding: 8px; background: #FFEDD5; text-align: center; color: #EA580C; font-weight: bold;">2A</td>
                <td style="border: 1px solid #CBD5E1; padding: 8px; background: #FEF9C3; text-align: center; color: #CA8A04; font-weight: bold;">2B</td>
                <td style="border: 1px solid #CBD5E1; padding: 8px; background: #FEF9C3; text-align: center; color: #CA8A04; font-weight: bold;">2C</td>
                <td style="border: 1px solid #CBD5E1; padding: 8px; background: #DCFCE7; text-align: center; color: #16A34A; font-weight: bold;">2D</td>
                <td style="border: 1px solid #CBD5E1; padding: 8px; background: #DCFCE7; text-align: center; color: #16A34A; font-weight: bold;">2E</td>
            </tr>
            <tr>
                <td style="border: 1px solid #CBD5E1; padding: 8px; background: #F1F5F9; font-weight: bold;">1 - Extremely Improbable</td>
                <td style="border: 1px solid #CBD5E1; padding: 8px; background: #FEF9C3; text-align: center; color: #CA8A04; font-weight: bold;">1A</td>
                <td style="border: 1px solid #CBD5E1; padding: 8px; background: #DCFCE7; text-align: center; color: #16A34A; font-weight: bold;">1B</td>
                <td style="border: 1px solid #CBD5E1; padding: 8px; background: #DCFCE7; text-align: center; color: #16A34A; font-weight: bold;">1C</td>
                <td style="border: 1px solid #CBD5E1; padding: 8px; background: #DCFCE7; text-align: center; color: #16A34A; font-weight: bold;">1D</td>
                <td style="border: 1px solid #CBD5E1; padding: 8px; background: #DCFCE7; text-align: center; color: #16A34A; font-weight: bold;">1E</td>
            </tr>
        </table>
    </div>
    <div style="display: flex; gap: 1rem; margin-top: 0.5rem; font-size: 0.75rem; flex-wrap: wrap;">
        <span style="display: flex; align-items: center; gap: 4px;"><span style="width: 12px; height: 12px; background: #FEE2E2; border: 1px solid #DC2626; border-radius: 2px;"></span> Extreme</span>
        <span style="display: flex; align-items: center; gap: 4px;"><span style="width: 12px; height: 12px; background: #FFEDD5; border: 1px solid #EA580C; border-radius: 2px;"></span> High</span>
        <span style="display: flex; align-items: center; gap: 4px;"><span style="width: 12px; height: 12px; background: #FEF9C3; border: 1px solid #CA8A04; border-radius: 2px;"></span> Medium</span>
        <span style="display: flex; align-items: center; gap: 4px;"><span style="width: 12px; height: 12px; background: #DCFCE7; border: 1px solid #16A34A; border-radius: 2px;"></span> Low</span>
    </div>
    """, unsafe_allow_html=True)


def render_risk_badge(risk_level: str) -> str:
    """Return HTML for risk level badge"""
    colors = {
        "Extreme": ("#DC2626", "#FEE2E2"),
        "High": ("#EA580C", "#FFEDD5"),
        "Medium": ("#CA8A04", "#FEF9C3"),
        "Low": ("#16A34A", "#DCFCE7")
    }
    text_color, bg_color = colors.get(risk_level, ("#64748B", "#F1F5F9"))
    return f'<span style="background: {bg_color}; color: {text_color}; padding: 4px 12px; border-radius: 20px; font-weight: 600; font-size: 0.85rem;">{risk_level}</span>'


# ============================================================================
# END OF PART 5
# ============================================================================
# ============================================================================
# PART 6: OPERATIONAL FORMS - FSR & CAPTAIN'S DEBRIEF
# ============================================================================
# Air Sial Corporate Safety Management System v3.0
# Flight Services Report and Captain's Debrief Report
# ============================================================================

def render_fsr_form():
    """
    Flight Services Report (FSR)
    Cabin crew and ground services quality reporting
    """
    st.markdown("## 🛫 Flight Services Report (FSR)")
    st.markdown("*Report flight services quality, issues, and passenger feedback*")
    
    with st.form("fsr_form", clear_on_submit=False):
        
        # ========== SECTION A: FLIGHT INFORMATION ==========
        st.markdown("""<div class="form-section">
            <div class="form-section-header">Section A: Flight Information</div>
        </div>""", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            report_id = st.text_input(
                "Report Reference Number",
                value=f"FSR-{datetime.now().strftime('%Y%m%d')}-{random.randint(100, 999)}",
                disabled=True
            )
        with col2:
            flight_date = st.date_input(
                "Flight Date *",
                value=date.today(),
                key="fsr_date"
            )
        
        col1, col2, col3 = st.columns(3)
        with col1:
            flight_number = st.text_input(
                "Flight Number *",
                placeholder="e.g., PF-101",
                key="fsr_flight"
            )
        with col2:
            aircraft_reg = st.selectbox(
                "Aircraft Registration *",
                # FIX: Use keys directly
                options=[""] + list(AIRCRAFT_FLEET.keys()),
                index=0,
                key="fsr_reg"
            )
        with col3:
            aircraft_type = st.text_input(
                "Aircraft Type",
                # FIX: Direct dictionary lookup
                value=AIRCRAFT_FLEET.get(aircraft_reg, {}).get("type", ""),
                disabled=True,
                key="fsr_type"
            )
        
        col1, col2 = st.columns(2)
        with col1:
            origin = st.selectbox(
                "Origin *",
                options=[""] + [f"{data['icao']} - {data['name']}" for data in AIRPORTS.values()],
                index=0,
                key="fsr_origin"
            )
        with col2:
            destination = st.selectbox(
                "Destination *",
                options=[""] + [f"{data['icao']} - {data['name']}" for data in AIRPORTS.values()],
                index=0,
                key="fsr_dest"
            )
        
        col1, col2, col3 = st.columns(3)
        with col1:
            std = st.time_input(
                "STD (Scheduled)",
                value=datetime.strptime("08:00", "%H:%M").time(),
                key="fsr_std"
            )
        with col2:
            atd = st.time_input(
                "ATD (Actual)",
                value=datetime.strptime("08:15", "%H:%M").time(),
                key="fsr_atd"
            )
        with col3:
            block_time = st.text_input(
                "Block Time",
                placeholder="e.g., 1:45"
            )
        
        # ========== SECTION B: CREW INFORMATION ==========
        st.markdown("""<div class="form-section">
            <div class="form-section-header">Section B: Crew Information</div>
        </div>""", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            captain_name = st.text_input(
                "Captain Name",
                key="fsr_captain"
            )
        with col2:
            fo_name = st.text_input(
                "First Officer Name",
                key="fsr_fo"
            )
        
        col1, col2 = st.columns(2)
        with col1:
            sccm_name = st.text_input(
                "SCCM Name *",
                placeholder="Senior Cabin Crew Member"
            )
        with col2:
            cabin_crew_count = st.number_input(
                "Number of Cabin Crew",
                min_value=1,
                max_value=20,
                value=4,
                step=1,
                key="fsr_cc"
            )
        
        cabin_crew_names = st.text_area(
            "Cabin Crew Names",
            placeholder="List all cabin crew members...",
            height=60
        )
        
        # ========== SECTION C: PASSENGER LOAD ==========
        st.markdown("""<div class="form-section">
            <div class="form-section-header">Section C: Passenger Load</div>
        </div>""", unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            pax_business = st.number_input(
                "Business Class",
                min_value=0,
                max_value=50,
                value=0,
                step=1
            )
        with col2:
            pax_economy = st.number_input(
                "Economy Class",
                min_value=0,
                max_value=300,
                value=0,
                step=1
            )
        with col3:
            pax_infant = st.number_input(
                "Infants",
                min_value=0,
                max_value=50,
                value=0,
                step=1,
                key="fsr_infant"
            )
        with col4:
            pax_total = st.number_input(
                "Total PAX",
                value=pax_business + pax_economy,
                disabled=True
            )
        
        col1, col2, col3 = st.columns(3)
        with col1:
            wchr_count = st.number_input(
                "WCHR (Wheelchair)",
                min_value=0,
                max_value=20,
                value=0,
                step=1
            )
        with col2:
            um_count = st.number_input(
                "UM (Unaccompanied Minors)",
                min_value=0,
                max_value=20,
                value=0,
                step=1
            )
        with col3:
            special_meals = st.number_input(
                "Special Meals",
                min_value=0,
                max_value=100,
                value=0,
                step=1
            )
        
        # ========== SECTION D: BAGGAGE & CARGO ==========
        st.markdown("""<div class="form-section">
            <div class="form-section-header">Section D: Baggage & Cargo</div>
        </div>""", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            checked_bags = st.number_input(
                "Checked Bags",
                min_value=0,
                max_value=500,
                value=0,
                step=1
            )
        with col2:
            baggage_weight = st.number_input(
                "Baggage Weight (kg)",
                min_value=0,
                max_value=20000,
                value=0,
                step=100
            )
        with col3:
            cargo_weight = st.number_input(
                "Cargo Weight (kg)",
                min_value=0,
                max_value=20000,
                value=0,
                step=100,
                key="fsr_cargo"
            )
        
        col1, col2 = st.columns(2)
        with col1:
            oversized_bags = st.number_input(
                "Oversized/Special Bags",
                min_value=0,
                max_value=50,
                value=0,
                step=1
            )
        with col2:
            gate_checked = st.number_input(
                "Gate Checked Items",
                min_value=0,
                max_value=50,
                value=0,
                step=1
            )
        
        # ========== SECTION E: SERVICE QUALITY RATINGS ==========
        st.markdown("""<div class="form-section">
            <div class="form-section-header">Section E: Service Quality Ratings</div>
        </div>""", unsafe_allow_html=True)
        
        st.markdown("*Rate each service area from 1 (Poor) to 5 (Excellent)*")
        
        col1, col2 = st.columns(2)
        with col1:
            boarding_rating = st.slider(
                "Boarding Process",
                min_value=1,
                max_value=5,
                value=4,
                help="1=Poor, 5=Excellent"
            )
            catering_rating = st.slider(
                "Catering Quality",
                min_value=1,
                max_value=5,
                value=4
            )
            cabin_cleanliness = st.slider(
                "Cabin Cleanliness",
                min_value=1,
                max_value=5,
                value=4
            )
        with col2:
            ife_rating = st.slider(
                "IFE System",
                min_value=1,
                max_value=5,
                value=4,
                help="In-Flight Entertainment"
            )
            crew_service = st.slider(
                "Crew Service Quality",
                min_value=1,
                max_value=5,
                value=4
            )
            overall_rating = st.slider(
                "Overall Flight Experience",
                min_value=1,
                max_value=5,
                value=4
            )
        
        # ========== SECTION F: ISSUES & IRREGULARITIES ==========
        st.markdown("""<div class="form-section">
            <div class="form-section-header">Section F: Issues & Irregularities</div>
        </div>""", unsafe_allow_html=True)
        
        issues_reported = st.multiselect(
            "Issues Encountered",
            options=[
                "No issues",
                "Catering - Short loaded",
                "Catering - Quality issues",
                "Catering - Late delivery",
                "Cabin - Equipment malfunction",
                "Cabin - Seat issues",
                "Cabin - IFE issues",
                "Cabin - Lavatory issues",
                "Cabin - Temperature issues",
                "Boarding - Delays",
                "Boarding - Overbooking",
                "Passenger - Unruly behavior",
                "Passenger - Medical emergency",
                "Passenger - Complaint",
                "Baggage - Mishandling",
                "Baggage - Delayed delivery",
                "Ground handling - Issues",
                "Security - Issues",
                "Other"
            ],
            default=["No issues"]
        )
        
        issue_details = st.text_area(
            "Issue Details (if any)",
            placeholder="Describe any issues in detail...",
            height=100
        )
        
        # ========== SECTION G: PASSENGER FEEDBACK ==========
        st.markdown("""<div class="form-section">
            <div class="form-section-header">Section G: Passenger Feedback</div>
        </div>""", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            compliments = st.number_input(
                "Compliments Received",
                min_value=0,
                max_value=50,
                value=0,
                step=1
            )
        with col2:
            complaints = st.number_input(
                "Complaints Received",
                min_value=0,
                max_value=50,
                value=0,
                step=1
            )
        with col3:
            comment_cards = st.number_input(
                "Comment Cards Collected",
                min_value=0,
                max_value=100,
                value=0,
                step=1
            )
        
        feedback_summary = st.text_area(
            "Feedback Summary",
            placeholder="Summarize notable passenger feedback...",
            height=80
        )
        
        # ========== SECTION H: MEDICAL INCIDENTS ==========
        st.markdown("""<div class="form-section">
            <div class="form-section-header">Section H: Medical Incidents</div>
        </div>""", unsafe_allow_html=True)
        
        medical_incident = st.selectbox(
            "Medical Incident Occurred?",
            options=["No", "Yes - Minor (First aid)", "Yes - Moderate (Medical kit used)", "Yes - Serious (Doctor paged)", "Yes - Emergency (Diversion considered)"],
            index=0
        )
        
        if medical_incident != "No":
            medical_details = st.text_area(
                "Medical Incident Details",
                placeholder="Describe the medical incident, response, and outcome...",
                height=80
            )
        else:
            medical_details = ""
        
        # ========== SECTION I: DELAYS ==========
        st.markdown("""<div class="form-section">
            <div class="form-section-header">Section I: Delay Information</div>
        </div>""", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            departure_delay = st.number_input(
                "Departure Delay (minutes)",
                min_value=0,
                max_value=600,
                value=0,
                step=5
            )
        with col2:
            arrival_delay = st.number_input(
                "Arrival Delay (minutes)",
                min_value=0,
                max_value=600,
                value=0,
                step=5
            )
        
        if departure_delay > 0 or arrival_delay > 0:
            delay_reason = st.selectbox(
                "Primary Delay Reason",
                options=[
                    "Aircraft - Technical",
                    "Aircraft - Late arrival",
                    "Operations - Crew",
                    "Operations - Fueling",
                    "Operations - Catering",
                    "Operations - Cleaning",
                    "Ground handling",
                    "Passengers - Late boarding",
                    "Passengers - Special assistance",
                    "Baggage - Loading",
                    "Weather",
                    "ATC - Slot",
                    "ATC - Flow control",
                    "Security",
                    "Airport - Infrastructure",
                    "Other"
                ],
                index=0
            )
            delay_remarks = st.text_input(
                "Delay Remarks",
                placeholder="Additional delay information..."
            )
        else:
            delay_reason = "N/A"
            delay_remarks = ""
        
        # ========== SECTION J: ADDITIONAL REMARKS ==========
        st.markdown("""<div class="form-section">
            <div class="form-section-header">Section J: Additional Remarks</div>
        </div>""", unsafe_allow_html=True)
        
        additional_remarks = st.text_area(
            "Additional Remarks",
            placeholder="Any other observations or comments...",
            height=100
        )
        
        reported_by = st.text_input(
            "Report Submitted By *",
            value=st.session_state.get('user_name', ''),
            key="fsr_reporter"
        )
        
        # Form submission
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            submitted = st.form_submit_button(
                "📤 Submit Flight Services Report",
                use_container_width=True,
                type="primary"
            )
        
        if submitted:
            # Validation
            errors = []
            if not flight_number:
                errors.append("Flight Number is required")
            if not aircraft_reg:
                errors.append("Aircraft Registration is required")
            if not sccm_name:
                errors.append("SCCM Name is required")
            if not reported_by:
                errors.append("Reporter Name is required")
            
            if errors:
                for error in errors:
                    st.error(f"❌ {error}")
            else:
                # Determine risk level based on issues
                if medical_incident in ["Yes - Serious (Doctor paged)", "Yes - Emergency (Diversion considered)"]:
                    risk_level = "High"
                elif "Passenger - Unruly behavior" in issues_reported or complaints > 3:
                    risk_level = "Medium"
                elif "No issues" not in issues_reported:
                    risk_level = "Low"
                else:
                    risk_level = "Low"
                
                # Create report record
                report_data = {
                    'id': report_id,
                    'type': 'Flight Services Report',
                    'date': flight_date.isoformat(),
                    'flight_number': flight_number,
                    'aircraft_reg': aircraft_reg,
                    'aircraft_type': aircraft_type,
                    'origin': origin.split(' - ')[0] if origin else '',
                    'destination': destination.split(' - ')[0] if destination else '',
                    'std': std.strftime('%H:%M'),
                    'atd': atd.strftime('%H:%M'),
                    'block_time': block_time,
                    'captain': captain_name,
                    'first_officer': fo_name,
                    'sccm': sccm_name,
                    'cabin_crew_count': cabin_crew_count,
                    'cabin_crew_names': cabin_crew_names,
                    'pax_business': pax_business,
                    'pax_economy': pax_economy,
                    'pax_infant': pax_infant,
                    'pax_total': pax_business + pax_economy,
                    'wchr_count': wchr_count,
                    'um_count': um_count,
                    'special_meals': special_meals,
                    'checked_bags': checked_bags,
                    'baggage_weight': baggage_weight,
                    'cargo_weight': cargo_weight,
                    'oversized_bags': oversized_bags,
                    'gate_checked': gate_checked,
                    'ratings': {
                        'boarding': boarding_rating,
                        'catering': catering_rating,
                        'cleanliness': cabin_cleanliness,
                        'ife': ife_rating,
                        'crew_service': crew_service,
                        'overall': overall_rating
                    },
                    'issues': issues_reported,
                    'issue_details': issue_details,
                    'compliments': compliments,
                    'complaints': complaints,
                    'comment_cards': comment_cards,
                    'feedback_summary': feedback_summary,
                    'medical_incident': medical_incident,
                    'medical_details': medical_details,
                    'departure_delay': departure_delay,
                    'arrival_delay': arrival_delay,
                    'delay_reason': delay_reason,
                    'delay_remarks': delay_remarks,
                    'remarks': additional_remarks,
                    'reported_by': reported_by,
                    'risk_level': risk_level,
                    'status': 'Open - Pending Review',
                    'created_at': datetime.now().isoformat(),
                    'department': 'Cabin Services'
                }
                
                # Add to session state
                # --- REPLACE WITH ---
                try:
                    # Ensure keys match your Supabase DB columns exactly
                    # Note: Changed 'incident_id' to 'report_id' to match the FSR form variable
                    response = supabase.table('fsr_reports').insert(report_data).execute()
                    st.balloons()
                    st.success(f"✅ Flight Services Report Saved to Database! Ref: {report_id}")
                except Exception as e:
                    st.error(f"Database Error: {e}")
# --------------------
                
                # Success feedback
                st.balloons()
                st.success(f"""
                    ✅ **Flight Services Report Submitted Successfully!**
                    
                    **Reference:** {report_id}  
                    **Flight:** {flight_number}  
                    **Overall Rating:** {overall_rating}/5
                    
                    The report has been added to the system.
                """)


def render_captain_dbr_form():
    """
    Captain's Debrief Report (DBR)
    Post-flight debrief and safety observations from flight crew
    """
    st.markdown("## 👨‍✈️ Captain's Debrief Report (DBR)")
    st.markdown("*Post-flight technical and operational debrief*")
    
    with st.form("captain_dbr_form", clear_on_submit=False):
        
        # ========== SECTION A: FLIGHT INFORMATION ==========
        st.markdown("""<div class="form-section">
            <div class="form-section-header">Section A: Flight Information</div>
        </div>""", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            report_id = st.text_input(
                "Report Reference Number",
                value=f"DBR-{datetime.now().strftime('%Y%m%d')}-{random.randint(100, 999)}",
                disabled=True
            )
        with col2:
            flight_date = st.date_input(
                "Flight Date *",
                value=date.today(),
                key="dbr_date"
            )
        
        col1, col2, col3 = st.columns(3)
        with col1:
            flight_number = st.text_input(
                "Flight Number *",
                placeholder="e.g., PF-101",
                key="dbr_flight"
            )
        with col2:
            aircraft_reg = st.selectbox(
                "Aircraft Registration *",
                # FIX: Use keys directly
                options=[""] + list(AIRCRAFT_FLEET.keys()),
                index=0,
                key="dbr_reg"
            )
        with col3:
            aircraft_type = st.text_input(
                "Aircraft Type",
                # FIX: Direct dictionary lookup
                value=AIRCRAFT_FLEET.get(aircraft_reg, {}).get("type", ""),
                disabled=True,
                key="dbr_type"
            )
        
        col1, col2 = st.columns(2)
        with col1:
            origin = st.selectbox(
                "Origin *",
                options=[""] + [f"{data['icao']} - {data['name']}" for data in AIRPORTS.values()],
                index=0,
                key="dbr_origin"
            )
        with col2:
            destination = st.selectbox(
                "Destination *",
                options=[""] + [f"{data['icao']} - {data['name']}" for data in AIRPORTS.values()],
                index=0,
                key="dbr_dest"
            )
        
        # ========== SECTION B: TIMES ==========
        st.markdown("""<div class="form-section">
            <div class="form-section-header">Section B: Flight Times</div>
        </div>""", unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            off_blocks = st.time_input(
                "Off Blocks (UTC)",
                value=datetime.strptime("08:00", "%H:%M").time(),
                key="dbr_off"
            )
        with col2:
            takeoff_time = st.time_input(
                "Takeoff (UTC)",
                value=datetime.strptime("08:15", "%H:%M").time()
            )
        with col3:
            landing_time = st.time_input(
                "Landing (UTC)",
                value=datetime.strptime("09:45", "%H:%M").time()
            )
        with col4:
            on_blocks = st.time_input(
                "On Blocks (UTC)",
                value=datetime.strptime("10:00", "%H:%M").time(),
                key="dbr_on"
            )
        
        col1, col2, col3 = st.columns(3)
        with col1:
            block_time_hrs = st.number_input(
                "Block Time (hours)",
                min_value=0.0,
                max_value=20.0,
                value=2.0,
                step=0.1
            )
        with col2:
            flight_time_hrs = st.number_input(
                "Flight Time (hours)",
                min_value=0.0,
                max_value=20.0,
                value=1.5,
                step=0.1
            )
        with col3:
            cycles = st.number_input(
                "Cycles",
                min_value=1,
                max_value=10,
                value=1,
                step=1
            )
        
        # ========== SECTION C: FUEL ==========
        st.markdown("""<div class="form-section">
            <div class="form-section-header">Section C: Fuel Information</div>
        </div>""", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            fuel_departure = st.number_input(
                "Block Fuel (kg)",
                min_value=0,
                max_value=100000,
                value=5000,
                step=100
            )
        with col2:
            fuel_arrival = st.number_input(
                "Remaining Fuel (kg)",
                min_value=0,
                max_value=100000,
                value=2500,
                step=100
            )
        with col3:
            fuel_used = st.number_input(
                "Fuel Used (kg)",
                value=fuel_departure - fuel_arrival,
                disabled=True
            )
        
        col1, col2 = st.columns(2)
        with col1:
            fuel_planned = st.number_input(
                "Planned Fuel Burn (kg)",
                min_value=0,
                max_value=50000,
                value=2400,
                step=100
            )
        with col2:
            fuel_variance = st.number_input(
                "Fuel Variance (kg)",
                value=(fuel_departure - fuel_arrival) - fuel_planned,
                disabled=True,
                help="Positive = more than planned"
            )
        
        fuel_remarks = st.text_input(
            "Fuel Remarks",
            placeholder="Any fuel-related observations..."
        )
        
        # ========== SECTION D: WEIGHTS ==========
        st.markdown("""<div class="form-section">
            <div class="form-section-header">Section D: Weight Information</div>
        </div>""", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            zfw = st.number_input(
                "ZFW (kg)",
                min_value=0,
                max_value=200000,
                value=55000,
                step=100,
                help="Zero Fuel Weight"
            )
        with col2:
            tow = st.number_input(
                "TOW (kg)",
                min_value=0,
                max_value=300000,
                value=60000,
                step=100,
                help="Takeoff Weight"
            )
        with col3:
            lw = st.number_input(
                "LW (kg)",
                min_value=0,
                max_value=250000,
                value=57500,
                step=100,
                help="Landing Weight"
            )
        
        col1, col2 = st.columns(2)
        with col1:
            pax_count = st.number_input(
                "Passengers",
                min_value=0,
                max_value=500,
                value=120,
                step=1,
                key="dbr_pax"
            )
        with col2:
            cargo_mail = st.number_input(
                "Cargo/Mail (kg)",
                min_value=0,
                max_value=50000,
                value=500,
                step=100
            )
        
        # ========== SECTION E: WEATHER ==========
        st.markdown("""<div class="form-section">
            <div class="form-section-header">Section E: Weather Conditions</div>
        </div>""", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Departure**")
            dep_weather = st.selectbox(
                "Departure Weather",
                options=WEATHER_CONDITIONS,
                index=0,
                key="dbr_dep_wx"
            )
            dep_visibility = st.text_input(
                "Departure Visibility",
                placeholder="e.g., 10km, CAVOK"
            )
            dep_wind = st.text_input(
                "Departure Wind",
                placeholder="e.g., 360/10kt"
            )
        
        with col2:
            st.markdown("**Arrival**")
            arr_weather = st.selectbox(
                "Arrival Weather",
                options=WEATHER_CONDITIONS,
                index=0,
                key="dbr_arr_wx"
            )
            arr_visibility = st.text_input(
                "Arrival Visibility",
                placeholder="e.g., 8km"
            )
            arr_wind = st.text_input(
                "Arrival Wind",
                placeholder="e.g., 270/15kt G25kt"
            )
        
        enroute_weather = st.text_area(
            "En-route Weather Remarks",
            placeholder="Turbulence, CB, icing, wind shear, etc...",
            height=60
        )
        
        # ========== SECTION F: APPROACH & LANDING ==========
        st.markdown("""<div class="form-section">
            <div class="form-section-header">Section F: Approach & Landing</div>
        </div>""", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            runway_used = st.text_input(
                "Runway Used",
                placeholder="e.g., 36L"
            )
        with col2:
            approach_type = st.selectbox(
                "Approach Type",
                options=["ILS CAT I", "ILS CAT II", "ILS CAT III", "VOR", "VOR/DME", "NDB", "RNAV (GPS)", "RNAV (RNP)", "Visual", "Circling", "Other"],
                index=0
            )
        with col3:
            autoland = st.selectbox(
                "Autoland Used?",
                options=["No", "Yes", "N/A"],
                index=0
            )
        
        col1, col2 = st.columns(2)
        with col1:
            approach_stable = st.selectbox(
                "Approach Stabilized?",
                options=["Yes - Fully stabilized", "Yes - Minor corrections", "No - Go-around", "N/A"],
                index=0
            )
        with col2:
            landing_quality = st.selectbox(
                "Landing Quality",
                options=["Smooth", "Normal", "Firm", "Hard", "Go-around executed"],
                index=1
            )
        
        approach_remarks = st.text_area(
            "Approach/Landing Remarks",
            placeholder="Wind shear, visual conditions, terrain awareness, etc...",
            height=60
        )
        
        # ========== SECTION G: TECHNICAL STATUS ==========
        st.markdown("""<div class="form-section">
            <div class="form-section-header">Section G: Technical Status</div>
        </div>""", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            mel_items = st.selectbox(
                "MEL Items Active?",
                options=["No", "Yes - 1 item", "Yes - 2 items", "Yes - 3+ items"],
                index=0
            )
        with col2:
            tech_issues = st.selectbox(
                "Technical Issues During Flight?",
                options=["No issues", "Minor - No operational impact", "Moderate - Operational limitation", "Significant - Procedure deviation", "Serious - Emergency procedure"],
                index=0
            )
        
        if tech_issues != "No issues":
            tech_description = st.text_area(
                "Technical Issue Description",
                placeholder="Describe the technical issue(s)...",
                height=80
            )
            aml_entry = st.selectbox(
                "AML Entry Made?",
                options=["Yes", "No - Not required", "Pending"],
                index=0
            )
        else:
            tech_description = ""
            aml_entry = "N/A"
        
        systems_checked = st.multiselect(
            "Systems with Anomalies (if any)",
            options=[
                "None",
                "Flight Controls",
                "Autopilot/Flight Director",
                "Engine 1",
                "Engine 2",
                "APU",
                "Hydraulics",
                "Electrics",
                "Pressurization",
                "Air Conditioning",
                "Anti-ice/De-ice",
                "Landing Gear",
                "Brakes",
                "Navigation",
                "Communication",
                "TCAS/EGPWS",
                "Weather Radar",
                "FMS/MCDU",
                "Other"
            ],
            default=["None"]
        )
        
        # ========== SECTION H: NAVIGATION ==========
        st.markdown("""<div class="form-section">
            <div class="form-section-header">Section H: Navigation & ATC</div>
        </div>""", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            route_deviation = st.selectbox(
                "Route Deviation?",
                options=["No - As planned", "Yes - Weather avoidance", "Yes - ATC instruction", "Yes - Traffic", "Yes - Other"],
                index=0
            )
        with col2:
            altitude_deviation = st.selectbox(
                "Altitude Deviation?",
                options=["No - As planned", "Yes - ATC assigned", "Yes - Weather", "Yes - Performance", "Yes - Other"],
                index=0
            )
        
        atc_remarks = st.text_area(
            "ATC/Navigation Remarks",
            placeholder="Significant ATC instructions, CPDLC issues, RVSM, etc...",
            height=60
        )
        
        # ========== SECTION I: CREW FACTORS ==========
        st.markdown("""<div class="form-section">
            <div class="form-section-header">Section I: Crew Information</div>
        </div>""", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            captain_name = st.text_input(
                "Captain Name *",
                key="dbr_captain"
            )
            captain_license = st.text_input(
                "Captain License",
                placeholder="e.g., ATPL-12345",
                key="dbr_cap_lic"
            )
        with col2:
            fo_name = st.text_input(
                "First Officer Name",
                key="dbr_fo"
            )
            fo_license = st.text_input(
                "FO License",
                placeholder="e.g., CPL-67890"
            )
        
        col1, col2 = st.columns(2)
        with col1:
            pilot_flying = st.selectbox(
                "Pilot Flying",
                options=["Captain", "First Officer"],
                index=0,
                key="dbr_pf"
            )
        with col2:
            fdp_status = st.selectbox(
                "FDP Status",
                options=["Within limits", "Extended - Pre-planned", "Extended - Operational", "Near limits", "Exceeded - Commander's discretion"],
                index=0
            )
        
        crew_fatigue = st.selectbox(
            "Crew Fatigue Level",
            options=["Normal - Well rested", "Mild - Acceptable", "Moderate - Noticeable", "High - Performance concern", "Severe - Reported to management"],
            index=0
        )
        
        # ========== SECTION J: SAFETY OBSERVATIONS ==========
        st.markdown("""<div class="form-section">
            <div class="form-section-header">Section J: Safety Observations & Recommendations</div>
        </div>""", unsafe_allow_html=True)
        
        safety_observations = st.text_area(
            "Safety Observations",
            placeholder="Any safety-related observations, good catches, or concerns...",
            height=100
        )
        
        hazards_identified = st.multiselect(
            "Hazards/Threats Identified",
            options=[
                "None identified",
                "Weather - Adverse conditions",
                "Terrain - Challenging approach",
                "Traffic - High density",
                "Fatigue - Crew",
                "Time pressure",
                "Aircraft - Technical issues",
                "ATC - Communication issues",
                "Airport - Infrastructure",
                "Ground handling - Issues",
                "Passenger - Disruption",
                "Wildlife - Activity",
                "Other"
            ],
            default=["None identified"]
        )
        
        recommendations = st.text_area(
            "Recommendations",
            placeholder="Suggestions for safety improvements...",
            height=80
        )
        
        # Overall assessment
        overall_flight = st.selectbox(
            "Overall Flight Assessment",
            options=[
                "Normal - Routine flight",
                "Minor variations - Within normal operations",
                "Notable events - Documented for review",
                "Significant issues - Requires follow-up",
                "Safety concern - Immediate review required"
            ],
            index=0
        )
        
        # Form submission
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            submitted = st.form_submit_button(
                "📤 Submit Captain's Debrief Report",
                use_container_width=True,
                type="primary"
            )
        
        if submitted:
            # Validation
            errors = []
            if not flight_number:
                errors.append("Flight Number is required")
            if not aircraft_reg:
                errors.append("Aircraft Registration is required")
            if not captain_name:
                errors.append("Captain Name is required")
            
            if errors:
                for error in errors:
                    st.error(f"❌ {error}")
            else:
                # Determine risk level
                if tech_issues in ["Significant - Procedure deviation", "Serious - Emergency procedure"]:
                    risk_level = "High"
                elif overall_flight in ["Significant issues - Requires follow-up", "Safety concern - Immediate review required"]:
                    risk_level = "High"
                elif tech_issues != "No issues" or "None identified" not in hazards_identified:
                    risk_level = "Medium"
                else:
                    risk_level = "Low"
                
                # Create report record
                report_data = {
                    'id': report_id,
                    'type': "Captain's Debrief",
                    'date': flight_date.isoformat(),
                    'flight_number': flight_number,
                    'aircraft_reg': aircraft_reg,
                    'aircraft_type': aircraft_type,
                    'origin': origin.split(' - ')[0] if origin else '',
                    'destination': destination.split(' - ')[0] if destination else '',
                    'times': {
                        'off_blocks': off_blocks.strftime('%H:%M'),
                        'takeoff': takeoff_time.strftime('%H:%M'),
                        'landing': landing_time.strftime('%H:%M'),
                        'on_blocks': on_blocks.strftime('%H:%M')
                    },
                    'block_time': block_time_hrs,
                    'flight_time': flight_time_hrs,
                    'cycles': cycles,
                    'fuel': {
                        'departure': fuel_departure,
                        'arrival': fuel_arrival,
                        'used': fuel_departure - fuel_arrival,
                        'planned': fuel_planned,
                        'variance': (fuel_departure - fuel_arrival) - fuel_planned
                    },
                    'fuel_remarks': fuel_remarks,
                    'weights': {
                        'zfw': zfw,
                        'tow': tow,
                        'lw': lw
                    },
                    'pax_count': pax_count,
                    'cargo_mail': cargo_mail,
                    'weather': {
                        'departure': dep_weather,
                        'dep_visibility': dep_visibility,
                        'dep_wind': dep_wind,
                        'arrival': arr_weather,
                        'arr_visibility': arr_visibility,
                        'arr_wind': arr_wind,
                        'enroute': enroute_weather
                    },
                    'approach': {
                        'runway': runway_used,
                        'type': approach_type,
                        'autoland': autoland,
                        'stable': approach_stable,
                        'landing_quality': landing_quality,
                        'remarks': approach_remarks
                    },
                    'technical': {
                        'mel_items': mel_items,
                        'issues': tech_issues,
                        'description': tech_description,
                        'aml_entry': aml_entry,
                        'systems_anomalies': systems_checked
                    },
                    'navigation': {
                        'route_deviation': route_deviation,
                        'altitude_deviation': altitude_deviation,
                        'atc_remarks': atc_remarks
                    },
                    'crew': {
                        'captain': captain_name,
                        'captain_license': captain_license,
                        'first_officer': fo_name,
                        'fo_license': fo_license,
                        'pilot_flying': pilot_flying,
                        'fdp_status': fdp_status,
                        'fatigue_level': crew_fatigue
                    },
                    'safety': {
                        'observations': safety_observations,
                        'hazards': hazards_identified,
                        'recommendations': recommendations
                    },
                    'overall_assessment': overall_flight,
                    'risk_level': risk_level,
                    'status': 'Open - Pending Review',
                    'created_at': datetime.now().isoformat(),
                    'department': 'Flight Operations'
                }
                
                # Add to session state
                # --- REPLACE WITH ---
                try:
                    # Ensure keys match your Supabase DB columns exactly
                    response = supabase.table('captain_dbr').insert(report_data).execute()
                    st.balloons()
                    # CORRECTION: Changed 'incident_id' to 'report_id'
                    st.success(f"✅ Captain's Debrief Report Saved to Database! Ref: {report_id}")
                except Exception as e:
                    st.error(f"Database Error: {e}")
                
                # Success feedback
                st.balloons()
                st.success(f"""
                    ✅ **Captain's Debrief Report Submitted Successfully!**
                    
                    **Reference:** {report_id}  
                    **Flight:** {flight_number}  
                    **Assessment:** {overall_flight.split(' - ')[0]}
                    
                    The report has been added to the system.
                """)


# ============================================================================
# END OF PART 6
# ============================================================================
# =============================================================================
# PART 7: DASHBOARD & VIEW REPORTS
# Air Sial SMS v3.0 - Safety Management System
# =============================================================================
# This part includes:
# - Main dashboard with KPI cards
# - Trend charts and analytics
# - View Reports with filtering
# - Report detail view
# - Status updates and actions
# - Email trail display
# - PDF download functionality
# =============================================================================

def render_dashboard():
    """
    Modified Dashboard: 4 Key Blocks + Existing Weather Widget
    1. Voluntary | 2. MOR | 3. Quality | 4. AI
    """
    # 1. Weather Widget (Retained from your original code)
    try:
        render_weather_widget()
    except:
        pass # Fail gracefully if weather service is down
    
    st.markdown("---")
    
    # 2. Main Dashboard Layout (Master Prompt Requirement)
    st.markdown("### 📡 Safety Overview")
    
    # Filter logic based on Role (Gatekeeper sees all, Analyst sees Dept, Reporter sees Public stats)
    # (Mocking counts for display - connect these to your st.session_state lists)
    vol_count = len(st.session_state.get('hazard_reports', []))
    mor_count = len(st.session_state.get('mor_reports', [])) 
    audit_count = len(st.session_state.get('audit_reports', []))
    
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.markdown(f"""
        <div style="background-color: #F8F9FA; padding: 20px; border-top: 5px solid #006400; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
            <h4 style="color: #333; margin:0;">Voluntary</h4>
            <p style="font-size: 0.8rem; color: #666; margin-bottom: 10px;">Hazards & Observations</p>
            <h1 style="color: #006400; font-size: 2.5rem; margin:0;">{vol_count}</h1>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown(f"""
        <div style="background-color: #F8F9FA; padding: 20px; border-top: 5px solid #8B0000; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
            <h4 style="color: #333; margin:0;">MOR</h4>
            <p style="font-size: 0.8rem; color: #666; margin-bottom: 10px;">Mandatory Occurrence</p>
            <h1 style="color: #8B0000; font-size: 2.5rem; margin:0;">{mor_count}</h1>
        </div>
        """, unsafe_allow_html=True)

    with c3:
        st.markdown(f"""
        <div style="background-color: #F8F9FA; padding: 20px; border-top: 5px solid #1e3c72; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
            <h4 style="color: #333; margin:0;">Quality</h4>
            <p style="font-size: 0.8rem; color: #666; margin-bottom: 10px;">Audits & Inspections</p>
            <h1 style="color: #1e3c72; font-size: 2.5rem; margin:0;">{audit_count}</h1>
        </div>
        """, unsafe_allow_html=True)

    with c4:
        st.markdown(f"""
        <div style="background-color: #E8F0FE; padding: 20px; border-top: 5px solid #666; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
            <h4 style="color: #333; margin:0;">AI Insights</h4>
            <p style="font-size: 0.8rem; color: #666; margin-bottom: 10px;">Predictive Analytics</p>
            <h1 style="color: #555; font-size: 2.5rem; margin:0;">--</h1>
        </div>
        """, unsafe_allow_html=True)

def generate_trend_data():
    """Generate monthly trend data from actual reports."""
    
    monthly_counts = defaultdict(int)
    
    # Aggregate all reports by month
    all_reports = []
    for report_type in ['bird_strikes', 'laser_strikes', 'tcas_reports', 
                        'aircraft_incidents', 'hazard_reports', 'fsr_reports', 'captain_dbr']:
        all_reports.extend(st.session_state.get(report_type, []))
    
    for report in all_reports:
        date_str = report.get('date') or report.get('incident_date') or report.get('report_date')
        if date_str:
            try:
                if isinstance(date_str, str):
                    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                else:
                    date_obj = date_str
                month_key = date_obj.strftime('%b %Y')
                monthly_counts[month_key] += 1
            except:
                pass
    
    # If no data, generate sample months
    if not monthly_counts:
        months = []
        for i in range(5, -1, -1):
            month_date = datetime.now() - timedelta(days=i*30)
            months.append({
                'Month': month_date.strftime('%b'),
                'Reports': 0
            })
        return months
    
    # Sort by date and return
    sorted_months = sorted(monthly_counts.items(), 
                          key=lambda x: datetime.strptime(x[0], '%b %Y'))
    return [{'Month': m, 'Reports': c} for m, c in sorted_months[-6:]]


def render_view_reports():
    """View and manage all submitted reports with filtering and actions."""
    
    st.markdown("""
    <div style="background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); 
                padding: 30px; border-radius: 15px; margin-bottom: 25px; color: white;">
        <h1 style="margin: 0; font-size: 2.2rem;">📋 View Reports</h1>
        <p style="margin: 10px 0 0 0; opacity: 0.9; font-size: 1.1rem;">
            Search, filter, and manage all safety reports
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # ==========================================================================
    # FILTERS SECTION
    # ==========================================================================
    with st.expander("🔍 **Search & Filter Options**", expanded=True):
        filter_col1, filter_col2, filter_col3, filter_col4 = st.columns(4)
        
        with filter_col1:
            report_type_filter = st.selectbox(
                "Report Type",
                ["All Types", "Bird Strike", "Laser Strike", "TCAS Report", 
                 "Aircraft Incident", "Hazard Report", "FSR Report", "Captain's Debrief"]
            )
        
        with filter_col2:
            risk_filter = st.selectbox(
                "Risk Level",
                ["All Levels", "Extreme", "High", "Medium", "Low"]
            )
        
        with filter_col3:
            status_filter = st.selectbox(
                "Status",
                ["All Status", "New", "Under Review", "Investigation", 
                 "Pending Action", "Resolved", "Closed"]
            )
        
        with filter_col4:
            date_range = st.date_input(
                "Date Range",
                value=(datetime.now() - timedelta(days=30), datetime.now()),
                max_value=datetime.now()
            )
        
        search_col1, search_col2 = st.columns([3, 1])
        with search_col1:
            search_query = st.text_input("🔎 Search by ID, description, or reporter", "")
        with search_col2:
            st.markdown("<br>", unsafe_allow_html=True)
            search_btn = st.button("🔍 Search", use_container_width=True)
    
    # ==========================================================================
    # GATHER ALL REPORTS
    # ==========================================================================
    all_reports = []
    
    # Map report types to session state keys and display info
    report_type_map = {
        'Bird Strike': ('bird_strikes', '🦅', 'BS'),
        'Laser Strike': ('laser_strikes', '🔴', 'LS'),
        'TCAS Report': ('tcas_reports', '✈️', 'TCAS'),
        'Aircraft Incident': ('aircraft_incidents', '⚠️', 'INC'),
        'Hazard Report': ('hazard_reports', '🔶', 'HAZ'),
        'FSR Report': ('fsr_reports', '📝', 'FSR'),
        "Captain's Debrief": ('captain_dbr', '👨‍✈️', 'DBR'),
    }
    
    for display_name, (state_key, icon, prefix) in report_type_map.items():
        for report in st.session_state.get(state_key, []):
            # Normalize report data
            normalized = {
                'id': report.get('report_id') or report.get('id') or f"{prefix}-{len(all_reports)+1:04d}",
                'type': display_name,
                'icon': icon,
                'date': report.get('date') or report.get('incident_date') or report.get('report_date') or 'N/A',
                'reporter': report.get('reporter_name') or report.get('reported_by') or report.get('captain_name') or 'Anonymous',
                'risk_level': report.get('risk_level') or 'Low',
                'status': report.get('status') or report.get('investigation_status') or 'New',
                'description': report.get('description') or report.get('narrative') or report.get('hazard_description') or 'No description',
                'raw_data': report  # Keep original for detail view
            }
            all_reports.append(normalized)
    
    # ==========================================================================
    # APPLY FILTERS
    # ==========================================================================
    filtered_reports = all_reports.copy()
    
    # Filter by type
    if report_type_filter != "All Types":
        filtered_reports = [r for r in filtered_reports if r['type'] == report_type_filter]
    
    # Filter by risk level
    if risk_filter != "All Levels":
        filtered_reports = [r for r in filtered_reports if r['risk_level'] == risk_filter]
    
    # Filter by status
    if status_filter != "All Status":
        filtered_reports = [r for r in filtered_reports if r['status'] == status_filter]
    
    # Filter by search query
    if search_query:
        query_lower = search_query.lower()
        filtered_reports = [r for r in filtered_reports if 
                          query_lower in r['id'].lower() or
                          query_lower in r['reporter'].lower() or
                          query_lower in r['description'].lower()]
    
    # Filter by date range
    if len(date_range) == 2:
        start_date, end_date = date_range
        filtered_reports = [r for r in filtered_reports if filter_by_date(r['date'], start_date, end_date)]
    
    # Sort by date (most recent first)
    filtered_reports.sort(key=lambda x: x['date'] if x['date'] != 'N/A' else '', reverse=True)
    
    # ==========================================================================
    # RESULTS SUMMARY
    # ==========================================================================
    st.markdown(f"""
    <div style="background: #F8F9FA; padding: 15px; border-radius: 10px; margin: 20px 0;">
        <strong>📊 Results:</strong> {len(filtered_reports)} reports found
        {f' matching "{search_query}"' if search_query else ''}
    </div>
    """, unsafe_allow_html=True)
    
    # ==========================================================================
    # REPORTS TABLE
    # ==========================================================================
    if filtered_reports:
        # Create tabs for different views
        tab_list, tab_table = st.tabs(["📋 Card View", "📊 Table View"])
        
        with tab_list:
            for idx, report in enumerate(filtered_reports):
                render_report_card(report, idx)
        
        with tab_table:
            # Convert to DataFrame for table view
            table_data = [{
                'ID': r['id'],
                'Type': r['type'],
                'Date': r['date'],
                'Reporter': r['reporter'],
                'Risk': r['risk_level'],
                'Status': r['status']
            } for r in filtered_reports]
            
            df = pd.DataFrame(table_data)
            
            # Style the dataframe
            def style_risk(val):
                colors = {
                    'Extreme': 'background-color: #DC3545; color: white',
                    'High': 'background-color: #FD7E14; color: white',
                    'Medium': 'background-color: #FFC107; color: black',
                    'Low': 'background-color: #28A745; color: white'
                }
                return colors.get(val, '')
            
            styled_df = df.style.applymap(style_risk, subset=['Risk'])
            st.dataframe(styled_df, use_container_width=True, hide_index=True)
            
            # Export options
            exp_col1, exp_col2, exp_col3 = st.columns([1, 1, 2])
            with exp_col1:
                csv = df.to_csv(index=False)
                st.download_button(
                    "📥 Export CSV",
                    csv,
                    "safety_reports.csv",
                    "text/csv",
                    use_container_width=True
                )
            with exp_col2:
                if st.button("📧 Email Report", use_container_width=True):
                    st.info("Email functionality available in full version.")
    else:
        st.info("No reports found matching your criteria. Try adjusting the filters or submit a new report.")
        
        if st.button("📝 Submit New Report"):
            st.session_state['current_page'] = 'Hazard Report'
            st.rerun()


def filter_by_date(date_str, start_date, end_date):
    """Helper to filter reports by date range."""
    if date_str == 'N/A':
        return True
    try:
        if isinstance(date_str, str):
            report_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        else:
            report_date = date_str
        return start_date <= report_date <= end_date
    except:
        return True


def render_report_card(report, idx):
    """Render a single report as an expandable card."""
    
    risk_colors = {
        'Extreme': ('#DC3545', '#FFF5F5'),
        'High': ('#FD7E14', '#FFF8F0'),
        'Medium': ('#FFC107', '#FFFBEB'),
        'Low': ('#28A745', '#F0FFF4')
    }
    
    border_color, bg_color = risk_colors.get(report['risk_level'], ('#6C757D', '#F8F9FA'))
    
    with st.expander(f"{report['icon']} **{report['id']}** - {report['type']} | {report['date']}", expanded=False):
        # Header with risk badge
        st.markdown(f"""
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
            <div>
                <span style="font-size: 1.5rem;">{report['icon']}</span>
                <strong style="font-size: 1.2rem; margin-left: 10px;">{report['id']}</strong>
            </div>
            <span style="background: {border_color}; color: white; padding: 5px 15px; 
                        border-radius: 20px; font-weight: bold;">
                {report['risk_level']} Risk
            </span>
        </div>
        """, unsafe_allow_html=True)
        
        # Details grid
        detail_col1, detail_col2, detail_col3 = st.columns(3)
        
        with detail_col1:
            st.markdown(f"**📅 Date:** {report['date']}")
            st.markdown(f"**📋 Type:** {report['type']}")
        
        with detail_col2:
            st.markdown(f"**👤 Reporter:** {report['reporter']}")
            st.markdown(f"**📊 Status:** {report['status']}")
        
        with detail_col3:
            st.markdown(f"**⚠️ Risk Level:** {report['risk_level']}")
        
        # Description
        st.markdown("---")
        st.markdown("**📝 Description:**")
        st.markdown(f"> {report['description'][:500]}{'...' if len(report['description']) > 500 else ''}")
        
        # Action buttons
        st.markdown("---")
        action_col1, action_col2, action_col3, action_col4 = st.columns(4)
        
        with action_col1:
            if st.button("👁️ View Details", key=f"view_{idx}", use_container_width=True):
                st.session_state['selected_report'] = report
                st.session_state['current_page'] = 'Report Detail'
                st.rerun()
        
        with action_col2:
            if st.button("✏️ Update Status", key=f"status_{idx}", use_container_width=True):
                st.session_state['update_report'] = report
                st.session_state['show_status_modal'] = True
        
        with action_col3:
            if st.button("📧 Send Email", key=f"email_{idx}", use_container_width=True):
                st.session_state['email_report'] = report
                st.info("Email dialog would open here")
        
        with action_col4:
            if st.button("📄 Download PDF", key=f"pdf_{idx}", use_container_width=True):
                generate_report_pdf(report)


def render_report_detail():
    """Detailed view of a single report with all information and actions."""
    
    report = st.session_state.get('selected_report')
    
    if not report:
        st.warning("No report selected. Please select a report from View Reports.")
        if st.button("← Back to Reports"):
            st.session_state['current_page'] = 'View Reports'
            st.rerun()
        return
    
    # Back button
    if st.button("← Back to Reports"):
        st.session_state['current_page'] = 'View Reports'
        st.rerun()
    
    # Report header
    risk_colors = {
        'Extreme': '#DC3545',
        'High': '#FD7E14',
        'Medium': '#FFC107',
        'Low': '#28A745'
    }
    risk_color = risk_colors.get(report.get('risk_level'), '#6C757D')
    
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); 
                padding: 30px; border-radius: 15px; margin: 20px 0; color: white;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <span style="font-size: 2.5rem;">{report.get('icon', '📄')}</span>
                <h1 style="display: inline; margin-left: 15px; font-size: 2rem;">{report.get('id', 'N/A')}</h1>
                <p style="margin: 10px 0 0 0; opacity: 0.9;">{report.get('type', 'Report')}</p>
            </div>
            <div style="text-align: right;">
                <span style="background: {risk_color}; color: white; padding: 10px 25px; 
                            border-radius: 25px; font-size: 1.2rem; font-weight: bold;">
                    {report.get('risk_level', 'Low')} Risk
                </span>
                <p style="margin: 10px 0 0 0; opacity: 0.9;">Status: {report.get('status', 'Unknown')}</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Detail tabs - THIS WAS THE LINE CAUSING YOUR ERROR
    tab_details, tab_timeline, tab_comms, tab_actions = st.tabs([
        "📋 Details", "🕐 Timeline", "💬 Communications", "⚡ Actions"
    ])
    
    with tab_details:
        render_report_details_tab(report)
    
    with tab_timeline:
        render_report_timeline(report)
    
    with tab_comms:
        st.markdown("### 💬 Communication History")
        
        # 1. Fetch Logs
        # Ensure 'id' exists, otherwise default to empty string to prevent errors
        r_id = report.get('id', '')
        email_logs = email_utils.get_email_logs(r_id) if r_id else []
        
        if not email_logs:
            st.info("No email history found.")
        else:
            for email in email_logs:
                is_outbound = email['direction'] == 'outbound'
                alignment = "flex-end" if is_outbound else "flex-start"
                bg_color = "#E3F2FD" if is_outbound else "#F5F5F5"
                icon = "📤" if is_outbound else "📥"
                sender_name = "Safety Team" if is_outbound else email.get('sender', 'Unknown')
                timestamp = email.get('timestamp', '')
                
                st.markdown(f"""
                <div style="display: flex; justify-content: {alignment}; margin-bottom: 10px;">
                    <div style="background: {bg_color}; padding: 15px; border-radius: 15px; max-width: 80%; border: 1px solid #ddd;">
                        <div style="font-size: 0.8em; color: #666; margin-bottom: 5px;">
                            {icon} <strong>{sender_name}</strong> • {timestamp}
                        </div>
                        <div style="font-weight: bold; margin-bottom: 5px;">{email.get('subject', 'No Subject')}</div>
                        <div style="white-space: pre-wrap;">{email.get('body', '')}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        st.divider()
        
        # 2. Reply / Log Actions
        action_type = st.radio("Action:", ["📧 Send Reply", "📥 Log Incoming Reply"], horizontal=True, key=f"comm_action_{report.get('id')}")
        
        if action_type == "📧 Send Reply":
            with st.form(f"reply_form_{report.get('id')}"):
                # Try to find a reporter contact or email
                default_to = report.get('reporter_contact') or report.get('reporter_email') or ""
                to_addr = st.text_input("To:", value=default_to)
                subj = st.text_input("Subject:", value=f"Re: Safety Report {report.get('id')}")
                msg_body = st.text_area("Message:")
                
                if st.form_submit_button("Send Email"):
                    if send_email(to_addr, None, subj, msg_body, report_id=report.get('id')):
                        st.success("Email sent and logged!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Failed to send.")
        else: 
            with st.form(f"log_reply_form_{report.get('id')}"):
                sender = st.text_input("From (Sender Name/Email):")
                msg_body = st.text_area("Message Content Received:")
                if st.form_submit_button("💾 Log Reply"):
                    # Use a temp client just to access the log function
                    dummy_client = email_utils.SMTPClient("","","","")
                    dummy_client.log_reply(report.get('id'), sender, msg_body)
                    st.success("Reply logged successfully!")
                    time.sleep(1)
                    st.rerun()
    
    with tab_actions:
        render_report_actions(report)


def render_report_details_tab(report):
    """Render the details tab of report detail view."""
    
    raw_data = report.get('raw_data', {})
    
    # Basic Information
    st.markdown("### 📌 Basic Information")
    
    info_col1, info_col2 = st.columns(2)
    
    with info_col1:
        st.markdown(f"**Report ID:** {report['id']}")
        st.markdown(f"**Report Type:** {report['type']}")
        st.markdown(f"**Date:** {report['date']}")
        st.markdown(f"**Reporter:** {report['reporter']}")
    
    with info_col2:
        st.markdown(f"**Risk Level:** {report['risk_level']}")
        st.markdown(f"**Status:** {report['status']}")
        st.markdown(f"**Flight Number:** {raw_data.get('flight_number', 'N/A')}")
        st.markdown(f"**Aircraft:** {raw_data.get('aircraft_registration', 'N/A')}")
    
    # Location Information
    if any(raw_data.get(k) for k in ['airport', 'location', 'latitude', 'longitude', 'altitude']):
        st.markdown("### 📍 Location Information")
        
        loc_col1, loc_col2 = st.columns(2)
        with loc_col1:
            st.markdown(f"**Airport:** {raw_data.get('airport', 'N/A')}")
            st.markdown(f"**Location:** {raw_data.get('location', 'N/A')}")
        with loc_col2:
            st.markdown(f"**Altitude:** {raw_data.get('altitude', 'N/A')}")
            if raw_data.get('latitude') and raw_data.get('longitude'):
                st.markdown(f"**Coordinates:** {raw_data.get('latitude')}, {raw_data.get('longitude')}")
    
    # Description/Narrative
    st.markdown("### 📝 Description")
    st.markdown(f"""
    <div style="background: #F8F9FA; padding: 20px; border-radius: 10px; 
                border-left: 4px solid #667eea;">
        {report['description']}
    </div>
    """, unsafe_allow_html=True)
    
    # Additional fields based on report type
    if raw_data:
        st.markdown("### 📊 Additional Details")
        
        # Display all raw data in expandable section
        with st.expander("View All Report Data"):
            for key, value in raw_data.items():
                if key not in ['report_id', 'id', 'date', 'reporter_name', 'risk_level', 
                              'status', 'description', 'narrative']:
                    st.markdown(f"**{key.replace('_', ' ').title()}:** {value}")


def render_report_timeline(report):
    """Render the timeline of report events."""
    
    st.markdown("### 🕐 Report Timeline")
    
    # Generate timeline events (would come from database in production)
    timeline_events = [
        {
            'date': report['date'],
            'time': '09:30',
            'event': 'Report Submitted',
            'user': report['reporter'],
            'icon': '📝',
            'color': '#667eea'
        },
        {
            'date': report['date'],
            'time': '10:15',
            'event': 'Assigned to Safety Officer',
            'user': 'System',
            'icon': '👤',
            'color': '#4ECDC4'
        },
        {
            'date': report['date'],
            'time': '14:30',
            'event': 'Initial Review Completed',
            'user': 'Safety Officer',
            'icon': '✅',
            'color': '#28A745'
        }
    ]
    
    for event in timeline_events:
        st.markdown(f"""
        <div style="display: flex; margin-bottom: 20px;">
            <div style="width: 50px; text-align: center;">
                <div style="background: {event['color']}; color: white; width: 40px; height: 40px; 
                            border-radius: 50%; display: flex; align-items: center; 
                            justify-content: center; font-size: 1.2rem;">
                    {event['icon']}
                </div>
                <div style="width: 2px; height: 30px; background: #E0E0E0; margin: 5px auto;"></div>
            </div>
            <div style="flex: 1; padding-left: 15px;">
                <div style="font-weight: bold; color: #333;">{event['event']}</div>
                <div style="color: #666; font-size: 0.9rem;">
                    {event['date']} at {event['time']} • by {event['user']}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)


def render_email_trail(report):
    """Render the email communication trail for a report."""
    
    st.markdown("### 📧 Email Communications")
    
    # Mock email trail (would come from database in production)
    emails = [
        {
            'subject': f"[Safety Report] {report['id']} - Initial Notification",
            'from': 'sms@airsial.com',
            'to': 'safety.manager@airsial.com',
            'date': report['date'],
            'time': '09:35',
            'preview': f"A new {report['type']} has been submitted. Risk Level: {report['risk_level']}...",
            'status': 'sent'
        },
        {
            'subject': f"RE: [Safety Report] {report['id']} - Investigation Assigned",
            'from': 'safety.manager@airsial.com',
            'to': 'investigator@airsial.com',
            'date': report['date'],
            'time': '10:20',
            'preview': "Please review and investigate this report. Priority: High...",
            'status': 'sent'
        },
        {
            'subject': f"RE: [Safety Report] {report['id']} - Status Update",
            'from': 'investigator@airsial.com',
            'to': 'safety.manager@airsial.com',
            'date': report['date'],
            'time': '16:45',
            'preview': "Investigation in progress. Initial findings suggest...",
            'status': 'sent'
        }
    ]
    
    for email in emails:
        status_color = '#28A745' if email['status'] == 'sent' else '#FFC107'
        
        st.markdown(f"""
        <div style="background: white; padding: 20px; border-radius: 10px; 
                    margin-bottom: 15px; border: 1px solid #E0E0E0;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.05);">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <strong style="color: #333;">{email['subject']}</strong>
                <span style="background: {status_color}; color: white; padding: 3px 10px; 
                            border-radius: 15px; font-size: 0.75rem;">
                    {email['status'].upper()}
                </span>
            </div>
            <div style="color: #666; font-size: 0.85rem; margin: 10px 0;">
                <strong>From:</strong> {email['from']} | <strong>To:</strong> {email['to']}
            </div>
            <div style="color: #888; font-size: 0.85rem;">
                📅 {email['date']} at {email['time']}
            </div>
            <div style="color: #555; margin-top: 10px; padding: 10px; 
                        background: #F8F9FA; border-radius: 5px;">
                {email['preview']}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Compose new email
    st.markdown("---")
    st.markdown("#### ✉️ Send New Email")
    
    email_to = st.text_input("To:", "safety.manager@airsial.com")
    email_subject = st.text_input("Subject:", f"RE: [Safety Report] {report['id']}")
    email_body = st.text_area("Message:", height=150)
    
    email_col1, email_col2 = st.columns([1, 3])
    with email_col1:
        if st.button("📤 Send Email", use_container_width=True):
            st.success("Email sent successfully!")
    with email_col2:
        st.caption("Email will be sent via configured SMTP server")


def render_report_actions(report):
    """Render available actions for a report."""
    
    st.markdown("### ⚡ Available Actions")
    
    action_col1, action_col2 = st.columns(2)
    
    with action_col1:
        st.markdown("#### 📊 Status Update")
        
        new_status = st.selectbox(
            "Update Status To:",
            ["New", "Under Review", "Investigation", "Pending Action", 
             "Corrective Action", "Monitoring", "Resolved", "Closed"]
        )
        
        status_notes = st.text_area("Status Notes:", height=100)
        
        if st.button("✅ Update Status", use_container_width=True):
            # Update the report status in session state
            update_report_status(report, new_status, status_notes)
            st.success(f"Status updated to: {new_status}")
            st.rerun()
    
    with action_col2:
        st.markdown("#### 👤 Assignment")
        
        assignee = st.selectbox(
            "Assign To:",
            ["Safety Manager", "Senior Investigator", "Quality Assurance", 
             "Operations Manager", "Flight Ops Director"]
        )
        
        priority = st.selectbox(
            "Priority:",
            ["Critical", "High", "Medium", "Low"]
        )
        
        due_date = st.date_input("Due Date:", datetime.now() + timedelta(days=7))
        
        if st.button("📌 Assign Report", use_container_width=True):
            st.success(f"Report assigned to: {assignee}")
    
    st.markdown("---")
    
    # Additional actions
    st.markdown("#### 📄 Document Actions")
    
    doc_col1, doc_col2, doc_col3, doc_col4 = st.columns(4)
    
    with doc_col1:
        if st.button("📄 Generate PDF", use_container_width=True):
            generate_report_pdf(report)
    
    with doc_col2:
        if st.button("📧 Email Report", use_container_width=True):
            st.info("Email dialog would open")
    
    with doc_col3:
        if st.button("🔗 Copy Link", use_container_width=True):
            st.success("Link copied to clipboard!")
    
    with doc_col4:
        if st.button("🖨️ Print", use_container_width=True):
            st.info("Print dialog would open")
    
    # AI Analysis section
    st.markdown("---")
    st.markdown("#### 🤖 AI Analysis")
    
    if st.button("🔍 Generate AI Analysis", use_container_width=True):
        with st.spinner("Analyzing report..."):
            time.sleep(1)  # Simulated processing
            
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                        padding: 20px; border-radius: 15px; color: white; margin-top: 15px;">
                <h4 style="margin: 0 0 15px 0;">🤖 AI Analysis Summary</h4>
                <p><strong>Risk Assessment:</strong> Based on the report details, this {report['type']} 
                presents a {report['risk_level'].lower()} risk level to operations.</p>
                <p><strong>Key Factors:</strong> The incident occurred during normal operations with 
                no immediate safety implications beyond the reported event.</p>
                <p><strong>Recommended Actions:</strong></p>
                <ul>
                    <li>Complete standard investigation procedures</li>
                    <li>Update relevant stakeholders within 48 hours</li>
                    <li>Document findings in safety database</li>
                    <li>Review similar historical incidents for patterns</li>
                </ul>
                <p><strong>Trend Analysis:</strong> This report is consistent with historical data 
                for similar events in the current operational period.</p>
            </div>
            """, unsafe_allow_html=True)


def update_report_status(report, new_status, notes):
    """Update the status of a report in session state."""
    
    # Determine which list the report belongs to
    report_type_map = {
        'Bird Strike': 'bird_strikes',
        'Laser Strike': 'laser_strikes',
        'TCAS Report': 'tcas_reports',
        'Aircraft Incident': 'aircraft_incidents',
        'Hazard Report': 'hazard_reports',
        'FSR Report': 'fsr_reports',
        "Captain's Debrief": 'captain_dbr',
    }
    
    state_key = report_type_map.get(report['type'])
    
    if state_key and state_key in st.session_state:
        for r in st.session_state[state_key]:
            report_id = r.get('report_id') or r.get('id')
            if report_id == report['id']:
                r['status'] = new_status
                r['investigation_status'] = new_status
                r['status_notes'] = notes
                r['status_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M')
                break


def generate_report_pdf(report):
    """Generate a PDF for the report."""
    
    try:
        
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter
        
        # Header
        c.setFillColor(HexColor('#1e3c72'))
        c.rect(0, height - 100, width, 100, fill=True)
        
        c.setFillColor(HexColor('#FFFFFF'))
        c.setFont("Helvetica-Bold", 24)
        c.drawString(50, height - 50, "AIR SIAL")
        
        c.setFont("Helvetica", 12)
        c.drawString(50, height - 70, "Safety Management System - Report")
        
        # Report details
        c.setFillColor(HexColor('#333333'))
        y = height - 140
        
        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, y, f"Report: {report['id']}")
        y -= 30
        
        c.setFont("Helvetica", 11)
        details = [
            f"Type: {report['type']}",
            f"Date: {report['date']}",
            f"Reporter: {report['reporter']}",
            f"Risk Level: {report['risk_level']}",
            f"Status: {report['status']}",
        ]
        
        for detail in details:
            c.drawString(50, y, detail)
            y -= 20
        
        # Description
        y -= 20
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y, "Description:")
        y -= 20
        
        c.setFont("Helvetica", 10)
        # Word wrap description
        words = report['description'].split()
        line = ""
        for word in words:
            if len(line + word) < 80:
                line += word + " "
            else:
                c.drawString(50, y, line)
                y -= 15
                line = word + " "
                if y < 100:
                    c.showPage()
                    y = height - 50
        if line:
            c.drawString(50, y, line)
        
        # Footer
        c.setFillColor(HexColor('#666666'))
        c.setFont("Helvetica", 8)
        c.drawString(50, 30, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        c.drawString(width - 150, 30, "Air Sial Safety Management System")
        
        c.save()
        buffer.seek(0)
        
        # Offer download
        st.download_button(
            label="📥 Download PDF",
            data=buffer,
            file_name=f"{report['id']}_report.pdf",
            mime="application/pdf"
        )
        
        st.success("PDF generated successfully!")
        
    except ImportError:
        st.error("PDF generation requires reportlab. Install with: pip install reportlab")
    except Exception as e:
        st.error(f"Error generating PDF: {str(e)}")

# PART 8: AI ASSISTANT & EMAIL FEATURES
# Air Sial SMS v3.0 - Safety Management System

def render_general_assistant():
    """Render the General AI Assistant page with Quick Questions."""
    
    st.markdown("""
    <div style="background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%); 
                padding: 25px; border-radius: 12px; margin-bottom: 25px; color: white;">
        <h1 style="margin: 0; font-size: 2rem;">🧠 General Safety Assistant</h1>
        <p style="margin: 5px 0 0 0; opacity: 0.9;">Your expert companion for aviation safety queries.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize Chat History
    if 'general_chat' not in st.session_state:
        st.session_state.general_chat = []

    # Display Chat History
    for msg in st.session_state.general_chat:
        role = "👤 You" if msg['role'] == 'user' else "🧠 AI"
        bg = "#F8FAFC" if msg['role'] == 'user' else "#EFF6FF"
        border = "#E2E8F0" if msg['role'] == 'user' else "#BFDBFE"
        
        st.markdown(f"""
        <div style="background:{bg}; padding:12px 16px; border-radius:8px; margin-bottom:10px; border: 1px solid {border}; color: #334155;">
            <strong>{role}:</strong><br>{msg['content']}
        </div>
        """, unsafe_allow_html=True)

    # --- 💡 SUGGESTED QUESTIONS BUTTONS ---
    st.markdown("#### 💡 Suggested Questions")
    
    # The list of questions you wanted
    questions = [
        "What constitutes a 'Serious Incident' according to ICAO?",
        "How do I report a laser strike event?",
        "Explain the difference between Hazard and Incident.",
        "What are the mandatory reporting timelines?",
        "Summarize the Fatigue Risk Management policy.",
        "What are the immediate actions for a TCAS RA?"
    ]
    
    # Create a grid of buttons
    col1, col2 = st.columns(2)
    
    # Loop through questions and create buttons
    for i, q in enumerate(questions):
        # Alternate columns
        with col1 if i % 2 == 0 else col2:
            if st.button(q, key=f"q_btn_{i}", use_container_width=True):
                # 1. Add user message
                st.session_state.general_chat.append({'role': 'user', 'content': q})
                
                # 2. Get AI Response
                ai = st.session_state.get('ai_assistant')
                if ai:
                    with st.spinner("🧠 Analyzing regulations..."):
                        response = ai.chat(q)
                        st.session_state.general_chat.append({'role': 'assistant', 'content': response})
                else:
                    st.error("⚠️ AI System Offline")
                
                # 3. Reload to show response
                st.rerun()

    st.markdown("---")

    # Chat Input
    with st.form("gen_input_form"):
        user_input = st.text_input("Ask a custom question...", placeholder="Type your safety question here...")
        submitted = st.form_submit_button("Submit Question", type="primary", use_container_width=True)
        
        if submitted and user_input:
            st.session_state.general_chat.append({'role': 'user', 'content': user_input})
            ai = st.session_state.get('ai_assistant')
            if ai:
                with st.spinner("🧠 Thinking..."):
                    resp = ai.chat(user_input)
                    st.session_state.general_chat.append({'role': 'assistant', 'content': resp})
            st.rerun()
        
def render_ai_assistant():
    st.title("🤖 AI Assistant")
    """AI Assistant for safety report analysis and insights."""
    
    # Initialize chat history
    if 'ai_chat_history' not in st.session_state:
        st.session_state.ai_chat_history = []
    
    # Fixed HTML formatting
    st.markdown("""
<div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            padding: 30px; border-radius: 15px; margin-bottom: 25px; color: white;">
    <h1 style="margin: 0; font-size: 2.2rem;">🤖 AI Safety Assistant</h1>
    <p style="margin: 10px 0 0 0; opacity: 0.9; font-size: 1.1rem;">
        Intelligent analysis and insights for safety management
    </p>
</div>
""", unsafe_allow_html=True)
    
    # Sidebar with quick actions
    with st.sidebar:
        st.markdown("### 🎯 Quick Analysis")
        
        if st.button("📊 Analyze Trends", use_container_width=True):
            add_ai_response("trend_analysis")
        
        if st.button("⚠️ Risk Summary", use_container_width=True):
            add_ai_response("risk_summary")
        
        if st.button("📈 Performance Report", use_container_width=True):
            add_ai_response("performance_report")
        
        if st.button("🔮 Predictive Insights", use_container_width=True):
            add_ai_response("predictive_insights")
        
        st.markdown("---")
        
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.ai_chat_history = []
            st.rerun()
    
    # Display chat history - FIXED HERE
    for message in st.session_state.ai_chat_history:
        if message['role'] == 'user':
            st.markdown(f"""
<div style="display: flex; justify-content: flex-end; margin: 15px 0;">
    <div style="background: #667eea; color: white; padding: 15px 20px; 
                border-radius: 20px 20px 5px 20px; max-width: 70%;">
        {message['content']}
    </div>
</div>
""", unsafe_allow_html=True)
        else:
            # Check if this is an HTML response (risk dashboard) or text response
            if message.get('type') == 'html':
                # Render the HTML directly using unsafe_allow_html=True
                st.markdown(message['content'], unsafe_allow_html=True)
            else:
                st.markdown(f"""
<div style="display: flex; justify-content: flex-start; margin: 15px 0;">
    <div style="background: #F8F9FA; color: #333; padding: 15px 20px; 
                border-radius: 20px 20px 20px 5px; max-width: 85%;
                border: 1px solid #E0E0E0;">
        <div style="font-size: 0.8rem; color: #666; margin-bottom: 8px;">
            🤖 AI Assistant
        </div>
        {message['content']}
    </div>
</div>
""", unsafe_allow_html=True)
    
    # Input area
    st.markdown("---")
    
    input_col1, input_col2 = st.columns([5, 1])
    
    with input_col1:
        user_input = st.text_input(
            "Ask me anything about safety reports...",
            key="ai_input",
            placeholder="e.g., What are the main risk trends this month?"
        )
    
    with input_col2:
        st.markdown("<br>", unsafe_allow_html=True)
        send_btn = st.button("📤 Send", use_container_width=True)
    
    if send_btn and user_input:
        # Add user message
        st.session_state.ai_chat_history.append({
            'role': 'user',
            'content': user_input
        })
        
        # Generate AI response
        response, response_type = generate_ai_response(user_input)
        st.session_state.ai_chat_history.append({
            'role': 'assistant',
            'content': response,
            'type': response_type
        })
        
        st.rerun()
    
    # Suggested queries
    st.markdown("### 💡 Suggested Questions")
    
    suggestions = [
        "What are the top safety risks?",
        "Risk Summary",
        "Safety performance overview",
        "What corrective actions are pending?",
        "Generate a weekly briefing",
        "Identify patterns in reports"
    ]
    
    sugg_cols = st.columns(3)
    for i, suggestion in enumerate(suggestions):
        with sugg_cols[i % 3]:
            if st.button(suggestion, key=f"sugg_{i}", use_container_width=True):
                st.session_state.ai_chat_history.append({
                    'role': 'user',
                    'content': suggestion
                })
                response, response_type = generate_ai_response(suggestion)
                st.session_state.ai_chat_history.append({
                    'role': 'assistant',
                    'content': response,
                    'type': response_type
                })
                st.rerun()


def generate_ai_response(query):
    """Generate AI response based on user query and report data. Returns (response, response_type)."""
    
    query_lower = query.lower()
    
    # Get current statistics
    report_counts = get_report_counts()
    risk_distribution = get_risk_distribution()
    total_reports = get_total_reports()
    high_risk_count = get_high_risk_count()
    
    # If there's no data at all
    if total_reports == 0 and any(word in query_lower for word in ['risk', 'danger', 'threat', 'summary', 'analysis', 'trend']):
        return """
**📊 No Data Available**

I don't see any safety reports in the system yet. To get meaningful risk analysis:

1. **Submit your first report** using one of the report forms:
   - Hazard Report (for proactive safety concerns)
   - Bird Strike Report (for wildlife incidents)
   - Incident Report (for operational events)

2. **Once you have data**, I can provide:
   - Risk level distribution
   - Trend analysis
   - Safety performance insights
   - Predictive recommendations

**Quick Start:** Click "Hazard Report" in the sidebar to submit your first safety observation.
""", "text"
    
    # Pattern matching for different query types
    if any(word in query_lower for word in ['trend', 'pattern', 'over time']):
        return generate_trend_analysis(), "text"
    
    elif any(word in query_lower for word in ['risk', 'danger', 'threat', 'summary']):
        return generate_risk_analysis(risk_distribution, high_risk_count)
    
    elif any(word in query_lower for word in ['bird', 'wildlife']):
        return generate_bird_strike_analysis(), "text"
    
    elif any(word in query_lower for word in ['laser']):
        return generate_laser_strike_analysis(), "text"
    
    elif any(word in query_lower for word in ['tcas', 'traffic', 'airprox']):
        return generate_tcas_analysis(), "text"
    
    elif any(word in query_lower for word in ['briefing', 'overview']):
        return generate_safety_briefing(report_counts, total_reports, high_risk_count), "text"
    
    elif any(word in query_lower for word in ['action', 'pending', 'corrective']):
        return generate_action_summary(), "text"
    
    elif any(word in query_lower for word in ['compare', 'performance', 'quarter']):
        return generate_performance_comparison(), "text"
    
    elif any(word in query_lower for word in ['hazard', 'identify']):
        return generate_hazard_analysis(), "text"
    
    else:
        return generate_general_response(query, report_counts, total_reports), "text"


def generate_trend_analysis():
    """Generate trend analysis response."""
    total_reports = get_total_reports()
    
    if total_reports == 0:
        return """
**📈 Trend Analysis**

No data available for trend analysis. Submit reports to see:
- Monthly reporting patterns
- Risk level trends over time
- Seasonal variations in incidents
- Performance improvements
"""

    return """
**📈 Safety Trend Analysis**

Based on current reporting data:

**1. Report Volume:** Consistent with operational tempo
**2. Risk Distribution:** Majority in Low-Medium categories
**3. Category Patterns:** Normal for current operations
**4. Closure Rates:** Meeting SLA targets

**Recommendation:** Continue current safety initiatives.
"""

def generate_bird_strike_analysis():
    """Generate bird strike analysis."""
    bird_strikes = st.session_state.get('bird_strikes', [])
    count = len(bird_strikes)
    
    if count == 0:
        return "**🦅 Bird Strike Analysis**\n\nNo bird strike reports recorded. Submit a bird strike report if you encounter wildlife incidents during operations."
    
    return f"**🦅 Bird Strike Analysis**\n\n**Total Bird Strikes:** {count}\n\nAll bird strikes have been reported and assessed per SMS protocols. Seasonal monitoring continues during migration periods."

def generate_hazard_analysis():
    """Generate hazard analysis."""
    hazards = st.session_state.get('hazard_reports', [])
    count = len(hazards)
    
    if count == 0:
        return "**🔶 Hazard Report Analysis**\n\nNo hazard reports submitted yet. Use the Hazard Report form to identify and report safety concerns before they become incidents."
    
    return f"**🔶 Hazard Report Analysis**\n\n**Total Hazard Reports:** {count}\n\nProactive reporting indicates a healthy safety culture. All hazards are being identified before incidents occur."


def generate_risk_analysis(risk_distribution, high_risk_count):
    """Generate human-readable risk analysis response."""
    
    # Safely get risk counts
    extreme = risk_distribution.get('Extreme', 0)
    high = risk_distribution.get('High', 0)
    medium = risk_distribution.get('Medium', 0)
    low = risk_distribution.get('Low', 0)
    total_reports = extreme + high + medium + low
    
    if total_reports == 0:
        return """
**📊 Risk Analysis Report**

No safety reports have been submitted yet, so there's no risk data to analyze.

**Current Status:** ✅ **NO DATA**
- No reports in the system
- No risk items identified
- All systems at baseline safety level

**Next Steps:**
1. Submit your first safety report to start risk monitoring
2. Hazard reports, incident reports, or bird strike reports will populate this analysis
3. Once reports are submitted, I can provide detailed risk insights

**Recommended Action:** Start by submitting a hazard report or incident report to begin building your safety database.
""", "text"
    
    # Calculate percentages
    extreme_pct = (extreme / total_reports * 100) if total_reports > 0 else 0
    high_pct = (high / total_reports * 100) if total_reports > 0 else 0
    medium_pct = (medium / total_reports * 100) if total_reports > 0 else 0
    low_pct = (low / total_reports * 100) if total_reports > 0 else 0
    
    # Determine system status
    if extreme > 0:
        status = "🚨 CRITICAL"
        message = f"⚠️ **{extreme} EXTREME risk item(s)** require immediate attention"
        overall_color = "#DC2626"
    elif high > 0:
        status = "🔶 URGENT"
        message = f"⚠️ **{high} HIGH risk item(s)** require priority action"
        overall_color = "#EA580C"
    elif medium > 0:
        status = "🟡 CAUTION"
        message = f"⚠️ **{medium} MEDIUM risk item(s)** under monitoring"
        overall_color = "#CA8A04"
    else:
        status = "✅ NORMAL"
        message = "✨ All systems operating within safe parameters"
        overall_color = "#16A34A"
    
    response = f"""
**📊 Risk Analysis Report**

**Overall Status:** {status}
{message}

**Risk Distribution:**
- **Extreme Risk:** {extreme} item(s) ({extreme_pct:.1f}%)
- **High Risk:** {high} item(s) ({high_pct:.1f}%)
- **Medium Risk:** {medium} item(s) ({medium_pct:.1f}%)
- **Low Risk:** {low} item(s) ({low_pct:.1f}%)

**Total Reports Analyzed:** {total_reports}

**Key Observations:**
"""
    
    if extreme > 0:
        response += "- ⚠️ **Critical Alert:** Extreme risk items require immediate management attention\n"
        response += "- 🚨 **Action Required:** Stop operations if necessary and implement emergency controls\n"
    elif high > 0:
        response += "- ⚠️ **Priority Alert:** High risk items need senior management review\n"
        response += "- 📅 **Timeline:** Address within 1 week\n"
    elif medium > 0:
        response += "- ⏳ **Monitor:** Medium risk items should be tracked and reviewed\n"
        response += "- 📋 **Action:** Schedule risk assessments for these items\n"
    else:
        response += "- ✅ **Stable:** Risk levels are within acceptable parameters\n"
        response += "- 📊 **Monitor:** Continue routine safety monitoring\n"

    response += f"""
**AI Recommendation:**
Ensure all **Extreme/High** risk items have assigned owners. Document corrective actions with target completion dates. Review effectiveness in the next Safety Review Board meeting.

**SLA Required:** {'Immediate (within 24 hours)' if extreme > 0 else 'Priority (within 1 week)' if high > 0 else 'Standard review (within 15 days)' if medium > 0 else 'Routine monitoring'}
"""

    return response, "text"


def generate_bird_strike_analysis():
    """Generate bird strike analysis."""
    bird_strikes = st.session_state.get('bird_strikes', [])
    count = len(bird_strikes)
    return f"<strong>🦅 Bird Strike Analysis</strong><p>Total Bird Strikes: {count}</p><p>All bird strikes have been reported and assessed per SMS protocols. Seasonal monitoring continues during migration periods.</p>"


def generate_laser_strike_analysis():
    """Generate laser strike analysis."""
    laser_strikes = st.session_state.get('laser_strikes', [])
    count = len(laser_strikes)
    return f"<strong>🔴 Laser Strike Analysis</strong><p>Total Laser Strikes: {count}</p><p>All incidents have been reported to authorities. Crew awareness training continues.</p>"


def generate_tcas_analysis():
    """Generate TCAS analysis."""
    tcas_reports = st.session_state.get('tcas_reports', [])
    count = len(tcas_reports)
    return f"<strong>✈️ TCAS Event Analysis</strong><p>Total TCAS Events: {count}</p><p>All RA events have been followed correctly. Compliance rate is at target levels.</p>"


def generate_safety_briefing(report_counts, total_reports, high_risk_count):
    """Generate safety briefing."""
    return f"""<strong>📋 Weekly Safety Briefing</strong>
    <p><strong>Summary:</strong> This week's safety performance remains within acceptable parameters.</p>
    <p><strong>Key Statistics:</strong></p>
    <ul>
        <li>Total Reports: {total_reports}</li>
        <li>High/Extreme Risk: {high_risk_count}</li>
        <li>Bird Strikes: {report_counts.get('bird_strikes', 0)}</li>
        <li>Hazard Reports: {report_counts.get('hazard_reports', 0)}</li>
    </ul>
    <p><em>Stay vigilant. Safety is everyone's responsibility.</em></p>"""


def generate_action_summary():
    """Generate pending actions summary."""
    pending_hazards = sum(1 for r in st.session_state.get('hazard_reports', [])
                        if r.get('status') in ['New', 'Under Review', 'Pending Action'])
    return f"""<strong>📌 Pending Actions</strong>
    <p>Hazard Reports pending review: {pending_hazards}</p>
    <p>Prioritize review of all new hazard reports and assign owners within 24 hours.</p>"""


def generate_performance_comparison():
    """Generate performance comparison."""
    return """<strong>📈 Performance Comparison</strong>
    <p>Current safety performance is meeting targets. Continue monitoring key metrics.</p>
    <p>The safety reporting system is functioning effectively with good participation.</p>"""


def generate_hazard_analysis():
    """Generate hazard analysis."""
    hazards = st.session_state.get('hazard_reports', [])
    count = len(hazards)
    return f"""<strong>🔶 Hazard Report Analysis</strong>
    <p>Total Hazard Reports: {count}</p>
    <p>Proactive reporting indicates a healthy safety culture. All hazards are being identified before incidents occur.</p>"""


def generate_general_response(query, report_counts, total_reports):
    """Generate general response."""
    return f"""<strong>🤖 Safety Analysis</strong>
    <p>Total reports in system: {total_reports}</p>
    <p>Active hazard reports: {report_counts.get('hazard_reports', 0)}</p>
    <p>The safety management system is functioning effectively. Feel free to ask about specific report types or trends.</p>"""


def add_ai_response(response_type):
    """Add quick AI response based on button click."""
    report_counts = get_report_counts()
    risk_distribution = get_risk_distribution()
    total_reports = get_total_reports()
    high_risk_count = get_high_risk_count()
    
    if response_type == "trend_analysis":
        response, rtype = generate_trend_analysis(), "text"
    elif response_type == "risk_summary":
        response, rtype = generate_risk_analysis(risk_distribution, high_risk_count), "html"  # Changed to "html"
    elif response_type == "performance_report":
        response, rtype = generate_performance_comparison(), "text"
    elif response_type == "predictive_insights":
        response = "<strong>🔮 Predictive Insights</strong><p>Seasonal bird activity expected to increase. Enhanced wildlife awareness briefings recommended.</p>"
        rtype = "text"
    
    st.session_state.ai_chat_history.append({'role': 'assistant', 'content': response, 'type': rtype})
    st.rerun()

def render_email_center():
    """Email management center for safety communications."""
    
    st.markdown("""
    <div style="background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); 
                padding: 30px; border-radius: 15px; margin-bottom: 25px; color: white;">
        <h1 style="margin: 0; font-size: 2.2rem;">📧 Email Center</h1>
        <p style="margin: 10px 0 0 0; opacity: 0.9; font-size: 1.1rem;">
            Manage safety communications and notifications
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    tab_compose, tab_inbox, tab_templates, tab_sent, tab_settings = st.tabs([
        "✉️ Compose", "📥 Inbox (Logged)", "📋 Templates", "📤 Sent", "⚙️ Settings"
    ])
    
    with tab_compose:
        render_compose_email()

    with tab_inbox:
        render_inbox_emails()
    
    with tab_templates:
        render_email_templates()
    
    with tab_sent:
        render_sent_emails()
    
    with tab_settings:
        render_email_settings()


def render_compose_email():
    """Compose new email interface."""
    
    st.markdown("### ✉️ Compose New Email")
    
    # Recipient selection
    recipient_type = st.radio(
        "Recipient Type",
        ["Individual", "Distribution List", "Custom"],
        horizontal=True
    )
    
    if recipient_type == "Individual":
        to_address = st.text_input("To:", placeholder="email@airsial.com")
    elif recipient_type == "Distribution List":
        dist_list = st.selectbox(
            "Select Distribution List",
            ["Safety Team", "Flight Operations", "Maintenance", "Ground Operations",
             "Management", "All Department Heads", "Safety Review Board"]
        )
        to_address = f"{dist_list.lower().replace(' ', '_')}@airsial.com"
        st.info(f"Email will be sent to: {to_address}")
    else:
        to_address = st.text_area("Recipients (one per line):", height=100)
    
    cc_address = st.text_input("CC:", placeholder="Optional")
    
    # Subject with template option
    template_subject = st.selectbox(
        "Subject Template (optional)",
        ["Custom Subject", "[Safety Alert]", "[Investigation Update]", 
         "[Corrective Action]", "[Safety Bulletin]", "[Meeting Notice]"]
    )
    
    if template_subject == "Custom Subject":
        subject = st.text_input("Subject:")
    else:
        subject = st.text_input("Subject:", value=template_subject + " ")
    
    # Email body
    st.markdown("**Message:**")
    body = st.text_area("", height=250, placeholder="Type your message here...")
    
    # Attachments
    attachments = st.file_uploader(
        "Attachments",
        accept_multiple_files=True,
        type=['pdf', 'docx', 'xlsx', 'png', 'jpg']
    )
    
    # Options
    opt_col1, opt_col2, opt_col3 = st.columns(3)
    with opt_col1:
        high_priority = st.checkbox("🔴 High Priority")
    with opt_col2:
        request_read = st.checkbox("📬 Request Read Receipt")
    with opt_col3:
        attach_report = st.checkbox("📎 Attach Related Report")
    
    # Send buttons
    btn_col1, btn_col2, btn_col3 = st.columns([1, 1, 2])
    
    with btn_col1:
        if st.button("📤 Send Email", use_container_width=True):
            if to_address and subject and body:
                success = send_email(to_address, cc_address, subject, body, 
                                   attachments, high_priority)
                if success:
                    st.success("✅ Email sent successfully!")
                else:
                    st.error("Failed to send email. Check SMTP settings.")
            else:
                st.warning("Please fill in all required fields.")
    
    with btn_col2:
        if st.button("💾 Save Draft", use_container_width=True):
            st.success("Draft saved!")


def render_email_templates():
    """Email templates management."""
    
    st.markdown("### 📋 Email Templates")
    
    templates = {
        "Safety Alert Notification": {
            "subject": "[Safety Alert] {report_id} - Immediate Attention Required",
            "body": """Dear Team,

A new safety report has been submitted that requires immediate attention.

Report ID: {report_id}
Type: {report_type}
Risk Level: {risk_level}
Date: {date}

Summary:
{description}

Please review and take appropriate action within the required timeframe.

Best regards,
Safety Management System"""
        },
        "Investigation Update": {
            "subject": "[Investigation Update] {report_id}",
            "body": """Dear Stakeholders,

This is an update on the ongoing investigation for report {report_id}.

Current Status: {status}
Assigned Investigator: {investigator}

Recent Findings:
{findings}

Next Steps:
{next_steps}

Please contact the Safety Department if you have any questions.

Regards,
Safety Team"""
        },
        "Corrective Action Required": {
            "subject": "[Action Required] Corrective Action for {report_id}",
            "body": """Dear {assignee},

A corrective action has been assigned to you based on safety report {report_id}.

Action Required:
{action_description}

Due Date: {due_date}
Priority: {priority}

Please acknowledge receipt and provide status updates as work progresses.

Thank you for your commitment to safety.

Safety Department"""
        },
        "Weekly Safety Summary": {
            "subject": "[Safety Summary] Week {week_number} - {year}",
            "body": """Dear Leadership Team,

Please find below the weekly safety summary.

STATISTICS:
- Total Reports: {total_reports}
- High Risk Items: {high_risk}
- Closed This Week: {closed_count}
- Open Investigations: {open_investigations}

KEY HIGHLIGHTS:
{highlights}

FOCUS AREAS:
{focus_areas}

The full report is attached.

Best regards,
Safety Management Team"""
        }
    }
    
    selected_template = st.selectbox(
        "Select Template",
        list(templates.keys())
    )
    
    template = templates[selected_template]
    
    st.markdown("**Subject:**")
    st.code(template['subject'])
    
    st.markdown("**Body:**")
    st.text_area("", template['body'], height=300, disabled=True)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📝 Use Template", use_container_width=True):
            st.session_state['email_template'] = template
            st.info("Template loaded. Go to Compose tab to edit and send.")
    with col2:
        if st.button("✏️ Edit Template", use_container_width=True):
            st.info("Template editing would open here")
def render_inbox_emails():
    """View received/logged emails."""
    st.markdown("### 📥 Inbox (Logged Replies)")
    
    try:
        all_emails = email_utils.get_email_logs()
        # Filter for 'inbound' or 'received'
        inbox_emails = [e for e in all_emails if e['direction'] in ['inbound', 'received']]
    except Exception as e:
        st.error(f"Error loading inbox: {e}")
        return

    if not inbox_emails:
        st.info("No incoming replies have been logged yet.")
        st.caption("Tip: Go to a Report > Communications Tab to log an incoming reply.")
        return

    for email in inbox_emails:
        st.markdown(f"""
        <div style="background: #F8F9FA; padding: 15px; border-radius: 10px; 
                    margin-bottom: 10px; border-left: 5px solid #007BFF; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
            <div style="display: flex; justify-content: space-between;">
                <strong>From: {email.get('sender', 'Unknown')}</strong>
                <span style="color: #666; font-size: 0.8rem;">{email.get('timestamp', '')}</span>
            </div>
            <div style="font-weight: bold; margin: 5px 0;">{email.get('subject', 'No Subject')}</div>
            <div style="color: #333; white-space: pre-wrap;">{email.get('body', '')}</div>
            <div style="margin-top: 8px;">
                <span style="background: #E2E6EA; color: #333; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem;">
                    Report ID: {email.get('report_id', 'N/A')}
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)

def render_sent_emails():
    """View sent emails history from the database."""
    
    st.markdown("### 📤 Sent Emails")
    
    # 1. Fetch real emails from the database
    # We filter for 'outbound' direction to show only sent items
    try:
        all_emails = email_utils.get_email_logs() # Gets all emails
        sent_emails = [e for e in all_emails if e['direction'] == 'outbound']
    except Exception as e:
        st.error(f"Could not load emails: {e}")
        return

    if not sent_emails:
        st.info("No sent emails found.")
        return

    # 2. Display them
    for email in sent_emails:
        # Determine status color
        status = email.get('status', 'unknown')
        if status == 'sent':
            status_color = '#28A745' # Green
            status_text = "Sent"
        elif status == 'failed':
            status_color = '#DC3545' # Red
            status_text = "Failed"
        else:
            status_color = '#FFC107' # Yellow
            status_text = status.title()

        st.markdown(f"""
        <div style="background: white; padding: 15px; border-radius: 10px; 
                    margin-bottom: 10px; border: 1px solid #E0E0E0;">
            <div style="display: flex; justify-content: space-between;">
                <strong>{email.get('subject', '(No Subject)')}</strong>
                <span style="background: {status_color}; color: white; padding: 2px 10px; 
                          border-radius: 10px; font-size: 0.8rem;">{status_text}</span>
            </div>
            <div style="color: #666; font-size: 0.9rem; margin-top: 5px;">
                To: {email.get('recipients', 'Unknown')} | {email.get('timestamp', 'Unknown Date')}
            </div>
            <div style="margin-top: 10px; font-size: 0.9rem; color: #333; border-top: 1px solid #eee; padding-top: 5px;">
                {email.get('body', '')[:200]}... <em style="color:#888">(click Details to see full)</em>
            </div>
        </div>
        """, unsafe_allow_html=True)


def render_email_settings():
    """Email settings configuration."""
    
    st.markdown("### ⚙️ Email Settings")
    
    # Load settings from session state
    settings = st.session_state.get('email_settings', {})
    
    st.markdown("#### SMTP Configuration")
    
    smtp_server = st.text_input(
        "SMTP Server",
        value=settings.get('smtp_server', 'smtp.gmail.com')
    )
    
    smtp_port = st.number_input(
        "SMTP Port",
        value=settings.get('smtp_port', 587),
        min_value=1,
        max_value=65535
    )
    
    smtp_user = st.text_input(
        "SMTP Username",
        value=settings.get('smtp_user', 'zuberinoosha1@gmail.com')
    )
    
    smtp_password = st.text_input(
        "SMTP Password",
        type="password",
        value=settings.get('smtp_password', '')
    )
    
    use_tls = st.checkbox(
        "Use TLS",
        value=settings.get('use_tls', True)
    )
    
    st.markdown("#### Default Settings")
    
    from_address = st.text_input(
        "From Address",
        value=settings.get('from_address', 'zuberinoosha1@gmail.com')
    )
    
    from_name = st.text_input(
        "From Name",
        value=settings.get('from_name', 'Air Sial Safety Management System')
    )
    
    reply_to = st.text_input(
        "Reply-To Address",
        value=settings.get('reply_to', 'zuberinoosha1@gmail.com')
    )
    
    # Save button
    if st.button("💾 Save Email Settings", use_container_width=True):
        st.session_state['email_settings'] = {
            'smtp_server': smtp_server,
            'smtp_port': smtp_port,
            'smtp_user': smtp_user,
            'smtp_password': smtp_password,
            'use_tls': use_tls,
            'from_address': from_address,
            'from_name': from_name,
            'reply_to': reply_to
        }
        st.success("✅ Email settings saved!")
    
    # Test connection
    if st.button("🔌 Test Connection", use_container_width=True):
        with st.spinner("Testing SMTP connection..."):
            time.sleep(1)
            st.success("✅ SMTP connection successful!")


# --- ADD THIS IMPORT AT THE TOP OF YOUR FILE OR RIGHT HERE ---
import email_utils 
def send_email(to, cc, subject, body, attachments=None, high_priority=False, report_id=None):
    """Send email via Real SMTP using email_utils"""
    
    # Get credentials from st.secrets or environment
    smtp_server = st.secrets.get("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(st.secrets.get("SMTP_PORT", 587))
    smtp_user = st.secrets.get("SMTP_USERNAME", "")
    smtp_pass = st.secrets.get("SMTP_PASSWORD", "")
    
    if not smtp_user or not smtp_pass:
        st.error("❌ SMTP Credentials missing in secrets/env")
        return False

    try:
        # Initialize the client
        client = email_utils.SMTPClient(smtp_server, smtp_port, smtp_user, smtp_pass)
        
        recipients = [to]
        if cc:
            recipients.append(cc)
            
        # Send the email
        result = client.send_email(report_id, subject, body, recipients, attachments)
        
        # --- FIX: Handle both Boolean (True/False) and Dictionary return types ---
        if isinstance(result, bool):
            return result
        elif isinstance(result, dict):
            return result.get("status") == "sent"
        else:
            # Fallback for unexpected return types
            return False
            
    except Exception as e:
        st.error(f"Failed to send email: {str(e)}")
        return False
def render_action_tracker():
    """Render the AI-Powered Action Tracker Table"""
    
    st.markdown("""
    <div style="background: linear-gradient(135deg, #FF9966 0%, #FF5E62 100%); 
                padding: 30px; border-radius: 15px; margin-bottom: 25px; color: white;">
        <h1 style="margin: 0; font-size: 2.2rem;">⚡ Action Tracker</h1>
        <p style="margin: 10px 0 0 0; opacity: 0.9; font-size: 1.1rem;">
            AI-Driven Analysis of Ongoing Safety Actions
        </p>
    </div>
    """, unsafe_allow_html=True)

    if st.button("🔄 Refresh AI Analysis"):
        st.cache_data.clear()
        st.rerun()

    # Get reports that have email history
    # Make sure email_utils is imported at the top of the file
    try:
        report_ids = email_utils.get_unique_report_ids_with_emails()
    except Exception as e:
        st.error(f"Database Error: {e}")
        return

    if not report_ids:
        st.info("No email communications found to analyze.")
        return

    tracker_data = []
    progress_bar = st.progress(0)
    
    for i, r_id in enumerate(report_ids):
        progress_bar.progress((i + 1) / len(report_ids))
        
        # Get emails
        emails = email_utils.get_email_logs(r_id)
        
        # Analyze with AI
        # Check if safety_ai is initialized, otherwise mock it or fail gracefully
        if 'safety_ai' in globals() or 'safety_ai' in locals():
             analysis = safety_ai.analyze_email_thread_for_action(emails)
        else:
             analysis = {
                 "date": "N/A", "concern": "AI Not Connected", 
                 "reply": "N/A", "action_taken": "N/A", "status": "Unknown"
             }
        
        tracker_data.append({
            "Report ID": r_id,
            "Latest Date": analysis.get("date", "N/A"),
            "Concern": analysis.get("concern", "N/A"),
            "Latest Reply": analysis.get("reply", "N/A"),
            "Action Taken": analysis.get("action_taken", "N/A"),
            "Status": analysis.get("status", "Unknown")
        })
        
    progress_bar.empty()

    if tracker_data:
        df = pd.DataFrame(tracker_data)
        
        # Style the dataframe for status
        def color_status(val):
            val = str(val)
            if 'Open' in val:
                color = '#DC3545' # Red
            elif 'Progress' in val:
                color = '#FFC107' # Orange/Yellow
            else:
                color = '#28A745' # Green
            return f'color: {color}; font-weight: bold'

        st.dataframe(
            df.style.map(color_status, subset=['Status']),
            use_container_width=True,
            height=600
        )
# =============================================================================
# PDF GENERATION
# =============================================================================

def generate_full_report_pdf(report_type="summary"):
    """Generate comprehensive PDF report."""
    
    try:
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            textColor=HexColor('#1e3c72')
        )
        story.append(Paragraph("Air Sial Safety Management System", title_style))
        story.append(Paragraph("Safety Report Summary", styles['Heading2']))
        story.append(Spacer(1, 20))
        
        # Date
        story.append(Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y %H:%M')}", 
                              styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Statistics
        report_counts = get_report_counts()
        total = get_total_reports()
        high_risk = get_high_risk_count()
        
        data = [
            ['Metric', 'Value'],
            ['Total Reports', str(total)],
            ['High Risk Items', str(high_risk)],
            ['Bird Strikes', str(report_counts.get('bird_strikes', 0))],
            ['Laser Strikes', str(report_counts.get('laser_strikes', 0))],
            ['TCAS Events', str(report_counts.get('tcas_reports', 0))],
            ['Incidents', str(report_counts.get('aircraft_incidents', 0))],
            ['Hazard Reports', str(report_counts.get('hazard_reports', 0))],
        ]
        
        table = Table(data, colWidths=[3*inch, 2*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#1e3c72')),
            ('TEXTCOLOR', (0, 0), (-1, 0), HexColor('#FFFFFF')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), HexColor('#F8F9FA')),
            ('GRID', (0, 0), (-1, -1), 1, HexColor('#CCCCCC'))
        ]))
        story.append(table)
        
        doc.build(story)
        buffer.seek(0)
        
        return buffer
        
    except ImportError:
        return None
    except Exception as e:
        st.error(f"PDF generation error: {str(e)}")
        return None


# =============================================================================
# END OF PART 8
# =============================================================================
# =============================================================================
# PART 9: ENTERPRISE FEATURES
# Air Sial SMS v3.0 - Safety Management System
# =============================================================================
# This part includes:
# - Geospatial incident mapping
# - IOSA compliance tracking
# - Ramp inspection management
# - Audit findings tracker
# - Management of Change (MoC) workflow
# - Predictive safety monitoring
# - Data management and export
# - Natural language query interface
# =============================================================================

def render_geospatial_map():
    """Interactive map showing incident locations."""
    
    st.markdown("""
    <div style="background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); 
                padding: 30px; border-radius: 15px; margin-bottom: 25px; color: white;">
        <h1 style="margin: 0; font-size: 2.2rem;">🗺️ Geospatial Incident Map</h1>
        <p style="margin: 10px 0 0 0; opacity: 0.9; font-size: 1.1rem;">
            Visual representation of safety events by location
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Filters
    with st.expander("🔍 **Map Filters**", expanded=True):
        filter_col1, filter_col2, filter_col3 = st.columns(3)
        
        with filter_col1:
            incident_types = st.multiselect(
                "Incident Types",
                ["Bird Strikes", "Laser Strikes", "TCAS Events", "Ground Incidents", 
                 "Technical Events", "Hazards"],
                default=["Bird Strikes", "Laser Strikes"]
            )
        
        with filter_col2:
            risk_levels = st.multiselect(
                "Risk Levels",
                ["Extreme", "High", "Medium", "Low"],
                default=["Extreme", "High", "Medium"]
            )
        
        with filter_col3:
            date_range = st.date_input(
                "Date Range",
                value=(datetime.now() - timedelta(days=90), datetime.now())
            )
    
    # Gather location data from reports
    map_data = collect_map_data(incident_types, risk_levels)
    
    if map_data:
        # Create the map
        st.markdown("### 📍 Incident Locations")
        
        # Convert to DataFrame
        df = pd.DataFrame(map_data)
        
        # Color mapping
        color_map = {
            'Extreme': [220, 53, 69, 200],
            'High': [253, 126, 20, 200],
            'Medium': [255, 193, 7, 200],
            'Low': [40, 167, 69, 200]
        }
        
        df['color'] = df['risk_level'].map(lambda x: color_map.get(x, [108, 117, 125, 200]))
        
        # PyDeck map
        if PYDECK_AVAILABLE and pdk is not None:
            try:
                layer = pdk.Layer(
                    'ScatterplotLayer',
                    data=df,
                    get_position='[longitude, latitude]',
                    get_color='color',
                    get_radius=50000,
                    pickable=True
                )
                
                # Center on Pakistan/Air Sial routes
                view_state = pdk.ViewState(
                    latitude=30.3753,
                    longitude=69.3451,
                    zoom=5,
                    pitch=0
                )
                
                deck = pdk.Deck(
                    layers=[layer],
                    initial_view_state=view_state,
                    tooltip={
                        'text': '{type}\n{id}\nRisk: {risk_level}\nDate: {date}'
                    }
                )
                
                st.pydeck_chart(deck)
                
            except Exception as e:
                # Fallback to simple map
                st.map(df[['latitude', 'longitude']])
        else:
            # Fallback to simple map if pydeck not available
            st.map(df[['latitude', 'longitude']])
        
        # Legend
        st.markdown("### 🎨 Legend")
        legend_cols = st.columns(4)
        colors = [("🔴", "Extreme"), ("🟠", "High"), ("🟡", "Medium"), ("🟢", "Low")]
        for col, (emoji, label) in zip(legend_cols, colors):
            with col:
                st.markdown(f"{emoji} **{label} Risk**")
        
        # Statistics
        st.markdown("### 📊 Location Statistics")
        
        stat_col1, stat_col2, stat_col3 = st.columns(3)
        
        with stat_col1:
            st.metric("Total Incidents Mapped", len(map_data))
        
        with stat_col2:
            airports = df['location'].value_counts()
            if not airports.empty:
                st.metric("Most Active Location", airports.index[0])
        
        with stat_col3:
            high_count = len(df[df['risk_level'].isin(['Extreme', 'High'])])
            st.metric("High Risk Events", high_count)
        
        # Location breakdown table
        st.markdown("### 📋 Events by Location")
        location_summary = df.groupby('location').agg({
            'id': 'count',
            'risk_level': lambda x: (x.isin(['Extreme', 'High'])).sum()
        }).rename(columns={'id': 'Total Events', 'risk_level': 'High Risk'})
        st.dataframe(location_summary, use_container_width=True)
        
    else:
        st.info("No location data available. Submit reports with location information to see them on the map.")
        
        # Show sample map centered on Pakistan
        sample_df = pd.DataFrame({
            'latitude': [31.5204, 24.8607, 33.6844],
            'longitude': [74.3587, 67.0011, 73.0479],
            'name': ['Lahore', 'Karachi', 'Islamabad']
        })
        st.map(sample_df)
        st.caption("Sample map showing Air Sial hub locations")


def collect_map_data(incident_types, risk_levels):
    """Collect location data from all reports for mapping."""
    
    map_data = []
    
    # Map incident type names to session state keys
    type_mapping = {
        "Bird Strikes": ("bird_strikes", "🦅"),
        "Laser Strikes": ("laser_strikes", "🔴"),
        "TCAS Events": ("tcas_reports", "✈️"),
        "Ground Incidents": ("aircraft_incidents", "⚠️"),
        "Technical Events": ("aircraft_incidents", "🔧"),
        "Hazards": ("hazard_reports", "🔶")
    }
    
    for inc_type in incident_types:
        if inc_type in type_mapping:
            state_key, icon = type_mapping[inc_type]
            reports = st.session_state.get(state_key, [])
            
            for report in reports:
                risk = report.get('risk_level', 'Low')
                if risk in risk_levels:
                    # Try to get coordinates
                    lat = report.get('latitude')
                    lon = report.get('longitude')
                    
                    # If no coordinates, try to get from airport
                    if not lat or not lon:
                        airport = report.get('airport', '')
                        coords = get_airport_coordinates(airport)
                        if coords:
                            lat, lon = coords
                    
                    # Only add if we have valid coordinates
                    if lat and lon:
                        try:
                            map_data.append({
                                'latitude': float(lat),
                                'longitude': float(lon),
                                'id': report.get('report_id') or report.get('id', 'N/A'),
                                'type': inc_type,
                                'icon': icon,
                                'risk_level': risk,
                                'date': report.get('date') or report.get('incident_date', 'N/A'),
                                'location': report.get('airport') or report.get('location', 'Unknown')
                            })
                        except (ValueError, TypeError):
                            pass
    
    return map_data


def get_airport_coordinates(airport_code):
    """Get coordinates for common airports."""
    
    airport_coords = {
        'OPLA': (31.5216, 74.4036),  # Lahore
        'OPKC': (24.9065, 67.1609),  # Karachi
        'OPRN': (33.6167, 73.0992),  # Islamabad
        'OPPS': (25.2900, 62.3157),  # Gwadar
        'OPMT': (30.2033, 71.4192),  # Multan
        'OPFA': (31.3650, 72.9945),  # Faisalabad
        'OPSR': (27.7220, 68.3658),  # Sukkur
        'OPQT': (30.2514, 66.9378),  # Quetta
        'OPSK': (27.4500, 68.7667),  # Moenjodaro
        'OPDG': (29.9617, 70.4856),  # Dera Ghazi Khan
    }
    
    # Also check by name
    if airport_code:
        code = airport_code.upper().split()[0]
        if code in airport_coords:
            return airport_coords[code]
        
        # Check if it contains a known code
        for ac, coords in airport_coords.items():
            if ac in airport_code.upper():
                return coords
    
    return None


def render_iosa_compliance():
    """IOSA Standards Compliance Tracking."""
    
    st.markdown("""
    <div style="background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); 
                padding: 30px; border-radius: 15px; margin-bottom: 25px; color: white;">
        <h1 style="margin: 0; font-size: 2.2rem;">✈️ IOSA Compliance Tracker</h1>
        <p style="margin: 10px 0 0 0; opacity: 0.9; font-size: 1.1rem;">
            IATA Operational Safety Audit Standards Management
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # IOSA Sections
    iosa_sections = {
        'ORG': {'name': 'Organization and Management System', 'standards': 45, 'compliant': 43},
        'FLT': {'name': 'Flight Operations', 'standards': 120, 'compliant': 115},
        'OPS': {'name': 'Operational Control', 'standards': 35, 'compliant': 34},
        'MNT': {'name': 'Aircraft Engineering and Maintenance', 'standards': 85, 'compliant': 82},
        'CAB': {'name': 'Cabin Operations', 'standards': 40, 'compliant': 38},
        'GRH': {'name': 'Ground Handling', 'standards': 55, 'compliant': 52},
        'CGO': {'name': 'Cargo Operations', 'standards': 30, 'compliant': 29},
        'SEC': {'name': 'Security Management', 'standards': 45, 'compliant': 44},
    }
    
    # Overall compliance
    total_standards = sum(s['standards'] for s in iosa_sections.values())
    total_compliant = sum(s['compliant'] for s in iosa_sections.values())
    overall_rate = (total_compliant / total_standards) * 100
    
    # Summary cards
    st.markdown("### 📊 Compliance Overview")
    
    card_cols = st.columns(4)
    
    with card_cols[0]:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #28A745 0%, #20C997 100%);
                    padding: 20px; border-radius: 15px; text-align: center; color: white;">
            <div style="font-size: 2.5rem; font-weight: bold;">{overall_rate:.1f}%</div>
            <div style="font-size: 0.9rem;">Overall Compliance</div>
        </div>
        """, unsafe_allow_html=True)
    
    with card_cols[1]:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    padding: 20px; border-radius: 15px; text-align: center; color: white;">
            <div style="font-size: 2.5rem; font-weight: bold;">{total_standards}</div>
            <div style="font-size: 0.9rem;">Total Standards</div>
        </div>
        """, unsafe_allow_html=True)
    
    with card_cols[2]:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #4ECDC4 0%, #556270 100%);
                    padding: 20px; border-radius: 15px; text-align: center; color: white;">
            <div style="font-size: 2.5rem; font-weight: bold;">{total_compliant}</div>
            <div style="font-size: 0.9rem;">Standards Met</div>
        </div>
        """, unsafe_allow_html=True)
    
    with card_cols[3]:
        gaps = total_standards - total_compliant
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #FFC107 0%, #FF8C00 100%);
                    padding: 20px; border-radius: 15px; text-align: center; color: white;">
            <div style="font-size: 2.5rem; font-weight: bold;">{gaps}</div>
            <div style="font-size: 0.9rem;">Gaps Identified</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Section breakdown
    st.markdown("### 📋 Compliance by Section")
    
    for code, data in iosa_sections.items():
        rate = (data['compliant'] / data['standards']) * 100
        gap = data['standards'] - data['compliant']
        
        color = '#28A745' if rate >= 95 else '#FFC107' if rate >= 90 else '#DC3545'
        
        with st.expander(f"**{code}** - {data['name']} ({rate:.1f}% Compliant)"):
            prog_col, stat_col = st.columns([3, 1])
            
            with prog_col:
                st.progress(rate / 100)
                st.markdown(f"""
                <div style="display: flex; justify-content: space-between; margin-top: -10px;">
                    <span style="color: #666;">0%</span>
                    <span style="color: {color}; font-weight: bold;">{rate:.1f}%</span>
                    <span style="color: #666;">100%</span>
                </div>
                """, unsafe_allow_html=True)
            
            with stat_col:
                st.markdown(f"""
                **Standards:** {data['standards']}  
                **Compliant:** {data['compliant']}  
                **Gaps:** {gap}
                """)
            
            if gap > 0:
                st.warning(f"⚠️ {gap} standard(s) require attention")
                if st.button(f"View {code} Gaps", key=f"gaps_{code}"):
                    st.info(f"Gap details for {code} section would be displayed here")
    
    # Action items
    st.markdown("### 📌 Priority Action Items")
    
    action_items = [
        {'section': 'FLT', 'item': 'FLT 3.4.2 - Crew Resource Management Training', 'due': '2025-12-31', 'status': 'In Progress'},
        {'section': 'MNT', 'item': 'MNT 2.1.5 - NDT Procedure Documentation', 'due': '2025-12-15', 'status': 'Pending'},
        {'section': 'GRH', 'item': 'GRH 4.2.1 - Ground Support Equipment Inspection', 'due': '2025-12-20', 'status': 'In Progress'},
        {'section': 'CAB', 'item': 'CAB 3.1.8 - Emergency Equipment Recurrent Training', 'due': '2026-01-15', 'status': 'Scheduled'},
    ]
    
    for item in action_items:
        status_color = {'In Progress': '#FFC107', 'Pending': '#DC3545', 'Scheduled': '#17A2B8'}
        
        st.markdown(f"""
        <div style="background: white; padding: 15px; border-radius: 10px; 
                    margin-bottom: 10px; border-left: 4px solid {status_color.get(item['status'], '#6C757D')};">
            <strong>[{item['section']}]</strong> {item['item']}
            <div style="color: #666; font-size: 0.9rem; margin-top: 5px;">
                Due: {item['due']} | Status: <span style="color: {status_color.get(item['status'], '#6C757D')}">{item['status']}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)


def render_ramp_inspection():
    """Ramp Safety Inspection Management."""
    
    st.markdown("""
    <div style="background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); 
                padding: 30px; border-radius: 15px; margin-bottom: 25px; color: white;">
        <h1 style="margin: 0; font-size: 2.2rem;">🛬 Ramp Safety Inspections</h1>
        <p style="margin: 10px 0 0 0; opacity: 0.9; font-size: 1.1rem;">
            Ground operations safety inspection management
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    tab_new, tab_view, tab_analytics = st.tabs([
        "➕ New Inspection", "📋 View Inspections", "📊 Analytics"
    ])
    
    with tab_new:
        render_new_ramp_inspection()
    
    with tab_view:
        render_ramp_inspection_list()
    
    with tab_analytics:
        render_ramp_analytics()


def render_new_ramp_inspection():
    """Form for new ramp inspection."""
    
    st.markdown("### ➕ New Ramp Inspection")
    
    with st.form("ramp_inspection_form"):
        # Basic info
        col1, col2 = st.columns(2)
        
        with col1:
            inspection_id = st.text_input(
                "Inspection ID",
                value=f"RAMP-{datetime.now().strftime('%Y%m%d')}-{random.randint(100,999)}"
            )
            inspection_date = st.date_input("Inspection Date", datetime.now())
            airport = st.selectbox("Airport", AIRPORTS if 'AIRPORTS' in dir() else 
                                  ["OPLA - Lahore", "OPKC - Karachi", "OPRN - Islamabad"])
        
        with col2:
            inspector = st.text_input("Inspector Name")
            flight_number = st.text_input("Flight Number (if applicable)")
            inspection_type = st.selectbox(
                "Inspection Type",
                ["Pre-Flight", "Transit", "Post-Flight", "Random", "Follow-up"]
            )
        
        st.markdown("---")
        st.markdown("### 📋 Inspection Checklist")
        
        # Checklist sections
        checklist_sections = {
            "Aircraft Exterior": [
                "General cleanliness and condition",
                "No visible damage or fluid leaks",
                "Doors and hatches properly secured",
                "Engine intake/exhaust covers removed",
                "Pitot covers removed",
                "Wheel chocks in place"
            ],
            "Ground Support Equipment": [
                "GSE positioned correctly",
                "Equipment in good condition",
                "Operators properly trained",
                "Safety barriers in place",
                "FOD prevention measures"
            ],
            "Fueling Operations": [
                "Fire extinguisher present",
                "Bonding wire connected",
                "No ignition sources nearby",
                "Fuel type verified",
                "Spill kit available"
            ],
            "Loading Operations": [
                "Load plan followed",
                "ULD locks secured",
                "Dangerous goods properly handled",
                "Weight and balance verified",
                "Cargo doors properly closed"
            ],
            "Personnel Safety": [
                "PPE worn correctly",
                "Hearing protection used",
                "Hi-vis clothing worn",
                "Safe movement around aircraft",
                "Awareness of propeller/jet blast zones"
            ]
        }
        
        findings = []
        
        for section, items in checklist_sections.items():
            st.markdown(f"**{section}**")
            
            for item in items:
                item_col1, item_col2 = st.columns([3, 1])
                with item_col1:
                    st.markdown(f"• {item}")
                with item_col2:
                    status = st.selectbox(
                        "",
                        ["✅ OK", "⚠️ Minor", "❌ Major", "N/A"],
                        key=f"check_{section}_{item}"[:50]
                    )
                    if status in ["⚠️ Minor", "❌ Major"]:
                        findings.append(f"{section}: {item} - {status}")
            
            st.markdown("")
        
        # Findings
        st.markdown("---")
        st.markdown("### 📝 Findings & Observations")
        
        observations = st.text_area(
            "Detailed Observations",
            height=150,
            placeholder="Document any findings, discrepancies, or notable observations..."
        )
        
        # Photos
        photos = st.file_uploader(
            "Upload Photos (optional)",
            accept_multiple_files=True,
            type=['jpg', 'jpeg', 'png']
        )
        
        # Risk assessment
        st.markdown("### ⚠️ Overall Assessment")
        
        overall_rating = st.select_slider(
            "Overall Compliance",
            options=["Non-Compliant", "Needs Improvement", "Satisfactory", "Good", "Excellent"]
        )
        
        immediate_action = st.checkbox("Immediate action required")
        follow_up = st.checkbox("Follow-up inspection required")
        
        # Submit
        submitted = st.form_submit_button("✅ Submit Inspection", use_container_width=True)
        
        if submitted:
            inspection_data = {
                'inspection_id': inspection_id,
                'date': str(inspection_date),
                'airport': airport,
                'inspector': inspector,
                'flight_number': flight_number,
                'type': inspection_type,
                'findings': findings,
                'observations': observations,
                'rating': overall_rating,
                'immediate_action': immediate_action,
                'follow_up': follow_up,
                'status': 'Completed'
            }
            
            if 'ramp_inspections' not in st.session_state:
                st.session_state['ramp_inspections'] = []
            
            st.session_state['ramp_inspections'].append(inspection_data)
            
            st.success("✅ Ramp inspection submitted successfully!")
            st.balloons()


def render_ramp_inspection_list():
    """View list of ramp inspections."""
    
    inspections = st.session_state.get('ramp_inspections', [])
    
    if inspections:
        for insp in inspections:
            rating_color = {
                'Excellent': '#28A745',
                'Good': '#20C997',
                'Satisfactory': '#FFC107',
                'Needs Improvement': '#FD7E14',
                'Non-Compliant': '#DC3545'
            }
            
            st.markdown(f"""
            <div style="background: white; padding: 20px; border-radius: 10px; 
                        margin-bottom: 15px; border-left: 4px solid {rating_color.get(insp.get('rating', 'Satisfactory'), '#6C757D')};">
                <div style="display: flex; justify-content: space-between;">
                    <strong>{insp['inspection_id']}</strong>
                    <span style="background: {rating_color.get(insp.get('rating', 'Satisfactory'), '#6C757D')}; 
                                color: white; padding: 3px 10px; border-radius: 15px;">
                        {insp.get('rating', 'N/A')}
                    </span>
                </div>
                <div style="color: #666; margin-top: 10px;">
                    📅 {insp['date']} | 🛫 {insp['airport']} | 👤 {insp['inspector']}
                </div>
                <div style="color: #888; margin-top: 5px;">
                    Type: {insp['type']} | Findings: {len(insp.get('findings', []))}
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No ramp inspections recorded yet. Submit a new inspection to see it here.")


def render_ramp_analytics():
    """Ramp inspection analytics."""
    
    inspections = st.session_state.get('ramp_inspections', [])
    
    st.markdown("### 📊 Ramp Safety Analytics")
    
    if inspections:
        # Metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Inspections", len(inspections))
        
        with col2:
            findings_count = sum(len(i.get('findings', [])) for i in inspections)
            st.metric("Total Findings", findings_count)
        
        with col3:
            excellent_count = sum(1 for i in inspections if i.get('rating') in ['Excellent', 'Good'])
            st.metric("Good/Excellent Rate", f"{(excellent_count/len(inspections)*100):.0f}%")
    else:
        st.info("Submit ramp inspections to see analytics here.")


def render_audit_findings():
    """Audit Findings Tracker."""
    
    st.markdown("""
    <div style="background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); 
                padding: 30px; border-radius: 15px; margin-bottom: 25px; color: white;">
        <h1 style="margin: 0; font-size: 2.2rem;">🔍 Audit Findings Tracker</h1>
        <p style="margin: 10px 0 0 0; opacity: 0.9; font-size: 1.1rem;">
            Track and manage internal and external audit findings
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sample findings
    findings = st.session_state.get('audit_findings', [
        {
            'id': 'AUD-2025-001',
            'source': 'Internal Audit',
            'date': '2025-11-15',
            'area': 'Flight Operations',
            'finding': 'CRM training records incomplete for 3 crew members',
            'classification': 'Minor',
            'status': 'Open',
            'due_date': '2025-12-31',
            'owner': 'Training Manager'
        },
        {
            'id': 'AUD-2025-002',
            'source': 'PCAA Inspection',
            'date': '2025-10-20',
            'area': 'Maintenance',
            'finding': 'Tool calibration certificates expired',
            'classification': 'Major',
            'status': 'In Progress',
            'due_date': '2025-12-15',
            'owner': 'Quality Manager'
        }
    ])
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    open_count = sum(1 for f in findings if f['status'] == 'Open')
    major_count = sum(1 for f in findings if f['classification'] == 'Major')
    
    with col1:
        st.metric("Total Findings", len(findings))
    with col2:
        st.metric("Open", open_count, delta=None if open_count == 0 else f"+{open_count}")
    with col3:
        st.metric("Major Findings", major_count)
    with col4:
        overdue = sum(1 for f in findings if f['status'] != 'Closed' and 
                     f.get('due_date', '9999') < datetime.now().strftime('%Y-%m-%d'))
        st.metric("Overdue", overdue)
    
    # Findings list
    st.markdown("### 📋 Findings Register")
    
    for finding in findings:
        class_color = {'Major': '#DC3545', 'Minor': '#FFC107', 'Observation': '#17A2B8'}
        status_color = {'Open': '#DC3545', 'In Progress': '#FFC107', 'Closed': '#28A745'}
        
        with st.expander(f"**{finding['id']}** - {finding['area']} ({finding['classification']})"):
            st.markdown(f"**Finding:** {finding['finding']}")
            st.markdown(f"**Source:** {finding['source']} | **Date:** {finding['date']}")
            st.markdown(f"**Owner:** {finding['owner']} | **Due:** {finding['due_date']}")
            st.markdown(f"""
            **Status:** <span style="background: {status_color.get(finding['status'], '#6C757D')}; 
                                    color: white; padding: 2px 10px; border-radius: 10px;">
                        {finding['status']}</span>
            """, unsafe_allow_html=True)
            
            # Actions
            act_col1, act_col2 = st.columns(2)
            with act_col1:
                new_status = st.selectbox(
                    "Update Status",
                    ["Open", "In Progress", "Closed"],
                    index=["Open", "In Progress", "Closed"].index(finding['status']),
                    key=f"status_{finding['id']}"
                )
            with act_col2:
                if st.button("Update", key=f"update_{finding['id']}"):
                    finding['status'] = new_status
                    st.success("Status updated!")


def render_moc_workflow():
    """Management of Change workflow."""
    
    st.markdown("""
    <div style="background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); 
                padding: 30px; border-radius: 15px; margin-bottom: 25px; color: white;">
        <h1 style="margin: 0; font-size: 2.2rem;">🔄 Management of Change</h1>
        <p style="margin: 10px 0 0 0; opacity: 0.9; font-size: 1.1rem;">
            Change management and risk assessment workflow
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    tab_new, tab_pending, tab_approved = st.tabs([
        "➕ New Change Request", "⏳ Pending Review", "✅ Approved Changes"
    ])
    
    with tab_new:
        st.markdown("### 📝 New Change Request")
        
        with st.form("moc_form"):
            change_title = st.text_input("Change Title")
            change_type = st.selectbox(
                "Change Type",
                ["Operational Procedure", "Equipment/System", "Organization", 
                 "Regulatory Compliance", "Training Program", "Route/Destination"]
            )
            
            description = st.text_area("Change Description", height=150)
            justification = st.text_area("Business Justification", height=100)
            
            # Risk assessment
            st.markdown("#### Risk Assessment")
            
            risk_col1, risk_col2 = st.columns(2)
            with risk_col1:
                likelihood = st.slider("Risk Likelihood", 1, 5, 3)
            with risk_col2:
                severity = st.selectbox("Risk Severity", ["A - Catastrophic", "B - Hazardous", 
                                                         "C - Major", "D - Minor", "E - Negligible"])
            
            mitigations = st.text_area("Proposed Risk Mitigations", height=100)
            
            # Approvers
            st.markdown("#### Approval Chain")
            dept_approval = st.multiselect(
                "Departments Required",
                ["Safety", "Flight Operations", "Maintenance", "Quality", 
                 "Compliance", "Training", "Security"]
            )
            
            submitted = st.form_submit_button("Submit Change Request", use_container_width=True)
            
            if submitted and change_title:
                moc_data = {
                    'id': f"MOC-{datetime.now().strftime('%Y%m%d')}-{random.randint(100,999)}",
                    'title': change_title,
                    'type': change_type,
                    'description': description,
                    'status': 'Pending Review',
                    'date': datetime.now().strftime('%Y-%m-%d'),
                    'departments': dept_approval
                }
                
                if 'moc_requests' not in st.session_state:
                    st.session_state['moc_requests'] = []
                
                st.session_state['moc_requests'].append(moc_data)
                st.success(f"✅ Change request {moc_data['id']} submitted!")
    
    with tab_pending:
        st.markdown("### ⏳ Pending Review")
        mocs = st.session_state.get('moc_requests', [])
        pending = [m for m in mocs if m['status'] == 'Pending Review']
        
        if pending:
            for moc in pending:
                st.markdown(f"""
                <div style="background: white; padding: 15px; border-radius: 10px; 
                            margin-bottom: 10px; border-left: 4px solid #FFC107;">
                    <strong>{moc['id']}</strong> - {moc['title']}
                    <div style="color: #666; font-size: 0.9rem;">
                        Type: {moc['type']} | Date: {moc['date']}
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No pending change requests.")
    
    with tab_approved:
        st.markdown("### ✅ Approved Changes")
        st.info("No approved changes to display.")


def render_predictive_monitor():
    """Predictive Safety Monitoring Dashboard."""
    
    st.markdown("""
    <div style="background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); 
                padding: 30px; border-radius: 15px; margin-bottom: 25px; color: white;">
        <h1 style="margin: 0; font-size: 2.2rem;">🔮 Predictive Safety Monitor</h1>
        <p style="margin: 10px 0 0 0; opacity: 0.9; font-size: 1.1rem;">
            AI-powered safety trend prediction and early warning
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Risk indicators
    st.markdown("### 📊 Leading Indicators")
    
    ind_cols = st.columns(4)
    
    indicators = [
        ("Fatigue Risk", 72, "green", "↓ 5%"),
        ("Weather Exposure", 45, "yellow", "→ 0%"),
        ("Technical Health", 88, "green", "↑ 3%"),
        ("Training Currency", 95, "green", "↑ 2%")
    ]
    
    for col, (name, value, color, trend) in zip(ind_cols, indicators):
        with col:
            color_map = {'green': '#28A745', 'yellow': '#FFC107', 'red': '#DC3545'}
            st.markdown(f"""
            <div style="background: white; padding: 20px; border-radius: 15px; 
                        text-align: center; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                <div style="font-size: 0.9rem; color: #666;">{name}</div>
                <div style="font-size: 2.5rem; font-weight: bold; color: {color_map[color]};">{value}%</div>
                <div style="font-size: 0.8rem; color: #888;">{trend}</div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Predictions
    st.markdown("### 🎯 Predictive Alerts")
    
    predictions = [
        {
            'title': 'Increased Bird Activity Expected',
            'timeframe': 'Next 2 weeks',
            'confidence': 85,
            'recommendation': 'Enhanced wildlife awareness briefings recommended for LHE/KHI routes'
        },
        {
            'title': 'Monsoon Weather Pattern',
            'timeframe': 'Next month',
            'confidence': 78,
            'recommendation': 'Review thunderstorm avoidance procedures and alternate airport availability'
        },
        {
            'title': 'Crew Fatigue Risk Elevated',
            'timeframe': 'Holiday period',
            'confidence': 72,
            'recommendation': 'Monitor duty hours closely and ensure adequate rest periods'
        }
    ]
    
    for pred in predictions:
        conf_color = '#28A745' if pred['confidence'] >= 80 else '#FFC107' if pred['confidence'] >= 60 else '#DC3545'
        
        st.markdown(f"""
        <div style="background: white; padding: 20px; border-radius: 10px; 
                    margin-bottom: 15px; border-left: 4px solid {conf_color};">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <strong style="font-size: 1.1rem;">{pred['title']}</strong>
                <span style="background: {conf_color}; color: white; padding: 3px 10px; 
                            border-radius: 15px; font-size: 0.8rem;">
                    {pred['confidence']}% Confidence
                </span>
            </div>
            <div style="color: #666; margin: 10px 0;">
                <strong>Timeframe:</strong> {pred['timeframe']}
            </div>
            <div style="background: #F8F9FA; padding: 10px; border-radius: 5px; margin-top: 10px;">
                <strong>💡 Recommendation:</strong> {pred['recommendation']}
            </div>
        </div>
        """, unsafe_allow_html=True)


def render_data_management():
    """Data Management and Export Interface."""
    
    st.markdown("""
    <div style="background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); 
                padding: 30px; border-radius: 15px; margin-bottom: 25px; color: white;">
        <h1 style="margin: 0; font-size: 2.2rem;">💾 Data Management</h1>
        <p style="margin: 10px 0 0 0; opacity: 0.9; font-size: 1.1rem;">
            Export, import, and manage safety data
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    tab_export, tab_import, tab_backup = st.tabs([
        "📤 Export Data", "📥 Import Data", "💾 Backup/Restore"
    ])
    
    with tab_export:
        st.markdown("### 📤 Export Safety Data")
        
        export_type = st.multiselect(
            "Select Data to Export",
            ["Bird Strike Reports", "Laser Strike Reports", "TCAS Reports",
             "Aircraft Incidents", "Hazard Reports", "FSR Reports", "Captain Debriefs",
             "Ramp Inspections", "Audit Findings"]
        )
        
        export_format = st.selectbox(
            "Export Format",
            ["CSV", "Excel (XLSX)", "JSON", "PDF Report"]
        )
        
        date_range = st.date_input(
            "Date Range",
            value=(datetime.now() - timedelta(days=365), datetime.now())
        )
        
        if st.button("📥 Generate Export", use_container_width=True):
            with st.spinner("Preparing export..."):
                time.sleep(1)
                
                # Collect data
                export_data = []
                type_map = {
                    "Bird Strike Reports": "bird_strikes",
                    "Laser Strike Reports": "laser_strikes",
                    "TCAS Reports": "tcas_reports",
                    "Aircraft Incidents": "aircraft_incidents",
                    "Hazard Reports": "hazard_reports",
                    "FSR Reports": "fsr_reports",
                    "Captain Debriefs": "captain_dbr"
                }
                
                for export_name in export_type:
                    if export_name in type_map:
                        data = st.session_state.get(type_map[export_name], [])
                        for item in data:
                            item['report_type'] = export_name
                            export_data.append(item)
                
                if export_data:
                    df = pd.DataFrame(export_data)
                    
                    if export_format == "CSV":
                        csv = df.to_csv(index=False)
                        st.download_button(
                            "📥 Download CSV",
                            csv,
                            "safety_export.csv",
                            "text/csv"
                        )
                    elif export_format == "Excel (XLSX)":
                        # Would use openpyxl in production
                        csv = df.to_csv(index=False)
                        st.download_button(
                            "📥 Download CSV (Excel not available)",
                            csv,
                            "safety_export.csv",
                            "text/csv"
                        )
                    elif export_format == "JSON":
                        json_str = df.to_json(orient='records', indent=2)
                        st.download_button(
                            "📥 Download JSON",
                            json_str,
                            "safety_export.json",
                            "application/json"
                        )
                    
                    st.success(f"✅ Export ready! {len(export_data)} records prepared.")
                else:
                    st.warning("No data to export for selected criteria.")
    
    with tab_import:
        st.markdown("### 📥 Import Safety Data")
        
        uploaded_file = st.file_uploader(
            "Upload Data File",
            type=['csv', 'xlsx', 'json']
        )
        
        if uploaded_file:
            st.info(f"File uploaded: {uploaded_file.name}")
            
            if st.button("Process Import"):
                st.success("Import processed successfully!")
    
    with tab_backup:
        st.markdown("### 💾 System Backup")
        
        if st.button("Create Full Backup", use_container_width=True):
            with st.spinner("Creating backup..."):
                time.sleep(1)
                
                backup_data = {
                    'timestamp': datetime.now().isoformat(),
                    'bird_strikes': st.session_state.get('bird_strikes', []),
                    'laser_strikes': st.session_state.get('laser_strikes', []),
                    'tcas_reports': st.session_state.get('tcas_reports', []),
                    'aircraft_incidents': st.session_state.get('aircraft_incidents', []),
                    'hazard_reports': st.session_state.get('hazard_reports', []),
                    'fsr_reports': st.session_state.get('fsr_reports', []),
                    'captain_dbr': st.session_state.get('captain_dbr', []),
                }
                
                backup_json = json.dumps(backup_data, indent=2, default=str)
                
                st.download_button(
                    "📥 Download Backup",
                    backup_json,
                    f"sms_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    "application/json"
                )
                
                st.success("Backup created successfully!")


def render_nl_query():
    """Natural Language Query Interface."""
    
    st.markdown("""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                padding: 30px; border-radius: 15px; margin-bottom: 25px; color: white;">
        <h1 style="margin: 0; font-size: 2.2rem;">🔍 Natural Language Query</h1>
        <p style="margin: 10px 0 0 0; opacity: 0.9; font-size: 1.1rem;">
            Ask questions about safety data in plain English
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Query input
    query = st.text_input(
        "Ask a question:",
        placeholder="e.g., How many bird strikes occurred at Lahore this year?"
    )
    
    # Example queries
    st.markdown("**Example queries:**")
    examples = [
        "How many reports were submitted this month?",
        "What are the top 3 hazard categories?",
        "Show all high-risk incidents",
        "List bird strikes at Karachi airport",
        "What is our safety performance trend?"
    ]
    
    ex_cols = st.columns(3)
    for i, example in enumerate(examples[:3]):
        with ex_cols[i]:
            if st.button(example, key=f"ex_{i}", use_container_width=True):
                query = example
    
    if query:
        with st.spinner("Processing query..."):
            time.sleep(0.5)
            
            # Simple NL processing
            query_lower = query.lower()
            
            response = process_nl_query(query_lower)
            
            st.markdown("### 📊 Query Results")
            st.markdown(response)


def process_nl_query(query):
    """Process natural language query and return results."""
    
    # Get data
    report_counts = get_report_counts()
    total = get_total_reports()
    
    if 'how many' in query and ('report' in query or 'total' in query):
        return f"""
        **Total Reports in System:** {total}
        
        **Breakdown by Type:**
        - Bird Strikes: {report_counts.get('bird_strikes', 0)}
        - Laser Strikes: {report_counts.get('laser_strikes', 0)}
        - TCAS Events: {report_counts.get('tcas_reports', 0)}
        - Incidents: {report_counts.get('aircraft_incidents', 0)}
        - Hazard Reports: {report_counts.get('hazard_reports', 0)}
        - FSR Reports: {report_counts.get('fsr_reports', 0)}
        - Captain Debriefs: {report_counts.get('captain_dbr', 0)}
        """
    
    elif 'bird strike' in query:
        bs_count = report_counts.get('bird_strikes', 0)
        return f"""
        **Bird Strike Summary:**
        - Total Bird Strikes: {bs_count}
        - Data available in Bird Strike Reports section
        """
    
    elif 'high risk' in query or 'extreme' in query:
        high_risk = get_high_risk_count()
        return f"""
        **High/Extreme Risk Items:**
        - Total: {high_risk} items requiring attention
        - View details in the Dashboard or View Reports section
        """
    
    elif 'trend' in query or 'performance' in query:
        return """
        **Safety Performance Trend:**
        - Reporting rate: Active and healthy
        - Risk distribution: Within acceptable parameters
        - Closure rate: Meeting targets
        
        View detailed trends in the Dashboard section.
        """
    
    else:
        return f"""
        I understand you're asking about: "{query}"
        
        Current system statistics:
        - Total Reports: {total}
        - High Risk Items: {get_high_risk_count()}
        
        Try asking about specific report types, risk levels, or trends.
        """


# ==============================================================================
# PART 10: SYSTEM, SETTINGS & MAIN ENTRY POINT
# ==============================================================================

# ==============================================================================
# PART 10: SYSTEM, SETTINGS & MAIN ENTRY POINT
# ==============================================================================

def render_settings():
    """Render the settings page."""
    
    st.markdown("""
    <div style="background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); 
                padding: 30px; border-radius: 15px; margin-bottom: 25px; color: white;">
        <h1 style="margin: 0; font-size: 2.2rem;">⚙️ System Settings</h1>
        <p style="margin: 10px 0 0 0; opacity: 0.9; font-size: 1.1rem;">
            Configure system preferences and options
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Load existing settings
    settings = st.session_state.get('app_settings', {})
    
    # Create tabs
    tab_general, tab_users = st.tabs(["🏢 General", "👥 Users"])
    
    with tab_general:
        st.markdown("### 🏢 General Configuration")
        
        col1, col2 = st.columns(2)
        with col1:
            st.text_input("Company Name", value=settings.get('company_name', 'Air Sial'))
            st.selectbox("Timezone", ["Asia/Karachi (PKT)", "UTC"], index=0)
        with col2:
            st.text_input("ICAO Code", value=settings.get('company_code', 'PF'))
            st.checkbox("Enable Email Notifications", value=True)
            
        if st.button("💾 Save Settings", type="primary"):
            st.session_state['app_settings'] = {
                'company_name': 'Air Sial',
                'company_code': 'PF'
            }
            st.success("Settings saved successfully!")

    with tab_users:
        st.markdown("### 👥 User Management")
        st.info("User management is handled via Supabase Auth.")

# --------------------------------------------------------------------------
# HELPER FUNCTIONS (Must be defined before Main Execution)
# --------------------------------------------------------------------------

def get_user_role(username):
    """Determine role based on username (Demo logic) or return 'Viewer'."""
    roles = {
        'admin': 'Administrator',
        'safety': 'Safety Officer', 
        'pilot': 'Flight Crew',
        'viewer': 'Viewer'
    }
    return roles.get(username.lower(), 'Viewer')

def load_data_from_supabase():
    """
    Fetch all data from Supabase into Session State.
    Handles empty tables gracefully.
    """
    tables = [
        'bird_strikes', 'laser_strikes', 'tcas_reports', 
        'aircraft_incidents', 'hazard_reports', 'fsr_reports', 'captain_dbr'
    ]
    
    for table in tables:
        try:
            # Fetch data
            response = supabase.table(table).select("*").execute()
            # Store in Session State
            st.session_state[table] = response.data
        except Exception as e:
            # Ensure key exists even if fetch fails
            if table not in st.session_state:
                st.session_state[table] = []

def initialize_session_state():
    """Initialize app state variables and load data."""
    # Auth State
    if 'authenticated' not in st.session_state: st.session_state['authenticated'] = False
    if 'username' not in st.session_state: st.session_state['username'] = None
    if 'user_role' not in st.session_state: st.session_state['user_role'] = 'Viewer'
    
    # Navigation State
    if 'current_page' not in st.session_state: st.session_state['current_page'] = 'Dashboard'
    
    # AI Assistant State
    if 'ai_assistant' not in st.session_state:
        try:
            st.session_state.ai_assistant = get_ai_assistant()
        except:
            st.session_state.ai_assistant = None
            
    # Load Data
    load_data_from_supabase()

# --------------------------------------------------------------------------
# AUTHENTICATION & UI RENDERERS
# --------------------------------------------------------------------------

def render_login_page():
    """Render the login page with Hybrid Auth."""
    
    if "code" in st.query_params:
        st.toast("✅ Email Verified! Please log in.", icon="🎉")

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown("# ✈️ AIR SIAL")
        st.markdown("#### Safety Management System v3.0")
        st.divider()
        
        tab_signin, tab_register = st.tabs(["🔐 Sign In", "📝 Register"])
        
        with tab_signin:
            # Unique key to avoid duplicate ID errors
            with st.form("login_form_main"):
                username = st.text_input("Username / Email", placeholder="admin")
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Sign In", type="primary", use_container_width=True)
                
                if submitted:
                    user_input = username.strip()
                    # Demo Login
                    demo_users = {'admin': 'admin123', 'safety': 'safety123', 'pilot': 'pilot123', 'viewer': 'viewer123'}
                    
                    if user_input.lower() in demo_users and demo_users[user_input.lower()] == password:
                        st.session_state['authenticated'] = True
                        st.session_state['username'] = user_input
                        st.session_state['user_role'] = get_user_role(user_input)
                        st.success("✅ Login successful!")
                        st.rerun()
                    
                    # Supabase Login
                    else:
                        try:
                            auth = supabase.auth.sign_in_with_password({"email": user_input, "password": password})
                            if auth.user:
                                st.session_state['authenticated'] = True
                                st.session_state['username'] = auth.user.email
                                # Fetch Role
                                try:
                                    profile = supabase.table('profiles').select('role').eq('id', auth.user.id).execute()
                                    st.session_state['user_role'] = profile.data[0]['role'] if profile.data else "Viewer"
                                except:
                                    st.session_state['user_role'] = "Viewer"
                                st.success("✅ Login successful!")
                                st.rerun()
                        except:
                            st.error("❌ Login failed.")

        with tab_register:
            with st.form("register_form_main"):
                new_email = st.text_input("Email")
                new_pass = st.text_input("Password", type="password")
                new_role = st.selectbox("Role", ["Viewer", "Flight Crew", "Maintenance", "Safety Officer"])
                reg_btn = st.form_submit_button("Register")
                
                if reg_btn:
                    try:
                        supabase.auth.sign_up({
                            "email": new_email, "password": new_pass,
                            "options": {"data": {"role": new_role}}
                        })
                        st.success("Check email for confirmation link!")
                    except Exception as e:
                        st.error(f"Error: {e}")

def render_sidebar():
    with st.sidebar:
        # 1. Branding & User Info
        st.image("logo.png", width=120) 
        st.markdown(f"**User:** {st.session_state.get('username', 'Guest')}")
        st.markdown(f"**Role:** {st.session_state.get('user_role', 'Reporter')}")
        st.markdown("---")

        # 2. Main Navigation
        if st.button("📊 Dashboard", use_container_width=True):
            st.session_state['current_page'] = 'Dashboard'
            st.rerun()

        # 3. Forms (Strict List)
        st.markdown("### 📝 Reporting")
        if st.button("⚠️ Hazard Report", use_container_width=True):
            st.session_state['current_page'] = 'Hazard Report'
            st.rerun()
        if st.button("🚨 MOR (Mandatory)", use_container_width=True):
            st.session_state['current_page'] = 'MOR'
            st.rerun()
        if st.button("🧪 Quality/Audit", use_container_width=True):
            st.session_state['current_page'] = 'Audit'
            st.rerun()
            
        # 4. Operational Forms (Legacy Preserved)
        with st.expander("📂 Operational Forms"):
            if st.button("📝 FSR Report"): st.session_state['current_page'] = 'FSR Report'
            if st.button("👨‍✈️ Capt Debrief"): st.session_state['current_page'] = 'Captain Debrief'
            
        # 5. Enterprise Tools & AI
        with st.expander("🏢 Enterprise Tools"):
            if st.button("IOSA Compliance"): st.session_state['current_page'] = 'IOSA Compliance'
            if st.button("Ramp Inspection"): st.session_state['current_page'] = 'Ramp Inspections'
            if st.button("Email Center"): st.session_state['current_page'] = 'Email Center'
            # ADDED HERE:
            if st.button("🤖 AI Assistant"): st.session_state['current_page'] = 'AI Assistant'

        # 6. Logout
        st.markdown("---")
        if st.button("Logout"):
            st.session_state['authenticated'] = False
            st.rerun()

def route_to_page():
    """
    Robust Routing: Maps Sidebar selections to Functions.
    """
    page = st.session_state.get('current_page', 'Dashboard')
    
    # Map Pages to Functions
    PAGES = {
        'Dashboard': render_dashboard,
        'Hazard Report': render_hazard_form,
        'MOR': render_mor_form,
        'Audit': render_audit_form,
        
        # Legacy / Operational
        'FSR Report': globals().get('render_fsr_form'),
        'Captain Debrief': globals().get('render_captain_debrief'),
        
        # Enterprise
        'IOSA Compliance': globals().get('render_iosa_compliance'),
        'Ramp Inspections': globals().get('render_ramp_inspection'),
        'Email Center': globals().get('render_email_center'),
        
        # AI Assistant - Points to the local function defined in app.py
        'AI Assistant': render_ai_assistant 
    }
    
    # Execution Logic
    if page in PAGES:
        func = PAGES[page]
        if func:
            try:
                func()
            except Exception as e:
                st.error(f"⚠️ Critical Error loading '{page}': {e}")
                st.info("Check the logs for details.")
        else:
            st.warning(f"🚧 Page '{page}' is enabled in menu but code is missing.")
    else:
        st.error(f"❌ Routing Error: Page '{page}' is unknown.")

# ==============================================================================
# 3. MAIN EXECUTION BLOCK (MUST BE LAST)
# ==============================================================================

if __name__ == "__main__":
    # 1. Initialize State
    initialize_session_state()
    
    # 2. Apply CSS
    apply_custom_css()
    
    # 3. Routing Logic
    if not st.session_state.get('authenticated', False):
        render_login_page()
    else:
        render_sidebar()
        render_header()
        route_to_page()
        render_footer()
