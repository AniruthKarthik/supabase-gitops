# Supabase GitOps Template

Supabase PostgreSQL schema and migration history for Supabase PostgreSQL.

---

## Repository layout

```
.github/workflows/
  deploy-migrations.yml          # Manually deploy local migrations → remote DB
  capture-supabase-migrations.yml # Manually capture dashboard changes → local files
  backup-database.yml            # Weekly automated + manual encrypted full DB backup
supabase/
  config.toml                    # Supabase CLI project configuration
  migrations/
    20261019000000_initial.sql   # Initial schema (profiles, RLS)
```

---

## GitHub Actions workflows

### 1. Deploy database migrations (`deploy-migrations.yml`)

Pushes **local** migration files to the **remote** Supabase database.

| Trigger | Manual (`workflow_dispatch`) |
|---|---|
| Input | `confirm_deploy: true` |
| Secret | `SUPABASE_DB_URL` |
| Branch | `master` |

---

### 2. Capturing schema drift from the Supabase dashboard

> **`capture-supabase-migrations.yml`** — the reverse direction.

Use this when you modify the database schema directly in the Supabase dashboard
and want to bring those changes back into the repository as a migration file.

#### What it can recover

| Situation | Outcome |
|---|---|
| **Case A** — Dashboard changes are in the remote history but have no local file | Generates a new consolidated diff migration using `supabase db pull` |
| **Case D** — Local files already match the remote history | Exits successfully, no commit |

#### What it cannot recover

| Situation | Outcome |
|---|---|
| **Case B** — Remote history contains versions whose original SQL is not stored | **Stops and explains reconciliation options** — the original DDL is gone and cannot be reconstructed from a schema diff |
| **Case C** — Both local files and remote history have extra entries the other side lacks | **Stops and requires manual reconciliation** — the baseline is ambiguous |

> **Important:** The generated migration is a *consolidated schema diff* — the SQL
> needed to transform the last local baseline into the current remote state.
> It does **not** reproduce the original sequence of individual dashboard changes.
> Always review the generated file before running the deploy workflow.

#### Required GitHub secret

Add a secret named **`SUPABASE_DB_URL`** at:

```
Repository > Settings > Secrets and variables > Actions > New repository secret
```

Use the **Direct Connection** or **Session Pooler** string from your Supabase
project dashboard (Database > Connect). **Do not use the Transaction Pooler
(port 6543)** — the Supabase CLI needs a persistent session.

```
postgresql://postgres.<project-ref>:<password>@<host>:5432/postgres
```

The secret is used only inside the workflow runner and is never printed to logs
or committed to the repository.

#### How to trigger

1. Open **Actions** in your GitHub repository.
2. Select **Capture database migrations** from the left sidebar.
3. Click **Run workflow**.
4. In the **confirm** field, type exactly: `capture`
5. Click **Run workflow**.

The workflow will:

1. Check out `master`.
2. Run `supabase migration list --db-url` to compare local files with the remote
   migration history table.
3. Query the remote history table to verify that SQL is stored for each
   remote-only version (distinguishing Case A from Case B).
4. If safe (Case A), run `supabase db pull --db-url` to generate a new
   migration file in `supabase/migrations/`.
5. Validate the generated SQL (must be non-empty, schema-only, inside
   `supabase/migrations/`).
6. Commit and push only the new file to `master`.
7. If nothing changed or the situation requires manual intervention, exit with
   a clear explanation.

#### After a successful capture

The new migration file is committed to `master` automatically. Before deploying
it to another environment, review the SQL:

```
supabase/migrations/<new-timestamp>_<name>.sql
```

When you are satisfied, trigger **Deploy database migrations** to apply it.

#### Case B — what to do when original SQL is missing

If the workflow fails with a Case B error, the remote migration history contains
an entry whose SQL was never stored (e.g. a change made via `psql` directly or
an older dashboard path). You have three options:

**Option 1 — Write the SQL by hand (recommended)**

```bash
# Create the file locally
cat > supabase/migrations/<version>_<description>.sql << 'SQL'
-- Reconstruct the change manually
ALTER TABLE ...;
SQL

# Register it in the remote history
supabase migration repair \
  --status applied <version> \
  --db-url "$SUPABASE_DB_URL"

# Commit and push, then re-trigger the capture workflow
git add supabase/migrations/
git commit -m "fix(db): add missing migration file for version <version>"
git push
```

**Option 2 — Placeholder (history-only)**

Use this when you cannot reconstruct the SQL but want to keep the history table
and local files in sync:

