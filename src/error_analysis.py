import pandas as pd


LABEL_NAME_MAP = {
    0: "genuine",
    1: "promotion",
}


def build_error_analysis_frame(x_test: pd.Series, y_test: pd.Series, predictions) -> pd.DataFrame:
    """Return a dataframe that compares true labels and predicted labels."""
    analysis_frame = pd.DataFrame(
        {
            "review_text": x_test.reset_index(drop=True),
            "true_label": y_test.reset_index(drop=True),
            "predicted_label": pd.Series(predictions),
        }
    )

    analysis_frame["true_label_name"] = analysis_frame["true_label"].map(LABEL_NAME_MAP)
    analysis_frame["predicted_label_name"] = analysis_frame["predicted_label"].map(LABEL_NAME_MAP)
    analysis_frame["is_error"] = analysis_frame["true_label"] != analysis_frame["predicted_label"]

    return analysis_frame


def extract_misclassified_reviews(analysis_frame: pd.DataFrame) -> pd.DataFrame:
    """Filter the analysis frame to only misclassified reviews."""
    return analysis_frame[analysis_frame["is_error"]].copy()
