"""
pdf_parser.py
PSG College of Technology — Question Paper Parser

Format per unit:
  1.a          →  2 marks   (unit number ONLY on part a)
     a.(ii)    →  2 marks
     b)        →  6 marks
     c) i)     → 10 marks   (either)
     (OR)
     c) ii)    → 10 marks   (or)

  2.a          →  next unit begins
     ...

PSG Tech watermark: diagonal "PSGTECH" / "PSG COLLEGE OF TECHNOLOGY"
text is scattered throughout — we strip it at character level.
"""

import re
import pdfplumber
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass


# ── Question dataclass ────────────────────────────────────────────────────────

@dataclass
class Question:
    unit: int
    part: str          # 'a_i', 'a_ii', 'b', 'c_i', 'c_ii'
    marks: int         # 2, 6, or 10
    is_either_or: bool
    text: str
    raw_line: str      # for debugging


PART_MARKS = {
    "a_i":  2,   # 1st two-mark question
    "a_ii": 2,   # 2nd two-mark question
    "a":    2,   # generic part a fallback
    "b":    6,   # the single six-mark question
    "b_i":  6,   # legacy fallback
    "b_ii": 6,   # legacy fallback
    "c_i":  10,  # 10 marks (either)
    "c_ii": 10,  # 10 marks (or)
}

EITHER_OR_PARTS = {"c_i", "c_ii"}


# ── Character-level watermark filter ─────────────────────────────────────────
# PSG Tech watermark is a diagonal "PSGTECH" stamp.
# pdfplumber sees it as characters with a 45° rotation matrix.

def not_watermark_char(char) -> bool:
    """
    Keep only upright characters (rotation matrix near identity).
    Watermark chars have matrix=(0.707, 0.707, -0.707, 0.707, ...) — 45° rotation.
    """
    m = char.get("matrix", (1, 0, 0, 1, 0, 0))
    # m[1] and m[2] are sin/cos components of rotation
    # For upright text: m[1]≈0, m[2]≈0
    if len(m) >= 4 and (abs(m[1]) > 0.1 or abs(m[2]) > 0.1):
        return False  # rotated → watermark
    return True


# ── Line-level noise filters ──────────────────────────────────────────────────

# Bloom's taxonomy level tags like (L1), (L2), ... (L6) at end of lines
RE_BLOOM = re.compile(r"\s*\(L[1-6]\)\s*$")

# Page footer / header patterns
RE_PAGE_NOISE = re.compile(
    r"(page\s*no\s*[.:]|www\.|\.com|reg\s*no|"
    r"roll\s*no|to\s*be\s*filled|"
    r"no\s*of\s*pages|course\s*code\s*:\s*\d|"
    r"answer\s*all|time\s*:\s*\d|max.*marks|"
    r"semester\s*examination|psg\s*college|coimbatore|"
    r"be\s*[–-]\s*electronic|department\s*of)",
    re.IGNORECASE,
)

# Watermark fragment patterns (letter clusters left after char-filter misses)
RE_WATERMARK_FRAG = re.compile(
    r"^[PSGTECH\s]{1,15}$",   # lines that are only PSGTECH letters + spaces
    re.IGNORECASE,
)

# Numeric-only lines (like "4012" exam code)
RE_NUMERIC_ONLY = re.compile(r"^\s*\d{3,6}\s*$")


def clean_question_text(text: str) -> str:
    """Remove Bloom's tags, trailing codes, and extra whitespace from question text."""
    # Remove Bloom's taxonomy tags: (L1), (L4) etc.
    text = RE_BLOOM.sub("", text)
    # Remove trailing exam codes like "(L4)" mid-text
    text = re.sub(r"\s*\(L[1-6]\)", "", text)
    # Remove "Page No. : N" anywhere in text
    text = re.sub(r"Page\s*No\s*\.?\s*:\s*\d+", "", text, flags=re.IGNORECASE)
    # Remove "4012" style exam codes (4-digit standalone numbers)
    text = re.sub(r"\b\d{4}\b", "", text)
    # Remove course code references like "19L701"
    text = re.sub(r"\b\d{2}[A-Z]\d{3}\b", "", text)
    # Remove "No of Pages : N"
    text = re.sub(r"No\s*of\s*Pages\s*:\s*\d+", "", text, flags=re.IGNORECASE)
    # Remove "Course Code : XXXXX"
    text = re.sub(r"Course\s*Code\s*:\s*[\w]+", "", text, flags=re.IGNORECASE)
    # Collapse multiple spaces
    text = re.sub(r"  +", " ", text)
    return text.strip()


