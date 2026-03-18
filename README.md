# saveloop

SaveLoop is a lightweight content experimentation and insight engine for creator growth. It is built for a simple workflow: log posts, compute performance signals, track experiments, and turn those signals into a weekly recommendation.

## What changed in this refactor

The old version worked as a small script bundle. This version restructures the project into clearer layers:

- `saveloop/io/` for loading, validation, and writing
- `saveloop/metrics/` for post-level and derived metrics
- `saveloop/analysis/` for signal interpretation and recommendations
- `saveloop/reporting/` for markdown summary generation
- `config/` for split configuration files
- `data/raw`, `data/processed`, and `data/reports` for a cleaner data flow

## Core workflow

Raw data in → metrics computed → insights inferred → recommendation generated → report written

## Project structure

```text
saveloop/
├── config/
│   ├── experiments.yaml
│   ├── metrics.yaml
│   └── settings.yaml
├── data/
│   ├── raw/
│   ├── processed/
│   └── reports/
├── briefs/
├── saveloop/
│   ├── analysis/
│   ├── io/
│   ├── metrics/
│   ├── models/
│   ├── reporting/
│   ├── cli.py
│   └── config.py
├── scripts/
└── tests/
```

## Metrics

The current objective stays the same:

- `save_rate = saves / views`
- `comment_rate = comments / views`
- `dm_rate = dms_started / profile_visits`
- `hook_efficiency = (saves * 1000) / views`
- `engagement_rate = (likes + comments + saves + shares) / views`
- `J = 0.6 * save_rate + 0.3 * comment_rate + 0.1 * dm_rate`

Thresholds and weights live in `config/metrics.yaml`.

## Commands

```bash
python3.11 -m venv .saveloop
source .saveloop/bin/activate
pip install -r requirements.txt

python -m saveloop.cli validate
python -m saveloop.cli analyze
python -m saveloop.cli report
python -m saveloop.cli recommend
python -m saveloop.cli run
```

## Data locations

- Input posts log: `data/raw/posts_log.csv`
- Processed metrics: `data/processed/posts_log_with_metrics.csv`
- Tag summary: `data/processed/tag_performance.csv`
- Pattern summary: `data/processed/pattern_performance.csv`
- Weekly markdown summary: `data/reports/weekly_summary.md`

## Notes

- `config.yaml`, `saveloop/metrics.py`, and `saveloop/reporting.py` are kept as thin compatibility layers.
- This version is still CSV-first, which makes it easy to keep using without any API dependency.
- The recommendation engine is now isolated in `saveloop/analysis/recommendations.py`, which makes future upgrades much easier.
