param(
    [int]$Port = 8000,
    [string]$ListenAddress = "127.0.0.1",
    [string]$OpenWebUIUrl = "",
    [string]$AlrifaiEnvironment = "",
    [switch]$UseVerifiedIdentityVerifyContainer,
    [switch]$SkipOpenWebUI
)

$ErrorActionPreference = "Stop"
$python = Join-Path $PSScriptRoot "..\.venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $python)) { throw "Project virtual environment not found: $python" }

$localConfig = Join-Path $PSScriptRoot "..\.env.local"
if (-not $env:ALRIFAI_DATABASE_URL -and (Test-Path -LiteralPath $localConfig)) {
    foreach ($line in Get-Content -LiteralPath $localConfig) {
        if ($line -match '^\s*([A-Za-z_][A-Za-z0-9_]*)=(.*)$') {
            Set-Item -Path ("Env:" + $matches[1]) -Value $matches[2]
        }
    }
}

if (-not $env:ALRIFAI_DATABASE_URL -and $UseVerifiedIdentityVerifyContainer) {
    $container = "alrifai-identity-verify-02c"
    $containerInfo = docker ps --filter "name=^/$container$" --format "{{.Names}}|{{.Status}}|{{.Ports}}"
    if ($LASTEXITCODE -ne 0 -or -not $containerInfo -or $containerInfo -notmatch '^alrifai-identity-verify-02c\|Up .*127\.0\.0\.1:57395->5432/tcp$') {
        throw "The verified local PostgreSQL container is not running with the expected identity and port."
    }
    $databaseUser = (docker exec $container sh -c 'printf %s "$POSTGRES_USER"').Trim()
    $databaseName = (docker exec $container sh -c 'printf %s "$POSTGRES_DB"').Trim()
    $databasePassword = (docker exec $container sh -c 'printf %s "$POSTGRES_PASSWORD"').Trim()
    if (-not $databaseUser -or -not $databaseName -or -not $databasePassword) {
        throw "The verified container did not expose its local initialization connection configuration."
    }
    # Keep the password out of the URI and pass it only through the child
    # process environment consumed by libpq/psycopg.
    $env:PGPASSWORD = $databasePassword
    $env:ALRIFAI_DATABASE_URL = "postgresql://$databaseUser@127.0.0.1:57395/$databaseName"
    Remove-Variable databasePassword -ErrorAction SilentlyContinue
}
if (-not $env:ALRIFAI_DATABASE_URL) { throw "Local database configuration is missing. Create .env.local or set ALRIFAI_DATABASE_URL." }
if (-not $env:ALRIFAI_ENV) { $env:ALRIFAI_ENV = "local" }
if ($OpenWebUIUrl) { $env:ALRIFAI_OPEN_WEBUI_URL = $OpenWebUIUrl }
if ($AlrifaiEnvironment) { $env:ALRIFAI_ENV = $AlrifaiEnvironment }

$probeErrorAction = $ErrorActionPreference
$ErrorActionPreference = "Continue"
$databaseProbe = @(& $python -c "import os, psycopg; connection=psycopg.connect(os.environ['ALRIFAI_DATABASE_URL']); connection.close(); print('database connection verified')" 2>&1)
$probeExitCode = $LASTEXITCODE
$ErrorActionPreference = $probeErrorAction
if ($probeExitCode -ne 0) {
    throw ("Database connection probe failed: " + ($databaseProbe -join ' '))
}

if (-not $SkipOpenWebUI) {
    $composeRoot = Join-Path $PSScriptRoot ".."
    & docker compose -f (Join-Path $composeRoot "docker-compose.yml") up -d alrifai-open-webui
    if ($LASTEXITCODE -ne 0) { throw "Open WebUI could not be started by Docker Compose." }
}

& $python -m uvicorn src.alrifai.web.app:app --host $ListenAddress --port $Port --reload
