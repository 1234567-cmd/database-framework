# Stage 2 Standards: Migrations, Testing and Recovery

Scope: schema migrations and version control (MIG), testing and automated schema validation (TST), backup, recovery and disaster recovery (BDR). Format: `../RULE_FORMAT.md`. Machine-readable copy: `../registry/05_migrations_testing_recovery.json`.

These rules come from existing research only. No web research was done and no sources were added. They contain no schemas, DDL or validator code.

## How to read this file

- Levels follow the classifications in `research/design_decision_matrix.md` sections 13, 18 and 19. Departures and differences from other research files are in "Classification record".
- The matrix states that no standards body addresses migrations, so no MIG rule is MANDATORY.
- `evidence` holds catalog IDs, plus `research/<file>#<anchor>` entries where a source has no catalog ID or a decision row is cited.
- Backup and recovery has no lifecycle stage of its own. Following the matrix, which places restore results and recovery under Monitoring, BDR rules use Monitoring, or Governance for ownership and objective-setting.
- Source wording is paraphrased throughout, in line with `research/research_gaps.md` section 6.1.


## Schema migrations and version control (MIG)

### MIG-001: Versioned, tool-applied schema changes

**Every schema change to a permanent environment SHOULD be a versioned script held in version control and applied by a migration tool that records what was applied.**

| Field | Value |
|---|---|
| Level | RECOMMENDED |
| Status | active |
| Decision ref | B1 |
| Scope | all |
| Applies when | always; for warehouse and lakehouse platforms, where DDL is managed through migrations or versioned models |
| Rationale | Manual changes leave environments out of step and cannot be reproduced or audited; Azure lists manual schema change as an antipattern. |
| Exceptions | Emergency manual change during an incident, recorded and back-ported to version control afterward; approved by the database owner. |
| Engine notes | Flyway, Liquibase, Alembic, Prisma and Atlas keep a history record in different forms. Warehouse teams may use versioned model code in place of migration scripts. |
| Evidence | OPS-15, OPS-01, OPS-10, CLOUD-18, research/design_decision_matrix.md#MG-1, research/data_engineering_principles.md#CHG-01 |
| Evidence strength | case_study |
| Check method | manual_review |
| Check | Confirm each environment has a migration history and that every applied entry matches a script in version control. |
| Lifecycle stage | Governance |

### MIG-002: Applied migrations are immutable

**A migration already applied to a permanent environment SHOULD NOT be edited; corrections SHOULD be made by a new migration.**

| Field | Value |
|---|---|
| Level | RECOMMENDED |
| Status | active |
| Decision ref | B1 |
| Scope | OLTP, data_warehouse |
| Applies when | Migration-based or hybrid authoring is in use |
| Rationale | Editing an applied migration makes environments diverge silently and invalidates the recorded history. |
| Exceptions | Comment-only or formatting repair using the tool's documented repair command; approved by the database owner. |
| Engine notes | Flyway checksums detect edits to applied versioned migrations. Rails guidance gives the same direction. |
| Evidence | OPS-10, research/data_engineering_principles.md#CHG-04 |
| Evidence strength | multi_vendor |
| Check method | migration_lint |
| Check | Compare stored checksums or file hashes of applied migrations with the repository and fail on any change. |
| Lifecycle stage | Governance |

### MIG-003: Authoring model chosen and recorded

**Each system MAY use state-based, migration-based or hybrid authoring, and SHOULD record the choice; the accepted default is hybrid with the planned migration checked in.**

| Field | Value |
|---|---|
| Level | OPTIONAL |
| Status | active |
| Decision ref | B3 |
| Scope | all |
| Applies when | always |
| Rationale | State-based tools can lose data on renames and pure migration histories accumulate; sources agree neither is ideal and no benchmark settles it, so the default is a judgment. |
| Exceptions | Deviation from the accepted default needs a recorded reason approved by the framework exception approver. |
| Engine notes | Atlas and Prisma derive a migration from desired state and check in the plan. Legacy Prisma Migrate behaviour was not verified against ORM 8 documentation. |
| Evidence | OPS-14, OPS-13, research/design_decision_matrix.md#MG-2, research/architecture_comparison.md#C-43, research/data_engineering_principles.md#CHG-16 |
| Evidence strength | multi_vendor |
| Check method | manual_review |
| Check | Confirm the system's design record names its authoring model and that any generated plan is committed before it is applied. |
| Lifecycle stage | Governance |

### MIG-004: Expand and contract for incompatible change

**On live OLTP systems, each schema change SHOULD be deployable while the previous application version runs, and incompatible changes SHOULD use expand, migrate and contract across separate releases.**

| Field | Value |
|---|---|
| Level | RECOMMENDED |
| Status | active |
| Decision ref | null |
| Scope | OLTP |
| Applies when | The system is deployed while serving traffic; covers renames, type changes and drops of columns or tables |
| Rationale | A change that breaks the running application version causes an outage even when the DDL itself takes no long lock, which is why a drop can be lock-safe and still application-unsafe (conflict C2). |
| Exceptions | Systems with an agreed maintenance window that stops all application versions; approved by the system owner. |
| Engine notes | Dropping a column is catalog-only on PostgreSQL but still breaks ORM caches; GitLab spreads it over three releases. Support for at least one prior schema version is stated by Azure only and is not a general rule. The every-change-deployable wording is the research authors' meta-rule [INFERENCE]. |
| Evidence | OPS-01, OPS-02, OPS-05, OPS-06, CASE-23, research/design_decision_matrix.md#MG-3, research/data_engineering_principles.md#CHG-02, research/data_engineering_principles.md#C2 |
| Evidence strength | case_study |
| Check method | manual_review |
| Check | For each rename, type change or drop, confirm the release plan shows the expand, migrate and contract steps in separate releases. |
| Lifecycle stage | Governance |

### MIG-005: Rollback stance

**OLTP migrations SHOULD be forward-only and rely on backward compatibility and tested backups for recovery, with down scripts optional and tested.**

| Field | Value |
|---|---|
| Level | RECOMMENDED |
| Status | active |
| Decision ref | B2 |
| Scope | OLTP |
| Applies when | always on OLTP systems |
| Rationale | Down scripts cover only some change types and cannot restore dropped data, so relying on them gives false assurance; sources disagree on whether reversibility is required (conflict C1). |
| Exceptions | Deviation from the accepted default needs a recorded reason approved by the framework exception approver. |
| Engine notes | GitLab requires reversibility with exceptions; Braintree does not revert schema to roll back; Flyway undo is limited and points to backward compatibility; Liquibase treats rollback as first-class with limits and no automatic rollback for drops, raw SQL or data operations; Prisma has no down files. |
| Evidence | OPS-10, OPS-11, OPS-04, OPS-07, research/design_decision_matrix.md#MG-4, research/architecture_comparison.md#C-42, research/data_engineering_principles.md#CHG-14, research/data_engineering_principles.md#C1 |
| Evidence strength | multi_vendor |
| Check method | manual_review |
| Check | Confirm the migration policy states the rollback stance and that each release plan names its recovery route. |
| Lifecycle stage | Governance |

### MIG-006: Developer authored, DBA reviewed

**Schema migrations SHOULD be authored by the delivery team, checked by automation and reviewed by the people responsible for the production database.**

| Field | Value |
|---|---|
| Level | RECOMMENDED |
| Status | active |
| Decision ref | null |
| Scope | all |
| Applies when | always |
| Rationale | Adopting migration practice without the production database owners meets resistance and bypasses their knowledge of production behaviour. |
| Exceptions | DBA-authored migrations are acceptable where the team has no developer ownership of the schema; approved by the database owner. |
| Engine notes | none. No source quantifies developer-authored against DBA-authored outcomes. |
| Evidence | OPS-15, OPS-01, research/design_decision_matrix.md#MG-5, research/data_engineering_principles.md#CHG-22 |
| Evidence strength | case_study |
| Check method | manual_review |
| Check | Confirm each merged migration has a review from a named production database owner. |
| Lifecycle stage | Governance |

### MIG-007: Generated migrations are candidates

**Tool-generated migrations SHOULD be reviewed and corrected before merge and SHOULD NOT be applied unchanged.**

| Field | Value |
|---|---|
| Level | RECOMMENDED |
| Status | active |
| Decision ref | null |
| Scope | all |
| Applies when | A tool or ORM generates the migration |
| Rationale | Generators cannot detect renames and report them as a drop and an add, which loses data if applied as produced. |
| Exceptions | none |
| Engine notes | Alembic states that manual review is always necessary. Topic note 13 labelled this MANDATORY; the matrix holds it as RECOMMENDED. |
| Evidence | OPS-12, OPS-13, research/design_decision_matrix.md#MG-6, research/architecture_comparison.md#C-44, research/data_engineering_principles.md#CHG-05 |
| Evidence strength | multi_vendor |
| Check method | manual_review |
| Check | Confirm generated migrations show review, and that any drop-plus-add pair was checked for being a rename. |
| Lifecycle stage | Governance |

