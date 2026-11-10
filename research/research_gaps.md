# Research gaps and evidence limits

Database schema design framework research. Status as of 2026-11-08. This document records what the research can and cannot support. Read it before citing anything from the catalog or the topic notes in a standard.

Inputs: `CORRECTIONS.md` (which overrides the topic notes), topic notes 01 to 23 with their Gaps sections and access notes, `verification_results.json`, and `resource_catalog.json` with its link check of 2026-11-08.

No new research was done for this document, and it adds no source that is not in the notes or the catalog. Research, including the follow-up in notes 18 to 23, is complete except for items that need licensed copies, manual browser checks or legal review. Section 7 lists them.

## 1. Research progress against the original phases

| Phase | Scope | Status | Output or position |
|---|---|---|---|
| Phase 1 | Resource collection | Done | 594 unique resources in `resource_catalog.json`, `.csv` and `.md` |
| Phase 2 | Documentation of resources | Done | 23 topic notes and 22 topic catalogs with concepts, principles, authority and verification fields |
| Phase 3 | Comparison | Done | `architecture_comparison.md` and `design_decision_matrix.md` |
| Phase 4 | Foundation | Done | Covers the 20 framework areas rated in section 3 |
| Follow-up | Evidence verification and gap research | Done, except items in section 7 that need licensed copies, manual browser checks or legal review | Notes 18 to 23 |
| Stage 2 | Standards | Not started | Uses the section 7 list to decide which sources can be cited |
| Stage 3 | Framework build | Not started | Depends on Stage 2 |

Catalog composition by ID prefix: LIT 60, CASE 47, PERF 45, LEG 36, TEN 33, GOV 32, SEC 32, ENG 28, ERP 25, THIN 25, DWM 23, ARCH 23, PIPE 22, CLOUD 21, OPS 21, PGMY 20, LAKE 19, DQ 19, MSOM 18, TXN 16, DES 15, BENCH 14.

Link check summary for all 594 entries:

| Status | Count | Meaning |
|---|---:|---|
| `reachable` | 565 | The URL responded to the script. This does not show that the content was read. |
| `bot_blocked_or_refused_403` | 18 | The host refused a script. The page is not shown to be down. |
| `bot_blocked_or_refused_406` | 4 | The host refused a script. The page is not shown to be down. |
| `bot_blocked_or_refused_401` | 1 | The host refused a script. The page is not shown to be down. |
| `bot_blocked_or_refused_503` | 1 | The host answered 503 to a script. The page is not shown to be down. |
| `not_checked_local_ssl_error` | 4 | The script's local certificate store failed. The page is not shown to be down. |
| `not_checked_timeout_or_connection` | 1 | No result from the check. |

In total, 568 entries have `url_verified` true and 26 have it false, and 29 entries are not `reachable`. The two problem groups overlap, and 41 entries are in at least one of them. All 41 are listed in section 5. There are no `dead_404` entries.

## 2. Evidence quality limits

These limits apply across the whole research set and take priority over any individual catalog field.

**Paraphrase by default.** Most web pages were read through a summarizing fetch tool. Quotation marks on web-page citations in the topic notes are paraphrases unless they have been checked, and must not be presented as verbatim. Note 22 records the check of 2026-11-08 and gives the source wording for each item tested.

**Reliable exception.** Text extracted directly from PDFs with pdftotext is reliable. This covers NIST, parts of Codd and Chen, and the Codd and PACELC passages confirmed in note 22. The NIST quotes in note 13 are confirmed reliable by CORRECTIONS.md.

**Paywalled ISO standards are known only by scope.** The notes hold catalogue abstracts, scope statements, maintenance-agency data and third-party summaries, not normative text:

- ISO/IEC 9075: no ISO catalogue page could be opened for its parts, so edition status per part is unverified.
- ISO/IEC 11179-3 and 11179-5: the published naming rules are unread. Note 20 read a partly downloaded 2004 committee draft of 11179-5.
- ISO/IEC 25012: all 15 characteristics were read on a secondary site (note 20). The official text is unread.
- ISO 8000 series: the inventory of parts is at community level only (Wikipedia, note 20).
- ISO/IEC 38505-1:2026: content and changes from 2017 were not visible.
- ISO/IEC 27001:2022: Annex A control titles come only from vendor blogs, and 27002:2022 was not consulted.
- ISO 15489-1: retention and disposition language was not visible.
- ISO 22301: details come from the EVS national record because iso.org returned 403.
- ISO/IEC 27031 and ISO 22313: not opened.

Other gated standards and frameworks have the same problem: DAMA-DMBOK (paid book), the DAMA UK whitepaper (members only), the CIS benchmark PDFs (registration), the final PCI DSS v4.0.1 PDF (license-gated), and DCAM (paywalled or members only).

**Books are known only from publisher pages where the notes say so.** Page-level or chapter-level claims from these are not source-verified:

- Designing Data-Intensive Applications: O'Reilly returned 403, and chapter-level claims are unverified.
- Karwin's SQL Antipatterns: only publisher descriptions and the table of contents were read.
- Date's books: content inaccessible.
- Celko's books: reconstructed from search summaries.
- Simsion and Witt, Hoberman, Hay and Silverston: bibliographic records or background knowledge only.
- Evans and Vernon on DDD: the books were not fetched. The DDD Reference and Vernon's essays were used instead.
- Fundamentals of Data Engineering and Streaming Systems: bodies not retrieved.
- Data Mesh (Dehghani): the book page returned 403, and only the 2020 article's component list is cited.
- Kimball's ETL Toolkit: ABC chapter not accessible.
- Accelerate: not opened; the DORA capability page was used instead.
- Johnston and Weis, and Date, Darwen and Lorentzos, on temporal data: not fetched.
- Inmon's Building the Data Lakehouse and Corporate Information Factory: text not verified or not fetched.

**Background knowledge in annotations.** Note 16 annotation details are from background knowledge rather than fetched pages. These cover Karwin anti-pattern names, Force.com flex-column details, Hay and Silverston contents, PACELC system classifications and some page numbers.

**Version and date uncertainty.**

