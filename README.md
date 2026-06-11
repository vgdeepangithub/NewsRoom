# Trump Trolls — Daily Podcast Workflow

Automated daily pipeline that:
1. Finds Trump's press briefing / interview transcript
2. Generates a Jon Stewart-style satirical rebuttal (~5-10 min)
3. Outputs a ready-to-read teleprompter script

---

## Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Configure API key
cp .env.example .env
# Edit .env and set ANTHROPIC_API_KEY=your_key_here
```

---

## Daily Usage

```bash
# Auto-fetch today's transcript and generate script
python main.py

# Use a specific URL (paste from any news site)
python main.py --url "https://www.rev.com/blog/..."

# Use a saved transcript file
python main.py --file my_transcript.txt

# Just check if a transcript exists (no API call)
python main.py --dry-run
```

Output lands in `output/YYYY-MM-DD_trump-trolls.txt` (teleprompter)
and `output/YYYY-MM-DD_trump-trolls.md` (archive/sharing).

---

## Transcript Sources & Expected Delays

| Source | Typical Availability | Notes |
|---|---|---|
| whitehouse.gov | Same day, ~1-3 hrs after event | Press briefings, remarks, statements |
| Rev.com | Same day to next morning | Auto-transcripts, very fast |
| American Presidency Project | 1-3 days | Most complete, academic archive |

**What to expect:**
- Morning events (before 2pm ET): transcript usually ready same evening
- Afternoon/late events: may slip to next morning
- If nothing found, the script prints "NO APPEARANCE — SKIPPING TODAY"
- If a transcript is from a prior day, you'll see a ⚠ delay warning

---

## Skip Days

The workflow auto-skips if no Trump public appearance is found. This covers:
- No scheduled press briefings
- Weekends / travel days with no public events
- Days where transcripts haven't hit any source yet (try re-running later)

---

## Cron Setup (optional)

Run at 7pm Eastern daily:

```cron
0 19 * * * cd /path/to/NewsRoom && python main.py >> logs/$(date +\%Y-\%m-\%d).log 2>&1
```

---

## Teleprompter Reading Guide

| Marker | Meaning |
|---|---|
| `[STAGE DIRECTION]` | Action cue — do not read aloud |
| `**WORD**` | Punch this word hard |
| `...` | Short pause (1-2 sec) |
| `(BEAT)` | Comedic pause — let it land (2-3 sec) |
| `[AUDIENCE LAUGH — WAIT]` | Hold until laughter settles |
