#!/usr/bin/env python3
"""
Builds the static Fieldnotes site from markdown posts into /docs (GitHub
Pages serves from /docs on the main branch, so no separate branch or build
step is needed). Run after generate_content.py, or on its own to rebuild
the whole site after a template change.

Requires: pip install markdown (already in requirements.txt)
"""

import json
import re
from datetime import datetime
from pathlib import Path

import markdown as md

ROOT = Path(__file__).resolve().parent.parent
POSTS_DIR = ROOT / "posts"
OUT_DIR = ROOT / "docs"
ASSETS_DIR = ROOT / "assets"

SITE_NAME = "Fieldnotes"
SITE_TAGLINE = "Dispatches on working alone, well."
# Fill these in once your accounts are approved — see README "Turning on money".
ADSENSE_CLIENT_ID = ""          # e.g. "ca-pub-1234567890123456"
AFFILIATE_DISCLOSURE = (
    "Fieldnotes may earn a commission from links on this page, at no cost to you."
)

AD_SLOT_HTML = """
<div class="ad-slot" aria-label="advertisement">
  <!-- Paste your AdSense (or other network) unit code here, or leave blank
       until you're approved — an empty slot just renders nothing. -->
</div>
""".strip()

BASE_CSS_LINK = '<link rel="stylesheet" href="{prefix}assets/style.css">'


def read_posts():
    posts = []
    for path in sorted(POSTS_DIR.glob("*.md"), reverse=True):
        text = path.read_text(encoding="utf-8")
        fm_match = re.match(r"^---\n(.*?)\n---\n\n(.*)$", text, re.DOTALL)
        if not fm_match:
            continue
        fm_raw, body = fm_match.groups()
        meta = {}
        for line in fm_raw.splitlines():
            key, _, val = line.partition(":")
            key = key.strip()
            val = val.strip()
            try:
                meta[key] = json.loads(val)
            except json.JSONDecodeError:
                meta[key] = val
        meta["slug"] = path.stem
        meta["body_html"] = md.markdown(body, extensions=["extra"])
        posts.append(meta)
    return posts


def page_shell(title, content, prefix="", description=""):
    desc = description or SITE_TAGLINE
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
{BASE_CSS_LINK.format(prefix=prefix)}
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,600;1,8..60,400&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">
</head>
<body>
<header class="site-header">
  <a class="wordmark" href="{prefix}index.html">{SITE_NAME}</a>
  <span class="tagline">{SITE_TAGLINE}</span>
</header>
<main>
{content}
</main>
<footer class="site-footer">
  <p>{AFFILIATE_DISCLOSURE}</p>
</footer>
</body>
</html>"""


def render_post_page(post, index):
    ad = AD_SLOT_HTML if ADSENSE_CLIENT_ID else ""
    cta = post.get("affiliate_cta") or ""
    cta_html = ""
    if cta:
        cta_html = f"""
<aside class="field-note">
  <p class="field-note__label">Field note</p>
  <p>If this is a recurring problem for you, it's usually worth having
  {cta} on hand rather than solving it from scratch each time.</p>
</aside>"""
    entry_no = f"{index:03d}"
    tags = ", ".join(post.get("tags", []))
    content = f"""
<article class="post">
  <p class="post__meta">No. {entry_no} — {post.get('date','')}{(' — ' + tags) if tags else ''}</p>
  <h1>{post.get('title','Untitled')}</h1>
  <div class="post__body">
    {post['body_html']}
  </div>
  {cta_html}
  {ad}
  <p class="back-link"><a href="../index.html">&larr; All dispatches</a></p>
</article>"""
    return page_shell(f"{post.get('title','Untitled')} — {SITE_NAME}", content, prefix="../",
                       description=post.get("title", ""))


def render_index(posts):
    rows = []
    for i, post in enumerate(posts):
        n = len(posts) - i
        tags = ", ".join(post.get("tags", []))
        rows.append(f"""
<a class="entry" href="posts/{post['slug']}.html">
  <span class="entry__no">No. {n:03d}</span>
  <span class="entry__title">{post.get('title','Untitled')}</span>
  <span class="entry__meta">{post.get('date','')}{(' · ' + tags) if tags else ''}</span>
</a>""")
    content = f"""
<section class="log">
{''.join(rows) if rows else '<p class="empty">First dispatch is on its way.</p>'}
</section>"""
    return page_shell(SITE_NAME, content, prefix="")


def main():
    OUT_DIR.mkdir(exist_ok=True)
    (OUT_DIR / "posts").mkdir(exist_ok=True)
    (OUT_DIR / "assets").mkdir(exist_ok=True)

    posts = read_posts()

    for css_file in ASSETS_DIR.glob("*.css"):
        (OUT_DIR / "assets" / css_file.name).write_text(
            css_file.read_text(encoding="utf-8"), encoding="utf-8"
        )

    for i, post in enumerate(posts):
        n = len(posts) - i
        html = render_post_page(post, n)
        (OUT_DIR / "posts" / f"{post['slug']}.html").write_text(html, encoding="utf-8")

    (OUT_DIR / "index.html").write_text(render_index(posts), encoding="utf-8")

    # .nojekyll so GitHub Pages serves files as-is
    (OUT_DIR / ".nojekyll").write_text("", encoding="utf-8")

    print(f"Built {len(posts)} post(s) into {OUT_DIR}")


if __name__ == "__main__":
    main()
