# 23 - Independent benchmarks: keys, RLS, warehouse modelling, foreign keys, HTAP

Researched 2026-11-08. Catalog: `catalog_23_benchmarks.json` (BENCH-01 to BENCH-15).

## How to read the evidence

- **Raw-confirmed**: numbers checked against text downloaded and extracted locally (BENCH-01, 07, 10, 11, 12, 13, 14).
- **Summary only**: curl failed on these pages, so numbers come from a WebFetch model summary and were not confirmed against raw text (BENCH-02, 03, 04, 05, 06, 08, 09). Re-check before citing them as authoritative.
- BENCH-15 has slides and code opened but the paper itself could not be reached. It carries no numbers.
- Linked repositories were not opened or rerun unless stated. "Scripts published" means the author says so.
- No result here was reproduced by this research.

## Summary

| Topic | Peer-reviewed independent evidence | Verdict |
|---|---|---|
| UUIDv7/v4/bigint, PostgreSQL | None found | Practitioner benchmarks only. They agree on direction, not magnitude. |
| UUIDv7/v4/bigint, MySQL | None found | No UUIDv7 benchmark found at all. Ordered UUID and UUIDv1 are proxies. |
| Row-level security overhead | None found | One small practitioner test. Complex policies have no measured evidence here. |
| One Big Table vs star | Yes, one (BENCH-10) | Engine-dependent. |
| Data Vault vs star | Effectively none | One thesis on a laptop and one weak proceedings paper. |
| Foreign key overhead at scale | None found | No at-scale evidence. No MySQL evidence. |
| HTAP isolation | Yes (BENCH-14, 15); vendor paper BENCH-13 | Best-covered topic, though commercial systems are anonymized in the most independent results. |

## 1. Primary keys on PostgreSQL

No peer-reviewed or vendor-neutral lab benchmark was found.

| ID | Who | Setup | Data | Results | Conflict |
|---|---|---|---|---|---|
| BENCH-01 | Ardent Performance blog | c7a.medium 1 core/2 GB, gp3 16k IOPS, PostgreSQL main 2024-01-29 + v17 UUIDv7 patch, shared_buffers=1G | 20M start + 1M inserted, with concurrent reads | uuid::text 410 s, 2421 tps, 4.31 GB; v4 375 s, 2670 tps, 2.65 GB; v7 290 s, 3420 tps, 2.47 GB; bigint 290 s, 3480 tps, 1.97 GB | Not established. Scripts in the post. |
| BENCH-02 | Josef Machytka, credativ | PostgreSQL 18, hardware not stated, naive single runs | 50M + 50M | 1st 50M: v4 1,239,840 ms, v7 106,343 ms. 2nd 50M: v4 2,776,881 ms, v7 100,354 ms. Index at 100M: 3,956 vs 3,008 MB. No bigint arm. | Host sells PostgreSQL services. |
| BENCH-03 | Coding Steve (no byline) | PostgreSQL 18 Testcontainers, M-series MacBook | 1M, batch 1,000 | bigint 3,615 ms, 21 MB; v7 3,820 ms, 30 MB; v4 4,837 ms, 38 MB | None stated. Repo linked, not opened. |

Reading: time ordering removes most of the v4 fragmentation penalty (about 50 percent leaf fragmentation for v4 in BENCH-02 and BENCH-03, near zero for v7). The v4 penalty grows sharply once the index exceeds memory: about 1.3x in BENCH-03 at 1M rows against 12x to 28x in BENCH-02. These are different setups, so that is an inference. BENCH-02's prose ratios disagree with its own timings; use the timings.

## 2. Primary keys on MySQL

**No independent benchmark of UUIDv7 on MySQL was found.**

| ID | Who | Setup | Data | Results | Conflict |
|---|---|---|---|---|---|
| BENCH-04 | Karthik Appigatla, Percona (2014) | Version and hardware not stated | 25M | .ibd: ordered UUID 13 GB, BIGINT 15 GB, random UUID PK 20 GB. Random UUID insert time grows almost linearly; timings charted only. | Percona sells MySQL services. |
| BENCH-05 | Michael Coburn, Percona (2015) | Percona Server 5.5 context; test version not stated | About 60,880 records | Leaf pages: AUTO_INCREMENT 99 (90 percent full), ordered binary(16) 147 (91 percent), UUID() char(36) about 399 (slightly above 50 percent) | As above. |
| BENCH-06 | Ayaan Zaidi (2022) | MySQL 8.0.30, EPYC 7642 4 vCPU, sysbench 16 threads, buffer pool 64 MB | Up to about 64M | UUIDv1 near INT. UUIDv4: INT led CHAR(36) by over 2,000 inserts/s at 500 s, nearly 4,000 at doubled duration; p99 about 6x better. | Linode gave hosting credits. Scripts linked. |

The 64 MB buffer pool in BENCH-06 deliberately forces disk I/O, so it is a stress case. BENCH-05 confounds key order with key width.

## 3. Row-level security overhead

**No peer-reviewed or vendor-neutral benchmark was found.**

BENCH-07 (Ashwin Sridhar, CTO koto7, 2026): 1M rows, one tenant about 10 percent, 50 runs minus 3 warmup. At p95, superuser bypass vs RLS differed by under 2 percent without an index (count 73.3 vs 74.9 ms). With an index on tenant_id, count was 2.2 vs 2.7 ms, which is proportionally larger. PostgreSQL version, hardware and scripts are not given, and the author had already chosen RLS.

