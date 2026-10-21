# Supabase GitOps: Enterprise Database DevOps & CI/CD

An enterprise-grade, open-source **Database-as-Code (GitOps)** and continuous database deployment platform for **Supabase PostgreSQL**.

Provides reliable bi-directional synchronization between GitHub and Supabase:
- **Deploy forward**: Preview and apply version-controlled SQL migrations with automated pre-migration safety backups.
- **Capture drift**: Pull schema changes made in the Supabase Dashboard back into Git migration files using shadow database verification.
- **Automated backups**: Weekly encrypted application-schema backups (`public` schema and data) with AES-256 cipher, zero data leakage in Git, and 90-day retention.
- **Disaster recovery drills**: Automated decryption and containerized restore verification to prove backup viability.
- **Security & compliance**: Automated Row Level Security (RLS) enforcement gates on pull requests.
- **Multi-environment promotion**: Two-stage staging to production pipeline with GitHub Environment protection.
- **Performance & index advisor**: Linting for unindexed foreign keys and missing primary keys.
- **Living documentation**: Auto-generated schema documentation and interactive Mermaid ER diagrams.
- **Developer experience**: Automated TypeScript type generation and ephemeral PR database preview environments.

---

## Quickstart

### Step 1: Fork and Clone
Fork this repository to your GitHub account and clone your fork locally (replace `<your-username>` with your GitHub username):

```bash
git clone https://github.com/<your-username>/supabase-gitops.git
cd supabase-gitops
```

### Step 2: Configure GitHub Secrets
Go to your repo: **Settings > Secrets and variables > Actions > New repository secret** and add:

| Secret | Description | Example / Format |
|---|---|---|
| `SUPABASE_DB_URL` | *(Required)* Direct PostgreSQL connection string for production | `postgresql://postgres.<ref>:<password>@<host>:5432/postgres` |
| `BACKUP_ENCRYPTION_KEY` | *(Required)* Master password for encrypted backups | `<strong-backup-passphrase>` |
| `SUPABASE_STAGING_DB_URL` | *(Required for Promotion)* Independent Staging database connection string | `postgresql://postgres.<ref>:<password>@<host>:5432/postgres` |
| `WEBHOOK_URL` | *(Optional)* Discord or Slack webhook for notifications | `https://discord.com/api/webhooks/...` |
| `SUPABASE_ACCESS_TOKEN` | *(Optional)* Supabase Management API token for cloud branching | `sbp_...` |
| `SUPABASE_PROJECT_ID` | *(Optional)* Supabase project reference ID for cloud branching | `abcdefghijklmnopqrst` |

> **Note on `SUPABASE_DB_URL`**: Use the **Direct Connection** or **Session Mode Pooler** string from your Supabase Dashboard (**Project Settings > Database > Connection string**). Do not use the transaction pooler on port 6543.

### Step 3: Configure GitHub Environments & Protection Rules
To enforce safe multi-environment promotion from `staging` to `production`:
1. Navigate to **Settings > Environments** in your repository.
2. Create an environment named `staging`. Add `SUPABASE_STAGING_DB_URL` as an environment secret (or repository secret).
3. Create an environment named `production`. Enable **Required reviewers** and select authorized database administrators. Add `SUPABASE_DB_URL` as an environment secret (or repository secret).
4. The promotion pipeline strictly prevents staging from falling back to production: `SUPABASE_STAGING_DB_URL` must point to an independent database host or the workflow aborts before applying any changes.

### Step 4: Configure Workflow Permissions
In repository **Settings > Actions > General > Workflow permissions**, select **"Read and write permissions"** so GitHub Actions can commit updated TypeScript definitions and schema documentation.

### Step 5: Initialize Migrations (First-Time Setup / Baselining)
By default, this repository ships with an empty `supabase/migrations/` directory so you can connect to your project without conflicting starter migrations.

Choose the path that matches your project:

#### Path A: Adopting an Existing (Live) Supabase Project (Baselining)
If your Supabase project already has tables, functions, or prior migrations applied, **do not run drift capture or deploy right away**. First create a clean baseline of your remote database:

```bash
# 1. Export your remote database schema as your initial baseline migration
TIMESTAMP=$(date -u +%Y%m%d%H%M%S)
supabase db dump --db-url "$SUPABASE_DB_URL" --schema public -f "supabase/migrations/${TIMESTAMP}_baseline.sql"

# 2. Tell Supabase the baseline is already applied on the remote database
supabase migration repair --status applied "$TIMESTAMP" --db-url "$SUPABASE_DB_URL"

# 3. If remote history contains obsolete migration versions not in your repo, mark them reverted:
# (Run `supabase migration list --db-url "$SUPABASE_DB_URL"` to view unmanaged remote versions)
# supabase migration repair --status reverted <OLD_VERSION_ID> --db-url "$SUPABASE_DB_URL"

# 4. Commit and push your baseline
git add supabase/migrations/
git commit -m "chore: baseline initial database schema"
git push origin master
```

