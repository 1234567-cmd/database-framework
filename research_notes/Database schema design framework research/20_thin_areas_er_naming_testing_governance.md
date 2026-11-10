# Thin areas: ER design, naming, testing and schema validation, documentation and governance

Status as of 2026-11-08. Research only: this note holds no framework rules or schemas. Catalog: `catalog_20_thin_areas.json`, THIN-01 to THIN-30.

Scope: areas 3, 6, 18 and 20 rated Thin in `research/research_gaps.md`, section 3.

## Reading guide

- Quotation marks show text extracted directly by curl or pdftotext. Everything else is paraphrase.
- Labels describe the strength of the source's own statement, within the scope shown. MANDATORY means the source states a hard limit or requirement in its own domain. It never means the framework must adopt it.
- "Inference" marks my reasoning, which no source states.
- WebSearch summaries were used only to locate pages. Where a fact rests only on a search result, it says so.

## Summary of what changed

| Area | Gap in research_gaps.md | Result |
|---|---|---|
| 3 ER design | Crow's foot origin from snippets; no read source for notation or subtype | Partly closed. FIPS 184 read directly. Everest origin now rests on two opened pages, but the 1976 paper is still unread. Subtype trade-offs read from Hibernate and EF Core. |
| 6 Naming | 11179-5 scope only; no vendor naming guidance | Partly closed. A 2004 committee draft gives the rule structure. Oracle does publish naming guidelines. Published 11179-5 text is still unread. |
| 18 Testing | No source for foreign key index, reserved-word or tenant checks | Largely closed. See the matrix. Money type and reserved-word checks remain weak. |
| 20 Governance | DMBOK, 11179, 25012 and 38505 unread | Partly closed. ISO 25012 definitions read from a secondary site. DMBOK status and revision facts confirmed from DAMA. DMBOK text, DCAM text and ISO/IEC 38505 remain unread. |

## 1. ER design

### 1.1 Crow's foot origin (THIN-02)

- Redgate's article, formerly on Vertabelo, says: "The beginning of crow's foot notation dates back to an article by Gordon Everest (1976, Fifth Computing Conference, IEEE)."
- It quotes Everest by correspondence: "I called it the "inverted arrow." at the time to distinguish [it] from Bachman's notation."
- He preferred it because "it did not imply directionality or a physical access path, and it was visually intuitive, showing manyness."
- The Runestone textbook independently attributes the family to Everest in 1976 and says the symbol was called an "inverted arrow", and later a "fork".
- **OPTIONAL/CONTEXTUAL, general:** the origin is historical context and carries no design requirement.
- **Conflict:** Redgate's body text says "Fifth Computing Conference, IEEE". Its footnote cites "Computing Systems 1976, Proceedings Fifth Texas Conference on Computing Systems, Austin,TX, 1976 October 18-19, pages 39-46".
- **Gap:** the 1976 paper was not opened. A search result claims the minimum-cardinality circle and bar were later additions. That comes from a low-authority blog and is unverified.

### 1.2 Cardinality and optionality

- Runestone: the symbol nearest the entity shows maximum cardinality, and the farther symbol shows minimum cardinality. Zero means optional and one means mandatory.
- FIPS 184 section 3.5.1 lists five cardinalities from the parent's perspective: zero or more, at least one, zero or one, an exact number, and a range.
- FIPS 184 figure 4 uses P for one or more, Z for zero or one, and a number or range for exact counts.
- **RECOMMENDED, general modeling:** notation varies by tool. Runestone states "Different drawing and modeling tools may or may not provide direct support for these, and notations vary widely."

### 1.3 IDEF1X (THIN-01)

- Issued 1993-12-21 and effective June 30, 1994, for US federal use. The full text was read by pdftotext.
- Rules of section 3.5.4, read directly:
  - A specific connection relationship "is always between exactly two entities".
  - In identifying and mandatory non-identifying relationships, each child instance is associated with exactly one parent instance.
  - In an optional non-identifying relationship, the child has zero or one parent.
  - "Only non-identifying relationships may be recursive".
