import re
from typing import Dict, Any, List
from difflib import SequenceMatcher

class ResponseEvaluator:
    def __init__(self):
        pass

    async def evaluate_response(self, user_answer: str, ai_solution: str, question: str, subject: str) -> Dict[str, Any]:
        user_clean = self._clean_text(user_answer)
        solution_clean = self._clean_text(ai_solution)
        
        similarity_score = self._calculate_similarity(user_clean, solution_clean)
        keyword_score = self._calculate_keyword_match(user_clean, solution_clean, subject)
        completeness_score = self._calculate_completeness(user_clean, question)
        structure_score = self._calculate_structure_quality(user_answer)
        
        final_score = (
            similarity_score * 0.3 +
            keyword_score * 0.4 +
            completeness_score * 0.2 +
            structure_score * 0.1
        )
        final_score = min(100, final_score)

        return {
            "score": round(final_score, 1),
            "percentage": round(final_score, 1),
            "breakdown": {
                "similarity": round(similarity_score, 1),
                "keywords": round(keyword_score, 1),
                "completeness": round(completeness_score, 1),
                "structure": round(structure_score, 1)
            },
            "feedback": self._generate_feedback(final_score),
            "strengths": self._identify_strengths(user_answer, final_score),
            "weaknesses": self._identify_weaknesses(user_answer, final_score, subject),
            "suggestions": self._generate_suggestions(final_score, subject)
        }

    def _clean_text(self, text: str) -> str:
        text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
        text = re.sub(r'[^\w\s]', '', text)
        text = re.sub(r'\s+', ' ', text)
        return text.lower().strip()

    def _calculate_similarity(self, user_text: str, solution_text: str) -> float:
        return SequenceMatcher(None, user_text, solution_text).ratio() * 100

    def _get_subject_keywords(self, subject: str) -> set:
        keyword_maps = {
            "aiml": {"model", "train", "data", "neural", "predict", "loss", "accuracy"},
            "dsa": {"algorithm", "complexity", "time", "space", "sort", "search", "node"},
            "os": {"process", "thread", "memory", "cpu", "schedule", "sync", "kernel"},
            "dbms": {"query", "table", "index", "normal", "transaction", "acid", "join"},
            "webdev": {"html", "css", "javascript", "api", "frontend", "backend", "http"}
        }
        return keyword_maps.get(subject, set())

    def _calculate_keyword_match(self, user_text: str, solution_text: str, subject: str) -> float:
        solution_keywords = set(solution_text.split())
        user_keywords = set(user_text.split())
        subject_specific_keywords = self._get_subject_keywords(subject)
        
        common_keywords = user_keywords.intersection(solution_keywords)
        important_matches = common_keywords.intersection(subject_specific_keywords)
        
        if not solution_keywords: return 0
        
        base_score = (len(common_keywords) / len(solution_keywords)) * 100
        bonus_score = len(important_matches) * 10
        
        return min(100, base_score + bonus_score)

    def _calculate_completeness(self, user_text: str, question: str) -> float:
        if len(user_text.split()) < 20: return 30
        
        score = 70
        if "explain" in question.lower() and len(user_text.split()) > 50:
            score += 15
        if "code" in question.lower() and ("def" in user_text or "class" in user_text or "function" in user_text):
            score += 15
        return min(100, score)

    def _calculate_structure_quality(self, user_answer: str) -> float:
        score = 50
        if "```" in user_answer: score += 25
        if re.search(r'^\d+\.|\*', user_answer, re.MULTILINE): score += 25
        return min(100, score)

    def _generate_feedback(self, score: float) -> str:
        if score >= 90: return "Excellent work! Your answer is comprehensive, accurate, and well-structured."
        if score >= 75: return "Good job! You have a solid understanding. Try to add more detail or examples next time."
        if score >= 60: return "Decent attempt. You've grasped the main concepts but missed some key details."
        if score >= 40: return "Your answer shows some understanding but lacks depth and correctness. Review the core topics."
        return "This answer needs significant improvement. Please review the topic thoroughly and try again."

    def _identify_strengths(self, user_answer: str, score: float) -> List[str]:
        strengths = []
        if len(user_answer) > 150: strengths.append("Provided a detailed explanation.")
        if "```" in user_answer: strengths.append("Included code examples.")
        if score > 70: strengths.append("Good grasp of core concepts.")
        if not strengths: strengths.append("Made a good attempt to solve the problem.")
        return strengths

    def _identify_weaknesses(self, user_answer: str, score: float, subject: str) -> List[str]:
        weaknesses = []
        if len(user_answer) < 50: weaknesses.append("Answer is too brief and lacks detail.")
        if score < 50: weaknesses.append("Missing key concepts and explanations.")
        if subject == "dsa" and "complexity" not in user_answer.lower():
            weaknesses.append("Missing analysis of time/space complexity.")
        if not weaknesses: weaknesses.append("Focus on providing more comprehensive explanations.")
        return weaknesses

    def _generate_suggestions(self, score: float, subject: str) -> List[str]:
        suggestions = []
        if score < 70:
            suggestions.append(f"Review fundamental {subject} concepts.")
            suggestions.append("Practice explaining concepts step-by-step.")
        
        subject_suggestions = {
            "dsa": "Focus on implementing algorithms and analyzing complexity.",
            "aiml": "Study different model evaluation techniques.",
            "os": "Practice with process scheduling problems.",
            "dbms": "Practice writing complex SQL queries.",
            "webdev": "Build more small projects to solidify concepts."
        }
        if subject in subject_suggestions:
            suggestions.append(subject_suggestions[subject])
        
        if not suggestions:
            suggestions.append("Keep practicing with more advanced problems.")
        
        return suggestions