Evidence gap: policies with subqueries or join-based permissions, plan-level effects from non-leakproof functions, and any MySQL equivalent. Repository `jchen1/row-level-security-performance` provides a schema harness (100 users, 100,000 items) but its README publishes no results, so it is not a catalog entry.

## 4. One Big Table vs star schema

Independent evidence exists but is limited, and it conflicts with the vendor-hosted test.

| ID | Who | Setup | Data | Results | Conflict |
|---|---|---|---|---|---|
| BENCH-10 | Ferreira and Fidalgo, UFPE, ICEIS 2024 | 3 nodes x 16 GB on AWS: Singlestore, Redshift, MariaDB Columnstore. Versions not found. | SSB SF10 (60M), SF50 (300M) | Star faster than flat by 74 percent (Redshift) and 63 percent (MariaDB Columnstore). Flat 42 percent faster on Singlestore. SF50 volume on Redshift 12.7 GB vs 62.7 GB. | Funding not located. |
| BENCH-09 | Michael Kaminsky on Fivetran blog, 2022 | Redshift dc2, Snowflake X-Large, BigQuery default | TPC-DS scale 100 subset | Flat faster: Redshift 25-30 percent, Snowflake about 25 percent, BigQuery about 50 percent (Redshift compile excluded). Disk just over 30 GB to over 90 GB. | Vendor-hosted, scripts public. |

The two disagree on Redshift. Differences include benchmark, cluster size, memory pressure and distribution keys. Do not state a general rule. An InterWorks post (40 s flat vs 77 s star, SQL Server PDW, data size and method undisclosed) was left out as unreproducible.

## 5. Data Vault vs star schema

**No independent, peer-reviewed benchmark at realistic scale was found.**

- BENCH-11 (Schiller, Rostock master's thesis, 2016): SQL Server on a 4 GB i5 laptop, SSB SF1 (about 4.5 GB). Star schema led on runtime and CPU; Data Vault runtimes were minimally worse on the very small dataset. Per-query values are in charts.
- BENCH-12 (Rorimpandey et al., EIC 2018): SQL Server, 13 information needs, Sidak post-hoc. No significant difference among Anchor, Data Vault and ONF; star differs. The stated conclusion that queries with more joins run faster has no adequate controls. Low confidence.

The two point in different directions and neither supports a production claim.

## 6. Foreign key enforcement overhead at scale

**No independent evidence at scale was found. No MySQL/InnoDB measurement was found.**

BENCH-08 (Thyago de Oliveira Perez, January 2026): PostgreSQL 16, unspecified dev machine, 4 FKs, parents up to 250K rows, 1,000 operations per scenario.

| Scenario | Without FK | With FK |
|---|---|---|
| Batch insert | 114.2 ms | 151.6 ms |
| Concurrent insert (10 threads) | 817.2 ms | 818.5 ms |
| Mixed | 2,697.4 ms | 2,870.9 ms |
| Sequential insert | 5,012.4 ms | 5,286.2 ms |

The concurrent difference is far inside its reported error (standard deviation about 70 ms), so it shows nothing about contention. The article has internal inconsistencies noted in the catalog.

Not catalogued: the TigerData post on constraints at 50K inserts/s reasons about cost and, in the sections checked, does not report a with/without FK measurement; it is also a vendor post. Search snippets also surfaced a Postgres.AI chat (2.36 percent TPS decrease) and a pgbench handout (FK 20-300 percent). Neither was opened, so treat them as unverified leads only.

## 7. HTAP isolation

| ID | Who | Setup | Data | Results | Conflict |
|---|---|---|---|---|---|
| BENCH-14 | Zhang, Li, Lv; PVLDB 17 | 4 nodes, 40 cores, 128 GB, PostgreSQL 14 streaming replication + 4 anonymized systems, 3 repeats | SF1/10/100 (518 MB, 5.3 GB, 56 GB) | SF1: PostgreSQL-SR H-Score 320, F-Score 24 ms. A4 QPS 676.29, XPS 45.49, F-Score 78 ms. A4 ATS 7.99 to 1.08 at T-max, F-Score 19.6 s at (100,20). | Partly Huawei-funded; thanks several vendor teams. Public code. |
| BENCH-13 | Huang et al., PingCAP; PVLDB 13 | 6 servers, 188 GB; CH-benCHmark | 10-100+ warehouses | TP degraded at most 10 percent by AP; AP at most 5 percent by TP. 100 warehouses under 1000 ms lag: 98.64-99.58 percent (2 AP clients), 84.82-87.17 percent (32). MemSQL 7.0 TP dropped more than 5x. | Vendor on own product. |
| BENCH-15 | Milkai et al., Wisconsin; SIGMOD 2022 | HATtrick method, code for Postgres, TiDB, MySQL | Not recorded | **No numbers recorded**: paper unreachable. | Not checked. |

The TiDB figures are not independent evidence. BENCH-14 is the most independent quantitative result, but DeWitt clauses keep its product identities hidden, so it supports claims about architecture, not named products.

## Gaps worth a controlled benchmark

UUIDv7 on MySQL 8; RLS with join-based policies; foreign keys under concurrency with parent contention on both engines; Data Vault vs star on a modern engine above 100 GB.
