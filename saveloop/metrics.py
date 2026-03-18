"""Backward-compatible access to the refactored metrics pipeline."""

from saveloop.metrics.aggregations import aggregate_pattern_performance, aggregate_tag_performance
from saveloop.metrics.core import compute_j_score, compute_rates, safe_div
from saveloop.metrics.derived import apply_derived_metrics, parse_afs_mean

__all__ = [
    "aggregate_pattern_performance",
    "aggregate_tag_performance",
    "apply_derived_metrics",
    "compute_j_score",
    "compute_rates",
    "parse_afs_mean",
    "safe_div",
]