- Oracle `/23/` URLs redirect to `/26/` and report Release 26 in page metadata. This includes the query rewrite page, whose body gives no version.
- Snowflake docs print no last-updated date.
- OWASP cheat sheets and microservices.io pages show no publication dates.
- Hermitage does not state the engine versions tested.
- Databricks multi-statement transactions reached general availability for Unity Catalog managed Delta tables in July 2026 and for managed Apache Iceberg tables in October 2026. The status of Metric Views as a whole is unresolved (note 21).

**Link check limits.**

- `reachable` is not evidence that content was read. O'Reilly and Springer entries pass the check while remaining `url_verified` false.
- `url_verified` true with a blocked or SSL status means an earlier fetch worked and the 2026-11-08 script check did not. It does not mean the page has gone.

**Topic and merged counts.** Differences between topic files and the merged catalog come from duplicate removal. Literature has 75 topic rows and 60 merged rows. Its 14 `url_verified` false rows become 12 because two of the removed duplicates (LIT-46 and LIT-66) were false. Case studies have 53 topic rows and 47 merged rows, with 6 false in both. Any count quoted from a topic file describes that file, not the merged catalog.

**Authority levels.** Use the catalog value. LIT-39, LIT-66 and LIT-74 are level 4.

## 3. Coverage of the 20 framework areas

The ratings are judgments made from the notes, and they measure how well the evidence supports a standard:

- **Strong:** primary or official sources were read across the main engines, and gaps are at the edges.
- **Adequate:** usable for a draft, but a named primary source or an engine is missing.
- **Thin:** key authorities are unread, or the area rests on inference or lower-authority sources.

| # | Framework area | Rating | Reason | Main notes |
|---:|---|---|---|---|
| 1 | Architecture principles | Adequate | Cloud frameworks and DDD or mesh sources were read. Google's framework has no database-specific recommendations in the pages fetched, DDIA and Evans were not read, and Data Fabric has no independent primary source. | 03, 07, 11 |
| 2 | Logical and physical modeling | Adequate | Methodology sources were read for Kimball, Inmon and Data Vault. Simsion and Witt and Hoberman are bibliographic only and ANSI/SPARC was not opened. Data Vault against star has only weak benchmarks, and One Big Table against star is engine-dependent. | 06, 10, 23 |
| 3 | ER design | Adequate (was Thin) | FIPS 184 IDEF1X was read directly, crow's foot origin rests on two opened pages, and subtype trade-offs were read from Hibernate and EF Core. The Everest 1976 paper and the practitioner modeling books remain unread, and database-native subtype enforcement was not covered. | 10, 20 |
| 4 | Normalization | Adequate | Codd 1970 and Kent's exposition were read, and Kent's exact wording is now recorded in note 22. Primary texts for BCNF, 4NF, 5NF and 6NF were not fetched, and Date was inaccessible. | 10, 16, 22 |
| 5 | Relational integrity | Strong | PostgreSQL and MySQL constraint documentation was read directly. Foreign keys to partitioned tables and SQL Server deferral are now covered in note 21. Edge gaps remain on the PostgreSQL child side of partitioned foreign keys and Karwin's own arguments. | 01, 02, 10, 21 |
| 6 | Naming | Adequate (was Thin) | Oracle publishes naming guidelines, framework conventions were read, and a 2004 draft gives the 11179-5 rule structure. Published 11179-5 text is unread. Singular versus plural is contested, with no outcome evidence. | 01, 02, 08, 10, 20 |
| 7 | Data types and precision | Adequate | PostgreSQL types and the ISO 4217 List One data file are solid. SQL Server, MySQL and MongoDB date semantics are now read, mostly through the fetch tool. Exchange-rate precision has no vendor-stated value. A dbt example conflicts with the exact-decimal rule. | 01, 02, 10, 18, 21 |
| 8 | Indexing and performance | Strong | Vendor documentation across engines was read and PERF has 45 entries. No numeric index thresholds were found. UUIDv7 and bigint evidence on PostgreSQL is practitioner level, and no UUIDv7 benchmark on MySQL was found. | 01, 02, 11, 23 |
| 9 | Transactions | Strong | Primary papers, vendor docs, Jepsen and Hermitage were used. Gilbert and Lynch 2002 is now extractable, and several removed claims are sourced in note 22. No Jepsen analysis covers current SQL Server, Oracle or Spanner. | 12, 16, 21, 22 |
| 10 | Multi-company and multi-tenant isolation | Adequate | SaaS Lens and Microsoft guidance support silo, pool and bridge, and fiscal-calendar and exchange-rate design now have vendor sources. RLS cost has one small practitioner test, there is no comparable Google guide, and SAP company code has no official definition read. | 03, 14, 18, 23 |
| 11 | Security and permissions | Strong | NIST PDF text, OWASP, regulator sources and official GDPR text were read. CIS benchmarks are gated, ASVS V11 and V16 text was not opened, and crypto-shredding as erasure is not settled by any regulator text found. | 09, 19 |
| 12 | Audit and history | Adequate | Oracle Unified Auditing, MongoDB auditing and Envers ValidityAuditStrategy are now read. Db2 temporal is missing, and the bitemporal books were not fetched. | 14, 21 |
| 13 | Migrations | Adequate | PostgreSQL expand-and-contract practice is well covered, and source wording for the main quotes is in note 22. MySQL online DDL is read through the fetch tool only. Oracle and SQL Server online DDL were out of scope. | 13, 17, 21, 22 |
| 14 | Pipelines and ETL/ELT | Strong | Official documentation was read for streaming, CDC, table formats and orchestration. Partial pages and unread books remain. Control columns such as `updated_at` are inferences, not vendor rules. | 04, 05 |
| 15 | Data quality | Adequate | Tool documentation was read. ISO 25012 is at secondary level, ISO 8000 is at community level, no numeric SLO benchmarks exist, Airbnb Midas is snippet only, and no defect-catch comparison was found. | 08, 15, 20 |
| 16 | Reporting and analytical models | Adequate | Kimball's consolidated PDF, Inmon's post, Data Vault and platform docs were read. One peer-reviewed One Big Table result exists and conflicts with a vendor-hosted test. Data Vault against star has no benchmark at realistic scale, and layering guidance is blog level. | 04, 06, 23 |
| 17 | Scalability | Adequate | Vendor partitioning and sharding docs and case studies were read, and PostgreSQL and MySQL replication-lag docs are now covered. DDIA is unverified and six case studies are search only. | 11, 17, 21 |
| 18 | Testing and schema validation | Adequate (was Thin) | Schemalint, utPLSQL, pgTAP, tSQLt, Atlas, prisma-lint and EF Core were read and compared, and the Testcontainers definition is confirmed. No tool ships a tenant-key rule, and money-type and reserved-word checks remain weak. | 13, 20, 22 |
| 19 | Backup and DR | Adequate | NIST text is reliable and vendor concepts are covered, including RMAN, Data Guard and Always On in note 21. Retention periods by jurisdiction are in note 19. ISO detail is indirect. | 09, 13, 19, 21 |
| 20 | Documentation and governance | Thin | The landscape is mapped and DAMA's own page now gives 11 knowledge areas. DMBOK text, DCAM text, published ISO/IEC 11179 and ISO/IEC 38505 remain unread. ISO 25012 is at secondary level. | 08, 15, 20 |

