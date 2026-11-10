# Stage 2 Standards: Naming Conventions and Data Types

Group 02. Rule prefixes: NAM (naming conventions), TYP (data types and precision). The registry form is `../registry/02_naming_and_data_types.json`. Rule format: `../RULE_FORMAT.md`.

All content comes from the existing files in `../../research/`. No sources were added. This file contains no schemas, DDL or code.

Naming patterns appear only in the pattern table below. Rules refer to them by NP number. The owner accepted all defaults on 2026-11-08, so decided style rules are organizational decisions and active. Style rules use SHOULD because `design_decision_matrix.md` says style rules are not MANDATORY. The owner may raise an approved style rule to MANDATORY within this framework, as `RULE_FORMAT.md` permits.

## Portable identifier length: derivation

The ceiling used by NAM-010 is the lowest current limit across the engines in the research. Limits are counted in different units, so NAM-006 (ASCII only) is what makes one character equal one byte.

| Engine | Limit | Unit | Note |
|---|---|---|---|
| PostgreSQL | 63 | bytes, by default | Longer names are truncated. **This sets the ceiling.** |
| MySQL 8.4 | 64 | characters | Databases, tables, columns, indexes and constraints |
| SQL Server | 128 | characters | 116 for local temporary tables |
| Oracle, COMPATIBLE 12.2 or higher | 128 | bytes | Database names are limited to 8 bytes |
| Snowflake | 255 | characters | Quoted or not |
| Databricks Unity Catalog | 255 | characters, object names | Column-name limit not confirmed |

**Result: 63 ASCII characters.** Excluded from the calculation: Oracle below COMPATIBLE 12.2 (30 bytes), which applies only if such a system is in the estate (C-22); and MongoDB, whose limit is on namespaces and whose field-name length was not captured. Sources: `database_design_standards.md` section 6.1; `official_documentation.md` hard limits sections 2 to 5, 10 and 11.

## Naming pattern table

Angle brackets are placeholders. Singular or plural inside a placeholder follows NAM-013 (accepted default: plural tables, singular within key names). Every row is subject to the length ceiling in NAM-010. Basis is the strongest support in the research; "Proposal" means no source states the pattern.

| ID | Object | Pattern | Example | Basis | Status |
|---|---|---|---|---|---|
| NP-01 | Table or view | `<entity_plural>` | `sales_orders` | Split sources (C-26); judgment | active |
| NP-02 | Primary key column | `<entity_singular>_id` | `customer_id` | dbt, sqlstyle | active |
| NP-03 | Foreign key column | `<parent_singular>_id` | `customer_id` | dbt, GitLab | active |
| NP-04 | Role-qualified foreign key | `<role>_<parent_singular>_id` | `billing_customer_id` | Proposal | active |
| NP-05 | Third-party identifier | `<source_or_concept>_xid` | `payment_provider_xid` | GitLab (one organization) | active |
| NP-06 | Boolean column | `is_<adjective>` or `has_<noun>` | `is_active`, `has_attachment` | dbt, Alibaba | active |
| NP-07 | Instant column | `<past_tense_event>_at` | `posted_at` | dbt | active |
| NP-08 | Calendar date column | `<event>_date` | `invoice_date` | dbt | active |
| NP-09 | Local wall-clock column | `<event>_local_datetime` | `appointment_local_datetime` | Proposal | provisional |
| NP-10 | Source time zone column | `<event>_time_zone` | `appointment_time_zone` | Proposal | provisional |
| NP-11 | Status column | `<lifecycle>_status` | `approval_status` | Proposal | active |
| NP-12 | Monetary amount column | `<measure>_amount` | `net_amount` | Proposal | active |
| NP-13 | Currency code column | `currency_code` or `<measure>_currency_code` | `net_currency_code` | Proposal | active |
| NP-14 | Integer minor-unit amount | `<measure>_in_<minor_unit>` | `price_in_cents` | dbt | active |
| NP-15 | Quantity column and its unit | `<measure>_quantity` with `<measure>_unit` | `shipped_quantity`, `shipped_unit` | Proposal | active |
| NP-16 | Primary key constraint | `pk_<table>` | `pk_sales_orders` | GitLab prefix (binds there only) | active |
| NP-17 | Foreign key constraint | `fk_<table>_<column>` | `fk_sales_orders_customer_id` | GitLab prefix | active |
| NP-18 | Unique constraint | `unique_<table>_<columns>` | `unique_customers_tax_number` | GitLab prefix | active |
| NP-19 | Check constraint | `check_<table>_<rule>` | `check_sales_orders_positive_total` | GitLab prefix | active |
| NP-20 | Exclusion constraint | `excl_<table>_<columns>` | `excl_room_bookings_room_period` | GitLab prefix | active |
| NP-21 | Index | `index_<table>_<columns>` | `index_sales_orders_customer_id` | GitLab prefix | active |
| NP-22 | Application schema | `<business_domain>` | `finance` | Proposal | active |
| NP-23 | Raw layer schema | `raw_<source_system>` | `raw_billing` | Layer: Databricks bronze; name is a proposal | active |
| NP-24 | Staging layer schema | `staging` | `staging` | dbt | active |
| NP-25 | Intermediate layer schema | `intermediate` | `intermediate` | dbt | active |
| NP-26 | Marts layer schema | `marts` or `marts_<domain>` | `marts_finance` | dbt | active |
| NP-27 | Snapshot schema | `snapshots` | `snapshots` | dbt (separate schema); name is a proposal | active |
| NP-28 | Staging object | `<source_system>_<entity_plural>` | `billing_invoices` | Proposal | active |
| NP-29 | Dimension | `dim_<entity_plural>` | `dim_customers` | dbt Kimball tutorial for the marker; it uses singular | active |
| NP-30 | Fact table | `fact_<business_process_plural>` | `fact_shipments` | Proposal | active |

## Part A. Naming conventions

### Governance of the convention

#### NAM-001 Convention is documented

**Each platform SHOULD have one documented naming convention that states its scope and its authority.**

| Field | Value |
|---|---|
| level | RECOMMENDED |
| scope | all |
| applies_when | always |
| rationale | Without a written convention and a named authority, reviewers have no basis for accepting or rejecting a name, and drift is invisible. |
| exceptions | none |
| engine_notes | none |
| evidence | GOV-08, THIN-08, DES-20, research/design_decision_matrix.md#NM-1, research/database_design_standards.md#6.1 |
| evidence_strength | standard |
| status | active |
| decision_ref | null |
| check_method | manual_review |
| check_description | Confirm a convention document exists, names its owner and states which systems it covers. |
| lifecycle_stage | Governance |

#### NAM-002 Convention is applied consistently

**Every new object MUST follow the approved convention in this file, so that one platform has one style.**

| Field | Value |
|---|---|
| level | MANDATORY |
| scope | all |
| applies_when | always |
| rationale | Mixed styles force every consumer to look names up and make automated checks unreliable. The style itself has no outcome evidence; only consistency is required by every style source. |
| exceptions | Inherited or vendor-managed schemas, with an exception recorded and approved by the framework exception approver. |
| engine_notes | none |
| evidence | DES-20, LAKE-16, THIN-15, research/design_decision_matrix.md#NM-1, research/database_design_standards.md#6.2, research/architecture_comparison.md#C-26 |
| evidence_strength | multi_vendor |
| status | active |
| decision_ref | A9 |
| check_method | schema_lint |
| check_description | Lint all new or changed identifiers against the approved pattern table; report the share of objects that fail. |
| lifecycle_stage | Governance |

#### NAM-003 Vocabulary comes from the business context

**Names in a bounded context SHOULD use that context's agreed business vocabulary, recorded in its glossary.**

| Field | Value |
|---|---|
| level | RECOMMENDED |
| scope | OLTP |
| applies_when | transactional domain models; analytical layers are covered by NAM-004 |
| rationale | Names invented by engineers diverge from the language the business uses, and the same word comes to mean different things in the same model. |
| exceptions | Different contexts may legitimately use different terms for one concept; the context owner approves the glossary. |
| engine_notes | none |
| evidence | ARCH-01, ARCH-02, research/design_decision_matrix.md#NM-11 |
| evidence_strength | single_vendor |
| status | active |
| decision_ref | null |
| check_method | manual_review |
| check_description | Sample table and column names and confirm each business term appears in the context glossary. |
| lifecycle_stage | Data Modeling |

#### NAM-004 One name per attribute

**The same attribute SHOULD carry the same column name in every table where it appears.**

| Field | Value |
|---|---|
| level | RECOMMENDED |
| scope | all |
| applies_when | always, within one bounded context or one analytical layer |
| rationale | When one attribute has several names, joins and lineage must be worked out by hand and errors go unnoticed. |
| exceptions | Role-qualified references under NP-04, and raw landing objects covered by NAM-007. |
| engine_notes | Oracle is the only one of the five database engines with formal naming guidance; the reading is from the 19c edition (THIN-15). |
| evidence | THIN-15, LAKE-16, research/design_decision_matrix.md#NM-13 |
| evidence_strength | single_vendor |
| status | active |
| decision_ref | null |
| check_method | catalog_query |
| check_description | Query the catalog for columns with the same domain or foreign key target but different names. |
| lifecycle_stage | Schema Design |

#### NAM-005 Dropped names are not reused

**A name that has been dropped SHOULD NOT be reused for an attribute with a different meaning.**

| Field | Value |
|---|---|
| level | RECOMMENDED |
| scope | all |
| applies_when | always; most important where table formats or downstream consumers track columns by name |
| rationale | A reused name silently attaches old history, grants or consumer logic to new data. No source states this for names; it is inferred from table-format rules on column identifiers. |
| exceptions | none |
| engine_notes | Iceberg forbids reuse of column identifiers; that is a rule about identifiers, not names. Name-tracked systems carry the risk without that protection. |
| evidence | PIPE-09, PIPE-10, research/design_decision_matrix.md#NM-12 |
| evidence_strength | inference |
| status | provisional |
| decision_ref | null |
| check_method | migration_lint |
| check_description | Compare each added name with the history of dropped names and flag matches for review. |
| lifecycle_stage | Governance |

