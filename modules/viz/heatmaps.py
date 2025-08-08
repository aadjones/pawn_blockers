"""Chess board heatmap visualizations"""

from typing import Dict, Optional, Tuple

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from ..core.board_analysis import FILES


def create_delta_heatmap(
    group1_data: Dict[str, float],
    group2_data: Dict[str, float],
    title: str = "Blocking Rate Difference",
    group1_name: str = "Group 1",
    group2_name: str = "Group 2",
) -> go.Figure:
    """
    Create a chess board heatmap showing difference in blocking rates.

    Args:
        group1_data: Dictionary with file -> blocking_rate for group 1
        group2_data: Dictionary with file -> blocking_rate for group 2
        title: Plot title
        group1_name: Name of first group
        group2_name: Name of second group

    Returns:
        Plotly figure object
    """
    # Create 8x8 board (White's perspective: rank 1 at bottom)
    board = np.zeros((8, 8))
    hover_text = [[""] * 8 for _ in range(8)]

    for i, file_letter in enumerate(FILES):
        rate1 = group1_data.get(file_letter, 0.0)
        rate2 = group2_data.get(file_letter, 0.0)
        difference = rate2 - rate1  # Group2 - Group1

        # Only squares a3-h3 (rank index 2) and a6-h6 (rank index 5) can have values
        # These are the squares directly ahead of starting pawn positions

        # White pawn ahead squares (rank 3)
        board[2, i] = difference
        hover_text[2][i] = (
            f"{file_letter}3<br>"
            f"{group1_name}: {rate1:.3f}<br>"
            f"{group2_name}: {rate2:.3f}<br>"
            f"Difference: {difference:+.3f}"
        )

        # Black pawn ahead squares (rank 6)
        board[5, i] = difference
        hover_text[5][i] = (
            f"{file_letter}6<br>"
            f"{group1_name}: {rate1:.3f}<br>"
            f"{group2_name}: {rate2:.3f}<br>"
            f"Difference: {difference:+.3f}"
        )

    # Find color scale limits
    max_abs = np.max(np.abs(board[np.nonzero(board)])) if np.any(board) else 1.0

    fig = go.Figure(
        data=go.Heatmap(
            z=board,
            x=list(FILES),
            y=list(range(1, 9)),
            colorscale="RdBu",
            zmid=0,
            zmin=-max_abs,
            zmax=max_abs,
            hovertemplate="%{text}<extra></extra>",
            text=hover_text,
            colorbar=dict(title=f"Rate Difference<br>({group2_name} - {group1_name})"),
        )
    )

    fig.update_layout(
        title=title,
        xaxis_title="File",
        yaxis_title="Rank",
        width=600,
        height=600,
        xaxis=dict(tickmode="array", tickvals=list(range(8)), ticktext=list(FILES), side="bottom"),
        yaxis=dict(tickmode="array", tickvals=list(range(8)), ticktext=list(range(1, 9)), autorange=True),
    )

    return fig


def create_per_file_comparison_chart(
    df: pd.DataFrame,
    group1_prefix: str = "group1",
    group2_prefix: str = "group2",
    title: str = "Per-File Blocking Rates",
) -> go.Figure:
    """
    Create a bar chart comparing per-file blocking rates between two groups.

    Args:
        df: DataFrame with per-file columns
        group1_prefix: Column prefix for first group
        group2_prefix: Column prefix for second group
        title: Chart title

    Returns:
        Plotly figure object
    """
    files = []
    group1_rates = []
    group2_rates = []

    for file_letter in FILES:
        col1 = f"{group1_prefix}_{file_letter}"
        col2 = f"{group2_prefix}_{file_letter}"

        if col1 in df.columns and col2 in df.columns:
            # Calculate median rates
            mask1 = df[col1].notna()
            mask2 = df[col2].notna()

            if mask1.sum() > 0 and mask2.sum() > 0:
                files.append(file_letter)
                group1_rates.append(df.loc[mask1, col1].median())
                group2_rates.append(df.loc[mask2, col2].median())

    fig = go.Figure()

    fig.add_trace(go.Bar(x=files, y=group1_rates, name=group1_prefix.title(), marker_color="lightblue"))

    fig.add_trace(go.Bar(x=files, y=group2_rates, name=group2_prefix.title(), marker_color="lightcoral"))

    fig.update_layout(
        title=title, xaxis_title="File", yaxis_title="Median Blocking Rate", barmode="group", width=800, height=500
    )

    return fig


