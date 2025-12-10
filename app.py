"""
Air Sial SMS v3.0 - Test Version
Minimal version to diagnose freeze issue
"""

import streamlit as st

# Page config MUST be first Streamlit command
st.set_page_config(
    page_title="Air Sial SMS v3.0",
    page_icon="✈️",
    layout="wide"
)

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'username' not in st.session_state:
    st.session_state.username = None

def login():
    st.title("✈️ AIR SIAL")
    st.subheader("Safety Management System v3.0")
    st.divider()
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        if st.button("Sign In", type="primary", use_container_width=True):
            if username == "admin" and password == "admin123":
                st.session_state.authenticated = True
                st.session_state.username = username
                st.rerun()
            else:
                st.error("Invalid credentials. Try admin/admin123")
        
        st.divider()
        st.info("**Demo:** admin / admin123")

def dashboard():
    st.title("📊 Dashboard")
    st.success(f"Welcome, {st.session_state.username}!")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Reports", "0")
    with col2:
        st.metric("Open Cases", "0")
    with col3:
        st.metric("High Risk", "0")
    
    if st.button("Logout"):
        st.session_state.authenticated = False
        st.session_state.username = None
        st.rerun()

# Main
if st.session_state.authenticated:
    dashboard()
else:
    login()
