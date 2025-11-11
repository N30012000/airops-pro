"""
AirOps Pro - Enterprise Airline Operational Reporting System
Configuration Module for Multi-Airline Deployment

This system enables 10+ airlines to run from the same codebase with zero code changes.
Each airline has isolated data, branding, and configurations.
"""

import os
from dataclasses import dataclass
from typing import Dict, List, Optional
from enum import Enum


class Environment(Enum):
    """Deployment environments"""
    DEVELOPMENT = "dev"
    STAGING = "staging"
    PRODUCTION = "prod"


@dataclass
class AirlineConfig:
    """Complete configuration for a single airline"""
    
    # === BRANDING ===
    airline_code: str  # e.g., "PIA", "AIR_BLUE"
    airline_name: str  # e.g., "Pakistan International Airlines"
    airline_display_name: str  # e.g., "PIA - Pakistan's National Carrier"
    
    # === COLORS & STYLING ===
    primary_color: str  # HEX color: #1E3A5F
    secondary_color: str  # HEX color: #E8A500
    accent_color: str  # HEX color: #0066CC
    background_color: str  # HEX color: #F5F7FA
    text_color: str  # HEX color: #1A1A1A
    
    # === LOGO & ASSETS ===
    logo_url: str  # URL to airline logo
    favicon_url: str  # URL to favicon
    
    # === DATA STORAGE ===
    # Using Supabase (PostgreSQL) - Free tier supports 500MB storage
    supabase_url: str
    supabase_key: str
    database_name: str
    
    # === AI & ANALYTICS ===
    openai_api_key: str  # For AI analysis reports
    anthropic_api_key: str  # Alternative AI provider
    
    # === OPERATIONAL SETTINGS ===
    headquarters_location: str  # City/Country
    operational_regions: List[str]  # List of regions served
    fleet_size: int  # Number of aircraft
    daily_flights_avg: int  # Average daily flights
    
    # === FEATURES ===
    enable_predictive_analytics: bool = True
    enable_cost_optimization: bool = True
    enable_fuel_efficiency: bool = True
    enable_delay_prediction: bool = True
    enable_revenue_optimization: bool = True
    enable_maintenance_alerts: bool = True
    
    # === REPORT TEMPLATES ===
    report_formats: List[str] = None  # ["weekly", "biweekly", "monthly", "quarterly", "biannual", "annual"]
    
    # === API KEYS FOR INTEGRATIONS ===
    maintenance_api_key: Optional[str] = None
    crew_management_api_key: Optional[str] = None
    fuel_management_api_key: Optional[str] = None
    revenue_management_api_key: Optional[str] = None
    
    def __post_init__(self):
        if self.report_formats is None:
            self.report_formats = ["weekly", "biweekly", "monthly", "quarterly", "biannual", "annual"]


# ============================================================================
# AIRLINE CONFIGURATIONS - ADD NEW AIRLINES HERE
# ============================================================================

