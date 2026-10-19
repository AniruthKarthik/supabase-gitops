# Database Schema Documentation

> Auto-generated from database schema on `2026-10-19 13:14:39 UTC`.

## Entity Relationship Diagram

```mermaid
erDiagram
    profiles {
        uuid id PK
        text username
        text full_name
        text avatar_url
        text website
        timestamp_with_time_zone created_at
        timestamp_with_time_zone updated_at
    }
```

---

## Tables Directory

### `profiles`

| Column | Type | Nullable | Default | Key |
|---|---|---|---|---|
| `id` | `uuid` | NO | `gen_random_uuid()` | PRIMARY KEY |
| `username` | `text` | YES | - | - |
| `full_name` | `text` | YES | - | - |
| `avatar_url` | `text` | YES | - | - |
| `website` | `text` | YES | - | - |
| `created_at` | `timestamp with time zone` | NO | `now()` | - |
| `updated_at` | `timestamp with time zone` | NO | `now()` | - |

