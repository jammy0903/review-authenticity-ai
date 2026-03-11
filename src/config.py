from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
LABELED_DATA_DIR = DATA_DIR / "labeled"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
OUTPUT_DIR = PROJECT_ROOT / "outputs"

DEFAULT_LABELED_FILE = LABELED_DATA_DIR / "coupang_multiproduct_labeled.csv"
DEFAULT_RAW_FILE = RAW_DATA_DIR / "raw_reviews.csv"
DEFAULT_COUPANG_URL_FILE = RAW_DATA_DIR / "coupang_seed_urls.txt"
DEFAULT_KAKAOMAP_URL_FILE = RAW_DATA_DIR / "kakaomap_place_urls.txt"
DEFAULT_KAKAOMAP_RAW_FILE = RAW_DATA_DIR / "kakaomap_reviews_raw.csv"
DEFAULT_KAKAOMAP_BLANK_FILE = LABELED_DATA_DIR / "kakaomap_reviews_blank.csv"
RANDOM_SEED = 42

RAW_REVIEW_COLUMNS = [
    "review_id",
    "platform",
    "store_or_product_name",
    "review_text_raw",
    "rating",
    "has_photo",
    "event_flag_raw",
    "reorder_count_raw",
    "collected_at",
    "source_note",
]

REQUIRED_LABELED_COLUMNS = [
    "review_id",
    "platform",
    "review_text_raw",
    "label",
    "label_reason",
]

CANONICAL_LABELS = {"genuine", "promotion", "uncertain"}
LABEL_ALIASES = {
    "genuine": "genuine",
    "promotion": "promotion",
    "uncertain": "uncertain",
    "informative": "genuine",
    "promotional": "promotion",
    "진심": "genuine",
    "리뷰": "promotion",
    "애매": "uncertain",
}
