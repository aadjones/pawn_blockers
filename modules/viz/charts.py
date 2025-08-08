"""Chart generation functions"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def line_chart(df: pd.DataFrame, metric: str, color: str = "#1f77b4") -> go.Figure:
    """
    Create a line chart for time series data.

    Args:
        df: DataFrame with time series data
        metric: Column name to plot
        color: Line color

    Returns:
        Plotly figure object
    """
    if df.empty or metric not in df.columns:
        # Return empty chart
        fig = go.Figure()
        fig.add_annotation(text="No data available", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
        return fig

    fig = px.line(df, x=df.columns[0], y=metric, title=f"{metric} over time")  # Assume first column is x-axis

    fig.update_traces(line_color=color)
    fig.update_layout(width=800, height=400, showlegend=False)

    return fig


def distribution_plot(values: list, title: str = "Distribution", bin_size: int = 20) -> go.Figure:
    """
    Create a histogram/distribution plot.

    Args:
        values: List of numeric values
        title: Plot title
        bin_size: Number of bins

    Returns:
        Plotly figure object
    """
    fig = go.Figure(data=[go.Histogram(x=values, nbinsx=bin_size, opacity=0.7)])

    fig.update_layout(title=title, xaxis_title="Value", yaxis_title="Frequency", width=600, height=400)

    return fig


def comparison_boxplot(
    group1_values: list,
    group2_values: list,
    group1_name: str = "Group 1",
    group2_name: str = "Group 2",
    title: str = "Group Comparison",
) -> go.Figure:
    """
    Create side-by-side boxplots for comparing two groups.

    Args:
        group1_values: Values for first group
        group2_values: Values for second group
        group1_name: Name of first group
        group2_name: Name of second group
        title: Plot title

    Returns:
        Plotly figure object
    """
    fig = go.Figure()

    fig.add_trace(go.Box(y=group1_values, name=group1_name, boxpoints="outliers"))

    fig.add_trace(go.Box(y=group2_values, name=group2_name, boxpoints="outliers"))

    fig.update_layout(title=title, yaxis_title="Value", width=600, height=500)

    return fig