### MIG-008: Separate lock and runtime budgets

**Migrations on live OLTP systems SHOULD state separate budgets for lock hold time and total runtime, set per system from rehearsal, and SHOULD fail or be replanned when rehearsal exceeds them; no value set framework-wide.**

| Field | Value |
|---|---|
| Level | RECOMMENDED |
| Status | provisional |
| Decision ref | B6 |
| Scope | OLTP |
| Applies when | Migrations run against tables serving live traffic |
| Rationale | Lock hold and runtime are different quantities, and an unbounded one stalls application traffic. The quoted operator values measure different things and no independent benchmark exists, so any default is a judgment. |
| Exceptions | none |
| Engine notes | Operator values, not portable defaults: Braintree about 2 seconds exclusive lock hold; strong_migrations 10 second lock timeout example; GitLab 15 second statement timeout, and 3, 10 and 20 minute limits by migration type. A statement timeout is not a lock-hold limit. Braintree covers PostgreSQL 9.1 to 12, so re-check against current versions. |
| Evidence | OPS-07, OPS-08, OPS-04, research/design_decision_matrix.md#MG-7, research/architecture_comparison.md#C-47, research/data_engineering_principles.md#CHG-09 |
| Evidence strength | case_study |
| Check method | pipeline_test |
| Check | Confirm both budgets are stated and compare rehearsal lock and duration measurements against them. |
| Lifecycle stage | Governance |

### MIG-009: Bounded lock acquisition

**Migrations on live OLTP systems SHOULD acquire locks with a short timeout and retry, after checking for long-running queries.**

| Field | Value |
|---|---|
| Level | RECOMMENDED |
| Status | active |
| Decision ref | null |
| Scope | OLTP |
| Applies when | Migrations run against tables serving live traffic |
| Rationale | A waiting lock request queues all later queries on the table, so a blocked migration can stall traffic before it has acquired anything. |
| Exceptions | Dedicated maintenance windows with no traffic; approved by the database owner. |
| Engine notes | The queueing behaviour is documented for PostgreSQL. Timeout mechanisms differ by engine. The research notes label this MANDATORY; the matrix states nothing in this area is MANDATORY. |
| Evidence | OPS-07, OPS-08, OPS-04, research/data_engineering_principles.md#CHG-08, research/data_engineering_principles.md#CHG-10 |
| Evidence strength | case_study |
| Check method | migration_lint |
| Check | Confirm each migration touching an existing table sets a lock timeout and has a defined retry. |
| Lifecycle stage | Schema Design |

### MIG-010: Use non-blocking DDL paths on large tables

**DDL on large or high-traffic OLTP tables SHOULD use the engine's documented online or staged path rather than a blocking form where such a path exists.**

| Field | Value |
|---|---|
| Level | RECOMMENDED |
| Status | active |
| Decision ref | null |
| Scope | OLTP |
| Applies when | The table is large or high-traffic; thresholds are set per system |
| Rationale | Blocking index builds, constraint validation and table rewrites stop writes, and sometimes reads, for the length of the operation. |
| Exceptions | Small tables, new empty tables, and operations with no documented online path, such as PostgreSQL exclusion constraints; approved by the database owner. |
| Engine notes | PostgreSQL: concurrent index builds outside a transaction, constraints added unvalidated and validated later, batched backfill. MySQL: INSTANT or INPLACE where available, otherwise an online tool. [WF] The MySQL 8.4 online DDL matrix was read through a summarising tool only; re-check against the manual before use. Safe sequences per operation are in data_engineering_principles.md section 3.3 and depend on engine version. |
| Evidence | OPS-09, PERF-10, OPS-07, OPS-05, OPS-08, CASE-23, research/design_decision_matrix.md#MG-8, research/design_decision_matrix.md#MG-9, research/official_documentation.md#Online DDL matrix |
| Evidence strength | single_vendor |
| Check method | migration_lint |
| Check | Flag blocking forms of index, constraint and type-change operations on tables above the system's size threshold, allowing recorded waivers. |
| Lifecycle stage | Schema Design |

### MIG-011: Online change tool selected deliberately

**Where an external online schema change tool is needed, the system MAY use a trigger-based or log-based tool and SHOULD record why; the accepted default is log-based unless constraints rule it out.**

| Field | Value |
|---|---|
| Level | OPTIONAL |
| Status | active |
| Decision ref | C10 |
| Scope | OLTP |
| Applies when | MySQL-family engines on tables where native online DDL is unsuitable |
| Rationale | Each mechanism has limits and each project describes itself favorably; no independent comparison exists, so the default is a judgment. |
| Exceptions | Deviation from the accepted default needs a recorded reason approved by the framework exception approver. |
| Engine notes | pt-online-schema-change uses triggers and will not run on tables that already have triggers. gh-ost reads the binlog and treats triggers as a source of risk. Test on a replica and verify backups first. Managed platforms may provide their own ghost-table workflow. |
| Evidence | CASE-23, research/design_decision_matrix.md#MG-9, research/architecture_comparison.md#C-46, research/data_engineering_principles.md#CHG-12, research/data_engineering_principles.md#C6 |
| Evidence strength | single_vendor |
| Check method | manual_review |
| Check | Confirm the migration plan names the tool and the reason, and that the table meets the tool's documented conditions. |
| Lifecycle stage | Schema Design |

### MIG-012: Large backfills batched outside DDL

**Large data backfills SHOULD run batched and throttled outside the DDL transaction.**

| Field | Value |
|---|---|
| Level | RECOMMENDED |
| Status | active |
| Decision ref | null |
| Scope | OLTP |
| Applies when | The backfill volume can hold locks or load beyond the system's budgets |
| Rationale | A backfill inside the DDL transaction holds its locks for the entire backfill. |
| Exceptions | none |
| Engine notes | GitLab uses batched background migrations. Stripe ran its large backfills offline. |
| Evidence | OPS-04, OPS-08, OPS-06, research/design_decision_matrix.md#MG-10, research/architecture_comparison.md#C-45 |
| Evidence strength | case_study |
| Check method | migration_lint |
| Check | Flag data modification statements inside a migration that also performs DDL, and confirm large backfills have batch size and throttle settings. |
| Lifecycle stage | Schema Design |

### MIG-013: Placement of small data changes

**Small data changes SHOULD be separate from schema changes, as a reviewed data migration in the same versioned history.**

| Field | Value |
|---|---|
| Level | RECOMMENDED |
| Status | active |
| Decision ref | B5 |
| Scope | OLTP |
| Applies when | A data change accompanies a schema change and is too small to need a batched backfill |
| Rationale | Mixing data and schema changes complicates review and lock behaviour; sources disagree on where data changes belong (conflict C4), and the threshold is volume-dependent. |
| Exceptions | Deviation from the accepted default needs a recorded reason approved by the framework exception approver. |
| Engine notes | Rails discourages data changes in migrations; GitLab allows post-deployment and batched ones; Django provides a data migration step. |
| Evidence | OPS-04, OPS-08, research/data_engineering_principles.md#CHG-06, research/data_engineering_principles.md#C4, research/architecture_comparison.md#C-45 |
| Evidence strength | multi_vendor |
| Check method | manual_review |
| Check | Confirm that data changes follow the approved placement and are reviewed like schema changes. |
| Lifecycle stage | Schema Design |

### MIG-014: Transaction boundary for DDL

**On high-traffic OLTP systems, each DDL statement SHOULD run in its own transaction, and other systems SHOULD use one transaction per migration where the engine supports it.**

| Field | Value |
|---|---|
| Level | RECOMMENDED |
| Status | active |
| Decision ref | B4 |
| Scope | OLTP |
| Applies when | The engine supports transactional DDL |
| Rationale | One transaction per migration gives atomicity but holds several objects' locks at once, and sources disagree (conflict C3). |
| Exceptions | Deviation from the accepted default needs a recorded reason approved by the framework exception approver. |
| Engine notes | Django and Flyway wrap migrations in a transaction by default where supported; Braintree does not combine DDL statements. When removing foreign keys use a consistent lock order. Concurrent index builds cannot run in a transaction on PostgreSQL. |
| Evidence | OPS-07, OPS-04, research/data_engineering_principles.md#C3 |
| Evidence strength | multi_vendor |
| Check method | migration_lint |
| Check | Flag migrations that put several DDL statements in one transaction on systems marked high-traffic. |
| Lifecycle stage | Schema Design |

### MIG-015: Safety rules tied to engine version

**Each migration safety rule SHOULD state the engine and version range it applies to.**

| Field | Value |
|---|---|
| Level | RECOMMENDED |
| Status | active |
| Decision ref | null |
| Scope | all |
| Applies when | always |
| Rationale | Rules go stale when defaults change; adding a column with a constant default was unsafe before PostgreSQL 11 and is metadata-only afterward (conflict C5). |
| Exceptions | none |
| Engine notes | PostgreSQL rewrite behaviour changed over versions. CASE-27 is 2014-era and must be re-checked against current versions before use. |
| Evidence | OPS-09, CASE-27, OPS-04, research/design_decision_matrix.md#MG-11, research/architecture_comparison.md#C-48, research/data_engineering_principles.md#CHG-07 |
| Evidence strength | case_study |
| Check method | manual_review |
| Check | Confirm each engine-specific migration rule or lint configuration records its version range. |
| Lifecycle stage | Schema Design |

