# Decisions to Approve

## Decision log

- **2026-11-08:** The owner said "accept all defaults". This approves the proposed default for all 61 decisions (A1 to A18, B1 to B32, C1 to C11) and the defaults of housekeeping items H1 to H3. It approves nothing else.
- **Applied:** the defaults are in `rules/` and `registry/`. Each decided rule carries a `decision_ref`. Alternatives below are kept for the record.
- **Still provisional, needs counsel:** A6, B8, B9, B10, and the Saudi part of A1. Any rule marked requires legal review stays provisional.
- **Still provisional, no value set:** A14 (rate precision), B6 (lock and runtime limits), B17 (triangulation), B28 (freshness and quality thresholds). No source supports a value.
- **H1:** "framework exception approver" is the one role for framework-level exceptions. No person is named yet.
- **Evidence:** approval makes an organizational choice binding. It does not create evidence, so `evidence_strength` is unchanged and no benchmark is claimed.

Stage 2 owner decision list. It merges the "Decisions needing owner approval" sections of the seven files in `rules/`. The owner's answers are recorded below and applied to the rules.

**Totals:** 61 decisions (A 18, B 32, C 11), from 69 source items. Six decisions are merged from 13 source items. One source item moved to housekeeping (H2).

**Priority:** A blocks Stage 3 or ASTRA design. B is an important default. C is minor.

**Evidence labels:** standard, vendor, or judgment. Judgment means no independent source settles the question.

**Counsel:** Yes means a lawyer should confirm before the default is relied on. This list is not legal advice.

Contradictions between rules are in `OVERLAP_REPORT.md`. Four of the five are settled by answering A4, A6, A14 and H2. The fifth is OR-5.

---

## A. Blocks Stage 3 or ASTRA design

### A1. Which tenancy model does ASTRA use?
- **Proposed default:** Shared pool with a tenant ID on every tenant table. Dedicated databases only for tenants that meet a written trigger (a bridge model).
- **Alternatives:** Pool only. Silo (a database per tenant) for all. Metadata-driven shared tables. Schema per tenant (no source assesses it; not proposed).
- **Consequence:** Default: isolation only where needed, but operations and migrations must support both models. Pool: cheapest, weakest isolation, per-tenant restore is hard. Silo: strongest isolation, highest cost. Metadata-driven: flexible, but only one vendor's evidence.
- **Evidence basis:** Vendor (AWS, Azure) for the options. The default is a judgment: the research has no ASTRA tenant counts, regions or regulatory profile.
- **Affected rules:** TEN-004 (with TEN-003, TEN-005, TEN-006, TEN-007)
- **Needs counsel:** Yes, only if ASTRA serves Saudi Arabia. In-Kingdom retention (RET-018) may force a silo.
- **Owner answer:** Accepted default, 2026-11-08

### A2. Where is tenant isolation enforced?
- **Proposed default:** Application filters plus engine row-level security, wherever the engine offers it and tenant identity reaches every query.
- **Alternatives:** Application filters only. Separate credentials per tenant.
- **Consequence:** Default: a second layer against a missed filter, but identity handling is complex and the cost is unmeasured. Filters only: simple, one missed filter is a leak. Credentials: strong boundary, management grows with tenants.
- **Evidence basis:** Vendor for the options. The default is a judgment; no independent performance evidence.
- **Affected rules:** TEN-009 (with TEN-010, TEN-011, TEN-012)
- **Needs counsel:** No
- **Owner answer:** Accepted default, 2026-11-08

### A3. What primary key do OLTP tables use? (merged)
- **Proposed default:** A surrogate key, plus a unique constraint on the natural key where one exists. Generated keys default to 64-bit integer. Use a time-ordered 128-bit ID in binary form only where global or client-generated uniqueness is needed.
- **Alternatives:** Natural primary key. Surrogate with no natural key constraint. Time-ordered 128-bit ID everywhere. Random UUIDv4 everywhere. No framework default.
- **Consequence:** Default: small, stable keys and no duplicates, at the cost of one more unique index; clients cannot generate integer keys. Natural: meaningful, but key changes spread. Surrogate only: duplicates of the real-world entity get in. 128-bit everywhere: clients can generate keys, wider indexes, creation time exposed. UUIDv4: index scatter. No default: repeated debate.
- **Evidence basis:** Judgment. Practitioner tests agree on direction, not size. No independent benchmark. No source measures natural against surrogate for OLTP.
- **Affected rules:** IDX-023, INT-016 (with TYP-029, TYP-030, TEN-014, NAM-017)
- **Needs counsel:** No
- **Owner answer:** Accepted default, 2026-11-08

### A4. What key type do warehouse and lakehouse dimensions use? (merged)
- **Proposed default:** Numeric surrogate keys in dimensional marts. Hash or string keys only where parallel, lookup-free loading is the priority, and recorded.
- **Alternatives:** Hash keys as default. String keys (dbt style). Natural keys. Each method or platform decides, with no framework default.
- **Consequence:** Numeric: best for joins and clustering, needs key lookups during load. Hash: parallel, repeatable loads, wider keys. String: simple in ELT, slower joins on Snowflake. Natural: weak where source keys change. No default: fits each method, joins across models need conversion.
- **Evidence basis:** Judgment. Vendors disagree (Kimball and Snowflake favour numeric; dbt strings; Databricks mixed). No benchmark. Also settles OR-3: confirm whether Data Vault is exempt.
- **Affected rules:** IDX-024, TYP-031, RPT-007
- **Needs counsel:** No
- **Owner answer:** Accepted default, 2026-11-08

