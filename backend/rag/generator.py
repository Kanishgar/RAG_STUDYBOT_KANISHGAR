"""
generator.py
Generates mark-aware answers using Gemini + retrieved question context.

The prompt changes based on marks:
  3 marks  → brief, 2-3 key points
  6 marks  → medium, with explanation and example
  10 marks → detailed, structured essay-style answer
"""

import os
from google import genai
from typing import List, Dict, Optional
from dotenv import load_dotenv

load_dotenv()

FALLBACK_MODELS = [
    "gemma-4-26b-a4b-it",
    "gemini-3.5-flash-lite",
    "gemini-3.8-flash",
    "gemini-3.1-flash-lite",
]

SUBJECT_FULLNAMES = {
    "rf":    "RF Passive and Active Circuits",
    "mmc":   "Multimedia Computing",
    "vr":    "Virtual Reality",
    "rdbms": "Relational Database Management Systems",
    "foc":   "Fiber Optic Communication",
}

# Answer length expectations per mark type
MARK_GUIDANCE = {
    3:  "Give a CONCISE answer — 2 to 3 key points only. No lengthy explanations. Suitable for a 3-mark short answer.",
    6:  "Give a MEDIUM-LENGTH answer — 4 to 6 points with brief explanations for each. Include one relevant example if helpful. Suitable for a 6-mark answer.",
    10: "Give a DETAILED and STRUCTURED answer — Use headings/subheadings, explain with examples, include diagrams description if needed. Cover all major aspects. Suitable for a 10-mark long answer.",
    0:  "Give a clear and helpful answer based on the context provided.",
}


def get_client() -> genai.Client:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not set.")
    return genai.Client(api_key=api_key)


def build_prompt(
    query: str,
    subject: str,
    unit: int,
    context_chunks: List[Dict],
    detected_marks: Optional[int] = None,
) -> str:
    subject_name = SUBJECT_FULLNAMES.get(subject.lower(), subject.upper())

    # Build context from retrieved chunks
    context_parts = []
    for i, chunk in enumerate(context_chunks, 1):
        part_name = chunk.get("part", "").replace("_", ".").upper()
        marks_num = chunk.get("marks", "")
        mark_label = f"[{marks_num} Marks — Part {part_name}]" if marks_num else f"[Part {part_name}]"
        context_parts.append(
            f"Question {i} {mark_label}:\n{chunk['text'].strip()}"
        )

    context_text = "\n\n---\n\n".join(context_parts) if context_parts else "No questions found."

    prompt = f"""You are an exam question retrieval assistant for PSG College of Technology (Anna University Semester 7).
Subject: {subject_name}
Unit: Unit {unit}

--- RETRIEVED QUESTIONS FROM EXAM PAPERS ---
{context_text}
--- END QUESTIONS ---

Student Query:
"{query}"

STRICT RULES:
1. Output ONLY the exact question(s) from the exam papers above that match the student's request.
2. DO NOT provide answers, explanations, solutions, or commentary. Output the exact question text alone.
3. Format each matching question as:
   • **[Part ... — X Marks]**: <exact question text>
4. If multiple matching questions are found, list each one.
5. If no questions match the student query, output: "No matching past exam questions found for this topic."

Exact Exam Question(s):"""
    return prompt


def detect_marks_from_query(query: str) -> Optional[int]:
    """
    Try to detect if the user mentions marks in the query.
    e.g. "explain for 10 marks", "3 mark question", "write short note (6 marks)"
    """
    import re
    m = re.search(r"(\d+)\s*[-]?\s*mark", query, re.IGNORECASE)
    if m:
        val = int(m.group(1))
        if val in (3, 6, 10):
            return val
    return None


def generate_answer(
    query: str,
    subject: str,
    unit: int,
    context_chunks: List[Dict],
    detected_marks: Optional[int] = None,
) -> str:
    """
    Retrieve and present exact exam questions matching the query.
    """
    if not context_chunks:
        return f"No past exam questions found in the uploaded question papers for Unit {unit}."

    client = get_client()

    # Auto-detect marks from query if not explicitly provided
    if not detected_marks:
        detected_marks = detect_marks_from_query(query)

    prompt = build_prompt(query, subject, unit, context_chunks, detected_marks)

    last_error = None
    for model_name in FALLBACK_MODELS:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
            )
            if response.text:
                return response.text
        except Exception as e:
            print(f"⚠️ Model {model_name} failed: {e}. Trying fallback...")
            last_error = e
            continue

    return f"Service temporarily busy across all models. Details: {last_error}"
