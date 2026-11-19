"""Load curb zones and curb policies from curb_data_input/ into the database.

Inputs (defaults are in curb_data_input/):
  * a zones CSV exported from `vw_curb_zones` (one row per zone, with
    `curb_policy_ids` as a Postgres array literal such as `{id1,id2}`)
  * a policies JSON exported from `vw_curb_policies` (a list of policies whose
    `rules`, `time_spans`, `rates` and `policy_color` hold JSON, possibly as strings)

These are split into the tables defined in sql/init_db.sql:
curb_zones, curb_policies, curb_zone_policies, curb_policy_rules,
curb_policy_time_spans (plus curb_policy_rates / curb_policy_colors if the
input has any; the current input has none).

Usage:
    uv run python scripts/load_curb_data.py                  # truncate + reload DB
    uv run python scripts/load_curb_data.py --mode upsert    # upsert on primary keys
    uv run python scripts/load_curb_data.py --csv            # write table CSVs only
    uv run python scripts/load_curb_data.py --db --csv       # both

DB settings come from DB_USER, DB_PASS, DB_HOST, DB_NAME and DB_SCHEMA (default
public_cds), read from the environment or .env, like main.py. `--schema` overrides DB_SCHEMA.
"""

import argparse
import csv
import io
import json
import os
import sys
from pathlib import Path

import psycopg2
from dotenv import load_dotenv
from psycopg2 import sql

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_INPUT_DIR = ROOT / "curb_data_input"

# Column order matches sql/init_db.sql. Keys are the tables' primary keys.
TABLES = {
    "curb_zones": {
        "columns": [
            "curb_zone_id",
            "geometry",
            "published_date",
            "last_updated_date",
            "start_date",
            "end_date",
            "name",
            "description",
            "jurisdiction_type",
            "owner_name",
            "user_zone_id",
            "street_name",
            "address_number",
            "cross_street_start_name",
            "length",
            "available",
            "available_space_lengths",
            "availability_time",
            "width",
            "parking_angle",
            "num_spaces",
            "street_side",
            "median",
            "entire_roadway",
        ],
        "key": ["curb_zone_id"],
    },
    "curb_policy_colors": {
        "columns": [
            "color_id",
            "primary_color",
            "primary_pattern_type",
            "primary_border_color",
            "primary_border_pattern_type",
            "secondary_color",
            "secondary_border_color",
            "secondary_border_pattern_type",
        ],
        "key": ["color_id"],
    },
    "curb_policies": {
        "columns": [
            "curb_policy_id",
            "name",
            "description",
            "published_date",
            "priority",
            "policy_color_id",
        ],
        "key": ["curb_policy_id"],
    },
    "curb_zone_policies": {
        "columns": ["curb_zone_id", "curb_policy_id"],
        "key": ["curb_zone_id", "curb_policy_id"],
    },
    "curb_policy_rules": {
        "columns": [
            "rule_id",
            "curb_policy_id",
            "name",
            "description",
            "activity",
            "max_stay",
            "max_stay_unit",
            "no_return",
            "no_return_unit",
            "user_classes",
            "user_classes_except",
            "purposes",
        ],
        "key": ["rule_id"],
    },
    "curb_policy_time_spans": {
        "columns": [
            "time_span_id",
            "curb_policy_id",
            "start_date",
            "end_date",
            "days_of_week",
            "days_of_month",
            "weeks_of_month",
            "months",
            "time_of_day_start",
            "time_of_day_end",
            "designated_period",
            "designated_period_except",
        ],
        "key": ["time_span_id"],
    },
    "curb_policy_rates": {
        "columns": [
            "rate_id",
            "curb_policy_id",
            "rate",
            "rate_unit",
            "rate_unit_period",
            "increment_duration",
            "increment_amount",
            "start_duration",
            "end_duration",
            "max_fee",
        ],
        "key": ["rate_id"],
    },
}

# Parents before children, so foreign keys are satisfied while loading.
LOAD_ORDER = [
    "curb_zones",
    "curb_policy_colors",
    "curb_policies",
    "curb_zone_policies",
    "curb_policy_rules",
    "curb_policy_time_spans",
    "curb_policy_rates",
]
# Tables that must be emptied together with curb_policies (FK references).
# curb_policy_colors is left alone: policies point at colors, not the reverse.
TRUNCATE_TABLES = [t for t in LOAD_ORDER if t != "curb_policy_colors"]


