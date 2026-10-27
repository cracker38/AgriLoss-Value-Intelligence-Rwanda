from __future__ import annotations

import pandas as pd

from scripts.dashboard_data import filter_production_data
from scripts.train_loss_model import FEATURES, prepare_model_data


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
    assert groups.nunique() == 5


def test_plot_group_is_identical_across_seasons() -> None:
    data = _model_rows().iloc[:2].copy()
    data.loc[data.index[1], "season"] = "B"
    data.loc[data.index[1], "s2q1"] = "0"
    data.loc[data.index[1], "Segment_ID"] = "segment-0"

    _, _, groups = prepare_model_data(data)

    assert groups.iloc[0] == groups.iloc[1]


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
