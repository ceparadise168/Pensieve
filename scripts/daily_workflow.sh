#!/usr/bin/env bash
# scripts/daily_workflow.sh — Run daily knowledge maintenance

set -euo pipefail
cd "$(dirname "$0")/.."

mkdir -p output
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

# Step 4: Rebuild search indexes
echo "[4/4] Rebuilding search indexes..."
./tools/kb search --rebuild-index

echo "=== Daily workflow complete ==="
