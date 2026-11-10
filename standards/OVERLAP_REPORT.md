# Overlap Report

Stage 2 rule groups compared across all 540 rules. The owner accepted all defaults on 2026-11-08. The Outcome column shows what was applied to `rules/` and `registry/`.

**Method:** Every rule statement was read. Matrix rows cited by more than one rule group were listed by script, then each candidate was read in full. Cross-references between rules were checked and none point to a missing rule.

**Summary**

| Type | Count | Meaning |
|---|---:|---|
| Contradiction | 5 | Same requirement, different level, status or default. |
| Duplicate | 22 | Same requirement written twice. |
| Overlap | 25 | Partly the same, or the rules depend on each other, with no conflict today. |
| **Total** | **52** | |

Most duplicates come from the groups working from the same matrix row. One rule is kept for each requirement. The other keeps its ID, takes status `superseded` and names the canonical rule in `superseded_by`. IDs are never reused or deleted.

**Outcomes:** 5 contradictions resolved. 22 duplicates reduced to one canonical rule each (OR-20 leaves one owner question open). 25 overlaps left in place, of which OR-29, OR-32 and OR-52 gained cross-references. 28 rules are superseded in total.

## Results of the checks you named

| Check | Result | Items |
|---|---|---|
| TXN-012 against pipeline rules | Overlap, no conflict | OR-28 |
| TXN-014 against FIN-034 | Duplicate | OR-6 |
| TXN-015 against FIN-031 | Duplicate | OR-7 |
| TXN-017 against NUM-001 | Duplicate | OR-8 |
| IDX-023 and 024 against group 01, TYP and RPT | Contradiction on warehouse keys; overlap on OLTP keys | OR-3, OR-29 |
| TYP-032 against INT | Overlap, complementary | OR-30 |
| TYP-035 against INT | Duplicate | OR-20 |
| Matrix rows MT-11 to MT-20, TEN against FIN | Nine duplicate pairs. MT-16 is in TEN only, and rightly so. | OR-9 to OR-17 |
| ERD-007 against INT-002 | Overlap, consistent under the accepted default | OR-31 |
| AUD-025 against RET-037 | Overlap, complementary, gap fixed | OR-32 |

## Contradictions

| ID | Rules | Type | What differs | Recommended resolution | Outcome |
|---|---|---|---|---|---|
| OR-1 | RPT-006, TYP-037 (INT-013 note) | contradiction | Same matrix row RP-5. RPT-006 is MANDATORY. TYP-037 is RECOMMENDED, with the note that a method owner is not an authority. INT-013 says it is mandatory by the method. | Owner decides under H2. Set both to the same level and keep RPT-006 as the home rule. | Resolved under H2. TYP-037 aligned to MANDATORY, then superseded by RPT-006, the home rule. INT-013 note points to RPT-006. |
| OR-2 | FIN-023, TYP-010, TYP-011 | contradiction | Same row FN-19. TYP-011 is RECOMMENDED and provisional: record the choice and set no figure. FIN-023 is OPTIONAL and needs_decision, and asks the owner to set a figure. | Owner decides under A14. Keep TYP-010 and TYP-011 as the rule. Make FIN-023 a pointer. | Resolved under A14. TYP-010 and TYP-011 are the rule, provisional, no value set. FIN-023 superseded by TYP-011. |
| OR-3 | IDX-024, TYP-031, RPT-007 | contradiction | IDX-024 defaults to integers and exempts Data Vault and dbt-led models. TYP-031 applies to Data Vault too. RPT-007 says decide per platform. Three different approvers. | Owner decides under A4, including whether Data Vault is exempt. Keep one rule, with the others as pointers. | Resolved under A4. IDX-024 is canonical and active: numeric keys in dimensional marts, with Data Vault and other integration layers outside the default. TYP-031 and RPT-007 superseded by IDX-024. |
| OR-4 | TXN-018, NUM-016, NUM-019 | contradiction | Same counter mechanism. TXN-018 is needs_decision. NUM-016 and NUM-019 are provisional, as if settled. TXN-018 says inside the issuing transaction; NUM-019 says at posting. | Owner decides under A6, including whether numbers are issued at issue or at posting. Align the statuses after that. Keep NUM rules as home. | Resolved under A6. Numbers are issued inside the issuing transaction. NUM-016, NUM-018 and NUM-019 are all provisional pending counsel. TXN-018 superseded by NUM-019. |
| OR-5 | TXN-016, FIN-026 | contradiction | Same row TX-11 and same case-study evidence. TXN-016 is provisional. FIN-026 is active. TXN-016 covers all ledgers; FIN-026 covers multi-currency ledgers only. | Owner to pick one status. Group 03's own definition makes case-study rules provisional, which points to provisional. Keep FIN-026 as home with the wider scope. | Resolved as the report recommends. FIN-026 is the home rule, widened to all ledgers and set provisional. TXN-016 superseded by FIN-026. |

