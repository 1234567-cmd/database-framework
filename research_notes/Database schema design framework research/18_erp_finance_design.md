# 18. ERP and financial data design: evidence notes

Research date: 2026-11-08. Scope: fiscal calendars and period close, multi-currency, multi-company, posted-entry immutability and reversals, subledger to GL. Research only: this file has no schemas and no framework rules. Catalog: `catalog_18_erp_finance.json` (ERP-01 to ERP-25).

## How to read this file

**Quotation marks** appear only for text extracted directly with curl or pdftotext: German statutes, 15 USC 78m, 17 CFR 240.13b2-1, ERPNext pages, the IAS 21 summary page, FAS 52, the SEC Baxter order, the PCAOB Audit Focus and Oracle's Using General Ledger PDF. Everything else came through a summarizing fetch tool and is paraphrase, even where it looks exact. Vendor identifiers in backticks were read through the same tool.

**Labels**
- MANDATORY: a law or accounting standard read here requires the substance, for the stated jurisdiction or reporting basis. It does not mean any specific implementation is mandated.
- RECOMMENDED: a vendor recommends it, or several vendors converge on it.
- OPTIONAL/CONTEXTUAL: depends on the product, deployment or workload.

**Workload scope** is given per finding: GL (general ledger OLTP), SUB (subledgers), CONS (consolidation), DW (reporting or warehouse copies).

**Evidence limits.** SAP's product docs (help.sap.com) rendered as empty shells, so SAP findings rest on SAP Learning training pages (authority 3). The current FASB Codification and PCAOB standard pages returned 403. IFRS full text requires sign-in. See Gaps.

## 1. Fiscal calendars and period close

### 1.1 Vendor comparison

| Vendor | Status keyed by | Status values or controls | Adjustment periods | Year-end |
|---|---|---|---|---|
| SAP S/4HANA (ERP-01) | Posting period variant assigned to company code; account type (+, A, D, K, M, V, S) and account interval | Open or closed through intervals: Normal, Adjustment, CO-related | Up to four special periods, 13-16; posting date must fall in the last regular period; period entered manually in the header | Not established in pages read |
| Oracle Fusion (ERP-05, ERP-06) | `APPLICATION_ID`, `LEDGER_ID`, `PERIOD_NAME` | `CLOSING_STATUS`: O, F, C, P, N (26A table) | `ADJUSTMENT_PERIOD_FLAG`; example `ADJ-NOV-20` shares its date with period end | Not fully extracted for Fusion |
| Oracle GL Users' Guide, older, release not stated (ERP-05 support) | Set of books, period | Open, Closed, Permanently Closed, Never Opened, Future-Entry | Not covered on page | Opening the first period of a new year updates Retained Earnings |
| Dynamics 365 Finance (ERP-09, ERP-10) | Ledger calendar: a per-legal-entity copy of a shared fiscal calendar; period status and module access | Open, On hold, Permanently closed | Closing period copies the dates of an open period; usually a 13th period | Generated opening transaction, optional closing transaction, rerun allowed, one fiscal calendar per template |
| NetSuite (ERP-14, ERP-15) | Period; per subsidiary for locks in OneWorld; per accounting book for close | Locks for A/R, A/P, Payroll, All; Close per book; Allow Non-G/L Changes | No statement found | No statement found |
| Odoo (ERP-18) | Date per company | Lock Everything date with logged exceptions; Hard Lock date | None in pages read | Manual miscellaneous entry from the current-year earnings account (default 999999) to equity |
| ERPNext (ERP-19) | Date range and company, listing document types | Accounting Period, Accounts Frozen Till Date, Period Closing Voucher | None in pages read | Period Closing Voucher transfers profit or loss |

### 1.2 Findings

