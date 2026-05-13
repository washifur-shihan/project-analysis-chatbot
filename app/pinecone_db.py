from typing import Optional

from pinecone import Pinecone, ServerlessSpec

from app.config import PINECONE_API_KEY, PINECONE_INDEX_NAME, EMBEDDING_DIMENSION

pc = Pinecone(api_key=PINECONE_API_KEY)


def clean_metadata(metadata: dict) -> dict:
    cleaned = {}

    for key, value in metadata.items():
        if value is None:
            continue

        if isinstance(value, (str, int, float, bool)):
            cleaned[key] = value

        elif isinstance(value, list):
            cleaned[key] = [str(item) for item in value if item is not None]

        else:
            cleaned[key] = str(value)

    return cleaned


def init_pinecone():
    existing_indexes = [idx["name"] for idx in pc.list_indexes()]

    if PINECONE_INDEX_NAME not in existing_indexes:
        pc.create_index(
            name=PINECONE_INDEX_NAME,
            dimension=EMBEDDING_DIMENSION,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1"),
        )

    return pc.Index(PINECONE_INDEX_NAME)


index = init_pinecone()


def delete_all_vectors():
    """
    Clears all old vectors from Pinecone.
    Use this before global sync so old project data does not appear in chat.
    """
    index.delete(delete_all=True)


def delete_project_vectors(project_id: str):
    """
    Clears vectors for one project before re-syncing that project.
    """
    index.delete(
        filter={
            "project_id": {
                "$eq": project_id
            }
        }
    )


def upsert_chunks(chunks, batch_size=50):
    vectors = []

    for chunk in chunks:
        metadata = {
            **chunk.get("metadata", {}),
            "text": chunk.get("text", ""),
        }

        vectors.append({
            "id": chunk["id"],
            "values": chunk["embedding"],
            "metadata": clean_metadata(metadata),
        })

    if not vectors:
        return

    for i in range(0, len(vectors), batch_size):
        index.upsert(vectors=vectors[i:i + batch_size])


def search_similar(query_embedding, top_k=5, project_id: Optional[str] = None):
    query = {
        "vector": query_embedding,
        "top_k": top_k,
        "include_metadata": True,
    }

    if project_id:
        query["filter"] = {
            "project_id": {
                "$eq": project_id
            }
        }

    return index.query(**query)