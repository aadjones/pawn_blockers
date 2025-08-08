"""Simple, clean chessboard heatmap from scratch"""

from typing import Dict

import numpy as np
import plotly.graph_objects as go


def create_simple_board_heatmap(
    file_data: Dict[str, float], title: str = "Blocking Rates", vmin: float = 0.0, vmax: float = 1.0
) -> go.Figure:
    """
    Create a simple, clean chessboard heatmap.

    Args:
        file_data: Dictionary with file letter -> blocking rate
        title: Chart title
        vmin: Minimum scale value
        vmax: Maximum scale value

    Returns:
        Plotly figure
    """
    # Create empty 8x8 board
    board = np.zeros((8, 8))

    # Fill in data for ranks 3 and 6
    # Since we display 8,7,6,5,4,3,2,1 from top to bottom:
    # - Rank 6 is at array index 2 (3rd row from top)
    # - Rank 3 is at array index 5 (6th row from top)
    for i, file_letter in enumerate("abcdefgh"):
        rate = file_data.get(file_letter, 0.0)
        board[2, i] = rate  # Rank 6 (black pawns ahead) - 3rd row from top
        board[5, i] = rate  # Rank 3 (white pawns ahead) - 6th row from top

    # Debug: print the board to see what we're sending
    print("Board being sent to heatmap:")
    for i, row in enumerate(board):
        rank = 8 - i  # Convert array index to rank number
        print(f"Array row {i} (Rank {rank}): {row}")

    # Try flipping the board vertically to force correct orientation
    board_flipped = np.flipud(board)

    # Create custom hover text
    hover_text = []
    for row_idx in range(8):
        hover_row = []
        for col_idx in range(8):
            file_letter = "abcdefgh"[col_idx]
            rank_number = row_idx + 1  # Now row 0 = rank 1, row 7 = rank 8
            rate = board_flipped[row_idx, col_idx]
            hover_row.append(f"File {file_letter}, Rank {rank_number}<br>Rate: {rate:.3f}")
        hover_text.append(hover_row)

    # Create the heatmap with flipped board
    fig = go.Figure(
        data=go.Heatmap(
            z=board_flipped,
            colorscale="Blues",
            zmin=vmin,
            zmax=vmax,
            showscale=True,
            hovertemplate="%{text}<extra></extra>",
            text=hover_text,
        )
    )

    # Configure layout for exact square
    fig.update_layout(
        title=title,
        width=400,
        height=400,
        xaxis=dict(tickvals=list(range(8)), ticktext=list("abcdefgh"), side="bottom", title="File"),
        yaxis=dict(
            tickvals=list(range(8)),
            ticktext=["1", "2", "3", "4", "5", "6", "7", "8"],  # Now 1 at bottom, 8 at top
            title="Rank",
        ),
        margin=dict(l=60, r=100, t=60, b=60),
    )

    return fig
