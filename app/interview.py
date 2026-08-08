from fastapi import APIRouter
from pydantic import BaseModel

from app.ai import evaluate_answer
from app.memory import InterviewMemory
from app.agents import interview_orchestrator
from app.ai import get_candidate, get_relevant_curriculum


router = APIRouter()

memory = InterviewMemory()


# =========================
# Request Models
# =========================

class InterviewRequest(BaseModel):
    candidate: str
    role: str


class AnswerRequest(BaseModel):
    candidate: str
    question: str
    answer: str


# =========================
# Start Interview
# =========================

@router.post("/interview")
def start_interview(request: InterviewRequest):

    result = interview_orchestrator(
        request.candidate,
        request.role
    )

    return result


# =========================
# Evaluate Answer
# =========================

@router.post("/evaluate")
def evaluate(data: AnswerRequest):

    result = evaluate_answer(
        data.question,
        data.answer
    )

    memory.add_result(
        candidate=data.candidate,
        question=data.question,
        answer=data.answer,
        evaluation=result
    )

    return result


# =========================
# Get Interview Session
# =========================

@router.get("/session/{candidate}")
def get_interview_session(candidate: str):

    session = memory.get_session(candidate)

    if not session:
        return {
            "message": "No interview session found"
        }

    return session


# =========================
# Get Relevant Curriculum
# =========================

@router.get("/curriculum/{candidate}")
def curriculum_for_candidate(candidate: str):

    profile = get_candidate(candidate)

    if not profile:
        return {
            "message": "Candidate not found"
        }

    curriculum = get_relevant_curriculum(profile)

    return {
        "candidate": candidate,
        "relevant_curriculum": curriculum
    }