# Database Schema Design and Data Engineering Standards (Stage 2)

**Status:** complete. Owner accepted all proposed defaults on 2026-11-08. Built from `../research/`. It contains no schemas, DDL templates or validator code.

## Start here

Use `rule_registry.json` and `validation_checklists.md`. `DECISIONS_TO_APPROVE.md` records the accepted decisions.

## Contents

| File | Purpose |
|---|---|
| `DECISIONS_TO_APPROVE.md` | 61 decisions and housekeeping items, with accepted defaults |
| `OVERLAP_REPORT.md` | Outcome of each duplicate, contradiction and coverage hole |
| `validation_checklists.md` | Checks for each lifecycle stage, generated from the registry |
| `rule_registry.json` | All 545 rules in structured form for Stage 3 validators |
| `RULE_FORMAT.md` | Rule fields and classification rules |
| `rules/01_modeling_and_integrity.md` | Architecture, modeling, ER design, normalization, integrity |
| `rules/02_naming_and_data_types.md` | Naming conventions, data types, NULL policy |
| `rules/03_performance_transactions_scalability.md` | Indexing, transactions, scalability |
| `rules/04_tenancy_security_audit.md` | Tenant isolation, security, audit and history |
| `rules/05_migrations_testing_recovery.md` | Migrations, testing, backup and recovery |
| `rules/06_pipelines_quality_governance.md` | Pipelines, data quality, reporting, monitoring, governance |
| `rules/07_erp_finance_compliance.md` | ERP finance, retention and erasure, document numbering |

## Rule counts

| Status | Count | Meaning |
|---|---|---|
| active | 367 | Usable now |
| provisional | 150 | Incomplete evidence, no value set, or needs legal review |
| superseded | 28 | Replaced by a canonical rule, kept for ID history |
| **Total** | **545** | 116 MANDATORY, 340 RECOMMENDED, 89 OPTIONAL |

Owner approval makes a choice binding within this framework. It does not create evidence, so the evidence strength of each rule is unchanged.

## Open items

These do not block Stage 3. Affected rules stay provisional.

- Legal review of retention, erasure and document numbering rules
- No value set for exchange-rate precision, triangulation, lock budgets and quality thresholds
- A named person for the framework exception approver role
- Whether the present-only exception in TYP-035 survives (OVERLAP_REPORT item OR-20)
- No research supports outbox relay monitoring, so no rule exists
