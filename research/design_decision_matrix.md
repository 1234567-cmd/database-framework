# Design Decision Matrix

Status: evidence inputs for later standards. These are not final rules and not schemas. Each row records a decision the framework will have to make, the options seen in the sources, and how strong the support is. The companion analysis is `research/architecture_comparison.md`; its Part C register is cited here as C-nn.

## How to read the tables

Citations are catalog IDs from `research/resource_catalog.json` or `[Title](URL)` from the notes. `CORRECTIONS.md`, notes 18 to 23 and the verification results in note 22 are applied, and web-page wording is paraphrased with no quotation marks. Some IDs used in the notes are merged in the catalog and are cited here under the merged ID: THIN-01 is GOV-27, THIN-17 is OPS-16, THIN-19 is OPS-13, ENG-03 is PGMY-16, ENG-04 is PGMY-13, BENCH-09 is DWM-22.

| Column | Meaning |
|---|---|
| ID | Stable decision reference for later standards work. |
| Question | The decision to be made. |
| Options | Choices documented in the notes. Option names are descriptive and prescribe no schema. |
| When each applies | Conditions from the sources. |
| Trade-offs | Cost of each option. |
| Class | MANDATORY principle, RECOMMENDED, or OPTIONAL pattern (defined below). |
| Scope | OLTP, OLAP, DW (data warehouse), lakehouse, streaming, or general. These are distinct workloads. |
| Evidence | Standard, multi-vendor, single vendor, case study or inference. The strongest applicable label is listed first. |
| Sources | Catalog IDs or links. |

| Class | Rule used in this file |
|---|---|
| MANDATORY | Requires an authoritative source: law, a standards body, a foundational paper, or official documentation from two or more independent vendors. The scope of the obligation is stated. A statute binds only in its own jurisdiction and population. Rules that are obligations only inside a method or engine say so. |
| RECOMMENDED | Advised by sources, or a method owner's strong guidance, with legitimate exceptions. Includes items the notes labelled MANDATORY where no authoritative source supports that label. |
| OPTIONAL | A context-dependent pattern. Choosing it does not make it mandatory. |

| Evidence | Meaning |
|---|---|
| Standard | Law, regulation, standards-body text, or a foundational peer-reviewed paper. |
| Multi-vendor | Official documentation from two or more independent vendors or projects. |
| Single vendor | One vendor's documentation or one project's guidance. |
| Case study | Engineering reports, incident post-mortems, surveys, and practitioner or vendor benchmarks. Benchmarks are never treated as independent evidence and none was reproduced in this research (note 23). |
| Inference | This author's synthesis; marked [INFERENCE]. Not stated by the cited source in that form. |

Where a row's classification departs from a topic note's label, the reason is in the area's Notes line.

[WF] marks a figure or statement read only through a summarising fetch tool, so it is not confirmed against raw page text. A class of No classification means no source supports a position.

---

## 1. Architecture principles

Scope: decisions that shape the system before any table is designed.

| ID | Question | Options | When each applies | Trade-offs | Class | Scope | Evidence | Sources |
|---|---|---|---|---|---|---|---|---|
| AP-1 | How is the data store chosen? | Relational; document or key-value; columnar warehouse; lake or lakehouse; event log | By access pattern, consistency need, scale, read and write ratio, operational maturity | Fit against the operational cost of more systems; Azure warns of premature fragmentation | RECOMMENDED | General | Multi-vendor, standard | CLOUD-01, CLOUD-17, PERF-38 |
| AP-2 | Do OLTP and analytics share a system? | Separate stores; row store plus columnar replica (HTAP); replica for reports | Separate as default; HTAP for operational analytics; replica only if reports do not feed decisions | Latency and pipeline cost against load interference and freshness | RECOMMENDED | OLTP, OLAP | Standard, multi-vendor | PERF-38, PERF-39, CLOUD-16, PERF-02, PERF-49, BENCH-14, BENCH-13 |
| AP-3 | Where is integrity enforced? | Engine constraints; pipeline tests; application only | Engine where it can enforce; pipeline where platforms cannot; application alone only under documented infrastructure limits | Write cost against silent corruption | MANDATORY (engine for OLTP system of record) | OLTP | Multi-vendor | MSOM-08, PGMY-01, MSOM-02, DES-18 |
| AP-4 | Which integrity must analytical platforms substitute for? | Enforced NOT NULL and CHECK; informational PK, FK, UNIQUE; tests and pipelines | Snowflake standard tables and Databricks enforce only the first; Redshift enforces NOT NULL and treats PK, FK and UNIQUE as informational | Load speed against guarantees | MANDATORY (know what is enforced) | DW, lakehouse | Multi-vendor | LAKE-02, LAKE-09, DQ-03, ENG-23 |
| AP-5 | What consistency posture does the system of record take? | Strong, single-writer or consensus; eventual with compensation | Strong where invariants need coordination; [INFERENCE] uniqueness, balances, numbering all do | Latency and availability against simplicity of correctness | RECOMMENDED | OLTP | Standard, inference | TXN-14, TXN-15, TXN-20 |
| AP-6 | What is the unit of schema ownership? | Bounded context; team; application | DDD names database schemas as a context boundary | Clear ownership against more integration work | RECOMMENDED | OLTP | Single vendor, inference | ARCH-01, ARCH-02 |
| AP-7 | How are service boundaries reflected in storage? | Private tables; schema per service; server per service | Start with lower-overhead options; server split for throughput, storage-type or deployment need | Isolation against cross-boundary ACID and joins | OPTIONAL | OLTP | Multi-vendor | ARCH-04, ARCH-05 |
| AP-8 | How many analytical layers? | Single presentation layer; integration plus marts; medallion hops | One layer for simple sources; add layers for audit or multi-source reconciliation | Traceability against latency and cost | OPTIONAL | DW, lakehouse | Multi-vendor | LAKE-01, LAKE-06, DWM-14, CLOUD-21 |
| AP-9 | Who owns analytical data? | Central team; domain-owned products (Mesh); hybrid | Hybrid is what adopters converge on | Autonomy against integration cost | OPTIONAL | DW, lakehouse | Case study, single vendor | ARCH-14, ARCH-15, ARCH-16, ARCH-19, ARCH-20 |
| AP-10 | How portable must designs be? | Standard SQL where it exists; vendor dialect | Standard syntax for portability, but adoption of SQL:2011 features was slow | Portability against engine capability | RECOMMENDED | General | Standard | GOV-05, GOV-06 |

Notes: AP-3 is scoped to OLTP systems of record. [INFERENCE] The framework should state enforcement as a matrix by workload rather than a single rule. HTAP isolation in AP-2 is the best-covered benchmark topic, but BENCH-14 anonymizes commercial systems, so it supports claims about architecture and not named products, and BENCH-13 is a vendor measuring its own product. BENCH-15 records no numbers.

## 2. Logical and physical modeling

Scope: the process and physical mapping choices.

