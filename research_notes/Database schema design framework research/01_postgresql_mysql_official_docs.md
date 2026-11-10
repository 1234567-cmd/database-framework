# PostgreSQL and MySQL Official Documentation: Prescriptions for Database Schema Design

Research scope: official PostgreSQL documentation (postgresql.org/docs/current = PostgreSQL 18.6 as of 2026-11-07), the official PostgreSQL wiki (wiki.postgresql.org), and the official MySQL 8.4 LTS Reference Manual (dev.mysql.com/doc/refman/8.4) plus MySQL release notes and docs landing pages. All URLs below were opened with WebFetch on 2026-11-07 unless explicitly flagged "(URL returned by search, not opened)". Pages from the PostgreSQL manual carry no per-page date and are recorded as "n.d., PostgreSQL 18.6 docs"; MySQL 8.4 manual pages likewise carry no per-page date and are recorded as "n.d., MySQL 8.4 Reference Manual".

Label legend used throughout: **MANDATORY** = violating it causes correctness or integrity failures per the source's own reasoning; **RECOMMENDED** = the source advises it for performance, portability, or maintainability; **OPTIONAL/CONTEXTUAL** = the source presents it as a trade-off depending on workload. Workload tags: OLTP, OLAP/warehouse, general (all).

---

## Version baseline: which documents cover which versions (as of 2026-11-07)

### Takeaway
PostgreSQL "current" docs are PostgreSQL 18.6; PostgreSQL 19 was at Release Candidate 1 (2026-10-15) and not yet GA. MySQL's supported LTS lines are 8.4 (latest 8.4.13) and 9.7 (latest 9.7.4); 26.7 and 26.10 are Innovation releases under a new calendar-versioning scheme. The MySQL 8.4 manual pages cited here are also listed in the version selectors for 9.7, 26.7 and 26.10, indicating the content is shared across lines.

