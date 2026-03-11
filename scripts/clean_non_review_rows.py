from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path


NON_REVIEW_PATTERNS = [
    re.compile(r"^.+, \d+개, \d+개입, \d+ml$"),
    re.compile(r"^.+, \d+kg\([^)]*\), \d+개$"),
    re.compile(r"^.+, \d+봉$"),
    re.compile(r"^팜조아 리얼 클렌즈 주스 Yellow KIT 200g \(냉동\), 5개$"),
    re.compile(r"^임실 요구르트세트, 요구르트세트 2호, 1개, 2400ml, 1박스$"),
    re.compile(r"^에르먼 S50 책상의자, 오트베이지, 640 x 500 x 1000~1080 mm$"),
    re.compile(r"^에르먼 S50 PRO AIR 풀메쉬 의자, 페블그레이, 640 x 580 x 980~1060 mm$"),
    re.compile(r"^네오체어 메쉬 사무용 게이밍 컴퓨터 의자 CPS-H, 아이보리, 610 x 1130 mm$"),
    re.compile(r"^듀오백 사무용 컴퓨터 책상 메쉬의자 Q1W 에어로, 그레이, 그레이$"),
    re.compile(r"^선물톡톡 포토인생 네컷액자 아크릴 투명 원목액자, 2x6인치\(51x154mm\), 1개$"),
    re.compile(r"^에르먼 S50 책상의자, 오닉스블랙, 640 x 500 x 1000~1080 mm$"),
    re.compile(r"^에르먼 S50 책상의자, 페블그레이, 640 x 500 x 1000~1080 mm$"),
]


def is_non_review_text(text: str) -> bool:
    normalized = " ".join(text.split())
    return any(pattern.fullmatch(normalized) for pattern in NON_REVIEW_PATTERNS)


def clean_csv(csv_path: Path, text_column: str = "review_text_raw") -> tuple[int, int]:
    with csv_path.open(encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        fieldnames = [field.lstrip("\ufeff") for field in (reader.fieldnames or [])]
        rows = []
        removed = 0
        for row in reader:
            normalized_row = {key.lstrip("\ufeff"): value for key, value in row.items()}
            if is_non_review_text(normalized_row.get(text_column, "")):
                removed += 1
                continue
            rows.append(normalized_row)

    with csv_path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return len(rows), removed


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Remove non-review rows such as product-option-only strings from CSV files."
    )
    parser.add_argument("csv_paths", nargs="+", type=Path)
    args = parser.parse_args()

    for csv_path in args.csv_paths:
        kept, removed = clean_csv(csv_path)
        print(f"{csv_path}: kept={kept}, removed={removed}")


if __name__ == "__main__":
    main()
