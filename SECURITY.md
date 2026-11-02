# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Security Model & Operator Requirements

### 1. Mandatory Private Repository
This repository is designed to be cloned or used as a **private template**:
- **Artifact Exposure**: The `backup-database.yml` workflow uploads encrypted SQL dumps as GitHub Actions artifacts. While encrypted with AES-256 via GPG, GitHub Actions artifacts on **public repositories** are downloadable by any logged-in GitHub user.
- **Drift Alert Issue Contents**: The `drift-alert.yml` workflow automatically creates GitHub issues when database drift is detected. On public repositories, this exposes table definitions, schema changes, and migration details.

**Always maintain your instance of this repository as Private.**

### 2. Secret Protection & Handling
- Connection strings (`SUPABASE_DB_URL`, `SUPABASE_STAGING_DB_URL`) and encryption keys (`BACKUP_ENCRYPTION_KEY`) must reside exclusively in GitHub Secrets or GitHub Environment Secrets.
- Workflows in this repository never pass passphrases through command-line arguments (avoiding process listing leaks) or environment variables directly into shells; passphrases are streamed via protected file descriptors (`--passphrase-fd 3`).
- The staging promotion pipeline (`promote-migrations.yml`) enforces strict host verification, failing closed if staging falls back to production credentials.

### 3. Pre-Migration Safeguards & Testing
- Workflows apply database migrations using `supabase db push`.
- Never connect this repository directly to a production database without verifying migrations against an ephemeral or staging database first.

## Reporting a Vulnerability

If you discover a security vulnerability within this repository, please report it privately:

1. **GitHub Security Advisory**: Open a draft security advisory via **Security > Advisories > Report a vulnerability**.
2. **Email Disclosure**: If GitHub Advisories are unavailable, contact the maintainer at `aniruthkarthik10@gmail.com`.

Please include:
- A description of the issue and potential impact
- Steps or proof-of-concept to reproduce the behavior
- Affected workflow(s) or script(s)

We will acknowledge receipt within 48 hours and work with you to remediate the vulnerability before public disclosure.
