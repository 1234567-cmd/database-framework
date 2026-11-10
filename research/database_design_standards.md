# Database Design Standards: Evidence Base
Research deliverable for the future technology-independent Database Schema Design and Data Engineering Standards Framework (ERP, financial, SaaS, data engineering). This phase is research only. The document contains no schemas, DDL templates or framework implementation. Identifiers in code font are vocabulary or examples of a source's convention.

Built only from the project notes, verified 2026-11-07/08. `CORRECTIONS.md` was applied over the notes. Updated 2026-11-08 from notes 20, 21 and 22 and `verification_results.json`, which override earlier restrictions where they confirm or correct a claim. No web research was performed for this file.

## 0. How to read this document
### 0.1 Statement labels
These are candidate labels for the later framework, graded by evidence. They are not adopted rules.

- **MANDATORY**: violating it corrupts data or breaks a hard engine rule, or at least two independent sources state it as a requirement. Always scoped.
- **RECOMMENDED**: strong default with sourced reasoning. Deviate only with a recorded reason.
- **OPTIONAL/CONTEXTUAL**: legitimate choices exist on both sides, or the source ties it to a situation.
- **[METHOD-MANDATORY]**: mandatory only inside a named methodology (for example Kimball). Not a general rule.
- **[ENGINE]**: true of the named engine only.
- **[INFERENCE]**: reasoned from sources by the note authors or this synthesis. No source states it directly.
- **[UNVERIFIED]**: the source could not be read, or `CORRECTIONS.md` restricts it. Do not treat as established.
### 0.2 Workload scope tags
Every statement carries one of these tags. They are never interchangeable.

| Tag | Meaning here |
|---|---|
| OLTP | Transactional system of record: many short reads and writes, integrity enforced at write time |
| OLAP | Analytical query workload on read-optimized engines, regardless of modeling method |
| DW | A data warehouse as an integrated, modeled store (dimensional, 3NF EDW or Data Vault). A DW usually runs on an OLAP engine, but DW modeling rules and OLAP physical rules are separate topics |
| LAKE | Lakehouse or open table formats and cloud warehouses with unenforced key constraints |
| STREAM | Event streams and their consumers |
| HTAP | Row store of record plus a columnar copy |
| ALL | Applies across the workloads above, and the sources support that breadth |

The evidence is uneven by scope. OLTP and DW are well covered. LAKE evidence is thin in the notes used here, and most LAKE tags in note 10 were inferred by analogy, as that note itself says. STREAM evidence in this topic set is limited to consumer idempotency and one 2005 throughput comparison. Where a statement is tagged only OLTP, its application elsewhere has not been evidenced.

### 0.3 Citation and quotation conventions
Citations are `[Title](URL)` followed by date or n.d., then the catalog ID where one exists. A source with no ID is not in `resource_catalog.json` under that URL.

Quotation marks appear for text extracted from PDFs, marked [PDF], and for web text extracted directly by curl or confirmed as exact or corrected wording in note 22, marked [RAW]. Other web-page content is paraphrase, because most web pages were read through a summarizing fetch tool. Findings tagged [WF] rest only on that tool. They are never quoted and must be re-checked against the page before being relied on.

### 0.4 Source weighting used
Standards and vendor manuals settle semantics (what NULL does, what a limit is). Foundational papers settle definitions. Recognized books and major-organization engineering standards settle defaults. Practitioner guides settle style. When two style sources disagree, the statement is labelled OPTIONAL/CONTEXTUAL and consistency is what is required. This weighting follows the inference recorded in note 10.

