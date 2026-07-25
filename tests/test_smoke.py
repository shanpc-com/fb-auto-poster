from app.facebook import FacebookPoster
from auto_poster import build_message

class Item:
    display_title = "Example Software  2026"
class Data:
    version = "1.0"; developer = "Example"; operating_system = "Windows"
    license_name = "Free"; file_size = "20 MB"; release_date = "2026-07-25"

def test_clean_permalink_removes_tracking():
    url = "https://www.facebook.com/page/posts/pfbid123?__cft__[0]=abc&__tn__=x"
    assert FacebookPoster.clean_permalink(url) == "https://www.facebook.com/page/posts/pfbid123"

def test_caption_has_title_first_and_link():
    text = build_message(Item(), Data(), "https://example.com", "A useful desktop application.", ["Fast", "Simple"], ["Software", "Windows"])
    assert text.splitlines()[0] == "Example Software 2026"
    assert "Download: https://example.com" in text
    assert "#Software" in text
