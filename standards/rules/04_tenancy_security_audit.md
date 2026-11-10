# Stage 2 Standards: Tenancy, Security and Audit

Group 04. Areas: multi-company and multi-tenant isolation (TEN), security and permissions (SEC), audit trails and historical records (AUD). Built only from existing research in `../../research/`; no new sources. Contains no schemas, DDL or code. Machine-readable copy: `../registry/04_tenancy_security_audit.json`.

Nothing here is legal advice. Provisional legal rules carry "requires legal review". Retention, erasure, legal hold and ledger immutability belong to other groups and are referenced only.

## Summary

| Prefix | Rules | MANDATORY | RECOMMENDED | OPTIONAL | active | provisional | superseded |
|---|---|---|---|---|---|---|---|
| TEN | 28 | 7 | 15 | 6 | 19 | 2 | 7 |
| SEC | 30 | 13 | 13 | 4 | 19 | 11 | 0 |
| AUD | 27 | 7 | 17 | 3 | 18 | 6 | 3 |
| ALL | 85 | 27 | 45 | 13 | 56 | 19 | 10 |

## Classification notes and recorded changes

These record where the rules depart from, or interpret, the classifications in `research/design_decision_matrix.md`.

- OWASP as evidence: the matrix labels OWASP-based rows Standard and rests SC-2 on OWASP alone. Evidence strength here follows that convention, although `database_security_standards.md` classes OWASP as community guidance.
- SC-1, SC-9, SC-16: `database_security_standards.md` labels these differently (AC-2 is conditional, MS-1 is RECOMMENDED, CIS adoption is RECOMMENDED). The matrix classification is used (MANDATORY, MANDATORY, OPTIONAL).
- Conditional rows split into a baseline and a scoped rule: SC-4 (SEC-009, SEC-010), SC-10 (SEC-018, SEC-019), SC-12 (SEC-020 to SEC-022), AH-10 (AUD-020, AUD-021).
- SC-7 (SEC-015): the matrix option reads column-level means. The rule follows the PCI 3.5.1 text as read, which lists four approaches and rejects disk or partition encryption alone. Class is unchanged.
- MT-2 (TEN-004): the matrix classes the choice of model OPTIONAL. Binding one model for ASTRA is an organizational choice, so it is MANDATORY within this framework; the owner accepted the default on 2026-11-08 (A1).
- MT-5 and AH-11 (TEN-009, AUD-024): the matrix carries these as open questions, not defaults. RULE_FORMAT requires a proposed default for conflicts, so each proposal was marked needs_decision until the owner accepted it (A2, B18).
- AH-11 (AUD-024): the matrix classes the merge option OPTIONAL. Defining a rule at all follows HT-9 (RECOMMENDED); which rule is the open decision.
- MT-9 (schema per tenant): unclassified in the matrix and no rule is written; it appears only as a non-proposed alternative in D1.
- AH-1 and AH-12 evidence: CASE-50 (iDempiere) is omitted and Frappe is not cited, per `research_gaps.md` section 6.7.
- Security-document items at MANDATORY that lack matrix rows use that document's label only where engine-enforced or standard-based. AU-9's MANDATORY label for card data is not carried, since it rests on the notes' reading of PCI scope; see AUD-010.
- MT-11 and MT-12: applied as RECOMMENDED per the matrix; note 14's MANDATORY labels are not adopted.

## Multi-company and multi-tenant isolation (TEN)

### TEN-001: Tenant isolation required

| Field | Value |
|---|---|
| Statement | A multi-tenant system MUST isolate each tenant's data by a named, documented mechanism. |
| Level | MANDATORY |
| Scope | OLTP |
| Applies when | Multi-tenant SaaS operational systems |
| Rationale | A breach of the tenant boundary is treated by AWS as a potentially unrecoverable event for a SaaS business. The mechanism is a choice; isolation is not. |
| Exceptions | none |
| Engine notes | Mechanism differs per engine; see TEN-009 and TEN-010. AWS and Azure frame this requirement; the notes hold no equivalent Google page. |
| Evidence | SEC-35; CLOUD-03; CLOUD-18; design_decision_matrix.md MT-1 |
| Evidence strength | multi_vendor |
| Status | active |
| Decision ref | null |
| Check method | manual_review |
| Check description | Design record names the isolation mechanism for every tenant data store. |
| Lifecycle stage | Governance |

### TEN-002: No unintended cross-tenant results

| Field | Value |
|---|---|
| Statement | A query path MUST NOT return data from more than one tenant unless it is explicitly designed and approved to do so. |
| Level | MANDATORY |
| Scope | OLTP |
| Applies when | Multi-tenant SaaS operational systems |
| Rationale | Application filtering makes every query a potential leak, since one missing predicate exposes another tenant's data. |
| Exceptions | Cross-tenant platform administration or reporting paths, approved by the data owner and listed in the design record. |
| Engine notes | none |
| Evidence | CLOUD-19; SEC-35; database_security_standards.md TN-2 |
| Evidence strength | multi_vendor |
| Status | active |
| Decision ref | null |
| Check method | pipeline_test |
| Check description | Tests run the same request under two tenants and confirm no row from the other tenant is returned on each access path. |
| Lifecycle stage | Data Validation |

### TEN-003: Tenancy model chosen deliberately

| Field | Value |
|---|---|
| Statement | Each multi-tenant system SHOULD record its tenancy model and the reasons for it before first production release. |
| Level | RECOMMENDED |
| Scope | OLTP |
| Applies when | Multi-tenant SaaS operational systems |
| Rationale | Changing the tenancy model later can be costly. |
| Exceptions | Prototype systems holding no customer data; approved by the system owner. |
| Engine notes | none |
| Evidence | CLOUD-19; database_security_standards.md TN-9; architecture_comparison.md X5 |
| Evidence strength | single_vendor |
| Status | active |
| Decision ref | A1 |
| Check method | manual_review |
| Check description | A design record states the model, the tenant-count and compliance assumptions and the alternatives rejected. |
| Lifecycle stage | Governance |

### TEN-004: ASTRA tenancy model

| Field | Value |
|---|---|
| Statement | ASTRA MUST operate as a shared pool with a tenant identifier on every tenant table, using dedicated databases only for tenants that meet a written silo trigger. |
| Level | MANDATORY |
| Scope | OLTP |
| Applies when | ASTRA only, in its multi-tenant deployments. Other systems follow TEN-003. Deployments serving Saudi Arabia are outside this active decision: that part stays provisional until counsel confirms whether in-Kingdom retention (RET-018) forces a silo. |
| Rationale | Without one approved model, key shape, restore, migration and security design diverge, and later change can be costly. The research has no ASTRA tenant counts or regulatory profile, so the default is a judgment and not a finding. |
| Exceptions | Saudi deployments: the tenancy model requires legal review by counsel before adoption; see RET-018. Any other deviation needs a recorded reason approved by the framework exception approver. |
| Engine notes | Model choice is engine-neutral. Tenant-held keys are hard in a pool and harder when sharded (CLOUD-18). |
| Evidence | CLOUD-03; CLOUD-18; CLOUD-19; design_decision_matrix.md MT-2; architecture_comparison.md B4; database_security_standards.md 9.2 |
| Evidence strength | multi_vendor |
| Status | active |
| Decision ref | A1 |
| Check method | manual_review |
| Check description | ASTRA design records show the shared pool with tenant identifiers, each dedicated database names its trigger under TEN-005, and any Saudi deployment carries counsel's recorded position. |
| Lifecycle stage | Governance |

### TEN-005: Silo triggers

| Field | Value |
|---|---|
| Statement | A tenant MAY be placed on dedicated resources when it needs its own keys, backup policy, data residency or regulatory separation. |
| Level | OPTIONAL |
| Scope | OLTP |
| Applies when | Multi-tenant systems where a tenant has one of the named needs. Whether a residency or sector rule applies is a legal question. |
| Rationale | Pool placement makes per-tenant keys and restores difficult. Silo placement raises cost per tenant. |
| Exceptions | none |
| Engine notes | none |
| Evidence | CLOUD-18; CLOUD-03; CLOUD-19; design_decision_matrix.md MT-2; database_security_standards.md TN-8 |
| Evidence strength | multi_vendor |
| Status | active |
| Decision ref | A1 |
| Check method | manual_review |
| Check description | Each dedicated placement records which trigger applied. |
| Lifecycle stage | Governance |

### TEN-006: Tenant identifier on pooled data

| Field | Value |
|---|---|
| Statement | Every tenant-scoped table in a pooled or sharded database MUST carry a non-null tenant identifier. |
| Level | MANDATORY |
| Scope | OLTP |
| Applies when | Pooled or sharded multi-tenant data |
| Rationale | Without the identifier, no predicate, policy or shard route can scope rows to a tenant. |
| Exceptions | none |
| Engine notes | Salesforce applies the equivalent as OrgID on shared generic tables (TEN-07). |
| Evidence | CLOUD-18; CLOUD-19; PERF-44; TEN-07; design_decision_matrix.md MT-3; database_security_standards.md TN-1 |
| Evidence strength | multi_vendor |
| Status | active |
| Decision ref | A1 |
| Check method | schema_lint |
| Check description | Every table marked tenant-scoped has a required tenant identifier. |
| Lifecycle stage | Schema Design |

### TEN-007: Tenant identifier in dedicated databases

| Field | Value |
|---|---|
| Statement | A hybrid or bridge deployment SHOULD keep the tenant identifier on tenant-scoped tables in dedicated databases as well. |
| Level | RECOMMENDED |
| Scope | OLTP |
| Applies when | Hybrid or bridge deployments where tenants can move between pooled and dedicated placement |
| Rationale | Tenants cannot be moved between placements without rewriting data if dedicated databases omit the identifier. |
| Exceptions | Deployments that never move tenants between placements; approved by the system owner. |
| Engine notes | none |
| Evidence | CLOUD-19; architecture_comparison.md B4; database_security_standards.md 9.2 |
| Evidence strength | single_vendor |
| Status | active |
| Decision ref | A1 |
| Check method | schema_lint |
| Check description | Tenant-scoped tables in dedicated databases carry the same identifier as pooled tables. |
| Lifecycle stage | Schema Design |

### TEN-008: Tenant context reaches the data layer

| Field | Value |
|---|---|
| Statement | Every request SHOULD carry verified tenant context to the data layer and be rejected if the context is absent. |
| Level | RECOMMENDED |
| Scope | OLTP |
| Applies when | Multi-tenant systems |
| Rationale | A request with no tenant context either fails unpredictably or runs unscoped. |
| Exceptions | Approved platform-level paths under TEN-002. |
| Engine notes | SQL Server documents read-only SESSION_CONTEXT set after connecting (MSOM-05). The common PostgreSQL session-setting approach is not in the official page read. |
| Evidence | CASE-42; CLOUD-18; PGMY-07; design_decision_matrix.md MT-4; database_security_standards.md TN-3 |
| Evidence strength | case_study |
| Status | active |
| Decision ref | null |
| Check method | pipeline_test |
| Check description | Requests without tenant context are rejected on each access path. |
| Lifecycle stage | Data Validation |

