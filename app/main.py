from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from app.rag import sync_project_knowledge, answer_question
from app.database import Base, engine, SessionLocal
from app.fact_cache import find_cached_answer
from app import models

app = FastAPI(title="Project RAG Chatbot")

Base.metadata.create_all(bind=engine)

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


class ChatRequest(BaseModel):
    question: str


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={}
    )


@app.post("/sync")
async def sync():
    return await sync_project_knowledge()


@app.post("/chat")
def chat(request: ChatRequest):
    db = SessionLocal()

    try:
        cached = find_cached_answer(db, request.question)

        if cached:
            return {
                "answer": cached["answer"],
                "sources": [
                    {
                        "type": cached["source"]
                    }
                ]
            }

    finally:
        db.close()

    return answer_question(request.question)