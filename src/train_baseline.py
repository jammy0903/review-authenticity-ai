import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split

from src.config import RANDOM_SEED
from src.data_loader import load_labeled_reviews
from src.preprocess import CLEAN_TEXT_COLUMN, preprocess_labeled_reviews


TEXT_LABEL_MAP = {
    "genuine": 0,
    "promotion": 1,
}


def prepare_training_data(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Filter uncertain rows and create binary labels for training."""
    filtered = dataframe[dataframe["label"].isin(TEXT_LABEL_MAP)].copy()
    filtered["label_binary"] = filtered["label"].map(TEXT_LABEL_MAP)
    return filtered


def split_training_data(dataframe: pd.DataFrame):
    """Split review text and labels into train and test sets."""
    features = dataframe[CLEAN_TEXT_COLUMN]
    targets = dataframe["label_binary"]

    return train_test_split(
        features,
        targets,
        test_size=0.2,
        random_state=RANDOM_SEED,
        stratify=targets,
    )


def train_baseline_model(x_train: pd.Series, y_train: pd.Series):
    """Train a TF-IDF + Logistic Regression baseline model."""
    vectorizer = TfidfVectorizer()
    x_train_vectors = vectorizer.fit_transform(x_train)

    model = LogisticRegression(random_state=RANDOM_SEED, max_iter=1000)
    model.fit(x_train_vectors, y_train)

    return vectorizer, model


def run_baseline_training() -> dict:
    """Run the full baseline training flow and return training artifacts."""
    raw_reviews = load_labeled_reviews()
    processed_reviews = preprocess_labeled_reviews(raw_reviews)
    training_reviews = prepare_training_data(processed_reviews)

    x_train, x_test, y_train, y_test = split_training_data(training_reviews)
    vectorizer, model = train_baseline_model(x_train, y_train)

    return {
        "vectorizer": vectorizer,
        "model": model,
        "x_train": x_train,
        "x_test": x_test,
        "y_train": y_train,
        "y_test": y_test,
    }
