"""
Generates a Jon Stewart-style satirical rebuttal from a Trump transcript,
formatted as a teleprompter script for the Trump Trolls podcast.

Target: 5-10 minutes of spoken content (approx 750-1400 words at 140 wpm).
"""

import anthropic

SYSTEM_PROMPT = """You are a comedy writer for a satirical political podcast called "Trump Trolls."
Your job is to write in the voice and style of Jon Stewart — the Jon Stewart who ran The Daily Show
from 1999-2015: smart, incredulous, exasperated, but fundamentally humanist and funny.

Jon Stewart's signature moves you must use:
- Quote the absurd thing VERBATIM first, then react to it with increasing disbelief
- The "What?! ... WHAT?!" slow build — start controlled, escalate to full explosion
- Rhetorical direct address: "Sir... SIR..."
- Historical comparisons that reframe the absurdity
- Deadpan pivot: present the crazy thing like it's normal, let the audience absorb it, then snap
- The resigned sign-off: "I don't know, man..."
- Self-awareness: occasionally acknowledge you can barely keep up
- Use actual quotes from the transcript as anchors — do not fabricate quotes

Tone rules:
- Punching at power, not at voters
- Exasperated love of democracy, not nihilism
- Funny because it's TRUE, not because it's mean
- Never personal appearance attacks

Output format: A TELEPROMPTER SCRIPT with these elements:
- [STAGE DIRECTION] — physical cues, facial expressions, pauses, prop use
- **EMPHASIS** — words to hit hard
- ... — natural pause beat
- (BEAT) — longer comedic pause, let it land
- [AUDIENCE LAUGH — WAIT] — hold for audience
- Approximate timing note at the top

Length: 750-1,400 words of spoken content (5-10 minutes).
Structure: Cold open → Main segment (3-4 beats) → Sign-off
"""

USER_PROMPT_TEMPLATE = """Here is today's Trump transcript to work from:

SOURCE: {source}
TITLE: {title}
DATE: {date}
URL: {url}

--- TRANSCRIPT ---
{transcript_excerpt}
--- END TRANSCRIPT ---

Write the full teleprompter script for today's "Trump Trolls" episode.
Pick the 2-4 most satirically rich moments from the transcript.
Open with the strongest moment as the cold open hook.
End with the Jon Stewart resignation sign-off.
"""

MAX_TRANSCRIPT_CHARS = 12_000  # ~3,000 words — enough context without blowing the prompt


def _trim_transcript(text: str) -> str:
    """Keep the first and last chunks — intros and sign-offs are usually the gold."""
    if len(text) <= MAX_TRANSCRIPT_CHARS:
        return text
    half = MAX_TRANSCRIPT_CHARS // 2
    return text[:half] + "\n\n[... transcript continues ...]\n\n" + text[-half:]


def generate_script(transcript: dict, model: str = "claude-opus-4-8") -> str:
    """
    Takes a transcript dict (from transcript_fetcher) and returns
    the full teleprompter script as a string.
    """
    client = anthropic.Anthropic()

    excerpt = _trim_transcript(transcript["text"])

    user_message = USER_PROMPT_TEMPLATE.format(
        source=transcript["source"],
        title=transcript["title"],
        date=transcript["date"],
        url=transcript["url"],
        transcript_excerpt=excerpt,
    )

    response = client.messages.create(
        model=model,
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )

    return response.content[0].text
