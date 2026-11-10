# Stage 2 Standards: ERP Finance, Retention and Legal Numbering (FIN, RET, NUM)

Status: owner defaults accepted 2026-11-08; legal rules stay provisional until counsel reviews them. Built only from existing research in `../../research/`. No web research was performed and no sources were added. Contains no schemas, DDL or code. Not legal advice.

## Reading notes

- The JSON registry is `../registry/07_erp_finance_compliance.json`. Field meanings are in `../RULE_FORMAT.md`.
- Scope labels: OLTP covers general ledger, subledger and invoicing systems. Consolidation is shown as OLTP and OLAP. Retention scope covers warehouse and lake copies because the duty attaches to the records and not to one store.
- Every statute-based rule binds only in the jurisdiction in `applies_when`, is `provisional`, and requires legal review (open item 30 in `research_gaps.md`). Provisional MANDATORY means mandatory in that jurisdiction if counsel confirms it.
- Evidence entries are catalog IDs from `research/resource_catalog.json` or research file sections. Quoted page wording is treated as paraphrase, as `research_gaps.md` section 6.1 requires, so no source is quoted here.
- Most ERP vendor pages were read through a summarising fetch tool, per the note under matrix section 21. Rules resting on matrix text marked [WF] carry a re-check note in engine_notes.
- Where no independent benchmark exists, the accepted default is a judgment.

## Rule counts

Total rules: 111.

| Level | active | provisional | superseded | Total |
|---|---:|---:|---:|---:|
| MANDATORY | 1 | 43 | 0 | 44 |
| RECOMMENDED | 26 | 21 | 2 | 49 |
| OPTIONAL | 12 | 4 | 2 | 18 |
| Total | 39 | 68 | 4 | 111 |

## Jurisdiction table

Research input only, requiring review by counsel for the entity concerned. Periods are in years unless stated. Details and start events are in the rules.

| Jurisdiction | Invoice numbering | Gap position | Retention | Erasure | Rules | Evidence quality |
|---|---|---|---|---|---|---|
| European Union | Sequential, series, unique (VAT Directive Art. 226(2)); corrective reference from 1 July 2030 where transposed | Silent | Set by Member States (Art. 247); integrity through storage (Art. 233) | Erasure without undue delay; recorded exceptions; register and timing recommended; undue delay for backups unsettled | NUM-001, NUM-014, RET-019, RET-025 to RET-029, RET-034 to RET-038 | Direct text; national transposition not researched |
| Germany | Consecutive, one or more series, issued once (UStG 14(4)) | Unverified (BMF snippet only, LEG-06 not cited) | Tax: books 10, vouchers 8, other 6; VAT invoices 8; commercial 10/8/6 | EU regime | NUM-002, RET-001 to RET-004, FIN-031, FIN-039 | Direct text; 8-year transition not read |
| France | Unique, chronological and continuous per series | No tolerance found | Tax 6; commercial 10 (unverified, RET-006) | EU regime | NUM-003, RET-005, RET-006 | Direct text; Art. 242 nonies A not opened; BOFiP version may be replaced |
| Italy | Progressive, uniquely identifying; date may contribute | Not addressed | Not researched in depth | EU regime | NUM-004 | Direct text |
| Spain | Sequential per series; separate corrective series; chained records for in-scope software | Not addressed for invoice numbers | Not researched in depth | EU regime | NUM-005, NUM-006 | [WF] Fetch-tool paraphrase; re-check |
| United Kingdom | Sequential, unique, one or more series | Tolerated with kept spoiled invoice or explanation (guidance) | VAT at least 6; Companies Act private 3, public 6 | ICO beyond-use for backups (Wayback only) | NUM-007, RET-007, RET-008, RET-025 to RET-027 | Direct HMRC text; VATREC is a manual |
| United States | None researched | None researched | IRS limitation-driven; broker-dealers only under 17a-4 | California only | FIN-012, FIN-032, FIN-033, RET-009, RET-010, RET-032, RET-034 | Mixed; IRS page is guidance; no statute read for general retention |
| PCI DSS scope (contractual, not a jurisdiction) | Not applicable | Not applicable | Audit logs 12 months, three immediately available; card authentication data not kept after authorization | Not applicable | RET-020, RET-031 | v4.0 SAQ D; v4.0.1 text not read |
| California | None researched | None researched | None researched | Delete and notify chain; backup delay until restore or next use | RET-023, RET-024 | CPPA copies |
| Pakistan | Serially numbered tax invoice (STA s23(1)); FBR invoice number and QR for integrated persons | Not found | Sales and income tax 6 years or until proceedings end; e-invoices 6 years on electronic media; company books not less than ten financial years; income tax proviso removes the limit for s111(2)(ii) matters | Not researched | NUM-008, NUM-009, NUM-020, RET-011 to RET-014 | Direct text; check gazette; start dates for FBR integration conflict and are unresolved |
| United Arab Emirates | Sequential, or unique and showing order; UUID in e-invoicing | Not found | 5 years; real estate 7; extensions for disputes, audits and disclosure | Not researched | NUM-010, NUM-011, NUM-020, RET-015, RET-016 | Direct text; amendment citation conflict (Decision 100 of 2024 vs 2025) |
| Saudi Arabia | Sequential unique number; counter never reused; previous-invoice hash | Counter not reused; rejected documents consume a value | At least 6; capital assets adjustment plus 5; real estate 15; in-Kingdom, Arabic | Not researched | NUM-012, NUM-013, NUM-020, RET-017, RET-018 | Direct text; technical guideline dated November 2022, later versions may exist |

## Vendor and source disagreements

| Topic | Positions | Handled by |
|---|---|---|
| Period status grain | SAP, Oracle, D365, NetSuite, ERPNext each use a different grain | FIN-002 |
| Permanent close | Oracle and Odoo offer it; D365 offers it and advises against it | FIN-009 |
| Rate effective-dating | Oracle exact-day key; ERPNext latest eligible record; SAP not established | FIN-015 |
| Inverse rates | ERPNext needs a separate record; Oracle stores a generally reciprocal row ([WF]); SAP direct and indirect quotation | FIN-016 |
| Revaluation reversal | D365 GL does not reverse; D365 AR and AP do and can only be rerun | FIN-020 |
| Unrealized differences presentation | D365 ledger page against D365 revaluation example; unresolved, noted only | FIN-019 |
| Reversal method and balance effect | SAP normal against negative posting; Oracle Change Sign and Switch Debit or Credit | FIN-035 |
| Reversing a reversal | Oracle forbids; D365 allows | FIN-036 |
| Deletion against non-alteration | D365 and NetSuite delete; HGB 239(3) forbids loss of original content; application to generated balances unknown | FIN-039 |
| Stored balance | Fowler and Modern Treasury derive; Square materializes | FIN-028 |
| Elimination location | D365 entity or report-time; SAP posting level 20; NetSuite elimination journals | FIN-048 |
| Master data scope | Dynamics cannot override; Odoo can restrict | FIN-046 |
| Numbering gaps | France continuity wording; UK tolerance; KSA counter; others silent or unverified | NUM-018 |
| Plain sequences for legal numbers | Industry-practice file MANDATORY where gaps are not acceptable; matrix and note 19 RECOMMENDED | NUM-016 |
| Backup erasure timing | ICO beyond use; California delay; Dutch AP records and erasure on restore | RET-026 |
| Immutable logs against erasure | PCI, 21 CFR 11.10(e) and vendor immutability against GDPR Art. 17; non-EU retention law not clearly within Art. 17(3)(b) | RET-036, RET-039 |
| Legal hold label | Matrix LG-23 RECOMMENDED; security file RT-4 OPTIONAL/CONTEXTUAL and strongly advisable for FIN; matrix followed | RET-022 |
| French retention | Tax 6 years against commercial 10 years (unverified) | RET-005, RET-006 |

## Classification changes from the research

Rows below record the position before the owner decisions of 2026-11-08. Each rule's level, status and decision_ref fields show the current position.

| Rule | Research classification | This file | Reason |
|---|---|---|---|
| FIN-025 | Practices table in `industry_best_practices.md` section 5: MANDATORY (ledgers); no row in the matrix classifies zero-sum balance separately | MANDATORY, active | Kept. Supported by independent vendor documentation (Modern Treasury, Oracle, ERPNext) and foundational accounting texts. Basis of the test is listed in engine_notes. |
| FIN-027 | Practices table: MANDATORY (ledgers) | RECOMMENDED, active | Downgraded. The only cited source is operator documentation (TEN-41), following the matrix reasoning for TX-10 and idempotency keys. |
| FIN-034 | Practices table: MANDATORY (ledgers built on this invariant) | RECOMMENDED, active | Follows matrix FN-21 and TX-10. Non-alteration is mandatory only in Germany (FIN-031). |
| FIN-008 | Matrix FN-3 classes adjustment periods OPTIONAL | RECOMMENDED, provisional, conditional on FIN-007 | Conditional consequence of an optional choice. Inference only, so provisional. |
| NUM-016 | Practices table: MANDATORY where gaps are not acceptable | RECOMMENDED, provisional | Follows matrix LG-13 and note 19. |
| FIN-012, RET-* and NUM-* statute rules | Matrix: MANDATORY | MANDATORY, provisional | RULE_FORMAT requires legal rules to be provisional with legal review. |
| FIN-023, FIN-024 | Matrix: No classification; evidence gap | OPTIONAL placeholder, needs_decision | OPTIONAL only because the field is required. These are decision items and not rules. RULE_FORMAT makes inference-only rules provisional; the request for this group requires needs_decision for no-source items, and that instruction is followed here. |
| RET-022 | Security file RT-4: OPTIONAL/CONTEXTUAL; matrix LG-23: RECOMMENDED | RECOMMENDED, provisional | Follows the matrix, as RULE_FORMAT requires. Inference only, so provisional. |
| RET-037 | Security file SD-1: MANDATORY (legal) as an inference | RECOMMENDED, provisional | RULE_FORMAT bars MANDATORY for inference-only rules, and no source names soft deletion. |
| RET-006 | Matrix LG-17: commercial part unverified | OPTIONAL placeholder, needs_decision | No rule is stated on an unverified period. |
| FIN-039 | Matrix FN-24: No classification; unresolved for Germany | OPTIONAL, needs_decision | OPTIONAL is a placeholder until counsel decides. |

## Rules

### Period status and close

#### FIN-001: Period status finer than company

| Field | Value |
|---|---|
| Statement | A general ledger SHOULD hold period status at a grain finer than the company. |
| Level | RECOMMENDED |
| Scope | OLTP |
| Applies when | General ledger and subledger posting with period control |
| Rationale | A single company-wide flag cannot close one ledger, module or book while another stays open, so close control is either too coarse or bypassed. |
| Exceptions | A single-ledger, single-module entity may use company grain; the finance owner approves. |
| Engine notes | SAP keys by posting period variant and account type; Oracle by application, ledger and period; D365 by per-entity ledger calendar and module access; NetSuite by period with subsidiary locks and per-book close; ERPNext by date range, company and document type. Odoo uses per-company lock dates. |
| Evidence | ERP-01, ERP-05, ERP-09, ERP-10, ERP-14, ERP-15, ERP-19, research/design_decision_matrix.md#FN-1 |
| Evidence strength | multi_vendor |
| Status | active |
| Decision ref | A17 |
| Check method | manual_review |
| Check description | Confirm that period status can differ below company level, at the grain chosen under FIN-002. |
| Lifecycle stage | Schema Design |

#### FIN-002: Period status grain

| Field | Value |
|---|---|
| Statement | Period status SHOULD be held per ledger and per application or module. |
| Level | RECOMMENDED |
| Scope | OLTP |
| Applies when | General ledger and subledger posting with period control |
| Rationale | The sources converge on finer than company but not on one grain, so an unapproved grain produces inconsistent close control across modules. |
| Exceptions | Deviation from the accepted default needs a recorded reason approved by the framework exception approver. |
| Engine notes | Grain differs by vendor: ledger and application (Oracle), module or account type (SAP, D365), book or document type (NetSuite, ERPNext). This is a judgment; no independent benchmark exists. |
| Evidence | ERP-01, ERP-05, ERP-09, ERP-14, ERP-15, ERP-19, research/design_decision_matrix.md#FN-1 |
| Evidence strength | multi_vendor |
| Status | active |
| Decision ref | A17 |
| Check method | manual_review |
| Check description | Confirm the approved grain is recorded and every period status record uses it. |
| Lifecycle stage | Schema Design |

#### FIN-003: Calendar separate from status

| Field | Value |
|---|---|
| Statement | The fiscal calendar definition SHOULD be held separately from period status. |
| Level | RECOMMENDED |
| Scope | OLTP |
| Applies when | Several ledgers or legal entities share a fiscal calendar |
| Rationale | Combining them forces calendar duplication or forces entities to open and close together. |
| Exceptions | A single-entity deployment may combine them; the finance owner approves. |
| Engine notes | D365 copies a shared calendar to a ledger calendar per legal entity; Oracle keys status by ledger; SAP assigns a variant to company codes. |
| Evidence | ERP-01, ERP-05, ERP-09, research/design_decision_matrix.md#FN-2 |
| Evidence strength | multi_vendor |
| Status | active |
| Decision ref | null |
| Check method | schema_lint |
| Check description | Check that calendar periods and per-entity period status are distinct records. |
| Lifecycle stage | Schema Design |

#### FIN-004: Period status checked at posting

| Field | Value |
|---|---|
| Statement | Posting SHOULD be refused when the period status for the entry's date and control grain does not permit it. |
| Level | RECOMMENDED |
| Scope | OLTP |
| Applies when | Any posting to a general ledger or subledger |
| Rationale | A status not checked at posting is decorative, and entries reach closed periods. |
| Exceptions | Controlled posting to an adjustment period or reopened period under FIN-006; the finance controller approves. |
| Engine notes | Vendors enforce this in application logic in the pages read: Odoo and ERPNext through dates, NetSuite through locks, Oracle and D365 through status. |
| Evidence | ERP-01, ERP-05, ERP-09, ERP-15, ERP-19, research/industry_best_practices.md#5 |
| Evidence strength | multi_vendor |
| Status | active |
| Decision ref | null |
| Check method | pipeline_test |
| Check description | Attempt a posting to a closed period and confirm it is refused. |
| Lifecycle stage | Transactions |

#### FIN-005: Close is an ordered gated process

| Field | Value |
|---|---|
| Statement | Period close SHOULD run as an ordered process with gating checks rather than as a single status change. |
| Level | RECOMMENDED |
| Scope | OLTP |
| Applies when | General ledger and subledger close |
| Rationale | A bare status write can close a period with open subledgers or pending intercompany work, leaving balances incomplete. |
| Exceptions | A small entity may use a manual checklist; the finance controller approves. |
| Engine notes | NetSuite publishes an ordered dependency list. Oracle can block GL close on open subledgers and always blocks on pending intercompany transactions. Oracle Fusion and NetSuite share one owner, so this counts as one vendor. |
| Evidence | ERP-05, ERP-06, ERP-14, research/design_decision_matrix.md#FN-4 |
| Evidence strength | single_vendor |
| Status | active |
| Decision ref | null |
| Check method | manual_review |
| Check description | Confirm the close procedure has ordered steps and that a failed gate stops the close. |
| Lifecycle stage | Governance |

#### FIN-006: Reopening invalidates later close work

| Field | Value |
|---|---|
| Statement | Reopening a closed period SHOULD be treated as invalidating close work in later periods and SHOULD record who reopened it and why. |
| Level | RECOMMENDED |
| Scope | OLTP |
| Applies when | A closed period can be reopened |
| Rationale | Later balances carried from a reopened period become stale without anyone being told. |
| Exceptions | none |
| Engine notes | Mechanisms differ: NetSuite reopens later closed periods automatically and stores a justification; D365 reopens on-hold periods and needs a close rerun to carry balances. The stored justification is NetSuite only. |
| Evidence | ERP-10, ERP-12, ERP-15, research/design_decision_matrix.md#FN-5 |
| Evidence strength | multi_vendor |
| Status | active |
| Decision ref | null |
| Check method | pipeline_test |
| Check description | Reopen a period and confirm later close results are flagged or rerun and a justification exists. |
| Lifecycle stage | Governance |

