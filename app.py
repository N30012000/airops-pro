"""
Air Sial Operations - Production-Ready Airline Operational Reporting System
A scalable, secure, and comprehensive operations management system for Air Sial
ENHANCED WITH COMPLETE AUTHENTICATION SYSTEM + GEMINI AI + GENERIC CHAT + BEAUTIFUL UI
The Pride of Pakistan
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import os
from typing import Optional, Dict, List, Any
import hashlib
import logging
from io import BytesIO
import base64
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURATION & ENVIRONMENT
# ============================================================================

class Config:
    """Application configuration from environment variables"""
    # Database
    SUPABASE_URL = os.getenv("SUPABASE_URL", st.secrets.get("SUPABASE_URL", "") if hasattr(st, 'secrets') else "")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY", st.secrets.get("SUPABASE_KEY", "") if hasattr(st, 'secrets') else "")
    DATABASE_URL = os.getenv("DATABASE_URL", "")
    
    # AI API Keys
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", st.secrets.get("GEMINI_API_KEY", "") if hasattr(st, 'secrets') else "")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", st.secrets.get("GROQ_API_KEY", "") if hasattr(st, 'secrets') else "")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", st.secrets.get("OPENAI_API_KEY", "") if hasattr(st, 'secrets') else "")
    OPENSKY_USERNAME = os.getenv("OPENSKY_USERNAME", st.secrets.get("OPENSKY_USERNAME", "") if hasattr(st, 'secrets') else "")
    OPENSKY_PASSWORD = os.getenv("OPENSKY_PASSWORD", st.secrets.get("OPENSKY_PASSWORD", "") if hasattr(st, 'secrets') else "")
    
    # Timezone - Pakistan Standard Time (GMT+5)
    TIMEZONE_OFFSET = 5  # GMT+5)
    
    # Auth
    ADMIN_PASSWORD_HASH = os.getenv("ADMIN_PASSWORD_HASH", "")
    API_TOKEN = os.getenv("API_TOKEN", "")
    
    # App Settings
    APP_MODE = os.getenv("APP_MODE", "production")  # Changed to production
    ENABLE_AUTH = os.getenv("ENABLE_AUTH", "true").lower() == "true"
    
    # Air Sial Brand Colors - Green & Gold Theme
    PRIMARY_COLOR = "#048444"    # Air Sial Green/Teal
    PRIMARY_LIGHT = "#05A858"    # Lighter Green
    PRIMARY_DARK = "#046C34"     # Darker Green
    SECONDARY_COLOR = "#FFFFFF"  # White
    ACCENT_COLOR = "#D4AF37"     # Gold
    ACCENT_LIGHT = "#E8C964"     # Light Gold
    TEXT_COLOR = "#1E1E1E"
    TEXT_LIGHT = "#6C757D"
    BACKGROUND = "#F8F9FA"
    CARD_BG = "#FFFFFF"

config = Config()

# ============================================================================
# TIMEZONE HELPER
# ============================================================================

def get_pakistan_time():
    """Get current time in Pakistan Standard Time (GMT+5)"""
    from datetime import timezone
    pkt = timezone(timedelta(hours=config.TIMEZONE_OFFSET))
    return datetime.now(pkt)

# ============================================================================
# DATABASE LAYER
# ============================================================================

class DatabaseManager:
    """Unified database manager supporting Supabase, PostgreSQL, MySQL, and SQLite"""
    
    def __init__(self):
        self.db_type = self._detect_db_type()
        self.connection = None
        self._init_database()
    
    def _detect_db_type(self) -> str:
        """Detect which database to use based on available credentials"""
        if config.SUPABASE_URL and config.SUPABASE_KEY:
            return "supabase"
        elif config.DATABASE_URL:
            if "postgres" in config.DATABASE_URL:
                return "postgresql"
            elif "mysql" in config.DATABASE_URL:
                return "mysql"
        return "sqlite"
    
    def _init_database(self):
        """Initialize database connection and create schema"""
        try:
            if self.db_type == "supabase":
                self._init_supabase()
            elif self.db_type == "sqlite":
                self._init_sqlite()
            else:
                self._init_sql_database()
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            self.db_type = "sqlite"
            self._init_sqlite()
    
    def _init_supabase(self):
        """Initialize Supabase connection"""
        try:
            from supabase import create_client, Client
            self.connection: Client = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)
            logger.info("Connected to Supabase")
        except ImportError:
            logger.warning("supabase-py not installed, falling back to SQLite")
            self.db_type = "sqlite"
            self._init_sqlite()
    
    def _init_sqlite(self):
        """Initialize SQLite connection with schema"""
        import sqlite3
        self.connection = sqlite3.connect('airsial_operations.db', check_same_thread=False)
        self._create_sqlite_schema()
        logger.info("Connected to SQLite")
    
    def _init_sql_database(self):
        """Initialize PostgreSQL/MySQL connection"""
        try:
            from sqlalchemy import create_engine
            self.connection = create_engine(config.DATABASE_URL, pool_pre_ping=True)
            logger.info(f"Connected to {self.db_type}")
        except Exception as e:
            logger.error(f"Failed to connect to {self.db_type}: {e}")
            self.db_type = "sqlite"
            self._init_sqlite()
    
    def _create_sqlite_schema(self):
        """Create SQLite tables"""
        cursor = self.connection.cursor()
        
        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                full_name TEXT,
                role TEXT DEFAULT 'user',
                last_login TIMESTAMP,
                reset_token TEXT,
                reset_token_expiry TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create default admin user if not exists
        try:
            admin_password = "admin123"
            password_hash = hashlib.sha256(admin_password.encode()).hexdigest()
            cursor.execute("""
                INSERT OR IGNORE INTO users (username, email, password_hash, full_name, role)
                VALUES (?, ?, ?, ?, ?)
            """, ("admin", "admin@airsial.com", password_hash, "Administrator", "admin"))
        except Exception as e:
            logger.error(f"Error creating default admin: {e}")
        
        # Maintenance table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS maintenance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                aircraft_registration TEXT NOT NULL,
                maintenance_type TEXT NOT NULL,
                description TEXT,
                scheduled_date DATE NOT NULL,
                completion_date DATE,
                technician_name TEXT,
                hours_spent REAL DEFAULT 0,
                cost REAL DEFAULT 0,
                status TEXT DEFAULT 'Scheduled',
                priority TEXT DEFAULT 'Medium',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Safety incidents table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS safety_incidents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                incident_date DATE NOT NULL,
                incident_type TEXT NOT NULL,
                severity TEXT NOT NULL,
                aircraft_registration TEXT,
                flight_number TEXT,
                location TEXT,
                description TEXT NOT NULL,
                immediate_action TEXT,
                investigation_status TEXT DEFAULT 'Open',
                reporter_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Flights table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS flights (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                flight_number TEXT NOT NULL,
                aircraft_registration TEXT NOT NULL,
                departure_airport TEXT NOT NULL,
                arrival_airport TEXT NOT NULL,
                scheduled_departure TIMESTAMP NOT NULL,
                actual_departure TIMESTAMP,
                scheduled_arrival TIMESTAMP NOT NULL,
                actual_arrival TIMESTAMP,
                passengers_count INTEGER DEFAULT 0,
                cargo_weight REAL DEFAULT 0,
                flight_status TEXT DEFAULT 'Scheduled',
                delay_reason TEXT,
                captain_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        self.connection.commit()
        logger.info("SQLite schema created with users table")
    
    def query(self, table: str, filters: Optional[Dict] = None, limit: int = 1000) -> pd.DataFrame:
        """Generic query method"""
        try:
            if self.db_type == "supabase":
                return self._query_supabase(table, filters, limit)
            elif self.db_type == "sqlite":
                return self._query_sqlite(table, filters, limit)
            else:
                return self._query_sql(table, filters, limit)
        except Exception as e:
            logger.error(f"Query failed: {e}")
            return pd.DataFrame()
    
    def _query_supabase(self, table: str, filters: Optional[Dict], limit: int) -> pd.DataFrame:
        """Query Supabase"""
        query = self.connection.table(table).select("*")
        if filters:
            for key, value in filters.items():
                query = query.eq(key, value)
        response = query.limit(limit).execute()
        return pd.DataFrame(response.data)
    
    def _query_sqlite(self, table: str, filters: Optional[Dict], limit: int) -> pd.DataFrame:
        """Query SQLite"""
        query = f"SELECT * FROM {table}"
        params = []
        
        if filters:
            conditions = []
            for key, value in filters.items():
                conditions.append(f"{key} = ?")
                params.append(value)
            query += " WHERE " + " AND ".join(conditions)
        
        query += f" LIMIT {limit}"
        return pd.read_sql_query(query, self.connection, params=params)
    
    def _query_sql(self, table: str, filters: Optional[Dict], limit: int) -> pd.DataFrame:
        """Query PostgreSQL/MySQL"""
        query = f"SELECT * FROM {table}"
        if filters:
            conditions = [f"{k} = :{k}" for k in filters.keys()]
            query += " WHERE " + " AND ".join(conditions)
        query += f" LIMIT {limit}"
        return pd.read_sql_query(query, self.connection, params=filters)
    
    def insert(self, table: str, data: Dict) -> bool:
        """Insert record"""
        try:
            if self.db_type == "supabase":
                self.connection.table(table).insert(data).execute()
            elif self.db_type == "sqlite":
                self._insert_sqlite(table, data)
            else:
                self._insert_sql(table, data)
            return True
        except Exception as e:
            logger.error(f"Insert failed: {e}")
            return False
    
    def _insert_sqlite(self, table: str, data: Dict):
        """Insert into SQLite"""
        columns = ", ".join(data.keys())
        placeholders = ", ".join(["?" for _ in data])
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        cursor = self.connection.cursor()
        cursor.execute(query, list(data.values()))
        self.connection.commit()
    
    def _insert_sql(self, table: str, data: Dict):
        """Insert into PostgreSQL/MySQL"""
        columns = ", ".join(data.keys())
        placeholders = ", ".join([f":{k}" for k in data.keys()])
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        self.connection.execute(query, data)
    
    def bulk_insert(self, table: str, records: List[Dict]) -> int:
        """Bulk insert records"""
        success_count = 0
        for record in records:
            if self.insert(table, record):
                success_count += 1
        return success_count
    
    def update(self, table: str, record_id: int, data: Dict) -> bool:
        """Update record"""
        try:
            data['updated_at'] = datetime.now().isoformat()
            if self.db_type == "supabase":
                self.connection.table(table).update(data).eq('id', record_id).execute()
            elif self.db_type == "sqlite":
                self._update_sqlite(table, record_id, data)
            else:
                self._update_sql(table, record_id, data)
            return True
        except Exception as e:
            logger.error(f"Update failed: {e}")
            return False
    
    def _update_sqlite(self, table: str, record_id: int, data: Dict):
        """Update SQLite record"""
        set_clause = ", ".join([f"{k} = ?" for k in data.keys()])
        query = f"UPDATE {table} SET {set_clause} WHERE id = ?"
        cursor = self.connection.cursor()
        cursor.execute(query, list(data.values()) + [record_id])
        self.connection.commit()
    
    def _update_sql(self, table: str, record_id: int, data: Dict):
        """Update PostgreSQL/MySQL record"""
        set_clause = ", ".join([f"{k} = :{k}" for k in data.keys()])
        query = f"UPDATE {table} SET {set_clause} WHERE id = :id"
        data['id'] = record_id
        self.connection.execute(query, data)
    
    def delete(self, table: str, record_id: int) -> bool:
        """Delete record"""
        try:
            if self.db_type == "supabase":
                self.connection.table(table).delete().eq('id', record_id).execute()
            elif self.db_type == "sqlite":
                cursor = self.connection.cursor()
                cursor.execute(f"DELETE FROM {table} WHERE id = ?", (record_id,))
                self.connection.commit()
            else:
                self.connection.execute(f"DELETE FROM {table} WHERE id = :id", {'id': record_id})
            return True
        except Exception as e:
            logger.error(f"Delete failed: {e}")
            return False
    
    def clear_table(self, table: str) -> bool:
        """Clear all records from a table"""
        try:
            if self.db_type == "supabase":
                # Supabase doesn't have a direct truncate, so delete all
                self.connection.table(table).delete().neq('id', 0).execute()
            elif self.db_type == "sqlite":
                cursor = self.connection.cursor()
                cursor.execute(f"DELETE FROM {table}")
                self.connection.commit()
            else:
                self.connection.execute(f"DELETE FROM {table}")
            return True
        except Exception as e:
            logger.error(f"Clear table failed: {e}")
            return False

# Initialize database
@st.cache_resource
def get_database():
    return DatabaseManager()

db = get_database()

# ============================================================================
# GEMINI AI HELPER - USING REST API (MORE RELIABLE)
# ============================================================================

class GeminiAI:
    """Gemini AI integration for chat and analysis using REST API"""
    
    @staticmethod
    def chat(message: str, system_prompt: str = "") -> str:
        """Send message to Gemini and get response using REST API"""
        if not config.GEMINI_API_KEY:
            return "❌ Gemini API key not configured. Please add GEMINI_API_KEY to your secrets."
        
        try:
            import requests
            
            # Use REST API directly - more reliable than the library
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={config.GEMINI_API_KEY}"
            
            # Combine system prompt with user message
            full_prompt = f"{system_prompt}\n\nUser: {message}" if system_prompt else message
            
            payload = {
                "contents": [{
                    "parts": [{"text": full_prompt}]
                }]
            }
            
            headers = {"Content-Type": "application/json"}
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                return data["candidates"][0]["content"]["parts"][0]["text"]
            else:
                error_msg = response.json().get("error", {}).get("message", response.text)
                return f"❌ Gemini API error: {error_msg}"
            
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            return f"❌ Error communicating with Gemini: {str(e)}"
    
    @staticmethod
    def analyze_data(df: pd.DataFrame, question: str) -> str:
        """Use Gemini to analyze data and answer questions"""
        if not config.GEMINI_API_KEY:
            return "❌ Gemini API key not configured."
        
        try:
            import requests
            
            # Prepare data summary
            data_summary = f"""
