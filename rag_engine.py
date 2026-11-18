import chromadb

from sentence_transformers import SentenceTransformer

client = chromadb.PersistentClient(
    path="./chroma_db"
)

collection = client.get_or_create_collection(
    name="incident_memory"
)

model = SentenceTransformer(
    'all-MiniLM-L6-v2'
)


def store_incident(text, metadata=None):

    embedding = model.encode(text).tolist()

    collection.add(
        documents=[text],
        embeddings=[embedding],
        ids=[str(hash(text))],
        metadatas=[metadata or {}]
    )


def search_similar_incidents(query):

    embedding = model.encode(query).tolist()

    results = collection.query(
        query_embeddings=[embedding],
        n_results=3
    )

    return results
