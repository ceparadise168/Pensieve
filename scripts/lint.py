"""
Wiki Linter — health checks and auto-repair for the knowledge base.

Usage:
    python scripts/lint.py --check
    python scripts/lint.py --fix
    python scripts/lint.py --suggest
"""
import re
import json
import click
from pathlib import Path
from datetime import datetime

import frontmatter

from utils.llm_client import ask

PROJECT_ROOT = Path(__file__).parent.parent
WIKI_DIR = PROJECT_ROOT / "wiki"
RAW_DIR = PROJECT_ROOT / "raw"


def check_broken_links() -> list[dict]:
    issues = []
    existing_slugs = {p.stem for p in (WIKI_DIR / "concepts").glob("*.md")}
    # Also index wiki-level files (e.g. _index, _graph, _glossary)
    wiki_files = {p.stem for p in WIKI_DIR.glob("*.md")}
    for md_file in WIKI_DIR.rglob("*.md"):
        content = md_file.read_text(encoding="utf-8")
        links = re.findall(r'\[\[([^\]|]+)', content)
        for link in links:
            # Strip trailing backslash from escaped pipes in tables (\|)
            raw = link.strip().rstrip("\\")
            # Handle path-style links like "concepts/slug"
            slug = raw.split("/")[-1].lower().replace(" ", "-")
            if slug in existing_slugs or slug in wiki_files:
                continue
            issues.append({
                "type": "broken_link",
                "file": str(md_file.relative_to(PROJECT_ROOT)),
                "link": raw,
                "severity": "warning",
            })
    return issues


def check_orphaned_articles() -> list[dict]:
    link_targets = set()
    for md_file in WIKI_DIR.rglob("*.md"):
        content = md_file.read_text(encoding="utf-8")
        links = re.findall(r'\[\[([^\]|]+)', content)
        for link in links:
            link_targets.add(link.strip().lower().replace(" ", "-"))
    issues = []
    for md_file in (WIKI_DIR / "concepts").glob("*.md"):
        if md_file.stem not in link_targets and md_file.stem != "_index":
            issues.append({
                "type": "orphaned",
                "file": str(md_file.relative_to(PROJECT_ROOT)),
                "severity": "info",
            })
    return issues


def check_frontmatter() -> list[dict]:
    required_fields = ["title", "tags", "created", "status"]
    issues = []
    for md_file in (WIKI_DIR / "concepts").glob("*.md"):
        try:
            post = frontmatter.load(md_file)
            for field in required_fields:
                if field not in post.metadata:
                    issues.append({
                        "type": "missing_frontmatter",
                        "file": str(md_file.relative_to(PROJECT_ROOT)),
                        "field": field,
                        "severity": "warning",
                    })
        except Exception as e:
            issues.append({
                "type": "invalid_frontmatter",
                "file": str(md_file.relative_to(PROJECT_ROOT)),
                "error": str(e),
                "severity": "error",
            })
    return issues


def check_mermaid_syntax() -> list[dict]:
    """Validate Mermaid code blocks in wiki files."""
    issues = []
    # Mermaid node IDs: only word chars (\w) and hyphens allowed
    valid_node_id = re.compile(r'^[\w-]+$')

    for md_file in WIKI_DIR.rglob("*.md"):
        content = md_file.read_text(encoding="utf-8")
        rel = str(md_file.relative_to(PROJECT_ROOT))

        # Extract mermaid blocks
        blocks = re.findall(r'```mermaid\n(.*?)```', content, re.DOTALL)
        for block in blocks:
            seen_edges = set()
            for line_num, line in enumerate(block.strip().splitlines(), 1):
                stripped = line.strip()
                if not stripped or stripped.startswith("graph ") or stripped.startswith("%%"):
                    continue

                # Match edge lines: nodeA --> nodeB, with optional ["label"] on either side
                edge_match = re.match(
                    r'([\w-]+)(?:\["[^"]*"\])?\s*-->\s*([\w-]+)(?:\["([^"]*)"\])?\s*$', stripped
                )
                if not edge_match:
                    # Check for common errors: bare names with spaces, unquoted labels
                    if '-->' in stripped:
                        issues.append({
                            "type": "mermaid_syntax",
                            "file": rel,
                            "detail": f"Invalid edge syntax: {stripped}",
                            "severity": "error",
                        })
                    continue

                src, tgt, label = edge_match.groups()
                if not valid_node_id.match(src):
                    issues.append({
                        "type": "mermaid_syntax",
                        "file": rel,
                        "detail": f"Invalid node ID: {src}",
                        "severity": "error",
                    })
                if not valid_node_id.match(tgt):
                    issues.append({
                        "type": "mermaid_syntax",
                        "file": rel,
                        "detail": f"Invalid node ID: {tgt}",
                        "severity": "error",
                    })

                edge_key = (src, tgt, label or "")
                if edge_key in seen_edges:
                    issues.append({
                        "type": "mermaid_duplicate",
                        "file": rel,
                        "detail": f"Duplicate edge: {src} --> {tgt}",
                        "severity": "warning",
                    })
                seen_edges.add(edge_key)
    return issues