- **F1. RECOMMENDED (GL, SUB): period status is not a single flag per company.** All vendors with period records keep status at a finer grain than company: SAP by account type and interval, Oracle by application and ledger, D365 by module and user group within a period, NetSuite by subledger lock and book, ERPNext by document type. Convergence on grain is strong; the chosen grain differs.
- **F2. RECOMMENDED (GL): calendar definition and period status are separable.** D365 keeps a shared fiscal calendar and copies it to a ledger calendar per legal entity (ERP-09). Oracle's key uses the ledger (ERP-05). SAP assigns the variant to company codes, so one variant can serve several (search snippet of SAP Help, unverified; ERP-01 confirms assignment).
- **F3. OPTIONAL/CONTEXTUAL (GL): adjustment periods are overlapping in dates, so a date does not identify a period.** SAP specials need a posting date in the last regular period and the period entered manually; D365 closing periods copy the dates of an existing period; Oracle's adjusting period example has a one-day range equal to the period end. Applies to any product or warehouse that derives period from date. Oracle says journals are not copied to adjusting periods when secondary ledgers use a different calendar: "If your requirement is to post to an adjusting period, then you must manually change the period in the secondary ledger journal." (ERP-06).
- **F4. RECOMMENDED (GL, SUB): close is ordered and gated, not a status write.** NetSuite publishes an ordered dependency list ending in Close Period, with revaluation, consolidated rates and elimination in that order (ERP-14). Oracle can block GL close when subledgers have open periods, and "Regardless of how the option is set, you can't close a General Ledger period for a ledger that has pending Intercompany transactions" with listed statuses (ERP-06). Oracle's table warns that setting status to open does not open a never-opened period (ERP-05).
- **F5. RECOMMENDED, with vendor disagreement (GL): irreversible close is available but discouraged by one vendor.** Oracle offers Permanently Closed (older guide: no transition out). D365 offers Permanently closed but advises against it because the period cannot reopen (ERP-10). Odoo's Hard Lock cannot be changed or overridden (ERP-18).
- **F6. RECOMMENDED (GL): reopening invalidates downstream close work.** NetSuite reopen automatically reopens later closed periods, requires the Manage Accounting Periods permission, and stores a justification as a user note (ERP-15). D365 lets you reopen on-hold periods for adjustments after year-end close, then requires rerun of the close to carry balances (ERP-10, ERP-12).
- **F7. OPTIONAL/CONTEXTUAL (GL, DW): fiscal year status differs from period status.** D365 blocks reversal when the year-end close has run even if a period in that year is open (ERP-12).
- **F8. OPTIONAL/CONTEXTUAL (GL, SUB): period close and P&L closing can be different objects.** ERPNext: "The voucher does not erase history or stop backdated entries." It directs users to Accounting Period or Accounts Frozen Upto for protection (ERP-19).

## 2. Multi-currency

### 2.1 What the standard setters say (public pages only)

- **IAS 21 (ERP-21), MANDATORY for IFRS reporters at the level of concepts.** The IFRS Foundation page says the standard prescribes accounting for foreign currency transactions, translation of foreign operations into the "functional currency" and translation into a "presentation currency", and that "The principal issues are which exchange rate(s) to use and how to report the effects of changes in exchange rates". Functional currency is "the currency of the primary economic environment in which the entity operates". The page does not give the rate rules. It records an August 2023 amendment on lack of exchangeability, without an effective date.
- **US GAAP.** The current Codification returned 403. Two public FASB and SEC sources were read:
  - SEC order on Baxter (ERP-22 support, 2022-02-22): "ASC 830-20-30-1 requires that foreign currency transactions initially be measured and recorded in an entity's functional currency using the exchange rate on the date of the transaction. ASC 830-20-35-2 requires that foreign currency denominated assets and liabilities be remeasured at the end of each reporting period using the exchange rate at that date."
  - FAS 52 (December 1981, ERP-22), now superseded by the Codification, para. 16: "At the date the transaction is recognized, each asset, liability, revenue, expense, gain, or loss arising from the transaction shall be measured and recorded in the functional currency of the recording entity by use of the exchange rate in effect at that date". Para. 12: "For assets and liabilities, the exchange rate at the balance sheet date shall be used." and "an appropriately weighted average exchange rate for the period may be used". Para. 138 on multiple rates uses the dividend remittance rate absent unusual circumstances.

### 2.2 Findings

