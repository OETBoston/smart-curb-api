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
