# Local multi-provider Copilot

This repository includes a secret-free Windows selector for the installed GitHub
Copilot CLI. It does not modify VPS services, 9Router configuration, Docker
configuration, gateway keys, or the user's persistent Copilot settings.

## Supported CLI configuration

The installed Copilot CLI is version `1.0.87-0`. Its provider help documents
environment-based BYOK configuration, not a `providers.json` file:

- `COPILOT_PROVIDER_BASE_URL`
- `COPILOT_PROVIDER_TYPE`
- `COPILOT_PROVIDER_API_KEY` or `COPILOT_PROVIDER_API_KEY_COMMAND`
- `COPILOT_PROVIDER_WIRE_API`
- `COPILOT_MODEL`

The `--model` command-line option overrides the model environment setting.
The provider environment is scoped to the launcher process and is cleared when
the launcher exits. No API key is written to the registry or repository.

## Registry and launcher

The registry is `scripts\copilot-providers.json`. The launcher is:

```powershell
.\scripts\select-copilot-provider.ps1 -List
.\scripts\select-copilot-provider.ps1 -Provider native-copilot
.\scripts\select-copilot-provider.ps1 -Provider 9router-general -Probe
.\scripts\select-copilot-provider.ps1 -Provider 9router-general -Probe -Compatibility
.\scripts\select-copilot-provider.ps1 -Provider ollama -Probe
```

For 9Router or Hugging Face, the launcher reads the API key as a secure prompt
and never prints it. The existing 9Router tunnel must already be running at
`http://127.0.0.1:20130/v1`.

`-Probe` (also accepted as `-Test`) performs model discovery and a
non-streaming chat probe. Adding
`-Compatibility` also probes streaming and tool-call response handling. A
provider is only considered verified after the required requests succeed.
`-Fallback` reports the
native Copilot fallback when a custom provider probe fails; it does not silently
claim that the failed provider worked.

## Current verification

| Provider | Status | Evidence |
|---|---|---|
| Native GitHub Copilot | VERIFIED LOCAL | `gh auth status` reports an active authenticated account; CLI starts with native routing |
| 9Router general combo | UNVERIFIED | Tunnel responds, but unauthenticated `/models` returns HTTP 401 |
| Poolside model | UNVERIFIED | `openrouter/poolside/laguna-s-2.1:free` is retained in the registry; authenticated inference was not run |
| Ollama | UNVERIFIED | `127.0.0.1:11434/api/tags` was unreachable during the audit |
| Hugging Face | UNVERIFIED | No endpoint/API-key probe was run |

## Rollback

Remove the newly added `scripts\copilot-providers.json`,
`scripts\select-copilot-provider.ps1`, and this document. Do not revert the
pre-existing `.gitignore`, `docker-compose.yml`, 9Router report, or tunnel
launcher changes. The launcher makes no persistent provider or service changes.
