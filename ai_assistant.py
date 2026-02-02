"""
AI Assistant Module for Air Sial SMS v3.0
Integrates with Google Gemini API for safety analysis
"""

import streamlit as st
import google.generativeai as genai
from typing import Optional


class DataGeocoder:
    """Mock geocoder for incident location mapping"""
    
    @staticmethod
    def get_coordinates(location: str) -> tuple:
        """Get coordinates for a location (mock implementation)"""
        locations = {
            'Lahore': (31.5204, 74.3587),
            'Karachi': (24.8607, 67.0011),
            'Islamabad': (33.6844, 73.0479),
            'Peshawar': (34.0151, 71.5783),
            'Quetta': (30.1798, 66.9750),
        }
        return locations.get(location, (30.0, 70.0))


class SafetyAIAssistant:
    """AI Assistant for aviation safety analysis"""
    
    def __init__(self, api_key: str):
        """Initialize AI assistant with Gemini API"""
        self.api_key = api_key
        self.model_name = "gemini-pro"
        
        try:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel(self.model_name)
            self.initialized = True
        except Exception as e:
            print(f"⚠️ AI initialization warning: {e}")
            self.initialized = False
    
    def chat(self, message: str) -> str:
        """
        Send message to AI and get response
        
        Args:
            message: User question or prompt
        
        Returns:
            AI response text
        """
        if not self.initialized:
            return self._mock_response(message)
        
        try:
            response = self.model.generate_content(message)
            return response.text
        except Exception as e:
            print(f"⚠️ AI API error: {e}")
            return self._mock_response(message)
    
    def analyze_safety_report(self, report_text: str) -> dict:
        """
        Analyze a safety report and provide insights
        
        Args:
            report_text: Description of safety report
        
        Returns:
            dict with analysis results
        """
        prompt = f"""
        Analyze this aviation safety report and provide:
        1. Key risks identified
        2. Recommended actions
        3. Potential root causes
        
        Report: {report_text}
        
        Provide structured analysis.
        """
        
        try:
            response = self.chat(prompt)
            return {
                'analysis': response,
                'confidence': 85,
                'status': 'success'
            }
        except Exception as e:
            return {
                'analysis': f'Analysis unavailable: {str(e)}',
                'confidence': 0,
                'status': 'error'
            }
    
    def analyze_email_thread_for_action(self, emails: list) -> dict:
        """
        Analyze email thread to extract action items
        
        Args:
            emails: List of email dictionaries
        
        Returns:
            dict with extracted action items
        """
        if not emails:
            return {
                'date': 'N/A',
                'concern': 'No emails',
                'reply': 'N/A',
                'action_taken': 'N/A',
                'status': 'No data'
            }
        
        latest_email = emails[-1] if emails else {}
        
        return {
            'date': latest_email.get('timestamp', 'N/A'),
            'concern': latest_email.get('subject', 'N/A')[:50],
            'reply': latest_email.get('body', 'N/A')[:100],
            'action_taken': 'Pending review',
            'status': 'Open'
        }
    
    def _mock_response(self, message: str) -> str:
        """Fallback mock response when API unavailable"""
        
        message_lower = message.lower()
        
        if 'serious incident' in message_lower:
            return """
A "Serious Incident" according to ICAO Annex 13 is an accident which, by a narrow margin, 
was not an accident. It includes situations where safety was compromised but no collision or impact occurred.

Examples:
- Loss of separation below minimum standards
- System failures during critical flight phases
- Controlled Flight Into Terrain (CFIT) warnings
- Fuel emergencies
            """
        
        elif 'laser strike' in message_lower:
            return """
Laser Strike Reporting Procedure:
1. Immediately notify ATC with aircraft callsign and position
2. Describe laser color, intensity, and direction
3. Assess any crew effects (vision, disorientation)
4. Continue flight operations safely
5. File official report with CAA within 24 hours
6. Photograph evidence if safe to do so

Report to: CAA Laser Strike Hotline + Safety Department
            """
        
        elif 'difference' in message_lower and 'hazard' in message_lower:
            return """
Key Difference: Hazard vs Incident

HAZARD: Potential condition that could cause an accident
- Example: Bird nesting near airport
- Prevention focused
- Corrected before incident occurs

INCIDENT: Actual event that occurred
- Example: Bird strike during flight
- Investigation focused
- Analyzed after occurrence
            """
        
        elif 'reporting time' in message_lower or 'timeline' in message_lower:
            return """
Mandatory Reporting Timelines (Pakistan CAA):

- Accidents: IMMEDIATELY + within 72 hours (formal report)
- Serious Incidents: Within 24 hours
- Incidents: Within 7 days
- Hazards: Within 30 days

Delays may trigger escalation and fines.
            """
        
        elif 'fatigue' in message_lower:
            return """
Fatigue Risk Management (FRMS) Policy Summary:

Crew Duty Limits:
- Max 9 hours flight duty per day
- Max 50 hours per week
- Min 10 hours rest between duties
- Min 2 consecutive rest days per week

Risk Monitoring:
- Pre-flight fatigue assessment
- Duty hour tracking
- Rest period compliance
- Medication/sleep quality tracking

Violations trigger crew standdown and investigation.
            """
        
        elif 'tcas' in message_lower and 'ra' in message_lower:
            return """
TCAS RA (Resolution Advisory) Immediate Actions:

1. DISCONNECT AUTOPILOT (if not already done)
2. FOLLOW RA GUIDANCE IMMEDIATELY
3. DO NOT TURN IF RA IS LEVEL-OFF COMMAND
4. DO NOT CLIMB IF RA IS DESCENT/DESCEND COMMAND
5. CONFIRM RA AVOIDANCE MANEUVER IS BEING EXECUTED
6. INFORM ATC: "FOLLOWING TCAS RA"

After Maneuver:
- Resume normal flight when RA clears
- Notify ATC of maneuver execution
- Document in aircraft logbook
- File official report within 24 hours
            """
        
        else:
            return f"""
I can help with aviation safety queries. Try asking about:
- ICAO incident classifications
- Reporting procedures
- TCAS/ACAS operations
- Fatigue management
- Hazard vs Incident differences

Your question: "{message}"

This response is from mock AI. For live analysis, ensure Gemini API is configured.
            """


def get_ai_assistant() -> Optional[SafetyAIAssistant]:
    """
    Factory function to get or create AI assistant
    Uses Streamlit session state for caching
    """
    if 'ai_assistant_instance' not in st.session_state:
        try:
            api_key = st.secrets.get("GEMINI_API_KEY", "")
            if not api_key:
                print("⚠️ GEMINI_API_KEY not configured in secrets")
                st.session_state['ai_assistant_instance'] = SafetyAIAssistant("")
            else:
                st.session_state['ai_assistant_instance'] = SafetyAIAssistant(api_key)
        except Exception as e:
            print(f"⚠️ AI initialization error: {e}")
            st.session_state['ai_assistant_instance'] = SafetyAIAssistant("")
    
    return st.session_state['ai_assistant_instance']
