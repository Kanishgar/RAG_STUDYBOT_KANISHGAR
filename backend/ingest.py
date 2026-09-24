"""
ingest.py — Pre-process & ingest all PDFs into ChromaDB (run ONCE before launch)

Usage:
    python ingest.py                          # ingest all PDFs in data/
    python ingest.py --subject rf             # ingest only RF subject
    python ingest.py --file data/rf/qp.pdf --subject rf
    python ingest.py --stats                  # show what's stored

data/ folder structure:
    data/
      rf/    ← drop all RF question paper PDFs here
      mmc/
      vr/
      rdbms/
      foc/
"""

import os
import argparse
from pathlib import Path
from rag.pdf_parser import (
    parse_pdf_to_chunks,
    extract_text_from_pdf,
    parse_questions_from_text,
    fallback_chunk_by_unit,
)
from rag.embedder import store_chunks_batch, get_collection_stats

DATA_DIR = Path(__file__).parent / "data"

SUBJECTS = {
    "rf":    "RF Passive & Active Circuits",
    "mmc":   "Multimedia Computing",
    "vr":    "Virtual Reality",
    "rdbms": "RDBMS",
    "foc":   "Fiber Optic Communication",
}

PART_LABEL = {
    "a":     "Part A (3 marks)",
    "b_i":   "Part B(i) (6 marks)",
    "b_ii":  "Part B(ii) (6 marks)",
    "c_i":   "Part C(i) — Either (10 marks)",
    "c_ii":  "Part C(ii) — Or (10 marks)",
    "generic": "Generic chunk",
}


def ingest_pdf(pdf_path: Path, subject: str, verbose: bool = True):
    """Parse and ingest a single PDF."""
    if verbose:
        print(f"\n  📄 {pdf_path.name}")

    # Try Anna University structured parse first
    chunks = parse_pdf_to_chunks(str(pdf_path))

    if not chunks:
        if verbose:
            print("     ⚠️  No Anna-U pattern found — falling back to generic chunker")
        raw_text = extract_text_from_pdf(str(pdf_path))
        if not raw_text.strip():
            print("     ❌ No text extracted — is the PDF scanned/image-only?")
            return 0
        chunks = fallback_chunk_by_unit(raw_text)

    if verbose:
        # Show breakdown
        from collections import Counter
        part_counts = Counter(c["part"] for c in chunks)
        for part, count in sorted(part_counts.items()):
            label = PART_LABEL.get(part, part)
            print(f"     📝 {label}: {count} questions found")

    stored = store_chunks_batch(subject, chunks)
    if verbose:
        print(f"     ✅ {stored} new chunks stored (skipped {len(chunks) - stored} duplicates)")

    return stored


def ingest_subject(subject: str):
    """Ingest all PDFs for one subject."""
    subject_dir = DATA_DIR / subject
    if not subject_dir.exists():
        print(f"  ⚠️  Folder not found: {subject_dir}  — skipping")
        return 0

    pdfs = list(subject_dir.glob("*.pdf"))
    if not pdfs:
        print(f"  ⚠️  No PDFs in {subject_dir} — drop your question papers there!")
        return 0

    print(f"\n📚 {SUBJECTS[subject]}  ({len(pdfs)} PDF{'s' if len(pdfs)>1 else ''})")
    total = 0
    for pdf in sorted(pdfs):
        total += ingest_pdf(pdf, subject)

    print(f"  📊 Subject total: {total} new chunks")
    return total


def show_stats():
    """Print breakdown of what's in Qdrant."""
    stats = get_collection_stats()
    count = stats.get("total_vectors", 0)
    print(f"\n{'='*50}")
    print(f"📦 Qdrant Vector Store Stats")
    print(f"{'='*50}")
    print(f"Total vectors stored: {count}")
    if count == 0:
        print("  (empty — add PDFs to data/ and run ingest.py)")
    print(f"{'='*50}")


def main():
    parser = argparse.ArgumentParser(
        description="Sem 7 RAG Ingestion — Anna University question paper format"
    )
    parser.add_argument("--subject", choices=list(SUBJECTS.keys()),
                        help="Ingest only this subject")
    parser.add_argument("--file",    help="Ingest a specific PDF file")
    parser.add_argument("--stats",   action="store_true",
                        help="Show ChromaDB stats and exit")
    args = parser.parse_args()

    print("\n🚀 Sem 7 RAG Ingestion Pipeline")
    print("   Format: Anna University (3 / 6 / 10 marks)")
    print("=" * 50)

    if args.stats:
        show_stats()
        return

    if args.file:
        if not args.subject:
            print("❌ --subject required with --file")
            return
        ingest_pdf(Path(args.file), args.subject)

    elif args.subject:
        ingest_subject(args.subject)

    else:
        if not DATA_DIR.exists():
            print(f"\n❌ 'data/' folder not found at: {DATA_DIR}")
            print("\nCreate it and add your PDFs:")
            for s in SUBJECTS:
                print(f"  data/{s}/  ← put {SUBJECTS[s]} PDFs here")
            return

        grand_total = 0
        for subject in SUBJECTS:
            grand_total += ingest_subject(subject)

        print(f"\n{'='*50}")
        print(f"🎉 Grand total: {grand_total} new chunks ingested")

    show_stats()
    print("\n✅ Ingestion complete! Your RAG model is trained.")
    print("   Now run: uvicorn main:app --reload --port 8000\n")


if __name__ == "__main__":
    main()
