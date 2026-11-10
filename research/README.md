# Database Schema Design Framework: Research Repository

This repository is the research foundation for a future technology-independent Database Schema Design and Data Engineering Standards Framework. Target uses are enterprise applications, ERP systems such as ASTRA, financial systems, SaaS platforms and large-scale data engineering.

**Status (2026-11-08):** Stage 1 research, including the follow-up research, is complete except for items that need licensed copies, manual browser checks or legal review. These are listed in `research_gaps.md`, section 7. Stage 2 has not started, and neither has Stage 3. This repository contains no schemas, DDL templates or validators, by design.

## Start here

| Goal | Read |
|---|---|
| Make a design decision | `design_decision_matrix.md` |
| Understand where approaches differ | `architecture_comparison.md` |
| Know what is not yet proven | `research_gaps.md` |
| Find or query a source | `resource_catalog.md`, `.json`, `.csv` |

## Contents

| File | Purpose |
|---|---|
| `resource_catalog.md` | Human-readable catalog of all sources |
| `resource_catalog.json`, `resource_catalog.csv` | Structured catalog for programmatic use |
| `official_documentation.md` | What PostgreSQL, MySQL, SQL Server, Oracle, MongoDB, AWS, Google Cloud, Azure, Databricks, Snowflake and dbt prescribe |
| `database_design_standards.md` | Modeling, normalization, keys, integrity, naming, types, indexing, transactions, anti-patterns |
| `data_modeling_approaches.md` | Kimball, Inmon, Data Vault, 3NF, One Big Table, Medallion, DDD, event-driven, Data Mesh, Data Fabric, temporal |
| `data_engineering_principles.md` | Validation, contracts, reconciliation, quality, lineage, observability, migrations, testing, backup, governance |
| `database_security_standards.md` | Security and privacy standards, tenant isolation, audit, retention, erasure |
| `data_pipeline_architecture.md` | ETL and ELT, batch and streaming, Kafka, CDC, table formats, orchestration |
| `industry_best_practices.md` | Production case studies, ledgers, ERP conventions, postmortems, reading list |
| `architecture_comparison.md` | Universal vs engine-specific practice, comparison matrices, conflict register |
| `design_decision_matrix.md` | Decisions for the 20 framework areas and the data lifecycle view |
| `research_gaps.md` | Progress, coverage ratings, unverified sources, follow-up list |

The working notes behind these files are in `../research_notes/Database schema design framework research/`. Its `CORRECTIONS.md` lists known errors in those notes, and the corrections override them.

## Catalog at a glance

| Measure | Count |
|---|---|
| Topic catalogs | 22 |
| Topic catalog rows | 671 |
| Duplicates merged | 77 |
| Unique resources | 594 |
| `url_verified` true | 568 |
| `url_verified` false | 26 |
| Reachable in scripted link check (2026-11-08) | 565 |
| Refused by host in link check | 24 |
| Local SSL error in link check | 4 |
| Timeout or connection failure in link check | 1 |
| Confirmed dead link | 0 |

The 29 links that were not `reachable` could not be confirmed by script. That does not mean those pages are gone. GOV-24, the earlier dead link, now points to an official GLEIF page.

## How to read the evidence

- **Classification.** MANDATORY means an engine-enforced rule, or a rule whose violation an authoritative source ties to a correctness, integrity or legal failure. RECOMMENDED is advised by the source. OPTIONAL/CONTEXTUAL depends on the situation.
- **Workload scope.** Every principle is scoped to OLTP, OLAP/warehouse, lakehouse, streaming or all. Advice for one must not be applied to another.
- **Authority.** Levels run from 5 (official documentation, standards bodies, foundational papers) to 1 (unverified).
- **Inference.** Synthesis that goes beyond a source is labelled as inference.

## Known limits

- Most web pages were read through a summarizing fetch tool. Quotation marks are reserved for PDF-extracted text, and other wording is paraphrase. Check the source before quoting it in a standard.
- Paywalled ISO standards are described only at scope level or from drafts and secondary sites.
- Many canonical books are known only from publisher pages or secondary reports.
- ERP evidence now covers fiscal period close, exchange-rate design and retention by jurisdiction (notes 18 and 19), but SAP product documentation, FASB Codification text and exchange-rate precision remain gaps.
- Legal content is research input, not legal advice. It needs review by counsel.

## Next stages

1. Close the items still open in `research_gaps.md`, section 7: licensed copies, manual browser checks and legal review.
2. Stage 2: turn the decision matrix into rules, checklists and naming conventions.
3. Stage 3: build enforceable rules, templates, automated validators and documentation across the full lifecycle: Data Modeling, Schema Design, Data Validation, Transactions, ETL/ELT, Data Quality, Governance, Reporting, Monitoring.
