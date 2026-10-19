#!/usr/bin/env python3
import sys
import json
import subprocess
from datetime import datetime, timezone

def fetch_schema_json(container_name_or_url, is_docker=True):
    query = """
    SELECT json_build_object(
      'tables', COALESCE((
        SELECT json_agg(json_build_object(
          'table_name', t.table_name,
          'columns', COALESCE((
            SELECT json_agg(json_build_object(
              'column_name', c.column_name,
              'data_type', c.data_type,
              'is_nullable', c.is_nullable,
              'column_default', c.column_default,
              'is_primary', EXISTS (
                SELECT 1 FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                  ON tc.constraint_name = kcu.constraint_name
                 AND tc.table_schema = kcu.table_schema
                WHERE tc.constraint_type = 'PRIMARY KEY'
                  AND tc.table_schema = 'public'
                  AND tc.table_name = t.table_name
                  AND kcu.column_name = c.column_name
              )
            ) ORDER BY c.ordinal_position), '[]'::json)
        ) ORDER BY t.table_name), '[]'::json),
      'foreign_keys', COALESCE((
        SELECT json_agg(json_build_object(
          'from_table', tc.table_name,
          'from_column', kcu.column_name,
          'to_table', ccu.table_name,
          'to_column', ccu.column_name
        ))
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu
          ON tc.constraint_name = kcu.constraint_name
         AND tc.table_schema = kcu.table_schema
        JOIN information_schema.constraint_column_usage ccu
          ON ccu.constraint_name = tc.constraint_name
         AND ccu.table_schema = tc.table_schema
        WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_schema = 'public'
      ), '[]'::json)
    );
    """
    if is_docker:
        cmd = ["docker", "exec", container_name_or_url, "psql", "-U", "postgres", "-d", "postgres", "-At", "-c", query]
    else:
        cmd = ["psql", container_name_or_url, "--no-psqlrc", "-At", "-c", query]
    
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return json.loads(result.stdout.strip())

def generate_markdown(schema_data):
    tables = schema_data.get("tables", [])
    fks = schema_data.get("foreign_keys", [])
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    lines = []
    lines.append("# Database Schema Documentation")
    lines.append("")
    lines.append(f"> Auto-generated from database migrations on `{now}`.")
    lines.append("")
    lines.append("## Entity Relationship Diagram")
    lines.append("")
    lines.append("```mermaid")
    lines.append("erDiagram")

    if fks:
        for fk in fks:
            lines.append(f"    {fk['to_table']} ||--o{{ {fk['from_table']} : \"has ({fk['from_column']})\"")

    for tbl in tables:
        tname = tbl["table_name"]
        lines.append(f"    {tname} {{")
        for col in tbl.get("columns", []):
            dtype = col["data_type"].replace(" ", "_")
            cname = col["column_name"]
            pk_mark = " PK" if col.get("is_primary") else ""
            lines.append(f"        {dtype} {cname}{pk_mark}")
        lines.append("    }")
    lines.append("```")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Tables")
    lines.append("")

    for tbl in tables:
        tname = tbl["table_name"]
        lines.append(f"### `{tname}`")
        lines.append("")
        lines.append("| Column | Type | Nullable | Default | Constraints |")
        lines.append("|---|---|---|---|---|")
        for col in tbl.get("columns", []):
            cname = f"`{col['column_name']}`"
            dtype = f"`{col['data_type']}`"
            nullable = "YES" if col.get("is_nullable") == "YES" else "NO"
            default_val = f"`{col['column_default']}`" if col.get("column_default") else "-"
            constraint = "PRIMARY KEY" if col.get("is_primary") else "-"
            lines.append(f"| {cname} | {dtype} | {nullable} | {default_val} | {constraint} |")
        lines.append("")

    return "\n".join(lines)

def main():
    target = sys.argv[1] if len(sys.argv) > 1 else "pg-doc-gen"
    out_file = sys.argv[2] if len(sys.argv) > 2 else "docs/schema.md"
    is_docker = not (target.startswith("postgres://") or target.startswith("postgresql://"))

    data = fetch_schema_json(target, is_docker=is_docker)
    md = generate_markdown(data)

    with open(out_file, "w") as f:
        f.write(md + "\n")
    print(f"Generated {out_file} successfully.")

if __name__ == "__main__":
    main()