### A5. Is master data shared across companies or held per company? (merged)
- **Proposed default:** Shared across the tenant, with optional per-company restriction for each class of master data.
- **Alternatives:** Tenant-shared with no override (Dynamics). Always per company.
- **Consequence:** Default: reuse with control where needed, and a recorded scope per class. No override: simplest, cannot limit a record to one company. Per company: most control, duplicated data, harder group reporting.
- **Evidence basis:** Vendor (Dynamics, Odoo disagree).
- **Affected rules:** TEN-022, FIN-046 (with TEN-019, FIN-044)
- **Needs counsel:** No
- **Owner answer:** Accepted default, 2026-11-08

### A6. How strict is legal document numbering, and how are numbers issued? (merged)
- **Proposed default:** Apply the strictest gap rule that applies to each legal entity and record every break. Issue numbers from a locked per-series counter inside the issuing transaction.
- **Alternatives:** Per-jurisdiction rule. Allow explained gaps everywhere (UK model). Plain sequence with documented gaps.
- **Consequence:** Default: conservative, one issuer at a time per series. Per-jurisdiction: less contention, needs counsel per country. UK model: cheapest, likely not compliant with French wording. Sequence: fast, cannot meet continuity wording.
- **Evidence basis:** Standard (statutes differ: France continuous, UK tolerates explained gaps, Saudi counter not reused). Vendor (PostgreSQL) for sequence gaps. The counter design is a judgment.
- **Affected rules:** TXN-018, NUM-018 (with NUM-016, NUM-019)
- **Needs counsel:** Yes
- **Owner answer:** Accepted default, 2026-11-08

### A7. Do foreign keys cross bounded contexts inside one database?
- **Proposed default:** Keep foreign keys inside one database until a boundary is approved for physical separation. Use plain IDs across separate stores.
- **Alternatives:** Plain IDs across every context, even in one database. Foreign keys everywhere with no separation path.
- **Consequence:** Default: keeps engine integrity, a later split must remove those keys. IDs everywhere: easy to separate, every reference needs an INT-002 exception. Foreign keys everywhere: strongest integrity, tight coupling.
- **Evidence basis:** Judgment. No source bans cross-context foreign keys.
- **Affected rules:** ERD-007 (with INT-002, INT-003)
- **Needs counsel:** No
- **Owner answer:** Accepted default, 2026-11-08

### A8. What is the default ON DELETE policy?
- **Proposed default:** CASCADE only for strict composition. RESTRICT or NO ACTION for independent objects. SET NULL only for optional links.
- **Alternatives:** CASCADE nearly always (GitLab). NO ACTION everywhere (PlanetScale). No cascades at all (Alibaba).
- **Consequence:** Default: each foreign key needs a classification, and mass deletion is limited. Cascade: automatic cleanup, more mass-deletion risk. NO ACTION: safest, the application does cleanup. No cascades: all cleanup moves to application code.
- **Evidence basis:** Judgment. Vendors disagree and no source settles it.
- **Affected rules:** INT-006
- **Needs counsel:** No
- **Owner answer:** Accepted default, 2026-11-08

### A9. Is the naming convention binding?
- **Proposed default:** Yes, for all new objects.
- **Alternatives:** Advisory only.
- **Consequence:** Binding: can be linted, with occasional exception requests. Advisory: drift returns and automated checks lose value.
- **Evidence basis:** Judgment. An organizational choice.
- **Affected rules:** NAM-002
- **Needs counsel:** No
- **Owner answer:** Accepted default, 2026-11-08

### A10. Which letter case do names use?
- **Proposed default:** Lowercase with underscores.
- **Alternatives:** Mixed case.
- **Consequence:** Lowercase: portable; Oracle and Snowflake display upper case. Mixed: needs quoting, against NAM-008.
- **Evidence basis:** Vendor and judgment.
- **Affected rules:** NAM-012
- **Needs counsel:** No
- **Owner answer:** Accepted default, 2026-11-08

### A11. Are table names singular or plural?
- **Proposed default:** Plural everywhere, including marts.
- **Alternatives:** Singular everywhere. Plural for operational tables and singular for dimensional objects.
- **Consequence:** Plural: matches more examples, differs from Django and Alibaba. Singular: simpler key names, needs overrides in Rails-style frameworks. Mixed: fits each community, two rules to lint.
- **Evidence basis:** Judgment. No source reports an outcome difference.
- **Affected rules:** NAM-013
- **Needs counsel:** No
- **Owner answer:** Accepted default, 2026-11-08

### A12. Are primary key columns named after the table, or just "id"?
- **Proposed default:** Named after the table (pattern NP-02), with matching foreign key names.
- **Alternatives:** Unqualified key name, as ORMs default to.
- **Consequence:** Named: joins read clearly, ORM mapping needs configuration. Unqualified: least ORM effort, every join needs table qualification.
- **Evidence basis:** Judgment.
- **Affected rules:** NAM-017, NAM-018
- **Needs counsel:** No
- **Owner answer:** Accepted default, 2026-11-08

