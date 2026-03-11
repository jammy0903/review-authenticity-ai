from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path

from src.config import DEFAULT_RAW_FILE, RAW_REVIEW_COLUMNS


@dataclass(slots=True)
class RawReviewRecord:
    review_id: str
    platform: str
    store_or_product_name: str
    review_text_raw: str
    rating: str = ""
    has_photo: int = 0
    event_flag_raw: str = ""
    reorder_count_raw: str = ""
    collected_at: str = ""
    source_note: str = ""

    def to_row(self) -> dict:
        row = asdict(self)
        row["review_text_raw"] = " ".join(str(self.review_text_raw).split())
        row["store_or_product_name"] = " ".join(str(self.store_or_product_name).split())
        row["collected_at"] = self.collected_at or date.today().isoformat()
        return row


def records_to_dataframe(records: list[RawReviewRecord]) -> list[dict]:
    unique_rows: list[dict] = []
    seen_keys: set[tuple[str, str]] = set()
    for record in records:
        row = record.to_row()
        dedupe_key = (row["platform"], row["review_id"])
        if dedupe_key in seen_keys:
            continue

        seen_keys.add(dedupe_key)
        unique_rows.append(row)

    return unique_rows


def save_raw_reviews(records: list[RawReviewRecord], output_path: Path | None = None) -> Path:
    target_path = output_path or DEFAULT_RAW_FILE
    target_path.parent.mkdir(parents=True, exist_ok=True)

    rows = records_to_dataframe(records)
    with target_path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=RAW_REVIEW_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    return target_path


def load_raw_review_rows(csv_path: Path | None = None) -> list[dict]:
    target_path = csv_path or DEFAULT_RAW_FILE
    if not target_path.exists():
        return []

    with target_path.open("r", encoding="utf-8", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        return list(reader)


def merge_raw_review_rows(existing_rows: list[dict], new_rows: list[dict]) -> list[dict]:
    merged_rows: list[dict] = []
    seen_keys: set[tuple[str, str]] = set()

    for row in [*existing_rows, *new_rows]:
        normalized_row = {column: row.get(column, "") for column in RAW_REVIEW_COLUMNS}
        dedupe_key = (normalized_row["platform"], normalized_row["review_id"])
        if dedupe_key in seen_keys:
            continue

        seen_keys.add(dedupe_key)
        merged_rows.append(normalized_row)

    return merged_rows


def save_raw_review_rows(rows: list[dict], output_path: Path | None = None) -> Path:
    target_path = output_path or DEFAULT_RAW_FILE
    target_path.parent.mkdir(parents=True, exist_ok=True)

    with target_path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=RAW_REVIEW_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    return target_path
