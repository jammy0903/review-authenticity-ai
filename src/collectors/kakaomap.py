from __future__ import annotations

import json
import re
from html import unescape

from src.collectors.base import RawReviewRecord


KAKAOMAP_PLATFORM = "kakaomap"


def parse_kakaomap_reviews(html: str, source_url: str = "", source_note: str = "") -> list[RawReviewRecord]:
    place_name = extract_place_name(html)
    place_id = extract_place_id(source_url, html)

    records = extract_json_reviews(html, place_name, place_id, source_url, source_note)
    if records:
        return dedupe_records(records)

    records = extract_dom_reviews(html, place_name, place_id, source_url, source_note)
    return dedupe_records(records)


def extract_place_name(html: str) -> str:
    patterns = [
        r'<h2[^>]*class=["\'][^"\']*tit_location[^"\']*["\'][^>]*>(.*?)</h2>',
        r'<h3[^>]*class=["\'][^"\']*tit_place[^"\']*["\'][^>]*>(.*?)</h3>',
        r'<strong[^>]*class=["\'][^"\']*tit_name[^"\']*["\'][^>]*>(.*?)</strong>',
        r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\'](.*?)["\']',
        r'<meta[^>]+name=["\']title["\'][^>]+content=["\'](.*?)["\']',
        r"<title>(.*?)</title>",
    ]
    for pattern in patterns:
        match = re.search(pattern, html, re.IGNORECASE | re.DOTALL)
        if match:
            text = clean_html_text(match.group(1))
            if text:
                return re.sub(r"\s*\|\s*카카오맵\s*$", "", text)
    return ""


def extract_place_id(source_url: str, html: str) -> str:
    meta_match = re.search(r'<meta[^>]+name=["\']source-url["\'][^>]+content=["\'](.*?)["\']', html, re.IGNORECASE)
    if meta_match:
        match = re.search(r"place\.map\.kakao\.com/(\d+)", meta_match.group(1))
        if match:
            return match.group(1)

    if source_url:
        match = re.search(r"place\.map\.kakao\.com/(\d+)", source_url)
        if match:
            return match.group(1)
        match = re.search(r"kakaomap_(\d+)\.html", source_url)
        if match:
            return match.group(1)

    match = re.search(r'"placeId"\s*:\s*"(\d+)"', html)
    if match:
        return match.group(1)

    return ""


def extract_json_reviews(
    html: str,
    place_name: str,
    place_id: str,
    source_url: str,
    source_note: str,
) -> list[RawReviewRecord]:
    records: list[RawReviewRecord] = []
    script_blocks = re.findall(r"<script[^>]*>(.*?)</script>", html, re.IGNORECASE | re.DOTALL)

    for block in script_blocks:
        lowered = block.lower()
        if "review" not in lowered and "comment" not in lowered:
            continue

        nested_list_match = re.search(
            r'"(?:reviews|review|comments|comment|list|data)"\s*:\s*(\[[^\]]*\])',
            block,
            re.IGNORECASE | re.DOTALL,
        )
        if nested_list_match:
            try:
                payload = json.loads(nested_list_match.group(1))
            except json.JSONDecodeError:
                payload = None
            if payload is not None:
                for review in iter_review_dicts(payload):
                    text = clean_html_text(
                        str(
                            review.get("comment")
                            or review.get("contents")
                            or review.get("review")
                            or review.get("reviewText")
                            or review.get("content")
                            or ""
                        )
                    )
                    if len(text) < 2:
                        continue

                    review_id = str(
                        review.get("id")
                        or review.get("commentid")
                        or review.get("reviewId")
                        or review.get("commentId")
                        or f"km_{place_id or 'unknown'}_{len(records) + 1:04d}"
                    ).strip()
                    rating = str(review.get("point") or review.get("rating") or review.get("score") or "").strip()
                    has_photo = int(bool(review.get("photoCount") or review.get("photo") or review.get("photos")))
                    note = build_source_note(source_note or "kakaomap_json", place_id, source_url)
                    records.append(
                        RawReviewRecord(
                            review_id=review_id,
                            platform=KAKAOMAP_PLATFORM,
                            store_or_product_name=place_name,
                            review_text_raw=text,
                            rating=rating,
                            has_photo=has_photo,
                            source_note=note,
                        )
                    )

        for payload in find_json_candidates(block):
            for review in iter_review_dicts(payload):
                text = clean_html_text(
                    str(
                        review.get("comment")
                        or review.get("contents")
                        or review.get("review")
                        or review.get("reviewText")
                        or review.get("content")
                        or ""
                    )
                )
                if len(text) < 2:
                    continue

                review_id = str(
                    review.get("id")
                    or review.get("commentid")
                    or review.get("reviewId")
                    or review.get("commentId")
                    or f"km_{place_id or 'unknown'}_{len(records) + 1:04d}"
                ).strip()
                rating = str(review.get("point") or review.get("rating") or review.get("score") or "").strip()
                has_photo = int(bool(review.get("photoCount") or review.get("photo") or review.get("photos")))
                note = build_source_note(source_note or "kakaomap_json", place_id, source_url)
                records.append(
                    RawReviewRecord(
                        review_id=review_id,
                        platform=KAKAOMAP_PLATFORM,
                        store_or_product_name=place_name,
                        review_text_raw=text,
                        rating=rating,
                        has_photo=has_photo,
                        source_note=note,
                    )
                )

    return records


