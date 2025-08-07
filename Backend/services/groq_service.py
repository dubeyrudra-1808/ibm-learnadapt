from groq import Groq
import json
from typing import Dict, List, Any

class GroqService:
    def __init__(self, api_key: str):
        self.client = Groq(api_key=api_key)

    async def create_problem_prompt(self, subject: str, topic: str, difficulty: str, q_type: str) -> str:
        prompt_instructions = {
            "MCQ": "- **Answer**: The single correct option key as a string (e.g., \"C\").",
            "MSQ": "- **Answer**: A JSON array of all correct option keys (e.g., [\"A\", \"C\"]).",
            "PREDICT_OUTPUT": "- **Answer**: The EXACT final output as a string."
        }
        chosen_instruction = prompt_instructions.get(q_type, prompt_instructions["MCQ"])
        prompt = f"""
        As a Computer Science exam expert, create one high-quality, {difficulty}-level {q_type} question about "{topic}" in "{subject}".

        STRUCTURE:
        - **Question**: A clear, unique, and challenging question. IMPORTANT: Preserve all formatting, including newlines, tables, and code blocks using markdown.
        - **Options**: A JSON object of four distinct choices (A, B, C, D). For PREDICT_OUTPUT, use an empty object {{}}.
        {chosen_instruction}
        - **Explanation**: A detailed, step-by-step reasoning for the answer (min. 50 words).

        CRITICAL: Respond with ONLY a single, valid, minified JSON object. Verify all calculations and answers for 100% accuracy.
        """
        return prompt

    async def generate_student_report(self, student_responses: List[Dict]) -> Dict[str, Any]:
        correct_count = sum(1 for r in student_responses if r.get("is_correct", False))
        total_count = len(student_responses)
        score = (correct_count / total_count * 100) if total_count > 0 else 0

        prompt = f"""
        Analyze the student's quiz performance based on this data: {json.dumps(student_responses, indent=2)}

        Create a comprehensive report as a single JSON object with these exact keys: "overall_summary", "topic_analysis", "reasoning_quality", "action_plan".

        **ANALYSIS REQUIREMENTS:**
        - **overall_summary**: Must contain "total_score": {score:.1f}, "problems_correct": {correct_count}, "total_problems": {total_count}, and a "summary" (a single insightful string).
        - **topic_analysis**: Must contain "strengths" (list of 2-3 specific concepts the student did well on) and "weaknesses" (list of 2-3 specific concepts they struggled with).
        - **reasoning_quality**: A detailed assessment of the student's reasoning as a single string.
        - **action_plan**: A list of 3 specific, actionable steps for improvement as strings.
        """
        try:
            response = self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama3-8b-8192",
                temperature=0.5,
                max_tokens=2000,
                response_format={"type": "json_object"}
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"Error generating Groq report: {e}")
            return self._create_fallback_report(student_responses)

    def _create_fallback_report(self, responses: List[Dict]) -> Dict[str, Any]:
        if not responses: return {}
        correct = sum(1 for r in responses if r.get("is_correct"))
        total = len(responses)
        score = (correct / total * 100) if total > 0 else 0
        return {
            "overall_summary": {
                "total_score": round(score), "problems_correct": correct, "total_problems": total,
                "summary": "Performance analysis complete. Focus on reviewing incorrect answers."
            },
            "topic_analysis": {
                "strengths": ["Good attempt on the quiz."],
                "weaknesses": ["Reviewing explanations for incorrect answers is recommended."]
            },
            "reasoning_quality": "Provide reasoning for your answers next time to get a detailed analysis.",
            "action_plan": ["Review incorrect answers.", "Practice more problems on weak topics."]
        }