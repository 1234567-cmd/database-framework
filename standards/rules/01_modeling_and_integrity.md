# Stage 2 Standards: Modeling and Integrity

Covers architecture principles (ARC), logical and physical modeling (MOD), entity relationship design (ERD), normalization and denormalization (NRM) and relational integrity (INT), for ERP, financial, SaaS and data engineering systems. Built from existing research only, in the format of `../RULE_FORMAT.md`. The machine-readable copy is `../registry/01_modeling_and_integrity.json`.

"Framework exception approver" is the one role for framework-level exceptions (decision H1); no person has been named yet. The owner accepted all defaults on 2026-11-08, so decided rules are organizational decisions. [INFERENCE] marks reasoning not stated by a source.

## Enforcement by workload

The matrix asks for enforcement to be stated by workload rather than as one rule.

| Workload | Where integrity is enforced | Rules |
|---|---|---|
| OLTP system of record | Database engine | ARC-003, INT-001, INT-002, INT-009 |
| OLTP, sharded or shadow-table online schema change | Compensating controls under an approved exception | INT-003 |
| Data warehouse | Platform where enforced, otherwise pipeline tests and load lookups | ARC-004, DQA-004, INT-015 |
| Lakehouse | Platform where enforced, otherwise pipeline tests | ARC-004, DQA-004 |
| Streaming | No rule in this group. The matrix areas covered here have no streaming rows. | none |

## Architecture principles

### ARC-001: Documented data store selection

**Each system SHOULD select its data store type from a documented assessment of access pattern, consistency need, scale, read and write ratio, and operational maturity.**

| Field | Value |
|---|---|
| level | RECOMMENDED |
| status | active |
| decision_ref | null |
| scope | all |
| applies_when | A new system or a new data store is proposed. |
| rationale | A store chosen by habit fits its workload poorly, and adding stores without need brings the premature fragmentation Azure warns about. |
| exceptions | Deviation with a recorded reason, approved by the framework exception approver. |
| engine_notes | none |
| evidence | CLOUD-01, CLOUD-17, PERF-38, design_decision_matrix.md#AP-1 |
| evidence_strength | multi_vendor |
| check_method | manual_review |
| check_description | The design record names the store type and addresses each of the five assessment factors. |
| lifecycle_stage | Data Modeling |

### ARC-002: Separate transactional and analytical workloads

**Analytical workloads SHOULD run on a store separate from the OLTP system of record.**

| Field | Value |
|---|---|
| level | RECOMMENDED |
| status | active |
| decision_ref | null |
| scope | OLTP, OLAP |
| applies_when | A system of record also serves reporting or analytics. |
| rationale | Analytical scans interfere with transactional load, and row and column storage are optimized for different work. |
| exceptions | A row store with a columnar replica (HTAP) is permitted for operational analytics. A read replica is permitted only where the reports do not feed decisions. Other deviations need a recorded reason approved by the framework exception approver. |
| engine_notes | HTAP evidence supports claims about architecture, not named products: BENCH-14 anonymizes commercial systems and BENCH-13 is a vendor measuring its own product. |
| evidence | PERF-38, PERF-39, CLOUD-16, PERF-02, PERF-49, BENCH-14, BENCH-13, design_decision_matrix.md#AP-2 |
| evidence_strength | standard |
| check_method | manual_review |
| check_description | The architecture record shows where analytical queries run and, if they share or replicate the system of record, which permitted exception applies. |
| lifecycle_stage | Data Modeling |

### ARC-003: Engine enforcement of integrity in systems of record

**An OLTP system of record MUST declare in the database engine every integrity rule the engine can enforce.**

| Field | Value |
|---|---|
| level | MANDATORY |
| status | active |
| decision_ref | null |
| scope | OLTP |
| applies_when | Transactional systems of record on engines that enforce the constraint type concerned, including ERP, financial and SaaS core tables. |
| rationale | Rules held only in application code are bypassed by other writers and can lose races, which leads to silent corruption. |
| exceptions | Application-only enforcement is permitted only under a documented infrastructure limit, such as sharding or shadow-table online schema change (conflict C-08). The framework exception approver approves each case. |
| engine_notes | Foreign keys are governed by INT-002. Analytical platforms are out of scope and are covered by ARC-004. |
| evidence | MSOM-08, PGMY-01, MSOM-02, DES-18, design_decision_matrix.md#AP-3, architecture_comparison.md#C-08 |
| evidence_strength | multi_vendor |
| check_method | manual_review |
| check_description | Each business invariant listed for the model is traced to an engine constraint, or to an approved infrastructure exception. |
| lifecycle_stage | Schema Design |

### ARC-004: Record what analytical platforms enforce

**Each data warehouse or lakehouse platform in use MUST have a record of which constraint types it enforces, and a constraint it does not enforce MUST NOT be treated as a data guarantee.**

| Field | Value |
|---|---|
| level | MANDATORY |
| status | active |
| decision_ref | null |
| scope | data_warehouse, lakehouse |
| applies_when | Any analytical platform on which constraints can be declared. |
| rationale | Declared keys that are only informational let duplicates and orphans through while appearing to prevent them. |
| exceptions | none |
| engine_notes | Snowflake standard tables and Databricks enforce NOT NULL and CHECK only, with PK, FK and UNIQUE informational. Redshift enforces NOT NULL and treats PK, FK and UNIQUE as informational. For DQ-03, the per-adapter table could not be attributed reliably from the fetched text, so use it only for its explicit statements. |
| evidence | LAKE-02, LAKE-09, DQ-03, ENG-23, design_decision_matrix.md#AP-4, architecture_comparison.md#C-04 |
| evidence_strength | multi_vendor |
| check_method | catalog_query |
| check_description | A per-platform enforcement record exists, and every declared but unenforced key has a substitute test (see DQA-004). |
| lifecycle_stage | Schema Design |

### ARC-005: Strong consistency for coordinated invariants

**An OLTP system of record SHOULD use strong consistency, through a single writer or consensus, for invariants that require coordination.**

| Field | Value |
|---|---|
| level | RECOMMENDED |
| status | active |
| decision_ref | null |
| scope | OLTP |
| applies_when | Invariants whose validity depends on concurrent writers. [INFERENCE] Uniqueness, balances and document numbering are such invariants. |
| rationale | Eventual consistency with later compensation can accept conflicting writes that break the invariant before anyone can correct them. |
| exceptions | Eventual consistency with compensation is permitted for invariants shown not to need coordination, with a recorded reason approved by the framework exception approver. |
| engine_notes | Conflict C-63 concerns how CAP is framed and is unresolved as theory, but practical guidance agrees. PACELC system classifications are not used. |
| evidence | TXN-14, TXN-15, TXN-20, design_decision_matrix.md#AP-5, architecture_comparison.md#C-63 |
| evidence_strength | standard |
| check_method | manual_review |
| check_description | The design lists invariants that need coordination and states how each is protected. |
| lifecycle_stage | Transactions |

### ARC-006: Single owner per schema

**Each OLTP database schema SHOULD be owned by exactly one bounded context.**

| Field | Value |
|---|---|
| level | RECOMMENDED |
| status | active |
| decision_ref | null |
| scope | OLTP |
| applies_when | Systems divided into domains or modules, such as ERP modules. |
| rationale | Without one owner, changes are uncoordinated and models from different domains blur together. |
| exceptions | A small Shared Kernel changed only by consultation is permitted. Other deviations need a recorded reason approved by the framework exception approver. |
| engine_notes | none |
| evidence | ARCH-01, ARCH-02, design_decision_matrix.md#AP-6, data_modeling_approaches.md#10. Domain-Driven Design |
| evidence_strength | single_vendor |
| check_method | catalog_query |
| check_description | Every schema has one recorded owning context, and shared schemas are recorded as Shared Kernel. |
| lifecycle_stage | Governance |

### ARC-007: Storage boundary per service

**A service MAY start with private tables or a private schema and MAY move to its own server when throughput, storage type or deployment needs justify it.**