#### Path B: Starting a Brand-New / Empty Supabase Project
If you are starting from a completely fresh database and building a new schema from scratch:

```bash
# 1. Generate a new migration file
supabase migration new initial_schema

# 2. Write your DDL / SQL statements in supabase/migrations/<timestamp>_initial_schema.sql

# 3. Commit and push to master
git add supabase/migrations/
git commit -m "feat: add initial schema"
git push origin master
```
*To deploy your new migrations, run the **Deploy database migrations** workflow in GitHub Actions (or enable `AUTO_DEPLOY=true`).*

### Step 6: (Optional) Enable Scheduled Workflows
By default, **no workflows run on a schedule** to avoid consuming runner minutes or running before configuration. All workflows can be triggered manually on-demand at any time.

To activate automated recurring runs, navigate to **Settings > Secrets and variables > Actions > Variables** and create any of the following repository variables:

| Repository Variable | Purpose | Default Setting |
|---|---|---|
| `AUTO_DEPLOY` | Set to `true` to auto-deploy migrations on merge to `master` | Off (requires manual confirmation `deploy`) |
| `ENABLE_ALL_SCHEDULES` | Set to `true` to enable all automated recurring tasks | Off (no schedules run by default) |
| `ENABLE_SCHEDULED_BACKUPS` | Set to `true` to enable automated encrypted backups | Every Sunday at 02:00 UTC |
| `ENABLE_SCHEDULED_DRIFT_ALERTS` | Set to `true` to enable automated schema drift audits | Every Monday at 04:00 UTC |
| `ENABLE_SCHEDULED_RESTORE_DRILLS` | Set to `true` to enable automated disaster recovery drills | 1st of every month at 03:00 UTC |

---

## Repository Structure

```
.github/workflows/
  deploy-migrations.yml          # Forward: Apply local migrations -> Supabase
  capture-supabase-migrations.yml # Reverse: Capture dashboard schema drift -> local migration
  backup-database.yml            # Backups: Weekly encrypted full DB backup
  test-restore.yml               # DR: Monthly automated backup decryption & restore drill
  lint-migrations.yml            # CI: Test migration syntax & execution in Docker
  rls-security-audit.yml         # Security: Enforce Row Level Security (RLS) on PRs
  promote-migrations.yml         # Release: Staging -> Production promotion pipeline
  db-advisor.yml                 # Perf: Audit unindexed foreign keys & schema linter
  generate-docs.yml              # Docs: Living schema markdown & Mermaid ER diagram
  generate-types.yml             # DX: Generate TypeScript definitions (database.types.ts)
  preview-database.yml           # Previews: Ephemeral PR database branch environments
  drift-alert.yml                # Monitoring: Scheduled weekly schema drift detection
docs/
  schema.md                      # Auto-generated database schema & Mermaid ER diagram
scripts/
  generate_schema_docs.py        # Introspection script for documentation generator
supabase/
  config.toml                    # Supabase CLI project configuration
  seed.sql                       # Sample seed data for local development
  migrations/                    # Version-controlled migration files (empty by default)
types/
  database.types.ts              # Auto-generated TypeScript definitions
```

---

## Workflows Overview

### 1. Deploy Database Migrations (`deploy-migrations.yml`)
Pushes local migration files to the remote Supabase database:
- **Trigger**: Manual (`workflow_dispatch`) with confirmation `deploy`, or automatically on `push` to `master` when `AUTO_DEPLOY = true`.
- **Pre-migration Safety**: Automatically creates a schema backup artifact before applying changes.
- **Dry-run Preview**: Shows a dry-run preview of pending migrations.
- **Verification**: Outputs a post-deploy verification table comparing local and remote migration versions.
- **Post-Deploy Contract Sync**: Automatically regenerates and commits updated TypeScript definitions (`types/database.types.ts`) immediately upon deployment.
- **Pre-deployment History Audit**: Validates monotonic migration timestamps and blocks deployment if remote database has unmanaged applied migrations.
- **Destructive DDL Safeguards**: Warns and highlights destructive SQL (`DROP TABLE`, `DROP COLUMN`, `TRUNCATE`).

#### PostgreSQL DDL Transactionality & Failure Recovery
In PostgreSQL, most DDL statements (`CREATE TABLE`, `ALTER TABLE ... ADD COLUMN`, `DROP TABLE`) are transactional and automatically roll back if an error occurs within the migration script.

