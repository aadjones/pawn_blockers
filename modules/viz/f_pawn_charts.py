"""F-pawn fate visualization charts."""

from typing import Dict, List

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


def plot_f_pawn_fates_stacked(
    cohort1_fates: Dict[str, int], cohort2_fates: Dict[str, int], cohort1_name: str, cohort2_name: str
) -> None:
    """Create 100% stacked bar chart showing F-pawn fate distributions."""

    # Define meaningful labels and colors (ordered from most flexible to most blocked)
    # This order determines the stacking order - most blocked will appear at top of chart
    from collections import OrderedDict

    fate_info = OrderedDict(
        [
            ("never_blocked", {"label": "Never blocked", "color": "#2E8B57"}),  # Sea green - most flexible
            ("capture", {"label": "Capture", "color": "#2ca02c"}),  # Green - active play
            ("push_one", {"label": "Push one square", "color": "#1f77b4"}),  # Blue - stays flexible
            ("push_two", {"label": "Push two squares", "color": "#ff7f0e"}),  # Orange - commits heavily
            ("temporary_block", {"label": "Temporary block", "color": "#9467bd"}),  # Purple
            ("permanent_block", {"label": "Permanent block", "color": "#8c564b"}),  # Brown - most restrictive at top
        ]
    )

    # Calculate percentages
    total1 = sum(cohort1_fates.values()) or 1
    total2 = sum(cohort2_fates.values()) or 1

    fig = go.Figure()

    # Convert raw fates to simplified categories
    def simplify_fates(raw_fates):
        return {
            "never_blocked": raw_fates.get("never_blocked", 0),
            "push_one": raw_fates.get("push_f3", 0),
            "push_two": raw_fates.get("push_f4", 0),
            "capture": raw_fates.get("capture_e3", 0) + raw_fates.get("capture_g3", 0),
            "temporary_block": raw_fates.get("temporary_block", 0),
            "permanent_block": raw_fates.get("permanent_block", 0),
        }

    simplified_fates1 = simplify_fates(cohort1_fates)
    simplified_fates2 = simplify_fates(cohort2_fates)

    # Recalculate totals with simplified data
    total1 = sum(simplified_fates1.values()) or 1
    total2 = sum(simplified_fates2.values()) or 1

    # Add traces for each fate category
    for fate, info in fate_info.items():
        pct1 = 100 * simplified_fates1[fate] / total1
        pct2 = 100 * simplified_fates2[fate] / total2

        fig.add_trace(
            go.Bar(
                name=info["label"],
                x=[cohort1_name, cohort2_name],
                y=[pct1, pct2],
                marker_color=info["color"],
                text=[f"{pct1:.1f}%" if pct1 > 0 else "", f"{pct2:.1f}%" if pct2 > 0 else ""],
                textposition="inside",
                textfont=dict(color="white", size=12),
            )
        )

    fig.update_layout(
        title=f"F-pawn Fate Distribution (n={total1}, n={total2})",
        xaxis_title="Cohort",
        yaxis_title="Percentage (%)",
        barmode="stack",
        height=600,
        legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.02),
        yaxis=dict(range=[0, 100]),
    )

    st.plotly_chart(fig, use_container_width=True)


def plot_f_pawn_fates_bar(
    cohort1_fates: Dict[str, int], cohort2_fates: Dict[str, int], cohort1_name: str, cohort2_name: str
) -> None:
    """Create a comparative bar chart showing F-pawn fate distributions."""

    fate_labels = {
        "push_f3": "Push to f3",
        "push_f4": "Push to f4",
        "capture_e3": "Capture on e3",
        "capture_g3": "Capture on g3",
        "temporary_block": "Temporary block",
        "permanent_block": "Permanent block",
    }

    # Calculate percentages
    total1 = sum(cohort1_fates.values()) or 1
    total2 = sum(cohort2_fates.values()) or 1

    categories = []
    cohort1_pcts = []
    cohort2_pcts = []

    for fate in fate_labels:
        categories.append(fate_labels[fate])
        cohort1_pcts.append(100 * cohort1_fates[fate] / total1)
        cohort2_pcts.append(100 * cohort2_fates[fate] / total2)

    fig = go.Figure()

    fig.add_trace(go.Bar(name=cohort1_name, x=categories, y=cohort1_pcts, marker_color="#1f77b4"))

    fig.add_trace(go.Bar(name=cohort2_name, x=categories, y=cohort2_pcts, marker_color="#ff7f0e"))

    fig.update_layout(
        title="F-pawn Fate Distribution Comparison",
        xaxis_title="Fate Category",
        yaxis_title="Percentage (%)",
        barmode="group",
        height=500,
        xaxis={"tickangle": 45},
    )

    st.plotly_chart(fig, use_container_width=True)