### TEN-009: Isolation enforcement point

| Field | Value |
|---|---|
| Statement | A pooled system MAY enforce tenant isolation through engine row-level security, application predicates or separate credentials; the accepted default is application predicates plus engine row-level security wherever the engine offers it and tenant identity can reach every query. |
| Level | OPTIONAL |
| Scope | OLTP |
| Applies when | Pooled multi-tenant systems |
| Rationale | Sources disagree: PostgreSQL and Azure SQL present row-level security as the mechanism, while the Azure Architecture Center says many solutions avoid it. No independent performance measurement exists, so the default is a judgment. |
| Exceptions | Deviation from the accepted default needs a recorded reason approved by the framework exception approver. |
| Engine notes | Row-level security availability differs per engine. MySQL: no row-level feature was found in pages read; [WF] re-check before use, and treat this as absence of evidence only. BENCH-07 is one small practitioner test and is not relied on. SQL Server advises keeping policy objects in a separate schema and avoiding conversions, recursion and excessive joins in predicates (MSOM-05). |
| Evidence | PGMY-07; MSOM-05; CLOUD-18; CLOUD-19; design_decision_matrix.md MT-5; architecture_comparison.md C-15; database_security_standards.md C5 |
| Evidence strength | multi_vendor |
| Status | active |
| Decision ref | A2 |
| Check method | manual_review |
| Check description | The design record names the enforcement point and, where it differs from the accepted default, the recorded reason. |
| Lifecycle stage | Schema Design |

### TEN-010: Row-level security bypass set named

| Field | Value |
|---|---|
| Statement | Where engine row-level security is an isolation control, the design MUST list every principal that can bypass or alter the policy and MUST ensure the application runtime role is not one of them. |
| Level | MANDATORY |
| Scope | OLTP |
| Applies when | Engine row-level security is relied on for isolation |
| Rationale | Each engine leaves privileged principals outside the policy, so an unlisted bypass silently voids the isolation guarantee. |
| Exceptions | none |
| Engine notes | PostgreSQL: superusers and BYPASSRLS roles always bypass, and owners do unless forced. SQL Server: policies apply to dbo, but dbo can alter them. Oracle VPD: SYS and default DBA roles are not bound; Oracle recommends Real Application Security for new work. |
| Evidence | PGMY-07; MSOM-05; MSOM-13; architecture_comparison.md E13; architecture_comparison.md C-14 |
| Evidence strength | multi_vendor |
| Status | active |
| Decision ref | A2 |
| Check method | catalog_query |
| Check description | Compare roles holding bypass or policy-alter rights with the listed set, and confirm the runtime role is absent. |
| Lifecycle stage | Governance |

### TEN-011: Isolation tested with the runtime role

| Field | Value |
|---|---|
| Statement | Row-level isolation SHOULD be tested using non-privileged roles, with table-owner bypass disabled where the engine allows. |
| Level | RECOMMENDED |
| Scope | OLTP |
| Applies when | Engine row-level security is used |
| Rationale | Tests run as an owner or superuser pass even when the policy is ineffective. |
| Exceptions | none |
| Engine notes | PostgreSQL: FORCE ROW LEVEL SECURITY binds owners. Enabling row security with no policy is default-deny. Equivalent controls on other engines were not researched. |
| Evidence | PGMY-07; database_security_standards.md RL-1 |
| Evidence strength | single_vendor |
| Status | active |
| Decision ref | A2 |
| Check method | pipeline_test |
| Check description | Isolation tests execute under the application runtime role and fail if another tenant's row is returned. |
| Lifecycle stage | Data Validation |

### TEN-012: Derived stores in isolation scope

| Field | Value |
|---|---|
| Statement | Where row-level security is the isolation control, each history table, change-capture feed and analytical copy of an isolated table MUST carry an equivalent tenant restriction. |
| Level | MANDATORY |
| Scope | OLTP |
| Applies when | Row-level security is the isolation control |
| Rationale | Row-level policies do not follow data into derived stores, and SQL Server documents whole-row leakage through change data capture. |
| Exceptions | none |
| Engine notes | SQL Server: Change Data Capture can leak whole rows, Change Tracking leaks primary keys, and temporal history tables need their own predicate. Other engines were not researched for this behaviour. Streaming tenancy was not researched. |
| Evidence | MSOM-05; MSOM-04; database_security_standards.md 9.4 |
| Evidence strength | single_vendor |
| Status | active |
| Decision ref | A2, H3 |
| Check method | manual_review |
| Check description | Each derived store of an isolated table is listed with its tenant restriction. |
| Lifecycle stage | Governance |

### TEN-013: Tenant-scoped uniqueness

| Field | Value |
|---|---|
| Statement | Unique constraints on tenant-scoped pooled tables SHOULD include the tenant identifier. |
| Level | RECOMMENDED |
| Scope | OLTP |
| Applies when | Pooled multi-tenant data |
| Rationale | A global unique constraint lets one tenant infer another tenant's values from conflict errors. |
| Exceptions | Values that are genuinely global across tenants; approved by the data owner. |
| Engine notes | PostgreSQL referential-integrity checks bypass row security and can create covert channels (PGMY-07). SQL Server documents error-based inference (MSOM-05). |
| Evidence | PGMY-07; PERF-44; design_decision_matrix.md MT-7; database_security_standards.md TN-5 |
| Evidence strength | inference |
| Status | provisional |
| Decision ref | null |
| Check method | schema_lint |
| Check description | Unique constraints on tenant-scoped tables include the tenant identifier or have a recorded exception. |
| Lifecycle stage | Schema Design |

### TEN-014: Tenant identifier in keys

| Field | Value |
|---|---|
| Statement | Pooled and sharded tenant-scoped tables SHOULD include the tenant identifier in the primary key, as its leading element where the table is sharded. |
| Level | RECOMMENDED |
| Scope | OLTP |
| Applies when | Pooled or sharded multi-tenant data |
| Rationale | Keys without the tenant identifier block co-location and tenant moves between shards. |
| Exceptions | Single-tenant databases. |
| Engine notes | Citus requires it in every primary and foreign key, so it is mandatory there. Microsoft asks for a leading primary key element for split and merge. Salesforce uses it as the partition key on generic tables. The sources differ by implementation (C-16). |
| Evidence | PERF-44; CLOUD-19; TEN-07; design_decision_matrix.md MT-6; database_security_standards.md TN-4 |
| Evidence strength | multi_vendor |
| Status | active |
| Decision ref | A3 |
| Check method | schema_lint |
| Check description | Primary keys of sharded tenant-scoped tables begin with the tenant identifier. |
| Lifecycle stage | Schema Design |

### TEN-015: No per-tenant tables or columns

| Field | Value |
|---|---|
| Statement | A shared database SHOULD NOT create tables or columns for individual tenants, and tenant-specific fields SHOULD use a dedicated custom-data structure. |
| Level | RECOMMENDED |
| Scope | OLTP |
| Applies when | Shared-database multi-tenant systems |
| Rationale | Azure lists both as antipatterns, because schema drift grows with tenant count. |
| Exceptions | Dedicated-database tenants under TEN-005. |
| Engine notes | none |
| Evidence | CLOUD-18; TEN-07; design_decision_matrix.md MT-8; database_security_standards.md TN-7 |
| Evidence strength | single_vendor |
| Status | active |
| Decision ref | null |
| Check method | schema_lint |
| Check description | No table or column name is specific to one tenant in a shared schema. |
| Lifecycle stage | Schema Design |

### TEN-016: Tenant catalog and lifecycle

| Field | Value |
|---|---|
| Statement | Siloed, sharded and bridge deployments SHOULD maintain a tenant placement catalog and automate tenant onboarding, offboarding and restore. |
| Level | RECOMMENDED |
| Scope | OLTP |
| Applies when | Siloed, sharded or bridge deployments |
| Rationale | Hard-coded placement and manual tenant operations do not scale and risk acting on the wrong tenant. |
| Exceptions | Fewer tenants than make automation worthwhile; approved by the system owner. |
| Engine notes | Schema version should be tracked per database in silo deployments (CLOUD-19). Offboarding retention follows the retention and erasure group's rules. |
| Evidence | CLOUD-19; CLOUD-18; CASE-42; design_decision_matrix.md MT-10; database_security_standards.md TN-6 |
| Evidence strength | single_vendor |
| Status | active |
| Decision ref | null |
| Check method | manual_review |
| Check description | A catalog maps each tenant to its placement, and onboarding and restore runbooks are automated. |
| Lifecycle stage | Governance |

### TEN-017: Analytical tenancy pattern

| Field | Value |
|---|---|
| Statement | An analytical platform MAY use multi-tenant tables, per-tenant objects or per-tenant accounts according to tenant count and isolation need. |
| Level | OPTIONAL |
| Scope | data_warehouse, lakehouse |
| Applies when | Multi-tenant analytical platforms. OLTP tenancy rules do not carry over automatically. |
| Rationale | Per-account isolation does not reach large tenant counts, and shared tables rely on policy for separation. |
| Exceptions | none |
| Engine notes | LAKE-13 (Snowflake) gives multi-tenant tables to millions, per-tenant objects to hundreds and per-tenant accounts to tens or low hundreds of tenants. Other platforms were not detailed. Streaming tenancy was not researched. |
| Evidence | LAKE-13; design_decision_matrix.md MT-16 |
| Evidence strength | single_vendor |
| Status | active |
| Decision ref | null |
| Check method | manual_review |
| Check description | The analytical design records the chosen pattern and the tenant-count assumption. |
| Lifecycle stage | Data Modeling |

### TEN-018: Tenant and company are separate

| Field | Value |
|---|---|
| Statement | Multi-company SaaS systems SHOULD identify the tenant and the company separately, as the customer boundary and the legal and posting boundary respectively. |
| Level | RECOMMENDED |
| Scope | OLTP |
| Applies when | ERP or financial system holding more than one company or legal entity and sold as multi-tenant SaaS |
| Rationale | Treating one identifier as both cannot represent a customer with several legal entities. Company filtering is an authorization rule and does not replace tenant isolation. |
| Exceptions | none |
| Engine notes | none |
| Evidence | TEN-08; TEN-09; database_security_standards.md MC-1; architecture_comparison.md B4 |
| Evidence strength | inference |
| Status | provisional |
| Decision ref | null |
| Check method | schema_lint |
| Check description | Company-scoped tables carry the company identifier as well as the tenant identifier where the tenant scope applies. |
| Lifecycle stage | Data Modeling |

### TEN-019: Company identifier on ERP tables

