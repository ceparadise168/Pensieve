"""
Q&A Engine — ask questions against the compiled wiki.

Usage:
    python scripts/query.py "What are the key differences between X and Y?"
    python scripts/query.py --output report "Comprehensive analysis of Z"
    python scripts/query.py --output slides "Overview of topic X"
"""
import click
import json
import subprocess
from datetime import datetime
from pathlib import Path

import frontmatter

from utils.llm_client import ask, ask_with_context, embed_text
from utils.markdown_utils import find_relevant_files

PROJECT_ROOT = Path(__file__).parent.parent
WIKI_DIR = PROJECT_ROOT / "wiki"
OUTPUT_DIR = PROJECT_ROOT / "output"


def _read_index() -> str:
    index_path = WIKI_DIR / "_index.md"
    if index_path.exists():
        return index_path.read_text(encoding="utf-8")
    return ""


def _find_relevant_articles(question: str, top_k: int = 10) -> list[Path]:
    index = _read_index()
    prompt = f"""Given this question and the knowledge base index below,
select the {top_k} most relevant article slugs to answer the question.

Question: {question}

Index:
{index}

Return ONLY a JSON array of slug strings, e.g. ["concept-a", "concept-b"].
If fewer than {top_k} are relevant, return fewer."""

    response = ask(prompt, task="query_simple", temperature=0.1)
    response = response.strip().strip("`").strip()
    if response.startswith("json"):
        response = response[4:]

    try:
        slugs = json.loads(response)
    except json.JSONDecodeError:
        slugs = [p.stem for p in (WIKI_DIR / "concepts").glob("*.md")][:top_k]

    paths = []
    for slug in slugs:
        p = WIKI_DIR / "concepts" / f"{slug}.md"
        if p.exists():
            paths.append(p)
    for slug in slugs:
        p = WIKI_DIR / "summaries" / f"{slug}.md"
        if p.exists():
            paths.append(p)
    return paths


def _query_text(question: str) -> str:
    relevant = _find_relevant_articles(question)
    click.echo(f"  Found {len(relevant)} relevant articles")
    return ask_with_context(
        question=question,
        context_files=[str(p) for p in relevant],
        task="query_complex",
    )


def _query_report(question: str) -> Path:
    relevant = _find_relevant_articles(question, top_k=15)
    context = []
    for p in relevant:
        context.append(p.read_text(encoding="utf-8")[:6000])
    full_context = "\n\n---\n\n".join(context)

    prompt = f"""Write a comprehensive research report answering the following question.

Question: {question}

Use the following knowledge base articles as sources:
{full_context}

Requirements:
- Start with a YAML frontmatter block (title, date, question, sources)
- Write an executive summary (2-3 paragraphs)
- Organize findings into logical sections
- Include specific citations to source documents
- End with a conclusion and open questions
- Target 1500-3000 words
"""
    report = ask(prompt, task="query_complex", max_tokens=16384)
    slug = datetime.now().strftime("%Y%m%d") + "-" + question[:40].lower().replace(" ", "-")
    report_path = OUTPUT_DIR / "reports" / f"{slug}.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")
    return report_path


def _query_slides(question: str) -> Path:
    relevant = _find_relevant_articles(question, top_k=10)
    context = []
    for p in relevant:
        context.append(p.read_text(encoding="utf-8")[:4000])
    full_context = "\n\n---\n\n".join(context)

    prompt = f"""Create a Marp-format slide presentation about:

{question}

Use the following knowledge base articles as source material:
{full_context}

Requirements:
- Use Marp markdown format (--- as slide separator)
- First slide: title slide with marp frontmatter
- 8-15 slides total
- Each slide: clear heading + 3-5 bullet points or a key diagram
- Use mermaid code blocks for diagrams where helpful
- Last slide: key takeaways and open questions

Start with:
---
marp: true
theme: default
paginate: true
---
"""
    slides = ask(prompt, task="generate_slides", max_tokens=8192)
    slug = datetime.now().strftime("%Y%m%d") + "-" + question[:40].lower().replace(" ", "-")
    slides_path = OUTPUT_DIR / "slides" / f"{slug}.md"
    slides_path.parent.mkdir(parents=True, exist_ok=True)
    slides_path.write_text(slides, encoding="utf-8")

    html_path = slides_path.with_suffix(".html")
    try:
        subprocess.run(
            ["npx", "marp", str(slides_path), "-o", str(html_path)],
            check=True, capture_output=True,
        )
        click.echo(f"  HTML slides: {html_path}")
    except (subprocess.CalledProcessError, FileNotFoundError):
        click.echo("  Warning: marp-cli not available, HTML not generated")
    return slides_path


@click.command()
@click.argument("question")
@click.option("--output", type=click.Choice(["text", "report", "slides"]), default="text")
@click.option("--file-back", is_flag=True, help="File the output back into wiki")
def query(question: str, output: str, file_back: bool):
    """Ask a question against the knowledge base."""
    click.echo(f"Question: {question}")
    click.echo(f"Output format: {output}")

    if output == "text":
        answer = _query_text(question)
        click.echo(f"\n{answer}")
    elif output == "report":
        report_path = _query_report(question)
        click.echo(f"\nReport saved: {report_path}")
        if file_back:
            dest = WIKI_DIR / "connections" / report_path.name
            dest.parent.mkdir(parents=True, exist_ok=True)
            import shutil
            shutil.copy2(report_path, dest)
            click.echo(f"Filed back to: {dest}")
    elif output == "slides":
        slides_path = _query_slides(question)
        click.echo(f"\nSlides saved: {slides_path}")


if __name__ == "__main__":
    query()
