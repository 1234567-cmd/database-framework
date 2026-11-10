# Stage 2 Standards: Pipelines, Quality, Reporting, Monitoring and Governance

Rule group 06. Prefixes: PIP, DQA, RPT, MON, GOV. Built from existing research only: `research/design_decision_matrix.md`, `research/data_pipeline_architecture.md`, `research/data_engineering_principles.md`, the analytical parts of `research/data_modeling_approaches.md`, and section 6 of `research/research_gaps.md`. No web research was done and no source was added. This file contains no schemas, DDL or code. The machine-readable copy is `standards/registry/06_pipelines_quality_governance.json`.

## How to read this file

Evidence entries are catalog IDs from `research/resource_catalog.json`, or research references written as `research/<file>#<decision ID or section number>`. A source with no catalog ID is cited through the research section that records it.

MUST pairs with MANDATORY, SHOULD with RECOMMENDED, and MAY with OPTIONAL. Rules state their workload in scope and applies_when. Rules for OLTP systems and rules for analytical systems are not interchangeable, and any rule that spans both says so.

## Substitutes for unenforced warehouse keys

Warehouses and lakehouses generally do not enforce primary, foreign or unique keys (DQA-003). The stated substitutes are:

| Requirement | Substitute | Rule |
|---|---|---|
| Primary key or uniqueness | Uniqueness and non-null tests on the key, and pipeline merge on the declared key | DQA-004, PIP-002 |
| Foreign key | Relationship tests or ETL key lookups with an orphan count; in Kimball models, default dimension rows | DQA-005, RPT-006 |
| Duplicates under retry | Idempotent writes and event deduplication identifiers | PIP-001, PIP-004 |
| Protecting consumers | Promotion gate, and blocking checks that actually block | DQA-007, DQA-008 |
| Optimizer trust in keys | Enabled only after the data has been verified | DQA-006 |

## Classification changes from the research

The matrix classifications are followed. Topic documents label some items more strongly than the matrix or `RULE_FORMAT.md` allow, and those are recorded here. Rows below record the position before the owner decisions of 2026-11-08. Each rule's level, status and decision_ref fields show the current position.

| Rule | Research label | Level here | Reason |
|---|---|---|---|
| DQA-004, DQA-005 | VAL-03 MANDATORY | RECOMMENDED | Matrix RI-11, RI-12 and TS-8; the source recommends the test and the raise was the framework's own |
| DQA-007 | VAL-04 MANDATORY | RECOMMENDED | Matrix DV-3 |
| DQA-010 | OBS-05 MANDATORY | RECOMMENDED, needs_decision | One case-study source |
| DQA-015, DQA-016 | REC-01, REC-02 MANDATORY | RECOMMENDED | Matrix DV-7; basis is inference and tools |
| DQA-017 | REC-03 MANDATORY | RECOMMENDED | Matrix DV-8; single vendor |
| DQA-020 | CON-01 MANDATORY | RECOMMENDED | Matrix DV-10; no source makes contracts compulsory |
| DQA-021 | CON-03 RECOMMENDED | OPTIONAL | Matrix DV-11 |
| DQA-023 | REG-01, CON-05 MANDATORY | RECOMMENDED | Matrix DV-14 |
| DQA-025 | REG-02 MANDATORY | RECOMMENDED | Single vendor; no matrix row |
| PIP-002, PIP-027, PIP-028, PIP-029 | IDM-02, ETL-02, BKF-01, BKF-05 MANDATORY | RECOMMENDED, provisional | Inference-only rules cannot be MANDATORY |
| PIP-003 | ORC-02, ORC-03 MANDATORY | RECOMMENDED | Matrix PL-5 |
| PIP-004 | IDM-03 MANDATORY | RECOMMENDED | Matrix PL-12 |
| PIP-005 | KAF-07, SPK-04 MANDATORY | RECOMMENDED | Matrix PL-16 |
| PIP-008 | CDC-08 MANDATORY | RECOMMENDED, provisional | Matrix PL-8; inference |
| PIP-010 | KAF-10 MANDATORY | RECOMMENDED | Single vendor; operational consequence is inference |
| PIP-012, PIP-013 | BAT-02, KAF-13, DFM-03 MANDATORY | RECOMMENDED | Matrix PL-13 |
| PIP-017 | SPK-01 MANDATORY | RECOMMENDED | Matrix PL-9; the Spark engine behaviour is in engine_notes |
| PIP-020 | ELT-03 MANDATORY | RECOMMENDED | Vendor-originated risk statement only |
| PIP-024 | LAM-01 RECOMMENDED | OPTIONAL, needs_decision | Matrix PL-3 and one-sided evidence |
| PIP-025 | KAP-01 MANDATORY | RECOMMENDED | Pipeline section 18, item 11 |
| PIP-026 | TRN-04 MANDATORY | RECOMMENDED | Single paper; current platform status unverified |
| DQA-011 | SMT-03 MANDATORY | RECOMMENDED | Matrix DV-5; the engine behaviour is in engine_notes |
| RPT-013 | LAM-02 MANDATORY | RECOMMENDED, provisional | Inference only |
| PIP-018 | ELT-07 MANDATORY on inference | MANDATORY, kept | Now rests on matrix DT-1, multi-vendor |
| PIP-011, PIP-014 | KAF-01, DFM-01 MANDATORY | MANDATORY, kept | No matrix row. Retained on engine behaviour and a foundational paper |
| RPT-009 | REP-05, BKF-06 MANDATORY | RECOMMENDED | Single vendor |
| GOV-002 | GVN-02 MANDATORY | RECOMMENDED, provisional | Matrix DG-2; DMBOK is not prescriptive |
| GOV-006 | OBS-03 MANDATORY | RECOMMENDED | Matrix DG-7 |
| DQA-003 | Matrix RI-11 RECOMMENDED | MANDATORY | RI-11 classifies the choice of substitute. This rule covers documented engine behaviour, in VAL-02, on which vendors agree |
| DQA-008 | ORC-07 MANDATORY; no matrix row | MANDATORY, kept | Conditional on a check being designated blocking; two vendors document that checks do not block by default |

## Scope boundaries

These items are left to other rule groups and are not repeated here: restore testing (BK-5, listed under Monitoring in the matrix lifecycle view), schema drift detection (TS-6), analytical test tooling beyond the key tests, table-format evolution (MG-13) and streaming version migration (MG-14), the transactional outbox, access control, GDPR classification and minimization (SC-4, SC-5). DG-6 is a pointer to DV-10 and is covered by DQA-020. BAT-03 and BAT-04 are materialization guidance and not requirements; the history limit in BAT-04 is noted in RPT-008.

## Data pipelines and ETL/ELT (PIP)

### PIP-001 Idempotent re-runnable writes

Every re-runnable pipeline step MUST leave the target in the same state, with no duplicates and no partial result, when re-run for the same input.

| Field | Value |
|---|---|
| level | MANDATORY |
| scope | data_warehouse, lakehouse, streaming |
| applies_when | always, for every pipeline step that writes to a target and can be retried or re-run |
| rationale | Orchestrators retry and CDC redelivers under fault, so a plain insert creates duplicates or partial loads that consumers cannot detect. |
| exceptions | none |
| engine_notes | Airflow frames tasks like transactions and prefers upsert over plain insert. Spark foreachBatch is at-least-once by default and batchId can deduplicate. Debezium is at-least-once under faults. Kafka does not provide end-to-end guarantees to external sinks. |
| evidence | PIPE-13, PIPE-08, PIPE-01, PIPE-06, research/design_decision_matrix.md#PL-4, research/data_pipeline_architecture.md#15.1, research/data_engineering_principles.md#6.1 |
| evidence_strength | multi_vendor |
| status | active |
| decision_ref | null |
| check_method | pipeline_test |
| check_description | Re-run a step for a fixed interval or offset range and confirm row counts and aggregates in the target do not change. |
| lifecycle_stage | ETL/ELT |

### PIP-002 Declared write grain

Each pipeline target SHOULD declare its merge or overwrite grain as a business key or as a partition and interval.

| Field | Value |
|---|---|
| level | RECOMMENDED |
| scope | data_warehouse, lakehouse, streaming |
| applies_when | the target is written by a pipeline and PIP-001 applies |
| rationale | Without a declared grain, idempotent writes cannot be implemented or reviewed, and a warehouse will not reject the resulting duplicates. |
| exceptions | Exception recorded with a reason and approved by the dataset owner |
| engine_notes | Warehouse MERGE on the declared key is also one of the substitutes for unenforced keys (see DQA-004). |
| evidence | PIPE-13, research/data_pipeline_architecture.md#15.2, research/design_decision_matrix.md#PL-4 |
| evidence_strength | inference |
| status | provisional |
| decision_ref | null |
| check_method | catalog_query |
| check_description | Each pipeline target has a recorded merge key or partition and interval definition. |
| lifecycle_stage | ETL/ELT |

### PIP-003 Deterministic interval inputs

Scheduled pipeline steps SHOULD read a declared data interval or partition rather than the latest data or wall-clock time.

| Field | Value |
|---|---|
| level | RECOMMENDED |
| scope | data_warehouse, lakehouse |
| applies_when | the pipeline runs on a schedule or can be backfilled |
| rationale | Reading latest data makes re-runs and backfills return different results for the same interval. |
| exceptions | Exception recorded with a reason and approved by the dataset owner |
| engine_notes | Airflow forbids reading latest data and basing logic on wall-clock calls within a task. Iceberg transforms still need the underlying timestamp column. |
| evidence | PIPE-13, research/design_decision_matrix.md#PL-5, research/data_pipeline_architecture.md#14.1 |
| evidence_strength | single_vendor |
| status | active |
| decision_ref | null |
| check_method | pipeline_test |
| check_description | Re-run a past interval and confirm the step reads only that interval's input and contains no wall-clock logic. |
| lifecycle_stage | ETL/ELT |

### PIP-004 Event deduplication identifier

Event records SHOULD carry a deduplication identifier such as an event ID or source position.

| Field | Value |
|---|---|
| level | RECOMMENDED |
| scope | streaming |
| applies_when | events are consumed by a sink that may receive them more than once |
| rationale | Delivery is at-least-once under failure, so consumers without an identifier cannot remove duplicates. |
| exceptions | Exception recorded with a reason and approved by the dataset owner |
| engine_notes | Debezium outbox id, CDC source position and Spark batchId at the sink are the documented mechanisms. The idempotent-reader requirement itself is inference. |
| evidence | PIPE-01, PIPE-05, PIPE-06, ARCH-11, research/design_decision_matrix.md#PL-12, research/data_pipeline_architecture.md#15.2 |
| evidence_strength | single_vendor |
| status | active |
| decision_ref | null |
| check_method | schema_lint |
| check_description | Each event schema names a field or envelope element usable for deduplication. |
| lifecycle_stage | ETL/ELT |

### PIP-005 Sink-level exactly-once

Exactly-once at an external sink SHOULD be achieved with idempotent writes or by storing the consumer position in the same transaction as the output.

| Field | Value |
|---|---|
| level | RECOMMENDED |
| scope | streaming |
| applies_when | a stream is written to an external database, warehouse or table format and duplicates would be wrong |
| rationale | Exactly-once is local to each system, so a design that assumes it end to end loses or duplicates data at the boundary. |
| exceptions | Exception recorded with a reason and approved by the dataset owner |
| engine_notes | Kafka exactly-once covers read-process-write inside Kafka only. Spark gives exactly-once for the file sink only; Kafka and foreach sinks are at-least-once. |
| evidence | PIPE-01, PIPE-08, research/design_decision_matrix.md#PL-16, research/data_pipeline_architecture.md#7.2, research/data_pipeline_architecture.md#12.2 |
| evidence_strength | multi_vendor |
| status | active |
| decision_ref | null |
| check_method | pipeline_test |
| check_description | Inject a consumer restart and confirm the sink has no duplicated or missing records. |
| lifecycle_stage | ETL/ELT |

### PIP-006 Identity on captured tables

Tables captured by log-based CDC MUST have a primary key or an equivalent configured replica identity whenever update and delete events are required.

| Field | Value |
|---|---|
| level | MANDATORY |
| scope | OLTP, streaming |
| applies_when | a table is captured by log-based CDC and updates or deletes must reach consumers |
| rationale | Without an identity, the connector cannot describe updates and deletes, so downstream state silently diverges from the source. |
| exceptions | none |
| engine_notes | PostgreSQL: with no primary key under REPLICA IDENTITY DEFAULT, Debezium emits only create events. The research covers the PostgreSQL connector only; MySQL, SQL Server and Oracle capture details are unresearched. |
| evidence | TEN-28, PIPE-06, research/design_decision_matrix.md#PL-7, research/data_pipeline_architecture.md#10.2 |
| evidence_strength | multi_vendor |
| status | active |
| decision_ref | null |
| check_method | catalog_query |
| check_description | Every captured table has a primary key or a replica identity that identifies rows. |
| lifecycle_stage | ETL/ELT |

