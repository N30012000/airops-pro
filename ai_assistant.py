# ai_assistant.py
import google.generativeai as genai
import streamlit as st
import json

def get_ai_assistant():
    return SafetyAIAssistant()

class SafetyAIAssistant:
    def __init__(self):
        self.model = None
        self.model_name = "Initializing..."
        
        try:
            self.api_key = st.secrets.get("GEMINI_API_KEY") or st.secrets.get("AI_API_KEY")
            if not self.api_key:
                print("⚠️ AI Init: No API Key found.")
                return

            genai.configure(api_key=self.api_key)
            
            # --- AUTO-DISCOVERY: ASK GOOGLE WHAT WE HAVE ---
            try:
                # List all models available to your specific API key
                all_models = list(genai.list_models())
                
                # Filter for models that can generate content
                valid_models = [m.name for m in all_models if 'generateContent' in m.supported_generation_methods]
                
                print(f"📋 Your Available Models: {valid_models}")
                
                # SELECTION STRATEGY:
                # 1. Look for 'gemini-1.5-flash' (Best for Audio)
                chosen = next((m for m in valid_models if 'gemini-1.5-flash' in m), None)
                
                # 2. If not, look for ANY '1.5' model (Supports Audio)
                if not chosen:
                    chosen = next((m for m in valid_models if '1.5' in m), None)
                    
                # 3. If not, look for 'gemini-pro' (Text Only)
                if not chosen:
                    chosen = next((m for m in valid_models if 'gemini-pro' in m), None)
                    
                # 4. Last resort: Pick the first valid model in the list
                if not chosen and valid_models:
                    chosen = valid_models[0]
                
                if chosen:
                    self.model = genai.GenerativeModel(chosen)
                    self.model_name = chosen
                    print(f"✅ AI Successfully Initialized using: {chosen}")
                else:
                    print("❌ No compatible Gemini models found for this API Key.")
                    self.model_name = "None Available"
                    
            except Exception as e:
                print(f"⚠️ Model Auto-Discovery Failed: {e}")
                # Blind Fallback
                self.model = genai.GenerativeModel('gemini-1.5-flash')
                self.model_name = 'gemini-1.5-flash (forced)'

        except Exception as e:
            print(f"AI Init Error: {e}")

    def _generate(self, prompt, parts=None):
        if not self.model:
            return None, f"⚠️ AI Offline. (Available models: {self.model_name})"
        
        try:
            if parts:
                return self.model.generate_content(parts), None
            return self.model.generate_content(prompt), None
        except Exception as e:
            return None, f"AI Error ({self.model_name}): {str(e)}"

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
        # Audio requires a 1.5 model. If we fell back to 1.0/Pro, we must warn the user.
        if '1.5' not in self.model_name and 'flash' not in self.model_name:
            return f"⚠️ Connected AI model ({self.model_name}) does not support audio. Please type the narrative."
            
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
