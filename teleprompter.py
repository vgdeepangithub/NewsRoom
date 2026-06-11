"""
Formats the generated script into a clean teleprompter file.

Outputs:
  - A .txt file with clean teleprompter formatting (large readable format)
  - A .md file for archiving / sharing

Naming: YYYY-MM-DD_trump-trolls.{txt,md}
"""

import os
import textwrap
from datetime import date
from pathlib import Path

OUTPUT_DIR = Path("output")

TELEPROMPTER_HEADER = """\
╔══════════════════════════════════════════════════════════╗
║            TRUMP TROLLS  ·  TELEPROMPTER SCRIPT         ║
╚══════════════════════════════════════════════════════════╝

  Episode Date : {date}
  Source       : {source}
  Transcript   : {url}
  Generated    : {generated}
{delay_warning}
══════════════════════════════════════════════════════════
  READING GUIDE
  [STAGE DIRECTION] = action cue (do not read aloud)
  **WORD**          = punch this word hard
  ...               = short pause (1-2 sec)
  (BEAT)            = comedic pause — let it land (2-3 sec)
  [AUDIENCE LAUGH — WAIT] = hold until laughter settles
══════════════════════════════════════════════════════════

"""

MD_HEADER = """\
# Trump Trolls — Episode {date}

**Source:** [{source}]({url})
**Generated:** {generated}
{delay_warning}

---

"""


def _wrap_lines(text: str, width: int = 70) -> str:
    """Wrap long lines but preserve stage directions and blank lines."""
    lines = text.split("\n")
    wrapped = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            wrapped.append("")
        elif stripped.startswith("[") or stripped.startswith("("):
            # stage directions — don't wrap, just indent
            wrapped.append("  " + stripped)
        else:
            # spoken text — wrap at width
            wrapped.extend(textwrap.wrap(line, width=width, subsequent_indent="  ") or [""])
    return "\n".join(wrapped)


def save_script(script: str, transcript: dict) -> tuple[Path, Path]:
    """
    Save the script as both a teleprompter .txt and an archive .md.
    Returns (txt_path, md_path).
    """
    OUTPUT_DIR.mkdir(exist_ok=True)
    today = date.today().isoformat()
    base = OUTPUT_DIR / f"{today}_trump-trolls"

    delay_section = (
        f"\n  ⚠  {transcript['delay_warning']}\n"
        if transcript.get("delay_warning")
        else ""
    )

    from datetime import datetime
    generated = datetime.now().strftime("%Y-%m-%d %H:%M")

    # ── Teleprompter .txt ──────────────────────────────────────
    header = TELEPROMPTER_HEADER.format(
        date=today,
        source=transcript["source"],
        url=transcript["url"],
        generated=generated,
        delay_warning=delay_section,
    )
    txt_content = header + _wrap_lines(script, width=70)
    txt_path = base.with_suffix(".txt")
    txt_path.write_text(txt_content, encoding="utf-8")

    # ── Archive .md ───────────────────────────────────────────
    md_delay = f"\n> **⚠ Delay notice:** {transcript['delay_warning']}\n" if transcript.get("delay_warning") else ""
    md_header = MD_HEADER.format(
        date=today,
        source=transcript["source"],
        url=transcript["url"],
        generated=generated,
        delay_warning=md_delay,
    )
    md_path = base.with_suffix(".md")
    md_path.write_text(md_header + script, encoding="utf-8")

    return txt_path, md_path
