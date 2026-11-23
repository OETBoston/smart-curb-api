# City of Boston Curbs API

This repository contains the City of Boston Curbs API: a read-only API that provides curb zones and curb policies for the City of Boston, following the [Curb Data Specification (CDS)](https://github.com/openmobilityfoundation/curb-data-specification) Curbs API (v1.1). The API is built with FastAPI and backed by a PostgreSQL/PostGIS database.

Published documentation: <https://cds-curb-api.boston.gov>

The repository includes:

- `main.py` and `models.py`: the FastAPI application and its response models.
- `sql/init_db.sql`: a script that initializes the database tables and views.
- A [reduced and annotated copy of the API docs](docs//reference/cds.md) indicating what is implemented
- [Database specification](docs/CURBS_database.md) and [specification of views](docs/CURBS_views.md).
- `docs/` and `mkdocs.yml`: source for the documentation site (MkDocs).
- `scripts/`: helper scripts to export the OpenAPI spec and to load data.
- `test-data/`: handwritten test data designed for initial API development and testing (not necessarily representative of on-ground conditions).

## 1. Initial setup

Requirements: Python 3.13 (see `.python-version`), [uv](https://docs.astral.sh/uv/), and PostgreSQL with the PostGIS extension.

1. Create your environment file from the example:

   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and set the database connection values:

   | Variable    | Description                                                     |
   | ----------- | --------------------------------------------------------------- |
   | `DB_HOST`   | Database host (e.g. `localhost`)                                |
   | `DB_NAME`   | Database name (e.g. `smart_curb_db`)                            |
   | `DB_SCHEMA` | Schema holding the API views (defaults to `public_cds`)         |
   | `DB_USER`   | Database user                                                   |
   | `DB_PASS`   | Database password                                               |

3. Install dependencies with uv:

   ```bash
   uv sync
   ```

   To also install the tools used to build the documentation, run `uv sync --group docs`.

## 2. Database setup

The database and view specification can be used to initialize a new PostgreSQL database suitable for population with the test data. Brief instructions on creating a database follow.

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

## 3. Generating the documentation

The documentation site is built with MkDocs from the `docs/` folder and the API's OpenAPI spec. The generated `docs/openapi.json` and `site/` folder are git-ignored.

```bash
uv sync --group docs
uv run python scripts/export_openapi.py   # writes docs/openapi.json (no database needed)
uv run mkdocs build --strict              # builds the site into ./site
```

To preview the docs with live reload while editing, run `uv run mkdocs serve` (after exporting the OpenAPI spec).

## 4. Running the API

```bash
uv run fastapi dev main.py
```

The API is then available at <http://127.0.0.1:8000>:

| Path                         | Description                                                                          |
| ---------------------------- | ------------------------------------------------------------------------------------ |
| `/documentation`             | The documentation site. Only available if you built it (`site/` exists). `/` redirects here. |
| `/docs`                      | Interactive Swagger UI generated by FastAPI                                          |
| `/v1/curbs/zones`            | Curb zones                                                                           |
| `/v1/curbs/policies`         | Curb policies                                                                        |

Example:

```bash
curl "http://127.0.0.1:8000/v1/curbs/zones?min_lng=-71.0524&min_lat=42.3395&max_lng=-71.0470&max_lat=42.3416&include_geometry=false"
```

### Deployment

- The `Procfile` starts the app with `uvicorn main:app`.
- `cloudbuild.yaml` builds the docs site, builds the container image, and verifies the docs are included in the image.
- Set `REQUIRE_DOCS=1` in deployed environments so that a build without the docs site fails to start instead of silently omitting the docs.
- Pull requests run `.github/workflows/docs.yml`, which builds the docs with `mkdocs build --strict`.

## 5. Loading CDS data (optional)

`scripts/load_curb_data.py` is an additional script to load curb zones and policies into the database when CDS data is available in the required format. It reads two files from `curb_data_input/`:

- `street_cleaning_curb_zones.csv`: zones CSV exported from `vw_curb_zones`, one row per zone, with `curb_policy_ids` as a Postgres array literal such as `{id1,id2}`.
- `street_cleaning_curb_policies.json`: policies JSON exported from `vw_curb_policies`, a list of policies whose `rules`, `time_spans`, `rates` and `policy_color` hold JSON.

The data is split into the tables defined in `sql/init_db.sql`. The script uses the same `DB_*` settings as the API (from the environment or `.env`).

```bash
uv run python scripts/load_curb_data.py                  # truncate tables and reload the database
uv run python scripts/load_curb_data.py --mode upsert    # upsert on primary keys instead
uv run python scripts/load_curb_data.py --csv            # only write one CSV per table
uv run python scripts/load_curb_data.py --db --csv       # load the database and write CSVs
```

Other options: `--input-dir`, `--zones`, `--policies`, `--output-dir` and `--schema` (defaults to `DB_SCHEMA`). Run with `--help` for details.
