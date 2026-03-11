from __future__ import annotations

import csv
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import DEFAULT_KAKAOMAP_BLANK_FILE, DEFAULT_KAKAOMAP_RAW_FILE


FIELDNAMES = [
    "review_id",
    "platform",
    "review_text_raw",
    "label",
    "label_reason",
    "annotator",
    "annotated_at",
    "store_or_product_name",
    "rating",
    "has_photo",
    "event_flag_raw",
    "reorder_count_raw",
    "notes",
]


def main() -> None:
    raw_path = DEFAULT_KAKAOMAP_RAW_FILE
    output_path = DEFAULT_KAKAOMAP_BLANK_FILE

    if not raw_path.exists():
        print(f"Raw file not found: {raw_path}")
        return

    with raw_path.open(encoding="utf-8-sig", newline="") as csv_file:
        raw_rows = list(csv.DictReader(csv_file))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8-sig", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=FIELDNAMES)
        writer.writeheader()
        for row in raw_rows:
            writer.writerow(
                {
                    "review_id": row.get("review_id", ""),
                    "platform": row.get("platform", ""),
                    "review_text_raw": row.get("review_text_raw", ""),
                    "label": "",
                    "label_reason": "",
                    "annotator": "",
                    "annotated_at": "",
                    "store_or_product_name": row.get("store_or_product_name", ""),
                    "rating": row.get("rating", ""),
                    "has_photo": row.get("has_photo", ""),
                    "event_flag_raw": row.get("event_flag_raw", ""),
                    "reorder_count_raw": row.get("reorder_count_raw", ""),
                    "notes": "",
                }
            )

    print(f"Derived {output_path} from {raw_path}. Rows: {len(raw_rows)}")


if __name__ == "__main__":
    main()
