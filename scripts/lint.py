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
    for md_file in WIKI_DIR.rglob("*.md"):
        content = md_file.read_text(encoding="utf-8")
        links = re.findall(r'\[\[([^\]|]+)', content)
        for link in links:
            slug = link.strip().lower().replace(" ", "-")
            if slug not in existing_slugs:
                issues.append({
                    "type": "broken_link",
                    "file": str(md_file.relative_to(PROJECT_ROOT)),
                    "link": link,
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
        click.echo("Running health checks...\n")

        click.echo("[1/3] Checking internal links...")
        issues = check_broken_links()
        all_issues.extend(issues)
        click.echo(f"  Found {len(issues)} broken links")

        click.echo("[2/3] Checking for orphaned articles...")
        issues = check_orphaned_articles()
        all_issues.extend(issues)
        click.echo(f"  Found {len(issues)} orphaned articles")

        click.echo("[3/3] Checking frontmatter...")
        issues = check_frontmatter()
        all_issues.extend(issues)
        click.echo(f"  Found {len(issues)} frontmatter issues")

        errors = [i for i in all_issues if i["severity"] == "error"]
        warnings = [i for i in all_issues if i["severity"] == "warning"]
        infos = [i for i in all_issues if i["severity"] == "info"]

        click.echo(f"\nTotal: {len(errors)} errors, {len(warnings)} warnings, {len(infos)} info")

        for issue in all_issues:
            icon = {"error": "✗", "warning": "⚠", "info": "ℹ"}.get(issue["severity"], "?")
            click.echo(f"  {icon} [{issue['type']}] {issue.get('file', '')} — {issue.get('link', issue.get('field', issue.get('error', '')))}")

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