def pg_array(values):
    """Format a list as a Postgres array literal, e.g. ['a b', 'c'] -> {"a b","c"}."""
    if values is None:
        return None
    items = []
    for v in values:
        if v is None:
            items.append("NULL")
        elif isinstance(v, bool):
            items.append("true" if v else "false")
        elif isinstance(v, (int, float)):
            items.append(str(v))
        else:
            escaped = str(v).replace("\\", "\\\\").replace('"', '\\"')
            items.append(f'"{escaped}"')
    return "{" + ",".join(items) + "}"


def parse_pg_array(text):
    """Parse the simple `{a,b}` UUID arrays found in `curb_policy_ids`."""
    text = (text or "").strip()
    if not text or text == "{}":
        return []
    return [x.strip().strip('"') for x in text.strip("{}").split(",") if x.strip()]


def as_json(value):
    """JSON columns may arrive as already-parsed values or as JSON strings."""
    if isinstance(value, str):
        value = value.strip()
        return json.loads(value) if value else None
    return value


def cell(value):
    """Convert a Python value to its CSV/COPY text form (None -> empty -> NULL)."""
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (list, tuple)):
        return pg_array(value)
    return str(value)


def build_tables(zones_path, policies_path):
    """Return {table: [row dict, ...]} for every table, validating references."""
    tables = {name: [] for name in TABLES}

    csv.field_size_limit(sys.maxsize)
    zone_cols = TABLES["curb_zones"]["columns"]
    with open(zones_path, newline="") as f:
        for rec in csv.DictReader(f):
            tables["curb_zones"].append({c: rec.get(c, "") for c in zone_cols})
            for policy_id in parse_pg_array(rec.get("curb_policy_ids")):
                tables["curb_zone_policies"].append(
                    {
                        "curb_zone_id": rec["curb_zone_id"],
                        "curb_policy_id": policy_id,
                    }
                )

    with open(policies_path) as f:
        policies = json.load(f)

    for p in policies:
        color = as_json(p.get("policy_color"))
        color_id = None
        if color:
            color_id = color["color_id"]
            tables["curb_policy_colors"].append(
                {c: color.get(c) for c in TABLES["curb_policy_colors"]["columns"]}
            )
        tables["curb_policies"].append(
            {
                "curb_policy_id": p["curb_policy_id"],
                "name": p.get("name"),
                "description": p.get("description"),
                "published_date": p.get("published_date"),
                "priority": p.get("priority"),
                "policy_color_id": color_id,
            }
        )
        for table, key in (
            ("curb_policy_rules", "rules"),
            ("curb_policy_time_spans", "time_spans"),
            ("curb_policy_rates", "rates"),
        ):
            for child in as_json(p.get(key)) or []:
                row = {c: child.get(c) for c in TABLES[table]["columns"]}
                row["curb_policy_id"] = p["curb_policy_id"]
                tables[table].append(row)

    # Several policies can share one color row.
    seen, colors = set(), []
    for row in tables["curb_policy_colors"]:
        if row["color_id"] not in seen:
            seen.add(row["color_id"])
            colors.append(row)
    tables["curb_policy_colors"] = colors

    # Fail early on dangling references or duplicate keys instead of mid-load.
    zone_ids = {r["curb_zone_id"] for r in tables["curb_zones"]}
    policy_ids = {r["curb_policy_id"] for r in tables["curb_policies"]}
    for r in tables["curb_zone_policies"]:
        if r["curb_zone_id"] not in zone_ids or r["curb_policy_id"] not in policy_ids:
            raise ValueError(f"Dangling zone/policy reference: {r}")
    for name, spec in TABLES.items():
        keys = [tuple(r[k] for k in spec["key"]) for r in tables[name]]
        if len(keys) != len(set(keys)):
            raise ValueError(f"Duplicate primary keys in {name}")
    return tables


def render_csv(columns, rows, out):
    writer = csv.writer(out, lineterminator="\n")
    writer.writerow(columns)
    for row in rows:
        writer.writerow([cell(row[c]) for c in columns])


def write_csvs(tables, out_dir):
    out_dir.mkdir(parents=True, exist_ok=True)
    for name in LOAD_ORDER:
        rows = tables[name]
        if not rows:
            continue  # nothing generated (e.g. rates/colors in the current input)
        path = out_dir / f"{name}.csv"
        with open(path, "w", newline="") as f:
            render_csv(TABLES[name]["columns"], rows, f)
        print(f"Wrote {len(rows):>7} rows to {path}")


def connect():
    load_dotenv()
    return psycopg2.connect(
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASS"],
        host=os.environ["DB_HOST"],
        dbname=os.environ["DB_NAME"],
    )


