import pandas as pd


TEXT_COLUMN = "review_text_raw"
CLEAN_TEXT_COLUMN = "review_text"

#원본을 정제시키는. NaN은 ""으로
def normalize_review_text(text: str) -> str:
    """Normalize whitespace and return a clean review string."""
    if pd.isna(text):
        return ""

    normalized_text = str(text).replace("\n", " ").replace("\t", " ")
    return " ".join(normalized_text.split())


def preprocess_labeled_reviews(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Create a copy of the labeled dataframe with cleaned review text."""
    processed = dataframe.copy()
    processed[CLEAN_TEXT_COLUMN] = processed[TEXT_COLUMN].apply(normalize_review_text)
    return processed
