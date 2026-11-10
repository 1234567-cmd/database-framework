# Data Pipeline Architecture: Evidence Review

Status: research phase only. This document contains no schemas and no implementation. It feeds a later technology-independent Database Schema Design and Data Engineering Standards Framework for ERP, financial, SaaS and data engineering systems.

Compiled 2026-11-08 from the project research notes (topic files 04, 05, 08, 13, 15 and CORRECTIONS.md, which overrides them). No web research was done for this document and no source outside the notes is cited. The sources themselves were opened by the note authors on or about 2026-11-07.

Companion document: `data_engineering_principles.md` (lifecycle principles, migrations, validation, reconciliation, governance, backup).

## 0. Reading conventions

### 0.1 Labels

Each principle carries one label. The label is the **proposed framework position**, which may differ from how strongly a source words it. The Basis tag says which.

| Label | Meaning |
|---|---|
| **MANDATORY** | A precondition of correctness or safety in the stated scope. Violating it produces wrong data, lost data or broken consumers. |
| **RECOMMENDED** | Default practice in the stated scope. Deviation needs a stated reason. |
| **OPTIONAL/CONTEXTUAL** | A trade-off to choose per workload. |

| Basis tag | Meaning |
|---|---|
| **[S]** | The cited source states the rule or mechanism. |
| **[I]** | Inference or framework decision drawn from the cited mechanism. No fetched source prescribes it directly. |

### 0.2 Workload scope tags

These tags are never interchangeable. A principle applies only to the scopes it names.

| Tag | Meaning in this document |
|---|---|
| **OLTP** | Transactional source databases: ERP, ledgers, SaaS application stores. Enforced constraints, short transactions. |
| **OLAP** | Analytical query workloads generally, on any columnar or analytical engine. |
| **DW** | A modeled data warehouse: staging, integration, dimensional presentation, typically on a cloud warehouse. |
| **Lakehouse** | Open table formats or lakehouse platforms on object storage. |
| **Streaming** | Event logs and stream processors. |
| **All** | Every scope above. Used sparingly. |

An arrow such as OLTP to Streaming names a boundary: the principle governs the hand-off between the two.

### 0.3 Citation and quotation policy

- Citations read as Title, URL, then date or n.d., catalog ID where one exists, and flags. `vendor` marks a claim originating with a commercial vendor about its own product or market. No catalog ID means the URL is in the notes but has no exact catalog match.
- Most web pages were read through a summarizing fetch tool. **All statements drawn from web pages are paraphrases, even when specific.** Quotation marks appear only for text the notes or catalog record as locally extracted from a PDF: here, only the Dataflow Model paper (PIPE-17) and the Delta Lake paper (LAKE-08).
- Configuration names and defaults are given in code font as recorded in the notes; they are not quotations of prose.
- Vendor documentation is authoritative about what that vendor's product does. It is not neutral evidence about what architecture is best.

### 0.4 Source limits that affect this document

See section 20 for the full register. The most consequential limits: book bodies (*Fundamentals of Data Engineering*, *Streaming Systems*, *Designing Data-Intensive Applications*) were not readable and are not used for content; Delta's type-widening and column-mapping pages were not fetched; the Confluent per-format compatibility tables were only partly readable; no fetched source defines a backfill standard or a reconciliation table design.

## 1. Summary of findings

1. **Pipelines place concrete obligations on source schemas.** Across Kafka, Debezium, Spark, table formats and Airflow, the same needs recur: a stable identity key, a change signal, an event-time column distinct from processing time, additive evolution, representable deletes, a deduplication key, a partition or interval column, and retention that covers reprocessing (section 18).
2. **Exactly-once is local, never a global property.** Kafka provides it inside Kafka; Debezium drops to at-least-once under faults; Spark gives it for the file sink only. End-to-end correctness is delivered by idempotent sinks (section 15).
3. **ELT is the vendor-recommended default for cloud warehouses, and is not a governance-free choice.** Vendor sources that recommend it concede raw-data risks, and regulated contexts may need hybrid or ETL (section 3).
4. **The strongest published position is that batch versus streaming is an engine choice under one model**, decided by correctness, latency and cost (section 6). Lambda is criticized by every fetched source that discusses it; no fetched source defends it, so this is one-sided evidence (section 5).
5. **Schema compatibility is defined per direction and carries a deployment order.** The registry default is non-transitive, which is weaker than long-retention topics need (section 8).
6. **Table formats agree on very little beyond adding nullable columns.** Rename, drop and reorder differ sharply. The portable-safe set in the notes is smaller than the notes first state once unfetched Delta pages are taken into account (section 13).
7. **Orchestrator rules are schema rules.** Re-runnable tasks need merge keys and interval-scoped partitions (section 14).

## 2. Workload map: what applies where