Rating totals: strong 5, adequate 14, thin 1. Three areas moved from thin to adequate after notes 20 to 22.

## 4. Gaps by topic

### Vendor documentation (notes 01, 02)

PostgreSQL 18.6 and 19 GA dates could not be confirmed because the news index returned 404. The MySQL LTS or Innovation classification of 26.x rests on the 8.4 page and search summaries. Foreign keys referencing partitioned tables are now covered in note 21, but the PostgreSQL child side was not confirmed. Whether PostgreSQL 18 virtual generated columns can be indexed is not stated on the fetched page. MySQL column-level privileges are now read through the GRANT page (ENG-06). PostgreSQL ALTER TABLE cost semantics were not fetched. No official MySQL page quantifies the cost of random primary keys. SQL Server columnstore, memory-optimized and filtered-index sections were not read in full. Oracle's Tables and Table Clusters chapter was not fetched. Oracle ARCHIVELOG and Data Guard are now read (ENG-17, ENG-18). Incremental levels were not confirmed. MongoDB date storage is now read (ENG-13). Time series details were not fetched, and no shard-key size limit should be asserted. No vendor page gives an official OLTP and OLAP decision table. The split in the notes is assembled.

### Cloud and platforms (notes 03, 04)

The AWS tenant-isolation and storage whitepapers redirected. Use the SaaS Lens for silo, pool and bridge. AWS Data Analytics Lens numbered best practices were not captured. Google has no multi-tenant SaaS partitioning guide or database decision table in the pages found. Azure alone publishes numeric trait tables, so any such table must be labeled as Azure. Databricks `RELY` semantics are now read (ENG-29). No Databricks page states whether medallion layers should be catalogs or schemas. No vendor provides a cost model behind the claim that storage is cheap and compute is expensive. No official OBT versus star performance comparison exists.

### Pipelines and streaming (note 05)

Confluent's per-type compatibility rules were not retrieved in readable form. Debezium `provide.transaction.metadata` ordering semantics were not captured. Delta type widening, Hudi ACID and time travel pages, and Spark partitioning guidance were not fetched. Prefect, Fivetran definitions and Streaming 102 were not retrieved. No source prescribes `updated_at`, soft-delete columns, late-arriving placeholders or reconciliation tables.
  Label these as framework decisions.

### Warehouse modeling (note 06)

Individual Kimball technique pages were not opened, and one Kimball Group article returned 404. No consolidated Data Vault 2.0 standards page could be opened. Historical Linstedt posts on sequences and hash keys were not retrievable. Teradata documentation of a normalized-model preference was not retrievable. Beauchemin's essay and the Coalesce 2020 talks are known only through search summaries. No like-for-like quantified comparison exists, so matrix ratings are relative judgments.

### DDD, events, mesh and fabric (note 07)

Greg Young's book was unreadable beyond the table of contents. CloudEvents attributes come from a work-in-progress spec branch, so wording may differ from the release. Gartner glossary pages returned 403, so Gartner definitions are third-party only. No independent critical analysis of data fabric was found. No threshold for splitting from schema-per-context to server-per-context was found. The mapping from Dehghani's output ports to ODCS is an inference.

### Governance and international standards (note 08)

DAMA's page says 11 knowledge areas but no opened DAMA page lists them all, and the DMBOK2 year was not confirmed from an opened DAMA page. ISO 3166, 4217, 8601 and 639 content relies on search snippets and maintenance-agency sites. ISO 20022 could not be fetched during research, and GS1 specifications returned 403. The ANSI/SPARC 1975 report was not opened. Standards prices were not visible.

### Security and privacy (note 09)

SP 800-53 Release 5.2.0 changes were not reviewed. Quoted text is Rev. 5 from the September 2020 PDF. SP 800-209 body recommendations and NIST Privacy Framework 1.1 status are unverified. GDPR Art. 17(1) and Art. 30(5) are now quoted from EUR-Lex in note 19. PCI wording is from the v4.0 SAQ D, and clause numbering in v4.0.1 was not re-verified. HIPAA NPRM items were not located, and final-rule status is unverified. California Civil Code 1798.105 was read from the CPPA-hosted copy, and leginfo was not opened. No regulator text found addresses soft delete by name or accepts key destruction as erasure.

### Core design (note 10)

Primary texts for the higher normal forms were not fetched. Date's position on surrogate keys was not fetched. NULL behaviour in UNIQUE constraints on SQL Server, MySQL and Oracle is now in note 21. Codd's A and I marks and Date's critique of nulls are known by title only. Hibernate naming strategies are now read in note 20. Lakehouse tags in this note are inferred and need validation against notes 04 and 05.

### Performance and scalability (note 11)

