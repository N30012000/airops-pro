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
                
                # Try to use Flash, but allow fallback if not available
                self.model_name = 'gemini-1.5-flash-latest'
                self.model = genai.GenerativeModel(self.model_name)
            else:
                self.model = None
        except Exception as e:
            print(f"AI Init Error: {e}")
            self.model = None

    def _generate(self, prompt, parts=None):
        """Helper to handle generation with fallback"""
        if not self.model:
            return None, "⚠️ AI System is offline (API Key missing)."
            
        try:
            if parts:
                return self.model.generate_content(parts), None
            return self.model.generate_content(prompt), None
        except Exception as e:
            # Fallback for 404 or other model errors
            if "404" in str(e) or "not found" in str(e).lower():
                try:
                    # Fallback to Pro model
                    fallback_model = genai.GenerativeModel('gemini-pro')
                    if parts:
                        return fallback_model.generate_content(parts), None
                    return fallback_model.generate_content(prompt), None
                except Exception as e2:
                    return None, f"AI Error (Fallback failed): {str(e2)}"
            return None, f"AI Error: {str(e)}"

    def chat(self, user_query):
        """General Chatbot Logic"""
        system_instruction = "You are an Aviation Safety Management System (SMS) Expert for Air Sial. Answer efficiently."
        response, error = self._generate(f"{system_instruction}\n\nUser: {user_query}")
        
        if error:
            return error
        return response.text

    def analyze_risk_from_narrative(self, narrative, report_type="General"):
        """Analyzes text to determine Risk Level (ICAO 5x5)"""
        prompt = f"""
        Act as a Safety Officer. Analyze this aviation safety narrative ({report_type}).
        Determine the Likelihood (1-5) and Severity (A-E) based on ICAO Annex 19.
        
        Narrative: "{narrative}"
        
        Return ONLY a JSON string like this:
        {{"likelihood": 3, "severity": "C", "risk_level": "Medium", "justification": "..."}}
        """
        response, error = self._generate(prompt)
        
        if error or not response:
            return {"likelihood": 3, "severity": "C", "risk_level": "Medium", "summary": "Analysis Failed"}
            
        try:
            # Clean up response to ensure valid JSON
            clean_text = response.text.replace("```json", "").replace("```", "").strip()
            return json.loads(clean_text)
        except:
            return {"likelihood": 3, "severity": "C", "risk_level": "Medium", "summary": "AI Parsing Error"}

    def transcribe_audio_narrative(self, audio_bytes):
        """Converts Voice Recording to Text using Gemini"""
        prompt = "Transcribe this audio recording of a safety report exactly. Do not add commentary."
        # Note: Fallback model (gemini-pro) does NOT support audio, so this might fail if Flash is down
        response, error = self._generate(prompt, parts=[prompt, {"mime_type": "audio/wav", "data": audio_bytes}])
        
        if error:
            return f"Transcription Failed: {error}"
        return response.text

    def generate_predictive_insights(self, reports_list):
        """Generates dashboard insights from DB data"""
        if not reports_list:
            return {"alerts": [], "trends": ["Insufficient Data"]}
            
        # Summarize data for AI (don't send huge payload)
        summary = str(reports_list[:20]) # Limit to last 20 reports
        
        prompt = f"""
        Analyze these recent safety reports and identify 3 key trends and 1 predictive alert.
        Return JSON: {{ "trends": ["trend1", "trend2"], "alerts": [{{ "title": "...", "confidence": 85, "recommendation": "..." }}] }}
        Data: {summary}
        """
        response, error = self._generate(prompt)
        
        if error or not response:
            return {"alerts": [], "trends": ["AI Analysis Error"]}
            
        try:
            clean_text = response.text.replace("```json", "").replace("```", "").strip()
            return json.loads(clean_text)
        except:
            return {"alerts": [], "trends": ["AI Parsing Error"]}

class DataGeocoder:
    @staticmethod
    def geocode_location(location_name):
        """Simple lookup for key airports to avoid API costs"""
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