Dataset Information:
- Shape: {df.shape[0]} rows, {df.shape[1]} columns
- Columns: {', '.join(df.columns)}

Sample Data (first 5 rows):
{df.head().to_string()}

Statistics:
{df.describe().to_string()}
"""
            
            system_prompt = """You are an AI data analyst for Air Sial - The Pride of Pakistan. 
Analyze the provided data and answer the user's question with specific insights, patterns, and recommendations.
Be concise but thorough. Use bullet points for clarity."""
            
            full_prompt = f"{system_prompt}\n\nData:\n{data_summary}\n\nQuestion: {question}"
            
            # Use REST API directly
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={config.GEMINI_API_KEY}"
            
            payload = {
                "contents": [{
                    "parts": [{"text": full_prompt}]
                }]
            }
            
            headers = {"Content-Type": "application/json"}
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                return data["candidates"][0]["content"]["parts"][0]["text"]
            else:
                error_msg = response.json().get("error", {}).get("message", response.text)
                return f"❌ Gemini API error: {error_msg}"
            
        except Exception as e:
            logger.error(f"Gemini analysis error: {e}")
            return f"❌ Analysis error: {str(e)}"

# ============================================================================
# GROQ AI HELPER (ALTERNATIVE)
# ============================================================================

class GroqAI:
    """Groq AI integration as alternative to Gemini"""
    
    @staticmethod
    def chat(message: str, system_prompt: str = "") -> str:
        """Send message to Groq and get response"""
        if not config.GROQ_API_KEY:
            return "❌ Groq API key not configured."
        
        try:
            from groq import Groq
            
            client = Groq(api_key=config.GROQ_API_KEY)
            
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": message})
            
            response = client.chat.completions.create(
                model="mixtral-8x7b-32768",
                messages=messages,
                temperature=0.7,
                max_tokens=1024
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Groq API error: {e}")
            return f"❌ Error communicating with Groq: {str(e)}"

# ============================================================================
# AUTHENTICATION
# ============================================================================

def check_password():
    """Enhanced authentication with full Login/Signup/Reset functionality"""
    
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'current_user' not in st.session_state:
        st.session_state.current_user = None
    
    if st.session_state.authenticated:
        return True
    
    # Beautiful login page with Air Sial branding
    st.markdown(f'''
        <div style="text-align:center;margin:3rem 0 2rem 0;">
            <div style="font-size:6rem;margin-bottom:1rem;animation:float 3s ease-in-out infinite;">✈️</div>
            <div style="background:linear-gradient(135deg, {config.PRIMARY_COLOR} 0%, {config.PRIMARY_DARK} 100%);
                        -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                        font-size:3.5rem;font-weight:800;margin-bottom:0.5rem;letter-spacing:-1px;">
                Air Sial Operations
            </div>
            <div style="color:{config.TEXT_LIGHT};font-size:1.2rem;font-weight:300;">
                The Pride of Pakistan - Operational Reporting & Analytics
            </div>
        </div>
        
        <style>
        @keyframes float {{
            0%, 100% {{ transform: translateY(0px); }}
            50% {{ transform: translateY(-20px); }}
        }}
        </style>
    ''', unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["🔐 Login", "📝 Sign Up", "🔑 Reset Password"])
    
    with tab1:
        st.markdown("### Welcome Back")
        st.markdown("---")
        
        with st.form("login_form", clear_on_submit=False):
            username = st.text_input("👤 Username", placeholder="Enter your username", key="login_username")
            password = st.text_input("🔒 Password", type="password", placeholder="Enter your password", key="login_password")
            remember = st.checkbox("Remember me for 30 days")
            
            col1, col2 = st.columns([1, 1])
            with col1:
                submit = st.form_submit_button("🚀 Login", use_container_width=True, type="primary")
            with col2:
                demo = st.form_submit_button("🎮 Demo Mode", use_container_width=True)
            
            if demo:
                st.session_state.authenticated = True
                st.session_state.current_user = {
                    'username': 'demo',
                    'email': 'demo@airsial.com',
                    'full_name': 'Demo User',
                    'role': 'admin'
                }
                st.success("Entering demo mode...")
                time.sleep(0.5)
                st.rerun()
            
            if submit:
                if not username or not password:
                    st.error("⚠️ Please enter both username and password")
                else:
                    try:
                        password_hash = hashlib.sha256(password.encode()).hexdigest()
                        
                        if db.db_type == "sqlite":
                            cursor = db.connection.cursor()
                            cursor.execute(
                                "SELECT * FROM users WHERE username = ? AND password_hash = ?",
                                (username, password_hash)
                            )
                            result = cursor.fetchone()
                            
                            if result:
                                columns = [description[0] for description in cursor.description]
                                user = dict(zip(columns, result))
                                
                                cursor.execute(
                                    "UPDATE users SET last_login = ? WHERE id = ?",
                                    (datetime.now().isoformat(), user['id'])
                                )
                                db.connection.commit()
                                
                                st.session_state.authenticated = True
                                st.session_state.current_user = {
                                    'id': user['id'],
                                    'username': user['username'],
                                    'email': user['email'],
                                    'full_name': user['full_name'],
                                    'role': user['role']
                                }
                                
                                st.success(f"✅ Welcome back, {user['full_name']}!")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error("❌ Invalid username or password")
                        
                        elif db.db_type == "supabase":
                            response = db.connection.table('users').select("*").eq('username', username).eq('password_hash', password_hash).execute()
                            
                            if response.data:
                                user = response.data[0]
                                db.connection.table('users').update({'last_login': datetime.now().isoformat()}).eq('id', user['id']).execute()
                                
                                st.session_state.authenticated = True
                                st.session_state.current_user = {
                                    'id': user['id'],
                                    'username': user['username'],
                                    'email': user['email'],
                                    'full_name': user['full_name'],
                                    'role': user['role']
                                }
                                st.success(f"✅ Welcome back, {user['full_name']}!")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error("❌ Invalid username or password")
                                
                    except Exception as e:
                        logger.error(f"Login error: {e}")
                        st.error(f"⚠️ Login error: {str(e)}")
        
        st.divider()
        st.info("💡 **Default credentials:** username: `admin` | password: `admin123`")
        st.caption("Or create a new account in the Sign Up tab")
    
    with tab2:
        st.markdown("### Create Your Account")
        st.markdown("---")
        
        with st.form("signup_form", clear_on_submit=True):
            full_name = st.text_input("👤 Full Name", placeholder="John Doe", key="signup_name")
            email = st.text_input("📧 Email Address", placeholder="john.doe@airsial.com", key="signup_email")
            username = st.text_input("👤 Username", placeholder="johndoe (min 3 characters)", key="signup_username")
            
            col1, col2 = st.columns(2)
            with col1:
                password = st.text_input("🔒 Password", type="password", placeholder="Min 6 characters", key="signup_password")
            with col2:
                password_confirm = st.text_input("🔒 Confirm Password", type="password", key="signup_password_confirm")
            
            terms = st.checkbox("I agree to the Terms of Service and Privacy Policy")
            
            submit = st.form_submit_button("📝 Create Account", use_container_width=True, type="primary")
            
            if submit:
                errors = []
                if not all([full_name, email, username, password, password_confirm]):
                    errors.append("Please fill in all fields")
                if password != password_confirm:
                    errors.append("Passwords do not match")
                if len(username) < 3:
                    errors.append("Username must be at least 3 characters")
                if len(password) < 6:
                    errors.append("Password must be at least 6 characters")
                if not terms:
                    errors.append("Please accept the Terms of Service")
                if '@' not in email:
                    errors.append("Please enter a valid email address")
                
                if errors:
                    for error in errors:
                        st.error(f"❌ {error}")
                else:
                    try:
                        password_hash = hashlib.sha256(password.encode()).hexdigest()
                        
                        if db.db_type == "sqlite":
                            cursor = db.connection.cursor()
                            cursor.execute("""
                                INSERT INTO users (username, email, password_hash, full_name, role, created_at)
                                VALUES (?, ?, ?, ?, ?, ?)
                            """, (username, email, password_hash, full_name, 'user', datetime.now().isoformat()))
                            db.connection.commit()
                            
                            st.success("✅ Account created successfully!")
                            st.info("👉 You can now login with your credentials in the Login tab")
                            st.balloons()
                        
                        elif db.db_type == "supabase":
                            db.connection.table('users').insert({
                                'username': username,
                                'email': email,
                                'password_hash': password_hash,
                                'full_name': full_name,
                                'role': 'user',
                                'created_at': datetime.now().isoformat()
                            }).execute()
                            
                            st.success("✅ Account created successfully!")
                            st.info("👉 You can now login with your credentials in the Login tab")
                            st.balloons()
                            
                    except Exception as e:
                        error_msg = str(e).lower()
                        if "unique" in error_msg or "duplicate" in error_msg:
                            if "username" in error_msg:
                                st.error("❌ Username already exists. Please choose a different one.")
                            elif "email" in error_msg:
                                st.error("❌ Email already registered. Please use a different email or login.")
                        else:
                            st.error(f"❌ Registration error: {str(e)}")
    
    with tab3:
        st.markdown("### Reset Your Password")
        st.markdown("---")
        
        reset_method = st.radio(
            "Choose reset method:",
            ["1️⃣ Generate Reset Token", "2️⃣ Reset with Token"],
            horizontal=True
        )
        
        if reset_method == "1️⃣ Generate Reset Token":
            with st.form("request_token_form"):
                email = st.text_input("📧 Email Address", placeholder="Enter your registered email")
                submit = st.form_submit_button("📨 Generate Reset Token", use_container_width=True, type="primary")
                
                if submit:
                    if not email:
                        st.error("❌ Please enter your email address")
                    else:
                        try:
                            if db.db_type == "sqlite":
                                cursor = db.connection.cursor()
                                cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
                                result = cursor.fetchone()
                                
                                if result:
                                    import secrets
                                    token = secrets.token_urlsafe(32)
                                    expiry = (datetime.now() + timedelta(hours=1)).isoformat()
                                    
                                    cursor.execute(
                                        "UPDATE users SET reset_token = ?, reset_token_expiry = ? WHERE email = ?",
                                        (token, expiry, email)
                                    )
                                    db.connection.commit()
                                    
                                    st.success("✅ Reset token generated successfully!")
                                    st.code(token, language=None)
                                    st.warning("⚠️ **Important:** Copy this token and use it in the 'Reset with Token' section. Token expires in 1 hour.")
                                else:
                                    st.error("❌ Email not found in our system")
                            
                            elif db.db_type == "supabase":
                                response = db.connection.table('users').select("id").eq('email', email).execute()
                                if response.data:
                                    import secrets
                                    token = secrets.token_urlsafe(32)
                                    expiry = (datetime.now() + timedelta(hours=1)).isoformat()
                                    
                                    db.connection.table('users').update({
                                        'reset_token': token,
                                        'reset_token_expiry': expiry
                                    }).eq('email', email).execute()
                                    
                                    st.success("✅ Reset token generated successfully!")
                                    st.code(token, language=None)
                                    st.warning("⚠️ **Important:** Copy this token and use it in the 'Reset with Token' section. Token expires in 1 hour.")
                                else:
                                    st.error("❌ Email not found in our system")
                                    
                        except Exception as e:
                            st.error(f"❌ Error: {str(e)}")
        
        else:
            with st.form("reset_password_form"):
                token = st.text_input("🔑 Reset Token", placeholder="Paste your reset token here")
                new_password = st.text_input("🔒 New Password", type="password", placeholder="Min 6 characters")
                confirm_password = st.text_input("🔒 Confirm New Password", type="password")
                
                submit = st.form_submit_button("🔄 Reset Password", use_container_width=True, type="primary")
                
                if submit:
                    if not all([token, new_password, confirm_password]):
                        st.error("❌ Please fill in all fields")
                    elif new_password != confirm_password:
                        st.error("❌ Passwords do not match")
                    elif len(new_password) < 6:
                        st.error("❌ Password must be at least 6 characters")
                    else:
                        try:
                            if db.db_type == "sqlite":
                                cursor = db.connection.cursor()
                                cursor.execute(
                                    "SELECT * FROM users WHERE reset_token = ?",
                                    (token,)
                                )
                                result = cursor.fetchone()
                                
                                if result:
                                    columns = [description[0] for description in cursor.description]
                                    user = dict(zip(columns, result))
                                    
                                    expiry = datetime.fromisoformat(user['reset_token_expiry'])
                                    if datetime.now() > expiry:
                                        st.error("❌ Token has expired. Please generate a new one.")
                                    else:
                                        password_hash = hashlib.sha256(new_password.encode()).hexdigest()
                                        cursor.execute("""
                                            UPDATE users 
                                            SET password_hash = ?, reset_token = NULL, reset_token_expiry = NULL
                                            WHERE id = ?
                                        """, (password_hash, user['id']))
                                        db.connection.commit()
                                        
                                        st.success("✅ Password reset successfully!")
                                        st.info("👉 You can now login with your new password")
                                        st.balloons()
                                else:
                                    st.error("❌ Invalid token")
                            
                            elif db.db_type == "supabase":
                                response = db.connection.table('users').select("*").eq('reset_token', token).execute()
                                if response.data:
                                    user = response.data[0]
                                    expiry = datetime.fromisoformat(user['reset_token_expiry'])
                                    
                                    if datetime.now() > expiry:
                                        st.error("❌ Token has expired. Please generate a new one.")
                                    else:
                                        password_hash = hashlib.sha256(new_password.encode()).hexdigest()
                                        db.connection.table('users').update({
                                            'password_hash': password_hash,
                                            'reset_token': None,
                                            'reset_token_expiry': None
                                        }).eq('id', user['id']).execute()
                                        
                                        st.success("✅ Password reset successfully!")
                                        st.info("👉 You can now login with your new password")
                                        st.balloons()
                                else:
                                    st.error("❌ Invalid token")
                                    
                        except Exception as e:
                            st.error(f"❌ Error: {str(e)}")
    
    return False

# ============================================================================
# DATA INTEGRATION SERVICES
# ============================================================================

class ExternalDataService:
    """Integration with external data sources"""
    
    @staticmethod
    def fetch_opensky_flights() -> Optional[pd.DataFrame]:
        """Fetch live flight data from OpenSky Network for Air Sial (IATA: PF)"""
        if not config.OPENSKY_USERNAME:
            return None
        
        try:
            import requests
            auth = (config.OPENSKY_USERNAME, config.OPENSKY_PASSWORD) if config.OPENSKY_PASSWORD else None
            response = requests.get(
                "https://opensky-network.org/api/states/all",
                auth=auth,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('states'):
                    df = pd.DataFrame(data['states'], columns=[
                        'icao24', 'callsign', 'origin_country', 'time_position',
                        'last_contact', 'longitude', 'latitude', 'baro_altitude',
                        'on_ground', 'velocity', 'true_track', 'vertical_rate',
                        'sensors', 'geo_altitude', 'squawk', 'spi', 'position_source'
                    ])
                    # Air Sial IATA code is PF
                    df = df[df['callsign'].str.strip().str.startswith('PF', na=False)]
                    return df
        except Exception as e:
            logger.error(f"OpenSky API error: {e}")
        
        return None
    
    @staticmethod
    def fetch_weather(city: str = "Sialkot") -> Optional[Dict]:
        """Fetch weather data from Open-Meteo (FREE, no API key needed!)"""
        try:
            import requests
            
            # City coordinates (latitude, longitude) - Air Sial hub cities
            city_coords = {
                "Sialkot": (32.4945, 74.5229),  # Air Sial HQ
                "Karachi": (24.8607, 67.0011),
                "Lahore": (31.5204, 74.3587),
                "Islamabad": (33.6844, 73.0479),
                "Peshawar": (34.0151, 71.5249),
                "Quetta": (30.1798, 66.9750),
                "Dubai": (25.2048, 55.2708),
                "Jeddah": (21.4858, 39.1925)
            }
            
            lat, lon = city_coords.get(city, (32.4945, 74.5229))  # Default to Sialkot
            
            # Open-Meteo API - completely free, no API key required!
            url = f"https://api.open-meteo.com/v1/forecast"
            params = {
                'latitude': lat,
                'longitude': lon,
                'current_weather': True,
                'temperature_unit': 'celsius',
                'windspeed_unit': 'ms',
                'timezone': 'auto'
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                current = data.get('current_weather', {})
                
                # Map weather codes to descriptions
                weather_codes = {
                    0: 'Clear sky', 1: 'Mainly clear', 2: 'Partly cloudy', 3: 'Overcast',
                    45: 'Foggy', 48: 'Foggy', 51: 'Light drizzle', 53: 'Moderate drizzle',
                    55: 'Dense drizzle', 61: 'Slight rain', 63: 'Moderate rain',
                    65: 'Heavy rain', 71: 'Slight snow', 73: 'Moderate snow',
                    75: 'Heavy snow', 77: 'Snow grains', 80: 'Slight rain showers',
                    81: 'Moderate rain showers', 82: 'Violent rain showers',
                    85: 'Slight snow showers', 86: 'Heavy snow showers',
                    95: 'Thunderstorm', 96: 'Thunderstorm with hail', 99: 'Thunderstorm with hail'
                }
                
                weather_code = current.get('weathercode', 0)
                description = weather_codes.get(weather_code, 'Unknown')
                
                # Convert to format similar to OpenWeatherMap for compatibility
                return {
                    'main': {
                        'temp': current.get('temperature', 0),
                        'humidity': 50  # Open-Meteo doesn't provide humidity in free tier
                    },
                    'weather': [{
                        'description': description,
                        'main': description.split()[0] if description else 'Clear'
                    }],
                    'wind': {
                        'speed': current.get('windspeed', 0)
                    },
                    'source': 'Open-Meteo (Free)'
                }
                
        except Exception as e:
            logger.error(f"Weather API error: {e}")
        
        return None

# ============================================================================
# NL QUERY ENGINE - USING GEMINI
# ============================================================================

class NLQueryEngine:
    """Natural language query processing with rule-based and Gemini AI fallback"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.rule_patterns = {
            'total_maintenance_hours': ['total maintenance hours', 'sum of maintenance hours', 'maintenance hours total'],
            'emergency_incidents': ['emergency', 'critical incidents', 'show emergency'],
            'delayed_flights': ['delayed flights', 'flight delays', 'delays'],
            'aircraft_status': ['aircraft status', 'status of aircraft', 'fleet status'],
            'recent_incidents': ['recent incidents', 'latest incidents', 'new incidents'],
        }
    
    def process_query(self, query: str) -> Dict[str, Any]:
        """Process natural language query"""
        query_lower = query.lower().strip()
        
        # Try rule-based matching first
        result = self._rule_based_query(query_lower)
        if result:
            return result
        
        # Try Gemini AI-powered query if key available
        if config.GEMINI_API_KEY:
            result = self._gemini_query(query)
            if result:
                return result
        
        return {
            'success': False,
            'message': 'Could not understand query. Try: "total maintenance hours", "show emergency incidents", "delayed flights"',
            'data': None
        }
    
    def _rule_based_query(self, query: str) -> Optional[Dict[str, Any]]:
        """Rule-based query matching"""
        
        if any(pattern in query for pattern in self.rule_patterns['total_maintenance_hours']):
            df = self.db.query('maintenance')
            if not df.empty:
                total_hours = df['hours_spent'].sum()
                return {
                    'success': True,
                    'message': f'Total maintenance hours: {total_hours:,.1f}',
                    'data': df[['aircraft_registration', 'maintenance_type', 'hours_spent', 'status']],
                    'chart_type': 'bar',
                    'metric': total_hours
                }
        
        if any(pattern in query for pattern in self.rule_patterns['emergency_incidents']):
            df = self.db.query('safety_incidents')
            if not df.empty:
                critical_df = df[df['severity'].isin(['Major', 'Critical'])]
                return {
                    'success': True,
                    'message': f'Found {len(critical_df)} critical incidents',
                    'data': critical_df,
                    'chart_type': 'table'
                }
        
        if any(pattern in query for pattern in self.rule_patterns['delayed_flights']):
            df = self.db.query('flights')
            if not df.empty:
                delayed_df = df[df['flight_status'] == 'Delayed']
                return {
                    'success': True,
                    'message': f'Found {len(delayed_df)} delayed flights',
                    'data': delayed_df[['flight_number', 'departure_airport', 'arrival_airport', 
                                        'scheduled_departure', 'delay_reason']],
                    'chart_type': 'table'
                }
        
        if any(pattern in query for pattern in self.rule_patterns['recent_incidents']):
            df = self.db.query('safety_incidents')
            if not df.empty:
                df['incident_date'] = pd.to_datetime(df['incident_date'])
                recent_df = df.nlargest(10, 'incident_date')
                return {
                    'success': True,
                    'message': f'10 most recent incidents',
                    'data': recent_df,
                    'chart_type': 'table'
                }
        
        return None
    
    def _gemini_query(self, query: str) -> Optional[Dict[str, Any]]:
        """Gemini AI-powered query"""
        try:
            schema_info = """
            Available tables:
            1. maintenance: aircraft_registration, maintenance_type, scheduled_date, hours_spent, cost, status, priority
            2. safety_incidents: incident_date, incident_type, severity, aircraft_registration, flight_number, description
            3. flights: flight_number, aircraft_registration, departure_airport, arrival_airport, passengers_count, flight_status
            """
            
            prompt = f"""Given this database schema:
{schema_info}

Determine which table would answer this query: "{query}"

Respond with ONLY the table name: maintenance, safety_incidents, or flights"""
            
            table = GeminiAI.chat(prompt).strip().lower()
            
            # Validate table name
            if table not in ['maintenance', 'safety_incidents', 'flights']:
                return None
            
            df = self.db.query(table)
            
            return {
                'success': True,
                'message': f'Found {len(df)} records in {table}',
                'data': df,
                'chart_type': 'table'
            }
            
        except Exception as e:
            logger.error(f"Gemini query error: {e}")
            return None