#### FIN-007: Adjustment periods

| Field | Value |
|---|---|
| Statement | A ledger MAY represent adjustment periods as separate periods that share dates with a regular period. |
| Level | OPTIONAL |
| Scope | OLTP, data_warehouse |
| Applies when | Year-end or audit adjustments need separation from regular activity |
| Rationale | Without separation, adjustments mix with regular activity; with it, extra periods must be maintained. |
| Exceptions | none |
| Engine notes | SAP special periods 13 to 16; D365 closing periods; Oracle adjusting periods share the period-end date. NetSuite has no statement; Odoo and ERPNext show none in pages read. Oracle does not copy journals to adjusting periods on secondary ledgers with a different calendar. |
| Evidence | ERP-01, ERP-05, ERP-06, ERP-09, ERP-10, research/design_decision_matrix.md#FN-3 |
| Evidence strength | multi_vendor |
| Status | active |
| Decision ref | null |
| Check method | manual_review |
| Check description | Confirm the decision to use or not use adjustment periods is recorded. |
| Lifecycle stage | Data Modeling |

#### FIN-008: Period identifier in analytical copies

| Field | Value |
|---|---|
| Statement | Where adjustment periods exist, analytical copies of ledger data SHOULD carry the period identifier and SHOULD NOT derive the period from the entry date alone. |
| Level | RECOMMENDED |
| Scope | data_warehouse, lakehouse, OLAP |
| Applies when | Adjustment periods are used in the source ledger |
| Rationale | Adjustment periods overlap in dates with regular periods, so a date-derived period misstates period totals. |
| Exceptions | none |
| Engine notes | Inference from vendor date overlap; no source states this rule. Analytical systems only; it does not apply to OLTP posting. |
| Evidence | ERP-01, ERP-06, ERP-09, research/design_decision_matrix.md#FN-3 |
| Evidence strength | inference |
| Status | provisional |
| Decision ref | null |
| Check method | pipeline_test |
| Check description | Check that warehouse period totals reconcile to source period totals including adjustment periods. |
| Lifecycle stage | Reporting |

#### FIN-009: Irreversible close

| Field | Value |
|---|---|
| Statement | Irreversible period close MAY be offered only under an approved exception, and the accepted default is reopenable close with restricted reopening. |
| Level | OPTIONAL |
| Scope | OLTP |
| Applies when | A general ledger offers period close |
| Rationale | An irreversible close gives assurance but makes a late correction impossible in that period. |
| Exceptions | Deviation from the accepted default needs a recorded reason approved by the framework exception approver. |
| Engine notes | Oracle offers a permanent close and Odoo a Hard Lock that cannot be overridden. D365 offers Permanently closed and advises against it because the period cannot reopen. |
| Evidence | ERP-05, ERP-10, ERP-18, research/design_decision_matrix.md#FN-6 |
| Evidence strength | multi_vendor |
| Status | active |
| Decision ref | B13 |
| Check method | manual_review |
| Check description | Confirm the decision is recorded and the system behaves accordingly. |
| Lifecycle stage | Governance |

#### FIN-010: Fiscal-year status

| Field | Value |
|---|---|
| Statement | A ledger MAY hold fiscal-year status separately from period status. |
| Level | OPTIONAL |
| Scope | OLTP |
| Applies when | Year-end close has effects that differ from period close |
| Rationale | Without separation, a year-end block cannot be expressed while a period is open. |
| Exceptions | none |
| Engine notes | D365 blocks reversal after year-end close even with a period open. No other vendor was confirmed. |
| Evidence | ERP-12, research/design_decision_matrix.md#FN-7 |
| Evidence strength | single_vendor |
| Status | active |
| Decision ref | null |
| Check method | manual_review |
| Check description | Confirm whether fiscal-year status exists and how it affects reversal. |
| Lifecycle stage | Data Modeling |

#### FIN-011: P&L closing as a separate object

| Field | Value |
|---|---|
| Statement | Profit and loss closing MAY be represented as a separate entry or voucher from period close. |
| Level | OPTIONAL |
| Scope | OLTP |
| Applies when | Year-end transfer of profit or loss to equity |
| Rationale | Treating closing as a status can suggest history was erased or backdating stopped, which ERPNext says its voucher does not do. |
| Exceptions | none |
| Engine notes | ERPNext uses a Period Closing Voucher; D365 generates year-end entries; Odoo posts a manual entry to equity. |
| Evidence | ERP-10, ERP-18, ERP-19, research/design_decision_matrix.md#FN-8 |
| Evidence strength | multi_vendor |
| Status | active |
| Decision ref | null |
| Check method | manual_review |
| Check description | Confirm how year-end profit or loss transfer is represented. |
| Lifecycle stage | Data Modeling |

### Currency and rates

#### FIN-012: Transaction-date rate (US GAAP)

| Field | Value |
|---|---|
| Statement | A foreign-currency transaction of a US GAAP issuer MUST be initially measured using the exchange rate at the transaction date. |
| Level | MANDATORY |
| Scope | OLTP |
| Applies when | Jurisdiction: United States. US GAAP issuers, foreign-currency transactions, measurement only |
| Rationale | The SEC described a mid-prior-month convention as not in accordance with GAAP. Requires legal review by counsel for the entity concerned before adoption. |
| Exceptions | FAS 52, superseded by the Codification, allows an appropriately weighted average where appropriate; whether and when this remains available needs counsel. Requires legal review by counsel for the entity concerned before adoption. |
| Engine notes | The source sets measurement, not storage. A stored per-line rate is an inference. IAS 21 rate rules were not read, so this rule does not extend to IFRS reporters. |
| Evidence | ERP-22, research/design_decision_matrix.md#FN-9 |
| Evidence strength | standard |
| Status | provisional |
| Decision ref | null |
| Check method | manual_review |
| Check description | Review that foreign-currency measurement uses a rate attributable to the transaction date. |
| Lifecycle stage | Transactions |

#### FIN-013: Several rate roles

| Field | Value |
|---|---|
| Statement | A ledger SHOULD support more than one rate role per period, such as closing, average and historical. |
| Level | RECOMMENDED |
| Scope | OLTP, OLAP |
| Applies when | Revaluation, translation or consolidation is performed |
| Rationale | A single rate cannot serve balance-sheet and income-statement translation, which FAS 52 and vendors distinguish. |
| Exceptions | A single-currency entity is exempt; the finance owner approves. |
| Engine notes | NetSuite stores three per period and subsidiary pair; D365 and SAP use rate types. |
| Evidence | ERP-03, ERP-11, ERP-16, ERP-22, research/design_decision_matrix.md#FN-10 |
| Evidence strength | multi_vendor |
| Status | active |
| Decision ref | null |
| Check method | schema_lint |
| Check description | Check that rate type or role is part of the rate data. |
| Lifecycle stage | Schema Design |

#### FIN-014: Rates keyed by pair, date and type

| Field | Value |
|---|---|
| Statement | Exchange rates SHOULD be identified by source currency, target currency, date and rate type. |
| Level | RECOMMENDED |
| Scope | OLTP, data_warehouse |
| Applies when | Multi-currency general ledger or warehouse rate tables |
| Rationale | A rate without pair, date and type cannot be attributed to a transaction and cannot be reconciled. |
| Exceptions | none |
| Engine notes | Oracle key: from currency, to currency, date and type. ERPNext is latest eligible record. SAP valid-from logic was not established. |
| Evidence | ERP-08, ERP-20, research/design_decision_matrix.md#FN-11 |
| Evidence strength | multi_vendor |
| Status | active |
| Decision ref | null |
| Check method | schema_lint |
| Check description | Check that rates are unique on pair, date and rate type. |
| Lifecycle stage | Schema Design |

#### FIN-015: Rate effective-dating

| Field | Value |
|---|---|
| Statement | Rate lookup SHOULD use an exact-day row for the pair and rate type. |
| Level | RECOMMENDED |
| Scope | OLTP, data_warehouse |
| Applies when | Multi-currency posting |
| Rationale | Exact-day rows fail on gaps and most-recent lookup can silently use stale rates, so the choice changes results. |
| Exceptions | Deviation from the accepted default needs a recorded reason approved by the framework exception approver. |
| Engine notes | Oracle key is exact-day; ERPNext picks the latest eligible record; SAP valid-from logic was not established. A staleness limit is the documented option for most-recent lookup. This is a judgment; no independent benchmark exists. |
| Evidence | ERP-08, ERP-20, research/design_decision_matrix.md#FN-11 |
| Evidence strength | multi_vendor |
| Status | active |
| Decision ref | B14 |
| Check method | manual_review |
| Check description | Confirm the approved lookup pattern and any staleness limit are documented and tested. |
| Lifecycle stage | Data Validation |

#### FIN-016: Inverse rates

| Field | Value |
|---|---|
| Statement | Each currency direction MAY be stored as its own rate, which is the accepted default. |
| Level | OPTIONAL |
| Scope | OLTP, data_warehouse |
| Applies when | Conversion in both directions of a pair |
| Rationale | A rate and its reciprocal may not agree after rounding, so two directions can give different results. |
| Exceptions | Deviation from the accepted default needs a recorded reason approved by the framework exception approver. |
| Engine notes | Conflicting: ERPNext says the inverse is not automatically equal and needs its own record; Oracle stores a generally reciprocal row; SAP presents direct and indirect quotation. [WF] Re-check the Oracle statement against raw page text. |
| Evidence | ERP-03, ERP-08, ERP-20, research/design_decision_matrix.md#FN-12 |
| Evidence strength | multi_vendor |
| Status | active |
| Decision ref | B15 |
| Check method | manual_review |
| Check description | Confirm the approved approach and test round-trip differences. |
| Lifecycle stage | Schema Design |

#### FIN-017: Amounts held per line

| Field | Value |
|---|---|
| Statement | A posted line SHOULD hold the transaction currency amount and the entity currency amount together, with a reporting currency amount where one is used. |
| Level | RECOMMENDED |
| Scope | OLTP |
| Applies when | Multi-currency general ledger or subledger |
| Rationale | Recomputing entity or reporting amounts later cannot reproduce the amounts as posted. |
| Exceptions | A single-currency entity is exempt; the finance owner approves. |
| Engine notes | D365 records accounting and optional reporting currency; ERPNext distinguishes three currencies; SAP allows up to eight additional currency types per ledger. ERPNext advises against changing an account currency after entries exist. |
| Evidence | ERP-03, ERP-09, ERP-20, research/design_decision_matrix.md#FN-13 |
| Evidence strength | multi_vendor |
| Status | active |
| Decision ref | null |
| Check method | schema_lint |
| Check description | Check that lines hold both transaction and entity amounts with their currencies. |
| Lifecycle stage | Schema Design |

#### FIN-018: Revaluation is a recorded run

| Field | Value |
|---|---|
| Statement | Foreign-currency revaluation SHOULD be recorded as a run with its own rate date rather than as ad hoc journals. |
| Level | RECOMMENDED |
| Scope | OLTP |
| Applies when | Period-end revaluation of foreign-currency balances |
| Rationale | Ad hoc journals cannot show which rate date, scope and method produced a revaluation. |
| Exceptions | none |
| Engine notes | D365 keeps run history with a separate rate date. NetSuite uses a period-end rate and advises locking first. |
| Evidence | ERP-11, ERP-17, research/design_decision_matrix.md#FN-14 |
| Evidence strength | multi_vendor |
| Status | active |
| Decision ref | null |
| Check method | manual_review |
| Check description | Confirm each revaluation can be traced to a run with a rate date. |
| Lifecycle stage | Governance |

#### FIN-019: Realized and unrealized differences

| Field | Value |
|---|---|
| Statement | Realized and unrealized exchange differences SHOULD be posted to separate accounts. |
| Level | RECOMMENDED |
| Scope | OLTP |
| Applies when | Foreign-currency settlement and revaluation |
| Rationale | Combined accounts hide how much of a gain or loss has actually been realized. |
| Exceptions | none |
| Engine notes | D365, ERPNext, Odoo and NetSuite separate them. Presentation is unresolved: D365's ledger page places unrealized gains and losses on the balance sheet, while its revaluation example posts to accounts named Unrealized loss and gain against cash. |
| Evidence | ERP-09, ERP-11, ERP-17, ERP-18, ERP-20, research/design_decision_matrix.md#FN-15 |
| Evidence strength | multi_vendor |
| Status | active |
| Decision ref | null |
| Check method | manual_review |
| Check description | Check the chart of accounts distinguishes the two. |
| Lifecycle stage | Data Modeling |

#### FIN-020: Reversal of revaluation

| Field | Value |
|---|---|
| Statement | Earlier revaluation MAY be reversed in the next period for AR and AP subledgers only, which is the accepted default. |
| Level | OPTIONAL |
| Scope | OLTP |
| Applies when | Revaluation is performed across periods |
| Rationale | Reversing and carrying forward give different period comparisons. |
| Exceptions | Deviation from the accepted default needs a recorded reason approved by the framework exception approver. |
| Engine notes | D365 GL does not reverse earlier revaluation; D365 AR and AP do and cannot be reversed afterward, only rerun. An older Oracle statement is a search snippet and is not relied on. |
| Evidence | ERP-11, ERP-12, research/design_decision_matrix.md#FN-16 |
| Evidence strength | single_vendor |
| Status | active |
| Decision ref | B16 |
| Check method | manual_review |
| Check description | Confirm the approved method is applied consistently. |
| Lifecycle stage | Governance |

#### FIN-021: Rounding differences

| Field | Value |
|---|---|
| Statement | A ledger MAY post conversion rounding differences to a defined account or hold them within a stated per-line tolerance. |
| Level | OPTIONAL |
| Scope | OLTP |
| Applies when | Currency conversion produces rounding differences |
| Rationale | Rounding differences with no defined home make balanced entries fail or leave unexplained residuals. |
| Exceptions | none |
| Engine notes | ERPNext rounds per line, so totals can differ by small units. Oracle balances by legal entity including rounding imbalances. |
| Evidence | ERP-07, ERP-20, research/design_decision_matrix.md#FN-17 |
| Evidence strength | multi_vendor |
| Status | active |
| Decision ref | null |
| Check method | manual_review |
| Check description | Confirm the chosen treatment is documented. |
| Lifecycle stage | Data Validation |

#### FIN-022: Translation paths

| Field | Value |
|---|---|
| Statement | Currency translation MAY use a direct path or an intermediate entity. |
| Level | OPTIONAL |
| Scope | OLTP, OLAP |
| Applies when | Consolidation across several currencies |
| Rationale | Assuming translation is transitive can produce results that the product does not compute. |
| Exceptions | none |
| Engine notes | D365 translates directly from source currency and needs an intermediate company for a two-step path. NetSuite rates are per subsidiary pair. |
| Evidence | ERP-13, ERP-16, research/design_decision_matrix.md#FN-18 |
| Evidence strength | multi_vendor |
| Status | active |
| Decision ref | null |
| Check method | manual_review |
| Check description | Confirm the translation path for each consolidation chain. |
| Lifecycle stage | Reporting |

#### FIN-023: Rate precision (no source)

| Field | Value |
|---|---|
| Statement | Stored exchange rates MAY use the precision each deployment records under TYP-011; no value set by this standard. |
| Level | OPTIONAL |
| Scope | OLTP, data_warehouse |
| Applies when | Exchange rates are stored |
| Rationale | No vendor page or standard-setter page read states a rate precision, so any number here would be invented. |
| Exceptions | none |
| Engine notes | No engine or vendor figure is available. D365's example rates are a display example and do not establish a precision. Superseded by TYP-011 under OR-2. |
| Evidence | research/design_decision_matrix.md#FN-19, research/research_gaps.md#6a |
| Evidence strength | inference |
| Status | superseded |
| Decision ref | A14 |
| Superseded by | TYP-011 |
| Check method | manual_review |
| Check description | Confirm the deployment records its rate precision under TYP-011. |
| Lifecycle stage | Schema Design |

#### FIN-024: Triangulation (no source)

