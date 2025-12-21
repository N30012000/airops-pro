# ai_assistant.py
import google.generativeai as genai
import streamlit as st
import json

def get_ai_assistant():
    return SafetyAIAssistant()

class SafetyAIAssistant:
    def __init__(self):
        try:
            # 1. Load API Key
            self.api_key = st.secrets.get("GEMINI_API_KEY") or st.secrets.get("AI_API_KEY")
            
            if self.api_key:
                genai.configure(api_key=self.api_key)
                
                # 2. FORCE 'gemini-pro'. This model is stable and works everywhere.
                self.model = genai.GenerativeModel('gemini-pro')
            else:
                self.model = None
                print("⚠️ No API Key found.")
        except Exception as e:
            print(f"AI Init Error: {e}")
            self.model = None

    def _generate(self, prompt):
        """Simple, text-only generation."""
        if not self.model:
            return "⚠️ AI Offline (Check API Key)"
        
        try:
            # gemini-pro does NOT support 'parts' parameter for images/audio well in this context
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"AI Error: {str(e)}"

    def chat(self, user_query):
        return self._generate(f"You are an Aviation Safety Expert. Answer briefly.\n\nUser: {user_query}")

    def analyze_risk_from_narrative(self, narrative, report_type="General"):
        prompt = f"""
        Act as a Safety Officer. Analyze this aviation safety narrative ({report_type}).
        Determine the Likelihood (1-5) and Severity (A-E) based on ICAO Annex 19.
        Narrative: "{narrative}"
        Return ONLY a JSON string: {{"likelihood": 3, "severity": "C", "risk_level": "Medium", "justification": "..."}}
        """
        response_text = self._generate(prompt)
        
        if "AI Error" in response_text or "Offline" in response_text:
             return {"likelihood": 3, "severity": "C", "risk_level": "Medium", "summary": "AI Offline"}

        try:
            # Clean JSON
            clean_text = response_text.replace("```json", "").replace("```", "").strip()
            return json.loads(clean_text)
        except:
            return {"likelihood": 3, "severity": "C", "risk_level": "Medium", "summary": "Parsing Error"}

    def transcribe_audio_narrative(self, audio_bytes):
        # 3. DISABLE AUDIO. gemini-pro cannot handle audio bytes.
        return "⚠️ Voice transcription is disabled in Stable Mode (gemini-pro)."

    def generate_predictive_insights(self, reports_list):
        if not reports_list: return {"alerts": [], "trends": ["Insufficient Data"]}
        
        summary = str(reports_list[:10]) 
        prompt = f"""
        Analyze these safety reports. Identify 3 trends and 1 predictive alert.
        Return JSON: {{ "trends": ["t1", "t2"], "alerts": [{{ "title": "...", "confidence": 85, "recommendation": "..." }}] }}
        Data: {summary}
        """
        response_text = self._generate(prompt)
        
        if "AI Error" in response_text: return {"alerts": [], "trends": ["AI Error"]}
        
        try:
            return json.loads(response_text.replace("```json", "").replace("```", "").strip())
        except:
            return {"alerts": [], "trends": ["Parsing Error"]}

class DataGeocoder:
    @staticmethod
    def geocode_location(location_name):
        return None, None