## Duplicates

| ID | Rules | Type | Note | Recommended resolution | Outcome |
|---|---|---|---|---|---|
| OR-6 | TXN-014, FIN-034 | duplicate | Same requirement and level. Approvers differ (schema owner against system owner and finance controller). | Keep FIN-034. TXN-014 becomes a pointer. | Resolved. TXN-014 superseded by FIN-034. |
| OR-7 | TXN-015, FIN-031 | duplicate | Same statutes. Both MANDATORY and provisional. | Keep FIN-031. TXN-015 becomes a pointer. | Resolved. TXN-015 superseded by FIN-031. |
| OR-8 | TXN-017, NUM-001 | duplicate | Same VAT Directive duty. Both MANDATORY and provisional. | Keep NUM-001. TXN-017 becomes a pointer. | Resolved. TXN-017 superseded by NUM-001. |
| OR-9 | TEN-019, FIN-044 (MT-11) | duplicate | Company identifier on ERP tables. Exception wording differs. | Keep TEN-019 for the tenancy boundary. | Resolved. FIN-044 superseded by TEN-019, with its exception merged. |
| OR-10 | TEN-020, FIN-043 (MT-12) | duplicate | One company per posting. FIN-043 allows NetSuite-style postings; TEN-020 points to intercompany rules. | Keep FIN-043. Align the exception. | Resolved. TEN-020 superseded by FIN-043, with the exception aligned. |
| OR-11 | TEN-021, FIN-047 (MT-13) | duplicate | Intercompany linked entries. | Keep FIN-047. | Resolved. TEN-021 superseded by FIN-047. |
| OR-12 | TEN-022, FIN-046 (MT-14) | duplicate | Master data scope. Same default. | One rule after A5. Keep TEN-022 for the tenancy boundary. | Resolved under A5. FIN-046 superseded by TEN-022. |
| OR-13 | TEN-024, FIN-050 (MT-15) | duplicate | Consolidation hierarchy. Scope differs (data_warehouse against OLAP). | Keep FIN-050 and settle the scope. | Resolved. TEN-024 superseded by FIN-050. Scope settled as OLTP, OLAP and data_warehouse, with analytical stores in scope only where consolidation is run there. |
| OR-14 | TEN-025, FIN-042 (MT-17) | duplicate | Legal entity, ledger, business unit distinct. | Keep FIN-042. | Resolved. TEN-025 superseded by FIN-042. |
| OR-15 | TEN-026, FIN-051 (MT-18) | duplicate | IFRS 10 consolidation. Wording differs slightly (data for statements against statements from ledgers). | Keep FIN-051. | Resolved. TEN-026 superseded by FIN-051. |
| OR-16 | TEN-027, FIN-048 (MT-19) | duplicate | Where elimination lives. | Keep FIN-048. | Resolved. TEN-027 superseded by FIN-048. |
| OR-17 | TEN-028, FIN-049 (MT-20) | duplicate | Intercompany currency differences. | Keep FIN-049. | Resolved. TEN-028 superseded by FIN-049. |
| OR-18 | TEN-018, FIN-045 | duplicate | Tenant and legal entity are separate. No matrix row. | Keep TEN-018. | Resolved. FIN-045 superseded by TEN-018. |
| OR-19 | INT-008, TYP-033 (RI-5) | duplicate | NOT NULL by default. Exceptions differ. | Keep INT-008. | Resolved. TYP-033 superseded by INT-008. |
| OR-20 | INT-009, TYP-035 (RI-6) | duplicate | CHECK needs NOT NULL. TYP-035 has an exception for present-only rules; INT-009 has none. | Keep INT-009. Owner to confirm whether the exception survives. | Resolved in part. TYP-035 superseded by INT-009. Still open for the owner: whether TYP-035's present-only exception survives. INT-009 exceptions stay none; its applies_when already limits it to rules that must hold for every row. |
| OR-21 | INT-010, TYP-034 (RI-7) | duplicate | NULLs in UNIQUE. TYP-034 also covers warehouses. | Keep TYP-034 for its wider scope. | Resolved. INT-010 superseded by TYP-034. |
| OR-22 | INT-014, DQA-004, TST-008 (RI-11, TS-8) | duplicate | Key tests in analytical models. | Keep DQA-004 for the requirement. TST-008 stays as the test method. | Resolved. INT-014 superseded by DQA-004. TST-008 stays as the test method. |
| OR-23 | NRM-006, RPT-002 (RP-2) | duplicate | Optional integration layer. | Keep RPT-002. | Resolved. NRM-006 superseded by RPT-002. |
| OR-24 | MOD-006, TYP-024 | duplicate | Keys and money as typed columns, not JSON. | Keep TYP-024. | Resolved. MOD-006 superseded by TYP-024, which now also covers entity-attribute-value tables. |
| OR-25 | AUD-019, TYP-015 | duplicate | Closed-open periods. TYP-015 also covers BETWEEN. | Keep TYP-015. | Resolved. AUD-019 superseded by TYP-015. |
| OR-26 | AUD-022, INT-011 | duplicate | Non-overlapping periods. | Keep INT-011. | Resolved. AUD-022 superseded by INT-011. |
| OR-27 | AUD-026, RPT-008 | duplicate | Slowly changing dimension choice. | Keep RPT-008. | Resolved. AUD-026 superseded by RPT-008, which keeps its Type 2 wording. |