### A13. How is money stored and named?
- **Proposed default:** Exact decimal. Integer minor units only as a marked exception.
- **Alternatives:** Integer minor units as the default.
- **Consequence:** Decimal: matches vendor manuals and handles varying scale, slower arithmetic. Integer: fast, needs currency-aware conversion everywhere.
- **Evidence basis:** Vendor. The naming patterns are a judgment.
- **Affected rules:** NAM-028, TYP-007
- **Needs counsel:** No
- **Owner answer:** Accepted default, 2026-11-08

### A14. What precision do stored exchange rates use? (merged)
- **Proposed default:** Exact decimal holding the full precision the rate source delivers. No framework-wide figure. Each deployment records its choice.
- **Alternatives:** One fixed framework-wide precision set by you. Adopt the rate provider's precision. Adopt the largest precision already in use across connected systems.
- **Consequence:** Delivered precision: no silent loss, columns may vary by provider. Fixed: uniform columns, but any figure today is unsupported and may truncate rates.
- **Evidence basis:** Judgment. No vendor or standard-setter states a precision. Also settles OR-2: FIN-023 asks you to set a number, while TYP-011 says set none.
- **Affected rules:** TYP-010, TYP-011, FIN-023
- **Needs counsel:** No
- **Owner answer:** Accepted default, 2026-11-08

### A15. How is deletion shown on operational tables?
- **Proposed default:** Mark at the aggregate root for a bounded grace period, then remove.
- **Alternatives:** Hard delete with a deleted-record archive. Per-row deleted flags.
- **Consequence:** Default: recoverable with little query burden, needs a purge job and a grace period. Archive: simple queries, archive stays in retention and erasure scope. Flags: familiar, burden on every query and foreign key, personal data remains.
- **Evidence basis:** Vendor and case study; sources disagree. Whether any form counts as erasure is separate (RET-037).
- **Affected rules:** AUD-025 (with RET-037)
- **Needs counsel:** No for the design. RET-037 covers the erasure effect and needs legal review.
- **Owner answer:** Accepted default, 2026-11-08

### A16. How are sensitive columns handled in change capture?
- **Proposed default:** Exclude or tokenize by default. Trails that must show prior values go in a classified, access-controlled store.
- **Alternatives:** Capture all values. Tokenize all sensitive values.
- **Consequence:** Default: fewer sensitive copies, excluded columns lose audit coverage. Capture all: complete history, sensitive values copied everywhere. Tokenize: keeps change evidence, needs token map management.
- **Evidence basis:** Standard (OWASP) against vendor practice. The reconciliation is a judgment.
- **Affected rules:** AUD-010 (with RET-039)
- **Needs counsel:** No
- **Owner answer:** Accepted default, 2026-11-08

### A17. At what level is accounting period status held?
- **Proposed default:** Per ledger and per application or module.
- **Alternatives:** Module or account type (SAP style). Book or document type (NetSuite, ERPNext style).
- **Consequence:** Default: precise control, more setup. Module or account type: simpler when ledgers are few. Book or document type: strongest for multi-book entities, most setup.
- **Evidence basis:** Vendor (ERP products each differ).
- **Affected rules:** FIN-002 (with FIN-001)
- **Needs counsel:** No
- **Owner answer:** Accepted default, 2026-11-08

### A18. Which validators does Stage 3 build?
- **Proposed default:** Build tenant key, money type and audit column checks as engine-neutral catalog queries. Raise TST-015 to TST-017 to RECOMMENDED.
- **Alternatives:** Keep them OPTIONAL and build on demand. Buy Atlas Pro or Liquibase Secure custom rules.
- **Consequence:** Default: no licence cost, Stage 3 owns upkeep; raising the level departs from the matrix and must be recorded. Optional: least work, policies rest on review. Buy: less code, licence cost, fewer engines.
- **Evidence basis:** Vendor (tool review; no tool ships a tenant key rule). The raise is a judgment.
- **Affected rules:** TST-007, TST-014, TST-015, TST-016, TST-017
- **Needs counsel:** No
- **Owner answer:** Accepted default, 2026-11-08

---

## B. Important defaults

### B1. Should core practices become framework-level MANDATORY? (merged)
- **Proposed default:** Keep them RECOMMENDED until you approve a raise.
- **Alternatives:** Raise selected items as internal MANDATORY with status needs_decision.
- **Consequence:** Keep: follows the matrix and leaves discretion to teams. Raise: firmer gates for ERP and finance, based on an organizational choice and not an outside authority.
- **Evidence basis:** Judgment. The matrix keeps these RECOMMENDED.
- **Affected rules:** MIG-001, MIG-002, TST-011, BDR-009, DQA-004, DQA-015, GOV-002, PIP-027 (examples named by the groups)
- **Needs counsel:** No
- **Owner answer:** Accepted default, 2026-11-08

