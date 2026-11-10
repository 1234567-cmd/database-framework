# Performance, Transactions and Scalability Standards

Stage 2 standards for indexing and performance (IDX), transaction management (TXN), and scalability and maintainability (SCL). Written from the research repository only. The registry copy is `../registry/03_performance_transactions_scalability.json`.

## Conventions used here

- `MUST` goes with MANDATORY, `SHOULD` with RECOMMENDED, `MAY` with OPTIONAL.
- `active` means a vendor document, standard or foundational paper states the rule directly. `provisional` means the rule is inference, legal, or rests only on case studies or practitioner sources. `needs_decision` meant an owner choice was open; no rule holds it after the owner decisions of 2026-11-08. `superseded` means a canonical rule replaced this one (see superseded_by).
- Exceptions name the framework exception approver (decision H1). No person has been named for the role yet.
- Evidence items are catalog IDs or research sections, written as `file §section, row IDs`.

## Classification record

The matrix classifications are followed. Where research documents differ, or a rule has no matrix row, it is listed here.

| Rule | Note |
|---|---|
| IDX-017, IDX-018 | `database_design_standards.md` 8.4 says MANDATORY; matrix IX-10 says RECOMMENDED. Followed the matrix. |
| IDX-006 | Note 10 and GitLab say MANDATORY; matrix IX-3 says RECOMMENDED per engine. Followed the matrix. |
| IDX-020 | Matrix IX-12 lists multi-vendor first. Recorded here as inference and provisional, because no vendor mandates it and support is indirect. Class unchanged. |
| TXN-006 | `database_design_standards.md` 10.2 says MANDATORY; matrix TX-5 says RECOMMENDED. Followed the matrix. |
| TXN-009, TXN-011, TXN-014 | Notes 12 and 14 and `database_design_standards.md` 10.4 say MANDATORY; matrix TX-7, TX-8, TX-10 say RECOMMENDED. Followed the matrix. |
| TXN-018 | `database_design_standards.md` 10.4 says MANDATORY; matrix TX-12 says RECOMMENDED for the mechanism. Followed the matrix. |
| IDX-004, IDX-015, IDX-016, TXN-002, TXN-008, TXN-012, TXN-022, TXN-023, TXN-024, SCL-003, SCL-006, SCL-010, SCL-017 | No dedicated matrix row. Taken from `database_design_standards.md`, `architecture_comparison.md` Part A, or `official_documentation.md` section 15, at the class stated there. |
| TXN-012 | MANDATORY comes from `architecture_comparison.md` U15, not a matrix row in this group. |
| SCL-004 | Matrix SM-3 lists CASE-05 (Pinterest 2012 slides). Left out; CASE-02 and CASE-03 carry the rule. |

## Indexing and performance (IDX)

### IDX-001: Index from named query patterns

**Statement.** Each secondary index on an OLTP table SHOULD be justified by a named query, join or constraint it serves.

| Field | Value |
|---|---|
| Level | RECOMMENDED |
| Scope | OLTP |
| Applies when | always |
| Status | active |
| Decision ref | null |
| Evidence strength | multi_vendor |
| Lifecycle stage | Schema Design |
| Check method | manual_review |

**Rationale.** Every index adds write and storage cost, so speculative indexes slow writes without helping any known read.

**Exceptions.** An index added ahead of a planned query, recorded with that query and approved by the framework exception approver.

**Engine notes.** No vendor or source gives a maximum index count, so no number is set. SQL Server names speculative indexing as a common mistake and advises extending existing indexes over near-duplicates.

**Evidence.** MSOM-01; MSOM-09; MSOM-15; PERF-09; PERF-17; PERF-27; PGMY-05; research/design_decision_matrix.md §8, IX-1; research/architecture_comparison.md §A1, U22

**Check.** Each secondary index is traceable to a recorded query, join or constraint.

### IDX-002: Remove unused indexes

**Statement.** Indexes that usage statistics show serve no query or constraint SHOULD be removed from OLTP tables.

| Field | Value |
|---|---|
| Level | RECOMMENDED |
| Scope | OLTP |
| Applies when | The engine exposes index usage data over a period long enough to include periodic workloads. |
| Status | active |
| Decision ref | null |
| Evidence strength | multi_vendor |
| Lifecycle stage | Monitoring |
| Check method | runtime_monitor |

**Rationale.** Unused indexes keep charging write, storage and maintenance cost for no read benefit.

**Exceptions.** Indexes kept for infrequent but critical runs such as period close, recorded and approved by the framework exception approver.

**Engine notes.** none

**Evidence.** MSOM-01; MSOM-15; PERF-17; research/design_decision_matrix.md §8, IX-1; research/official_documentation.md §15

**Check.** Index usage counters are reviewed and indexes with no recorded use are removed or justified.

### IDX-003: Trial index removal before dropping

**Statement.** An index MAY be made invisible or modelled hypothetically to test the effect of removing it before it is dropped.

| Field | Value |
|---|---|
| Level | OPTIONAL |
| Scope | OLTP |
| Applies when | The engine or an extension offers invisible or hypothetical indexes. |
| Status | active |
| Decision ref | null |
| Evidence strength | multi_vendor |
| Lifecycle stage | Schema Design |
| Check method | manual_review |

**Rationale.** Dropping an index that a query still needs causes a plan regression that takes a rebuild to reverse.

**Exceptions.** none

**Engine notes.** Invisible indexes exist in Oracle and MySQL. PostgreSQL has none natively; HypoPG provides hypothetical indexes.

**Evidence.** PERF-20; PERF-53; research/database_design_standards.md §8.3

**Check.** Where a trial was used, its result is recorded with the removal.

### IDX-004: Enforce known uniqueness with a unique constraint or index

**Statement.** Columns whose values are unique by business rule SHOULD carry a unique constraint or unique index.

| Field | Value |
|---|---|
| Level | RECOMMENDED |
| Scope | OLTP |
| Applies when | The engine enforces uniqueness. |
| Status | active |
| Decision ref | null |
| Evidence strength | multi_vendor |
| Lifecycle stage | Schema Design |
| Check method | schema_lint |

**Rationale.** Without it duplicates can enter and the optimizer loses information about row counts.

**Exceptions.** Distributed tables where the engine cannot enforce global uniqueness, with a compensating check approved by the framework exception approver.

**Engine notes.** NULL treatment in UNIQUE differs by engine and is not portable (C-83). [WF] SQL Server, MySQL and Oracle NULL behaviour needs a re-check against the vendor pages.

**Evidence.** MSOM-01; PGMY-01; ENG-05; ENG-10; ENG-15; research/database_design_standards.md §8.4; research/architecture_comparison.md §Part C, C-83

**Check.** Attributes documented as unique have a matching unique constraint or index.

### IDX-005: Composite B-tree key order

**Statement.** Composite B-tree indexes SHOULD lead with equality columns and then order sort and range columns by query use, and SHOULD NOT be ordered by selectivity alone.

| Field | Value |
|---|---|
| Level | RECOMMENDED |
| Scope | OLTP |
| Applies when | The index is a B-tree or equivalent ordered structure. |
| Status | active |
| Decision ref | null |
| Evidence strength | multi_vendor |
| Lifecycle stage | Schema Design |
| Check method | manual_review |

**Rationale.** A poor leading column stops the index serving its queries, and the most-selective-first folk rule produces that result.

**Exceptions.** none

**Engine notes.** Selectivity matters only among independent range columns. MongoDB uses Equality, Sort, Range, with a very selective range before sort. PostgreSQL says multicolumn indexes should be used sparingly and more than three columns is rarely helpful; PostgreSQL 18 skip scan relaxes the leading-column requirement in some cases. Snowflake clustering keys order low to high cardinality, a different mechanism that must not be transferred (C-29).

**Evidence.** PERF-06; PERF-16; PERF-18; PERF-34; MSOM-17; LAKE-10; research/design_decision_matrix.md §8, IX-2; research/architecture_comparison.md §Part C, C-28, C-29

**Check.** Composite index column order is compared with the predicates of the queries it serves.

### IDX-006: Index foreign keys by engine need

**Statement.** Foreign key columns SHOULD be indexed where the child is joined on them or the parent rows can be updated or deleted.

| Field | Value |
|---|---|
| Level | RECOMMENDED |
| Scope | OLTP |
| Applies when | A foreign key exists and the engine does not create the index automatically. |
| Status | active |
| Decision ref | null |
| Evidence strength | multi_vendor |
| Lifecycle stage | Schema Design |
| Check method | schema_lint |

**Rationale.** Without the index, parent changes scan the child table and on some engines take a broad lock on it.

**Exceptions.** Rarely joined append-only children, or parents never updated or deleted, recorded and approved by the framework exception approver.

**Engine notes.** InnoDB creates the index automatically. PostgreSQL does not, and says it is often a good idea. Oracle says index as a rule, to avoid child table locks and full scans, except where the parent key is never updated or deleted. SQL Server says useful but not required. Note 10 and GitLab treat this as mandatory on PostgreSQL; the matrix classification is followed.

**Evidence.** PGMY-01; PGMY-14; PERF-24; MSOM-02; MSOM-08; research/design_decision_matrix.md §8, IX-3; research/architecture_comparison.md §Part C, C-10; research/official_documentation.md §13, C4

**Check.** Foreign keys without a leading-column index are listed and each is indexed or has a recorded exemption.

### IDX-007: Covering indexes for named queries

**Statement.** A covering index MAY be used when a named query needs it and the table's write rate has been considered.

| Field | Value |
|---|---|
| Level | OPTIONAL |
| Scope | OLTP |
| Applies when | A named query would otherwise need repeated row lookups. |
| Status | active |
| Decision ref | null |
| Evidence strength | multi_vendor |
| Lifecycle stage | Schema Design |
| Check method | manual_review |

