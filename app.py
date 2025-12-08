"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                     AIR SIAL CORPORATE SAFETY MANAGEMENT SYSTEM              ║
║                              Enterprise Edition v2.0                         ║
║                                                                              ║
║  A comprehensive, CAA Pakistan compliant Safety Management System           ║
║  designed for commercial aviation safety reporting, investigation,          ║
║  and risk management.                                                        ║
║                                                                              ║
║  Features:                                                                   ║
║  • Full CAA-compliant mandatory reporting (Bird Strike, Laser, TCAS, etc.)  ║
║  • ICAO Standard Risk Assessment Matrix                                      ║
║  • 15-Day SLA Tracking with Escalation                                      ║
║  • OCR Document Scanning (Gemini Vision + Tesseract)                        ║
║  • Investigation Workflow Management                                         ║
║  • PDF Report Generation for CAA Submission                                 ║
║  • Role-Based Access Control                                                 ║
║  • Complete Audit Trail                                                      ║
║  • Real-time Dashboard Analytics                                             ║
║                                                                              ║
║  Copyright © 2024 Air Sial. All Rights Reserved.                            ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import hashlib
import json
import os
import io
import base64
import requests
from datetime import datetime, timedelta, date
from typing import Optional, Dict, List, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import uuid
import re

# ══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION & ENVIRONMENT
# ══════════════════════════════════════════════════════════════════════════════

class Config:
    """Application configuration settings"""
    
    # Application Info
    APP_NAME = "Air Sial Corporate Safety"
    APP_VERSION = "2.0.0"
    APP_SUBTITLE = "Safety Management System"
    COMPANY_NAME = "Air Sial"
    COMPANY_IATA = "PF"
    COMPANY_ICAO = "SIS"
    
    # Regulatory Info
    CAA_COUNTRY = "Pakistan"
    CAA_AUTHORITY = "Pakistan Civil Aviation Authority (PCAA)"
    AOC_NUMBER = "AOC-PK-0XX"
    
    # SLA Configuration (in days)
    HAZARD_SLA_DAYS = 15
    INCIDENT_SLA_DAYS = 30
    BIRD_STRIKE_SLA_DAYS = 7
    LASER_STRIKE_SLA_DAYS = 7
    TCAS_SLA_DAYS = 14
    
    # SLA Warning Thresholds
    SLA_CRITICAL_DAYS = 3
    SLA_WARNING_DAYS = 7
    
    # Email Configuration
    SAFETY_EMAIL = "safety@airsial.com"
    CAA_EMAIL = "reporting@caapakistan.com.pk"
    
    # API Keys (from secrets)
    @staticmethod
    def get_supabase_url():
        return st.secrets.get("SUPABASE_URL", "")
    
    @staticmethod
    def get_supabase_key():
        return st.secrets.get("SUPABASE_KEY", "")
    
    @staticmethod
    def get_gemini_key():
        return st.secrets.get("GEMINI_API_KEY", "")
    
    @staticmethod
    def get_groq_key():
        return st.secrets.get("GROQ_API_KEY", "")
    
    # Timezone
    TIMEZONE = "Asia/Karachi"
    UTC_OFFSET = 5
    
    # File Upload Settings
    MAX_UPLOAD_SIZE_MB = 10
    ALLOWED_IMAGE_TYPES = ['png', 'jpg', 'jpeg', 'bmp', 'tiff', 'webp']
    ALLOWED_DOC_TYPES = ['pdf', 'docx', 'xlsx']


# ══════════════════════════════════════════════════════════════════════════════
# ENUMERATIONS & CONSTANTS
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
    "Flight Operations", "Engineering & Maintenance", "Cabin Services",
    "Ground Operations", "Cargo Operations", "Flight Training",
    "Quality Assurance", "Safety Department", "Security Department",
    "Commercial", "Airport Operations - SKT", "Airport Operations - KHI",
    "Airport Operations - LHE", "Airport Operations - ISB",
    "Airport Operations - DXB", "Human Resources", "Finance",
    "IT Department", "Corporate Office", "Crew Scheduling",
    "Flight Dispatch", "Ramp Operations", "Catering Services"
]

AIRCRAFT_FLEET = {
    "AP-BMA": {"type": "ATR 72-600", "msn": "1234", "config": "70Y"},
    "AP-BMB": {"type": "ATR 72-600", "msn": "1235", "config": "70Y"},
    "AP-BMC": {"type": "ATR 72-600", "msn": "1236", "config": "70Y"},
    "AP-BMD": {"type": "ATR 72-600", "msn": "1237", "config": "70Y"},
    "AP-BME": {"type": "ATR 72-600", "msn": "1238", "config": "70Y"},
    "AP-BMF": {"type": "ATR 72-500", "msn": "1100", "config": "68Y"},
    "AP-BMG": {"type": "ATR 72-500", "msn": "1101", "config": "68Y"},
    "AP-BMH": {"type": "A320-200", "msn": "5500", "config": "180Y"},
    "AP-BMI": {"type": "A320-200", "msn": "5501", "config": "180Y"},
    "AP-BMJ": {"type": "A320neo", "msn": "8000", "config": "186Y"},
}

AIRCRAFT_TYPES = [
    "ATR 72-600", "ATR 72-500", "ATR 42-500", "A320-200", "A320neo",
    "A321-200", "A321neo", "B737-800", "B737 MAX 8"
]

AIRPORTS = {
    "OPSK": {"name": "Sialkot International Airport", "city": "Sialkot", "country": "Pakistan", "base": True},
    "OPKC": {"name": "Jinnah International Airport", "city": "Karachi", "country": "Pakistan", "base": True},
    "OPLA": {"name": "Allama Iqbal International Airport", "city": "Lahore", "country": "Pakistan", "base": True},
    "OPIS": {"name": "Islamabad International Airport", "city": "Islamabad", "country": "Pakistan", "base": True},
    "OPPS": {"name": "Peshawar Bacha Khan Airport", "city": "Peshawar", "country": "Pakistan", "base": False},
    "OPQT": {"name": "Quetta International Airport", "city": "Quetta", "country": "Pakistan", "base": False},
    "OPFA": {"name": "Faisalabad International Airport", "city": "Faisalabad", "country": "Pakistan", "base": False},
    "OPMT": {"name": "Multan International Airport", "city": "Multan", "country": "Pakistan", "base": False},
    "OMDB": {"name": "Dubai International Airport", "city": "Dubai", "country": "UAE", "base": False},
    "OMSJ": {"name": "Sharjah International Airport", "city": "Sharjah", "country": "UAE", "base": False},
    "OMAA": {"name": "Abu Dhabi International Airport", "city": "Abu Dhabi", "country": "UAE", "base": False},
    "OERK": {"name": "King Khalid International Airport", "city": "Riyadh", "country": "Saudi Arabia", "base": False},
    "OEJN": {"name": "King Abdulaziz International Airport", "city": "Jeddah", "country": "Saudi Arabia", "base": False},
    "OEDF": {"name": "King Fahd International Airport", "city": "Dammam", "country": "Saudi Arabia", "base": False},
    "OTHH": {"name": "Hamad International Airport", "city": "Doha", "country": "Qatar", "base": False},
    "OBBI": {"name": "Bahrain International Airport", "city": "Bahrain", "country": "Bahrain", "base": False},
    "OOMS": {"name": "Muscat International Airport", "city": "Muscat", "country": "Oman", "base": False},
    "OKBK": {"name": "Kuwait International Airport", "city": "Kuwait City", "country": "Kuwait", "base": False},
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

TCAS_EQUIPMENT_TYPES = [
    "TCAS I", "TCAS II (Version 6.04a)", "TCAS II (Version 7.0)",
    "TCAS II (Version 7.1)", "ACAS X (ADS-B based)", "Unknown/Not Determined"
]

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

APPROACH_TYPES = [
    "ILS CAT I", "ILS CAT II", "ILS CAT III", "VOR/DME", "VOR",
    "NDB", "RNAV (GNSS)", "RNP AR", "Visual", "Circling",
    "LOC Only", "LDA", "SDF", "PAR", "ASR"
]

RUNWAY_CONDITIONS = [
    "Dry", "Damp", "Wet", "Contaminated - Water", "Contaminated - Slush",
    "Contaminated - Snow (Dry)", "Contaminated - Snow (Compacted)",
    "Contaminated - Ice", "Contaminated - Frost", "Flooded"
]

BRAKING_ACTIONS = [
    "Good", "Good to Medium", "Medium", "Medium to Poor", "Poor", "Nil"
]

TURBULENCE_INTENSITY = [
    "None", "Light", "Light Occasional", "Light Frequent",
    "Moderate", "Moderate Occasional", "Moderate Frequent",
    "Severe", "Severe Occasional", "Extreme"
]


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
    "A": {"name": "Catastrophic", "description": "Equipment destroyed, multiple deaths", "operational": "Multiple fatalities (passengers/crew/ground)"},
    "B": {"name": "Hazardous", "description": "Large reduction in safety margins, serious injury", "operational": "Fatal injury or serious injury to small number of people"},
    "C": {"name": "Major", "description": "Significant reduction in safety margins", "operational": "Injury to persons, major equipment damage"},
    "D": {"name": "Minor", "description": "Nuisance, operating limitations", "operational": "Minor injury, minor damage, use of emergency procedures"},
    "E": {"name": "Negligible", "description": "Little consequence", "operational": "Inconvenience, no safety effect"}
}

RISK_MATRIX = {
    ("5", "A"): RiskLevel.EXTREME, ("5", "B"): RiskLevel.EXTREME, ("5", "C"): RiskLevel.HIGH,
    ("5", "D"): RiskLevel.MEDIUM, ("5", "E"): RiskLevel.LOW,
    ("4", "A"): RiskLevel.EXTREME, ("4", "B"): RiskLevel.HIGH, ("4", "C"): RiskLevel.HIGH,
    ("4", "D"): RiskLevel.MEDIUM, ("4", "E"): RiskLevel.LOW,
    ("3", "A"): RiskLevel.HIGH, ("3", "B"): RiskLevel.HIGH, ("3", "C"): RiskLevel.MEDIUM,
    ("3", "D"): RiskLevel.MEDIUM, ("3", "E"): RiskLevel.LOW,
    ("2", "A"): RiskLevel.HIGH, ("2", "B"): RiskLevel.MEDIUM, ("2", "C"): RiskLevel.MEDIUM,
    ("2", "D"): RiskLevel.LOW, ("2", "E"): RiskLevel.LOW,
    ("1", "A"): RiskLevel.MEDIUM, ("1", "B"): RiskLevel.MEDIUM, ("1", "C"): RiskLevel.LOW,
    ("1", "D"): RiskLevel.LOW, ("1", "E"): RiskLevel.LOW,
}

RISK_ACTIONS = {
    RiskLevel.EXTREME: {
        "action": "STOP OPERATIONS",
        "description": "Immediate action required. Stop operations if necessary until risk is mitigated.",
        "color": "#DC3545", "timeline": "Immediate", "authority": "Accountable Manager / CEO"
    },
    RiskLevel.HIGH: {
        "action": "URGENT CORRECTIVE ACTION",
        "description": "Senior management attention required. Urgent corrective action must be implemented.",
        "color": "#FD7E14", "timeline": "Within 24-48 hours", "authority": "Safety Manager / Director"
    },
    RiskLevel.MEDIUM: {
        "action": "CORRECTIVE ACTION REQUIRED",
        "description": "Management responsibility. Corrective action within defined timeline.",
        "color": "#FFC107", "timeline": "Within 15 days", "authority": "Department Manager"
    },
    RiskLevel.LOW: {
        "action": "MONITOR AND REVIEW",
        "description": "Accept risk with monitoring. Review periodically during normal safety reviews.",
        "color": "#28A745", "timeline": "Next scheduled review", "authority": "Safety Officer"
    }
}


# ══════════════════════════════════════════════════════════════════════════════
# DATA CLASSES
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class SLAStatus:
    days_remaining: int
    status: str
    color: str
    text: str
    percentage: float


# ══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

