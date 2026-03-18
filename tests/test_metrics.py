import pandas as pd

from saveloop.metrics.core import compute_j_score, compute_rates
from saveloop.metrics.derived import apply_derived_metrics


def test_metric_pipeline_basic():
    df = pd.DataFrame(
        [
            {
                "post_id": "p1",
                "date_posted": "2026-03-18",
                "format": "Reel",
                "pattern": "P01",
                "aesthetic_tags": "warm-light,steam",
                "views": 100,
                "reach": 80,
                "likes": 10,
                "comments": 5,
                "saves": 8,
                "shares": 2,
                "profile_visits": 20,
                "follows": 1,
                "avg_view_duration_s": 3.5,
                "replays": 4,
                "dms_started": 2,
                "note": "AFS: 4,4,4,4,4,4,4,4,4",
            }
        ]
    )
    df = compute_rates(df)
    df = compute_j_score(df)
    df = apply_derived_metrics(df)

    assert round(df.loc[0, "save_rate"], 3) == 0.08
    assert round(df.loc[0, "comment_rate"], 3) == 0.05
    assert round(df.loc[0, "dm_rate"], 3) == 0.1
    assert round(df.loc[0, "afs_mean"], 3) == 4.0