### PIP-007 Change capture method

Sources feeding incremental loads SHOULD use log-based change capture, falling back to query-based extraction only where log access is unavailable.

| Field | Value |
|---|---|
| level | RECOMMENDED |
| scope | OLTP, streaming |
| applies_when | a source feeds incremental downstream loads |
| rationale | Query-based extraction misses hard deletes and intermediate states unless additional design is added. |
| exceptions | Exception recorded with a reason and approved by the dataset owner |
| engine_notes | Debezium's comparison favouring log-based CDC comes from a CDC project describing itself, so it is not neutral. |
| evidence | PIPE-06, TEN-26, TEN-29, research/design_decision_matrix.md#PL-6, research/data_pipeline_architecture.md#10.1 |
| evidence_strength | multi_vendor |
| status | active |
| decision_ref | null |
| check_method | manual_review |
| check_description | The capture method is recorded per source, and any query-based source states why log access is unavailable. |
| lifecycle_stage | ETL/ELT |

### PIP-008 Change signal for query-based extraction

Tables extracted by query SHOULD maintain a reliable change column and a defined way to observe deletes.

| Field | Value |
|---|---|
| level | RECOMMENDED |
| scope | OLTP |
| applies_when | the table is extracted by query rather than log-based CDC; this is not a requirement on CDC-captured tables |
| rationale | An unreliable change signal causes incremental loads to skip rows, and hard deletes are invisible to queries. |
| exceptions | Exception recorded with a reason and approved by the dataset owner |
| engine_notes | No official source prescribes an updated-at column; this remains a framework decision. |
| evidence | PIPE-06, TEN-26, research/design_decision_matrix.md#PL-8, research/data_pipeline_architecture.md#10.4 |
| evidence_strength | inference |
| status | provisional |
| decision_ref | null |
| check_method | schema_lint |
| check_description | Query-extracted tables have a change column that is maintained on every write, and a recorded delete-detection method. |
| lifecycle_stage | ETL/ELT |

### PIP-009 Deletes in compacted topics

Compacted event topics MUST represent deletion with a keyed tombstone or delete event.

| Field | Value |
|---|---|
| level | MANDATORY |
| scope | streaming |
| applies_when | the topic uses log compaction |
| rationale | Compaction retains the last value per key, so a key with no tombstone stays live forever. |
| exceptions | none |
| engine_notes | Kafka treats a key with a null payload as a delete marker. Debezium emits a delete event followed by a tombstone, with tombstones.on.delete defaulting to true. |
| evidence | PIPE-01, PIPE-06, research/design_decision_matrix.md#PL-11, research/data_pipeline_architecture.md#7.3 |
| evidence_strength | single_vendor |
| status | active |
| decision_ref | H3 |
| check_method | pipeline_test |
| check_description | Delete a source record and confirm a keyed tombstone reaches the compacted topic. |
| lifecycle_stage | ETL/ELT |

### PIP-010 Rebuild within tombstone retention

Consumers rebuilding state from a compacted topic SHOULD reach the head of the log within the tombstone retention period.

| Field | Value |
|---|---|
| level | RECOMMENDED |
| scope | streaming |
| applies_when | a consumer rebuilds state from a compacted topic |
| rationale | A consumer that misses a tombstone resurrects deleted keys. |
| exceptions | Exception recorded with a reason and approved by the dataset owner |
| engine_notes | Kafka delete.retention.ms defaults to one day (documented in the 4.2 configuration reference). Do not rely on compaction to meet an erasure deadline, because the default maximum compaction lag gives no deadline. |
| evidence | PIPE-01, research/data_pipeline_architecture.md#7.3 |
| evidence_strength | single_vendor |
| status | active |
| decision_ref | null |
| check_method | runtime_monitor |
| check_description | Measured rebuild time is below the configured tombstone retention. |
| lifecycle_stage | ETL/ELT |

### PIP-011 Ordering requires a shared key

Records that must remain ordered relative to each other MUST share a partition key on any log that guarantees order only per partition.

| Field | Value |
|---|---|
| level | MANDATORY |
| scope | streaming |
| applies_when | the transport guarantees ordering only within a partition |
| rationale | Ordering across partitions is not guaranteed, so related events can be applied in the wrong order. |
| exceptions | none |
| engine_notes | Kafka hashes the key to select a partition. A change of partition count or key definition breaks the ordering guarantee, and should be handled as a breaking change (GOV-006); that consequence is inference. |
| evidence | PIPE-01, research/data_pipeline_architecture.md#7.1 |
| evidence_strength | single_vendor |
| status | active |
| decision_ref | H3 |
| check_method | manual_review |
| check_description | Each ordering requirement names the key that delivers it and the key is set at production time. |
| lifecycle_stage | ETL/ELT |

### PIP-012 Explicit event time

Event records SHOULD carry business event time as an explicit field distinct from processing and ingest time.

| Field | Value |
|---|---|
| level | RECOMMENDED |
| scope | streaming |
| applies_when | the dataset may be processed or windowed by event time |
| rationale | Broker timestamps have a topic-configurable meaning, so windowing and late-data handling are wrong if they rely on them. |
| exceptions | Exception recorded with a reason and approved by the dataset owner |
| engine_notes | Kafka message.timestamp.type is CreateTime or LogAppendTime per topic. |
| evidence | PIPE-17, PIPE-16, PIPE-01, research/design_decision_matrix.md#PL-13, research/data_pipeline_architecture.md#4.2, research/data_pipeline_architecture.md#7.4 |
| evidence_strength | standard |
| status | active |
| decision_ref | null |
| check_method | schema_lint |
| check_description | Each event schema has an event-time field separate from processing and ingest timestamps. |
| lifecycle_stage | ETL/ELT |

### PIP-013 Event-time windows

Streaming aggregates that must reflect when events happened SHOULD use event-time windows.

| Field | Value |
|---|---|
| level | RECOMMENDED |
| scope | streaming |
| applies_when | a streaming aggregate must reflect when events occurred |
| rationale | Processing-time windows give wrong results under out-of-order arrival. |
| exceptions | Exception recorded with a reason and approved by the dataset owner |
| engine_notes | Spark watermark cleanup needs an event-time column or window in the aggregation. |
| evidence | PIPE-16, PIPE-17, research/data_pipeline_architecture.md#6.3 |
| evidence_strength | standard |
| status | active |
| decision_ref | null |
| check_method | manual_review |
| check_description | Each streaming aggregate records its window type, and processing-time windows state why they are acceptable. |
| lifecycle_stage | ETL/ELT |

### PIP-014 No assumption of completeness

Stream consumers MUST NOT rely on a dataset ever being complete or on data later than a watermark being dropped.

| Field | Value |
|---|---|
| level | MANDATORY |
| scope | streaming |
| applies_when | always, for stream consumers |
| rationale | Watermarks are heuristic lower bounds, so logic that assumes completeness produces incorrect results when late data arrives. |
| exceptions | none |
| engine_notes | Spark guarantees only that data less late than the threshold is not dropped; later data may or may not be processed. |
| evidence | PIPE-17, PIPE-08, research/data_pipeline_architecture.md#6.1, research/data_pipeline_architecture.md#17.1 |
| evidence_strength | standard |
| status | active |
| decision_ref | null |
| check_method | manual_review |
| check_description | Consumer logic has a defined outcome for records arriving after the watermark. |
| lifecycle_stage | ETL/ELT |

### PIP-015 Late-data policy

Windowed streaming aggregates SHOULD define allowed lateness and the handling of data that arrives after it.

| Field | Value |
|---|---|
| level | RECOMMENDED |
| scope | streaming, OLAP |
| applies_when | the pipeline produces windowed aggregates |
| rationale | Without a stated policy, completeness and latency trade off invisibly and results change without explanation. |
| exceptions | Exception recorded with a reason and approved by the dataset owner |
| engine_notes | Spark append mode needs a watermark for aggregations, and stream-stream outer and semi joins require watermarks and time constraints. |
| evidence | PIPE-08, PIPE-17, research/design_decision_matrix.md#PL-14, research/data_pipeline_architecture.md#17.2 |
| evidence_strength | single_vendor |
| status | active |
| decision_ref | null |
| check_method | manual_review |
| check_description | Each streaming aggregate table records allowed lateness and post-lateness handling. |
| lifecycle_stage | ETL/ELT |

### PIP-016 Refinement mode recorded

Each streaming aggregate SHOULD state whether results are discarded, accumulated, or accumulated with retraction.

| Field | Value |
|---|---|
| level | RECOMMENDED |
| scope | streaming, OLAP |
| applies_when | a streaming aggregate is written to an analytical sink |
| rationale | The refinement mode fixes the sink's key and write semantics, so an unstated mode leads to double counting. |
| exceptions | Exception recorded with a reason and approved by the dataset owner |
| engine_notes | No source prescribes the mode-to-sink mapping. |
| evidence | PIPE-17, research/data_pipeline_architecture.md#6.2, research/data_pipeline_architecture.md#6.3 |
| evidence_strength | inference |
| status | provisional |
| decision_ref | null |
| check_method | manual_review |
| check_description | Each streaming aggregate names a refinement mode consistent with its sink. |
| lifecycle_stage | ETL/ELT |

### PIP-017 Declared schema at ingestion

Ingestion SHOULD use a declared schema rather than one inferred from the data.

| Field | Value |
|---|---|
| level | RECOMMENDED |
| scope | lakehouse, streaming |
| applies_when | structured or typed data is ingested; permissive raw payloads under PIP-019 are handled separately |
| rationale | Inference changes with sample content and can yield wrong types or silent nulls. |
| exceptions | Exception recorded with a reason and approved by the dataset owner |
| engine_notes | Spark streaming file sources require a declared schema by default. Spark JSON inference defaults to floating point unless prefersDecimal is set, and PERMISSIVE mode nulls malformed fields. |
| evidence | PIPE-07, PIPE-08, research/design_decision_matrix.md#PL-9, research/data_pipeline_architecture.md#12.1 |
| evidence_strength | single_vendor |
| status | active |
| decision_ref | null |
| check_method | pipeline_test |
| check_description | The ingestion configuration declares a schema, and malformed input is captured rather than becoming nulls. |
| lifecycle_stage | ETL/ELT |

### PIP-018 Exact money types from the first typed layer

Monetary values MUST be declared as exact decimal or integer minor units at the first typed layer of a pipeline.

| Field | Value |
|---|---|
| level | MANDATORY |
| scope | data_warehouse, lakehouse, OLAP |
| applies_when | the dataset carries monetary amounts |
| rationale | Inferred or floating-point amounts introduce rounding errors that reconciliation later cannot explain. |
| exceptions | none |
| engine_notes | Spark JSON inference yields floating point by default. A dbt style-guide example casts an order total to float; it conflicts with this rule and must not be copied. |
| evidence | PGMY-02, MSOM-18, PIPE-07, research/design_decision_matrix.md#DT-1, research/data_pipeline_architecture.md#3.3, research/data_engineering_principles.md#9.2, research/data_modeling_approaches.md#18.15 |
| evidence_strength | multi_vendor |
| status | active |
| decision_ref | null |
| check_method | schema_lint |
| check_description | No monetary column in a typed layer uses a binary floating-point type. |
| lifecycle_stage | ETL/ELT |

### PIP-019 Raw landing layer

Pipelines MAY keep a raw landing layer with a permissive payload before typing, provided the envelope is declared.

| Field | Value |
|---|---|
| level | OPTIONAL |
| scope | lakehouse, data_warehouse |
| applies_when | the pipeline lands data before transforming it |
| rationale | Typing at ingest loses re-derivation, while raw landing raises exposure of unmasked data. |
| exceptions | none |
| engine_notes | The layer stance is a framework position: permissive raw payload with declared key, event time, ingest time, source and schema version, and declared types from the validated layer upward. Databricks suggests bronze fields as string, VARIANT or binary. |
| evidence | LAKE-01, PIPE-18, CLOUD-21, research/design_decision_matrix.md#PL-10, research/data_pipeline_architecture.md#3.3, research/data_modeling_approaches.md#18.14 |
| evidence_strength | multi_vendor |
| status | active |
| decision_ref | null |
| check_method | manual_review |
| check_description | If a raw layer exists, its envelope fields are declared and consumers do not read it directly. |
| lifecycle_stage | ETL/ELT |

### PIP-020 Raw landing is governed

A raw landing store holding personal or financial data SHOULD have the same access control, classification and retention as any other store.

