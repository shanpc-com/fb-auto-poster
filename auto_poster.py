#!/usr/bin/env python3
"""
Facebook Auto Poster
---------------------
Reads a list of keywords (from a CSV file), builds a post using a fixed
template + fixed link, and publishes it to a Facebook Page via the
Graph API. Designed to be run on a schedule (e.g. GitHub Actions cron,
a server cron job, or manually).

HOW IT WORKS
1. Keywords come from keywords.csv (one keyword per line, column "keyword").
2. Each run, the script picks the NEXT unposted keyword (tracked in
   posted_log.json so it never repeats one automatically).
3. It builds the message using TEMPLATE from config.json, where:
      {keyword} -> replaced with the keyword
      {link}    -> replaced with your fixed LINK from config.json
4. It posts the text to your Facebook Page using the Graph API.

This script only posts TEXT. No AI text/image generation is used —
keeps things simple, transparent, and fully under your control.
"""

import json
import os
import sys
import requests
from pathlib import Path

BASE_DIR = Path(__file__).parent
CONFIG_PATH = BASE_DIR / "config.json"
KEYWORDS_PATH = BASE_DIR / "keywords.csv"
LOG_PATH = BASE_DIR / "posted_log.json"


def load_config():
    if not CONFIG_PATH.exists():
        sys.exit(f"[ERROR] config.json not found. Copy config.example.json -> config.json and fill it in.")
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def load_keywords():
    if not KEYWORDS_PATH.exists():
        sys.exit(f"[ERROR] keywords.csv not found. Add your keywords there (one per line, header 'keyword').")
    keywords = []
    with open(KEYWORDS_PATH, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]
    # skip header if present
    if lines and lines[0].lower() == "keyword":
        lines = lines[1:]
    return lines


def load_posted_log():
    if LOG_PATH.exists():
        with open(LOG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"posted": []}


def save_posted_log(log):
    with open(LOG_PATH, "w", encoding="utf-8") as f:
        json.dump(log, f, indent=2, ensure_ascii=False)


def build_message(template: str, keyword: str, link: str) -> str:
    return template.replace("{keyword}", keyword).replace("{link}", link)


def post_to_facebook(page_id: str, access_token: str, message: str):
    url = f"https://graph.facebook.com/v19.0/{page_id}/feed"
    payload = {"message": message, "access_token": access_token}
    resp = requests.post(url, data=payload, timeout=30)
    if resp.status_code != 200:
        sys.exit(f"[ERROR] Facebook API error: {resp.status_code} - {resp.text}")
    return resp.json()


def main():
    config = load_config()
    keywords = load_keywords()
    log = load_posted_log()

    remaining = [k for k in keywords if k not in log["posted"]]

    if not remaining:
        print("[INFO] All keywords have been posted. Add more to keywords.csv, "
              "or clear posted_log.json to start over.")
        return

    # How many posts to publish this run (default 1, configurable)
    batch_size = config.get("posts_per_run", 1)
    batch = remaining[:batch_size]

    for keyword in batch:
        message = build_message(config["template"], keyword, config["link"])
        print(f"[INFO] Posting: {message}")

        result = post_to_facebook(config["facebook_page_id"], config["facebook_access_token"], message)
        print(f"[SUCCESS] Posted. Facebook post id: {result.get('id')}")

        log["posted"].append(keyword)
        save_posted_log(log)


if __name__ == "__main__":
    main()