| Field | Value |
|---|---|
| level | OPTIONAL |
| status | active |
| decision_ref | null |
| scope | OLTP |
| applies_when | Service or modular designs where storage is divided by service. |
| rationale | Splitting servers early gives up cross-boundary ACID and joins for isolation that may not be needed. |
| exceptions | Deviation with a recorded reason, approved by the framework exception approver. |
| engine_notes | No quantitative threshold for separating servers exists in the sources. |
| evidence | ARCH-04, ARCH-05, design_decision_matrix.md#AP-7, data_modeling_approaches.md#18.9 Physical strength of the bounded context |
| evidence_strength | multi_vendor |
| check_method | manual_review |
| check_description | Where a server split exists, the record states which of the three reasons applies. |
| lifecycle_stage | Data Modeling |

### ARC-008: Number of analytical layers

**An analytical platform MAY use one presentation layer for simple sources and MAY add integration or medallion layers where audit or multi-source reconciliation needs them.**

| Field | Value |
|---|---|
| level | OPTIONAL |
| status | active |
| decision_ref | null |
| scope | data_warehouse, lakehouse |
| applies_when | Designing warehouse or lakehouse layering. |
| rationale | Each hop adds latency and cost, while too few hops lose traceability for audited or multi-source data. |
| exceptions | Deviation with a recorded reason, approved by the framework exception approver. |
| engine_notes | Medallion is a layering pattern, not a data model, and is not a requirement (conflict C-07). |
| evidence | LAKE-01, LAKE-06, DWM-14, CLOUD-21, design_decision_matrix.md#AP-8, architecture_comparison.md#C-07 |
| evidence_strength | multi_vendor |
| check_method | manual_review |
| check_description | The layer list states the purpose of each layer. |
| lifecycle_stage | ETL/ELT |

### ARC-009: Analytical data ownership model

**Analytical data MAY be owned centrally, by domains as data products, or by a hybrid of the two.**

| Field | Value |
|---|---|
| level | OPTIONAL |
| status | active |
| decision_ref | null |
| scope | data_warehouse, lakehouse |
| applies_when | Deciding who owns analytical data. |
| rationale | Domain ownership adds integration cost and central ownership can become a bottleneck, so the fit depends on the organization. |
| exceptions | Deviation with a recorded reason, approved by the framework exception approver. |
| engine_notes | Hybrid is what adopters converge on. Evidence is case studies, and ARCH-16 has an interest as the originator's then employer. |
| evidence | ARCH-14, ARCH-15, ARCH-16, ARCH-19, ARCH-20, design_decision_matrix.md#AP-9 |
| evidence_strength | case_study |
| check_method | manual_review |
| check_description | The governance record names the ownership model and an owner for each analytical dataset. |
| lifecycle_stage | Governance |

### ARC-010: Portable SQL where it exists

**Designs SHOULD prefer standard SQL constructs over vendor dialect where the engines in use support them.**

| Field | Value |
|---|---|
| level | RECOMMENDED |
| status | provisional |
| decision_ref | null |
| scope | all |
| applies_when | The design may need to run on more than one engine. |
| rationale | Vendor-only constructs raise the cost of moving engines, although standard features were adopted slowly and engine capability can justify dialect. |
| exceptions | Deviation with a recorded reason, approved by the framework exception approver. |
| engine_notes | ISO/IEC 9075 text was not read, so no clause-level claim is made and feature support must be confirmed per engine. |
| evidence | GOV-06, design_decision_matrix.md#AP-10, database_design_standards.md#12.4 Standards position |
| evidence_strength | inference |
| check_method | manual_review |
| check_description | Vendor-specific constructs in the design are identified and each has a stated reason. |
| lifecycle_stage | Schema Design |

## Logical and physical modeling

### MOD-001: Separate logical and physical design

**Each data model SHOULD be developed as separate conceptual, logical and physical levels.**

| Field | Value |
|---|---|
| level | RECOMMENDED |
| status | active |
| decision_ref | null |
| scope | all |
| applies_when | Any new model or major model change. |
| rationale | Mixing logical meaning with engine representation ties users to access paths and raises the cost of later change. |
| exceptions | Deviation with a recorded reason, approved by the framework exception approver. |
| engine_notes | The physical level carries engine types, indexes, partitioning and controlled redundancy. |
| evidence | GOV-27, DES-01, design_decision_matrix.md#LP-1, database_design_standards.md#2.2 Statements, data_modeling_approaches.md#2. Foundations shared by all approaches |
| evidence_strength | standard |
| check_method | manual_review |
| check_description | Design records exist for each level and the physical model traces back to the logical one. |
| lifecycle_stage | Data Modeling |

### MOD-002: Modeling start point by data paradigm

**OLTP models SHOULD begin from normalized entities on relational stores and from access patterns on key-value, document and key-distributed stores.**

| Field | Value |
|---|---|
| level | RECOMMENDED |
| status | active |
| decision_ref | null |
| scope | OLTP |
| applies_when | Designing an operational store. |
| rationale | Applying one paradigm's method to the other loses either query flexibility or predictable performance. |
| exceptions | Deviation with a recorded reason, approved by the framework exception approver. |
| engine_notes | Access-pattern modeling applies on DynamoDB, Cosmos DB and MongoDB, and to key design on Spanner. Conflicts C-01 and C-06 are resolved by paradigm and operability. |
| evidence | CLOUD-06, CLOUD-20, MSOM-15, CLOUD-11, design_decision_matrix.md#LP-2, architecture_comparison.md#C-01, architecture_comparison.md#C-06 |
| evidence_strength | multi_vendor |
| check_method | manual_review |
| check_description | The design states the paradigm and shows entities or a list of access patterns accordingly. |
| lifecycle_stage | Data Modeling |

### MOD-003: Record physical departures from the logical model

**Every physical departure from the logical model SHOULD be documented with its reason and the dependency it introduces.**

| Field | Value |
|---|---|
| level | RECOMMENDED |
| status | active |
| decision_ref | null |
| scope | OLTP, data_warehouse |
| applies_when | The physical model stops short of the logical model, or adds redundancy. |
| rationale | Undocumented redundancy becomes invisible, so copies drift and no one knows what must stay consistent. |
| exceptions | Deviation with a recorded reason, approved by the framework exception approver. |
| engine_notes | none |
| evidence | DES-02, DES-01, design_decision_matrix.md#LP-3 |
| evidence_strength | standard |
| check_method | manual_review |
| check_description | Each departure between logical and physical models has a recorded reason and a stated dependency. |
| lifecycle_stage | Data Modeling |

### MOD-004: Supertype and subtype mapping

**A subtype hierarchy MAY use class-table mapping when a subtype attribute must be required or a subtype takes part in a foreign key, and single-table mapping otherwise.**

| Field | Value |
|---|---|
| level | OPTIONAL |
| status | active |
| decision_ref | B20 |
| scope | OLTP |
| applies_when | A supertype and subtype relationship is being mapped to tables. |
| rationale | One table loses required-value enforcement on subtype columns, joined tables cost joins, and concrete tables lose foreign keys to the supertype. |
| exceptions | Concrete-table mapping is permitted where no shared foreign key target is needed. Other deviations need a recorded reason approved by the framework exception approver. |
| engine_notes | No independent or engine-neutral benchmark exists, so this default is a judgment. Hibernate favours joined tables for constraints, and EF Core defaults to one table and warns on joined-table performance. Native exclusive-arc enforcement was not covered. On PostgreSQL, the community wiki advises against table inheritance for subtypes (single source). |
| evidence | DES-14, GOV-27, THIN-03, THIN-04, THIN-05, PGMY-10, design_decision_matrix.md#LP-4, design_decision_matrix.md#LP-5, design_decision_matrix.md#ER-7, architecture_comparison.md#C-85 |
| evidence_strength | multi_vendor |
| check_method | manual_review |
| check_description | Each hierarchy has a recorded mapping and reason, and required subtype attributes are enforced under the mapping chosen. |
| lifecycle_stage | Schema Design |

### MOD-005: Hierarchy storage pattern

**A hierarchy MAY be stored as an adjacency list, a materialized path or an engine-native hierarchy type, provided the choice records the read and write pattern and how cycles are handled.**

