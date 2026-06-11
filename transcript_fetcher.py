"""
Fetches Trump transcripts from public sources.

Source priority (fastest to most delayed):
  1. whitehouse.gov briefing room  — same day, within ~2 hrs of event
  2. Rev.com auto-transcripts      — same day to next morning
  3. American Presidency Project   — 1-3 day delay, very complete

Returns a dict: {source, title, date, url, text, delay_warning}
Returns None if nothing found for today (skip-day signal).
"""

import re
import time
import logging
from datetime import date, datetime, timedelta, timezone

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    )
}

# ─────────────────────────────────────────────
# Source 1: whitehouse.gov RSS
# ─────────────────────────────────────────────

WH_RSS_FEEDS = [
    "https://www.whitehouse.gov/feed/",
    "https://www.whitehouse.gov/briefing-room/speeches-remarks/feed/",
    "https://www.whitehouse.gov/briefing-room/press-briefings/feed/",
    "https://www.whitehouse.gov/briefing-room/statements-releases/feed/",
]

TRUMP_KEYWORDS = [
    "trump", "president trump", "the president", "press briefing",
    "remarks by", "statement from the president", "interview",
    "press conference", "media availability",
]


def _is_trump_content(title: str, summary: str = "") -> bool:
    text = (title + " " + summary).lower()
    return any(kw in text for kw in TRUMP_KEYWORDS)


def _entry_published_today(pub_date_str: str) -> bool:
    """Parse an RSS <pubDate> string and check if it's today."""
    today = date.today()
    today_str = today.strftime("%d %b %Y")
    # Most RSS dates look like: Wed, 11 Jun 2025 14:30:00 +0000
    return today_str in pub_date_str or str(today) in pub_date_str


def _fetch_wh_full_text(url: str) -> str:
    """Extract body text from a whitehouse.gov article."""
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "lxml")
        body = soup.find("div", class_="body-content") or soup.find("article")
        if not body:
            body = soup.find("main")
        if not body:
            return ""
        paragraphs = body.find_all("p")
        return "\n\n".join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))
    except Exception as e:
        logger.warning("Failed to fetch WH full text from %s: %s", url, e)
        return ""


def fetch_from_whitehouse() -> dict | None:
    """Check WH RSS feeds for today's Trump content by parsing XML directly."""
    for feed_url in WH_RSS_FEEDS:
        try:
            r = requests.get(feed_url, headers=HEADERS, timeout=15)
            r.raise_for_status()
            soup = BeautifulSoup(r.content, "xml")
            items = soup.find_all("item")
            for item in items:
                pub_date = (item.find("pubDate") or item.find("pubdate") or item.find("dc:date"))
                pub_date_str = pub_date.get_text(strip=True) if pub_date else ""
                if pub_date_str and not _entry_published_today(pub_date_str):
                    continue
                title_tag = item.find("title")
                title = title_tag.get_text(strip=True) if title_tag else ""
                desc_tag = item.find("description")
                summary = desc_tag.get_text(strip=True) if desc_tag else ""
                if not _is_trump_content(title, summary):
                    continue
                link_tag = item.find("link")
                url = link_tag.get_text(strip=True) if link_tag else ""
                text = _fetch_wh_full_text(url)
                if len(text) < 200:
                    continue
                logger.info("Found WH transcript: %s", title)
                return {
                    "source": "whitehouse.gov",
                    "title": title,
                    "date": str(date.today()),
                    "url": url,
                    "text": text,
                    "delay_warning": None,
                }
        except Exception as e:
            logger.warning("Error parsing WH feed %s: %s", feed_url, e)
    return None


# ─────────────────────────────────────────────
# Source 2: Rev.com transcript search
# ─────────────────────────────────────────────

REV_SEARCH_URL = "https://www.rev.com/blog/transcript-category/white-house-transcripts"
REV_TRUMP_SEARCH = "https://www.rev.com/blog/?s=trump+{date}"


def _rev_entry_is_today(title: str, url: str) -> bool:
    today = date.today()
    date_str = today.strftime("%B-%d-%Y").lower().replace("-0", "-")
    alt_date_str = today.strftime("%Y/%m/%d")
    return date_str in url.lower() or alt_date_str in url.lower() or str(today.year) in title


