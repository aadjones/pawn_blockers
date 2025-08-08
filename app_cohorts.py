#!/usr/bin/env python3
"""Cohort-focused Streamlit app for chess game analysis."""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from modules.cohorts import CohortManager
from modules.metrics import get_registry
from modules.viz import comparison_boxplot, create_simple_board_heatmap

# Configure page
st.set_page_config(page_title="Pawn Blockers - Cohort Analysis", page_icon="♟️", layout="wide")


# Initialize systems
@st.cache_resource
def get_cohort_manager():
    """Get cached cohort manager instance."""
    return CohortManager()


@st.cache_resource
def get_metric_registry():
    """Get cached metric registry."""
    return get_registry()


# Main app
def main():
    st.title("♟️ Pawn Blockers - Cohort Analysis")
    st.markdown("**Compare pawn blocking patterns between different cohorts**")

    # Initialize managers
    cohort_manager = get_cohort_manager()
    metric_registry = get_metric_registry()

    # Sidebar for cohort selection
    st.sidebar.title("🎯 Cohort Comparison")

    # Get available cohorts
    available_cohorts = cohort_manager.list_available_cohorts()
    cohort_options = {f"{c.id} ({c.name})": c.id for c in available_cohorts}

    if not cohort_options:
        st.error("No cohorts available. Run `python scripts/manage_cohorts.py process` to create cohorts.")
        return

    # Cohort selection with defaults
    default_cohort1 = None
    default_cohort2 = None

    # Set defaults if we have the expected cohorts
    cohort_ids = list(cohort_options.values())
    if "leela_odds" in cohort_ids:
        default_cohort1 = next(k for k, v in cohort_options.items() if v == "leela_odds")
    if "twic_strong" in cohort_ids:
        default_cohort2 = next(k for k, v in cohort_options.items() if v == "twic_strong")

    # If we don't have defaults, use first two available
    options_list = list(cohort_options.keys())
    if not default_cohort1 and options_list:
        default_cohort1 = options_list[0]
    if not default_cohort2 and len(options_list) > 1:
        default_cohort2 = options_list[1]
    elif not default_cohort2:
        default_cohort2 = default_cohort1

    cohort1_display = st.sidebar.selectbox(
        "Cohort A",
        options=list(cohort_options.keys()),
        index=options_list.index(default_cohort1) if default_cohort1 in options_list else 0,
        key="cohort1",
    )
    cohort2_display = st.sidebar.selectbox(
        "Cohort B",
        options=list(cohort_options.keys()),
        index=(
            options_list.index(default_cohort2)
            if default_cohort2 in options_list
            else 1 if len(options_list) > 1 else 0
        ),
        key="cohort2",
    )

    cohort1_id = cohort_options[cohort1_display]
    cohort2_id = cohort_options[cohort2_display]

    # Metric selection (for future extensibility)
    st.sidebar.title("📊 Analysis Options")
    available_metrics = metric_registry.list_metrics()
    selected_metric_id = st.sidebar.selectbox(
        "Metric to Compare",
        options=[m.metric_id for m in available_metrics],
        format_func=lambda x: metric_registry.get_metric(x).display_name,
        key="metric",
    )

    # Main content area
    if cohort1_id == cohort2_id:
        st.warning("⚠️ Please select two different cohorts to compare")
        return

    # Load cohort data
    with st.spinner("Loading cohort data..."):
        cohort1_data = cohort_manager.pipeline.load_cohort_results(cohort1_id)
        cohort2_data = cohort_manager.pipeline.load_cohort_results(cohort2_id)

    if cohort1_data is None or cohort1_data.empty:
        st.error(f"No data found for cohort '{cohort1_id}'. Process it first with the management script.")
        return

    if cohort2_data is None or cohort2_data.empty:
        st.error(f"No data found for cohort '{cohort2_id}'. Process it first with the management script.")
        return

    # Show cohort info
    col1, col2 = st.columns(2)

    with col1:
        st.subheader(f"🅰️ {cohort1_display}")
        st.metric("Games", len(cohort1_data))
        players1 = len(set(cohort1_data["white_player"]) | set(cohort1_data["black_player"]))
        st.metric("Players", players1)

    with col2:
        st.subheader(f"🅱️ {cohort2_display}")
        st.metric("Games", len(cohort2_data))
        players2 = len(set(cohort2_data["white_player"]) | set(cohort2_data["black_player"]))
        st.metric("Players", players2)

    # Run comparison
    st.markdown("---")
    st.subheader("📊 Comparison Results")

    # Get selected metric and run comparison
    metric = metric_registry.get_metric(selected_metric_id)
    result = metric.compare_cohorts(cohort1_data, cohort2_data, cohort1_id, cohort2_id)

    # Display summary statistics
    if "error" in result.summary_stats:
        st.error(result.summary_stats["error"])
        return

    # Summary metrics
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(f"{cohort1_id} Median", f"{result.summary_stats['cohort1_median']:.3f}")

    with col2:
        st.metric(f"{cohort2_id} Median", f"{result.summary_stats['cohort2_median']:.3f}")

    with col3:
        diff = result.summary_stats["median_difference"]
        st.metric("Difference", f"{diff:+.3f}", delta=f"{diff:+.3f}")

    # Visualizations
    st.markdown("### 📈 Distributions")

    # Box plot comparison
    if result.cohort1_values and result.cohort2_values:
        fig = comparison_boxplot(
            result.cohort1_values, result.cohort2_values, cohort1_id, cohort2_id, f"{metric.display_name} Comparison"
        )
        st.plotly_chart(fig, use_container_width=True)

    # Per-file heatmaps (if available)
    if "per_file_data" in result.visualization_data:
        st.markdown("### 🏁 Per-File Analysis")

        per_file_data = result.visualization_data["per_file_data"]

        if cohort1_id in per_file_data and cohort2_id in per_file_data:
            # Calculate shared scale
            all_values = list(per_file_data[cohort1_id].values()) + list(per_file_data[cohort2_id].values())
            vmin = 0.0
            vmax = max(all_values) if all_values else 1.0

            col1, col2 = st.columns(2)

            with col1:
                fig1 = create_simple_board_heatmap(
                    per_file_data[cohort1_id], f"{cohort1_id} - {metric.display_name}", vmin=vmin, vmax=vmax
                )
                st.plotly_chart(fig1, use_container_width=True)

            with col2:
                fig2 = create_simple_board_heatmap(
                    per_file_data[cohort2_id], f"{cohort2_id} - {metric.display_name}", vmin=vmin, vmax=vmax
                )
                st.plotly_chart(fig2, use_container_width=True)

            st.caption(f"📏 Shared scale: {vmin:.3f} to {vmax:.3f}")

    # Statistical details
    with st.expander("📋 Statistical Details"):
        stats_df = pd.DataFrame(
            [
                {"Statistic": "Count", cohort1_id: len(result.cohort1_values), cohort2_id: len(result.cohort2_values)},
                {
                    "Statistic": "Mean",
                    cohort1_id: f"{result.summary_stats['cohort1_mean']:.3f}",
                    cohort2_id: f"{result.summary_stats['cohort2_mean']:.3f}",
                },
                {
                    "Statistic": "Median",
                    cohort1_id: f"{result.summary_stats['cohort1_median']:.3f}",
                    cohort2_id: f"{result.summary_stats['cohort2_median']:.3f}",
                },
                {
                    "Statistic": "Std Dev",
                    cohort1_id: f"{result.summary_stats['cohort1_std']:.3f}",
                    cohort2_id: f"{result.summary_stats['cohort2_std']:.3f}",
                },
                {
                    "Statistic": "Effect Size (Cohen's d)",
                    cohort1_id: f"{result.summary_stats.get('effect_size', 0):.3f}",
                    cohort2_id: "",
                },
            ]
        )
        st.dataframe(stats_df, use_container_width=True)

    # Cohort management link
    st.markdown("---")
    st.markdown("### ⚙️ Cohort Management")
    st.markdown("To process new cohorts or check status, use: `python scripts/manage_cohorts.py status`")


