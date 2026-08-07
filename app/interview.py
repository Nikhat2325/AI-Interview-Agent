from fastapi import APIRouter
from pydantic import BaseModel
from app.ai import generate_response


router = APIRouter()


class InterviewRequest(BaseModel):
    candidate:str
    role:str


@router.post("/interview")
def create_interview(data:InterviewRequest):

    result = generate_response(
        data.candidate,
        data.role
    )

    return {
        "question":result
    }