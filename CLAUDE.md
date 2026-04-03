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
```
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
