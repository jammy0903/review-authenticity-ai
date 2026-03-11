from __future__ import annotations

import argparse
import csv
from pathlib import Path


DEFAULT_FIELDNAMES = [
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


def load_rows(csv_path: Path) -> list[dict]:
    with csv_path.open(encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        rows: list[dict] = []
        for row in reader:
            normalized_row = {key.lstrip("\ufeff"): value for key, value in row.items()}
            rows.append(normalized_row)
        return rows


def build_existing_label_map(existing_rows: list[dict]) -> dict[str, dict]:
    label_map: dict[str, dict] = {}
    for row in existing_rows:
        review_id = row["review_id"]
        if review_id:
            label_map[review_id] = row
    return label_map


def derive_labeled_rows(raw_rows: list[dict], existing_label_map: dict[str, dict]) -> list[dict]:
    derived_rows: list[dict] = []
    for raw_row in raw_rows:
        existing_row = existing_label_map.get(raw_row["review_id"], {})
        derived_rows.append(
            {
                "review_id": raw_row["review_id"],
                "platform": raw_row["platform"],
                "review_text_raw": raw_row["review_text_raw"],
                "label": existing_row.get("label", ""),
                "label_reason": existing_row.get("label_reason", ""),
                "annotator": existing_row.get("annotator", ""),
                "annotated_at": existing_row.get("annotated_at", ""),
                "store_or_product_name": raw_row.get("store_or_product_name", ""),
                "rating": raw_row.get("rating", ""),
                "has_photo": raw_row.get("has_photo", ""),
                "event_flag_raw": raw_row.get("event_flag_raw", ""),
                "reorder_count_raw": raw_row.get("reorder_count_raw", ""),
                "notes": existing_row.get("notes", ""),
            }
        )
    return derived_rows


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create a labeled CSV from raw reviews and copy any existing labels by review_id."
    )
    parser.add_argument("--raw", type=Path, required=True)
    parser.add_argument("--existing-labeled", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    raw_rows = load_rows(args.raw)
    existing_rows = load_rows(args.existing_labeled) if args.existing_labeled.exists() else []
    existing_label_map = build_existing_label_map(existing_rows)
    derived_rows = derive_labeled_rows(raw_rows, existing_label_map)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=DEFAULT_FIELDNAMES)
        writer.writeheader()
        writer.writerows(derived_rows)

    labeled_count = sum(1 for row in derived_rows if row["label"])
    print(
        f"Derived {args.output} from {args.raw}. "
        f"Rows: {len(derived_rows)}, prefilled labels: {labeled_count}"
    )


if __name__ == "__main__":
    main()
