#!/usr/bin/env python3
import sys
import subprocess
from datetime import datetime, timezone

def run_query(target, query, is_docker=True):
    if is_docker:
        cmd = ["docker", "exec", "-i", target, "psql", "-U", "postgres", "-d", "postgres", "-At"]
    else:
        cmd = ["psql", target, "--no-psqlrc", "-At"]
    
    res = subprocess.run(cmd, input=query, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"Database query failed: {res.stderr.strip()}", file=sys.stderr)
        sys.exit(1)
    
    return [line.split("|") for line in res.stdout.strip().split("\n") if line.strip()]

def build_schema_documentation(target, is_docker=True):
    q_tables = "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE' ORDER BY table_name;"
    table_rows = run_query(target, q_tables, is_docker)
    tables = [r[0] for r in table_rows if r and r[0]]
    if not tables:
        print("Error: Schema introspection found zero public tables. Database is uninitialized or introspection failed.", file=sys.stderr)
        sys.exit(1)

    q_cols = """
    SELECT table_name, column_name, data_type, is_nullable, COALESCE(column_default, '')
    FROM information_schema.columns
    WHERE table_schema = 'public'
    ORDER BY table_name, ordinal_position;
    """
    col_rows = run_query(target, q_cols, is_docker)
    
    q_pks = """
    SELECT kcu.table_name, kcu.column_name
    FROM information_schema.table_constraints tc
    JOIN information_schema.key_column_usage kcu
      ON tc.constraint_name = kcu.constraint_name AND tc.table_schema = kcu.table_schema
    WHERE tc.constraint_type = 'PRIMARY KEY' AND tc.table_schema = 'public';
    """
    pk_rows = run_query(target, q_pks, is_docker)
    pks = set((r[0], r[1]) for r in pk_rows if len(r) >= 2)

    q_fks = """
    SELECT tc.table_name, kcu.column_name, ccu.table_name, ccu.column_name
    FROM information_schema.table_constraints tc
    JOIN information_schema.key_column_usage kcu
      ON tc.constraint_name = kcu.constraint_name AND tc.table_schema = kcu.table_schema
    JOIN information_schema.constraint_column_usage ccu
      ON ccu.constraint_name = tc.constraint_name AND ccu.table_schema = tc.table_schema
    WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_schema = 'public';
    """
    fk_rows = run_query(target, q_fks, is_docker)

    columns_by_table = {}
    for r in col_rows:
        if len(r) >= 5:
            tname, cname, dtype, nullable, default_val = r[0], r[1], r[2], r[3], r[4]
            columns_by_table.setdefault(tname, []).append({
                "name": cname,
                "type": dtype,
                "nullable": nullable,
                "default": default_val,
                "is_pk": (tname, cname) in pks
            })

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    lines = []
    lines.append("# Database Schema Documentation")
    lines.append("")
    lines.append(f"> Auto-generated from database schema on `{now}`.")
    lines.append("")
    lines.append("## Entity Relationship Diagram")
    lines.append("")
    lines.append("```mermaid")
    lines.append("erDiagram")

    for fk in fk_rows:
        if len(fk) >= 4:
            lines.append(f"    {fk[2]} ||--o{{ {fk[0]} : \"references ({fk[1]})\"")

    for tname in tables:
        lines.append(f"    {tname} {{")
        for col in columns_by_table.get(tname, []):
            clean_type = col["type"].replace(" ", "_")
            pk_mark = " PK" if col["is_pk"] else ""
            lines.append(f"        {clean_type} {col['name']}{pk_mark}")
        lines.append("    }")
    lines.append("```")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Tables Directory")
    lines.append("")

    for tname in tables:
        lines.append(f"### `{tname}`")
        lines.append("")
        lines.append("| Column | Type | Nullable | Default | Key |")
        lines.append("|---|---|---|---|---|")
        for col in columns_by_table.get(tname, []):
            c_name = f"`{col['name']}`"
            c_type = f"`{col['type']}`"
            nullable_str = "YES" if col["nullable"] == "YES" else "NO"
            default_str = f"`{col['default']}`" if col["default"] else "-"
            key_str = "PRIMARY KEY" if col["is_pk"] else "-"
            lines.append(f"| {c_name} | {c_type} | {nullable_str} | {default_str} | {key_str} |")
        lines.append("")

    return "\n".join(lines)

def main():
    target = sys.argv[1] if len(sys.argv) > 1 else "pg-doc-target"
    out_file = sys.argv[2] if len(sys.argv) > 2 else "docs/schema.md"
    is_docker = not (target.startswith("postgres://") or target.startswith("postgresql://"))

    doc = build_schema_documentation(target, is_docker=is_docker)
    with open(out_file, "w") as f:
        f.write(doc + "\n")
    print(f"Generated {out_file} successfully.")

if __name__ == "__main__":
    main()
