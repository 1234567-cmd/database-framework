# Corrections that override the topic notes (apply when writing research/ deliverables)

## Verification update 2026-11-08

Source: `22_evidence_verification.md` and `verification_results.json` (95 objects). Where this section conflicts with older text below, this section wins. The older text is kept for history.

### Restrictions lifted

| Item | Result | Exact detail | Source |
|---|---|---|---|
| Testcontainers definition (note 13) | Exact wording confirmed; may be used | "Testcontainers is an open source library for providing throwaway, lightweight instances of databases, message brokers, web browsers, or just about anything that can run in a Docker container." | https://testcontainers.com/ |
| Codd primary key passage, opening words | Exact wording confirmed; pdftotext on the PDF retrieved by WebFetch | "Normally, one domain (or combination of domains) of a given relation has values which uniquely identify each element (n-tuple) of that relation. Such a domain (or combination) is called a primary key." | https://www.engineering.upenn.edu/~zives/03f/cis550/codd.pdf |
| PACELC definition | Exact wording confirmed; may be quoted; pdftotext on the PDF retrieved by WebFetch | "if there is a partition (P), how does the system trade off availability and consistency (A and C); else (E), when the system is running normally in the absence of partitions, how does the system trade off latency (L) and consistency (C)?" | https://www.cs.umd.edu/~abadi/papers/abadi-pacelc.pdf |
| PostgreSQL section numbers | Confirmed for Documentation 18; cite with the version | 8.3 Character Types, 8.14 JSON Types, 8.18 Domain Types, 9.14 UUID Functions | postgresql.org/docs/current pages `datatype-character`, `datatype-json`, `domains`, `functions-uuid` |
| RFC 9562 publication date | Confirmed from page metadata | `citation_publication_date` 2024/05/07, that is 2024-05-07 | https://www.rfc-editor.org/rfc/rfc9562 (redirects to https://www.rfc-editor.org/info/rfc9562/) |
| MongoDB TransientTransactionError and UnknownTransactionCommitResult labels | Sourced; cite the page | "error handling logic for TransientTransactionError and UnknownTransactionCommitResult" | https://www.mongodb.com/docs/manual/core/transactions-in-applications/ |
| Oracle ORA-01555 | Sourced; cite the page | "ORA-01555 - snapshot too old: rollback segment number string with name "string" too small" | https://docs.oracle.com/en/error-help/db/ora-01555/ |
| MySQL section 17.7.2.1 | Sourced for MySQL 8.4 | "MySQL 8.4 Reference Manual :: 17.7.2.1 Transaction Isolation Levels" | https://dev.mysql.com/doc/refman/8.4/en/innodb-transaction-isolation-levels.html |
| Summary lesson 6, NOT VALID | The older statement that no fetched page supports this is withdrawn; Braintree 2019 supports it | "ALTER TABLE ... ADD FOREIGN KEY ... NOT VALID" | https://gist.github.com/jcoleman/1e6ad1bf8de454c166da94b67537758b |
| Gilbert and Lynch 2002 | The PDF has an extractable text layer, so "unreadable scan" no longer holds; notes may be sourced from it | "Theorem 1 It is impossible in the asynchronous network model to implement a read/write data object that guarantees the following properties:" | https://www.comp.nus.edu.sg/~gilbert/pubs/BrewersConjecture-SigAct.pdf |

### Still unconfirmed