## Overlaps

| ID | Rules | Type | Note | Recommended resolution | Outcome |
|---|---|---|---|---|---|
| OR-28 | TXN-012, PIP-001, PIP-004, PIP-005 | overlap | Both MANDATORY rules cover streaming re-runs. TXN-012 says "pipeline steps", and PIP-001 owns those. PIP-004 and PIP-005 are mechanisms. | Keep TXN-012 for service consumers and outbox relays. Keep PIP-001 for pipeline writes. Drop "pipeline steps" from TXN-012 when the owner allows edits. | Left unchanged, no conflict. The owner has not allowed the TXN-012 edit. |
| OR-29 | IDX-023, INT-016, TYP-029, TYP-030, NAM-017, TEN-014, SCL-006 | overlap | Consistent, but split across groups. Exception approvers differ for natural keys. IDX-023 and NAM-017 assume a single-column key; TEN-014 and SCL-006 add the tenant or distribution column. | Settle under A3. Record that the key is composite in pooled and sharded tables. | Reconciled under A3. IDX-023 and NAM-017 now record that the key is composite in pooled and sharded tables. |
| OR-30 | TYP-032, INT-001, DQA-004 | overlap | INT-001 requires a key on OLTP tables. TYP-032 requires NOT NULL on key columns everywhere. DQA-004 tests it. | Keep all three. | Left unchanged, no conflict. |
| OR-31 | ERD-007, INT-002, ARC-006 | overlap | Each refers to the other correctly. It becomes a conflict only if A7's alternative "IDs across every context" is chosen, since INT-002 is MANDATORY. | Settle under A7. If that alternative is chosen, add a stated exception to INT-002. | Checked under A7, no conflict. INT-002 already defers to ERD-007 for boundaries approved for separation, so no edit was needed. |
| OR-32 | AUD-025, RET-037, RET-021, RET-022 | overlap | Complementary, and cross-referenced. Gap: AUD-025's default ends in removal but does not mention retention duties or legal hold. | After A15, add a link to RET-021 and RET-022 so that the purge checks both. | Reconciled under A15. AUD-025 now requires the purge to check RET-021 and RET-022. |
| OR-33 | ARC-004, DQA-003 (RI-11) | overlap | Both say do not trust unenforced keys. ARC-004 adds a platform record. | Keep both. Make DQA-003 refer to ARC-004. | Left unchanged, no conflict. |
| OR-34 | ARC-003, DQA-002, INT-002 (RI-2) | overlap | Three MANDATORY rules on enforcing integrity in OLTP. | Keep ARC-003 as principle and INT-002 for foreign keys. DQA-002 becomes a pointer. | Left unchanged, no conflict. Pointer not applied. |
| OR-35 | INT-015, DQA-005, DQA-006 (RI-12) | overlap | Warehouse foreign keys, tests and optimizer trust. | Keep DQA-005 and DQA-006. Make INT-015 a pointer. | Left unchanged, no conflict. Pointer not applied. |
| OR-36 | NRM-007, RPT-001 | overlap | Star against snowflake, and star against wide. Different questions, same default. | Keep both. Cross-reference them. | Left unchanged. Consistent under B24. |
| OR-37 | INT-004, TYP-020 | overlap | Matching key types. TYP-020 also covers collation and warehouses. | Keep TYP-020. | Left unchanged, no conflict. |
| OR-38 | AUD-023, TYP-012 | overlap | UTC for instants and for period columns. | Keep TYP-012 as the general rule. | Left unchanged, no conflict. |
| OR-39 | INT-013, TYP-036 (RI-10) | overlap | No sentinel values, general and dimensional. | Keep both. Cross-reference them. | Left unchanged, no conflict. |
| OR-40 | SEC-009, SEC-010, GOV-004 (SC-4) | overlap | Classification. GOV-004 already defers to the stronger rule. | Keep all three. | Left unchanged, no conflict. |
| OR-41 | TYP-001, PIP-018 (DT-1) | overlap | Exact money types. PIP-018 is the pipeline form. | Keep both. | Left unchanged, no conflict. |
| OR-42 | PIP-017, TYP-027 | overlap | Declared schemas; TYP-027 is the decimal subset. | Keep PIP-017. TYP-027 becomes a pointer. | Left unchanged, no conflict. Pointer not applied. |
| OR-43 | NAM-007, TYP-026, PIP-019 (PL-10) | overlap | Raw layer permissions: names, types and payload. | Keep all three. Cross-reference them. | Left unchanged, no conflict. |
| OR-44 | MIG-018, MIG-019, GOV-006, DQA-023 (MG-14) | overlap | Breaking changes for contracts and streams. | Keep GOV-006 for classification. Keep MIG rules for release method. | Left unchanged, no conflict. |
| OR-45 | ERD-008, TYP-006, TYP-022 | overlap | Code lists as reference data. | Keep ERD-008 as the principle. Keep TYP-006 for ISO 4217. | Left unchanged, no conflict. |
| OR-46 | NAM-016, GOV-005 | overlap | ISO/IEC 11179 naming. Levels differ (OPTIONAL against RECOMMENDED), scopes differ. | Keep both with a cross-reference. | Left unchanged, no conflict. |
| OR-47 | TEN-012, AUD-012 | overlap | History and copies carry the base table's protection. | Keep both. AUD-012 is general and TEN-012 is the tenant case. | Left unchanged, no conflict. |
| OR-48 | MOD-008, IDX-010, MOD-009, IDX-011 | overlap | Analytical physical design. MOD-009 is RECOMMENDED and IDX-011 is OPTIONAL for similar lakehouse clustering. | Owner to pick one level. Keep the IDX rules. | Left unchanged. The level question is still open; it is not one of the approved decisions. |
| OR-49 | NAM-009, SCL-017 | overlap | Identifier limits. | Keep NAM-009 for names. SCL-017 is the general limit. | Left unchanged, no conflict. |
| OR-50 | IDX-014, SCL-006 | overlap | Partition or distribution column in keys. | Keep both. Scopes differ. | Left unchanged, no conflict. |
| OR-51 | RPT-014, SCL-010, ARC-002, SCL-009, TXN-020 | overlap | Reports on replicas and reads that drive decisions. RPT-014 is SHOULD, SCL-010 is MAY. | Keep RPT-014. Make SCL-010 a pointer, and keep the decision-read rules. | Left unchanged, no conflict. Pointer not applied. |
| OR-52 | BDR-013, RET-026, RET-038, BDR-015, SEC-018, AUD-010, RET-039 | overlap | Immutable stores against erasure, and key separation. | Answer B7 and B8 together. AUD-010 and RET-039 should cite each other. | Reconciled under B7, B8 and A16. BDR-013 refers to RET-026, and AUD-010 and RET-039 cite each other. RET-026 stays provisional. |

