# Contributing to Kiln

Thanks for your interest in contributing!

## Getting Started

```bash
git clone https://github.com/yourusername/kiln.git
cd kiln
bash scripts/bootstrap.sh
source .venv/bin/activate
pytest tests/ -v  # make sure everything passes
```

## Development Workflow

1. Fork the repo and create a branch from `main`
2. Write tests for any new functionality
3. Run `pytest tests/ -v` and make sure all tests pass
4. Submit a pull request

## Project Structure

- `scripts/` -- Python modules (ingest, compile, query, lint, search)
- `scripts/utils/` -- Shared utilities (LLM client, markdown helpers)
- `tools/kb` -- Shell CLI wrapper
- `config/` -- LLM routing and model configuration
- `tests/` -- pytest test suite

## Guidelines

- Keep functions focused and testable
- LLM calls should go through `scripts/utils/llm_client.py`
- Wrap user content in XML delimiters in LLM prompts (prompt injection defense)
- Add error handling around LLM calls (they can timeout or return bad output)
- Don't modify files in `raw/` from scripts other than `ingest.py`

## Reporting Issues

Open an issue with:
- What you expected to happen
- What actually happened
- Your OS, Python version, and Ollama model
