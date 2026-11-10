# Data Modeling Approaches: Evidence Review

Research deliverable for the Database Schema Design and Data Engineering Standards Framework. Research phase only: this file contains no schemas and no framework implementation. Compiled 2026-11-08 from existing research notes (sources opened 2026-11-07 unless flagged). No new web research was done and no source outside the notes was added.

## 1. How to read this document

### 1.1 Evidence conventions

- **Citations** take the form [Title](URL) (date or n.d.) followed by the catalog ID in backticks. A citation with no backticked ID is in the notes but has no matching row in `resource_catalog.json`. To keep the file readable, a source is linked in full where first cited and is referred to afterwards by catalog ID alone, or by a short name where it has no ID.
- **Wording.** All source statements are paraphrase. Most web pages were read through a summarizing fetch tool, so their wording cannot be presented as verbatim. The only quotation marks in this file enclose text from FIPS 184, a PDF that the notes record as reliably extracted.
- **Flags.** VENDOR marks a source that sells a product in the category. VENDOR MARKETING marks promotional material. UNVERIFIED marks a source known only from a search snippet, a third party, or a page that could not be opened. INFERENCE marks a conclusion drawn in the notes or in this review rather than stated by a source.
- **Authority** uses the catalog scale where cited: A5 official body, vendor documentation or peer-reviewed paper; A4 recognized book, major engineering blog or originator's own channel; A3 reputable tool documentation or practitioner; A2 forum, lesser-known blog or preprint.

### 1.2 Principle labels

Each label reports the strength **inside the named approach**. It is not yet a requirement of the future framework.

| Label | Meaning |
|---|---|
| **MANDATORY** | The source states a rule or invariant, or the approach is not itself without it. Applies if you claim to follow that approach. |
| **RECOMMENDED** | The source presents a default or best practice that admits trade-offs. |
| **OPTIONAL/CONTEXTUAL** | The source presents a choice that depends on the situation. |

### 1.3 Workload scope tags

These tags are not interchangeable and every labelled principle carries at least one.

| Tag | Meaning |
|---|---|
| `[OLTP]` | Transactional system of record: short concurrent reads and writes, invariants enforced at write time. |
| `[DW-integration]` | Data warehouse integration layer: multi-source, granular, historical store, not for direct BI use. |
| `[DW-presentation]` | Data warehouse presentation layer: marts and star schemas. |
| `[OLAP]` | Analytical query workload on any platform, including ad hoc BI and aggregates. |
| `[Lakehouse]` | Analytical tables on object storage with a transactional metadata layer. |
| `[Streaming]` | Event transport and stream processing. |
| `[All]` | Stated by the source as independent of workload. |

### 1.4 These approaches are not the same kind of thing

Treating them as competing options is the most common category error. INFERENCE: the classification below is this review's synthesis of the sections that follow.

| Kind | Approaches | Decides |
|---|---|---|
| Relational design discipline | 3NF | Structure of base relations |
| Warehouse consumption model | Kimball, One Big Table | Shape of analytical tables |
| Warehouse integration model or architecture | Inmon CIF, Data Vault 2.0, Anchor | Shape and rules of the integrated historical store |
| Layering pattern, not a data model | Medallion | Number of hops and quality per hop |
| Boundary and consistency method | DDD | Where models and transactions begin and end |
| Application persistence and integration patterns | Event-driven modeling, event sourcing, CQRS | How state changes are recorded and read |
| Organizational operating model | Data Mesh | Who owns analytical data and how it is published |
| Metadata and integration design concept | Data Fabric | How integration and policy are automated |
| Non-relational database model | MongoDB document modeling | Document shape from access patterns |
| Cross-cutting time treatment | Temporal modeling | How time and change are represented |

## 2. Foundations shared by all approaches

These references frame the conceptual to logical to physical vocabulary. None of them chooses among the approaches.

