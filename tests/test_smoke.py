from pathlib import Path
from app.keywords import load_keywords

def test_keywords_load():
    assert load_keywords(Path("keywords.csv"), lawful_only=True)
