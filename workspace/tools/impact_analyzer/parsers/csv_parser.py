# parsers/csv_parser.py
import csv
import os

def extract_csv_header(path, max_rows=5):
    """
    Return header list if CSV has header row, otherwise try to infer.
    """
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", newline="", encoding="utf-8") as f:
            sniffer = csv.Sniffer()
            sample = f.read(4096)
            f.seek(0)
            has_header = False
            try:
                has_header = sniffer.has_header(sample)
            except Exception:
                has_header = True  # default to True if uncertain
            f.seek(0)
            reader = csv.reader(f)
            if has_header:
                header = next(reader, None)
                if header:
                    return [h.strip() for h in header]
            # fallback: infer column count from first data row
            first = next(reader, None)
            if first:
                return [f"col_{i}" for i in range(len(first))]
    except Exception:
        return None
    return None
