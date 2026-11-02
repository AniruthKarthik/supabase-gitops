# Contributing to Supabase GitOps

Thank you for your interest in contributing to Supabase GitOps! This project helps developers and teams run automated migrations, drift detection, and verified backups for Supabase PostgreSQL.

---

## Getting Started

### Entry Points for Contributors
- Check open issues tagged with [`good first issue`](https://github.com/AniruthKarthik/supabase-gitops/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22) for beginner-friendly tasks.
- Browse the [Roadmap](README.md#roadmap) section in the README for upcoming priorities (such as direct S3/R2 backup streaming, Auth schema exports, and configurable `main` branch support).

### Prerequisites
- [Docker](https://docs.docker.com/get-docker/) (used for ephemeral PostgreSQL containers in tests)
- [Supabase CLI](https://supabase.com/docs/guides/cli) (`brew install supabase/tap/supabase` or equivalent)
- Python 3.10+ (for documentation introspection scripts)

---

## Local Development & Testing

Before submitting a pull request, run the local verification test suites:

### 1. Test Local Migration Lifecycle
Validates clean container initialization, sequential migration execution, seed data insertion, and rollback on syntax errors:

```bash
./scripts/test_local_migrations.sh
```

### 2. Test Negative Recovery & DR Traps
Runs automated negative tests against decryption and restore failure paths:

```bash
./scripts/test_backup_negative.sh
```

### 3. Test RLS Authorization Matrix
Inspects Row Level Security policies and executes role impersonation (`anon`, `authenticated`, `service_role`):

```bash
# Start local Supabase instance
supabase start

# Run the RLS audit harness
psql "postgresql://postgres:postgres@127.0.0.1:54322/postgres" -f scripts/audit_rls_behavior.sql
```

---

## Repository Conventions

### Default Branch
- The primary branch of this repository is currently **`master`**.
- Please base feature branches off `master` and target pull requests to `master`.

### Branch Naming
- `feat/<feature-name>` for new features or workflows
- `fix/<bug-description>` for bug fixes and edge case remediation
- `docs/<documentation-topic>` for documentation and runbook updates
- `test/<test-description>` for harness and validation improvements

### Commit Messages
We follow Conventional Commits:
- `feat(workflows): add direct S3 upload step to backup workflow`
- `fix(dr): catch corrupt pg_dump header in test-restore drill`
- `docs: update baseline runbook with repair command examples`

---

## Pull Request Guidelines

1. **Keep Workflows Robust**:
   - Ensure shell steps use `set -euo pipefail`.
   - Never suppress errors using `|| true` on database or drift comparison commands.
   - Never expose secret passphrases in CLI arguments; use streaming file descriptors (e.g. `--passphrase-fd 3`).
2. **Automated Checks**:
   - Every pull request runs `lint-migrations.yml`, `rls-security-audit.yml`, and `db-advisor.yml`.
   - All CI checks must pass before merging.
3. **Documentation**:
   - If introducing new secrets, variables, or workflow triggers, update `README.md` and relevant runbooks in `docs/`.

---

## Labels Reference

| Label | Description |
|---|---|
| `good first issue` | Good for newcomers; self-contained scope with clear guidance |
| `help wanted` | Open community task requiring attention |
| `area/workflows` | Changes to GitHub Actions workflows in `.github/workflows/` |
| `area/backup` | Changes to backup, encryption, or restore drill logic |
| `area/migrations` | Changes to migration baselining, drift capture, or SQL scripts |
| `area/docs` | Improvements to README, runbooks, or demonstration walkthroughs |
