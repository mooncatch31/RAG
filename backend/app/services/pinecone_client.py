from pinecone import Pinecone, ServerlessSpec
from app.config import settings

def _pc():
    if not settings.PINECONE_API_KEY:
        raise RuntimeError("PINECONE_API_KEY not set")
    return Pinecone(api_key=settings.PINECONE_API_KEY)

def ensure_index(dimension: int):
    pc = _pc()
    name = settings.PINECONE_INDEX

    try:
        pc.describe_index(name)
    except Exception:
        pc.create_index(
            name=name,
            dimension=dimension,
            metric="cosine",
            spec=ServerlessSpec(cloud=settings.PINECONE_CLOUD, region=settings.PINECONE_REGION),
        )
    return pc.Index(name)

def get_index():
    return _pc().Index(settings.PINECONE_INDEX)