def extract_dom_reviews(
    html: str,
    place_name: str,
    place_id: str,
    source_url: str,
    source_note: str,
) -> list[RawReviewRecord]:
    detail_records = extract_detail_dom_reviews(html, place_name, place_id, source_url, source_note)
    if detail_records:
        return detail_records

    records: list[RawReviewRecord] = []
    node_pattern = re.compile(
        r"<(?P<tag>li|div|article)(?P<attrs>[^>]*)>(?P<body>.*?)</(?P=tag)>",
        re.IGNORECASE | re.DOTALL,
    )

    for index, match in enumerate(node_pattern.finditer(html), start=1):
        node_html = match.group(0)
        attrs = match.group("attrs")
        class_attr = extract_attr(attrs, "class")
        if "review" not in class_attr.lower() and "comment" not in class_attr.lower():
            continue

        text = extract_dom_review_text(node_html)
        if len(text) < 2:
            continue

        review_id = (
            extract_attr(attrs, "data-review-id")
            or extract_attr(attrs, "data-comment-id")
            or f"km_{place_id or 'unknown'}_{index:04d}"
        )
        rating = extract_first_match(
            node_html,
            [
                r'data-rating=["\'](.*?)["\']',
                r'data-score=["\'](.*?)["\']',
                r'<span[^>]*class=["\'][^"\']*score[^"\']*["\'][^>]*>(.*?)</span>',
            ],
        )
        has_photo = int("<img" in node_html.lower())
        note = build_source_note(source_note or "kakaomap_dom", place_id, source_url)
        records.append(
            RawReviewRecord(
                review_id=review_id,
                platform=KAKAOMAP_PLATFORM,
                store_or_product_name=place_name,
                review_text_raw=text,
                rating=rating,
                has_photo=has_photo,
                source_note=note,
            )
        )

    return records


def extract_detail_dom_reviews(
    html: str,
    place_name: str,
    place_id: str,
    source_url: str,
    source_note: str,
) -> list[RawReviewRecord]:
    records: list[RawReviewRecord] = []
    review_marker = '<li class=""><div class="inner_review">'
    chunks = html.split(review_marker)

    for index, chunk in enumerate(chunks[1:], start=1):
        node_html = review_marker + chunk
        text = extract_first_match(
            node_html,
            [
                r'<p[^>]*class=["\'][^"\']*desc_review[^"\']*["\'][^>]*>(.*?)</p>',
            ],
        )
        if len(text) < 2:
            continue

        reviewer_name = extract_first_match(
            node_html,
            [
                r'<span[^>]*class=["\'][^"\']*name_user[^"\']*["\'][^>]*>(.*?)</span>',
            ],
        )
        review_date = extract_first_match(
            node_html,
            [
                r'<span[^>]*class=["\'][^"\']*txt_date[^"\']*["\'][^>]*>(.*?)</span>',
            ],
        )
        rating = str(len(re.findall(r'figure_star on', node_html, re.IGNORECASE)))
        has_photo = int('wrap_photo' in node_html and '<img' in node_html.lower())
        review_id = build_dom_review_id(place_id, reviewer_name, review_date, text, index)
        note = build_source_note(source_note or "kakaomap_dom_detail", place_id, source_url)
        records.append(
            RawReviewRecord(
                review_id=review_id,
                platform=KAKAOMAP_PLATFORM,
                store_or_product_name=place_name,
                review_text_raw=text,
                rating=rating,
                has_photo=has_photo,
                source_note=note,
            )
        )

    return records


