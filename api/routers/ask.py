from datetime import datetime

from fastapi import APIRouter
from pydantic import BaseModel


router = APIRouter()


class AskRequest(BaseModel):
    question: str
    dataset: str = "olist"


@router.post("")
def ask(request: AskRequest):
    return {
        "status": "pending",
        "question": request.question,
        "answer": "RAG system will be available after Day 5",
        "dataset": request.dataset,
        "timestamp": datetime.now().isoformat(),
    }
