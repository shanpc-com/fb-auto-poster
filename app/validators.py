from __future__ import annotations
from io import BytesIO
from urllib.parse import urlparse
import requests
from PIL import Image

UA={"User-Agent":"Mozilla/5.0 (compatible; FB-Auto-Poster/5.0)"}
def validate_public_image(url: str, timeout=25, min_width=240, min_height=160):
    p=urlparse(url)
    if p.scheme not in {"http","https"}: raise ValueError("Image URL is not public HTTP(S)")
    r=requests.get(url,headers=UA,timeout=timeout,stream=True,allow_redirects=True); r.raise_for_status()
    ctype=r.headers.get("content-type","").lower()
    data=r.content
    if "image" not in ctype and len(data)<100: raise ValueError("URL did not return an image")
    im=Image.open(BytesIO(data)); im.verify()
    im=Image.open(BytesIO(data))
    if im.width<min_width or im.height<min_height: raise ValueError(f"Image too small: {im.width}x{im.height}")
    return {"url":r.url,"width":im.width,"height":im.height,"content_type":ctype,"bytes":len(data)}