| Item | Result | Handling |
|---|---|---|
| Kimball, keys should not encode meaning | Not found. Nearest text: "your smart keys built up out of real data" (Surrogate Keys); "Meaningless, sequentially assigned surrogate keys" (10 Essential Rules, Rule #8) | Keep as a paraphrase only. Do not attribute the sentence to Kimball. |
| DORA, "with the same rigor as production application changes" | Not found. Source text: "store their database changes as scripts in version control and manage these changes in the same way they manage production application changes" | Replace the quote with the source text. |
| "One Size Fits All", ICDE 2005 venue | Not found in the PDF text at https://cs.brown.edu/~ugur/fits_all.pdf | Source the venue elsewhere or drop it. |
| Karwin, closure table and nested set alternatives | Not found. The table of contents says only: Naive Trees, Solution: Use Alternative Tree Models | Do not name closure table or nested set as Karwin's content until the book is read. |

`22_evidence_verification.md` also holds corrected wording for the Kent, DORA, Braintree, GitLab, evodb, strong_migrations and Jepsen lines, and result-level detail for other items. Use that file before quoting any of them.

## Global rule
Most web pages were read through a summarizing fetch tool. Quotation marks on web-page citations are paraphrases unless checked. Do not present them as verbatim. Text extracted directly from PDFs with pdftotext (e.g. NIST, parts of Codd and Chen) is reliable.

## 01 PostgreSQL/MySQL
- The wiki "Don't Do This" page itemises 19 anti-patterns, not 22.

## 10 Core design
- Codd primary key quote: opening words "Normally, one domain (or combination of domains)..." are from memory; only "given relation has values which uniquely identify" onward is confirmed.
- Kent: "from multiplicative to additive", "blank fields become ambiguous", "the key, the whole key, and nothing but the key" are summaries, not verified wording.
- Kimball "Keys should not encode meaning" is a summary, not his words.
- PostgreSQL section numbers 8.3, 8.14, 8.18, 9.14 are unconfirmed; do not cite them.
- Karwin: 31 Flavors remedy and closure table / nested set alternatives are from memory; only publisher descriptions were read.
- RFC 9562: fetched excerpt confirms 2024 only; month unconfirmed.
- Conflict to include: a dbt example casts money to float, against the exact-decimal rule.

## 12 Transactions
- Remove or source: MongoDB TransientTransactionError / UnknownTransactionCommitResult labels, Oracle ORA-01555, MySQL section "17.7.2.1". All from general knowledge.
- Jepsen MySQL "permits G2-item, G-single, and lost update" and the MongoDB write-conflict sentence are paraphrases.
- PACELC definition was partly completed from memory; do not quote it.
- Gilbert & Lynch 2002 is an unreadable scan; formal content not captured. The 2012 Perspectives paper is unverified.
- DDIA "C doesn't belong in ACID" not verified against the book.

## 13 Migrations/backup
- Paraphrases, not quotes: DORA ("with the same rigor...", "Test every schema change...", "without consulting DBAs..."), Braintree 2019 ("about 2 seconds", "rollbacks must not revert"), GitLab ("Migrations must be reversible", "Prefer Arel..."), evodb ("all database artifacts are version controlled..."), strong_migrations ("blocks writes on both tables").
- Testcontainers definition ending was filled in from memory; do not use it.
- ISO 22301 details come from the EVS national record because iso.org returned 403.
- NIST quotes are reliable (PDF text).

## Status notes from agents
- 03: AWS SaaS Tenant Isolation and Storage Strategies whitepapers redirect to the SaaS Lens; CLOUD-04 is unverified. Use the SaaS Lens for silo/pool/bridge.
- 07: Gartner glossary and O'Reilly page returned 403; Gartner definitions are third-party only. Data Fabric has no independent primary source.
- 15: Airbnb Wall and Midas posts are search-snippet only. Sanderson manifesto is via InfoWorld only. Amundsen archived 2026-09-29; data-diff archived 2024-05-17.

## 11 Performance
- Key Question 7 count ("Thirty-one distinct resources (45 verified pages)") is wrong; the notes cite 58 pages.
- DDIA chapter-level claims (including chapter 3 contents) are unverified; O'Reilly returned 403.
- Oracle /23/ URLs served Oracle AI Database 26/26ai content; the query rewrite page shows no version.
- ICDE 2005 venue for "One Size Fits All" is from the brief, not the PDF text.

## 17 Case studies
- Correct count: 47 of 53 catalogued resources were fetched. Six are search-only and unverified: Pinterest Medium post, Instagram "Sharding & IDs", 4 Airbnb posts (Tracking the Money, Scaling Payment Platform, Data Quality, Minerva).
- A12 Instagram date is unknown (n.d.); the late-2011 claim is unsupported.
- A11: the claim that Snowflake IDs were the template for Instagram, Discord and Pinterest is an unsourced inference. Pinterest's ID has no time component.
- A13 TAO: "over sharded MySQL" / "over a relational store" not supported by the abstract page read.
- Summary lesson 6: "NOT VALID" is not supported by any fetched page.
- Summary lessons 2 and 4 list Instagram as evidence, but that post is unverified.
- Theme F: "record-level versioning for optimistic locking" is unsourced. For Frappe only name, creation, modified, docstatus were seen. iDempiere columns verified on the AD_Org interface only.
- From memory, do not use: gc_grace_seconds (A9), "pre-PG 11 behavior" (B6), Brandur as "former Stripe engineer" (C5).
- Not found or verified and omitted: Figma "Keeping Figma fast", Cloudflare, Stack Overflow, Netflix, Zalando, Spotify, Intuit, Monzo/Wise, Etsy, Instacart, DoorDash, Dolibarr, Heap.

## 16 Literature
- Catalog: 61 verified, 14 url_verified=false (O'Reilly, Springer, Pearson, Technics search-only/blocked; LIT-15, LIT-17, LIT-38 DOI redirect never loaded).
- Annotation details from background knowledge, not fetched pages: Karwin anti-pattern names, Force.com flex-column details, Hay and Silverston contents, PACELC system classifications, some page numbers. Do not present as source-verified.
- Authority levels: use the catalog value (LIT-39, LIT-66, LIT-74 = 4).
- Weak: LIT-02 is a DBLP record only; LIT-03 is a 5-page excerpt; LIT-13 year comes from the brief; LIT-21, LIT-22 IEEE details partly from memory.
- Date's Introduction to Database Systems 8th ed. omitted (404). Force.com whitepaper replaced by SIGMOD 2009 paper (LIT-38).
