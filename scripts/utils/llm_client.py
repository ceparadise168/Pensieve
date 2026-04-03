"""
Unified LLM client for the Knowledge Base.
Resolves task → model alias → actual model, then calls Ollama directly via LiteLLM.
"""
import os
import yaml
from pathlib import Path
from litellm import completion, embedding

CONFIG_DIR = Path(__file__).parent.parent.parent / "config"


def _load_model_config() -> dict:
    with open(CONFIG_DIR / "models.yaml") as f:
        return yaml.safe_load(f)


def _load_litellm_config() -> dict:
    with open(CONFIG_DIR / "litellm_config.yaml") as f:
        return yaml.safe_load(f)


_config = _load_model_config()
_litellm_config = _load_litellm_config()

# Build alias → litellm_params lookup from litellm_config.yaml
_model_registry = {}
for entry in _litellm_config.get("model_list", []):
    _model_registry[entry["model_name"]] = entry["litellm_params"]


def get_model_for_task(task: str) -> str:
    """Resolve model alias for a given task type."""
    return _config["task_models"].get(task, "local-main")


def _resolve_model(alias: str) -> tuple[str, str]:
    """Resolve alias to (actual_model, api_base)."""
    params = _model_registry.get(alias, {})
    model = params.get("model", f"ollama/gemma4")
    api_base = params.get("api_base", "http://localhost:11434")
    return model, api_base


def ask(
    prompt: str,
    task: str = "query_simple",
    system: str = "",
    temperature: float = 0.3,
    max_tokens: int = 4096,
) -> str:
    """Send a prompt to the appropriate LLM based on task type."""
    alias = get_model_for_task(task)
    model, api_base = _resolve_model(alias)

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    response = completion(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        api_base=api_base,
    )
    return response.choices[0].message.content


def embed_text(text: str) -> list[float]:
    """Generate embedding vector for text using the embedding model."""
    alias = get_model_for_task("embed")
    model, api_base = _resolve_model(alias)

    response = embedding(
        model=model,
        input=[text],
        api_base=api_base,
    )
    return response.data[0]["embedding"]

MAX_CONTEXT_CHARS = 24000  # ~6K tokens, safe for most local models


def ask_with_context(
    question: str,
    context_files: list[str],
    task: str = "query_complex",
) -> str:
    """
    Ask a question with wiki files as context.
    Truncates total context to MAX_CONTEXT_CHARS to fit model context windows.
    """
    context_parts = []
    total_chars = 0
    for fpath in context_files:
        p = Path(fpath)
        if p.exists():
            content = p.read_text(encoding="utf-8")
            if total_chars + len(content) > MAX_CONTEXT_CHARS:
                remaining = MAX_CONTEXT_CHARS - total_chars
                if remaining > 500:
                    content = content[:remaining] + "\n[...truncated]"
                else:
                    break
            context_parts.append(f"--- {p.name} ---\n{content}\n")
            total_chars += len(content)

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
