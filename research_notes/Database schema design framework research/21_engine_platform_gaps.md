# 21. Engine and platform gaps (official documentation)

Research only. No framework rules or schemas. Accessed 2026-11-08. Catalog: `catalog_21_engine_gaps.json` (ENG-01 to ENG-30).

## Method and evidence limits

- **Label meaning.** MANDATORY = the engine enforces it, or the docs state a hard limit. RECOMMENDED = the vendor advises it. OPTIONAL/CONTEXTUAL = a choice that depends on workload. Labels describe how strongly the docs state something. They are not framework requirements.
- **Quotation marks** appear only around text extracted directly with curl (PostgreSQL, MongoDB, Snowflake, Redshift, DynamoDB, Databricks). All other findings are paraphrased from WebFetch model output and carry the tag [WF].
- **Access.** `dev.mysql.com` returned an Akamai 403 to curl, so all MySQL findings are [WF]. I did not try to work around the block with curl. Curl failed locally (libcurl error 43) for learn.microsoft.com, docs.oracle.com, cloud.google.com and jboss.org, so those are [WF] too. Re-check [WF] numbers against the page before relying on them, especially the MySQL DDL matrix.
- **Versions.** Each finding records what the page reported. `/current/` PostgreSQL pages reported 18. MySQL pages are the 8.4 manual; 9.x was not surveyed.

## 1. MySQL online DDL (MySQL 8.4) [WF] - ENG-01

| Operation | Instant | In place | Rebuild | Concurrent DML |
|---|---|---|---|---|
| Add column | Yes* | Yes | No* | Yes* |
| Drop column | Yes* | Yes | Yes | Yes |
| Rename column | Yes* | Yes | No | Yes* |
| Reorder columns | No | Yes | Yes | Yes |
| Set or drop default | Yes | Yes | No | Yes |
| Change data type | No | No | Yes | No |
| Extend VARCHAR | No | Yes | No | Yes |
| Make NULL | No | Yes | Yes* | Yes |
| Make NOT NULL | No | Yes* | Yes* | Yes |
| Modify ENUM/SET | Yes | Yes | No | Yes |
| Add secondary index | No | Yes | No | Yes |
| Drop or rename index | No | Yes | No | Yes |
| Add FULLTEXT | No | Yes* | No* | No |
| Add SPATIAL | No | Yes | No | No |
| Add primary key | No | Yes* | Yes* | Yes |
| Drop primary key alone | No | No | Yes | No |
| Drop and add primary key | No | Yes | Yes | Yes |
| Add foreign key | No | Yes* | No | Yes |
| Drop foreign key | No | Yes | No | Yes |
| Add STORED generated | No | No | Yes | No |
| Add VIRTUAL generated | Yes | Yes | No | Yes |
| Drop VIRTUAL generated | Yes | Yes | No | Yes |

* = the manual attaches conditions.

- MANDATORY (OLTP, MySQL): in-place FK addition requires `foreign_key_checks` disabled; otherwise only COPY is supported.
- MANDATORY (OLTP, MySQL): in-place VARCHAR extension cannot cross the 255/256-byte boundary. Shrinking requires COPY.
- MANDATORY (OLTP, MySQL): INSTANT is limited to 64 row versions per table. The page also cites 255 as of 9.1.0. A rebuild resets the counter. Not supported for ROW_FORMAT=COMPRESSED, tables with FULLTEXT, data dictionary tablespace tables or temporary tables.
- CONTEXTUAL (OLTP, MySQL): INSTANT is the default for ADD and DROP COLUMN in 8.4.
- RECOMMENDED (OLTP, MySQL): define the primary key in CREATE TABLE where possible, because redefining it copies the data.

## 2. Replication lag and read-your-writes

### MySQL 8.4 [WF] - ENG-02
- CONTEXTUAL (OLTP): Seconds_Behind_Source is an approximation. It is stated to be unreliable on slow networks, can show 0 while the replica is behind, depends on clock stability, can fluctuate in chained topologies with direct writes, and on multithreaded replicas may not reflect the latest commit.
- CONTEXTUAL (OLTP): `WAIT_FOR_EXECUTED_GTID_SET(gtid_set[, timeout])` blocks until the set is applied. It returns 0 on success and 1 on timeout. The default timeout of 0 waits indefinitely. This is the documented primitive for waiting on a known write.
- MANDATORY (OLTP): semisynchronous replication waits for receipt and relay-log flush on a replica, not for apply. It does not make a write visible on replicas.
- CONTEXTUAL (OLTP, Group Replication): `group_replication_consistency` has the values EVENTUAL, BEFORE_ON_PRIMARY_FAILOVER, BEFORE, AFTER and BEFORE_AND_AFTER, settable per session or globally. The system variables page gives the default as BEFORE_ON_PRIMARY_FAILOVER. AFTER makes later transactions on any member read the value or newer, at a latency cost.

