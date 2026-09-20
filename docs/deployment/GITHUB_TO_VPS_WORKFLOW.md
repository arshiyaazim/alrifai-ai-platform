# GitHub to VPS Workflow

## Deployment principle

GitHub is the reviewed source of code. The VPS deploys an approved commit explicitly; it must not deploy every experimental push.

The AL-RIFAI Compose project remains independent from Fazle-Core, Hermes, WhatsApp bridges, Ollama, 9Router, and the existing Open WebUI deployment. Deployment commands must target only `/home/azim/alrifai-ai-platform`.

## Release flow

1. Develop on a Windows feature branch.
2. Run lint, tests, migration validation, and secret scanning.
3. Open a pull request against `main`.
4. Review and merge the approved change.
5. Record the merge commit or release tag.
6. On the VPS, verify the local working tree, fetch GitHub, and check out the approved commit.
7. Verify configuration and backup readiness.
8. Validate migrations without applying destructive changes.
9. Deploy only the affected AL-RIFAI services with the project Compose file.
10. Run health checks and record the deployed commit.

## First-push preparation (do not run until approved)

After authenticated GitHub verification and creation of the empty private repository:

```bash
cd /home/azim/alrifai-ai-platform
git remote add origin git@github.com:arshiyaazim/alrifai-ai-platform.git
git push -u origin main
```

The first push is intentionally not executed by this audit.

## VPS release procedure

```bash
cd /home/azim/alrifai-ai-platform
git status --short --branch
git fetch --prune origin
git show --no-patch --format='%H %s' <approved-commit>
git diff --exit-code HEAD <approved-commit>
git checkout --detach <approved-commit>
docker compose config
./scripts/health-check.sh
docker compose up -d alrifai-postgres alrifai-open-webui
./scripts/health-check.sh
git show -s --format='%H' HEAD
```

The `git diff` check is a review gate; deployment should stop if the VPS contains unexpected local changes or the approved commit is not the expected one. Do not use `git reset --hard` as an automatic deployment step.

## Service boundaries

Do not restart or recreate:

- Fazle-Core
- Hermes
- WhatsApp bridges
- Ollama
- 9Router
- existing Open WebUI

Only AL-RIFAI services may be changed by the AL-RIFAI deployment procedure.
