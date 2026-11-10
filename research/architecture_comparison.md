# Architecture Comparison: Phase 3 Comparative Analysis

Status: research only. No schemas, no implementation. Input to a later technology-independent Database Schema Design and Data Engineering Standards Framework covering ERP, financial, SaaS and data engineering systems.

Evidence base: the topic notes 01 to 23 in `research_notes/Database schema design framework research/`, read with `CORRECTIONS.md` and the verification results of note 22 applied, and `research/resource_catalog.json`. No web research was done and no source outside the notes is added.

## 0. How to read this document

| Convention | Meaning |
|---|---|
| Catalog ID (for example `PGMY-01`) | A resource in `resource_catalog.json`. Prefixes: PGMY PostgreSQL/MySQL, MSOM SQL Server/Oracle/MongoDB, CLOUD cloud frameworks, LAKE lakehouse/warehouse platforms, PIPE pipelines, DWM warehouse methods, ARCH architecture paradigms, GOV standards and governance, SEC security, DES core design, PERF performance, TXN transactions, OPS migrations and recovery, TEN tenancy/audit/temporal, DQ quality and lineage, LIT literature, CASE case studies. |
| `[Title](URL)` | A source cited in the notes that has no catalog entry of its own. |
| `[INFERENCE]` | This author's synthesis. It is not stated by the cited sources in that form, and it should be challenged before it becomes a standard. |
| MANDATORY | Used only when an authoritative source supports it: a standard, law or foundational paper, or official documentation from at least two independent vendors. Scope conditions are stated, and a statute binds only in its own jurisdiction. |
| [WF] | Read only through a summarising fetch tool, so the figure or wording is unconfirmed against raw text. |
| RECOMMENDED | Sources advise it, or a method owner prescribes it, but exceptions are legitimate or no authoritative mandate exists. |
| OPTIONAL | A pattern whose use depends on context. |
| Workload terms | OLTP, OLAP, data warehouse (DW), lakehouse and streaming are kept distinct throughout. OLAP is a workload and query style, DW an integrated analytical store, lakehouse a storage and table architecture, streaming a processing and transport model. |

Handling rules applied from `CORRECTIONS.md` and the brief:

- Web-page wording is paraphrased. No quotation marks are used for web-page text, because most pages were read through a summarising fetch tool.
- Claims the corrections file withdraws or note 22 could not find are omitted. Omitted items include the DDIA wording on the C in ACID, Karwin's remedies, PACELC system classifications, the unsourced Snowflake-as-template claim, record-level versioning for optimistic locking in ERP frameworks, Frappe standard columns, and the unsupported case-study claims listed there. Note 22 lifts the restriction on the Testcontainers definition and confirms the MongoDB transaction error labels and ORA-01555.
- Practitioner and vendor benchmarks are not independent evidence, and none was reproduced here (note 23). Merged catalog IDs are used where notes give another: BENCH-09 is DWM-22, ENG-03 is PGMY-16, ENG-04 is PGMY-13, THIN-01 is GOV-27, THIN-17 is OPS-16, THIN-19 is OPS-13.
- Sources with `url_verified=false` are avoided. Where one is used it is marked (unverified).
- Oracle `/23/` URLs report Release 26 in page metadata (note 22), so no 23ai provenance is claimed.

## 1. Summary of findings

[INFERENCE] The comparison across notes 01 to 23 supports seven conclusions.

1. Very few rules are universal, and those few concern meaning rather than form: exact money, declared identity, the semantics of NULL and constraints, restore-tested recovery, least privilege, idempotent reprocessing, and additive schema change.
2. Most physical advice is conditional on engine topology. Key ordering, foreign key indexing, default isolation, string sizing and partition behaviour all change between clustered, heap, range-sharded and columnar engines, so a technology-independent standard must state these rules as conditionals.
3. OLTP, OLAP, DW, lakehouse and streaming differ most in where integrity is enforced. OLTP enforces it at write time in the engine. DW and lakehouse enforce only a subset and move the rest into pipelines and tests. Streaming enforces it by contract at the producer and by idempotence at the consumer.
4. Modeling methodology and storage architecture are now independent decisions. Medallion layering, Kimball, Inmon and Data Vault answer different questions and are composable.
5. Most apparent conflicts in the register (Part C) dissolve once workload, engine version or topology is specified. The open ones are mostly about style and defaults.
6. Evidence is uneven. Transactions, recovery, indexing and regulation are well sourced. Fiscal-period status, rate tables and reversals now have multi-vendor product evidence (B7), and law binds them only in stated jurisdictions. Rate precision, triangulation, numeric quality targets, schema-per-tenant cost and defect-catch rates of validation layers are still unsupported (Part D).
7. Most performance comparisons remain judgments. Note 23 found no independent evidence for key types, RLS overhead, foreign keys at scale or Data Vault against star (B9). The One Big Table result is engine-dependent (C-84).

---

# Part A. Findings

## A1. Principles that apply universally

Scope for this table is every workload unless the caveat column narrows it. A principle appears here only if at least two independent authoritative sources support it.