| Field | Value |
|---|---|
| Statement | Currency triangulation MAY be used only under a method recorded for the deployment; no value set, because no source describes a method. |
| Level | OPTIONAL |
| Scope | OLTP |
| Applies when | Conversions through a third currency are required |
| Rationale | No vendor page opened describes triangulation, so any method here would be invented. |
| Exceptions | none |
| Engine notes | D365 mentions triangulation only in a training objective seen in a search snippet, which is not relied on. |
| Evidence | research/design_decision_matrix.md#FN-30, research/industry_best_practices.md#5 |
| Evidence strength | inference |
| Status | provisional |
| Decision ref | B17 |
| Check method | manual_review |
| Check description | Confirm the owner has recorded a decision and any method is documented. |
| Lifecycle stage | Data Modeling |

### Ledger balance

#### FIN-025: Journals balance

| Field | Value |
|---|---|
| Statement | Every posted journal in a double-entry ledger MUST have entries that sum to zero. |
| Level | MANDATORY |
| Scope | OLTP |
| Applies when | Ledgers built on double-entry bookkeeping |
| Rationale | An unbalanced journal means the books no longer reconcile and the error spreads into every balance. |
| Exceptions | none |
| Engine notes | The basis on which balance is tested differs: Modern Treasury per currency, Oracle by legal entity including rounding, ERPNext per company entry. See FIN-026. |
| Evidence | TEN-40, TEN-41, TEN-42, TEN-43, TEN-44, ERP-07, ERP-20, research/industry_best_practices.md#5 |
| Evidence strength | multi_vendor |
| Status | active |
| Decision ref | null |
| Check method | pipeline_test |
| Check description | Sum entries per journal in the posting test and in a periodic reconciliation and confirm zero. |
| Lifecycle stage | Data Validation |

#### FIN-026: Balance per currency

| Field | Value |
|---|---|
| Statement | Each journal SHOULD balance per currency and SHOULD enforce this in the posting transaction. |
| Level | RECOMMENDED |
| Scope | OLTP |
| Applies when | The store is a financial ledger, whether it holds entries in one currency or several. |
| Rationale | Amounts in different currencies cannot be summed, so a journal can appear to balance while one currency is out. |
| Exceptions | none |
| Engine notes | Modern Treasury is the only source explicitly requiring balance per currency. Stripe does not report how balances are modelled. Held provisional under OR-5: the evidence is case studies only. Canonical rule for TXN-016, with its wider ledger scope. |
| Evidence | TEN-41, TEN-42, CASE-31, research/design_decision_matrix.md#TX-11, research/industry_best_practices.md#5 |
| Evidence strength | case_study |
| Status | provisional |
| Decision ref | null |
| Check method | pipeline_test |
| Check description | Sum entries per journal and currency and confirm zero. |
| Lifecycle stage | Data Validation |

#### FIN-027: Atomic multi-entry posting

| Field | Value |
|---|---|
| Statement | All entries of a journal SHOULD be written atomically in one transaction. |
| Level | RECOMMENDED |
| Scope | OLTP |
| Applies when | Posting multi-entry journals |
| Rationale | A partial journal is visible as an unbalanced entry until repaired. |
| Exceptions | A distributed write with a compensating process may be approved by the system owner. |
| Engine notes | Multi-document atomicity differs by engine; see the transactions standards. |
| Evidence | TEN-41, research/industry_best_practices.md#5 |
| Evidence strength | single_vendor |
| Status | active |
| Decision ref | null |
| Check method | pipeline_test |
| Check description | Inject a failure during posting and confirm no partial journal remains. |
| Lifecycle stage | Transactions |

#### FIN-028: Derive balances from entries

| Field | Value |
|---|---|
| Statement | Balances SHOULD be derived from entries, and any stored balance SHOULD be reconcilable to those entries. |
| Level | RECOMMENDED |
| Scope | OLTP |
| Applies when | Ledger with materialized balances |
| Rationale | A balance that drifts from entries cannot be explained, and entries are the auditable record. |
| Exceptions | none |
| Engine notes | Fowler and Modern Treasury derive the balance from entries; Square materializes it. These agree only if entries remain the source of truth. |
| Evidence | TEN-40, TEN-41, TEN-42, research/industry_best_practices.md#5 |
| Evidence strength | multi_vendor |
| Status | active |
| Decision ref | null |
| Check method | catalog_query |
| Check description | Compare stored balances to the sum of entries and report differences. |
| Lifecycle stage | Data Quality |

#### FIN-029: Explicit posting lifecycle

| Field | Value |
|---|---|
| Statement | Transactional financial documents SHOULD have an explicit lifecycle state, such as pending, posted and archived, with financial fields fixed once posted. |
| Level | RECOMMENDED |
| Scope | OLTP |
| Applies when | Documents that move from draft to posted |
| Rationale | Without an explicit state, drafts and posted entries cannot be distinguished or controlled. |
| Exceptions | none |
| Engine notes | Modern Treasury uses pending, posted, archived, and keeps metadata updatable. Frappe docstatus has draft, submitted, cancelled. Amend semantics in Frappe were not read. |
| Evidence | TEN-41, CASE-31, CASE-32, CASE-47, research/industry_best_practices.md#5 |
| Evidence strength | multi_vendor |
| Status | active |
| Decision ref | null |
| Check method | schema_lint |
| Check description | Check that posted documents carry a state and that financial fields are protected after posting. |
| Lifecycle stage | Schema Design |

#### FIN-030: Clearing accounts monitored

| Field | Value |
|---|---|
| Statement | Clearing accounts SHOULD be monitored for a net zero balance at steady state. |
| Level | RECOMMENDED |
| Scope | OLTP |
| Applies when | Fund flows or subledgers use clearing accounts |
| Rationale | A non-zero clearing balance at steady state signals a missing or wrong event. |
| Exceptions | Accounts with a documented, expected residual; the finance controller approves. |
| Engine notes | Detailed evidence is Stripe's alone. |
| Evidence | TEN-43, research/industry_best_practices.md#5 |
| Evidence strength | case_study |
| Status | active |
| Decision ref | null |
| Check method | runtime_monitor |
| Check description | Alert when a clearing account stays non-zero past its expected settlement window. |
| Lifecycle stage | Monitoring |

### Reversal and immutability

#### FIN-031: Non-alteration of books (Germany)

| Field | Value |
|---|---|
| Statement | German commercial and tax books MUST NOT be changed in a way that loses the original content or leaves the timing of the change uncertain. |
| Level | MANDATORY |
| Scope | OLTP |
| Applies when | Jurisdiction: Germany. Commercial and tax books, including entries held in GL and subledger systems |
| Rationale | HGB 239(3) and AO 146(4) forbid such changes. Requires legal review by counsel for the entity concerned before adoption. |
| Exceptions | No exception identified in the sources read. Requires legal review by counsel for the entity concerned before adoption. |
| Engine notes | The statutes bar loss of original content and do not prescribe append-only storage or any database mechanism. |
| Evidence | ERP-23, research/design_decision_matrix.md#FN-20, research/industry_best_practices.md#5 |
| Evidence strength | standard |
| Status | provisional |
| Decision ref | B10 |
| Check method | manual_review |
| Check description | Review that a posted entry's original content and the timing of any change remain ascertainable. |
| Lifecycle stage | Governance |

#### FIN-032: Accurate books (US issuers)

| Field | Value |
|---|---|
| Statement | US issuers MUST keep books and records that accurately and fairly reflect transactions in reasonable detail and MUST maintain internal accounting controls. |
| Level | MANDATORY |
| Scope | OLTP |
| Applies when | Jurisdiction: United States. Issuers under 15 USC 78m(b)(2) and 17 CFR 240.13b2-1 |
| Rationale | Non-compliance is a violation of federal securities law. Requires legal review by counsel for the entity concerned before adoption. |
| Exceptions | No exception identified in the sources read. Requires legal review by counsel for the entity concerned before adoption. |
| Engine notes | No mechanism is named. Row-level immutability is an inference and is not stated by these texts. |
| Evidence | ERP-24, research/design_decision_matrix.md#FN-29, research/industry_best_practices.md#5 |
| Evidence strength | standard |
| Status | provisional |
| Decision ref | null |
| Check method | manual_review |
| Check description | Review that controls exist and that records can show transactions accurately. |
| Lifecycle stage | Governance |

#### FIN-033: Journal-entry population support

| Field | Value |
|---|---|
| Statement | US audited issuers SHOULD be able to demonstrate the completeness of the journal entry population to auditors. |
| Level | RECOMMENDED |
| Scope | OLTP |
| Applies when | Jurisdiction: United States. Issuers audited under PCAOB standards |
| Rationale | PCAOB staff list untested journal entry completeness as a deficiency; the publication states it is not a Board rule. Requires legal review by counsel for the entity concerned before adoption. |
| Exceptions | Staff text is not a rule. Requires legal review by counsel for the entity concerned before adoption. |
| Engine notes | Row-level immutability is an inference. AS 2401 was known only through this staff publication. |
| Evidence | ERP-25, research/design_decision_matrix.md#FN-29, research/industry_best_practices.md#5 |
| Evidence strength | standard |
| Status | provisional |
| Decision ref | null |
| Check method | manual_review |
| Check description | Confirm a complete journal population can be produced for a period. |
| Lifecycle stage | Governance |

#### FIN-034: Correct by new entry

| Field | Value |
|---|---|
| Statement | Posted financial entries SHOULD be corrected by new reversing or correcting entries and SHOULD NOT be edited in place. |
| Level | RECOMMENDED |
| Scope | OLTP |
| Applies when | General ledger and subledger entries after posting |
| Rationale | In-place edits lose the original and break audit tracing. |
| Exceptions | Year-end generated vouchers follow FIN-039, which stays provisional pending counsel. System owner and finance controller approve any other exception. |
| Engine notes | Oracle, SAP document reversal, D365 and ERPNext correct by new entry. Stripe, Square and Modern Treasury permit only history-preserving correction. Vendor exceptions: D365 year-end reversal deletes vouchers and NetSuite Delete keeps only a record of deletion. Non-alteration is mandatory only in Germany (FIN-031), and no law read requires append-only storage or database immutability. |
| Evidence | ERP-02, ERP-06, ERP-12, ERP-19, TEN-41, TEN-42, TEN-43, research/design_decision_matrix.md#FN-21, research/design_decision_matrix.md#TX-10, research/industry_best_practices.md#5 |
| Evidence strength | multi_vendor |
| Status | active |
| Decision ref | B10 |
| Check method | schema_lint |
| Check description | Check that posted financial entry tables do not permit ordinary updates or deletes of financial fields. |
| Lifecycle stage | Transactions |

#### FIN-035: Reversal method

| Field | Value |
|---|---|
| Statement | Reversal MAY use a posted inverse entry, which is the accepted default. |
| Level | OPTIONAL |
| Scope | OLTP |
| Applies when | Reversal of posted entries |
| Rationale | Methods produce different debit and credit activity totals, so reports differ by method. |
| Exceptions | Deviation from the accepted default needs a recorded reason approved by the framework exception approver. |
| Engine notes | SAP normal reversal raises figures and negative posting resets them. Oracle offers Change Sign and Switch Debit or Credit. Fowler catalogues reversal and difference strategies. |
| Evidence | ERP-02, ERP-06, TEN-40, research/design_decision_matrix.md#FN-22 |
| Evidence strength | multi_vendor |
| Status | active |
| Decision ref | B11 |
| Check method | manual_review |
| Check description | Confirm the method and its effect on activity totals are documented. |
| Lifecycle stage | Transactions |

#### FIN-036: Reversing a reversal

| Field | Value |
|---|---|
| Statement | A system MAY forbid reversing a reversal, which is the accepted default, with correction made by a new entry. |
| Level | OPTIONAL |
| Scope | OLTP |
| Applies when | Reversal entries exist |
| Rationale | Allowing it keeps correction simple but gives a longer chain to audit, and forbidding it requires a new entry. |
| Exceptions | Deviation from the accepted default needs a recorded reason approved by the framework exception approver. |
| Engine notes | Conflicting: Oracle forbids reversing a reversal; D365 allows it. |
| Evidence | ERP-06, ERP-12, research/design_decision_matrix.md#FN-23 |
| Evidence strength | multi_vendor |
| Status | active |
| Decision ref | B12 |
| Check method | manual_review |
| Check description | Confirm the behaviour matches the approved decision. |
| Lifecycle stage | Transactions |

#### FIN-037: Reversal attributes

| Field | Value |
|---|---|
| Statement | A reversal SHOULD carry its own date, method and reason. |
| Level | RECOMMENDED |
| Scope | OLTP |
| Applies when | Reversal of posted entries |
| Rationale | Defaulting to the original date or an unstated reason makes corrections hard to review. |
| Exceptions | none |
| Engine notes | D365 allows a different reversal date; SAP requires a reason; Oracle sets date and method. |
| Evidence | ERP-02, ERP-06, ERP-12, research/design_decision_matrix.md#FN-25 |
| Evidence strength | multi_vendor |
| Status | active |
| Decision ref | null |
| Check method | schema_lint |
| Check description | Check that reversal records carry date, method and reason. |
| Lifecycle stage | Schema Design |

#### FIN-038: Reversal eligibility

| Field | Value |
|---|---|
| Statement | Reversal eligibility SHOULD be decided from settlement, transfer and fiscal status as well as from the entry itself. |
| Level | RECOMMENDED |
| Scope | OLTP |
| Applies when | Reversal of posted entries |
| Rationale | Reversing a settled or transferred item leaves the subledger and ledger inconsistent. |
| Exceptions | none |
| Engine notes | D365 uses settlement, transfer and fiscal status; Oracle uses non-reversal journal and unfrozen source status. SAP blocks cleared items until reset. |
| Evidence | ERP-02, ERP-06, ERP-12, research/design_decision_matrix.md#FN-26 |
| Evidence strength | multi_vendor |
| Status | active |
| Decision ref | null |
| Check method | pipeline_test |
| Check description | Attempt to reverse a settled or transferred item and confirm the block. |
| Lifecycle stage | Transactions |

#### FIN-039: Generated voucher deletion (Germany unresolved)

| Field | Value |
|---|---|
| Statement | A system MAY offer year-end reversal only by posting a reversing voucher, and generated vouchers are not deleted unless counsel confirms otherwise. |
| Level | OPTIONAL |
| Scope | OLTP |
| Applies when | Jurisdiction: Germany for the legal question; any system offering year-end reversal for the design default |
| Rationale | No source says whether generated opening balances count as books under HGB 239(3). Requires legal review by counsel for the entity concerned before adoption. |
| Exceptions | Deletion only if counsel confirms it is permitted. Requires legal review by counsel for the entity concerned before adoption. |
| Engine notes | D365 year-end reversal deletes vouchers with a history record. NetSuite Delete keeps only a record of deletion and is unavailable when reversing-journal voiding is on. |
| Evidence | ERP-10, ERP-12, ERP-15, ERP-23, research/design_decision_matrix.md#FN-24 |
| Evidence strength | standard |
| Status | provisional |
| Decision ref | B10 |
| Check method | manual_review |
| Check description | Confirm counsel's position is recorded and the behaviour matches it. |
| Lifecycle stage | Governance |

#### FIN-040: Subledger entries before GL transfer

| Field | Value |
|---|---|
| Statement | Subledger entries not yet transferred to the general ledger SHOULD be tracked until transfer completes. |
| Level | RECOMMENDED |
| Scope | OLTP |
| Applies when | Subledger postings are transferred to the GL asynchronously |
| Rationale | Untracked entries are invisible to close and to reversal checks. |
| Exceptions | none |
| Engine notes | D365 blocks some reversals until transfer. Oracle treats unprocessed and untransferred subledger transactions as period close exceptions. |
| Evidence | ERP-06, ERP-12, research/design_decision_matrix.md#FN-27 |
| Evidence strength | multi_vendor |
| Status | active |
| Decision ref | null |
| Check method | catalog_query |
| Check description | List subledger entries not yet transferred and confirm close reports them. |
| Lifecycle stage | Data Quality |

#### FIN-041: Tamper evidence

