from pathlib import Path

import pandas as pd

from src.config import CANONICAL_LABELS, DEFAULT_LABELED_FILE, LABEL_ALIASES, REQUIRED_LABELED_COLUMNS


def load_labeled_reviews(csv_path: Path | None = None) -> pd.DataFrame:
    """Load labeled reviews, normalize labels, and validate the dataset."""
    target_path = csv_path or DEFAULT_LABELED_FILE
    dataframe = pd.read_csv(target_path)

    validate_required_columns(dataframe, REQUIRED_LABELED_COLUMNS)
    dataframe = normalize_labels(dataframe)
    validate_labels(dataframe)

    return dataframe


def validate_required_columns(dataframe: pd.DataFrame, required_columns: list[str]) -> None:
    missing_columns = [column for column in required_columns if column not in dataframe.columns]
    if missing_columns:
        missing_text = ", ".join(missing_columns)
        raise ValueError(f"Missing required columns: {missing_text}")


def normalize_labels(dataframe: pd.DataFrame) -> pd.DataFrame:
    normalized = dataframe.copy()
    normalized["label"] = normalized["label"].apply(normalize_label_value)
    return normalized


def normalize_label_value(value) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip()
    return LABEL_ALIASES.get(text, text)


def validate_labels(dataframe: pd.DataFrame) -> None:
    unique_labels = set(dataframe["label"].dropna().unique())
    invalid_labels = sorted(label for label in unique_labels if label and label not in CANONICAL_LABELS)
    if invalid_labels:
        invalid_text = ", ".join(invalid_labels)
        raise ValueError(f"Invalid labels found: {invalid_text}")
