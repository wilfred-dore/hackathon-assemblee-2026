"""Introspecte les schémas legifrance + assemblee de Canutes et génère :
  - docs/schema/canutes_schema.json  (machine-readable, agent-friendly)
  - docs/schema/canutes.dbml         (rendu sur https://dbdiagram.io)

Lancer :  MODE=live uv run python tools/gen_schema.py
(nécessite l'extra db : `uv sync --extra db` + CANUTES_DB_* dans .env)
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import psycopg  # noqa: E402

from src.config import CONFIG  # noqa: E402

SCHEMAS = ("legifrance", "assemblee")
OUT = "docs/schema"
GEN_DATE = "2026-07-03"


def main() -> None:
    dsn = (
        f"host={CONFIG.canutes_db_host} port={CONFIG.canutes_db_port} "
        f"user={CONFIG.canutes_db_user} password={CONFIG.canutes_db_password} "
        f"dbname={CONFIG.canutes_db_name} connect_timeout=20"
    )
    with psycopg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute(
            "select table_schema, table_name, table_type from information_schema.tables "
            "where table_schema = any(%s) order by 1,2", (list(SCHEMAS),),
        )
        tables = {(s, t): {"is_view": ty == "VIEW", "columns": [], "pk": [], "fks": []}
                  for s, t, ty in cur.fetchall()}

        cur.execute(
            "select table_schema, table_name, column_name, data_type, is_nullable "
            "from information_schema.columns where table_schema = any(%s) "
            "order by table_schema, table_name, ordinal_position", (list(SCHEMAS),),
        )
        for s, t, col, typ, nullable in cur.fetchall():
            if (s, t) in tables:
                tables[(s, t)]["columns"].append({"name": col, "type": typ, "nullable": nullable == "YES"})

        for ctype, key in (("PRIMARY KEY", "pk"),):
            cur.execute(
                "select tc.table_schema, tc.table_name, kcu.column_name "
                "from information_schema.table_constraints tc "
                "join information_schema.key_column_usage kcu "
                "  on tc.constraint_name=kcu.constraint_name and tc.table_schema=kcu.table_schema "
                "where tc.constraint_type=%s and tc.table_schema = any(%s)", (ctype, list(SCHEMAS)),
            )
            for s, t, col in cur.fetchall():
                if (s, t) in tables:
                    tables[(s, t)][key].append(col)

        cur.execute(
            "select tc.table_schema, tc.table_name, kcu.column_name, "
            "  ccu.table_schema, ccu.table_name, ccu.column_name "
            "from information_schema.table_constraints tc "
            "join information_schema.key_column_usage kcu "
            "  on tc.constraint_name=kcu.constraint_name and tc.table_schema=kcu.table_schema "
            "join information_schema.constraint_column_usage ccu "
            "  on ccu.constraint_name=tc.constraint_name and ccu.table_schema=tc.table_schema "
            "where tc.constraint_type='FOREIGN KEY' and tc.table_schema = any(%s)", (list(SCHEMAS),),
        )
        for s, t, col, fs, ft, fcol in cur.fetchall():
            if (s, t) in tables:
                tables[(s, t)]["fks"].append({"column": col, "ref_table": f"{fs}.{ft}", "ref_column": fcol})

    os.makedirs(OUT, exist_ok=True)
    with open(f"{OUT}/canutes_schema.json", "w") as f:
        json.dump({f"{s}.{t}": v for (s, t), v in tables.items()}, f, ensure_ascii=False, indent=2)

    lines = [
        f"// Canutes — schémas {', '.join(SCHEMAS)} (introspecté {GEN_DATE})",
        "// Rendu : coller sur https://dbdiagram.io. NB: aucune FK déclarée en base",
        "// (relations implicites -> voir docs/schema/README.md).",
        "",
    ]
    for (s, t), v in tables.items():
        lines.append(f"Table {s}.{t} {{" + ("  // VIEW" if v["is_view"] else ""))
        for c in v["columns"]:
            attrs = [a for a, ok in (("pk", c["name"] in v["pk"]), ("not null", not c["nullable"])) if ok]
            lines.append(f'  "{c["name"]}" {c["type"].replace(" ", "_")}' + (f" [{', '.join(attrs)}]" if attrs else ""))
        lines += ["}", ""]
    for (s, t), v in tables.items():
        for fk in v["fks"]:
            lines.append(f'Ref: {s}.{t}."{fk["column"]}" > {fk["ref_table"]}."{fk["ref_column"]}"')
    with open(f"{OUT}/canutes.dbml", "w") as f:
        f.write("\n".join(lines) + "\n")

    nv = sum(1 for v in tables.values() if v["is_view"])
    nfk = sum(len(v["fks"]) for v in tables.values())
    print(f"tables={len(tables)} (vues={nv}) | colonnes={sum(len(v['columns']) for v in tables.values())} | FK={nfk}")
    print(f"écrit: {OUT}/canutes_schema.json, {OUT}/canutes.dbml")


if __name__ == "__main__":
    main()