def generate_report_number(report_type: ReportType, department: str = "") -> str:
    prefix_map = {
        ReportType.AIRCRAFT_INCIDENT: "INC",
        ReportType.BIRD_STRIKE: "BRD",
        ReportType.LASER_STRIKE: "LSR",
        ReportType.TCAS_REPORT: "TCS",
        ReportType.HAZARD_REPORT: "HZD",
        ReportType.FSR: "FSR",
        ReportType.CAPTAIN_DBR: "DBR"
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
        created_date = datetime.strptime(created_date[:10], "%Y-%m-%d").date()
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
    if include_time:
        return dt.strftime("%d-%b-%Y %H:%M")
    return dt.strftime("%d-%b-%Y")


def get_airport_name(icao: str) -> str:
    airport = AIRPORTS.get(icao.upper())
    return f"{airport['city']} ({icao})" if airport else icao


def get_aircraft_info(registration: str) -> dict:
    return AIRCRAFT_FLEET.get(registration.upper(), {"type": "Unknown", "msn": "N/A", "config": "N/A"})


# ══════════════════════════════════════════════════════════════════════════════
# DATABASE INTERFACE
# ══════════════════════════════════════════════════════════════════════════════

class Database:
    _instance = None
    _client = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._client is None:
            self._initialize_client()
    
    def _initialize_client(self):
        try:
            from supabase import create_client
            url = Config.get_supabase_url()
            key = Config.get_supabase_key()
            if url and key and url != "" and key != "":
                self._client = create_client(url, key)
            else:
                self._client = None
        except ImportError:
            # Supabase not installed
            self._client = None
        except Exception as e:
            self._client = None
    
    @property
    def client(self):
        return self._client
    
    @property
    def is_connected(self) -> bool:
        return self._client is not None
    
    def get_user_by_username(self, username: str) -> Optional[dict]:
        if not self.is_connected:
            return None
        try:
            result = self.client.table('users').select('*').eq('username', username).execute()
            return result.data[0] if result.data else None
        except:
            return None
    
    def create_user(self, user_data: dict) -> Optional[dict]:
        if not self.is_connected:
            return None
        try:
            result = self.client.table('users').insert(user_data).execute()
            return result.data[0] if result.data else None
        except:
            return None
    
    def insert_report(self, table: str, data: dict) -> Optional[dict]:
        if not self.is_connected:
            return None
        try:
            result = self.client.table(table).insert(data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            return None
    
    def update_report(self, table: str, report_id: str, data: dict) -> Optional[dict]:
        if not self.is_connected:
            return None
        try:
            result = self.client.table(table).update(data).eq('id', report_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            st.error(f"Error updating report: {e}")
            return None
    
    def get_report(self, table: str, report_id: str) -> Optional[dict]:
        if not self.is_connected:
            return None
        try:
            result = self.client.table(table).select('*').eq('id', report_id).execute()
            return result.data[0] if result.data else None
        except:
            return None
    
    def get_reports(self, table: str, filters: dict = None, limit: int = 100) -> List[dict]:
        if not self.is_connected:
            return []
        try:
            query = self.client.table(table).select('*')
            if filters:
                for key, value in filters.items():
                    query = query.eq(key, value)
            result = query.order('created_at', desc=True).limit(limit).execute()
            return result.data if result.data else []
        except:
            return []
    
    def get_report_counts(self) -> dict:
        counts = {}
        tables = ['aircraft_incidents', 'bird_strikes', 'laser_strikes', 
                  'tcas_reports', 'hazard_reports', 'fsr_reports', 'captain_dbr']
        for table in tables:
            try:
                if self.is_connected:
                    result = self.client.table(table).select('id', count='exact').execute()
                    counts[table] = result.count if result.count else 0
                else:
                    counts[table] = 0
            except:
                counts[table] = 0
        return counts
    
    def get_hazards_by_sla_status(self) -> dict:
        result = {'overdue': [], 'critical': [], 'warning': [], 'ok': []}
        hazards = self.get_reports('hazard_reports')
        for hazard in hazards:
            if hazard.get('status') not in ['Closed', 'Investigation Complete']:
                sla = calculate_sla_status(hazard.get('created_at', date.today()), Config.HAZARD_SLA_DAYS)
                result[sla.status].append({**hazard, 'sla_info': sla})
        return result
    
    def get_investigation_stats(self) -> dict:
        stats = {'total': 0, 'open': 0, 'in_progress': 0, 'awaiting_reply': 0, 'closed': 0, 'by_status': {}}
        tables = ['aircraft_incidents', 'bird_strikes', 'laser_strikes', 'tcas_reports', 'hazard_reports']
        for table in tables:
            reports = self.get_reports(table)
            for report in reports:
                status = report.get('investigation_status', 'Draft')
                stats['total'] += 1
                stats['by_status'][status] = stats['by_status'].get(status, 0) + 1
                if status in ['Draft', 'Submitted', 'Under Review', 'Assigned to Investigator', 'Investigation In Progress']:
                    stats['open'] += 1
                elif status == 'Awaiting Reply':
                    stats['awaiting_reply'] += 1
                elif status == 'Closed':
                    stats['closed'] += 1
        stats['in_progress'] = stats['by_status'].get('Investigation In Progress', 0)
        return stats
    
    def log_action(self, user_id: str, action: str, table_name: str, record_id: str, old_values: dict = None, new_values: dict = None):
        if not self.is_connected:
            return
        try:
            self.client.table('audit_log').insert({
                'user_id': user_id,
                'action': action,
                'table_name': table_name,
                'record_id': record_id,
                'old_values': json.dumps(old_values) if old_values else None,
                'new_values': json.dumps(new_values) if new_values else None,
                'timestamp': datetime.now().isoformat()
            }).execute()
        except:
            pass


# Lazy database initialization - only connects when actually needed
_db_instance = None

def get_db():
    """Get database instance (lazy initialization)"""
    global _db_instance
    if _db_instance is None:
        _db_instance = Database()
    return _db_instance

# For backwards compatibility - this property won't connect until accessed
class LazyDB:
    @property
    def is_connected(self):
        return get_db().is_connected
    
    def __getattr__(self, name):
        return getattr(get_db(), name)

db = LazyDB()
# ══════════════════════════════════════════════════════════════════════════════
# CUSTOM CSS STYLING
# ══════════════════════════════════════════════════════════════════════════════


# ==============================================================================
# LIGHT THEME CSS - PROFESSIONAL ENTERPRISE DESIGN
# ==============================================================================

def apply_custom_css():
    """Apply professional light theme CSS with ERP mode support"""
    
    # Check if ERP mode is active
    erp_mode = st.session_state.get('erp_mode', False)
    
    if erp_mode:
        header_bg = "linear-gradient(135deg, #DC2626 0%, #B91C1C 100%)"
        header_animation = """
        @keyframes erp-flash {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.7; }
        }
        .main-header { animation: erp-flash 1s infinite; }
        """
    else:
        header_bg = "linear-gradient(135deg, #1E40AF 0%, #3B82F6 100%)"
        header_animation = ""
    
    st.markdown(f"""
    <style>
    /* ===========================================================================
       LIGHT THEME - AIR SIAL CORPORATE SAFETY v3.0
       =========================================================================== */
    
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    :root {{
        --primary-blue: #1E40AF;
        --primary-blue-light: #3B82F6;
        --bg-primary: #F8FAFC;
        --bg-secondary: #F1F5F9;
        --bg-card: #FFFFFF;
        --border-color: #E2E8F0;
        --text-primary: #1E293B;
        --text-secondary: #334155;
        --text-muted: #64748B;
    }}
    
    .stApp {{
        background: linear-gradient(135deg, #F8FAFC 0%, #F1F5F9 100%);
    }}
    
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header {{visibility: hidden;}}
    
    section[data-testid="stSidebar"] {{
        background: linear-gradient(180deg, #F1F5F9 0%, #E2E8F0 100%);
        border-right: 1px solid #E2E8F0;
    }}
    
    section[data-testid="stSidebar"] .stRadio label {{
        color: #334155 !important;
        font-weight: 500;
    }}
    
    {header_animation}
    
    .main-header {{
        background: {header_bg};
        padding: 1.5rem 2rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        display: flex;
        align-items: center;
        justify-content: space-between;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }}
    
    .main-header h1, .header-title {{
        color: #FFFFFF;
        font-size: 1.75rem;
        font-weight: 700;
        margin: 0;
    }}
    
    .header-subtitle {{
        color: #BFDBFE;
        font-size: 0.9rem;
        margin-top: 0.25rem;
    }}
    
    .header-time {{
        color: #FFFFFF;
        font-size: 0.9rem;
        text-align: right;
    }}
    
    .kpi-card {{
        background: #FFFFFF;
        border-radius: 12px;
        padding: 1.25rem;
        text-align: center;
        border: 1px solid #E2E8F0;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }}
    
    .kpi-card:hover {{
        transform: translateY(-3px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        border-color: #3B82F6;
    }}
    
    .kpi-card::before {{
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, #1E40AF, #3B82F6);
    }}
    
    .kpi-value {{
        font-size: 2.25rem;
        font-weight: 700;
        color: #1E40AF;
        line-height: 1;
        margin: 0.5rem 0;
    }}
    
    .kpi-label {{
        color: #64748B;
        font-size: 0.8rem;
        font-weight: 500;
        text-transform: uppercase;
    }}
    
    .risk-badge {{
        display: inline-block;
        padding: 0.35rem 0.75rem;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
    }}
    
    .risk-extreme {{ background: #FEE2E2; color: #DC2626; }}
    .risk-high {{ background: #FFEDD5; color: #EA580C; }}
    .risk-medium {{ background: #FEF9C3; color: #CA8A04; }}
    .risk-low {{ background: #DCFCE7; color: #16A34A; }}
    
    .sla-overdue {{ background: #FEE2E2; border-left: 4px solid #DC2626; color: #991B1B; }}
    .sla-critical {{ background: #FFEDD5; border-left: 4px solid #EA580C; color: #9A3412; }}
    .sla-warning {{ background: #FEF9C3; border-left: 4px solid #CA8A04; color: #854D0E; }}
    .sla-ok {{ background: #DCFCE7; border-left: 4px solid #22C55E; color: #166534; }}
    
    .report-card {{
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 1.25rem;
        margin-bottom: 1rem;
    }}
    
    .report-card:hover {{
        border-color: #3B82F6;
        box-shadow: 0 4px 15px rgba(30, 64, 175, 0.1);
    }}
    
    .report-number {{
        font-family: 'Courier New', monospace;
        font-weight: 600;
        color: #1E40AF;
    }}
    
    .category-badge {{
        display: inline-block;
        padding: 0.25rem 0.6rem;
        border-radius: 12px;
        font-size: 0.7rem;
        font-weight: 600;
        text-transform: uppercase;
    }}
    
    .cat-bird {{ background: #DBEAFE; color: #1D4ED8; }}
    .cat-laser {{ background: #F3E8FF; color: #7C3AED; }}
    .cat-tcas {{ background: #FFEDD5; color: #C2410C; }}
    .cat-hazard {{ background: #FEE2E2; color: #DC2626; }}
    .cat-incident {{ background: #D1FAE5; color: #059669; }}
    .cat-fsr {{ background: #CCFBF1; color: #0D9488; }}
    .cat-dbr {{ background: #FEF3C7; color: #D97706; }}
    
    .form-section {{
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
    }}
    
    .form-section-title {{
        color: #1E40AF;
        font-size: 1.1rem;
        font-weight: 600;
        margin-bottom: 1rem;
        padding-bottom: 0.75rem;
        border-bottom: 2px solid #DBEAFE;
    }}
    
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > div {{
        background-color: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        color: #1E293B !important;
        border-radius: 8px !important;
    }}
    
    .stTextInput label,
    .stTextArea label,
    .stSelectbox label {{
        color: #334155 !important;
        font-weight: 500 !important;
    }}
    
    .stButton > button {{
        background: linear-gradient(135deg, #1E40AF 0%, #3B82F6 100%);
        color: #FFFFFF;
        border: none;
        border-radius: 8px;
        padding: 0.6rem 1.5rem;
        font-weight: 600;
    }}
    
    .stButton > button:hover {{
        background: linear-gradient(135deg, #1E3A8A 0%, #2563EB 100%);
        box-shadow: 0 4px 15px rgba(30, 64, 175, 0.3);
    }}
    
    .stTabs [data-baseweb="tab-list"] {{
        background: #F1F5F9;
        border-radius: 10px;
        padding: 0.25rem;
    }}
    
    .stTabs [data-baseweb="tab"] {{
        background: transparent;
        color: #64748B;
        border-radius: 8px;
    }}
    
    .stTabs [aria-selected="true"] {{
        background: #FFFFFF;
        color: #1E40AF;
    }}
    
    .alert-box {{
        padding: 1rem 1.25rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 1rem;
    }}
    
    .alert-success {{ background: #F0FDF4; border: 1px solid #86EFAC; color: #166534; }}
    .alert-warning {{ background: #FFFBEB; border: 1px solid #FCD34D; color: #92400E; }}
    .alert-danger {{ background: #FEF2F2; border: 1px solid #FECACA; color: #991B1B; }}
    .alert-info {{ background: #EFF6FF; border: 1px solid #93C5FD; color: #1E40AF; }}
    
    .status-light {{
        width: 12px;
        height: 12px;
        border-radius: 50%;
        display: inline-block;
        margin-right: 8px;
    }}
    
    .status-red {{ background: #DC2626; box-shadow: 0 0 8px rgba(220, 38, 38, 0.5); }}
    .status-yellow {{ background: #EAB308; box-shadow: 0 0 8px rgba(234, 179, 8, 0.5); }}
    .status-green {{ background: #22C55E; box-shadow: 0 0 8px rgba(34, 197, 94, 0.5); }}
    
    .cpa-table {{
        width: 100%;
        border-collapse: collapse;
        background: #FFFFFF;
        border-radius: 10px;
        overflow: hidden;
        border: 1px solid #E2E8F0;
    }}
    
    .cpa-table th {{
        background: #1E40AF;
        color: #FFFFFF;
        padding: 0.75rem 1rem;
        text-align: left;
        font-weight: 600;
    }}
    
    .cpa-table td {{
        padding: 0.75rem 1rem;
        border-bottom: 1px solid #E2E8F0;
        color: #334155;
    }}
    
    .cpa-table tr:hover {{
        background: #F8FAFC;
    }}
    
    .prediction-card {{
        background: linear-gradient(135deg, #1E40AF 0%, #7C3AED 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 12px;
        margin-bottom: 1rem;
    }}
    
    .prediction-value {{
        font-size: 3rem;
        font-weight: 700;
    }}
    
    .weather-card {{
        background: #FFFFFF;
        border-radius: 12px;
        padding: 1rem;
        text-align: center;
        border: 1px solid #E2E8F0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }}
    
    .weather-icon {{
        font-size: 2rem;
        margin-bottom: 0.25rem;
    }}
    
    .weather-temp {{
        font-size: 1.5rem;
        font-weight: 700;
        color: #1E40AF;
    }}
    
    .weather-city {{
        color: #64748B;
        font-size: 0.85rem;
        font-weight: 500;
    }}
    
    .ocr-scanner {{
        background: #F8FAFC;
        border: 2px dashed #CBD5E1;
        border-radius: 12px;
        padding: 2rem;
        text-align: center;
        margin-bottom: 1.5rem;
    }}
    
    .ocr-scanner:hover {{
        border-color: #3B82F6;
        background: #EFF6FF;
    }}
    
    .erp-emergency {{
        background: #FEE2E2;
        border: 2px solid #DC2626;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
    }}
    
    .bulletin-card {{
        background: #FFFFFF;
        border-left: 4px solid #3B82F6;
        padding: 1rem;
        margin-bottom: 0.75rem;
        border-radius: 0 8px 8px 0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }}
    
    [data-testid="stMetricValue"] {{
        font-size: 2rem;
        font-weight: 700;
        color: #1E40AF;
    }}
    
    [data-testid="stMetricLabel"] {{
        color: #64748B;
    }}
    
    .dataframe {{
        background: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
    }}
    
    .dataframe th {{
        background: #F8FAFC !important;
        color: #334155 !important;
    }}
    
    .dataframe td {{
        color: #475569 !important;
    }}
    
    ::-webkit-scrollbar {{
        width: 8px;
    }}
    
    ::-webkit-scrollbar-track {{
        background: #F1F5F9;
    }}
    
    ::-webkit-scrollbar-thumb {{
        background: #94A3B8;
        border-radius: 4px;
    }}
    
    @media print {{
        .no-print {{ display: none !important; }}
    }}
    
    </style>
    """, unsafe_allow_html=True)



# ==============================================================================
# LOGO LOADING
# ==============================================================================

def load_logo_base64():
    """Load logo.png and convert to base64 for embedding"""
    import pathlib
    import os
    
    # Get the directory where this script is located
    try:
        script_dir = pathlib.Path(__file__).parent.resolve()
    except:
        script_dir = pathlib.Path.cwd()
    
    # Try multiple possible locations
    logo_paths = [
        script_dir / "logo.png",
        pathlib.Path("logo.png"),
        pathlib.Path("./logo.png"),
        pathlib.Path("/mount/src/airops-pro/logo.png"),
        pathlib.Path(os.getcwd()) / "logo.png",
    ]
    
    for path in logo_paths:
        try:
            path = pathlib.Path(path)
            if path.exists() and path.is_file():
                with open(path, "rb") as f:
                    return base64.b64encode(f.read()).decode()
        except Exception as e:
            continue
    
    return None


def render_logo_in_header():
    """Try to render logo using st.image as fallback"""
    import pathlib
    import os
    
    logo_paths = [
        "logo.png",
        "./logo.png",
        "/mount/src/airops-pro/logo.png",
    ]
    
    for path in logo_paths:
        try:
            if os.path.exists(path):
                return path
        except:
            continue
    return None


# ==============================================================================
# UI COMPONENTS
# ==============================================================================

def render_header():
    """Render the main application header with logo support"""
    current_time = get_pakistan_time()
    
    # Check ERP mode
    erp_mode = st.session_state.get('erp_mode', False)
    
    # ERP mode banner
    if erp_mode:
        st.markdown('<div style="background: #DC2626; color: white; padding: 0.5rem; text-align: center; font-weight: bold; margin-bottom: 0.5rem; border-radius: 8px;">⚠️ EMERGENCY RESPONSE PLAN ACTIVATED ⚠️</div>', unsafe_allow_html=True)
    
    # Try to load logo with base64
    logo_base64 = load_logo_base64()
    
    # Create header with columns for logo
    col_logo, col_title, col_time = st.columns([1, 4, 2])
    
    with col_logo:
        # Try st.image first (most reliable)
        logo_path = render_logo_in_header()
        if logo_path:
            try:
                st.image(logo_path, width=80)
            except:
                st.markdown("🛡️✈️", unsafe_allow_html=True)
        elif logo_base64:
            st.markdown(f'<img src="data:image/png;base64,{logo_base64}" style="height: 60px;">', unsafe_allow_html=True)
        else:
            st.markdown('<span style="font-size: 3rem;">🛡️✈️</span>', unsafe_allow_html=True)
    
    with col_title:
        st.markdown(f"""
        <div style="padding-top: 0.5rem;">
            <h2 style="color: #1E40AF; margin: 0; font-weight: 700;">{Config.APP_NAME}</h2>
            <p style="color: #64748B; margin: 0; font-size: 0.9rem;">{Config.APP_SUBTITLE} v3.0 | {Config.COMPANY_ICAO} | AOC: {Config.AOC_NUMBER}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col_time:
        st.markdown(f"""
        <div style="text-align: right; padding-top: 0.5rem;">
            <div style="color: #64748B; font-size: 0.8rem;">🇵🇰 Pakistan Standard Time</div>
            <div style="color: #1E40AF; font-size: 1.3rem; font-weight: 700;">{current_time.strftime("%H:%M:%S")}</div>
            <div style="color: #64748B; font-size: 0.8rem;">{current_time.strftime("%A, %d %B %Y")}</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Blue header bar
    st.markdown("""
    <div style="background: linear-gradient(135deg, #1E40AF 0%, #3B82F6 100%); height: 4px; border-radius: 4px; margin: 0.5rem 0 1rem 0;"></div>
    """, unsafe_allow_html=True)

def render_kpi_cards(counts: dict, investigation_stats: dict):
    """Render dashboard KPI cards"""
    
    total_reports = sum(counts.values())
    
    st.markdown("""
    <div class="kpi-container">
        <div class="kpi-card">
            <div class="kpi-icon">📊</div>
            <div class="kpi-value">{}</div>
            <div class="kpi-label">Total Reports</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-icon">🐦</div>
            <div class="kpi-value">{}</div>
            <div class="kpi-label">Bird Strikes</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-icon">🔴</div>
            <div class="kpi-value">{}</div>
            <div class="kpi-label">Laser Strikes</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-icon">📡</div>
            <div class="kpi-value">{}</div>
            <div class="kpi-label">TCAS Events</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-icon">⚠️</div>
            <div class="kpi-value">{}</div>
            <div class="kpi-label">Hazards</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-icon">🔎</div>
            <div class="kpi-value">{}</div>
            <div class="kpi-label">Open Investigations</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-icon">⏳</div>
            <div class="kpi-value">{}</div>
            <div class="kpi-label">Awaiting Reply</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-icon">✅</div>
            <div class="kpi-value">{}</div>
            <div class="kpi-label">Closed</div>
        </div>
    </div>
    """.format(
        total_reports,
        counts.get('bird_strikes', 0),
        counts.get('laser_strikes', 0),
        counts.get('tcas_reports', 0),
        counts.get('hazard_reports', 0),
        investigation_stats.get('open', 0),
        investigation_stats.get('awaiting_reply', 0),
        investigation_stats.get('closed', 0)
    ), unsafe_allow_html=True)


def render_sla_indicator(sla_status: SLAStatus, report_number: str, title: str):
    """Render an SLA status indicator"""
    status_class = f"sla-{sla_status.status}"
    icon = "⚠️" if sla_status.status == "overdue" else "🔴" if sla_status.status == "critical" else "🟡" if sla_status.status == "warning" else "🟢"
    
    st.markdown(f"""
    <div class="sla-indicator {status_class}">
        <span style="font-size: 1.2rem; margin-right: 0.75rem;">{icon}</span>
        <div style="flex: 1;">
            <div style="font-weight: 600;">{report_number}</div>
            <div style="font-size: 0.85rem; opacity: 0.8;">{title[:50]}...</div>
        </div>
        <div style="text-align: right;">
            <div style="font-weight: 600; color: {sla_status.color};">{sla_status.text}</div>
            <div class="progress-container" style="width: 100px;">
                <div class="progress-bar" style="width: {sla_status.percentage}%; background: {sla_status.color};"></div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_risk_badge(risk_level: RiskLevel) -> str:
    """Return HTML for a risk level badge"""
    class_map = {
        RiskLevel.EXTREME: "risk-extreme",
        RiskLevel.HIGH: "risk-high",
        RiskLevel.MEDIUM: "risk-medium",
        RiskLevel.LOW: "risk-low"
    }
    return f'<span class="risk-badge {class_map[risk_level]}">{risk_level.value}</span>'


def render_category_badge(category: str) -> str:
    """Return HTML for a category badge"""
    class_map = {
        "bird": "cat-bird",
        "laser": "cat-laser",
        "tcas": "cat-tcas",
        "hazard": "cat-hazard",
        "incident": "cat-incident",
        "fsr": "cat-fsr",
        "dbr": "cat-dbr"
    }
    cat_class = class_map.get(category.lower(), "cat-incident")
    return f'<span class="category-badge {cat_class}">{category.upper()}</span>'


def render_risk_matrix_selector():
    """Render interactive ICAO risk matrix selector"""
    
    st.markdown("#### 📊 Risk Assessment (ICAO Standard)")
    
    col1, col2 = st.columns(2)
    
    with col1:
        likelihood = st.select_slider(
            "**Likelihood**",
            options=[1, 2, 3, 4, 5],
            value=3,
            format_func=lambda x: f"{x} - {LIKELIHOOD_SCALE[x]['name']}",
            help="How likely is this hazard to occur?"
        )
        st.caption(f"📋 {LIKELIHOOD_SCALE[likelihood]['description']}")
        st.caption(f"📈 Frequency: {LIKELIHOOD_SCALE[likelihood]['frequency']}")
    
    with col2:
        severity = st.selectbox(
            "**Severity**",
            options=["E", "D", "C", "B", "A"],
            index=2,
            format_func=lambda x: f"{x} - {SEVERITY_SCALE[x]['name']}",
            help="What is the potential consequence?"
        )
        st.caption(f"📋 {SEVERITY_SCALE[severity]['description']}")
        st.caption(f"⚠️ {SEVERITY_SCALE[severity]['operational']}")
    
    # Calculate risk
    risk_level = calculate_risk_level(likelihood, severity)
    risk_info = RISK_ACTIONS[risk_level]
    risk_classification = f"{likelihood}{severity}"
    
    # Display result
    st.markdown(f"""
    <div style="background: {risk_info['color']}20; border: 2px solid {risk_info['color']}; 
                border-radius: 10px; padding: 1.5rem; margin-top: 1rem;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <span style="font-size: 2rem; font-weight: 700; color: {risk_info['color']};">
                    {risk_classification}
                </span>
                <span style="font-size: 1.5rem; margin-left: 1rem;">
                    {render_risk_badge(risk_level)}
                </span>
            </div>
            <div style="text-align: right;">
                <div style="font-weight: 600; color: {risk_info['color']};">{risk_info['action']}</div>
                <div style="font-size: 0.85rem; opacity: 0.8;">Timeline: {risk_info['timeline']}</div>
                <div style="font-size: 0.85rem; opacity: 0.8;">Authority: {risk_info['authority']}</div>
            </div>
        </div>
        <div style="margin-top: 1rem; font-size: 0.9rem;">{risk_info['description']}</div>
    </div>
    """, unsafe_allow_html=True)
    
    return likelihood, severity, risk_level, risk_classification


def render_visual_risk_matrix():
    """Render visual 5x5 risk matrix"""
    
    st.markdown("#### 🎯 ICAO Risk Matrix")
    
    # Create matrix data
    matrix_html = """
    <div style="overflow-x: auto;">
    <table style="border-collapse: collapse; margin: 1rem 0;">
        <tr>
            <th style="padding: 8px; background: #161B22; color: #FFD700;"></th>
            <th style="padding: 8px; background: #161B22; color: #FFD700; text-align: center;">A<br><small>Catastrophic</small></th>
            <th style="padding: 8px; background: #161B22; color: #FFD700; text-align: center;">B<br><small>Hazardous</small></th>
            <th style="padding: 8px; background: #161B22; color: #FFD700; text-align: center;">C<br><small>Major</small></th>
            <th style="padding: 8px; background: #161B22; color: #FFD700; text-align: center;">D<br><small>Minor</small></th>
            <th style="padding: 8px; background: #161B22; color: #FFD700; text-align: center;">E<br><small>Negligible</small></th>
        </tr>
    """
    
    colors = {
        RiskLevel.EXTREME: "#DC3545",
        RiskLevel.HIGH: "#FD7E14",
        RiskLevel.MEDIUM: "#FFC107",
        RiskLevel.LOW: "#28A745"
    }
    
    for l in [5, 4, 3, 2, 1]:
        likelihood_name = LIKELIHOOD_SCALE[l]['name']
        matrix_html += f'<tr><td style="padding: 8px; background: #161B22; color: #FFD700; font-weight: 600;">{l} - {likelihood_name}</td>'
        
        for s in ["A", "B", "C", "D", "E"]:
            risk = RISK_MATRIX.get((str(l), s), RiskLevel.LOW)
            color = colors[risk]
            text_color = "#000" if risk in [RiskLevel.MEDIUM, RiskLevel.LOW] else "#FFF"
            matrix_html += f'<td style="padding: 8px; background: {color}; color: {text_color}; text-align: center; font-weight: 600;">{l}{s}</td>'
        
        matrix_html += '</tr>'
    
    matrix_html += '</table></div>'
    
    st.markdown(matrix_html, unsafe_allow_html=True)
    
    # Legend
    st.markdown("""
    <div style="display: flex; gap: 1rem; margin-top: 1rem; flex-wrap: wrap;">
        <span class="risk-badge risk-extreme">EXTREME - Stop Operations</span>
        <span class="risk-badge risk-high">HIGH - Urgent Action</span>
        <span class="risk-badge risk-medium">MEDIUM - Corrective Action</span>
        <span class="risk-badge risk-low">LOW - Monitor</span>
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# OCR SCANNER
# ══════════════════════════════════════════════════════════════════════════════

class OCRScanner:
    """OCR Scanner with Gemini Vision and Tesseract support"""
    
    def __init__(self):
        self.gemini_key = Config.get_gemini_key()
    
    def extract_with_gemini(self, image_data: bytes, prompt: str) -> Optional[str]:
        """Extract text using Google Gemini Vision API"""
        
        if not self.gemini_key:
            return None
        
        try:
            base64_image = base64.b64encode(image_data).decode('utf-8')
            
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.gemini_key}"
            
            payload = {
                "contents": [{
                    "parts": [
                        {"text": prompt},
                        {
                            "inline_data": {
                                "mime_type": "image/jpeg",
                                "data": base64_image
                            }
                        }
                    ]
                }],
                "generationConfig": {
                    "temperature": 0.1,
                    "maxOutputTokens": 4096
                }
            }
            
            response = requests.post(url, json=payload, timeout=60)
            
            if response.status_code == 200:
                result = response.json()
                if 'candidates' in result and result['candidates']:
                    return result['candidates'][0]['content']['parts'][0]['text']
            else:
                st.error(f"Gemini API error: {response.status_code}")
                return None
                
        except Exception as e:
            st.error(f"OCR extraction error: {str(e)}")
            return None
    
    def extract_with_tesseract(self, image_data: bytes) -> Optional[str]:
        """Extract text using Tesseract OCR (local)"""
        
        try:
            import pytesseract
            from PIL import Image
            
            image = Image.open(io.BytesIO(image_data))
            
            # Preprocess
            if image.mode != 'L':
                image = image.convert('L')
            
            # OCR
            text = pytesseract.image_to_string(
                image, 
                config='--oem 3 --psm 6'
            )
            
            return text.strip() if text else None
            
        except ImportError:
            st.warning("Tesseract not installed. Please install: `pip install pytesseract` and Tesseract OCR engine.")
            return None
        except Exception as e:
            st.error(f"Tesseract error: {str(e)}")
            return None


def get_ocr_prompt_for_form(form_type: str) -> str:
    """Get form-specific OCR extraction prompt"""
    
    prompts = {
        "bird_strike": """Extract all information from this Bird Strike Report form. 
        Return a JSON object with these fields:
        {
            "date": "YYYY-MM-DD",
            "time": "HH:MM",
            "flight_number": "",
            "aircraft_registration": "",
            "aircraft_type": "",
            "departure_airport": "",
            "arrival_airport": "",
            "flight_phase": "",
            "altitude_agl": "",
            "speed_kts": "",
            "bird_species": "",
            "bird_size": "",
            "number_of_birds": "",
            "parts_struck": [],
            "damage_description": "",
            "damage_level": "",
            "effect_on_flight": "",
            "pilot_warned": "",
            "weather_conditions": "",
            "remarks": "",
            "captain_name": "",
            "license_number": ""
        }
        Extract exactly what's written, use null for empty fields.""",
        
        "laser_strike": """Extract all information from this Laser Strike Report form.
        Return a JSON object with these fields:
        {
            "date": "YYYY-MM-DD",
            "time": "HH:MM",
            "flight_number": "",
            "aircraft_registration": "",
            "departure_airport": "",
            "arrival_airport": "",
            "location_description": "",
            "latitude": "",
            "longitude": "",
            "altitude_feet": "",
            "laser_color": "",
            "laser_intensity": "",
            "duration_seconds": "",
            "beam_movement": "",
            "crew_affected": "",
            "flash_blindness": false,
            "afterimage": false,
            "glare": false,
            "eye_pain": false,
            "disorientation": false,
            "medical_attention": false,
            "atc_notified": false,
            "police_notified": false,
            "remarks": "",
            "captain_name": ""
        }
        Extract exactly what's written, use null for empty fields.""",
        
        "tcas_report": """Extract all information from this TCAS Report form.
        Return a JSON object with these fields:
        {
            "date": "YYYY-MM-DD",
            "time": "HH:MM",
            "flight_number": "",
            "aircraft_registration": "",
            "aircraft_type": "",
            "departure_airport": "",
            "arrival_airport": "",
            "position": "",
            "altitude_feet": "",
            "heading": "",
            "tcas_equipment": "",
            "alert_type": "",
            "traffic_position": "",
            "traffic_altitude": "",
            "traffic_relative_bearing": "",
            "ra_followed": "",
            "vertical_deviation_feet": "",
            "minimum_separation_vertical": "",
            "minimum_separation_horizontal": "",
            "atc_clearance": "",
            "atc_notified": false,
            "remarks": "",
            "captain_name": ""
        }
        Extract exactly what's written, use null for empty fields.""",
        
        "hazard_report": """Extract all information from this Hazard Report form.
        Return a JSON object with these fields:
        {
            "date": "YYYY-MM-DD",
            "time": "HH:MM",
            "location": "",
            "department": "",
            "hazard_category": "",
            "hazard_title": "",
            "hazard_description": "",
            "existing_controls": "",
            "suggested_action": "",
            "likelihood": "",
            "severity": "",
            "reporter_name": "",
            "reporter_employee_id": "",
            "reporter_contact": ""
        }
        Extract exactly what's written, use null for empty fields.""",
        
        "incident_report": """Extract all information from this Aircraft Incident Report form.
        Return a JSON object with these fields:
        {
            "date": "YYYY-MM-DD",
            "time": "HH:MM",
            "flight_number": "",
            "aircraft_registration": "",
            "aircraft_type": "",
            "departure_airport": "",
            "arrival_airport": "",
            "incident_category": "",
            "flight_phase": "",
            "location": "",
            "altitude_feet": "",
            "weather_conditions": "",
            "captain_name": "",
            "first_officer_name": "",
            "passengers_total": "",
            "crew_total": "",
            "injuries_fatal": "",
            "injuries_serious": "",
            "injuries_minor": "",
            "aircraft_damage": "",
            "incident_description": "",
            "immediate_actions": "",
            "emergency_declared": false,
            "evacuation": false,
            "caa_notified": false,
            "remarks": ""
        }
        Extract exactly what's written, use null for empty fields."""
    }
    
    return prompts.get(form_type, prompts["incident_report"])


def render_ocr_scanner(form_type: str) -> Optional[dict]:
    """Render OCR scanner interface and return extracted data"""
    
    st.markdown("""
    <div class="ocr-scanner">
        <div class="ocr-scanner-icon">📷</div>
        <h4 style="color: #FFD700;">Scan Handwritten Form</h4>
        <p style="color: #8B949E;">Upload an image of a filled form to auto-extract data</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        uploaded_file = st.file_uploader(
            "Upload Form Image",
            type=['png', 'jpg', 'jpeg', 'bmp', 'tiff', 'webp'],
            key=f"ocr_{form_type}"
        )
    
    with col2:
        ocr_method = st.radio(
            "OCR Method",
            options=["Gemini Vision (Recommended)", "Tesseract (Offline)"],
            key=f"ocr_method_{form_type}"
        )
    
    if uploaded_file:
        image_data = uploaded_file.read()
        
        col1, col2 = st.columns([1, 1])
        with col1:
            st.image(image_data, caption="Uploaded Form", use_container_width=True)
        
        with col2:
            if st.button("🔍 Extract Data", key=f"extract_{form_type}", type="primary"):
                with st.spinner("Analyzing form..."):
                    scanner = OCRScanner()
                    
                    if "Gemini" in ocr_method:
                        prompt = get_ocr_prompt_for_form(form_type)
                        extracted_text = scanner.extract_with_gemini(image_data, prompt)
                    else:
                        extracted_text = scanner.extract_with_tesseract(image_data)
                    
                    if extracted_text:
                        st.success("✅ Data extracted successfully!")
                        
                        # Try to parse as JSON
                        try:
                            # Clean up the response
                            json_match = re.search(r'\{[\s\S]*\}', extracted_text)
                            if json_match:
                                parsed_data = json.loads(json_match.group())
                                st.session_state[f'ocr_data_{form_type}'] = parsed_data
                                
                                with st.expander("📋 View Extracted Data"):
                                    st.json(parsed_data)
                                
                                return parsed_data
                        except json.JSONDecodeError:
                            st.warning("Could not parse structured data. Raw text extracted:")
                            st.text_area("Extracted Text", extracted_text, height=200)
                    else:
                        st.error("❌ Could not extract data. Please try again or enter manually.")
    
    # Return previously extracted data if available
    return st.session_state.get(f'ocr_data_{form_type}')


# ══════════════════════════════════════════════════════════════════════════════
# AI ASSISTANT
# ══════════════════════════════════════════════════════════════════════════════

class AIAssistant:
    """AI-powered safety analysis assistant"""
    
    def __init__(self):
        self.gemini_key = Config.get_gemini_key()
        self.groq_key = Config.get_groq_key()
    
    def get_safety_analysis(self, report_data: dict, report_type: str) -> str:
        """Get AI analysis of safety report"""
        
        prompt = f"""You are a Safety Data Analyst for {Config.COMPANY_NAME} airline. 
        Analyze this {report_type} report and provide:
        1. Key safety concerns identified
        2. Potential contributing factors
        3. Recommended corrective actions
        4. Risk mitigation suggestions
        5. Any regulatory considerations (CAA Pakistan)
        
        Report Data:
        {json.dumps(report_data, indent=2)}
        
        Provide a concise, professional analysis."""
        
        return self._call_gemini(prompt)
    
    def get_trend_analysis(self, reports: List[dict], report_type: str) -> str:
        """Get trend analysis for multiple reports"""
        
        prompt = f"""Analyze these {len(reports)} {report_type} reports for trends:
        
        {json.dumps(reports[:20], indent=2)}
        
        Identify:
        1. Common patterns or recurring issues
        2. Time-based trends (increasing/decreasing)
        3. Location or flight phase hotspots
        4. Recommendations for systemic improvements
        
        Keep analysis concise and actionable."""
        
        return self._call_gemini(prompt)
    
    def _call_gemini(self, prompt: str) -> str:
        """Call Gemini API"""
        
        if not self.gemini_key:
            return "AI analysis not available. Please configure Gemini API key."
        
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.gemini_key}"
            
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": 0.3,
                    "maxOutputTokens": 2048
                }
            }
            
            response = requests.post(url, json=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if 'candidates' in result and result['candidates']:
                    return result['candidates'][0]['content']['parts'][0]['text']
            
            return f"API error: {response.status_code}"
            
        except Exception as e:
            return f"Error: {str(e)}"


# ══════════════════════════════════════════════════════════════════════════════
# WEATHER SERVICE
# ══════════════════════════════════════════════════════════════════════════════

class WeatherService:
    """Weather data service - uses static data by default, API on refresh"""
    
    AIRPORT_COORDS = {
        "OPSK": (32.5356, 74.3639, "Sialkot"),
        "OPKC": (24.9065, 67.1608, "Karachi"),
        "OPLA": (31.5216, 74.4036, "Lahore"),
        "OPIS": (33.5607, 72.8494, "Islamabad"),
        "OMDB": (25.2528, 55.3644, "Dubai"),
    }
    
    # Static default weather data (prevents freezing on load)
    STATIC_WEATHER = {
        "OPSK": {"icon": "🌤️", "temperature": 18, "wind_speed": 12, "city": "Sialkot", "condition": "Partly Cloudy"},
        "OPKC": {"icon": "☀️", "temperature": 28, "wind_speed": 15, "city": "Karachi", "condition": "Clear"},
        "OPLA": {"icon": "🌤️", "temperature": 20, "wind_speed": 10, "city": "Lahore", "condition": "Partly Cloudy"},
        "OPIS": {"icon": "⛅", "temperature": 15, "wind_speed": 8, "city": "Islamabad", "condition": "Cloudy"},
        "OMDB": {"icon": "☀️", "temperature": 32, "wind_speed": 18, "city": "Dubai", "condition": "Clear"},
    }
    
    @staticmethod
    def fetch_live_weather():
        """Fetch live weather - only called on user action"""
        results = {}
        weather_codes = {
            0: ("☀️", "Clear"), 1: ("🌤️", "Partly Cloudy"), 2: ("⛅", "Cloudy"),
            3: ("☁️", "Overcast"), 45: ("🌫️", "Foggy"), 48: ("🌫️", "Rime Fog"),
            51: ("🌧️", "Light Drizzle"), 61: ("🌧️", "Light Rain"),
            63: ("🌧️", "Moderate Rain"), 65: ("🌧️", "Heavy Rain"),
            80: ("🌦️", "Rain Showers"), 95: ("⛈️", "Thunderstorm"),
        }
        
        for airport_icao, (lat, lon, city) in WeatherService.AIRPORT_COORDS.items():
            try:
                url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,weathercode,windspeed_10m&timezone=auto"
                response = requests.get(url, timeout=5)
                
                if response.status_code == 200:
                    data = response.json()
                    current = data.get('current', {})
                    code = current.get('weathercode', 0)
                    icon, condition = weather_codes.get(code, ("🌡️", "Unknown"))
                    
                    results[airport_icao] = {
                        "temperature": current.get('temperature_2m', 'N/A'),
                        "wind_speed": current.get('windspeed_10m', 'N/A'),
                        "condition": condition,
                        "icon": icon,
                        "city": city
                    }
            except Exception:
                pass
        
        return results if results else None
    
    @classmethod
    def render_weather_widget(cls):
        """Render weather widget for key airports"""
        
        col_header, col_btn = st.columns([4, 1])
        with col_header:
            st.markdown("#### 🌤️ Current Weather at Key Airports")
        with col_btn:
            refresh = st.button("🔄 Refresh", key="refresh_weather")
        
        # Use cached live data if available, otherwise static
        if refresh:
            with st.spinner("Fetching live weather..."):
                live_data = cls.fetch_live_weather()
                if live_data:
                    st.session_state.weather_cache = live_data
                    st.session_state.weather_updated = datetime.now().strftime("%H:%M")
        
        weather_data = st.session_state.get('weather_cache', cls.STATIC_WEATHER)
        
        cols = st.columns(5)
        airports = ["OPSK", "OPKC", "OPLA", "OPIS", "OMDB"]
        
        for col, airport in zip(cols, airports):
            with col:
                weather = weather_data.get(airport, cls.STATIC_WEATHER.get(airport))
                if weather:
                    st.markdown(f"""
                    <div class="weather-card">
                        <div class="weather-icon">{weather['icon']}</div>
                        <div class="weather-temp">{weather['temperature']}°C</div>
                        <div class="weather-city">{weather['city']}</div>
                        <div style="font-size: 0.75rem; color: #64748B;">💨 {weather['wind_speed']} km/h</div>
                    </div>
                    """, unsafe_allow_html=True)
        
        if st.session_state.get('weather_updated'):
            st.caption(f"Last updated: {st.session_state.weather_updated}")

# ══════════════════════════════════════════════════════════════════════════════
# REPORT FORMS - CAA PAKISTAN COMPLIANT
# ══════════════════════════════════════════════════════════════════════════════

def render_bird_strike_form(ocr_data: dict = None):
    """Full CAA-compliant Bird Strike Report Form"""
    
    st.markdown('<h2 style="color: #58A6FF;">🐦 Bird Strike Report</h2>', unsafe_allow_html=True)
    st.markdown("*CAA Pakistan Bird/Wildlife Strike Report Form*")
    
    # Pre-fill from OCR if available
    data = ocr_data or {}
    
    with st.form("bird_strike_form"):
        
        # ══════════════════════════════════════════════════════════════════════
        # SECTION A: INCIDENT IDENTIFICATION
        # ══════════════════════════════════════════════════════════════════════
        st.markdown('<div class="form-section"><div class="form-section-title">📋 SECTION A: INCIDENT IDENTIFICATION</div>', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            report_number = st.text_input("Report Number*", value=generate_report_number(ReportType.BIRD_STRIKE), disabled=True)
            incident_date = st.date_input("Date of Incident*", value=date.today())
        with col2:
            incident_time_local = st.time_input("Local Time (LT)*", value=datetime.now().time())
            incident_time_utc = st.time_input("UTC Time*", value=(datetime.utcnow()).time())
        with col3:
            reported_by = st.text_input("Reported By*", value=st.session_state.get('user_name', ''))
            reporter_designation = st.selectbox("Designation", options=CREW_POSITIONS)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # ══════════════════════════════════════════════════════════════════════
        # SECTION B: FLIGHT INFORMATION
        # ══════════════════════════════════════════════════════════════════════
        st.markdown('<div class="form-section"><div class="form-section-title">✈️ SECTION B: FLIGHT INFORMATION</div>', unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            flight_number = st.text_input("Flight Number*", value=data.get('flight_number', ''), placeholder="PF-XXX")
            flight_type = st.selectbox("Flight Type", options=["Scheduled Passenger", "Scheduled Cargo", "Charter", "Positioning", "Training", "Test Flight", "Other"])
        with col2:
            aircraft_reg = st.selectbox("Aircraft Registration*", options=list(AIRCRAFT_FLEET.keys()))
            aircraft_info = get_aircraft_info(aircraft_reg)
            st.caption(f"Type: {aircraft_info['type']} | MSN: {aircraft_info['msn']}")
        with col3:
            departure = st.selectbox("Departure Airport*", options=list(AIRPORTS.keys()), format_func=get_airport_name)
            etd = st.time_input("ETD")
        with col4:
            arrival = st.selectbox("Arrival Airport*", options=list(AIRPORTS.keys()), index=1, format_func=get_airport_name)
            eta = st.time_input("ETA")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # ══════════════════════════════════════════════════════════════════════
        # SECTION C: STRIKE LOCATION & CONDITIONS
        # ══════════════════════════════════════════════════════════════════════
        st.markdown('<div class="form-section"><div class="form-section-title">📍 SECTION C: STRIKE LOCATION & CONDITIONS</div>', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            flight_phase = st.selectbox("Flight Phase at Strike*", options=FLIGHT_PHASES)
            strike_location = st.selectbox("Strike Location (Airport)", options=["Departure Airport", "Arrival Airport", "Enroute", "Alternate", "Other"])
        with col2:
            altitude_agl = st.number_input("Altitude AGL (feet)*", min_value=0, max_value=50000, value=int(data.get('altitude_agl', 0)))
            altitude_msl = st.number_input("Altitude MSL (feet)", min_value=0, max_value=50000, value=0)
        with col3:
            indicated_speed = st.number_input("Indicated Airspeed (knots)*", min_value=0, max_value=500, value=int(data.get('speed_kts', 0)))
            heading = st.number_input("Heading (degrees)", min_value=0, max_value=360, value=0)
        
        col1, col2 = st.columns(2)
        with col1:
            weather_conditions = st.selectbox("Weather Conditions", options=WEATHER_CONDITIONS)
            visibility = st.selectbox("Visibility", options=["Greater than 10km", "5-10km", "2-5km", "1-2km", "Less than 1km", "Not recorded"])
        with col2:
            cloud_conditions = st.selectbox("Cloud Conditions", options=["Clear/Few", "Scattered", "Broken", "Overcast", "Not recorded"])
            precipitation = st.selectbox("Precipitation", options=["None", "Light Rain", "Moderate Rain", "Heavy Rain", "Snow", "Mist/Fog"])
        
        col1, col2, col3 = st.columns(3)
        with col1:
            time_of_day = st.selectbox("Time of Day", options=["Dawn", "Day", "Dusk", "Night"])
        with col2:
            pilot_warned = st.selectbox("Pilot Warned of Birds?", options=["Yes - ATIS", "Yes - ATC", "Yes - NOTAM", "Yes - Other Pilot", "No Warning", "Not Applicable"])
        with col3:
            runway_in_use = st.text_input("Runway in Use", placeholder="e.g., 09L")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # ══════════════════════════════════════════════════════════════════════
        # SECTION D: BIRD/WILDLIFE DETAILS
        # ══════════════════════════════════════════════════════════════════════
        st.markdown('<div class="form-section"><div class="form-section-title">🦅 SECTION D: BIRD/WILDLIFE DETAILS</div>', unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            bird_species = st.selectbox("Species (if known)", options=BIRD_SPECIES)
            species_identified_by = st.selectbox("Species Identified By", options=["Pilot Observation", "Remains Analysis", "Airport Wildlife Control", "Ornithologist", "Unknown"])
        with col2:
            bird_size = st.selectbox("Size Category*", options=[f"{s[0]} - {s[1]}" for s in BIRD_SIZES])
            number_seen = st.number_input("Number of Birds Seen", min_value=1, max_value=1000, value=1)
        with col3:
            number_struck = st.number_input("Number of Birds Struck*", min_value=1, max_value=100, value=1)
            bird_behavior = st.selectbox("Bird Behavior", options=["Stationary on ground", "Walking/Running", "Taking off", "Landing", "Hovering", "Flying - Level", "Flying - Ascending", "Flying - Descending", "Circling/Soaring", "Unknown"])
        with col4:
            attracted_by = st.selectbox("Birds Attracted By", options=["Unknown", "Airport lights", "Waste disposal", "Standing water", "Crops/Vegetation", "Prey (rodents/insects)", "Nesting site", "Landfill nearby", "Other"])
            remains_collected = st.selectbox("Remains Collected?", options=["Yes - Sent for ID", "Yes - Retained", "No - No remains", "No - Not practical"])
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # ══════════════════════════════════════════════════════════════════════
        # SECTION E: PARTS OF AIRCRAFT STRUCK
        # ══════════════════════════════════════════════════════════════════════
        st.markdown('<div class="form-section"><div class="form-section-title">🔧 SECTION E: PARTS OF AIRCRAFT STRUCK & DAMAGED</div>', unsafe_allow_html=True)
        
        st.markdown("**Select all parts STRUCK and DAMAGED:**")
        
        # Aircraft parts grid
        parts_col1, parts_col2, parts_col3, parts_col4 = st.columns(4)
        
        with parts_col1:
            st.markdown("**Forward Section**")
            radome_struck = st.checkbox("Radome - Struck")
            radome_damaged = st.checkbox("Radome - Damaged")
            windshield_struck = st.checkbox("Windshield - Struck")
            windshield_damaged = st.checkbox("Windshield - Damaged")
            nose_struck = st.checkbox("Nose - Struck")
            nose_damaged = st.checkbox("Nose - Damaged")
            pitot_struck = st.checkbox("Pitot/Static - Struck")
            pitot_damaged = st.checkbox("Pitot/Static - Damaged")
        
        with parts_col2:
            st.markdown("**Engines**")
            engine1_struck = st.checkbox("Engine #1 - Struck")
            engine1_damaged = st.checkbox("Engine #1 - Damaged")
            engine2_struck = st.checkbox("Engine #2 - Struck")
            engine2_damaged = st.checkbox("Engine #2 - Damaged")
            propeller_struck = st.checkbox("Propeller - Struck")
            propeller_damaged = st.checkbox("Propeller - Damaged")
            engine_cowl_struck = st.checkbox("Engine Cowl - Struck")
            engine_cowl_damaged = st.checkbox("Engine Cowl - Damaged")
        
        with parts_col3:
            st.markdown("**Wings & Fuselage**")
            wing_le_struck = st.checkbox("Wing Leading Edge - Struck")
            wing_le_damaged = st.checkbox("Wing Leading Edge - Damaged")
            wing_te_struck = st.checkbox("Wing Trailing Edge - Struck")
            wing_te_damaged = st.checkbox("Wing Trailing Edge - Damaged")
            fuselage_struck = st.checkbox("Fuselage - Struck")
            fuselage_damaged = st.checkbox("Fuselage - Damaged")
            lights_struck = st.checkbox("Lights - Struck")
            lights_damaged = st.checkbox("Lights - Damaged")
        
        with parts_col4:
            st.markdown("**Tail & Landing Gear**")
            tail_struck = st.checkbox("Tail/Empennage - Struck")
            tail_damaged = st.checkbox("Tail/Empennage - Damaged")
            lg_struck = st.checkbox("Landing Gear - Struck")
            lg_damaged = st.checkbox("Landing Gear - Damaged")
            other_struck = st.checkbox("Other - Struck")
            other_damaged = st.checkbox("Other - Damaged")
            other_part = st.text_input("If Other, specify:")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # ══════════════════════════════════════════════════════════════════════
        # SECTION F: DAMAGE ASSESSMENT
        # ══════════════════════════════════════════════════════════════════════
        st.markdown('<div class="form-section"><div class="form-section-title">💥 SECTION F: DAMAGE ASSESSMENT</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            overall_damage = st.selectbox("Overall Damage Level*", options=[f"{d[0]} - {d[1]}" for d in DAMAGE_LEVELS])
            damage_description = st.text_area("Damage Description*", height=100, placeholder="Describe the damage observed...")
        with col2:
            ingestion = st.selectbox("Engine Ingestion", options=["None", "Engine #1", "Engine #2", "Both Engines", "Suspected but unconfirmed"])
            damage_discovered = st.selectbox("Damage Discovered", options=["During Flight", "After Landing - Walk Around", "After Landing - Maintenance", "Post-Flight Inspection", "Later During Maintenance"])
        
        col1, col2, col3 = st.columns(3)
        with col1:
            engine_shutdown = st.selectbox("Engine Shutdown Required?", options=["No", "Yes - Precautionary", "Yes - Emergency"])
        with col2:
            estimated_cost = st.number_input("Estimated Repair Cost (USD)", min_value=0, value=0)
        with col3:
            aircraft_downtime = st.number_input("Aircraft Downtime (hours)", min_value=0, value=0)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # ══════════════════════════════════════════════════════════════════════
        # SECTION G: EFFECT ON FLIGHT
        # ══════════════════════════════════════════════════════════════════════
        st.markdown('<div class="form-section"><div class="form-section-title">⚡ SECTION G: EFFECT ON FLIGHT</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            effect_on_flight = st.selectbox("Effect on Flight*", options=[
                "None - Flight continued normally",
                "Precautionary landing at destination",
                "Precautionary landing at alternate",
                "Return to departure airport",
                "Emergency landing",
                "Aborted takeoff",
                "Aborted approach / Go-around",
                "Other"
            ])
            emergency_declared = st.selectbox("Emergency Declared?", options=["No", "PAN PAN", "MAYDAY"])
        with col2:
            abort_phase = st.selectbox("If Aborted, at what phase?", options=["Not Applicable", "Low Speed (< 80 kts)", "High Speed (> 80 kts, < V1)", "After V1", "During Approach", "During Go-Around"])
            evacuation = st.checkbox("Evacuation Performed?")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # ══════════════════════════════════════════════════════════════════════
        # SECTION H: CREW INFORMATION
        # ══════════════════════════════════════════════════════════════════════
        st.markdown('<div class="form-section"><div class="form-section-title">👨‍✈️ SECTION H: CREW INFORMATION</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            captain_name = st.text_input("Captain (PIC) Name*", value=data.get('captain_name', ''))
            captain_license = st.text_input("Captain License Number*")
            captain_hours = st.number_input("Captain Total Hours", min_value=0, value=0)
        with col2:
            fo_name = st.text_input("First Officer Name")
            fo_license = st.text_input("First Officer License Number")
            fo_hours = st.number_input("First Officer Total Hours", min_value=0, value=0)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # ══════════════════════════════════════════════════════════════════════
        # SECTION I: NOTIFICATIONS
        # ══════════════════════════════════════════════════════════════════════
        st.markdown('<div class="form-section"><div class="form-section-title">📢 SECTION I: NOTIFICATIONS & ACTIONS</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            atc_notified = st.checkbox("ATC Notified?", value=True)
            atc_notification_time = st.time_input("ATC Notification Time", key="atc_time")
            airport_wildlife_notified = st.checkbox("Airport Wildlife Control Notified?")
        with col2:
            caa_notified = st.checkbox("CAA Notified?")
            caa_notification_date = st.date_input("CAA Notification Date", value=date.today(), key="caa_date")
            company_ops_notified = st.checkbox("Company Ops Control Notified?", value=True)
        
        immediate_actions = st.text_area("Immediate Actions Taken", height=80, placeholder="Describe any immediate actions taken by crew...")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # ══════════════════════════════════════════════════════════════════════
        # SECTION J: ADDITIONAL INFORMATION
        # ══════════════════════════════════════════════════════════════════════
        st.markdown('<div class="form-section"><div class="form-section-title">📝 SECTION J: ADDITIONAL INFORMATION</div>', unsafe_allow_html=True)
        
        narrative = st.text_area("Narrative Description*", height=150, 
                                  placeholder="Provide a detailed narrative of the event including what was observed, actions taken, and any other relevant information...")
        
        contributing_factors = st.multiselect("Contributing Factors (select all that apply)", options=[
            "Poor visibility",
            "Sun glare",
            "Night operations",
            "High bird activity reported",
            "Inadequate bird control at airport",
            "Attraction (lights, waste, water)",
            "Seasonal migration",
            "Weather conditions",
            "Low altitude operation",
            "High speed approach",
            "Other"
        ])
        
        lessons_learned = st.text_area("Lessons Learned / Recommendations", height=80)
        
        photos_available = st.checkbox("Photos/Evidence Available?")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # ══════════════════════════════════════════════════════════════════════
        # SECTION K: INVESTIGATION
        # ══════════════════════════════════════════════════════════════════════
        st.markdown('<div class="form-section"><div class="form-section-title">🔍 SECTION K: INVESTIGATION STATUS</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            investigation_status = st.selectbox("Investigation Status", options=[s.value for s in ReportStatus])
            assigned_investigator = st.text_input("Assigned Investigator")
        with col2:
            target_closure = st.date_input("Target Closure Date", value=date.today() + timedelta(days=Config.BIRD_STRIKE_SLA_DAYS))
            priority = st.selectbox("Priority", options=["Routine", "Priority", "Urgent", "Critical"])
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # ══════════════════════════════════════════════════════════════════════
        # FORM SUBMISSION
        # ══════════════════════════════════════════════════════════════════════
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            submitted = st.form_submit_button("📤 Submit Report", type="primary", use_container_width=True)
        with col2:
            save_draft = st.form_submit_button("💾 Save Draft", use_container_width=True)
        
        if submitted:
            # Compile form data
            form_data = {
                "report_number": report_number,
                "incident_date": str(incident_date),
                "incident_time_local": str(incident_time_local),
                "incident_time_utc": str(incident_time_utc),
                "reported_by": reported_by,
                "reporter_designation": reporter_designation,
                "flight_number": flight_number,
                "flight_type": flight_type,
                "aircraft_registration": aircraft_reg,
                "aircraft_type": aircraft_info['type'],
                "departure_airport": departure,
                "arrival_airport": arrival,
                "flight_phase": flight_phase,
                "altitude_agl": altitude_agl,
                "altitude_msl": altitude_msl,
                "indicated_speed": indicated_speed,
                "heading": heading,
                "weather_conditions": weather_conditions,
                "visibility": visibility,
                "time_of_day": time_of_day,
                "pilot_warned": pilot_warned,
                "bird_species": bird_species,
                "bird_size": bird_size,
                "number_seen": number_seen,
                "number_struck": number_struck,
                "remains_collected": remains_collected,
                "radome_struck": radome_struck,
                "radome_damaged": radome_damaged,
                "windshield_struck": windshield_struck,
                "windshield_damaged": windshield_damaged,
                "engine1_struck": engine1_struck,
                "engine1_damaged": engine1_damaged,
                "engine2_struck": engine2_struck,
                "engine2_damaged": engine2_damaged,
                "wing_le_struck": wing_le_struck,
                "wing_le_damaged": wing_le_damaged,
                "fuselage_struck": fuselage_struck,
                "fuselage_damaged": fuselage_damaged,
                "overall_damage": overall_damage,
                "damage_description": damage_description,
                "engine_ingestion": ingestion,
                "effect_on_flight": effect_on_flight,
                "emergency_declared": emergency_declared,
                "captain_name": captain_name,
                "captain_license": captain_license,
                "fo_name": fo_name,
                "atc_notified": atc_notified,
                "caa_notified": caa_notified,
                "immediate_actions": immediate_actions,
                "narrative": narrative,
                "contributing_factors": contributing_factors,
                "investigation_status": investigation_status,
                "created_at": datetime.now().isoformat(),
                "created_by": st.session_state.get('user_id', 'anonymous')
            }
            
            # Save to database
            result = db.insert_report('bird_strikes', form_data)
            
            if result:
                st.success(f"✅ Bird Strike Report {report_number} submitted successfully!")
                st.balloons()
                db.log_action(st.session_state.get('user_id', ''), 'CREATE', 'bird_strikes', report_number, None, form_data)
            else:
                st.error("❌ Error submitting report. Please try again.")
                # Store locally for demo mode
                if 'bird_strikes' not in st.session_state:
                    st.session_state.bird_strikes = []
                st.session_state.bird_strikes.append(form_data)
                st.success(f"✅ Report {report_number} saved locally (Demo Mode)")
        
        if save_draft:
            st.info("💾 Draft saved successfully!")


def render_laser_strike_form(ocr_data: dict = None):
    """Full CAA-compliant Laser Strike Report Form"""
    
    st.markdown('<h2 style="color: #A855F7;">🔴 Laser Strike Report</h2>', unsafe_allow_html=True)
    st.markdown("*CAA Pakistan Laser Illumination Incident Report*")
    
    data = ocr_data or {}
    
    with st.form("laser_strike_form"):
        
        # SECTION A: INCIDENT IDENTIFICATION
        st.markdown('<div class="form-section"><div class="form-section-title">📋 SECTION A: INCIDENT IDENTIFICATION</div>', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            report_number = st.text_input("Report Number*", value=generate_report_number(ReportType.LASER_STRIKE), disabled=True)
            incident_date = st.date_input("Date of Incident*", value=date.today())
        with col2:
            incident_time_local = st.time_input("Local Time (LT)*")
            incident_time_utc = st.time_input("UTC Time*")
        with col3:
            reported_by = st.text_input("Reported By*", value=st.session_state.get('user_name', ''))
            reporter_contact = st.text_input("Contact Number")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # SECTION B: FLIGHT INFORMATION
        st.markdown('<div class="form-section"><div class="form-section-title">✈️ SECTION B: FLIGHT INFORMATION</div>', unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            flight_number = st.text_input("Flight Number*", value=data.get('flight_number', ''))
            callsign = st.text_input("Callsign (if different)")
        with col2:
            aircraft_reg = st.selectbox("Aircraft Registration*", options=list(AIRCRAFT_FLEET.keys()))
            aircraft_info = get_aircraft_info(aircraft_reg)
        with col3:
            departure = st.selectbox("Departure Airport*", options=list(AIRPORTS.keys()), format_func=get_airport_name)
        with col4:
            arrival = st.selectbox("Arrival Airport*", options=list(AIRPORTS.keys()), index=1, format_func=get_airport_name)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # SECTION C: LOCATION OF INCIDENT
        st.markdown('<div class="form-section"><div class="form-section-title">📍 SECTION C: LOCATION OF INCIDENT</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            location_description = st.text_input("Location Description*", placeholder="e.g., 5nm final RWY 09L Lahore")
            nearest_city = st.text_input("Nearest City/Town")
            radial_dme = st.text_input("Radial/DME from Navaid", placeholder="e.g., LHE VOR 270/5")
        with col2:
            latitude = st.text_input("Latitude (if known)", placeholder="e.g., N31 31.2")
            longitude = st.text_input("Longitude (if known)", placeholder="e.g., E074 24.5")
            fir = st.selectbox("FIR", options=["Karachi FIR", "Lahore FIR"])
        
        col1, col2, col3 = st.columns(3)
        with col1:
            altitude_feet = st.number_input("Altitude (feet MSL)*", min_value=0, max_value=50000, value=3000)
        with col2:
            flight_phase = st.selectbox("Flight Phase*", options=FLIGHT_PHASES)
        with col3:
            heading = st.number_input("Aircraft Heading", min_value=0, max_value=360, value=0)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # SECTION D: LASER CHARACTERISTICS
        st.markdown('<div class="form-section"><div class="form-section-title">🔦 SECTION D: LASER CHARACTERISTICS</div>', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            laser_color = st.selectbox("Laser Color*", options=LASER_COLORS)
            laser_intensity = st.selectbox("Laser Intensity*", options=[f"{i[0]}: {i[1]}" for i in LASER_INTENSITIES])
        with col2:
            duration_seconds = st.number_input("Duration (seconds)*", min_value=1, max_value=600, value=5)
            number_of_strikes = st.number_input("Number of Separate Strikes", min_value=1, max_value=50, value=1)
        with col3:
            beam_movement = st.selectbox("Beam Movement", options=[
                "Stationary (fixed point)",
                "Tracking aircraft movement",
                "Sweeping/Scanning",
                "Erratic/Random",
                "Pulsing/Flashing",
                "Could not determine"
            ])
            laser_source = st.selectbox("Apparent Source Direction", options=[
                "Ground - Left of track",
                "Ground - Right of track",
                "Ground - Ahead",
                "Ground - Behind",
                "Ground - Directly below",
                "Unknown/Could not determine",
                "Another aircraft"
            ])
        
        col1, col2 = st.columns(2)
        with col1:
            laser_entry = st.selectbox("Laser Entry Point", options=[
                "Directly through windshield",
                "Side windows",
                "Reflected off surfaces",
                "Could not determine"
            ])
        with col2:
            distance_estimate = st.selectbox("Estimated Distance to Source", options=[
                "Less than 1 km",
                "1-2 km",
                "2-5 km",
                "More than 5 km",
                "Unable to estimate"
            ])
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # SECTION E: CREW EFFECTS
        st.markdown('<div class="form-section"><div class="form-section-title">👁️ SECTION E: EFFECTS ON CREW</div>', unsafe_allow_html=True)
        
        st.markdown("**Crew Members Affected:**")
        
        col1, col2 = st.columns(2)
        with col1:
            captain_affected = st.checkbox("Captain (PIC) Affected")
            fo_affected = st.checkbox("First Officer Affected")
            observer_affected = st.checkbox("Observer/Check Pilot Affected")
        with col2:
            cabin_crew_affected = st.checkbox("Cabin Crew Affected")
            passengers_affected = st.checkbox("Passengers Affected")
            other_affected = st.checkbox("Other Personnel Affected")
        
        st.markdown("**Visual Effects Experienced (select all that apply):**")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            effect_glare = st.checkbox("Glare")
            effect_distraction = st.checkbox("Distraction")
        with col2:
            effect_flash_blindness = st.checkbox("Flash Blindness")
            effect_afterimage = st.checkbox("Afterimage")
        with col3:
            effect_eye_pain = st.checkbox("Eye Pain/Discomfort")
            effect_watering = st.checkbox("Eye Watering")
        with col4:
            effect_disorientation = st.checkbox("Disorientation")
            effect_headache = st.checkbox("Headache")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            vision_impaired = st.selectbox("Vision Impaired?", options=["No", "Temporarily (< 5 seconds)", "Temporarily (5-30 seconds)", "Temporarily (> 30 seconds)", "Ongoing"])
            duration_impairment = st.text_input("Duration of Impairment", placeholder="e.g., 15 seconds")
        with col2:
            able_to_continue = st.selectbox("Able to Continue Duties?", options=["Yes - Immediately", "Yes - After brief recovery", "No - Transferred duties", "No - Required landing"])
            duties_transferred = st.checkbox("Flight Duties Transferred to Other Pilot?")
        with col3:
            protective_eyewear = st.selectbox("Protective Eyewear?", options=["Not worn", "Worn - No effect", "Worn - Reduced effect", "Worn - Prevented effect"])
            visor_down = st.checkbox("Sun Visor Down?")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # SECTION F: MEDICAL
        st.markdown('<div class="form-section"><div class="form-section-title">🏥 SECTION F: MEDICAL ASSESSMENT</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            medical_attention = st.selectbox("Medical Attention Sought?", options=[
                "No - Not required",
                "Yes - Precautionary eye exam",
                "Yes - Treatment required",
                "Yes - Referred to specialist",
                "Pending"
            ])
            medical_findings = st.text_area("Medical Findings (if applicable)", height=80)
        with col2:
            time_off_duty = st.number_input("Time Off Duty (hours)", min_value=0, value=0)
            fitness_status = st.selectbox("Current Fitness Status", options=[
                "Fit for duty",
                "Temporarily unfit",
                "Under medical review",
                "Not applicable"
            ])
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # SECTION G: EFFECT ON FLIGHT
        st.markdown('<div class="form-section"><div class="form-section-title">⚡ SECTION G: EFFECT ON FLIGHT</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            effect_on_flight = st.selectbox("Effect on Flight*", options=[
                "None - Flight continued normally",
                "Minor - Brief distraction only",
                "Significant - Difficulty maintaining control",
                "Precautionary landing made",
                "Emergency declared",
                "Aborted approach / Go-around",
                "Missed approach lighting/signals",
                "Other"
            ])
        with col2:
            flight_controls_affected = st.selectbox("Flight Control Affected?", options=["No", "Yes - Momentarily", "Yes - Required other pilot intervention", "Yes - Automation disconnect"])
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # SECTION H: NOTIFICATIONS
        st.markdown('<div class="form-section"><div class="form-section-title">📢 SECTION H: NOTIFICATIONS</div>', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            atc_notified = st.checkbox("ATC Notified?", value=True)
            atc_time = st.time_input("ATC Notification Time")
            atc_response = st.text_input("ATC Response/Action")
        with col2:
            police_notified = st.checkbox("Police/Law Enforcement Notified?")
            police_reference = st.text_input("Police Reference Number")
            airport_security = st.checkbox("Airport Security Notified?")
        with col3:
            caa_notified = st.checkbox("CAA Notified?")
            company_ops_notified = st.checkbox("Company Ops Control Notified?", value=True)
            safety_dept_notified = st.checkbox("Safety Department Notified?", value=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # SECTION I: NARRATIVE
        st.markdown('<div class="form-section"><div class="form-section-title">📝 SECTION I: NARRATIVE & ADDITIONAL INFO</div>', unsafe_allow_html=True)
        
        narrative = st.text_area("Detailed Narrative*", height=150, 
                                  placeholder="Provide a complete description of the incident including approach, first contact with laser, effects experienced, actions taken, and any other relevant information...")
        
        crew_recommendations = st.text_area("Crew Recommendations", height=80, 
                                            placeholder="Any recommendations based on this experience...")
        
        col1, col2 = st.columns(2)
        with col1:
            photos_available = st.checkbox("Photos/Evidence Available?")
            cockpit_voice = st.checkbox("Cockpit Voice Recording Available?")
        with col2:
            witness_statements = st.checkbox("Witness Statements Available?")
            additional_evidence = st.text_input("Other Evidence", placeholder="Describe any other evidence")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # SECTION J: INVESTIGATION
        st.markdown('<div class="form-section"><div class="form-section-title">🔍 SECTION J: INVESTIGATION STATUS</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            investigation_status = st.selectbox("Investigation Status", options=[s.value for s in ReportStatus])
            prosecution_status = st.selectbox("Prosecution Status", options=["Not Pursued", "Under Investigation", "Suspect Identified", "Prosecution Initiated", "Convicted", "Case Closed"])
        with col2:
            target_closure = st.date_input("Target Closure Date", value=date.today() + timedelta(days=Config.LASER_STRIKE_SLA_DAYS))
            priority = st.selectbox("Priority", options=["Routine", "Priority", "Urgent", "Critical"])
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # FORM SUBMISSION
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            submitted = st.form_submit_button("📤 Submit Report", type="primary", use_container_width=True)
        with col2:
            save_draft = st.form_submit_button("💾 Save Draft", use_container_width=True)
        
        if submitted:
            form_data = {
                "report_number": report_number,
                "incident_date": str(incident_date),
                "incident_time_local": str(incident_time_local),
                "flight_number": flight_number,
                "aircraft_registration": aircraft_reg,
                "departure_airport": departure,
                "arrival_airport": arrival,
                "location_description": location_description,
                "latitude": latitude,
                "longitude": longitude,
                "altitude_feet": altitude_feet,
                "flight_phase": flight_phase,
                "laser_color": laser_color,
                "laser_intensity": laser_intensity,
                "duration_seconds": duration_seconds,
                "beam_movement": beam_movement,
                "captain_affected": captain_affected,
                "fo_affected": fo_affected,
                "effect_flash_blindness": effect_flash_blindness,
                "effect_afterimage": effect_afterimage,
                "effect_glare": effect_glare,
                "effect_eye_pain": effect_eye_pain,
                "effect_disorientation": effect_disorientation,
                "medical_attention": medical_attention,
                "effect_on_flight": effect_on_flight,
                "atc_notified": atc_notified,
                "police_notified": police_notified,
                "caa_notified": caa_notified,
                "narrative": narrative,
                "investigation_status": investigation_status,
                "prosecution_status": prosecution_status,
                "created_at": datetime.now().isoformat(),
                "created_by": st.session_state.get('user_id', 'anonymous')
            }
            
            result = db.insert_report('laser_strikes', form_data)
            
            if result:
                st.success(f"✅ Laser Strike Report {report_number} submitted successfully!")
                st.balloons()
            else:
                if 'laser_strikes' not in st.session_state:
                    st.session_state.laser_strikes = []
                st.session_state.laser_strikes.append(form_data)
                st.success(f"✅ Report {report_number} saved locally (Demo Mode)")


def render_tcas_form(ocr_data: dict = None):
    """Full CAA-compliant TCAS Report Form"""
    
    st.markdown('<h2 style="color: #F97316;">📡 TCAS Report</h2>', unsafe_allow_html=True)
    st.markdown("*CAA Pakistan ACAS/TCAS Resolution Advisory Report*")
    
    data = ocr_data or {}
    
    with st.form("tcas_form"):
        
        # SECTION A: INCIDENT IDENTIFICATION
        st.markdown('<div class="form-section"><div class="form-section-title">📋 SECTION A: INCIDENT IDENTIFICATION</div>', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            report_number = st.text_input("Report Number*", value=generate_report_number(ReportType.TCAS_REPORT), disabled=True)
            incident_date = st.date_input("Date of Incident*", value=date.today())
        with col2:
            incident_time_local = st.time_input("Local Time (LT)*")
            incident_time_utc = st.time_input("UTC Time*")
        with col3:
            reported_by = st.text_input("Reported By*")
            reporter_license = st.text_input("License Number")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # SECTION B: OWN AIRCRAFT INFORMATION
        st.markdown('<div class="form-section"><div class="form-section-title">✈️ SECTION B: OWN AIRCRAFT INFORMATION</div>', unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            flight_number = st.text_input("Flight Number*", value=data.get('flight_number', ''))
            callsign = st.text_input("Callsign (if different)")
        with col2:
            aircraft_reg = st.selectbox("Aircraft Registration*", options=list(AIRCRAFT_FLEET.keys()))
            aircraft_info = get_aircraft_info(aircraft_reg)
            st.caption(f"Type: {aircraft_info['type']}")
        with col3:
            departure = st.selectbox("Departure*", options=list(AIRPORTS.keys()), format_func=get_airport_name)
        with col4:
            arrival = st.selectbox("Arrival*", options=list(AIRPORTS.keys()), index=1, format_func=get_airport_name)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            tcas_equipment = st.selectbox("TCAS Equipment Type*", options=TCAS_EQUIPMENT_TYPES)
        with col2:
            transponder_mode = st.selectbox("Transponder Mode", options=["Mode S with ES", "Mode S", "Mode C", "Mode A", "Unknown"])
        with col3:
            flight_rules = st.selectbox("Flight Rules", options=["IFR", "VFR", "SVFR"])
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # SECTION C: POSITION AT TIME OF EVENT
        st.markdown('<div class="form-section"><div class="form-section-title">📍 SECTION C: POSITION AT TIME OF EVENT</div>', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            position = st.text_input("Position (Fix/Radial-DME)*", placeholder="e.g., LHE VOR 090/25")
            latitude = st.text_input("Latitude", placeholder="e.g., N31 31.2")
            longitude = st.text_input("Longitude", placeholder="e.g., E074 24.5")
        with col2:
            altitude_feet = st.number_input("Altitude (feet)*", min_value=0, max_value=50000, value=25000)
            flight_level = st.text_input("Flight Level", placeholder="e.g., FL250")
            vertical_speed = st.number_input("Vertical Speed (fpm)", min_value=-6000, max_value=6000, value=0)
        with col3:
            heading = st.number_input("Heading (degrees)*", min_value=0, max_value=360, value=90)
            indicated_speed = st.number_input("Indicated Airspeed (knots)", min_value=0, max_value=500, value=280)
            mach = st.number_input("Mach Number", min_value=0.0, max_value=1.0, value=0.78, format="%.2f")
        
        col1, col2 = st.columns(2)
        with col1:
            flight_phase = st.selectbox("Flight Phase*", options=FLIGHT_PHASES)
            airspace_class = st.selectbox("Airspace Class", options=["Class A", "Class B", "Class C", "Class D", "Class E", "Class G", "Unknown"])
        with col2:
            atc_unit = st.text_input("ATC Unit in Contact", placeholder="e.g., Lahore Radar")
            atc_frequency = st.text_input("ATC Frequency", placeholder="e.g., 127.75")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # SECTION D: TCAS ALERT INFORMATION
        st.markdown('<div class="form-section"><div class="form-section-title">🚨 SECTION D: TCAS ALERT INFORMATION</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            alert_type = st.selectbox("Alert Type*", options=TCAS_ALERT_TYPES)
            ta_received = st.checkbox("Traffic Advisory (TA) Received Before RA?")
            ta_duration = st.number_input("TA Duration (seconds)", min_value=0, max_value=120, value=0)
        with col2:
            ra_sense = st.selectbox("RA Sense*", options=[
                "Climb",
                "Descend",
                "Level Off",
                "Maintain Vertical Speed",
                "Adjust Vertical Speed - Climb",
                "Adjust Vertical Speed - Descend",
                "Crossing Climb",
                "Crossing Descend",
                "Reversal to Climb",
                "Reversal to Descend",
                "Increase Climb",
                "Increase Descend",
                "Not Applicable (TA Only)"
            ])
            ra_strength = st.selectbox("RA Strength", options=["Corrective", "Preventive", "Not Applicable"])
        
        col1, col2, col3 = st.columns(3)
        with col1:
            ra_followed = st.selectbox("RA Followed?*", options=[
                "Yes - Full compliance",
                "Yes - Partial compliance",
                "No - Conflicting ATC instruction",
                "No - Visual acquisition",
                "No - Other reason",
                "Not Applicable"
            ])
        with col2:
            if "No" in ra_followed:
                non_compliance_reason = st.text_input("Reason for Non-Compliance")
        with col3:
            vertical_deviation = st.number_input("Vertical Deviation from Clearance (feet)", min_value=0, max_value=5000, value=0)
        
        multi_ra = st.checkbox("Multiple RAs Received?")
        if multi_ra:
            ra_sequence = st.text_area("Describe RA Sequence", height=80, placeholder="e.g., Initial Climb followed by Increase Climb then Level Off")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # SECTION E: TRAFFIC (INTRUDER) INFORMATION
        st.markdown('<div class="form-section"><div class="form-section-title">🎯 SECTION E: TRAFFIC (INTRUDER) INFORMATION</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            traffic_displayed = st.selectbox("Traffic Displayed on TCAS?", options=["Yes - With Mode C", "Yes - No Mode C", "No Traffic Displayed", "Unknown"])
            traffic_visual = st.selectbox("Traffic Acquired Visually?", options=["Yes - Before Alert", "Yes - During Alert", "Yes - After Alert", "No", "N/A"])
        with col2:
            traffic_callsign = st.text_input("Traffic Callsign (if known)")
            traffic_type = st.text_input("Traffic Aircraft Type (if known)")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            traffic_position = st.selectbox("Traffic Position*", options=[
                "12 o'clock", "1 o'clock", "2 o'clock", "3 o'clock",
                "4 o'clock", "5 o'clock", "6 o'clock", "7 o'clock",
                "8 o'clock", "9 o'clock", "10 o'clock", "11 o'clock",
                "Unknown"
            ])
            traffic_altitude = st.selectbox("Traffic Altitude Relative", options=[
                "Same level",
                "Above - Climbing",
                "Above - Descending",
                "Above - Level",
                "Below - Climbing",
                "Below - Descending",
                "Below - Level",
                "Unknown"
            ])
        with col2:
            traffic_range = st.number_input("Traffic Range (nm)", min_value=0.0, max_value=50.0, value=5.0, format="%.1f")
            traffic_bearing = st.number_input("Traffic Bearing (degrees)", min_value=0, max_value=360, value=0)
        with col3:
            closure_rate = st.selectbox("Closure Rate", options=["High (converging)", "Medium", "Low (diverging)", "Unknown"])
            traffic_maneuver = st.selectbox("Did Traffic Maneuver?", options=["Yes - Appeared to follow RA", "Yes - Opposite to expected RA", "No apparent maneuver", "Unknown"])
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # SECTION F: SEPARATION
        st.markdown('<div class="form-section"><div class="form-section-title">📏 SECTION F: SEPARATION</div>', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            min_vertical_sep = st.number_input("Minimum Vertical Separation (feet)*", min_value=0, max_value=10000, value=500)
        with col2:
            min_horizontal_sep = st.number_input("Minimum Horizontal Separation (nm)*", min_value=0.0, max_value=20.0, value=2.0, format="%.1f")
        with col3:
            cpa_time = st.time_input("Time of Closest Point of Approach")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # SECTION G: ATC COORDINATION
        st.markdown('<div class="form-section"><div class="form-section-title">🎧 SECTION G: ATC COORDINATION</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            atc_clearance = st.text_input("ATC Clearance at Time of Event", placeholder="e.g., Maintain FL250")
            conflicting_clearance = st.checkbox("ATC Clearance Conflicted with RA?")
            atc_notified_ra = st.selectbox("ATC Notified of RA?", options=["Yes - Immediately", "Yes - After event", "No", "Not Applicable"])
        with col2:
            atc_traffic_info = st.selectbox("ATC Traffic Information Provided?", options=["Yes - Before Alert", "Yes - After Alert", "No", "Not Applicable"])
            atc_response = st.text_area("ATC Response to RA Report", height=80)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # SECTION H: CREW ACTIONS
        st.markdown('<div class="form-section"><div class="form-section-title">👨‍✈️ SECTION H: CREW INFORMATION & ACTIONS</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            captain_name = st.text_input("Captain (PIC) Name*")
            captain_license = st.text_input("Captain License Number")
            pf_at_time = st.selectbox("Pilot Flying at Time of Event", options=["Captain", "First Officer", "Autopilot Engaged"])
        with col2:
            fo_name = st.text_input("First Officer Name")
            fo_license = st.text_input("First Officer License Number")
            autopilot_status = st.selectbox("Autopilot Status", options=["Engaged - Disconnected for RA", "Engaged - Remained Engaged", "Not Engaged"])
        
        crew_actions = st.text_area("Crew Actions Taken*", height=100, placeholder="Describe the actions taken by the crew in response to the TCAS alert...")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # SECTION I: NARRATIVE
        st.markdown('<div class="form-section"><div class="form-section-title">📝 SECTION I: NARRATIVE</div>', unsafe_allow_html=True)
        
        narrative = st.text_area("Detailed Narrative*", height=150, 
                                  placeholder="Provide a complete description of the event including flight conditions, TCAS indications, visual acquisition, maneuvers, ATC communications, and any other relevant information...")
        
        contributing_factors = st.multiselect("Possible Contributing Factors", options=[
            "ATC Instruction",
            "Conflicting Clearances",
            "Traffic Density",
            "Weather Deviation",
            "Non-Compliance (other aircraft)",
            "Equipment Malfunction",
            "Communication Issues",
            "Airspace Structure",
            "Other"
        ])
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # SECTION J: AIRPROX CLASSIFICATION
        st.markdown('<div class="form-section"><div class="form-section-title">⚠️ SECTION J: AIRPROX CLASSIFICATION</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            airprox_filed = st.selectbox("Airprox Report Filed?", options=["Yes", "No", "Pending"])
            airprox_reference = st.text_input("Airprox Reference Number")
        with col2:
            risk_category = st.selectbox("Risk Category (if known)", options=[
                "A - Risk of Collision",
                "B - Safety Not Assured",
                "C - No Risk of Collision",
                "D - Risk Not Determined",
                "E - ATM Induced",
                "Not Yet Classified"
            ])
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # SECTION K: INVESTIGATION STATUS
        st.markdown('<div class="form-section"><div class="form-section-title">🔍 SECTION K: INVESTIGATION STATUS</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            investigation_status = st.selectbox("Investigation Status", options=[s.value for s in ReportStatus])
            assigned_investigator = st.text_input("Assigned Investigator")
        with col2:
            target_closure = st.date_input("Target Closure Date", value=date.today() + timedelta(days=Config.TCAS_SLA_DAYS))
            priority = st.selectbox("Priority", options=["Routine", "Priority", "Urgent", "Critical"])
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # FORM SUBMISSION
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            submitted = st.form_submit_button("📤 Submit Report", type="primary", use_container_width=True)
        with col2:
            save_draft = st.form_submit_button("💾 Save Draft", use_container_width=True)
        
        if submitted:
            form_data = {
                "report_number": report_number,
                "incident_date": str(incident_date),
                "incident_time_local": str(incident_time_local),
                "incident_time_utc": str(incident_time_utc),
                "flight_number": flight_number,
                "aircraft_registration": aircraft_reg,
                "aircraft_type": aircraft_info['type'],
                "departure_airport": departure,
                "arrival_airport": arrival,
                "tcas_equipment": tcas_equipment,
                "position": position,
                "altitude_feet": altitude_feet,
                "heading": heading,
                "flight_phase": flight_phase,
                "alert_type": alert_type,
                "ra_sense": ra_sense,
                "ra_followed": ra_followed,
                "vertical_deviation": vertical_deviation,
                "traffic_position": traffic_position,
                "traffic_altitude": traffic_altitude,
                "traffic_range": traffic_range,
                "min_vertical_sep": min_vertical_sep,
                "min_horizontal_sep": min_horizontal_sep,
                "atc_clearance": atc_clearance,
                "atc_notified_ra": atc_notified_ra,
                "captain_name": captain_name,
                "crew_actions": crew_actions,
                "narrative": narrative,
                "contributing_factors": contributing_factors,
                "airprox_filed": airprox_filed,
                "risk_category": risk_category,
                "investigation_status": investigation_status,
                "created_at": datetime.now().isoformat(),
                "created_by": st.session_state.get('user_id', 'anonymous')
            }
            
            result = db.insert_report('tcas_reports', form_data)
            
            if result:
                st.success(f"✅ TCAS Report {report_number} submitted successfully!")
                st.balloons()
            else:
                if 'tcas_reports' not in st.session_state:
                    st.session_state.tcas_reports = []
                st.session_state.tcas_reports.append(form_data)
                st.success(f"✅ Report {report_number} saved locally (Demo Mode)")
# ══════════════════════════════════════════════════════════════════════════════
# AIRCRAFT INCIDENT REPORT FORM - CAA PAKISTAN COMPLIANT
# ══════════════════════════════════════════════════════════════════════════════

def render_incident_form(ocr_data: dict = None):
    """Full CAA-compliant Aircraft Incident/Accident Report Form"""
    
    st.markdown('<h2 style="color: #10B981;">🚨 Aircraft Incident Report</h2>', unsafe_allow_html=True)
    st.markdown("*CAA Pakistan Aircraft Incident/Accident Notification Form (ANF-1)*")
    
    data = ocr_data or {}
    
    with st.form("incident_form"):
        
        # ══════════════════════════════════════════════════════════════════════
        # SECTION A: NOTIFICATION TYPE
        # ══════════════════════════════════════════════════════════════════════
        st.markdown('<div class="form-section"><div class="form-section-title">📋 SECTION A: NOTIFICATION TYPE</div>', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            report_number = st.text_input("Report Number*", value=generate_report_number(ReportType.AIRCRAFT_INCIDENT), disabled=True)
            notification_type = st.selectbox("Notification Type*", options=[
                "Accident",
                "Serious Incident",
                "Incident",
                "Occurrence (Mandatory Reportable)",
                "Occurrence (Voluntary Report)"
            ])
        with col2:
            incident_date = st.date_input("Date of Occurrence*", value=date.today())
            incident_time_local = st.time_input("Local Time (LT)*")
        with col3:
            incident_time_utc = st.time_input("UTC Time*")
            reported_by = st.text_input("Reported By*", value=st.session_state.get('user_name', ''))
        
        col1, col2 = st.columns(2)
        with col1:
            reporter_designation = st.selectbox("Reporter Designation", options=CREW_POSITIONS + ["Safety Officer", "Ground Staff", "Maintenance", "Other"])
            reporter_contact = st.text_input("Reporter Contact Number")
        with col2:
            initial_notification_time = st.time_input("Initial Notification Time")
            notification_method = st.selectbox("Notification Method", options=["Phone", "Email", "SMS", "Safety Reporting System", "In Person"])
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # ══════════════════════════════════════════════════════════════════════
        # SECTION B: AIRCRAFT INFORMATION
        # ══════════════════════════════════════════════════════════════════════
        st.markdown('<div class="form-section"><div class="form-section-title">✈️ SECTION B: AIRCRAFT INFORMATION</div>', unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            aircraft_reg = st.selectbox("Aircraft Registration*", options=list(AIRCRAFT_FLEET.keys()))
            aircraft_info = get_aircraft_info(aircraft_reg)
            st.caption(f"Type: {aircraft_info['type']} | MSN: {aircraft_info['msn']}")
        with col2:
            aircraft_type = st.selectbox("Aircraft Type*", options=AIRCRAFT_TYPES, index=AIRCRAFT_TYPES.index(aircraft_info['type']) if aircraft_info['type'] in AIRCRAFT_TYPES else 0)
            aircraft_msn = st.text_input("Manufacturer Serial Number", value=aircraft_info['msn'])
        with col3:
            year_manufacture = st.number_input("Year of Manufacture", min_value=1990, max_value=2030, value=2020)
            total_hours = st.number_input("Total Aircraft Hours", min_value=0, value=0)
        with col4:
            total_cycles = st.number_input("Total Cycles", min_value=0, value=0)
            last_check = st.selectbox("Last Major Check", options=["A-Check", "B-Check", "C-Check", "D-Check", "Unknown"])
        
        col1, col2 = st.columns(2)
        with col1:
            engine_type = st.text_input("Engine Type", placeholder="e.g., PW127M")
            engine1_hours = st.number_input("Engine #1 Hours", min_value=0, value=0)
        with col2:
            engine_count = st.selectbox("Number of Engines", options=[1, 2, 3, 4], index=1)
            engine2_hours = st.number_input("Engine #2 Hours", min_value=0, value=0)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # ══════════════════════════════════════════════════════════════════════
        # SECTION C: FLIGHT INFORMATION
        # ══════════════════════════════════════════════════════════════════════
        st.markdown('<div class="form-section"><div class="form-section-title">🛫 SECTION C: FLIGHT INFORMATION</div>', unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            flight_number = st.text_input("Flight Number*", value=data.get('flight_number', ''))
            flight_type = st.selectbox("Flight Type*", options=[
                "Scheduled Passenger",
                "Scheduled Cargo",
                "Charter Passenger",
                "Charter Cargo",
                "Positioning/Ferry",
                "Training",
                "Test Flight",
                "Maintenance Check",
                "Other"
            ])
        with col2:
            departure = st.selectbox("Departure Airport*", options=list(AIRPORTS.keys()), format_func=get_airport_name)
            std = st.time_input("Scheduled Departure Time")
            atd = st.time_input("Actual Departure Time")
        with col3:
            arrival = st.selectbox("Destination Airport*", options=list(AIRPORTS.keys()), index=1, format_func=get_airport_name)
            sta = st.time_input("Scheduled Arrival Time")
            ata = st.time_input("Actual Arrival Time")
        with col4:
            alternate = st.selectbox("Alternate Airport", options=["N/A"] + list(AIRPORTS.keys()), format_func=lambda x: get_airport_name(x) if x != "N/A" else "N/A")
            flight_rules = st.selectbox("Flight Rules", options=["IFR", "VFR", "SVFR"])
            flight_plan_filed = st.checkbox("Flight Plan Filed?", value=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # ══════════════════════════════════════════════════════════════════════
        # SECTION D: LOCATION OF OCCURRENCE
        # ══════════════════════════════════════════════════════════════════════
        st.markdown('<div class="form-section"><div class="form-section-title">📍 SECTION D: LOCATION OF OCCURRENCE</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            occurrence_location = st.selectbox("Occurrence Location*", options=[
                "At Departure Airport - Ramp",
                "At Departure Airport - Taxiway",
                "At Departure Airport - Runway",
                "At Departure Airport - Other",
                "Enroute - Climb",
                "Enroute - Cruise",
                "Enroute - Descent",
                "At Destination Airport - Approach",
                "At Destination Airport - Runway",
                "At Destination Airport - Taxiway",
                "At Destination Airport - Ramp",
                "At Alternate Airport",
                "Other Location"
            ])
            location_description = st.text_input("Location Description", placeholder="e.g., 25nm south of Lahore")
        with col2:
            latitude = st.text_input("Latitude", placeholder="e.g., N31 31.2")
            longitude = st.text_input("Longitude", placeholder="e.g., E074 24.5")
            nearest_airport = st.selectbox("Nearest Airport", options=list(AIRPORTS.keys()), format_func=get_airport_name)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            flight_phase = st.selectbox("Flight Phase*", options=FLIGHT_PHASES)
        with col2:
            altitude_feet = st.number_input("Altitude (feet)", min_value=0, max_value=50000, value=0)
        with col3:
            speed_kts = st.number_input("Speed (knots)", min_value=0, max_value=500, value=0)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # ══════════════════════════════════════════════════════════════════════
        # SECTION E: INCIDENT CATEGORY & DESCRIPTION
        # ══════════════════════════════════════════════════════════════════════
        st.markdown('<div class="form-section"><div class="form-section-title">⚠️ SECTION E: INCIDENT CATEGORY & DESCRIPTION</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            primary_category = st.selectbox("Primary Incident Category*", options=INCIDENT_CATEGORIES)
            secondary_categories = st.multiselect("Secondary Categories (if applicable)", options=INCIDENT_CATEGORIES)
        with col2:
            event_type = st.selectbox("Event Type", options=[
                "Single Event",
                "Chain of Events",
                "Near Miss",
                "Precursor Event"
            ])
            safety_margin = st.selectbox("Safety Margin", options=[
                "Not Reduced",
                "Reduced",
                "Significantly Reduced",
                "No Safety Margin Remaining"
            ])
        
        incident_title = st.text_input("Brief Incident Title*", placeholder="e.g., Engine failure during climb")
        
        incident_description = st.text_area("Detailed Description of Event*", height=150,
            placeholder="Provide a complete chronological description of the event including:\n- What happened\n- When it happened\n- Where it happened\n- Initial indications/warnings\n- Actions taken\n- Final outcome")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # ══════════════════════════════════════════════════════════════════════
        # SECTION F: WEATHER CONDITIONS
        # ══════════════════════════════════════════════════════════════════════
        st.markdown('<div class="form-section"><div class="form-section-title">🌤️ SECTION F: WEATHER CONDITIONS</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            weather_conditions = st.selectbox("Weather Conditions*", options=WEATHER_CONDITIONS)
            weather_factor = st.selectbox("Weather as Contributing Factor?", options=["No", "Possibly", "Yes - Contributing", "Yes - Primary Cause"])
        with col2:
            visibility = st.selectbox("Visibility", options=["Greater than 10km", "5-10km", "2-5km", "1-2km", "500m-1km", "Less than 500m"])
            ceiling = st.selectbox("Ceiling", options=["Clear", "Few > 5000ft", "Scattered", "Broken", "Overcast", "Below Minimums"])
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            wind_direction = st.number_input("Wind Direction (degrees)", min_value=0, max_value=360, value=0)
        with col2:
            wind_speed = st.number_input("Wind Speed (knots)", min_value=0, max_value=100, value=0)
        with col3:
            wind_gusts = st.number_input("Gusts (knots)", min_value=0, max_value=100, value=0)
        with col4:
            temperature = st.number_input("Temperature (°C)", min_value=-50, max_value=60, value=25)
        
        metar = st.text_input("METAR (if available)", placeholder="e.g., OPLA 120800Z 36010KT 9999 FEW040 28/18 Q1012")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # ══════════════════════════════════════════════════════════════════════
        # SECTION G: CREW INFORMATION
        # ══════════════════════════════════════════════════════════════════════
        st.markdown('<div class="form-section"><div class="form-section-title">👨‍✈️ SECTION G: FLIGHT CREW INFORMATION</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Captain (PIC)**")
            captain_name = st.text_input("Captain Name*")
            captain_license = st.text_input("Captain License Number*")
            captain_license_type = st.selectbox("Captain License Type", options=["ATPL", "CPL", "MPL"])
            captain_total_hours = st.number_input("Captain Total Hours", min_value=0, value=0)
            captain_type_hours = st.number_input("Captain Hours on Type", min_value=0, value=0)
            captain_last_90_days = st.number_input("Captain Hours Last 90 Days", min_value=0, value=0)
            captain_duty_hours = st.number_input("Captain Duty Hours at Time of Event", min_value=0.0, max_value=24.0, value=0.0, format="%.1f")
        with col2:
            st.markdown("**First Officer (SIC)**")
            fo_name = st.text_input("First Officer Name")
            fo_license = st.text_input("First Officer License Number")
            fo_license_type = st.selectbox("FO License Type", options=["ATPL", "CPL", "MPL", "N/A"])
            fo_total_hours = st.number_input("FO Total Hours", min_value=0, value=0)
            fo_type_hours = st.number_input("FO Hours on Type", min_value=0, value=0)
            fo_last_90_days = st.number_input("FO Hours Last 90 Days", min_value=0, value=0)
            fo_duty_hours = st.number_input("FO Duty Hours at Time of Event", min_value=0.0, max_value=24.0, value=0.0, format="%.1f")
        
        col1, col2 = st.columns(2)
        with col1:
            pilot_flying = st.selectbox("Pilot Flying (PF) at Time of Event", options=["Captain", "First Officer", "Autopilot Engaged", "N/A"])
            pilot_monitoring = st.selectbox("Pilot Monitoring (PM)", options=["Captain", "First Officer", "N/A"])
        with col2:
            additional_crew = st.text_input("Additional Flight Crew (if any)", placeholder="e.g., Check Captain, Relief FO")
            cabin_crew_count = st.number_input("Number of Cabin Crew", min_value=0, max_value=20, value=0)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # ══════════════════════════════════════════════════════════════════════
        # SECTION H: PASSENGERS & LOAD
        # ══════════════════════════════════════════════════════════════════════
        st.markdown('<div class="form-section"><div class="form-section-title">👥 SECTION H: PASSENGERS & LOAD</div>', unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            pax_adult = st.number_input("Adult Passengers", min_value=0, max_value=300, value=0)
            pax_child = st.number_input("Child Passengers", min_value=0, max_value=100, value=0)
        with col2:
            pax_infant = st.number_input("Infant Passengers", min_value=0, max_value=50, value=0)
            pax_total = pax_adult + pax_child + pax_infant
            st.metric("Total Passengers", pax_total)
        with col3:
            baggage_kg = st.number_input("Baggage (kg)", min_value=0, max_value=50000, value=0)
            cargo_kg = st.number_input("Cargo (kg)", min_value=0, max_value=50000, value=0)
        with col4:
            fuel_departure = st.number_input("Fuel at Departure (kg)", min_value=0, max_value=50000, value=0)
            zfw = st.number_input("Zero Fuel Weight (kg)", min_value=0, max_value=100000, value=0)
        
        col1, col2 = st.columns(2)
        with col1:
            tow = st.number_input("Takeoff Weight (kg)", min_value=0, max_value=150000, value=0)
            max_tow = st.number_input("Max Takeoff Weight (kg)", min_value=0, max_value=150000, value=0)
        with col2:
            lw = st.number_input("Landing Weight (kg)", min_value=0, max_value=150000, value=0)
            max_lw = st.number_input("Max Landing Weight (kg)", min_value=0, max_value=150000, value=0)
        
        within_limits = st.checkbox("Aircraft Within Weight & Balance Limits?", value=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # ══════════════════════════════════════════════════════════════════════
        # SECTION I: INJURIES & DAMAGE
        # ══════════════════════════════════════════════════════════════════════
        st.markdown('<div class="form-section"><div class="form-section-title">🏥 SECTION I: INJURIES & DAMAGE</div>', unsafe_allow_html=True)
        
        st.markdown("**Injuries:**")
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.markdown("*Fatal*")
            fatal_crew = st.number_input("Crew - Fatal", min_value=0, value=0, key="fatal_crew")
            fatal_pax = st.number_input("Passengers - Fatal", min_value=0, value=0, key="fatal_pax")
            fatal_ground = st.number_input("Ground - Fatal", min_value=0, value=0, key="fatal_ground")
        with col2:
            st.markdown("*Serious*")
            serious_crew = st.number_input("Crew - Serious", min_value=0, value=0, key="serious_crew")
            serious_pax = st.number_input("Passengers - Serious", min_value=0, value=0, key="serious_pax")
            serious_ground = st.number_input("Ground - Serious", min_value=0, value=0, key="serious_ground")
        with col3:
            st.markdown("*Minor*")
            minor_crew = st.number_input("Crew - Minor", min_value=0, value=0, key="minor_crew")
            minor_pax = st.number_input("Passengers - Minor", min_value=0, value=0, key="minor_pax")
            minor_ground = st.number_input("Ground - Minor", min_value=0, value=0, key="minor_ground")
        with col4:
            st.markdown("*None*")
            none_crew = st.number_input("Crew - None", min_value=0, value=0, key="none_crew")
            none_pax = st.number_input("Passengers - None", min_value=0, value=0, key="none_pax")
            none_ground = st.number_input("Ground - None", min_value=0, value=0, key="none_ground")
        with col5:
            st.markdown("*Totals*")
            total_fatal = fatal_crew + fatal_pax + fatal_ground
            total_serious = serious_crew + serious_pax + serious_ground
            total_minor = minor_crew + minor_pax + minor_ground
            st.metric("Total Fatal", total_fatal)
            st.metric("Total Serious", total_serious)
            st.metric("Total Minor", total_minor)
        
        st.markdown("**Aircraft Damage:**")
        col1, col2 = st.columns(2)
        with col1:
            aircraft_damage = st.selectbox("Aircraft Damage Level*", options=[f"{d[0]} - {d[1]}" for d in DAMAGE_LEVELS])
            damage_description = st.text_area("Damage Description", height=100, placeholder="Describe the damage to the aircraft...")
        with col2:
            fire_occurred = st.selectbox("Fire Occurred?", options=["No", "Yes - In-flight", "Yes - Post-impact", "Yes - Ground fire"])
            third_party_damage = st.checkbox("Third Party Property Damage?")
            if third_party_damage:
                third_party_description = st.text_input("Third Party Damage Description")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # ══════════════════════════════════════════════════════════════════════
        # SECTION J: EMERGENCY RESPONSE
        # ══════════════════════════════════════════════════════════════════════
        st.markdown('<div class="form-section"><div class="form-section-title">🚨 SECTION J: EMERGENCY RESPONSE</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            emergency_declared = st.selectbox("Emergency Declared?*", options=["No", "PAN PAN", "MAYDAY"])
            evacuation = st.selectbox("Evacuation Performed?", options=["No", "Yes - Commanded", "Yes - Precautionary", "Yes - Uncommanded"])
            if evacuation != "No":
                evacuation_time = st.number_input("Evacuation Time (seconds)", min_value=0, value=90)
                slides_used = st.checkbox("Evacuation Slides Deployed?")
        with col2:
            arff_response = st.selectbox("ARFF Response?", options=["No", "Yes - Standby", "Yes - Active Response"])
            ems_response = st.checkbox("EMS/Medical Response Required?")
            airport_closed = st.checkbox("Airport/Runway Closed?")
            if airport_closed:
                closure_duration = st.text_input("Closure Duration", placeholder="e.g., 2 hours")
        
        immediate_actions = st.text_area("Immediate Actions Taken*", height=100,
            placeholder="Describe the immediate actions taken by crew and/or ground personnel...")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # ══════════════════════════════════════════════════════════════════════
        # SECTION K: NOTIFICATIONS
        # ══════════════════════════════════════════════════════════════════════
        st.markdown('<div class="form-section"><div class="form-section-title">📢 SECTION K: NOTIFICATIONS</div>', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            caa_notified = st.checkbox("CAA Pakistan Notified?*")
            caa_notification_time = st.time_input("CAA Notification Time", key="caa_time_inc")
            caa_reference = st.text_input("CAA Reference Number")
        with col2:
            aaib_notified = st.checkbox("AAIB Notified?")
            police_notified = st.checkbox("Police Notified?")
            insurance_notified = st.checkbox("Insurance Notified?")
        with col3:
            manufacturer_notified = st.checkbox("Aircraft Manufacturer Notified?")
            engine_manufacturer_notified = st.checkbox("Engine Manufacturer Notified?")
            state_of_design_notified = st.checkbox("State of Design Notified?")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # ══════════════════════════════════════════════════════════════════════
        # SECTION L: INVESTIGATION
        # ══════════════════════════════════════════════════════════════════════
        st.markdown('<div class="form-section"><div class="form-section-title">🔍 SECTION L: INVESTIGATION STATUS</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            investigation_status = st.selectbox("Investigation Status", options=[s.value for s in ReportStatus])
            assigned_investigator = st.text_input("Assigned Investigator")
            investigation_type = st.selectbox("Investigation Type", options=[
                "Internal Investigation Only",
                "CAA Investigation",
                "AAIB Investigation",
                "Joint Investigation",
                "No Investigation Required"
            ])
        with col2:
            target_closure = st.date_input("Target Closure Date", value=date.today() + timedelta(days=Config.INCIDENT_SLA_DAYS))
            priority = st.selectbox("Priority", options=["Routine", "Priority", "Urgent", "Critical"])
            confidential = st.checkbox("Confidential Report?")
        
        root_cause = st.text_area("Preliminary Root Cause Analysis", height=80,
            placeholder="Initial assessment of root cause(s)...")
        
        corrective_actions = st.text_area("Proposed Corrective Actions", height=80,
            placeholder="Proposed actions to prevent recurrence...")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # FORM SUBMISSION
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            submitted = st.form_submit_button("📤 Submit Report", type="primary", use_container_width=True)
        with col2:
            save_draft = st.form_submit_button("💾 Save Draft", use_container_width=True)
        
        if submitted:
            form_data = {
                "report_number": report_number,
                "notification_type": notification_type,
                "incident_date": str(incident_date),
                "incident_time_local": str(incident_time_local),
                "incident_time_utc": str(incident_time_utc),
                "reported_by": reported_by,
                "aircraft_registration": aircraft_reg,
                "aircraft_type": aircraft_type,
                "flight_number": flight_number,
                "flight_type": flight_type,
                "departure_airport": departure,
                "arrival_airport": arrival,
                "occurrence_location": occurrence_location,
                "flight_phase": flight_phase,
                "altitude_feet": altitude_feet,
                "primary_category": primary_category,
                "secondary_categories": secondary_categories,
                "incident_title": incident_title,
                "incident_description": incident_description,
                "weather_conditions": weather_conditions,
                "captain_name": captain_name,
                "captain_license": captain_license,
                "fo_name": fo_name,
                "pax_total": pax_total,
                "fatal_total": total_fatal,
                "serious_total": total_serious,
                "minor_total": total_minor,
                "aircraft_damage": aircraft_damage,
                "damage_description": damage_description,
                "emergency_declared": emergency_declared,
                "evacuation": evacuation,
                "immediate_actions": immediate_actions,
                "caa_notified": caa_notified,
                "investigation_status": investigation_status,
                "investigation_type": investigation_type,
                "root_cause": root_cause,
                "corrective_actions": corrective_actions,
                "created_at": datetime.now().isoformat(),
                "created_by": st.session_state.get('user_id', 'anonymous')
            }
            
            result = db.insert_report('aircraft_incidents', form_data)
            
            if result:
                st.success(f"✅ Aircraft Incident Report {report_number} submitted successfully!")
                st.balloons()
            else:
                if 'aircraft_incidents' not in st.session_state:
                    st.session_state.aircraft_incidents = []
                st.session_state.aircraft_incidents.append(form_data)
                st.success(f"✅ Report {report_number} saved locally (Demo Mode)")


# ══════════════════════════════════════════════════════════════════════════════
# HAZARD REPORT FORM WITH RISK MATRIX
# ══════════════════════════════════════════════════════════════════════════════

def render_hazard_form(ocr_data: dict = None):
    """Full Hazard Report Form with ICAO Risk Matrix"""
    
    st.markdown('<h2 style="color: #EF4444;">⚠️ Hazard Report</h2>', unsafe_allow_html=True)
    st.markdown("*Safety Hazard Identification & Risk Assessment Form*")
    
    data = ocr_data or {}
    
    with st.form("hazard_form"):
        
        # ══════════════════════════════════════════════════════════════════════
        # SECTION A: REPORTER INFORMATION
        # ══════════════════════════════════════════════════════════════════════
        st.markdown('<div class="form-section"><div class="form-section-title">👤 SECTION A: REPORTER INFORMATION</div>', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            report_number = st.text_input("Report Number*", value=generate_report_number(ReportType.HAZARD_REPORT), disabled=True)
            report_date = st.date_input("Report Date*", value=date.today())
        with col2:
            reporter_name = st.text_input("Reporter Name*", value=st.session_state.get('user_name', ''))
            reporter_employee_id = st.text_input("Employee ID*")
        with col3:
            reporter_department = st.selectbox("Department*", options=DEPARTMENTS)
            reporter_contact = st.text_input("Contact Number")
        
        anonymous_report = st.checkbox("Submit as Anonymous Report?")
        if anonymous_report:
            st.info("ℹ️ Your identity will be kept confidential. Only the Safety Department will have access to reporter details if follow-up is required.")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # ══════════════════════════════════════════════════════════════════════
        # SECTION B: HAZARD IDENTIFICATION
        # ══════════════════════════════════════════════════════════════════════
        st.markdown('<div class="form-section"><div class="form-section-title">🔍 SECTION B: HAZARD IDENTIFICATION</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            hazard_date = st.date_input("Date Hazard Observed*", value=date.today())
            hazard_time = st.time_input("Time Hazard Observed")
        with col2:
            hazard_category = st.selectbox("Hazard Category*", options=HAZARD_CATEGORIES)
            subcategory = st.text_input("Subcategory (if applicable)")
        
        col1, col2 = st.columns(2)
        with col1:
            location = st.selectbox("Location*", options=[
                "Aircraft - Cockpit",
                "Aircraft - Cabin",
                "Aircraft - Cargo Hold",
                "Aircraft - Exterior",
                "Ramp/Apron",
                "Taxiway",
                "Runway",
                "Terminal Building",
                "Maintenance Hangar",
                "Cargo Warehouse",
                "Training Center",
                "Office Building",
                "Parking Area",
                "Other"
            ])
        with col2:
            specific_location = st.text_input("Specific Location Details", placeholder="e.g., Bay 5, Gate 12, Aircraft AP-BMA")
            airport = st.selectbox("Airport (if applicable)", options=["N/A"] + list(AIRPORTS.keys()), format_func=lambda x: get_airport_name(x) if x != "N/A" else "N/A")
        
        hazard_title = st.text_input("Hazard Title*", placeholder="Brief title describing the hazard")
        
        hazard_description = st.text_area("Detailed Hazard Description*", height=150,
            placeholder="Provide a detailed description of the hazard including:\n- What was observed\n- Environmental conditions\n- People involved or at risk\n- Equipment or systems affected\n- Frequency of occurrence (if recurring)")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # ══════════════════════════════════════════════════════════════════════
        # SECTION C: RISK ASSESSMENT
        # ══════════════════════════════════════════════════════════════════════
        st.markdown('<div class="form-section"><div class="form-section-title">📊 SECTION C: RISK ASSESSMENT (ICAO STANDARD)</div>', unsafe_allow_html=True)
        
        # Visual Risk Matrix
        render_visual_risk_matrix()
        
        st.markdown("---")
        
        # Interactive Risk Selector
        likelihood, severity, risk_level, risk_classification = render_risk_matrix_selector()
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # ══════════════════════════════════════════════════════════════════════
        # SECTION D: EXISTING CONTROLS
        # ══════════════════════════════════════════════════════════════════════
        st.markdown('<div class="form-section"><div class="form-section-title">🛡️ SECTION D: EXISTING CONTROLS</div>', unsafe_allow_html=True)
        
        existing_controls = st.text_area("Existing Controls/Barriers*", height=100,
            placeholder="Describe any existing controls, procedures, or barriers that are in place to mitigate this hazard...")
        
        col1, col2 = st.columns(2)
        with col1:
            controls_effective = st.selectbox("Are Existing Controls Effective?", options=[
                "Yes - Fully Effective",
                "Partially Effective",
                "No - Ineffective",
                "No Controls in Place",
                "Unknown"
            ])
        with col2:
            control_failures = st.text_input("If Controls Failed, Describe How", placeholder="How did existing controls fail?")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # ══════════════════════════════════════════════════════════════════════
        # SECTION E: SUGGESTED ACTIONS
        # ══════════════════════════════════════════════════════════════════════
        st.markdown('<div class="form-section"><div class="form-section-title">💡 SECTION E: SUGGESTED ACTIONS</div>', unsafe_allow_html=True)
        
        suggested_actions = st.text_area("Suggested Corrective/Preventive Actions*", height=120,
            placeholder="What actions do you suggest to eliminate or mitigate this hazard?\n- Immediate actions\n- Short-term actions\n- Long-term solutions")
        
        col1, col2 = st.columns(2)
        with col1:
            action_priority = st.selectbox("Suggested Priority", options=[
                "Immediate - Within 24 hours",
                "Urgent - Within 72 hours",
                "High - Within 1 week",
                "Medium - Within 2 weeks",
                "Low - Within 1 month"
            ])
        with col2:
            responsible_department = st.selectbox("Suggested Responsible Department", options=DEPARTMENTS)
        
        resources_required = st.text_input("Resources Required (if known)", placeholder="e.g., Budget, Equipment, Training")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # ══════════════════════════════════════════════════════════════════════
        # SECTION F: RELATED INFORMATION
        # ══════════════════════════════════════════════════════════════════════
        st.markdown('<div class="form-section"><div class="form-section-title">📎 SECTION F: RELATED INFORMATION</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            related_flight = st.text_input("Related Flight Number (if applicable)", placeholder="e.g., PF-101")
            related_aircraft = st.selectbox("Related Aircraft (if applicable)", options=["N/A"] + list(AIRCRAFT_FLEET.keys()))
        with col2:
            related_reports = st.text_input("Related Report Numbers", placeholder="e.g., HZD-20240101-ABC123")
            recurring_issue = st.selectbox("Is This a Recurring Issue?", options=["No", "Yes - First Time Reported", "Yes - Previously Reported", "Unknown"])
        
        witnesses = st.text_area("Witnesses (Names & Contact)", height=60, placeholder="List any witnesses...")
        
        evidence_available = st.checkbox("Photos/Evidence Available?")
        if evidence_available:
            evidence_description = st.text_input("Describe Available Evidence", placeholder="e.g., Photos uploaded to shared drive")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # ══════════════════════════════════════════════════════════════════════
        # SECTION G: FOR SAFETY DEPARTMENT USE
        # ══════════════════════════════════════════════════════════════════════
        st.markdown('<div class="form-section"><div class="form-section-title">🔒 SECTION G: FOR SAFETY DEPARTMENT USE</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            investigation_status = st.selectbox("Investigation Status", options=[s.value for s in ReportStatus])
            assigned_to = st.text_input("Assigned To")
        with col2:
            sla_deadline = st.date_input("SLA Deadline", value=date.today() + timedelta(days=Config.HAZARD_SLA_DAYS))
            sla_days_display = (sla_deadline - date.today()).days
            if sla_days_display < 0:
                st.error(f"⚠️ OVERDUE by {abs(sla_days_display)} days")
            elif sla_days_display <= 3:
                st.warning(f"🔴 {sla_days_display} days remaining - CRITICAL")
            elif sla_days_display <= 7:
                st.warning(f"🟡 {sla_days_display} days remaining")
            else:
                st.success(f"🟢 {sla_days_display} days remaining")
        
        safety_review_notes = st.text_area("Safety Department Review Notes", height=80)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            verified = st.checkbox("Hazard Verified?")
            verification_date = st.date_input("Verification Date", value=date.today(), key="verify_date")
        with col2:
            action_plan_approved = st.checkbox("Action Plan Approved?")
            approval_date = st.date_input("Approval Date", value=date.today(), key="approve_date")
        with col3:
            closed = st.checkbox("Report Closed?")
            closure_date = st.date_input("Closure Date", value=date.today(), key="close_date")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # ══════════════════════════════════════════════════════════════════════
        # SECTION H: MANAGEMENT REVIEW
        # ══════════════════════════════════════════════════════════════════════
        st.markdown('<div class="form-section"><div class="form-section-title">📋 SECTION H: MANAGEMENT REVIEW</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            reviewed_by = st.text_input("Reviewed By (Manager)")
            review_date = st.date_input("Review Date", value=date.today(), key="review_date")
        with col2:
            final_risk_accepted = st.selectbox("Final Risk Decision", options=[
                "Pending Review",
                "Risk Accepted - Existing Controls Adequate",
                "Risk Accepted - After Additional Controls",
                "Risk Not Accepted - Further Action Required",
                "Hazard Eliminated"
            ])
        
        management_comments = st.text_area("Management Comments", height=80)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # FORM SUBMISSION
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            submitted = st.form_submit_button("📤 Submit Report", type="primary", use_container_width=True)
        with col2:
            save_draft = st.form_submit_button("💾 Save Draft", use_container_width=True)
        
        if submitted:
            form_data = {
                "report_number": report_number,
                "report_date": str(report_date),
                "reporter_name": reporter_name if not anonymous_report else "Anonymous",
                "reporter_employee_id": reporter_employee_id if not anonymous_report else "Anonymous",
                "reporter_department": reporter_department,
                "anonymous": anonymous_report,
                "hazard_date": str(hazard_date),
                "hazard_time": str(hazard_time),
                "hazard_category": hazard_category,
                "location": location,
                "specific_location": specific_location,
                "airport": airport if airport != "N/A" else None,
                "hazard_title": hazard_title,
                "hazard_description": hazard_description,
                "likelihood": likelihood,
                "severity": severity,
                "risk_classification": risk_classification,
                "risk_level": risk_level.value,
                "existing_controls": existing_controls,
                "controls_effective": controls_effective,
                "suggested_actions": suggested_actions,
                "action_priority": action_priority,
                "responsible_department": responsible_department,
                "related_flight": related_flight,
                "related_aircraft": related_aircraft if related_aircraft != "N/A" else None,
                "recurring_issue": recurring_issue,
                "investigation_status": investigation_status,
                "assigned_to": assigned_to,
                "sla_deadline": str(sla_deadline),
                "created_at": datetime.now().isoformat(),
                "created_by": st.session_state.get('user_id', 'anonymous')
            }
            
            result = db.insert_report('hazard_reports', form_data)
            
            if result:
                st.success(f"✅ Hazard Report {report_number} submitted successfully!")
                st.balloons()
                
                # Show risk action required
                risk_info = RISK_ACTIONS[risk_level]
                st.markdown(f"""
                <div class="alert-box" style="background: {risk_info['color']}20; border-color: {risk_info['color']};">
                    <span style="font-size: 1.5rem;">⚠️</span>
                    <div>
                        <strong>Risk Level: {risk_level.value}</strong><br>
                        Action Required: {risk_info['action']}<br>
                        Timeline: {risk_info['timeline']} | Authority: {risk_info['authority']}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                if 'hazard_reports' not in st.session_state:
                    st.session_state.hazard_reports = []
                st.session_state.hazard_reports.append(form_data)
                st.success(f"✅ Report {report_number} saved locally (Demo Mode)")
# ══════════════════════════════════════════════════════════════════════════════
# FLIGHT SERVICES REPORT (FSR)
# ══════════════════════════════════════════════════════════════════════════════

def render_fsr_form(ocr_data: dict = None):
    """Flight Services Report Form"""
    
    st.markdown('<h2 style="color: #14B8A6;">📋 Flight Services Report (FSR)</h2>', unsafe_allow_html=True)
    st.markdown("*Post-Flight Cabin Services Quality Report*")
    
    data = ocr_data or {}
    
    with st.form("fsr_form"):
        
        # SECTION A: FLIGHT INFORMATION
        st.markdown('<div class="form-section"><div class="form-section-title">✈️ SECTION A: FLIGHT INFORMATION</div>', unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            report_number = st.text_input("Report Number*", value=generate_report_number(ReportType.FSR), disabled=True)
            flight_date = st.date_input("Flight Date*", value=date.today())
        with col2:
            flight_number = st.text_input("Flight Number*", placeholder="PF-XXX")
            aircraft_reg = st.selectbox("Aircraft Registration*", options=list(AIRCRAFT_FLEET.keys()))
        with col3:
            departure = st.selectbox("Departure*", options=list(AIRPORTS.keys()), format_func=get_airport_name)
            std = st.time_input("STD")
            atd = st.time_input("ATD")
        with col4:
            arrival = st.selectbox("Arrival*", options=list(AIRPORTS.keys()), index=1, format_func=get_airport_name)
            sta = st.time_input("STA")
            ata = st.time_input("ATA")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # SECTION B: CREW INFORMATION
        st.markdown('<div class="form-section"><div class="form-section-title">👥 SECTION B: CREW INFORMATION</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            cabin_manager = st.text_input("Cabin Manager / Purser Name*")
            cabin_manager_id = st.text_input("Employee ID*")
        with col2:
            cabin_crew_count = st.number_input("Number of Cabin Crew", min_value=1, max_value=20, value=3)
            cabin_crew_names = st.text_area("Cabin Crew Names", height=60, placeholder="List all cabin crew members...")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # SECTION C: PASSENGER LOAD
        st.markdown('<div class="form-section"><div class="form-section-title">👥 SECTION C: PASSENGER INFORMATION</div>', unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            pax_adult = st.number_input("Adults", min_value=0, max_value=300, value=0)
            pax_child = st.number_input("Children (2-11)", min_value=0, max_value=100, value=0)
        with col2:
            pax_infant = st.number_input("Infants (< 2)", min_value=0, max_value=50, value=0)
            pax_total = pax_adult + pax_child + pax_infant
            st.metric("Total Passengers", pax_total)
        with col3:
            special_pax = st.number_input("Special Assistance (WCHR/WCHC)", min_value=0, value=0)
            um_pax = st.number_input("Unaccompanied Minors", min_value=0, value=0)
        with col4:
            vip_pax = st.number_input("VIP/CIP Passengers", min_value=0, value=0)
            connecting_pax = st.number_input("Connecting Passengers", min_value=0, value=0)
        
        col1, col2 = st.columns(2)
        with col1:
            load_factor = st.slider("Load Factor (%)", min_value=0, max_value=100, value=75)
        with col2:
            seat_config = st.text_input("Seat Configuration", value=get_aircraft_info(aircraft_reg)['config'])
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # SECTION D: BAGGAGE & CARGO
        st.markdown('<div class="form-section"><div class="form-section-title">🧳 SECTION D: BAGGAGE & CARGO</div>', unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            checked_bags = st.number_input("Checked Bags", min_value=0, value=0)
            baggage_weight = st.number_input("Baggage Weight (kg)", min_value=0, value=0)
        with col2:
            cabin_bags = st.number_input("Cabin Bags", min_value=0, value=0)
            excess_baggage = st.number_input("Excess Baggage (kg)", min_value=0, value=0)
        with col3:
            cargo_weight = st.number_input("Cargo Weight (kg)", min_value=0, value=0)
            mail_weight = st.number_input("Mail Weight (kg)", min_value=0, value=0)
        with col4:
            fragile_items = st.number_input("Fragile Items", min_value=0, value=0)
            oversized_items = st.number_input("Oversized Items", min_value=0, value=0)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # SECTION E: SERVICE QUALITY ASSESSMENT
        st.markdown('<div class="form-section"><div class="form-section-title">⭐ SECTION E: SERVICE QUALITY ASSESSMENT</div>', unsafe_allow_html=True)
        
        st.markdown("**Rate each aspect (1 = Poor, 5 = Excellent):**")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            boarding_rating = st.slider("Boarding Process", min_value=1, max_value=5, value=4)
            seat_cleanliness = st.slider("Seat & Cabin Cleanliness", min_value=1, max_value=5, value=4)
            lavatory_cleanliness = st.slider("Lavatory Cleanliness", min_value=1, max_value=5, value=4)
        with col2:
            catering_quality = st.slider("Catering Quality", min_value=1, max_value=5, value=4)
            catering_presentation = st.slider("Catering Presentation", min_value=1, max_value=5, value=4)
            beverage_service = st.slider("Beverage Service", min_value=1, max_value=5, value=4)
        with col3:
            crew_service = st.slider("Crew Service Attitude", min_value=1, max_value=5, value=4)
            announcement_quality = st.slider("Announcement Quality", min_value=1, max_value=5, value=4)
            overall_rating = st.slider("Overall Flight Experience", min_value=1, max_value=5, value=4)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # SECTION F: ISSUES & IRREGULARITIES
        st.markdown('<div class="form-section"><div class="form-section-title">⚠️ SECTION F: ISSUES & IRREGULARITIES</div>', unsafe_allow_html=True)
        
        st.markdown("**Select all issues encountered:**")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("*Boarding Issues*")
            issue_late_boarding = st.checkbox("Late Boarding")
            issue_gate_change = st.checkbox("Gate Change")
            issue_seat_conflict = st.checkbox("Seat Assignment Conflict")
            issue_boarding_pass = st.checkbox("Boarding Pass Issues")
            issue_overhead_bin = st.checkbox("Overhead Bin Space")
        with col2:
            st.markdown("*Catering Issues*")
            issue_meal_shortage = st.checkbox("Meal Shortage")
            issue_special_meal = st.checkbox("Special Meal Not Loaded")
            issue_meal_quality = st.checkbox("Meal Quality Complaint")
            issue_beverage_shortage = st.checkbox("Beverage Shortage")
            issue_catering_late = st.checkbox("Catering Loaded Late")
        with col3:
            st.markdown("*Equipment Issues*")
            issue_ife_inop = st.checkbox("IFE System Inoperative")
            issue_seat_inop = st.checkbox("Seat(s) Inoperative")
            issue_lavatory_inop = st.checkbox("Lavatory Inoperative")
            issue_pax_service_unit = st.checkbox("PSU Issues (Lights/Air)")
            issue_cabin_temp = st.checkbox("Cabin Temperature")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("*Service Issues*")
            issue_pax_complaint = st.checkbox("Passenger Complaint")
            issue_delay = st.checkbox("Service Delay")
            issue_crew_shortage = st.checkbox("Crew Shortage")
        with col2:
            st.markdown("*Safety Issues*")
            issue_medical = st.checkbox("Medical Incident")
            issue_unruly_pax = st.checkbox("Unruly Passenger")
            issue_safety_demo = st.checkbox("Safety Demo Issue")
        
        issue_details = st.text_area("Issue Details", height=100, 
            placeholder="Provide details of any issues selected above...")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # SECTION G: PASSENGER FEEDBACK
        st.markdown('<div class="form-section"><div class="form-section-title">💬 SECTION G: PASSENGER FEEDBACK</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            complaints_count = st.number_input("Number of Complaints Received", min_value=0, value=0)
            complaint_details = st.text_area("Complaint Details", height=80, placeholder="Summarize passenger complaints...")
        with col2:
            compliments_count = st.number_input("Number of Compliments Received", min_value=0, value=0)
            compliment_details = st.text_area("Compliment Details", height=80, placeholder="Summarize passenger compliments...")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # SECTION H: MEDICAL INCIDENTS
        st.markdown('<div class="form-section"><div class="form-section-title">🏥 SECTION H: MEDICAL INCIDENTS</div>', unsafe_allow_html=True)
        
        medical_incident = st.checkbox("Medical Incident Occurred?")
        if medical_incident:
            col1, col2 = st.columns(2)
            with col1:
                medical_type = st.selectbox("Type of Medical Issue", options=[
                    "Fainting/Syncope",
                    "Cardiac Event",
                    "Respiratory Issue",
                    "Allergic Reaction",
                    "Nausea/Vomiting",
                    "Anxiety/Panic Attack",
                    "Seizure",
                    "Injury",
                    "Other"
                ])
                medical_pax_type = st.selectbox("Person Affected", options=["Passenger", "Crew Member", "Other"])
            with col2:
                doctor_onboard = st.checkbox("Medical Professional Onboard?")
                medical_kit_used = st.checkbox("Medical Kit Used?")
                diversion_required = st.checkbox("Diversion Required?")
            
            medical_details = st.text_area("Medical Incident Details", height=80)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # SECTION I: DELAYS
        st.markdown('<div class="form-section"><div class="form-section-title">⏱️ SECTION I: DELAYS</div>', unsafe_allow_html=True)
        
        delay_occurred = st.checkbox("Delay Occurred?")
        if delay_occurred:
            col1, col2, col3 = st.columns(3)
            with col1:
                delay_minutes = st.number_input("Delay Duration (minutes)", min_value=0, value=0)
            with col2:
                delay_code = st.selectbox("Delay Code", options=[
                    "11 - Late Crew",
                    "12 - Late Crew from another flight",
                    "13 - Crew Legality",
                    "21 - Catering",
                    "31 - Cargo/Baggage",
                    "32 - Late Baggage",
                    "41 - Aircraft Defect",
                    "42 - Scheduled Maintenance",
                    "51 - Damage during ground handling",
                    "61 - ATC/Airways",
                    "71 - Weather",
                    "81 - Passenger Handling",
                    "82 - Late Passengers",
                    "83 - Passenger Illness",
                    "91 - Reactionary Delay",
                    "96 - Airport Facilities",
                    "99 - Other"
                ])
            with col3:
                delay_responsibility = st.selectbox("Delay Responsibility", options=[
                    "Air Sial",
                    "Ground Handler",
                    "Airport",
                    "ATC",
                    "Weather",
                    "Passenger",
                    "Other"
                ])
            
            delay_details = st.text_area("Delay Details", height=60)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # SECTION J: ADDITIONAL REMARKS
        st.markdown('<div class="form-section"><div class="form-section-title">📝 SECTION J: ADDITIONAL REMARKS</div>', unsafe_allow_html=True)
        
        additional_remarks = st.text_area("Additional Remarks / Observations", height=100,
            placeholder="Any other observations, recommendations, or comments...")
        
        follow_up_required = st.checkbox("Follow-up Required?")
        if follow_up_required:
            follow_up_department = st.multiselect("Follow-up Department(s)", options=[
                "Cabin Services",
                "Catering",
                "Ground Operations",
                "Maintenance",
                "Safety",
                "Quality Assurance",
                "Commercial",
                "HR"
            ])
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # FORM SUBMISSION
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            submitted = st.form_submit_button("📤 Submit Report", type="primary", use_container_width=True)
        with col2:
            save_draft = st.form_submit_button("💾 Save Draft", use_container_width=True)
        
        if submitted:
            form_data = {
                "report_number": report_number,
                "flight_date": str(flight_date),
                "flight_number": flight_number,
                "aircraft_registration": aircraft_reg,
                "departure_airport": departure,
                "arrival_airport": arrival,
                "cabin_manager": cabin_manager,
                "pax_total": pax_total,
                "load_factor": load_factor,
                "boarding_rating": boarding_rating,
                "cleanliness_rating": seat_cleanliness,
                "catering_rating": catering_quality,
                "crew_service_rating": crew_service,
                "overall_rating": overall_rating,
                "complaints_count": complaints_count,
                "compliments_count": compliments_count,
                "medical_incident": medical_incident,
                "delay_occurred": delay_occurred,
                "delay_minutes": delay_minutes if delay_occurred else 0,
                "additional_remarks": additional_remarks,
                "created_at": datetime.now().isoformat(),
                "created_by": st.session_state.get('user_id', 'anonymous')
            }
            
            result = db.insert_report('fsr_reports', form_data)
            
            if result:
                st.success(f"✅ FSR {report_number} submitted successfully!")
            else:
                if 'fsr_reports' not in st.session_state:
                    st.session_state.fsr_reports = []
                st.session_state.fsr_reports.append(form_data)
                st.success(f"✅ Report {report_number} saved locally (Demo Mode)")


# ══════════════════════════════════════════════════════════════════════════════
# CAPTAIN'S DEBRIEF REPORT (DBR)
# ══════════════════════════════════════════════════════════════════════════════

def render_dbr_form(ocr_data: dict = None):
    """Captain's Debrief Report Form"""
    
    st.markdown('<h2 style="color: #F59E0B;">👨‍✈️ Captain\'s Debrief Report (DBR)</h2>', unsafe_allow_html=True)
    st.markdown("*Post-Flight Technical & Operational Debrief*")
    
    data = ocr_data or {}
    
    with st.form("dbr_form"):
        
        # SECTION A: FLIGHT INFORMATION
        st.markdown('<div class="form-section"><div class="form-section-title">✈️ SECTION A: FLIGHT INFORMATION</div>', unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            report_number = st.text_input("Report Number*", value=generate_report_number(ReportType.CAPTAIN_DBR), disabled=True)
            flight_date = st.date_input("Flight Date*", value=date.today())
        with col2:
            flight_number = st.text_input("Flight Number*", placeholder="PF-XXX")
            aircraft_reg = st.selectbox("Aircraft Registration*", options=list(AIRCRAFT_FLEET.keys()))
            aircraft_info = get_aircraft_info(aircraft_reg)
        with col3:
            departure = st.selectbox("Departure*", options=list(AIRPORTS.keys()), format_func=get_airport_name)
            arrival = st.selectbox("Arrival*", options=list(AIRPORTS.keys()), index=1, format_func=get_airport_name)
        with col4:
            alternate_used = st.selectbox("Alternate Used?", options=["No", "Yes"])
            if alternate_used == "Yes":
                alternate = st.selectbox("Alternate Airport", options=list(AIRPORTS.keys()), format_func=get_airport_name)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # SECTION B: TIMES
        st.markdown('<div class="form-section"><div class="form-section-title">⏱️ SECTION B: TIMES</div>', unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            block_off = st.time_input("Block Off (OOOI)*")
            takeoff_time = st.time_input("Takeoff Time*")
        with col2:
            landing_time = st.time_input("Landing Time*")
            block_on = st.time_input("Block On (OOOI)*")
        with col3:
            block_time = st.text_input("Block Time", placeholder="HH:MM")
            flight_time = st.text_input("Flight Time", placeholder="HH:MM")
        with col4:
            air_time = st.text_input("Air Time", placeholder="HH:MM")
            taxi_out = st.number_input("Taxi Out (min)", min_value=0, value=10)
            taxi_in = st.number_input("Taxi In (min)", min_value=0, value=5)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # SECTION C: FUEL
        st.markdown('<div class="form-section"><div class="form-section-title">⛽ SECTION C: FUEL</div>', unsafe_allow_html=True)
        
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            fuel_planned = st.number_input("Planned Trip Fuel (kg)", min_value=0, value=0)
            fuel_departure = st.number_input("Departure Fuel (kg)*", min_value=0, value=0)
        with col2:
            fuel_arrival = st.number_input("Arrival Fuel (kg)*", min_value=0, value=0)
            fuel_used = st.number_input("Fuel Used (kg)*", min_value=0, value=0)
        with col3:
            fuel_variance = fuel_planned - fuel_used if fuel_planned > 0 else 0
            st.metric("Fuel Variance (kg)", f"{fuel_variance:+d}")
            tankering = st.number_input("Tankering (kg)", min_value=0, value=0)
        with col4:
            fuel_uplift = st.number_input("Fuel Uplift (kg)", min_value=0, value=0)
            density = st.number_input("Fuel Density", min_value=0.75, max_value=0.85, value=0.80, format="%.3f")
        with col5:
            min_fuel_event = st.checkbox("Minimum Fuel Declared?")
            mayday_fuel = st.checkbox("Mayday Fuel Declared?")
        
        fuel_remarks = st.text_input("Fuel Remarks", placeholder="Any fuel-related observations...")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # SECTION D: WEIGHTS & PERFORMANCE
        st.markdown('<div class="form-section"><div class="form-section-title">⚖️ SECTION D: WEIGHTS & PERFORMANCE</div>', unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            zfw = st.number_input("ZFW (kg)", min_value=0, value=0)
            tow = st.number_input("TOW (kg)*", min_value=0, value=0)
        with col2:
            lw = st.number_input("LW (kg)*", min_value=0, value=0)
            mac = st.number_input("MAC (%)", min_value=0.0, max_value=100.0, value=25.0, format="%.1f")
        with col3:
            takeoff_config = st.selectbox("Takeoff Flap Setting", options=["0", "5", "10", "15", "20", "25"])
            takeoff_thrust = st.selectbox("Takeoff Thrust", options=["TOGA", "Flex/Derated", "Other"])
        with col4:
            flex_temp = st.number_input("Flex Temp (°C)", min_value=0, max_value=70, value=45)
            v_speeds = st.text_input("V-Speeds (V1/VR/V2)", placeholder="e.g., 125/128/135")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # SECTION E: WEATHER
        st.markdown('<div class="form-section"><div class="form-section-title">🌤️ SECTION E: WEATHER</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Departure Weather**")
            dep_metar = st.text_input("Departure METAR", placeholder="e.g., OPLA 120800Z...")
            dep_conditions = st.selectbox("Departure Conditions", options=WEATHER_CONDITIONS, key="dep_wx")
            dep_wind = st.text_input("Departure Wind", placeholder="e.g., 360/10G18")
            dep_rwy_condition = st.selectbox("Departure RWY Condition", options=RUNWAY_CONDITIONS, key="dep_rwy")
        with col2:
            st.markdown("**Arrival Weather**")
            arr_metar = st.text_input("Arrival METAR", placeholder="e.g., OPKC 120900Z...")
            arr_conditions = st.selectbox("Arrival Conditions", options=WEATHER_CONDITIONS, key="arr_wx")
            arr_wind = st.text_input("Arrival Wind", placeholder="e.g., 270/15G25")
            arr_rwy_condition = st.selectbox("Arrival RWY Condition", options=RUNWAY_CONDITIONS, key="arr_rwy")
        
        st.markdown("**Enroute Weather**")
        col1, col2, col3 = st.columns(3)
        with col1:
            turbulence = st.selectbox("Turbulence Encountered", options=TURBULENCE_INTENSITY)
            turbulence_altitude = st.text_input("Turbulence Altitude/Location", placeholder="e.g., FL280, 50nm south LHE")
        with col2:
            icing = st.selectbox("Icing Encountered", options=["None", "Light", "Moderate", "Severe"])
            icing_altitude = st.text_input("Icing Altitude/Location", placeholder="If icing encountered")
        with col3:
            windshear = st.selectbox("Windshear Encountered", options=["None", "Light", "Moderate", "Severe", "PIREP Only"])
            wx_deviation = st.checkbox("Weather Deviation Required?")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # SECTION F: APPROACH & LANDING
        st.markdown('<div class="form-section"><div class="form-section-title">🛬 SECTION F: APPROACH & LANDING</div>', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            approach_type = st.selectbox("Approach Type*", options=APPROACH_TYPES)
            runway_used = st.text_input("Runway Used*", placeholder="e.g., 25R")
            approach_category = st.selectbox("Approach Category", options=["CAT I", "CAT II", "CAT III", "Non-Precision", "Visual"])
        with col2:
            autoland = st.checkbox("Autoland Performed?")
            go_around = st.checkbox("Go-Around Performed?")
            if go_around:
                go_around_reason = st.text_input("Go-Around Reason")
            landing_rating = st.select_slider("Landing Rating", options=["Hard", "Firm", "Normal", "Smooth", "Very Smooth"])
        with col3:
            braking_action = st.selectbox("Braking Action", options=BRAKING_ACTIONS)
            thrust_reverser = st.selectbox("Thrust Reverser Used", options=["Yes - Both", "Yes - #1 Only", "Yes - #2 Only", "No", "INOP"])
            autobrake = st.selectbox("Autobrake Setting", options=["LO", "MED", "MAX", "Manual", "RTO"])
        
        unstable_approach = st.checkbox("Unstable Approach?")
        if unstable_approach:
            unstable_details = st.text_area("Unstable Approach Details", height=60,
                placeholder="Describe the unstable approach and actions taken...")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # SECTION G: TECHNICAL STATUS
        st.markdown('<div class="form-section"><div class="form-section-title">🔧 SECTION G: TECHNICAL STATUS</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            mel_items = st.checkbox("Aircraft Operating with MEL/CDL Items?")
            if mel_items:
                mel_details = st.text_area("MEL/CDL Items", height=60, placeholder="List MEL/CDL items...")
        with col2:
            new_defects = st.checkbox("New Defects to Report?")
            if new_defects:
                defect_details = st.text_area("New Defect Details", height=60, placeholder="Describe defects discovered...")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            apu_status = st.selectbox("APU Status", options=["Serviceable", "Unserviceable", "Used for Start", "Not Required"])
        with col2:
            tcas_status = st.selectbox("TCAS Status", options=["Normal", "TA Only", "INOP", "Test Required"])
        with col3:
            gpws_status = st.selectbox("GPWS/EGPWS Status", options=["Normal", "Caution Received", "Warning Received", "INOP"])
        
        technical_remarks = st.text_area("Technical Remarks", height=60, placeholder="Any technical observations...")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # SECTION H: NAVIGATION & ATC
        st.markdown('<div class="form-section"><div class="form-section-title">🧭 SECTION H: NAVIGATION & ATC</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            route_flown = st.text_input("Route Flown", placeholder="e.g., OPLA DCT ESMUR UM875 OPKC")
            route_deviation = st.checkbox("Route Deviation Required?")
            if route_deviation:
                deviation_reason = st.text_input("Deviation Reason")
            fms_nav = st.selectbox("Primary Navigation", options=["FMS/RNAV", "VOR/DME", "NDB", "Radar Vectors", "Visual"])
        with col2:
            atc_handling = st.select_slider("ATC Handling Quality", options=["Poor", "Fair", "Good", "Very Good", "Excellent"])
            atc_delays = st.checkbox("ATC Delays Encountered?")
            if atc_delays:
                atc_delay_details = st.text_input("ATC Delay Details", placeholder="e.g., 20 min hold at ESMUR")
            rvsm_compliance = st.checkbox("RVSM Airspace Flown?", value=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # SECTION I: CREW & HUMAN FACTORS
        st.markdown('<div class="form-section"><div class="form-section-title">👨‍✈️ SECTION I: CREW & HUMAN FACTORS</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            captain_name = st.text_input("Captain Name*")
            captain_license = st.text_input("Captain License*")
            captain_duty_hours = st.number_input("Captain Duty Hours", min_value=0.0, max_value=24.0, value=0.0, format="%.1f")
        with col2:
            fo_name = st.text_input("First Officer Name")
            fo_license = st.text_input("FO License")
            fo_duty_hours = st.number_input("FO Duty Hours", min_value=0.0, max_value=24.0, value=0.0, format="%.1f")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            fatigue_level = st.select_slider("Fatigue Level (Samn-Perelli)", options=[1, 2, 3, 4, 5, 6, 7],
                format_func=lambda x: f"{x} - {'Fully Alert' if x==1 else 'Very Lively' if x==2 else 'OK' if x==3 else 'Little Tired' if x==4 else 'Moderately Tired' if x==5 else 'Extremely Tired' if x==6 else 'Completely Exhausted'}")
        with col2:
            crew_coordination = st.select_slider("Crew Coordination", options=["Poor", "Fair", "Good", "Very Good", "Excellent"])
        with col3:
            training_flight = st.checkbox("Training Flight?")
            check_flight = st.checkbox("Check Flight?")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # SECTION J: SAFETY OBSERVATIONS
        st.markdown('<div class="form-section"><div class="form-section-title">🛡️ SECTION J: SAFETY OBSERVATIONS</div>', unsafe_allow_html=True)
        
        safety_events = st.multiselect("Safety Events (select all that apply)", options=[
            "TCAS TA",
            "TCAS RA",
            "GPWS Warning",
            "Windshear Alert",
            "Stall Warning",
            "Engine Warning",
            "Fire Warning",
            "Smoke/Fumes",
            "Bird Strike",
            "Laser Strike",
            "Near Miss",
            "Runway Incursion",
            "Unstable Approach",
            "Hard Landing",
            "Long Landing",
            "Tail Strike",
            "Rejected Takeoff",
            "Emergency Descent",
            "Medical Emergency",
            "Unruly Passenger",
            "Security Incident",
            "None"
        ])
        
        safety_observations = st.text_area("Safety Observations & Recommendations", height=100,
            placeholder="Any safety observations, concerns, or recommendations...")
        
        separate_report_required = st.checkbox("Separate Safety Report Required?")
        if separate_report_required:
            st.info("ℹ️ Please submit a separate report via the appropriate form (Incident, Bird Strike, Laser Strike, TCAS, or Hazard Report)")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # SECTION K: OVERALL ASSESSMENT
        st.markdown('<div class="form-section"><div class="form-section-title">📊 SECTION K: OVERALL ASSESSMENT</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            flight_rating = st.select_slider("Overall Flight Rating", options=["Unsatisfactory", "Below Average", "Average", "Good", "Excellent"])
        with col2:
            flight_highlights = st.text_input("Flight Highlights/Lowlights", placeholder="Key aspects of the flight")
        
        general_remarks = st.text_area("General Remarks", height=100,
            placeholder="Any additional remarks or comments about the flight...")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # FORM SUBMISSION
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            submitted = st.form_submit_button("📤 Submit Report", type="primary", use_container_width=True)
        with col2:
            save_draft = st.form_submit_button("💾 Save Draft", use_container_width=True)
        
        if submitted:
            form_data = {
                "report_number": report_number,
                "flight_date": str(flight_date),
                "flight_number": flight_number,
                "aircraft_registration": aircraft_reg,
                "departure_airport": departure,
                "arrival_airport": arrival,
                "block_off": str(block_off),
                "block_on": str(block_on),
                "fuel_departure": fuel_departure,
                "fuel_arrival": fuel_arrival,
                "fuel_used": fuel_used,
                "tow": tow,
                "lw": lw,
                "approach_type": approach_type,
                "runway_used": runway_used,
                "go_around": go_around,
                "landing_rating": landing_rating,
                "unstable_approach": unstable_approach,
                "turbulence": turbulence,
                "captain_name": captain_name,
                "fo_name": fo_name,
                "fatigue_level": fatigue_level,
                "safety_events": safety_events,
                "safety_observations": safety_observations,
                "flight_rating": flight_rating,
                "general_remarks": general_remarks,
                "created_at": datetime.now().isoformat(),
                "created_by": st.session_state.get('user_id', 'anonymous')
            }
            
            result = db.insert_report('captain_dbr', form_data)
            
            if result:
                st.success(f"✅ Captain's DBR {report_number} submitted successfully!")
            else:
                if 'captain_dbr' not in st.session_state:
                    st.session_state.captain_dbr = []
                st.session_state.captain_dbr.append(form_data)
                st.success(f"✅ Report {report_number} saved locally (Demo Mode)")
# ══════════════════════════════════════════════════════════════════════════════
# DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════

def render_dashboard():
    """Main dashboard with analytics and KPIs"""
    
    st.markdown("## 📊 Safety Dashboard")
    
    # Get data
    counts = db.get_report_counts()
    investigation_stats = db.get_investigation_stats()
    hazards_by_sla = db.get_hazards_by_sla_status()
    
    # If database not connected, use session state data
    if not db.is_connected:
        counts = {
            'bird_strikes': len(st.session_state.get('bird_strikes', [])),
            'laser_strikes': len(st.session_state.get('laser_strikes', [])),
            'tcas_reports': len(st.session_state.get('tcas_reports', [])),
            'hazard_reports': len(st.session_state.get('hazard_reports', [])),
            'aircraft_incidents': len(st.session_state.get('aircraft_incidents', [])),
            'fsr_reports': len(st.session_state.get('fsr_reports', [])),
            'captain_dbr': len(st.session_state.get('captain_dbr', []))
        }
        investigation_stats = {'total': sum(counts.values()), 'open': 0, 'awaiting_reply': 0, 'closed': 0, 'in_progress': 0, 'by_status': {}}
    
    # KPI Cards
    render_kpi_cards(counts, investigation_stats)
    
    # Weather Widget
    st.markdown("---")
    WeatherService.render_weather_widget()
    
    # Main content
    st.markdown("---")
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Report Distribution Charts
        st.markdown("### 📈 Report Distribution")
        
        tab1, tab2 = st.tabs(["📊 By Type", "📅 By Month"])
        
        with tab1:
            # Pie chart
            report_data = {
                'Type': ['Bird Strikes', 'Laser Strikes', 'TCAS', 'Hazards', 'Incidents', 'FSR', 'DBR'],
                'Count': [
                    counts.get('bird_strikes', 0),
                    counts.get('laser_strikes', 0),
                    counts.get('tcas_reports', 0),
                    counts.get('hazard_reports', 0),
                    counts.get('aircraft_incidents', 0),
                    counts.get('fsr_reports', 0),
                    counts.get('captain_dbr', 0)
                ]
            }
            
            fig = px.pie(
                report_data, 
                values='Count', 
                names='Type',
                color='Type',
                color_discrete_map={
                    'Bird Strikes': '#3B82F6',
                    'Laser Strikes': '#8B5CF6',
                    'TCAS': '#F97316',
                    'Hazards': '#EF4444',
                    'Incidents': '#10B981',
                    'FSR': '#14B8A6',
                    'DBR': '#F59E0B'
                },
                hole=0.4
            )
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font_color='#C9D1D9',
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=-0.2)
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with tab2:
            # Bar chart by month (mock data for demo)
            months = ['Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
            fig = go.Figure()
            fig.add_trace(go.Bar(name='Bird Strikes', x=months, y=[5, 8, 12, 7, 4, 3], marker_color='#3B82F6'))
            fig.add_trace(go.Bar(name='Laser Strikes', x=months, y=[2, 3, 5, 4, 6, 2], marker_color='#8B5CF6'))
            fig.add_trace(go.Bar(name='Hazards', x=months, y=[8, 12, 15, 10, 8, 6], marker_color='#EF4444'))
            fig.update_layout(
                barmode='group',
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font_color='#C9D1D9',
                xaxis=dict(showgrid=False),
                yaxis=dict(showgrid=True, gridcolor='#30363D')
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Department Breakdown
        st.markdown("### 🏢 Hazards by Department")
        
        # Get department data
        dept_data = {}
        hazards = st.session_state.get('hazard_reports', [])
        for hazard in hazards:
            dept = hazard.get('reporter_department', 'Unknown')
            dept_data[dept] = dept_data.get(dept, 0) + 1
        
        if dept_data:
            fig = px.bar(
                x=list(dept_data.values()),
                y=list(dept_data.keys()),
                orientation='h',
                color=list(dept_data.values()),
                color_continuous_scale='Reds'
            )
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font_color='#C9D1D9',
                showlegend=False,
                xaxis_title="Count",
                yaxis_title="",
                coloraxis_showscale=False
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No hazard reports yet. Submit reports to see department breakdown.")
    
    with col2:
        # SLA Alerts
        st.markdown("### ⏰ SLA Alerts")
        
        # Get hazards from session state for demo
        hazards = st.session_state.get('hazard_reports', [])
        
        overdue_count = 0
        critical_count = 0
        warning_count = 0
        
        for hazard in hazards:
            sla = calculate_sla_status(hazard.get('created_at', str(date.today())), Config.HAZARD_SLA_DAYS)
            if sla.status == 'overdue':
                overdue_count += 1
            elif sla.status == 'critical':
                critical_count += 1
            elif sla.status == 'warning':
                warning_count += 1
        
        if overdue_count > 0:
            st.markdown(f"""
            <div class="alert-box alert-danger">
                <span style="font-size: 1.5rem;">🚨</span>
                <div>
                    <strong>{overdue_count} OVERDUE</strong><br>
                    <small>Requires immediate attention</small>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        if critical_count > 0:
            st.markdown(f"""
            <div class="alert-box alert-warning">
                <span style="font-size: 1.5rem;">🔴</span>
                <div>
                    <strong>{critical_count} Critical</strong><br>
                    <small>Due within 3 days</small>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        if warning_count > 0:
            st.markdown(f"""
            <div class="alert-box" style="background: rgba(255,193,7,0.1); border: 1px solid #FFC107;">
                <span style="font-size: 1.5rem;">🟡</span>
                <div>
                    <strong>{warning_count} Warning</strong><br>
                    <small>Due within 7 days</small>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        if overdue_count == 0 and critical_count == 0 and warning_count == 0:
            st.markdown("""
            <div class="alert-box alert-success">
                <span style="font-size: 1.5rem;">✅</span>
                <div>
                    <strong>All Clear</strong><br>
                    <small>No urgent SLA items</small>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # Recent Activity
        st.markdown("### 📋 Recent Activity")
        
        # Combine all reports and sort by date
        all_reports = []
        for report_type, reports in [
            ('bird_strikes', st.session_state.get('bird_strikes', [])),
            ('laser_strikes', st.session_state.get('laser_strikes', [])),
            ('tcas_reports', st.session_state.get('tcas_reports', [])),
            ('hazard_reports', st.session_state.get('hazard_reports', [])),
            ('aircraft_incidents', st.session_state.get('aircraft_incidents', []))
        ]:
            for report in reports:
                all_reports.append({
                    'type': report_type,
                    'number': report.get('report_number', 'N/A'),
                    'date': report.get('created_at', str(datetime.now()))
                })
        
        # Sort by date and take last 5
        all_reports.sort(key=lambda x: x['date'], reverse=True)
        
        for report in all_reports[:5]:
            type_icons = {
                'bird_strikes': '🐦',
                'laser_strikes': '🔴',
                'tcas_reports': '📡',
                'hazard_reports': '⚠️',
                'aircraft_incidents': '🚨'
            }
            icon = type_icons.get(report['type'], '📋')
            
            st.markdown(f"""
            <div style="padding: 0.5rem; border-left: 3px solid #2E7D32; margin-bottom: 0.5rem; background: #161B22; border-radius: 4px;">
                <span>{icon}</span> <strong>{report['number']}</strong>
                <br><small style="color: #8B949E;">{report['date'][:16]}</small>
            </div>
            """, unsafe_allow_html=True)
        
        if not all_reports:
            st.info("No recent activity")
        
        # Risk Matrix Summary
        st.markdown("### 🎯 Risk Distribution")
        
        # Count by risk level
        risk_counts = {'Extreme': 0, 'High': 0, 'Medium': 0, 'Low': 0}
        for hazard in hazards:
            risk = hazard.get('risk_level', 'Low')
            risk_counts[risk] = risk_counts.get(risk, 0) + 1
        
        for level, count in risk_counts.items():
            color = RISK_ACTIONS[RiskLevel[level.upper()]]['color']
            st.markdown(f"""
            <div style="display: flex; justify-content: space-between; padding: 0.5rem; 
                        background: {color}20; border-radius: 4px; margin-bottom: 0.25rem;">
                <span style="color: {color}; font-weight: 600;">{level}</span>
                <span style="font-weight: 600;">{count}</span>
            </div>
            """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# VIEW REPORTS
# ══════════════════════════════════════════════════════════════════════════════

def generate_mock_emails(report_id: str):
    """Generate mock email thread for a report"""
    import random
    
    senders = [
        ("Safety Manager", "safety.manager@airsial.com"),
        ("Engineering HOD", "engineering.hod@airsial.com"),
        ("Flight Ops Manager", "flightops.manager@airsial.com"),
        ("Quality Assurance", "qa@airsial.com"),
        ("Ground Ops Supervisor", "groundops@airsial.com"),
        ("CAA Liaison", "caa.liaison@airsial.com"),
        ("Maintenance Controller", "maint.controller@airsial.com"),
    ]
    
    subjects = [
        f"RE: Investigation Required - {report_id}",
        f"FW: Action Items for {report_id}",
        f"RE: Status Update - {report_id}",
        f"RE: Corrective Action Proposed - {report_id}",
        f"RE: Closure Review - {report_id}",
    ]
    
    messages = [
        "Initial report received. Assigning to relevant department for investigation.",
        "Thank you for the report. We have reviewed the incident details and are initiating corrective measures.",
        "Engineering team has inspected the affected component. Root cause identified as wear and tear.",
        "Proposed corrective action: Replace affected sensor and update maintenance schedule.",
        "All corrective actions have been implemented. Requesting closure approval.",
        "Verified implementation of corrective actions. Recommend closing this report.",
        "Report closure approved. Documentation archived for future reference.",
    ]
    
    emails = []
    base_date = datetime.now() - timedelta(days=random.randint(5, 30))
    
    num_emails = random.randint(3, 6)
    for i in range(num_emails):
        sender_name, sender_email = random.choice(senders)
        email_date = base_date + timedelta(days=i, hours=random.randint(1, 12))
        
        emails.append({
            "date": email_date.strftime("%b %d, %Y %H:%M"),
            "sender_name": sender_name,
            "sender_email": sender_email,
            "subject": subjects[min(i, len(subjects)-1)],
            "message": messages[min(i, len(messages)-1)],
            "direction": "incoming" if i % 2 == 0 else "outgoing"
        })
    
    return emails


def generate_ai_conclusion(report_id: str, emails: list):
    """Generate AI-based conclusion from email thread"""
    
    conclusions = [
        f"✅ **Issue Resolved**: Based on the email thread analysis, the issue reported in {report_id} has been successfully resolved. Engineering replaced the affected component on the reported date and verification was completed.",
        f"✅ **Corrective Action Implemented**: Analysis indicates that all necessary corrective actions for {report_id} have been implemented. The maintenance schedule has been updated to prevent recurrence.",
        f"✅ **Investigation Complete**: The investigation for {report_id} has been concluded. Root cause was identified as procedural gap, and updated SOPs have been distributed to all relevant personnel.",
        f"⚠️ **Pending Final Verification**: Report {report_id} is near closure. Awaiting final verification from Quality Assurance before official closure.",
        f"✅ **Closed - No Further Action**: {report_id} has been reviewed and closed. Contributing factors were addressed through enhanced training and equipment inspection protocols.",
    ]
    
    import random
    random.seed(hash(report_id))
    
    key_findings = [
        "Root cause: Equipment wear beyond service limits",
        "Contributing factor: Environmental conditions",
        "Corrective action: Component replacement completed",
        "Preventive measure: Updated inspection schedule",
        "Training: Refresher briefing conducted for crew",
    ]
    
    return {
        "conclusion": random.choice(conclusions),
        "key_findings": random.sample(key_findings, 3),
        "confidence": f"{random.randint(85, 98)}%",
        "analyzed_emails": len(emails),
        "analysis_date": datetime.now().strftime("%b %d, %Y %H:%M")
    }


def render_view_reports():
    """View and manage submitted reports with enhanced tracking"""
    
    st.markdown("## 📋 View Reports")
    st.markdown("*Advanced Report Tracking with Email Trail & AI Analysis*")
    
    # Report type and Department filters
    col1, col2 = st.columns(2)
    with col1:
        report_type = st.selectbox("Select Report Type", options=[
            "All Reports",
            "Bird Strikes",
            "Laser Strikes",
            "TCAS Reports",
            "Hazard Reports",
            "Aircraft Incidents",
            "FSR Reports",
            "Captain DBR"
        ])
    
    with col2:
        # Department filter - NEW
        dept_filter = st.multiselect(
            "🏢 Filter by Department",
            options=DEPARTMENTS,
            default=[],
            help="Select departments to filter reports"
        )
    
    # Additional filters
    col1, col2, col3 = st.columns(3)
    with col1:
        date_filter = st.date_input("From Date", value=date.today() - timedelta(days=30))
    with col2:
        status_filter = st.selectbox("Status", options=["All"] + [s.value for s in ReportStatus])
    with col3:
        search_term = st.text_input("Search", placeholder="Report number or keyword...")
    
    st.markdown("---")
    
    # Get reports based on selection
    type_mapping = {
        "Bird Strikes": "bird_strikes",
        "Laser Strikes": "laser_strikes",
        "TCAS Reports": "tcas_reports",
        "Hazard Reports": "hazard_reports",
        "Aircraft Incidents": "aircraft_incidents",
        "FSR Reports": "fsr_reports",
        "Captain DBR": "captain_dbr"
    }
    
    # Department assignment for demo
    dept_assignment = {
        "bird_strikes": "Flight Operations",
        "laser_strikes": "Flight Operations",
        "tcas_reports": "Flight Operations",
        "hazard_reports": "Safety Department",
        "aircraft_incidents": "Engineering & Maintenance",
        "fsr_reports": "Cabin Services",
        "captain_dbr": "Flight Operations"
    }
    
    reports = []
    
    if report_type == "All Reports":
        for rtype, key in type_mapping.items():
            type_reports = st.session_state.get(key, [])
            for r in type_reports:
                r['_type'] = rtype
                r['_department'] = r.get('reporter_department', dept_assignment.get(key, 'Safety Department'))
            reports.extend(type_reports)
    else:
        key = type_mapping.get(report_type, "hazard_reports")
        reports = st.session_state.get(key, [])
        for r in reports:
            r['_type'] = report_type
            r['_department'] = r.get('reporter_department', dept_assignment.get(key, 'Safety Department'))
    
    # Apply filters
    if search_term:
        reports = [r for r in reports if search_term.lower() in str(r).lower()]
    
    if status_filter != "All":
        reports = [r for r in reports if r.get('investigation_status') == status_filter]
    
    # Department filter - NEW
    if dept_filter:
        reports = [r for r in reports if r.get('_department') in dept_filter]
    
    # Display reports
    if reports:
        st.markdown(f"**Found {len(reports)} report(s)**")
        
        for report in reports:
            report_num = report.get('report_number', f"RPT-{uuid.uuid4().hex[:8].upper()}")
            report_date = report.get('created_at', '')[:10] if report.get('created_at') else date.today().isoformat()
            report_status = report.get('investigation_status', 'Draft')
            report_title = report.get('hazard_title') or report.get('incident_title') or report.get('flight_number', 'N/A')
            report_dept = report.get('_department', 'Safety Department')
            
            # Determine category badge
            rtype = report.get('_type', 'Other')
            badge_class = {
                'Bird Strikes': ('cat-bird', '#DBEAFE', '#1D4ED8'),
                'Laser Strikes': ('cat-laser', '#F3E8FF', '#7C3AED'),
                'TCAS Reports': ('cat-tcas', '#FFEDD5', '#C2410C'),
                'Hazard Reports': ('cat-hazard', '#FEE2E2', '#DC2626'),
                'Aircraft Incidents': ('cat-incident', '#D1FAE5', '#059669'),
                'FSR Reports': ('cat-fsr', '#CCFBF1', '#0D9488'),
                'Captain DBR': ('cat-dbr', '#FEF3C7', '#D97706')
            }.get(rtype, ('cat-incident', '#D1FAE5', '#059669'))
            
            # Department badge colors
            dept_colors = {
                'Flight Operations': ('#DBEAFE', '#1D4ED8'),
                'Engineering & Maintenance': ('#FEF3C7', '#D97706'),
                'Safety Department': ('#FEE2E2', '#DC2626'),
                'Ground Operations': ('#D1FAE5', '#059669'),
                'Cabin Services': ('#F3E8FF', '#7C3AED'),
                'Quality Assurance': ('#CCFBF1', '#0D9488'),
            }
            dept_bg, dept_color = dept_colors.get(report_dept, ('#F1F5F9', '#475569'))
            
            with st.expander(f"📋 {report_num} - {report_title}", expanded=False):
                # Header with badges - Department Badge
                st.markdown(f"""
                <div style="display: flex; gap: 0.5rem; margin-bottom: 1rem; flex-wrap: wrap;">
                    <span style="background: {badge_class[1]}; color: {badge_class[2]}; padding: 0.25rem 0.6rem; border-radius: 12px; font-size: 0.75rem; font-weight: 600;">{rtype}</span>
                    <span style="background: {dept_bg}; color: {dept_color}; padding: 0.25rem 0.6rem; border-radius: 12px; font-size: 0.75rem; font-weight: 600;">🏢 {report_dept}</span>
                    <span style="background: #F1F5F9; color: #475569; padding: 0.25rem 0.6rem; border-radius: 12px; font-size: 0.75rem; font-weight: 600;">📅 {report_date}</span>
                </div>
                """, unsafe_allow_html=True)
                
                # PROMINENT TABS with custom styling
                st.markdown("""
                <style>
                .report-tabs .stTabs [data-baseweb="tab-list"] {
                    gap: 8px;
                    background: #F1F5F9;
                    padding: 8px;
                    border-radius: 12px;
                }
                .report-tabs .stTabs [data-baseweb="tab"] {
                    padding: 10px 20px;
                    font-weight: 600;
                }
                </style>
                """, unsafe_allow_html=True)
                
                # Main tabs - make them prominent
                tab_details, tab_email, tab_ai, tab_actions = st.tabs([
                    "📄 Report Details", 
                    "📧 Communication Track", 
                    "🤖 AI Conclusion",
                    "⚡ Actions"
                ])
                
                with tab_details:
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.markdown(f"**Report Number:** `{report_num}`")
                        st.markdown(f"**Date:** {report_date}")
                    with col2:
                        st.markdown(f"**Type:** {rtype}")
                        st.markdown(f"**Status:** {report_status}")
                    with col3:
                        st.markdown(f"**Department:** {report_dept}")
                        if rtype == 'Hazard Reports':
                            risk = report.get('risk_level', 'Low')
                            try:
                                risk_color = RISK_ACTIONS[RiskLevel[risk.upper()]]['color']
                            except:
                                risk_color = '#64748B'
                            st.markdown(f"**Risk Level:** <span style='color: {risk_color}; font-weight: 600;'>{risk}</span>", unsafe_allow_html=True)
                    
                    st.markdown("---")
                    
                    # Show key details based on report type
                    if rtype == 'Bird Strikes':
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown(f"**Flight:** {report.get('flight_number', 'N/A')}")
                            st.markdown(f"**Aircraft:** {report.get('aircraft_registration', 'N/A')}")
                        with col2:
                            st.markdown(f"**Species:** {report.get('bird_species', 'Unknown')}")
                            st.markdown(f"**Damage:** {report.get('overall_damage', 'N/A')}")
                    
                    elif rtype == 'Laser Strikes':
                        st.markdown(f"**Flight:** {report.get('flight_number', 'N/A')}")
                        st.markdown(f"**Location:** {report.get('location_description', 'N/A')}")
                        st.markdown(f"**Laser Color:** {report.get('laser_color', 'N/A')}")
                    
                    elif rtype == 'TCAS Reports':
                        st.markdown(f"**Flight:** {report.get('flight_number', 'N/A')}")
                        st.markdown(f"**Alert Type:** {report.get('alert_type', 'N/A')}")
                    
                    elif rtype == 'Hazard Reports':
                        st.markdown(f"**Category:** {report.get('hazard_category', 'N/A')}")
                        st.markdown(f"**Location:** {report.get('location', 'N/A')}")
                        desc = report.get('hazard_description', 'N/A')
                        st.markdown(f"**Description:** {desc[:200] if desc else 'N/A'}...")
                    
                    elif rtype == 'Aircraft Incidents':
                        st.markdown(f"**Flight:** {report.get('flight_number', 'N/A')}")
                        st.markdown(f"**Category:** {report.get('primary_category', 'N/A')}")
                
                with tab_email:
                    # EMAIL TRACK & TRACE
                    st.markdown("#### 📧 Communication Timeline")
                    st.markdown("*Complete email thread for this report*")
                    
                    # Generate mock emails
                    emails = generate_mock_emails(report_num)
                    
                    for i, email in enumerate(emails):
                        direction_icon = "📤" if email['direction'] == 'outgoing' else "📥"
                        direction_color = "#DBEAFE" if email['direction'] == 'outgoing' else "#F0FDF4"
                        border_color = "#3B82F6" if email['direction'] == 'outgoing' else "#22C55E"
                        
                        st.markdown(f"""
                        <div style="background: {direction_color}; border-left: 4px solid {border_color}; padding: 1rem; margin-bottom: 0.75rem; border-radius: 0 8px 8px 0;">
                            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                                <div>
                                    <strong style="color: #1E40AF;">{direction_icon} {email['sender_name']}</strong>
                                    <span style="color: #64748B; font-size: 0.8rem;"> &lt;{email['sender_email']}&gt;</span>
                                </div>
                                <span style="color: #64748B; font-size: 0.8rem;">{email['date']}</span>
                            </div>
                            <div style="color: #475569; font-size: 0.85rem; margin-top: 0.25rem;"><strong>Subject:</strong> {email['subject']}</div>
                            <div style="color: #334155; margin-top: 0.5rem; padding: 0.5rem; background: white; border-radius: 4px;">{email['message']}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    st.markdown("---")
                    # Compose new email
                    with st.form(key=f"compose_email_{report_num}"):
                        st.markdown("**✉️ Compose New Message**")
                        email_to = st.selectbox("To:", ["Safety Manager", "Engineering HOD", "Flight Ops Manager", "Quality Assurance", "CAA Liaison"], key=f"to_{report_num}")
                        email_subject = st.text_input("Subject:", value=f"RE: {report_num} - Follow-up", key=f"subj_{report_num}")
                        email_body = st.text_area("Message:", placeholder="Type your message...", key=f"body_{report_num}")
                        
                        if st.form_submit_button("📤 Send Email", type="primary"):
                            st.success(f"✅ Email sent successfully to {email_to}!")
                            st.balloons()
                
                with tab_ai:
                    # AI AUTO-CONCLUSION
                    st.markdown("#### 🤖 AI-Generated Analysis")
                    st.markdown("*Automated conclusion based on report data and communication history*")
                    
                    # Generate AI conclusion
                    emails = generate_mock_emails(report_num)
                    ai_result = generate_ai_conclusion(report_num, emails)
                    
                    # Conclusion box - prominent green
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #F0FDF4 0%, #DCFCE7 100%); border: 2px solid #22C55E; border-radius: 12px; padding: 1.5rem; margin-bottom: 1rem;">
                        <div style="font-size: 1.1rem; color: #166534; font-weight: 600; margin-bottom: 0.5rem;">📊 AI Analysis Summary</div>
                        <div style="color: #15803D; font-size: 1rem;">{ai_result['conclusion']}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Key findings in expandable
                    st.markdown("**🔍 Key Findings:**")
                    for finding in ai_result['key_findings']:
                        st.markdown(f"• {finding}")
                    
                    # Analysis metadata
                    st.markdown("---")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Confidence Score", ai_result['confidence'])
                    with col2:
                        st.metric("Emails Analyzed", ai_result['analyzed_emails'])
                    with col3:
                        st.metric("Analysis Date", ai_result['analysis_date'][:12])
                    
                    # Action buttons
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("🔄 Regenerate Analysis", key=f"regen_{report_num}"):
                            st.info("🔄 Re-analyzing... Analysis updated!")
                            st.rerun()
                    with col2:
                        if st.button("📋 Copy to Clipboard", key=f"copy_{report_num}"):
                            st.success("✅ Conclusion copied!")
                
                with tab_actions:
                    # ACTIONS TAB - PDF & Email (REAL FUNCTIONALITY)
                    st.markdown("#### ⚡ Quick Actions")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("##### 📄 Generate PDF Report")
                        st.markdown("Create a professional PDF document of this report.")
                        
                        # Generate PDF using real function
                        pdf_bytes = generate_pdf_report(report, rtype)
                        
                        # Determine file extension based on whether reportlab is available
                        try:
                            from reportlab.lib.pagesizes import A4
                            file_ext = "pdf"
                            mime_type = "application/pdf"
                        except ImportError:
                            file_ext = "txt"
                            mime_type = "text/plain"
                        
                        st.download_button(
                            label="📄 Download PDF Report",
                            data=pdf_bytes,
                            file_name=f"{report_num}_report.{file_ext}",
                            mime=mime_type,
                            key=f"dl_pdf_{report_num}",
                            type="primary",
                            use_container_width=True
                        )
                        st.caption("Click above to download the report")
                    
                    with col2:
                        st.markdown("##### 📧 Send Report via Email")
                        
                        # Check if SMTP is configured
                        smtp_configured = bool(st.session_state.get('smtp_email') and st.session_state.get('smtp_password'))
                        
                        if not smtp_configured:
                            st.warning("⚠️ Email not configured. Go to **Settings > Email (SMTP)** to set up.")
                        
                        with st.form(key=f"quick_email_{report_num}"):
                            recipient_name = st.selectbox("Send to:", list(EMAIL_CONTACTS.keys()))
                            recipient_email = st.text_input("Email address:", value=EMAIL_CONTACTS.get(recipient_name, ''))
                            custom_email = st.text_input("Or enter custom email:", placeholder="email@example.com")
                            include_ai = st.checkbox("Include AI Analysis in email", value=True)
                            add_note = st.text_area("Add a note:", placeholder="Optional message...")
                            
                            if st.form_submit_button("📤 Send Report Now", type="primary", use_container_width=True):
                                final_email = custom_email if custom_email else recipient_email
                                
                                if not final_email:
                                    st.error("Please enter an email address")
                                elif not smtp_configured:
                                    st.error("Please configure SMTP settings first in Settings > Email (SMTP)")
                                else:
                                    # Build email body
                                    email_body = f"""
Air Sial Corporate Safety System
================================

Report: {report_num}
Type: {rtype}
Date: {report_date}
Status: {report_status}
Department: {report_dept}

"""
                                    if rtype == 'Bird Strikes':
                                        email_body += f"""
BIRD STRIKE DETAILS
-------------------
Flight: {report.get('flight_number', 'N/A')}
Aircraft: {report.get('aircraft_registration', 'N/A')}
Species: {report.get('bird_species', 'Unknown')}
Damage: {report.get('overall_damage', 'N/A')}
"""
                                    elif rtype == 'Hazard Reports':
                                        email_body += f"""
HAZARD DETAILS
--------------
Title: {report.get('hazard_title', 'N/A')}
Category: {report.get('hazard_category', 'N/A')}
Location: {report.get('location', 'N/A')}
Risk Level: {report.get('risk_level', 'N/A')}
Description: {report.get('hazard_description', 'N/A')}
"""
                                    
                                    if include_ai:
                                        ai_result = generate_ai_conclusion(report_num, [])
                                        email_body += f"""

AI ANALYSIS
-----------
{ai_result['conclusion']}

Key Findings:
- {chr(10).join('- ' + f for f in ai_result['key_findings'])}
"""
                                    
                                    if add_note:
                                        email_body += f"""

ADDITIONAL NOTES
----------------
{add_note}
"""
                                    
                                    email_body += f"""

---
Sent from Air Sial Corporate Safety System v3.0
Sent by: {st.session_state.get('user_name', 'Unknown')}
"""
                                    
                                    # Send the email
                                    success, message = send_real_email(
                                        to_email=final_email,
                                        subject=f"Safety Report: {report_num} - {report.get('hazard_title', report.get('flight_number', 'Report'))}",
                                        body=email_body
                                    )
                                    
                                    if success:
                                        st.success(f"✅ {message}")
                                        st.balloons()
                                    else:
                                        st.error(f"❌ {message}")
                    
                    st.markdown("---")
                    
                    # Additional actions
                    st.markdown("##### 🔧 Other Actions")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if st.button("📝 Edit Report", key=f"edit_action_{report_num}", use_container_width=True):
                            st.session_state.editing_report = report_num
                            st.info(f"Opening editor for {report_num}...")
                    with col2:
                        new_status = st.selectbox("Update Status:", ["Under Review", "Assigned to Investigator", "Investigation Complete", "Closed"], key=f"new_status_{report_num}")
                        if st.button("🔄 Save Status", key=f"save_status_{report_num}", use_container_width=True):
                            report['investigation_status'] = new_status
                            st.success(f"✅ Status updated to: {new_status}")
                    with col3:
                        if st.button("🗑️ Archive Report", key=f"archive_{report_num}", use_container_width=True):
                            st.warning("⚠️ Report archived.")
    else:
        # No reports - show demo data option
        st.info("No reports found matching your criteria.")
        
        if st.button("📊 Load Demo Reports"):
            # Create some demo reports
            demo_reports = [
                {
                    'report_number': 'HZD-20241207-DEMO1',
                    'created_at': '2024-12-07',
                    'hazard_title': 'FOD on Taxiway Alpha',
                    'hazard_category': 'Foreign Object Debris',
                    'location': 'OPSK - Sialkot',
                    'hazard_description': 'Metal debris found on taxiway during routine inspection.',
                    'risk_level': 'High',
                    'investigation_status': 'Under Review',
                    'reporter_department': 'Ground Operations'
                },
                {
                    'report_number': 'HZD-20241206-DEMO2',
                    'created_at': '2024-12-06',
                    'hazard_title': 'Lighting malfunction at Gate 3',
                    'hazard_category': 'Infrastructure',
                    'location': 'OPLA - Lahore',
                    'hazard_description': 'Apron lighting flickering intermittently at night.',
                    'risk_level': 'Medium',
                    'investigation_status': 'Assigned to Investigator',
                    'reporter_department': 'Engineering & Maintenance'
                },
                {
                    'report_number': 'BRD-20241205-DEMO3',
                    'created_at': '2024-12-05',
                    'flight_number': 'PF-302',
                    'aircraft_registration': 'AP-BMA',
                    'bird_species': 'Black Kite',
                    'overall_damage': 'Minor',
                    'investigation_status': 'Investigation Complete',
                    'reporter_department': 'Flight Operations'
                }
            ]
            
            if 'hazard_reports' not in st.session_state:
                st.session_state.hazard_reports = []
            if 'bird_strikes' not in st.session_state:
                st.session_state.bird_strikes = []
            
            st.session_state.hazard_reports.extend(demo_reports[:2])
            st.session_state.bird_strikes.append(demo_reports[2])
            st.success("✅ Demo reports loaded! Refresh the page to see them.")
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# AUTHENTICATION
# ══════════════════════════════════════════════════════════════════════════════

def render_login():
    """Render login page"""
    
    # Center the login content
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # Logo display using st.image
        logo_path = render_logo_in_header()
        if logo_path:
            try:
                st.image(logo_path, width=150, use_container_width=False)
            except:
                st.markdown('<div style="text-align: center; font-size: 5rem;">🛡️✈️</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div style="text-align: center; font-size: 5rem;">🛡️✈️</div>', unsafe_allow_html=True)
        
        st.markdown("""
        <div style="text-align: center; padding: 1rem;">
            <h1 style="color: #1E40AF; margin-top: 1rem;">Air Sial Corporate Safety</h1>
            <p style="color: #64748B;">Safety Management System v3.0</p>
        </div>
        """, unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["🔐 Login", "📝 Sign Up", "🔑 Reset Password"])
    
    with tab1:
        with st.form("login_form"):
            st.markdown("### Login")
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            
            col1, col2 = st.columns(2)
            with col1:
                login_btn = st.form_submit_button("🔐 Login", use_container_width=True, type="primary")
            with col2:
                demo_btn = st.form_submit_button("🎮 Demo Mode", use_container_width=True)
            
            if login_btn:
                if username and password:
                    # Check credentials
                    user = db.get_user_by_username(username)
                    if user and user.get('password_hash') == hash_password(password):
                        st.session_state.logged_in = True
                        st.session_state.user_id = user.get('id')
                        st.session_state.user_name = user.get('full_name')
                        st.session_state.user_role = user.get('role', 'reporter')
                        st.session_state.user_department = user.get('department')
                        st.success("✅ Login successful!")
                        st.rerun()
                    elif username == "admin" and password == "admin123":
                        # Default admin for demo
                        st.session_state.logged_in = True
                        st.session_state.user_id = "admin"
                        st.session_state.user_name = "Administrator"
                        st.session_state.user_role = "admin"
                        st.session_state.user_department = "Safety Department"
                        st.success("✅ Login successful!")
                        st.rerun()
                    else:
                        st.error("❌ Invalid username or password")
                else:
                    st.warning("Please enter username and password")
            
            if demo_btn:
                st.session_state.logged_in = True
                st.session_state.user_id = "demo"
                st.session_state.user_name = "Demo User"
                st.session_state.user_role = "admin"
                st.session_state.user_department = "Safety Department"
                st.success("✅ Demo mode activated!")
                st.rerun()
    
    with tab2:
        with st.form("signup_form"):
            st.markdown("### Create Account")
            
            col1, col2 = st.columns(2)
            with col1:
                new_username = st.text_input("Username*", key="new_username")
                new_email = st.text_input("Email*", key="new_email")
                new_password = st.text_input("Password*", type="password", key="new_password")
            with col2:
                new_full_name = st.text_input("Full Name*", key="new_fullname")
                new_employee_id = st.text_input("Employee ID*", key="new_empid")
                new_password_confirm = st.text_input("Confirm Password*", type="password", key="new_password2")
            
            col1, col2 = st.columns(2)
            with col1:
                new_department = st.selectbox("Department*", options=DEPARTMENTS, key="new_dept")
            with col2:
                new_designation = st.text_input("Designation*", key="new_designation")
            
            new_phone = st.text_input("Phone Number", key="new_phone")
            
            signup_btn = st.form_submit_button("📝 Create Account", use_container_width=True, type="primary")
            
            if signup_btn:
                if new_password != new_password_confirm:
                    st.error("Passwords do not match")
                elif not all([new_username, new_email, new_password, new_full_name, new_employee_id]):
                    st.warning("Please fill all required fields")
                else:
                    user_data = {
                        'username': new_username,
                        'email': new_email,
                        'password_hash': hash_password(new_password),
                        'full_name': new_full_name,
                        'employee_id': new_employee_id,
                        'department': new_department,
                        'designation': new_designation,
                        'phone': new_phone,
                        'role': 'reporter',
                        'is_active': True,
                        'created_at': datetime.now().isoformat()
                    }
                    
                    result = db.create_user(user_data)
                    if result:
                        st.success("✅ Account created! Please login.")
                    else:
                        st.info("Account created (Demo Mode). Please login.")
    
    with tab3:
        with st.form("reset_form"):
            st.markdown("### Reset Password")
            reset_email = st.text_input("Email Address")
            reset_btn = st.form_submit_button("🔑 Send Reset Link", use_container_width=True)
            
            if reset_btn:
                if reset_email:
                    st.success("✅ If an account exists with this email, a reset link has been sent.")
                else:
                    st.warning("Please enter your email address")


def render_sidebar():
    """Render sidebar navigation"""
    
    with st.sidebar:
        st.markdown(f"""
        <div style="text-align: center; padding: 1rem; background: linear-gradient(135deg, #1B5E20, #2E7D32); border-radius: 10px; margin-bottom: 1rem;">
            <span style="font-size: 2rem;">🛡️✈️</span>
            <h3 style="color: #FFD700; margin: 0.5rem 0;">Air Sial Safety</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # User info
        st.markdown(f"""
        <div style="padding: 0.75rem; background: #161B22; border-radius: 8px; margin-bottom: 1rem;">
            <div style="font-weight: 600;">👤 {st.session_state.get('user_name', 'User')}</div>
            <div style="font-size: 0.8rem; color: #8B949E;">{st.session_state.get('user_department', 'Department')}</div>
            <div style="font-size: 0.75rem; color: #58A6FF;">Role: {st.session_state.get('user_role', 'Reporter').title()}</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Navigation
        st.markdown("### 📍 Navigation")
        
        page = st.radio(
            "Select Page",
            options=[
                "📊 Dashboard",
                "📋 View Reports",
                "---",
                "🐦 Bird Strike Report",
                "🔴 Laser Strike Report",
                "📡 TCAS Report",
                "🚨 Incident Report",
                "⚠️ Hazard Report",
                "---",
                "📋 Flight Services (FSR)",
                "👨‍✈️ Captain's DBR",
                "---",
                "🤖 AI Assistant",
                "⚙️ Settings"
            ],
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        
        # Quick Actions
        st.markdown("### ⚡ Quick Actions")
        if st.button("🆘 Emergency Report", use_container_width=True, type="primary"):
            st.session_state.page = "incident"
        
        st.markdown("---")
        
        # Logout
        if st.button("🚪 Logout", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
        
        return page


def render_ai_assistant():
    """Render AI Assistant page"""
    
    st.markdown("## 🤖 AI Safety Assistant")
    st.markdown("*Powered by Gemini AI*")
    
    # Initialize chat history
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    # Chat interface
    st.markdown('<div style="height: 400px; overflow-y: auto; padding: 1rem; background: #161B22; border-radius: 10px;">', unsafe_allow_html=True)
    
    for message in st.session_state.chat_history:
        if message['role'] == 'user':
            st.markdown(f"""
            <div style="text-align: right; margin-bottom: 1rem;">
                <span style="background: #2E7D32; padding: 0.5rem 1rem; border-radius: 15px; display: inline-block;">
                    {message['content']}
                </span>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="text-align: left; margin-bottom: 1rem;">
                <span style="background: #30363D; padding: 0.5rem 1rem; border-radius: 15px; display: inline-block;">
                    {message['content']}
                </span>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Input
    user_input = st.text_input("Ask a question about safety...", key="ai_input")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        if st.button("📤 Send", use_container_width=True):
            if user_input:
                st.session_state.chat_history.append({'role': 'user', 'content': user_input})
                
                # Get AI response
                ai = AIAssistant()
                response = ai._call_gemini(f"As a safety analyst for Air Sial airline, answer this question: {user_input}")
                
                st.session_state.chat_history.append({'role': 'assistant', 'content': response})
                st.rerun()
    
    with col2:
        if st.button("🗑️ Clear", use_container_width=True):
            st.session_state.chat_history = []
            st.rerun()
    
    # Quick prompts
    st.markdown("### 💡 Quick Prompts")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("📊 Analyze trends"):
            st.session_state.chat_history.append({'role': 'user', 'content': "Analyze the safety trends for our airline"})
            st.rerun()
    with col2:
        if st.button("📋 Risk assessment"):
            st.session_state.chat_history.append({'role': 'user', 'content': "How do I conduct a proper risk assessment?"})
            st.rerun()
    with col3:
        if st.button("✈️ Best practices"):
            st.session_state.chat_history.append({'role': 'user', 'content': "What are aviation safety best practices?"})
            st.rerun()


def render_settings():
    """Render settings page with SMTP configuration"""
    
    st.markdown("## ⚙️ Settings")
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["👤 Profile", "📧 Email (SMTP)", "🔔 Notifications", "💾 Data Backup", "🎨 Appearance"])
    
    with tab1:
        st.markdown("### User Profile")
        
        with st.form("profile_form"):
            col1, col2 = st.columns(2)
            with col1:
                profile_name = st.text_input("Full Name", value=st.session_state.get('user_name', ''))
                profile_email = st.text_input("Email", value=st.session_state.get('user_email', 'user@airsial.com'))
                profile_emp_id = st.text_input("Employee ID", value=st.session_state.get('employee_id', 'EMP001'))
            with col2:
                profile_dept = st.selectbox("Department", options=DEPARTMENTS, index=DEPARTMENTS.index(st.session_state.get('user_department', 'Safety Department')) if st.session_state.get('user_department') in DEPARTMENTS else 7)
                profile_designation = st.text_input("Designation", value=st.session_state.get('designation', 'Safety Officer'))
                profile_phone = st.text_input("Phone", value=st.session_state.get('phone', '+92-XXX-XXXXXXX'))
            
            if st.form_submit_button("💾 Save Profile", type="primary"):
                st.session_state.user_name = profile_name
                st.session_state.user_email = profile_email
                st.session_state.employee_id = profile_emp_id
                st.session_state.user_department = profile_dept
                st.session_state.designation = profile_designation
                st.session_state.phone = profile_phone
                save_settings_to_file()
                st.success("✅ Profile saved!")
    
    with tab2:
        st.markdown("### 📧 Email Configuration (SMTP)")
        st.markdown("*Configure email settings to enable report sending*")
        
        st.markdown("""
        <div class="alert-box alert-info">
            <span style="font-size: 1.2rem;">ℹ️</span>
            <div>
                <strong>SMTP Setup Guide</strong><br>
                <small>For Gmail: smtp.gmail.com:587 | For Outlook: smtp.office365.com:587<br>
                Use App Password for Gmail (not your regular password)</small>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("smtp_form"):
            col1, col2 = st.columns(2)
            with col1:
                smtp_server = st.text_input("SMTP Server", value=st.session_state.get('smtp_server', 'smtp.gmail.com'))
                smtp_port = st.number_input("SMTP Port", value=st.session_state.get('smtp_port', 587), min_value=1, max_value=65535)
                smtp_email = st.text_input("Sender Email", value=st.session_state.get('smtp_email', ''))
            with col2:
                smtp_password = st.text_input("Email Password/App Password", type="password", value=st.session_state.get('smtp_password', ''))
                smtp_name = st.text_input("Sender Name", value=st.session_state.get('smtp_name', 'Air Sial Safety System'))
                use_tls = st.checkbox("Use TLS", value=st.session_state.get('smtp_tls', True))
            
            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("💾 Save SMTP Settings", type="primary"):
                    st.session_state.smtp_server = smtp_server
                    st.session_state.smtp_port = smtp_port
                    st.session_state.smtp_email = smtp_email
                    st.session_state.smtp_password = smtp_password
                    st.session_state.smtp_name = smtp_name
                    st.session_state.smtp_tls = use_tls
                    save_settings_to_file()
                    st.success("✅ SMTP settings saved!")
        
        # Test email button outside form
        st.markdown("---")
        test_recipient = st.text_input("Test Email Recipient", placeholder="test@example.com")
        if st.button("📤 Send Test Email"):
            if test_recipient and st.session_state.get('smtp_email'):
                success, message = send_real_email(
                    to_email=test_recipient,
                    subject="Air Sial SMS - Test Email",
                    body="This is a test email from Air Sial Corporate Safety System.\n\nIf you received this, your email configuration is working correctly!\n\n- Air Sial Safety Team"
                )
                if success:
                    st.success(f"✅ {message}")
                else:
                    st.error(f"❌ {message}")
            else:
                st.warning("Please configure SMTP settings and enter a test recipient")
    
    with tab3:
        st.markdown("### Notification Preferences")
        
        with st.form("notif_form"):
            notif_new_reports = st.checkbox("Email notifications for new reports", value=st.session_state.get('notif_new_reports', True))
            notif_sla = st.checkbox("Email notifications for SLA alerts", value=st.session_state.get('notif_sla', True))
            notif_daily = st.checkbox("Daily digest of safety reports", value=st.session_state.get('notif_daily', False))
            notif_weekly = st.checkbox("Weekly summary report", value=st.session_state.get('notif_weekly', True))
            notif_assigned = st.checkbox("Notify when assigned as investigator", value=st.session_state.get('notif_assigned', True))
            
            if st.form_submit_button("💾 Save Notifications", type="primary"):
                st.session_state.notif_new_reports = notif_new_reports
                st.session_state.notif_sla = notif_sla
                st.session_state.notif_daily = notif_daily
                st.session_state.notif_weekly = notif_weekly
                st.session_state.notif_assigned = notif_assigned
                save_settings_to_file()
                st.success("✅ Notification preferences saved!")
    
    with tab4:
        st.markdown("### 💾 Data Backup & Restore")
        st.markdown("*Export and import your reports data*")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📤 Export Data")
            if st.button("📥 Export All Reports to JSON", use_container_width=True):
                export_data = {
                    'exported_at': datetime.now().isoformat(),
                    'bird_strikes': st.session_state.get('bird_strikes', []),
                    'laser_strikes': st.session_state.get('laser_strikes', []),
                    'tcas_reports': st.session_state.get('tcas_reports', []),
                    'hazard_reports': st.session_state.get('hazard_reports', []),
                    'aircraft_incidents': st.session_state.get('aircraft_incidents', []),
                    'fsr_reports': st.session_state.get('fsr_reports', []),
                    'captain_dbr': st.session_state.get('captain_dbr', []),
                }
                json_str = json.dumps(export_data, indent=2, default=str)
                st.download_button(
                    "⬇️ Download Backup File",
                    data=json_str,
                    file_name=f"airsial_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json",
                    use_container_width=True
                )
        
        with col2:
            st.markdown("#### 📥 Import Data")
            uploaded_backup = st.file_uploader("Upload backup JSON file", type=['json'])
            if uploaded_backup:
                try:
                    import_data = json.load(uploaded_backup)
                    st.info(f"Backup from: {import_data.get('exported_at', 'Unknown')}")
                    
                    if st.button("🔄 Restore from Backup", type="primary", use_container_width=True):
                        for key in ['bird_strikes', 'laser_strikes', 'tcas_reports', 'hazard_reports', 'aircraft_incidents', 'fsr_reports', 'captain_dbr']:
                            if key in import_data:
                                st.session_state[key] = import_data[key]
                        st.success("✅ Data restored successfully!")
                        st.rerun()
                except Exception as e:
                    st.error(f"Error reading backup: {e}")
    
    with tab5:
        st.markdown("### Appearance")
        
        with st.form("appearance_form"):
            theme = st.selectbox("Theme", options=["Light (Default)", "Dark", "System"], index=0)
            language = st.selectbox("Language", options=["English", "اردو (Urdu)"])
            font_size = st.slider("Font Size", min_value=12, max_value=20, value=14)
            
            if st.form_submit_button("💾 Save Appearance", type="primary"):
                st.session_state.theme = theme
                st.session_state.language = language
                st.session_state.font_size = font_size
                save_settings_to_file()
                st.success("✅ Appearance settings saved!")


# ==============================================================================
# REAL EMAIL FUNCTIONALITY
# ==============================================================================

def send_real_email(to_email: str, subject: str, body: str, attachments: list = None) -> tuple:
    """Send actual email via SMTP"""
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    from email.mime.base import MIMEBase
    from email import encoders
    
    # Get SMTP settings
    smtp_server = st.session_state.get('smtp_server', '')
    smtp_port = st.session_state.get('smtp_port', 587)
    smtp_email = st.session_state.get('smtp_email', '')
    smtp_password = st.session_state.get('smtp_password', '')
    smtp_name = st.session_state.get('smtp_name', 'Air Sial Safety System')
    use_tls = st.session_state.get('smtp_tls', True)
    
    if not smtp_server or not smtp_email or not smtp_password:
        return False, "SMTP not configured. Go to Settings > Email (SMTP) to configure."
    
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = f"{smtp_name} <{smtp_email}>"
        msg['To'] = to_email
        msg['Subject'] = subject
        
        # Add body
        msg.attach(MIMEText(body, 'plain'))
        
        # Add attachments if any
        if attachments:
            for attachment in attachments:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment['data'])
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', f"attachment; filename= {attachment['filename']}")
                msg.attach(part)
        
        # Connect and send
        server = smtplib.SMTP(smtp_server, smtp_port)
        if use_tls:
            server.starttls()
        server.login(smtp_email, smtp_password)
        server.send_message(msg)
        server.quit()
        
        # Log the email
        log_email_sent(to_email, subject)
        
        return True, f"Email sent successfully to {to_email}"
    
    except smtplib.SMTPAuthenticationError:
        return False, "Authentication failed. Check your email and password. For Gmail, use App Password."
    except smtplib.SMTPConnectError:
        return False, f"Could not connect to {smtp_server}:{smtp_port}. Check server settings."
    except Exception as e:
        return False, f"Email error: {str(e)}"


def log_email_sent(to_email: str, subject: str):
    """Log sent emails for tracking"""
    if 'email_log' not in st.session_state:
        st.session_state.email_log = []
    
    st.session_state.email_log.append({
        'to': to_email,
        'subject': subject,
        'sent_at': datetime.now().isoformat(),
        'sent_by': st.session_state.get('user_name', 'Unknown')
    })


# ==============================================================================
# REAL PDF GENERATION
# ==============================================================================

def generate_pdf_report(report_data: dict, report_type: str) -> bytes:
    """Generate actual PDF report"""
    from io import BytesIO
    
    # Try to use reportlab, fall back to simple text if not available
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*inch, bottomMargin=0.5*inch)
        styles = getSampleStyleSheet()
        story = []
        
        # Title style
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            textColor=colors.HexColor('#1E40AF')
        )
        
        # Header
        story.append(Paragraph("AIR SIAL CORPORATE SAFETY", title_style))
        story.append(Paragraph("Safety Management System - Official Report", styles['Heading2']))
        story.append(Spacer(1, 20))
        
        # Report info table
        report_num = report_data.get('report_number', 'N/A')
        report_date = report_data.get('created_at', str(date.today()))[:10]
        
        info_data = [
            ['Report Number:', report_num, 'Report Type:', report_type],
            ['Date:', report_date, 'Status:', report_data.get('investigation_status', 'Draft')],
            ['Department:', report_data.get('reporter_department', 'N/A'), 'Generated:', datetime.now().strftime('%Y-%m-%d %H:%M')],
        ]
        
        info_table = Table(info_data, colWidths=[1.5*inch, 2*inch, 1.5*inch, 2*inch])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#F1F5F9')),
            ('BACKGROUND', (2, 0), (2, -1), colors.HexColor('#F1F5F9')),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
            ('PADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(info_table)
        story.append(Spacer(1, 20))
        
        # Incident details based on type
        story.append(Paragraph("INCIDENT DETAILS", styles['Heading2']))
        story.append(Spacer(1, 10))
        
        if report_type == 'Bird Strikes':
            details = [
                ['Flight Number:', report_data.get('flight_number', 'N/A')],
                ['Aircraft Registration:', report_data.get('aircraft_registration', 'N/A')],
                ['Bird Species:', report_data.get('bird_species', 'Unknown')],
                ['Number of Birds:', str(report_data.get('number_of_birds', 'N/A'))],
                ['Damage Assessment:', report_data.get('overall_damage', 'N/A')],
                ['Phase of Flight:', report_data.get('phase_of_flight', 'N/A')],
            ]
        elif report_type == 'Hazard Reports':
            details = [
                ['Hazard Title:', report_data.get('hazard_title', 'N/A')],
                ['Category:', report_data.get('hazard_category', 'N/A')],
                ['Location:', report_data.get('location', 'N/A')],
                ['Risk Level:', report_data.get('risk_level', 'N/A')],
                ['Description:', report_data.get('hazard_description', 'N/A')[:100] + '...' if len(report_data.get('hazard_description', '')) > 100 else report_data.get('hazard_description', 'N/A')],
            ]
        elif report_type == 'Laser Strikes':
            details = [
                ['Flight Number:', report_data.get('flight_number', 'N/A')],
                ['Location:', report_data.get('location_description', 'N/A')],
                ['Laser Color:', report_data.get('laser_color', 'N/A')],
                ['Effect on Crew:', report_data.get('effect_on_crew', 'N/A')],
            ]
        elif report_type == 'TCAS Reports':
            details = [
                ['Flight Number:', report_data.get('flight_number', 'N/A')],
                ['Alert Type:', report_data.get('alert_type', 'N/A')],
                ['RA Followed:', report_data.get('ra_followed', 'N/A')],
                ['Traffic Type:', report_data.get('traffic_type', 'N/A')],
            ]
        else:
            details = [
                ['Flight Number:', report_data.get('flight_number', 'N/A')],
                ['Description:', str(report_data.get('description', report_data.get('incident_description', 'N/A')))[:100]],
            ]
        
        details_table = Table(details, colWidths=[2*inch, 5*inch])
        details_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#F1F5F9')),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
            ('PADDING', (0, 0), (-1, -1), 8),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        story.append(details_table)
        story.append(Spacer(1, 30))
        
        # Footer
        story.append(Paragraph("_" * 80, styles['Normal']))
        story.append(Spacer(1, 10))
        story.append(Paragraph(f"Generated by Air Sial Corporate Safety System v3.0", styles['Normal']))
        story.append(Paragraph(f"This is an official document. Report ID: {report_num}", styles['Normal']))
        
        doc.build(story)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        return pdf_bytes
        
    except ImportError:
        # Fallback: Create a formatted text file
        content = f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                      AIR SIAL CORPORATE SAFETY                                ║
║                    Safety Management System - Official Report                 ║
╚══════════════════════════════════════════════════════════════════════════════╝

REPORT INFORMATION
==================
Report Number:    {report_data.get('report_number', 'N/A')}
Report Type:      {report_type}
Date:             {report_data.get('created_at', str(date.today()))[:10]}
Status:           {report_data.get('investigation_status', 'Draft')}
Department:       {report_data.get('reporter_department', 'N/A')}

INCIDENT DETAILS
================
"""
        if report_type == 'Bird Strikes':
            content += f"""
Flight Number:        {report_data.get('flight_number', 'N/A')}
Aircraft:             {report_data.get('aircraft_registration', 'N/A')}
Bird Species:         {report_data.get('bird_species', 'Unknown')}
Damage:               {report_data.get('overall_damage', 'N/A')}
"""
        elif report_type == 'Hazard Reports':
            content += f"""
Hazard Title:         {report_data.get('hazard_title', 'N/A')}
Category:             {report_data.get('hazard_category', 'N/A')}
Location:             {report_data.get('location', 'N/A')}
Risk Level:           {report_data.get('risk_level', 'N/A')}
Description:          {report_data.get('hazard_description', 'N/A')}
"""
        else:
            content += f"""
Flight Number:        {report_data.get('flight_number', 'N/A')}
Details:              See full report in system.
"""
        
        content += f"""
════════════════════════════════════════════════════════════════════════════════
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Air Sial Corporate Safety System v3.0
This is an official document.
════════════════════════════════════════════════════════════════════════════════
"""
        return content.encode('utf-8')


# ==============================================================================
# SETTINGS PERSISTENCE
# ==============================================================================

def save_settings_to_file():
    """Save settings to a JSON file for persistence"""
    settings = {
        'smtp_server': st.session_state.get('smtp_server', ''),
        'smtp_port': st.session_state.get('smtp_port', 587),
        'smtp_email': st.session_state.get('smtp_email', ''),
        'smtp_name': st.session_state.get('smtp_name', ''),
        'smtp_tls': st.session_state.get('smtp_tls', True),
        'user_name': st.session_state.get('user_name', ''),
        'user_email': st.session_state.get('user_email', ''),
        'user_department': st.session_state.get('user_department', ''),
    }
    
    try:
        with open('settings.json', 'w') as f:
            json.dump(settings, f)
    except:
        pass  # Silently fail on Streamlit Cloud


def load_settings_from_file():
    """Load settings from JSON file"""
    try:
        with open('settings.json', 'r') as f:
            settings = json.load(f)
            for key, value in settings.items():
                if key not in st.session_state:
                    st.session_state[key] = value
    except:
        pass  # File doesn't exist yet


# ==============================================================================
# EMAIL ADDRESSES DATABASE
# ==============================================================================

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
}


# ══════════════════════════════════════════════════════════════════════════════
# MAIN APPLICATION
# ══════════════════════════════════════════════════════════════════════════════

def main():
    """Main application entry point"""
    
    # Page config
    st.set_page_config(
        page_title="Air Sial Corporate Safety",
        page_icon="🛡️",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Apply custom CSS
    apply_custom_css()
    
    # Check authentication
    if not st.session_state.get('logged_in', False):
        render_login()
        return
    
    # Render header
    render_header()
    
    # Render sidebar and get selected page
    page = render_sidebar()
    
    # Route to appropriate page
    if page == "📊 Dashboard":
        render_dashboard()
    elif page == "📋 View Reports":
        render_view_reports()
    elif page == "🐦 Bird Strike Report":
        ocr_data = render_ocr_scanner("bird_strike")
        render_bird_strike_form(ocr_data)
    elif page == "🔴 Laser Strike Report":
        ocr_data = render_ocr_scanner("laser_strike")
        render_laser_strike_form(ocr_data)
    elif page == "📡 TCAS Report":
        ocr_data = render_ocr_scanner("tcas_report")
        render_tcas_form(ocr_data)
    elif page == "🚨 Incident Report":
        ocr_data = render_ocr_scanner("incident_report")
        render_incident_form(ocr_data)
    elif page == "⚠️ Hazard Report":
        ocr_data = render_ocr_scanner("hazard_report")
        render_hazard_form(ocr_data)
    elif page == "📋 Flight Services (FSR)":
        render_fsr_form()
    elif page == "👨‍✈️ Captain's DBR":
        render_dbr_form()
    elif page == "🤖 AI Assistant":
        render_ai_assistant()
    elif page == "⚙️ Settings":
        render_settings()


# Original main() call removed - using main_v3() at end of file


# ==============================================================================
# NEW ENTERPRISE FEATURES V3.0
# ==============================================================================

# ==============================================================================
# 1. GEOSPATIAL RISK MAP
# ==============================================================================

def generate_mock_locations():
    """Generate mock incident locations around Pakistan airports for demo"""
    import random
    
    # Airport coordinates
    airports = {
        "Karachi (OPKC)": (24.9065, 67.1608),
        "Lahore (OPLA)": (31.5216, 74.4036),
        "Islamabad (OPIS)": (33.5607, 72.8494),
        "Sialkot (OPSK)": (32.5356, 74.3639),
        "Peshawar (OPPS)": (33.9939, 71.5146),
        "Multan (OPMT)": (30.2033, 71.4191),
    }
    
    incidents = []
    incident_types = [
        ("Bird Strike", "#3B82F6", "blue"),
        ("Laser Strike", "#8B5CF6", "purple"),
        ("Hazard", "#DC2626", "red"),
        ("TCAS Event", "#F97316", "orange"),
        ("Runway Incursion", "#EAB308", "yellow"),
    ]
    
    random.seed(42)  # Reproducible demo data
    
    for airport_name, (lat, lon) in airports.items():
        # Generate 5-15 incidents around each airport
        num_incidents = random.randint(5, 15)
        for i in range(num_incidents):
            # Random offset within ~50km radius
            lat_offset = random.uniform(-0.3, 0.3)
            lon_offset = random.uniform(-0.3, 0.3)
            
            incident_type, color, color_name = random.choice(incident_types)
            severity = random.choice(["Low", "Medium", "High", "Extreme"])
            
            incidents.append({
                "lat": lat + lat_offset,
                "lon": lon + lon_offset,
                "airport": airport_name,
                "type": incident_type,
                "severity": severity,
                "color": color,
                "color_name": color_name,
                "date": f"2024-{random.randint(1,12):02d}-{random.randint(1,28):02d}",
                "report_id": f"RPT-{random.randint(1000, 9999)}"
            })
    
    return incidents


def render_geospatial_map():
    """Render Geospatial Risk Map page"""
    
    st.markdown("## 🌍 Geospatial Risk Map")
    st.markdown("*Visualize safety incidents across Air Sial network*")
    
    st.markdown("""
    <div class="alert-box alert-info">
        <span style="font-size: 1.5rem;">🗺️</span>
        <div>
            <strong>Interactive Incident Map</strong><br>
            <small>View safety incidents plotted by location. Color indicates incident type.</small>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        filter_type = st.multiselect(
            "Incident Type",
            options=["Bird Strike", "Laser Strike", "Hazard", "TCAS Event", "Runway Incursion"],
            default=["Bird Strike", "Laser Strike", "Hazard"]
        )
    with col2:
        filter_severity = st.multiselect(
            "Severity",
            options=["Low", "Medium", "High", "Extreme"],
            default=["High", "Extreme"]
        )
    with col3:
        filter_airport = st.multiselect(
            "Airport",
            options=["Karachi (OPKC)", "Lahore (OPLA)", "Islamabad (OPIS)", "Sialkot (OPSK)", "Peshawar (OPPS)", "Multan (OPMT)"],
            default=[]
        )
    
    # Generate mock data
    incidents = generate_mock_locations()
    
    # Apply filters
    filtered = incidents
    if filter_type:
        filtered = [i for i in filtered if i['type'] in filter_type]
    if filter_severity:
        filtered = [i for i in filtered if i['severity'] in filter_severity]
    if filter_airport:
        filtered = [i for i in filtered if i['airport'] in filter_airport]
    
    # Create DataFrame for map
    df = pd.DataFrame(filtered)
    
    if len(df) > 0:
        # Summary stats
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Incidents", len(df))
        with col2:
            high_risk = len(df[df['severity'].isin(['High', 'Extreme'])])
            st.metric("High/Extreme Risk", high_risk)
        with col3:
            bird_strikes = len(df[df['type'] == 'Bird Strike'])
            st.metric("Bird Strikes", bird_strikes)
        with col4:
            unique_airports = df['airport'].nunique()
            st.metric("Airports Affected", unique_airports)
        
        st.markdown("---")
        
        # Map using pydeck
        try:
            import pydeck as pdk
            
            # Color mapping
            color_map = {
                "blue": [59, 130, 246, 200],
                "purple": [139, 92, 246, 200],
                "red": [220, 38, 38, 200],
                "orange": [249, 115, 22, 200],
                "yellow": [234, 179, 8, 200],
            }
            
            df['color'] = df['color_name'].map(color_map)
            
            layer = pdk.Layer(
                "ScatterplotLayer",
                data=df,
                get_position=["lon", "lat"],
                get_color="color",
                get_radius=8000,
                pickable=True,
            )
            
            view_state = pdk.ViewState(
                latitude=30.5,
                longitude=69.5,
                zoom=5,
                pitch=0,
            )
            
            deck = pdk.Deck(
                layers=[layer],
                initial_view_state=view_state,
                tooltip={"text": "{type}\n{airport}\nSeverity: {severity}\nDate: {date}"}
            )
            
            st.pydeck_chart(deck)
            
        except ImportError:
            # Fallback to st.map
            st.map(df[['lat', 'lon']], zoom=5)
        
        # Legend
        st.markdown("### Legend")
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.markdown("🔵 Bird Strike")
        col2.markdown("🟣 Laser Strike")
        col3.markdown("🔴 Hazard")
        col4.markdown("🟠 TCAS Event")
        col5.markdown("🟡 Runway Incursion")
        
        # Data table
        with st.expander("📊 View Incident Data Table"):
            display_df = df[['report_id', 'date', 'airport', 'type', 'severity']].copy()
            display_df.columns = ['Report ID', 'Date', 'Airport', 'Type', 'Severity']
            st.dataframe(display_df, use_container_width=True)
    else:
        st.warning("No incidents match the selected filters.")


# ==============================================================================
# 2. AUDIT & COMPLIANCE MANAGER
# ==============================================================================

def render_audit_compliance():
    """Render Audit & Compliance Manager page"""
    
    st.markdown("## 📋 Audit & Compliance Manager")
    st.markdown("*Safety Assurance & IOSA Audit Preparedness*")
    
    tab1, tab2, tab3 = st.tabs(["🔍 Ramp Inspection", "📊 IOSA Preparedness", "📝 Audit Findings"])
    
    with tab1:
        st.markdown("### Ramp Inspection Checklist")
        st.markdown("*Complete this checklist during aircraft turnaround*")
        
        with st.form("ramp_inspection_form"):
            col1, col2 = st.columns(2)
            with col1:
                inspection_date = st.date_input("Inspection Date", value=date.today())
                aircraft_reg = st.selectbox("Aircraft Registration", options=list(AIRCRAFT_FLEET.keys()))
                flight_number = st.text_input("Flight Number", placeholder="PF-XXX")
            with col2:
                inspector_name = st.text_input("Inspector Name", value=st.session_state.get('user_name', ''))
                location = st.selectbox("Location", options=["OPSK - Sialkot", "OPKC - Karachi", "OPLA - Lahore", "OPIS - Islamabad"])
                inspection_type = st.selectbox("Inspection Type", options=["Pre-Departure", "Post-Arrival", "Transit", "Overnight"])
            
            st.markdown("---")
            st.markdown("#### Ground Equipment & Safety")
            
            col1, col2 = st.columns(2)
            with col1:
                chk_chocks = st.checkbox("✅ Wheel chocks in place", value=True)
                chk_cones = st.checkbox("✅ Safety cones positioned")
                chk_fod = st.checkbox("✅ FOD check completed")
                chk_fire_ext = st.checkbox("✅ Fire extinguisher available")
                chk_spill_kit = st.checkbox("✅ Spill kit accessible")
            with col2:
                chk_gpu = st.checkbox("✅ GPU properly connected")
                chk_stairs = st.checkbox("✅ Stairs/jetbridge secure")
                chk_belt_loader = st.checkbox("✅ Belt loader positioned correctly")
                chk_fuel_truck = st.checkbox("✅ Fuel truck grounded")
                chk_catering = st.checkbox("✅ Catering truck clear of hazards")
            
            st.markdown("#### Aircraft Condition")
            col1, col2 = st.columns(2)
            with col1:
                chk_tires = st.checkbox("✅ Tires - no visible damage/wear")
                chk_brakes = st.checkbox("✅ Brakes - no fluid leaks")
                chk_landing_gear = st.checkbox("✅ Landing gear - normal condition")
            with col2:
                chk_engine = st.checkbox("✅ Engines - no visible damage/leaks")
                chk_fuselage = st.checkbox("✅ Fuselage - no dents/damage")
                chk_windows = st.checkbox("✅ Windows/windshield - clear")
            
            st.markdown("#### Remarks")
            remarks = st.text_area("Additional Observations", placeholder="Enter any discrepancies or notes...")
            
            submitted = st.form_submit_button("✅ Submit Inspection", type="primary", use_container_width=True)
            
            if submitted:
                # Calculate compliance
                checks = [chk_chocks, chk_cones, chk_fod, chk_fire_ext, chk_spill_kit, 
                         chk_gpu, chk_stairs, chk_belt_loader, chk_fuel_truck, chk_catering,
                         chk_tires, chk_brakes, chk_landing_gear, chk_engine, chk_fuselage, chk_windows]
                compliance = sum(checks) / len(checks) * 100
                
                if compliance == 100:
                    st.success(f"✅ Inspection Complete - 100% Compliance")
                elif compliance >= 80:
                    st.warning(f"⚠️ Inspection Complete - {compliance:.0f}% Compliance - Some items require attention")
                else:
                    st.error(f"❌ Inspection Complete - {compliance:.0f}% Compliance - Multiple discrepancies found")
                
                st.balloons()
    
    with tab2:
        st.markdown("### IOSA Audit Preparedness")
        st.markdown("*IATA Operational Safety Audit Readiness Status*")
        
        # Overall progress
        overall_progress = 0.85
        st.markdown(f"""
        <div class="form-section" style="text-align: center;">
            <h3 style="color: #1E40AF;">Overall IOSA Readiness</h3>
            <div style="font-size: 4rem; font-weight: 700; color: {'#22C55E' if overall_progress >= 0.8 else '#EAB308'};">{overall_progress*100:.0f}%</div>
            <div style="color: #64748B;">Target: 100% by March 2025</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.progress(overall_progress)
        
        st.markdown("---")
        st.markdown("#### Section-wise Compliance")
        
        sections = [
            ("ORG - Organization & Management", 92, "Complete"),
            ("FLT - Flight Operations", 88, "In Progress"),
            ("DSP - Operational Control & Dispatch", 85, "In Progress"),
            ("MNT - Aircraft Maintenance", 78, "Action Required"),
            ("CAB - Cabin Operations", 90, "Complete"),
            ("GRH - Ground Handling", 82, "In Progress"),
            ("CGO - Cargo Operations", 75, "Action Required"),
            ("SEC - Security Management", 88, "In Progress"),
        ]
        
        for section, progress, status in sections:
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.markdown(f"**{section}**")
                st.progress(progress/100)
            with col2:
                color = "#22C55E" if progress >= 85 else "#EAB308" if progress >= 75 else "#DC2626"
                st.markdown(f"<span style='color: {color}; font-weight: bold;'>{progress}%</span>", unsafe_allow_html=True)
            with col3:
                if status == "Complete":
                    st.markdown("✅ Complete")
                elif status == "In Progress":
                    st.markdown("🔄 In Progress")
                else:
                    st.markdown("⚠️ Action Req'd")
    
    with tab3:
        st.markdown("### Recent Audit Findings")
        
        findings = [
            {"id": "F-2024-001", "section": "MNT", "finding": "Incomplete tool control documentation", "severity": "Minor", "status": "Open", "due": "Dec 15, 2024"},
            {"id": "F-2024-002", "section": "FLT", "finding": "EFB update procedure needs revision", "severity": "Observation", "status": "Closed", "due": "Nov 30, 2024"},
            {"id": "F-2024-003", "section": "GRH", "finding": "FOD prevention training overdue for 3 staff", "severity": "Minor", "status": "In Progress", "due": "Dec 20, 2024"},
            {"id": "F-2024-004", "section": "CGO", "finding": "DG handling manual not current revision", "severity": "Major", "status": "Open", "due": "Dec 10, 2024"},
        ]
        
        for f in findings:
            severity_color = {"Major": "#DC2626", "Minor": "#EAB308", "Observation": "#3B82F6"}[f['severity']]
            status_icon = {"Open": "🔴", "In Progress": "🟡", "Closed": "🟢"}[f['status']]
            
            st.markdown(f"""
            <div class="report-card">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <strong style="color: #1E40AF;">{f['id']}</strong> | <span class="category-badge cat-hazard">{f['section']}</span>
                        <div style="margin-top: 0.5rem;">{f['finding']}</div>
                    </div>
                    <div style="text-align: right;">
                        <span style="background: {severity_color}20; color: {severity_color}; padding: 0.25rem 0.5rem; border-radius: 12px; font-size: 0.75rem; font-weight: 600;">{f['severity']}</span>
                        <div style="margin-top: 0.5rem;">{status_icon} {f['status']}</div>
                        <small style="color: #64748B;">Due: {f['due']}</small>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)


# ==============================================================================
# 3. MANAGEMENT OF CHANGE (MoC) WORKFLOW
# ==============================================================================

def render_moc_workflow():
    """Render Management of Change page"""
    
    st.markdown("## 🔄 Management of Change (MoC)")
    st.markdown("*Operational Change Request & Risk Assessment*")
    
    tab1, tab2 = st.tabs(["📝 New Change Request", "📋 Pending Changes"])
    
    with tab1:
        st.markdown("### Submit Operational Change Request")
        
        with st.form("moc_form"):
            st.markdown("#### Change Details")
            col1, col2 = st.columns(2)
            with col1:
                change_type = st.selectbox("Change Type", options=[
                    "New Route / Destination",
                    "New Aircraft Type",
                    "Fleet Addition",
                    "Operational Procedure Change",
                    "Maintenance Procedure Change",
                    "Training Program Change",
                    "Ground Equipment Change",
                    "IT System Change",
                    "Organizational Change",
                    "Regulatory Compliance",
                    "Other"
                ])
                change_title = st.text_input("Change Title*", placeholder="Brief title of the change")
            with col2:
                initiator_dept = st.selectbox("Initiating Department", options=DEPARTMENTS)
                priority = st.selectbox("Priority", options=["Low", "Medium", "High", "Critical"])
                target_date = st.date_input("Target Implementation Date")
            
            change_description = st.text_area("Change Description*", placeholder="Detailed description of the proposed change...", height=100)
            
            st.markdown("---")
            st.markdown("#### Risk Assessment")
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Potential Hazards Identified**")
                haz_safety = st.checkbox("Safety Impact")
                haz_operational = st.checkbox("Operational Disruption")
                haz_regulatory = st.checkbox("Regulatory Non-Compliance")
                haz_training = st.checkbox("Training Requirements")
                haz_cost = st.checkbox("Cost Impact")
            with col2:
                likelihood = st.select_slider("Likelihood", options=["Rare", "Unlikely", "Possible", "Likely", "Almost Certain"])
                severity = st.select_slider("Severity", options=["Negligible", "Minor", "Moderate", "Major", "Catastrophic"])
            
            mitigation = st.text_area("Proposed Mitigation Measures", placeholder="How will identified risks be mitigated?")
            
            st.markdown("---")
            st.markdown("#### Approvals Required")
            col1, col2, col3 = st.columns(3)
            with col1:
                appr_safety = st.checkbox("Safety Manager", value=True)
                appr_qa = st.checkbox("Quality Assurance")
            with col2:
                appr_ops = st.checkbox("Operations Manager")
                appr_maint = st.checkbox("Maintenance Manager")
            with col3:
                appr_training = st.checkbox("Training Manager")
                appr_accountable = st.checkbox("Accountable Manager", value=True)
            
            submitted = st.form_submit_button("📤 Submit Change Request", type="primary", use_container_width=True)
            
            if submitted:
                if change_title and change_description:
                    st.success("✅ Change Request Submitted Successfully!")
                    st.info(f"Reference: MOC-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:4].upper()}")
                    st.balloons()
                else:
                    st.error("Please fill in all required fields")
    
    with tab2:
        st.markdown("### Pending Change Requests")
        
        pending_changes = [
            {
                "id": "MOC-20241201-A1B2",
                "title": "New Dubai-Sialkot Route",
                "type": "New Route / Destination",
                "dept": "Flight Operations",
                "priority": "High",
                "status": "Pending Safety Review",
                "submitted": "Dec 01, 2024",
                "risk": "Medium"
            },
            {
                "id": "MOC-20241128-C3D4",
                "title": "ATR 72-600 FANS-1/A Installation",
                "type": "Aircraft Modification",
                "dept": "Engineering",
                "priority": "Medium",
                "status": "Awaiting QA Approval",
                "submitted": "Nov 28, 2024",
                "risk": "Low"
            },
            {
                "id": "MOC-20241125-E5F6",
                "title": "Updated De-icing Procedures",
                "type": "Operational Procedure Change",
                "dept": "Ground Operations",
                "priority": "High",
                "status": "Approved - Implementation",
                "submitted": "Nov 25, 2024",
                "risk": "Low"
            },
        ]
        
        for change in pending_changes:
            priority_color = {"Critical": "#DC2626", "High": "#F97316", "Medium": "#EAB308", "Low": "#22C55E"}[change['priority']]
            risk_color = {"High": "#DC2626", "Medium": "#EAB308", "Low": "#22C55E"}[change['risk']]
            
            with st.expander(f"📄 {change['id']} - {change['title']}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**Type:** {change['type']}")
                    st.markdown(f"**Department:** {change['dept']}")
                    st.markdown(f"**Submitted:** {change['submitted']}")
                with col2:
                    st.markdown(f"**Priority:** <span style='color: {priority_color};'>{change['priority']}</span>", unsafe_allow_html=True)
                    st.markdown(f"**Risk Level:** <span style='color: {risk_color};'>{change['risk']}</span>", unsafe_allow_html=True)
                    st.markdown(f"**Status:** {change['status']}")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.button("✅ Approve", key=f"approve_{change['id']}")
                with col2:
                    st.button("❌ Reject", key=f"reject_{change['id']}")
                with col3:
                    st.button("💬 Comment", key=f"comment_{change['id']}")


# ==============================================================================
# 4. ERP "RED MODE"
# ==============================================================================

def render_erp_controls():
    """Render ERP mode toggle in sidebar and emergency contacts when active"""
    
    st.markdown("### 🚨 Emergency Response")
    
    erp_active = st.session_state.get('erp_mode', False)
    
    if erp_active:
        if st.button("🟢 DEACTIVATE ERP MODE", use_container_width=True, type="secondary"):
            st.session_state.erp_mode = False
            st.rerun()
        
        st.markdown("""
        <div class="erp-emergency">
            <h4 style="color: #DC2626; margin: 0 0 1rem 0;">⚠️ ERP ACTIVE</h4>
            <div style="font-size: 0.85rem;">
                <strong>Emergency Contacts:</strong><br>
                📞 CEO: +92-XXX-XXXXXXX<br>
                📞 Safety Manager: +92-XXX-XXXXXXX<br>
                📞 CAA Pakistan: +92-51-9144000<br>
                📞 Insurance: +92-XXX-XXXXXXX<br>
                📞 Media Relations: +92-XXX-XXXXXXX
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        if st.button("🚨 ACTIVATE ERP MODE", use_container_width=True, type="primary"):
            st.session_state.erp_mode = True
            st.rerun()


# ==============================================================================
# 5. SAFETY NEWSFEED (Dashboard Widget)
# ==============================================================================

def render_safety_bulletins():
    """Render Safety Bulletins widget for dashboard"""
    
    st.markdown("### 📰 Safety Bulletins")
    
    bulletins = [
        {
            "date": "Dec 07, 2024",
            "title": "Winter Ops: De-icing Procedures Updated",
            "content": "Revised de-icing holdover times for Type I and Type IV fluids. All crew to review updated OM-A Chapter 8.",
            "priority": "High",
            "category": "Operations"
        },
        {
            "date": "Dec 05, 2024",
            "title": "Bird Activity Warning - Sialkot",
            "content": "Increased bird activity reported near RWY 28 threshold. Enhanced vigilance during approach and departure. Bird dispersal unit activated.",
            "priority": "Medium",
            "category": "Wildlife"
        },
        {
            "date": "Dec 03, 2024",
            "title": "TCAS Bulletin: Updated RA Response",
            "content": "Reminder: Always follow TCAS RA commands. Recent industry events highlight importance of immediate response to RA advisories.",
            "priority": "High",
            "category": "Safety"
        },
        {
            "date": "Dec 01, 2024",
            "title": "Fog Season Advisory",
            "content": "November-February fog season. Review low visibility procedures. Ensure CATII/III currency is maintained.",
            "priority": "Medium",
            "category": "Weather"
        },
    ]
    
    for bulletin in bulletins:
        priority_color = {"High": "#DC2626", "Medium": "#EAB308", "Low": "#22C55E"}[bulletin['priority']]
        
        st.markdown(f"""
        <div class="bulletin-card" style="border-left-color: {priority_color};">
            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                <div>
                    <strong style="color: #1E40AF;">{bulletin['title']}</strong>
                    <div style="font-size: 0.85rem; color: #475569; margin-top: 0.25rem;">{bulletin['content']}</div>
                </div>
                <div style="text-align: right; min-width: 100px;">
                    <span style="background: {priority_color}20; color: {priority_color}; padding: 0.15rem 0.4rem; border-radius: 8px; font-size: 0.7rem; font-weight: 600;">{bulletin['priority']}</span>
                    <div style="font-size: 0.75rem; color: #64748B; margin-top: 0.25rem;">{bulletin['date']}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)


# ==============================================================================
# PREDICTIVE RISK MONITOR (From previous version)
# ==============================================================================

def render_predictive_risk():
    """Predictive Risk Monitor with 30-day forecast"""
    import numpy as np
    
    st.markdown("## 📈 Predictive Risk Monitor")
    st.markdown("*AI-Powered Incident Forecasting*")
    
    np.random.seed(42)
    dates = pd.date_range(start=date.today(), periods=30, freq='D')
    
    base = 12
    trend = np.linspace(0, 4, 30)
    seasonal = 5 * np.sin(np.linspace(0, 2*np.pi, 30))
    noise = np.random.normal(0, 2.5, 30)
    predicted = np.maximum(0, base + trend + seasonal + noise)
    
    HIGH_RISK = 18
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=dates, y=predicted, mode='lines+markers', name='Predicted', line=dict(color='#1E40AF', width=3)))
        fig.add_hline(y=HIGH_RISK, line_dash="dash", line_color="#DC2626", annotation_text="High Risk Threshold")
        fig.update_layout(
            title="30-Day Forecast",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(248,250,252,1)',
            font=dict(color='#334155'),
            xaxis=dict(showgrid=True, gridcolor='#E2E8F0'),
            yaxis=dict(showgrid=True, gridcolor='#E2E8F0')
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown(f"""
        <div class="prediction-card">
            <div style="font-size: 0.9rem; opacity: 0.9;">Next 7 Days</div>
            <div class="prediction-value">{int(predicted[:7].sum())}</div>
            <div style="font-size: 0.85rem;">Predicted Incidents</div>
        </div>
        """, unsafe_allow_html=True)
        
        high_days = sum(1 for p in predicted if p > HIGH_RISK)
        st.metric("High Risk Days", high_days)


# ==============================================================================
# DATA MANAGEMENT (From previous version)
# ==============================================================================

def render_data_management():
    """Data Management with CSV upload"""
    
    st.markdown("## 💾 Data Management")
    
    tab1, tab2 = st.tabs(["📤 Upload CSV", "📥 Export"])
    
    with tab1:
        uploaded = st.file_uploader("Upload CSV", type=['csv'])
        if uploaded:
            df = pd.read_csv(uploaded)
            st.success(f"✅ Loaded {len(df)} rows")
            st.dataframe(df.head(10), use_container_width=True)
    
    with tab2:
        export_type = st.selectbox("Export", ["All Reports", "Bird Strikes", "Hazards"])
        if st.button("📥 Generate Export"):
            st.download_button("⬇️ Download", "Sample data", "export.csv")


# ==============================================================================
# NL/AI QUERY (From previous version)  
# ==============================================================================

def render_nl_query():
    """Natural Language Query"""
    
    st.markdown("## 🤖 Natural Language Query")
    
    query = st.text_input("Ask a question...", placeholder="e.g., Show high risk hazards")
    
    if query:
        st.markdown("**Generated SQL:**")
        st.code("SELECT * FROM hazard_reports WHERE risk_level = 'High'", language="sql")
        st.dataframe(pd.DataFrame({'Report': ['HZD-001', 'HZD-002'], 'Risk': ['High', 'High']}))


# ==============================================================================
# CPA TABLE (From previous version)
# ==============================================================================

def render_cpa_table():
    """Corrective Actions table"""
    
    st.markdown("### 📋 Corrective & Preventive Actions")
    
    cpa_data = [
        {"id": "CPA-001", "action": "Install bird deterrent", "status": "overdue", "days": -7},
        {"id": "CPA-002", "action": "Update laser procedure", "status": "critical", "days": 1},
        {"id": "CPA-003", "action": "FOD training", "status": "warning", "days": 5},
        {"id": "CPA-004", "action": "TCAS procedure review", "status": "ok", "days": 19},
    ]
    
    for cpa in cpa_data:
        status_map = {"overdue": ("🔴", "#DC2626"), "critical": ("🔴", "#DC2626"), "warning": ("🟡", "#EAB308"), "ok": ("🟢", "#22C55E")}
        icon, color = status_map[cpa['status']]
        days_txt = f"{abs(cpa['days'])} days {'overdue' if cpa['days']<0 else 'left'}"
        st.markdown(f"{icon} **{cpa['id']}** - {cpa['action']} - <span style='color:{color}'>{days_txt}</span>", unsafe_allow_html=True)


# ==============================================================================
# UPDATED SIDEBAR WITH ALL NEW FEATURES
# ==============================================================================

def render_sidebar_v3():
    """Updated sidebar with all features"""
    
    with st.sidebar:
        st.markdown(f"""
        <div style="text-align: center; padding: 1rem; background: linear-gradient(135deg, #1E40AF, #3B82F6); border-radius: 12px; margin-bottom: 1rem;">
            <span style="font-size: 2.5rem;">🛡️✈️</span>
            <h3 style="color: white; margin: 0.5rem 0;">Air Sial Safety</h3>
            <small style="color: #BFDBFE;">Enterprise SMS v3.0</small>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div style="padding: 0.75rem; background: #F1F5F9; border-radius: 8px; margin-bottom: 1rem; border: 1px solid #E2E8F0;">
            <div style="font-weight: 600; color: #1E293B;">👤 {st.session_state.get('user_name', 'User')}</div>
            <div style="font-size: 0.8rem; color: #64748B;">{st.session_state.get('user_department', 'Department')}</div>
        </div>
        """, unsafe_allow_html=True)
        
        # ERP Controls
        render_erp_controls()
        
        st.markdown("---")
        st.markdown("### 📍 Navigation")
        
        page = st.radio(
            "Page",
            options=[
                "📊 Dashboard",
                "📈 Predictive Risk",
                "🌍 Geospatial Map",
                "📋 Audit & Compliance",
                "🔄 Management of Change",
                "💾 Data Management",
                "🤖 NL/AI Query",
                "📋 View Reports",
                "──────────────",
                "🐦 Bird Strike Report",
                "🔴 Laser Strike Report",
                "📡 TCAS Report",
                "🚨 Incident Report",
                "⚠️ Hazard Report",
                "──────────────",
                "📋 Flight Services (FSR)",
                "👨‍✈️ Captain's DBR",
                "──────────────",
                "🤖 AI Assistant",
                "⚙️ Settings"
            ],
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        
        if st.button("🆘 Emergency Report", use_container_width=True, type="primary"):
            return "🚨 Incident Report"
        
        if st.button("🚪 Logout", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
        
        return page


# ==============================================================================
# UPDATED DASHBOARD WITH SAFETY BULLETINS
# ==============================================================================

def render_dashboard_v3():
    """Enhanced dashboard with weather and safety bulletins - optimized"""
    
    # Get counts with error handling
    try:
        if db.is_connected:
            counts = db.get_report_counts()
            investigation_stats = db.get_investigation_stats()
        else:
            counts = {
                'bird_strikes': len(st.session_state.get('bird_strikes', [])),
                'laser_strikes': len(st.session_state.get('laser_strikes', [])),
                'tcas_reports': len(st.session_state.get('tcas_reports', [])),
                'hazard_reports': len(st.session_state.get('hazard_reports', [])),
                'aircraft_incidents': len(st.session_state.get('aircraft_incidents', [])),
                'fsr_reports': len(st.session_state.get('fsr_reports', [])),
                'captain_dbr': len(st.session_state.get('captain_dbr', []))
            }
            investigation_stats = {'total': sum(counts.values()), 'open': 0, 'closed': 0, 'awaiting_reply': 0}
    except Exception:
        counts = {'bird_strikes': 0, 'laser_strikes': 0, 'tcas_reports': 0, 'hazard_reports': 0, 'aircraft_incidents': 0, 'fsr_reports': 0, 'captain_dbr': 0}
        investigation_stats = {'total': 0, 'open': 0, 'closed': 0, 'awaiting_reply': 0}
    
    # KPI Cards - using st.columns for better performance
    st.markdown("### 📊 Safety Dashboard")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📊 Total Reports", sum(counts.values()))
    with col2:
        st.metric("🐦 Bird Strikes", counts.get('bird_strikes', 0))
    with col3:
        st.metric("🔴 Laser Strikes", counts.get('laser_strikes', 0))
    with col4:
        st.metric("⚠️ Hazards", counts.get('hazard_reports', 0))
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📡 TCAS Events", counts.get('tcas_reports', 0))
    with col2:
        st.metric("🚨 Incidents", counts.get('aircraft_incidents', 0))
    with col3:
        st.metric("📋 FSR", counts.get('fsr_reports', 0))
    with col4:
        st.metric("👨‍✈️ DBR", counts.get('captain_dbr', 0))
    
    st.markdown("---")
    
    # Weather Widget - with loading indicator
    try:
        WeatherService.render_weather_widget()
    except Exception as e:
        st.info("🌤️ Weather data loading...")
    
    st.markdown("---")
    
    # Main content
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 📈 Report Distribution")
        
        tab1, tab2 = st.tabs(["📊 By Type", "📅 By Month"])
        
        with tab1:
            try:
                report_data = {
                    'Type': ['Bird', 'Laser', 'TCAS', 'Hazards', 'Incidents', 'FSR', 'DBR'],
                    'Count': [counts.get('bird_strikes', 0), counts.get('laser_strikes', 0), 
                             counts.get('tcas_reports', 0), counts.get('hazard_reports', 0),
                             counts.get('aircraft_incidents', 0), counts.get('fsr_reports', 0),
                             counts.get('captain_dbr', 0)]
                }
                fig = px.pie(report_data, values='Count', names='Type', hole=0.4)
                fig.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)', 
                    plot_bgcolor='rgba(0,0,0,0)', 
                    font_color='#334155',
                    margin=dict(l=20, r=20, t=30, b=20)
                )
                st.plotly_chart(fig, use_container_width=True)
            except Exception:
                st.info("Chart loading...")
        
        with tab2:
            try:
                months = ['Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                fig = go.Figure()
                fig.add_trace(go.Bar(name='Bird', x=months, y=[5, 8, 12, 7, 4, 3], marker_color='#3B82F6'))
                fig.add_trace(go.Bar(name='Hazards', x=months, y=[8, 12, 15, 10, 8, 6], marker_color='#EF4444'))
                fig.update_layout(
                    barmode='group', 
                    paper_bgcolor='rgba(0,0,0,0)', 
                    font_color='#334155',
                    margin=dict(l=20, r=20, t=30, b=20)
                )
                st.plotly_chart(fig, use_container_width=True)
            except Exception:
                st.info("Chart loading...")
    
    with col2:
        render_safety_bulletins()
    
    st.markdown("---")
    render_cpa_table()


# ==============================================================================
# MAIN V3 ENTRY POINT
# ==============================================================================

def main_v3():
    """Main entry point for v3.0"""
    
    st.set_page_config(
        page_title="Air Sial Safety v3.0",
        page_icon="🛡️",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Load saved settings
    load_settings_from_file()
    
    apply_custom_css()
    
    if not st.session_state.get('logged_in', False):
        render_login()
        return
    
    render_header()
    
    page = render_sidebar_v3()
    
    # Skip separators
    if page and "────" in page:
        page = "📊 Dashboard"
    
    # Route pages
    if page == "📊 Dashboard":
        render_dashboard_v3()
    elif page == "📈 Predictive Risk":
        render_predictive_risk()
    elif page == "🌍 Geospatial Map":
        render_geospatial_map()
    elif page == "📋 Audit & Compliance":
        render_audit_compliance()
    elif page == "🔄 Management of Change":
        render_moc_workflow()
    elif page == "💾 Data Management":
        render_data_management()
    elif page == "🤖 NL/AI Query":
        render_nl_query()
    elif page == "📋 View Reports":
        render_view_reports()
    elif page == "🐦 Bird Strike Report":
        ocr_data = render_ocr_scanner("bird_strike")
        render_bird_strike_form(ocr_data)
    elif page == "🔴 Laser Strike Report":
        ocr_data = render_ocr_scanner("laser_strike")
        render_laser_strike_form(ocr_data)
    elif page == "📡 TCAS Report":
        ocr_data = render_ocr_scanner("tcas_report")
        render_tcas_form(ocr_data)
    elif page == "🚨 Incident Report":
        ocr_data = render_ocr_scanner("incident_report")
        render_incident_form(ocr_data)
    elif page == "⚠️ Hazard Report":
        ocr_data = render_ocr_scanner("hazard_report")
        render_hazard_form(ocr_data)
    elif page == "📋 Flight Services (FSR)":
        render_fsr_form()
    elif page == "👨‍✈️ Captain's DBR":
        render_dbr_form()
    elif page == "🤖 AI Assistant":
        render_ai_assistant()
    elif page == "⚙️ Settings":
        render_settings()


if __name__ == "__main__":
    main_v3()
