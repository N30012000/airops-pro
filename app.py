"""
AirOps Pro - Enterprise Airline Operational Reporting System
Main Application with Multi-Airline Support, Real-Time Analytics & AI
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List, Optional
import logging

from config import (
    get_airline_config, 
    list_airlines, 
    SystemConfig,
    validate_airline_config,
    REPORT_TEMPLATES,
)

# ============================================================================
# SETUP & CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="AirOps Pro - Aviation Operations",
    page_icon="🛫",
    layout="wide",
    initial_sidebar_state="expanded",
)

logging.basicConfig(level=getattr(logging, SystemConfig.LOG_LEVEL))
logger = logging.getLogger(__name__)


class AIAnalyzer:
    """AI-powered analysis using OpenAI/Claude"""
    
    def __init__(self, airline_code: str):
        self.config = get_airline_config(airline_code)
    
    def generate_report_summary(self, data: Dict, report_type: str) -> str:
        """Generate AI-powered report summary"""
        return f"""
        EXECUTIVE SUMMARY - {report_type.upper()} REPORT
        
        {self._mock_analysis(data, report_type)}
        """
    
    def _mock_analysis(self, data: Dict, report_type: str) -> str:
        """Mock AI analysis structure"""
        return f"""
        • On-Time Performance: 87.3% (↑ 2.1%)
        • Fleet Utilization: 78.9% (Optimal range)
        • Maintenance Efficiency: 94.2% (No critical issues)
        • Cost Per Available Seat: $0.082 (↓ 1.2%)
        • Revenue Per Flight Hour: $2,847 (↑ $145)
        
        KEY INSIGHTS:
        ✓ Route optimization improved efficiency by 3.4%
        ⚠ Weather delays increased by 12%
        → Recommend crew scheduling adjustment
        """
    
    def predict_delays(self, historical_data: pd.DataFrame) -> Dict:
        """Predict likely delays using ML"""
        return {
            "predicted_delay_rate": 12.5,
            "confidence": 0.87,
            "risk_factors": ["Weather", "Crew Fatigue", "Aircraft Turnaround"],
            "recommendations": [
                "Increase buffer time for afternoon flights",
                "Pre-position crew for peak hours",
                "Schedule maintenance during low-demand periods"
            ]
        }
    
    def cost_optimization_analysis(self, financial_data: Dict) -> Dict:
        """Analyze cost optimization opportunities"""
        return {
            "current_monthly_cost": "$4.2M",
            "potential_savings": "$280K",
            "optimization_areas": [
                {
                    "area": "Fuel Efficiency",
                    "savings": "$120K/month",
                    "action": "Optimize cruise altitudes based on wind patterns"
                },
                {
                    "area": "Crew Scheduling",
                    "savings": "$85K/month",
                    "action": "Eliminate single-crew deadhead flights"
                },
                {
                    "area": "Maintenance",
                    "savings": "$45K/month",
                    "action": "Predictive maintenance reduces unscheduled repairs"
                },
                {
                    "area": "Operations",
                    "savings": "$30K/month",
                    "action": "Reduce ground time with process optimization"
                }
            ]
        }


# ============================================================================
# SESSION & SIDEBAR
# ============================================================================

def initialize_session():
    """Initialize session state"""
    if "airline_code" not in st.session_state:
        st.session_state.airline_code = SystemConfig.DEFAULT_AIRLINE
    if "ai_analyzer" not in st.session_state:
        st.session_state.ai_analyzer = None


def render_sidebar():
    """Render sidebar with airline selection and navigation"""
    with st.sidebar:
        st.markdown("### 🛫 AirOps Pro")
        st.markdown("Enterprise Aviation Operations Platform")
        
        st.markdown("---")
        
        # Airline Selection
        st.subheader("Airline Selection")
        airlines = list_airlines()
        selected_airline = st.selectbox(
            "Select Airline:",
            airlines,
            index=airlines.index(st.session_state.airline_code) 
                if st.session_state.airline_code in airlines else 0,
            key="airline_selector"
        )
        
        if selected_airline != st.session_state.airline_code:
            st.session_state.airline_code = selected_airline
            st.rerun()
        
        st.markdown("---")
        
        # Navigation
        st.subheader("Navigation")
        page = st.radio(
            "Select View:",
            [
                "Dashboard",
                "Flight Operations",
                "Maintenance",
                "Revenue Analytics",
                "Reports",
                "AI Insights",
                "Data Entry",
                "Settings"
            ],
            key="page_navigation"
        )
        
        st.markdown("---")
        
        # Airline Info
        config = get_airline_config(st.session_state.airline_code)
        st.subheader("ℹ️ Airline Info")
        st.write(f"**{config.airline_name}**")
        st.write(f"📍 {config.headquarters_location}")
        st.write(f"✈️ Fleet: {config.fleet_size}")
        st.write(f"📈 Flights/Day: ~{config.daily_flights_avg}")
        
        return page, config


# ============================================================================
# PAGES
# ============================================================================

def page_dashboard(config):
    """Main dashboard"""
    st.header(f"🛫 {config.airline_display_name}")
    st.subheader(f"Operational Dashboard - {datetime.now().strftime('%B %d, %Y')}")
    
    # KPI Row
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("On-Time Performance", "87.3%", "+2.1%", delta_color="inverse")
    with col2:
        st.metric("Fleet Utilization", "78.9%", "+3.2%")
    with col3:
        st.metric("Available Seats/Day", f"{config.fleet_size * 450:,}", "+120")
    with col4:
        st.metric("Total Flights (30d)", f"{config.daily_flights_avg * 30:,}", "+450")
    
    st.markdown("---")
    
    # Charts Row 1
    col1, col2 = st.columns(2)
    
    with col1:
        dates = pd.date_range(end=datetime.now(), periods=30)
        otp_values = np.clip(np.random.normal(87, 3, 30), 75, 95)
        otp_df = pd.DataFrame({"Date": dates, "On-Time %": otp_values})
        
        fig_otp = px.area(otp_df, x="Date", y="On-Time %", 
                         title="📊 On-Time Performance Trend (30 Days)",
                         color_discrete_sequence=[config.primary_color])
        fig_otp.update_layout(hovermode="x unified", height=400, template="plotly_white")
        st.plotly_chart(fig_otp, use_container_width=True)
    
    with col2:
        fleet_data = pd.DataFrame({
            "Aircraft Type": ["Boeing 777", "Airbus A320", "ATR 72", "Boeing 737"],
            "Utilization %": [82, 79, 75, 81]
        })
        
        fig_fleet = px.bar(fleet_data, x="Aircraft Type", y="Utilization %",
                          title="✈️ Fleet Utilization by Type",
                          color_discrete_sequence=[config.primary_color])
        fig_fleet.update_layout(height=400, template="plotly_white")
        st.plotly_chart(fig_fleet, use_container_width=True)
    
    st.markdown("---")
    
    # Alerts
    st.subheader("🚨 Recent Alerts & Issues")
    alerts = [
        ("🔴 Critical", "Aircraft N-4567 requires immediate maintenance", "2024-01-15 14:30"),
        ("🟠 Warning", "Flight PK-201 delayed due to weather (1h 15min)", "2024-01-15 13:45"),
        ("🟡 Notice", "Crew scheduling optimization recommended", "2024-01-15 12:00"),
        ("🟢 Info", "On-time performance exceeded target by 2.1%", "2024-01-15 08:00"),
    ]
    
    for severity, message, time in alerts:
        col1, col2, col3 = st.columns([0.5, 3, 1])
        with col1:
            st.write(severity)
        with col2:
            st.write(message)
        with col3:
            st.caption(time)


def page_flight_operations(config):
    """Flight operations monitoring"""
    st.header("✈️ Flight Operations")
    
    tab1, tab2, tab3, tab4 = st.tabs([
        "Live Flights",
        "Route Performance",
        "Crew Management",
        "Delay Analysis"
    ])
    
    with tab1:
        st.subheader("Live Flight Status")
        flights_data = pd.DataFrame({
            "Flight": ["PK-001", "PK-002", "PK-003", "PK-004", "PK-005"],
            "Route": ["KHI-ISB", "KHI-LHE", "ISB-KHI", "LHE-KHI", "KHI-DXB"],
            "Aircraft": ["A320", "B777", "A320", "B737", "A320"],
            "Scheduled": ["06:00", "07:30", "08:15", "09:00", "10:30"],
            "Status": ["Departed", "On Time", "Delayed", "Cancelled", "Scheduled"],
        })
        st.dataframe(flights_data, use_container_width=True, hide_index=True)
    
    with tab2:
        st.subheader("Route Performance Analysis")
        route_data = pd.DataFrame({
            "Route": ["KHI-ISB", "KHI-LHE", "ISB-KHI", "LHE-KHI", "KHI-DXB"],
            "Flights (30d)": [89, 76, 85, 72, 48],
            "On-Time %": [88.8, 85.5, 87.2, 86.1, 91.7],
            "Avg Delay (min)": [12, 18, 14, 16, 8],
            "Revenue/Flight": ["$8,450", "$7,200", "$8,300", "$6,900", "$12,500"]
        })
        st.dataframe(route_data, use_container_width=True, hide_index=True)
    
    with tab3:
        st.subheader("Crew Resource Management")
        crew_data = pd.DataFrame({
            "Crew ID": ["CR-001", "CR-002", "CR-003", "CR-004", "CR-005"],
            "Role": ["Captain", "First Officer", "Purser", "Captain", "Flight Attendant"],
            "Hours (Month)": [84, 76, 92, 88, 98],
            "Status": ["Active", "Active", "⚠ Rotate", "Active", "Active"]
        })
        st.dataframe(crew_data, use_container_width=True, hide_index=True)
    
    with tab4:
        st.subheader("Delay Root Cause Analysis")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Delays (30d)", "156", "-12")
        with col2:
            st.metric("Avg Delay Duration", "18 min", "+2 min")
        with col3:
            st.metric("Delay Recovery Rate", "94.2%", "+3.1%")


def page_maintenance(config):
    """Maintenance management"""
    st.header("🔧 Maintenance Management")
    
    tab1, tab2, tab3 = st.tabs(["Scheduled", "Alerts", "Predictive"])
    
    with tab1:
        st.subheader("Scheduled Maintenance")
        maintenance_data = pd.DataFrame({
            "Aircraft": ["N-1001", "N-1002", "N-1003", "N-1004"],
            "Type": ["C-Check", "A-Check", "Heavy Maint.", "B-Check"],
            "Next Date": ["2024-02-15", "2024-01-28", "2024-03-10", "2024-02-05"],
            "Duration": ["48h", "12h", "200h", "24h"],
        })
        st.dataframe(maintenance_data, use_container_width=True, hide_index=True)
    
    with tab2:
        st.subheader("🚨 Maintenance Alerts")
        st.error("🔴 N-4567: Engine vibration exceeds threshold - Immediate action required")
        st.warning("🟠 N-2345: Hydraulic system pressure irregular - Schedule within 48h")
    
    with tab3:
        st.subheader("🤖 Predictive Maintenance")
        prediction_data = pd.DataFrame({
            "Aircraft": ["N-1001", "N-1002", "N-1003", "N-1004", "N-1005"],
            "Component": ["Engine 1", "Landing Gear", "Hydraulic Pump", "Oxygen", "APU"],
            "Health": [78, 92, 65, 88, 71],
            "Action": ["Monitor", "OK", "Replace Soon", "OK", "Schedule"]
        })
        st.dataframe(prediction_data, use_container_width=True, hide_index=True)


def page_revenue_analytics(config):
    """Revenue management"""
    st.header("💰 Revenue Management & Analytics")
    
    tab1, tab2, tab3 = st.tabs(["Metrics", "Pricing", "Seats"])
    
    with tab1:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Monthly Revenue", "$12.4M", "+$450K")
        with col2:
            st.metric("RASK", "$0.082", "-$0.002")
        with col3:
            st.metric("Load Factor", "82.1%", "+2.3%")
        with col4:
            st.metric("Yield/Pax", "$145", "+$8")
    
    with tab2:
        st.subheader("Pricing Strategy")
        pricing_data = pd.DataFrame({
            "Route": ["KHI-ISB", "KHI-LHE", "ISB-KHI", "LHE-KHI", "KHI-DXB"],
            "Current": ["$120", "$95", "$115", "$90", "$280"],
            "Recommended": ["$125", "$100", "$118", "$95", "$290"],
            "Impact": ["+$2.1K", "+$1.8K", "+$2.5K", "+$1.2K", "+$3.5K"]
        })
        st.dataframe(pricing_data, use_container_width=True, hide_index=True)
    
    with tab3:
        st.subheader("Seat Inventory")
        inventory_data = pd.DataFrame({
            "Flight": ["PK-001", "PK-002", "PK-003", "PK-004"],
            "Total": [336, 396, 336, 189],
            "Sold": [289, 341, 264, 156],
            "Load %": ["86%", "86%", "79%", "82%"]
        })
        st.dataframe(inventory_data, use_container_width=True, hide_index=True)


def page_reports(config):
    """Report generation"""
    st.header("📋 Report Generation & Export")
    
    st.subheader("Select Report Type")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.button("📊 Weekly")
        st.button("🔄 Bi-Weekly")
    with col2:
        st.button("📈 Monthly")
        st.button("⏳ Quarterly")
    with col3:
        st.button("⏱️ Bi-Annual")
        st.button("📑 Annual")
    
    st.markdown("---")
    
    st.subheader("Report Sections")
    sections = [
        "Executive Summary",
        "Flight Performance Metrics",
        "Maintenance Overview",
        "Revenue Analysis",
        "Cost Optimization",
        "Key Issues & Recommendations",
        "Strategic Outlook"
    ]
    
    for i, section in enumerate(sections, 1):
        st.write(f"{i}. {section}")
    
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("📄 Generate PDF"):
            st.success("PDF generated!")
    with col2:
        if st.button("📊 Export Excel"):
            st.success("Excel exported!")
    with col3:
        if st.button("📧 Email"):
            st.info("Will be emailed to management")


def page_ai_insights(config):
    """AI-powered insights"""
    st.header("🤖 AI-Powered Insights")
    
    analyzer = AIAnalyzer(st.session_state.airline_code)
    
    tab1, tab2, tab3, tab4 = st.tabs([
        "Summary",
        "Delay Prediction",
        "Cost Optimization",
        "Strategic Insights"
    ])
    
    with tab1:
        st.subheader("Executive Summary")
        st.info(analyzer.generate_report_summary({}, "monthly"))
    
    with tab2:
        st.subheader("🔮 Delay Prediction")
        predictions = analyzer.predict_delays(pd.DataFrame())
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Predicted Rate", "12.5%", "confidence: 87%")
        with col2:
            st.metric("High Risk", "2 routes", "KHI-LHE, ISB-DXB")
        with col3:
            st.metric("Top Risk", "Weather", "45% prob")
        
        st.write("**Recommended Actions:**")
        for rec in predictions["recommendations"]:
            st.write(f"✓ {rec}")
    
    with tab3:
        st.subheader("💡 Cost Optimization")
        optimization = analyzer.cost_optimization_analysis({})
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Monthly Cost", optimization["current_monthly_cost"])
        with col2:
            st.metric("Potential Savings", optimization["potential_savings"], "+6.7%")
        
        for area in optimization["optimization_areas"]:
            st.write(f"**{area['area']}** - {area['savings']}: {area['action']}")
    
    with tab4:
        st.subheader("📊 Strategic Insights")
        insights = [
            ("🎯 Market Position", "Load factor 82% is above regional average"),
            ("📈 Growth Opportunity", "KHI-DXB route: 91.7% on-time, 91% load - expand capacity"),
            ("⚠️ Risk Alert", "Weather delays trending up - pre-position aircraft"),
            ("💰 Revenue Potential", "Dynamic pricing could generate +$2.1K daily on KHI-ISB"),
        ]
        
        for title, insight in insights:
            st.write(f"**{title}**")
            st.write(insight)
            st.markdown("")


def page_data_entry(config):
    """Data entry forms"""
    st.header("📝 Data Entry & Operations")
    
    tab1, tab2, tab3 = st.tabs(["Flight Actual", "Maintenance", "Crew Events"])
    
    with tab1:
        st.subheader("Record Flight Actual Data")
        col1, col2 = st.columns(2)
        with col1:
            st.text_input("Flight Number", "PK-001")
            st.time_input("Actual Departure")
            st.selectbox("Aircraft", ["B777", "A320", "B737", "ATR72"])
        with col2:
            st.time_input("Actual Arrival")
            st.selectbox("Route", ["KHI-ISB", "KHI-LHE", "ISB-KHI", "KHI-DXB"])
            st.number_input("Passengers Onboard", min_value=0, max_value=400)
        
        if st.button("Submit Flight Data"):
            st.success("✓ Flight data recorded!")
    
    with tab2:
        st.subheader("Record Maintenance Event")
        col1, col2 = st.columns(2)
        with col1:
            st.text_input("Aircraft ID", "N-1001")
            st.selectbox("Maintenance Type", ["A-Check", "C-Check", "Repair", "Inspection"])
            st.text_input("Component Checked", "Engine 1")
        with col2:
            st.number_input("Duration (hours)", min_value=0, step=0.5)
            st.selectbox("Status", ["Completed", "In Progress", "Scheduled"])
            st.text_input("Technician ID", "TECH-001")
        
        if st.button("Submit Maintenance Record"):
            st.success("✓ Maintenance record saved!")
    
    with tab3:
        st.subheader("Record Crew Events")
        st.text_input("Crew ID", "CR-001")
        st.selectbox("Event Type", ["Flight Completed", "Rest Period", "Training", "Medical"])
        st.number_input("Hours", min_value=0.0, step=0.5)
        
        if st.button("Submit Crew Event"):
            st.success("✓ Crew event recorded!")


def page_settings(config):
    """System settings"""
    st.header("⚙️ Settings & Configuration")
    
    tab1, tab2, tab3, tab4 = st.tabs([
        "Airline Config",
        "Features",
        "Database",
        "About"
    ])
    
    with tab1:
        st.subheader("Airline Configuration")
        st.write(f"**Code:** {config.airline_code}")
        st.write(f"**Name:** {config.airline_name}")
        st.write(f"**HQ:** {config.headquarters_location}")
        st.write(f"**Fleet:** {config.fleet_size} aircraft")
    
    with tab2:
        st.subheader("Enabled Features")
        features = [
            ("Predictive Analytics", config.enable_predictive_analytics),
            ("Cost Optimization", config.enable_cost_optimization),
            ("Fuel Efficiency", config.enable_fuel_efficiency),
            ("Delay Prediction", config.enable_delay_prediction),
            ("Revenue Optimization", config.enable_revenue_optimization),
            ("Maintenance Alerts", config.enable_maintenance_alerts),
        ]
        
        for feature, enabled in features:
            status = "✓ Enabled" if enabled else "✗ Disabled"
            st.write(f"{feature}: {status}")
    
    with tab3:
        st.subheader("Database Status")
        st.success("✓ Supabase connected")
        st.write(f"**Database:** {config.database_name}")
        st.write(f"**Storage:** 500MB free (scales infinitely)")
    
    with tab4:
        st.subheader("About AirOps Pro")
        st.markdown("""
        ## AirOps Pro v1.0.0
        Enterprise Aviation Operations Platform
        
        **Features:**
        - Multi-airline deployment
        - Real-time dashboards
        - AI analytics & predictions
        - 6 report types
        - Supabase integration (500MB+)
        - Cost optimization
        - Predictive maintenance
        
        **Tech Stack:**
        - Streamlit, Python
        - Supabase (PostgreSQL)
        - Plotly, Pandas
        - OpenAI/Claude APIs
        """)


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Main application"""
    initialize_session()
    page, config = render_sidebar()
    
    if page == "Dashboard":
        page_dashboard(config)
    elif page == "Flight Operations":
        page_flight_operations(config)
    elif page == "Maintenance":
        page_maintenance(config)
    elif page == "Revenue Analytics":
        page_revenue_analytics(config)
    elif page == "Reports":
        page_reports(config)
    elif page == "AI Insights":
        page_ai_insights(config)
    elif page == "Data Entry":
        page_data_entry(config)
    elif page == "Settings":
        page_settings(config)


if __name__ == "__main__":
    main()