### PostgreSQL 18 - ENG-07
- MANDATORY (OLTP): "PostgreSQL streaming replication is asynchronous by default."
- MANDATORY (OLTP): hot standby data is described as lagging: "We say that data on the standby is eventually consistent with the primary."
- CONTEXTUAL (OLTP): "Setting synchronous_commit to remote_apply will cause each commit to wait until the current synchronous standbys report that they have replayed the transaction, making it visible to user queries. In simple cases, this allows for load balancing with causal consistency."
- CONTEXTUAL (OLTP): remote_apply "will cause much larger commit delays than previous settings since it waits for WAL replay."
- CONTEXTUAL (OLTP): cascading replication is asynchronous, and synchronous settings do not apply to it. Long standby queries interact with `max_standby_streaming_delay`.
- CONTEXTUAL: `pg_stat_replication` exposes write_lag, flush_lag and replay_lag.

### SQL Server (2017 to 2025 applies-to) [WF] - ENG-12
- MANDATORY (OLTP): a change is visible on a readable secondary only after its log record is applied, even in synchronous-commit mode, because synchronous commit waits on log hardening rather than redo.
- RECOMMENDED (OLTP): where data latency is unacceptable, the page advises running read workloads on the primary.

## 3. Foreign keys and partitioned tables

- MANDATORY (OLTP/general, MySQL 8.4) [WF] ENG-03: partitioned InnoDB tables support neither side of a foreign key. A partitioned table cannot declare FKs and cannot be referenced by one.
- CONTEXTUAL (OLTP/general, PostgreSQL) ENG-08: PostgreSQL 12 release notes (2019-10-03): "Allow foreign keys to reference partitioned tables".
- MANDATORY (PostgreSQL 18) ENG-08: a unique or primary key on a partitioned table must include all partition key columns and no expressions: "the constraint's columns must include all of the partition key columns." A referenced key on a partitioned parent is therefore constrained in the same way (inference from the two statements).
- CONTEXTUAL (PostgreSQL 18): detaching a partition takes a "SHARE lock" on tables that reference the partitioned table through foreign keys.

## 4. Date and time

### SQL Server [WF] - ENG-09
- RECOMMENDED: avoid `datetime` for new work. Use time, date, datetime2 or datetimeoffset.
- MANDATORY: `datetime` rounds to increments of .000, .003 or .007 seconds, ranges from 1753-01-01, and is not ANSI or ISO 8601 compliant.
- MANDATORY: `datetime2` ranges from 0001 to 9999 at up to 100 ns, with no offset and no DST awareness.
- MANDATORY: `datetimeoffset` stores and compares in UTC and preserves the offset for retrieval, with offsets from -14:00 to +14:00.
- CONTEXTUAL: under compatibility level 130 and above, implicit datetime to datetime2 conversion accounts for fractional milliseconds. The page advises explicit casts in mixed comparisons.
- CONTEXTUAL: Fabric Data Warehouse cannot create datetimeoffset columns.

### MySQL 8.4 [WF] - ENG-04
- MANDATORY: TIMESTAMP converts session time zone to UTC on store and back on retrieve. Range is 1970 to 2038-01-19 UTC. DATETIME is not converted and is stored as written.
- CONTEXTUAL: a changed session time zone changes the TIMESTAMP value returned. Both types accept up to 6 fractional digits.

### MongoDB 9.0 selector - ENG-13
- MANDATORY: "BSON Date is a 64-bit integer that represents the number of milliseconds since the Unix epoch (Jan 1, 1970)."
- RECOMMENDED: "The BSON timestamp type is for internal MongoDB use. For most cases, in application development, use the BSON date type."
- CONTEXTUAL: "MongoDB stores times in UTC by default, and converts any local time representations into this form." The same page shows storing a separate offset to reconstruct local time.

## 5. NULL in UNIQUE constraints

| Engine | Behaviour | Label |
|---|---|---|
| SQL Server [WF] ENG-10 | Only one NULL allowed per column in a UNIQUE constraint | MANDATORY |
| MySQL 8.4 [WF] ENG-05 | UNIQUE index permits multiple NULLs | MANDATORY |
| Oracle (page reports 26) [WF] ENG-15 | A row with NULLs in all key columns satisfies the constraint. Two rows with NULLs in some key columns and the same values in the others violate it. | MANDATORY |

- CONTEXTUAL (SQL Server) [WF]: filters cannot apply to UNIQUE constraints but can apply to indexes with the UNIQUE property. The page shows a non-unique `WHERE col IS NOT NULL` example. A unique filtered index that tolerates many NULLs is an inference from those statements, not a documented example in the page read.

## 6. SQL Server deferrable constraints [WF] - ENG-10

