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
                self.model = genai.GenerativeModel('gemini-1.5-flash')
                self.active_model_name = 'gemini-1.5-flash'
            else:
                self.model = None
        except Exception as e:
            print(f"AI Init Error: {e}")
            self.model = None

    def _generate(self, prompt, parts=None):
        """ robust generation with auto-fallback to available models """
        if not self.model:
            return None, "⚠️ AI System is offline (API Key missing)."
            
        # List of models to try in order of preference
        fallback_models = ['gemini-1.5-flash', 'gemini-1.5-flash-latest', 'gemini-1.0-pro', 'gemini-pro']
        
        def attempt_gen(model_obj):
            if parts:
                return model_obj.generate_content(parts)
            return model_obj.generate_content(prompt)

        # 1. Try with current model
        try:
            return attempt_gen(self.model), None
        except Exception as e:
            # 2. If 404 (Not Found) or 400 (Bad Request), try cycling models
            error_str = str(e).lower()
            if "404" in error_str or "not found" in error_str or "400" in error_str:
                for model_name in fallback_models:
                    if model_name == self.active_model_name: continue
                    try:
                        # Switch model and retry
                        print(f"Switching AI model to: {model_name}")
                        new_model = genai.GenerativeModel(model_name)
                        result = attempt_gen(new_model)
                        
                        # If successful, save this as the new default
                        self.model = new_model
                        self.active_model_name = model_name
                        return result, None
                    except:
                        continue
            
            # If all attempts fail
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
    def geocode_location(loc):
        return None, None
