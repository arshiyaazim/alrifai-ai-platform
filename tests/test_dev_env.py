import os
from pathlib import Path

from alrifai.ai_runtime.dev_env import load_development_env


def test_dev_env_loads_values_without_overriding_existing_environment(tmp_path: Path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "# comment\nNEW_VALUE='loaded value'\nexport SECOND=two\nEXISTING=from-file\nINVALID-NAME=ignored\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("EXISTING", "process-value")
    assert load_development_env(env_file) == ("NEW_VALUE", "SECOND")
    assert os.getenv("NEW_VALUE") == "loaded value"
    assert os.getenv("SECOND") == "two"
    assert os.getenv("EXISTING") == "process-value"
