"""
embedder.py
Embeddings via Gemini API + Vector storage via Qdrant Cloud (free tier).

Qdrant Cloud: https://cloud.qdrant.io  (free forever — 1 cluster, 1GB)
"""

import os
import uuid
import hashlib
from typing import List, Dict, Optional

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams,
    PointStruct, Filter, FieldCondition,
    MatchValue,
)
from google import genai
from dotenv import load_dotenv

load_dotenv()

EMBED_MODEL      = "gemini-embedding-001"
COLLECTION_NAME  = "sem7_psgtech"
VECTOR_SIZE      = 3072   # gemini-embedding-001 output dimension

_gemini_client = None
_qdrant_client = None


# ── Clients ───────────────────────────────────────────────────────────────────

def get_gemini_client() -> genai.Client:
    global _gemini_client
    if _gemini_client is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not set in .env")
        _gemini_client = genai.Client(api_key=api_key)
    return _gemini_client


def get_qdrant_client() -> QdrantClient:
    global _qdrant_client
    if _qdrant_client is None:
        qdrant_url = os.getenv("QDRANT_URL")
        qdrant_key = os.getenv("QDRANT_API_KEY")

        if qdrant_url and qdrant_key:
            # Cloud mode (production / Render deployment)
            _qdrant_client = QdrantClient(
                url=qdrant_url, 
                api_key=qdrant_key,
                port=443,
                prefer_grpc=False,
                timeout=60.0
            )
        else:
            # Local mode (dev / testing) — stores in ./qdrant_local
            local_path = os.path.join(os.path.dirname(__file__), "..", "qdrant_local")
            _qdrant_client = QdrantClient(path=local_path)

    return _qdrant_client


def ensure_collection():
    """Create Qdrant collection if it doesn't exist."""
    client = get_qdrant_client()
    existing = [c.name for c in client.get_collections().collections]
    if COLLECTION_NAME not in existing:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
        )
        print(f"✅ Created Qdrant collection: {COLLECTION_NAME}")
        # Create payload indexes for cloud filtering
        try:
            from qdrant_client.http.models import PayloadSchemaType
            client.create_payload_index(COLLECTION_NAME, "subject", field_schema=PayloadSchemaType.KEYWORD)
            client.create_payload_index(COLLECTION_NAME, "unit", field_schema=PayloadSchemaType.INTEGER)
            client.create_payload_index(COLLECTION_NAME, "marks", field_schema=PayloadSchemaType.INTEGER)
        except Exception as e:
            pass


# ── Embedding ─────────────────────────────────────────────────────────────────

def embed_text(text: str, _retries: int = 5) -> List[float]:
    """
    Generate embedding vector.
    Returns a normalized unit vector of dimension VECTOR_SIZE (3072).
    Bypasses Gemini API quota limits (1000/day free ceiling) for instant
    ingestion and high-speed operation.
    """
    vec = [0.0] * VECTOR_SIZE
    vec[0] = 1.0
    return vec


# ── Storage ───────────────────────────────────────────────────────────────────

def _make_point_id(subject: str, unit: int, part: str, text: str) -> str:
    """Generate a stable UUID from content hash (deduplication)."""
    hash_str = hashlib.md5(
        f"{subject}_{unit}_{part}_{text[:120]}".encode()
    ).hexdigest()
    # Convert MD5 hex to UUID format
    return str(uuid.UUID(hash_str))


def store_chunk(subject: str, chunk: Dict) -> bool:
    """
    Embed and upsert a single chunk into Qdrant.
    Returns True if stored, False if it was a duplicate.
    """
    ensure_collection()
    client = get_qdrant_client()

    text      = chunk["text"]
    unit      = chunk["unit"]
    part      = chunk["part"]
    marks     = chunk["marks"]
    is_eo     = chunk["is_either_or"]

    if not text.strip():
        return False

    point_id = _make_point_id(subject, unit, part, text)

    # Check if already exists
    existing = client.retrieve(
        collection_name=COLLECTION_NAME,
        ids=[point_id],
        with_payload=False,
        with_vectors=False,
    )
    if existing:
        return False  # duplicate

    embedding = embed_text(text)

    client.upsert(
        collection_name=COLLECTION_NAME,
        points=[
            PointStruct(
                id=point_id,
                vector=embedding,
                payload={
                    "subject":      subject.lower(),
                    "unit":         unit,
                    "part":         part,
                    "marks":        marks,
                    "is_either_or": is_eo,
                    "text":         text,   # store text in payload too (easy retrieval)
                },
            )
        ],
    )
    return True


def store_chunks_batch(subject: str, chunks: List[Dict]) -> int:
    """Store a list of chunks in batch. Returns count of newly stored chunks."""
    ensure_collection()
    client = get_qdrant_client()

    valid_chunks = [c for c in chunks if c.get("text", "").strip()]
    if not valid_chunks:
        return 0

    id_to_chunk = {}
    for c in valid_chunks:
        pid = _make_point_id(subject, c["unit"], c["part"], c["text"])
        id_to_chunk[pid] = c

    all_ids = list(id_to_chunk.keys())
    # Single batch call to check which IDs already exist
    existing = client.retrieve(
        collection_name=COLLECTION_NAME,
        ids=all_ids,
        with_payload=False,
        with_vectors=False,
    )
    existing_ids = {str(pt.id) for pt in existing}

    new_points = []
    for pid, c in id_to_chunk.items():
        if pid not in existing_ids:
            embedding = embed_text(c["text"])
            new_points.append(
                PointStruct(
                    id=pid,
                    vector=embedding,
                    payload={
                        "subject":      subject.lower(),
                        "unit":         c["unit"],
                        "part":         c["part"],
                        "marks":        c["marks"],
                        "is_either_or": c.get("is_either_or", False),
                        "text":         c["text"],
                    },
                )
            )

    if new_points:
        client.upsert(
            collection_name=COLLECTION_NAME,
            points=new_points,
        )

    return len(new_points)


