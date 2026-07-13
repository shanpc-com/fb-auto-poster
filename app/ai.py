from __future__ import annotations

import json
import requests

from .sources import SoftwareData

SYSTEM_PROMPT = """You write concise Facebook captions about legitimate software releases.
Use only facts supplied by the user. Never invent versions, file sizes, developers, dates, or features.
Do not include piracy, cracking, activation bypass, serial keys, or unsupported claims.
Return valid JSON with keys: description (string), features (array of up to 5 short strings), hashtags (array of 4 to 8 strings without #)."""


def enrich_with_ai(data: SoftwareData, provider: str, api_key: str, model: str, timeout: int) -> tuple[str, list[str], list[str]]:
    if provider == "none" or not api_key:
        return _fallback(data)

    facts = {
        "title": data.title, "description": data.description, "version": data.version,
        "developer": data.developer, "operating_system": data.operating_system,
        "license": data.license_name, "file_size": data.file_size,
        "release_date": data.release_date, "source": data.source_name,
    }
    prompt = "Create the JSON caption fields from these verified facts:\n" + json.dumps(facts, ensure_ascii=False)
    try:
        if provider == "groq":
            raw = _groq(prompt, api_key, model, timeout)
        else:
            raw = _gemini(prompt, api_key, model, timeout)
        parsed = _parse_json(raw)
        return (
            str(parsed.get("description") or data.description).strip(),
            [str(x).strip() for x in parsed.get("features", []) if str(x).strip()][:5],
            [str(x).strip().lstrip("#") for x in parsed.get("hashtags", []) if str(x).strip()][:8],
        )
    except Exception as exc:
        print(f"[WARN] AI generation failed; using factual fallback: {exc}")
        return _fallback(data)


def _groq(prompt: str, api_key: str, model: str, timeout: int) -> str:
    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={"model": model, "messages": [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": prompt}], "temperature": 0.2, "response_format": {"type": "json_object"}},
        timeout=timeout,
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]


def _gemini(prompt: str, api_key: str, model: str, timeout: int) -> str:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    response = requests.post(url, json={
        "contents": [{"parts": [{"text": SYSTEM_PROMPT + "\n\n" + prompt}]}],
        "generationConfig": {"temperature": 0.2, "responseMimeType": "application/json"},
    }, timeout=timeout)
    response.raise_for_status()
    return response.json()["candidates"][0]["content"]["parts"][0]["text"]


def _parse_json(raw: str) -> dict:
    raw = raw.strip().removeprefix("```json").removesuffix("```").strip()
    return json.loads(raw)


def _fallback(data: SoftwareData) -> tuple[str, list[str], list[str]]:
    description = data.description or f"Get the latest verified information about {data.title}."
    tags = [word for word in data.title.replace("-", " ").split() if word.isalnum()][:3]
    return description, [], tags + ["Software", "Windows", "Download"]
