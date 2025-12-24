# ai_assistant.py
import google.generativeai as genai
import streamlit as st
import json
import speech_recognition as sr
import io

def get_ai_assistant():
    return SafetyAIAssistant()

class SafetyAIAssistant:
    def __init__(self):
        self.model = None
        self.model_name = "Initializing..."
        
        try:
            self.api_key = st.secrets.get("GEMINI_API_KEY") or st.secrets.get("AI_API_KEY")
            if not self.api_key:
                # print("⚠️ AI Init: No API Key found.")
                self.model_name = "No API Key"
                return

            genai.configure(api_key=self.api_key)
            
            # --- AUTO-DISCOVERY: ASK GOOGLE WHAT WE HAVE ---
            try:
                # List all models available to your specific API key
                all_models = list(genai.list_models())
                
                # Filter for models that can generate content
                valid_models = [m.name for m in all_models if 'generateContent' in m.supported_generation_methods]
                
                # SELECTION STRATEGY: Prioritize Flash/1.5 for speed and multimodal
                chosen = next((m for m in valid_models if 'gemini-1.5-flash' in m), None)
                if not chosen:
                    chosen = next((m for m in valid_models if '1.5' in m), None)
                if not chosen:
                    chosen = next((m for m in valid_models if 'gemini-pro' in m), None)
                
                if chosen:
                    self.model = genai.GenerativeModel(chosen)
                    self.model_name = chosen
                else:
                    self.model_name = "No Compatible Model"
                    
            except Exception as e:
                # Fallback to standard
                self.model = genai.GenerativeModel('gemini-1.5-flash')
                self.model_name = 'gemini-1.5-flash (forced)'

        except Exception as e:
            print(f"AI Init Error: {e}")

    def _generate(self, prompt, parts=None):
        if not self.model:
            return None, f"⚠️ AI Offline. (Status: {self.model_name})"
        
        try:
            if parts:
                return self.model.generate_content(parts), None
            return self.model.generate_content(prompt), None
        except Exception as e:
            return None, f"AI Error: {str(e)}"

    def chat(self, user_query):
        response, error = self._generate(f"You are an Aviation Safety Expert. Answer briefly.\n\nUser: {user_query}")
        if error: return error
        return response.text

    def analyze_risk_from_narrative(self, narrative, report_type="General"):
        if not narrative:
            return {"risk_level": "Unknown", "summary": "No narrative provided"}
            
        prompt = f"""
        Act as a Safety Officer. Analyze this aviation safety narrative ({report_type}).
        Determine the Likelihood (1-5) and Severity (A-E) based on ICAO Annex 19.
        Narrative: "{narrative}"
        Return ONLY a JSON string: {{"likelihood": 3, "severity": "C", "risk_level": "Medium", "justification": "..."}}
        """
        response, error = self._generate(prompt)
        if error or not response:
            return {"likelihood": 3, "severity": "C", "risk_level": "Medium", "summary": "AI Parsing Error"}
        try:
            clean_text = response.text.replace("```json", "").replace("```", "").strip()
            return json.loads(clean_text)
        except:
            return {"likelihood": 3, "severity": "C", "risk_level": "Medium", "summary": "AI Parsing Error"}

    def transcribe_audio_narrative(self, audio_bytes):
        """
        Robust transcription that tries AI first, then falls back to standard SpeechRecognition
        """
        # 1. Try Google Speech Recognition (Free, Non-LLM) first as it's often faster/more reliable for pure text
        try:
            r = sr.Recognizer()
            # Convert bytes to file-like object
            audio_file = io.BytesIO(audio_bytes)
            with sr.AudioFile(audio_file) as source:
                audio_data = r.record(source)
                # Use Google Web Speech API (default key included in library)
                text = r.recognize_google(audio_data)
                return f"{text} (via SpeechRecognition)"
        except Exception as e_sr:
            # print(f"SpeechRecognition failed: {e_sr}, trying Gemini...")
            pass

        # 2. Try Gemini AI (if key exists)
        if self.model:
            # Try as WAV first, then general audio
            prompt = "Transcribe this aviation safety report audio exactly."
            try:
                response, error = self._generate(prompt, parts=[prompt, {"mime_type": "audio/wav", "data": audio_bytes}])
                if not error: return response.text
                
                # If WAV failed, try generic or mp3 mime type (sometimes helps with webm containers)
                response, error = self._generate(prompt, parts=[prompt, {"mime_type": "audio/mp3", "data": audio_bytes}])
                if not error: return response.text
                
                return f"⚠️ Transcription failed: {error}"
            except Exception as e:
                return f"⚠️ AI Transcription error: {str(e)}"
        
        return "⚠️ Could not transcribe. Please type the narrative."

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

# --- RESTORED CLASS ---
class DataGeocoder:
    @staticmethod
    def geocode_location(location_name):
        return None, None