| Field | Value |
|---|---|
| level | RECOMMENDED |
| scope | lakehouse, data_warehouse |
| applies_when | a raw landing store holds personal or financial data |
| rationale | Vendors recommending ELT concede raw data carries security and compliance risk, and raw zones are easily forgotten by access reviews. |
| exceptions | Exception recorded with a reason and approved by the framework exception approver |
| engine_notes | Databricks states bronze data is not intended for analyst access. |
| evidence | PIPE-18, LAKE-01, research/data_pipeline_architecture.md#3.2 |
| evidence_strength | single_vendor |
| status | active |
| decision_ref | null |
| check_method | catalog_query |
| check_description | Raw stores appear in access, classification and retention inventories. |
| lifecycle_stage | ETL/ELT |

### PIP-021 ETL or ELT choice

Each dataset MAY use ETL, ELT or a hybrid, with ELT as the default where raw data can be governed and ETL or hybrid where data must be masked before loading.

| Field | Value |
|---|---|
| level | OPTIONAL |
| scope | data_warehouse, lakehouse |
| applies_when | a dataset is being designed for an analytical target; this is not an OLTP pattern |
| rationale | Choosing without recording the reason hides the trade-off between re-derivation and raw exposure. |
| exceptions | none |
| engine_notes | Google and dbt recommend ELT and both have an interest in in-warehouse transformation. No measured ETL against ELT cost comparison exists. |
| evidence | PIPE-19, PIPE-18, research/design_decision_matrix.md#PL-1, research/data_pipeline_architecture.md#3.1 |
| evidence_strength | multi_vendor |
| status | active |
| decision_ref | null |
| check_method | manual_review |
| check_description | The design record states the pattern chosen and why. |
| lifecycle_stage | ETL/ELT |

### PIP-022 Source-conformed staging

Warehouse pipelines SHOULD keep a source-conformed staging layer separate from business-conformed models, applying each transformation once.

| Field | Value |
|---|---|
| level | RECOMMENDED |
| scope | data_warehouse |
| applies_when | the warehouse is built with layered transformations |
| rationale | Mixing joins and business logic into staging duplicates logic and hides source problems. |
| exceptions | Exception recorded with a reason and approved by the dataset owner |
| engine_notes | dbt describes staging as one-to-one with sources, doing renames, casts and basic computation only. |
| evidence | LAKE-15, research/data_pipeline_architecture.md#3.2 |
| evidence_strength | single_vendor |
| status | active |
| decision_ref | null |
| check_method | manual_review |
| check_description | Staging models have one source and contain no joins or aggregations. |
| lifecycle_stage | ETL/ELT |

### PIP-023 Batch or streaming choice

Each dataset MAY use batch, micro-batch or streaming, chosen by correctness, latency and cost.

| Field | Value |
|---|---|
| level | OPTIONAL |
| scope | data_warehouse, lakehouse, streaming |
| applies_when | a dataset is being designed |
| rationale | Choosing by fashion rather than by need adds cost or leaves freshness unmet. |
| exceptions | none |
| engine_notes | Snowflake dynamic tables have a minimum target lag of 60 seconds. |
| evidence | PIPE-16, PIPE-17, research/design_decision_matrix.md#PL-2, research/data_pipeline_architecture.md#4.2 |
| evidence_strength | standard |
| status | active |
| decision_ref | null |
| check_method | manual_review |
| check_description | The design record states the processing mode and the freshness need it meets. |
| lifecycle_stage | ETL/ELT |

### PIP-024 Single implementation of reprocessing logic

Reprocessing MAY use Lambda, Kappa or a unified model, and the accepted default is one implementation of the logic, replay-based or unified.

| Field | Value |
|---|---|
| level | OPTIONAL |
| scope | streaming, OLAP |
| applies_when | the pipeline needs both low latency and reprocessing |
| rationale | Two codebases drift apart, and the Dataflow paper reports customers ceasing to trust the weakly consistent results. |
| exceptions | Exception recorded with a reason and approved by the framework exception approver |
| engine_notes | Azure documents Lambda; Kreps and Akidau argue against dual codebases. Every source discussing it is critical or neutral and both critics advocate streaming, so the evidence is one-sided and no measured comparison exists. This is a judgment. |
| evidence | PIPE-15, PIPE-16, PIPE-17, CLOUD-17, research/design_decision_matrix.md#PL-3, research/data_pipeline_architecture.md#5.3 |
| evidence_strength | standard |
| status | active |
| decision_ref | B25 |
| check_method | manual_review |
| check_description | A dual path has a recorded justification and one authoritative metric definition. |
| lifecycle_stage | ETL/ELT |

### PIP-025 Replay retention

Log retention SHOULD cover the reprocessing window wherever replay is the reprocessing strategy.

| Field | Value |
|---|---|
| level | RECOMMENDED |
| scope | streaming |
| applies_when | replay of a retained log is the reprocessing strategy |
| rationale | Replay beyond retention is impossible, and the gap is typically found only when the replay is needed. |
| exceptions | Exception recorded with a reason and approved by the dataset owner |
| engine_notes | Kafka retention.ms defaults to 7 days, so longer windows need explicit configuration, a compacted topic or an archive. |
| evidence | PIPE-15, research/data_pipeline_architecture.md#5.2, research/data_pipeline_architecture.md#7.4 |
| evidence_strength | single_vendor |
| status | active |
| decision_ref | null |
| check_method | catalog_query |
| check_description | Topic retention is at least the recorded reprocessing window. |
| lifecycle_stage | ETL/ELT |

### PIP-026 Do not assume cross-table atomicity

Lakehouse pipelines SHOULD treat each table write as atomic only for that table unless the platform's current documentation confirms otherwise.

| Field | Value |
|---|---|
| level | RECOMMENDED |
| scope | lakehouse |
| applies_when | a pipeline publishes more than one lakehouse table together |
| rationale | Consumers can read one table updated and a related table not yet updated. |
| exceptions | Exception recorded with a reason and approved by the dataset owner |
| engine_notes | The Delta paper limits transactions to one table. Multi-table support was a private preview in December 2025 and its current status is unverified. The Databricks statement that medallion guarantees ACID across layers should not be read as cross-layer atomicity. |
| evidence | LAKE-08, LAKE-06, research/data_pipeline_architecture.md#13.4, research/data_engineering_principles.md#5 |
| evidence_strength | single_vendor |
| status | active |
| decision_ref | null |
| check_method | manual_review |
| check_description | Multi-table publications define consumer behaviour during partial completion, or cite platform confirmation. |
| lifecycle_stage | ETL/ELT |

### PIP-027 Load run record

Every load SHOULD record its run identity, source position or interval, code version and result.

| Field | Value |
|---|---|
| level | RECOMMENDED |
| scope | data_warehouse, lakehouse, streaming |
| applies_when | always, for pipeline loads |
| rationale | Without a run record, a bad load cannot be traced to its input or code, or be replayed. |
| exceptions | Exception recorded with a reason and approved by the dataset owner |
| engine_notes | OpenLineage run facets and Kimball audit attributes are the mechanisms read. No source defines a universal control-table design. |
| evidence | DQ-15, GOV-31, research/data_engineering_principles.md#6.1 |
| evidence_strength | inference |
| status | provisional |
| decision_ref | B1 |
| check_method | catalog_query |
| check_description | Each loaded interval has one record with run, position, version and outcome. |
| lifecycle_stage | ETL/ELT |

### PIP-028 Backfill by declared interval

A backfill SHOULD overwrite or merge one declared interval or partition at a time and publish through the same gate as normal loads.

| Field | Value |
|---|---|
| level | RECOMMENDED |
| scope | data_warehouse, lakehouse |
| applies_when | historical data is reprocessed; OLTP backfills are outside this rule |
| rationale | Unbounded backfills cannot be verified or safely retried, and they bypass checks. |
| exceptions | Exception recorded with a reason and approved by the dataset owner |
| engine_notes | No source defines a backfill standard, and Airflow's backfill tooling was not researched. Databricks RESTORE can produce duplicates for streaming readers. |
| evidence | PIPE-13, DQ-12, DQ-13, research/data_pipeline_architecture.md#16 |
| evidence_strength | inference |
| status | provisional |
| decision_ref | null |
| check_method | pipeline_test |
| check_description | A backfill run names its interval and passes the same promotion gate. |
| lifecycle_stage | ETL/ELT |

### PIP-029 Reconcile financial backfills

Backfills of financial data SHOULD be reconciled against the source after completion.

| Field | Value |
|---|---|
| level | RECOMMENDED |
| scope | data_warehouse, lakehouse |
| applies_when | the backfill touches financial data |
| rationale | A backfill can silently drop or duplicate amounts in closed periods. |
| exceptions | Exception recorded with a reason and approved by the dataset owner |
| engine_notes | Stripe re-ran an offline job to confirm no records were missed; applying this as a rule is inference. |
| evidence | OPS-06, research/data_pipeline_architecture.md#16 |
| evidence_strength | inference |
| status | provisional |
| decision_ref | null |
| check_method | pipeline_test |
| check_description | A reconciliation result exists for each financial backfill interval. |
| lifecycle_stage | ETL/ELT |

### PIP-030 Rebuild and swap

Reprocessing MAY build a new versioned output and then switch readers rather than overwrite the live table.

| Field | Value |
|---|---|
| level | OPTIONAL |
| scope | OLAP, streaming |
| applies_when | logic changes require reprocessing retained data |
| rationale | In-place reprocessing exposes partially rebuilt results to readers. |
| exceptions | none |
| engine_notes | Snapshots and history tables cannot be rebuilt this way (see RPT-009). |
| evidence | PIPE-15, research/design_decision_matrix.md#PL-3, research/data_pipeline_architecture.md#5.2, research/data_pipeline_architecture.md#16 |
| evidence_strength | single_vendor |
| status | active |
| decision_ref | null |
| check_method | manual_review |
| check_description | Reprocessing plans state whether output is swapped or overwritten. |
| lifecycle_stage | ETL/ELT |

### PIP-031 Unit of orchestration

Pipelines MAY be orchestrated by task or by data asset.

| Field | Value |
|---|---|
| level | OPTIONAL |
| scope | data_warehouse, lakehouse |
| applies_when | an orchestrator is being chosen |
| rationale | The choice affects tooling only, because both models require re-runnable units. |
| exceptions | none |
| engine_notes | Airflow is task-centric and Dagster asset-centric. |
| evidence | PIPE-13, PIPE-14, research/design_decision_matrix.md#PL-15, research/data_pipeline_architecture.md#14.3 |
| evidence_strength | multi_vendor |
| status | active |
| decision_ref | null |
| check_method | manual_review |
| check_description | The orchestration model is recorded and PIP-001 holds under it. |
| lifecycle_stage | ETL/ELT |

### PIP-032 Connector-edge transforms

Connector-edge transforms MAY be used for narrow per-record changes, provided canonical flattening and type coercion are documented.

| Field | Value |
|---|---|
| level | OPTIONAL |
| scope | streaming |
| applies_when | transforms are applied inside a connector |
| rationale | Undocumented flattening becomes a hidden contract that consumers depend on. |
| exceptions | none |
| engine_notes | Set keys at production time rather than repairing them at the connector, because ordering is decided before the sink edge. |
| evidence | PIPE-04, research/design_decision_matrix.md#PL-17, research/data_pipeline_architecture.md#9 |
| evidence_strength | single_vendor |
| status | active |
| decision_ref | null |
| check_method | manual_review |
| check_description | Each applied transform is listed in the dataset's documentation. |
| lifecycle_stage | ETL/ELT |

## Data quality and validation (DQA)

### DQA-001 Layered validation

Validation SHOULD combine source constraints, pipeline gates and warehouse tests according to the failure class each catches.

| Field | Value |
|---|---|
| level | RECOMMENDED |
| scope | all |
| applies_when | always |
| rationale | Each layer catches a different failure class, so relying on one leaves the others undetected. |
| exceptions | Exception recorded with a reason and approved by the dataset owner |
| engine_notes | No controlled comparison of defect-catch rates exists, so the layering is a judgment. |
| evidence | DQ-03, DQ-14, DQ-12, LAKE-19, research/design_decision_matrix.md#DV-1, research/data_engineering_principles.md#4.1, research/data_engineering_principles.md#11 |
| evidence_strength | multi_vendor |
| status | active |
| decision_ref | null |
| check_method | manual_review |
| check_description | The dataset's validation plan names the layer covering each failure class. |
| lifecycle_stage | Data Validation |

### DQA-002 OLTP constraints at the source

OLTP systems of record MUST enforce integrity with database constraints at the point of write.

| Field | Value |
|---|---|
| level | MANDATORY |
| scope | OLTP |
| applies_when | the system is a non-sharded OLTP system of record; this rule does not apply to analytical systems |
| rationale | Nothing downstream can retroactively enforce what the source admitted. |
| exceptions | Exception recorded with a reason and approved by the framework exception approver |
| engine_notes | Detailed constraint rules belong to the relational integrity standards. Where foreign keys are unavailable, RI-2 keeps FK columns, indexes, orphan audits and a documented risk. |
| evidence | PGMY-01, MSOM-02, MSOM-08, research/design_decision_matrix.md#DV-2, research/design_decision_matrix.md#RI-2 |
| evidence_strength | multi_vendor |
| status | active |
| decision_ref | null |
| check_method | schema_lint |
| check_description | Tables in the system of record declare their key, reference and value constraints. |
| lifecycle_stage | Data Validation |

