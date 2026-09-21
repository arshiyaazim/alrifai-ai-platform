# 9Router Local Setup Report

Generated for the Windows workspace at `D:\apps\alrifai-ai-platform`.

## Current status

| Check | Result |
|---|---|
| Git worktree | Preserved existing changes: `.gitignore` and `docker-compose.yml` are modified |
| SSH tunnel | Running as `127.0.0.1:20130 -> 127.0.0.1:20129` through SSH host `iamazim` |
| 9Router dashboard | Reachable at `http://127.0.0.1:20129/dashboard` |
| 9Router API path | Reachable, but unauthenticated requests return `401 Unauthorized` |
| API key in local process/user/machine/repository environment | Not present |
| Docker Desktop | Available and responding (`29.8.0`) |
| Docker Compose | Parses, with expected warnings because local `.env` secrets are not configured |
| Python test collection | 11 tests collected successfully |

The tunnel target is intentionally the VPS loopback API port `20129`. OmniRoute is separate and was not changed.

## API capability tests

Authenticated model discovery and authenticated chat, streaming, and tool-calling tests remain blocked until a 9Router API key is supplied securely. The unauthenticated checks reached the expected API and returned `401`, so this is an authentication prerequisite rather than a tunnel failure. No model/provider failure has been observed yet.

Do not put the key in `.env`, repository files, shell history, or command-line arguments. For a one-session test, enter it into a secure prompt and expose it only to the child process:

Run this exact block in the already-correct terminal. It prompts locally, performs discovery/chat/stream/tool probes, reports authentication separately from provider/model errors, then launches Copilot CLI with the same transient settings:

```powershell
$key = Read-Host "9Router API key" -AsSecureString
$ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($key)
try {
    $plain = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr)
    $env:COPILOT_PROVIDER_BASE_URL = "http://127.0.0.1:20130/v1"
    $env:COPILOT_PROVIDER_TYPE = "openai"
    $env:COPILOT_PROVIDER_API_KEY = $plain
    $env:COPILOT_PROVIDER_WIRE_API = "completions"
    $env:COPILOT_MODEL = "openrouter/poolside/laguna-s-2.1:free"
    $headers = @{ Authorization = "Bearer $plain"; "Content-Type" = "application/json" }
    $base = $env:COPILOT_PROVIDER_BASE_URL
    $model = $env:COPILOT_MODEL

    function Test-9RouterRequest([string]$Name, [string]$Uri, [string]$Body) {
        try {
            $response = Invoke-WebRequest -Uri $Uri -Method Post -Headers $headers -Body $Body -UseBasicParsing -TimeoutSec 60
            Write-Output "$Name => HTTP $($response.StatusCode)"
            return $response.Content
        }
        catch {
            $status = if ($_.Exception.Response) { [int]$_.Exception.Response.StatusCode } else { 0 }
            if ($status -eq 401 -or $status -eq 403) {
                Write-Output "$Name => AUTHENTICATION_FAILURE HTTP $status"
            }
            elseif ($status -gt 0) {
                Write-Output "$Name => PROVIDER_OR_MODEL_FAILURE HTTP $status"
            }
            else {
                Write-Output "$Name => TRANSPORT_FAILURE $($_.Exception.Message)"
            }
            return $null
        }
    }

    try {
        $models = Invoke-WebRequest -Uri "$base/models" -Method Get -Headers $headers -UseBasicParsing -TimeoutSec 30
        $ids = ($models.Content | ConvertFrom-Json).data.id -join ", "
        Write-Output "model discovery => HTTP $($models.StatusCode); models: $ids"
    }
    catch {
        $status = if ($_.Exception.Response) { [int]$_.Exception.Response.StatusCode } else { 0 }
        if ($status -eq 401 -or $status -eq 403) { Write-Output "model discovery => AUTHENTICATION_FAILURE HTTP $status" }
        elseif ($status -gt 0) { Write-Output "model discovery => PROVIDER_FAILURE HTTP $status" }
        else { Write-Output "model discovery => TRANSPORT_FAILURE $($_.Exception.Message)" }
    }

    $chatBody = @{ model = $model; messages = @(@{ role = "user"; content = "Reply with exactly: 9Router chat OK" }) } | ConvertTo-Json -Depth 6
    [void](Test-9RouterRequest "chat completion" "$base/chat/completions" $chatBody)

    $streamBody = @{ model = $model; messages = @(@{ role = "user"; content = "Reply with exactly: 9Router stream OK" }); stream = $true } | ConvertTo-Json -Depth 6
    $streamContent = Test-9RouterRequest "streaming completion" "$base/chat/completions" $streamBody
    if ($streamContent) { Write-Output "streaming completion => received response body" }

    $toolBody = @{
        model = $model
        messages = @(@{ role = "user"; content = "Use the lookup tool once." })
        tools = @(@{ type = "function"; function = @{ name = "lookup"; description = "Test tool"; parameters = @{ type = "object"; properties = @{} } } })
        tool_choice = "required"
    } | ConvertTo-Json -Depth 10
    $toolContent = Test-9RouterRequest "tool calling" "$base/chat/completions" $toolBody
    if ($toolContent) {
        $toolCalls = ($toolContent | ConvertFrom-Json).choices[0].message.tool_calls
        if ($toolCalls) { Write-Output "tool calling => MODEL_TOOL_CALL_RETURNED" }
        else { Write-Output "tool calling => MODEL_DID_NOT_RETURN_TOOL_CALL" }
    }

    copilot --model $model
}
finally {
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr)
    Remove-Item Env:COPILOT_PROVIDER_API_KEY -ErrorAction SilentlyContinue
    Remove-Item Env:COPILOT_PROVIDER_BASE_URL,COPILOT_PROVIDER_TYPE,COPILOT_PROVIDER_WIRE_API,COPILOT_MODEL -ErrorAction SilentlyContinue
}
```

