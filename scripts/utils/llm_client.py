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
