# ai_assistant.py
import google.generativeai as genai
import streamlit as st
import json
import io
from datetime import datetime

# Configure AI (Safe Fallback)
def get_ai_assistant():
    return SafetyAIAssistant()

class SafetyAIAssistant:
    def __init__(self):
        # Try to get key from secrets, handle missing keys gracefully
        try:
            self.api_key = st.secrets.get("GEMINI_API_KEY") or st.secrets.get("AI_API_KEY")
            if self.api_key:
                genai.configure(api_key=self.api_key)
                # Use the new Flash model
                self.model = genai.GenerativeModel('gemini-1.5-flash')
                self.vision_model = genai.GenerativeModel('gemini-1.5-flash')
            else:
                self.model = None
        except Exception as e:
            print(f"AI Init Error: {e}")
            self.model = None

    def chat(self, user_query):
        """General Chatbot Logic"""
        if not self.model:
            return "⚠️ AI System is offline (API Key missing)."
        
        system_instruction = "You are an Aviation Safety Management System (SMS) Expert for Air Sial. Answer efficiently."
        try:
            response = self.model.generate_content(f"{system_instruction}\n\nUser: {user_query}")
            return response.text
        except Exception as e:
            return f"AI Error: {str(e)}"

    def analyze_risk_from_narrative(self, narrative, report_type="General"):
        """Analyzes text to determine Risk Level (ICAO 5x5)"""
        if not self.model:
            return {"likelihood": 3, "severity": "C", "risk_level": "Medium", "summary": "AI Offline"}

        prompt = f"""
        Act as a Safety Officer. Analyze this aviation safety narrative ({report_type}).
        Determine the Likelihood (1-5) and Severity (A-E) based on ICAO Annex 19.
        
        Narrative: "{narrative}"
        
        Return ONLY a JSON string like this:
        {{"likelihood": 3, "severity": "C", "risk_level": "Medium", "justification": "..."}}
        """
        try:
            response = self.model.generate_content(prompt)
            # Clean up response to ensure valid JSON
            clean_text = response.text.replace("```json", "").replace("```", "").strip()
            return json.loads(clean_text)
        except:
            return {"likelihood": 3, "severity": "C", "risk_level": "Medium", "summary": "Analysis Failed"}

    def transcribe_audio_narrative(self, audio_bytes):
        """Converts Voice Recording to Text using Gemini"""
        if not self.model:
            return "AI Offline - Cannot transcribe."
        
        try:
            # Gemini 1.5 Flash can process audio directly
            prompt = "Transcribe this audio recording of a safety report exactly. Do not add commentary."
            response = self.model.generate_content([prompt, {"mime_type": "audio/wav", "data": audio_bytes}])
            return response.text
        except Exception as e:
            return f"Transcription Failed: {str(e)}"

    def generate_predictive_insights(self, reports_list):
        """Generates dashboard insights from DB data"""
        if not self.model or not reports_list:
            return {"alerts": [], "trends": ["Insufficient Data"]}
            
        # Summarize data for AI (don't send huge payload)
        summary = str(reports_list[:20]) # Limit to last 20 reports
        
        prompt = f"""
        Analyze these recent safety reports and identify 3 key trends and 1 predictive alert.
        Return JSON: {{ "trends": ["trend1", "trend2"], "alerts": [{{ "title": "...", "confidence": 85, "recommendation": "..." }}] }}
        Data: {summary}
        """
        try:
            response = self.model.generate_content(prompt)
            clean_text = response.text.replace("```json", "").replace("```", "").strip()
            return json.loads(clean_text)
        except:
            return {"alerts": [], "trends": ["AI Analysis Error"]}

class DataGeocoder:
    @staticmethod
    def geocode_location(location_name):
        """Simple lookup for key airports to avoid API costs"""
        # You can expand this list or use geopy if needed
        locations = {
            "sialkot": (32.5353, 74.3636), "opsk": (32.5353, 74.3636),
            "karachi": (24.9060, 67.1600), "opkc": (24.9060, 67.1600),
            "lahore": (31.5216, 74.4036), "opla": (31.5216, 74.4036),
            "islamabad": (33.5490, 73.0169), "opis": (33.5490, 73.0169),
            "dubai": (25.2532, 55.3657), "omdb": (25.2532, 55.3657),
        }
        for key in locations:
            if key in location_name.lower():
                return locations[key]
        return None, None