### MIG-016: Verify large data migrations

**Large OLTP data migrations SHOULD verify the new path against the old, for example through dual writes and comparison reads, before switching reads.**

| Field | Value |
|---|---|
| Level | RECOMMENDED |
| Status | active |
| Decision ref | null |
| Scope | OLTP |
| Applies when | A data model or storage migration moves live data |
| Rationale | Without comparison, defects in the new path surface only after the old path is gone. |
| Exceptions | Small migrations verified by reconciliation counts; approved by the system owner. |
| Engine notes | Stripe used a comparison harness on hundreds of millions of objects. This rule also covers matrix row TS-11, so no separate TST rule exists. All sources are single-operator reports. |
| Evidence | OPS-06, CASE-02, CASE-03, CASE-07, CASE-15, research/design_decision_matrix.md#MG-12, research/design_decision_matrix.md#TS-11, research/data_engineering_principles.md#CHG-11 |
| Evidence strength | case_study |
| Check method | pipeline_test |
| Check | Confirm the migration plan names a comparison method and that mismatch results were reviewed before cutover. |
| Lifecycle stage | Schema Design |

### MIG-017: Portable safe changes on table formats

**Lakehouse tables intended to stay portable across table formats SHOULD limit in-place schema evolution to the changes all target formats support: adding a nullable column, widening integer and float types, and widening decimal types.**

| Field | Value |
|---|---|
| Level | RECOMMENDED |
| Status | active |
| Decision ref | null |
| Scope | lakehouse |
| Applies when | Tables are or may be read through more than one table format |
| Rationale | A change safe in one format can break readers on another. |
| Exceptions | Single-format tables may use that format's wider evolution rules; approved by the data platform owner. |
| Engine notes | Iceberg, Delta and Hudi differ beyond this set. The Hudi promotion matrix was reconstructed from flattened page text and should be verified on the page. OLTP migration rules do not apply here. |
| Evidence | PIPE-10, PIPE-11, PIPE-12, research/design_decision_matrix.md#MG-13 |
| Evidence strength | multi_vendor |
| Check method | pipeline_test |
| Check | Compare the proposed schema change against the supported set for every format that reads the table. |
| Lifecycle stage | ETL/ELT |

### MIG-018: Breaking changes in event streams

**Event schemas SHOULD evolve compatibly, and a change that compatibility cannot express SHOULD use a dual upgrade with a versioned topic.**

| Field | Value |
|---|---|
| Level | RECOMMENDED |
| Status | active |
| Decision ref | null |
| Scope | streaming |
| Applies when | Schemas are shared between producers and consumers on a stream |
| Rationale | An incompatible change breaks consumers still reading the earlier form. |
| Exceptions | none |
| Engine notes | Confluent Schema Registry compatibility modes are the evidenced mechanism; other registries were not assessed here. |
| Evidence | PIPE-02, PIPE-03, research/design_decision_matrix.md#MG-14 |
| Evidence strength | single_vendor |
| Check method | pipeline_test |
| Check | Run the registry's compatibility check against the proposed schema and confirm that breaking changes have a versioned topic and consumer migration plan. |
| Lifecycle stage | ETL/ELT |

### MIG-019: Breaking changes to contracted models

**Removal, type change or constraint removal on a contracted analytical model SHOULD be classified as breaking and released under a new model version.**

| Field | Value |
|---|---|
| Level | RECOMMENDED |
| Status | active |
| Decision ref | null |
| Scope | data_warehouse, lakehouse |
| Applies when | The model has a published contract or external consumers |
| Rationale | A silent contract change breaks downstream consumers. |
| Exceptions | Internal models with no consumers outside the owning team. |
| Engine notes | dbt model contracts and versions are the evidenced mechanism. dbt warns that adopting model versions too early raises maintenance cost. DQ-03 and LAKE-17 are the same page, so this is single-vendor evidence. The research notes label this MANDATORY; the matrix holds it as RECOMMENDED. |
| Evidence | DQ-03, LAKE-17, research/design_decision_matrix.md#MG-15, research/data_engineering_principles.md#CHG-23 |
| Evidence strength | single_vendor |
| Check method | pipeline_test |
| Check | Diff the proposed contract against the published one and fail on breaking changes with no new version. |
| Lifecycle stage | Governance |

### MIG-020: Per-tenant schema version tracking

**Systems using one database or schema per tenant MAY track the applied schema version per tenant.**

| Field | Value |
|---|---|
| Level | OPTIONAL |
| Status | active |
| Decision ref | null |
| Scope | OLTP |
| Applies when | Tenants are isolated into separate databases or schemas |
| Rationale | Without per-tenant version records, partial rollouts leave tenants on unknown versions. |
| Exceptions | none |
| Engine notes | Stated by Azure only; recorded in official_documentation.md section 15 as not yet a general rule. |
| Evidence | CLOUD-18, research/official_documentation.md#per-tenant schema version tracking |
| Evidence strength | single_vendor |
| Check method | catalog_query |
| Check | Confirm each tenant has a recorded schema version and report tenants behind the current one. |
| Lifecycle stage | Governance |

## Testing and automated schema validation (TST)

### Tool coverage and Stage 3 validator needs

Coverage is from `research/data_engineering_principles.md` section 3.7 (note 20). Not found means not found in the pages read and is not proof of absence. Atlas custom rules need Pro and Liquibase custom checks need a Secure license.

| Check | Rule | Existing tool coverage | Stage 3 custom validator needed? |
|---|---|---|---|
| Blocking and destructive migration patterns | TST-002 | Existing tools: Squawk, Atlas analyzers, Liquibase policy checks (licensed), strong_migrations | No |
| Schema structure and behaviour assertions | TST-003 | By per-object assertion: pgTAP, tSQLt, utPLSQL | No; a schema-wide sweep needs generated tests |
| Drift from intended state | TST-006 | Atlas drift detection, Flyway checksums, Prisma marker check | No |
| Analytical key and relationship tests | TST-008 | Built in: dbt tests, Dagster asset checks | No |
| Foreign key index | TST-012 | Built in: Schemalint, prisma-lint. Custom: Atlas Pro. Assertion: pgTAP | No, where a listed tool fits the engine |
| Primary key present, required columns | TST-013 | Built in: Schemalint, prisma-lint. Custom: Atlas Pro. Assertion: pgTAP | No, where a listed tool fits the engine |
| Reserved words | TST-014 | Partial: SQLFluff RF04, dialect-dependent, excludes reserved keywords from its own rule | Yes, for full coverage |
| **Money types** | TST-015 | No built-in money rule. Generic only: pgTAP `col_type_is`, tSQLt schema comparison, prisma-lint `require-field-type` by field name | **Yes** |
| **Tenant keys** | TST-016 | No rule named for tenant keys. Generic only: Schemalint `mandatory-columns`, prisma-lint `require-field`, pgTAP `has_column`, Atlas predicate (Pro). RLS rules are a different check | **Yes** |
| **Audit columns** | TST-017 | No rule named for them. Required-column rules are the available mechanism (inference) | **Yes** |


### TST-001: Three-tier schema change gate

**Schema changes SHOULD pass static lint, then a real-engine apply with tests, then a production-like rehearsal before production.**

| Field | Value |
|---|---|
| Level | RECOMMENDED |
| Status | provisional |
| Decision ref | null |
| Scope | all |
| Applies when | always; the rehearsal tier applies where a production-like dataset can be provided |
| Rationale | Each tier catches failures the others miss, and skipping one lets those failures reach production. The three-tier shape is the research authors' synthesis of the tool set. |
| Exceptions | A tier may be skipped with a recorded waiver from the database owner. |
| Engine notes | The tool for each tier varies by engine; see TST-002, TST-003 and TST-004. |
| Evidence | OPS-16, OPS-13, OPS-15, research/design_decision_matrix.md#TS-1, research/data_engineering_principles.md#CHG-19 |
| Evidence strength | inference |
| Check method | pipeline_test |
| Check | Confirm the delivery pipeline runs all three tiers in order and blocks promotion on failure. |
| Lifecycle stage | Governance |

### TST-002: Static migration lint with waivers

**OLTP migrations SHOULD pass a static lint for blocking and destructive patterns, with explicit recorded waivers for intended exceptions.**