| Field | Value |
|---|---|
| level | OPTIONAL |
| status | active |
| decision_ref | null |
| scope | OLTP |
| applies_when | The model contains parent and child trees, such as charts of accounts or organizational units. |
| rationale | Recursive queries loop on cycles unless these are detected, and each pattern trades query complexity against write cost. |
| exceptions | Deviation with a recorded reason, approved by the framework exception approver. |
| engine_notes | Adjacency is foreign-key enforceable. PostgreSQL offers ltree for indexed path queries. SQL Server hierarchyid is reported faster for subtree queries and slower for moving non-leaf nodes, with no figures published, and it does not enforce relationships as a foreign key does. Closure table and nested set have no opened source and are not assessed here. |
| evidence | THIN-07, design_decision_matrix.md#LP-6, database_design_standards.md#2.1 Findings |
| evidence_strength | single_vendor |
| check_method | manual_review |
| check_description | Each hierarchy records its pattern, the read and write reason, and its cycle handling. |
| lifecycle_stage | Schema Design |

### MOD-006: Typed columns for core attributes

**Keys, monetary values and attributes used for filtering SHOULD be typed columns and SHOULD NOT be held in JSON documents or entity-attribute-value tables.**

| Field | Value |
|---|---|
| level | RECOMMENDED |
| status | superseded |
| decision_ref | null |
| superseded_by | TYP-024 |
| scope | OLTP |
| applies_when | Core business data. JSON remains available for sparse or externally defined attributes, such as tenant custom fields. |
| rationale | Values outside typed columns cannot take the normal constraints, and are harder to index and validate. |
| exceptions | Deviation with a recorded reason, approved by the framework exception approver. |
| engine_notes | DES-13 supports only the publisher-listed name of the entity-attribute-value antipattern. Its legitimate-use text was not read. Superseded by TYP-024 under OR-24. |
| evidence | PGMY-04, MSOM-15, DES-13, DES-20, design_decision_matrix.md#LP-7, database_design_standards.md#11. Schema anti-patterns |
| evidence_strength | multi_vendor |
| check_method | schema_lint |
| check_description | No key, money or filter attribute appears only within a document or a generic attribute table. |
| lifecycle_stage | Schema Design |

### MOD-007: Large binary object placement

**Large binary objects MAY be stored in the database or in an object store with a reference, chosen by size and lifecycle.**

| Field | Value |
|---|---|
| level | OPTIONAL |
| status | provisional |
| decision_ref | null |
| scope | OLTP |
| applies_when | The model stores files or other large objects. |
| rationale | Storing in the database affects row size, while external storage loses transactional integrity and shared backup scope. |
| exceptions | Deviation with a recorded reason, approved by the framework exception approver. |
| engine_notes | No fetched detail supports either option. |
| evidence | DES-13, DES-20, design_decision_matrix.md#LP-8, database_design_standards.md#11. Schema anti-patterns |
| evidence_strength | inference |
| check_method | manual_review |
| check_description | The design records the placement and the size and lifecycle reason. |
| lifecycle_stage | Schema Design |

### MOD-008: Physical levers in analytical design

**Analytical physical designs SHOULD specify distribution, sort, partition and clustering keys where the platform offers them.**

| Field | Value |
|---|---|
| level | RECOMMENDED |
| status | active |
| decision_ref | null |
| scope | OLAP, data_warehouse |
| applies_when | Massively parallel and cloud warehouses. |
| rationale | On these platforms such keys take the place of B-trees, so leaving them unplanned raises scan and join cost. |
| exceptions | Deviation with a recorded reason, approved by the framework exception approver. |
| engine_notes | B-tree column-order guidance does not transfer to clustering keys (conflict C-29). |
| evidence | CLOUD-08, CLOUD-13, LAKE-10, design_decision_matrix.md#LP-9, architecture_comparison.md#C-29 |
| evidence_strength | multi_vendor |
| check_method | catalog_query |
| check_description | Each large analytical table has its chosen physical keys recorded, or a stated reason for none. |
| lifecycle_stage | Schema Design |

### MOD-009: Mutable physical layout on lakehouse tables

**Lakehouse tables SHOULD use mutable clustering or hidden partitioning where the platform supports it.**

| Field | Value |
|---|---|
| level | RECOMMENDED |
| status | active |
| decision_ref | null |
| scope | lakehouse |
| applies_when | The platform offers liquid clustering, hidden partitions or an equivalent. |
| rationale | A fixed layout has to be rebuilt when query patterns change. |
| exceptions | Deviation with a recorded reason, approved by the framework exception approver. |
| engine_notes | Documented on Databricks liquid clustering and Iceberg. Availability is platform-dependent. |
| evidence | LAKE-03, PIPE-10, design_decision_matrix.md#LP-10 |
| evidence_strength | multi_vendor |
| check_method | catalog_query |
| check_description | Tables on supporting platforms use the mutable layout, or have a recorded reason for a fixed one. |
| lifecycle_stage | Schema Design |

### MOD-010: Published interface over internal schema

**Consumers outside the owning system SHOULD read from a published interface and SHOULD NOT read the internal OLTP schema directly.**

| Field | Value |
|---|---|
| level | RECOMMENDED |
| status | provisional |
| decision_ref | null |
| scope | OLTP, data_warehouse |
| applies_when | Data is consumed outside the owning team. |
| rationale | Direct use of internal tables couples consumers to the model, so internal changes break them. |
| exceptions | Deviation with a recorded reason, approved by the framework exception approver. |
| engine_notes | none |
| evidence | ARCH-14, ARCH-15, PIPE-20, design_decision_matrix.md#LP-11 |
| evidence_strength | inference |
| check_method | manual_review |
| check_description | External consumers are listed against a published interface, and none reads internal tables directly. |
| lifecycle_stage | Governance |

## Entity relationship design

### ERD-001: Explicit cardinality and optionality

**Each relationship SHOULD have its cardinality and optionality stated before keys are assigned.**

| Field | Value |
|---|---|
| level | RECOMMENDED |
| status | active |
| decision_ref | null |
| scope | all |
| applies_when | Conceptual and logical modeling. |
| rationale | Assigning keys before relationships are understood leads to late rework. |
| exceptions | Deviation with a recorded reason, approved by the framework exception approver. |
| engine_notes | none |
| evidence | DES-03, GOV-27, design_decision_matrix.md#ER-1 |
| evidence_strength | standard |
| check_method | manual_review |
| check_description | Every relationship in the model shows cardinality and optionality. |
| lifecycle_stage | Data Modeling |

### ERD-002: One notation per model

**A model MAY use Chen, IDEF1X, crow's foot or UML notation, provided one notation is used consistently within that model.**

| Field | Value |
|---|---|
| level | OPTIONAL |
| status | provisional |
| decision_ref | null |
| scope | all |
| applies_when | Producing entity relationship diagrams. |
| rationale | Mixed notation makes cardinality and optionality harder to read. No evidence favors one notation for outcomes, so the consistency requirement is a judgment. |
| exceptions | Deviation with a recorded reason, approved by the framework exception approver. |
| engine_notes | The IDEF1X federal mandate is reported withdrawn, and the withdrawal date rests on Wikipedia. The origin of crow's foot rests on two opened pages and the 1976 paper is unread, so it is not asserted. |
| evidence | GOV-27, GOV-28, THIN-02, design_decision_matrix.md#ER-2, database_design_standards.md#2.4 Contested |
| evidence_strength | inference |
| check_method | manual_review |
| check_description | Each diagram uses a single named notation. |
| lifecycle_stage | Data Modeling |

### ERD-003: Association table for many-to-many

**A many-to-many relationship in a relational store MUST be realized as an association table.**

| Field | Value |
|---|---|
| level | MANDATORY |
| status | active |
| decision_ref | null |
| scope | OLTP, data_warehouse |
| applies_when | Relational stores. |
| rationale | A foreign key alone cannot represent the relationship, and the usual workarounds cannot be constrained. |
| exceptions | none |
| engine_notes | Non-relational stores are out of scope. Whether the join row needs its own identity is not settled by these sources (see ERD-004). |
| evidence | DES-03, DES-14, GOV-27, THIN-06, design_decision_matrix.md#ER-3 |
| evidence_strength | standard |
| check_method | manual_review |
| check_description | No many-to-many relationship in the logical model lacks an association table in the physical model. |
| lifecycle_stage | Schema Design |

