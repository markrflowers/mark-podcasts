#!/usr/bin/env python3
"""Add one MP3 episode to Mark's private podcast feed and rebuild feed.xml.

Run from a clone of the mark-podcasts repo:

    python3 tools/publish.py --mp3 /path/The_Monday_Ledger_2026-11-30.mp3 \
        --show "The Monday Ledger" --title "Fed minutes, Nvidia, holiday retail" \
        --description "Short summary of the episode..."

Then commit and push (see README.md). Uses only the Python standard library
plus ffprobe for the duration.
"""
import argparse
import datetime as dt
import email.utils
import json
import os
import re
import shutil
import subprocess
import sys
from xml.sax.saxutils import escape

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EP_DIR = os.path.join(ROOT, "episodes")
DB = os.path.join(ROOT, "episodes.json")
CONFIG = os.path.join(ROOT, "config.json")
KEEP_PER_SHOW = 6  # older episodes are dropped to keep the site small


def duration_seconds(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", path],
        capture_output=True, text=True, check=True).stdout.strip()
    return int(round(float(out)))


def hms(sec):
    return f"{sec // 3600}:{sec % 3600 // 60:02d}:{sec % 60:02d}"


def build_feed(cfg, episodes):
    base = cfg["base_url"].rstrip("/")
    items = []
    for ep in sorted(episodes, key=lambda e: e["published"], reverse=True):
        url = f"{base}/episodes/{ep['file']}"
        pub = email.utils.format_datetime(dt.datetime.fromisoformat(ep["published"]))
        title = f"{ep['show']}: {ep['title']}" if ep.get("title") else ep["show"]
        items.append(f"""    <item>
      <title>{escape(title)}</title>
      <description>{escape(ep.get('description', ''))}</description>
      <itunes:summary>{escape(ep.get('description', ''))}</itunes:summary>
      <itunes:author>{escape(ep['show'])}</itunes:author>
      <enclosure url="{escape(url)}" length="{ep['bytes']}" type="audio/mpeg"/>
      <guid isPermaLink="false">{escape(ep['file'])}</guid>
      <pubDate>{pub}</pubDate>
      <itunes:duration>{hms(ep['seconds'])}</itunes:duration>
      <itunes:explicit>false</itunes:explicit>
      <itunes:episodeType>full</itunes:episodeType>
    </item>""")
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>{escape(cfg['title'])}</title>
    <link>{escape(base)}/</link>
    <atom:link href="{escape(base)}/feed.xml" rel="self" type="application/rss+xml"/>
    <description>{escape(cfg['description'])}</description>
    <language>en-us</language>
    <itunes:author>{escape(cfg['author'])}</itunes:author>
    <itunes:image href="{escape(base)}/cover.jpg"/>
    <image><url>{escape(base)}/cover.jpg</url><title>{escape(cfg['title'])}</title><link>{escape(base)}/</link></image>
    <itunes:category text="News"><itunes:category text="Business News"/></itunes:category>
    <itunes:explicit>false</itunes:explicit>
    <itunes:type>episodic</itunes:type>
    <itunes:block>Yes</itunes:block>
    <lastBuildDate>{email.utils.format_datetime(dt.datetime.now(dt.timezone.utc))}</lastBuildDate>
{chr(10).join(items)}
  </channel>
</rss>
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mp3", help="MP3 file to add (omit to just rebuild the feed)")
    ap.add_argument("--show", help='Show name, e.g. "The Monday Ledger"')
    ap.add_argument("--title", default="", help="Episode headline topics")
    ap.add_argument("--description", default="", help="Episode summary")
    a = ap.parse_args()

    cfg = json.load(open(CONFIG))
    episodes = json.load(open(DB)) if os.path.exists(DB) else []
    os.makedirs(EP_DIR, exist_ok=True)

    if a.mp3:
        if not a.show:
            sys.exit("--show is required with --mp3")
        name = re.sub(r"[^A-Za-z0-9._-]", "_", os.path.basename(a.mp3))
        shutil.copyfile(a.mp3, os.path.join(EP_DIR, name))
        episodes = [e for e in episodes if e["file"] != name]
        episodes.append({
            "file": name, "show": a.show, "title": a.title.strip(),
            "description": a.description.strip(),
            "bytes": os.path.getsize(os.path.join(EP_DIR, name)),
            "seconds": duration_seconds(os.path.join(EP_DIR, name)),
            "published": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        })

    # keep only the newest KEEP_PER_SHOW episodes of each show
    kept = []
    for show in {e["show"] for e in episodes}:
        eps = sorted((e for e in episodes if e["show"] == show),
                     key=lambda e: e["published"], reverse=True)
        kept += eps[:KEEP_PER_SHOW]
    keep_files = {e["file"] for e in kept}
    for f in os.listdir(EP_DIR):
        if f.endswith(".mp3") and f not in keep_files:
            os.remove(os.path.join(EP_DIR, f))

    json.dump(sorted(kept, key=lambda e: e["published"]), open(DB, "w"), indent=2)
    open(os.path.join(ROOT, "feed.xml"), "w").write(build_feed(cfg, kept))
    print(f"feed.xml rebuilt with {len(kept)} episode(s)")


if __name__ == "__main__":
    main()