**Rationale.** Payload columns widen the index and raise write cost, and they can give no benefit on frequently updated tables.

**Exceptions.** none

**Engine notes.** SQL Server encourages included columns and warns against too-wide indexes. PostgreSQL payload columns help only when the table changes slowly enough for index-only scans to skip the heap, so its documentation is cautious.

**Evidence.** MSOM-01; PGMY-12; PERF-07; research/design_decision_matrix.md §8, IX-4

**Check.** Each covering index names its query and notes the table's update profile.

### IDX-008: Partial and expression indexes for named queries

**Statement.** A partial or expression index MAY be used for a named query or subset uniqueness, but not as a replacement for partitioning.

| Field | Value |
|---|---|
| Level | OPTIONAL |
| Scope | OLTP |
| Applies when | The query predicate matches the index condition or expression. |
| Status | active |
| Decision ref | null |
| Evidence strength | single_vendor |
| Lifecycle stage | Schema Design |
| Check method | manual_review |

**Rationale.** An index the query does not exactly match is never used, and sets of non-overlapping partial indexes are a poor substitute for partitioning.

**Exceptions.** none

**Engine notes.** PostgreSQL and SQL Server support partial or filtered indexes. MySQL and SQL Server index expressions through generated or computed columns.

**Evidence.** PERF-08; PERF-36; PGMY-05; research/design_decision_matrix.md §8, IX-5; research/official_documentation.md §2

**Check.** Each partial or expression index names its query, and no group of them stands in for partitioning.

### IDX-009: Specialized index types by operator need

**Statement.** A specialized index type MAY be chosen when the data shape or operator needs it and the B-tree default cannot serve the query.

| Field | Value |
|---|---|
| Level | OPTIONAL |
| Scope | all |
| Applies when | The engine provides the index type and the operator is in use. |
| Status | active |
| Decision ref | null |
| Evidence strength | single_vendor |
| Lifecycle stage | Schema Design |
| Check method | manual_review |

**Rationale.** Choosing a specialized type without the matching operator adds maintenance cost and gives no read benefit.

**Exceptions.** none

**Engine notes.** PostgreSQL offers GIN, GiST, SP-GiST, BRIN and hash; BRIN depends on correlation with physical row order. Hash indexes are equality-only on PostgreSQL and MySQL, and on SQL Server are for memory-optimized tables. Availability elsewhere is engine-specific.

**Evidence.** PGMY-04; PGMY-05; PERF-19; MSOM-01; research/design_decision_matrix.md §8, IX-6

**Check.** A specialized index records the operator or query that requires it.

### IDX-010: Analytical access paths by platform

**Statement.** Large analytical tables SHOULD use the access path native to the platform, such as columnar storage, bitmap indexes, or partitioning and clustering, rather than OLTP index design.

| Field | Value |
|---|---|
| Level | RECOMMENDED |
| Scope | OLAP, data_warehouse |
| Applies when | The table is a large fact or analytical table on a platform offering the access path. |
| Status | active |
| Decision ref | null |
| Evidence strength | multi_vendor |
| Lifecycle stage | Schema Design |
| Check method | manual_review |

**Rationale.** OLTP B-tree design does not suit scan-heavy analytical queries, and each platform's own path carries its own DML cost.

**Exceptions.** none

**Engine notes.** SQL Server uses clustered columnstore, with vendor-stated gains up to tenfold. Oracle bitmap indexes suit low-cardinality, rarely modified columns and are inappropriate for many OLTP applications. BigQuery uses partitioning and clustering. Snowflake micro-partitions are automatic and clustering keys are for large, typically multi-terabyte tables, with credit cost. Oracle star transformation requires bitmap indexes on fact foreign keys.

**Evidence.** PERF-02; PERF-24; PERF-38; MSOM-12; CLOUD-13; LAKE-10; research/design_decision_matrix.md §8, IX-7; research/architecture_comparison.md §A2, E17

**Check.** Each large analytical table records the platform access path chosen and why.

### IDX-011: Clustering and partitioning on lakehouse tables

**Statement.** Lakehouse tables MAY be clustered or partitioned on frequent filter columns, using the mechanism current for the table format, treated as a changeable physical choice.

| Field | Value |
|---|---|
| Level | OPTIONAL |
| Scope | lakehouse |
| Applies when | Queries filter repeatedly on the columns and the table format supports the mechanism. |
| Status | active |
| Decision ref | null |
| Evidence strength | multi_vendor |
| Lifecycle stage | Schema Design |
| Check method | manual_review |

**Rationale.** Treating a physical layout as part of the model makes it costly to change, and legacy advice can conflict with current engine behaviour.

**Exceptions.** none

**Engine notes.** Databricks recommends liquid clustering for new tables; it replaces partitioning and ZORDER and is incompatible with both, so 2022 Z-order advice is legacy. Fabric prefers liquid clustering for silver and gold. Iceberg offers hidden partitioning. Delta and Hudi expose partition columns.

**Evidence.** LAKE-03; CLOUD-21; PIPE-10; PIPE-11; PIPE-12; research/architecture_comparison.md §A2, E19; research/official_documentation.md §13, C17

**Check.** The clustering or partitioning choice is recorded and matches the current guidance for the table format.

### IDX-012: Materialized views in OLTP need a cost check

**Statement.** A materialized or indexed view MAY be used on an OLTP system only after its DML cost has been assessed against the write rate.

| Field | Value |
|---|---|
| Level | OPTIONAL |
| Scope | OLTP |
| Applies when | A materialized or indexed view is proposed on a transactional store. |
| Status | active |
| Decision ref | null |
| Evidence strength | single_vendor |
| Lifecycle stage | Schema Design |
| Check method | manual_review |

**Rationale.** View maintenance adds cost to every write on the base tables.

**Exceptions.** none

**Engine notes.** SQL Server offers indexed views with a stated DML cost. Stonebraker argues against them in OLTP. Oracle query rewrite has a stale-tolerant mode with a risk of inaccurate results. In OLAP and warehouse systems, materialized views are a normal tool (see IDX-010).

**Evidence.** PERF-04; PERF-26; PERF-38; research/architecture_comparison.md §Part C, C-19; research/database_design_standards.md §8.4

**Check.** A proposed OLTP materialized view has a recorded write-cost assessment.

### IDX-013: Partition for manageability, not point lookups

**Statement.** A table SHOULD be partitioned only when retention, maintenance or pruning on a dominant filter justifies it, and point lookup speed alone SHOULD NOT be the justification.

| Field | Value |
|---|---|
| Level | RECOMMENDED |
| Scope | OLTP, data_warehouse |
| Applies when | A table is very large or has data that is removed together. |
| Status | active |
| Decision ref | null |
| Evidence strength | multi_vendor |
| Lifecycle stage | Schema Design |
| Check method | manual_review |

**Rationale.** Partitioning adds planning cost and can slow queries that span many partitions, while the manageability benefits are what the sources agree on.

**Exceptions.** A measured case showing a pruning benefit, approved by the framework exception approver.

**Engine notes.** Thresholds are engine-specific and must not be merged: PostgreSQL suggests table size above server memory, Oracle cites 2 GB candidates (dated), SQL Server says partitioning rarely improves OLTP performance. Oracle's performance emphasis comes from DSS-style history tables with pruning (C-20).

**Evidence.** PGMY-06; PERF-03; MSOM-11; research/design_decision_matrix.md §8, IX-8; research/architecture_comparison.md §Part C, C-20; research/official_documentation.md §13, C10

**Check.** Each partitioned table records its reason, and the reason is not point lookup speed alone.

### IDX-014: Partition key columns in unique keys

**Statement.** On natively partitioned tables, every primary or unique key MUST include all partition key columns unless the engine provides a documented alternative and that alternative is recorded.

| Field | Value |
|---|---|
| Level | MANDATORY |
| Scope | OLTP, OLAP, data_warehouse |
| Applies when | The table is natively partitioned on an engine that enforces uniqueness. |
| Status | active |
| Decision ref | null |
| Evidence strength | multi_vendor |
| Lifecycle stage | Schema Design |
| Check method | schema_lint |

**Rationale.** Engines reject or cannot enforce such keys otherwise, so uniqueness is lost or the design fails at creation.

**Exceptions.** A documented engine alternative such as an Oracle global index or a SQL Server nonaligned index, recorded with its maintenance cost.

**Engine notes.** PostgreSQL and MySQL require it (engine-enforced). SQL Server requires the partitioning column in the clustering key and unique nonclustered indexes for alignment, with nonaligned indexes as the alternative. Oracle allows a global index without the partitioning key, so the rule is not universal without this exception (C9). Warehouses whose keys are informational do not enforce it.

**Evidence.** PGMY-06; PGMY-16; PERF-03; MSOM-11; research/design_decision_matrix.md §8, IX-9; research/architecture_comparison.md §A1, U6; research/official_documentation.md §13, C9

**Check.** Primary and unique keys on partitioned tables include the partition columns, or the alternative is recorded.

### IDX-015: Bound partition counts

**Statement.** Partition counts SHOULD stay within the bound justified for the workload and within what the engine plans efficiently.

| Field | Value |
|---|---|
| Level | RECOMMENDED |
| Scope | OLTP, OLAP, data_warehouse |
| Applies when | The table is partitioned. |
| Status | active |
| Decision ref | null |
| Evidence strength | multi_vendor |
| Lifecycle stage | Schema Design |
| Check method | catalog_query |

**Rationale.** Too many partitions raise planning time and memory.

**Exceptions.** none

**Engine notes.** No universal number exists. PostgreSQL planners handle up to a few thousand when most are pruned; SQL Server advises against many hundreds or thousands unless needed and caps at 15,000; MySQL caps at 8192; Oracle allows up to a million. Warehouse workloads can sensibly use more partitions than OLTP.

