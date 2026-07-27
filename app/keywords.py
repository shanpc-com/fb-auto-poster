from __future__ import annotations
import csv
from dataclasses import dataclass
from pathlib import Path

@dataclass
class KeywordItem:
    original: str; search_term: str; display_title: str; source_url: str=""; site_link: str=""

BLOCKED = {"crack","keygen","serial key","license key","patched","pre-activated","activator"}

def load_keywords(path: Path, lawful_only=True):
    if not path.exists(): raise FileNotFoundError(path)
    rows=[]
    with path.open(encoding="utf-8-sig", newline="") as f:
        sample=f.read(2048); f.seek(0)
        has_header = "keyword" in sample.lower().splitlines()[0] if sample else False
        if has_header:
            for r in csv.DictReader(f):
                raw=(r.get("keyword") or r.get("title") or "").strip()
                if raw: rows.append(KeywordItem(raw,(r.get("search_term") or raw).strip(),(r.get("display_title") or raw).strip(),(r.get("source_url") or "").strip(),(r.get("site_link") or "").strip()))
        else:
            for r in csv.reader(f):
                if r and r[0].strip():
                    raw=r[0].strip(); rows.append(KeywordItem(raw,raw,raw,r[1].strip() if len(r)>1 else "",r[2].strip() if len(r)>2 else ""))
    if lawful_only:
        rows=[x for x in rows if not any(t in x.original.lower() for t in BLOCKED)]
    return rows
