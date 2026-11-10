# 17. Case Studies from Official Engineering Blogs, Conference Talks, and Open-Source ERP Schemas

Scope: documented, real production decisions about keys, sharding, migrations, ledgers, multi-tenancy, audit and data quality, taken only from official company engineering blogs, company-hosted or recognized-conference talks, official open-source repositories/docs, and official postmortems. Verified 2026-11-07 (see `catalog_17_case_studies.json` for per-resource verification flags).

Method and verification notes:
- 41 of the 45 catalogued resources were opened directly (WebFetch) and their content read; two conference/talk slide decks (Pinterest QCon SF 2012, Pettus Percona Live 2017) were downloaded as PDFs and text-extracted.
- Medium-hosted official publications (Pinterest Engineering 2015 post, Instagram Engineering, Airbnb Engineering) returned HTTP 403 to every fetch path tried (direct, reader proxy, Internet Archive). Their URLs were returned verbatim by WebSearch and are listed with `url_verified=false`; only what the search excerpts stated is reported for them, with the caveats noted. The Pinterest design was instead verified from the official QCon SF 2012 slide deck.
- The iDempiere wiki returned 403; the official project Javadoc (jenkins-artifacts.idempiere.org) was used instead.
- Dates are given as shown on the page; "n.d." where the page shows none.

---

## Theme A. Scaling relational databases: sharding, partitioning, and keys/IDs

### Takeaway
Across Figma, Notion, GitHub, Slack, Shopify, Pinterest, Discord and Uber, the consistent pattern is: (1) exhaust vertical scaling and vertical (table-group) partitioning first; (2) pick a tenant-like sharding key (workspace, shop, org/file/user, channel) that keeps most joins and transactions local; (3) prefer many logical shards mapped to few physical hosts so capacity can be added by moving logical shards, not re-keying data; (4) migrate with dual-write or log replay + backfill + dark-read verification; (5) encode shard/time into 64-bit IDs rather than depend on per-database auto-increment. Teams repeatedly rejected NewSQL/NoSQL rewrites as higher-uncertainty than extending their existing engine, but were split on build (Figma, Notion, Pinterest) vs. adopt (Slack, GitHub chose Vitess).

### Cases

