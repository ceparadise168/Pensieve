import sys
from pathlib import Path

# Add scripts to path so we can import utils
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from utils.llm_client import get_model_for_task, _load_model_config


def test_load_model_config():
    config = _load_model_config()
    assert "task_models" in config


def test_get_model_for_task_known():
    model = get_model_for_task("summarize")
    assert model == "local-fast"


def test_get_model_for_task_compile():
    model = get_model_for_task("compile_article")
    assert model == "local-main"


def test_get_model_for_task_unknown_defaults():
    model = get_model_for_task("nonexistent_task")
    assert model == "local-main"


def test_get_model_for_task_embed():
    model = get_model_for_task("embed")
    assert model == "local-embed"
