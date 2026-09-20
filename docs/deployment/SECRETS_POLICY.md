# Secrets and Sensitive Data Policy

## Never commit

- `.env` or any environment file containing values
- PostgreSQL passwords
- Open WebUI secret keys
- 9Router API keys
- SMTP credentials
- JWT or application signing secrets
- SSH private keys
- GitHub tokens
- WhatsApp session data
- employee, client, payroll, cash, or conversation data
- database dumps, backups, logs, or media

## Allowed in GitHub

- `.env.example` with placeholders only
- Compose files referencing environment variables
- schema definitions and reviewed migrations
- sanitized seed templates and test fixtures
- documentation that does not include secrets or private data

## Current audit findings

- The real VPS `.env` is ignored and untracked, but contains populated credentials.
- No credential value was printed during the audit.
- `.env.example` contains placeholders.
- No tracked private keys, GitHub tokens, common API-key patterns, database dumps, or runtime data artifacts were found.
- The VPS `.env` permissions were `664`; change them to `600`.
- Backup scripts write SQL files under `backups/`; those paths are now ignored by `.gitignore`.

## Handling rules

Use a separate development `.env` and development database. Prefer a VPS secret manager or owner-only environment file for production. Rotate credentials if they were exposed in shell history, logs, screenshots, chat, or tickets. Never use production credentials for local development.

## CI/CD secret rules

CI secrets belong in GitHub Actions secrets or environments. Production deployment secrets must require an explicit protected-environment approval. Do not store private SSH keys or production passwords in the repository.