### Identifier safety and length

#### NAM-006 Portable character set

**Identifiers MUST use only ASCII letters, digits and underscores, and MUST start with a letter.**

| Field | Value |
|---|---|
| level | MANDATORY |
| scope | all |
| applies_when | always, for names the platform creates |
| rationale | Other characters need quoting, behave differently per engine and break tooling. ASCII also makes one character equal one byte, which the length limit in NAM-010 depends on. |
| exceptions | Raw landing objects under NAM-007. |
| engine_notes | MySQL permits only BMP characters in identifiers. Databricks Hive metastore schema and table names are limited to alphanumeric ASCII and underscores. Oracle discourages dollar and number signs. SQL Server permanent objects must not begin with at or number signs. |
| evidence | PGMY-09, PGMY-10, THIN-15, ENG-30, research/database_design_standards.md#6.2, research/official_documentation.md#3 |
| evidence_strength | multi_vendor |
| status | active |
| decision_ref | null |
| check_method | schema_lint |
| check_description | Test every identifier against the allowed character set and first-character rule. |
| lifecycle_stage | Schema Design |

#### NAM-007 Raw landing keeps source names

**Raw landing objects MAY keep source-system names unchanged, provided the first conformed layer renames them to this convention.**

| Field | Value |
|---|---|
| level | OPTIONAL |
| scope | data_warehouse, lakehouse |
| applies_when | only in the raw layer of NP-23 |
| rationale | Renaming at ingest breaks traceability to the source, while carrying source names further spreads unsafe identifiers. The exception is inferred from layer-based enforcement. |
| exceptions | none |
| engine_notes | Delta column names cannot differ only by case, so a source with case-variant names needs handling at landing. |
| evidence | LAKE-01, PIPE-11, research/architecture_comparison.md#C-53, research/design_decision_matrix.md#PL-10 |
| evidence_strength | inference |
| status | active |
| decision_ref | C7 |
| check_method | pipeline_test |
| check_description | Confirm no object outside the raw layer fails the identifier rules. |
| lifecycle_stage | ETL/ELT |

#### NAM-008 No reliance on quoting

**Identifiers SHOULD be created and referenced unquoted, and SHOULD NOT depend on quoting or letter case to be distinct.**

| Field | Value |
|---|---|
| level | RECOMMENDED |
| scope | all |
| applies_when | always |
| rationale | Quoting makes a name case-sensitive on some engines, and the same name then fails when referenced without quotes. Two names differing only by case do not survive a move between engines. |
| exceptions | Raw landing objects under NAM-007. |
| engine_notes | PostgreSQL advises always or never quoting a given name. Oracle does not recommend quoted object names. MySQL column and index names are never case-sensitive. SQL Server case follows database collation. Databricks and Delta names are case-insensitive when referenced. |
| evidence | PGMY-09, PGMY-17, MSOM-10, THIN-15, ENG-20, research/design_decision_matrix.md#NM-4 |
| evidence_strength | multi_vendor |
| status | active |
| decision_ref | null |
| check_method | schema_lint |
| check_description | Flag quoted identifiers in migrations, and names in one namespace that differ only by case. |
| lifecycle_stage | Schema Design |

#### NAM-009 Fit within every target engine

**Every identifier MUST fit within the lowest identifier limit of the engines on which it will be deployed.**

| Field | Value |
|---|---|
| level | MANDATORY |
| scope | all |
| applies_when | always |
| rationale | Engines reject or misbehave beyond their limits. PostgreSQL truncates longer names rather than preserving them, so two long names can collide. |
| exceptions | none |
| engine_notes | Limits are listed in the derivation table in this file. SQL Server local temporary tables are limited to 116 characters. A separate Databricks column-name limit was not confirmed. MongoDB limits namespaces (255 bytes, 235 sharded); its field-name length was not captured. |
| evidence | PGMY-09, PGMY-17, MSOM-10, THIN-15, ENG-20, ENG-30, research/design_decision_matrix.md#NM-3, research/official_documentation.md#2, research/official_documentation.md#3, research/official_documentation.md#4 |
| evidence_strength | multi_vendor |
| status | active |
| decision_ref | B30 |
| check_method | schema_lint |
| check_description | Compare each identifier's byte length with the lowest limit of its declared target engines. |
| lifecycle_stage | Schema Design |

#### NAM-010 Portable identifier ceiling

**Identifiers SHOULD NOT exceed the portable ceiling of 63 ASCII characters given in the derivation table.**

| Field | Value |
|---|---|
| level | RECOMMENDED |
| scope | all |
| applies_when | any system that may run on, or replicate to, more than one engine; deployments on a single engine may approve its limit instead |
| rationale | A ceiling set per engine makes later migration or replication fail on names that were legal when created. The 30-byte figure comes only from Oracle below COMPATIBLE 12.2 and is outdated as a universal ceiling. |
| exceptions | Single-engine estates may adopt that engine's limit, approved by the framework exception approver. An estate with Oracle below COMPATIBLE 12.2 must use 30. |
| engine_notes | 63 is PostgreSQL's default limit, in bytes. It is the lowest of the current engine limits and equals 63 characters only because NAM-006 restricts names to ASCII. |
| evidence | PGMY-09, MSOM-10, ENG-20, ENG-30, DES-20, research/architecture_comparison.md#C-22, research/design_decision_matrix.md#NM-3, research/database_design_standards.md#6.5 |
| evidence_strength | multi_vendor |
| status | active |
| decision_ref | B30 |
| check_method | schema_lint |
| check_description | Fail any identifier longer than the approved ceiling. |
| lifecycle_stage | Schema Design |

#### NAM-011 Reserved words and prefixes

**Identifiers MUST NOT be a reserved word, or use a reserved prefix, of any target engine.**

| Field | Value |
|---|---|
| level | MANDATORY |
| scope | all |
| applies_when | always |
| rationale | Reserved names fail outright or force quoting, which NAM-008 discourages, and system prefixes can collide with engine objects. |
| exceptions | none |
| engine_notes | Reserved prefixes: pg_ on PostgreSQL; SYS_ and ORA_ on Oracle. Nonquoted Oracle identifiers cannot be reserved words. Reserved-word lists differ per engine and version and are not reproduced in the research; a check must load each target engine's own list. |
| evidence | PGMY-09, MSOM-10, THIN-15, DES-20, research/design_decision_matrix.md#NM-5 |
| evidence_strength | multi_vendor |
| status | active |
| decision_ref | null |
| check_method | schema_lint |
| check_description | Compare identifiers with the union of the reserved-word and prefix lists for declared target engines. |
| lifecycle_stage | Schema Design |

### Case, number and words

#### NAM-012 Lowercase snake case

**Identifiers SHOULD be written in lowercase with words separated by single underscores.**

| Field | Value |
|---|---|
| level | RECOMMENDED |
| scope | all |
| applies_when | always |
| rationale | Unquoted case handling differs by engine, so mixed case does not round-trip. Vendors and style guides converge on lowercase for portability, from different causes. |
| exceptions | Raw landing objects under NAM-007. |
| engine_notes | Oracle and Snowflake store unquoted names in upper case, so a lowercase name appears upper case in their catalogs; do not quote to preserve it. MySQL table case depends on the file system and lower_case_table_names, fixed at initialization; lowercase names and the value 1 are advised for InnoDB portability. |
| evidence | PGMY-10, PGMY-17, LAKE-16, DES-20, DES-22, research/design_decision_matrix.md#NM-2 |
| evidence_strength | multi_vendor |
| status | active |
| decision_ref | A10 |
| check_method | schema_lint |
| check_description | Test written identifiers in migration and model source against the lowercase, single-underscore form. |
| lifecycle_stage | Schema Design |

#### NAM-013 Plural table names

**Tables and views SHOULD be named with a plural noun as in NP-01, and the choice SHOULD be uniform across a platform.**

| Field | Value |
|---|---|
| level | RECOMMENDED |
| scope | all |
| applies_when | always |
| rationale | No source reports an outcome difference, so this is a judgment and consistency is the real requirement. Plural was accepted because more table-level examples in the research use it. |
| exceptions | Framework-mapped tables may keep the framework's default if overriding it would be costly, approved by the framework exception approver. |
| engine_notes | Primary sources split. Rails and GitLab examples are plural; dbt's style guide is plural though its own Kimball tutorial is singular; Alibaba forbids plurals; Django defaults and Prisma models are singular, while Prisma calls plural tables common. EF Core follows the DbSet name. Linters treat it as configurable. |
| evidence | THIN-10, THIN-11, THIN-12, THIN-13, THIN-14, THIN-16, THIN-24, LAKE-16, DES-22, DWM-21, research/architecture_comparison.md#C-26, research/design_decision_matrix.md#NM-6 |
| evidence_strength | multi_vendor |
| status | active |
| decision_ref | A11 |
| check_method | schema_lint |
| check_description | Check table names for grammatical number using a configurable inflection rule. |
| lifecycle_stage | Data Modeling |

#### NAM-014 Full words and an abbreviation register

**Names SHOULD use full words, and an abbreviation SHOULD be used only if it is listed in an approved abbreviation register.**

| Field | Value |
|---|---|
| level | RECOMMENDED |
| scope | all |
| applies_when | always |
| rationale | Private abbreviations make names ambiguous and undiscoverable. Length pressure on constraint names still needs a controlled way to shorten. |
| exceptions | none |
| engine_notes | Sources conflict and the conflict (C-25) is settled for this framework by owner decision B31. Oracle asks for full, descriptive, pronounceable names and dbt for no abbreviations. MySQL's optimization page suggests short unprefixed column names under 18 characters. |
| evidence | THIN-15, LAKE-16, PERF-17, research/architecture_comparison.md#C-25, research/database_design_standards.md#6.1 |
| evidence_strength | multi_vendor |
| status | active |
| decision_ref | B31 |
| check_method | schema_lint |
| check_description | Split identifiers into words and flag any word in neither the dictionary nor the register. |
| lifecycle_stage | Schema Design |

#### NAM-015 No type-indicating prefixes

**Names SHOULD NOT carry a prefix that only repeats the object type or data type.**

