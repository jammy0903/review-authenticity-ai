import json
from pathlib import Path

import pandas as pd

from src.config import OUTPUT_DIR

METRICS_OUTPUT_PATH = OUTPUT_DIR / "metrics" / "baseline_metrics.json"
ERRORS_OUTPUT_PATH = OUTPUT_DIR / "metrics" / "misclassified_reviews.csv"


def save_metrics(metrics: dict, confusion_matrix: list[list[int]], output_path: Path = METRICS_OUTPUT_PATH) -> None:
    """Save evaluation metrics and confusion matrix as JSON."""
    payload = {
        "metrics": metrics,
        "confusion_matrix": confusion_matrix,
    }
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def save_misclassified_reviews(dataframe: pd.DataFrame, output_path: Path = ERRORS_OUTPUT_PATH) -> None:
    """Save misclassified review rows as CSV."""
    dataframe.to_csv(output_path, index=False)