MongoDB sub-pages for covered queries, partial and TTL indexes were not fetched. BigQuery partition limits and Vitess shard-size guidance were not on fetched pages. ProxySQL and Oracle In-Memory or HTAP documentation were not fetched. No independent HTAP isolation benchmark was found. No source quantifies the cost of denormalization in OLTP.

### Transactions (note 12)

The SQL Server locking guide was read only to character 100,000 of 176,855. `deadlock_timeout`, `SKIP LOCKED` and `NOWAIT` pages were not fetched. The XA specification itself was not fetched. Saga countermeasures reference a book that was not available on the fetched pages. No vendor specifies a canonical outbox column list, so the column set is an inference.

### Migrations, testing and DR (note 13)

The Flyway Migrations concept page is gone, and repeatable-migration semantics were not found beyond ordering and checksums. Legacy Prisma Migrate behaviour was not verified against current ORM 8 documentation. AWS RPO and RTO tier ranges are in a figure, so no numbers are quoted. No source quantifies legal retention requirements for database backups. The DBA-authored versus developer-authored migration debate has no quantitative source.

### Multi-tenancy, audit, temporal and retention (note 14)

Schema-per-tenant migration burden is inferred from Microsoft's schema-versioning guidance. NetSuite period and currency pages are now read in note 18. The Envers ValidityAuditStrategy trade-offs are read from the Hibernate repository's `main` branch (note 21). PCI 10.5.1 wording now comes from the public v4.0 SAQ D (note 19). The claim that PostgreSQL lacks native system versioning rests on the PG 18 release notes alone. The UK VAT retention period is now read from Notice 700/21 (note 19). Legal hold mechanics and BigQuery table expiration are not covered.

### Data quality, lineage and metadata (note 15)

GX metric persistence, Soda's v4 check list and Elementary's anomaly parameters were not confirmed. ODCS quality rule types and SLA property names remain unverified. OpenMetadata's models and Apache Atlas's type system are not verified. The link from Snowflake lineage to ACCESS_HISTORY is inferred. No source gives alert-routing or incident-SLA numbers. Oracle frames reconciliation as explained differences, so debits equal credits is an accounting assertion,
  not a sourced pipeline rule.
- Amundsen was archived 2026-09-29 and data-diff was archived 2024-05-17. Weigh this before recommending either.

### Literature (note 16)

There is no official full text for Codd 1971 (RJ909). The DOI for Stonebraker and Pavlo 2024 was not confirmed. LIT-02 is a DBLP record only, and LIT-03 is a five-page excerpt. The LIT-13 year comes from the brief, and LIT-21 and LIT-22 IEEE details are partly from memory.

### Case studies (note 17)

Instagram's bit layout and function were not verified, and RFC 9562 cites the post as December 2012. GitHub's horizontal-sharding follow-up post was not located. Frappe's full standard-column list was not seen, and the iDempiere wiki pages were blocked. Not found or verified, and omitted: Figma "Keeping Figma fast", Cloudflare, Stack Overflow, Netflix, Zalando,
  Spotify, Intuit, Monzo and Wise, Etsy, Instacart, DoorDash, Dolibarr, Heap.

### Follow-up notes 18 to 23

- **ERP and finance (note 18).** help.sap.com pages rendered empty, and FASB Codification and PCAOB standards pages returned 403. IAS 21 and IFRS 10 full text was not read. No vendor states an exchange-rate precision. ISA 240 was not retrieved.
- **Legal (note 19).** German BMF pages returned 503. French, Italian, Spanish and Pakistani gap treatment is incomplete. Pakistani e-invoicing start dates and the UAE Article 59 amendment citation conflict. The ICO and Dutch AP are cited from Wayback captures.
- **Thin areas (note 20).** The Everest 1976 paper, published ISO/IEC 11179-5, METeOR, caDSR guidance and closure table or nested set sources were not read. Liquibase check list URLs returned 404.
- **Engines (note 21).** Native MySQL row-level security was not found in pages read, DynamoDB transactional isolation was not read, and Metric Views status is unresolved.
- **Benchmarks (note 23).** Worth a controlled benchmark: UUIDv7 on MySQL 8, RLS with join-based policies, foreign keys under parent contention on both engines, and Data Vault against star above 100 GB.

## 5. Unverified or unreachable resources

Status reading:

- `not_checked_local_ssl_error` is a failure of the script's local certificate store, not of the page.
- `bot_blocked_or_refused_*` means the host refused a script.
- `reachable` with `url_verified` false means the URL answered but the content was not verified.

### 5.1 Dead

None. GOV-24 returned a real 404 and now points to https://www.gleif.org/en/organizational-identity/lei-vlei/the-legal-entity-identifier-lei, which confirms the 20-character format and the ISO 17442 basis. Do not cite character positions from it.

### 5.2 Host refused the script, content not verified

| ID | Title | URL | Link status | url_verified |
|---|---|---|---|---|
| GOV-09 | ISO/IEC 11179-3:2023 Metadata registries (MDR), Part 3: Metamodel for registry common facilities | https://www.iso.org/standard/78915.html | bot_blocked_or_refused_403 | false |
| GOV-13 | ISO 8000-110:2021 Data quality, Part 110: Master data: Exchange of characteristic data | https://www.iso.org/standard/78501.html | bot_blocked_or_refused_403 | false |
| GOV-19 | ISO 3166, Country Codes (Parts 1-3, 2020 editions) | https://www.iso.org/iso-3166-country-codes.html | bot_blocked_or_refused_403 | false |
| GOV-22 | ISO 639:2023 Code for individual languages and language groups | https://www.iso.org/iso-639-language-code | bot_blocked_or_refused_403 | false |
| LIT-15 | Principles of Transaction-Oriented Database Recovery | https://doi.org/10.1145/289.291 | bot_blocked_or_refused_403 | false |
| LIT-17 | Sagas | https://doi.org/10.1145/38713.38742 | bot_blocked_or_refused_403 | false |
| LIT-38 | The Design of the Force.com Multitenant Internet Application Development Platform | https://doi.org/10.1145/1559845.1559942 | bot_blocked_or_refused_403 | false |
| CASE-06 | Sharding Pinterest: How we scaled our MySQL fleet | https://medium.com/pinterest-engineering/sharding-pinterest-how-we-scaled-our-mysql-fleet-3f341e96ca6f | bot_blocked_or_refused_403 | false |
| CASE-35 | Tracking the Money - Scaling Financial Reporting at Airbnb | https://medium.com/airbnb-engineering/6d742b80f040 | bot_blocked_or_refused_403 | false |
| CASE-36 | Scaling Airbnb's Payment Platform | https://medium.com/airbnb-engineering/scaling-airbnbs-payment-platform-43ebfc99b324 | bot_blocked_or_refused_403 | false |
| CASE-39 | Data Quality at Airbnb | https://medium.com/airbnb-engineering/data-quality-at-airbnb-870d03080469 | bot_blocked_or_refused_403 | false |
| CASE-40 | How Airbnb Achieved Metric Consistency at Scale | https://medium.com/airbnb-engineering/how-airbnb-achieved-metric-consistency-at-scale-f23cc53dea70 | bot_blocked_or_refused_403 | false |
| LEG-06 | UStAE section 14.5 Pflichtangaben in der Rechnung (BMF) | https://usth.bundesfinanzministerium.de/usth/2022/A-Umsatzsteuergesetz/IV-Steuer-und-Vorsteuer/Paragraf-14/ae-14-5.html | bot_blocked_or_refused_503 | false |