| Field | Value |
|---|---|
| level | RECOMMENDED |
| scope | all |
| applies_when | tables and columns; the warehouse prefixes in NP-29 and NP-30 and the constraint and index prefixes in NP-16 to NP-21 mark role and are excepted |
| rationale | Such prefixes add length without information and become false when the object changes kind. |
| exceptions | none |
| engine_notes | none |
| evidence | DES-20, research/database_design_standards.md#6.1, research/database_design_standards.md#6.5 |
| evidence_strength | single_vendor |
| status | active |
| decision_ref | null |
| check_method | schema_lint |
| check_description | Flag table names beginning with a table marker and columns beginning with a data-type marker. |
| lifecycle_stage | Schema Design |

#### NAM-016 Three-part registry names

**An object-class, property and representation-term name form MAY be used, and it is required only where a registry or regulator mandates it.**

| Field | Value |
|---|---|
| level | OPTIONAL |
| scope | all |
| applies_when | metadata registries or regulated data element catalogs |
| rationale | The form makes names self-describing at the cost of length. Its only direct reading in the research is an informative annex of a 2004 committee draft, so it is not presented as required by the standard. |
| exceptions | none |
| engine_notes | The published 2005 and 2015 editions of ISO/IEC 11179-5 were not read beyond the 2015 abstract. |
| evidence | GOV-08, THIN-08, research/design_decision_matrix.md#NM-10 |
| evidence_strength | inference |
| status | provisional |
| decision_ref | null |
| check_method | manual_review |
| check_description | Where a registry applies, confirm registered names follow its rule set. |
| lifecycle_stage | Governance |

### Column semantics

#### NAM-017 Primary key column name

**A single-column surrogate primary key SHOULD be named as in NP-02.**

| Field | Value |
|---|---|
| level | RECOMMENDED |
| scope | all |
| applies_when | tables with a single-column surrogate key |
| rationale | Named keys let a join column keep one name across tables and models. The cost is a conflict with ORM defaults. |
| exceptions | Framework-managed tables that use the framework's unqualified key name, approved by the framework exception approver. They must keep NP-03 for the columns that refer to them. |
| engine_notes | dbt and sqlstyle favour named keys. Rails and EF Core favour an unqualified key name. MySQL's optimization page favours short unprefixed names. In pooled or sharded tables the key is composite: it includes the tenant or distribution column under TEN-014 and SCL-006. |
| evidence | LAKE-16, DES-20, research/design_decision_matrix.md#NM-7, research/database_design_standards.md#6.4, research/architecture_comparison.md#C-25 |
| evidence_strength | multi_vendor |
| status | active |
| decision_ref | A3, A12 |
| check_method | schema_lint |
| check_description | Check that the single-column primary key of each table matches the pattern. |
| lifecycle_stage | Schema Design |

#### NAM-018 Foreign key column name

**A foreign key column SHOULD be named as in NP-03, or as in NP-04 where a table holds more than one reference to the same parent or the role matters.**

| Field | Value |
|---|---|
| level | RECOMMENDED |
| scope | all |
| applies_when | foreign key relationships, including unenforced ones |
| rationale | A reference whose name differs from the parent key hides the relationship from readers and catalog tooling. |
| exceptions | Framework-managed tables, as in NAM-017. |
| engine_notes | Role qualification in NP-04 is this framework's proposal; the research does not state it. |
| evidence | LAKE-16, DES-18, THIN-14, research/design_decision_matrix.md#NM-7 |
| evidence_strength | multi_vendor |
| status | active |
| decision_ref | A12 |
| check_method | catalog_query |
| check_description | Compare each foreign key column name with the parent key name and the pattern. |
| lifecycle_stage | Schema Design |

#### NAM-019 Identifier suffix means a real key

**The key suffix in NP-02 and NP-03 SHOULD be used only for columns that are real keys, and identifiers issued by third parties SHOULD use NP-05.**

| Field | Value |
|---|---|
| level | RECOMMENDED |
| scope | all |
| applies_when | always |
| rationale | A column that looks like a key but enforces nothing misleads both readers and tools that infer relationships. |
| exceptions | none |
| engine_notes | This is one organization's convention (GitLab), generalized here. |
| evidence | DES-18, THIN-14, research/database_design_standards.md#6.2 |
| evidence_strength | single_vendor |
| status | active |
| decision_ref | C1 |
| check_method | catalog_query |
| check_description | List columns carrying the key suffix with no primary, unique or foreign key, and review them. |
| lifecycle_stage | Schema Design |

#### NAM-020 Boolean column names

**Boolean columns SHOULD be named as in NP-06.**

| Field | Value |
|---|---|
| level | RECOMMENDED |
| scope | all |
| applies_when | boolean columns |
| rationale | A question-form name states which value means true; without it, readers must look the meaning up. |
| exceptions | Inherited schemas, under NAM-002. |
| engine_notes | On MySQL the name form carries the meaning that the integer type does not. |
| evidence | LAKE-16, DES-20, DES-22, research/design_decision_matrix.md#NM-8 |
| evidence_strength | multi_vendor |
| status | active |
| decision_ref | C2 |
| check_method | schema_lint |
| check_description | Check that columns of boolean type match the pattern and that pattern-matching columns have boolean type. |
| lifecycle_stage | Schema Design |

#### NAM-021 Instant and date column names

**Columns holding an instant SHOULD be named as in NP-07, and columns holding a calendar date as in NP-08.**

| Field | Value |
|---|---|
| level | RECOMMENDED |
| scope | all |
| applies_when | always; strongest in analytical layers |
| rationale | A consistent suffix tells readers whether a value is an instant or a date, which prevents time-zone and boundary errors. |
| exceptions | Inherited schemas, under NAM-002. |
| engine_notes | The instant suffix implies UTC only where TYP-012 is applied. Check the type as well as the name. |
| evidence | LAKE-16, DES-20, research/design_decision_matrix.md#NM-8 |
| evidence_strength | multi_vendor |
| status | active |
| decision_ref | C2 |
| check_method | schema_lint |
| check_description | Check that instant-typed and date-typed columns match their patterns. |
| lifecycle_stage | Schema Design |

#### NAM-022 Status column names and values

**Lifecycle status columns SHOULD be named as in NP-11, and stored status codes SHOULD follow the rules of NAM-012.**

| Field | Value |
|---|---|
| level | RECOMMENDED |
| scope | all |
| applies_when | columns holding the state of a record or process |
| rationale | One undifferentiated status name cannot say whose lifecycle it tracks once a table has more than one. No source in the research states a status column convention; this is a proposal. |
| exceptions | Inherited schemas, under NAM-002. |
| engine_notes | PostgreSQL enum labels are limited to 63 bytes. |
| evidence | research/database_design_standards.md#7.4, research/design_decision_matrix.md#DT-9 |
| evidence_strength | inference |
| status | active |
| decision_ref | C3 |
| check_method | schema_lint |
| check_description | Check that columns registered as status match the pattern, and that stored codes are lowercase. |
| lifecycle_stage | Schema Design |

### Constraints, indexes, schemas and layers

#### NAM-023 Explicit constraint and index names

**Constraints and indexes SHOULD be named explicitly using NP-16 to NP-21, and SHOULD NOT rely on engine-generated names.**

| Field | Value |
|---|---|
| level | RECOMMENDED |
| scope | all |
| applies_when | any constraint or index that a migration may later alter or drop, including informational constraints on analytical platforms |
| rationale | Generated names differ per environment, so a migration written against one environment fails on another. The migration impact is inferred. |
| exceptions | When a name would exceed the ceiling in NAM-010, shorten it using the register in NAM-014; never rely on engine truncation. |
| engine_notes | Unnamed constraints receive generated names on SQL Server and MySQL. The prefixes are GitLab's and bind inside GitLab only. EF Core and similar frameworks generate names by convention, which need an explicit override. |
| evidence | DES-19, DES-18, PGMY-01, PGMY-14, THIN-12, THIN-14, research/design_decision_matrix.md#NM-9, research/database_design_standards.md#6.2 |
| evidence_strength | single_vendor |
| status | active |
| decision_ref | B32 |
| check_method | migration_lint |
| check_description | Flag constraints and indexes created without a name or with a name not matching the pattern table. |
| lifecycle_stage | Schema Design |

#### NAM-024 Schema names

**Application schemas SHOULD be named for a business domain as in NP-22, and SHOULD NOT be named for a team or a technology.**

| Field | Value |
|---|---|
| level | RECOMMENDED |
| scope | OLTP |
| applies_when | transactional databases that use more than one schema |
| rationale | Team names and products change while domains are more stable, so renames are avoided. No source in the research states a schema naming rule; this is a proposal. |
| exceptions | none |
| engine_notes | Oracle database names are limited to 8 bytes, which is a different object from a schema. Tenant schemas are decided in the tenancy standards. |
| evidence | research/database_design_standards.md#6.1, research/design_decision_matrix.md#NM-11 |
| evidence_strength | inference |
| status | active |
| decision_ref | C4 |
| check_method | manual_review |
| check_description | Review schema names against the domain list. |
| lifecycle_stage | Schema Design |

#### NAM-025 Warehouse layer names

**Analytical layers SHOULD be named by the single approved vocabulary in NP-23 to NP-26, and SHOULD NOT mix vocabularies on one platform.**

| Field | Value |
|---|---|
| level | RECOMMENDED |
| scope | data_warehouse, lakehouse |
| applies_when | platforms with more than one analytical layer |
| rationale | Mixed layer words hide which data has been conformed and which rules apply. The number of layers is a separate optional choice; this rule only names those that exist. |
| exceptions | A platform with existing medallion names may keep them, recording the mapping and with approval from the framework exception approver. |
| engine_notes | Databricks and Fabric use bronze, silver and gold; dbt uses staging, intermediate and marts. Medallion is a recommended pattern and not a requirement (C-07). The mapping between the vocabularies is this framework's inference. |
| evidence | LAKE-01, LAKE-06, LAKE-15, CLOUD-21, research/architecture_comparison.md#C-07, research/design_decision_matrix.md#AP-8 |
| evidence_strength | multi_vendor |
| status | active |
| decision_ref | C5 |
| check_method | catalog_query |
| check_description | List schemas in the analytical platform and confirm each maps to one approved layer. |
| lifecycle_stage | Schema Design |

