# ai_assistant.py
import google.generativeai as genai
import streamlit as st
import json

def get_ai_assistant():
    return SafetyAIAssistant()

class SafetyAIAssistant:
    def __init__(self):
        try:
            self.api_key = st.secrets.get("GEMINI_API_KEY") or st.secrets.get("AI_API_KEY")
            if self.api_key:
                genai.configure(api_key=self.api_key)
                # SWITCHING TO GEMINI-PRO (STABLE) TO FIX 404 ERRORS
                self.model = genai.GenerativeModel('gemini-pro')
            else:
                self.model = None
        except Exception as e:
            print(f"AI Init Error: {e}")
            self.model = None

    def _generate(self, prompt, parts=None):
        """Simple generation with error handling"""
        if not self.model:
            return None, "⚠️ AI System is offline (API Key missing)."
            
        try:
            # gemini-pro handles text-only prompts best
            if parts:
                # If parts contains images/audio, we try our best or fail gracefully
                try:
                    return self.model.generate_content(parts), None
                except:
                    return None, "⚠️ This AI model cannot process images/audio."
            
            return self.model.generate_content(prompt), None
        except Exception as e:
            return None, f"AI Error: {str(e)}"

    def chat(self, user_query):
        response, error = self._generate(f"You are an Aviation Safety Expert. Answer briefly.\n\nUser: {user_query}")
        if error: return error
        return response.text

    def analyze_risk_from_narrative(self, narrative, report_type="General"):
        prompt = f"""
        Act as a Safety Officer. Analyze this aviation safety narrative ({report_type}).
        Determine the Likelihood (1-5) and Severity (A-E) based on ICAO Annex 19.
        Narrative: "{narrative}"
        Return ONLY a JSON string: {{"likelihood": 3, "severity": "C", "risk_level": "Medium", "justification": "..."}}
        """
        response, error = self._generate(prompt)
        if error or not response:
            return {"likelihood": 3, "severity": "C", "risk_level": "Medium", "summary": "Analysis Failed"}
        try:
            clean_text = response.text.replace("```json", "").replace("```", "").strip()
            return json.loads(clean_text)
        except:
            return {"likelihood": 3, "severity": "C", "risk_level": "Medium", "summary": "AI Parsing Error"}

    def transcribe_audio_narrative(self, audio_bytes):
        # gemini-pro cannot do audio, so we return a placeholder to prevent crashes
        return "⚠️ Audio transcription requires gemini-1.5-flash (currently unavailable). Please type the narrative."

    def generate_predictive_insights(self, reports_list):
        if not reports_list: return {"alerts": [], "trends": ["Insufficient Data"]}
        summary = str(reports_list[:15]) 
        prompt = f"""
        Analyze these safety reports. Identify 3 trends and 1 predictive alert.
        Return JSON: {{ "trends": ["t1", "t2"], "alerts": [{{ "title": "...", "confidence": 85, "recommendation": "..." }}] }}
        Data: {summary}
        """
        response, error = self._generate(prompt)
        if error: return {"alerts": [], "trends": ["AI Error"]}
        try:
            return json.loads(response.text.replace("```json", "").replace("```", "").strip())
        except:
            return {"alerts": [], "trends": ["Parsing Error"]}

class DataGeocoder:
    @staticmethod
    def geocode_location(location_name):
        return None, None
