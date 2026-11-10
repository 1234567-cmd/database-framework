# Industry Best Practices from Production Systems and Canonical Literature
Research deliverable for the Database Schema Design and Data Engineering Standards Framework (ERP, financial, SaaS, data engineering). Research only: this file proposes no schema and no implementation.

Sources: topic notes 13, 14, 16 and 17, as overridden by `CORRECTIONS.md`; notes 18 (ERP and finance), 19 (legal retention and numbering) and 22 (evidence verification of 2026-11-08, with `verification_results.json`). Where note 22 tested an item, its result overrides `CORRECTIONS.md` and the earlier notes for that item. No web research was done and no source outside the notes was added. Catalog IDs refer to `resource_catalog.json`; where a note's resource has no catalog entry, the citation says so.

## 0. How to read this file
**Quotation policy.** Web pages read through a summarizing fetch tool are paraphrased here, even where the topic notes used quotation marks. Quotation marks enclose only raw-extracted text: the Pinterest QCon 2012 slides (CASE-05, PDF-extracted); text notes 18 and 19 record as extracted with curl or pdftotext (German statutes, 15 USC 78m, 17 CFR 240.13b2-1, ERPNext pages, the IAS 21 summary page, FAS 52, the SEC Baxter order, the PCAOB Audit Focus, Oracle's Using General Ledger PDF, and the legal texts note 19 quotes); and excerpts note 22 took from the served page. Vendor identifiers in backticks from note 18 came through the fetch tool.

**Legal status.** Everything here on law, tax or accounting standards is research input, not legal advice, and needs review by counsel before it is relied on.

**Practice labels.** These are candidate labels for the later framework.

| Label | Test applied here |
|---|---|
| MANDATORY | Legal text, an engine-documented fact, or an invariant on which at least two independent organizations or canonical works converge. The scope is always stated. |
| RECOMMENDED | Repeated across cases but with real exceptions, or reasoned from strong evidence that does not cover every context. |
| OPTIONAL/CONTEXTUAL | Depends on scale, engine or domain, or rests on one organization. |

A single company's practice is evidence for context, not a universal rule. Where one company is the only source, the text says so, and the practice cannot rise above OPTIONAL/CONTEXTUAL unless an engine fact or a law supports it.

**Evidence grades.**

| Grade | Meaning |
|---|---|
| A | Verified case: official engineering post, postmortem or slide deck, fetched and read, describing a production decision and outcome. |
| B | Verified official documentation or repository: design or rules, with no independently reported outcome. |
| C | Verified practitioner, community or individual-author source. |
| L | Literature entry, verified to the level stated in section 11. |
| U | Unverified snippet: search excerpt only, never opened. |
| I | Inference drawn in these notes; no source states it. |

**Limits that apply to every case.**
- Outcome figures are self-reported by the operating company. None was independently audited.
- 47 of the 53 resources catalogued for topic 17 were fetched. Six are search-only and unverified: the Pinterest Medium post (CASE-06), Instagram Sharding & IDs (CASE-20), and four Airbnb posts (CASE-35, CASE-36, CASE-39, CASE-40).
- Note 22 did not re-read the Uber posts (CASE-09, CASE-10, CASE-30, CASE-38): the catalog records refusal of automated access on that host, so their links need a manual check by the owner. Content reported from them stands as first read.
- Survivorship bias: engineering blogs report systems that worked. Only the two postmortems in section 9 document failure directly.
- Scope tags: OLTP, OLAP, or OLTP+OLAP. The case base is heavily OLTP. Note 18's finer scopes are kept in brackets where they matter, mapped here as GL and SUB (general ledger and subledgers) to OLTP, CONS (consolidation) to OLTP+OLAP, and DW (reporting or warehouse copies) to OLAP.
- Where the notes give no alternative, the case says so instead of supplying one.

## 1. Main findings
1. Relational operators repeatedly chose a tenant-like sharding key that keeps most joins and transactions local (Figma, Notion, Slack, Shopify; Citus documents the same pattern). Grade A.
2. Logical shards outnumbering physical hosts made re-sharding routine at Notion and made capacity additions possible without moving data at Pinterest. Grade A.
3. Large migrations pair incremental copy with a read-comparison check before cutover (Notion, Slack, Discord, Stripe, GitHub). Grade A.
4. Expand, migrate, contract is the shared shape of safe schema change from the literature through operator rulebooks. Grades A, B, L.
5. Stripe, Square and Modern Treasury describe balanced, append-only ledgers with correction by new entry, consistent with Fowler and Kleppmann. This is the strongest convergence on financial correctness, though Uber's LedgerStore evidence in the notes covers indexing only.
6. Fiscal period close, multi-currency and multi-company now have vendor and standard-setter evidence (section 5). Vendors disagree on material points: reversing a reversal, permanent close, and deleting generated vouchers. Rate precision and triangulation remain unsupported.
6a. A single invoice-gap rule cannot be derived. France has the strictest wording found, the UK the clearest tolerance of gaps, and the German no-gap reading rests on search snippets only (section 5).
7. Both postmortems were recovery-design failures: unverified backups (GitLab) and promotion across regions that produced divergent writes (GitHub).
8. Two debates stay open: Uber against the PostgreSQL community, and dropping foreign keys at scale. The notes support scoped conclusions, not a verdict.

## 2. Scaling and sharding
### Cases
#### S1. Figma: horizontal sharding of RDS Postgres (OLTP, grade A)
Source: [How Figma's databases team lived to tell the scale](https://www.figma.com/blog/how-figmas-databases-team-lived-to-tell-the-scale/) (2024-03-14; CASE-01).
- Problem: the stack grew almost 100x from 2020 to 2024. Some tables reached several TB and billions of rows, vacuum hurt reliability, and the highest-write tables neared the RDS IOPS limit. Vertical partitioning was exhausted because one table is its smallest unit.
- Decision: horizontal sharding over the existing fleet. *Colos* group related tables sharing a sharding key (UserID, FileID, OrgID) so joins and transactions stay possible within a key. Routing hashes the key to avoid hotspots from sequential IDs. Logical sharding through views came first and physical sharding later. A Go proxy (DBProxy) plans queries. There are no atomic cross-shard transactions. The supported query subset, roughly the most common 90%, was chosen by shadow planning on live traffic.
- Alternatives rejected: CockroachDB, TiDB, Spanner, Vitess (migration complexity and lost Postgres expertise, too risky given months of runway); NoSQL (backend rewrite).
- Outcome: first sharded table shipped September 2023, about nine months end to end. Failover caused about 10 seconds of partial primary unavailability. View overhead was under 10% in the worst case.
- Transferable lesson: take reversible steps, and fit the sharding layer to your own query mix instead of building a general database.
#### S2. Notion: application-level sharding by workspace (OLTP, grade A)
Source: [Herding elephants: Lessons learned from sharding Postgres at Notion](https://www.notion.com/blog/sharding-postgres-at-notion) (2021-10-06; CASE-02).
- Problem: one Postgres monolith after about five years and four orders of magnitude of growth. Autovacuum stalled and transaction-ID wraparound became an existential risk.
- Decision: workspace ID as partition key; every table reachable from `block` through foreign keys is sharded; 480 logical shards (Postgres schemas) on 32 physical databases. 480 was chosen because its many factors allow growth from 32 to 40 to 48 hosts, where 512 would force 64.
- Alternatives rejected: vertical scaling; Citus and Vitess (clustering logic too opaque); DynamoDB (too risky); bare-metal NVMe (backup and replication maintenance). Native partitioning was passed over to keep one routing source in the application.
- Migration: direct dual writes proved too flaky and logical replication could not keep up with `block` during the snapshot, so writes were replayed from an audit log. Backfill took about 3 days. Verification sampled UUIDs and used dark reads, and migration and verification logic had different authors.
- Outcome: five minutes of scheduled maintenance at switchover.
- Transferable lesson: shard before headroom runs out, and merge the old primary key with the partition key so the tenant key need not be threaded through the application.
#### S3. Notion: re-sharding from 32 to 96 databases (OLTP, grade A)
Source: [The Great Re-shard: adding Postgres capacity (again) with zero downtime](https://www.notion.com/blog/the-great-re-shard) (2023-07-17; CASE-03).
- Problem: by late 2022 some shards exceeded 90% peak CPU, many neared provisioned IOPS, and PgBouncer hit connection limits. Decision: triple the fleet, using logical replication. Deferring index creation cut sync from 3 days to 12 hours. PgBouncer was regrouped because about 100 instances at 6 connections each meant about 600 connections per shard. Dark reads compared results on a sample. A four-step failover, including reverse replication for rollback, was rehearsed in staging.
- Alternatives rejected: vertical scaling (same limits, no per-shard sizing).
- Outcome: Notion reports no perceived downtime, about 1 second of spinner at worst, and peak CPU and IOPS near 20%.
- Transferable lesson: the connection pool is its own scaling dimension. Re-sharding is repeatable when logical shards outnumber hosts.
#### S4. GitHub: schema domains, then Vitess (OLTP, grade A)
Source: [Partitioning GitHub's relational databases to scale](https://github.blog/2021-09-27-partitioning-githubs-relational-databases-scale/) (2021-09-27, updated 2022-03-02; CASE-04).
- Problem: core features shared one MySQL cluster (`mysql1`), so any incident there affected them all. Decision: declare schema domains in a file with a linter requiring every table to belong to one; flag cross-domain joins with a query linter; catch cross-domain transactions with a sampled production linter; move whole domains with Vitess VReplication, plus an in-house cutover as a second tool.
- Alternatives considered: application-side joins behind Scientist experiments; Rails `disable_joins`; moving polymorphic data into same-domain tables; Vitess against in-house cutover.
- Outcome: 950K queries/s on `mysql1` in 2019; 1.2M across clusters in 2021 with per-host load halved. One cutover moved 130 busy tables in tens of milliseconds.
- Transferable lesson: enforce boundaries with linters before moving data.
#### S5. Pinterest: manual ID sharding on MySQL (OLTP, grade A for the 2012 slides)
Source: [Scaling Pinterest (QCon SF 2012 slides)](https://qconsf.com/sf2012/dl/qcon-sanfran-2012/slides/MartyWeiner_and_YashwanthNelapati_ScalingPinterest.pdf) (2012-11-09; CASE-05, PDF-extracted). The 2015 recap [Sharding Pinterest: How we scaled our MySQL fleet](https://medium.com/pinterest-engineering/sharding-pinterest-how-we-scaled-our-mysql-fleet-3f341e96ca6f) (n.d.; CASE-06) is **unverified** (grade U) and adds nothing relied on here.
- Problem: in January 2012 a three-engineer team ran MySQL, Cassandra, Membase and Mongo clusters together. The slides' first lesson: "It will fail. Keep it simple."
- Decision: sharding over clustering; 8 servers holding 512 databases each (4096 shards); a static lookup map; objects stored as blobs; `noun_verb_noun` mapping tables. Slide wording: "Queries are PK or index lookups (no joins)". Capacity is added by replicating a server and handing over half its databases: "Data DOES NOT MOVE".
- Alternatives rejected: clustering (Cassandra, Membase, HBase), judged young and complicated. Slide wording: "Clustering is scary."
- Costs the slides list: "Cannot perform most JOINS", "No transaction capabilities", "Extra effort to maintain unique constraints", "Reports require running same query on all shards".
- Outcome: October 2012: 80 MySQL databases with one replica each; 500M pins and 1.6B follower rows migrated.
- Transferable lesson: a static map trades joins, transactions and uniqueness for operational predictability. The verdict on clustering is time-bound (see 10.3).
#### S6. Slack: Vitess over workspace-sharded MySQL (OLTP, grade A)
Source: [Scaling Datastores at Slack with Vitess](https://slack.engineering/scaling-datastores-at-slack-with-vitess/) (2020-12-01; CASE-07).
- Problem: workspace-based shards produced hot spots beside idle hosts, and a shard outage took down every workspace on it. Decision: adopt Vitess, with a sharding key chosen per keyspace (messages by channel so one huge customer does not sit on one shard). Migration used backfill, double writes and double reads.
- Alternatives rejected: application-level sharding (prototypes coupled application logic to storage layout); DynamoDB, Cassandra, Spanner, CockroachDB (too disruptive).
- Outcome: 99% of MySQL load on Vitess; 2.3M QPS peak; median 2 ms, p99 11 ms; absorbed 50% more QPS in one week of March 2020.
- Transferable lesson: the per-table sharding key is the central design decision. Adopting middleware also means rebuilding provisioning, discovery and backup processes.
#### S7. Shopify: pods as the unit of isolation (OLTP, grade A)
Source: [A Pods Architecture To Allow Shopify To Scale](https://shopify.engineering/a-pods-architecture-to-allow-shopify-to-scale) (2018-03-02; CASE-08).
- Problem: after sharding in 2015, shared code acting across shards meant one failed shard could disable an action platform-wide. Decision: a pod is a group of shops on fully isolated datastores. Requests are bound to one pod and no action crosses pods. Each pod has an active and a recovery data center.
- Alternatives: not stated in the notes. Outcome: qualitative only. Pod Mover relocates a pod in about a minute and is used daily.
- Transferable lesson: sharding for capacity differs from isolating for resilience.
#### S8. Discord: MongoDB to Cassandra to ScyllaDB (OLTP, wide-column, grade A)
Sources: [How Discord Stores Billions of Messages](https://discord.com/blog/how-discord-stores-billions-of-messages) (2017-01-13; CASE-15); [How Discord Stores Trillions of Messages](https://discord.com/blog/how-discord-stores-trillions-of-messages) (2023-03-06; CASE-16).
- Problem: in 2015 MongoDB data and index outgrew RAM at about 100M messages. By 2023, 177 Cassandra nodes suffered hot partitions, GC pauses and compaction backlog.
- Decision: partition on channel plus a roughly 10-day bucket to keep partitions under 100 MB, cluster on a time-sortable Snowflake message ID. In 2023 move to ScyllaDB and add Rust data services that coalesce concurrent requests and route by channel.
- Alternatives rejected: MongoDB sharding (complicated, unstable).
- Problems found: null writes created needless tombstones, and one heavily deleted channel took 20 seconds to load. Discord's remedy, in the source's words: "We lowered the lifespan of tombstones from 10 days down to 2 days" (CASE-15, confirmed in note 22). The parameter name used in the earlier note is not on the page and is not used.
- Outcome: 177 to 72 nodes; historical read p99 from 40-125 ms to about 15 ms. A Rust migrator took 9 days and stalled at 99.9999% on large tombstone ranges.
- Transferable lesson: bound partition size and hot-key exposure. Deletes in LSM stores are writes. The swap alone did not fix hot partitions; upstream coalescing helped.
#### S9. Facebook TAO (OLTP, grade A at abstract level only)
Source: [TAO: Facebook's Distributed Data Store for the Social Graph](https://www.usenix.org/conference/atc13/technical-sessions/presentation/bronson) (2013; CASE-21).
- Problem and decision: a simple data model and API tailored to the social graph, deployed in place of memcache for data fitting that model.
- Alternatives: not stated on the page read. Outcome: thousands of machines, a billion reads and millions of writes per second.
- Transferable lesson: a deliberately restricted API can enable caching and geo-distribution. Only the abstract page was read, so the storage substrate is not asserted here. Note 22 found neither MySQL nor relational on that page; the paper PDF remains unread.

### Practices

| Practice | Label | Evidence |
|---|---|---|
| Exhaust vertical scaling and functional partitioning first, while leaving headroom for the migration itself | RECOMMENDED | S1, S2, S4, S5 |
| Choose a tenant-like sharding key that keeps most joins and transactions local | RECOMMENDED (MANDATORY once a relational OLTP system is sharded and needs local transactions) | S1, S2, S6, S7, T3 |
| Treat cross-shard atomic transactions as unavailable unless the engine provides them | RECOMMENDED | S1, S7 |
| Make logical shards far more numerous than physical hosts, and pick a count with many factors | RECOMMENDED; the factor argument is Notion's alone | S2, S3, S5 |
| Enforce boundaries with linters before moving data | OPTIONAL/CONTEXTUAL (GitHub only) | S4 |
| Bind each request to one isolation unit | OPTIONAL/CONTEXTUAL (Shopify; extreme end of T1-T3) | S7 |
| Bound partition size and hot-key exposure in wide-column stores | RECOMMENDED for that engine class | S8 |
| Plan the connection-pool layer as part of capacity | RECOMMENDED | S3 and Uber's connection discussion in 10.1 |

### Open build-or-adopt question
Figma, Notion and Pinterest built sharding layers. Slack and GitHub adopted Vitess. All the relational operators above rejected a move to NewSQL or NoSQL as riskier than evolving the incumbent engine, but that reflects each team's runway and expertise. Pavlo and Aslett's [What's Really New with NewSQL?](https://db.cs.cmu.edu/papers/2016/pavlo-newsql-sigmodrec2016.pdf) (2016; LIT-37) gives the vocabulary for the alternative. Label: OPTIONAL/CONTEXTUAL.

## 3. ID generation
#### I1. Flickr ticket servers (OLTP, grade A)
Source: [Ticket Servers: Distributed Unique Primary Keys on the Cheap](https://code.flickr.net/2010/02/08/ticket-servers-distributed-unique-primary-keys-on-the-cheap/) (2010-02-08; CASE-17).
- Problem: keys had to be unique across MySQL master-master shards so records could move without collision. Decision: dedicated sequence servers, two of them splitting odd and even values, with separate sequences per ID type.
- Alternatives rejected: GUIDs (poor MySQL indexing, too large for in-memory indexes); consistent hashing; one central auto-increment database.
- Outcome: in production since January 2006. The two servers drift by a few hundred thousand IDs without harm.
- Transferable lesson: a very small sequence service can give roughly ordered integers. Uniqueness is guaranteed; strict order is not.
#### I2. Twitter Snowflake (OLTP/streaming, grade B)
Sources: [twitter-archive/snowflake](https://github.com/twitter-archive/snowflake) (2010; archived 2021-09-18; CASE-18); [Snowflake README](https://raw.githubusercontent.com/twitter-archive/snowflake/snowflake-2010/README.mkd) (2010; CASE-19).
- Problem: the move from MySQL to Cassandra left no sequential ID facility. Decision: a network service issuing 64-bit IDs: 41 bits of milliseconds from a custom epoch, 10 bits of machine ID, 12 bits of sequence. Generators do not coordinate. IDs are k-sortable. Generation refuses to proceed if the clock moves backward.
- Alternatives: not stated in the notes. Outcome: retired as a release. Discord separately uses a Snowflake message ID (S8).
- Transferable lesson: time in the high bits gives sortability, a generator field gives uniqueness, and clock regression must be handled explicitly.
- Correction: the claim that Snowflake was the template for Instagram, Discord and Pinterest IDs is an unsourced inference and is not made here.
#### I3. Instagram in-database IDs (OLTP, grade U, **UNVERIFIED**)
Source: [Sharding & IDs at Instagram](https://instagram-engineering.com/1cf5a71e5a5c) (n.d.; CASE-20). Never opened; the note 22 retest failed with a connection error and no HTTP exchange, so it needs a manual check.
- **Date conflict.** The earlier late-2011 dating was not found in any source. [RFC 9562](https://www.rfc-editor.org/rfc/rfc9562) (2024-05, confirmed by page metadata in note 22; DES-04) lists reference [ShardingID], "Sharding & IDs at Instagram", December 2012. Because the post itself is unread, the citation stays n.d. and December 2012 is only the RFC's reference date.
- The search excerpt indicates only that the post covers sharding Postgres and generating unique IDs across shards, with a leading timestamp keeping IDs time-sortable.
- Bit layout, PL/pgSQL function and shard counts come from secondary summaries and are unverified.
- Problem, alternatives and outcome cannot be reported. This case supports no practice in this file.
#### I4. Pinterest shard-encoded IDs (OLTP, grade A)
Source: CASE-05 (see S5).
- Problem: locate an object from its ID across thousands of shards. Decision: a 64-bit ID of shard ID, type and local ID, with space for 65,536 shards and local IDs from auto-increment. The ID has **no time component**.
- Alternatives: not stated. Outcome: see S5. Transferable lesson: encoding the logical shard in the ID keeps routing simple and lets shards move between hosts without rewriting keys, at the cost of time-sortability.
#### I5. Keys chosen to avoid hotspots: Square and Figma (OLTP, grade A)
Sources: [Books, an immutable double-entry accounting database service](https://developer.squareup.com/blog/books-an-immutable-double-entry-accounting-database-service/) (2019-10-16; TEN-42); CASE-01.
- Problem: sequential keys concentrate writes in distributed or partitioned storage. Decision: Square uses UUIDs and interleaved tables on Spanner. Figma routes on a hash of the key.
- Alternatives: not stated. Outcome: see L2 and S1. Transferable lesson: key distribution must match how the storage engine places data.

### Practices

| Practice | Label | Evidence |
|---|---|---|
| Choose key shape from the storage engine's placement behavior, and record the reason | MANDATORY for any distributed or sharded design | Contrast of I1 with I5 |
| Do not depend on per-database auto-increment for keys that must be unique across shards | MANDATORY when records can move between shards | I1, I2, I4 |
| Place time in high bits when sortability matters | OPTIONAL/CONTEXTUAL | I2; S8 |
| Encode a logical shard in the ID when routing must work without a directory | OPTIONAL/CONTEXTUAL | I4 |
| Keep integer IDs wide enough from the start; GitLab needs a multi-release process to widen primary keys | RECOMMENDED | M3 |
| Treat ID ordering as approximate unless strict order is guaranteed | RECOMMENDED | I1, I2 |

Correction to the topic notes: they group Snowflake with B-tree locality arguments, but the README's stated context is Cassandra. Only Flickr's GUID objection is directly about B-tree index behavior.

## 4. Schema change at scale
### Foundations
- [Evolutionary Database Design](https://martinfowler.com/articles/evodb.html) (2016-05; OPS-01): versioned, small migrations applied by a tool, with a transition period when old and new access patterns coexist.
- [ParallelChange](https://martinfowler.com/bliki/ParallelChange.html) (2014-05-13; OPS-02): expand, migrate, contract, with the stated cost of carrying two versions and needing discipline to finish.
- [Refactoring Databases](https://www.informit.com/store/refactoring-databases-evolutionary-database-design-9780321293534) (2006-03-03; OPS-03): the catalogue of database refactorings.
- [DORA database change management](https://dora.dev/capabilities/database-change-management/) (n.d.; OPS-15) and [Accelerate](https://itrevolution.com/product/accelerate/) (2018-03-27; LIT-75) tie database change into delivery performance.

### Cases
#### M1. Stripe: online migration of Subscriptions (OLTP, grade A)
Source: [Online migrations at scale](https://stripe.com/blog/online-migrations) (2017-02-02; OPS-06).
- Problem: move hundreds of millions of subscription objects out of the Customer record with the API available and consistent. Decision: four phases: dual write and backfill offline; change reads, comparing both paths with Scientist; change writes, new store first; remove old data lazily.
- Alternatives: not stated in the notes. Outcome: the new table became the source of truth. A batch job confirmed no subscription was missing.
- Transferable lesson: phase the work, verify heavily offline, keep each code change to a few hundred lines, and make each step observable.
#### M2. gh-ost and pt-online-schema-change (OLTP, MySQL, grade B)
Sources: [github/gh-ost](https://github.com/github/gh-ost) (n.d.; CASE-23); [pt-online-schema-change docs](https://docs.percona.com/percona-toolkit/pt-online-schema-change.html) (n.d., v3.7.2; no catalog ID).
- Problem: altering large MySQL tables without blocking writes. Decision: gh-ost copies to a ghost table and follows the binary log. pt-osc copies in chunks and syncs with triggers.
- Alternatives: each is the other's alternative. gh-ost's README treats triggers as a source of risk; pt-osc cannot run on tables that already have triggers without restrictions.
- Outcome: no independent outcome data in the notes. The 2016 announcement post was not fetched.
- Transferable lesson: pausable, testable change capture lowers risk. pt-osc's documentation also warns about foreign keys and silent data loss on unique-index changes, so test on non-production and verify backups.
#### M3. GitLab: codified zero-downtime rules (OLTP, grade B)
Sources: [Avoiding downtime in migrations](https://docs.gitlab.com/ee/development/database/avoiding_downtime_in_migrations/) (n.d.; CASE-24); [Migration Style Guide](https://docs.gitlab.com/ee/development/migration_style_guide.html) (n.d.; OPS-04); [NOT NULL constraints](https://docs.gitlab.com/ee/development/database/not_null_constraints.html) (n.d.; no catalog ID). Note 22: the style guide URL now redirects to https://docs.gitlab.com/development/migration_style_guide/, which reads "Your migration must be reversible."
- Problem: migrations must not require installations to go offline. Decision: dropping a column spans three releases. Renames, type changes, and integer-to-bigint primary keys use concurrent helpers across releases. Regular migrations are capped at 3 minutes, post-deployment at 10, concurrent indexes at 20. Statement timeout on GitLab.com is 15 seconds.
- Alternatives: not stated. Outcome: enforced through tooling and review. No outcome figures in the notes.
- Transferable lesson: schema evolution is a release-management process, and application code must tolerate both versions. The numeric limits are GitLab's own and are context, not a universal rule.
#### M4. Braintree: safe and unsafe PostgreSQL operations (OLTP, grade C)
Sources: [Safe Operations For High Volume PostgreSQL](https://pgrs.net/2014/05/14/safe-operations-for-high-volume-postgresql/) (2014-05-14; CASE-27); [Braintree redux gist](https://gist.github.com/jcoleman/1e6ad1bf8de454c166da94b67537758b) (2019-02-01; OPS-07).
- Problem: for a payments API with almost no scheduled downtime, a table lock held more than a few seconds is an outage. Decision: an explicit list of unsafe operations and workarounds. The 2019 notes state "Any exclusive locks acquired on tables or indexes be held for at most ~2 seconds." and "Rollback strategies do not involve reverting the database schema to its previous version." They add "we do not combine multiple DDL statements into a single transaction", require forward and backward compatibility (paraphrase), and list `ALTER TABLE ... ADD FOREIGN KEY ... NOT VALID` (OPS-07; wording per note 22).
- Alternatives: each unsafe operation's workaround, such as concurrent index builds and new-column dual writes.
- Outcome: not quantified.
- Transferable lesson: maintain a per-engine, per-version allow/deny list. The 2019 notes record the PostgreSQL 11 change: "In the recently release PostgreSQL 11, this is no longer the case for non-volatile default values." [sic] (OPS-07, note 22). Rules age.
#### M5. PlanetScale deploy requests (OLTP, grade B)
Sources: [Deploy requests](https://planetscale.com/docs/concepts/deploy-requests) (n.d.; CASE-25); [Safe migrations](https://planetscale.com/docs/concepts/safe-migrations) (n.d.; no catalog ID).
- Problem: schema change needs review and a recovery path. Decision: branch, diff, review, non-blocking copy-and-swap, with a revert window of up to 30 minutes that retains interim writes.
- Alternatives: not stated. Outcome: vendor documentation only. Transferable lesson: treat schema as reviewed code and keep a revert path that preserves interim data.
#### M6. Shopify Ghostferry (OLTP, grade B)
Source: [Shopify/ghostferry](https://github.com/Shopify/ghostferry) (n.d.; CASE-26).
- Problem: move data live between MySQL instances. Decision: a tool inspired by gh-ost that copies across databases and can copy partial datasets.
- Alternatives and outcome: not stated. Transferable lesson: the binlog-copy pattern for schema change also moves tenants between databases.
#### M7. strong_migrations (OLTP, grade B)
Source: [ankane/strong_migrations](https://github.com/ankane/strong_migrations) (n.d.; OPS-08).
- Problem: developers can ship locking DDL unknowingly. Decision: default-fail checks with suggested alternatives, plus guidance to set a short lock timeout (example value 10 seconds).
- Alternatives and outcome: not stated. Transferable lesson: encode the danger list in tooling.

### Engine facts behind the rules
- [PostgreSQL ALTER TABLE](https://www.postgresql.org/docs/current/sql-altertable.html) (n.d., v18.6; OPS-09): `NOT VALID` skips the scan and later validation takes a weaker lock. Most other forms take the strongest lock. Non-volatile defaults avoid a rewrite; volatile defaults do not.
- [PostgreSQL CREATE INDEX](https://www.postgresql.org/docs/current/sql-createindex.html) (n.d., v18.6; PERF-10): a normal build blocks writes; `CONCURRENTLY` takes longer and can leave an invalid index that must be dropped and retried.
- Correction: `CORRECTIONS.md` says no fetched page supports topic 17's summary lesson on `NOT VALID`. Note 22 found that Braintree 2019 (OPS-07, case M4) does, so that restriction is lifted for M4. OPS-09 documents the engine behavior.

### Practices

| Practice | Label | Evidence |
|---|---|---|
| Keep every schema change in version-controlled, tool-applied migrations | MANDATORY | OPS-01, OPS-15, M3 |
| Make each change deployable while the previous application version runs; use expand, migrate, contract for incompatible changes | MANDATORY for zero-downtime services | OPS-02, M1, M3, M4 |
| Budget lock-hold time and total runtime separately; set a lock timeout | MANDATORY in principle. Values are contextual: about 2 s Braintree, 10 s strong_migrations example, 15 s GitLab statement timeout | M3, M4, M7 |
| Separate backfill from DDL transactions; batch and throttle | MANDATORY for large tables | M3, M7 |
| Tie danger lists to engine and version | RECOMMENDED | M4, OPS-09 |
| Verify with a comparison harness or dark reads before cutover | RECOMMENDED; effectively required for store-to-store migrations | M1, S2, S3, S6, S8 |
| Lint DDL in CI against the danger list | RECOMMENDED | M3, M7 |
| Use binlog-based or platform-managed online change on large MySQL tables | OPTIONAL/CONTEXTUAL | M2, M5 |

### Disagreements in the notes
- **Reversibility.** GitLab requires reversible migrations, while Braintree's rollbacks do not revert schema. These reconcile if `down` scripts exist for emergencies and deployment safety comes from expand and contract (inference in topic 13). Treat forward-only compatibility as the safety mechanism.
- **Triggers or binlog.** See M2. Depends on engine and on existing triggers.
- **Data in migrations.** GitLab allows batched background migrations, and Stripe backfilled offline. All agree data work should not hold DDL locks.

## 5. Ledgers and financial correctness
### Cases
#### L1. Stripe Ledger (OLTP+OLAP, grade A)
Source: [Ledger: Stripe's system for tracking and validating money movement](https://stripe.dev/blog/ledger-stripe-system-for-tracking-and-validating-money-movement) (2024-02-16; TEN-43).
- Problem: prove to internal users and auditors that many partner systems, with different formats and cadences, model financials correctly.
- Decision: an immutable, auditable log and system of record using double-entry. Producer systems are modelled as state machines and fund flows. A non-zero clearing balance at steady state signals a missing or wrong event. Each flow is scored on clearing, timeliness and completeness. Corrections are a reviewed revert-and-reprocess operation.
- Alternatives: not stated. Outcome: about 5 billion events per day; 99.99% of dollar volume verified within four days.
- Transferable lesson: measure correctness as balance, not row counts.
#### L2. Square Books (OLTP, grade A)
Source: TEN-42 (see I5).
- Problem: expensive per-merchant aggregation for payouts, no way to split a payment across payouts, and nothing in the database preventing inconsistent payouts.
- Decision: accounts as books and transactions as journal entries that must balance to zero. Inserts only on entry tables. Corrections are new entries. Client isolation via namespaced shelves. Spanner with UUIDs.
- Alternatives: the prior settlement approach is described; other options are not stated.
- Outcome: arbitrary payout splits; a payout is one row; about 20 TB run by a team of three.
- Transferable lesson: make the invariant a property of the data model. Note that the book balance row is the one mutable element.
#### L3. Uber LedgerStore (OLTP, grade A, indexing scope only)
Source: [How LedgerStore Supports Trillions of Indexes at Uber](https://www.uber.com/blog/how-ledgerstore-supports-trillions-of-indexes/) (2024-04-04; CASE-30).
- Problem: complete and correct indexes over ledgers at petabyte scale. Decision: three index classes: strongly consistent (two-phase intent, write, commit, with leftover intents resolved on read), eventually consistent, and time-range for offloading. Index storage moved from DynamoDB to Docstore, partitioned on full timestamp to avoid hot partitions.
- Alternatives: the prior DynamoDB design.
- Outcome: over 2 trillion indexes; no inconsistencies in more than six months; over $6M per year saved.
- Transferable lesson: choose the consistency class per access path. The notes do not establish that LedgerStore is double-entry, so this case is not counted as balance evidence.
#### L4. Modern Treasury Ledgers (OLTP, grade B)
Sources: [Ledgers Objects](https://docs.moderntreasury.com/ledgers/docs/guide-to-ledger-objects) (n.d.; CASE-31); [Transaction Status and Balances](https://docs.moderntreasury.com/ledgers/docs/transaction-status-and-balances) (n.d.; CASE-32); [Ledgers Guarantees](https://docs.moderntreasury.com/ledgers/docs/ledgers-guarantees) (n.d.; TEN-41).
- Problem: a product guaranteeing ledger correctness to customers. Decision: transactions of at least two entries, credits equal to debits per currency; pending (mutable), posted, archived; posted entries immutable, metadata updatable; reversal by a second transaction; atomic multi-entry writes; idempotency keys on POST.
- Alternatives and outcome: vendor documentation only.
- Transferable lesson: a three-state lifecycle with immutability after posting; keep mutable metadata apart from financial fields.
#### L5. Idempotency keys (OLTP, grades B and C)
Sources: [Idempotent requests](https://docs.stripe.com/api/idempotent_requests) (n.d.; CASE-33); [Implementing Stripe-like Idempotency Keys in Postgres](https://brandur.org/idempotency-keys) (2017-10-27; TXN-19, individual practitioner). Leach's [about page](https://brandur.org/about) (n.d.; no catalog ID) says "I recently spent five and a half years at Stripe" (note 22); the post remains a personal account, not Stripe documentation.
- Problem: retries of money-moving requests must not duplicate effects. Decision: Stripe saves the first response for a client key, rejects reuse with different parameters, and may prune keys after at least 24 hours. Leach's design stores the request fingerprint and a recovery point in the same ACID store, splits work into atomic phases, and commits before any foreign call.
- Alternatives: API v2 at Stripe retries work to completion rather than replaying a saved response.
- Outcome: not reported.
- Transferable lesson: persist the fingerprint and progress marker with the business rows.
#### L6. Airbnb financial reporting (OLTP to OLAP, grade U, **UNVERIFIED**)
Sources: [Tracking the Money - Scaling Financial Reporting at Airbnb](https://medium.com/airbnb-engineering/6d742b80f040) (2017-03; CASE-35); [Scaling Airbnb's Payment Platform](https://medium.com/airbnb-engineering/scaling-airbnbs-payment-platform-43ebfc99b324) (2016-09; CASE-36). Never opened.
- Search excerpts suggest a nightly MySQL ETL replaced by an event pipeline with money-in equals money-out, and reporting that had been reverse-engineered from audit trails.
- Alternatives and outcome cannot be reported. Treat as a lead for later verification only.

### Topic findings
**ERP sources used below (note 18).** Grade B unless stated. SAP findings rest on SAP Learning training pages, because help.sap.com rendered as empty shells. Supporting pages named "support" are listed in the catalog entry for that ID.
- SAP: [Posting Period Variants](https://learning.sap.com/courses/local-close-for-the-general-ledger/using-posting-period-variants-to-control-the-opening-and-closing-of-posting-periods_e7818699-66ac-451f-8687-981376d9b6aa) (n.d.; ERP-01); [Configuring Document Reversal](https://learning.sap.com/courses/customizing-core-settings-in-financial-accounting-in-sap-s4hana/configuring-document-reversal) (n.d.; ERP-02); [Currency Keys and Exchange Rate Types](https://learning.sap.com/courses/customizing-core-settings-in-financial-accounting-in-sap-s4hana/identifying-the-basic-functionality-of-currency-keys-and-exchange-rate-types) (n.d.; ERP-03); [Eliminating Intercompany Revenue and Cost](https://learning.sap.com/courses/explaining-corporate-close-with-group-reporting/eliminating-intercompany-revenue-and-cost_bf0684be-4502-4f31-86ad-85dd3d2d04a2) (n.d.; ERP-04).
- Oracle: [GL_PERIOD_STATUSES](https://docs.oracle.com/en/cloud/saas/financials/26a/oedmf/glperiodstatuses-28953.html) (26A; ERP-05); [Using General Ledger](https://docs.oracle.com/en/cloud/saas/financials/26b/faugl/using-general-ledger.pdf) (26B, 2026-03-17; ERP-06); [Financial Enterprise Structure Components](https://docs.oracle.com/en/cloud/saas/applications-common/25d/faesc/financial-enterprise-structure-components.html) (25D; ERP-07); [GL_DAILY_RATES](https://docs.oracle.com/en/cloud/saas/financials/26a/oedmf/gldailyrates-25304.html) (26A; ERP-08).
- Dynamics 365 Finance: [Configure ledgers](https://learn.microsoft.com/en-us/dynamics365/finance/general-ledger/configure-ledger) (2026-04-06; ERP-09); [Year-end close](https://learn.microsoft.com/en-us/dynamics365/finance/general-ledger/year-end-close) (2024-09-25; ERP-10); [Foreign currency revaluation](https://learn.microsoft.com/en-us/dynamics365/finance/general-ledger/foreign-currency-revaluation-general-ledger) (2026-06-24; ERP-11); [Can't reverse a transaction](https://learn.microsoft.com/en-us/troubleshoot/dynamics-365/finance/general-ledger/cant-reverse-transactions) (2024-04-30; ERP-12); [Consolidations and currency translation](https://learn.microsoft.com/en-us/dynamics365/finance/general-ledger/financial-consolidations-currency-translation) (2026-05-01; ERP-13).
- NetSuite: [Closing Tasks and Their Dependencies](https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4317009345.html) (n.d.; ERP-14); [Reopening a Closed Period](https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_N1457543.html) (n.d.; ERP-15); [Consolidated Exchange Rate](https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4685850130.html) (n.d.; ERP-16); [Intercompany Elimination Overview](https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_N1498385.html) (n.d.; ERP-17).
- Open source: [Odoo 18.0 Data inalterability check report](https://www.odoo.com/documentation/18.0/applications/finance/accounting/reporting/data_inalterability.html) (n.d.; ERP-18); [ERPNext Accounting Period](https://docs.frappe.io/erpnext/accounting-period) (n.d.; ERP-19); [ERPNext Currency Exchange](https://docs.frappe.io/erpnext/currency-exchange) (n.d.; ERP-20).
- Standards and law: [IAS 21 summary page](https://www.ifrs.org/issued-standards/list-of-standards/ias-21-the-effects-of-changes-in-foreign-exchange-rates/) (n.d.; ERP-21); [FAS 52](https://storage.fasb.org/aop_fas52.pdf) (1981-12, superseded by the Codification; ERP-22), with the [SEC Baxter order](https://www.sec.gov/files/litigation/admin/2022/33-11032.pdf) (2022-02-22; ERP-22 support); [HGB s.239](https://www.gesetze-im-internet.de/hgb/__239.html) (n.d.; ERP-23); [15 USC 78m](https://www.law.cornell.edu/uscode/text/15/78m) (n.d.; ERP-24); [PCAOB Audit Focus: Journal Entries](https://pcaobus.org/documents/audit-focus-journal-entries.pdf) (2025-01; ERP-25).

**Double entry.** Each transaction's entries sum to zero: L1, L2, L4, plus Fowler's [Patterns for Accounting](https://martinfowler.com/eaaDev/AccountingNarrative.html) (2006-01-24; TEN-40) and Kleppmann's [Accounting for Computer Scientists](https://martin.kleppmann.com/2011/03/07/accounting-for-computer-scientists.html) (2011-03-07; TEN-44).

**Immutability and correction.** Fowler catalogues three correction strategies: replacement (loses history), reversal and difference. L1, L2 and L4 permit only history-preserving options. Modern Treasury adds that pending transactions can be archived and posted ones cannot. Fowler and Modern Treasury derive the balance from entries, while Square materializes it. These agree if entries remain the source of truth.

ERP and legal evidence on posted entries:
- **MANDATORY in substance (Germany, commercial and tax books; OLTP: GL, SUB).** HGB s.239(3): "Eine Eintragung oder eine Aufzeichnung darf nicht in einer Weise verändert werden, daß der ursprüngliche Inhalt nicht mehr feststellbar ist." AO s.146(4) has the same rule for tax, and HGB s.238(1) requires that transactions can be followed: "Die Geschäftsvorfälle müssen sich in ihrer Entstehung und Abwicklung verfolgen lassen." (ERP-23 and support). The statutes bar loss of original content; they do not prescribe a database mechanism.
- **MANDATORY, mechanism not specified (US issuers; OLTP: GL, SUB).** 15 USC 78m(b)(2)(A) requires issuers to "make and keep books, records, and accounts, which, in reasonable detail, accurately and fairly reflect the transactions and dispositions of the assets of the issuer" (ERP-24). 17 CFR 240.13b2-1: "No person shall directly or indirectly, falsify or cause to be falsified, any book, record or account" (ERP-24 support). Neither text mentions reversal entries or database immutability.
- **RECOMMENDED, grounded in audit standards (audited issuers; OLTP: GL).** PCAOB staff list not testing "the completeness of the population of journal entries" as a deficiency (ERP-25). The publication states: "It is not a rule, policy, or statement of the Board." Whether this requires row-level immutability is an inference.
- **RECOMMENDED (OLTP: GL, SUB): correct by new entry.** This is the vendor norm, with the exceptions below.

| Vendor | After posting | Reversal details |
|---|---|---|
| SAP (ERP-02) | Reversal available for documents that cannot be modified | Normal reversal (inverse, increases figures) or negative posting (resets figures); reversal reason required; cleared items block until reset |
| Oracle (ERP-06) | "After posting, either reverse and enter the journal again, or enter a new journal to correct the amounts in question." | "Reversal journals can't be reversed."; methods Change Sign and Switch Debit or Credit |
| Dynamics 365 (ERP-12) | Reversal subject to period status, year-end status and settlement | Reversal can itself be reversed; some documents need credit notes; year-end reversal deletes vouchers |
| NetSuite (ERP-15) | GL-impacting edits blocked in closed periods | Void sets totals to zero; Delete keeps only a record of deletion, and is unavailable when reversing-journal voiding is on |
| Odoo (ERP-18) | Secured entries cannot be edited | SHA-256 chain over named fields; Hard Lock irreversible |
| ERPNext (ERP-19) | "Do not edit a submitted posting." | Reverse Journal Entry "creates a separate draft with exchanged debit and credit sides"; cancellation is a separate path, subject to Immutable Ledger rules not read |

Vendor conflicts, recorded and not resolved:
- **Deletion against non-alteration.** Dynamics 365's Reverse year-end close deletes opening and closing vouchers with a history record and posts no reversing voucher (ERP-10, ERP-12). NetSuite Delete retains only the fact of deletion (ERP-15). HGB s.239(3) forbids changes that lose original content. No source read says whether generated opening balances count as books under the statute.
- **Reversing a reversal.** Oracle does not allow it (ERP-06); Dynamics 365 does (ERP-12).
- **What a reversal does to balances.** SAP negative posting resets figures while normal reversal increases them; Oracle Change Sign keeps the column and flips the sign (ERP-02, ERP-06). Debit and credit activity totals differ by method.
- **Revaluation reversal.** Dynamics 365 GL does not reverse earlier revaluation, while its AR and AP do (ERP-11), and those cannot be reversed afterward, only rerun (ERP-12).

Other findings: a reversal has a separately chosen date and method (RECOMMENDED; OLTP: GL; ERP-02, ERP-06, ERP-12). Eligibility depends on settlement, transfer and fiscal status (RECOMMENDED; OLTP: GL, SUB; ERP-06, ERP-12). Subledger entries can exist before transfer: Dynamics 365 blocks reversal of some invoices until transfer, and Oracle treats "Unprocessed and untransferred subledger transactions" as period close exceptions (RECOMMENDED; OLTP: SUB to GL). Tamper evidence: Odoo's hash chain is the only cryptographic control seen, and no law or standard read requires hashing (OPTIONAL/CONTEXTUAL).

**Gapless numbering.**
- Law, EU: [VAT Directive 2006/112/EC, consolidated](https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:02006L0112-20250414) (2025-04-14; LEG-01) Art. 226(2) requires "a sequential number, based on one or more series, which uniquely identifies the invoice". It does not say whether "sequential" excludes gaps. The UK-archived copy is [TEN-39](https://www.legislation.gov.uk/eudr/2006/112/article/226). **MANDATORY** (OLTP, invoicing; EU VAT-registered suppliers).
- Engine fact: [PostgreSQL Sequence Manipulation Functions](https://www.postgresql.org/docs/current/functions-sequence.html) (n.d.; TEN-33) states that sequences can leave gaps through aborts, crashes and even conflict handling, and cannot provide gapless numbering.
- Sequential does not by itself mean gapless. **Conflict: a single gap rule cannot be derived from these sources.** Positions read (note 19; research input, not legal advice, needs review by counsel):

| Jurisdiction | Requirement | Gaps | Evidence quality | Label and scope |
|---|---|---|---|---|
| EU Directive (LEG-01) | As above | Silent | Direct text | MANDATORY (OLTP, invoicing; EU VAT-registered) |
| Germany (LEG-04, LEG-06) | UStG s.14(4) point 4: "eine fortlaufende Nummer mit einer oder mehreren Zahlenreihen, die zur Identifizierung der Rechnung vom Rechnungsaussteller einmalig vergeben wird" | Reported not mandatory | **Gap rule rests on search snippets of BMF pages only (grade U).** UStAE 14.5(10) could not be opened (HTTP 503) and the 2026 wording was not checked | MANDATORY for one-time issue and series. Gap tolerance unconfirmed |
| France (LEG-07, LEG-08) | "un numéro unique basé sur une séquence chronologique et continue"; series numbering must be chronological and "qu'elle soit continue" | No tolerance found; Service-Public says "without rupture". No official text on spoiled numbers | Direct text; Art. 242 nonies A not opened | MANDATORY (OLTP, invoicing; French scope). Strictest wording found |
| Italy (LEG-10) | "numero progressivo che la identifichi in modo univoco"; the date may contribute to uniqueness | Not addressed | Direct text | MANDATORY (OLTP, invoicing; Italian scope) |
| Spain (LEG-11, LEG-12) | Sequential within each series; separate series for corrective invoices (paraphrase) | Not addressed. VERI*FACTU's no-gap rule concerns the chain of billing records, not invoice numbers | Fetch-tool paraphrase of BOE and AEAT | MANDATORY (OLTP, invoicing; Spanish scope); chained records for billing software in scope of RD 1007/2023 |
| UK (LEG-13, LEG-14) | "a sequential number based on one or more series which uniquely identifies the document" | "As long as you retain the cancelled or spoiled invoice in your accounting records, or you can provide an explanation for the break in sequence, this is acceptable." | Direct HMRC text; VATREC is an internal manual, so it records HMRC's view | MANDATORY for the number; gaps tolerated by guidance. Clearest gap statement found |
| Pakistan (LEG-18, LEG-19) | Sales Tax Act s.23(1): "serially numbered tax invoice"; integrated persons also hold the "unique FBR invoice number" and "every adjustment, modification or cancellation must be recorded" | Not found | Direct text. **Citation conflict on start dates:** SRO 709(I)/2025 reportedly lists 1 May 2025 for corporates (search snippet); FBR's FAQ says June 1st 2025 corporate and July 1st 2025 non-corporate. An extension notice was not opened, so current dates are unresolved | MANDATORY (OLTP, invoicing; Pakistani registered persons, and integrated persons notified by FBR) |
| UAE (LEG-22, LEG-24) | Art. 59(1)(d): "A sequential Tax Invoice number or a unique number which enables identification of the Tax Invoice and the order of the Tax Invoice in any sequence of invoices." E-invoicing adds a UUID "generated in addition to the Electronic Invoice sequential number" | Not found | Direct text. **Citation conflict:** the MoF compilation footnote reads "Article amended as per Cabinet Decision No. 100 of 2024", while secondary commentary cites No. 100 of 2025. The compilation is an October 2024 upload | MANDATORY (OLTP, invoicing; UAE VAT registrants) |
| Saudi Arabia (LEG-25 to LEG-27) | "The tax invoice must include a sequential number that distinguishes it from other invoices" | "Invoice counter value should not be re-used."; rejected documents consume a counter value and stay in the hash chain | Direct text; the technical guideline is November 2022 and later versions may exist | MANDATORY (OLTP, invoicing; KSA e-invoicing scope) |

Source links: [UStG s.14](https://www.gesetze-im-internet.de/ustg_1980/__14.html) (LEG-04); [UStAE 14.5](https://usth.bundesfinanzministerium.de/usth/2022/A-Umsatzsteuergesetz/IV-Steuer-und-Vorsteuer/Paragraf-14/ae-14-5.html) (2022 edition; LEG-06, **unverified, not opened**); [BOFiP mentions obligatoires](https://bofip.impots.gouv.fr/bofip/140-PGP.html/identifiant=BOI-TVA-DECLA-30-20-20-10-20121231) (LEG-07); [Service-Public billing](https://entreprendre.service-public.gouv.fr/vosdroits/F23208?lang=en) (LEG-08); [Risoluzione 1/E](https://www.agenziaentrate.gov.it/portale/documents/20143/304338/Risoluzione+1++10012013a_risoluzione+1e.pdf/71b92d56-5b2e-6e70-a1c1-47cf4d365a29) (2013-01-10; LEG-10); [RD 1619/2012](https://www.boe.es/buscar/act.php?id=BOE-A-2012-14696) (LEG-11); [AEAT trazabilidad FAQ](https://sede.agenciatributaria.gob.es/Sede/iva/sistemas-informaticos-facturacion-verifactu/preguntas-frecuentes/caracteristicas-requisitos-sif-trazabilidad.html) (2026-10-21; LEG-12); [VAT Notice 700/21](https://www.gov.uk/guidance/record-keeping-for-vat-notice-70021) (LEG-13); [VATREC5010](https://www.gov.uk/hmrc-internal-manuals/vat-trader-records/vatrec5010) (LEG-14); [Sales Tax Act 1990](https://download1.fbr.gov.pk/Docs/202586148252375SalesTaxActupdatedupto2025-26.pdf) (LEG-18); [Sales Tax Rules 2006](https://download1.fbr.gov.pk/Docs/2025881385446623STR-2006-UpdatedUpto06-08-2025(ver-iv).pdf) (LEG-19); [VAT Executive Regulation](https://mof.gov.ae/wp-content/uploads/2024/10/Executive-Regulation-of-Federal-Decree-Law-No-8-of-2017.pdf) (LEG-22); [UAE E-Invoicing Guidelines V2.0](https://mof.gov.ae/wp-content/uploads/2026/10/UAE-Electronic-Invoicing-Guidelines_En.pdf) (2026-10-26; LEG-24); [ZATCA invoicing guideline](https://zatca.gov.sa/en/HelpCenter/guidelines/Documents/Guideline-for-Tax-Invoicing-and-Records-under-VAT-Provisions.pdf) (LEG-25); [E-invoicing technical guidelines v2](https://zatca.gov.sa/en/E-Invoicing/Introduction/Guidelines/Documents/E-invoicing-Detailed-Technical-Guideline.pdf) (2022-11; LEG-26); [XML Implementation Standard](https://zatca.gov.sa/ar/E-Invoicing/SystemsDevelopers/Documents/20230519_ZATCA_Electronic_Invoice_XML_Implementation_Standard_%20vF.pdf) (LEG-27).
- Inference (grade I): assign the number inside the posting transaction from a locked per-series counter, only at posting, so drafts consume none. The cost is serialized posting per series. No fetched case documents this at scale.
- ViDA: [Council Directive (EU) 2025/516](https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=OJ:L_202500516) (2025-03-25; LEG-02), now read on EUR-Lex, adds Art. 226 point (16) through its Art. 5, with effect from 1 July 2030: "in the case of a corrective invoice as referred to in Article 219, the sequential number which identifies the corrected invoice, as referred to in point (2) of this paragraph". **MANDATORY from 1 July 2030 where transposed** (OLTP, invoicing; EU scope per national law). Art. 226(2) is not rewritten by any amendment seen, and national transposition was not researched. Full phases are in `database_security_standards.md`, section 12.8.
- Design consequence (inference, note 19): a system built for several jurisdictions would meet the strictest applicable rule per legal entity and keep an explanation record for any number not used. Authority-assigned numbers, UUIDs, counters and previous-invoice hashes are separate attributes from the local number where those regimes apply.
- Frappe's naming series (E2) is a convention; the notes do not show whether it is gapless.

**Multi-currency.** Modern Treasury is the only source explicitly requiring balance per currency. Stripe reports over 135 currencies but the notes do not capture how balances are modelled. Amounts must be exact: [PostgreSQL Numeric Types](https://www.postgresql.org/docs/current/datatype-numeric.html) (n.d.; PGMY-02) says floating types are inexact and directs monetary values to `numeric`. **Conflict:** an example in [How we style our dbt models](https://docs.getdbt.com/best-practices/how-we-style/1-how-we-style-our-dbt-models) (2026-09-10; LAKE-16) casts a money-like total to float, `( order_total / 100.0 ) :: float as order_total` (confirmed in note 22), against the exact-decimal rule. Style examples should not be read as money-handling guidance.

ERP and standard-setter evidence (note 18):
- **Standards.** IAS 21's summary page says "The principal issues are which exchange rate(s) to use and how to report the effects of changes in exchange rates" and defines functional currency as "the currency of the primary economic environment in which the entity operates" (ERP-21). It does not give the rate rules, and full IFRS text was not read. MANDATORY for IFRS reporters at concept level only.
- **US GAAP.** The current Codification returned 403. The SEC Baxter order states: "ASC 830-20-30-1 requires that foreign currency transactions initially be measured and recorded in an entity's functional currency using the exchange rate on the date of the transaction. ASC 830-20-35-2 requires that foreign currency denominated assets and liabilities be remeasured at the end of each reporting period using the exchange rate at that date." FAS 52 para. 12 allows that "an appropriately weighted average exchange rate for the period may be used" (ERP-22).
- **MANDATORY in substance (US GAAP issuers, per the SEC order; OLTP: GL, SUB): a transaction-date rate must be attributable to the transaction.** The order describes a convention using a specified mid-month prior-period rate as "not in accordance with GAAP". Whether a stored per-line rate is required is an inference, not stated.
- **RECOMMENDED (OLTP+OLAP: GL, CONS): several rate roles per period.** NetSuite stores `currentrate`, `averagerate`, `historicalrate` per period, subsidiary pair and book (ERP-16). Dynamics 365 allows different rate types for revaluation and reporting per main account (ERP-11). SAP rate types include M, B, G and P (ERP-03 support).
- **RECOMMENDED (OLTP, OLAP: GL, DW): rates keyed by pair, date and type.** Oracle's key is `FROM_CURRENCY, TO_CURRENCY, CONVERSION_DATE, CONVERSION_TYPE` (ERP-08). ERPNext "searches by transaction date and chooses the latest eligible matching record" (ERP-20). So two effective-dating patterns exist: exact-day rows and most-recent-on-or-before. SAP's valid-from logic was not established.
- **RECOMMENDED (OLTP: GL, SUB): keep original, entity and optional reporting amounts together.** Dynamics 365 records accounting and optional reporting currency on all vouchers (ERP-09). ERPNext says "Do not change an Account's currency after ledger entries exist." (ERP-20 support). SAP allows up to eight additional currency types per ledger (ERP-03 support).
- **RECOMMENDED (OLTP: GL): revaluation has a run record and a separate rate date** (ERP-11; ERP-17 support). **Realized and unrealized differences use separate accounts** (ERP-09, ERP-20 support; ERP-18 support; ERP-17 support).
- **OPTIONAL/CONTEXTUAL (OLTP: GL): rounding needs a defined home.** ERPNext: "Each line is converted and rounded separately, so totals can differ by a cent or a few units of a small currency." (ERP-20 support). Oracle balances by legal entity including rounding imbalances (ERP-07).
- **OPTIONAL/CONTEXTUAL (OLTP+OLAP: CONS): translation paths are not transitive in the products read.** Dynamics 365 needs an intermediate consolidation company for MXN to USD to EUR (ERP-13); NetSuite rates are per subsidiary pair (ERP-16).
- **Conflict: inverse rates.** ERPNext: "The inverse is not automatically the same number, so create USD to EUR separately when that direction is needed." (ERP-20). Oracle stores an inverse row that is generally the reciprocal (paraphrase, ERP-08). A rate and its reciprocal may not agree after rounding.
- **Conflict: unrealized differences.** Dynamics 365's ledger page places unrealized gains and losses on the balance sheet (ERP-09), while its revaluation example posts to accounts named Unrealized loss and gain against cash (ERP-11). Presentation needs clarification.
- **Not supported:** rate precision (no vendor or standard page read states one) and triangulation (no vendor page opened describes it).

**Fiscal period close.** Vendor documentation replaces the earlier inference of one per-company period status (note 18). No law or standard read prescribes a period-close data model.

| Vendor | Status keyed by | Status values or controls | Adjustment periods | Year-end |
|---|---|---|---|---|
| SAP S/4HANA (ERP-01) | Posting period variant per company code; account type and interval | Open or closed through intervals | Up to four special periods, 13-16 | Not established |
| Oracle Fusion (ERP-05, ERP-06) | `APPLICATION_ID`, `LEDGER_ID`, `PERIOD_NAME` | `CLOSING_STATUS`: O, F, C, P, N (26A table) | `ADJUSTMENT_PERIOD_FLAG` | Not fully extracted |
| Dynamics 365 Finance (ERP-09, ERP-10) | Per-entity ledger calendar copied from a shared fiscal calendar; module access | Open, On hold, Permanently closed | Closing period copies dates of an open period | Generated opening transaction, rerun allowed |
| NetSuite (ERP-14, ERP-15) | Period; per subsidiary for locks; per book for close | Locks for A/R, A/P, Payroll, All; Close per book | No statement found | No statement found |
| Odoo (ERP-18) | Date per company | Lock Everything date with logged exceptions; Hard Lock date | None in pages read | Manual entry to equity |
| ERPNext (ERP-19) | Date range and company, by document type | Accounting Period, Accounts Frozen Till Date, Period Closing Voucher | None in pages read | Period Closing Voucher transfers profit or loss |

- **RECOMMENDED (OLTP: GL, SUB): status is held at a finer grain than company.** Convergence on the principle is strong; the chosen grain differs by vendor.
- **RECOMMENDED (OLTP: GL): calendar definition and period status are separable** (ERP-05, ERP-09).
- **RECOMMENDED (OLTP: GL, SUB): close is ordered and gated, not a status write.** NetSuite publishes an ordered dependency list (ERP-14). Oracle: "Regardless of how the option is set, you can't close a General Ledger period for a ledger that has pending Intercompany transactions" (ERP-06).
- **RECOMMENDED (OLTP: GL): reopening invalidates downstream close work.** NetSuite reopens later closed periods automatically and stores a justification (ERP-15). Dynamics 365 requires a rerun of close to carry balances (ERP-10, ERP-12).
- **OPTIONAL/CONTEXTUAL (OLTP, OLAP: GL, DW): adjustment periods overlap in dates, so a date does not identify a period** (ERP-01, ERP-06, ERP-09). Fiscal year status also differs from period status (ERP-12).
- **OPTIONAL/CONTEXTUAL (OLTP: GL, SUB): period close and P&L closing can be different objects.** ERPNext: "The voucher does not erase history or stop backdated entries." (ERP-19).
- **Conflict: permanent close.** An older Oracle guide offers Permanently Closed with no transition out (ERP-05 support), and Odoo's Hard Lock cannot be overridden (ERP-18). Dynamics 365 offers Permanently closed but advises against it because the period cannot reopen (ERP-10).
- **Unconfirmed:** a Fusion REST status W appears only in search output.

**Multi-company posting.** [Subsidiaries in OneWorld](https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_N268563.html) (n.d.; TEN-09) describes postings to a single subsidiary with intercompany exceptions, and elimination journals at consolidation. [Organizations and organizational hierarchies overview](https://learn.microsoft.com/en-us/dynamics365/fin-ops-core/fin-ops/organization-administration/organizations-organizational-hierarchies) (2026-04-24; TEN-08) uses the company ID as a data-security boundary. [Odoo 18.0: Companies](https://www.odoo.com/documentation/18.0/applications/general/companies.html) (n.d.; TEN-10) distinguishes companies from branches.

Further evidence (note 18):
- **RECOMMENDED (OLTP+OLAP: GL, CONS): legal entity, ledger and business unit are distinct.** Oracle's primary balancing segment represents legal entities, and a business unit posts to one primary ledger (ERP-07). Dynamics 365 configures a ledger per legal entity (ERP-09). No official SAP definition of company code against legal entity was read.
- **RECOMMENDED (OLTP+OLAP: GL, CONS): intercompany is a linked pair of entries, each balanced per entity.** ERPNext: "Each company's entry balances independently." (ERP-20 support). Dynamics 365 uses directional legal entity pairs with due-to and due-from accounts (ERP-13 support). Oracle balances automatically by legal entity (ERP-07).
- **OPTIONAL/CONTEXTUAL (OLTP+OLAP: CONS): where elimination lives varies.** Dynamics 365 uses a separate elimination entity or report-time consolidation (ERP-13); SAP uses posting level 20 (ERP-04); NetSuite uses elimination journals with differences to CTA-E (ERP-17).
- **RECOMMENDED (OLTP+OLAP: CONS): currency differences on intercompany are expected, not errors** (ERP-13, ERP-17).
- **MANDATORY in substance only for consolidated reporters (CONS).** The IFRS 10 page says a parent must present consolidated statements (paraphrase, ERP-21 support). Elimination paragraphs were not available, and that page does not mention intragroup elimination. FAS 52 para. 25 addresses elimination of intercompany profits. 17 CFR 210.3A-04 could not be read.

### Practices

| Practice | Label | Evidence |
|---|---|---|
| Each ledger transaction balances to zero | MANDATORY (ledgers) | L1, L2, L4, TEN-40, TEN-44 |
| Posted entries are never updated or deleted; correct by new entries | MANDATORY (ledgers built on this invariant); MANDATORY in substance for German commercial and tax books, as non-alteration only; RECOMMENDED for ERP general ledgers, with vendor exceptions | L1, L2, L4, TEN-40; ERP-23; ERP-02, ERP-06, ERP-12, ERP-15 |
| Multi-entry writes are atomic | MANDATORY (ledgers) | L4; transaction theory in section 11 |
| Money-moving writes are idempotent | MANDATORY (payment and posting APIs) | L4, L5 |
| Store monetary amounts in exact types | MANDATORY | PGMY-02; LAKE-16 is the conflict |
| Invoice numbers are sequential within series and unique | MANDATORY where Art. 226 or the national rule applies | LEG-01, TEN-39; jurisdiction table above |
| Record every unused or cancelled invoice number with a reason | RECOMMENDED (OLTP, invoicing) | LEG-14, LEG-07, LEG-26 |
| Corrective invoices reference the corrected invoice's sequential number | MANDATORY from 1 July 2030 where transposed (OLTP, invoicing; EU) | LEG-02 |
| Keep authority number, UUID, counter and previous hash apart from the local number | MANDATORY where the regime applies (OLTP, invoicing; Pakistan, UAE, Saudi Arabia) | LEG-19, LEG-24, LEG-26, LEG-27 |
| Do not use database sequence objects for legally numbered documents | MANDATORY where gaps are not acceptable; France has the strictest wording found. Note 19 labels the design move RECOMMENDED | TEN-33, LEG-07; other engines not checked here |
| Balance per currency, each entry carrying its currency | RECOMMENDED. Topic 14 labels it MANDATORY, downgraded here because one vendor states it; it follows logically from amounts in different currencies not being summable | L4 |
| Derive balances from entries; version any materialized balance | RECOMMENDED | TEN-40, L2, L4 |
| Explicit lifecycle such as pending, posted, archived | RECOMMENDED | L4, E2 |
| Clearing accounts monitored for net zero | RECOMMENDED; detailed evidence is Stripe's alone | L1 |
| One legal entity per posting, paired postings for intercompany | RECOMMENDED for multi-entity ERP. Topic 14 labels it MANDATORY; the sources are vendor designs | TEN-09, TEN-08 |
| Locked per-series counter assigned at posting | RECOMMENDED, provisional (inference) | Grade I |
| Period status checked at posting, at a grain finer than company | RECOMMENDED (OLTP: GL, SUB); the grain differs by vendor | ERP-01, ERP-05, ERP-09, ERP-15, ERP-19 |
| Close runs as an ordered, gated process, and reopening invalidates later close work | RECOMMENDED (OLTP: GL, SUB) | ERP-06, ERP-10, ERP-14, ERP-15 |
| Decide explicitly whether an irreversible close exists | RECOMMENDED, with vendor disagreement on using it (OLTP: GL) | ERP-05, ERP-10, ERP-18 |
| Attribute a transaction-date rate to each foreign-currency transaction | MANDATORY in substance (US GAAP issuers; OLTP: GL, SUB). A stored per-line rate is an inference | ERP-22 and support |
| Key rates by pair, date and rate type, and keep several rate roles per period | RECOMMENDED (OLTP+OLAP: GL, CONS, DW) | ERP-08, ERP-11, ERP-16, ERP-20 |
| Keep original, entity and optional reporting amounts together | RECOMMENDED (OLTP: GL, SUB) | ERP-03 support, ERP-09, ERP-20 support |
| Intercompany as linked entries, each balanced per entity | RECOMMENDED (OLTP+OLAP: GL, CONS) | ERP-07, ERP-13 support, ERP-20 support |
| Tamper-evident or system-versioned journal storage | OPTIONAL/CONTEXTUAL | [Temporal Features in SQL:2011](https://sigmodrecord.org/publications/sigmodRecord/1209/pdfs/07.industry.kulkarni.pdf) (2012-09; GOV-06) |

## 6. Data platforms and quality
#### D1. LinkedIn DataHub (OLTP+OLAP metadata, grade A)
Source: [DataHub: Popular metadata architectures explained](https://www.linkedin.com/blog/engineering/data-management/datahub-popular-metadata-architectures-explained) (2020-12-07; CASE-37).
- Problem: pull-based crawlers are fragile and stale. Push APIs lack a change log and create a central bottleneck. Decision: third-generation event-sourced design, with a metadata change log materialized into search, graph and analytical indexes, over strongly typed models.
- Alternatives: first-generation crawlers and second-generation push services, with named examples.
- Outcome: about 10M change events per day and over 5M indexed entities and relationships.
- Transferable lesson: make the log the source of truth so indexes can be rebuilt. The cost is complexity.
#### D2. Uber Databook (OLAP metadata, grade A)
Source: [Databook: Turning Big Data into Knowledge with Metadata at Uber](https://www.uber.com/blog/databook/) (2018-08-03; CASE-38).
- Problem: tens of thousands of tables across Hive, Presto and Vertica. Decision: build rather than adopt; store metadata rather than query sources on demand; separate collection from serving; link cluster-specific and cluster-agnostic metadata at read time; Cassandra for multi-DC replication.
- Alternatives rejected: WhereHows (no cross-DC reads and writes, unsupported stack); MySQL (about 70 ms added per cross-DC write).
- Outcome: about 1,500 QPS peak API.
- Transferable lesson: do not push read load onto systems not designed for it.
#### D3. Stripe data-quality rubric (OLTP+OLAP, grade A)
Source: TEN-43 (see L1). Clearing, timeliness and completeness form a reusable rubric for pipelines that must reconcile to external truth. One company's scheme; context only.
#### D4. Airbnb Midas and Minerva (OLAP, grade U, **UNVERIFIED**)
Sources: [Data Quality at Airbnb](https://medium.com/airbnb-engineering/data-quality-at-airbnb-870d03080469) (n.d.; CASE-39); [How Airbnb Achieved Metric Consistency at Scale](https://medium.com/airbnb-engineering/how-airbnb-achieved-metric-consistency-at-scale-f23cc53dea70) (n.d.; CASE-40). Never opened.
- Search excerpts suggest a certification process with a later lighter-weight score, and a centralized metric layer. Metric counts come only from a secondary summary.
- Problem, alternatives and outcome are not verified. Supports no practice here.

### Literature context for OLAP
- [One Size Fits All: An Idea Whose Time Has Come and Gone](https://cs.brown.edu/~ugur/fits_all.pdf) (2005; PERF-38; venue unconfirmed in the PDF text) is the argument for separating OLTP and OLAP engines. [C-Store](https://www.vldb.org/archives/website/2005/program/paper/thu/p553-stonebraker.pdf) (2005; PERF-39) supplies columnar design levers.
- [Delta Lake](https://www.vldb.org/pvldb/vol13/p3411-armbrust.pdf) (2020-08; LAKE-08) and [Lakehouse](https://www.cidrdb.org/cidr2021/papers/cidr2021_paper17.pdf) (2021-01; LAKE-07) bring transaction logs and declared schemas to open tables.
- Kimball's [Data Warehouse Toolkit](https://www.wiley.com/en-us/-p-9781118530801) (2013-07; LIT-43), Inmon's [Building the Data Warehouse](https://www.wiley.com/en-us/-p-9780764599446) (2005-10; LIT-45) and Linstedt's [Data Vault 2.0](https://shop.elsevier.com/books/building-a-scalable-data-warehouse-with-data-vault-20/linstedt/978-0-12-802510-9) (2015-09; LIT-47) are competing modelling schools, not one best practice.

### Practices

| Practice | Label | Evidence |
|---|---|---|
| Separate metadata collection from serving | RECOMMENDED | D1, D2 |
| Keep an event or change log as the rebuildable source for derived indexes | RECOMMENDED for platform-scale metadata and ledgers | D1, L1, L2 |
| Reconcile pipeline outputs to an external truth on balance, timeliness and completeness | RECOMMENDED for financial pipelines | L1 |
| Choose warehouse modelling style by explicit criteria | RECOMMENDED | LIT-43, LIT-45, LIT-47 |
| Tiered data certification and single-definition metrics | OPTIONAL/CONTEXTUAL; unverified evidence only | D4 |

## 7. Multi-tenancy
#### T1. Salesforce metadata-driven tenancy (OLTP, grade B)
Sources: [Platform Multitenant Architecture](https://architect.salesforce.com/fundamentals/platform-multitenant-architecture) (n.d.; TEN-07); [The Design of the Force.com Multitenant Internet Application Development Platform](https://doi.org/10.1145/1559845.1559942) (2009; LIT-38; DOI redirect never loaded, so its flex-column details are not verified from the paper).
- Problem: many tenants with custom objects on one shared schema. Decision (from TEN-07): object and field metadata tables; a data table with generic slot columns keyed by org; pivot tables for indexing, uniqueness and relationships; an optimizer with tenant-level statistics.
- Alternatives: not stated. Outcome: not reported. Transferable lesson: per-tenant skew defeats global statistics. This design suits platforms with tenant-defined objects; it is not a default for ordinary SaaS or ERP.
#### T2. Atlassian tenant context (OLTP, grade B)
Source: [Cloud architecture and operational practices](https://www.atlassian.com/trust/reliability/cloud-architecture-and-operational-practices/) (n.d.; CASE-42).
- Problem: shared services must keep tenant data segregated. Decision: a tenant context service, with requests rejected if no context exists; service-owned stores; per-service keys wrapped by KMS; a separate single-tenant offering.
- Alternatives and outcome: not stated; trust documentation. Transferable lesson: logical isolation needs a mandatory tenant token on the request path.
#### T3. Citus tenant co-location (OLTP, grade B)
Source: [Multi-tenant Applications](https://docs.citusdata.com/en/stable/use_cases/multi_tenant.html) (n.d.; PERF-44).
- Problem: keep joins, constraints and transactions local after distribution. Decision: a tenant column on every table used as distribution column, primary and foreign keys that include it, reference tables replicated to workers, and tooling to isolate large tenants.
- Alternatives: not stated. Outcome: documentation only.
- Transferable lesson: composite keys with a tenant prefix are the price of co-location. Notion's retrospective reaches a related conclusion (S2).
#### T4. Tenant versus legal entity in ERP (OLTP, grade B, inference for the split)
Sources: TEN-08, TEN-09, TEN-10, and F4 in section 8. A SaaS tenant is the customer boundary, and a company is the posting and statutory boundary within it. iDempiere's client and organization columns show the two levels directly. The conclusion that both identifiers are always needed is an inference from topic 14.

### Practices

| Practice | Label | Evidence |
|---|---|---|
| No data access path without a tenant scope (column, token or physical unit) | MANDATORY for multi-tenant systems | T1, T2, T3, S7 |
| Include tenant key in primary and foreign keys when distributing by tenant | RECOMMENDED; MANDATORY under engines requiring it, as Citus does | T3, S2 |
| Provide a way to isolate outlier tenants | RECOMMENDED | T3, S3, S6 |
| Keep tenant-aware statistics or plan for skew | OPTIONAL/CONTEXTUAL | T1 |
| Separate tenant from legal entity in ERP | RECOMMENDED (inference) | T4 |
| Full pod isolation | OPTIONAL/CONTEXTUAL | S7 |

## 8. Open-source ERP conventions
All are OLTP and grade B (official documentation). They show what mature frameworks standardize. They are reference conventions, not proof of good outcomes.
#### E1. Odoo
Source: [ORM API (Odoo 18.0)](https://www.odoo.com/documentation/18.0/developer/reference/backend/orm.html) (n.d.; CASE-44).
- Problem: uniform audit, multi-company and archive behavior across many models. Decision: automatic `id` and access-log fields (`create_date`, `create_uid`, `write_date`, `write_uid`); reserved `active`, `state`, `parent_id`/`parent_path`, `company_id`; company-consistency checks at ORM level.
- Alternatives and outcome: not stated. Lesson: ORM-level conventions make cross-cutting behavior uniform, but checks live in the application tier.
#### E2. Frappe/ERPNext
Sources: [DocTypes](https://docs.frappe.io/framework/user/en/basics/doctypes) (n.d.; CASE-45); [Naming](https://docs.frappe.io/framework/user/en/basics/doctypes/naming) (n.d.; CASE-46); [DocStatus](https://docs.frappe.io/framework/doctypes/docstatus) (n.d.; CASE-47).
- Problem: document-centric lifecycle and naming. Decision: a primary key called `name`; multiple naming strategies including naming series; integer `docstatus` of draft, submitted, cancelled; submitted and cancelled documents not editable except explicitly allowed fields; amended documents get numbered suffixes.
- Alternatives and outcome: not stated. Lesson: a three-state lifecycle with post-submit immutability parallels ledger posting. Note 22 confirmed `docstatus` at the [DocStatus page](https://docs.frappe.io/framework/doctypes/docstatus) but found no owner, modified or creation text on the DocTypes page, so `creation` and `modified` are unconfirmed there. The full standard column list and amend semantics were not seen.
#### E3. Apache OFBiz
Sources: [General Entity Overview](https://cwiki.apache.org/confluence/display/OFBIZ/General+Entity+Overview) (2016-12-05, last updated; CASE-48); [EntitySync manual](https://apache.googlesource.com/ofbiz-framework/+/1bc8a206346f251c9076c2fb9babc896ba6bdf0d/framework/entityext/src/doc/asciidoc/EntitySync-manual.adoc) (n.d.; CASE-49).
- Problem: extensible entities and replayable sync between instances. Decision: XML entity definitions; join entities for many-to-many; a type and attribute extensibility pattern; four automatic stamp fields, row-level and transaction-level, so changes can be replayed in order; removals logged separately.
- Alternatives and outcome: not stated. Lesson: separate row timestamps from transaction timestamps when replay is needed. The Silverston attribution is not verified.
#### E4. iDempiere
Source: [I_AD_Org (iDempiere Javadoc)](https://jenkins-artifacts.idempiere.org/javadoc12/org/compiere/model/I_AD_Org.html) (n.d.; CASE-50).
- Problem: two-level tenancy in one schema. Decision: `AD_Client_ID` (tenant), `AD_Org_ID` (organization within tenant), `IsActive`, `Created`, `CreatedBy`, `Updated`, `UpdatedBy`, `Value`, `Name`.
- Alternatives and outcome: not stated. Lesson: two-level tenancy can be explicit. Columns were verified on the AD_Org interface only; that they appear on every table comes from an unverified wiki excerpt.

### Convergence matrix (as verified in the notes)

| Concern | Odoo | Frappe | OFBiz | iDempiere (AD_Org only) |
|---|---|---|---|---|
| Surrogate or primary identifier | `id` | `name` | not captured | `Table_ID` is table-level; row ID not captured |
| Created at / by | `create_date` / `create_uid` | `creation` unconfirmed (note 22) / not seen | `createdStamp` / not captured | `Created` / `CreatedBy` |
| Updated at / by | `write_date` / `write_uid` | `modified` unconfirmed (note 22) / not seen | `lastUpdatedStamp` / not captured | `Updated` / `UpdatedBy` |
| Transaction-level stamps | not captured | not captured | `createdTxStamp`, `lastUpdatedTxStamp` | not captured |
| Tenant or company column | `company_id` | not seen | not captured | `AD_Client_ID`, `AD_Org_ID` |
| Archive or soft delete | `active` | `docstatus=2` is cancel, not delete | removal log | `IsActive` |
| Document state | `state` (reserved) | `docstatus` | not captured | not captured |
| Optimistic-lock version column | not captured | not captured | not captured | not captured |

Corrections applied: the note's claim of record-level versioning for optimistic locking is unsourced and removed. The note's four-way convergence on tenant and soft-delete columns is narrower than stated, as the matrix shows.

### Practices

| Practice | Label | Evidence |
|---|---|---|
| Uniform who/when audit columns applied by framework, not by hand | RECOMMENDED; three of four frameworks verified for both fields, Frappe unconfirmed (note 22) | E1, E3, E4 |
| Document lifecycle state with immutability after submit or post | RECOMMENDED for transactional documents | E2, L4 |
| Soft-delete or archive flag for master data | OPTIONAL/CONTEXTUAL; conflicts with erasure and tombstone concerns noted in 10.3 | E1, E4 |
| Separate transaction stamp for replayable sync | OPTIONAL/CONTEXTUAL | E3 |
| Type and attribute tables for extension | OPTIONAL/CONTEXTUAL; a form of generic modelling that needs review against EAV costs | E3, T1 |

## 9. Postmortems
#### P1. GitLab.com outage, January 31, 2017 (OLTP, grade A)
Source: [Postmortem of database outage of January 31](https://about.gitlab.com/blog/2017/02/10/postmortem-of-database-outage-of-january-31/) (2017-02-10; CASE-51).
- Problem: a load spike caused replication lag and WAL segments were removed before the secondary consumed them. During manual resync an engineer wiped the primary's data directory instead of the secondary's.
- Decision during incident: recover from a 6-hour-old LVM snapshot, the only usable copy. `pg_dump` had run at the wrong version and failed, failure emails were rejected, the S3 bucket was empty, and database disk snapshots were never enabled.
- Alternatives: none remained. Outcome: about 18 hours of outage and about six hours of data lost, covering at least 5,000 projects, 5,000 comments and about 700 accounts. GitLab's root cause was that nobody owned testing the procedure.
- Transferable lesson: replication is not a backup, an unrestored backup is unproven, and production hosts must be unmistakable.
#### P2. GitHub, October 21, 2018 (OLTP, grade A)
Sources: [October 21 post-incident analysis](https://github.blog/2018-10-30-oct21-post-incident-analysis/) (2018-10-30, updated 2021-12-19; CASE-52); [MySQL High Availability at GitHub](https://github.blog/2018-06-20-mysql-high-availability-at-github/) (2018-06-20, updated 2020-05-21; CASE-53).
- Problem: 43 seconds of lost East Coast connectivity. Orchestrator promoted West primaries and writes landed on both coasts. Decision: prioritize data integrity over site usability, and restore East clusters from multi-terabyte backups. A full-cluster restore had never been done.
- Alternatives: faster recovery at the risk of inconsistency, which GitHub declined.
- Outcome: 24 hours 11 minutes degraded. One cluster had 954 unreconciled writes, and about 200K webhook payloads expired.
- Transferable lesson: failover automation must encode topologies the application can actually serve; measure restore time; design out divergent writes.

### Practices

| Practice | Label | Evidence |
|---|---|---|
| Test restores on a schedule with a named owner | MANDATORY | P1, P2 |
| Do not count replication as backup | MANDATORY | P1; [AWS disaster recovery options](https://docs.aws.amazon.com/whitepapers/latest/disaster-recovery-workloads-on-aws/disaster-recovery-options-in-the-cloud.html) (n.d.; OPS-21) |
| Alert on backup job failure through a verified channel | RECOMMENDED | P1 |
| Measure full restore duration, not just job success | RECOMMENDED | P2 |
| Constrain automated promotion by topology | RECOMMENDED; GitHub is the only detailed source | P2 |
| Make primary and secondary hosts unmistakable | RECOMMENDED | P1 |

## 10. Contested cases
### 10.1 Uber against the PostgreSQL community (OLTP)
**Uber's position.** Sources: [Why Uber Engineering Switched from Postgres to MySQL](https://www.uber.com/blog/postgres-to-mysql-migration/) (2016-07-26; CASE-09); [Designing Schemaless](https://www.uber.com/blog/schemaless-part-one-mysql-datastore/) (2016-01-12; CASE-10).
- Problem: from early 2014 Uber could not store enough trip data on Postgres. It reported write amplification across indexes, verbose physical WAL replication across regions, a replication bug in 9.2 returning duplicate rows, replica query conflicts, major-upgrade downtime, and limits from process-per-connection.
- Decision: Schemaless, an append-only sparse hash map of immutable JSON cells on sharded MySQL/InnoDB, with global eventually consistent secondary indexes.
- Alternatives rejected: Cassandra, Riak, MongoDB, for not meeting its five requirements in the time available. Uber later adopted Cassandra and Riak elsewhere.
- Outcome: the notes report the architecture and rationale, not comparative measurements.

**The rebuttals.**
- Winand, [On Uber's Choice of Databases](https://use-the-index-luke.com/blog/2016-07-29/on-ubers-choice-of-databases) (2016-07-29; CASE-11): the findings concern an UPDATE-heavy workload, the InnoDB secondary-index penalty is understated, and Uber built Schemaless rather than simply replacing one database with another.
- Riggs, [Thoughts on Uber's List of Postgres Limitations](https://www.enterprisedb.com/blog/thoughts-ubers-list-postgres-limitations) (2016-08-02; CASE-12): HOT and the visibility map address much of the write and vacuum critique; the replication comparison sets logical against physical; `hot_standby_feedback` prevents most replay conflicts. The post is hosted by a PostgreSQL vendor.
- Pettus, [A PostgreSQL Response to Uber](https://thebuild.com/blog/2017/04/28/a-postgresql-response-to-uber) (2017-04-28; CASE-13) with [slides](https://thebuild.com/presentations/uber-perconalive-2017.pdf) (2017; CASE-14): an item-by-item assessment finding the claims partly true, partly misdirected. He acknowledges real pain points, but says Uber offered little quantitative data, had already decided on a schemaless architecture, and that the MySQL advantage was largely tolerance of application bugs.

| Claim | Uber | Community response | Assessment from the notes |
|---|---|---|---|
| Write amplification | Each indexed update touches all indexes | True when an indexed column changes; HOT avoids it otherwise; InnoDB pays on secondary reads | Real but pattern-dependent |
| Replication | Physical WAL too verbose | Compares logical with physical; logical options exist | Comparison was uneven |
| Replica MVCC | Queries cancelled or replay delayed | Configurable (`hot_standby_feedback`, separate replicas) | Partly addressed by settings |
| Upgrades | Hours of downtime | `pg_upgrade -k`, logical upgrades | Partly valid at the time |
| Connections | Few hundred connections | Pooling exists; impact unquantified | Valid but unquantified |
| Data model | Moved to Schemaless | Real change was the data model | Community point is strong |

**Scoped conclusion (label OPTIONAL/CONTEXTUAL).** Evaluate engines against your own update pattern, index count, replication model and connection discipline. Neither side provides controlled comparative data in the notes. Uber's result does not support a general preference between engines.

### 10.2 No foreign keys at scale against integrity advocates (OLTP)
**For dropping database-enforced relationships.**
- Pinterest (S5) gave up joins and transactions; its path runs from "1 DB + Foreign Keys + Joins" to ID-sharded databases, and its advice is "Remove all joins and complex queries, add cache". Its slides also list the costs.
- Uber Schemaless (10.1) stores JSON cells with application-level structure.
- Operational cost is real: per [ALTER TABLE](https://www.postgresql.org/docs/current/sql-altertable.html) (OPS-09), adding a foreign key takes a lock on both tables. strong_migrations (OPS-08) flags this and notes that MySQL lacks an equivalent of deferred validation. pt-osc (M2) needs special handling, and one option leaves foreign keys pointing at a nonexistent table.
- Referential checks across shards require coordination. Bailis et al., [Highly Available Transactions](https://www.vldb.org/pvldb/vol7/p181-bailis.pdf) (2014; LIT-18), per the notes' annotation, informs which invariants need it.

**For retaining integrity.**
- Codd's [relational model](https://www.engineering.upenn.edu/~zives/03f/cis550/codd.pdf) (1970-06; DES-01) makes keys the means of expressing connections.
- Citus (T3) keeps composite foreign keys under distribution.
- GitLab (M3) keeps foreign keys at large scale, and invests in concurrent helpers and multi-release removal.
- Date's [SQL and Relational Theory](https://www.oreilly.com/library/view/sql-and-relational/9781491941164/copy.html) (2015; LIT-08, URL not verified by fetch) treats constraints as the primary expression of business rules, per the annotation.
- Financial cases (L2) argue for placing invariants in the data model.

**What the notes do not establish.** No fetched source reports measured foreign-key overhead. Figma, Notion and GitHub keep joins and transactions local, but the notes do not show they enforce foreign keys in the database. The topic 17 notes list ERP frameworks on the integrity side, yet Odoo's company check is ORM-level and no database-level foreign-key evidence for the four ERPs was captured.

**Scoped conclusion.**

| Practice | Label |
|---|---|
| Keep database-enforced keys and foreign keys within a single database or shard locality unless a documented reason exists | RECOMMENDED |
| Where foreign keys cross shard boundaries or are dropped, record who enforces the relationship and how drift is detected | MANDATORY as a design-record requirement (derived from Pinterest's listed costs) |
| Dropping foreign keys for performance without measured evidence | Not supported by these notes |
| Financial and ERP systems: keep invariants in the transactional store | RECOMMENDED; L2 and L4 support this for ledgers specifically |

### 10.3 Other disagreements

| Topic | Positions | Status |
|---|---|---|
| Clustering and auto-sharding | Pinterest 2012 rejected it; Slack and GitHub adopted Vitess; Discord and Square rely on distributed stores | Time- and maturity-dependent; Figma and Notion still chose custom layers |
| Sequential or random keys | Flickr rejected GUIDs on MySQL; Square uses UUIDs on Spanner; Figma hashes | Depends on engine placement |
| Native partitioning as shard unit | Notion used schemas; Figma used views | Neither used declarative partitioning as the sharding unit |
| Deletes | Ledgers forbid them; ERPs flag; Discord shows physical deletes are expensive in LSM stores | Domain-dependent. Retention and erasure need separate treatment (topic 14) |
| Backups | GitLab had none usable; GitHub's worked but slowly | Restore time and ownership are architecture concerns |
| Competing OLAP schools | Kimball, Inmon, Data Vault, Anchor | Selectable styles |

## 11. Recommended reading
Drawn only from topic 16 and the catalog. Authority values are the catalog's. *Verified* means a copy or publisher page was read as described; it does not mean every annotation detail was checked.

### Tier 1: read first

| Work | Catalog | Authority | Why | Caveat |
|---|---|---|---|---|
| Codd, [A Relational Model of Data for Large Shared Data Banks](https://www.engineering.upenn.edu/~zives/03f/cis550/codd.pdf) (1970-06) | DES-01 | 5 | Root of keys and data independence | Opening words of the primary-key passage confirmed by pdftotext (note 22); the curl link retest failed locally, so the link needs a manual check |
| Kent, [A Simple Guide to Five Normal Forms](http://www.bkent.net/Doc/simple5.htm) (1983-02) | LIT-06 | 5 | Practitioner normalization checklist | The well-known phrasing is a summary. Note 22: the served page literally reads "us the whole key", so quote only "the whole key, and nothing but the key" |
| Berenson et al., [A Critique of ANSI SQL Isolation Levels](https://arxiv.org/abs/cs/0701157) (1995-06) | LIT-16 | 5 | What isolation levels actually guarantee | None |
| Gray, [The Transaction Concept](https://jimgray.azurewebsites.net/papers/thetransactionconcept.pdf) (1981-06) | TXN-01 | 5 | Foundations and long-lived transactions | None |
| Kleppmann, [Designing Data-Intensive Applications](https://dataintensive.net/) (n.d. on site; 2017 per notes) | PIPE-21 | 4 | Bridge from papers to daily decisions | Chapter-level claims unverified |
| Kimball and Ross, [The Data Warehouse Toolkit](https://www.wiley.com/en-us/-p-9781118530801) (2013-07) | LIT-43 | 4 | Dimensional modelling | Publisher page only |
| Ambler and Sadalage, [Refactoring Databases](https://www.informit.com/store/refactoring-databases-evolutionary-database-design-9780321293534) (2006-03-03) | OPS-03 | 4 | Schema evolution playbook | Publisher page only |
| Fowler, [Patterns for Accounting](https://martinfowler.com/eaaDev/AccountingNarrative.html) (2006-01-24) | TEN-40 | 4 | Ledger correction strategies | First draft |

### Tier 2: by topic

| Topic | Work | Catalog | Authority | Caveat |
|---|---|---|---|---|
| Normalization | Date, [Database Design and Relational Theory](https://link.springer.com/book/10.1007/978-1-4842-5540-7) (2019-12) | LIT-07 | 4 | URL not fetched directly |
| Normalization | Codd, [Further Normalization](https://www.vldb.org/dblp/db/indices/a-tree/c/Codd:E=_F=.html) (1971) | LIT-02 | 5 | DBLP record only |
| Conceptual | Chen, [The Entity-Relationship Model](https://www.csc.lsu.edu/~chen/pdf/erd-5-pages.pdf) (1976-03) | LIT-03 | 5 | 5-page excerpt |
| Anti-patterns | Karwin, [SQL Antipatterns](https://pragprog.com/titles/bksap1/sql-antipatterns-volume-1/) (2022-10) | DES-13 | 4 | Publisher table of contents read for headings only (note 22); closure table and nested set were not found there, and remedy detail is unverified against the book |
| Indexing | Winand, [SQL Performance Explained](https://sql-performance-explained.com/) (2012) | LIT-13 | 3 | Year comes from the brief |
| Long transactions | Garcia-Molina and Salem, [Sagas](https://doi.org/10.1145/38713.38742) (1987) | LIT-17 | 5 | DOI redirect never loaded |
| Recovery | Haerder and Reuter, [Principles of Transaction-Oriented Database Recovery](https://doi.org/10.1145/289.291) (1983-12) | LIT-15 | 5 | DOI redirect never loaded |
| Distribution | Bailis et al., [Highly Available Transactions](https://www.vldb.org/pvldb/vol7/p181-bailis.pdf) (2014) | LIT-18 | 5 | None |
| Distribution | Abadi, [Consistency Tradeoffs](https://www.cs.umd.edu/~abadi/papers/abadi-pacelc.pdf) (2012-02) | TXN-14 | 5 | PACELC definition confirmed by pdftotext and may be quoted (note 22). Per-system classifications not checked and not used; curl link retest failed locally |
| Distribution | Kleppmann, [A Critique of the CAP Theorem](https://arxiv.org/abs/1509.05393) (2015-09-17) | TXN-16 | 4 | Preprint |
| Distribution | Gilbert and Lynch, [Brewer's Conjecture](https://www.comp.nus.edu.sg/~gilbert/pubs/BrewersConjecture-SigAct.pdf) (2002-06) | LIT-20 | 5 | Text layer is extractable and Theorem 1 is confirmed (note 22) |
| Distribution | Gilbert and Lynch, [Perspectives on the CAP Theorem](https://groups.csail.mit.edu/tds/papers/Gilbert/Brewer2.pdf) (2012) | LIT-21 | 5 | Title and authors confirmed (note 22); specific claims still unchecked |
| Stores | [Dynamo](https://www.allthingsdistributed.com/files/amazon-dynamo-sosp2007.pdf) (2007; LIT-25), [Bigtable](https://research.google/pubs/bigtable-a-distributed-storage-system-for-structured-data/) (2006; LIT-26), [Spanner](https://www.usenix.org/conference/osdi12/technical-sessions/presentation/corbett) (2012; LIT-27) | as listed | 5 | None |
| Internals | Petrov, [Database Internals](https://www.oreilly.com/library/view/database-internals/9781492040330/) (2019-10) | LIT-39 | 4 | Publisher blocked; URL not fetched |
| Architecture | Hellerstein et al., [Architecture of a Database System](https://www.emerald.com/ftdbs/article/1/2/141/1331441/Architecture-of-a-Database-System) (2007-11-07) | LIT-30 | 5 | Publisher page refuses automated access; link needs a manual check (note 22) |
| Direction | [What Goes Around Comes Around](https://15721.courses.cs.cmu.edu/spring2020/papers/01-intro/whatgoesaround-stonebraker.pdf) (2005; LIT-28); [... And Around](https://sigmodrecord.org/2024/06/30/what-goes-around-comes-around-and-around) (2024-06; LIT-29) | as listed | 5 | None |
| Scale-out | Pavlo and Aslett, [What's Really New with NewSQL?](https://db.cs.cmu.edu/papers/2016/pavlo-newsql-sigmodrec2016.pdf) (2016) | LIT-37 | 5 | None |
| OLAP engines | [Snowflake](https://www.cs.purdue.edu/homes/csjgwang/CloudNativeDB/SnowflakeSIGMOD16.pdf) (2016; LIT-34), [Dremel](https://research.google/pubs/dremel-interactive-analysis-of-web-scale-datasets-2/) (2010; LIT-33) | as listed | 5 | None |
| Warehousing | [ETL Toolkit](https://www.wiley.com/en-us/-p-9780764567575) (2004-10; LIT-44), LIT-45, LIT-47 | as listed | 4 | Publisher pages |
| Modelling | [Anchor Modeling](https://www.anchormodeling.com/publications/) (2010; LIT-48) | LIT-48 | 5 | Preprint listing |
| Patterns | Silverston, [Data Model Resource Book Vol. 1](https://www.wiley.com/en-us/-p-9780471380238) (2001-03; LIT-53); Hay, [Data Model Patterns](https://www.dorsethouse.com/books/dmp.html) (1996; LIT-56) | as listed | 4 | Contents from background, not fetched pages |
| Model review | Hoberman, [Data Model Scorecard](https://technicspub.com/data-model-scorecard/) (n.d. on page) | GOV-32 | 4 | Ten categories confirmed on page |
| Temporal | [Temporal Features in SQL:2011](https://sigmodrecord.org/publications/sigmodRecord/1209/pdfs/07.industry.kulkarni.pdf) (2012-09; GOV-06); Snodgrass, [Developing Time-Oriented Database Applications](https://www2.cs.arizona.edu/~rts/publications.html) (1999-07; LIT-59); [Bitemporal Data](https://shop.elsevier.com/books/bitemporal-data/johnston/978-0-12-408067-6) (2014-08-19; LIT-60) | as listed | 5, 4, 4 | None noted |
| Pipelines | [Kafka](https://people.csail.mit.edu/matei/courses/2015/6.S897/readings/kafka.pdf) (2011-06; LIT-62); [Dataflow Model](https://www.vldb.org/pvldb/vol8/p1792-Akidau.pdf) (2015; PIPE-17) | as listed | 4, 5 | Kafka via course copy |
| Pipelines | Reis and Housley, [Fundamentals of Data Engineering](https://www.oreilly.com/library/view/fundamentals-of-data/9781098108298/) (2022-06) | PIPE-22 | 4 | Publisher blocked |
| Operations | Campbell and Majors, [Database Reliability Engineering](https://www.oreilly.com/library/view/database-reliability-engineering/9781491925935/) (2017-10-26) | LIT-67 | 4 | Publisher blocked |
| Application | [PoEAA](https://www.informit.com/store/patterns-of-enterprise-application-architecture-9780321127426) (2002-11-05; LIT-68), [DDD](https://www.informit.com/store/domain-driven-design-tackling-complexity-in-the-heart-9780321125217) (2003-08-20; LIT-69), [Implementing DDD](https://www.informit.com/store/implementing-domain-driven-design-9780321834577) (2013-02-06; LIT-70) | as listed | 4 | Publisher pages |
| Governance | [DAMA-DMBOK](https://technicspub.com/?p=3334) (2017; LIT-73); Dehghani, [Data Mesh](https://www.oreilly.com/library/view/data-mesh/9781492092384/) (2022-03; LIT-74) | as listed | 4 | Data Mesh publisher blocked |

Omitted because no official page was verified: Date's *An Introduction to Database Systems*, 8th ed.

## 12. Lessons and evidence strength
*Verified case* means at least one grade A source. Counts include only verified sources.

| # | Lesson | Scope | Verified cases | Unverified support (not counted) | Strength | Label |
|---|---|---|---|---|---|---|
| 1 | Shard on a tenant-like key keeping joins and transactions local | OLTP | S1, S2, S6, S7 (T3 docs) | none | Verified case, strong | RECOMMENDED |
| 2 | Many logical shards per host | OLTP | S2, S3, S5 | CASE-20 | Verified case, moderate | RECOMMENDED |
| 3 | Include tenant key in primary and foreign keys | OLTP | S2 (retrospective) | none; T3 is docs | Verified docs plus one case | RECOMMENDED |
| 4 | Match key distribution to storage engine | OLTP | I1, I5 (S1, L2) | CASE-20 | Verified case, moderate | MANDATORY for distributed designs |
| 5 | Time-prefixed IDs where sortability matters | OLTP | S8; I2 docs | CASE-20 | Verified, limited | OPTIONAL/CONTEXTUAL |
| 6 | Dual write or log replay, batched backfill, read comparison | OLTP | S2, S3, S6, S8, M1 | none | Verified case, strong | RECOMMENDED |
| 7 | Expand, migrate, contract | OLTP | M1 (OPS-01, OPS-02, M3, M4) | none | Verified case plus literature, strong | MANDATORY for zero-downtime services |
| 8 | Budget lock time; per-version danger list | OLTP | M4 at grade C; M3, M7 docs | none | Verified docs, strong; values contextual | MANDATORY in principle |
| 9 | Lint partition boundaries before moving | OLTP | S4 | none | Single verified case | OPTIONAL/CONTEXTUAL |
| 10 | Balanced entries; correction by new entry; lifecycle states | OLTP+OLAP | L1, L2 (L4 docs, TEN-40; ERP-02, ERP-06, ERP-12 docs) | CASE-35 | Verified case, strong; ERP vendors have exceptions | MANDATORY for ledgers built on this invariant; RECOMMENDED for ERP general ledgers |
| 11 | Correctness as balance, timeliness, completeness | OLTP+OLAP | L1 | none | Single verified case | RECOMMENDED |
| 12 | Idempotency with stored fingerprint and recovery point | OLTP | L5 at grades B and C; L4 docs | none | Verified docs | MANDATORY for money movement |
| 13 | Non-transactional sequences cannot give gapless numbers; gap tolerance varies by jurisdiction | OLTP | TEN-33 engine fact; LEG-01, LEG-07, LEG-14 | German gap rule (LEG-06) search snippets only | Verified docs and law; implementation inferred | MANDATORY where applicable |
| 14 | Per-currency balance | OLTP | L4 docs only | none | Single vendor doc | RECOMMENDED |
| 15 | Fiscal period close control, gated and held below company grain | OLTP | none as cases; ERP-01, ERP-05, ERP-06, ERP-09, ERP-10, ERP-14, ERP-15, ERP-19 docs | none | Verified vendor docs, strong on grain; vendors disagree on permanent close; no case outcomes | RECOMMENDED |
| 16 | Bound partition size; deletes are writes in LSM | OLTP | S8 | none | Single verified case, repeated | RECOMMENDED for wide-column |
| 17 | Event log as source; decouple collection from serving | OLAP metadata | D1, D2 | none | Verified case, moderate | RECOMMENDED |
| 18 | Standard audit columns and tenant fields, framework-applied | OLTP | E1, E3, E4 docs; E2 timestamps unconfirmed (note 22) | iDempiere wiki excerpt | Verified docs, partial | RECOMMENDED |
| 19 | Tenant scope on every access path | OLTP | S7 (T1, T2, T3 docs) | none | Verified docs plus case | MANDATORY for multi-tenant |
| 20 | Restore ownership and rehearsed restore time | OLTP | P1, P2 | none | Verified case, strong | MANDATORY |
| 21 | Failover constrained by serveable topology | OLTP | P2 | none | Single verified case | RECOMMENDED |
| 22 | Engine trade-offs depend on workload | OLTP | 10.1, contested | none | Verified but disputed, no controlled data | OPTIONAL/CONTEXTUAL |
| 23 | Evolve the incumbent engine over a rewrite when runway is short | OLTP | S1, S2, S6, S4 | none | Verified, with survivorship bias | OPTIONAL/CONTEXTUAL |
| 24 | Tier certification; centralize metric definitions | OLAP | none | CASE-39, CASE-40 | **Unverified snippet only** | OPTIONAL/CONTEXTUAL |
| 25 | Model money as balanced events for reporting | OLTP to OLAP | L1 in part | CASE-35, CASE-36 | Partly verified; Airbnb detail **unverified snippet** | RECOMMENDED via L1 only |
| 26 | Instagram-style in-database ID generation | OLTP | none | CASE-20 | **Unverified snippet only** | No practice derived |
| 27 | Transaction-date rate attribution; rates keyed by pair, date and type | OLTP+OLAP | ERP-08, ERP-11, ERP-16, ERP-20 docs; ERP-22 and SEC order | none | Verified docs and one enforcement order; precision unsupported | MANDATORY in substance for US GAAP issuers; otherwise RECOMMENDED |
| 28 | Intercompany as linked entries balanced per entity | OLTP+OLAP | ERP-07, ERP-13 support, ERP-20 support docs | none | Verified docs, no case outcomes | RECOMMENDED |

## 13. Corrections applied and remaining gaps
**Corrections applied from `CORRECTIONS.md`, as updated by note 22.** Instagram date is n.d. and its late-2011 dating is dropped; RFC 9562 cites December 2012 and the post remains unread (see I3). It is not counted as evidence for lessons 2 and 4. Snowflake is not described as the template for other ID schemes, and Pinterest IDs are stated to have no time component. TAO is not described as running over sharded MySQL or a relational store. `NOT VALID` is attributed to OPS-09 and to Braintree 2019 (OPS-07), which note 22 confirmed. The topic 17 count is stated as 47 of 53. Removed: record-level versioning in ERP frameworks (not checked in note 22, no source to test) and the pre-PostgreSQL 11 attribution to the 2014 Braintree post (the version fact is credited to OPS-07 and OPS-09). Restored in source wording after note 22: the Discord tombstone lifespan change and Leach's time at Stripe. Frappe and iDempiere column claims are narrowed to what was seen, and Frappe `creation` and `modified` are marked unconfirmed. Literature caveats appear in section 11, and PACELC classifications are not used. Omitted as not found or not verified: Figma's Keeping Figma fast, Cloudflare, Stack Overflow, Netflix, Zalando, Spotify, Intuit, Monzo/Wise, Etsy, Instacart, DoorDash, Dolibarr, Heap.

**Additional adjustments made here.** LedgerStore is not counted as double-entry evidence, because the notes describe only its indexing. Topic 17's claim of B-tree motivation for Snowflake is not repeated. ERP frameworks are not cited for database-level foreign keys. Topic 14's MANDATORY labels for per-currency balance and single-entity posting are lowered under this file's single-source test.

**Remaining evidence gaps.**
- This file is research input, not legal advice. Legal and accounting content needs review by counsel.
- Fiscal period close and locking: vendor sources only. SAP product docs rendered empty, so SAP rests on training pages. NetSuite adjustment periods and year-end, and Fusion year-end, were not established.
- Standards: the FASB Codification and PCAOB standards pages returned 403, IAS 21 and IFRS 10 full text were not read, 17 CFR 210.3A-04 and GoBD could not be read, and ISA 240 was not retrieved. ASC 830 is known only through FAS 52 and an SEC order.
- ERPNext Immutable Ledger: named in the docs, page not found.
- Exchange-rate design: no source states a rate precision or describes triangulation. SAP's valid-from rule was not established.
- Invoice numbering gaps: the German gap rule rests on search snippets, because UStAE 14.5(10) could not be opened. Italy, Spain, Pakistan and the UAE have no gap statement in the sources read. France has no official text on spoiled numbers. ViDA national transposition was not researched.
- Citation conflicts left open: Pakistan e-invoicing start dates (SRO 709(I)/2025 snippet against the FBR FAQ) and the UAE Art. 59 amendment (Cabinet Decision No. 100 of 2024 against 2025).
- Gapless counter throughput at scale: no case.
- Foreign-key overhead: no measured data.
- Odoo inter-company and consolidation pages, official SAP company code definition: not read.
- GitHub's horizontal-sharding follow-up and the 2016 gh-ost announcement: not fetched.
- Instagram, Airbnb and the Pinterest 2015 post need re-verification by a method that can reach those pages; note 22 could not. The Uber posts need a manual link check.
- Catalog gaps: GitLab NOT NULL constraints, pt-online-schema-change and PlanetScale Safe migrations are cited from topic 13 but have no catalog ID.