#### NAM-026 Snapshot objects kept apart

**History snapshots SHOULD be kept in their own schema as in NP-27.**

| Field | Value |
|---|---|
| level | RECOMMENDED |
| scope | data_warehouse, lakehouse |
| applies_when | platforms using snapshot-based history capture |
| rationale | Snapshots cannot be rebuilt from current source state, so they need protection from refresh and cleanup jobs on rebuilt layers. |
| exceptions | none |
| engine_notes | Single-vendor advice from dbt. |
| evidence | LAKE-18, research/official_documentation.md#12 |
| evidence_strength | single_vendor |
| status | active |
| decision_ref | C6 |
| check_method | catalog_query |
| check_description | Confirm snapshot objects sit only in the snapshot schema. |
| lifecycle_stage | Schema Design |

#### NAM-027 Conformed and mart object names

**Staging objects SHOULD be named as in NP-28, and dimensional objects as in NP-29 and NP-30.**

| Field | Value |
|---|---|
| level | RECOMMENDED |
| scope | data_warehouse, lakehouse |
| applies_when | conformed and dimensional layers |
| rationale | Source-qualified staging names stop two sources colliding, and a role marker tells consumers how a table may be joined. Only the dimension marker appears in the research; the others are proposals. |
| exceptions | none |
| engine_notes | dbt's Kimball tutorial uses a singular dimension name, which differs from the plural default in NAM-013. |
| evidence | DWM-21, LAKE-15, research/architecture_comparison.md#C-26, research/official_documentation.md#13 |
| evidence_strength | single_vendor |
| status | active |
| decision_ref | C6 |
| check_method | catalog_query |
| check_description | Check mart and staging object names against the patterns. |
| lifecycle_stage | Reporting |

#### NAM-028 Measure column names

**Monetary, minor-unit, currency and quantity columns SHOULD be named as in NP-12, NP-13, NP-14 and NP-15.**

| Field | Value |
|---|---|
| level | RECOMMENDED |
| scope | all |
| applies_when | columns holding money, currency codes or quantities |
| rationale | A column whose name does not reveal its unit gets mixed with one in another unit. Only the unit suffix for integer amounts appears in the research; the others are proposals. |
| exceptions | none |
| engine_notes | none |
| evidence | LAKE-16, research/database_design_standards.md#7.1, research/design_decision_matrix.md#NM-8 |
| evidence_strength | single_vendor |
| status | active |
| decision_ref | A13, C2 |
| check_method | schema_lint |
| check_description | Check that decimal or integer columns registered as measures match their patterns. |
| lifecycle_stage | Schema Design |

## Part B. Data types and precision

### Money

#### TYP-001 Money is exact

**Monetary values MUST be stored in an exact decimal type or in integer minor units, and MUST NOT be stored or calculated in binary floating point.**

| Field | Value |
|---|---|
| level | MANDATORY |
| scope | all |
| applies_when | always |
| rationale | Binary floating point cannot represent most decimal fractions, so totals fail to reconcile. A dbt style-guide example casts an amount to float; it conflicts with this rule and must not be copied (C-27). |
| exceptions | Raw landing may hold a value as delivered in text or semi-structured form under TYP-026, but not in a floating type. |
| engine_notes | PostgreSQL numeric; MySQL DECIMAL (up to 65 digits; default DECIMAL(10,0)); SQL Server decimal (precision 1 to 38); Oracle NUMBER with precision and scale, where excess scale rounds and excess precision errors; MongoDB Decimal128; Snowflake NUMBER, or DECFLOAT for ledgers and variable scale. Databricks money guidance was not captured. |
| evidence | PGMY-02, MSOM-03, MSOM-10, MSOM-18, DES-22, research/architecture_comparison.md#C-27, research/design_decision_matrix.md#DT-1, research/official_documentation.md#2, research/official_documentation.md#3 |
| evidence_strength | multi_vendor |
| status | active |
| decision_ref | null |
| check_method | schema_lint |
| check_description | Flag floating-type columns registered as money or matching the measure patterns; test pipelines for casts to float. |
| lifecycle_stage | Schema Design |

#### TYP-002 No proprietary money types

**Monetary columns SHOULD NOT use a proprietary money type.**

| Field | Value |
|---|---|
| level | RECOMMENDED |
| scope | all |
| applies_when | always |
| rationale | Proprietary types carry no currency, and can round on calculation or depend on locale settings on reload. |
| exceptions | Single-currency, whole-cent, add-and-subtract use on PostgreSQL, which the PostgreSQL wiki tolerates, with framework exception approver approval. |
| engine_notes | SQL Server money and smallmoney truncate in calculations and store no currency. PostgreSQL money depends on lc_monetary and stores no currency. |
| evidence | PGMY-10, MSOM-03, research/database_design_standards.md#7.1 |
| evidence_strength | multi_vendor |
| status | active |
| decision_ref | null |
| check_method | schema_lint |
| check_description | Flag columns of a proprietary money type. |
| lifecycle_stage | Schema Design |

#### TYP-003 Scale fits the currency

**The scale of a monetary column SHOULD cover the ISO 4217 minor unit of every currency it may hold, and SHOULD NOT assume two decimals.**

| Field | Value |
|---|---|
| level | RECOMMENDED |
| scope | all |
| applies_when | always |
| rationale | Minor units vary from 0 (JPY) through 2 (USD, EUR) and 3 (KWD, BHD) to 4 (CLF, UYW), and change by amendment, so hard-coded scales lose value or misstate it. |
| exceptions | none |
| engine_notes | The list used was dated 2026-09-17. The ISO standard page itself returned 403, so the edition is not verified; the SIX lists are the source. |
| evidence | GOV-20, DES-11, research/design_decision_matrix.md#DT-2, research/database_design_standards.md#7.1 |
| evidence_strength | standard |
| status | active |
| decision_ref | null |
| check_method | catalog_query |
| check_description | Compare declared scales with the largest minor unit among the currencies permitted for the column. |
| lifecycle_stage | Schema Design |

#### TYP-004 Mixed-currency minimum scale

**Columns holding amounts in more than one currency SHOULD have a scale of at least 4.**

| Field | Value |
|---|---|
| level | RECOMMENDED |
| scope | all |
| applies_when | stored transaction amounts in multi-currency columns; does not apply to exchange rates, unit prices or intermediate results |
| rationale | A lower scale cannot hold CLF and UYW amounts. This is a low-confidence inference from those minor units and from SQL Server's four-place advice; no source states a figure. |
| exceptions | none |
| engine_notes | SQL Server's four-place advice concerns its decimal type in calculations. |
| evidence | DES-11, MSOM-03, research/design_decision_matrix.md#DT-2, research/database_design_standards.md#7.1 |
| evidence_strength | inference |
| status | active |
| decision_ref | B22 |
| check_method | catalog_query |
| check_description | List multi-currency monetary columns with scale below 4. |
| lifecycle_stage | Schema Design |

#### TYP-005 Currency stored with the amount

**Each amount in a multi-currency context SHOULD be stored with its currency, as an ISO 4217 alphabetic code.**

| Field | Value |
|---|---|
| level | RECOMMENDED |
| scope | OLTP, data_warehouse |
| applies_when | any column set that can hold more than one currency |
| rationale | An amount without a currency cannot be interpreted or balanced by currency. |
| exceptions | Single-currency systems may state the currency once in metadata, approved by the framework exception approver. |
| engine_notes | ERP products hold transaction, entity and optional reporting amounts together; that requirement belongs to the financial controls standards. |
| evidence | PGMY-10, TEN-41, ERP-03, ERP-09, ERP-20, research/design_decision_matrix.md#DT-3, research/database_design_standards.md#7.1 |
| evidence_strength | multi_vendor |
| status | active |
| decision_ref | null |
| check_method | schema_lint |
| check_description | Confirm each monetary column has a registered currency column or a documented fixed currency. |
| lifecycle_stage | Schema Design |

#### TYP-006 Currency reference data

**Currency codes and minor units SHOULD be held as effective-dated reference data loaded from the ISO 4217 lists.**

| Field | Value |
|---|---|
| level | RECOMMENDED |
| scope | OLTP, data_warehouse |
| applies_when | multi-currency systems |
| rationale | Codes retire and minor units change by amendment, for example BGN moving to List Three when Bulgaria adopted EUR, so a static list goes wrong and history must stay valid. |
| exceptions | none |
| engine_notes | none |
| evidence | GOV-20, DES-11, research/database_design_standards.md#7.1 |
| evidence_strength | inference |
| status | provisional |
| decision_ref | null |
| check_method | pipeline_test |
| check_description | Reconcile the reference data with the latest SIX lists and confirm retired codes keep their end dates. |
| lifecycle_stage | Data Quality |

#### TYP-007 Integer minor units

**Integer minor units MAY be used for monetary values only as a marked exception to exact decimal, if the column name marks the unit as in NP-14 and the currency is known from the row or from metadata.**

| Field | Value |
|---|---|
| level | OPTIONAL |
| scope | all |
| applies_when | where integer arithmetic is worth the conversion burden |
| rationale | Unmarked integer amounts are read as whole currency units. Exact decimal arithmetic is much slower than integer, so the option is legitimate, but no source gives numbers. |
| exceptions | none |
| engine_notes | MongoDB prefers its decimal type over a scale-factor method. PostgreSQL states numeric is much slower than integer arithmetic. |
| evidence | LAKE-16, PGMY-02, research/database_design_standards.md#7.1 |
| evidence_strength | single_vendor |
| status | active |
| decision_ref | A13 |
| check_method | schema_lint |
| check_description | Confirm integer columns registered as money carry the unit marker and a resolvable currency. |
| lifecycle_stage | Schema Design |

### Quantities and exchange rates

#### TYP-008 Exact quantities

**Quantities that must add up or reconcile exactly SHOULD use an exact decimal or integer type.**

