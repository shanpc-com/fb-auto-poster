from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Iterable


CATEGORY_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("Browsers", ("chrome", "firefox", "browser", "opera", "edge", "brave")),
    ("PDF & Documents", ("pdf", "acrobat", "document", "office", "word", "excel", "powerpoint")),
    ("Media Players", ("vlc", "media player", "video player", "audio player", "codec")),
    ("Audio & Video", ("video", "audio", "editor", "converter", "recorder", "streaming")),
    ("Graphics & Design", ("photoshop", "illustrator", "design", "photo", "image", "cad", "3d")),
    ("Developer Tools", ("developer", "ide", "visual studio", "python", "java", "git", "database", "sql")),
    ("Security", ("antivirus", "security", "vpn", "firewall", "malware", "password")),
    ("Backup & Recovery", ("backup", "recovery", "restore", "partition", "disk", "data recovery")),
    ("Drivers & Utilities", ("driver", "utility", "cleaner", "optimizer", "system", "tool")),
    ("Compression", ("zip", "rar", "7-zip", "archive", "compression")),
)

CATEGORY_HASHTAGS = {
    "Browsers": ("WebBrowser", "InternetTools"),
    "PDF & Documents": ("PDFTools", "OfficeSoftware"),
    "Media Players": ("MediaPlayer", "VideoPlayer"),
    "Audio & Video": ("VideoSoftware", "AudioSoftware"),
    "Graphics & Design": ("GraphicDesign", "CreativeSoftware"),
    "Developer Tools": ("DeveloperTools", "Programming"),
    "Security": ("CyberSecurity", "SecuritySoftware"),
    "Backup & Recovery": ("DataRecovery", "BackupSoftware"),
    "Drivers & Utilities": ("PCUtilities", "WindowsTools"),
    "Compression": ("FileCompression", "ArchiveTools"),
    "General Software": ("WindowsSoftware", "SoftwareDownload"),
}

CTA_TEMPLATES = (
    "Have you used {name}? Share your experience in the comments.",
    "Which feature of {name} do you use most? Tell us below.",
    "Would you recommend {name} to other users? Leave a comment.",
    "Save this post for later and share it with someone who may need {name}.",
)

INTRO_TEMPLATES = (
    "Get the latest available information for {name}, including platform, version and key features.",
    "Looking for {name}? Review the latest software details, supported platform and download information.",
    "Discover {name} with a clear overview of its latest available version and useful features.",
    "Find current information about {name} and access its software details from one place.",
)


@dataclass(frozen=True)
class RankedContent:
    caption: str
    category: str
    primary_keyword: str
    secondary_keywords: tuple[str, ...]
    hashtags: tuple[str, ...]
    template_id: int
    quality_score: int


def _seed(text: str) -> int:
    return int(hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()[:12], 16)


def _clean_space(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def classify_category(*texts: str) -> str:
    haystack = " ".join(_clean_space(x).lower() for x in texts)
    for category, words in CATEGORY_RULES:
        if any(word in haystack for word in words):
            return category
    return "General Software"


def _keyword_tokens(title: str) -> list[str]:
    stop = {"download", "latest", "full", "version", "software", "for", "and", "the", "free", "offline", "installer"}
    words = re.findall(r"[A-Za-z0-9][A-Za-z0-9+.-]*", title)
    return [w for w in words if len(w) > 1 and w.lower() not in stop]


def _hashtag(value: str) -> str:
    value = (value or "").strip()
    if value and not any(ch.isspace() for ch in value):
        return "".join(ch for ch in value if ch.isalnum())
    return "".join(ch for ch in value.title() if ch.isalnum())


def _unique(values: Iterable[str], limit: int) -> tuple[str, ...]:
    out: list[str] = []
    seen: set[str] = set()
    for value in values:
        clean = _hashtag(value)
        key = clean.lower()
        if clean and key not in seen:
            seen.add(key)
            out.append(clean)
        if len(out) >= limit:
            break
    return tuple(out)


def build_ranked_content(item, data, link: str, description: str, features: list[str], source_tags: list[str]) -> RankedContent:
    title = _clean_space(item.display_title or data.title or item.search_term)
    category = classify_category(title, description, " ".join(features))
    token_words = _keyword_tokens(title)
    primary = title
    secondary = tuple(dict.fromkeys([
        f"{title} download",
        f"{title} latest version",
        f"{title} for Windows",
        f"{category} software",
    ]))

    seed = _seed(item.original or title)
    template_id = seed % len(INTRO_TEMPLATES)
    cta_id = (seed // 7) % len(CTA_TEMPLATES)
    intro = INTRO_TEMPLATES[template_id].format(name=title)
    source_desc = _clean_space(description)
    if source_desc and source_desc.lower() not in intro.lower():
        source_desc = source_desc[:420]
    else:
        source_desc = ""

    details = [
        ("Category", category),
        ("Version", getattr(data, "version", "")),
        ("Platform", getattr(data, "operating_system", "")),
        ("Developer", getattr(data, "developer", "")),
        ("License", getattr(data, "license_name", "")),
        ("File size", getattr(data, "file_size", "")),
        ("Updated", getattr(data, "release_date", "")),
    ]
    details = [(k, _clean_space(v)) for k, v in details if _clean_space(v)]
    feature_lines = [_clean_space(x) for x in features if _clean_space(x)][:4]

    hashtags = _unique(
        list(token_words[:4])
        + list(CATEGORY_HASHTAGS.get(category, ()))
        + list(source_tags)
        + ["LatestSoftwareDownload"],
        8,
    )

    lines = [title, "", intro]
    if source_desc:
        lines += [source_desc]
    lines += ["", f"Download & details: {link}"]
    if details:
        lines += ["", "Software information"] + [f"• {k}: {v}" for k, v in details]
    if feature_lines:
        lines += ["", "Key features"] + [f"• {x}" for x in feature_lines]
    lines += ["", CTA_TEMPLATES[cta_id].format(name=title), "", " ".join(f"#{x}" for x in hashtags)]
    caption = "\n".join(lines).strip()

    score = 55
    score += 10 if 35 <= len(title) <= 90 else 5
    score += 10 if source_desc else 5
    score += 10 if len(feature_lines) >= 3 else len(feature_lines) * 2
    score += 10 if len(hashtags) >= 5 else len(hashtags)
    score += 5 if link.startswith("http") else 0
    score = min(score, 100)

    return RankedContent(
        caption=caption,
        category=category,
        primary_keyword=primary,
        secondary_keywords=secondary,
        hashtags=hashtags,
        template_id=template_id,
        quality_score=score,
    )
