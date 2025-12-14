# ai_assistant.py
# Lightweight AI wrapper. Replace the ask() implementation with your preferred LLM provider.
import os
from typing import List, Dict, Any
from config_loader import AI_API_KEY

class AIClient:
    def analyze_email_thread_for_action(self, email_history: List[Dict]) -> Dict:
        """
        Analyzes a list of emails to determine the current status and action taken.
        """
        if not email_history:
            return {"date": "N/A", "concern": "No emails", "reply": "N/A", "action_taken": "None", "status": "No Data"}

        # Construct the conversation string
        conversation = ""
        for email in email_history:
            role = "Support Team" if email['direction'] == 'outbound' else "Stakeholder/Sender"
            conversation += f"[{email['timestamp']}] {role} ({email['sender']}): {email['body']}\n\n"

        prompt = f"""
        Analyze the following email thread regarding a safety report. 
        Extract the following information into a JSON object:
        1. "date": The date of the most recent interaction.
        2. "concern": A 1-sentence summary of the main issue being discussed.
        3. "reply": A 1-sentence summary of the latest response.
        4. "action_taken": What concrete action has been promised or taken?
        5. "status": Determine status (Open, In Progress, Resolved, Closed).

        Email Thread:
        {conversation}
        """
        
        # Call your AI model (Using the existing ask method or generate_content)
        # Adjust 'self.model.generate_content' if you are using the SafetyAI class from app.py
        try:
            # Assuming use of the SafetyAI style from app.py:
            response = self.model.generate_content(prompt)
            result_text = response.text
            
            # Clean up potential markdown code blocks from AI response
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0]
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0]
                
            return json.loads(result_text)
        except Exception as e:
            return {
                "date": datetime.now().strftime("%Y-%m-%d"), 
                "concern": "Error parsing thread", 
                "reply": "AI Error", 
                "action_taken": "Manual review required", 
                "status": "Unknown"
            }