## Items other groups assumed covered

| Item | Assumed by | Found | Result |
|---|---|---|---|
| Restore testing (BK-5) | Group 06 | BDR-007, BDR-008, BDR-009 | Exists. Frequency is deliberately unset. |
| Schema drift detection (TS-6) | Group 06 | TST-006 | Exists. Scope now includes data_warehouse, matching applies_when. |
| Table-format migration (MG-13) | Group 06 | MIG-017 | Exists, for multi-format tables. Single-format tables are handled only by an exception. |
| Stream version migration (MG-14) | Group 06 | MIG-018, GOV-006, DQA-023 to DQA-025 | Exists. |
| Transactional outbox | Group 06 | TXN-011, TXN-012 | Exists. Remaining limit: no rule monitors the relay, because no research source supports one. MON-003 covers CDC only. |
| Access control | Group 06 | SEC-001, SEC-003, SEC-024, SEC-030, PIP-020 | Exists. |
| GDPR classification and minimization (SC-4, SC-5) | Group 06 | SEC-009, SEC-010, SEC-011, GOV-004 | Exists. |
| Analytical test tooling beyond key tests | Group 06 | TST-008 | Exists. |
| Retention and erasure by record class | Group 04 | RET-001 to RET-040, AUD-027 | Exists. AH-14 is AUD-027, and HIPAA log retention is RET-040 (holes 1 and 3). |
| Legal hold | Group 04 | RET-022 | Exists. |
| Key destruction and soft deletion as erasure | Group 04 | RET-030, RET-037 | Exists. SC-14 is not cited by RET-030, but the substance is there through LG-26. |
| Stored card authentication data | Group 04 | RET-020 | Exists. |
| Ledger immutability | Group 04 | FIN-031, FIN-034 | Exists. |
| Other-jurisdiction numbering (LG-2 to LG-9) | Group 03 | NUM-002 to NUM-012 | Exists. |
| Rate inverses and amount triples | Group 02 | FIN-016, FIN-017 | Exists. |
| Money, tenant and audit column rules behind validators | Group 05 | TYP-001, TEN-006, AUD-001 | Exists. AUD-001 is the only source of required audit columns. |