| Field | Value |
|---|---|
| Level | RECOMMENDED |
| Status | active |
| Decision ref | null |
| Scope | OLTP |
| Applies when | A linter exists for the engine in use |
| Rationale | Blocking and destructive DDL is easy to miss in review; lint stops it before it runs. |
| Exceptions | Waiver per rule and migration, approved by the database owner. |
| Engine notes | Existing tools cover this: Squawk (PostgreSQL), Atlas, Liquibase policy checks, strong_migrations. Atlas and Liquibase rule engines are paid. Squawk's required-field rule concerns migration safety and is not a table policy. SQLFluff is a style linter and not a safety tool. |
| Evidence | OPS-16, OPS-13, OPS-08, THIN-20, research/design_decision_matrix.md#TS-2, research/data_engineering_principles.md#CHG-20 |
| Evidence strength | multi_vendor |
| Check method | migration_lint |
| Check | Existing tool coverage. Run the linter on every migration; failures block merge unless a waiver is recorded. |
| Lifecycle stage | Governance |

### TST-003: Schema assertions in tests

**OLTP schemas SHOULD have automated assertions on structure and behaviour of critical objects, run in the delivery pipeline.**

| Field | Value |
|---|---|
| Level | RECOMMENDED |
| Status | active |
| Decision ref | null |
| Scope | OLTP |
| Applies when | A test framework exists for the engine in use |
| Rationale | Linters do not confirm that the deployed schema behaves as designed, and constraints go untested otherwise. |
| Exceptions | none |
| Engine notes | Existing tools: pgTAP, tSQLt, utPLSQL; assertions are written per object, so a schema-wide sweep needs generated tests. tSQLt warns that a faked table does not test its constraints. |
| Evidence | THIN-21, THIN-22, THIN-23, research/design_decision_matrix.md#TS-3 |
| Evidence strength | multi_vendor |
| Check method | pipeline_test |
| Check | Existing tool coverage. Confirm assertions run for critical objects and that constraint tests are not run against faked tables. |
| Lifecycle stage | Data Validation |

### TST-004: Test on a real engine

**OLTP migration and schema tests SHOULD run on a disposable instance of the same engine and version as production rather than on a mock.**

| Field | Value |
|---|---|
| Level | RECOMMENDED |
| Status | active |
| Decision ref | null |
| Scope | OLTP |
| Applies when | The engine can be provisioned for testing |
| Rationale | Engine semantics differ by version, so mocks and other engines miss real failures. |
| Exceptions | Managed engines with no disposable equivalent may use a shared test instance; approved by the database owner. |
| Engine notes | Testcontainers supplies throwaway engines and performs no checks itself; it must be paired with the tools in TST-002 and TST-003. |
| Evidence | OPS-15, THIN-25, research/design_decision_matrix.md#TS-4 |
| Evidence strength | single_vendor |
| Check method | pipeline_test |
| Check | Confirm the pipeline's test engine and version match production. |
| Lifecycle stage | Governance |

### TST-005: Production-like rehearsal

**OLTP schema changes SHOULD be rehearsed against a production-like dataset, with sensitive data masked or synthetic, and with timing compared to thresholds.**

| Field | Value |
|---|---|
| Level | RECOMMENDED |
| Status | active |
| Decision ref | null |
| Scope | OLTP |
| Applies when | A production-like dataset can be provided within data protection rules |
| Rationale | Lock duration and backfill time depend on data volume and distribution, which small fixtures hide. |
| Exceptions | Masking requirements are set by security rule SC-12, which is MANDATORY under PCI and US federal scope; those requirements are not waivable here. |
| Engine notes | GitLab uses thin clones of production for this check. DORA's test-every-change wording is confirmed in note 22. |
| Evidence | OPS-15, OPS-04, research/design_decision_matrix.md#TS-5, research/design_decision_matrix.md#SC-12, research/data_engineering_principles.md#CHG-18 |
| Evidence strength | case_study |
| Check method | pipeline_test |
| Check | Confirm the rehearsal uses masked or synthetic production-like data, and record duration and lock measurements against thresholds. |
| Lifecycle stage | Governance |

### TST-006: Schema drift detection

**Deployed schemas SHOULD be compared continuously or on a schedule with the version-controlled intended state, and differences SHOULD raise an alert.**

| Field | Value |
|---|---|
| Level | RECOMMENDED |
| Status | active |
| Decision ref | null |
| Scope | OLTP, data_warehouse |
| Applies when | always on OLTP systems; extend to warehouses where DDL is version controlled |
| Rationale | Out-of-band changes invalidate tests and can break later migrations. |
| Exceptions | none |
| Engine notes | Existing tools: Atlas drift detection; Flyway checksums guard edits to applied migrations; Prisma stops on out-of-band change; PlanetScale rejects direct DDL. EF Core's HasPendingModelChanges can back a test for a missing migration. Scope includes data_warehouse to match applies_when; matrix row TS-6 is scoped OLTP. |
| Evidence | OPS-10, research/design_decision_matrix.md#TS-6, research/data_engineering_principles.md#CHG-21 |
| Evidence strength | multi_vendor |
| Check method | catalog_query |
| Check | Existing tool coverage. Compare the live catalog with intended state and report any differences. |
| Lifecycle stage | Monitoring |

### TST-007: Custom checks for framework policies

**Framework policies that existing tools do not check, including tenant keys, money types and audit columns, SHOULD have custom automated validators.**

| Field | Value |
|---|---|
| Level | RECOMMENDED |
| Status | active |
| Decision ref | A18 |
| Scope | OLTP |
| Applies when | The schema is subject to these policies |
| Rationale | Without a validator these policies rely on review alone; no tool read ships a named rule for tenant keys, money types or audit columns. |
| Exceptions | A check may be replaced by a documented assertion suite for the affected tables; approved by the database owner. |
| Engine notes | Not-found marks in the research mean not found in the pages read and are not proof of absence. Paid rule engines (Atlas Pro, Liquibase Secure) offer custom rules. See the tool coverage table in the rules file. |
| Evidence | OPS-13, OPS-16, THIN-16, THIN-18, THIN-20, THIN-21, THIN-24, research/design_decision_matrix.md#TS-7, research/data_engineering_principles.md#CHG-20 |
| Evidence strength | multi_vendor |
| Check method | schema_lint |
| Check | Stage 3 custom validators required for tenant keys (TST-016), money types (TST-015) and audit columns (TST-017). Confirm each is implemented or waived. |
| Lifecycle stage | Data Quality |

### TST-008: Analytical model tests

**Warehouse and lakehouse models SHOULD have unique and not-null tests on their primary key, relationship tests where relevant, and unit tests for non-trivial logic.**

| Field | Value |
|---|---|
| Level | RECOMMENDED |
| Status | active |
| Decision ref | null |
| Scope | data_warehouse, lakehouse |
| Applies when | Models are built by a transformation or orchestration tool |
| Rationale | Most analytical platforms do not enforce declared keys, so tests are the available check on them. |
| Exceptions | Models without a defined grain, recorded in the model documentation. |
| Engine notes | dbt data tests and unit tests; Dagster asset checks. OLTP test tooling does not apply. |
| Evidence | LAKE-19, DQ-03, PIPE-14, research/design_decision_matrix.md#TS-8 |
| Evidence strength | single_vendor |
| Check method | pipeline_test |
| Check | Existing tool coverage. Confirm each model has key tests and that failures are reported or block as the dataset's tier requires. |
| Lifecycle stage | Data Quality |

### TST-009: Test rollback paths that exist

**Where down scripts exist, they SHOULD be tested by deploy, rollback and redeploy.**

| Field | Value |
|---|---|
| Level | RECOMMENDED |
| Status | active |
| Decision ref | null |
| Scope | OLTP |
| Applies when | The migration has a down script |
| Rationale | Complex structural and data changes are hard to roll back, and an untested rollback may fail when it is needed. |
| Exceptions | none |
| Engine notes | Liquibase documents deploy, rollback and redeploy testing, with automatic rollback limited to certain change types. Depends on the outcome of MIG-005. |
| Evidence | OPS-11, research/design_decision_matrix.md#TS-9, research/data_engineering_principles.md#CHG-15 |
| Evidence strength | single_vendor |
| Check method | pipeline_test |
| Check | Confirm the pipeline applies, reverts and re-applies migrations that declare a down path. |
| Lifecycle stage | Governance |

### TST-010: Concurrency anomaly testing

**Teams MAY run isolation anomaly tests per engine and version for correctness-critical transaction flows.**

| Field | Value |
|---|---|
| Level | OPTIONAL |
| Status | active |
| Decision ref | null |
| Scope | OLTP |
| Applies when | Correctness depends on a specific isolation guarantee |
| Rationale | Engines differ in what each isolation level prevents, and assumptions can be wrong. |
| Exceptions | none |
| Engine notes | Hermitage or Jepsen style reassessment. Jepsen tested MySQL 8.0.34, so re-check against 8.4 before relying on it. Hermitage does not state engine versions. |
| Evidence | TXN-10, TXN-11, research/design_decision_matrix.md#TS-10 |
| Evidence strength | case_study |
| Check method | pipeline_test |
| Check | Confirm any such test records the engine, version and isolation level tested. |
| Lifecycle stage | Transactions |

### TST-011: Automated change delivery

**All production schema changes SHOULD be delivered through an automated pipeline.**

