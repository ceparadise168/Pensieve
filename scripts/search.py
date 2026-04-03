"""
Local search engine for the wiki.
Supports both keyword search and semantic (embedding-based) search.
Caches indexes to disk/memory for performance.

Usage:
    python scripts/search.py "query terms"
    python scripts/search.py --semantic "natural question"
    python scripts/search.py --rebuild-index
    python scripts/search.py --serve
"""
import json
import os
import re
import click
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
import urllib.parse

from utils.llm_client import embed_text

PROJECT_ROOT = Path(__file__).parent.parent
WIKI_DIR = PROJECT_ROOT / "wiki"
KEYWORD_INDEX_CACHE = PROJECT_ROOT / ".keyword_index.json"
EMBED_INDEX_CACHE = PROJECT_ROOT / ".embed_index.json"

# In-memory caches (persist across web server requests)
_keyword_index_cache = None
_embed_index_cache = None


# ── Keyword Search ──

def build_keyword_index() -> dict:
    """Build inverted index from all wiki files."""
    index = {}
    for md_file in WIKI_DIR.rglob("*.md"):
        rel = str(md_file.relative_to(PROJECT_ROOT))
        content = md_file.read_text(encoding="utf-8")
        for i, line in enumerate(content.split("\n"), 1):
            words = re.findall(r'\w+', line.lower())
            for word in set(words):
                if len(word) < 2:
                    continue
                if word not in index:
                    index[word] = []
                index[word].append({
                    "file": rel,
                    "line": i,
                    "context": line.strip()[:120],
                })
    return index


def _get_keyword_index() -> dict:
    """Get keyword index from memory cache, disk cache, or build fresh."""
    global _keyword_index_cache
    if _keyword_index_cache is not None:
        return _keyword_index_cache

    if KEYWORD_INDEX_CACHE.exists():
        try:
            _keyword_index_cache = json.loads(KEYWORD_INDEX_CACHE.read_text())
            return _keyword_index_cache
        except (json.JSONDecodeError, OSError):
            pass

    _keyword_index_cache = build_keyword_index()
    _save_keyword_index(_keyword_index_cache)
    return _keyword_index_cache


def _save_keyword_index(index: dict):
    """Persist keyword index to disk."""
    try:
        KEYWORD_INDEX_CACHE.write_text(json.dumps(index))
    except OSError:
        pass


def keyword_search(query: str, top_k: int = 20) -> list[dict]:
    words = re.findall(r'\w+', query.lower())
    index = _get_keyword_index()
    file_scores = {}
    file_matches = {}
    for word in words:
        for hit in index.get(word, []):
            f = hit["file"]
            file_scores[f] = file_scores.get(f, 0) + 1
            if f not in file_matches:
                file_matches[f] = []
            file_matches[f].append(hit)
    ranked = sorted(file_scores.items(), key=lambda x: -x[1])[:top_k]
    results = []
    for fpath, score in ranked:
        matches = file_matches[fpath][:3]
        results.append({
            "file": fpath,
            "score": score,
            "matches": matches,
        })
    return results


# ── Semantic Search ──

def build_embed_index() -> dict:
    """Pre-compute embeddings for all wiki files."""
    index = {}
    for md_file in WIKI_DIR.rglob("*.md"):
        rel = str(md_file.relative_to(PROJECT_ROOT))
        content = md_file.read_text(encoding="utf-8")
        try:
            vec = embed_text(content[:1000])
            index[rel] = {
                "vector": vec,
                "preview": content[:200].replace("\n", " "),
            }
            click.echo(f"  Embedded: {rel}")
        except Exception as e:
            click.echo(f"  ERROR embedding {rel}: {e}", err=True)
    return index


def _get_embed_index() -> dict:
    """Get embedding index from memory cache, disk cache, or build fresh."""
    global _embed_index_cache
    if _embed_index_cache is not None:
        return _embed_index_cache

    if EMBED_INDEX_CACHE.exists():
        try:
            _embed_index_cache = json.loads(EMBED_INDEX_CACHE.read_text())
            return _embed_index_cache
        except (json.JSONDecodeError, OSError):
            pass

    click.echo("Building embedding index (first time or after --rebuild-index)...")
    _embed_index_cache = build_embed_index()
    _save_embed_index(_embed_index_cache)
    return _embed_index_cache


def _save_embed_index(index: dict):
    """Persist embedding index to disk."""
    try:
        EMBED_INDEX_CACHE.write_text(json.dumps(index))
    except OSError:
        pass