This uses Copilot CLI's documented BYOK provider mode. `COPILOT_PROVIDER_API_KEY_COMMAND` is preferable when the key can be retrieved from an approved local secret manager, because the key is then refreshed per request and is not stored in the environment.

## Local multi-provider implementation

The secret-free local registry and Windows selector are now implemented:

- `scripts/copilot-providers.json`
- `scripts/select-copilot-provider.ps1`
- `docs/development/COPILOT_MULTI_PROVIDER.md`

The selector supports native Copilot, the existing 9Router general combo,
Ollama, and Hugging Face. Custom-provider variables are scoped to the child
Copilot process and restored afterward. The 9Router and Hugging Face keys are
requested through a secure prompt and are never written to files or printed.
`-Probe -Compatibility` performs model discovery, chat, streaming, and tool
calling probes; a failed custom provider can report the native Copilot fallback
without claiming the custom provider is healthy.

The installed CLI help did not document a `providers.json` schema. The
supported configuration surface is the `COPILOT_PROVIDER_*` environment
variables plus `COPILOT_MODEL` and command-line overrides.

## Copilot CLI provider support

Copilot CLI 1.0.87 documents OpenAI-compatible custom providers:

- `COPILOT_PROVIDER_BASE_URL=http://127.0.0.1:20130/v1`
- `COPILOT_PROVIDER_TYPE=openai`
- `COPILOT_PROVIDER_API_KEY` or `COPILOT_PROVIDER_API_KEY_COMMAND`
- `COPILOT_MODEL=openrouter/poolside/laguna-s-2.1:free`
- Optional `COPILOT_PROVIDER_WIRE_API=completions` (the default)
- Optional CLI `--stream on` or the persisted `stream` setting; streaming is enabled by default in this installed version

Do not assume agent tool support for the discovered model. The model must first pass an authenticated request containing a tool definition and return a valid tool call; a normal chat response is not evidence of tool support.

## VS Code Copilot Chat

The installed VS Code/Copilot configuration exposes model selections and existing OmniRoute settings, but no repository-local 9Router provider setting was found. The documented Copilot CLI BYOK variables apply to the CLI process and should not be copied into VS Code global settings. Keep OmniRoute settings unchanged.

VS Code can use custom language-model providers only when an installed extension contributes that provider through the VS Code language-model API. The current local configuration does not establish a native 9Router provider, so use the Copilot CLI BYOK path for this endpoint unless a dedicated VS Code provider extension is installed and configured.

## Safe tunnel launcher

Run:

```powershell
.\scripts\start-9router-tunnel.ps1
```

The launcher validates the SSH client and key path, refuses to overwrite a non-SSH process already using port `20130`, and starts:

```text
ssh -i $env:USERPROFILE\.ssh\id_ed25519 -N -T -o ExitOnForwardFailure=yes -L 127.0.0.1:20130:127.0.0.1:20129 iamazim
```

Rollback for the tunnel only is to stop the specific SSH PID reported by the launcher:

```powershell
Stop-Process -Id <reported-pid>
```

No VPS service, production configuration, 9Router installation, or OmniRoute setting is modified by this launcher.
