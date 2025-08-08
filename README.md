# Pawn Blockers Analysis

Analyzes pawn blocking patterns in chess games using SPBTS (Self-Pawn Block To Start) metrics through a cohort-based comparison system.

## What It Does

Measures how often pawns on their starting squares get blocked by friendly pieces, revealing strategic differences between AI engines and human players. **Key finding**: Strong humans block pawns ~65% more than Leela (0.130 vs 0.079 median SPBTS).

## Quick Start

```bash
# Install dependencies
make install

# Process cohort data (~2000 games)
make cohorts

# Run the comparison app
make dev

# Check status
make status
```

## Current Analysis

**Two High-Quality Cohorts:**
- **Leela Odds** (984 games): AI playing with material handicaps vs humans
- **TWIC Strong** (999 games): Tournament games between 2000+ rated humans

**Sample Results:**
```
📊 Comparing leela_odds vs twic_strong
Leela Odds: median=0.079 SPBTS (984 games, 140 players)
TWIC Strong: median=0.130 SPBTS (999 games, 795 players)  
Difference: -0.051 (strong humans block 65% more)
```

## Architecture

**Extensible Cohort System:**
```
modules/
├── cohorts/        # Cohort configuration and management
├── metrics/        # Pluggable analysis metrics (SPBTS + future)
├── core/           # Chess analysis engine
├── data/           # Multi-source data collection (Lichess, TWIC)
├── stats/          # Statistical testing
└── viz/            # Interactive visualizations
```

**Data Sources:**
- **Lichess API**: User games, live data
- **TWIC Archive**: Tournament games, rating-filtered
- **Future**: Chess.com API, PGN imports, databases

## Usage

**Cohort Management:**
```bash
# List available cohorts
python scripts/manage_cohorts.py list

# Process specific cohorts
python scripts/manage_cohorts.py process leela_odds twic_strong

# Compare any two cohorts
python scripts/manage_cohorts.py compare leela_odds twic_strong

# System status
python scripts/manage_cohorts.py status
```

**Web Interface:**
```bash
# Interactive comparison app
streamlit run app_cohorts.py
```

## Adding New Metrics

The system is designed for easy extension:

```python
# Example: Opening diversity metric
class OpeningDiversityMetric(AbstractMetric):
    metric_id = "opening_diversity"
    display_name = "Opening Repertoire Diversity"
    
    def calculate_for_cohort(self, df): 
        # Calculate Shannon entropy of openings
        pass
    
    def compare_cohorts(self, df1, df2, id1, id2):
        # Custom comparison logic
        pass
```

Metrics auto-register and appear in the UI dropdown.

## Key Findings

- **F-file Dominance**: F-pawns get blocked 20-50% of the time (other files ~0-5%)
- **AI vs Human**: Leela blocks pawns significantly less than strong humans
- **Consistency**: Results hold across ~2000 games from diverse sources
- **Statistical Significance**: Large effect size (Cohen's d > 0.5)

## Development

```bash
# Makefile shortcuts
make help      # Show all commands
make test      # Run test suite  
make fmt       # Format code
make clean     # Reset environment

# Manual workflow
source env/bin/activate
python scripts/manage_cohorts.py --help
streamlit run app_cohorts.py --server.port 8501
```