| Field | Value |
|---|---|
| Statement | A ledger MAY use a hash chain or tamper-evident storage for journal entries. |
| Level | OPTIONAL |
| Scope | OLTP |
| Applies when | Added tamper evidence is wanted beyond application controls |
| Rationale | Without it, an authorised database change can go unnoticed; with it, complexity increases. |
| Exceptions | none |
| Engine notes | Odoo's hash chain is the only cryptographic control seen, and no law or standard read requires hashing for general ledgers. KSA e-invoice hashing is a separate rule (NUM-013). |
| Evidence | ERP-18, GOV-06, research/design_decision_matrix.md#FN-28 |
| Evidence strength | single_vendor |
| Status | active |
| Decision ref | null |
| Check method | manual_review |
| Check description | Record whether tamper evidence is used and how it is verified. |
| Lifecycle stage | Governance |

### Multi-company

#### FIN-042: Legal entity, ledger and business unit distinct

| Field | Value |
|---|---|
| Statement | Legal entity, ledger and business unit SHOULD be modelled as distinct concepts. |
| Level | RECOMMENDED |
| Scope | OLTP, OLAP |
| Applies when | ERP with more than one legal entity, ledger or business unit |
| Rationale | Combining them prevents one entity holding several ledgers or a business unit posting across structures. |
| Exceptions | A single-entity deployment may combine them; the finance owner approves. |
| Engine notes | Oracle separates balancing segment, ledger and business unit; D365 configures a ledger per legal entity. No official SAP company-code definition was read. |
| Evidence | ERP-07, ERP-09, research/design_decision_matrix.md#MT-17 |
| Evidence strength | multi_vendor |
| Status | active |
| Decision ref | null |
| Check method | manual_review |
| Check description | Confirm the model distinguishes the three concepts. |
| Lifecycle stage | Data Modeling |

#### FIN-043: One company per posting

| Field | Value |
|---|---|
| Statement | A financial posting SHOULD belong to one legal entity, with intercompany activity handled under FIN-047. |
| Level | RECOMMENDED |
| Scope | OLTP |
| Applies when | Multi-entity ERP |
| Rationale | Mixed-entity postings cannot be balanced or closed by entity. |
| Exceptions | Intercompany transactions are handled under FIN-047, and decomposing them is a modeling choice. NetSuite-style intercompany postings to two or more subsidiaries need finance controller approval. |
| Engine notes | NetSuite generally posts to one subsidiary with intercompany exceptions; D365 uses company ID as a data-security boundary. Topic 14 labelled this MANDATORY; the sources are vendor designs. |
| Evidence | TEN-08, TEN-09, TEN-10, ERP-07, research/design_decision_matrix.md#MT-12, research/industry_best_practices.md#5 |
| Evidence strength | multi_vendor |
| Status | active |
| Decision ref | null |
| Check method | schema_lint |
| Check description | Check that every posting carries exactly one legal entity. |
| Lifecycle stage | Schema Design |

#### FIN-044: Company identifier on ERP tables

| Field | Value |
|---|---|
| Statement | Transactional and most setup tables in a multi-company ERP SHOULD carry a company identifier. |
| Level | RECOMMENDED |
| Scope | OLTP |
| Applies when | Multi-company ERP |
| Rationale | Without the identifier, posting, security and reporting cannot be scoped to a company. |
| Exceptions | Tenant-shared setup tables approved by the data owner. |
| Engine notes | ERP products use a company or legal-entity boundary for posting and sometimes security. Odoo uses company_id; iDempiere's organization column is verified on one interface only. Superseded by TEN-019 under OR-9. |
| Evidence | TEN-08, TEN-09, TEN-10, ERP-07, ERP-09, research/design_decision_matrix.md#MT-11 |
| Evidence strength | multi_vendor |
| Status | superseded |
| Decision ref | A5 |
| Superseded by | TEN-019 |
| Check method | schema_lint |
| Check description | List ERP tables without a company identifier and confirm each is approved. |
| Lifecycle stage | Schema Design |

#### FIN-045: Tenant separate from legal entity

| Field | Value |
|---|---|
| Statement | A multi-tenant ERP SHOULD treat the tenant and the legal entity as separate identifiers. |
| Level | RECOMMENDED |
| Scope | OLTP |
| Applies when | SaaS ERP in which a customer can hold several legal entities |
| Rationale | A tenant is the customer boundary and a company is the posting and statutory boundary, so conflating them blocks multi-entity customers. |
| Exceptions | A single-entity product may combine them; the system owner approves. |
| Engine notes | iDempiere's client and organization columns show two levels on the AD_Org interface only. The conclusion that both are always needed is an inference. Superseded by TEN-018 under OR-18. |
| Evidence | TEN-08, TEN-09, TEN-10, CASE-50, research/industry_best_practices.md#7 |
| Evidence strength | inference |
| Status | superseded |
| Decision ref | null |
| Superseded by | TEN-018 |
| Check method | manual_review |
| Check description | Confirm tenant and legal entity are separate where the product is multi-tenant. |
| Lifecycle stage | Data Modeling |

#### FIN-046: Master data scope

| Field | Value |
|---|---|
| Statement | Master data MAY be shared across a tenant with per-company restriction available, which is the accepted default under TEN-022. |
| Level | OPTIONAL |
| Scope | OLTP |
| Applies when | Multi-company ERP with shared master data |
| Rationale | Shared master data aids reuse, while per-company restriction aids control. |
| Exceptions | Deviation from the accepted default needs a recorded reason approved by the framework exception approver. |
| Engine notes | Dynamics cannot override this; Odoo can restrict (recorded as C-18 in the matrix). Superseded by TEN-022 under OR-12. |
| Evidence | TEN-08, TEN-10, research/design_decision_matrix.md#MT-14 |
| Evidence strength | multi_vendor |
| Status | superseded |
| Decision ref | A5 |
| Superseded by | TEN-022 |
| Check method | manual_review |
| Check description | Confirm the approved master data scope is applied. |
| Lifecycle stage | Data Modeling |

### Intercompany

#### FIN-047: Intercompany as linked entries

| Field | Value |
|---|---|
| Statement | Intercompany activity SHOULD be recorded as linked entries, each balanced within its own legal entity. |
| Level | RECOMMENDED |
| Scope | OLTP, OLAP |
| Applies when | Transactions between legal entities |
| Rationale | Unlinked or cross-balanced entries cannot be matched, eliminated or closed entity by entity. |
| Exceptions | none |
| Engine notes | ERPNext balances each company's entry independently; D365 uses directional legal-entity pairs with due-to and due-from accounts; Oracle balances by legal entity; NetSuite posts to two or more subsidiaries. |
| Evidence | TEN-09, ERP-07, ERP-13, ERP-20, research/design_decision_matrix.md#MT-13, research/industry_best_practices.md#5 |
| Evidence strength | multi_vendor |
| Status | active |
| Decision ref | null |
| Check method | pipeline_test |
| Check description | Confirm each intercompany entry balances per entity and is linked to its counterpart. |
| Lifecycle stage | Data Validation |

#### FIN-048: Elimination location

| Field | Value |
|---|---|
| Statement | Intercompany elimination MAY live in an elimination entity, at report time, at a posting level or by line-level flag. |
| Level | OPTIONAL |
| Scope | OLTP, OLAP |
| Applies when | Consolidated reporting across entities |
| Rationale | Traceability and reporting complexity differ by location, and no source favours one. |
| Exceptions | none |
| Engine notes | D365 uses a separate elimination entity or report-time consolidation; SAP uses posting level 20; NetSuite uses elimination journals with differences to CTA-E. |
| Evidence | ERP-04, ERP-13, ERP-17, research/design_decision_matrix.md#MT-19, research/industry_best_practices.md#5 |
| Evidence strength | multi_vendor |
| Status | active |
| Decision ref | null |
| Check method | manual_review |
| Check description | Record the chosen elimination location and how eliminations are traced. |
| Lifecycle stage | Reporting |

#### FIN-049: Intercompany currency differences

| Field | Value |
|---|---|
| Statement | Currency differences on intercompany balances SHOULD be treated as expected amounts posted to a defined account rather than as errors. |
| Level | RECOMMENDED |
| Scope | OLTP, OLAP |
| Applies when | Intercompany balances across different currencies |
| Rationale | Treating them as errors creates false reconciliation breaks. |
| Exceptions | none |
| Engine notes | NetSuite posts differences to CTA-E; D365 shows originating currency in elimination journals. |
| Evidence | ERP-13, ERP-17, research/design_decision_matrix.md#MT-20, research/industry_best_practices.md#5 |
| Evidence strength | multi_vendor |
| Status | active |
| Decision ref | null |
| Check method | manual_review |
| Check description | Confirm a defined account exists and reconciliation handles differences. |
| Lifecycle stage | Reporting |

#### FIN-050: Consolidation hierarchy

| Field | Value |
|---|---|
| Statement | A multi-entity group SHOULD maintain a consolidation hierarchy that includes elimination entities where they are used. |
| Level | RECOMMENDED |
| Scope | OLTP, OLAP, data_warehouse |
| Applies when | Statutory or consolidated reporting across entities. The rule applies to an analytical store only where consolidation is run there. |
| Rationale | Without a maintained hierarchy, consolidated reports depend on undocumented structure. |
| Exceptions | none |
| Engine notes | D365, NetSuite and SAP each provide a hierarchy or elimination structure. |
| Evidence | TEN-08, TEN-09, ERP-04, ERP-13, ERP-17, research/design_decision_matrix.md#MT-15 |
| Evidence strength | multi_vendor |
| Status | active |
| Decision ref | null |
| Check method | manual_review |
| Check description | Confirm the hierarchy is maintained and used by consolidation. |
| Lifecycle stage | Reporting |

#### FIN-051: Consolidated statements (IFRS parents)

| Field | Value |
|---|---|
| Statement | A parent presenting consolidated statements under IFRS 10 MUST be able to produce them from its group ledgers. |
| Level | MANDATORY |
| Scope | OLTP, OLAP |
| Applies when | Jurisdiction: IFRS adopters. Parents in scope of IFRS 10, at concept level only |
| Rationale | The IFRS 10 summary page says a parent presents consolidated statements. Requires legal review by counsel for the entity concerned before adoption. |
| Exceptions | No exception identified in the sources read. Requires legal review by counsel for the entity concerned before adoption. |
| Engine notes | Summary page only. Elimination paragraphs were not read, and this rule imposes no intragroup elimination method. |
| Evidence | ERP-21, research/design_decision_matrix.md#MT-18 |
| Evidence strength | standard |
| Status | provisional |
| Decision ref | null |
| Check method | manual_review |
| Check description | Confirm consolidated statements can be produced for the parent. |
| Lifecycle stage | Reporting |

### Retention by jurisdiction

#### RET-001: Germany tax records

| Field | Value |
|---|---|
| Statement | German tax records MUST be retained for 10 years for books, records and annual accounts, 8 years for booking vouchers and 6 years for other listed documents, and MUST NOT be disposed of while still relevant to an open assessment. |
| Level | MANDATORY |
| Scope | OLTP, data_warehouse, lakehouse |
| Applies when | Jurisdiction: Germany. Records under AO 147 |
| Rationale | Early disposal breaches the Abgabenordnung, and the period does not run out while documents matter for open assessments. Requires legal review by counsel for the entity concerned before adoption. |
| Exceptions | No exception identified in the sources read. Requires legal review by counsel for the entity concerned before adoption. |
| Engine notes | Periods run from the end of the calendar year of last entry or creation. The transitional provision for the 8-year voucher period was not read; a search snippet says it applies only to vouchers whose period had not ended before 1 January 2025. |
| Evidence | LEG-05, research/design_decision_matrix.md#LG-16, research/database_security_standards.md#12.6 |
| Evidence strength | standard |
| Status | provisional |
| Decision ref | null |
| Check method | manual_review |
| Check description | Check the retention schedule against AO 147 and confirm disposal checks open assessments. |
| Lifecycle stage | Governance |

#### RET-002: Germany VAT invoices

| Field | Value |
|---|---|
| Statement | German invoice copies issued and invoices received MUST be retained for 8 years from the end of the calendar year of issue. |
| Level | MANDATORY |
| Scope | OLTP, data_warehouse, lakehouse |
| Applies when | Jurisdiction: Germany. Invoices under UStG 14b |
| Rationale | Early disposal breaches UStG 14b. Requires legal review by counsel for the entity concerned before adoption. |
| Exceptions | No exception identified in the sources read. Requires legal review by counsel for the entity concerned before adoption. |
| Engine notes | none |
| Evidence | LEG-04, research/design_decision_matrix.md#LG-16, research/database_security_standards.md#12.6 |
| Evidence strength | standard |
| Status | provisional |
| Decision ref | null |
| Check method | manual_review |
| Check description | Check the schedule entry for German VAT invoices. |
| Lifecycle stage | Governance |

#### RET-003: Germany commercial records

| Field | Value |
|---|---|
| Statement | German commercial records MUST be retained for 10 years for books, 8 years for booking vouchers and 6 years for other documents. |
| Level | MANDATORY |
| Scope | OLTP, data_warehouse, lakehouse |
| Applies when | Jurisdiction: Germany. Records under HGB 257 |
| Rationale | Early disposal breaches the Handelsgesetzbuch. Requires legal review by counsel for the entity concerned before adoption. |
| Exceptions | Institutions under KWG and listed categories keep booking vouchers for 10 years. Requires legal review by counsel for the entity concerned before adoption. |
| Engine notes | Periods run from the end of the calendar year. |
| Evidence | LEG-05, ERP-23, research/design_decision_matrix.md#LG-16, research/database_security_standards.md#12.6 |
| Evidence strength | standard |
| Status | provisional |
| Decision ref | null |
| Check method | manual_review |
| Check description | Check the schedule entry for German commercial records. |
| Lifecycle stage | Governance |

#### RET-004: Germany post-migration carrier

| Field | Value |
|---|---|
| Statement | After a system change, German tax data MUST NOT be held only on a machine-readable carrier until the fifth following calendar year has ended. |
| Level | MANDATORY |
| Scope | OLTP, data_warehouse, lakehouse |
| Applies when | Jurisdiction: Germany. Data subject to AO 147 after a system change |
| Rationale | Moving to a carrier too early can breach data access duties. Requires legal review by counsel for the entity concerned before adoption. |
| Exceptions | No exception identified in the sources read. Requires legal review by counsel for the entity concerned before adoption. |
| Engine notes | Known through note 19's summary of section 147; check wording during legal review. |
| Evidence | LEG-05, research/design_decision_matrix.md#LG-16, research/database_security_standards.md#12.6 |
| Evidence strength | standard |
| Status | provisional |
| Decision ref | null |
| Check method | manual_review |
| Check description | Confirm archive plans for retired systems follow this timing. |
| Lifecycle stage | Governance |

#### RET-005: France tax records

| Field | Value |
|---|---|
| Statement | French tax books, records and documents MUST be retained for 6 years from the date of the last transaction or document. |
| Level | MANDATORY |
| Scope | OLTP, data_warehouse, lakehouse |
| Applies when | Jurisdiction: France. Records under LPF L102 B |
| Rationale | Early disposal breaches French tax procedure law. Requires legal review by counsel for the entity concerned before adoption. |
| Exceptions | No exception identified in the sources read. Requires legal review by counsel for the entity concerned before adoption. |
| Engine notes | The BOFiP version read was in force from 2013-10-18 to 2014-05-28 and may have been replaced. |
| Evidence | LEG-09, research/design_decision_matrix.md#LG-17, research/database_security_standards.md#12.6 |
| Evidence strength | standard |
| Status | provisional |
| Decision ref | B9 |
| Check method | manual_review |
| Check description | Check the schedule entry for French tax records against the current BOFiP. |
| Lifecycle stage | Governance |

#### RET-006: France commercial period (unverified)

| Field | Value |
|---|---|
| Statement | The retention period for French commercial accounting documents MAY be configured only after counsel confirms it; no value set, and planning assumes the longer of the tax and commercial periods. |
| Level | OPTIONAL |
| Scope | OLTP, data_warehouse, lakehouse |
| Applies when | Jurisdiction: France. Accounting documents under the Code de commerce |
| Rationale | The 10-year period rests on a search snippet and a CNIL billing reference, and Code de commerce L123-22 was not opened. Requires legal review by counsel for the entity concerned before adoption. |
| Exceptions | Counsel must confirm the period before configuration. Requires legal review by counsel for the entity concerned before adoption. |
| Engine notes | A search snippet says BOFiP treats the tax provisions as independent of L123-22. The longer period applying where both apply is an inference. |
| Evidence | LEG-36, research/design_decision_matrix.md#LG-17, research/database_security_standards.md#12.6 |
| Evidence strength | inference |
| Status | provisional |
| Decision ref | B9 |
| Check method | manual_review |
| Check description | Confirm counsel has confirmed the period before configuration. |
| Lifecycle stage | Governance |

