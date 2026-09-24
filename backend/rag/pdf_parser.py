"""
pdf_parser.py
PSG College of Technology — Question Paper Parser

Format per unit:
  1.a          →  3 marks   (unit number ONLY on part a)
     b.(i)     →  6 marks   (no unit number prefix)
     b.(ii)    →  6 marks
     c.(i)     → 10 marks   (either)
     c.(ii)    → 10 marks   (or)

  2.a          →  next unit begins
     b.(i)     →  6 marks
     ...

PSG Tech watermark: diagonal "PSGTECH" / "PSG COLLEGE OF TECHNOLOGY"
text is scattered throughout — we strip it aggressively.
"""

import re
import pdfplumber
from typing import List, Dict
from dataclasses import dataclass


# ── Question dataclass ────────────────────────────────────────────────────────

@dataclass
class Question:
    unit: int
    part: str          # 'a', 'b_i', 'b_ii', 'c_i', 'c_ii'
    marks: int         # 3, 6, or 10
    is_either_or: bool
    text: str
    raw_line: str      # for debugging


PART_MARKS = {
    "a":    3,
    "b_i":  6,
    "b_ii": 6,
    "c_i":  10,
    "c_ii": 10,
}

EITHER_OR_PARTS = {"c_i", "c_ii"}


# ── PSG Tech watermark patterns ───────────────────────────────────────────────
# The diagonal watermark gets extracted as repeated fragments by pdfplumber

WATERMARK_PATTERNS = [
    re.compile(r"P\s*S\s*G\s*T\s*E\s*C\s*H", re.IGNORECASE),
    re.compile(r"P\s*S\s*G\s+C\s*O\s*L\s*L\s*E\s*G\s*E", re.IGNORECASE),
    re.compile(r"P\s*S\s*G\s+C\s*T", re.IGNORECASE),
    re.compile(r"COIMBATORE", re.IGNORECASE),
    re.compile(r"PSG\s*TECH", re.IGNORECASE),
    re.compile(r"psg\s*tech", re.IGNORECASE),
]

def is_watermark_line(line: str) -> bool:
    """Return True if this line is likely a PSG watermark fragment."""
    stripped = line.strip()
    if not stripped:
        return False
    # Check watermark patterns
    for pat in WATERMARK_PATTERNS:
        if pat.search(stripped):
            return True
    # Very short lines that are just letter clusters (watermark noise)
    # e.g. "G T E C H", "S G T", etc.
    if re.match(r"^[A-Z\s]{1,12}$", stripped) and len(stripped.replace(" ", "")) <= 8:
        return True
    return False


# ── PSG Tech question paper regex patterns ────────────────────────────────────

# Matches: "1.a" / "1) a" / "1. a"  (unit number + part a — marks start of new unit)
RE_UNIT_A = re.compile(
    r"^\s*(\d)\s*[.)]\s*[aA]\b\.?\s*(.*)?$"
)

# Matches continuation parts (NO unit number prefix):
# "b.(i)" / "b) (i)" / "(b)(i)" / "b (i)"
RE_B_II = re.compile(
    r"^\s*[bB]\s*[.)]\s*[.(]?\s*[iI]{2}\b\.?\s*(.*)?$"
)
RE_B_I = re.compile(
    r"^\s*[bB]\s*[.)]\s*[.(]?\s*[iI]\b(?!\s*[iI])\.?\s*(.*)?$"
)

# "c.(i)" / "c) i" / "c. (ii)"
RE_C_II = re.compile(
    r"^\s*(?:(?:or|either|OR|Either)\s+)?[cC]\s*[.)]\s*[.(]?\s*[iI]{2}\b\.?\s*(.*)?$"
)
RE_C_I = re.compile(
    r"^\s*(?:(?:or|either|OR|Either)\s+)?[cC]\s*[.)]\s*[.(]?\s*[iI]\b(?!\s*[iI])\.?\s*(.*)?$"
)

# Standalone either/or separator lines
RE_EITHER_OR = re.compile(r"^\s*(either|or)\s*$", re.IGNORECASE)

# Header/footer noise to skip
RE_NOISE = re.compile(
    r"(page\s*\d+|www\.|\.com|reg\s*no|name\s*:|department|semester|time\s*:|max\s*marks|answer\s*all)",
    re.IGNORECASE,
)


# ── Extraction ────────────────────────────────────────────────────────────────