def semantic_search(query: str, top_k: int = 10) -> list[dict]:
    import numpy as np
    query_vec = np.array(embed_text(query))
    index = _get_embed_index()

    results = []
    for rel, entry in index.items():
        doc_vec = np.array(entry["vector"])
        similarity = float(np.dot(query_vec, doc_vec) / (
            np.linalg.norm(query_vec) * np.linalg.norm(doc_vec) + 1e-8
        ))
        results.append({
            "file": rel,
            "score": similarity,
            "preview": entry.get("preview", ""),
        })
    results.sort(key=lambda x: -x["score"])
    return results[:top_k]


def rebuild_all_indexes():
    """Rebuild both keyword and embedding indexes from scratch."""
    global _keyword_index_cache, _embed_index_cache

    click.echo("Rebuilding keyword index...")
    _keyword_index_cache = build_keyword_index()
    _save_keyword_index(_keyword_index_cache)
    click.echo(f"  Indexed {len(_keyword_index_cache)} terms")

    click.echo("Rebuilding embedding index...")
    _embed_index_cache = build_embed_index()
    _save_embed_index(_embed_index_cache)
    click.echo(f"  Embedded {len(_embed_index_cache)} files")


# ── CLI ──

@click.command()
@click.argument("query", required=False)
@click.option("--semantic", is_flag=True, help="Use embedding-based semantic search")
@click.option("--serve", is_flag=True, help="Start web UI server")
@click.option("--port", default=8080, help="Web UI port")
@click.option("--json-out", is_flag=True, help="Output as JSON")
@click.option("--rebuild-index", is_flag=True, help="Rebuild all search indexes")
def search(query: str, semantic: bool, serve: bool, port: int, json_out: bool, rebuild_index: bool):
    """Search the knowledge base wiki."""
    if rebuild_index:
        rebuild_all_indexes()
        click.echo("Index rebuild complete.")
        return

    if serve:
        click.echo(f"Starting search server on http://localhost:{port}")
        _start_server(port)
        return
    if not query:
        click.echo("Usage: python scripts/search.py 'query'")
        return
    if semantic:
        results = semantic_search(query)
    else:
        results = keyword_search(query)
    if json_out:
        click.echo(json.dumps(results, indent=2))
    else:
        click.echo(f"Results for: '{query}' ({'semantic' if semantic else 'keyword'})\n")
        for i, r in enumerate(results, 1):
            click.echo(f"  {i}. [{r['score']:.2f}] {r['file']}")
            if "matches" in r:
                for m in r["matches"]:
                    click.echo(f"     L{m['line']}: {m['context']}")
            elif "preview" in r:
                click.echo(f"     {r['preview'][:100]}...")
            click.echo()


# ── Web Server ──

def _start_server(port: int):
    class SearchHandler(SimpleHTTPRequestHandler):
        def do_GET(self):
            parsed = urllib.parse.urlparse(self.path)
            if parsed.path == "/api/search":
                params = urllib.parse.parse_qs(parsed.query)
                q = params.get("q", [""])[0]
                mode = params.get("mode", ["keyword"])[0]
                if mode == "semantic":
                    results = semantic_search(q)
                else:
                    results = keyword_search(q)
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps(results).encode())
            elif parsed.path == "/" or parsed.path == "/index.html":
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(_search_html().encode())
            else:
                self.send_response(404)
                self.end_headers()

        def log_message(self, format, *args):
            pass

    server = HTTPServer(("127.0.0.1", port), SearchHandler)
    server.serve_forever()


def _search_html() -> str:
    return """<!DOCTYPE html>
<html><head><title>KB Search</title>
<style>
  body { font-family: system-ui; max-width: 800px; margin: 40px auto; padding: 0 20px; }
  input { width: 100%; padding: 12px; font-size: 16px; border: 2px solid #ddd; border-radius: 8px; }
  .result { margin: 16px 0; padding: 12px; border-left: 3px solid #4a9eff; background: #f8f9fa; }
  .score { color: #888; font-size: 0.9em; }
  .match { color: #555; font-size: 0.9em; margin-top: 4px; }
</style></head><body>
<h1>Knowledge Base Search</h1>
<input type="text" id="q" placeholder="Search..." autofocus>
<div id="results"></div>
<script>
function esc(s) {
  const d = document.createElement('div');
  d.textContent = s;
  return d.innerHTML;
}
let timer;
document.getElementById('q').addEventListener('input', (e) => {
  clearTimeout(timer);
  timer = setTimeout(() => {
    fetch('/api/search?q=' + encodeURIComponent(e.target.value))
      .then(r => r.json())
      .then(data => {
        document.getElementById('results').innerHTML = data.map(r =>
          `<div class="result"><b>${esc(r.file)}</b> <span class="score">(${esc(String(r.score))})</span>` +
          (r.matches ? r.matches.map(m => `<div class="match">L${esc(String(m.line))}: ${esc(m.context)}</div>`).join('') : '') +
          '</div>'
        ).join('');
      });
  }, 300);
});
</script></body></html>"""


if __name__ == "__main__":
    search()
