# Test Status

## Latest recorded runs

| Scope | Result | Notes |
|---|---:|---|
| Full local suite with restored isolated PostgreSQL | 49 passed | Test-only container `alrifai-identity-verify-02c`; no production database used |
| Shared authentication integration | Passed | `/internal/auth-check`, session revocation/expiry/disabled checks, shared-cookie scope/delete semantics, and return-target validation |
| Local 9Router HTTP verification | Passed | Authenticated real completions previously verified for `general`, `coding`, `fast`, and `auto`; secrets omitted |
| VPS HTTPS/Nginx configuration | Blocked | SSH succeeds, but `sudo` requires an interactive password; no VPS change was attempted |
| `git diff --check` | Passed | Warning only about Git line-ending normalization |
| Verified-container runtime credential drift | Passed | Startup derives the current password from the isolated test container; local and Tailscale `/health` returned 200; unauthenticated `/internal/auth-check` returned 401 |

## Verification boundary

These results verify repository behavior and local integration only. They do not verify the public HTTPS browser flow, mobile layout, VPS Nginx, live messaging, or end-to-end frontend/MCP workflows.