| Field | Value |
|---|---|
| Level | RECOMMENDED |
| Status | active |
| Decision ref | B1 |
| Scope | all |
| Applies when | always |
| Rationale | Manual delivery bypasses the gates in TST-001. |
| Exceptions | Incident changes under MIG-001's exception. |
| Engine notes | DORA presents 100 percent automation as a capability goal; the research notes label this MANDATORY but the matrix holds it as RECOMMENDED. |
| Evidence | OPS-15, research/design_decision_matrix.md#TS-12, research/data_engineering_principles.md#CHG-17 |
| Evidence strength | case_study |
| Check method | manual_review |
| Check | Compare production migration history with pipeline runs and report changes with no pipeline record. |
| Lifecycle stage | Governance |

### TST-012: Foreign key index check

**Where the framework's indexing rule requires an index on a foreign key, the requirement SHOULD be checked automatically.**

| Field | Value |
|---|---|
| Level | RECOMMENDED |
| Status | active |
| Decision ref | null |
| Scope | OLTP |
| Applies when | The indexing standard (matrix row IX-3) requires an index for the engine and ownership case |
| Rationale | A missing index is invisible until load exposes it. Whether one is needed depends on the engine and who creates it. |
| Exceptions | As set by the indexing standard. |
| Engine notes | Existing tools cover this: Schemalint index-referencing-column and prisma-lint require-field-index are built in; Atlas has a Pro custom rule; pgTAP asserts per object. EF Core creates the index by convention. GitLab requires it only inside GitLab. Squawk's foreign key rule concerns locks and does not check indexes. |
| Evidence | THIN-12, THIN-14, THIN-16, THIN-21, THIN-24, OPS-13, research/design_decision_matrix.md#TS-13 |
| Evidence strength | multi_vendor |
| Check method | catalog_query |
| Check | Existing tool coverage. Report foreign keys lacking a supporting index where the indexing standard requires one. |
| Lifecycle stage | Data Quality |

### TST-013: Primary key and required-column check

**Primary key presence and framework-required columns SHOULD be checked automatically.**

| Field | Value |
|---|---|
| Level | RECOMMENDED |
| Status | active |
| Decision ref | null |
| Scope | OLTP |
| Applies when | The schema is subject to these policies |
| Rationale | A table without a primary key or a required column passes review easily and is costly to fix later. |
| Exceptions | As set by the integrity and audit standards. |
| Engine notes | Existing tools cover this: Schemalint and prisma-lint built in; Atlas custom (Pro); pgTAP assertions. prisma-lint reads schema files and Schemalint reads a live catalog. Liquibase built-in check lists returned 404, so they are not cited. |
| Evidence | THIN-16, THIN-21, THIN-24, OPS-13, research/design_decision_matrix.md#TS-14 |
| Evidence strength | multi_vendor |
| Check method | catalog_query |
| Check | Existing tool coverage. Report tables lacking a primary key or a framework-required column. |
| Lifecycle stage | Data Quality |

### TST-014: Reserved word check

**Identifiers MAY be checked against reserved words for the target engine, beyond what the engine itself rejects.**

| Field | Value |
|---|---|
| Level | OPTIONAL |
| Status | active |
| Decision ref | A18 |
| Scope | all |
| Applies when | Identifiers may move between engines or dialects |
| Rationale | A word reserved in another dialect can break a later port, and existing tool coverage is thin. |
| Exceptions | none |
| Engine notes | SQLFluff RF04 is the only linter rule found; it is partial and dialect-dependent and excludes reserved keywords from its own scope. A full check needs a custom Stage 3 validator using each engine's reserved word list. |
| Evidence | THIN-15, THIN-18, research/design_decision_matrix.md#TS-15, research/data_engineering_principles.md#Reserved words |
| Evidence strength | single_vendor |
| Check method | schema_lint |
| Check | Partial tool coverage; Stage 3 custom validator needed for full coverage. Compare identifiers with reserved word lists for each target engine. |
| Lifecycle stage | Data Quality |

### TST-015: Money type check

**Columns holding money SHOULD be checked automatically against the framework's approved money types.**

| Field | Value |
|---|---|
| Level | RECOMMENDED |
| Status | active |
| Decision ref | A18 |
| Scope | OLTP |
| Applies when | The schema holds monetary values and the data types standard defines the approved types |
| Rationale | Inexact money columns cause rounding errors that review can miss; no built-in money rule was found in any tool read. |
| Exceptions | none |
| Engine notes | Generic routes only: pgTAP col_type_is per column, tSQLt schema comparison, prisma-lint require-field-type by field name. Identifying which columns hold money needs a framework convention or metadata. The class is the matrix's and applies to the checking mechanism; the money-type requirement belongs to the data types standard. Level raised from OPTIONAL to RECOMMENDED by owner decision A18, a recorded departure from the matrix; evidence_strength is unchanged. |
| Evidence | THIN-21, THIN-22, THIN-24, research/design_decision_matrix.md#TS-16, research/data_engineering_principles.md#Money types |
| Evidence strength | inference |
| Check method | catalog_query |
| Check | Stage 3 custom validator required, built as an engine-neutral catalog query. Identify money columns from metadata or convention and report any column not using an approved type. |
| Lifecycle stage | Data Quality |

### TST-016: Tenant key check

**Tenant-scoped tables SHOULD be checked automatically for the framework's tenant key.**

| Field | Value |
|---|---|
| Level | RECOMMENDED |
| Status | active |
| Decision ref | A18 |
| Scope | OLTP |
| Applies when | The system is multi-tenant in a shared schema or database |
| Rationale | A missing tenant column can expose one tenant's data to another; no tool read ships a rule named for tenant keys. |
| Exceptions | Tables marked as shared or global by the tenancy standard. |
| Engine notes | Generic routes only: Schemalint mandatory-columns, prisma-lint require-field (its documentation uses tenantId as an example), Atlas predicates (Pro), pgTAP has_column. Schemalint row-level-security and Atlas ensure-row-security-enabled check row-level security, which is a different check. The class applies to the checking mechanism; the tenant key requirement belongs to the tenancy standard. Level raised from OPTIONAL to RECOMMENDED by owner decision A18, a recorded departure from the matrix; evidence_strength is unchanged. |
| Evidence | THIN-16, THIN-21, THIN-24, OPS-13, research/design_decision_matrix.md#TS-17, research/data_engineering_principles.md#Tenant keys |
| Evidence strength | inference |
| Check method | catalog_query |
| Check | Stage 3 custom validator required, built as an engine-neutral catalog query. Report tenant-scoped tables lacking the tenant key, excluding approved global tables. |
| Lifecycle stage | Data Quality |

### TST-017: Audit column check

**Tables subject to the audit standard SHOULD be checked automatically for the framework's required audit columns.**

| Field | Value |
|---|---|
| Level | RECOMMENDED |
| Status | active |
| Decision ref | A18 |
| Scope | OLTP |
| Applies when | The audit standard requires audit columns on the table |
| Rationale | A missing audit column loses history that cannot be recovered later; no tool read has a rule named for audit columns. |
| Exceptions | As set by the audit standard. |
| Engine notes | Required-column rules are the available mechanism; this use is inference from the research, with no document showing it. The matrix has no row for this check; the level matches the sibling rows TS-16 and TS-17. Level raised from OPTIONAL to RECOMMENDED by owner decision A18, a recorded departure from the matrix; evidence_strength is unchanged. |
| Evidence | THIN-16, THIN-21, THIN-24, research/data_engineering_principles.md#Audit columns |
| Evidence strength | inference |
| Check method | catalog_query |
| Check | Stage 3 custom validator required, built as an engine-neutral catalog query. Report tables in audit scope lacking a required audit column. |
| Lifecycle stage | Data Quality |

## Backup, recovery and disaster recovery (BDR)

### BDR-001: Recovery objectives from BIA, NIST-governed systems

**NIST-governed systems MUST define RTO, RPO and MTD from a business impact analysis.**

| Field | Value |
|---|---|
| Level | MANDATORY |
| Status | provisional |
| Decision ref | null |
| Scope | all |
| Applies when | US federal information systems, or systems bound to NIST SP 800-34 by regulation or contract |
| Rationale | Without BIA-derived objectives, recovery design has no target. Requires legal review to confirm applicability for a given system. |
| Exceptions | Requires legal review of applicability; none otherwise. |
| Engine notes | none |
| Evidence | OPS-17, research/design_decision_matrix.md#BK-1, research/data_engineering_principles.md#DR-01 |
| Evidence strength | standard |
| Check method | manual_review |
| Check | Confirm a current BIA exists and that RTO is shorter than MTD. |
| Lifecycle stage | Governance |

### BDR-002: Recovery objectives from BIA, other systems

**Production systems outside NIST governance SHOULD define RTO, RPO and MTD from a business impact analysis.**

