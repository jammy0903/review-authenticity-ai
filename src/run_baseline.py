from pprint import pprint

from src.evaluate import evaluate_model
from src.error_analysis import build_error_analysis_frame, extract_misclassified_reviews
from src.save_results import save_metrics, save_misclassified_reviews
from src.train_baseline import run_baseline_training


def main() -> None:
    """Run baseline training, evaluation, error analysis, and save results."""
    training_result = run_baseline_training()

    evaluation_result = evaluate_model(
        vectorizer=training_result["vectorizer"],
        model=training_result["model"],
        x_test=training_result["x_test"],
        y_test=training_result["y_test"],
    )

    analysis_frame = build_error_analysis_frame(
        x_test=training_result["x_test"],
        y_test=training_result["y_test"],
        predictions=evaluation_result["predictions"],
    )
    misclassified_reviews = extract_misclassified_reviews(analysis_frame)

    save_metrics(
        metrics=evaluation_result["metrics"],
        confusion_matrix=evaluation_result["confusion_matrix"],
    )
    save_misclassified_reviews(misclassified_reviews)

    print("=== Metrics ===")
    pprint(evaluation_result["metrics"])
    print()

    print("=== Confusion Matrix ===")
    pprint(evaluation_result["confusion_matrix"])
    print()

    print("=== Misclassified Reviews ===")
    if misclassified_reviews.empty:
        print("No misclassified reviews found.")
    else:
        printable_columns = [
            "review_text",
            "true_label_name",
            "predicted_label_name",
        ]
        print(misclassified_reviews[printable_columns].to_string(index=False))

    print()
    print("Saved results:")
    print("- outputs/metrics/baseline_metrics.json")
    print("- outputs/metrics/misclassified_reviews.csv")


if __name__ == "__main__":
    main()
