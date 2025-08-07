from groq import Groq
import json
from typing import Dict, List, Any

class GroqService:
    def __init__(self, api_key: str):
        self.client = Groq(api_key=api_key)

    async def create_problem_prompt(self, subject: str, topic: str, difficulty: str, q_type: str) -> str:
        
        prompt_instructions = {
            "MCQ": """
1.  **Question**: A clear, challenging multiple-choice question.
2.  **Options**: A JSON object with four keys: "A", "B", "C", "D".
3.  **Answer**: A string indicating the correct option key (e.g., "C").
4.  **Explanation**: A detailed explanation of why the correct answer is right and why the others are wrong.
            """,
            "MSQ": """
1.  **Question**: A clear, challenging multiple-select question where one or more options can be correct.
2.  **Options**: A JSON object with four keys: "A", "B", "C", "D".
3.  **Answer**: A JSON array of strings indicating all correct option keys (e.g., ["A", "D"]).
4.  **Explanation**: A detailed explanation for each option, stating why it is correct or incorrect.
            """,
            "PREDICT_OUTPUT": """
1.  **Question**: A block of pseudocode or simple code with a specific input. The user's task is to predict the final output.
2.  **Answer**: The exact, final output of the code as a string.
3.  **Explanation**: A step-by-step trace of how the code executes to arrive at the final answer.
            """
        }

        chosen_instruction = prompt_instructions.get(q_type, prompt_instructions["MCQ"])

        prompt = f"""
        You are an expert Computer Science test creator, specializing in questions similar to the JEE Mains exam.
        Your task is to generate a single, high-quality problem based on the following specifications.

        - **Subject**: {subject}
        - **Topic**: {topic}
        - **Difficulty**: {difficulty}
        - **Question Type**: {q_type}

        Please provide the output as a single, minified JSON object with NO markdown formatting. The JSON object must contain these exact keys: "question", "options", "answer", "explanation". For PREDICT_OUTPUT questions, the "options" key should contain an empty JSON object.

        Use the following structure for your response based on the question type:

        {chosen_instruction}

        Ensure the entire output is a single, valid JSON object.
        """
        return prompt

    async def generate_student_report(self, student_responses: List[Dict]) -> Dict[str, Any]:
        
        prompt = f"""
        Analyze the following student quiz performance data. For each question, the student provided an answer and their reasoning.

        Student Quiz Data:
        {json.dumps(student_responses, indent=2)}

        Create a comprehensive report in a single JSON object. The report must have these exact keys: "overall_summary", "topic_analysis", "reasoning_quality", "action_plan".
        
        - "overall_summary": Provide total score, number correct, and a one-sentence summary of performance.
        - "topic_analysis": For each topic covered, identify strengths (where reasoning and answers were good) and weaknesses (where they were poor).
        - "reasoning_quality": Provide a general assessment of the student's ability to explain their answers. Note if their reasoning is logical even when the answer is wrong, or if it's weak even when the answer is right.
        - "action_plan": Suggest 3 specific, actionable steps the student should take to improve, based directly on their weaknesses.
        """
        try:
            response = self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="mixtral-8x7b-32768",
                temperature=0.6,
                max_tokens=2000,
                response_format={"type": "json_object"}
            )
            content = response.choices[0].message.content.strip()
            return json.loads(content)
        except Exception as e:
            return self._create_fallback_report(student_responses)

    def _create_fallback_report(self, responses: List[Dict]) -> Dict[str, Any]:
        if not responses: return {}
        correct_count = sum(1 for r in responses if r.get("is_correct"))
        total_count = len(responses)
        avg_score = (correct_count / total_count) * 100 if total_count > 0 else 0
        
        return {
            "overall_summary": {
                "total_score": round(avg_score, 1),
                "problems_correct": correct_count,
                "total_problems": total_count,
                "summary": "The student shows a foundational understanding but needs to work on accuracy and detailed reasoning."
            },
            "topic_analysis": {
                "strengths": ["Good attempt on foundational topics."],
                "weaknesses": ["Struggled with multi-step problems and edge cases."]
            },
            "reasoning_quality": "Reasoning is often brief. It's important to explain the 'why' behind each step.",
            "action_plan": [
                "Review the fundamentals of weaker topics.",
                "Practice writing out the step-by-step reasoning for every problem, even simple ones.",
                "Focus on identifying edge cases in problems."
            ]
        }