# ============================================================================
# AI ANALYSIS ENGINE - USING GEMINI
# ============================================================================

class AIAnalysisEngine:
    """AI-powered analysis and reporting using Gemini"""
    
    @staticmethod
    def analyze_data(df: pd.DataFrame, analysis_type: str, prompt: str = "") -> str:
        """Analyze data and provide insights"""
        if df.empty:
            return "No data available for analysis."
        
        analysis = f"## Data Analysis Results\n\n"
        analysis += f"**Total Records:** {len(df)}\n\n"
        
        if analysis_type == "summary":
            analysis += "### Summary Statistics\n"
            analysis += df.describe().to_markdown() if hasattr(df.describe(), 'to_markdown') else str(df.describe())
        
        elif analysis_type == "trends":
            analysis += "### Trend Analysis\n"
            date_cols = df.select_dtypes(include=['datetime64']).columns
            if len(date_cols) > 0:
                analysis += f"Analyzing trends across {len(date_cols)} time-based dimensions.\n"
            else:
                analysis += "No time-based data found for trend analysis.\n"
        
        elif analysis_type == "anomalies":
            analysis += "### Anomaly Detection\n"
            numeric_cols = df.select_dtypes(include=['number']).columns
            for col in numeric_cols:
                mean = df[col].mean()
                std = df[col].std()
                anomalies = df[(df[col] > mean + 2*std) | (df[col] < mean - 2*std)]
                if len(anomalies) > 0:
                    analysis += f"- **{col}**: {len(anomalies)} potential anomalies detected\n"
        
        elif analysis_type == "root_cause":
            analysis += "### Root Cause Analysis Hints\n"
            analysis += "Based on the data patterns:\n"
            analysis += "- Check correlations between variables\n"
            analysis += "- Review temporal patterns\n"
            analysis += "- Identify common factors in incidents\n"
        
        # If Gemini key available, enhance with AI insights
        if config.GEMINI_API_KEY and prompt:
            try:
                ai_insight = GeminiAI.analyze_data(df, prompt)
                analysis += f"\n\n### AI-Enhanced Insights (Gemini)\n{ai_insight}"
            except Exception as e:
                logger.error(f"AI analysis error: {e}")
        
        return analysis

