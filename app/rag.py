from typing import Optional

from openai import OpenAI

from app.config import OPENAI_API_KEY, CHAT_MODEL
from app.fetcher import fetch_project, fetch_projects
from app.chunker import chunk_project_payload, chunk_full_json_payload, normalize_payload
from app.embeddings import create_embedding
from app.pinecone_db import (
    upsert_chunks,
    search_similar,
    delete_all_vectors,
    delete_project_vectors,
)
from app.database import SessionLocal
from app.fact_cache import save_project_facts

client = OpenAI(api_key=OPENAI_API_KEY)


async def sync_project_knowledge(project_id: Optional[str] = None):
    if project_id:
        payload = await fetch_project(project_id)
    else:
        payload = await fetch_projects()

    payload = normalize_payload(payload)

    db = SessionLocal()

    try:
        save_project_facts(db, payload)
    finally:
        db.close()

    chunks = chunk_project_payload(payload)
    chunks += chunk_full_json_payload(payload, max_lines=40)

    for chunk in chunks:
        chunk["embedding"] = create_embedding(chunk["text"])

    if project_id:
        delete_project_vectors(project_id)
    else:
        delete_all_vectors()

    upsert_chunks(chunks)

    return {
        "scope": "single" if project_id else "global",
        "project_id": project_id,
        "synced_chunks": len(chunks),
        "cached_facts": True,
    }


def answer_question(question: str, project_id: Optional[str] = None):
    query_embedding = create_embedding(question)
    results = search_similar(query_embedding, top_k=12, project_id=project_id)

    matches = results.matches if hasattr(results, "matches") else results.get("matches", [])

    contexts = []

    for match in matches:
        metadata = match.metadata if hasattr(match, "metadata") else match.get("metadata", {})
        text = metadata.get("text", "")

        if text:
            contexts.append(text)

    if not contexts:
        return {
            "answer": "I don't have enough information in the project data to answer that. Please run sync first.",
            "sources": [],
        }

    context_text = "\n\n---\n\n".join(contexts)

    if project_id:
        project_rule = f"- Only answer for project_id {project_id}."
    else:
        project_rule = "- The context may contain multiple projects. Mention project names when useful."

    prompt = f"""
You are a project data assistant.

Answer the user's question using ONLY the provided JSON context.

Rules:
- If the answer exists in the context, answer clearly.
- Understand this API shape: each item can contain project plus top-level raidd.
- The project name is found at project.name.
- RAIDD data can be found at raidd.aiDetection.raiddData and raidd.aiDetection.email.raiddData.
- If the user asks "what is the project name", answer from Project Name / project.name only.
- If there is one project in context, give only that project name.
- If there are multiple projects, list the project names.
- If the user asks about RAIDD, risks, assumptions, issues, dependencies, decisions, AI detection, source email, sentiment, tasks, meetings, manager, client, status, URL, or date, search the context carefully.
{project_rule}
- Do not use outside knowledge.
- Do not invent information.
- Keep the answer concise.

Context:
{context_text}

User question:
{question}
"""

    response = client.chat.completions.create(
        model=CHAT_MODEL,
        messages=[
            {
                "role": "system",
                "content": "You answer questions from synced project JSON data only.",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0.1,
    )

    return {
        "answer": response.choices[0].message.content,
        "sources": [
            match.metadata if hasattr(match, "metadata") else match.get("metadata", {})
            for match in matches
        ],
    }