#### RET-007: UK VAT records

| Field | Value |
|---|---|
| Statement | Business records for UK VAT MUST be retained for at least 6 years. |
| Level | MANDATORY |
| Scope | OLTP, data_warehouse, lakehouse |
| Applies when | Jurisdiction: United Kingdom. Records for VAT under Notice 700/21 |
| Rationale | Early disposal breaches HMRC record-keeping requirements. Requires legal review by counsel for the entity concerned before adoption. |
| Exceptions | HMRC may allow a shorter period for some records on request. Other taxes may need longer. Requires legal review by counsel for the entity concerned before adoption. |
| Engine notes | none |
| Evidence | LEG-13, research/design_decision_matrix.md#LG-18, research/database_security_standards.md#12.6 |
| Evidence strength | standard |
| Status | provisional |
| Decision ref | null |
| Check method | manual_review |
| Check description | Check the schedule entry for UK VAT records. |
| Lifecycle stage | Governance |

#### RET-008: UK Companies Act records

| Field | Value |
|---|---|
| Statement | UK accounting records MUST be preserved for 3 years for private companies and 6 years for public companies from the date they are made. |
| Level | MANDATORY |
| Scope | OLTP, data_warehouse, lakehouse |
| Applies when | Jurisdiction: United Kingdom. Companies under Companies Act 2006 s388(4) |
| Rationale | Early disposal breaches the Companies Act. Requires legal review by counsel for the entity concerned before adoption. |
| Exceptions | No exception identified in the sources read. Requires legal review by counsel for the entity concerned before adoption. |
| Engine notes | This period differs from the VAT period, and both can apply to one record set. |
| Evidence | LEG-15, research/design_decision_matrix.md#LG-18, research/database_security_standards.md#12.6 |
| Evidence strength | standard |
| Status | provisional |
| Decision ref | null |
| Check method | manual_review |
| Check description | Check the schedule entry for UK company accounting records. |
| Lifecycle stage | Governance |

#### RET-009: US IRS records

| Field | Value |
|---|---|
| Statement | US federal tax records SHOULD be retained on limitation-driven periods as described by the IRS rather than one flat period. |
| Level | RECOMMENDED |
| Scope | OLTP, data_warehouse, lakehouse |
| Applies when | Jurisdiction: United States. Federal income and employment tax records |
| Rationale | IRS periods are limitation-driven, and a flat period can be too short for some cases. Requires legal review by counsel for the entity concerned before adoption. |
| Exceptions | No exception identified in the sources read. Requires legal review by counsel for the entity concerned before adoption. Note 19 labelled this MANDATORY; the matrix holds it RECOMMENDED because no statute was read. |
| Engine notes | IRS page: 3 years generally; 3 from filing or 2 from payment for refund claims; 7 for worthless securities or bad debt; 6 if income is under-reported by more than 25 percent; indefinitely if no return or a fraudulent return; employment tax at least 4 years. |
| Evidence | LEG-16, research/design_decision_matrix.md#LG-19, research/database_security_standards.md#12.6 |
| Evidence strength | standard |
| Status | provisional |
| Decision ref | null |
| Check method | manual_review |
| Check description | Check the schedule includes the limitation cases and the employment-tax period. |
| Lifecycle stage | Governance |

#### RET-010: US broker-dealer records

| Field | Value |
|---|---|
| Statement | US broker-dealers MUST preserve the records listed in 17 CFR 240.17a-4 for the stated periods and in a system that keeps a complete time-stamped audit trail or a non-rewriteable, non-erasable format. |
| Level | MANDATORY |
| Scope | OLTP, data_warehouse, lakehouse |
| Applies when | Jurisdiction: United States. Broker-dealers only; it must not be applied to general SaaS |
| Rationale | This is a specific SEC requirement for broker-dealers. Requires legal review by counsel for the entity concerned before adoption. |
| Exceptions | No exception identified in the sources read. Requires legal review by counsel for the entity concerned before adoption. |
| Engine notes | 17a-4(a) records 6 years, first 2 easily accessible; 17a-4(b) records 3 years, first 2 easily accessible; 17a-4(c) account opening and terms records 6 years after account closing. |
| Evidence | LEG-17, research/design_decision_matrix.md#LG-24, research/database_security_standards.md#12.6 |
| Evidence strength | standard |
| Status | provisional |
| Decision ref | null |
| Check method | manual_review |
| Check description | For broker-dealers only, confirm the storage mode and schedule against the rule. |
| Lifecycle stage | Governance |

#### RET-011: Pakistan sales tax records

| Field | Value |
|---|---|
| Statement | Pakistani sales tax records and documents MUST be retained for 6 years after the end of the tax period or until any proceedings are finally decided. |
| Level | MANDATORY |
| Scope | OLTP, data_warehouse, lakehouse |
| Applies when | Jurisdiction: Pakistan. Registered persons under Sales Tax Act 1990 s24 |
| Rationale | Early disposal breaches the Sales Tax Act. Requires legal review by counsel for the entity concerned before adoption. |
| Exceptions | No exception identified in the sources read. Requires legal review by counsel for the entity concerned before adoption. |
| Engine notes | Consolidated text read; check the gazette for the legal citation. |
| Evidence | LEG-18, research/design_decision_matrix.md#LG-20, research/database_security_standards.md#12.6 |
| Evidence strength | standard |
| Status | provisional |
| Decision ref | null |
| Check method | manual_review |
| Check description | Check the schedule entry and that disposal checks open proceedings. |
| Lifecycle stage | Governance |

#### RET-012: Pakistan e-invoice records

| Field | Value |
|---|---|
| Statement | Real-time e-invoices and debit and credit notes of FBR-integrated persons MUST be retained on electronic media for 6 years. |
| Level | MANDATORY |
| Scope | OLTP, data_warehouse, lakehouse |
| Applies when | Jurisdiction: Pakistan. Integrated persons notified by FBR under Sales Tax Rules 2006, Rule 150S |
| Rationale | Early disposal breaches the Sales Tax Rules. Requires legal review by counsel for the entity concerned before adoption. |
| Exceptions | No exception identified in the sources read. Requires legal review by counsel for the entity concerned before adoption. |
| Engine notes | Start dates for integration conflict in the sources: a reported SRO table and FBR's FAQ differ, and an extension notice was not opened. |
| Evidence | LEG-19, research/design_decision_matrix.md#LG-20, research/database_security_standards.md#12.6 |
| Evidence strength | standard |
| Status | provisional |
| Decision ref | null |
| Check method | manual_review |
| Check description | Check the schedule entry for integrated persons. |
| Lifecycle stage | Governance |

#### RET-013: Pakistan income tax records

| Field | Value |
|---|---|
| Statement | Pakistani income tax accounts and documents MUST be retained for 6 years after the end of the tax year or until proceedings end. |
| Level | MANDATORY |
| Scope | OLTP, data_warehouse, lakehouse |
| Applies when | Jurisdiction: Pakistan. Persons under Income Tax Ordinance 2001 s174(3) |
| Rationale | Early disposal breaches the Ordinance. Requires legal review by counsel for the entity concerned before adoption. |
| Exceptions | The final proviso removes the limit for records relating to matters under clause (ii) of s111(2). Requires legal review by counsel for the entity concerned before adoption. |
| Engine notes | The proviso means some records have no end date; legal review needed. |
| Evidence | LEG-20, research/design_decision_matrix.md#LG-20, research/database_security_standards.md#12.6 |
| Evidence strength | standard |
| Status | provisional |
| Decision ref | null |
| Check method | manual_review |
| Check description | Check the schedule entry and the treatment of records under the proviso. |
| Lifecycle stage | Governance |

#### RET-014: Pakistan company books

| Field | Value |
|---|---|
| Statement | Pakistani company books of account with vouchers MUST be retained for not less than the ten financial years preceding a financial year. |
| Level | MANDATORY |
| Scope | OLTP, data_warehouse, lakehouse |
| Applies when | Jurisdiction: Pakistan. Companies under Companies Act 2017 s220(5) |
| Rationale | Early disposal breaches the Companies Act. Requires legal review by counsel for the entity concerned before adoption. |
| Exceptions | No exception identified in the sources read. Requires legal review by counsel for the entity concerned before adoption. |
| Engine notes | Rules for resolutions were read without confirming section numbers and are not ruled here. |
| Evidence | LEG-21, research/design_decision_matrix.md#LG-20, research/database_security_standards.md#12.6 |
| Evidence strength | standard |
| Status | provisional |
| Decision ref | null |
| Check method | manual_review |
| Check description | Check the schedule entry for Pakistani company books. |
| Lifecycle stage | Governance |

#### RET-015: UAE tax records

| Field | Value |
|---|---|
| Statement | UAE tax records MUST be retained for 5 years, real estate records for 7 years, and the listed extensions for disputes, audits and voluntary disclosure MUST be applied. |
| Level | MANDATORY |
| Scope | OLTP, data_warehouse, lakehouse |
| Applies when | Jurisdiction: United Arab Emirates. Persons under Cabinet Decision 74 of 2023, Article 3 |
| Rationale | Early disposal breaches UAE tax procedure rules. Requires legal review by counsel for the entity concerned before adoption. |
| Exceptions | No exception identified in the sources read. Requires legal review by counsel for the entity concerned before adoption. |
| Engine notes | Extensions: 4 more years for disputes (or until settled, whichever is later), audits or audit notice; 1 year for voluntary disclosure in the fifth year. |
| Evidence | LEG-23, research/design_decision_matrix.md#LG-21, research/database_security_standards.md#12.6 |
| Evidence strength | standard |
| Status | provisional |
| Decision ref | null |
| Check method | manual_review |
| Check description | Check the schedule includes the periods and extension triggers. |
| Lifecycle stage | Governance |

#### RET-016: UAE e-invoice data

| Field | Value |
|---|---|
| Statement | UAE e-invoice issue, transmission and receipt data MUST be retained for the same periods in a system that preserves its integrity. |
| Level | MANDATORY |
| Scope | OLTP, data_warehouse, lakehouse |
| Applies when | Jurisdiction: United Arab Emirates. E-invoicing under Guidelines V2.0 section 5.4 |
| Rationale | E-invoicing guidance applies the tax retention periods to this data. Requires legal review by counsel for the entity concerned before adoption. |
| Exceptions | No exception identified in the sources read. Requires legal review by counsel for the entity concerned before adoption. |
| Engine notes | none |
| Evidence | LEG-24, research/design_decision_matrix.md#LG-21, research/database_security_standards.md#12.6 |
| Evidence strength | standard |
| Status | provisional |
| Decision ref | null |
| Check method | manual_review |
| Check description | Check that e-invoice data is under the retention schedule and integrity control. |
| Lifecycle stage | Governance |

#### RET-017: Saudi Arabia VAT records

| Field | Value |
|---|---|
| Statement | Saudi VAT records MUST be retained for at least 6 years, movable capital assets for the adjustment period plus 5 years and real estate for at least 15 years. |
| Level | MANDATORY |
| Scope | OLTP, data_warehouse, lakehouse |
| Applies when | Jurisdiction: Saudi Arabia. KSA VAT scope, ZATCA guide 8.3.3 |
| Rationale | Early disposal breaches ZATCA requirements. Requires legal review by counsel for the entity concerned before adoption. |
| Exceptions | No exception identified in the sources read. Requires legal review by counsel for the entity concerned before adoption. |
| Engine notes | none |
| Evidence | LEG-25, research/design_decision_matrix.md#LG-22, research/database_security_standards.md#12.6 |
| Evidence strength | standard |
| Status | provisional |
| Decision ref | null |
| Check method | manual_review |
| Check description | Check the schedule entry for KSA VAT records. |
| Lifecycle stage | Governance |

#### RET-018: Saudi Arabia location and language

| Field | Value |
|---|---|
| Statement | Saudi VAT records MUST be retained within the Kingdom and in the Arabic language. |
| Level | MANDATORY |
| Scope | OLTP, data_warehouse, lakehouse |
| Applies when | Jurisdiction: Saudi Arabia. KSA VAT scope |
| Rationale | ZATCA requires both, which affects where systems and archives may run. Requires legal review by counsel for the entity concerned before adoption. |
| Exceptions | Workstation exception for permanent establishments with centralised systems abroad. Requires legal review by counsel for the entity concerned before adoption. |
| Engine notes | A SaaS deployment must check data location for this scope. |
| Evidence | LEG-25, research/design_decision_matrix.md#LG-22, research/database_security_standards.md#12.6 |
| Evidence strength | standard |
| Status | provisional |
| Decision ref | null |
| Check method | manual_review |
| Check description | Confirm data location and language for KSA VAT records. |
| Lifecycle stage | Governance |

#### RET-019: EU invoice integrity

| Field | Value |
|---|---|
| Statement | EU invoices MUST have ensured authenticity of origin, integrity of content and legibility from issue until the end of the storage period. |
| Level | MANDATORY |
| Scope | OLTP, data_warehouse, lakehouse |
| Applies when | Jurisdiction: European Union. VAT-registered suppliers under VAT Directive Article 233(1) |
| Rationale | The Directive makes this a storage duty, while Article 247 leaves the period to Member States. Requires legal review by counsel for the entity concerned before adoption. |
| Exceptions | No exception identified in the sources read. Requires legal review by counsel for the entity concerned before adoption. |
| Engine notes | Article 233 allows business controls or other means. No period is set at EU level; Italian and Spanish periods were not researched in depth. |
| Evidence | LEG-01, research/design_decision_matrix.md#LG-11, research/database_security_standards.md#12.6 |
| Evidence strength | standard |
| Status | provisional |
| Decision ref | null |
| Check method | manual_review |
| Check description | Confirm stored invoices have integrity and legibility controls for the whole storage period. |
| Lifecycle stage | Governance |

#### RET-020: Card authentication data

| Field | Value |
|---|---|
| Statement | Sensitive card authentication data MUST NOT be retained after authorization, even if encrypted. |
| Level | MANDATORY |
| Scope | OLTP, data_warehouse, lakehouse |
| Applies when | Scope: PCI DSS cardholder data environments (contractual standard, not a statute) |
| Rationale | PCI DSS 3.3.1 forbids it. Requires legal review by counsel for the entity concerned before adoption. |
| Exceptions | No exception identified in the sources read. Requires legal review by counsel for the entity concerned before adoption. |
| Engine notes | Read through the v4.0 SAQ D; v4.0.1 text was not read. Coverage of logs and backups is an inference. LEG-31 was read only through a summarising fetch tool; [WF] re-check. |
| Evidence | SEC-17, LEG-30, LEG-31, research/design_decision_matrix.md#LG-25 |
| Evidence strength | standard |
| Status | provisional |
| Decision ref | null |
| Check method | manual_review |
| Check description | Scan schemas, logs and backups for stored authentication data. |
| Lifecycle stage | Governance |

### Retention controls

#### RET-021: Retention schedule keyed

| Field | Value |
|---|---|
| Statement | A retention schedule SHOULD be keyed by record class, jurisdiction, start event and legal hold. |
| Level | RECOMMENDED |
| Scope | OLTP, data_warehouse, lakehouse |
| Applies when | Jurisdiction-scoped retention obligations apply; the jurisdictions are those in RET-001 to RET-020 |
| Rationale | A single flat period over- or under-retains, because periods differ by class, start event and jurisdiction. Requires legal review by counsel for the entity concerned before adoption. |
| Exceptions | No exception identified in the sources read. Requires legal review by counsel for the entity concerned before adoption. |
| Engine notes | Design inference. Where more than one period applies to a record, the longer applying is also an inference. |
| Evidence | LEG-05, LEG-18, LEG-20, LEG-23, research/design_decision_matrix.md#LG-23 |
| Evidence strength | inference |
| Status | provisional |
| Decision ref | null |
| Check method | catalog_query |
| Check description | Check every governed record class has jurisdiction, period, start event and hold status. |
| Lifecycle stage | Governance |