# ============================================================================
# REPORT GENERATOR
# ============================================================================

class ReportGenerator:
    """Generate downloadable reports in various formats"""
    
    @staticmethod
    def generate_csv_report(df: pd.DataFrame, filename: str) -> bytes:
        """Generate CSV report"""
        return df.to_csv(index=False).encode('utf-8')
    
    @staticmethod
    def generate_excel_report(df: pd.DataFrame, filename: str) -> bytes:
        """Generate Excel report"""
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Report')
        return output.getvalue()
    
    @staticmethod
    def generate_pdf_report(content: str, title: str) -> bytes:
        """Generate PDF report using reportlab"""
        try:
            from reportlab.lib.pagesizes import letter, A4
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.lib import colors
            
            output = BytesIO()
            doc = SimpleDocTemplate(output, pagesize=A4)
            story = []
            styles = getSampleStyleSheet()
            
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                textColor=colors.HexColor(config.PRIMARY_COLOR),
                spaceAfter=30
            )
            story.append(Paragraph(title, title_style))
            story.append(Spacer(1, 0.2*inch))
            
            for line in content.split('\n'):
                if line.strip():
                    if line.startswith('##'):
                        story.append(Paragraph(line.replace('##', ''), styles['Heading2']))
                    elif line.startswith('-'):
                        story.append(Paragraph(line, styles['Bullet']))
                    else:
                        story.append(Paragraph(line, styles['Normal']))
                    story.append(Spacer(1, 0.1*inch))
            
            footer_text = f"Generated by Air Sial Operations System on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            story.append(Spacer(1, 0.5*inch))
            story.append(Paragraph(footer_text, styles['Italic']))
            
            doc.build(story)
            return output.getvalue()
            
        except ImportError:
            return content.encode('utf-8')

# ============================================================================
# PREDICTIVE ANALYTICS
# ============================================================================

class PredictiveAnalytics:
    """Predictive analytics module with baseline models"""
    
    @staticmethod
    def predict_delays(historical_data: pd.DataFrame) -> Dict[str, Any]:
        """Predict flight delays using simple baseline model"""
        if historical_data.empty:
            return {'error': 'Insufficient data'}
        
        try:
            delayed = historical_data[historical_data['flight_status'] == 'Delayed']
            delay_rate = len(delayed) / len(historical_data) * 100
            
            return {
                'overall_delay_rate': f"{delay_rate:.1f}%",
                'high_risk_routes': delayed.groupby('departure_airport').size().nlargest(5).to_dict(),
                'recommendation': 'Consider additional buffer time for high-risk routes',
                'model': 'Baseline Statistical Model'
            }
        except Exception as e:
            return {'error': str(e)}
    
    @staticmethod
    def forecast_maintenance_hours(maintenance_data: pd.DataFrame, periods: int = 30) -> Dict[str, Any]:
        """Forecast maintenance hours using ARIMA baseline"""
        if maintenance_data.empty or len(maintenance_data) < 10:
            return {'error': 'Insufficient historical data (need at least 10 records)'}
        
        try:
            daily_hours = maintenance_data.groupby('scheduled_date')['hours_spent'].sum()
            ma_7 = daily_hours.rolling(window=7).mean()
            forecast_value = ma_7.iloc[-1] if not ma_7.empty else daily_hours.mean()
            
            return {
                'forecast_daily_hours': f"{forecast_value:.1f}",
                'forecast_period': f"{periods} days",
                'total_forecast': f"{forecast_value * periods:.1f} hours",
                'model': 'Moving Average Baseline',
                'note': 'Install statsmodels for ARIMA forecasting'
            }
        except Exception as e:
            return {'error': str(e)}

# ============================================================================
# UI COMPONENTS - ENHANCED WITH AIR SIAL BRANDING
# ============================================================================

