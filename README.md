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