### DQA-003 Declared keys are not assumed enforced

Analytical platforms MUST NOT rely on a declared primary key, foreign key or unique constraint as proof of integrity unless the platform documents enforcement for that table type.

| Field | Value |
|---|---|
| level | MANDATORY |
| scope | data_warehouse, lakehouse, OLAP |
| applies_when | always, on warehouse and lakehouse tables; this is the opposite of the OLTP position in DQA-002 |
| rationale | Standard warehouses accept duplicates and orphans silently, and a declaration suggests a guarantee that does not exist. |
| exceptions | none |
| engine_notes | Snowflake standard tables and Databricks do not enforce PK, FK or UNIQUE; NOT NULL and CHECK are enforced. Snowflake hybrid tables enforce them. Microsoft Fabric records them only. Platform documentation prevails over dbt's summary. |
| evidence | LAKE-09, LAKE-02, DQ-03, research/design_decision_matrix.md#RI-11, research/data_engineering_principles.md#4.2, research/data_pipeline_architecture.md#2 |
| evidence_strength | multi_vendor |
| status | active |
| decision_ref | null |
| check_method | catalog_query |
| check_description | For each analytical table type in use, the record states which constraints the platform enforces. |
| lifecycle_stage | Data Validation |

### DQA-004 Substitute for key uniqueness

Every analytical model SHOULD have uniqueness and non-null tests on its key, plus pipeline merge on that key, in place of enforced keys.

| Field | Value |
|---|---|
| level | RECOMMENDED |
| scope | data_warehouse, lakehouse |
| applies_when | the platform does not enforce the key for this table type (DQA-003) |
| rationale | Without a substitute, duplicates inflate measures with no error raised. |
| exceptions | Exception recorded with a reason and approved by the dataset owner |
| engine_notes | dbt recommends the primary-key test. Tests run after the data exists, so publishing depends on DQA-007 and DQA-008. |
| evidence | LAKE-19, DQ-03, LAKE-02, LAKE-09, ENG-23, research/design_decision_matrix.md#RI-11, research/design_decision_matrix.md#TS-8, research/data_engineering_principles.md#4.3 |
| evidence_strength | multi_vendor |
| status | active |
| decision_ref | B1 |
| check_method | pipeline_test |
| check_description | Each model has passing unique and not-null tests on its declared key. |
| lifecycle_stage | Data Validation |

### DQA-005 Substitute for referential integrity

Foreign key relationships in analytical models SHOULD be protected by relationship tests or ETL key lookups with an orphan count.

| Field | Value |
|---|---|
| level | RECOMMENDED |
| scope | data_warehouse, lakehouse |
| applies_when | the platform does not enforce foreign keys for this table type (DQA-003) |
| rationale | Orphans silently drop rows in inner joins, and no error is raised. |
| exceptions | Exception recorded with a reason and approved by the dataset owner |
| engine_notes | Kimball-method fact tables pair lookups with default dimension rows (RPT-006). |
| evidence | LAKE-19, DES-12, research/design_decision_matrix.md#RI-12, research/design_decision_matrix.md#TS-8, research/data_engineering_principles.md#4.3 |
| evidence_strength | multi_vendor |
| status | active |
| decision_ref | null |
| check_method | pipeline_test |
| check_description | Relationship tests or lookup orphan counts exist for each declared foreign key. |
| lifecycle_stage | Data Validation |

### DQA-006 Trust-the-constraint settings

An optimizer trust setting on an unenforced constraint SHOULD be enabled only when the data has been verified to comply.

| Field | Value |
|---|---|
| level | RECOMMENDED |
| scope | data_warehouse, lakehouse |
| applies_when | the platform allows the optimizer to rely on unenforced constraints |
| rationale | An optimizer that trusts an unenforced key can return wrong results if the data does not comply. |
| exceptions | Exception recorded with a reason and approved by the dataset owner |
| engine_notes | Snowflake RELY is only appropriate if compliance is ensured. Databricks defaults to NORELY. Redshift's planner assumes keys are valid and advises against declaring doubtful keys. |
| evidence | LAKE-09, MSOM-12, ENG-23, ENG-29, research/design_decision_matrix.md#RI-12, research/data_engineering_principles.md#4.2 |
| evidence_strength | multi_vendor |
| status | active |
| decision_ref | null |
| check_method | catalog_query |
| check_description | Constraints with trust enabled have corresponding passing tests. |
| lifecycle_stage | Data Validation |

### DQA-007 Promotion gate

Consumer-facing datasets SHOULD be written out of view, audited, and only then published.

| Field | Value |
|---|---|
| level | RECOMMENDED |
| scope | data_warehouse, lakehouse |
| applies_when | the dataset is published to consumers |
| rationale | Post-hoc tests expose bad data to consumers before anyone can respond. |
| exceptions | Exception recorded with a reason and approved by the dataset owner |
| engine_notes | Iceberg audit branches and Databricks expect_or_fail implement this. Netflix notes not every table needs coverage. The matrix holds this as RECOMMENDED. |
| evidence | DQ-12, DQ-13, DQ-14, research/design_decision_matrix.md#DV-3, research/data_engineering_principles.md#4.3 |
| evidence_strength | multi_vendor |
| status | active |
| decision_ref | null |
| check_method | pipeline_test |
| check_description | A failed audit leaves the published dataset unchanged. |
| lifecycle_stage | Data Validation |

### DQA-008 Blocking checks must block

A check defined as blocking MUST be wired so that its failure prevents downstream publication.

| Field | Value |
|---|---|
| level | MANDATORY |
| scope | data_warehouse, lakehouse |
| applies_when | a check is designated as blocking in the severity tiers (DQA-009) |
| rationale | Vendors state that a failing check does not by itself stop downstream work, so consumers are unprotected while the check appears to exist. |
| exceptions | none |
| engine_notes | Dagster asset checks stop downstream materialization only with blocking=True. Databricks states expectations control data quality and not orchestration. |
| evidence | DQ-14, research/data_pipeline_architecture.md#14.2 |
| evidence_strength | multi_vendor |
| status | active |
| decision_ref | null |
| check_method | pipeline_test |
| check_description | Force a blocking check to fail and confirm downstream publication does not occur. |
| lifecycle_stage | Data Quality |

### DQA-009 Severity tiers

Quality checks SHOULD be assigned a severity tier of warn, quarantine or fail according to dataset criticality.

| Field | Value |
|---|---|
| level | RECOMMENDED |
| scope | data_warehouse, lakehouse |
| applies_when | always, for checks on datasets with consumers |
| rationale | An all-blocking policy trades availability away, and an all-warning policy lets bad data through. |
| exceptions | Exception recorded with a reason and approved by the dataset owner |
| engine_notes | Netflix, Databricks and dbt use tiers; Databricks warns by default. |
| evidence | DQ-13, DQ-14, LAKE-19, research/design_decision_matrix.md#DV-4, research/data_engineering_principles.md#11 |
| evidence_strength | multi_vendor |
| status | active |
| decision_ref | null |
| check_method | catalog_query |
| check_description | Each check has a recorded severity. |
| lifecycle_stage | Data Quality |

### DQA-010 Financial quality failures block publication

Quality failures on financial datasets SHOULD block publication for checks on amounts and completeness, and other checks SHOULD be tiered.

| Field | Value |
|---|---|
| level | RECOMMENDED |
| scope | data_warehouse, lakehouse |
| applies_when | the dataset feeds financial reporting |
| rationale | Publishing incorrect financial figures has a higher cost than delayed publication. |
| exceptions | Exception recorded with a reason and approved by the framework exception approver |
| engine_notes | Intuit's circuit breaker is the only source and is blocking. Tiered sources differ, and Intuit stage-gating mechanics are excluded as unverified. No comparison exists, so this is a judgment. |
| evidence | research/design_decision_matrix.md#DV-4, research/data_engineering_principles.md#10.1, research/data_engineering_principles.md#11 |
| evidence_strength | case_study |
| status | active |
| decision_ref | B26 |
| check_method | pipeline_test |
| check_description | Failing amount or completeness checks on financial datasets stop publication. |
| lifecycle_stage | Data Quality |

### DQA-011 Rejected rows are captured and counted

Rows rejected by validation SHOULD be routed to a quarantine or dead-letter location and counted, and SHOULD NOT be silently dropped.

| Field | Value |
|---|---|
| level | RECOMMENDED |
| scope | lakehouse, streaming |
| applies_when | validation can reject individual rows |
| rationale | Silently dropped rows produce incomplete results that no check reports. |
| exceptions | Exception recorded with a reason and approved by the dataset owner |
| engine_notes | Kafka Connect with errors.tolerance=all skips errors without logging to the worker log; DLQs apply only to sink connectors and context headers default off. Databricks shows a flagged table with filtered views. Kimball describes an error-event schema for warehouses. |
| evidence | DQ-14, research/design_decision_matrix.md#DV-5, research/data_pipeline_architecture.md#9, research/data_engineering_principles.md#4.3, research/data_engineering_principles.md#6.2 |
| evidence_strength | multi_vendor |
| status | active |
| decision_ref | null |
| check_method | runtime_monitor |
| check_description | Input count equals accepted plus quarantined count for each batch. |
| lifecycle_stage | Data Quality |

### DQA-012 Quality vocabulary

Quality rules SHOULD use one dimension vocabulary, the DAMA UK six plus currency, mapped to ISO/IEC 25012.

| Field | Value |
|---|---|
| level | RECOMMENDED |
| scope | all |
| applies_when | always |
| rationale | Differing vocabularies make quality results incomparable. |
| exceptions | Exception recorded with a reason and approved by the framework exception approver |
| engine_notes | DAMA UK and ISO/IEC 25012 differ, and the GOV.UK text allows other dimensions. ISO/IEC 25012 definitions were read only on a secondary site, so confirm them before citing as ISO text. DMBOK is voluntary and is cited as vocabulary only. |
| evidence | GOV-03, GOV-04, GOV-10, GOV-11, GOV-12, GOV-02, research/design_decision_matrix.md#DV-6, research/data_engineering_principles.md#7.1 |
| evidence_strength | standard |
| status | active |
| decision_ref | C11 |
| check_method | manual_review |
| check_description | Quality rules each map to one dimension in the adopted vocabulary. |
| lifecycle_stage | Data Quality |

### DQA-013 Dimensions mapped to enforcement points

Each adopted quality dimension SHOULD be mapped to its enforcement mechanism per workload and to a monitoring signal.

| Field | Value |
|---|---|
| level | RECOMMENDED |
| scope | OLTP, data_warehouse, lakehouse |
| applies_when | a vocabulary has been adopted under DQA-012 |
| rationale | Unmapped dimensions are measured nowhere, and OLTP and warehouse mechanisms are not interchangeable. |
| exceptions | Exception recorded with a reason and approved by the dataset owner |
| engine_notes | Accuracy is not provable by schema alone in any workload. |
| evidence | research/data_engineering_principles.md#7.2 |
| evidence_strength | inference |
| status | provisional |
| decision_ref | null |
| check_method | manual_review |
| check_description | A mapping exists for each dimension, separately for OLTP and analytical layers. |
| lifecycle_stage | Data Quality |

### DQA-014 Critical data elements

Quality measurement SHOULD focus on identified critical data elements.

| Field | Value |
|---|---|
| level | RECOMMENDED |
| scope | all |
| applies_when | always |
| rationale | Measuring everything equally spreads effort thinly and misses what matters. |
| exceptions | Exception recorded with a reason and approved by the dataset owner |
| engine_notes | DMBOK2R defines critical data elements, but DAMA states DMBOK is not a prescriptive standard, so it supplies vocabulary only and is not the source of obligation. |
| evidence | GOV-04, GOV-02, research/data_engineering_principles.md#7.2 |
| evidence_strength | single_vendor |
| status | provisional |
| decision_ref | null |
| check_method | manual_review |
| check_description | A list of critical data elements exists and each has quality rules. |
| lifecycle_stage | Data Quality |

### DQA-015 Batch reconciliation

Consumer-facing batch loads SHOULD compare source and target row counts and at least one aggregate.

| Field | Value |
|---|---|
| level | RECOMMENDED |
| scope | data_warehouse, lakehouse |
| applies_when | the load produces a consumer-facing dataset |
| rationale | Counts alone miss wrong values, and unreconciled loads can lose data unnoticed. |
| exceptions | Exception recorded with a reason and approved by the dataset owner |
| engine_notes | Soda, Databricks and Netflix provide count mechanisms. No source defines a universal control-record design. |
| evidence | DQ-04, DQ-14, DQ-13, DQ-15, research/design_decision_matrix.md#DV-7, research/data_engineering_principles.md#6.2 |
| evidence_strength | multi_vendor |
| status | active |
| decision_ref | B1 |
| check_method | pipeline_test |
| check_description | Each batch has a recorded count and aggregate comparison. |
| lifecycle_stage | Data Quality |