AIRLINES: Dict[str, AirlineConfig] = {
    "PIA": AirlineConfig(
        airline_code="PIA",
        airline_name="Pakistan International Airlines",
        airline_display_name="PIA - Pakistan's National Carrier",
        
        # Branding
        primary_color="#1E3A5F",  # Deep Navy Blue
        secondary_color="#E8A500",  # Gold
        accent_color="#0066CC",  # Sky Blue
        background_color="#F5F7FA",
        text_color="#1A1A1A",
        
        # Assets
        logo_url="https://upload.wikimedia.org/wikipedia/en/thumb/2/23/PIA_Logo.svg/300px-PIA_Logo.svg.png",
        favicon_url="https://www.piaa.com.pk/favicon.ico",
        
        # Data Storage (Supabase - Free with 500MB)
        supabase_url=os.getenv("PIA_SUPABASE_URL", "https://your-project.supabase.co"),
        supabase_key=os.getenv("PIA_SUPABASE_KEY", ""),
        database_name="pia_operations",
        
        # AI APIs
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY", ""),
        
        # Operations
        headquarters_location="Karachi, Pakistan",
        operational_regions=["South Asia", "Middle East", "Europe", "North America"],
        fleet_size=28,
        daily_flights_avg=80,
        
        # Features
        enable_predictive_analytics=True,
        enable_cost_optimization=True,
        enable_fuel_efficiency=True,
        enable_delay_prediction=True,
        enable_revenue_optimization=True,
        enable_maintenance_alerts=True,
    ),
    
    "AIRBLUE": AirlineConfig(
        airline_code="AIRBLUE",
        airline_name="AirBlue",
        airline_display_name="AirBlue - Excellence in Service",
        
        # Branding
        primary_color="#003DA5",  # Deep Blue
        secondary_color="#FF6B35",  # Orange
        accent_color="#004E89",  # Navy
        background_color="#F8F9FA",
        text_color="#1F2937",
        
        # Assets
        logo_url="https://upload.wikimedia.org/wikipedia/en/thumb/f/f9/AirBlue_Logo.svg/300px-AirBlue_Logo.svg.png",
        favicon_url="https://www.airblue.com/favicon.ico",
        
        # Data Storage
        supabase_url=os.getenv("AIRBLUE_SUPABASE_URL", "https://your-project.supabase.co"),
        supabase_key=os.getenv("AIRBLUE_SUPABASE_KEY", ""),
        database_name="airblue_operations",
        
        # AI APIs
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY", ""),
        
        # Operations
        headquarters_location="Karachi, Pakistan",
        operational_regions=["South Asia", "Middle East"],
        fleet_size=15,
        daily_flights_avg=45,
        
        # Features
        enable_predictive_analytics=True,
        enable_cost_optimization=True,
        enable_fuel_efficiency=True,
        enable_delay_prediction=True,
        enable_revenue_optimization=False,  # Custom per airline
        enable_maintenance_alerts=True,
    ),
}


# ============================================================================
# GLOBAL SYSTEM CONFIGURATION
# ============================================================================

class SystemConfig:
    """Global system configuration - shared across all airlines"""
    
    # Environment
    ENVIRONMENT: Environment = Environment(os.getenv("ENVIRONMENT", "dev"))
    
    # Default airline (for local testing)
    DEFAULT_AIRLINE: str = os.getenv("DEFAULT_AIRLINE", "PIA")
    
    # Database (Free tier = 500MB)
    # Supabase: 500MB free, scales to 1GB+ (PostgreSQL with real-time)
    # Alternative: Firebase (1GB free) or MongoDB Atlas (512MB free)
    USE_SUPABASE: bool = True
    
    # Caching
    CACHE_TTL: int = 3600  # 1 hour
    
    # Data Retention
    DATA_RETENTION_DAYS: int = 365 * 5  # 5 years
    
    # Report Generation
    AUTO_GENERATE_REPORTS: bool = True
    REPORT_GENERATION_HOUR: int = 23  # 11 PM UTC
    
    # File Storage (Use Supabase Storage - Free 1GB)
    FILE_STORAGE_PATH: str = "airline-reports"
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Security
    REQUIRE_AUTH: bool = True
    SESSION_TIMEOUT_MINUTES: int = 60
    
    # API Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 3600  # 1 hour


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_airline_config(airline_code: str) -> AirlineConfig:
    """
    Retrieve configuration for a specific airline
    
    Args:
        airline_code: Airline identifier (e.g., "PIA", "AIRBLUE")
    
    Returns:
        AirlineConfig object
    
    Raises:
        ValueError: If airline not found
    """
    if airline_code not in AIRLINES:
        raise ValueError(
            f"Airline '{airline_code}' not configured. "
            f"Available: {list(AIRLINES.keys())}"
        )
    return AIRLINES[airline_code]


def list_airlines() -> List[str]:
    """Get list of all configured airlines"""
    return list(AIRLINES.keys())


def add_new_airline(config: AirlineConfig) -> None:
    """
    Register a new airline (can be done programmatically)
    
    Args:
        config: AirlineConfig object
    """
    if config.airline_code in AIRLINES:
        raise ValueError(f"Airline '{config.airline_code}' already exists")
    AIRLINES[config.airline_code] = config


