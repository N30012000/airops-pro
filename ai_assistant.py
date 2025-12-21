"""
AI Assistant Module for Aviation Safety Management System
Handles all Google Gemini API interactions
"""

import google.generativeai as genai
from typing import Optional, Dict, List
import streamlit as st
import json
import re

class SafetyAIAssistant:
    """AI-powered safety analysis using Google Gemini"""
    
    def __init__(self, api_key: str):
        """Initialize the AI assistant with Gemini API key"""
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        self.safety_system_prompt = """You are an Expert Aviation Safety Officer with 20+ years of experience. 
Your role is to analyze safety reports, identify risks, provide recommendations, and generate insights.
Always be professional, factual, and safety-focused. Format responses clearly with headers and bullet points."""
    
    def analyze_risk_from_narrative(self, narrative: str, report_type: str) -> Dict:
        """
        Analyze a safety report narrative and extract risk level, factors, and recommendations.
        
        Returns:
        {
            'likelihood': int (1-5),
            'severity': str ('A'-'E'),
            'risk_level': str ('Extreme'|'High'|'Medium'|'Low'),
            'key_factors': [list of factors],
            'recommendations': [list of recommendations],
            'summary': str
        }
        """
        try:
            prompt = f"""Analyze this aviation safety report and assess the risk:

Report Type: {report_type}
Narrative: {narrative}

Provide a JSON response with:
{{
    "likelihood": <1-5 scale: 1=Extremely Improbable, 5=Frequent>,
    "severity": <A-E scale: A=Catastrophic, E=Negligible>,
    "risk_level": <Extreme|High|Medium|Low based on likelihood x severity matrix>,
    "key_factors": [list of contributing factors],
    "recommendations": [list of safety recommendations],
    "summary": "brief safety summary"
}}

Respond ONLY with valid JSON, no other text."""
            
            response = self.model.generate_content(prompt)
            result = json.loads(response.text)
            return result
            
        except Exception as e:
            st.error(f"AI Risk Analysis Error: {e}")
            return {
                'likelihood': 3,
                'severity': 'C',
                'risk_level': 'Medium',
                'key_factors': [],
                'recommendations': [],
                'summary': 'Error analyzing report'
            }
    
    def generate_predictive_insights(self, reports: List[Dict]) -> Dict:
        """
        Analyze historical reports to generate predictive safety insights.
        """
        if not reports:
            return {
                'alerts': [],
                'trends': [],
                'recommendations': []
            }
        
        try:
            # Prepare report summary for AI
            report_summary = f"Total Reports: {len(reports)}\n"
            
            # Count by type
            types = {}
            risk_counts = {'Extreme': 0, 'High': 0, 'Medium': 0, 'Low': 0}
            
            for r in reports:
                rtype = r.get('type', 'Unknown')
                types[rtype] = types.get(rtype, 0) + 1
                risk = r.get('risk_level', 'Low')
                if risk in risk_counts:
                    risk_counts[risk] += 1
            
            report_summary += f"High/Extreme Risk: {risk_counts['High'] + risk_counts['Extreme']}\n"
            report_summary += f"Report Types: {types}\n"
            
            prompt = f"""Based on this aviation safety data, generate predictive insights:

{report_summary}

Provide a JSON response with:
{{
    "alerts": [
        {{"title": "Alert Title", "timeframe": "timeframe", "confidence": <0-100>, "recommendation": "action"}}
    ],
    "trends": ["trend 1", "trend 2"],
    "recommendations": ["recommendation 1", "recommendation 2"]
}}

Be specific and actionable. Respond ONLY with valid JSON."""
            
            response = self.model.generate_content(prompt)
            result = json.loads(response.text)
            return result
            
        except Exception as e:
            st.error(f"Predictive Analysis Error: {e}")
            return {
                'alerts': [],
                'trends': ['No trends available'],
                'recommendations': ['Submit more reports for better insights']
            }
    
    def analyze_email_thread(self, emails: List[Dict]) -> Dict:
        """
        Analyze email thread for actions and responses.
        """
        if not emails:
            return {
                'actions_identified': [],
                'status': 'No communication',
                'next_steps': []
            }
        
        try:
            email_text = ""
            for email in emails:
                email_text += f"From: {email.get('sender', 'Unknown')}\n"
                email_text += f"Subject: {email.get('subject', '')}\n"
                email_text += f"Body: {email.get('body', '')}\n\n"
            
            prompt = f"""Analyze this email thread about a safety report. Extract actions and next steps:

{email_text}

Provide JSON:
{{
    "actions_identified": ["action 1", "action 2"],
    "status": "status summary",
    "next_steps": ["step 1", "step 2"],
    "concerns": ["concern 1"]
}}

Respond ONLY with valid JSON."""
            
            response = self.model.generate_content(prompt)
            result = json.loads(response.text)
            return result
            
        except Exception as e:
            return {
                'actions_identified': [],
                'status': 'Analysis error',
                'next_steps': []
            }
    
    def transcribe_audio_narrative(self, audio_bytes: bytes) -> str:
        """
        Transcribe audio using Gemini's multimodal capabilities.
        Falls back to SpeechRecognition if needed.
        """
        try:
            import speech_recognition as sr
            from io import BytesIO
            
            recognizer = sr.Recognizer()
            audio = sr.AudioData(audio_bytes, 16000, 2)
            
            try:
                # Try Google Speech Recognition (free)
                text = recognizer.recognize_google(audio)
                return text
            except sr.UnknownValueError:
                return "[Audio could not be transcribed - unclear speech]"
            except sr.RequestError:
                return "[Speech recognition service unavailable]"
                
        except ImportError:
            st.warning("SpeechRecognition library not installed. Install with: pip install SpeechRecognition pydub")
            return "[Audio transcription not available]"
        except Exception as e:
            return f"[Transcription error: {str(e)}]"
    
    def generate_report_summary(self, report: Dict) -> str:
        """
        Generate an AI-powered summary of a detailed report.
        """
        try:
            prompt = f"""Summarize this aviation safety report in 2-3 sentences:

Type: {report.get('type', 'Unknown')}
Date: {report.get('date', 'Unknown')}
Description: {report.get('description', '')}

Be concise and focus on key safety implications."""
            
            response = self.model.generate_content(prompt)
            return response.text
            
        except Exception as e:
            return f"Summary generation failed: {e}"
    
    def chat(self, user_message: str, chat_history: List[Dict] = None) -> str:
        """
        General purpose chat for the AI Assistant.
        """
        try:
            # Build conversation
            messages = []
            if chat_history:
                for msg in chat_history:
                    messages.append({
                        'role': msg['role'],
                        'parts': [msg['content']]
                    })
            
            messages.append({
                'role': 'user',
                'parts': [user_message]
            })
            
            response = self.model.generate_content(
                [msg['parts'][0] for msg in messages],
                stream=False
            )
            
            return response.text
            
        except Exception as e:
            return f"Error: {str(e)}"


class DataGeocoder:
    """Handle location geocoding for reports"""
    
    @staticmethod
    def geocode_location(location_name: str) -> tuple:
        """
        Convert location name to coordinates.
        
        Returns: (latitude, longitude) or (None, None)
        """
        try:
            from geopy.geocoders import Nominatim
            import time
            
            geolocator = Nominatim(user_agent="air_sial_sms")
            time.sleep(1)  # Rate limiting
            
            location = geolocator.geocode(location_name)
            if location:
                return (location.latitude, location.longitude)
            return (None, None)
            
        except ImportError:
            st.warning("geopy not installed. Install with: pip install geopy")
            return (None, None)
        except Exception as e:
            st.error(f"Geocoding error: {e}")
            return (None, None)


# Initialize at module level
def get_ai_assistant(api_key: Optional[str] = None) -> SafetyAIAssistant:
    """Factory function to get or create AI assistant"""
    if api_key is None:
        api_key = st.secrets.get("GEMINI_API_KEY") or st.secrets.get("AI_API_KEY")
    
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in secrets")
    
    return SafetyAIAssistant(api_key)