### DQA-016 Financial amounts must tie

Reconciliation of financial pipelines SHOULD compare amounts as well as counts at every layer.

| Field | Value |
|---|---|
| level | RECOMMENDED |
| scope | data_warehouse, lakehouse |
| applies_when | the pipeline carries financial amounts |
| rationale | Matching counts can hide wrong or duplicated amounts. |
| exceptions | Exception recorded with a reason and approved by the dataset owner |
| engine_notes | No source states this as a pipeline rule. |
| evidence | DQ-16, research/data_engineering_principles.md#4.3, research/data_engineering_principles.md#6.3 |
| evidence_strength | inference |
| status | provisional |
| decision_ref | null |
| check_method | pipeline_test |
| check_description | Financial reconciliation records include amount totals by currency. |
| lifecycle_stage | Data Quality |

### DQA-017 Subledger to ledger reconciliation

Financial pipelines SHOULD reconcile subledger to general ledger per closed period and SHOULD classify and explain each difference.

| Field | Value |
|---|---|
| level | RECOMMENDED |
| scope | data_warehouse |
| applies_when | the warehouse reports on subledger and general ledger data |
| rationale | Unclassified differences make the reported figures unprovable at period close. |
| exceptions | Exception recorded with a reason and approved by the framework exception approver |
| engine_notes | Oracle Fusion runs this after periods close to new transactions and classifies differences. The page states no numeric zero-difference target; no numeric tolerance is set under decision B27. |
| evidence | DQ-16, TEN-43, research/design_decision_matrix.md#DV-8, research/data_engineering_principles.md#6.3 |
| evidence_strength | single_vendor |
| status | active |
| decision_ref | B27 |
| check_method | manual_review |
| check_description | Each closed period has a reconciliation with differences classified. |
| lifecycle_stage | Data Quality |

### DQA-018 Row-level difference checks

Migration and replication validation MAY use row-level hash or segment differences.

| Field | Value |
|---|---|
| level | OPTIONAL |
| scope | all |
| applies_when | data is being migrated or replicated and aggregates are insufficient |
| rationale | Aggregates can balance while individual rows differ. |
| exceptions | none |
| engine_notes | data-diff is archived, and reladiff is a fork that publishes its own benchmarks. |
| evidence | DQ-17, research/design_decision_matrix.md#DV-9, research/data_engineering_principles.md#6.3 |
| evidence_strength | single_vendor |
| status | active |
| decision_ref | null |
| check_method | pipeline_test |
| check_description | If used, the difference report is retained with the migration record. |
| lifecycle_stage | Data Quality |

### DQA-019 Audit dimension

Fact tables SHOULD carry an audit dimension recording load context and quality flags.

| Field | Value |
|---|---|
| level | RECOMMENDED |
| scope | data_warehouse |
| applies_when | the warehouse uses dimensional fact tables |
| rationale | Consumers cannot tell which load produced a row or whether it carries a warning. |
| exceptions | Exception recorded with a reason and approved by the dataset owner |
| engine_notes | Kimball treats flags as warnings to users and advises starting simply. |
| evidence | DQ-15, research/data_engineering_principles.md#6.3 |
| evidence_strength | single_vendor |
| status | active |
| decision_ref | null |
| check_method | schema_lint |
| check_description | Fact tables reference an audit dimension or equivalent load context. |
| lifecycle_stage | Data Quality |

### DQA-020 Data contract for shared datasets

Datasets crossing a team boundary SHOULD have a contract recording schema, owner, service level, quality rules and version.

| Field | Value |
|---|---|
| level | RECOMMENDED |
| scope | data_warehouse, lakehouse, streaming |
| applies_when | the dataset is consumed by another team |
| rationale | Producers change shape or meaning without notice and consumers break. |
| exceptions | Exception recorded with a reason and approved by the dataset owner |
| engine_notes | A registry enforces compatibility, while a contract is the broader agreement (ODCS). The agility cost is argued but not measured. dbt contracts cover shape only. |
| evidence | PIPE-20, ARCH-23, DQ-03, PIPE-03, research/design_decision_matrix.md#DV-10, research/data_engineering_principles.md#4.4 |
| evidence_strength | multi_vendor |
| status | active |
| decision_ref | null |
| check_method | catalog_query |
| check_description | Each cross-team dataset has a versioned contract with the listed sections. |
| lifecycle_stage | Data Validation |

### DQA-021 Contract enforcement point

Contracts MAY be enforced in producer CI, in the pipeline, or in the warehouse.

| Field | Value |
|---|---|
| level | OPTIONAL |
| scope | data_warehouse, lakehouse, streaming |
| applies_when | a contract exists |
| rationale | Enforcement later in the flow detects breaks later, while producer enforcement costs producers effort. |
| exceptions | none |
| engine_notes | The sources advocating producer enforcement are parties selling or advocating this approach, and the maturity progression is inference. |
| evidence | DQ-11, DQ-03, research/design_decision_matrix.md#DV-11 |
| evidence_strength | single_vendor |
| status | active |
| decision_ref | null |
| check_method | manual_review |
| check_description | The contract states where it is enforced. |
| lifecycle_stage | Data Validation |

### DQA-022 Specifications over tools

Quality and contract rules SHOULD be expressed against open specifications and capabilities, with tools named only as examples.

| Field | Value |
|---|---|
| level | RECOMMENDED |
| scope | all |
| applies_when | always |
| rationale | Tools churn, and rules tied to them are lost when a tool is archived. |
| exceptions | Exception recorded with a reason and approved by the dataset owner |
| engine_notes | data-diff and Amundsen are archived. |
| evidence | PIPE-20, GOV-31, research/design_decision_matrix.md#DV-13, research/data_engineering_principles.md#6.4 |
| evidence_strength | inference |
| status | provisional |
| decision_ref | null |
| check_method | manual_review |
| check_description | Standards text states the required capability, and any tool reference is an example. |
| lifecycle_stage | Data Quality |

### DQA-023 Registered stream compatibility

Topics crossing a team boundary SHOULD have a registered schema and a compatibility mode other than NONE.

| Field | Value |
|---|---|
| level | RECOMMENDED |
| scope | streaming |
| applies_when | producers and consumers deploy independently |
| rationale | Incompatible producer changes break consumers at read time. |
| exceptions | Exception recorded with a reason and approved by the dataset owner |
| engine_notes | Compatibility vocabulary comes from Confluent's documentation; no neutral standard defines it. |
| evidence | PIPE-02, research/design_decision_matrix.md#DV-14, research/data_pipeline_architecture.md#8.3 |
| evidence_strength | single_vendor |
| status | active |
| decision_ref | null |
| check_method | catalog_query |
| check_description | Each cross-team topic has a registered schema and a mode other than NONE. |
| lifecycle_stage | Data Validation |

### DQA-024 Transitive compatibility for long-lived data

Compacted, long-retention or replayed topics SHOULD use a transitive compatibility mode.

| Field | Value |
|---|---|
| level | RECOMMENDED |
| scope | streaming |
| applies_when | consumers may read records older than the previous schema version |
| rationale | Non-transitive checks permit a chain where the newest schema cannot read data two versions back. |
| exceptions | Exception recorded with a reason and approved by the dataset owner |
| engine_notes | The registry default is non-transitive. Confluent names BACKWARD_TRANSITIVE as Protobuf best practice. |
| evidence | PIPE-02, research/design_decision_matrix.md#DV-15, research/data_pipeline_architecture.md#8.3 |
| evidence_strength | single_vendor |
| status | active |
| decision_ref | null |
| check_method | catalog_query |
| check_description | Long-retention topics are configured with a transitive mode. |
| lifecycle_stage | Data Validation |

### DQA-025 Deployment order follows compatibility mode

The deployment order of producers and consumers SHOULD follow the topic's compatibility mode and be part of the change plan.

| Field | Value |
|---|---|
| level | RECOMMENDED |
| scope | streaming |
| applies_when | a schema change is deployed to a registered topic |
| rationale | Deploying in the wrong order breaks readers even for compatible changes. |
| exceptions | Exception recorded with a reason and approved by the dataset owner |
| engine_notes | BACKWARD upgrades consumers first and FORWARD upgrades producers first. Table loaders count as consumers. |
| evidence | PIPE-02, research/data_pipeline_architecture.md#8.1, research/data_pipeline_architecture.md#8.3 |
| evidence_strength | single_vendor |
| status | active |
| decision_ref | null |
| check_method | manual_review |
| check_description | The change plan states an order consistent with the mode. |
| lifecycle_stage | Data Validation |

## Reporting and analytical models (RPT)

### RPT-001 Consumption shape

Analytical consumption models SHOULD default to a star schema, with wide tables built only as derived layers.

| Field | Value |
|---|---|
| level | RECOMMENDED |
| scope | OLAP, data_warehouse, lakehouse |
| applies_when | a model is exposed to reporting consumers; not an OLTP pattern |
| rationale | Without a default shape, each mart makes the trade-off differently and queries become hard to reuse. |
| exceptions | Exception recorded with a reason and approved by the framework exception approver |
| engine_notes | [WF] re-check needed: the vendor-hosted test finding flat tables faster on three platforms was read only through a summarizing fetch. Benchmarks disagree on Redshift and differ on keys and distribution, so query speed gives no general rule and this is a judgment. Nested shapes suit BigQuery. dbt prefers wide marts except under its Semantic Layer. |
| evidence | DWM-14, CLOUD-21, LAKE-14, CLOUD-12, DWM-22, BENCH-10, research/design_decision_matrix.md#RP-1, research/data_modeling_approaches.md#7, research/data_modeling_approaches.md#18.4 |
| evidence_strength | multi_vendor |
| status | active |
| decision_ref | B24 |
| check_method | manual_review |
| check_description | Each consumption model records its shape, and wide tables identify the model they derive from. |
| lifecycle_stage | Reporting |

### RPT-002 Integration layer

A warehouse MAY add a 3NF or Data Vault integration layer below its marts, where sources are many or audit needs require one.

| Field | Value |
|---|---|
| level | OPTIONAL |
| scope | data_warehouse, lakehouse |
| applies_when | a warehouse architecture is being chosen |
| rationale | A needless layer adds load complexity, while a missing one makes multi-source reconciliation hard. |
| exceptions | none |
| engine_notes | Kimball and Inmon disagree and neither has retracted; both accept hybrids. |
| evidence | DWM-04, DWM-06, DWM-08, DWM-14, research/design_decision_matrix.md#RP-2, research/data_modeling_approaches.md#18.1 |
| evidence_strength | multi_vendor |
| status | active |
| decision_ref | null |
| check_method | manual_review |
| check_description | The design record states whether an integration layer exists and why. |
| lifecycle_stage | Reporting |

### RPT-003 Declared single grain

Fact tables MUST have a declared single grain before dimensions and facts are chosen.

| Field | Value |
|---|---|
| level | MANDATORY |
| scope | OLAP, data_warehouse |
| applies_when | the model is presented as following the Kimball dimensional method; teams not using that method are not bound |
| rationale | Mixed grains double count measures and break aggregation. |
| exceptions | none |
| engine_notes | Obligation within the Kimball method only. Wide tables should keep one grain as well (RECOMMENDED, inference). |
| evidence | DWM-01, DWM-02, research/design_decision_matrix.md#RP-3, research/data_modeling_approaches.md#3 |
| evidence_strength | single_vendor |
| status | active |
| decision_ref | H2 |
| check_method | manual_review |
| check_description | Each fact table has a one-sentence grain statement and contains only that grain. |
| lifecycle_stage | Reporting |

### RPT-004 Conformed dimensions in Kimball models

Marts built under the Kimball method MUST use conformed dimensions for shared entities.

| Field | Value |
|---|---|
| level | MANDATORY |
| scope | data_warehouse |
| applies_when | the model is presented as following the Kimball method |
| rationale | Independent marts produce conflicting figures for the same entity. |
| exceptions | none |
| engine_notes | Obligation within the Kimball method only. |
| evidence | DWM-01, DWM-02, research/design_decision_matrix.md#RP-4 |
| evidence_strength | single_vendor |
| status | active |
| decision_ref | H2 |
| check_method | manual_review |
| check_description | Shared dimensions appear once on the bus matrix and are reused across facts. |
| lifecycle_stage | Reporting |

### RPT-005 Avoid stovepipe marts

Warehouses outside the Kimball method SHOULD share conformed or integrated entities across marts.