| Field | Value |
|---|---|
| Statement | Transactional tables and most setup tables in an ERP SHOULD carry a company identifier. |
| Level | RECOMMENDED |
| Scope | OLTP |
| Applies when | ERP or financial system holding more than one company or legal entity |
| Rationale | ERP products use the company or legal entity as the posting boundary and sometimes the security boundary, and without the identifier neither can be applied. |
| Exceptions | Master data intentionally shared across companies under TEN-022, and other tenant-shared setup tables approved by the data owner. |
| Engine notes | Dynamics 365 uses DataAreaId. SAP rests on training pages only. |
| Evidence | TEN-08; TEN-09; TEN-10; ERP-07; ERP-09; design_decision_matrix.md MT-11 |
| Evidence strength | multi_vendor |
| Status | active |
| Decision ref | A5 |
| Check method | schema_lint |
| Check description | Transactional and company-scoped setup tables carry the company identifier. |
| Lifecycle stage | Schema Design |

### TEN-020: One company per posting

| Field | Value |
|---|---|
| Statement | A financial posting SHOULD be attributed to exactly one company. |
| Level | RECOMMENDED |
| Scope | OLTP |
| Applies when | ERP or financial system holding more than one company or legal entity |
| Rationale | Postings spanning companies cannot be balanced or reported per legal entity without decomposition. |
| Exceptions | Intercompany transactions, handled under TEN-021. Decomposing them is a modeling choice, since NetSuite allows one transaction to post to two or more subsidiaries. |
| Engine notes | NetSuite generally posts a transaction to one subsidiary. Superseded by FIN-043 under OR-10. |
| Evidence | TEN-09; TEN-08; TEN-10; ERP-07; design_decision_matrix.md MT-12; database_security_standards.md MC-2 |
| Evidence strength | multi_vendor |
| Status | superseded |
| Decision ref | null |
| Superseded by | FIN-043 |
| Check method | pipeline_test |
| Check description | Each posted line resolves to exactly one company. |
| Lifecycle stage | Data Validation |

### TEN-021: Intercompany as linked balanced entries

| Field | Value |
|---|---|
| Statement | Intercompany transactions SHOULD be recorded as a linked pair of entries, each balanced per entity, with eliminations. |
| Level | RECOMMENDED |
| Scope | OLTP |
| Applies when | ERP or financial system holding more than one company or legal entity |
| Rationale | Unlinked entries cannot be reconciled or eliminated on consolidation. |
| Exceptions | none |
| Engine notes | NetSuite posts to two or more subsidiaries; ERPNext balances each company's entry independently; Dynamics 365 uses directional legal-entity pairs; Oracle balances by legal entity. Superseded by FIN-047 under OR-11. |
| Evidence | TEN-09; ERP-07; ERP-13; ERP-20; design_decision_matrix.md MT-13 |
| Evidence strength | multi_vendor |
| Status | superseded |
| Decision ref | null |
| Superseded by | FIN-047 |
| Check method | pipeline_test |
| Check description | Each intercompany document links its entries, and each entity's side balances. |
| Lifecycle stage | Data Validation |

### TEN-022: Master data scope

| Field | Value |
|---|---|
| Statement | An ERP MAY scope master data per company or share it across a tenant; the accepted default is tenant-shared master data with optional per-company restriction for each class. |
| Level | OPTIONAL |
| Scope | OLTP |
| Applies when | ERP or financial system holding more than one company or legal entity |
| Rationale | Sources differ: Dynamics shared master data cannot be overridden per organization, while Odoo can restrict it by company. Both default to shared. |
| Exceptions | Deviation from the accepted default needs a recorded reason approved by the framework exception approver. |
| Engine notes | none |
| Evidence | TEN-08; TEN-10; design_decision_matrix.md MT-14; architecture_comparison.md C-18 |
| Evidence strength | multi_vendor |
| Status | active |
| Decision ref | A5 |
| Check method | manual_review |
| Check description | Each master data class has a recorded scope. |
| Lifecycle stage | Data Modeling |

### TEN-023: Company as access dimension

| Field | Value |
|---|---|
| Statement | An ERP MAY treat company as an access-control dimension where users are restricted by entity. |
| Level | OPTIONAL |
| Scope | OLTP |
| Applies when | ERP or financial system holding more than one company or legal entity with users restricted by entity |
| Rationale | Without it, company-level restrictions depend on application convention. Cross-company roles such as group accountants need explicit modeling. |
| Exceptions | none |
| Engine notes | Dynamics 365 uses DataAreaId as a security boundary in some functional areas (TEN-08). |
| Evidence | TEN-08; database_security_standards.md MC-3 |
| Evidence strength | single_vendor |
| Status | active |
| Decision ref | null |
| Check method | manual_review |
| Check description | Role definitions state which companies each role can reach. |
| Lifecycle stage | Governance |

### TEN-024: Consolidation hierarchy

| Field | Value |
|---|---|
| Statement | An ERP with consolidated reporting SHOULD model the company hierarchy as a tree with elimination entities. |
| Level | RECOMMENDED |
| Scope | OLTP, data_warehouse |
| Applies when | ERP or financial system holding more than one company or legal entity and statutory or consolidated reporting. The rule applies to the warehouse only where consolidation is run there. |
| Rationale | Without a hierarchy, consolidation and elimination depend on off-system rework. |
| Exceptions | none |
| Engine notes | SAP rests on training pages only. Superseded by FIN-050 under OR-13. |
| Evidence | TEN-08; TEN-09; ERP-04; ERP-13; ERP-17; design_decision_matrix.md MT-15; database_security_standards.md MC-4 |
| Evidence strength | multi_vendor |
| Status | superseded |
| Decision ref | null |
| Superseded by | FIN-050 |
| Check method | manual_review |
| Check description | A hierarchy exists with a root and elimination entities used for consolidated reports. |
| Lifecycle stage | Data Modeling |

### TEN-025: Legal entity, ledger and business unit are distinct

| Field | Value |
|---|---|
| Statement | An ERP SHOULD model legal entity, ledger and business unit as distinct concepts. |
| Level | RECOMMENDED |
| Scope | OLTP |
| Applies when | ERP or financial system holding more than one company or legal entity |
| Rationale | A single company concept cannot express entities that need several ledgers or units that cross entities. |
| Exceptions | Single-entity systems with one ledger; approved by the finance owner. |
| Engine notes | Oracle separates balancing segment, ledger and business unit. Dynamics 365 configures a ledger per legal entity. No official SAP company-code definition was read. Superseded by FIN-042 under OR-14. |
| Evidence | ERP-07; ERP-09; design_decision_matrix.md MT-17 |
| Evidence strength | multi_vendor |
| Status | superseded |
| Decision ref | null |
| Superseded by | FIN-042 |
| Check method | manual_review |
| Check description | The conceptual model separates the three concepts or records why they are merged. |
| Lifecycle stage | Data Modeling |

### TEN-026: Consolidated statements under IFRS

| Field | Value |
|---|---|
| Statement | A system supporting a parent that presents consolidated statements under IFRS 10 MUST be able to produce the data for those statements. |
| Level | MANDATORY |
| Scope | OLTP |
| Applies when | Parents presenting consolidated statements under IFRS 10, at concept level only. Matrix scope is consolidation. |
| Rationale | The statements cannot be prepared without consolidated data. This rule requires legal review and accounting review of the applicable IFRS adoption. |
| Exceptions | Entities outside IFRS 10 consolidation; determined by counsel and finance. |
| Engine notes | IFRS 10 was read as a summary page only, held as a supporting page under ERP-21. No paragraph is cited. Superseded by FIN-051 under OR-15. |
| Evidence | ERP-21; ERP-22; design_decision_matrix.md MT-18 |
| Evidence strength | standard |
| Status | superseded |
| Decision ref | null |
| Superseded by | FIN-051 |
| Check method | manual_review |
| Check description | Finance confirms consolidated statements can be produced from system data. Elimination paragraphs were not read and are not asserted. |
| Lifecycle stage | Reporting |

### TEN-027: Elimination location

| Field | Value |
|---|---|
| Statement | An ERP MAY hold intercompany eliminations in an elimination entity, at report time, at a posting level or by a line-level flag. |
| Level | OPTIONAL |
| Scope | OLTP |
| Applies when | ERP or financial system holding more than one company or legal entity and consolidation. Matrix scope is consolidation. |
| Rationale | The choice trades traceability against reporting complexity. |
| Exceptions | none |
| Engine notes | Dynamics 365 uses an entity or report-time elimination; SAP uses posting level 20 (training pages only); NetSuite uses elimination journals. Superseded by FIN-048 under OR-16. |
| Evidence | ERP-04; ERP-13; ERP-17; design_decision_matrix.md MT-19 |
| Evidence strength | multi_vendor |
| Status | superseded |
| Decision ref | null |
| Superseded by | FIN-048 |
| Check method | manual_review |
| Check description | The design records where eliminations live. |
| Lifecycle stage | Data Modeling |

### TEN-028: Intercompany currency differences are expected

| Field | Value |
|---|---|
| Statement | Intercompany currency differences SHOULD be recorded to a defined account and not treated as errors. |
| Level | RECOMMENDED |
| Scope | OLTP |
| Applies when | ERP or financial system holding more than one company or legal entity and multi-currency consolidation. Matrix scope is consolidation. |
| Rationale | Treating expected differences as errors breaks reconciliation design. |
| Exceptions | none |
| Engine notes | NetSuite uses CTA-E with its revaluation link. Dynamics 365 shows originating currency in elimination journals. Superseded by FIN-049 under OR-17. |
| Evidence | ERP-13; ERP-17; design_decision_matrix.md MT-20 |
| Evidence strength | multi_vendor |
| Status | superseded |
| Decision ref | null |
| Superseded by | FIN-049 |
| Check method | pipeline_test |
| Check description | Intercompany reconciliation books currency differences to the defined account. |
| Lifecycle stage | Data Validation |

## Security and permissions (SEC)

### SEC-001: Least-privilege application role

| Field | Value |
|---|---|
| Statement | The application runtime MUST connect with a least-privilege role that does not own database objects and holds no administrative rights. |
| Level | MANDATORY |
| Scope | all |
| Applies when | always |
| Rationale | An owner or administrator connection turns any injection or defect into full database control, and it voids row-security and audit guarantees. |
| Exceptions | none |
| Engine notes | PostgreSQL owners bypass row security unless forced (PGMY-07). |
| Evidence | SEC-08; SEC-01; SEC-07; design_decision_matrix.md SC-1; architecture_comparison.md U9 |
| Evidence strength | standard |
| Status | active |
| Decision ref | null |
| Check method | catalog_query |
| Check description | Runtime role owns no objects and holds no administrative or bypass rights. |
| Lifecycle stage | Governance |

### SEC-002: Bound parameters