| ID | Question | Options | When each applies | Trade-offs | Class | Scope | Evidence | Sources |
|---|---|---|---|---|---|---|---|---|
| LP-1 | Are logical and physical design separated? | Conceptual to logical to physical; physical only | Separation aligns with ANSI/SPARC and IDEF1X objectives | Modeling effort against later change cost | RECOMMENDED | General | Standard | GOV-25, GOV-27, DES-01 |
| LP-2 | Entity-first or access-pattern-first? | Normalized entities; access-pattern modeling | Entity-first on relational; access-pattern on DynamoDB, Cosmos DB, MongoDB, Spanner keys | Query flexibility against predictable performance | RECOMMENDED per paradigm | OLTP | Multi-vendor | CLOUD-06, CLOUD-20, MSOM-15, CLOUD-11 |
| LP-3 | How are physical departures from the logical model recorded? | Documented with reason; undocumented | Kent's caveat allows stopping short when performance justifies it; Codd requires consistency statements for redundancy | Governance effort against invisible redundancy | RECOMMENDED | OLTP, DW | Standard, inference | DES-02, DES-01 |
| LP-4 | How is inheritance mapped? | Single table; class table with shared key; concrete table | Single table for few differing columns; class table when subtype NOT NULL and FK constraints matter; concrete table where no shared FK target is needed. Hibernate favours joined tables for constraints, EF Core defaults to one table and warns on joined-table performance (C-85) | One table loses NOT NULL on subtype columns; joined tables cost joins; concrete tables lose FKs to the supertype. Native exclusive-arc enforcement was not covered | OPTIONAL | OLTP | Multi-vendor (ORM mapping documentation), single vendor (Fowler); no engine-neutral benchmark found | DES-14, GOV-27, THIN-03, THIN-04, THIN-05 |
| LP-5 | Should PostgreSQL table inheritance be used for subtypes? | Use; avoid | Avoid per wiki | Single-source guidance | RECOMMENDED | OLTP (PostgreSQL) | Single vendor | PGMY-10 |
| LP-6 | How are hierarchies stored? | Adjacency list; materialized path; SQL Server hierarchyid | Adjacency for FK-enforced integrity; path for indexed subtree queries (`ltree`); hierarchyid per Microsoft is faster for subtree queries and slower for moving non-leaf nodes, with no figures published | Query complexity against write cost. hierarchyid does not enforce relationships as an FK does. Recursive queries loop on cycles unless detected. Closure table and nested set have no opened source, and neither can be attributed to Karwin (note 22) | OPTIONAL | OLTP | Single vendor, inference | DES-13, [ltree](https://www.postgresql.org/docs/current/ltree.html), THIN-07 |
| LP-7 | How are variable attributes stored? | Columns; JSON documents; EAV | Columns for keys, money and filters; JSON for sparse or external attributes; EAV listed as an antipattern | Flexibility against indexing and constraints | RECOMMENDED (columns for core data) | OLTP | Multi-vendor | PGMY-04, MSOM-15, DES-13, DES-20 |
| LP-8 | Large binary objects: in database or external? | In database; object store plus reference | By size and lifecycle; Karwin's listing warns against assuming external storage | Transactional integrity and backup scope against row size | OPTIONAL | OLTP | Inference, single vendor | DES-13, DES-20 |
| LP-9 | Which physical levers are part of the design? | Distribution, sort, partition and clustering keys | MPP warehouses; cloud warehouses replace B-trees with these | Scan and join cost against rebuild cost | RECOMMENDED | OLAP, DW | Multi-vendor | CLOUD-08, CLOUD-13, LAKE-10, [Synapse tables overview](https://learn.microsoft.com/en-us/azure/synapse-analytics/sql-data-warehouse/sql-data-warehouse-tables-overview) |
| LP-10 | Is the physical layout mutable? | Fixed partitions; mutable clustering or hidden partitions | Mutable on Databricks liquid clustering and Iceberg | Simpler change against platform dependence | RECOMMENDED per platform | Lakehouse | Multi-vendor | LAKE-03, PIPE-10 |
| LP-11 | Is the OLTP model exposed to consumers? | Direct access; published interface | [INFERENCE] Internal schemas should not be the shared surface | Coupling against an extra projection | RECOMMENDED | OLTP, DW | Single vendor, inference | ARCH-14, ARCH-15, PIPE-20 |

Notes: Karwin is cited for publisher-listed antipattern names only; remedies were not read (`CORRECTIONS.md`).

## 3. ER design

Scope: entities, relationships and how they map to keys.

| ID | Question | Options | When each applies | Trade-offs | Class | Scope | Evidence | Sources |
|---|---|---|---|---|---|---|---|---|
| ER-1 | Is cardinality and optionality explicit before keys are chosen? | Explicit; implied | Chen's design procedure decides keys after relationships | Early effort against late rework | RECOMMENDED | General | Standard | DES-03, GOV-26, GOV-27 |
| ER-2 | Which notation? | Chen; IDEF1X; crow's foot; UML | Any, consistently | IDEF1X was a federal mandate 1994 to 2008 and is withdrawn; the withdrawal date rests on Wikipedia. Crow's foot is attributed to Everest 1976 by two opened pages; the 1976 paper is unread | OPTIONAL | General | Standard | GOV-26, GOV-27, GOV-28, THIN-02 |
| ER-3 | How are many-to-many relationships realized? | Association table | Always in relational stores; FIPS 184 requires refinement before the key-based phase. Whether the join row needs its own identity is not settled by these sources | None significant | MANDATORY (relational) | OLTP, DW | Standard | DES-03, DES-14, GOV-27, THIN-06 |
| ER-4 | Primary key of an association table? | Composite of the two FKs; surrogate | Composite unless the row is referenced or has its own lifecycle | Index width against FK simplicity | RECOMMENDED | OLTP | Inference, single vendor | DES-13, DES-20, DES-03 |
| ER-5 | Weak entities: identifying or non-identifying relationship? | Parent key in child PK; surrogate plus UNIQUE (parent, local key) | Identifying in Chen and IDEF1X; surrogate in ORM-centric schemas ([INFERENCE]) | Key width against flexibility | RECOMMENDED | OLTP | Standard, inference | DES-03, GOV-27 |
| ER-6 | Can one column reference several parents? | Polymorphic type and id pair; supertype table; one FK per target | Listed as an antipattern because no FK can be declared | Flexibility against integrity | RECOMMENDED (avoid the pair) | OLTP | Single vendor, inference | DES-13, DES-14 |
| ER-7 | Supertype and subtype? | See LP-4 | Category relationships in IDEF1X; complete and incomplete category clusters are defined in FIPS 184 | See LP-4 | OPTIONAL | OLTP | Standard, multi-vendor | GOV-27, DES-14, THIN-03, THIN-04, THIN-05 |
| ER-8 | How are references across aggregates or contexts stored? | FK to root; bare identifier | Identifier across contexts; [INFERENCE] no FK across a context boundary | Decoupling against integrity | RECOMMENDED | OLTP | Single vendor, inference | ARCH-01, ARCH-03 |
| ER-9 | Are code lists modeled as reference tables? | Table with effective dating; embedded literals | Tables when codes are amended over time, as ISO 4217 lists are | Join cost against change safety | RECOMMENDED | General | Standard, inference | GOV-20, DES-11 |
| ER-10 | Is the subtype discriminator required? | Required for complete clusters; optional | FIPS 184 forbids an optional discriminator on a complete cluster, inside IDEF1X only | Modeling discipline | OPTIONAL; binds only inside IDEF1X conformance, and the standard is withdrawn | OLTP | Standard | GOV-27 |

Notes: ER-3 follows from relational representation of m:n relationships in Chen and is implemented by every relational engine. ER-6 is RECOMMENDED because the antipattern is a publisher-listed name; note 10's MANDATORY label is not retained. Subtype evidence in LP-4 and ER-7 is ORM mapping documentation; Simsion and Witt and similar books remain unread.

## 4. Normalization

Scope: how far to normalize and when to stop.

| ID | Question | Options | When each applies | Trade-offs | Class | Scope | Evidence | Sources |
|---|---|---|---|---|---|---|---|---|
| NF-1 | Are multi-valued columns allowed in relational base tables? | Atomic columns (1NF); repeating groups or delimited lists | 1NF in relational base tables. Nested data is a documented exception on BigQuery and document stores | Joins against unindexable data | MANDATORY (relational system of record) | OLTP | Standard | DES-01, DES-02, DES-13 |
| NF-2 | Target normal form? | 3NF or BCNF; lower | 3NF default where non-key fields are updated | Fewer anomalies against joins | RECOMMENDED | OLTP | Standard, multi-vendor | DES-02, CLOUD-16, MSOM-14, PERF-17 |
| NF-3 | When to check 4NF and 5NF? | Check; skip | Tables holding two or more independent multivalued facts | Analysis cost against redundancy | RECOMMENDED | OLTP | Standard | DES-02, LIT-04, LIT-05 |
| NF-4 | When may a read shape be denormalized? | Controlled read model; ad hoc redundancy | Read-dominant, one controlled write path, dependency documented | Read speed against consistency | OPTIONAL | OLAP, DW, lakehouse | Standard, inference | DES-02, DES-01, DWM-01 |
| NF-5 | Denormalize OLTP base tables for speed? | Keep normalized and add read models; denormalize | Prefer a read model or columnar replica | Consistency against complexity | RECOMMENDED (keep normalized) | OLTP | Standard, multi-vendor | PERF-38, PERF-56, PERF-02 |
| NF-6 | DW integration shape? | 3NF EDW; Data Vault; none | See RP-2 | See RP-2 | OPTIONAL | DW | Standard, single vendor | DWM-14, DWM-08 |
| NF-7 | Star or snowflake in presentation? | Star; snowflake | Oracle advises star unless there is a clear reason | Fewer joins against redundancy | RECOMMENDED | OLAP, DW | Multi-vendor | DWM-14, DWM-01, CLOUD-21 |
| NF-8 | 6NF? | Anchor Modeling; other | Highly volatile, sparse, heavily historized data | Table count and tooling | OPTIONAL | DW | Single vendor (author paper) | DWM-16 |
| NF-9 | Document stores: embed or reference? | Embed; reference | Embed what is read together, within limits | Read speed against unbounded arrays and bloated documents | RECOMMENDED | OLTP (document) | Single vendor | MSOM-15 |
| NF-10 | Is redundancy maintained in application code? | Generated columns; ETL or refresh; application | Prefer a single controlled write path | Coupling | RECOMMENDED | General | Inference | DES-01, DES-02 |

Notes: Note 10 labels 3NF MANDATORY for OLTP. It is RECOMMENDED here because Kent explicitly allows stopping short for performance. NF-1 excludes analytical nested types and document stores, which the sources document as legitimate.

## 5. Relational integrity

Scope: keys and constraints.

| ID | Question | Options | When each applies | Trade-offs | Class | Scope | Evidence | Sources |
|---|---|---|---|---|---|---|---|---|
| RI-1 | Does every base table have a primary key? | Declared PK; none | System-of-record tables; required for logical replication of updates and deletes | None material | MANDATORY | OLTP | Standard, multi-vendor | DES-01, PGMY-01, PGMY-12, MSOM-02, TEN-28 |
| RI-2 | Foreign keys enforced in the database? | Enforce; application only | Enforce on unsharded OLTP; where unavailable keep FK columns, indexes, orphan audits, documented risk | Write and DDL cost against orphans | MANDATORY (non-sharded OLTP) | OLTP | Multi-vendor | PGMY-01, MSOM-02, MSOM-08, DES-18, DES-17 |
| RI-3 | Default for ON DELETE? | CASCADE; RESTRICT or NO ACTION; SET NULL | [INFERENCE] CASCADE for strict composition, RESTRICT otherwise, SET NULL for optional links. Sources disagree (C-09) | Automatic cleanup against accidental mass deletion | RECOMMENDED: declare one per FK; default unresolved | OLTP | Case study, single vendor, inference | DES-18, DES-17, DES-22 |
| RI-4 | Deferrable constraints? | Deferrable; immediate | PostgreSQL for cycles and bulk insert; Oracle supports deferrable constraints but they cannot be altered in place; MySQL has no deferral; the SQL Server CREATE TABLE grammar shows no deferral syntax [WF] | Portability | OPTIONAL | OLTP | Multi-vendor | PGMY-01, PGMY-14, MSOM-08, ENG-10, ENG-15 |
| RI-5 | NOT NULL by default? | NOT NULL; nullable with documented meaning | NOT NULL unless absence has a defined meaning | Migration effort against three-valued logic | RECOMMENDED | General | Multi-vendor | PGMY-01, PERF-17 |
| RI-6 | Do CHECK rules hold for NULL? | CHECK plus NOT NULL; CHECK alone | Pair when the rule must always hold | None | MANDATORY (semantics) | General | Multi-vendor | PGMY-01, PGMY-15 |
| RI-7 | Uniqueness with nullable columns? | Do not assume NULL handling; NULLS NOT DISTINCT; filtered unique index; avoid nullable unique columns | Behaviour differs by engine (C-83): PostgreSQL treats NULLs as distinct by default with an option to change; MySQL permits many NULLs [WF]; SQL Server allows one NULL per column in a UNIQUE constraint [WF]; Oracle has a composite-specific rule [WF]. A SQL Server unique filtered index is an inference from the docs, not a documented example | No portable rule can assume one behaviour | RECOMMENDED (state per engine; no portable default) | OLTP | Multi-vendor | PGMY-01, ENG-05, ENG-10, ENG-15 |
| RI-8 | No-overlap rules? | EXCLUDE; WITHOUT OVERLAPS; application | Engines supporting them | Portability | RECOMMENDED where supported | OLTP | Standard, single vendor | PGMY-01, GOV-06, PERF-16 |
| RI-9 | Cross-table rules? | Trigger; constraint; application | CHECK cannot safely reference other rows | Complexity | OPTIONAL | OLTP | Single vendor | PGMY-01 |
| RI-10 | Sentinel values in place of NULL? | NULL with meaning; explicit dimension rows; magic literals | Dimension default rows in DW; avoid magic literals | Correctness of aggregates | RECOMMENDED | DW | Single vendor (method owner), inference | DWM-01, DWM-02 |
| RI-11 | Key uniqueness in the warehouse? | Test `unique` and `not_null`; pipeline MERGE keys; rely on declaration | Declaration alone does not enforce on Snowflake standard tables or Databricks | Test cost against duplicates | RECOMMENDED | DW, lakehouse | Multi-vendor | LAKE-19, DQ-03, LAKE-02, LAKE-09, ENG-23 |
| RI-12 | FK enforcement in DW? | RELY or non-enforced; ETL lookup | ETL-controlled loads; Databricks defaults to NORELY; Redshift's planner assumes keys are valid and advises against declaring doubtful keys | RELY is unsafe if data does not comply | RECOMMENDED | DW | Multi-vendor | MSOM-12, LAKE-09, DES-12, ENG-23, ENG-29 |
| RI-13 | Natural or surrogate key? | Surrogate plus UNIQUE natural; natural; surrogate only | Contested (C-12) | Stability against meaning | OPTIONAL | OLTP | Inference | LIT-10, DES-12, DES-20, DES-03 |
| RI-14 | Reuse or fill key gaps? | Never reuse; fill | Listed as an antipattern | None material | RECOMMENDED (do not fill) | OLTP | Single vendor | DES-13 |

Notes: RI-1 elevates vendor strong wording to MANDATORY on the basis of Codd and replication requirements; the elevation is this author's. The mandate in RI-2 is scoped because sharding and shadow-table DDL are documented limits (C-08). FK cost remains a judgment: no independent evidence at scale and no MySQL measurement were found. BENCH-08 is one practitioner test at small scale [WF], and its concurrent result is inside its own error.

## 6. Naming

Scope: identifiers. No engine vendor publishes a naming standard for table or column semantics (notes 01 and 02); Oracle publishes general naming guidance.

| ID | Question | Options | When each applies | Trade-offs | Class | Scope | Evidence | Sources |
|---|---|---|---|---|---|---|---|---|
| NM-1 | Is there a documented convention? | Documented; informal | ISO/IEC 11179-5 scope is principles for naming conventions; a 2004 committee draft requires scope and authority to be documented for registry conventions only | None material | RECOMMENDED | General | Standard (scope), committee draft | GOV-08, DES-20, THIN-08 |
| NM-2 | Case and separators? | lowercase snake_case; mixed case | Vendors converge on lowercase for portability, from different causes | Readability | RECOMMENDED | General | Multi-vendor | PGMY-10, PGMY-17, LAKE-16, DES-20, DES-22 |
| NM-3 | Length limits? | Engine limit; portable ceiling | 63 bytes PostgreSQL; 64 characters MySQL; 128 SQL Server; 128 bytes Oracle, 30 below COMPATIBLE 12.2; 255 characters Snowflake and Databricks Unity Catalog object names | Descriptiveness against portability | MANDATORY (engine limits) | General | Multi-vendor | PGMY-09, PGMY-17, MSOM-10, THIN-15, ENG-20, ENG-30 |
| NM-4 | Quoted identifiers? | Avoid; allow | Avoid; quoting and case rules differ by engine | None material | RECOMMENDED | General | Multi-vendor | PGMY-09, PGMY-17, MSOM-10, THIN-15, ENG-20 |
| NM-5 | Reserved prefixes and words? | Forbid | pg_ in PostgreSQL; SYS_ and ORA_ on Oracle; reserved words | None material | MANDATORY (engine rules) | General | Multi-vendor | PGMY-09, MSOM-10, THIN-15 |
| NM-6 | Singular or plural table names? | Singular; plural | Primary sources split: Rails and GitLab examples plural; Django default and Prisma models singular, while Prisma calls plural snake_case tables common; EF Core follows DbSet naming. Linters make it configurable. No source reports an outcome difference (C-26) | Style | OPTIONAL | General | Multi-vendor (conflicting) | DES-22, LAKE-16, DES-20, DES-18, THIN-10, THIN-11, THIN-12, THIN-13, THIN-14, THIN-16, THIN-24 |
| NM-7 | Key column names? | `id`; `<object>_id` | Prefer `<object>_id` where joined across models; ORM shops may keep `id` | Convention conflict with ORMs | RECOMMENDED | General | Multi-vendor | LAKE-16, DES-20 |
| NM-8 | Semantic suffixes and prefixes? | `_at`, `_date`, `is_`, `has_`; none | Strongest in analytical layers | Style | RECOMMENDED | General | Multi-vendor | LAKE-16, DES-20, DES-22 |
| NM-9 | Constraint and index names? | Typed prefixes with table and columns; system generated | Explicit names; generated names vary per environment | Length pressure | RECOMMENDED | General | Single vendor (typed-prefix pattern), multi-vendor (generated names vary), inference | DES-19, DES-18, PGMY-01, PGMY-14, THIN-12, THIN-14 |
| NM-10 | Object class, property and representation term pattern? | Adopt; other | 2004 committee draft annex examples use one object class, property and representation term; the annex is informative. Published 2005 and 2015 editions are unread | Length | OPTIONAL | General | Committee draft (informative annex), inference | GOV-08, THIN-08 |
| NM-11 | Which vocabulary do names use? | Ubiquitous language of the context; global dictionary | Context language; different contexts may legitimately differ | Global search against model fit | RECOMMENDED | OLTP | Single vendor, inference | ARCH-01, ARCH-02 |
| NM-12 | Can a dropped name be reused? | Never for a different meaning; reuse | [INFERENCE] Iceberg forbids ID reuse; name-tracked systems risk confusion | None material | RECOMMENDED | Lakehouse, general | Single vendor, inference | PIPE-09, PIPE-10 |
| NM-13 | Is one name used for one attribute across tables? | Same name; per-table naming | Oracle guidelines advise the same name for the same entity or attribute, and full, descriptive names | None material | RECOMMENDED | General | Single vendor | THIN-15 |

Notes: Hard limits are classed as MANDATORY because the engines reject or misbehave beyond them. Style rules are never MANDATORY; only consistency is. The singular-noun example in the 11179-5 draft is informative and concerns registry data elements, so it is not evidence for singular table names. GitLab's constraint-prefix rules bind inside GitLab only. No Zalando database naming guideline was found.

## 7. Data types and precision

Scope: representation of values.

| ID | Question | Options | When each applies | Trade-offs | Class | Scope | Evidence | Sources |
|---|---|---|---|---|---|---|---|---|
| DT-1 | Money representation? | Exact decimal; integer minor units; float | Exact decimal or minor units always | Arithmetic speed against correctness. A dbt example casts to float (C-27) | MANDATORY | General | Multi-vendor | PGMY-02, MSOM-03, MSOM-10, MSOM-18, DES-22 |
| DT-2 | Decimal scale? | Per ISO 4217 minor unit; fixed high scale | Data-driven because minor units change; [INFERENCE] scale of at least 4 for mixed currency (CLF and UYW use 4) | Storage against conversion error | RECOMMENDED | General | Standard, inference | GOV-20, DES-11 |
| DT-3 | Is a currency code stored with each amount? | Stored alongside; implicit | Multi-currency amounts; per-currency balancing in ledgers; ERP products keep transaction, entity and optional reporting amounts together (FN-13) | Column count | RECOMMENDED | OLTP, DW | Multi-vendor (ERP amount sets), single vendor, inference | PGMY-10, TEN-41, ERP-03, ERP-09, ERP-20 |
| DT-4 | Instant type? | UTC-normalized instant; local datetime; offset type; epoch type | PostgreSQL timestamptz, MySQL TIMESTAMP with 2038 limit, SQL Server datetime2 or datetimeoffset, MongoDB BSON Date in UTC | Convention against engine limits | RECOMMENDED | General | Multi-vendor | PGMY-03, PGMY-13, MSOM-03, PGMY-10, ENG-09, ENG-13 |
| DT-5 | Date or timestamp? | Calendar date; instant | Date only when no time semantics; half-open range filtering | Boundary errors | RECOMMENDED | General | Multi-vendor, inference | PGMY-03, GOV-06 |
| DT-6 | String sizing? | Unbounded text with CHECK; bounded varchar; char(n) | PostgreSQL unbounded; MySQL bounded (C-21). PostgreSQL wiki rejects char(n) | Engine-specific performance | RECOMMENDED per engine | OLTP | Multi-vendor | PGMY-10, PERF-17 |
| DT-7 | Character set on MySQL? | utf8mb4; utf8mb3 | utf8mb4 for new applications | None material | RECOMMENDED | OLTP (MySQL) | Single vendor | [utf8mb3 reference](https://dev.mysql.com/doc/refman/8.4/en/charset-unicode-utf8mb3.html) |
| DT-8 | Boolean? | Native boolean; tinyint on MySQL | Native where the engine has one | None material | RECOMMENDED | OLTP | Multi-vendor | DES-22, DES-20 |
| DT-9 | Enumerated values? | Reference table; CHECK on text; ENUM type | Reference table when set changes or carries attributes; ENUM for static sets (V5 in the companion) | PostgreSQL enums cannot remove values; MySQL ENUM pitfalls | RECOMMENDED | OLTP | Multi-vendor, single vendor | PGMY-10, DES-19, DES-13 |
| DT-10 | Numeric-looking identifiers? | String; integer | String; leading zeros matter, as ISO 4217 numeric 048 shows | [INFERENCE] for phone, postal, national IDs | RECOMMENDED | General | Standard (code list), inference | DES-11 |
| DT-11 | Width of generated integer keys? | 64-bit; 32-bit | 64-bit default; 32-bit for bounded lookups; check FK widths too | Storage against overflow | RECOMMENDED | OLTP | Case study, single vendor | [Buildkite incident](https://buildkitestatus.com/incidents/63zxhjsysszc), [Rails 5.1 Release Notes](https://guides.rubyonrails.org/5_1_release_notes.html), DES-22, PGMY-02 |
| DT-12 | UUID storage? | Native 16-byte; string | Native type or BINARY(16) | Storage and comparison speed | RECOMMENDED | OLTP | Single vendor, case study | DES-04, PERF-15, DES-15, BENCH-01, BENCH-05 |
| DT-13 | Semi-structured columns? | JSON type; flattened columns | JSON for sparse attributes; flatten what is filtered | Index and constraint limits | RECOMMENDED | OLTP, lakehouse | Multi-vendor | PGMY-04, MSOM-15, LAKE-01 |
| DT-14 | Declared decimal at analytical landing? | Declared DECIMAL; inferred | Spark inference defaults floats to double unless configured | Effort against silent loss | RECOMMENDED | Lakehouse, streaming | Single vendor, inference | PIPE-07 |
| DT-15 | Reference code standards? | ISO 3166, 4217, 639; proprietary | ISO lists free; ISO 3166 and 639 pages were unverified in research (GOV-19, GOV-22) | Dependence on maintenance agencies | RECOMMENDED | General | Standard, partly unverified | GOV-20, GOV-19 (unverified), GOV-22 (unverified) |
| DT-16 | Date exchange format? | ISO 8601 strings for interchange | Interchange only; not a storage type | None material | RECOMMENDED | General | Standard | GOV-21 |

Notes: The notes label UTC instants and currency columns MANDATORY in places. DT-3 and DT-4 are RECOMMENDED because vendors recommend rather than require them and the evidence for currency columns is narrow. Key-type performance remains a judgment: no peer-reviewed or vendor-neutral benchmark exists for UUIDv7, v4 or bigint on PostgreSQL, and no UUIDv7 benchmark exists for MySQL at all. BENCH-01 is raw-confirmed but one blog test. BENCH-02 to BENCH-06 are [WF] and practitioner or vendor-hosted. Rate precision is FN-19, not DT-2.

## 8. Indexing and performance

Scope: access paths, partitioning and query discipline.

| ID | Question | Options | When each applies | Trade-offs | Class | Scope | Evidence | Sources |
|---|---|---|---|---|---|---|---|---|
| IX-1 | What gets an index? | Query-driven; all columns | Index predicates and joins that matter; remove unused | Read speed against write and storage cost | RECOMMENDED | OLTP | Multi-vendor | MSOM-01, MSOM-09, MSOM-15, PERF-17, PGMY-05 |
| IX-2 | Composite column order? | Equality first and usage-driven; most selective first | Selectivity decides only among range columns. Most-selective-first is a documented myth | Prefix reuse | RECOMMENDED | OLTP | Multi-vendor, case study | PERF-34, PERF-06, PERF-18, MSOM-17 |
| IX-3 | Index foreign keys? | Index; skip | InnoDB automatic; PostgreSQL and Oracle advisable for joined FKs or deletable parents | Write cost against lock and scan cost | RECOMMENDED per engine | OLTP | Multi-vendor | PGMY-14, PGMY-01, PERF-24, MSOM-02 |
| IX-4 | Covering indexes? | INCLUDE or key columns; narrow indexes | Strong on SQL Server and InnoDB; conditional on PostgreSQL's visibility map | Index size | OPTIONAL | OLTP | Multi-vendor | MSOM-01, PGMY-12, PERF-07 |
| IX-5 | Partial and expression indexes? | Use; avoid | Excluding common values, subset uniqueness; not a partitioning substitute | Query must match | OPTIONAL | OLTP | Single vendor | PERF-08, PGMY-05 |
| IX-6 | Specialized index types? | GIN, GiST, SP-GiST, BRIN; hash | Multi-component values, geometry, correlated physical order | Maintenance | OPTIONAL | General | Single vendor | PGMY-05, PGMY-04 |
| IX-7 | Analytical access paths? | Columnstore; bitmap; partition and cluster | By platform (see LP-9) | DML cost | RECOMMENDED per platform | OLAP, DW | Multi-vendor | PERF-02, MSOM-12, CLOUD-13, LAKE-10 |
| IX-8 | When to partition? | Partition; no partition | Very large tables, retention, dominant filter; not for OLTP point queries | Planning cost against manageability | RECOMMENDED | OLTP, DW | Multi-vendor | PGMY-06, PERF-03, MSOM-11 |
| IX-9 | Partition key in unique keys? | Include; violate | Required on PostgreSQL and MySQL | Key width | MANDATORY (engine rule) | OLTP, OLAP | Multi-vendor | PGMY-06, PGMY-16 |
| IX-10 | Query discipline? | SARGable predicates, current statistics, EXPLAIN; ad hoc | Baseline for all relational workloads | Review effort | RECOMMENDED | General | Multi-vendor | PERF-13, PERF-23, PERF-17, PERF-36 |
| IX-11 | Optimizer hints? | Last resort with review; routine | PostgreSQL has none by design; the community position is from 2015 | Upgrade risk | RECOMMENDED (last resort) | OLTP (PostgreSQL) | Single vendor | PERF-55 |
| IX-12 | Select list? | Named columns; SELECT star | No vendor mandate; covering and columnar benefit | Maintainability | RECOMMENDED | General | Multi-vendor, inference | PERF-04, PERF-07, PERF-02 |
| IX-13 | Pagination? | Keyset; OFFSET | Keyset for deep pages | Implementation complexity | RECOMMENDED | OLTP | Single vendor | PERF-35 |
| IX-14 | N+1 access? | Joins in the database; per-row round trips | Avoid per-row fetching | ORM convenience | RECOMMENDED | OLTP | Single vendor | PERF-37 |

Notes: Note 10 labels FK indexing MANDATORY; IX-3 follows note 11, which shows it is engine-dependent and exempts rarely-joined append-only children.

## 9. Transactions

Scope: correctness under concurrency.

| ID | Question | Options | When each applies | Trade-offs | Class | Scope | Evidence | Sources |
|---|---|---|---|---|---|---|---|---|
| TX-1 | How is isolation specified? | Per transaction class, per engine and configuration; rely on default or name | Always specify; level names are not portable | Documentation effort | MANDATORY | OLTP | Standard, multi-vendor | TXN-03, TXN-10, TXN-11, PGMY-08, MSOM-06, ENG-19, ENG-21, ENG-22, ENG-24 |
| TX-2 | How are read-then-write invariants protected? | SERIALIZABLE with retry; explicit locks; declarative constraint | Credit limits, stock, cross-row balances | Throughput against anomalies | MANDATORY (choose one) | OLTP | Standard | TXN-03, TXN-04, PGMY-08 |
| TX-3 | Handling of serialization and deadlock failures? | Whole-transaction retry; surface error | Required where the engine aborts | Retry logic | MANDATORY | OLTP | Multi-vendor | PGMY-08, MSOM-18, [SQL Server deadlocks guide](https://learn.microsoft.com/en-us/sql/relational-databases/sql-server-deadlocks-guide) |
| TX-4 | What bounds a transaction? | Aggregate; multi-aggregate | DDD: do not cross aggregates; MongoDB prefers single-document atomicity | Eventual consistency across | RECOMMENDED | OLTP | Multi-vendor | ARCH-02, ARCH-03, MSOM-18 |
| TX-5 | Long or conversational transactions? | Short; held across user interaction | Keep short; PostgreSQL offers idle-in-transaction timeouts; MongoDB imposes a 60 s limit | Complexity | RECOMMENDED | OLTP | Multi-vendor | PGMY-08, MSOM-18 |
| TX-6 | Conflict control across system transactions? | Optimistic version column; pessimistic lock; advisory lock | Optimistic for low contention; `updated_at` is not a safe substitute ([INFERENCE]) | Retries against blocking | RECOMMENDED | OLTP | Multi-vendor | DES-14, [rowversion](https://learn.microsoft.com/en-us/sql/t-sql/data-types/rowversion-transact-sql), PGMY-08 |
| TX-7 | Retries on external side effects? | Idempotency key with stored outcome and tenant-scoped uniqueness; none | Money movement and retried APIs | Storage and reaper | RECOMMENDED | OLTP | Case study, single vendor | CASE-33, TXN-19 |
| TX-8 | Publishing events with a change? | Transactional outbox; dual write | Outbox whenever events must match commits | Relay and de-duplication | RECOMMENDED | OLTP, streaming | Multi-vendor | TXN-18, PIPE-05, TEN-27 |
| TX-9 | Multi-service workflow? | Saga; 2PC via external manager; consensus database | Sagas when no shared transaction exists; 2PC only inside managed systems | Isolation loss against coupling | OPTIONAL | OLTP | Standard, single vendor | TXN-17, TXN-20, ARCH-06 |
| TX-10 | Ledger shape? | Append-only postings; mutable balance | Financial systems. Correction by new entry is the vendor norm (FN-21). Germany forbids changes that lose original content (FN-20) | Correction by reversal; balance derivation | RECOMMENDED; non-alteration of books is MANDATORY in Germany (FN-20), which does not prescribe append-only storage | OLTP | Case study, multi-vendor, standard (Germany only) | TEN-41, TEN-42, TEN-43, CASE-30, CASE-31, ERP-02, ERP-06, ERP-23 |
| TX-11 | Does each journal balance per currency? | Enforced in posting transaction; reported later | Ledgers | Posting logic | RECOMMENDED | OLTP | Case study | TEN-41, TEN-42, CASE-31 |
| TX-12 | Legal document numbers? | Locked per-series counter; sequence | EU invoices must be sequential and unique; national gap rules differ (LG-1 to LG-9); sequences have gaps on PostgreSQL | Series-level contention | MANDATORY (EU VAT-registered suppliers: sequential and unique; other jurisdictions in LG-2 to LG-9); RECOMMENDED (counter mechanism) | OLTP | Standard, single vendor | TEN-39, TEN-33, LEG-01 |
| TX-13 | MongoDB snapshot guarantees? | Explicit snapshot read and majority write concern; defaults | Required to obtain snapshot isolation | Latency | MANDATORY (engine rule) | OLTP (MongoDB) | Single vendor | MSOM-18, [Jepsen MongoDB](https://jepsen.io/analyses/mongodb-4.2.6) |
| TX-14 | Which endpoint for safety-critical reads? | Primary; replica | Primary; replicas may weaken guarantees | Load | RECOMMENDED | OLTP | Case study | [Jepsen RDS PostgreSQL 17.4](https://jepsen.io/analyses/amazon-rds-for-postgresql-17.4), PERF-31 |
| TX-15 | Check anomaly assumptions per engine version? | Reassess at major version; assume stable | [INFERENCE] Jepsen's PostgreSQL 12.3 finding shows regressions occur | Test effort | RECOMMENDED | OLTP | Case study, inference | TXN-12, TXN-11, TXN-10 |

Notes: Notes 12 and 14 label idempotency keys, outbox writes and ledger immutability MANDATORY. They are RECOMMENDED here because the supporting sources are operator documentation and practitioner reports rather than standards. Oracle and SQL Server anomaly rows rest on vendor docs plus Hermitage. Gilbert and Lynch's theorem text was confirmed at the catalogued URL (note 22); no further claims from it are used.

## 10. Multi-company and multi-tenant isolation

Scope: tenant separation (SaaS) and company separation (ERP). These are orthogonal axes.

| ID | Question | Options | When each applies | Trade-offs | Class | Scope | Evidence | Sources |
|---|---|---|---|---|---|---|---|---|
| MT-1 | Must tenants be isolated? | Isolated by some mechanism; not | Every SaaS provider per AWS SaaS Lens | Cost | MANDATORY (mechanism is a choice) | OLTP | Multi-vendor | SEC-35, CLOUD-03, CLOUD-18 |
| MT-2 | Which tenancy model? | Silo; pool; bridge | Silo for own keys, backup policy, residency; pool for many small tenants; bridge per service or tier | Isolation, noisy neighbour, restore, cost, customization | OPTIONAL | OLTP | Multi-vendor | CLOUD-03, CLOUD-18, CLOUD-19 |
| MT-3 | Tenant column in pooled data? | Required on tenant-scoped tables; omit | Pooled and sharded designs | None material | MANDATORY (pool and sharded) | OLTP | Multi-vendor | CLOUD-18, CLOUD-19, PERF-44, TEN-07 |
| MT-4 | Does tenant context reach the data layer on every request? | Mandatory context; convention | Atlassian rejects requests without tenant context; Microsoft and AWS note identity must be propagated when RLS is used | Plumbing | RECOMMENDED | OLTP | Case study, multi-vendor | CLOUD-18, PGMY-07, CASE-42 |
| MT-5 | Where is isolation enforced? | Engine RLS; application predicates; separate credentials | RLS default-deny, with bypass rules and covert channels; many solutions avoid it (C-15) | Assurance against complexity | OPTIONAL | OLTP | Multi-vendor | PGMY-07, MSOM-05, CLOUD-18 |
| MT-6 | Tenant in keys? | Leading PK element; every PK and FK; partition key | Citus requires it; Microsoft for split and merge; Salesforce partition | Key width (C-16) | RECOMMENDED; MANDATORY on Citus | OLTP | Multi-vendor | PERF-44, CLOUD-19, TEN-07 |
| MT-7 | Unique constraints in pooled data? | Include tenant; global | [INFERENCE] prevents cross-tenant value inference; FK checks can bypass RLS | Key width | RECOMMENDED | OLTP | Single vendor, inference | PGMY-07, PERF-44 |
| MT-8 | Per-tenant tables or columns? | Avoid; dedicated custom-data table | Azure lists both as antipatterns | Customization | RECOMMENDED (avoid) | OLTP | Single vendor | CLOUD-18, TEN-07 |
| MT-9 | Schema per tenant? | Not assessed | No source recommends or assesses it | Migration cost inferred | No classification; evidence gap | OLTP | Inference | Note 14 |
| MT-10 | Tenant placement catalog? | Maintained catalog; hard-coded | Silo, sharded, bridge | Operational component | RECOMMENDED | OLTP | Single vendor, case study | CLOUD-19, CASE-42 |
| MT-11 | Company identifier in ERP tables? | On transactional and most setup tables; tenant only | ERP products use a company or legal-entity boundary for posting, sometimes security | Join and key width | RECOMMENDED | OLTP (ERP) | Multi-vendor | TEN-08, TEN-09, TEN-10, ERP-07, ERP-09 |
| MT-12 | Posting boundary? | One company per financial posting | NetSuite generally posts to one subsidiary | Intercompany handling | RECOMMENDED | OLTP (ERP) | Multi-vendor | TEN-09, TEN-08, TEN-10, ERP-07 |
| MT-13 | Intercompany? | Linked pair of entries, each balanced per entity, with eliminations | NetSuite posts to two or more subsidiaries; ERPNext balances each company's entry independently; D365 uses directional legal-entity pairs; Oracle balances by legal entity | Complexity | RECOMMENDED | OLTP (ERP) | Multi-vendor | TEN-09, ERP-07, ERP-13, ERP-20 |
| MT-14 | Master data scope? | Tenant-shared; per-company restricted | Dynamics cannot override; Odoo can restrict (C-18) | Reuse against control | OPTIONAL | OLTP (ERP) | Multi-vendor | TEN-08, TEN-10 |
| MT-15 | Consolidation hierarchy? | Tree with elimination entities | Statutory and consolidated reporting | Maintenance | RECOMMENDED | OLTP (ERP), DW | Multi-vendor | TEN-08, TEN-09, ERP-04, ERP-13, ERP-17 |
| MT-16 | Analytical tenancy? | MTT; OPT; APT | MTT scales to millions; OPT to hundreds; APT to tens or low hundreds | Same axes as OLTP | OPTIONAL | DW, lakehouse | Single vendor | LAKE-13 |
| MT-17 | Are legal entity, ledger and business unit distinct concepts? | Distinct; one company concept | Oracle separates balancing segment, ledger and business unit; D365 configures a ledger per legal entity. No official SAP company-code definition was read | Setup complexity | RECOMMENDED | OLTP (ERP), consolidation | Multi-vendor | ERP-07, ERP-09 |
| MT-18 | Is consolidation a legal requirement? | Consolidated statements; none | A parent presents consolidated statements under IFRS 10. Elimination paragraphs were not read; FAS 52 para. 25 addresses intercompany profit | Reporting cost | MANDATORY (IFRS parents presenting consolidated statements, at concept level only) | Consolidation | Standard (summary page only) | ERP-21, ERP-22 |
| MT-19 | Where does elimination live? | Elimination entity; report-time; posting level; line-level flag | D365 entity or report-time; SAP posting level 20; NetSuite elimination journals | Traceability against reporting complexity | OPTIONAL | Consolidation | Multi-vendor | ERP-04, ERP-13, ERP-17 |
| MT-20 | Are intercompany currency differences errors? | Expected, with a defined account; treated as errors | NetSuite CTA-E and its revaluation link; D365 shows originating currency in elimination journals | Reconciliation design | RECOMMENDED | Consolidation | Multi-vendor | ERP-13, ERP-17 |

Notes: MT-4 is RECOMMENDED because note 14 partly relies on an AWS whitepaper tenet that is search-only. MT-11 and MT-12 are RECOMMENDED; note 14's MANDATORY label rests on ERP product documentation, which describes those products rather than obliging others. SAP rests on training pages only (ERP-01 to ERP-04). MT-5 overhead remains a judgment: the only measurement is BENCH-07, one small practitioner test, and no result covers join-based policies or MySQL. MT-1 is framed by AWS and Azure; Google has no equivalent page in the notes.

## 11. Security and permissions

Scope: access, secrets, encryption, privacy.

| ID | Question | Options | When each applies | Trade-offs | Class | Scope | Evidence | Sources |
|---|---|---|---|---|---|---|---|---|
| SC-1 | Application database role? | Least privilege, non-owner DML role; owner or admin | Always | Provisioning | MANDATORY | General | Standard | SEC-08, SEC-01, SEC-07 |
| SC-2 | SQL construction? | Bound parameters; string concatenation | Every access path | None material | MANDATORY | General | Standard | SEC-02, SEC-03, SEC-06 |
| SC-3 | Role separation? | Separate migrator, read-only, audit-writer, security manager roles; shared | [INFERENCE] composite of OWASP and vendor guidance | Role count | RECOMMENDED | General | Standard, inference | SEC-01, SEC-05, SEC-28, MSOM-05 |
| SC-4 | Sensitive data classification? | Attribute-level classification; none | ASVS requires inventory; GDPR Art. 30 requires processing records. The Art. 30(5) small-enterprise exemption is narrow and is lost where processing is not occasional | Upkeep | MANDATORY where GDPR applies or ASVS conformity is claimed; otherwise RECOMMENDED | General | Standard | SEC-07, SEC-15, TEN-34, LEG-03 |
| SC-5 | Data minimization? | Collect only what is needed; retain broadly | GDPR Art. 5(1)(c), Art. 25; OWASP avoid storing where possible | Feature richness | MANDATORY where GDPR applies | General | Standard | SEC-15, SEC-04 |
| SC-6 | Encryption layer? | TDE; column or application level; Always Encrypted | TDE for at-rest and media threats; column or client-side against DBAs, with query limits | Protection against queryability | OPTIONAL by threat model | General | Multi-vendor | SEC-24, SEC-23, SEC-04, SEC-08 |
| SC-7 | Stored PAN? | Rendered unreadable by column-level means; disk encryption alone | PCI DSS 3.5.1, with disk-level alone rejected by 3.5.1.2 | Tokenization cost | MANDATORY (PCI scope) | General | Standard | SEC-17 |
| SC-8 | ePHI encryption? | Encrypt | HIPAA addressable today; 2025 NPRM proposes required; final status not verified | Key management | RECOMMENDED; design as if required ([INFERENCE]) | General | Standard | SEC-18 |
| SC-9 | Is masking a boundary? | Treat as defence in depth; treat as a control | SQL Server and Oracle both document inference attacks | Expectation setting | MANDATORY (do not rely on it alone) | General | Multi-vendor | SEC-25, MSOM-13 |
| SC-10 | Key handling? | Keys separate, managed lifecycle; alongside data | Authenticated modes under managed keys | KMS dependence | MANDATORY for NIST-aligned systems; RECOMMENDED otherwise | General | Standard | SEC-11, SEC-04, SEC-08 |
| SC-11 | Secrets in code? | Secrets manager; code or repo | Never in code or repositories; avoid environment variables for keys | Tooling | RECOMMENDED | General | Standard | SEC-04, SEC-01 |
| SC-12 | Non-production data? | Masked or synthetic; copy of production | NIST PM-25 and SP 800-122; PCI forbids live PANs pre-production | Realism against leakage | RECOMMENDED; MANDATORY (PCI, federal) | General | Standard | SEC-08, SEC-09, SEC-17 |
| SC-13 | Isolate PII in dedicated structures? | Separate tables or schemas with a surrogate; inline | [INFERENCE] supports pseudonymisation and encryption scope | Joins | OPTIONAL | OLTP | Standard, inference | SEC-16, SEC-09 |
| SC-14 | Erasing data via key destruction? | Per-subject keys; true deletion | No regulator text accepts key destruction as Art. 17 erasure. A consultation-stage EDPB text on blockchain describes the effect and recalls that encrypted data is still personal data; [INFERENCE] also needs SP 800-88 preconditions | Key system complexity; must not be presented as settled legal erasure | OPTIONAL | General | Inference; consultation text does not endorse it | SEC-12, SEC-16, LEG-33, LEG-34 |
| SC-15 | Central policy on analytical platforms? | Tags and masks; per-object grants | Snowflake tags, Unity Catalog filters and masks, BigQuery policy tags | Policy type-matching risks | RECOMMENDED | DW, lakehouse | Multi-vendor | SEC-31, SEC-32, SEC-33, LAKE-04 |
| SC-16 | Hardening baseline? | Version-pinned CIS Benchmark; ad hoc | Benchmarks exist per engine major version; PDFs were not read | Upkeep | OPTIONAL | General | Standard (index only) | SEC-14 |

Notes: SC-1 and SC-2 are MANDATORY on OWASP guidance (catalog authority 4) plus NIST AC-6 for SC-1; no regulator text in the notes states parameter binding. Regulations apply only in their jurisdictions and sectors. SEC-16 is a consultation version. NIST text is reliable PDF extraction per `CORRECTIONS.md`.

## 12. Audit and history

Scope: who changed what, what was true when, and how long it stays.

| ID | Question | Options | When each applies | Trade-offs | Class | Scope | Evidence | Sources |
|---|---|---|---|---|---|---|---|---|
| AH-1 | Row-level audit columns? | created and updated by and at; none | Business tables; Odoo and OFBiz standardize variants; iDempiere is confirmed for AD_Org only; Frappe standard columns were not found in verification | Storage; no before-values | RECOMMENDED | OLTP | Case study, multi-vendor | TEN-45, DES-22, CASE-44, CASE-48, CASE-50 |
| AH-2 | Before and after values? | Trigger shadow; system versioning; ORM revisions | Same-transaction capture where history must match commits | Write cost | RECOMMENDED | OLTP | Multi-vendor | TEN-11, MSOM-04, TEN-15 |
| AH-3 | Access and DDL events? | Engine audit log; none | pgAudit, SQL Server Audit, Oracle Unified Auditing | Log volume; pgAudit is best-effort | RECOMMENDED | OLTP | Multi-vendor | SEC-27, SEC-26, SEC-28, ENG-14, ENG-16 |
| AH-4 | Regulated electronic records? | Secure, computer-generated, time-stamped trail not obscuring prior values | 21 CFR 11.10(e), retained as long as the record | Storage | MANDATORY (Part 11 scope) | OLTP | Standard | TEN-17 |
| AH-5 | Card or health audit? | PCI 10 and HIPAA audit controls | PCI: 12 months, three months immediately available (wording from v4.0 SAQ D, v4.0.1 text not read); HIPAA audit controls | Storage | MANDATORY (PCI, HIPAA scope) | General | Standard | SEC-17, SEC-18, LEG-30 |
| AH-6 | Who can alter audit data? | Restricted, app cannot disable; application-owned | Application must not run as owner or superuser | Separate roles | MANDATORY | OLTP | Standard, multi-vendor | SEC-08, TEN-11, SEC-26 |
| AH-7 | Tamper evidence? | Hash chain with digests off-database; ACL only | Auditor attestation; no relational engine prevents DBA tampering | Complexity | OPTIONAL | OLTP | Single vendor | TEN-14, TEN-11 |
| AH-8 | Time dimensions? | System time; valid time; bitemporal | System for audit; valid for business effect; both when past-effective corrections must be reconstructable | Query complexity | OPTIONAL | General | Standard | GOV-06, TEN-23, LIT-58 |
| AH-9 | Period convention? | Closed-open; inclusive | Closed-open in SQL:2011, Snodgrass and SQL Server; beware BETWEEN (C-33) | Query care | RECOMMENDED | General | Standard, multi-vendor | GOV-06, TEN-23, MSOM-04 |
| AH-10 | System time source? | Engine-maintained; user-editable | Engine-maintained where history is an audit obligation | Engine support varies; emulated on PostgreSQL | MANDATORY where the record is legally regulated; RECOMMENDED otherwise | OLTP | Standard | GOV-06, TEN-17, MSOM-04 |
| AH-11 | Valid-time merge rule? | FOR PORTION OF split; out-of-order overwrite | Must be chosen (C-34) | Semantics | OPTIONAL | OLTP | Standard, single vendor | GOV-06, TEN-25 |
| AH-12 | Soft delete? | Hard delete with archive; aggregate-level mark with purge; per-row flag | Aggregate root with grace period is the reconciled position (C-38). No regulator text addresses soft deletion by name; [INFERENCE] a flag leaves personal data present and is a step before real erasure, not erasure | Query, FK and erasure burden against recoverability | RECOMMENDED (avoid pervasive flags) | OLTP | Case study | TEN-30, TEN-31, CASE-44, CASE-50, LEG-03, LEG-36 |
| AH-13 | Retention schedule per record class? | Documented with legal basis; none | GDPR Art. 30 and 21 CFR Part 11. Statutory periods differ by jurisdiction, record class and start event (LG-16 to LG-24) | Governance | MANDATORY (GDPR, Part 11 scope); RECOMMENDED otherwise | General | Standard | TEN-34, TEN-17, LEG-03, LEG-05 |
| AH-14 | Retention mechanism? | Date partitions; archive tables; object lifecycle | Partition DETACH or DROP for scale | Partition design | RECOMMENDED | OLTP, DW | Multi-vendor | PGMY-06, TEN-20, TEN-35 |
| AH-15 | Erasure versus retention? | Legal-obligation exception; purge | Art. 17(3)(b) and (e) disapply erasure to the extent processing is necessary; basis must be recorded. Art. 17(3)(b) refers to Union or Member State law, so a non-EU retention rule is not clearly covered | Legal analysis | MANDATORY (GDPR scope) | General | Standard | SEC-15, TEN-34, LEG-03 |
| AH-16 | Analytical history? | SCD types | Type 2 for reconstructable attributes; system-versioned OLTP tables can feed Type 2 | Row growth | OPTIONAL | DW | Single vendor (method owner) | DWM-01, TEN-24, MSOM-04 |

Notes: SOX 18 USC 1520 retention covers auditors' workpapers rather than all financial data (TEN-36). Crypto-shredding has no direct regulator support (SC-14, LG-26). Ledger tables and system versioning are options, not requirements, outside named regulated contexts.

## 13. Migrations and version control

Scope: changing schemas safely.

| ID | Question | Options | When each applies | Trade-offs | Class | Scope | Evidence | Sources |
|---|---|---|---|---|---|---|---|---|
| MG-1 | Are schema changes scripted and versioned? | Versioned scripts applied by tool; manual | All environments; Azure lists manual schema change as an antipattern | Tooling | RECOMMENDED | General | Case study, multi-vendor | OPS-15, OPS-01, OPS-10, CLOUD-18 |
| MG-2 | Authoring model? | State-based; migration-based; hybrid | Hybrid is the trend; neither ideal (C-43) | Renames against accumulation | OPTIONAL | General | Multi-vendor | OPS-14, OPS-13 |
| MG-3 | Compatibility during deploy? | Expand and contract; breaking change | Every change deployable while the previous version runs ([INFERENCE] meta-rule) | Multi-release effort | RECOMMENDED | OLTP | Case study, multi-vendor | OPS-01, OPS-02, OPS-05, OPS-06, CASE-23 |
| MG-4 | Rollback stance? | Forward-only with compatibility; down scripts; backup as recovery | Down scripts are an emergency convenience with tested scope (C-42) | Coverage varies per tool | RECOMMENDED (forward-only) | OLTP | Multi-vendor | OPS-10, OPS-11, OPS-04, OPS-07 |
| MG-5 | Who writes and reviews? | Developer-authored with DBA review; DBA-authored | Sources converge on collaboration | Skills | RECOMMENDED | General | Case study | OPS-15, OPS-01 |
| MG-6 | Generated migrations? | Treat as candidates requiring review; apply unchanged | Every tool's documentation requires review; renames undetectable | Review effort | RECOMMENDED | General | Multi-vendor | OPS-12, OPS-13 |
| MG-7 | Lock and duration budgets? | State both; unmanaged | About 2 s, 10 s or 15 s lock budgets from three operators (C-47) | Slower rollouts | RECOMMENDED | OLTP | Case study | OPS-07, OPS-08, OPS-04 |
| MG-8 | Online changes on PostgreSQL? | CONCURRENTLY, NOT VALID then VALIDATE, batched backfill; blocking DDL | Large tables | Multiple steps | RECOMMENDED | OLTP (PostgreSQL) | Single vendor, case study | OPS-09, PERF-10, OPS-07, OPS-05, OPS-08 |
| MG-9 | Online changes on MySQL? | INSTANT or INPLACE; gh-ost; pt-osc | INSTANT if possible; tools for large tables; triggers versus binlog (C-46) | Tool limits | RECOMMENDED | OLTP (MySQL) | Single vendor, case study | [pt-osc](https://docs.percona.com/percona-toolkit/pt-online-schema-change.html), CASE-23 |
| MG-10 | Data backfills? | Outside DDL transaction, batched; inside migration | Batched and throttled; GitLab batched background migrations (C-45) | Duration | RECOMMENDED | OLTP | Case study | OPS-04, OPS-08, OPS-06 |
| MG-11 | Tie rules to engine version? | Versioned rule set; timeless | PostgreSQL default rewrite behaviour changed over versions (C-48) | Maintenance | RECOMMENDED | General | Case study, inference | OPS-09, CASE-27, OPS-04 |
| MG-12 | Verifying data migrations? | Dual-write and dark reads; none | Verification appears in several migrations | Duplicate load | RECOMMENDED | OLTP | Case study | OPS-06, CASE-02, CASE-03, CASE-07, CASE-15 |
| MG-13 | Safe changes on table formats? | Intersection set; format-specific | Add nullable, widen int and float, widen decimal | Portability | RECOMMENDED | Lakehouse | Multi-vendor | PIPE-10, PIPE-11, PIPE-12 |
| MG-14 | Breaking change in streams? | Compatible evolution; dual schema with versioned topic | Dual upgrade where compatibility cannot express the change | Consumer migration | RECOMMENDED | Streaming | Single vendor, inference | PIPE-02, PIPE-03 |
| MG-15 | Contracted analytical change? | Model versions and contract diff; silent change | Public models; dbt classifies removal, type change, constraint removal as breaking | Contract upkeep | RECOMMENDED | DW, lakehouse | Single vendor | DQ-03, LAKE-17 |

Notes: Tool documentation is authority level 3 or 4, and no standards body addresses this area, so nothing is MANDATORY. Note 13's MANDATORY label on reviewing generated DDL is held here as RECOMMENDED.

## 14. Pipelines and ETL/ELT

Scope: moving and transforming data.

| ID | Question | Options | When each applies | Trade-offs | Class | Scope | Evidence | Sources |
|---|---|---|---|---|---|---|---|---|
| PL-1 | ETL or ELT? | ETL; ELT; hybrid | ELT recommended by Google and dbt; ETL for existing transforms or regulated fields | Re-derivation against raw exposure | OPTIONAL | DW, lakehouse | Multi-vendor | PIPE-19, PIPE-18 |
| PL-2 | Batch or streaming? | Batch; micro-batch; streaming | By freshness need | Cost against latency | OPTIONAL | DW, lakehouse, streaming | Standard, single vendor | PIPE-16, PIPE-17 |
| PL-3 | Reprocessing architecture? | Lambda; Kappa; unified model | Against dual codebases per Kreps and Akidau (C-54) | Retention, swap mechanics | OPTIONAL | Streaming | Standard, single vendor | PIPE-15, PIPE-17, CLOUD-17 |
| PL-4 | Are pipeline runs idempotent? | Upsert or partition overwrite; plain INSERT | Every re-runnable step | Merge keys | MANDATORY | DW, lakehouse, streaming | Multi-vendor | PIPE-13, PIPE-08, PIPE-01, PIPE-06 |
| PL-5 | Deterministic inputs per interval? | Interval-partitioned reads; latest data | Scheduled pipelines; Airflow forbids reading latest | Interval column | RECOMMENDED | DW, lakehouse | Single vendor | PIPE-13 |
| PL-6 | Change capture source? | Log-based CDC; query-based timestamp; trigger | Log-based preferred; timestamp when no log access | Connector operations | RECOMMENDED | OLTP, streaming | Multi-vendor | PIPE-06, TEN-26, TEN-29 |
| PL-7 | Prerequisites of capture? | PK or replica identity; none | Required for update and delete capture | Key discipline | MANDATORY (CDC tables, PostgreSQL logical replication) | OLTP, streaming | Multi-vendor | TEN-28, PIPE-06 |
| PL-8 | Updated-at column? | Maintained; omitted | Needed for query-based extraction, not for log-based CDC | Writes | RECOMMENDED; conditional | OLTP | Inference | PIPE-06, note 05 |
| PL-9 | Schema at ingestion? | Declared; inferred | Declare; Spark inference has documented pitfalls | Up-front effort | RECOMMENDED | Lakehouse, streaming | Single vendor | PIPE-07, PIPE-08 |
| PL-10 | Raw landing? | Keep raw then type; type at ingest | Bronze as source of truth; compliance risk from raw PII | Security against re-derivation | OPTIONAL | Lakehouse, DW | Multi-vendor | LAKE-01, PIPE-18, CLOUD-21 |
| PL-11 | Deletes in event flows? | Keyed tombstone or delete event; none | Compaction and CDC | Retention of tombstones | MANDATORY (engine rule for compacted topics) | Streaming | Single vendor | PIPE-01, PIPE-06 |
| PL-12 | Event identity? | Stable key plus dedupe id; none | Required for ordering; [INFERENCE] for idempotent reads | Producer discipline | RECOMMENDED | Streaming | Single vendor, inference | PIPE-01, ARCH-11, PIPE-05 |
| PL-13 | Time in events? | Explicit event and processing time; broker time | Event time is what matters for windowing | Field upkeep | RECOMMENDED | Streaming | Standard, inference | PIPE-17, PIPE-16, PIPE-01 |
| PL-14 | Late data policy? | Watermark with defined lateness; none | Windowed aggregates | Completeness against latency | RECOMMENDED | Streaming | Single vendor, standard | PIPE-08, PIPE-17 |
| PL-15 | Unit of orchestration? | Task (Airflow); asset (Dagster) | Both agree on idempotence | Tool model | OPTIONAL | DW, lakehouse | Multi-vendor | PIPE-13, PIPE-14 |
| PL-16 | Sink exactly-once? | Idempotent sink; transactional sink; none | Delegated to sink by Kafka; Spark depends on sink | Sink capability | RECOMMENDED | Streaming | Multi-vendor | PIPE-01, PIPE-08 |
| PL-17 | Connector-edge transforms? | Single message transforms; stream processor | [INFERENCE] document flattening conventions | Hidden contract | OPTIONAL | Streaming | Single vendor | PIPE-04 |

Notes: Note 05 states that no official source prescribes `updated_at`, soft-delete columns, late-arriving-dimension placeholders or reconciliation tables explicitly; these remain framework decisions.

## 15. Data quality and validation

Scope: checks and reconciliation.

| ID | Question | Options | When each applies | Trade-offs | Class | Scope | Evidence | Sources |
|---|---|---|---|---|---|---|---|---|
| DV-1 | Where does validation sit? | Constraints; pipeline gates; warehouse tests | All three; each catches a different failure class (C-57) | Duplicate effort against gaps | RECOMMENDED | General | Multi-vendor | DQ-03, DQ-14, DQ-12, LAKE-19 |
| DV-2 | Is validation the system of record's job? | Constraints at source; downstream only | Nothing downstream can retroactively enforce what the source admitted ([INFERENCE] from note 15) | Write cost | MANDATORY (OLTP constraints, see RI-2) | OLTP | Multi-vendor | PGMY-01, MSOM-02, MSOM-08 |
| DV-3 | Promotion gate before consumers see data? | Write-Audit-Publish; expectations with fail; post-hoc tests | Consumer-facing tables | Latency against bad data exposure | RECOMMENDED | DW, lakehouse | Multi-vendor, case study | DQ-12, DQ-13, DQ-14 |
| DV-4 | Failure severity? | Blocking; warn; tiered | Netflix, Databricks and dbt use tiers; Intuit strictly blocks | SLA against quality | RECOMMENDED (tiered) | DW, lakehouse | Multi-vendor, case study | DQ-13, DQ-14, LAKE-19 |
| DV-5 | What happens to bad rows? | Fail; drop; quarantine with flag and view; DLQ | Quarantine in batch; DLQ for streams, reconciled or silent | Storage and handling | RECOMMENDED | Lakehouse, streaming | Multi-vendor | DQ-14, [Kafka Connect Concepts](https://docs.confluent.io/platform/current/connect/concepts.html) |
| DV-6 | Quality vocabulary? | DAMA UK six plus currency; ISO/IEC 25012 model; ISO 8000 process | Pick one and map others; [INFERENCE] 25012 inherent characteristics map to constraints | Vocabulary alignment | RECOMMENDED | General | Standard, single vendor | GOV-03, GOV-04, GOV-10, GOV-11, GOV-12, GOV-02 |
| DV-7 | Batch reconciliation? | Row counts and aggregates; none | Consumer-facing loads; note 15 labels this MANDATORY but the sources are tools | Run cost | RECOMMENDED | DW, lakehouse | Multi-vendor, case study | DQ-04, DQ-14, DQ-13, DQ-15 |
| DV-8 | Financial reconciliation? | Subledger to GL per closed period, with classified differences; counts only | Financial pipelines | Control account discipline | RECOMMENDED | DW | Single vendor | DQ-16, TEN-43 |
| DV-9 | Row-level difference checks? | Hash or segment diffs; aggregates only | Migration and replication validation; data-diff is archived, reladiff fork exists | Compute | OPTIONAL | General | Single vendor | DQ-17 |
| DV-10 | Data contracts? | ODCS-style; schema-only registry; none | Datasets crossing team boundaries | Agility cost argued, not measured (C-56) | RECOMMENDED | DW, lakehouse, streaming | Multi-vendor | PIPE-20, ARCH-23, DQ-03, PIPE-03 |
| DV-11 | Where are contracts enforced? | Producer CI; pipeline; warehouse | Maturity progression ([INFERENCE]) | Producer effort | OPTIONAL | DW, lakehouse, streaming | Single vendor (vendor-adjacent), inference | DQ-11, DQ-03 |
| DV-12 | Metrics over time? | Persisted; single-run | Anomaly and distributional checks need history | Storage | RECOMMENDED | DW, lakehouse | Multi-vendor | DQ-05, DQ-07 |
| DV-13 | Tool or specification? | Prefer specifications; tool lock-in | Tools churn (data-diff, Amundsen archived); specs persist | Tool ergonomics | RECOMMENDED | General | Inference, standard | PIPE-20, GOV-31 |
| DV-14 | Streaming schema checks? | Registered compatibility mode other than NONE; none | Producer and consumer independence | Upgrade order | RECOMMENDED | Streaming | Single vendor | PIPE-02 |
| DV-15 | Transitive compatibility? | BACKWARD_TRANSITIVE or similar; default | [INFERENCE] for compacted or long-retention topics | Restrictiveness | RECOMMENDED | Streaming | Single vendor, inference | PIPE-02 |

Notes: Note 15's MANDATORY labels on contracts and batch controls derive from tool and specification structure and are held as RECOMMENDED. No source gives numeric SLO targets, and no controlled comparison of defect-catch rates exists.

## 16. Reporting and analytical models

Scope: OLAP and DW consumption, and lakehouse Gold.

| ID | Question | Options | When each applies | Trade-offs | Class | Scope | Evidence | Sources |
|---|---|---|---|---|---|---|---|---|
| RP-1 | Consumption shape? | Star; snowflake; wide table; nested | Star default by method and vendor guidance; OBT as derived layer; nested on BigQuery. Query speed is engine-dependent (C-84) | Query simplicity against storage and update cost. BENCH-10 found star faster on Redshift and MariaDB Columnstore and flat faster on Singlestore; a vendor-hosted test found flat faster on three platforms [WF] | RECOMMENDED (star) | OLAP, DW, lakehouse | Multi-vendor; case study (one conference benchmark, unreproduced; one vendor-hosted test) | DWM-14, CLOUD-21, LAKE-14, CLOUD-12, DWM-22, BENCH-10 |
| RP-2 | Integration layer? | None; 3NF EDW; Data Vault | Few stable sources: none; many sources or audit need: add one and keep marts | Load complexity against reconciliation | OPTIONAL | DW, lakehouse | Multi-vendor, inference | DWM-04, DWM-06, DWM-08, DWM-14 |
| RP-3 | Fact grain? | Declared, single grain; mixed | Always within dimensional modeling | None material | MANDATORY (Kimball method) | OLAP, DW | Single vendor (method owner) | DWM-01, DWM-02 |
| RP-4 | Conformed dimensions? | Conformed; independent marts | Both Kimball and Inmon reject stovepipes | Coordination | MANDATORY (Kimball method); RECOMMENDED overall | DW | Single vendor (method owner) | DWM-01, DWM-02, DWM-04 |
| RP-5 | NULL fact foreign keys? | Default dimension row; NULL | Dimensional fact tables | Row management | MANDATORY (Kimball method) | DW | Single vendor (method owner) | DWM-01, DWM-02 |
| RP-6 | Dimension key type? | Integer; hash; natural | Contested (C-11) | Join speed against parallel idempotent load | RECOMMENDED (integer in Kimball); otherwise unresolved | DW, lakehouse | Multi-vendor conflict | DWM-01, LAKE-14, LAKE-16, DWM-21 |
| RP-7 | Attribute history? | SCD 0 to 7; snapshots; none | Per attribute; Dynamic Tables cannot express SCD2 | Row growth | OPTIONAL | DW, lakehouse | Single vendor (method owner) | DWM-01, TEN-24, LAKE-18, LAKE-12 |
| RP-8 | Aggregates? | Materialized views; aggregate tables; on demand | Warehouse aggregation | Refresh and DML cost; not for high-DML OLTP | RECOMMENDED | OLAP, DW | Multi-vendor | PERF-26, PERF-04, PERF-38 |
| RP-9 | Metric definitions? | Semantic layer; per-report logic | [INFERENCE] one definition per metric; Airbnb detail unverified | Tool dependence | OPTIONAL | OLAP, DW | Single vendor | [Snowflake semantic views](https://docs.snowflake.com/en/user-guide/views-semantic/overview), LAKE-06 |
| RP-10 | Source for operational reports? | Primary; replica; warehouse | Replica unless report drives transactions | Staleness | RECOMMENDED | OLTP, OLAP | Case study, inference | [Jepsen RDS PostgreSQL 17.4](https://jepsen.io/analyses/amazon-rds-for-postgresql-17.4), CLOUD-16 |
| RP-11 | Vault direct to consumers? | Via information marts; direct | Marts; Linstedt says vault should not be directly accessed | Mart build | MANDATORY (Data Vault method) | DW | Single vendor (method owner) | DWM-08 |
| RP-12 | Activity Schema? | Use; do not use | Single-entity behavioural analytics; no multi-entity financial support | Tooling | OPTIONAL | OLAP | Single vendor | DWM-24 |
| RP-13 | Financial reporting? | Reconciled facts, multi-currency, allocations; raw | Kimball covers allocations and multi-currency facts | Grain planning | RECOMMENDED | DW | Single vendor (method owner) | DWM-01, DQ-16 |
| RP-14 | Fact foreign keys and surrogates through ETL? | Lookup pipeline with effective dating; direct | Late-arriving facts resolve as of event date | Pipeline complexity | RECOMMENDED | DW | Single vendor (method owner), inference | DWM-01, DES-12 |

Notes: MANDATORY in this section is method-scoped only. A team not using Kimball or Data Vault is not bound by those rows. Data Vault against star remains a judgment: BENCH-11 and BENCH-12 point in different directions at very small scale or low confidence, and neither supports a production claim.

## 17. Scalability and maintainability

Scope: growth paths and long-term upkeep.

| ID | Question | Options | When each applies | Trade-offs | Class | Scope | Evidence | Sources |
|---|---|---|---|---|---|---|---|---|
| SM-1 | When to scale out? | Vertical first; vertical partitioning; horizontal | Teams exhausted vertical options first | Complexity later | RECOMMENDED | OLTP | Case study | CASE-01, CASE-02, CASE-04, CASE-08 |
| SM-2 | Shard key? | Tenant-like key; entity id | High cardinality, even, in most queries; keep most transactions local | Rebalancing cost | RECOMMENDED | OLTP | Multi-vendor, case study | PERF-30, PERF-43, PERF-45, CASE-01, CASE-02, CASE-07 |
| SM-3 | Logical shards? | Many logical on few physical; physical only | Enables capacity moves without re-keying | Metadata | RECOMMENDED | OLTP | Case study | CASE-02, CASE-03, CASE-05 |
| SM-4 | Sequential keys under distribution? | Avoid or hash; sequential | Range-sharded systems | Locality loss | RECOMMENDED (range-sharded and distributed topologies) | OLTP (distributed) | Multi-vendor | CLOUD-11, PERF-48, CLOUD-06 |
| SM-5 | Cross-shard transactions? | Forbid by design; allow; consensus system | Keep within shard key where possible | Application complexity | RECOMMENDED | OLTP | Case study, multi-vendor | CASE-01, CASE-04, TXN-20, PERF-44 |
| SM-6 | Build or adopt shard layer? | Build; adopt Vitess or Citus | Contested (X22 in the companion) | Control against maturity | OPTIONAL | OLTP | Case study | CASE-01, CASE-02, CASE-07, CASE-04 |
| SM-7 | Read replicas? | Replicas with session guarantees; primary only | Eventual by default; read-your-writes via primary or causal sessions; replication is asynchronous by default on PostgreSQL, and a change is visible on a SQL Server secondary only after redo [WF] | Lag | RECOMMENDED | OLTP | Multi-vendor, case study | PERF-31, CASE-53, ENG-02, ENG-07, ENG-12 |
| SM-8 | Connection pooling? | Transaction pooling; session pooling | Common scaling lever; feature breakage documented | Feature loss | OPTIONAL | OLTP | Single vendor | PERF-52 |
| SM-9 | Caching? | Cache-aside; none | Read-heavy; invalidation needed | Staleness | OPTIONAL | OLTP | Single vendor | PERF-57 |
| SM-10 | CQRS and read models? | Same database first; separate store | Separate only for scale or different storage | Consistency | OPTIONAL | OLTP | Single vendor | PERF-56, ARCH-07 |
| SM-11 | Engine family? | B-tree; LSM | LSM for write-heavy flash; B-tree default for read latency | Compaction amplification | OPTIONAL | OLTP | Single vendor, inference | PERF-42 |
| SM-12 | Rewriting to a new engine? | Evolve incumbent; rewrite | Teams repeatedly rejected rewrites as riskier (C-66) | Migration risk | RECOMMENDED | OLTP | Case study | CASE-01, CASE-02, CASE-07, CASE-04, CASE-09 |
| SM-13 | Cloud table and instance bounds? | Respect guidelines; ignore | SLA-conditioned operational limits on RDS, Aurora and Cloud SQL | Architecture constraints | MANDATORY (SLA-conditioned, per vendor) | OLTP | Multi-vendor | CLOUD-09, CLOUD-14 |
| SM-14 | Partition size in wide-column stores? | Bound; unbounded | Discord's bucketing; tombstones are writes | Modelling care | RECOMMENDED | OLTP (wide-column) | Case study | CASE-15, CASE-16 |
| SM-15 | Enforce boundaries before moving data? | Linters and experiments; move first | GitHub schema-domain linters | Tooling | RECOMMENDED | OLTP | Case study | CASE-04 |

Notes: Case studies are observational and survivorship-biased ([INFERENCE]). Uber's switch is contested and should not be generalised (C-66). No source gives a numeric threshold for moving between stages.

## 18. Testing and automated schema validation

Scope: proving the schema and migrations.

| ID | Question | Options | When each applies | Trade-offs | Class | Scope | Evidence | Sources |
|---|---|---|---|---|---|---|---|---|
| TS-1 | CI gate shape? | Lint, then real engine, then production-like rehearsal | [INFERENCE] three tiers derived from the tool set | Pipeline time | RECOMMENDED | General | Inference, multi-vendor | OPS-16, OPS-13, OPS-15 |
| TS-2 | Static migration lint? | Squawk, Atlas, Liquibase policy checks; none | Blocking DDL and destructive changes; escape hatch by waiver. Squawk's rules target migration safety, and its required-field rule is not a table policy | False positives | RECOMMENDED | OLTP | Multi-vendor | OPS-16, OPS-13, [Liquibase policy checks](https://docs.liquibase.com/liquibase-pro/policy-checks/home.html) |
| TS-3 | Schema assertions? | pgTAP, tSQLt, utPLSQL; none | Structural and behaviour checks, written per object; tSQLt warns that a faked table does not test its constraints | Authoring cost | RECOMMENDED | OLTP | Multi-vendor | THIN-21, THIN-22, THIN-23 |
| TS-4 | Real engine in tests? | Disposable real engine; mocks | Engine semantics differ by version; Testcontainers provides throwaway real engines but performs no checks itself | Runtime | RECOMMENDED | OLTP | Single vendor, inference | OPS-15, THIN-25 |
| TS-5 | Production-like rehearsal? | Yes, with timing thresholds; no | DORA advises production-like data; GitLab uses thin clones | Data safety (see SC-12) | RECOMMENDED | OLTP | Case study | OPS-15, OPS-04 |
| TS-6 | Drift detection? | Continuous; ad hoc | Compare intended and actual schema; Flyway checksums guard edits | Tooling | RECOMMENDED | OLTP | Multi-vendor | [Atlas drift detection](https://atlasgo.io/monitoring/drift-detection), OPS-10 |
| TS-7 | Custom framework checks? | Custom rules; none | Built-in rules cover FK index, PK and required columns in some linters (TS-13, TS-14). Money types, reserved words and tenant columns still need custom rules or assertions (TS-15 to TS-17) | Authoring | RECOMMENDED | OLTP | Multi-vendor (capability), inference | OPS-13, OPS-16, THIN-16, THIN-18, THIN-20, THIN-21, THIN-24 |
| TS-8 | Analytical tests? | PK unique and not_null; relationships; unit tests; asset checks | PK tests on every model per dbt; unit tests for logic | Authoring | RECOMMENDED | DW, lakehouse | Single vendor | LAKE-19, DQ-03, PIPE-14 |
| TS-9 | Test rollback paths? | Test where down scripts exist; untested | Liquibase states rollback scripts need testing | Effort | RECOMMENDED | OLTP | Single vendor | OPS-11 |
| TS-10 | Concurrency correctness? | Anomaly checks per engine; assume | [INFERENCE] Hermitage or Jepsen style reassessment | Effort | OPTIONAL | OLTP | Case study | TXN-10, TXN-11 |
| TS-11 | Migration rollout verification? | Comparison harness; none | Dark reads, Scientist-style comparison | Duplicate load | RECOMMENDED | OLTP | Case study | OPS-06, CASE-02 |
| TS-12 | Automate change delivery target? | Fully automated; partial | DORA target of 100 percent automation | Investment | RECOMMENDED | General | Case study | OPS-15 |
| TS-13 | How is an FK index check automated? | Built-in rule; custom rule; assertion; ORM convention | Built in on Schemalint and prisma-lint; Atlas custom rule (Pro); pgTAP assertions per object; EF Core creates the index by convention; GitLab requires it inside GitLab | Engine and ownership decide need (IX-3) | RECOMMENDED | OLTP | Multi-vendor | THIN-12, THIN-14, THIN-16, THIN-21, THIN-24, OPS-13 |
| TS-14 | How are PK and required-column policies checked? | Built-in rule; custom rule; assertion | Schemalint and prisma-lint built-in; Atlas custom (Pro); pgTAP assertions | Tool cost; prisma-lint reads schema files and Schemalint a live catalog | RECOMMENDED | OLTP | Multi-vendor | THIN-16, THIN-21, THIN-24, OPS-13 |
| TS-15 | How are reserved words checked? | Engine rejection; lint rule; none | SQLFluff RF04 is partial and dialect-dependent, and excludes reserved keywords from its own rule; no other linter opened covers it | Coverage gap | OPTIONAL | General | Single vendor | THIN-15, THIN-18 |
| TS-16 | How are money types checked? | Custom rule; assertion; none | No built-in money rule was found; prisma-lint has a generic field-type rule, pgTAP `col_type_is`, tSQLt schema comparison | Authoring cost | OPTIONAL | OLTP | Inference, single vendor | THIN-21, THIN-22, THIN-24 |
| TS-17 | How are tenant columns checked? | Configurable required-field rule; assertion; none | No tool ships a named tenant-key rule; RLS checks in Schemalint and Atlas are a different check | Authoring cost | OPTIONAL | OLTP | Inference, single vendor | THIN-16, THIN-21, THIN-24, OPS-13 |

Notes: Note 22 confirms the Testcontainers definition, so the restriction in `CORRECTIONS.md` is lifted and TS-4 now cites THIN-25. Not-found marks in note 20 mean not found in the pages read and are not proof of absence. No EF-specific schema-design analyzer was found. Liquibase built-in check lists returned 404, so TS-14 omits them. Atlas and Liquibase rule engines are paid.

## 19. Backup and disaster recovery

Scope: recovery of data and service.

| ID | Question | Options | When each applies | Trade-offs | Class | Scope | Evidence | Sources |
|---|---|---|---|---|---|---|---|---|
| BK-1 | Are RTO, RPO and MTD defined from a BIA? | Defined; assumed | NIST seven-step process; AWS and Google tie design to objectives | Analysis effort | MANDATORY for NIST-governed systems; RECOMMENDED otherwise | General | Standard, multi-vendor | OPS-17, OPS-21, CLOUD-10 |
| BK-2 | Backup foundation? | Base backup plus continuous log; snapshots alone | RPO bounded by log archive ([INFERENCE]) | Storage and tooling | MANDATORY where point-in-time recovery is required | OLTP | Multi-vendor | PGMY-11, PGMY-19, OPS-19, OPS-20 |
| BK-3 | Logical dumps? | Supplement; primary | Portability, partial restore | Not a PITR solution | RECOMMENDED | OLTP | Multi-vendor | PGMY-19, OPS-20, [PG dump](https://www.postgresql.org/docs/current/backup-dump.html) |
| BK-4 | Do replicas count as backups? | Separate backups; replicas only | Never as a substitute | Cost | MANDATORY | General | Multi-vendor | MSOM-07, OPS-20, OPS-21 |
| BK-5 | Restore testing? | Scheduled, verified; untested | Every backup strategy | Time | MANDATORY | General | Standard, multi-vendor, case study | OPS-17, OPS-19, OPS-22, CLOUD-10, CASE-51 |
| BK-6 | Who owns restore capability? | Named owner; shared | GitLab's lapse was lack of ownership | Accountability | RECOMMENDED | General | Case study | CASE-51 |
| BK-7 | Copy strategy? | 3-2-1; offline or immutable copy | Ransomware exposure; CISA endorses immutability with caution (C-51) | Cost, misconfiguration | RECOMMENDED | General | Standard, single vendor | OPS-22, [Veeam](https://www.veeam.com/blog/321-backup-rule.html) |
| BK-8 | Backup encryption and separation? | Encrypted, separated, least privilege; alongside data | Microsoft recommends separation and encryption | Key handling | RECOMMENDED | General | Standard, single vendor | OPS-19, SEC-08 |
| BK-9 | DR tier? | Backup and restore; pilot light; warm standby; active/active | From BIA | Cost against RTO | OPTIONAL | General | Standard, multi-vendor | OPS-17, OPS-21 |
| BK-10 | Failover topology constraints? | Encoded in automation; unconstrained | Divergent writes are the costliest failure (GitHub 2018) | Availability | RECOMMENDED | OLTP | Case study | CASE-52, CASE-53 |
| BK-11 | Restore time measured? | Rehearsed and timed; assumed | Large cluster restores were slow and had not been fully rehearsed | Rehearsal cost | RECOMMENDED | General | Case study | CASE-52, CASE-51 |
| BK-12 | Per-tenant restore? | DB per tenant; side-copy selective | Silo restores in place; pool needs selective recovery | Tenancy choice | OPTIONAL | OLTP | Single vendor | CLOUD-18, CLOUD-19 |
| BK-13 | Lakehouse and warehouse recovery? | Time travel within window; separate backup | Time travel is not long-term backup | Retention windows | MANDATORY (U7 in the companion) | Lakehouse, DW | Multi-vendor | LAKE-11, [Delta history](https://docs.databricks.com/aws/en/delta/history) |

Notes: Vendor retention limits were not on the pages fetched, so none is asserted. ISO 22301 details in note 13 come from a national standards record. NIST SP 800-34 is mandatory for US federal systems and a reference elsewhere.

## 20. Documentation and governance

Scope: the metadata and ownership around schemas.

| ID | Question | Options | When each applies | Trade-offs | Class | Scope | Evidence | Sources |
|---|---|---|---|---|---|---|---|---|
| DG-1 | Governance framework? | DAMA-DMBOK; DCAM; DGI; COBIT APO14; none | Voluntary bodies of knowledge | Cost | OPTIONAL | General | Single vendor, standard | GOV-01, GOV-02, GOV-17, GOV-18 |
| DG-2 | Accountability for each table? | Named owner; none | ODCS Team sections; dbt exposures require owner; note 15 labels MANDATORY but sources are tool-specific | Upkeep | RECOMMENDED | General | Multi-vendor, inference | PIPE-20, LAKE-19, GOV-18 |
| DG-3 | Descriptions at table and column level? | In the schema artefact; external | `COMMENT ON` or dbt YAML; never sensitive values | Upkeep | RECOMMENDED | General | Multi-vendor | DQ-25, LAKE-19 |
| DG-4 | Column-level classification? | Tag attribute; none | See SC-4; drives masking and retention | Upkeep | RECOMMENDED | General | Standard, multi-vendor | SEC-07, SEC-31, SEC-33 |
| DG-5 | Naming and registry standard? | ISO/IEC 11179 aligned; local | Registry required only where mandated | Effort | RECOMMENDED | General | Standard | GOV-08 |
| DG-6 | Contract for shared datasets? | See DV-10 | | | RECOMMENDED | DW, lakehouse, streaming | Single vendor | PIPE-20 |
| DG-7 | Breaking-change classification? | Registry or contract diff; none | Same classification in Confluent and dbt | Process | RECOMMENDED | DW, lakehouse, streaming | Multi-vendor | PIPE-02, DQ-03 |
| DG-8 | Lineage standard? | OpenLineage push; platform native; catalog pull | Platform lineage retention varies from 30 days to one year | Integration | RECOMMENDED | DW, lakehouse | Multi-vendor | GOV-31, DQ-19, DQ-20, DQ-21, DQ-22 |
| DG-9 | Lineage-friendly design? | Avoid renames and opaque UDFs; ignore | Platform lineage has holes | Constraints on design | RECOMMENDED | DW, lakehouse | Multi-vendor, inference | DQ-20, DQ-21 |
| DG-10 | Catalog metadata vocabulary? | DCAT 3; platform catalog | Publishing dataset metadata on the web | Effort | RECOMMENDED for web publication | General | Standard | GOV-30 |
| DG-11 | Data model review? | Scorecard; informal | Practitioner method; industry-standard claim is the publisher's | Effort | OPTIONAL | General | Single vendor | GOV-32 |
| DG-12 | Security governance? | ISO/IEC 27001 | Clauses 4 to 10 when conformity is claimed; Annex A by risk | Certification cost | MANDATORY when conformity is claimed | General | Standard | GOV-15 |
| DG-13 | Records management? | ISO 15489-1 principles | Where data constitutes records; text not fully read | Effort | RECOMMENDED | General | Standard | GOV-16 |
| DG-14 | Governing-body data governance? | ISO/IEC 38505-1 | Voluntary vocabulary; 2026 edition not visible | Low | OPTIONAL | General | Standard | GOV-14 |
| DG-15 | Metadata architecture? | Push or event-log; pull crawlers | LinkedIn and Uber moved toward event-based | Build effort | OPTIONAL | General | Case study | CASE-37, CASE-38 |
| DG-16 | Regulatory identifiers? | LEI where mandated; internal | Regulated reporting; GLEIF confirms the LEI is a 20-character code based on ISO 17442; character-position structure was not confirmed (note 22) | Fees | RECOMMENDED; regulator-mandated contexts could not be verified | Finance | Standard | GOV-24 |
| DG-17 | Financial message vocabulary? | ISO 20022 dictionary; proprietary | Where a scheme mandates it, not verified here | Mapping | OPTIONAL | Finance | Standard, unverified | GOV-23 (unverified) |

Notes: Governance standards prescribe accountability, not schema structures (note 08). Clause-level content of paid ISO standards was not read. Column-level ownership and quality SLAs are framework decisions.

## 21. ERP financial controls

Scope: general ledger OLTP, subledgers, consolidation and their warehouse copies. Evidence: note 18 and `catalog_18_erp_finance.json`.

| ID | Question | Options | When each applies | Trade-offs | Class | Scope | Evidence | Sources |
|---|---|---|---|---|---|---|---|---|
| FN-1 | At what grain is period status held? | Single flag per company; by ledger and application; by module or account type; by book or document type | All vendors with period records hold status finer than company; the chosen grain differs | Control precision against setup work | RECOMMENDED (finer than company; grain itself open) | OLTP (GL, subledger) | Multi-vendor | ERP-01, ERP-05, ERP-09, ERP-10, ERP-14, ERP-15, ERP-19 |
| FN-2 | Is the calendar definition separate from period status? | Shared calendar with per-entity status; one combined record | D365 copies a shared calendar to a ledger calendar per legal entity; Oracle keys status by ledger; SAP assigns a variant to company codes | Reuse against per-entity flexibility | RECOMMENDED | OLTP (GL) | Multi-vendor | ERP-01, ERP-05, ERP-09 |
| FN-3 | How are adjustment periods represented? | Separate periods sharing dates; none | SAP special periods 13 to 16; D365 closing periods; Oracle adjusting periods share the period-end date. NetSuite has no statement; Odoo and ERPNext none in pages read | [INFERENCE] a date no longer identifies a period, so warehouses cannot derive period from date alone. Oracle does not copy journals to adjusting periods on secondary ledgers with a different calendar | OPTIONAL | OLTP (GL), DW | Multi-vendor | ERP-01, ERP-05, ERP-06, ERP-09, ERP-10 |
| FN-4 | Is close a status write or an ordered process? | Ordered gated steps; status change only | NetSuite publishes an ordered dependency list; Oracle can block GL close on open subledgers and always blocks on pending intercompany | Close duration against control | RECOMMENDED | OLTP (GL, subledger) | Single vendor (Oracle Fusion and NetSuite share one owner) | ERP-05, ERP-06, ERP-14 |
| FN-5 | What does reopening a period do? | Reopen with cascade and justification; reopen with close rerun; no reopening | NetSuite reopens later closed periods and stores a justification; D365 reopens on-hold periods and needs a close rerun | Flexibility against repeated close work | RECOMMENDED (treat reopening as invalidating later close work) | OLTP (GL) | Multi-vendor | ERP-10, ERP-12, ERP-15 |
| FN-6 | Is an irreversible close offered? | Permanent close; reopenable only | Oracle and Odoo offer it; D365 offers it and advises against it (C-75) | Assurance against recoverability | OPTIONAL | OLTP (GL) | Multi-vendor (conflicting) | ERP-05, ERP-10, ERP-18 |
| FN-7 | Is fiscal-year status separate from period status? | Separate; combined | D365 blocks reversal after year-end close even with a period open | Extra state | OPTIONAL | OLTP (GL) | Single vendor | ERP-12 |
| FN-8 | Is P&L closing a separate object from period close? | Separate voucher or entry; same as period close | ERPNext's closing voucher neither erases history nor stops backdated entries; D365 and Odoo generate or post year-end entries separately | Clarity against more objects | OPTIONAL | OLTP (GL) | Multi-vendor | ERP-10, ERP-18, ERP-19 |
| FN-9 | Must a transaction carry the rate at its date? | Transaction-date rate; period or convention rate | The SEC Baxter order states ASC 830-20 measurement at the transaction-date rate and calls a mid-prior-month convention not in accordance with GAAP. IAS 21 rate rules were not read. [INFERENCE] a stored per-line rate is not stated by any source | Lookup against stored rate | MANDATORY (US GAAP issuers, measurement only; storage not prescribed) | OLTP (GL, subledger) | Standard | ERP-22 |
| FN-10 | Which rate roles exist per period? | Closing, average, historical and others; one rate | FAS 52 implies balance-sheet and weighted average rates; NetSuite stores three per period and subsidiary pair; D365 and SAP use rate types | Table size | RECOMMENDED | OLTP (GL), consolidation | Multi-vendor | ERP-03, ERP-11, ERP-16, ERP-22 |
| FN-11 | How are rates keyed and effective-dated? | Exact-day row per pair and type; most recent on or before, with a staleness limit | Oracle key is from currency, to currency, date and type; ERPNext picks the latest eligible record. SAP valid-from logic was not established (C-78) | Completeness against gaps | RECOMMENDED (key by pair, date, type); effective-dating open | OLTP (GL), DW | Multi-vendor | ERP-08, ERP-20 |
| FN-12 | How are inverse rates handled? | Store each direction; derive reciprocal | Oracle stores a generally reciprocal row [WF]; ERPNext says the inverse is not automatically equal and needs its own record; SAP presents direct and indirect quotation (C-77) | Rounding disagreement against storage | OPTIONAL; unresolved | OLTP (GL), DW | Multi-vendor (conflicting) | ERP-03, ERP-08, ERP-20 |
| FN-13 | Which amounts are held per line? | Transaction, entity and optional reporting amounts; one amount | D365 records accounting and reporting currency; ERPNext distinguishes three currencies; SAP allows up to eight additional currency types | Columns against reconciliation | RECOMMENDED | OLTP (GL, subledger) | Multi-vendor | ERP-03, ERP-09, ERP-20 |
| FN-14 | Is revaluation a recorded run? | Run record with separate rate date; ad hoc journals | D365 keeps run history with a separate rate date; NetSuite uses a period-end rate and says to lock first | Run bookkeeping | RECOMMENDED | OLTP (GL) | Multi-vendor | ERP-11, ERP-17 |
| FN-15 | Realized and unrealized differences? | Separate accounts; combined | D365, ERPNext, Odoo and NetSuite separate them | Chart of accounts | RECOMMENDED | OLTP (GL) | Multi-vendor | ERP-09, ERP-17, ERP-18, ERP-20 |
| FN-16 | Does revaluation reverse in the next period? | Reverse; carry forward | D365 GL does not; D365 AR and AP do. An older Oracle statement is a search snippet and is not relied on (C-76) | Comparability | OPTIONAL | OLTP (GL) | Single vendor | ERP-11, ERP-12 |
| FN-17 | Where do rounding differences go? | Defined account; per-line tolerance | ERPNext rounds per line, so totals can differ by small units; Oracle balances by legal entity including rounding | Balance discipline | OPTIONAL | OLTP (GL) | Multi-vendor | ERP-07, ERP-20 |
| FN-18 | Are currency translation paths transitive? | Direct per pair; through an intermediate entity | D365 translates directly from source currency and needs an intermediate company for a two-step path; NetSuite rates are per subsidiary pair | Setup against simplicity | OPTIONAL | Consolidation | Multi-vendor | ERP-13, ERP-16 |
| FN-19 | What precision do stored rates need? | Not established | No vendor page states a precision standard and no standard-setter page addresses it. D365's example display does not establish one | Not assessed | No classification; evidence gap | OLTP (GL), DW | Inference | Note 18 section 2.3 |
| FN-20 | May posted entries be altered? | Alter in place; change only with original content ascertainable | HGB 239(3) and AO 146(4) forbid changes that lose the original content or leave its timing uncertain. Mechanism is not prescribed | Correction cost against auditability | MANDATORY (Germany, commercial and tax books) | OLTP (GL, subledger), Germany | Standard | ERP-23 |
| FN-21 | How are posted errors corrected elsewhere? | New reversing or correcting entry; edit in place | Oracle, SAP document reversal, D365 and ERPNext correct by new entry. 15 USC 78m requires accurate books for US issuers but names no mechanism. Exceptions are in FN-24 | Volume against traceability | RECOMMENDED | OLTP (GL, subledger) | Multi-vendor | ERP-02, ERP-06, ERP-12, ERP-19 |
| FN-22 | Which reversal method? | Inverse entry; negative posting or change sign; switch debit and credit | SAP normal reversal raises figures, negative posting resets them; Oracle offers Change Sign and Switch Debit or Credit (C-74) | Debit and credit activity totals differ by method | OPTIONAL | OLTP (GL) | Multi-vendor | ERP-02, ERP-06 |
| FN-23 | Can a reversal be reversed? | Forbidden; allowed | Oracle forbids it; D365 allows it (C-73) | Audit trail shape | OPTIONAL | OLTP (GL) | Multi-vendor (conflicting) | ERP-06, ERP-12 |
| FN-24 | May generated vouchers be deleted on year-end reversal? | Delete with history record; post reversing voucher | D365 year-end reversal deletes vouchers and NetSuite Delete keeps only a record of deletion. No source says whether generated balances count as books under HGB 239(3) (C-72) | Simplicity against non-alteration | No classification; unresolved for Germany | OLTP (GL), Germany | Standard, inference | ERP-10, ERP-12, ERP-15, ERP-23 |
| FN-25 | What attributes does a reversal carry? | Separate date, method, reason; default to the original | D365 allows a different reversal date; SAP requires a reason; Oracle sets date and method | Input effort | RECOMMENDED | OLTP (GL) | Multi-vendor | ERP-02, ERP-06, ERP-12 |
| FN-26 | What decides reversal eligibility? | State beyond the entry; entry only | Settlement, transfer and fiscal status in D365; non-reversal journal and unfrozen source in Oracle | Rule surface | RECOMMENDED | OLTP (GL, subledger) | Multi-vendor | ERP-06, ERP-12 |
| FN-27 | Can subledger entries exist before GL transfer? | Yes, tracked until transferred; synchronous only | D365 blocks some reversals until transfer; Oracle treats untransferred items as close exceptions | Reconciliation | RECOMMENDED | OLTP (subledger to GL) | Multi-vendor | ERP-06, ERP-12 |
| FN-28 | Is a ledger hash chain needed? | Hash chain; none | Odoo's is the only control seen; no law or standard read requires hashing for general ledgers. KSA e-invoice hashing is a separate rule (LG-9) | Complexity against tamper evidence | OPTIONAL | OLTP (GL) | Single vendor | ERP-18 |
| FN-29 | What must US issuers show about books and the journal population? | Accurate books with internal controls; less | 15 USC 78m(b)(2) and 17 CFR 240.13b2-1 bind issuers. PCAOB staff text on journal-entry completeness says it is not a Board rule. [INFERENCE] row-level immutability is not stated | Control cost | MANDATORY (US issuers: accurate books and internal controls, no mechanism); RECOMMENDED (journal completeness support) | OLTP (GL), US | Standard | ERP-24, ERP-25 |
| FN-30 | How is triangulation handled? | Not established | No vendor page opened describes it; D365 mentions it only in a training objective seen in a search snippet | Not assessed | No classification; evidence gap | OLTP (GL) | Inference | Note 18 section 6 |

Notes: SAP findings rest on training pages because product documentation rendered empty. The FASB Codification and PCAOB standards returned 403, so ASC 830 is known only through a superseded statement and an SEC order, and AS 2401 only through a staff publication that says it is not a rule. IAS 21 and IFRS 10 full text was not read; the IFRS page gives concepts and no rate rules. Oracle Fusion and NetSuite are products of one owner, so they count as a single vendor for FN-4. Most vendor pages were read through a summarising fetch tool.

## 22. Legal numbering, retention and erasure

Scope: invoicing systems, archives, backups and analytical copies. Evidence: note 19 and `catalog_19_legal_retention.json`. This is research input and not legal advice. Each row binds only the stated jurisdiction and population.

| ID | Question | Options | When each applies | Trade-offs | Class | Scope | Evidence | Sources |
|---|---|---|---|---|---|---|---|---|
| LG-1 | EU invoice number requirement? | Sequential, series-based, unique; other | VAT Directive Art. 226(2). The text does not say whether sequential excludes gaps | Series design against contention | MANDATORY (EU VAT-registered suppliers) | OLTP (invoicing), EU | Standard | LEG-01, TEN-39 |
| LG-2 | Germany? | Number issued once, one or more series | UStG 14(4) point 4. Gap treatment rests on a search snippet of BMF pages, so it is not relied on | See LG-12 | MANDATORY (German invoice issuers); gaps unsettled | OLTP (invoicing), Germany | Standard; gap position unverified | LEG-04, LEG-06 (unverified) |
| LG-3 | France? | Chronological and continuous per series, no duplicates | BOFiP and Service-Public use the strictest wording found; no official tolerance for gaps or guidance on spoiled numbers was found. Article 242 nonies A was not opened | Gap prevention cost | MANDATORY (French invoice issuers) | OLTP (invoicing), France | Standard | LEG-07, LEG-08 |
| LG-4 | Italy? | Progressive, uniquely identifying; date may contribute | Art. 21 DPR 633/1972 per Risoluzione 1/E of 2013; gaps not addressed | See LG-12 | MANDATORY (Italian invoice issuers); gaps unsettled | OLTP (invoicing), Italy | Standard | LEG-10 |
| LG-5 | Spain? | Sequential per series; separate series for corrective invoices | RD 1619/2012 [WF]. VERI*FACTU requires chained billing records, which is not a rule on invoice number gaps. RD 1007/2023 scope and dates were not researched | Series count | MANDATORY (Spanish invoice issuers; chained records only for software in RD 1007/2023 scope); invoice number gaps unsettled | OLTP (invoicing), Spain | Standard | LEG-11, LEG-12 |
| LG-6 | United Kingdom? | Sequential, unique, one or more series | Notice 700/21 and VATREC5010. HMRC tolerates a break if the spoiled invoice is kept or the break explained; VATREC records HMRC's view and is not legislation | Explanation records | MANDATORY (UK VAT-registered suppliers, numbering); gap tolerance is regulator guidance | OLTP (invoicing), UK | Standard | LEG-13, LEG-14 |
| LG-7 | Pakistan? | Serial number; FBR number and QR for integrated persons | Sales Tax Act s23(1), Rules 150Q onward; every adjustment or cancellation is recorded. Start dates conflict in the sources; gaps not found | Authority integration | MANDATORY (Pakistani registered persons; e-invoice items for FBR-notified integrated persons) | OLTP (invoicing), Pakistan | Standard | LEG-18, LEG-19 |
| LG-8 | UAE? | Sequential number, or unique number showing order; UUID in e-invoicing | VAT Executive Regulation Art. 59(1)(d). A random identifier alone would not show order ([INFERENCE]). Amendment citation conflicts; gaps not found | Identifier design | MANDATORY (UAE VAT registrants; UUID where e-invoicing applies) | OLTP (invoicing), UAE | Standard | LEG-22, LEG-24 |
| LG-9 | Saudi Arabia? | Sequential unique number, counter never reused, previous-invoice hash | ZATCA guidance; rejected documents consume a counter value and stay in the hash chain. The technical guideline read is dated November 2022 | Append-only event series ([INFERENCE]) | MANDATORY (KSA VAT and e-invoicing scope) | OLTP (invoicing), KSA | Standard | LEG-25, LEG-26, LEG-27 |
| LG-10 | Must corrective invoices cite the corrected invoice? | Cite its sequential number; none | ViDA Art. 226(16) from 1 July 2030 where transposed; national status not researched. A self-reference is [INFERENCE] | Linking effort | MANDATORY from 1 July 2030 where transposed (EU) | OLTP (invoicing), EU | Standard | LEG-02 |
| LG-11 | Integrity of stored invoices? | Authenticity, integrity and legibility through storage; none | VAT Directive Art. 233(1), through business controls or other means | Archive design | MANDATORY (EU VAT-registered suppliers) | OLTP, archive, EU | Standard | LEG-01 |
| LG-12 | How are unused invoice numbers handled? | Record each with a reason; ignore | UK guidance, French continuity wording and ZATCA's counter rule. No single rule can be derived; [INFERENCE] meet the strictest rule applying per legal entity (C-79) | Bookkeeping | RECOMMENDED | OLTP (invoicing) | Standard, inference | LEG-07, LEG-14, LEG-26 |
| LG-13 | Plain database sequence for legal numbers? | Avoid; use | Sequences can skip on rollback, and France has continuity wording | Contention on the series | RECOMMENDED (avoid where gap sensitivity applies) | OLTP (invoicing) | Standard, single vendor, inference | LEG-07, TEN-33 |
| LG-14 | How is the numbering series modelled? | Per legal entity and document type; global | [INFERENCE] from the laws allowing one or more series; Spain requires separate corrective series | More series | RECOMMENDED | OLTP (invoicing) | Inference, standard | LEG-01, LEG-04, LEG-11, LEG-13 |
| LG-15 | Local number, authority number, UUID, counter, previous hash? | Separate items; combined | Pakistan, UAE and KSA regimes each require the items; separate attributes are [INFERENCE] | Columns | MANDATORY (data items in those regimes); RECOMMENDED (separate attributes) | OLTP (invoicing), Pakistan, UAE, KSA | Standard | LEG-19, LEG-24, LEG-26, LEG-27 |
| LG-16 | Retention in Germany? | Tax: books 10, vouchers 8, others 6 years; VAT invoices 8; commercial by HGB 257 | From end of the calendar year. Tax periods do not lapse while documents matter for open assessments. An 8-year voucher transition was not read. Post-migration carrier rule in AO 147 | Archive scope | MANDATORY (Germany) | OLTP, archive, Germany | Standard | LEG-04, LEG-05, ERP-23 |
| LG-17 | Retention in France? | Tax 6 years; commercial 10 years | LPF L102 B via BOFiP. The commercial period rests on a search snippet and CNIL's billing reference, and the longer period applies where both apply ([INFERENCE]) | Longer retention | MANDATORY (France, tax period); commercial period unverified | OLTP, archive, France | Standard; commercial part unverified | LEG-09, LEG-36 |
| LG-18 | Retention in the UK? | VAT records at least 6 years; Companies Act private 3, public 6 | Notice 700/21; CA 2006 s388(4). HMRC may allow shorter periods on request | Differs by law | MANDATORY (UK) | OLTP, archive, UK | Standard | LEG-13, LEG-15 |
| LG-19 | Retention in the US for general business? | Limitation-driven periods | IRS guidance: 3 years generally, longer in listed cases, indefinite if no or fraudulent return; employment tax at least 4 years. Not a flat rule | Case-by-case schedule | RECOMMENDED (US federal income and employment tax, as limitation-driven guidance) | OLTP, archive, US | Standard | LEG-16 |
| LG-20 | Retention in Pakistan? | Sales and income tax 6 years or until proceedings end; companies 10 financial years | STA s24, ITO s174(3) with a final proviso, Companies Act s220(5) | Proceedings tracking | MANDATORY (Pakistan) | OLTP, archive, Pakistan | Standard | LEG-18, LEG-20, LEG-21 |
| LG-21 | Retention in the UAE? | Tax records 5 years, real estate 7; extensions for disputes and audits | Cabinet Decision 74 of 2023 Art. 3; e-invoice data follows the same periods | Extension tracking | MANDATORY (UAE) | OLTP, archive, UAE | Standard | LEG-23, LEG-24 |
| LG-22 | Retention in Saudi Arabia? | At least 6 years; capital assets and real estate longer; in-Kingdom and Arabic | ZATCA guide; a workstation exception exists for centralised systems abroad | Data location | MANDATORY (KSA VAT scope) | OLTP, archive, KSA | Standard | LEG-25 |
| LG-23 | How is a retention schedule keyed? | Record class, jurisdiction, start event and hold; flat period | Periods differ by class and start event; Germany, UAE and Pakistan extend on open matters. Italian and Spanish periods were not researched | Schedule upkeep | RECOMMENDED; [INFERENCE] on design; extension duties are MANDATORY only in the cited jurisdictions | OLTP, archive, DW | Standard, inference | LEG-05, LEG-18, LEG-20, LEG-23 |
| LG-24 | Broker-dealer records? | Audit-trail system or non-rewriteable storage | 17 CFR 240.17a-4 only; not general SaaS | Storage cost | MANDATORY (US broker-dealers only) | OLTP, archive, US | Standard | LEG-17 |
| LG-25 | Stored card authentication data? | Not retained after authorization; retained | PCI DSS 3.3.1 per the v4.0 SAQ D, even if encrypted; v4.0.1 text not read. Logs and backups are in scope ([INFERENCE]) | None material | MANDATORY (PCI DSS scope) | OLTP, logs | Standard | SEC-17, LEG-30, LEG-31 |
| LG-26 | Is key destruction erasure? | Treat as erasure; treat as exposure reduction | No regulator text found accepts it; see SC-14 | Key system complexity | OPTIONAL; not settled | Backups, event logs | Inference | LEG-33, LEG-34 |
| LG-27 | Deletion under California law? | Delete and notify the chain; none | Civil Code 1798.105(c) and (d), read from the CPPA copy; regulation section 7022 permits delay on backups until restore or next use | Propagation effort | MANDATORY (CCPA scope) | General, backups, California | Standard | LEG-28, LEG-29 |
| LG-28 | Erasure and backups in the EU and UK? | Record requests outside backups and reapply on restore; delete at once | EDPB, Dutch AP and ICO all address backups; how long undue delay runs is not settled (C-81). ICO and AP are read from Wayback captures | Register upkeep | RECOMMENDED (EU, UK); the undue-delay limit is unsettled | General, backups | Standard | LEG-32, LEG-33, LEG-35 |
| LG-29 | Field-level treatment of retained records? | Keep only fields under legal obligation; keep whole record | Art. 17(3) applies to the extent necessary. Which fields is a legal judgment | Split design | RECOMMENDED; [INFERENCE] on design | OLTP, DW, lakehouse | Standard, inference | LEG-03 |
| LG-30 | Is erasure verified and demonstrable? | Verified and evidenced; assumed | EDPB CEF report recommendation; a regulator report and not a legal text | Evidence records | RECOMMENDED (EU) | General | Standard | LEG-32 |

Notes: Note 19 labels IRS retention MANDATORY; LG-19 is RECOMMENDED because the page describes limitation-driven guidance and no statute was read. The design-implication table in note 19 is inference from law, so its MANDATORY entries are held here only where the law itself carries the obligation. Germany LG-2 gap treatment and France's commercial period are unverified and not relied on. Member-state ViDA transposition, Italian and Spanish retention, and PCI DSS v4.0.1 text were not researched or could not be read.

---

## Lifecycle view

Decision IDs refer to the tables above. Each stage lists the decisions that bind it, what evidence it produces, and how it differs by workload. Artefact names describe inputs for later standards and prescribe no schema.

| Stage | Purpose | Binding decisions | MANDATORY items in scope | Evidence artefacts to produce | Main evidence gaps |
|---|---|---|---|---|---|
| Data Modeling | Decide what exists and who owns it | AP-1, AP-6, LP-1, LP-2, ER-1 to ER-9, NF-1 to NF-5, RP-1, RP-2, RP-3, MT-2 | ER-3 (relational), NF-1 (relational system of record), RP-3 and RP-4 (Kimball method) | Conceptual and logical model, relationship cardinalities, grain statements | No source defines a cross-methodology decision table |
| Schema Design | Choose types, keys, constraints, tenancy and physical levers | LP-7 to LP-10, RI-1 to RI-14, NM-1 to NM-13, DT-1 to DT-16, IX-1 to IX-9, MT-1 to MT-8, MT-11, MT-17, FN-1 to FN-3, FN-10 to FN-13, LG-14, LG-15 | RI-1, RI-2, RI-6, NM-3, NM-5, DT-1, IX-9, MT-1, MT-3, LG-15 (named regimes) | Design record with engine annex and departures from normal form | Rate precision, triangulation |
| Data Validation | Enforce or check values at write and load | RI-5 to RI-12, DV-1, DV-2, DV-3, DV-5, PL-9, TS-8 | RI-6, DV-2 | Constraint inventory and declared versus enforced list | Defect-catch comparison of layers |
| Transactions | Protect concurrency and side effects | TX-1 to TX-15, AP-5, MT-5, FN-20 to FN-27, LG-1 to LG-13 | TX-1, TX-2, TX-3, TX-12 (EU), TX-13 (MongoDB), FN-20 (Germany), FN-29 (US issuers), LG-1 to LG-11 (per jurisdiction) | Isolation map per transaction class, invariant catalogue | Current Jepsen results for SQL Server and Oracle |
| ETL/ELT | Move and transform data reproducibly | PL-1 to PL-17, MG-13, MG-14, AP-8 | PL-4, PL-7 (CDC), PL-11 (compaction) | Pipeline contract, reprocessing plan, interval and key definitions | No official reconciliation-table prescription |
| Data Quality | Prove correctness and completeness | DV-1 to DV-15, TS-8, TS-13 to TS-17, RP-13, TX-11, FN-27 | DV-2 | Quality rules, severity tiers, reconciliation records | Numeric SLOs, debit and credit assertions |
| Governance | Assign accountability and control change | DG-1 to DG-17, MG-1 to MG-7, SC-4, SC-5, AH-13, AH-15, FN-4 to FN-6, LG-16 to LG-30 | SC-4 and SC-5 (GDPR), AH-13 and AH-15 (GDPR, Part 11), DG-12 (when claimed), LG-16 to LG-25 and LG-27 (per jurisdiction or population) | Ownership metadata, classification, retention schedule, erasure records, contracts | ISO clause-level text; backup erasure timing; invoice gap rules in several countries |
| Reporting | Serve trustworthy analytical access | RP-1 to RP-14, NF-7, IX-7, RI-11, SC-15 | RP-3, RP-4, RP-5 (Kimball); RP-11 (Data Vault) | Mart specifications, metric definitions | Like-for-like modeling benchmarks |
| Monitoring | Detect failure and drift | TS-6, DV-4, DV-12, BK-5, BK-11, SM-7, DG-8 | BK-5 | Freshness and volume signals, CDC lag, restore results, drift reports | Alerting and incident SLA figures |

### Workload differences by lifecycle stage

| Stage | OLTP | OLAP | Data warehouse | Lakehouse | Streaming |
|---|---|---|---|---|---|
| Data Modeling | Entities, aggregates and normalization (NF-2, TX-4) | Query shapes and star schema (RP-1) | Grain, conformed dimensions, integration decision (RP-2, RP-3) | Per-layer models (LP-10, AP-8) | Event identity and keys (PL-12) |
| Schema Design | Declared constraints, tenant keys (RI-1, RI-2, MT-3) | Column and clustering levers (IX-7) | RELY constraints, surrogates (RI-12, RP-6) | Enforced and informational split (AP-4, RI-11) | Payload schema with event time (PL-13) |
| Data Validation | Engine constraints (DV-2) | Post-build tests (TS-8) | Reconciliation (DV-7) | Promotion gates (DV-3) | Registry compatibility and DLQ (DV-5, DV-14) |
| Transactions | Isolation, retry, outbox (TX-1, TX-3, TX-8) | Not applicable to reads in the Azure trait table | Load atomicity per platform | Single-table ACID (note 04) | Idempotent sinks (PL-4, PL-16) |
| ETL/ELT | CDC source requirements (PL-6, PL-7) | Refresh strategy (RP-8) | Idempotent loads, late-arriving data (PL-4, RP-14) | Medallion hops, raw landing (AP-8, PL-10) | Replay and watermarks (PL-3, PL-14) |
| Data Quality | Constraint violations, drift (TS-6) | Metric tests (DV-12) | Audit dimension and GL tie-out (DV-8) | WAP and expectations (DV-3) | Lag, duplicates, DLQ counts (DV-5) |
| Governance | Migrations, roles, retention (MG-1, SC-1, AH-13) | Semantic definitions (RP-9) | Contracts on marts (DV-10) | Catalog policies (SC-15) | Compatibility policy (DV-14, MG-14) |
| Reporting | Primary or replica endpoints (RP-10, TX-14) | Aggregates (RP-8) | Marts (RP-1) | Gold layer (RP-1, AP-8) | Near-real-time views ([INFERENCE]) |
| Monitoring | Drift, restore tests (TS-6, BK-5) | Query cost ([INFERENCE]) | Freshness, volume (DV-12) | Lineage and freshness (DG-8) | CDC lag, consumer lag ([Debezium PostgreSQL connector](https://debezium.io/documentation/reference/stable/connectors/postgresql.html), PIPE-06) |

### Evidence strength across the lifecycle

[INFERENCE] Strongest evidence: Schema Design semantics, Transactions, and recovery within Monitoring, where standards, foundational papers and multi-vendor documentation agree. Moderate: ETL/ELT and Data Validation, where vendor and project documentation converge without standards. Fiscal periods, exchange-rate tables and reversals moved from inference to multi-vendor product evidence, with German and US law binding only in scope. Weakest: Data Quality targets, Reporting benchmarks, rate precision, triangulation, consolidation elimination rules, and every performance comparison in note 23 that has no independent evidence (keys, RLS, foreign keys, Data Vault), which remain judgments.

Decision rows that the framework should treat as open until further evidence exists: RI-3, RI-13, NM-6, RP-6, MT-5, MT-9, AH-11, MG-2, FN-6, FN-11 (effective-dating), FN-12, FN-19, FN-24, FN-30, LG-2 to LG-5 and LG-7 to LG-8 (gap treatment), LG-26, LG-28 (timing), and C-41, C-79 and C-84 in the companion register. These are carried forward as open questions, not defaults.
