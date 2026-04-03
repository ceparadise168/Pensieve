# LLM Knowledge Base Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a self-maintaining, LLM-compiled personal knowledge base where human curates sources into `raw/`, LLM compiles `wiki/`, and human reads via Obsidian.

**Architecture:** Python CLI tools orchestrate LLM calls (via LiteLLM router to Ollama local models with cloud fallback) to ingest raw sources, compile them into structured wiki articles, answer queries, and maintain wiki health. Shell wrapper `tools/kb` is the single entry point. Obsidian is the read-only UI.

**Tech Stack:** Python 3.11, Click (CLI), LiteLLM (LLM router), Ollama (local models), python-frontmatter, BeautifulSoup4, Marp (slides), Obsidian (viewer)

---

## File Structure

```
knowledge-base/
├── CLAUDE.md                      # Agent instructions
├── Makefile                       # Shortcut commands
├── pyproject.toml                 # Python project config
├── config/
│   ├── litellm_config.yaml        # LLM router config
│   ├── models.yaml                # Task → model mapping
│   └── env.example                # Env var template
├── scripts/
│   ├── ingest.py                  # Data ingestion pipeline
│   ├── compile.py                 # Wiki compilation orchestrator
│   ├── query.py                   # Q&A interface
│   ├── lint.py                    # Wiki health checker
│   ├── search.py                  # Local search engine
│   ├── daily_workflow.sh          # Daily maintenance script
│   └── utils/
│       ├── __init__.py
│       ├── llm_client.py          # Unified LLM API client
│       └── markdown_utils.py      # Markdown parsing helpers
├── tools/
│   └── kb                         # Main CLI entry point (shell)
├── tests/
│   ├── test_llm_client.py
│   ├── test_ingest.py
│   └── test_compile.py
├── raw/                           # Human-curated sources (LLM read-only)
│   ├── articles/
│   ├── papers/
│   ├── repos/
│   ├── datasets/
│   └── images/
├── wiki/                          # LLM-compiled output (human read-only)
│   ├── _index.md
│   ├── _glossary.md
│   ├── _graph.md
│   ├── _dashboard.md
│   ├── concepts/
│   ├── summaries/
│   ├── connections/
│   └── images/
└── output/                        # Query outputs
    ├── reports/
    ├── slides/
    └── charts/
```

---

### Task 1: Directory Structure & Config Files

**Files:**
- Create: `config/litellm_config.yaml`
- Create: `config/models.yaml`
- Create: `config/env.example`
- Create: `CLAUDE.md`
- Create: `Makefile`
- Create: `pyproject.toml`
- Create: `.gitignore`
- Create: all `raw/`, `wiki/`, `output/` subdirectories

- [ ] **Step 1: Create all directories**

```bash
cd /Users/erictu/worksapce/KM
mkdir -p raw/{articles,papers,repos,datasets,images}
mkdir -p wiki/{concepts,summaries,connections,images}
mkdir -p output/{reports,slides,charts}
mkdir -p scripts/utils
mkdir -p tools
mkdir -p config
mkdir -p tests
```

- [ ] **Step 2: Create config/litellm_config.yaml**

The LiteLLM router config pointing to local Ollama models. See blueprint Section 2.2 for full content.

- [ ] **Step 3: Create config/models.yaml**

Task-to-model mapping. See blueprint Section 2.2.

- [ ] **Step 4: Create config/env.example**

Environment variable template. See blueprint Section 2.2.

- [ ] **Step 5: Create CLAUDE.md**

Agent instructions file. See blueprint Section 2.2.

- [ ] **Step 6: Create .gitignore**

```
.venv/
.env
.compile_state.json
.search_index.json
node_modules/
__pycache__/
raw/repos/*/
*.pyc
```

- [ ] **Step 7: Create pyproject.toml**

- [ ] **Step 8: Create Makefile**

See blueprint Section 6.3.

- [ ] **Step 9: Git init and initial commit**

```bash
git init
git add -A
git commit -m "chore: initial project structure and config"
```

---

### Task 2: Python Environment & Dependencies