#### RET-022: Legal hold suspends disposal

| Field | Value |
|---|---|
| Statement | A legal hold SHOULD suspend disposal and purge of the records it covers, and disposal SHOULD check open matters as well as the retention date. |
| Level | RECOMMENDED |
| Scope | OLTP, data_warehouse, lakehouse |
| Applies when | Jurisdiction-scoped: mandatory in substance in Germany, UAE and Pakistan by RET-001, RET-011, RET-013 and RET-015; elsewhere a recommended control |
| Rationale | Date-only disposal can destroy records still needed for open assessments or proceedings. Requires legal review by counsel for the entity concerned before adoption. |
| Exceptions | No exception identified in the sources read. Requires legal review by counsel for the entity concerned before adoption. |
| Engine notes | Inference from the statutes on extensions, including AO 147(3). No source covers database legal-hold mechanics, so none are specified. SOX 18 USC 1519 is an intent-based offence and not a retention schedule; when a matter is pending, counsel decides. |
| Evidence | LEG-05, LEG-18, LEG-20, LEG-23, research/design_decision_matrix.md#LG-23, research/database_security_standards.md#12.6, research/database_security_standards.md#12.4 |
| Evidence strength | inference |
| Status | provisional |
| Decision ref | null |
| Check method | pipeline_test |
| Check description | Attempt disposal of a held record and confirm the block. |
| Lifecycle stage | Governance |

#### RET-031: PCI audit log retention

| Field | Value |
|---|---|
| Statement | Audit log history in PCI DSS scope MUST be retained for at least 12 months with at least the most recent three months immediately available for analysis. |
| Level | MANDATORY |
| Scope | all |
| Applies when | Scope: PCI DSS cardholder data environments (contractual standard, not a statute) |
| Rationale | PCI DSS 10.5.1 sets this period for audit logs. Requires legal review by counsel for the entity concerned before adoption. |
| Exceptions | No exception identified in the sources read. Requires legal review by counsel for the entity concerned before adoption. |
| Engine notes | Wording is from v4.0 SAQ D; v4.0.1 text was not read. This is not a retention basis for other cardholder data. |
| Evidence | SEC-17, LEG-30, research/design_decision_matrix.md#AH-5, research/database_security_standards.md#12.3 |
| Evidence strength | standard |
| Status | provisional |
| Decision ref | null |
| Check method | manual_review |
| Check description | Confirm log retention and immediate availability for in-scope systems. |
| Lifecycle stage | Governance |

#### RET-032: FDA Part 11 audit trail retention

| Field | Value |
|---|---|
| Statement | Audit trail documentation for electronic records under 21 CFR Part 11 MUST be retained at least as long as the subject record. |
| Level | MANDATORY |
| Scope | OLTP |
| Applies when | Jurisdiction: United States. FDA-regulated electronic records under 21 CFR 11.10(e) only |
| Rationale | Part 11 ties trail retention to the record. It does not apply to financial records as such. Requires legal review by counsel for the entity concerned before adoption. |
| Exceptions | No exception identified in the sources read. Requires legal review by counsel for the entity concerned before adoption. |
| Engine notes | none |
| Evidence | TEN-17, research/design_decision_matrix.md#AH-4, research/database_security_standards.md#12.3 |
| Evidence strength | standard |
| Status | provisional |
| Decision ref | null |
| Check method | manual_review |
| Check description | For FDA-regulated records only, confirm trail retention matches the subject record. |
| Lifecycle stage | Governance |

#### RET-033: Audit log retention period defined

| Field | Value |
|---|---|
| Statement | Each audit log class outside a scope with a stated period SHOULD have a retention period defined by the organization and recorded in the retention schedule. |
| Level | RECOMMENDED |
| Scope | all |
| Applies when | Audit records not covered by RET-031 or RET-032 |
| Rationale | With no stated period, logs are either destroyed early or kept indefinitely. |
| Exceptions | none |
| Engine notes | NIST SP 800-53 AU-11 leaves the period organization-defined. This standard gives no number because no source supports a general period. |
| Evidence | SEC-08, research/database_security_standards.md#12.3 |
| Evidence strength | standard |
| Status | active |
| Decision ref | null |
| Check method | catalog_query |
| Check description | Check every audit log class has a recorded retention period and basis. |
| Lifecycle stage | Governance |

#### RET-034: Retention schedule with basis (GDPR, Part 11)

| Field | Value |
|---|---|
| Statement | A retention schedule per record class with its legal basis documented MUST exist for personal data in GDPR scope and for records in 21 CFR Part 11 scope. |
| Level | MANDATORY |
| Scope | all |
| Applies when | Jurisdiction: European Union (GDPR Articles 5(1)(e), 5(2) and 30) and United States (FDA records under 21 CFR Part 11) |
| Rationale | Undocumented retention cannot be justified to a regulator. Requires legal review by counsel for the entity concerned before adoption. |
| Exceptions | No exception identified in the sources read. Requires legal review by counsel for the entity concerned before adoption. |
| Engine notes | Outside these scopes the schedule is RECOMMENDED under RET-021. GDPR sets no fixed period, so a fixed period is not automatically lawful. |
| Evidence | TEN-34, TEN-17, LEG-03, research/design_decision_matrix.md#AH-13, research/database_security_standards.md#12.4 |
| Evidence strength | standard |
| Status | provisional |
| Decision ref | null |
| Check method | catalog_query |
| Check description | Check that in-scope record classes have a schedule entry with a basis. |
| Lifecycle stage | Governance |

### Erasure

#### RET-023: California deletion chain

| Field | Value |
|---|---|
| Statement | A business in CCPA scope MUST delete personal information on a consumer deletion request and MUST notify service providers, contractors and third parties as the statute requires. |
| Level | MANDATORY |
| Scope | all |
| Applies when | Jurisdiction: California. Businesses in CCPA scope, Civil Code 1798.105(c) and (d) |
| Rationale | Failure to delete or propagate breaches the statute. Requires legal review by counsel for the entity concerned before adoption. |
| Exceptions | No exception identified in the sources read. Requires legal review by counsel for the entity concerned before adoption. |
| Engine notes | Read from the CPPA copy; statute changes after 2025-01 were not checked. |
| Evidence | LEG-28, research/design_decision_matrix.md#LG-27, research/database_security_standards.md#12.7 |
| Evidence strength | standard |
| Status | provisional |
| Decision ref | null |
| Check method | manual_review |
| Check description | Confirm the deletion workflow reaches each downstream recipient. |
| Lifecycle stage | Governance |

#### RET-024: California backups

| Field | Value |
|---|---|
| Statement | A business in CCPA scope MUST apply deletion on archived or backup systems, at the latest on restore or next access or use, having delayed only as regulation section 7022 permits. |
| Level | MANDATORY |
| Scope | all |
| Applies when | Jurisdiction: California. Businesses, service providers and contractors in CCPA scope, regulation section 7022 |
| Rationale | Delay ends on restore or next access or use for sale, disclosure or commercial purpose. Requires legal review by counsel for the entity concerned before adoption. |
| Exceptions | No exception identified in the sources read. Requires legal review by counsel for the entity concerned before adoption. |
| Engine notes | The file name at the URL suggests a statute, but it held the Regulations when read. |
| Evidence | LEG-29, research/design_decision_matrix.md#LG-27, research/database_security_standards.md#12.7 |
| Evidence strength | standard |
| Status | provisional |
| Decision ref | null |
| Check method | pipeline_test |
| Check description | Restore a test backup and confirm deletion is re-applied before use. |
| Lifecycle stage | Governance |

#### RET-025: Erasure register outside backups

| Field | Value |
|---|---|
| Statement | Erasure requests SHOULD be recorded durably outside the backups and re-applied after any restore. |
| Level | RECOMMENDED |
| Scope | all |
| Applies when | Jurisdiction: European Union and United Kingdom personal data, and CCPA scope as a supporting practice |
| Rationale | If backups cannot be edited, restored data would otherwise reappear with erased data intact. Requires legal review by counsel for the entity concerned before adoption. |
| Exceptions | No exception identified in the sources read. Requires legal review by counsel for the entity concerned before adoption. |
| Engine notes | Common element in EDPB, Dutch AP and California text. ICO and AP were read from Wayback captures because live sites refused access; confirm on the live site. |
| Evidence | LEG-29, LEG-32, LEG-33, LEG-35, research/design_decision_matrix.md#LG-28, research/database_security_standards.md#12.7 |
| Evidence strength | standard |
| Status | provisional |
| Decision ref | B8 |
| Check method | pipeline_test |
| Check description | Restore a test backup and confirm register entries are re-applied. |
| Lifecycle stage | Governance |

#### RET-026: Backup erasure timing

| Field | Value |
|---|---|
| Statement | Backups in EU or UK scope SHOULD put erased data beyond use, with a durable erasure register, erasure re-applied on restore and a defined backup expiry. |
| Level | RECOMMENDED |
| Scope | all |
| Applies when | Jurisdiction: European Union and United Kingdom personal data in backups |
| Rationale | How long undue delay runs for backups is unsettled, and the EDPB itself lists it for possible guidance. Requires legal review by counsel for the entity concerned before adoption. |
| Exceptions | Counsel must confirm the position before reliance. Requires legal review by counsel for the entity concerned before adoption. |
| Engine notes | ICO uses a beyond-use approach. California permits delay until restore or next use. The Dutch AP expects records and erasure on restore. One authority found incremental deletion over long periods made undue delay hard to establish. ICO and AP are Wayback captures; confirm on the live site. |
| Evidence | LEG-29, LEG-32, LEG-33, LEG-35, research/design_decision_matrix.md#LG-28, research/database_security_standards.md#12.7 |
| Evidence strength | standard |
| Status | provisional |
| Decision ref | B8, B7 |
| Check method | manual_review |
| Check description | Confirm counsel's position and that backup handling follows it. |
| Lifecycle stage | Governance |

#### RET-027: Predictable backup retention

| Field | Value |
|---|---|
| Statement | Backup retention SHOULD be defined so that data expiry is predictable. |
| Level | RECOMMENDED |
| Scope | all |
| Applies when | Jurisdiction: European Union and United Kingdom personal data |
| Rationale | Unbounded backups keep personal data indefinitely. EDPB material shows retention alone is not always seen as adequate. Requires legal review by counsel for the entity concerned before adoption. |
| Exceptions | No exception identified in the sources read. Requires legal review by counsel for the entity concerned before adoption. |
| Engine notes | Based on EDPB and ICO material; ICO needs confirmation on the live site. |
| Evidence | LEG-32, LEG-33, research/database_security_standards.md#12.7 |
| Evidence strength | standard |
| Status | provisional |
| Decision ref | B8 |
| Check method | manual_review |
| Check description | Confirm backup retention periods exist and are documented. |
| Lifecycle stage | Governance |

#### RET-028: Field-level treatment

| Field | Value |
|---|---|
| Statement | Where erasure is limited by a legal obligation to retain a record, only the fields under that obligation SHOULD be retained. |
| Level | RECOMMENDED |
| Scope | OLTP, data_warehouse, lakehouse |
| Applies when | Jurisdiction: European Union. GDPR Article 17(3) applies to the record |
| Rationale | Article 17(3) applies only to the extent necessary, so keeping the whole record can over-retain. Which fields is a legal judgment. Requires legal review by counsel for the entity concerned before adoption. |
| Exceptions | No exception identified in the sources read. Requires legal review by counsel for the entity concerned before adoption. |
| Engine notes | Design is an inference. |
| Evidence | LEG-03, research/design_decision_matrix.md#LG-29 |
| Evidence strength | standard |
| Status | provisional |
| Decision ref | null |
| Check method | manual_review |
| Check description | Confirm a field-level retention basis is recorded for retained records. |
| Lifecycle stage | Governance |

#### RET-029: Erasure verified and demonstrable

| Field | Value |
|---|---|
| Statement | Erasure SHOULD be verified and the controller SHOULD be able to demonstrate it was carried out. |
| Level | RECOMMENDED |
| Scope | all |
| Applies when | Jurisdiction: European Union personal data, from an EDPB report |
| Rationale | An unverified deletion cannot be evidenced to a regulator. The EDPB report is a regulator report and not a legal text. Requires legal review by counsel for the entity concerned before adoption. |
| Exceptions | No exception identified in the sources read. Requires legal review by counsel for the entity concerned before adoption. |
| Engine notes | The report also notes replacing personal data with random strings and tools that move data out of reach. |
| Evidence | LEG-32, research/design_decision_matrix.md#LG-30, research/database_security_standards.md#12.7 |
| Evidence strength | standard |
| Status | provisional |
| Decision ref | null |
| Check method | manual_review |
| Check description | Confirm erasure evidence exists for a sampled request. |
| Lifecycle stage | Governance |

#### RET-030: Key destruction

| Field | Value |
|---|---|
| Statement | Key destruction MAY be used to reduce exposure in backups, event logs and immutable stores where the preconditions in the engine notes are met, and MAY be treated as erasure only if counsel accepts it. |
| Level | OPTIONAL |
| Scope | all |
| Applies when | Jurisdiction: any regime where erasure is claimed; no regulator text read accepts it |
| Rationale | Encrypted personal data remains personal data, and key destruction is a limited technical effect. Requires legal review by counsel for the entity concerned before adoption. |
| Exceptions | Requires legal review by counsel for the entity concerned before adoption. |
| Engine notes | Preconditions: data encrypted before first write everywhere it lands, governed key backups and escrow, destruction recorded, remaining plaintext assessed, and cryptographic strength over the retention horizon considered. SP 800-88 addresses media sanitization and not legal erasure. LEG-34 is a consultation version on blockchain and not a ruling. OWASP's advice to retain old keys for backups works against this. |
| Evidence | LEG-34, SEC-04, SEC-11, SEC-12, research/design_decision_matrix.md#LG-26, research/database_security_standards.md#12.5 |
| Evidence strength | inference |
| Status | provisional |
| Decision ref | null |
| Check method | manual_review |
| Check description | Confirm preconditions and counsel's position before any claim of erasure by key destruction. |
| Lifecycle stage | Governance |

#### RET-035: Erasure without undue delay (GDPR)

| Field | Value |
|---|---|
| Statement | Applicable GDPR erasure requests MUST be honoured without undue delay unless an Article 17(3) exception applies. |
| Level | MANDATORY |
| Scope | all |
| Applies when | Jurisdiction: European Union. Personal data under GDPR Article 17 |
| Rationale | Article 17 makes this a duty of the controller. Requires legal review by counsel for the entity concerned before adoption. |
| Exceptions | No exception identified in the sources read. Requires legal review by counsel for the entity concerned before adoption. |
| Engine notes | How long undue delay runs for backups is unsettled; see RET-026. |
| Evidence | LEG-03, SEC-15, research/database_security_standards.md#12.4 |
| Evidence strength | standard |
| Status | provisional |
| Decision ref | null |
| Check method | manual_review |
| Check description | Sample erasure requests and confirm timely completion or a recorded exception. |
| Lifecycle stage | Governance |

#### RET-036: Retention exception limits (GDPR)

| Field | Value |
|---|---|
| Statement | Personal data kept under a GDPR Article 17(3) exception MUST be kept only to the extent necessary and the basis MUST be recorded. |
| Level | MANDATORY |
| Scope | all |
| Applies when | Jurisdiction: European Union. GDPR Article 17(3)(b) and (e) |
| Rationale | Article 17(3)(b) refers to Union or Member State law, so SOX and PCI DSS retention do not obviously displace erasure for EU data subjects. Requires legal review by counsel for the entity concerned before adoption. |
| Exceptions | No exception identified in the sources read. Requires legal review by counsel for the entity concerned before adoption. |
| Engine notes | Whether legal claims or another basis applies is fact-specific and for counsel. CCPA has its own exceptions in 1798.105(d). |
| Evidence | LEG-03, SEC-15, TEN-34, research/design_decision_matrix.md#AH-15, research/database_security_standards.md#13 |
| Evidence strength | standard |
| Status | provisional |
| Decision ref | null |
| Check method | manual_review |
| Check description | Confirm each retained class under an exception has a recorded basis and extent. |
| Lifecycle stage | Governance |