def validate_airline_config(airline_code: str) -> Dict[str, any]:
    """
    Validate that all required settings are present
    
    Returns:
        Dictionary with validation results
    """
    config = get_airline_config(airline_code)
    errors = []
    warnings = []
    
    # Required fields check
    if not config.supabase_url or config.supabase_url.startswith("https://your-"):
        errors.append("Supabase URL not configured")
    
    if not config.supabase_key:
        warnings.append("Supabase key not set (will use public mode)")
    
    if not config.openai_api_key:
        warnings.append("OpenAI API key not set (AI features disabled)")
    
    return {
        "airline": airline_code,
        "is_valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings
    }


# ============================================================================
# DEFAULT FEATURE FLAGS
# ============================================================================

FEATURE_FLAGS = {
    "enable_dark_mode": True,
    "enable_export_pdf": True,
    "enable_export_excel": True,
    "enable_email_reports": True,
    "enable_slack_integration": False,
    "enable_advanced_analytics": True,
    "enable_predictive_maintenance": True,
    "enable_fuel_optimization": True,
    "enable_crew_scheduling": False,
    "enable_revenue_management": True,
}


# ============================================================================
# REPORT TEMPLATE CONFIGURATIONS
# ============================================================================

REPORT_TEMPLATES = {
    "weekly": {
        "name": "Weekly Operations Report",
        "frequency": "Every Monday 8 AM",
        "sections": [
            "Executive Summary",
            "Flight Performance",
            "Maintenance Alert",
            "Revenue Metrics",
            "Key Issues",
            "Next Week Outlook"
        ]
    },
    "biweekly": {
        "name": "Bi-Weekly Operational Review",
        "frequency": "Every 2 weeks",
        "sections": [
            "Executive Summary",
            "Performance Trends",
            "Incident Analysis",
            "Maintenance Schedule",
            "Cost Analysis",
            "Recommendations"
        ]
    },
    "monthly": {
        "name": "Monthly Operations Report",
        "frequency": "1st of every month",
        "sections": [
            "Executive Summary",
            "Monthly KPIs",
            "Flight Analytics",
            "Revenue Analysis",
            "Cost Optimization",
            "Maintenance Overview",
            "Staff Performance",
            "Recommendations"
        ]
    },
    "quarterly": {
        "name": "Quarterly Business Review",
        "frequency": "Every 3 months",
        "sections": [
            "Executive Summary",
            "Quarterly Performance",
            "Strategic Analysis",
            "Financial Review",
            "Market Position",
            "Risk Assessment",
            "Strategic Recommendations"
        ]
    },
    "biannual": {
        "name": "Bi-Annual Strategic Review",
        "frequency": "Every 6 months",
        "sections": [
            "Executive Summary",
            "Performance vs Targets",
            "Strategic Initiatives",
            "Market Analysis",
            "Financial Review",
            "Risk Analysis",
            "Board Recommendations"
        ]
    },
    "annual": {
        "name": "Annual Report",
        "frequency": "December 31",
        "sections": [
            "Executive Summary",
            "Year in Review",
            "Financial Performance",
            "Operational Metrics",
            "Strategic Achievements",
            "Risk Assessment",
            "Next Year Strategy",
            "Board Certification"
        ]
    }
}


if __name__ == "__main__":
    print("🛫 AirOps Pro Configuration System\n")
    print(f"Configured Airlines: {list_airlines()}")
    print(f"\nDefault Airline: {SystemConfig.DEFAULT_AIRLINE}")
    print(f"Environment: {SystemConfig.ENVIRONMENT.value}")
    
    # Validate all airlines
    for airline_code in list_airlines():
        validation = validate_airline_config(airline_code)
        print(f"\n✓ {airline_code}: {'VALID' if validation['is_valid'] else 'NEEDS CONFIG'}")
        if validation['warnings']:
            for w in validation['warnings']:
                print(f"  ⚠ {w}")