- [ ] **Step 1: Create virtualenv and install dependencies**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install litellm openai anthropic click rich pyyaml python-frontmatter beautifulsoup4 markdownify matplotlib requests pytest numpy
```

- [ ] **Step 2: Install Node dependencies (Marp)**

```bash
npm init -y
npm install --save-dev @marp-team/marp-cli
```

- [ ] **Step 3: Pull Ollama models**

```bash
ollama pull llama3.2:3b
ollama pull qwen2.5:14b
ollama pull nomic-embed-text
```

- [ ] **Step 4: Verify Ollama is serving**

```bash
ollama list
```

---

### Task 3: LLM Client (`scripts/utils/llm_client.py`)

**Files:**
- Create: `scripts/utils/__init__.py`
- Create: `scripts/utils/llm_client.py`
- Create: `tests/test_llm_client.py`

- [ ] **Step 1: Create `scripts/utils/__init__.py`** (empty file)

- [ ] **Step 2: Write test for llm_client**

```python
# tests/test_llm_client.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from utils.llm_client import get_model_for_task, _load_model_config

def test_load_model_config():
    config = _load_model_config()
    assert "task_models" in config

def test_get_model_for_task_known():
    model = get_model_for_task("summarize")
    assert model == "local-fast"

def test_get_model_for_task_unknown_defaults():
    model = get_model_for_task("nonexistent_task")
    assert model == "local-main"
```

- [ ] **Step 3: Run test to verify it fails**

```bash
source .venv/bin/activate
pytest tests/test_llm_client.py -v
```

- [ ] **Step 4: Implement `scripts/utils/llm_client.py`**

Full implementation from blueprint Section 3.1: `ask()`, `embed_text()`, `ask_with_context()`, `get_model_for_task()`.

- [ ] **Step 5: Run tests to verify they pass**

```bash
pytest tests/test_llm_client.py -v
```

- [ ] **Step 6: Commit**

```bash
git add scripts/utils/ tests/test_llm_client.py
git commit -m "feat: add unified LLM client with task-based model routing"
```

---

### Task 4: Markdown Utilities (`scripts/utils/markdown_utils.py`)

**Files:**
- Create: `scripts/utils/markdown_utils.py`

- [ ] **Step 1: Implement markdown_utils.py**

```python
"""Markdown parsing helpers for the Knowledge Base."""
from pathlib import Path
from markdownify import markdownify
import subprocess

def html_to_markdown(html: str) -> str:
    """Convert HTML content to clean Markdown."""
    return markdownify(html, heading_style="ATX", strip=["script", "style"])

def pdf_to_markdown(pdf_path: Path) -> str:
    """Convert PDF to Markdown using pandoc."""
    result = subprocess.run(
        ["pandoc", str(pdf_path), "-t", "markdown", "--wrap=none"],
        capture_output=True, text=True, timeout=60,
    )
    if result.returncode == 0:
        return result.stdout
    raise RuntimeError(f"pandoc failed: {result.stderr}")

def find_relevant_files(wiki_dir: Path, keywords: list[str], top_k: int = 10) -> list[Path]:
    """Find wiki files containing the most keyword matches."""
    scores = {}
    for md_file in wiki_dir.rglob("*.md"):
        content = md_file.read_text(encoding="utf-8").lower()
        score = sum(content.count(kw.lower()) for kw in keywords)
        if score > 0:
            scores[md_file] = score
    ranked = sorted(scores.items(), key=lambda x: -x[1])
    return [p for p, _ in ranked[:top_k]]
```

- [ ] **Step 2: Commit**

```bash
git add scripts/utils/markdown_utils.py
git commit -m "feat: add markdown parsing utilities (HTML, PDF conversion)"
```

---

### Task 5: Ingest Pipeline (`scripts/ingest.py`)

**Files:**
- Create: `scripts/ingest.py`
- Create: `tests/test_ingest.py`

- [ ] **Step 1: Write ingest test**

```python
# tests/test_ingest.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from ingest import _slug

def test_slug_basic():
    assert _slug("Hello World Example") == "hello-world-example"

def test_slug_special_chars():
    assert _slug("What's New? (2024)") == "whats-new-2024"

def test_slug_max_length():
    long = "a" * 100
    assert len(_slug(long)) <= 80
```

- [ ] **Step 2: Run test to verify it fails**

- [ ] **Step 3: Implement `scripts/ingest.py`**

Full implementation from blueprint Section 3.2: `url`, `file`, `repo` commands with Click CLI.

- [ ] **Step 4: Run tests to verify pass**

- [ ] **Step 5: Commit**

```bash
git add scripts/ingest.py tests/test_ingest.py
git commit -m "feat: add data ingest pipeline (url, file, repo)"
```

---

### Task 6: Wiki Compiler (`scripts/compile.py`)

**Files:**
- Create: `scripts/compile.py`
- Create: `tests/test_compile.py`

- [ ] **Step 1: Write compile test**

```python
# tests/test_compile.py
import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from compile import _file_hash, _load_state, _save_state

