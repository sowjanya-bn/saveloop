# SaveLoop

SaveLoop is a lightweight trend-driven content planning and feedback system.

## Current flow

1. Pull or load trend signals
2. Generate content bundles
3. Shortlist and manage bundles in the UI
4. Link posted content back to a bundle
5. Analyse performance and generate a weekly recommendation

## Batch A updates

- human-readable weekly summary
- richer content bundle schema
- `bundle_id` linkage from bundle to post log
- Streamlit bundle board with status editing and filters

## Commands

```bash
python -m saveloop.cli trends
python -m saveloop.cli bundles
python -m saveloop.cli validate
python -m saveloop.cli analyze
python -m saveloop.cli report
python -m saveloop.cli run
```

## UI

```bash
streamlit run saveloop/ui/app.py
```


## Optional Gemini generation

Generation Studio supports a rule-based mode and a Gemini-enhanced mode. Configure `GEMINI_API_KEY` in `.env` to enable richer copy generation with `gemini-3-flash-preview` and optional image creation with `gemini-3.1-flash-image-preview`.