def is_noise_line(line: str) -> bool:
    """Return True if this line should be discarded entirely."""
    stripped = line.strip()
    if not stripped:
        return True
    if RE_PAGE_NOISE.search(stripped) and len(stripped) < 80:
        return True
    if RE_WATERMARK_FRAG.match(stripped):
        return True
    if RE_NUMERIC_ONLY.match(stripped):
        return True
    return False


# ── PSG Tech question paper regex patterns ────────────────────────────────────

# Unit start: "1. a) i)" / "1. a) i)" / "1.a" / "1) a"
# Captures: group(1)=unit_num, group(2)=rest of text after the a/a(i) marker
RE_UNIT_A = re.compile(
    r"^\s*(\d)\s*[.)]\s*[aA]\s*[.)]\s*(?:[.(]?\s*[iI]\s*[).]?\s*)?(.*)?$"
)

# a(ii) line: "ii)" / "a) ii)" / "a.(ii)" — but NOT "iii)" or "(OR)"
RE_A_II = re.compile(
    r"^\s*(?:[aA]\s*[.)]\s*)?[.(]?\s*ii\s*[).]?\s*(.*)?$",
    re.IGNORECASE,
)

# b) line: "b)" / "b." — NOT starting with a digit (avoid matching sub-items)
RE_B = re.compile(
    r"^\s*[bB]\s*[.)]\s*(.*)?$"
)

# c) or c) i) — Either (10 marks)
RE_C_START = re.compile(
    r"^\s*[cC]\s*[.)]\s*(?:[.(]?\s*i\s*[).]?\s*)?(.*)?$",
    re.IGNORECASE,
)

# c) ii) or standalone ii) — Or (10 marks)
RE_C_OR_START = re.compile(
    r"^\s*(?:[cC]\s*[.)]\s*)?[.(]?\s*ii\s*[).]?\s*(.*)?$",
    re.IGNORECASE,
)

# Standalone (OR) / OR separator
RE_OR = re.compile(r"^\s*\(?OR\)?\s*$", re.IGNORECASE)

# Standalone (EITHER) separator
RE_EITHER = re.compile(r"^\s*\(?EITHER\)?\s*$", re.IGNORECASE)

# CO / BTL annotation lines to skip
RE_CO_LINE = re.compile(r"^\s*CO\s*[O0]?\s*:", re.IGNORECASE)
RE_BTL_LINE = re.compile(r"BTL\s*:", re.IGNORECASE)


# ── Extraction ────────────────────────────────────────────────────────────────

def extract_text_from_pdf(file_path: str) -> str:
    """
    Extract text from a PSG Tech question paper PDF with:
    1. Character-level watermark removal (rotation matrix filter)
    2. Line-level noise removal (headers, footers, watermark fragments)
    """
    lines_out = []

    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            # Step 1: filter out rotated (watermark) characters
            filtered_page = page.filter(not_watermark_char)
            page_text = filtered_page.extract_text()
            if not page_text:
                continue

            for line in page_text.split("\n"):
                # Step 2: skip noise lines
                if is_noise_line(line):
                    continue
                lines_out.append(line)

    return "\n".join(lines_out)


# ── Parsing ───────────────────────────────────────────────────────────────────

def _strip_part_prefix(line: str, part: str) -> str:
    """
    Remove the leading part marker from a line so we get clean question text.
    e.g. "i) Draw the VI..." → "Draw the VI..."
         "ii) Examine..." → "Examine..."
         "b) Write..." → "Write..."
    """
    # Remove leading: i) / ii) / a) i) / b) / c) i) / c) ii) etc.
    line = re.sub(
        r"^\s*(?:\d\s*[.)]\s*)?(?:[a-cA-C]\s*[.)]\s*)?(?:[.(]?\s*i{1,2}\s*[).]?\s*)?",
        "",
        line,
    ).strip()
    return line


