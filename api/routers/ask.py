from datetime import datetime

from fastapi import APIRouter
from pydantic import BaseModel


router = APIRouter()


class AskRequest(BaseModel):
    question: str
    dataset: str = "olist"


@router.post("")
def ask(request: AskRequest):
    try:
        from rag.chain import RAGChain

        chain = RAGChain()
        result = chain.answer(question=request.question, dataset=request.dataset)

        return {
            "status": "success",
            "question": request.question,
            "answer": result["answer"],
            "sources": result["sources"],
            "query_time_ms": result["query_time_ms"],
            "dataset": request.dataset,
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        return {
            "status": "error",
            "question": request.question,
            "error": str(e),
            "dataset": request.dataset,
            "timestamp": datetime.now().isoformat(),
        }
