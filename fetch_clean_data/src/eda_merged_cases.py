import json
from pathlib import Path
from fetch_ocr import DocText
from download_pdf import DocPDF

def exc():

    JSONL_PATH = Path("../data/input/merged_cases/20260212_case_index_output_all.jsonl")

    with JSONL_PATH.open() as f:
        record = json.loads(f.readline())

    print(record)

    for key, value in record.items():
        print(f"{'─'*60}")
        print(f"KEY : {key}")
        print(f"TYPE: {type(value).__name__}")
        print(f"VAL : {value}")
    print('─'*60)

    # --- OCR for first sha1 ---
    sha1 = record["sha1s"][0]
    print(f"\n{'='*60}")
    print(f"Fetching OCR for sha1: {sha1}")
    print(f"{'='*60}\n")

    dt = DocText()
    pages = dt.get_text(sha1)

    print(f"Total pages returned: {len(pages)}\n")
    for page in pages:
        print(f"{'─'*60}")
        print(f"PAGE {page.page_number}")
        print(f"{'─'*60}")
        print(page.text)

    # --- PDF for first sha1 ---
    print(f"\n{'='*60}")
    print(f"Fetching PDF for sha1: {sha1}")
    print(f"{'='*60}\n")

    dp = DocPDF()
    pdf_path = dp.get_pdf(sha1)
    print(f"PDF saved to: {pdf_path}")
    print(f"File size: {pdf_path.stat().st_size:,} bytes")

    return record


if __name__ == "__main__":
    exc()