**Evidence.** PGMY-06; PGMY-16; PERF-03; MSOM-11; research/database_design_standards.md §9.3; research/official_documentation.md §15

**Check.** Partition counts per table are listed and compared with the recorded bound.

### IDX-016: Do not assume foreign keys work with partitioning

**Statement.** A design combining foreign keys and partitioned tables SHOULD be confirmed against the target engine before adoption.

| Field | Value |
|---|---|
| Level | RECOMMENDED |
| Scope | OLTP |
| Applies when | A partitioned table is on either side of a foreign key. |
| Status | active |
| Decision ref | null |
| Evidence strength | multi_vendor |
| Lifecycle stage | Schema Design |
| Check method | manual_review |

**Rationale.** Portable designs break when an engine rejects the combination.

**Exceptions.** none

**Engine notes.** MySQL does not support foreign keys on user-partitioned InnoDB tables. PostgreSQL allows foreign keys to reference partitioned tables since version 12; the child side was not confirmed in the research.

**Evidence.** PGMY-16; PGMY-06; ENG-08; research/architecture_comparison.md §A2, E7

**Check.** Foreign keys touching partitioned tables are confirmed against the engine documentation for the target version.

### IDX-017: Predicates that can use the index

**Statement.** Query predicates SHOULD compare values of matching types and SHOULD NOT wrap indexed columns in functions unless a matching expression index exists.

| Field | Value |
|---|---|
| Level | RECOMMENDED |
| Scope | all |
| Applies when | The query runs on a relational engine using indexes or pruning. |
| Status | active |
| Decision ref | null |
| Evidence strength | multi_vendor |
| Lifecycle stage | Schema Design |
| Check method | manual_review |

**Rationale.** Implicit conversions and functions on columns can prevent index use and force scans.

**Exceptions.** none

**Engine notes.** MySQL cannot use a string column's index when comparing it to a number. MySQL and SQL Server use generated or computed columns for expression indexing. `database_design_standards.md` 8.4 labels the matching-types statement MANDATORY; the matrix class RECOMMENDED is followed.

**Evidence.** PERF-17; PERF-23; PERF-36; research/design_decision_matrix.md §8, IX-10; research/database_design_standards.md §8.2

**Check.** Reviewed queries have type-matched predicates and no unindexed function on a filtered column.

### IDX-018: Keep statistics current and check plans

**Statement.** Engines with cost-based optimizers SHOULD have statistics kept current, and plans for critical queries SHOULD be checked against observed behaviour.

| Field | Value |
|---|---|
| Level | RECOMMENDED |
| Scope | all |
| Applies when | The engine uses a cost-based optimizer. |
| Status | active |
| Decision ref | null |
| Evidence strength | multi_vendor |
| Lifecycle stage | Monitoring |
| Check method | runtime_monitor |

**Rationale.** Stale statistics lead the planner to choose poor plans, and unmeasured plans hide regressions.

**Exceptions.** none

**Engine notes.** PostgreSQL estimates depend on ANALYZE. EXPLAIN ANALYZE really executes the statement, so side effects occur. The research labels this MANDATORY in one place; the matrix class RECOMMENDED is followed.

**Evidence.** PERF-13; PERF-17; research/design_decision_matrix.md §8, IX-10; research/database_design_standards.md §8.4

**Check.** Statistics age is monitored and critical query plans are reviewed after major data or version changes.

### IDX-019: Optimizer hints as a last resort

**Statement.** Optimizer hints SHOULD be used only as a last resort, with a recorded reason and a review at each engine upgrade.

| Field | Value |
|---|---|
| Level | RECOMMENDED |
| Scope | OLTP |
| Applies when | A hint is proposed on an engine that supports hints or a hint extension. |
| Status | provisional |
| Decision ref | null |
| Evidence strength | single_vendor |
| Lifecycle stage | Schema Design |
| Check method | manual_review |

**Rationale.** Hints freeze a plan choice that can become wrong as data and engine versions change.

**Exceptions.** Each hint is itself an exception and is approved by the framework exception approver.

**Engine notes.** Evidence is the 2015 PostgreSQL community position, which predates current pg_hint_plan use and has not been re-validated. Oracle and SQL Server hint cautions were not fetched.

**Evidence.** PERF-55; research/design_decision_matrix.md §8, IX-11; research/database_design_standards.md §8.3

**Check.** Each hint has a recorded reason and a review date.

### IDX-020: Select only needed columns

**Statement.** Queries in application and pipeline code SHOULD name the columns they need rather than selecting all columns.

| Field | Value |
|---|---|
| Level | RECOMMENDED |
| Scope | all |
| Applies when | The query is in maintained code rather than ad hoc analysis. |
| Status | provisional |
| Decision ref | null |
| Evidence strength | inference |
| Lifecycle stage | Schema Design |
| Check method | manual_review |

**Rationale.** Selecting all columns can stop covering indexes and columnar pruning from helping, and hides schema dependencies.

**Exceptions.** Ad hoc analysis needs no approval.

**Engine notes.** No vendor mandates this. Support is indirect, through covering index and columnar mechanics, so strength is recorded as inference despite the matrix listing multi-vendor first.

**Evidence.** PERF-02; PERF-04; PERF-07; research/design_decision_matrix.md §8, IX-12; research/database_design_standards.md §8.4

**Check.** Maintained queries name their columns.

### IDX-021: Keyset pagination for deep paging

**Statement.** Deep or unbounded result paging SHOULD use keyset pagination, with OFFSET limited to shallow random access.

| Field | Value |
|---|---|
| Level | RECOMMENDED |
| Scope | OLTP |
| Applies when | Users or services page through large ordered result sets. |
| Status | active |
| Decision ref | null |
| Evidence strength | single_vendor |
| Lifecycle stage | Schema Design |
| Check method | manual_review |

**Rationale.** OFFSET reads and discards every skipped row, so cost grows with page depth.

**Exceptions.** Features that need arbitrary page jumps, which keyset cannot provide, approved by the framework exception approver.

**Engine notes.** Keyset requires a deterministic sort order.

**Evidence.** PERF-35; research/design_decision_matrix.md §8, IX-13

**Check.** Deep paging endpoints use a keyset with a deterministic sort.

### IDX-022: Avoid per-row query loops

**Statement.** Related rows SHOULD be fetched with joins or batched queries rather than one query per parent row.

| Field | Value |
|---|---|
| Level | RECOMMENDED |
| Scope | OLTP |
| Applies when | Application or ORM code loads related data. |
| Status | active |
| Decision ref | null |
| Evidence strength | single_vendor |
| Lifecycle stage | Schema Design |
| Check method | runtime_monitor |

**Rationale.** Per-row fetching multiplies network round trips and load.

**Exceptions.** none

**Engine notes.** Single practitioner source (Winand); the round-trip mechanics are inferred from vendor material.

**Evidence.** PERF-37; research/design_decision_matrix.md §8, IX-14; research/database_design_standards.md §8.4

**Check.** Query logs are checked for repeated single-row statements within one request.

### IDX-023: Default key type on single-node OLTP engines (judgment)

**Statement.** On single-node OLTP engines, generated primary keys SHOULD default to a 64-bit integer identity, and a time-ordered 128-bit identifier in native binary form SHOULD be used only where global or client-generated uniqueness is required.

| Field | Value |
|---|---|
| Level | RECOMMENDED |
| Scope | OLTP |
| Applies when | The primary key is generated on a single-node or non-range-sharded engine. |
| Status | active |
| Decision ref | A3 |
| Evidence strength | case_study |
| Lifecycle stage | Schema Design |
| Check method | schema_lint |

**Rationale.** Random keys scatter index writes and enlarge indexes, and 32-bit keys can overflow. This is a judgment, not a measured finding: no independent benchmark compares bigint, UUIDv7 and UUIDv4, and the practitioner tests agree on direction but not magnitude.

**Exceptions.** Natural keys or provably bounded lookup tables, approved by the framework exception approver.

**Engine notes.** [WF] BENCH-02 to BENCH-06 figures are from a summarising fetch and need a re-check against the source pages; BENCH-01 is one raw-confirmed blog test. No UUIDv7 benchmark exists for MySQL. Clustered engines (InnoDB, SQL Server) copy the key into secondary indexes, so width and order cost more there; PostgreSQL has heap storage yet still pays index scatter and write-ahead log costs. Time-ordered identifiers expose creation time. On range-sharded engines this default does not apply; see SCL-005. In pooled or sharded tables the key is composite: it includes the tenant or distribution column under TEN-014 and SCL-006.

**Evidence.** BENCH-01; BENCH-02; BENCH-03; BENCH-04; BENCH-05; BENCH-06; DES-04; DES-15; DES-16; PERF-15; MSOM-01; PGMY-12; research/architecture_comparison.md §B9; research/architecture_comparison.md §Part C, C-13; research/design_decision_matrix.md §7, DT-11, DT-12; research/database_design_standards.md §4.5

**Check.** Generated key columns use the approved default type, or carry a recorded reason for another type.

### IDX-024: Default surrogate key type in analytical models (judgment)

**Statement.** Surrogate keys in dimensional marts SHOULD be numeric, and hash or string keys SHOULD be chosen only where parallel, lookup-free loading is the priority and the choice is recorded.

| Field | Value |
|---|---|
| Level | RECOMMENDED |
| Scope | data_warehouse, lakehouse |
| Applies when | A dimensional mart needs surrogate keys. Data Vault and other integration layers are outside this default and record their own key convention. |
| Status | active |
| Decision ref | A4 |
| Evidence strength | multi_vendor |
| Lifecycle stage | Data Modeling |
| Check method | manual_review |

**Rationale.** Integer keys favour join and clustering performance while hashes favour parallel, idempotent loads. This is a judgment: no benchmark in the research settles the choice and conflict C-11 is settled for this framework by owner decision A4.