The university-hosted copies TXN-02 and TXN-17 were used for LIT-15 and LIT-17, as recorded in note 12.

### 5.3 Timeout or connection failure, content not verified

| ID | Title | URL | Link status | url_verified |
|---|---|---|---|---|
| CASE-20 | Sharding & IDs at Instagram | https://instagram-engineering.com/1cf5a71e5a5c | not_checked_timeout_or_connection | false |

### 5.4 URL answered the check, content not verified

| ID | Title | URL | Link status | url_verified |
|---|---|---|---|---|
| CLOUD-04 | SaaS Tenant Isolation Strategies and Multi-tenant SaaS Storage Strategies (AWS whitepapers) | https://docs.aws.amazon.com/whitepapers/latest/saas-tenant-isolation-strategies/saas-tenant-isolation-strategies.html | reachable | false |
| PIPE-22 | Fundamentals of Data Engineering: Plan and Build Robust Data Systems | https://www.oreilly.com/library/view/fundamentals-of-data/9781098108298/ | reachable | false |
| GOV-23 | ISO 20022 Repository: Data Dictionary and Business Process Catalogue | https://www.iso20022.org/financial-repository | reachable | false |
| LIT-07 | Database Design and Relational Theory: Normal Forms and All That Jazz, 2nd ed. | https://link.springer.com/book/10.1007/978-1-4842-5540-7 | reachable | false |
| LIT-08 | SQL and Relational Theory: How to Write Accurate SQL Code, 3rd ed. | https://www.oreilly.com/library/view/sql-and-relational/9781491941164/copy.html | reachable | false |
| LIT-39 | Database Internals: A Deep Dive into How Distributed Data Systems Work | https://www.oreilly.com/library/view/database-internals/9781492040330/ | reachable | false |
| LIT-42 | Database Systems: The Complete Book, 2nd ed. | https://www.pearson.com/en-us/subject-catalog/p/database-systems-the-complete-book/P200000003515/9780133002010 | reachable | false |
| LIT-49 | Agile Data Warehouse Design: Collaborative Dimensional Modeling, from Whiteboard to Star Schema | http://www.decisionone.co.uk/press/agile-data-warehouse-design-sampler.pdf | reachable | false |
| LIT-51 | Data Modeling Made Simple, 2nd ed. | https://technicspub.com/data-modeling-made-simple/ | reachable | false |
| LIT-65 | Designing Data-Intensive Applications, 2nd ed. | https://www.oreilly.com/library/view/designing-data-intensive-applications/9781098119058/ | reachable | false |
| LIT-67 | Database Reliability Engineering | https://www.oreilly.com/library/view/database-reliability-engineering/9781491925935/ | reachable | false |
| LIT-74 | Data Mesh: Delivering Data-Driven Value at Scale | https://www.oreilly.com/library/view/data-mesh/9781492092384/ | reachable | false |

CLOUD-04 should not be cited. Use the SaaS Lens for silo, pool and bridge.

### 5.5 Verified earlier, not confirmed by the 2026-11-08 script

These are not known problems. Each needs only a manual browser check.

| ID | Title | URL | Link status | url_verified |
|---|---|---|---|---|
| DES-01 | A Relational Model of Data for Large Shared Data Banks | https://www.engineering.upenn.edu/~zives/03f/cis550/codd.pdf | not_checked_local_ssl_error | true |
| TXN-02 | Principles of Transaction-Oriented Database Recovery | https://www.cs.utexas.edu/~dsb/cs386d/Readings/Recovery/Principles-of-Recovery.pdf | not_checked_local_ssl_error | true |
| TXN-14 | Consistency Tradeoffs in Modern Distributed Database System Design: CAP is Only Part of the Story | https://www.cs.umd.edu/~abadi/papers/abadi-pacelc.pdf | not_checked_local_ssl_error | true |
| TXN-17 | Sagas | https://www.cs.cornell.edu/andru/cs711/2002fa/reading/sagas.pdf | not_checked_local_ssl_error | true |
| OPS-14 | Introduction to DevOps Database Delivery | https://www.red-gate.com/simple-talk/devops/database-devops/introduction-to-devops-database-delivery/ | bot_blocked_or_refused_401 | true |
| OPS-22 | #StopRansomware Guide | https://www.cisa.gov/stopransomware/ransomware-guide | bot_blocked_or_refused_403 | true |
| LIT-30 | Architecture of a Database System | https://www.emerald.com/ftdbs/article/1/2/141/1331441/Architecture-of-a-Database-System | bot_blocked_or_refused_403 | true |
| CASE-09 | Why Uber Engineering Switched from Postgres to MySQL | https://www.uber.com/blog/postgres-to-mysql-migration/ | bot_blocked_or_refused_406 | true |
| CASE-10 | Designing Schemaless, Uber Engineering's Scalable Datastore Using MySQL | https://www.uber.com/blog/schemaless-part-one-mysql-datastore/ | bot_blocked_or_refused_406 | true |
| CASE-30 | How LedgerStore Supports Trillions of Indexes at Uber | https://www.uber.com/blog/how-ledgerstore-supports-trillions-of-indexes/ | bot_blocked_or_refused_406 | true |
| CASE-38 | Databook: Turning Big Data into Knowledge with Metadata at Uber | https://www.uber.com/blog/databook/ | bot_blocked_or_refused_406 | true |
| ENG-01 | MySQL 8.4 Online DDL Operations | https://dev.mysql.com/doc/refman/8.4/en/innodb-online-ddl-operations.html | bot_blocked_or_refused_403 | true |
| ENG-02 | MySQL 8.4 SHOW REPLICA STATUS | https://dev.mysql.com/doc/refman/8.4/en/show-replica-status.html | bot_blocked_or_refused_403 | true |
| ENG-05 | MySQL 8.4 CREATE INDEX Statement | https://dev.mysql.com/doc/refman/8.4/en/create-index.html | bot_blocked_or_refused_403 | true |
| ENG-06 | MySQL 8.4 GRANT Statement | https://dev.mysql.com/doc/refman/8.4/en/grant.html | bot_blocked_or_refused_403 | true |

