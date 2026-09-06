#!/usr/bin/env python3
"""
Fieldnotes autonomous content generator.

Picks the next unused topic from topics.json, asks Claude to write a full
article in the site's voice, and saves it as a markdown file with frontmatter
into /posts. Designed to be run on a schedule (see .github/workflows/publish.yml)
with zero human input.

Requires: ANTHROPIC_API_KEY environment variable (set as a GitHub Actions secret).
"""

import json
import os
import re
import sys
import time
import urllib.request
import urllib.error
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOPICS_FILE = ROOT / "topics.json"
POSTS_DIR = ROOT / "posts"
STATE_FILE = ROOT / "state.json"
MODEL = "claude-sonnet-4-6"
API_URL = "https://api.anthropic.com/v1/messages"

SYSTEM_PROMPT = """You are the sole writer for Fieldnotes, a small independent \
publication of practical dispatches on remote work and solo-professional \
productivity. Voice: direct, specific, a little dry, no hype, no exclamation \
points, no "in today's fast-paced world" filler. You write like someone who \
has actually tried the thing, not like marketing copy.

Rules:
- Never invent statistics, studies, or specific product claims you can't be sure of.
- Never name a specific software product's pricing, feature list, or version \
  number unless it is extremely well-established and unlikely to be wrong \
  (if unsure, describe the category of tool instead, e.g. "a habit tracker" \
  rather than a specific app name with claimed specs).
- Structure: a short opening (2-3 sentences, no throat-clearing), then 3-5 \
  sections with plain sentence-case headers (##), then a short closing \
  paragraph. No numbered "tips 1-10" listicle format unless the topic is \
  genuinely a sequence.
- Length: 600-900 words.
- Include exactly one "## Try this" section near the end with one concrete, \
  actionable exercise the reader can do in under 15 minutes.
- Output ONLY the article body in markdown. No title (that's handled \
  separately), no frontmatter, no preamble, no "Here is the article".
"""

TITLE_SYSTEM_PROMPT = """Write ONE short, specific, non-clickbait title (under \
9 words, sentence case, no colons-as-crutch, no "The Ultimate Guide") for the \
article topic given. Output ONLY the title text, nothing else."""


def call_claude(system, user_message, max_tokens=2000):
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY environment variable is not set.", file=sys.stderr)
        sys.exit(1)

    body = json.dumps({
        "model": MODEL,
        "max_tokens": max_tokens,
        "system": system,
        "messages": [{"role": "user", "content": user_message}],
    }).encode("utf-8")

    req = urllib.request.Request(
        API_URL,
        data=body,
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )

    last_err = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                parts = [b["text"] for b in data.get("content", []) if b.get("type") == "text"]
                return "".join(parts).strip()
        except urllib.error.HTTPError as e:
            last_err = e
            if e.code == 529 or e.code == 429:
                time.sleep(5 * (attempt + 1))
                continue
            raise
    raise last_err


def slugify(text):
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"[\s]+", "-", text)
    return text[:60].strip("-")


def load_topics():
    with open(TOPICS_FILE) as f:
        return json.load(f)


def load_state():
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            return json.load(f)
    return {"used_topics": []}


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def next_topic(topics, state):
    used = set(state.get("used_topics", []))
    for t in topics:
        if t["id"] not in used:
            return t
    # All topics used: recycle from the start rather than stopping forever.
    state["used_topics"] = []
    return topics[0]


def main():
    topics = load_topics()
    state = load_state()
    topic = next_topic(topics, state)

    print(f"Generating article for topic: {topic['id']} — {topic['prompt']}")

    title = call_claude(TITLE_SYSTEM_PROMPT, topic["prompt"], max_tokens=50)
    title = title.strip().strip('"')

    body = call_claude(SYSTEM_PROMPT, topic["prompt"], max_tokens=2000)

    today = date.today().isoformat()
    slug = f"{today}-{slugify(title)}"
    frontmatter = (
        "---\n"
        f"title: {json.dumps(title)}\n"
        f"date: {today}\n"
        f"topic_id: {topic['id']}\n"
        f"tags: {json.dumps(topic.get('tags', []))}\n"
        f"affiliate_cta: {json.dumps(topic.get('affiliate_cta', ''))}\n"
        "---\n\n"
    )

    out_path = POSTS_DIR / f"{slug}.md"
    out_path.write_text(frontmatter + body, encoding="utf-8")
    print(f"Wrote {out_path}")

    state.setdefault("used_topics", []).append(topic["id"])
    state["last_run"] = datetime.utcnow().isoformat() + "Z"
    save_state(state)


if __name__ == "__main__":
    main()
