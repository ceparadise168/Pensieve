# LLM Knowledge Base — 完整專案藍圖

> A self-maintaining, LLM-compiled personal knowledge base system.
> Inspired by [Andrej Karpathy's LLM Knowledge Bases workflow](https://x.com/karpathy).
> 本文件的設計目標：讓 Claude Code、Cursor、Aider 等 AI agent 能夠**完整理解並自主實現**整套系統。

---

## 0. 設計哲學 Design Philosophy

### 0.1 核心轉變：從「人寫筆記」到「LLM 編譯知識」

傳統的知識管理（PKM）流程是：人類閱讀 → 人類摘要 → 人類整理 → 人類查詢。
本系統的根本轉變在於：**人類只負責決定「研究什麼」和「問什麼問題」，LLM 負責閱讀、整理、結構化、維護、查詢的全部工作。**

```
傳統 PKM:  Human → Read → Summarize → Organize → Query → Answer
本系統:    Human → Curate Sources → LLM Compiles → LLM Queries → Human Reviews
```

### 0.2 三大設計原則

**Principle 1: Markdown as Universal Interface**
所有知識以 `.md` + 本地圖片儲存。Markdown 是 LLM 最容易讀寫的格式，也是人類最容易閱讀的純文字格式。不依賴任何專有資料庫。

**Principle 2: LLM-First, Human-View**
Wiki 的所有內容由 LLM 撰寫和維護，人類透過 Obsidian 瀏覽和閱讀。人類幾乎不直接編輯 wiki 檔案。

**Principle 3: Feedback Loop（自我增強迴圈）**
每次查詢的結果都可以回填到 wiki 中，使知識庫隨著使用而持續增長和改善。

### 0.3 系統架構總覽

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER (Human)                             │
│  Decides: what to research, what to ask, what to curate        │
└────────┬──────────────────────────┬─────────────────────────────┘
         │ curate sources           │ ask questions / review
         ▼                          ▼
┌─────────────────┐    ┌──────────────────────────────────────────┐
│   Data Ingest   │    │            Obsidian IDE                  │
│   (raw/)        │    │  View: wiki, visualizations, slides      │
│                 │    │  Plugins: Marp, Dataview, Graph          │
│  Web Clipper    │    └──────────────────────────────────────────┘
│  Manual files   │                     ▲
│  Git repos      │                     │ render .md / .marp / .png
└────────┬────────┘                     │
         │                    ┌─────────┴──────────┐
         ▼                    │     Output Layer    │
┌─────────────────┐           │  .md articles       │
│  LLM Compiler   │──────────▶│  .marp slides       │
│                 │           │  .png charts         │
│  Summarize      │           │  search index        │
│  Categorize     │◀──────────┤                      │
│  Link           │  feedback │  (filed back into    │
│  Index          │  loop     │   wiki)              │
└────────┬────────┘           └────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│                      LLM Backend                                │
│                                                                 │
│  ┌──────────┐    ┌──────────────┐    ┌───────────────────┐     │
│  │  Ollama   │◀──│  LiteLLM     │◀───│  Agent Scripts    │     │
│  │  (local)  │   │  Router      │    │  (Python/Node)    │     │
│  └──────────┘    │              │    └───────────────────┘     │
│                  │  ┌────────┐  │                               │
│  ┌──────────┐    │  │fallback│  │                               │
│  │Claude API│◀───│  └────────┘  │                               │
│  │OpenAI API│    └──────────────┘                               │
│  └──────────┘                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 1. 專案目錄結構 Project Structure

```
knowledge-base/
├── CLAUDE.md                  # Agent instructions (本文件的精簡版)
├── config/
│   ├── litellm_config.yaml    # LLM router configuration
│   ├── models.yaml            # Model preferences per task type
│   └── env.example            # Environment variable template
├── raw/                       # 原始資料（人類策展，LLM 不修改）
│   ├── articles/              # Web articles (.md via Clipper)
│   ├── papers/                # Academic papers (.pdf → .md)
│   ├── repos/                 # Cloned repositories (partial)
│   ├── datasets/              # Data files (.csv, .json)
│   └── images/                # Downloaded images referenced by articles
├── wiki/                      # LLM 編譯產出（LLM 完全擁有，人類唯讀）
│   ├── _index.md              # Master index of all articles
│   ├── _glossary.md           # Term definitions
│   ├── _graph.md              # Concept relationship map
│   ├── concepts/              # Concept articles (one .md per concept)
│   ├── summaries/             # Source document summaries
│   ├── connections/           # Cross-cutting theme articles
│   └── images/                # LLM-generated diagrams
├── output/                    # Query outputs (可回填至 wiki)
│   ├── reports/               # Long-form analysis outputs
│   ├── slides/                # Marp slide decks
│   └── charts/                # matplotlib / mermaid outputs
├── scripts/                   # Automation scripts
│   ├── ingest.py              # Data ingestion pipeline
│   ├── compile.py             # Wiki compilation orchestrator
│   ├── query.py               # Q&A interface
│   ├── lint.py                # Wiki health checker
│   ├── search.py              # Local search engine
│   └── utils/
│       ├── llm_client.py      # Unified LLM API client (via LiteLLM)
│       ├── markdown_utils.py  # Markdown parsing helpers
│       └── obsidian_sync.py   # Obsidian CLI integration
├── tools/                     # CLI tools
│   ├── kb                     # Main CLI entry point (shell wrapper)
│   ├── kb-ingest              # Ingest new source
│   ├── kb-compile             # Run compilation
│   ├── kb-query               # Ask a question
│   ├── kb-lint                # Run health checks
│   └── kb-search              # Search the wiki
├── tests/                     # Test suite
│   ├── test_ingest.py
│   ├── test_compile.py
│   └── test_llm_client.py
├── .obsidian/                 # Obsidian vault config (tracked in git)
│   └── plugins/
├── pyproject.toml             # Python project config
├── package.json               # Node.js dependencies (Marp, etc.)
└── Makefile                   # Common commands shortcut
```

### 1.1 目錄所有權規則 Ownership Rules

| Directory | Owner | Rule |
|-----------|-------|------|
| `raw/` | Human + Ingest Script | LLM 不得修改；只新增（透過 ingest script） |
| `wiki/` | LLM only | 人類不應直接編輯；所有修改透過 compile/lint scripts |
| `output/` | LLM only | 查詢結果暫存區；優質結果可被回填至 wiki |
| `scripts/` | Human + Agent | 程式碼由人類或 AI agent 共同維護 |
| `config/` | Human | 配置由人類管理 |

---

## 2. 環境搭建 Environment Setup

### 2.1 系統需求 Prerequisites

- macOS 14+ (Sonoma or later), Apple Silicon recommended
- Homebrew installed
- Python 3.11+
- Node.js 18+
- Git

### 2.2 一鍵安裝腳本 Bootstrap Script

建立 `scripts/bootstrap.sh`：

```bash
#!/usr/bin/env bash
set -euo pipefail

echo "=== LLM Knowledge Base Bootstrap ==="

# ── 1. System tools ──
echo "[1/6] Installing system dependencies..."
brew install ollama marp-cli jq ripgrep pandoc

# ── 2. Python environment ──
echo "[2/6] Setting up Python environment..."
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install litellm[proxy] \
            openai \
            anthropic \
            click \
            rich \
            pyyaml \
            python-frontmatter \
            beautifulsoup4 \
            markdownify \
            matplotlib \
            requests \
            pytest

# ── 3. Node.js dependencies ──
echo "[3/6] Installing Node.js dependencies..."
npm init -y 2>/dev/null || true
npm install --save-dev @marp-team/marp-cli

# ── 4. Ollama models ──
echo "[4/6] Pulling Ollama models..."
ollama pull qwen2.5:14b        # Primary: good balance of speed and quality
ollama pull nomic-embed-text    # Embedding model for search
ollama pull llama3.2:3b         # Fast model for simple tasks (summarize, tag)

# ── 5. Directory structure ──
echo "[5/6] Creating directory structure..."
mkdir -p raw/{articles,papers,repos,datasets,images}
mkdir -p wiki/{concepts,summaries,connections,images}
mkdir -p output/{reports,slides,charts}
mkdir -p scripts/utils
mkdir -p tools
mkdir -p config
mkdir -p tests

# ── 6. Config files ──
echo "[6/6] Generating config files..."
if [ ! -f config/litellm_config.yaml ]; then
  cat > config/litellm_config.yaml << 'YAML'
model_list:
  # ── Local models (Ollama) ──
  - model_name: "local-main"
    litellm_params:
      model: "ollama/qwen2.5:14b"
      api_base: "http://localhost:11434"
      timeout: 120
      stream: true

  - model_name: "local-fast"
    litellm_params:
      model: "ollama/llama3.2:3b"
      api_base: "http://localhost:11434"
      timeout: 60
      stream: true

  - model_name: "local-embed"
    litellm_params:
      model: "ollama/nomic-embed-text"
      api_base: "http://localhost:11434"

  # ── Cloud fallback (uncomment and set API keys) ──
  # - model_name: "cloud-main"
  #   litellm_params:
  #     model: "anthropic/claude-sonnet-4-20250514"
  #     api_key: "os.environ/ANTHROPIC_API_KEY"
  #     timeout: 120

  # - model_name: "cloud-heavy"
  #   litellm_params:
  #     model: "anthropic/claude-opus-4-20250514"
  #     api_key: "os.environ/ANTHROPIC_API_KEY"
  #     timeout: 300

router_settings:
  routing_strategy: "simple-shuffle"
  num_retries: 2
  timeout: 120
  allowed_fails: 3
  cooldown_time: 60

general_settings:
  master_key: "sk-kb-local-dev"
YAML
fi

if [ ! -f config/models.yaml ]; then
  cat > config/models.yaml << 'YAML'
# Task → Model mapping
# Agent scripts use this to select the right model per task type
task_models:
  summarize: "local-fast"         # Fast, simple extraction
  compile_article: "local-main"   # Needs reasoning + writing quality
  compile_index: "local-main"     # Structural understanding
  query_simple: "local-main"      # Single-hop Q&A
  query_complex: "cloud-main"     # Multi-hop reasoning, fallback to cloud
  lint: "local-main"              # Consistency checking
  generate_slides: "local-main"   # Markdown generation
  generate_chart: "local-fast"    # Code generation (matplotlib)
  embed: "local-embed"            # Vector embeddings for search
YAML
fi

if [ ! -f config/env.example ]; then
  cat > config/env.example << 'ENV'
# Copy to .env and fill in values
# Only needed if using cloud LLM fallback

# ANTHROPIC_API_KEY=sk-ant-...
# OPENAI_API_KEY=sk-...

# Obsidian vault path (auto-detected if running inside vault)
OBSIDIAN_VAULT_PATH="."

# LiteLLM proxy (if running as separate service)
LITELLM_PROXY_URL="http://localhost:4000"

# Search engine port
SEARCH_PORT=8080
ENV
fi

# ── Create CLAUDE.md ──
if [ ! -f CLAUDE.md ]; then
  cat > CLAUDE.md << 'CLAUDEMD'
# LLM Knowledge Base — Agent Instructions

## What is this project?
A personal knowledge base where raw sources are compiled by LLMs into a structured wiki.
Human curates sources into `raw/`. LLM compiles `wiki/`. Human reads in Obsidian.

## Key rules
- NEVER modify files in `raw/` (except via ingest script adding new files)
- `wiki/` is LLM-owned: all edits go through `scripts/compile.py`
- Always update `wiki/_index.md` when adding/removing wiki articles
- Maintain backlinks: if article A references B, B should link back to A
- Use relative links: `[Concept X](../concepts/concept-x.md)`
- Images go in `wiki/images/` with descriptive names

## Available CLI tools
- `./tools/kb ingest <url|file>` — Add new source to raw/
- `./tools/kb compile [--full|--incremental]` — Compile wiki from raw sources
- `./tools/kb query "question"` — Ask a question against the wiki
- `./tools/kb lint` — Run health checks on the wiki
- `./tools/kb search "term"` — Search the wiki

## LLM backend
- Primary: Ollama (local) via LiteLLM router
- Fallback: Cloud APIs (Claude/OpenAI) for complex tasks
- Config: `config/litellm_config.yaml` and `config/models.yaml`

## Wiki article format
Every wiki article must follow this template:
```markdown
---
title: "Article Title"
aliases: ["alias1", "alias2"]
sources: ["raw/articles/source.md"]
created: "YYYY-MM-DD"
updated: "YYYY-MM-DD"
tags: [tag1, tag2]
status: draft | review | published
---

# Article Title

Brief summary paragraph.

## Content sections...

## Related
- [[concept-a]]
- [[concept-b]]

## Sources
- [Source Title](../raw/articles/source.md)
```
CLAUDEMD
fi

echo ""
echo "=== Bootstrap complete ==="
echo "Next steps:"
echo "  1. Start Ollama:          ollama serve"
echo "  2. (Optional) Start LiteLLM proxy: litellm --config config/litellm_config.yaml"
echo "  3. Open Obsidian and set this directory as vault"
echo "  4. Enable Obsidian CLI:   Settings → General → Command line interface"
echo "  5. Ingest your first source: ./tools/kb ingest <url>"
```

### 2.3 Ollama 模型選擇指引 Model Selection Guide

| Task Type | Recommended Model | VRAM | Reasoning |
|-----------|------------------|------|-----------|
| Summarization | `llama3.2:3b` | ~2GB | 簡單提取任務，速度優先 |
| Article writing | `qwen2.5:14b` | ~9GB | 需要推理和寫作品質 |
| Complex Q&A | `qwen2.5:32b` 或 cloud API | ~20GB | 多跳推理，32B 需要 32GB+ RAM |
| Embeddings | `nomic-embed-text` | ~0.3GB | 搜尋用向量嵌入 |
| Code generation | `qwen2.5-coder:14b` | ~9GB | 腳本生成和圖表繪製 |

Apple Silicon 記憶體建議：16GB → 用 3b+14b, 32GB → 可跑 32b, 64GB+ → 全部本地化。

### 2.4 LiteLLM Router 啟動與驗證

```bash
# Start Ollama in background
ollama serve &

# Start LiteLLM proxy
source .venv/bin/activate
litellm --config config/litellm_config.yaml --port 4000 &

# Verify: list available models
curl http://localhost:4000/v1/models | jq '.data[].id'

# Test a completion
curl http://localhost:4000/v1/chat/completions \
  -H "Authorization: Bearer sk-kb-local-dev" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "local-main",
    "messages": [{"role": "user", "content": "Hello, respond in one word."}]
  }'
```

---

## 3. 核心模組實作 Core Modules

### 3.1 統一 LLM 客戶端 `scripts/utils/llm_client.py`

此模組是所有 LLM 互動的唯一入口，封裝 LiteLLM 調用並根據任務類型自動選擇模型。

```python
"""
Unified LLM client for the Knowledge Base.
Routes requests through LiteLLM based on task type.
"""
import os
import yaml
from pathlib import Path
from litellm import completion, embedding

# Load task → model mapping
CONFIG_DIR = Path(__file__).parent.parent.parent / "config"

def _load_model_config() -> dict:
    with open(CONFIG_DIR / "models.yaml") as f:
        return yaml.safe_load(f)

_config = _load_model_config()

def get_model_for_task(task: str) -> str:
    """Resolve model name for a given task type."""
    return _config["task_models"].get(task, "local-main")

def ask(
    prompt: str,
    task: str = "query_simple",
    system: str = "",
    temperature: float = 0.3,
    max_tokens: int = 4096,
) -> str:
    """
    Send a prompt to the appropriate LLM based on task type.

    Args:
        prompt: User/task prompt
        task: Task type key from config/models.yaml
        system: System prompt (optional)
        temperature: Sampling temperature
        max_tokens: Max output tokens

    Returns:
        LLM response text
    """
    model = get_model_for_task(task)
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    proxy_url = os.getenv("LITELLM_PROXY_URL", "http://localhost:4000")

    response = completion(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        api_base=proxy_url,
        api_key=os.getenv("LITELLM_API_KEY", "sk-kb-local-dev"),
    )
    return response.choices[0].message.content

def embed_text(text: str) -> list[float]:
    """Generate embedding vector for text using the embedding model."""
    model = get_model_for_task("embed")
    proxy_url = os.getenv("LITELLM_PROXY_URL", "http://localhost:4000")

    response = embedding(
        model=model,
        input=[text],
        api_base=proxy_url,
        api_key=os.getenv("LITELLM_API_KEY", "sk-kb-local-dev"),
    )
    return response.data[0]["embedding"]

def ask_with_context(
    question: str,
    context_files: list[str],
    task: str = "query_complex",
) -> str:
    """
    Ask a question with wiki files as context.

    Args:
        question: The question to answer
        context_files: List of file paths to include as context
        task: Task type for model selection
    """
    context_parts = []
    for fpath in context_files:
        p = Path(fpath)
        if p.exists():
            content = p.read_text(encoding="utf-8")
            context_parts.append(f"--- {p.name} ---\n{content}\n")

    full_context = "\n".join(context_parts)

    system = (
        "You are a research assistant with access to a curated knowledge base. "
        "Answer the question based on the provided context documents. "
        "Cite specific documents when referencing information. "
        "If the context doesn't contain enough information, say so clearly."
    )

    prompt = f"""## Context Documents

{full_context}

## Question

{question}

## Instructions
- Answer based on the context above
- Cite document names when referencing specific information
- If multiple documents disagree, note the discrepancy
- If context is insufficient, state what's missing
"""
    return ask(prompt, task=task, system=system, max_tokens=8192)
```

### 3.2 資料攝入模組 `scripts/ingest.py`

```python
"""
Data Ingest Pipeline.
Converts various source formats into normalized .md files in raw/.

Usage:
    python scripts/ingest.py url "https://example.com/article"
    python scripts/ingest.py file "/path/to/paper.pdf"
    python scripts/ingest.py repo "https://github.com/user/repo"
"""
import click
import json
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

from utils.llm_client import ask
from utils.markdown_utils import html_to_markdown, pdf_to_markdown

RAW_DIR = Path(__file__).parent.parent / "raw"

def _slug(text: str) -> str:
    """Convert text to a URL-friendly slug."""
    import re
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    return text[:80]

def _download_images(html_content: str, article_slug: str) -> str:
    """
    Download all images referenced in HTML to raw/images/{slug}/
    and rewrite image URLs to local paths.
    """
    import re
    import requests

    img_dir = RAW_DIR / "images" / article_slug
    img_dir.mkdir(parents=True, exist_ok=True)

    img_pattern = r'!\[([^\]]*)\]\((https?://[^)]+)\)'
    found = re.findall(img_pattern, html_content)

    for i, (alt, url) in enumerate(found):
        try:
            ext = Path(urlparse(url).path).suffix or ".png"
            local_name = f"img-{i:03d}{ext}"
            local_path = img_dir / local_name

            resp = requests.get(url, timeout=15)
            resp.raise_for_status()
            local_path.write_bytes(resp.content)

            rel_path = f"../images/{article_slug}/{local_name}"
            html_content = html_content.replace(url, rel_path)
        except Exception as e:
            print(f"  Warning: failed to download image {url}: {e}")

    return html_content

def _generate_frontmatter(content: str, source_type: str, source_url: str = "") -> str:
    """Use LLM to generate frontmatter metadata for the ingested content."""
    prompt = f"""Analyze this document and generate YAML frontmatter.
Return ONLY the YAML block, no explanation.

Required fields:
- title: descriptive title
- tags: list of 3-7 relevant tags
- summary: one-sentence summary (under 200 chars)
- source_type: "{source_type}"
- source_url: "{source_url}"
- ingested: "{datetime.now().strftime('%Y-%m-%d')}"

Document (first 2000 chars):
{content[:2000]}
"""
    return ask(prompt, task="summarize", temperature=0.1)

@click.group()
def cli():
    """Knowledge Base Ingest Tool."""
    pass

@cli.command()
@click.argument("url")
def url(url: str):
    """Ingest a web article by URL."""
    import requests
    from bs4 import BeautifulSoup

    click.echo(f"Fetching: {url}")
    resp = requests.get(url, timeout=30, headers={"User-Agent": "KB-Ingest/1.0"})
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    title = soup.title.string if soup.title else urlparse(url).path
    slug = _slug(title)

    # Convert HTML → Markdown
    md_content = html_to_markdown(resp.text)

    # Download images locally
    md_content = _download_images(md_content, slug)

    # Generate frontmatter
    frontmatter = _generate_frontmatter(md_content, "web_article", url)

    # Write to raw/articles/
    outpath = RAW_DIR / "articles" / f"{slug}.md"
    outpath.parent.mkdir(parents=True, exist_ok=True)
    outpath.write_text(f"---\n{frontmatter}\n---\n\n{md_content}", encoding="utf-8")

    click.echo(f"Ingested: {outpath}")

@cli.command()
@click.argument("filepath", type=click.Path(exists=True))
def file(filepath: str):
    """Ingest a local file (PDF, .md, .txt, .html)."""
    src = Path(filepath)
    suffix = src.suffix.lower()

    if suffix == ".pdf":
        md_content = pdf_to_markdown(src)
        dest_dir = RAW_DIR / "papers"
    elif suffix in (".md", ".txt"):
        md_content = src.read_text(encoding="utf-8")
        dest_dir = RAW_DIR / "articles"
    elif suffix == ".html":
        md_content = html_to_markdown(src.read_text(encoding="utf-8"))
        dest_dir = RAW_DIR / "articles"
    else:
        # Copy as-is to datasets
        dest_dir = RAW_DIR / "datasets"
        dest_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest_dir / src.name)
        click.echo(f"Copied to: {dest_dir / src.name}")
        return

    slug = _slug(src.stem)
    frontmatter = _generate_frontmatter(md_content, "local_file", str(src))

    outpath = dest_dir / f"{slug}.md"
    outpath.parent.mkdir(parents=True, exist_ok=True)
    outpath.write_text(f"---\n{frontmatter}\n---\n\n{md_content}", encoding="utf-8")

    click.echo(f"Ingested: {outpath}")

@cli.command()
@click.argument("repo_url")
@click.option("--depth", default=1, help="Git clone depth")
def repo(repo_url: str, depth: int):
    """Ingest a Git repository (shallow clone + README/docs extraction)."""
    repo_name = urlparse(repo_url).path.strip("/").split("/")[-1].replace(".git", "")
    clone_dir = RAW_DIR / "repos" / repo_name

    if clone_dir.exists():
        click.echo(f"Repo already exists: {clone_dir}, pulling latest...")
        subprocess.run(["git", "-C", str(clone_dir), "pull"], check=True)
    else:
        click.echo(f"Cloning: {repo_url}")
        subprocess.run(
            ["git", "clone", "--depth", str(depth), repo_url, str(clone_dir)],
            check=True,
        )

    # Extract key documentation files
    doc_files = list(clone_dir.glob("*.md")) + list(clone_dir.glob("docs/**/*.md"))
    click.echo(f"Found {len(doc_files)} documentation files in repo.")

    # Generate a repo summary
    readme = clone_dir / "README.md"
    if readme.exists():
        content = readme.read_text(encoding="utf-8")[:5000]
        summary = ask(
            f"Summarize this repository based on its README:\n\n{content}",
            task="summarize",
        )
        summary_path = RAW_DIR / "repos" / f"{repo_name}-summary.md"
        summary_path.write_text(
            f"---\ntitle: '{repo_name} Repository Summary'\n"
            f"source_type: repository\n"
            f"source_url: '{repo_url}'\n"
            f"ingested: '{datetime.now().strftime('%Y-%m-%d')}'\n---\n\n{summary}",
            encoding="utf-8",
        )
        click.echo(f"Summary: {summary_path}")

if __name__ == "__main__":
    cli()
```

### 3.3 Wiki 編譯器 `scripts/compile.py`

這是系統的核心——LLM 將 raw/ 中的原始資料「編譯」成結構化的 wiki。

```python
"""
Wiki Compiler — the heart of the knowledge base.
Reads raw/ sources and compiles/updates wiki/ articles.

Usage:
    python scripts/compile.py --full        # Full recompilation
    python scripts/compile.py --incremental # Only process new/changed sources
    python scripts/compile.py --article "concept-name"  # Recompile specific article
"""
import click
import json
import hashlib
from datetime import datetime
from pathlib import Path

import frontmatter

from utils.llm_client import ask, ask_with_context

PROJECT_ROOT = Path(__file__).parent.parent
RAW_DIR = PROJECT_ROOT / "raw"
WIKI_DIR = PROJECT_ROOT / "wiki"
STATE_FILE = PROJECT_ROOT / ".compile_state.json"

# ── State Management ──

def _load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"file_hashes": {}, "last_compile": None}

def _save_state(state: dict):
    state["last_compile"] = datetime.now().isoformat()
    STATE_FILE.write_text(json.dumps(state, indent=2))

def _file_hash(path: Path) -> str:
    return hashlib.md5(path.read_bytes()).hexdigest()

def _get_changed_files(state: dict) -> list[Path]:
    """Find raw files that are new or changed since last compile."""
    changed = []
    for md_file in RAW_DIR.rglob("*.md"):
        h = _file_hash(md_file)
        rel = str(md_file.relative_to(PROJECT_ROOT))
        if state["file_hashes"].get(rel) != h:
            changed.append(md_file)
            state["file_hashes"][rel] = h
    return changed

# ── Compilation Steps ──

def step_1_summarize_sources(sources: list[Path]) -> list[dict]:
    """Generate summaries for each raw source file."""
    summaries = []
    for src in sources:
        content = src.read_text(encoding="utf-8")
        rel_path = str(src.relative_to(PROJECT_ROOT))

        summary = ask(
            f"Summarize the following document in 3-5 paragraphs. "
            f"Focus on key concepts, findings, and actionable insights.\n\n"
            f"Document: {src.name}\n\n{content[:12000]}",
            task="summarize",
        )

        # Write summary to wiki/summaries/
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

    return summaries

def step_2_extract_concepts(summaries: list[dict]) -> list[str]:
    """Identify key concepts across all summaries."""
    all_summaries = "\n\n".join(
        f"[{s['source']}]: {s['summary']}" for s in summaries
    )

    # Also read existing concepts for continuity
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

    # Parse JSON (handle potential markdown fences)
    response = response.strip()
    if response.startswith("```"):
        response = response.split("\n", 1)[1].rsplit("```", 1)[0]

    try:
        concepts = json.loads(response)
    except json.JSONDecodeError:
        click.echo("  Warning: Failed to parse concepts JSON, retrying...")
        concepts = json.loads(ask(
            f"Fix this JSON and return ONLY valid JSON:\n{response}",
            task="summarize",
            temperature=0.0,
        ))

    return concepts

def step_3_write_concept_articles(concepts: list[dict]):
    """Write or update a wiki article for each concept."""
    for concept in concepts:
        slug = concept["slug"]
        article_path = WIKI_DIR / "concepts" / f"{slug}.md"

        # Gather source content for context
        source_contents = []
        for src_rel in concept.get("related_sources", []):
            src_path = PROJECT_ROOT / src_rel
            if src_path.exists():
                source_contents.append(src_path.read_text(encoding="utf-8")[:8000])

        context = "\n\n---\n\n".join(source_contents)

        # Check if article already exists (for incremental update)
        existing_content = ""
        if article_path.exists():
            existing_content = article_path.read_text(encoding="utf-8")

        if existing_content:
            prompt = f"""Update the following wiki article with new information from the sources below.
Preserve existing accurate content. Add new insights. Fix any inconsistencies.

EXISTING ARTICLE:
{existing_content}

NEW SOURCE MATERIAL:
{context}

Return the COMPLETE updated article in markdown with YAML frontmatter."""
        else:
            prompt = f"""Write a comprehensive wiki article about: {concept['title']}

Description: {concept['description']}

Use the following source material:
{context}

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

def step_4_build_index():
    """Rebuild the master index file."""
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

    # Generate index content
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

    # Group by tag
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

def step_5_build_graph():
    """Build a concept relationship map by analyzing cross-references."""
    concepts_dir = WIKI_DIR / "concepts"
    import re

    graph = {}
    for md_file in concepts_dir.glob("*.md"):
        content = md_file.read_text(encoding="utf-8")
        slug = md_file.stem
        # Find all [[wiki-links]]
        links = re.findall(r'\[\[([^\]|]+)', content)
        graph[slug] = links

    # Write graph as markdown
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
    for source, targets in graph.items():
        for target in targets:
            lines.append(f"    {source} --> {target}")
    lines.append("```")
    lines.append("")

    # Also list as text
    lines.append("## Adjacency List")
    lines.append("")
    for source, targets in sorted(graph.items()):
        if targets:
            links_str = ", ".join(f"[[{t}]]" for t in targets)
            lines.append(f"- **{source}** → {links_str}")

    (WIKI_DIR / "_graph.md").write_text("\n".join(lines), encoding="utf-8")
    click.echo(f"  Graph updated: {len(graph)} nodes")

# ── Main CLI ──

@click.command()
@click.option("--full", is_flag=True, help="Full recompilation of all sources")
@click.option("--incremental", is_flag=True, default=True, help="Only process changed sources")
@click.option("--article", type=str, help="Recompile a specific article by slug")
def compile_wiki(full: bool, incremental: bool, article: str):
    """Compile the wiki from raw sources."""
    state = _load_state()

    if article:
        click.echo(f"Recompiling article: {article}")
        # Find related sources and recompile just this article
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

    # Get sources to process
    if full:
        sources = list(RAW_DIR.rglob("*.md"))
        click.echo(f"Full compile: {len(sources)} source files")
    else:
        sources = _get_changed_files(state)
        if not sources:
            click.echo("No changes detected. Use --full to force recompilation.")
            return
        click.echo(f"Incremental compile: {len(sources)} changed files")

    # Pipeline
    click.echo("\n[Step 1/5] Summarizing sources...")
    summaries = step_1_summarize_sources(sources)

    click.echo("\n[Step 2/5] Extracting concepts...")
    concepts = step_2_extract_concepts(summaries)
    click.echo(f"  Found {len(concepts)} concepts")

    click.echo("\n[Step 3/5] Writing concept articles...")
    step_3_write_concept_articles(concepts)

    click.echo("\n[Step 4/5] Building index...")
    step_4_build_index()

    click.echo("\n[Step 5/5] Building concept graph...")
    step_5_build_graph()

    _save_state(state)
    click.echo(f"\nCompilation complete. Wiki: {WIKI_DIR}")

if __name__ == "__main__":
    compile_wiki()
```

### 3.4 查詢引擎 `scripts/query.py`

```python
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
    """Read the master index for context."""
    index_path = WIKI_DIR / "_index.md"
    if index_path.exists():
        return index_path.read_text(encoding="utf-8")
    return ""

def _find_relevant_articles(question: str, top_k: int = 10) -> list[Path]:
    """
    Find the most relevant wiki articles for a question.
    Strategy: LLM reads the index and selects relevant articles.
    """
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
        # Fallback: return all concept files
        slugs = [p.stem for p in (WIKI_DIR / "concepts").glob("*.md")][:top_k]

    paths = []
    for slug in slugs:
        p = WIKI_DIR / "concepts" / f"{slug}.md"
        if p.exists():
            paths.append(p)

    # Also check summaries
    for slug in slugs:
        p = WIKI_DIR / "summaries" / f"{slug}.md"
        if p.exists():
            paths.append(p)

    return paths

def _query_text(question: str) -> str:
    """Answer a question and return markdown text."""
    relevant = _find_relevant_articles(question)
    click.echo(f"  Found {len(relevant)} relevant articles")

    return ask_with_context(
        question=question,
        context_files=[str(p) for p in relevant],
        task="query_complex",
    )

def _query_report(question: str) -> Path:
    """Generate a long-form report and save to output/reports/."""
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
    """Generate a Marp slide deck and save to output/slides/."""
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

    # Also generate HTML via Marp CLI
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
            # Copy to wiki/connections/ for future reference
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
```

### 3.5 Wiki 健康檢查 `scripts/lint.py`

```python
"""
Wiki Linter — health checks and auto-repair for the knowledge base.

Checks:
  1. Broken internal links ([[slug]] pointing to nonexistent articles)
  2. Orphaned articles (no inbound links)
  3. Missing frontmatter fields
  4. Inconsistent data across articles
  5. Stale summaries (source changed since last summary)
  6. Suggested new article candidates

Usage:
    python scripts/lint.py --check          # Report issues only
    python scripts/lint.py --fix            # Auto-fix what we can
    python scripts/lint.py --suggest        # Suggest improvements
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
    """Find [[wiki-links]] that point to nonexistent articles."""
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
    """Find articles with no inbound links."""
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
    """Check for missing or incomplete frontmatter."""
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
    """Use LLM to suggest wiki improvements."""
    # Gather article titles and brief summaries
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
        check = True  # Default to check mode

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

        # Summary
        errors = [i for i in all_issues if i["severity"] == "error"]
        warnings = [i for i in all_issues if i["severity"] == "warning"]
        infos = [i for i in all_issues if i["severity"] == "info"]

        click.echo(f"\nTotal: {len(errors)} errors, {len(warnings)} warnings, {len(infos)} info")

        for issue in all_issues:
            icon = {"error": "✗", "warning": "⚠", "info": "ℹ"}.get(issue["severity"], "?")
            click.echo(f"  {icon} [{issue['type']}] {issue.get('file', '')} — {issue.get('link', issue.get('field', issue.get('error', '')))}")

    if fix:
        click.echo("\nAuto-fixing issues...")
        # Fix broken links by creating stub articles
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
```

### 3.6 搜尋引擎 `scripts/search.py`

```python
"""
Local search engine for the wiki.
Supports both keyword search and semantic (embedding-based) search.

Usage:
    python scripts/search.py "query terms"              # Keyword search
    python scripts/search.py --semantic "natural question"  # Semantic search
    python scripts/search.py --serve                    # Start web UI server
"""
import json
import re
import click
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
import urllib.parse

from utils.llm_client import embed_text

PROJECT_ROOT = Path(__file__).parent.parent
WIKI_DIR = PROJECT_ROOT / "wiki"
INDEX_CACHE = PROJECT_ROOT / ".search_index.json"

def build_keyword_index() -> dict:
    """Build an inverted index of all wiki content."""
    index = {}  # word -> [(file, line_num, context)]

    for md_file in WIKI_DIR.rglob("*.md"):
        rel = str(md_file.relative_to(PROJECT_ROOT))
        content = md_file.read_text(encoding="utf-8")

        for i, line in enumerate(content.split("\n"), 1):
            words = re.findall(r'\w+', line.lower())
            for word in set(words):  # Dedupe per line
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

def keyword_search(query: str, top_k: int = 20) -> list[dict]:
    """Search wiki by keyword matching."""
    words = re.findall(r'\w+', query.lower())
    index = build_keyword_index()

    # Score files by term frequency
    file_scores = {}
    file_matches = {}

    for word in words:
        for hit in index.get(word, []):
            f = hit["file"]
            file_scores[f] = file_scores.get(f, 0) + 1
            if f not in file_matches:
                file_matches[f] = []
            file_matches[f].append(hit)

    # Sort by score
    ranked = sorted(file_scores.items(), key=lambda x: -x[1])[:top_k]

    results = []
    for fpath, score in ranked:
        matches = file_matches[fpath][:3]  # Top 3 matching lines
        results.append({
            "file": fpath,
            "score": score,
            "matches": matches,
        })

    return results

def semantic_search(query: str, top_k: int = 10) -> list[dict]:
    """Search wiki using embedding similarity."""
    import numpy as np

    query_vec = np.array(embed_text(query))

    results = []
    for md_file in WIKI_DIR.rglob("*.md"):
        content = md_file.read_text(encoding="utf-8")
        # Embed first 1000 chars as document representation
        doc_vec = np.array(embed_text(content[:1000]))

        similarity = np.dot(query_vec, doc_vec) / (
            np.linalg.norm(query_vec) * np.linalg.norm(doc_vec) + 1e-8
        )
        results.append({
            "file": str(md_file.relative_to(PROJECT_ROOT)),
            "score": float(similarity),
            "preview": content[:200].replace("\n", " "),
        })

    results.sort(key=lambda x: -x["score"])
    return results[:top_k]

@click.command()
@click.argument("query", required=False)
@click.option("--semantic", is_flag=True, help="Use embedding-based semantic search")
@click.option("--serve", is_flag=True, help="Start web UI server")
@click.option("--port", default=8080, help="Web UI port")
@click.option("--json-out", is_flag=True, help="Output as JSON (for LLM tool use)")
def search(query: str, semantic: bool, serve: bool, port: int, json_out: bool):
    """Search the knowledge base wiki."""
    if serve:
        click.echo(f"Starting search server on http://localhost:{port}")
        # Minimal search web UI — serves a simple HTML page with search input
        # and returns results via /api/search?q=...
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

def _start_server(port: int):
    """Start a minimal search web server."""
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
            pass  # Suppress default logging

    server = HTTPServer(("", port), SearchHandler)
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
let timer;
document.getElementById('q').addEventListener('input', (e) => {
  clearTimeout(timer);
  timer = setTimeout(() => {
    fetch('/api/search?q=' + encodeURIComponent(e.target.value))
      .then(r => r.json())
      .then(data => {
        document.getElementById('results').innerHTML = data.map(r =>
          `<div class="result"><b>${r.file}</b> <span class="score">(${r.score})</span>` +
          (r.matches ? r.matches.map(m => `<div class="match">L${m.line}: ${m.context}</div>`).join('') : '') +
          '</div>'
        ).join('');
      });
  }, 300);
});
</script></body></html>"""

if __name__ == "__main__":
    search()
```

---

## 4. CLI 工具入口 CLI Tool Wrappers

建立 `tools/kb`（主 CLI wrapper）:

```bash
#!/usr/bin/env bash
# tools/kb — Main CLI entry point for the Knowledge Base
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
VENV="$PROJECT_ROOT/.venv"

# Activate virtualenv
if [ -f "$VENV/bin/activate" ]; then
    source "$VENV/bin/activate"
fi

export PYTHONPATH="$PROJECT_ROOT/scripts:$PYTHONPATH"

COMMAND="${1:-help}"
shift || true

case "$COMMAND" in
    ingest)
        python "$PROJECT_ROOT/scripts/ingest.py" "$@"
        ;;
    compile)
        python "$PROJECT_ROOT/scripts/compile.py" "$@"
        ;;
    query)
        python "$PROJECT_ROOT/scripts/query.py" "$@"
        ;;
    lint)
        python "$PROJECT_ROOT/scripts/lint.py" "$@"
        ;;
    search)
        python "$PROJECT_ROOT/scripts/search.py" "$@"
        ;;
    serve)
        python "$PROJECT_ROOT/scripts/search.py" --serve "$@"
        ;;
    status)
        echo "=== Knowledge Base Status ==="
        echo "Raw sources:  $(find "$PROJECT_ROOT/raw" -name '*.md' | wc -l) files"
        echo "Wiki articles: $(find "$PROJECT_ROOT/wiki/concepts" -name '*.md' 2>/dev/null | wc -l) articles"
        echo "Summaries:    $(find "$PROJECT_ROOT/wiki/summaries" -name '*.md' 2>/dev/null | wc -l) summaries"
        echo "Outputs:      $(find "$PROJECT_ROOT/output" -type f 2>/dev/null | wc -l) files"
        if command -v ollama &>/dev/null; then
            echo "Ollama:       $(ollama list 2>/dev/null | tail -n +2 | wc -l) models loaded"
        fi
        ;;
    help|--help|-h)
        echo "Usage: kb <command> [args]"
        echo ""
        echo "Commands:"
        echo "  ingest <url|file|repo>     Add a new source to the knowledge base"
        echo "  compile [--full|--incremental]  Compile wiki from raw sources"
        echo "  query 'question' [--output text|report|slides]  Ask a question"
        echo "  lint [--check|--fix|--suggest]  Run wiki health checks"
        echo "  search 'terms' [--semantic]     Search the wiki"
        echo "  serve [--port 8080]             Start search web UI"
        echo "  status                          Show knowledge base stats"
        ;;
    *)
        echo "Unknown command: $COMMAND"
        echo "Run 'kb help' for usage."
        exit 1
        ;;
esac
```

```bash
# Make executable
chmod +x tools/kb
```

---

## 5. Obsidian 整合 Obsidian Integration

### 5.1 Obsidian CLI 使用

Obsidian 在 v1.12.4+ 提供了官方 CLI。啟用方法：

```
Settings → General → Command line interface → Enable
```

啟用後可在 terminal 中使用：

```bash
# Read a wiki article
obsidian read wiki/concepts/transformer-architecture.md

# Search across vault
obsidian search "attention mechanism" --format json

# Append content to a note (useful for filing back query results)
obsidian append wiki/connections/daily-log.md "## $(date)\n\nNew finding: ..."

# Open a specific note in Obsidian GUI
obsidian open wiki/_index.md
```

### 5.2 建議安裝的 Obsidian Plugins

| Plugin | 用途 | 配置要點 |
|--------|------|----------|
| **Dataview** | 動態查詢 wiki 文章（by tags, status, date） | 啟用 JavaScript queries |
| **Marp Slides** | 在 Obsidian 內預覽 Marp 投影片 | 指向 output/slides/ |
| **Graph Analysis** | 進階概念圖視覺化 | 預設設定即可 |
| **Obsidian Git** | 自動備份 wiki 變更 | 設定 auto-commit interval |
| **Local REST API** | 提供 HTTP API 供外部腳本存取 | 設定 API key, port 27123 |
| **Templater** | 標準化文章模板 | 配置 wiki article template |

### 5.3 Dataview 範例查詢

在 Obsidian 中建立一個 `wiki/_dashboard.md`：

````markdown
# Knowledge Base Dashboard

## Recent Articles
```dataview
TABLE title, status, updated
FROM "wiki/concepts"
SORT updated DESC
LIMIT 20
```

## Draft Articles (need review)
```dataview
LIST
FROM "wiki/concepts"
WHERE status = "draft"
SORT created DESC
```

## Tag Cloud
```dataview
TABLE WITHOUT ID
  length(rows) AS "Count",
  rows.file.link AS "Articles"
FROM "wiki/concepts"
FLATTEN tags AS tag
GROUP BY tag
SORT length(rows) DESC
```

## Stub Articles (need content)
```dataview
LIST
FROM "wiki/concepts"
WHERE status = "stub"
```
````

---

## 6. Agent 自動化工作流程 Agent Workflows

### 6.1 Daily Knowledge Ingestion（每日知識攝入）

以下是一個可由 cron 或 AI agent 定期執行的工作流程：

```bash
#!/usr/bin/env bash
# scripts/daily_workflow.sh — Run daily knowledge maintenance

set -euo pipefail
cd "$(dirname "$0")/.."

echo "=== Daily Knowledge Base Workflow ==="
echo "Date: $(date)"

# Step 1: Compile any new raw sources
echo "[1/4] Compiling new sources..."
./tools/kb compile --incremental

# Step 2: Run lint checks
echo "[2/4] Running health checks..."
./tools/kb lint --check --suggest 2>&1 | tee output/lint-report-$(date +%Y%m%d).txt

# Step 3: Auto-fix trivial issues
echo "[3/4] Auto-fixing issues..."
./tools/kb lint --fix

# Step 4: Rebuild search index
echo "[4/4] Rebuilding search index..."
./tools/kb search --rebuild-index 2>/dev/null || true

echo "=== Daily workflow complete ==="
```

### 6.2 Agent 指令集（供 Claude Code / Cursor 等使用）

在 `CLAUDE.md` 或 `.cursorrules` 中加入以下指令，讓 AI agent 知道如何操作本系統：

```markdown
## Agent Workflow Commands

When the user asks you to work with the knowledge base, use these patterns:

### Adding a new source
1. Run: `./tools/kb ingest url "https://..."` or `./tools/kb ingest file "/path/to/file"`
2. Then: `./tools/kb compile --incremental`
3. Verify: `./tools/kb status`

### Answering a research question
1. First try: `./tools/kb search "keywords" --json-out` to find relevant files
2. Read the relevant files to gather context
3. Synthesize an answer based on the wiki content
4. If the answer is substantial, save it: `./tools/kb query "question" --output report --file-back`

### Improving the wiki
1. Run: `./tools/kb lint --check --suggest`
2. Review suggestions
3. For each suggested new article: identify sources in raw/, then run compile
4. For contradictions: read both articles, determine which is correct, update

### Creating a presentation
1. Run: `./tools/kb query "topic" --output slides`
2. The slides will be in output/slides/ in Marp format
3. Convert to HTML: `npx marp output/slides/filename.md -o output/slides/filename.html`
```

### 6.3 Makefile 快捷指令

```makefile
# Makefile — Common knowledge base operations

.PHONY: setup compile lint query search serve clean

# First-time setup
setup:
	bash scripts/bootstrap.sh

# Start all services
up:
	ollama serve &
	@echo "Ollama started on :11434"

# Compile wiki (incremental)
compile:
	./tools/kb compile --incremental

# Full recompilation
compile-full:
	./tools/kb compile --full

# Run health checks
lint:
	./tools/kb lint --check --suggest

# Auto-fix issues
fix:
	./tools/kb lint --fix

# Start search web UI
serve:
	./tools/kb serve --port 8080

# Show stats
status:
	./tools/kb status

# Daily maintenance
daily:
	bash scripts/daily_workflow.sh

# Clean generated files (keep raw/)
clean:
	rm -rf .compile_state.json .search_index.json
	@echo "Cleaned build state. Wiki and raw data preserved."
```

---

## 7. 進階功能與擴展 Advanced Features

### 7.1 LLM Router 進階配置

當知識庫規模增長，不同任務需要不同等級的模型。在 `config/litellm_config.yaml` 中配置 fallback chain：

```yaml
model_list:
  # Tier 1: Local fast (summaries, tagging, simple extraction)
  - model_name: "tier1"
    litellm_params:
      model: "ollama/llama3.2:3b"
      api_base: "http://localhost:11434"
      rpm: 30  # rate limit

  # Tier 2: Local main (article writing, Q&A, linting)
  - model_name: "tier2"
    litellm_params:
      model: "ollama/qwen2.5:14b"
      api_base: "http://localhost:11434"
      rpm: 10

  # Tier 3: Cloud heavy (complex multi-hop reasoning, long context)
  - model_name: "tier3"
    litellm_params:
      model: "anthropic/claude-sonnet-4-20250514"
      api_key: "os.environ/ANTHROPIC_API_KEY"
      rpm: 5

  # Tier 4: Cloud max (critical analysis, final report generation)
  - model_name: "tier4"
    litellm_params:
      model: "anthropic/claude-opus-4-20250514"
      api_key: "os.environ/ANTHROPIC_API_KEY"
      rpm: 2

router_settings:
  routing_strategy: "usage-based-routing"
  num_retries: 3
  fallbacks: [
    {"tier2": ["tier3"]},   # If local-main fails, try cloud
    {"tier3": ["tier4"]},   # If sonnet fails, try opus
  ]
  context_window_fallbacks: [
    {"tier2": ["tier3"]},   # If context too long for 14B, use cloud
  ]
```

### 7.2 Synthetic Data + Fine-tuning Pipeline

當 wiki 達到一定規模，可以考慮 fine-tuning 一個小型模型來「內化」知識：

```bash
# Step 1: Generate Q&A pairs from wiki (synthetic training data)
python scripts/generate_training_data.py \
    --wiki-dir wiki/ \
    --output training_data.jsonl \
    --pairs-per-article 10

# Step 2: Convert to Ollama modelfile format
python scripts/prepare_finetune.py \
    --input training_data.jsonl \
    --base-model qwen2.5:3b \
    --output Modelfile.kb

# Step 3: Create fine-tuned model in Ollama
ollama create kb-expert -f Modelfile.kb

# Step 4: Update config to use fine-tuned model for simple queries
# In config/models.yaml, set: query_simple: "ollama/kb-expert"
```

### 7.3 Multi-Vault 架構

不同研究主題使用獨立的 vault，共享工具鏈：

```
~/knowledge/
├── tools/                    # Shared CLI tools and scripts
├── config/                   # Shared LLM config
├── vaults/
│   ├── ai-research/         # AI/ML research vault
│   │   ├── raw/
│   │   ├── wiki/
│   │   └── .obsidian/
│   ├── crypto/              # Cryptocurrency research vault
│   │   ├── raw/
│   │   ├── wiki/
│   │   └── .obsidian/
│   └── biology/             # Biology research vault
│       ├── raw/
│       ├── wiki/
│       └── .obsidian/
└── cross-vault-index.md     # Cross-vault concept mapping
```

### 7.4 Web Search 增強（Lint 時自動補全缺失資料）

```python
# In scripts/lint.py, add web search capability for imputing missing data
def impute_missing_data(article_path: Path):
    """Use web search to fill in missing information in an article."""
    content = article_path.read_text(encoding="utf-8")

    # Identify gaps
    gaps = ask(
        f"Identify specific factual gaps or 'TODO' markers in this article:\n\n{content}",
        task="lint",
    )

    # For each gap, search the web and update
    # (integrate with your preferred search API: Tavily, SerpAPI, etc.)
    pass
```

---

## 8. 監控與維護 Monitoring & Maintenance

### 8.1 知識庫健康指標

```python
# scripts/metrics.py — Generate health metrics for the knowledge base
def generate_metrics():
    return {
        "total_raw_sources": count_files("raw/", "*.md"),
        "total_wiki_articles": count_files("wiki/concepts/", "*.md"),
        "total_words": sum_word_counts("wiki/"),
        "orphaned_articles": len(check_orphaned_articles()),
        "broken_links": len(check_broken_links()),
        "stub_articles": count_by_status("stub"),
        "draft_articles": count_by_status("draft"),
        "published_articles": count_by_status("published"),
        "avg_article_length": avg_word_count("wiki/concepts/"),
        "last_compile": get_last_compile_time(),
        "last_lint": get_last_lint_time(),
    }
```

### 8.2 Git 版本控制策略

```bash
# .gitignore
.venv/
.env
.compile_state.json
.search_index.json
node_modules/
__pycache__/
raw/repos/*/         # Don't track cloned repos (too large)
*.pyc

# DO track:
# raw/articles/      — curated sources
# raw/papers/        — paper conversions
# wiki/              — compiled wiki (track changes over time)
# output/            — query outputs
# config/            — configuration
# scripts/           — automation code
```

---

## 9. 快速開始流程 Quick Start

```bash
# 1. Clone or create the project
mkdir my-knowledge-base && cd my-knowledge-base

# 2. Run bootstrap
bash scripts/bootstrap.sh

# 3. Start Ollama
ollama serve

# 4. Ingest your first source
./tools/kb ingest url "https://example.com/interesting-article"

# 5. Compile the wiki
./tools/kb compile --full

# 6. Open in Obsidian
# Open Obsidian → Open folder as vault → select this directory

# 7. Ask your first question
./tools/kb query "What are the key concepts discussed in the sources?"

# 8. Run health check
./tools/kb lint --check --suggest

# 9. Generate a presentation
./tools/kb query "Overview of main themes" --output slides
```

---

## 10. 給 AI Agent 的實作檢查清單 Implementation Checklist for AI Agents

如果你是一個 AI agent（Claude Code, Cursor, Aider 等）正在實作這個系統，請按以下順序執行：

- [ ] **Phase 1: 環境** — 執行 `bootstrap.sh`，確認 Ollama, LiteLLM, Marp 可用
- [ ] **Phase 2: 核心** — 實作 `llm_client.py` 並通過基本 completion test
- [ ] **Phase 3: 攝入** — 實作 `ingest.py`，成功攝入一個 URL 和一個本地檔案
- [ ] **Phase 4: 編譯** — 實作 `compile.py`，從 raw/ 成功產生 wiki/ 文章
- [ ] **Phase 5: 查詢** — 實作 `query.py`，能回答基於 wiki 的問題
- [ ] **Phase 6: 品質** — 實作 `lint.py`，能檢測斷連結和孤立文章
- [ ] **Phase 7: 搜尋** — 實作 `search.py`，keyword search 可用
- [ ] **Phase 8: CLI** — 建立 `tools/kb` wrapper，所有子命令可用
- [ ] **Phase 9: Obsidian** — 確認 vault 可在 Obsidian 中開啟，Dataview queries 正常
- [ ] **Phase 10: 自動化** — 設定 daily workflow, Makefile 可用

每完成一個 Phase，執行 `./tools/kb status` 確認系統狀態正常。

---

> **最後一句話：** 這個系統的精神是——你（人類）決定探索什麼，LLM 負責所有的苦力活。
> Wiki 永遠是 LLM 的領域，你只需要閱讀、提問、和策展來源。
