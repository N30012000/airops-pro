# config_loader.py
# Loads configuration from environment variables or .env (local dev)
import os
from dotenv import load_dotenv

load_dotenv()  # safe: will do nothing if .env not present

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
AI_API_KEY = os.getenv("AI_API_KEY") or os.getenv("GEMINI_API_KEY")
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")

# UI / Branding
AIR_SIAL_BLUE = os.getenv("AIR_SIAL_BLUE", "#1e3c72")
LOGO_PATH = os.getenv("LOGO_PATH", "assets/airsial_logo.png")