### ERD-004: Association table primary key

**An association table SHOULD use the composite of its two foreign keys as primary key unless the row is referenced elsewhere or has its own lifecycle.**

| Field | Value |
|---|---|
| level | RECOMMENDED |
| status | provisional |
| decision_ref | null |
| scope | OLTP |
| applies_when | Association tables in relational OLTP stores. |
| rationale | An unneeded surrogate adds an index and can allow duplicate pairs unless a further constraint is added. |
| exceptions | Deviation with a recorded reason, approved by the framework exception approver. |
| engine_notes | DES-13 supports only a publisher-listed antipattern name. Distributed engines can add their own composite key requirements. |
| evidence | DES-13, DES-20, DES-03, design_decision_matrix.md#ER-4, database_design_standards.md#4.5 Statements |
| evidence_strength | inference |
| check_method | schema_lint |
| check_description | Association tables have a composite key of both foreign keys, or a recorded reason for a surrogate. |
| lifecycle_stage | Schema Design |

### ERD-005: Identity of dependent entities

**A dependent entity SHOULD carry its parent key in its identity, either within the primary key or as a unique constraint on parent key and local key alongside a surrogate.**

| Field | Value |
|---|---|
| level | RECOMMENDED |
| status | active |
| decision_ref | null |
| scope | OLTP |
| applies_when | Weak entities and identifying relationships, such as document lines under a document. |
| rationale | Without the parent in its identity, a child row can duplicate its local key within a parent. |
| exceptions | Deviation with a recorded reason, approved by the framework exception approver. |
| engine_notes | The parent key in the child primary key comes from Chen and IDEF1X. The surrogate plus unique form is [INFERENCE] for ORM-centric schemas. |
| evidence | DES-03, GOV-27, design_decision_matrix.md#ER-5, database_design_standards.md#2.2 Statements |
| evidence_strength | standard |
| check_method | schema_lint |
| check_description | Each dependent table has a key or unique constraint that includes the parent key. |
| lifecycle_stage | Schema Design |

### ERD-006: No polymorphic reference columns

**A column SHOULD NOT reference several parent tables through a type and identifier pair.**

| Field | Value |
|---|---|
| level | RECOMMENDED |
| status | provisional |
| decision_ref | null |
| scope | OLTP |
| applies_when | Modeling a reference that may point to more than one kind of parent. |
| rationale | No foreign key can be declared for the pair, so the reference cannot be enforced. |
| exceptions | A supertype table or one foreign key per target are the alternatives. Other deviations need a recorded reason approved by the framework exception approver. |
| engine_notes | DES-13 supports only the publisher-listed name, and its remedies were not read. Rails ships this pattern, which shows real-world tolerance. |
| evidence | DES-13, DES-14, design_decision_matrix.md#ER-6, database_design_standards.md#11. Schema anti-patterns |
| evidence_strength | inference |
| check_method | schema_lint |
| check_description | No table has a type and identifier column pair acting as a reference without an approved deviation. |
| lifecycle_stage | Schema Design |

### ERD-007: References across bounded contexts

**A reference between bounded contexts in separate stores SHOULD be held as an identifier, while a reference between contexts within one database SHOULD keep its foreign key until the boundary is approved for physical separation.**

| Field | Value |
|---|---|
| level | RECOMMENDED |
| status | active |
| decision_ref | A7 |
| scope | OLTP |
| applies_when | A reference crosses an aggregate or bounded context boundary. |
| rationale | Foreign keys across a boundary couple contexts, while bare identifiers lose engine integrity and can leave orphans. |
| exceptions | Shared Kernel tables may keep foreign keys. Other deviations need a recorded reason approved by the framework exception approver. |
| engine_notes | No source states a ban on foreign keys across contexts. It is [INFERENCE], while modular monoliths retain cross-table ACID (ARCH-04). This rule limits INT-002 only where a boundary is approved for separation. |
| evidence | ARCH-01, ARCH-03, ARCH-04, design_decision_matrix.md#ER-8, data_modeling_approaches.md#10. Domain-Driven Design |
| evidence_strength | single_vendor |
| check_method | manual_review |
| check_description | Each cross-context reference is recorded as identifier or foreign key, with the boundary status. |
| lifecycle_stage | Schema Design |

### ERD-008: Reference tables for amended code lists

**A code list that is amended over time SHOULD be modeled as a reference table with effective dating and SHOULD NOT be embedded as literals.**

| Field | Value |
|---|---|
| level | RECOMMENDED |
| status | provisional |
| decision_ref | null |
| scope | all |
| applies_when | Codes such as ISO 4217 currency codes that change over time. |
| rationale | Literal lists need a schema change for each amendment and cannot show which codes were valid at a past date. |
| exceptions | Deviation with a recorded reason, approved by the framework exception approver. |
| engine_notes | ISO 4217 shows that such lists are amended. Using a table is [INFERENCE] and is not stated by that standard. Enum limits are engine-specific. |
| evidence | GOV-20, DES-11, design_decision_matrix.md#ER-9 |
| evidence_strength | inference |
| check_method | manual_review |
| check_description | Amended code lists are held in reference tables with validity dates. |
| lifecycle_stage | Data Modeling |

### ERD-009: Discriminator on complete subtype clusters

**A complete subtype cluster MAY make its discriminator a required attribute, and a model that claims IDEF1X conformance adopts this as a condition of that claim.**

| Field | Value |
|---|---|
| level | OPTIONAL |
| status | active |
| decision_ref | null |
| scope | OLTP |
| applies_when | Subtype clusters. Binding only for models claiming IDEF1X conformance. |
| rationale | An optional discriminator on a complete cluster leaves it unclear which subtype a row belongs to. |
| exceptions | Deviation with a recorded reason, approved by the framework exception approver. |
| engine_notes | The standard is reported withdrawn. |
| evidence | GOV-27, design_decision_matrix.md#ER-10 |
| evidence_strength | standard |
| check_method | manual_review |
| check_description | Models claiming IDEF1X conformance have required discriminators on complete clusters. |
| lifecycle_stage | Data Modeling |

## Normalization and denormalization

### NRM-001: Atomic values in relational base tables

**Relational system-of-record base tables MUST NOT store repeating groups, delimited lists or numbered-column arrays.**

| Field | Value |
|---|---|
| level | MANDATORY |
| status | active |
| decision_ref | null |
| scope | OLTP |
| applies_when | Relational system-of-record base tables. Analytical nested types, raw landing layers and document stores are out of scope. |
| rationale | Values inside a list cannot be constrained, joined or indexed individually. |
| exceptions | none |
| engine_notes | Nested data is a documented design choice on BigQuery, and in document stores. Atomicity for lakehouse Silver and Gold layers is unresolved in the research and is not covered here. |
| evidence | DES-01, DES-02, DES-13, design_decision_matrix.md#NF-1, database_design_standards.md#3.4 Contested |
| evidence_strength | standard |
| check_method | schema_lint |
| check_description | No base-table column holds a delimited list, and no table has numbered columns for one repeating fact. |
| lifecycle_stage | Schema Design |

### NRM-002: Third normal form as OLTP default

**OLTP base tables whose non-key fields are updated SHOULD be in third normal form.**

| Field | Value |
|---|---|
| level | RECOMMENDED |
| status | active |
| decision_ref | null |
| scope | OLTP |
| applies_when | Relational system-of-record tables whose non-key fields are updated. |
| rationale | Without it, repeated facts drift on update, and facts cannot be stored or kept without an unrelated row. |
| exceptions | Stopping short is permitted where performance requirements justify it, as Kent allows, with a recorded reason (MOD-003) approved by the framework exception approver. |
| engine_notes | BCNF is a matrix option, but its primary text was not read, so this rule does not require it. |
| evidence | DES-02, CLOUD-16, MSOM-14, PERF-17, design_decision_matrix.md#NF-2, data_modeling_approaches.md#6. Third Normal Form |
| evidence_strength | standard |
| check_method | manual_review |
| check_description | Reviewers confirm that no non-key field depends on part of a key or on another non-key field, or that a recorded deviation exists. |
| lifecycle_stage | Data Modeling |

### NRM-003: Check higher normal forms for multivalued facts

