#!/usr/bin/env python3
import argparse
import csv
from pathlib import Path
from urllib.parse import parse_qs, urlparse


DEFAULT_INPUT = Path('data/raw/coupang_seed_urls.txt')
DEFAULT_PARSED_OUTPUT = Path('data/raw/coupang_seed_urls_parsed.csv')
DEFAULT_DEDUPED_OUTPUT = Path('data/raw/coupang_seed_urls_deduped.txt')


def extract_seed_metadata(seed_url: str) -> dict:
    parsed = urlparse(seed_url.strip())
    path_parts = [part for part in parsed.path.split('/') if part]

    product_id = ''
    if len(path_parts) >= 3 and path_parts[0] == 'vp' and path_parts[1] == 'products':
        product_id = path_parts[2]

    query_params = parse_qs(parsed.query)
    item_id = first_query_value(query_params, 'itemId')
    vendor_item_id = first_query_value(query_params, 'vendorItemId')
    canonical_url = build_canonical_url(product_id, item_id, vendor_item_id)

    return {
        'seed_url': seed_url.strip(),
        'canonical_url': canonical_url,
        'product_id': product_id,
        'item_id': item_id,
        'vendor_item_id': vendor_item_id,
        'has_item_id': int(bool(item_id)),
        'has_vendor_item_id': int(bool(vendor_item_id)),
    }


def first_query_value(query_params: dict, key: str) -> str:
    values = query_params.get(key, [])
    return values[0] if values else ''


def build_canonical_url(product_id: str, item_id: str, vendor_item_id: str) -> str:
    if not product_id:
        return ''

    base_url = f'https://www.coupang.com/vp/products/{product_id}'
    query_parts = []

    if item_id:
        query_parts.append(f'itemId={item_id}')
    if vendor_item_id:
        query_parts.append(f'vendorItemId={vendor_item_id}')

    if not query_parts:
        return base_url

    return f'{base_url}?{"&".join(query_parts)}'


def read_seed_urls(input_path: Path) -> list[str]:
    with input_path.open('r', encoding='utf-8') as file:
        return [line.strip() for line in file if line.strip()]


def dedupe_seed_rows(rows: list[dict]) -> list[dict]:
    deduped_by_key = {}

    for row in rows:
        dedupe_key = row['canonical_url'] or row['seed_url']
        existing = deduped_by_key.get(dedupe_key)
        if existing is None or row_completeness_score(row) > row_completeness_score(existing):
            deduped_by_key[dedupe_key] = row

    return sorted(deduped_by_key.values(), key=lambda row: (row['product_id'], row['item_id'], row['vendor_item_id']))


def row_completeness_score(row: dict) -> tuple[int, int, int]:
    return (
        int(bool(row['product_id'])),
        int(bool(row['item_id'])),
        int(bool(row['vendor_item_id'])),
    )


def write_parsed_csv(rows: list[dict], output_path: Path) -> None:
    fieldnames = [
        'seed_url',
        'canonical_url',
        'product_id',
        'item_id',
        'vendor_item_id',
        'has_item_id',
        'has_vendor_item_id',
    ]
    with output_path.open('w', encoding='utf-8-sig', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_deduped_txt(rows: list[dict], output_path: Path) -> None:
    canonical_urls = [row['canonical_url'] or row['seed_url'] for row in rows]
    output_path.write_text('\n'.join(canonical_urls) + '\n', encoding='utf-8')


def main() -> None:
    parser = argparse.ArgumentParser(description='Extract Coupang seed URL metadata and dedupe seeds.')
    parser.add_argument('--input', type=Path, default=DEFAULT_INPUT)
    parser.add_argument('--parsed-output', type=Path, default=DEFAULT_PARSED_OUTPUT)
    parser.add_argument('--deduped-output', type=Path, default=DEFAULT_DEDUPED_OUTPUT)
    args = parser.parse_args()

    seed_urls = read_seed_urls(args.input)
    parsed_rows = [extract_seed_metadata(seed_url) for seed_url in seed_urls]
    deduped_rows = dedupe_seed_rows(parsed_rows)

    write_parsed_csv(parsed_rows, args.parsed_output)
    write_deduped_txt(deduped_rows, args.deduped_output)

    print(f'input_rows={len(seed_urls)}')
    print(f'parsed_output={args.parsed_output}')
    print(f'deduped_output={args.deduped_output}')
    print(f'deduped_rows={len(deduped_rows)}')


if __name__ == '__main__':
    main()