| Field | Value |
|---|---|
| level | RECOMMENDED |
| scope | all |
| applies_when | stock, measured and billed quantities; not scientific or sensor measures where approximate values are acceptable |
| rationale | Inexact types make stock and billing totals disagree with their sources. |
| exceptions | Measures where approximation is acceptable may use floating point, recorded in the data dictionary. |
| engine_notes | PostgreSQL advises numeric for exact quantities. Snowflake reserves FLOAT for cases where imprecise results are acceptable. |
| evidence | PGMY-02, research/database_design_standards.md#7.1, research/official_documentation.md#2, research/official_documentation.md#11 |
| evidence_strength | multi_vendor |
| status | active |
| decision_ref | null |
| check_method | schema_lint |
| check_description | Flag floating-type columns registered as reconciling quantities. |
| lifecycle_stage | Schema Design |

#### TYP-009 Quantity carries its unit

**Quantities SHOULD be stored with a unit of measure, and the scale SHOULD be declared per unit in the design record.**

| Field | Value |
|---|---|
| level | RECOMMENDED |
| scope | OLTP, data_warehouse |
| applies_when | columns that can hold more than one unit, or whose unit is not fixed by the column's definition |
| rationale | A quantity without a unit cannot be compared or converted safely. The research states no scale or unit rule for quantities; this is an inference by analogy with currency. |
| exceptions | none |
| engine_notes | none |
| evidence | research/database_design_standards.md#7.1 |
| evidence_strength | inference |
| status | active |
| decision_ref | B23 |
| check_method | manual_review |
| check_description | Confirm each quantity column has a unit column or a documented fixed unit, and a declared scale. |
| lifecycle_stage | Schema Design |

#### TYP-010 Exchange rates are exact

**Stored exchange rates SHOULD use an exact decimal type that holds the full precision the rate source delivers; no value set for a framework-wide precision.**

| Field | Value |
|---|---|
| level | RECOMMENDED |
| scope | OLTP, data_warehouse |
| applies_when | any stored exchange rate; PROVISIONAL and no value set, because no source addresses rate representation |
| rationale | Rates feed converted amounts, so rounding in a floating type carries into posted figures. This extends the money rule by inference. |
| exceptions | none |
| engine_notes | A rate and its reciprocal may disagree after rounding, and products differ on storing inverses (C-77); this is left to the financial controls standards. |
| evidence | research/design_decision_matrix.md#FN-19, research/architecture_comparison.md#C-77, research/research_gaps.md#6a, research/database_design_standards.md#7.1 |
| evidence_strength | inference |
| status | provisional |
| decision_ref | A14 |
| check_method | schema_lint |
| check_description | Flag floating-type columns registered as exchange rates. |
| lifecycle_stage | Schema Design |

#### TYP-011 Exchange rate precision is a recorded decision

**Each deployment SHOULD record the precision and scale of its exchange-rate columns as a design decision, SHOULD hold the full precision the rate source delivers, and SHOULD NOT round a delivered rate on capture; no value set for a framework-wide precision.**

| Field | Value |
|---|---|
| level | RECOMMENDED |
| scope | OLTP, data_warehouse |
| applies_when | any stored exchange rate; PROVISIONAL and no value set, because no vendor or standard-setter read states a precision |
| rationale | A rate column narrower than what the provider delivers loses value silently, but any figure in this framework would be invented, so decision A14 records no value set. |
| exceptions | none |
| engine_notes | No vendor page states a precision standard. D365's example display does not establish one. |
| evidence | research/design_decision_matrix.md#FN-19, research/research_gaps.md#6a, research/database_design_standards.md#7.1 |
| evidence_strength | inference |
| status | provisional |
| decision_ref | A14 |
| check_method | manual_review |
| check_description | Confirm the design record states the rate precision and that it covers the provider's delivered precision. |
| lifecycle_stage | Schema Design |

### Instants and dates

#### TYP-012 Instants are unambiguous relative to UTC

**An instant SHOULD be stored in a UTC-normalizing type where one fits the required range, or otherwise under a documented UTC convention.**

| Field | Value |
|---|---|
| level | RECOMMENDED |
| scope | all |
| applies_when | any column recording a point in time |
| rationale | A local timestamp with no zone cannot be placed on a timeline, so ordering and duration calculations break across zones and daylight changes. |
| exceptions | none |
| engine_notes | PostgreSQL timestamptz stores UTC and drops the zone; timetz is advised against, and the wiki is stricter than the manual on plain timestamp (C-24). MySQL TIMESTAMP ends 2038-01-19, while DATETIME has no conversion and needs an application UTC convention. SQL Server: avoid datetime; no official choice between datetime2 in UTC and datetimeoffset; treat datetimeoffset as a fixed offset (C-88). [WF] The datetimeoffset daylight-saving behaviour (ENG-09) was read through a summarising fetch and needs a re-check against the page before use. Oracle WITH LOCAL TIME ZONE normalizes to the database zone. MongoDB BSON Date is UTC. Snowflake notes TZ types hurt pruning and advises keeping a non-TZ column for filtering. |
| evidence | PGMY-03, PGMY-10, PGMY-13, MSOM-03, ENG-09, ENG-13, LAKE-14, research/architecture_comparison.md#C-24, research/architecture_comparison.md#C-88, research/design_decision_matrix.md#DT-4, research/database_design_standards.md#7.2 |
| evidence_strength | multi_vendor |
| status | active |
| decision_ref | null |
| check_method | schema_lint |
| check_description | Flag instant-named columns with a zone-less type that lack a documented UTC convention. |
| lifecycle_stage | Schema Design |

#### TYP-013 Calendar dates use a date type

**A value with no time-of-day meaning SHOULD be stored in a calendar date type and not as an instant.**

| Field | Value |
|---|---|
| level | RECOMMENDED |
| scope | all |
| applies_when | birth dates, accounting dates, due dates and similar |
| rationale | A date stored as an instant shifts by a day when read in another zone. |
| exceptions | none |
| engine_notes | Oracle DATE includes time to the second, so a date-only rule on Oracle needs an added truncation check. |
| evidence | PGMY-03, MSOM-10, research/design_decision_matrix.md#DT-5, research/database_design_standards.md#7.2 |
| evidence_strength | multi_vendor |
| status | active |
| decision_ref | null |
| check_method | schema_lint |
| check_description | Flag date-named columns with an instant type, and on Oracle test for non-midnight values. |
| lifecycle_stage | Schema Design |

#### TYP-014 Local time retained where it has meaning

**Where a local wall-clock time or source zone has business meaning, it SHOULD be stored separately as in NP-09 and NP-10.**

| Field | Value |
|---|---|
| level | RECOMMENDED |
| scope | OLTP |
| applies_when | when the local time or zone is itself part of the business fact; analytical use is not addressed by the research |
| rationale | UTC normalization discards the original zone. No source covers future-dated local events specifically. |
| exceptions | none |
| engine_notes | PostgreSQL states the zone is not retained. Oracle TIMESTAMP WITH TIME ZONE does preserve zone information. |
| evidence | PGMY-03, MSOM-10, research/database_design_standards.md#7.2 |
| evidence_strength | inference |
| status | provisional |
| decision_ref | null |
| check_method | manual_review |
| check_description | Review requirements for local-time semantics and confirm a separate column exists where they apply. |
| lifecycle_stage | Data Modeling |

#### TYP-015 Half-open time ranges

**Time ranges SHOULD be expressed as an inclusive start and an exclusive end, and range filters SHOULD NOT use BETWEEN on instants.**

| Field | Value |
|---|---|
| level | RECOMMENDED |
| scope | all |
| applies_when | stored periods and range predicates on instants |
| rationale | An inclusive upper bound double-counts or misses rows at the boundary. |
| exceptions | none |
| engine_notes | SQL:2011 periods are closed-open as reported by committee authors; the clause text was not read. SQL Server temporal tables use a 9999-12-31 end for open rows. |
| evidence | PGMY-10, GOV-06, MSOM-04, research/architecture_comparison.md#C-33, research/design_decision_matrix.md#DT-5 |
| evidence_strength | multi_vendor |
| status | active |
| decision_ref | null |
| check_method | manual_review |
| check_description | Review range definitions and search query code for BETWEEN on instant columns. |
| lifecycle_stage | Reporting |

#### TYP-016 ISO 8601 for interchange only

**Date-time values exchanged between systems as text SHOULD use ISO 8601, and ISO 8601 SHOULD NOT be treated as a storage type.**

| Field | Value |
|---|---|
| level | RECOMMENDED |
| scope | all |
| applies_when | interchange formats |
| rationale | Ambiguous text dates are misread on exchange, and text storage loses type checks. |
| exceptions | ISO 8601 excludes non-Gregorian calendars; such interchange is excepted, approved by the framework exception approver. |
| engine_notes | none |
| evidence | GOV-21, research/design_decision_matrix.md#DT-16, research/database_design_standards.md#7.2 |
| evidence_strength | standard |
| status | active |
| decision_ref | null |
| check_method | pipeline_test |
| check_description | Test interface payloads against the ISO 8601 profile. |
| lifecycle_stage | ETL/ELT |

### Text

#### TYP-017 Text sizing follows the engine

**Text columns SHOULD be sized under the target engine's annex, and any declared length SHOULD be recorded as either a business limit or a storage choice.**

| Field | Value |
|---|---|
| level | RECOMMENDED |
| scope | OLTP |
| applies_when | transactional engines; analytical sizing is not addressed by the research |
| rationale | Invented limits cause production errors, yet engines differ on whether unbounded text is costless (C-21), so a single portable size rule would be wrong on some engine. |
| exceptions | none |
| engine_notes | PostgreSQL: unbounded text with CHECK for real limits; no performance difference apart from padding. MySQL: bounded VARCHAR with the smallest suitable type, considering row format and index limits. SQL Server nvarchar(n) counts byte-pairs, not characters. Oracle: use VARCHAR2, not VARCHAR. |
| evidence | PGMY-10, PERF-17, MSOM-03, MSOM-10, research/architecture_comparison.md#C-21, research/design_decision_matrix.md#DT-6, research/database_design_standards.md#7.3 |
| evidence_strength | multi_vendor |
| status | active |
| decision_ref | null |
| check_method | manual_review |
| check_description | Review declared lengths against the design record's business limits and the engine annex. |
| lifecycle_stage | Schema Design |