| # | Principle | Class | Evidence | Caveat or scope limit |
|---|---|---|---|---|
| U1 | Exact decimal representation for money; no binary floating point | MANDATORY | PGMY-02, MSOM-03, MSOM-10, MSOM-18, DES-22, DES-20 | A dbt style example casts an amount to float, against this rule (`LAKE-16`, see C-27). Integer minor units are an accepted equivalent. |
| U2 | CHECK constraints pass when the expression is NULL or UNKNOWN, so a rule that must always hold needs NOT NULL as well | MANDATORY (semantics) | PGMY-01, PGMY-15 | Verified for PostgreSQL and MySQL only in the notes. |
| U3 | Every system-of-record table has a declared primary key | MANDATORY for OLTP base tables | DES-01, PGMY-01, PGMY-12, MSOM-02, TEN-28 | Vendors phrase it as strong best practice. The MANDATORY elevation rests on Codd's definition and on logical replication and CDC needing row identity. Analytical platforms treat keys as informational (U6). |
| U4 | Declare integrity in the engine wherever the engine enforces it | MANDATORY for OLTP; RECOMMENDED elsewhere | MSOM-08, PGMY-01, MSOM-02, DES-18 | Documented exceptions come from sharding and shadow-table online DDL (C-08). |
| U5 | Know which constraints the platform enforces; declared is not the same as enforced | MANDATORY (semantics) | LAKE-02, LAKE-09, DQ-03, MSOM-12, ENG-23 | Snowflake standard tables and Databricks enforce NOT NULL and CHECK; PK, FK and UNIQUE are informational. Snowflake hybrid tables enforce them (LAKE-09). Redshift enforces NOT NULL and treats PK, FK and UNIQUE as informational (ENG-23). |
| U6 | Partition key columns must be part of every unique key on natively partitioned tables | MANDATORY (engine rule) | PGMY-06, PGMY-16 | Holds for PostgreSQL and MySQL in the notes; aligned uniqueness on SQL Server is the equivalent noted in note 11. |
| U7 | Replicas, snapshots and table history are not backups | MANDATORY | MSOM-07, OPS-20, OPS-21, LAKE-11, [Delta history](https://docs.databricks.com/aws/en/delta/history) | Replication, snapshots and time travel serve availability and bounded recovery windows. |
| U8 | A backup is not proven until a restore has been tested | MANDATORY | OPS-17, OPS-19, OPS-22, CLOUD-10, CASE-51 | Strongest single rule across the notes. CASE-51 is the failure case. |
| U9 | Least privilege, with the application separated from object ownership | MANDATORY | SEC-08 (AC-6), SEC-01, SEC-07, TEN-11 | PostgreSQL owners bypass RLS unless forced (PGMY-07). |
| U10 | Bind parameters on every database access path | MANDATORY | SEC-02, SEC-03, SEC-06 | Applies to dynamic SQL in pipelines and stored procedures as well (note 09 inference). |
| U11 | Masking, redaction and at-rest encryption are bounded controls, not security boundaries | MANDATORY when claiming protection beyond their threat model | SEC-25, MSOM-13, SEC-24, SEC-04, SEC-17 | PCI DSS 3.5.1.2 explicitly rejects disk-level encryption alone for PAN. |
| U12 | Do not rely on an isolation level's name; state the guarantee per engine and configuration | MANDATORY | TXN-03, TXN-10, TXN-11, TXN-08, PGMY-08 | See engine matrix B2. |
| U13 | Retry whole transactions that fail with serialization, deadlock or write-conflict errors | MANDATORY for OLTP | PGMY-08, MSOM-18, [SQL Server deadlocks guide](https://learn.microsoft.com/en-us/sql/relational-databases/sql-server-deadlocks-guide) | The signal differs by engine. |
| U14 | Read-then-write invariants need serializable execution, explicit locks or a declarative constraint on snapshot-class engines | MANDATORY for OLTP | TXN-03, TXN-04, PGMY-08 | Write skew is allowed by snapshot isolation by construction. |
| U15 | Consumers and pipeline steps must tolerate re-delivery and re-runs | MANDATORY for CDC, streaming and scheduled pipelines | PIPE-01, PIPE-06, PIPE-08, PIPE-13 | Applies wherever delivery is at-least-once or runs can repeat. |
| U16 | Additive nullable change is the only schema change safe across table formats and registries | RECOMMENDED | PIPE-02, PIPE-10, PIPE-11, PIPE-12, DQ-03 | Int-to-long, float-to-double and decimal precision widening are also safe across the formats (note 05). |
| U17 | Incompatible change passes through a transition where old and new coexist | RECOMMENDED | OPS-01, OPS-02, OPS-05, OPS-06, CASE-23 | Sources are operators and method authors, not standards. |
| U18 | Schema change is scripted, version-controlled and applied by tooling | RECOMMENDED | OPS-15, OPS-01, OPS-10, OPS-11, CLOUD-18 | No standard mandates it; DORA supplies the research basis. |
| U19 | Name the two time dimensions (valid or application time, and system or transaction time) separately | RECOMMENDED | GOV-06, TEN-21, TEN-23, MSOM-04 | Vendors use temporal table to mean different things (C-32). |
| U20 | Store periods as closed-open intervals | RECOMMENDED | GOV-06, TEN-23, MSOM-04 | SQL Server and SQL:2011 BETWEEN syntax is inclusive at the upper bound (C-33). |
| U21 | Choose the data store by workload and access pattern, not by habit | RECOMMENDED | CLOUD-01, CLOUD-17, PERF-38 | Azure adds a warning against premature fragmentation (CLOUD-17). |
| U22 | Index from the query pattern; every index taxes writes | RECOMMENDED | MSOM-01, MSOM-09, MSOM-15, PERF-17, PGMY-05 | Thresholds are qualitative; no vendor gives a maximum index count. |
| U23 | Retention has a documented basis per record class | MANDATORY where GDPR or 21 CFR Part 11 applies | TEN-34, TEN-17, SEC-15, LEG-03, LEG-05, LEG-13, LEG-18, LEG-23, LEG-25 | Elsewhere this is RECOMMENDED. Periods differ by jurisdiction, record class and start event, and bind only in that jurisdiction (matrix LG-16 to LG-24). |
| U24 | Separate read-optimized analytical shapes from write-optimized transactional shapes | RECOMMENDED | PERF-38, PERF-39, CLOUD-16, PGMY-12 | HTAP replicas narrow but do not remove the split (PERF-02, PERF-49). |

## A2. Principles that depend on the engine

The rule varies because a physical fact varies. Each row names that fact. The last column is a proposal.

| # | Topic | What varies | Sources | Consequence for the framework ([INFERENCE]) |
|---|---|---|---|---|
| E1 | Primary key shape | SQL Server and InnoDB embed the clustered key in every secondary index, so narrow ever-increasing keys matter. PostgreSQL stores rows in a heap and every index is secondary. | MSOM-01, PGMY-12, PERF-07 | State narrow-key and insert-order rules as clustered-engine rules only. |
| E2 | Key distribution | Single-node B-tree engines favour ordered keys. Spanner and CockroachDB warn against monotonic keys and recommend UUID v4 or hashing. | MSOM-01, CLOUD-11, PERF-48, CASE-01, TEN-42 | Key rule is conditional on topology. Never one rule for both. |
| E3 | Foreign key indexing | InnoDB creates the index automatically. PostgreSQL does not. Oracle ties it to avoiding full table locks. SQL Server says it is not required but often useful. | PGMY-14, PGMY-01, PERF-24, MSOM-02 | RECOMMENDED default with engine-specific notes (C-10). |
| E4 | FK deferral and actions | PostgreSQL supports deferrable FKs and SET DEFAULT, MySQL rejects SET DEFAULT and treats NO ACTION as RESTRICT, Oracle supports deferrable constraints. The SQL Server CREATE TABLE grammar read shows no deferral syntax [WF]. | PGMY-01, PGMY-14, MSOM-08, ENG-10, ENG-15 | Portable designs cannot assume deferral. SQL Server non-support is inferred from the grammar, and no explicit statement was located. |
| E5 | Default isolation | PostgreSQL and Oracle READ COMMITTED; InnoDB REPEATABLE READ; SQL Server locking READ COMMITTED; Azure SQL Database and Fabric SQL use RCSI. | PGMY-08, PGMY-18, MSOM-06, TXN-08 | Set isolation explicitly per transaction class (note 01). |
| E6 | What SERIALIZABLE means | PostgreSQL uses SSI. SQL Server uses key-range locks. Oracle SERIALIZABLE is snapshot isolation and permits write skew. InnoDB is lock-based and depends on autocommit. | TXN-04, MSOM-06, TXN-10, TXN-11 | Key guarantees to engine, level and flags. |
| E7 | Partitioning limits | MySQL forbids foreign keys on either side of partitioned InnoDB tables and caps partitions at 8192. PostgreSQL allows FKs to reference partitioned tables since 12; the child side was not confirmed. | PGMY-16, PGMY-06, ENG-08 | Do not assume FK plus partitioning is portable. |
| E8 | Identifier limits and case | PostgreSQL 63 bytes and lower-case folding; MySQL 64 characters and file-system dependent table case; SQL Server 128 characters; Oracle 128 bytes, or 30 bytes below COMPATIBLE 12.2. Snowflake and Databricks Unity Catalog object names 255 characters. | PGMY-09, PGMY-17, MSOM-10, ENG-20, ENG-30 | Portable ceiling depends on the oldest Oracle target (C-22). |
| E9 | String sizing | PostgreSQL reports no performance difference between text and varchar and its wiki discourages arbitrary limits. MySQL advises the smallest types and has index prefix limits. | PGMY-10, PERF-17 | Engine annex, not a universal rule (C-21). |
| E10 | Money type names | numeric or DECIMAL; decimal rather than money on SQL Server; NUMBER on Oracle; Decimal128 on MongoDB. | PGMY-02, MSOM-03, MSOM-10, MSOM-18 | Principle universal, type name engine-specific. |
| E11 | Instant types | timestamptz stores UTC. MySQL TIMESTAMP converts to UTC and ends in 2038; DATETIME does not convert. SQL Server offers datetime2 and datetimeoffset. | PGMY-03, PGMY-13, MSOM-03 | UTC-normalized instant is the principle; the type is an annex. |
| E12 | JSON | PostgreSQL jsonb is directly GIN-indexable; MySQL indexes JSON through generated columns or multi-valued indexes; MongoDB is document-native. | PGMY-04, PERF-17, MSOM-15 | SQL JSON typing is vendor-specific in practice (note 08). |
| E13 | Row-level security | PostgreSQL has superuser, BYPASSRLS and owner bypass unless forced. SQL Server applies policies to dbo, though dbo can alter them. Oracle VPD does not bind SYS or default DBA roles. No MySQL row-level feature was found in pages read [WF], which is absence of evidence only. | PGMY-07, MSOM-05, MSOM-13, ENG-06 | Isolation requirements must name the bypass set per engine (C-14). |
| E14 | System-time and valid-time history | SQL Server and MariaDB provide system versioning only; Oracle offers both; PostgreSQL 18 adds temporal constraints but not system versioning; MongoDB has an application pattern. | MSOM-04, TEN-20, TEN-21, PERF-16, MSOM-14 | On PostgreSQL, history requires emulation. |
| E15 | Online DDL | MySQL 8.4 defaults to INSTANT where possible with a row-version cap. PostgreSQL relies on CONCURRENTLY and NOT VALID. | OPS-09, OPS-05, OPS-07 | Safe-migration tables are engine annexes tied to versions. |
| E16 | Transactional DDL | PostgreSQL and SQLite yes; MySQL and Oracle no. | [Django migrations](https://docs.djangoproject.com/en/5.2/topics/migrations/), [Flyway undo](https://documentation.red-gate.com/fd/undo-migrations-273973334.html) | Failure semantics of a migration depend on this. SQL Server not verified. |
| E17 | Warehouse indexing | Oracle DW uses bitmap indexes; SQL Server uses clustered columnstore; cloud warehouses use partitioning and clustering. | MSOM-12, PERF-02, CLOUD-13, LAKE-10 | Warehouse physical rules are per platform. |
| E18 | MPP distribution | Redshift DISTKEY and SORTKEY, Synapse hash distribution, BigQuery partition plus cluster. | CLOUD-08, CLOUD-13, [Synapse tables overview](https://learn.microsoft.com/en-us/azure/synapse-analytics/sql-data-warehouse/sql-data-warehouse-tables-overview) | Treat distribution and clustering keys as schema decisions with cost consequences (note 03). |
| E19 | Partitioning versus clustering in lakehouse | Databricks recommends liquid clustering for new tables and it replaces partitioning. Iceberg offers hidden partitioning. Delta and Hudi expose partition columns. | LAKE-03, PIPE-10, PIPE-11, PIPE-12 | Model clustering as mutable, not schema-fixing. |
| E20 | Rename and drop in table formats | Iceberg is metadata-only with field IDs. Delta needs column mapping or rewrite. Hudi needs an experimental, irreversible switch. | PIPE-10, PIPE-11, PIPE-12 | Portable rule is the intersection only. |
| E21 | Integer width | Snowflake treats integer types as NUMBER(38,0) with storage sized by value. Width is a real decision on other engines. | [Snowflake numeric types](https://docs.snowflake.com/en/sql-reference/data-types-numeric), PGMY-02 | Do not generalise integer-width rules to Snowflake (note 04). |
| E22 | Backup primitives | WAL, binary log, transaction log and archived redo differ in tooling but share shape: base backup plus continuous log. | PGMY-11, PGMY-19, OPS-19, OPS-20 | Shape universal, procedure engine-specific. |
| E23 | Security feature availability | PostgreSQL column grants and RLS; SQL Server RLS, DDM, Always Encrypted, TDE; Oracle VPD or RAS, TDE, Redaction. MySQL column privileges exist [WF]; row-level capability was not found in pages read. | PGMY-07, MSOM-05, MSOM-13, PGMY-19, ENG-06 | Absence on the MySQL roles page is not proof of absence (note 01). |
| E24 | NULL in UNIQUE | PostgreSQL treats NULLs as distinct by default with an option to change. MySQL permits many NULLs [WF]. SQL Server allows one NULL per column in a UNIQUE constraint [WF]. Oracle has a composite-specific rule [WF]. | PGMY-01, ENG-05, ENG-10, ENG-15 | No portable uniqueness rule can assume one behaviour (C-83). |
| E25 | Default isolation or consistency beyond OLTP engines | Snowflake READ COMMITTED only on tables. BigQuery snapshot [WF]. Redshift SNAPSHOT default. Spanner Serializable default [WF]. DynamoDB eventually consistent reads by default. Cosmos DB set per account [WF]. | ENG-19, ENG-21, ENG-22, ENG-24, ENG-25, ENG-26 | Do not assume transactional isolation carries across platforms. |
| E26 | Read-your-writes primitives | PostgreSQL remote_apply waits for replay. MySQL semisynchronous replication waits for receipt, not apply, and WAIT_FOR_EXECUTED_GTID_SET is the wait primitive [WF]. SQL Server secondaries show a change only after redo [WF]. | ENG-02, ENG-07, ENG-12 | Synchronous replication does not by itself make a write visible on replicas. |

## A3. Approaches that suit transactional systems

Scope is OLTP, including ERP, financial and SaaS systems of record.

| # | Approach | Use it when | Avoid or limit when | Class | Evidence |
|---|---|---|---|---|---|
| T1 | Normalized base tables, 3NF by default | Non-key fields are updated, the system of record owns the facts | Kent allows stopping short for performance, so document the reason | RECOMMENDED default | DES-02, CLOUD-16, MSOM-14, PERF-17 |
| T2 | Declared PK, FK, UNIQUE, NOT NULL, CHECK | Always on unsharded system-of-record tables | Cross-shard references, where only columns and audits remain | MANDATORY | MSOM-08, PGMY-01, MSOM-02, DES-18 |
| T3 | 64-bit generated keys | Default for generated keys | Provably bounded lookup tables may use 32-bit | RECOMMENDED | [Buildkite incident](https://buildkitestatus.com/incidents/63zxhjsysszc) (case), [Rails 5.1 Release Notes](https://guides.rubyonrails.org/5_1_release_notes.html), DES-22, PGMY-02 |
| T4 | Time-ordered UUID | Global or client-generated IDs on B-tree engines | Creation time leaks; range-sharded stores | RECOMMENDED where global IDs are needed | DES-04, PERF-15, DES-15, DES-16 |
| T5 | Aggregate as transaction boundary | Domain-modelled systems | Cross-aggregate invariants need asynchronous reconciliation | RECOMMENDED | ARCH-01, ARCH-02, ARCH-03 |
| T6 | Optimistic version column | Business transactions spanning several system transactions | High-contention hot rows | RECOMMENDED | DES-14, [rowversion](https://learn.microsoft.com/en-us/sql/t-sql/data-types/rowversion-transact-sql), [Optimistic Offline Lock](https://martinfowler.com/eaaCatalog/optimisticOfflineLock.html) |
| T7 | Pessimistic row locks | Read-then-write within one transaction, ordered lock acquisition | Long transactions | RECOMMENDED | PGMY-08, MSOM-06, [Explicit locking](https://www.postgresql.org/docs/current/explicit-locking.html) |
| T8 | SERIALIZABLE with retry | PostgreSQL cross-row invariants | Oracle, where the named level is snapshot isolation | OPTIONAL per engine | TXN-04, PGMY-08, TXN-10 |
| T9 | Idempotency key with stored outcome | Money-moving or retried writes | Key retention needs a reaper | RECOMMENDED | CASE-33, TXN-19 |
| T10 | Transactional outbox | Publishing events with a business change | Adds a relay; consumers still need de-duplication | RECOMMENDED | TXN-18, PIPE-05, TEN-27 |
| T11 | Saga with compensation | Multi-service workflows without a shared transaction | No isolation between steps; needs semantic locks | OPTIONAL | TXN-17, ARCH-06 |
| T12 | Append-only double-entry ledger | Financial postings | Hot balance queries need a derived, reconcilable balance | RECOMMENDED; non-alteration of books is MANDATORY in Germany (HGB 239(3), AO 146(4)), which does not prescribe append-only storage; see Part D | TEN-40, TEN-41, TEN-42, TEN-43, CASE-30, CASE-31, ERP-02, ERP-06, ERP-12, ERP-23 |
| T13 | Locked per-series counter | Legally sequential documents | High write contention on a series | RECOMMENDED as a mechanism; numbering duties are MANDATORY only per jurisdiction (B8) | TEN-39, TEN-33, LEG-01, LEG-07, LEG-14 |
| T14 | Event sourcing | Ledgers, payments, audit-heavy streams | Reference and master data; Microsoft calls it complex and selective | OPTIONAL | ARCH-09, ARCH-10, ARCH-08 |
| T15 | CQRS read model | Read patterns diverge sharply from writes | Simple CRUD; eventual consistency cost | OPTIONAL | PERF-56, ARCH-07 |
| T16 | Document embedding by access pattern | Data read together on MongoDB, DynamoDB, Cosmos DB | Unbounded arrays and bloated documents | RECOMMENDED on document stores | MSOM-15, CLOUD-06, CLOUD-20 |
| T17 | Log-based CDC for downstream propagation | Analytics and integration feeds | Needs PK or replica identity; at-least-once delivery | RECOMMENDED | PIPE-06, TEN-26, TEN-28, TEN-29 |
| T18 | Tenant-prefixed composite keys | Pooled or sharded multi-tenant OLTP | Single-tenant databases | RECOMMENDED; MANDATORY on Citus | PERF-44, CLOUD-19, TEN-07 |
| T19 | Logical shards mapped to fewer hosts | Horizontal scale on a tenant-like key | Before vertical scaling and vertical partitioning are exhausted | OPTIONAL | CASE-02, CASE-03, CASE-05 |
| T20 | Schema-per-context, shared server | Modular monolith with module boundaries | Independent deployment or differing storage needs | RECOMMENDED | ARCH-05, ARCH-01, ARCH-04 |
| T21 | Strong-consistency distributed SQL | Geo-distributed systems of record | Single-region systems without that need | OPTIONAL | TXN-20, CLOUD-11, PERF-48 |
| T22 | Period status finer than one company flag, with gated close | ERP general ledgers and subledgers | Grain differs by product; no standard sets one | RECOMMENDED | ERP-01, ERP-05, ERP-09, ERP-14, ERP-15, ERP-19 |
| T23 | Correction by new entry, with date, method and reason | Posted financial entries | Vendor exceptions delete generated vouchers (C-72) | RECOMMENDED; non-alteration is MANDATORY in Germany only | ERP-02, ERP-06, ERP-12, ERP-19, ERP-23 |
| T24 | Rates keyed by pair, date and type | Multi-currency ledgers and DW copies | Effective-dating and inverse-rate rules are not settled (C-77, C-78) | RECOMMENDED | ERP-08, ERP-20 |
| T25 | Series-based numbering per legal entity, with a record of unused numbers | Invoicing in several jurisdictions | [INFERENCE] per-entity strictest-rule design; France has continuity wording, UK tolerates explained gaps | RECOMMENDED | LEG-01, LEG-07, LEG-14 |

## A4. Approaches that suit analytical systems

OLAP, DW, lakehouse and streaming are analysed separately because the notes give them different evidence and different integrity models.

### A4.1 OLAP workloads (query shape and engine, whatever the store)

| # | Approach | Fit | Limit | Class | Evidence |
|---|---|---|---|---|---|
| A1 | Star schema as the consumption shape | BI and aggregate queries over facts and dimensions | Not a universal replacement for nested data on BigQuery | RECOMMENDED | CLOUD-08, CLOUD-16, CLOUD-21, DWM-14, LAKE-14 |
| A2 | Columnar storage with compression and projection | Scans over few columns of many rows | Point lookups and frequent updates | RECOMMENDED | PERF-38, PERF-39, PERF-02 |
| A3 | Materialized and indexed views for aggregates | Warehouse aggregation with controlled refresh | Stonebraker rejects them for OLTP; SQL Server warns of DML cost | RECOMMENDED for OLAP only | PERF-38, PERF-04, PERF-26 |
| A4 | Bitmap indexes | Low-DML warehouse joins on Oracle | Engine-specific; high-DML tables | RECOMMENDED on Oracle DW | MSOM-12, MSOM-09 |
| A5 | Partition by date, cluster by filter columns | Cloud warehouses that lack B-tree indexes | Small partitions; BigQuery prefers clustering when partitions are small | RECOMMENDED | CLOUD-13, LAKE-10, LAKE-03 |
| A6 | One Big Table derived from a star | BI tools without relationship support, small teams | Result is engine-dependent (C-84). Vendor-hosted test found flat faster on three platforms [WF]; BENCH-10 found star faster on Redshift and MariaDB Columnstore and flat faster on Singlestore. Poor for multi-grain ledgers | OPTIONAL | DWM-22, DWM-21, DWM-20, BENCH-10 |
| A7 | Nested and repeated fields | Hierarchical one-to-many on BigQuery | BigQuery itself concedes star schemas are typically optimized | OPTIONAL | CLOUD-12 |
| A8 | HTAP columnar replica | Operational analytics on live data | Write amplification and freshness caveats. BENCH-14 is the most independent result but anonymizes commercial systems; BENCH-13 is a vendor measuring its own product | OPTIONAL | PERF-02, PERF-49, CLOUD-16, BENCH-13, BENCH-14 |
| A9 | Cube | Pre-aggregated multidimensional analysis | Often needs recomputation; sourced to Azure only | OPTIONAL | CLOUD-16 |
| A10 | Asynchronous read replica for reports | Reports that do not feed back into decisions | Replicated endpoints may weaken guarantees below snapshot isolation | OPTIONAL | [Jepsen RDS PostgreSQL 17.4](https://jepsen.io/analyses/amazon-rds-for-postgresql-17.4), TXN-14 |
| A11 | Semantic layer over dimensional models | Consistent metric definitions | Evidence is vendor documentation; Airbnb Minerva detail is unverified | OPTIONAL | [Snowflake semantic views](https://docs.snowflake.com/en/user-guide/views-semantic/overview), CASE-40 (unverified) |

### A4.2 Data warehouse (integrated historical store)

| # | Approach | Fit | Limit | Class | Evidence |
|---|---|---|---|---|---|
| W1 | Declare grain first; one grain per fact table | Any dimensional model | None stated by the method owner | MANDATORY within the Kimball method | DWM-01, DWM-02 |
| W2 | Conformed dimensions on a bus matrix | Integration without a central normalized layer | Multi-source key reconciliation may justify an integration layer | MANDATORY within Kimball; a method choice overall | DWM-01, DWM-02, DWM-04 |
| W3 | Integer surrogate keys on dimensions | History tracking and unstable source keys | Date dimension is exempt; cloud-era critics dispute cost (C-11) | MANDATORY within Kimball; RECOMMENDED by Oracle | DWM-01, DES-12, DWM-14 |
| W4 | Default rows instead of NULL fact foreign keys | Fact tables | Row must be a real dimension member, not a magic literal | MANDATORY within Kimball | DWM-01, DWM-02 |
| W5 | SCD Types 0 to 7 | History on dimensions | Dynamic Tables on Snowflake cannot express SCD2 | OPTIONAL per attribute | DWM-01, TEN-24, LAKE-18, LAKE-12 |
| W6 | Inmon integrated granular foundation feeding dependent marts | Enterprise integration, master data | Slow integration work; 3NF physicalization is RECOMMENDED rather than definitional in Inmon's own recent text | RECOMMENDED where an integration layer is needed | DWM-06, DWM-04, DWM-14 |
| W7 | Data Vault 2.0 raw and business vault with information marts | Many sources, audit needs, parallel loads | Consumers should not query the vault; skills and complexity are the top reported drawbacks | OPTIONAL, method-mandated parts apply if chosen | DWM-08, DWM-09, DWM-11, DWM-13 |
| W8 | Anchor Modeling, 6NF | Highly volatile schemas with heavy historization | Thin tooling and adoption evidence; author-published | OPTIONAL | DWM-16 |
| W9 | Non-enforced foreign keys with RELY | Loads controlled by ETL | RELY is safe only if data complies | RECOMMENDED by Oracle and Snowflake | MSOM-12, LAKE-09 |
| W10 | Audit dimension and error-event schema | Traceable batch quality | The ETL Toolkit chapter itself was not accessed | RECOMMENDED | DQ-15, DWM-01 |
| W11 | Subledger-to-GL reconciliation per closed period | Financial marts | Sourced to one vendor's product documentation | RECOMMENDED for finance | DQ-16 |
| W12 | Mart as a governed publication with contract | Cross-team consumption | Agility cost argued but not measured | RECOMMENDED | DQ-03, PIPE-20 |

### A4.3 Lakehouse (open storage with table semantics)

| # | Approach | Fit | Limit | Class | Evidence |
|---|---|---|---|---|---|
| L1 | Medallion layering | Staged quality progression | Pattern, not model; Databricks itself says not a requirement | RECOMMENDED by two vendors, OPTIONAL as a standard | LAKE-01, LAKE-06, CLOUD-15, CLOUD-21 |
| L2 | Open table formats with ACID metadata | Object-store data needing warehouse semantics | Single-table ACID; Databricks multi-statement transactions on Unity Catalog managed Delta tables became generally available in July 2026 with listed limits (ENG-27) | RECOMMENDED | LAKE-07, LAKE-08, PIPE-09, ENG-27 |
| L3 | Raw landing as string, VARIANT or binary | Unknown or volatile source shape | Compliance and security risk of raw data; needs typed Silver | OPTIONAL | LAKE-01, [Snowflake VARIANT considerations](https://docs.snowflake.com/en/user-guide/semistructured-considerations), PIPE-18 |
| L4 | Put a data model inside each layer | Silver integration, Gold consumption | Model-to-layer mapping is blog-level guidance, not product docs | RECOMMENDED | LAKE-05, LAKE-06, DWM-19 |
| L5 | Schema enforcement by default, evolution opt-in | Protecting tables from drift | Evolution rules differ by format | RECOMMENDED | PIPE-11, LAKE-02, PIPE-08 |
| L6 | Mutable clustering or hidden partitioning | Layout that can change later | Format-specific | RECOMMENDED per platform | LAKE-03, PIPE-10 |
| L7 | Write-Audit-Publish | Publishing to consumers | Validation tables alone do not block downstream without orchestration wiring | RECOMMENDED | DQ-12, DQ-13, DQ-14 |
| L8 | Time travel within a bounded window | Reproducibility and short-term recovery | Not long-term backup or archive | RECOMMENDED; never as backup (U7) | LAKE-11, [Delta history](https://docs.databricks.com/aws/en/delta/history) |
| L9 | Catalog-level row filters, column masks, tags | Central governance over shared storage | Policy UDF column types must match parameters | RECOMMENDED | LAKE-04, SEC-31, SEC-32 |
| L10 | Do not use as OLTP | Delta write rates are limited to several transactions per second | Snowflake hybrid tables are the OLTP-oriented exception | MANDATORY as an engine fact for Delta only | LAKE-08, LAKE-09 |
| L11 | Accept weaker data independence | Direct access to open files | The Lakehouse paper concedes this departs from relational premises | Trade-off to record | LAKE-07, DES-01 |

### A4.4 Streaming (unbounded data and event transport)

| # | Approach | Fit | Limit | Class | Evidence |
|---|---|---|---|---|---|
| S1 | Stable entity key per event | Per-entity ordering and compaction | Ordering is per partition only | MANDATORY on Kafka for per-entity ordering | PIPE-01 |
| S2 | Explicit event time distinct from processing time | Any late-arriving stream | Broker timestamp defaults to producer-set; payload event time is an inference | RECOMMENDED | PIPE-16, PIPE-17, PIPE-01 |
| S3 | Deletes as keyed tombstones | Compacted topics and CDC | Tombstone retention is bounded | MANDATORY where compaction is used | PIPE-01, PIPE-06 |
| S4 | Registered compatibility mode | Producer and consumer independence | Default BACKWARD checks only the latest schema | RECOMMENDED | PIPE-02, PIPE-03 |
| S5 | Versioned streams for breaking change | Changes compatibility modes cannot express | Consumer migration work | RECOMMENDED | PIPE-03 |
| S6 | Standard event envelope | Cross-system events | CloudEvents text read was a work-in-progress branch | OPTIONAL | ARCH-11, ARCH-12 |
| S7 | Idempotent consumers | Any at-least-once path | Requires a stored dedupe key | MANDATORY (U15) | PIPE-01, PIPE-06, PIPE-08 |
| S8 | Exactly-once within the platform | Kafka transactions, Spark file sinks | End-to-end delivery is delegated to the sink | OPTIONAL | PIPE-01, PIPE-08 |
| S9 | Watermarks with a late-data policy | Windowed aggregates | Data later than the threshold may or may not be processed | RECOMMENDED | PIPE-08, PIPE-17 |
| S10 | Declared schema, not inference | File sources and landing tables | Spark requires it for streaming file sources; batch inference is a default | RECOMMENDED; required by Spark streaming file sources | PIPE-07, PIPE-08 |
| S11 | Dead-letter stream | Poison records | Silent unless counts are reconciled | RECOMMENDED | PIPE-03, [Kafka Connect Concepts](https://docs.confluent.io/platform/current/connect/concepts.html) |
| S12 | Log-based CDC and outbox as sources | Database-to-stream integration | Additive column changes propagate transparently; others need coordination | RECOMMENDED | PIPE-05, PIPE-06, TEN-26 |
| S13 | Kappa replay from retained log | One codebase for reprocessing | Retention must cover the window; output swap needed | OPTIONAL | PIPE-15, PIPE-01 |
| S14 | Dataflow model, engine choice under one logical model | Teams wanting latency and correctness trade-offs per pipeline | Requires tooling that implements it | OPTIONAL | PIPE-17, LIT-63, PIPE-16 |

## A5. Practices that are outdated or controversial

### A5.1 Outdated or superseded

| # | Practice | Status | Basis | Replacement or note |
|---|---|---|---|---|
| O1 | Most selective column first in composite indexes | Outdated myth | PERF-34, PERF-06, PERF-18, MSOM-17 | Equality first, usage-driven; selectivity matters only among range columns. PostgreSQL 18 skip scan further loosens prefix rules (PERF-16). |
| O2 | Adding a column with a default is always a rewrite | Version-dependent, outdated on current PostgreSQL | OPS-09, CASE-27, OPS-04 | Non-volatile defaults need no rewrite on current PostgreSQL; volatile defaults still rewrite. |
| O3 | Oracle's 2 GB partitioning heuristic | Dated | MSOM-11, PGMY-06 | PostgreSQL's rule of thumb is a table larger than server memory. |
| O4 | Pre-planned partitions and indexes in cloud DW | Superseded on Snowflake and Databricks | LAKE-03, LAKE-10, [Snowflake modeling blog](https://www.snowflake.com/en/blog/support-multiple-data-modeling-approaches-with-snowflake/) | Automatic or mutable layouts. Kimball logical rules survive. |
| O5 | Date partitioning everywhere on Databricks | Superseded | LAKE-03 | Liquid clustering is now recommended for new tables. |
| O6 | Oracle VPD for new work | Being superseded by RAS | MSOM-13 | Oracle recommends RAS for new projects (note 02). |
| O7 | Oracle traditional auditing | Desupported in 26ai per note 02 | MSOM-13, SEC-28 | Unified Auditing. |
| O8 | IDEF1X as a federal mandate | Withdrawn | GOV-27 | Notation remains usable and OPTIONAL. |
| O9 | OMG CWM | No update since 2003 | GOV-29 | Legacy tool interchange only. |
| O10 | Amazon QLDB as a ledger store | Retired, end of support 2025-07-31 | TEN-16 | Tamper-evident options are engine-specific. |
| O11 | INNOQ Data Contract Specification | Deprecated as of ODCS v3.1.0 | PIPE-20, ARCH-23 | ODCS v3.x. |
| O12 | data-diff and Amundsen as standing dependencies | Archived 2024-05-17 and 2026-09-29 | DQ-17 and note 15 | Prefer specifications over tools. |
| O13 | utf8mb3 on MySQL | Deprecated | [MySQL utf8mb3](https://dev.mysql.com/doc/refman/8.4/en/charset-unicode-utf8mb3.html) | utf8mb4 for new applications. |
| O14 | serial in PostgreSQL | Discouraged by the wiki only | PGMY-10 | Identity columns. The manual is neutral (C-23). |
| O15 | SQL Server datetime type for new work | Discouraged by vendor | MSOM-03 | datetime2 or datetimeoffset. |

### A5.2 Controversial

| # | Topic | Camps | Status |
|---|---|---|---|
| V1 | Natural versus surrogate OLTP keys | Celko, sqlstyle, Karwin's ID Required listing against Kimball, Chen's artificial attribute, ORM conventions (DES-12, DES-20, DES-13, LIT-10) | Unresolved. [INFERENCE] Surrogate PK plus UNIQUE on natural key satisfies both integrity goals. |
| V2 | Foreign keys at sharded scale | Alibaba, gh-ost, Pinterest against GitLab, PostgreSQL docs, Citus (DES-22, CASE-23, CASE-05, DES-18, PERF-44) | Context-resolved for sharding. PlanetScale reversed course (DES-17). |
| V3 | ON DELETE default | GitLab favours CASCADE in most cases; PlanetScale prefers NO ACTION; Alibaba warns of update storms (DES-18, DES-17, DES-22) | Unresolved. |
| V4 | Singular or plural table names | Alibaba forbids plurals; Rails, dbt and GitLab examples use plural; Django defaults and Prisma models are singular while Prisma calls plural tables common (DES-22, LAKE-16, DES-20, THIN-10, THIN-11, THIN-13, THIN-14) | Unresolved. Consistency only. No source reports an outcome difference. |
| V5 | ENUM type or lookup table | PostgreSQL enums cannot remove values; MySQL ENUM pitfalls; GitLab uses CHECK; Karwin lists 31 Flavors as an antipattern, remedy not read (PGMY-10, DES-18, DES-13) | Context-resolved by how static the value set is. |
| V6 | Soft delete | Leach argues against per-row flags; GitLab marks aggregates for deletion; ERP frameworks use active flags (TEN-30, TEN-31, CASE-44, CASE-50) | Partly resolved at aggregate level. |
| V7 | Kimball is dead | Beauchemin and forum positions against dbt, Databricks, Oracle (DWM-23, DWM-20, DWM-21, LAKE-06, DWM-14) | Largely resolved: logical rules survive and physical motivations weaken. |
| V8 | Hash or integer surrogate keys | dbt and Databricks DV use hashes; Snowflake advises numeric keys (LAKE-16, DWM-21, LAKE-14) | Unresolved; depends on load parallelism and engine (C-11). |
| V9 | Data Mesh adoption | Dehghani against Thoughtworks Radar caution (ARCH-14, ARCH-15, ARCH-16) | Partly resolved: core is ownership plus central platform. |
| V10 | Data Fabric as a category | Gartner and IBM definitions are analyst or vendor sourced | Unresolved. No independent primary source in the notes. |
| V11 | Lambda architecture | Kreps, Akidau argue against; Azure documents both neutrally (PIPE-15, PIPE-16, PIPE-17, CLOUD-17) | Largely resolved against dual codebases. |
| V12 | Event sourcing for general systems | Microsoft and Fowler warn of cost; ledger community favours it (ARCH-10, ARCH-08, TEN-42) | Context-resolved to selective use. |
| V13 | 2PC | Spanner in favour; microservices.io against; PostgreSQL restricts it to transaction managers (TXN-20, ARCH-06, [PREPARE TRANSACTION](https://www.postgresql.org/docs/current/sql-prepare-transaction.html)) | Context-resolved by topology. |
| V14 | CAP framing | Brewer, Abadi, Kleppmann differ (TXN-15, TXN-14, TXN-16) | Unresolved as framing. Practical guidance agrees. |
| V15 | Reversible migrations | GitLab requires down paths; Braintree and Flyway favour forward-only (OPS-04, OPS-07, OPS-10) | Resolved by compatibility as the safety mechanism. |
| V16 | State-based or migration-based authoring | Redgate says neither is ideal; Atlas and Prisma propose hybrids (OPS-14, OPS-13) | Unresolved. |
| V17 | Shift-left contracts versus warehouse testing | Confluent and Sanderson (via InfoWorld only) against warehouse-native practice (DQ-11, LAKE-19) | Resolved as layers; both sides vendor-adjacent. |
| V18 | NoSQL for scale | Undercut by documented SQL scale-out (PERF-45, PERF-44, CLOUD-11, PERF-30) | Largely resolved; scale comes from key design. |
| V19 | Subtype mapping default | Hibernate favours joined tables for constraints; EF Core defaults to one table and warns on joined-table performance (THIN-04, THIN-05) | Unresolved. Each optimises a different goal; no engine-neutral benchmark found. |
| V20 | Permanent period close | Oracle and Odoo offer it; D365 offers it and advises against it (ERP-05, ERP-18, ERP-10) | Unresolved; product choice. |

## A6. Decisions that are trade-offs

No source declares a single winner on these axes. The last column gives the deciding variables.

| # | Decision | Axis | Side A | Side B | What decides it | Sources |
|---|---|---|---|---|---|---|
| X1 | Normalize or denormalize | Update safety against read speed | Normalize (DES-02) | Denormalize (DWM-01, CLOUD-12) | Update frequency, single controlled write path | DES-02, PERF-38, DWM-22 |
| X2 | Isolation strength | Correctness against throughput | SERIALIZABLE, SSI | Read Committed with explicit locks | Invariant type, retry tolerance | TXN-04, TXN-03, PGMY-08 |
| X3 | Consistency during normal operation | Consistency against latency | Primary-only reads | Asynchronous replicas | Whether results feed decisions | TXN-14, TXN-15 |
| X4 | Key type | Locality against distribution against privacy | Sequential integer | UUIDv4 or hash | Engine topology, leak tolerance | MSOM-01, CLOUD-11, DES-04 |
| X5 | Tenancy model | Isolation against cost against agility | Silo | Pool | Compliance, restore, customization, tenant count | CLOUD-03, CLOUD-18, CLOUD-19 |
| X6 | Row-level security in the engine or the application | Assurance against complexity | Engine RLS (PGMY-07, MSOM-05) | Application filter (CLOUD-18 notes many avoid RLS) | Whether tenant identity can reach every query | CLOUD-18, PGMY-07 |
| X7 | Foreign keys | Integrity against write and online-DDL cost | Enforce | Application and audits | Sharding, tooling | DES-18, DES-17 |
| X8 | History mechanism | Fidelity against storage and write cost | System-versioned or trigger history | Audit columns only | Legal requirement, reconstruction need | TEN-17, MSOM-04, TEN-11 |
| X9 | Encryption layer | Protection against query capability | Application or client-side | TDE | Threat model, need for range queries | SEC-23, SEC-24, SEC-17 |
| X10 | Soft or hard delete | Recoverability against query and erasure burden | Hard delete with archive | Flag with purge | Erasure duties, undelete likelihood | TEN-30, TEN-31, SEC-15 |
| X11 | ETL or ELT | Governance before load against flexibility after load | ETL | ELT | Regulated fields, existing transforms | PIPE-19, PIPE-18 |
| X12 | Batch or streaming | Cost and simplicity against latency | Batch | Streaming | Freshness requirement | PIPE-16, PIPE-17 |
| X13 | Validation gate position | Blocking against availability | Blocking checks | Warn and continue | Table criticality | DQ-13, DQ-14 |
| X14 | Index count | Read latency against write cost | More indexes | Fewer indexes | Write ratio | MSOM-01, MSOM-09 |
| X15 | Partitioning | Manageability against planning cost | Partition | No partition | Table size relative to memory, retention pattern | PGMY-06, PERF-03 |
| X16 | Warehouse model | Audit and flexibility against query simplicity and skills | Data Vault | Direct Kimball | Number of sources, audit need, team skills | DWM-13, DWM-08, DWM-01 |
| X17 | Medallion hop count | Traceability against latency and cost | More layers | Fewer layers | Regulation, team size | LAKE-01, LAKE-06 |
| X18 | Contracts | Consumer safety against producer agility | FULL compatibility | BACKWARD or NONE | Upgrade coordination, retention | PIPE-02, DQ-03 |
| X19 | Migration method | Tool support against control | Generated DDL | Hand-written SQL | Rename frequency, review practice | OPS-12, OPS-04 |
| X20 | DR tier | Cost against RTO and RPO | Backup and restore | Multi-site active/active | Business impact analysis | OPS-21, OPS-17 |
| X21 | Single-table NoSQL design | Fewer requests against operability | Single table | Multiple tables | Per-tenant encryption, backups, Streams cost | CLOUD-06, CLOUD-07 |
| X22 | Build or adopt a sharding layer | Control against maturity | Figma, Notion built | Slack, GitHub adopted Vitess | Team capacity, reversibility | CASE-01, CASE-02, CASE-04, CASE-07 |
| X23 | Rate effective-dating | Completeness against gap tolerance | Exact-day rows (ERP-08) | Most recent on or before with a staleness limit (ERP-20) | Rate source frequency, whether gaps are acceptable | ERP-08, ERP-20 |
| X24 | Subtype mapping | Constraints against joins | Joined or class tables | Single table | Need for subtype NOT NULL and FKs, read shape | THIN-03, THIN-04, THIN-05 |

---

# Part B. Comparison matrices

## B1. OLTP, OLAP, data warehouse, lakehouse, streaming

Numeric scale figures come from Azure only, because no other framework publishes a comparable trait table (note 03). Cells without a citation restate the row's source column.

| Dimension | OLTP | OLAP | Data warehouse | Lakehouse | Streaming |
|---|---|---|---|---|---|
| What it is | Recording business interactions as they occur (CLOUD-16) | Analytical query workload over large data (CLOUD-16) | Integrated historical store for reporting; Inmon's subject-oriented, integrated, time-variant, non-volatile definition (DWM-06, CLOUD-17) | Open-format lake storage with warehouse semantics (LAKE-07, CLOUD-15, CLOUD-17) | Processing and transport of unbounded data (PIPE-16, PIPE-01) |
| Category | System of record | Workload and query style | Architecture and store | Storage and table architecture | Processing and delivery model |
| Primary shape | Normalized relational or aggregates on documents (CLOUD-16, MSOM-15) | Star, snowflake or cube (CLOUD-16) | Integration layer plus marts, or dimensional bus (DWM-01, DWM-04) | Layered medallion plus a model per layer (LAKE-01, LAKE-05) | Keyed events, topics, compacted tables (PIPE-01) |
| Workload | Heavy writes, moderate reads (CLOUD-16) | Heavy reads, read-only (CLOUD-16) | Batch loads, heavy reads (CLOUD-16, DWM-14) | Mixed batch, streaming, SQL, ML (LAKE-07) | Continuous append and consumption (PIPE-01) |
| Schema timing | Schema on write, enforced (CLOUD-16) | Schema on write, strongly enforced in the Azure trait table (CLOUD-16) | Schema on write at presentation; staging varies (DWM-14) | Raw may be schema-on-read; Silver and Gold enforced (LAKE-01, PIPE-11) | Registered schema per topic, checked at producer or registry (PIPE-02) |
| Integrity locus | Engine constraints (MSOM-08, PGMY-01) | Engine-dependent; often pre-validated | Loads and tests; constraints often RELY or informational (MSOM-12, LAKE-09) | NOT NULL and CHECK enforced; PK, FK, UNIQUE informational (LAKE-02, LAKE-09) | Contracts plus idempotent consumers (PIPE-02, PIPE-06) |
| Transactions | Strong, ACID (CLOUD-16) | None in Azure's OLAP trait table (CLOUD-16) | Load-window atomicity; platform-specific | Single-table ACID via log (LAKE-08, PIPE-09) | Exactly-once inside the platform, at-least-once to external systems (PIPE-01, PIPE-08) |
| Physical levers | Primary and secondary B-tree (CLOUD-16, MSOM-01) | Columnar, multidimensional indexes (PERF-39, CLOUD-16) | Bitmap, columnstore, distribution, sort or cluster keys (MSOM-12, PERF-02, CLOUD-08) | Clustering, hidden partitions, compaction (LAKE-03, PIPE-10) | Partitions by key, compaction, retention (PIPE-01) |
| Normalization posture | Highly normalized (CLOUD-16, MSOM-14) | Denormalized for query (CLOUD-16) | 3NF or vault for integration; star at presentation (DWM-14, DWM-08) | Bronze source-shaped, Silver normalized or vault, Gold star or wide (LAKE-05) | Event payload; carried state varies (ARCH-08) |
| Keys | Identity, UUIDv7, tenant-prefixed (DES-04, PERF-15, PERF-44) | Surrogate joins, numeric preferred (LAKE-14) | Integer surrogates in Kimball; hash in Data Vault (DWM-01, DWM-11) | Identity columns or hash keys (LAKE-05, LAKE-16) | Record key per entity, deterministic bytes (PIPE-01) |
| History | Audit columns, history tables, temporal features (TEN-45, MSOM-04, TEN-11) | Periodic snapshots | SCD, insert-only satellites (DWM-01, DWM-11) | Time travel, SCD2 via CDC tools (LAKE-11, LAKE-18) | Retained log, bounded by retention (PIPE-01) |
| Change handling | Migrations with expand and contract (OPS-02, OPS-05) | Rebuild or incremental | Conformed-dimension change, versioned loads (DWM-02) | Format-dependent evolution (PIPE-10, PIPE-11, PIPE-12) | Compatibility modes, versioned topics (PIPE-02, PIPE-03) |
| Quality control | Constraints first (MSOM-08) | Tests after build (LAKE-19) | Reconciliation, audit dimension (DQ-15, DQ-16) | Expectations, WAP gate (DQ-12, DQ-14) | Dead-letter handling, schema validator (PIPE-03) |
| Freshness | Immediate | Depends on refresh | Batch, per load | Batch to near real time | Near real time, with late data (PIPE-08) |
| Late or out-of-order data | Not applicable to normal commits | Reload | Late-arriving facts and dimensions (DWM-01) | Upsert, MERGE, re-run (PIPE-13) | Watermarks and triggers (PIPE-08, PIPE-17) |
| Failure and replay | Transaction retry (PGMY-08) | Re-query | Idempotent reload (PIPE-13) | Re-run by partition, restore version (PIPE-13, LAKE-11) | Offset replay (PIPE-01, PIPE-15) |
| Security model | Roles, RLS, encryption (PGMY-07, MSOM-05) | Grants and views | Roles, views, masking (LAKE-04, SEC-33) | Catalog policies and tags (LAKE-04, SEC-31, SEC-32) | Topic ACLs; not covered in depth by the notes |
| Typical scale (Azure figures only) | MBs to a few TBs (CLOUD-16) | Hundreds of GBs to multiple PBs (CLOUD-16) | Synapse floor of 250 GB as a fit guide ([Azure scenario](https://learn.microsoft.com/en-us/azure/architecture/example-scenario/data/data-warehouse)) | Not stated | Not stated |
| Poor fit | Large analytical scans (CLOUD-16) | Frequent row updates (PERF-38) | Operational transactions (PERF-38) | Delta write rates of several transactions per second (LAKE-08) | Ad hoc joins over full history without a store |
| Multi-tenancy pattern | Pool, silo, bridge (CLOUD-03, CLOUD-19) | Tenant column and clustering | Shared marts or secure views (LAKE-13) | MTT, OPT, APT patterns (LAKE-13) | Keys and topics per tenant not covered in the notes |
| [INFERENCE] Dominant risk | Silent corruption from missing constraints | Stale or mis-joined aggregates | Mis-stated grain and history | Assuming declared keys are enforced | Duplicates and compatibility drift |

## B2. Engines

### B2.1 Operational engines

Not verified means the notes do not support a statement for that cell. Oracle version labels follow what the pages served.

| Topic | PostgreSQL 18 | MySQL 8.4 InnoDB | SQL Server and Azure SQL | Oracle (23/26 pages) | MongoDB 9.0 |
|---|---|---|---|---|---|
| Table storage | Heap; all indexes secondary (PERF-07) | Clustered PK; secondary indexes carry PK (PGMY-12) | Clustered index recommended; heap generally not (MSOM-01) | Heap default; IOT for specific cases (MSOM-09) | Documents by `_id` (MSOM-15) |
| Default isolation | READ COMMITTED (PGMY-08) | REPEATABLE READ (PGMY-18) | Locking READ COMMITTED; RCSI on Azure SQL DB and Fabric SQL (MSOM-06) | READ COMMITTED (TXN-08) | Read concern local (MSOM-18) |
| Named RR behaviour | Snapshot isolation (TXN-10, TXN-12) | Weaker than SI; lost update, G-single, G2-item observed (TXN-11, TXN-10) | Locking; phantoms possible (MSOM-06) | Not offered (TXN-08) | Not applicable |
| Named SERIALIZABLE | SSI, true serializability (TXN-04, PGMY-08) | Lock-based, implicit FOR SHARE with autocommit off (TXN-11) | Key-range locks (MSOM-06) | Snapshot isolation, write skew possible (TXN-10) | Snapshot read concern plus majority write concern gives SI (MSOM-18, [Jepsen MongoDB](https://jepsen.io/analyses/mongodb-4.2.6)) |
| Retry signal | SQLSTATE 40001 (PGMY-08) | Deadlock and lock-wait errors (TXN-11) | Errors 3960 and 1205 ([deadlocks guide](https://learn.microsoft.com/en-us/sql/relational-databases/sql-server-deadlocks-guide)) | ORA-08177 and ORA-00060 (TXN-08) | Write-conflict aborts (MSOM-18) |
| FK index | Not automatic (PGMY-01) | Automatic (PGMY-14) | Not required, often useful (MSOM-02) | Recommended to avoid table locks (PERF-24) | Not applicable |
| FK deferral | Deferrable (PGMY-01) | No (PGMY-14) | No deferral syntax in the CREATE TABLE grammar read; no explicit statement (ENG-10) [WF] | Deferrable states exist (MSOM-08, ENG-15) | Not applicable |
| SET DEFAULT action | Supported (PGMY-01) | Rejected (PGMY-14) | Not verified | Not verified | Not applicable |
| CHECK | Passes on NULL (PGMY-01) | Passes on NULL; enforced since 8.0.16 (PGMY-15) | Declarative (MSOM-02) | Declarative (MSOM-08) | `$jsonSchema` validation; 9.0 constraint level (MSOM-16) |
| Unique with NULL | NULLS DISTINCT default, option to change (PGMY-01) | Multiple NULLs permitted (ENG-05) [WF] | One NULL per column in a UNIQUE constraint (ENG-10) [WF] | All-NULL rows satisfy; partly NULL rows with equal other values violate (ENG-15) [WF] | Not applicable |
| Identifier limit | 63 bytes, lower-case folding (PGMY-09) | 64 characters, table case file-system dependent (PGMY-17) | 128 characters (note 02) | 128 bytes; 30 below COMPATIBLE 12.2 (MSOM-10) | Namespace limits, not schema-level (note 02) |
| Money | numeric (PGMY-02) | DECIMAL ([Fixed-Point Types](https://dev.mysql.com/doc/refman/8.4/en/fixed-point-types.html)) | decimal, not money (MSOM-03) | NUMBER with explicit precision (MSOM-10) | Decimal128 (MSOM-18) |
| Instants | timestamptz (PGMY-03) | TIMESTAMP to UTC, ends 2038-01-19; DATETIME no conversion (PGMY-13) | datetime2 or datetimeoffset (MSOM-03) | Not detailed in the notes | BSON Date, milliseconds since epoch, stored in UTC (ENG-13) |
| JSON | jsonb with GIN (PGMY-04) | Via generated columns or multi-valued indexes (PERF-17) | Not detailed | JSON-schema constraint states (note 02) | Native (MSOM-15) |
| Partition rules | Unique keys include partition key (PGMY-06, ENG-08); can be FK target since 12, child side unconfirmed (ENG-08) | Same; no FKs on either side; 8192 cap (PGMY-16) | Aligned uniqueness (PERF-03) | Rich partitioning; global indexes for OLTP, local for DSS (MSOM-11) | Shard key (PERF-29, PERF-30) |
| Row-level security | RLS, bypass by superuser, BYPASSRLS, owner unless forced (PGMY-07) | None found in pages read; column privileges exist (ENG-06) [WF] | RLS applies to dbo, dbo can alter (MSOM-05) | VPD, RAS for new work; SYS and DBA roles not bound (MSOM-13) | Roles; security checklist (SEC-30) |
| System-time history | None native in 18 (PERF-16) | Not researched | System-versioned tables (MSOM-04) | Flashback Data Archive (MSOM-14) | Application pattern |
| Application-time history | WITHOUT OVERLAPS, PERIOD FKs in 18 (PERF-16) | Not researched | None in the notes | Temporal Validity (TEN-21) | Application pattern |
| Tamper evidence | Trigger or pgAudit; superuser can evade (TEN-11, SEC-27) | Not researched | Ledger tables (TEN-14) | Unified Auditing; traditional auditing desupported in 26ai; trail table insert-only (SEC-28, ENG-16) [WF] | Audit facility on Enterprise and Atlas M10 or larger (ENG-14) |
| Replica visibility | Asynchronous by default; remote_apply for causal reads (ENG-07) | Semisync waits for receipt, not apply; GTID wait primitive (ENG-02) [WF] | Visible only after redo, even in synchronous commit (ENG-12) [WF] | Data Guard modes; default Maximum Performance (ENG-18) [WF] | Not detailed |
| Transactional DDL | Yes (note 13) | No (note 13) | Not verified | No (note 13) | Not applicable |
| Backup core | Base backup plus WAL (PGMY-11) | Full plus binary log (PGMY-19) | Full, differential, log (OPS-19) | Physical backups required; logical insufficient alone (OPS-20) | mongodump for small deployments; Ops or Cloud Manager for PITR ([Backup Methods](https://www.mongodb.com/docs/manual/core/backups/)) |
| Hard limits worth encoding | 63-byte names | 8192 partitions; 64 row versions for INSTANT in 8.4 | Lock escalation at 5,000 locks | 128-byte identifiers at COMPATIBLE 12.2 or above | 16 MiB documents, 100 nesting levels, 64 indexes, 60 s transactions (MSOM-15, MSOM-18) |

### B2.2 Analytical platforms

| Topic | Snowflake | Databricks and Delta | BigQuery | Redshift | Synapse and Fabric |
|---|---|---|---|---|---|
| Enforced constraints | NOT NULL and CHECK; hybrid tables enforce PK, FK, UNIQUE (LAKE-09) | NOT NULL and CHECK (LAKE-02); RELY default NORELY (ENG-29) | Not verified in the notes | NOT NULL enforced; unique, PK, FK informational (ENG-23) | Not verified |
| Default isolation | READ COMMITTED only on tables (ENG-19) | Transactions on Unity Catalog managed tables GA, limits apply (ENG-27) | Snapshot (ENG-21) [WF] | SNAPSHOT default (ENG-22) | Not detailed |
| Identifier limit | 255 characters; unquoted stored uppercase (ENG-20) | Unity Catalog objects 255 characters (ENG-30) | Not detailed | Not detailed | Not detailed |
| Physical layout | Micro-partitions plus clustering keys for very large tables (LAKE-10) | Liquid clustering for new tables (LAKE-03) | Partition plus cluster (CLOUD-13) | DISTKEY and SORTKEY (CLOUD-08) | Hash distribution with clustered columnstore; Liquid Clustering on Fabric (CLOUD-21) |
| Modeling stance | Claims neutrality; performance guide leans star (LAKE-14) | Star at presentation, DV or 3NF in Silver (LAKE-05, LAKE-06) | Nested and repeated preferred where hierarchical (CLOUD-12) | Star designs with shared DISTKEY (CLOUD-08) | Star schema recommended (CLOUD-21) |
| Key guidance | Numeric keys strongly recommended (LAKE-14) | Identity surrogates; hash keys in DV blog (LAKE-05) | Not specified | Common column for fact and dimension (CLOUD-08) | Hash on a shared column ([Synapse tables overview](https://learn.microsoft.com/en-us/azure/synapse-analytics/sql-data-warehouse/sql-data-warehouse-tables-overview)) |
| History and recovery | Time Travel, Fail-safe not user-accessible (LAKE-11) | History retention defaults; not long-term backup ([Delta history](https://docs.databricks.com/aws/en/delta/history)) | Not detailed | Not detailed | Not detailed |
| Semi-structured | VARIANT (note 04) | VARIANT at Bronze (LAKE-01) | STRUCT and ARRAY (CLOUD-12) | Not detailed | Not detailed |
| Governance | Tags, row access, masking (SEC-31) | Unity Catalog filters, masks, tags (LAKE-04, SEC-32) | Policy tags (SEC-33) | Not detailed | Purview catalog (DQ-22) |
| Multi-tenant | MTT, OPT, APT (LAKE-13) | Not detailed | Not detailed | Not detailed | Not detailed |

### B2.3 Distributed and scale-out systems

| System | Unit of distribution | Key rule | Cross-partition transactions | Evidence |
|---|---|---|---|---|
| Spanner | Range | Avoid monotonic keys; UUID v4 recommended; interleave children | Yes: 2PC over Paxos | CLOUD-11, TXN-20 |
| CockroachDB | Range | Spread inserts with UUIDs | Not detailed in the notes | PERF-48 |
| Citus | Hash on distribution column | Tenant column in every PK and FK | Co-location keeps them single-node | PERF-43, PERF-44 |
| Vitess | Keyspace by Primary Vindex | Unique Primary Vindex, secondary vindexes to avoid scatter | Vitess 2PC docs not fetched | PERF-45, PERF-46 |
| TiDB | Row store plus TiFlash columnar replica | HTAP separation | Not detailed | PERF-49 |
| MongoDB sharded | Shard key | High cardinality, even frequency, non-monotonic | Supported; bounded lifetime | PERF-29, PERF-30, MSOM-18 |
| DynamoDB | Partition key | Access pattern first; avoid hot keys | Not detailed | CLOUD-06, CLOUD-07 |
| Cosmos DB | Logical partition | Hierarchical keys or synthetic keys; no low-cardinality keys | Not detailed | CLOUD-20 |
| Open table formats | Files under a metadata log | Iceberg field IDs; Delta column mapping; Hudi schema-on-read flag | Single-table ACID | PIPE-09, PIPE-10, PIPE-11, PIPE-12 |

## B3. Modeling methodologies

Low, Medium and High are relative judgments synthesised in note 06. They are not measurements.

| Dimension | Kimball star | Inmon CIF, 3NF EDW | Data Vault 2.0 | Anchor (6NF) | One Big Table | Activity Schema | Medallion (a pattern) |
|---|---|---|---|---|---|---|---|
| Layer | Consumption | Integration | Integration | Integration | Consumption | Consumption (event) | Layering between models |
| Absorbs change | Medium (DWM-01) | High (DWM-14) | High (DWM-13) | Highest (DWM-16) | Low (DWM-20) | Medium (DWM-24) | Not applicable (LAKE-06) |
| Auditability | Medium; Type 1 destroys history (DWM-01) | High (DWM-06) | Highest (DWM-11, DWM-09) | High (DWM-16) | Low (DWM-22) | Medium (DWM-24) | Bronze retains raw (LAKE-01) |
| Load complexity | Medium (DWM-02) | High (DWM-06) | Low per pattern, high in volume (DWM-13, DWM-09) | High table count (DWM-16) | Low logic, high I/O (DWM-22) | Low to medium (DWM-24) | Adds hops by design (LAKE-01) |
| Consumer query complexity | Low (DWM-14) | High (DWM-14) | High on vault, low via marts (DWM-08) | High without views and table elimination (DWM-16) | Lowest (DWM-22) | Medium, temporal self-joins (DWM-24) | Gold read-optimized (LAKE-05) |
| Historization | SCD Types 0 to 7 (DWM-01) | Time-variant granular (DWM-06) | Insert-only satellites, PIT tables (DWM-11) | Historized attributes, zero-update strategy (DWM-16) | Usually none, or full snapshots (DWM-23) | Append-only events (DWM-24) | Delegated to models (DWM-19) |
| ERP and finance fit | High for reporting (DWM-01, DWM-03) | High for integration (DWM-06, DWM-15) | High for audited multi-source integration (DWM-11); needs marts (DWM-08) | Reported in insurance (DWM-16); little tooling ([INFERENCE]) | Low for multi-grain ledgers (DWM-20) | Low; no multi-entity ledger support in the spec (DWM-24) | Neutral |
| Tooling and maturity | Highest (DWM-14, DWM-21) | High (DWM-13, DWM-15) | Growing; skills gap (DWM-13) | Low (DWM-16) | Medium (DWM-21) | Low; single-vendor origin (DWM-24) | High on Databricks; term has spread (LAKE-12) |
| Internal mandates | Grain; non-NULL fact FKs; integer surrogates; conformed dimensions (DWM-01, DWM-02) | Integrated, granular, non-volatile; sole source for marts (DWM-06) | Hub, Link, Satellite definitions; repeatable loads; audit metadata; consumers via marts (DWM-08, DWM-09) | Extensions only; insert-only (DWM-16) | None | Immutable activities, required columns (DWM-24) | None; not a requirement (LAKE-01) |
| Recommended parts | Atomic grain, flatten hierarchies, Unknown rows (DWM-01) | 3NF physicalization, MDM (DWM-06, DWM-14) | Hash keys, insert-only, PIT and bridge (DWM-11, LAKE-05) | Historize when versioning matters (DWM-16) | Derive from a star (DWM-22, DWM-21) | Verb-noun naming (DWM-24) | Bronze raw, Silver validated, Gold served (LAKE-01) |
| Reported weakness | Physical assumptions dated on cloud platforms (LAKE-14) | Slow integration (DWM-06) | Skills 48%, complexity 35%, query performance 32% in BARC 2023 survey (DWM-13) | Thin adoption evidence (DWM-16) | Update amplification; storage and speed results are engine-dependent (DWM-22, BENCH-10) | Single entity only (DWM-24) | Vendor-originated; orthogonal to shape (LAKE-01) |
| Evidence type | Method owner, multi-vendor adoption | Method owner, vendor practice | Method owner, survey; BENCH-11 and BENCH-12 give no usable comparison | Author-published paper | Vendor test, one conference benchmark (BENCH-10), practitioner | Specification | Single-vendor origin, wider adoption |

[INFERENCE] Routing supported by note 06: few sources and stable processes go directly to Kimball; many sources or strong audit needs justify an integration layer (Data Vault or 3NF) with Kimball marts on top; medallion is the hop convention in either case. No source benchmarks the methods like for like (B9).

## B4. Tenancy models

AWS and Azure terms are mapped in note 03. Note 22 found no silo, pool or bridge text at the CLOUD-04 landing page, so CLOUD-04 is not cited and the SaaS Lens subpage is used (CLOUD-03).

| Attribute | Silo: standalone or DB per tenant | Schema per tenant | Table per tenant | Bridge or hybrid | Pool: shared table with tenant column | Pool, sharded | Metadata-driven shared tables |
|---|---|---|---|---|---|---|---|
| Isolation | Highest (CLOUD-19) | Not assessed by any source | Not assessed | Per service or tier (CLOUD-03) | Lower; relies on predicates (CLOUD-19) | Lower across shards; per shard placement | Org-level logical (TEN-07) |
| Cost per tenant | High standalone; low with elastic pools (CLOUD-19) | Not assessed | Not assessed | Mixed | Lowest for small tenants (CLOUD-19) | Lowest | Lowest (TEN-07) |
| Noisy neighbour | Avoided (CLOUD-03) | Shared engine; [INFERENCE] | Shared engine; [INFERENCE] | Isolate only heavy tenants (CLOUD-03) | Increased risk (CLOUD-18) | Mitigated by placement | Mitigated by tenant-aware optimization (TEN-07) |
| Per-tenant restore | One DB, no impact on others (CLOUD-19) | Not assessed | Not assessed | Depends on placement | Restore to side copy, selective recovery (CLOUD-18) | Same | Not stated |
| Schema customization | Straightforward (CLOUD-19) | Possible, version tracking burden [INFERENCE] | Discouraged | Siloed tenants only | Difficult (CLOUD-19) | Difficult | By design through metadata (TEN-07) |
| Tenant scale | Medium to high with pools (CLOUD-19) | Not assessed | Not assessed | Varies | Very high (CLOUD-19) | Very high | Very high |
| Key implication | Tenant catalog, per-DB versioning (CLOUD-19) | Per-schema versioning | Metadata Tribbles concern (DES-13) | Tenant ID in all DBs so tenants can move (CLOUD-19) | NOT NULL tenant column on tenant tables (CLOUD-18, CLOUD-19) | Tenant column in PK and FKs (PERF-44) | OrgID on rows, pivot tables (TEN-07) |
| Source position | Valid; regulatory and key-ownership triggers | No source recommends it (note 14) | Azure antipattern (CLOUD-18) | Valid | Valid and common | Valid; Citus, case studies (PERF-44, CASE-01, CASE-07) | Single-vendor architecture |
| Typical trigger | Own keys, backup policy, residency (CLOUD-18, CLOUD-19) | None documented | None | Tiered plans (CLOUD-19) | Many small tenants (CLOUD-19) | Tenant-like key with growth (CASE-02, CASE-08) | Tenant-level customization at scale (TEN-07) |
| Analytical equivalent | APT, account per tenant, tens to low hundreds (LAKE-13) | OPT (LAKE-13) | OPT variant (LAKE-13) | MTT storage with dedicated compute (LAKE-13) | MTT with tenant clustering (LAKE-13) | Not covered | Not covered |

Multi-company inside a tenant is a separate axis ([INFERENCE] from note 14).

| Aspect | Dynamics 365 | NetSuite | Odoo | Evidence and status |
|---|---|---|---|---|
| Company concept | Legal entity plus operating units; `DataAreaId` as security and posting boundary | Subsidiary tree with elimination subsidiaries | Company with branches | TEN-08, TEN-09, TEN-10 |
| Posting boundary | Legal entity | Single subsidiary per transaction, generally | Company | TEN-08, TEN-09, TEN-10 |
| Shared master data | Cannot be overridden per organization | Not covered | Can be restricted by Company field | TEN-08, TEN-10; conflict C-18 |
| Consolidation | Organizational hierarchies | Tree to root, elimination entities | Parent company | TEN-08, TEN-09, TEN-10 |
| Remaining gaps | SAP company-code definition unread (training pages only); fiscal calendars, rates and close are in B7 | | | Note 18 gaps |

## B5. Architecture paradigms

| Paradigm | Decides | Schema implication | Consistency stance | Best fit | Main risk | Evidence and status |
|---|---|---|---|---|---|---|
| DDD bounded context and aggregate | Ownership and transaction scope | Contexts appear as schemas; aggregates as transaction units; references by identity ([INFERENCE] mapping) | Strong in aggregate, asynchronous across | Complex domains, ERP modules | Over-fragmentation | ARCH-01, ARCH-02, ARCH-03; well established |
| Modular monolith, shared database | Deployment | Schema per module, governed Shared Kernel (ARCH-01, ARCH-05) | Local ACID | ERP needing cross-module SQL | Ownership erosion | ARCH-05; [INFERENCE] on thresholds, no numeric split criteria exist |
| Microservices, database per service | Team autonomy | Private tables, schema or server (ARCH-05, ARCH-04) | Sagas and eventual | Independent scaling needs | Lost joins and cross-service ACID | ARCH-04, ARCH-05, ARCH-06 |
| Event notification | Coupling | Thin events | Eventual | Decoupled reactions | Hidden flows | ARCH-08 |
| Event-carried state | Data locality | Larger payloads, schema contracts | Eventual | Read autonomy | Stale copies | ARCH-08 |
| Event sourcing | System of record shape | Append-only streams, snapshots, PII kept out or shredded ([INFERENCE] on shredding) | Optimistic per stream | Ledgers, audit-heavy domains | Upcasting, complexity | ARCH-08, ARCH-09, ARCH-10, ARCH-13 |
| CQRS | Read and write separation | Read model schemas | Eventual to read model | Divergent reads | Complexity for simple CRUD | PERF-56, ARCH-07 |
| Data Mesh | Analytical ownership | Output ports with contracts; global identifiers | By product | Multi-domain enterprises | High integration cost; stalled at Trial on Thoughtworks Radar | ARCH-14, ARCH-15, ARCH-16, ARCH-17, ARCH-18, ARCH-19 |
| Data Fabric | Metadata automation | Rich machine-readable metadata | Not applicable | Heterogeneous estates | Vendor-defined concept; no independent primary source | ARCH-21, ARCH-22; Gartner definitions are third-party only |
| Lakehouse or modern data architecture | Storage and serving | Open tables with catalog | Table-level | Mixed BI and ML | Weaker enforcement | LAKE-07, CLOUD-02, CLOUD-05, CLOUD-15 |
| Data contracts | Interface between producer and consumer | Schema, quality, SLA, ownership | Per contract | Cross-team datasets | Agility cost unmeasured | PIPE-20, ARCH-23, DQ-03, PIPE-03 |
| Polyglot persistence | Store per workload | Multiple models to govern | Per store | Divergent access patterns | Premature fragmentation (CLOUD-17) | CLOUD-01, CLOUD-17 |
| HTAP | Combined serving | Row store plus columnar replica | Replica freshness | Operational reporting | Freshness and write cost | PERF-02, PERF-49, CLOUD-16 |

[INFERENCE] Mesh decides ownership and fabric automates metadata. Every source that compares them calls them complementary, though all fabric definitions reachable were analyst or vendor sourced (note 07).

## B6. ETL versus ELT; batch versus streaming

### B6.1 ETL and ELT

| Dimension | ETL | ELT | Sources |
|---|---|---|---|
| Sequence | Transform before load | Load raw, transform in warehouse | PIPE-19, PIPE-18 |
| Vendor default | Used for existing transformations or to limit warehouse resource use | Google recommends ELT for most customers; dbt advocates it | PIPE-19, PIPE-18 |
| Raw data | Not retained by default | Retained, enabling re-derivation | PIPE-18 |
| Compliance surface | Sensitive fields can be transformed before landing | dbt concedes security and compliance risk from raw landing | PIPE-18 |
| Compute locus | External engine | Warehouse | PIPE-19, PIPE-18 |
| Cost | External infrastructure | Storage and warehouse compute | PIPE-18, PIPE-19 |
| Engineering practice | Tool-dependent | Analytics code under version control, tests, CI | PIPE-18, LAKE-15 |
| Contract coverage | Not addressed by either vendor source | Not addressed; gap filled by ODCS and the Confluent Data Contract pattern | PIPE-20, PIPE-03 |
| Fit: DW | Regulated or legacy transforms | Modern cloud DW | PIPE-19, DWM-14 |
| Fit: lakehouse | Rare per the notes | Bronze landing then transform | LAKE-01 |
| Fit: OLTP as source | CDC or batch extract | CDC or batch extract | PIPE-06, TEN-26 |
| [INFERENCE] Hybrid | Field-level protection before load, then ELT, reconciles compliance with re-derivation | Same | No source states this hybrid |

### B6.2 Batch, micro-batch and streaming

| Dimension | Batch | Micro-batch | Streaming | Sources |
|---|---|---|---|---|
| Data model | Bounded | Bounded slices of unbounded | Unbounded | PIPE-16, PIPE-17 |
| Time semantics | Data interval | Trigger interval | Event time with watermarks | PIPE-13, PIPE-08, PIPE-17 |
| Delivery guarantee | Re-run by interval | Checkpointed; sink-dependent | At-least-once or platform exactly-once | PIPE-13, PIPE-08, PIPE-01 |
| Sink requirement | Upsert or partition overwrite | Idempotent by batch ID | Idempotent or transactional | PIPE-13, PIPE-08 |
| Completeness | Assumed at interval close | Assumed per trigger | Never fully knowable per the Dataflow paper | PIPE-17 |
| Schema evolution | Migration in window | Checkpoint compatibility | Registry compatibility | PIPE-08, PIPE-02 |
| Operational cost | Lowest | Moderate | Highest: not quantified in the notes | [INFERENCE] |
| Choose when | Daily or hourly freshness is enough | Minutes are enough | Seconds matter or events drive actions | [INFERENCE] |

### B6.3 Lambda, Kappa and Dataflow

| Dimension | Lambda | Kappa | Dataflow model | Sources |
|---|---|---|---|---|
| Structure | Batch layer plus speed layer | Single streaming path with log replay | One model; engine selectable per pipeline | CLOUD-17, PIPE-15, PIPE-17 |
| Codebases | Two | One | One | PIPE-15 |
| Reprocessing | Batch layer | Second job from retained log, then swap output | Windowing and triggers | PIPE-15, PIPE-17 |
| Trust risk | Users stopped trusting weakly consistent results in Google's experience | Depends on retention | Refinement modes make corrections explicit | PIPE-17 |
| Schema implication | Two output tables for the same metric | Versioned output tables and views ([INFERENCE]) | Sink handling for accumulating or retracting results ([INFERENCE]) | PIPE-15, PIPE-17 |
| Limit | Maintenance burden | Default 7-day retention on Kafka bounds replay unless raised | Needs a capable runner | PIPE-15, PIPE-01 |

## B7. ERP financial controls

Vendor product behaviour, not requirements. Most vendor pages were read through a summarising fetch tool. SAP rests on training pages. Oracle Fusion and NetSuite have one owner.

| Topic | SAP S/4HANA | Oracle Fusion | Dynamics 365 Finance | NetSuite | Odoo | ERPNext |
|---|---|---|---|---|---|---|
| Period status grain | Variant on company code, account type and interval (ERP-01) | Application, ledger, period (ERP-05) | Module and user group in a ledger calendar (ERP-09) | Subledger locks per subsidiary; close per book (ERP-14, ERP-15) | Lock dates per company (ERP-18) | Date range, company, document type (ERP-19) |
| Adjustment periods | Up to four special periods, 13 to 16 (ERP-01) | Adjusting periods sharing period-end date (ERP-05, ERP-06) | Closing periods copying open-period dates (ERP-09, ERP-10) | No statement found | None in pages read | None in pages read |
| Close and reopen | Not established | GL close blocked by pending intercompany (ERP-06) | Reopen on-hold periods; close rerun (ERP-10, ERP-12) | Ordered close; reopen cascades and stores justification (ERP-14, ERP-15) | Lock dates; Hard Lock (ERP-18) | Closing voucher does not protect history (ERP-19) |
| Permanent close | Not established | Permanently Closed offered (ERP-05) | Offered, advised against (ERP-10) | Not established | Hard Lock cannot be overridden (ERP-18) | Not established |
| Rate roles and key | Rate types M, B, G, P (ERP-03) | From, to, date, type (ERP-08) | Per-account rate types (ERP-11) | Current, average, historical per period and pair (ERP-16) | Not established | Latest eligible record by date (ERP-20) |
| Inverse rate | Direct and indirect quotation (ERP-03) | Generally a reciprocal row (ERP-08) [WF] | Not established | Not established | Not established | Not automatically equal; separate record (ERP-20) |
| After posting | Reversal; document cannot be modified (ERP-02) | Reverse or correct by new journal (ERP-06) | Reversal subject to status and settlement (ERP-12) | Edits blocked in closed periods; void or delete (ERP-15) | Secured entries cannot be edited (ERP-18) | No edit of submitted posting (ERP-19) |
| Reversal of a reversal | Not established | Not allowed (ERP-06) | Allowed (ERP-12) | Not established | Not established | Not established |
| Year-end deletion | Not established | Not established | Reverse year-end deletes vouchers with a history record (ERP-10, ERP-12) | Delete keeps only record of deletion (ERP-15) | Not established | Not established |
| Hash chain | Not established | Not established | Not established | Not established | SHA-256 chain over named fields (ERP-18) | Immutable ledger page not read |

## B8. Invoice numbering by jurisdiction

Each row binds only its jurisdiction and stated population. Gap treatment is not derivable from the VAT Directive.

| Jurisdiction | Requirement | Gaps | Evidence quality | Sources |
|---|---|---|---|---|
| EU Directive | Sequential, series-based, unique | Not addressed | Direct text | LEG-01 |
| Germany | Issued once, one or more series | Reported not mandatory, from search snippets only; not relied on | Requirement direct; gap position unverified | LEG-04, LEG-06 (unverified) |
| France | Chronological and continuous per series | No tolerance found; no treatment of spoiled numbers found | Direct text | LEG-07, LEG-08 |
| Italy | Progressive and uniquely identifying | Not addressed | Direct text | LEG-10 |
| Spain | Sequential per series; separate corrective series | Not addressed; chained billing records are a different rule | Regulation read through summary [WF] | LEG-11, LEG-12 |
| United Kingdom | Sequential, unique, one or more series | Tolerated if the spoiled invoice is kept or the break explained; HMRC's view, not legislation | Direct text | LEG-13, LEG-14 |
| Pakistan | Serial number; FBR number and QR on integrated invoices | Not found | Direct text; start dates conflict | LEG-18, LEG-19 |
| UAE | Sequential, or unique number showing order | Not found | Direct text; amendment citation conflicts | LEG-22, LEG-24 |
| Saudi Arabia | Sequential, unique; counter never reused; hash chain | Rejected documents consume a counter value | Direct text, guideline dated November 2022 | LEG-25, LEG-26, LEG-27 |

## B9. Benchmark evidence status

No result here was reproduced by this research. Practitioner and vendor tests are not independent. Where the third column says none, the framework position is a judgment and not a measured finding.

| Topic | What exists | Independent evidence | Status for the framework |
|---|---|---|---|
| UUIDv7, v4, bigint on PostgreSQL | BENCH-01 raw-confirmed blog test; BENCH-02 and BENCH-03 [WF] | None found | Judgment. Direction agrees across tests, magnitude does not |
| UUIDv7 on MySQL | None. Ordered UUID and UUIDv1 proxies in BENCH-04 to BENCH-06 [WF] | None found | Judgment |
| RLS overhead | BENCH-07, one small practitioner test; no version, hardware or scripts | None found | Judgment. Join-based policies have no measurement |
| One Big Table against star | BENCH-10 conference paper, raw-confirmed; DWM-22 vendor-hosted test [WF] | One result, not reproduced | Engine-dependent; no general rule (C-84) |
| Data Vault against star | BENCH-11 laptop-scale thesis; BENCH-12 low-confidence paper | Effectively none | Judgment (C-86) |
| Foreign key overhead at scale | BENCH-08 small practitioner test [WF] | None found; no MySQL measurement | Judgment |
| HTAP isolation | BENCH-14 PVLDB paper, anonymized systems, partly vendor funded; BENCH-13 vendor paper; BENCH-15 no numbers | Partial | Architecture-level claims only, not named products |

---

# Part C. Register of conflicting recommendations

Status values are: Resolved (context, the sources' scope settles it), Resolved (version), Resolved (layering), Partly resolved, or Unresolved. Resolution text is this author's reading of the cited sources and is [INFERENCE] unless a source states it directly.

| ID | Topic | Source A | Source B | Context that resolves it, or unresolved | Status |
|---|---|---|---|---|---|
| C-01 | Normalize or co-locate | Oracle: OLTP uses fully normalized schemas (MSOM-14); Azure OLTP traits (CLOUD-16) | MongoDB: data accessed together is stored together, duplication is acceptable (MSOM-15) | Data-model paradigm. Embedding is a bounded default on document stores; normalization is the relational default. | Resolved (context) |
| C-02 | Normal forms against flattened dimensions | Kent and Codd: normalize base tables (DES-02, DES-01) | Kimball: surrogate-keyed flattened dimensions (DWM-01) | Scope: system of record against presentation layer fed by a controlled load. | Resolved (context) |
| C-03 | Enforce constraints in warehouses | Oracle Concepts: use constraints whenever possible (MSOM-08) | Oracle DW Guide: define FKs as non-enforced where possible (MSOM-12) | OLTP against ETL-controlled DW; RELY only if data truly complies (LAKE-09). | Resolved (context) |
| C-04 | Declared keys in cloud warehouses | Kimball and 3NF assume enforceable keys (DWM-01, DES-01) | Snowflake and Databricks: PK, FK, UNIQUE informational (LAKE-09, LAKE-02); dbt: most platforms enforce only not_null (DQ-03) | Split declared and enforced integrity; substitute tests where unenforced. | Resolved (context) |
| C-05 | Star or nested schema | Fabric, Synapse, Redshift centre on star (CLOUD-21, CLOUD-08) | BigQuery: nested and repeated fields (CLOUD-12) | BigQuery-native alternative for hierarchical one-to-many. BigQuery concedes stars are typically optimized. | Resolved (context) |
| C-06 | Single-table NoSQL | DynamoDB: as few tables as possible (CLOUD-06) | DynamoDB foundations list reasons for multiple tables (CLOUD-07); Cosmos DB discriminators (CLOUD-20) | Operability needs decide. Treat as contextual. | Resolved (context) |
| C-07 | Medallion as required architecture | Fabric: recommended design approach (CLOUD-21) | Databricks: recommended but not a requirement (LAKE-01, LAKE-06) | A pattern, orthogonal to the model. | Resolved (context) |
| C-08 | Foreign keys in the database | PostgreSQL, SQL Server, GitLab: declare them (PGMY-01, MSOM-02, DES-18) | Alibaba prohibits them; gh-ost cannot use them; PlanetScale operated without them before implementing support (DES-22, CASE-23, DES-17) | Sharding and shadow-table DDL are infrastructure limits. Keep FK columns, indexes and orphan audits where unavailable. | Resolved (context) |
| C-09 | ON DELETE default | GitLab: CASCADE in nearly all cases (DES-18) | PlanetScale prefers NO ACTION; Alibaba warns of update storms (DES-17, DES-22) | No source settles it. [INFERENCE] CASCADE for strict composition, RESTRICT elsewhere. | Unresolved |
| C-10 | Indexing foreign keys | Oracle: FKs should be indexed, avoids table locks (PERF-24) | SQL Server: not required, often useful (MSOM-02); InnoDB automatic (PGMY-14); EF Core creates it by convention (THIN-12); GitLab requires it on PostgreSQL (THIN-14) | Engine locking behaviour. | Resolved (context) |
| C-11 | Surrogate key data type | Kimball: integer surrogates (DWM-01); Snowflake: numeric keys strongly recommended (LAKE-14) | dbt style: keys should be strings; dbt Kimball tutorial and Databricks DV: hash keys (LAKE-16, DWM-21, LAKE-05) | Parallel, idempotent loads favour hashes; join and clustering performance favours integers. No benchmark in the notes. | Unresolved |
| C-12 | Natural or surrogate OLTP key | Celko, sqlstyle, Karwin's ID Required listing (LIT-10, DES-20, DES-13) | Chen's artificial attribute, ORM defaults, Kimball for DW (DES-03, DES-12) | Celko's text was not read. [INFERENCE] Surrogate plus UNIQUE natural key. | Unresolved |
| C-13 | Sequential or random keys | SQL Server, InnoDB, Flickr, Twitter Snowflake: ordered keys (MSOM-01, PGMY-12, CASE-17, CASE-18) | Spanner, CockroachDB, Square on Spanner, Figma hashing: spread keys (CLOUD-11, PERF-48, TEN-42, CASE-01) | Engine topology. | Resolved (context) |
| C-14 | Who can bypass row-level security | SQL Server: policies apply to dbo, who can alter them (MSOM-05) | Oracle VPD does not bind SYS or default DBA roles (MSOM-13); PostgreSQL superuser and owner bypass (PGMY-07) | Engine-specific; requirements must list the bypass set. | Resolved (context) |
| C-15 | RLS as the tenant isolation mechanism | PostgreSQL and Azure SQL present RLS as the mechanism (PGMY-07, CLOUD-19) | Azure Architecture Center: many multitenant solutions avoid it (CLOUD-18) | Both need tenant identity on every request. Engine or application enforcement remains a choice. | Partly resolved |
| C-16 | Where the tenant column sits in keys | Citus: every PK and FK (PERF-44) | Microsoft: leading PK element for sharded tables (CLOUD-19); Salesforce: partition key on generic tables (TEN-07) | Implementation-specific. | Resolved (context) |
| C-17 | Per-tenant tables in a shared database | Azure: antipattern (CLOUD-18) | Live SaaS Lens defines bridge per service (CLOUD-03). Note 22 found no silo, pool or bridge text at the CLOUD-04 landing page, so CLOUD-04 is no longer cited | Current texts agree. | Resolved (context) |
| C-18 | Shared master data scope | Dynamics: cannot override per organization (TEN-08) | Odoo: can restrict by Company field (TEN-10) | Product decision; both default to shared. | Partly resolved |
| C-19 | Materialized views in OLTP | Stonebraker: not in OLTP worlds (PERF-38) | SQL Server: indexed views exist, DML cost warned (PERF-04) | Treat as OLAP tool with a DML cost gate for OLTP. | Resolved (context) |
| C-20 | Partitioning for performance | SQL Server: rarely improves OLTP performance (PERF-03) | Oracle: consider tables over 2 GB, pruning can be dramatic (MSOM-11) | Manageability first. Oracle's context is DW and its threshold is dated. | Resolved (context) |
| C-21 | String column sizing | PostgreSQL: no performance difference; wiki against arbitrary limits (PGMY-10) | MySQL: smallest data types, prefix indexes (PERF-17) | Storage engine internals. | Resolved (context) |
| C-22 | Identifier length ceiling | sqlstyle: 30 bytes (DES-20) | PostgreSQL 63, MySQL 64, SQL Server 128, Oracle 128 (PGMY-09, PGMY-17, MSOM-10) | 30 is needed only for Oracle below COMPATIBLE 12.2. | Resolved (version) |
| C-23 | Identity or serial | PostgreSQL manual: neutral ([Identity columns](https://www.postgresql.org/docs/current/ddl-identity-columns.html)) | Wiki: do not use serial (PGMY-10) | Strength difference. Attribute preference to the wiki. | Resolved (context) |
| C-24 | timestamp without time zone | Manual: recommends types with date and time (PGMY-03) | Wiki: do not use it (PGMY-10) | Strength difference. | Resolved (context) |
| C-25 | Column name length and qualifiers | MySQL: short, unprefixed, under 18 characters for portability (PERF-17) | dbt and sqlstyle: `<object>_id`, descriptive names (LAKE-16, DES-20) | Oracle publishes general guidelines on descriptive names (THIN-15), so the earlier claim that no vendor gives naming guidance is corrected. Length and qualifier remain unresolved. | Unresolved |
| C-26 | Singular or plural table names | Alibaba: no plurals (DES-22); dbt Kimball blog examples singular (DWM-21); Django defaults and Prisma models singular (THIN-11, THIN-13) | Rails, dbt style, GitLab examples plural (LAKE-16, DES-18, THIN-10, THIN-14); Prisma calls plural tables common (THIN-13) | Consistency only. No source reports an outcome difference, and the 11179-5 singular example is informative for data elements and not table names. | Unresolved |
| C-27 | Money as float in pipelines | Exact decimal (PGMY-02, MSOM-03, DES-22) | A dbt style-guide example casts an amount to float (LAKE-16) | The example conflicts with the exact-decimal rule and should not be copied. | Resolved (context) |
| C-28 | Most selective index column first | Folk rule | Winand and vendors' prefix mechanics (PERF-34, PERF-06, PERF-18, MSOM-17) | Equality first. | Resolved (context) |
| C-29 | Clustering key cardinality order | Snowflake: lowest cardinality first for clustering keys (LAKE-10) | B-tree equality-first guidance (PERF-34) | Different structures; do not transfer. | Resolved (context) |
| C-30 | Oracle SERIALIZABLE | Oracle: no dirty, fuzzy or phantom reads (TXN-08) | Hermitage: snapshot isolation; Berenson: SI is non-serializable (TXN-10, TXN-03) | Treat as snapshot isolation. | Resolved (context) |
| C-31 | MySQL REPEATABLE READ | MySQL: consistent reads use the first-read snapshot (PGMY-18) | Jepsen found lost update, G-single, G2-item and calls the docs misleading; disputes Hermitage's label (TXN-11, TXN-10) | Snapshot applies to SELECT, not necessarily DML. Do not rely on it for read-then-write rules. | Resolved (context) |
| C-32 | Meaning of temporal table | SQL Server, MariaDB: system-versioned (MSOM-04, TEN-20) | SQL:2011 and Oracle: valid time is also primary (GOV-06, TEN-21) | Name both dimensions. | Resolved (context) |
| C-33 | Inclusive or half-open upper bound | Closed-open storage in SQL:2011, Snodgrass, SQL Server (GOV-06, TEN-23, MSOM-04) | BETWEEN ... AND is inclusive; Kimball SCD2 does not specify (DWM-01) | Syntax trap, not a storage conflict. | Resolved (context) |
| C-34 | Backdated changes | SQL:2011 FOR PORTION OF splits rows (GOV-06) | Workday out-of-order semantics let a later-effective edit overwrite (TEN-25) | A framework must choose. | Unresolved |
| C-35 | Mutability of history | SQL:2011, SQL Server forbid edits (GOV-06, MSOM-04) | MariaDB DELETE HISTORY, Oracle RETENTION purge (TEN-20, TEN-21) | Tamper-resistant yet retention-bounded by design. | Resolved (context) |
| C-36 | Superuser tamper resistance | pgAudit, trigger audit, SQL Server Audit concede sysadmin evasion (SEC-27, TEN-11, SEC-26) | SQL Server ledger claims protection from privileged users, detection on verification (TEN-14) | No engine prevents DBA tampering; evidence needs digests held off-database. | Resolved (context) |
| C-37 | Transactional or best-effort audit | Triggers and Envers commit with the change (TEN-11, TEN-15) | pgAudit best-effort, engine logs capture reads and DDL (SEC-27, SEC-26) | Layer them; each catches different events. | Resolved (layering) |
| C-38 | Soft delete | Leach: probably not worth it (TEN-30) | GitLab marks aggregates for deletion (TEN-31); ERP frameworks use active flags (CASE-44, CASE-50) | Aggregate root, bounded grace period. | Partly resolved |
| C-39 | Immutable logs or right to erasure | GDPR Art. 17 erasure (SEC-15, TEN-34) | PCI 10.5.1 retention, 21 CFR 11.10(e), SOX 18 USC 1520 for audit workpapers (SEC-17, TEN-17, TEN-36) | Art. 17(3)(b) covers Union or Member State legal obligations, and non-EU retention law is not clearly covered (LEG-03). No regulator text found accepts key destruction as erasure (LEG-34). See C-81 for backups. | Partly resolved |
| C-40 | Where the balance lives | Fowler, Modern Treasury: derived from entries (TEN-40, TEN-41) | Square materialises it on the books row (TEN-42) | A versioned cache is acceptable if entries stay the truth. | Resolved (context) |
| C-41 | Sequential or gapless numbers | EU VAT: sequential and uniquely identifying (TEN-39) | PostgreSQL: sequences cannot give gapless values (TEN-33) | Across countries see C-79. A plain sequence can skip values on rollback, so it cannot meet continuity wording alone; how each country treats gaps is mostly unsettled. | Unresolved |
| C-42 | Must migrations be reversible | GitLab: reversible with exceptions (OPS-04) | Braintree: rollback must not revert schema (OPS-07); Flyway favours roll-forward (OPS-10) | Expand and contract is the safety mechanism; down paths are an emergency tool. | Resolved (context) |
| C-43 | State-based or migration-based | Redgate: neither ideal (OPS-14) | Atlas and Prisma: hybrid with checked-in planned migrations (OPS-13, [Prisma mental model](https://www.prisma.io/docs/orm/prisma-migrate/understanding-prisma-migrate/mental-model)) | Hybrid trend, no settled winner. | Unresolved |
| C-44 | Generated or hand-written DDL | Alembic: autogenerate is not intended to be perfect, renames undetectable (OPS-12) | GitLab prefers plain SQL in data migrations (OPS-04) | Generated output is a candidate needing review. | Resolved (context) |
| C-45 | Data changes in migrations | Rails discourages ([Rails guide](https://guides.rubyonrails.org/active_record_migrations.html)) | GitLab allows batched background migrations; Django RunPython (OPS-04, [Django](https://docs.djangoproject.com/en/5.2/topics/migrations/)) | Keep data work out of DDL transactions and batch it. | Partly resolved |
| C-46 | Triggers or binlog for online change | pt-osc uses triggers ([pt-osc](https://docs.percona.com/percona-toolkit/pt-online-schema-change.html)) | gh-ost: triggers are the source of limitations (CASE-23) | Tool and engine; PlanetScale uses a platform ghost table (CASE-25). | Partly resolved |
| C-47 | Lock and duration budgets | Braintree about 2 s lock (OPS-07) | strong_migrations 10 s lock_timeout; GitLab 15 s statement timeout (OPS-08, OPS-04) | Different quantities: lock hold and total runtime. | Resolved (context) |
| C-48 | Adding a column with a default | Braintree 2014: unsafe (CASE-27) | Current PostgreSQL: non-volatile default needs no rewrite (OPS-09); GitLab allows it (OPS-04) | Engine version. | Resolved (version) |
| C-49 | Logical or physical backups | Oracle: logical not sufficient alone (OPS-20) | pg_dump is the cross-version method (PGMY-11 and [PG dump](https://www.postgresql.org/docs/current/backup-dump.html)); MySQL lists both (PGMY-19) | Complementary. | Resolved (layering) |
| C-50 | Replication and snapshots as backup | AWS: replication may not protect against corruption or malicious attack (OPS-21) | Data Guard protects against corruption, yet backups are offloaded, not replaced ([Data Guard](https://docs.oracle.com/en/database/oracle/oracle-database/19/sbydb/introduction-to-oracle-data-guard-concepts.html)) | Replicas reduce some risks; PITR backups remain. | Resolved (context) |
| C-51 | Immutable backup copies | Veeam promotes 3-2-1-1-0 ([Veeam](https://www.veeam.com/blog/321-backup-rule.html)) | CISA endorses immutability with caution (OPS-22) | Vendor against government caution; cost and misconfiguration matter. | Partly resolved |
| C-52 | ETL or ELT default | Google and dbt: ELT (PIPE-19, PIPE-18) | Same sources keep ETL for regulated or existing transforms | Governance need and existing estate. Neither mentions contracts. | Partly resolved |
| C-53 | Raw landing or schema enforcement | Bronze as string or VARIANT (LAKE-01, [VARIANT](https://docs.snowflake.com/en/user-guide/semistructured-considerations)) | Delta schema enforcement by default; Spark requires schema for streaming files (PIPE-11, PIPE-08) | Layer-based: raw accepted, enforced from Silver. | Resolved (layering) |
| C-54 | Lambda or Kappa | Lambda documented by Azure (CLOUD-17) | Kreps and Akidau argue against dual codebases (PIPE-15, PIPE-16, PIPE-17) | Largely against Lambda. Kappa needs long retention. | Partly resolved |
| C-55 | Schema evolution across formats | Iceberg rename and drop are safe (PIPE-10) | Delta needs column mapping; Hudi experimental (PIPE-11, PIPE-12) | Portable set is the intersection. | Resolved (context) |
| C-56 | Scope of a data contract | ODCS: schema plus quality, SLA, team, roles and more (PIPE-20) | Confluent pattern: schema and registry (PIPE-03) | Different layers; ODCS is broader. | Resolved (context) |
| C-57 | Post-build tests or pre-publish gates | dbt data tests after build (LAKE-19) | Iceberg and Netflix WAP, Databricks fail-on-violation (DQ-12, DQ-13, DQ-14) | Complementary. No defect-catch data exists. | Resolved (layering) |
| C-58 | Blocking or tiered checks | Intuit circuit breaker is strictly blocking ([Strata 2019](https://conferences.oreilly.com/strata/strata-ca-2019/public/schedule/detail/73082.html)) | Netflix and Databricks accept tiering (DQ-13, DQ-14); Airbnb's reported experience is search-snippet only | Table criticality. | Resolved (context) |
| C-59 | Shift-left or downstream tooling | Confluent; Sanderson via InfoWorld only (DQ-11) | Warehouse-native tools assume data has landed (LAKE-19, DQ-07) | Layers. Both advocates are vendor-adjacent. | Partly resolved |
| C-60 | Vendor taxonomy or open standard | Monte Carlo pillars, which have changed over time (DQ-08) | OpenLineage facets under LF governance (GOV-31) | Prefer specifications. | Resolved (context) |
| C-61 | Fabric or Mesh | Fabric as metadata automation (ARCH-21) | Mesh as ownership model (ARCH-14) | Complementary in every source that compares them; no independent primary source for fabric. | Partly resolved |
| C-62 | Use of 2PC | Spanner in favour (TXN-20) | microservices.io against (ARCH-06); PostgreSQL restricts prepared transactions to transaction managers | Engine-managed consensus against application-level services. | Resolved (context) |
| C-63 | CAP framing | Brewer: limited design corner (TXN-15) | Abadi adds normal-operation latency; Kleppmann finds CAP too ambiguous (TXN-14, TXN-16) | Practical guidance agrees. Gilbert and Lynch's theorem text was confirmed at the catalogued URL (note 22); no further claims from it are used. | Unresolved |
| C-64 | Explicit locks under SERIALIZABLE | PostgreSQL: remove FOR UPDATE when SERIALIZABLE protects (PGMY-08) | Leach combines SERIALIZABLE with a locked_at column (TXN-19); Jepsen offers FOR UPDATE or SERIALIZABLE for MySQL (TXN-11) | Engine and pattern. | Resolved (context) |
| C-65 | Idempotency replay | Stripe v1 replays saved responses including failures; v2 retries to completion (CASE-33) | Retention windows of about 24 h and 72 h in one source (TXN-19) | API version and business need. | Partly resolved |
| C-66 | Uber's Postgres to MySQL move | Uber's stated limits (CASE-09) | Winand, Riggs, Pettus rebuttals (CASE-12, CASE-13, CASE-14, CASE-11) | Workload-specific; do not generalise. | Resolved (context) |
| C-67 | Kimball or Inmon | Bus architecture, dimensional atomic data (DWM-04, DWM-01) | CIF, integrated granular foundation (DWM-06) | [INFERENCE] The live decision is whether an integration layer is justified. | Resolved (context) |
| C-68 | Star or One Big Table | Star retained at presentation (DWM-14, LAKE-06, LAKE-14) | OBT faster in a vendor-hosted test [WF]; dbt marts favour wide (DWM-22, LAKE-15); BENCH-10 is mixed by engine | Derived consumption layer. Query speed is engine-dependent (C-84). One conference benchmark, none reproduced. | Partly resolved |
| C-69 | No joins at scale | Pinterest 2012 removed joins (CASE-05) | Figma, Notion, Citus preserve joins within shard locality (CASE-01, CASE-02, PERF-44) | Locality scope. | Resolved (context) |
| C-70 | Deletes at scale | Textbook physical DELETE | ERP flags, ledger reversal, LSM tombstones (CASE-44, TEN-43, CASE-15) | Workload and storage engine. | Resolved (context) |
| C-71 | Automatic clustering or manual sharding | Pinterest 2012 wary of auto-sharding (CASE-05) | Vitess adoption at Slack and GitHub; ScyllaDB at Discord (CASE-07, CASE-04, CASE-16) | Time and maturity dependent; Figma and Notion still chose application sharding. | Unresolved |
| C-72 | Vendor reversal behaviour against German non-alteration | D365 reverse year-end deletes vouchers with a history record and posts no reversing voucher (ERP-10, ERP-12); NetSuite Delete keeps only a record of deletion (ERP-15) | HGB 239(3) and AO 146(4) forbid changes that lose original content (ERP-23) | Binds in Germany only. No source read says whether generated opening balances are books under the statute. | Unresolved |
| C-73 | Reversal of a reversal | Oracle: not allowed (ERP-06) | D365: allowed (ERP-12) | Product choice. | Unresolved |
| C-74 | What a reversal does to activity totals | SAP normal reversal raises figures; negative posting resets them (ERP-02) | Oracle Change Sign keeps the column and flips sign (ERP-06) | Debit and credit activity differs by method, so the method must be recorded. | Resolved (context) |
| C-75 | Permanent period close | Oracle and Odoo offer irreversible close (ERP-05, ERP-18) | D365 offers it and advises against it (ERP-10) | Product and policy choice. | Unresolved |
| C-76 | Revaluation reversal | D365 GL does not reverse earlier revaluation (ERP-11) | D365 AR and AP do (ERP-11). An older Oracle snippet is unverified and not relied on | Varies inside one product. | Unresolved |
| C-77 | Inverse rates | Oracle stores an inverse row generally the reciprocal (ERP-08) [WF] | ERPNext says the inverse is not automatically equal and needs its own record (ERP-20); SAP presents direct and indirect quotation (ERP-03) | A rate and its reciprocal may disagree after rounding. No standard read settles it. | Unresolved |
| C-78 | Rate effective-dating | Oracle exact-day row (ERP-08) | ERPNext most recent eligible record (ERP-20) | SAP valid-from logic was not established. | Unresolved |
| C-79 | Invoice number gaps by country | France: chronological and continuous, no tolerance found (LEG-07, LEG-08) | UK: gaps tolerated if explained or the spoiled invoice is kept (LEG-14); Saudi Arabia: rejected documents consume a counter value (LEG-26) | No single rule exists. Germany rests on unverified snippets (LEG-06); Italy, Spain, Pakistan and UAE do not address gaps in texts read. [INFERENCE] strictest rule per legal entity. | Unresolved |
| C-80 | Overlapping retention periods | France tax 6 years (LEG-09) | France commercial 10 years, snippet-only; Germany 8-year voucher transition not read (LEG-05) | [INFERENCE] the longer period where both apply; verify both before use. | Partly resolved |
| C-81 | Erasure from backups | Dutch AP reads as stricter, keeping records and erasing on restore (LEG-35) | ICO beyond-use approach (LEG-33); California delay until restore or next use (LEG-29) | Different regimes. EDPB lists timing as a possible future guidance item (LEG-32). | Unresolved |
| C-82 | Is a hash chain required | No law read requires hashing for general ledgers; Odoo offers one (ERP-18) | ZATCA requires a previous-invoice hash for e-invoices (LEG-26, LEG-27) | Scope: KSA e-invoicing against general ledgers. | Resolved (context) |
| C-83 | UNIQUE and NULL | MySQL permits many NULLs (ENG-05) [WF]; PostgreSQL NULLs distinct by default (PGMY-01) | SQL Server one NULL per column (ENG-10) [WF]; Oracle composite-specific rule (ENG-15) [WF] | Engine-specific. No portable default. | Resolved (context) |
| C-84 | One Big Table against star, by engine | Star faster on Redshift and MariaDB Columnstore (BENCH-10) | Flat faster on Singlestore (BENCH-10); flat faster on Redshift, Snowflake and BigQuery in a vendor-hosted test (DWM-22) [WF] | The two disagree on Redshift. Benchmark, cluster and distribution keys differ. No general rule. | Unresolved |
| C-85 | Subtype mapping default | Hibernate favours joined tables for constraints (THIN-04) | EF Core defaults to one table and warns on joined-table performance (THIN-05) | Different goals; no engine-neutral benchmark. | Unresolved |
| C-86 | Data Vault against star performance | Star led on runtime at laptop scale (BENCH-11) | No significant difference among some models, weak controls (BENCH-12) | Neither supports a production claim. Judgment. | Unresolved |
| C-87 | Redshift isolation naming | SNAPSHOT and SERIALIZABLE both called serializable levels (ENG-22) | Same page: only SERIALIZABLE prevents write skew (ENG-22) | Name the guarantee, not the level (U12). | Resolved (context) |
| C-88 | SQL Server datetimeoffset and DST | Property table: not DST aware (ENG-09) [WF] | Prose: offset assumed DST aware (ENG-09) [WF] | Treat as a fixed offset; the AT TIME ZONE page was not opened. | Partly resolved |
| C-89 | Meaning of required field in linters | Squawk's rule concerns migration safety (OPS-16) | Schemalint, Atlas and prisma-lint mean a table policy (THIN-16, OPS-13, THIN-24) | Different checks; do not treat as equivalent. | Resolved (context) |

---

# Part D. Evidence limits and items the notes could not support

| # | Limit | Effect on this analysis |
|---|---|---|
| D1 | No standards or regulatory source in the notes prescribes append-only ledgers or debits equalling credits as a database rule; note 15 records debits equal credits as accounting first principles not sourced there. HGB 239(3) requires non-alteration in Germany without naming a mechanism, and 15 USC 78m names none. | Ledger immutability and balance invariants are RECOMMENDED here on convergent case studies and vendor practice (TEN-41, TEN-42, TEN-43, CASE-30, ERP-06), with non-alteration MANDATORY only in Germany, although notes 12 and 14 label them MANDATORY. |
| D2 | Idempotency evidence is Stripe plus one practitioner source. | RECOMMENDED here, although note 12 labels it MANDATORY. |
| D3 | Fiscal period status, rate tables and reversal now have product and partial legal evidence (B7, B8). Rate precision, triangulation, consolidation elimination rules and gap treatment in several countries were not found. | Open items stay unclassified in the matrix (FN-19, FN-30, LG-2 to LG-5, LG-7, LG-8). |
| D4 | Schema-per-tenant is not recommended or assessed by any fetched source. | B4 marks attributes not assessed. |
| D5 | No quantified comparison of validation layers or contract agility cost. RLS overhead rests on one small practitioner test (BENCH-07). | Trade-offs are stated qualitatively and RLS cost is a judgment (B9). |
| D6 | No independent benchmark of UUIDv7 against bigint, RLS, foreign keys at scale, or Data Vault against star. One conference benchmark covers OBT against star, and the seven approaches have no like-for-like comparison. | Ratings in B3 are relative judgments. B9 states the status per topic. Figures marked [WF] are unconfirmed. |
| D7 | ISO paywalled texts (9075, 11179-5, 25012, 25024) were seen only through catalogue scope statements. | Clause-level claims are not made. |
| D8 | CIS Benchmarks PDFs are gated. | No recommendation numbers are cited. |
| D9 | No regulator text found accepts key destruction as erasure; the EDPB blockchain text is a consultation version describing the effect (LEG-34). | Marked inference and not settled; NIST SP 800-88 preconditions are the nearest technical basis (SEC-12). |
| D10 | Search-only or unverified resources: Pinterest Medium post, Instagram Sharding and IDs, four Airbnb posts, the retired AWS whitepapers. CLOUD-04 failed verification (note 22). | Not relied on for any classification. |
| D11 | Gartner and Data Fabric definitions are third-party or vendor sourced. | Marked in B5 and C-61. |
| D12 | DDIA chapter-level claims, Karwin's remedies and legitimate-use sections, and PACELC system classifications were not verified. Note 22 confirms the PACELC definition only. | Not used. Karwin is cited only for publisher-listed antipattern names. |
| D13 | Streaming security and topic-level tenancy were not researched. MySQL row-level capability and SQL Server deferrable constraints are known only from absence in pages read (note 21). | Marked not verified. |
| D14 | Numeric thresholds such as maximum index counts, schema-to-server split points, quality SLO targets and incident SLAs do not exist in the notes. | No thresholds are proposed. |
| D15 | Note 13's ISO 22301 details come from a national standards record because iso.org refused access. | Not relied on. |
| D16 | SAP product documentation rendered empty; FASB Codification and PCAOB standards returned 403; IAS 21 and IFRS 10 full text requires sign-in; GoBD returned 503. | SAP rests on training pages. ASC 830 is known through a superseded statement and an SEC order. No IFRS paragraph numbers are cited. |
| D17 | UStAE 14.5(10) is unverified (LEG-06); French Article 242 nonies A and L123-22 were not opened. | Germany gap treatment and the French commercial period are not relied on. |
| D18 | ViDA transposition, Italian and Spanish retention, UAE corporate tax retention, and Saudi income tax retention were not researched. | No statement is made. |
| D19 | PCI DSS v4.0.1 text could not be read; wording is from the v4.0 SAQ D. ICO and Dutch AP pages are Wayback captures. | Requirement wording must be rechecked before use. |
| D20 | Note 22 could not find several claims, including the Kimball wording on keys encoding meaning, the DORA rigor wording, the Instagram late-2011 date and the TAO storage attribution. | Not relied on. |
| D21 | Published ISO/IEC 11179-5 editions and ISO/IEC 38505 are unread; the 11179-5 draft is a truncated 2004 committee draft; ISO 25012 definitions are secondary. | No clause-level claims are made. |
