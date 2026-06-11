#!/usr/bin/env python3
"""
Trump Trolls — Daily Podcast Workflow
--------------------------------------
Run this script each day to:
  1. Find today's Trump transcript (press briefing, interview, etc.)
  2. Generate a Jon Stewart-style satirical teleprompter script
  3. Save it to output/YYYY-MM-DD_trump-trolls.{txt,md}

Usage:
    python main.py                  # auto-fetch today's transcript
    python main.py --url URL        # use a specific transcript URL
    python main.py --file FILE.txt  # use a local transcript file
    python main.py --dry-run        # fetch only, no script generation
"""

import argparse
import logging
import os
import sys
from datetime import date
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def _check_api_key():
    key = os.getenv("ANTHROPIC_API_KEY", "")
    if not key or key == "your_key_here":
        logger.error(
            "ANTHROPIC_API_KEY is not set. "
            "Copy .env.example to .env and add your key."
        )
        sys.exit(1)


def _load_local_file(path: str) -> dict:
    text = Path(path).read_text(encoding="utf-8")
    return {
        "source": "local file",
        "title": Path(path).name,
        "date": str(date.today()),
        "url": path,
        "text": text,
        "delay_warning": None,
    }


def _fetch_url_transcript(url: str) -> dict:
    import requests
    from bs4 import BeautifulSoup
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
        )
    }
    r = requests.get(url, headers=headers, timeout=20)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "lxml")
    for tag in soup(["script", "style", "nav", "header", "footer", "aside"]):
        tag.decompose()
    body = (
        soup.find("article")
        or soup.find("main")
        or soup.find("div", class_="body-content")
        or soup.find("div", class_="entry-content")
        or soup.body
    )
    text = "\n\n".join(
        p.get_text(strip=True)
        for p in (body or soup).find_all("p")
        if len(p.get_text(strip=True)) > 40
    )
    title = soup.find("title")
    return {
        "source": url,
        "title": title.get_text(strip=True) if title else url,
        "date": str(date.today()),
        "url": url,
        "text": text,
        "delay_warning": None,
    }


def run(args: argparse.Namespace):
    _check_api_key()

    # ── Step 1: Get transcript ──────────────────────────────
    print()
    print("=" * 60)
    print("  TRUMP TROLLS  ·  Daily Podcast Workflow")
    print(f"  {date.today().strftime('%A, %B %d, %Y')}")
    print("=" * 60)
    print()

    if args.file:
        logger.info("Loading local file: %s", args.file)
        transcript = _load_local_file(args.file)
    elif args.url:
        logger.info("Fetching transcript from URL: %s", args.url)
        transcript = _fetch_url_transcript(args.url)
    else:
        from transcript_fetcher import get_todays_transcript
        logger.info("Searching for today's Trump transcript…")
        transcript = get_todays_transcript()

    if transcript is None:
        print()
        print("━" * 60)
        print("  NO APPEARANCE FOUND — SKIPPING TODAY")
        print()
        print("  No Trump press briefing, interview, or public statement")
        print(f"  was found for {date.today().isoformat()}.")
        print()
        print("  Re-run later in the day if you expect an event,")
        print("  or check back tomorrow.")
        print("━" * 60)
        print()
        sys.exit(0)

    # ── Report what we found ────────────────────────────────
    print(f"  ✓ Transcript found")
    print(f"    Source : {transcript['source']}")
    print(f"    Title  : {transcript['title']}")
    print(f"    Date   : {transcript['date']}")
    print(f"    Words  : ~{len(transcript['text'].split()):,}")
    if transcript.get("delay_warning"):
        print()
        print(f"  ⚠  {transcript['delay_warning']}")
    print()

    if args.dry_run:
        print("  [--dry-run] Stopping before script generation.")
        print()
        return

    # ── Step 2: Generate script ─────────────────────────────
    from script_generator import generate_script
    model = args.model or "claude-opus-4-8"
    print(f"  Generating Jon Stewart-style script (model: {model})…")
    print("  This takes ~15-30 seconds…")
    print()

    script = generate_script(transcript, model=model)

    # ── Step 3: Save teleprompter files ────────────────────
    from teleprompter import save_script
    txt_path, md_path = save_script(script, transcript)

    print("━" * 60)
    print("  DONE — Files saved:")
    print(f"    Teleprompter : {txt_path}")
    print(f"    Archive      : {md_path}")
    print("━" * 60)
    print()

    # Print a preview of the first 40 lines
    lines = txt_path.read_text(encoding="utf-8").split("\n")
    preview_lines = [l for l in lines if l.strip()][:40]
    print("\n".join(preview_lines))
    print()
    print("  [Full script saved to files above]")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Trump Trolls — Daily Podcast Script Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--url", help="Fetch transcript from this URL instead of auto-searching")
    parser.add_argument("--file", help="Use a local .txt transcript file")
    parser.add_argument("--dry-run", action="store_true", help="Find transcript only, skip generation")
    parser.add_argument("--model", help="Claude model to use (default: claude-opus-4-8)")
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
