from __future__ import annotations

import pandas as pd
import pytest
from sklearn.ensemble import HistGradientBoostingClassifier

from scripts.dashboard_data import filter_production_data, load_public_dashboard_data
from scripts.public_dashboard import _follow_up_brief, _named_crops
from scripts.train_loss_model import (
    FEATURES,
    _grouped_cv_splits,
    build_classifier,
    prepare_model_data,
)


def _model_rows() -> pd.DataFrame:
    rows = []
    for index in range(10):
        rows.append(
            {
                "season": "A" if index % 2 == 0 else "B",
                "s1q1": "East",
                "s1q2": "District",
                "s1q3": "Area frame",
                "s1q8": "Female",
                "s2q4": "Maize",
                "CropCategory": "Cereal",
                "s2q2": "1.5",
                "s2q39": "4" if index % 2 else "0",
                "Segment_ID": f"segment-{index // 2}",
                "s2q1": str(index % 2),
                "id": str(index),
            }
        )
    rows.append(
        {
            "season": "A",
            "s1q1": "East",
            "s1q2": "District",
            "s1q3": "Area frame",
            "s1q8": "Female",
            "s2q4": "Maize",
            "CropCategory": "Cereal",
            "s2q2": "1.5",
            "s2q39": "",
            "Segment_ID": "segment-missing",
            "s2q1": "1",
            "id": "missing-target",
        }
    )
    return pd.DataFrame(rows)


def test_model_target_excludes_missing_values_and_identifiers_from_features() -> None:
    features, target, groups = prepare_model_data(_model_rows())

    assert len(features) == 10
    assert set(target.unique()) == {0, 1}
    assert set(features.columns) == set(FEATURES)
    assert "id" not in features
    assert "Segment_ID" not in features
    assert "s2q39" not in features
    assert groups.nunique() == 10


def test_plot_group_is_identical_across_seasons() -> None:
    data = _model_rows().iloc[:2].copy()
    data.loc[data.index[1], "season"] = "B"
    data.loc[data.index[1], "s2q1"] = "0"
    data.loc[data.index[1], "Segment_ID"] = "segment-0"

    _, _, groups = prepare_model_data(data)

    assert groups.iloc[0] == groups.iloc[1]


def test_plot_group_key_does_not_collide_when_values_contain_separator() -> None:
    data = _model_rows().iloc[:2].copy()
    data.loc[data.index[0], ["Segment_ID", "s2q1"]] = ["segment::a", "b"]
    data.loc[data.index[1], ["Segment_ID", "s2q1"]] = ["segment", "a::b"]

    _, _, groups = prepare_model_data(data)

    assert groups.iloc[0] != groups.iloc[1]


def test_grouped_cross_validation_checks_fold_count_before_training() -> None:
    features, target, groups = prepare_model_data(_model_rows().iloc[:2])

    with pytest.raises(ValueError, match="At least 5 distinct plot groups"):
        _grouped_cv_splits(features, target, groups)


def test_classifier_uses_dense_categorical_inputs_for_gradient_boosting() -> None:
    classifier = build_classifier()
    categorical_pipeline = classifier.named_steps["preprocess"].transformers[0][1]

    assert isinstance(classifier.named_steps["classifier"], HistGradientBoostingClassifier)
    assert categorical_pipeline.named_steps["encode"].sparse_output is False


def test_named_crops_exclude_pooled_groups_and_tag_nst2_priority() -> None:
    crops = pd.DataFrame(
        [
            {
                "crop": "Maize",
                "records": 200,
                "loss_reported_records": 180,
                "loss_missing_records": 20,
                "positive_reported_loss_records": 18,
                "positive_reported_loss_share": 0.1,
                "median_reported_harvest_kg": 46,
                "harvest_reported_records": 180,
            },
            {
                "crop": "Other or unreported crops (pooled)",
                "records": 200,
                "loss_reported_records": 180,
                "loss_missing_records": 20,
                "positive_reported_loss_records": 18,
                "positive_reported_loss_share": 0.1,
                "median_reported_harvest_kg": 10,
                "harvest_reported_records": 180,
            },
        ]
    )

    named = _named_crops(crops)

    assert list(named["crop"]) == ["Maize"]
    assert bool(named.iloc[0]["is_priority_crop"]) is True


def test_storage_brief_states_limits_and_next_fields() -> None:
    crop_row = pd.Series(
        {
            "crop": "Maize",
            "records": 200,
            "loss_reported_records": 180,
            "loss_missing_records": 20,
            "positive_reported_loss_records": 18,
            "positive_reported_loss_share": 0.1,
            "loss_missing_share": 0.1,
            "median_reported_harvest_kg": 46,
            "harvest_reported_records": 180,
            "is_priority_crop": True,
        }
    )

    brief = _follow_up_brief(
        crop_row,
        "Crops with the highest share of positive loss reports",
        "provisional",
        "storage",
    )

    assert "not a national post-harvest loss rate" in brief
    assert "s2q36" in brief
    assert "Maize" in brief


def test_public_aggregates_file_loads() -> None:
    payload = load_public_dashboard_data()

    assert payload["schema_version"] == 1
    assert "by_crop" in payload
    assert payload["overall"]["records"] > 0


def test_dashboard_filters_only_selected_season_province_and_crop() -> None:
    data = pd.DataFrame(
        [
            {"season": "A", "s1q1": "East", "s2q4": "Maize"},
            {"season": "A", "s1q1": "West", "s2q4": "Maize"},
            {"season": "B", "s1q1": "East", "s2q4": "Beans"},
        ]
    )

    result = filter_production_data(
        data, seasons=["A"], provinces=["East"], crops=["Maize"]
    )

    assert result.to_dict("records") == [
        {"season": "A", "s1q1": "East", "s2q4": "Maize"}
    ]
