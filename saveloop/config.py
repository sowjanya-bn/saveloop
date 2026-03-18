from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = ROOT / "config"
LEGACY_CONFIG = ROOT / "config.yaml"


def _read_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def load_settings() -> dict[str, Any]:
    return _read_yaml(CONFIG_DIR / "settings.yaml")


def load_metrics_config() -> dict[str, Any]:
    cfg = _read_yaml(CONFIG_DIR / "metrics.yaml")
    if cfg:
        return cfg
    return _read_yaml(LEGACY_CONFIG)


def load_experiments_config() -> dict[str, Any]:
    return _read_yaml(CONFIG_DIR / "experiments.yaml")


def project_paths() -> dict[str, Path]:
    settings = load_settings()
    paths = settings.get("paths", {})
    return {
        "raw_data_dir": ROOT / paths.get("raw_data_dir", "data/raw"),
        "processed_data_dir": ROOT / paths.get("processed_data_dir", "data/processed"),
        "reports_dir": ROOT / paths.get("reports_dir", "data/reports"),
    }
