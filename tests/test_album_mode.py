from app.facebook import FacebookPoster


def test_album_url():
    assert FacebookPoster.album_url("12345") == "https://www.facebook.com/media/set/?set=a.12345"
    assert FacebookPoster.album_url("") == ""


def test_clean_permalink_removes_tracking():
    url = "https://www.facebook.com/page/posts/abc?__cft__=x&__tn__=y"
    assert FacebookPoster.clean_permalink(url) == "https://www.facebook.com/page/posts/abc"
