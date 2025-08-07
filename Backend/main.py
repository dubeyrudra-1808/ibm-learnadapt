
import random
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any
from datetime import datetime
from dotenv import load_dotenv
import os

from services.groq_service import GroqService
from services.gemini_service import GeminiService
from services.evaluator import ResponseEvaluator

load_dotenv()
app = FastAPI(title="IBM LearnAdapt - High-Quality Quiz Edition", version="4.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

groq_service = GroqService(os.getenv("GROQ_API_KEY"))
gemini_service = GeminiService(os.getenv("GEMINI_API_KEY"))
evaluator = ResponseEvaluator()

class QuizRequest(BaseModel):
    subject: str; topic: str; num_questions: int = 5; difficulty: str = "medium"
class UserAnswer(BaseModel):
    question_id: str; answer: Any; reasoning: str
class QuizSubmission(BaseModel):
    quiz_id: str; student_id: str; answers: List[UserAnswer]

app.state.quiz_data_store = {}

@app.post("/api/quiz/generate")
async def generate_quiz(request: QuizRequest):
    app.state.quiz_data_store.clear()
    gemini_service.reset_question_history()
    
    quiz_questions = []
    question_types = ["MCQ", "MSQ", "PREDICT_OUTPUT"]
    max_total_attempts = request.num_questions * 3 # Give up after this many total tries

    while len(quiz_questions) < request.num_questions and max_total_attempts > 0:
        max_total_attempts -= 1
        q_type = random.choice(question_types)
        
        try:
            prompt = await groq_service.create_problem_prompt(
                subject=request.subject, topic=request.topic, difficulty=request.difficulty, q_type=q_type
            )
            problem_data = gemini_service.generate_quiz_question(prompt)
            
            if not problem_data.get("fallback"):
                question_id = f"q_{len(quiz_questions) + 1}_{random.randint(1000, 9999)}"
                
                quiz_questions.append({
                    "id": question_id, "type": q_type,
                    "question": problem_data.get("question"), "options": problem_data.get("options"),
                })

                server_copy = problem_data.copy()
                server_copy["id"] = question_id
                server_copy["question_type"] = q_type
                app.state.quiz_data_store[question_id] = server_copy
        except Exception as e:
            print(f"Error in main generation loop: {e}")
            
    quiz_id = f"quiz_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    return {"success": True, "quiz_id": quiz_id, "quiz": quiz_questions}

@app.post("/api/quiz/evaluate")
async def evaluate_quiz(submission: QuizSubmission):
    if not hasattr(app.state, "quiz_data_store") or not app.state.quiz_data_store:
        raise HTTPException(status_code=404, detail="No quiz data found on server.")
    
    full_evaluation_data = []
    for user_answer in submission.answers:
        question_id = user_answer.question_id
        correct_answer_data = app.state.quiz_data_store.get(question_id)
        if not correct_answer_data: continue
        
        is_correct = evaluator.compare_answers(
            user_answer.answer, correct_answer_data.get("answer"), correct_answer_data.get("question_type", "MCQ")
        )
        full_evaluation_data.append({
            "question": correct_answer_data.get("question"), "user_answer": user_answer.answer,
            "correct_answer": correct_answer_data.get("answer"), "user_reasoning": user_answer.reasoning,
            "ai_explanation": correct_answer_data.get("explanation"), "is_correct": is_correct
        })
    
    try:
        final_report = await groq_service.generate_student_report(full_evaluation_data)
        return {"success": True, "report": final_report, "details": full_evaluation_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {e}")