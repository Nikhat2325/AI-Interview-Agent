from fastapi import APIRouter
from pydantic import BaseModel

from app.ai import generate_response, evaluate_answer
from app.memory import InterviewMemory


router = APIRouter()

memory = InterviewMemory()


class InterviewRequest(BaseModel):
    candidate:str
    role:str



class AnswerRequest(BaseModel):
    candidate: str
    question: str
    answer: str


@router.post("/interview")
def create_interview(data:InterviewRequest):

    result = generate_response(
        data.candidate,
        data.role
    )

    return {
        "question":result
    }


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

@router.get("/session/{candidate}")
def get_interview_session(candidate: str):

    session = memory.get_session(candidate)

    if not session:
        return {
            "message": "No interview session found"
        }

    return session


@router.get("/curriculum/{candidate}")
def curriculum_for_candidate(candidate: str):

    from app.ai import get_candidate, get_relevant_curriculum

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