def apply_custom_css():
    """Apply custom Air Sial branding and styling - GREEN & GOLD THEME"""
    st.markdown(f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
        
        * {{
            font-family: 'Inter', sans-serif;
        }}
        
        :root {{
            --primary-color: {config.PRIMARY_COLOR};
            --primary-light: {config.PRIMARY_LIGHT};
            --primary-dark: {config.PRIMARY_DARK};
            --secondary-color: {config.SECONDARY_COLOR};
            --accent-color: {config.ACCENT_COLOR};
            --accent-light: {config.ACCENT_LIGHT};
            --text-color: {config.TEXT_COLOR};
            --text-light: {config.TEXT_LIGHT};
            --background: {config.BACKGROUND};
            --card-bg: {config.CARD_BG};
        }}
        
        /* Main app background */
        .stApp {{
            background: linear-gradient(135deg, #f5f7fa 0%, #e8ecef 100%);
        }}
        
        /* Header styling */
        .main-header {{
            background: linear-gradient(135deg, {config.PRIMARY_COLOR} 0%, {config.PRIMARY_DARK} 100%);
            padding: 2.5rem 2rem;
            border-radius: 16px;
            margin-bottom: 2rem;
            color: white;
            box-shadow: 0 10px 30px rgba(4,132,68,0.2);
            position: relative;
            overflow: hidden;
        }}
        
        .main-header::before {{
            content: '';
            position: absolute;
            top: -50%;
            right: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle, rgba(212,175,55,0.15) 0%, transparent 70%);
            animation: shimmer 8s ease-in-out infinite;
        }}
        
        @keyframes shimmer {{
            0%, 100% {{ transform: translate(0, 0); }}
            50% {{ transform: translate(-10%, -10%); }}
        }}
        
        .main-header h1 {{
            margin: 0;
            font-size: 2.8rem;
            font-weight: 800;
            position: relative;
            z-index: 1;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }}
        
        .main-header p {{
            margin: 0.7rem 0 0 0;
            opacity: 0.95;
            font-size: 1.1rem;
            font-weight: 300;
            position: relative;
            z-index: 1;
        }}
        
        /* KPI Cards - Enhanced with Gold accent */
        .kpi-card {{
            background: linear-gradient(135deg, white 0%, #f8f9fa 100%);
            padding: 1.8rem;
            border-radius: 16px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.08);
            border-left: 5px solid {config.PRIMARY_COLOR};
            margin-bottom: 1.5rem;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
        }}
        
        .kpi-card::before {{
            content: '';
            position: absolute;
            top: 0;
            right: 0;
            width: 100px;
            height: 100px;
            background: radial-gradient(circle, {config.ACCENT_COLOR}15 0%, transparent 70%);
            transition: all 0.3s ease;
        }}
        
        .kpi-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 8px 30px rgba(4,132,68,0.15);
            border-left-color: {config.ACCENT_COLOR};
        }}
        
        .kpi-card:hover::before {{
            width: 150px;
            height: 150px;
        }}
        
        .kpi-value {{
            font-size: 2.5rem;
            font-weight: 800;
            background: linear-gradient(135deg, {config.PRIMARY_COLOR} 0%, {config.PRIMARY_LIGHT} 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin: 0.5rem 0;
            position: relative;
            z-index: 1;
        }}
        
        .kpi-label {{
            color: {config.TEXT_LIGHT};
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 1px;
            font-weight: 600;
            position: relative;
            z-index: 1;
        }}
        
        /* Status Badges - Enhanced */
        .status-badge {{
            display: inline-block;
            padding: 0.4rem 1rem;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: 600;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            transition: all 0.2s ease;
        }}
        
        .status-badge:hover {{
            transform: scale(1.05);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }}
        
        .status-success {{ 
            background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%); 
            color: #155724; 
        }}
        .status-warning {{ 
            background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%); 
            color: #856404; 
        }}
        .status-danger {{ 
            background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%); 
            color: #721c24; 
        }}
        .status-info {{ 
            background: linear-gradient(135deg, #d1ecf1 0%, #bee5eb 100%); 
            color: #0c5460; 
        }}
        
        /* Buttons - Enhanced with Gold hover */
        .stButton>button {{
            background: linear-gradient(135deg, {config.PRIMARY_COLOR} 0%, {config.PRIMARY_DARK} 100%);
            color: white;
            border: none;
            border-radius: 12px;
            padding: 0.7rem 2.5rem;
            font-weight: 600;
            font-size: 1rem;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            box-shadow: 0 4px 15px rgba(4,132,68,0.2);
            position: relative;
            overflow: hidden;
        }}
        
        .stButton>button::before {{
            content: '';
            position: absolute;
            top: 50%;
            left: 50%;
            width: 0;
            height: 0;
            border-radius: 50%;
            background: rgba(212,175,55,0.3);
            transform: translate(-50%, -50%);
            transition: width 0.6s, height 0.6s;
        }}
        
        .stButton>button:hover::before {{
            width: 300px;
            height: 300px;
        }}
        
        .stButton>button:hover {{
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(4,132,68,0.3);
        }}
        
        .stButton>button:active {{
            transform: translateY(0);
        }}
        
        /* Forms - Enhanced */
        .stTextInput>div>div>input, 
        .stSelectbox>div>div>div,
        .stTextArea>div>div>textarea {{
            border-radius: 10px;
            border: 2px solid #e0e0e0;
            padding: 0.7rem 1rem;
            transition: all 0.3s ease;
            font-size: 0.95rem;
        }}
        
        .stTextInput>div>div>input:focus, 
        .stSelectbox>div>div>div:focus,
        .stTextArea>div>div>textarea:focus {{
            border-color: {config.PRIMARY_COLOR};
            box-shadow: 0 0 0 3px {config.PRIMARY_COLOR}20;
        }}
        
        /* Tabs - Enhanced with Gold accent */
        .stTabs [data-baseweb="tab-list"] {{
            gap: 8px;
            background-color: white;
            padding: 10px;
            border-radius: 12px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }}
        
        .stTabs [data-baseweb="tab"] {{
            border-radius: 8px;
            padding: 12px 24px;
            font-weight: 600;
            transition: all 0.3s ease;
        }}
        
        .stTabs [data-baseweb="tab"]:hover {{
            background-color: {config.PRIMARY_COLOR}10;
        }}
        
        .stTabs [aria-selected="true"] {{
            background: linear-gradient(135deg, {config.PRIMARY_COLOR} 0%, {config.PRIMARY_DARK} 100%);
            color: white;
        }}
        
        /* Sidebar - Enhanced */
        [data-testid="stSidebar"] {{
            background: linear-gradient(180deg, white 0%, #f8f9fa 100%);
            box-shadow: 4px 0 20px rgba(0,0,0,0.05);
        }}
        
        [data-testid="stSidebar"] .stRadio > label {{
            background: white;
            padding: 0.8rem 1.2rem;
            border-radius: 10px;
            margin-bottom: 0.5rem;
            transition: all 0.3s ease;
            border: 2px solid transparent;
        }}
        
        [data-testid="stSidebar"] .stRadio > label:hover {{
            background: {config.PRIMARY_COLOR}10;
            border-color: {config.PRIMARY_COLOR}30;
            transform: translateX(5px);
        }}
        
        /* Metrics - Enhanced */
        [data-testid="stMetricValue"] {{
            font-size: 2rem;
            font-weight: 800;
            background: linear-gradient(135deg, {config.PRIMARY_COLOR} 0%, {config.PRIMARY_LIGHT} 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        
        /* DataFrames - Enhanced */
        .dataframe {{
            font-size: 0.9rem;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        }}
        
        .dataframe thead tr {{
            background: linear-gradient(135deg, {config.PRIMARY_COLOR} 0%, {config.PRIMARY_DARK} 100%);
            color: white;
        }}
        
        .dataframe tbody tr:hover {{
            background-color: {config.PRIMARY_COLOR}10;
            transition: background-color 0.2s ease;
        }}
        
        /* Expanders - Enhanced */
        .streamlit-expanderHeader {{
            background: linear-gradient(135deg, white 0%, #f8f9fa 100%);
            border-radius: 12px;
            font-weight: 600;
            padding: 1rem;
            transition: all 0.3s ease;
            border: 2px solid #e0e0e0;
        }}
        
        .streamlit-expanderHeader:hover {{
            border-color: {config.PRIMARY_COLOR};
            box-shadow: 0 4px 15px rgba(4,132,68,0.1);
        }}
        
        /* Info/Success/Warning/Error boxes - Enhanced */
        .stAlert {{
            border-radius: 12px;
            border-left-width: 5px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.08);
            animation: slideIn 0.3s ease;
        }}
        
        @keyframes slideIn {{
            from {{
                opacity: 0;
                transform: translateY(-10px);
            }}
            to {{
                opacity: 1;
                transform: translateY(0);
            }}
        }}
        
        /* Dividers - Enhanced */
        hr {{
            margin: 2rem 0;
            border: none;
            height: 2px;
            background: linear-gradient(90deg, transparent 0%, {config.PRIMARY_COLOR}30 50%, transparent 100%);
        }}
        
        /* Code blocks - Enhanced */
        .stCodeBlock {{
            border-radius: 12px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        }}
        
        /* Plotly charts - Enhanced container */
        .js-plotly-plot {{
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.08);
            overflow: hidden;
        }}
        
        /* Scrollbars - Enhanced */
        ::-webkit-scrollbar {{
            width: 10px;
            height: 10px;
        }}
        
        ::-webkit-scrollbar-track {{
            background: #f1f1f1;
            border-radius: 10px;
        }}
        
        ::-webkit-scrollbar-thumb {{
            background: linear-gradient(135deg, {config.PRIMARY_COLOR} 0%, {config.PRIMARY_DARK} 100%);
            border-radius: 10px;
            transition: background 0.3s ease;
        }}
        
        ::-webkit-scrollbar-thumb:hover {{
            background: {config.PRIMARY_DARK};
        }}
        
        /* Loading animation */
        .stSpinner > div {{
            border-color: {config.PRIMARY_COLOR} transparent transparent transparent;
        }}
        
        /* Mobile responsiveness */
        @media (max-width: 768px) {{
            .main-header h1 {{
                font-size: 2rem;
            }}
            .kpi-value {{
                font-size: 1.8rem;
            }}
            .stButton>button {{
                padding: 0.6rem 1.5rem;
                font-size: 0.9rem;
            }}
        }}
        
        /* Animations */
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(20px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        
        .element-container {{
            animation: fadeIn 0.5s ease;
        }}
        
        /* Download buttons - Enhanced with Gold */
        .stDownloadButton>button {{
            background: linear-gradient(135deg, {config.ACCENT_COLOR} 0%, #B8962E 100%);
            color: white;
            border: none;
            border-radius: 12px;
            padding: 0.7rem 2rem;
            font-weight: 600;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(212,175,55,0.2);
        }}
        
        .stDownloadButton>button:hover {{
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(212,175,55,0.3);
        }}
        
        /* File uploader - Enhanced */
        [data-testid="stFileUploader"] {{
            background: white;
            border-radius: 12px;
            padding: 1.5rem;
            border: 2px dashed {config.PRIMARY_COLOR}40;
            transition: all 0.3s ease;
        }}
        
        [data-testid="stFileUploader"]:hover {{
            border-color: {config.PRIMARY_COLOR};
            box-shadow: 0 4px 20px rgba(4,132,68,0.1);
        }}
        
        /* Number input - Enhanced */
        .stNumberInput>div>div>input {{
            border-radius: 10px;
            border: 2px solid #e0e0e0;
            transition: all 0.3s ease;
        }}
        
        .stNumberInput>div>div>input:focus {{
            border-color: {config.PRIMARY_COLOR};
            box-shadow: 0 0 0 3px {config.PRIMARY_COLOR}20;
        }}
        </style>
    """, unsafe_allow_html=True)

def render_header():
    """Render application header with live clock in GMT+5"""
    pkt_time = get_pakistan_time()
    st.markdown(f"""
        <div class="main-header">
            <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;">
                <div style="flex:1;min-width:300px;">
                    <h1>✈️ Air Sial Operations Dashboard</h1>
                    <p>The Pride of Pakistan - Real-time Operational Reporting & Analytics</p>
                </div>
                <div style="text-align:right;min-width:200px;">
                    <div style="background:rgba(212,175,55,0.2);padding:1rem 1.5rem;border-radius:12px;
                                backdrop-filter:blur(10px);border:1px solid rgba(212,175,55,0.3);">
                        <div style="color:white;font-size:0.75rem;opacity:0.9;margin-bottom:0.3rem;">
                            PAKISTAN TIME (GMT+5)
                        </div>
                        <div id="live-clock" style="color:white;font-size:1.8rem;font-weight:700;letter-spacing:1px;">
                            {pkt_time.strftime('%H:%M:%S')}
                        </div>
                        <div id="live-date" style="color:white;font-size:0.75rem;opacity:0.8;margin-top:0.2rem;">
                            {pkt_time.strftime('%a, %d %b %Y')}
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <script>
        function updateClock() {{
            // Get current time in GMT+5 (Pakistan Standard Time)
            const now = new Date();
            const utc = now.getTime() + (now.getTimezoneOffset() * 60000);
            const pkt = new Date(utc + (3600000 * 5)); // GMT+5
            
            // Update time
            const hours = String(pkt.getHours()).padStart(2, '0');
            const minutes = String(pkt.getMinutes()).padStart(2, '0');
            const seconds = String(pkt.getSeconds()).padStart(2, '0');
            const timeString = hours + ':' + minutes + ':' + seconds;
            
            // Update date
            const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
            const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
            const dateString = days[pkt.getDay()] + ', ' + 
                              String(pkt.getDate()).padStart(2, '0') + ' ' + 
                              months[pkt.getMonth()] + ' ' + 
                              pkt.getFullYear();
            
            const clockElement = document.getElementById('live-clock');
            const dateElement = document.getElementById('live-date');
            
            if (clockElement) clockElement.textContent = timeString;
            if (dateElement) dateElement.textContent = dateString;
        }}
        
        // Update immediately and then every second
        updateClock();
        setInterval(updateClock, 1000);
        </script>
    """, unsafe_allow_html=True)

def render_kpi_card(label: str, value: str, delta: str = None):
    """Render a KPI card"""
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">{label}</div>
                <div class="kpi-value">{value}</div>
            </div>
        """, unsafe_allow_html=True)

def create_download_link(data: bytes, filename: str, file_format: str) -> str:
    """Create a download link for reports"""
    b64 = base64.b64encode(data).decode()
    mime_types = {
        'csv': 'text/csv',
        'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'pdf': 'application/pdf'
    }
    return f'<a href="data:{mime_types.get(file_format, "application/octet-stream")};base64,{b64}" download="{filename}">Download {file_format.upper()} Report</a>'

# ============================================================================
# PAGE: DASHBOARD - NO AUTO DEMO DATA
# ============================================================================

def page_dashboard():
    """Main dashboard page with KPIs and charts - NO AUTO DEMO DATA"""
    st.header("📊 Operations Dashboard")
    
    # Fetch data
    maintenance_df = db.query('maintenance', limit=1000)
    incidents_df = db.query('safety_incidents', limit=1000)
    flights_df = db.query('flights', limit=1000)
    
    # Show message if no data instead of auto-generating
    if maintenance_df.empty and incidents_df.empty and flights_df.empty:
        st.info("📝 **No data found.** Please add data using:")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("- **📝 Forms & Submit** - Add individual records")
        with col2:
            st.markdown("- **📤 CSV Upload** - Bulk import data")
        return
    
    # KPI Cards
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        total_maintenance = len(maintenance_df)
        completed = len(maintenance_df[maintenance_df['status']=='Completed']) if not maintenance_df.empty else 0
        st.metric("Maintenance Tasks", total_maintenance, delta=f"{completed} completed")
    
    with col2:
        total_incidents = len(incidents_df)
        critical = len(incidents_df[incidents_df['severity'].isin(['Major', 'Critical'])]) if not incidents_df.empty else 0
        st.metric("Safety Incidents", total_incidents, delta=f"{critical} critical", delta_color="inverse")
    
    with col3:
        total_flights = len(flights_df)
        delayed = len(flights_df[flights_df['flight_status']=='Delayed']) if not flights_df.empty else 0
        st.metric("Total Flights", total_flights, delta=f"{delayed} delayed", delta_color="inverse")
    
    with col4:
        total_hours = maintenance_df['hours_spent'].sum() if not maintenance_df.empty else 0
        st.metric("Maintenance Hours", f"{total_hours:,.0f}", delta="This period")
    
    with col5:
        # Weather summary - FREE, no API key needed! Default to Sialkot (Air Sial HQ)
        weather_data = ExternalDataService.fetch_weather("Sialkot")
        if weather_data:
            temp = weather_data['main']['temp']
            description = weather_data['weather'][0]['description'].title()
            weather_icons = {
                'clear': '☀️', 'mainly': '🌤️', 'partly': '⛅', 'overcast': '☁️',
                'clouds': '☁️', 'rain': '🌧️', 'drizzle': '🌦️',
                'thunderstorm': '⛈️', 'snow': '❄️', 'fog': '🌫️'
            }
            
            # Find matching icon
            icon = '🌤️'
            desc_lower = description.lower()
            for key, emoji in weather_icons.items():
                if key in desc_lower:
                    icon = emoji
                    break
            
            st.metric(f"{icon} Sialkot", f"{temp:.1f}°C", delta=description)
        else:
            st.metric("🌤️ Weather", "Loading...", delta="Fetching data")
    
    st.divider()
    
    # Charts Section
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Maintenance by Type")
        if not maintenance_df.empty:
            maint_type_counts = maintenance_df['maintenance_type'].value_counts()
            fig = px.bar(x=maint_type_counts.index, y=maint_type_counts.values,
                         labels={'x': 'Type', 'y': 'Count'},
                         color_discrete_sequence=[config.PRIMARY_COLOR])
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No maintenance data available")
    
    with col2:
        st.subheader("Safety Incidents by Severity")
        if not incidents_df.empty:
            severity_counts = incidents_df['severity'].value_counts()
            fig = px.pie(values=severity_counts.values, names=severity_counts.index,
                         color_discrete_sequence=[config.PRIMARY_COLOR, config.ACCENT_COLOR, '#FFA500', '#FFD700'])
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No incident data available")
    
    st.divider()
    
    # Timeline Chart
    st.subheader("Flight Operations Timeline")
    if not flights_df.empty:
        flights_df['scheduled_departure'] = pd.to_datetime(flights_df['scheduled_departure'])
        daily_flights = flights_df.groupby(flights_df['scheduled_departure'].dt.date).size().reset_index()
        daily_flights.columns = ['Date', 'Flights']
        
        fig = px.line(daily_flights, x='Date', y='Flights',
                      color_discrete_sequence=[config.PRIMARY_COLOR])
        fig.update_layout(hovermode='x unified')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No flight data available")
    
    # External Data Integration
    with st.expander("🌐 Live External Data"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Live Flight Tracking")
            if st.button("Fetch OpenSky Data"):
                with st.spinner("Fetching live flight data..."):
                    live_flights = ExternalDataService.fetch_opensky_flights()
                    if live_flights is not None and not live_flights.empty:
                        st.success(f"Found {len(live_flights)} Air Sial flights")
                        st.dataframe(live_flights[['callsign', 'origin_country', 'latitude', 'longitude', 'velocity']])
                    else:
                        st.info("No live Air Sial flights found or API key not configured")
        
        with col2:
            st.subheader("Weather Conditions")
            city = st.selectbox("Select Airport City", ["Sialkot", "Karachi", "Lahore", "Islamabad", "Dubai", "Jeddah"])
            if st.button("Fetch Weather"):
                with st.spinner("Fetching weather data..."):
                    weather = ExternalDataService.fetch_weather(city)
                    if weather:
                        st.success("✅ Using Open-Meteo (Free Weather API)")
                        col_a, col_b, col_c = st.columns(3)
                        with col_a:
                            st.metric("Temperature", f"{weather['main']['temp']:.1f}°C")
                        with col_b:
                            st.metric("Conditions", weather['weather'][0]['description'].title())
                        with col_c:
                            st.metric("Wind Speed", f"{weather['wind']['speed']:.1f} m/s")
                    else:
                        st.error("Unable to fetch weather data. Check internet connection.")
    
    # Admin Tools
    if st.session_state.get('current_user', {}).get('role') == 'admin':
        with st.expander("⚙️ Admin Tools"):
            st.warning("**Danger Zone:** These actions cannot be undone!")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("🗑️ Clear Maintenance Data", type="secondary"):
                    if db.clear_table('maintenance'):
                        st.success("Maintenance data cleared!")
                        st.rerun()
            
            with col2:
                if st.button("🗑️ Clear Incidents Data", type="secondary"):
                    if db.clear_table('safety_incidents'):
                        st.success("Incidents data cleared!")
                        st.rerun()
            
            with col3:
                if st.button("🗑️ Clear Flights Data", type="secondary"):
                    if db.clear_table('flights'):
                        st.success("Flights data cleared!")
                        st.rerun()

# ============================================================================
# PAGE: FORMS & SUBMIT
# ============================================================================

def page_forms():
    """CRUD forms for data entry"""
    st.header("📝 Data Entry Forms")
    
    tab1, tab2, tab3 = st.tabs(["✈️ Maintenance", "⚠️ Safety Incident", "🛫 Flight Record"])
    
    with tab1:
        st.subheader("Maintenance Record")
        with st.form("maintenance_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                aircraft = st.text_input("Aircraft Registration*", placeholder="AP-BOA")
                maint_type = st.selectbox("Maintenance Type*", 
                    ["A-Check", "B-Check", "C-Check", "D-Check", "Engine Overhaul", 
                     "Landing Gear", "Avionics", "Interior Refurb"])
                scheduled_date = st.date_input("Scheduled Date*", datetime.now())
                completion_date = st.date_input("Completion Date", None)
            
            with col2:
                technician = st.text_input("Technician Name", placeholder="Tech-001")
                hours = st.number_input("Hours Spent", min_value=0.0, step=0.5)
                cost = st.number_input("Cost (PKR)", min_value=0.0, step=1000.0)
                status = st.selectbox("Status", ["Scheduled", "In Progress", "Completed", "Delayed"])
            
            priority = st.selectbox("Priority", ["Low", "Medium", "High", "Critical"])
            description = st.text_area("Description")
            
            submitted = st.form_submit_button("Submit Maintenance Record")
            
            if submitted:
                if not aircraft or not maint_type:
                    st.error("Please fill required fields marked with *")
                else:
                    record = {
                        'aircraft_registration': aircraft,
                        'maintenance_type': maint_type,
                        'description': description,
                        'scheduled_date': scheduled_date.isoformat(),
                        'completion_date': completion_date.isoformat() if completion_date else None,
                        'technician_name': technician,
                        'hours_spent': hours,
                        'cost': cost,
                        'status': status,
                        'priority': priority
                    }
                    
                    if db.insert('maintenance', record):
                        st.success("✅ Maintenance record created successfully!")
                        st.balloons()
                    else:
                        st.error("Failed to create record")
    
    with tab2:
        st.subheader("Safety Incident Report")
        with st.form("incident_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                incident_date = st.date_input("Incident Date*", datetime.now())
                incident_type = st.selectbox("Incident Type*",
                    ["Bird Strike", "Hard Landing", "Engine Issue", "Weather Diversion",
                     "Cabin Pressure", "Hydraulic Failure", "Ground Incident", "Medical Emergency"])
                severity = st.selectbox("Severity*", ["Minor", "Moderate", "Major", "Critical"])
                aircraft = st.text_input("Aircraft Registration", placeholder="AP-BOA")
            
            with col2:
                flight_number = st.text_input("Flight Number", placeholder="PF121")
                location = st.text_input("Location", placeholder="Sialkot")
                reporter = st.text_input("Reporter Name", placeholder="Capt. Khan")
                investigation_status = st.selectbox("Investigation Status", 
                    ["Open", "Under Investigation", "Closed", "Pending"])
            
            description = st.text_area("Incident Description*", height=100)
            immediate_action = st.text_area("Immediate Action Taken", height=100)
            
            submitted = st.form_submit_button("Submit Incident Report")
            
            if submitted:
                if not incident_date or not incident_type or not severity or not description:
                    st.error("Please fill required fields marked with *")
                else:
                    record = {
                        'incident_date': incident_date.isoformat(),
                        'incident_type': incident_type,
                        'severity': severity,
                        'aircraft_registration': aircraft,
                        'flight_number': flight_number,
                        'location': location,
                        'description': description,
                        'immediate_action': immediate_action,
                        'investigation_status': investigation_status,
                        'reporter_name': reporter
                    }
                    
                    if db.insert('safety_incidents', record):
                        st.success("✅ Incident report submitted successfully!")
                        st.balloons()
                    else:
                        st.error("Failed to submit report")
    
    with tab3:
        st.subheader("Flight Record")
        with st.form("flight_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                flight_number = st.text_input("Flight Number*", placeholder="PF121")
                aircraft = st.text_input("Aircraft Registration*", placeholder="AP-BOA")
                departure = st.text_input("Departure Airport*", placeholder="SKT")
                arrival = st.text_input("Arrival Airport*", placeholder="KHI")
                scheduled_dep = st.text_input("Scheduled Departure*", value=datetime.now().strftime("%Y-%m-%d %H:%M"))
            
            with col2:
                scheduled_arr = st.text_input("Scheduled Arrival*", 
                    value=(datetime.now() + timedelta(hours=2)).strftime("%Y-%m-%d %H:%M"))
                passengers = st.number_input("Passengers", min_value=0, max_value=500, step=1)
                cargo = st.number_input("Cargo Weight (kg)", min_value=0.0, step=100.0)
                status = st.selectbox("Status", 
                    ["Scheduled", "On Time", "Delayed", "Departed", "Arrived", "Cancelled"])
                captain = st.text_input("Captain Name", placeholder="Capt. Khan")
            
            delay_reason = st.text_input("Delay Reason (if applicable)")
            
            submitted = st.form_submit_button("Submit Flight Record")
            
            if submitted:
                if not flight_number or not aircraft or not departure or not arrival:
                    st.error("Please fill required fields marked with *")
                else:
                    record = {
                        'flight_number': flight_number,
                        'aircraft_registration': aircraft,
                        'departure_airport': departure,
                        'arrival_airport': arrival,
                        'scheduled_departure': scheduled_dep,
                        'actual_departure': None,
                        'scheduled_arrival': scheduled_arr,
                        'actual_arrival': None,
                        'passengers_count': passengers,
                        'cargo_weight': cargo,
                        'flight_status': status,
                        'delay_reason': delay_reason,
                        'captain_name': captain
                    }
                    
                    if db.insert('flights', record):
                        st.success("✅ Flight record created successfully!")
                        st.balloons()
                    else:
                        st.error("Failed to create record")

# ============================================================================
# PAGE: CSV UPLOAD
# ============================================================================

def page_csv_upload():
    """Bulk CSV upload with flexible header mapping"""
    st.header("📤 CSV Bulk Upload")
    
    st.markdown("### 📥 Download CSV Templates")
    st.info("💡 **New to bulk upload?** Download a template file below, fill it with your data, and upload it back!")
    
    col1, col2, col3 = st.columns(3)
    
    templates = {
        'maintenance': {
            'data': """aircraft_registration,maintenance_type,description,scheduled_date,completion_date,technician_name,hours_spent,cost,status,priority
AP-BOA,A-Check,Routine A-Check inspection and servicing,2024-01-15,2024-01-16,Tech-101,8.5,45000,Completed,Medium
AP-BOB,Engine Overhaul,Complete engine overhaul - left engine,2024-02-20,,Tech-205,0,350000,Scheduled,High
AP-BOC,Landing Gear,Landing gear inspection and maintenance,2024-01-28,2024-01-29,Tech-150,12.0,85000,Completed,High""",
            'filename': 'maintenance_template.csv',
            'icon': '✈️'
        },
        'safety_incidents': {
            'data': """incident_date,incident_type,severity,aircraft_registration,flight_number,location,description,immediate_action,investigation_status,reporter_name
2024-01-10,Bird Strike,Minor,AP-BOA,PF121,Sialkot,Bird strike during takeoff - windshield damage,Flight continued safely - windshield inspected upon landing,Closed,Capt. Khan-201
2024-01-15,Hard Landing,Moderate,AP-BOB,PF150,Karachi,Hard landing due to wind shear conditions,Aircraft inspected - no structural damage found,Closed,Capt. Ahmed-305
2024-01-22,Engine Issue,Major,AP-BOC,PF205,Dubai,Engine vibration detected during cruise,Emergency landing protocol initiated - landed safely,Under Investigation,Capt. Hassan-410""",
            'filename': 'safety_incidents_template.csv',
            'icon': '⚠️'
        },
        'flights': {
            'data': """flight_number,aircraft_registration,departure_airport,arrival_airport,scheduled_departure,scheduled_arrival,passengers_count,cargo_weight,flight_status,delay_reason,captain_name
PF121,AP-BOA,SKT,ISB,2024-01-15 08:00,2024-01-15 09:00,145,5500,Arrived,,Capt. Khan-201
PF122,AP-BOB,ISB,SKT,2024-01-15 10:30,2024-01-15 11:30,138,4200,Arrived,,Capt. Ahmed-305
PF150,AP-BOC,SKT,KHI,2024-01-16 14:00,2024-01-16 16:00,162,6000,Delayed,Technical,Capt. Hassan-410""",
            'filename': 'flights_template.csv',
            'icon': '🛫'
        }
    }
    
    with col1:
        st.markdown(f"#### {templates['maintenance']['icon']} Maintenance")
        st.download_button(
            label="Download Template",
            data=templates['maintenance']['data'],
            file_name=templates['maintenance']['filename'],
            mime='text/csv',
            key='download_maintenance',
            use_container_width=True
        )
    
    with col2:
        st.markdown(f"#### {templates['safety_incidents']['icon']} Safety Incidents")
        st.download_button(
            label="Download Template",
            data=templates['safety_incidents']['data'],
            file_name=templates['safety_incidents']['filename'],
            mime='text/csv',
            key='download_incidents',
            use_container_width=True
        )
    
    with col3:
        st.markdown(f"#### {templates['flights']['icon']} Flights")
        st.download_button(
            label="Download Template",
            data=templates['flights']['data'],
            file_name=templates['flights']['filename'],
            mime='text/csv',
            key='download_flights',
            use_container_width=True
        )
    
    st.divider()
    
    st.markdown("### 📤 Upload Your CSV File")
    
    table_choice = st.selectbox("Select Target Table", 
        ["maintenance", "safety_incidents", "flights"])
    
    st.info("📋 Upload a CSV file to bulk import records. The system will help you map columns to database fields.")
    
    # Modified section with delete button
    uploaded_file = st.file_uploader("Choose CSV file", type=['csv'], key="csv_file_uploader")
    
    # Add the delete button if a file is present
    if uploaded_file is not None:
        if st.button("🗑️ Delete/Clear Uploaded File", type="secondary"):
            st.session_state.csv_file_uploader = None
            st.rerun()
    
    if uploaded_file:
        try:
            df = pd.read_csv(uploaded_file)
            st.success(f"✅ File uploaded: {len(df)} rows found")
            
            st.subheader("Preview Data")
            st.dataframe(df.head())
            
            st.subheader("Map Columns")
            
            expected_columns = {
                'maintenance': ['aircraft_registration', 'maintenance_type', 'scheduled_date', 
                                'technician_name', 'hours_spent', 'cost', 'status', 'priority'],
                'safety_incidents': ['incident_date', 'incident_type', 'severity', 
                                     'aircraft_registration', 'description', 'investigation_status'],
                'flights': ['flight_number', 'aircraft_registration', 'departure_airport', 
                            'arrival_airport', 'scheduled_departure', 'scheduled_arrival', 
                            'passengers_count', 'flight_status']
            }
            
            column_mapping = {}
            cols = st.columns(2)
            
            for idx, expected_col in enumerate(expected_columns[table_choice]):
                with cols[idx % 2]:
                    mapped = st.selectbox(
                        f"Map '{expected_col}'",
                        options=['-- Skip --'] + list(df.columns),
                        key=f"map_{expected_col}"
                    )
                    if mapped != '-- Skip --':
                        column_mapping[expected_col] = mapped
            
            if st.button("Import Data", type="primary"):
                with st.spinner("Importing data..."):
                    records = []
                    for _, row in df.iterrows():
                        record = {}
                        for expected, actual in column_mapping.items():
                            record[expected] = row[actual]
                        records.append(record)
                    
                    success_count = db.bulk_insert(table_choice, records)
                    
                    if success_count > 0:
                        st.success(f"✅ Successfully imported {success_count} out of {len(records)} records!")
                        st.balloons()
                    else:
                        st.error("Failed to import records")
        
        except Exception as e:
            st.error(f"Error processing file: {e}")

# ============================================================================
# PAGE: DATA MANAGEMENT
# ============================================================================

def page_data_management():
    """View, edit, and delete records"""
    st.header("🗂️ Data Management")
    
    table = st.selectbox("Select Table", ["maintenance", "safety_incidents", "flights"])
    
    df = db.query(table, limit=1000)
    
    if df.empty:
        st.warning("No records found")
        return
    
    st.subheader(f"Total Records: {len(df)}")
    
    with st.expander("🔍 Filters"):
        col1, col2 = st.columns(2)
        
        with col1:
            if 'aircraft_registration' in df.columns:
                aircraft_filter = st.multiselect("Aircraft", df['aircraft_registration'].unique())
                if aircraft_filter:
                    df = df[df['aircraft_registration'].isin(aircraft_filter)]
        
        with col2:
            if 'status' in df.columns:
                status_filter = st.multiselect("Status", df['status'].unique())
                if status_filter:
                    df = df[df['status'].isin(status_filter)]
            elif 'flight_status' in df.columns:
                status_filter = st.multiselect("Status", df['flight_status'].unique())
                if status_filter:
                    df = df[df['flight_status'].isin(status_filter)]
    
    st.dataframe(df, use_container_width=True, height=400)
    
    st.subheader("Edit/Delete Record")
    
    if 'id' in df.columns:
        record_id = st.number_input("Record ID to Edit/Delete", min_value=1, step=1)
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🗑️ Delete Record", type="secondary"):
                if db.delete(table, record_id):
                    st.success("Record deleted successfully!")
                    st.rerun()
                else:
                    st.error("Failed to delete record")
        
        with col2:
            if st.button("✏️ View/Edit"):
                record = df[df['id'] == record_id]
                if not record.empty:
                    st.json(record.iloc[0].to_dict())
                else:
                    st.error("Record not found")

# ============================================================================
# PAGE: NL/AI QUERY - USING GEMINI
# ============================================================================

def page_nl_query():
    """Natural language query interface with Gemini AI"""
    st.header("💬 Natural Language Query")
    
    st.markdown("""
    Ask questions about your operations data in plain English. Examples:
    - "Total maintenance hours"
    - "Show emergency incidents"
    - "Delayed flights"
    - "Recent incidents"
    """)
    
    query_engine = NLQueryEngine(db)
    
    query = st.text_input("Enter your question:", placeholder="Total maintenance hours")
    
    if st.button("Search", type="primary"):
        if query:
            with st.spinner("Processing query..."):
                result = query_engine.process_query(query)
                
                if result['success']:
                    st.success(result['message'])
                    
                    if result['data'] is not None and not result['data'].empty:
                        if 'metric' in result:
                            st.metric("Result", f"{result['metric']:,.1f}")
                        
                        st.subheader("Query Results")
                        
                        if result.get('chart_type') == 'table':
                            st.dataframe(result['data'], use_container_width=True)
                        elif result.get('chart_type') == 'bar':
                            fig = px.bar(result['data'], x='maintenance_type', y='hours_spent',
                                       color='status', barmode='group')
                            st.plotly_chart(fig, use_container_width=True)
                        
                        csv = result['data'].to_csv(index=False)
                        st.download_button(
                            "Download Results",
                            csv,
                            f"query_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            "text/csv"
                        )
                else:
                    st.warning(result['message'])
        else:
            st.error("Please enter a query")
    
    st.divider()
    st.subheader("🤖 AI Analysis Assistant")
    
    # Check if Gemini is configured
    if not config.GEMINI_API_KEY:
        st.warning("💡 **Gemini AI not configured.** Add GEMINI_API_KEY to your secrets to enable AI analysis.")
        return
    
    st.success("✅ Gemini AI is enabled and ready!")
    
    analysis_prompt = st.text_area("Ask for analysis or insights:", 
        placeholder="Analyze maintenance trends and suggest optimizations...")
    
    analysis_type = st.selectbox("Analysis Type", 
        ["summary", "trends", "anomalies", "root_cause"])
    
    table_for_analysis = st.selectbox("Data Source", 
        ["maintenance", "safety_incidents", "flights"])
    
    if st.button("Analyze", type="primary"):
        if analysis_prompt:
            with st.spinner("Analyzing data with Gemini AI..."):
                df = db.query(table_for_analysis, limit=1000)
                
                if df.empty:
                    st.warning("No data available for analysis")
                else:
                    analysis = AIAnalysisEngine.analyze_data(df, analysis_type, analysis_prompt)
                    st.markdown(analysis)
                    
                    st.subheader("Download Analysis Report")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        pdf_data = ReportGenerator.generate_pdf_report(analysis, "AI Analysis Report")
                        st.download_button("Download PDF", pdf_data, 
                                          f"analysis_{datetime.now().strftime('%Y%m%d')}.pdf",
                                          "application/pdf")
                    
                    with col2:
                        csv_data = df.to_csv(index=False).encode('utf-8')
                        st.download_button("Download CSV", csv_data,
                                          f"data_{datetime.now().strftime('%Y%m%d')}.csv",
                                          "text/csv")

# ============================================================================
# PAGE: GENERIC AI CHAT
# ============================================================================

def page_ai_chat():
    """Generic AI chat assistant using Gemini"""
    st.header("🤖 AI Assistant")
    
    st.markdown("""
    Chat with an AI assistant about anything! This is a general-purpose chat,
    separate from data analysis. Ask questions, get advice, or just have a conversation.
    """)
    
    # Check if Gemini is configured
    if not config.GEMINI_API_KEY and not config.GROQ_API_KEY:
        st.error("❌ **AI not configured.** Please add either GEMINI_API_KEY or GROQ_API_KEY to your secrets.")
        st.info("""
        **How to add API keys:**
        1. Go to Settings → Secrets
        2. Add your Gemini API key: `GEMINI_API_KEY = "your-key-here"`
        3. Or add Groq API key: `GROQ_API_KEY = "your-key-here"`
        4. Restart the app
        """)
        return
    
    # Choose AI provider
    if config.GEMINI_API_KEY and config.GROQ_API_KEY:
        ai_provider = st.selectbox("AI Provider", ["Gemini (Google)", "Groq (Fast)"])
    elif config.GEMINI_API_KEY:
        ai_provider = "Gemini (Google)"
        st.success("✅ Using Gemini AI")
    else:
        ai_provider = "Groq (Fast)"
        st.success("✅ Using Groq AI")
    
    # Initialize chat history
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    # Clear chat button
    col1, col2 = st.columns([4, 1])
    with col2:
        if st.button("🗑️ Clear Chat"):
            st.session_state.chat_history = []
            st.rerun()
    
    # Display chat history
    for message in st.session_state.chat_history:
        if message['role'] == 'user':
            st.markdown(f"**You:** {message['content']}")
        else:
            st.markdown(f"**AI:** {message['content']}")
        st.divider()
    
    # Chat input
    user_message = st.text_area("Your message:", placeholder="Ask me anything...", height=100, key="chat_input")
    
    col1, col2 = st.columns([1, 4])
    with col1:
        send_button = st.button("📤 Send", type="primary", use_container_width=True)
    
    if send_button and user_message:
        # Add user message to history
        st.session_state.chat_history.append({'role': 'user', 'content': user_message})
        
        with st.spinner("AI is thinking..."):
            # Get AI response
            system_prompt = """You are a helpful AI assistant for Air Sial - The Pride of Pakistan. 
Be friendly, informative, and concise. Help the user with any questions they have, 
whether about airline operations, technology, or general topics."""
            
            if "Gemini" in ai_provider:
                ai_response = GeminiAI.chat(user_message, system_prompt)
            else:
                ai_response = GroqAI.chat(user_message, system_prompt)
            
            # Add AI response to history
            st.session_state.chat_history.append({'role': 'assistant', 'content': ai_response})
        
        st.rerun()
    
    # Example questions
    with st.expander("💡 Example Questions"):
        st.markdown("""
        **General:**
        - What are best practices for airline maintenance?
        - Explain the difference between A-Check and C-Check
        - How to improve on-time performance?
        
        **Technical:**
        - What is predictive maintenance?
        - Explain aircraft turnaround time optimization
        - Best practices for safety reporting
        
        **Casual:**
        - What's the weather like today?
        - Tell me a joke
        - Give me productivity tips
        """)

# ============================================================================
# PAGE: REPORTS
# ============================================================================

def page_reports():
    """Generate scheduled and on-demand reports"""
    st.header("📊 Reports & Analytics")
    
    tab1, tab2, tab3 = st.tabs(["📅 Scheduled Reports", "🔮 Predictive Analytics", "📈 Custom Report"])
    
    with tab1:
        st.subheader("Generate Reports")
        
        col1, col2 = st.columns(2)
        
        with col1:
            report_type = st.selectbox("Report Type", 
                ["Maintenance Summary", "Safety Report", "Flight Operations", "Comprehensive"])
            
            period = st.selectbox("Period", 
                ["Weekly", "Bi-Monthly", "Monthly", "Quarterly", "Bi-Annual", "Annual"])
        
        with col2:
            date_from = st.date_input("From Date", datetime.now() - timedelta(days=30))
            date_to = st.date_input("To Date", datetime.now())
            
            format_choice = st.selectbox("Format", ["PDF", "Excel", "CSV"])
        
        if st.button("Generate Report", type="primary"):
            with st.spinner("Generating report..."):
                if report_type == "Maintenance Summary":
                    df = db.query('maintenance', limit=1000)
                elif report_type == "Safety Report":
                    df = db.query('safety_incidents', limit=1000)
                elif report_type == "Flight Operations":
                    df = db.query('flights', limit=1000)
                else:
                    maint = db.query('maintenance', limit=500)
                    incidents = db.query('safety_incidents', limit=500)
                    flights = db.query('flights', limit=500)
                    
                    report_content = f"""
# Air Sial Operations Comprehensive Report
**Period:** {date_from} to {date_to}

## Maintenance Summary
- Total Tasks: {len(maint)}
- Total Hours: {maint['hours_spent'].sum() if not maint.empty else 0:,.1f}
- Total Cost: PKR {maint['cost'].sum() if not maint.empty else 0:,.2f}

## Safety Summary
- Total Incidents: {len(incidents)}
- Critical Incidents: {len(incidents[incidents['severity'].isin(['Major', 'Critical'])]) if not incidents.empty else 0}

## Flight Operations
- Total Flights: {len(flights)}
- Delayed: {len(flights[flights['flight_status']=='Delayed']) if not flights.empty else 0}
- Total Passengers: {flights['passengers_count'].sum() if not flights.empty else 0:,.0f}
"""
                    
                    if format_choice == "PDF":
                        report_data = ReportGenerator.generate_pdf_report(report_content, 
                            f"{report_type} - {period}")
                        st.download_button("Download PDF Report", report_data,
                            f"comprehensive_report_{datetime.now().strftime('%Y%m%d')}.pdf",
                            "application/pdf")
                    
                    st.markdown(report_content)
                    st.success("Report generated successfully!")
                    return
                
                if not df.empty:
                    if format_choice == "CSV":
                        csv_data = ReportGenerator.generate_csv_report(df, f"{report_type}.csv")
                        st.download_button("Download CSV", csv_data,
                            f"{report_type.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.csv",
                            "text/csv")
                    elif format_choice == "Excel":
                        excel_data = ReportGenerator.generate_excel_report(df, f"{report_type}.xlsx")
                        st.download_button("Download Excel", excel_data,
                            f"{report_type.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.xlsx",
                            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                    
                    st.dataframe(df, use_container_width=True)
                    st.success("Report generated successfully!")
                else:
                    st.warning("No data available for selected criteria")
    
    with tab2:
        st.subheader("Predictive Models")
        
        st.info("📊 Basic predictive models using historical data")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Flight Delay Prediction")
            if st.button("Predict Delays"):
                flights_df = db.query('flights', limit=1000)
                if flights_df.empty:
                    st.warning("No flight data available")
                else:
                    predictions = PredictiveAnalytics.predict_delays(flights_df)
                    
                    if 'error' not in predictions:
                        st.metric("Overall Delay Rate", predictions['overall_delay_rate'])
                        st.json(predictions['high_risk_routes'])
                        st.info(predictions['recommendation'])
                        st.caption(f"Model: {predictions['model']}")
                    else:
                        st.error(predictions['error'])
        
        with col2:
            st.markdown("### Maintenance Hours Forecast")
            forecast_days = st.number_input("Forecast Days", min_value=7, max_value=90, value=30)
            
            if st.button("Forecast Hours"):
                maint_df = db.query('maintenance', limit=1000)
                if maint_df.empty:
                    st.warning("No maintenance data available")
                else:
                    forecast = PredictiveAnalytics.forecast_maintenance_hours(maint_df, forecast_days)
                    
                    if 'error' not in forecast:
                        st.metric("Daily Forecast", forecast['forecast_daily_hours'])
                        st.metric("Total Forecast", forecast['total_forecast'])
                        st.caption(f"Model: {forecast['model']}")
                        if 'note' in forecast:
                            st.info(forecast['note'])
                    else:
                        st.error(forecast['error'])
    
    with tab3:
        st.subheader("Custom Report Builder")
        
        st.markdown("Build a custom report with selected metrics and visualizations")
        
        data_sources = st.multiselect("Data Sources", 
            ["Maintenance", "Safety Incidents", "Flights"])
        
        metrics = st.multiselect("Metrics to Include",
            ["Total Records", "Date Range", "Status Breakdown", "Cost Analysis", 
             "Trend Charts", "Top 10 Items"])
        
        if st.button("Build Custom Report"):
            st.info("🚧 Custom report builder - Feature in development!")

# ============================================================================
# MAIN APPLICATION
# ============================================================================

def main():
    """Main application entry point"""
    
    st.set_page_config(
        page_title="Air Sial Operations",
        page_icon="✈️",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    apply_custom_css()
    
    if not check_password():
        return
    
    render_header()
    
    with st.sidebar:
        # Air Sial Logo placeholder
        st.markdown(f"""
            <div style="text-align:center;padding:1rem;margin-bottom:1rem;">
                <div style="font-size:2.5rem;margin-bottom:0.5rem;">✈️</div>
                <div style="background:linear-gradient(135deg, {config.PRIMARY_COLOR} 0%, {config.PRIMARY_DARK} 100%);
                            -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                            font-size:1.5rem;font-weight:800;">Air Sial</div>
                <div style="color:{config.ACCENT_COLOR};font-size:0.8rem;font-weight:600;">The Pride of Pakistan</div>
            </div>
        """, unsafe_allow_html=True)
        
        # Live Clock - GMT+5 (Pakistan Standard Time)
        pkt_time = get_pakistan_time()
        st.markdown(f"""
            <div style="background:linear-gradient(135deg, {config.PRIMARY_COLOR} 0%, {config.PRIMARY_DARK} 100%);
                        padding:1.5rem;border-radius:12px;margin-bottom:1rem;text-align:center;
                        box-shadow:0 4px 15px rgba(4,132,68,0.2);">
                <div style="color:white;font-size:0.85rem;font-weight:600;margin-bottom:0.3rem;opacity:0.9;">
                    🕐 PAKISTAN TIME (GMT+5)
                </div>
                <div style="color:white;font-size:1.8rem;font-weight:800;letter-spacing:1px;">
                    {pkt_time.strftime('%H:%M:%S')}
                </div>
                <div style="color:white;font-size:0.85rem;opacity:0.8;margin-top:0.3rem;">
                    {pkt_time.strftime('%A, %B %d, %Y')}
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        # Weather City Selector
        weather_city = st.selectbox(
            "🌍 Weather Location",
            ["Sialkot", "Karachi", "Lahore", "Islamabad", "Peshawar", "Quetta", "Dubai", "Jeddah"],
            index=0,
            key="weather_city_selector"
        )
        
        # Weather Widget - FREE (No API key needed!)
        weather_data = ExternalDataService.fetch_weather(weather_city)
        if weather_data:
            temp = weather_data['main']['temp']
            description = weather_data['weather'][0]['description'].title()
            wind_speed = weather_data['wind']['speed']
            
            # Weather icon mapping
            weather_icons = {
                'clear': '☀️', 'mainly': '🌤️', 'partly': '⛅', 'overcast': '☁️',
                'clouds': '☁️', 'rain': '🌧️', 'drizzle': '🌦️',
                'thunderstorm': '⛈️', 'snow': '❄️', 'fog': '🌫️',
                'haze': '🌫️', 'dust': '💨', 'smoke': '💨'
            }
            
            # Find matching icon
            icon = '🌤️'
            desc_lower = description.lower()
            for key, emoji in weather_icons.items():
                if key in desc_lower:
                    icon = emoji
                    break
            
            st.markdown(f"""
                <div style="background:linear-gradient(135deg, #4A90E2 0%, #357ABD 100%);
                            padding:1.5rem;border-radius:12px;margin-bottom:1rem;text-align:center;
                            box-shadow:0 4px 15px rgba(74,144,226,0.2);">
                    <div style="color:white;font-size:0.85rem;font-weight:600;margin-bottom:0.3rem;opacity:0.9;">
                        🌍 {weather_city.upper()} WEATHER
                    </div>
                    <div style="color:white;font-size:3rem;margin:0.5rem 0;">
                        {icon}
                    </div>
                    <div style="color:white;font-size:2rem;font-weight:800;margin-bottom:0.3rem;">
                        {temp:.1f}°C
                    </div>
                    <div style="color:white;font-size:0.95rem;opacity:0.9;margin-bottom:0.8rem;">
                        {description}
                    </div>
                    <div style="display:flex;justify-content:space-around;color:white;font-size:0.8rem;">
                        <div style="text-align:center;">
                            <div style="opacity:0.8;">💨 Wind</div>
                            <div style="font-weight:600;">{wind_speed:.1f} m/s</div>
                        </div>
                        <div style="text-align:center;">
                            <div style="opacity:0.8;">📡 Source</div>
                            <div style="font-weight:600;">Open-Meteo</div>
                        </div>
                    </div>
                    <div style="color:white;font-size:0.7rem;opacity:0.7;margin-top:0.5rem;">
                        ✨ Free Weather API
                    </div>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
                <div style="background:linear-gradient(135deg, #95a5a6 0%, #7f8c8d 100%);
                            padding:1.5rem;border-radius:12px;margin-bottom:1rem;text-align:center;
                            box-shadow:0 4px 15px rgba(149,165,166,0.2);">
                    <div style="color:white;font-size:0.85rem;font-weight:600;margin-bottom:0.5rem;">
                        🌍 {weather_city.upper()} WEATHER
                    </div>
                    <div style="color:white;font-size:0.9rem;opacity:0.8;">
                        Unable to fetch weather data.<br>Check your internet connection.
                    </div>
                </div>
            """, unsafe_allow_html=True)
        
        st.title("Navigation")
        
        page = st.radio("Go to", [
            "📊 Dashboard",
            "📝 Forms & Submit",
            "📤 CSV Upload",
            "🗂️ Data Management",
            "💬 NL/AI Query",
            "🤖 AI Assistant",
            "📊 Reports"
        ])
        
        st.divider()
        
        # Auto-refresh toggle for live updates
        auto_refresh = st.checkbox("🔄 Auto-refresh (30s)", value=False)
        if auto_refresh:
            st.caption("Live updates enabled")
            time.sleep(30)
            st.rerun()
        
        if st.session_state.get('current_user'):
            user = st.session_state.current_user
            st.markdown(f"### 👤 {user['full_name']}")
            st.caption(f"@{user['username']} | {user['role'].title()}")
            
            if st.button("🚪 Logout", use_container_width=True, type="secondary"):
                st.session_state.authenticated = False
                st.session_state.current_user = None
                st.session_state.chat_history = []
                st.success("Logged out successfully!")
                time.sleep(1)
                st.rerun()
            
            st.divider()
        
        st.subheader("System Status")
        st.caption(f"Database: {db.db_type.upper()}")
        st.caption(f"Mode: {config.APP_MODE.upper()}")
        
        # AI Status
        if config.GEMINI_API_KEY:
            st.success("✅ Gemini AI Enabled")
        elif config.GROQ_API_KEY:
            st.success("✅ Groq AI Enabled")
        else:
            st.info("ℹ️ AI Disabled")
        
        st.divider()
        
        st.subheader("Quick Stats")
        maint_count = len(db.query('maintenance', limit=10))
        incidents_count = len(db.query('safety_incidents', limit=10))
        flights_count = len(db.query('flights', limit=10))
        
        st.metric("Maintenance", maint_count)
        st.metric("Incidents", incidents_count)
        st.metric("Flights", flights_count)
    
    # Route to pages
    if "Dashboard" in page:
        page_dashboard()
    elif "Forms" in page:
        page_forms()
    elif "CSV" in page:
        page_csv_upload()
    elif "Data Management" in page:
        page_data_management()
    elif "NL/AI Query" in page:
        page_nl_query()
    elif "AI Assistant" in page:
        page_ai_chat()
    elif "Reports" in page:
        page_reports()
    
    st.divider()
    st.caption("© 2025 Air Sial - The Pride of Pakistan - Operations Management System v2.0 | Powered by Gemini AI")

if __name__ == "__main__":
    main()
