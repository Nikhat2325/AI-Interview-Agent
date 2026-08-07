from fastapi import APIRouter
from pydantic import BaseModel
from app.memory import InterviewMemory


from app.ai import generate_response, evaluate_answer

emory = InterviewMemory()
router = APIRouter()


class InterviewRequest(BaseModel):
    candidate:str
    role:str



class AnswerRequest(BaseModel):
    question:str
    answer:str



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
def evaluate(data:AnswerRequest):

    result = evaluate_answer(
        data.question,
        data.answer
    )

    return result