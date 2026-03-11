from __future__ import annotations

import argparse
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.collectors.base import (
    load_raw_review_rows,
    merge_raw_review_rows,
    save_raw_review_rows,
)
from src.collect_reviews import build_parser, collect_reviews


def build_merge_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Parse Coupang HTML files and merge them into data/raw/raw_reviews.csv."
    )
    parser.add_argument("--html-dir", type=Path, required=True)
    parser.add_argument("--html-glob", default="*.html")
    parser.add_argument("--output", type=Path, default=Path("data/raw/raw_reviews.csv"))
    parser.add_argument("--platform", choices=["coupang"], default="coupang")
    parser.add_argument("--source-note", default="")
    return parser


def main() -> None:
    parser = build_merge_parser()
    args = parser.parse_args()

    collect_args = build_parser().parse_args(
        [
            "--platform",
            args.platform,
            "--html-dir",
            str(args.html_dir),
            "--html-glob",
            args.html_glob,
            "--output",
            str(args.output),
            "--source-note",
            args.source_note,
        ]
    )

    new_records = collect_reviews(collect_args)
    new_rows = [record.to_row() for record in new_records]
    existing_rows = load_raw_review_rows(args.output)
    merged_rows = merge_raw_review_rows(existing_rows, new_rows)
    save_raw_review_rows(merged_rows, args.output)

    print(
        f"Merged {len(new_rows)} parsed rows into {args.output}. "
        f"Total unique rows: {len(merged_rows)}"
    )


if __name__ == "__main__":
    main()
