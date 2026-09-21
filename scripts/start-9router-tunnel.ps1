[CmdletBinding()]
param(
    [string]$SshHost = "iamazim",
    [string]$IdentityFile = "$env:USERPROFILE\.ssh\id_ed25519",
    [int]$LocalPort = 20130,
    [string]$RemoteHost = "127.0.0.1",
    [int]$RemotePort = 20129
)

$ErrorActionPreference = "Stop"

if (-not (Get-Command ssh.exe -ErrorAction SilentlyContinue)) {
    throw "OpenSSH client was not found on PATH."
}

if (-not (Test-Path -LiteralPath $IdentityFile -PathType Leaf)) {
    throw "SSH identity file was not found: $IdentityFile"
}

$existing = Get-NetTCPConnection -LocalPort $LocalPort -ErrorAction SilentlyContinue
if ($existing) {
    $owners = $existing | Select-Object -ExpandProperty OwningProcess -Unique
    foreach ($owner in $owners) {
        $process = Get-Process -Id $owner -ErrorAction SilentlyContinue
        if ($process -and $process.Path -and ($process.Path -ieq (Get-Command ssh.exe).Source)) {
            Write-Output "SSH tunnel already appears to be running on 127.0.0.1:$LocalPort (PID $owner)."
            exit 0
        }
    }

    throw "Local port $LocalPort is already in use by another process."
}

$arguments = @(
    "-i", $IdentityFile,
    "-N",
    "-T",
    "-o", "ExitOnForwardFailure=yes",
    "-o", "ServerAliveInterval=15",
    "-o", "ServerAliveCountMax=3",
    "-o", "ConnectTimeout=15",
    "-L", "127.0.0.1:$LocalPort`:$RemoteHost`:$RemotePort",
    $SshHost
)

$process = Start-Process -FilePath (Get-Command ssh.exe).Source -ArgumentList $arguments -PassThru -WindowStyle Hidden
Start-Sleep -Seconds 2

if ($process.HasExited) {
    throw "SSH tunnel exited immediately with code $($process.ExitCode)."
}

Write-Output "Started 9Router tunnel: 127.0.0.1:$LocalPort -> $RemoteHost`:$RemotePort via $SshHost (PID $($process.Id))."