**A table that holds two or more independent multivalued facts SHOULD be checked against fourth and fifth normal form.**

| Field | Value |
|---|---|
| level | RECOMMENDED |
| status | active |
| decision_ref | null |
| scope | OLTP |
| applies_when | A table combines independent multivalued facts. |
| rationale | Combining such facts multiplies rows and makes blank fields ambiguous. |
| exceptions | Deviation with a recorded reason, approved by the framework exception approver. |
| engine_notes | Based on Kent's exposition only. The primary papers were not read. |
| evidence | DES-02, design_decision_matrix.md#NF-3 |
| evidence_strength | standard |
| check_method | manual_review |
| check_description | Tables with several multivalued facts have a recorded 4NF and 5NF review. |
| lifecycle_stage | Data Modeling |

### NRM-004: Conditions for denormalized read shapes

**An analytical or read-model structure MAY be denormalized when the workload is read-dominant, the redundancy has one controlled write path, and the dependency is documented.**

| Field | Value |
|---|---|
| level | OPTIONAL |
| status | provisional |
| decision_ref | null |
| scope | OLAP, data_warehouse, lakehouse |
| applies_when | Read-dominant shapes fed by a controlled load. Not a licence for OLTP base tables (see NRM-005). |
| rationale | Unmanaged redundancy produces read shapes that disagree with their source. |
| exceptions | Deviation with a recorded reason, approved by the framework exception approver. |
| engine_notes | The three conditions are [INFERENCE] from Codd and Kent. No vendor page states them. |
| evidence | DES-02, DES-01, DWM-01, design_decision_matrix.md#NF-4, architecture_comparison.md#C-02 |
| evidence_strength | inference |
| check_method | manual_review |
| check_description | Each denormalized structure names its write path and source dependency. |
| lifecycle_stage | Reporting |

### NRM-005: Keep OLTP base tables normalized

**OLTP base tables SHOULD NOT be denormalized for read speed where a read model or columnar replica can serve the need.**

| Field | Value |
|---|---|
| level | RECOMMENDED |
| status | active |
| decision_ref | null |
| scope | OLTP |
| applies_when | Read performance pressure on a system of record. |
| rationale | Redundant copies in base tables create inconsistency for writers, and read models contain that cost outside the write path. |
| exceptions | Denormalization is permitted with a measured need and a single maintaining path, approved by the framework exception approver. |
| engine_notes | SQL Server indexed views are permitted with a warned DML cost (conflict C-19). No source quantifies OLTP denormalization cost. |
| evidence | PERF-38, PERF-56, PERF-02, PERF-04, design_decision_matrix.md#NF-5, architecture_comparison.md#C-19 |
| evidence_strength | standard |
| check_method | manual_review |
| check_description | Any redundant column in a base table has a measured need and a named maintaining path. |
| lifecycle_stage | Schema Design |

### NRM-006: Warehouse integration shape

**A warehouse MAY add a 3NF or Data Vault integration layer when it has many sources or an audit need, and MAY omit one for few stable sources.**

| Field | Value |
|---|---|
| level | OPTIONAL |
| status | superseded |
| decision_ref | null |
| superseded_by | RPT-002 |
| scope | data_warehouse |
| applies_when | Choosing the warehouse integration layer. Cross-reference decision RP-2. |
| rationale | An integration layer adds load complexity, while omitting one leaves multi-source data unreconciled. |
| exceptions | Deviation with a recorded reason, approved by the framework exception approver. |
| engine_notes | No independent benchmark of Data Vault against star exists (conflict C-86), so the choice is a judgment. Superseded by RPT-002 under OR-23. |
| evidence | DWM-14, DWM-08, design_decision_matrix.md#NF-6, design_decision_matrix.md#RP-2, architecture_comparison.md#C-67, architecture_comparison.md#C-86 |
| evidence_strength | multi_vendor |
| check_method | manual_review |
| check_description | The warehouse design records whether an integration layer exists and why. |
| lifecycle_stage | Data Modeling |

### NRM-007: Star before snowflake

**Warehouse presentation layers SHOULD use a star schema rather than a snowflake unless there is a recorded clear reason.**

| Field | Value |
|---|---|
| level | RECOMMENDED |
| status | active |
| decision_ref | B24 |
| scope | OLAP, data_warehouse |
| applies_when | Dimensional presentation layers. |
| rationale | Snowflaked dimensions add joins for users and tools. |
| exceptions | Deviation with a recorded reason, approved by the framework exception approver. |
| engine_notes | BigQuery nested and repeated fields are a documented alternative for hierarchical one-to-many data (conflict C-05). Wide-table questions are outside this rule (decision RP-1, conflict C-84). |
| evidence | DWM-14, DWM-01, CLOUD-21, design_decision_matrix.md#NF-7, architecture_comparison.md#C-05 |
| evidence_strength | multi_vendor |
| check_method | manual_review |
| check_description | Snowflaked dimensions in presentation layers have a recorded reason. |
| lifecycle_stage | Reporting |

### NRM-008: Sixth normal form for volatile data

**A warehouse MAY use Anchor Modeling or similar 6NF structures for highly volatile, sparse and heavily historized data.**

| Field | Value |
|---|---|
| level | OPTIONAL |
| status | active |
| decision_ref | null |
| scope | data_warehouse |
| applies_when | Volatile, sparse, heavily historized attributes. |
| rationale | Table counts and reliance on optimizer support are high, so it suits specialist cases only. |
| exceptions | Deviation with a recorded reason, approved by the framework exception approver. |
| engine_notes | Evidence is the authors' own paper. Primary 6NF texts were not read. |
| evidence | DWM-16, design_decision_matrix.md#NF-8, data_modeling_approaches.md#8. Anchor Modeling |
| evidence_strength | single_vendor |
| check_method | manual_review |
| check_description | Use of 6NF structures has a recorded volatility and sparsity reason. |
| lifecycle_stage | Data Modeling |

### NRM-009: Embed or reference in document stores

**Document models SHOULD embed data read together within size limits and SHOULD reference high-cardinality, unbounded or independently existing data.**

| Field | Value |
|---|---|
| level | RECOMMENDED |
| status | active |
| decision_ref | null |
| scope | OLTP |
| applies_when | Operational document stores only. |
| rationale | Unbounded arrays and bloated documents degrade reads and updates, and duplicated data is expensive to update. |
| exceptions | Deviation with a recorded reason, approved by the framework exception approver. |
| engine_notes | From MongoDB documentation. Conflict C-01 is resolved by paradigm. No source evaluates this for ERP or ledgers. |
| evidence | MSOM-15, design_decision_matrix.md#NF-9, architecture_comparison.md#C-01 |
| evidence_strength | single_vendor |
| check_method | manual_review |
| check_description | Embedded collections have a stated growth bound, and referenced data is identified. |
| lifecycle_stage | Schema Design |

### NRM-010: One controlled path for redundant data

**Each redundant value SHOULD be maintained through one controlled mechanism, such as a generated column or a single ETL or refresh process.**

| Field | Value |
|---|---|
| level | RECOMMENDED |
| status | provisional |
| decision_ref | null |
| scope | all |
| applies_when | Any redundant or derived stored value. |
| rationale | Several writers of one derived value let copies diverge. |
| exceptions | Deviation with a recorded reason, approved by the framework exception approver. |
| engine_notes | none |
| evidence | DES-01, DES-02, design_decision_matrix.md#NF-10 |
| evidence_strength | inference |
| check_method | manual_review |
| check_description | Each derived column names exactly one maintaining mechanism. |
| lifecycle_stage | Schema Design |

## Relational integrity

### INT-001: Primary key on every base table

**Every OLTP system-of-record base table MUST declare a primary key.**

| Field | Value |
|---|---|
| level | MANDATORY |
| status | active |
| decision_ref | null |
| scope | OLTP |
| applies_when | System-of-record base tables. |
| rationale | Without a declared identity, rows cannot be reliably addressed, and logical replication of updates and deletes fails. |
| exceptions | none |
| engine_notes | InnoDB creates a hidden key if none is declared. PostgreSQL requires a replica identity for logical replication of updates and deletes. Citus requires the distribution column in primary keys. The MANDATORY level is the matrix author's elevation from strong vendor wording, based on Codd and replication requirements. |
| evidence | DES-01, PGMY-01, PGMY-12, MSOM-02, TEN-28, PERF-44, design_decision_matrix.md#RI-1 |
| evidence_strength | standard |
| check_method | schema_lint |
| check_description | No system-of-record base table lacks a declared primary key. |
| lifecycle_stage | Schema Design |

