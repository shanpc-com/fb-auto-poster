from __future__ import annotations

import requests


class FacebookPoster:
    def __init__(self, page_id: str, token: str, api_version: str, timeout: int = 25):
        self.page_id = page_id
        self.token = token
        self.base = f"https://graph.facebook.com/{api_version}/{page_id}"
        self.timeout = timeout

    def publish(self, message: str, link: str = "", image_url: str = "") -> dict:
        if image_url:
            try:
                return self._post_photo(message, image_url)
            except requests.RequestException as exc:
                print(f"[WARN] Image post failed; falling back to link post: {exc}")
        return self._post_feed(message, link)

    def _post_photo(self, message: str, image_url: str) -> dict:
        response = requests.post(
            f"{self.base}/photos",
            data={"url": image_url, "caption": message, "access_token": self.token},
            timeout=self.timeout,
        )
        self._raise(response)
        return response.json()

    def _post_feed(self, message: str, link: str) -> dict:
        payload = {"message": message, "access_token": self.token}
        if link:
            payload["link"] = link
        response = requests.post(f"{self.base}/feed", data=payload, timeout=self.timeout)
        self._raise(response)
        return response.json()

    @staticmethod
    def _raise(response: requests.Response) -> None:
        if response.ok:
            return
        try:
            detail = response.json()
        except ValueError:
            detail = response.text
        raise requests.HTTPError(f"Facebook API {response.status_code}: {detail}", response=response)
