# Limitations

Be careful with what this tool does not know. It reports what it can check. Where it cannot check, the rule is skipped and listed under coverage.

## What was tested, and how

| Area | How it was tested |
|---|---|
| PostgreSQL connector, extraction and read-only behaviour | A real PostgreSQL server started by pgserver |
| Generated PostgreSQL migrations, up and down | A real scratch server, only on the SaaS sample. Other plans were not executed on PostgreSQL. |
| MySQL connector | **A fake driver only.** No MySQL server was available and the Docker daemon was off. One real-server test exists and skips unless `DBINTEL_MYSQL_URL` is set. |
| Generated MySQL migrations | **Generated and reviewed in tests, never run on MySQL.** The SQLite sandbox marks most MySQL steps not testable. |
| `pg_stat_statements` input | The code path runs on the test server, but the extension is not loaded there, so the real path is **untested** with live statistics. Query rules were tested with sample logs. |
| Oracle, SQL Server and other engines | Not implemented. Add a connector. |

## Heuristics

- Most findings come from names, types, structure and sampled rows. A rule can be wrong about your system. Context-dependent findings exist for this reason.
- Sensitive-data rules look at names and value shapes. They can miss data or flag harmless columns.
- Missing foreign keys are inferred from names such as `customer_id`. Orphan detection needs the parent to have a single-column primary key. So orphans pointing at a table without a primary key are not reported, for example `orders.customer_id` to `customers` in the ERP sample.
- Severity, the score, the critical cap and category weights are framework judgments, not a published standard.
- Row checks read a sample up to `data_sample_limit`. A clean sample does not prove the whole table is clean.
- Findings describe the input. A dump, CSV or Excel file may not match production.

## CSV and Excel

Column types come from guessing cell values, so rules that need a declared schema are skipped, not reported. These include primary keys, foreign keys and declared money types. Skipped rules lower confidence.

## SQL parsing

- Dumps are read by a token-level parser, not a server. Vendor-specific syntax can be skipped with an import warning.
- Query parsing uses sqlglot. Unusual dialects or dynamic SQL may be missed. Procedural bodies are searched by name only.
- Views are parsed when possible, and searched by name otherwise.

## Migrations

- Every generated migration is a proposal. Review it, and test it on a copy.
- The plan cannot see application code unless you pass `--app-source-dir`, and even then only by name search. Dynamic SQL can be missed.
- The financial protection works from table names. Add yours with `financial_table_patterns`.
- Manual steps carry no SQL.
- Large-table lock behaviour cannot be proven here. Rehearse on production-sized copies.

## Reporting

- The ER diagrams are a simple grid layout. Lines can cross on busy schemas; the Mermaid source is included for better rendering elsewhere.
- Lineage is at object level only. Column-level lineage is not derived.
- Root cause groups are formed from matching text and are a starting point for discussion.
- 262 of the 517 active or provisional standards need manual review and 145 need a runtime this tool does not operate. See `docs/RULES.md`.

## Web interface

- The sandbox only targets a temporary SQLite copy. Steps that cannot run on SQLite are reported as not testable. Use `migrate test --scratch-url` for the target engine.
- A saved run is tested from its stored schema only, so paths that depend on row data are untested. Reopened runs can show sandbox results only from the current launch.
- The ER view shows one domain or one table's neighbours, up to 60 tables. Layout is automatic and lines can still cross.
- Cancelling a sandbox test ends the process holding sample rows. Further tests of that run are schema only.
- A file path entered in the form is read with the permissions of the person running the app.
- Browser behaviour is exercised by a headless Chrome check run by hand, not by the automated test suite.