| Field | Value |
|---|---|
| Level | RECOMMENDED |
| Status | active |
| Decision ref | null |
| Scope | all |
| Applies when | Production systems not covered by BDR-001 |
| Rationale | AWS and Google tie recovery design to stated objectives; assumed objectives surface only during an outage. |
| Exceptions | Non-critical systems with a recorded owner acceptance of data loss. |
| Engine notes | ISO 22301:2019 is known to this research only through the EVS national record and is cited as such. The research notes label this MANDATORY for all production; the matrix holds it RECOMMENDED outside NIST-governed systems. |
| Evidence | OPS-17, OPS-21, CLOUD-10, research/design_decision_matrix.md#BK-1, research/data_engineering_principles.md#DR-01 |
| Evidence strength | multi_vendor |
| Check method | manual_review |
| Check | Confirm RTO, RPO and MTD are recorded per system with their BIA basis. |
| Lifecycle stage | Governance |

### BDR-003: Point-in-time recovery foundation

**Systems requiring point-in-time recovery MUST take physical or snapshot-based base backups and continuously archive the transaction log.**

| Field | Value |
|---|---|
| Level | MANDATORY |
| Status | active |
| Decision ref | null |
| Scope | OLTP |
| Applies when | Point-in-time recovery is required by the system's RPO |
| Rationale | Snapshots or dumps alone can recover only to the moment they were taken. |
| Exceptions | none |
| Engine notes | PostgreSQL: WAL level replica or higher; test archiving before the first base backup; archive commands must not overwrite and must report success correctly. MySQL: binary logging on, the 8.4 default. Oracle: ARCHIVELOG mode; backups taken in NOARCHIVELOG are unusable after switching ([WF] re-check against the page). SQL Server: full recovery with log backups. MongoDB: only Cloud and Ops Manager give point-in-time restore with guaranteed sharded consistency. Managed services differ; Cloud SQL point-in-time restore creates a new instance. That RPO is bounded by log archive frequency is inference. |
| Evidence | PGMY-11, PGMY-19, OPS-19, OPS-20, research/design_decision_matrix.md#BK-2, research/data_engineering_principles.md#BCK-02, research/official_documentation.md#point-in-time recovery needs physical |
| Evidence strength | multi_vendor |
| Check method | runtime_monitor |
| Check | Confirm base backups and log archiving are running without gaps, and that a recovery to a chosen time has succeeded. |
| Lifecycle stage | Monitoring |

### BDR-004: Logical dumps supplement physical backups

**Logical dumps SHOULD be used only as a supplement to physical backups, for portability and partial restore.**

| Field | Value |
|---|---|
| Level | RECOMMENDED |
| Status | active |
| Decision ref | null |
| Scope | OLTP |
| Applies when | Physical backups are available for the engine |
| Rationale | Logical dumps are not a point-in-time recovery solution, and Oracle states they are insufficient alone. |
| Exceptions | Small MongoDB deployments, where mongodump is described as suitable; other small systems with the owner's recorded acceptance. |
| Engine notes | PostgreSQL pg_dump is the cross-version method and cannot be a PITR base. MySQL physical backups are faster but hardware-bound. File copies alone are not valid for InnoDB. Percona XtraBackup 8.0 reached end of life in June 2026. |
| Evidence | PGMY-19, OPS-20, research/design_decision_matrix.md#BK-3, research/architecture_comparison.md#C-49, research/data_engineering_principles.md#BCK-04, research/data_engineering_principles.md#C11 |
| Evidence strength | multi_vendor |
| Check method | manual_review |
| Check | Confirm the backup plan does not rely on logical dumps as its only recovery method. |
| Lifecycle stage | Monitoring |

### BDR-005: Replicas are not backups

**Replicas and standbys MUST NOT be counted as a substitute for separate backups.**

| Field | Value |
|---|---|
| Level | MANDATORY |
| Status | active |
| Decision ref | null |
| Scope | all |
| Applies when | The system's data is not reproducible from another source |
| Rationale | Replication can carry corruption and malicious deletion to every copy. |
| Exceptions | none |
| Engine notes | SQL Server is the only database engine that states this explicitly; AWS states it for replication generally and says active-active still needs backups; Oracle Data Guard guidance offloads backups to a standby instead of replacing them. Matrix row BK-4 also cites OPS-20, but official_documentation.md section 16 finds that page concerns logical against physical backups, so it is omitted here. |
| Evidence | MSOM-07, OPS-21, research/design_decision_matrix.md#BK-4, research/architecture_comparison.md#C-50, research/data_engineering_principles.md#BCK-05 |
| Evidence strength | multi_vendor |
| Check method | manual_review |
| Check | Confirm every system with replicas also has independent backups. |
| Lifecycle stage | Monitoring |

### BDR-006: Table history is not backup

**Time travel, table history and platform-internal recovery features MUST NOT be the only recovery mechanism for warehouse or lakehouse data that must be recoverable beyond the feature's retention window.**

| Field | Value |
|---|---|
| Level | MANDATORY |
| Status | active |
| Decision ref | null |
| Scope | lakehouse, data_warehouse |
| Applies when | The data is not reproducible from sources within the system's RTO |
| Rationale | These windows are bounded and some features are not accessible to customers. |
| Exceptions | Data fully reproducible from retained sources, recorded by the data owner. |
| Engine notes | Databricks says not to use table history for long-term archival, and raising retention raises storage cost. Snowflake Fail-safe is for Snowflake's use only and not an access path to history; Time Travel retention is bounded. |
| Evidence | LAKE-11, research/design_decision_matrix.md#BK-13, research/architecture_comparison.md#U7, research/data_engineering_principles.md#BCK-06 |
| Evidence strength | multi_vendor |
| Check method | manual_review |
| Check | Confirm a separate backup or reproducibility record exists for each dataset needing recovery beyond the window. |
| Lifecycle stage | Monitoring |

### BDR-007: Restores are tested and verified

**Every backup strategy MUST include scheduled restore tests whose results are verified for consistency.**

| Field | Value |
|---|---|
| Level | MANDATORY |
| Status | active |
| Decision ref | null |
| Scope | all |
| Applies when | always, for systems of record and for warehouse or lakehouse data not reproducible from sources |
| Rationale | A backup that has not been restored is unproven, and GitLab's January 31 outage postmortem showed backups can be unusable when they are needed. |
| Exceptions | none |
| Engine notes | SQL Server: restore to a test system and check consistency. The test frequency is not set by any source read and is left to each system's RTO and RPO. OPS-22 was read earlier and was bot-blocked at the 2026-11-08 link check. |
| Evidence | OPS-17, OPS-19, OPS-22, CLOUD-10, CASE-51, research/design_decision_matrix.md#BK-5, research/data_engineering_principles.md#BCK-01 |
| Evidence strength | standard |
| Check method | runtime_monitor |
| Check | Report the date and result of the latest verified restore per system and alert when one is overdue. |
| Lifecycle stage | Monitoring |

### BDR-008: Restore tests cover the application stack

**Restoration tests SHOULD cover the whole application stack and be judged on integrity, RTO and RPO.**

| Field | Value |
|---|---|
| Level | RECOMMENDED |
| Status | active |
| Decision ref | null |
| Scope | all |
| Applies when | The application depends on more than one data store or service |
| Rationale | A database that restores cleanly can still leave the application unusable. |
| Exceptions | Systems with no dependent application. |
| Engine notes | Stated by Google only; official_documentation.md section 15 records it as not yet a general rule. AWS requires failover testing, which is a different activity. |
| Evidence | CLOUD-10, research/official_documentation.md#Restoration tests covering the whole application stack |
| Evidence strength | single_vendor |
| Check method | manual_review |
| Check | Confirm restore test reports include application-level checks and integrity, RTO and RPO results. |
| Lifecycle stage | Monitoring |

### BDR-009: Recovery rehearsed and timed

**Full recovery SHOULD be rehearsed regularly and its duration measured against RTO.**

| Field | Value |
|---|---|
| Level | RECOMMENDED |
| Status | active |
| Decision ref | B1 |
| Scope | all |
| Applies when | The system has a stated RTO |
| Rationale | GitHub found large cluster restores slow and not fully rehearsed; an unmeasured RTO is an assumption. |
| Exceptions | none |
| Engine notes | data_engineering_principles.md DR-03 reports that AWS and Azure advise periodic testing, but official_documentation.md section 16 narrows the cloud claims on restore testing, so neither is relied on here. The research notes label rehearsal MANDATORY for all production; the matrix holds it as RECOMMENDED. |
| Evidence | CASE-52, CASE-51, research/design_decision_matrix.md#BK-11, research/data_engineering_principles.md#DR-03 |
| Evidence strength | case_study |
| Check method | runtime_monitor |
| Check | Report measured recovery duration from the latest rehearsal against RTO. |
| Lifecycle stage | Monitoring |

### BDR-010: Backup schedule meets RPO

**Backup and log archive schedules SHOULD be set to meet the system's RPO.**

