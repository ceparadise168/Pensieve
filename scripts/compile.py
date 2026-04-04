"""
Wiki Compiler — the heart of the knowledge base.
Reads raw/ sources and compiles/updates wiki/ articles.

Usage:
    python scripts/compile.py --full
    python scripts/compile.py --incremental
    python scripts/compile.py --article "concept-name"
"""
import click
import json
import re
import hashlib
from datetime import datetime
from pathlib import Path

import frontmatter

from utils.llm_client import ask, ask_with_context
from lint import run_checks

PROJECT_ROOT = Path(__file__).parent.parent
RAW_DIR = PROJECT_ROOT / "raw"
WIKI_DIR = PROJECT_ROOT / "wiki"
STATE_FILE = PROJECT_ROOT / ".compile_state.json"


def _load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"file_hashes": {}, "last_compile": None}


def _save_state(state: dict):
    state["last_compile"] = datetime.now().isoformat()
    STATE_FILE.write_text(json.dumps(state, indent=2))


def _file_hash(path: Path) -> str:
    return hashlib.md5(path.read_bytes()).hexdigest()


def _get_changed_files(state: dict) -> tuple[list[Path], dict[str, str]]:
    """Find raw files that are new or changed since last compile.
    Returns (changed_files, new_hashes) without mutating state.
    """
    changed = []
    new_hashes = {}
    for md_file in RAW_DIR.rglob("*.md"):
        h = _file_hash(md_file)
        rel = str(md_file.relative_to(PROJECT_ROOT))
        if state["file_hashes"].get(rel) != h:
            changed.append(md_file)
            new_hashes[rel] = h
    return changed, new_hashes


def step_1_summarize_sources(sources: list[Path]) -> list[dict]:
    summaries = []
    for src in sources:
        try:
            content = src.read_text(encoding="utf-8")
            rel_path = str(src.relative_to(PROJECT_ROOT))
            summary = ask(
                f"Summarize the following document in 3-5 paragraphs. "
                f"Focus on key concepts, findings, and actionable insights.\n\n"
                f"Document: {src.name}\n\n"
                f"<document>\n{content[:12000]}\n</document>",
                task="summarize",
            )
            slug = src.stem
            summary_path = WIKI_DIR / "summaries" / f"{slug}.md"
            summary_path.parent.mkdir(parents=True, exist_ok=True)
            summary_path.write_text(
                f"---\ntitle: 'Summary: {slug}'\n"
                f"source: '{rel_path}'\n"
                f"compiled: '{datetime.now().strftime('%Y-%m-%d')}'\n"
                f"type: summary\n---\n\n{summary}",
                encoding="utf-8",
            )
            summaries.append({
                "source": rel_path,
                "summary_path": str(summary_path.relative_to(PROJECT_ROOT)),
                "summary": summary[:500],
            })
            click.echo(f"  Summarized: {src.name}")
        except Exception as e:
            click.echo(f"  ERROR summarizing {src.name}: {e}", err=True)
    return summaries


def step_2_extract_concepts(summaries: list[dict]) -> list[str]:
    all_summaries = "\n\n".join(
        f"[{s['source']}]: {s['summary']}" for s in summaries
    )
    existing = [p.stem for p in (WIKI_DIR / "concepts").glob("*.md")]
    prompt = f"""Analyze these document summaries and identify all key concepts
that deserve their own wiki article.

Existing concepts (avoid duplicates): {', '.join(existing) if existing else 'none'}

Summaries:
{all_summaries}

Return a JSON array of objects, each with:
- "slug": URL-friendly concept name (lowercase, hyphens)
- "title": Human-readable title
- "description": One-sentence description
- "related_sources": list of source file paths that discuss this concept

Return ONLY the JSON array, no markdown fences or explanation."""

    response = ask(prompt, task="compile_article", temperature=0.2)
    response = response.strip()
    if response.startswith("```"):
        response = response.split("\n", 1)[1].rsplit("```", 1)[0]
    try:
        concepts = json.loads(response)
    except json.JSONDecodeError:
        click.echo("  Warning: Failed to parse concepts JSON, retrying...")
        try:
            concepts = json.loads(ask(
                f"Fix this JSON and return ONLY valid JSON:\n{response}",
                task="summarize",
                temperature=0.0,
            ))
        except (json.JSONDecodeError, Exception) as e:
            click.echo(f"  ERROR: Could not extract concepts: {e}", err=True)
            return []
    return concepts


