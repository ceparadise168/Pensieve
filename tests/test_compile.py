import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from compile import _file_hash, _load_state, _save_state


def test_file_hash_deterministic(tmp_path):
    f = tmp_path / "test.md"
    f.write_text("hello world")
    assert _file_hash(f) == _file_hash(f)


def test_file_hash_changes(tmp_path):
    f = tmp_path / "test.md"
    f.write_text("hello world")
    h1 = _file_hash(f)
    f.write_text("hello world changed")
    h2 = _file_hash(f)
    assert h1 != h2


def test_state_roundtrip(tmp_path, monkeypatch):
    import compile
    state_file = tmp_path / ".compile_state.json"
    monkeypatch.setattr(compile, "STATE_FILE", state_file)
    _save_state({"file_hashes": {"a": "b"}, "last_compile": None})
    state_file_content = json.loads(state_file.read_text())
    assert state_file_content["file_hashes"]["a"] == "b"
    assert state_file_content["last_compile"] is not None
