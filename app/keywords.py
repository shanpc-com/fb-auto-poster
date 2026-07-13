from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path

UNSAFE_MARKETING_TERMS = re.compile(
    r"\b(crack(?:ed)?|pre[- ]?activated|full activated|activation key|serial key|"
    r"keygen|license bypass|patch(?:ed)?|warez)\b",
    flags=re.IGNORECASE,
)

@dataclass(frozen=True)
class KeywordItem:
    original: str
    search_term: str
    display_title: str
    site_link: str = ""
    source_url: str = ""


def clean_title(value: str) -> str:
    value = UNSAFE_MARKETING_TERMS.sub("", value)
    value = re.sub(r"\s{2,}", " ", value)
    value = re.sub(r"\s+([,.;:])", r"\1", value)
    return value.strip(" -–—,|_")


def load_keywords(path: Path) -> list[KeywordItem]:
    if not path.exists():
        raise FileNotFoundError(f"Keyword file not found: {path}")

    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.reader(handle))
    if not rows:
        return []

    header = [cell.strip().lower() for cell in rows[0]]
    structured = "keyword" in header
    items: list[KeywordItem] = []

    if structured:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                original = (row.get("keyword") or row.get("Keyword") or "").strip()
                if not original:
                    continue
                cleaned = clean_title(original)
                if not cleaned:
                    continue
                items.append(KeywordItem(
                    original=original,
                    search_term=cleaned,
                    display_title=cleaned,
                    site_link=(row.get("site_link") or "").strip(),
                    source_url=(row.get("source_url") or "").strip(),
                ))
    else:
        for row in rows:
            original = (row[0] if row else "").strip()
            if original and original.lower() != "keyword":
                cleaned = clean_title(original)
                if cleaned:
                    items.append(KeywordItem(original, cleaned, cleaned))
    return items
