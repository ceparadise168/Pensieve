# Pensieve

> *"I use the Pensieve. One simply siphons the excess thoughts from one's mind, pours them into the basin, and examines them at one's leisure."* — Albus Dumbledore

A self-maintaining, LLM-compiled personal knowledge base.

Human curates sources. LLM compiles the wiki. Human reads in Obsidian.

Inspired by [Andrej Karpathy's LLM Knowledge Bases workflow](https://x.com/karpathy/status/2039805659525644595).

```
Traditional PKM:  Human -> Read -> Summarize -> Organize -> Query -> Answer
Pensieve:         Human -> Curate Sources -> LLM Compiles -> LLM Queries -> Human Reviews
```

## How it works

```
raw/                    LLM Compiler              wiki/
articles/ ─────┐                              ┌── concepts/
papers/   ─────┤   Summarize -> Extract ->    ├── summaries/
repos/    ─────┤   Write -> Index -> Graph    ├── _index.md
datasets/ ─────┘                              ├── _glossary.md
                                              └── _graph.md
                         │
                    Obsidian views it all
```

**`raw/`** is yours -- curate articles, papers, repos, datasets.
**`wiki/`** is the LLM's -- it writes and maintains every file.
**`output/`** holds query results -- reports, slides, charts.

## Quick start

```bash
# 1. Clone and bootstrap
git clone https://github.com/ceparadise168/Pensieve.git
cd Pensieve
bash scripts/bootstrap.sh

# 2. Start Ollama
ollama serve

# 3. Ingest your first source
./tools/kb ingest url "https://example.com/interesting-article"
# or
./tools/kb ingest file /path/to/paper.pdf

# 4. Compile the wiki
./tools/kb compile --full

# 5. Open in Obsidian (Open folder as vault -> select this directory)

# 6. Ask questions
./tools/kb query "What are the key concepts?"

# 7. Generate a report or slides
./tools/kb query "Deep analysis of topic X" --output report
./tools/kb query "Overview of topic Y" --output slides
```

## Commands

| Command | What it does |
|---------|-------------|
| `kb ingest url <url>` | Fetch a web article, convert to markdown, save to `raw/` |
| `kb ingest file <path>` | Ingest a local file (PDF, markdown, HTML, etc.) |
| `kb ingest repo <url>` | Shallow-clone a repo, extract docs and README summary |
| `kb compile --full` | Recompile entire wiki from all raw sources |
| `kb compile --incremental` | Only process new/changed sources |
| `kb query "question"` | Ask a question against the wiki |
| `kb query "topic" --output report` | Generate a long-form research report |
| `kb query "topic" --output slides` | Generate a Marp slide deck |
| `kb lint --check` | Run health checks (broken links, orphans, frontmatter) |
| `kb lint --fix` | Auto-fix issues (create stub articles for broken links) |
| `kb lint --suggest` | Get LLM suggestions for wiki improvements |
| `kb search "terms"` | Keyword search across the wiki |
| `kb search "question" --semantic` | Embedding-based semantic search |
| `kb search --rebuild-index` | Rebuild keyword and embedding indexes |
| `kb serve` | Start the search web UI on localhost:8080 |
| `kb status` | Show knowledge base stats |

## Architecture

```
┌──────────────┐     ┌─────────────┐     ┌──────────────────┐
│  Data Ingest │     │ LLM Compiler│     │   Output Layer   │
│  (ingest.py) │────>│ (compile.py)│────>│  wiki/, output/  │
└──────────────┘     └──────┬──────┘     └────────┬─────────┘
                            │                     │
                     ┌──────▼──────┐              │ feedback
                     │  LLM Router │              │ loop
                     │  (LiteLLM)  │<─────────────┘
                     └──────┬──────┘
                            │
                ┌───────────┼───────────┐
                ▼           ▼           ▼
           ┌────────┐ ┌─────────┐ ┌──────────┐
           │ Ollama │ │  Cloud  │ │ Fallback │
           │ (local)│ │  APIs   │ │  chain   │
           └────────┘ └─────────┘ └──────────┘
```

**LLM Router:** Uses [LiteLLM](https://github.com/BerriAI/litellm) Router in-process for automatic retries, fallbacks, and model selection per task type.

**Compile Pipeline (6 steps):**
1. Summarize each raw source
2. Extract key concepts across all summaries
3. Write/update a wiki article per concept
4. Build master index (grouped by tags)
5. Build glossary
6. Build concept relationship graph (Mermaid)

## LLM Configuration

Models are configured in `config/litellm_config.yaml` (which models to use) and `config/models.yaml` (which model handles which task).

```yaml
# config/models.yaml — task routing
task_models:
  summarize: "local-fast"        # Quick extraction
  compile_article: "local-main"  # Needs reasoning + writing quality
  query_simple: "local-main"     # Single-hop Q&A
  query_complex: "cloud-main"    # Multi-hop reasoning (cloud fallback)
  lint: "local-main"             # Consistency checking
  embed: "local-embed"           # Vector embeddings for search
```

**Recommended models (2026):**

| Task | Model | Ollama name | Size | Notes |
|------|-------|-------------|------|-------|
| Fast (summarize, tag) | Qwen 2.5 3B | `qwen2.5:3b` | ~2GB | Best instruction-following at this size |
| Main (articles, Q&A) | Qwen3 14B | `qwen3:14b` | ~12GB | Hybrid thinking mode, rivals GPT-4 for everyday tasks |
| Complex reasoning | DeepSeek-R1 32B | `deepseek-r1:32b` | ~24GB | Chain-of-thought reasoning with thinking tokens |
| Embeddings | nomic-embed-text | `nomic-embed-text` | ~0.3GB | Surpasses OpenAI text-embedding-3-small |

**Apple Silicon RAM guide:**

| RAM | Recommended setup |
|-----|-------------------|
| 8GB | `qwen2.5:3b` only — use cloud fallback for complex tasks |
| 16GB | `qwen2.5:3b` (fast) + `qwen3:14b` (main) + `nomic-embed-text` |
| 32GB | Above + `deepseek-r1:32b` or `gemma3:27b` for complex reasoning |
| 64GB+ | All local, no cloud needed — can run `qwen3:32b` comfortably |

## Obsidian Integration

Open this directory as an Obsidian vault. Recommended plugins:

- **Dataview** -- Dynamic queries over wiki articles (dashboard included at `wiki/_dashboard.md`)
- **Marp Slides** -- Preview generated slide decks
- **Graph Analysis** -- Visualize concept relationships
- **Obsidian Git** -- Auto-backup wiki changes

## Directory Structure

```
pensieve/
├── raw/                 # Human-curated sources (LLM read-only)
│   ├── articles/        # Web articles (.md via Clipper or ingest)
│   ├── papers/          # Academic papers (.pdf -> .md)
│   ├── repos/           # Cloned repositories
│   └── datasets/        # Data files (.csv, .json)
├── wiki/                # LLM-compiled output (human read-only)
│   ├── concepts/        # One article per concept
│   ├── summaries/       # Source document summaries
│   ├── connections/     # Cross-cutting analyses
│   ├── _index.md        # Master index
│   ├── _glossary.md     # Term definitions
│   ├── _graph.md        # Concept relationship map
│   └── _dashboard.md    # Obsidian Dataview dashboard
├── output/              # Query results
│   ├── reports/         # Long-form analysis
│   ├── slides/          # Marp slide decks
│   └── charts/          # Visualizations
├── scripts/             # Python automation
├── tools/kb             # CLI entry point
└── config/              # LLM and system configuration
```

## Requirements

- macOS / Linux
- Python 3.11+
- Node.js 18+ (for Marp slides)
- [Ollama](https://ollama.com) (for local LLM inference)
- [Obsidian](https://obsidian.md) (optional, for viewing)

## Development

```bash
# Run tests
source .venv/bin/activate
pytest tests/ -v

# Daily maintenance (compile + lint + fix + reindex)
make daily

# Full recompile
make compile-full
```

## License

[MIT](LICENSE)

## Credits

- Concept by [Andrej Karpathy](https://x.com/karpathy/status/2039805659525644595)
- Built with [LiteLLM](https://github.com/BerriAI/litellm), [Ollama](https://ollama.com), [Click](https://click.palletsprojects.com), [Obsidian](https://obsidian.md)
