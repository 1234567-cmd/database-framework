# Configuration

Start with `python -m dbintel init-profile profile.yaml`. Every key is optional. Unknown keys are refused.

## Profile keys

| Key | Default | Meaning |
|---|---|---|
| `workload` | `OLTP` | `OLTP`, `OLAP`, `data_warehouse` or `lakehouse` |
| `tenancy` | `none` | `none`, `pool`, `bridge` or `silo` |
| `tenant_column` | `tenant_id` | Tenant column name |
| `company_column` | `company_id` | Company column name |
| `multi_company` | `false` | Check `company_column` on tables |
| `system_of_record` | `true` | Treat as the authoritative source |
| `audit_columns` | created_at and so on | Column name groups expected on tables |
| `tenant_exempt_tables` | small set | Tables that need no tenant column |
| `audit_exempt_tables` | small set | Tables that need no audit columns |
| `exclude_tables` | none | Tables to ignore |
| `money_name_patterns` | amount, price and so on | Names treated as money |
| `identifier_limit` | 63 | Longest allowed identifier |
| `target_engines` | postgres, mysql | Engines the schema should stay portable to |
| `table_plural` | `true` | Plural table name convention |
| `data_sample_limit` | 100000 | Most rows read per data check |
| `financial_table_patterns` | none | Extra regexes marking financial tables, in addition to journal, ledger, invoice and payment. Destructive changes to these are refused. |
| `rules` | none | Rule overrides, below |

## Rule overrides

```yaml
rules:
  SCH-047:
    enabled: false
  GVN-002:
    severity: informational
  SCH-002:
    kind: optional_improvement
  DQ-005:
    params:
      min_rows: 500
```

An override can set `enabled`, `severity`, `kind` and `params`. See each rule with `python -m dbintel rules show ID`. No code changes are needed.

The migration safety module also accepts `rules: {migration.financial: {patterns: [...]}}` for financial tables. Use `financial_table_patterns` for new profiles.

## Add a rule

1. Add an entry to a file in `src/dbintel/rules/catalog/`. It needs an id, check name, title, category, severity, kind, the standards it enforces, root cause, business and technical impact, solution, complexity, migration notes, risks and validation text.
2. Optional keys: `requires` (any of `data`, `security_metadata`, `query_stats`, `pipelines`, `live`, `declared_schema`), `workloads`, `tenancy`, `params`, `confidence`.
3. If no existing check fits, add a function in an analyzer module:

```python
from ..rules.engine import Hit, check

@check("schema.my_check")
def my_check(db, profile, params):
    for table in db.tables:
        yield Hit(table=table.fqname, evidence="what was found")
```

Checks must only find facts. Text comes from the catalog. The engine refuses unknown or superseded standards. Regenerate `docs/RULES.md` with `python scripts/generate_rules_doc.py`.

## Add a connector

Subclass `connectors.base.Connector`, implement `_execute`, `extract` and `close`, put the session in read-only mode in the constructor, and register it:

```python
from dbintel.connectors import register_connector

register_connector("oracle", OracleConnector)
```

Do not bypass `Connector.query`, which refuses any statement that is not a read.

## Data inputs

- Query logs are JSON (`[{"sql": ..., "calls": 10, "mean_ms": 2.5}]`) or plain SQL statements.
- Pipeline manifests are YAML with a `pipelines` list of jobs and steps. Field names match `PipelineJob` and `PipelineStep` in `model.py`. See `samples\pipelines.yaml`.