- **F9. MANDATORY in substance (US GAAP issuers, per the SEC order) (GL, SUB): a transaction-date rate must be attributable to the transaction.** The Baxter order describes a convention using rates from a specified date near the middle of the prior month as "not in accordance with GAAP" (order para. 8, before July 2019). Workload: any ledger posting foreign currency entries. Whether a stored per-line rate is required is an inference, not stated.
- **F10. RECOMMENDED (GL, CONS): several rate roles exist per period.** FAS 52 implies balance sheet date and weighted average rates. NetSuite stores `currentrate`, `averagerate`, `historicalrate` per period, subsidiary pair and book (ERP-16). D365 allows different rate types for revaluation and financial reporting per main account (ERP-11). SAP rate types include M (average), B, G and P (ERP-03 support).
- **F11. RECOMMENDED (GL, DW): rates are keyed by pair, date and type.** Oracle's primary key is `FROM_CURRENCY, TO_CURRENCY, CONVERSION_DATE, CONVERSION_TYPE` (ERP-08). ERPNext "searches by transaction date and chooses the latest eligible matching record" (ERP-20). Two effective-dating patterns therefore exist: exact-day rows (Oracle) and most-recent-on-or-before with a staleness limit (ERPNext). SAP's valid-from logic was not established.
- **F12. RECOMMENDED (GL, SUB): keep original, entity and optional reporting currency amounts together.** D365 records accounting and optional reporting currency on all vouchers (ERP-09). ERPNext distinguishes company, account and transaction currency and says "Do not change an Account's currency after ledger entries exist." (ERP-20 support). SAP allows up to eight additional currency types per ledger (ERP-03 support).
- **F13. RECOMMENDED (GL): revaluation has a run record and a separate rate date.** D365 keeps history per legal entity and posting layer, and Date of Rate is independent of the To date (ERP-11). NetSuite uses the rate at the last day of the period, or the current date if run from the menu early, and says to lock first (ERP-17 support).
- **F14. RECOMMENDED (GL): realized and unrealized differences use separate accounts.** D365 and ERPNext both name separate accounts (ERP-09, ERP-20 support); Odoo has journal, gain and loss defaults (ERP-18 support). NetSuite posts realized on settlement and unrealized on revaluation (ERP-17 support).
- **F15. OPTIONAL/CONTEXTUAL (GL): rounding differences need a defined home.** ERPNext: "Each line is converted and rounded separately, so totals can differ by a cent or a few units of a small currency." (ERP-20 support). A D365 search snippet says revaluations rounding to zero are not posted (not opened). Oracle balances by legal entity including rounding imbalances (ERP-07).
- **F16. OPTIONAL/CONTEXTUAL (CONS): translation paths are not transitive in the products read.** D365 consolidation translates from the source accounting currency directly: to go MXN to USD to EUR requires an intermediate consolidation company (ERP-13). NetSuite rates are per subsidiary pair (ERP-16).

### 2.3 Rate precision

Evidence is thin. Oracle lists `CONVERSION_RATE` as `NUMBER` with no precision given (ERP-08). ERPNext's Currency Precision "affects monetary values such as rate and amount" (ERP-20 support), a site setting. D365's example displays 166.6667 and computes with 1.666667 (ERP-11). No vendor page read states a rate precision standard, and no standard setter page read addresses it.

## 3. Multi-company

- **F17. RECOMMENDED (GL, CONS): legal entity, ledger and business unit are distinct.** Oracle: the primary balancing segment represents legal entities; a business unit posts to one primary ledger and has a default legal entity (ERP-07). D365: a ledger is configured per legal entity (ERP-09). SAP: company codes attach to variants (ERP-01); no official definition of company code against legal entity was read. Odoo: companies are the multi-company unit, and branches were not explained in the excerpt (ERP-18 support).
- **F18. MANDATORY in substance only for consolidated reporters (CONS).** The IFRS 10 page says a parent must present consolidated statements and describes the group as a single economic entity (ERP-21 support, paraphrase). Elimination paragraphs were not available. FAS 52 para. 25 addresses elimination of intercompany profits. 17 CFR 210.3A-04 could not be read.
- **F19. RECOMMENDED (GL, CONS): intercompany is a linked pair of entries, each balanced per entity.** ERPNext: "Each company's entry balances independently." and the first entry "posts only in the first Company" (ERP-20 support). D365 uses directional legal entity pairs with due-to and due-from accounts, and a second pair for reciprocity (ERP-13 support). Oracle balances automatically by legal entity (ERP-07).
- **F20. OPTIONAL/CONTEXTUAL (CONS): where elimination lives varies.** D365: separate elimination legal entity or report-time consolidation (ERP-13). SAP: posting level 20 with one-sided revenue and cost elimination (ERP-04). NetSuite: elimination journal entries with currency differences to CTA-E, and line-level elimination flags (ERP-17).
- **F21. RECOMMENDED (CONS): currency differences on intercompany are expected, not errors.** NetSuite CTA-E and its example linking revaluation to the original line (ERP-17); D365 notes elimination journals show originating currency rather than accounting currency (ERP-13).