| Field | Value |
|---|---|
| Level | RECOMMENDED |
| Status | active |
| Decision ref | null |
| Scope | all |
| Applies when | The system has a stated RPO |
| Rationale | A schedule set by habit can miss the data-loss limit the business has accepted. |
| Exceptions | none |
| Engine notes | Stated by Google; AWS ties strategy to objectives. AWS tier ranges are in a figure and were not captured, so no numbers are given. |
| Evidence | CLOUD-10, OPS-21, research/official_documentation.md#Schedule backups to the RPO, research/design_decision_matrix.md#BK-1 |
| Evidence strength | single_vendor |
| Check method | runtime_monitor |
| Check | Compare the actual interval between backups or archived logs with the RPO. |
| Lifecycle stage | Monitoring |

### BDR-011: Named owner for restore capability

**Each system SHOULD have a named owner for its backup and restore capability.**

| Field | Value |
|---|---|
| Level | RECOMMENDED |
| Status | active |
| Decision ref | null |
| Scope | all |
| Applies when | always |
| Rationale | GitLab's backup failure was attributed to lack of ownership. |
| Exceptions | none |
| Engine notes | none |
| Evidence | CASE-51, research/design_decision_matrix.md#BK-6 |
| Evidence strength | case_study |
| Check method | manual_review |
| Check | Confirm each system records an owner for restore capability. |
| Lifecycle stage | Governance |

### BDR-012: 3-2-1 baseline with an offline copy

**Backups SHOULD follow the 3-2-1 baseline and SHOULD keep an offline, encrypted copy that is tested regularly.**

| Field | Value |
|---|---|
| Level | RECOMMENDED |
| Status | active |
| Decision ref | B7 |
| Scope | all |
| Applies when | Systems of record with ransomware exposure |
| Rationale | Ransomware variants try to find and delete or encrypt accessible backups. |
| Exceptions | Offline copy may be replaced by an approved immutable copy under BDR-013; approved by the security owner. |
| Engine notes | 3-2-1 comes from CISA Data Backup Options, not from OPS-22. OPS-22 is the source for offline, encrypted copies. The research notes label the offline copy MANDATORY; the matrix holds this row as RECOMMENDED. |
| Evidence | OPS-22, research/design_decision_matrix.md#BK-7, research/data_engineering_principles.md#BCK-08, research/data_engineering_principles.md#BCK-09 |
| Evidence strength | standard |
| Check method | manual_review |
| Check | Confirm copy count, media or location separation, and the last test of the offline copy. |
| Lifecycle stage | Monitoring |

### BDR-013: Immutable backup copy

**Systems MAY hold an immutable backup copy in addition to the baseline; the accepted default is one immutable copy for systems of record, with compliance and misconfiguration reviewed.**

| Field | Value |
|---|---|
| Level | OPTIONAL |
| Status | active |
| Decision ref | B7 |
| Scope | all |
| Applies when | Ransomware exposure is in scope |
| Rationale | Immutability resists deletion, but the only strong promotion is vendor marketing and CISA adds cautions on compliance and misconfiguration (conflict C12), so the default is a judgment. |
| Exceptions | Deviation from the accepted default needs a recorded reason approved by the framework exception approver. |
| Engine notes | Veeam's 3-2-1-1-0 extension is vendor marketing. Azure SQL guidance mentions backup immutability. Check erasure handling under RET-026, which stays provisional. |
| Evidence | OPS-22, research/design_decision_matrix.md#BK-7, research/architecture_comparison.md#C-51, research/data_engineering_principles.md#C12 |
| Evidence strength | single_vendor |
| Check method | manual_review |
| Check | Confirm that any immutable copy has a reviewed retention setting and that its legal effect has been considered. |
| Lifecycle stage | Monitoring |

### BDR-014: Backups encrypted, separated, least privilege

**Backups SHOULD be encrypted, stored separately from primary systems, and accessible only with least privilege.**

| Field | Value |
|---|---|
| Level | RECOMMENDED |
| Status | active |
| Decision ref | null |
| Scope | all |
| Applies when | always |
| Rationale | Backups held beside the primary fail with it and expose the same data if compromised. |
| Exceptions | none |
| Engine notes | Separate accounts or regions protect against compromise (AWS). Managed services differ on what survives deletion of the instance, so confirm per service. The research notes label this MANDATORY; the matrix holds it as RECOMMENDED. |
| Evidence | OPS-19, SEC-08, OPS-17, research/design_decision_matrix.md#BK-8, research/data_engineering_principles.md#BCK-07, research/data_engineering_principles.md#BCK-10 |
| Evidence strength | standard |
| Check method | manual_review |
| Check | Confirm encryption, separate storage location and access lists for backups. |
| Lifecycle stage | Monitoring |

### BDR-015: Backup keys recoverable

**Keys or certificates needed to decrypt backups SHOULD be stored separately from the backups and be available during recovery.**

| Field | Value |
|---|---|
| Level | RECOMMENDED |
| Status | active |
| Decision ref | null |
| Scope | all |
| Applies when | Backups or the database are encrypted |
| Rationale | Encrypted backups are unrecoverable without their keys. |
| Exceptions | none |
| Engine notes | SQL Server states that certificates must be backed up when TDE is used. The matrix has no separate row; this follows the level of BK-8. |
| Evidence | OPS-17, SEC-24, research/data_engineering_principles.md#BCK-07, research/official_documentation.md#back up the certificates |
| Evidence strength | standard |
| Check method | manual_review |
| Check | Confirm key location, separation from backups, and inclusion of keys in restore tests. |
| Lifecycle stage | Monitoring |

### BDR-016: DR tier chosen from BIA

**Each system MAY select a disaster recovery tier from backup and restore, pilot light, warm standby or active/active, based on its RTO, RPO and cost.**

| Field | Value |
|---|---|
| Level | OPTIONAL |
| Status | active |
| Decision ref | null |
| Scope | all |
| Applies when | A BIA exists under BDR-001 or BDR-002 |
| Rationale | Choosing a tier without the objectives either overspends or misses them. |
| Exceptions | none |
| Engine notes | AWS names four tiers; NIST names cold, warm, hot, mobile and mirrored sites. RPO and RTO figures per tier were not captured, so none are stated. On Azure SQL, geo-restore is the most basic option and failover groups are advised for business-critical applications. |
| Evidence | OPS-17, OPS-21, research/design_decision_matrix.md#BK-9, research/data_engineering_principles.md#DR-02, research/data_engineering_principles.md#DR-04 |
| Evidence strength | standard |
| Check method | manual_review |
| Check | Confirm the chosen tier is recorded and traced to the objectives. |
| Lifecycle stage | Governance |

### BDR-017: Failover topology constraints encoded

**OLTP failover automation SHOULD encode topology constraints that prevent divergent writes.**

| Field | Value |
|---|---|
| Level | RECOMMENDED |
| Status | active |
| Decision ref | null |
| Scope | OLTP |
| Applies when | Automated failover is in use across sites or regions |
| Rationale | Divergent writes were the costliest failure in GitHub's 2018 incident. |
| Exceptions | none |
| Engine notes | Evidence is one operator's MySQL topology. |
| Evidence | CASE-52, CASE-53, research/design_decision_matrix.md#BK-10 |
| Evidence strength | case_study |
| Check method | manual_review |
| Check | Confirm failover automation documents which promotions it refuses, and that this was tested. |
| Lifecycle stage | Monitoring |

### BDR-018: Per-tenant restore approach

**Multi-tenant systems MAY provide per-tenant restore through tenant-isolated databases or selective recovery from a side copy.**

| Field | Value |
|---|---|
| Level | OPTIONAL |
| Status | active |
| Decision ref | null |
| Scope | OLTP |
| Applies when | The tenancy model or contracts call for restoring a single tenant |
| Rationale | In a shared pool, restoring one tenant by rolling back the whole database harms all others. |
| Exceptions | none |
| Engine notes | Silo databases restore in place; pool models need selective recovery. Evidence is Azure guidance. No source quantifies effort. |
| Evidence | CLOUD-18, CLOUD-19, research/design_decision_matrix.md#BK-12 |
| Evidence strength | single_vendor |
| Check method | manual_review |
| Check | Confirm the tenant restore method is documented and has been tested for a sample tenant. |
| Lifecycle stage | Monitoring |

### BDR-019: Verify state after recovery

**After recovery, the database SHOULD be inspected to confirm it reached the desired state before service resumes.**

| Field | Value |
|---|---|
| Level | RECOMMENDED |
| Status | active |
| Decision ref | null |
| Scope | all |
| Applies when | Any recovery event or rehearsal |
| Rationale | A recovery that stopped at the wrong point can return bad data to service. |
| Exceptions | none |
| Engine notes | PostgreSQL advises verifying the desired state. Reconciling derived stores against the restored source is inference. |
| Evidence | PGMY-11, research/data_engineering_principles.md#DR-05 |
| Evidence strength | single_vendor |
| Check method | manual_review |
| Check | Confirm the recovery runbook has a state-check step and a record of its result. |
| Lifecycle stage | Monitoring |

### BDR-020: Pipeline state in DR planning

**DR plans for systems with change data capture SHOULD include replication slots and connector offsets.**

