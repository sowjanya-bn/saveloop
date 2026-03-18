from __future__ import annotations

from pathlib import Path

import pandas as pd

from saveloop.config import project_paths


def ensure_output_dirs() -> dict[str, Path]:
    paths = project_paths()
    for path in paths.values():
        path.mkdir(parents=True, exist_ok=True)
    return paths


def write_dataframe(df: pd.DataFrame, output_name: str, target: str = "processed_data_dir") -> Path:
    paths = ensure_output_dirs()
    out_path = paths[target] / output_name
    df.to_csv(out_path, index=False)
    return out_path


def write_text(text: str, output_name: str, target: str = "reports_dir") -> Path:
    paths = ensure_output_dirs()
    out_path = paths[target] / output_name
    out_path.write_text(text, encoding="utf-8")
    return out_path