| Field | Value |
|---|---|
| Statement | Every database access path MUST pass values as bound parameters and MUST NOT concatenate them into SQL. |
| Level | MANDATORY |
| Scope | all |
| Applies when | always, including dynamic SQL inside stored procedures and pipeline code. The extension to pipelines is an inference in the notes. |
| Rationale | Concatenated values are the injection path, and escaping is explicitly discouraged by OWASP. |
| Exceptions | Identifiers that cannot be bound must be fixed in code or mapped through an allow-list. |
| Engine notes | Binding at a procedure call does not protect dynamic SQL built inside the procedure. |
| Evidence | SEC-02; SEC-03; SEC-06; design_decision_matrix.md SC-2; architecture_comparison.md U10 |
| Evidence strength | standard |
| Status | active |
| Decision ref | null |
| Check method | manual_review |
| Check description | Reviewers confirm no value is concatenated into SQL on any access path, including dynamic SQL. |
| Lifecycle stage | Governance |

### SEC-003: Duty-separated database roles

| Field | Value |
|---|---|
| Statement | Databases SHOULD use separate roles for runtime, migration, read-only analysis, audit writing, and security policy administration. |
| Level | RECOMMENDED |
| Scope | all |
| Applies when | always |
| Rationale | Shared roles let one credential both change data and alter the controls that record it. |
| Exceptions | Small non-production environments; approved by the system owner. |
| Engine notes | Role names are descriptive only. OWASP's DML example omits INSERT; read it as an illustration and not as a grant list. |
| Evidence | SEC-01; SEC-05; SEC-28; MSOM-05; SEC-31; design_decision_matrix.md SC-3; database_security_standards.md AC-7 |
| Evidence strength | inference |
| Status | provisional |
| Decision ref | null |
| Check method | catalog_query |
| Check description | Each duty maps to a distinct role, and no role combines runtime data access with policy or audit administration. |
| Lifecycle stage | Governance |

### SEC-004: Unique identity per person or service

| Field | Value |
|---|---|
| Statement | Each person and service SHOULD have a unique database or application identity, with accounts reviewed and removed when no longer needed. |
| Level | RECOMMENDED |
| Scope | all |
| Applies when | always. For ePHI see SEC-005. |
| Rationale | Shared identities make access and change evidence unattributable. |
| Exceptions | none |
| Engine notes | none |
| Evidence | SEC-01; SEC-30; database_security_standards.md AC-3 |
| Evidence strength | multi_vendor |
| Status | active |
| Decision ref | null |
| Check method | catalog_query |
| Check description | No shared human accounts exist, and accounts are reviewed on a schedule. |
| Lifecycle stage | Governance |

### SEC-005: HIPAA access control and unique user identification

| Field | Value |
|---|---|
| Statement | Systems holding ePHI MUST limit access to those granted rights and MUST assign unique user identification. |
| Level | MANDATORY |
| Scope | all |
| Applies when | ePHI under HIPAA in the United States, within scope of 45 CFR 164.312 |
| Rationale | Access control and unique identification are stated regulatory standards. This rule requires legal review. |
| Exceptions | Scope determination by counsel. |
| Engine notes | Shared application logins need per-user attribution in audit data (inference). |
| Evidence | SEC-18; database_security_standards.md 3.6 |
| Evidence strength | standard |
| Status | provisional |
| Decision ref | null |
| Check method | manual_review |
| Check description | Access grants and unique user identification are demonstrated for ePHI stores. |
| Lifecycle stage | Governance |

### SEC-006: HIPAA emergency access procedure

| Field | Value |
|---|---|
| Statement | Systems holding ePHI MUST have a documented emergency access procedure. |
| Level | MANDATORY |
| Scope | all |
| Applies when | ePHI under HIPAA in the United States, within scope of 45 CFR 164.312 |
| Rationale | The emergency access procedure is a required specification. This rule requires legal review. |
| Exceptions | Scope determination by counsel. |
| Engine notes | A controlled and audited break-glass path is the suggested form; that design is an inference. |
| Evidence | SEC-18; database_security_standards.md 3.6 |
| Evidence strength | standard |
| Status | provisional |
| Decision ref | null |
| Check method | manual_review |
| Check description | A documented emergency procedure exists and its use is recorded. |
| Lifecycle stage | Governance |

### SEC-007: Separate accounts per environment

| Field | Value |
|---|---|
| Statement | Each environment SHOULD use separate database accounts and separate databases. |
| Level | RECOMMENDED |
| Scope | all |
| Applies when | always |
| Rationale | Shared accounts let a non-production credential reach production data. |
| Exceptions | none |
| Engine notes | none |
| Evidence | SEC-01; database_security_standards.md AC-4 |
| Evidence strength | standard |
| Status | active |
| Decision ref | null |
| Check method | manual_review |
| Check description | No account is valid in more than one environment. |
| Lifecycle stage | Governance |

### SEC-008: Secrets outside code

| Field | Value |
|---|---|
| Statement | Credentials and keys SHOULD be held in a secrets manager, KMS or HSM and SHOULD NOT appear in code, repositories or environment variables. |
| Level | RECOMMENDED |
| Scope | all |
| Applies when | always |
| Rationale | Secrets in code spread through history and copies and cannot be rotated reliably. |
| Exceptions | none |
| Engine notes | none |
| Evidence | SEC-04; SEC-01; design_decision_matrix.md SC-11; database_security_standards.md AC-5 |
| Evidence strength | standard |
| Status | active |
| Decision ref | null |
| Check method | migration_lint |
| Check description | Repositories and deployment definitions contain no credentials. |
| Lifecycle stage | Governance |

### SEC-009: Sensitive data classification

| Field | Value |
|---|---|
| Statement | Sensitive data SHOULD be inventoried and classified at attribute level, in context, with required protections per level. |
| Level | RECOMMENDED |
| Scope | all |
| Applies when | Systems outside SEC-010 |
| Rationale | The same fields can merit different levels depending on the population, and unclassified data cannot be protected consistently. |
| Exceptions | none |
| Engine notes | No source prescribes column-level metadata fields; the attribute set in research is an inference. A claim that classification implements an ISO 27001 Annex A control is not supported. |
| Evidence | SEC-07; SEC-09; design_decision_matrix.md SC-4; database_security_standards.md DM-1; database_security_standards.md PI-1 |
| Evidence strength | standard |
| Status | active |
| Decision ref | null |
| Check method | catalog_query |
| Check description | Attributes holding sensitive data have a recorded classification and required treatment. |
| Lifecycle stage | Governance |

### SEC-010: Classification where GDPR or ASVS applies

| Field | Value |
|---|---|
| Statement | Systems where GDPR applies, or which claim OWASP ASVS conformity, MUST maintain an inventory classifying sensitive data at attribute level. |
| Level | MANDATORY |
| Scope | all |
| Applies when | Personal data within GDPR territorial and material scope, or systems claiming ASVS 5.0.0 V14 conformity at L2 or above |
| Rationale | ASVS requires identification and classification, and GDPR Art. 30 requires processing records. This rule requires legal review. |
| Exceptions | The Art. 30(5) small-enterprise exemption is narrow, and is lost where processing is not occasional; do not rely on it without counsel. |
| Engine notes | Art. 30 requires records of processing and does not itself prescribe column-level classification. |
| Evidence | SEC-07; SEC-15; LEG-03; design_decision_matrix.md SC-4 |
| Evidence strength | standard |
| Status | provisional |
| Decision ref | null |
| Check method | catalog_query |
| Check description | The inventory covers all attributes in in-scope stores. |
| Lifecycle stage | Governance |

### SEC-011: Data minimization under GDPR

| Field | Value |
|---|---|
| Statement | Systems holding personal data under GDPR MUST collect only the attributes necessary for a documented purpose. |
| Level | MANDATORY |
| Scope | all |
| Applies when | Personal data within GDPR scope |
| Rationale | Art. 5(1)(c) and Art. 25 require minimisation and data protection by design. This rule requires legal review. |
| Exceptions | Scope and necessity determined by counsel. |
| Engine notes | Each collected attribute needs a purpose (inference). Retention is covered by the retention and erasure group. |
| Evidence | SEC-15; SEC-04; design_decision_matrix.md SC-5 |
| Evidence strength | standard |
| Status | provisional |
| Decision ref | null |
| Check method | manual_review |
| Check description | Each personal data attribute has a recorded purpose. |
| Lifecycle stage | Governance |

### SEC-012: Encryption layer by threat

| Field | Value |
|---|---|
| Statement | A system MAY use volume or transparent encryption, column or application encryption, or client-side encryption according to its threat model. |
| Level | OPTIONAL |
| Scope | all |
| Applies when | Where a threat model covers the data |
| Rationale | No layer answers every threat: at-rest encryption addresses stolen media, not authorized sessions, and stronger layers remove query capability. |
| Exceptions | none |
| Engine notes | Always Encrypted imposes collation and type restrictions (SEC-23). Oracle column encryption restricts index range scans (MSOM-13). TDE backup files are encrypted with the DEK, and losing certificates loses data (SEC-24). |
| Evidence | SEC-24; SEC-23; SEC-04; SEC-08; design_decision_matrix.md SC-6 |
| Evidence strength | multi_vendor |
| Status | active |
| Decision ref | null |
| Check method | manual_review |
| Check description | The chosen layer for each protected store is recorded against its threat. |
| Lifecycle stage | Schema Design |

### SEC-013: Encryption decisions name their threat

| Field | Value |
|---|---|
| Statement | Each encryption decision SHOULD record the threats it addresses and those it does not. |
| Level | RECOMMENDED |
| Scope | all |
| Applies when | Whenever encryption is claimed as a control |
| Rationale | Compliance claims from at-rest encryption alone overstate protection. |
| Exceptions | none |
| Engine notes | none |
| Evidence | SEC-04; SEC-24; database_security_standards.md EN-1; database_security_standards.md C4 |
| Evidence strength | inference |
| Status | provisional |
| Decision ref | null |
| Check method | manual_review |
| Check description | Each encryption record lists addressed and unaddressed threats. |
| Lifecycle stage | Governance |

### SEC-014: Encrypted connections

| Field | Value |
|---|---|
| Statement | Database connections SHOULD use TLS with certificate verification. |
| Level | RECOMMENDED |
| Scope | all |
| Applies when | always |
| Rationale | At-rest encryption does not protect data in transit. |
| Exceptions | Local connections on a single host with no network path; approved by the system owner. |
| Engine notes | none |
| Evidence | SEC-01; SEC-24; database_security_standards.md EN-3 |
| Evidence strength | standard |
| Status | active |
| Decision ref | null |
| Check method | runtime_monitor |
| Check description | Connections are confirmed to use verified TLS. |
| Lifecycle stage | Governance |

### SEC-015: Stored PAN rendered unreadable

