from __future__ import annotations

import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.evaluate import evaluate_model
from src.train_baseline import run_baseline_training


def main() -> None:
    artifacts = run_baseline_training()
    evaluation = evaluate_model(
        artifacts["vectorizer"],
        artifacts["model"],
        artifacts["x_test"],
        artifacts["y_test"],
    )

    result = {
        "train_size": len(artifacts["x_train"]),
        "test_size": len(artifacts["x_test"]),
        "metrics": evaluation["metrics"],
        "confusion_matrix": evaluation["confusion_matrix"],
    }

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