#### RET-037: Deletion flag is not erasure

| Field | Value |
|---|---|
| Statement | A deleted flag, or a move to an archive, SHOULD NOT be recorded as fulfilling an erasure duty until the data is purged or anonymized. |
| Level | RECOMMENDED |
| Scope | all |
| Applies when | Jurisdiction: European Union personal data where an erasure duty applies, and other regimes on counsel's advice |
| Rationale | A flag leaves identifiable data in place. No regulator text read addresses soft deletion by name, so this is an inference. Requires legal review by counsel for the entity concerned before adoption. |
| Exceptions | No exception identified in the sources read. Requires legal review by counsel for the entity concerned before adoption. |
| Engine notes | Deletion-state design belongs to AUD-025; this rule covers only the erasure effect. A Recital 26 anonymization requires that the person is no longer identifiable, and overwriting a name alone may not achieve that. |
| Evidence | LEG-03, TEN-30, TEN-31, research/design_decision_matrix.md#AH-12, research/database_security_standards.md#12.1, research/database_security_standards.md#13 |
| Evidence strength | inference |
| Status | provisional |
| Decision ref | A15 |
| Check method | manual_review |
| Check description | Confirm erasure is only marked complete after purge or anonymization. |
| Lifecycle stage | Governance |

#### RET-038: Erasure reach

| Field | Value |
|---|---|
| Statement | Erasure SHOULD reach every store holding the personal data, including archives, history, audit logs as far as they hold identifiable values, indexes, caches, replicas, change streams, warehouses and non-production copies, with backups handled under RET-025 and RET-026. |
| Level | RECOMMENDED |
| Scope | all |
| Applies when | Jurisdiction: European Union personal data where Article 17 applies |
| Rationale | Article 17 applies to the personal data and not to one table, so erasure in only the primary store leaves copies. No source enumerates the stores. Requires legal review by counsel for the entity concerned before adoption. |
| Exceptions | No exception identified in the sources read. Requires legal review by counsel for the entity concerned before adoption. |
| Engine notes | Inference. A deleted-record archive holds whole rows and is in scope. SCD Type 2 dimensions with personal attributes extend the scope. CDC can carry deletes downstream, but applying them is the consumer's responsibility. |
| Evidence | LEG-03, TEN-26, research/database_security_standards.md#12.2, research/database_security_standards.md#12.1 |
| Evidence strength | inference |
| Status | provisional |
| Decision ref | null |
| Check method | manual_review |
| Check description | Trace a sampled erasure through each listed store. |
| Lifecycle stage | Governance |

#### RET-039: Identifiers out of immutable logs

| Field | Value |
|---|---|
| Statement | Immutable logs SHOULD hold stable pseudonymous references rather than identifying values, with the identifying map in a separately controlled store that can be erased. |
| Level | RECOMMENDED |
| Scope | all |
| Applies when | Audit logs, ledgers or history stores that cannot be altered and may hold personal data |
| Rationale | Identifying values written to an immutable store cannot be erased later. Requires legal review, since a log using pseudonyms remains personal data while re-identification is possible. |
| Exceptions | A retention duty or regulator requiring identified entries; the data owner and counsel approve. |
| Engine notes | Inference. Removing the map moves toward anonymity but does not guarantee it, since quasi-identifiers may remain. Row-level redaction in ledger structures was not researched. Sensitive columns in change capture are covered by AUD-010. |
| Evidence | SEC-05, SEC-16, research/database_security_standards.md#13 |
| Evidence strength | inference |
| Status | provisional |
| Decision ref | A16 |
| Check method | manual_review |
| Check description | Sample immutable logs for direct identifiers. |
| Lifecycle stage | Schema Design |

#### RET-040: HIPAA activity log retention (no value set)

| Field | Value |
|---|---|
| Statement | A system holding ePHI SHOULD record counsel's determination of whether its activity logs fall under the six-year documentation retention in 45 CFR 164.316(b)(2)(i); no value set for activity log retention. |
| Level | RECOMMENDED |
| Scope | all |
| Applies when | Jurisdiction: United States. ePHI under HIPAA, for activity logs recorded under AUD-015 |
| Rationale | 45 CFR 164.316(b)(2)(i) sets six years for documentation required by (b)(1), and whether specific audit logs fall in that scope is unresolved. Requires legal review by counsel for the entity concerned before adoption. |
| Exceptions | No exception identified in the sources read. Requires legal review by counsel for the entity concerned before adoption. |
| Engine notes | The six-year period is a floor for required documentation and is not a retention period for ePHI itself. HIPAA final-rule status and application to system activity logs are open research gaps. |
| Evidence | TEN-37, SEC-18, research/database_security_standards.md#12.3, research/design_decision_matrix.md#AH-5 |
| Evidence strength | standard |
| Status | provisional |
| Decision ref | null |
| Check method | manual_review |
| Check description | Confirm the retention schedule records counsel's determination for ePHI activity logs. |
| Lifecycle stage | Governance |

### Numbering by jurisdiction

#### NUM-001: EU sequential invoice number

| Field | Value |
|---|---|
| Statement | EU invoices MUST carry a sequential number, based on one or more series, that uniquely identifies the invoice. |
| Level | MANDATORY |
| Scope | OLTP |
| Applies when | Jurisdiction: European Union. VAT-registered suppliers under VAT Directive Article 226(2) |
| Rationale | An invoice without it is not valid under Article 226. The Article does not say whether sequential excludes gaps. Requires legal review by counsel for the entity concerned before adoption. |
| Exceptions | No exception identified in the sources read. Requires legal review by counsel for the entity concerned before adoption. |
| Engine notes | No amendment seen rewrites Article 226(2). Gap treatment is governed by NUM-018. |
| Evidence | LEG-01, TEN-39, research/design_decision_matrix.md#LG-1 |
| Evidence strength | standard |
| Status | provisional |
| Decision ref | null |
| Check method | manual_review |
| Check description | Confirm series exist per supplier and numbers are unique and sequential. |
| Lifecycle stage | Governance |

#### NUM-002: Germany invoice number

| Field | Value |
|---|---|
| Statement | German invoices MUST carry a consecutive number, with one or more series, issued once by the issuer. |
| Level | MANDATORY |
| Scope | OLTP |
| Applies when | Jurisdiction: Germany. Invoice issuers under UStG 14(4) point 4 |
| Rationale | The number is a required invoice item. Requires legal review by counsel for the entity concerned before adoption. |
| Exceptions | No exception identified in the sources read. Requires legal review by counsel for the entity concerned before adoption. |
| Engine notes | Gap treatment is not relied on: it rests on search snippets of BMF pages, and UStAE 14.5 could not be opened (LEG-06, not cited). See NUM-018. |
| Evidence | LEG-04, research/design_decision_matrix.md#LG-2 |
| Evidence strength | standard |
| Status | provisional |
| Decision ref | null |
| Check method | manual_review |
| Check description | Confirm one-time issue within each series. |
| Lifecycle stage | Governance |

#### NUM-003: France invoice number

| Field | Value |
|---|---|
| Statement | French invoices MUST carry a unique number from a chronological and continuous sequence per series, with no duplicates. |
| Level | MANDATORY |
| Scope | OLTP |
| Applies when | Jurisdiction: France. Invoice issuers |
| Rationale | This is the strictest wording found, and no official tolerance for gaps or spoiled numbers was found. Requires legal review by counsel for the entity concerned before adoption. |
| Exceptions | No exception identified in the sources read. Requires legal review by counsel for the entity concerned before adoption. |
| Engine notes | Article 242 nonies A was not opened. |
| Evidence | LEG-07, LEG-08, research/design_decision_matrix.md#LG-3 |
| Evidence strength | standard |
| Status | provisional |
| Decision ref | null |
| Check method | manual_review |
| Check description | Confirm continuity within each series and reasons for any break. |
| Lifecycle stage | Governance |

#### NUM-004: Italy invoice number

| Field | Value |
|---|---|
| Statement | Italian invoices MUST carry a progressive number that uniquely identifies them, to which the date may contribute. |
| Level | MANDATORY |
| Scope | OLTP |
| Applies when | Jurisdiction: Italy. Invoice issuers under Article 21 DPR 633/1972, per Risoluzione 1/E of 2013 |
| Rationale | The number is a required invoice item, and the source does not address gaps. Requires legal review by counsel for the entity concerned before adoption. |
| Exceptions | No exception identified in the sources read. Requires legal review by counsel for the entity concerned before adoption. |
| Engine notes | Gap treatment is governed by NUM-018. |
| Evidence | LEG-10, research/design_decision_matrix.md#LG-4 |
| Evidence strength | standard |
| Status | provisional |
| Decision ref | null |
| Check method | manual_review |
| Check description | Confirm progressive numbering and uniqueness. |
| Lifecycle stage | Governance |

#### NUM-005: Spain invoice number

| Field | Value |
|---|---|
| Statement | Spanish invoices MUST be numbered sequentially within each series, with a separate series for corrective invoices. |
| Level | MANDATORY |
| Scope | OLTP |
| Applies when | Jurisdiction: Spain. Invoice issuers under RD 1619/2012 |
| Rationale | The number is a required invoice item, and corrective invoices use their own series. Requires legal review by counsel for the entity concerned before adoption. |
| Exceptions | No exception identified in the sources read. Requires legal review by counsel for the entity concerned before adoption. |
| Engine notes | [WF] LEG-11 was read only through a summarising fetch tool; re-check against raw BOE text. Gap treatment is governed by NUM-018. |
| Evidence | LEG-11, research/design_decision_matrix.md#LG-5 |
| Evidence strength | standard |
| Status | provisional |
| Decision ref | null |
| Check method | manual_review |
| Check description | Confirm series design, including a separate corrective series. |
| Lifecycle stage | Governance |

#### NUM-006: Spain VERI*FACTU chain

| Field | Value |
|---|---|
| Statement | Billing software within RD 1007/2023 scope MUST produce chained billing records. |
| Level | MANDATORY |
| Scope | OLTP |
| Applies when | Jurisdiction: Spain. Billing software within RD 1007/2023 scope only |
| Rationale | The chain rule concerns billing records and is not a rule on invoice number gaps. Requires legal review by counsel for the entity concerned before adoption. |
| Exceptions | No exception identified in the sources read. Requires legal review by counsel for the entity concerned before adoption. |
| Engine notes | [WF] LEG-12 was read only through a summarising fetch tool; re-check. RD 1007/2023 scope and dates were not researched. |
| Evidence | LEG-12, research/design_decision_matrix.md#LG-5 |
| Evidence strength | standard |
| Status | provisional |
| Decision ref | null |
| Check method | manual_review |
| Check description | Confirm whether the software is in scope and, if so, that records are chained. |
| Lifecycle stage | Governance |

#### NUM-007: UK invoice number

| Field | Value |
|---|---|
| Statement | UK VAT invoices MUST carry a sequential number based on one or more series that uniquely identifies the document. |
| Level | MANDATORY |
| Scope | OLTP |
| Applies when | Jurisdiction: United Kingdom. VAT-registered suppliers under Notice 700/21 |
| Rationale | The number is a required invoice item. Requires legal review by counsel for the entity concerned before adoption. |
| Exceptions | HMRC tolerates a break if the spoiled invoice is kept or the break is explained; VATREC is an internal manual recording HMRC's view, not legislation. Requires legal review by counsel for the entity concerned before adoption. |
| Engine notes | Clearest gap statement found. |
| Evidence | LEG-13, LEG-14, research/design_decision_matrix.md#LG-6 |
| Evidence strength | standard |
| Status | provisional |
| Decision ref | null |
| Check method | manual_review |
| Check description | Confirm sequential numbering and retained explanations for any break. |
| Lifecycle stage | Governance |

#### NUM-008: Pakistan serial invoice number

| Field | Value |
|---|---|
| Statement | Pakistani registered persons MUST issue serially numbered tax invoices. |
| Level | MANDATORY |
| Scope | OLTP |
| Applies when | Jurisdiction: Pakistan. Registered persons under Sales Tax Act 1990 s23(1) |
| Rationale | The serial number is a statutory invoice item. Requires legal review by counsel for the entity concerned before adoption. |
| Exceptions | No exception identified in the sources read. Requires legal review by counsel for the entity concerned before adoption. |
| Engine notes | Gap treatment was not found in the sources. Consolidated text read; check the gazette for the legal citation. |
| Evidence | LEG-18, research/design_decision_matrix.md#LG-7 |
| Evidence strength | standard |
| Status | provisional |
| Decision ref | null |
| Check method | manual_review |
| Check description | Confirm serial numbering per registered person. |
| Lifecycle stage | Governance |

#### NUM-009: Pakistan FBR integration

| Field | Value |
|---|---|
| Statement | FBR-integrated persons MUST hold the unique FBR invoice number and QR code and MUST record every adjustment, modification or cancellation. |
| Level | MANDATORY |
| Scope | OLTP |
| Applies when | Jurisdiction: Pakistan. Integrated persons notified by FBR under Sales Tax Rules 2006, Rule 150Q onward |
| Rationale | These are required items for integrated persons. Requires legal review by counsel for the entity concerned before adoption. |
| Exceptions | Start dates conflict: a reported SRO 709(I)/2025 table lists 1 May 2025 for corporates (search snippet), FBR's FAQ says 1 June 2025 corporate and 1 July 2025 non-corporate, and an extension notice was not opened. Do not fix a start date without review. Requires legal review by counsel for the entity concerned before adoption. |
| Engine notes | See NUM-020 for separating these items from the local number. |
| Evidence | LEG-19, research/design_decision_matrix.md#LG-7 |
| Evidence strength | standard |
| Status | provisional |
| Decision ref | null |
| Check method | manual_review |
| Check description | Confirm the FBR number, QR and adjustment records for integrated persons. |
| Lifecycle stage | Governance |

#### NUM-010: UAE invoice number

| Field | Value |
|---|---|
| Statement | UAE tax invoices MUST carry a sequential number or a unique number that identifies the invoice and its order in a sequence of invoices. |
| Level | MANDATORY |
| Scope | OLTP |
| Applies when | Jurisdiction: United Arab Emirates. VAT registrants under VAT Executive Regulation Article 59(1)(d) |
| Rationale | A random identifier alone would not show order, which is an inference from the text. Requires legal review by counsel for the entity concerned before adoption. |
| Exceptions | No exception identified in the sources read. Requires legal review by counsel for the entity concerned before adoption. |
| Engine notes | Citation conflict: the MoF compilation footnote cites Cabinet Decision 100 of 2024, while commentary cites 100 of 2025. Gap treatment was not found. |
| Evidence | LEG-22, research/design_decision_matrix.md#LG-8 |
| Evidence strength | standard |
| Status | provisional |
| Decision ref | null |
| Check method | manual_review |
| Check description | Confirm the number shows order within a sequence. |
| Lifecycle stage | Governance |

#### NUM-011: UAE e-invoice UUID

| Field | Value |
|---|---|
| Statement | UAE e-invoices MUST carry a UUID in addition to the sequential e-invoice number. |
| Level | MANDATORY |
| Scope | OLTP |
| Applies when | Jurisdiction: United Arab Emirates. E-invoicing under Guidelines V2.0 |
| Rationale | E-invoicing guidance requires it in addition to the sequence. Requires legal review by counsel for the entity concerned before adoption. |
| Exceptions | No exception identified in the sources read. Requires legal review by counsel for the entity concerned before adoption. |
| Engine notes | See NUM-020. |
| Evidence | LEG-24, research/design_decision_matrix.md#LG-8, research/design_decision_matrix.md#LG-15 |
| Evidence strength | standard |
| Status | provisional |
| Decision ref | null |
| Check method | manual_review |
| Check description | Confirm UUID and sequential number are both present. |
| Lifecycle stage | Governance |

#### NUM-012: KSA invoice number