| Field | Value |
|---|---|
| Statement | Stored PAN MUST be rendered unreadable by one of the approaches listed in PCI DSS 3.5.1, and disk-level or partition-level encryption alone MUST NOT be relied on. |
| Level | MANDATORY |
| Scope | all |
| Applies when | Systems storing PAN within PCI DSS scope (a contractual industry standard) |
| Rationale | Wording is from PCI DSS v4.0 SAQ D, not re-verified against v4.0.1. Requires legal review, and scope questions go to the organization's PCI assessor. |
| Exceptions | none |
| Engine notes | The PCI text does not name TDE. Where file-level TDE falls is unresolved; ask the assessor. Listed approaches are one-way hashes of the entire PAN, truncation, index tokens, or strong cryptography with key management. Hashed and truncated forms of one PAN need correlation controls. |
| Evidence | SEC-17; design_decision_matrix.md SC-7; database_security_standards.md 3.7; database_security_standards.md C4 |
| Evidence strength | standard |
| Status | provisional |
| Decision ref | null |
| Check method | manual_review |
| Check description | Each stored PAN column maps to a listed approach, confirmed by the assessor. |
| Lifecycle stage | Governance |

### SEC-016: ePHI encryption

| Field | Value |
|---|---|
| Statement | Systems holding ePHI SHOULD encrypt it as if encryption were required. |
| Level | RECOMMENDED |
| Scope | all |
| Applies when | ePHI under HIPAA in the United States |
| Rationale | Encryption is addressable today and a 2025 NPRM proposes making it required; final-rule status is unverified. This rule requires legal review. |
| Exceptions | An addressable specification allows a documented equivalent and reasoning, confirmed by counsel. |
| Engine notes | The design-as-if-required position is an inference. |
| Evidence | SEC-18; design_decision_matrix.md SC-8 |
| Evidence strength | standard |
| Status | provisional |
| Decision ref | null |
| Check method | manual_review |
| Check description | ePHI stores are encrypted, or an equivalent and reasoning are documented. |
| Lifecycle stage | Governance |

### SEC-017: Masking is not a boundary

| Field | Value |
|---|---|
| Statement | Dynamic masking or redaction MUST NOT be relied on as the sole control for sensitive data. |
| Level | MANDATORY |
| Scope | all |
| Applies when | always |
| Rationale | SQL Server and Oracle both document inference attacks using predicates against masked values. |
| Exceptions | none |
| Engine notes | SQL Server masking cannot be combined with Always Encrypted, does not stop updates, and high-privilege users can view originals (SEC-25). Oracle redacted values can be written back by updating applications (MSOM-13). |
| Evidence | SEC-25; MSOM-13; design_decision_matrix.md SC-9; architecture_comparison.md U11 |
| Evidence strength | multi_vendor |
| Status | active |
| Decision ref | null |
| Check method | manual_review |
| Check description | Each masked column has an additional control recorded. |
| Lifecycle stage | Governance |

### SEC-018: Key handling

| Field | Value |
|---|---|
| Statement | Encryption keys SHOULD be held apart from the data, under a managed lifecycle, using authenticated encryption modes. |
| Level | RECOMMENDED |
| Scope | all |
| Applies when | Encryption is used, outside SEC-019 |
| Rationale | Keys stored with data fall with one foothold, and unmanaged keys cannot be rotated on compromise. |
| Exceptions | none |
| Engine notes | Tagging ciphertext with a key identifier allows multiple live keys (SEC-04). Separate key classes for recoverable and destruction-capable data are an inference. |
| Evidence | SEC-11; SEC-04; SEC-08; design_decision_matrix.md SC-10 |
| Evidence strength | standard |
| Status | active |
| Decision ref | null |
| Check method | manual_review |
| Check description | Key storage, rotation triggers and cipher modes are documented. |
| Lifecycle stage | Governance |

### SEC-019: Key handling for NIST-aligned systems

| Field | Value |
|---|---|
| Statement | US federal systems and systems claiming NIST alignment MUST hold keys apart from the data under a managed lifecycle. |
| Level | MANDATORY |
| Scope | all |
| Applies when | US federal systems, or systems claiming alignment with NIST SP 800-53 and SP 800-57 |
| Rationale | NIST SC-12 sets key management requirements for these systems. |
| Exceptions | none |
| Engine notes | SP 800-53 Release 5.2.0 changes were not reviewed. |
| Evidence | SEC-08; SEC-11; design_decision_matrix.md SC-10 |
| Evidence strength | standard |
| Status | active |
| Decision ref | null |
| Check method | manual_review |
| Check description | Key management records match the stated controls. |
| Lifecycle stage | Governance |

### SEC-020: Non-production data

| Field | Value |
|---|---|
| Statement | Non-production environments SHOULD use masked or synthetic data instead of copies of production. |
| Level | RECOMMENDED |
| Scope | all |
| Applies when | always. See SEC-021 and SEC-022 for stricter conditions. |
| Rationale | Production copies in test expose real data under weaker controls. |
| Exceptions | Where production data is needed, the copy must be protected at the production level; approved by the data owner. |
| Engine notes | SP 800-122 requires PII in test to be protected at the production level. |
| Evidence | SEC-08; SEC-09; design_decision_matrix.md SC-12; database_security_standards.md MS-3 |
| Evidence strength | standard |
| Status | active |
| Decision ref | null |
| Check method | manual_review |
| Check description | Non-production data sources are confirmed masked or synthetic. |
| Lifecycle stage | Governance |

### SEC-021: No live PAN in pre-production

| Field | Value |
|---|---|
| Statement | Live PANs MUST NOT be used in pre-production environments unless those environments are in the cardholder data environment and protected accordingly. |
| Level | MANDATORY |
| Scope | all |
| Applies when | Systems within PCI DSS scope (a contractual industry standard) |
| Rationale | Wording is from PCI DSS v4.0 SAQ D, not re-verified against v4.0.1. Requires legal review, and scope questions go to the organization's PCI assessor. |
| Exceptions | none |
| Engine notes | 6.5.6 numbering is v4.0 and was not re-verified for v4.0.1. |
| Evidence | SEC-17; design_decision_matrix.md SC-12; database_security_standards.md MS-2 |
| Evidence strength | standard |
| Status | provisional |
| Decision ref | null |
| Check method | manual_review |
| Check description | Pre-production stores are confirmed to hold no live PAN. |
| Lifecycle stage | Governance |

### SEC-022: PII in testing for federal systems

| Field | Value |
|---|---|
| Statement | US federal systems MUST limit personally identifiable information used for testing, training and research. |
| Level | MANDATORY |
| Scope | all |
| Applies when | US federal systems under NIST SP 800-53 PM-25 |
| Rationale | PM-25 limits this use of PII to reduce exposure. |
| Exceptions | none |
| Engine notes | none |
| Evidence | SEC-08; design_decision_matrix.md SC-12; database_security_standards.md MS-3 |
| Evidence strength | standard |
| Status | active |
| Decision ref | null |
| Check method | manual_review |
| Check description | Test datasets are reviewed for PII. |
| Lifecycle stage | Governance |

### SEC-023: Hardening baseline

| Field | Value |
|---|---|
| Statement | A system MAY adopt a version-pinned CIS Benchmark for each engine major version as its hardening baseline. |
| Level | OPTIONAL |
| Scope | all |
| Applies when | Where a hardening baseline is wanted |
| Rationale | Unpinned hardening drifts as engines change. Benchmark PDFs are gated, so no specific recommendation is asserted here. |
| Exceptions | none |
| Engine notes | Benchmarks exist per engine major version; pin the benchmark beside the engine version. |
| Evidence | SEC-14; design_decision_matrix.md SC-16 |
| Evidence strength | standard |
| Status | active |
| Decision ref | null |
| Check method | manual_review |
| Check description | The benchmark and version in use are recorded per engine. |
| Lifecycle stage | Governance |

### SEC-024: Central policy on analytical platforms

| Field | Value |
|---|---|
| Statement | Analytical platforms SHOULD apply central, machine-enforced tag or policy controls instead of per-object grants for sensitive data. |
| Level | RECOMMENDED |
| Scope | data_warehouse, lakehouse |
| Applies when | Analytical platforms holding sensitive data. Not applied to OLTP. |
| Rationale | Per-object grants fall out of step as data is copied, and classification has to follow the data. |
| Exceptions | Platforms without tag or policy controls; approved by the data owner. |
| Engine notes | Snowflake binds masking policies to tags and propagates them; Unity Catalog offers governed tags, row filters and column masks; BigQuery enforces policy tags. Policy type matching carries a risk. Other platforms' propagation was not examined. |
| Evidence | SEC-31; SEC-32; SEC-33; LAKE-04; design_decision_matrix.md SC-15; database_security_standards.md DM-3 |
| Evidence strength | multi_vendor |
| Status | active |
| Decision ref | null |
| Check method | catalog_query |
| Check description | Sensitive columns carry a tag or policy with an enforced control. |
| Lifecycle stage | Governance |

### SEC-025: PII in dedicated structures

| Field | Value |
|---|---|
| Statement | An OLTP design MAY hold PII in dedicated structures linked by a surrogate. |
| Level | OPTIONAL |
| Scope | OLTP |
| Applies when | OLTP systems with PII, where pseudonymisation or encryption scope benefits |
| Rationale | Separation narrows encryption and access scope, at a cost in joins. |
| Exceptions | none |
| Engine notes | Same-database placement may not achieve separation against all pseudonymisation domains. |
| Evidence | SEC-16; SEC-09; design_decision_matrix.md SC-13 |
| Evidence strength | inference |
| Status | provisional |
| Decision ref | null |
| Check method | manual_review |
| Check description | Where used, the design records which attributes are separated and why. |
| Lifecycle stage | Data Modeling |

### SEC-026: Pseudonym maps held apart

| Field | Value |
|---|---|
| Statement | Where pseudonymisation is relied on under GDPR, the additional identifying information MUST be held separately from the pseudonymised data under separate access. |
| Level | MANDATORY |
| Scope | all |
| Applies when | Personal data under GDPR where pseudonymisation is relied on |
| Rationale | Art. 4(5) requires separately kept additional information under safeguards. Pseudonymised data remains personal data. This rule requires legal review. |
| Exceptions | Counsel determines reliance. |
| Engine notes | EDPB 01/2025 (SEC-16) is a consultation version. Tokenization vault designs were not researched. |
| Evidence | SEC-15; SEC-16; database_security_standards.md TK-1 |
| Evidence strength | standard |
| Status | provisional |
| Decision ref | null |
| Check method | manual_review |
| Check description | The location and access of pseudonym maps are confirmed separate. |
| Lifecycle stage | Governance |

### SEC-027: Passwords hashed

| Field | Value |
|---|---|
| Statement | Stored passwords MUST be hashed with a password-hashing algorithm and MUST NOT be reversibly encrypted. |
| Level | MANDATORY |
| Scope | all |
| Applies when | Systems storing passwords |
| Rationale | Reversible storage exposes every credential if the key or data leaks. |
| Exceptions | none |
| Engine notes | none |
| Evidence | SEC-04; database_security_standards.md EN-8 |
| Evidence strength | standard |
| Status | active |
| Decision ref | null |
| Check method | manual_review |
| Check description | Password storage is confirmed to use a password-hashing algorithm. |
| Lifecycle stage | Schema Design |

