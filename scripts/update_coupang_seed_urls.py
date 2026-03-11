#!/usr/bin/env python3
import argparse
import csv
import html
import re
from pathlib import Path
from urllib.parse import parse_qs, urlparse

DEFAULT_HTML_DIR = Path('data/raw/coupang_saved_html')
DEFAULT_SEED_INPUT = Path('data/raw/coupang_seed_urls.txt')
DEFAULT_PARSED_OUTPUT = Path('data/raw/coupang_seed_urls_parsed.csv')
DEFAULT_DEDUPED_OUTPUT = Path('data/raw/coupang_seed_urls_deduped.txt')

COUPANG_URL_PATTERN = re.compile(r'https://www\.coupang\.com/vp/products/[^\s"\'<>]+')


def load_existing_seed_urls(seed_path: Path) -> list[str]:
    if not seed_path.exists():
        return []
    with seed_path.open('r', encoding='utf-8') as file:
        return [line.strip() for line in file if line.strip()]


def normalize_html_text(text: str) -> str:
    normalized = html.unescape(text)
    normalized = normalized.replace('\\u0026', '&')
    normalized = normalized.replace('\\/', '/')
    normalized = normalized.replace('\\\\', '\\')
    return normalized


def clean_extracted_url(url: str) -> str:
    cleaned = url.rstrip('\\').rstrip(',')
    return html.unescape(cleaned)


def is_supported_product_url(url: str) -> bool:
    parsed = urlparse(url)
    path_parts = [part for part in parsed.path.split('/') if part]
    if len(path_parts) < 3:
        return False
    if path_parts[0] != 'vp' or path_parts[1] != 'products':
        return False
    if len(path_parts) > 3:
        return False
    return True


def extract_urls_from_html_file(html_path: Path) -> list[str]:
    text = html_path.read_text(encoding='utf-8', errors='ignore')
    normalized = normalize_html_text(text)
    matches = [clean_extracted_url(match) for match in COUPANG_URL_PATTERN.findall(normalized)]
    return [url for url in matches if is_supported_product_url(url)]


def extract_urls_from_html_dir(html_dir: Path) -> list[str]:
    collected = []
    for html_path in sorted(html_dir.glob('*.html')):
        collected.extend(extract_urls_from_html_file(html_path))
    return collected


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


def is_valid_row(row: dict) -> bool:
    product_id = row['product_id']
    return bool(product_id) and product_id.isdigit() and product_id != '0'


def row_completeness_score(row: dict) -> tuple[int, int, int]:
    return (
        int(bool(row['product_id'])),
        int(bool(row['item_id'])),
        int(bool(row['vendor_item_id'])),
    )


def rows_match_known_fields(candidate: dict, target: dict) -> bool:
    if candidate['product_id'] != target['product_id']:
        return False
    for key in ('item_id', 'vendor_item_id'):
        candidate_value = candidate[key]
        target_value = target[key]
        if candidate_value and target_value and candidate_value != target_value:
            return False
    return True


def is_more_complete(candidate: dict, target: dict) -> bool:
    return row_completeness_score(candidate) > row_completeness_score(target)


def remove_dominated_rows(rows: list[dict]) -> list[dict]:
    kept = []
    for row in rows:
        dominated = False
        for other in rows:
            if row is other:
                continue
            if rows_match_known_fields(other, row) and is_more_complete(other, row):
                dominated = True
                break
        if not dominated:
            kept.append(row)
    return kept


def dedupe_seed_rows(rows: list[dict]) -> list[dict]:
    deduped_by_key = {}
    for row in rows:
        dedupe_key = row['canonical_url'] or row['seed_url']
        existing = deduped_by_key.get(dedupe_key)
        if existing is None or row_completeness_score(row) > row_completeness_score(existing):
            deduped_by_key[dedupe_key] = row

    cleaned_rows = remove_dominated_rows(list(deduped_by_key.values()))
    return sorted(cleaned_rows, key=lambda row: (row['product_id'], row['item_id'], row['vendor_item_id'], row['seed_url']))


def write_seed_input(seed_urls: list[str], output_path: Path) -> None:
    output_path.write_text('\n'.join(seed_urls) + '\n', encoding='utf-8')


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
    parser = argparse.ArgumentParser(description='Extract Coupang product URLs from saved HTML, merge with seeds, and dedupe.')
    parser.add_argument('--html-dir', type=Path, default=DEFAULT_HTML_DIR)
    parser.add_argument('--seed-input', type=Path, default=DEFAULT_SEED_INPUT)
    parser.add_argument('--parsed-output', type=Path, default=DEFAULT_PARSED_OUTPUT)
    parser.add_argument('--deduped-output', type=Path, default=DEFAULT_DEDUPED_OUTPUT)
    args = parser.parse_args()

    existing_seed_urls = [url for url in load_existing_seed_urls(args.seed_input) if is_supported_product_url(url)]
    extracted_urls = extract_urls_from_html_dir(args.html_dir)
    merged_seed_urls = sorted(set(existing_seed_urls + extracted_urls))
    parsed_rows = [extract_seed_metadata(seed_url) for seed_url in merged_seed_urls]
    valid_rows = [row for row in parsed_rows if is_valid_row(row)]
    deduped_rows = dedupe_seed_rows(valid_rows)
    cleaned_seed_urls = sorted({row['seed_url'] for row in deduped_rows})

    write_seed_input(cleaned_seed_urls, args.seed_input)
    write_parsed_csv(deduped_rows, args.parsed_output)
    write_deduped_txt(deduped_rows, args.deduped_output)

    print(f'existing_seed_urls={len(existing_seed_urls)}')
    print(f'extracted_urls={len(extracted_urls)}')
    print(f'merged_seed_urls={len(merged_seed_urls)}')
    print(f'deduped_rows={len(deduped_rows)}')


if __name__ == '__main__':
    main()
