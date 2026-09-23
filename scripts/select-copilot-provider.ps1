[CmdletBinding()]
param(
    [ValidateSet("native-copilot", "9router-general", "poolside-laguna", "ollama", "huggingface")]
    [string]$Provider = "native-copilot",
    [string]$Model,
    [switch]$List,
    [Alias("Test")]
    [switch]$Probe,
    [switch]$Fallback,
    [switch]$NoChat,
    [switch]$Compatibility,
    [string]$RegistryPath = "$PSScriptRoot\copilot-providers.json"
)

$ErrorActionPreference = "Stop"

function Read-Registry {
    if (-not (Test-Path -LiteralPath $RegistryPath -PathType Leaf)) {
        throw "Provider registry was not found: $RegistryPath"
    }
    return Get-Content -Raw -LiteralPath $RegistryPath | ConvertFrom-Json
}

function Get-ProviderEntry([object]$Registry, [string]$Name) {
    $entry = $Registry.providers.$Name
    if (-not $entry) {
        throw "Provider '$Name' is not defined in the registry."
    }
    return $entry
}

function Get-SecureApiKey {
    $secure = Read-Host "Provider API key" -AsSecureString
    $ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
    try {
        return [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr)
    }
    finally {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr)
    }
}

function Invoke-ProviderProbe([object]$Entry, [string]$ApiKey, [string]$SelectedModel) {
    $headers = @{ "Content-Type" = "application/json" }
    if ($ApiKey) {
        $headers.Authorization = "Bearer $ApiKey"
    }

    try {
        $models = Invoke-WebRequest -UseBasicParsing -Uri "$($Entry.baseUrl)/models" -Headers $headers -TimeoutSec 15
        $modelIds = @((($models.Content | ConvertFrom-Json).data | ForEach-Object { $_.id }))
        $modelFound = $modelIds -contains $SelectedModel
        Write-Information "model discovery => HTTP $($models.StatusCode); selected model advertised: $modelFound" -InformationAction Continue
    }
    catch {
        $status = if ($_.Exception.Response) { [int]$_.Exception.Response.StatusCode } else { 0 }
        if ($status -eq 401 -or $status -eq 403) {
            Write-Information "model discovery => AUTHENTICATION_FAILURE HTTP $status" -InformationAction Continue
        }
        elseif ($status -gt 0) {
            Write-Information "model discovery => PROVIDER_FAILURE HTTP $status" -InformationAction Continue
        }
        else {
            Write-Information "model discovery => TRANSPORT_FAILURE" -InformationAction Continue
        }
        return $false
    }

    $body = @{
        model = $SelectedModel
        messages = @(@{ role = "user"; content = "Reply with exactly: provider chat OK" })
    } | ConvertTo-Json -Depth 6

    try {
        $chat = Invoke-WebRequest -UseBasicParsing -Method Post -Uri "$($Entry.baseUrl)/chat/completions" -Headers $headers -Body $body -TimeoutSec 60
        Write-Information "chat completion => HTTP $($chat.StatusCode)" -InformationAction Continue
    }
    catch {
        $status = if ($_.Exception.Response) { [int]$_.Exception.Response.StatusCode } else { 0 }
        if ($status -eq 401 -or $status -eq 403) {
            Write-Information "chat completion => AUTHENTICATION_FAILURE HTTP $status" -InformationAction Continue
        }
        elseif ($status -gt 0) {
            Write-Information "chat completion => PROVIDER_OR_MODEL_FAILURE HTTP $status" -InformationAction Continue
        }
        else {
            Write-Information "chat completion => TRANSPORT_FAILURE" -InformationAction Continue
        }
        return $false
    }

    if ($Compatibility) {
        $streamBody = @{
            model = $SelectedModel
            messages = @(@{ role = "user"; content = "Reply with exactly: provider stream OK" })
            stream = $true
        } | ConvertTo-Json -Depth 6

        try {
            $stream = Invoke-WebRequest -UseBasicParsing -Method Post -Uri "$($Entry.baseUrl)/chat/completions" -Headers $headers -Body $streamBody -TimeoutSec 60
            $streamText = [string]$stream.Content
            if ($streamText -match "data:") {
                Write-Information "streaming completion => HTTP $($stream.StatusCode); SSE data received" -InformationAction Continue
            }
            else {
                Write-Information "streaming completion => HTTP $($stream.StatusCode); response was not SSE" -InformationAction Continue
            }
        }
        catch {
            $status = if ($_.Exception.Response) { [int]$_.Exception.Response.StatusCode } else { 0 }
            Write-Information "streaming completion => FAILURE HTTP $status" -InformationAction Continue
        }

        $toolBody = @{
            model = $SelectedModel
            messages = @(@{ role = "user"; content = "Use the lookup tool once." })
            tools = @(@{
                type = "function"
                function = @{
                    name = "lookup"
                    description = "Compatibility probe"
                    parameters = @{ type = "object"; properties = @{} }
                }
            })
            tool_choice = "required"
        } | ConvertTo-Json -Depth 10

        try {
            $tool = Invoke-WebRequest -UseBasicParsing -Method Post -Uri "$($Entry.baseUrl)/chat/completions" -Headers $headers -Body $toolBody -TimeoutSec 60
            $toolCalls = ($tool.Content | ConvertFrom-Json).choices[0].message.tool_calls
            if ($toolCalls) {
                Write-Information "tool calling => MODEL_TOOL_CALL_RETURNED" -InformationAction Continue
            }
            else {
                Write-Information "tool calling => MODEL_DID_NOT_RETURN_TOOL_CALL" -InformationAction Continue
            }
        }
        catch {
            $status = if ($_.Exception.Response) { [int]$_.Exception.Response.StatusCode } else { 0 }
            Write-Information "tool calling => FAILURE HTTP $status" -InformationAction Continue
        }
    }

    return $true
}

