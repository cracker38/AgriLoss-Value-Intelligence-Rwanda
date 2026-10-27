from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    balanced_accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedGroupKFold, cross_val_predict
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from scripts.dashboard_data import ROOT, load_production_data


MODEL_PATH = ROOT / "artifacts" / "loss_classifier.joblib"
METRICS_PATH = ROOT / "artifacts" / "loss_model_metrics.json"
CATEGORICAL_FEATURES = (
    "season",
    "s1q1",
    "s1q2",
    "s1q3",
    "s1q8",
    "s2q4",
    "CropCategory",
)
NUMERIC_FEATURES = ("s2q2",)
FEATURES = (*CATEGORICAL_FEATURES, *NUMERIC_FEATURES)
TARGET = "reported_positive_loss"
RANDOM_STATE = 2024
FOLDS = 5


def prepare_model_data(data: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series, pd.Series]:
    """Create an exploratory positive-loss target and grouped split keys."""
    required = {*FEATURES, "s2q39", "Segment_ID", "s2q1"}
    missing = required.difference(data.columns)
    if missing:
        raise ValueError(f"Production data is missing required fields: {sorted(missing)}")

    frame = data.loc[:, [*FEATURES, "s2q39", "Segment_ID", "s2q1"]].copy()
    frame["s2q39"] = pd.to_numeric(frame["s2q39"], errors="coerce")
    frame = frame.dropna(subset=["s2q39", "Segment_ID", "s2q1"])
    target = frame["s2q39"].gt(0).astype("int8")

    plot_keys = pd.MultiIndex.from_frame(
        frame[["Segment_ID", "s2q1"]].astype(str)
    )
    groups = pd.Series(
        pd.factorize(plot_keys, sort=False)[0],
        index=frame.index,
        name="plot_group",
    )
    features = frame.loc[:, FEATURES].copy()
    if target.nunique() != 2:
        raise ValueError("Both zero and positive reported-loss records are required")
    return features, target, groups


def _grouped_cv_splits(
    features: pd.DataFrame, target: pd.Series, groups: pd.Series
) -> list[tuple[np.ndarray, np.ndarray]]:
    if groups.nunique() < FOLDS:
        raise ValueError(f"At least {FOLDS} distinct plot groups are required")

    splitter = StratifiedGroupKFold(
        n_splits=FOLDS, shuffle=True, random_state=RANDOM_STATE
    )
    splits = list(splitter.split(features, target, groups))
    for fold_number, (train_indices, test_indices) in enumerate(splits, start=1):
        if (
            target.iloc[train_indices].nunique() != 2
            or target.iloc[test_indices].nunique() != 2
        ):
            raise ValueError(
                f"Both target classes must appear in the training and test data "
                f"for every fold; fold {fold_number} does not meet this requirement"
            )
    return splits


def build_classifier() -> Pipeline:
    preprocessing = ColumnTransformer(
        transformers=[
            (
                "categorical",
                Pipeline(
                    steps=[
                        ("impute", SimpleImputer(strategy="most_frequent")),
                        ("encode", OneHotEncoder(handle_unknown="ignore")),
                    ]
                ),
                list(CATEGORICAL_FEATURES),
            ),
            (
                "numeric",
                Pipeline(
                    steps=[
                        ("impute", SimpleImputer(strategy="median")),
                        ("scale", StandardScaler()),
                    ]
                ),
                list(NUMERIC_FEATURES),
            ),
        ]
    )
    return Pipeline(
        steps=[
            ("preprocess", preprocessing),
            (
                "classifier",
                LogisticRegression(
                    class_weight="balanced",
                    max_iter=1000,
                    random_state=RANDOM_STATE,
                ),
            ),
        ]
    )


def _classification_metrics(
    target: pd.Series, predictions: np.ndarray, probabilities: np.ndarray
) -> dict[str, Any]:
    matrix = confusion_matrix(target, predictions, labels=[0, 1])
    return {
        "accuracy": float(accuracy_score(target, predictions)),
        "precision": float(precision_score(target, predictions, zero_division=0)),
        "recall": float(recall_score(target, predictions, zero_division=0)),
        "f1": float(f1_score(target, predictions, zero_division=0)),
        "balanced_accuracy": float(balanced_accuracy_score(target, predictions)),
        "roc_auc": float(roc_auc_score(target, probabilities)),
        "average_precision": float(average_precision_score(target, probabilities)),
        "confusion_matrix": {
            "true_negative": int(matrix[0, 0]),
            "false_positive": int(matrix[0, 1]),
            "false_negative": int(matrix[1, 0]),
            "true_positive": int(matrix[1, 1]),
        },
    }


def train_and_evaluate() -> dict[str, Any]:
    data = load_production_data(("A", "B"))
    features, target, groups = prepare_model_data(data)
    splits = _grouped_cv_splits(features, target, groups)
    classifier = build_classifier()
    probabilities = cross_val_predict(
        classifier,
        features,
        target,
        groups=groups,
        cv=splits,
        method="predict_proba",
        n_jobs=1,
    )[:, 1]
    predictions = (probabilities >= 0.5).astype("int8")
    model_metrics = _classification_metrics(target, predictions, probabilities)

    baseline_predictions = np.zeros(len(target), dtype="int8")
    baseline_metrics = _classification_metrics(
        target,
        baseline_predictions,
        np.full(len(target), float(target.mean())),
    )

    classifier.fit(features, target)
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(classifier, MODEL_PATH)

    result: dict[str, Any] = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "model": "Class-weighted logistic regression",
        "target": "s2q39 > 0: a positive reported-loss value, not a loss rate",
        "target_unit": "Unconfirmed; do not interpret as kilograms",
        "training_seasons": ["A", "B"],
        "season_c_excluded": "Restricted sample; kept out of this exploratory model.",
        "evaluation": "5-fold stratified group cross-validation",
        "grouping": "Segment_ID + s2q1 plot key; plot groups do not cross folds.",
        "threshold": 0.5,
        "rows_evaluated": int(len(target)),
        "positive_rows": int(target.sum()),
        "negative_rows": int((target == 0).sum()),
        "positive_prevalence": float(target.mean()),
        "groups": int(groups.nunique()),
        "excluded_missing_target_or_group_rows": int(len(data) - len(target)),
        "features": list(FEATURES),
        "leakage_controls": [
            "Excluded s2q39-derived and post-harvest fields s2q40-s2q50.",
            "Excluded row identifiers and grouping keys from model features.",
            "Survey weights are not applied; scores are not population estimates.",
        ],
        "metrics": model_metrics,
        "majority_class_baseline": baseline_metrics,
        "model_file": str(MODEL_PATH.relative_to(ROOT)),
        "interpretation": (
            "Retrospective exploratory classification of survey-reported records. "
            "It is not a prospective forecast, causal model, calibrated risk estimate, "
            "or a basis for decisions about individual farmers."
        ),
    }
    METRICS_PATH.write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return result


if __name__ == "__main__":
    metrics = train_and_evaluate()
    print(json.dumps(metrics, ensure_ascii=False, indent=2))