### INT-002: Enforced foreign keys on non-sharded OLTP

**Non-sharded OLTP systems of record MUST enforce references between tables with database foreign keys.**

| Field | Value |
|---|---|
| level | MANDATORY |
| status | active |
| decision_ref | A7 |
| scope | OLTP |
| applies_when | Non-sharded relational systems of record. |
| rationale | Application-only checks are fallible and leave orphan rows. |
| exceptions | Infrastructure limits such as sharding or shadow-table online schema change permit omission under INT-003, approved by the framework exception approver. Boundaries approved for separation are governed by ERD-007. |
| engine_notes | Foreign keys are not supported on user-partitioned InnoDB tables. gh-ost does not support them. PlanetScale support is unsharded only. Citus requires the distribution column. Foreign key cost at scale is a judgment: no independent evidence at scale and no MySQL measurement exist. |
| evidence | PGMY-01, MSOM-02, MSOM-08, DES-18, DES-17, PGMY-16, CASE-23, PERF-44, design_decision_matrix.md#RI-2, architecture_comparison.md#C-08 |
| evidence_strength | multi_vendor |
| check_method | schema_lint |
| check_description | Each referencing column on a non-sharded system has a foreign key or a recorded INT-003 exception. |
| lifecycle_stage | Schema Design |

### INT-003: Compensating controls where foreign keys are unavailable

**Where foreign keys cannot be enforced, the reference column SHOULD be kept and indexed, orphan rows SHOULD be audited on a schedule, and the risk SHOULD be recorded.**

| Field | Value |
|---|---|
| level | RECOMMENDED |
| status | active |
| decision_ref | A7 |
| scope | OLTP |
| applies_when | An approved INT-002 exception applies, such as sharding or shadow-table online schema change. |
| rationale | Without these controls, orphans accumulate and go unnoticed. |
| exceptions | Deviation with a recorded reason, approved by the framework exception approver. |
| engine_notes | Controls are drawn from PlanetScale's published mitigations. Risk acceptance is [INFERENCE]. Alibaba prohibits foreign keys in its MySQL guidelines, which is the opposing position in C-08. |
| evidence | DES-17, DES-22, CASE-23, design_decision_matrix.md#RI-2, architecture_comparison.md#C-08, database_design_standards.md#5.2 Statements |
| evidence_strength | single_vendor |
| check_method | pipeline_test |
| check_description | Each exception has an indexed reference column, a scheduled orphan audit and a recorded risk acceptance. |
| lifecycle_stage | Data Quality |

### INT-004: Reference column matches its key

**A reference column SHOULD have the same data type and width as the key it references.**

| Field | Value |
|---|---|
| level | RECOMMENDED |
| status | active |
| decision_ref | null |
| scope | OLTP |
| applies_when | Any reference column, whether or not a foreign key is declared. |
| rationale | A narrower reference fails once the key outgrows it, as in the Buildkite 32-bit incident. |
| exceptions | Deviation with a recorded reason, approved by the framework exception approver. |
| engine_notes | MySQL enforces matching size and sign for fixed-precision types. Other engines were not confirmed. |
| evidence | PGMY-14, database_design_standards.md#4.5 Statements, database_design_standards.md#11. Schema anti-patterns |
| evidence_strength | single_vendor |
| check_method | schema_lint |
| check_description | Reference columns match the type and width of the referenced key. |
| lifecycle_stage | Schema Design |

### INT-005: Explicit delete and update action per foreign key

**Each foreign key SHOULD declare its delete and update actions explicitly.**

| Field | Value |
|---|---|
| level | RECOMMENDED |
| status | active |
| decision_ref | null |
| scope | OLTP |
| applies_when | Every foreign key. |
| rationale | Implicit defaults vary by engine, so behaviour can differ silently. |
| exceptions | Deviation with a recorded reason, approved by the framework exception approver. |
| engine_notes | PostgreSQL defaults to NO ACTION, which can be deferred, and RESTRICT cannot. In MySQL/InnoDB, NO ACTION equals RESTRICT and SET DEFAULT is rejected. InnoDB cascades do not fire triggers. Cascades are hidden from binlog consumers. |
| evidence | DES-18, PGMY-01, PGMY-14, MSOM-02, design_decision_matrix.md#RI-3, database_design_standards.md#5.3 Universal vs engine-specific |
| evidence_strength | single_vendor |
| check_method | schema_lint |
| check_description | Every foreign key has reviewed delete and update actions stated. |
| lifecycle_stage | Schema Design |

### INT-006: Default referential action

**A foreign key SHOULD use CASCADE only for strict composition, RESTRICT or NO ACTION for independent objects, and SET NULL only for optional relationships.**

| Field | Value |
|---|---|
| level | RECOMMENDED |
| status | active |
| decision_ref | A8 |
| scope | OLTP |
| applies_when | Choosing the action for a foreign key. |
| rationale | Cascades can cause accidental mass deletion, while always restricting leaves cleanup to application code. |
| exceptions | Deviation with a recorded reason, approved by the framework exception approver. |
| engine_notes | Sources disagree and none settles it (conflict C-09). This default is [INFERENCE], with the split also seen in the PostgreSQL entry. GitLab runs database-owned data on PostgreSQL, and PlanetScale and Alibaba come from sharded MySQL. |
| evidence | DES-18, DES-17, DES-22, PGMY-01, design_decision_matrix.md#RI-3, architecture_comparison.md#C-09 |
| evidence_strength | case_study |
| check_method | manual_review |
| check_description | Each CASCADE is justified as composition, and each other action fits the stated relationship type. |
| lifecycle_stage | Schema Design |

### INT-007: Deferrable constraints

**A constraint MAY be deferrable when reference cycles or bulk insert order require it and the engine supports deferral.**

| Field | Value |
|---|---|
| level | OPTIONAL |
| status | active |
| decision_ref | null |
| scope | OLTP |
| applies_when | Cycles or bulk ordering. Check engine support first. |
| rationale | Immediate checks can block valid multi-row changes, while deferral reduces portability. |
| exceptions | Deviation with a recorded reason, approved by the framework exception approver. |
| engine_notes | Re-check needed: text marked [WF] in the research was read only through a summarizing fetch and is not confirmed against the raw page. Supported on PostgreSQL for UNIQUE, PRIMARY KEY, foreign key and EXCLUDE. Oracle supports deferral, and such constraints cannot be altered in place. MySQL/InnoDB has no deferral. The SQL Server CREATE TABLE grammar shows no deferral syntax [WF], which is known only from absence. |
| evidence | PGMY-01, PGMY-14, MSOM-08, ENG-10, ENG-15, design_decision_matrix.md#RI-4 |
| evidence_strength | multi_vendor |
| check_method | manual_review |
| check_description | Deferrable constraints have a recorded cycle or load-order reason and a supporting engine. |
| lifecycle_stage | Transactions |

### INT-008: NOT NULL by default

**Columns SHOULD be NOT NULL unless absence has a documented meaning.**

| Field | Value |
|---|---|
| level | RECOMMENDED |
| status | active |
| decision_ref | null |
| scope | all |
| applies_when | Modeled tables. Raw landing layers that accept source data as received are excluded (conflict C-53). |
| rationale | Undefined NULLs bring three-valued logic and ambiguous meaning into queries. |
| exceptions | Deviation with a recorded reason, approved by the framework exception approver. |
| engine_notes | Primary key columns are NOT NULL on every engine. |
| evidence | PGMY-01, PERF-17, design_decision_matrix.md#RI-5, database_design_standards.md#7.5 NULL, architecture_comparison.md#C-53 |
| evidence_strength | multi_vendor |
| check_method | schema_lint |
| check_description | Each nullable column has a documented meaning for NULL. |
| lifecycle_stage | Schema Design |

### INT-009: CHECK paired with NOT NULL

