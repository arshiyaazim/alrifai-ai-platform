# Test Status

## Latest recorded runs

| Scope | Result | Notes |
|---|---:|---|
| Unit/regression without integration variables | 34 passed, 10 skipped | PostgreSQL suites skipped by isolation guard; Task 03B-01 policy tests included |
| Full suite with isolated PostgreSQL | 38 passed | Uses preserved `alrifai-identity-verify-02c` local test container |
| `git diff --check` | Passed | Warning only about Git line-ending normalization |

## Verification boundary

These results verify repository behavior and an isolated local database only. They do not verify production, VPS, live messaging, Admin authorization, or end-to-end frontend/MCP workflows.
