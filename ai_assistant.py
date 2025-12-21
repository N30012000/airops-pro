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
                # We don't hardcode the model here anymore.
                # We find the best available one in _get_model()
                self.model = None
                self.active_model_name = None
            else:
                self.model = None
        except Exception as e:
            print(f"AI Init Error: {e}")
            self.model = None

    def _get_model(self, require_audio=False):
        """
        Finds a working model. 
        If audio is required, it prioritizes 1.5 Flash/Pro.
        """
        # If we already have a working model and it supports what we need, return it
        if self.model:
            # If we need audio, make sure we aren't using legacy Pro (1.0)
            if require_audio and 'gemini-pro' in self.active_model_name and '1.5' not in self.active_model_name:
                pass # We need to switch to a 1.5 model
            else:
                return self.model

        # Priority list for Audio/Multimodal
        # We try specific versions (-001) first as they are more stable than aliases
        multimodal_candidates = [
            'gemini-1.5-flash-001', 
            'gemini-1.5-flash',
            'gemini-1.5-flash-latest',
            'gemini-1.5-pro-001',
            'gemini-1.5-pro'
        ]
        
        # Fallback for text-only
        text_candidates = ['gemini-pro']

        candidates = multimodal_candidates if require_audio else (multimodal_candidates + text_candidates)

        for name in candidates:
            try:
                # Attempt to initialize and ping the model
                model = genai.GenerativeModel(name)
                model.generate_content("Test")
                
                # If successful, save and return
                self.model = model
                self.active_model_name = name
                print(f"✅ Connected to AI Model: {name}")
                return model
            except Exception as e:
                # print(f"Failed to connect to {name}: {e}") # Debug only
                continue
        
        return None

    def _generate(self, prompt, parts=None):
        """Generates content, automatically finding a model that works."""
        # Check if this request needs audio/image support
        need_multimodal = parts is not None
        
        model = self._get_model(require_audio=need_multimodal)
        
        if not model:
            return None, "⚠️ AI Service Unavailable. No compatible model found for this request."

        try:
            if parts:
                return model.generate_content(parts), None
            return model.generate_content(prompt), None
        except Exception as e:
            # If it fails, try to re-acquire a model one last time
            self.model = None 
            model = self._get_model(require_audio=need_multimodal)
            if model:
                try:
                    if parts:
                        return model.generate_content(parts), None
                    return model.generate_content(prompt), None
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
        # We explicitly pass the audio parts here
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
