"""Analysis framework for flexible game comparisons"""

from .comparisons import compare_groups
from .grouping import GameFilter, PlayerClassifier, create_leela_vs_human_classifier
from .pipeline import AnalysisPipeline

__all__ = [
    "PlayerClassifier",
    "GameFilter",
    "compare_groups",
    "AnalysisPipeline",
    "create_leela_vs_human_classifier",
]
