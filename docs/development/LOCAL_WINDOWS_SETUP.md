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

## 6. PostgreSQL integration tests

The integration suite requires an explicitly isolated local PostgreSQL database.
Do not point these tests at the Compose database, an existing business database,
or any VPS database.

Install the project dependency into the local virtual environment:

```powershell
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Set a dedicated test connection string and the isolation flag for the current
PowerShell session. Do not save credentials in the repository:

```powershell
$env:ALRIFAI_TEST_DATABASE_URL = "postgresql://<test-user>:<test-password>@127.0.0.1:<random-port>/<test-database>"
$env:ALRIFAI_TEST_DATABASE_ISOLATED = "1"
```

Prepare the schema in a disposable PostgreSQL 17 container using
`database\init-sql\001_identity_foundation.sql`, a separate anonymous or
explicitly test-owned volume, and a random localhost port. Mount the SQL
directory read-only. Keep all test records inside that database.

Run the unit suite:

```powershell
.venv\Scripts\python.exe -m pytest -q
```

Run only the PostgreSQL integration suite:

```powershell
.venv\Scripts\python.exe -m pytest -q tests\integration\test_identity_resolver_postgres.py
```

When testing is complete, verify the container name and volume belong to this
test run, then remove only those named resources. Do not use `docker compose
down`, `docker system prune`, or `docker volume prune`. If ownership is
uncertain, stop and inspect rather than deleting.

## 7. Local web authentication

The local launcher uses the Git-ignored `.env.local` file. Keep its connection
for the preserved test container only:

```powershell
.\scripts\start-alrifai-web.ps1
```

The script verifies the database before starting. The application is served at
`http://127.0.0.1:8000/`. In VS Code, run
**Simple Browser: Show** from the Command Palette and enter that URL. Bootstrap
the approved Owner interactively:

```powershell
.venv\Scripts\python.exe -m src.alrifai.auth.bootstrap_owner
```

For local recovery, use the hidden-input command below. It does not send email
or SMS:

```powershell
.venv\Scripts\python.exe -m src.alrifai.auth.reset_password azimpolcu
```
