from types import SimpleNamespace
from app.content_engine import build_ranked_content
from app.keywords import KeywordItem


def test_ranked_caption_smoke():
    item = KeywordItem("Example App", "Example App", "Example App")
    data = SimpleNamespace(
        title="Example App", description="A useful desktop application.",
        features=["Fast setup", "Simple interface", "Regular updates"],
        version="1.0", developer="Example", operating_system="Windows",
        license_name="Free", file_size="20 MB", release_date="2026",
    )
    result = build_ranked_content(item, data, "https://example.com", data.description, data.features, ["ExampleApp"])
    assert result.caption.startswith("Example App")
    assert "https://example.com" in result.caption
    assert result.quality_score > 0
