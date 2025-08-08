"""Cohort configuration system."""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


class CohortType(Enum):
    """Types of cohorts based on data source."""

    LICHESS_USER = "lichess_user"
    LICHESS_HUMAN_SAMPLE = "lichess_human_sample"
    TWIC = "twic"
    LICHESS_QUERY = "lichess_query"
    PGN_FILES = "pgn_files"
    MIXED = "mixed"


@dataclass
class CohortConfig:
    """Configuration for a single cohort."""

    # Basic info
    id: str
    name: str
    description: str
    type: CohortType

    # Data collection
    data_sources: List[Dict[str, Any]]
    target_games: int = 200

    # Filters
    min_rating: Optional[int] = None
    max_rating: Optional[int] = None
    time_controls: Optional[List[str]] = None
    variants: Optional[List[str]] = None

    # Classification rules (for identifying players in mixed games)
    player_patterns: Optional[List[str]] = None
    engine_detection: bool = True

    # Analysis params
    max_plies: int = 24
    min_exposure: int = 64

    # Metadata
    tags: List[str] = field(default_factory=list)
    priority: int = 1  # Higher numbers processed first

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CohortConfig":
        """Create config from dictionary."""
        # Convert type string to enum
        if "type" in data:
            data["type"] = CohortType(data["type"])
        return cls(**data)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = {}
        for key, value in self.__dict__.items():
            if isinstance(value, CohortType):
                result[key] = value.value
            else:
                result[key] = value
        return result


class CohortConfigManager:
    """Manages cohort configurations from YAML files."""

    def __init__(self, config_dir: str = "config/cohorts"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self._cohorts = {}
        self._load_configs()

    def _load_configs(self):
        """Load all YAML config files from the config directory."""
        self._cohorts.clear()

        for yaml_file in self.config_dir.glob("*.yaml"):
            try:
                with open(yaml_file, "r") as f:
                    data = yaml.safe_load(f)

                # Handle multiple cohorts in one file
                if isinstance(data, list):
                    for cohort_data in data:
                        cohort = CohortConfig.from_dict(cohort_data)
                        self._cohorts[cohort.id] = cohort
                elif isinstance(data, dict):
                    cohort = CohortConfig.from_dict(data)
                    self._cohorts[cohort.id] = cohort

            except Exception as e:
                print(f"Error loading {yaml_file}: {e}")

    def get_cohort(self, cohort_id: str) -> Optional[CohortConfig]:
        """Get cohort config by ID."""
        return self._cohorts.get(cohort_id)

    def list_cohorts(self) -> List[CohortConfig]:
        """Get all cohort configurations."""
        return list(self._cohorts.values())

    def get_cohorts_by_tag(self, tag: str) -> List[CohortConfig]:
        """Get cohorts matching a specific tag."""
        return [c for c in self._cohorts.values() if tag in c.tags]

    def save_cohort(self, cohort: CohortConfig):
        """Save a cohort configuration to YAML."""
        filename = f"{cohort.id}.yaml"
        filepath = self.config_dir / filename

        with open(filepath, "w") as f:
            yaml.dump(cohort.to_dict(), f, default_flow_style=False)

        # Reload to pick up changes
        self._cohorts[cohort.id] = cohort


def create_example_configs() -> List[CohortConfig]:
    """Create default cohort configurations."""

    configs = [
        # Leela odds games
        CohortConfig(
            id="leela_odds",
            name="Leela Odds Games",
            description="Games where Leela plays with material handicap",
            type=CohortType.LICHESS_USER,
            data_sources=[
                {"type": "lichess_user", "username": "LeelaRookOdds", "max_games": 300},
                {"type": "lichess_user", "username": "LeelaKnightOdds", "max_games": 200},
                {"type": "lichess_user", "username": "LeelaQueenOdds", "max_games": 100},
            ],
            target_games=500,
            player_patterns=["leela", "lc0"],
            tags=["ai", "handicap"],
            priority=10,
        ),
        # TWIC strong human games
        CohortConfig(
            id="twic_strong",
            name="Strong Human Games (TWIC 2000+)",
            description="Tournament and strong amateur games from The Week in Chess",
            type=CohortType.TWIC,
            data_sources=[{"type": "twic", "min_rating": 2000, "max_issues": 8, "max_games": 400}],
            target_games=400,
            min_rating=2000,
            engine_detection=True,
            tags=["human", "strong", "tournament", "twic"],
            priority=8,
        ),
    ]

    return configs
