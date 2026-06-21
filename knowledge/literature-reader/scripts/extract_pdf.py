#!/usr/bin/env python3
"""Extract text from PDF files using pdfplumber.

Usage:
    python3 extract_pdf.py <pdf_path> [--output <output_path>] [--pages <page_range>]

Examples:
    python3 extract_pdf.py paper.pdf
    python3 extract_pdf.py paper.pdf --output /tmp/text.txt
    python3 extract_pdf.py paper.pdf --pages 1-5
    python3 extract_pdf.py paper.pdf --pages 3
"""

import argparse
import sys
from pathlib import Path

try:
    import pdfplumber
except ImportError:
    print("Error: pdfplumber not installed. Run: pip3 install pdfplumber", file=sys.stderr)
    sys.exit(1)


def parse_page_range(page_str: str, total_pages: int) -> list[int]:
    """Parse page range string like '1-5' or '3' into list of 0-based indices."""
    if "-" in page_str:
        start, end = page_str.split("-", 1)
        start = max(1, int(start))
        end = min(total_pages, int(end))
        return list(range(start - 1, end))
    else:
        page = int(page_str)
        if 1 <= page <= total_pages:
            return [page - 1]
        return []


def extract_text(pdf_path: str, page_indices: list[int] | None = None) -> str:
    """Extract text from PDF, optionally for specific pages."""
    sections = []
    with pdfplumber.open(pdf_path) as pdf:
        total = len(pdf.pages)
        targets = page_indices if page_indices else range(total)

        for i in targets:
            if i >= total:
                continue
            page = pdf.pages[i]
            text = page.extract_text()
            if text:
                sections.append(f"--- Page {i + 1}/{total} ---\n{text}")

            tables = page.extract_tables()
            for t_idx, table in enumerate(tables):
                if table:
                    header = table[0]
                    rows = table[1:]
                    table_str = " | ".join(str(c) if c else "" for c in header) + "\n"
                    table_str += " | ".join("---" for _ in header) + "\n"
                    for row in rows:
                        table_str += " | ".join(str(c) if c else "" for c in row) + "\n"
                    sections.append(f"[Table {t_idx + 1} on Page {i + 1}]\n{table_str}")

    return "\n\n".join(sections)


def main():
    parser = argparse.ArgumentParser(description="Extract text from PDF files")
    parser.add_argument("pdf_path", help="Path to the PDF file")
    parser.add_argument("--output", "-o", help="Output file path (default: stdout)")
    parser.add_argument("--pages", "-p", help="Page range, e.g. '1-5' or '3'")
    args = parser.parse_args()

    pdf_path = Path(args.pdf_path).expanduser().resolve()
    if not pdf_path.exists():
        print(f"Error: File not found: {pdf_path}", file=sys.stderr)
        sys.exit(1)

    page_indices = None
    if args.pages:
        with pdfplumber.open(str(pdf_path)) as pdf:
            page_indices = parse_page_range(args.pages, len(pdf.pages))

    text = extract_text(str(pdf_path), page_indices)

    if args.output:
        out = Path(args.output).expanduser().resolve()
        out.write_text(text, encoding="utf-8")
        print(f"Extracted text saved to: {out}", file=sys.stderr)
    else:
        print(text)


if __name__ == "__main__":
    main()
