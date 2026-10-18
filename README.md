# Supabase Database DevOps & CI/CD Workflow Template

A production-ready **Database-as-Code (GitOps)** and DevOps automation template for **Supabase PostgreSQL**.

Provides reliable bi-directional synchronization between GitHub and Supabase:
- **Deploy forward**: Preview and apply version-controlled SQL migrations with automated pre-migration safety backups.
- **Capture drift**: Pull schema changes made in the Supabase Dashboard back into Git migration files using shadow database verification.
- **Automated backups**: Weekly encrypted full-database backups (schema + data) with AES-256 cipher, zero data leakage in Git, and 90-day retention.
- **CI/CD Quality**: Automated PR migration testing, schema drift alerts, and optional TypeScript type generation.

---

## Quickstart

### Step 1: Use this template
Click the **"Use this template"** button at the top of this repository (or clone it).

### Step 2: Configure GitHub Secrets
Go to your repo: **Settings > Secrets and variables > Actions > New repository secret** and add:

| Secret | Description | Example / Format |
|---|---|---|
| `SUPABASE_DB_URL` | *(Required)* Direct PostgreSQL connection string | `postgresql://postgres.<ref>:<password>@<host>:5432/postgres` |
| `BACKUP_ENCRYPTION_KEY` | *(Required)* Master password for encrypted backups | `MyStrongPassword2026!#` |
| `WEBHOOK_URL` | *(Optional)* Discord or Slack webhook for notifications | `https://discord.com/api/webhooks/...` |

> **Note on `SUPABASE_DB_URL`**: Use the **Direct Connection** or **Session Mode Pooler** string from your Supabase Dashboard (**Project Settings > Database > Connection string**). Do not use the transaction pooler on port 6543.

### Step 3: Customize or Deploy
- Modify or replace the starter migration in `supabase/migrations/20261019000000_initial.sql`.
- Run the **Deploy database migrations** workflow to apply it to your Supabase project.

---

## Repository Structure

```
.github/workflows/
  deploy-migrations.yml          # Forward: Apply local migrations → Supabase
  capture-supabase-migrations.yml # Reverse: Capture dashboard schema drift → local migration
  backup-database.yml            # Backups: Weekly encrypted full DB backup
  lint-migrations.yml            # CI: Test migration syntax & execution on Pull Requests
  generate-types.yml             # DX: Generate TypeScript definitions (database.types.ts)
  drift-alert.yml                # Monitoring: Scheduled weekly schema drift detection
supabase/
  config.toml                    # Supabase CLI project configuration
  seed.sql                       # Sample seed data for local development
  migrations/
    20261019000000_initial.sql   # Starter migration (profiles table with RLS)
```

---

## Workflows Overview

### 1. Deploy Database Migrations (`deploy-migrations.yml`)
Pushes **local** migration files to the **remote** Supabase database.

- **Trigger**: Manual (`workflow_dispatch`) with confirmation `deploy`.
- **Pre-migration Safety**: Automatically creates a schema backup artifact before applying any change.
- **Dry-run Preview**: Shows a dry-run preview of pending migrations.
- **Verification**: Outputs a post-deploy verification table comparing local and remote migration versions.

---

### 2. Capture Schema Drift (`capture-supabase-migrations.yml`)
Brings visual schema changes made directly in the **Supabase Dashboard** back into version control.

- **Trigger**: Manual (`workflow_dispatch`) with confirmation `capture`.
- **Pre-flight Check**: Classifies remote migration history vs. local files into 4 baseline cases (A, B, C, D).
- **Shadow Database**: Uses a temporary Docker PostgreSQL shadow database to compute a clean consolidated schema diff.
- **Safety Validator**: Rejects data manipulation statements (`INSERT`, `UPDATE`, `DELETE`) to ensure no user data is committed to Git. Warns on destructive operations (`DROP TABLE`).
- **Linear Git History**: Re-bases and pushes the new migration file directly to `master`.

---

### 3. Encrypted Database Backups (`backup-database.yml`)
Creates a full, self-contained snapshot of the remote PostgreSQL database (**schema + all table rows**).

- **Trigger**: Weekly automated schedule (every Sunday at 02:00 UTC) or manual on-demand trigger.
- **Zero-Trust Encryption**: Uses `postgres:17-alpine` Docker container to run `pg_dump`, streaming output directly into `gpg` with **AES-256 symmetric encryption**.
- **Clean Git**: Backups are stored as downloadable **GitHub Actions Artifacts** (retained for 90 days), ensuring zero sensitive data leaks into Git history.

#### How to restore any backup:
```bash
# 1. Download the artifact from GitHub Actions and decrypt with your password:
gpg --decrypt supabase_backup_<timestamp>.sql.gpg > rebuild.sql

# 2. Rebuild your database anywhere:
# Option A: Paste rebuild.sql into any Supabase Dashboard SQL Editor
# Option B: Feed into any Postgres instance via terminal:
psql "<TARGET_DATABASE_URL>" < rebuild.sql
```

---

### 4. PR Migration Testing (`lint-migrations.yml`)
Runs automatically on every Pull Request modifying `supabase/migrations/**`:
- Verifies migration filenames follow the `YYYYMMDDHHMMSS_name.sql` standard.
- Spins up an ephemeral PostgreSQL 17 test container.
- Applies all migrations in sequence to verify syntax, foreign keys, and constraint integrity before merging.

---

### 5. Automated TypeScript Types (`generate-types.yml`)
Generates complete TypeScript definitions directly from your remote database schema:
- Produces `types/database.types.ts`.
- Gives your frontend/backend Supabase client 100% end-to-end type safety and autocomplete.

---

### 6. Scheduled Drift Alerting (`drift-alert.yml`)
Runs weekly on Monday at 04:00 UTC to check if uncaptured dashboard changes were made.
- Posts a warning in GitHub Actions if schema drift is detected, reminding your team to capture migrations.

---

## Local Development

Local development requires Docker and Supabase CLI:

```bash
# 1. Start local Supabase stack (applies migrations and seed.sql automatically)
supabase start

# 2. Check local database status
supabase status

# 3. Create a new migration file
supabase migration new <feature_name>

# 4. Stop local stack
supabase stop
```

---

## License

MIT License. Free to use for personal, academic, and commercial projects.