### Cited Findings
- PostgreSQL versioning table lists 18 (current minor 18.6, first release 2025-09-25, supported to 2030-11-14) as the top row; PostgreSQL 19 is not in the released table, and the site banner reads "PostgreSQL 19 RC 1 Released!" dated 2026-10-15. Policy: one major release per year, minor releases at least every three months, 5 years of support per major. — [PostgreSQL Versioning Policy](https://www.postgresql.org/support/versioning/) (n.d., fetched 2026-11-07)
- Every PostgreSQL manual page fetched reports "PostgreSQL 18.6 Documentation" in its header (e.g., [Constraints](https://www.postgresql.org/docs/current/ddl-constraints.html)).
- PostgreSQL 18 (released 2025-09-25 per the versioning page) added `uuidv7()` and virtual generated columns; the official announcement is [PostgreSQL 18 Released!](https://www.postgresql.org/about/news/postgresql-18-released-3142/) (URL returned by search, not opened) and the release notes at [Release 18](https://www.postgresql.org/docs/current/release-18.html) (URL returned by search, not opened).
- MySQL documentation home lists reference manuals for MySQL 26.10, 26.7, 9.7, 8.4 and 8.0, and the "current release notes" list server versions 26.10.0, 9.7.4, 8.4.13 and 8.0.46. — [MySQL Documentation](https://dev.mysql.com/doc/) (n.d., fetched 2026-11-07)
- The 8.4 manual tells readers to "decide whether to install from an LTS series like MySQL 8.4, or install from an Innovation series like MySQL 26.7" and explains the 8.4 numbering (major.minor.patch where the minor number "does not change for an LTS series"). — [Which MySQL Version and Distribution to Install](https://dev.mysql.com/doc/refman/8.4/en/which-version.html) (n.d.)
- MySQL 26.7.0 (2026-07-28) and 26.7.1 (2026-08-18) are the listed 26.7 releases; "MySQL 26.7.0 is the first release to use the YY.M.P calendar-version format", and "9.7.x LTS is the only legacy release line that can enter the first calendar-versioned lineage." — [MySQL 26.7 Release Notes](https://dev.mysql.com/doc/relnotes/mysql/26.7/en/) (doc generated 2026-11-05) and [What Is New in MySQL 26.7](https://dev.mysql.com/doc/refman/26.7/en/mysql-nutshell.html) (n.d.)
- Oracle's blog states MySQL 9.7.0 LTS shipped 2026-04-21 and that 26.7.0 is the first Innovation release after 9.7 LTS. — [MySQL 9.7.0 LTS Is Now Available](https://blogs.oracle.com/mysql/mysql-9-7-0-lts-is-now-available-expanded-community-capabilities-and-dynamic-data-masking-for-enterprise) and [MySQL July 2026 GA Releases Now Available](https://blogs.oracle.com/mysql/mysql-july-2026-ga-releases-now-available) (URLs returned by search, not opened); also [MySQL 26.7 Manual 1.3 MySQL Releases: Innovation and LTS](https://dev.mysql.com/doc/refman/26.7/en/mysql-releases.html) (URL returned by search, not opened).
- The MySQL 26.7 "what is new" page lists no schema-relevant data-type, constraint, or partitioning changes versus 9.7; the only InnoDB storage change is batch persistence of AUTO_INCREMENT counters via `innodb_autoinc_preallocate` (default 50), with the warning that "an unexpected server exit can cause unused reserved values to be skipped". — [What Is New in MySQL 26.7](https://dev.mysql.com/doc/refman/26.7/en/mysql-nutshell.html)

### Inferences
- Citing the MySQL 8.4 LTS manual is appropriate for schema-design guidance in late 2026: the pages fetched are shared across 8.4/9.7/26.x selectors and the 26.7 "what is new" page lists no schema-level changes.
- PostgreSQL 19 GA was imminent at research time; nothing in this report depends on 19-only features.

### Gaps
- The postgresql.org news index returned HTTP 404 during research, so exact PostgreSQL 18.6 and 19 GA dates could not be confirmed beyond the versioning page banner.
- The 26.7 manual's "MySQL Releases: Innovation and LTS" page was not opened; the LTS/Innovation classification of 26.x rests on the 8.4 "which version" page plus search summaries of Oracle blogs.

---

## PostgreSQL Q1: Constraints (PRIMARY KEY, FOREIGN KEY actions, CHECK, UNIQUE, NOT NULL, EXCLUDE, DEFERRABLE)

### Takeaway
PostgreSQL's DDL chapter treats constraints as the primary integrity mechanism: it says relational theory dictates a primary key on every table (not enforced, "usually best practice"), tells designers that most columns should be NOT NULL, warns that CHECK constraints cannot safely reference other rows or tables, and explains that referencing (FK) columns are not indexed automatically. ON DELETE/UPDATE semantics (NO ACTION deferrable vs RESTRICT not deferrable, SET DEFAULT supported) are spelled out in detail.

### Cited Findings
- CHECK: "A CHECK constraint is satisfied if the expression is true or NULL"; therefore CHECK does not prevent NULLs; use NOT NULL for that. Example `price numeric CHECK (price > 0)` and table-level `CONSTRAINT valid_discount CHECK (price > discounted_price)`. **MANDATORY understanding** (NULL passes). — [PostgreSQL 5.5 Constraints](https://www.postgresql.org/docs/current/ddl-constraints.html) (n.d., PG 18.6 docs)
- CHECK must not reference other rows/tables: it "may appear to work in simple tests" but cannot guarantee the invariant and can break dump/restore; use UNIQUE, EXCLUDE, or FOREIGN KEY instead; CHECK expressions must be immutable because they are evaluated only on INSERT/UPDATE. **MANDATORY**. — [Constraints](https://www.postgresql.org/docs/current/ddl-constraints.html)
- NOT NULL: equivalent to `CHECK (col IS NOT NULL)` but "more efficient"; "Tip: In most designs, the majority of columns should be NOT NULL." **RECOMMENDED** (official tip). — [Constraints](https://www.postgresql.org/docs/current/ddl-constraints.html)
- UNIQUE creates a unique B-tree index automatically; by default two NULLs are not equal so duplicate NULL rows are allowed; `UNIQUE NULLS NOT DISTINCT` treats NULLs as equal; the SQL standard leaves default NULL treatment implementation-defined, "so be careful with portability". A uniqueness rule over a subset of rows requires a unique partial index, not a UNIQUE constraint. — [Constraints](https://www.postgresql.org/docs/current/ddl-constraints.html)
- PRIMARY KEY = UNIQUE + NOT NULL plus a unique B-tree index; at most one per table; "Relational theory says every table should have a primary key. PostgreSQL does not enforce this, but it is usually best practice"; it is the default FK target. **RECOMMENDED (strongly)**. — [Constraints](https://www.postgresql.org/docs/current/ddl-constraints.html)
- FOREIGN KEY referential actions: `NO ACTION` (default; check can be deferred to end of transaction), `RESTRICT` (immediate, "cannot be deferred"; for ON UPDATE it blocks even a no-op change such as 'abc' to 'ABC' under case-insensitive collations), `CASCADE`, `SET NULL`, `SET DEFAULT` (fails if default violates FK). Column lists are allowed for SET NULL/SET DEFAULT on ON DELETE only (example: `FOREIGN KEY (tenant_id, author_id) REFERENCES users ON DELETE SET NULL (author_id)`). — [Constraints](https://www.postgresql.org/docs/current/ddl-constraints.html)
- Guidance on choosing an action: CASCADE when child rows "cannot exist without the referenced row" (order items); RESTRICT/NO ACTION when both tables are independent objects (products and orders); SET NULL/SET DEFAULT for optional relationships. **RECOMMENDED**. — [Constraints](https://www.postgresql.org/docs/current/ddl-constraints.html)
- MATCH FULL vs default MATCH SIMPLE: by default a row escapes the FK check if any referencing column is NULL; declare referencing columns NOT NULL to prevent that. — [Constraints](https://www.postgresql.org/docs/current/ddl-constraints.html)
- Referenced columns must be a PK, UNIQUE constraint, or non-partial unique index; "Referencing columns are not indexed automatically... it is often a good idea to create an index on the referencing columns yourself" because DELETE/UPDATE on the parent must scan the child. **RECOMMENDED** (performance). — [Constraints](https://www.postgresql.org/docs/current/ddl-constraints.html)
- EXCLUDE: `EXCLUDE USING gist (c WITH &&)` guarantees that for any two rows at least one operator comparison returns false or NULL; automatically creates an index of the named type. — [Constraints](https://www.postgresql.org/docs/current/ddl-constraints.html)
- DEFERRABLE: "IMMEDIATE constraints are checked at the end of each statement. DEFERRED constraints are not checked until transaction commit"; "only UNIQUE, PRIMARY KEY, REFERENCES (foreign key), and EXCLUDE constraints are affected"; NOT NULL and CHECK are always checked immediately; non-deferrable uniqueness is checked per row "not at end of statement as the standard would suggest." — [SET CONSTRAINTS](https://www.postgresql.org/docs/current/sql-set-constraints.html) (n.d., PG 18.6 docs)

### Inferences
- PostgreSQL's constraint model is strictly richer than MySQL's on three axes: deferrable FK/unique checks, SET DEFAULT, and EXCLUDE constraints (see comparison section).
- The "index your FK columns" advice is engine-specific to PostgreSQL in practice because MySQL auto-creates that index (see MySQL Q3).

### Gaps
- The docs give no quantitative guidance on when deferral is worth its cost; they present it as a correctness tool for circular references, not a performance tool.

---

## PostgreSQL Q2: Data types (numeric vs float for money, timestamptz, uuid, jsonb, text vs varchar(n), boolean, enum, money)

### Takeaway
The manual is explicit: use `numeric` for money (floats are inexact), prefer `timestamp with time zone` for instants (stored as UTC) and avoid `time with time zone`, prefer `jsonb` over `json`, and treat `text`/`varchar` as performance-equivalent with `char(n)` being the slowest. `uuid` is positioned for distributed uniqueness with native v4 and time-ordered v7 generation in PG 18. The `money` type is locale-dependent and the wiki says not to use it.

### Cited Findings
- Integer guidance: "The type integer is the common choice, as it offers the best balance between range, storage size, and performance"; smallint "generally only used if disk space is at a premium"; bigint when integer's range is insufficient. **RECOMMENDED**. — [8.1 Numeric Types](https://www.postgresql.org/docs/current/datatype-numeric.html) (n.d., PG 18.6)
- `numeric`/`decimal` "is especially recommended for storing monetary amounts and other quantities where exactness is required", but "calculations on numeric values are very slow compared to the integer types, or to the floating-point types". Floats are "inexact"; "If you require exact storage and calculations (such as for monetary amounts), use the numeric type instead"; "Comparing two floating-point values for equality might not always work as expected." Rounding differs: numeric rounds ties away from zero, float rounds ties to even. **MANDATORY for money** (correctness). — [8.1 Numeric Types](https://www.postgresql.org/docs/current/datatype-numeric.html)
- Serial types "are not true types, but merely a notational convenience"; a `SERIAL` column is integer NOT NULL DEFAULT nextval(...); UNIQUE/PK "is not automatic"; use `bigserial` if more than 2^31 identifiers are anticipated; gaps can occur even without deletes. — [8.1 Numeric Types](https://www.postgresql.org/docs/current/datatype-numeric.html)
- `money`: 8 bytes, fixed fractional precision from `lc_monetary`; output is locale-sensitive so data "may not load correctly into a database with a different lc_monetary setting"; converting float to money via numeric "is not recommended because floating-point rounding errors make floats unsuitable for money." — [8.2 Monetary Types](https://www.postgresql.org/docs/current/datatype-money.html) (n.d., PG 18.6)
- Date/time: both timestamp types are 8 bytes; `timestamp with time zone` input is converted to UTC and "the value is stored internally as UTC, and the originally stated or assumed time zone is not retained"; `timestamp without time zone` "will silently ignore any time zone indication". Recommendation: "we recommend using date/time types that contain both date and time when using time zones. We do not recommend using the type time with time zone" because a time-of-day offset "cannot adapt to daylight-saving time". `timestamptz` abbreviation is a PostgreSQL extension; bare `timestamp` means without time zone per SQL standard. **RECOMMENDED** (official); the wiki escalates this (see Q9). — [8.5 Date/Time Types](https://www.postgresql.org/docs/current/datatype-datetime.html) (n.d., PG 18.6)
- Character types: "There is no performance difference among these three types, apart from increased storage space when using the blank-padded type, and a few extra CPU cycles to check the length when storing into a length-constrained column... character(n) is usually the slowest of the three because of its additional storage costs. In most situations text or character varying should be used instead." Over-length values error unless excess is spaces; `n` counts characters, max 10,485,760; strings up to about 1 GB; long values are compressed and TOASTed automatically. **RECOMMENDED**. — [8.3 Character Types](https://www.postgresql.org/docs/current/datatype-character.html) (n.d., PG 18.6)
- JSON: "In general, most applications should prefer to store JSON data as jsonb, unless there are quite specialized needs, such as legacy assumptions about ordering of object keys." jsonb drops whitespace/key order and keeps only the last duplicate key; GIN operator classes `jsonb_ops` (default; supports `?`, `?|`, `?&`, `@>`, `@?`, `@@`) and `jsonb_path_ops` (smaller, only `@>`, `@?`, `@@`); example `CREATE INDEX idxgin ON api USING GIN (jdoc);` and `CREATE INDEX idxgintags ON api USING GIN ((jdoc -> 'tags'));`. Design guidance: "it is still recommended that JSON documents have a somewhat fixed structure"; "any update acquires a row-level lock on the whole row. Consider limiting JSON documents to a manageable size"; documents should represent "an atomic datum that business rules dictate cannot reasonably be further subdivided". **RECOMMENDED**. — [8.14 JSON Types](https://www.postgresql.org/docs/current/datatype-json.html) (n.d., PG 18.6)
- UUID: 128-bit quantity per RFC 9562; for distributed systems UUIDs "provide a better uniqueness guarantee than sequence generators, which are only unique within a single database"; PostgreSQL natively generates UUIDv4 and UUIDv7. — [8.12 UUID Type](https://www.postgresql.org/docs/current/datatype-uuid.html) (n.d., PG 18.6)
- UUID functions: `gen_random_uuid()`/`uuidv4()` generate version 4; `uuidv7([shift interval])` "Generates a version 7 (time-ordered) UUID" computed from a millisecond UNIX timestamp + sub-millisecond + random; `uuid_extract_timestamp()` works for v1/v7; `uuid_extract_version()`. — [9.14 UUID Functions](https://www.postgresql.org/docs/current/functions-uuid.html) (n.d., PG 18.6)
- Boolean: 1 byte; three states true/false/unknown (SQL NULL); accepts true/yes/on/1 and false/no/off/0. — [8.6 Boolean Type](https://www.postgresql.org/docs/current/datatype-boolean.html) (n.d., PG 18.6)
- Enum: `CREATE TYPE mood AS ENUM ('sad','ok','happy')`; sort order is declaration order; distinct enum types cannot be compared without casting; 4 bytes on disk; labels limited to NAMEDATALEN (63 bytes); values can be added/renamed with ALTER TYPE but "cannot be removed" and order cannot change without recreating the type. **OPTIONAL/CONTEXTUAL** (note the removal limitation). — [8.7 Enumerated Types](https://www.postgresql.org/docs/current/datatype-enum.html) (n.d., PG 18.6)

### Inferences
- "Exact numeric for money" and "store instants as UTC-normalized timestamps" are universal principles; the specific type names (numeric vs DECIMAL; timestamptz vs TIMESTAMP/DATETIME) are engine-specific.
- PostgreSQL's position that `varchar(n)` adds nothing but a length check (and the wiki's "don't use varchar(n) by default") directly contrasts with MySQL's "use the smallest data types possible" (see comparison section): this is a genuine documented divergence in philosophy.

### Gaps
- The numeric-types page does not itself say identity columns are preferred over serial; that recommendation comes only from the wiki (Q9).

---

## PostgreSQL Q3: Identity columns vs serial; generated columns

### Takeaway
The official manual documents identity columns (`GENERATED { ALWAYS | BY DEFAULT } AS IDENTITY`) neutrally and notes they do not guarantee uniqueness without PK/UNIQUE; the wiki, not the manual, says "don't use serial", use identity columns. PG 18 made virtual generated columns the default.

### Cited Findings
- Identity: `id bigint GENERATED ALWAYS AS IDENTITY`; with ALWAYS a user value is accepted only with `OVERRIDING SYSTEM VALUE`; with BY DEFAULT the user value wins; ALWAYS "provides some more protection against accidentally inserting an explicit value"; identity columns are automatically NOT NULL; uniqueness is "not guaranteed", so add PRIMARY KEY or UNIQUE; partitions inherit identity columns and cannot define their own; inheritance children do not inherit them. The page contains no comparison with serial and no preference statement. — [5.3 Identity Columns](https://www.postgresql.org/docs/current/ddl-identity-columns.html) (n.d., PG 18.6)
- Wiki: "Don't use serial... Why not: its behaviors complicate schema, dependency, and permission management. Alternative: identity columns. When should you: PostgreSQL < 10, some inheritance setups, or when sharing one sequence across tables." **RECOMMENDED** (wiki). — [Don't Do This](https://wiki.postgresql.org/wiki/Don%27t_Do_This) (last edited 2024-11-21)
- Generated columns: "A generated column is a special column that is always computed from other columns... for columns what a view is for tables"; two kinds, stored and virtual; virtual is the default in PG 18 (use `STORED` explicitly); example `height_in numeric GENERATED ALWAYS AS (height_cm / 2.54) STORED`; expression must use only immutable functions, no subqueries, cannot reference another generated column, cannot have a default or identity, cannot be part of a partition key; virtual columns cannot use user-defined types/functions and are not yet logically replicated; stored ones can be replicated via `publish_generated_columns`. — [5.4 Generated Columns](https://www.postgresql.org/docs/current/ddl-generated-columns.html) (n.d., PG 18.6)

### Inferences
- Conflict of emphasis (not fact): official manual is neutral on serial vs identity; the wiki is prescriptive. Report writers should attribute "prefer identity" to the wiki.

### Gaps
- Whether PG 18 virtual generated columns can be indexed was not stated on the fetched page.

---

## PostgreSQL Q4: Index types (B-tree, hash, GIN, GiST, SP-GiST, BRIN, partial, expression, covering INCLUDE)

### Takeaway
B-tree is the default and "fits the most common situations"; hash handles only equality; GIN is for multi-component values (arrays, jsonb); GiST/SP-GiST are extensible frameworks (geometry, nearest-neighbor); BRIN is for columns correlated with physical row order. Partial indexes are for excluding common/uninteresting values or enforcing subset uniqueness, and must not be used as a substitute for partitioning. `INCLUDE` builds covering indexes but should be used conservatively.

### Cited Findings
- "By default, the CREATE INDEX command creates B-tree indexes, which fit the most common situations"; B-tree handles `<, <=, =, >=, >`, BETWEEN, IN, IS [NOT] NULL, sorted retrieval, and anchored `LIKE 'foo%'` (non-C locales need a special operator class). — [11.2 Index Types](https://www.postgresql.org/docs/current/indexes-types.html) (n.d., PG 18.6)
- Hash: "store a 32-bit hash code... can only handle simple equality comparisons." GiST: "an infrastructure within which many different indexing strategies can be implemented", supports nearest-neighbor (`ORDER BY location <-> point '(101,456)' LIMIT 10`). SP-GiST: non-balanced structures (quadtrees, k-d trees, radix trees). GIN: "inverted indexes which are appropriate for data values that contain multiple component values, such as arrays." BRIN: "store summaries about the values stored in consecutive physical block ranges... most effective for columns whose values are well-correlated with the physical order of the table rows." **RECOMMENDED** (choice by operator class). — [11.2 Index Types](https://www.postgresql.org/docs/current/indexes-types.html)
- Partial indexes: Example 11.1 excludes common values (`WHERE NOT (client_ip > inet '192.168.100.0' AND client_ip < inet '192.168.100.255')`); Example 11.2 `CREATE INDEX orders_unbilled_index ON orders (order_nr) WHERE billed is not true;`; Example 11.3 `CREATE UNIQUE INDEX tests_success_constraint ON tests (subject, target) WHERE success;`. The planner uses a partial index only when the query WHERE clause provably implies the predicate; parameterized predicates do not match. Example 11.4: many per-category partial indexes is "a bad idea"; prefer `CREATE INDEX mytable_cat_data ON mytable (category, data);` or real partitioning. **RECOMMENDED / CONTEXTUAL**. — [11.8 Partial Indexes](https://www.postgresql.org/docs/current/indexes-partial.html) (n.d., PG 18.6)
- Index-only scans require an index type that supports them (B-tree always; GiST/SP-GiST for some opclasses; GIN never) and a visibility map with all-visible pages; `CREATE INDEX tab_x_y ON tab(x) INCLUDE (y);` stores y as payload; `CREATE UNIQUE INDEX tab_x_y ON tab(x) INCLUDE (y);` enforces uniqueness on x only; INCLUDE also works in UNIQUE/PRIMARY KEY constraints; only B-tree, GiST, SP-GiST support INCLUDE; expressions cannot be included. Advice: be conservative with payload columns (bloat, max tuple size); little benefit on frequently updated tables. **RECOMMENDED / CONTEXTUAL**. — [11.9 Index-Only Scans and Covering Indexes](https://www.postgresql.org/docs/current/indexes-index-only-scans.html) (n.d., PG 18.6)
- Expression indexes on jsonb: `CREATE INDEX idxgintags ON api USING GIN ((jdoc -> 'tags'));` — [8.14 JSON Types](https://www.postgresql.org/docs/current/datatype-json.html)

### Inferences
- PostgreSQL stores table rows in a heap separate from all indexes (the index-only-scan page speaks of "visiting the heap" and the visibility map), which is the structural opposite of InnoDB's clustered index: in PostgreSQL every index is a "secondary" index pointing to heap tuples, so PK length does not inflate other indexes.
- BRIN is applicable mostly to append-only/time-series or warehouse-style tables where physical order correlates with the column (OLAP/general), though the docs frame it by correlation rather than by table size.

### Gaps
- The index-types page does not mention jsonb under GIN; jsonb GIN support is documented on the JSON types page.

---

## PostgreSQL Q5: Declarative partitioning and limitations

### Takeaway
Partitioning is worthwhile "only when a table would otherwise be very large" (rule of thumb: larger than server RAM). Range/list/hash are supported; unique/PK constraints must include all partition-key columns; a few thousand partitions are manageable if pruning works; warehouse workloads tolerate more partitions than OLTP.

### Cited Findings
- Benefits: query performance when "most of the heavily accessed rows... are in a single partition or a small number of partitions"; bulk deletes via `DROP TABLE`/`ALTER TABLE DETACH PARTITION` "far faster than a bulk operation"; tiering to cheaper storage. "A rule of thumb is that the size of the table should exceed the physical memory of the database server." **OPTIONAL/CONTEXTUAL**. — [5.12 Table Partitioning](https://www.postgresql.org/docs/current/ddl-partitioning.html) (n.d., PG 18.6)
- DDL: `CREATE TABLE measurement (...) PARTITION BY RANGE (logdate);` then `CREATE TABLE measurement_y2006m02 PARTITION OF measurement FOR VALUES FROM ('2006-02-01') TO ('2006-03-01');`; range bounds are inclusive lower/exclusive upper; `CREATE INDEX ON measurement (logdate);` cascades to partitions; `ALTER TABLE measurement DETACH PARTITION measurement_y2006m02 CONCURRENTLY;`. Rows that map to no partition error. — [5.12 Table Partitioning](https://www.postgresql.org/docs/current/ddl-partitioning.html)
- Limitations: for unique/PK constraints "the partition keys must not include any expressions or function calls and the constraint's columns must include all of the partition key columns"; exclusion constraints must include all partition-key columns compared for equality; "BEFORE ROW triggers on INSERT cannot change which partition is the final destination"; no mixing temporary and permanent relations; partitions cannot have extra columns; `TRUNCATE ONLY` errors. **MANDATORY** (hard limits). — [5.12 Table Partitioning](https://www.postgresql.org/docs/current/ddl-partitioning.html)
- Best practices: partition by "the column or set of columns which most commonly appear in WHERE clauses"; design so "all data to be removed at once is located in a single partition"; planner handles "up to a few thousand partitions fairly well, provided that typical queries allow the query planner to prune all but a small number of partitions"; "With data warehouse type workloads, it can make sense to use a larger number of partitions than with an OLTP type workload"; "Never just assume that more partitions are better than fewer partitions, nor vice-versa." Pruning is "driven only by the constraints defined implicitly by the partition keys, not by the presence of indexes." **RECOMMENDED**. — [5.12 Table Partitioning](https://www.postgresql.org/docs/current/ddl-partitioning.html)

### Inferences
- The "unique keys must include the partition key" rule is shared by MySQL (see MySQL Q5), making it a universal constraint of horizontal partitioning in both engines.

### Gaps
- The fetched extract did not include the manual's statements about foreign keys referencing partitioned tables; support cannot be confirmed from fetched content.

---

## PostgreSQL Q6: Schemas/namespaces, row-level security, roles and privileges

### Takeaway
Schemas are the recommended unit for multi-user/multi-app separation; since PG 15 the public schema no longer grants CREATE to everyone, and the manual says the "grant CREATE on public, keep default search_path" pattern "is never a secure pattern." RLS is default-deny once enabled, bypassed by superusers/BYPASSRLS/owners unless FORCE, and the manual warns of covert channels through FK checks. Privileges are fine-grained down to columns and have conservative PUBLIC defaults.

### Cited Findings
- Schemas serve "to allow many users to use one database without interfering with each other", "to organize database objects into logical groups", and to isolate third-party apps; they "cannot be nested"; "Schema names beginning with pg_ are reserved"; "For maximum conformance to the standard, you should not use the public schema." — [5.10 Schemas](https://www.postgresql.org/docs/current/ddl-schemas.html) (n.d., PG 18.6)
- search_path security: "adding a schema to search_path effectively trusts all users having CREATE privilege on that schema." Secure patterns: (1) user-private schemas with no public CREATE ("In PostgreSQL 15 and later, the default configuration supports this usage pattern"; older/upgraded DBs: `REVOKE CREATE ON SCHEMA public FROM PUBLIC`); (2) remove public from search_path (`ALTER ROLE ALL SET search_path = "$user"`); (3) keep default and grant CREATE on public: "this is never a secure pattern. It is acceptable only when the database has a single user or a few mutually-trusting users." **MANDATORY for multi-user security**. — [5.10 Schemas](https://www.postgresql.org/docs/current/ddl-schemas.html)
- RLS: `ALTER TABLE accounts ENABLE ROW LEVEL SECURITY;` with no policy means "no rows are visible or can be modified" (default deny); `CREATE POLICY account_managers ON accounts TO managers USING (manager = current_user);`; USING filters reads/existing rows, WITH CHECK validates new rows; permissive policies OR together, `AS RESTRICTIVE` policies AND; superusers and BYPASSRLS roles always bypass; owners bypass unless `FORCE ROW LEVEL SECURITY`; TRUNCATE and REFERENCES are not subject to RLS. Warnings: unique/PK/FK checks "always ignore row security", so beware "covert channel leaks"; policies with sub-selects can race under READ COMMITTED; `row_security = off` errors rather than silently filtering (protects pg_dump). **MANDATORY awareness when using RLS**. — [5.9 Row Security Policies](https://www.postgresql.org/docs/current/ddl-rowsecurity.html) (n.d., PG 18.6)
- Privileges: SELECT, INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER, CREATE, CONNECT, TEMPORARY, EXECUTE, USAGE, SET, ALTER SYSTEM, MAINTAIN; by default PUBLIC gets no privileges on tables/columns/sequences/schemas but does get CONNECT and TEMPORARY on databases, EXECUTE on functions, USAGE on languages/types; column-level grants `GRANT SELECT (col1), UPDATE (col1) ON mytable TO miriam_rw;`; `ALTER DEFAULT PRIVILEGES` for future objects; recommendation to revoke defaults "in the same transaction that creates the object" for maximum security. — [5.8 Privileges](https://www.postgresql.org/docs/current/ddl-priv.html) (n.d., PG 18.6)
- Wiki (older): one database with named schemas rather than many databases; remove the public schema; create a NOLOGIN owner role named after the schema plus read/write and read-only roles and grant to roles not users; separate servers for dev vs prod. — [Database Schema Recommendations for an Application](https://wiki.postgresql.org/wiki/Database_Schema_Recommendations_for_an_Application) (last modified 2016-09-15; flagged as dated)

### Inferences
- PostgreSQL's security toolbox for schema design (schemas, column grants, RLS, default-deny) is more granular than MySQL's documented role model (MySQL Q8), where the fetched roles page shows database-level grants and mentions neither column-level nor row-level security.

### Gaps
- MySQL column-level privilege documentation was not fetched; absence on the roles page is not proof MySQL lacks column grants.

---

## PostgreSQL Q7: MVCC and transaction isolation defaults

### Takeaway
PostgreSQL's default is READ COMMITTED; Read Uncommitted behaves as Read Committed; Repeatable Read prevents phantoms (stricter than the standard requires) and Serializable uses SSI. Applications using Repeatable Read or Serializable must retry on SQLSTATE 40001; declare READ ONLY where possible.

### Cited Findings
- "Read Committed is the default isolation level in PostgreSQL." "PostgreSQL's Read Uncommitted mode behaves like Read Committed." Table 13.1: phantom reads are "Allowed, but not in PG" at Repeatable Read. — [13.2 Transaction Isolation](https://www.postgresql.org/docs/current/transaction-iso.html) (n.d., PG 18.6)
- Repeatable Read sees "a snapshot as of the start of the first non-transaction-control statement in the transaction"; on conflict "ERROR: could not serialize access due to concurrent update"; "it should abort the current transaction and retry the whole transaction from the beginning"; "only updating transactions might need to be retried." Serializable "emulates serial transaction execution"; failures "always return with an SQLSTATE value of '40001'". **MANDATORY** (retry logic) when using these levels. — [13.2 Transaction Isolation](https://www.postgresql.org/docs/current/transaction-iso.html)
- Serializable performance advice: "Declare transactions as READ ONLY when possible"; use connection pooling; "Don't put more into a single transaction than needed for integrity purposes"; avoid idle-in-transaction; drop explicit locks/SELECT FOR UPDATE where SSI already protects; avoid sequential scans ("A sequential scan will always necessitate a relation-level predicate lock"); tune `max_pred_locks_per_*`. **RECOMMENDED**. — [13.2 Transaction Isolation](https://www.postgresql.org/docs/current/transaction-iso.html)

### Inferences
- Default isolation is a documented engine difference (PG READ COMMITTED vs InnoDB REPEATABLE READ); portable schema/transaction designs should set isolation explicitly rather than rely on defaults.

### Gaps
- None material.

---

## PostgreSQL Q8: Backup, PITR/WAL archiving, logical replication

### Takeaway
PostgreSQL documents three backup approaches (SQL dump, file-system backup, continuous archiving). PITR requires `wal_level = replica` or higher, `archive_mode = on`, an archive command that never overwrites, and a base backup (pg_basebackup recommended). Logical replication (publish/subscribe) does not replicate DDL, sequences, or large objects, and schema design must provide replica identity (PK) for UPDATE/DELETE.

### Cited Findings
- Chapter 25 lists exactly three approaches: SQL dump, file system level backup, continuous archiving, "each has its own strengths and weaknesses". — [25. Backup and Restore](https://www.postgresql.org/docs/current/backup.html) (n.d., PG 18.6)
- PITR setup: `wal_level = replica`, `archive_mode = on`, `archive_command = 'test ! -f /mnt/server/archivedir/%f && cp %p /mnt/server/archivedir/%f'`; the command "must return zero only on success"; "Archive commands must not overwrite existing files"; pg_dump/pg_dumpall "cannot be used for this approach"; if `pg_wal/` fills up the server PANICs. Base backup: `pg_basebackup -D /backup/base -X stream -c fast` (recommended) or low-level `pg_backup_start`/`pg_backup_stop`; incremental backups via `pg_basebackup --incremental` + `pg_combinebackup`. Recovery via `restore_command`, `recovery.signal`, recovery targets (time or named restore point), and timelines. Caveats: CREATE TABLESPACE replay can overwrite paths; take a new base backup after tablespace changes; set `archive_timeout` on low-traffic systems; back up config files separately; monitor the archiver. **MANDATORY** (archive must not overwrite; test before first base backup). — [25.3 Continuous Archiving and PITR](https://www.postgresql.org/docs/current/continuous-archiving.html) (n.d., PG 18.6)
- Logical replication: publish/subscribe based on "replication identity (usually a primary key)"; use cases include incremental change feeds, consolidating databases for analytics, cross-version and cross-platform replication, sharing subsets. — [29. Logical Replication](https://www.postgresql.org/docs/current/logical-replication.html) (n.d., PG 18.6)
- Restrictions: "Schema and DDL are not replicated"; "Sequence data is not replicated" (subscriber sequences stay at start; must be advanced on failover); TRUNCATE fails if subscriber tables have FKs outside the subscription; "Large objects are not replicated"; only tables (including partitioned) are supported; `publish_via_partition_root` controls partition identity; UPDATE/DELETE cannot be applied for REPLICA IDENTITY FULL tables with types lacking B-tree/hash opclasses "overcome by defining a primary key or replica identity". **MANDATORY awareness** for replicated schemas. — [29.8 Restrictions](https://www.postgresql.org/docs/current/logical-replication-restrictions.html) (n.d., PG 18.6)

### Inferences
- Schema-design consequence: every logically replicated table should have a primary key (replica identity), and identity/serial sequences need a failover procedure.

### Gaps
- The `wal_level = logical` requirement and the exact error for missing replica identity are on sub-pages not fetched.

---

## PostgreSQL Q9: Identifier rules (63 bytes, case folding, quoting) and the wiki "Don't Do This" list

### Takeaway
Unquoted identifiers fold to lower case (contrary to the SQL standard's upper case), are limited to 63 bytes (NAMEDATALEN-1), and the manual's portability advice is to "always quote a particular name or never quote it." The wiki's "Don't Do This" page (last edited 2024-11-21) enumerates 22 anti-patterns across encoding, tools, SQL constructs, date/time, text, other types, and authentication.

### Cited Findings
- Identifiers start with a letter or underscore; later characters may be letters, underscores, digits, or `$` ("dollar signs are not allowed in identifiers according to the letter of the SQL standard"); "The SQL standard will not define a key word that contains digits or starts or ends with an underscore, so identifiers of this form are safe against possible conflict with future extensions of the standard." "By default, NAMEDATALEN is 64 so the maximum identifier length is 63 bytes"; longer names "will be truncated". "Key words and unquoted identifiers are case-insensitive"; "The folding of unquoted names to lower case in PostgreSQL is incompatible with the SQL standard, which says that unquoted names should be folded to upper case"; "Quoting an identifier also makes it case-sensitive"; "If you want to write portable applications you are advised to always quote a particular name or never quote it." **MANDATORY** (consistency of quoting). — [4.1.1 Identifiers and Key Words](https://www.postgresql.org/docs/current/sql-syntax-lexical.html) (n.d., PG 18.6)
- Wiki "Don't Do This" items (each with why/when): Don't use SQL_ASCII encoding; don't use psql -W; don't use rules (use triggers); don't use table inheritance (use declarative partitioning); don't use NOT IN (NULL semantics, no anti-join; use NOT EXISTS); don't use upper-case table/column names (use lowercase with underscores; alias for report headers); don't use BETWEEN especially with timestamps (use `>= start AND < next_start`); don't use timestamp without time zone (use timestamptz); don't use timestamp to store UTC; don't use timetz; don't use CURRENT_TIME; don't use timestamp(0)/timestamptz(0) (rounds, use date_trunc); don't use +/-HH:mm as text time-zone names (POSIX sign inversion); don't use char(n) (padding, no speed benefit); don't use char(n) even for fixed-length identifiers (use text + CHECK or a domain); don't use varchar(n) by default (arbitrary limits cause production errors; same performance as text); don't use money (no fractional cents, no currency, lc_monetary dependent; use numeric with a currency column); don't use serial (use identity columns); don't use trust authentication over TCP/IP (use scram-sha-256). **RECOMMENDED (wiki; community-maintained but hosted by the project)**. — [Don't Do This](https://wiki.postgresql.org/wiki/Don%27t_Do_This) (last edited 2024-11-21)

### Inferences
- The wiki's "lowercase with underscores" is the closest thing PostgreSQL has to an official naming convention, and it derives directly from the manual's lower-case folding rule.
- The wiki is stricter than the manual in several places (timestamp without time zone: manual "recommends" types with both date and time when using time zones; wiki says "don't"; varchar(n): manual says no performance difference; wiki says don't use by default). These are differences of strength, not contradictions.

### Gaps
- No official PostgreSQL document prescribes table/column naming beyond case, length, `pg_` prefix, and quoting consistency.

---

## MySQL Q1: InnoDB clustered index design and primary key choice (random vs sequential)

### Takeaway
InnoDB stores row data in the clustered index (PK, else first UNIQUE NOT NULL index, else hidden 6-byte row ID). Every secondary index stores the PK columns, so the manual repeatedly says PKs should be short and that every table should have one (auto-increment if nothing natural). On random vs sequential keys, the official 8.4 manual says only that inserting in PRIMARY KEY order is faster, "particularly important for tables that do not fit entirely within the buffer pool"; it does not discuss UUIDs or page splits explicitly.

### Cited Findings
- Clustered index selection order: PRIMARY KEY; else "the first UNIQUE index where all the key columns are defined as NOT NULL"; else hidden `GEN_CLUST_INDEX` on a 6-byte monotonically increasing row ID. "Accessing a row through the clustered index is fast because the index search leads directly to the page that contains the row data." "If the primary key is long, the secondary indexes use more space, so it is advantageous to have a short primary key." "A primary key should be defined for each table." "If there is no logical unique and non-null column or set of columns to use as the primary key, add an auto-increment column." **RECOMMENDED (strongly)**; the hidden-index fallback is a correctness/perf hazard. — [17.6.2.1 Clustered and Secondary Indexes](https://dev.mysql.com/doc/refman/8.4/en/innodb-index-types.html) (n.d., MySQL 8.4 Reference Manual)
- "Specify a primary key for every table using the most frequently queried column or columns, or an auto-increment value if there is no obvious primary key." "define foreign keys on the join columns, and declare those columns with the same data type in each table"; "Turn off autocommit"; group DML into transactions; "Do not use LOCK TABLES"; enable `innodb_file_per_table` (default); evaluate compression; run with `--sql_mode=NO_ENGINE_SUBSTITUTION`. **RECOMMENDED**. — [17.1.2 Best Practices for InnoDB Tables](https://dev.mysql.com/doc/refman/8.4/en/innodb-best-practices.html) (n.d.)
- "specify a set of primary key columns for each table, columns that are used in the most important and time-critical queries"; "Do not specify too many or too long columns in the primary key, because these column values are duplicated in each secondary index"; "If an indexed column cannot contain any NULL values, declare it as NOT NULL." — [10.5.6 Optimizing InnoDB Queries](https://dev.mysql.com/doc/refman/8.4/en/optimizing-innodb-queries.html) (n.d.)
- "When performing bulk inserts, it is faster to insert rows in PRIMARY KEY order. InnoDB tables use a clustered index, which makes it relatively fast to use data in the order of the PRIMARY KEY. Performing bulk inserts in PRIMARY KEY order is particularly important for tables that do not fit entirely within the buffer pool." Also: turn off autocommit, `unique_checks=0`/`foreign_key_checks=0` for trusted loads, `innodb_autoinc_lock_mode=2`, multi-row INSERT. The page does not mention UUIDs, random keys, or page splits. — [10.5.5 Bulk Data Loading for InnoDB Tables](https://dev.mysql.com/doc/refman/8.4/en/optimizing-innodb-bulk-data-loading.html) (n.d.)
- "The primary index of a table should be as short as possible... For InnoDB tables, the primary key columns are duplicated in each secondary index entry, so a short primary key saves considerable space if you have many secondary indexes." — [10.4.1 Optimizing Data Size](https://dev.mysql.com/doc/refman/8.4/en/data-size.html) (n.d.)
- Changing the clustered index is expensive: "Adding a primary key" is in-place but rebuilds the table; "Dropping a primary key" requires ALGORITHM=COPY; "restructuring the clustered index always requires copying table data, so it's best to define the primary key in CREATE TABLE." **RECOMMENDED**. — [17.12.1 Online DDL Operations](https://dev.mysql.com/doc/refman/8.4/en/innodb-online-ddl-operations.html) (n.d.)
- MySQL 26.7 changes AUTO_INCREMENT persistence to batches (`innodb_autoinc_preallocate`, default 50); "an unexpected server exit can cause unused reserved values to be skipped." — [What Is New in MySQL 26.7](https://dev.mysql.com/doc/refman/26.7/en/mysql-nutshell.html) (n.d.)

### Inferences
- The widely repeated claim that random (UUIDv4) primary keys hurt InnoDB is consistent with, but not literally stated by, the official 8.4 manual; the official basis is the clustered-index description plus "insert in PRIMARY KEY order is faster" and "short primary key". Report writers should attribute the explicit "random keys cause page splits" argument to non-official sources.
- PostgreSQL's uuidv7 (time-ordered) and InnoDB's PK-order preference point the same direction: if UUID keys are needed, time-ordered UUIDs align with both engines' documented storage behavior.

### Gaps
- No official MySQL page fetched quantifies the cost of random PKs or recommends UUIDv7/`UUID_TO_BIN(..., 1)` swapping specifically.

---

## MySQL Q2: Data types (DECIMAL for money, DATETIME vs TIMESTAMP, utf8mb4/collation, NOT NULL, smallest types)

### Takeaway
MySQL docs say DECIMAL/NUMERIC are for exact values "for example with monetary data"; TIMESTAMP converts to/from UTC and stops at 2038-01-19, DATETIME does not convert and reaches 9999; utf8mb4 is the server default (collation utf8mb4_0900_ai_ci) and "All new applications should use utf8mb4" since utf8mb3 is deprecated; the optimization chapter says to use the smallest data types and declare NOT NULL where possible.

### Cited Findings
- DECIMAL/NUMERIC "store exact numeric values"; NUMERIC is implemented as DECIMAL; "used when it is important to preserve exact precision, for example with monetary data"; `salary DECIMAL(5,2)` range -999.99..999.99; default is DECIMAL(10,0); maximum 65 digits. **MANDATORY for money**. — [13.1.3 Fixed-Point Types (Exact Value)](https://dev.mysql.com/doc/refman/8.4/en/fixed-point-types.html) (n.d.)
- DATE '1000-01-01'..'9999-12-31'; DATETIME '1000-01-01 00:00:00'..'9999-12-31 23:59:59'; TIMESTAMP '1970-01-01 00:00:01' UTC..'2038-01-19 03:14:07' UTC; fractional seconds up to 6 digits. "MySQL converts TIMESTAMP values from the current time zone to UTC for storage, and back from UTC to the current time zone for retrieval. (This does not occur for other types such as DATETIME.)" If the session `time_zone` differs between store and retrieve, the value differs. Invalid dates become zero dates unless strict mode/NO_ZERO_DATE. **MANDATORY awareness** (2038 limit; TZ conversion). — [13.2.2 The DATE, DATETIME, and TIMESTAMP Types](https://dev.mysql.com/doc/refman/8.4/en/datetime.html) (n.d.)
- Auto-init/update: `ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP, dt DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP`; "An auto-updated column is automatically updated to the current timestamp when the value of any other column in the row is changed"; with `explicit_defaults_for_timestamp` disabled the legacy behavior makes the first TIMESTAMP column auto-initialized and TIMESTAMP columns NOT NULL by default with NULL assignment meaning "now". **RECOMMENDED** (explicit DEFAULT/ON UPDATE clauses). — [13.2.5 Automatic Initialization and Updating for TIMESTAMP and DATETIME](https://dev.mysql.com/doc/refman/8.4/en/timestamp-initialization.html) (n.d.)
- Server defaults: "The server character set defaults to utf8mb4, and the server collation defaults to utf8mb4_0900_ai_ci"; these apply when CREATE DATABASE omits them. — [12.3.2 Server Character Set and Collation](https://dev.mysql.com/doc/refman/8.4/en/charset-server.html) (n.d.)
- utf8mb4 supports BMP and supplementary characters with up to four bytes and is a superset of utf8mb3. — [12.9.1 The utf8mb4 Character Set](https://dev.mysql.com/doc/refman/8.4/en/charset-unicode-utf8mb4.html) (n.d.)
- "The recommended character set for MySQL is utf8mb4. All new applications should use utf8mb4." "The utf8mb3 character set is deprecated. utf8mb3 remains supported for the lifetimes of the MySQL 8.0.x and MySQL 8.4.x LTS release series." "Expect utf8mb3 to be removed in a future major release of MySQL." **RECOMMENDED (strongly; deprecation)**. — [12.9.2 The utf8mb3 Character Set](https://dev.mysql.com/doc/refman/8.4/en/charset-unicode-utf8mb3.html) (n.d.)
- "Use the most efficient (smallest) data types possible... MEDIUMINT is often a better choice than INT because a MEDIUMINT column uses 25% less space." "Declare columns to be NOT NULL if possible. It makes SQL operations faster, by enabling better use of indexes and eliminating overhead for testing whether each value is NULL... Just avoid the default setting that allows NULL values in every column." InnoDB default row format DYNAMIC; compact row formats trade CPU for space. "Normally, try to keep all data nonredundant (observing what is referred to in database theory as third normal form)"; but "in a business intelligence scenario where you analyze all the data from large tables, you can relax the normalization rules, duplicating information or creating summary tables to gain more speed." **RECOMMENDED** (3NF for OLTP; denormalize for BI). — [10.4.1 Optimizing Data Size](https://dev.mysql.com/doc/refman/8.4/en/data-size.html) (n.d.)
- Join columns should have identical types/sizes and the same character set: "comparing a utf8mb4 column with a latin1 column precludes index use". — [10.3.1 How MySQL Uses Indexes](https://dev.mysql.com/doc/refman/8.4/en/mysql-indexes.html) (n.d.)

### Inferences
- MySQL docs are the only official source among the two that explicitly says 3NF for transactional data and denormalization/summary tables for BI: a workload-dependent (OLTP vs OLAP) rule stated by a vendor.
- Choosing TIMESTAMP for "instants" matches PostgreSQL's timestamptz semantics (UTC normalization) but carries a 2038 ceiling that PostgreSQL does not have; DATETIME has no normalization, so applications must normalize to UTC themselves.

### Gaps
- The 8.4 datetime page does not recommend one of DATETIME/TIMESTAMP over the other; the default of `explicit_defaults_for_timestamp` was not stated on the fetched page.

---

## MySQL Q3: Foreign keys, CHECK constraints (enforced since 8.0.16), generated columns, JSON

### Takeaway
InnoDB foreign keys require same storage engine, matching types, an index on referencing columns (auto-created), reject SET DEFAULT, and treat NO ACTION as RESTRICT (no deferral). CHECK constraints have been enforced since 8.0.16 (2019-04-25) with NULL/UNKNOWN passing and tight expression restrictions. Generated columns (VIRTUAL default, STORED optional) are the documented way to index JSON paths; multi-valued indexes handle JSON arrays.

### Cited Findings
- FK: "Parent and child tables must use the same storage engine, and they cannot be defined as temporary tables"; "The size and sign of fixed precision types such as INTEGER and DECIMAL must be the same"; "In the referencing table, there must be an index where the foreign key columns are listed as the first columns in the same order. Such an index is created on the referencing table automatically if it does not exist"; referencing non-unique/partial indexes is deprecated; "BLOB and TEXT columns cannot be included in a foreign key"; "InnoDB does not currently support foreign keys for tables with user-defined partitioning. This includes both parent and child tables." Actions: CASCADE ("Cascaded foreign key actions do not activate triggers"), SET NULL (columns must not be NOT NULL), RESTRICT, NO ACTION ("For InnoDB, this is equivalent to RESTRICT; the delete or update operation for the parent table is immediately rejected"), SET DEFAULT ("Both InnoDB and NDB reject table definitions containing ON DELETE SET DEFAULT or ON UPDATE SET DEFAULT"). Example: `FOREIGN KEY (product_category, product_id) REFERENCES product(category, id) ON UPDATE CASCADE ON DELETE RESTRICT`. `foreign_key_checks` re-enable "does not trigger a scan of table data". **MANDATORY** (engine and type matching; no deferral). — [15.1.20.5 FOREIGN KEY Constraints](https://dev.mysql.com/doc/refman/8.4/en/create-table-foreign-keys.html) (n.d.)
- CHECK: `[CONSTRAINT [symbol]] CHECK (expr) [[NOT] ENFORCED]`; expr "must evaluate to TRUE or UNKNOWN (for NULL values) for each row... If the condition evaluates to FALSE, it fails"; auto names `tbl_chk_N`; names must be unique per schema; expressions may not use AUTO_INCREMENT columns, other tables, nondeterministic functions (NOW(), CURRENT_USER(), CONNECTION_ID()), stored/loadable functions, variables, or subqueries; CHECK columns cannot be used in FK referential actions and vice versa; `INSERT IGNORE` downgrades violations to warnings; evaluation uses the session SQL mode. Example `c2 INT CONSTRAINT c2_positive CHECK (c2 > 0)`. **MANDATORY** (NULL passes; IGNORE bypass). — [15.1.20.6 CHECK Constraints](https://dev.mysql.com/doc/refman/8.4/en/create-table-check-constraints.html) (n.d.)
- Release note: "Previously, MySQL permitted a limited form of CHECK constraint syntax, but parsed and ignored it. MySQL now implements the core features of table and column CHECK constraints, for all storage engines." Release 8.0.16 date: 2019-04-25. — [Changes in MySQL 8.0.16](https://dev.mysql.com/doc/relnotes/mysql/8.0/en/news-8-0-16.html) (2019-04-25)
- Generated columns: `col_name data_type [GENERATED ALWAYS] AS (expr) [VIRTUAL | STORED]`; VIRTUAL is default (no storage, computed on read, InnoDB supports secondary indexes on them); STORED is materialized; example `sidec DOUBLE AS (SQRT(sidea * sidea + sideb * sideb))`; same deterministic-expression restrictions as CHECK; cannot use AUTO_INCREMENT; use cases: unify query logic, materialized cache, simulate functional indexes (JSON), optimizer uses indexed generated columns for matching expressions. — [15.1.20.8 CREATE TABLE and Generated Columns](https://dev.mysql.com/doc/refman/8.4/en/create-table-generated-columns.html) (n.d.)
- JSON indexing: "JSON columns cannot be indexed directly"; `CREATE TABLE jemp (c JSON, g INT GENERATED ALWAYS AS (c->"$.id"), INDEX i (g));` then `SELECT c->>"$.name" FROM jemp WHERE g > 2` uses index `i` (EXPLAIN type: range). InnoDB virtual-column indexes are secondary only; indexed virtual values are materialized in the index and computed on INSERT/UPDATE. — [15.1.20.9 Secondary Indexes and Generated Columns](https://dev.mysql.com/doc/refman/8.4/en/create-table-secondary-indexes.html) (n.d.)
- JSON type: "Automatic validation of JSON documents stored in JSON columns. Invalid documents produce an error"; "Optimized storage format"; document size limited by `max_allowed_packet`; "JSON columns, like columns of other binary types, are not indexed directly"; InnoDB supports multi-valued indexes on JSON arrays; partial in-place updates for JSON_SET/JSON_REPLACE/JSON_REMOVE with `binlog_row_value_options=PARTIAL_JSON`; "last duplicate key wins"; key order "not guaranteed to be consistent across releases"; BETWEEN/IN/GREATEST/LEAST unsupported on JSON values. — [13.5 The JSON Data Type](https://dev.mysql.com/doc/refman/8.4/en/json.html) (n.d.)
- CREATE INDEX: "A UNIQUE index permits multiple NULL values for columns that can contain NULL"; prefix indexes `INDEX part_of_name (name(10))` with limits 767 bytes (REDUNDANT/COMPACT) and 3072 bytes (DYNAMIC/COMPRESSED); "Prefixes must be specified for BLOB and TEXT key parts"; functional key parts `CREATE INDEX idx1 ON t1 ((col1 + col2));` ("primary keys cannot include functional key parts"; implemented as hidden virtual generated columns); multi-valued `INDEX zips ((CAST(custinfo->'$.zipcode' AS UNSIGNED ARRAY)))` used by MEMBER OF(), JSON_CONTAINS(), JSON_OVERLAPS(); descending indexes; invisible indexes. — [15.1.15 CREATE INDEX Statement](https://dev.mysql.com/doc/refman/8.4/en/create-index.html) (n.d.)

### Inferences
- Both engines agree that CHECK passes on NULL/UNKNOWN (universal SQL semantics) and both forbid non-deterministic or subquery-based CHECK expressions.
- MySQL's inability to defer FK checks and its rejection of SET DEFAULT are hard engine differences that affect portable schema designs with circular references or default-restoring semantics.

### Gaps
- MySQL docs fetched do not discuss `NULLS NOT DISTINCT` equivalents; InnoDB unique indexes simply allow multiple NULLs.

---

## MySQL Q4: Partitioning and its limitations (including FK restriction)

### Takeaway
MySQL partitioning (InnoDB/NDB) forbids foreign keys in both directions, FULLTEXT and spatial columns, caps at 8192 partitions, requires integer partitioning expressions (except KEY and RANGE/LIST COLUMNS), and imposes the same unique-key rule as PostgreSQL: every unique key (including the PK) must include all partitioning columns.

### Cited Findings
- "A partitioned InnoDB table cannot contain foreign key references"; "An InnoDB table with foreign key references cannot be partitioned"; "An InnoDB table cannot reference a user-partitioned table"; partitioned tables do not support FULLTEXT or spatial columns; temporary and log tables cannot be partitioned; max 8192 partitions (non-NDB) including subpartitions; many partitions can hit "Out of resources when opening file"; partitioning expressions must resolve to integers (exceptions: [LINEAR] KEY accepts any type but TEXT/BLOB; RANGE COLUMNS/LIST COLUMNS accept string, DATE, DATETIME); subpartitions must be HASH or KEY under RANGE/LIST; SQL mode changes after creation can make partitioned tables inaccessible ("never change the SQL mode after creating partitioned tables"); after `ADD COLUMN ... ALGORITHM=INSTANT` partitions can no longer be exchanged. **MANDATORY** (hard limits). — [26.6 Restrictions and Limitations on Partitioning](https://dev.mysql.com/doc/refman/8.4/en/partitioning-limitations.html) (n.d.)
- "All columns used in the partitioning expression for a partitioned table must be part of every unique key that the table may have"; "Since every primary key is by definition a unique key, this restriction also includes the table's primary key"; error `ERROR 1491 (HY000): A PRIMARY KEY must include all columns in the table's partitioning function`; a table with `UNIQUE KEY (col1, col3), UNIQUE KEY (col2, col4)` "cannot be partitioned at all"; tables with no unique keys are exempt. **MANDATORY**. — [26.6.1 Partitioning Keys, Primary Keys, and Unique Keys](https://dev.mysql.com/doc/refman/8.4/en/partitioning-limitations-partitioning-keys-unique-keys.html) (n.d.)

### Inferences
- Universal: "partition key must be part of every unique key" holds in both engines (PostgreSQL phrases it as the constraint's columns must include all partition-key columns).
- Engine-specific: MySQL loses foreign keys entirely when partitioning; PostgreSQL's fetched page lists no such FK prohibition (though its FK-on-partitioned-table support could not be confirmed from the fetched extract).

### Gaps
- MySQL docs give no "when is partitioning worthwhile" rule analogous to PostgreSQL's "table larger than RAM" heuristic.

---

## MySQL Q5: Identifier rules and case sensitivity (lower_case_table_names)

### Takeaway
MySQL identifiers are 64 characters (aliases 256, labels 16), BMP-only Unicode, quoted with backticks (double quotes only with ANSI_QUOTES). Database/table name case sensitivity depends on the file system and `lower_case_table_names`, which cannot be changed after initialization; the manual recommends always using lowercase names and, for InnoDB portability, `lower_case_table_names=1` everywhere.

### Cited Findings
- Length limits (characters): database 64, table 64, column 64, index 64, constraint 64, stored program 64, view 64, tablespace 64, server 64, log file group 64, alias 256 (view column aliases checked at 64), compound statement label 16, user-defined variable 64, resource group 64; "Identifiers are stored using Unicode (UTF-8)"; generated `_ibfk_`/`_chk_` names can exceed 64 if the table name is near the limit. — [11.2.1 Identifier Length Limits](https://dev.mysql.com/doc/refman/8.4/en/identifier-length.html) (n.d.)
- Permitted characters: unquoted `[0-9a-zA-Z$_]` plus U+0080..U+FFFF; quoted U+0001..U+007F plus U+0080..U+FFFF; "Only the Unicode Basic Multilingual Plane (BMP) is allowed"; identifiers may begin with a digit but unquoted may not consist solely of digits; names cannot end with spaces; backtick quoting (`` CREATE TABLE `a``b` (`c"d` INT); ``); `ANSI_QUOTES` enables double-quoted identifiers; reserved words must be quoted. — [11.2 Schema Object Names](https://dev.mysql.com/doc/refman/8.4/en/identifiers.html) (n.d.)
- Case: database/table names depend on file system (case-sensitive on most Unix, not on Windows; macOS HFS+ insensitive); column, index, stored routine, event, resource group, partition names and column aliases are never case-sensitive; `lower_case_table_names` 0/1/2 with defaults Unix 0, Windows 1, macOS 2; "it is best to adopt a consistent convention, such as always creating and referring to databases and tables using lowercase names. This convention is recommended for maximum portability and ease of use"; "If you are using InnoDB tables and you are trying to avoid these data transfer problems, you should use lower_case_table_names=1 on all platforms"; "Changing the lower_case_table_names setting after the server is initialized is prohibited"; do not use 0 on case-insensitive file systems (MyISAM index corruption risk). **RECOMMENDED (lowercase); MANDATORY (setting fixed at init)**. — [11.2.3 Identifier Case Sensitivity](https://dev.mysql.com/doc/refman/8.4/en/identifier-case-sensitivity.html) (n.d.)

### Inferences
- Both vendors converge on lowercase identifiers for portability, from different root causes: PostgreSQL's lower-case folding versus MySQL's file-system-dependent table names.
- Identifier limits differ in unit: PostgreSQL 63 bytes (multibyte names consume more) vs MySQL 64 characters (multibyte does not reduce count).

### Gaps
- None material.

---

## MySQL Q6: Index optimization guidance

### Takeaway
MySQL's optimization chapter prescribes: index the columns used in WHERE/joins, exploit leftmost prefixes of composite indexes, prefer a few composite indexes over many single-column ones, keep the PK short, use prefix indexes on long strings, match types and charsets across join columns, declare indexed columns NOT NULL where possible, and recognize that indexes slow inserts/updates and matter less for small tables or full-scan reports.

### Cited Findings
- Index structures: PRIMARY KEY, UNIQUE, INDEX, FULLTEXT stored in B-trees; spatial in R-trees; MEMORY tables support hash; "the optimizer can use (col1), (col1, col2), and (col1, col2, col3)" of an index on (col1, col2, col3) (leftmost prefix); indexes serve WHERE, joins, MIN()/MAX(), ORDER BY/GROUP BY, and covering reads; "Indexes are less important for queries on small tables, or big tables where report queries process most or all of the rows." — [10.3.1 How MySQL Uses Indexes](https://dev.mysql.com/doc/refman/8.4/en/mysql-indexes.html) (n.d.)
- "Create only the indexes that you need to improve query performance. Indexes are good for retrieval, but slow down insert and update operations"; "create a single composite index on them rather than a separate index for each column. The first part of the index should be the column most used"; prefix indexes: "Shorter indexes are faster... more hits in the index cache". **RECOMMENDED**. — [10.4.1 Optimizing Data Size](https://dev.mysql.com/doc/refman/8.4/en/data-size.html) (n.d.)
- "Do not create a separate secondary index for each column, because each query can only make use of one index. Indexes on rarely tested columns or columns with only a few different values might not be helpful"; covering index "might be able to avoid reading the table data at all". — [10.5.6 Optimizing InnoDB Queries](https://dev.mysql.com/doc/refman/8.4/en/optimizing-innodb-queries.html) (n.d.)
- Functional indexes, multi-valued indexes, descending and invisible indexes (see MySQL Q3 CREATE INDEX citation). — [15.1.15 CREATE INDEX Statement](https://dev.mysql.com/doc/refman/8.4/en/create-index.html)

### Inferences
- MySQL's "composite index with most-used column first" parallels PostgreSQL's Example 11.4 advice to put the low-cardinality column first in a single index instead of many partial indexes: a universal indexing heuristic stated by both vendors.

### Gaps
- MySQL's "each query can only make use of one index" is a simplification (index merge exists) but is the manual's stated guidance; not contradicted by other fetched pages.

---

## MySQL Q7: Transaction isolation (REPEATABLE READ default) and online DDL / instant ADD COLUMN

### Takeaway
InnoDB defaults to REPEATABLE READ with gap/next-key locking; READ COMMITTED uses per-statement snapshots, disables most gap locks, and requires row-based binary logging. Online DDL in 8.4 defaults to ALGORITHM=INSTANT where possible: ADD/DROP COLUMN, RENAME COLUMN, SET/DROP DEFAULT are metadata-only, limited to 64 row versions before a rebuild (255 as of 9.1.0); data-type changes and PK drops require table copies.

### Cited Findings
- "The default isolation level for InnoDB is REPEATABLE READ." Consistent reads use the first-read snapshot; locking reads use gap/next-key locks; READ COMMITTED sets a fresh snapshot per read, disables gap locking except for FK/duplicate-key checks, "Only row-based binary logging is supported"; READ UNCOMMITTED allows dirty reads; SERIALIZABLE converts plain SELECT to `SELECT ... FOR SHARE` when autocommit is off. Example: under REPEATABLE READ session A's `UPDATE t SET b = 5 WHERE b = 3` blocks session B's `UPDATE t SET b = 4 WHERE b = 2` on the first row; under READ COMMITTED B proceeds on non-matching rows. — [17.7.2.1 Transaction Isolation Levels](https://dev.mysql.com/doc/refman/8.4/en/innodb-transaction-isolation-levels.html) (n.d.)
- Online DDL column operations: adding a column Instant=Yes (any position), dropping a column Instant=Yes, renaming Instant=Yes, set/drop default Instant=Yes, modifying ENUM/SET Instant=Yes; reordering columns rebuilds; "Changing the column data type" is not instant, not in place, rebuilds, no concurrent DML ("only supported with ALGORITHM=COPY"); extending VARCHAR in place only within the same length-byte class (<256 vs >=256). INSTANT restrictions: not on ROW_FORMAT=COMPRESSED, FULLTEXT-indexed, data-dictionary or temporary tables; 1022-column internal limit; each instant ADD/DROP creates a row version with a maximum of 64 in 8.4 (255 as of 9.1.0), after which "Maximum row versions reached... Please use COPY/INPLACE". Example: `ALTER TABLE t1 ADD COLUMN c2 INT, ADD COLUMN c3 INT, ALGORITHM=INSTANT;`. Index ops: add/drop secondary index in place with concurrent DML; adding a PK rebuilds; dropping a PK requires COPY. **RECOMMENDED** (define PK at CREATE; plan type changes as rebuilds). — [17.12.1 Online DDL Operations](https://dev.mysql.com/doc/refman/8.4/en/innodb-online-ddl-operations.html) (n.d.)

### Inferences
- Schema evolution guidance differs: MySQL documents a metadata-only path for column additions/drops with a version cap; PostgreSQL's equivalent (ADD COLUMN with constant default being metadata-only) was not in scope of the fetched pages, so no official comparison is drawn here.

### Gaps
- PostgreSQL ALTER TABLE cost semantics were not fetched; do not infer parity.

---

## MySQL Q8: Backup (mysqldump, MySQL Enterprise Backup, binary log PITR) and security roles

### Takeaway
MySQL documents MySQL Enterprise Backup (commercial, hot physical backups for InnoDB), mysqldump (logical; `--single-transaction` for online InnoDB dumps), file copies/snapshots (with FLUSH TABLES WITH READ LOCK; not valid for InnoDB files alone), delimited-text exports, incremental backups via binary logs (enabled by default in 8.4), and backups from replicas; PITR = restore full backup then replay binlogs with mysqlbinlog in a single connection. Security is role-based (`CREATE ROLE`, `GRANT ... TO role`, `SET DEFAULT ROLE`, `mandatory_roles`).

### Cited Findings
- MySQL Enterprise Backup: "physical backups of entire instances or selected databases and tables", incremental and compressed, hot backup for InnoDB, "restore much faster than logical tools like mysqldump"; mysqldump: "For InnoDB, --single-transaction produces an online backup that takes no table locks" (`mysqldump --single-transaction --all-databases > backup.sql`); file copies for MyISAM only, with `FLUSH TABLES tbl_list WITH READ LOCK` and a warning that InnoDB may hold unflushed data in memory; `SELECT ... INTO OUTFILE` / `mysqldump --tab`; incremental backups: "Binary logging is enabled by default in MySQL 8.4", `FLUSH LOGS` to rotate then copy logs; back up replicas instead of the source (include connection and applier metadata repositories); snapshot procedure (FLUSH TABLES WITH READ LOCK, mount snapshot, UNLOCK TABLES, copy). — [9.2 Database Backup Methods](https://dev.mysql.com/doc/refman/8.4/en/backup-methods.html) (n.d.)
- PITR definition: "recovery of data changes up to a given point in time... performed after restoring a full backup." — [9.5 Point-in-Time (Incremental) Recovery](https://dev.mysql.com/doc/refman/8.4/en/point-in-time-recovery.html) (n.d.)
- "To allow a server to be restored to a point-in-time, binary logging must be enabled on it, which is the default setting for MySQL 8.4"; `SHOW BINARY LOGS; SHOW BINARY LOG STATUS;`; `mysqlbinlog binlog_files | mysql -u root -p`; "If you have more than one binary log to apply on the MySQL server, use a single connection to apply the contents of all binary log files"; for encrypted logs use `--read-from-remote-server ... --ssl-mode=required` (VERIFY_CA/VERIFY_IDENTITY preferred). **MANDATORY** (binlog enabled; single connection for multi-file replay). — [9.5.1 Point-in-Time Recovery Using Binary Log](https://dev.mysql.com/doc/refman/8.4/en/point-in-time-recovery-binlog.html) (n.d.)
- Roles: "A role is a named collection of privileges"; `CREATE ROLE 'app_developer', 'app_read', 'app_write'; GRANT ALL ON app_db.* TO 'app_developer'; GRANT SELECT ON app_db.* TO 'app_read'; GRANT INSERT, UPDATE, DELETE ON app_db.* TO 'app_write'; GRANT 'app_read', 'app_write' TO 'rw_user1'@'localhost';` roles are not active until `SET DEFAULT ROLE` or `activate_all_roles_on_login` (off by default); `mandatory_roles` are implicitly granted to all users; the page mentions neither column-level privileges nor row-level security. — [8.2.10 Using Roles](https://dev.mysql.com/doc/refman/8.4/en/roles.html) (n.d.)

### Inferences
- Backup architecture is universal across engines: logical dump + physical base backup + continuous log (WAL vs binlog) for PITR; tool names and defaults differ (PG requires enabling archive_mode; MySQL binlog is on by default).

### Gaps
- MySQL column-level privileges and any row-filtering mechanism (e.g., views) were not researched; the roles page alone does not establish MySQL's full security feature set.

---

## Synthesis: Universal principles vs engine-specific prescriptions, and where sources conflict

### Takeaway
Both vendors agree on a core of universal rules (declare integrity in the database, exact numerics for money, UTC-normalized instant types, NOT NULL by default, every table has a PK, partition keys inside unique keys, lowercase identifiers for portability, logical + physical + log-based backups). They diverge on clustered vs heap storage, FK semantics (deferral, SET DEFAULT, auto-indexing), default isolation, identifier limits, string-length philosophy, and partitioning restrictions.

### Cited Findings (comparison, each side cited above)
- UNIVERSAL / MANDATORY: exact numeric for money. PG: numeric "especially recommended for storing monetary amounts" [8.1 Numeric Types](https://www.postgresql.org/docs/current/datatype-numeric.html); MySQL: DECIMAL "for example with monetary data" [13.1.3 Fixed-Point Types](https://dev.mysql.com/doc/refman/8.4/en/fixed-point-types.html). All workloads.
- UNIVERSAL / RECOMMENDED (strong): primary key on every table. PG: "usually best practice" [Constraints](https://www.postgresql.org/docs/current/ddl-constraints.html); MySQL: "A primary key should be defined for each table" [Clustered and Secondary Indexes](https://dev.mysql.com/doc/refman/8.4/en/innodb-index-types.html); PG logical replication additionally needs a replica identity [29.8 Restrictions](https://www.postgresql.org/docs/current/logical-replication-restrictions.html). All workloads.
- UNIVERSAL / RECOMMENDED: NOT NULL by default. PG: "the majority of columns should be NOT NULL" [Constraints](https://www.postgresql.org/docs/current/ddl-constraints.html); MySQL: "Declare columns to be NOT NULL if possible" [Optimizing Data Size](https://dev.mysql.com/doc/refman/8.4/en/data-size.html). All.
- UNIVERSAL / MANDATORY: CHECK passes on NULL/UNKNOWN in both engines [PG Constraints](https://www.postgresql.org/docs/current/ddl-constraints.html); [MySQL CHECK Constraints](https://dev.mysql.com/doc/refman/8.4/en/create-table-check-constraints.html). All.
- UNIVERSAL / MANDATORY: partition key columns must be in every unique key/PK [PG 5.12](https://www.postgresql.org/docs/current/ddl-partitioning.html); [MySQL 26.6.1](https://dev.mysql.com/doc/refman/8.4/en/partitioning-limitations-partitioning-keys-unique-keys.html). OLTP and OLAP.
- UNIVERSAL / RECOMMENDED: lowercase identifiers for portability [PG wiki](https://wiki.postgresql.org/wiki/Don%27t_Do_This); [MySQL 11.2.3](https://dev.mysql.com/doc/refman/8.4/en/identifier-case-sensitivity.html). All.
- UNIVERSAL / RECOMMENDED: UTC-normalized instant type: PG timestamptz stored as UTC [8.5](https://www.postgresql.org/docs/current/datatype-datetime.html); MySQL TIMESTAMP converted to UTC [13.2.2](https://dev.mysql.com/doc/refman/8.4/en/datetime.html). Engine-specific caveat: MySQL TIMESTAMP ends 2038-01-19.
- UNIVERSAL / RECOMMENDED: composite index with most-used/low-cardinality column first rather than many narrow indexes [PG 11.8 Example 11.4](https://www.postgresql.org/docs/current/indexes-partial.html); [MySQL 10.4.1](https://dev.mysql.com/doc/refman/8.4/en/data-size.html). OLTP primarily.
- UNIVERSAL / CONTEXTUAL (OLTP vs OLAP): normalize to 3NF for transactional data; denormalize/summary tables for BI [MySQL 10.4.1](https://dev.mysql.com/doc/refman/8.4/en/data-size.html); more partitions acceptable for warehouse workloads than OLTP [PG 5.12](https://www.postgresql.org/docs/current/ddl-partitioning.html).
- ENGINE-SPECIFIC: storage model. InnoDB clustered index (row data in PK B-tree; secondary indexes carry PK) [MySQL 17.6.2.1](https://dev.mysql.com/doc/refman/8.4/en/innodb-index-types.html) vs PostgreSQL heap + visibility map with all indexes secondary [PG 11.9](https://www.postgresql.org/docs/current/indexes-index-only-scans.html). Consequence: "short PK" and "insert in PK order" are InnoDB-specific; PG's uuidv7 is motivated by time-ordering rather than clustering.
- ENGINE-SPECIFIC: surrogate keys. PG identity columns (SQL standard) / serial (wiki: avoid) [5.3](https://www.postgresql.org/docs/current/ddl-identity-columns.html), [wiki](https://wiki.postgresql.org/wiki/Don%27t_Do_This); MySQL AUTO_INCREMENT with `innodb_autoinc_lock_mode` and (26.7) batch persistence [17.1.2](https://dev.mysql.com/doc/refman/8.4/en/innodb-best-practices.html), [26.7 nutshell](https://dev.mysql.com/doc/refman/26.7/en/mysql-nutshell.html).
- ENGINE-SPECIFIC: FK semantics. PG: NO ACTION deferrable, RESTRICT immediate, SET DEFAULT allowed, referencing columns NOT auto-indexed [Constraints](https://www.postgresql.org/docs/current/ddl-constraints.html); MySQL/InnoDB: NO ACTION = RESTRICT (immediate), SET DEFAULT rejected, referencing index auto-created, FKs incompatible with partitioning [15.1.20.5](https://dev.mysql.com/doc/refman/8.4/en/create-table-foreign-keys.html), [26.6](https://dev.mysql.com/doc/refman/8.4/en/partitioning-limitations.html).
- ENGINE-SPECIFIC: default isolation. PG READ COMMITTED [13.2](https://www.postgresql.org/docs/current/transaction-iso.html); InnoDB REPEATABLE READ [17.7.2.1](https://dev.mysql.com/doc/refman/8.4/en/innodb-transaction-isolation-levels.html).
- ENGINE-SPECIFIC: identifiers. PG 63 bytes, lower-case folding, quoting makes case-sensitive [4.1.1](https://www.postgresql.org/docs/current/sql-syntax-lexical.html); MySQL 64 characters, backticks, file-system-dependent table-name case, lower_case_table_names fixed at init [11.2.1](https://dev.mysql.com/doc/refman/8.4/en/identifier-length.html), [11.2.3](https://dev.mysql.com/doc/refman/8.4/en/identifier-case-sensitivity.html).
- ENGINE-SPECIFIC: unique constraints and NULL. PG default NULLS DISTINCT with `NULLS NOT DISTINCT` option [Constraints](https://www.postgresql.org/docs/current/ddl-constraints.html); MySQL "A UNIQUE index permits multiple NULL values" with no documented alternative on the fetched page [CREATE INDEX](https://dev.mysql.com/doc/refman/8.4/en/create-index.html).
- ENGINE-SPECIFIC: JSON. PG jsonb directly GIN-indexable [8.14](https://www.postgresql.org/docs/current/datatype-json.html); MySQL JSON indexed only via generated columns or multi-valued indexes [13.5](https://dev.mysql.com/doc/refman/8.4/en/json.html), [15.1.20.9](https://dev.mysql.com/doc/refman/8.4/en/create-table-secondary-indexes.html).
- ENGINE-SPECIFIC: security. PG row-level security, column grants, schema search_path hardening [5.9](https://www.postgresql.org/docs/current/ddl-rowsecurity.html), [5.8](https://www.postgresql.org/docs/current/ddl-priv.html), [5.10](https://www.postgresql.org/docs/current/ddl-schemas.html); MySQL roles (database-level grants shown) [8.2.10](https://dev.mysql.com/doc/refman/8.4/en/roles.html).

### Conflicts between sources
- CONFLICT (philosophy): string column sizing. PostgreSQL manual: "no performance difference" among text/varchar/char and wiki "Don't use varchar(n) by default" [8.3](https://www.postgresql.org/docs/current/datatype-character.html), [wiki](https://wiki.postgresql.org/wiki/Don%27t_Do_This); MySQL manual: "Use the most efficient (smallest) data types possible" and prefix indexes for long strings [10.4.1](https://dev.mysql.com/doc/refman/8.4/en/data-size.html). Resolution: engine-specific; PostgreSQL's TOAST/varlena storage makes declared length irrelevant to performance, while MySQL's row formats, index prefix limits (767/3072 bytes) and in-place VARCHAR growth classes make declared size matter.
- CONFLICT (strength, not fact): PostgreSQL manual is neutral on identity vs serial [5.3](https://www.postgresql.org/docs/current/ddl-identity-columns.html); the wiki says don't use serial [wiki](https://wiki.postgresql.org/wiki/Don%27t_Do_This).
- CONFLICT (strength): manual "recommends" timestamp types containing both date and time when using time zones and "does not recommend" timetz [8.5](https://www.postgresql.org/docs/current/datatype-datetime.html); wiki says "don't use timestamp (without time zone)" at all except for abstract app-handled values [wiki](https://wiki.postgresql.org/wiki/Don%27t_Do_This).
- CONFLICT (naming): MySQL optimization page suggests short unprefixed column names (`name` not `customer_name`, "shorter than 18 characters" for portability) [10.4.1](https://dev.mysql.com/doc/refman/8.4/en/data-size.html); PostgreSQL wiki prescribes only lowercase_with_underscores and otherwise defers to application conventions [wiki](https://wiki.postgresql.org/wiki/Don%27t_Do_This). Neither vendor publishes a formal naming standard (see next section).
- NON-CONFLICT clarification: the "random PKs are bad in InnoDB" claim is widely attributed to MySQL but the official 8.4 pages fetched only say PK-order inserts are faster and PKs should be short [10.5.5](https://dev.mysql.com/doc/refman/8.4/en/optimizing-innodb-bulk-data-loading.html), [17.6.2.1](https://dev.mysql.com/doc/refman/8.4/en/innodb-index-types.html).

### Inferences
- A cross-engine schema standard can safely mandate: PK on every table, NOT NULL default, exact numerics for money, UTC instant types, constraints declared in-database, partition key inside unique keys, lowercase snake_case identifiers at or below 63 bytes, and explicit isolation level per transaction class. Everything about surrogate key type (identity vs AUTO_INCREMENT), key ordering, varchar sizing, FK deferral, and JSON indexing must be written as engine-specific annexes.

### Gaps
- No official source from either vendor quantifies trade-offs (e.g., exact overhead of numeric vs bigint-cents, or the cost of random PKs); such numbers must come from non-official benchmarks.

---

## Naming conventions: is there official guidance?

### Takeaway
Neither PostgreSQL nor MySQL publishes a formal naming-convention standard. The official material is limited to: PostgreSQL's lower-case folding/quoting consistency/63-byte limit/`pg_` reservation and the wiki's "lowercase with underscores"; MySQL's "always creating and referring to databases and tables using lowercase names", 64-character limits, and an optimization-page suggestion to keep column names simple and under 18 characters for portability.

### Cited Findings
- PostgreSQL manual: quote always or never; identifiers containing digits or starting/ending with underscore "are safe against possible conflict with future extensions of the standard"; `$` is non-standard; 63-byte truncation. — [4.1.1 Identifiers and Key Words](https://www.postgresql.org/docs/current/sql-syntax-lexical.html)
- PostgreSQL manual: avoid `pg_`-prefixed names (reserved for system catalogs); avoid the public schema for standards conformance. — [5.10 Schemas](https://www.postgresql.org/docs/current/ddl-schemas.html)
- PostgreSQL wiki: "Don't use upper case table or column names... Use lowercase names with underscores"; use column aliases for readable report headers. — [Don't Do This](https://wiki.postgresql.org/wiki/Don%27t_Do_This) (2024-11-21)
- PostgreSQL wiki (2016): name the owner role after the schema; create read/write and read-only roles. — [Database Schema Recommendations for an Application](https://wiki.postgresql.org/wiki/Database_Schema_Recommendations_for_an_Application) (2016-09-15)
- MySQL manual: "always creating and referring to databases and tables using lowercase names... recommended for maximum portability and ease of use". — [11.2.3 Identifier Case Sensitivity](https://dev.mysql.com/doc/refman/8.4/en/identifier-case-sensitivity.html)
- MySQL manual: "Keep column names simple, so that you can use the same name across different tables and simplify join queries. For example, in a table named customer, use a column name of name instead of customer_name. To make your names portable to other SQL servers, consider keeping them shorter than 18 characters." — [10.4.1 Optimizing Data Size](https://dev.mysql.com/doc/refman/8.4/en/data-size.html)
- MySQL manual: reserved words must be quoted when used as identifiers; names may not end with spaces or consist solely of digits unquoted. — [11.2 Schema Object Names](https://dev.mysql.com/doc/refman/8.4/en/identifiers.html)

### Inferences
- A portable naming rule derivable from both vendors: lowercase ASCII letters, digits, underscores; no leading/trailing underscore issues for keyword safety (PG) but avoid `pg_` prefix; length at most 63 bytes (the stricter of 63 bytes vs 64 characters); never rely on case to distinguish objects; quote nothing (so folding/case-insensitivity are irrelevant).

### Gaps
- Explicitly: there is no official PostgreSQL or MySQL naming-convention document (singular vs plural table names, FK column naming, index naming). The auto-generated constraint-name patterns are the only vendor conventions found: PostgreSQL `<table>_<col>_fkey`/`_not_null` style appears in examples (e.g., `products_name_not_null`, `orders_customer_id_fkey`), MySQL `tbl_chk_N` and `_ibfk_N`.

---

## Supplementary verified sources not placed in the JSON catalog

All opened with WebFetch on 2026-11-07 and cited above: [PG 8.3 Character Types](https://www.postgresql.org/docs/current/datatype-character.html); [PG 8.2 Monetary Types](https://www.postgresql.org/docs/current/datatype-money.html); [PG 8.6 Boolean](https://www.postgresql.org/docs/current/datatype-boolean.html); [PG 8.7 Enumerated Types](https://www.postgresql.org/docs/current/datatype-enum.html); [PG 8.12 UUID Type](https://www.postgresql.org/docs/current/datatype-uuid.html); [PG 9.14 UUID Functions](https://www.postgresql.org/docs/current/functions-uuid.html); [PG 5.3 Identity Columns](https://www.postgresql.org/docs/current/ddl-identity-columns.html); [PG 5.4 Generated Columns](https://www.postgresql.org/docs/current/ddl-generated-columns.html); [PG 11.8 Partial Indexes](https://www.postgresql.org/docs/current/indexes-partial.html); [PG 11.9 Index-Only Scans](https://www.postgresql.org/docs/current/indexes-index-only-scans.html); [PG 5.10 Schemas](https://www.postgresql.org/docs/current/ddl-schemas.html); [PG 5.8 Privileges](https://www.postgresql.org/docs/current/ddl-priv.html); [PG SET CONSTRAINTS](https://www.postgresql.org/docs/current/sql-set-constraints.html); [PG 25 Backup and Restore](https://www.postgresql.org/docs/current/backup.html); [PG 29 Logical Replication](https://www.postgresql.org/docs/current/logical-replication.html); [PG 29.8 Restrictions](https://www.postgresql.org/docs/current/logical-replication-restrictions.html); [PG Versioning Policy](https://www.postgresql.org/support/versioning/); [PG wiki Database Schema Recommendations for an Application](https://wiki.postgresql.org/wiki/Database_Schema_Recommendations_for_an_Application); [MySQL 13.1.3 Fixed-Point Types](https://dev.mysql.com/doc/refman/8.4/en/fixed-point-types.html); [MySQL 13.2.5 Automatic Initialization](https://dev.mysql.com/doc/refman/8.4/en/timestamp-initialization.html); [MySQL 12.3.2 Server Character Set](https://dev.mysql.com/doc/refman/8.4/en/charset-server.html); [MySQL 12.9.1 utf8mb4](https://dev.mysql.com/doc/refman/8.4/en/charset-unicode-utf8mb4.html); [MySQL 12.9.2 utf8mb3](https://dev.mysql.com/doc/refman/8.4/en/charset-unicode-utf8mb3.html); [MySQL 15.1.20.8 Generated Columns](https://dev.mysql.com/doc/refman/8.4/en/create-table-generated-columns.html); [MySQL 15.1.20.9 Secondary Indexes and Generated Columns](https://dev.mysql.com/doc/refman/8.4/en/create-table-secondary-indexes.html); [MySQL 13.5 JSON](https://dev.mysql.com/doc/refman/8.4/en/json.html); [MySQL 15.1.15 CREATE INDEX](https://dev.mysql.com/doc/refman/8.4/en/create-index.html); [MySQL 26.6.1 Partitioning Keys](https://dev.mysql.com/doc/refman/8.4/en/partitioning-limitations-partitioning-keys-unique-keys.html); [MySQL 11.2 Schema Object Names](https://dev.mysql.com/doc/refman/8.4/en/identifiers.html); [MySQL 11.2.1 Identifier Length Limits](https://dev.mysql.com/doc/refman/8.4/en/identifier-length.html); [MySQL 17.12.1 Online DDL Operations](https://dev.mysql.com/doc/refman/8.4/en/innodb-online-ddl-operations.html); [MySQL 9.5 PITR](https://dev.mysql.com/doc/refman/8.4/en/point-in-time-recovery.html); [MySQL 9.5.1 PITR Using Binary Log](https://dev.mysql.com/doc/refman/8.4/en/point-in-time-recovery-binlog.html); [MySQL 10.4.1 Optimizing Data Size](https://dev.mysql.com/doc/refman/8.4/en/data-size.html); [MySQL 10.3.1 How MySQL Uses Indexes](https://dev.mysql.com/doc/refman/8.4/en/mysql-indexes.html); [MySQL 10.5.5 Bulk Data Loading](https://dev.mysql.com/doc/refman/8.4/en/optimizing-innodb-bulk-data-loading.html); [MySQL 10.5.6 Optimizing InnoDB Queries](https://dev.mysql.com/doc/refman/8.4/en/optimizing-innodb-queries.html); [MySQL 8.2.10 Using Roles](https://dev.mysql.com/doc/refman/8.4/en/roles.html); [MySQL 8.0.16 Release Notes](https://dev.mysql.com/doc/relnotes/mysql/8.0/en/news-8-0-16.html); [MySQL Documentation home](https://dev.mysql.com/doc/); [MySQL 2.1.2 Which Version](https://dev.mysql.com/doc/refman/8.4/en/which-version.html); [MySQL 26.7 Release Notes](https://dev.mysql.com/doc/relnotes/mysql/26.7/en/); [MySQL 26.7 What Is New](https://dev.mysql.com/doc/refman/26.7/en/mysql-nutshell.html).

Search-returned but not opened (not relied on for any fact beyond the search summary): [PostgreSQL 18 Released!](https://www.postgresql.org/about/news/postgresql-18-released-3142/); [PG Release 18 notes](https://www.postgresql.org/docs/current/release-18.html); [MySQL 26.7 1.3 MySQL Releases: Innovation and LTS](https://dev.mysql.com/doc/refman/26.7/en/mysql-releases.html); [Oracle blog: MySQL 9.7.0 LTS Is Now Available](https://blogs.oracle.com/mysql/mysql-9-7-0-lts-is-now-available-expanded-community-capabilities-and-dynamic-data-masking-for-enterprise); [Oracle blog: MySQL July 2026 GA Releases](https://blogs.oracle.com/mysql/mysql-july-2026-ga-releases-now-available); [MySQL 9.7.0 release notes](https://dev.mysql.com/doc/relnotes/mysql/9.7/en/news-9-7-0.html). Failed fetch: https://www.postgresql.org/about/news/ (HTTP 404).
