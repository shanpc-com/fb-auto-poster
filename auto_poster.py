#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from app.ai import enrich_with_ai
from app.config import BASE_DIR, load_settings
from app.facebook import FacebookPoster
from app.keywords import KeywordItem, load_keywords
from app.sources import SoftwareData, SourceFetcher

KEYWORDS_PATH = BASE_DIR / "keywords.csv"
LOG_PATH = BASE_DIR / "posted_log.json"


def load_log() -> dict:
    if not LOG_PATH.exists():
        return {"posted": [], "failed": []}
    try:
        value = json.loads(LOG_PATH.read_text(encoding="utf-8"))
        value.setdefault("posted", [])
        value.setdefault("failed", [])
        return value
    except (json.JSONDecodeError, OSError):
        return {"posted": [], "failed": []}


def save_log(log: dict) -> None:
    LOG_PATH.write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8")


def build_message(item: KeywordItem, data: SoftwareData, site_link: str, description: str, features: list[str], hashtags: list[str]) -> str:
    lines = [item.display_title, "", "📥 Download Now:", site_link, ""]
    details = [
        ("📦 Version", data.version), ("🏢 Developer", data.developer),
        ("💻 Platform", data.operating_system), ("📄 License", data.license_name),
        ("💾 File Size", data.file_size), ("📅 Updated", data.release_date),
    ]
    for label, value in details:
        if value:
            lines.append(f"{label}: {value}")
    if any(value for _, value in details):
        lines.append("")
    if description:
        lines.extend(["📝 About", description[:900], ""])
    if features:
        lines.append("✨ Key Features")
        lines.extend(f"• {feature}" for feature in features[:5])
        lines.append("")
    if data.source_name:
        lines.extend([f"Information source: {data.source_name}", ""])
    safe_tags = []
    for tag in hashtags:
        normalized = "".join(ch for ch in tag if ch.isalnum())
        if normalized and normalized.lower() not in {x.lower() for x in safe_tags}:
            safe_tags.append(normalized)
    if safe_tags:
        lines.append(" ".join(f"#{tag}" for tag in safe_tags[:8]))
    return "\n".join(lines).strip()


def main() -> int:
    try:
        settings = load_settings()
        items = load_keywords(KEYWORDS_PATH)
    except Exception as exc:
        print(f"[ERROR] Configuration failed: {exc}")
        return 2

    log = load_log()
    posted_originals = {entry["keyword"] if isinstance(entry, dict) else entry for entry in log["posted"]}
    remaining = [item for item in items if item.original not in posted_originals]
    if not remaining:
        print("[INFO] All keywords have been processed.")
        return 0

    fetcher = SourceFetcher(settings.source_domains, settings.request_timeout)
    poster = FacebookPoster(
        settings.page_id,
        settings.access_token,
        settings.graph_api_version,
        settings.request_timeout,
        album_id=settings.album_id,
    )
    completed = 0

    for item in remaining:
        if completed >= settings.posts_per_run:
            break
        print(f"[INFO] Processing: {item.search_term}")
        try:
            data = fetcher.fetch(item.search_term, item.source_url)
            if not data.title:
                data.title = item.display_title
            description, features, hashtags = enrich_with_ai(
                data, settings.ai_provider, settings.ai_api_key, settings.ai_model, settings.request_timeout
            )
            link = item.site_link or settings.site_link
            message = build_message(item, data, link, description, features, hashtags)
            print("[PREVIEW]\n" + message)

            if settings.dry_run:
                result = {"id": "dry-run"}
            else:
                result = poster.publish(message, link=link, image_url=data.image_url if settings.post_image else "")

            log["posted"].append({
                "keyword": item.original,
                "display_title": item.display_title,
                "facebook_post_id": result.get("post_id") or result.get("id"),
                "facebook_photo_id": result.get("id"),
                "facebook_album_id": result.get("album_id", ""),
                "facebook_album_url": result.get("album_url", ""),
                "publish_mode": result.get("mode", ""),
                "source_url": data.source_url,
                "posted_at": datetime.now(timezone.utc).isoformat(),
            })
            save_log(log)
            completed += 1
            published_id = result.get("post_id") or result.get("id")
            print(f"[SUCCESS] Posted: {published_id}")
            if result.get("album_url"):
                print(f"[ALBUM] {result['album_url']}")
        except Exception as exc:
            print(f"[ERROR] Failed for '{item.search_term}': {exc}")
            log["failed"].append({"keyword": item.original, "error": str(exc), "failed_at": datetime.now(timezone.utc).isoformat()})
            save_log(log)

    if completed == 0:
        print("[ERROR] No post was published in this run.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