#### TYP-018 Fixed-length codes validated by content

**Fixed-length codes SHOULD be validated by a content rule on length and character class, and not by reliance on a padded fixed-width type.**

| Field | Value |
|---|---|
| level | RECOMMENDED |
| scope | OLTP, data_warehouse |
| applies_when | codes such as ISO currency codes |
| rationale | A padded type changes comparison and does not check content. The content rule is universal; the storage type is engine-specific. |
| exceptions | none |
| engine_notes | The research suggested a three-character fixed type or text with CHECK; the PostgreSQL wiki says not to use char(n) even for fixed-length identifiers. Resolve per engine. |
| evidence | PGMY-10, research/database_design_standards.md#7.1, research/database_design_standards.md#7.3 |
| evidence_strength | single_vendor |
| status | active |
| decision_ref | null |
| check_method | schema_lint |
| check_description | Confirm registered code columns have a content rule. |
| lifecycle_stage | Schema Design |

#### TYP-019 Unicode-capable encoding

**A database SHOULD use one Unicode-capable encoding for text.**

| Field | Value |
|---|---|
| level | RECOMMENDED |
| scope | all |
| applies_when | always |
| rationale | Mixed or partial encodings lose characters and break comparison across columns. |
| exceptions | none |
| engine_notes | MySQL: use utf8mb4, since utf8mb3 is deprecated and expected to be removed. This specific name has single-engine evidence. |
| evidence | research/design_decision_matrix.md#DT-7, research/database_design_standards.md#7.3, research/official_documentation.md#3 |
| evidence_strength | single_vendor |
| status | active |
| decision_ref | null |
| check_method | catalog_query |
| check_description | Query the catalog for database, table and column encodings. |
| lifecycle_stage | Schema Design |

#### TYP-020 Joined columns match

**Columns that are joined or related by a foreign key SHOULD have the same data type, width, character set and collation.**

| Field | Value |
|---|---|
| level | RECOMMENDED |
| scope | OLTP, data_warehouse |
| applies_when | foreign keys and recurring join columns |
| rationale | Mismatches cause implicit conversion, lost index use, and overflow where a referencing integer is narrower than its parent. |
| exceptions | none |
| engine_notes | MySQL says joined columns should share character set and type. Snowflake says never to use collation on join keys. |
| evidence | PERF-17, LAKE-14, research/design_decision_matrix.md#DT-11, research/database_design_standards.md#7.3 |
| evidence_strength | single_vendor |
| status | active |
| decision_ref | null |
| check_method | catalog_query |
| check_description | Compare type, width, character set and collation across each foreign key and registered join. |
| lifecycle_stage | Schema Design |

### Booleans, enumerations and JSON

#### TYP-021 Native boolean

**Yes-or-no attributes SHOULD use the engine's native boolean type where one exists.**

| Field | Value |
|---|---|
| level | RECOMMENDED |
| scope | OLTP |
| applies_when | transactional engines with a native type |
| rationale | Coded substitutes admit more values than true and false unless separately constrained. |
| exceptions | none |
| engine_notes | MySQL: use tinyint with the naming pattern in NP-06, per Alibaba. The research has no source for calling single-character flags an antipattern, and none is claimed. |
| evidence | DES-22, DES-20, research/design_decision_matrix.md#DT-8, research/database_design_standards.md#7.4 |
| evidence_strength | multi_vendor |
| status | active |
| decision_ref | null |
| check_method | schema_lint |
| check_description | Flag NP-06 columns that do not have the native boolean type on engines offering one. |
| lifecycle_stage | Schema Design |

#### TYP-022 Enumerated value sets

**A value set that can change or carries attributes SHOULD be a reference table referenced by a foreign key.**

| Field | Value |
|---|---|
| level | RECOMMENDED |
| scope | OLTP |
| applies_when | transactional schemas; analytical layers use conformed dimensions instead |
| rationale | Native enums are hard to change, and a CHECK list needs a schema change for each new value. The reference-table default is inferred from engine limits; sources disagree, so a CHECK may serve small stable sets. |
| exceptions | A CHECK on text may be used for small stable sets, approved by the framework exception approver. |
| engine_notes | PostgreSQL enums cannot have values removed without re-creating the type. MySQL ENUM values are stored as indexes, sort by index, and invalid input in non-strict mode becomes an empty string. |
| evidence | PGMY-10, DES-19, research/design_decision_matrix.md#DT-9, research/database_design_standards.md#7.4 |
| evidence_strength | multi_vendor |
| status | active |
| decision_ref | B21 |
| check_method | schema_lint |
| check_description | Flag native enum columns and long CHECK lists for review against the approved option. |
| lifecycle_stage | Schema Design |

#### TYP-023 Native enums only for static sets

**A native enumeration type MAY be used only for a value set that will not change.**

| Field | Value |
|---|---|
| level | OPTIONAL |
| scope | OLTP |
| applies_when | truly static value sets |
| rationale | A static set avoids a join and a reference table, but a set that later changes becomes costly to alter. |
| exceptions | none |
| engine_notes | [WF] MySQL's online DDL matrix lists ENUM changes; it was read through a summarising fetch and needs a re-check against the page before use. |
| evidence | PGMY-10, research/design_decision_matrix.md#DT-9, research/database_design_standards.md#7.4, research/official_documentation.md#3 |
| evidence_strength | multi_vendor |
| status | active |
| decision_ref | null |
| check_method | manual_review |
| check_description | Review each native enum for evidence that the set is static. |
| lifecycle_stage | Schema Design |

#### TYP-024 JSON use is bounded

**Keys, money and attributes that are filtered or aggregated SHOULD remain typed relational columns and SHOULD NOT be held in entity-attribute-value tables, and JSON SHOULD hold only sparse or externally defined attributes.**

| Field | Value |
|---|---|
| level | RECOMMENDED |
| scope | OLTP |
| applies_when | transactional schemas; lakehouse raw capture is TYP-026 |
| rationale | JSON columns weaken constraints and indexing, and updates can rewrite or lock whole documents. |
| exceptions | none |
| engine_notes | PostgreSQL advises small, atomic documents because any update locks the whole row. MySQL cannot index JSON directly and needs generated columns or multi-valued indexes; PostgreSQL uses GIN. |
| evidence | PGMY-04, MSOM-15, DES-13, research/design_decision_matrix.md#DT-13, research/database_design_standards.md#7.4 |
| evidence_strength | multi_vendor |
| status | active |
| decision_ref | null |
| check_method | manual_review |
| check_description | Review JSON columns and generic attribute tables for embedded keys, money or fields used in filters. |
| lifecycle_stage | Schema Design |

#### TYP-025 Native JSON type

**JSON documents SHOULD be stored in the engine's native JSON type where one exists.**

| Field | Value |
|---|---|
| level | RECOMMENDED |
| scope | OLTP, lakehouse |
| applies_when | engines with a native type |
| rationale | Plain text gives no validation and no path access. |
| exceptions | none |
| engine_notes | PostgreSQL prefers jsonb. Oracle says to use its JSON type for JSON columns. Snowflake and Databricks use VARIANT. SQL:2023 added a JSON type per secondary sources, so portability is engine-dependent. |
| evidence | PGMY-04, MSOM-10, LAKE-01, research/database_design_standards.md#7.4, research/official_documentation.md#2, research/official_documentation.md#5 |
| evidence_strength | multi_vendor |
| status | active |
| decision_ref | null |
| check_method | schema_lint |
| check_description | Flag text columns registered as JSON on engines with a native type. |
| lifecycle_stage | Schema Design |

#### TYP-026 Semi-structured raw capture

**Raw landing layers MAY store source payloads in semi-structured or string form, provided typed columns are applied from the first conformed layer.**

| Field | Value |
|---|---|
| level | OPTIONAL |
| scope | lakehouse, data_warehouse |
| applies_when | raw landing layers; never serving layers |
| rationale | Typing at ingest can lose unparsed data, while carrying semi-structured data further loses the type guarantees downstream. |
| exceptions | none |
| engine_notes | Databricks describes bronze as mostly string, VARIANT or binary. Snowflake advises flattening dates, numbers in strings and arrays. Delta enforces schema by default. |
| evidence | LAKE-01, PIPE-11, research/architecture_comparison.md#C-53, research/design_decision_matrix.md#PL-10, research/design_decision_matrix.md#DT-13 |
| evidence_strength | multi_vendor |
| status | active |
| decision_ref | null |
| check_method | pipeline_test |
| check_description | Confirm conformed tables have no semi-structured columns for fields declared in the contract. |
| lifecycle_stage | ETL/ELT |

#### TYP-027 Decimals declared at analytical landing

**Pipelines that infer schemas SHOULD declare decimal columns explicitly and not rely on inference.**

| Field | Value |
|---|---|
| level | RECOMMENDED |
| scope | lakehouse, streaming |
| applies_when | file or stream ingestion with schema inference |
| rationale | Inference can silently produce a floating type, which breaks TYP-001. |
| exceptions | none |
| engine_notes | Spark inference defaults floats to double unless configured. |
| evidence | PIPE-07, research/design_decision_matrix.md#DT-14 |
| evidence_strength | single_vendor |
| status | active |
| decision_ref | null |
| check_method | pipeline_test |
| check_description | Compare inferred output types with the contract's declared decimals. |
| lifecycle_stage | ETL/ELT |

### Identifiers

#### TYP-028 Numeric-looking identifiers are strings

**Codes and identifiers that look numeric but are not quantities SHOULD be stored as strings.**

| Field | Value |
|---|---|
| level | RECOMMENDED |
| scope | all |
| applies_when | codes with possible leading zeros or no arithmetic meaning |
| rationale | Numeric storage strips leading zeros: ISO 4217 numeric code 048 shows this directly. Phone, postal and national identifiers are inference. |
| exceptions | none |
| engine_notes | none |
| evidence | DES-11, research/design_decision_matrix.md#DT-10, research/database_design_standards.md#7.1 |
| evidence_strength | standard |
| status | active |
| decision_ref | null |
| check_method | manual_review |
| check_description | Review numeric columns whose names suggest codes. |
| lifecycle_stage | Schema Design |

