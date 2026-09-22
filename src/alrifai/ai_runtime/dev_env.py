"""Minimal server-side development ``.env`` loading.

This is deliberately limited to the development launcher. Existing process
environment values win, and parsed values are never logged or returned to a
client. Production deployments should provide environment/file references
through their own secret manager instead.
"""

from __future__ import annotations

import os
from pathlib import Path


def load_development_env(path: str | os.PathLike[str]) -> tuple[str, ...]:
    """Load simple ``KEY=VALUE`` entries without overriding the environment.

    Returns only the names loaded, which is useful for tests and diagnostics
    without making secret values observable.
    """

    loaded: list[str] = []
    env_path = Path(path)
    if not env_path.is_file():
        return ()
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].lstrip()
        if "=" not in line:
            continue
        name, value = line.split("=", 1)
        name = name.strip()
        if not name or not name.replace("_", "a").isalnum() or name[0].isdigit():
            continue
        if name in os.environ:
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        os.environ[name] = value
        loaded.append(name)
    return tuple(loaded)


def load_repo_development_env() -> tuple[str, ...]:
    """Load the repository-root ``.env`` for local/development processes."""

    repo_root = Path(__file__).resolve().parents[3]
    return load_development_env(repo_root / ".env")