- Section 3.6: a category cluster is complete if every generic instance has a category instance, and incomplete if some categories are omitted.
- Rule (h) in the category rules: the discriminator of a complete cluster "must not be an optional attribute."
- Annex A3.4.1: at the key-based phase "only a specific relationship form" may be used, so many-to-many relationships must be refined.
- **MANDATORY within IDEF1X conformance only (historical US federal scope).** Status: withdrawn. Wikipedia gives September 2, 2008 and Federal Register vol. 73 page 51276. No NIST notice was opened.
- ISO/IEC/IEEE 31320-2:2012 is reported as the successor by Wikipedia and an IEC listing in a search result. Its text was not read.

### 1.4 Supertype and subtype (THIN-03, 04, 05)

| Option | Fowler | Hibernate | EF Core |
|---|---|---|---|
| One table for hierarchy | Single Table Inheritance | SINGLE_TABLE: "Attributes declared by subclasses map to columns without NOT NULL constraints." Subclass data denormalized. | TPH: default. "Database columns are automatically made nullable as necessary when using TPH mapping." |
| One table per class | Class Table Inheritance | JOINED: any attribute may be NOT NULL, any association may have a foreign key, tables normalized. "The best option when we care a lot about constraints and normalization." | TPT: "In many cases, TPT shows inferior performance when compared to TPH." |
| One table per concrete class | Concrete Table Inheritance | TABLE_PER_CLASS: UNION to read. "Associations targeting a superclass cannot have a corresponding FOREIGN KEY constraint in the database." | TPC: tables per concrete type; addresses some TPT performance problems. |

- **RECOMMENDED, OLTP with an ORM:** the sources agree on the shape of the trade-off: one table costs NOT NULL enforcement, joined tables cost joins, and concrete tables cost superclass foreign keys.
- **Conflict:** Hibernate favours JOINED when constraints matter, while EF Core defaults to TPH and warns on TPT performance. They optimise for different goals, so neither is a universal default.
- **Gap:** EF Core's performance page with measurements was not opened. No engine-neutral benchmark was found.
- **Scope limit:** these are ORM mapping sources. Database-native subtype enforcement, such as an exclusive-arc constraint, was not covered. Simsion and Witt and similar books remain unread.

### 1.5 Many-to-many (THIN-06, THIN-01)

- EF Core: a many-to-many relationship "cannot be represented in a simple way using just a foreign key" and uses a join table, which the ORM may hide.
- FIPS 184 models it as a non-specific relationship and requires refinement before the key-based phase.
- **RECOMMENDED, relational OLTP:** a join table is the convergent answer. Whether the join row needs its own attributes or identity is a design choice not settled by these sources.

### 1.6 Hierarchies (THIN-07)

Microsoft compares `hierarchyid` with parent/child:

| Operation | Stated result |
|---|---|
| Subtree queries | "significantly faster with hierarchyid" |
| Direct descendant queries | slightly slower with hierarchyid |
| Moving nonleaf nodes | slower with hierarchyid |
| Moving a row | parent/child affects a single row; hierarchyid affects n rows in the subtree |

- Microsoft notes hierarchyid relationships aren't enforced like a foreign key, and uniqueness needs a constraint.
- PostgreSQL's recursive query docs warn that a recursive query will loop if link relationships contain cycles, and show cycle detection.
- **OPTIONAL/CONTEXTUAL, OLTP, SQL Server specific:** statements carry no numbers.
- **Gap:** closure table and nested set options have no opened source here. PostgreSQL `ltree` was downloaded, but only its title was reviewed.

## 2. Naming

### 2.1 ISO/IEC 11179-5 (THIN-08, THIN-09)

Source read: ISO/IEC FCD 11179-5 dated 2004-01-09. It is a committee draft, and it was only partly downloaded.

- A naming convention covers scope, authority, semantic, syntactic, lexical and uniqueness rules.
- The draft says the scope "of each naming convention represented in the MDR shall be documented", and the same for authority. Semantic, syntactic, lexical and uniqueness rules "should be documented".
- Annex A is informative. Its example rule sets require one object class term, one property term and one representation term. The object class comes first and the representation term last.
- Example: "Cost Budget Period Total Amount".
- Lexical example: "Nouns are used in singular form only, unless the concept itself is plural."