def step_3_write_concept_articles(concepts: list[dict]):
    for concept in concepts:
        slug = concept["slug"]
        try:
            article_path = WIKI_DIR / "concepts" / f"{slug}.md"
            source_contents = []
            for src_rel in concept.get("related_sources", []):
                src_path = PROJECT_ROOT / src_rel
                if src_path.exists():
                    source_contents.append(src_path.read_text(encoding="utf-8")[:8000])
            context = "\n\n---\n\n".join(source_contents)
            existing_content = ""
            if article_path.exists():
                existing_content = article_path.read_text(encoding="utf-8")
            if existing_content:
                prompt = f"""Update the following wiki article with new information from the sources below.
Preserve existing accurate content. Add new insights. Fix any inconsistencies.

EXISTING ARTICLE:
<article>
{existing_content}
</article>

NEW SOURCE MATERIAL:
<sources>
{context}
</sources>

Return the COMPLETE updated article in markdown with YAML frontmatter."""
            else:
                prompt = f"""Write a comprehensive wiki article about: {concept['title']}

Description: {concept['description']}

Use the following source material:
<sources>
{context}
</sources>

Requirements:
- Start with YAML frontmatter (title, aliases, tags, sources, created, updated, status)
- Write a clear introduction paragraph
- Organize into logical sections with ## headings
- Include a ## Related section with wiki-links to potentially related concepts
- Include a ## Sources section linking back to raw/ files
- Be thorough but concise. Target 500-1500 words.
- Use wiki-style internal links: [[concept-slug]]"""

            article_content = ask(prompt, task="compile_article", max_tokens=8192)
            article_path.parent.mkdir(parents=True, exist_ok=True)
            article_path.write_text(article_content, encoding="utf-8")
            click.echo(f"  Wrote: {article_path.name}")
        except Exception as e:
            click.echo(f"  ERROR writing article {slug}: {e}", err=True)


def step_4_build_index():
    articles = []
    for md_file in sorted((WIKI_DIR / "concepts").glob("*.md")):
        try:
            post = frontmatter.load(md_file)
            articles.append({
                "slug": md_file.stem,
                "title": post.get("title", md_file.stem),
                "tags": post.get("tags", []),
                "summary": post.content[:200].replace("\n", " "),
                "status": post.get("status", "draft"),
            })
        except Exception:
            articles.append({"slug": md_file.stem, "title": md_file.stem})

    lines = [
        "---",
        "title: 'Knowledge Base Index'",
        f"updated: '{datetime.now().strftime('%Y-%m-%d')}'",
        f"total_articles: {len(articles)}",
        "---",
        "",
        "# Knowledge Base Index",
        "",
        f"Total articles: {len(articles)}",
        "",
    ]
    tag_map = {}
    for a in articles:
        for tag in a.get("tags", ["untagged"]):
            tag_map.setdefault(tag, []).append(a)
    for tag in sorted(tag_map.keys()):
        lines.append(f"## {tag}")
        lines.append("")
        for a in tag_map[tag]:
            status = a.get("status", "")
            marker = " ✓" if status == "published" else ""
            lines.append(f"- [[{a['slug']}|{a.get('title', a['slug'])}]]{marker}")
        lines.append("")

    (WIKI_DIR / "_index.md").write_text("\n".join(lines), encoding="utf-8")
    click.echo(f"  Index updated: {len(articles)} articles")