```bash
supabase migration repair --status applied <version> --db-url "$SUPABASE_DB_URL"

cat > supabase/migrations/<version>_placeholder.sql << 'SQL'
-- Placeholder: this migration was applied directly via the Supabase dashboard
-- or psql on <date>. The original SQL was not captured. Schema state at this
-- point: <brief description>
SQL

git add supabase/migrations/
git commit -m "fix(db): add placeholder for uncaptured migration <version>"
git push
```

After either option, re-trigger the capture workflow.

#### Case C — what to do when the baseline is ambiguous

This happens when local files and the remote history have diverged in both
directions simultaneously. Fix it locally:

```bash
# Check the current state
supabase migration list --db-url "$SUPABASE_DB_URL"

# For each remote version missing from your local files:
#   Either add the file, or mark the entry as reverted if it should not exist:
supabase migration repair --status reverted <version> --db-url "$SUPABASE_DB_URL"

# For each local file not on the remote:
#   Either push it with the deploy workflow, or remove it from the repository.
```

#### Safety constraints

- This workflow **never** runs `supabase db push`, `DROP`, `TRUNCATE`, or any
  SQL that modifies production data.
- It **never** commits the connection string, password, or any secret.
- It **never** overwrites or deletes existing migration files.
- It is **idempotent**: repeated runs with no additional dashboard changes will
  not create empty migrations or duplicate commits.
- Concurrent executions are serialised by a dedicated concurrency group
---

### 3. Encrypted database backups (`backup-database.yml`)

Creates a complete, self-contained snapshot of the remote PostgreSQL database
(**schema + all row data**), encrypts it with AES-256 using your secret key,
and stores it as a downloadable GitHub Actions artifact (retained for 90 days).

| Trigger | Schedule (Weekly every Sunday at 02:00 UTC) **or** Manual (`workflow_dispatch`) |
|---|---|
| Secret | `SUPABASE_DB_URL`, `BACKUP_ENCRYPTION_KEY` |
| Encryption | AES-256 symmetric cipher via `gpg` |
| Output | `supabase_backup_<YYYYMMDD_HHMMSS>.sql.gpg` |
| Retention | 90 days (GitHub Actions Artifact) |

#### Setting up the encryption secret

1. Go to: **Repository > Settings > Secrets and variables > Actions > New repository secret**
2. Name: `BACKUP_ENCRYPTION_KEY`
3. Value: *A strong password of your choice*

> When triggered manually, you can optionally supply an override password in the workflow inputs. For automated weekly runs, the `BACKUP_ENCRYPTION_KEY` secret is used.

#### How to download and restore the backup

1. In GitHub, go to **Actions > Backup database > (latest run) > Artifacts**.
2. Download the artifact (e.g. `encrypted-database-backup-20261019_020000.zip`).
3. Unzip the file to find `supabase_backup_<timestamp>.sql.gpg`.

**Step 1 — Decrypt the SQL using your password:**
```bash
gpg --decrypt supabase_backup_<timestamp>.sql.gpg > rebuild.sql
```

**Step 2 — Restore the database:**

- **Option A (Supabase Dashboard / SQL Editor)**: Open `rebuild.sql`, copy all text, paste it into the SQL Editor of any Supabase project, and click **Run**.
- **Option B (Terminal to any PostgreSQL database)**:
  ```bash
  psql "<YOUR_TARGET_DATABASE_URL>" < rebuild.sql
  ```
- **Option C (Local Docker PostgreSQL)**:
  ```bash
  docker run --name test-db -e POSTGRES_PASSWORD=postgres -p 5432:5432 -d postgres:17
  psql "postgresql://postgres:postgres@localhost:5432/postgres" < rebuild.sql
  ```

---

## Local development

Local Supabase development requires Docker. The capture workflow also requires
Docker on the runner (Ubuntu GitHub-hosted runners include it by default). Your
local Arch Linux development machine is not affected — the workflow runs only in
GitHub Actions.

```bash
# Start the local Supabase stack
supabase start

# Apply migrations to the local database
supabase db push

# Check migration state against the remote
supabase migration list --db-url "$SUPABASE_DB_URL"
```

---

## Migration naming convention

```
supabase/migrations/<YYYYMMDDHHMMSS>_<snake_case_description>.sql
```

Example: `20261019000000_initial.sql`

Timestamps are UTC and must be 14 digits. The Supabase CLI generates the
timestamp automatically when you run `supabase db pull` or
`supabase migration new`.