Labels and limits:

- **RECOMMENDED, metadata registries:** the structure of a convention. Scope and authority are "shall" for registry entries in this draft.
- **OPTIONAL/CONTEXTUAL:** the singular noun rule. It is an informative example for registry names of data elements, not for table names. Treating it as support for singular tables would be an inference.
- **Gap:** the published 2005 and 2015 editions were not read. Search results report a fourth edition in draft, not confirmed from an opened ISO page. Wording may have changed.

### 2.2 Free availability

- `standards.iso.org/ittf/PubliclyAvailableStandards` reads: "The ISO/IEC Information Technology Task Force (ITTF) web site is now closed." Deliverables are said to be at no charge on the ISO and IEC webstores.
- The JTC 1/SC 32 page lists ISO/IEC 11179-1:2004, -2:2005, -3:2003, -4:2004, -5:2005 and -6:2005 as freely available. These are older editions.
- **Gap:** the current webstore free list could not be read (the IEC path tried returned 404, and ISO product pages returned 403). No download of 11179-5:2005 was obtained.

### 2.3 METeOR and caDSR

- METeOR (`meteor.aihw.gov.au`) returned 403 to both curl and WebFetch.
- caDSR: `cadsr.cancer.gov` returned no usable content; the cancer.gov path tried returned 404.
- A search result states caDSR data elements are built from object class, property and representation term, but no NCI curation document was opened.
- **Gap:** neither registry was read. They are omitted from the catalog.

### 2.4 Framework and organization conventions

| Source | Table name form | Other conventions read | Label |
|---|---|---|---|
| Rails (THIN-10) | Plural snake_case: "book_clubs" for BookClub | Foreign key `singularized_table_name_id`; `created_at`; `lock_version`; `(association_name)_type` | RECOMMENDED, Rails OLTP (overridable) |
| Django (THIN-11) | App label plus lowercased class: "bookstore_book" | Advises lowercase names when overriding on MariaDB and MySQL | RECOMMENDED, Django OLTP |
| EF Core (THIN-12) | Same name as the DbSet property, or class name if none. Commonly plural because of `Blogs` naming, which is inference | Index `IX_<type name>_<property name>` | RECOMMENDED, EF Core OLTP |
| Hibernate (THIN-04) | JPA-compliant implicit naming by default. Logical name is the physical name under Jakarta Persistence | Pluggable implicit and physical strategies | OPTIONAL/CONTEXTUAL |
| Prisma (THIN-13) | Model singular PascalCase recommended; `@@map` keeps plural snake_case tables | Says plural snake_case is "A common approach" | RECOMMENDED, Prisma |
| GitLab (THIN-14) | Examples use plural (`projects`, `groups`); no explicit rule found | `fk_<table name>_<column name>...`, `index_<table name>_on_<column name>...`, `unique_`, `check_`; prefixes preferred over suffixes | MANDATORY inside GitLab only |
| Oracle (THIN-15) | Not addressed | See below | Mixed |

Oracle:

- **MANDATORY, Oracle:** "Nonquoted identifiers cannot be Oracle SQL reserved words." Names run from 1 to 128 bytes under COMPATIBLE 12.2 or higher, and 1 to 30 bytes below that, with exceptions.
- **RECOMMENDED, Oracle:** "Oracle does not recommend using quoted identifiers for database object names."
- **RECOMMENDED, Oracle:** guidelines say to "Use full, descriptive, pronounceable names" and "Use the same name to describe the same entity or attribute across tables."
- This corrects the gap statement that no vendor prescribes naming beyond identifier rules.

Zalando:

- **Gap:** no Zalando database naming guideline was found. The Zalando RESTful API guidelines (opened) have "MUST pluralize resource names" and snake_case properties, but they apply to APIs. They are not evidence for tables and are not catalogued.

