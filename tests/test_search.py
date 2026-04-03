"""Tests for search engine (keyword indexing, no LLM needed)."""


def test_keyword_search_finds_matches(tmp_path, monkeypatch):
    import search
    monkeypatch.setattr(search, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(search, "WIKI_DIR", tmp_path / "wiki")
    monkeypatch.setattr(search, "_keyword_index_cache", None)
    monkeypatch.setattr(search, "KEYWORD_INDEX_CACHE", tmp_path / ".kw.json")

    wiki = tmp_path / "wiki" / "concepts"
    wiki.mkdir(parents=True)
    (wiki / "ml.md").write_text("Machine learning is great\nDeep learning too")
    (wiki / "web.md").write_text("Web development with JavaScript")

    results = search.keyword_search("machine learning")
    assert len(results) >= 1
    assert results[0]["file"].endswith("ml.md")


def test_keyword_search_empty_query(tmp_path, monkeypatch):
    import search
    monkeypatch.setattr(search, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(search, "WIKI_DIR", tmp_path / "wiki")
    monkeypatch.setattr(search, "_keyword_index_cache", None)
    monkeypatch.setattr(search, "KEYWORD_INDEX_CACHE", tmp_path / ".kw.json")

    wiki = tmp_path / "wiki"
    wiki.mkdir(parents=True)

    results = search.keyword_search("")
    assert results == []


def test_build_keyword_index(tmp_path, monkeypatch):
    import search
    monkeypatch.setattr(search, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(search, "WIKI_DIR", tmp_path / "wiki")

    wiki = tmp_path / "wiki"
    wiki.mkdir(parents=True)
    (wiki / "test.md").write_text("Hello world test")

    index = search.build_keyword_index()
    assert "hello" in index
    assert "world" in index
    assert len(index["hello"]) == 1
