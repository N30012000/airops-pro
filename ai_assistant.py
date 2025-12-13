# ai_assistant.py
# Lightweight AI wrapper. Replace the ask() implementation with your preferred LLM provider.
import os
from typing import List, Dict, Any
from config_loader import AI_API_KEY

class AIClient:
    def __init__(self, api_key=None):
        self.api_key = api_key or AI_API_KEY

    def ask(self, prompt: str, max_tokens=512) -> Dict[str, Any]:
        """
        Placeholder implementation. Replace with actual API call to your LLM provider.
        Returns dict: {"success": True, "answer": "..."} or {"success": False, "error": "..."}
        """
        try:
            # TODO: Replace with real provider call (OpenAI, Google Gemini, etc.)
            simulated = f"[Simulated AI] Summary: {prompt[:300]}"
            return {"success": True, "answer": simulated}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def analyze_emails_for_actions(self, email_thread: List[Dict]) -> Dict:
        prompt = "You are an aviation safety assistant. Read the following email thread and propose the next action, priority, and status.\n\n"
        for e in email_thread:
            prompt += f"Direction: {e.get('direction')}\nSubject: {e.get('subject')}\nBody: {e.get('body')}\n\n"
        prompt += "\nReturn JSON with keys: action, priority (low/medium/high), status (open/in-progress/closed), rationale."
        res = self.ask(prompt)
        if res.get("success"):
            return {"action": "Investigate and assign to MO", "priority":"high", "status":"in-progress", "rationale": res["answer"]}
        return {"action":"unable_to_determine","priority":"low","status":"open","rationale":res.get("error","unknown")}

    def analyze_document(self, text: str) -> Dict:
        prompt = f"Analyze the following document for safety issues and produce a short summary and recommended actions:\n\n{text[:4000]}"
        return self.ask(prompt)