### SEC-028: Masked output is not de-identified

| Field | Value |
|---|---|
| Statement | Masked output SHOULD NOT be treated as de-identified data without a de-identification assessment. |
| Level | RECOMMENDED |
| Scope | data_warehouse, lakehouse, OLTP |
| Applies when | Masked data shared or used for analysis |
| Rationale | Not all masking tools provide what de-identification requires, so re-identification risk remains. |
| Exceptions | none |
| Engine notes | none |
| Evidence | SEC-10; database_security_standards.md MS-4 |
| Evidence strength | standard |
| Status | active |
| Decision ref | null |
| Check method | manual_review |
| Check description | Datasets described as de-identified have an assessment on record. |
| Lifecycle stage | Governance |

### SEC-029: No personal data in tags

| Field | Value |
|---|---|
| Statement | Tag values and metadata SHOULD NOT contain personal data. |
| Level | RECOMMENDED |
| Scope | data_warehouse, lakehouse |
| Applies when | Analytical platforms using tags or metadata |
| Rationale | Databricks warns that tag data is stored as plain text and may be replicated. |
| Exceptions | none |
| Engine notes | Stated by Databricks; other platforms were not examined. |
| Evidence | SEC-32; database_security_standards.md MS-5 |
| Evidence strength | single_vendor |
| Status | active |
| Decision ref | null |
| Check method | catalog_query |
| Check description | Tag values are scanned for personal data. |
| Lifecycle stage | Governance |

### SEC-030: Restricted access to security-critical tables

| Field | Value |
|---|---|
| Statement | Security-critical tables MAY be exposed only through views or column and row permissions. |
| Level | OPTIONAL |
| Scope | OLTP, data_warehouse |
| Applies when | Security-critical applications |
| Rationale | Direct table access exposes columns that callers do not need. |
| Exceptions | none |
| Engine notes | MySQL column privileges exist [WF]; re-check before relying on them. Row-level capability was not found in pages read (ENG-06). |
| Evidence | SEC-01; SEC-02; database_security_standards.md AC-6 |
| Evidence strength | standard |
| Status | active |
| Decision ref | null |
| Check method | catalog_query |
| Check description | Direct table grants on security-critical tables are limited to the views or permissions recorded. |
| Lifecycle stage | Governance |

## Audit trails and historical records (AUD)

### AUD-001: Row-level audit columns

| Field | Value |
|---|---|
| Statement | Business tables SHOULD record who created and last updated each row and when. |
| Level | RECOMMENDED |
| Scope | OLTP |
| Applies when | Business tables in operational systems |
| Rationale | Without them, basic attribution of a row is lost. They are overwritten by design, so they are not a history. |
| Exceptions | Immutable or insert-only tables that have no update path. |
| Engine notes | Odoo and OFBiz standardize variants. iDempiere is confirmed for AD_Org only and Frappe standard columns were not confirmed, so neither is used as evidence (research_gaps.md 6.7). |
| Evidence | TEN-45; DES-22; CASE-44; CASE-48; design_decision_matrix.md AH-1; research_gaps.md 6.7 |
| Evidence strength | case_study |
| Status | active |
| Decision ref | null |
| Check method | schema_lint |
| Check description | Business tables have the four attribution values or a recorded exception. |
| Lifecycle stage | Schema Design |

### AUD-002: Same-transaction change capture

| Field | Value |
|---|---|
| Statement | Where history must match commits, before and after values SHOULD be captured in the same transaction as the change. |
| Level | RECOMMENDED |
| Scope | OLTP |
| Applies when | Tables where changes must be reconstructable |
| Rationale | Capture outside the transaction can disagree with what committed. |
| Exceptions | Tables where audit columns alone are enough; approved by the data owner. |
| Engine notes | ORM history misses changes made outside the application (TEN-15). Trigger capture misses SELECT, DDL and catalog events (TEN-11). System versioning is available on SQL Server and MariaDB; PostgreSQL 18 has no native system versioning per its release notes alone, so history there is emulated. Oracle Temporal Validity support in a CDB must be re-verified. |
| Evidence | TEN-11; MSOM-04; TEN-15; design_decision_matrix.md AH-2; architecture_comparison.md C-37 |
| Evidence strength | multi_vendor |
| Status | active |
| Decision ref | null |
| Check method | manual_review |
| Check description | The capture mechanism commits with the change for each in-scope table. |
| Lifecycle stage | Schema Design |

### AUD-003: Engine audit of access and DDL

| Field | Value |
|---|---|
| Statement | Operational databases SHOULD enable the engine's audit log for access, DDL and role events, alongside change capture. |
| Level | RECOMMENDED |
| Scope | OLTP |
| Applies when | Operational systems holding sensitive or financial data |
| Rationale | Change capture misses reads and DDL, and engine logs miss business context, so each catches different events. |
| Exceptions | Low-sensitivity systems; approved by the system owner. |
| Engine notes | pgAudit is best-effort and not transactional, and superusers cannot be reliably audited. SQL Server sysadmin can tamper with audit components. Oracle traditional auditing is reported desupported in 26ai and the unified trail is insert-only [WF]; re-check. MongoDB audit is limited to Enterprise and Atlas M10 or larger [WF]; re-check. |
| Evidence | SEC-27; SEC-26; SEC-28; ENG-14; ENG-16; design_decision_matrix.md AH-3; architecture_comparison.md C-37; database_security_standards.md AU-7 |
| Evidence strength | multi_vendor |
| Status | active |
| Decision ref | null |
| Check method | catalog_query |
| Check description | Audit is enabled for the event classes listed. |
| Lifecycle stage | Monitoring |

### AUD-004: Real user in the audit record

| Field | Value |
|---|---|
| Statement | Audit records SHOULD carry the real acting user and not only the shared service account. |
| Level | RECOMMENDED |
| Scope | all |
| Applies when | always. For PCI scope see AUD-014. |
| Rationale | A service-account-only trail cannot attribute an action to a person. |
| Exceptions | none |
| Engine notes | ORM revision entities can carry the application user (TEN-15). |
| Evidence | TEN-15; SEC-05; database_security_standards.md AU-8 |
| Evidence strength | single_vendor |
| Status | active |
| Decision ref | null |
| Check method | pipeline_test |
| Check description | A change made through the application is recorded with the acting user. |
| Lifecycle stage | Schema Design |

### AUD-005: Audit data protected from alteration

| Field | Value |
|---|---|
| Statement | Audit data MUST NOT be alterable or disableable by the application's runtime role. |
| Level | MANDATORY |
| Scope | OLTP |
| Applies when | Any audit trail that is relied on |
| Rationale | An application role that can alter its own trail makes the trail worthless as evidence. |
| Exceptions | none |
| Engine notes | SQL Server: sysadmin and db_owner limits apply (SEC-26). PostgreSQL: owners and superusers can tamper with trigger audit (TEN-11). |
| Evidence | SEC-08; TEN-11; SEC-26; design_decision_matrix.md AH-6; database_security_standards.md AU-6 |
| Evidence strength | standard |
| Status | active |
| Decision ref | null |
| Check method | catalog_query |
| Check description | The runtime role has no write, delete or configuration rights on audit objects. |
| Lifecycle stage | Governance |

### AUD-006: Audit administration separate from viewing

| Field | Value |
|---|---|
| Statement | Audit administration and audit viewing SHOULD be held by different roles. |
| Level | RECOMMENDED |
| Scope | all |
| Applies when | Where audit is relied on for oversight |
| Rationale | A single role able to configure and read audit data can hide its own activity. |
| Exceptions | Small teams where separation is impractical; approved by the system owner. |
| Engine notes | Oracle documents this separation (SEC-28). |
| Evidence | SEC-28; database_security_standards.md AC-8 |
| Evidence strength | single_vendor |
| Status | active |
| Decision ref | null |
| Check method | catalog_query |
| Check description | No role holds both audit administration and audit viewing rights. |
| Lifecycle stage | Governance |

### AUD-007: Audit copied out of DBA reach

| Field | Value |
|---|---|
| Statement | Engine audit output for financial or card systems SHOULD be shipped to storage that database administrators cannot alter. |
| Level | RECOMMENDED |
| Scope | all |
| Applies when | Financial systems or systems within PCI DSS scope |
| Rationale | An administrator with write access to audit storage can remove evidence. |
| Exceptions | none |
| Engine notes | SQL Server sysadmin can tamper with any audit component (SEC-26). Report from a separate instance where possible. |
| Evidence | SEC-26; SEC-05; database_security_standards.md AU-10 |
| Evidence strength | multi_vendor |
| Status | active |
| Decision ref | null |
| Check method | manual_review |
| Check description | Audit storage permissions exclude database administrators. |
| Lifecycle stage | Monitoring |

### AUD-008: No claim of tamper-proofing

| Field | Value |
|---|---|
| Statement | Audit designs MUST NOT claim that privileged tampering is impossible. |
| Level | MANDATORY |
| Scope | OLTP |
| Applies when | Any audit design statement or compliance claim |
| Rationale | No relational engine reviewed prevents privileged tampering, so such a claim is false. |
| Exceptions | none |
| Engine notes | pgAudit, trigger audit and SQL Server Audit all concede sysadmin evasion. SQL Server ledger detects tampering on verification and depends on digests held outside the database (TEN-14). |
| Evidence | SEC-27; TEN-11; SEC-26; TEN-14; architecture_comparison.md C-36; database_security_standards.md 10.2 |
| Evidence strength | multi_vendor |
| Status | active |
| Decision ref | null |
| Check method | manual_review |
| Check description | Design records state resistance or evidence and make no claim of prevention. |
| Lifecycle stage | Governance |

### AUD-009: Tamper evidence

| Field | Value |
|---|---|
| Statement | A system MAY use hash-chained digests held outside DBA control where third-party attestation is needed. |
| Level | OPTIONAL |
| Scope | OLTP |
| Applies when | Audit data needing third-party attestation |
| Rationale | Access controls alone give no way to show that records were not altered. |
| Exceptions | none |
| Engine notes | SQL Server ledger is the only mechanism researched; row-level redaction within ledger structures was not researched. Do not select Amazon QLDB, whose end of support is reported by a secondary source only (TEN-16). |
| Evidence | TEN-14; TEN-11; design_decision_matrix.md AH-7 |
| Evidence strength | single_vendor |
| Status | active |
| Decision ref | null |
| Check method | manual_review |
| Check description | Where used, digests are stored outside the database and verified on a schedule. |
| Lifecycle stage | Governance |

### AUD-010: Sensitive values in change capture

