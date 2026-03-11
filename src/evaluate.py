import pandas as pd
from sklearn.metrics import confusion_matrix, f1_score, precision_score, recall_score


METRIC_LABELS = [0, 1]


def predict_with_model(vectorizer, model, x_test: pd.Series):
    """Vectorize test text and return model predictions."""
    x_test_vectors = vectorizer.transform(x_test)
    return model.predict(x_test_vectors)


def calculate_classification_metrics(y_test: pd.Series, predictions) -> dict:
    """Calculate core classification metrics for the baseline model."""
    return {
        "f1": f1_score(y_test, predictions),
        "precision": precision_score(y_test, predictions),
        "recall": recall_score(y_test, predictions),
    }


def calculate_confusion_matrix(y_test: pd.Series, predictions) -> list[list[int]]:
    """Return confusion matrix as a plain nested list."""
    matrix = confusion_matrix(y_test, predictions, labels=METRIC_LABELS)
    return matrix.tolist()


def evaluate_model(vectorizer, model, x_test: pd.Series, y_test: pd.Series) -> dict:
    """Run prediction and return evaluation results."""
    predictions = predict_with_model(vectorizer, model, x_test)
    metrics = calculate_classification_metrics(y_test, predictions)
    matrix = calculate_confusion_matrix(y_test, predictions)

    return {
        "metrics": metrics,
        "confusion_matrix": matrix,
        "predictions": predictions,
    }
