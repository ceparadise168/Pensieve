"""
Article Remover — safely remove articles from the knowledge base.

Usage:
    python scripts/remove.py <slug>                           # by concept slug
    python scripts/remove.py raw/articles/test.pdf            # by raw source
    python scripts/remove.py raw/articles/a.pdf raw/b.pdf     # multiple sources
    python scripts/remove.py <target> --dry-run
"""
import re
import click
from pathlib import Path

import frontmatter

from data_repo import snapshot, is_initialized, init
from compile import step_4_build_index, step_5_build_glossary, step_6_build_graph, step_7_build_dashboard

PROJECT_ROOT = Path(__file__).parent.parent
RAW_DIR = PROJECT_ROOT / "raw"
WIKI_DIR = PROJECT_ROOT / "wiki"


# ── Helpers ──────────────────────────────────────────────────────────────────

def _source_matches(entry: str, source_path: Path) -> bool:
    """Check if a frontmatter source entry matches a given raw source path.
    Handles both path-style ('raw/articles/foo.pdf') and name-style ('Foo Bar') entries.
    """
    entry = entry.strip()
    rel = str(source_path.relative_to(PROJECT_ROOT))
    stem = source_path.stem
    return entry == rel or entry == str(source_path) or entry == stem


def list_articles():
    """List all concept articles."""
    concepts_dir = WIKI_DIR / "concepts"
    if not concepts_dir.exists():
        return []
    articles = []
    for md_file in sorted(concepts_dir.glob("*.md")):
        if md_file.name == ".gitkeep":
            continue
        try:
            post = frontmatter.load(md_file)
            title = post.get("title", md_file.stem)
        except Exception:
            title = md_file.stem
        articles.append({"slug": md_file.stem, "title": title})
    return articles


def find_backlinks(slug: str) -> list[tuple[Path, str, str]]:
    """Find all wiki files that link to this slug.
    Returns list of (file_path, original_link_text, display_text).
    """
    backlinks = []
    for md_file in WIKI_DIR.rglob("*.md"):
        content = md_file.read_text(encoding="utf-8")
        # Match [[slug|display]] or [[slug]]
        for match in re.finditer(r'\[\[(' + re.escape(slug) + r')(?:\|([^\]]*))?\]\]', content):
            full_match = match.group(0)
            display = match.group(2) or match.group(1)
            backlinks.append((md_file, full_match, display))
        # Also match path-style links like [[concepts/slug|display]]
        for match in re.finditer(r'\[\[concepts/' + re.escape(slug) + r'(?:\|([^\]]*))?\]\]', content):
            full_match = match.group(0)
            display = match.group(1) or slug
            backlinks.append((md_file, full_match, display))
    return backlinks


def clean_backlinks(slugs: list[str], dry_run: bool = False) -> list[str]:
    """Remove or replace backlinks to removed articles. Returns files modified."""
    all_backlinks: dict[Path, list[tuple[str, str]]] = {}
    for slug in slugs:
        for fpath, link_text, display in find_backlinks(slug):
            all_backlinks.setdefault(fpath, []).append((link_text, display))

    modified = []
    for fpath, replacements in all_backlinks.items():
        content = fpath.read_text(encoding="utf-8")
        for link_text, display in replacements:
            content = content.replace(link_text, display)
        if not dry_run:
            fpath.write_text(content, encoding="utf-8")
        modified.append(str(fpath.relative_to(PROJECT_ROOT)))
    return modified


def _rebuild_indices():
    click.echo("\nRebuilding indices...")
    step_4_build_index()
    step_5_build_glossary()
    step_6_build_graph()
    step_7_build_dashboard()


def _ensure_data_repo():
    if not is_initialized():
        init()


# ── Remove by slug ───────────────────────────────────────────────────────────

def find_related_files(slug: str) -> dict:
    """Find all files related to a concept article."""
    files = {"concept": None, "summary": None, "raw_sources": [], "images": []}

    concept_path = WIKI_DIR / "concepts" / f"{slug}.md"
    if concept_path.exists():
        files["concept"] = concept_path
        try:
            post = frontmatter.load(concept_path)
            for src in post.get("sources", []):
                src_path = PROJECT_ROOT / src
                if src_path.exists():
                    files["raw_sources"].append(src_path)
        except Exception:
            pass

        content = concept_path.read_text(encoding="utf-8")
        for img_match in re.findall(r'!\[.*?\]\(([^)]+)\)', content):
            img_path = (concept_path.parent / img_match).resolve()
            if img_path.exists() and "wiki/images" in str(img_path):
                files["images"].append(img_path)

    summary_path = WIKI_DIR / "summaries" / f"{slug}.md"
    if summary_path.exists():
        files["summary"] = summary_path

    return files


