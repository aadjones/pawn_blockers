import numpy as np
import plotly.graph_objects as go

# Create simple test board
board = np.zeros((8, 8))

# Put a test value on what should be rank 6 and rank 3
board[2, 5] = 1.0  # Should show on rank 6, file f
board[5, 5] = 0.5  # Should show on rank 3, file f

print("Board array:")
print(board)
print()
print("Row 0 (should be rank 8):", board[0])
print("Row 2 (should be rank 6):", board[2])
print("Row 5 (should be rank 3):", board[5])
print("Row 7 (should be rank 1):", board[7])

# Create heatmap
fig = go.Figure(data=go.Heatmap(z=board, colorscale="Blues", showscale=True))

fig.update_layout(
    title="Debug Board",
    width=400,
    height=400,
    xaxis=dict(tickvals=list(range(8)), ticktext=list("abcdefgh"), title="File"),
    yaxis=dict(tickvals=list(range(8)), ticktext=["8", "7", "6", "5", "4", "3", "2", "1"], title="Rank"),
)

fig.show()