### B2. Must migrations be reversible?
- **Proposed default:** Forward-only with backward compatibility. Down scripts optional and tested.
- **Alternatives:** Reversible by default with exceptions (GitLab). Backup restore as the only rollback.
- **Consequence:** Default: fewer scripts, needs expand and contract discipline. Reversible: more work and false comfort for drops. Restore: simplest, means downtime and data loss.
- **Evidence basis:** Vendor; sources disagree.
- **Affected rules:** MIG-005
- **Needs counsel:** No
- **Owner answer:** Accepted default, 2026-11-08

### B3. How are migrations authored?
- **Proposed default:** Hybrid, with the planned migration checked in.
- **Alternatives:** Migration-based only. State-based only.
- **Consequence:** Default: needs tooling and plan review. Migration-based: builds history and handles renames explicitly. State-based: least work, risks data loss on renames.
- **Evidence basis:** Judgment. No benchmark.
- **Affected rules:** MIG-003
- **Needs counsel:** No
- **Owner answer:** Accepted default, 2026-11-08

### B4. Is the transaction per migration or per DDL statement?
- **Proposed default:** Per DDL on high-traffic OLTP. Per migration elsewhere.
- **Alternatives:** Per migration always. Per DDL always.
- **Consequence:** Default: needs a traffic classification. Per migration: atomic, holds several locks. Per DDL: shortest locks, partial failure needs manual repair.
- **Evidence basis:** Vendor.
- **Affected rules:** MIG-014
- **Needs counsel:** No
- **Owner answer:** Accepted default, 2026-11-08

### B5. Where do small data changes go?
- **Proposed default:** A separate, reviewed data migration in the same history.
- **Alternatives:** Inside the schema migration. Outside migrations.
- **Consequence:** Default: traceable, one more file. Inside: simple, longer locks. Outside: keeps migrations pure, loses ordering with schema.
- **Evidence basis:** Vendor and judgment.
- **Affected rules:** MIG-013
- **Needs counsel:** No
- **Owner answer:** Accepted default, 2026-11-08

### B6. What lock and runtime limits do migrations use?
- **Proposed default:** Set per system from rehearsal. No framework-wide number.
- **Alternatives:** About 2 s lock hold (Braintree). 10 s lock timeout (strong_migrations). 15 s statement timeout (GitLab).
- **Consequence:** Default: fits each system, needs measurement. 2 s: strictest, more retries. 10 s: longer queueing. 15 s: limits statements, not lock hold.
- **Evidence basis:** Judgment. No independent evidence for any value.
- **Affected rules:** MIG-008
- **Needs counsel:** No
- **Owner answer:** Accepted default, 2026-11-08

### B7. Is an immutable backup copy required?
- **Proposed default:** One immutable copy for systems of record, with compliance and misconfiguration reviewed.
- **Alternatives:** Offline copy only. Adopt 3-2-1-1-0.
- **Consequence:** Default: resists deletion, adds cost, may conflict with erasure duties. Offline: cheaper, slower to restore. 3-2-1-1-0: most protection, rests on vendor marketing.
- **Evidence basis:** Judgment. CISA cautions and one vendor promotion.
- **Affected rules:** BDR-013 (with BDR-012, RET-026)
- **Needs counsel:** No, but check against B8.
- **Owner answer:** Accepted default, 2026-11-08

### B8. How are erasures handled in EU and UK backups?
- **Proposed default:** Put erased data beyond use, keep a durable register, re-apply on restore, and set a defined backup expiry.
- **Alternatives:** Immediate deletion from backups. Delay until restore or next use (California model).
- **Consequence:** Default: follows ICO and EDPB patterns, undue delay is unsettled. Immediate: strongest position, may harm backup integrity. California: lawful in CCPA scope only.
- **Evidence basis:** Standard (regulators disagree).
- **Affected rules:** RET-026 (with RET-025, RET-027)
- **Needs counsel:** Yes
- **Owner answer:** Accepted default, 2026-11-08

### B9. What retention period applies to French commercial accounting documents?
- **Proposed default:** Set no binding period until counsel confirms. Plan on the longer of the tax and commercial periods.
- **Alternatives:** Adopt 10 years now (unverified). Apply only the 6-year tax period.
- **Consequence:** Default: no compliance claim. 10 years: over-retention risk. 6 years: possible under-retention.
- **Evidence basis:** Standard, but the commercial period is unverified.
- **Affected rules:** RET-006 (with RET-005)
- **Needs counsel:** Yes
- **Owner answer:** Accepted default, 2026-11-08

### B10. May generated year-end vouchers be deleted on reversal?
- **Proposed default:** Post a reversing voucher. Do not delete.
- **Alternatives:** Delete with a history record (D365). Keep only a record of deletion (NetSuite).
- **Consequence:** Default: non-alteration met, more entries. Deletion: simpler, legally unresolved under German HGB 239(3).
- **Evidence basis:** Standard against vendor practice.
- **Affected rules:** FIN-039 (with FIN-031, FIN-034)
- **Needs counsel:** Yes
- **Owner answer:** Accepted default, 2026-11-08