GOV-20 and DES-11 are now `reachable` and have left this list. The 2026-11-08 retests of DES-01, TXN-02, TXN-14 and TXN-17 failed locally on certificate revocation checks. WebFetch did retrieve the DES-01 and TXN-14 PDFs.

## 6. Claims that must not be cited until checked

All entries come from CORRECTIONS.md and note 22. The wording below identifies each claim and is not a quotation from the source unless shown in quotation marks. Rows marked **Lifted** may be cited as described. Exact source wording for every tested item is in note 22.

### 6.1 Global rule

| Claim | Restriction |
|---|---|
| Any quoted web-page wording in the topic notes | Treat as paraphrase unless checked. Items confirmed in note 22 may be quoted in the confirmed wording. |

### 6.2 Core design and engine documentation

| Source or topic | Claim | Required handling |
|---|---|---|
| PostgreSQL wiki, "Don't Do This" | Any count of 22 anti-patterns | The correct count is 19. |
| Codd, primary key passage | Opening words of the passage | **Lifted.** Exact wording confirmed from the PDF. |
| Kent | The phrases on multiplicative to additive, ambiguous blank fields, and the key, whole key and nothing but the key | Wording differs. Use the source text in note 22. The served page reads "us the whole key", so quote only "the whole key, and nothing but the key". |
| Kimball | That keys should not encode meaning, as his words | Not found. Paraphrase only, and do not attribute the sentence to Kimball. |
| PostgreSQL docs | Section numbers 8.3, 8.14, 8.18, 9.14 | **Lifted.** Confirmed for Documentation 18. Cite with the version. |
| Karwin | 31 Flavors remedy, and closure table and nested set alternatives | Table of contents only. Remedy detail is unverified, and closure table and nested set must not be named as Karwin's content until the book is read. |
| RFC 9562 | Publication date | **Lifted.** 2024-05-07, from page metadata. |
| dbt | Example casting money to float | Exact wording confirmed. Record as a conflict with the exact-decimal rule. Do not cite as good practice. |

### 6.3 Transactions and consistency

| Source or topic | Claim | Required handling |
|---|---|---|
| MongoDB | TransientTransactionError and UnknownTransactionCommitResult labels | **Lifted.** Sourced to the MongoDB transactions-in-applications page. |
| Oracle | ORA-01555 | **Lifted.** Sourced to the Oracle error-help page. |
| MySQL | Section "17.7.2.1" | **Lifted.** Sourced for MySQL 8.4. |
| Jepsen | MySQL anomaly list and the MongoDB write-conflict sentence | Jepsen MySQL wording differs, and the note merged two sentences. Quote them separately. The write-conflict sentence is confirmed, attributed to MongoDB docs rather than Jepsen. |
| PACELC | Definition | **Lifted.** Exact wording confirmed from the PDF. May be quoted. |
| Gilbert and Lynch 2002 | Formal content | **Lifted.** The catalogued PDF has an extractable text layer. |
| Gilbert and Lynch 2012 Perspectives paper | Specific claims | Title and authors confirmed and text extractable. Check each claim individually. |
| DDIA | That C does not belong in ACID | Not verified against the book. Needs a licensed copy. |

### 6.4 Migrations and backup

| Source or topic | Claim | Required handling |
|---|---|---|
| DORA | The rigor, test-every-change and DBA-consultation lines | The same-rigor phrase was not found, so use the source text in note 22. Test-every-change is confirmed. DBA-consultation wording differs. |
| Braintree 2019 | The duration and rollback lines | Wording differs. Use the source text in note 22. |
| GitLab | The reversible migrations and Arel lines | Wording differs. Use the source text in note 22. |
| evodb | The version-control line | Exact wording confirmed for the section heading. The migration-script line differs. Use the source text in note 22. |
| strong_migrations | The write-blocking line | **Lifted.** Exact wording confirmed. |
| Testcontainers | Definition ending | **Lifted.** Exact wording confirmed on the served page. |
| ISO 22301 | Details | From the EVS national record. Cite as such. |

### 6.5 Performance and books

| Source or topic | Claim | Required handling |
|---|---|---|
| Note 11, Key Question 7 | Count of thirty-one resources and 45 verified pages | Wrong. The notes cite 58 pages. |
| DDIA | Chapter-level claims, including chapter 3 contents | Unverified. Needs a licensed copy. |
| Oracle `/23/` URLs | Any claim of 23ai provenance | All six checked URLs report Release 26 and redirect to `/26/`. Cite as Release 26 or use the final URL. |
| "One Size Fits All" | ICDE 2005 venue | Not found in the PDF text. Source the venue elsewhere or drop it. |
| Note 16 annotations | Karwin anti-pattern names, Force.com flex-column details, Hay and Silverston contents, PACELC classifications, some page numbers | Background knowledge. Do not present as source-verified. |
| LIT-02, LIT-03, LIT-13, LIT-21, LIT-22 | Content or details noted as weak | DBLP record only, 5-page excerpt, year from the brief, and IEEE details partly from memory. |
| Date, Introduction to Database Systems, 8th ed. | Any catalog citation | Omitted (404). |

