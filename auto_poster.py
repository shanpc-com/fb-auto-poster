#!/usr/bin/env python3
from __future__ import annotations
import sys
from datetime import datetime, timezone
from app.ai import enrich_with_ai
from app.config import BASE_DIR, load_settings
from app.facebook import FacebookPoster
from app.keywords import load_keywords
from app.image_processor import prepare_post_image
from app.logger import setup_logger
from app.sources import SourceFetcher
from app.utils import load_json, save_json

KEYWORDS=BASE_DIR/"keywords.csv"; LOG=BASE_DIR/"posted_log.json"
logger=setup_logger(BASE_DIR/"logs")

def message(item,data,link,desc,features,tags):
    # Facebook has no separate SEO title field for a normal Page photo post.
    # The first caption line therefore acts as the visible title and the most
    # important text for search snippets.
    title = item.display_title.strip()
    lines=[title,"",f"Download Here 👉 {link}",""]
    for label,val in [("📦 Version",data.version),("🏢 Developer",data.developer),("💻 Platform",data.operating_system),("📄 License",data.license_name),("💾 File Size",data.file_size),("📅 Updated",data.release_date)]:
        if val: lines.append(f"{label}: {val}")
    if any((data.version,data.developer,data.operating_system,data.license_name,data.file_size,data.release_date)): lines.append("")
    lines += ["📝 About",desc,""]
    if features: lines += ["✨ Key Features"]+[f"• {x}" for x in features[:5]]+[""]
    if data.source_name: lines += [f"Information source: {data.source_name}",""]
    lines.append(" ".join("#"+"".join(c for c in t if c.isalnum()) for t in tags if t))
    return "\n".join(lines).strip()

def main():
    try: s=load_settings(); items=load_keywords(KEYWORDS,s.lawful_content_only)
    except Exception as e: logger.error("Configuration failed: %s",e); return 2
    log=load_json(LOG,{"posted":[],"failed":[]}); log.setdefault("posted",[]); log.setdefault("failed",[])
    posted={x.get("keyword") if isinstance(x,dict) else x for x in log["posted"]}
    remaining=[x for x in items if x.original not in posted]
    if not remaining: logger.info("All eligible keywords have been processed."); return 0
    fetcher=SourceFetcher(s.source_domains,s.request_timeout,s.max_source_results,s.min_image_width,s.min_image_height)
    fb=FacebookPoster(s.page_id,s.access_token,s.graph_api_version,s.request_timeout)
    done=0
    for item in remaining:
        if done>=s.posts_per_run: break
        logger.info("Processing: %s",item.search_term)
        try:
            data=fetcher.fetch(item.search_term,item.source_url); data.title=data.title or item.display_title
            desc,features,tags=enrich_with_ai(data,s.ai_provider,s.ai_api_key,s.ai_model,s.request_timeout)
            caption=message(item,data,item.site_link or s.site_link,desc,features,tags)
            print("[PREVIEW]\n"+caption)
            image_path, image_mode = prepare_post_image(item.display_title, data.image_url, BASE_DIR/"assets"/"current-post.jpg", s.request_timeout)
            logger.info("Prepared post image (%s): %s", image_mode, image_path)
            result={"id":"dry-run","post_id":"dry-run","permalink_url":"","mode":"dry_run"} if s.dry_run else fb.publish_photo_file(caption,image_path)
            log["posted"].append({"keyword":item.original,"display_title":item.display_title,"facebook_post_id":result["post_id"],"facebook_photo_id":result["id"],"facebook_permalink":result.get("permalink_url", ""),"publish_mode":result["mode"],"image_url":data.image_url,"image_mode":image_mode,"source_url":data.source_url,"posted_at":datetime.now(timezone.utc).isoformat()})
            save_json(LOG,log); done+=1; logger.info("SUCCESS verified photo post: %s",result["post_id"]); logger.info("Facebook permalink: %s", result.get("permalink_url", ""))
        except Exception as e:
            logger.error("Failed for '%s': %s",item.search_term,e)
            log["failed"].append({"keyword":item.original,"error":str(e),"failed_at":datetime.now(timezone.utc).isoformat()}); save_json(LOG,log)
    if done==0: logger.error("No photo post was published in this run."); return 1
    return 0
if __name__=="__main__": sys.exit(main())