### 2.5 Singular versus plural: evidence

| Singular | Plural |
|---|---|
| Django default (singular class name) | Rails default |
| Prisma recommendation for model names | Prisma's statement of common database practice |
| 11179-5 draft annex (data element names, informative) | GitLab examples (Rails application) |
| Schemalint README example `"singular"` (a sample config only) | EF Core examples, by convention of DbSet name (inference) |

- **Finding: OPTIONAL/CONTEXTUAL, general.** The primary sources split. Defaults follow each framework's mapping style. No source read provides evidence of an outcome difference.
- Linters treat it as configurable: Schemalint `name-inflection` and prisma-lint `model-name-grammatical-number` accept either style.
- Search results show blogs on both sides. None is a primary source, and none is used here.

## 3. Testing and schema validation

### 3.1 Capability matrix

Legend: **B** built-in rule or assertion read in source or docs. **C** documented custom or example rule. **A** possible by assertion on a named object. **I** inference: mechanism exists, no doc shows this use. **–** not found in pages read.

| Tool | FK index | Reserved words | PK present | Required columns | Money types | Tenant key |
|---|---|---|---|---|---|---|
| Schemalint (THIN-16) | B `index-referencing-column` | – | B `require-primary-key` | B `mandatory-columns` | I custom rule | I via `mandatory-columns`; B `row-level-security` covers RLS only |
| Squawk (THIN-17) | – | – | – | – (`adding-required-field` is migration safety) | – | – |
| SQLFluff (THIN-18) | – | B RF04, partial | – | – | – | – |
| Atlas (THIN-19) | C `require-index-fk-columns` (Pro) | – | I custom predicate | C `table-required-columns`, `id-column-required` (Pro) | I type predicate | I `has_column` predicate |
| Liquibase (THIN-20) | I custom | – | I custom | I custom | I custom | I custom |
| pgTAP (THIN-21) | A `is_indexed`, `has_index` | – | A `has_pk`, `col_is_pk` | A `has_column`, `columns_are`, `col_not_null` | A `col_type_is` | A `has_column` |
| tSQLt (THIN-22) | I on metadata | – | I on metadata | A `AssertEqualsTableSchema` | A `AssertEqualsTableSchema` (compares data types) | I |
| utPLSQL (THIN-23) | I dictionary query | – | I | I | I | I |
| prisma-lint (THIN-24) | B `require-field-index` with `forAllRelations` | – | – | B `require-field` | B `require-field-type` by field name | B `require-field`; docs use `tenantId` in examples |
| EF Core (THIN-12) | Default convention creates the index | – | – | – | – | – |
| Testcontainers (THIN-25) | Hosts tests, performs no checks | | | | | |

Cautions on the matrix:

- "–" means not found in the pages read. Only Schemalint's rule files and the rule lists were covered closely. It is not proof of absence.
- Grep for the word `money` found nothing in the Schemalint, Squawk, SQLFluff (three categories), Atlas, prisma-lint, Liquibase custom, utPLSQL or pgTAP text.
- prisma-lint and Schemalint inspect different things: schema file versus live catalog.

### 3.2 Tool notes

