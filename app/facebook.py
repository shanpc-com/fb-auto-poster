from __future__ import annotations

from dataclasses import dataclass

import requests


@dataclass(frozen=True)
class FacebookPublishResult:
    id: str = ""
    post_id: str = ""
    album_id: str = ""
    album_url: str = ""
    mode: str = "feed"

    def as_dict(self) -> dict:
        return {
            "id": self.id,
            "post_id": self.post_id,
            "album_id": self.album_id,
            "album_url": self.album_url,
            "mode": self.mode,
        }


class FacebookPoster:
    """Publish software posts to a Facebook Page.

    Facebook's current Graph API does not allow an app to create a new Page
    album. Album mode therefore uploads the image to an album that was created
    manually on the Page and supplied through FB_ALBUM_ID/config.json.
    """

    def __init__(
        self,
        page_id: str,
        token: str,
        api_version: str,
        timeout: int = 25,
        album_id: str = "",
    ):
        self.page_id = page_id
        self.token = token
        self.api_version = api_version
        self.graph_base = f"https://graph.facebook.com/{api_version}"
        self.page_base = f"{self.graph_base}/{page_id}"
        self.timeout = timeout
        self.album_id = self._normalize_album_id(album_id)

    def publish(self, message: str, link: str = "", image_url: str = "") -> dict:
        if image_url and self.album_id:
            try:
                return self._post_album_photo(message, image_url)
            except requests.RequestException as exc:
                print(f"[WARN] Album upload failed; falling back to Page photo post: {exc}")

        if image_url:
            try:
                return self._post_page_photo(message, image_url)
            except requests.RequestException as exc:
                print(f"[WARN] Image post failed; falling back to link post: {exc}")

        return self._post_feed(message, link)

    def _post_album_photo(self, message: str, image_url: str) -> dict:
        response = requests.post(
            f"{self.graph_base}/{self.album_id}/photos",
            data={
                "url": image_url,
                "caption": message,
                "published": "true",
                "access_token": self.token,
            },
            timeout=self.timeout,
        )
        self._raise(response)
        payload = response.json()
        result = FacebookPublishResult(
            id=str(payload.get("id", "")),
            post_id=str(payload.get("post_id", "")),
            album_id=self.album_id,
            album_url=self.album_url(self.album_id),
            mode="album_photo",
        )
        return result.as_dict()

    def _post_page_photo(self, message: str, image_url: str) -> dict:
        response = requests.post(
            f"{self.page_base}/photos",
            data={
                "url": image_url,
                "caption": message,
                "published": "true",
                "access_token": self.token,
            },
            timeout=self.timeout,
        )
        self._raise(response)
        payload = response.json()
        return FacebookPublishResult(
            id=str(payload.get("id", "")),
            post_id=str(payload.get("post_id", "")),
            mode="page_photo",
        ).as_dict()

    def _post_feed(self, message: str, link: str) -> dict:
        payload = {"message": message, "access_token": self.token}
        if link:
            payload["link"] = link
        response = requests.post(f"{self.page_base}/feed", data=payload, timeout=self.timeout)
        self._raise(response)
        data = response.json()
        return FacebookPublishResult(
            id=str(data.get("id", "")),
            post_id=str(data.get("post_id", "")),
            mode="feed",
        ).as_dict()

    @staticmethod
    def _normalize_album_id(album_id: str) -> str:
        value = str(album_id or "").strip()
        if value.startswith("a."):
            value = value[2:]
        return value

    @staticmethod
    def album_url(album_id: str) -> str:
        normalized = FacebookPoster._normalize_album_id(album_id)
        return f"https://www.facebook.com/media/set/?set=a.{normalized}" if normalized else ""

    @staticmethod
    def _raise(response: requests.Response) -> None:
        if response.ok:
            return
        try:
            detail = response.json()
        except ValueError:
            detail = response.text
        raise requests.HTTPError(f"Facebook API {response.status_code}: {detail}", response=response)
