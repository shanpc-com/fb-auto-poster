from __future__ import annotations
import json, os
from dataclasses import dataclass
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

def _bool(v, default=False):
    if v is None: return default
    return str(v).strip().lower() in {"1","true","yes","on"}

def _int(v, default):
    try: return int(v)
    except (TypeError, ValueError): return default

@dataclass(frozen=True)
class Settings:
    page_id: str; access_token: str; site_link: str
    graph_api_version: str = "v25.0"
    posts_per_run: int = 1
    post_image: bool = True
    dry_run: bool = False
    request_timeout: int = 25
    max_source_results: int = 4
    min_image_width: int = 240
    min_image_height: int = 160
    ai_provider: str = "none"
    ai_api_key: str = ""
    ai_model: str = ""
    source_domains: tuple[str,...] = ("filehippo.com","filehorse.com","softpedia.com","sourceforge.net","uptodown.com")
    lawful_content_only: bool = True

def load_settings() -> Settings:
    file_data = {}
    config_path = BASE_DIR / "config.json"
    if config_path.exists():
        file_data = json.loads(config_path.read_text(encoding="utf-8"))
    def get(name, default=""):
        return os.getenv(name, file_data.get(name.lower(), default))
    domains = get("SOURCE_DOMAINS", ",".join(Settings.__dataclass_fields__["source_domains"].default))
    settings = Settings(
        page_id=str(get("FB_PAGE_ID", get("FACEBOOK_PAGE_ID", ""))).strip(),
        access_token=str(get("FB_ACCESS_TOKEN", get("FACEBOOK_ACCESS_TOKEN", ""))).strip(),
        site_link=str(get("FIXED_LINK", get("SITE_LINK", ""))).strip(),
        graph_api_version=str(get("GRAPH_API_VERSION", "v25.0")).strip(),
        posts_per_run=max(1, _int(get("POSTS_PER_RUN", 1), 1)),
        post_image=_bool(get("POST_IMAGE", True), True),
        dry_run=_bool(get("DRY_RUN", False), False),
        request_timeout=max(5, _int(get("REQUEST_TIMEOUT", 25), 25)),
        max_source_results=max(1, _int(get("MAX_SOURCE_RESULTS", 4), 4)),
        min_image_width=max(100, _int(get("MIN_IMAGE_WIDTH", 240), 240)),
        min_image_height=max(100, _int(get("MIN_IMAGE_HEIGHT", 160), 160)),
        ai_provider=str(get("AI_PROVIDER", "none")).lower(),
        ai_api_key=str(get("AI_API_KEY", "")),
        ai_model=str(get("AI_MODEL", "")),
        source_domains=tuple(x.strip().lower() for x in str(domains).split(",") if x.strip()),
        lawful_content_only=_bool(get("LAWFUL_CONTENT_ONLY", True), True),
    )
    if not settings.dry_run:
        missing = [n for n,v in (("FB_PAGE_ID",settings.page_id),("FB_ACCESS_TOKEN",settings.access_token),("FIXED_LINK",settings.site_link)) if not v]
        if missing: raise ValueError("Missing required settings: " + ", ".join(missing))
    if not settings.post_image: raise ValueError("POST_IMAGE must be true in v5 strict photo mode.")
    return settings