| Field | Value |
|---|---|
| level | RECOMMENDED |
| scope | data_warehouse |
| applies_when | the warehouse has more than one mart and is not bound by RPT-004 |
| rationale | Kimball and Inmon both reject stovepipes because separately defined entities cannot be compared. |
| exceptions | Exception recorded with a reason and approved by the dataset owner |
| engine_notes | Inmon argues conformed dimensions are insufficient on their own. |
| evidence | DWM-01, DWM-04, DWM-06, research/design_decision_matrix.md#RP-4 |
| evidence_strength | single_vendor |
| status | active |
| decision_ref | null |
| check_method | manual_review |
| check_description | Shared entities across marts have a common definition. |
| lifecycle_stage | Reporting |

### RPT-006 No null fact foreign keys

Fact-table foreign keys under the Kimball method MUST NOT be null and MUST point to a default dimension row when unknown.

| Field | Value |
|---|---|
| level | MANDATORY |
| scope | data_warehouse |
| applies_when | the model is presented as following the Kimball method |
| rationale | Nulls drop rows from inner joins and hide unknown members from reports. |
| exceptions | none |
| engine_notes | Obligation within the Kimball method only. The warehouse will not enforce this, so it needs a test under DQA-005. |
| evidence | DWM-01, DWM-02, research/design_decision_matrix.md#RP-5, research/data_modeling_approaches.md#3 |
| evidence_strength | single_vendor |
| status | active |
| decision_ref | H2 |
| check_method | pipeline_test |
| check_description | No fact foreign key column contains a null, and default rows exist. |
| lifecycle_stage | Reporting |

### RPT-007 Dimension key type

Dimension key type SHOULD default to numeric surrogates in dimensional marts, as set in IDX-024.

| Field | Value |
|---|---|
| level | RECOMMENDED |
| scope | data_warehouse, lakehouse |
| applies_when | a dimension is being designed |
| rationale | Key type affects join speed and whether parallel, idempotent loads are possible, and mixed practice complicates integration. |
| exceptions | Exception recorded with a reason and approved by the framework exception approver |
| engine_notes | Kimball and Snowflake favour numeric keys. dbt prefers strings and hashed keys. Databricks prefers natural or identity keys in dimensional models and hash keys in Data Vault. No benchmark exists; this is a judgment. Superseded by IDX-024 under OR-3. |
| evidence | DWM-01, DWM-19, DWM-21, LAKE-14, LAKE-16, research/design_decision_matrix.md#RP-6, research/data_modeling_approaches.md#18.3, research/data_engineering_principles.md#9.3 |
| evidence_strength | multi_vendor |
| status | superseded |
| decision_ref | A4 |
| superseded_by | IDX-024 |
| check_method | manual_review |
| check_description | The platform's key type decision is recorded and followed. |
| lifecycle_stage | Reporting |

### RPT-008 Attribute history policy

Each dimension attribute MAY use any slowly changing dimension type or snapshot, chosen and recorded per attribute, with Type 2 for attributes that must be reconstructable.

| Field | Value |
|---|---|
| level | OPTIONAL |
| scope | data_warehouse, lakehouse |
| applies_when | a dimension has attributes that change |
| rationale | Unrecorded choices make as-was reporting unreliable. |
| exceptions | none |
| engine_notes | Snowflake dynamic tables cannot express SCD2. Time travel should not be the basis of SCD history, as Databricks table history is not for long-term retention (inference). |
| evidence | DWM-01, TEN-24, LAKE-18, LAKE-12, research/design_decision_matrix.md#RP-7, research/data_modeling_approaches.md#18.6 |
| evidence_strength | single_vendor |
| status | active |
| decision_ref | null |
| check_method | manual_review |
| check_description | Each changing attribute has a recorded history type. |
| lifecycle_stage | Reporting |

### RPT-009 Protect unrebuildable history

Captured history such as snapshots SHOULD use a verified unique key and be stored apart from rebuildable models.

| Field | Value |
|---|---|
| level | RECOMMENDED |
| scope | data_warehouse |
| applies_when | the warehouse captures history by snapshot |
| rationale | Snapshots cannot be rebuilt once lost, and a non-unique key corrupts them silently. |
| exceptions | Exception recorded with a reason and approved by the dataset owner |
| engine_notes | dbt says snapshots cannot be rebuilt and suggests a separate schema. |
| evidence | LAKE-18, research/data_pipeline_architecture.md#16, research/data_engineering_principles.md#9.2 |
| evidence_strength | single_vendor |
| status | active |
| decision_ref | null |
| check_method | pipeline_test |
| check_description | The snapshot key has a passing uniqueness test and the snapshot is excluded from full-refresh rebuilds. |
| lifecycle_stage | Reporting |

### RPT-010 Late-arriving facts

Late-arriving facts SHOULD resolve dimension keys as of the event date using effective-dated lookups.

| Field | Value |
|---|---|
| level | RECOMMENDED |
| scope | data_warehouse |
| applies_when | facts can arrive after the event date and dimensions keep history |
| rationale | Current-row lookups attribute old facts to the wrong dimension version. |
| exceptions | Exception recorded with a reason and approved by the dataset owner |
| engine_notes | Late-arriving dimension placeholders have no source; see RPT-019. |
| evidence | DWM-01, DES-12, research/design_decision_matrix.md#RP-14, research/data_pipeline_architecture.md#17.1 |
| evidence_strength | single_vendor |
| status | active |
| decision_ref | null |
| check_method | pipeline_test |
| check_description | A late fact joins to the dimension version effective on its event date. |
| lifecycle_stage | Reporting |

### RPT-011 Aggregates

Warehouse aggregation SHOULD use materialized views, aggregate tables or on-demand query, chosen by refresh and query cost.

| Field | Value |
|---|---|
| level | RECOMMENDED |
| scope | OLAP, data_warehouse |
| applies_when | the workload aggregates large analytical data; not for high-DML OLTP tables |
| rationale | Unmanaged aggregates become stale or costly. |
| exceptions | Exception recorded with a reason and approved by the dataset owner |
| engine_notes | This rule is not applicable to OLTP tables with high write rates. |
| evidence | PERF-26, PERF-04, PERF-38, research/design_decision_matrix.md#RP-8 |
| evidence_strength | multi_vendor |
| status | active |
| decision_ref | null |
| check_method | manual_review |
| check_description | Each aggregate records its refresh method and source. |
| lifecycle_stage | Reporting |

### RPT-012 Semantic layer

Metrics MAY be defined in a semantic layer.

| Field | Value |
|---|---|
| level | OPTIONAL |
| scope | OLAP, data_warehouse |
| applies_when | a semantic layer tool is available |
| rationale | Metric logic spread across reports diverges. |
| exceptions | none |
| engine_notes | Tool dependence is the cost. Airbnb's metric platform details are unverified and are not used. |
| evidence | LAKE-06, research/design_decision_matrix.md#RP-9 |
| evidence_strength | single_vendor |
| status | active |
| decision_ref | null |
| check_method | manual_review |
| check_description | If used, metrics resolve to the semantic layer. |
| lifecycle_stage | Reporting |

### RPT-013 One governed definition per metric

Each published metric SHOULD have one governed definition, and any provisional result from a second path SHOULD be labelled.

| Field | Value |
|---|---|
| level | RECOMMENDED |
| scope | OLAP, data_warehouse |
| applies_when | a metric appears in more than one report or path |
| rationale | The Dataflow paper reports customers ceasing to trust results when two paths disagreed. |
| exceptions | Exception recorded with a reason and approved by the dataset owner |
| engine_notes | Framework position derived from the trust finding; no source prescribes this. |
| evidence | PIPE-17, research/data_engineering_principles.md#9.2, research/data_pipeline_architecture.md#5.2 |
| evidence_strength | inference |
| status | provisional |
| decision_ref | null |
| check_method | manual_review |
| check_description | Each metric has one definition, and dual-path results carry a label. |
| lifecycle_stage | Reporting |

### RPT-014 Operational report source

Operational reports SHOULD read a replica unless the report drives a transaction.

| Field | Value |
|---|---|
| level | RECOMMENDED |
| scope | OLTP, OLAP |
| applies_when | a report runs against operational data |
| rationale | Reports on the primary compete with transactions, while replica staleness can mislead reports that drive decisions. |
| exceptions | Exception recorded with a reason and approved by the dataset owner |
| engine_notes | Replica lag and read-your-writes behaviour differ by engine. |
| evidence | CLOUD-16, research/design_decision_matrix.md#RP-10 |
| evidence_strength | case_study |
| status | active |
| decision_ref | null |
| check_method | manual_review |
| check_description | Each operational report records its endpoint and why. |
| lifecycle_stage | Reporting |

### RPT-015 Vault through information marts

Data Vault structures MUST be exposed to consumers only through information marts.

| Field | Value |
|---|---|
| level | MANDATORY |
| scope | data_warehouse |
| applies_when | the warehouse follows the Data Vault method |
| rationale | Direct vault access exposes consumers to raw history and complex joins. |
| exceptions | none |
| engine_notes | Obligation within the Data Vault method only. No independent benchmark compares Data Vault with star schemas. |
| evidence | DWM-08, research/design_decision_matrix.md#RP-11 |
| evidence_strength | single_vendor |
| status | active |
| decision_ref | H2 |
| check_method | catalog_query |
| check_description | Consumer roles have no direct grant on vault tables. |
| lifecycle_stage | Reporting |

### RPT-016 Activity Schema

Single-entity behavioural analytics MAY use an Activity Schema.

| Field | Value |
|---|---|
| level | OPTIONAL |
| scope | OLAP |
| applies_when | the analysis is single-entity behavioural; not for multi-entity financial reporting |
| rationale | Used outside its scope, the pattern cannot support multi-entity reporting. |
| exceptions | none |
| engine_notes | none |
| evidence | DWM-24, research/design_decision_matrix.md#RP-12 |
| evidence_strength | single_vendor |
| status | active |
| decision_ref | null |
| check_method | manual_review |
| check_description | The design record shows the use is single-entity. |
| lifecycle_stage | Reporting |

### RPT-017 Financial reporting models

Financial reporting models SHOULD use reconciled facts with planned multi-currency and allocation grains.

| Field | Value |
|---|---|
| level | RECOMMENDED |
| scope | data_warehouse |
| applies_when | the warehouse serves financial reporting; these models are not ledgers of record |
| rationale | Unplanned allocation and currency grains produce figures that cannot be tied back. |
| exceptions | Exception recorded with a reason and approved by the dataset owner |
| engine_notes | Balances are semi-additive across time (inference). Periodic snapshots fit balances (inference). |
| evidence | DWM-01, DQ-16, research/design_decision_matrix.md#RP-13 |
| evidence_strength | single_vendor |
| status | active |
| decision_ref | null |
| check_method | manual_review |
| check_description | Financial facts state their grain, currency treatment and reconciliation source. |
| lifecycle_stage | Reporting |

### RPT-018 Freshness and close state visible

Financial reports SHOULD show consumers the data freshness, period-close state, and any restatement after close.

| Field | Value |
|---|---|
| level | RECOMMENDED |
| scope | data_warehouse |
| applies_when | the report presents financial periods |
| rationale | Consumers can act on open-period figures believing them final. |
| exceptions | Exception recorded with a reason and approved by the dataset owner |
| engine_notes | dbt source freshness is one mechanism. No source defines restatement behaviour. |
| evidence | DQ-16, research/data_engineering_principles.md#9.2, research/data_pipeline_architecture.md#17.2 |
| evidence_strength | inference |
| status | provisional |
| decision_ref | null |
| check_method | manual_review |
| check_description | Report output shows freshness and period status. |
| lifecycle_stage | Reporting |

### RPT-019 Late-arriving dimensions use a placeholder member

A fact whose dimension has not yet arrived SHOULD reference a placeholder dimension member that is updated when the dimension arrives.

| Field | Value |
|---|---|
| level | RECOMMENDED |
| scope | data_warehouse |
| applies_when | a fact can arrive before its dimension row |
| rationale | A placeholder keeps facts complete, at the cost of update logic. No source prescribes any option, so this is a judgment accepted under decision B29. |
| exceptions | Holding the fact, or assigning the default unknown member, recorded with a reason and approved by the dataset owner |
| engine_notes | Late-arriving dimension handling has no source in the research (LAT-05). The placeholder is a dimension row, so RPT-006 still holds. Late-arriving facts are RPT-010. |
| evidence | research/data_pipeline_architecture.md#17.2, research/data_pipeline_architecture.md#20.3 |
| evidence_strength | inference |
| status | provisional |
| decision_ref | B29 |
| check_method | pipeline_test |
| check_description | Load a fact before its dimension, then confirm a placeholder member exists and is updated when the dimension arrives. |
| lifecycle_stage | ETL/ELT |

## Monitoring and observability (MON)

### MON-001 Core data signals

Published datasets SHOULD be monitored for freshness, volume, schema change and distribution.