- **Schemalint. RECOMMENDED, PostgreSQL OLTP.** The rule file reads `description: "Require index on referencing column of foreign keys"`. A violation carries a suggested `CREATE INDEX`.
- **Squawk. RECOMMENDED, PostgreSQL migrations.** Its rules "focus on ensuring safe migrations". Its foreign key rule concerns locks ("requires a table scan and a SHARE ROW EXCLUSIVE lock on both tables"), not indexes.
- **SQLFluff. OPTIONAL/CONTEXTUAL.** RF04 limit: "reserved keywords cannot be used as unquoted identifiers and will cause parsing errors and so are not covered by this rule." Its rule title is "Avoid keywords as the name of an alias", with a policy that can extend to other unquoted identifiers. Reserved-word coverage is therefore partial and dialect dependent.
- **Atlas. OPTIONAL/CONTEXTUAL (paid).** Naming analyzer: tables, columns, indexes, and also "schema, table, column, foreign_key and check". Reported violations do not fail by default. "The schema linting rules language is available exclusively to Pro users."
- **Liquibase. OPTIONAL/CONTEXTUAL (paid).** Secure license required. Only `TableColumnLimit` and `ObjectNameMustMatch` were seen by name.
- **pgTAP. RECOMMENDED, PostgreSQL.** Assertions exist for each structural item, but must be written per object.
- **tSQLt. RECOMMENDED, SQL Server.** "Remember if you are faking a table, you are not testing the constraints on the table."
- **EF Core.** "By convention, an index is created in each property (or set of properties) that are used as a foreign key." `HasPendingModelChanges()` can back a unit test that fails when a migration is missing. **No EF-specific schema-design analyzer was found.** The Roslyn page covers general code analysis, and `EFCore.NamingConventions` is a third-party package.
- **Testcontainers.** "Testcontainers is a library that provides easy and lightweight APIs for bootstrapping local development and test dependencies with real services wrapped in Docker containers." This fills the definition gap in research_gaps.md.

### 3.3 Foreign key indexes: direct conflict of defaults

- GitLab (**MANDATORY inside GitLab, PostgreSQL OLTP**): "When adding a foreign key in PostgreSQL, the column is not indexed automatically. Thus, you must also add a concurrent index."
- GitLab accepts a composite index when the foreign key is in the first position.
- EF Core creates the index by convention. Schemalint and prisma-lint check for it.
- Inference: the need depends on engine and on who creates the index. Exceptions were not surveyed.

### 3.4 Tenant keys

- Of all tools read, only prisma-lint documentation uses `tenantId`, and only in examples.
- Schemalint's `row-level-security` and Atlas's `ensure-row-security-enabled` check RLS, which differs from a tenant column check.
- GitLab's sharding key section has moved. The new location was not opened, so GitLab's actual tenant key rule is unread.
- **Gap:** no tool ships a built-in rule named for tenant keys. Every option found is a configurable required-field rule.

## 4. Documentation and governance

### 4.1 DAMA (THIN-26)

Read directly from dama.org:

- DAMA says DMBOK organizes data management "into 11 knowledge areas". The page names only six: Data Governance, Data Quality, Data Security, Data Architecture, Metadata Management, and Data Integration & Interoperability.
- DMBOK is "Not a Prescriptive Standard" and "Not a Regulation or Compliance Mandate".
- The Revised Edition FAQ says it would be available from Technics Publications "by April 2024", and that it addresses known inconsistencies and inaccuracies.
- "In 2024 DAMA launched the DAMA DMBOK® 2.0 Revision".
- "The DAMA-DMBOK® 3.0 project started in 2025".

Labels and limits:

- **OPTIONAL/CONTEXTUAL, general:** by DAMA's own statement, DMBOK is reference material and should not be cited as a binding requirement.
- **Conflict resolved in part:** research_gaps.md notes a knowledge-area count conflict. DAMA's current page says 11.
- **Gap:** no opened DAMA page lists all 11. A secondary search result places Data Modeling and Design among them. The 2017 date of the second edition rests on a Dataversity result in search, not an opened DAMA page. Book content is unread.

### 4.2 DCAM (THIN-27)

- "DCAM is available exclusively to our member firms."
- Public facts: DCAM v3, eight core components, "34 capabilities and 101 sub-capabilities", and a scoring matrix with auditable evidence.
- v3 consolidates Architecture capabilities into one component and adds Business Data Knowledge.
- The site refers to both "EDM Council" and "EDM Association".
- **OPTIONAL/CONTEXTUAL, enterprise programs.** **Gap:** full component list and all capability text.

### 4.3 ISO/IEC 25012 (THIN-28)

iso25000.com is a secondary site, and it gives definitions for all 15 characteristics.

| Group | Characteristics |
|---|---|
| Inherent | Accuracy, Completeness, Consistency, Credibility, Currentness |
| Inherent and system-dependent | Accessibility, Compliance, Confidentiality, Efficiency, Precision, Traceability, Understandability |
| System-dependent | Availability, Portability, Recoverability |