def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from PDF with PSG Tech watermark filtering."""
    lines_out = []

    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if not page_text:
                continue
            for line in page_text.split("\n"):
                if is_watermark_line(line):
                    continue
                if RE_NOISE.search(line) and len(line.strip()) < 60:
                    continue
                lines_out.append(line)

    return "\n".join(lines_out)


# ── Parsing ───────────────────────────────────────────────────────────────────

def _try_match_continuation(line: str):
    """
    Try to match a continuation sub-part line (b/c parts — no unit prefix).
    Returns (part_key, captured_text) or None.
    Order matters: check ii before i.
    """
    for pattern, part_key in [
        (RE_C_II, "c_ii"),
        (RE_B_II, "b_ii"),
        (RE_C_I,  "c_i"),
        (RE_B_I,  "b_i"),
    ]:
        m = pattern.match(line)
        if m:
            captured = m.group(1).strip() if m.lastindex and m.group(1) else ""
            return part_key, captured
    return None


def parse_questions_from_text(text: str) -> List[Question]:
    """
    Parse PSG Tech question paper text into Question objects.

    State machine:
      - When we see "N.a" → new unit N begins, start collecting part 'a'
      - When we see "b.(i)", "b.(ii)", "c.(i)", "c.(ii)" → continuation of same unit
      - Accumulate text lines until the next known header
    """
    lines = text.split("\n")
    questions: List[Question] = []

    current_unit = None
    current_part = None
    current_lines: List[str] = []

    def flush():
        if current_unit is not None and current_part and current_lines:
            q_text = " ".join(l for l in current_lines if l.strip())
            if q_text.strip():
                questions.append(Question(
                    unit=current_unit,
                    part=current_part,
                    marks=PART_MARKS.get(current_part, 0),
                    is_either_or=(current_part in EITHER_OR_PARTS),
                    text=q_text.strip(),
                    raw_line=current_lines[0] if current_lines else "",
                ))

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue

        # Skip standalone either/or markers
        if RE_EITHER_OR.match(line):
            continue

        # Check if this is "N.a" — start of a new unit
        m_unit_a = RE_UNIT_A.match(line)
        if m_unit_a:
            flush()
            current_unit = int(m_unit_a.group(1))
            current_part = "a"
            first_text   = m_unit_a.group(2).strip() if m_unit_a.group(2) else ""
            current_lines = [first_text] if first_text else []
            continue

        # Check if this is a continuation part (b.(i), b.(ii), c.(i), c.(ii))
        if current_unit is not None:
            cont = _try_match_continuation(line)
            if cont:
                flush()
                current_part  = cont[0]
                first_text    = cont[1]
                current_lines = [first_text] if first_text else []
                continue

        # Otherwise it's a continuation of the current question text
        if current_unit is not None and current_part:
            current_lines.append(line)

    flush()
    return questions


# ── Conversion to chunks ──────────────────────────────────────────────────────

def questions_to_chunks(questions: List[Question]) -> List[Dict]:
    """Convert Question objects to chunk dicts for ChromaDB ingestion."""
    chunks = []
    for q in questions:
        if not q.text.strip():
            continue
        chunks.append({
            "text":         q.text,
            "unit":         q.unit,
            "part":         q.part,
            "marks":        q.marks,
            "is_either_or": q.is_either_or,
        })
    return chunks


def parse_pdf_to_chunks(file_path: str) -> List[Dict]:
    """Full pipeline: PDF → cleaned text → questions → chunks."""
    text      = extract_text_from_pdf(file_path)
    questions = parse_questions_from_text(text)
    return questions_to_chunks(questions)


# ── Fallback: generic chunker ─────────────────────────────────────────────────

def fallback_chunk_by_unit(text: str, default_units: int = 5) -> List[Dict]:
    """
    Simple chunker when PSG format isn't detected.
    Splits on unit headers or by equal partition.
    """
    RE_UNIT_HEADER = re.compile(r"^\s*unit\s*[-:]?\s*(\d+)", re.IGNORECASE)
    lines = text.split("\n")
    unit_lines: Dict[int, List[str]] = {i: [] for i in range(1, default_units + 1)}
    current_unit = 1

    for line in lines:
        m = RE_UNIT_HEADER.match(line.strip())
        if m:
            current_unit = int(m.group(1))
        elif line.strip():
            unit_lines.setdefault(current_unit, []).append(line.strip())

    chunks = []
    for unit, lns in unit_lines.items():
        words = " ".join(lns).split()
        for i in range(0, max(1, len(words)), 200):
            passage = " ".join(words[i:i+200]).strip()
            if passage:
                chunks.append({
                    "text":         passage,
                    "unit":         unit,
                    "part":         "generic",
                    "marks":        0,
                    "is_either_or": False,
                })
    return chunks
