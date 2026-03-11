from __future__ import annotations

import argparse
from pathlib import Path
from urllib.request import Request, urlopen

from src.collectors.base import save_raw_reviews
from src.collectors.coupang import parse_coupang_reviews
from src.collectors.coupang_eats import parse_coupang_eats_reviews
from src.collectors.kakaomap import parse_kakaomap_reviews
from src.config import DEFAULT_COUPANG_URL_FILE, DEFAULT_KAKAOMAP_URL_FILE


USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Collect raw reviews into the project CSV schema.")
    parser.add_argument("--platform", choices=["coupang", "coupang_eats", "kakaomap"], required=True)
    parser.add_argument("--url", help="Public page URL to fetch before parsing.")
    parser.add_argument("--url-file", type=Path, help="Text file with one public page URL per line.")
    parser.add_argument("--html-file", type=Path, help="Saved HTML file to parse instead of fetching URL.")
    parser.add_argument("--html-dir", type=Path, help="Directory that contains saved HTML files to parse in batch.")
    parser.add_argument(
        "--html-glob",
        default="*.html",
        help="Glob pattern used with --html-dir. Defaults to '*.html'.",
    )
    parser.add_argument("--output", type=Path, help="CSV output path. Defaults to data/raw/raw_reviews.csv.")
    parser.add_argument("--source-note", default="", help="Extra source note stored in raw_reviews.csv.")
    return parser


def fetch_html(url: str) -> str:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=20) as response:
        return response.read().decode("utf-8", errors="replace")


def load_html(args: argparse.Namespace) -> str:
    if args.html_file:
        return args.html_file.read_text(encoding="utf-8")

    if args.url:
        return fetch_html(args.url)

    raise ValueError("Either --url, --url-file, --html-file, or --html-dir must be provided.")


def load_url_list(url_file: Path) -> list[str]:
    return [
        line.strip()
        for line in url_file.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]


def load_html_file_list(html_dir: Path, html_glob: str) -> list[Path]:
    return sorted(path for path in html_dir.glob(html_glob) if path.is_file())


def parse_reviews_for_source(args: argparse.Namespace, html: str, source_url: str = ""):
    if args.platform == "coupang":
        return parse_coupang_reviews(html, source_url=source_url, source_note=args.source_note)
    if args.platform == "kakaomap":
        return parse_kakaomap_reviews(html, source_url=source_url, source_note=args.source_note)

    return parse_coupang_eats_reviews(html, source_note=args.source_note)


def collect_reviews(args: argparse.Namespace):
    if args.html_dir:
        all_records = []
        for html_file in load_html_file_list(args.html_dir, args.html_glob):
            html = html_file.read_text(encoding="utf-8")
            all_records.extend(parse_reviews_for_source(args, html, source_url=str(html_file)))
        return all_records

    if args.url_file:
        all_records = []
        for url in load_url_list(args.url_file):
            html = fetch_html(url)
            all_records.extend(parse_reviews_for_source(args, html, source_url=url))
        return all_records

    html = load_html(args)
    return parse_reviews_for_source(args, html, source_url=args.url or "")


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.platform == "coupang" and not args.url and not args.url_file and not args.html_file:
        args.url_file = DEFAULT_COUPANG_URL_FILE
    if args.platform == "kakaomap" and not args.url and not args.url_file and not args.html_file:
        args.url_file = DEFAULT_KAKAOMAP_URL_FILE

    records = collect_reviews(args)
    output_path = save_raw_reviews(records, args.output)
    print(f"Saved {len(records)} reviews to {output_path}")


if __name__ == "__main__":
    main()
