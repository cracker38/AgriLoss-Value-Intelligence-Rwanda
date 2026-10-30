from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    balanced_accuracy_score,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedGroupKFold, cross_val_predict
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from scripts.dashboard_data import ROOT, load_production_data


MODEL_PATH = ROOT / "artifacts" / "loss_classifier.joblib"
METRICS_PATH = ROOT / "artifacts" / "loss_model_metrics.json"
PUBLIC_MODEL_CARD_PATH = ROOT / "public_data" / "model_card.json"
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
    frame = frame.loc[frame["s2q39"].ge(0)].copy()
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
                        (
                            "encode",
                            OneHotEncoder(
                                handle_unknown="ignore", sparse_output=False
                            ),
                        ),
                    ]
                ),
                list(CATEGORICAL_FEATURES),
            ),
            (
                "numeric",
                SimpleImputer(strategy="median"),
                list(NUMERIC_FEATURES),
            ),
        ]
    )
    return Pipeline(
        steps=[
            ("preprocess", preprocessing),
            (
                "classifier",
                HistGradientBoostingClassifier(
                    max_iter=120,
                    learning_rate=0.08,
                    max_leaf_nodes=15,
                    l2_regularization=2.0,
                    class_weight="balanced",
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


def _season_holdout_evaluation(
    features: pd.DataFrame, target: pd.Series, groups: pd.Series
) -> dict[str, Any]:
    """Evaluate an A-to-B retrospective holdout with repeated plots kept out of training."""
    season = features["season"].astype("string")
    train_season_mask = season.eq("A")
    test_mask = season.eq("B")
    repeated_test_groups = set(groups.loc[test_mask].unique())
    repeated_groups = set(groups.loc[train_season_mask].unique()).intersection(
        repeated_test_groups
    )
    train_mask = train_season_mask & ~groups.isin(repeated_test_groups)

    if not train_mask.any() or not test_mask.any():
        raise ValueError("Season A training and Season B holdout records are required")
    if target.loc[train_mask].nunique() != 2 or target.loc[test_mask].nunique() != 2:
        raise ValueError("Both target classes must appear in the Season A and B holdout data")
    if set(groups.loc[train_mask]).intersection(groups.loc[test_mask]):
        raise ValueError("A plot group appears in both the season training and holdout data")

    classifier = build_classifier()
    classifier.fit(features.loc[train_mask], target.loc[train_mask])
    probabilities = classifier.predict_proba(features.loc[test_mask])[:, 1]
    predictions = (probabilities >= 0.5).astype("int8")
    metrics = _classification_metrics(target.loc[test_mask], predictions, probabilities)

    baseline_predictions = np.zeros(int(test_mask.sum()), dtype="int8")
    baseline_metrics = _classification_metrics(
        target.loc[test_mask],
        baseline_predictions,
        np.full(int(test_mask.sum()), float(target.loc[train_mask].mean())),
    )
    return {
        "training_season": "A",
        "holdout_season": "B",
        "rows_trained": int(train_mask.sum()),
        "rows_evaluated": int(test_mask.sum()),
        "training_plot_groups": int(groups.loc[train_mask].nunique()),
        "holdout_plot_groups": int(groups.loc[test_mask].nunique()),
        "repeated_plot_groups_removed_from_training": len(repeated_groups),
        "positive_prevalence": float(target.loc[test_mask].mean()),
        "threshold": 0.5,
        "metrics": metrics,
        "always_negative_baseline": baseline_metrics,
        "interpretation": (
            "Retrospective cross-season classification of the same survey response, "
            "not a forecast of a future-period loss outcome."
        ),
    }


def choose_operating_threshold(target: pd.Series, probabilities: np.ndarray) -> dict[str, Any]:
    """Pick a cutoff by maximum F1 on out-of-fold scores. 0.5 is kept for comparison."""
    probabilities = np.asarray(probabilities, dtype=float)
    precision, recall, thresholds = precision_recall_curve(target, probabilities)
    if thresholds.size == 0:
        return {
            "selection_rule": "Maximum F1 on out-of-fold predictions",
            "threshold": 0.5,
            "f1": 0.0,
            "precision": 0.0,
            "recall": 0.0,
        }
    denom = precision[:-1] + recall[:-1]
    f1 = np.divide(
        2 * precision[:-1] * recall[:-1],
        denom,
        out=np.zeros_like(thresholds, dtype=float),
        where=denom > 0,
    )
    index = int(np.argmax(f1))
    return {
        "selection_rule": "Maximum F1 on out-of-fold predictions",
        "threshold": float(thresholds[index]),
        "f1": float(f1[index]),
        "precision": float(precision[index]),
        "recall": float(recall[index]),
    }


def _crop_group_metrics(
    features: pd.DataFrame,
    target: pd.Series,
    probabilities: np.ndarray,
    threshold: float,
    minimum_records: int = 400,
    minimum_positives: int = 30,
) -> list[dict[str, Any]]:
    """Grouped out-of-fold skill by crop. Never a farmer score."""
    rows: list[dict[str, Any]] = []
    crop_values = features["s2q4"].astype("string").to_numpy()
    labels = target.to_numpy()
    for name in pd.unique(crop_values):
        mask = crop_values == name
        group_labels = labels[mask]
        if mask.sum() < minimum_records or int(group_labels.sum()) < minimum_positives:
            continue
        if np.unique(group_labels).size != 2:
            continue
        scores = probabilities[mask]
        predictions = (scores >= threshold).astype("int8")
        try:
            auc = float(roc_auc_score(group_labels, scores))
        except ValueError:
            continue
        rows.append(
            {
                "crop": str(name),
                "records": int(mask.sum()),
                "positive_rows": int(group_labels.sum()),
                "roc_auc": round(auc, 4),
                "recall": round(float(recall_score(group_labels, predictions, zero_division=0)), 4),
                "average_precision": round(float(average_precision_score(group_labels, scores)), 4),
            }
        )
    rows.sort(key=lambda item: item["records"], reverse=True)
    return rows


def _top_feature_importances(classifier: Pipeline, limit: int = 12) -> list[dict[str, Any]]:
    model = classifier.named_steps["classifier"]
    if not hasattr(model, "feature_importances_"):
        return []
    preprocess = classifier.named_steps["preprocess"]
    encoder = preprocess.named_transformers_["categorical"].named_steps["encode"]
    names = list(encoder.get_feature_names_out(list(CATEGORICAL_FEATURES))) + list(
        NUMERIC_FEATURES
    )
    importances = model.feature_importances_
    if len(names) != len(importances):
        return []
    ranked = sorted(zip(names, importances), key=lambda item: item[1], reverse=True)[:limit]
    return [{"feature": name, "importance": float(value)} for name, value in ranked]


def export_public_model_card(result: dict[str, Any]) -> dict[str, Any]:
    """Write a respondent-free methods card for the public website."""
    operating = result.get("operating_point") or {"threshold": result.get("threshold", 0.5)}
    metrics = result["metrics"]
    baseline = result["majority_class_baseline"]
    card = {
        "schema_version": 1,
        "public_safe": True,
        "title": "Exploratory reported-loss classifier",
        "model": result.get("model"),
        "status": "retrospective research; not an operational alert or farmer score",
        "target": result.get("target_definition"),
        "training": {
            "seasons": result.get("training_seasons"),
            "season_c_excluded": result.get("season_c_excluded"),
            "rows_evaluated": result.get("rows_evaluated"),
            "positive_rows": result.get("positive_rows"),
            "negative_rows": result.get("negative_rows"),
            "positive_prevalence": round(float(result.get("positive_prevalence") or 0), 4),
            "plot_groups": result.get("groups"),
            "evaluation": result.get("evaluation"),
            "features": result.get("features"),
            "leakage_controls": result.get("leakage_controls"),
        },
        "operating_point": operating,
        "out_of_fold_metrics": {
            key: round(float(metrics[key]), 4)
            for key in (
                "accuracy",
                "precision",
                "recall",
                "f1",
                "balanced_accuracy",
                "roc_auc",
                "average_precision",
            )
        },
        "always_negative_baseline": {
            key: round(float(baseline[key]), 4)
            for key in (
                "accuracy",
                "precision",
                "recall",
                "f1",
                "balanced_accuracy",
                "roc_auc",
                "average_precision",
            )
        },
        "season_holdout": result.get("season_holdout_evaluation"),
        "crop_group_out_of_fold": result.get("crop_group_out_of_fold", []),
        "top_features": result.get("top_features", []),
        "reading_for_users": [
            "Accuracy is high because most records report zero. That does not mean the model finds most positive-loss records.",
            "Compare ROC AUC and average precision with the always-negative baseline. Ranking skill can exist even when recall at 0.5 is low.",
            "This is a same-survey classification, not a prediction of next season’s loss, and not a score of farmers.",
            "Crop pages use survey shares and a transparent follow-up signal, not this classifier’s individual probabilities.",
        ],
        "hackathon_use": "Shown only as grouped methods evidence for Track 1.",
    }
    PUBLIC_MODEL_CARD_PATH.parent.mkdir(parents=True, exist_ok=True)
    PUBLIC_MODEL_CARD_PATH.write_text(
        json.dumps(card, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return card


def train_and_evaluate() -> dict[str, Any]:
    data = load_production_data(("A", "B"))
    features, target, groups = prepare_model_data(data)
    season_holdout = _season_holdout_evaluation(features, target, groups)
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
    operating_point = choose_operating_threshold(target, probabilities)
    operating_threshold = float(operating_point["threshold"])
    predictions = (probabilities >= operating_threshold).astype("int8")
    model_metrics = _classification_metrics(target, predictions, probabilities)
    metrics_at_half = _classification_metrics(
        target, (probabilities >= 0.5).astype("int8"), probabilities
    )
    crop_group_out_of_fold = _crop_group_metrics(
        features, target, probabilities, operating_threshold
    )

    baseline_predictions = np.zeros(len(target), dtype="int8")
    baseline_metrics = _classification_metrics(
        target,
        baseline_predictions,
        np.full(len(target), float(target.mean())),
    )

    classifier.fit(features, target)
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(classifier, MODEL_PATH)
    top_features = _top_feature_importances(classifier)

    result: dict[str, Any] = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "model": "Histogram gradient boosting",
        "target": "s2q39 > 0: a positive reported-loss value, not a loss rate",
        "target_definition": {
            "source_field": "s2q39",
            "positive_class": "s2q39 > 0",
            "negative_class": "s2q39 == 0",
            "excluded_responses": "Blank, nonnumeric, negative, or missing plot-key responses.",
            "interpretation": "Presence of a positive reported value only; not loss severity, a loss rate, or a confirmed kilogram quantity.",
        },
        "target_unit": "Unconfirmed; do not interpret as kilograms",
        "training_seasons": ["A", "B"],
        "season_c_excluded": "Restricted sample; kept out of this exploratory model.",
        "evaluation": "5-fold stratified group cross-validation",
        "grouping": "Segment_ID + s2q1 plot key; plot groups do not cross folds.",
        "season_holdout_evaluation": season_holdout,
        "operating_point": operating_point,
        "threshold": operating_threshold,
        "metrics_at_0_5": metrics_at_half,
        "crop_group_out_of_fold": crop_group_out_of_fold,
        "top_features": top_features,
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
        "model_configuration": {
            "max_iter": 120,
            "learning_rate": 0.08,
            "max_leaf_nodes": 15,
            "l2_regularization": 2.0,
            "positive_class_weighting": "balanced",
        },
        "metrics": model_metrics,
        "majority_class_baseline": baseline_metrics,
        "model_file": str(MODEL_PATH.relative_to(ROOT)),
        "interpretation": (
            "Retrospective exploratory classification of the same-survey s2q39 response. "
            "The A-to-B holdout checks cross-season generalization but is not a future-period "
            "forecast, causal model, calibrated risk estimate, or basis for decisions about individuals."
        ),
    }
    METRICS_PATH.write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    export_public_model_card(result)
    return result


if __name__ == "__main__":
    metrics = train_and_evaluate()
    print(json.dumps(metrics, ensure_ascii=False, indent=2))
