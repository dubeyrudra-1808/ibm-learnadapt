import google.generativeai as genai
import json
import re
import hashlib
from typing import Dict, Any, Set

class GeminiService:
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        self.generated_questions: Set[str] = set()

    def generate_quiz_question(self, optimized_prompt: str, attempt: int = 1) -> Dict[str, Any]:
        try:
            enhanced_prompt = f"{optimized_prompt}\n\nATTEMPT #{attempt}: Ensure this is a unique, high-quality question."
            response = self.model.generate_content(enhanced_prompt)
            result = self.parse_json_response(response.text)
            
            question_hash = self._get_question_hash(result.get("question", ""))
            if question_hash in self.generated_questions and attempt < 3:
                print(f"Duplicate question detected. Regenerating (Attempt {attempt + 1})...")
                return self.generate_quiz_question(optimized_prompt, attempt + 1)
            
            self.generated_questions.add(question_hash)
            return result
        except Exception as e:
            print(f"Error in Gemini service call: {e}")
            return self.create_fallback_question(str(e))

    def _get_question_hash(self, question_text: str) -> str:
        """Creates a more robust hash to better detect similar questions."""
        # Lowercase, remove all non-alphanumeric characters
        normalized = re.sub(r'[^a-z0-9]', '', question_text.lower())
        # Use a significant portion of the string for the hash
        return hashlib.md5(normalized[:100].encode()).hexdigest()

    def parse_json_response(self, content: str) -> Dict[str, Any]:
        content = content.strip().replace('```json', '').replace('```', '')
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            match = re.search(r'\{.*\}', content, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(0))
                except json.JSONDecodeError:
                    pass
        return self.create_fallback_question("No valid JSON found in response")

    def create_fallback_question(self, error_message: str) -> Dict[str, Any]:
        return {
            "question": "Which data structure uses a First-In-First-Out (FIFO) approach?",
            "options": {"A": "Stack", "B": "Queue", "C": "Tree", "D": "Graph"},
            "answer": "B",
            "explanation": f"A Queue uses the FIFO principle. Fallback generated due to: {error_message}",
            "fallback": True
        }

    def reset_question_history(self):
        self.generated_questions.clear()