def remove_by_slug(slug: str, keep_raw: bool, dry_run: bool, yes: bool):
    """Remove a single concept article by slug."""
    files = find_related_files(slug)

    if not files["concept"]:
        click.echo(f"Article not found: {slug}")
        click.echo("\nAvailable articles:")
        for a in list_articles():
            click.echo(f"  {a['slug']}  ({a['title']})")
        return

    click.echo(f"\n{'[DRY RUN] ' if dry_run else ''}Removing: {slug}")
    click.echo("─" * 40)

    to_delete = []
    click.echo("\nFiles to delete:")
    if files["concept"]:
        click.echo(f"  {files['concept'].relative_to(PROJECT_ROOT)}")
        to_delete.append(files["concept"])
    if files["summary"]:
        click.echo(f"  {files['summary'].relative_to(PROJECT_ROOT)}")
        to_delete.append(files["summary"])
    if files["raw_sources"] and not keep_raw:
        for src in files["raw_sources"]:
            click.echo(f"  {src.relative_to(PROJECT_ROOT)}")
            to_delete.append(src)
    elif files["raw_sources"]:
        click.echo(f"\n  (keeping {len(files['raw_sources'])} raw source files)")
    if files["images"]:
        for img in files["images"]:
            click.echo(f"  {img.relative_to(PROJECT_ROOT)}")
            to_delete.append(img)

    backlinks = find_backlinks(slug)
    if backlinks:
        click.echo(f"\nBacklinks to clean ({len(backlinks)} references):")
        seen = set()
        for fpath, _, _ in backlinks:
            rel = str(fpath.relative_to(PROJECT_ROOT))
            if rel not in seen:
                count = sum(1 for f, _, _ in backlinks if f == fpath)
                click.echo(f"  {rel}  ({count} links → plain text)")
                seen.add(rel)

    if dry_run:
        click.echo("\n[DRY RUN] No changes made.")
        return

    if not yes:
        click.echo()
        if not click.confirm("Proceed with removal?"):
            click.echo("Cancelled.")
            return

    _ensure_data_repo()
    snapshot(f"before removing: {slug}")

    click.echo("\nDeleting files...")
    for f in to_delete:
        f.unlink()
        click.echo(f"  Deleted: {f.relative_to(PROJECT_ROOT)}")

    if backlinks:
        click.echo("\nCleaning backlinks...")
        for m in clean_backlinks([slug]):
            click.echo(f"  Updated: {m}")

    _rebuild_indices()
    snapshot(f"removed: {slug}")
    click.echo(f"\nDone. To undo: kb undo")


# ── Remove by source ─────────────────────────────────────────────────────────

def find_derived_from_sources(source_paths: list[Path]) -> dict:
    """Given raw source paths, find all derived wiki content.

    Returns:
        {
            "remove_concepts": [(slug, path)],   # concepts whose ALL sources are being removed
            "update_concepts": [(slug, path, remaining_sources)],  # concepts with other sources left
            "summaries": [path],
            "source_files": [path],
        }
    """
    result = {
        "remove_concepts": [],
        "update_concepts": [],
        "summaries": [],
        "source_files": list(source_paths),
    }

    concepts_dir = WIKI_DIR / "concepts"
    if not concepts_dir.exists():
        return result

    for md_file in concepts_dir.glob("*.md"):
        if md_file.name == ".gitkeep":
            continue
        try:
            post = frontmatter.load(md_file)
        except Exception:
            continue

        concept_sources = post.get("sources", [])
        if not concept_sources:
            continue

        # Check which of this concept's sources are in the removal set
        matched = []
        remaining = []
        for entry in concept_sources:
            if any(_source_matches(entry, sp) for sp in source_paths):
                matched.append(entry)
            else:
                remaining.append(entry)

        if not matched:
            continue

        slug = md_file.stem
        if remaining:
            result["update_concepts"].append((slug, md_file, remaining))
        else:
            result["remove_concepts"].append((slug, md_file))

    # Find summaries matching source stems
    summaries_dir = WIKI_DIR / "summaries"
    if summaries_dir.exists():
        for sp in source_paths:
            summary = summaries_dir / f"{sp.stem}.md"
            if summary.exists():
                result["summaries"].append(summary)

    return result