**A column whose CHECK rule must always hold MUST also be NOT NULL.**

| Field | Value |
|---|---|
| level | MANDATORY |
| status | active |
| decision_ref | null |
| scope | all |
| applies_when | Engines enforcing CHECK, for rules that must hold for every row. |
| rationale | A CHECK passes when its expression is NULL, so a NULL value escapes the rule. |
| exceptions | none |
| engine_notes | Confirmed for PostgreSQL and MySQL. Behaviour on SQL Server, Oracle and analytical platforms was not captured, and the pairing is safe regardless. |
| evidence | PGMY-01, PGMY-15, design_decision_matrix.md#RI-6, database_design_standards.md#5.3 Universal vs engine-specific |
| evidence_strength | multi_vendor |
| check_method | schema_lint |
| check_description | Columns under an always-true CHECK are NOT NULL, including for composite conditions. |
| lifecycle_stage | Schema Design |

### INT-010: State NULL treatment in uniqueness rules

**A uniqueness rule over a nullable column SHOULD state its intended NULL treatment and how each engine in use implements it.**

| Field | Value |
|---|---|
| level | RECOMMENDED |
| status | superseded |
| decision_ref | null |
| superseded_by | TYP-034 |
| scope | OLTP |
| applies_when | Unique constraints or indexes over nullable columns. |
| rationale | Engines differ, so a rule assumed to allow one NULL or many can behave otherwise after a move. |
| exceptions | none |
| engine_notes | Re-check needed: text marked [WF] in the research was read only through a summarizing fetch and is not confirmed against the raw page. No portable default exists (conflict C-83). PostgreSQL treats NULLs as distinct by default, with an option to change this. MySQL permits many NULLs [WF]. SQL Server allows one NULL per column in a UNIQUE constraint [WF]. Oracle has a composite-specific rule [WF], from a page reporting Release 26. A SQL Server unique filtered index is [INFERENCE], not a documented example. Superseded by TYP-034 under OR-21. |
| evidence | PGMY-01, ENG-05, ENG-10, ENG-15, design_decision_matrix.md#RI-7, architecture_comparison.md#C-83 |
| evidence_strength | multi_vendor |
| check_method | manual_review |
| check_description | Each unique rule on a nullable column records the intended NULL behaviour per engine. |
| lifecycle_stage | Schema Design |

### INT-011: No-overlap rules for periods

**A rule that periods must not overlap for one business key SHOULD be declared in the database where the engine supports it.**

| Field | Value |
|---|---|
| level | RECOMMENDED |
| status | active |
| decision_ref | null |
| scope | OLTP |
| applies_when | Effective-dated data, such as rates or prices, on a supporting engine. |
| rationale | Overlapping periods make it ambiguous which row applied at a given time. |
| exceptions | On engines without support, cross-row enforcement under INT-012 is permitted. |
| engine_notes | PostgreSQL offers exclusion constraints and, from version 18, WITHOUT OVERLAPS. MySQL has no exclusion constraint. Support on other engines was not captured. SQL:2011 is known through its committee authors, and the ISO text was not read. |
| evidence | PGMY-01, GOV-06, PERF-16, design_decision_matrix.md#RI-8 |
| evidence_strength | standard |
| check_method | schema_lint |
| check_description | Effective-dated tables on supporting engines declare the no-overlap rule. |
| lifecycle_stage | Schema Design |

### INT-012: Cross-table integrity rules

**A rule that spans rows or tables MAY be enforced with a trigger or other engine mechanism because a CHECK cannot safely reference other rows.**

| Field | Value |
|---|---|
| level | OPTIONAL |
| status | active |
| decision_ref | null |
| scope | OLTP |
| applies_when | An invariant that a single-row constraint cannot express. |
| rationale | A CHECK that reads other rows gives unsafe results, and application-only logic is open to races. |
| exceptions | Deviation with a recorded reason, approved by the framework exception approver. |
| engine_notes | On PostgreSQL, the wiki says rules should not be used. On InnoDB, cascaded foreign key actions do not fire triggers. |
| evidence | PGMY-01, PGMY-10, PGMY-14, design_decision_matrix.md#RI-9, database_design_standards.md#5.2 Statements |
| evidence_strength | single_vendor |
| check_method | manual_review |
| check_description | Each cross-table invariant names its enforcement mechanism and known bypasses. |
| lifecycle_stage | Data Validation |

### INT-013: Default dimension rows over magic literals

**Warehouse dimensional models SHOULD represent missing references with explicit default dimension rows and SHOULD NOT use magic literal values.**

| Field | Value |
|---|---|
| level | RECOMMENDED |
| status | active |
| decision_ref | H2 |
| scope | data_warehouse |
| applies_when | Dimensional fact and dimension tables. |
| rationale | Magic literals are aggregated or filtered as real values and so give wrong totals. |
| exceptions | A documented end-of-time value on a period column is a distinct case and must be declared. |
| engine_notes | Within Kimball-method models, default rows for fact foreign keys are mandatory by that method (RP-5). SQL Server temporal tables use 9999-12-31 for open rows. The home rule for fact foreign keys is RPT-006. |
| evidence | DWM-01, DWM-02, design_decision_matrix.md#RI-10, database_design_standards.md#7.5 NULL |
| evidence_strength | single_vendor |
| check_method | pipeline_test |
| check_description | Fact references resolve to a real or default dimension row, and no undeclared literal stands in for unknown. |
| lifecycle_stage | Data Quality |

### INT-014: Test warehouse key uniqueness

**Declared logical keys on warehouse and lakehouse tables SHOULD be verified by uniqueness and not-null tests in the pipeline.**

| Field | Value |
|---|---|
| level | RECOMMENDED |
| status | superseded |
| decision_ref | null |
| superseded_by | DQA-004 |
| scope | data_warehouse, lakehouse |
| applies_when | Platforms where keys are not enforced. |
| rationale | Declaration alone does not prevent duplicate keys. |
| exceptions | Deviation with a recorded reason, approved by the framework exception approver. |
| engine_notes | Key declarations do not enforce on Snowflake standard tables or Databricks. Pipeline MERGE keys are an alternative control. Superseded by DQA-004 under OR-22. |
| evidence | LAKE-19, DQ-03, LAKE-02, LAKE-09, ENG-23, design_decision_matrix.md#RI-11, architecture_comparison.md#C-04 |
| evidence_strength | multi_vendor |
| check_method | pipeline_test |
| check_description | Each table with a logical key has passing uniqueness and not-null tests or an equivalent load control. |
| lifecycle_stage | Data Quality |

### INT-015: Warehouse foreign keys under controlled loads

**Warehouse foreign keys SHOULD be non-enforced with lookup validation in ETL-controlled loads, and SHOULD be declared as trusted by the optimizer only when the data is known to comply.**

| Field | Value |
|---|---|
| level | RECOMMENDED |
| status | active |
| decision_ref | null |
| scope | data_warehouse |
| applies_when | Warehouse tables loaded through controlled pipelines. |
| rationale | An optimizer that trusts invalid keys can return wrong results, and full enforcement adds load cost. |
| exceptions | Deviation with a recorded reason, approved by the framework exception approver. |
| engine_notes | Databricks defaults to NORELY. Redshift's planner assumes keys are valid and advises against declaring doubtful keys. Conflict C-03 is resolved by context. |
| evidence | MSOM-12, LAKE-09, DES-12, ENG-23, ENG-29, design_decision_matrix.md#RI-12, architecture_comparison.md#C-03 |
| evidence_strength | multi_vendor |
| check_method | pipeline_test |
| check_description | Each trusted key has a passing compliance test, and loads validate references by lookup. |
| lifecycle_stage | ETL/ELT |

### INT-016: Natural or surrogate key

**An OLTP entity with a natural key MAY use a surrogate primary key with a unique constraint on the natural key, which is the accepted default.**