## 4. Posted-entry immutability, reversals and subledger to GL

### 4.1 Authoritative sources

- **F22. MANDATORY (Germany, commercial and tax books) (GL, SUB).** HGB s.239(3): "Eine Eintragung oder eine Aufzeichnung darf nicht in einer Weise verändert werden, daß der ursprüngliche Inhalt nicht mehr feststellbar ist. Auch solche Veränderungen dürfen nicht vorgenommen werden, deren Beschaffenheit es ungewiß läßt, ob sie ursprünglich oder erst später gemacht worden sind." AO s.146(4) has the same rule for tax. HGB s.238(1): "Die Geschäftsvorfälle müssen sich in ihrer Entstehung und Abwicklung verfolgen lassen." Retention under HGB s.257(4): "zehn Jahre", "acht Jahre" and "sechs Jahre" by document class. All ERP-23.
- **F23. MANDATORY (US issuers) (GL, SUB), but mechanism not specified.** 15 USC 78m(b)(2)(A) requires issuers to "make and keep books, records, and accounts, which, in reasonable detail, accurately and fairly reflect the transactions and dispositions of the assets of the issuer", and (B) a system of internal accounting controls (ERP-24). 17 CFR 240.13b2-1: "No person shall directly or indirectly, falsify or cause to be falsified, any book, record or account" (ERP-24 support). Neither text mentions reversal entries or database immutability.
- **F24. RECOMMENDED, grounded in binding audit standards (audited issuers) (GL).** PCAOB staff's January 2025 publication states AS 2401 misstatements involve "recording inappropriate or unauthorized journal entries throughout the year or at period end", or "adjustments to amounts reported in the financial statements that are not reflected in formal journal entries", and lists not testing "the completeness of the population of journal entries" as a deficiency (ERP-25). It states: "It is not a rule, policy, or statement of the Board."

### 4.2 Vendor behaviour

| Vendor | After posting | Reversal details |
|---|---|---|
| SAP (ERP-02) | Reversal available for documents that cannot be modified | Normal reversal (inverse, increases figures) or negative posting (resets figures); requires reversal reason; cleared items block until reset |
| Oracle (ERP-06) | "After posting, either reverse and enter the journal again, or enter a new journal to correct the amounts in question." | "Reversal journals can't be reversed."; methods Change Sign and Switch Debit or Credit |
| D365 (ERP-12) | Reversal subject to period and year-end status and settlement | Reversal can itself be reversed; some documents need credit notes; year-end reversal deletes vouchers |
| NetSuite (ERP-15) | GL-impacting edits blocked in closed periods | Void sets totals to zero; Delete keeps only a record of deletion and is unavailable when the Void Transactions Using Reversing Journals preference is on |
| Odoo (ERP-18) | Secured entries cannot be edited | SHA-256 chain over named fields; Hard Lock irreversible |
| ERPNext (ERP-19) | "Do not edit a submitted posting." | Reverse Journal Entry "creates a separate draft with exchanged debit and credit sides"; cancellation is a separate path, subject to Immutable Ledger rules not read |

### 4.3 Findings

- **F25. RECOMMENDED (GL, SUB): correction by new entry is the vendor norm, with exceptions.** Oracle, SAP (document reversal), D365 and ERPNext all correct by new entry, consistent with F22. Exceptions in section 5.
- **F26. RECOMMENDED (GL): a reversal has separately chosen date and method.** D365 allows a different reversing date (ERP-12). SAP has an alternative posting date indicator (search snippet of SAP Learning, not on the page opened) and a reversal reason (ERP-02). Oracle's reversal options determine accounting date and method (ERP-06).
- **F27. RECOMMENDED (GL, SUB): reversal eligibility depends on state beyond the entry itself.** Settlement, transfer status and fiscal status (ERP-12). Oracle requires, for automatic reversal, a non-reversal journal and a source that is not frozen, among others (ERP-06).
- **F28. RECOMMENDED (SUB to GL): subledger entries can exist before transfer.** D365 blocks reversal of non-PO vendor and free text invoices until the entry is transferred (ERP-12). Oracle treats "Unprocessed and untransferred subledger transactions" as period close exceptions (ERP-06), and ERP-06 lists "Pending transactions in the General Ledger interface".
- **F29. OPTIONAL/CONTEXTUAL (GL, regulated jurisdictions): tamper evidence.** Odoo's hash chain is the only cryptographic control seen. Odoo describes its Hard Lock date as intended for data inalterability in certain countries. No law or standard read requires hashing.
- **F30. OPTIONAL/CONTEXTUAL (GL, audited issuers): auditability of the population.** F24 supports a complete, reconcilable journal. Whether this requires row-level immutability is an inference.