def create_single_heatmap(
    file_data: Dict[str, float],
    title: str = "Blocking Rates",
    player_name: str = "Player",
    vmin: float = None,
    vmax: float = None,
) -> go.Figure:
    """
    Create a single chess board heatmap showing blocking rates.

    Args:
        file_data: Dictionary with file -> blocking_rate
        title: Plot title
        player_name: Player name for hover text
        vmin: Minimum value for color scale
        vmax: Maximum value for color scale

    Returns:
        Plotly figure object
    """
    # Create 8x8 board (White's perspective: rank 1 at bottom)
    board = np.zeros((8, 8))
    hover_text = [[""] * 8 for _ in range(8)]

    for i, file_letter in enumerate(FILES):
        rate = file_data.get(file_letter, 0.0)

        # Only squares a3-h3 (rank index 2) and a6-h6 (rank index 5) can have values
        # These are the squares directly ahead of starting pawn positions

        # White pawn ahead squares (rank 3)
        board[2, i] = rate
        hover_text[2][i] = f"{file_letter}3<br>" f"{player_name}: {rate:.3f}"

        # Black pawn ahead squares (rank 6)
        board[5, i] = rate
        hover_text[5][i] = f"{file_letter}6<br>" f"{player_name}: {rate:.3f}"

    # Use provided scale or calculate from data
    if vmin is None:
        min_val = 0
    else:
        min_val = vmin

    if vmax is None:
        max_val = np.max(board) if np.any(board) else 1.0
    else:
        max_val = vmax

    fig = go.Figure(
        data=go.Heatmap(
            z=board,
            x=list(FILES),
            y=list(range(1, 9)),
            colorscale="Blues",  # Single color scale instead of diverging
            zmin=min_val,
            zmax=max_val,
            hovertemplate="%{text}<extra></extra>",
            text=hover_text,
            colorbar=dict(title="Blocking Rate"),
        )
    )

    fig.update_layout(
        title=dict(text=title, x=0.5),  # Center the title
        xaxis_title="File",
        yaxis_title="Rank",
        width=400,  # Square dimensions
        height=450,  # Slightly taller to account for title/labels
        margin=dict(l=50, r=50, t=80, b=50),  # Consistent margins
        xaxis=dict(
            tickmode="array",
            tickvals=list(range(8)),
            ticktext=list(FILES),
            side="bottom",
            showgrid=False,  # Turn off built-in grid
            range=[-0.5, 7.5],  # Exact range for 8 squares
            fixedrange=True,  # Prevent zooming
        ),
        yaxis=dict(
            tickmode="array",
            tickvals=list(range(8)),
            ticktext=list(range(1, 9)),
            showgrid=False,  # Turn off built-in grid
            range=[-0.5, 7.5],  # Exact range for 8 squares
            scaleanchor="x",  # Force equal aspect ratio
            scaleratio=1,
            fixedrange=True,  # Prevent zooming
        ),
        plot_bgcolor="white",
    )

    # Add explicit grid lines to make chess squares visible
    for i in range(9):  # 9 lines for 8 squares
        # Vertical lines
        fig.add_shape(
            type="line",
            x0=i - 0.5,
            x1=i - 0.5,
            y0=-0.5,
            y1=7.5,
            line=dict(color="gray", width=1, dash="solid"),
            layer="below",
        )
        # Horizontal lines
        fig.add_shape(
            type="line",
            x0=-0.5,
            x1=7.5,
            y0=i - 0.5,
            y1=i - 0.5,
            line=dict(color="gray", width=1, dash="solid"),
            layer="below",
        )

    return fig
