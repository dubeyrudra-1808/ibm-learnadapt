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

app = FastAPI(
    title="IBM LearnAdapt - Advanced Quiz Edition",
    description="JEE-style quiz generation and evaluation platform.",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Services
groq_service = GroqService(os.getenv("GROQ_API_KEY"))
gemini_service = GeminiService(os.getenv("GEMINI_API_KEY"))
evaluator = ResponseEvaluator()

# --- Pydantic Models ---
class QuizRequest(BaseModel):
    subject: str
    topic: str
    num_questions: int = 5
    difficulty: str = "medium"
    question_types: List[str] = ["MCQ", "MSQ", "PREDICT_OUTPUT"]

class UserAnswer(BaseModel):
    question_id: str
    answer: Any
    reasoning: str

class QuizSubmission(BaseModel):
    quiz_id: str
    student_id: str
    answers: List[UserAnswer]

# --- In-Memory Storage ---
app.state.quiz_data_store = {}

# --- API Endpoints ---
@app.get("/")
async def root():
    return {"message": "Welcome to the LearnAdapt Advanced Quiz API"}

@app.post("/api/quiz/generate")
async def generate_quiz(request: QuizRequest):
    """Generate quiz with proper error handling"""
    app.state.quiz_data_store.clear()
    
    quiz_questions = []
    for i in range(request.num_questions):
        q_type = random.choice(request.question_types)
        
        try:
            # Create prompt using Groq
            prompt = await groq_service.create_problem_prompt(
                subject=request.subject,
                topic=request.topic,
                difficulty=request.difficulty,
                q_type=q_type
            )
            
            # Generate question using Gemini (FIXED: No async needed)
            problem_data = await gemini_service.generate_quiz_question(prompt)
            
            question_id = f"q_{i+1}"
            
            # Prepare question for frontend
            frontend_question = {
                "id": question_id,
                "type": q_type,
                "question": problem_data.get("question", "Question generation failed"),
                "options": problem_data.get("options", {}),
            }
            quiz_questions.append(frontend_question)

            # Store full question data on server
            server_copy_data = problem_data.copy()
            server_copy_data["id"] = question_id
            app.state.quiz_data_store[question_id] = server_copy_data

        except Exception as e:
            print(f"Error generating question {i+1} of type {q_type}: {e}")
            # Create a fallback question
            fallback_question = gemini_service.create_fallback_question(str(e))
            question_id = f"q_{i+1}"
            
            frontend_question = {
                "id": question_id,
                "type": q_type,
                "question": fallback_question["question"],
                "options": fallback_question["options"],
            }
            quiz_questions.append(frontend_question)
            
            fallback_question["id"] = question_id
            app.state.quiz_data_store[question_id] = fallback_question
    
    quiz_id = f"quiz_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    return {"success": True, "quiz_id": quiz_id, "quiz": quiz_questions}

@app.post("/api/quiz/evaluate")
async def evaluate_quiz(submission: QuizSubmission):
    """Evaluate quiz submission"""
    if not hasattr(app.state, "quiz_data_store") or not app.state.quiz_data_store:
        raise HTTPException(status_code=404, detail="No quiz data found. Generate quiz first.")

    full_evaluation_data = []
    for user_answer in submission.answers:
        question_id = user_answer.question_id
        correct_answer_data = app.state.quiz_data_store.get(question_id)
        
        if not correct_answer_data:
            continue

        is_correct = (user_answer.answer == correct_answer_data.get("answer"))
        
        full_evaluation_data.append({
            "question": correct_answer_data.get("question"),
            "user_answer": user_answer.answer,
            "correct_answer": correct_answer_data.get("answer"),
            "user_reasoning": user_answer.reasoning,
            "ai_explanation": correct_answer_data.get("explanation"),
            "is_correct": is_correct
        })
    
    try:
        final_report = await groq_service.generate_student_report(full_evaluation_data)
        return {"success": True, "report": final_report, "details": full_evaluation_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {e}")
