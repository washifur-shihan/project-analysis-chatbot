from openai import OpenAI

from app.config import OPENAI_API_KEY, CHAT_MODEL
from app.fetcher import fetch_projects
from app.chunker import chunk_project_payload, chunk_full_json_payload
from app.embeddings import create_embedding
from app.pinecone_db import upsert_chunks, search_similar
from app.database import SessionLocal
from app.fact_cache import save_project_facts

client = OpenAI(api_key=OPENAI_API_KEY)


async def sync_project_knowledge():
    payload = await fetch_projects()

    db = SessionLocal()
    try:
        save_project_facts(db, payload)
    finally:
        db.close()

    chunks = chunk_project_payload(payload)
    chunks += chunk_full_json_payload(payload, max_lines=40)

    for chunk in chunks:
        chunk["embedding"] = create_embedding(chunk["text"])

    upsert_chunks(chunks)

    return {
        "synced_chunks": len(chunks),
        "cached_facts": True
    }


def answer_question(question: str):
    query_embedding = create_embedding(question)
    results = search_similar(query_embedding, top_k=8)

    matches = results.matches if hasattr(results, "matches") else results.get("matches", [])

    contexts = []

    for match in matches:
        metadata = match.metadata if hasattr(match, "metadata") else match.get("metadata", {})
        text = metadata.get("text", "")

        if text:
            contexts.append(text)

    if not contexts:
        return {
            "answer": "I don't have enough information in the project data to answer that.",
            "sources": []
        }

    context_text = "\n\n---\n\n".join(contexts)

    prompt = f"""
You are a project data assistant.

Answer the user's question using ONLY the provided JSON context.

Rules:
- If the answer exists in the context, answer clearly.
- If the user asks about a person, meeting, task, message, transcript, status, vendor, manager, issue, risk, dependency, decision, action point, URL, or date, search the context carefully.
- Do not say you do not know unless the answer is truly not present in the context.
- If useful, mention the project name.
- Keep the answer concise.
- Do not invent information.

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
                "content": "You answer questions from project JSON data only."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.2
    )

    return {
        "answer": response.choices[0].message.content,
        "sources": [
            match.metadata if hasattr(match, "metadata") else match.get("metadata", {})
            for match in matches
        ]
    }