> [!WARNING]
> **Non-Transactional DDL**: Certain statements cannot execute inside a multi-statement transaction or cannot be rolled back if an error occurs later in the script:
> - `CREATE INDEX CONCURRENTLY` / `DROP INDEX CONCURRENTLY`
> - `VACUUM` / `CLUSTER`
> - `ALTER TYPE ... ADD VALUE` (when new values are referenced within the same transaction)

**Recovery Runbook for Failed Deployments**:
1. Download the pre-migration schema artifact (`pre-migration-backup-<run_id>`) from the failed workflow run.
2. If non-transactional operations partially modified the remote database, restore the pre-migration snapshot:
   ```bash
   psql "$SUPABASE_DB_URL" < pre_migration_backup.sql
   ```
3. Mark the failed migration reverted in the remote history table:
   ```bash
   supabase migration repair --status reverted <FAILED_VERSION_ID> --db-url "$SUPABASE_DB_URL"
   ```
4. Correct the migration SQL in your local branch, test locally with `supabase start`, and re-deploy.

---

### 2. Capture Schema Drift (`capture-supabase-migrations.yml`)
Brings visual schema changes made directly in the Supabase Dashboard back into version control:
- **Trigger**: Manual (`workflow_dispatch`) with confirmation `capture`.
- **Pre-flight Check**: Classifies remote migration history vs. local files into 4 baseline cases (A, B, C, D).
- **Shadow Database**: Uses a temporary Docker PostgreSQL shadow database to compute a clean consolidated schema diff.
- **Safety Validator**: Rejects data manipulation statements (`INSERT`, `UPDATE`, `DELETE`) to ensure no user data is committed to Git. Warns on destructive operations (`DROP TABLE`).

---

### 3. Encrypted Database Backups (`backup-database.yml`)
Creates an encrypted application-schema backup (`public` schema structure, sequences, triggers, and all table rows) with AES-256 cipher:
- **Trigger**: Weekly automated schedule (every Sunday at 02:00 UTC) or manual on-demand trigger.
- **Zero-Trust Encryption**: Uses `postgres:17-alpine` Docker container to run `pg_dump`, streaming output directly into `gpg` with **AES-256 symmetric encryption** via secure file descriptor piping (`--passphrase-fd 3`).
- **Clean Git**: Backups are stored as downloadable GitHub Actions Artifacts (retained for 90 days), preventing raw data from entering git history.

#### Backup & Recovery Boundaries

| Boundary Dimension | Scope & Behavior | Rationale / Prerequisite |
|---|---|---|
| **Included in Backup** | `public` schema tables, data rows, sequences, foreign keys, triggers, and custom functions | Captures all core business domain data and application state without triggering privilege errors. |
| **Excluded: `auth` Schema** | GoTrue identities, encrypted passwords, sessions, refresh tokens, MFA credentials | Managed by Supabase GoTrue; requires superuser/bypassrls to dump directly. Must be exported via Supabase Management API (`/v1/projects/{ref}/users`) or admin scripts. |
| **Excluded: `storage` Schema** | Storage bucket metadata and object tables (`storage.buckets`, `storage.objects`) | Underlying binary assets reside in S3-compatible object storage. Object storage must be replicated separately (e.g. via AWS CLI or rclone). |
| **Excluded: `vault` Schema** | Encrypted secrets and KMS keys managed by `pgsodium` | Decryption keys reside in Supabase Key Management System. Master secrets must be stored in external secret managers (e.g. GitHub Secrets). |
| **Excluded: Platform Schemas** | `graphql`, `realtime`, `pg_catalog`, `information_schema`, `supabase_functions` | Ephemeral or managed system schemas recreated automatically by the Supabase platform runtime. |

> [!NOTE]
> **Why `public` schema only?**
> On hosted Supabase instances (and AWS RDS / PostgreSQL-as-a-Service generally), connection strings connect via standard project roles (e.g., `postgres` or connection poolers). These roles lack superuser privileges to dump platform-owned schemas without throwing permission violations. Restricting the automated snapshot to `--schema=public` ensures reliable, clean backups without permission failures.

#### Enterprise Retention & Off-Site Storage Recommendations

GitHub Actions Artifact Storage provides convenience for CI/CD drills and intermediate verification, but has architectural limitations for production compliance:
- **Retention Limits**: GitHub Actions artifacts automatically expire after a maximum of 90 days.
- **Repository Coupling**: Artifacts are coupled to repository metadata and cannot be independently locked against accidental repository deletion or administrative pruning.
- **Compliance Gaps**: Enterprise compliance frameworks (SOC 2, HIPAA, ISO 27001) frequently mandate multi-year immutable retention.

##### Recommended Production Architecture: Off-Site Cloud Storage

For enterprise-grade disaster recovery, stream the encrypted output directly from the CI runner or cron agent into dedicated cloud object storage:

