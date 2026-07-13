from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def _env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


def _as_bool(value: str | bool | None, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    page_id: str
    access_token: str
    site_link: str
    graph_api_version: str = "v23.0"
    posts_per_run: int = 1
    ai_provider: str = "none"
    ai_api_key: str = ""
    ai_model: str = ""
    post_image: bool = True
    dry_run: bool = False
    request_timeout: int = 25
    source_domains: tuple[str, ...] = (
        "filehippo.com", "filehorse.com", "uptodown.com", "download.cnet.com",
        "softpedia.com", "softonic.com", "sourceforge.net"
    )


def load_settings() -> Settings:
    cfg_path = BASE_DIR / "config.json"
    cfg: dict = {}
    if cfg_path.exists():
        cfg = json.loads(cfg_path.read_text(encoding="utf-8"))

    page_id = _env("FB_PAGE_ID", str(cfg.get("facebook_page_id", "")))
    token = _env("FB_ACCESS_TOKEN", str(cfg.get("facebook_access_token", "")))
    site_link = _env("FIXED_LINK", str(cfg.get("link", "")))
    provider = _env("AI_PROVIDER", str(cfg.get("ai_provider", "none"))).lower()
    api_key = _env("AI_API_KEY", str(cfg.get("ai_api_key", "")))
    model = _env("AI_MODEL", str(cfg.get("ai_model", "")))

    dry_run = _as_bool(_env("DRY_RUN", str(cfg.get("dry_run", "false"))))
    if not dry_run:
        missing = [name for name, value in {
            "FB_PAGE_ID": page_id,
            "FB_ACCESS_TOKEN": token,
            "FIXED_LINK": site_link,
        }.items() if not value]
        if missing:
            raise ValueError("Missing required settings: " + ", ".join(missing))

    if provider not in {"none", "groq", "gemini"}:
        raise ValueError("AI_PROVIDER must be none, groq, or gemini")
    if provider != "none" and not api_key:
        raise ValueError("AI_API_KEY is required when AI_PROVIDER is enabled")

    default_model = "llama-3.3-70b-versatile" if provider == "groq" else "gemini-2.5-flash"
    domains = cfg.get("source_domains") or list(Settings.source_domains)

    return Settings(
        page_id=page_id,
        access_token=token,
        site_link=site_link,
        graph_api_version=_env("GRAPH_API_VERSION", str(cfg.get("graph_api_version", "v23.0"))),
        posts_per_run=max(1, int(_env("POSTS_PER_RUN", str(cfg.get("posts_per_run", 1))))),
        ai_provider=provider,
        ai_api_key=api_key,
        ai_model=model or default_model,
        post_image=_as_bool(_env("POST_IMAGE", str(cfg.get("post_image", "true"))), True),
        dry_run=dry_run,
        request_timeout=max(10, int(cfg.get("request_timeout", 25))),
        source_domains=tuple(domains),
    )