# Cohort management page
def show_cohort_management():
    """Show cohort management interface."""
    st.title("⚙️ Cohort Management")

    cohort_manager = get_cohort_manager()
    status = cohort_manager.get_status()

    st.subheader("System Status")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total Cohorts", status["total_cohorts"])
    with col2:
        st.metric("Active Cohorts", status["active_cohorts"])
    with col3:
        st.metric("Total Games", status["total_games"])

    st.subheader("Cohort Details")

    # Create status dataframe
    cohort_data = []
    for cohort in status["cohorts"]:
        progress = cohort["progress"]
        status_icon = "✅" if progress >= 80 else "🔄" if progress > 0 else "⏸️"

        cohort_data.append(
            {
                "Status": status_icon,
                "ID": cohort["id"],
                "Target Games": cohort["target_games"],
                "Collected": cohort["collected_games"],
                "Progress": f"{progress:.1f}%",
                "Tags": ", ".join(cohort["tags"][:3]),
            }
        )

    if cohort_data:
        df = pd.DataFrame(cohort_data)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No cohorts configured.")


if __name__ == "__main__":
    # Simple navigation
    page = st.sidebar.radio("Navigation", ["🎯 Compare Cohorts", "⚙️ Manage Cohorts"])

    if page == "🎯 Compare Cohorts":
        main()
    else:
        show_cohort_management()