**Exceptions.** Deviation from the accepted default needs a recorded reason approved by the framework exception approver.

**Engine notes.** Kimball uses integers on dimensions except date, and Snowflake strongly recommends numeric join keys and warns that clustering considers only the first five VARCHAR bytes. Oracle recommends sequential integers for dimensions. dbt style says keys should be strings, and dbt's Kimball tutorial and Databricks' Data Vault guidance use hash keys. Canonical rule for OR-3: TYP-031 and RPT-007 are superseded by this rule.

**Evidence.** DES-12; DWM-01; DWM-21; LAKE-05; LAKE-14; LAKE-16; MSOM-12; research/architecture_comparison.md §Part C, C-11; research/design_decision_matrix.md §16, RP-6; research/official_documentation.md §13, C6

**Check.** Each analytical model records its key type and, if not the default, the reason.

## Transaction management (TXN)

### TXN-001: Specify isolation by guarantee

**Statement.** Each OLTP transaction class MUST state its required isolation as a guarantee tied to engine, level and configuration, never by the level's name alone.

| Field | Value |
|---|---|
| Level | MANDATORY |
| Scope | OLTP |
| Applies when | always |
| Status | active |
| Decision ref | null |
| Evidence strength | standard |
| Lifecycle stage | Transactions |
| Check method | manual_review |

**Rationale.** Isolation names are not portable: the same name gives different anomalies on different engines, so a design that relies on a name can be silently unsafe.

**Exceptions.** none

**Engine notes.** Defaults: PostgreSQL and Oracle read committed; InnoDB repeatable read; SQL Server read committed with locking; Azure SQL Database read committed with row versioning. Oracle SERIALIZABLE behaves as snapshot isolation per Hermitage (C-30). InnoDB repeatable read is unsafe for read-then-write logic per Jepsen (C-31). Hermitage is undated and directional. [WF] Spanner's default (ENG-24) needs a re-check against the page.

**Evidence.** TXN-03; TXN-08; TXN-10; TXN-11; PGMY-08; PGMY-18; MSOM-06; ENG-24; research/design_decision_matrix.md §9, TX-1; research/architecture_comparison.md §A1, U12; research/architecture_comparison.md §Part C, C-30, C-31; research/database_design_standards.md §10.2

**Check.** Each transaction class records engine, level, configuration and the guarantee it depends on.

### TXN-002: Do not assume isolation carries across analytical platforms

**Statement.** Pipelines writing to analytical platforms SHOULD rely only on the isolation that platform documents for the operation used.

| Field | Value |
|---|---|
| Level | RECOMMENDED |
| Scope | OLAP, data_warehouse, lakehouse |
| Applies when | A pipeline depends on concurrent read or write behaviour on the platform. |
| Status | active |
| Decision ref | null |
| Evidence strength | multi_vendor |
| Lifecycle stage | Transactions |
| Check method | manual_review |

**Rationale.** Isolation names and guarantees differ between platforms, so assumptions from OLTP or from another platform can produce wrong results.

**Exceptions.** none

**Engine notes.** This is stated separately from TXN-001 because the research does not cover OLAP transaction semantics in depth. Snowflake tables support only READ COMMITTED. Redshift defaults to SNAPSHOT, and calls SNAPSHOT and SERIALIZABLE both serializable levels although only SERIALIZABLE prevents write skew (C-87). Current Databricks isolation options were not captured. [WF] BigQuery snapshot isolation (ENG-21) and Cosmos DB consistency settings (ENG-26) need a re-check against the pages.

**Evidence.** ENG-19; ENG-21; ENG-22; ENG-26; research/architecture_comparison.md §A2, E25; research/architecture_comparison.md §Part C, C-87; research/official_documentation.md §14

**Check.** Pipelines depending on concurrency record the platform guarantee they use.

### TXN-003: Protect read-then-write invariants

**Statement.** Cross-row invariants enforced by read-then-write logic MUST be protected by true serializable execution with retries, explicit row locks, or a declarative constraint.

| Field | Value |
|---|---|
| Level | MANDATORY |
| Scope | OLTP |
| Applies when | The invariant spans rows and runs under snapshot-class or repeatable-read isolation. |
| Status | active |
| Decision ref | null |
| Evidence strength | standard |
| Lifecycle stage | Transactions |
| Check method | manual_review |

**Rationale.** Snapshot isolation allows write skew by construction, so limits such as credit or stock can be broken without any error.

**Exceptions.** none

**Engine notes.** PostgreSQL repeatable read is snapshot isolation and allows write skew; SERIALIZABLE uses SSI. Oracle SERIALIZABLE is treated as snapshot isolation (C-30). Do not rely on InnoDB repeatable read for this; use locking reads or SERIALIZABLE (C-31). PostgreSQL says to remove explicit locks when SERIALIZABLE protects, while Leach combines both (C-64).

**Evidence.** TXN-03; TXN-04; TXN-11; PGMY-08; research/design_decision_matrix.md §9, TX-2; research/architecture_comparison.md §A1, U14; research/architecture_comparison.md §Part C, C-64

**Check.** Each cross-row invariant names the mechanism that protects it.

### TXN-004: Retry whole transactions on concurrency failures

**Statement.** Transactions that can fail with serialization, deadlock or write-conflict errors MUST be retried as whole transactions.

| Field | Value |
|---|---|
| Level | MANDATORY |
| Scope | OLTP |
| Applies when | The engine can abort the transaction for a concurrency reason. |
| Status | active |
| Decision ref | null |
| Evidence strength | multi_vendor |
| Lifecycle stage | Transactions |
| Check method | pipeline_test |

**Rationale.** Surfacing or partly retrying these errors loses work or applies part of a change.

**Exceptions.** none

**Engine notes.** Signals differ: PostgreSQL SQLSTATE 40001; SQL Server errors 3960 and 1205; Oracle ORA-08177 and ORA-00060; MongoDB TransientTransactionError and UnknownTransactionCommitResult. Use backoff on managed services (Azure SQL, Cloud SQL guidance).

**Evidence.** PGMY-08; MSOM-18; CLOUD-14; research/design_decision_matrix.md §9, TX-3; research/architecture_comparison.md §A1, U13; research/official_documentation.md §15

**Check.** A test forces a concurrency failure and confirms the whole transaction is retried.

### TXN-005: Bound transactions by aggregate

**Statement.** A single transaction SHOULD change one aggregate, with changes across aggregates handled through eventual consistency.

| Field | Value |
|---|---|
| Level | RECOMMENDED |
| Scope | OLTP |
| Applies when | Domain aggregates are defined. |
| Status | active |
| Decision ref | null |
| Evidence strength | multi_vendor |
| Lifecycle stage | Transactions |
| Check method | manual_review |

**Rationale.** Transactions spanning aggregates widen contention and couple parts of the domain.

**Exceptions.** Documented cases where an invariant truly spans aggregates, approved by the framework exception approver.

**Engine notes.** MongoDB prefers single-document atomicity. The research records debate over whether this rule is absolute.

**Evidence.** ARCH-02; ARCH-03; MSOM-18; research/design_decision_matrix.md §9, TX-4

**Check.** Transactions touching more than one aggregate are listed and justified.

### TXN-006: Keep transactions short

**Statement.** Transactions SHOULD be no longer than integrity requires and SHOULD NOT remain open while waiting for user input.

| Field | Value |
|---|---|
| Level | RECOMMENDED |
| Scope | OLTP |
| Applies when | always |
| Status | active |
| Decision ref | null |
| Evidence strength | multi_vendor |
| Lifecycle stage | Monitoring |
| Check method | runtime_monitor |

**Rationale.** Long transactions hold locks and block maintenance, which leads to contention and engine-specific failures.

**Exceptions.** none

**Engine notes.** PostgreSQL long transactions hold back VACUUM and it offers idle-in-transaction timeouts. MongoDB imposes a 60-second transaction limit. Oracle can fail with ORA-01555. SQL Server escalates locks at 5,000 on one statement; consider RCSI or SNAPSHOT and batch large deletes. The standards document labels this MANDATORY; the matrix class RECOMMENDED is followed.

**Evidence.** PGMY-08; MSOM-18; research/design_decision_matrix.md §9, TX-5; research/database_design_standards.md §10.2

**Check.** Transaction duration and idle-in-transaction time are monitored against a set limit.

### TXN-007: Optimistic control across system transactions

**Statement.** Business transactions spanning several system transactions SHOULD use a version column with a compare-and-set update.

| Field | Value |
|---|---|
| Level | RECOMMENDED |
| Scope | OLTP |
| Applies when | A user or process edits data across more than one system transaction. |
| Status | active |
| Decision ref | null |
| Evidence strength | multi_vendor |
| Lifecycle stage | Transactions |
| Check method | manual_review |

**Rationale.** Without a version check one writer can silently overwrite another.

**Exceptions.** High-contention cases using pessimistic or advisory locks, approved by the framework exception approver.

**Engine notes.** An integer or engine version is preferred to a timestamp column, which is not guaranteed unique or monotonic [INFERENCE]. SQL Server provides rowversion. PostgreSQL advisory locks fit pessimistic patterns that sit poorly with MVCC.

**Evidence.** DES-14; PGMY-08; research/design_decision_matrix.md §9, TX-6; research/database_design_standards.md §10.2

**Check.** Multi-step edits use a version check and handle a lost compare.

### TXN-008: Consistent lock ordering

**Statement.** Transactions that lock several rows or resources SHOULD acquire them in a consistent order.

| Field | Value |
|---|---|
| Level | RECOMMENDED |
| Scope | OLTP |
| Applies when | A transaction takes more than one lock. |
| Status | active |
| Decision ref | null |
| Evidence strength | multi_vendor |
| Lifecycle stage | Transactions |
| Check method | manual_review |

**Rationale.** Inconsistent ordering causes deadlocks.

**Exceptions.** none

