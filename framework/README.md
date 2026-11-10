# dbintel

`dbintel` assesses an existing database and writes a report: findings, health scores, and proposed fixes as SQL files. It reads the database. It never changes it.

## Quick start

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -e ".[all,dev]"
.venv\Scripts\python -m dbintel assess samples\erp_mysql.sql --profile samples\profiles\erp.yaml --out reports\erp
```

Open `reports\erp\report.html` in a browser. The report works offline. Generated SQL is in `reports\erp\migrations`.

Or use the local web interface:

```powershell
ui.bat
```

It opens in your browser and runs only on this computer. See [docs/UI_GUIDE.md](docs/UI_GUIDE.md).

Assess a live database:

```powershell
$env:DB_PASSWORD = "..."
.venv\Scripts\python -m dbintel assess "postgresql://user@host/dbname" --password-env DB_PASSWORD --out reports\live
```

## What it can read

| Source | Example |
|---|---|
| PostgreSQL, MySQL, SQLite (live, read-only) | `postgresql://user@host/db` |
| SQL dumps | `dump.sql` (mysqldump, pg_dump, SQLite) |
| CSV folders, CSV files, Excel | `samples\csv`, `book.xlsx` |
| JSON metadata | `metadata.json` |
| Query logs and pipeline manifests | `--query-log`, `--pipelines` |

## Commands

| Command | Purpose |
|---|---|
| `assess SOURCE --out DIR` | Run the assessment and write reports |
| `rules list`, `rules show ID` | Inspect the rule catalog |
| `standards coverage` | How many standards have a rule |
| `migrate test SOURCE --approve HASH` | Test the plan in a sandbox |
| `init-profile FILE` | Write a starter profile |
| `ui [--port 8765] [--no-open]` | Open the local web interface |

`assess` prints a plan hash. `migrate test` will not run without that exact hash. No command applies a migration to a source database.

See [docs/USER_GUIDE.md](docs/USER_GUIDE.md), [docs/UI_GUIDE.md](docs/UI_GUIDE.md), [docs/INSTALL.md](docs/INSTALL.md), [docs/CONFIGURATION.md](docs/CONFIGURATION.md), [docs/RULES.md](docs/RULES.md), [docs/LIMITATIONS.md](docs/LIMITATIONS.md) and [PROGRESS.md](PROGRESS.md).
