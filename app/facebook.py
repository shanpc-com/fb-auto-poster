from __future__ import annotations
import requests

class FacebookPoster:
    def __init__(self,page_id,access_token,version="v25.0",timeout=25):
        self.page_id=page_id; self.token=access_token; self.version=version; self.timeout=timeout
    def publish_photo(self,caption,image_url):
        url=f"https://graph.facebook.com/{self.version}/{self.page_id}/photos"
        r=requests.post(url,data={"url":image_url,"caption":caption,"published":"true","access_token":self.token},timeout=self.timeout)
        try: payload=r.json()
        except Exception: payload={"raw":r.text}
        if not r.ok or "error" in payload: raise RuntimeError(f"Facebook photo publish failed ({r.status_code}): {payload}")
        return {"id":payload.get("id", ""),"post_id":payload.get("post_id",payload.get("id","")),"mode":"page_photo"}