**Engine notes.** Grounded on PostgreSQL and SQL Server documentation.

**Evidence.** research/database_design_standards.md §10.2

**Check.** Code paths taking multiple locks follow a documented order.

### TXN-009: Idempotency for retried side effects

**Statement.** Operations whose retries can cause duplicate effects SHOULD record an idempotency key under a unique constraint scoped to the caller, and SHOULD compare request parameters on replay.

| Field | Value |
|---|---|
| Level | RECOMMENDED |
| Scope | OLTP |
| Applies when | Clients or systems can retry an operation with external or financial effects. |
| Status | provisional |
| Decision ref | null |
| Evidence strength | case_study |
| Lifecycle stage | Transactions |
| Check method | pipeline_test |

**Rationale.** Retries after a timeout can double-apply money movement or other effects.

**Exceptions.** none

**Engine notes.** Evidence is Stripe documentation and one practitioner source (D2), so the note labels of MANDATORY are not followed. Tenant scoping is [INFERENCE] from Brandur's user scope. Stripe's suggestion of UUIDv4 for client tokens does not conflict with key locality guidance for primary keys.

**Evidence.** CASE-33; TXN-19; research/design_decision_matrix.md §9, TX-7; research/architecture_comparison.md §Part D, D2

**Check.** A duplicate request with the same key returns the recorded outcome and applies no second effect.

### TXN-010: Idempotency replay and retention policy

**Statement.** Idempotency records SHOULD return the saved outcome on replay and SHOULD be retained at least 24 hours.

| Field | Value |
|---|---|
| Level | RECOMMENDED |
| Scope | OLTP |
| Applies when | TXN-009 applies. |
| Status | active |
| Decision ref | B19 |
| Evidence strength | case_study |
| Lifecycle stage | Transactions |
| Check method | pipeline_test |

**Rationale.** Without a stated policy, clients cannot know whether a replay repeats work or how long a key protects them.

**Exceptions.** Longer retention set per business need by the framework exception approver.

**Engine notes.** Stripe API v1 replays saved responses including server errors; v2 retries work to completion. Retention is at least 24 hours at Stripe; Brandur's text gives about 24 hours and about 72 hours in different passages (C-65).

**Evidence.** CASE-33; TXN-19; research/architecture_comparison.md §Part C, C-65

**Check.** Replay behaviour and key expiry match the approved policy.

### TXN-011: Transactional outbox for event publication

**Statement.** Where events must match committed changes, the event SHOULD be written to an outbox in the same local transaction as the business change.

| Field | Value |
|---|---|
| Level | RECOMMENDED |
| Scope | OLTP, streaming |
| Applies when | A service publishes events derived from its own database changes. |
| Status | active |
| Decision ref | null |
| Evidence strength | multi_vendor |
| Lifecycle stage | Transactions |
| Check method | manual_review |

**Rationale.** Writing to the database and the broker separately loses or invents events on partial failure.

**Exceptions.** Log-based CDC as the relay or replacement where it meets the same guarantee, approved by the framework exception approver.

**Engine notes.** microservices.io treats log tailing as one relay option. CockroachDB prefers CDC to outbox tables on range-sharded engines to avoid index-tail contention (PERF-48). No vendor specifies a canonical outbox column list, so none is set. The notes' MANDATORY label is not followed.

**Evidence.** TXN-18; PIPE-05; TEN-27; PERF-48; PERF-56; research/design_decision_matrix.md §9, TX-8; research/database_design_standards.md §10.4

**Check.** Events are written in the same transaction as the change, and no separate dual write exists.

### TXN-012: Consumers tolerate redelivery

**Statement.** Consumers and pipeline steps on at-least-once delivery MUST produce the same result when a message or run is repeated.

| Field | Value |
|---|---|
| Level | MANDATORY |
| Scope | streaming, OLTP |
| Applies when | Delivery is at-least-once or a run can repeat, including outbox relays and CDC. |
| Status | active |
| Decision ref | null |
| Evidence strength | multi_vendor |
| Lifecycle stage | Transactions |
| Check method | pipeline_test |

**Rationale.** A relay may publish more than once and runs can repeat, so a non-idempotent consumer double-applies effects.

**Exceptions.** none

**Engine notes.** This rule also applies to the outbox relay in TXN-011. Check for overlap with the pipeline group's rules when registries are merged.

**Evidence.** PIPE-01; PIPE-06; PIPE-08; PIPE-13; TXN-18; research/architecture_comparison.md §A1, U15

**Check.** A test replays messages or runs and confirms the result is unchanged.

### TXN-013: Sagas and managed two-phase commit

**Statement.** Multi-service workflows MAY use a saga with persisted state and compensating steps, and MAY use two-phase commit only inside a system or manager that governs it.

| Field | Value |
|---|---|
| Level | OPTIONAL |
| Scope | OLTP |
| Applies when | A workflow spans stores with no shared transaction. |
| Status | active |
| Decision ref | null |
| Evidence strength | standard |
| Lifecycle stage | Transactions |
| Check method | manual_review |

**Rationale.** Sagas have no automatic rollback or isolation across steps, and two-phase commit is not available across independently owned services.

**Exceptions.** none

**Engine notes.** Spanner runs two-phase commit over consensus inside a managed system. PostgreSQL restricts prepared transactions to external transaction managers and warns they hold back VACUUM. Saga countermeasure detail references an unread book and is not relied on; status columns as semantic locks are [INFERENCE]. Orchestration against choreography has no comparative evidence.

**Evidence.** TXN-17; TXN-20; ARCH-06; research/design_decision_matrix.md §9, TX-9; research/architecture_comparison.md §Part C, C-62

**Check.** Multi-service workflows record their compensation steps and where two-phase commit is used.

### TXN-014: Correct posted ledger entries by new entry

**Statement.** Posted ledger entries SHOULD be corrected by a new reversing or compensating entry rather than edited in place.

| Field | Value |
|---|---|
| Level | RECOMMENDED |
| Scope | OLTP |
| Applies when | The store is a financial ledger or subledger. |
| Status | superseded |
| Decision ref | null |
| Superseded by | FIN-034 |
| Evidence strength | multi_vendor |
| Lifecycle stage | Transactions |
| Check method | manual_review |

**Rationale.** Editing posted entries destroys the history that auditors and reconciliations depend on.

**Exceptions.** Product-specific reversal exceptions recorded and approved by the framework exception approver.

**Engine notes.** No standard or regulation read prescribes append-only storage as a database rule (D1). Convergent vendor and case-study practice is the basis, so the notes' MANDATORY label is not followed. Germany is covered by TXN-015. Check for overlap with the financial controls group. Superseded by FIN-034 under OR-6.

**Evidence.** TEN-41; TEN-42; TEN-43; CASE-30; CASE-31; ERP-02; ERP-06; research/design_decision_matrix.md §9, TX-10; research/architecture_comparison.md §Part D, D1

**Check.** Posted entries are never updated, and corrections appear as new entries.

### TXN-015: German non-alteration of books

**Statement.** Commercial and tax book entries subject to HGB section 239(3) or AO section 146(4) MUST NOT be changed in a way that loses their original content or leaves the timing of the change uncertain.

| Field | Value |
|---|---|
| Level | MANDATORY |
| Scope | OLTP |
| Applies when | The books fall under German commercial or tax law (Germany only). |
| Status | superseded |
| Decision ref | null |
| Superseded by | FIN-031 |
| Evidence strength | standard |
| Lifecycle stage | Transactions |
| Check method | manual_review |

**Rationale.** A change that loses original content breaches these statutes where they apply. The statutes prescribe no storage mechanism.

**Exceptions.** Requires legal review. No exception is defined here.

**Engine notes.** Superseded by FIN-031 under OR-7.

**Evidence.** ERP-23; research/design_decision_matrix.md §21, FN-20; research/design_decision_matrix.md §9, TX-10

**Check.** Reviewers confirm the design keeps original content and change timing ascertainable for in-scope books.

### TXN-016: Balance each journal per currency in the posting transaction

**Statement.** Each journal SHOULD be checked to balance per currency within the posting transaction.

| Field | Value |
|---|---|
| Level | RECOMMENDED |
| Scope | OLTP |
| Applies when | The store is a financial ledger. |
| Status | superseded |
| Decision ref | null |
| Superseded by | FIN-026 |
| Evidence strength | case_study |
| Lifecycle stage | Transactions |
| Check method | pipeline_test |

**Rationale.** A journal that does not balance is an error that gets far harder to trace once reporting has run.

**Exceptions.** none

**Engine notes.** No standard or regulation read prescribes this as a database rule (D1). Evidence is case studies and product documentation. Superseded by FIN-026 under OR-5.

**Evidence.** TEN-41; TEN-42; CASE-31; research/design_decision_matrix.md §9, TX-11; research/architecture_comparison.md §Part D, D1

**Check.** A test submits an unbalanced journal and confirms rejection.

### TXN-017: EU invoices carry sequential unique numbers

**Statement.** Invoices issued by EU VAT-registered suppliers MUST carry a sequential number that uniquely identifies the invoice.

| Field | Value |
|---|---|
| Level | MANDATORY |
| Scope | OLTP |
| Applies when | The supplier is VAT-registered in the EU. Other jurisdictions are covered by the legal numbering rules (LG-2 to LG-9). |
| Status | superseded |
| Decision ref | null |
| Superseded by | NUM-001 |
| Evidence strength | standard |
| Lifecycle stage | Transactions |
| Check method | manual_review |

**Rationale.** Non-compliant numbering breaches the VAT Directive invoice content requirement. The Directive does not say whether sequential excludes gaps.

**Exceptions.** Requires legal review. National gap rules differ (C-79).

**Engine notes.** Superseded by NUM-001 under OR-8.

**Evidence.** LEG-01; TEN-39; research/design_decision_matrix.md §9, TX-12; research/design_decision_matrix.md §22, LG-1