- MANDATORY (OLTP): the CREATE TABLE page, read in full, shows no DEFERRABLE, INITIALLY DEFERRED or deferred-checking syntax. Absence from the grammar is the evidence; no statement of non-support was located.
- CONTEXTUAL: NOT FOR REPLICATION exempts FK and CHECK constraints during replication agent operations.
- Contrast (Oracle, ENG-15): DEFERRABLE is supported, NOT DEFERRABLE is the default, deferrability cannot be altered in place, and the optimizer does not treat indexes on deferrable constraints as usable.

## 7. MySQL row and column access [WF] - ENG-06

- MANDATORY (MySQL 8.4): column privileges cover INSERT, REFERENCES, SELECT and UPDATE, with the syntax `GRANT SELECT (col1) ON ...`.
- MANDATORY: the GRANT page lists global, database, table, column and routine levels and does not mention row-level privileges.
- RECOMMENDED: use SQL SECURITY INVOKER when possible. Definer-context objects can reach data the invoker has no privileges for.
- CONTEXTUAL: Enterprise Data Masking is a commercial MySQL Enterprise feature for transforming, generating or substituting data. The page does not present it as row or column access control.
- Gap: the docs read do not present views as a row-filtering security mechanism.

## 8. Auditing

- Oracle Unified Auditing (page reports 26ai) [WF] ENG-16: traditional auditing is desupported starting in 26ai, and existing settings keep working but cannot be created or updated. RECOMMENDED: unified auditing, a separate tablespace for the trail, and migrating traditional settings. MANDATORY: mandatory audits cannot be disabled. The trail table `AUD$UNIFIED` allows only inserts. Roles are AUDIT_ADMIN and AUDIT_VIEWER.
- MongoDB ENG-14: "MongoDB Enterprise includes an auditing facility for mongod and mongos instances in self-managed deployments." MANDATORY: Enterprise only for self-managed; "MongoDB Atlas supports auditing for M10 and larger clusters." Destinations are console, syslog, JSON file or BSON file.

## 9. Backup and high availability

- Oracle ARCHIVELOG (page reports 26) [WF] ENG-17: RECOMMENDED where no data loss from disk failure is acceptable. NOARCHIVELOG restores only to the last whole closed backup and permits no online backups. MANDATORY: backups taken in NOARCHIVELOG are unusable after switching to ARCHIVELOG, so take a new backup.
- RMAN (page reports 26ai) [WF] ENG-17: `BACKUP DATABASE PLUS ARCHIVELOG` works on an open ARCHIVELOG database. NOARCHIVELOG requires a consistent, mounted backup. The fast recovery area is set through DB_RECOVERY_FILE_DEST.
- Oracle Data Guard (page reports 26) [WF] ENG-18: Maximum Performance is the default (asynchronous, possible loss). Maximum Availability is synchronous and falls back to Performance behaviour without a synchronized standby. Maximum Protection shuts the primary down rather than run unprotected. RECOMMENDED: at least two standbys for Maximum Protection. Active Data Guard is a licensed option.
- SQL Server Always On [WF] ENG-12: one primary, up to eight secondaries, up to five synchronous replicas including the primary. Asynchronous-commit allows only forced failover, with possible data loss. RECOMMENDED: secondaries are not backups, so continue backups and log backups. A timed-out synchronous secondary stops holding up commits.

## 10. Default isolation and consistency

| Platform | Default documented | Evidence |
|---|---|---|
| Snowflake (tables) | READ COMMITTED: "READ COMMITTED is the only isolation level currently supported for tables." | ENG-19 |
| BigQuery | Multi-statement transactions use snapshot isolation [WF]; no alternative level described | ENG-21 |
| Redshift | "SNAPSHOT isolation is the default isolation level when creating provisioned clusters and serverless workgroups" | ENG-22 |
| Spanner | Serializable is the default; repeatable read also offered [WF] | ENG-24 |
| DynamoDB | "Eventually consistent is the default read consistent model for all read operations." | ENG-25 |
| Cosmos DB | No product-wide default named on the page read; the default level is set per account [WF] | ENG-26 |

- MANDATORY (DynamoDB): "All reads from GSIs and streams are eventually consistent."
- CONTEXTUAL (Cosmos DB) [WF]: session consistency gives read-your-writes within a session or with a shared session token. Tokens are partition-bound. Strong is unavailable with multiple write regions.
- CONTEXTUAL (BigQuery) [WF]: conflicting mutating transactions fail immediately rather than queue. Limits are 100 tables and 100,000 partition modifications per transaction.

## 11. Redshift constraints - ENG-23

