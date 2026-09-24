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

LLM_MODEL = "gemini-3.5-flash-lite"

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
        mark_label = f"[{chunk['marks']} marks - Part {chunk['part'].replace('_', '.')}]" if chunk["marks"] else ""
        eo_label   = " [Either/Or question]" if chunk["is_either_or"] else ""
        context_parts.append(
            f"Q{i} {mark_label}{eo_label}:\n{chunk['text']}"
        )

    context_text = "\n\n---\n\n".join(context_parts) if context_parts else "No specific past questions found for this topic."

    # Figure out mark guidance
    mark_guidance = MARK_GUIDANCE.get(detected_marks, MARK_GUIDANCE[0])

    marks_section = ""
    if detected_marks:
        marks_section = f"\nAnswer Format: This appears to be a **{detected_marks}-mark** question. {mark_guidance}"

    prompt = f"""You are an expert academic assistant for Semester 7 engineering students studying under Anna University.

Subject: {subject_name}
Unit: Unit {unit}
{marks_section}

Past questions and context from this unit's question papers:

--- PAST QUESTION PAPER CONTEXT ---
{context_text}
--- END CONTEXT ---

Student's Question:
{query}

Instructions:
- Answer based primarily on the context above (past question patterns).
- Tailor the depth of your answer to the mark weightage indicated.
- Use bullet points, numbered steps, or headings as needed for clarity.
- For 10-mark answers: structure with Introduction → Main Content → Conclusion.
- For 6-mark answers: explain with brief examples.
- For 3-mark answers: be crisp and direct.
- Do NOT hallucinate. If unsure, say "This may need further reference."

Answer:"""
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
    Generate a mark-aware RAG answer using Gemini.
    """
    client = get_client()

    # Auto-detect marks from query if not explicitly provided
    if not detected_marks:
        detected_marks = detect_marks_from_query(query)

    # Also try to infer from retrieved chunks (most common marks in top results)
    if not detected_marks and context_chunks:
        mark_counts = {}
        for c in context_chunks:
            m = c.get("marks", 0)
            if m:
                mark_counts[m] = mark_counts.get(m, 0) + 1
        if mark_counts:
            detected_marks = max(mark_counts, key=mark_counts.get)

    prompt = build_prompt(query, subject, unit, context_chunks, detected_marks)

    response = client.models.generate_content(
        model=LLM_MODEL,
        contents=prompt,
    )

    return response.text or "Could not generate an answer. Please try again."