def test_file_hash_deterministic(tmp_path):
    f = tmp_path / "test.md"
    f.write_text("hello world")
    assert _file_hash(f) == _file_hash(f)

def test_state_roundtrip(tmp_path, monkeypatch):
    import compile
    state_file = tmp_path / ".compile_state.json"
    monkeypatch.setattr(compile, "STATE_FILE", state_file)
    _save_state({"file_hashes": {"a": "b"}, "last_compile": None})
    loaded = _load_state()
    assert loaded["file_hashes"]["a"] == "b"
    assert loaded["last_compile"] is not None
```

- [ ] **Step 2: Run test to verify it fails**

- [ ] **Step 3: Implement `scripts/compile.py`**

Full implementation from blueprint Section 3.3: 5-step pipeline (summarize, extract concepts, write articles, build index, build graph).

- [ ] **Step 4: Run tests to verify pass**

- [ ] **Step 5: Commit**

```bash
git add scripts/compile.py tests/test_compile.py
git commit -m "feat: add wiki compiler (summarize, extract, write, index, graph)"
```

---

### Task 7: Query Engine (`scripts/query.py`)

**Files:**
- Create: `scripts/query.py`

- [ ] **Step 1: Implement `scripts/query.py`**

Full implementation from blueprint Section 3.4: text, report, and slides output modes with `--file-back` option.

- [ ] **Step 2: Commit**

```bash
git add scripts/query.py
git commit -m "feat: add Q&A engine with text, report, and slides output"
```

---

### Task 8: Wiki Linter (`scripts/lint.py`)

**Files:**
- Create: `scripts/lint.py`

- [ ] **Step 1: Implement `scripts/lint.py`**

Full implementation from blueprint Section 3.5: broken links, orphans, frontmatter checks, auto-fix, LLM suggestions.

- [ ] **Step 2: Commit**

```bash
git add scripts/lint.py
git commit -m "feat: add wiki linter with health checks and auto-fix"
```

---

### Task 9: Search Engine (`scripts/search.py`)

**Files:**
- Create: `scripts/search.py`

- [ ] **Step 1: Implement `scripts/search.py`**

Full implementation from blueprint Section 3.6: keyword search, semantic search, web UI server.

- [ ] **Step 2: Commit**

```bash
git add scripts/search.py
git commit -m "feat: add search engine (keyword, semantic, web UI)"
```

---

### Task 10: CLI Wrapper (`tools/kb`)

**Files:**
- Create: `tools/kb`

- [ ] **Step 1: Create `tools/kb`**

Shell wrapper from blueprint Section 4. Dispatches to ingest, compile, query, lint, search, serve, status.

- [ ] **Step 2: Make executable and test**

```bash
chmod +x tools/kb
./tools/kb help
./tools/kb status
```

- [ ] **Step 3: Commit**

```bash
git add tools/kb
git commit -m "feat: add kb CLI wrapper with all subcommands"
```

---

### Task 11: Obsidian Dashboard & Daily Workflow

**Files:**
- Create: `wiki/_dashboard.md`
- Create: `scripts/daily_workflow.sh`

- [ ] **Step 1: Create Obsidian dashboard**

Dataview-powered dashboard from blueprint Section 5.3.

- [ ] **Step 2: Create daily workflow script**

From blueprint Section 6.1.

- [ ] **Step 3: Commit**

```bash
git add wiki/_dashboard.md scripts/daily_workflow.sh
git commit -m "feat: add Obsidian dashboard and daily workflow automation"
```

---

### Task 12: End-to-End Smoke Test

- [ ] **Step 1: Ingest a test source**

Create a small test markdown file in `raw/articles/` manually, then run compile.

- [ ] **Step 2: Compile wiki**

```bash
./tools/kb compile --full
```

- [ ] **Step 3: Verify wiki output**

```bash
ls wiki/concepts/ wiki/summaries/
cat wiki/_index.md
```

- [ ] **Step 4: Run lint**

```bash
./tools/kb lint --check
```

- [ ] **Step 5: Search**

```bash
./tools/kb search "test"
```

- [ ] **Step 6: Query**

```bash
./tools/kb query "What topics are covered in the knowledge base?"
```

- [ ] **Step 7: Status check**

```bash
./tools/kb status
```
