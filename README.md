# SaveLoop

SaveLoop is a verified consumer intelligence tool for Instagram. It monitors shrinkflation, fake deals, subscription traps, and single-person pricing — turning community-flagged claims into verified, ready-to-post content.

## Pipeline

```
Signals (Reddit · Google Trends · RSS · Community submissions)
    ↓  candidates.csv  (status: new)
Triage (AI pre-fill — optional)
    ↓
Verification Board (Streamlit — human verifies numbers)
    ↓  status: verified
Bundle Generator → Script + Carousel Renderer → ZIP pack
    ↓
Post (Mon · Wed · Fri) → Metrics → Weekly summary
```

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env   # add GEMINI_API_KEY if you have one
```

## Running the UI

```bash
streamlit run saveloop/ui/app.py
```

The UI has four tabs:

| Tab | What it does |
|---|---|
| **This Week's Content** | Generate and download the 3-post weekly zip |
| **Verification Board** | Triage and verify candidates before they become posts |
| **Advanced** | Browse all candidates, edit bundle statuses, single post studio |
| **Performance** | Post history, analytics, weekly summary |

## CLI reference

### Fetch fresh signals
Pulls from Reddit, Google Trends, and RSS (MSE · Which? · BBC Business).
Adds new rows to `data/raw/candidates.csv` with `status: new`.

```bash
python -m saveloop.cli trends --fetch
```

### Review pending candidates
```bash
python -m saveloop.cli verify --list
```

### Update a candidate status (non-human transitions only)
```bash
python -m saveloop.cli verify --candidate <ID> --status pending_review --notes "checked source"
```

> `verified`, `rejected`, `needs_more_evidence`, and `duplicate` can only be set via the Streamlit Verification Board — not from the CLI.

### Generate bundles from verified candidates
```bash
python -m saveloop.cli bundles
```

### Generate a single post plan
```bash
python -m saveloop.cli generate
```

### Analytics and reporting
```bash
python -m saveloop.cli validate    # check posts_log.csv
python -m saveloop.cli analyze     # run analysis pipeline
python -m saveloop.cli report      # write weekly_summary.md
python -m saveloop.cli run         # validate + analyze + report
```

## Weekly content schedule

| Day | Type | Pillars | Posting window |
|---|---|---|---|
| Monday | Watchdog carousel | shrinkflation_watch · fake_deal_forensics | 10:00–12:00 |
| Wednesday | Story / Reel | reddit_verified · subscription_trap | 18:00–20:00 |
| Friday | Utility / Community | honest_meal_cost · saveloop_flag · single_person_tax | 17:00–19:00 |

Fallback: `honest_meal_cost` is used if no verified watchdog candidates are available.

## Community submissions

Export your Google Form responses to CSV and drop the file at `data/raw/submissions.csv`.
Then click **Import submissions** in the Verification Board tab, or run:

```bash
# Via Streamlit — recommended
# Import submissions button in the Verification Board tab
```

Submissions arrive as `pending_review` candidates and must be verified before they can become posts.

## Verification rules

- A candidate must reach `status: verified` before entering bundle generation.
- Exception: `honest_meal_cost` candidates bypass verification (`verification_required: False`).
- The Gemini triage helper in the Verification Board can pre-fill fields (product, retailer, claimed change) from raw text — but it never sets a status. All verification decisions are human-only.

## Gemini (optional)

Set `GEMINI_API_KEY` in `.env` to enable:
- Richer copy generation for slides and captions
- AI triage pre-fill in the Verification Board

Without a key, the pipeline falls back to rule-based copy generation and triage is disabled.

## Data files

| File | Purpose |
|---|---|
| `data/raw/candidates.csv` | All candidates (new → verified → posted) |
| `data/raw/submissions.csv` | Google Form CSV export (drop here manually) |
| `data/raw/trends_snapshot.csv` | Latest signal fetch (for display only) |
| `data/processed/content_bundles.csv` | Generated bundles |
| `data/processed/post_plans.json` | Individual post plans |
| `data/processed/weekly_catalog.json` | Weekly posting log |
| `data/raw/posts_log.csv` | Manual metrics import |
