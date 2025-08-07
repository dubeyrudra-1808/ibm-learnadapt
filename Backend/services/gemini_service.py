import google.generativeai as genai
import json
import re
from typing import Dict, Any

class GeminiService:
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')  # Updated model name

    async def generate_quiz_question(self, optimized_prompt: str) -> Dict[str, Any]:
        """Generate a structured quiz question"""
        try:
            # FIX: Use the correct async method
            response = await self.model.generate_content_async(optimized_prompt)
            return self.parse_json_response(response.text)
        except Exception as e:
            print(f"Error in Gemini service call: {e}")
            return self.create_fallback_question(str(e))

    def parse_json_response(self, content: str) -> Dict[str, Any]:
        """Parse JSON from AI response"""
        # Clean the content first
        content = content.strip()
        
        # Try to extract JSON object
        try:
            # First try to parse directly
            if content.startswith('{') and content.endswith('}'):
                return json.loads(content)
        except:
            pass
            
        # If direct parse fails, search for JSON object in text
        match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', content, re.DOTALL)
        
        if match:
            json_string = match.group(0)
            try:
                return json.loads(json_string)
            except json.JSONDecodeError as e:
                print(f"Failed to decode JSON: {e}")
                print(f"Attempted to parse: {json_string}")
                return self.create_fallback_question("Invalid JSON format")
        else:
            print(f"No JSON found in response: {content}")
            return self.create_fallback_question("No JSON in response")

    def create_fallback_question(self, error_message: str) -> Dict[str, Any]:
        """Create fallback question when generation fails"""
        return {
            "question": "What is the basic concept in computer science?",
            "options": {
                "A": "Data Structure",
                "B": "Algorithm", 
                "C": "Programming",
                "D": "All of the above"
            },
            "answer": "D",
            "explanation": f"Fallback question used due to error: {error_message}"
        }
