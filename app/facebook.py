from __future__ import annotations

from pathlib import Path
from typing import Any
import requests


class FacebookPoster:
    def __init__(self, page_id: str, access_token: str, version: str = "v25.0", timeout: int = 25):
        self.page_id = page_id
        self.token = access_token
        self.version = version
        self.timeout = timeout
        self.base = f"https://graph.facebook.com/{self.version}"

    @staticmethod
    def _payload(response: requests.Response) -> dict[str, Any]:
        try:
            payload = response.json()
        except Exception:
            payload = {"raw": response.text}
        if not response.ok or "error" in payload:
            raise RuntimeError(f"Facebook API failed ({response.status_code}): {payload}")
        return payload

    def _get_permalink(self, object_id: str) -> str:
        if not object_id:
            return ""
        response = requests.get(
            f"{self.base}/{object_id}",
            params={
                "fields": "id,permalink_url,created_time",
                "access_token": self.token,
            },
            timeout=max(self.timeout, 30),
        )
        try:
            payload = self._payload(response)
        except RuntimeError:
            return ""
        return str(payload.get("permalink_url", "") or "")

    def publish_photo_file(self, caption: str, image_path: Path) -> dict[str, str]:
        """Publish one public Page photo post and verify its Facebook permalink."""
        url = f"{self.base}/{self.page_id}/photos"
        with image_path.open("rb") as fh:
            response = requests.post(
                url,
                data={
                    "caption": caption,
                    "published": "true",
                    "access_token": self.token,
                },
                files={"source": (image_path.name, fh, "image/jpeg")},
                timeout=max(self.timeout, 90),
            )
        payload = self._payload(response)
        photo_id = str(payload.get("id", "") or "")
        post_id = str(payload.get("post_id", "") or photo_id)
        if not photo_id:
            raise RuntimeError(f"Facebook returned no photo id: {payload}")

        permalink = self._get_permalink(post_id) or self._get_permalink(photo_id)
        if not permalink:
            # The photo was accepted, but visibility could not be verified.
            raise RuntimeError(
                "Facebook accepted the image but returned no public permalink. "
                "Check Page token permissions and Page/app visibility."
            )

        return {
            "id": photo_id,
            "post_id": post_id,
            "permalink_url": permalink,
            "mode": "verified_page_photo",
        }
