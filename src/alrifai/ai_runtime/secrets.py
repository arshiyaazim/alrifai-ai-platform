"""Server-side secret resolution for AI gateways.

Secrets live in the process environment or a server-side file. They are
never returned to browsers, written to logs, or stored in configuration
rows. Frontends only learn ``credential_configured`` booleans.
"""

from __future__ import annotations

import os


class SecretMissing(RuntimeError):
    """No credential is configured for the requested gateway."""


class SecretResolver:
    """Resolve ``env:NAME`` / ``file:/path`` references without exposing values."""

    def __init__(self, environ: dict[str, str] | None = None) -> None:
        self._environ = environ if environ is not None else os.environ

    def credential_configured(self, secret_ref: str | None) -> bool:
        if secret_ref is None:
            return True
        try:
            self.resolve(secret_ref)
        except SecretMissing:
            return False
        return True

    def resolve(self, secret_ref: str) -> str:
        if secret_ref.startswith("env:"):
            value = self._environ.get(secret_ref[4:], "")
            if not value:
                raise SecretMissing("credential is not configured")
            return value
        if secret_ref.startswith("file:"):
            path = secret_ref[5:]
            try:
                with open(path, encoding="utf-8") as handle:
                    value = handle.read().strip()
            except OSError as exc:
                raise SecretMissing("credential file is unavailable") from exc
            if not value:
                raise SecretMissing("credential file is empty")
            return value
        raise SecretMissing("unsupported secret reference")