| Field | Value |
|---|---|
| level | RECOMMENDED |
| scope | data_warehouse, lakehouse, streaming |
| applies_when | the dataset has consumers |
| rationale | Failures that do not raise job errors reach consumers undetected. |
| exceptions | Exception recorded with a reason and approved by the dataset owner |
| engine_notes | Monte Carlo's five pillars are a vendor taxonomy and are not adopted. dbt warn_after and error_after are one freshness mechanism. |
| evidence | DQ-05, DQ-07, DQ-08, DQ-13, research/data_pipeline_architecture.md#8.1, research/data_engineering_principles.md#10.1 |
| evidence_strength | multi_vendor |
| status | active |
| decision_ref | null |
| check_method | runtime_monitor |
| check_description | Each signal has an active monitor for published datasets. |
| lifecycle_stage | Monitoring |

### MON-002 Persist quality metrics

Quality metric results SHOULD be persisted over time.

| Field | Value |
|---|---|
| level | RECOMMENDED |
| scope | data_warehouse, lakehouse |
| applies_when | anomaly or distributional checks are used |
| rationale | Single-run results cannot detect drift, and distributional checks need history. |
| exceptions | Exception recorded with a reason and approved by the dataset owner |
| engine_notes | Deequ's metrics repository and stored dbt failures are examples. |
| evidence | DQ-05, DQ-07, research/design_decision_matrix.md#DV-12, research/data_engineering_principles.md#7.2 |
| evidence_strength | multi_vendor |
| status | active |
| decision_ref | null |
| check_method | catalog_query |
| check_description | Metric history exists for monitored datasets. |
| lifecycle_stage | Monitoring |

### MON-003 CDC health

CDC pipelines SHOULD monitor lag, last-event age and connection state.

| Field | Value |
|---|---|
| level | RECOMMENDED |
| scope | OLTP, streaming |
| applies_when | log-based CDC is in use |
| rationale | Stalled capture is silent, and retained logs accumulate on the source. |
| exceptions | Exception recorded with a reason and approved by the dataset owner |
| engine_notes | Debezium exposes MilliSecondsBehindSource percentiles, MilliSecondsSinceLastEvent and Connected. Clock differences affect the lag value. Dropping a slot on the primary loses data. |
| evidence | PIPE-06, research/data_engineering_principles.md#10.1, research/data_pipeline_architecture.md#10.3 |
| evidence_strength | single_vendor |
| status | active |
| decision_ref | null |
| check_method | runtime_monitor |
| check_description | Alerts exist for lag, stale events and disconnection. |
| lifecycle_stage | Monitoring |

### MON-004 Stream consumer health

Stream consumers SHOULD be monitored for lag and dead-letter counts.

| Field | Value |
|---|---|
| level | RECOMMENDED |
| scope | streaming |
| applies_when | a stream consumer writes to a sink |
| rationale | Growing lag or dead-letter volume indicates data loss in progress. |
| exceptions | Exception recorded with a reason and approved by the dataset owner |
| engine_notes | Confluent recommends metrics or comparing source and processed counts where errors are tolerated. |
| evidence | research/design_decision_matrix.md#DV-5, research/data_pipeline_architecture.md#9 |
| evidence_strength | inference |
| status | provisional |
| decision_ref | null |
| check_method | runtime_monitor |
| check_description | Lag and dead-letter counts have monitors. |
| lifecycle_stage | Monitoring |

### MON-005 Alerts route to the recorded owner

Data alerts SHOULD route to the owner recorded in metadata.

| Field | Value |
|---|---|
| level | RECOMMENDED |
| scope | data_warehouse, lakehouse |
| applies_when | ownership metadata exists (GOV-002) |
| rationale | Alerts sent to a shared channel have no one accountable for acting on them. |
| exceptions | Exception recorded with a reason and approved by the dataset owner |
| engine_notes | No source specifies alert-routing or incident-response time targets. |
| evidence | DQ-07, research/data_engineering_principles.md#10.1 |
| evidence_strength | inference |
| status | provisional |
| decision_ref | null |
| check_method | catalog_query |
| check_description | Each monitored dataset resolves to an alert recipient. |
| lifecycle_stage | Monitoring |

### MON-006 Service levels declared

Published datasets SHOULD declare freshness and quality thresholds set by their owner and recorded in the contract; no value set framework-wide.

| Field | Value |
|---|---|
| level | RECOMMENDED |
| scope | data_warehouse, lakehouse, streaming |
| applies_when | the dataset has consumers |
| rationale | Monitors without agreed thresholds cannot distinguish failure from normal variation. |
| exceptions | Exception recorded with a reason and approved by the dataset owner |
| engine_notes | No source gives numeric SLO values or incident targets. dbt thresholds and the ODCS SLA section are mechanisms only, so values are adopter decisions. |
| evidence | PIPE-20, research/design_decision_matrix.md#DV-12, research/data_engineering_principles.md#7.3, research/data_engineering_principles.md#12.3 |
| evidence_strength | inference |
| status | provisional |
| decision_ref | B28 |
| check_method | catalog_query |
| check_description | Thresholds are recorded with their owner. |
| lifecycle_stage | Monitoring |

### MON-007 Anomaly detection

Datasets MAY use statistical or machine-learned anomaly detection.

| Field | Value |
|---|---|
| level | OPTIONAL |
| scope | data_warehouse, lakehouse |
| applies_when | volume or distribution varies enough that fixed thresholds fail |
| rationale | Fixed bands create noise on seasonal data, while learned methods add opacity and cost. |
| exceptions | none |
| engine_notes | Statistical bands may be enough for most tables (inference). Monte Carlo's methods were not disclosed on the page read. |
| evidence | DQ-08, DQ-13, research/data_engineering_principles.md#10.1 |
| evidence_strength | single_vendor |
| status | active |
| decision_ref | null |
| check_method | manual_review |
| check_description | The detection method is recorded. |
| lifecycle_stage | Monitoring |

## Documentation and governance (GOV)

### GOV-001 Governance framework

An organization MAY adopt DAMA-DMBOK, DCAM, DGI or COBIT APO14 as its governance structure.

| Field | Value |
|---|---|
| level | OPTIONAL |
| scope | all |
| applies_when | the organization wants a governance framework |
| rationale | Adopting a framework as if binding wastes effort, and having none leaves accountability undefined. |
| exceptions | none |
| engine_notes | DMBOK and similar frameworks are voluntary; DAMA states DMBOK is not a prescriptive standard, so it is cited as vocabulary only. DCAM is members-only. |
| evidence | GOV-01, GOV-02, GOV-17, GOV-18, research/design_decision_matrix.md#DG-1, research/data_engineering_principles.md#8.1 |
| evidence_strength | single_vendor |
| status | provisional |
| decision_ref | null |
| check_method | manual_review |
| check_description | Any adopted framework is recorded with the areas it covers. |
| lifecycle_stage | Governance |

### GOV-002 Named accountable owner

Each table or dataset SHOULD have a named accountable owner.

| Field | Value |
|---|---|
| level | RECOMMENDED |
| scope | all |
| applies_when | always |
| rationale | Issues without an owner are not resolved, and access and retention decisions have no decider. |
| exceptions | Exception recorded with a reason and approved by the dataset owner |
| engine_notes | DMBOK and similar frameworks are voluntary; DAMA states DMBOK is not a prescriptive standard, so it is cited as vocabulary only. ODCS and dbt exposures carry owner fields, but those are tool-specific. Column-level ownership is a framework decision. |
| evidence | PIPE-20, LAKE-19, GOV-18, GOV-02, research/design_decision_matrix.md#DG-2, research/data_engineering_principles.md#8.2 |
| evidence_strength | multi_vendor |
| status | provisional |
| decision_ref | B1 |
| check_method | catalog_query |
| check_description | Every dataset resolves to a named owner. |
| lifecycle_stage | Governance |

### GOV-003 Table and column descriptions

Tables and columns SHOULD have descriptions held with the schema artefact and containing no sensitive values.

| Field | Value |
|---|---|
| level | RECOMMENDED |
| scope | all |
| applies_when | always |
| rationale | Undocumented columns are misread, and descriptions copied from data can leak values. |
| exceptions | Exception recorded with a reason and approved by the dataset owner |
| engine_notes | COMMENT ON and dbt YAML are the mechanisms read. The evidence shows capability and does not state an obligation. |
| evidence | DQ-25, LAKE-19, research/design_decision_matrix.md#DG-3 |
| evidence_strength | multi_vendor |
| status | provisional |
| decision_ref | null |
| check_method | catalog_query |
| check_description | Description coverage on tables and columns meets the adopted threshold. |
| lifecycle_stage | Governance |

### GOV-004 Column classification

Columns SHOULD carry a classification attribute that drives masking and retention.

| Field | Value |
|---|---|
| level | RECOMMENDED |
| scope | all |
| applies_when | always; where GDPR applies or ASVS conformity is claimed the stronger obligation in the security standards (SC-4) governs |
| rationale | Unclassified sensitive columns escape masking and retention controls. |
| exceptions | Exception recorded with a reason and approved by the dataset owner |
| engine_notes | Classification tags differ by platform. Legal obligations are stated in the security standards and need legal review. |
| evidence | SEC-07, SEC-31, SEC-33, research/design_decision_matrix.md#DG-4, research/design_decision_matrix.md#SC-4 |
| evidence_strength | standard |
| status | provisional |
| decision_ref | null |
| check_method | catalog_query |
| check_description | Every column in scope has a classification value. |
| lifecycle_stage | Governance |

### GOV-005 Naming and registry alignment

Data element naming SHOULD align with ISO/IEC 11179 principles, with a formal registry only where mandated.

| Field | Value |
|---|---|
| level | RECOMMENDED |
| scope | all |
| applies_when | always; a formal metadata registry only where required by a mandate |
| rationale | Inconsistent element naming prevents reuse and comparison. |
| exceptions | Exception recorded with a reason and approved by the dataset owner |
| engine_notes | The ISO/IEC 11179-5 text read is a partly downloaded 2004 committee draft. |
| evidence | GOV-08, research/design_decision_matrix.md#DG-5, research/data_engineering_principles.md#12.1 |
| evidence_strength | standard |
| status | provisional |
| decision_ref | null |
| check_method | manual_review |
| check_description | Naming guidance references the adopted alignment. |
| lifecycle_stage | Governance |

### GOV-006 Breaking-change classification

Every schema change to a contracted dataset or registered stream SHOULD be classified as breaking or non-breaking before release.

| Field | Value |
|---|---|
| level | RECOMMENDED |
| scope | data_warehouse, lakehouse, streaming |
| applies_when | the dataset has a contract or a registered schema |
| rationale | An unclassified change reaches consumers without the required migration. |
| exceptions | Exception recorded with a reason and approved by the dataset owner |
| engine_notes | Confluent and dbt classify removal and narrowing as breaking and optional additions as non-breaking. Breaking stream changes go to a versioned stream (MG-14). |
| evidence | PIPE-02, DQ-03, research/design_decision_matrix.md#DG-7, research/design_decision_matrix.md#MG-14, research/data_engineering_principles.md#10.1 |
| evidence_strength | multi_vendor |
| status | active |
| decision_ref | null |
| check_method | pipeline_test |
| check_description | A contract or registry diff in CI produces the classification. |
| lifecycle_stage | Governance |

### GOV-007 Lineage capture

Pipelines SHOULD emit run-level lineage using an open event model or platform-native lineage.

| Field | Value |
|---|---|
| level | RECOMMENDED |
| scope | data_warehouse, lakehouse, streaming |
| applies_when | the pipeline produces data for consumers |
| rationale | Without lineage, the blast radius of a failure or backfill cannot be determined. |
| exceptions | Exception recorded with a reason and approved by the dataset owner |
| engine_notes | OpenLineage is an LF AI & Data project and not a de jure standard. DataHub warns manual and programmatic edits can overwrite each other. |
| evidence | GOV-31, DQ-19, DQ-20, DQ-21, DQ-22, research/design_decision_matrix.md#DG-8, research/data_engineering_principles.md#8.3 |
| evidence_strength | multi_vendor |
| status | active |
| decision_ref | null |
| check_method | catalog_query |
| check_description | Each published dataset has upstream lineage available. |
| lifecycle_stage | Governance |

### GOV-008 Lineage retention

Lineage SHOULD be exported where audit needs exceed platform retention.

| Field | Value |
|---|---|
| level | RECOMMENDED |
| scope | data_warehouse, lakehouse |
| applies_when | audit or reprocessing needs exceed the platform's lineage retention |
| rationale | Platform lineage expires between 30 days and about 13 months, and audits fall outside that window. |
| exceptions | Exception recorded with a reason and approved by the dataset owner |
| engine_notes | Dataplex retains 30 days, Snowflake one year, Unity Catalog system tables a rolling 395 days. Re-check these limits, as they are vendor settings. |
| evidence | DQ-20, DQ-21, research/design_decision_matrix.md#DG-8, research/data_engineering_principles.md#8.3 |
| evidence_strength | multi_vendor |
| status | active |
| decision_ref | null |
| check_method | catalog_query |
| check_description | Lineage retention meets the recorded audit need. |
| lifecycle_stage | Governance |

