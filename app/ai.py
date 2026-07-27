from __future__ import annotations
import re

def enrich_with_ai(data, provider="none", api_key="", model="", timeout=25):
    # Deterministic fallback keeps the workflow reliable and free.
    description=data.description.strip() or f"Get verified information and the latest available details about {data.title}."
    features=[re.sub(r"\s+"," ",x).strip() for x in data.features if x.strip()][:5]
    if not features: features=["Current software information","Platform and version details","Direct access to the official information page"]
    words=re.findall(r"[A-Za-z0-9]+",data.title)[:4]
    tags=[]
    for w in words+["Software","Windows","Download"]:
        if len(w)>1 and w.lower() not in {x.lower() for x in tags}: tags.append(w)
    return description[:900],features,tags[:8]