| Field | Value |
|---|---|
| Statement | Change capture SHOULD exclude or tokenize sensitive columns by default, and trails that must show prior values SHOULD be held in a classified, access-controlled store. |
| Level | RECOMMENDED |
| Scope | all |
| Applies when | Before-and-after capture or logging that touches sensitive columns. Card data rules are in AUD-014 and the retention and erasure group's rules. |
| Rationale | Sources pull in opposite directions: before-and-after capture copies sensitive values, while OWASP excludes PII and cardholder data from logs. The reconciliation is an inference. |
| Exceptions | Deviation from the accepted default needs a recorded reason approved by the framework exception approver. |
| Engine notes | The PostgreSQL audit trigger's excluded-column option is an example (TEN-11). Identifiers in immutable logs are covered by RET-039. |
| Evidence | TEN-11; SEC-05; database_security_standards.md C7; database_security_standards.md AU-9 |
| Evidence strength | standard |
| Status | active |
| Decision ref | A16 |
| Check method | manual_review |
| Check description | The capture configuration lists excluded columns and the reason for any sensitive column retained. |
| Lifecycle stage | Schema Design |

### AUD-011: Audit stores classified

| Field | Value |
|---|---|
| Statement | Audit and history stores SHOULD be classified as sensitive to the level of the values they contain. |
| Level | RECOMMENDED |
| Scope | all |
| Applies when | Before-and-after images of sensitive tables |
| Rationale | Before-and-after images copy sensitive values into stores that are often less protected. |
| Exceptions | none |
| Engine notes | none |
| Evidence | TEN-11; SEC-05; database_security_standards.md AU-12 |
| Evidence strength | inference |
| Status | provisional |
| Decision ref | null |
| Check method | catalog_query |
| Check description | Audit and history stores have a recorded classification. |
| Lifecycle stage | Governance |

### AUD-012: History protected like the base table

| Field | Value |
|---|---|
| Statement | History structures of a protected table MUST carry access control, masking and classification at least equal to the base table. |
| Level | MANDATORY |
| Scope | all |
| Applies when | A base table is protected by access control, masking or classification |
| Rationale | Row-security predicates, indexes and check constraints are not copied to SQL Server history tables, so history can bypass base-table controls. |
| Exceptions | none |
| Engine notes | SQL Server behaviour stated (MSOM-05, MSOM-04). MariaDB DELETE HISTORY is privileged and dumps need an explicit history option (TEN-20). Other engines were not researched for this behaviour. |
| Evidence | MSOM-05; MSOM-04; database_security_standards.md HT-6 |
| Evidence strength | single_vendor |
| Status | active |
| Decision ref | H3 |
| Check method | catalog_query |
| Check description | History objects are compared to base tables for protection parity. |
| Lifecycle stage | Governance |

### AUD-013: Part 11 audit trail

| Field | Value |
|---|---|
| Statement | FDA-regulated electronic records MUST have a secure, computer-generated, time-stamped audit trail in which changes do not obscure earlier information. |
| Level | MANDATORY |
| Scope | OLTP |
| Applies when | Electronic records under 21 CFR Part 11 in the United States (FDA scope only) |
| Rationale | 21 CFR 11.10(e) states this. It does not apply to financial records as such. This rule requires legal review. |
| Exceptions | Scope determined by counsel. |
| Engine notes | Retention of the trail is covered by the retention and erasure group's rules. |
| Evidence | TEN-17; design_decision_matrix.md AH-4; database_security_standards.md AU-3 |
| Evidence strength | standard |
| Status | provisional |
| Decision ref | null |
| Check method | manual_review |
| Check description | The trail is confirmed secure, computer-generated, time-stamped and non-obscuring. |
| Lifecycle stage | Governance |

### AUD-014: PCI audit logging

| Field | Value |
|---|---|
| Statement | Systems within PCI DSS scope MUST log all individual user access to cardholder data and MUST protect audit logs from modification. |
| Level | MANDATORY |
| Scope | all |
| Applies when | Systems within PCI DSS scope (a contractual industry standard) |
| Rationale | Wording is from PCI DSS v4.0 SAQ D, not re-verified against v4.0.1. Requires legal review, and scope questions go to the organization's PCI assessor. |
| Exceptions | none |
| Engine notes | Audit log retention is covered by the retention and erasure group's rules (matrix AH-5; 10.5.1 wording is v4.0 SAQ D). |
| Evidence | SEC-17; LEG-30; design_decision_matrix.md AH-5; database_security_standards.md AU-2 |
| Evidence strength | standard |
| Status | provisional |
| Decision ref | null |
| Check method | manual_review |
| Check description | Logs show individual access to cardholder data, and only authorised parties can alter them. |
| Lifecycle stage | Monitoring |

### AUD-015: HIPAA audit controls

| Field | Value |
|---|---|
| Statement | Systems holding ePHI MUST have mechanisms that record and allow examination of activity. |
| Level | MANDATORY |
| Scope | all |
| Applies when | ePHI under HIPAA in the United States |
| Rationale | 45 CFR 164.312(b) states this. This rule requires legal review. |
| Exceptions | Scope determined by counsel. |
| Engine notes | How HIPAA retention applies to activity logs is unresolved and belongs to the retention and erasure group; see RET-040. |
| Evidence | SEC-18; design_decision_matrix.md AH-5; database_security_standards.md AU-1 |
| Evidence strength | standard |
| Status | provisional |
| Decision ref | null |
| Check method | manual_review |
| Check description | Activity on ePHI is recorded and examinable. |
| Lifecycle stage | Monitoring |

### AUD-016: Non-obscuring audit for financial records

| Field | Value |
|---|---|
| Statement | Financial records SHOULD keep prior values visible when changed, by analogy with Part 11. |
| Level | RECOMMENDED |
| Scope | OLTP |
| Applies when | ERP and financial systems outside FDA scope. Analogy only; Part 11 does not bind them. |
| Rationale | Changes that obscure earlier values remove the basis for later review. Ledger immutability belongs to the ERP financial group. |
| Exceptions | none |
| Engine notes | none |
| Evidence | TEN-17; TEN-42; TEN-43; database_security_standards.md AU-4 |
| Evidence strength | inference |
| Status | provisional |
| Decision ref | null |
| Check method | manual_review |
| Check description | Financial change history shows prior values. |
| Lifecycle stage | Data Modeling |

### AUD-017: Name the two time dimensions

| Field | Value |
|---|---|
| Statement | Each history mechanism SHOULD state whether it records valid time or system time. |
| Level | RECOMMENDED |
| Scope | all |
| Applies when | always, where history is kept |
| Rationale | Vendors use temporal table to mean different things, so an unnamed dimension is misread. |
| Exceptions | none |
| Engine notes | SQL Server and MariaDB use the term for system versioning; SQL:2011 and Oracle treat valid time as primary too. |
| Evidence | GOV-06; TEN-21; TEN-23; MSOM-04; architecture_comparison.md U19; architecture_comparison.md C-32; database_security_standards.md HT-1 |
| Evidence strength | standard |
| Status | active |
| Decision ref | null |
| Check method | manual_review |
| Check description | Each history object's design record names its time dimension. |
| Lifecycle stage | Data Modeling |

### AUD-018: Choice of time dimensions

| Field | Value |
|---|---|
| Statement | A system MAY record system time for audit, valid time for business effect, or both where past-effective corrections must be reconstructable. |
| Level | OPTIONAL |
| Scope | all |
| Applies when | Where history is kept |
| Rationale | Bitemporal modeling adds query complexity and is only justified by a reconstruction need. |
| Exceptions | none |
| Engine notes | Engine support differs: see AUD-002 engine notes. |
| Evidence | GOV-06; TEN-23; LIT-58; design_decision_matrix.md AH-8; database_security_standards.md HT-7 |
| Evidence strength | standard |
| Status | active |
| Decision ref | null |
| Check method | manual_review |
| Check description | The design records which dimensions are used and why. |
| Lifecycle stage | Data Modeling |

### AUD-019: Closed-open periods

| Field | Value |
|---|---|
| Statement | Stored time periods SHOULD be closed-open intervals. |
| Level | RECOMMENDED |
| Scope | all |
| Applies when | always, where periods are stored |
| Rationale | Mixed conventions create gaps or overlaps at boundaries. |
| Exceptions | none |
| Engine notes | BETWEEN is inclusive at the upper bound in SQL Server and SQL:2011 syntax. Kimball SCD2 does not specify a convention (C-33). Superseded by TYP-015 under OR-25. |
| Evidence | GOV-06; TEN-23; MSOM-04; design_decision_matrix.md AH-9; architecture_comparison.md U20; architecture_comparison.md C-33 |
| Evidence strength | standard |
| Status | superseded |
| Decision ref | null |
| Superseded by | TYP-015 |
| Check method | manual_review |
| Check description | Period definitions and queries use closed-open semantics. |
| Lifecycle stage | Schema Design |

### AUD-020: Engine-maintained system time

| Field | Value |
|---|---|
| Statement | System-time values relied on as history SHOULD be maintained by the engine and not be user-editable. |
| Level | RECOMMENDED |
| Scope | OLTP |
| Applies when | Outside AUD-021, where history serves an audit purpose |
| Rationale | User-editable system time undermines the history as evidence. |
| Exceptions | Engines without system versioning, where emulation must prevent direct edits; approved by the data owner. |
| Engine notes | Emulated on PostgreSQL (absence of native feature rests on PG 18 release notes alone). SQL:2011 tamper language does not describe resistance to privileged operators, and vendors supply purge paths. |
| Evidence | GOV-06; MSOM-04; design_decision_matrix.md AH-10 |
| Evidence strength | standard |
| Status | active |
| Decision ref | null |
| Check method | manual_review |
| Check description | Period columns are not writable by application roles. |
| Lifecycle stage | Schema Design |

### AUD-021: System time for regulated records

| Field | Value |
|---|---|
| Statement | Where a record is legally regulated and history is an audit obligation, system time MUST be engine-maintained. |
| Level | MANDATORY |
| Scope | OLTP |
| Applies when | Records within a regime such as 21 CFR Part 11 in the United States; applicability per jurisdiction |
| Rationale | A user-editable timestamp cannot support a regulated trail. This rule requires legal review. |
| Exceptions | Emulation on engines without system versioning, if it prevents edits and is accepted by counsel. |
| Engine notes | See AUD-020 engine notes. |
| Evidence | TEN-17; GOV-06; MSOM-04; design_decision_matrix.md AH-10; database_security_standards.md HT-2 |
| Evidence strength | standard |
| Status | provisional |
| Decision ref | null |
| Check method | manual_review |
| Check description | Period columns are confirmed system-generated. |
| Lifecycle stage | Schema Design |

### AUD-022: Non-overlapping periods

