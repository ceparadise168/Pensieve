#!/usr/bin/env bash
set -euo pipefail

echo "=== LLM Knowledge Base Bootstrap ==="

# ── 1. System tools ──
echo "[1/6] Installing system dependencies..."
brew install ollama marp-cli jq ripgrep pandoc 2>/dev/null || true

# ── 2. Python environment ──
echo "[2/6] Setting up Python environment..."
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip -q
pip install litellm openai anthropic click rich pyyaml \
            python-frontmatter beautifulsoup4 markdownify \
            matplotlib requests pytest numpy -q

# ── 3. Node.js dependencies ──
echo "[3/6] Installing Node.js dependencies..."
npm init -y 2>/dev/null || true
npm install --save-dev @marp-team/marp-cli 2>/dev/null || true

# ── 4. Ollama models ──
echo "[4/6] Pulling Ollama models (if space available)..."
ollama pull qwen2.5:3b 2>/dev/null || echo "  Skipped qwen2.5:3b (check disk space)"
ollama pull gemma4 2>/dev/null || echo "  Skipped gemma4 (check disk space)"
ollama pull nomic-embed-text 2>/dev/null || echo "  Skipped nomic-embed-text (check disk space)"

# ── 5. Directory structure ──
echo "[5/6] Creating directory structure..."
mkdir -p raw/{articles,papers,repos,datasets,images}
mkdir -p wiki/{concepts,summaries,connections,images}
mkdir -p output/{reports,slides,charts}
mkdir -p scripts/utils
mkdir -p tools
mkdir -p config
mkdir -p tests

# ── 6. Make tools executable ──
echo "[6/6] Setting permissions..."
chmod +x tools/kb 2>/dev/null || true
chmod +x scripts/daily_workflow.sh 2>/dev/null || true

echo ""
echo "=== Bootstrap complete ==="
echo "Next steps:"
echo "  1. Start Ollama:     ollama serve"
echo "  2. Open in Obsidian: Open folder as vault -> select this directory"
echo "  3. Ingest a source:  ./tools/kb ingest url 'https://...'"
echo "  4. Compile wiki:     ./tools/kb compile --full"
