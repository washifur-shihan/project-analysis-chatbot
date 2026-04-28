from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import Request
from pydantic import BaseModel

from app.rag import sync_project_knowledge, answer_question

app = FastAPI(title="Project RAG Chatbot")

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
    return answer_question(request.question)