| Field | Value |
|---|---|
| Statement | Valid-time periods SHOULD be constrained to not overlap per business key where the engine supports it. |
| Level | RECOMMENDED |
| Scope | OLTP |
| Applies when | Valid-time data on engines with non-overlap support |
| Rationale | Overlapping periods give two answers for one date. |
| Exceptions | Engines without support, where tests must substitute; approved by the system owner. |
| Engine notes | PostgreSQL 18 adds WITHOUT OVERLAPS and PERIOD constraints. Superseded by INT-011 under OR-26. |
| Evidence | GOV-06; PERF-16; database_security_standards.md HT-4 |
| Evidence strength | standard |
| Status | superseded |
| Decision ref | null |
| Superseded by | INT-011 |
| Check method | schema_lint |
| Check description | Valid-time tables have a non-overlap constraint or a test. |
| Lifecycle stage | Schema Design |

### AUD-023: Period timestamps in UTC

| Field | Value |
|---|---|
| Statement | Period timestamps SHOULD be stored in UTC where the engine does not fix this. |
| Level | RECOMMENDED |
| Scope | all |
| Applies when | Period timestamps on engines that do not fix the zone |
| Rationale | Local-time periods create ambiguous history across zones and daylight changes. |
| Exceptions | none |
| Engine notes | SQL Server stores system-time periods in UTC (MSOM-04). |
| Evidence | MSOM-04; database_security_standards.md HT-5 |
| Evidence strength | single_vendor |
| Status | active |
| Decision ref | null |
| Check method | schema_lint |
| Check description | Period timestamps are stored in UTC. |
| Lifecycle stage | Schema Design |

### AUD-024: Backdated-change rule

| Field | Value |
|---|---|
| Statement | A system recording valid time SHOULD use the SQL:2011 period-split behaviour as its backdated-change rule. |
| Level | RECOMMENDED |
| Scope | OLTP |
| Applies when | Systems recording valid time with backdated changes |
| Rationale | SQL:2011 splits rows while Workday lets a later-effective edit overwrite, and the two give different histories. |
| Exceptions | Deviation from the accepted default needs a recorded reason approved by the framework exception approver. |
| Engine notes | SQL:2011 FOR PORTION OF splits rows. Workday out-of-order semantics differ (TEN-25). |
| Evidence | GOV-06; TEN-25; design_decision_matrix.md AH-11; architecture_comparison.md C-34; database_security_standards.md HT-9 |
| Evidence strength | multi_vendor |
| Status | active |
| Decision ref | B18 |
| Check method | manual_review |
| Check description | The design records the rule, and tests cover a backdated correction. |
| Lifecycle stage | Data Modeling |

### AUD-025: Deletion state design

| Field | Value |
|---|---|
| Statement | Operational tables SHOULD avoid pervasive per-row deleted flags and SHOULD mark deletion at the aggregate root for a bounded grace period, followed by removal. |
| Level | RECOMMENDED |
| Scope | OLTP |
| Applies when | Operational tables needing deletion or recoverability. Whether any form satisfies erasure belongs to the retention and erasure group. |
| Rationale | Sources disagree: Leach argues per-row soft deletion is rarely worthwhile, GitLab marks aggregates, and ERP frameworks use active flags. Flags burden every query and foreign key. |
| Exceptions | Deviation from the accepted default needs a recorded reason approved by the framework exception approver. Active-flag business state, such as an inactive record kept for reference, is not a deletion flag. |
| Engine notes | Odoo active flags are the verified ERP example (CASE-44). iDempiere is verified on AD_Org only and is not used. The purge must check the retention schedule (RET-021) and legal hold (RET-022) before removal; the erasure effect is RET-037. |
| Evidence | TEN-30; TEN-31; CASE-44; design_decision_matrix.md AH-12; architecture_comparison.md C-38; research_gaps.md 6.7 |
| Evidence strength | case_study |
| Status | active |
| Decision ref | A15 |
| Check method | schema_lint |
| Check description | Tables with a deleted flag have a recorded reason and purge path, and the purge checks RET-021 and RET-022. |
| Lifecycle stage | Schema Design |

### AUD-026: Analytical history pattern

| Field | Value |
|---|---|
| Statement | A warehouse MAY use slowly changing dimension types, with Type 2 for attributes that must be reconstructable. |
| Level | OPTIONAL |
| Scope | data_warehouse |
| Applies when | Dimensional warehouse history. OLTP history rules do not carry over automatically. |
| Rationale | Type 1 destroys history, while Type 2 grows rows. |
| Exceptions | none |
| Engine notes | System-versioned OLTP tables can feed Type 2 (MSOM-04). Personal attributes in Type 2 dimensions extend erasure scope (inference; see the retention and erasure group). Superseded by RPT-008 under OR-27. |
| Evidence | DWM-01; TEN-24; MSOM-04; design_decision_matrix.md AH-16 |
| Evidence strength | single_vendor |
| Status | superseded |
| Decision ref | null |
| Superseded by | RPT-008 |
| Check method | manual_review |
| Check description | Each dimension attribute has a recorded history type. |
| Lifecycle stage | Data Modeling |

### AUD-027: Declared retention mechanism

| Field | Value |
|---|---|
| Statement | Retained data SHOULD be expired through a declared mechanism chosen from date partitions, archive tables or object lifecycle rules, with partition detach or drop preferred at scale. |
| Level | RECOMMENDED |
| Scope | OLTP, data_warehouse |
| Applies when | Records or history are expired or archived by age. |
| Rationale | Disposal with no declared mechanism is left to each job. The matrix names date partitions, archive tables and object lifecycle as the options, with partition detach or drop for scale. |
| Exceptions | Deviation with a recorded reason, approved by the system owner. |
| Engine notes | PostgreSQL partition detach or drop (PGMY-06). MariaDB history partitions and DELETE HISTORY for system-versioned tables (TEN-20). Object lifecycle rules such as Amazon S3 for exported history and archives (TEN-35). Disposal checks the retention schedule (RET-021) and legal hold (RET-022) first. |
| Evidence | PGMY-06; TEN-20; TEN-35; design_decision_matrix.md AH-14 |
| Evidence strength | multi_vendor |
| Status | active |
| Decision ref | null |
| Check method | manual_review |
| Check description | Each retained table or store records its expiry mechanism, and disposal jobs check RET-021 and RET-022. |
| Lifecycle stage | Governance |

## Referenced from other groups

- Retention and erasure, by record class and jurisdiction: matrix AH-13 to AH-15, SC-14, LG-16 to LG-30; architecture C-39 and C-81.
- Legal treatment of soft deletion and of key destruction as erasure: matrix AH-12, LG-26.
- Stored card authentication data: matrix LG-25.
- Ledger immutability and correction by new entry: ERP financial controls group, matrix section 21.

## Decisions needing owner approval

Answered by the owner on 2026-11-08: all defaults accepted. See `../DECISIONS_TO_APPROVE.md` for the decision log, and each rule's decision_ref for its decision number. Questions and alternatives are kept for the record.

### D1: Which tenancy model does ASTRA adopt?

Rule: TEN-004

**Proposed default.** Shared pool with the tenant identifier on every tenant-scoped table (TEN-006), plus dedicated databases only for tenants meeting a documented trigger (TEN-005), keeping the tenant identifier there too (TEN-007). This is effectively a bridge model. The default is a judgment: the research holds no ASTRA tenant counts, deployment regions or regulatory profile.

| Alternative | Consequence |
|---|---|
| Pool only | Lowest cost per tenant and one schema to migrate. Isolation relies on predicates, noisy-neighbour risk increases, per-tenant restore means side-copy recovery, and tenant-held keys are hard. |
| Silo or database per tenant for all tenants | Highest isolation, simple restore and natural fit for tenant keys and residency. Highest operating cost, and version tracking per database. |
| Bridge (proposed default) | Isolation only where needed. Must support both models in operations and migration. |
| Metadata-driven shared tables | Tenant customization at scale, but evidence is one vendor's architecture (TEN-07). |
| Schema per tenant | No source assesses or recommends it (matrix MT-9). Not proposed; choosing it would rest on inference only. |

**Note.** Saudi VAT records carry a within-Kingdom retention rule (database_security_standards.md 12.6); if ASTRA serves that market, residency may force a silo trigger. That point requires legal review.

### D2: Where is tenant isolation enforced?

Rule: TEN-009

**Proposed default.** Application predicates plus engine row-level security wherever the engine offers it and tenant identity can reach every query. The matrix carries MT-5 as open; this default is a proposal for the owner, and a judgment because no independent performance evidence exists.

| Alternative | Consequence |
|---|---|
| Engine row-level security with application predicates (proposed default) | Second enforcement layer against a missed predicate. Identity propagation is complex, bypass sets must be managed (TEN-010), and overhead is unmeasured. |
| Application predicates only | Simple to operate and common per Azure. Every query must be correct, so a single miss is a leak. |
| Separate credentials per tenant | Strong credential boundary. Connection and credential management grows with tenant count; the notes do not quantify this. |

### D3: Is master data shared across companies or restricted per company?

Rule: TEN-022

**Proposed default.** Tenant-shared, with optional per-company restriction per master data class.

| Alternative | Consequence |
|---|---|
| Tenant-shared with optional restriction (proposed default) | Reuse with control where needed. Requires a recorded scope per class. |
| Shared with no override (Dynamics position) | Simplest. Cannot restrict a master record to one company. |
| Always per-company | Maximum control. Duplicates data and complicates group reporting (inference). |

### D4: What is the backdated-change rule for valid-time data?

Rule: AUD-024

**Proposed default.** SQL:2011 period-split behaviour. The matrix carries AH-11 as open; this default is a proposal for the owner.

| Alternative | Consequence |
|---|---|
| SQL:2011 period split (proposed default) | Preserves prior periods and is standard-defined. Row counts grow. |
| Out-of-order overwrite (Workday position) | Later-effective edits take effect simply. Prior effective values can be overwritten, so reconstruction needs system time. |

### D5: How is deletion state represented on operational tables?

Rule: AUD-025

**Proposed default.** Aggregate-root marking with a bounded grace period, then removal. Erasure sufficiency is out of scope here.

| Alternative | Consequence |
|---|---|
| Aggregate-root marking with grace period (proposed default) | Recoverable with limited query burden. Needs a purge job and a decision on the grace period. |
| Hard delete with a deleted-record archive (Leach) | Keeps queries and foreign keys simple. The archive stays in retention and erasure scope. |
| Per-row flags (ERP framework pattern) | Familiar and recoverable. Every query and foreign key carries the burden, and flagged personal data remains present. |

### D6: How are sensitive columns treated in change capture?

Rule: AUD-010

**Proposed default.** Exclude or tokenize by default, and hold trails that must show prior values in a classified, access-controlled store.

| Alternative | Consequence |
|---|---|
| Exclude by default, classified store by exception (proposed default) | Reduces sensitive copies. Audit coverage of excluded columns is lost, and the store needs its own access controls. |
| Capture all values | Complete reconstruction. Copies sensitive values into every audit store and widens retention and erasure scope. |
| Tokenize all sensitive values | Keeps change evidence without plain values. Requires token map management, and prior values cannot be read without it. |