No general rule below rests on one vendor's page alone unless it is flagged [ENGINE] or single-source.
## 1. Why OLTP, OLAP, DW and LAKE rules differ
**Scope: ALL (framing).**
- Row stores are write-optimized and column stores are read-optimized. The C-Store authors tie row storage to OLTP-style applications and column storage to reading only the columns a query requires: [C-Store: A Column-oriented DBMS](https://www.vldb.org/archives/website/2005/program/paper/thu/p553-stonebraker.pdf) (2005; PERF-39). Its benchmark is the authors' own, read-only, on 2005 hardware, so its ratios are directional only.
- Stonebraker and Cetintemel argue one engine design no longer fits all markets. They describe star schemas as common in warehouses and virtually absent from OLTP, and bitmap indexes as suited to warehouses and not to OLTP: [One Size Fits All: An Idea Whose Time Has Come and Gone](https://cs.brown.edu/~ugur/fits_all.pdf) (2005; PERF-38). The ICDE venue commonly attached to this paper is not printed in the PDF, so it is not asserted here.
- Vendor documentation operationalizes the same split. SQL Server positions rowstore indexes for transactional seeks and columnstore for analytic scans: [Columnstore indexes: Overview](https://learn.microsoft.com/en-us/sql/relational-databases/indexes/columnstore-indexes-overview) (2026-09-14; PERF-02). Oracle positions global indexes for OLTP and local indexes for decision support: [Partitioning Concepts](https://docs.oracle.com/en/database/oracle/oracle-database/26/vldbg/partition-concepts.html) (n.d.; MSOM-11).
- LAKE systems differ again on a point that matters for this document. Primary key, foreign key and unique constraints are informational and unenforced on Databricks and on Snowflake standard tables, while NOT NULL and CHECK are enforced: [Constraints on Databricks](https://docs.databricks.com/aws/en/tables/constraints) (2026-10-29; LAKE-02), [Constraints overview (Snowflake)](https://docs.snowflake.com/en/sql-reference/constraints-overview) (n.d.; LAKE-09). Snowflake gives the load and DML cost on large distributed columnar tables as the reason.

**Consequence for the framework [INFERENCE]:** a rule without a scope tag should not be admitted. Most apparent conflicts in the literature resolve as scope differences, and the rest are listed in section 12.2.
## 2. Logical and physical modeling; ER design
**Scope: ALL for the separation of levels. OLTP and DW for the specific constructs.**
### 2.1 Findings
- Codd separates the user's model from machine representation. He states that future users of large data banks must be protected from knowing how data is organized in the machine, and identifies ordering, indexing and access-path dependence to remove: [A Relational Model of Data for Large Shared Data Banks](https://www.engineering.upenn.edu/~zives/03f/cis550/codd.pdf) (1970-06; DES-01).
- Chen defines entities, relationship sets, attributes as functions into value sets, and weak entities through existence dependence. His diagram uses rectangles for entity sets and diamonds for relationship sets, with 1:n and m:n mappings. Minimum as well as maximum participation can be specified. His procedure decides primary keys only after entity and relationship relations are organized: [The Entity-Relationship Model: Toward a Unified View of Data](https://www.comp.nus.edu.sg/~lingtw/papers/tods76.chen.pdf) (1976-03; DES-03).
- Chen on artificial identifiers [PDF]: "If we cannot find such one-to-one mapping on available data, or if simplicity in identifying entities is desired, we may define an artificial attribute and a value set so that such mapping is possible." Same source.
- IDEF1X is described as a logical database design method. It has identifier-independent and identifier-dependent entities, key migration from parent to child, identifying relationships where the child key includes the parent key, and category relationships with a discriminator: [IDEF1X Data Modeling Method](https://www.idef.com/idef1x-data-modeling-method/) (n.d.). FIPS 184 was issued 1993-12-21 and effective June 30, 1994; its full text has now been read by pdftotext (note 20), which replaces the earlier finding that the PDF had no extractable text: [FIPS PUB 184](https://nvlpubs.nist.gov/nistpubs/Legacy/FIPS/fipspub184.pdf) (1993-12-21; GOV-27). Section 3.5.4 [PDF]: a specific connection relationship "is always between exactly two entities"; in identifying and mandatory non-identifying relationships each child instance has exactly one parent instance; in an optional non-identifying relationship the child has zero or one parent; "Only non-identifying relationships may be recursive". Section 3.5.1 lists five cardinalities from the parent's perspective: zero or more, at least one, zero or one, an exact number, and a range. Section 3.6: a category cluster is complete if every generic instance has a category instance, and the discriminator of a complete cluster "must not be an optional attribute." Annex A3.4.1: at the key-based phase "only a specific relationship form" may be used, so many-to-many relationships must be refined. Status: withdrawn, per Wikipedia (2008-09-02; Federal Register vol. 73, page 51276). No NIST notice was opened.
- Fowler catalogs the physical mappings: Identity Field, Foreign Key Mapping, Association Table Mapping, Embedded Value, Serialized LOB, and Single Table, Class Table and Concrete Table Inheritance: [Catalog of Patterns of Enterprise Application Architecture](https://martinfowler.com/eaaCatalog/) (2003-03-05; DES-14).
- Hierarchies: PostgreSQL offers `ltree` for materialized paths with indexed ancestor and descendant queries: [ltree](https://www.postgresql.org/docs/current/ltree.html) (n.d.). Karwin lists relying on simple parent references as the Naive Trees antipattern: [SQL Antipatterns, Volume 1](https://pragprog.com/titles/bksap1/sql-antipatterns-volume-1/) (2022-10; DES-13). Only the publisher's one-line descriptions and table of contents were read; the contents say only Naive Trees, Solution: Use Alternative Tree Models (note 22). Closure table and nested set are not found there, so they are not named as Karwin's content, and no other opened source covers them.
- Hierarchies on SQL Server: Microsoft states that subtree queries are "significantly faster with hierarchyid", that direct descendant queries are slightly slower, that moving nonleaf nodes is slower, and that a row move touches one row with parent/child and n subtree rows with `hierarchyid`. Its relationships are not enforced like a foreign key, and uniqueness needs a constraint: [SQL Server: Hierarchical data](https://learn.microsoft.com/en-us/sql/relational-databases/hierarchical-data-sql-server) (n.d.; THIN-07) [ENGINE: SQL Server; statements carry no numbers].
- Crow's foot origin: Redgate [RAW] says "The beginning of crow's foot notation dates back to an article by Gordon Everest (1976, Fifth Computing Conference, IEEE)." Everest called it the "inverted arrow": [Crow's Foot Notation](https://www.red-gate.com/blog/crow-s-foot-notation/) (n.d.; THIN-02). The 1976 paper was not opened, and Redgate's body text and footnote name the venue differently (12.2).
- Supertype and subtype mappings, as described by the sources (ORM mapping sources, OLTP). [Inheritance mapping patterns (Fowler)](https://martinfowler.com/eaaCatalog/singleTableInheritance.html) (2003-03-05; THIN-03), [An Introduction to Hibernate 6](https://docs.hibernate.org/orm/6.6/introduction/html_single/) (n.d., version 6.6; THIN-04), [EF Core: Inheritance](https://learn.microsoft.com/en-us/ef/core/modeling/inheritance) (n.d.; THIN-05)

| Option | Fowler | Hibernate | EF Core |
|---|---|---|---|
| One table for hierarchy | Single Table Inheritance | SINGLE_TABLE [RAW]: "Attributes declared by subclasses map to columns without NOT NULL constraints." | TPH, the default [RAW]: "Database columns are automatically made nullable as necessary when using TPH mapping." |
| One table per class | Class Table Inheritance | JOINED: NOT NULL and foreign keys remain available. [RAW] "The best option when we care a lot about constraints and normalization." | TPT [RAW]: "In many cases, TPT shows inferior performance when compared to TPH." |
| One table per concrete class | Concrete Table Inheritance | TABLE_PER_CLASS: UNION to read. [RAW] "Associations targeting a superclass cannot have a corresponding FOREIGN KEY constraint in the database." | TPC: addresses some TPT performance problems |

- Many-to-many: EF Core [RAW] says the relationship "cannot be represented in a simple way using just a foreign key" and uses a join table: [EF Core: Many-to-many relationships](https://learn.microsoft.com/en-us/ef/core/modeling/relationships/many-to-many) (n.d.; THIN-06). FIPS 184 requires refinement before the key-based phase.
### 2.2 Statements
- RECOMMENDED (ALL): model in three levels, conceptual (entities and relationships), logical (relations, keys, identifying relationships), physical (engine types, indexes, partitioning, controlled redundancy). Grounding: Codd, Chen, IDEF1X, and Kent's physical-performance caveat in section 3. The three-schema ANSI/SPARC origin is known in the notes only through an unfetched encyclopedia result [UNVERIFIED].
- MANDATORY (OLTP, DW at the logical level): every relationship has explicit cardinality and optionality before keys are assigned. Grounding: Chen and IDEF1X. [INFERENCE] as a process requirement.
- MANDATORY (OLTP): a many-to-many relationship is realized by an association table with two foreign keys. Grounding: Chen's m:n relationship relations, Fowler's Association Table Mapping, EF Core and FIPS 184. Whether the join row needs its own attributes or identity is not settled by these sources.
- [METHOD-MANDATORY] (IDEF1X conformance only, historical US federal scope): the FIPS 184 relationship and category rules in 2.1.
- RECOMMENDED (OLTP): identifying relationships carry the parent key into the child key (Chen, IDEF1X). An ORM-centric equivalent is a surrogate child key plus a unique constraint on the parent key and local key [INFERENCE].
- OPTIONAL/CONTEXTUAL (OLTP): supertype and subtype mapping. Single Table favors few subtype columns and simple queries but relies on nullable columns. Class Table supports subtype-specific NOT NULL and foreign keys at the cost of joins and matches the IDEF1X category structure. Concrete Table has no shared foreign key target. The shape of this trade-off is now stated by Hibernate and EF Core (2.1). No source measures it, and engine-neutral evidence and database-native subtype enforcement (such as an exclusive-arc constraint) were not covered.
- OPTIONAL/CONTEXTUAL (OLTP): hierarchy pattern chosen by read and write ratio. An adjacency list is foreign-key enforceable.
- RECOMMENDED (DW): declare the grain first and never mix grains in a fact table [METHOD-MANDATORY in Kimball]: [Kimball Dimensional Modeling Techniques](https://www.kimballgroup.com/wp-content/uploads/2013/08/2013.09-Kimball-Dimensional-Modeling-Techniques11.pdf) (2013; DWM-01).
### 2.3 Universal vs engine-specific
Universal: the three levels, cardinality and optionality, association tables for m:n in relational OLTP. Engine-specific: `ltree` [ENGINE: PostgreSQL]; PostgreSQL table inheritance, which the community wiki says not to use: [Don't Do This](https://wiki.postgresql.org/wiki/Don%27t_Do_This) (2024-11-21; PGMY-10).

### 2.4 Contested
- **Notation** (crow's foot, Chen, IDEF1X): the crow's foot origin now rests on two opened pages (Redgate and the [Runestone textbook](https://runestone.academy/ns/books/published/practical_db/PART2_DATA_MODELING/04-other-notations/other-notations.html), n.d., supporting page recorded with THIN-02), but the 1976 paper is unread. Runestone [RAW]: "Different drawing and modeling tools may or may not provide direct support for these, and notations vary widely." No evidence favors one notation for outcomes. Treat as OPTIONAL with consistency required.
- **Supertype mapping**: no source in the notes measures the alternatives. Hibernate favors JOINED when constraints matter, while EF Core defaults to TPH and warns on TPT performance; they optimize for different goals, so neither is a universal default. Rails makes Single Table the framework default through its reserved `type` column ([Active Record Basics](https://guides.rubyonrails.org/active_record_basics.html), n.d., THIN-10), which is a convention and not evidence of merit.
### 2.5 Outdated
- FIPS 184's federal mandate has lapsed per Wikipedia and the catalog record (no NIST notice opened). ISO/IEC/IEEE 31320-2:2012 is reported as the successor, and its text was not read. The method remains a useful reference.
- PostgreSQL table inheritance as a modeling tool. See the wiki above.
## 3. Normalization and denormalization
**Scope: OLTP for normalization rules. OLAP, DW and read models for sanctioned denormalization.**
### 3.1 Findings
- Codd defines normalization as eliminating non-simple domains. Confirmed text [PDF]: "There is, in fact, a very simple elimination procedure, which we shall call normalization." Condition (2) of his normal form [PDF]: "No primary key has a component domain which is nonsimple." [Codd 1970](https://www.engineering.upenn.edu/~zives/03f/cis550/codd.pdf) (1970-06; DES-01).
- Codd records that consistency checks on redundant data slow insertions, deletions and key updates [PDF]: "Naturally, such checking will slow these operations down." Same source.
- Kent gives plain-language definitions (paraphrase). 1NF concerns uniform record shape and is more definitional than guidance. 2NF prohibits a non-key field depending on part of a composite key. 3NF prohibits a non-key field depending on another non-key field. Together, a non-key field is a fact about the whole key and nothing else; [RAW] "the whole key, and nothing but the key" (the served page reads "us the whole key", so only this part is quoted). 4NF prohibits independent multivalued facts in one record. 5NF applies where information can be reconstructed from smaller records and differs from 4NF only under a symmetric constraint: [A Simple Guide to Five Normal Forms](https://www.bkent.net/Doc/simple5.htm) (1983-02; DES-02).
- Kent names the anomalies (paraphrase): repeated data drifts on update; a department's location cannot be stored without an employee; combining multivalued facts makes blanks ambiguous. Exact wording from the page [RAW]: "such a format also leads to ambiguities regarding the meanings of blank fields"; "the size of the normalized files increases in an additive fashion, while the size of the unnormalized file increases in a multiplicative fashion". Earlier shortened phrasings are not his words.
- Kent limits his own guidance (paraphrase): the rules assume non-key fields are updated often, they penalize retrieval, full normalization is not required, and performance requirements can justify stopping short. Same source.
- Chen observes that changing functional dependencies can take relations out of 3NF, and contrasts 3NF with ER relations: [Chen 1976](https://www.comp.nus.edu.sg/~lingtw/papers/tods76.chen.pdf) (1976-03; DES-03).
- Dimensional design departs from 3NF deliberately. [Kimball Dimensional Modeling Techniques](https://www.kimballgroup.com/wp-content/uploads/2013/08/2013.09-Kimball-Dimensional-Modeling-Techniques11.pdf) (2013; DWM-01). Star schemas are a warehouse form: [One Size Fits All](https://cs.brown.edu/~ugur/fits_all.pdf) (2005; PERF-38).
- MySQL's optimization guidance separates normalized transactional data from denormalized or summary data for reporting: [Optimizing Data Size](https://dev.mysql.com/doc/refman/8.4/en/data-size.html) (n.d.).
- Read models: CQRS read stores may be materialized and denormalized at the cost of eventual consistency and added complexity, and the pattern is not suited to simple CRUD domains: [CQRS Pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/cqrs) (2025-02-20; PERF-56).
### 3.2 Statements
- MANDATORY (OLTP base tables): no repeating groups, delimited lists or numbered-column arrays. Grounding: Codd, Kent, Karwin's Jaywalking and Multicolumn Attributes. Note 10 extends this to all workloads. This document does not, because LAKE and OLAP engines offer nested and semi-structured columns as a design choice, and Databricks describes VARIANT, JSON strings, structs and arrays as Silver-layer modeling options (note 04). See 3.4.
- MANDATORY (OLTP system-of-record tables whose non-key fields are updated): 3NF, with BCNF where every determinant must be a key. Grounding: Kent's anomalies arise exactly when non-key fields are updated. BCNF primary text was not read [UNVERIFIED definition].
- RECOMMENDED (OLTP): check 4NF and 5NF wherever a table holds two or more independent multivalued facts (Kent).
- OPTIONAL/CONTEXTUAL (OLAP, DW, read replicas): denormalize when the workload is read-dominant, the redundancy has one controlled write path, and the dependency is documented. The three conditions are [INFERENCE] from Codd and Kent. No vendor page in the notes states them.
- OPTIONAL/CONTEXTUAL (OLTP): denormalize only with a measured need and a single maintaining path. Kent permits it, but no source in the notes quantifies the benefit or cost in OLTP.
- OPTIONAL/CONTEXTUAL (HTAP): prefer a columnar secondary copy to schema denormalization where operational analytics are needed: [Columnstore overview](https://learn.microsoft.com/en-us/sql/relational-databases/indexes/columnstore-indexes-overview) (2026-09-14; PERF-02), [TiDB: Explore HTAP](https://docs.pingcap.com/tidb/stable/explore-htap/) (n.d.; PERF-49). Both are vendor claims. No independent benchmark is in the notes.
### 3.3 Universal vs engine-specific
Universal: the definitions of the normal forms and the anomalies they prevent. Workload-specific: where they are required. Not engine-specific, except where a store has no joins or unenforced keys.

### 3.4 Contested
- **Normalize vs dimensional modeling**: Kent and Codd address transactional base tables, Kimball addresses the presentation layer fed by ETL. This is a scope difference.
- **1NF in analytical stores**: Codd knew of no application requiring relaxation [PDF: "The writer knows of no application which would require any relaxation of these conditions."]. LAKE platforms ship nested types, and Databricks recommends storing most Bronze fields as strings, VARIANT or binary to guard against source change (note 04). Context: Codd's statement is from 1970 and concerns a relational data model; Bronze layers are raw capture. Atomicity is unresolved for Silver and Gold LAKE layers in the notes used here.
- **Denormalize for performance**: true for warehouses and read models, not a default for OLTP. Stonebraker says materialized views suit warehouses and never OLTP. SQL Server permits indexed views on transactional tables while warning of significant DML degradation: [Create Indexed Views](https://learn.microsoft.com/en-us/sql/relational-databases/views/create-indexed-views) (2025-01-14; PERF-04).
### 3.5 Outdated
- Denormalize as a general performance reflex, carried over from read-reporting advice into OLTP.
- Treating Stonebraker's categorical 2005 statement as current for all engines. Indexed views and HTAP copies exist, with documented costs.
- 6NF and primary formal texts for BCNF, 4NF and 5NF were not read. C. J. Date's works were inaccessible. Do not cite them for specific claims.
## 4. Keys: natural vs surrogate, integer vs UUID
**Scope: varies by statement. Physical key advice depends on topology.**
### 4.1 Findings: identity
- Codd's primary key [PDF]: "Normally, one domain (or combination of domains) of a given relation has values which uniquely identify each element (n-tuple) of that relation. Such a domain (or combination) is called a primary key." Confirmed in note 22 by pdftotext on the PDF retrieved by WebFetch; a curl retest failed locally. [Codd 1970](https://www.engineering.upenn.edu/~zives/03f/cis550/codd.pdf) (1970-06; DES-01).
- PostgreSQL says relational theory requires a primary key on every table and that it is usually best to follow this although it is not enforced: [Constraints](https://www.postgresql.org/docs/current/ddl-constraints.html) (n.d.; PGMY-01).
- InnoDB uses the primary key as the clustered index, falls back to the first unique NOT NULL index, and otherwise creates a hidden 6-byte row ID index. The manual advises defining a primary key on each table and keeping it short because secondary indexes contain it: [Clustered and Secondary Indexes](https://dev.mysql.com/doc/refman/8.4/en/innodb-index-types.html) (n.d.; PGMY-12).
- SQL Server states that a heap is generally not recommended, and that a clustered key should be narrow, unique, ever-increasing and immutable: [Index Architecture and Design Guide](https://learn.microsoft.com/en-us/sql/relational-databases/sql-server-index-design-guide) (2026-09-14; MSOM-01).
- PostgreSQL's logical replication additionally needs a replica identity (note 01).
### 4.2 Findings: natural vs surrogate
- Kimball's warehouse rule: dimension and fact joins use surrogate keys, which are simple integers. His reasons are history tracking, insulation from production key behavior, special rows for missing cases, and smaller fact tables. He concedes the join-performance benefit is suspected but unproven: [Surrogate Keys](https://www.kimballgroup.com/1998/05/surrogate-keys/) (1998-05-02; DES-12). The often-repeated line that keys should not encode meaning was not found on the page (note 22), so it is not attributed to him. The nearest text [RAW]: "your smart keys built up out of real data" (Surrogate Keys) and "Meaningless, sequentially assigned surrogate keys" (10 Essential Rules, Rule #8).
- Kimball exempts the date dimension and treats fact-table surrogate keys as optional: [Kimball Techniques](https://www.kimballgroup.com/wp-content/uploads/2013/08/2013.09-Kimball-Dimensional-Modeling-Techniques11.pdf) (2013; DWM-01), [The 10 Essential Rules](https://www.kimballgroup.com/2009/05/the-10-essential-rules-of-dimensional-modeling/) (2009-05-29; DWM-02).
- Data Vault 2.0 replaces integer sequences with hash keys derived from business keys, removing lookups and supporting parallel loading across platforms: [Hash Keys in Data Vault](https://www.scalefree.com/blog/data-vault/hash-keys-in-the-data-vault/) (2017-04-28, updated 2026-05-11). Note 06 records this as a default rather than the only compliant choice.
- dbt's style guide says each model has a primary key named `<object>_id` and that keys should be strings: [How we style our dbt models](https://docs.getdbt.com/best-practices/how-we-style/1-how-we-style-our-dbt-models) (2026-09-10; LAKE-16).
- Celko is reported to classify auto-increment values as exposed physical locators and to prefer industry-standard then natural keys. This comes from search summaries only [UNVERIFIED].
- Karwin lists applying one primary key convention to every table as the ID Required antipattern, and filling key gaps as Pseudokey Neat-Freak: [SQL Antipatterns, Vol. 1](https://pragprog.com/titles/bksap1/sql-antipatterns-volume-1/) (2022-10; DES-13). Publisher descriptions only.
- ORM defaults use `id` as primary key (Rails, Django, EF Core), with 64-bit defaults in Rails since 5.1 and in Django's `BigAutoField`: [Rails 5.1 Release Notes](https://guides.rubyonrails.org/5_1_release_notes.html) (n.d.), [Django model field reference](https://docs.djangoproject.com/en/5.2/ref/models/fields/) (n.d.), [EF Core: Keys](https://learn.microsoft.com/en-us/ef/core/modeling/keys) (n.d.).
### 4.3 Findings: integer width
- Integer overflow raises an error at the range limit: [Numeric Types](https://www.postgresql.org/docs/current/datatype-numeric.html) (n.d.; PGMY-02).
- Buildkite (2023-07-22) had `bigint` agent IDs and a 32-bit referencing column. Once IDs passed the 32-bit limit, jobs could not be assigned to newly connected agents. Follow-ups included alerting at 50% of identifier range and tests blocking new 32-bit identifiers: [Newly connected agents unable to run jobs](https://buildkitestatus.com/incidents/63zxhjsysszc) (2023-07-22).
- Alibaba mandates an unsigned bigint `id`: [Alibaba Java Coding Guidelines](https://alibaba.github.io/Alibaba-Java-Coding-Guidelines/) (n.d.; DES-22).
- The PostgreSQL wiki prefers identity columns to `serial`, while the manual is neutral (note 01). [Don't Do This](https://wiki.postgresql.org/wiki/Don%27t_Do_This) (2024-11-21; PGMY-10).
### 4.4 Findings: UUID and ordered IDs
- RFC 9562 (Proposed Standard, obsoletes RFC 4122) defines UUIDv7 with a 48-bit Unix millisecond timestamp. It says non-time-ordered versions such as v4 have poor index locality, recommends v7 over v1 and v6 where possible, and advises against name-based versions as primary keys: [RFC 9562](https://www.rfc-editor.org/rfc/rfc9562) (2024-05; DES-04; May 2024 confirmed from page metadata in note 22).
- Percona (InnoDB): out-of-order inserts cause page splits and low fill. Primary key copies took about 70 percent of storage in one schema: [UUIDs are Popular, but Bad for Performance](https://www.percona.com/blog/uuids-are-popular-but-bad-for-performance-lets-discuss/) (2019-11-22; DES-15).
- PlanetScale (InnoDB): fill can fall to about 50 percent with random keys, and storage relative to a 32-bit integer is 4x for `BINARY(16)` and 9x for `CHAR(36)`: [The Problem with Using a UUID Primary Key in MySQL](https://planetscale.com/blog/the-problem-with-using-a-uuid-primary-key-in-mysql) (2024-03-19).
- EDB (PostgreSQL benchmarks): random UUIDs cut throughput to under 30 percent of baseline in a medium dataset and raised WAL from about 2.5 GB to over 20 GB. PostgreSQL has no clustered table, so this cost is a real heap-engine effect from index scatter and full-page writes: [Sequential UUID Generators](https://www.enterprisedb.com/blog/sequential-uuid-generators) (2018-11-27; DES-16).
- PostgreSQL 18 adds a `uuidv7()` generator: [UUID Functions, section 9.14 (docs 18)](https://www.postgresql.org/docs/current/functions-uuid.html) (n.d.; PERF-15), [PostgreSQL 18 Release Notes](https://www.postgresql.org/docs/18/release-18.html) (2025-09-25; PERF-16).
- ULID is a 128-bit identifier with a 48-bit millisecond timestamp and 80 random bits: [ULID specification](https://github.com/ulid/spec) (n.d.).
- Distributed SQL advises the opposite for key position. Spanner warns against monotonic first key parts on high write-rate tables and recommends UUID version 4, with bit-reversal and hash prefixes as alternatives: [Schema design best practices](https://docs.cloud.google.com/spanner/docs/schema-design) (n.d.; CLOUD-11). CockroachDB names sequential keys as index-tail hotspots and recommends UUID keys or hash-sharded indexes: [Understand Hotspots](https://docs.cockroachlabs.com/docs/stable/understand-hotspots) (n.d.; PERF-48).
- No fetched source benchmarks UUIDv7 against bigint and UUIDv4 together on B-tree engines (note 11 gap).
### 4.5 Statements
- MANDATORY (OLTP): every base table declares a primary key. Independent grounding: Codd, PostgreSQL docs, InnoDB docs, Karwin.
- RECOMMENDED (DW, LAKE): every table has a declared logical key tested by the pipeline, since LAKE engines do not enforce it. dbt says each model has a primary key. Enforcement by test is [INFERENCE] here.
- RECOMMENDED (OLTP, single-node): 64-bit integer identity as the default generated key. 32-bit only for provably bounded lookup tables. Grounding: Rails, Django, Alibaba, Buildkite, and SQL Server's clustered key properties.
- MANDATORY (OLTP): a foreign key column has the same type and width as the key it references. Grounding: Buildkite incident, Karwin's mismatched-type foreign keys, and MySQL's rule that size and sign of fixed-precision types must match: [FOREIGN KEY Constraints](https://dev.mysql.com/doc/refman/8.4/en/create-table-foreign-keys.html) (n.d.; PGMY-14).
- RECOMMENDED (OLTP): monitor identifier consumption against range. Single-incident evidence (Buildkite).
- RECOMMENDED (OLTP, single-node, when global or client-generated uniqueness is needed): a time-ordered 128-bit identifier in the engine's native binary form, never as a text representation. Grounding: RFC 9562, Percona, PlanetScale, EDB. Record that it exposes creation time (RFC 9562, Percona, EDB).
- RECOMMENDED (range-sharded distributed SQL): do not lead keys with monotonic values. Use random UUIDs, bit-reversal or hash-sharding as the platform documents (Spanner, CockroachDB).
- MANDATORY (ALL): never reuse a retired key value, and do not fill key gaps. Grounding: Karwin (Pseudokey Neat-Freak); sequences are not rolled back by design (PostgreSQL).
- RECOMMENDED (OLTP): surrogate key plus a unique constraint on the natural key where a natural key exists. This meets both positions' integrity goals [INFERENCE].
- RECOMMENDED (OLTP): pure junction tables use the composite of their two foreign keys as primary key, unless the row is referenced elsewhere or has its own lifecycle. Grounding: Karwin, sqlstyle, Chen, IDEF1X. Citus-type distribution adds its own composite requirement (9.2).
- [METHOD-MANDATORY] (DW, Kimball dimensions): integer surrogates on every dimension except date; facts join only on them. Not a general DW rule, because Data Vault and dbt practice differ.
### 4.6 Universal vs engine-specific

| Point | Universal | Engine or topology specific |
|---|---|---|
| A declared identity per table | Yes for OLTP | Enforced in PostgreSQL only by choice; InnoDB synthesizes a hidden key; LAKE keys informational |
| Short key benefit | No | InnoDB and SQL Server clustered designs copy the key into secondary indexes; PostgreSQL has heap storage |
| Ordered inserts | No | Beneficial on single-node B-trees; harmful as a leading key on range-sharded systems |
| 128-bit native storage | Yes when UUIDs are used | `uuid` type in PostgreSQL, `BINARY(16)` in MySQL |
| Generators | No | Identity vs AUTO_INCREMENT vs `uuidv7()` |

### 4.7 Contested
- **Natural vs surrogate in OLTP.** For natural: prevents duplicates, carries meaning, avoids a lookup (Karwin's ID Required, sqlstyle's advice against bare `id`; Celko [UNVERIFIED]). For surrogate: natural keys change, get recycled, or are wide (Kimball's reasons, stated for the DW; Chen permits artificial attributes; ORM defaults). Context: the strongest published surrogate arguments are for warehouses. No source in the notes measures this for OLTP. Treat as OPTIONAL/CONTEXTUAL.
- **Warehouse key type.** Kimball integers vs dbt strings vs Data Vault hashes. Context: Kimball optimizes fact size and history; dbt targets ELT models with business keys; Data Vault targets parallel load without lookups.
- **UUID as primary key.** Against on single-node clustered engines (SQL Server's guide on 16-byte keys and missing ever-increasing property; MySQL's short-key advice; Percona; PlanetScale). For on range-sharded systems (Spanner, CockroachDB). The note authors call this the sharpest conflict in the corpus. UUIDv7 reintroduces the monotonic pattern that Spanner and CockroachDB warn against, so it is not a universal answer. Resolve by topology.
- **MySQL official position.** The widely repeated claim that random primary keys are bad in InnoDB rests on benchmarks. The official 8.4 pages read say only that primary-key-order inserts are faster and primary keys should be short (note 01).
### 4.8 Outdated
- 32-bit integer as a default generated key. Rails moved to bigint in 5.1.
- `serial` in new PostgreSQL schemas, per the wiki. The manual is neutral.
- `CHAR(36)` UUID storage.
- UUIDv1 for new keys (RFC 9562, Spanner).
- MySQL `UUID_TO_BIN` time-swap as a general answer: it assumes version 1 values per the manual: [Miscellaneous Functions](https://dev.mysql.com/doc/refman/8.4/en/miscellaneous-functions.html) (n.d.).
## 5. Referential integrity and constraints
**Scope: OLTP for enforcement rules. DW and LAKE substitutions are stated separately.**
### 5.1 Findings
- Haerder and Reuter's ACID consistency is defined through successful transactions, not a generic engine guarantee (section 10.1). For schema design this means invariants expressible as constraints should be declared, since the engine checks them at every isolation level, while read-then-write logic depends on the level [INFERENCE from note 12].
- PostgreSQL: a CHECK is satisfied when the expression is true or NULL. CHECK cannot reference other rows or tables. Foreign keys do not automatically index the referencing side. The default ON DELETE is NO ACTION. NO ACTION can be deferred, RESTRICT cannot. MATCH FULL changes how partly-NULL composite foreign keys are treated: [Constraints](https://www.postgresql.org/docs/current/ddl-constraints.html) (n.d.; PGMY-01).
- PostgreSQL deferral applies to UNIQUE, PRIMARY KEY, foreign key and EXCLUDE constraints. NOT NULL and CHECK are always immediate: [SET CONSTRAINTS](https://www.postgresql.org/docs/current/sql-set-constraints.html) (n.d.).
- MySQL/InnoDB: NO ACTION is equivalent to RESTRICT and is not deferred. SET DEFAULT is rejected. The referencing index is created automatically and can later be silently dropped if another index can serve. Foreign keys are not supported on user-partitioned InnoDB tables. Cascaded foreign key actions do not activate triggers: [FOREIGN KEY Constraints](https://dev.mysql.com/doc/refman/8.4/en/create-table-foreign-keys.html) (n.d.; PGMY-14), [Restrictions and Limitations on Partitioning](https://dev.mysql.com/doc/refman/8.4/en/partitioning-limitations.html) (n.d.; PGMY-16). CHECK is enforced from 8.0.16, and NULL or UNKNOWN passes: [CHECK Constraints](https://dev.mysql.com/doc/refman/8.4/en/create-table-check-constraints.html) (n.d.; PGMY-15).
- SQL Server: foreign keys enforce referential integrity and do not automatically create an index. Cascading actions are NO ACTION, CASCADE, SET NULL and SET DEFAULT: [Primary and foreign key constraints](https://learn.microsoft.com/en-us/sql/relational-databases/tables/primary-and-foreign-key-constraints) (2024-07-19; MSOM-02).
- Oracle: constraints can be deferrable, and constraint states include enable or disable with validate or novalidate: [Data Integrity](https://docs.oracle.com/en/database/oracle/oracle-database/26/cncpt/data-integrity.html) (n.d.). An unindexed foreign key can require a full table lock on parent change: [Indexes and Index-Organized Tables](https://docs.oracle.com/en/database/oracle/oracle-database/26/cncpt/indexes-and-index-organized-tables.html) (n.d.; PERF-24; served content was labelled Oracle AI Database 26).
- GitLab requires foreign keys for referencing columns, explicit ON DELETE on every foreign key, and an index added before the constraint. It treats application-level consistency as fallible, and prefers database cascade to ORM callbacks: [Foreign keys and associations](https://docs.gitlab.com/ee/development/database/foreign_keys/) (n.d.; DES-18).
- Alibaba forbids foreign keys and cascades in its MySQL guidelines, citing distributed high-concurrency clusters, cascade blocking and insertion cost: [Alibaba Java Coding Guidelines](https://alibaba.github.io/Alibaba-Java-Coding-Guidelines/) (n.d.; DES-22).
- PlanetScale documented operating without foreign key constraints on Vitess, citing locking, column change limits and multi-server splitting. Its alternatives keep the foreign key column, order operations in the application and clean orphans in small batches: [Operating without foreign key constraints](https://planetscale.com/docs/vitess/operating-without-foreign-key-constraints) (n.d.). It then built foreign key support, noting cascades are hidden from binlog consumers: [The challenges of supporting foreign key constraints](https://planetscale.com/blog/challenges-of-supporting-foreign-key-constraints) (2023-12-05; DES-17). General availability was unsharded only: [Foreign key constraints are now generally available](https://planetscale.com/blog/foreign-key-constraints-are-now-generally-available) (2024-02-16).
- gh-ost does not support foreign key constraints: [Requirements and limitations](https://github.com/github/gh-ost/blob/master/doc/requirements-and-limitations.md) (n.d.; project entry CASE-23 covers the repository).
- Citus requires primary and foreign keys to include the distribution column: [Multi-tenant Applications](https://docs.citusdata.com/en/stable/use_cases/multi_tenant.html) (n.d.; PERF-44).
### 5.2 Statements
- MANDATORY (OLTP system of record): declare primary key, foreign key, NOT NULL, unique and CHECK constraints in the database, unless the platform cannot enforce them. Independent grounding: PostgreSQL, SQL Server, GitLab, Karwin (Keyless Entry).
- MANDATORY (ALL engines with CHECK): pair a CHECK with NOT NULL when the rule must always hold, since CHECK passes on NULL. Grounding: PostgreSQL and MySQL manuals.
- MANDATORY (OLTP): every foreign key has an explicit, reviewed delete and update policy. Grounding: GitLab as a requirement; the semantic differences across engines (5.3) make an implicit default non-portable [INFERENCE].
- RECOMMENDED (OLTP): index referencing columns by default. See 8.4 for the label difference between notes.
- RECOMMENDED (OLTP) [INFERENCE]: CASCADE only for strict composition, RESTRICT or NO ACTION across aggregates, SET NULL only for optional relationships. The PostgreSQL catalog entry supports this split: CASCADE for dependent components, RESTRICT or NO ACTION for independent objects, SET NULL or SET DEFAULT for optional relationships (PGMY-01).
- RECOMMENDED (OLTP) [ENGINE: PostgreSQL, Oracle]: use deferrable constraints for cycles and bulk ordering. MySQL has no deferral. SQL Server deferral was not verified.
- OPTIONAL/CONTEXTUAL (OLTP): triggers for cross-table rules CHECK cannot express. PostgreSQL rules should not be used (wiki).
- CONTEXTUAL exception (sharded or online-DDL-constrained MySQL): where constraints are unavailable, require matching column types, indexed foreign key columns, scheduled small-batch orphan cleanup and a recorded risk acceptance. Drawn from PlanetScale's own mitigations. The risk acceptance is [INFERENCE].
- RECOMMENDED (DW, Kimball) [METHOD-MANDATORY]: fact-table foreign keys are never NULL; a default dimension row stands in: [Kimball Techniques](https://www.kimballgroup.com/wp-content/uploads/2013/08/2013.09-Kimball-Dimensional-Modeling-Techniques11.pdf) (2013; DWM-01).
- RECOMMENDED (LAKE): treat declared primary and foreign keys as documentation and enforce them by pipeline tests. Grounding: Databricks and Snowflake state these constraints are not enforced. Test requirement is [INFERENCE].
- OPTIONAL/CONTEXTUAL (DW): disable foreign key enforcement during loads and rely on ETL lookups. The notes label this a common practice without a dedicated fetched source [UNVERIFIED as a measured practice].
- Data Vault soft integrity: referential integrity is managed by housekeeping processes rather than enforced (note 06).
### 5.3 Universal vs engine-specific

| Behavior | PostgreSQL | MySQL/InnoDB | SQL Server | Oracle | LAKE (Databricks, Snowflake std.) |
|---|---|---|---|---|---|
| Foreign key enforced | Yes | Yes | Yes | Yes | No, informational |
| Referencing side auto-indexed | No | Yes, may be silently replaced | No | Not stated; index advised | n/a |
| NO ACTION deferrable | Yes | No, equals RESTRICT | Not verified | Deferrable states exist | n/a |
| SET DEFAULT | Yes | Rejected | Yes | Not captured | n/a |
| CHECK passes on NULL | Yes | Yes | Not captured | Not captured | CHECK enforced; NULL handling not captured |
| EXCLUDE | Yes | No | Not captured | Not captured | n/a |

Universal: CHECK cannot substitute for NOT NULL (shown for two engines; treat other engines as needing confirmation). Engine-specific: everything in the table's non-identical rows.

### 5.4 Contested
- **Foreign keys in the database vs in the application.** For the database: atomic enforcement under concurrency and no orphans (PostgreSQL, SQL Server, GitLab, Karwin). For the application: sharding, online-DDL shadow tables and insert cost (Alibaba, earlier PlanetScale, gh-ost). Context: the exceptions are infrastructure constraints in sharded MySQL. PlanetScale's move to build support is evidence of demand. It remains unsharded only, so the constraint on shards persists.
- **ON DELETE default.** GitLab uses CASCADE in nearly all cases. PlanetScale prefers NO ACTION and advises great care with CASCADE. Alibaba bans cascade update. Context: GitLab runs its own monolith on PostgreSQL with database-owned data; Alibaba and PlanetScale come from sharded MySQL. InnoDB cascades also bypass triggers and are invisible to binlog consumers.
- **DW foreign keys**: enforce, omit, or declare as informational. Context-dependent on engine.
### 5.5 Outdated
- PlanetScale documentation predating its foreign key support, if read as a statement that the platform cannot have them.
- MySQL treated as parsing CHECK without enforcement: enforced since 8.0.16.
- The Rails-era no-foreign-keys practice was not confirmed by any fetched source, so it is not presented as history here.
## 6. Naming conventions
**Scope: ALL for identifier safety. Style items are consistency requirements.**
### 6.1 Findings
- Identifier limits and folding differ per engine.

| Engine | Maximum length | Unquoted case handling |
|---|---|---|
| PostgreSQL | 63 bytes by default, longer names truncated | Folded to lower case, which the manual notes is incompatible with the standard's upper-case folding |
| MySQL 8.4 | 64 characters for most objects | Table-name case depends on file system and `lower_case_table_names`, fixed at initialization |
| SQL Server | 128 characters, 116 for local temporary tables | Follows database collation |
| Oracle | 128 bytes with COMPATIBLE at least 12.2, 30 bytes below | Interpreted as upper case |
| Snowflake | 255 characters, quoted or not | Unquoted stored and resolved in upper case; quoted case-sensitive |
| Databricks (Unity Catalog) | 255 characters for object names; a separate column-name limit was not confirmed | Case-insensitive when referenced |

Sources: [Lexical Structure](https://www.postgresql.org/docs/current/sql-syntax-lexical.html) (n.d.; PGMY-09), [Identifier Length Limits](https://dev.mysql.com/doc/refman/8.4/en/identifier-length.html) (n.d.), [Database identifiers](https://learn.microsoft.com/en-us/sql/relational-databases/databases/database-identifiers) (2026-04-08), [Database Object Names and Qualifiers](https://docs.oracle.com/en/database/oracle/oracle-database/23/sqlrf/Database-Object-Names-and-Qualifiers.html) (n.d.; MSOM-10), [Snowflake: Identifier Requirements](https://docs.snowflake.com/en/sql-reference/identifiers-syntax) (n.d.; ENG-20), [Databricks: SQL Names](https://docs.databricks.com/aws/en/sql/language-manual/sql-ref-names) (2026-11-02; ENG-30).

- PostgreSQL advises either always or never quoting a given name. Oracle does not recommend quoted object names: same sources. The PostgreSQL wiki recommends only a-z, 0-9 and underscore: [Don't Do This](https://wiki.postgresql.org/wiki/Don%27t_Do_This) (2024-11-21; PGMY-10).
- Style guides converge on lowercase snake_case and no reserved words: [SQL Style Guide](https://www.sqlstyle.guide/) (n.d.; DES-20), [dbt style](https://docs.getdbt.com/best-practices/how-we-style/1-how-we-style-our-dbt-models) (2026-09-10; LAKE-16), [Mozilla SQL Style Guide](https://docs.telemetry.mozilla.org/concepts/sql_style.html) (n.d.), [Alibaba](https://alibaba.github.io/Alibaba-Java-Coding-Guidelines/) (n.d.; DES-22). sqlstyle advises against Hungarian prefixes, and against a table sharing a column's name.
- dbt prescribes `<event>_at` in UTC, `<event>_date`, `is_` or `has_` prefixes, past-tense events, business terminology and consistent names across models.
- GitLab prescribes type-prefixed constraint names (`pk_`, `fk_`, `index_`, `unique_`, `check_`, `excl_`), reserves `_id` for real associations and uses `_xid` for third-party IDs: [Constraints naming conventions](https://docs.gitlab.com/ee/development/database/constraint_naming_convention/) (n.d.; DES-19), [Foreign keys and associations](https://docs.gitlab.com/ee/development/database/foreign_keys/) (n.d.; DES-18).
- Unnamed constraints receive generated names on SQL Server and MySQL: [Database identifiers](https://learn.microsoft.com/en-us/sql/relational-databases/databases/database-identifiers) (2026-04-08), [Identifier Length Limits](https://dev.mysql.com/doc/refman/8.4/en/identifier-length.html) (n.d.).
- ISO/IEC 11179-5:2015, Edition 3.0 (published 2015-03-18, JTC 1/SC 32), sets out principles and rules for developing naming conventions for concepts, data element concepts, conceptual domains, data elements and value domains. This is the abstract only: [ISO/IEC 11179-5:2015](https://webstore.iec.ch/publication/21986) (2015-03-18; GOV-08). A 4th edition is at DIS stage (note 08, search-returned). The object class, property and representation term form is **not in the abstract**. It is known from secondary sources ([Wikipedia: Representation term](https://en.wikipedia.org/wiki/Representation_term), n.d., and a state government standard reached by search) and from the 2004 committee draft below. Note 10 calls the 2005 edition current. Note 08 supersedes that.
- ISO/IEC FCD 11179-5, dated 2004-01-09, is a committee draft and was only partly downloaded: [ISO/IEC FCD 11179-5 committee draft](https://www.jtc1sc32.org/doc/N1051-1100/32N1073T-FCD11179-5_doc) (2004-01-09; THIN-08; partly downloaded draft). Its limits govern everything in this bullet. It is not the published standard, the 2005 and 2015 editions were not read, wording may have changed, and a fourth edition is reported in search results only. A naming convention covers scope, authority, semantic, syntactic, lexical and uniqueness rules. The scope [RAW] "of each naming convention represented in the MDR shall be documented", and likewise authority; semantic, syntactic, lexical and uniqueness rules "should be documented". Annex A is informative. Its example rule sets require one object class term, one property term and one representation term, for example "Cost Budget Period Total Amount". Lexical example: "Nouns are used in singular form only, unless the concept itself is plural." That concerns registry names of data elements, not table names, so reading it as support for singular tables would be [INFERENCE].
- The JTC 1/SC 32 page lists older editions, including 11179-5:2005, as freely available, but no download was obtained, and the current webstore free list could not be read: [JTC 1/SC 32 Freely Available Standards](https://jtc1sc32.org/free_standards.html) (n.d.; THIN-09).
- ISO/IEC 11179-3:2023 is the registry metamodel, catalog-listed but not fetched: [ISO/IEC 11179-3:2023](https://www.iso.org/standard/78915.html) (2023-01; GOV-09; url_verified false) [UNVERIFIED detail].
- Oracle does publish naming guidelines, which corrects the earlier statement that no vendor goes beyond identifier rules. RECOMMENDED [ENGINE: Oracle] [RAW]: "Use full, descriptive, pronounceable names" and "Use the same name to describe the same entity or attribute across tables." "Oracle does not recommend using quoted identifiers for database object names." MANDATORY [ENGINE: Oracle]: "Nonquoted identifiers cannot be Oracle SQL reserved words." Read from the 19c edition: [Oracle 19c SQL Reference: Database Object Names and Qualifiers](https://docs.oracle.com/en/database/oracle/oracle-database/19/sqlrf/Database-Object-Names-and-Qualifiers.html) (n.d., 19c; THIN-15). The Release 26 page was not separately compared for this wording.
- Framework and organization conventions:

| Source | Table name form | Label |
|---|---|---|
| Rails, [Active Record Basics](https://guides.rubyonrails.org/active_record_basics.html) (n.d.; THIN-10) | Plural snake_case (`book_clubs` for BookClub) | RECOMMENDED, Rails OLTP (overridable) |
| Django, [Django Model Meta options](https://docs.djangoproject.com/en/5.2/ref/models/options/) (n.d., v5.2; THIN-11) | App label plus lowercased class (`bookstore_book`) | RECOMMENDED, Django OLTP |
| EF Core, [EF Core: Indexes and constraints](https://learn.microsoft.com/en-us/ef/core/modeling/indexes) (n.d.; THIN-12) | Same name as the DbSet property, or class name if none. Commonly plural only by DbSet naming [INFERENCE] | RECOMMENDED, EF Core OLTP |
| Hibernate, [An Introduction to Hibernate 6](https://docs.hibernate.org/orm/6.6/introduction/html_single/) (n.d., version 6.6; THIN-04) | JPA-compliant implicit naming by default; pluggable strategies | OPTIONAL/CONTEXTUAL |
| Prisma, [Prisma: Database mapping](https://www.prisma.io/docs/orm/v7/prisma-schema/data-model/database-mapping) (n.d., v7 docs; THIN-13) | Model singular PascalCase recommended; `@@map` keeps plural snake_case tables, described as "A common approach" | RECOMMENDED, Prisma |
| GitLab, [GitLab: Foreign keys and associations](https://docs.gitlab.com/development/database/foreign_keys/) (n.d.; THIN-14) | Examples use plural (`projects`, `groups`); no explicit rule found | MANDATORY inside GitLab only (constraint name prefixes) |

- Neither PostgreSQL nor MySQL publishes a formal naming standard. MySQL's optimization page suggests simple column names under 18 characters (note 01). No official Google or Microsoft schema style guide was found.
- SQL standard: the manuals' descriptions of identifier folding are the only verified statements of standard behavior here. See 12.4 for ISO/IEC 9075 limits.
### 6.2 Statements
- MANDATORY (ALL): identifiers use a character set safe across the target engines: letters, digits and underscores, starting with a letter, not a reserved word, and no reliance on quoting or case. Grounding: PostgreSQL, Oracle and SQL Server manuals, plus style guides.
- MANDATORY (ALL): the convention is written down and applied consistently. Grounding: ISO/IEC 11179-5's scope exists for this purpose, and the 2004 draft says scope and authority "shall" be documented for registry conventions (draft text, registry scope only). Consistency is required by every style source.
- RECOMMENDED (ALL): lowercase snake_case. sqlstyle, dbt, Mozilla, Alibaba, GitLab and PostgreSQL wiki agree.
- RECOMMENDED (ALL): name constraints and indexes explicitly with type prefix, table and columns. Generated names differ per environment [INFERENCE for migration impact].
- RECOMMENDED (ALL): consistent semantic suffixes for keys, timestamps, dates and booleans. Strongest in analytics layers (dbt).
- RECOMMENDED (ALL): a documented maximum length tied to the engine set in use. 30 bytes only if legacy Oracle compatibility or sqlstyle's rule is adopted.
- RECOMMENDED (ALL): reserve `_id` for actual keys (GitLab) [single-organization convention].
- MANDATORY (ALL) [ENGINE items]: no `SYS_` or `ORA_` prefixes on Oracle. No `@` or `#` leading characters for permanent objects on SQL Server.
- OPTIONAL/CONTEXTUAL: an ISO 11179-style three-part name. Present as aligned with, not required by, the standard. Required only where a registry or regulator mandates it (note 08).
- OPTIONAL/CONTEXTUAL (ALL): singular or plural table names, with consistency required. The primary sources split and defaults follow each framework's mapping style. Linters treat it as configurable (Schemalint `name-inflection`, prisma-lint `model-name-grammatical-number`).
### 6.3 Universal vs engine-specific
Universal: safe character set, no reliance on quoted names, consistency. Engine-specific: length ceilings, case folding, reserved words, prefix prohibitions.

### 6.4 Contested
- **Singular vs plural.** Plural or collective: Rails, dbt, GitLab examples, sqlstyle, Prisma's statement of common database practice, and EF Core examples by DbSet convention [INFERENCE]. Singular: Alibaba forbids plurals, Django's default, Prisma's recommendation for model names, the 11179-5 draft's informative annex (data element names only), and a relational tradition attributed to Celko [UNVERIFIED]. No source links either to outcomes. Context: ORM default or house style.
- **Bare `id` vs `<object>_id`.** sqlstyle and dbt favor named keys. Rails and EF Core favor `id`. MySQL's optimization page favors short unprefixed names. Context: ORM use versus cross-model joining.
- **11179 names in practice.** Government registries mandate them. A list-archive critic called the results ugly and unusable (search summary, unfetched) [UNVERIFIED].
### 6.5 Outdated
- A 30-byte limit as a universal ceiling. It comes from Oracle before 12.2.
- `tbl_`-style prefixes.
- Citing ISO/IEC 11179-5:2005 as current.
## 7. Data types and precision
**Scope: ALL for exactness and instant semantics. Type names are engine-specific.**
### 7.1 Money and exact numerics
**Findings**
- PostgreSQL recommends `numeric` for monetary amounts and warns that floating-point types store approximations. It also says numeric arithmetic is much slower than integer or floating-point: [Numeric Types](https://www.postgresql.org/docs/current/datatype-numeric.html) (n.d.; PGMY-02).
- MySQL describes DECIMAL and NUMERIC as exact, for use where preservation of exact precision matters, such as money: [Fixed-Point Types](https://dev.mysql.com/doc/refman/8.4/en/fixed-point-types.html) (n.d.).
- SQL Server warns of rounding errors from truncation with `money` and `smallmoney` when values are used in calculations, and recommends `decimal` with at least four decimal places. It also says no currency information is stored with the symbol: [money and smallmoney](https://learn.microsoft.com/en-us/sql/t-sql/data-types/money-and-smallmoney-transact-sql) (2024-05-21; MSOM-03).
- Oracle advises specifying precision and scale for fixed-point numbers for integrity. A value exceeding scale is rounded and one exceeding precision errors: [Data Types](https://docs.oracle.com/en/database/oracle/oracle-database/26/sqlrf/Data-Types.html) (n.d.; MSOM-10).
- MongoDB's catalog entry states that binary floating point cannot represent exact decimal fractions and is unsuitable for monetary arithmetic, and points to a decimal type: MSOM-18, [Transactions (MongoDB)](https://www.mongodb.com/docs/manual/core/transactions/) (n.d.). Treat as a catalog annotation on a combined entry.
- Alibaba bans float and double for decimals: [Alibaba](https://alibaba.github.io/Alibaba-Java-Coding-Guidelines/) (n.d.; DES-22). sqlstyle limits floats to genuine floating-point math: [SQL Style Guide](https://www.sqlstyle.guide/) (n.d.; DES-20). Karwin lists FLOAT where exact precision is needed as Rounding Errors: [SQL Antipatterns, Vol. 1](https://pragprog.com/titles/bksap1/sql-antipatterns-volume-1/) (2022-10; DES-13).
- The PostgreSQL wiki rejects its `money` type because no currency is stored and output depends on locale: [Don't Do This](https://wiki.postgresql.org/wiki/Don%27t_Do_This) (2024-11-21; PGMY-10).
- ISO 4217 is maintained by SIX, which publishes List One, List Two and List Three free of charge, with a Minor Unit field. In the file dated 2026-09-17: JPY has 0 minor units, USD and EUR 2, KWD and BHD 3, CLF and UYW 4. BHD's numeric code is `048`, with a leading zero: [ISO 4217 List One](https://www.six-group.com/dam/download/financial-information/data-center/iso-currrency/lists/list-one.xml) (2026-09-17; DES-11), [SIX Data Standards](https://www.six-group.com/en/products-services/financial-information/data-standards.html) (n.d.; GOV-20).
- Lists change by amendment. Bulgaria adopts EUR effective 2026-01-01 and BGN moves to List Three (GOV-20). The ISO standard page returned 403, so the edition is not verified.

**Statements**
- MANDATORY (ALL): monetary values use an exact type or integer minor units, never binary floating point. Grounding: PostgreSQL, MySQL, Alibaba, sqlstyle, Karwin.
- MANDATORY (OLTP, DW multi-currency): an amount is stored with its currency, as an ISO 4217 alphabetic code. Grounding: PostgreSQL wiki and SQL Server note that the proprietary money types do not carry currency.
- RECOMMENDED (ALL): treat minor-unit scale as data-driven reference data, since minor units and code validity change by amendment (note 08).
- RECOMMENDED (OLTP, DW): store currencies in a reference table loaded from the SIX lists, effective-dated, since codes retire [INFERENCE from note 08].
- OPTIONAL/CONTEXTUAL (ALL): decimal amount vs integer minor units. If integer, mark it in the name, such as dbt's `price_in_cents`.
- RECOMMENDED (ALL): codes with leading zeros are strings. Direct evidence: `048`. Phone and postal identifiers are [INFERENCE]. No source states them directly.
- [INFERENCE, low confidence] Multi-currency columns need at least 4 decimal places (CLF, UYW; also SQL Server's four-place advice). No source states a scale for FX rates, unit prices or intermediate calculation, and this needs separate research.

**Contested**
- **Exact decimal vs dbt's float cast.** The dbt style guide says prices should be decimal currency, yet its staging example casts money with `(order_total / 100.0)::float`: [How we style our dbt models](https://docs.getdbt.com/best-practices/how-we-style/1-how-we-style-our-dbt-models) (2026-09-10; LAKE-16). The exact-decimal position has the weight of vendor manuals. The dbt example appears to be illustrative style in an analytics context and should not be taken as guidance on financial marts. It does show that the exact-decimal rule is not universally followed in ELT practice.
- **`CHAR(3)` currency code.** Note 10 suggests `CHAR(3)` or text with CHECK, while the PostgreSQL wiki says not to use `char(n)` even for fixed-length identifiers. Resolve by engine: three-character content rule universal, storage type engine-specific.
- **Proprietary money type.** Rejected by PostgreSQL wiki and warned against by Microsoft for calculation, but tolerated by the wiki for single-currency, whole-cent, add-and-subtract use.

**Outdated:** binary floating point for currency in new designs; hard-coding two decimals; treating a currency code list as static.

### 7.2 Time
**Findings**
- PostgreSQL stores `timestamp with time zone` as UTC and does not retain the original zone. It advises against `time with time zone`: [Date/Time Types](https://www.postgresql.org/docs/current/datatype-datetime.html) (n.d.; PGMY-03).
- The PostgreSQL wiki says to use `timestamptz` for points in time, not to store UTC in `timestamp`, and to use half-open ranges rather than BETWEEN: [Don't Do This](https://wiki.postgresql.org/wiki/Don%27t_Do_This) (2024-11-21; PGMY-10).
- MySQL TIMESTAMP is converted to UTC for storage and ends at 2038-01-19. DATETIME is not converted and reaches 9999: [DATE, DATETIME and TIMESTAMP](https://dev.mysql.com/doc/refman/8.4/en/datetime.html) (n.d.; PGMY-13).
- SQL Server says to avoid `datetime` for new work in favor of `date`, `time`, `datetime2` and `datetimeoffset`. There is no official statement choosing between `datetimeoffset` and UTC in `datetime2`: [datetime](https://learn.microsoft.com/en-us/sql/t-sql/data-types/datetime-transact-sql) (2026-06-29; MSOM-03 family).
- Oracle `DATE` includes time to the second and has no fractional seconds or zone. `TIMESTAMP WITH TIME ZONE` preserves zone information. `WITH LOCAL TIME ZONE` normalizes to the database zone: [Data Types](https://docs.oracle.com/en/database/oracle/oracle-database/26/sqlrf/Data-Types.html) (n.d.; MSOM-10).
- ISO 8601-1:2019 specifies representations as character strings for information interchange, including UTC-based time shifts. It is not a storage type standard. It excludes non-Gregorian calendars. Published 2019-03-25 and under revision: [ISO 8601-1:2019](https://isotc154.org/standards/iso-8601-1-2019) (2019-03-25; GOV-21).
- SQL:2011 temporal periods are closed-open, as reported by committee authors, with period definitions as table metadata (note 08). Clause text was not read.
- SQL Server temporal tables use `datetime2` period columns, UTC transaction begin times, and 9999-12-31 for open rows: [Temporal tables](https://learn.microsoft.com/en-us/sql/relational-databases/tables/temporal-tables) (2026-08-18; MSOM-04).

**Statements**
- MANDATORY (ALL): an instant is stored unambiguously relative to UTC, using a UTC-normalizing type where one fits the range, or a documented UTC convention. Grounding: PostgreSQL docs and wiki, MySQL docs, dbt.
- RECOMMENDED (ALL): calendar dates use a date type, and event columns follow a consistent naming pattern (dbt).
- RECOMMENDED (ALL): query intervals are half-open. Grounding: PostgreSQL wiki and SQL:2011 closed-open periods.
- RECOMMENDED (ALL interchange): exchange date-time as ISO 8601 strings. This does not govern storage.
- RECOMMENDED (OLTP) [INFERENCE]: where a local wall-clock time or source zone has business meaning, store it separately, since normalization discards it (PostgreSQL states the zone is not retained). No source covers future-dated local events specifically.
- [ENGINE] MySQL: TIMESTAMP's 2038 ceiling is a constraint on long-lived instants. DATETIME needs an application-level UTC convention (note 01).

**Contested:** PostgreSQL's manual advises and the wiki goes further, saying not to use `timestamp` without zone except for abstract application-handled values. SQL Server leaves a UTC-versus-offset choice open.

**Outdated:** SQL Server `datetime`; `timetz` and `CURRENT_TIME` in PostgreSQL; `BETWEEN` on timestamps.

### 7.3 Text
**Findings**
- PostgreSQL: no performance difference among `text`, `varchar` and `char(n)` apart from padding storage. `char(n)` is usually slowest. Avoid invented length limits: [Character Types, section 8.3 (docs 18)](https://www.postgresql.org/docs/current/datatype-character.html) (n.d.).
- The PostgreSQL wiki also says `char(n)` silently pads and can prevent index use with text parameters, and `varchar(n)` by default risks production errors: [Don't Do This](https://wiki.postgresql.org/wiki/Don%27t_Do_This) (2024-11-21; PGMY-10).
- MySQL recommends the smallest efficient types, supports prefix indexes for long strings, and says joined columns should share character set and type: [Optimizing Data Size](https://dev.mysql.com/doc/refman/8.4/en/data-size.html) (n.d.), [How MySQL Uses Indexes](https://dev.mysql.com/doc/refman/8.4/en/mysql-indexes.html) (n.d.). It recommends utf8mb4 for all new applications and has deprecated utf8mb3: [The utf8mb3 Character Set](https://dev.mysql.com/doc/refman/8.4/en/charset-unicode-utf8mb3.html) (n.d.).
- Alibaba: `varchar` length up to 5000, text beyond that, ideally in a separate table.
- SQL Server: `nvarchar(n)` counts byte-pairs, not characters: [nchar and nvarchar](https://learn.microsoft.com/en-us/sql/t-sql/data-types/nchar-and-nvarchar-transact-sql) (2024-06-06; MSOM-03 family).
- Oracle says to use VARCHAR2 rather than VARCHAR (MSOM-10).

**Statements**
- RECOMMENDED [ENGINE: PostgreSQL]: `text` plus CHECK for real business limits. Avoid `char(n)`.
- CONTEXTUAL [ENGINE: MySQL]: bounded `varchar`, with very long values in `text`, considering row format and index limits.
- RECOMMENDED (ALL): use one Unicode-capable encoding, utf8mb4 on MySQL. [Single-engine evidence for the specific name.]
- MANDATORY (OLTP): joined columns have matching type and, where relevant, character set. Grounding: MySQL docs and Karwin's mismatched data types.

**Contested:** sizing philosophy between PostgreSQL and MySQL. Engine storage models differ, so the framework needs engine annexes (note 01).

**Outdated:** `char(n)` for performance on PostgreSQL; utf8mb3.

### 7.4 Booleans, enumerations, JSON, large objects
**Findings**
- PostgreSQL enums cannot have values removed without re-creating the type: [Enumerated Types](https://www.postgresql.org/docs/current/datatype-enum.html) (n.d.).
- MySQL ENUM values are stored as indexes, sort by index, and invalid input in non-strict mode becomes an empty string: [The ENUM Type](https://dev.mysql.com/doc/refman/8.4/en/enum.html) (n.d.).
- Karwin lists restricting values in the column definition as 31 Flavors. The table of contents shows only Antipattern: Specify Values in the Column Definition and Solution: Specify Values in Data (note 22), at heading level. The remedy's detail is unverified against the book.
- GitLab shows a CHECK-constrained plain column: `check_projects_type_enum` in [Constraints naming conventions](https://docs.gitlab.com/ee/development/database/constraint_naming_convention/) (n.d.; DES-19).
- PostgreSQL prefers `jsonb` for most applications. It advises keeping JSON documents small and atomic, because any update locks the whole row: [JSON Types, section 8.14 (docs 18)](https://www.postgresql.org/docs/current/datatype-json.html) (n.d.; PGMY-04).
- SQL:2016 added SQL/JSON functions without a JSON type. SQL:2023 added a JSON type as feature T801, per community and committee-derived sources (Wikipedia, modern-sql.com; note 08). JSON indexing differs: PostgreSQL GIN versus MySQL generated columns or multi-valued indexes (note 01).
- Karwin's Phantom Files concerns assuming bulky media must be external. Only the publisher description was read.

**Statements**
- RECOMMENDED (OLTP): lookup tables with foreign keys for value sets that change or need attributes. Grounding: [INFERENCE] from PostgreSQL enum limits and MySQL pitfalls. Treat as a default, not Karwin's stated remedy.
- OPTIONAL/CONTEXTUAL (OLTP): native enums for truly static sets; CHECK as a middle path.
- RECOMMENDED (OLTP): JSON only for semi-structured or externally defined atoms. Keys, money and filtered or aggregated attributes remain relational. Grounding: PostgreSQL docs, single-vendor on the rationale.
- OPTIONAL/CONTEXTUAL (LAKE): semi-structured Bronze capture (note 04).
- OPTIONAL/CONTEXTUAL (ALL): large objects in-database versus object store, decided by size and lifecycle [INFERENCE].
- RECOMMENDED (OLTP): native boolean where available; on MySQL use `is_` with `tinyint` (Alibaba). The claim that `CHAR(1)` flags are an antipattern has **no source** in the notes and is not asserted.

**Contested:** enum vs lookup table vs CHECK. JSON as replacement for EAV is [INFERENCE] in note 10; sqlstyle instead points to specialist products.

**Outdated:** none established by the notes.

### 7.5 NULL
**Findings**
- PostgreSQL unique constraints treat NULLs as distinct by default, changeable with `NULLS NOT DISTINCT`, and the manual calls default NULL treatment implementation-defined per the standard: [Constraints](https://www.postgresql.org/docs/current/ddl-constraints.html) (n.d.; PGMY-01). MySQL 8.4 unique indexes permit multiple NULLs [WF]: [CREATE INDEX](https://dev.mysql.com/doc/refman/8.4/en/create-index.html) (n.d.; ENG-05). SQL Server allows only one NULL per column in a UNIQUE constraint [WF]: [SQL Server: Unique constraints and check constraints](https://learn.microsoft.com/en-us/sql/relational-databases/tables/unique-constraints-and-check-constraints) (2023-12-29; ENG-10). Oracle [WF]: a row with NULLs in all key columns satisfies the constraint, while two rows with NULLs in some key columns and the same values in the others violate it: [Oracle SQL Reference: constraint](https://docs.oracle.com/en/database/oracle/oracle-database/23/sqlrf/constraint.html) (n.d., page reports 26; ENG-15). Filters cannot apply to SQL Server UNIQUE constraints but can apply to unique indexes; a unique filtered index tolerating many NULLs is [INFERENCE], since `CREATE INDEX` was not opened. Databricks treats NULLs as distinct in its preview UNIQUE (LAKE-02). SQL:2023 adds UNIQUE null treatment as optional feature F292 (note 08, Wikipedia citing a post whose URL failed).
- PostgreSQL's catalog entry says most columns should be NOT NULL (PGMY-01). MySQL says to declare columns NOT NULL where possible: [Optimizing Data Size](https://dev.mysql.com/doc/refman/8.4/en/data-size.html) (n.d.).
- A foreign key with any NULL referencing column escapes the check unless MATCH FULL is used (PGMY-01).
- The wiki says to avoid `NOT IN` because of NULL behavior and poor plans: [Don't Do This](https://wiki.postgresql.org/wiki/Don%27t_Do_This) (2024-11-21; PGMY-10).
- Codd's split of missing information into applicable and inapplicable kinds is documented by a paper title and metadata only: [SIGMOD Record archive](https://sigmodrecord.org/1987/03/08/more-commentary-on-missing-information-in-relational-databases-applicable-and-inapplicable-information/) (1987-03-08). Date's opposition to NULL is from low-authority search results [UNVERIFIED].
- Kimball says aggregates handle NULL facts gracefully but foreign keys must not be NULL (note 06), and criticizes real dates meaning unknown: [Surrogate Keys](https://www.kimballgroup.com/1998/05/surrogate-keys/) (1998-05-02; DES-12).

**Statements**
- MANDATORY (ALL): primary key columns are NOT NULL. Engines force it.
- RECOMMENDED (OLTP): NOT NULL by default, with a documented meaning for each nullable column. Grounding: PostgreSQL, MySQL, Kent's blank-field ambiguity.
- RECOMMENDED (OLTP, DW): decide explicitly how unique constraints treat NULLs, and never assume portability. SQL Server (one), MySQL and PostgreSQL by default (many), and Oracle (composite-specific) differ. The SQL Server, MySQL and Oracle behaviours are [WF] and need re-checking before use.
- MANDATORY (ALL): do not use an ordinary in-domain value to mean unknown. Grounding: Kimball's criticism and MySQL's silent empty-string behavior as a cautionary case. Note 10's list of specific literals is broader than its evidence.
- RECOMMENDED (query layer, ALL): `NOT EXISTS` over `NOT IN` where NULLs can appear.
- [METHOD-MANDATORY] (DW, Kimball): default dimension rows in place of NULL foreign keys.

**Universal vs engine-specific:** NULL distinctness in unique constraints is engine-specific. CHECK passing on NULL is shown for PostgreSQL and MySQL.

**Contested**
- **NULL vs no NULL.** Codd's marks, Date's rejection (both [UNVERIFIED] as to content) and SQL's single NULL.
- **Open-ended period terminators.** Note 10 lists `9999-12-31` as a banned sentinel. SQL Server's own temporal tables use it for open rows, while dbt snapshots use NULL or a configurable current value (note 04). Resolution [INFERENCE]: the ban concerns values standing in for unknown data; an engine-managed or documented end-of-time convention on a period column is a different case and must be declared.

**Outdated:** none beyond MySQL non-strict mode's silent coercion.
## 8. Indexing and query performance
**Scope: each statement is tagged. OLTP and OLAP physical advice must not be merged.**
### 8.1 Findings: types and structures
- B-tree is the default and supports equality, range, sort and anchored prefix searches: [Index Types](https://www.postgresql.org/docs/current/indexes-types.html) (n.d.; PGMY-05), [Comparison of B-Tree and Hash Indexes](https://dev.mysql.com/doc/refman/8.4/en/index-btree-hash.html) (n.d.; PERF-19).
- Hash indexes are equality-only in PostgreSQL and MySQL. SQL Server hash indexes are for memory-optimized tables with bucket sizing: [Index Design Guide](https://learn.microsoft.com/en-us/sql/relational-databases/sql-server-index-design-guide) (2026-09-14; MSOM-01).
- Oracle bitmap indexes suit warehouses and low-cardinality, rarely modified columns, and are inappropriate for many OLTP applications because DML locks many rows: [Indexes and IOTs](https://docs.oracle.com/en/database/oracle/oracle-database/26/cncpt/indexes-and-index-organized-tables.html) (n.d.; PERF-24). Independently: [One Size Fits All](https://cs.brown.edu/~ugur/fits_all.pdf) (2005; PERF-38).
- Columnstore indexes are the SQL Server standard for large fact tables, with vendor-stated gains up to tenfold in query speed and compression: [Columnstore overview](https://learn.microsoft.com/en-us/sql/relational-databases/indexes/columnstore-indexes-overview) (2026-09-14; PERF-02).
- Cloud warehouses replace B-trees with pruning and clustering: [Introduction to partitioned tables](https://docs.cloud.google.com/bigquery/docs/partitioned-tables) (n.d.; CLOUD-13), [Clustering Keys](https://docs.snowflake.com/en/user-guide/tables-clustering-keys) (n.d.; LAKE-10).
- LSM engines trade write, space and read amplification by compaction style: [RocksDB Overview](https://github.com/facebook/rocksdb/wiki/RocksDB-Overview) (2023-07-18; PERF-42). DDIA chapter-level comparisons were not readable and are not relied on [UNVERIFIED]. Book existence only: [DDIA 2nd edition announcement](https://martin.kleppmann.com/2026/03/24/designing-data-intensive-applications-2e.html) (2026-03; PERF-41).
### 8.2 Findings: composite order, covering, partial, expression
- Leading-column mechanics are vendor-documented: [Multicolumn Indexes](https://www.postgresql.org/docs/current/indexes-multicolumn.html) (n.d.; PERF-06), [Multiple-Column Indexes](https://dev.mysql.com/doc/refman/8.4/en/multiple-column-indexes.html) (n.d.; PERF-18). PostgreSQL says multicolumn indexes should be used sparingly and that more than three columns are rarely helpful.
- MongoDB's guideline places equality first, then sort, then range, with range before sort when the range is very selective: [The ESR Guideline](https://www.mongodb.com/docs/manual/tutorial/equality-sort-range-guideline/) (n.d.; MSOM-17).
- Winand rejects most-selective-first, keeping selectivity relevant only among independent range conditions, and cites Harrison, Lewis and Shaw: [Myth: Most Selective First](https://use-the-index-luke.com/sql/myth-directory/most-selective-first) (n.d.; PERF-34).
- PostgreSQL 18 adds B-tree skip scan, which relaxes the leading-column requirement in some cases: [Release Notes](https://www.postgresql.org/docs/18/release-18.html) (2025-09-25; PERF-16).
- Covering: SQL Server advises included columns for non-predicate needs and warns against too-wide indexes (MSOM-01). PostgreSQL says payload columns help only if the table changes slowly enough that index-only scans skip the heap: [Index-Only Scans and Covering Indexes](https://www.postgresql.org/docs/current/indexes-index-only-scans.html) (n.d.; PERF-07).
- Partial and filtered: useful for small subsets on PostgreSQL and SQL Server. PostgreSQL warns that sets of non-overlapping partial indexes are a poor substitute for partitioning: [Partial Indexes](https://www.postgresql.org/docs/current/indexes-partial.html) (n.d.; PERF-08).
- Functions on columns defeat ordinary indexes unless an expression index matches. MySQL and SQL Server use generated or computed columns: [Case-Insensitive Search](https://use-the-index-luke.com/sql/where-clause/functions/case-insensitive-search) (n.d.; PERF-36).
- MySQL cannot use a string column's index when comparing it to a number: [Type Conversion in Expression Evaluation](https://dev.mysql.com/doc/refman/8.4/en/type-conversion.html) (n.d.; PERF-23).
### 8.3 Findings: cost, plans and access patterns
- Index cost on writes appears across PostgreSQL, MySQL, SQL Server, Oracle and MongoDB: [Indexes Introduction](https://www.postgresql.org/docs/current/indexes-intro.html) (n.d.; PERF-09), [Optimization and Indexes](https://dev.mysql.com/doc/refman/8.4/en/optimization-indexes.html) (n.d.; PERF-17), MSOM-01, PERF-24, [MongoDB Indexes](https://www.mongodb.com/docs/manual/indexes/) (n.d.; PERF-27). SQL Server names speculative indexing as a common mistake.
- No fetched source gives a numeric maximum of indexes per OLTP table.
- Fill factor: PostgreSQL B-tree default 90. Lower values smooth page splits on write-heavy tables: [CREATE INDEX](https://www.postgresql.org/docs/current/sql-createindex.html) (n.d.; PERF-10).
- Invisible indexes allow drop-testing in Oracle and MySQL: [Invisible Indexes](https://dev.mysql.com/doc/refman/8.4/en/invisible-indexes.html) (n.d.; PERF-20). PostgreSQL has none natively. HypoPG provides hypothetical indexes: [Usage](https://hypopg.readthedocs.io/en/latest/usage.html) (n.d.; PERF-53).
- Statistics and EXPLAIN: PostgreSQL planner estimates depend on ANALYZE. EXPLAIN ANALYZE really executes, so side effects occur: [Using EXPLAIN](https://www.postgresql.org/docs/current/using-explain.html) (n.d.; PERF-13).
- N+1 query patterns from ORMs multiply round trips: [Nested Loops and the N+1 Problem](https://use-the-index-luke.com/sql/join/nested-loops-join-n1-problem) (n.d.; PERF-37).
- Keyset pagination fetches following rows after the last seen entry, while OFFSET counts from the start. Keyset cannot jump to arbitrary pages and requires a deterministic sort: [Fetching the Next Page](https://use-the-index-luke.com/sql/partial-results/fetch-next-page) (n.d.; PERF-35).
- Materialized views: Oracle query rewrite offers freshness modes including a stale-tolerant one with a risk of inaccurate results: [Basic Query Rewrite](https://docs.oracle.com/en/database/oracle/oracle-database/26/dwhsg/basic-query-rewrite-materialized-views.html) (n.d.; PERF-26).
- Hints: the PostgreSQL community argued against hints in 2015 for maintainability and upgrade reasons: [OptimizerHintsDiscussion](https://wiki.postgresql.org/wiki/OptimizerHintsDiscussion) (2015-07-05; PERF-55). Oracle and SQL Server hint cautions were not fetched.
- Prepared statements: PostgreSQL moves to a generic plan after five custom executions when costs allow: [PREPARE](https://www.postgresql.org/docs/current/sql-prepare.html) (n.d.; PERF-14). Transaction-pooling restrictions apply under PgBouncer: [Features](https://www.pgbouncer.org/features.html) (n.d.; PERF-52).
### 8.4 Statements
- RECOMMENDED (OLTP): a few narrow indexes aimed at critical queries, driven by observed predicates. Grounding: SQL Server, MySQL, PostgreSQL, Oracle, Karwin's Index Shotgun.
- RECOMMENDED (OLTP): add a unique constraint or index when data is unique, since it gives the optimizer information and enforces integrity. Grounding: SQL Server and PostgreSQL.
- RECOMMENDED (ALL B-tree composite indexes): lead with equality columns, then consider sort and range, prioritizing prefix reuse by query patterns. Grounding: PostgreSQL, MySQL, MongoDB, Winand.
- RECOMMENDED (OLTP; PostgreSQL and Oracle) and automatic on InnoDB: index foreign key columns used in joins or whose parents see deletes or updates. **Label reconciliation:** note 10 labels this MANDATORY based on GitLab. Note 11 labels it RECOMMENDED because PostgreSQL's manual explicitly says it is not always needed. This document follows note 11 for the general statement, while GitLab's rule stands as one organization's mandate. On InnoDB it is engine-enforced.
- MANDATORY (ALL): predicates compare matching types. Grounding: MySQL docs and PostgreSQL wiki's parameter type issue.
- MANDATORY (ALL engines with cost-based optimizers): statistics are kept current and plans checked against observed behavior. Grounding: PostgreSQL, SQL Server, Oracle docs.
- RECOMMENDED (OLTP): execute joins in the database and avoid N+1 (Winand). Single practitioner source, mechanics corroborated by vendor round-trip logic [INFERENCE].
- RECOMMENDED (OLTP): keyset pagination for deep or infinite paging; OFFSET acceptable for shallow random access.
- RECOMMENDED (ALL): retrieve only needed columns. There is no vendor mandate against `SELECT *`. Support is indirect through covering indexes and columnstore mechanics.
- RECOMMENDED (OLAP, DW): columnar storage for large fact tables, bitmap indexes on low-cardinality columns where offered, and materialized views with rewrite.
- OPTIONAL/CONTEXTUAL (LAKE, cloud DW): date partitioning and clustering on filter columns. Snowflake targets multi-terabyte tables and warns of credit cost.
- OPTIONAL/CONTEXTUAL (OLTP): partial, expression and covering indexes when justified by a named query.
- RECOMMENDED (ALL): hints are a last resort with a review obligation [INFERENCE from PostgreSQL community reasoning, dated 2015].
- OPTIONAL (OLTP): test index removal with invisible or hypothetical tools before dropping.
### 8.5 Universal vs engine-specific
Universal: the read and write trade-off, leading-prefix logic on B-trees, cost-based planning, write cost of indexes. Engine-specific: clustered versus heap storage, foreign key auto-indexing, INCLUDE syntax and payoff, bitmap and columnstore availability, invisible index support, hash index role, skip scan. Note: PostgreSQL has no clustered table in the SQL Server or InnoDB sense [INFERENCE from its index-only scan docs].

### 8.6 Contested
- **Most selective column first.** Winand and those he cites reject it. No vendor page read recommends it. Residual truth exists for SQL Server statistics on the first key column (per Winand) and for range conditions. Note 01 states a most-used and low-cardinality first heuristic from a PostgreSQL example. That example is about one `(category, data)` index replacing many partial indexes, and is not a general rule.
- **Clustering-key order.** Snowflake recommends lowest cardinality first, the inverse of the folk B-tree rule. The mechanism (micro-partition pruning) differs, so it does not transfer to B-trees.
- **Covering breadth.** SQL Server encourages adding included columns. PostgreSQL is cautious and disables deduplication for INCLUDE indexes.
- **Materialized views in OLTP.** See 3.4.
- **Autotuning and hints**: thin evidence.
### 8.7 Outdated
- Most-selective-first. Lewis called it a poor rule of thumb in 2007, per Winand.
- PostgreSQL's strict leading-column requirement as absolute, given PostgreSQL 18 skip scan.
- The 2015 hints page as a current community position. It predates current `pg_hint_plan` usage and was not re-validated.
## 9. Partitioning and scaling
**Scope: partitioning within a node is separate from distribution across nodes. Do not conflate them.**
### 9.1 Findings: partitioning
- All relational vendors offer range, list and hash forms: [Table Partitioning](https://www.postgresql.org/docs/current/ddl-partitioning.html) (n.d.; PGMY-06), [Partitioned Tables and Indexes](https://learn.microsoft.com/en-us/sql/relational-databases/partitions/partitioned-tables-and-indexes) (2025-12-29; PERF-03), [Partitioning Concepts](https://docs.oracle.com/en/database/oracle/oracle-database/26/vldbg/partition-concepts.html) (n.d.; MSOM-11).
- PostgreSQL requires unique and primary keys on partitioned tables to include all partition key columns, and says a table should typically exceed physical memory before partitioning is worthwhile. It reports planners handling up to a few thousand partitions when most are pruned, and warns that too many increase planning time and memory.
- SQL Server says partitioning rarely improves OLTP query performance and can add overhead when queries span many partitions. It advises avoiding many hundreds or thousands of partitions unless needed, supports up to 15,000, and requires unique index keys to contain the partitioning column for alignment.
- MySQL requires partition key columns in every unique key, and does not support foreign keys on user-partitioned InnoDB tables: [Restrictions and Limitations on Partitioning](https://dev.mysql.com/doc/refman/8.4/en/partitioning-limitations.html) (n.d.; PGMY-16).
- Oracle leads with performance, cites a case of about 100 times faster with pruning and says tables over 2 GB should be considered candidates. It recommends global indexes for OLTP and local indexes for decision support.
- Dropping or detaching a partition avoids bulk delete costs, including VACUUM overhead (PostgreSQL). BigQuery offers partition expiration (CLOUD-13).
### 9.2 Findings: distribution and scale-out
- Vertical scaling fits workloads that do not divide easily, and horizontal scaling fits those that do. Databases need careful design to scale out: [Optimize scaling and partitioning](https://learn.microsoft.com/en-us/azure/well-architected/performance-efficiency/scale-partition) (2023-11-15; PERF-58).
- MongoDB's shard key criteria are high cardinality, even frequency and non-monotonic values, with hashed sharding for monotonic keys. Queries without the shard key go to all shards and do not scale linearly: [Choose a Shard Key](https://www.mongodb.com/docs/manual/core/sharding-choose-a-shard-key/) (n.d.; PERF-30), [Shard Keys](https://www.mongodb.com/docs/manual/core/sharding-shard-key/) (n.d.; PERF-29).
- Citus advises distribution by tenant or entity ID, co-location, reference tables for small dimensions, and not choosing a timestamp as the distribution column: [Choosing Distribution Column](https://docs.citusdata.com/en/stable/sharding/data_modeling.html) (n.d.; PERF-43), [Multi-tenant Applications](https://docs.citusdata.com/en/stable/use_cases/multi_tenant.html) (n.d.; PERF-44).
- Vitess uses a unique Primary Vindex, with secondary vindexes to avoid scatter, and supports resharding with brief read-only cutover: [Sharding](https://vitess.io/docs/22.0/reference/features/sharding/) (2026-04-30; PERF-45), [Vindexes](https://vitess.io/docs/22.0/reference/features/vindexes/) (2026-04-30; PERF-46).
- Spanner and CockroachDB warn against monotonic keys (section 4.4). CockroachDB states that hash-sharding spreads writes but makes range reads scan every shard.
- Read replicas and causal guarantees: MongoDB states majority read and write concerns are needed for all causal consistency guarantees: [Causal Consistency and Read and Write Concerns](https://www.mongodb.com/docs/manual/core/causal-consistency-read-write-concerns/) (n.d.; PERF-31). Jepsen found RDS PostgreSQL multi-AZ reader endpoints did not ensure Snapshot Isolation, recommending the writer endpoint for safety-critical reads: [Amazon RDS for PostgreSQL 17.4](https://jepsen.io/analyses/amazon-rds-for-postgresql-17.4) (2025-04-29).
- Pooling: PgBouncer transaction mode disables session-level features such as session advisory locks and SQL-level PREPARE: [Features](https://www.pgbouncer.org/features.html) (n.d.; PERF-52). ProxySQL was not fetched.
- Caching: cache-aside does not guarantee consistency and works best for relatively static, frequently read data: [Cache-Aside Pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/cache-aside) (2025-09-11; PERF-57).
- HTAP: see 3.2.
### 9.3 Statements
- MANDATORY (ALL relational partitioning, as engine constraints): partition key columns are included in unique and primary keys, or uniqueness is enforced by a documented alternative. PostgreSQL and MySQL state it. SQL Server's rule is alignment-based, with nonaligned indexes as the alternative. Oracle's global index is another alternative.
- RECOMMENDED (ALL): partition for retention, maintenance and pruning on the dominant filter on very large tables.
- RECOMMENDED (OLTP): do not partition to speed up point lookups. Grounding: SQL Server directly, PostgreSQL's conditions.
- RECOMMENDED (ALL): keep partition counts bounded and evidence-based. Hard numbers are engine-specific.
- RECOMMENDED (distributed OLTP): choose a shard key present in nearly every transaction, with high cardinality and even frequency, not time-ordered. Grounding: MongoDB, Citus, Vitess, Spanner, CockroachDB.
- MANDATORY [ENGINE: Citus]: distribution column inside primary and foreign keys.
- RECOMMENDED (distributed OLTP): plan sharding early. Azure WAF says partitioning as an afterthought is harder.
- RECOMMENDED (OLTP with replicas): route read-your-writes and safety-critical reads to the writer, or use engine guarantees. Grounding: Jepsen, MongoDB.
- OPTIONAL/CONTEXTUAL (OLTP): CQRS, cache-aside, and pooling with documented feature limits. CQRS is explicitly unsuited to simple CRUD.
### 9.4 Universal vs engine-specific
Universal: uniqueness and partition key coupling (mechanism differs), pruning requires predicates on the partition key, shard-key selection criteria. Engine-specific: partition counts, global indexes (Oracle), filegroups and partition schemes (SQL Server), foreign key compatibility.

### 9.5 Contested
- **Time as a key.** Good range partition key inside a node (Oracle, PostgreSQL, BigQuery), poor distribution key across nodes (Citus, Spanner, CockroachDB). Same column, different mechanism.
- **Hashed vs ranged distribution.** Hashing spreads writes and destroys range locality (MongoDB, CockroachDB).
- **Partition for performance.** Oracle emphasizes performance benefits. SQL Server and PostgreSQL subordinate performance to manageability. Oracle's example involves large historical tables with pruning, which is DSS-oriented.
- **Partition thresholds.** Oracle's 2 GB and PostgreSQL's physical-memory rule of thumb. Neither is universal.
- **Scatter-gather.** A liability in OLTP but useful for large aggregations (MongoDB).
- **NoSQL for scale.** Documented SQL scale-out (Vitess, Citus, Spanner, CockroachDB) undercuts the claim. Scale comes from key and co-location design.
### 9.6 Outdated
- Oracle's 2 GB candidate threshold, read as a modern default. It is dated relative to current memory sizes [INFERENCE].
- Partial index sets as a partitioning substitute.
- PostgreSQL inheritance-based partitioning, replaced by declarative partitioning (wiki).
## 10. Transaction management
**Scope: OLTP unless stated. OLAP and LAKE transaction semantics are outside the notes used.**
### 10.1 ACID
- Gray defines a transaction with three properties [PDF]: "A transaction is a transformation of state which has the properties of atomicity (all or nothing), durability (effects survive failures) and consistency (a correct transformation)." The term ACID does not appear: [The Transaction Concept](https://jimgray.azurewebsites.net/papers/thetransactionconcept.pdf) (1981-06; TXN-01).
- Haerder and Reuter name ACID and define consistency through successful transactions [PDF]: "a database is consistent if and only if it contains the results of successful transactions": [Principles of Transaction-Oriented Database Recovery](https://www.cs.utexas.edu/~dsb/cs386d/Readings/Recovery/Principles-of-Recovery.pdf) (1983-12; TXN-02).
- Both describe compensating actions for bad transactions, which is the lineage of sagas [INFERENCE].
- Brewer separates ACID consistency (integrity rules such as unique keys) from CAP consistency (single-copy): [CAP Twelve Years Later](https://www.infoq.com/articles/cap-twelve-years-later-how-the-rules-have-changed/) (2012-05-30; TXN-15).
- The claim attributed to DDIA that the C does not really belong in ACID was **not** verified against the book and is not relied on. Kleppmann's verifiable position is that most so-called ACID databases do not protect against race conditions by default: [Hermitage: Testing the I in ACID](https://martin.kleppmann.com/2014/11/25/hermitage-testing-the-i-in-acid.html) (2014-11-25).
### 10.2 Isolation
**Findings**
- The ANSI phenomena were shown to be ambiguous. Berenson et al. add dirty write (P0), lost update (P4), read skew (A5A), write skew (A5B) and define Snapshot Isolation, which is incomparable with Repeatable Read [PDF]: "Snapshot Isolation histories prohibit histories with anomaly A3, but allow A5B": [A Critique of ANSI SQL Isolation Levels](https://www.microsoft.com/en-us/research/wp-content/uploads/2016/02/tr-95-51.pdf) (1995-06; TXN-03).
- PostgreSQL's SSI cost less than 7% relative to SI in the paper's workloads [PDF]: [Serializable Snapshot Isolation in PostgreSQL](https://drkp.net/papers/ssi-vldb12.pdf) (2012-08; TXN-04).
- Most systems do not default to serializable. Three of 18 surveyed provided serializability by default [PDF-extracted, dated 2014]: [Highly Available Transactions](https://www.vldb.org/pvldb/vol7/p181-bailis.pdf) (2014; LIT-18).

**Isolation by engine.** What a named level gives, with remaining anomalies. Paraphrased from official docs and independent tests. Version-specific and to be re-checked at major releases.

| Engine (docs) | Default | Named Repeatable Read | Snapshot | Serializable | Known remaining issues | Retry signal |
|---|---|---|---|---|---|---|
| PostgreSQL 18 ([Transaction Isolation](https://www.postgresql.org/docs/current/transaction-iso.html), n.d., PGMY-08) | Read Committed | Is Snapshot Isolation | RR | SSI, true serializability | RR allows write skew | SQLSTATE 40001, retry whole transaction |
| MySQL 8.4 InnoDB ([Transaction Isolation Levels, section 17.7.2.1](https://dev.mysql.com/doc/refman/8.4/en/innodb-transaction-isolation-levels.html), n.d., PGMY-18) | Repeatable Read | First-read snapshot for plain SELECT; locking statements see latest committed | None named | Lock-based; plain SELECT becomes shared-locking with autocommit off | RR [RAW, Jepsen]: "MySQL's Repeatable Read still allows G2-item, G-single, and lost update"; separately "MySQL's Repeatable Read routinely allows G2-item, even on a single healthy node." | Deadlock and lock-wait errors; use FOR UPDATE or Serializable |
| SQL Server and Azure SQL ([SET TRANSACTION ISOLATION LEVEL](https://learn.microsoft.com/en-us/sql/t-sql/statements/set-transaction-isolation-level-transact-sql), 2025-09-26, MSOM-06) | Read Committed: locking on SQL Server, RCSI on Azure SQL Database | Shared locks to end; phantoms possible | Requires ALLOW_SNAPSHOT_ISOLATION | Key-range locks | SNAPSHOT: write skew as SI by definition [INFERENCE]; lock escalation at 5,000 locks | Errors 3960 and 1205 |
| Oracle ([Data Concurrency and Consistency](https://docs.oracle.com/en/database/oracle/oracle-database/26/cncpt/data-concurrency-and-consistency.html), n.d., TXN-08) | Read Committed | Not offered | Provided under the name Serializable | Is Snapshot Isolation per Hermitage | Write skew; undo-based snapshot too old failures | ORA-08177, ORA-00060 |
| MongoDB 9.0 ([Transactions](https://www.mongodb.com/docs/manual/core/transactions/), n.d., MSOM-18) | Client default write concern majority (5.0+) | n/a | Read concern snapshot with write concern majority | Not offered | w:1 [RAW, Jepsen 4.2.6]: "By default, client-level write concern is w: 1." and "MongoDB may lose data by default" from single-node acknowledgement; "The snapshot read concern does not actually guarantee snapshot isolation, and must always be used in conjunction with write concern majority"; a retry bug produced anomalies in 4.2.6, fixed by 4.2.8 | Abort and retry on `TransientTransactionError`; handle `UnknownTransactionCommitResult` |

Independent test sources: [Hermitage](https://github.com/ept/hermitage) (n.d.; TXN-10; versions tested not stated, MySQL classification partly superseded by Jepsen), [Jepsen: PostgreSQL 12.3](https://jepsen.io/analyses/postgresql-12.3) (2020-06-12; TXN-12), [Jepsen: MySQL 8.0.34](https://jepsen.io/analyses/mysql-8.0.34) (2023-12-19; TXN-11), [Jepsen: MongoDB 4.2.6](https://jepsen.io/analyses/mongodb-4.2.6) (2020-05-15), [Jepsen: Consistency Models](https://jepsen.io/consistency/models) (n.d.; TXN-13). No current Jepsen analysis of SQL Server or Oracle exists in the index read. The error labels are sourced to [MongoDB: Transactions in Applications](https://www.mongodb.com/docs/manual/core/transactions-in-applications/) (n.d.).

**Statements**
- MANDATORY (OLTP): specify guarantees as engine, level and configuration, never as the level's name. Grounding: Hermitage, Jepsen, and Oracle's SERIALIZABLE and MySQL's RR behavior.
- MANDATORY (OLTP): cross-row invariants under SI or RR levels use true serializability with retries, explicit row locks, or declarative constraints. Grounding: Berenson on write skew, Ports and Grittner, PostgreSQL docs, Jepsen.
- MANDATORY (OLTP): transactions that can fail with serialization, deadlock or write-conflict errors are retried as whole transactions. Grounding: PostgreSQL, SQL Server, MongoDB docs.
- MANDATORY (OLTP): keep transactions short and do not wait for user input inside one. Grounding: PostgreSQL; MongoDB's lifetime limit.
- MANDATORY [ENGINE: MongoDB]: set read concern snapshot and write concern majority explicitly when transaction guarantees are needed.
- RECOMMENDED (OLTP): consistent lock ordering. Grounding: PostgreSQL, SQL Server.
- RECOMMENDED (OLTP): a version column and compare-and-set update for business transactions spanning several system transactions: [rowversion](https://learn.microsoft.com/en-us/sql/t-sql/data-types/rowversion-transact-sql) (2017-07-22, updated 2026-10-19), [Optimistic Offline Lock](https://martinfowler.com/eaaCatalog/optimisticOfflineLock.html) (2003-03-05). An integer or engine version is preferable to `updated_at`, which is not guaranteed unique or monotonic [INFERENCE].
- RECOMMENDED (OLTP): bound transactions by aggregate: [DDD_Aggregate](https://martinfowler.com/bliki/DDD_Aggregate.html) (2013-04-23; ARCH-02).
- RECOMMENDED [ENGINE: SQL Server]: consider RCSI or SNAPSHOT and batch large deletes to reduce blocking: [Transaction locking and row versioning guide](https://learn.microsoft.com/en-us/sql/relational-databases/sql-server-transaction-locking-and-row-versioning-guide) (2026-04-22).
- OPTIONAL/CONTEXTUAL [ENGINE: PostgreSQL]: advisory locks for pessimistic patterns fitting MVCC poorly: [Explicit Locking](https://www.postgresql.org/docs/current/explicit-locking.html) (n.d.).

**MVCC cost, engine-specific:** PostgreSQL dead rows require VACUUM and long transactions hold it back: [Routine Vacuuming](https://www.postgresql.org/docs/current/routine-vacuuming.html) (n.d.). SQL Server escalates locks at 5,000 on one statement (locking guide). Oracle can fail with snapshot too old [RAW]: "ORA-01555 - snapshot too old: rollback segment number string with name "string" too small": [ORA-01555](https://docs.oracle.com/en/error-help/db/ora-01555/) (n.d.). MongoDB [RAW]: "If a transaction is in progress and a write outside the transaction modifies a document that an operation in the transaction later tries to modify, the transaction aborts because of a write conflict." It waits only briefly for locks: [Production Considerations](https://www.mongodb.com/docs/manual/core/transactions-production-consideration/) (n.d.; part of MSOM-18).

**Contested**
- **Oracle SERIALIZABLE.** Its docs list no dirty, fuzzy or phantom reads and do not mention write skew. Hermitage classifies it as Snapshot Isolation.
- **MySQL Repeatable Read.** Manual versus Jepsen 2023, which finds the level unsafe for read-then-write logic. Jepsen [RAW]: "Kleppmann's 2014 Hermitage suggested MySQL Repeatable Read might be Monotonic Atomic View, but this cannot be true: we found monotonicity violations."
- **PostgreSQL terminology.** Jepsen asked PostgreSQL to name snapshot isolation explicitly.
- **Explicit locks under Serializable.** PostgreSQL says to remove them when Serializable protects. Brandur combines Serializable with a lock column. Jepsen offers FOR UPDATE or Serializable as alternatives on MySQL.

**Outdated:** treating the SQL-92 definitions as sufficient; assuming a serializable label means correct (PostgreSQL's SSI bug patched in August 2020 shows implementations regress); pre-5.0 MongoDB defaults.

### 10.3 CAP and PACELC
**Scope: distributed OLTP and replicated stores.**
- Brewer's 2012 retrospective says CAP's two-of-three reading is misleading, that partitions are rare and that systems should detect them and manage them with explicit modes and compensation (TXN-15).
- Abadi argues CAP constrains behavior only under failures and that the latency-consistency trade-off in normal operation shapes designs more. He proposes PACELC as a framing for both conditions: [Consistency Tradeoffs in Modern Distributed Database System Design](https://www.cs.umd.edu/~abadi/papers/abadi-pacelc.pdf) (2012-02; TXN-14). Definition [PDF]: "if there is a partition (P), how does the system trade off availability and consistency (A and C); else (E), when the system is running normally in the absence of partitions, how does the system trade off latency (L) and consistency (C)?" He writes that "one particular tradeoff--between consistency and latency--arguably has been more influential on DDBS design than the CAP tradeoffs". Both confirmed in note 22 by pdftotext on the PDF retrieved by WebFetch. His system classifications date from 2012 and predate current defaults (for example MongoDB's). Do not reuse them as current facts.
- Kleppmann argues CAP's definitions are ambiguous and proposes a delay-sensitivity framework: [A Critique of the CAP Theorem](https://arxiv.org/abs/1509.05393) (2015-09-17; TXN-16).
- Jepsen's map treats snapshot isolation and stronger as unavailable in asynchronous networks (TXN-13).
- Gilbert and Lynch 2002 has an extractable text layer at the catalogued URL, so "unreadable scan" no longer holds. Theorem 1 [PDF]: "It is impossible in the asynchronous network model to implement a read/write data object that guarantees the following properties:" (only this opening was checked in note 22): [Brewer's Conjecture and the Feasibility of Consistent, Available, Partition-Tolerant Web Services](https://www.comp.nus.edu.sg/~gilbert/pubs/BrewersConjecture-SigAct.pdf) (2002-06; LIT-20). The 2012 Perspectives paper's title and authors are confirmed and its text is extractable, but specific claims still need individual checks, so it is not used for content: [Perspectives on the CAP Theorem](https://groups.csail.mit.edu/tds/papers/Gilbert/Brewer2.pdf) (2012; LIT-21).
- Bailis et al. show uniqueness-style invariants need coordination while many foreign-key-style invariants do not: [Coordination Avoidance in Database Systems](http://www.bailis.org/papers/ca-vldb2015.pdf) (2015).

**Statements**
- RECOMMENDED (distributed OLTP, financial) [INFERENCE]: favor consistency over availability and latency for systems of record whose invariants require coordination (uniqueness, sums, sequential numbering). No source states this as a rule for ERP. It follows from Bailis and from Brewer's treatment of invariants.
- OPTIONAL/CONTEXTUAL (OLAP, replicas): latency-favoring asynchronous replicas, provided reports do not feed transactional decisions.
- OPTIONAL/CONTEXTUAL (distributed OLTP): Brewer's partition mode with bounded operations and later compensation; invariant-confluence analysis.

**Contested:** Brewer, Abadi and Kleppmann each frame CAP differently. The positions are complementary in practice. Use PACELC's vocabulary to describe trade-offs, not CAP labels as engine classifications.

**Outdated:** pick two of three as a design rule.

### 10.4 Distributed transactions, idempotency, sagas, outbox
**Findings**
- PostgreSQL says PREPARE TRANSACTION is for external transaction managers and that prepared transactions left open interfere with VACUUM: [PREPARE TRANSACTION](https://www.postgresql.org/docs/current/sql-prepare-transaction.html) (n.d.). MySQL describes XA and says Repeatable Read may be insufficient for distributed transactions: [XA Transactions](https://dev.mysql.com/doc/refman/8.4/en/xa.html) (n.d.).
- Spanner uses two-phase commit over Paxos with TrueTime and argues programmers should handle overuse of transactions when it becomes a bottleneck rather than code around their absence [PDF]: [Spanner](https://research.google/pubs/spanner-googles-globally-distributed-database-2/) (2012; TXN-20). Calvin avoids two-phase commit through deterministic ordering [PDF]: [Calvin](http://cs.yale.edu/homes/thomson/publications/calvin-sigmod12.pdf) (2012).
- Sagas are sequences of transactions with compensating transactions for partial execution [PDF]: [Sagas](https://www.cs.cornell.edu/andru/cs711/2002fa/reading/sagas.pdf) (1987; TXN-17). The modern pattern notes no automatic rollback and no isolation across steps, with choreography and orchestration variants: [Pattern: Saga](https://microservices.io/patterns/data/saga.html) (n.d.; ARCH-06). Saga countermeasures such as semantic locks are referenced to a book and were not read [UNVERIFIED detail].
- The transactional outbox stores a message in the same transaction as the business change, and a relay publishes it. The relay may publish more than once, so consumers must be idempotent: [Pattern: Transactional outbox](https://microservices.io/patterns/data/transactional-outbox.html) (n.d.; TXN-18). CQRS guidance also recommends outbox and idempotent consumers (PERF-56).
- Stripe's idempotency contract: client keys up to 255 characters, parameters compared against the original request, results saved after execution begins, keys prunable after at least 24 hours: [Idempotent requests](https://docs.stripe.com/api/idempotent_requests) (n.d.; CASE-33).
- Brandur describes a table with a unique key per user and idempotency key, stored response, recovery point and lock column, with atomic phases and a background completer and reaper: [Implementing Stripe-like Idempotency Keys in Postgres](https://brandur.org/idempotency-keys) (2017-10-27; TXN-19).
- Raft achieves exactly-once command application through client serial numbers tracked by the state machine [PDF]: [In Search of an Understandable Consensus Algorithm](https://raft.github.io/raft.pdf) (2014).
- TigerBeetle transfers carry a user-specified unique ID and execute at most once. Transfers are immutable and corrected by compensation: [Jepsen: TigerBeetle 0.16.11](https://jepsen.io/analyses/tigerbeetle-0.16.11) (2025-06-06).
- Stripe's ledger is double-entry and append-only, with reversal and clearing-account zero checks: [Ledger](https://stripe.dev/blog/ledger-stripe-system-for-tracking-and-validating-money-movement) (2024-02-16; TEN-43).
- PostgreSQL sequence calls are never rolled back, so sequences cannot give gapless numbering. Gapless numbering needs a locked counter at higher cost: [CREATE SEQUENCE](https://www.postgresql.org/docs/current/sql-createsequence.html) (n.d.). Sequence caching allows out-of-order values across sessions.

**Statements**
- MANDATORY (OLTP, when retried writes can cause duplicate effects): an idempotency record guarded by a unique constraint scoped to the caller, with request parameters compared on replay. Grounding: Stripe, Brandur, and the same mechanism in Raft and TigerBeetle. Scoping by tenant is [INFERENCE] from Brandur's user scope.
- MANDATORY (OLTP with event publication): if the outbox pattern is used, write the outbox row in the same local transaction, and consumers are idempotent. Grounding: microservices.io and Azure CQRS guidance.
- MANDATORY (STREAM consumers): consumers tolerate redelivery. Same grounding.
- MANDATORY (OLTP, ledgers): posted entries are immutable; corrections are compensating entries. Grounding: Stripe Ledger, TigerBeetle, and Gray's and Haerder and Reuter's compensation lineage.
- MANDATORY (OLTP): do not use sequences or identity for gapless legal numbering. **Evidence limit:** the explicit statement comes from PostgreSQL. Transferring it to other engines is [INFERENCE]. No source in the notes establishes which jurisdictions require gapless numbers.
- RECOMMENDED (OLTP, multi-service): sagas with persisted state and explicit status on business rows, orchestrated where steps are many. Status columns as semantic locks are [INFERENCE].
- RECOMMENDED (OLTP): `created_at` is not a reliable global order; use a single-writer sequence or ledger position [INFERENCE from CREATE SEQUENCE].
- OPTIONAL/CONTEXTUAL (distributed OLTP): XA through a transaction manager; Spanner-class or Raft-based systems; deterministic scheduling.

**Universal vs engine-specific:** the patterns are universal. Retry signals, XA details and sequence semantics are engine-specific.

**Contested**
- **2PC.** Spanner favors offering transactions and running 2PC over consensus. microservices.io treats 2PC as unavailable for database-per-service. PostgreSQL restricts it to transaction managers. Calvin avoids it. Context: Spanner's position assumes a single managed system, while microservices.io assumes independent services.
- **Outbox vs CDC.** microservices.io treats log tailing as one relay option. CockroachDB's hotspot page prefers CDC to outbox tables to avoid index-tail contention (PERF-48). Context: range-sharded engines.
- **Saga control.** Choreography vs orchestration. No comparative evidence in the notes.
- **Idempotency replay.** Stripe v1 replays saved responses including server errors. Stripe v2 retries work to completion. Retention varies: Stripe's at least 24 hours, Brandur 24 or about 72 hours in different passages.
- **Random key format.** Stripe suggests V4 UUIDs for idempotency keys. This is about entropy in a client token and does not conflict with section 4 advice on index locality for primary keys.

**Outdated:** assuming exactly-once delivery by infrastructure; relying on distributed transactions across independently owned services.
## 11. Schema anti-patterns
**Scope column applies per row. Karwin's items are from the publisher's one-line descriptions and table of contents: [SQL Antipatterns, Volume 1](https://pragprog.com/titles/bksap1/sql-antipatterns-volume-1/) (2022-10; DES-13). His remedies and legitimate-use sections were not read.** The label is this document's, not his.

| Antipattern | Issue | Corroboration | Scope | Label |
|---|---|---|---|---|
| Jaywalking, Multicolumn Attributes | Lists in a column, numbered columns | Codd normal form; Kent | OLTP | MANDATORY avoid |
| Keyless Entry | Missing constraints | PostgreSQL, SQL Server, GitLab | OLTP | MANDATORY avoid, with 5.2 exception |
| ID Required | One key convention everywhere | sqlstyle | OLTP | RECOMMENDED avoid |
| Entity-Attribute-Value | Generic attribute table | sqlstyle | OLTP | RECOMMENDED avoid. Note 10 says MANDATORY, but only two style-level sources support it and legitimate-use text was unread |
| Polymorphic Associations | One reference to several parents, cannot be constrained | Karwin's description; Rails ships the pattern | OLTP | RECOMMENDED avoid. Rails' convention shows real-world tolerance |
| Metadata Tribbles | Cloning tables or columns for scale | sqlstyle on splitting logical tables; partitioning docs | OLTP, DW | RECOMMENDED avoid |
| Naive Trees | Parent-only hierarchies | PostgreSQL `ltree` as an alternative | OLTP | CONTEXTUAL |
| Rounding Errors | FLOAT for exact values | PostgreSQL, MySQL, SQL Server, Alibaba | ALL | MANDATORY avoid |
| 31 Flavors | Values in column definitions | PostgreSQL and MySQL enum limits | OLTP | CONTEXTUAL |
| Phantom Files | Assuming media must be external | No fetched detail | ALL | CONTEXTUAL |
| Index Shotgun | Unplanned indexes | SQL Server, MySQL, PostgreSQL, Oracle | OLTP | RECOMMENDED avoid |
| Fear of the Unknown | Mishandled NULL | PostgreSQL wiki, Kent | ALL | RECOMMENDED avoid |
| Pseudokey Neat-Freak | Filling key gaps | PostgreSQL sequences | ALL | MANDATORY avoid |
| Foreign key mini-antipatterns | Reversed references, mismatched types, orphans | Buildkite, MySQL FK rules | OLTP | MANDATORY avoid (types); RECOMMENDED (others) |
| Random UUID clustered key | Locality loss | Percona, PlanetScale, EDB, SQL Server guide | OLTP single-node | RECOMMENDED avoid; not applicable to range-sharded engines |
| 32-bit key columns | Exhaustion | Buildkite | OLTP | RECOMMENDED avoid |
| Partial indexes as partitioning | Planner and maintenance burden | PostgreSQL | OLTP | RECOMMENDED avoid |
| Non-SARGable predicates, mismatched types | Index unusable | Winand, MySQL, PostgreSQL wiki | ALL | MANDATORY avoid (types); RECOMMENDED (functions) |
| N+1 queries | Round trips | Winand | OLTP | RECOMMENDED avoid |
| Sequence for gapless numbers | Non-transactional values | PostgreSQL | OLTP | MANDATORY avoid, see 10.4 limit |
| Read-then-write invariants at weak isolation | Write skew or lost update | Berenson, Jepsen | OLTP | MANDATORY avoid |
| Secondary replica reads for safety-critical decisions | Lag or weaker isolation | Jepsen RDS, MongoDB | OLTP | RECOMMENDED avoid |

PostgreSQL-specific do-not items, with the wiki itemizing 19 in total per `CORRECTIONS.md`: `money`, `char(n)`, `timestamp` for UTC, `timetz`, `serial`, rules, table inheritance, `NOT IN`, `BETWEEN` on timestamps, upper-case names: [Don't Do This](https://wiki.postgresql.org/wiki/Don%27t_Do_This) (2024-11-21; PGMY-10). A community page, weighted accordingly.
## 12. Cross-cutting register
### 12.1 What is universal

| Topic | Universal statement | Scope |
|---|---|---|
| Identity | Every base table has a declared key | OLTP |
| Integrity | Declare constraints the engine can enforce | OLTP |
| Types | Exact numerics for money; instants unambiguous to UTC | ALL |
| Naming | A written, consistent, safe convention | ALL |
| Indexing | Indexes trade write and storage cost for reads | ALL with indexes |
| Isolation | Level names are not portable | OLTP |
| Retries | Serialization and deadlock failures are retried as a whole | OLTP |
| Distributed writes | Consumers are idempotent | OLTP, STREAM |

### 12.2 Contested register

| Debate | Position A | Position B | What decides |
|---|---|---|---|
| Natural vs surrogate | Celko [UNVERIFIED], sqlstyle, Karwin | Kimball (DW), Chen, ORMs | Key stability; workload |
| Warehouse key type | Kimball integer | dbt strings; Data Vault hashes | Methodology and load pattern |
| UUID as key | Avoid on clustered single-node | Prefer random on range-sharded | Topology |
| Foreign keys | In database | In application under sharding | Infrastructure |
| ON DELETE default | GitLab CASCADE | PlanetScale NO ACTION; Alibaba none | Ownership; replication tooling |
| Index every foreign key | GitLab MANDATORY | PostgreSQL case by case | Engine; access pattern |
| Singular vs plural | Alibaba, Django default, Prisma model names, 11179-5 draft annex (data elements) | Rails, dbt, GitLab, sqlstyle, Prisma on common practice | Consistency |
| NULL in UNIQUE | SQL Server one NULL [WF] | MySQL [WF], PostgreSQL many; Oracle composite-specific [WF] | Engine; never portable |
| Subtype mapping default | Hibernate favors JOINED for constraints | EF Core defaults to TPH, warns on TPT | ORM goal and constraint needs |
| Foreign key index creation | PostgreSQL leaves it to the developer, per GitLab | EF Core and InnoDB create it | Engine and tool |
| Crow's foot venue | Redgate body: Fifth Computing Conference, IEEE | Redgate footnote: Fifth Texas Conference on Computing Systems | Unresolved; 1976 paper unread |
| Most selective first | Folk rule | Winand and vendor mechanics | Largely resolved against folk rule |
| Partition for performance | Oracle | SQL Server, PostgreSQL | Workload; pruning |
| Materialized views in OLTP | Stonebraker, never | SQL Server permits with cost | Write rate |
| Enum vs lookup vs CHECK | Static enum | Lookup or CHECK | Value volatility |
| 2PC | Spanner | microservices.io | Single system or independent services |
| Outbox vs CDC | microservices.io | CockroachDB | Engine and hotspot risk |
| CAP framing | Brewer | Abadi; Kleppmann | Complementary |
| Exact decimal vs float in ELT | Vendor manuals | dbt example | Exact wins for finance |

### 12.3 Outdated advice summary
Most-selective-first index order; 32-bit generated keys by default; `serial` on PostgreSQL per the wiki; `CHAR(36)` UUIDs; UUIDv1 for new keys; float for money; hard-coded two-decimal currency; `datetime` on SQL Server; utf8mb3; 30-byte identifier limits as universal; denormalize as an OLTP default; partition for OLTP point lookups; two-of-three CAP reasoning; SQL-92 isolation definitions as sufficient; inheritance-based partitioning on PostgreSQL.

### 12.4 Standards position
- **ISO/IEC 9075 (SQL).** Multi-part and paywalled. ISO/IEC 9075-1:2023 was published 2023-06-01: [BSI Knowledge](https://knowledge.bsigroup.com/products/information-technology-database-languages-sql-part-1-framework-sql-framework) (2023-06-01; GOV-05). Feature names and part lists come from search results and community sources. Temporal features in SQL:2011 and JSON in SQL:2016 and SQL:2023 are documented by committee authors and community summaries (note 08). No clause text was read. Cite by feature ID without asserting clause content. Conforming syntax is RECOMMENDED for portability, though commercial adoption has been slow per those authors.
- **ISO/IEC 11179.** See 6.1. Authority for having a convention, not for specific name patterns.
- **ISO 4217.** See 7.1. Free code lists from SIX. Use as reference data.
- **ISO 8601.** See 7.2. An interchange representation.
## 13. Evidence limits
### 13.1 Sources not verified or restricted

| Item | Status | Handling |
|---|---|---|
| Celko's key taxonomy, plural position | Search summaries only | [UNVERIFIED] |
| C. J. Date's content (normal forms, NULL, surrogate keys) | Inaccessible | Not cited for content |
| BCNF, 4NF, 5NF, 6NF primary papers | Not read | Kent's exposition only |
| Karwin content beyond publisher lines | Not read | Names and one-liners only; remedies not attributed |
| Kent phrases | Note 22 corrected the wording | Corrected text quoted [RAW] |
| Kimball "Keys should not encode meaning" | Not found on the page | Paraphrase only; not attributed |
| Perspectives 2012 specific claims | Title, authors and text layer confirmed; claims unchecked | Not used for content |
| PostgreSQL other section numbers | Not checked beyond 8.3, 8.14, 8.18 and 9.14 for docs 18 | Page titles used |
| DDIA chapter contents; the C in ACID remark | Not verified | Not relied on |
| Oracle pages at /23/ URLs | Six report Release 26 and redirect to /26/ (note 22) | Final /26/ URLs used; no 23ai provenance. Database Object Names stays at its /23/ URL as recorded; THIN-15 is 19c |
| All [WF] findings (SQL Server, MySQL, Oracle UNIQUE NULL behaviour) | WebFetch only | Paraphrase; re-check against the page |
| ISO/IEC 11179-5 | Abstract plus partly downloaded 2004 draft; published text unread | Draft content flagged as draft |
| Everest 1976; closure table and nested set sources | Not opened | Origin via two secondary pages; not attributed to Karwin |
| One Size Fits All venue | Not in PDF | Only year given |
| ISO product pages | HTTP 403 | Abstracts, mirrors, maintenance agencies |
| FIPS 184 withdrawal | Wikipedia only; no NIST notice opened | Described as reported |
| Hermitage | Undated; versions unstated | Treat as directional |

### 13.2 Questions the notes do not answer
- Scale for FX rates, unit prices and intermediate calculation.
- SQL Server: explicit statement on deferrable constraints (only grammar absence was found [WF]) and an explicit unique filtered index example for NULLs.
- A controlled comparison of natural and surrogate keys in OLTP.
- A combined UUIDv7, UUIDv4 and bigint benchmark on B-tree engines.
- Denormalization cost measurements in OLTP.
- Legal requirements for gapless document numbering by jurisdiction.
- LAKE-specific schema standards beyond constraint semantics, and streaming schema rules. These belong to the adjacent topic files.
- Published ISO/IEC 11179-5 text and its naming rules; engine-neutral subtype enforcement; a measured comparison of subtype mappings.