### 6.6 Architecture, tenancy and data quality

| Source or topic | Claim | Required handling |
|---|---|---|
| CLOUD-04 | Any content from the AWS whitepapers | The URL redirects to the SaaS Lens landing page. Stop citing it. Read the specific SaaS Lens subpage before citing silo, pool or bridge. |
| Gartner | Definitions | Third-party only. |
| Data Fabric | Any claim of independent primary support | None exists in the notes. |
| Airbnb Wall and Midas | Architecture and certification details | Search snippets only. |
| Sanderson manifesto | Direct attribution | Known only through InfoWorld. |

### 6.7 Case studies

| Source or topic | Claim | Required handling |
|---|---|---|
| Note 17 count | Any resource count | 47 of 53 catalogued resources were fetched. |
| Pinterest, Instagram, 4 Airbnb posts | Any content | Search only and unverified. |
| A12 Instagram | Late-2011 date | Not found. RFC 9562 cites the post as December 2012, and the post itself is unread. |
| A11 | Snowflake IDs as the template for Instagram, Discord and Pinterest | Unsourced inference. Pinterest's ID has no time component. |
| A13 TAO | Description as over sharded MySQL or a relational store | Not found on the page read. The paper PDF was not read. |
| Summary lesson 6 | "NOT VALID" | **Lifted.** Braintree 2019 supports it. |
| Summary lessons 2 and 4 | Instagram as evidence | That post is unverified. |
| Theme F | Record-level versioning for optimistic locking | Unsourced. |
| Theme F, Frappe | Standard columns beyond those seen | Keep the restriction. Only docstatus was confirmed at retest, on the docstatus page. |
| Theme F, iDempiere | Columns beyond the AD_Org interface | Verified on that interface only. |
| A9, B6, C5 | gc_grace_seconds, "pre-PG 11 behavior", Brandur as former Stripe engineer | A9: the parameter name is not on the page, so use the Discord wording. B6 is supported by Braintree 2019. C5 is supported in substance by Brandur's about page. |

## 6a. Gaps found while writing the deliverables

These surfaced after the topic-level review and matter most for ERP and financial systems.

| Area | What is missing | Where it is discussed |
|---|---|---|
| Fiscal period close | Partly closed. Vendor period-status and lock designs are in note 18. SAP product docs and NetSuite adjustment periods remain unread or unstated. | `industry_best_practices.md`, `design_decision_matrix.md` |
| Multi-currency | Partly closed. Rate keys, rate roles and functional currency are in note 18. No vendor or standard setter read states a rate precision. | `industry_best_practices.md`, `database_design_standards.md` |
| Gapless numbering | Partly closed. Positions by jurisdiction are in note 19, and no single gap-free rule can be derived. The locked-counter implementation remains inference. Needs legal review. | `industry_best_practices.md` |
| Ledger invariants | Partly closed. HGB and AO non-alteration rules are MANDATORY in Germany, and correction by new entry is the vendor norm (note 18). No law read requires database immutability or hashing. | `design_decision_matrix.md` |
| Foreign keys at scale | Still open. One small PostgreSQL practitioner test exists (note 23), and no at-scale or MySQL measurement was found. No verdict is offered. | `industry_best_practices.md` |
| Retention law | Partly closed. Periods for Germany, France, the UK, the US, Pakistan, the UAE and Saudi Arabia are in note 19. Italian and Spanish periods were not researched in depth. Needs legal review. | `database_security_standards.md` |
| Erasure | Still unsettled after note 19. EDPB, ICO, AP and California text on backups was read. No regulator text found accepts key destruction as erasure or addresses soft deletion by name. Legal review is required. | `database_security_standards.md` |
| Standards text | Open. PCI DSS v4.0.1, ISO/IEC 27001 Annex A and CIS Benchmark contents were not read. Needs licensed copies. PCI wording in note 19 is v4.0 SAQ D. | `database_security_standards.md` |
| Benchmarks | Partly closed. Note 23 records practitioner key benchmarks, conflicting One Big Table results and HTAP studies. No peer-reviewed key benchmark, realistic Data Vault benchmark or validation-layer defect-rate comparison was found. | `architecture_comparison.md` |
| Schema-per-tenant | No primary source assesses it. Its decision row is left unclassified. | `design_decision_matrix.md` |

**Catalog counts.** The 22 topic catalogs total 671 rows. Merging removed 77 duplicates and left 594 unique resources, so a topic can have fewer rows in the combined catalog than in its own file. Literature has 60 rows in the combined catalog.

## 7. Prioritised follow-up list

Status of each item as of 2026-11-08. Status is closed, partly closed or open. Owner is one of: **web research done** (no further web research is planned), **needs owner in browser**, **needs licensed copy**, **needs legal review**. Items 29 and 30 were added from note 19 and section 6a. Totals are given after the tables.

### P1: required before any Stage 2 standard cites the source