#### TYP-029 Width of generated integer keys

**Generated integer keys SHOULD be 64-bit, unless the table is a bounded lookup table.**

| Field | Value |
|---|---|
| level | RECOMMENDED |
| scope | OLTP |
| applies_when | tables keyed by a generated integer |
| rationale | A 32-bit key that runs out is an outage and a difficult migration, and referencing columns need widening too. |
| exceptions | Bounded lookup tables may use 32-bit keys. |
| engine_notes | Evidence is an incident report and framework defaults; storage cost is not quantified. |
| evidence | DES-22, PGMY-02, research/design_decision_matrix.md#DT-11, research/database_design_standards.md#4.3 |
| evidence_strength | case_study |
| status | active |
| decision_ref | A3 |
| check_method | schema_lint |
| check_description | Flag 32-bit generated keys on tables not registered as bounded lookups. |
| lifecycle_stage | Schema Design |

#### TYP-030 UUIDs in binary form

**UUIDs SHOULD be stored in a native 16-byte type or equivalent binary form and not as text.**

| Field | Value |
|---|---|
| level | RECOMMENDED |
| scope | OLTP |
| applies_when | tables keyed or referenced by UUID |
| rationale | Text storage increases size and slows comparison. Key-type performance overall remains a judgment because no peer-reviewed or vendor-neutral benchmark exists. |
| exceptions | none |
| engine_notes | PostgreSQL has a native type and generates version 4 and 7 values. MySQL needs BINARY(16). Ordering and version are decided in the keys standards. |
| evidence | DES-04, PERF-15, DES-15, BENCH-01, BENCH-05, research/design_decision_matrix.md#DT-12 |
| evidence_strength | single_vendor |
| status | active |
| decision_ref | A3 |
| check_method | schema_lint |
| check_description | Flag columns registered as UUID with a text type. |
| lifecycle_stage | Schema Design |

#### TYP-031 Warehouse surrogate key type

**Dimensional surrogate keys SHOULD be numeric, unless hash or string keys are chosen and recorded under IDX-024.**

| Field | Value |
|---|---|
| level | RECOMMENDED |
| scope | data_warehouse, lakehouse |
| applies_when | dimensional and Data Vault models |
| rationale | Parallel, idempotent loads favour hashes while join and clustering performance favours integers. No benchmark exists in the research, so this is a judgment (C-11). |
| exceptions | Hash keys where parallel or idempotent loads are decisive, approved by the framework exception approver. |
| engine_notes | Snowflake strongly recommends numeric join keys, and prefers numeric surrogates over MD5 hash keys for Data Vault. The dbt style guide says string keys; its Kimball tutorial and Databricks' Data Vault guidance use hash keys. Superseded by IDX-024 under OR-3. |
| evidence | DWM-01, LAKE-14, LAKE-16, DWM-21, LAKE-05, research/architecture_comparison.md#C-11, research/official_documentation.md#13 |
| evidence_strength | multi_vendor |
| status | superseded |
| decision_ref | A4 |
| superseded_by | IDX-024 |
| check_method | catalog_query |
| check_description | List surrogate key columns by type and compare with the approved option. |
| lifecycle_stage | Schema Design |

### NULL policy

#### TYP-032 Primary key columns are NOT NULL

**Primary key columns MUST be declared NOT NULL.**

| Field | Value |
|---|---|
| level | MANDATORY |
| scope | all |
| applies_when | always |
| rationale | A key that can be NULL does not identify its row. |
| exceptions | none |
| engine_notes | Engines force this for enforced keys. Snowflake standard tables and Databricks treat primary keys as informational, so declare NOT NULL explicitly, which they do enforce. |
| evidence | PGMY-01, MSOM-02, LAKE-09, LAKE-02, research/database_design_standards.md#7.5 |
| evidence_strength | multi_vendor |
| status | active |
| decision_ref | null |
| check_method | schema_lint |
| check_description | Confirm all primary key columns are NOT NULL in the catalog. |
| lifecycle_stage | Data Validation |

#### TYP-033 NOT NULL by default

**Columns SHOULD be NOT NULL unless absence has a documented meaning.**

| Field | Value |
|---|---|
| level | RECOMMENDED |
| scope | all |
| applies_when | always; on analytical platforms apply where the column is loaded under a contract |
| rationale | Undocumented NULLs are ambiguous and bring three-valued logic to every predicate. |
| exceptions | Raw landing objects, where absence is defined by the source. |
| engine_notes | Superseded by INT-008 under OR-19. |
| evidence | PGMY-01, PERF-17, research/design_decision_matrix.md#RI-5, research/database_design_standards.md#7.5 |
| evidence_strength | multi_vendor |
| status | superseded |
| decision_ref | null |
| superseded_by | INT-008 |
| check_method | schema_lint |
| check_description | List nullable columns with no recorded meaning of absence. |
| lifecycle_stage | Data Validation |

#### TYP-034 UNIQUE on nullable columns is engine-specific

**Each UNIQUE rule on a nullable column SHOULD state its intended NULL behaviour for each target engine, and SHOULD NOT assume one portable behaviour.**

| Field | Value |
|---|---|
| level | RECOMMENDED |
| scope | OLTP, data_warehouse |
| applies_when | any uniqueness rule that includes a nullable column |
| rationale | The same declaration admits many NULLs on one engine and one on another, so uniqueness silently changes on migration. There is no portable default (C-83). |
| exceptions | none |
| engine_notes | PostgreSQL: NULLs distinct by default, changeable with NULLS NOT DISTINCT. MySQL 8.4 [WF]: many NULLs. SQL Server [WF]: one NULL per column in a UNIQUE constraint; a filtered unique index tolerating many NULLs is an inference. Oracle Release 26 [WF]: an all-NULL key satisfies the constraint, while two rows with NULLs in some key columns and equal other values violate it. Databricks: NULLs distinct in its preview UNIQUE, which is informational. [WF] The MySQL, SQL Server and Oracle behaviours were read through a summarising fetch and need a re-check against the page before use. |
| evidence | PGMY-01, ENG-05, ENG-10, ENG-15, LAKE-02, research/architecture_comparison.md#C-83, research/design_decision_matrix.md#RI-7, research/database_design_standards.md#7.5 |
| evidence_strength | multi_vendor |
| status | active |
| decision_ref | null |
| check_method | manual_review |
| check_description | List unique constraints with nullable columns and confirm the design record states behaviour per engine. |
| lifecycle_stage | Data Validation |

#### TYP-035 CHECK needs NOT NULL

**A CHECK rule that must always hold MUST be paired with NOT NULL on the columns it tests.**

| Field | Value |
|---|---|
| level | MANDATORY |
| scope | all |
| applies_when | CHECK rules on nullable columns, on engines enforcing CHECK |
| rationale | A CHECK passes when its expression is NULL, so a NULL value escapes the rule. |
| exceptions | Columns where NULL has a documented meaning and the rule applies only to present values. |
| engine_notes | CHECK passing on NULL is shown for PostgreSQL and MySQL. SQL Server also passes on UNKNOWN. Snowflake hybrid tables apply CHECK only at creation. Superseded by INT-009 under OR-20. |
| evidence | PGMY-01, PGMY-15, research/design_decision_matrix.md#RI-6, research/database_design_standards.md#7.5 |
| evidence_strength | multi_vendor |
| status | superseded |
| decision_ref | null |
| superseded_by | INT-009 |
| check_method | schema_lint |
| check_description | List CHECK constraints whose columns are nullable and confirm the intent. |
| lifecycle_stage | Data Validation |

#### TYP-036 No in-domain values for unknown

**An ordinary in-domain value SHOULD NOT be used to represent unknown or missing data.**

| Field | Value |
|---|---|
| level | RECOMMENDED |
| scope | all |
| applies_when | always |
| rationale | A real-looking value used for unknown corrupts aggregates and filters. |
| exceptions | A documented end-of-time convention on a period column is a different case and must be declared. Dimension default rows are covered by RPT-006. |
| engine_notes | SQL Server temporal tables use 9999-12-31 for open rows, and dbt snapshots use NULL or a configurable value. MySQL non-strict mode can silently store an empty string for an invalid ENUM value. |
| evidence | DES-12, DWM-01, DWM-02, research/design_decision_matrix.md#RI-10, research/database_design_standards.md#7.5 |
| evidence_strength | single_vendor |
| status | active |
| decision_ref | null |
| check_method | pipeline_test |
| check_description | Profile columns for high-frequency placeholder values. |
| lifecycle_stage | Data Quality |

#### TYP-037 Default dimension rows

**Dimensional fact foreign keys MUST reference a default dimension row in place of NULL.**

| Field | Value |
|---|---|
| level | MANDATORY |
| scope | data_warehouse |
| applies_when | Kimball-style dimensional fact tables only; this is an obligation inside the method, not a general rule |
| rationale | A NULL fact key drops rows from inner joins, so totals change by query path. |
| exceptions | Non-dimensional models, which follow TYP-033. |
| engine_notes | Level aligned to MANDATORY under owner decision H2. Superseded by RPT-006 under OR-1. |
| evidence | DWM-01, DWM-02, research/design_decision_matrix.md#RP-5, research/database_design_standards.md#7.5 |
| evidence_strength | single_vendor |
| status | superseded |
| decision_ref | H2 |
| superseded_by | RPT-006 |
| check_method | pipeline_test |
| check_description | Test fact tables for NULL dimension keys. |
| lifecycle_stage | Reporting |

#### TYP-038 NOT EXISTS over NOT IN

**Query logic SHOULD use NOT EXISTS, and SHOULD NOT use NOT IN where the compared values can be NULL.**

| Field | Value |
|---|---|
| level | RECOMMENDED |
| scope | all |
| applies_when | query and transformation code |
| rationale | NOT IN returns no rows when the list holds a NULL, and it can also plan poorly. |
| exceptions | none |
| engine_notes | none |
| evidence | PGMY-10, research/database_design_standards.md#7.5 |
| evidence_strength | single_vendor |
| status | active |
| decision_ref | null |
| check_method | manual_review |
| check_description | Search query and model code for NOT IN over nullable columns. |
| lifecycle_stage | Reporting |

