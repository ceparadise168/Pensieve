"""Markdown parsing helpers for the Knowledge Base."""
from pathlib import Path
from markdownify import markdownify
import subprocess


def html_to_markdown(html: str) -> str:
    """Convert HTML content to clean Markdown."""
    return markdownify(html, heading_style="ATX", strip=["script", "style"])


def pdf_to_markdown(pdf_path: Path) -> str:
    """Convert PDF to Markdown using pymupdf."""
    import pymupdf

    doc = pymupdf.open(str(pdf_path))
    pages = []
    for page in doc:
        text = page.get_text("text")
        if text.strip():
            pages.append(text)
    doc.close()
    if not pages:
        raise RuntimeError(f"No text extracted from {pdf_path}")
    return "\n\n---\n\n".join(pages)


def find_relevant_files(
    wiki_dir: Path, keywords: list[str], top_k: int = 10
) -> list[Path]:
    """Find wiki files containing the most keyword matches."""
    scores = {}
    for md_file in wiki_dir.rglob("*.md"):
        content = md_file.read_text(encoding="utf-8").lower()
        score = sum(content.count(kw.lower()) for kw in keywords)
        if score > 0:
            scores[md_file] = score
    ranked = sorted(scores.items(), key=lambda x: -x[1])
    return [p for p, _ in ranked[:top_k]]