def _fetch_rev_transcript_text(url: str) -> str:
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "lxml")
        # Rev transcript body
        body = (
            soup.find("div", class_="fl-rich-text")
            or soup.find("div", class_="entry-content")
            or soup.find("article")
        )
        if not body:
            return ""
        paragraphs = body.find_all("p")
        return "\n\n".join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))
    except Exception as e:
        logger.warning("Failed to fetch Rev transcript: %s", e)
        return ""


def fetch_from_rev() -> dict | None:
    today = date.today()
    search_url = REV_TRUMP_SEARCH.format(date=today.strftime("%Y-%m-%d"))
    try:
        r = requests.get(search_url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "lxml")
        articles = soup.find_all("article") or soup.find_all("div", class_="post")
        for article in articles[:5]:
            link_tag = article.find("a", href=True)
            if not link_tag:
                continue
            url = link_tag["href"]
            title = link_tag.get_text(strip=True) or article.find("h2", string=True) or ""
            if isinstance(title, str) and _is_trump_content(title) and _rev_entry_is_today(title, url):
                text = _fetch_rev_transcript_text(url)
                if len(text) > 300:
                    return {
                        "source": "rev.com",
                        "title": str(title),
                        "date": str(today),
                        "url": url,
                        "text": text,
                        "delay_warning": None,
                    }
    except Exception as e:
        logger.warning("Rev.com fetch failed: %s", e)
    return None


# ─────────────────────────────────────────────
# Source 3: American Presidency Project
# ─────────────────────────────────────────────

APP_SEARCH_URL = (
    "https://www.presidency.ucsb.edu/advanced-search"
    "?field-keywords=&field-keywords2=&field-keywords3="
    "&from%5Bdate%5D={from_date}&to%5Bdate%5D={to_date}"
    "&person2=200301&category2%5B%5D=46&category2%5B%5D=47"
    "&category2%5B%5D=406&items_per_page=5"
)


def fetch_from_presidency_project(max_days_old: int = 3) -> dict | None:
    """Checks APP for recent Trump transcripts (1-3 day delay expected)."""
    today = date.today()
    from_date = (today - timedelta(days=max_days_old)).strftime("%m-%d-%Y")
    to_date = today.strftime("%m-%d-%Y")
    url = APP_SEARCH_URL.format(from_date=from_date, to_date=to_date)
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "lxml")
        rows = soup.select("td.views-field-title a")
        if not rows:
            return None
        first = rows[0]
        title = first.get_text(strip=True)
        href = first.get("href", "")
        full_url = f"https://www.presidency.ucsb.edu{href}" if href.startswith("/") else href

        # Get the date of the document
        date_cells = soup.select("td.date-display-single")
        doc_date_str = date_cells[0].get_text(strip=True) if date_cells else ""

        r2 = requests.get(full_url, headers=HEADERS, timeout=20)
        r2.raise_for_status()
        soup2 = BeautifulSoup(r2.text, "lxml")
        body = soup2.find("div", class_="field-docs-content")
        if not body:
            return None
        paragraphs = body.find_all("p")
        text = "\n\n".join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))
        if len(text) < 300:
            return None

        delay_days = (today - today).days  # placeholder; actual calc below
        try:
            doc_date = datetime.strptime(doc_date_str, "%B %d, %Y").date()
            delay_days = (today - doc_date).days
        except ValueError:
            delay_days = 1

        delay_warning = (
            f"Note: This transcript is from {doc_date_str} "
            f"({delay_days} day(s) old) — the American Presidency Project "
            f"typically lags 1-3 days behind real-time events."
        ) if delay_days > 0 else None

        return {
            "source": "presidency.ucsb.edu",
            "title": title,
            "date": doc_date_str,
            "url": full_url,
            "text": text,
            "delay_warning": delay_warning,
        }
    except Exception as e:
        logger.warning("Presidency Project fetch failed: %s", e)
    return None


# ─────────────────────────────────────────────
# Public entry point
# ─────────────────────────────────────────────

def get_todays_transcript() -> dict | None:
    """
    Try sources in order of freshness.
    Returns transcript dict or None (no appearance today → skip day).
    """
    logger.info("Checking whitehouse.gov…")
    result = fetch_from_whitehouse()
    if result:
        return result

    logger.info("Checking Rev.com…")
    result = fetch_from_rev()
    if result:
        return result

    logger.info("Checking American Presidency Project (may be delayed)…")
    result = fetch_from_presidency_project()
    if result:
        return result

    return None