#### TYP-039 Country and language codes

**Country and language columns SHOULD use the maintained ISO 3166 and ISO 639 code lists and SHOULD NOT use locally invented codes.**

| Field | Value |
|---|---|
| level | RECOMMENDED |
| scope | all |
| applies_when | columns holding a country or a language; PROVISIONAL because the ISO sources are unverified |
| rationale | Invented codes cannot be exchanged or reported reliably across systems. This follows matrix row DT-15 by analogy with currency codes, and the evidence for these two lists is unverified. |
| exceptions | A proprietary list, with a recorded reason, approved by the framework exception approver. |
| engine_notes | The ISO 3166 and ISO 639 pages returned 403 during research and were seen only through search results (GOV-19, GOV-22; research_gaps.md). Re-check before relying on this rule. No code element, such as alpha-2 or alpha-3, is prescribed because the unverified pages do not settle it. ISO 4217 is covered by TYP-005 and TYP-006. Evidence is recorded as inference although the matrix labels DT-15 Standard, partly unverified. |
| evidence | GOV-19, GOV-22, research/design_decision_matrix.md#DT-15, research/data_engineering_principles.md#MOD-06, research/research_gaps.md#Governance and international standards (note 08) |
| evidence_strength | inference |
| status | provisional |
| decision_ref | null |
| check_method | catalog_query |
| check_description | List country and language columns and confirm each reconciles to the ISO list or records its proprietary list. |
| lifecycle_stage | Schema Design |

## Classification record

Departures from `design_decision_matrix.md`, and cases where the matrix and `database_design_standards.md` differ. Rows below record the position before the owner decisions of 2026-11-08. Each rule's level, status and decision_ref fields show the current position. TYP-037 is MANDATORY and superseded by RPT-006 (decision H2, OR-1).

| Rule | Matrix or research label | This file | Reason |
|---|---|---|---|
| TYP-010, TYP-011 | FN-19: no classification, evidence gap | RECOMMENDED, `provisional`, no figure set | The brief requires a provisional rule. Only exactness and a recording duty are stated; no precision is proposed. |
| NAM-001 | NM-1 RECOMMENDED; section 6.2 MANDATORY | RECOMMENDED | Follows the matrix. The ISO draft's documentation duty binds metadata registries only. |
| NAM-002 | Matrix note: only consistency is MANDATORY | MANDATORY, `needs_decision` | Organizational choice permitted by `RULE_FORMAT.md`, until the owner approves. |
| NAM-006 | No matrix row; section 6.2 MANDATORY | MANDATORY | Follows section 6.2. The ASCII narrowing comes from the PostgreSQL wiki's advice and the length derivation. |
| NAM-013 | NM-6 OPTIONAL, listed as open with no default | RECOMMENDED, `needs_decision` | The brief and `RULE_FORMAT.md` require one proposed default. The sources still disagree. |
| NAM-012, NAM-017, NAM-020, NAM-021, NAM-023 | NM-2, NM-7, NM-8, NM-9 RECOMMENDED | RECOMMENDED, `needs_decision` | Level unchanged. Status reflects organizational choice. |
| TYP-005 | DT-3 RECOMMENDED; section 7.1 MANDATORY | RECOMMENDED | Follows the matrix. |
| TYP-012 | DT-4 RECOMMENDED; section 7.2 MANDATORY | RECOMMENDED | Follows the matrix. |
| TYP-020 | No matrix row; section 7.3 MANDATORY, grounded partly in a Karwin title | RECOMMENDED | The remaining support is MySQL only. Karwin anti-pattern names may not be presented as source-verified. |
| TYP-022 | DT-9 RECOMMENDED with DES-13 cited | RECOMMENDED, `needs_decision`; DES-13 removed | `research_gaps.md` section 6.2: the Karwin remedy is unverified. Sources disagree on the default. |
| TYP-036 | RI-10 RECOMMENDED, DW; section 7.5 MANDATORY, all | RECOMMENDED, all | Level follows the matrix. Scope follows section 7.5. Kimball alone cannot carry a MUST. |
| TYP-037 | RP-5 MANDATORY (Kimball method) | RECOMMENDED | `RULE_FORMAT.md` requires an authoritative source for MANDATORY. A method owner's rule is not one, so the obligation is stated inside the method only. |

## Decisions needing owner approval

Answered by the owner on 2026-11-08: all defaults accepted. See `../DECISIONS_TO_APPROVE.md` for the decision log, and each rule's decision_ref for its decision number. Questions and alternatives are kept for the record.

| # | Question | Proposed default | Alternatives | Consequence of each |
|---|---|---|---|---|
| 1 | Is compliance with the approved convention binding (NAM-002)? | Yes, for all new objects | Advisory only | Binding: lintable, with occasional exception requests. Advisory: drift returns and automated checks lose value. |
| 2 | Which case style (NAM-012)? | Lowercase with underscores | Mixed case | Default: portable; Oracle and Snowflake show the names in upper case. Mixed: requires quoting, against NAM-008. |
| 3 | Singular or plural tables (NAM-013, NP-01, NP-29, NP-30)? Judgment: no source reports an outcome difference. | Plural everywhere, including marts | Singular everywhere; plural for operational tables and singular for dimensional objects | Plural: matches more table-level examples, differs from Django and Alibaba and from dbt's Kimball tutorial. Singular: matches those and simplifies key names, but needs overrides in Rails-style frameworks. Mixed: fits each community, at the cost of two rules to lint. |
| 4 | Portable identifier ceiling (NAM-010)? | 63 ASCII characters | Limit of the single engine in use; 30 bytes | 63: safe on every current engine in the research. Single-engine: more room, and a migration later can fail. 30: needed only for Oracle below COMPATIBLE 12.2; forces heavy abbreviation. |
| 5 | How strict on abbreviations (NAM-014), given unresolved C-25? | Full words, with an approved register | No abbreviations at all; short names favoured, as MySQL's page suggests | Register: readable, with a small upkeep cost. None: long constraint names can exceed the ceiling. Short: compact, less discoverable, and against Oracle and dbt guidance. |
| 6 | Named or unqualified primary key column (NAM-017, NAM-018)? | Named, as in NP-02 | Unqualified key name, as ORMs default to | Named: joins read clearly across models; ORM mapping needs configuration. Unqualified: least ORM effort; every join needs table qualification. |
| 7 | Adopt the third-party identifier marker (NAM-019, NP-05)? | Yes | Treat all identifiers alike | Adopt: real keys are distinguishable from external references. Decline: relationship inference by name becomes unreliable. |
| 8 | Adopt the semantic patterns (NAM-020, NAM-021, NAM-028)? | Yes | No semantic patterns | Adopt: type intent visible in the name; renames for inherited schemas are exempted. Decline: meaning must be looked up. |
| 9 | Status column pattern (NAM-022, NP-11)? No source. | Lifecycle-qualified | One standard unqualified status name | Qualified: a table can track several lifecycles. Unqualified: shorter, but breaks once a second lifecycle appears. |
| 10 | Constraint and index naming (NAM-023, NP-16 to NP-21)? | GitLab-style typed prefixes, table and columns | Shorter prefixes; engine-generated names | Typed: names are comparable across environments, under length pressure. Shorter: less length pressure, not supported by a named source. Generated: differ per environment and break migrations. |
| 11 | Schema naming (NAM-024, NP-22)? No source. | Business domain | Team or technology names | Domain: stable through reorganizations. Team: clearer ownership today; renames follow reorganizations. |
| 12 | Layer vocabulary (NAM-025, NP-23 to NP-26)? | Raw, staging, intermediate, marts | Bronze, silver, gold | Default: says what each layer does, and matches dbt. Medallion: matches Databricks and Fabric usage, with less precise meaning at silver. |
| 13 | Snapshot schema and mart markers (NAM-026, NAM-027, NP-27 to NP-30)? | As in the pattern table | No role markers, with layer schema alone | Markers: join role visible in the name; only the dimension marker has a source. None: shorter; role must be documented elsewhere. |
| 14 | Measure column patterns and minor units (NAM-028, TYP-007, NP-12 to NP-15)? | Exact decimal, with integer minor units as a marked exception | Integer minor units as the default | Decimal: matches vendor manuals and handles varying scale; slower arithmetic. Integer: fast, but needs currency-aware conversion everywhere. |
| 15 | Enumerated values (TYP-022)? | Reference table when the set can change or has attributes | CHECK on text; native enumeration | Reference table: changes are data, at the cost of a join. CHECK: simple, each change is a migration. Native: compact, and PostgreSQL cannot remove values. |
| 16 | Warehouse surrogate key type (TYP-031)? Judgment: no benchmark in the research. | Numeric | Deterministic hash key stored as a string | Numeric: favoured for joins and clustering; needs key assignment during load. Hash: parallel, idempotent loads; wider keys. |
| 17 | Exchange-rate precision (TYP-010, TYP-011)? No vendor or standard-setter read states one (FN-19). | Exact decimal holding the full precision the rate source delivers. No framework-wide figure is proposed. | A fixed framework-wide precision and scale, once a source exists or the owner sets one by judgment | Delivered precision: no silent loss; column definitions may vary by provider. Fixed: uniform columns, but any figure today would be unsupported and could truncate a provider's rate. |
| 18 | Quantity scale and unit (TYP-009, NP-15)? No source. | Unit stored or fixed by definition, with scale declared per unit | One fixed scale for all quantities | Per unit: accurate; more design records. Fixed: uniform, and either wastes storage or rounds small units. |
| 19 | Mixed-currency minimum scale (TYP-004)? Low-confidence inference. | At least 4 | Exact per-currency scale only, with no minimum | 4: holds CLF and UYW without per-currency handling. Per-currency only: tighter, but a column holding multiple currencies must still accept the largest. |
| 20 | Raw layer exceptions (NAM-007)? Inference. | Source names preserved in raw only | Rename at ingest | Preserve: direct trace to source; unsafe names exist in raw. Rename: uniform, with loss of direct traceability. |