| Concern | OLTP | OLAP / DW | Lakehouse | Streaming |
|---|---|---|---|---|
| Role in a pipeline | Source of record; emits changes | Target for modeled analytics | Raw-to-curated storage on object stores | Transport and continuous processing |
| Key enforcement | Enforced by engine | PK, UNIQUE, FK generally not enforced on standard Snowflake tables or Databricks ([Snowflake Constraints overview](https://docs.snowflake.com/en/sql-reference/constraints-overview) (n.d.; LAKE-09; vendor), [Constraints on Databricks](https://docs.databricks.com/aws/en/tables/constraints) (2026-10-29; LAKE-02; vendor)) | As Databricks; Delta clients enforce schema and NOT NULL or CHECK | Key is a routing and compaction concept, not a constraint ([Apache Kafka 4.3 Design](https://kafka.apache.org/43/design/design/) (n.d.; PIPE-01)) |
| Primary integrity tool | DDL constraints | Tests and pipeline logic ([dbt: Add data tests to your DAG](https://docs.getdbt.com/docs/build/data-tests) (2026-09-16; LAKE-19; vendor)) | Schema enforcement, constraints, tests | Registry compatibility, idempotent consumers ([Schema Evolution and Compatibility for Schema Registry on Confluent Platform](https://docs.confluent.io/platform/current/schema-registry/fundamentals/schema-evolution.html) (2026-10-13; PIPE-02; vendor)) |
| Schema-change mechanism | Migrations, expand and contract (see companion document) | Versioned models, additive contracts ([dbt: Model contracts](https://docs.getdbt.com/docs/mesh/govern/model-contracts) (2026-10-29; LAKE-17; also DQ-03; vendor)) | Format-specific evolution (section 13) | Compatibility modes, versioned streams ([Schema Evolution pattern](https://developer.confluent.io/patterns/event-stream/schema-evolution/) (n.d.; vendor)) |
| Transaction scope | Multi-table | Platform-specific | Single-table in the Delta paper; multi-statement was a private preview in December 2025, current status unverified ([Delta Lake: High-Performance ACID Table Storage over Cloud Object Stores](https://www.vldb.org/pvldb/vol13/p3411-armbrust.pdf) (2020; LAKE-08), [Databricks Lakehouse Data Modeling: Myths, Truths, and Best Practices](https://www.databricks.com/blog/databricks-lakehouse-data-modeling-myths-truths-and-best-practices) (2025-12-15; LAKE-06; vendor)) | Kafka transactions across partitions inside Kafka ([Apache Kafka 4.3 Design](https://kafka.apache.org/43/design/design/) (n.d.; PIPE-01)) |
| Suitability as OLTP store | Yes | No, except specialized table types such as Snowflake hybrid tables ([Snowflake Constraints overview](https://docs.snowflake.com/en/sql-reference/constraints-overview) (n.d.; LAKE-09; vendor)) | No. The Delta paper reports write rate limited to several transactions per second ([Delta Lake: High-Performance ACID Table Storage over Cloud Object Stores](https://www.vldb.org/pvldb/vol13/p3411-armbrust.pdf) (2020; LAKE-08)) | Not applicable |

## 3. ETL versus ELT

Scope of this entire section: OLAP, DW and Lakehouse targets. ETL and ELT are not OLTP design patterns, though they impose requirements on OLTP sources (section 18).

### 3.1 Evidence

- Google recommends ELT for most BigQuery customers, on the grounds that it splits integration into two stages, removes other processing tools, and scales transformation in the warehouse. ETL is described as useful for an existing transformation process or to reduce BigQuery resource use: [BigQuery: Introduction to loading, transforming, and exporting data](https://docs.cloud.google.com/bigquery/docs/load-transform-export-intro) (n.d.; PIPE-19; vendor).
- dbt Labs lists benefits of ELT (raw data remains available, warehouse compute is used, analytics code gets software practices) and drawbacks (storage cost, complexity at scale, performance bottlenecks, and security and compliance risk from raw data). It describes ETL as suited to industries needing strict governance such as finance and healthcare, and suggests hybrids: [dbt Labs: Understanding ELT](https://www.getdbt.com/blog/extract-load-transform) (2023-09-06; PIPE-18; vendor). A second dbt post says ETL for compliance-sensitive masking before load is valid within a hybrid: [ETL vs ELT: What's the difference?](https://getdbt.com/blog/etl-vs-elt) (2023-03-15; vendor).
- The Lakehouse paper criticizes the two-tier pattern where data is ETLed into lakes and then ELTed into warehouses, for its complexity, delays and failure modes: [Lakehouse: A New Generation of Open Platforms that Unify Data Warehousing and Advanced Analytics](https://www.cidrdb.org/cidr2021/papers/cidr2021_paper17.pdf) (2021; LAKE-07).

### 3.2 Principles

- **ELT-01. RECOMMENDED. Scope: DW, Lakehouse.** Default to ELT when the target has elastic compute and raw retention can be governed. Basis [S], vendor-originated: [BigQuery: Introduction to loading, transforming, and exporting data](https://docs.cloud.google.com/bigquery/docs/load-transform-export-intro) (n.d.; PIPE-19; vendor), [dbt Labs: Understanding ELT](https://www.getdbt.com/blog/extract-load-transform) (2023-09-06; PIPE-18; vendor). Both sources sell or operate the in-warehouse transformation model, so treat this as an interested recommendation.
- **ELT-02. OPTIONAL/CONTEXTUAL. Scope: DW, Lakehouse in regulated domains.** Use ETL or a hybrid when data must be cleaned, validated or masked before it reaches the analytical store. Basis [S]: [dbt Labs: Understanding ELT](https://www.getdbt.com/blog/extract-load-transform) (2023-09-06; PIPE-18; vendor), [ETL vs ELT: What's the difference?](https://getdbt.com/blog/etl-vs-elt) (2023-03-15; vendor).
- **ELT-03. MANDATORY. Scope: DW, Lakehouse holding personal or financial data.** A raw landing zone is a governed store: it needs access control, classification and retention like any other. Basis [S] on the risk and the need for strict governance policies, vendor-originated: [dbt Labs: Understanding ELT](https://www.getdbt.com/blog/extract-load-transform) (2023-09-06; PIPE-18; vendor). See also Databricks, which says bronze data is not intended for analyst access: [Medallion lakehouse architecture](https://docs.databricks.com/aws/en/lakehouse/medallion) (2026-10-29; LAKE-01; vendor).
- **ELT-04. RECOMMENDED. Scope: DW, Lakehouse.** Pair ELT with producer-consumer data contracts. Basis [I]: the pro-ELT sources read do not address contracts; that gap is filled by [Data Contract pattern](https://developer.confluent.io/patterns/event/data-contract/) (n.d.; PIPE-03; vendor) and [Open Data Contract Standard (latest)](https://bitol-io.github.io/open-data-contract-standard/latest/) (n.d.; PIPE-20). This is an argument across sources, not one any single source makes.
- **ELT-05. OPTIONAL/CONTEXTUAL. Scope: Lakehouse, DW.** Layered quality topologies such as medallion organize data by quality level. Databricks itself calls medallion a recommended best practice but not a requirement, and later a guideline: [Medallion lakehouse architecture](https://docs.databricks.com/aws/en/lakehouse/medallion) (2026-10-29; LAKE-01; vendor), [Databricks Lakehouse Data Modeling: Myths, Truths, and Best Practices](https://www.databricks.com/blog/databricks-lakehouse-data-modeling-myths-truths-and-best-practices) (2025-12-15; LAKE-06; vendor). Basis [S]. Medallion is a topology and not a data model; models are placed within it (3NF or Data Vault in silver, star schemas in gold) per Databricks blog guidance: [Data Warehousing Modeling Techniques and Their Implementation on the Databricks Lakehouse Platform](https://www.databricks.com/blog/2022/06/24/data-warehousing-modeling-techniques-and-their-implementation-on-the-databricks-lakehouse-platform.html) (2022-06-24; LAKE-05; vendor).
- **ELT-06. RECOMMENDED. Scope: DW.** Keep a source-conformed layer distinct from a business-conformed layer, applying each transformation once. dbt recommends staging models one-to-one with source tables, doing only renames, casts and basic computation, without joins or aggregations: [How we structure our dbt projects](https://docs.getdbt.com/best-practices/how-we-structure/1-guide-overview) (2026-08-19; LAKE-15; vendor), [Staging: Preparing our atomic building blocks](https://docs.getdbt.com/best-practices/how-we-structure/2-staging) (2026-07-07; vendor). Basis [S], vendor-originated.

### 3.3 Schema-on-read versus schema-on-write

**Conflict.** ELT guidance favors landing raw data, and Databricks recommends storing most bronze fields as string, VARIANT or binary to guard against source changes ([Medallion lakehouse architecture](https://docs.databricks.com/aws/en/lakehouse/medallion) (2026-10-29; LAKE-01; vendor)); Snowflake suggests VARIANT when query patterns are unknown ([Considerations for semi-structured data stored in VARIANT](https://docs.snowflake.com/en/user-guide/semistructured-considerations) (n.d.; vendor)). Table formats and streaming engines default to strict schema-on-write: Delta rejects unknown columns and type mismatches on write ([Delta Lake: Table batch reads and writes](https://docs.delta.io/latest/delta-batch.html) (n.d.; PIPE-11)), and Spark requires a declared schema for streaming file sources ([Structured Streaming Programming Guide: APIs on DataFrames and Datasets](https://spark.apache.org/docs/latest/streaming/apis-on-dataframes-and-datasets.html) (n.d.; PIPE-08)).

**Resolution by layer (framework position, [I]).** The conflict is about where typing happens, and it dissolves per layer:

| Layer | Stance | Scope |
|---|---|---|
| Raw landing | Permissive payload is acceptable, but the envelope (key, event time, ingest time, source, schema version) is declared | Lakehouse, DW |
| Validated or staging | Schema-on-write, declared types | Lakehouse, DW |
| Presentation | Strict schema-on-write, contracted | DW, Lakehouse |
| Event topics | Registered schema with compatibility mode | Streaming |

- **ELT-07. MANDATORY. Scope: Lakehouse, DW, for financial amounts.** Declare monetary values as exact decimals at the first typed layer; never rely on inference. Spark's JSON inference yields floating-point unless `prefersDecimal` is set: [Spark SQL JSON Files](https://spark.apache.org/docs/latest/sql-data-sources-json.html) (n.d., Spark 4.3.0; PIPE-07). Basis [I] from that default. A related conflict with a dbt style-guide example is recorded in the companion document.

## 4. Batch versus streaming

### 4.1 Evidence

- Akidau defines streaming as an engine designed with infinite data sets in mind, separates that from unbounded data, argues well-designed streaming systems are a superset of batch, and distinguishes event time from processing time: [The world beyond batch: Streaming 101](https://www.oreilly.com/radar/the-world-beyond-batch-streaming-101/) (2015-08-05; PIPE-16).
- Databricks summarizes the trade-off as continuous incremental (higher cost, lower latency), triggered incremental (lower cost, higher latency) and batch (lowest cost, highest latency): [Medallion lakehouse architecture](https://docs.databricks.com/aws/en/lakehouse/medallion) (2026-10-29; LAKE-01; vendor).
- Snowflake says dynamic tables do not suit data fresher than 60 seconds, their minimum target lag: [Snowflake Dynamic tables](https://docs.snowflake.com/en/user-guide/dynamic-tables-about) (n.d.; vendor).

### 4.2 Principles

- **BAT-01. RECOMMENDED. Scope: OLAP, DW, Lakehouse, Streaming.** Choose batch, micro-batch or streaming per dataset by correctness, latency and cost, and record the decision. Basis [S]: the Dataflow Model paper says its model allows the choice of engine to become one of simply correctness, latency and cost: [The Dataflow Model](https://www.vldb.org/pvldb/vol8/p1792-Akidau.pdf) (2015; PIPE-17).
- **BAT-02. MANDATORY. Scope: Streaming, Lakehouse.** Any dataset that may be processed by event time carries event time as an explicit field. Basis [S] on the distinction ([The world beyond batch: Streaming 101](https://www.oreilly.com/radar/the-world-beyond-batch-streaming-101/) (2015-08-05; PIPE-16), [The Dataflow Model](https://www.vldb.org/pvldb/vol8/p1792-Akidau.pdf) (2015; PIPE-17)) and [I] on the field requirement.
- **BAT-03. RECOMMENDED. Scope: DW.** Escalate materialization only on need. dbt advises starting with a view, moving to a table when queries are too slow, and to incremental when builds are too slow, and warns against defaulting to incremental: [Marts: Business-defined entities](https://docs.getdbt.com/best-practices/how-we-structure/4-marts) (2026-07-07; vendor). Basis [S], vendor-originated.
- **BAT-04. RECOMMENDED. Scope: DW, Lakehouse on Snowflake-like platforms.** Prefer declarative incremental pipelines for current-state data, but do not use them for history. Snowflake recommends dynamic tables for new multi-table SQL pipelines and says they represent current state and not a historical record, so they do not provide SCD Type 2: [Decision guide for dynamic tables](https://docs.snowflake.com/en/user-guide/dynamic-tables-comparison) (n.d.; LAKE-12; vendor). Basis [S], vendor-originated.

## 5. Lambda versus kappa

Scope of this section: Streaming and its OLAP serving layers. Neither is an OLTP pattern.

### 5.1 Evidence

- Kreps describes Lambda as feeding a batch and a stream system in parallel and implementing logic twice, doubts this is fixable, and proposes keeping the input log, running a second job from the start of the log when code changes, writing to a new table, switching readers, and dropping the old job and table: [Questioning the Lambda Architecture](https://www.oreilly.com/radar/questioning-the-lambda-architecture/) (2014-07-02; PIPE-15).
- Akidau also criticizes maintaining parallel pipelines and predicts Lambda's decline: [The world beyond batch: Streaming 101](https://www.oreilly.com/radar/the-world-beyond-batch-streaming-101/) (2015-08-05; PIPE-16).
- The Dataflow paper reports a MillWheel customer who ran a weakly consistent stream with a nightly MapReduce for truth: "They found that customers stopped trusting the weakly consistent results over time": [The Dataflow Model](https://www.vldb.org/pvldb/vol8/p1792-Akidau.pdf) (2015; PIPE-17).

### 5.2 Principles

- **LAM-01. RECOMMENDED. Scope: Streaming, OLAP serving.** Avoid maintaining two independent implementations of the same logic. Basis [S]: [Questioning the Lambda Architecture](https://www.oreilly.com/radar/questioning-the-lambda-architecture/) (2014-07-02; PIPE-15), [The world beyond batch: Streaming 101](https://www.oreilly.com/radar/the-world-beyond-batch-streaming-101/) (2015-08-05; PIPE-16).
- **LAM-02. MANDATORY. Scope: OLAP serving, where any dual-path design exists.** If a dual path is unavoidable, publish one authoritative metric definition and label provisional results. Basis [I], from the trust finding in [The Dataflow Model](https://www.vldb.org/pvldb/vol8/p1792-Akidau.pdf) (2015; PIPE-17).
- **KAP-01. MANDATORY. Scope: Streaming, where replay is the reprocessing strategy.** Retention must cover the reprocessing window. Basis [S]: [Questioning the Lambda Architecture](https://www.oreilly.com/radar/questioning-the-lambda-architecture/) (2014-07-02; PIPE-15). Kafka's default `retention.ms` is 7 days ([Kafka 4.2 Topic Configs](https://kafka.apache.org/42/configuration/topic-configs/) (n.d.)), so replay beyond a week requires explicit configuration, a compacted topic or a separate archive.
- **KAP-02. OPTIONAL/CONTEXTUAL. Scope: OLAP, Streaming.** Design output tables to be versioned and swappable, so a reprocessing job can build alongside the live table. Basis [S] for the pattern ([Questioning the Lambda Architecture](https://www.oreilly.com/radar/questioning-the-lambda-architecture/) (2014-07-02; PIPE-15)), [I] for the naming and view-swap implication.
- **KAP-03. MANDATORY. Scope: Streaming, where replay is the reprocessing strategy.** Schema compatibility must span the retained log, since a replaying consumer reads old records. Basis [I], combining [Schema Evolution and Compatibility for Schema Registry on Confluent Platform](https://docs.confluent.io/platform/current/schema-registry/fundamentals/schema-evolution.html) (2026-10-13; PIPE-02; vendor) and [Questioning the Lambda Architecture](https://www.oreilly.com/radar/questioning-the-lambda-architecture/) (2014-07-02; PIPE-15).

### 5.3 Evidence caveat

**Every fetched source on this topic is critical of Lambda, and both named critics advocate stream processing.** The notes contain no defense of Lambda and no measured comparison. Kafka's retention, storage cost at scale, and replay duration for large histories are not quantified in any source read. Treat kappa as a well-argued pattern and not as a proven replacement.

## 6. The Dataflow model

Scope of this section: Streaming and any unbounded-data processing that feeds OLAP.

### 6.1 Core ideas

- The paper decomposes pipelines along four questions: what is computed, where in event time, when in processing time results are materialized, and how earlier results relate to later refinements: [The Dataflow Model](https://www.vldb.org/pvldb/vol8/p1792-Akidau.pdf) (2015; PIPE-17).
- A central design principle reads: "Never rely on any notion of completeness." Its abstract urges the field to work under the assumption "that we will never know if or when we have seen all of our data": [The Dataflow Model](https://www.vldb.org/pvldb/vol8/p1792-Akidau.pdf) (2015; PIPE-17).
- A watermark is defined as "a lower bound (often heuristically established) on event times that have been processed": [The Dataflow Model](https://www.vldb.org/pvldb/vol8/p1792-Akidau.pdf) (2015; PIPE-17). It is an estimate, so it cannot by itself prove completeness.
- Refinement modes are discarding, accumulating, and accumulating and retracting: [The Dataflow Model](https://www.vldb.org/pvldb/vol8/p1792-Akidau.pdf) (2015; PIPE-17).

### 6.2 Mapping refinement modes to sink shapes (inference)

No source prescribes these mappings. They are [I], derived from the paper's mode descriptions.

| Refinement mode | Sink requirement | Scope |
|---|---|---|
| Discarding | Append-only rows; each firing is separate | Streaming to OLAP |
| Accumulating | Upsert by key and window; consumer overwrites prior value | Streaming to OLAP |
| Accumulating and retracting | Sink accepts retraction rows or versioned rows | Streaming to OLAP |

### 6.3 Principles

- **DFM-01. MANDATORY. Scope: Streaming.** Do not design a stream consumer that assumes a dataset is ever complete. Basis [S]: [The Dataflow Model](https://www.vldb.org/pvldb/vol8/p1792-Akidau.pdf) (2015; PIPE-17).
- **DFM-02. RECOMMENDED. Scope: Streaming to OLAP.** State for each streaming aggregate which refinement mode it uses, because this fixes the sink's key and write semantics. Basis [I]: [The Dataflow Model](https://www.vldb.org/pvldb/vol8/p1792-Akidau.pdf) (2015; PIPE-17).
- **DFM-03. MANDATORY. Scope: Streaming.** Prefer event-time windows when results must reflect when events happened. Processing-time windows are wrong under out-of-order arrival. Basis [S]: [The world beyond batch: Streaming 101](https://www.oreilly.com/radar/the-world-beyond-batch-streaming-101/) (2015-08-05; PIPE-16).

## 7. Apache Kafka

Scope of this section: Streaming unless noted. Defaults are recorded from the 4.3 design page and 4.2 configuration reference, which are different documentation versions.

### 7.1 Ordering and keys

- **KAF-01. MANDATORY. Scope: Streaming.** Records that must stay ordered must share a partition, and therefore a key. Kafka guarantees ordering only within a partition, and each partition is consumed by one member of a consumer group at a time: [Apache Kafka 4.3 Design](https://kafka.apache.org/43/design/design/) (n.d.; PIPE-01). Basis [S].
- **KAF-02. MANDATORY. Scope: Streaming.** Choose the record key as the stable business entity identity, and serialize composite keys deterministically. Keys are hashed to select a partition: [Apache Kafka 4.3 Design](https://kafka.apache.org/43/design/design/) (n.d.; PIPE-01). Basis [S] for hashing, [I] for deterministic serialization.
- **KAF-03. MANDATORY. Scope: Streaming.** Treat a change of partition count or key definition as a breaking change for ordering guarantees. Basis [I] from the hash-to-partition mechanism in [Apache Kafka 4.3 Design](https://kafka.apache.org/43/design/design/) (n.d.; PIPE-01). No fetched page discusses this directly.
- **KAF-04. RECOMMENDED. Scope: Streaming.** Set the key at production time instead of repairing it in Connect. The existence of the `ValueToKey` transform shows key repair is possible, not that it is safe, because ordering is decided before the sink edge: [Single Message Transforms for Confluent Platform](https://docs.confluent.io/kafka-connectors/transforms/current/overview.html) (2026-10-22; PIPE-04; vendor). Basis [I].

### 7.2 Delivery semantics

| Guarantee | What it covers | Source |
|---|---|---|
| At most once | Messages may be lost, never redelivered | [Apache Kafka 4.3 Design](https://kafka.apache.org/43/design/design/) (n.d.; PIPE-01) |
| At least once | Messages never lost, may be redelivered | [Apache Kafka 4.3 Design](https://kafka.apache.org/43/design/design/) (n.d.; PIPE-01) |
| Idempotent producer | Broker deduplicates resends by producer ID and sequence number | [Apache Kafka 4.3 Design](https://kafka.apache.org/43/design/design/) (n.d.; PIPE-01) |
| Transactions with `read_committed` | Atomic writes across partitions; consumers see only committed records | [Apache Kafka 4.3 Design](https://kafka.apache.org/43/design/design/) (n.d.; PIPE-01) |
| Kafka Streams exactly-once | Read-process-write inside Kafka | [Apache Kafka 4.3 Design](https://kafka.apache.org/43/design/design/) (n.d.; PIPE-01) |
| End-to-end to external sinks | Not provided; docs describe storing the consumer offset with the output | [Apache Kafka 4.3 Design](https://kafka.apache.org/43/design/design/) (n.d.; PIPE-01) |

- **KAF-05. RECOMMENDED. Scope: Streaming.** Enable the idempotent producer. It does not address duplicates across producer sessions or systems. Basis [S] for the mechanism ([Apache Kafka 4.3 Design](https://kafka.apache.org/43/design/design/) (n.d.; PIPE-01)). The session limit comes from a Kafka 1.1 Javadoc page that was returned by search and never opened, so treat it as unverified.
- **KAF-06. OPTIONAL/CONTEXTUAL. Scope: Streaming.** Use transactions and `read_committed` only for read-process-write loops that stay inside Kafka. Basis [S]: [Apache Kafka 4.3 Design](https://kafka.apache.org/43/design/design/) (n.d.; PIPE-01).
- **KAF-07. MANDATORY. Scope: Streaming to OLTP, OLAP or Lakehouse sinks.** For correctness at an external sink, the sink must store its position with the output or apply idempotent writes. Basis [S]: [Apache Kafka 4.3 Design](https://kafka.apache.org/43/design/design/) (n.d.; PIPE-01).
- **KAF-08. RECOMMENDED. Scope: Streaming.** Use `acks=all` with `min.insync.replicas` above 1 for durable topics. The default `min.insync.replicas` is 1 ([Kafka 4.2 Topic Configs](https://kafka.apache.org/42/configuration/topic-configs/) (n.d.)); the mechanism is in [Apache Kafka 4.3 Design](https://kafka.apache.org/43/design/design/) (n.d.; PIPE-01). Basis [S] for the mechanism, [I] for the numeric choice.

### 7.3 Log compaction and deletes

Log compaction retains at least the last value per key. A record with a key and null payload is a delete marker, kept for `delete.retention.ms`, default one day. Compaction preserves order, never changes offsets, and a consumer reading from the start sees the final state if it reaches the head within that retention: [Apache Kafka 4.3 Design](https://kafka.apache.org/43/design/design/) (n.d.; PIPE-01), [Kafka 4.2 Topic Configs](https://kafka.apache.org/42/configuration/topic-configs/) (n.d.).

- **KAF-09. MANDATORY. Scope: Streaming, compacted topics.** A compacted topic is a table keyed by the record key. It requires a stable key and null-value tombstones to express deletion. Basis [S]: [Apache Kafka 4.3 Design](https://kafka.apache.org/43/design/design/) (n.d.; PIPE-01).
- **KAF-10. MANDATORY. Scope: Streaming, compacted topics.** Consumers must rebuild state within `delete.retention.ms` or risk missing tombstones and resurrecting deleted keys. Basis [S] for the guarantee's condition, [I] for the operational consequence: [Apache Kafka 4.3 Design](https://kafka.apache.org/43/design/design/) (n.d.; PIPE-01), [Kafka 4.2 Topic Configs](https://kafka.apache.org/42/configuration/topic-configs/) (n.d.).
- **KAF-11. RECOMMENDED. Scope: Streaming.** Do not rely on compaction to meet an erasure deadline. Timing depends on `min.compaction.lag.ms`, `max.compaction.lag.ms` and `min.cleanable.dirty.ratio`, whose defaults are 0, the maximum long value and 0.5: [Kafka 4.2 Topic Configs](https://kafka.apache.org/42/configuration/topic-configs/) (n.d.). Basis [I]: a defaulted maximum lag gives no deadline, so privacy deletion needs a separately designed process.

### 7.4 Retention and time

- **KAF-12. OPTIONAL/CONTEXTUAL. Scope: Streaming.** Retention is a reprocessing-window decision. Defaults: `cleanup.policy=delete`, `retention.ms` 7 days, `retention.bytes` unlimited: [Kafka 4.2 Topic Configs](https://kafka.apache.org/42/configuration/topic-configs/) (n.d.). Basis [S].
- **KAF-13. MANDATORY. Scope: Streaming.** Carry business event time in the payload. `message.timestamp.type` defaults to `CreateTime` and can be `LogAppendTime` per topic, so the record timestamp's meaning is a topic setting: [Kafka 4.2 Topic Configs](https://kafka.apache.org/42/configuration/topic-configs/) (n.d.). Basis [I].

## 8. Schema registries and compatibility

Scope of this section: Streaming. The source is Confluent's own documentation (vendor), authoritative for its product. The compatibility vocabulary is widely reused, but the notes contain no neutral standard defining it.

### 8.1 Compatibility modes

Paraphrased from [Schema Evolution and Compatibility for Schema Registry on Confluent Platform](https://docs.confluent.io/platform/current/schema-registry/fundamentals/schema-evolution.html) (2026-10-13; PIPE-02; vendor).

| Mode | Guarantee | Checked against | Upgrade order |
|---|---|---|---|
| BACKWARD (default) | New-schema consumer reads data from the current and previous schema | Latest only | Consumers first |
| BACKWARD_TRANSITIVE | New-schema consumer reads data from all previous schemas | All previous | Consumers first |
| FORWARD | Data from the new schema is readable by consumers on the current and previous schema | Latest only | Producers first; ensure older data is gone before upgrading consumers |
| FORWARD_TRANSITIVE | Extends forward compatibility to all earlier schemas | All previous | Producers first |
| FULL | Backward and forward between adjacent versions | Latest only | Independent |
| FULL_TRANSITIVE | Backward and forward across all registered schemas | All previous | Independent |
| NONE | Checks disabled | None | Manual coordination |

### 8.2 Per-format rules

| Format | Rule | Label |
|---|---|---|
| Avro | Adding a field needs a default to stay backward compatible. A default must conform to the first union branch, so optional fields are a union with null first and a null default. | MANDATORY under BACKWARD |
| Protobuf | Confluent names BACKWARD_TRANSITIVE as best practice. Adding new message types is not forward compatible. | RECOMMENDED |
| JSON Schema | Result depends on `compatibilityPolicy` and whether the content model is open or closed. | OPTIONAL/CONTEXTUAL |

All rows: [Schema Evolution and Compatibility for Schema Registry on Confluent Platform](https://docs.confluent.io/platform/current/schema-registry/fundamentals/schema-evolution.html) (2026-10-13; PIPE-02; vendor). The page's detailed cell-by-cell tables for required-field changes could not be read in the notes, so no required-field compatibility claim beyond one-direction-only is made here.

### 8.3 Principles

- **REG-01. MANDATORY. Scope: Streaming.** Every topic that crosses a team boundary has a registered schema and a compatibility mode other than NONE. Basis [I] from the registry's enforcement role in [Schema Evolution and Compatibility for Schema Registry on Confluent Platform](https://docs.confluent.io/platform/current/schema-registry/fundamentals/schema-evolution.html) (2026-10-13; PIPE-02; vendor).
- **REG-02. MANDATORY. Scope: Streaming.** Deployment order follows the compatibility mode and is part of the change plan. Basis [S]: [Schema Evolution and Compatibility for Schema Registry on Confluent Platform](https://docs.confluent.io/platform/current/schema-registry/fundamentals/schema-evolution.html) (2026-10-13; PIPE-02; vendor).
- **REG-03. RECOMMENDED. Scope: Streaming, compacted or long-retention topics.** Use a transitive mode where consumers may read old records. Non-transitive checks permit a chain in which the newest schema cannot read data two versions back. Basis [S] for the mechanism ([Schema Evolution and Compatibility for Schema Registry on Confluent Platform](https://docs.confluent.io/platform/current/schema-registry/fundamentals/schema-evolution.html) (2026-10-13; PIPE-02; vendor)), [I] for the recommendation. Confluent's preference for BACKWARD for Kafka so consumers can rewind supports the direction: [Schema Evolution and Compatibility for Schema Registry on Confluent Platform](https://docs.confluent.io/platform/current/schema-registry/fundamentals/schema-evolution.html) (2026-10-13; PIPE-02; vendor).
- **REG-04. MANDATORY. Scope: Streaming.** Declare fields optional or defaulted at creation if they may ever be removed. Which changes are legal depends on how a field was originally declared: [Schema Evolution and Compatibility for Schema Registry on Confluent Platform](https://docs.confluent.io/platform/current/schema-registry/fundamentals/schema-evolution.html) (2026-10-13; PIPE-02; vendor). Basis [S].
- **REG-05. MANDATORY. Scope: Streaming.** Compatible changes evolve in place. Breaking changes go to a new versioned stream with explicit consumer migration and retirement of the old stream: [Schema Evolution pattern](https://developer.confluent.io/patterns/event-stream/schema-evolution/) (n.d.; vendor). Basis [S], vendor pattern.
- **REG-06. MANDATORY. Scope: Streaming with Kafka Streams consumers.** Use only BACKWARD, BACKWARD_TRANSITIVE, FULL or FULL_TRANSITIVE, and upgrade Streams applications before upstream producers: [Schema Evolution and Compatibility for Schema Registry on Confluent Platform](https://docs.confluent.io/platform/current/schema-registry/fundamentals/schema-evolution.html) (2026-10-13; PIPE-02; vendor). Basis [S].
- **REG-07. RECOMMENDED. Scope: Streaming to DW or Lakehouse.** Treat a table loader as a consumer. Under BACKWARD, redeploy it before producers change, and keep the landing table a superset with nullable additions. Basis [I]: [Schema Evolution and Compatibility for Schema Registry on Confluent Platform](https://docs.confluent.io/platform/current/schema-registry/fundamentals/schema-evolution.html) (2026-10-13; PIPE-02; vendor), [Delta Lake: Table batch reads and writes](https://docs.delta.io/latest/delta-batch.html) (n.d.; PIPE-11).

### 8.4 Contract scope conflict

**Conflict.** Confluent's pattern treats a contract as a shared schema held in a registry ([Data Contract pattern](https://developer.confluent.io/patterns/event/data-contract/) (n.d.; PIPE-03; vendor)). ODCS includes quality, SLA, team, roles, support and pricing ([Open Data Contract Standard (latest)](https://bitol-io.github.io/open-data-contract-standard/latest/) (n.d.; PIPE-20)). A later Confluent blog expands to SLAs and ownership and says registry rules can enforce quality in streams ([Shifting Left: How Data Contracts Underpin People, Processes, and Technology](https://www.confluent.io/blog/shifting-left/) (2025-04-02; DQ-11; vendor)). Framework position: a registry provides the technical compatibility enforcement point; a contract is the larger agreement. The companion document covers contracts.

## 9. Kafka Connect transforms

Scope: Streaming boundary with OLTP, OLAP or Lakehouse.

Single message transforms change individual records in flight, inside Connect, without a separate stream processor. Most behave differently for schema-aware and schemaless records. Several reshape structure, type or key, including `Cast`, `Flatten`, `ValueToKey`, `SetSchemaMetadata`, `MaskField` and the Debezium `EventRouter`: [Single Message Transforms for Confluent Platform](https://docs.confluent.io/kafka-connectors/transforms/current/overview.html) (2026-10-22; PIPE-04; vendor).

- **SMT-01. OPTIONAL/CONTEXTUAL. Scope: Streaming boundary.** Use transforms for narrow per-record adjustments. Confluent's page does not give guidance on when to prefer them over stream processing: [Single Message Transforms for Confluent Platform](https://docs.confluent.io/kafka-connectors/transforms/current/overview.html) (2026-10-22; PIPE-04; vendor).
- **SMT-02. RECOMMENDED. Scope: Streaming to OLAP.** Document canonical flattening and type coercion, since they become an implicit contract once applied at the sink. Basis [I]: [Single Message Transforms for Confluent Platform](https://docs.confluent.io/kafka-connectors/transforms/current/overview.html) (2026-10-22; PIPE-04; vendor).
- **SMT-03. MANDATORY. Scope: Streaming, Connect sinks.** Do not set `errors.tolerance=all` without routing failures and reconciling counts. With that setting, errors are skipped and not written to the worker log, so Confluent says to use metrics or compare source and processed counts. DLQs apply only to sink connectors, and context headers default to off: [Kafka Connect Concepts](https://docs.confluent.io/platform/current/connect/concepts.html) (2026-10-16; vendor). Basis [S], vendor.

## 10. Change data capture

Scope: OLTP to Streaming unless noted. Details are from Debezium documentation and largely specific to its PostgreSQL connector.

### 10.1 Why log-based CDC

Debezium states that log-based CDC, unlike polling or dual writes, captures all data changes with low delay and without the CPU cost of frequent polling, requires no model change such as a last-updated column, captures deletes, and can capture old row state and transaction metadata: [Debezium Features](https://debezium.io/documentation/reference/stable/features.html) (n.d.; TEN-26). Debezium is a CDC project describing its own approach, so this comparison is not neutral.

### 10.2 Semantics that matter to schema design

| Topic | Documented behavior | Source |
|---|---|---|
| Mechanism | PostgreSQL logical decoding, standard plug-in `pgoutput`; resumes from where it left off in the WAL after a restart | [Debezium connector for PostgreSQL](https://debezium.io/documentation/reference/stable/connectors/postgresql.html) (n.d., Debezium 3.7; PIPE-06) |
| Initial load | Consistent snapshot; snapshot rows use `op = r` | [Debezium connector for PostgreSQL](https://debezium.io/documentation/reference/stable/connectors/postgresql.html) (n.d., Debezium 3.7; PIPE-06) |
| Envelope | `before`, `after`, mandatory `source` and `op`; op values c, u, d, r, t, m | [Debezium connector for PostgreSQL](https://debezium.io/documentation/reference/stable/connectors/postgresql.html) (n.d., Debezium 3.7; PIPE-06) |
| No primary key, REPLICA IDENTITY DEFAULT | Connector emits only create events | [Debezium connector for PostgreSQL](https://debezium.io/documentation/reference/stable/connectors/postgresql.html) (n.d., Debezium 3.7; PIPE-06) |
| REPLICA IDENTITY FULL | Update and delete events contain previous values of all columns | [Debezium connector for PostgreSQL](https://debezium.io/documentation/reference/stable/connectors/postgresql.html) (n.d., Debezium 3.7; PIPE-06) |
| Deletes | Delete event followed by a tombstone with the same key, `tombstones.on.delete` default true | [Debezium connector for PostgreSQL](https://debezium.io/documentation/reference/stable/connectors/postgresql.html) (n.d., Debezium 3.7; PIPE-06) |
| Delivery | Exactly once in normal operation; at least once on faults; consumers should expect duplicates | [Debezium connector for PostgreSQL](https://debezium.io/documentation/reference/stable/connectors/postgresql.html) (n.d., Debezium 3.7; PIPE-06) |
| DDL | Logical decoding does not carry DDL; `schema.refresh.mode` default `columns_diff` | [Debezium connector for PostgreSQL](https://debezium.io/documentation/reference/stable/connectors/postgresql.html) (n.d., Debezium 3.7; PIPE-06) |
| Truncate | Skipped by default; ordering guaranteed only with a single partition | [Debezium connector for PostgreSQL](https://debezium.io/documentation/reference/stable/connectors/postgresql.html) (n.d., Debezium 3.7; PIPE-06) |
| Incremental snapshot | Schema changes are not supported while one runs | [Debezium connector for PostgreSQL](https://debezium.io/documentation/reference/stable/connectors/postgresql.html) (n.d., Debezium 3.7; PIPE-06) |
| Replication slots | Debezium warns that dropping a slot on the primary loses data | [Debezium connector for PostgreSQL](https://debezium.io/documentation/reference/stable/connectors/postgresql.html) (n.d., Debezium 3.7; PIPE-06) |

### 10.3 Principles

- **CDC-01. MANDATORY. Scope: OLTP tables captured by CDC.** Every captured table has a primary key. Basis [S] under DEFAULT replica identity: [Debezium connector for PostgreSQL](https://debezium.io/documentation/reference/stable/connectors/postgresql.html) (n.d., Debezium 3.7; PIPE-06).
- **CDC-02. OPTIONAL/CONTEXTUAL. Scope: OLTP captured tables.** Choose replica identity by consumer need. Full before-images have a logging cost that the notes do not quantify. Basis [S] for behavior: [Debezium connector for PostgreSQL](https://debezium.io/documentation/reference/stable/connectors/postgresql.html) (n.d., Debezium 3.7; PIPE-06).
- **CDC-03. MANDATORY. Scope: Streaming to OLAP, OLTP or Lakehouse sinks.** CDC sinks are idempotent. Basis [S]: [Debezium connector for PostgreSQL](https://debezium.io/documentation/reference/stable/connectors/postgresql.html) (n.d., Debezium 3.7; PIPE-06).
- **CDC-04. MANDATORY. Scope: OLTP captured tables.** Migrations on captured tables are coordinated with CDC operations: no schema change during an incremental snapshot, and additive changes first. Basis [S] for the snapshot rule ([Debezium connector for PostgreSQL](https://debezium.io/documentation/reference/stable/connectors/postgresql.html) (n.d., Debezium 3.7; PIPE-06)), [I] for additive-first.
- **CDC-05. RECOMMENDED. Scope: Streaming, compacted CDC topics.** Keep tombstones on. Basis [S]: [Debezium connector for PostgreSQL](https://debezium.io/documentation/reference/stable/connectors/postgresql.html) (n.d., Debezium 3.7; PIPE-06).
- **CDC-06. RECOMMENDED. Scope: OLAP, DW landing from CDC.** Retain the operation type and a source position or transaction identifier in landing tables, so deletes and ordering stay visible. Basis [I] from the envelope in [Debezium connector for PostgreSQL](https://debezium.io/documentation/reference/stable/connectors/postgresql.html) (n.d., Debezium 3.7; PIPE-06).
- **CDC-07. RECOMMENDED. Scope: OLTP to Streaming.** Monitor lag and connection health, using `MilliSecondsBehindSource` percentiles, `MilliSecondsSinceLastEvent` and `Connected`. Debezium notes that clock differences affect the lag value: [Debezium connector for PostgreSQL](https://debezium.io/documentation/reference/stable/connectors/postgresql.html) (n.d., Debezium 3.7; PIPE-06), [Debezium: Monitoring](https://debezium.io/documentation/reference/stable/operations/monitoring.html) (n.d., Debezium 3.7). Basis [S] for metrics, [I] for alerting.

### 10.4 CDC versus query-based incremental extraction

- **CDC-08. MANDATORY. Scope: OLTP sources feeding OLAP.** A table feeding incremental loads needs a reliable change signal: log-based CDC, or a maintained `updated_at` or version column. Basis [I]: no fetched source prescribes this either-or. It follows from Debezium's statement that CDC removes the need for a last-updated column: [Debezium Features](https://debezium.io/documentation/reference/stable/features.html) (n.d.; TEN-26). Query-based extraction cannot observe hard deletes without additional design ([I]).

## 11. Transactional outbox

Scope: OLTP to Streaming.

Debezium's Outbox Event Router documents these default columns: `id` (unique event ID, usable to remove duplicates), `aggregatetype` (routing; default topic prefix `outbox.event.`), `aggregateid` (event key, important for ordering in partitions), `type`, `payload` (JSON by default). The transform filters out DELETE operations on the outbox table. Updates are disallowed, but the default `table.op.invalid.behavior` is to warn, so the default does not reject them. `route.tombstone.on.empty.payload` defaults to false: [Debezium Outbox Event Router](https://debezium.io/documentation/reference/stable/transformations/outbox-event-router.html) (n.d., Debezium 3.7; PIPE-05).

- **OUT-01. RECOMMENDED. Scope: OLTP to Streaming.** Publish domain events by writing an outbox row in the same database transaction as the business change. Basis [I]: the outbox page describes reliable exchange between services and Debezium's features page contrasts log-based CDC with dual writes, but the outbox page does not state the dual-write argument itself: [Debezium Outbox Event Router](https://debezium.io/documentation/reference/stable/transformations/outbox-event-router.html) (n.d., Debezium 3.7; PIPE-05), [Debezium Features](https://debezium.io/documentation/reference/stable/features.html) (n.d.; TEN-26).
- **OUT-02. MANDATORY. Scope: OLTP outbox tables under the Debezium router.** The table supplies the roles of unique event ID, aggregate type, aggregate key, event type and payload. The column names listed above are documented defaults. Basis [S]: [Debezium Outbox Event Router](https://debezium.io/documentation/reference/stable/transformations/outbox-event-router.html) (n.d., Debezium 3.7; PIPE-05).
- **OUT-03. MANDATORY. Scope: OLTP outbox tables.** Outbox rows are insert-only. Enforce this in the application or database, because the router's default behavior only warns. Basis [S] for the rule, [I] for enforcement: [Debezium Outbox Event Router](https://debezium.io/documentation/reference/stable/transformations/outbox-event-router.html) (n.d., Debezium 3.7; PIPE-05).
- **OUT-04. MANDATORY. Scope: Streaming consumers of an outbox.** Consumers deduplicate on event ID. The outbox page states no delivery guarantee; only that `id` can deduplicate. Debezium's general guidance to expect duplicates applies: [Debezium Outbox Event Router](https://debezium.io/documentation/reference/stable/transformations/outbox-event-router.html) (n.d., Debezium 3.7; PIPE-05), [Debezium connector for PostgreSQL](https://debezium.io/documentation/reference/stable/connectors/postgresql.html) (n.d., Debezium 3.7; PIPE-06). Basis [S].
- **OUT-05. RECOMMENDED. Scope: OLTP outbox tables.** Set the aggregate key for any aggregate whose events must stay ordered. Basis [S]: [Debezium Outbox Event Router](https://debezium.io/documentation/reference/stable/transformations/outbox-event-router.html) (n.d., Debezium 3.7; PIPE-05).
- **OUT-06. OPTIONAL/CONTEXTUAL. Scope: OLTP outbox tables.** Delete outbox rows soon after writing, since deletes are filtered and do not emit events. Basis [S] for filtering ([Debezium Outbox Event Router](https://debezium.io/documentation/reference/stable/transformations/outbox-event-router.html) (n.d., Debezium 3.7; PIPE-05)), [I] for the housekeeping pattern. Check audit requirements before doing this for financial events.

**Choosing outbox or CDC of business tables ([I]).** CDC of business tables exposes internal structure and physical changes. Outbox publishes a deliberate event contract. ERP and financial systems publishing business events generally fit outbox; replication to analytics generally fits direct CDC. No fetched source makes this comparison, so it is a framework decision to validate.

## 12. Apache Spark

Scope: OLAP, Lakehouse, Streaming as tagged.

### 12.1 Schema inference

Spark's JSON reader infers by default. `samplingRatio` defaults to 1.0; `primitivesAsString`, `prefersDecimal`, `inferTimestamp` and `dropFieldIfAllNull` default to false. Default `PERMISSIVE` mode puts a malformed record in a corrupt-record field and sets malformed fields to null: [Spark SQL JSON Files](https://spark.apache.org/docs/latest/sql-data-sources-json.html) (n.d., Spark 4.3.0; PIPE-07). Structured Streaming from file sources requires a declared schema by default, so that the schema stays consistent across failures; inference can be enabled for ad-hoc use: [Structured Streaming Programming Guide: APIs on DataFrames and Datasets](https://spark.apache.org/docs/latest/streaming/apis-on-dataframes-and-datasets.html) (n.d.; PIPE-08).

- **SPK-01. MANDATORY. Scope: Streaming file sources.** Declare the schema. Basis [S]: [Structured Streaming Programming Guide: APIs on DataFrames and Datasets](https://spark.apache.org/docs/latest/streaming/apis-on-dataframes-and-datasets.html) (n.d.; PIPE-08).
- **SPK-02. RECOMMENDED. Scope: Lakehouse, DW batch ingestion.** Build landing tables from a declared schema and not from inference output. The Spark JSON page does not itself recommend this for batch. Basis [I], from the defaults in [Spark SQL JSON Files](https://spark.apache.org/docs/latest/sql-data-sources-json.html) (n.d., Spark 4.3.0; PIPE-07).
- **SPK-03. RECOMMENDED. Scope: Lakehouse, DW batch ingestion.** Capture corrupt records with a user-defined schema field instead of letting bad rows become silent nulls. Basis [S]: [Spark SQL JSON Files](https://spark.apache.org/docs/latest/sql-data-sources-json.html) (n.d., Spark 4.3.0; PIPE-07).

### 12.2 Structured Streaming output

| Sink | Guarantee |
|---|---|
| File | Exactly-once |
| Kafka | At-least-once |
| Foreach | At-least-once |
| ForeachBatch | Depends on implementation; at-least-once by default, `batchId` can deduplicate |
| Memory | Not fault tolerant |

Source: [Structured Streaming Programming Guide: APIs on DataFrames and Datasets](https://spark.apache.org/docs/latest/streaming/apis-on-dataframes-and-datasets.html) (n.d.; PIPE-08).

- **SPK-04. MANDATORY. Scope: Streaming to OLTP or OLAP database sinks.** Use `batchId` or natural keys for idempotent writes when exactly-once matters. Basis [S]: [Structured Streaming Programming Guide: APIs on DataFrames and Datasets](https://spark.apache.org/docs/latest/streaming/apis-on-dataframes-and-datasets.html) (n.d.; PIPE-08).
- **SPK-05. MANDATORY. Scope: Streaming.** File-source inputs must be placed atomically in the directory. Basis [S]: [Structured Streaming Programming Guide: APIs on DataFrames and Datasets](https://spark.apache.org/docs/latest/streaming/apis-on-dataframes-and-datasets.html) (n.d.; PIPE-08).
- **SPK-06. MANDATORY. Scope: Streaming.** Append mode requires results that never change. Aggregations without a watermark do not support append mode, and non-aggregate queries do not support complete mode: [Structured Streaming Programming Guide: APIs on DataFrames and Datasets](https://spark.apache.org/docs/latest/streaming/apis-on-dataframes-and-datasets.html) (n.d.; PIPE-08). Basis [S].
- **SPK-07. MANDATORY. Scope: Streaming.** Define watermarks and time constraints for outer and semi stream-stream joins. They are required, while inner joins grow state indefinitely without them: [Structured Streaming Programming Guide: APIs on DataFrames and Datasets](https://spark.apache.org/docs/latest/streaming/apis-on-dataframes-and-datasets.html) (n.d.; PIPE-08). Basis [S].

## 13. Open table formats and schema evolution

Scope of this section: Lakehouse. None of these formats is an OLTP store.

### 13.1 Comparison

| Capability | Apache Iceberg | Delta Lake | Apache Hudi |
|---|---|---|---|
| Column tracking | By immutable field ID ([Iceberg Table Spec](https://iceberg.apache.org/spec/) (n.d.; PIPE-09)) | Not stated directly in pages read; rename and drop need column mapping, and the notes infer name-based tracking otherwise ([Delta Lake: Table batch reads and writes](https://docs.delta.io/latest/delta-batch.html) (n.d.; PIPE-11), [Update Delta Lake table schema](https://docs.databricks.com/aws/en/delta/update-schema) (2026-09-11; vendor)) | Write-mode rules below; internals not read |
| Add column | Metadata-only ([Iceberg Docs: Evolution](https://iceberg.apache.org/docs/latest/evolution/) (n.d., docs 1.12.0; PIPE-10)) | Opt-in per write or via DDL, added at end, existing rows null ([Delta Lake: Table batch reads and writes](https://docs.delta.io/latest/delta-batch.html) (n.d.; PIPE-11), [Update Delta Lake table schema](https://docs.databricks.com/aws/en/delta/update-schema) (2026-09-11; vendor)) | Nullable at end of root or struct ([Apache Hudi: Schema Evolution](https://hudi.apache.org/docs/schema_evolution) (n.d., version 1.2.1; PIPE-12)) |
| Add non-nullable column | Not stated in pages read | Not stated in pages read | Rejected ([Apache Hudi: Schema Evolution](https://hudi.apache.org/docs/schema_evolution) (n.d., version 1.2.1; PIPE-12)) |
| Rename | Metadata-only, ID unchanged ([Iceberg Table Spec](https://iceberg.apache.org/spec/) (n.d.; PIPE-09), [Iceberg Docs: Evolution](https://iceberg.apache.org/docs/latest/evolution/) (n.d., docs 1.12.0; PIPE-10)) | Requires column mapping, else table rewrite ([Delta Lake: Table batch reads and writes](https://docs.delta.io/latest/delta-batch.html) (n.d.; PIPE-11)) | Only under experimental schema-on-read ([Apache Hudi: Schema Evolution](https://hudi.apache.org/docs/schema_evolution) (n.d., version 1.2.1; PIPE-12)) |
| Drop | Metadata-only ([Iceberg Docs: Evolution](https://iceberg.apache.org/docs/latest/evolution/) (n.d., docs 1.12.0; PIPE-10)) | Requires column mapping; data not removed from files by the drop ([Delta Lake: Table batch reads and writes](https://docs.delta.io/latest/delta-batch.html) (n.d.; PIPE-11), [Update Delta Lake table schema](https://docs.databricks.com/aws/en/delta/update-schema) (2026-09-11; vendor)) | Only under experimental schema-on-read ([Apache Hudi: Schema Evolution](https://hudi.apache.org/docs/schema_evolution) (n.d., version 1.2.1; PIPE-12)) |
| Reorder | Allowed, no side effects ([Iceberg Docs: Evolution](https://iceberg.apache.org/docs/latest/evolution/) (n.d., docs 1.12.0; PIPE-10)) | Via ALTER TABLE ([Delta Lake: Table batch reads and writes](https://docs.delta.io/latest/delta-batch.html) (n.d.; PIPE-11)) | Adding a column together with reorder rejected in write mode ([Apache Hudi: Schema Evolution](https://hudi.apache.org/docs/schema_evolution) (n.d., version 1.2.1; PIPE-12)) |
| Type widening | int to long, float to double, decimal precision; date to timestamp in v3 ([Iceberg Table Spec](https://iceberg.apache.org/spec/) (n.d.; PIPE-09)) | Mismatches rejected by default; the type-widening page was not fetched ([Delta Lake: Table batch reads and writes](https://docs.delta.io/latest/delta-batch.html) (n.d.; PIPE-11)) | Includes numerics to string and string to and from bytes; matrix reconstructed in notes, verify on live page ([Apache Hudi: Schema Evolution](https://hudi.apache.org/docs/schema_evolution) (n.d., version 1.2.1; PIPE-12)) |
| Extra columns on write | Not stated in pages read | Rejected by default ([Delta Lake: Table batch reads and writes](https://docs.delta.io/latest/delta-batch.html) (n.d.; PIPE-11)) | Not stated in pages read |
| Missing columns on write | Not stated in pages read | Set to null ([Delta Lake: Table batch reads and writes](https://docs.delta.io/latest/delta-batch.html) (n.d.; PIPE-11)) | Pipeline fails unless `hoodie.write.set.null.for.missing.columns` is set ([Apache Hudi: Schema Evolution](https://hudi.apache.org/docs/schema_evolution) (n.d., version 1.2.1; PIPE-12)) |
| Partitioning | Hidden, derived by transforms; can evolve as metadata ([Iceberg Docs: Partitioning](https://iceberg.apache.org/docs/latest/partitioning/) (n.d.), [Iceberg Docs: Evolution](https://iceberg.apache.org/docs/latest/evolution/) (n.d., docs 1.12.0; PIPE-10)) | Databricks recommends liquid clustering for new tables, replacing partitioning and ZORDER ([Use liquid clustering for tables](https://docs.databricks.com/aws/en/delta/clustering) (2026-11-02; LAKE-03; vendor)) | Not read |
| Isolation | Atomic metadata swap provides serializable isolation basis; readers see committed snapshots ([Iceberg Table Spec](https://iceberg.apache.org/spec/) (n.d.; PIPE-09)) | Writes serializable, reads snapshot isolated, per the Delta paper ([Delta Lake: High-Performance ACID Table Storage over Cloud Object Stores](https://www.vldb.org/pvldb/vol13/p3411-armbrust.pdf) (2020; LAKE-08)) | Not read |
| Time travel | Snapshot-based; branches and tags ([Apache Iceberg: Branching and Tagging](https://iceberg.apache.org/docs/latest/branching/) (n.d., docs 1.12.0; DQ-12)) | `VERSION AS OF`, `TIMESTAMP AS OF` ([Delta Lake: Table batch reads and writes](https://docs.delta.io/latest/delta-batch.html) (n.d.; PIPE-11)) | Not read |

### 13.2 Principles

- **OTF-01. MANDATORY. Scope: Lakehouse.** Only additive nullable column additions at the end of a table or struct are treated as portable across Iceberg, Delta and Hudi. Basis [S] across [Iceberg Docs: Evolution](https://iceberg.apache.org/docs/latest/evolution/) (n.d., docs 1.12.0; PIPE-10), [Delta Lake: Table batch reads and writes](https://docs.delta.io/latest/delta-batch.html) (n.d.; PIPE-11), [Apache Hudi: Schema Evolution](https://hudi.apache.org/docs/schema_evolution) (n.d., version 1.2.1; PIPE-12).
- **OTF-02. RECOMMENDED. Scope: Lakehouse.** Treat type widening as format-specific until verified per format. **Correction to the notes:** the notes name int to long, float to double and decimal precision widening as the portable intersection, but Delta's type-widening page was not fetched and the Hudi matrix read shows no decimal entry. Only Iceberg's rules for those three are confirmed: [Iceberg Table Spec](https://iceberg.apache.org/spec/) (n.d.; PIPE-09), [Apache Hudi: Schema Evolution](https://hudi.apache.org/docs/schema_evolution) (n.d., version 1.2.1; PIPE-12), [Delta Lake: Table batch reads and writes](https://docs.delta.io/latest/delta-batch.html) (n.d.; PIPE-11). Basis [S] for each format and [I] for the restriction.
- **OTF-03. MANDATORY. Scope: Lakehouse, DW.** Never reuse a dropped column's name for a different meaning. Iceberg warns that formats tracking columns by name can inadvertently un-delete a column when a name is reused: [Iceberg Docs: Evolution](https://iceberg.apache.org/docs/latest/evolution/) (n.d., docs 1.12.0; PIPE-10). Basis [S] for the mechanism, [I] for generalizing to all storage.
- **OTF-04. RECOMMENDED. Scope: Lakehouse on Iceberg.** Derive partitions by transform from a real timestamp column instead of maintaining a synthetic date column. Iceberg documents silent wrong results when writers produce a wrong partition format under Hive-style partitioning: [Iceberg Docs: Partitioning](https://iceberg.apache.org/docs/latest/partitioning/) (n.d.). Basis [S].
- **OTF-05. RECOMMENDED. Scope: Lakehouse on Delta.** Enable schema evolution per write, never session-wide. Both delta.io and Databricks advise against the session-wide setting: [Delta Lake: Table batch reads and writes](https://docs.delta.io/latest/delta-batch.html) (n.d.; PIPE-11), [Update Delta Lake table schema](https://docs.databricks.com/aws/en/delta/update-schema) (2026-09-11; vendor). Basis [S]. Schema updates conflict with concurrent writes and terminate streams reading the table: [Update Delta Lake table schema](https://docs.databricks.com/aws/en/delta/update-schema) (2026-09-11; vendor).
- **OTF-06. RECOMMENDED. Scope: Lakehouse on Hudi.** Stay in write-mode evolution. Schema-on-read is experimental and cannot be disabled after enabling: [Apache Hudi: Schema Evolution](https://hudi.apache.org/docs/schema_evolution) (n.d., version 1.2.1; PIPE-12). Basis [S].
- **OTF-07. MANDATORY. Scope: Lakehouse.** Treat logical drop as distinct from physical erasure. In Delta, dropping a column does not delete its data from files: [Delta Lake: Table batch reads and writes](https://docs.delta.io/latest/delta-batch.html) (n.d.; PIPE-11), [Update Delta Lake table schema](https://docs.databricks.com/aws/en/delta/update-schema) (2026-09-11; vendor). Basis [S]. Privacy deletion needs a physical rewrite step and retention clean-up.
- **OTF-08. RECOMMENDED. Scope: Lakehouse.** Align time-travel retention with reprocessing and audit needs, and do not treat table history as backup. Databricks says not to use table history for long-term archival: [Work with Delta Lake table history](https://docs.databricks.com/aws/en/delta/history) (2026-11-06; vendor). Basis [S].
- **OTF-09. OPTIONAL/CONTEXTUAL. Scope: Lakehouse.** Model clustering keys as a changeable property. Basis [I]: [Use liquid clustering for tables](https://docs.databricks.com/aws/en/delta/clustering) (2026-11-02; LAKE-03; vendor).
- **OTF-10. RECOMMENDED. Scope: Lakehouse on Iceberg.** Use audit branches for write-audit-publish. The table's schema applies across branches: [Apache Iceberg: Branching and Tagging](https://iceberg.apache.org/docs/latest/branching/) (n.d., docs 1.12.0; DQ-12). Basis [S]. See the companion document on promotion gates.

### 13.3 Format conflicts

- **Rename and drop:** Iceberg by default, Delta only with column mapping, Hudi only with an irreversible experimental mode. This affects any framework rule on renames: [Iceberg Docs: Evolution](https://iceberg.apache.org/docs/latest/evolution/) (n.d., docs 1.12.0; PIPE-10), [Delta Lake: Table batch reads and writes](https://docs.delta.io/latest/delta-batch.html) (n.d.; PIPE-11), [Apache Hudi: Schema Evolution](https://hudi.apache.org/docs/schema_evolution) (n.d., version 1.2.1; PIPE-12).
- **Delta retention wording:** delta.io says up to 30 days of time travel by default, while Databricks says that from Runtime 18.0 queries older than the 7-day deleted-file threshold are blocked. The default log retention is 30 days and deleted-file retention is 7 days in both: [Delta Lake: Table batch reads and writes](https://docs.delta.io/latest/delta-batch.html) (n.d.; PIPE-11), [Work with Delta Lake table history](https://docs.databricks.com/aws/en/delta/history) (2026-11-06; vendor). Check the actual platform rather than assuming 30 days.
- **Hidden partitions:** the Iceberg page's critique is aimed at Hive. **The notes' statement that Delta and Hudi expose partition columns as a contrast is not supported by a Delta or Hudi partitioning page**; those pages were not read for this.

### 13.4 Vendor claim to treat carefully

Databricks states that medallion guarantees ACID properties as data passes through layers: [Medallion lakehouse architecture](https://docs.databricks.com/aws/en/lakehouse/medallion) (2026-10-29; LAKE-01; vendor). The evidence read supports single-table transactions; the Delta paper says "Delta Lake currently only supports transactions within one table": [Delta Lake: High-Performance ACID Table Storage over Cloud Object Stores](https://www.vldb.org/pvldb/vol13/p3411-armbrust.pdf) (2020; LAKE-08). Multi-table atomicity was reported as a private preview in December 2025: [Databricks Lakehouse Data Modeling: Myths, Truths, and Best Practices](https://www.databricks.com/blog/databricks-lakehouse-data-modeling-myths-truths-and-best-practices) (2025-12-15; LAKE-06; vendor). Treat cross-layer atomicity as not established.

## 14. Orchestration

Scope: All pipeline-run workloads, applied mainly to DW and Lakehouse. Orchestrators do not manage OLTP transactions.

### 14.1 Airflow rules

- **ORC-01. MANDATORY. Scope: DW, Lakehouse, batch pipelines.** Treat tasks like database transactions: a re-run produces the same outcome, without duplicates, and never a partial result. Airflow's guidance is to use upsert and not a plain insert that duplicates on re-run: [Airflow Best Practices](https://airflow.apache.org/docs/apache-airflow/stable/best-practices.html) (n.d., Airflow 3.4.0; PIPE-13). Basis [S]. The page does not use the words idempotent or atomic; the transaction analogy is its framing.
- **ORC-02. MANDATORY. Scope: DW, Lakehouse, batch pipelines.** Read a specific partition for the data interval and never the latest data. Basis [S]: [Airflow Best Practices](https://airflow.apache.org/docs/apache-airflow/stable/best-practices.html) (n.d., Airflow 3.4.0; PIPE-13).
- **ORC-03. MANDATORY. Scope: DW, Lakehouse, batch pipelines.** Do not base logic on wall-clock calls such as `datetime.now()` within a task. Basis [S]: [Airflow Best Practices](https://airflow.apache.org/docs/apache-airflow/stable/best-practices.html) (n.d., Airflow 3.4.0; PIPE-13).
- **ORC-04. MANDATORY. Scope: Airflow deployments.** Do no database access, heavy computation or networking at DAG top level. Basis [S]: [Airflow Best Practices](https://airflow.apache.org/docs/apache-airflow/stable/best-practices.html) (n.d., Airflow 3.4.0; PIPE-13).
- **ORC-05. RECOMMENDED. Scope: Airflow deployments.** Use XCom only for small messages, use remote storage for larger data, and keep credentials in Connections. Basis [S]: [Airflow Best Practices](https://airflow.apache.org/docs/apache-airflow/stable/best-practices.html) (n.d., Airflow 3.4.0; PIPE-13).
- **ORC-06. RECOMMENDED. Scope: Airflow deployments.** Take care when deleting tasks, since history becomes hard to inspect. Test DAGs, use a staging environment, and do not hard-code per-environment values. Back up the metadata database before upgrades. Basis [S]: [Airflow Best Practices](https://airflow.apache.org/docs/apache-airflow/stable/best-practices.html) (n.d., Airflow 3.4.0; PIPE-13).

### 14.2 Data gates

Airflow provides SQL column, table, value and threshold check operators: [Airflow common-sql provider: Operators](https://airflow.apache.org/docs/apache-airflow-providers-common-sql/stable/operators.html) (n.d., provider 2.4.0). Dagster asset checks test one property each and, with `blocking=True`, prevent downstream materialization; by default a failed check does not stop the run: [Dagster Docs: Asset checks](https://dagster.io/docs/guides/test/asset-checks) (n.d.; vendor). Databricks warns that expectations control data quality and not orchestration, so a validation table does not by itself block downstream tables: [Databricks: Expectation recommendations and advanced patterns](https://docs.databricks.com/aws/en/ldp/expectation-patterns) (2026-10-26; vendor).

- **ORC-07. MANDATORY. Scope: DW, Lakehouse, datasets published to consumers.** A check only protects consumers if the orchestration blocks on it. Basis [S]: [Dagster Docs: Asset checks](https://dagster.io/docs/guides/test/asset-checks) (n.d.; vendor), [Databricks: Expectation recommendations and advanced patterns](https://docs.databricks.com/aws/en/ldp/expectation-patterns) (2026-10-26; vendor).

### 14.3 Task-centric versus asset-centric orchestration

**Conflict in emphasis.** Airflow models dependencies between tasks ([Airflow Best Practices](https://airflow.apache.org/docs/apache-airflow/stable/best-practices.html) (n.d., Airflow 3.4.0; PIPE-13)). Dagster (vendor) models persistent assets with declared dependencies and attached checks ([Dagster Docs: Assets](https://dagster.io/docs/guides/build/assets) (n.d.; PIPE-14; vendor)). Both require re-runnable units. They differ on whether the job or the data asset is the first-class object.

- **ORC-08. OPTIONAL/CONTEXTUAL. Scope: DW, Lakehouse.** Either model is acceptable. Basis [I]. In asset-centric designs, a machine-readable schema allows a conformance check on the asset.

### 14.4 Platform-native orchestration

- **ORC-09. OPTIONAL/CONTEXTUAL. Scope: DW on Snowflake.** Streams and tasks suit procedural logic, MERGE, external calls and CRON, while dynamic tables are declarative and read-only: [Decision guide for dynamic tables](https://docs.snowflake.com/en/user-guide/dynamic-tables-comparison) (n.d.; LAKE-12; vendor). A stream goes stale if its offset falls outside retention: [Introduction to Streams](https://docs.snowflake.com/en/user-guide/streams-intro) (n.d.; vendor). Basis [S], vendor.

## 15. Idempotency

Scope tags per principle. This section consolidates a constraint that recurs throughout.

### 15.1 Why it is unavoidable

| System | Guarantee to external sinks | Source |
|---|---|---|
| Kafka | Sink must manage offsets with output | [Apache Kafka 4.3 Design](https://kafka.apache.org/43/design/design/) (n.d.; PIPE-01) |
| Debezium | At least once under fault | [Debezium connector for PostgreSQL](https://debezium.io/documentation/reference/stable/connectors/postgresql.html) (n.d., Debezium 3.7; PIPE-06) |
| Spark ForeachBatch | At least once by default | [Structured Streaming Programming Guide: APIs on DataFrames and Datasets](https://spark.apache.org/docs/latest/streaming/apis-on-dataframes-and-datasets.html) (n.d.; PIPE-08) |
| Airflow | Tasks may be retried | [Airflow Best Practices](https://airflow.apache.org/docs/apache-airflow/stable/best-practices.html) (n.d., Airflow 3.4.0; PIPE-13) |

### 15.2 Principles

- **IDM-01. MANDATORY. Scope: All sinks written by a pipeline (OLTP, DW, Lakehouse).** Every sink write is safely repeatable. Basis [S] for the need (table above), [I] for the universal rule.
- **IDM-02. MANDATORY. Scope: DW, Lakehouse, OLTP targets of pipelines.** Each target declares its merge or overwrite grain: a business key or a partition and interval. Basis [I], from the upsert rule in [Airflow Best Practices](https://airflow.apache.org/docs/apache-airflow/stable/best-practices.html) (n.d., Airflow 3.4.0; PIPE-13).
- **IDM-03. MANDATORY. Scope: Streaming to OLTP, DW, Lakehouse.** Event records carry a deduplication identifier: for example the outbox `id`, a source position, or a `batchId` at the sink. Basis [S] for each mechanism: [Debezium Outbox Event Router](https://debezium.io/documentation/reference/stable/transformations/outbox-event-router.html) (n.d., Debezium 3.7; PIPE-05), [Debezium connector for PostgreSQL](https://debezium.io/documentation/reference/stable/connectors/postgresql.html) (n.d., Debezium 3.7; PIPE-06), [Structured Streaming Programming Guide: APIs on DataFrames and Datasets](https://spark.apache.org/docs/latest/streaming/apis-on-dataframes-and-datasets.html) (n.d.; PIPE-08).
- **IDM-04. RECOMMENDED. Scope: OLTP or DW sinks without atomic merge.** Store the consumer offset or checkpoint within the same transaction as the output. Basis [S]: [Apache Kafka 4.3 Design](https://kafka.apache.org/43/design/design/) (n.d.; PIPE-01).
- **IDM-05. RECOMMENDED. Scope: Streaming.** Confluent catalogs Idempotent Writer and Idempotent Reader as patterns: [Confluent Event Streaming Patterns](https://developer.confluent.io/patterns/) (n.d.; vendor). Their pattern bodies were not read, so only the existence of the catalog entries is supported.
- **IDM-06. RECOMMENDED. Scope: DW, for surrogate key generation under replay.** Weigh hash-derived keys against sequence-generated ones. Hash keys help parallel and join-free loading, but warehouse performance guidance favors numeric keys (see the companion document's conflict register). Basis [I].

## 16. Backfills and reprocessing

No fetched source defines a backfill standard, and Airflow's own backfill tooling is not covered in the notes. This section assembles rules from adjacent evidence and most principles are therefore [I].

- **BKF-01. MANDATORY. Scope: DW, Lakehouse.** A backfill overwrites or merges exactly one declared interval or partition at a time. Basis [I], from the interval and upsert rules in [Airflow Best Practices](https://airflow.apache.org/docs/apache-airflow/stable/best-practices.html) (n.d., Airflow 3.4.0; PIPE-13).
- **BKF-02. MANDATORY. Scope: OLTP.** OLTP backfills run in batches and throttled, outside the DDL transaction. Basis [S]: [ankane/strong_migrations README](https://github.com/ankane/strong_migrations) (n.d.; OPS-08), [GitLab Migration Style Guide](https://docs.gitlab.com/ee/development/migration_style_guide.html) (n.d.; OPS-04). The companion document gives the sequence.
- **BKF-03. RECOMMENDED. Scope: OLAP, Streaming.** For logic changes on retained logs, rebuild into a new output table and switch readers. Basis [S]: [Questioning the Lambda Architecture](https://www.oreilly.com/radar/questioning-the-lambda-architecture/) (2014-07-02; PIPE-15).
- **BKF-04. RECOMMENDED. Scope: DW, Lakehouse.** Backfills publish through a gate: write to a non-visible location, audit, then publish. Basis [S] for write-audit-publish: [Apache Iceberg: Branching and Tagging](https://iceberg.apache.org/docs/latest/branching/) (n.d., docs 1.12.0; DQ-12), [Scaling Data Quality @ Netflix](https://www.slideshare.net/MichelleFUfford/scaling-data-quality-netflix-76917740) (2017-06-12; DQ-13). Applying it to backfills is [I].
- **BKF-05. MANDATORY. Scope: All backfills of financial data.** Reconcile after a backfill. Stripe re-ran its offline job to confirm no records were missed: [Online migrations at scale](https://stripe.com/blog/online-migrations) (2017-02-02; OPS-06). Basis [S] for the example, [I] for the rule.
- **BKF-06. MANDATORY. Scope: DW.** Treat history capture as non-reconstructable. dbt says snapshots cannot be rebuilt and suggests a separate schema: [dbt: Add snapshots to your DAG](https://docs.getdbt.com/docs/build/snapshots) (2026-09-29; LAKE-18; vendor). Basis [S], vendor.
- **BKF-07. RECOMMENDED. Scope: Lakehouse.** Consider downstream streaming readers when restoring. Databricks notes RESTORE is a data-changing operation that can produce duplicates for streaming consumers: [Work with Delta Lake table history](https://docs.databricks.com/aws/en/delta/history) (2026-11-06; vendor). Basis [S], vendor.
- **BKF-08. RECOMMENDED. Scope: DW, Lakehouse.** Use lineage to determine a backfill's blast radius. Marquez describes its lineage API as supporting backfills and root cause analysis: [Marquez](https://marquezproject.ai/) (n.d.). Basis [S].

## 17. Late and out-of-order data

### 17.1 Evidence

- Spark's watermark guarantees that data less late than the threshold is not dropped. The guarantee holds in one direction only: later data may or may not be processed: [Structured Streaming Programming Guide: APIs on DataFrames and Datasets](https://spark.apache.org/docs/latest/streaming/apis-on-dataframes-and-datasets.html) (n.d.; PIPE-08).
- Preconditions for watermark state cleanup are append or update output mode, an event-time column or window in the aggregation, and calling `withWatermark` on the same column before the aggregation: [Structured Streaming Programming Guide: APIs on DataFrames and Datasets](https://spark.apache.org/docs/latest/streaming/apis-on-dataframes-and-datasets.html) (n.d.; PIPE-08).
- Dataflow watermarks are heuristic, so they can be wrong: [The Dataflow Model](https://www.vldb.org/pvldb/vol8/p1792-Akidau.pdf) (2015; PIPE-17).
- Kimball says that late-arriving facts must look up the dimension keys effective when the event occurred: [Kimball Techniques: Late Arriving Facts](https://www.kimballgroup.com/data-warehouse-business-intelligence-resources/kimball-techniques/dimensional-modeling-techniques/late-arriving-fact/) (n.d.).
- Databricks lists late and out-of-order handling among silver-layer operations: [Medallion lakehouse architecture](https://docs.databricks.com/aws/en/lakehouse/medallion) (2026-10-29; LAKE-01; vendor).

### 17.2 Principles

- **LAT-01. MANDATORY. Scope: Streaming.** Treat the watermark as a lower bound on what is kept, and do not rely on data later than the threshold being dropped. Basis [S]: [Structured Streaming Programming Guide: APIs on DataFrames and Datasets](https://spark.apache.org/docs/latest/streaming/apis-on-dataframes-and-datasets.html) (n.d.; PIPE-08).
- **LAT-02. RECOMMENDED. Scope: Streaming to OLAP.** Set a late-data policy per table: the allowed lateness, and what happens after it. Basis [S] on the mechanics ([Structured Streaming Programming Guide: APIs on DataFrames and Datasets](https://spark.apache.org/docs/latest/streaming/apis-on-dataframes-and-datasets.html) (n.d.; PIPE-08), [The Dataflow Model](https://www.vldb.org/pvldb/vol8/p1792-Akidau.pdf) (2015; PIPE-17)), [I] for the per-table rule.
- **LAT-03. RECOMMENDED. Scope: Streaming to OLAP.** Streaming aggregate tables keep a key and window as upsert grain plus a processing-time update column, so late refinements are visible. Basis [I]: [The Dataflow Model](https://www.vldb.org/pvldb/vol8/p1792-Akidau.pdf) (2015; PIPE-17), [Structured Streaming Programming Guide: APIs on DataFrames and Datasets](https://spark.apache.org/docs/latest/streaming/apis-on-dataframes-and-datasets.html) (n.d.; PIPE-08).
- **LAT-04. MANDATORY. Scope: DW, where facts can arrive late.** Dimensions used for late facts keep effective-date ranges. Basis [S] for the lookup ([Kimball Techniques: Late Arriving Facts](https://www.kimballgroup.com/data-warehouse-business-intelligence-resources/kimball-techniques/dimensional-modeling-techniques/late-arriving-fact/) (n.d.)), [I] for the design requirement.
- **LAT-05. OPTIONAL/CONTEXTUAL. Scope: DW.** Handling for late-arriving dimensions, such as placeholder members, needs a framework decision. No fetched source in these notes prescribes it.
- **LAT-06. RECOMMENDED. Scope: DW for financial reporting.** Define when a reporting period closes to late data, and how post-close items are restated. Oracle runs subledger reconciliation only after periods close to new transactions: [Oracle: Account Reconciliation and Subledgers](https://docs.oracle.com/en/cloud/saas/financials/26a/faugl/account-reconciliation-and-subledgers.html) (n.d., release 26A; DQ-16; vendor). Basis [S] for reconciliation timing, [I] for restatement.

## 18. Requirements pipelines impose on source schemas

Consolidated from notes section KQ5, with labels and basis restated. These are research findings for later framework work; they are not schema definitions.

| # | Requirement | Label | Scope | Motivating evidence | Basis |
|---|---|---|---|---|---|
| 1 | Stable identity key per entity table and event | MANDATORY | OLTP, Streaming, DW, Lakehouse | Partition routing and compaction ([Apache Kafka 4.3 Design](https://kafka.apache.org/43/design/design/) (n.d.; PIPE-01)); no PK yields create events only ([Debezium connector for PostgreSQL](https://debezium.io/documentation/reference/stable/connectors/postgresql.html) (n.d., Debezium 3.7; PIPE-06)); outbox key ordering ([Debezium Outbox Event Router](https://debezium.io/documentation/reference/stable/transformations/outbox-event-router.html) (n.d., Debezium 3.7; PIPE-05)); upsert needs a key ([Airflow Best Practices](https://airflow.apache.org/docs/apache-airflow/stable/best-practices.html) (n.d., Airflow 3.4.0; PIPE-13)) | [S] |
| 2 | Reliable change signal: CDC or a maintained `updated_at`/version | MANDATORY | OLTP sources feeding OLAP | Debezium says CDC removes the need for such a column ([Debezium Features](https://debezium.io/documentation/reference/stable/features.html) (n.d.; TEN-26)) | [I] |
| 3 | Event-time field distinct from processing and ingest time | MANDATORY | Streaming, Lakehouse | Broker timestamp is a topic setting ([Kafka 4.2 Topic Configs](https://kafka.apache.org/42/configuration/topic-configs/) (n.d.)); watermark on event time ([Structured Streaming Programming Guide: APIs on DataFrames and Datasets](https://spark.apache.org/docs/latest/streaming/apis-on-dataframes-and-datasets.html) (n.d.; PIPE-08)); Dataflow separation ([The Dataflow Model](https://www.vldb.org/pvldb/vol8/p1792-Akidau.pdf) (2015; PIPE-17)) | [S] for mechanisms, [I] for field |
| 4 | Additive, nullable or defaulted evolution as the default change | MANDATORY | Streaming, Lakehouse, DW | Avro defaults ([Schema Evolution and Compatibility for Schema Registry on Confluent Platform](https://docs.confluent.io/platform/current/schema-registry/fundamentals/schema-evolution.html) (2026-10-13; PIPE-02; vendor)); Hudi nullable adds ([Apache Hudi: Schema Evolution](https://hudi.apache.org/docs/schema_evolution) (n.d., version 1.2.1; PIPE-12)); Iceberg additive semantics ([Iceberg Docs: Evolution](https://iceberg.apache.org/docs/latest/evolution/) (n.d., docs 1.12.0; PIPE-10)); Delta additions ([Delta Lake: Table batch reads and writes](https://docs.delta.io/latest/delta-batch.html) (n.d.; PIPE-11)) | [S] |
| 5 | No reuse of a dropped column name for a new meaning | MANDATORY | Lakehouse, DW | Name-tracking un-delete risk ([Iceberg Docs: Evolution](https://iceberg.apache.org/docs/latest/evolution/) (n.d., docs 1.12.0; PIPE-10)) | [S], generalized by [I] |
| 6 | Deletes are representable | MANDATORY | Streaming, DW, Lakehouse | Null-payload tombstones ([Apache Kafka 4.3 Design](https://kafka.apache.org/43/design/design/) (n.d.; PIPE-01)); delete plus tombstone ([Debezium connector for PostgreSQL](https://debezium.io/documentation/reference/stable/connectors/postgresql.html) (n.d., Debezium 3.7; PIPE-06)); soft-delete flag or operation column in landing tables is [I] | [S] and [I] |
| 7 | Idempotency or deduplication key at sinks | MANDATORY | All sinks | [Debezium connector for PostgreSQL](https://debezium.io/documentation/reference/stable/connectors/postgresql.html) (n.d., Debezium 3.7; PIPE-06), [Apache Kafka 4.3 Design](https://kafka.apache.org/43/design/design/) (n.d.; PIPE-01), [Structured Streaming Programming Guide: APIs on DataFrames and Datasets](https://spark.apache.org/docs/latest/streaming/apis-on-dataframes-and-datasets.html) (n.d.; PIPE-08), [Debezium Outbox Event Router](https://debezium.io/documentation/reference/stable/transformations/outbox-event-router.html) (n.d., Debezium 3.7; PIPE-05), [Airflow Best Practices](https://airflow.apache.org/docs/apache-airflow/stable/best-practices.html) (n.d., Airflow 3.4.0; PIPE-13) | [S] |
| 8 | Interval or partition column aligned to the orchestrator | MANDATORY | DW, Lakehouse | Interval reads ([Airflow Best Practices](https://airflow.apache.org/docs/apache-airflow/stable/best-practices.html) (n.d., Airflow 3.4.0; PIPE-13)); Iceberg transforms still need the underlying timestamp ([Iceberg Docs: Partitioning](https://iceberg.apache.org/docs/latest/partitioning/) (n.d.)) | [S] and [I] |
| 9 | Late-data policy per table | RECOMMENDED | Streaming to OLAP | [Structured Streaming Programming Guide: APIs on DataFrames and Datasets](https://spark.apache.org/docs/latest/streaming/apis-on-dataframes-and-datasets.html) (n.d.; PIPE-08), [The Dataflow Model](https://www.vldb.org/pvldb/vol8/p1792-Akidau.pdf) (2015; PIPE-17) | [I] |
| 10 | Compatibility mode and upgrade order declared per stream | MANDATORY | Streaming | [Schema Evolution and Compatibility for Schema Registry on Confluent Platform](https://docs.confluent.io/platform/current/schema-registry/fundamentals/schema-evolution.html) (2026-10-13; PIPE-02; vendor), [Schema Evolution pattern](https://developer.confluent.io/patterns/event-stream/schema-evolution/) (n.d.; vendor) | [S] |
| 11 | Retention at least the reprocessing and audit window | RECOMMENDED | Streaming, Lakehouse | [Kafka 4.2 Topic Configs](https://kafka.apache.org/42/configuration/topic-configs/) (n.d.), [Questioning the Lambda Architecture](https://www.oreilly.com/radar/questioning-the-lambda-architecture/) (2014-07-02; PIPE-15), [Delta Lake: Table batch reads and writes](https://docs.delta.io/latest/delta-batch.html) (n.d.; PIPE-11) | [S] and [I] |
| 12 | Declared schemas for landing | MANDATORY for streaming file sources; RECOMMENDED otherwise | Streaming; DW, Lakehouse | [Structured Streaming Programming Guide: APIs on DataFrames and Datasets](https://spark.apache.org/docs/latest/streaming/apis-on-dataframes-and-datasets.html) (n.d.; PIPE-08), [Spark SQL JSON Files](https://spark.apache.org/docs/latest/sql-data-sources-json.html) (n.d., Spark 4.3.0; PIPE-07) | [S] and [I] |
| 13 | Contract beyond schema: quality, SLA, ownership | RECOMMENDED | Cross-team datasets, any scope | [Open Data Contract Standard (latest)](https://bitol-io.github.io/open-data-contract-standard/latest/) (n.d.; PIPE-20), [Dagster Docs: Asset checks](https://dagster.io/docs/guides/test/asset-checks) (n.d.; vendor) | [S] |
| 14 | Swappable or versioned outputs for reprocessing | OPTIONAL/CONTEXTUAL | OLAP, Streaming | [Questioning the Lambda Architecture](https://www.oreilly.com/radar/questioning-the-lambda-architecture/) (2014-07-02; PIPE-15) | [S] and [I] |
| 15 | Monetary values exact-typed from the first typed layer | MANDATORY | OLTP, DW, Lakehouse | Spark float inference default ([Spark SQL JSON Files](https://spark.apache.org/docs/latest/sql-data-sources-json.html) (n.d., Spark 4.3.0; PIPE-07)); see companion document | [I] |

### 18.1 What this means by source type

- **OLTP, ERP and financial sources:** primary keys on all captured tables (1); a change signal (2); deliberate event publication through an outbox where business events cross system boundaries (section 11); soft-versus-hard delete policy compatible with downstream delete handling (6).
- **SaaS multi-tenant sources:** the requirements above apply per tenant-scoped entity. The notes read for this document contain no CDC-specific guidance on tenant keys. Snowflake's paper covers analytical multi-tenancy only ([Design Patterns for Building Multi-Tenant Applications on Snowflake](https://www.snowflake.com/wp-content/uploads/2021/10/Design-Patterns-for-Building-Multi-Tenant-Applications-on-Snowflake.pdf) (2021 per URL and metadata; LAKE-13; vendor)).
- **Event producers:** key, event time, event ID, registered schema and optional-field discipline.

**Inference caveat.** The notes call key, event time, processing time, nullable-additive evolution, delete representation and idempotency key a common denominator that would meet all of the systems above simultaneously. That is a synthesis by the note authors, not a tested claim.

## 19. Conflict register

| # | Conflict | Sides | Context resolution |
|---|---|---|---|
| 1 | ELT default versus governance | Google, dbt recommend ELT ([BigQuery: Introduction to loading, transforming, and exporting data](https://docs.cloud.google.com/bigquery/docs/load-transform-export-intro) (n.d.; PIPE-19; vendor), [dbt Labs: Understanding ELT](https://www.getdbt.com/blog/extract-load-transform) (2023-09-06; PIPE-18; vendor)); dbt also lists compliance risk | ELT where raw zone can be governed; ETL or hybrid where data must be masked first |
| 2 | Schema-on-read versus schema-on-write | Bronze as string or VARIANT ([Medallion lakehouse architecture](https://docs.databricks.com/aws/en/lakehouse/medallion) (2026-10-29; LAKE-01; vendor)); Delta rejects mismatches ([Delta Lake: Table batch reads and writes](https://docs.delta.io/latest/delta-batch.html) (n.d.; PIPE-11)) | Depends on layer (section 3.3) |
| 3 | Lambda versus kappa | Critics only in the notes ([Questioning the Lambda Architecture](https://www.oreilly.com/radar/questioning-the-lambda-architecture/) (2014-07-02; PIPE-15), [The world beyond batch: Streaming 101](https://www.oreilly.com/radar/the-world-beyond-batch-streaming-101/) (2015-08-05; PIPE-16), [The Dataflow Model](https://www.vldb.org/pvldb/vol8/p1792-Akidau.pdf) (2015; PIPE-17)) | Prefer a single implementation; evidence is one-sided |
| 4 | Contract scope | Schema only ([Data Contract pattern](https://developer.confluent.io/patterns/event/data-contract/) (n.d.; PIPE-03; vendor)) versus full agreement ([Open Data Contract Standard (latest)](https://bitol-io.github.io/open-data-contract-standard/latest/) (n.d.; PIPE-20)) | Registry enforces compatibility; contract is broader |
| 5 | Delivery claims | Debezium: exactly once in normal operation, at least once on fault ([Debezium connector for PostgreSQL](https://debezium.io/documentation/reference/stable/connectors/postgresql.html) (n.d., Debezium 3.7; PIPE-06)) | Design for the failure case |
| 6 | Rename and drop across formats | Iceberg, Delta, Hudi (section 13.3) | Format-specific; only additive is portable |
| 7 | Tolerance for missing write columns | Delta sets null ([Delta Lake: Table batch reads and writes](https://docs.delta.io/latest/delta-batch.html) (n.d.; PIPE-11)); Hudi fails unless configured ([Apache Hudi: Schema Evolution](https://hudi.apache.org/docs/schema_evolution) (n.d., version 1.2.1; PIPE-12)) | Format-specific |
| 8 | Delta time-travel window | delta.io versus Databricks (section 13.3) | Verify on the platform in use |
| 9 | Task versus asset orchestration | [Airflow Best Practices](https://airflow.apache.org/docs/apache-airflow/stable/best-practices.html) (n.d., Airflow 3.4.0; PIPE-13) versus [Dagster Docs: Assets](https://dagster.io/docs/guides/build/assets) (n.d.; PIPE-14; vendor) | Both require re-runnability |
| 10 | Blocking versus non-blocking gates | See companion document | Tier by dataset criticality |
| 11 | ACID claims | Medallion guarantee ([Medallion lakehouse architecture](https://docs.databricks.com/aws/en/lakehouse/medallion) (2026-10-29; LAKE-01; vendor)) versus single-table scope ([Delta Lake: High-Performance ACID Table Storage over Cloud Object Stores](https://www.vldb.org/pvldb/vol13/p3411-armbrust.pdf) (2020; LAKE-08)) | Do not assume cross-layer atomicity |

## 20. Unverified sources and gaps

### 20.1 Used with caution

- **Kafka 1.1 Javadoc:** the single-session idempotence limit comes from a page returned by search and not opened (`https://kafka.apache.org/11/javadoc/org/apache/kafka/clients/producer/KafkaProducer.html`). Marked unverified at KAF-05.
- **Kafka documentation versions:** design content is from 4.3 and defaults from 4.2. The exact sentence about append order within a partition was not found on the 4.3 page.
- **Hudi promotion matrix:** reconstructed from page text in the notes.
- **Confluent compatibility tables:** per-format rules for primitives, enums, arrays and unions were not retrievable, and required-field cells were unreadable.
- **Confluent pattern bodies:** Idempotent Writer, Compacted Event Stream and Schema Validator were listed in the catalog page, but their bodies were not read.
- **Google, dbt:** the claim that neither discusses data contracts rests on the pages read.

### 20.2 Bibliographic anchors only

These books could not be read and support no claim here: *Fundamentals of Data Engineering* (PIPE-22, catalog url_verified=false), *Streaming Systems* (O'Reilly listing not opened), *Designing Data-Intensive Applications* (PIPE-21 is the author's site; CORRECTIONS.md records that chapter-level claims are unverified).

### 20.3 Gaps with no supporting evidence in the notes

- A backfill standard or Airflow's backfill mechanics.
- Late-arriving dimension placeholder strategies.
- `updated_at` or soft-delete prescriptions from any official source.
- Reconciliation checkpoint table designs.
- Delta type-widening and column-mapping details; Hudi ACID and time-travel; Iceberg snapshot details beyond isolation.
- Spark partition discovery guidance and checkpoint recovery detail.
- Prefect orchestration, Fivetran definitions, Streaming 102, Debezium `column.include.list` and transaction-metadata ordering.
- CDC connectors other than PostgreSQL, so MySQL, SQL Server and Oracle log-capture details are absent.
- Tenant-aware CDC patterns.
- Measured comparisons of Lambda and kappa, or of ELT and ETL total cost.
- Neutral (non-vendor) definitions of schema compatibility modes.