def find_json_candidates(raw_text: str) -> list[object]:
    candidates: list[object] = []
    for match in re.finditer(r"(\[[^\]]*\])", raw_text, flags=re.DOTALL):
        fragment = match.group(1)
        try:
            payload = json.loads(fragment)
        except json.JSONDecodeError:
            continue
        candidates.append(payload)
    return candidates


def iter_review_dicts(payload: object) -> list[dict]:
    reviews: list[dict] = []
    if isinstance(payload, dict):
        keys = ["review", "reviews", "comment", "comments", "list", "data"]
        for key in keys:
            value = payload.get(key)
            if isinstance(value, list):
                reviews.extend(item for item in value if isinstance(item, dict))
        if any(key in payload for key in ["comment", "contents", "reviewText", "review"]):
            reviews.append(payload)
    elif isinstance(payload, list):
        reviews.extend(item for item in payload if isinstance(item, dict))
    return reviews


def extract_dom_review_text(node_html: str) -> str:
    patterns = [
        r'<p[^>]*class=["\'][^"\']*txt_comment[^"\']*["\'][^>]*>(.*?)</p>',
        r'<div[^>]*class=["\'][^"\']*comment[^"\']*["\'][^>]*>(.*?)</div>',
        r'<span[^>]*class=["\'][^"\']*txt_comment[^"\']*["\'][^>]*>(.*?)</span>',
        r"<p[^>]*>(.*?)</p>",
    ]
    for pattern in patterns:
        text = extract_first_match(node_html, [pattern])
        if len(text) >= 2:
            return text
    return ""


def extract_first_match(html: str, patterns: list[str]) -> str:
    for pattern in patterns:
        match = re.search(pattern, html, re.IGNORECASE | re.DOTALL)
        if match:
            text = clean_html_text(match.group(1))
            if text:
                return text
    return ""


def extract_attr(html_fragment: str, attr_name: str) -> str:
    match = re.search(rf'{attr_name}=["\'](.*?)["\']', html_fragment, re.IGNORECASE)
    return match.group(1).strip() if match else ""


def clean_html_text(text: str) -> str:
    without_tags = re.sub(r"<[^>]+>", " ", text)
    without_scripts = re.sub(r"\s+", " ", unescape(without_tags))
    return without_scripts.strip()


def build_source_note(source_note: str, place_id: str, source_url: str) -> str:
    parts = [source_note]
    if place_id:
        parts.append(f"place_id={place_id}")
    if source_url:
        parts.append(f"url={source_url}")
    return "|".join(part for part in parts if part)


def dedupe_records(records: list[RawReviewRecord]) -> list[RawReviewRecord]:
    deduped: list[RawReviewRecord] = []
    seen_keys: set[tuple[str, str]] = set()
    for record in records:
        key = (record.review_id, record.review_text_raw)
        if key in seen_keys:
            continue
        seen_keys.add(key)
        deduped.append(record)
    return deduped


def build_dom_review_id(place_id: str, reviewer_name: str, review_date: str, text: str, index: int) -> str:
    seed = "|".join(
        [
            place_id or "unknown",
            reviewer_name.strip(),
            review_date.strip(),
            " ".join(text.split())[:80],
        ]
    )
    compact = re.sub(r"[^0-9A-Za-z가-힣]+", "-", seed).strip("-")
    if compact:
        return f"km_{compact[:120]}"
    return f"km_{place_id or 'unknown'}_{index:04d}"