| # | Item | Status | Owner | Position |
|---:|---|---|---|---|
| 1 | Paywalled standards: ISO/IEC 11179-5, 9075, 25012, ISO 8000 | Partly closed | Needs licensed copy | 11179-5 from a 2004 draft, 25012 from a secondary site, ISO 8000 from Wikipedia. ISO/IEC 9075 and all published text unread. |
| 2 | ISO/IEC 27001 and 27002, ISO 22301, ISO/IEC 38505-1:2026, ISO 15489-1 | Open | Needs licensed copy | Not read. |
| 3 | DAMA-DMBOK: knowledge areas, data modeling content, publication year | Partly closed | Needs licensed copy | DAMA says 11 knowledge areas and names six. Full list, content and 2017 date not confirmed. |
| 4 | DDIA: replace chapter-level claims | Open | Needs licensed copy | Not read. |
| 5 | Karwin's SQL Antipatterns | Open | Needs licensed copy | Table of contents only. |
| 6 | Date on normal forms; primary texts for BCNF, 4NF, 5NF, 6NF | Open | Needs licensed copy | Not read. |
| 7 | Simsion and Witt, and Hoberman | Open | Needs licensed copy | Not read. |
| 8 | Re-verify quoted wording in section 6 | Closed | Web research done | Note 22 records a result for Kent, Kimball, DORA, Braintree, GitLab, evodb, strong_migrations and Jepsen. The Kimball sentence and the DORA same-rigor phrase were not found and must not be quoted. |
| 9 | Remove or source items marked general knowledge or from memory | Partly closed | Needs licensed copy | Most sourced in note 22. Karwin and Hay and Silverston contents need the books. A11 and Theme F versioning have no source to test and should be removed or sourced. |

### P2: closes thin coverage areas

| # | Item | Status | Owner | Position |
|---:|---|---|---|---|
| 10 | Testing and schema validation sources, Testcontainers definition | Closed | Web research done | Schemalint, utPLSQL, prisma-lint and EF Core read in note 20, and the definition is confirmed in note 22. No EF-specific schema-design analyzer was found. |
| 11 | Naming: singular or plural as a framework decision | Partly closed | Web research done | Evidence recorded as contested in note 20. The decision belongs to Stage 2. |
| 12 | ER design: notation origin and subtype guidance | Partly closed | Web research done | FIPS 184, two origin pages and ORM subtype sources read. The Everest 1976 paper is unread. |
| 13 | Governance: replace secondary content in note 08 | Partly closed | Needs licensed copy | Note 20 improved the sources. Replacement depends on items 1 to 3. |

### P3: closes engine and platform gaps in adequate areas

| # | Item | Status | Owner | Position |
|---:|---|---|---|---|
| 14 | MySQL online DDL, replication-lag docs, foreign keys to partitioned tables | Closed | Web research done | Note 21. MySQL read through the fetch tool. PostgreSQL child side not confirmed. |
| 15 | Date and time semantics, MongoDB date modeling, NULL in UNIQUE | Closed | Web research done | Note 21. The MySQL time zone page and SQL Server `AT TIME ZONE` were not opened. |
| 16 | Oracle Unified Auditing, MongoDB auditing, RMAN, Always On | Closed | Web research done | Note 21. |
| 17 | Databricks transactions, Metric Views and `RELY` | Partly closed | Web research done | Transactions and `RELY` read. Metric Views status as a whole is unresolved. |
| 18 | Temporal books and Envers ValidityAuditStrategy | Partly closed | Needs licensed copy | Envers read in note 21. Books not read. |
| 19 | SAP company code, NetSuite subsidiary, fiscal-calendar and exchange-rate sourcing | Partly closed | Needs owner in browser | Note 18 covers NetSuite, fiscal calendars and rates. help.sap.com rendered empty, so no official company code definition was read. |
| 20 | GDPR official text, PCI DSS v4.0.1, California Civil Code wording | Partly closed | Needs licensed copy | GDPR and the CPPA-hosted statute are read. PCI DSS v4.0.1 text was not accessible. leginfo was not opened. |

### P4: resource and catalog hygiene

| # | Item | Status | Owner | Position |
|---:|---|---|---|---|
| 21 | GOV-24: working source or remove | Closed | Web research done | Replaced with an official GLEIF page. |
| 22 | Open section 5.2 and 5.3 resources in a browser | Open | Needs owner in browser | 19 sites refused automated access, from note 22: GOV-09, GOV-13, GOV-19, GOV-22, OPS-14, OPS-22, LIT-15, LIT-17, LIT-30, LIT-38, CASE-06, CASE-09, CASE-10, CASE-30, CASE-35, CASE-36, CASE-38, CASE-39, CASE-40. |
| 23 | Local link failures | Partly closed | Needs owner in browser | GOV-20 and DES-11 are now reachable. Five local failures remain: DES-01, TXN-02, TXN-14, TXN-17 and CASE-20. |
| 24 | Replace CLOUD-04 with the SaaS Lens | Closed | Web research done | The deliverables use the SaaS Lens. Read the specific subpage before citing silo, pool or bridge. |
| 25 | Reconcile literature and case-study counts | Closed | Web research done | The differences come from duplicate removal. See section 2. |
| 26 | Oracle `/23/` provenance | Closed | Web research done | All six URLs report Release 26. |
| 29 | Confirm the two Wayback-only regulators on live sites | Open | Needs owner in browser | ICO (LEG-33) and Dutch AP (LEG-35). |

The catalog also records refusals outside the 19 sites in item 22: LEG-06 (503) and ENG-01, ENG-02, ENG-05 and ENG-06 (dev.mysql.com, 403). The catalog still holds the older URLs for GOV-20 and the six Oracle `/23/` entries, so check the final URLs in note 22 when citing them.

### P5: evidence that may not exist

| # | Item | Status | Owner | Position |
|---:|---|---|---|---|
| 27 | Independent benchmarks: UUIDv7, RLS, Data Vault and One Big Table, HTAP | Partly closed | Web research done | Note 23. HTAP and One Big Table have some independent evidence. UUIDv7, RLS and Data Vault at scale do not. |
| 28 | Express unmeasured items as judgments in standards | Open | Web research done | Applies when Stage 2 writes standards. |

### Legal

| # | Item | Status | Owner | Position |
|---:|---|---|---|---|
| 30 | Counsel review of retention, invoice numbering gaps and erasure (backups, key destruction, soft deletion) | Open | Needs legal review | Note 19 is research input and not legal advice. Its conflicts and not-settled positions need counsel. |

### Totals

| Status | Items |
|---|---:|
| Closed | 9 |
| Partly closed | 12 |
| Open | 9 |
| **Total** | **30** |

| Owner | Items |
|---|---:|
| Web research done | 14 |
| Needs owner in browser | 4 |
| Needs licensed copy | 11 |
| Needs legal review | 1 |