## Coverage holes against the 20 framework areas

| # | Area | Rules | Result |
|---:|---|---|---|
| 1 | Architecture principles | ARC 10 | Covered |
| 2 | Logical and physical modeling | MOD 10 | Covered |
| 3 | ER design | ERD 9 | Covered |
| 4 | Normalization | NRM 10 | Covered |
| 5 | Relational integrity | INT 17 | Covered |
| 6 | Naming | NAM 28 | Covered |
| 7 | Data types and precision | TYP 39 | Hole 2 filled (TYP-039, provisional) |
| 8 | Indexing and performance | IDX 24 | Covered |
| 9 | Transactions | TXN 24 | Covered |
| 10 | Multi-company and multi-tenant isolation | TEN 28, FIN-042 to FIN-051 | Covered |
| 11 | Security and permissions | SEC 30 | Covered |
| 12 | Audit and history | AUD 27 | Holes 1 and 3 filled (AUD-027, RET-040) |
| 13 | Migrations | MIG 20 | Covered |
| 14 | Pipelines and ETL/ELT | PIP 32 | Covered |
| 15 | Data quality | DQA 25, MON 7 | Covered |
| 16 | Reporting and analytical models | RPT 19 | Hole 4 filled (RPT-019, provisional) |
| 17 | Scalability | SCL 19 | Covered |
| 18 | Testing and schema validation | TST 17 | Covered. TST-006 scope fixed. |
| 19 | Backup and DR | BDR 21 | Hole 5 filled (BDR-021, provisional) |
| 20 | Documentation and governance | GOV 18 | Covered. Evidence is rated thin in the research. |

FIN, RET and NUM (111 rules, less the ten counted under area 10) cover matrix sections 21 and 22, which sit outside the 20 areas.

**Holes**

| # | Hole | Area | Detail | Suggested next step | Outcome |
|---:|---|---|---|---|---|
| 1 | Retention mechanism (AH-14) | 12 | Matrix row is RECOMMENDED: date partitions, archive tables or object lifecycle. Group 04 assumed group 07 covered it. No rule does. | Add a rule from the existing row. No new source needed. | Filled. AUD-027, RECOMMENDED, active. |
| 2 | Reference code standards (DT-15) | 7 | Matrix row is RECOMMENDED. Only ISO 4217 was covered (TYP-005, TYP-006). Research marks the ISO 3166 and 639 pages unverified. | Filled provisionally at the owner's direction; sources still to be checked. | Filled provisionally. TYP-039, RECOMMENDED; the ISO sources are unverified. |
| 3 | HIPAA audit log retention | 12 | AUD-015 says group 07 owns this. No RET rule mentions HIPAA. RET-033 covers it only generically. | Counsel question. Add to the legal review list. | Filled as a process rule. RET-040, provisional, requires legal review, no value set. |
| 4 | Late-arriving dimensions | 16 | No rule, because no source prescribes one. Listed as decision B29. | Owner answers B29. | Filled under B29. RPT-019, RECOMMENDED, provisional, inference. |
| 5 | Re-establishing CDC after failover | 19 | BDR-020 is inference only, and group 05 records that no source covers it. | Leave provisional. Note it as a research gap. | Filled as inference. BDR-021, RECOMMENDED, provisional. The research gap remains. |

**Deliberate omissions, not holes:** schema per tenant (MT-9, no source assesses it), ISO 20022 (DG-17, unverified), Data Fabric (no primary source), and DG-6 (a pointer to DV-10, covered by DQA-020).
