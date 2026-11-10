# Install

Needs Python 3.10 or later.

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -e ".[all,dev]"
```

Extras:

| Extra | Adds |
|---|---|
| `postgres` | psycopg, for live PostgreSQL |
| `mysql` | PyMySQL, for live MySQL |
| `excel` | openpyxl, for `.xlsx` files |
| `dev` | pytest, and pgserver (a private PostgreSQL for tests) |
| `all` | postgres, mysql and excel |

Install only what you need, for example `pip install -e ".[postgres]"`. SQL dumps, CSV and SQLite need no extras.

## Check the install

```powershell
.venv\Scripts\python -m dbintel --version
.venv\Scripts\python -m pytest -q
```

The PostgreSQL tests start their own server through pgserver, in a temporary folder. They skip if pgserver or psycopg is missing. MySQL tests use a fake driver unless `DBINTEL_MYSQL_URL` is set.

`python -m dbintel` and the `dbintel` command are the same program.