## 5. Conflicts recorded

1. **Deletion against non-alteration.** D365 Reverse year-end close deletes opening and closing vouchers, with a history record, and states that no reversing voucher is posted (ERP-12, ERP-10). NetSuite Delete retains only the fact of deletion (ERP-15). HGB s.239(3) forbids changes that lose original content (ERP-23). Whether generated opening balances count as books under the statute is not addressed by any source read.
2. **Reversal of a reversal.** Oracle: not allowed (ERP-06). D365: allowed (ERP-12).
3. **Permanent close.** Oracle and Odoo offer it; D365 advises against it (F5).
4. **What a reversal does to balances.** SAP negative posting resets figures while normal reversal increases them; Oracle Change Sign keeps the column and flips sign (ERP-02, ERP-06). Debit and credit activity totals differ between methods.
5. **Revaluation reversal.** D365 GL does not reverse earlier revaluation; D365 AR and AP do (ERP-11). AR and AP revaluation cannot themselves be reversed afterwards, only rerun (ERP-12). An older Oracle guide snippet says balance sheet revaluations reverse next period (search snippet only, unverified).
6. **Inverse rates.** Oracle stores an inverse row "generally" the reciprocal (paraphrase, ERP-08). ERPNext: "The inverse is not automatically the same number, so create USD to EUR separately when that direction is needed." (ERP-20). SAP presents direct and indirect quotation over a rate (ERP-03). A rate and its reciprocal may not agree after rounding.
7. **Status list.** Oracle's 26A table lists five status codes (ERP-05); a Fusion REST snippet also lists W, read only in search output. Treat as unconfirmed.
8. **Unrealized differences on the balance sheet.** D365's ledger page says unrealized gains and losses are recorded on the balance sheet (ERP-09), while its revaluation example posts to accounts named Unrealized loss and gain against cash (ERP-11). The presentation of each side needs clarification.
9. **Odoo versions.** 17.0 and 18.0 pages differ in emphasis on hash locking (the 17.0 page was seen only in search output).

## 6. Gaps and unresolved items

- **SAP product docs**: help.sap.com pages rendered as empty; no ACDOCA table-level detail, no official company code definition, no valid-from rule for rates, no decimal or precision information. SAP findings rest on training pages.
- **FASB Codification** (asc.fasb.org) and **PCAOB standards pages** returned 403. ASC 830 is known here only through a superseded statement and an SEC order. AS 2401 paragraph text is known only through the staff publication.
- **IAS 21 and IFRS 10 full text**: not read. No IAS 21 or IFRS 10 paragraph numbers are cited. Consolidation elimination requirements are unverified.
- **17 CFR 210.3A-04**: page returned no rule text; ecfr.gov redirected to a blocking page.
- **GoBD** (German tax administration): 503 at retrieval. Rz. references seen only in search snippets are excluded from findings.
- **Triangulation**: no vendor page opened describes triangulation; D365 training mentions it only as a learning objective (search snippet). D365's exchange rate provider, effective-date selection and rounding settings were not found.
- **Rate precision**: no vendor-stated precision (section 2.3). A framework decision on rate precision is not supported by evidence from this research.
- **Oracle Fusion ledger detail**: the 25C page on primary and secondary ledgers returned a landing page. The Fusion year-end and period-status narrative were not fully extracted from the 26B PDF.
- **NetSuite adjustment periods and year-end**: no statement found.
- **Odoo and ERPNext rate precision, branches, exchange rate semantics**: partly unread.
- **ISA 240 (IAASB)**: not retrieved.
- **ERPNext immutable ledger**: named in docs, page not found.

Sources: see catalog for full URLs, supporting pages and verification status. All 25 catalog entries are url_verified true; supporting pages not opened are named above and in catalog notes.