```
┌────────────────────────┐      ┌─────────────────────────┐      ┌─────────────────────────┐
│ Supabase PostgreSQL DB │ ───> │  AES-256 GPG Encryption │ ───> │ Immutable Object Store  │
│  (pg_dump application) │      │ (Streaming Unix Pipe)   │      │ (AWS S3 / Cloudflare R2)│
└────────────────────────┘      └─────────────────────────┘      └─────────────────────────┘
                                                                               │
                                                                   ┌───────────┴───────────┐
                                                                   │ Object Lock (WORM)    │
                                                                   │ Cross-Region Replic.  │
                                                                   │ Lifecycle: 7 Years    │
                                                                   └───────────────────────┘
```

1. **WORM Immutability (Write-Once, Read-Many)**:
   Enable **S3 Object Lock** in Compliance Mode or **GCS Bucket Lock** with retention locks. This prevents any entity—even cloud root administrators or compromised API keys—from deleting or tampering with database backups before the retention window expires.
2. **Cross-Region Replication (CRR)**:
   Replicate backup archives to a distinct geographical cloud region (e.g. `us-east-1` to `eu-central-1`) or a multi-cloud secondary provider (e.g. Cloudflare R2 or Wasabi) to eliminate single-cloud vendor risk.
3. **Tamper-Evident SHA-256 Manifest**:
   Every backup artifact generated by this repository includes a companion `manifest.sha256` and `manifest.json` file. Disaster recovery drills automatically compute and verify cryptographic hashes prior to decryption, guaranteeing detection of bit-rot, truncation, or hostile tampering.
4. **Direct Cloud Stream Example**:
   ```bash
   docker run --rm postgres:17-alpine \
     pg_dump "$SUPABASE_DB_URL" --schema=public --clean --if-exists --quote-all-identifiers \
     | gpg --batch --yes --symmetric --cipher-algo AES256 --passphrase-fd 3 3<<< "$BACKUP_ENCRYPTION_KEY" \
     | aws s3 cp - "s3://enterprise-db-backups/supabase/backup-$(date +%Y%m%d_%H%M%S).sql.gpg"
   ```

---

### 4. Disaster Recovery Restore Drill (`test-restore.yml`)
Proves backup integrity and disaster recovery readiness:
- **Trigger**: Monthly automated schedule (1st of every month at 03:00 UTC) or manual on-demand trigger.
- **Automated Verification**: Downloads the latest encrypted backup, decrypts with AES-256, restores into an isolated `postgres:17-alpine` container, and validates table counts and row integrity.

---

### 5. PR Migration Testing (`lint-migrations.yml`)
Runs automatically on every Pull Request modifying `supabase/migrations/**`:
- Verifies migration filenames follow the `YYYYMMDDHHMMSS_name.sql` standard.
- Spins up an ephemeral PostgreSQL 17 test container.
- Applies all migrations in sequence to verify syntax, foreign keys, and constraint integrity before merging.

---

### 6. Row Level Security Audit (`rls-security-audit.yml`)
Enforces database security standards on Pull Requests:
- Fails the build if any table in the `public` schema lacks `ENABLE ROW LEVEL SECURITY`.
- Audits for overly permissive mutation policies (`USING (true)` or `WITH CHECK (true)` on write operations).

---

### 7. Multi-Environment Promotion Pipeline (`promote-migrations.yml`)
Enterprise staging-to-production release management:
- First applies and verifies migrations in the `staging` environment.
- Promotes to `production` with pre-migration backups at each stage and GitHub Environment protection.

---

### 8. Database Performance Advisor (`db-advisor.yml`)
Schema optimization and query performance linter:
- Detects unindexed foreign keys to prevent full table scans on joins and cascades.
- Flags tables missing primary keys and runs `supabase db lint`.

---

### 9. Living Schema Documentation (`generate-docs.yml`)
Synchronizes database documentation with source code:
- Introspects tables, columns, and foreign key relationships.
- Generates an interactive Mermaid entity-relationship (ER) diagram and Markdown directory in `docs/schema.md`.

---

### 10. Automated TypeScript Types (`generate-types.yml`)
Generates complete TypeScript definitions directly from your database schema:
- Produces `types/database.types.ts`.
- Provides frontend/backend Supabase clients 100% end-to-end type safety and autocomplete.

---

### 11. Ephemeral PR Database Previews (`preview-database.yml`)
Disposable preview databases for feature testing on Pull Requests:
- Automatically creates an ephemeral database branch or test container per PR.
- Applies pending migrations and tears down the preview when the PR is merged or closed.

---

### 12. Scheduled Drift Alerting (`drift-alert.yml`)
Continuous compliance monitoring:
- Runs weekly on Monday at 04:00 UTC to detect uncaptured dashboard changes.
- Alerts the team in GitHub Actions if production schema drifts from repository code.

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
