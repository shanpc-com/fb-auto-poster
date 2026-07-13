from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from html import unescape
from urllib.parse import parse_qs, quote_plus, unquote, urlparse

import requests
from bs4 import BeautifulSoup

USER_AGENT = "Mozilla/5.0 (compatible; FacebookSoftwarePoster/2.0; +https://github.com/)"

@dataclass
class SoftwareData:
    title: str
    source_url: str = ""
    source_name: str = ""
    description: str = ""
    version: str = ""
    developer: str = ""
    operating_system: str = ""
    license_name: str = ""
    file_size: str = ""
    release_date: str = ""
    image_url: str = ""
    features: list[str] = field(default_factory=list)

    def useful(self) -> bool:
        return bool(self.description or self.version or self.developer or self.image_url)


class SourceFetcher:
    def __init__(self, domains: tuple[str, ...], timeout: int = 25):
        self.domains = domains
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT, "Accept-Language": "en-US,en;q=0.8"})

    def fetch(self, keyword: str, source_url: str = "") -> SoftwareData:
        candidates: list[str] = []
        if source_url:
            candidates.append(source_url)
        candidates.extend(self._search_candidates(keyword))
        seen: set[str] = set()
        best = SoftwareData(title=keyword)
        for url in candidates[:12]:
            if not url or url in seen:
                continue
            seen.add(url)
            try:
                data = self._parse_page(url, keyword)
            except requests.RequestException as exc:
                print(f"[WARN] Source request failed: {url} ({exc})")
                continue
            except Exception as exc:
                print(f"[WARN] Source parse failed: {url} ({exc})")
                continue
            if data.useful():
                return data
            if len(data.description) > len(best.description):
                best = data
        return best

    def _search_candidates(self, keyword: str) -> list[str]:
        results: list[str] = []
        for domain in self.domains:
            query = quote_plus(f'site:{domain} "{keyword}"')
            url = f"https://html.duckduckgo.com/html/?q={query}"
            try:
                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, "html.parser")
                for anchor in soup.select("a.result__a"):
                    href = anchor.get("href", "")
                    decoded = self._decode_ddg_url(href)
                    if decoded and domain in urlparse(decoded).netloc.lower():
                        results.append(decoded)
                        break
            except requests.RequestException as exc:
                print(f"[WARN] Search unavailable for {domain}: {exc}")
        return results

    @staticmethod
    def _decode_ddg_url(url: str) -> str:
        if not url:
            return ""
        parsed = urlparse(url)
        target = parse_qs(parsed.query).get("uddg", [""])[0]
        return unquote(target) if target else url

    def _parse_page(self, url: str, fallback_title: str) -> SoftwareData:
        response = self.session.get(url, timeout=self.timeout, allow_redirects=True)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        domain = urlparse(response.url).netloc.lower().removeprefix("www.")

        def meta(*keys: tuple[str, str]) -> str:
            for attr, value in keys:
                tag = soup.find("meta", attrs={attr: value})
                if tag and tag.get("content"):
                    return unescape(tag["content"].strip())
            return ""

        title = meta(("property", "og:title"), ("name", "twitter:title"))
        if not title and soup.title:
            title = soup.title.get_text(" ", strip=True)
        description = meta(("property", "og:description"), ("name", "description"), ("name", "twitter:description"))
        image = meta(("property", "og:image"), ("name", "twitter:image"))

        structured = self._extract_json_ld(soup)
        title = structured.get("name") or title or fallback_title
        description = structured.get("description") or description
        image = structured.get("image") or image
        version = structured.get("softwareVersion", "")
        developer = self._organization_name(structured.get("author") or structured.get("publisher"))
        os_name = structured.get("operatingSystem", "")
        license_name = structured.get("license", "")
        release_date = structured.get("datePublished", "") or structured.get("dateModified", "")
        file_size = structured.get("fileSize", "") or self._find_label_value(soup, ["file size", "size"])

        if not version:
            version = self._find_label_value(soup, ["version", "latest version"])
        if not developer:
            developer = self._find_label_value(soup, ["developer", "publisher", "author"])
        if not os_name:
            os_name = self._find_label_value(soup, ["operating system", "os", "platform"])
        if not license_name:
            license_name = self._find_label_value(soup, ["license", "licence"])

        return SoftwareData(
            title=self._clean(title), source_url=response.url, source_name=domain,
            description=self._clean(description)[:900], version=self._clean(str(version)),
            developer=self._clean(str(developer)), operating_system=self._clean(str(os_name)),
            license_name=self._clean(str(license_name)), file_size=self._clean(str(file_size)),
            release_date=self._clean(str(release_date)), image_url=image.strip(),
        )

    @staticmethod
    def _extract_json_ld(soup: BeautifulSoup) -> dict:
        candidates: list[dict] = []
        for tag in soup.find_all("script", attrs={"type": "application/ld+json"}):
            try:
                payload = json.loads(tag.string or tag.get_text())
            except (json.JSONDecodeError, TypeError):
                continue
            queue = payload if isinstance(payload, list) else [payload]
            for obj in queue:
                if not isinstance(obj, dict):
                    continue
                graph = obj.get("@graph", [])
                if isinstance(graph, list):
                    queue.extend(x for x in graph if isinstance(x, dict))
                kind = str(obj.get("@type", "")).lower()
                if any(word in kind for word in ("software", "product", "application")):
                    candidates.insert(0, obj)
                else:
                    candidates.append(obj)
        return candidates[0] if candidates else {}

    @staticmethod
    def _organization_name(value) -> str:
        if isinstance(value, dict):
            return str(value.get("name", ""))
        if isinstance(value, list) and value:
            return SourceFetcher._organization_name(value[0])
        return str(value or "")

    @staticmethod
    def _find_label_value(soup: BeautifulSoup, labels: list[str]) -> str:
        text = soup.get_text("\n", strip=True)
        for label in labels:
            match = re.search(rf"(?im)^\s*{re.escape(label)}\s*[:\-]?\s*([^\n]{{1,100}})$", text)
            if match:
                return match.group(1).strip()
        return ""

    @staticmethod
    def _clean(value: str) -> str:
        return re.sub(r"\s+", " ", unescape(value or "")).strip()
