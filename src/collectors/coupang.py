from __future__ import annotations

import json
import re
from html import unescape
from urllib.parse import parse_qs, urlparse

from src.collectors.base import RawReviewRecord


COUPANG_PLATFORM = "coupang"
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


def parse_coupang_reviews(html: str, source_url: str = "", source_note: str = "") -> list[RawReviewRecord]:
    product_name = extract_coupang_product_name(html)
    records = extract_coupang_html_reviews(html, product_name, source_note)

    if records:
        return records

    records = extract_coupang_modern_reviews(html, product_name, source_note)
    if records:
        return records

    return extract_coupang_jsonld_reviews(html, source_url, product_name, source_note)


def extract_coupang_product_name(html: str) -> str:
    meta_match = re.search(r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\'](.*?)["\']', html, re.IGNORECASE)
    if meta_match:
        return clean_html_text(meta_match.group(1))

    title_match = re.search(r"<title>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
    return clean_html_text(title_match.group(1)) if title_match else ""


def extract_coupang_html_reviews(
    html: str,
    product_name: str,
    source_note: str,
) -> list[RawReviewRecord]:
    records: list[RawReviewRecord] = []

    pattern = re.compile(
        r"<(?P<tag>article|div)(?P<attrs>[^>]*)>(?P<body>.*?)</(?P=tag)>",
        re.IGNORECASE | re.DOTALL,
    )
    for index, match in enumerate(pattern.finditer(html), start=1):
        node_html = match.group(0)
        class_attr = extract_attr(node_html, "class")
        class_tokens = class_attr.split()
        if "sdp-review__article__list" not in class_tokens:
            continue

        review_id = extract_attr(node_html, "data-review-id") or f"coupang_{index:04d}"
        text = extract_first_match(
            node_html,
            [
                r'<[^>]*class=["\'][^"\']*sdp-review__article__list__review__content[^"\']*["\'][^>]*>(.*?)</[^>]+>',
                r'<[^>]*class=["\'][^"\']*js_reviewArticleContent[^"\']*["\'][^>]*>(.*?)</[^>]+>',
                r'<[^>]*class=["\'][^"\']*review__content[^"\']*["\'][^>]*>(.*?)</[^>]+>',
            ],
        )
        if not text:
            continue

        rating = extract_first_match(
            node_html,
            [
                r'<[^>]*class=["\'][^"\']*js_reviewArticleRatingValue[^"\']*["\'][^>]*>(.*?)</[^>]+>',
                r'<[^>]*class=["\'][^"\']*star-orange[^"\']*["\'][^>]*>(.*?)</[^>]+>',
            ],
        )
        has_photo = int("attachment" in node_html or "<img" in node_html.lower())
        records.append(
            RawReviewRecord(
                review_id=review_id,
                platform=COUPANG_PLATFORM,
                store_or_product_name=product_name,
                review_text_raw=text,
                rating=rating,
                has_photo=has_photo,
                source_note=source_note or "coupang_html",
            )
        )

    return records


def extract_coupang_jsonld_reviews(
    html: str,
    source_url: str,
    product_name: str,
    source_note: str,
) -> list[RawReviewRecord]:
    records: list[RawReviewRecord] = []

    for raw_text in re.findall(r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', html, re.IGNORECASE | re.DOTALL):
        try:
            payload = json.loads(raw_text)
        except json.JSONDecodeError:
            continue

        for review in iter_review_objects(payload):
            text = str(review.get("reviewBody", "")).strip()
            if not text:
                continue

            review_id = build_review_id_from_url(source_url, len(records) + 1)
            rating_value = review.get("reviewRating", {}).get("ratingValue", "")
            records.append(
                RawReviewRecord(
                    review_id=review_id,
                    platform=COUPANG_PLATFORM,
                    store_or_product_name=product_name,
                    review_text_raw=text,
                    rating=str(rating_value),
                    has_photo=0,
                    source_note=source_note or "coupang_jsonld",
                )
            )

    return records


def extract_coupang_modern_reviews(
    html: str,
    product_name: str,
    source_note: str,
) -> list[RawReviewRecord]:
    records: list[RawReviewRecord] = []
    article_pattern = re.compile(r"<article\b[^>]*>(.*?)</article>", re.IGNORECASE | re.DOTALL)

    for index, match in enumerate(article_pattern.finditer(html), start=1):
        article_html = match.group(0)
        review_id = extract_attr(article_html, "data-review-id")
        if not review_id:
            continue

        text = extract_modern_review_text(article_html)
        if not text:
            continue

        rating = extract_modern_review_rating(article_html)
        has_photo = int("PRODUCTREVIEW" in article_html or article_html.lower().count("<img") >= 2)
        records.append(
            RawReviewRecord(
                review_id=review_id,
                platform=COUPANG_PLATFORM,
                store_or_product_name=product_name,
                review_text_raw=text,
                rating=rating,
                has_photo=has_photo,
                source_note=source_note or "coupang_modern_html",
            )
        )

    return records


def iter_review_objects(payload) -> list[dict]:
    if isinstance(payload, dict):
        if payload.get("@type") == "Review":
            return [payload]

        if isinstance(payload.get("review"), list):
            return [item for item in payload["review"] if isinstance(item, dict)]

        if isinstance(payload.get("@graph"), list):
            reviews: list[dict] = []
            for item in payload["@graph"]:
                reviews.extend(iter_review_objects(item))
            return reviews

    if isinstance(payload, list):
        reviews: list[dict] = []
        for item in payload:
            reviews.extend(iter_review_objects(item))
        return reviews

    return []


def build_review_id_from_url(source_url: str, index: int) -> str:
    product_id = ""
    if source_url:
        query = parse_qs(urlparse(source_url).query)
        product_id = query.get("productId", [""])[0]
        if not product_id:
            match = re.search(r"/vp/products/(\\d+)", source_url)
            if match:
                product_id = match.group(1)

    suffix = product_id or "unknown"
    return f"cp_{suffix}_{index:04d}"


def extract_first_match(html: str, patterns: list[str]) -> str:
    for pattern in patterns:
        match = re.search(pattern, html, re.IGNORECASE | re.DOTALL)
        if match:
            text = clean_html_text(match.group(1))
            if text:
                return text

    return ""


def extract_modern_review_text(article_html: str) -> str:
    helpful_index = article_html.find("js_reviewArticleHelpfulContainer")
    review_section = article_html[:helpful_index] if helpful_index != -1 else article_html

    candidates = []
    for match in re.finditer(r"<span\b[^>]*>(.*?)</span>", review_section, re.IGNORECASE | re.DOTALL):
        text = clean_html_text(match.group(1))
        if is_valid_review_text(text):
            candidates.append(text)

    if not candidates:
        for match in re.finditer(r"<div\b[^>]*>(.*?)</div>", review_section, re.IGNORECASE | re.DOTALL):
            text = clean_html_text(match.group(1))
            if is_valid_review_text(text):
                candidates.append(text)

    if not candidates:
        return ""

    return max(candidates, key=len)


def extract_modern_review_rating(article_html: str) -> str:
    full_stars = len(re.findall(r"twc-bg-full-star", article_html))
    half_stars = len(re.findall(r"twc-bg-half-star", article_html))
    if not full_stars and not half_stars:
        return ""

    return str(full_stars + 0.5 * half_stars)


def is_valid_review_text(text: str) -> bool:
    if len(text) < 20:
        return False

    excluded_phrases = {
        "도움이 됐어요",
        "신고하기",
        "착석감",
        "조립 난이도",
        "아주 쉬워요",
        "무난해요",
        "상품리뷰 운영원칙",
    }
    if any(phrase in text for phrase in excluded_phrases):
        return False

    return not any(pattern.fullmatch(text) for pattern in NON_REVIEW_PATTERNS)


def extract_attr(html: str, attr_name: str) -> str:
    match = re.search(rf'{attr_name}=["\'](.*?)["\']', html, re.IGNORECASE)
    return match.group(1).strip() if match else ""


def clean_html_text(text: str) -> str:
    without_tags = re.sub(r"<[^>]+>", " ", text)
    return " ".join(unescape(without_tags).split())