function Set-ProviderEnvironment([object]$Entry, [string]$ApiKey, [string]$SelectedModel) {
    $env:COPILOT_PROVIDER_BASE_URL = [string]$Entry.baseUrl
    $env:COPILOT_PROVIDER_TYPE = [string]$Entry.type
    $env:COPILOT_PROVIDER_WIRE_API = [string]$Entry.wireApi
    $env:COPILOT_MODEL = $SelectedModel
    if ($ApiKey) {
        $env:COPILOT_PROVIDER_API_KEY = $ApiKey
    }
}

function Clear-ProviderEnvironment {
    param([hashtable]$OriginalEnvironment)
    foreach ($name in $OriginalEnvironment.Keys) {
        if ($null -eq $OriginalEnvironment[$name]) {
            Remove-Item "Env:$name" -ErrorAction SilentlyContinue
        }
        else {
            Set-Item "Env:$name" $OriginalEnvironment[$name]
        }
    }
}

$registry = Read-Registry

if ($List) {
    foreach ($name in $registry.fallbackOrder) {
        $entry = Get-ProviderEntry $registry $name
        Write-Output ("{0}`t{1}`t{2}`t{3}" -f $name, $entry.status, $entry.type, $entry.model)
    }
    exit 0
}

$selectedName = $Provider
$selectedEntry = Get-ProviderEntry $registry $selectedName
$selectedModel = if ($Model) { $Model } else { [string]$selectedEntry.model }
$providerEnvironmentNames = @(
    "COPILOT_PROVIDER_BASE_URL",
    "COPILOT_PROVIDER_TYPE",
    "COPILOT_PROVIDER_WIRE_API",
    "COPILOT_MODEL",
    "COPILOT_PROVIDER_API_KEY",
    "PATH"
)
$originalEnvironment = @{}
foreach ($name in $providerEnvironmentNames) {
    $originalEnvironment[$name] = [Environment]::GetEnvironmentVariable($name, "Process")
}

# Ensure Windows PowerShell directory is in PATH for Copilot child process.
# Copilot's internal shell discovery searches for powershell.exe/pwsh.exe;
# if System32\WindowsPowerShell\v1.0 is missing from PATH the lookup fails.
$psDir = "$([Environment]::GetEnvironmentVariable('SystemRoot'))\System32\WindowsPowerShell\v1.0"
if (Test-Path -LiteralPath "$psDir\powershell.exe" -PathType Leaf) {
    $currentPath = [Environment]::GetEnvironmentVariable("PATH", "Process")
    if ($currentPath -split [System.IO.Path]::PathSeparator -notcontains $psDir) {
        [Environment]::SetEnvironmentVariable("PATH", "$psDir$([System.IO.Path]::PathSeparator)$currentPath", "Process")
    }
}

if ($selectedEntry.type -eq "native") {
    Write-Output "provider => native GitHub Copilot subscription"
    if (-not $NoChat) {
        & copilot --model $selectedModel
        exit $LASTEXITCODE
    }
    exit 0
}

$apiKey = $null
try {
    if ($selectedEntry.requiresApiKey) {
        $apiKey = Get-SecureApiKey
    }

    if ($Probe) {
        $healthy = Invoke-ProviderProbe $selectedEntry $apiKey $selectedModel
        if (-not $healthy -and $Fallback) {
            foreach ($fallbackName in $registry.fallbackOrder) {
                if ($fallbackName -eq $selectedName) {
                    continue
                }
                $fallbackEntry = Get-ProviderEntry $registry $fallbackName
                if ($fallbackEntry.type -eq "native") {
                    Write-Output "fallback => native GitHub Copilot subscription"
                    exit 0
                }
            }
        }
        if (-not $healthy) {
            exit 2
        }
    }

    Set-ProviderEnvironment $selectedEntry $apiKey $selectedModel
    if ($NoChat) {
        Write-Output "provider => $selectedName"
        Write-Output "model => $selectedModel"
        exit 0
    }
    & copilot --model $selectedModel
    exit $LASTEXITCODE
}
finally {
    Clear-ProviderEnvironment $originalEnvironment
}
