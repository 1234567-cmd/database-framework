# User guide

## Assess a database

```powershell
python -m dbintel assess SOURCE --out DIR [options]
```

Useful options:

| Option | Meaning |
|---|---|
| `--profile FILE` | Your workload, tenancy and rule settings |
| `--dialect mysql` | Dump dialect, if detection is wrong |
| `--password-env NAME` | Environment variable holding the password |
| `--query-log FILE` | Query log, to run performance rules |
| `--pipelines FILE` | Pipeline manifest, to run data engineering rules |
| `--app-source-dir DIR` | Source code to search for uses of changed tables |
| `--target-dialect postgres` | Generate SQL for another engine |
| `--format html` | Only some formats (repeatable) |
| `--fail-on high` | Exit 3 if any finding is at or above this severity |
| `--fail-kind confirmed_defect` | Limit `--fail-on` to one kind of finding |

## What is written

| Path | Contents |
|---|---|
| `report.html` | The full report. Self-contained, works offline, no external assets. |
| `report.md`, `report.json` | The same content as Markdown and JSON |
| `er\*.mmd` | Mermaid ER diagram sources, current and proposed |
| `migrations\` | Proposed SQL per step, `.up.sql` and `.down.sql`, `plan.json`, `README.md` |

Nothing is applied. Read `migrations\README.md` before using any step.

## Reading the report

- **Executive summary:** the headline numbers and top risks.
- **Health scores:** an overall score and ten categories. Each shows grade, confidence and the exact deductions.
- **Findings:** split into confirmed defects, optional improvements, and context-dependent items that need your judgment. Each finding names the evidence, root cause, impact, standard, fix, migration needs, risks and validation.
- **Recommendations:** grouped by table, with before and after, proposed SQL, dependencies, rollback and tests.
- **Migration plan:** every step, destructive steps, and steps refused by safety rules. Tables that look financial never get generated destructive SQL.
- **Roadmap:** phases from priority, with dependencies moved earlier.
- **Coverage:** rules run, skipped and why, and errors. A skipped rule lowers confidence; it does not count as passing.

Scores are a framework judgment for prioritizing work. They are not a certification.

## Test a plan safely

```powershell
python -m dbintel migrate test SOURCE [same options as assess] --approve PLAN_HASH
```

`PLAN_HASH` is printed by `assess`. It must match the exact plan, so a changed input changes the hash. By default the test uses a temporary SQLite file built from the model and sample rows. SQL that only runs on PostgreSQL or MySQL is marked not testable on SQLite.

To test on a real engine, point at a scratch server that you own:

```powershell
python -m dbintel migrate test SOURCE --approve PLAN_HASH ^
  --scratch-url "postgresql://user@host/dbintel_sandbox_mine" --allow-host host --scratch-password-env SCRATCH_PW
```

The database name must start with `dbintel_sandbox_`, and the host must be listed with `--allow-host`.

## Exit codes

| Code | Meaning |
|---|---|
| 0 | Success |
| 1 | An error, such as a missing file |
| 2 | Bad arguments, a refused token or a refused sandbox target |
| 3 | `--fail-on` was triggered |
| 4 | A sandbox step failed |

## Samples

`samples\` holds fictional databases and their `expected_findings.yaml` files. See `reports\demo\` for reports generated from them.
