# Windows Local Development Setup

This project uses the workflow:

`Windows PC → GitHub → approved VPS release`

The Windows machine is independent from `/home/azim/alrifai-ai-platform`; use a normal Windows development directory such as:

`C:\Users\<YourWindowsUser>\source\repos\alrifai-ai-platform`

## 1. Verify tools

In PowerShell:

```powershell
git --version
gh --version
code --version
docker version
```

Install Git for Windows, GitHub CLI, and VS Code if any command is missing. Docker Desktop is only required for local container-based tests.

## 2. Authenticate and verify GitHub

```powershell
gh auth login
gh auth status
gh api user --jq .login
```

The account must be `arshiyaazim`. Do not paste tokens into the terminal or repository files.

For SSH authentication:

```powershell
ssh-keygen -t ed25519 -C "your-github-email@example.com"
Get-Service ssh-agent | Set-Service -StartupType Automatic
Start-Service ssh-agent
ssh-add $env:USERPROFILE\.ssh\id_ed25519
ssh -T git@github.com
```

Add the public key from `$env:USERPROFILE\.ssh\id_ed25519.pub` to GitHub. The private key must remain on the Windows machine and must never be committed.

## 3. Clone the approved repository

After the owner creates the empty private repository:

```powershell
cd "$env:USERPROFILE\source\repos"
git clone git@github.com:arshiyaazim/alrifai-ai-platform.git
cd .\alrifai-ai-platform
git status
code .
```

Do not use the VPS filesystem path on Windows.

## 4. Branch, test, commit, and push

```powershell
git switch -c feature/<short-description>
python -m pytest
git diff --check
git status
git add <specific-files>
git commit -m "Describe the focused change"
git push --set-upstream origin feature/<short-description>
gh pr create --base main --head feature/<short-description> --fill
```

Use focused branches and pull requests. Do not develop directly on `main`.

## 5. Local configuration

```powershell
Copy-Item .env.example .env
```

Use a separate development database and development-only credentials. Never copy VPS `.env`, production dumps, employee data, payroll data, or WhatsApp data to the Windows machine.
