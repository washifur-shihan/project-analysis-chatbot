from openai import OpenAI
from app.config import OPENAI_API_KEY, CHAT_MODEL
from app.fetcher import fetch_projects
from app.chunker import chunk_project_payload
from app.embeddings import create_embedding
from app.pinecone_db import upsert_chunks, search_similar

client = OpenAI(api_key=OPENAI_API_KEY)


async def sync_project_knowledge():
    payload = await fetch_projects()
    chunks = chunk_project_payload(payload)

    for chunk in chunks:
        chunk["embedding"] = create_embedding(chunk["text"])

    upsert_chunks(chunks)

    return {
        "synced_chunks": len(chunks)
    }


def answer_question(question: str):
    query_embedding = create_embedding(question)
    results = search_similar(query_embedding, top_k=6)

    contexts = []

    for match in results.get("matches", []):
        metadata = match.get("metadata", {})
        contexts.append(metadata.get("text", ""))

    context_text = "\n\n---\n\n".join(contexts)

    prompt = f"""
You are a project management assistant.

Answer the user's question using ONLY the context below.
If the answer is not available in the context, say:
"I don't have enough information in the project data to answer that."

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
                "content": "You answer project questions using retrieved project data. Be concise and accurate."
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
            match.get("metadata", {}) for match in results.get("matches", [])
        ]
    }