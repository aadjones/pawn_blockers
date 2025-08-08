"""Registry for available chess game metrics."""

from typing import Dict, List

from .base import AbstractMetric
from .pawn_blocking import PawnBlockingMetric


class MetricRegistry:
    """Registry of available metrics for analysis."""

    def __init__(self):
        self._metrics: Dict[str, AbstractMetric] = {}
        self._register_builtin_metrics()

    def _register_builtin_metrics(self):
        """Register built-in metrics."""
        # Start with just pawn blocking - more metrics added later
        self.register(PawnBlockingMetric())

    def register(self, metric: AbstractMetric):
        """Register a new metric."""
        self._metrics[metric.metric_id] = metric

    def get_metric(self, metric_id: str) -> AbstractMetric:
        """Get a metric by ID."""
        if metric_id not in self._metrics:
            raise ValueError(f"Unknown metric: {metric_id}")
        return self._metrics[metric_id]

    def list_metrics(self) -> List[AbstractMetric]:
        """Get all available metrics."""
        return list(self._metrics.values())

    def get_metric_ids(self) -> List[str]:
        """Get all metric IDs."""
        return list(self._metrics.keys())

    def get_default_metric_id(self) -> str:
        """Get the default metric for analysis."""
        return "pawn_blocking"


# Global registry instance
_registry = MetricRegistry()


def get_registry() -> MetricRegistry:
    """Get the global metric registry."""
    return _registry