**Check.** Reviewers confirm the numbering series is sequential and unique for each in-scope supplier.

### TXN-018: Locked counter for continuous number series

**Statement.** Where a document number series must be continuous, the number SHOULD be assigned from a locked per-series counter inside the issuing transaction rather than from a sequence or identity column.

| Field | Value |
|---|---|
| Level | RECOMMENDED |
| Scope | OLTP |
| Applies when | A number series has a continuity requirement in its jurisdiction or policy. |
| Status | superseded |
| Decision ref | A6 |
| Superseded by | NUM-019 |
| Evidence strength | single_vendor |
| Lifecycle stage | Transactions |
| Check method | pipeline_test |

**Rationale.** Sequence values are consumed even when transactions roll back, so sequences alone cannot give continuous numbering. A per-series counter limits concurrency to one issuer at a time.

**Exceptions.** Requires legal review of the gap rule for each jurisdiction.

**Engine notes.** The explicit statement comes from PostgreSQL; applying it to other engines is [INFERENCE]. The locked-counter design is also inference. No single gap rule exists across jurisdictions (C-41, C-79 unresolved). France reads as continuous; the UK tolerates explained gaps; Saudi Arabia consumes a counter value on rejection. Superseded by NUM-019 under OR-4.

**Evidence.** TEN-33; TEN-39; LEG-01; research/design_decision_matrix.md §9, TX-12; research/architecture_comparison.md §Part C, C-41, C-79; research/database_design_standards.md §10.4

**Check.** A test rolls back an issuing transaction and confirms no number is lost in a continuous series.

### TXN-019: Set read and write concerns where snapshot needs them

**Statement.** Where an engine's snapshot guarantee depends on explicit read and write concern settings, transactions needing that guarantee MUST set them explicitly.

| Field | Value |
|---|---|
| Level | MANDATORY |
| Scope | OLTP |
| Applies when | The engine's transaction guarantees depend on such settings. |
| Status | active |
| Decision ref | H3 |
| Evidence strength | single_vendor |
| Lifecycle stage | Transactions |
| Check method | manual_review |

**Rationale.** Defaults or partial settings do not deliver the snapshot behaviour the design relies on.

**Exceptions.** none

**Engine notes.** On MongoDB use read concern snapshot with write concern majority. Jepsen's findings on MongoDB 4.2.6 predate the 5.0 majority default and are dated, but its point that snapshot read concern needs majority write concern stands in the sources.

**Evidence.** MSOM-18; research/design_decision_matrix.md §9, TX-13; research/database_design_standards.md §10.2

**Check.** Transaction code on affected engines sets both concerns explicitly.

### TXN-020: Route safety-critical reads to the primary

**Statement.** Reads that feed safety-critical decisions SHOULD go to the primary or use an engine guarantee proven for that purpose.

| Field | Value |
|---|---|
| Level | RECOMMENDED |
| Scope | OLTP |
| Applies when | Replicas are in use and the read drives a decision that must see current data. |
| Status | provisional |
| Decision ref | null |
| Evidence strength | case_study |
| Lifecycle stage | Transactions |
| Check method | manual_review |

**Rationale.** Replica endpoints can give weaker guarantees than the writer, so decisions may rest on stale or inconsistent data.

**Exceptions.** none

**Engine notes.** Jepsen found RDS PostgreSQL multi-AZ reader endpoints did not ensure Snapshot Isolation and recommends the writer endpoint for safety-critical reads. MongoDB needs majority read and write concerns for all causal consistency guarantees.

**Evidence.** PERF-31; research/design_decision_matrix.md §9, TX-14; research/database_design_standards.md §9.3

**Check.** Safety-critical reads are listed with the endpoint or guarantee used.

### TXN-021: Reassess anomaly assumptions at major versions

**Statement.** Isolation and anomaly assumptions SHOULD be rechecked at each major engine version.

| Field | Value |
|---|---|
| Level | RECOMMENDED |
| Scope | OLTP |
| Applies when | A major engine upgrade is planned. |
| Status | provisional |
| Decision ref | null |
| Evidence strength | case_study |
| Lifecycle stage | Transactions |
| Check method | manual_review |

**Rationale.** Implementations regress and defaults change, so an unrevised assumption can become wrong silently.

**Exceptions.** none

**Engine notes.** Jepsen's PostgreSQL 12.3 finding shows that regressions occur. The rule itself is [INFERENCE].

**Evidence.** TXN-10; TXN-11; TXN-12; research/design_decision_matrix.md §9, TX-15

**Check.** Upgrade plans include a recheck of the recorded isolation guarantees.

### TXN-022: Favor consistency for coordinated invariants

**Statement.** Systems of record whose invariants need coordination, such as uniqueness, sums or sequential numbering, SHOULD favor consistency over availability and latency.

| Field | Value |
|---|---|
| Level | RECOMMENDED |
| Scope | OLTP |
| Applies when | The system is distributed or replicated and holds financial or equivalent invariants. |
| Status | provisional |
| Decision ref | null |
| Evidence strength | inference |
| Lifecycle stage | Transactions |
| Check method | manual_review |

**Rationale.** Weakening coordination on these invariants allows states that cannot be repaired without compensation.

**Exceptions.** none

**Engine notes.** No source states this as a rule for ERP. It is [INFERENCE] from Bailis and Brewer's treatment of invariants.

**Evidence.** TXN-15; research/database_design_standards.md §10.3

**Check.** Designs of distributed systems of record identify coordinated invariants and how they are preserved.

### TXN-023: Describe distributed trade-offs in PACELC terms

**Statement.** Distributed design documents SHOULD describe consistency trade-offs for both partition and normal operation, using PACELC terms rather than CAP two-of-three labels.

| Field | Value |
|---|---|
| Level | RECOMMENDED |
| Scope | OLTP |
| Applies when | The system is distributed or replicated. |
| Status | active |
| Decision ref | C8 |
| Evidence strength | standard |
| Lifecycle stage | Data Modeling |
| Check method | manual_review |

**Rationale.** Two-of-three reasoning is outdated and hides the latency-consistency trade-off during normal operation.

**Exceptions.** Teams may use another framework the framework exception approver accepts.

**Engine notes.** Brewer, Abadi and Kleppmann each frame this differently (C-63), settled for this framework by owner decision C8. Abadi's 2012 system classifications predate current defaults and must not be reused as current facts.

**Evidence.** TXN-14; TXN-15; TXN-16; research/architecture_comparison.md §Part C, C-63; research/database_design_standards.md §10.3

**Check.** Design documents state the trade-off in both conditions.

### TXN-024: Do not use creation time as a global order

**Statement.** A timestamp column SHOULD NOT be used as the global order of events, and a single-writer sequence or ledger position SHOULD be used where order matters.

| Field | Value |
|---|---|
| Level | RECOMMENDED |
| Scope | OLTP |
| Applies when | A consumer or process depends on the order of records. |
| Status | provisional |
| Decision ref | null |
| Evidence strength | inference |
| Lifecycle stage | Data Modeling |
| Check method | manual_review |

**Rationale.** Timestamps are not reliably unique or monotonic, and sequence caching allows out-of-order values across sessions.

**Exceptions.** none

**Engine notes.** This is [INFERENCE] from PostgreSQL's CREATE SEQUENCE documentation.

**Evidence.** research/database_design_standards.md §10.4

**Check.** Processes that depend on order name an ordering column that is not a timestamp.

## Scalability and maintainability (SCL)

### SCL-001: Exhaust simpler scaling before sharding

**Statement.** OLTP systems SHOULD exhaust vertical scaling and vertical partitioning before horizontal sharding.

| Field | Value |
|---|---|
| Level | RECOMMENDED |
| Scope | OLTP |
| Applies when | Capacity growth is planned. |
| Status | provisional |
| Decision ref | null |
| Evidence strength | case_study |
| Lifecycle stage | Data Modeling |
| Check method | manual_review |

**Rationale.** Sharding adds lasting complexity, and teams in the sources adopted it only after simpler options ran out.

**Exceptions.** Workloads known to divide easily and to outgrow a single node, approved by the framework exception approver.

**Engine notes.** Case studies are observational and survivorship-biased. No source gives a numeric threshold for moving between stages. Azure's guidance fits vertical scaling to workloads that do not divide easily. See SCL-003 on planning keys early.

**Evidence.** CASE-01; CASE-02; CASE-04; CASE-08; PERF-58; research/design_decision_matrix.md §17, SM-1

**Check.** A sharding proposal records the simpler options tried and why they fell short.

### SCL-002: Shard key selection

**Statement.** A shard key SHOULD be present in nearly every transaction, have high cardinality and even frequency, and keep most transactions on one shard.

| Field | Value |
|---|---|
| Level | RECOMMENDED |
| Scope | OLTP |
| Applies when | The system is horizontally distributed. |
| Status | active |
| Decision ref | null |
| Evidence strength | multi_vendor |
| Lifecycle stage | Data Modeling |
| Check method | manual_review |

**Rationale.** Poor shard keys create hot shards and force queries across all shards.

**Exceptions.** none

**Engine notes.** Citus advises distribution by tenant or entity and not by timestamp. MongoDB advises hashed sharding for monotonic keys; queries without the shard key go to all shards. Vitess uses a unique Primary Vindex. Time is a good range partition key within a node and a poor distribution key across nodes: same column, different mechanism. Scatter-gather is a liability in OLTP and useful for large aggregations. DynamoDB and Cosmos DB want even distribution across partition keys.

**Evidence.** PERF-29; PERF-30; PERF-43; PERF-45; PERF-46; CLOUD-06; CLOUD-20; CASE-01; CASE-02; CASE-07; research/design_decision_matrix.md §17, SM-2; research/database_design_standards.md §9.3

**Check.** The shard key is shown against the top transactions, cardinality and value distribution.

