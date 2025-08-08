"""Test visualization functions."""

import pandas as pd
import pytest

from modules.viz import create_delta_heatmap, line_chart


def test_line_chart():
    """Test line chart creation."""
    df = pd.DataFrame({"year": [2020, 2021, 2022], "sales": [100, 150, 200]})
    fig = line_chart(df, "sales")
    assert fig is not None


def test_line_chart_empty_df():
    """Test line chart with empty dataframe."""
    df = pd.DataFrame()
    fig = line_chart(df, "nonexistent")
    assert fig is not None


def test_create_delta_heatmap():
    """Test delta heatmap creation."""
    group1_data = {f: 0.1 * i for i, f in enumerate("abcdefgh")}
    group2_data = {f: 0.05 * i for i, f in enumerate("abcdefgh")}

    fig = create_delta_heatmap(
        group1_data, group2_data, title="Test Heatmap", group1_name="Group 1", group2_name="Group 2"
    )

    assert fig is not None
    assert "Test Heatmap" in fig.layout.title.text
