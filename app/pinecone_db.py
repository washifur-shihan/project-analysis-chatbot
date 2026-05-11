from pinecone import Pinecone, ServerlessSpec
from app.config import (
    PINECONE_API_KEY,
    PINECONE_INDEX_NAME,
    EMBEDDING_DIMENSION,
)

pc = Pinecone(api_key=PINECONE_API_KEY)


def init_pinecone():
    existing_indexes = [idx["name"] for idx in pc.list_indexes()]

    if PINECONE_INDEX_NAME not in existing_indexes:
        pc.create_index(
            name=PINECONE_INDEX_NAME,
            dimension=EMBEDDING_DIMENSION,
            metric="cosine",
            spec=ServerlessSpec(
                cloud="aws",
                region="us-east-1"
            )
        )

    return pc.Index(PINECONE_INDEX_NAME)


index = init_pinecone()


def upsert_chunks(chunks, batch_size=50):
    """
    Upsert chunks to Pinecone in smaller batches to avoid request size limits.
    Pinecone has a ~4MB max request size. Large metadata + embeddings can exceed this.
    Default batch_size=50, reduce to 25 if you still hit limits.
    """
    vectors = []

    for chunk in chunks:
        vectors.append({
            "id": chunk["id"],
            "values": chunk["embedding"],
            "metadata": {
                **chunk["metadata"],
                "text": chunk["text"]
            }
        })

    if not vectors:
        return

    # Upsert in batches to stay under Pinecone's request size limit
    for i in range(0, len(vectors), batch_size):
        batch = vectors[i:i + batch_size]
        index.upsert(vectors=batch)


def search_similar(query_embedding, top_k=5):
    return index.query(
        vector=query_embedding,
        top_k=top_k,
        include_metadata=True
    )