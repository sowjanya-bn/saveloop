# saveloop — an aesthetics first feedback loop for Instagram

A small project that tracks simple Instagram growth with a save first objective. You post two items a week and log numbers. The toolkit computes a save first score and suggests one change for next week.

## Positioning
Audience: students and busy early career folks in the UK who want simple wins.  
Promise: tasty budget meals, easy routines, small money savers.  
Tone: calm and practical.

## Cadence
- Wed 19:00 Reel for a recipe
- Sun 16:00 Carousel for tips or lifestyle
- Fri story poll that drives DMs

## Aesthetic system
First frame: final dish close up with motion like drizzle or steam.  
Light and palette: warm neutrals and one accent.  
Overlay: five to seven words that are large and high contrast.  
Pacing: 0.6 to 1.2 second cuts.  
Tags to track: warm-light, drizzle, steam, tight-closeup, text-minimal, clean-bg, fork-twirl, knife-cut, sauce-swirl.

## Objective
J = 0.6·save_rate + 0.3·comment_rate + 0.1·dm_rate  
- save_rate = saves ÷ views  
- comment_rate = comments ÷ views  
- dm_rate = DMs started ÷ profile visits

Wins: Reel engagement_rate ≥ 0.50 percent. Carousel engagement_rate ≥ 0.55 percent.  
Guardrails: keep one control post and change at most one aesthetic lever and one timing lever each week.

## Data model
Per post fields:
post_id, date_posted, format, pattern, aesthetic_tags, views, reach, likes, comments, saves, shares, profile_visits, follows, avg_view_duration_s, replays, dms_started, save_rate, comment_rate, dm_rate, hook_efficiency, engagement_rate, J_score, win_flag, note.  
Rubric in note: `AFS: 4,4,5,5,4,4,3,4,4`.

## What is inside
- `config.yaml` with commented weights and thresholds
- `saveloop/metrics.py` with clear docstrings for each formula
- `saveloop/reporting.py` that writes a weekly summary
- `saveloop/cli.py` with a small command line
- `data/` with seed CSVs
- `briefs/` with two filled drafts for this week

## How to use
```bash
python3 -m venv .venv && source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m saveloop.cli analyze    # after you fill data/posts_log.csv
```

## Comments and insights from the API
You need a Professional account linked to a Page. You need a Meta app. The API gives you:  
- per post: like_count, comments_count, media_type, media_product_type, timestamp, permalink  
- insights: impressions, reach, saved, engagement, plays for Reels where available  
- account daily: reach, impressions, profile_views  
DMs are not in Insights. Use messaging webhooks if you want automation or count replies to your poll manually for the first two weeks.

## Experiments log
Keep one control post. Change one lever. Examples: first frame steam vs text first, overlay length, cover dish vs ingredients, timing shift.

## Style
Avoid em dash. Avoid Oxford comma. Use clear language.
