"""Statistical analysis utilities"""

from .corrections import holm_correction
from .tests import per_file_analysis, wilcoxon_test

__all__ = [
    "wilcoxon_test",
    "per_file_analysis",
    "holm_correction",
]
