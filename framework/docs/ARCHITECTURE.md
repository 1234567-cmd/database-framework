# Architecture

`dbintel` assesses an existing database and proposes improvements. It never changes the database it analyzes.

## Workflow

Import or connect, extract metadata, analyze, run rules, classify, explain, recommend, show before and after, generate proposed SQL, then write the report.

| Layer | Package | Responsibility |
|---|---|---|
| Model | `model.py` | Engine-independent description of schema, security, workload and pipelines |
| Connectors | `connectors/` | Read-only access to MySQL, PostgreSQL, SQLite and registered adapters |
| Importers | `importers/` | SQL dumps, CSV, Excel, JSON metadata, query logs, pipeline manifests |
| Rule engine | `rules/engine.py`, `rules/catalog/*.yaml` | Runs configurable, standards-linked rules |
| Analyzers | `analyzers/` | Check functions that find facts and return hits |
| Recommendations | `recommend/` | Before and after design, dependencies, priorities |
| Migrations | `migrate/` | Proposed SQL, rollback, destructive-change detection, sandbox test |
| Health | `scoring.py` | Explainable category and overall scores with confidence |
| Reporting | `reporting/` | JSON, Markdown, HTML, ER diagrams, roadmap |
| Pipeline | `pipeline.py`, `cli.py` | The end-to-end workflow and command line |

## Technology

Python 3.10 or later. Required packages are `sqlglot` for SQL parsing and `PyYAML` for rule catalogs. Database drivers and Excel support are optional extras.

## Rule engine

Each catalog rule names a check function, the Stage 2 standards it enforces, its category, severity, finding kind, workload scope, required inputs, parameters and all explanatory text. A profile can disable a rule or override its severity, kind or parameters without code changes. The engine refuses to start if a rule cites an unknown or superseded standard.

A rule whose inputs are unavailable is skipped and recorded. Skipped rules lower the confidence of the health score instead of counting as a pass.

## Security model

- Connectors run in read-only mode and also pass every statement through a guard that allows only read statements.
- Generated migrations are written to files. The framework has no path that applies them to a source database.
- A sandbox test requires an approval token equal to the hash of the exact migration plan.
- Passwords are read from environment variables and are redacted from errors and reports. Sample values from sensitive columns are masked.

## Extending

- **New engine:** implement `connectors.base.Connector` and register it with `register_connector`.
- **New rule:** add a catalog entry, and a `@check` function if no existing check fits.

Known limits are in `LIMITATIONS.md`.