def check_plugin_dependencies() -> list[dict]:
    """Check for syntax that requires uninstalled Obsidian plugins."""
    issues = []
    plugins_dir = PROJECT_ROOT / ".obsidian" / "plugins"
    installed_plugins = set()
    if plugins_dir.is_dir():
        installed_plugins = {p.name for p in plugins_dir.iterdir() if p.is_dir()}

    # Map: code block language -> required plugin name
    plugin_blocks = {
        "dataview": "dataview",
        "dataviewjs": "dataview",
    }

    for md_file in WIKI_DIR.rglob("*.md"):
        content = md_file.read_text(encoding="utf-8")
        rel = str(md_file.relative_to(PROJECT_ROOT))
        for lang, plugin in plugin_blocks.items():
            if f"```{lang}" in content and plugin not in installed_plugins:
                issues.append({
                    "type": "missing_plugin",
                    "file": rel,
                    "detail": f"Uses ```{lang}``` but '{plugin}' plugin is not installed",
                    "severity": "error",
                })
    return issues


def suggest_improvements() -> list[dict]:
    articles = []
    for md_file in (WIKI_DIR / "concepts").glob("*.md"):
        content = md_file.read_text(encoding="utf-8")[:300]
        articles.append(f"- {md_file.stem}: {content[:200]}")
    if not articles:
        return []
    articles_text = "\n".join(articles)

    prompt = f"""Analyze this knowledge base article list and suggest improvements.

Articles:
{articles_text}

Suggest:
1. Missing concepts that should have their own articles (based on gaps)
2. Articles that might contain contradictory information
3. Potential connections between articles that aren't linked
4. Topics that could benefit from deeper exploration

Return a JSON array of objects with fields:
- "suggestion_type": "new_article" | "contradiction" | "missing_link" | "explore_deeper"
- "description": what to do
- "related_articles": list of relevant article slugs

Return ONLY the JSON array."""

    response = ask(prompt, task="lint", temperature=0.4)
    response = response.strip()
    if response.startswith("```"):
        response = response.split("\n", 1)[1].rsplit("```", 1)[0]
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        return [{"suggestion_type": "error", "description": "Failed to parse suggestions"}]


def _issue_detail(issue: dict) -> str:
    """Extract the most relevant detail string from an issue dict."""
    return issue.get("detail", issue.get("link", issue.get("field", issue.get("error", ""))))


def run_checks() -> list[dict]:
    """Run all lint checks and return issues. Used by compile.py for post-compile validation."""
    checks = [
        ("internal links", check_broken_links),
        ("orphaned articles", check_orphaned_articles),
        ("frontmatter", check_frontmatter),
        ("mermaid syntax", check_mermaid_syntax),
        ("plugin dependencies", check_plugin_dependencies),
    ]
    all_issues = []
    for name, fn in checks:
        all_issues.extend(fn())
    return all_issues


@click.command()
@click.option("--check", is_flag=True, help="Run all checks and report")
@click.option("--fix", is_flag=True, help="Auto-fix issues where possible")
@click.option("--suggest", is_flag=True, help="Get LLM suggestions for improvements")
def lint(check: bool, fix: bool, suggest: bool):
    """Run health checks on the knowledge base wiki."""
    if not any([check, fix, suggest]):
        check = True

    all_issues = []

    if check or fix:
        checks = [
            ("internal links", check_broken_links),
            ("orphaned articles", check_orphaned_articles),
            ("frontmatter", check_frontmatter),
            ("mermaid syntax", check_mermaid_syntax),
            ("plugin dependencies", check_plugin_dependencies),
        ]
        click.echo("Running health checks...\n")
        for i, (name, fn) in enumerate(checks, 1):
            click.echo(f"[{i}/{len(checks)}] Checking {name}...")
            issues = fn()
            all_issues.extend(issues)
            click.echo(f"  Found {len(issues)} issues")

        errors = [i for i in all_issues if i["severity"] == "error"]
        warnings = [i for i in all_issues if i["severity"] == "warning"]
        infos = [i for i in all_issues if i["severity"] == "info"]

        click.echo(f"\nTotal: {len(errors)} errors, {len(warnings)} warnings, {len(infos)} info")

        for issue in all_issues:
            icon = {"error": "✗", "warning": "⚠", "info": "ℹ"}.get(issue["severity"], "?")
            click.echo(f"  {icon} [{issue['type']}] {issue.get('file', '')} — {_issue_detail(issue)}")

    if fix:
        click.echo("\nAuto-fixing issues...")
        broken = [i for i in all_issues if i["type"] == "broken_link"]
        for issue in broken:
            slug = issue["link"].strip().lower().replace(" ", "-")
            stub_path = WIKI_DIR / "concepts" / f"{slug}.md"
            if not stub_path.exists():
                stub_path.write_text(
                    f"---\ntitle: '{issue['link']}'\nstatus: stub\n"
                    f"created: '{datetime.now().strftime('%Y-%m-%d')}'\ntags: []\n---\n\n"
                    f"# {issue['link']}\n\n> This is a stub article. Run `kb compile` to populate.\n",
                    encoding="utf-8",
                )
                click.echo(f"  Created stub: {slug}")

    if suggest:
        click.echo("\nGenerating improvement suggestions...\n")
        suggestions = suggest_improvements()
        for s in suggestions:
            stype = s.get("suggestion_type", "unknown")
            desc = s.get("description", "")
            related = ", ".join(s.get("related_articles", []))
            click.echo(f"  [{stype}] {desc}")
            if related:
                click.echo(f"    Related: {related}")


if __name__ == "__main__":
    lint()
