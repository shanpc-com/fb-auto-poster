from __future__ import annotations
from pathlib import Path
import requests

class FacebookPoster:
    def __init__(self, page_id, access_token, version="v25.0", timeout=25):
        self.page_id = page_id
        self.token = access_token
        self.version = version
        self.timeout = timeout

    def publish_photo_file(self, caption: str, image_path: Path):
        url = f"https://graph.facebook.com/{self.version}/{self.page_id}/photos"
        with image_path.open("rb") as fh:
            r = requests.post(
                url,
                data={"caption": caption, "published": "true", "access_token": self.token},
                files={"source": (image_path.name, fh, "image/jpeg")},
                timeout=max(self.timeout, 60),
            )
        try:
            payload = r.json()
        except Exception:
            payload = {"raw": r.text}
        if not r.ok or "error" in payload:
            raise RuntimeError(f"Facebook photo publish failed ({r.status_code}): {payload}")
        return {"id": payload.get("id", ""), "post_id": payload.get("post_id", payload.get("id", "")), "mode": "page_photo_file"}