### SCL-003: Plan distribution keys early when distribution is expected

**Statement.** Where horizontal distribution is expected, key and co-location design SHOULD be planned before tables grow rather than as an afterthought.

| Field | Value |
|---|---|
| Level | RECOMMENDED |
| Scope | OLTP |
| Applies when | Distribution is a realistic future need. |
| Status | active |
| Decision ref | null |
| Evidence strength | single_vendor |
| Lifecycle stage | Data Modeling |
| Check method | manual_review |

**Rationale.** Retrofitting a distribution key means re-keying large tables under load.

**Exceptions.** none

**Engine notes.** Azure says partitioning as an afterthought is harder. This does not conflict with SCL-001: capacity scaling comes first, and key design can still anticipate later distribution [INFERENCE].

**Evidence.** PERF-58; research/database_design_standards.md §9.3

**Check.** Models expected to distribute carry a chosen candidate key.

### SCL-004: Many logical shards on fewer physical nodes

**Statement.** Sharded systems SHOULD use more logical shards than physical nodes so that capacity can move without re-keying.

| Field | Value |
|---|---|
| Level | RECOMMENDED |
| Scope | OLTP |
| Applies when | The system uses application or middleware sharding. |
| Status | provisional |
| Decision ref | null |
| Evidence strength | case_study |
| Lifecycle stage | Data Modeling |
| Check method | manual_review |

**Rationale.** Tying shards to physical nodes makes every capacity change a re-keying project.

**Exceptions.** none

**Engine notes.** Evidence is case studies only. Matrix SM-3 also lists CASE-05 (Pinterest 2012 slides). It is left out as a precaution because research_gaps.md restricts Pinterest content; that restriction names the unverified Medium post (CASE-06), and CASE-05 is itself verified.

**Evidence.** CASE-02; CASE-03; research/design_decision_matrix.md §17, SM-3

**Check.** The sharding design records the logical to physical mapping.

### SCL-005: Avoid monotonic leading keys on range-sharded systems

**Statement.** Range-sharded systems SHOULD NOT lead high-write keys with monotonic values and SHOULD use the spreading method the platform documents.

| Field | Value |
|---|---|
| Level | RECOMMENDED |
| Scope | OLTP |
| Applies when | The engine distributes data by key range. |
| Status | active |
| Decision ref | null |
| Evidence strength | multi_vendor |
| Lifecycle stage | Schema Design |
| Check method | schema_lint |

**Rationale.** Monotonic keys concentrate inserts on one range, creating a write hotspot.

**Exceptions.** Low write-rate tables, approved by the framework exception approver.

**Engine notes.** Spanner recommends UUID version 4, bit-reversal or hash prefixes. CockroachDB recommends UUID keys or hash-sharded indexes, noting that hash-sharding makes range reads scan every shard. UUIDv7 reintroduces the monotonic pattern, so it is not a universal answer. This reverses single-node guidance by topology (C-13); see IDX-023.

**Evidence.** CLOUD-11; PERF-48; CLOUD-06; research/design_decision_matrix.md §17, SM-4; research/architecture_comparison.md §Part C, C-13; research/official_documentation.md §13, C1

**Check.** On range-sharded engines, no high-write table leads its key with a monotonic column.

### SCL-006: Distribution column in keys where the engine requires it

**Statement.** Where a distribution engine requires the distribution column in primary and foreign keys, keys MUST include it.

| Field | Value |
|---|---|
| Level | MANDATORY |
| Scope | OLTP |
| Applies when | The engine imposes this requirement. |
| Status | active |
| Decision ref | H3 |
| Evidence strength | single_vendor |
| Lifecycle stage | Schema Design |
| Check method | schema_lint |

**Rationale.** The engine otherwise rejects the constraint or cannot enforce it across nodes.

**Exceptions.** none

**Engine notes.** Citus requires the distribution column in primary and foreign keys. Other platforms place tenant columns differently: Microsoft as a leading primary key element on sharded tables, Salesforce as a partition key on generic tables (C-16).

**Evidence.** PERF-44; TEN-07; CLOUD-19; research/database_design_standards.md §9.3; research/architecture_comparison.md §Part C, C-16

**Check.** On such engines, keys include the distribution column.

### SCL-007: Keep transactions within a shard

**Statement.** Transactions on sharded systems SHOULD stay within one shard key value where possible.

| Field | Value |
|---|---|
| Level | RECOMMENDED |
| Scope | OLTP |
| Applies when | The system is sharded. |
| Status | active |
| Decision ref | null |
| Evidence strength | multi_vendor |
| Lifecycle stage | Transactions |
| Check method | manual_review |

**Rationale.** Cross-shard transactions add coordination cost and failure modes that application teams must handle.

**Exceptions.** Consensus-based engines designed for distributed transactions, per platform documentation, approved by the framework exception approver.

**Engine notes.** Spanner runs two-phase commit over consensus. Citus co-location keeps joins local to a shard, and Figma and Notion keep joins within shard locality (C-69).

**Evidence.** CASE-01; CASE-04; TXN-20; PERF-44; research/design_decision_matrix.md §17, SM-5; research/architecture_comparison.md §Part C, C-69

**Check.** Cross-shard transactions are listed and justified.

### SCL-008: Build or adopt a sharding layer

**Statement.** Teams needing sharding MAY adopt an existing sharding layer by default and MAY build one only with a recorded reason.

| Field | Value |
|---|---|
| Level | OPTIONAL |
| Scope | OLTP |
| Applies when | A sharding layer is needed. |
| Status | active |
| Decision ref | C9 |
| Evidence strength | case_study |
| Lifecycle stage | Data Modeling |
| Check method | manual_review |

**Rationale.** A home-built layer carries lasting maintenance, and adopted layers bring operational and fit limits. No comparative evidence exists, so this is a judgment.

**Exceptions.** Decision recorded by the framework exception approver.

**Engine notes.** Figma and Notion built their own, and Slack and GitHub adopted Vitess (X22). The maturity picture changes over time (C-71).

**Evidence.** CASE-01; CASE-02; CASE-04; CASE-07; research/design_decision_matrix.md §17, SM-6; research/architecture_comparison.md §A6, X22; research/architecture_comparison.md §Part C, C-71

**Check.** The sharding choice and reason are recorded.

### SCL-009: Read replicas with session guarantees

**Statement.** Reads that must see the writer's own changes SHOULD go to the primary or use the engine's session or causal guarantees.

| Field | Value |
|---|---|
| Level | RECOMMENDED |
| Scope | OLTP |
| Applies when | Read replicas are in use. |
| Status | active |
| Decision ref | null |
| Evidence strength | multi_vendor |
| Lifecycle stage | Data Modeling |
| Check method | manual_review |

**Rationale.** Replicas lag, so a user can fail to see their own change.

**Exceptions.** none

**Engine notes.** PostgreSQL replication is asynchronous by default, with remote_apply to wait for replay. MongoDB needs majority read and write concerns for causal guarantees. [WF] SQL Server redo visibility (ENG-12) and MySQL WAIT_FOR_EXECUTED_GTID_SET (ENG-02) need a re-check against the pages.

**Evidence.** PERF-31; ENG-02; ENG-07; ENG-12; CASE-53; research/design_decision_matrix.md §17, SM-7; research/architecture_comparison.md §A2, E26

**Check.** Read-your-writes paths name the endpoint or guarantee used.

### SCL-010: Asynchronous replicas for reporting

**Statement.** Asynchronous replicas MAY serve reporting provided their results do not feed transactional decisions.

| Field | Value |
|---|---|
| Level | OPTIONAL |
| Scope | OLAP |
| Applies when | Reports run on a replica. |
| Status | provisional |
| Decision ref | null |
| Evidence strength | inference |
| Lifecycle stage | Data Modeling |
| Check method | manual_review |

**Rationale.** Stale replica data feeding a transactional decision can cause incorrect actions.

**Exceptions.** none

**Engine notes.** No independent HTAP isolation benchmark was found, and HTAP claims stay at architecture level (B9).

**Evidence.** research/database_design_standards.md §10.3; research/architecture_comparison.md §B9

**Check.** Replica-based reports are not inputs to transactional processes.

### SCL-011: Connection pooling with known feature limits

**Statement.** Connection pooling MAY be used with its feature limits recorded.

| Field | Value |
|---|---|
| Level | OPTIONAL |
| Scope | OLTP |
| Applies when | Connection count limits throughput. |
| Status | active |
| Decision ref | null |
| Evidence strength | single_vendor |
| Lifecycle stage | Data Modeling |
| Check method | manual_review |

**Rationale.** Transaction pooling silently breaks session-level features.

**Exceptions.** none

**Engine notes.** PgBouncer transaction mode disables session-level features such as session advisory locks and SQL-level PREPARE. ProxySQL was not fetched.

**Evidence.** PERF-52; research/design_decision_matrix.md §17, SM-8

**Check.** The pooling mode is recorded and no session-level feature relies on it.

### SCL-012: Cache-aside for static read-heavy data

**Statement.** Cache-aside MAY be used for relatively static, frequently read data with an invalidation approach recorded.

| Field | Value |
|---|---|
| Level | OPTIONAL |
| Scope | OLTP |
| Applies when | Read load justifies a cache. |
| Status | active |
| Decision ref | null |
| Evidence strength | single_vendor |
| Lifecycle stage | Data Modeling |
| Check method | manual_review |

**Rationale.** Cache-aside does not guarantee consistency, so stale values can be served.

**Exceptions.** none

**Engine notes.** none

**Evidence.** PERF-57; research/design_decision_matrix.md §17, SM-9

**Check.** Cached entities name their invalidation approach.

### SCL-013: CQRS and separate read models

**Statement.** A separate read store MAY be introduced only when scale or storage needs differ between reads and writes.

