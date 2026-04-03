---
title: 'Concept Graph'
updated: '2026-04-04'
---

# Concept Relationship Graph

```mermaid
graph LR
    llm-knowledge-bases --> Obsidian
    llm-knowledge-bases --> Knowledge Graph
    llm-knowledge-bases --> Retrieval-Augmented Generation (RAG)
    llm-knowledge-bases --> Personal Knowledge Management (PKM)
    llm-knowledge-bases --> Obsidian
    llm-knowledge-bases --> Markdown
    automated-content-compilation --> Retrieval-Augmented Generation (RAG)
    automated-content-compilation --> Personal Knowledge Management (PKM)
    automated-content-compilation --> Obsidian
    automated-content-compilation --> Knowledge Graph
    knowledge-structuring --> Personal Knowledge Base (PKB)
    knowledge-structuring --> Retrieval-Augmented Generation (RAG)
    knowledge-structuring --> Graph Databases
    knowledge-structuring --> Semantic Web
    knowledge-structuring --> Information Architecture
    knowledge-structuring --> LLM Knowledge Bases — Andrej Karpathy
```

## Adjacency List

- **automated-content-compilation** → [[Retrieval-Augmented Generation (RAG)]], [[Personal Knowledge Management (PKM)]], [[Obsidian]], [[Knowledge Graph]]
- **knowledge-structuring** → [[Personal Knowledge Base (PKB)]], [[Retrieval-Augmented Generation (RAG)]], [[Graph Databases]], [[Semantic Web]], [[Information Architecture]], [[LLM Knowledge Bases — Andrej Karpathy]]
- **llm-knowledge-bases** → [[Obsidian]], [[Knowledge Graph]], [[Retrieval-Augmented Generation (RAG)]], [[Personal Knowledge Management (PKM)]], [[Obsidian]], [[Markdown]]