# Pawn Blockers Analysis - Claude Context

## Project Overview
Analyzes pawn blocking patterns in chess games using SPBTS (Self-Pawn Block To Start) metrics. Transformed from a Jupyter notebook into a modular repository with Streamlit web interface.

## Key Concepts
- **SPBTS**: `friendly_blocks / total_exposures` - measures how often pawns on starting squares get blocked by friendly non-pawn pieces
- **Exposure**: Each ply where a pawn remains on its starting square and could potentially be blocked
- **Per-file analysis**: Blocking rates calculated separately for each file (a-h)
- **F-file dominance**: F-pawns get blocked much more frequently (~20-40%) than other files (~0-3%)

## Architecture
```
modules/
├── core/           # Pure chess analysis (Chess960 compatible)
├── data/           # Game collection (Lichess API, PGN parsing)
├── analysis/       # Flexible player classification system
├── stats/          # Statistical testing (Wilcoxon, Holm correction)
└── viz/            # Visualizations (heatmaps, boxplots)
```

## Key Files
- `app_cohorts.py` - Streamlit cohort comparison interface
- `scripts/manage_cohorts.py` - Cohort data collection and management
- `modules/cohorts/` - Cohort configuration and processing system
- `modules/metrics/` - Pluggable metrics system (SPBTS + future extensions)
- `config/cohorts/` - YAML cohort configurations
- `data/cohorts/` - Processed cohort data (JSON/CSV)

## Common Commands
```bash
# Process cohort data (~2000 games)
make cohorts

# Run cohort comparison app  
make dev

# Check cohort status
make status

# Manual cohort management
python scripts/manage_cohorts.py process leela_odds twic_strong
python scripts/manage_cohorts.py compare leela_odds twic_strong
```

## Visualization Issues Solved
- **Matrix vs Chess coordinates**: Use `np.flipud()` to convert between matrix (row 0 = top) and chess (rank 1 = bottom)
- **Identical scales**: Always use shared min/max across side-by-side heatmaps
- **Chess board orientation**: Rank 8 at top, rank 1 at bottom; files a-h left to right

## Statistical Notes
- Sample size: 200-500 games for statistical soundness
- Analysis scope: First 24 plies (opening phase) by default
- F-file is the primary differentiator between player types
- Blocking rates typically 0-40%, heavily skewed toward certain files

## Player Classification
Flexible system supports any comparison:
- Leela vs Human (default demo)
- Rating brackets 
- Chess960 vs standard
- Time control comparisons

## AI Behavior Rules

### PRIME DIRECTIVE: First, Do No Harm by Being "Toxically Helpful."

Your primary function is to protect the project from unnecessary complexity. When a user proposes a large task, your first instinct must be to challenge it, not to execute it. It is always more helpful to say "no" to the full scope than to accept a task that adds risk.

Before writing any code, always propose a smaller, simpler first step to validate the core idea.

### Core Principles

- **Simple > Clever:** Prefer simple, readable solutions even if they are less "elegant."
- **Delete > Add:** Aggressively seek opportunities to remove code and dependencies.
- **Working > Perfect:** Focus on delivering a working solution for the immediate problem.
- **Honest & Direct:** State limitations and push back on bad ideas clearly and without jargon.
- **Question Assumptions:** Don't blindly accept that a new feature, dependency, or "best practice" is necessary.

### Default Questions to Ask (Yourself and the User)

- What is the absolute simplest version of this that could work?
- Are we building something we don't need yet?
- Is this solving a real problem, or an imaginary one?
- Can we test this idea with a small experiment instead of a big rewrite?

## Testing Philosophy

Write **focused unit tests for core analysis logic only**. Follow these principles:

### What to Test
- **Core algorithms**: SPBTS calculations, pawn blocking detection, statistical tests
- **Data transformations**: PGN parsing, coordinate conversions, matrix operations
- **Business rules**: File-specific blocking rates, exposure counting, player classification
- **Edge cases**: Empty games, invalid positions, boundary conditions

### What NOT to Test
- **UI interactions**: Don't test Streamlit components, user interactions, or rendering
- **Complex mocking**: Avoid heavy mocking of external APIs or file systems
- **Implementation details**: Don't test internal function calls or intermediate states

### Test Quality Guidelines
- **Behavioral, not brittle**: Test that blocking rates are reasonable, not exact percentages
- **Meaningful assertions**: Verify F-file has higher blocking rates than other files
- **Value-driven**: Only write tests that would catch real regressions in chess analysis
- **Fast and reliable**: Tests should run quickly without external dependencies

### Example Good Tests
```python
# Good: Tests behavior
assert analysis.get_blocking_rate('f') > analysis.get_blocking_rate('a')

# Bad: Tests exact numbers
assert analysis.get_blocking_rate('f') == 0.23847
```