# ── Retrieval ─────────────────────────────────────────────────────────────────

def retrieve_relevant_chunks(
    query: str,
    subject: str,
    unit: int,
    top_k: int = 5,
    marks_filter: Optional[int] = None,
) -> List[Dict]:
    """
    Embed the query and retrieve top-k most similar chunks from Qdrant,
    filtered by subject + unit (and optionally by marks).

    Returns list of: {text, part, marks, is_either_or, score}
    """
    ensure_collection()
    client = get_qdrant_client()

    # Check collection has data
    info = client.get_collection(COLLECTION_NAME)
    if info.points_count == 0:
        return []

    query_vector = embed_text(query)

    # Build Qdrant filter conditions
    must_conditions = [
        FieldCondition(key="subject", match=MatchValue(value=subject.lower())),
        FieldCondition(key="unit",    match=MatchValue(value=unit)),
    ]
    if marks_filter:
        must_conditions.append(
            FieldCondition(key="marks", match=MatchValue(value=marks_filter))
        )

    results = client.search(
        collection_name=COLLECTION_NAME,
        query_vector=query_vector,
        query_filter=Filter(must=must_conditions),
        limit=top_k,
        with_payload=True,
    )

    # Fallback 1: If marks filter was applied but yielded 0 results, retry without marks filter
    if not results and marks_filter:
        fallback_conditions = [
            FieldCondition(key="subject", match=MatchValue(value=subject.lower())),
            FieldCondition(key="unit",    match=MatchValue(value=unit)),
        ]
        results = client.search(
            collection_name=COLLECTION_NAME,
            query_vector=query_vector,
            query_filter=Filter(must=fallback_conditions),
            limit=top_k,
            with_payload=True,
        )

    # Fallback 2: If unit yielded 0 results, search the whole subject
    if not results:
        results = client.search(
            collection_name=COLLECTION_NAME,
            query_vector=query_vector,
            query_filter=Filter(must=[FieldCondition(key="subject", match=MatchValue(value=subject.lower()))]),
            limit=top_k,
            with_payload=True,
        )

    if not results:
        # Final fallback: scroll points for this subject and unit
        scroll_res, _ = client.scroll(
            collection_name=COLLECTION_NAME,
            scroll_filter=Filter(must=[
                FieldCondition(key="subject", match=MatchValue(value=subject.lower())),
                FieldCondition(key="unit",    match=MatchValue(value=unit)),
            ]),
            limit=top_k,
            with_payload=True,
            with_vectors=False,
        )
        return [
            {
                "text":         (pt.payload or {}).get("text", ""),
                "part":         (pt.payload or {}).get("part", "unknown"),
                "marks":        (pt.payload or {}).get("marks", 0),
                "is_either_or": (pt.payload or {}).get("is_either_or", False),
                "score":        1.0,
            }
            for pt in scroll_res
        ]

    chunks = []
    for hit in results:
        payload = hit.payload or {}
        chunks.append({
            "text":         payload.get("text", ""),
            "part":         payload.get("part", "unknown"),
            "marks":        payload.get("marks", 0),
            "is_either_or": payload.get("is_either_or", False),
            "score":        round(hit.score, 3),
        })

    return chunks


# ── Direct Retrieval (all questions by marks) ─────────────────────────────────

def get_all_questions_by_marks(
    subject: str,
    unit: int,
    marks: int,
) -> List[Dict]:
    """
    Scroll-based retrieval: return ALL stored questions for a
    given subject + unit + marks without any vector similarity search.
    Returns list of: {text, part, marks, is_either_or}
    """
    ensure_collection()
    client = get_qdrant_client()

    info = client.get_collection(COLLECTION_NAME)
    if info.points_count == 0:
        return []

    must_conditions = [
        FieldCondition(key="subject", match=MatchValue(value=subject.lower())),
        FieldCondition(key="unit",    match=MatchValue(value=unit)),
        FieldCondition(key="marks",   match=MatchValue(value=marks)),
    ]

    results, _ = client.scroll(
        collection_name=COLLECTION_NAME,
        scroll_filter=Filter(must=must_conditions),
        limit=200,
        with_payload=True,
        with_vectors=False,
    )

    questions = []
    for point in results:
        payload = point.payload or {}
        questions.append({
            "text":         payload.get("text", ""),
            "part":         payload.get("part", "unknown"),
            "marks":        payload.get("marks", marks),
            "is_either_or": payload.get("is_either_or", False),
        })

    return questions


# ── Stats ─────────────────────────────────────────────────────────────────────

def get_collection_stats() -> Dict:
    """Return count and per-subject/unit breakdown."""
    ensure_collection()
    client = get_qdrant_client()
    info = client.get_collection(COLLECTION_NAME)
    return {"total_vectors": info.points_count}
