# smart-curb-api

An API that will provide access to curb data according to the Curb Data Specification (CDS)

The repository currently includes:

- A [reduced and annotated copy of the API docs](docs/CURBS.md) indicating what is implemented.
- A [database specification](docs/CURBS_database.md).
- [Specification of views](docs/CURBS_views.md) contained in the database.
- A SQL script that will initialize the specified database and views.
- Handwritten test data designed for initial API development and testing (not necessarily representative of on-ground conditions)

## Database Setup

That database and view specification can be used to initialize a new PostgreSQL database suitable for population with the test data. Brief instructions on creating a database follow.

These instructions assume that you have installed PostgreSQL, including the PostGIS extension, and can operate on the database from the command line. Instructions assume use of `sudo` to operate on the database as user `postgres`, but the approach can be adopted for different situations.

Start by creating a database named `smart_curb_db`. This can be accomplished with:

```bash
$ sudo -u postgres createdb smart_curb_db
```

Next, run `sql/init_db.sql` on this new database.

```bash
sudo -u postgres psql -d smart_curb_db -f sql/init_db.sql
```

Finally, import test data into the database. The shell script `scripts/load_data.sh` provides a sample approach. You can either run the script as-is, make edits for your database situation, or enter similar commands to load data.

### Some tips for connecting via a command line:

To connect to psql, use:

```bash
psql -U my-username -d cds -h localhost -p 5432
```

And modify parameters as needed. You will likely be prompted for a password.

From the `psql` prompt, you can set a schema (for example, public_cds) and then run a SQL script with the following:

```psql
SET search_path = public_cds, public;
\i init_db.sql;
```

The path must also include `public` so psql knows where to find the PostGIS extension.

After creating the tables and views, you can load data from CSV, or by other means. If loading from CSV, you can run commands like:

```psql
\copy table_name from '../test-data/table_name.csv' WITH (FORMAT csv, HEADER true);
```

### Process to update public_cds

1. Create a new schema named `public_cds_next`.
2. Load data into the new schema, verify that it is valid.
3. Swap schema names and add user permissions in one transaction with:

```sql
BEGIN;
DROP SCHEMA IF EXISTS public_cds_previous;
ALTER SCHEMA public_cds RENAME TO public_cds_previous;
ALTER SCHEMA public_cds_next RENAME TO public_cds;

GRANT USAGE ON SCHEMA public_cds TO "cds-api";
GRANT SELECT ON ALL TABLES IN SCHEMA public_cds TO "cds-api";

ALTER DEFAULT PRIVILEGES IN SCHEMA public_cds
GRANT SELECT ON TABLES TO "cds-api";

COMMIT;
```


## Schema Selection (Dev Only)

Endpoints accept an optional `schema` query parameter (e.g. `?schema=chinatown_cds`) that
directs queries at a specific Postgres schema instead of the default `public_cds` (citywide)
data. This exists to support in-progress, neighborhood-by-neighborhood data cleanup —
each neighborhood's provisional data lives in its own schema until it's validated and
merged back into `public_cds` (see "Process to update public_cds" above).

**This is disabled by default and must never be enabled on the public production service.**
It is gated behind the `ALLOW_SCHEMA_OVERRIDE` environment variable, which must be set to
exactly `"true"` for the override to take effect. If the variable is unset, missing, or set
to anything else, all requests are served from `public_cds` regardless of what `schema`
value is passed — this is a deliberate fail-safe default, not just a default value.

- **Production (`smart-curb-api`)**: `ALLOW_SCHEMA_OVERRIDE` must not be set.
- **Dev (`smart-curb-api-dev`)**: `ALLOW_SCHEMA_OVERRIDE=true`.

Valid schema names are maintained in the `ALLOWED_SCHEMAS` set in `main.py` and updated as neighborhoods enter and complete the cleanup process.