def step_5_build_glossary():
    """Build a glossary of key terms extracted from concept articles."""
    terms = {}
    for md_file in (WIKI_DIR / "concepts").glob("*.md"):
        try:
            post = frontmatter.load(md_file)
            title = post.get("title", md_file.stem)
            # Use first paragraph after frontmatter as brief definition
            content_lines = post.content.strip().split("\n")
            # Skip heading lines to find first paragraph
            definition = ""
            for line in content_lines:
                stripped = line.strip()
                if stripped and not stripped.startswith("#"):
                    definition = stripped[:200]
                    break
            terms[title] = {
                "slug": md_file.stem,
                "definition": definition,
            }
        except Exception:
            pass

    lines = [
        "---",
        "title: 'Glossary'",
        f"updated: '{datetime.now().strftime('%Y-%m-%d')}'",
        f"total_terms: {len(terms)}",
        "---",
        "",
        "# Glossary",
        "",
    ]
    for term in sorted(terms.keys(), key=str.lower):
        entry = terms[term]
        lines.append(f"**[[{entry['slug']}|{term}]]**")
        if entry["definition"]:
            lines.append(f": {entry['definition']}")
        lines.append("")

    (WIKI_DIR / "_glossary.md").write_text("\n".join(lines), encoding="utf-8")
    click.echo(f"  Glossary updated: {len(terms)} terms")


def step_6_build_graph():
    concepts_dir = WIKI_DIR / "concepts"
    graph = {}
    for md_file in concepts_dir.glob("*.md"):
        content = md_file.read_text(encoding="utf-8")
        slug = md_file.stem
        links = re.findall(r'\[\[([^\]|]+)', content)
        graph[slug] = links

    lines = [
        "---",
        "title: 'Concept Graph'",
        f"updated: '{datetime.now().strftime('%Y-%m-%d')}'",
        "---",
        "",
        "# Concept Relationship Graph",
        "",
        "```mermaid",
        "graph LR",
    ]
    seen_edges = set()
    for source, targets in graph.items():
        for target in targets:
            # Slugify for valid Mermaid node IDs
            target_id = re.sub(r'[^\w-]', '', target.strip().lower().replace(" ", "-"))
            if not target_id:
                continue
            edge_key = (source, target_id)
            if edge_key in seen_edges:
                continue
            seen_edges.add(edge_key)
            # Escape quotes in label to prevent Mermaid parse errors
            safe_label = target.strip().replace('"', '#quot;')
            lines.append(f'    {source} --> {target_id}["{safe_label}"]')
    lines.append("```")
    lines.append("")
    lines.append("## Adjacency List")
    lines.append("")
    for source, targets in sorted(graph.items()):
        if targets:
            links_str = ", ".join(f"[[{t}]]" for t in targets)
            lines.append(f"- **{source}** → {links_str}")

    (WIKI_DIR / "_graph.md").write_text("\n".join(lines), encoding="utf-8")
    click.echo(f"  Graph updated: {len(graph)} nodes")


def step_7_build_dashboard():
    """Build a static dashboard — no Dataview plugin required."""
    articles = []
    for md_file in sorted((WIKI_DIR / "concepts").glob("*.md")):
        try:
            post = frontmatter.load(md_file)
            articles.append({
                "slug": md_file.stem,
                "title": post.get("title", md_file.stem),
                "tags": post.get("tags", []),
                "status": post.get("status", "draft"),
                "updated": str(post.get("updated", post.get("created", ""))),
            })
        except Exception:
            articles.append({
                "slug": md_file.stem, "title": md_file.stem,
                "tags": [], "status": "unknown", "updated": "",
            })

    # Sort by updated date descending
    articles.sort(key=lambda a: a["updated"], reverse=True)

    lines = [
        "---",
        "title: 'Knowledge Base Dashboard'",
        f"updated: '{datetime.now().strftime('%Y-%m-%d')}'",
        "---",
        "",
        "# Knowledge Base Dashboard",
        "",
        "## Recent Articles",
        "",
        "| Article | Status | Updated |",
        "|---------|--------|---------|",
    ]
    for a in articles[:20]:
        lines.append(f"| [[concepts/{a['slug']}|{a['title']}]] | {a['status']} | {a['updated']} |")

    # Draft / stub sections
    drafts = [a for a in articles if a["status"] in ("draft", "stub")]
    if drafts:
        lines += ["", "## Drafts & Stubs", ""]
        for a in drafts:
            lines.append(f"- [[concepts/{a['slug']}|{a['title']}]] ({a['status']})")

    # Tag cloud
    tag_map: dict[str, list] = {}
    for a in articles:
        for tag in a.get("tags", []):
            tag_map.setdefault(tag, []).append(a)
    if tag_map:
        lines += ["", "## Tags", ""]
        for tag in sorted(tag_map, key=lambda t: len(tag_map[t]), reverse=True):
            article_links = ", ".join(
                f"[[concepts/{a['slug']}|{a['title']}]]" for a in tag_map[tag]
            )
            lines.append(f"- `#{tag}` ({len(tag_map[tag])}) — {article_links}")

    lines += [
        "", "## Navigation", "",
        "- [[_index|Wiki Index]]",
        "- [[_graph|Concept Graph]]",
        "- [[_glossary|Glossary]]",
    ]

    (WIKI_DIR / "_dashboard.md").write_text("\n".join(lines), encoding="utf-8")
    click.echo(f"  Dashboard updated: {len(articles)} articles")