| Field | Value |
|---|---|
| level | OPTIONAL |
| status | active |
| decision_ref | A3 |
| scope | OLTP |
| applies_when | Choosing the primary key of an OLTP entity. Warehouse key type is separate (decision RP-6, conflict C-11). |
| rationale | Natural keys can change or be wide, while surrogate-only keys let duplicates of the real-world entity in. |
| exceptions | Deviation with a recorded reason, approved by the framework exception approver. |
| engine_notes | No source measures this for OLTP, so the default is a judgment. Celko's text was not read and is not relied on. The strongest published surrogate arguments are for warehouses. |
| evidence | DES-12, DES-20, DES-03, design_decision_matrix.md#RI-13, architecture_comparison.md#C-12, database_design_standards.md#4.7 Contested |
| evidence_strength | single_vendor |
| check_method | schema_lint |
| check_description | Tables with a surrogate key and a known natural key also have a unique constraint on the natural key. |
| lifecycle_stage | Schema Design |

### INT-017: Do not reuse or fill key values

**Retired key values SHOULD NOT be reused and gaps in generated keys SHOULD NOT be filled.**

| Field | Value |
|---|---|
| level | RECOMMENDED |
| status | provisional |
| decision_ref | null |
| scope | OLTP |
| applies_when | Generated keys. Legal numbering of documents is a separate topic. |
| rationale | Reused values can attach old references to new rows. |
| exceptions | Deviation with a recorded reason, approved by the framework exception approver. |
| engine_notes | Supported only by a publisher-listed antipattern name in DES-13, so the rule stays provisional until the book is read. |
| evidence | DES-13, design_decision_matrix.md#RI-14, database_design_standards.md#11. Schema anti-patterns |
| evidence_strength | single_vendor |
| check_method | manual_review |
| check_description | No process renumbers keys or assigns retired values. |
| lifecycle_stage | Schema Design |

## Matrix coverage

| Matrix decisions | Rules |
|---|---|
| AP-1 to AP-10 | ARC-001 to ARC-010, in order |
| LP-1 to LP-3 | MOD-001 to MOD-003 |
| LP-4, LP-5, ER-7 | MOD-004. LP-5 is PostgreSQL-only and is kept in engine_notes to stay engine-neutral |
| LP-6 to LP-11 | MOD-005 to MOD-010 |
| ER-1 to ER-6 | ERD-001 to ERD-006 |
| ER-8, ER-9, ER-10 | ERD-007, ERD-008, ERD-009 |
| NF-1 to NF-10 | NRM-001 to NRM-010, in order |
| RI-1 | INT-001 |
| RI-2 | INT-002, INT-003 |
| RI-3 | INT-005, INT-006 |
| RI-4 to RI-14 | INT-007 to INT-017, in order |
| Not in the matrix | INT-004, from database_design_standards.md sections 4.5 and 11 |

## Classification changes

Rows below record the position before the owner decisions of 2026-11-08. Each rule's level, status and decision_ref fields show the current position.

| Rule | Research position | Position here and why |
|---|---|---|
| INT-004 | Research label MANDATORY (database_design_standards.md 4.5). No matrix row. | RECOMMENDED. Only MySQL enforcement and one incident support it. |
| ERD-001 | Standards file MANDATORY. Matrix RECOMMENDED. | Matrix followed. |
| NRM-002 | Standards file MANDATORY. Matrix RECOMMENDED. | Matrix followed, since Kent allows stopping short. |
| INT-005 | Standards file MANDATORY. Matrix RECOMMENDED. | Matrix followed. Only GitLab states it as a requirement. |
| INT-013 | Standards file MANDATORY for all workloads. Matrix RECOMMENDED for DW. | Matrix followed. |
| INT-017 | Standards file MANDATORY for all workloads. Matrix RECOMMENDED for OLTP. | Matrix followed, and set provisional because the only source is a publisher listing. |
| ARC-010, ERD-008 | Matrix evidence Standard, or Standard with inference. | Set to inference and provisional. The standard does not state the practice, and ISO 9075 text is unread. |
| ERD-002 | Matrix evidence Standard. | Set to inference and provisional. The standards define notations, but the consistency requirement is a judgment. |
| MOD-010, NRM-004, ERD-004, ERD-006 | Matrix evidence mixed with inference. | Set to inference and provisional because the normative content is marked inference. |
| NRM-006 | Matrix evidence Standard, single vendor. | Set to multi_vendor, matching RP-2. The sources are Oracle and Data Vault Alliance documentation. |
| INT-016 | Matrix evidence Inference. | Set to single_vendor with needs_decision. Named sources disagree (C-12), and only the proposed default is inference, so the rule is not inference-only. |
| ERD-007 | Note 07 MANDATORY. Matrix RECOMMENDED. | Matrix level followed, and needs_decision added because the matrix default conflicts with INT-002 inside one database. |

## Matrix citations not used as evidence

| Source | Matrix row | Reason |
|---|---|---|
| GOV-05 (ISO/IEC 9075) | AP-10 | Text unread, and listed in research_gaps.md section 7 item 1. |
| GOV-25 (ANSI/SPARC) | LP-1 | Only a Crossref record was opened. Three-schema details are unverified. |
| GOV-26 (Chen, MIT record) | ER-1 | Abstract from a snippet. DES-03 is the text-extracted copy of the same paper. |
| LIT-04, LIT-05 (Fagin) | NF-3 | Primary 4NF and 5NF texts unread (section 7 item 6). Kent is used instead. |
| LIT-10 (Celko) | RI-13 | Known from search summaries only. |
| BENCH-15 | AP-2 note | Records no numbers. |

DES-13 (Karwin) is used only for publisher-listed antipattern names. Rules that rest on it alone or on inference are provisional. research_gaps.md section 7 item 5 lists the book as still needing a licensed copy.

## Decisions needing owner approval

Answered by the owner on 2026-11-08: all defaults accepted. See `../DECISIONS_TO_APPROVE.md` for the decision log, and each rule's decision_ref for its decision number. Questions and alternatives are kept for the record.

### MOD-004. Which mapping is the default for supertype and subtype hierarchies?

**Proposed default:** Class-table mapping when a subtype attribute must be required or a subtype takes part in a foreign key. Single-table mapping otherwise. This is a judgment, because no independent benchmark exists (C-85).

| Option | Consequence |
|---|---|
| Class-table always | Strongest constraints, and more joins on every subtype read. |
| Single-table always | Simplest reads, and required subtype attributes cannot be enforced by NOT NULL. |
| Concrete-table | No shared foreign key target for references to the supertype. |
| Proposed default | Requires a mapping decision per hierarchy, and gives required-value enforcement where it matters. |

### ERD-007. Do foreign keys cross bounded context boundaries inside one database?

**Proposed default:** Keep foreign keys inside one database until a boundary is approved for physical separation. Use identifiers across separate stores.

| Option | Consequence |
|---|---|
| Proposed default | Modular ERP keeps engine integrity, and a later split must remove those keys first. |
| Identifiers across every context, even in one database | Follows the matrix inference. Contexts are easier to separate, but each such reference needs an INT-002 exception and INT-003 controls. |
| Foreign keys everywhere in one database with no separation path | Strongest integrity, and contexts become tightly coupled. |

### INT-006. What is the default ON DELETE policy?

**Proposed default:** CASCADE only for strict composition, RESTRICT or NO ACTION for independent objects, SET NULL only for optional relationships. No source settles this (C-09).

| Option | Consequence |
|---|---|
| Proposed default | Each foreign key needs a relationship classification, and accidental mass deletion is limited. [INFERENCE] Financial records that are corrected by new entries would not be cascade targets. |
| CASCADE in nearly all cases (GitLab) | Cleanup is automatic, with greater risk of mass deletion. InnoDB cascades skip triggers and are hidden from binlog consumers. |
| NO ACTION everywhere (PlanetScale) | Deletes are safest, and the application must order and perform cleanup. |
| No cascades at all (Alibaba) | Avoids cascade blocking and update storms, and moves all referential cleanup to application code. |

### INT-016. Natural or surrogate primary key for OLTP entities?

**Proposed default:** Surrogate primary key plus a unique constraint on the natural key where one exists. This is a judgment (C-12).

| Option | Consequence |
|---|---|
| Proposed default | Stable references and duplicate prevention, at the cost of an extra unique index. |
| Natural primary key | Meaningful keys and no lookup. Key changes spread to every referencing table. |
| Surrogate only | Simplest references, and duplicates of the real-world entity are not prevented. |
