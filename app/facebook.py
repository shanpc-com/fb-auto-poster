from __future__ import annotations

from pathlib import Path
from typing import Any
from urllib.parse import urlsplit, urlunsplit
import time
import requests


class FacebookPoster:
    def __init__(self, page_id: str, access_token: str, version: str = "v25.0", timeout: int = 25):
        self.page_id = page_id
        self.token = access_token
        self.version = version
        self.timeout = timeout
        self.base = f"https://graph.facebook.com/{self.version}"
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "SuperToolZone-Facebook-Auto-Poster/7.0"})

    @staticmethod
    def _payload(response: requests.Response) -> dict[str, Any]:
        try:
            payload = response.json()
        except Exception:
            payload = {"raw": response.text}
        if not response.ok or "error" in payload:
            raise RuntimeError(f"Facebook API failed ({response.status_code}): {payload}")
        return payload

    @staticmethod
    def clean_permalink(url: str) -> str:
        if not url:
            return ""
        parts = urlsplit(url.strip())
        return urlunsplit((parts.scheme or "https", parts.netloc, parts.path, "", ""))

    @staticmethod
    def album_url(album_id: str) -> str:
        return f"https://www.facebook.com/media/set/?set=a.{album_id}" if album_id else ""

    def _get(self, object_id: str, fields: str) -> dict[str, Any]:
        response = self.session.get(
            f"{self.base}/{object_id}",
            params={"fields": fields, "access_token": self.token},
            timeout=max(self.timeout, 30),
        )
        return self._payload(response)

    def verify_page(self) -> dict[str, str]:
        payload = self._get(self.page_id, "id,name,username,link")
        returned_id = str(payload.get("id", ""))
        if returned_id != str(self.page_id):
            raise RuntimeError(f"Page verification mismatch: expected {self.page_id}, got {returned_id}")
        return {
            "id": returned_id,
            "name": str(payload.get("name", "") or ""),
            "username": str(payload.get("username", "") or ""),
            "link": self.clean_permalink(str(payload.get("link", "") or "")),
        }

    def verify_album(self, album_id: str) -> dict[str, str]:
        payload = self._get(album_id, "id,name,link,from")
        returned_id = str(payload.get("id", "") or "")
        if returned_id != str(album_id):
            raise RuntimeError(f"Album verification mismatch: expected {album_id}, got {returned_id}")
        owner = payload.get("from") or {}
        owner_id = str(owner.get("id", "") or "") if isinstance(owner, dict) else ""
        if owner_id and owner_id != str(self.page_id):
            raise RuntimeError(f"Album {album_id} belongs to Page {owner_id}, not configured Page {self.page_id}.")
        return {
            "id": returned_id,
            "name": str(payload.get("name", "") or ""),
            "link": self.clean_permalink(str(payload.get("link", "") or "")) or self.album_url(returned_id),
            "owner_id": owner_id,
        }

    def verify_post(self, object_id: str, attempts: int = 5) -> dict[str, Any]:
        last_error: Exception | None = None
        for attempt in range(attempts):
            try:
                payload = self._get(object_id, "id,permalink_url,created_time,is_published,message,full_picture")
                permalink = self.clean_permalink(str(payload.get("permalink_url", "") or ""))
                if payload.get("is_published") is False:
                    raise RuntimeError("Facebook read-back says the post is not published.")
                if permalink:
                    payload["permalink_url"] = permalink
                    return payload
            except Exception as exc:
                last_error = exc
            if attempt + 1 < attempts:
                time.sleep(2 ** attempt)
        if last_error:
            raise RuntimeError(f"Post read-back verification failed: {last_error}")
        raise RuntimeError("Facebook returned no public permalink during post verification.")

    def _publish_to_endpoint(self, endpoint_id: str, caption: str, image_path: Path) -> dict[str, Any]:
        url = f"{self.base}/{endpoint_id}/photos"
        with image_path.open("rb") as fh:
            response = self.session.post(
                url,
                data={"caption": caption, "published": "true", "access_token": self.token},
                files={"source": (image_path.name, fh, "image/jpeg")},
                timeout=max(self.timeout, 90),
            )
        return self._payload(response)

    def _verify_publish_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        photo_id = str(payload.get("id", "") or "")
        post_id = str(payload.get("post_id", "") or photo_id)
        if not photo_id:
            raise RuntimeError(f"Facebook returned no photo id: {payload}")

        verified = None
        verified_object = ""
        for candidate in dict.fromkeys([post_id, photo_id]):
            if not candidate:
                continue
            try:
                verified = self.verify_post(candidate)
                verified_object = candidate
                break
            except RuntimeError:
                continue
        if not verified:
            raise RuntimeError(
                "Facebook accepted the image, but the published object could not be read back with a permalink. "
                "Check Page token permissions and visibility."
            )
        return {
            "id": photo_id,
            "post_id": post_id,
            "verified_object_id": verified_object,
            "permalink_url": verified["permalink_url"],
            "created_time": str(verified.get("created_time", "") or ""),
            "is_published": verified.get("is_published", True),
            "full_picture": str(verified.get("full_picture", "") or ""),
        }

    def publish_photo_file(self, caption: str, image_path: Path) -> dict[str, Any]:
        result = self._verify_publish_payload(self._publish_to_endpoint(self.page_id, caption, image_path))
        return {**result, "mode": "verified_page_photo_v7", "album_id": "", "album_url": ""}

    def publish_to_album(self, album_id: str, caption: str, image_path: Path) -> dict[str, Any]:
        album = self.verify_album(album_id)
        result = self._verify_publish_payload(self._publish_to_endpoint(album_id, caption, image_path))
        return {
            **result,
            "mode": "verified_existing_album_photo_v7",
            "album_id": album["id"],
            "album_name": album["name"],
            "album_url": album["link"] or self.album_url(album["id"]),
        }