- MANDATORY (data_warehouse): "Uniqueness, primary key, and foreign key constraints are informational only; they are not enforced by Amazon Redshift when you populate a table."
- MANDATORY: "Amazon Redshift does enforce NOT NULL column constraints."
- RECOMMENDED: "Do not define key constraints for your tables if you doubt their validity." Invalid keys can produce incorrect results, because the planner assumes keys are valid.

## 12. Identifiers

- Snowflake ENG-20, MANDATORY: "Regardless of whether an identifier is unquoted or double-quoted, the maximum number of characters allowed is 255 (including blank spaces)." Unquoted identifiers: "stored and resolved in uppercase". Quoted identifiers are case-sensitive.
- Databricks ENG-30, MANDATORY (Unity Catalog): "Object names cannot exceed 255 characters." "Identifiers are case-insensitive when referenced." Hive metastore schema and table names are limited to alphanumeric ASCII and underscores.

## 13. Databricks current status (release notes through November 2026)

- Multi-statement transactions ENG-27: Public Preview noted in March 2026. July 2026: "Transactions that write to Unity Catalog managed Delta tables are now generally available." October 2026 extends GA to managed Apache Iceberg tables. MANDATORY: requires Unity Catalog managed tables with catalog commits; DDL is not allowed inside transactions; a transaction can touch at most 100 tables and 100 views; interactive transactions roll back after 10 minutes idle. Non-interactive transactions need DBR 18.0+ on clusters.
- Metric Views ENG-28: "Metric views are in Public Preview" (May 2025). I found **no** release note declaring metric views as a whole GA. The current page (updated 2026-10-29) carries no preview label on metric views overall. Sub-features differ: window measures GA (October 2026), sharing with OpenSharing GA (September 2026), parameters Public Preview (June 2026), relationships Beta. Status of the core feature is unresolved.
- RELY ENG-29: "The default is NORELY." Supported from DBR 14.2 (PK), 15.4 (FK) and 18.2 (UNIQUE) per the constraint page, and requires pro or serverless SQL warehouses or serverless compute. No preview label on the page. MANDATORY caution: "Relying on a constraint that is not satisfied may lead to incorrect query results." "It is the user's responsibility to check whether a constraint is satisfied."

## 14. Hibernate Envers ValidityAuditStrategy [WF] - ENG-11

- CONTEXTUAL (OLTP): the default strategy stores only a start revision, and its queries rely on subqueries the docs describe as slow and hard to index.
- CONTEXTUAL (OLTP): ValidityAuditStrategy stores start and end revisions and updates the previous row's end revision. Reads are faster; writes are slower. `REVEND` holds the end revision, with an FK to REVINFO.
- CONTEXTUAL: configured via `org.hibernate.envers.audit_strategy`. The docs frame this as a trade-off, with no universal recommendation. Partitioning by end revision needs the validity strategy.
- Source caveat: read from the `main` branch of the official Hibernate repository. The published 7.4.15.Final guide was opened, but the text returned stopped before the Envers chapter.

## Conflicts

1. SQL Server `datetimeoffset`: the property table says daylight saving aware = No, while the prose says the offset is assumed DST aware. [WF] Treat the type as storing a fixed offset; confirm with `AT TIME ZONE`, whose own page was not opened.
2. Redshift calls both SNAPSHOT and SERIALIZABLE "serializable isolation levels", yet the same page says only SERIALIZABLE prevents write-skew anomalies.
3. MySQL Group Replication: the consistency guarantees page does not state the default and describes EVENTUAL as the historic behaviour. The variables page gives BEFORE_ON_PRIMARY_FAILOVER. The variables page is used here.
4. Metric Views: last release-note status for the whole feature is Public Preview, but the current page has no preview label.
5. NULL in UNIQUE differs across SQL Server (one), MySQL (many) and Oracle (composite-specific rule), so a portable uniqueness rule cannot assume one behaviour.

## Unresolved gaps

- MySQL has no page read that uses the term read-your-writes or gives prescriptive guidance. Only mechanisms were found.
- Native MySQL row-level security: none found in pages read. This is absence of evidence from those pages, not a statement of non-support.
- SQL Server: no explicit statement that deferrable constraints are unsupported, and no explicit unique filtered index example for NULLs. `CREATE INDEX` was not opened.
- PostgreSQL: whether a partitioned table can hold FKs (child side) was not confirmed in current docs. Only the referenced side is confirmed, from version 12 notes.
- Cosmos DB account creation default is not named on the page read.
- Snowflake hybrid table isolation was not established beyond row-level locking text.
- DynamoDB transactional isolation was not read.
- Oracle pages: release is inferred by WebFetch from page metadata and links. All /23/ URLs reported 26 or 26ai.
- Databricks column-name length limit not confirmed separately from the 255-character object name limit.
- Not opened: MySQL time zone page and `create-table-foreign-keys`, SQL Server `AT TIME ZONE`, Spanner transactions overview.
