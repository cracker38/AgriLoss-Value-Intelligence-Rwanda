from __future__ import annotations

import pandas as pd
import pytest
from sklearn.ensemble import HistGradientBoostingClassifier

from scripts.build_public_dashboard import _measure_summary
from scripts.dashboard_data import filter_production_data, load_public_dashboard_data
from scripts.public_dashboard import (
    STORAGE_LENSES,
    VALUE_LENSES,
    _follow_up_brief,
    _follow_up_checks,
    _named_crops,
    _rank_crop_review,
    _review_signal,
)


def _crop_summary(**overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "crop": "Maize",
        "records": 200,
        "loss_reported_records": 180,
        "loss_missing_records": 20,
        "positive_reported_loss_records": 18,
        "positive_reported_loss_share": 0.1,
        "median_reported_harvest_kg": 46,
        "harvest_reported_records": 180,
        "stored_reported_records": 180,
        "stored_missing_records": 20,
        "stored_positive_records": 20,
        "stored_positive_share": 0.111,
        "stored_median_positive_kg": 35,
        "storage_loss_reported_records": 180,
        "public_stored_positive_records": 0,
        "storage_loss_positive_records": 4,
        "storage_loss_positive_share": 0.022,
        "storage_loss_negative_records": 1,
        "transformed_reported_records": 180,
        "transformed_positive_records": 80,
        "transformed_positive_share": 0.44,
        "transformed_median_positive_kg": 60,
        "sold_reported_records": 180,
        "sold_positive_records": 90,
        "sold_positive_share": 0.5,
        "sold_median_positive_kg": 40,
        "sold_with_positive_price_records": 70,
        "sold_with_zero_price_records": 5,
        "sold_with_missing_price_records": 15,
    }
    row.update(overrides)
    return row
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
            _crop_summary(),
            _crop_summary(crop="Other or unreported crops (pooled)", stored_positive_share=0.1),
        ]
    )

    named = _named_crops(crops)

    assert list(named["crop"]) == ["Maize"]
    assert bool(named.iloc[0]["is_priority_crop"]) is True


def test_crop_review_sort_excludes_missing_values_and_breaks_ties_by_records() -> None:
    crops = pd.DataFrame(
        [
            _crop_summary(crop="Lower count", records=300, storage_loss_positive_share=0.05),
            _crop_summary(crop="Higher count", records=400, storage_loss_positive_share=0.05),
            _crop_summary(crop="Unavailable", records=500, storage_loss_positive_share=None),
        ]
    )

    ranked = _rank_crop_review(crops, "storage_loss_positive_share")

    assert list(ranked["crop"]) == ["Higher count", "Lower count"]


def test_review_signal_explains_rank_and_valid_denominator() -> None:
    signal = _review_signal(
        pd.Series(_crop_summary()),
        STORAGE_LENSES[0],
        "storage",
        rank=2,
        ranked_crops=8,
    )

    assert "ranks 2 of 8 named crop groups" in signal
    assert "20 of 180 valid answers" in signal
    assert "not an intervention ranking" in signal


def test_follow_up_checks_use_observed_quality_flags_and_local_condition() -> None:
    crop_row = pd.Series(
        _crop_summary(
            stored_missing_records=35,
            storage_loss_negative_records=2,
        )
    )

    checks = _follow_up_checks(crop_row, "storage", "Collection or transport")

    assert any("35 records are missing" in check for check in checks)
    assert any("2 negative storage-stage loss values" in check for check in checks)
    assert any("collection distances, transport costs" in check for check in checks)


def test_value_addition_checks_flag_sales_price_quality() -> None:
    checks = _follow_up_checks(
        pd.Series(_crop_summary()),
        "value",
        "Market access / prices",
    )

    assert any("5 zero-price responses" in check for check in checks)
    assert any("15 records with positive sales have no reported price" in check for check in checks)
    assert any("current buyer prices" in check for check in checks)


def test_storage_brief_states_limits_and_next_fields() -> None:
    crop_row = pd.Series(_crop_summary(is_priority_crop=True))

    brief = _follow_up_brief(
        crop_row,
        "Share of records with stored quantity (kg)",
        "provisional",
        "storage",
        province_context={
            "province": "East",
            "records": 1000,
            "stored_positive_share": 0.2,
        },
        local_condition="Storage capacity",
        local_notes="Inspect seasonal overflow.",
    )

    assert "not Rwanda’s national post-harvest loss rate" in brief
    assert "s2q36" in brief
    assert "Maize" in brief
    assert "Province values are a separate marginal summary" in brief
    assert "Inspect seasonal overflow." in brief
    assert "Compare the survey summary with verified local storage capacity" in brief


def test_measure_summary_keeps_blanks_missing_and_flags_negative_storage_loss() -> None:
    frame = pd.DataFrame(
        {
            "s2q21": [10] * 100,
            "s2q25": [0] * 90 + [20] * 10,
            "s2q26": [5] * 100,
            "s2q28": [100] * 99 + [0],
            "s2q36": [0] * 80 + [12] * 20,
            "s2q38": [0] * 100,
            "s2q39": [0] * 90 + [3] * 10,
            "s2q47": [0] * 97 + [8] * 2 + [-2],
        }
    )
    extra_missing = pd.DataFrame(
        {
            "s2q21": [None],
            "s2q25": [None],
            "s2q26": [None],
            "s2q28": [None],
            "s2q36": [None],
            "s2q38": [None],
            "s2q39": [None],
            "s2q47": [None],
        }
    )
    summary = _measure_summary(pd.concat([frame, extra_missing], ignore_index=True))

    assert summary["records"] == 101
    assert summary["stored_missing_records"] == 1
    assert summary["stored_positive_records"] == 20
    assert summary["storage_loss_negative_records"] == 1
    assert summary["transformed_positive_records"] == 10
    assert summary["sold_with_zero_price_records"] == 1


def test_public_aggregates_file_loads() -> None:
    payload = load_public_dashboard_data()

    assert payload["schema_version"] == 1
    assert "by_crop" in payload
    assert payload["overall"]["records"] > 0
    assert "stored_positive_share" in payload["overall"]
    assert "transformed_positive_share" in payload["overall"]


def test_released_aggregates_generate_a_ranked_value_follow_up_brief() -> None:
    payload = load_public_dashboard_data()
    crops = _rank_crop_review(
        _named_crops(pd.DataFrame(payload["by_crop"])),
        "sold_positive_share",
    )
    crop_row = crops.iloc[0]
    signal = _review_signal(
        crop_row,
        VALUE_LENSES[1],
        "value",
        rank=1,
        ranked_crops=len(crops),
    )

    brief = _follow_up_brief(
        crop_row,
        VALUE_LENSES[1],
        "provisional",
        "value",
        review_signal=signal,
        province_context=pd.DataFrame(payload["by_province"]).iloc[0].to_dict(),
        local_condition="Market access / prices",
    )

    assert "ranks 1 of" in brief
    assert "Market access / prices" in brief
    assert "Province values are a separate marginal summary" in brief
    assert "Recommended evidence checks" in brief


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
