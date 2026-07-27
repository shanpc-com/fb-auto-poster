#!/usr/bin/env python3
from __future__ import annotations
import sys
from datetime import datetime, timezone
from app.ai import enrich_with_ai
from app.content_engine import build_ranked_content
from app.config import BASE_DIR, load_settings
from app.facebook import FacebookPoster
from app.keywords import load_keywords
from app.image_processor import prepare_post_image
from app.logger import setup_logger
from app.sources import SourceFetcher
from app.utils import load_json, save_json

KEYWORDS = BASE_DIR / "keywords.csv"
LOG = BASE_DIR / "posted_log.json"
STATUS = BASE_DIR / "logs" / "last-publish-status.json"
logger = setup_logger(BASE_DIR / "logs")

def main():
    try:
        settings = load_settings()
        items = load_keywords(KEYWORDS, settings.lawful_content_only)
    except Exception as exc:
        logger.error("Configuration failed: %s", exc)
        return 2

    log = load_json(LOG, {"posted": [], "failed": []})
    log.setdefault("posted", [])
    log.setdefault("failed", [])
    posted = {x.get("keyword") if isinstance(x, dict) else x for x in log["posted"]}
    remaining = [x for x in items if x.original not in posted]
    if not remaining:
        logger.info("All eligible keywords have been processed.")
        return 0

    fetcher = SourceFetcher(settings.source_domains, settings.request_timeout, settings.max_source_results, settings.min_image_width, settings.min_image_height)
    fb = FacebookPoster(settings.page_id, settings.access_token, settings.graph_api_version, settings.request_timeout)

    if not settings.dry_run:
        page = fb.verify_page()
        logger.info("Verified Page: %s (@%s) %s", page["name"], page["username"], page["link"])
    else:
        page = {"id": "dry-run", "name": "Dry Run", "username": "", "link": ""}

    done = 0
    for item in remaining:
        if done >= settings.posts_per_run:
            break
        logger.info("Processing: %s", item.search_term)
        try:
            data = fetcher.fetch(item.search_term, item.source_url)
            data.title = data.title or item.display_title
            desc, features, tags = enrich_with_ai(data, settings.ai_provider, settings.ai_api_key, settings.ai_model, settings.request_timeout)
            ranked = build_ranked_content(item, data, item.site_link or settings.site_link, desc, features, tags)
            caption = ranked.caption
            print(f"[POST PREVIEW | category={ranked.category} | quality={ranked.quality_score}/100]\n" + caption)
            image_path, image_mode = prepare_post_image(
                item.display_title,
                data.image_url,
                BASE_DIR / "assets" / "current-post.jpg",
                settings.request_timeout,
                ranked.category,
            )
            logger.info("Prepared post image (%s): %s", image_mode, image_path)

            if settings.dry_run:
                result = {"id": "dry-run", "post_id": "dry-run", "verified_object_id": "dry-run", "permalink_url": "", "created_time": "", "is_published": True, "full_picture": "", "mode": "dry_run", "album_id": settings.album_id, "album_url": FacebookPoster.album_url(settings.album_id)}
            elif settings.album_id:
                try:
                    result = fb.publish_to_album(settings.album_id, caption, image_path)
                    logger.info("Published into existing album: %s", result.get("album_url", ""))
                except Exception as album_exc:
                    if not settings.album_fallback_to_page:
                        raise
                    logger.warning("Album upload failed; falling back to normal Page photo: %s", album_exc)
                    result = fb.publish_photo_file(caption, image_path)
                    result["album_error"] = str(album_exc)
            else:
                result = fb.publish_photo_file(caption, image_path)
            record = {
                "keyword": item.original,
                "display_title": item.display_title,
                "category": ranked.category,
                "primary_keyword": ranked.primary_keyword,
                "secondary_keywords": list(ranked.secondary_keywords),
                "hashtags": list(ranked.hashtags),
                "caption_template_id": ranked.template_id,
                "content_quality_score": ranked.quality_score,
                "facebook_page": page,
                "facebook_post_id": result["post_id"],
                "facebook_photo_id": result["id"],
                "verified_object_id": result.get("verified_object_id", ""),
                "facebook_permalink": result.get("permalink_url", ""),
                "facebook_is_published": result.get("is_published", True),
                "facebook_created_time": result.get("created_time", ""),
                "facebook_full_picture": result.get("full_picture", ""),
                "publish_mode": result["mode"],
                "facebook_album_id": result.get("album_id", ""),
                "facebook_album_url": result.get("album_url", ""),
                "album_error": result.get("album_error", ""),
                "image_url": data.image_url,
                "image_mode": image_mode,
                "source_url": data.source_url,
                "posted_at": datetime.now(timezone.utc).isoformat(),
            }
            log["posted"].append(record)
            save_json(LOG, log)
            save_json(STATUS, {"status": "success", **record})
            done += 1
            logger.info("SUCCESS verified published photo: %s", result["post_id"])
            logger.info("Clean public permalink: %s", result.get("permalink_url", ""))
            if result.get("album_url"):
                logger.info("Facebook album URL: %s", result.get("album_url"))
        except Exception as exc:
            logger.error("Failed for '%s': %s", item.search_term, exc)
            failure = {"keyword": item.original, "error": str(exc), "failed_at": datetime.now(timezone.utc).isoformat()}
            log["failed"].append(failure)
            save_json(LOG, log)
            save_json(STATUS, {"status": "failed", **failure})

    if done == 0:
        logger.error("No photo post was published in this run.")
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())