| Field | Value |
|---|---|
| Statement | Saudi tax invoices MUST carry a sequential number that distinguishes them from other invoices. |
| Level | MANDATORY |
| Scope | OLTP |
| Applies when | Jurisdiction: Saudi Arabia. KSA VAT scope, ZATCA invoicing guideline |
| Rationale | The number is a required invoice item. Requires legal review by counsel for the entity concerned before adoption. |
| Exceptions | No exception identified in the sources read. Requires legal review by counsel for the entity concerned before adoption. |
| Engine notes | Gap treatment is governed by NUM-018 and NUM-013. |
| Evidence | LEG-25, research/design_decision_matrix.md#LG-9 |
| Evidence strength | standard |
| Status | provisional |
| Decision ref | null |
| Check method | manual_review |
| Check description | Confirm sequential numbering per taxpayer. |
| Lifecycle stage | Governance |

#### NUM-013: KSA counter and hash chain

| Field | Value |
|---|---|
| Statement | In KSA e-invoicing scope, the invoice counter value MUST NOT be reused, rejected documents MUST consume a counter value and stay in the chain, and each invoice MUST hold the previous invoice hash. |
| Level | MANDATORY |
| Scope | OLTP |
| Applies when | Jurisdiction: Saudi Arabia. KSA e-invoicing scope, ZATCA technical guidelines |
| Rationale | The technical guideline requires this chain. Requires legal review by counsel for the entity concerned before adoption. |
| Exceptions | No exception identified in the sources read. Requires legal review by counsel for the entity concerned before adoption. |
| Engine notes | The technical guideline read is dated November 2022 and later versions may exist. Append-only event series is an inference. |
| Evidence | LEG-26, LEG-27, research/design_decision_matrix.md#LG-9, research/design_decision_matrix.md#LG-15 |
| Evidence strength | standard |
| Status | provisional |
| Decision ref | null |
| Check method | pipeline_test |
| Check description | Confirm counter values are not reused and chain continuity holds, including rejected documents. |
| Lifecycle stage | Transactions |

#### NUM-014: ViDA corrective invoice reference

| Field | Value |
|---|---|
| Statement | From 1 July 2030 where transposed, EU corrective invoices MUST cite the sequential number of the corrected invoice. |
| Level | MANDATORY |
| Scope | OLTP |
| Applies when | Jurisdiction: European Union. From 1 July 2030 where transposed into national law, under Directive (EU) 2025/516 Article 5 |
| Rationale | ViDA adds point (16) to Article 226. National transposition was not researched. Requires legal review by counsel for the entity concerned before adoption. |
| Exceptions | Article 6(5) derogation for Member States with a qualifying real-time reporting obligation applies specified measures by 1 January 2035. Requires legal review by counsel for the entity concerned before adoption. |
| Engine notes | Article 226(2) is not rewritten by any amendment seen. A self-reference design is an inference. Transposition deadline for Article 5 is 30 June 2030. |
| Evidence | LEG-02, research/design_decision_matrix.md#LG-10, research/database_security_standards.md#12.8 |
| Evidence strength | standard |
| Status | provisional |
| Decision ref | null |
| Check method | manual_review |
| Check description | Check national transposition and confirm corrective invoices can cite the corrected number. |
| Lifecycle stage | Governance |

### Numbering controls

#### NUM-015: Record unused numbers

| Field | Value |
|---|---|
| Statement | Every unused, cancelled or spoiled invoice number SHOULD be recorded with a reason. |
| Level | RECOMMENDED |
| Scope | OLTP |
| Applies when | Jurisdiction-scoped: legal entities under the UK, French and KSA rules in NUM-003, NUM-007 and NUM-013; elsewhere a recommended control |
| Rationale | An unexplained break is hard to defend; UK guidance tolerates a break if it is explained or the spoiled invoice kept. Requires legal review by counsel for the entity concerned before adoption. |
| Exceptions | No exception identified in the sources read. Requires legal review by counsel for the entity concerned before adoption. |
| Engine notes | UK and ZATCA guidance are the direct sources. No French official text on spoiled numbers was found, so that wording is the continuity wording only. |
| Evidence | LEG-07, LEG-14, LEG-26, research/design_decision_matrix.md#LG-12 |
| Evidence strength | standard |
| Status | provisional |
| Decision ref | null |
| Check method | catalog_query |
| Check description | List gaps in each series and confirm each has a recorded reason. |
| Lifecycle stage | Data Quality |

#### NUM-016: Avoid plain sequences for legal numbers

| Field | Value |
|---|---|
| Statement | Legally numbered documents SHOULD NOT take numbers from a plain database sequence object where a gap-sensitive rule applies. |
| Level | RECOMMENDED |
| Scope | OLTP |
| Applies when | Jurisdiction-scoped: where a gap-sensitive rule applies, with France as the strictest wording found |
| Rationale | Sequences can skip on rollback or crash and cannot provide gapless numbering. Requires legal review by counsel for the entity concerned before adoption. |
| Exceptions | Series in jurisdictions where counsel confirms gaps are tolerated; the owner approves. Requires legal review by counsel for the entity concerned before adoption. |
| Engine notes | PostgreSQL documents sequences as non-gapless; other engines were not checked. The industry-practice file labels this MANDATORY where gaps are not acceptable; the matrix and note 19 hold it RECOMMENDED. |
| Evidence | TEN-33, LEG-07, research/design_decision_matrix.md#LG-13 |
| Evidence strength | single_vendor |
| Status | provisional |
| Decision ref | A6 |
| Check method | migration_lint |
| Check description | Flag any legal document number column sourced from a sequence object. |
| Lifecycle stage | Schema Design |

#### NUM-017: Series per legal entity and document type

| Field | Value |
|---|---|
| Statement | Legal numbering series SHOULD be defined per legal entity and document type. |
| Level | RECOMMENDED |
| Scope | OLTP |
| Applies when | Jurisdiction-scoped: regimes that allow one or more series; Spain requires a separate corrective series under NUM-005 |
| Rationale | A global series cannot meet per-entity rules or separate corrective series. Requires legal review by counsel for the entity concerned before adoption. |
| Exceptions | No exception identified in the sources read. Requires legal review by counsel for the entity concerned before adoption. |
| Engine notes | Design inference from the laws allowing one or more series. |
| Evidence | LEG-01, LEG-04, LEG-11, LEG-13, research/design_decision_matrix.md#LG-14 |
| Evidence strength | inference |
| Status | provisional |
| Decision ref | null |
| Check method | schema_lint |
| Check description | Check each numbered document type has a series scoped to its legal entity. |
| Lifecycle stage | Schema Design |

#### NUM-018: Gap policy per legal entity

| Field | Value |
|---|---|
| Statement | A multi-jurisdiction system SHOULD apply the strictest gap rule applying to each legal entity and SHOULD record every break in the series. |
| Level | RECOMMENDED |
| Scope | OLTP |
| Applies when | Jurisdiction-scoped: all jurisdictions in NUM-001 to NUM-013; no single gap rule can be derived |
| Rationale | Gap positions differ by jurisdiction and some are unsettled or unverified. Requires legal review by counsel for the entity concerned before adoption. |
| Exceptions | Counsel must confirm the gap rule for each legal entity. Requires legal review by counsel for the entity concerned before adoption. |
| Engine notes | France: continuity wording, no tolerance found. UK: tolerated with kept invoice or explanation. KSA: counter never reused. Germany: unverified. Italy, Spain, Pakistan, UAE: not addressed or not found. |
| Evidence | LEG-07, LEG-13, LEG-14, LEG-25, LEG-26, research/design_decision_matrix.md#LG-12, research/industry_best_practices.md#5 |
| Evidence strength | standard |
| Status | provisional |
| Decision ref | A6 |
| Check method | manual_review |
| Check description | Confirm the gap rule recorded for each legal entity and series. |
| Lifecycle stage | Governance |

#### NUM-019: Locked counter at posting

| Field | Value |
|---|---|
| Statement | Legal numbers SHOULD be assigned inside the issuing transaction from a locked per-series counter, so that drafts consume none. |
| Level | RECOMMENDED |
| Scope | OLTP |
| Applies when | Gap-sensitive numbering per NUM-016 |
| Rationale | Assignment outside the posting transaction consumes numbers for failed work; the cost is serialized posting per series. |
| Exceptions | Where counsel confirms gaps are tolerated; the system owner approves. |
| Engine notes | Inference; no fetched case documents this at scale. Frappe's naming series is a convention, and the notes do not show whether it is gapless. Decision A6 settles where assignment happens (OR-4): inside the issuing transaction, which is also the posting transaction where a document is issued on posting. Canonical rule for TXN-018. |
| Evidence | research/design_decision_matrix.md#TX-12, research/industry_best_practices.md#5 |
| Evidence strength | inference |
| Status | provisional |
| Decision ref | A6 |
| Check method | pipeline_test |
| Check description | Run concurrent postings with failures and confirm no number is lost or duplicated within a series. |
| Lifecycle stage | Transactions |

#### NUM-020: Separate authority identifiers

| Field | Value |
|---|---|
| Statement | Authority number, UUID, counter and previous-invoice hash SHOULD be held as separate attributes from the local invoice number where those regimes apply. |
| Level | RECOMMENDED |
| Scope | OLTP |
| Applies when | Jurisdiction-scoped: Pakistan FBR integrated persons, UAE e-invoicing and KSA e-invoicing |
| Rationale | Combining them prevents correlation with the authority and breaks chain validation. Requires legal review by counsel for the entity concerned before adoption. |
| Exceptions | No exception identified in the sources read. Requires legal review by counsel for the entity concerned before adoption. |
| Engine notes | The data items are mandatory under NUM-009, NUM-011 and NUM-013. Separation as attributes is an inference. |
| Evidence | LEG-19, LEG-24, LEG-26, LEG-27, research/design_decision_matrix.md#LG-15 |
| Evidence strength | inference |
| Status | provisional |
| Decision ref | null |
| Check method | schema_lint |
| Check description | Check that each regime's items are distinct attributes. |
| Lifecycle stage | Schema Design |

## Unsupported or not ruled

- Rate precision and triangulation: no source; no value set (TYP-010, TYP-011 and FIN-024, decisions A14 and B17).
- IAS 21 rate rules and IFRS 10 elimination paragraphs were not read. FIN-012 covers US GAAP issuers only, and FIN-051 imposes no elimination method.
- FASB Codification and PCAOB standards returned 403. ASC 830 is known through the SEC Baxter order and FAS 52 (superseded). AS 2401 is known only through a staff publication.
- SAP findings rest on training pages; no official company code definition was read. NetSuite adjustment periods are unstated.
- No law read requires database immutability or ledger hashing. Germany non-alteration does not prescribe a mechanism.
- Germany gap tolerance is not relied on: LEG-06 was not opened and is not cited.
- Gap positions were not found for Italy, Spain (invoice numbers), Pakistan or UAE.
- France commercial 10-year period: search snippet only, so held as RET-006.
- Italian and Spanish retention periods were not researched in depth.
- National ViDA transposition was not researched. RD 1007/2023 scope and dates were not researched.
- Pakistan FBR integration start dates are unresolved. Pakistani Companies Act rules for resolutions were read without confirming section numbers and are not ruled.
- Erasure: no regulator text read accepts key destruction as erasure or addresses soft deletion by name, so RET-037 is an inference. Undue delay for backups is unsettled.
- PCI DSS v4.0.1 text was not read; RET-020 and RET-031 rest on v4.0 SAQ D.
- Audit log retention: no source gives a general period, so RET-033 sets none. SOX 18 USC 1520 (5 years) and section 103 (7 years) cover auditor workpapers and not issuer ERP or log data. HIPAA 6 years covers required documentation; whether specific audit logs fall in scope is for counsel, so no HIPAA log period is ruled.
- Legal hold: no source covers database legal-hold mechanics, so RET-022 states the outcome only.
- ICO (LEG-33) and Dutch AP (LEG-35) were read only from Wayback captures and need confirmation on live sites.
- Excluded from this group as cross-cutting: exact monetary types (DT rows) and idempotent posting (TX-7). Airbnb financial reporting (CASE-35, CASE-36) and Uber LedgerStore (CASE-30) are not cited.

## Decisions needing owner approval

Answered by the owner on 2026-11-08: all defaults accepted. See `../DECISIONS_TO_APPROVE.md` for the decision log, and each rule's decision_ref for its decision number. Questions and alternatives are kept for the record.

Items marked as legal questions also need counsel. Each stays provisional in the registry until counsel confirms it.

| Rule | Question | Proposed default | Alternatives | Consequence of each |
|---|---|---|---|---|
| FIN-002 | At what grain is period status held? | Ledger and application or module. | Module or account type (SAP style); Book or document type (NetSuite, ERPNext style) | Default: precise control and more setup. Module or account type: simpler when ledgers are few. Book or document type: strongest for multi-book entities and most setup. |
| FIN-009 | Is an irreversible close offered? | Reopenable close with restricted reopening. | Offer permanent close (Oracle, Odoo); Offer it but advise against use (D365) | Default: recoverable, weaker assurance. Permanent: strong assurance, no late corrections. Offered with advice against: flexibility, relies on discipline. |
| FIN-015 | How are rates effective-dated? | Exact-day row per pair and type. | Most recent on or before, with a staleness limit (ERPNext style) | Default: precise and fails visibly on gaps. Alternative: tolerates gaps but can use stale rates; the limit has no sourced value. |
| FIN-016 | How are inverse rates handled? | Store each direction. | Derive the reciprocal (Oracle row generally reciprocal); Quotation convention (SAP) | Default: more rows, no reciprocal disagreement. Derive: less storage, rounding differences. Quotation: depends on rate setup. |
| FIN-020 | Does revaluation reverse in the next period? | Reverse for AR and AP only. | Carry forward everywhere; Reverse everywhere | Default: matches D365 split. Carry forward: fewer entries, comparability differs. Reverse everywhere: uniform but contradicts D365 GL. |
| FIN-023 | What precision do stored rates need? | None proposed; no sourced value exists. Owner sets one and records the reason. | Adopt a rate from the rate provider; Adopt the largest precision already in use across connected systems | Any value is a judgment. Too low risks conversion differences; too high adds display and rounding handling. No source quantifies either. |
| FIN-024 | How is triangulation handled? | None proposed; no method is sourced. Decide if the business needs it. | Use only direct rates (D365 and NetSuite pair behaviour); Define a triangulation method after research | Direct only: no method needed, but setup per pair. Defined method: needs a source first. |
| FIN-035 | Which reversal method? | Posted inverse entry. | Negative posting (SAP); Change Sign or Switch Debit or Credit (Oracle) | Default: activity totals rise and history is clear. Negative posting: activity resets. Change Sign: keeps the column and flips the sign. |
| FIN-036 | Can a reversal be reversed? | Forbid, and use a new entry. | Allow (D365) | Default: simpler audit trail, one extra entry. Allow: faster correction, longer chain. |
| FIN-039 | May generated vouchers be deleted on year-end reversal? (Legal question for Germany) | Post a reversing voucher. | Delete with a history record (D365); Keep only a record of deletion (NetSuite) | Default: non-alteration satisfied at the cost of extra entries. Deletion: simpler but legally unresolved under HGB 239(3). |
| FIN-046 | What is the master data scope? | Tenant-shared with per-company restriction available. | Tenant-shared only (D365 pattern); Per-company by default | Default: flexibility and more configuration. Tenant-shared: reuse, weaker control. Per-company: strong control, more duplicates. |
| NUM-018 | What gap rule applies per legal entity? (Legal question) | Apply the strictest rule applying to the entity and record every break. | Per-jurisdiction rule without the strictest-rule default; Allow gaps with explanation everywhere (UK model) | Default: conservative and adds contention. Per-jurisdiction: less cost but needs counsel per country. UK model everywhere: cheapest and likely non-compliant with French wording. |
| RET-006 | What period applies to French commercial accounting documents? (Legal question) | Configure no binding period until counsel confirms; plan on the longer of the tax and commercial periods. | Adopt 10 years now (unverified); Apply only the 6-year tax period | Default: no compliance claim made. 10 years now: over-retention risk and unverified. 6 years only: possible under-retention. |
| RET-026 | How are erasures in EU and UK backups handled? (Legal question) | Beyond use, durable register, re-apply on restore, with a defined backup expiry. | Immediate deletion from backups; Delay until restore or next use (California model) | Default: follows ICO and EDPB patterns, undue delay unsettled. Immediate: strongest position and may harm backup integrity. California model: lawful in CCPA scope only. |
