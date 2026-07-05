import json
import pytest
from pathlib import Path
from unittest.mock import patch
from model_manager import ModelManager


@pytest.fixture
def config_file(tmp_path):
    cfg = {
        "llm": {"provider": "mlx", "model": "mlx-community/Qwen3.6-35B-A3B-4bit"},
        "vlm": {"provider": "mlx", "model": "mlx-community/Qwen3-VL-8B-Instruct"},
        "tts": {"provider": "mlx-audio", "model": "kokoro"},
        "stt": {"provider": "mlx-audio", "model": "whisper-large-v3"},
    }
    p = tmp_path / "models.json"
    p.write_text(json.dumps(cfg))
    return str(p)


def test_loads_config(config_file):
    mgr = ModelManager(config_file)
    assert mgr.config["llm"]["model"] == "mlx-community/Qwen3.6-35B-A3B-4bit"


def test_get_download_command(config_file):
    mgr = ModelManager(config_file)
    cmd = mgr.get_download_command("llm")
    assert "mlx-community/Qwen3.6-35B-A3B-4bit" in cmd
    assert "hf download" in cmd


def test_check_model_available_missing(config_file):
    mgr = ModelManager(config_file)
    with patch.object(Path, "exists", return_value=False):
        assert mgr.is_model_available("llm") is False


def test_check_model_available_present(config_file):
    mgr = ModelManager(config_file)
    with patch.object(Path, "exists", return_value=True):
        assert mgr.is_model_available("llm") is True