### B11. Which reversal method does the ledger use?
- **Proposed default:** A posted inverse entry.
- **Alternatives:** Negative posting (SAP). Change Sign or Switch Debit or Credit (Oracle).
- **Consequence:** Default: activity totals rise, history is clear. Negative posting: activity resets. Change Sign: keeps the column and flips the sign.
- **Evidence basis:** Vendor.
- **Affected rules:** FIN-035
- **Needs counsel:** No
- **Owner answer:** Accepted default, 2026-11-08

### B12. Can a reversal be reversed?
- **Proposed default:** No. Use a new entry.
- **Alternatives:** Allow it (D365).
- **Consequence:** Default: simpler audit trail, one more entry. Allow: faster correction, longer chain.
- **Evidence basis:** Vendor (Oracle forbids, D365 allows).
- **Affected rules:** FIN-036
- **Needs counsel:** No
- **Owner answer:** Accepted default, 2026-11-08

### B13. Is an irreversible period close offered?
- **Proposed default:** Reopenable close with restricted reopening.
- **Alternatives:** Offer permanent close (Oracle, Odoo). Offer it but advise against use (D365).
- **Consequence:** Default: recoverable, weaker assurance. Permanent: strong assurance, no late corrections. Advise against: flexible, relies on discipline.
- **Evidence basis:** Vendor.
- **Affected rules:** FIN-009
- **Needs counsel:** No
- **Owner answer:** Accepted default, 2026-11-08

### B14. How are exchange rates dated?
- **Proposed default:** Exact-day row per currency pair and rate type.
- **Alternatives:** Most recent on or before, with a staleness limit (ERPNext style).
- **Consequence:** Default: precise, fails visibly on gaps. Alternative: tolerates gaps, can use stale rates; the limit has no sourced value.
- **Evidence basis:** Vendor.
- **Affected rules:** FIN-015
- **Needs counsel:** No
- **Owner answer:** Accepted default, 2026-11-08

### B15. How are inverse rates handled?
- **Proposed default:** Store each direction.
- **Alternatives:** Derive the reciprocal (Oracle). Quotation convention (SAP).
- **Consequence:** Default: more rows, no disagreement. Derive: less storage, rounding differences. Quotation: depends on rate setup.
- **Evidence basis:** Vendor.
- **Affected rules:** FIN-016
- **Needs counsel:** No
- **Owner answer:** Accepted default, 2026-11-08

