# ui_integration.py
import streamlit as st
from config_loader import LOGO_PATH, AIR_SIAL_BLUE

def apply_branding_css(path="branding.css"):
    try:
        with open(path) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except Exception:
        # If CSS not found, continue gracefully
        pass

def header_bar(logo_path=None):
    logo = logo_path or LOGO_PATH
    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:12px;">
      <img src="{logo}" class="logo"/>
      <div>
        <h2 style="margin:0;color:white">Air Sial Safety Management System</h2>
        <div style="color:rgba(255,255,255,0.85)">Professional Safety Reporting & Analysis</div>
      </div>
    </div>
    """, unsafe_allow_html=True)