- Schema relevant wording: Completeness is the degree to which "subject data associated with an entity has values for all expected attributes and related entity instances".
- Traceability concerns "an audit trail of access to the data and of any changes made to the data".
- **RECOMMENDED as vocabulary, general.** Confirm against the standard before citing it as ISO text.
- ISO 25012's list is now verified, but only at secondary level.

### 4.4 ISO 8000 (THIN-29)

- Wikipedia lists parts including ISO 8000-2:2022 (vocabulary), -8:2015, -61:2016, -100:2016, -110:2021, -150:2022 and sensor parts. ISO 8000-102:2009 is marked withdrawn.
- ISO 8000-1:2022 appears in search results only. The ANSI preview returned 403.
- **OPTIONAL/CONTEXTUAL, master data exchange.** Inventory at community level only.
- **Gap:** no ISO 8000 part was confirmed free. The SC 32 list covers SC 32 standards, which excludes ISO 8000 according to its contents. One search result pointed to an apparent unauthorized copy, which was not opened.

### 4.5 Data dictionary and ADR practice (THIN-30)

- PostgreSQL `COMMENT`: "COMMENT stores, replaces, or removes the comment on a database object." Only one comment string is stored per object.
- Atlas's rule examples include requiring a specific comment on PII columns.
- Nygard's ADR format has Context, Decision, Status and Consequences.
- AWS: "When the team accepts an ADR, it becomes immutable." A new ADR supersedes the earlier one.
- **RECOMMENDED, general:** ADRs are a documented practice. No source applies them specifically to schema design, so that use is inference.
- **Gap:** the USGS data dictionary page returned 202 with no content. No authoritative data dictionary standard was read.

### 4.6 ISO/IEC 38505

Not resolved. The ISO page tried returned 403, and no other source was opened.

## 5. Conflicts recorded

1. Crow's foot venue: "Fifth Computing Conference, IEEE" against "Fifth Texas Conference on Computing Systems" (same Redgate page).
2. Subtype default: Hibernate favours JOINED for constraints; EF Core defaults to TPH and warns about TPT performance.
3. Singular versus plural: Rails and GitLab examples plural; Django and Prisma models singular; Prisma itself describes the opposite as common.
4. Prior statement that no vendor gives naming guidance: Oracle's guidelines contradict it.
5. Foreign key indexes: created automatically by EF Core; PostgreSQL leaves it to the developer, per GitLab.
6. "Required field" has two meanings: Squawk's `adding-required-field` concerns migration safety, while Schemalint, Atlas and prisma-lint mean a table policy.

## 6. Unresolved gaps

| Item | State |
|---|---|
| Everest 1976 paper | Not opened |
| Published ISO/IEC 11179-5 (2005 or 2015) | Not read; only a truncated 2004 draft |
| ISO and IEC webstore free lists | Not readable |
| METeOR | 403 |
| caDSR curation guidance | Not found |
| Zalando database naming | Not found |
| Liquibase built-in check list | Catalog URLs returned 404 |
| GitLab sharding key page | Moved; not opened |
| EF Core inheritance measurements | Not opened |
| Closure table and nested set sources | Not read |
| Full 11 DMBOK knowledge areas from DAMA | Not on the pages opened |
| DMBOK2 2017 date from DAMA | Not confirmed |
| DMBOK, DCAM and ISO 8000 text | Gated |
| ISO/IEC 38505, ISO/IEC 25012 official text | Not read |
| Tool coverage for money types and reserved words | No built-in rule found, aside from SQLFluff RF04 partial and prisma-lint's generic type rule |

## 7. Method notes

- Git-bash curl failed with error 43 on many hosts, so System32 `curl.exe` was used. Early 000 results were local tool failures, not site failures.
- Pages were converted to text with a local script and searched by keyword. Long pages were read in part, so absence claims are limited to the text covered.
- URLs in the catalog were all opened on 2026-11-08 with HTTP 200, except the 11179-5 draft, which returned 200 but was truncated.