### B16. Does revaluation reverse in the next period?
- **Proposed default:** Reverse for AR and AP only.
- **Alternatives:** Carry forward everywhere. Reverse everywhere.
- **Consequence:** Default: matches the D365 split. Carry forward: fewer entries, comparability differs. Reverse everywhere: uniform, contradicts D365 GL.
- **Evidence basis:** Vendor (one vendor's split).
- **Affected rules:** FIN-020
- **Needs counsel:** No
- **Owner answer:** Accepted default, 2026-11-08

### B17. How is currency triangulation handled?
- **Proposed default:** None proposed. Decide if the business needs it.
- **Alternatives:** Direct rates only (D365, NetSuite). Define a method after research.
- **Consequence:** Direct only: no method needed, setup per pair. Defined method: needs a source first.
- **Evidence basis:** Judgment. No method is sourced.
- **Affected rules:** FIN-024
- **Needs counsel:** No
- **Owner answer:** Accepted default, 2026-11-08

### B18. What is the rule for backdated changes to valid-time data?
- **Proposed default:** SQL:2011 period split.
- **Alternatives:** Out-of-order overwrite (Workday).
- **Consequence:** Default: preserves prior periods, more rows. Overwrite: simple, reconstruction needs system time.
- **Evidence basis:** Standard against vendor. The choice is yours; the matrix leaves it open.
- **Affected rules:** AUD-024
- **Needs counsel:** No
- **Owner answer:** Accepted default, 2026-11-08

### B19. How do idempotency replay and retention work?
- **Proposed default:** Replay the saved outcome. Keep records at least 24 hours.
- **Alternatives:** Retry to completion (Stripe API v2). Keep about 72 hours.
- **Consequence:** Default: predictable, a saved server error repeats until expiry. Retry: better completion, needs a completer. 72 hours: covers longer retries, more storage.
- **Evidence basis:** Vendor; sources disagree.
- **Affected rules:** TXN-010
- **Needs counsel:** No
- **Owner answer:** Accepted default, 2026-11-08

### B20. Which mapping is used for supertype and subtype hierarchies?
- **Proposed default:** Class-table when a subtype attribute must be required or a subtype takes part in a foreign key. Single-table otherwise.
- **Alternatives:** Class-table always. Single-table always. Concrete-table.
- **Consequence:** Default: decision per hierarchy, enforces required values where it matters. Class-table: strongest constraints, more joins. Single-table: simplest, required values cannot use NOT NULL. Concrete: no shared foreign key target.
- **Evidence basis:** Judgment. No independent benchmark.
- **Affected rules:** MOD-004
- **Needs counsel:** No
- **Owner answer:** Accepted default, 2026-11-08

### B21. How are enumerated values stored?
- **Proposed default:** A reference table when the set can change or has attributes.
- **Alternatives:** CHECK on text. Native enumeration.
- **Consequence:** Reference table: changes are data, one more join. CHECK: simple, each change is a migration. Native: compact, PostgreSQL cannot remove values.
- **Evidence basis:** Vendor; sources disagree.
- **Affected rules:** TYP-022
- **Needs counsel:** No
- **Owner answer:** Accepted default, 2026-11-08

### B22. What minimum scale do mixed-currency columns use?
- **Proposed default:** At least 4.
- **Alternatives:** Exact per-currency scale only, no minimum.
- **Consequence:** 4: holds CLF and UYW without per-currency handling. Per-currency: tighter, but a mixed column must still accept the largest.
- **Evidence basis:** Judgment (low-confidence inference from ISO 4217).
- **Affected rules:** TYP-004
- **Needs counsel:** No
- **Owner answer:** Accepted default, 2026-11-08

### B23. How are quantity scale and unit set?
- **Proposed default:** Unit stored or fixed by definition, with scale declared per unit.
- **Alternatives:** One fixed scale for all quantities.
- **Consequence:** Per unit: accurate, more design records. Fixed: uniform, wastes storage or rounds small units.
- **Evidence basis:** Judgment. No source.
- **Affected rules:** TYP-009
- **Needs counsel:** No
- **Owner answer:** Accepted default, 2026-11-08

### B24. What is the default analytical consumption shape?
- **Proposed default:** Star schema, with wide tables as derived layers.
- **Alternatives:** Wide tables as primary. Nested structures where the engine favours them.
- **Consequence:** Star: simpler conformance, more joins. Wide: simpler queries, higher update and storage cost. Nested: engine-specific.
- **Evidence basis:** Judgment. Benchmarks conflict.
- **Affected rules:** RPT-001 (with NRM-007)
- **Needs counsel:** No
- **Owner answer:** Accepted default, 2026-11-08

### B25. Which reprocessing architecture is used?
- **Proposed default:** One implementation of the logic, replay-based or unified.
- **Alternatives:** Lambda with dual paths.
- **Consequence:** One implementation: no logic drift, needs long retention and replay capacity. Lambda: separate batch truth, duplicated logic.
- **Evidence basis:** Vendor; one-sided and unmeasured.
- **Affected rules:** PIP-024
- **Needs counsel:** No
- **Owner answer:** Accepted default, 2026-11-08

### B26. Must financial quality failures block publication?
- **Proposed default:** Yes for amount and completeness checks. Tiered for the rest.
- **Alternatives:** All checks block. Tiered, with warnings only.
- **Consequence:** Selected: protects figures, some delay. All: strongest, more delays. Warnings: no delay, risk of wrong figures.
- **Evidence basis:** Case study (one source).
- **Affected rules:** DQA-010
- **Needs counsel:** No
- **Owner answer:** Accepted default, 2026-11-08

### B27. What tolerance applies between subledger and general ledger?
- **Proposed default:** Classify and explain every difference. No numeric tolerance.
- **Alternatives:** Zero difference required. A numeric tolerance per account.
- **Consequence:** Classified: matches Oracle evidence. Zero: stronger control, no source. Numeric: practical, needs your values.
- **Evidence basis:** Vendor (Oracle only).
- **Affected rules:** DQA-017
- **Needs counsel:** No
- **Owner answer:** Accepted default, 2026-11-08

### B28. Who sets freshness and quality thresholds?
- **Proposed default:** Each dataset owner, recorded in the contract. No framework-wide values.
- **Alternatives:** Framework-wide numeric defaults by tier.
- **Consequence:** Owner-set: fits the evidence, values vary. Framework-wide: consistent, no source supports any number.
- **Evidence basis:** Judgment. No numeric source.
- **Affected rules:** MON-006
- **Needs counsel:** No
- **Owner answer:** Accepted default, 2026-11-08

### B29. How are late-arriving dimensions handled? (no rule yet)
- **Proposed default:** A placeholder member, updated when the dimension arrives.
- **Alternatives:** Hold the fact until the dimension arrives. Assign the default unknown member.
- **Consequence:** Placeholder: keeps facts complete, needs update logic. Hold: delays facts. Default member: simple, loses attribution.
- **Evidence basis:** Judgment. No source prescribes any option.
- **Affected rules:** None yet (related: RPT-010, RPT-006)
- **Needs counsel:** No
- **Owner answer:** Accepted default, 2026-11-08

### B30. What is the portable maximum identifier length?
- **Proposed default:** 63 ASCII characters.
- **Alternatives:** The limit of the single engine in use. 30 bytes.
- **Consequence:** 63: safe on every current engine researched. Single-engine: more room, a later move can fail. 30: needed only for old Oracle, heavy abbreviation.
- **Evidence basis:** Vendor (engine limits).
- **Affected rules:** NAM-010 (with NAM-009)
- **Needs counsel:** No
- **Owner answer:** Accepted default, 2026-11-08

### B31. How strict are abbreviations?
- **Proposed default:** Full words, with an approved abbreviation list.
- **Alternatives:** No abbreviations at all. Short names favoured (MySQL).
- **Consequence:** List: readable, small upkeep. None: long names can hit the limit. Short: compact, harder to find, against Oracle and dbt guidance.
- **Evidence basis:** Vendor; sources disagree.
- **Affected rules:** NAM-014
- **Needs counsel:** No
- **Owner answer:** Accepted default, 2026-11-08

### B32. How are constraints and indexes named?
- **Proposed default:** GitLab-style typed prefixes with table and columns.
- **Alternatives:** Shorter prefixes. Engine-generated names.
- **Consequence:** Typed: comparable across environments, long names. Shorter: less length pressure, no named source. Generated: differ per environment, break migrations.
- **Evidence basis:** Vendor (GitLab).
- **Affected rules:** NAM-023
- **Needs counsel:** No
- **Owner answer:** Accepted default, 2026-11-08

---

## C. Minor

### C1. Mark third-party identifiers differently from real keys?
- **Proposed default:** Yes.
- **Alternatives:** Treat all identifiers alike.
- **Consequence:** Adopt: real keys stand apart from outside references. Decline: guessing relationships by name becomes unreliable.
- **Evidence basis:** Judgment.
- **Affected rules:** NAM-019
- **Needs counsel:** No
- **Owner answer:** Accepted default, 2026-11-08

### C2. Adopt naming patterns that show meaning (booleans, dates, measures)?
- **Proposed default:** Yes.
- **Alternatives:** No semantic patterns.
- **Consequence:** Adopt: intent visible in the name; inherited schemas are exempt from renames. Decline: meaning must be looked up.
- **Evidence basis:** Judgment.
- **Affected rules:** NAM-020, NAM-021, NAM-028
- **Needs counsel:** No
- **Owner answer:** Accepted default, 2026-11-08

### C3. How are status columns named?
- **Proposed default:** Qualified by lifecycle.
- **Alternatives:** One standard unqualified name.
- **Consequence:** Qualified: a table can track several lifecycles. Unqualified: shorter, breaks once a second lifecycle appears.
- **Evidence basis:** Judgment. No source.
- **Affected rules:** NAM-022
- **Needs counsel:** No
- **Owner answer:** Accepted default, 2026-11-08

### C4. How are schemas named?
- **Proposed default:** By business domain.
- **Alternatives:** Team or technology names.
- **Consequence:** Domain: stable through reorganizations. Team: clearer today, renames follow reorganizations.
- **Evidence basis:** Judgment. No source.
- **Affected rules:** NAM-024
- **Needs counsel:** No
- **Owner answer:** Accepted default, 2026-11-08

### C5. Which words name warehouse layers?
- **Proposed default:** Raw, staging, intermediate, marts.
- **Alternatives:** Bronze, silver, gold.
- **Consequence:** Default: says what each layer does, matches dbt. Medallion: matches Databricks and Fabric, less precise at silver.
- **Evidence basis:** Vendor; sources disagree.
- **Affected rules:** NAM-025
- **Needs counsel:** No
- **Owner answer:** Accepted default, 2026-11-08

### C6. Use snapshot schemas and mart role markers?
- **Proposed default:** Yes, as in the pattern table.
- **Alternatives:** No markers, layer schema only.
- **Consequence:** Markers: role visible in the name, only the dimension marker has a source. None: shorter, role documented elsewhere.
- **Evidence basis:** Vendor for the dimension marker. Judgment for the rest.
- **Affected rules:** NAM-026, NAM-027
- **Needs counsel:** No
- **Owner answer:** Accepted default, 2026-11-08

### C7. Keep source names in the raw layer?
- **Proposed default:** Yes, in raw only.
- **Alternatives:** Rename at ingest.
- **Consequence:** Preserve: direct trace to source, unsafe names in raw. Rename: uniform, loses direct trace.
- **Evidence basis:** Judgment.
- **Affected rules:** NAM-007
- **Needs counsel:** No
- **Owner answer:** Accepted default, 2026-11-08

### C8. Which terms describe distributed trade-offs in design documents?
- **Proposed default:** PACELC terms.
- **Alternatives:** Brewer's partition-mode framing. Kleppmann's delay-sensitivity framework.
- **Consequence:** PACELC: covers normal operation, do not reuse the 2012 classifications. Brewer: strong on partitions, thin on normal operation. Kleppmann: precise, less familiar.
- **Evidence basis:** Judgment. Foundational papers differ.
- **Affected rules:** TXN-023
- **Needs counsel:** No
- **Owner answer:** Accepted default, 2026-11-08

### C9. Adopt or build a sharding layer?
- **Proposed default:** Adopt, unless a recorded reason requires building.
- **Alternatives:** Build. Consensus-based distributed SQL.
- **Consequence:** Adopt: faster start, limited by the layer. Build: full control, lasting cost. Distributed SQL: no layer to run, different engine and migration risk.
- **Evidence basis:** Case study. Judgment on the default.
- **Affected rules:** SCL-008
- **Needs counsel:** No
- **Owner answer:** Accepted default, 2026-11-08

### C10. Which online schema change tool for large MySQL-family tables?
- **Proposed default:** Log-based (gh-ost) unless constraints rule it out.
- **Alternatives:** Trigger-based (pt-online-schema-change). Platform workflow where offered.
- **Consequence:** Log-based: no trigger overhead, needs binlog access. Trigger-based: works without binlog access, cannot run on tables with triggers. Platform: least work, tied to the platform.
- **Evidence basis:** Judgment. Both projects describe themselves.
- **Affected rules:** MIG-011
- **Needs counsel:** No
- **Owner answer:** Accepted default, 2026-11-08

### C11. Which data quality vocabulary is used?
- **Proposed default:** DAMA UK six dimensions plus currency, mapped to ISO/IEC 25012.
- **Alternatives:** ISO/IEC 25012 as primary. ISO 8000-61 process model. Local vocabulary.
- **Consequence:** DAMA UK: simple, voluntary. ISO 25012: formal, official text not read. ISO 8000-61: a process model, not a vocabulary. Local: flexible, not comparable.
- **Evidence basis:** Standard (secondary reading only).
- **Affected rules:** DQA-012
- **Needs counsel:** No
- **Owner answer:** Accepted default, 2026-11-08

---

## Housekeeping confirmations

### H1. Who approves exceptions?
RULE_FORMAT defines no roles, so each group picked its own approver name. "Framework owner" and "schema owner" are placeholders.

| Name in exceptions field | Rules | Groups |
|---|---:|---|
| dataset owner | 61 | PIP, DQA, RPT, MON, GOV |
| framework owner | 56 | ARC, MOD, ERD, NRM, INT, some PIP, DQA, RPT |
| schema owner | 21 | IDX, TXN, SCL |
| system owner | 14 | TEN, SEC, AUD, MIG, FIN, NUM |
| data architecture owner | 10 | NAM, TYP |
| database owner | 9 | MIG, TST |
| data owner | 9 | TEN, SEC, AUD, BDR, FIN, RET |
| finance owner | 6 | TEN, FIN |
| Others, one each (context, developer, data platform, recorded, security owner) | 5 | NAM, MIG, BDR |

- **Proposed default (judgment):** Name one role for framework-level exceptions, replacing framework owner, schema owner and data architecture owner. Keep dataset, system and finance owner as per-asset roles.
- **Alternatives:** Keep every name as written. Name a separate role per group.
- **Consequence:** One role: clear approval path, one person may become a bottleneck. As written: no edits, unclear who approves. Per group: matches team structure, more roles to staff.
- **Owner answer:** Accepted default, 2026-11-08

### H2. How are method-scoped MANDATORY rules treated?
RPT-003, RPT-004, RPT-006 and RPT-015 bind only teams using the Kimball or Data Vault method. Each rests on a single method owner, which RULE_FORMAT does not list as an authority type. The same matrix row is treated differently elsewhere: RPT-006 is MANDATORY, and TYP-037 is RECOMMENDED (see OR-1).

- **Proposed default:** Keep them MANDATORY, scoped to teams claiming that method, as the matrix does. Then align TYP-037 to match.
- **Alternatives:** Lower all to RECOMMENDED, which matches RULE_FORMAT and TYP-037, and weakens the method's definition.
- **Consequence:** Keep: matches the matrix; needs a recorded exception to RULE_FORMAT. Lower: consistent with the format wording.
- **Evidence basis:** Vendor (single method owner).
- **Affected rules:** RPT-003, RPT-004, RPT-006, RPT-015, TYP-037, INT-013 (note only)
- **Needs counsel:** No
- **Owner answer:** Accepted default, 2026-11-08

### H3. Other single-vendor MANDATORY rules (for confirmation)
TXN-019, SCL-006, TEN-012, AUD-012, PIP-009 and PIP-011 are MANDATORY and active on single-vendor evidence. The groups retained them on engine behaviour, which RULE_FORMAT allows. TEN-012 and AUD-012 are the least engine-defined.

- **Proposed default:** Keep as written.
- **Alternatives:** Review TEN-012 and AUD-012 for RECOMMENDED.
- **Owner answer:** Accepted default, 2026-11-08

---

## Source trace

| Source file | Items | Destination |
|---|---:|---|
| 01 modeling | 4 | MOD-004 B20. ERD-007 A7. INT-006 A8. INT-016 A3. |
| 02 naming and types | 20 | #1 A9. #2 A10. #3 A11. #4 B30. #5 B31. #6 A12. #7 C1. #8 C2. #9 C3. #10 B32. #11 C4. #12 C5. #13 C6. #14 A13. #15 B21. #16 A4. #17 A14. #18 B23. #19 B22. #20 C7. |
| 03 performance | 6 | IDX-023 A3. IDX-024 A4. TXN-010 B19. TXN-018 A6. TXN-023 C8. SCL-008 C9. |
| 04 tenancy | 6 | D1 A1. D2 A2. D3 A5. D4 B18. D5 A15. D6 A16. |
| 05 migrations | 9 | D1 B2. D2 B3. D3 B6. D4 C10. D5 B5. D6 B4. D7 B7. D8 A18. D9 B1. |
| 06 pipelines | 10 | #1 B24. #2 A4. #3 B25. #4 C11. #5 B26. #6 B27. #7 B28. #8 H2. #9 B1. #10 B29. |
| 07 finance | 14 | FIN-002 A17. FIN-009 B13. FIN-015 B14. FIN-016 B15. FIN-020 B16. FIN-023 A14. FIN-024 B17. FIN-035 B11. FIN-036 B12. FIN-039 B10. FIN-046 A5. NUM-018 A6. RET-006 B9. RET-026 B8. |
