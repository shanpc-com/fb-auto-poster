from types import SimpleNamespace
from app.content_engine import build_ranked_content, classify_category
from app.keywords import KeywordItem


def test_category_classification():
    assert classify_category("VLC Media Player") == "Media Players"
    assert classify_category("Adobe PDF Editor") == "PDF & Documents"


def test_caption_is_search_friendly_and_deterministic():
    item = KeywordItem("VLC Media Player", "VLC Media Player", "VLC Media Player")
    data = SimpleNamespace(
        title="VLC Media Player", description="A popular multimedia player.",
        features=["Plays many formats", "Subtitle support", "Streaming support"],
        version="3.0", developer="VideoLAN", operating_system="Windows",
        license_name="Free", file_size="40 MB", release_date="2026",
    )
    a = build_ranked_content(item, data, "https://example.com/vlc", data.description, data.features, ["VLC"])
    b = build_ranked_content(item, data, "https://example.com/vlc", data.description, data.features, ["VLC"])
    assert a.caption == b.caption
    assert a.category == "Media Players"
    assert "VLC Media Player" in a.caption
    assert "Download & details:" in a.caption
    assert "#LatestSoftwareDownload" in a.caption
    assert a.quality_score >= 80