- **ANSI/X3/SPARC three-schema architecture.** External, conceptual and internal schemas, from the 1975 interim report and the 1978 report in *Information Systems*: [The ANSI/X3/SPARC DBMS framework report](https://api.crossref.org/works/10.1016%2F0306-4379%2878%2990001-7) (1978-01) `GOV-25`. Only the Crossref bibliographic record was opened. The three-schema details and the statement that it never became a formal standard rest on Wikipedia, returned by search (UNVERIFIED). The 1975 text was not opened.
- **Chen entity-relationship model.** Proposed a model that captures real-world semantics, with a diagramming technique, and showed that other models can be derived from it: [The entity-relationship model: toward a unified view of data](https://dspace.mit.edu/handle/1721.1/47638) (1976) `GOV-26`; open copy at [NUS](https://www.comp.nus.edu.sg/~lingtw/papers/tods76.chen.pdf) (1976-03) `DES-03`. Chen also compared 3NF relations with ER relations and argued the latter have clearer semantics. The abstract is from a search snippet. The notes disagree on the NUS copy: note 08 calls it image-only, while note 10 reports text extraction.
- **IDEF1X (FIPS 184).** Issued 1993-12-21 as a US federal software standard for logical data modeling: [FIPS PUB 184](https://nvlpubs.nist.gov/nistpubs/Legacy/FIPS/fipspub184.pdf) (1993-12-21) `GOV-27`. One stated objective is "an application-independent view of data which can be validated by users and transformed into a physical database design". Withdrawal on 2008-09-02 and the successor ISO/IEC/IEEE 31320-2:2012 come from Wikipedia via search (UNVERIFIED).
- **DAMA-DMBOK.** A voluntary body of knowledge, not a standard. The 2024 revised second edition was a maintenance release that left the knowledge areas unchanged: [DAMA-DMBOK](https://dama.org/learning-resources/dama-data-management-body-of-knowledge-dmbok/) (n.d.) `GOV-01`; [DMBOK Revision](https://dama.org/dama-dmbok-revision/) (2024) `GOV-02`. Data Modeling and Design appears among its context diagrams, but no opened DAMA page describes that chapter. The widely repeated summary of its modeling schemes is UNVERIFIED.

Principles:

- **RECOMMENDED** `[All]` Separate external, conceptual and internal views, and progress from conceptual to logical to physical. Grounded in ANSI/SPARC and FIPS 184; never a de jure requirement today.
- **OPTIONAL/CONTEXTUAL** `[All]` IDEF1X notation. It was MANDATORY for US federal agencies under FIPS 184, with waivers, until withdrawal.
- **OPTIONAL/CONTEXTUAL** `[All]` DMBOK knowledge-area structure as an organizing vocabulary.

## 3. Kimball dimensional modeling

**Origin and authority.** Ralph Kimball introduced the approach in the 1996 *Data Warehouse Toolkit*. The Kimball Group's consolidated list of techniques is drawn from the 2013 third edition: [Kimball Dimensional Modeling Techniques](https://www.kimballgroup.com/wp-content/uploads/2013/08/2013.09-Kimball-Dimensional-Modeling-Techniques11.pdf) (2013) `DWM-01`, A5; [The 10 Essential Rules of Dimensional Modeling](https://www.kimballgroup.com/2009/05/the-10-essential-rules-of-dimensional-modeling/) (2009-05-29) `DWM-02`, A5; [The Data Warehouse Toolkit, 3rd Edition](https://www.wiley.com/en-us/The+Data+Warehouse+Toolkit%3A+The+Definitive+Guide+to+Dimensional+Modeling%2C+3rd+Edition-p-9781118530801) (2013-07) `DWM-03`. Scope is the analytical presentation layer only. It is not an OLTP method.

**Core rules** (all from `DWM-01` and `DWM-02` unless noted)

- **MANDATORY** `[DW-presentation]` Follow the four-step sequence: select the business process, declare the grain, identify dimensions, identify facts.
- **MANDATORY** `[DW-presentation]` Declare grain before choosing dimensions or facts. Each grain is a separate physical table and grains are never mixed in one fact table.
- **MANDATORY** `[DW-presentation]` Fact-table foreign keys are never null. Unknown or not-applicable cases point to a default dimension row.
- **MANDATORY** `[DW-presentation]` Each dimension has an anonymous, sequentially assigned integer surrogate key rather than a natural key. The date dimension is exempt.
- **MANDATORY** `[DW-presentation]` Every fact table has an associated date dimension.
- **MANDATORY** `[DW-presentation]` Enterprise integration uses conformed dimensions, planned on the bus matrix, with business processes as rows and dimensions as columns.
- **RECOMMENDED** `[DW-presentation]` Load atomic grain, because summary grains presuppose the questions. Store additive components and compute ratios in the BI layer.
- **RECOMMENDED** `[DW-presentation]` Flatten fixed-depth hierarchies and avoid snowflaking.
- **RECOMMENDED** `[DW-presentation]` Replace null dimension attributes with descriptive defaults such as Unknown.
- **RECOMMENDED** `[DW-presentation]` Type 2 dimensions carry at least effective date, expiration date and current-row indicator.
- **OPTIONAL/CONTEXTUAL** `[DW-presentation]` Fact-table surrogate keys, outriggers (sparingly), junk dimensions, bridge tables for multivalued dimensions and ragged hierarchies, and SCD Types 3 and 5 to 7.

Fact table types are transaction, periodic snapshot and accumulating snapshot, with factless tables for events and coverage. Accumulating snapshots are the one type that is routinely updated in place.

**Workload fit.** Stable business processes consumed through BI tools. Oracle's guide states that most data warehouses use a dimensional model and that many BI tools expect a star: [Oracle 21c Data Warehousing Guide, Logical Design](https://docs.oracle.com/en/database/oracle/oracle-database/21/dwhsg/data-warehouse-logical-design.html) (n.d.) `DWM-14`. Not for `[OLTP]` write paths.

**Strengths.** Simple one-join-per-dimension queries (`DWM-14`). Extensible without breaking queries when adding facts, dimensions or attributes consistent with the grain (`DWM-01`). The bus architecture is platform independent (`DWM-01`). Still described as among the most widely adopted analytics techniques: [Building a Kimball dimensional model with dbt](https://docs.getdbt.com/blog/kimball-dimensional-model) (2023-04-20) `DWM-21`.

**Weaknesses.** The grain is a binding contract, and a common criticism is less analytical flexibility than 3NF (`DWM-14`). Type 1 overwrites destroy history (`DWM-01`). Inmon argues that conformed dimensions cover only some attributes and that copying data does not reconcile it: [A Tale of Two Architectures](https://williaminmon.substack.com/p/a-tale-of-two-architectures-kimball) (2025-12-23) `DWM-06`. Cloud-era critics find surrogate keys and SCD machinery costly: [The Rise of the Data Engineer](https://www.freecodecamp.org/news/the-rise-of-the-data-engineer-91be18f1e603/) (2017-01-20) `DWM-23`.

**ERP, financial and SaaS suitability.** High for financial and ERP **reporting**, not for ledgers of record. INFERENCE: periodic snapshots fit balances, since Kimball classes balances as semi-additive and not additive across time. Note 06's matrix asserts accounting, procurement and invoicing case studies from the Wiley page, but the same note says that page does not expose its contents, so that claim is not supported here. For SaaS analytics, Snowflake's white paper reports that data model shape affects clustering choices, and recommends clustering shared tables by tenant and date: [Design Patterns for Building Multi-Tenant Applications on Snowflake](https://www.snowflake.com/wp-content/uploads/2021/10/Design-Patterns-for-Building-Multi-Tenant-Applications-on-Snowflake.pdf) (2021) `LAKE-13`, VENDOR.

**Combines with.** Sits above Inmon or Data Vault as the mart layer (`DWM-06`, `DWM-14`). Gold-layer shape in Medallion: [Databricks data warehousing modeling techniques](https://www.databricks.com/blog/2022/06/24/data-warehousing-modeling-techniques-and-their-implementation-on-the-databricks-lakehouse-platform.html) (2022-06-24) `LAKE-05`, VENDOR. OBT can be derived from it. SCD types are the warehouse rendering of temporal modeling (Section 16). A data product can publish a star as an output (INFERENCE).

## 4. Inmon Corporate Information Factory

**Origin and authority.** W. H. Inmon, *Building the Data Warehouse*, 4th edition 2005: [Wiley record](https://www.wiley.com/en-us/Building+the+Data+Warehouse%2C+4th+Edition-p-9780764599446) (2005-10) `DWM-05`. The notes' best primary text is his own restatement in `DWM-06` (2025-12-23), A4. The *Corporate Information Factory* book and the text of his lakehouse books were not read. Lakehouse titles are known from a publisher listing: [Bill Inmon's Data Lakehouse Collection](https://technicspub.com/data-lakehouse-collection/) (n.d.) `DWM-07`.

**Core rules** (from `DWM-06`)

- **MANDATORY** `[DW-integration]` The warehouse is subject-oriented, integrated, time-variant and non-volatile.
- **MANDATORY** `[DW-integration]` It holds granular, historical, integrated data and is the only source for dependent data marts.
- **RECOMMENDED** `[DW-integration]` Physicalize the warehouse in 3NF. See Section 18.2: the Kimball Group calls 3NF a requirement of CIF, while Inmon's 2025 text stresses integration and granularity. The RECOMMENDED label is the notes' INFERENCE.
- **RECOMMENDED** `[DW-integration]` Use master data golden records to reconcile identity.
- **RECOMMENDED** `[DW-presentation]` Feed star-schema marts from the central integrated warehouse.
- **OPTIONAL/CONTEXTUAL** `[Lakehouse]` Lakehouse incarnation and DW 2.0 extensions (`DWM-07`).

**Workload fit.** Enterprise integration of many sources where one reconciled version is the priority. Not a BI access layer and not an `[OLTP]` schema.

**Strengths.** Single integrated foundation, with history preserved at grain. Inmon names the single version of the truth as the architecture's most important feature (`DWM-06`).

**Weaknesses.** Inmon himself says integration is slow and laborious, making CIF a long-term effort (`DWM-06`). The Kimball Group sees added cost and delay from storing atomic data twice: [Differences of Opinion](https://www.kimballgroup.com/2004/03/differences-of-opinion/) (2004-03-03) `DWM-04`.

**ERP, financial and SaaS suitability.** Strong for consolidating several ERPs or subsidiaries into one reconciled store (INFERENCE from the integration and master-data emphasis). Weak for a single-product SaaS with one source, where the integration layer has little to reconcile (INFERENCE).

**Combines with.** Star marts on top, the hybrid accepted by Inmon, the Kimball Group and Oracle. In Medallion terms it is a Silver-layer model (`LAKE-05`, INFERENCE in the notes for the Inmon EDW). Master data work supports it directly.

## 5. Data Vault 2.0

**Origin and authority.** Daniel Linstedt, with the Data Vault Alliance as standards body and the book *Building a Scalable Data Warehouse with Data Vault 2.0* by Linstedt and Olschimke: [Elsevier record](https://shop.elsevier.com/books/building-a-scalable-data-warehouse-with-data-vault-2-0/linstedt/978-0-12-802510-9) (2015-09) `DWM-10`. Governing text: [How To: Test an Idea for Data Vault Standards](https://datavaultalliance.com/news/dv/dv-standards/how-to-propose-dv-standards) (2021-09-30, modified 2026-01-23) `DWM-09`, A5. No consolidated public standards page could be opened. The Alliance and Scalefree both sell training or services in this field, so treat their claims of value as interested (VENDOR for value claims).

**Core rules**

- **MANDATORY** `[DW-integration]` Hub, Link and Satellite base definitions do not change. New object types become extended objects (`DWM-09`).
- **MANDATORY** `[DW-integration]` Standards must be repeatable, pattern-based, non-conditional, restartable, auditable, and work in batch and real time (`DWM-09`).
- **MANDATORY** `[DW-integration]` Every Hub, Link and Satellite row carries load date and record source. Load date is arrival time, not event time: [Data Vault Glossary](https://www.scalefree.com/blog/data-vault/data-vault-glossary-hub-link-satellite-business-vault-and-more/) (2026-05-04) `DWM-11`.
- **MANDATORY** `[DW-integration]` The Raw Vault stores unmodified source data with no business rules (`DWM-11`, definitional). Databricks states this more softly, as not typically applied: [Prescriptive Guidance for a Data Vault on Databricks](https://www.databricks.com/blog/2022/06/24/prescriptive-guidance-for-implementing-a-data-vault-model-on-the-databricks-lakehouse-platform.html) (2022-06-24), companion to `LAKE-05`, VENDOR.
- **RECOMMENDED** (strong) `[DW-integration]` Consumers use Information Marts, not the vault. Linstedt's wording is should-not with a named exception for data scientists: [Get Data from a Vault Easy](https://datavaultalliance.com/engineering/getting-data-out-of-a-data-vault-is-a-lot-easier-than-some-people-think/) (2022-08-29, modified 2026-01-23) `DWM-08`. Note 06 labels this MANDATORY, which exceeds its own label definition.
- **RECOMMENDED** `[DW-integration]` Hash keys generated in staging for lookup-free parallel loads: [Data Vault 2.0 differences with 1.0](https://roelantvos.com/blog/?p=1063) (2014-05-12) `DWM-12`; [Hash Keys in Data Vault](https://www.scalefree.com/blog/data-vault/hash-keys-in-the-data-vault/) (2017-04-28, updated 2026-05-11). Standards must also accommodate sequences and natural keys (`DWM-09`), so hashing is a default and not part of the definition.
- **RECOMMENDED** `[DW-integration]` Insert-only loads with no end-dating in raw structures. The Alliance course calls this a best practice and not a standard (UNVERIFIED: [DV101 course snippet](https://learn.datavaultalliance.com/cs/dv101-baseline-hands-on/ls/introduction-to-this-course/), n.d., search only).
- **RECOMMENDED** `[DW-integration]` Automate patterns. Implementation criteria expect at least 98 percent of cases to be automatable (`DWM-09`).
- **OPTIONAL/CONTEXTUAL** `[DW-integration]` Business Vault, effectivity satellites, PIT and bridge helpers. `[DW-presentation]` Virtualized marts.

**Workload fit.** Many volatile sources, acquisitions, and a need to reload or re-derive marts from unmodified history. Never `[OLTP]`.

**Strengths.** Extensibility was the top cited driver at 53 percent in a survey of 238 practitioners: [BARC/Eckerson adoption trends](https://barc.com/infographic-data-warehouse-and-data-vault-adoption/) (2023-04-27) `DWM-13`. Row-level source and load lineage is the auditability mechanism (`DWM-11`).

**Weaknesses.** Cited drawbacks were skills and training 48 percent, implementation complexity 35 percent, query performance 32 percent, design complexity 29 percent and multiple versions of data 29 percent. Only 31 percent said their implementation fully aligned with standards, and usage trails 3NF and star schema (`DWM-13`). Practitioners report messy implementations: [dbt Discourse thread](https://discourse.getdbt.com/t/is-kimball-dimensional-modeling-still-relevant-in-a-modern-data-warehouse/225) (2019-2022) `DWM-20`, A2. No controlled independent benchmark of query performance against star schemas was found.

**ERP, financial and SaaS suitability.** High for audited, multi-ERP integration, with marts still required. The source for fit with acquisitions is a consultancy listing: [Scalefree Data Vault blog listing](https://www.scalefree.com/data-vault/) (n.d.), VENDOR. Probably excessive for a single-source SaaS analytics stack, given the skills and automation burden (INFERENCE). A business-key collision code exists for keys that mean different things across sources (Scalefree 2017), which is relevant to multi-company ERP data (INFERENCE).

**Combines with.** Kimball marts are effectively required (`DWM-08`). Staging in Bronze, Raw and Business Vault in Silver, PIT and dimensional presentation in Gold (Databricks DV guidance). Satellites provide an insert-only form of transaction-time-style history keyed by load date (INFERENCE; load date is arrival time per `DWM-11`).

## 6. Third Normal Form

Two scopes exist and must be kept apart.

**Origin and authority.** Codd defined the relational model and normalization: [A Relational Model of Data for Large Shared Data Banks](https://www.engineering.upenn.edu/~zives/03f/cis550/codd.pdf) (1970-06) `DES-01`, A5. 2NF and 3NF come from Codd's 1971 paper, known here only bibliographically: [Further Normalization](https://www.vldb.org/dblp/db/indices/a-tree/c/Codd:E=_F=.html) (1971) `LIT-02`, a DBLP record only, flagged weak in the corrections. Plain-language definitions: [A Simple Guide to Five Normal Forms](https://www.bkent.net/Doc/simple5.htm) (1983-02) `DES-02`, A5. Warehouse use: `DWM-14` (A5) and [Oracle9i Schema Modeling Techniques](https://docs.oracle.com/cd/A97630_01/server.920/a96520/schemas.htm) (n.d.), A5; [Teradata Retail Data Model](https://www.teradata.com/industries/retail/retail-data-model) (n.d.) `DWM-15`, VENDOR.

**Core rules**

- **MANDATORY** `[OLTP]` Within the relational model, first normal form: simple domains and no repeating groups (`DES-01`). Note 10 extends this to all workloads. Lakehouse Bronze layers and MongoDB embedding openly depart from it, so it is scoped here to relational base tables.
- **RECOMMENDED** (strong default) `[OLTP]` Bring base tables whose non-key fields are updated to 3NF. Non-key fields depend only on the key, which removes update, insertion and deletion anomalies (`DES-02`). Kent himself says full normalization is not required when performance requirements justify stopping short. Note 10 labels this MANDATORY as an inference, which is stronger than its source.
- **RECOMMENDED** `[OLTP]` Check 4NF and 5NF where a table holds independent multivalued facts (`DES-02`).
- **OPTIONAL/CONTEXTUAL** `[OLAP]` `[DW-presentation]` Denormalize when the workload is read-dominant, the redundancy has one controlled write path and the dependency is documented (INFERENCE in note 10, grounded in Kent's caveat).
- **OPTIONAL/CONTEXTUAL** `[DW-integration]` 3NF as the warehouse foundation layer. Oracle says the choice rests on project requirements and preferences (Oracle9i) and describes 3NF as neutral with respect to applications and common in large data-loading environments that feed marts.
- **RECOMMENDED** `[DW-presentation]` Pair a 3NF foundation with a star access layer (`DWM-14`). Oracle accepts sensible denormalization in 3NF warehouses through views or slightly denormalized tables.

**Workload fit.** Default for `[OLTP]` systems of record. Viable for `[DW-integration]`. Poor as a direct `[OLAP]` access layer, since full-scale enterprise models commonly exceed a thousand tables and need complex multi-join queries (`DWM-14`).

**Strengths.** Minimizes redundancy and anomalies, and extends with relative ease (`DWM-14`). Application-neutral. Enforced by mature constraint mechanisms on relational engines.

**Weaknesses.** Retrieval is penalized (`DES-02`). On Databricks and Snowflake standard tables, primary, unique and foreign keys are informational, so integrity moves to pipelines: [Databricks constraints](https://docs.databricks.com/aws/en/tables/constraints) (2026-10-29) `LAKE-02`; [Snowflake constraints overview](https://docs.snowflake.com/en/sql-reference/constraints-overview) (n.d.). Teradata's product page supports the 3NF-with-dimensional-access pattern, but no Teradata documentation stating a normalized preference was retrievable.

**ERP, financial and SaaS suitability.** The strongest default for ERP and financial `[OLTP]` cores, where anomalies in master and transactional data are costly (INFERENCE from Kent's scope). Ledger invariants add rules beyond normalization: entries balance per currency and posted entries are never updated, with corrections made by new entries: [Patterns for Accounting](https://martinfowler.com/eaaDev/AccountingNarrative.html) (2006-01-24) `TEN-40`; [Modern Treasury Ledgers Guarantees](https://docs.moderntreasury.com/ledgers/docs/ledgers-guarantees) (n.d.) `TEN-41`, VENDOR; [Books: immutable double-entry accounting](https://developer.squareup.com/blog/books-an-immutable-double-entry-accounting-database-service) (2019-10-16) `TEN-42`; [Stripe Ledger](https://stripe.dev/blog/ledger-stripe-system-for-tracking-and-validating-money-movement) (2024-02-16) `TEN-43`. For SaaS, note 14 labels tenant identifiers in primary, unique and foreign keys RECOMMENDED for sharded or distributed designs.

**Combines with.** DDD aggregates shape which 3NF tables form one transaction (`[OLTP]`). Star schemas derive from it in warehouses. Silver in Medallion (`LAKE-05`). Application-time and system-time periods extend it (Section 16).

## 7. One Big Table

**Origin and authority.** No originator or governing specification exists in the notes. It is a practitioner pattern. Main evidence: [Star schema vs. OBT](https://fivetran.com/blog/star-schema-vs-obt) (2022-08-16) `DWM-22`, VENDOR, with its test setup published; `DWM-21` (A3); `DWM-20` (A2); `DWM-23` (A3).

**Core rules.** No source states any MANDATORY rule.

- **RECOMMENDED** `[OLAP]` `[DW-presentation]` Build a star in transformation and derive the wide table for end users (`DWM-22`).
- **RECOMMENDED** `[DW-presentation]` Use OBT when the BI tool has no semantic layer that supports relationships (`DWM-21`).
- **RECOMMENDED** `[OLAP]` Keep one grain per table, since joining mismatched grains risks gaps and duplicates (`DWM-20`, A2). INFERENCE: this carries Kimball's grain rule across.
- **OPTIONAL/CONTEXTUAL** `[Lakehouse]` Fully denormalized Gold tables for data-science feature engineering (`LAKE-05`).
- **OPTIONAL/CONTEXTUAL** `[OLAP]` Degree of denormalization. Snowflake says there is no universal guideline and extensive testing is needed: [Snowflake performance guide](https://www.snowflake.com/en/developers/guides/performance/) (n.d.) `LAKE-14`. dbt reverses its advice when its Semantic Layer is used, preferring normalized marts: [dbt Marts guide](https://docs.getdbt.com/best-practices/how-we-structure/4-marts) (2026-07-07).

**Workload fit.** Low-latency dashboards, small teams, single-subject analysis. Not `[OLTP]` and not a `[DW-integration]` layer.

**Strengths.** Fivetran's TPC-DS-derived test found wide tables faster: about 25 to 30 percent on Redshift, about 25 percent on Snowflake and an average 49 percent on BigQuery, with the star showing more variance on BigQuery (`DWM-22`).

**Weaknesses.** Results were not uniform: on Snowflake the star won three queries, and only one schema shape and vendor-run test exist (`DWM-22`). No peer-reviewed benchmark was found. Storage rises. **Evidence caution:** note 06 summarizes this as tripled storage, yet its detailed figures are a store_sales table of about 29.8 GB against an OBT of about 60.3 GB, with disk moving from a bit over 30 GB to over 90 GB. INFERENCE: the table-level ratio is about 2x and the 3x figure may count both tables on disk. Snowflake warns that very wide tables raise compile time (`LAKE-14`). Forum reports say a single big table hits a wall at scale and is hard to navigate (`DWM-20`).

**ERP, financial and SaaS suitability.** Low for multi-grain ledgers and for any record of authority. Acceptable as a derived SaaS customer-facing reporting table at one grain (INFERENCE).

**Combines with.** Derived from Kimball or an integration model. Gold in Medallion. dbt's entity-grained marts lean this way but are one entity at one grain, not a fact pre-joined with all dimensions (note 04, INFERENCE).

## 8. Anchor Modeling

**Origin and authority.** Rönnbäck, Regardt, Bergholtz, Johannesson and Wohed: [Anchor Modeling, DKE preprint](https://www.anchormodeling.com/wp-content/uploads/2011/05/Anchor-Modeling.pdf) (2010-10-05) `DWM-16`, A5; [publications page](https://www.anchormodeling.com/publications/) (2010) `LIT-48`. A best-paper award at ER 2009 and acceptance by *Data and Knowledge Engineering* come from an unopened search result (UNVERIFIED). The current site is the author's blog: [anchormodeling.com](https://www.anchormodeling.com/) (2022), A4.

**Core rules** (from `DWM-16`)

- **MANDATORY** `[DW-integration]` Changes require only extensions, never modifications, so earlier schema versions remain subsets of the current schema.
- **MANDATORY** `[DW-integration]` Zero update strategy: loads only insert.
- **MANDATORY** `[DW-integration]` Declare primary and foreign keys, since table elimination depends on them.
- **MANDATORY** `[DW-integration]` Build from four constructs: anchors, knots, attributes and ties.
- **RECOMMENDED** `[DW-integration]` Historize attributes and ties only when versioning matters. Prefer several smaller ties when roles may be temporarily unknown.
- **OPTIONAL/CONTEXTUAL** `[DW-integration]` Transitional modeling and posits, per the author's later blog posts.

**Workload fit.** Volatile schemas with heavy historization and sparse attributes. Often reaches 6NF. Not `[OLTP]` guidance.

**Strengths.** Extreme non-destructive evolution. The paper claims no null values and fast retrieval through optimizer table elimination, with lab results better than traditional techniques under certain conditions (`DWM-16`). No row locking because there are no updates (`DWM-16`).

**Weaknesses.** Very high table counts and reliance on optimizer support. Evidence is largely author-published. The largest warehouse cited was close to one terabyte (`DWM-16`). Author timings from 2022 caution that workarounds may have skewed results (anchormodeling.com). Not measured in the BARC survey. Note 06's matrix mentions bitemporal variants without a detailed finding, so that is not relied on here.

**ERP, financial and SaaS suitability.** Self-reported uses in insurance, logistics and retail (`DWM-16`). Note 06's matrix additionally cites CPM consolidation, which its findings do not substantiate. Specialist option only; thin tooling makes it risky as an enterprise default (INFERENCE).

**Combines with.** Silver-layer model in Medallion (INFERENCE). Needs a presentation layer or views for BI (INFERENCE). Natural kin to Data Vault, with insert-only loading and non-destructive extension.

## 9. Medallion architecture

**A layering pattern, not a data model.** Databricks defines it as a data design pattern that organizes data into layers denoting quality. The documentation names neither Kimball nor Data Vault and does not itself say it is not a data model. That conclusion follows from its content.

**Origin and authority.** [Medallion lakehouse architecture](https://docs.databricks.com/aws/en/lakehouse/medallion) (2026-10-29) `LAKE-01`, A5, VENDOR. The notes attribute the term to Databricks and hold no equivalent from other vendors, although the catalog lists a Microsoft Fabric treatment (`CLOUD-21`) that was outside this review's notes. Status: recommended best practice and not a requirement per `LAKE-01`, and a reference architecture rather than a mandatory structure per [Databricks Lakehouse Data Modeling: Myths, Truths, and Best Practices](https://www.databricks.com/blog/databricks-lakehouse-data-modeling-myths-truths-and-best-practices) (2025-12-15) `LAKE-06`.

**Core rules.** No source states any MANDATORY rule.

- **RECOMMENDED** `[Lakehouse]` Bronze holds raw, appended data in near-original form, stores most fields as string, VARIANT or binary, and is not for analysts (`LAKE-01`).
- **RECOMMENDED** `[Lakehouse]` Silver holds validated, deduplicated, non-aggregated data and is not written directly from ingestion (`LAKE-01`).
- **RECOMMENDED** `[Lakehouse]` `[OLAP]` Gold holds refined, business-aligned datasets, typically modeled dimensionally (`LAKE-01`).
- **OPTIONAL/CONTEXTUAL** `[Lakehouse]` Add or remove layers (`LAKE-06`).

**Workload fit.** Lakehouse pipelines only. Says nothing about `[OLTP]`.

**Strengths.** Clear quality contract per hop. Bronze enables reprocessing and audit. Separates ingestion typing from business modeling.

**Weaknesses.** Choosing it decides no table shapes. Extra hops add processing and storage (INFERENCE; the page's cost table compares refresh modes, not hop counts). The documentation's ACID claim concerns Delta transactions and should not be read as cross-layer atomicity, a limit the page does not qualify (note 04). Delta's paper limited transactions to one table: [Delta Lake paper](https://www.vldb.org/pvldb/vol13/p3411-armbrust.pdf) (2020). Multi-table transactions were in private preview in December 2025 (`LAKE-06`), with current status unverified.

**ERP, financial and SaaS suitability.** Neutral. Useful as a hop convention for finance analytics, provided that retention of raw data respects erasure and records rules (INFERENCE).

**Combines with.** Bronze uses source shapes; Silver takes 3NF-like or Data Vault models; Gold takes Kimball, Inmon-style marts or denormalized tables (`LAKE-05`). Data Mesh can expose Gold or Silver outputs as data products (INFERENCE).

## 10. Domain-Driven Design

**Origin and authority.** Eric Evans. The book is known only through a publisher record: [Domain-Driven Design](https://www.informit.com/store/domain-driven-design-tackling-complexity-in-the-heart-9780321125217) (2003-08-20) `LIT-69`. Primary text used: [DDD Reference](https://www.domainlanguage.com/wp-content/uploads/2016/05/DDD_Reference_2015-03.pdf) (2015-03) `ARCH-01`, A5. Also: [Effective Aggregate Design](https://www.dddcommunity.org/library/vernon_2011/) (2011) `ARCH-03`, A4; [Fowler: BoundedContext](https://martinfowler.com/bliki/BoundedContext.html) (2014-01-15) and [DDD_Aggregate](https://martinfowler.com/bliki/DDD_Aggregate.html) (2013-04-23) `ARCH-02`, A4; [Data sovereignty per microservice](https://learn.microsoft.com/en-us/dotnet/architecture/microservices/architect-microservice-container-applications/data-sovereignty-per-microservice) (2018, updated 2022) `ARCH-04`, A5; [Database per service](https://microservices.io/patterns/data/database-per-service.html) (n.d.) `ARCH-05`, A3. DDD is a boundary method, not a storage model.

**Core rules**

- **MANDATORY** `[All]` Explicitly bound each model, including in physical manifestations that Evans names as code bases and database schemas (`ARCH-01`).
- **MANDATORY** `[All]` Use the ubiquitous language within a context, including in code. A language change is a model change (`ARCH-01`).
- **MANDATORY** `[OLTP]` External objects reference only the aggregate root. Aggregate boundaries govern transactions and distribution: synchronous inside, asynchronous across (`ARCH-01`).
- **MANDATORY** `[OLTP]` Value objects are immutable and have no identity. Entities are defined by identity (`ARCH-01`).
- **RECOMMENDED** (strong default) `[OLTP]` Modify one aggregate instance per transaction. Vernon calls it a rule of thumb and lists reasons to break it (`ARCH-03`).
- **RECOMMENDED** `[OLTP]` Keep aggregates small, reference others by identity, use eventual consistency outside the boundary (`ARCH-03`).
- **RECOMMENDED** `[OLTP]` Start with private tables or schema per service, the lowest-overhead options (`ARCH-05`).
- **RECOMMENDED** (INFERENCE) `[OLTP]` No foreign keys across context boundaries, with references held as identifiers. Note 07 marks this MANDATORY, but it is derived and no source states it. Evans's Shared Kernel explicitly allows a small shared database design, and modular monoliths retain cross-table ACID (`ARCH-04`).
- **OPTIONAL/CONTEXTUAL** `[OLTP]` Shared Kernel kept small and changed only by consultation; database server per service, driven by throughput or storage type (`ARCH-01`, `ARCH-05`).

Context-map relationships work as a decision table for shared data (INFERENCE): Shared Kernel, Customer/Supplier, Conformist, Anticorruption Layer, Open-host Service, Published Language, Separate Ways, Partnership (`ARCH-01`).

**Workload fit.** Complex `[OLTP]` domains. The bounded-context idea transfers to analytics through Data Mesh. Aggregates do not govern `[OLAP]`.

**Strengths.** Gives a principled answer to schema ownership and transaction scope. Allows one business thing to carry different names in different contexts (`ARCH-04`).

**Weaknesses.** Reference-by-identity can make composing views harder, which pushes toward CQRS (`ARCH-03`). Saga and outbox complexity follows once boundaries become physical: saga has no automatic rollback and lacks isolation: [Pattern: Saga](https://microservices.io/patterns/data/saga.html) (n.d.) `ARCH-06`. Sources give no quantitative threshold for separating servers.

**ERP, financial and SaaS suitability.** Note 07 recommends a modular-monolith ERP with one server, schema per context and per-context database users, promoting only when needed (INFERENCE from `ARCH-05`). Shared reference data fits Shared Kernel governance. The DDD and mesh sources do not prescribe multi-tenant layout. Vernon's examples carry a tenant identifier in aggregates but specify no storage design.

**Combines with.** CQRS reads (`ARCH-03`). Event sourcing and domain events (`ARCH-01`). Data Mesh source-aligned products (`ARCH-14`). Each context can use 3NF internally (INFERENCE).

## 11. Event-driven modeling and event sourcing

These are distinct. Fowler separates event notification, event-carried state transfer, event sourcing and CQRS, and says each is good only on the right terrain: [What do you mean by Event-Driven?](https://martinfowler.com/articles/201701-event-driven.html) (2017-02-07) `ARCH-08`, A4. All four are **OPTIONAL/CONTEXTUAL** `[All]` as patterns.

**Origin and authority.** The earliest pattern text in the notes is [Fowler: Event Sourcing](https://martinfowler.com/eaaDev/EventSourcing.html) (2005-12-12) `ARCH-09`. The notes do not establish who originated it. Others: [Microsoft Event Sourcing pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/event-sourcing) (2026-03-27, updated 2026-09-25) `ARCH-10`, A5; [Pattern: Event sourcing](https://microservices.io/patterns/data/event-sourcing.html) (n.d.), grouped under `ARCH-07`; Young's versioning views via [InfoQ's report](https://www.infoq.com/news/2017/07/versioning-event-sourcing) (2017-07-17) `ARCH-13`, A3, with his book seen only as a table of contents. Envelope and contract specifications: [CloudEvents](https://github.com/cloudevents/spec/blob/main/cloudevents/spec.md) (1.0.3-wip, n.d.) `ARCH-11`; [AsyncAPI 3.0.0](https://www.asyncapi.com/docs/reference/specification/v3.0.0) (n.d.) `ARCH-12`.

**Core rules**

- **MANDATORY** `[OLTP]` Within event sourcing: never update stored events, and undo only through compensating events (`ARCH-10`).
- **MANDATORY** `[Streaming]` With at-least-once delivery, consumers must be idempotent, for example through a processed-message record written in the business transaction: [Pattern: Idempotent Consumer](https://microservices.io/patterns/communication-style/idempotent-consumer.html) (n.d.), grouped under `ARCH-06`.
- **MANDATORY** `[Streaming]` If claiming CloudEvents conformance: required `id`, `source`, `specversion`, `type`, with `source` plus `id` unique per event (`ARCH-11`).
- **RECOMMENDED** `[OLTP]` `[Streaming]` Use a transactional outbox when a database update and a message publish must be atomic: [Pattern: Transactional outbox](https://microservices.io/patterns/data/transactional-outbox.html) (n.d.) `TXN-18`.
- **RECOMMENDED** `[OLTP]` One stream per entity, optimistic concurrency per stream, snapshots only as an optimization (`ARCH-10`).
- **RECOMMENDED** `[OLTP]` Record business intent rather than resulting state (`ARCH-10`). Evans's domain events carry occurrence time and often entry time (`ARCH-01`).
- **RECOMMENDED** `[OLTP]` `[Streaming]` Evolve events by tolerant reading, versioning or upcasting. In-place migration is a last resort (`ARCH-10`). Young prefers weak schemas and argues against altering events (`ARCH-13`).
- **RECOMMENDED** `[OLTP]` Keep personal data outside the event store and reference it, or use crypto-shredding (`ARCH-10`).
- **OPTIONAL/CONTEXTUAL** `[OLTP]` Event sourcing itself. Microsoft says traditional data management is sufficient for most systems, and to apply it selectively (`ARCH-10`).

**Workload fit.** Audit-heavy and intent-rich `[OLTP]` subdomains. `[Streaming]` integration. Microsoft advises against it for simple CRUD, prototypes, mostly static reference data, and teams without event-driven experience (`ARCH-10`). Not a `[DW-presentation]` model, though events can feed one.

**Strengths.** Strong audit capability and state reconstruction at any point (`ARCH-08`, `ARCH-09`). Natural partitioning by entity (`ARCH-10`).

**Weaknesses.** Costly to migrate to or from (`ARCH-10`). The store is hard to query and needs CQRS: microservices.io event sourcing page. Replay is hard when results depend on external systems (`ARCH-08`). Event notification flows can be hard to see in program text (`ARCH-08`). Event-carried state transfer creates many copies (`ARCH-08`).

**ERP, financial and SaaS suitability.** Microsoft names payment ledgers and order processing as selective candidates, and user profiles and configuration as CRUD cases (`ARCH-10`). Note 07 is internally inconsistent here, using RECOMMENDED in one inference and OPTIONAL/CONTEXTUAL in another. OPTIONAL/CONTEXTUAL is used here as it matches the source. **Do not conflate ledger immutability with event sourcing:** append-only, balanced, correct-by-new-entry ledgers are MANDATORY `[OLTP]` for ledgers in note 14's synthesis (`TEN-40` to `TEN-43`), and these do not require an event-sourced application. Fowler observes that accounting data uses event sourcing when derived from domain events, even if the rest of the application does not (`TEN-40`). Note 14 says no fetched source discusses crypto-shredding, which conflicts with note 07's report of the Microsoft page; the Microsoft citation is used here.

**Combines with.** CQRS is described as necessary for event-sourced systems: [Pattern: CQRS](https://microservices.io/patterns/data/cqrs.html) (n.d.) `ARCH-07`. Aggregates define streams (INFERENCE). Bronze can ingest events (INFERENCE). Bitemporal concepts parallel occurrence and recording times (INFERENCE). Data contracts govern published events (Section 13).

## 12. CQRS

**Origin and authority.** The notes do not establish its originator. Sources: [Microsoft CQRS pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/cqrs) (2025-02-20, updated 2026-10-11) `ARCH-10`, also `PERF-56` (the catalog rates the page A4 under one ID and A5 under the other); `ARCH-07`; `ARCH-08`.

**Core rules**

- **MANDATORY** `[OLTP]` None as a general rule. If paired with event sourcing, the event store is the write model and source of truth (`ARCH-10`).
- **RECOMMENDED** `[OLTP]` Use a transactional outbox and idempotent consumers to keep read models current (Microsoft CQRS page).
- **OPTIONAL/CONTEXTUAL** `[OLTP]` Separate models over a single data store, the foundational level, which needs no second database (Microsoft CQRS page).
- **OPTIONAL/CONTEXTUAL** `[OLTP]` `[OLAP]` Separate read and write stores, including a denormalized view store (`ARCH-07`).

**Workload fit.** High-contrast read and write needs and cross-context joins. Microsoft advises against it for simple domains or CRUD interfaces.

**Strengths.** Independent scaling, query-optimized and update-optimized schemas, simpler queries, security separation (Microsoft CQRS page). An alternative to in-memory joins: [Pattern: API Composition](https://microservices.io/patterns/data/api-composition.html) (n.d.), grouped under `ARCH-07`.

**Weaknesses.** Complexity, possible code duplication, replication lag (`ARCH-07`). Fowler reports colleagues being deeply wary because it is often misused (`ARCH-08`).

**ERP, financial and SaaS suitability.** Useful for operational reporting and tenant dashboards that must not load write tables (INFERENCE). Read models are derived data and must never be the authority for balances (INFERENCE, consistent with note 14's derived-balance guidance).

**Combines with.** Aggregates as the write side (`ARCH-10`). Event sourcing. Not a replacement for a warehouse: a read model serves application queries, while a warehouse integrates sources and history (INFERENCE).

## 13. Data Mesh

**Origin and authority.** Zhamak Dehghani: [How to Move Beyond a Monolithic Data Lake](https://martinfowler.com/articles/data-monolith-to-mesh.html) (2019-05-20) `ARCH-14`; [Data Mesh Principles and Logical Architecture](https://martinfowler.com/articles/data-mesh-principles.html) (2020-12-03) `ARCH-15`, A4; book [Data Mesh](https://www.oreilly.com/library/view/data-mesh/9781492092384/) (2022-03) `LIT-74`, whose page returned 403, url_verified false, so its contents are unread and UNVERIFIED. An operating model for **analytical** data.

**Core rules**

- **MANDATORY** `[OLAP]` `[Lakehouse]` `[Streaming]` Four principles define it: domain ownership, data as a product, self-serve platform, federated computational governance (`ARCH-15`).
- **MANDATORY** `[OLAP]` `[Lakehouse]` A data product is discoverable, addressable, trustworthy, self-describing, interoperable and secure (`ARCH-14`).
- **MANDATORY** `[OLAP]` `[Lakehouse]` Domain data models stay local, while cross-domain identifiers and policies are standardized globally (`ARCH-15`).
- **RECOMMENDED** `[OLAP]` Publish quality and service-level indicators and work backward from use cases: [Data product thinking](https://www.thoughtworks.com/radar/techniques/data-product-thinking) (2025-04), grouped under `ARCH-16`.
- **RECOMMENDED** (INFERENCE) `[OLAP]` `[Lakehouse]` `[Streaming]` Encode an output as a data contract: [Open Data Contract Standard](https://github.com/bitol-io/open-data-contract-standard) (v3.2.0, n.d.) `ARCH-23`. Neither Dehghani's articles nor ODCS cites the other.
- **OPTIONAL/CONTEXTUAL** `[OLAP]` Polyglot serving: events, batch files, relational tables, graphs (`ARCH-15`).

**Workload fit.** Large organizations whose central data team is a bottleneck: [AWS Prescriptive Guidance](https://docs.aws.amazon.com/prescriptive-guidance/latest/strategy-data-mesh/introduction.html) (n.d.) `ARCH-18`, VENDOR. It does not design `[OLTP]` schemas; note 07 adds that the internal operational schema should not be the shared surface (INFERENCE).

**Strengths.** Addresses ownership and bottlenecks. Practice converges on decentralized ownership with central governance or infrastructure: [Architecture and functions in a data mesh](https://docs.cloud.google.com/architecture/data-mesh) (n.d.) `ARCH-17`, VENDOR; [Zalando and Thoughtworks slides](https://www.slideshare.net/slideshow/data-mesh-in-practice-how-europes-leading-online-platform-for-fashion-goes-beyond-the-data-lake-236728093/236728093) (2020-06-25) `ARCH-20`.

**Weaknesses.** Thoughtworks kept it at Trial and never moved it to Adopt, citing high integration costs, adoption limited to parts of large organizations, and vendors distracting from social change: [Data mesh radar entry](https://www.thoughtworks.com/radar/techniques/data-mesh) (last updated 2022-03-29) `ARCH-16`. Requires organizational restructuring and domain willingness (`ARCH-16`). Thoughtworks has an interest as the then employer of the originator.

**ERP, financial and SaaS suitability.** A financial case exists: JPMorgan Chase used per-product lakes, shared rather than copied data, and retained audit-oriented catalogs: [How JPMorgan Chase built a data mesh](https://aws.amazon.com/blogs/big-data/how-jpmorgan-chase-built-a-data-mesh-architecture-to-drive-significant-value-to-enhance-their-enterprise-data-platform/) (2021-05-05) `ARCH-19`, published on a vendor blog. Unsuited to a small ERP or SaaS team lacking multiple autonomous domains (INFERENCE).

**Combines with.** DDD supplies domain boundaries. Inside a data product any model can apply (INFERENCE). Fabric automates metadata and policy across products (Section 14). Medallion can organize a product's internal layers (INFERENCE).

## 14. Data Fabric

**Evidence warning.** Every reachable definition comes from Gartner (paywalled) or vendors with a fabric product. **The notes contain no independent primary source, no peer-reviewed definition and no standards-body definition.** Treat all of this section as VENDOR MARKETING or analyst-reported.

**Origin and authority**

- Gartner glossary: HTTP 403 on both pages. Its wording describing an integrated layer of data and connecting processes reaches the notes only through search-returned third parties, such as [iterate.ai](https://iterate.ai/ai-glossary/data-fabric) (n.d.) and [saturncloud](https://saturncloud.io/glossary/data-fabric) (n.d.). UNVERIFIED.
- Gartner's 2021 Quick Answer note is paywalled and known only through [Starburst's summary](https://www.starburst.io/blog/gartner-data-fabric-data-mesh/) (2022-03-07) `ARCH-22`, A2, VENDOR MARKETING.
- [IBM: What Is a Data Fabric?](https://www.ibm.com/think/topics/data-fabric) (n.d.) `ARCH-21`, A3, VENDOR.
- [Informatica on Data Fabric](https://www.informatica.com/resources/articles/data-fabric-the-transformative-next-step-in-data-management.html) (n.d.), grouped under `ARCH-22`, VENDOR MARKETING.
- [CData Gartner summit recap](https://www.cdata.com/blog/gartner-summit-recap-part3-from-fabric-to-mesh-and-beyond) (n.d.), VENDOR, UNVERIFIED (search only).
- No Thoughtworks Radar blip for data fabric was located.

**Core claims and rules.** No source states a rule that binds a schema.

- IBM describes a design approach rather than a piece of software, using active metadata, semantic knowledge graphs and machine learning, as opposed to static, manually curated metadata (`ARCH-21`, VENDOR).
- **OPTIONAL/CONTEXTUAL** `[OLAP]` `[Lakehouse]` Adopting a fabric design at all.
- **RECOMMENDED** (INFERENCE from note 07) `[All]` Give every schema object machine-readable descriptions, classification, ownership and lineage. This requirement stands independently through Dehghani's self-describing attribute and ODCS.

**Workload fit.** Described by vendors for hybrid or multi-cloud integration. Unproven independently.

**Strengths (as claimed by vendors).** Automated discovery, governance and lineage. May coexist with mesh (`ARCH-21`, `ARCH-22`).

**Weaknesses.** Definition is vendor shaped. It contributes almost nothing to where schema boundaries go (note 07, INFERENCE). No independent critical analysis or measured outcomes appear in the notes.

**ERP, financial and SaaS suitability.** No note source evaluates it for these domains. Metadata requirements may be useful for regulated data (INFERENCE).

**Combines with.** Reported as complementary to mesh, with mesh deciding ownership and fabric automating plumbing (IBM and Gartner summaries; all interested or second-hand).

## 15. MongoDB document modeling

**Origin and authority.** MongoDB's own manual, version 9.0, A5 as official documentation, VENDOR in that it advises on its own product: [Data Modeling](https://www.mongodb.com/docs/manual/data-modeling/) (n.d.) `MSOM-15`; [Schema Validation](https://www.mongodb.com/docs/manual/core/schema-validation/) (n.d.) `MSOM-16`; [Transactions](https://www.mongodb.com/docs/manual/core/transactions/) (n.d.) `MSOM-18`. Release notes give 9.0.0 as released 2026-09-28. Scope below is operational document workloads.

**Core rules**

- **MANDATORY** `[OLTP]` (document stores) Platform limits: 16 MiB BSON documents, 100 nesting levels, 64 indexes per collection, 32 fields in a compound index, and unique immutable `_id` (`MSOM-15`, limits page).
- **MANDATORY** `[OLTP]` (document stores) Write atomicity is at single-document level unless a transaction is used. Transactions need a replica set and must run under one minute by default (`MSOM-15`, `MSOM-18`).
- **RECOMMENDED** `[OLTP]` (document stores) Store together what is accessed together and shape models from access patterns: identify workload, map relationships, apply patterns, create indexes (`MSOM-15`).
- **RECOMMENDED** `[OLTP]` (document stores) Embed for contains relationships and co-accessed or co-updated data. Reference for high-cardinality children, unbounded growth, write-heavy divergent timing, or independent existence (`MSOM-15`).
- **RECOMMENDED** `[OLTP]` (document stores) Avoid the five named anti-patterns: unbounded arrays, bloated documents, unnecessary indexes, too many collections, too many `$lookup` stages (`MSOM-15`).
- **RECOMMENDED** `[OLTP]` (document stores) Use schema validation once an application's structure is established (`MSOM-16`). MongoDB 9.0's `constraint` level guarantees that every document conforms.
- **RECOMMENDED** (strong) `[OLTP]` (document stores) Model money as decimal, not float or double. The vendor states binary floating point is unsuitable for monetary arithmetic and prefers the decimal type over a scale factor (`MSOM-18`, monetary page).
- **OPTIONAL/CONTEXTUAL** `[OLTP]` (document stores) Bucket, polymorphic, schema versioning, archive, computed and single-collection patterns (`MSOM-15`).

**Workload fit.** Aggregate-shaped operational data with known access patterns. Not an analytical warehouse methodology in these sources.

**Strengths.** Avoids joins for co-located data and reduces the need for multi-document transactions (`MSOM-15`, `MSOM-18`). Flexible field sets.

**Weaknesses.** Duplicated data makes updates expensive (`MSOM-15`). Validation is opt-in. MongoDB says distributed transactions cost more and should not replace schema design (`MSOM-15`). Older blog-era patterns such as attribute, extended reference and approximation are not on the current patterns page (note 02).

**ERP, financial and SaaS suitability.** No note source evaluates it for ERP or ledgers. INFERENCE: it suits aggregate-shaped SaaS configuration, catalogs and per-tenant variable attributes better than multi-document ledger posting, where cross-document invariants would depend on transactions the vendor positions as secondary.

**Combines with.** DDD aggregates map closely to documents (INFERENCE). CQRS read models (Microsoft names a document database as a read-store option). `[OLTP]` source for Bronze or Data Vault ingestion (INFERENCE). Optional schema versioning parallels event upcasting (INFERENCE).

## 16. Temporal modeling

**Origin and authority.** Valid time and transaction time are orthogonal, and a table with both is bitemporal: [Snodgrass, Developing Time-Oriented Database Applications in SQL](https://www2.cs.arizona.edu/~rts/tdbbook.pdf) (2000/1999) `TEN-23`. SQL:2011 standardized both, known here through [Temporal features in SQL:2011](https://sigmodrecord.org/publications/sigmodRecord/1209/pdfs/07.industry.kulkarni.pdf) (2012-09) `GOV-06`, A5; the ISO text was not read. Date, Darwen and Lorentzos, and Johnston's asserted versioning, were not fetched beyond publisher records (`LIT-58`, `LIT-60`).

| Vendor or layer | System time | Application or valid time | Source |
|---|---|---|---|
| SQL Server | Native | Not described on the page | [Temporal tables](https://learn.microsoft.com/en-us/sql/relational-databases/tables/temporal-tables) (2026-08-18) `MSOM-04` |
| MariaDB | Native | Not in the page read | [System-Versioned Tables](https://mariadb.com/docs/server/reference/sql-structure/temporal-tables/system-versioned-tables) (n.d.) `TEN-20` |
| Oracle | Flashback Time Travel | Temporal Validity | [Flashback 19c](https://docs.oracle.com/en/database/oracle/oracle-database/19/adfns/flashback.html) (n.d.); [Temporal Validity](https://docs.oracle.com/database/122/VLDBG/control-validity-visibility-data.htm) (n.d.) `TEN-21` |
| PostgreSQL 18 | Not in release notes | `WITHOUT OVERLAPS`, `PERIOD` foreign keys | [PostgreSQL 18 Release Notes](https://www.postgresql.org/docs/18/release-18.html) (2025-09-25) `PERF-16` |
| Warehouse | Not specified by Kimball | SCD Types 0 to 7; Type 2 effective and expiration dates (INFERENCE: application-time rendering) | `DWM-01`; [Design Tip #152](https://www.kimballgroup.com/2013/02/design-tip-152-slowly-changing-dimension-types-0-4-5-6-7/) (2013-02-05) `TEN-24` |

Note: the absence of native PostgreSQL system versioning rests on release notes alone. Db2 temporal documentation could not be retrieved.

**Core rules** (note 14's labels unless stated)

- **MANDATORY** `[OLTP]` Where law or audit requires history, system-time history is system-maintained and not user-editable (`GOV-06` rationale; 21 CFR 11.10(e) as cited in note 14).
- **RECOMMENDED** `[OLTP]` `[DW-integration]` Closed-open periods for valid and system time (`GOV-06`, `TEN-23`, `MSOM-04`).
- **RECOMMENDED** `[OLTP]` Non-overlap constraints per business key, and period-aware foreign keys where the engine supports them (`GOV-06`, `PERF-16`).
- **RECOMMENDED** `[OLTP]` Period timestamps in UTC with transaction-begin semantics (`MSOM-04`).
- **RECOMMENDED** `[DW-presentation]` Choose SCD type per attribute. Type 2 carries effective, expiration and current-row columns (`DWM-01`).
- **OPTIONAL/CONTEXTUAL** `[OLTP]` Bitemporal modeling only when corrections to past-effective facts must be reconstructable as known at a past time (`GOV-06`; `TEN-23` Chapter 10).
- **OPTIONAL/CONTEXTUAL** `[OLTP]` Partition history by system time for retention (`TEN-20`; Flashback `RETENTION`).

Name the time dimension explicitly. Snodgrass classifies queries and constraints as current, sequenced or nonsequenced (`TEN-23`), and sequenced constraints are the hard case.

**Workload fit.** Cross-cutting. Application time and system time mainly apply at `[OLTP]` source, SCD at `[DW-presentation]`, satellites at `[DW-integration]`. Platform time travel is an operational recovery feature, not a history model: Databricks says not to use table history as a long-term backup: [Work with Delta Lake table history](https://docs.databricks.com/aws/en/delta/history) (2026-11-06). Snowflake's retention tops out at 90 days on Enterprise, and Fail-safe is not for user access: [Time Travel](https://docs.snowflake.com/en/user-guide/data-time-travel) (n.d.) `LAKE-11`; [Fail-safe](https://docs.snowflake.com/en/user-guide/data-failsafe) (n.d.).

**Strengths.** Standard vocabulary and engine enforcement where available. Tamper resistance for system-versioned history (`GOV-06`). SQL Server explicitly lists slowly changing dimension maintenance as a temporal-table use (`MSOM-04`).

**Weaknesses.** Vendor coverage varies, and temporal table means different things by vendor (note 14). History is retention-bounded: MariaDB allows privileged history deletion and Flashback purges past retention. Warehouse tools differ: Snowflake Dynamic Tables hold current state only and so cannot hold SCD2 history: [Decision guide for dynamic tables](https://docs.snowflake.com/en/user-guide/dynamic-tables-comparison) (n.d.) `LAKE-12`. dbt snapshots cannot be rebuilt: [dbt snapshots](https://docs.getdbt.com/docs/build/snapshots) (2026-09-29) `LAKE-18`.

**ERP, financial and SaaS suitability.** Essential. ERP effective dating is application time with out-of-order semantics: [Workday Out of Order Changes and Effective Dating](https://doc.workday.com/admin-guide/en-us/human-capital-management/compensation/manage-compensation/meq1649709028535.html) (2025-05-02) `TEN-25`, VENDOR. Note 14 reports insurance and finance as bitemporal examples. Oracle HCM and SAP validity dates were not fetched.

**Combines with.** SCD Type 2 is the warehouse rendering of application-time state, and system-versioned tables can feed it (note 14, INFERENCE). Event streams carry occurrence and entry times. Data Vault load date is arrival time, not valid time (`DWM-11`).

## 17. Comparison matrix

Ratings are relative judgments by this review and the notes. They are not measurements. No source compares all approaches like for like (note 06). n/a means the approach does not decide the property. Evidence sits in the section for each approach.

| Approach | Primary scope | Flexibility | Auditability | Load complexity | Query complexity | Historization | ERP/financial suitability | Tooling maturity | Key evidence |
|---|---|---|---|---|---|---|---|---|---|
| Kimball | DW-presentation, OLAP | Medium | Medium | Medium | Low | SCD 0 to 7 | High for reporting; not a ledger | Highest | `DWM-01`, `DWM-14` |
| Inmon CIF | DW-integration | High | High | High | High at core; low via marts | Time-variant, non-volatile | High for integration | High | `DWM-06`, `DWM-14` |
| Data Vault 2.0 | DW-integration | High | Highest | Low per pattern, high overall | High on vault; low via marts | Insert-only satellites | High for audited multi-source | Growing; skills gap | `DWM-09`, `DWM-13` |
| 3NF | OLTP; also DW-integration | High | Medium; needs history design | Medium | High for analytics | None without temporal design | Highest for OLTP core | Highest | `DES-02`, `DWM-14` |
| One Big Table | OLAP, DW-presentation | Low | Low | Low logic, high I/O | Lowest | None, or full snapshots | Low for ledgers; derived reports only | Medium | `DWM-21`, `DWM-22` |
| Anchor | DW-integration | Highest | High | High table count; templated | High without views and table elimination | Historized attributes and ties | Specialist; thin evidence | Low | `DWM-16` |
| Medallion | Lakehouse layering | n/a (layers adjustable) | Bronze retains raw | Adds hops | Gold read-optimized | n/a; delegated | Neutral | High on Databricks | `LAKE-01`, `LAKE-06` |
| DDD | OLTP boundaries | High within contexts | n/a | n/a | Higher across contexts | n/a | High for modular ERP boundaries (inference) | Mature literature | `ARCH-01`, `ARCH-05` |
| Event-driven | Streaming, OLTP integration | High (low coupling for notification) | Medium | Medium to high | Medium | Depends on pattern | Useful for integration | High; open specs | `ARCH-08`, `ARCH-11` |
| Event sourcing | OLTP subdomains | Medium; event evolution is hard | Highest | High | High without projections | Full event history | Selective, for ledgers and orders | Moderate | `ARCH-09`, `ARCH-10` |
| CQRS | OLTP read paths | Medium | n/a alone | Medium to high with separate store | Low on read model | n/a alone | Useful for operational reads | Moderate | `ARCH-07`, `ARCH-08` |
| Data Mesh | OLAP organization | High for domains | Depends on product standards | High organizational cost | Varies by product | n/a | One large financial case | Immature; Trial on Radar | `ARCH-15`, `ARCH-16`, `ARCH-19` |
| Data Fabric | Metadata and integration | Unproven | Claimed; unverified | Unproven | Unproven | n/a | No evidence | Vendor products; no independent assessment | `ARCH-21`, `ARCH-22` |
| MongoDB document | OLTP (document stores) | High | Low without extra design | Low to medium | Low for embedded; higher with `$lookup` | Optional versioning pattern | Weak evidence; not for ledgers (inference) | High | `MSOM-15`, `MSOM-18` |
| Temporal modeling | Cross-cutting | Medium | High with system time | Medium | High for sequenced queries | Valid, system or bitemporal | Essential | Uneven across vendors | `GOV-06`, `TEN-23` |

### 17.1 Composition by layer (INFERENCE, assembled from Sections 3 to 16)

| Layer | Typical choices | Governing rules |
|---|---|---|
| `[OLTP]` boundaries | DDD contexts and aggregates | Section 10 |
| `[OLTP]` store | 3NF, or document model where aggregate-shaped | Sections 6 and 15 |
| `[OLTP]` history and audit | System-versioned or application-time tables; event sourcing for selected subdomains; append-only ledgers | Sections 11 and 16 |
| Integration between systems | Outbox, events, published contracts | Section 11 |
| Lakehouse hops | Medallion | Section 9 |
| `[DW-integration]` | Inmon 3NF EDW, Data Vault or Anchor, justified by multi-source reconciliation or audit | Sections 4, 5 and 8 |
| `[DW-presentation]` | Kimball star, with derived OBT where justified | Sections 3 and 7 |
| Organization and publishing | Data Mesh ownership and data contracts | Section 13 |
| Metadata | Machine-readable descriptions and lineage; any fabric tooling is optional | Section 14 |

## 18. Documented disagreements

Each item names the positions and states what remains unresolved. None is a settled verdict.

### 18.1 Kimball versus Inmon on integration

- Kimball Group: a normalized layer is unwarranted duplication in most cases, and conformed dimensions are the enterprise backbone (`DWM-04`).
- Inmon: conformed dimensions are insufficient, and a normalized integrated warehouse with master data is required (`DWM-06`).
- Neither has retracted. Both accept a hybrid, and each portrays it as the other's movement. Oracle treats the two as layers (`DWM-14`). The Kimball Group later de-escalated: [Design Tip #139](https://decisionworks.com/2011/10/design-tip-139-much-ado-about-nothing/) (2011-10-05), A4. Each side alleges commercial motive in the other. Top-down and bottom-up labels are secondary framing absent from the 2004 paper: [TDWI column](https://tdwi.org/blogs/data-101/2026/05/architectural-disagreement-that-still-shapes-data-warehouses.aspx) (2026, A3).
- A 2026 preprint concludes no single methodology is universally optimal: [arXiv 2606.29355](https://arxiv.org/abs/2606.29355) (2026-06-28), A2, un-refereed, full mapping not read.

### 18.2 Whether 3NF is intrinsic to CIF

The Kimball Group says CIF requires a 3NF layer (`DWM-04`). Inmon's 2025 text stresses integrated, granular, non-volatile data (`DWM-06`). The notes treat 3NF as RECOMMENDED within Inmon's school. The original CIF book was not read, so this remains open.

### 18.3 Surrogate key strategy

| Position | Source |
|---|---|
| Sequential integer surrogates, date exempt | Kimball, `DWM-01` |
| Natural keys, surrogates are tricky | Beauchemin, `DWM-23` |
| Hashed surrogates | dbt tutorial, `DWM-21`; Data Vault 2.0 default, `DWM-12` |
| String keys | [dbt style guide](https://docs.getdbt.com/best-practices/how-we-style/1-how-we-style-our-dbt-models) (2026-09-10) `LAKE-16` |
| Natural keys preferred, avoid hash surrogates, deterministic order-preserving surrogates when IDs are unstable | [Dimensional modeling in Lakeflow pipelines](https://docs.databricks.com/aws/en/ldp/best-practices/dimensional-modeling) (2026-10-15) `DWM-19` |
| Identity columns | Databricks blog, `LAKE-06` |
| Numeric keys over hash keys, including for Data Vault | Snowflake, `LAKE-14`; [Snowflake Data Vault tips](https://www.snowflake.com/en/blog/tips-for-optimizing-the-data-vault-architecture-on-snowflake/) (2020-02-03) |

Databricks' own Data Vault blog recommends hash keys while its Lakeflow documentation advises against hash surrogates for dimensional models. Kimball's two reasons, attribute history and unstable source keys, are the common ground (note 06, INFERENCE). Separately, the standards criteria require Data Vault to support hash, sequence and natural keys (`DWM-09`), which weakens the claim that hashing defines DV 2.0.

### 18.4 Denormalization as a performance necessity

Kimball and Oracle denormalize dimensions for speed. Anchor claims strong retrieval in 6NF through table elimination, under certain conditions (`DWM-16`). Fivetran measures wide tables as faster in most tests (`DWM-22`). dbt prefers wide marts, except with its Semantic Layer. Snowflake denies any universal guideline (`LAKE-14`). Evidence is vendor, author or practitioner in every case.

### 18.5 Is Kimball obsolete?

The claim lives in talks and forum posts (A2 to A3). Coalesce 2020 talks and Beauchemin's *Functional Data Engineering* were not opened (UNVERIFIED). A4 and A5 sources retain facts and dimensions (`DWM-21`, `LAKE-06`). What critics actually discard are performance-motivated parts, namely mandatory integer keys and heavy SCD handling.

### 18.6 How to record history in analytics

Kimball SCD row versioning; Beauchemin's dimension snapshots per partition (`DWM-23`); Data Vault insert-only satellites with PIT; automated SCD2 via Databricks AUTO CDC. These are implementation strategies for as-is and as-was reporting (note 06). **Sub-conflict:** a Databricks blog calls SCDs easy with Delta time travel (`LAKE-06`), while Databricks documentation warns table history is not for long-term retention and defaults to 7 days of deleted-file retention. INFERENCE: time travel should not be the basis of SCD history.

### 18.7 Temporal semantics

Closed-open storage is shared, yet `BETWEEN ... AND` includes the upper bound while `FROM ... TO` excludes it. Kimball's Type 2 does not specify open or closed semantics. SQL:2011 `FOR PORTION OF` splits a row so a backdated change applies to its interval, whereas Workday lets a later-effective edit supersede a backdated one (`TEN-25`). Vendors also use temporal table to mean different things (note 14).

### 18.8 Aggregate transaction rule: absolute or default

Fowler says transactions should not cross aggregate boundaries (`ARCH-02`). Vernon calls one aggregate per transaction a rule of thumb and lists reasons to break it (`ARCH-03`).

### 18.9 Physical strength of the bounded context

Microsoft states each context must have its own model and database, but also says the pattern does not require a distributed service (`ARCH-04`). Evans names database schemas (`ARCH-01`). Richardson offers a ladder from private tables to separate servers (`ARCH-05`). The same site labels Shared Database both a pattern and an anti-pattern: [Pattern: Shared database](https://microservices.io/patterns/data/shared-database.html) (n.d.), grouped under `ARCH-05`.

### 18.10 Event sourcing claims

- Source of truth: Fowler 2005 says the record may be either the log or the current state (`ARCH-09`), while Fowler 2017 makes the event store the principal source (`ARCH-08`).
- Broker versus store: microservices.io says the store behaves like a broker, while Microsoft says a broker such as Kafka is no substitute for an event store (`ARCH-10`).
- Asynchrony: Fowler says it is not necessary (`ARCH-08`), while Microsoft's reference flow uses queues and is eventually consistent (`ARCH-10`). Both treat this as a design choice.
- Immutability versus erasure: Microsoft notes the append-only store conflicts with data protection obligations (`ARCH-10`).

### 18.11 Data Mesh polyglot versus standardized infrastructure

Dehghani emphasizes polyglot serving within the quantum (`ARCH-15`). Zalando says decentralized ownership does not imply decentralized infrastructure (`ARCH-20`). JPMorgan standardizes on one stack (`ARCH-19`). Google allows domain variation within guardrails (`ARCH-17`). Thoughtworks left mesh at Trial yet moved the narrower data product thinking to Adopt in April 2025 (`ARCH-16`).

### 18.12 Data Fabric versus Data Mesh

Sources describe them as complementary or a category mismatch (`ARCH-21`, `ARCH-22`, CData). All such statements are vendor or second-hand reports of Gartner. There is no independent adjudication in the notes.

### 18.13 Normalize versus co-locate

Oracle's 3NF aims to minimize redundancy (`DWM-14`). MongoDB's core principle is to store together what is accessed together (`MSOM-15`). This is largely a scope and engine difference. MongoDB itself bounds embedding through its anti-patterns.

### 18.14 Schema on write versus schema at ingestion

Classic warehouses assume typed staging. Databricks Bronze stores most fields as string, VARIANT or binary (`LAKE-01`). The Lakehouse paper concedes some loss of data independence: [Lakehouse](https://www.cidrdb.org/cidr2021/papers/cidr2021_paper17.pdf) (2021-01) `LAKE-07`.

### 18.15 Money types in examples

A dbt style-guide example casts an order total to float (`LAKE-16`). That conflicts with MongoDB's statement that binary floating point is unsuitable for money (`MSOM-18`) and Snowflake's recommendation of exact types for ledgers: [Numeric data types](https://docs.snowflake.com/en/sql-reference/data-types-numeric) (n.d.). INFERENCE: this is an illustrative example rather than dbt policy, and should not be copied.

## 19. Evidence gaps carried forward

- **Originators not established in the notes:** CQRS, event sourcing, Medallion date of first use, Data Fabric. One Big Table has no originator.
- **Books not read:** Kimball toolkit text, Inmon, *Corporate Information Factory*, Linstedt and Olschimke, Evans 2003, Vernon 2013, Dehghani 2022, Young's versioning book, DMBOK, Date, Johnston.
- **No independent benchmark** of Data Vault against star schema, or peer-reviewed comparison of OBT against star.
- **ERP, financial and SaaS suitability** is mostly INFERENCE. Direct evidence exists for ledgers, ERP effective dating, Snowflake multi-tenant patterns and one Data Mesh financial case. No note source evaluates MongoDB or Data Fabric for ERP. The DDD and mesh literature does not prescribe tenant storage.
- **Time-limited facts** to recheck: Databricks multi-statement transactions and Metric Views (preview in December 2025), CloudEvents text read from a 1.0.3-wip branch, and AsyncAPI, where a 3.1.0 version exists but was not read.
- **Undated pages:** microservices.io, Snowflake documentation and several vendor pages carry no publication date, so their currency is known only as live on 2026-11-07.