def copy_rows(cur, target, columns, rows):
    """COPY rows into `target` (a table or temp table) via an in-memory CSV."""
    buf = io.StringIO()
    render_csv(columns, rows, buf)
    buf.seek(0)
    cur.copy_expert(
        sql.SQL("COPY {} ({}) FROM STDIN WITH (FORMAT csv, HEADER true)")
        .format(
            sql.Identifier(target),
            sql.SQL(", ").join(map(sql.Identifier, columns)),
        )
        .as_string(cur),
        buf,
    )


def load_db(tables, mode, schema):
    """Load all tables in one transaction; any error rolls everything back."""
    conn = connect()
    try:
        with conn, conn.cursor() as cur:
            cur.execute(
                "SELECT 1 FROM information_schema.schemata WHERE schema_name = %s",
                (schema,),
            )
            if cur.fetchone() is None:
                raise SystemExit(
                    f"Schema {schema!r} does not exist. Create it and run sql/init_db.sql "
                    "inside it first (SET search_path = <schema>, public)."
                )
            # Unqualified table names resolve to `schema`; public stays for PostGIS.
            cur.execute(
                sql.SQL("SET LOCAL search_path TO {}, public").format(
                    sql.Identifier(schema)
                )
            )
            if mode == "truncate":
                cur.execute(
                    sql.SQL("TRUNCATE {}").format(
                        sql.SQL(", ").join(map(sql.Identifier, TRUNCATE_TABLES))
                    )
                )
                print(f"Truncated: {', '.join(TRUNCATE_TABLES)}")

            for name in LOAD_ORDER:
                rows = tables[name]
                if not rows:
                    continue
                spec = TABLES[name]
                cols = spec["columns"]
                if mode == "truncate":
                    copy_rows(cur, name, cols, rows)
                else:
                    stage = f"stg_{name}"
                    cur.execute(
                        sql.SQL(
                            "CREATE TEMP TABLE {} (LIKE {} INCLUDING DEFAULTS) ON COMMIT DROP"
                        ).format(sql.Identifier(stage), sql.Identifier(name))
                    )
                    copy_rows(cur, stage, cols, rows)
                    updates = [c for c in cols if c not in spec["key"]]
                    action = (
                        sql.SQL("DO UPDATE SET {}").format(
                            sql.SQL(", ").join(
                                sql.SQL("{0} = EXCLUDED.{0}").format(sql.Identifier(c))
                                for c in updates
                            )
                        )
                        if updates
                        else sql.SQL("DO NOTHING")
                    )
                    cur.execute(
                        sql.SQL(
                            "INSERT INTO {} ({}) SELECT {} FROM {} ON CONFLICT ({}) {}"
                        ).format(
                            sql.Identifier(name),
                            sql.SQL(", ").join(map(sql.Identifier, cols)),
                            sql.SQL(", ").join(map(sql.Identifier, cols)),
                            sql.Identifier(stage),
                            sql.SQL(", ").join(map(sql.Identifier, spec["key"])),
                            action,
                        )
                    )
                print(f"Loaded {len(rows):>7} rows into {name} ({mode})")
    finally:
        conn.close()


def main():
    load_dotenv()  # so DB_SCHEMA from .env is the --schema default
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--input-dir", type=Path, default=DEFAULT_INPUT_DIR)
    parser.add_argument(
        "--zones",
        type=Path,
        help="zones CSV (default: <input-dir>/street_cleaning_curb_zones.csv)",
    )
    parser.add_argument(
        "--policies",
        type=Path,
        help="policies JSON (default: <input-dir>/street_cleaning_curb_policies.json)",
    )
    parser.add_argument("--db", action="store_true", help="insert into the database")
    parser.add_argument("--csv", action="store_true", help="write one CSV per table")
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="where --csv writes files (default: the input dir)",
    )
    parser.add_argument(
        "--mode",
        choices=["truncate", "upsert"],
        default="truncate",
        help="truncate: empty the tables first (default); upsert: ON CONFLICT DO UPDATE on primary keys",
    )
    parser.add_argument(
        "--schema",
        default=os.environ.get("DB_SCHEMA", "public_cds"),
        help="target schema (default: $DB_SCHEMA, else public_cds)",
    )
    args = parser.parse_args()

    # With neither flag, behave as --db.
    do_db = args.db or not args.csv
    zones = args.zones or args.input_dir / "street_cleaning_curb_zones.csv"
    policies = args.policies or args.input_dir / "street_cleaning_curb_policies.json"

    tables = build_tables(zones, policies)
    for name in LOAD_ORDER:
        print(f"{name:<24} {len(tables[name]):>7} rows")

    if args.csv:
        write_csvs(tables, args.output_dir or args.input_dir)
    if do_db:
        load_db(tables, args.mode, args.schema)


if __name__ == "__main__":
    main()