def step_8_post_compile_lint() -> bool:
    """Run lint checks after compilation. Returns True if no errors found."""
    issues = run_checks()
    errors = [i for i in issues if i["severity"] == "error"]
    warnings = [i for i in issues if i["severity"] == "warning"]
    if errors or warnings:
        click.echo(f"\n  {len(errors)} errors, {len(warnings)} warnings")
        for issue in errors + warnings:
            icon = "✗" if issue["severity"] == "error" else "⚠"
            detail = issue.get("detail", issue.get("link", issue.get("field", "")))
            click.echo(f"    {icon} [{issue['type']}] {issue.get('file', '')} — {detail}")
    else:
        click.echo("  All checks passed")
    return len(errors) == 0


@click.command()
@click.option("--full", is_flag=True, help="Full recompilation of all sources")
@click.option("--article", type=str, help="Recompile a specific article by slug")
def compile_wiki(full: bool, article: str):
    """Compile the wiki from raw sources."""
    state = _load_state()

    if article:
        click.echo(f"Recompiling article: {article}")
        concept_path = WIKI_DIR / "concepts" / f"{article}.md"
        if concept_path.exists():
            post = frontmatter.load(concept_path)
            sources = [PROJECT_ROOT / s for s in post.get("sources", [])]
            step_3_write_concept_articles([{
                "slug": article,
                "title": post.get("title", article),
                "description": "",
                "related_sources": [str(s.relative_to(PROJECT_ROOT)) for s in sources],
            }])
        return

    new_hashes = {}
    if full:
        sources = list(RAW_DIR.rglob("*.md"))
        click.echo(f"Full compile: {len(sources)} source files")
    else:
        sources, new_hashes = _get_changed_files(state)
        if not sources:
            click.echo("No changes detected. Use --full to force recompilation.")
            return
        click.echo(f"Incremental compile: {len(sources)} changed files")

    click.echo("\n[Step 1/8] Summarizing sources...")
    summaries = step_1_summarize_sources(sources)

    # Save state after summarization so successful work is not lost
    if new_hashes:
        state["file_hashes"].update(new_hashes)
        _save_state(state)

    click.echo("\n[Step 2/8] Extracting concepts...")
    concepts = step_2_extract_concepts(summaries)
    click.echo(f"  Found {len(concepts)} concepts")

    click.echo("\n[Step 3/8] Writing concept articles...")
    step_3_write_concept_articles(concepts)

    click.echo("\n[Step 4/8] Building index...")
    step_4_build_index()

    click.echo("\n[Step 5/8] Building glossary...")
    step_5_build_glossary()

    click.echo("\n[Step 6/8] Building concept graph...")
    step_6_build_graph()

    click.echo("\n[Step 7/8] Building dashboard...")
    step_7_build_dashboard()

    click.echo("\n[Step 8/8] Post-compile validation...")
    passed = step_8_post_compile_lint()

    _save_state(state)
    if passed:
        click.echo(f"\nCompilation complete. Wiki: {WIKI_DIR}")
    else:
        click.echo(f"\nCompilation complete with issues. Run `kb lint --fix` to auto-repair.")


if __name__ == "__main__":
    compile_wiki()