### GOV-009 Lineage-friendly design

Model changes SHOULD avoid renames and opaque functions where lineage matters, and SHOULD treat any rename as a lineage event.

| Field | Value |
|---|---|
| level | RECOMMENDED |
| scope | data_warehouse, lakehouse |
| applies_when | lineage is relied on for audit or impact analysis |
| rationale | Platform lineage has holes, so renames and opaque functions silently break the graph. |
| exceptions | Exception recorded with a reason and approved by the dataset owner |
| engine_notes | Unity Catalog loses lineage on rename and has no column lineage for UDFs. |
| evidence | DQ-20, DQ-21, research/design_decision_matrix.md#DG-9, research/data_engineering_principles.md#8.3 |
| evidence_strength | multi_vendor |
| status | active |
| decision_ref | null |
| check_method | manual_review |
| check_description | Renames in change records state how lineage is preserved. |
| lifecycle_stage | Governance |

### GOV-010 Stable dataset identity

Datasets SHOULD have a stable namespaced identity.

| Field | Value |
|---|---|
| level | RECOMMENDED |
| scope | data_warehouse, lakehouse |
| applies_when | the dataset appears in lineage or a catalog |
| rationale | Unstable identifiers split a dataset's lineage history. |
| exceptions | Exception recorded with a reason and approved by the dataset owner |
| engine_notes | OpenLineage says namespace and name should uniquely identify a dataset. |
| evidence | GOV-31, research/data_engineering_principles.md#8.3 |
| evidence_strength | single_vendor |
| status | active |
| decision_ref | null |
| check_method | catalog_query |
| check_description | Dataset identifiers are unique and unchanged across runs. |
| lifecycle_stage | Governance |

### GOV-011 Business glossary

Organizations SHOULD maintain a business glossary with named term owners.

| Field | Value |
|---|---|
| level | RECOMMENDED |
| scope | all |
| applies_when | always |
| rationale | Teams use the same term with different meanings and the metrics diverge. |
| exceptions | Exception recorded with a reason and approved by the dataset owner |
| engine_notes | Evidence shows tool capability only; the need is inference. |
| evidence | research/data_engineering_principles.md#8.4 |
| evidence_strength | inference |
| status | provisional |
| decision_ref | null |
| check_method | manual_review |
| check_description | Glossary terms have owners and link to datasets. |
| lifecycle_stage | Governance |

### GOV-012 Web dataset metadata

Dataset metadata published on the web SHOULD use the W3C DCAT 3 vocabulary.

| Field | Value |
|---|---|
| level | RECOMMENDED |
| scope | all |
| applies_when | dataset metadata is published on the web; internal catalogs may use platform vocabularies |
| rationale | Proprietary metadata cannot be harvested by other catalogs. |
| exceptions | Exception recorded with a reason and approved by the dataset owner |
| engine_notes | Platform catalogs are acceptable for internal use. |
| evidence | GOV-30, research/design_decision_matrix.md#DG-10, research/data_engineering_principles.md#8.4 |
| evidence_strength | standard |
| status | active |
| decision_ref | null |
| check_method | manual_review |
| check_description | Published catalogs expose DCAT 3 terms. |
| lifecycle_stage | Governance |

### GOV-013 Data model review

Data models MAY be reviewed with a scorecard.

| Field | Value |
|---|---|
| level | OPTIONAL |
| scope | all |
| applies_when | a formal model review is wanted |
| rationale | Informal reviews apply criteria inconsistently. |
| exceptions | none |
| engine_notes | The industry-standard claim is the publisher's own. |
| evidence | GOV-32, research/design_decision_matrix.md#DG-11 |
| evidence_strength | single_vendor |
| status | provisional |
| decision_ref | null |
| check_method | manual_review |
| check_description | If used, the scorecard is retained with the design record. |
| lifecycle_stage | Governance |

### GOV-014 ISO/IEC 27001 conformity

An organization claiming conformity to ISO/IEC 27001 MUST meet clauses 4 to 10, with Annex A controls selected by risk.

| Field | Value |
|---|---|
| level | MANDATORY |
| scope | all |
| applies_when | the organization claims ISO/IEC 27001 conformity; no obligation arises otherwise |
| rationale | A claim of conformity without the required clauses is invalid. |
| exceptions | none |
| engine_notes | Only the scope statement was read, and clause-level and Annex A content must be confirmed against a licensed copy. |
| evidence | GOV-15, research/design_decision_matrix.md#DG-12, research/data_engineering_principles.md#8.1 |
| evidence_strength | standard |
| status | provisional |
| decision_ref | null |
| check_method | manual_review |
| check_description | A statement of applicability and clause evidence exist for the claim. |
| lifecycle_stage | Governance |

### GOV-015 Records management principles

Data that constitutes records SHOULD be managed according to ISO 15489-1 principles.

| Field | Value |
|---|---|
| level | RECOMMENDED |
| scope | all |
| applies_when | the data constitutes organizational records |
| rationale | Records without management cannot serve as evidence. |
| exceptions | Exception recorded with a reason and approved by the dataset owner |
| engine_notes | The text was not fully read. The abstract does not mention retention or disposition, so no retention requirement is attributed to it. |
| evidence | GOV-16, research/design_decision_matrix.md#DG-13, research/data_engineering_principles.md#8.1 |
| evidence_strength | standard |
| status | provisional |
| decision_ref | null |
| check_method | manual_review |
| check_description | Datasets designated as records are identified. |
| lifecycle_stage | Governance |

### GOV-016 Governing-body vocabulary

Governing bodies MAY use ISO/IEC 38505-1 as a voluntary governance vocabulary.

| Field | Value |
|---|---|
| level | OPTIONAL |
| scope | all |
| applies_when | board-level data governance is being defined |
| rationale | Without a common vocabulary, board-level duties remain ambiguous. |
| exceptions | none |
| engine_notes | The 2017 edition was withdrawn on 2026-08-20 and the 2026 edition was not visible, so re-check the current text. |
| evidence | GOV-14, research/design_decision_matrix.md#DG-14, research/data_engineering_principles.md#8.1 |
| evidence_strength | standard |
| status | provisional |
| decision_ref | null |
| check_method | manual_review |
| check_description | Any use cites the current edition. |
| lifecycle_stage | Governance |

### GOV-017 Metadata architecture

Metadata collection MAY use push or event-log ingestion instead of pull crawlers.

| Field | Value |
|---|---|
| level | OPTIONAL |
| scope | all |
| applies_when | a metadata platform is being designed |
| rationale | Pull crawlers lag behind changes, while push requires integration work. |
| exceptions | none |
| engine_notes | LinkedIn and Uber moved toward event-based metadata. Case-study evidence only. CASE-38 was bot-blocked at the 2026-11-08 link check. |
| evidence | CASE-37, CASE-38, research/design_decision_matrix.md#DG-15 |
| evidence_strength | case_study |
| status | provisional |
| decision_ref | null |
| check_method | manual_review |
| check_description | The metadata ingestion model is recorded. |
| lifecycle_stage | Governance |

### GOV-018 Regulatory identifiers

Legal entities in regulated reporting SHOULD use an LEI where a regulator mandates one.

| Field | Value |
|---|---|
| level | RECOMMENDED |
| scope | all |
| applies_when | the jurisdiction's regulator mandates an LEI for that reporting; statutory scope applies only in that jurisdiction |
| rationale | Reports without a mandated identifier can be rejected. |
| exceptions | This rule requires legal review to confirm the mandate per jurisdiction; approved by legal counsel |
| engine_notes | GLEIF confirms a 20-character code based on ISO 17442. The character-position structure was not confirmed, and regulator-mandated contexts could not be verified. |
| evidence | GOV-24, research/design_decision_matrix.md#DG-16, research/data_engineering_principles.md#12.1 |
| evidence_strength | standard |
| status | provisional |
| decision_ref | null |
| check_method | manual_review |
| check_description | Regulated reports carry an LEI where the confirmed mandate applies. |
| lifecycle_stage | Governance |

## Unsupported or excluded

| Topic | Handling |
|---|---|
| Certification tiers for trusted datasets (QLT-06) | No rule. The only source is the Airbnb Midas post, which is search-snippet only and must not be cited |
| Airbnb metric platform and Wall | Not cited. RPT-012 does not rely on them |
| Sanderson manifesto | Not attributed. DQA-021 cites DQ-11 only |
| Data Fabric | No rule. No independent primary support exists |
| ISO 20022 message vocabulary (DG-17) | No rule. GOV-23 is unverified and the mandate was not verified |
| Late-arriving dimension placeholders (LAT-05) | No rule. No source prescribes one, so it is listed as an owner decision |
| Backfill standard, reconciliation table design, numeric SLOs, alert and incident targets | No source. PIP-028, DQA-015 and MON-006 state the need and set no design or value |
| Trial-balance assertion and zero-difference targets | No source. DQA-017 omits a tolerance, which is listed as an owner decision |
| CDC connectors other than PostgreSQL | Unresearched. Recorded in PIP-006 engine_notes |
| DMBOK content | Vocabulary only. Rules that lean on it are provisional |

## Decisions needing owner approval

Answered by the owner on 2026-11-08: all defaults accepted. See `../DECISIONS_TO_APPROVE.md` for the decision log, and each rule's decision_ref for its decision number. Questions and alternatives are kept for the record.

| # | Question | Proposed default | Alternatives | Consequence of each |
|---|---|---|---|---|
| 1 | What is the default consumption shape (RPT-001)? | Star schema, with wide tables as derived layers | Wide tables as the primary shape; nested structures where the engine favours them | Star: simpler conformance and more joins. Wide: simpler queries, higher update and storage cost, weak fit for several grains. Nested: engine-specific and less portable. Benchmarks conflict, so this is a judgment |
| 2 | Which dimension key type (RPT-007)? | Decide per platform; numeric surrogates in dimensional marts | Hash keys; natural keys; string keys | Numeric: favours joins and clustering, needs sequence assignment during load. Hash: parallel and idempotent loads, larger join keys. Natural: simple, weak where source keys are unstable. String: tool-friendly, slower joins per Snowflake guidance. No benchmark exists |
| 3 | Which reprocessing architecture (PIP-024)? | One implementation of the logic, replay-based or unified | Lambda with dual paths | One implementation: no logic drift, needs long retention and replay capacity. Lambda: separate batch truth, duplicated logic and possible loss of trust. The evidence is one-sided and unmeasured |
| 4 | Which quality vocabulary (DQA-012)? | DAMA UK six plus currency, mapped to ISO/IEC 25012 | ISO/IEC 25012 as primary; ISO 8000-61 process model; local vocabulary | DAMA UK: simple and used by UK Government, voluntary. ISO/IEC 25012: formal, but official text not read and needs a licence. ISO 8000-61: a process model rather than a vocabulary. Local: flexible, not comparable |
| 5 | Must financial quality failures block publication (DQA-010)? | Yes for amount and completeness checks; tiered for others | All checks block; tiered with warnings only | Blocking selected checks: protects figures with some delay. All block: strongest protection, more delays. Warnings only: no delay, risk of publishing incorrect figures |
| 6 | What is the tolerance on subledger to ledger differences (DQA-017)? | Every difference is classified and explained, with no numeric tolerance set | Zero difference required; a numeric tolerance per account | Classified: matches the Oracle evidence. Zero: stronger control and a framework decision without a source. Numeric tolerance: practical, needs owner-defined values |
| 7 | Who sets freshness and quality thresholds (MON-006), and at what values? | Each dataset owner, recorded in the contract; no framework-wide values | Framework-wide numeric defaults by tier | Owner-set: fits the evidence, values will vary. Framework-wide: consistent, but no source supports any number |
| 8 | Should single-vendor method rules stay MANDATORY (RPT-003, 004, 006, 015)? | Keep MANDATORY, scoped to teams claiming that method, per matrix RP-3, RP-4, RP-5 and RP-11 | Lower to RECOMMENDED | Keep: matches the matrix, though `RULE_FORMAT.md` lists a method owner as no listed authority type. Lower: consistent with the format wording, and weakens the method's definition |
| 9 | Should the framework raise any downgraded items to internal MANDATORY (for example DQA-004, DQA-015, GOV-002, PIP-027)? | Keep RECOMMENDED until the owner approves a raise | Raise selected items with status needs_decision | Keep: consistent with the authority rule, leaves discretion to teams. Raise: stronger control as an organizational choice, with no authoritative source |
| 10 | How should late-arriving dimensions be handled (no rule yet)? | Placeholder member, later updated when the dimension arrives | Hold the fact until the dimension arrives; assign to the default unknown member | Placeholder: keeps fact completeness, needs update logic. Hold: delays facts. Default member: simple, loses attribution. No source prescribes any of these |
