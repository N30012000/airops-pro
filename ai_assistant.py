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
                # We start with None to force the _generate method to find a working model
                self.model = None 
                self.active_model_name = None
            else:
                self.model = None
        except Exception as e:
            print(f"AI Init Error: {e}")
            self.model = None

    def _get_working_model(self):
        """Finds a model that works with your API key"""
        # List of models to try (Flash is faster, Pro is more compatible)
        candidates = ['gemini-1.5-flash', 'gemini-1.5-flash-latest', 'gemini-1.0-pro', 'gemini-pro']
        
        for model_name in candidates:
            try:
                model = genai.GenerativeModel(model_name)
                # Test the model with a simple prompt
                model.generate_content("Test")
                print(f"✅ AI Connected using: {model_name}")
                self.active_model_name = model_name
                return model
            except Exception:
                continue
        return None

    def _generate(self, prompt, parts=None):
        """Robust generation that finds a working model first"""
        if not self.api_key:
            return None, "⚠️ AI System is offline (API Key missing)."

        # If we don't have a working model yet, find one
        if not self.model:
            self.model = self._get_working_model()
            if not self.model:
                return None, "⚠️ AI Error: Could not connect to any Gemini model. Check API Key."

        try:
            if parts:
                return self.model.generate_content(parts), None
            return self.model.generate_content(prompt), None
        except Exception as e:
            # If the current model fails, try to find a new one
            self.model = self._get_working_model()
            if self.model:
                try:
                    if parts:
                        return self.model.generate_content(parts), None
                    return self.model.generate_content(prompt), None
                except Exception as e2:
                    return None, f"AI Error: {str(e2)}"
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
        prompt = "Transcribe this aviation safety report audio exactly."
        response, error = self._generate(prompt, parts=[prompt, {"mime_type": "audio/wav", "data": audio_bytes}])
        if error: return f"Transcription Failed: {error}"
        return response.text

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
