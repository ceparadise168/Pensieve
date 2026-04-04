"""Tests for wiki linter checks (no LLM calls needed)."""

from lint import (
    check_broken_links, check_orphaned_articles, check_frontmatter,
    check_mermaid_syntax, check_plugin_dependencies,
)


def test_broken_links_detects_missing(tmp_path, monkeypatch):
    import lint
    monkeypatch.setattr(lint, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(lint, "WIKI_DIR", tmp_path / "wiki")

    concepts = tmp_path / "wiki" / "concepts"
    concepts.mkdir(parents=True)
    (concepts / "real-article.md").write_text(
        "---\ntitle: Real\n---\nLinks to [[nonexistent]]"
    )

    issues = check_broken_links()
    assert len(issues) == 1
    assert issues[0]["type"] == "broken_link"
    assert issues[0]["link"] == "nonexistent"


def test_broken_links_passes_valid(tmp_path, monkeypatch):
    import lint
    monkeypatch.setattr(lint, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(lint, "WIKI_DIR", tmp_path / "wiki")

    concepts = tmp_path / "wiki" / "concepts"
    concepts.mkdir(parents=True)
    (concepts / "article-a.md").write_text("---\ntitle: A\n---\nSee [[article-b]]")
    (concepts / "article-b.md").write_text("---\ntitle: B\n---\nSee [[article-a]]")

    issues = check_broken_links()
    assert len(issues) == 0


def test_orphaned_articles(tmp_path, monkeypatch):
    import lint
    monkeypatch.setattr(lint, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(lint, "WIKI_DIR", tmp_path / "wiki")

    concepts = tmp_path / "wiki" / "concepts"
    concepts.mkdir(parents=True)
    (concepts / "linked.md").write_text("---\ntitle: Linked\n---\nContent")
    (concepts / "orphan.md").write_text("---\ntitle: Orphan\n---\nContent")
    # Only linked is referenced
    index = tmp_path / "wiki" / "_index.md"
    index.write_text("See [[linked]]")

    issues = check_orphaned_articles()
    orphan_files = [i["file"] for i in issues]
    assert any("orphan.md" in f for f in orphan_files)


def test_frontmatter_missing_fields(tmp_path, monkeypatch):
    import lint
    monkeypatch.setattr(lint, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(lint, "WIKI_DIR", tmp_path / "wiki")

    concepts = tmp_path / "wiki" / "concepts"
    concepts.mkdir(parents=True)
    # Missing tags, created, status
    (concepts / "incomplete.md").write_text("---\ntitle: Incomplete\n---\nContent")

    issues = check_frontmatter()
    missing_fields = {i["field"] for i in issues}
    assert "tags" in missing_fields
    assert "created" in missing_fields
    assert "status" in missing_fields


def test_mermaid_valid_syntax(tmp_path, monkeypatch):
    import lint
    monkeypatch.setattr(lint, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(lint, "WIKI_DIR", tmp_path / "wiki")

    wiki = tmp_path / "wiki"
    wiki.mkdir(parents=True)
    (wiki / "graph.md").write_text(
        '```mermaid\ngraph LR\n    a --> b["Label"]\n    a --> c\n```'
    )
    issues = check_mermaid_syntax()
    assert len(issues) == 0


def test_mermaid_detects_bare_spaces(tmp_path, monkeypatch):
    import lint
    monkeypatch.setattr(lint, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(lint, "WIKI_DIR", tmp_path / "wiki")

    wiki = tmp_path / "wiki"
    wiki.mkdir(parents=True)
    (wiki / "graph.md").write_text(
        '```mermaid\ngraph LR\n    a --> Knowledge Graph\n```'
    )
    issues = check_mermaid_syntax()
    assert any(i["type"] == "mermaid_syntax" for i in issues)


def test_mermaid_detects_duplicates(tmp_path, monkeypatch):
    import lint
    monkeypatch.setattr(lint, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(lint, "WIKI_DIR", tmp_path / "wiki")

    wiki = tmp_path / "wiki"
    wiki.mkdir(parents=True)
    (wiki / "graph.md").write_text(
        '```mermaid\ngraph LR\n    a --> b["X"]\n    a --> b["X"]\n```'
    )
    issues = check_mermaid_syntax()
    assert any(i["type"] == "mermaid_duplicate" for i in issues)


def test_plugin_dependency_detected(tmp_path, monkeypatch):
    import lint
    monkeypatch.setattr(lint, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(lint, "WIKI_DIR", tmp_path / "wiki")

    wiki = tmp_path / "wiki"
    wiki.mkdir(parents=True)
    # No .obsidian/plugins/dataview directory
    (tmp_path / ".obsidian").mkdir()
    (wiki / "dashboard.md").write_text("# Dashboard\n```dataview\nLIST FROM *\n```")

    issues = check_plugin_dependencies()
    assert len(issues) == 1
    assert issues[0]["type"] == "missing_plugin"
    assert "dataview" in issues[0]["detail"]


def test_plugin_dependency_ok_when_installed(tmp_path, monkeypatch):
    import lint
    monkeypatch.setattr(lint, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(lint, "WIKI_DIR", tmp_path / "wiki")

    wiki = tmp_path / "wiki"
    wiki.mkdir(parents=True)
    (tmp_path / ".obsidian" / "plugins" / "dataview").mkdir(parents=True)
    (wiki / "dashboard.md").write_text("# Dashboard\n```dataview\nLIST FROM *\n```")

    issues = check_plugin_dependencies()
    assert len(issues) == 0