#### A1. Figma: horizontal sharding of RDS Postgres (2024)
Source: [How Figma's databases team lived to tell the scale](https://www.figma.com/blog/how-figmas-databases-team-lived-to-tell-the-scale/) — Sammy Steele, March 14, 2024.
- Problem: database stack grew almost 100x from 2020 (a single Postgres on AWS's largest instance) to 2024; some tables reached several TB and billions of rows; vacuum hurt reliability; highest-write tables neared RDS max IOPS; vertical partitioning was exhausted because "the smallest unit of partitioning is a single table."
- Decision: horizontal sharding on top of the existing vertically partitioned RDS fleet. Key constructs: "colos" (groups of related tables that share a sharding key and physical layout so joins/transactions remain possible within one key); sharding keys such as UserID, FileID, OrgID; routing on a hash of the key "to avoid hotspots from sequential IDs"; logical sharding first (Postgres views over unsharded data, rolled out and rolled back by configuration) and physical sharding later; DBProxy (Go) with query parser, logical and physical planners and load-shedding; full logical replication of the dataset to each shard, then restricting reads/writes to that shard's subset; no atomic cross-shard transactions; a query language covering roughly the most common 90% of queries, chosen by "shadow planning" on live production traffic.
- Alternatives rejected: CockroachDB, TiDB, Spanner, Vitess (complex data migration plus loss of Postgres expertise, judged too risky with months of runway); NoSQL (would require rewriting most of the backend).
- Outcome: first horizontally sharded table shipped September 2023, about nine months end-to-end; failover caused ~10 seconds of partial primary unavailability and no replica impact; view overhead under 10% worst case; no latency/availability regressions.
- Lesson (OLTP): incremental, reversible steps; tailor the sharding layer to your own query mix instead of building a general database; the team "favored known low-risk solutions over potentially easier options with much higher uncertainty."

#### A2. Notion: application-level sharding by workspace (2021)
Source: [Herding elephants: Lessons learned from sharding Postgres at Notion](https://www.notion.com/blog/sharding-postgres-at-notion) — Garrett Fidalgo, October 6, 2021.
- Problem: a single Postgres monolith had served about five years and four orders of magnitude of growth; autovacuum kept stalling; transaction-ID wraparound became an "existential threat to the product."
- Decision: application-level sharding with workspace ID as partition key (every block belongs to exactly one workspace); shard every table reachable from `block` via foreign keys; 480 logical shards across 32 physical databases (15 per database), each logical shard a Postgres schema; 480 chosen because it has many factors (hosts can grow 32→40→48, whereas 512 would force 64 hosts); limits of 500 GB/table, 10 TB/physical DB, ≥60K IOPS; separate tables rather than native partitioning to keep a single routing source in the application.
- Alternatives rejected: vertical scaling; Citus and Vitess (clustering logic too opaque, team wanted control over distribution); DynamoDB (too risky); bare-metal NVMe (backup/replication maintenance).
- Migration: direct dual writes were "too flaky" and logical replication could not keep up with `block` write volume during the snapshot, so writes were replayed from an audit log by a catch-up script (a reverse audit log was prepared for rollback); ~3-day backfill on an m5.24xlarge comparing record versions; verification by sampling UUIDs/adjacent ranges and "dark reads" that read both stores and logged discrepancies; migration and verification logic written by different people.
- Outcome: five minutes of scheduled maintenance for the switchover; users noticed the speedup.
- Lesson (OLTP): shard earlier (late sharding left no headroom for migration load); aim for zero downtime; "use a combined primary key" merging old PK and partition key so `space_id` need not be threaded through the application.

#### A3. Notion: re-sharding 32→96 databases with zero downtime (2023)
Source: [The Great Re-shard: adding Postgres capacity (again) with zero downtime](https://www.notion.com/blog/the-great-re-shard) — Arka Ganguli, Tanner Johnson, Ben Kraft, Nathan Northcutt, July 17, 2023.
- Problem: by late 2022 some of the 32 shards exceeded 90% CPU at peak, many neared provisioned IOPS, and PgBouncer hit connection limits before an expected new-year spike.
- Decision: triple the fleet to 96 machines (15→5 logical schemas each) using smaller instances; Postgres logical replication (3 publications × 5 schemas per source); skipping index creation during the copy and rebuilding afterwards cut sync from 3 days to 12 hours; PgBouncer re-architected into groups (one cluster per unsharded DB plus four clusters of 24 space-shard DBs) because ~100 PgBouncers × 6 connections per shard already meant ~600 connections per shard; dark reads comparing ≤5-row queries on a sample with a 1-second delay; a four-step failover (pause via PgBouncer, verify replication caught up, flip shard map and reverse replication for rollback, resume) rehearsed in staging.
- Alternative rejected: vertical scaling (would hit the same limits; horizontal allows per-shard sizing).
- Outcome: "no report or observation in our metrics of perceived user downtime"; worst case ~1 second of a saving spinner; peak CPU/IOPS dropped to ~20%; spreading load exposed outlier workspaces.
- Lesson (OLTP): the connection-pool layer is itself a scaling dimension; re-sharding is repeatable if logical shards > physical hosts.

#### A4. GitHub: partitioning MySQL by schema domains, then Vitess (2021)
Source: [Partitioning GitHub's relational databases to scale](https://github.blog/2021-09-27-partitioning-githubs-relational-databases-scale/) — Thomas Maurer, September 27, 2021 (updated March 2, 2022).
- Problem: core features (users, repositories, issues, pull requests) lived on one MySQL cluster `mysql1`; "Any sort of incident negatively affecting `mysql1` would affect all features that stored their data on this cluster."
- Decision: "schema domains" declared in `db/schema-domains.yml` with a linter requiring every table to belong to a domain; a query linter flagging joins across domains; a sampled production transaction linter catching cross-domain transactions; vertical partitioning by moving whole domains with Vitess VReplication, plus an in-house write-cutover using MySQL replication and ProxySQL routing as a second, independent tool.
- Alternatives considered: replacing joins with preload/application-side joins shipped behind Scientist experiments; Rails `disable_joins`; moving polymorphic data (e.g., `reactions`) into same-domain tables to keep transactional consistency; Vitess vs. in-house cutover (Vitess adoption was early in 2020).
- Outcome: 2019 `mysql1` averaged 950K queries/s (900K replicas, 50K primary); by 2021 the same tables spread across clusters served 1.2M queries/s with per-host load halved; the write-cutover moved 130 busy tables at once with a cutover of tens of milliseconds.
- Lesson (OLTP): enforce partition boundaries with linters before moving data; application-side joins can be more predictable than the optimizer; keep two independent migration tools; "boring" technology plus small code changes scaled.

#### A5. Pinterest: manual ID-sharded MySQL, no joins, mapping tables (QCon SF 2012; 2015 recap)
Sources: [Scaling Pinterest (QCon SF 2012 slides)](https://qconsf.com/sf2012/dl/qcon-sanfran-2012/slides/MartyWeiner_and_YashwanthNelapati_ScalingPinterest.pdf) — Marty Weiner, Yashh Nelapati, November 9, 2012 (conference-hosted; text-extracted). The 2015 recap [Sharding Pinterest: How we scaled our MySQL fleet](https://medium.com/pinterest-engineering/sharding-pinterest-how-we-scaled-our-mysql-fleet-3f341e96ca6f) could not be fetched (HTTP 403); per search excerpt it says the design went live early 2012 and still stores core data.
- Problem: Jan 2012 infrastructure had "5 Functionally Sharded MySQL DB + 9 read slaves, 4 Cassandra Nodes, 15 Membase Nodes (3 separate clusters), ... 3 Mongo Clusters" run by 3 engineers; lesson #1: "It will fail. Keep it simple."
- Decision: sharding over clustering. Clustering (Cassandra, Membase, HBase) was "Still fairly young", "Fundamentally complicated", with "a single point of failure. A BIG one" (the cluster manager: "Data corruption across all nodes", "Improper balancing that cannot be fixed"). Lesson #2: "Clustering is scary." Sharding pros: "Algorithm for placing data is very simple", "ID generation is simplistic". Transition path: "1 DB + Foreign Keys + Joins → 1 DB + Denormalized + Cache → 1 DB + Read slaves + Cache → Several functionally sharded DBs + Read slaves + Cache → ID sharded DBs + Backup slaves + Cache." Initially 8 physical servers × 512 databases = 4096 shards, master-master replication; capacity added by replicating a server and handing half its databases to the replica ("Data DOES NOT MOVE"). 64-bit ID = Shard ID | Type | Local ID, with ID space for 65,536 shards and a server→shard-range lookup map cached in every app process; local IDs by auto-increment; new users randomly distributed, boards/pins co-located with the user. Object tables store `Local ID → MySQL blob (JSON / Serialized thrift)`; mapping tables (`user_has_boards`, `pin_has_likes`, naming `noun_verb_noun`) store `Full ID → Full ID (+ timestamp)`; "Queries are PK or index lookups (no joins)"; "All tables exist on all shards"; "No schema changes required (index = new table)". Why MySQL: "Rarely catastrophic loss of data", "Response time to request rate increases linearly", Percona support.
- Costs acknowledged: "Cannot perform most JOINS", "No transaction capabilities", "Extra effort to maintain unique constraints", "Schema changes requires more planning", "Reports require running same query on all shards"; "Sharding makes schema design harder" but "Waiting too long makes the transition harder"; advice: "Remove all joins and complex queries, add cache", "Functionally shard as much as possible", then shard by ID if still growing.
- Outcome: Oct 2012: 80 MySQL DBs (cc2.8xlarge) + 1 slave each, 110 Redis, 200 Memcache; migration of 500M pins and 1.6B follower rows via a scripting farm.
- Lesson (OLTP): a manual, static shard map plus shard-encoded IDs trades away joins/transactions/unique constraints for operational predictability; the 2012 "clustering is scary" verdict is time-bound (contrast A6, A9, C2).

#### A6. Slack: Vitess over workspace-sharded MySQL (2020)
Source: [Scaling Datastores at Slack with Vitess](https://slack.engineering/scaling-datastores-at-slack-with-vitess/) — Arka Ganguli, Guido Iaquinti, Maggie Zhou, Rafael Chacón, December 1, 2020.
- Problem: all of a workspace's data lived on one MySQL shard; the largest customers hit the largest hardware; hot spots alongside underutilized shards; a shard outage took down every workspace on it; the application routed directly to database hosts, so replicas were hard to use safely.
- Decision: Vitess, keeping MySQL as storage/replication engine while adding horizontal sharding, failover, backups and topology management; different keyspaces sharded by different keys (users, teams, channels), e.g., messages by channel ID so one huge customer does not sit on one shard; first migrated feature (RSS-to-channel) used backfill, double-writes and double-reads against legacy stores; Slack contributed topology, MySQL-compatibility and migration tooling upstream.
- Alternatives rejected: sharding inside the application (prototypes showed heavy coupling of app logic to storage layout, no help with operational issues); DynamoDB/Cassandra and Spanner/CockroachDB (too disruptive to leave MySQL and the relational model).
- Outcome: 99% of MySQL query load on Vitess; 2.3M QPS peak (≈2M reads, 300K writes); median 2 ms, p99 11 ms; absorbed +50% QPS in one week of March 2020 via resharding workflows; underpins data residency across six regions.
- Lesson (OLTP): per-table choice of sharding key is the central design decision; adopting a sharding middleware means rebuilding provisioning, discovery, backup and credential processes.

#### A7. Shopify: pods as the unit of isolation and failover (2018)
Source: [A Pods Architecture To Allow Shopify To Scale](https://shopify.engineering/a-pods-architecture-to-allow-shopify-to-scale) — Xavier Denis, March 2, 2018.
- Problem: Shopify sharded in 2015 when it could no longer buy a bigger server, but "what we gained in performance and scalability we lost in resilience": shared code ran actions across all shards, so one failed shard could make an action unavailable platform-wide.
- Decision: a pod is a group of shops on a fully isolated set of datastores; shared workers/app servers/load balancers talk to one pod at a time; "we don't allow any actions to reach across pods"; each request/job is bound to one pod; a routing layer ("Sorting Hat") tags each request with its pod; every pod has an active and a recovery data center; "Pod Mover" relocates a pod in about a minute without dropping requests or jobs, used daily.
- Outcome: qualitative — pods became the basis of resiliency, disaster recovery and scaling; adding a pod does not interfere with existing ones.
- Lesson (OLTP): sharding for capacity is not the same as isolating for resilience; make the tenant group the unit of both failover and scaling.

#### A8. Uber: Postgres → MySQL (Schemaless) and the community rebuttals (2016–2017) — CONTESTED
Uber's position: [Why Uber Engineering Switched from Postgres to MySQL](https://www.uber.com/blog/postgres-to-mysql-migration/) — Evan Klitzke, July 26, 2016; [Designing Schemaless, Uber Engineering's Scalable Datastore Using MySQL](https://www.uber.com/blog/schemaless-part-one-mysql-datastore/) — Jakob Holdgaard Thomsen, January 12, 2016.
- Problem (Uber): in early 2014 "we simply couldn't store enough trip data with Postgres"; requirements were linear scalability, write availability, change notification, secondary indexes and operational trust. The 2016 post lists Postgres limitations: write amplification ("an update to a field that is only covered by a single index must be propagated into all 12 indexes"); verbose physical WAL replication that struggled cross-country; a 9.2 replication bug returning duplicate rows; replicas that must cancel queries or delay WAL replay ("replica MVCC"); major-version upgrades requiring hours of downtime (legacy instances stuck on 9.2 while 9.5 was GA); process-per-connection scaling to only a few hundred connections, with "idle in transaction" bugs causing extended downtime despite pgbouncer.
- Decision: Schemaless, "an append-only sparse three dimensional persistent hash map" on sharded MySQL/InnoDB: immutable JSON cells keyed by (row key, column name, ref key); buffered writes; triggers (pub/sub on changes); global eventually consistent secondary indexes sharded by a designated field, with lag "well below 20ms" in most cases. MySQL reasons: secondary indexes point to the PK so updates touch only changed indexes; compact logical replication; true replica MVCC; rolling upgrades via logical replication; InnoDB buffer pool; thread-per-connection to ~10K connections.
- Alternatives rejected (Schemaless post): Cassandra, Riak, MongoDB — none met all five requirements in the available timeframe (notifications would be application-level; scatter-gather index queries slow; limited operational familiarity). Uber later adopted Cassandra and Riak elsewhere.

Rebuttals (PostgreSQL community):
- [On Uber's Choice of Databases](https://use-the-index-luke.com/blog/2016-07-29/on-ubers-choice-of-databases) — Markus Winand, July 29, 2016: the findings apply to an UPDATE-heavy use case, not Postgres generally ("Sadly, the only thing that sticks in the reader's mind is that PostgreSQL is lousy"); HOT avoids index writes only when no indexed column changes; the InnoDB secondary-index penalty Uber calls "slight" is significant for secondary-key queries; the "B-tree rebalancing" framing is a misconception; Uber mentions only one of two replica-conflict remedies (delayed replay) and omits `hot_standby_feedback`; "I believe Uber did not replace PostgreSQL by MySQL as their article suggests" — they built Schemaless, for which InnoDB is a better substrate.
- [Thoughts on Uber's List of Postgres Limitations](https://www.enterprisedb.com/blog/thoughts-ubers-list-postgres-limitations) — Simon Riggs, August 2, 2016: HOT (8.3, 2007) and the visibility map (2008) address the write/vacuum critique; indirect indexes are feasible as an option; the replication critique compares logical to physical replication, and Postgres offers both (pglogical, logical replication slated for 10); `hot_standby_feedback = on` (since 9.1) prevents replay conflicts in normal conditions — "PostgreSQL replicas certainly allow access to data with full MVCC semantics"; `pg_upgrade -k` and logical-replication upgrades address downtime.
- [A PostgreSQL Response to Uber](https://thebuild.com/blog/2017/04/28/a-postgresql-response-to-uber) — Christophe Pettus, April 28, 2017, with [slides from Percona Live 2017](https://thebuild.com/presentations/uber-perconalive-2017.pdf) (also given as "Why Uber Was (Mostly) Wrong", PGDay Nordic 2017). Scorecard: write amplification "Half-True, Half-False" (true that every index is updated when an indexed column changes and old versions persist until vacuum; but HOT exists, autovacuum has not needed full scans "for years and years", and MySQL's design needs a rollback area and two index operations per non-PK lookup); replication "Apples and Oranges" (MySQL logical vs. Postgres binary; logical replication tools have long existed, plugin since 9.4, core in 10); corruption bug: "I would not call MySQL bug free"; replica MVCC: configurable — run a "close" replica for failover and a "delayed" replica for queries; note Uber admitted long-running transactions from ORM-obscured code; upgrades "Half-True" (no in-place major upgrade; same logical-replication upgrade process is possible); buffers and connections "Mostly True" but of unquantified impact, and pgbouncer exists. Closing: "Uber identified some real pain points with PostgreSQL", yet there was "remarkably little quantitative information", "They had already made a decision to move to a schema-less architecture", and the real message was "MySQL handles our devs' bugs better."
- Transferable lesson (OLTP): the storage-engine choice interacts with the UPDATE pattern (many indexes on frequently updated rows amplify writes under heap+direct-index designs, while clustered-PK engines penalize secondary lookups), with the replication model (physical vs. logical), and with connection discipline (ORM-held transactions). Uber's valid pain points were real but specific; the general claim was overstated, and the actual fix was a new data model (Schemaless) more than an engine swap.

#### A9. Discord: MongoDB → Cassandra (2017) → ScyllaDB (2023)
Sources: [How Discord Stores Billions of Messages](https://discord.com/blog/how-discord-stores-billions-of-messages) — Stanislav Vishnevskiy, January 13, 2017; [How Discord Stores Trillions of Messages](https://discord.com/blog/how-discord-stores-trillions-of-messages) — Bo Ingram, March 6, 2023.
- Problem (2017): a single MongoDB replica set with an index on (channel_id, created_at); at ~100M messages (Nov 2015) data and index exceeded RAM and latency became unpredictable; ~50/50 read/write with highly random reads; planned features (mentions, pins, search) would add more random reads. Requirements: linear scalability, automatic failover, low maintenance, proven, predictable performance (alert when API p95 > 80 ms), no Redis/Memcached cache layer, not a blob store, open source.
- Decision (2017): Cassandra with primary key `((channel_id, bucket), message_id)` — partition = channel plus ~10-day time bucket sized to keep partitions under 100 MB; clustering key = Snowflake message ID (time-sortable); recent-message loads walk buckets backwards; dark launch with double reads/writes to MongoDB and Cassandra for about a week. MongoDB sharding rejected as complicated and unstable.
- Problems found: edit/delete races under eventual consistency left rows with only PK + text (fix: treat null `author_id` as deleted); writing nulls created tombstones (average message set 4 of 16 columns → 12 needless tombstones; fix: write only non-null values); a channel where millions of messages had been deleted took 20 seconds to load with 10-second GC pauses from tombstone scans (fixes: `gc_grace_seconds` 10 days → 2 days with nightly repairs; track empty buckets per channel).
- Outcome (2017): sub-millisecond writes, <5 ms reads; from >100M total to >120M messages/day; 12 nodes, RF 3, ~1 TB compressed per node; the whole live dataset moved to Cassandra.
- Problem (2023): the messages cluster had grown to 177 Cassandra nodes holding trillions of messages; hot partitions (one hot channel-bucket raised latency cluster-wide because quorum reads/writes hit the same replicas); JVM GC pauses requiring manual reboots; compaction backlog handled by a "gossip dance"; "our on-call team was frequently paged for issues with the database."
- Decision (2023): ScyllaDB (C++, no GC) plus Rust "data services" between the API monolith and the database with roughly one gRPC endpoint per query, request coalescing (concurrent requests for the same row share one query) and consistent-hash routing by channel ID; partition key unchanged. Migration: dual writes; the vendor's Spark migrator estimated ~3 months, a Rust migrator written in an afternoon took 9 days at up to 3.2M messages/s with SQLite checkpoints; it stalled at 99.9999% on huge uncompacted tombstone ranges; validation by sending a sample of reads to both stores; cutover May 2022.
- Outcome (2023): 177 → 72 nodes (~9 TB/node vs ~4 TB); historical read p99 40–125 ms → ~15 ms; insert p99 5–70 ms → steady 5 ms; "a quiet, well-behaved database".
- Lesson (OLTP, wide-column): partition design must bound partition size and hot-key exposure; deletes in LSM stores are writes (tombstones) and can dominate reads; the database swap alone did not fix hot partitions — upstream coalescing/routing did; large migrations fail on edge cases that appear only at full scale.

#### A10. Flickr: ticket servers for globally unique keys across shards (2010)
Source: [Ticket Servers: Distributed Unique Primary Keys on the Cheap](https://code.flickr.net/2010/02/08/ticket-servers-distributed-unique-primary-keys-on-the-cheap/) — posted by Kay Kremerskothen, February 8, 2010.
- Problem: data sharded across many MySQL master-master pairs; keys must be unique across all shards so records can migrate without collision; MySQL auto-increment cannot guarantee that across databases.
- Decision: dedicated ticket servers with a one-row table per ID type (`Tickets64(id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY, stub CHAR(1) UNIQUE)`), issuing IDs with `REPLACE INTO Tickets64 (stub) VALUES ('a'); SELECT LAST_INSERT_ID();`; two servers split parity via `auto-increment-increment = 2` and offsets 1/2, clients round-robin; separate sequences for photos, accounts, offline tasks, groups.
- Alternatives rejected: GUIDs ("index badly in MySQL", too large for memory-resident indexes, and sequential IDs help reporting/debugging); consistent hashing (suits write-cheap LSM stores, not MySQL's random-read strengths); one central auto-increment database (would grow unmanageably).
- Outcome: in production since January 13, 2006; "works shockingly well"; the two servers drift by a few hundred thousand IDs, which "hurts no one".
- Lesson (OLTP): a tiny, replicated-by-parity sequence service gives globally unique, roughly sequential integer keys without coordination or replication; "dumbest possible thing that will work".

#### A11. Twitter Snowflake: uncoordinated, time-sortable 64-bit IDs (2010)
Sources: [twitter-archive/snowflake](https://github.com/twitter-archive/snowflake) (archived September 18, 2021; original code under tag `snowflake-2010`) and its [2010 README](https://raw.githubusercontent.com/twitter-archive/snowflake/snowflake-2010/README.mkd).
- Problem: Twitter was moving from MySQL to Cassandra — "There is no sequential id generation facility in Cassandra, nor should there be."
- Decision: a Thrift network service generating 64-bit IDs = 41 bits of millisecond time from a custom epoch (~69 years) | 10 bits configured machine ID (1,024 generators) | 12 bits sequence (4,096 IDs per machine per millisecond); generators do not coordinate; IDs are k-sortable (ordered within a 1-second bound, goal tens of ms); generation refuses to proceed if the clock moves backwards; NTP must never step the clock back.
- Outcome: retired as a release but the scheme became the template for Instagram's in-database variant (A12), Discord's message IDs (A9) and Pinterest's shard-encoded IDs (A5).
- Lesson (OLTP/streaming): embed time in the high bits for sortability/locality and a generator/shard ID for uniqueness; reserve bits for growth.

#### A12. Instagram: Snowflake-style IDs generated inside PostgreSQL (c. 2011) — URL not fetchable
Source: [Sharding & IDs at Instagram](https://instagram-engineering.com/1cf5a71e5a5c) (official Instagram Engineering publication; every fetch path returned 403/connection refused; URL returned verbatim by WebSearch). Note: the accompanying Hacker News thread (news.ycombinator.com item 3058327) dates discussion to late 2011, so the "2012" date in the brief is doubtful; treat the date as unverified.
- What the search excerpt confirms: the post covers sharding Postgres data and generating unique IDs across shards, and states that "if you use a timestamp as the first component of the ID, the IDs remain time-sortable". Secondary summaries describe a 64-bit ID of 41 bits timestamp, 13 bits logical shard ID and 10 bits per-shard sequence, generated by a PL/pgSQL function with thousands of logical shards (Postgres schemas) mapped to fewer physical servers. These specifics were NOT verified against the original in this session.
- Lesson (OLTP, if confirmed): ID generation can live in the database itself (no extra service) while still encoding time and logical shard; logical-shard-in-ID lets shards move between hosts without rewriting keys.

#### A13. Facebook TAO: objects-and-associations store over sharded MySQL (ATC 2013)
Source: [TAO: Facebook's Distributed Data Store for the Social Graph](https://www.usenix.org/conference/atc13/technical-sessions/presentation/bronson) — Bronson et al., USENIX ATC '13, 2013.
- Problem/decision (abstract): "a simple data model and API tailored for serving the social graph" and TAO, "a geographically distributed data store that provides efficient and timely access to the social graph," deployed in place of memcache for data types fitting its model.
- Outcome: runs on thousands of machines over many petabytes; "TAO can process a billion reads and millions of writes each second."
- Lesson (OLTP): a deliberately restricted graph API (objects, associations) over a relational store enables caching and geo-distribution that a general SQL surface would not; the full paper (PDF) should be consulted for sharding-by-object-id and consistency details, which the abstract page does not state.

### Inferences (Theme A)
- Every team that stayed relational chose a tenant-like key that makes most transactions single-shard; Figma's "colos", GitHub's "schema domains", Notion's "tables reachable from block via FKs" and Citus's co-location (E3) are the same idea under different names.
- Logical shards >> physical hosts (Notion 480/32, Pinterest 4096/8, Instagram thousands) is the enabling design for cheap re-sharding; both Notion re-shards relied on it.
- Verification is never skipped: dual/double reads and dark reads appear at Notion (twice), Slack, Discord (twice), Stripe (B1) and GitHub (Scientist).
- Key design is storage-engine dependent: B-tree engines (Flickr, Snowflake, Instagram) favor monotonic keys; range-partitioned distributed stores (Square on Spanner, B3) and hash-routed shards (Figma) avoid them.

### Gaps (Theme A)
- Instagram's exact bit layout and PL/pgSQL function were not verified (fetch blocked).
- GitHub's horizontal-sharding follow-up post referenced in A4 was not located.
- Figma's "Keeping Figma fast" (2020) and Cloudflare's Postgres cluster post were not fetched/verified and are omitted.
- Stack Overflow's architecture posts live on a personal blog (nickcraver.com) and were omitted under the official-sources constraint.

---

## Theme B. Schema change and data migration at scale

### Takeaway
All verified sources converge on the same expand/migrate/contract choreography: add the new structure, dual-write, backfill in batches, verify (ideally with a read-comparison harness), switch reads, switch writes, then remove the old structure in a later release. Tooling differs (Stripe's four steps with Scientist; gh-ost's binlog-based ghost table; GitLab's multi-release helpers; PlanetScale's branch/deploy-request workflow), and operations that take long locks (unqualified `CREATE INDEX`, type changes, `NOT NULL`, defaults on old Postgres) are explicitly forbidden.

### Cases

#### B1. Stripe: four-step online migration of hundreds of millions of Subscriptions (2017)
Source: [Online migrations at scale](https://stripe.com/blog/online-migrations) — Jacqueline Xu, February 2, 2017.
- Problem: move subscriptions out of the Customer record into their own table — "hundreds of millions of Subscriptions objects" — while the API stays available and consistent.
- Decision: (1) dual write to old and new stores and backfill existing records offline (Hadoop/Scalding); (2) change all read paths, comparing both stores with GitHub's Scientist library so mismatches alert engineers without affecting the request; (3) change all write paths to write new-first and archive old; (4) remove old data lazily. A Scalding job confirmed no subscription was missing from the new table.
- Outcome: the new table became the source of truth and the `subscriptions` array was removed from Customer.
- Lesson (OLTP): phase the migration; do heavy verification offline; "We never attempted to change more than a few hundred lines of code at one time"; make every step observable.

#### B2. GitHub gh-ost: triggerless online schema change (2016–)
Source: [github/gh-ost](https://github.com/github/gh-ost) README (official repository; the 2016 announcement post on github.blog was rate-limited and not fetched).
- Problem: trigger-based online schema change tools were "the source of many limitations and risks" (the README's phrase).
- Decision: create a ghost table, copy rows incrementally, capture ongoing changes from the binary log and apply them asynchronously, then swap tables at cut-over; features: true pause (throttling stops all writes to the primary), dynamic reconfiguration, auditing over a socket, postponable cut-over, running the full flow on a replica for testing, hooks.
- Lesson (OLTP): decouple change capture from the production table (binlog, not triggers) so migrations are pausable, testable and low-impact.

#### B3. GitLab: codified zero-downtime migration rules (official development docs)
Source: [Avoiding downtime in migrations](https://docs.gitlab.com/ee/development/database/avoiding_downtime_in_migrations/) — GitLab Docs, n.d.
- Rules: dropping a column spans three releases (ignore in the model with `remove_with`/`remove_after`, drop in a post-deployment migration next release, remove the ignore rule after that) — "Dropping a column before properly ignoring it in the model can cause problems with zero-downtime migrations"; rename with `rename_column_concurrently` (keeps data in sync, copies indexes and FKs) then `cleanup_concurrent_column_rename`; add `NOT NULL` only in a post-deployment migration after app changes ship; change types with `change_column_type_concurrently` + cleanup (with `type_cast_function` when casting, e.g., text→jsonb); defaults via `SafelyChangeColumnDefault`; indexes via `add_concurrent_index`; drop FKs one per post-deployment migration inside `with_lock_retries` before dropping tables; very large tables (e.g., integer→bigint PKs) use batched background migrations across releases N (initialize), N+1 (swap), N+2 (remove triggers/old columns); renaming tables and JSON schema property changes also require multi-release sequences.
- Lesson (OLTP): schema evolution is a release-management process, not a single DDL; application code must tolerate both schema versions during the window.

#### B4. PlanetScale deploy requests: branch-and-review schema workflow (official docs)
Source: [Deploy requests](https://planetscale.com/docs/concepts/deploy-requests) — PlanetScale Docs, n.d.
- Design: schema changes flow from a development branch into a production branch via a deploy request showing a diff; the target branch must have "safe migrations" enabled; deployability checks warn about data loss; optional admin approval; the change is applied non-blocking by copying affected tables, syncing, then swapping; reverts possible for "up to 30 minutes" with intervening writes retained; "gated deployments" let an operator click to perform the final swap.
- Lesson (OLTP): treat schema like code (branch, diff, review, revertable deploy); keep a revert path that preserves data written in the interim.

#### B5. Shopify Ghostferry: live data movement between MySQL instances (official repo)
Source: [Shopify/ghostferry](https://github.com/Shopify/ghostferry) README, n.d. — "The swiss army knife of live data migrations"; it can "selectively copy data from one mysql instance to another" with little downtime, inspired by gh-ost but copying across databases and able to copy partial datasets (example tool `ghostferry-copydb`; a `sharding` directory exists but the README does not describe it).
- Lesson (OLTP): the same binlog-copy pattern used for schema change also moves tenants/shards between databases, which is the operational complement of Shopify's pods (A7).

#### B6. Braintree: safe vs. unsafe PostgreSQL schema operations (2014)
Source: [Safe Operations For High Volume PostgreSQL](https://pgrs.net/2014/05/14/safe-operations-for-high-volume-postgresql/) — Paul Gross, May 14, 2014 (cross-posted to Braintree's blog; author's own site).
- Context: "We almost never take scheduled downtime of our payments API"; "any operation that locks a table for updates for more than a few seconds means downtime for us."
- Safe: add column; drop column; add index `CONCURRENTLY`; drop constraint; add a default to an existing column. Unsafe → workaround: plain `CREATE INDEX` → `CONCURRENTLY`; change column type → add new column, dual-write, backfill; add column with default → add, then set default, then backfill (pre-PG 11 behavior); add non-nullable column → new table + dual write + backfill + switch; unique constraint → create unique index concurrently then add constraint using it; `VACUUM FULL` → `pg_repack`.
- Lesson (OLTP): maintain an explicit allow/deny list of DDL per engine version and enforce it in review/CI (compare GitLab's helpers, B3).

### Inferences (Theme B)
- Every "unsafe" operation becomes safe through the same decomposition: add nullable → backfill in batches → add constraint using an already-built concurrent index → flip application → drop old.
- Verification harnesses (Scientist, dark reads) are the difference between a migration and a gamble; they appear in A2, A3, A6, A9 and B1.

### Gaps (Theme B)
- The 2016 gh-ost announcement and GitLab's "required stops" page were not fetched; Etsy, Instacart and DoorDash migration posts were not located on official domains in this session and are omitted.

---

## Theme C. Financial ledgers, idempotency and money correctness

### Takeaway
Stripe, Square, Uber and Modern Treasury independently converged on immutable, append-only, double-entry ledgers where every transaction must balance, corrections are new reversing entries rather than updates, and data-quality is measured as clearing-account imbalance, timeliness and completeness. Idempotency keys stored with request parameters and a recovery point make money-moving APIs safely retryable.

### Cases

#### C1. Stripe Ledger: immutable log + double-entry + data-quality scoring (2024)
Source: [Ledger: Stripe's system for tracking and validating money movement](https://stripe.dev/blog/ledger-stripe-system-for-tracking-and-validating-money-movement) — Ilya Ganelin, February 16, 2024 (stripe.com URL redirects here).
- Problem: the Global Payments and Treasury Network spans many partners with different interfaces, data models, cadences and volumes (some emit billions of events a day, others hundreds); Stripe must prove to internal users and external auditors that all of these systems model its financials correctly; real failures include malformed partner reports and "currencies ceasing to exist or large banks collapsing overnight."
- Decision: Ledger, "an immutable and auditable log" and system of record; producer systems are modelled as state machines and fund flows, each operation recorded as a transaction between accounts (e.g., `charge.creation`, `charge.release`); double-entry so credits and debits must balance, and a non-zero clearing-account balance at steady state signals a missing event or a wrong `business`/`id`; a Data Quality platform scores each fund flow on clearing, timeliness (hard delivery threshold) and completeness (cross-system ID checks plus statistical arrival models); corrections go through a two-phase review-and-commit process because immutability makes fixes a revert-and-reprocess operation.
- Outcome: ~5 billion events/day; 99.99% of dollar volume ingested and verified within four days; 99.999% of activity monitored/categorized/triaged; >99.9999% of money movement explainable even after a 10x data increase; Black Friday–Cyber Monday 300M transactions and $18.6B volume at >99.999% API availability; 135+ currencies/payment methods in 185 countries.
- Lesson (OLTP + OLAP): "we built a system that keeps these imperfections manageable and bounded"; "a system with a 99.99% data quality score is extremely unlikely to hide major problems" — measure correctness as balance, not as row counts.

#### C2. Square Books: immutable double-entry ledger service on Spanner (2019)
Source: [Books, an immutable double-entry accounting database service](https://developer.squareup.com/blog/books-an-immutable-double-entry-accounting-database-service/) — Łukasz Strzałkowski, October 16, 2019.
- Problem: the settlement service computed payouts with expensive per-merchant aggregations; a single payment could not be split across payouts ("if a merchant we deem risky makes a single $100,000 transaction, we have to decide to block the entire transaction or none of it"); nothing in the database prevented inconsistent payouts (e.g., a nulled payout reference); sharding and cross-shard transactions added complexity.
- Decision: Books — accounts are "books" with balances; transactions are "journal entries" and "all transactions (which we call "journal entries") must balance to 0"; debits positive, credits negative (a deliberate simplification); core tables `books` (balance, type, owner, id), `journal_entries`, `book_entries` (debit/credit amount plus a per-book version counter); multi-tenancy via "shelves" that namespace secondary indexes; storage on Google Cloud Spanner on GKE with UUIDs instead of sequential integers and interleaved tables to avoid hotspots; "Books are immutable and can only have the balance changed by participating in accounting transaction"; mistakes are fixed with correcting entries — "this is not a bug - this is a feature."
- Outcome: payouts can be split arbitrarily and a payout is a single row rather than an aggregation; ~20 TB managed by a team of three.
- Lesson (OLTP): make the invariant (entries sum to zero) a property of the schema; append-only yields the audit trail for free; key choice must follow the storage engine (UUIDs on range-sharded Spanner).

#### C3. Uber LedgerStore: immutable ledger with trillions of indexes (2024)
Source: [How LedgerStore Supports Trillions of Indexes at Uber](https://www.uber.com/blog/how-ledgerstore-supports-trillions-of-indexes/) — Kaushik Devarajaiah, April 4, 2024.
- Problem: ledgers are the source of truth for financial events; indexes must be complete and correct at petabyte scale.
- Decision: LedgerStore provides "verifiable data completeness and correctness guarantees"; three index classes: strongly consistent (read-your-writes for authorization holds) built with a two-phase commit — write an index intent, write the record, commit the intent asynchronously, and resolve leftover intents on the read path; eventually consistent (built from Docstore materialized views, acceptable for payment history where "a lag of a few seconds is acceptable"); time-range indexes for offloading older ledgers to cold storage in batches. Index storage moved from DynamoDB (buffer + permanent tables; "if the temporary buffer tables are not created in time, it can lead to write failure") to Docstore with a single time-range table partitioned on the full timestamp to avoid hot partitions.
- Outcome: >2 trillion unique indexes; no inconsistencies in 6+ months; no incidents during backfill; >$6M/year savings.
- Lesson (OLTP): "maintaining a petabyte-scale of indexes in an OLTP system brings in certain challenges" — imbalanced partitioning, read/write amplification, noisy neighbors; pick the consistency class per access path, and partition time-series indexes on the full timestamp.

#### C4. Modern Treasury Ledgers: object model and status immutability (official docs)
Sources: [Ledgers Objects](https://docs.moderntreasury.com/ledgers/docs/guide-to-ledger-objects) and [Transaction Status and Balances](https://docs.moderntreasury.com/ledgers/docs/transaction-status-and-balances) — Modern Treasury Docs, n.d.
- Model: a Ledger contains Ledger Accounts ("the balances your platform will track", any currency or currency-like unit); Ledger Transactions "represent financial events" and "its credit and debit entries must sum to the same amount", each with at least two Ledger Entries, each entry updating one account; a transaction "can write to only a single ledger"; Account Categories aggregate accounts. Statuses: `pending` ("While a Ledger Transaction is `pending`, it is mutable"), `posted` (on settlement), `archived` (cancel); "Once a ledger transaction is `posted` or `archived` its status and entries are immutable", metadata remains updatable, and reversal is a second reversing transaction; accounts expose `pending_balance`, `posted_balance`, `available_balance`.
- Lesson (OLTP): a three-state lifecycle (pending/posted/archived) plus immutability after posting is the vendor-neutral ledger pattern; keep mutable metadata separate from immutable financial fields.

#### C5. Idempotency keys: Stripe API semantics and a Postgres implementation (2017; docs n.d.)
Sources: [Idempotent requests](https://docs.stripe.com/api/idempotent_requests) — Stripe API reference, n.d.; [Implementing Stripe-like Idempotency Keys in Postgres](https://brandur.org/idempotency-keys) — Brandur Leach, October 27, 2017 (well-known practitioner; former Stripe engineer).
- Stripe semantics: clients send an `Idempotency-Key` (V4 UUID suggested, up to 255 chars, no sensitive data); for API v1 Stripe saves the status code and body of the first request once execution begins and returns the saved response on retry "including `500` errors"; keys may be pruned after at least 24 hours; reusing a key with different parameters errors; only POST accepts keys; API v2 instead retries failed/partial work to completion.
- Postgres design (Brandur): table `idempotency_keys(id BIGSERIAL, created_at, idempotency_key TEXT ≤100, last_run_at, locked_at, request_method, request_params JSONB, request_path, response_code, response_body JSONB, recovery_point TEXT, user_id)` with `UNIQUE (user_id, idempotency_key)`; work is split into atomic phases run in `SERIALIZABLE` transactions, each ending in a recovery point (`started`, `ride_created`, `charge_created`, `finished`); every foreign call (e.g., Stripe charge) gets its own phase and "Atomic phases should be safely committed before initiating any foreign state mutation"; `locked_at` prevents concurrent retries; background jobs are staged transactionally (`staged_jobs`); a completer finishes abandoned requests and a reaper deletes old keys (~72 hours); "API backends should aim to be passively safe."
- Lesson (OLTP): persist the request fingerprint and the progress marker in the same ACID store as the business rows; non-ACID stores make atomic phases impossible.

#### C6. Airbnb: event-based financial reporting (2017) — URL not fetchable
Source: [Tracking the Money — Scaling Financial Reporting at Airbnb](https://medium.com/airbnb-engineering/6d742b80f040) (official Airbnb Engineering publication; fetch blocked; URL returned verbatim by WebSearch). Search excerpt: by Alice Liang, March 2017 (the brief's "2019" appears incorrect); the previous system was a parameterized nightly MySQL ETL built in early 2012 and retired late 2016; "Every product change had a unique money flow", forcing bespoke reports; the replacement is an event-based pipeline over payment events (bank movements and stored value such as gift cards) with the invariant that money in equals money out and horizontal scale-out. A related post, [Scaling Airbnb's Payment Platform](https://medium.com/airbnb-engineering/scaling-airbnbs-payment-platform-43ebfc99b324) (September 2016, not fetched), reportedly notes that financial reporting had been reverse-engineered from audit trails, which was error-prone.
- Lesson (OLTP→OLAP, unverified detail): model money movement as first-class balanced events at write time; reporting reverse-engineered from audit logs does not scale.

### Inferences (Theme C)
- Four independent organizations (Stripe, Square, Uber, Modern Treasury) arrived at: append-only; balanced double-entry; reversal-by-new-entry; explicit lifecycle states; correctness checks as imbalance detection. This is the strongest cross-case convergence in the whole set.
- Stripe's data-quality dimensions (clearing, timeliness, completeness) are a reusable rubric for any pipeline whose output must reconcile to an external truth.

### Gaps (Theme C)
- Airbnb's post could not be read; Monzo/Wise ledger posts and Uber's "Money Scale" were not found on official domains (search found no such Uber title) and are omitted.

---

## Theme D. Data platform, metadata, lineage and data quality

### Takeaway
LinkedIn and Uber both moved metadata from pull-based crawlers toward push/event-sourced architectures with a changelog as source of truth, decoupling collection from serving; Airbnb's (unverified) Midas/Minerva programs and Stripe's DQ platform show that quality is enforced by certification, single-definition metrics and balance checks rather than ad hoc tests.

### Cases

#### D1. LinkedIn DataHub: three generations of metadata architecture (2020)
Source: [DataHub: Popular metadata architectures explained](https://www.linkedin.com/blog/engineering/data-management/datahub-popular-metadata-architectures-explained) — Shirshanka Das, December 7, 2020 (engineering.linkedin.com URL redirects here).
- Gen 1 (monolith + pull-based crawlers; Amundsen, original WhereHows, Spotify Lexikon, Shopify Artifact, Airbnb Dataportal): crawlers are fragile, need central credentials, overload sources with batch pulls, and metadata goes stale. Gen 2 (service with push API; Collibra, Alation, Marquez): clearer producer contracts but no change log, so no real-time subscription or index rebuilds, and a central-team bottleneck — "The central metadata team runs into the same issues that a central data warehouse team runs into." Gen 3 (event-sourced; Apache Atlas, Egeria, Uber Databook, DataHub): a metadata change log materialized deterministically into search/graph/lake/OLAP indexes; strongly typed Entity/Aspect/Relationship models teams can extend; cost is complexity.
- Scale: ~10M change events/day, >5M indexed entities/relationships, low-millisecond lookups at LinkedIn.
- Lesson (general): "Putting metadata to work is harder than just putting metadata together"; make the metadata log the source of truth so indexes are rebuildable and consumers can react.

#### D2. Uber Databook: store-not-fetch metadata with decoupled collection (2018)
Source: [Databook: Turning Big Data into Knowledge with Metadata at Uber](https://www.uber.com/blog/databook/) — Luyao Li, Kaan Onuk, Lauren Tindal, August 3, 2018.
- Problem: tens of thousands of tables across Hive, Presto and Vertica; cataloguing began in 2015 as static HTML; "Big data by itself, though, isn't enough to leverage insights."
- Decision: build (WhereHows lacked cross-data-center read/write and used unsupported Play/Gradle); store metadata rather than query sources on demand (a Vertica schema query can take seconds); separate request-serving from collection so crawler load cannot breach API SLAs; crawlers (Quartz + Cherami) later supplemented with Kafka event streams for lineage/freshness; link cluster-specific and cluster-agnostic metadata at read time, because write-time linking failed when schemas diverged; Cassandra replaced MySQL for multi-DC replication (single-master MySQL added ~70 ms per cross-DC write and took hours to promote).
- Outcome: ~1,500 QPS peak API; schema, lineage, freshness, owners and personal-data categories served via UI/API; a query-rewriting service depends on it.
- Lesson (general): decouple collection from serving; do not push read load onto systems not designed for it; choose storage for the replication topology you need.

#### D3. Airbnb Midas data certification (2020) and Minerva metrics layer (2021) — URLs not fetchable
Sources: [Data Quality at Airbnb](https://medium.com/airbnb-engineering/data-quality-at-airbnb-870d03080469) and [How Airbnb Achieved Metric Consistency at Scale](https://medium.com/airbnb-engineering/how-airbnb-achieved-metric-consistency-at-scale-f23cc53dea70) (official Airbnb Engineering publication; fetches blocked; URLs returned verbatim by WebSearch).
- Search excerpts: Midas unites the company behind a shared "gold standard" so that "Midas Certified" data carries a single promise, via a nine-step process including spec review and data review; Airbnb's later Data Quality Score post states that "Starting in 2020, the Midas process, along with the work to re-architect our most critical data models, has brought a dramatic increase in data quality and timeliness" but that full certification "demands significant cross-functional investment", prompting a lighter-weight score. Minerva (Robert Chang): "From metric creation through computation, serving, consumption, and eventually deprecation, Minerva covers the full life cycle of a metric"; Part II (Amit Pahwa) standardizes dataset definitions through declarative configs, uses data versioning for cross-dataset consistency and backfills with zero downtime. A secondary summary cites 12,000+ metrics and 4,000+ dimensions (not verified).
- Lesson (OLAP/data warehouse, unverified detail): certification plus single-definition metrics address consistency; heavyweight certification does not scale to the long tail, so tier the rigor.

#### D4. Stripe Data Quality platform (see C1) — the clearing/timeliness/completeness rubric applies to any pipeline reconciled against an external system.

### Inferences (Theme D)
- The metadata evolution (crawl → push → event log) mirrors the ledger evolution (mutable balances → immutable event log): both make the log the truth and derive indexes.

### Gaps (Theme D)
- Netflix (Medium-hosted), Zalando data mesh, Spotify, Intuit SuperGlue and Shopify data-platform posts were not fetched/verified in this session and are omitted rather than cited from memory.

---

## Theme E. Multi-tenancy at scale

### Takeaway
Three models appear: metadata-driven shared tables with a tenant column on every row and tenant-aware indexing (Salesforce); shared microservice stores with mandatory tenant context on every request (Atlassian); and tenant-column co-located sharding with composite keys (Citus), with Shopify pods (A7) as the fully isolated end of the spectrum. ERP systems (Theme F) hard-code the tenant column into every table.

### Cases

#### E1. Salesforce: metadata-driven multitenant data model (official architecture docs)
Source: [Platform Multitenant Architecture](https://architect.salesforce.com/fundamentals/platform-multitenant-architecture) — Steve Bobrowski and Tom Leddy, Salesforce Architects, n.d.
- Design: `MT_Objects` (ObjID, OrgID, ObjName) and `MT_Fields` (FieldID, OrgID, ObjID, FieldName, datatype, indexed flag, position) describe tenant schemas; `MT_Data` holds rows as (GUID, OrgID, ObjID, Name, Value0…ValueN) where "flex columns, also known as slots, store application data" and "no two fields of the same object can map to the same slot"; indexing is done by "synchronously copying field data marked for indexing to an appropriate column in an MT_Indexes pivot table" (StringValue/NumValue/DateValue); `MT_Unique_Indexes` enforce uniqueness via native unique indexes; `MT_Relationships` has "two underlying database unique composite indexes that allow for efficient object traversals"; `MT_Fallback_Indexes` and `MT_Name_Denorm` support search fallback and parent/child name display; a multitenant-aware optimizer keeps tenant/group/user-level statistics because "Conventional, cost-based optimizer statistics are designed for single-tenant applications."
- Lesson (OLTP): OrgID on every row plus pivot tables substitute for per-tenant physical schemas; the optimizer must be tenant-aware because data skew per tenant defeats global statistics.

#### E2. Atlassian: tenant context enforced on every request (official trust docs)
Source: [Cloud architecture and operational practices](https://www.atlassian.com/trust/reliability/cloud-architecture-and-operational-practices/) — Atlassian Trust Center, n.d. (© 2025).
- Design: "a single service serves multiple customers"; shards hold several tenants; the Tenant Context Service stores a per-tenant context keyed by unique ID (databases, licenses, features) and Jira/Confluence "require this tenant context or the request will be rejected"; tenant data is "kept logically segregated" at rest; each microservice owns its data store; data keys are per service wrapped with AWS KMS, with customer-managed keys for eligible customers; data residency in 11 regions; single-tenant "Isolated Cloud" offered separately.
- Lesson (OLTP): logical isolation requires a mandatory tenant token on the request path, not just a column; per-service stores limit blast radius.

#### E3. Citus: tenant column on every table, composite keys, co-location (official docs)
Source: [Multi-tenant Applications](https://docs.citusdata.com/en/stable/use_cases/multi_tenant.html) — Citus Docs, n.d.
- Design: "every table in our schema has a column to clearly mark which tenant owns which rows" (e.g., `company_id`) used as distribution column; primary and foreign keys must include it, e.g., PK `(company_id, id)` and FK `(company_id, campaign_id) → (company_id, id)`; co-located tables keep joins, constraints and transactions on one node; shared lookup data (e.g., `geo_ips`) becomes a reference table "replicated across all worker nodes"; queries filtering on the tenant route to one node; large tenants can be isolated with `isolate_tenant_to_new_shard(..., 'CASCADE')` and moved with `citus_move_shard_placement()` (requires `wal_level = logical`).
- Lesson (OLTP): composite keys with the tenant prefix are the price of tenant co-location; the same pattern Notion (A2) wished it had adopted ("combined primary key").

### Inferences (Theme E)
- Whether the tenant is a column (Salesforce, Citus, ERPs), a request token (Atlassian) or a physical pod (Shopify), the invariant is identical: no query path may exist without a tenant predicate.

### Gaps (Theme E)
- The Citus/Heap customer page returned empty content; Intercom was not researched; Atlassian's dedicated tenant-isolation engineering post was not located.

---

## Theme F. Open-source ERP schema conventions (reference implementations)

### Takeaway
Four mature ERP frameworks independently standardize the same row-level columns: a surrogate key, creator/creation timestamp, last-modifier/modification timestamp, a company/tenant column, and a soft-delete or activity flag; document-centric systems add a document state machine (Frappe `docstatus`) and record-level versioning for optimistic locking.

### Cases

#### F1. Odoo ORM (v18 developer docs)
Source: [ORM API — Odoo 18.0](https://www.odoo.com/documentation/18.0/developer/reference/backend/orm.html) — Odoo S.A., n.d.
- Automatic fields: `id`; `display_name`; access-log fields `create_date`, `create_uid` (Many2one `res.users`), `write_date`, `write_uid`, maintained only when `_log_access` is enabled (defaults to `_auto`; "_log_access must be enabled on TransientModel").
- Reserved names: `name` (default `_rec_name`); `active` (Boolean that toggles global visibility — inactive records are hidden from most searches/listings, i.e., archive/soft-delete); `state` (Selection lifecycle used by field `states`); `parent_id`/`parent_path` (tree storage, `parent_path` must be `index=True`); `company_id` — "Main field name used for Odoo multi-company behavior" (empty = shared across companies); `_check_company_auto` runs company-consistency checks on create/write for relational fields with `check_company=True`.
- Lesson (OLTP): ORM-level conventions make audit, multi-company and soft delete uniform across hundreds of tables.

#### F2. Frappe/ERPNext DocType conventions (official docs)
Sources: [DocTypes](https://docs.frappe.io/framework/user/en/basics/doctypes), [Naming](https://docs.frappe.io/framework/user/en/basics/doctypes/naming), [DocStatus](https://docs.frappe.io/framework/doctypes/docstatus) — Frappe Technologies, n.d.
- "All DocTypes in Frappe have a primary key called `name`"; tables are `tab<DocType>`; DocType names are singular; naming strategies: set by user, autoincrement ("Deleted records are not reused"), by field, by naming series (`naming_series` field), expression (e.g., `.#####` counters), random, UUID v4, or `autoname` script; child DocTypes do not follow naming rules; amended documents get `-1`, `-2` suffixes.
- `docstatus` is an integer: 0 Draft, 1 Submitted, 2 Cancelled; "Documents that are not submittable will always remain in the "draft" state"; "Documents in the submitted and cancelled state cannot be edited" except fields explicitly allowed after submit; `creation` is the default sort (`creation desc`) and `db_set` "updates the modified timestamp" (the standard `owner`, `creation`, `modified`, `modified_by`, `idx`, `parent/parentfield/parenttype` columns were not enumerated on the pages fetched — see Gaps).
- Lesson (OLTP): a three-state document lifecycle with post-submit immutability and amend-by-copy is the same pattern as ledger posting (C4).

#### F3. Apache OFBiz Entity Engine and data model (official wiki and manual)
Sources: [OFBiz Data Model / General Entity Overview](https://cwiki.apache.org/confluence/display/OFBIZ/General+Entity+Overview) — created by Scott Gray, last updated by Pierre Smits, December 5, 2016; [EntitySync manual](https://apache.googlesource.com/ofbiz-framework/+/1bc8a206346f251c9076c2fb9babc896ba6bdf0d/framework/entityext/src/doc/asciidoc/EntitySync-manual.adoc) — Apache OFBiz, n.d.
- Entities are defined in XML (`entitydef`); many-to-many relations use dedicated join entities (`ProductCategoryMember`, `ProductCategoryRollup`); the "Extensibility Pattern" adds types/attributes via `EntityType`, `EntityAttribute`, `EntityTypeAttr` without new tables; deprecated entities get an "Old" prefix while `table-name` keeps the table unchanged. "The four fields (lastUpdatedStamp, lastUpdatedTxStamp, createdStamp, createdTxStamp) are added to each entity" automatically (disable with `no-auto-stamp`) so "queries can be done on each entity to get all records created, updated, or removed in a certain transaction" and changes can be replayed remotely in order; removals are logged in `EntitySyncRemove`.
- Lesson (OLTP): separate row timestamps from transaction timestamps when you need replayable sync; type/attribute tables provide schema-less extension inside a relational model. (The wiki page does not cite Silverston's universal data model; that attribution is not verified here.)

#### F4. iDempiere (Compiere/ADempiere lineage): AD_Client/AD_Org on every table (official Javadoc)
Source: [I_AD_Org (iDempiere Javadoc)](https://jenkins-artifacts.idempiere.org/javadoc12/org/compiere/model/I_AD_Org.html) — iDempiere project build artifacts, n.d. (wiki returned 403).
- Standard columns and documented meanings: `AD_Client_ID` — "Tenant for this installation."; `AD_Org_ID` — "Organizational entity within tenant"; `IsActive` — "The record is active in the system"; `Created`/`CreatedBy` — "Date this record was created"/"User who created this records"; `Updated`/`UpdatedBy`; `Value` — "Search key for the record in the format required - must be unique"; `Name`, `Description`, `IsSummary`; each table has a stable `Table_ID` (AD_Org = 155). The wiki's Table Prefix page (search excerpt, unverified) lists the required set as AD_Client_ID, AD_Org_ID, IsActive, Created, CreatedBy, Updated, UpdatedBy with Numeric(10) NOT NULL IDs and Char(1) Y/N flags.
- Lesson (OLTP): two-level tenancy (client → organization) baked into every table, with `IsActive` as soft delete, is the oldest and most explicit form of the pattern in Theme E.

### Inferences (Theme F)
- Convergent audit columns: Odoo `create_uid/create_date/write_uid/write_date`; Frappe `owner/creation/modified/modified_by`; OFBiz `createdStamp/lastUpdatedStamp` (+Tx variants); iDempiere `Created/CreatedBy/Updated/UpdatedBy`. Soft delete: Odoo `active`, iDempiere `IsActive`; Frappe instead uses `docstatus=2` for transactional documents.
- Tenant column: Odoo `company_id`, iDempiere `AD_Client_ID`+`AD_Org_ID`; this matches Citus/Salesforce guidance in Theme E.

### Gaps (Theme F)
- Frappe's full standard-column list and `amend` semantics were not on the fetched pages; Dolibarr was not researched; the iDempiere wiki pages were blocked.

---

## Theme G. Official postmortems with schema/ops lessons

### Takeaway
Both incidents were failures of recovery design, not of schema per se: GitLab lost six hours of data because every backup path had silently failed and nobody owned testing restores; GitHub's 43-second partition became a 24-hour degradation because cross-region primary promotion created divergent writes and restoring multi-terabyte clusters from backup was slow. Restore time and write-topology constraints belong in the data architecture.

#### G1. GitLab.com database outage (January 31, 2017)
Source: [Postmortem of database outage of January 31](https://about.gitlab.com/blog/2017/02/10/postmortem-of-database-outage-of-january-31/) — GitLab, February 10, 2017.
- Chain: load spike (partly a background job deleting a mistakenly flagged employee account) → replication lag → WAL segments removed before the secondary consumed them (no WAL archiving) → manual resync, `max_wal_senders` 3→32, `max_connections` 8000→2000 → an engineer wiped the data directory on the primary instead of the secondary (~300 GB gone in seconds). Recovery used a 6-hour-old LVM snapshot after every other backup failed: `pg_dump` ran as 9.2 against a 9.6 server and failed; failure emails were rejected because DMARC was not configured; the S3 bucket was empty; Azure disk snapshots were enabled for NFS but not databases.
- Impact: ~18 hours of outage; roughly six hours of data lost — at least 5,000 projects, 5,000 comments and ~700 user accounts; repositories/wikis unaffected.
- Root cause statement: "Because there was no ownership, as a result nobody was responsible for testing this procedure." Remediation: hourly LVM snapshots, restore testing with an owner, PITR via WAL archiving (WAL-E/Barman), sane `max_connections`, clearer host identification over command restrictions.
- Lesson (OLTP): a backup that has never been restored is not a backup; replication is not a backup; make the production/secondary distinction unmistakable.

#### G2. GitHub October 21, 2018 incident and its HA design
Sources: [October 21 post-incident analysis](https://github.blog/2018-10-30-oct21-post-incident-analysis/) — Jason Warner, October 30, 2018 (updated December 19, 2021); [MySQL High Availability at GitHub](https://github.blog/2018-06-20-mysql-high-availability-at-github/) — Shlomi Noach, June 20, 2018 (updated May 21, 2020).
- HA design (June 2018): orchestrator/raft for detection and failover (quorum across data centers so an isolated DC cannot lead), Consul KV for primary identity, GLB/HAProxy proxies and anycast writer hostnames, semi-synchronous replication with a 500 ms timeout; replaced cooperative VIP+DNS where "We can end up with a split-brain"; typical failover 10–13 seconds; known limitation: an isolated primary may keep accepting local writes, STONITH planned.
- Incident: replacing failing 100G optical equipment cut East-Coast hub connectivity for 43 seconds at 22:52 UTC; Orchestrator deselected the East leader and West nodes promoted West primaries; writes landed on both coasts; the team chose to "prioritize data integrity over site usability and time to recovery", restoring East clusters from multi-terabyte backups (decompress/checksum/load dominated time; a full-cluster restore had never been done), while East app servers suffered cross-country latency and replicas lagged for hours on a power-decay catch-up curve; >5M webhook events and 80K Pages builds queued, ~200K webhook payloads dropped by TTL; one busiest cluster had 954 unreconciled writes. Degraded for 24 h 11 m.
- Remediation: prevent cross-region primary promotion in Orchestrator; component-level status reporting; move toward active/active/active across facilities; fault injection/chaos engineering; better recovery estimates.
- Lesson (OLTP): failover automation must encode topology constraints the application can actually serve; measure and rehearse restore time; divergent-write reconciliation is the costliest failure mode and should be designed out.

---

## Where cases conflict with each other or with textbook advice

1. Uber vs. the PostgreSQL community (A8). Uber's claims about write amplification, replication and connections were partly valid for an UPDATE-heavy, many-index workload with ORM-held transactions; Winand, Riggs and Pettus show the comparison mixed logical vs. physical replication, ignored HOT/`hot_standby_feedback`, provided little quantitative data, and that the real change was adopting a schema-less data model. Transferable lesson: evaluate engine trade-offs against your own update/index pattern; do not generalize one workload's conclusion.
2. "No joins, no foreign keys at scale" (Pinterest A5: "Remove all joins", mapping tables, FK-free blobs; Uber Schemaless A8: schema-less JSON cells) vs. integrity-preserving sharding (Figma colos, Notion FK-reachable shard sets, GitHub schema-domain linters, Citus composite FKs, every ERP in Theme F). Reconciliation: constraints and joins are kept within the sharding key's locality and forbidden across it; dropping them entirely (Pinterest 2012) shifts uniqueness, referential checks and reporting to the application — costs Pinterest's own slides enumerate.
3. Sequential vs. random keys. Flickr (GUIDs "index badly in MySQL"), Snowflake and Instagram favour time-ordered integers for B-tree locality; Square on Spanner uses UUIDs and Figma hashes keys specifically to avoid hotspots from sequential IDs. Lesson: the key's distribution must match the storage engine's partitioning (B-tree/heap vs. range-sharded/distributed).
4. Clustering/auto-sharding "is scary" (Pinterest 2012) vs. successful adoption of Vitess (Slack 2020, GitHub 2021), Cassandra→ScyllaDB (Discord) and Spanner (Square). Lesson: the verdict is time- and maturity-dependent; Figma and Notion still chose application-level sharding in 2021–2024 for control and reversibility, so the question remains open.
5. Build vs. adopt a sharding layer: Figma/Notion/Pinterest built; Slack/GitHub adopted Vitess; all rejected a migration to NewSQL/NoSQL as higher risk than evolving the incumbent engine.
6. Native table partitioning vs. schemas/views: Notion used separate schemas to keep routing in the app; Figma used views for reversible logical sharding; neither used Postgres declarative partitioning as the sharding unit.
7. Deletes: ERPs favour soft delete flags (Odoo `active`, iDempiere `IsActive`) and ledgers forbid deletes entirely (reversing entries), while Discord shows physical deletes in LSM stores are themselves expensive writes (tombstones). Textbook "just DELETE" is the minority position at scale.
8. Metadata and money converge on the same architecture: an immutable event/change log as truth with derived indexes (DataHub Gen 3, Databook event streams, Stripe Ledger, Square Books, LedgerStore), contradicting designs that treat mutable balances or crawled snapshots as truth.
9. Backups: GitLab (untested, silently failing) vs. GitHub (tested but slow to restore). Both show restore time and ownership are architectural properties.

---

## Summary table of transferable lessons

| # | Lesson | Evidence (cases) | Applies to |
|---|--------|------------------|-----------|
| 1 | Shard on a tenant-like key that keeps joins/transactions local; forbid cross-shard transactions | Figma, Notion, Slack, Shopify, Citus, GitHub | OLTP |
| 2 | Many logical shards per physical host; re-shard by moving logical shards, not re-keying | Notion (480/32→96), Pinterest (4096/8), Instagram | OLTP |
| 3 | Include the tenant/partition key in the primary key and in foreign keys | Citus, Notion retrospective, iDempiere, Odoo | OLTP |
| 4 | Encode time (high bits) and generator/shard in 64-bit IDs; match key distribution to storage engine | Snowflake, Flickr, Instagram, Discord, Square (UUIDs on Spanner), Figma (hashing) | OLTP |
| 5 | Migrate with dual-write or log replay + batched backfill + dark/double reads; use a comparison harness | Notion ×2, Slack, Discord ×2, Stripe, GitHub | OLTP |
| 6 | Multi-release expand/contract for every DDL; never take long locks (CONCURRENTLY, NOT VALID, batched backfills) | GitLab docs, Braintree, gh-ost, PlanetScale | OLTP |
| 7 | Enforce partition boundaries with linters/experiments before moving data | GitHub | OLTP |
| 8 | Ledgers: append-only, double-entry, balanced transactions, reversal by new entry, explicit pending/posted/archived states | Stripe, Square, Uber LedgerStore, Modern Treasury | OLTP + OLAP |
| 9 | Measure correctness as clearing-account imbalance, timeliness and completeness | Stripe Ledger/DQ | OLTP + OLAP |
| 10 | Idempotency keys: persist request fingerprint + recovery point in the same ACID store; commit before foreign calls | Stripe docs, Brandur | OLTP |
| 11 | Bound partition size and hot-key exposure; deletes in LSM stores are writes | Discord 2017/2023 | OLTP (wide-column) |
| 12 | Metadata: event-sourced change log as truth; decouple collection from serving | DataHub, Databook | general |
| 13 | Standard row columns: surrogate id, created/updated by/at, tenant column, soft-delete flag, document state | Odoo, Frappe, OFBiz, iDempiere | OLTP |
| 14 | Tenant predicate on every access path (column, request token or pod) and tenant-aware statistics | Salesforce, Atlassian, Citus, Shopify | OLTP |
| 15 | Restore time, backup ownership and failover topology constraints are architecture, not ops detail | GitLab 2017, GitHub 2018 | OLTP |
| 16 | Engine trade-offs depend on update/index pattern and replication model; do not generalize | Uber vs. Winand/Riggs/Pettus | OLTP |
| 17 | Prefer evolving the incumbent engine over NewSQL/NoSQL rewrites when runway is short | Figma, Notion, Slack, GitHub | OLTP |
| 18 | Heavyweight data certification does not scale to the long tail; tier rigor and centralize metric definitions | Airbnb Midas/Minerva (unverified detail) | OLAP / data_warehouse |
