import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from ingest import _slug


def test_slug_basic():
    assert _slug("Hello World Example") == "hello-world-example"


def test_slug_special_chars():
    result = _slug("What's New? (2024)")
    assert "whats" in result
    assert "new" in result
    assert "2024" in result


def test_slug_max_length():
    long = "a " * 100
    assert len(_slug(long)) <= 80


def test_slug_preserves_hyphens():
    assert _slug("my-cool-article") == "my-cool-article"


def test_slug_strips_whitespace():
    assert _slug("  hello world  ") == "hello-world"