| Field | Value |
|---|---|
| Level | RECOMMENDED |
| Status | provisional |
| Decision ref | null |
| Scope | OLTP, streaming |
| Applies when | Change data capture reads from the recovered database |
| Rationale | Slots and offsets are bound to a database's history, so a recovery or failover can lose or repeat changes. |
| Exceptions | none |
| Engine notes | Debezium warns that dropping a slot on the primary loses data. The DR scope is inference, and no source read covers re-establishing CDC after failover. The research notes label this MANDATORY; an inference-only rule cannot be MANDATORY. |
| Evidence | PIPE-06, research/data_engineering_principles.md#DR-06 |
| Evidence strength | inference |
| Check method | manual_review |
| Check | Confirm the DR plan lists CDC slots and offsets and the steps to re-establish them. |
| Lifecycle stage | Monitoring |

### BDR-021: CDC re-established after failover

**After a database failover or restore, change data capture SHOULD be re-established by a documented procedure that confirms each replication slot and connector offset matches the recovered database before consumers resume.**

| Field | Value |
|---|---|
| Level | RECOMMENDED |
| Status | provisional |
| Decision ref | null |
| Scope | OLTP, streaming |
| Applies when | Change data capture reads from a database that has failed over or been restored |
| Rationale | Slots and offsets bind to one database history, so resuming capture without checking them can lose or repeat changes. No source read covers re-establishing CDC after failover; this is an inference. |
| Exceptions | none |
| Engine notes | Inference only, from Debezium's warning that dropping a slot on the primary loses data and from DR-06. No engine procedure was researched. BDR-020 puts slots and offsets in the DR plan; this rule covers the recovery step. |
| Evidence | PIPE-06, research/data_engineering_principles.md#DR-06 |
| Evidence strength | inference |
| Check method | manual_review |
| Check | Confirm the recovery procedure has this step, and that a rehearsal shows consumers resume without loss or duplication. |
| Lifecycle stage | Monitoring |

## Classification record

RULE_FORMAT requires following the matrix and recording any change. Rows below record the position before the owner decisions of 2026-11-08. Each rule's level, status and decision_ref fields show the current position.

| Rule | Matrix | Other research | Applied here | Reason |
|---|---|---|---|---|
| MIG-001, MIG-002, MIG-004, MIG-005, MIG-007, MIG-009, MIG-019; TST-005, TST-011 | RECOMMENDED, or no row | `data_engineering_principles.md` labels CHG-01 to CHG-05, CHG-08, CHG-10, CHG-14, CHG-17, CHG-18, CHG-23 as MANDATORY | RECOMMENDED | Matrix followed: no standards body covers this area |
| BDR-002, BDR-009, BDR-012, BDR-014 | RECOMMENDED | DR-01, DR-03, BCK-07, BCK-08 labelled MANDATORY | RECOMMENDED | Matrix followed |
| BDR-001, BDR-002 | One row, BK-1, with two classes | | Split into two rules | The level field holds one value; the row binds two populations |
| BDR-005 | MANDATORY citing MSOM-07, OPS-20, OPS-21 | `official_documentation.md` section 16 finds the Oracle evidence is about logical against physical backups | MANDATORY; OPS-20 removed | **Change from matrix.** The MANDATORY level still rests on Microsoft and AWS |
| BDR-007 | MANDATORY citing OPS-17, OPS-19, OPS-22, CLOUD-10, CASE-51 | `official_documentation.md` narrows the claim about all three cloud frameworks | MANDATORY; OPS-21 not cited | Matches the matrix source list. Whole-stack scope is split out as BDR-008, single vendor |
| BDR-020 | No row | DR-06 labelled MANDATORY with an inference basis | RECOMMENDED, provisional | Inference-only rules cannot be MANDATORY |
| BDR-015 | No row | SQL Server states MANDATORY when TDE is used | RECOMMENDED | Follows the level of BK-8 |
| TST-015, TST-016, TST-017 | OPTIONAL | TS-7 is RECOMMENDED | RECOMMENDED | **Change from matrix.** Owner decision A18 (2026-11-08) raised the level to build the validators. Evidence strength is unchanged |

Merged rows: MG-12 and TS-11 form MIG-016. Conflicts C2, C5 and C11 are context, version or layering differences and are resolved inside the rules, so they carry no decision.

## Unsupported or thin

- No source read sets a restore test frequency, or backup retention periods; `research_gaps.md` records that none quantifies legal retention for database backups. No rule sets them.
- Erasure from backups is unsettled and requires legal review. It is not addressed here.
- RPO and RTO figures per DR tier were not captured, so none are given.
- No independent evidence supports any lock budget value, and no source quantifies developer-authored against DBA-authored migrations.
- No source read covers re-establishing CDC after failover.
- Sources without catalog IDs are cited through their research sections: Atlas drift detection, pt-online-schema-change, Delta history, PostgreSQL dump, Veeam, Rails and Django guides, Flyway undo, Oracle Data Guard, Azure SQL restore and Google's restore-testing page.
- Re-check before relying on them: the MySQL online DDL matrix and Oracle ARCHIVELOG detail ([WF]), Hudi promotion matrix (reconstructed text), CASE-27 (2014) and OPS-07 (PostgreSQL 9.1 to 12), TXN-11 (MySQL 8.0.34). OPS-14 and OPS-22 were bot-blocked at the 2026-11-08 link check, though read earlier.

## Decisions needing owner approval

Answered by the owner on 2026-11-08: all defaults accepted. See `../DECISIONS_TO_APPROVE.md` for the decision log, and each rule's decision_ref for its decision number. Questions and alternatives are kept for the record.

| ID | Rules | Question | Proposed default | Alternatives | Consequence of each |
|---|---|---|---|---|---|
| D1 | MIG-005 | Must migrations be reversible? | Forward-only with compatibility; down scripts optional and tested | (a) Reversible by default with exceptions, as GitLab does. (b) Backup restore as the only rollback | Default: fewer scripts, but needs expand and contract discipline. (a): more authoring and false assurance for drops and data changes. (b): simplest, but restore means downtime and loss since the backup |
| D2 | MIG-003 | Which authoring model? | Hybrid with checked-in plan. Judgment; no benchmark | (a) Migration-based only. (b) State-based only | Default: needs tooling and plan review. (a): accumulates history but handles renames explicitly. (b): least authoring, risks data loss on renames |
| D3 | MIG-008 | What default lock and runtime budgets? | Set per system from rehearsal, with no framework-wide number. Judgment | (a) Adopt about 2 s lock hold (Braintree). (b) Adopt 10 s lock timeout (strong_migrations). (c) Adopt GitLab's 15 s statement timeout | Default: fits each system but needs measurement. (a): strictest, more retries. (b): looser, longer queueing. (c): limits statements, not lock hold, and is GitLab-specific |
| D4 | MIG-011 | Which online tool for MySQL-family large tables? | Log-based (gh-ost) unless constraints rule it out. Judgment; both projects describe themselves | (a) Trigger-based (pt-online-schema-change). (b) Platform workflow where offered | Default: avoids trigger overhead, depends on binlog access. (a): works where binlog access is limited, cannot run on tables with triggers. (b): least operational work, ties to the platform |
| D5 | MIG-013 | Where do small data changes go? | Separate reviewed data migration in the same history | (a) Inside the schema migration. (b) Outside migrations entirely | Default: traceable, one more artifact. (a): simple, holds locks longer. (b): keeps migrations pure, loses ordering with schema |
| D6 | MIG-014 | One transaction per migration or per DDL? | Per DDL on high-traffic OLTP; per migration elsewhere | (a) Per migration always. (b) Per DDL always | Default: needs a traffic classification. (a): atomic, holds several locks at once. (b): shortest locks, partial failure needs manual repair |
| D7 | BDR-013 | Is an immutable backup copy required? | One immutable copy for systems of record, with review of compliance and misconfiguration. Judgment | (a) Offline copy only, as in BDR-012. (b) Adopt 3-2-1-1-0 | Default: resists deletion, adds cost and may conflict with erasure duties. (a): cheaper, slower to restore. (b): most protection, rests on vendor marketing |
| D8 | TST-007, TST-014 to TST-017 | Which validators does Stage 3 build? | Build tenant key, money type and audit column checks as engine-neutral catalog queries; raise TST-015 to TST-017 to RECOMMENDED | (a) Keep them OPTIONAL and build on demand. (b) Buy Atlas Pro or Liquibase Secure custom rules | Default: no license cost, Stage 3 owns upkeep; raising the level departs from the matrix and must be recorded. (a): least work, policies rest on review. (b): less code, license cost and fewer engines |
| D9 | MIG-001, MIG-002, TST-011, BDR-009 | Promote core practices to framework-level MANDATORY? | Keep RECOMMENDED until the owner decides | Promote as framework-internal MANDATORY with status `needs_decision`, as RULE_FORMAT allows | Default: follows the matrix, leaves enforcement discretionary. Promote: firm gate for ERP and financial systems, but the basis is an organizational choice and not an external authority |
