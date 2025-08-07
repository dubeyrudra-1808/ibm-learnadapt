from typing import Any, List
import re

class ResponseEvaluator:
    """Enhanced response evaluator with smarter answer comparison logic."""

    def compare_answers(self, user_answer: Any, correct_answer: Any, question_type: str) -> bool:
        """Compares user and correct answers based on question type."""
        if user_answer is None:
            return False
        
        try:
            if question_type == "MCQ":
                return self._compare_mcq(user_answer, correct_answer)
            elif question_type == "MSQ":
                return self._compare_msq(user_answer, correct_answer)
            elif question_type == "PREDICT_OUTPUT":
                return self._compare_output(user_answer, correct_answer)
            else:
                # Default comparison for any other types
                return str(user_answer).strip().lower() == str(correct_answer).strip().lower()
        except Exception as e:
            print(f"Error comparing answers: {e}")
            return False

    def _compare_mcq(self, user_answer: Any, correct_answer: Any) -> bool:
        """Compare single-choice answers."""
        return str(user_answer).strip().upper() == str(correct_answer).strip().upper()

    def _compare_msq(self, user_answer: Any, correct_answer: Any) -> bool:
        """Compare multiple-select answers by converting both to sets."""
        if not isinstance(user_answer, list) or not isinstance(correct_answer, list):
            return False # MSQ answers should be lists
        
        # Normalize and convert to sets for order-independent comparison
        user_set = {str(item).strip().upper() for item in user_answer}
        correct_set = {str(item).strip().upper() for item in correct_answer}
        
        return user_set == correct_set

    def _compare_output(self, user_answer: Any, correct_answer: Any) -> bool:
        """Compare PREDICT_OUTPUT answers with some flexibility."""
        user_str = str(user_answer).strip()
        correct_str = str(correct_answer).strip()
        
        # 1. Exact match
        if user_str == correct_str:
            return True
        
        # 2. Case-insensitive match
        if user_str.lower() == correct_str.lower():
            return True
        
        # 3. Normalize whitespace and compare
        user_normalized = ' '.join(user_str.split())
        correct_normalized = ' '.join(correct_str.split())
        if user_normalized.lower() == correct_normalized.lower():
            return True
            
        # 4. For numeric outputs, try comparing as numbers
        try:
            # Extract numbers (including decimals and negatives)
            user_num_str = re.sub(r'[^\d.-]', '', user_str)
            correct_num_str = re.sub(r'[^\d.-]', '', correct_str)
            if user_num_str and correct_num_str:
                user_num = float(user_num_str)
                correct_num = float(correct_num_str)
                # Allow for small floating-point differences
                return abs(user_num - correct_num) < 0.001
        except (ValueError, TypeError):
            pass # Not a number, continue to next check

        return False