def remove_by_source(source_paths: list[Path], dry_run: bool, yes: bool):
    """Remove everything derived from the given raw source files."""
    # Validate source paths
    valid = []
    for sp in source_paths:
        if sp.exists():
            valid.append(sp)
        else:
            click.echo(f"Source not found: {sp.relative_to(PROJECT_ROOT)}")
    if not valid:
        click.echo("\nNo valid source files to remove.")
        return

    derived = find_derived_from_sources(valid)
    source_names = ", ".join(sp.name for sp in valid)

    click.echo(f"\n{'[DRY RUN] ' if dry_run else ''}Removing source: {source_names}")
    click.echo("─" * 50)

    # Show raw source files
    click.echo(f"\nRaw sources to delete ({len(derived['source_files'])}):")
    for sp in derived["source_files"]:
        click.echo(f"  {sp.relative_to(PROJECT_ROOT)}")

    # Show summaries
    if derived["summaries"]:
        click.echo(f"\nSummaries to delete ({len(derived['summaries'])}):")
        for sp in derived["summaries"]:
            click.echo(f"  {sp.relative_to(PROJECT_ROOT)}")

    # Show concepts to fully remove
    if derived["remove_concepts"]:
        click.echo(f"\nConcepts to delete ({len(derived['remove_concepts'])}):")
        for slug, path in derived["remove_concepts"]:
            click.echo(f"  {path.relative_to(PROJECT_ROOT)}  ({slug})")

    # Show concepts to update (strip source from frontmatter)
    if derived["update_concepts"]:
        click.echo(f"\nConcepts to update ({len(derived['update_concepts'])}):")
        for slug, path, remaining in derived["update_concepts"]:
            remaining_str = ", ".join(remaining)
            click.echo(f"  {slug}  (remaining sources: {remaining_str})")

    # Count backlinks for concepts being fully removed
    slugs_to_remove = [slug for slug, _ in derived["remove_concepts"]]
    total_backlinks = 0
    if slugs_to_remove:
        for slug in slugs_to_remove:
            total_backlinks += len(find_backlinks(slug))
        if total_backlinks:
            click.echo(f"\nBacklinks to clean: {total_backlinks} references")

    if not any([derived["remove_concepts"], derived["update_concepts"],
                derived["summaries"], derived["source_files"]]):
        click.echo("\nNothing derived from these sources found.")
        return

    if dry_run:
        click.echo("\n[DRY RUN] No changes made.")
        return

    if not yes:
        click.echo()
        if not click.confirm("Proceed with removal?"):
            click.echo("Cancelled.")
            return

    _ensure_data_repo()
    snapshot(f"before removing source: {source_names}")

    # Delete raw source files
    click.echo("\nDeleting raw sources...")
    for sp in derived["source_files"]:
        sp.unlink()
        click.echo(f"  Deleted: {sp.relative_to(PROJECT_ROOT)}")

    # Delete summaries
    if derived["summaries"]:
        click.echo("\nDeleting summaries...")
        for sp in derived["summaries"]:
            sp.unlink()
            click.echo(f"  Deleted: {sp.relative_to(PROJECT_ROOT)}")

    # Delete concepts (fully removed)
    if derived["remove_concepts"]:
        click.echo("\nDeleting concepts...")
        for slug, path in derived["remove_concepts"]:
            path.unlink()
            click.echo(f"  Deleted: {path.relative_to(PROJECT_ROOT)}")

    # Update concepts (strip removed source from frontmatter)
    if derived["update_concepts"]:
        click.echo("\nUpdating concept sources...")
        for slug, path, remaining in derived["update_concepts"]:
            post = frontmatter.load(path)
            post["sources"] = remaining
            path.write_text(frontmatter.dumps(post), encoding="utf-8")
            click.echo(f"  Updated: {slug} (kept {len(remaining)} sources)")

    # Clean backlinks for fully removed concepts
    if slugs_to_remove:
        click.echo("\nCleaning backlinks...")
        for m in clean_backlinks(slugs_to_remove):
            click.echo(f"  Updated: {m}")

    _rebuild_indices()
    snapshot(f"removed source: {source_names}")
    click.echo(f"\nDone. To undo: kb undo")


# ── CLI ──────────────────────────────────────────────────────────────────────

def _is_source_path(target: str) -> bool:
    """Detect if the target is a raw source path (vs a concept slug)."""
    return "/" in target or target.startswith("raw")


@click.command()
@click.argument("targets", nargs=-1, required=True)
@click.option("--keep-raw", is_flag=True, help="Keep raw source files (slug mode only)")
@click.option("--dry-run", is_flag=True, help="Show what would be removed without doing it")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt")
def remove(targets: tuple[str], keep_raw: bool, dry_run: bool, yes: bool):
    """Remove articles from the knowledge base.

    TARGET can be a concept slug or a raw source path.
    Multiple source paths can be passed at once.

    \b
    Examples:
        kb remove zen-meditation              # by concept slug
        kb remove raw/articles/test.pdf       # by raw source
        kb remove raw/articles/a.pdf raw/articles/b.pdf  # multiple sources
    """
    if any(_is_source_path(t) for t in targets):
        source_paths = [PROJECT_ROOT / t for t in targets]
        remove_by_source(source_paths, dry_run, yes)
    elif len(targets) == 1:
        remove_by_slug(targets[0], keep_raw, dry_run, yes)
    else:
        # Multiple slugs — remove each one
        for slug in targets:
            remove_by_slug(slug, keep_raw, dry_run, yes)


if __name__ == "__main__":
    remove()
