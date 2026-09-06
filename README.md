# Fieldnotes — an autonomous content business

A niche site (remote work / solo-professional productivity) that writes,
publishes, and formats its own articles twice a week, forever, with no
ongoing human involvement — after a one-time setup that takes about 30–45
minutes.

Read this whole file before you start. It tells you exactly which parts need
a human once, and which parts never need a human again.

## What's autonomous vs. what isn't

**Fully autonomous, forever, once set up:**
- Picking the next topic
- Writing the article (Claude API)
- Formatting it into the site's HTML/CSS
- Publishing it (git commit + push, triggered by a schedule)
- Hosting (GitHub Pages, free, no server to maintain)

**Requires a human once, up front (can't be automated — these all require
identity verification or a human decision):**
- Creating the GitHub repo and turning this on
- Signing up for Google AdSense (or another ad network) — approval takes
  days to weeks and requires a real human account
- Signing up for affiliate programs (e.g. Amazon Associates) relevant to
  your topics
- Buying a domain, if you want one instead of the free `github.io` URL

**Might need a human occasionally (rare, but be aware):**
- If an ad network flags the site for a policy review
- If you want to expand the topic list (edit one JSON file, 2 minutes)

## One-time setup

1. **Create a new GitHub repository** and push everything in this folder to it.

2. **Get an Anthropic API key** from the Claude Console, and add it as a
   repository secret:
   `Settings → Secrets and variables → Actions → New repository secret`
   Name: `ANTHROPIC_API_KEY`

3. **Turn on GitHub Pages:**
   `Settings → Pages → Source: Deploy from a branch → Branch: main, folder: /docs`
   Your site will be live at `https://<your-username>.github.io/<repo-name>/`
   within a few minutes.

4. **Test it manually once** before waiting for the schedule: go to the
   **Actions** tab → **Autonomous publish** → **Run workflow**. Check that a
   new file appears in `/posts` and the site updates.

5. That's it. The workflow in `.github/workflows/publish.yml` runs on its
   own from here — Monday and Thursday at 13:00 UTC by default. Edit the
   `cron` line in that file to change the schedule.

## Turning on money (the part that needs a human)

The site is built to accept both revenue streams without any code changes:

- **Ads:** once approved for AdSense, paste your ad unit's snippet into the
  `AD_SLOT_HTML` block in `scripts/build_site.py` and set `ADSENSE_CLIENT_ID`
  at the top of that file. Every future post gets it automatically.
- **Affiliate links:** each topic in `topics.json` has an `affiliate_cta`
  field describing the category of product to suggest — this becomes a
  "Field note" callout box on the article. Once you have real affiliate
  links, you can either edit the callout text in `build_site.py` to include
  them, or reply on specific posts by hand (rare exception to "no human
  touch," but a one-line edit).

Until you've done this, the site runs and grows exactly the same way —
it just doesn't earn anything yet, so there's no rush and nothing breaks
by waiting.

## Growing it

- Add more entries to `topics.json` any time — the generator works through
  them in order and loops back around when the list is exhausted, so it
  never runs dry.
- Want a different niche entirely? Rewrite `SYSTEM_PROMPT` in
  `scripts/generate_content.py` and replace `topics.json`. Everything else
  (scheduling, publishing, styling) stays the same.
- Want a real domain instead of `github.io`? Buy one, then add a `CNAME`
  file to `/docs` with the domain name in it, and point the domain's DNS at
  GitHub Pages.

## Files

```
scripts/generate_content.py   the writer — calls Claude, saves a markdown post
scripts/build_site.py         the publisher — turns markdown into the live HTML site
topics.json                   the queue of article topics (edit to add more)
posts/                        generated (and seed) markdown articles
docs/                         the built, live site — do not edit by hand, it's regenerated
assets/style.css              the site's visual design
.github/workflows/publish.yml the schedule that makes this autonomous
state.json                    tracks which topics have been used (auto-created)
```