def parse_questions_from_text(text: str) -> List[Question]:
    """
    State machine parser for PSG Tech question paper text.

    States:
      - Waiting for unit start (N.a ...)
      - Inside a_i   → collect until a_ii / b / c_i marker
      - Inside a_ii  → collect until b marker
      - Inside b     → collect until c_i marker
      - Inside c_i   → collect until (OR) / c_ii marker
      - Inside c_ii  → collect until next unit start
    """
    lines = text.split("\n")
    questions: List[Question] = []

    current_unit: Optional[int] = None
    current_part: Optional[str] = None
    current_lines: List[str]    = []
    seen_or: bool               = False   # tracks if we just saw (OR)

    def flush():
        nonlocal current_unit, current_part, current_lines
        if current_unit is not None and current_part and current_lines:
            raw = " ".join(l for l in current_lines if l.strip())
            q_text = clean_question_text(raw)
            if q_text and len(q_text) > 5:  # skip trivial fragments
                questions.append(Question(
                    unit=current_unit,
                    part=current_part,
                    marks=PART_MARKS.get(current_part, 10 if "c" in current_part else 0),
                    is_either_or=(current_part in EITHER_OR_PARTS),
                    text=q_text,
                    raw_line=current_lines[0] if current_lines else "",
                ))

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue

        # Skip annotation/CO lines
        if RE_CO_LINE.match(line) or RE_BTL_LINE.search(line):
            continue

        # ── (OR) separator ────────────────────────────────────────────────────
        if RE_OR.match(line):
            seen_or = True
            continue

        # ── (EITHER) separator ────────────────────────────────────────────────
        if RE_EITHER.match(line):
            continue

        # ── New unit start: "N. a) i) ..." ───────────────────────────────────
        m_unit = RE_UNIT_A.match(line)
        if m_unit:
            flush()
            current_unit  = int(m_unit.group(1))
            current_part  = "a_i"
            seen_or       = False
            rest          = (m_unit.group(2) or "").strip()
            rest          = clean_question_text(rest)
            current_lines = [rest] if rest else []
            continue

        if current_unit is None:
            continue  # haven't started parsing yet

        # ── Part markers (order matters — check most specific first) ──────────

        # If seen_or was True, the next line begins c_ii (Or)
        if seen_or and current_part in ("c_i", "c", "b"):
            flush()
            current_part  = "c_ii"
            seen_or       = False
            m_c2 = RE_C_OR_START.match(line)
            rest = (m_c2.group(1) or "").strip() if m_c2 else line
            rest = clean_question_text(rest)
            current_lines = [rest] if rest else []
            continue

        # c) or c) i) — Part C (10 marks)
        m_c = RE_C_START.match(line)
        if m_c and current_part in ("b", "a_ii", "a_i"):
            flush()
            current_part  = "c_i"
            seen_or       = False
            rest          = clean_question_text((m_c.group(1) or "").strip())
            current_lines = [rest] if rest else []
            continue

        # b) — 6-mark question
        m_b = RE_B.match(line)
        if m_b and current_part in ("a_i", "a_ii"):
            flush()
            current_part  = "b"
            seen_or       = False
            rest          = clean_question_text((m_b.group(1) or "").strip())
            current_lines = [rest] if rest else []
            continue

        # a) ii) — 2nd two-mark question
        m_a2 = RE_A_II.match(line)
        if m_a2 and current_part == "a_i":
            flush()
            current_part  = "a_ii"
            seen_or       = False
            rest          = (m_a2.group(1) or "").strip()
            rest          = clean_question_text(rest)
            current_lines = [rest] if rest else []
            continue

        # ── Continuation line ─────────────────────────────────────────────────
        cleaned = clean_question_text(line)
        if cleaned:
            current_lines.append(cleaned)

    flush()
    return questions


# ── Conversion to chunks ──────────────────────────────────────────────────────

def questions_to_chunks(questions: List[Question]) -> List[Dict]:
    """Convert Question objects to chunk dicts for Qdrant ingestion."""
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
