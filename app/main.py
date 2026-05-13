from typing import Optional

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from app.rag import sync_project_knowledge, answer_question
from app.database import Base, engine, SessionLocal
from app.fact_cache import find_cached_answer

app = FastAPI(title="Project RAG Chatbot")

Base.metadata.create_all(bind=engine)

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


class ChatRequest(BaseModel):
    question: str
    project_id: Optional[str] = None


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(request=request, name="index.html", context={})


@app.post("/sync")
async def sync_global():
    return await sync_project_knowledge()


@app.post("/sync/project/{project_id}")
async def sync_single_project(project_id: str):
    return await sync_project_knowledge(project_id=project_id)


@app.post("/chat")
def chat(request: ChatRequest):
    db = SessionLocal()

    try:
        cached = find_cached_answer(db, request.question)

        if cached and not request.project_id:
            return {
                "answer": cached["answer"],
                "sources": [{"type": cached["source"]}],
            }
    finally:
        db.close()

    return answer_question(request.question, project_id=request.project_id)


@app.post("/chat/project/{project_id}")
def chat_single_project(project_id: str, request: ChatRequest):
    return answer_question(request.question, project_id=project_id)