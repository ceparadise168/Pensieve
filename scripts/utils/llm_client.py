"""
Unified LLM client for the Knowledge Base.
Uses LiteLLM Router in-process for retry, fallback, and model routing.
"""
import os
import yaml
from pathlib import Path
from litellm import Router, embedding

CONFIG_DIR = Path(__file__).parent.parent.parent / "config"


def _load_model_config() -> dict:
    config_path = CONFIG_DIR / "models.yaml"
    if not config_path.exists():
        return {"task_models": {}}
    with open(config_path) as f:
        return yaml.safe_load(f) or {"task_models": {}}


def _load_litellm_config() -> dict:
    config_path = CONFIG_DIR / "litellm_config.yaml"
    if not config_path.exists():
        return {"model_list": [], "router_settings": {}}
    with open(config_path) as f:
        return yaml.safe_load(f) or {}


_config = _load_model_config()
_litellm_config = _load_litellm_config()

# Initialize the LiteLLM Router with full config (retries, fallbacks, etc.)
_router_settings = _litellm_config.get("router_settings", {})
_model_list = _litellm_config.get("model_list", [])

_router = None
if _model_list:
    _router = Router(
        model_list=_model_list,
        num_retries=_router_settings.get("num_retries", 2),
        timeout=_router_settings.get("timeout", 120),
        allowed_fails=_router_settings.get("allowed_fails", 3),
        cooldown_time=_router_settings.get("cooldown_time", 60),
    )

# Build alias → params lookup for embed_text (Router doesn't handle embeddings)
_model_registry = {}
for entry in _model_list:
    _model_registry[entry["model_name"]] = entry["litellm_params"]


def get_model_for_task(task: str) -> str:
    """Resolve model alias for a given task type."""
    return _config["task_models"].get(task, "local-main")


def ask(
    prompt: str,
    task: str = "query_simple",
    system: str = "",
    temperature: float = 0.3,
    max_tokens: int = 4096,
) -> str:
    """Send a prompt to the appropriate LLM via the Router."""
    model = get_model_for_task(task)

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    if _router:
        response = _router.completion(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
    else:
        # Fallback: direct call if router not configured
        from litellm import completion
        response = completion(
            model="ollama/gemma4",
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            api_base="http://localhost:11434",
        )
    return response.choices[0].message.content


def embed_text(text: str) -> list[float]:
    """Generate embedding vector for text.
    Falls back to a simple hash-based pseudo-embedding if no embedding model available.
    """
    alias = get_model_for_task("embed")
    params = _model_registry.get(alias, {})
    model = params.get("model", "")
    api_base = params.get("api_base", "http://localhost:11434")

    # Check if model is a real embedding model (not a chat model)
    is_embed_model = any(kw in model.lower() for kw in ["embed", "nomic", "bge", "e5"])

    if is_embed_model:
        response = embedding(
            model=model,
            input=[text],
            api_base=api_base,
        )
        return response.data[0]["embedding"]

    # Fallback: simple bag-of-words hash embedding for chat models
    # Not great quality but allows search to function
    import hashlib
    import struct
    words = set(text.lower().split())
    vec = [0.0] * 128
    for word in words:
        h = hashlib.md5(word.encode()).digest()
        for i in range(0, 128, 4):
            idx = i // 4
            val = struct.unpack('f', h[idx % 16:(idx % 16) + 4])[0]
            vec[i % 128] += val
    # Normalize
    norm = sum(v * v for v in vec) ** 0.5
    if norm > 0:
        vec = [v / norm for v in vec]
    return vec


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
