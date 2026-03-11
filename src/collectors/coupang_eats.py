from __future__ import annotations

import json
import re
from html import unescape

from src.collectors.base import RawReviewRecord


COUPANG_EATS_PLATFORM = "coupang_eats"


def parse_coupang_eats_reviews(html: str, source_note: str = "") -> list[RawReviewRecord]:
    store_name = extract_store_name(html)
    records = extract_json_reviews(html, store_name, source_note)

    if records:
        return records

    return extract_dom_reviews(html, store_name, source_note)


def extract_store_name(html: str) -> str:
    meta_match = re.search(r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\'](.*?)["\']', html, re.IGNORECASE)
    if meta_match:
        return clean_html_text(meta_match.group(1))

    header_match = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.IGNORECASE | re.DOTALL)
    if header_match:
        return clean_html_text(header_match.group(1))

    title_match = re.search(r"<title>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
    return clean_html_text(title_match.group(1)) if title_match else ""


def extract_json_reviews(
    html: str,
    store_name: str,
    source_note: str,
) -> list[RawReviewRecord]:
    records: list[RawReviewRecord] = []

    for raw_text in re.findall(r"<script[^>]*>(.*?)</script>", html, re.IGNORECASE | re.DOTALL):
        if "review" not in raw_text.lower():
            continue
        for payload in find_json_candidates(raw_text):
            for review in payload:
                text = str(review.get("reviewText", "") or review.get("content", "")).strip()
                if not text:
                    continue

                review_id = str(review.get("id", "")).strip() or f"ce_{len(records) + 1:04d}"
                rating = review.get("rating", "")
                has_photo = int(bool(review.get("imageUrls") or review.get("photo")))
                records.append(
                    RawReviewRecord(
                        review_id=review_id,
                        platform=COUPANG_EATS_PLATFORM,
                        store_or_product_name=store_name,
                        review_text_raw=text,
                        rating=str(rating),
                        has_photo=has_photo,
                        source_note=source_note or "coupang_eats_json",
                    )
                )

    return records


def extract_dom_reviews(
    html: str,
    store_name: str,
    source_note: str,
) -> list[RawReviewRecord]:
    records: list[RawReviewRecord] = []
    seen_texts: set[str] = set()
    node_pattern = re.compile(
        r"<(?P<tag>div|article|li)[^>]*(data-review-id=[\"'].*?[\"']|class=[\"'][^\"']*review[^\"']*[\"'])[^>]*>(?P<body>.*?)</(?P=tag)>",
        re.IGNORECASE | re.DOTALL,
    )
    for match in node_pattern.finditer(html):
        node_html = match.group(0)
        text = extract_review_text(node_html)
        if not text or text in seen_texts:
            continue

        seen_texts.add(text)
        review_id = extract_attr(node_html, "data-review-id") or f"ce_{len(records) + 1:04d}"
        rating = extract_attr(node_html, "data-rating")
        has_photo = int("<img" in node_html.lower())
        records.append(
            RawReviewRecord(
                review_id=review_id,
                platform=COUPANG_EATS_PLATFORM,
                store_or_product_name=store_name,
                review_text_raw=text,
                rating=rating,
                has_photo=has_photo,
                source_note=source_note or "coupang_eats_dom",
            )
        )

    return records


def find_json_candidates(raw_text: str) -> list[list[dict]]:
    candidates: list[list[dict]] = []
    for match in re.finditer(r"(\[\{.*?\}\])", raw_text, flags=re.DOTALL):
        fragment = match.group(1)
        try:
            payload = json.loads(fragment)
        except json.JSONDecodeError:
            continue

        if isinstance(payload, list) and payload and isinstance(payload[0], dict):
            candidates.append(payload)

    return candidates


def extract_review_text(node) -> str:
    patterns = [
        r'<[^>]*class=["\'][^"\']*content[^"\']*["\'][^>]*>(.*?)</[^>]+>',
        r'<[^>]*class=["\'][^"\']*text[^"\']*["\'][^>]*>(.*?)</[^>]+>',
        r"<p[^>]*>(.*?)</p>",
        r"<span[^>]*>(.*?)</span>",
    ]
    for pattern in patterns:
        match = re.search(pattern, node, re.IGNORECASE | re.DOTALL)
        if not match:
            continue

        text = clean_html_text(match.group(1))
        if text and len(text) >= 5:
            return text

    text = clean_html_text(node)
    return text if len(text) >= 5 else ""


def extract_attr(html: str, attr_name: str) -> str:
    match = re.search(rf'{attr_name}=["\'](.*?)["\']', html, re.IGNORECASE)
    return match.group(1).strip() if match else ""


def clean_html_text(text: str) -> str:
    without_tags = re.sub(r"<[^>]+>", " ", text)
    return " ".join(unescape(without_tags).split())
