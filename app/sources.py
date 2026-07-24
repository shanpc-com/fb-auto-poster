from __future__ import annotations
from dataclasses import dataclass, field
from urllib.parse import quote_plus, urljoin, urlparse, parse_qs
import re
import requests
from bs4 import BeautifulSoup
from .validators import validate_public_image, UA

@dataclass
class SoftwareData:
    title: str = ""
    description: str = ""
    version: str = ""
    developer: str = ""
    operating_system: str = ""
    license_name: str = ""
    file_size: str = ""
    release_date: str = ""
    image_url: str = ""
    source_url: str = ""
    source_name: str = ""
    features: list[str] = field(default_factory=list)

class SourceFetcher:
    def __init__(self, domains, timeout=25, max_results=4, min_w=240, min_h=160):
        self.domains = domains
        self.timeout = timeout
        self.max_results = max_results
        self.min_w = min_w
        self.min_h = min_h
        self.s = requests.Session()
        self.s.headers.update(UA)

    def _wikipedia(self, term: str) -> list[SoftwareData]:
        """Reliable, no-key metadata/image fallback for common software names."""
        api = "https://en.wikipedia.org/w/api.php"
        params = {
            "action": "query",
            "generator": "search",
            "gsrsearch": f'{term} software',
            "gsrlimit": 4,
            "prop": "pageimages|extracts|info",
            "piprop": "thumbnail|original",
            "pithumbsize": 1200,
            "exintro": 1,
            "explaintext": 1,
            "inprop": "url",
            "format": "json",
            "formatversion": 2,
        }
        r = self.s.get(api, params=params, timeout=self.timeout)
        r.raise_for_status()
        pages = r.json().get("query", {}).get("pages", [])
        out = []
        for p in pages:
            image = (p.get("thumbnail") or {}).get("source", "") or (p.get("original") or {}).get("source", "")
            out.append(SoftwareData(
                title=p.get("title", term),
                description=(p.get("extract") or "")[:1200],
                image_url=image,
                source_url=p.get("fullurl", ""),
                source_name="wikipedia.org",
            ))
        return out

    def _search(self, term, domain):
        q = quote_plus(f"site:{domain} {term}")
        endpoints = [
            f"https://html.duckduckgo.com/html/?q={q}",
            f"https://lite.duckduckgo.com/lite/?q={q}",
        ]
        out = []
        for endpoint in endpoints:
            try:
                r = self.s.get(endpoint, timeout=self.timeout)
                r.raise_for_status()
                soup = BeautifulSoup(r.text, "html.parser")
                selectors = ["a.result__a", "a.result-link"]
                for selector in selectors:
                    for a in soup.select(selector):
                        href = a.get("href", "")
                        if "uddg=" in href:
                            href = parse_qs(urlparse(href).query).get("uddg", [href])[0]
                        if domain in urlparse(href).netloc and href not in out:
                            out.append(href)
                        if len(out) >= self.max_results:
                            return out
            except Exception:
                continue
        return out

    def _meta(self, soup, *keys):
        for key in keys:
            tag = soup.find("meta", attrs={"property": key}) or soup.find("meta", attrs={"name": key})
            if tag and tag.get("content"):
                return tag["content"].strip()
        return ""

    def _scrape(self, url):
        r = self.s.get(url, timeout=self.timeout, allow_redirects=True)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        title = self._meta(soup, "og:title", "twitter:title") or (soup.title.get_text(" ", strip=True) if soup.title else "")
        desc = self._meta(soup, "og:description", "description", "twitter:description")
        image = self._meta(soup, "og:image", "twitter:image", "twitter:image:src")
        if image:
            image = urljoin(r.url, image)
        text = soup.get_text(" ", strip=True)
        def grab(pattern):
            m = re.search(pattern, text, re.I)
            return m.group(1).strip() if m else ""
        features = []
        for li in soup.select("li"):
            t = li.get_text(" ", strip=True)
            if 12 <= len(t) <= 160 and t not in features:
                features.append(t)
            if len(features) >= 8:
                break
        return SoftwareData(
            title=title[:180], description=desc[:1200],
            version=grab(r"Version\s*[:\-]?\s*([\w.\- ]{1,35})"),
            developer=grab(r"Developer\s*[:\-]?\s*([^|]{2,60})"),
            operating_system=grab(r"(?:OS|Operating System|Platform)\s*[:\-]?\s*([^|]{2,60})"),
            license_name=grab(r"License\s*[:\-]?\s*([^|]{2,35})"),
            file_size=grab(r"(?:File Size|Size)\s*[:\-]?\s*([\d.,]+\s*(?:KB|MB|GB))"),
            release_date=grab(r"(?:Updated|Release Date)\s*[:\-]?\s*([^|]{4,35})"),
            image_url=image, source_url=r.url,
            source_name=urlparse(r.url).netloc.removeprefix("www."), features=features,
        )

    def fetch(self, term, source_url=""):
        candidates = []
        errors = []
        if source_url:
            try:
                candidates.append(self._scrape(source_url))
            except Exception as e:
                errors.append(f"{source_url}: {e}")
        else:
            try:
                candidates.extend(self._wikipedia(term))
            except Exception as e:
                errors.append(f"Wikipedia: {e}")
            for d in self.domains:
                try:
                    for url in self._search(term, d):
                        try:
                            candidates.append(self._scrape(url))
                        except Exception as e:
                            errors.append(f"{url}: {e}")
                except Exception as e:
                    errors.append(f"Search {d}: {e}")

        # Prefer a candidate with a validated public image.
        for data in candidates:
            if not data.image_url:
                continue
            try:
                info = validate_public_image(data.image_url, self.timeout, self.min_w, self.min_h)
                data.image_url = info["url"]
                return data
            except Exception as e:
                errors.append(f"{data.image_url}: {e}")

        # Keep useful metadata even when remote image search is blocked.
        if candidates:
            best = max(candidates, key=lambda x: len(x.description or ""))
            best.image_url = ""
            return best
        return SoftwareData(
            title=term,
            description=f"Get the latest verified information about {term}.",
            source_name="",
        )
