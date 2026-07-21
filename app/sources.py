from __future__ import annotations
from dataclasses import dataclass, field
from urllib.parse import quote_plus, urljoin, urlparse, parse_qs
import re, requests
from bs4 import BeautifulSoup
from .validators import validate_public_image, UA

@dataclass
class SoftwareData:
    title:str=""; description:str=""; version:str=""; developer:str=""; operating_system:str=""; license_name:str=""; file_size:str=""; release_date:str=""; image_url:str=""; source_url:str=""; source_name:str=""; features:list[str]=field(default_factory=list)

class SourceFetcher:
    def __init__(self, domains, timeout=25, max_results=4, min_w=240, min_h=160):
        self.domains=domains; self.timeout=timeout; self.max_results=max_results; self.min_w=min_w; self.min_h=min_h
        self.s=requests.Session(); self.s.headers.update(UA)
    def _search(self, term, domain):
        q=quote_plus(f"site:{domain} {term}")
        r=self.s.get(f"https://html.duckduckgo.com/html/?q={q}",timeout=self.timeout); r.raise_for_status()
        soup=BeautifulSoup(r.text,"html.parser"); out=[]
        for a in soup.select("a.result__a"):
            href=a.get("href","")
            if "uddg=" in href: href=parse_qs(urlparse(href).query).get("uddg",[href])[0]
            if domain in urlparse(href).netloc and href not in out: out.append(href)
            if len(out)>=self.max_results: break
        return out
    def _meta(self,soup,*keys):
        for key in keys:
            tag=soup.find("meta",attrs={"property":key}) or soup.find("meta",attrs={"name":key})
            if tag and tag.get("content"): return tag["content"].strip()
        return ""
    def _scrape(self,url):
        r=self.s.get(url,timeout=self.timeout,allow_redirects=True); r.raise_for_status()
        soup=BeautifulSoup(r.text,"html.parser")
        title=self._meta(soup,"og:title","twitter:title") or (soup.title.get_text(" ",strip=True) if soup.title else "")
        desc=self._meta(soup,"og:description","description","twitter:description")
        image=self._meta(soup,"og:image","twitter:image","twitter:image:src")
        if image: image=urljoin(r.url,image)
        text=soup.get_text(" ",strip=True)
        def grab(pattern):
            m=re.search(pattern,text,re.I); return m.group(1).strip() if m else ""
        features=[]
        for li in soup.select("li"):
            t=li.get_text(" ",strip=True)
            if 12<=len(t)<=160 and t not in features: features.append(t)
            if len(features)>=8: break
        return SoftwareData(title=title[:180],description=desc[:1200],version=grab(r"Version\s*[:\-]?\s*([\w.\- ]{1,35})"),developer=grab(r"Developer\s*[:\-]?\s*([^|]{2,60})"),operating_system=grab(r"(?:OS|Operating System|Platform)\s*[:\-]?\s*([^|]{2,60})"),license_name=grab(r"License\s*[:\-]?\s*([^|]{2,35})"),file_size=grab(r"(?:File Size|Size)\s*[:\-]?\s*([\d.,]+\s*(?:KB|MB|GB))"),release_date=grab(r"(?:Updated|Release Date)\s*[:\-]?\s*([^|]{4,35})"),image_url=image,source_url=r.url,source_name=urlparse(r.url).netloc.removeprefix("www."),features=features)
    def fetch(self,term,source_url=""):
        urls=[source_url] if source_url else []
        if not urls:
            for d in self.domains:
                try: urls += self._search(term,d)
                except Exception: continue
        errors=[]
        for url in urls:
            if not url: continue
            try:
                data=self._scrape(url)
                if not data.image_url: raise ValueError("No OG image")
                info=validate_public_image(data.image_url,self.timeout,self.min_w,self.min_h)
                data.image_url=info["url"]
                return data
            except Exception as e: errors.append(f"{url}: {e}")
        raise RuntimeError("No valid software image found. " + " | ".join(errors[-4:]))
