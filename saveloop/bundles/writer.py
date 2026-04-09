from __future__ import annotations

from pathlib import Path

import pandas as pd

from saveloop.io.writers import write_dataframe


def save_bundles(df: pd.DataFrame, filename: str = "content_bundles.csv") -> Path:
    return write_dataframe(df, filename, target="processed_data_dir")
