"""
main.py - FastAPI Backend for Sem 7 RAG Chatbot
PDFs are pre-ingested via ingest.py. This API handles retrieval + generation only.
"""

import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

from rag.embedder import retrieve_relevant_chunks
from rag.generator import generate_answer, detect_marks_from_query

app = FastAPI(title="Sem 7 RAG Chatbot API", version="2.0.0")

ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:3000",
    "https://kanishgar-studybot.vercel.app",   # production frontend
    "https://kanishgar-sem7.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

VALID_SUBJECTS = {"rf", "mmc", "vr", "rdbms", "foc"}


class ChatRequest(BaseModel):
    question: str
    subject: str
    unit: int
    marks: Optional[int] = None   # 3, 6, or 10 — optional, auto-detected if not given
    semester: int = 7


class ChatResponse(BaseModel):
    answer: str
    subject: str
    unit: int
    detected_marks: Optional[int]
    chunks_used: int
    top_parts: list   # which question parts were retrieved (a, b_i, c_ii, etc.)


@app.get("/")
def root():
    return {"message": "Sem 7 RAG Chatbot API v2 — Anna University format 🚀"}


@app.get("/subjects")
def get_subjects():
    return {
        "semester": 7,
        "subjects": [
            {"id": "rf",    "name": "RF Passive & Active Circuits", "units": 5},
            {"id": "mmc",   "name": "Multimedia Computing",         "units": 5},
            {"id": "vr",    "name": "Virtual Reality",              "units": 5},
            {"id": "rdbms", "name": "RDBMS",                        "units": 5},
            {"id": "foc",   "name": "Fiber Optic Communication",    "units": 5},
        ]
    }


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    RAG Chat endpoint:
    1. Embed user query
    2. Retrieve top-5 relevant question chunks from ChromaDB
    3. Generate mark-aware answer using Gemini
    """
    subject = request.subject.lower().strip()

    if subject not in VALID_SUBJECTS:
        raise HTTPException(status_code=400, detail=f"Invalid subject '{subject}'.")
    if not (1 <= request.unit <= 5):
        raise HTTPException(status_code=400, detail="Unit must be 1–5.")
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")
    if request.marks and request.marks not in (3, 6, 10):
        raise HTTPException(status_code=400, detail="Marks must be 3, 6, or 10.")

    # Auto-detect marks if not provided by user
    detected_marks = request.marks or detect_marks_from_query(request.question)

    # Retrieve relevant chunks (optionally filtered by marks)
    chunks = retrieve_relevant_chunks(
        query=request.question,
        subject=subject,
        unit=request.unit,
        top_k=5,
        marks_filter=detected_marks if request.marks else None,
    )

    # Generate mark-aware answer
    answer = generate_answer(
        query=request.question,
        subject=subject,
        unit=request.unit,
        context_chunks=chunks,
        detected_marks=detected_marks,
    )

    top_parts = list({c["part"] for c in chunks})

    return ChatResponse(
        answer=answer,
        subject=subject,
        unit=request.unit,
        detected_marks=detected_marks,
        chunks_used=len(chunks),
        top_parts=top_parts,
    )


@app.get("/health")
def health():
    return {"status": "ok"}