| Field | Value |
|---|---|
| Level | OPTIONAL |
| Scope | OLTP |
| Applies when | The same database cannot serve reads and writes adequately. |
| Status | active |
| Decision ref | null |
| Evidence strength | single_vendor |
| Lifecycle stage | Data Modeling |
| Check method | manual_review |

**Rationale.** A separate read model adds synchronisation and eventual consistency.

**Exceptions.** none

**Engine notes.** CQRS is explicitly unsuited to simple CRUD. Azure guidance recommends outbox and idempotent consumers with it.

**Evidence.** PERF-56; ARCH-07; research/design_decision_matrix.md §17, SM-10

**Check.** A proposed read store states the scale or storage need.

### SCL-014: Storage engine family choice

**Statement.** An LSM engine MAY be chosen for write-heavy workloads, with B-tree remaining the default for read latency.

| Field | Value |
|---|---|
| Level | OPTIONAL |
| Scope | OLTP |
| Applies when | A storage engine family is being selected. |
| Status | active |
| Decision ref | null |
| Evidence strength | single_vendor |
| Lifecycle stage | Data Modeling |
| Check method | manual_review |

**Rationale.** LSM engines trade write, space and read amplification according to compaction style.

**Exceptions.** none

**Engine notes.** RocksDB documents compaction trade-offs. DDIA chapter-level comparisons were not verified and are not used.

**Evidence.** PERF-42; research/design_decision_matrix.md §17, SM-11

**Check.** The engine family choice records the workload and compaction trade-off.

### SCL-015: Prefer evolving the incumbent engine

**Statement.** Teams SHOULD evolve the incumbent engine before rewriting to a new one.

| Field | Value |
|---|---|
| Level | RECOMMENDED |
| Scope | OLTP |
| Applies when | An engine replacement is proposed. |
| Status | provisional |
| Decision ref | null |
| Evidence strength | case_study |
| Lifecycle stage | Data Modeling |
| Check method | manual_review |

**Rationale.** Teams in the sources repeatedly rejected rewrites as riskier than evolving what they ran.

**Exceptions.** A documented limit that the incumbent cannot meet, approved by the framework exception approver.

**Engine notes.** Uber's switch from PostgreSQL to MySQL is contested and must not be generalised (C-66).

**Evidence.** CASE-01; CASE-02; CASE-04; CASE-07; CASE-09; research/design_decision_matrix.md §17, SM-12; research/architecture_comparison.md §Part C, C-66

**Check.** A replacement proposal records why the incumbent cannot meet the need.

### SCL-016: Stay within SLA-conditioned cloud bounds

**Statement.** Managed database deployments that depend on the vendor SLA MUST follow the operational guidelines that condition it.

| Field | Value |
|---|---|
| Level | MANDATORY |
| Scope | OLTP |
| Applies when | The instance runs on RDS, Aurora or Cloud SQL and relies on SLA coverage. |
| Status | active |
| Decision ref | null |
| Evidence strength | multi_vendor |
| Lifecycle stage | Monitoring |
| Check method | runtime_monitor |

**Rationale.** Breaching the guidelines removes SLA coverage for the instance.

**Exceptions.** Accepted loss of SLA coverage, approved by the framework exception approver.

**Engine notes.** AWS states that the RDS SLA requires following its guidelines; Cloud SQL states the same for its SLA. The 10,000-table figure is shared by RDS and Cloud SQL. Guidelines change, so use the current vendor pages.

**Evidence.** CLOUD-09; CLOUD-14; research/design_decision_matrix.md §17, SM-13; research/official_documentation.md §15

**Check.** Instance metrics and table counts are compared with the current vendor guidelines.

### SCL-017: Respect published hard limits

**Statement.** Schemas MUST stay within the engine's published hard limits for keys, indexes, partitions and identifiers.

| Field | Value |
|---|---|
| Level | MANDATORY |
| Scope | all |
| Applies when | always |
| Status | active |
| Decision ref | null |
| Evidence strength | multi_vendor |
| Lifecycle stage | Schema Design |
| Check method | schema_lint |

**Rationale.** Exceeding an engine-enforced limit fails at creation or at run time.

**Exceptions.** none

**Engine notes.** Limits vary by engine and are listed per platform in the official documentation review: for example MongoDB allows 64 indexes per collection, SQL Server allows 999 nonclustered indexes, and MySQL allows 8192 partitions.

**Evidence.** MSOM-01; MSOM-02; PERF-03; PGMY-16; research/official_documentation.md §15; research/official_documentation.md §14

**Check.** Schema objects are checked against the published limits for the target engine.

### SCL-018: Bound partition size in wide-column stores

**Statement.** Partition keys in wide-column stores SHOULD be designed to bound partition size.

| Field | Value |
|---|---|
| Level | RECOMMENDED |
| Scope | OLTP |
| Applies when | The store is wide-column. |
| Status | provisional |
| Decision ref | null |
| Evidence strength | case_study |
| Lifecycle stage | Schema Design |
| Check method | manual_review |

**Rationale.** Unbounded partitions are what bucketing is meant to prevent, and deletes are writes that leave tombstones.

**Exceptions.** none

**Engine notes.** Discord's bucketing is the basis. Evidence is a single company.

**Evidence.** CASE-15; CASE-16; research/design_decision_matrix.md §17, SM-14

**Check.** The partition key design states how partition size is bounded.

### SCL-019: Enforce domain boundaries before moving data

**Statement.** Schema domain boundaries SHOULD be enforced by linters or experiments before data is physically moved.

| Field | Value |
|---|---|
| Level | RECOMMENDED |
| Scope | OLTP |
| Applies when | Tables are to be split across clusters or services. |
| Status | provisional |
| Decision ref | null |
| Evidence strength | case_study |
| Lifecycle stage | Data Modeling |
| Check method | manual_review |

**Rationale.** Moving data while cross-domain queries still exist breaks those queries.

**Exceptions.** none

**Engine notes.** One organization's practice (GitHub).

**Evidence.** CASE-04; research/design_decision_matrix.md §17, SM-15

**Check.** Cross-domain joins and transactions are detected and cleared before the move.

## Decisions needing owner approval

Answered by the owner on 2026-11-08: all defaults accepted. See `../DECISIONS_TO_APPROVE.md` for the decision log, and each rule's decision_ref for its decision number. Questions and alternatives are kept for the record.

### IDX-023

**Question.** What key type should generated primary keys default to on single-node OLTP engines? This is a judgment: no independent benchmark exists (B9).

**Proposed default.** 64-bit integer identity by default; time-ordered 128-bit identifier in native binary form only where global or client-generated uniqueness is required.

| Alternative | Consequence |
|---|---|
| Default as proposed | Smallest keys on the evidence available, with a stated path for distributed identifiers. Integer keys cannot be generated by clients. |
| Time-ordered 128-bit identifier everywhere | Uniform and client-generatable, with wider keys, more secondary index cost on clustered engines, and creation time exposed. |
| Random UUIDv4 everywhere | No time leakage and simple generation, with index scatter on B-tree engines reported by the practitioner tests, which agree on direction but not magnitude. |
| Choose per system with no framework default | Maximum fit, with inconsistency and repeated debate. |

### IDX-024

**Question.** What key type should warehouse and lakehouse dimensions default to? This is a judgment, and C-11 is unresolved.

**Proposed default.** Integer surrogate keys for dimensional models; hash or string keys recorded where parallel, lookup-free loading is the priority.

| Alternative | Consequence |
|---|---|
| Integer default | Favours join and clustering performance; needs key lookups during load. |
| Hash keys default | Parallel, idempotent loads without lookups; wider keys and weaker clustering on some platforms. |
| String keys, dbt style | Simple in ELT; the same clustering concerns on Snowflake, which considers only the first five VARCHAR bytes. |
| Method decides, no framework default | Fits Kimball and Data Vault separately; cross-model joins need conversion. |

### TXN-010

**Question.** How should idempotency replay and retention work? (C-65)

**Proposed default.** Replay the saved outcome and retain records at least 24 hours.

| Alternative | Consequence |
|---|---|
| Replay saved outcome | Predictable for clients; a saved server error is replayed until the key expires. |
| Retry to completion, as Stripe API v2 does | Better completion; needs a server-side completer and more care for partial work. |
| Longer retention, about 72 hours | Covers longer client retries; more storage and reaper work. |

### TXN-018

**Question.** Which mechanism should issue document numbers where continuity is required, given unresolved gap rules (C-41, C-79)? Requires legal review.

**Proposed default.** A locked per-series counter inside the issuing transaction, applying the strictest rule per legal entity.

| Alternative | Consequence |
|---|---|
| Locked per-series counter | Meets continuity wording; serializes issuers within each series. |
| Sequence or identity with documented gaps | High throughput; cannot meet continuity wording alone and is only defensible where gaps are tolerated. |
| Per-jurisdiction choice | Matches each rule; more configuration and legal upkeep. |

### TXN-023

**Question.** Which vocabulary should design documents use for distributed trade-offs? (C-63)

**Proposed default.** PACELC terms for partition and normal operation.

| Alternative | Consequence |
|---|---|
| PACELC | Covers normal-operation latency; the 2012 system classifications must not be reused. |
| Brewer's partition-mode framing | Strong on managing partitions; says less about normal operation. |
| Kleppmann's delay-sensitivity framework | More precise; less familiar to most teams. |

### SCL-008

**Question.** Should teams adopt or build a sharding layer? (X22, C-71)

**Proposed default.** Adopt an existing layer unless a recorded reason requires building one.

| Alternative | Consequence |
|---|---|
| Adopt (Vitess, Citus or similar) | Faster start and shared maintenance; limited by the layer's constraints. |
| Build | Full control, as Figma and Notion chose; lasting maintenance cost. |
| Consensus-based distributed SQL | No shard layer to run; a different engine and migration risk. |
