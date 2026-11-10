# 16. Books and Research Papers: Annotated Bibliography for a Database Schema Design Framework

Research notes compiled 2026-11-07/08. Companion structured catalog: `catalog_16_literature.json` (same folder, ids LIT-01 .. LIT-75).

## Verification method and caveats

- Every URL below was either (a) opened with WebFetch, or (b) returned verbatim by WebSearch from the publisher's own domain. Where a fetch failed (HTTP 403 bot protection on dl.acm.org, oreilly.com, ieeexplore.ieee.org, sciencedirect.com, nowpublishers.com, mitpress.mit.edu; TLS or connection errors on a few author sites) this is stated per entry and the catalog carries `url_verified: false` for that URL.
- For ACM / IEEE / Elsevier papers the ACM Digital Library landing pages could not be fetched directly (HTTP 403), but each `https://doi.org/...` link was fetched and returned an HTTP 302 redirect to the matching `dl.acm.org/doi/...`, `ieeexplore.ieee.org/document/...` or `linkinghub.elsevier.com/...` record, which confirms the DOI is registered. Wherever possible the paper text itself was then verified from an author-hosted, VLDB/CIDR/USENIX, Google Research, arXiv or SIGMOD Record copy and the first page was text-extracted from the downloaded PDF to confirm title and authors.
- ISBNs are recorded only when they appeared on the publisher page or in the publisher's own URL; otherwise the field says so.
- Wikipedia and retailer listings were used only as navigation aids, never as the cited resource.

### Omitted because no official page could be verified
- C. J. Date, *An Introduction to Database Systems*, 8th ed. (Pearson/Addison-Wesley 2003/2004, ISBN 9780321197849 per retailers). The Pearson catalog URL returned by search (`pearson.com/en-nz/.../P200000003393/9780321197849`) returned HTTP 404 when fetched; no other Pearson page was confirmed before the research tool quota was exhausted.
- *Readings in Database Systems*, 4th ed. (MIT Press 2005, the collection that first printed "What Goes Around Comes Around"): `mitpress.mit.edu/9780262693141/...` returned 403 and `redbook.io` (5th ed.) reset the connection. The 2005 essay itself is still catalogued (LIT-28) via a text-verified CMU course copy.
- Kafka's NetDB 2011 workshop proceedings have no surviving official page (the Microsoft Research link listed by ODBMS.org now redirects to a generic page); the paper is catalogued (LIT-62) via a text-verified MIT course copy.
- The original Salesforce "Force.com Multitenant Architecture" whitepaper: `developer.salesforce.com/wiki/multi_tenant_architecture` returned 404 (English) / 403 (Japanese mirror). The peer-reviewed SIGMOD 2009 version by the same authors is catalogued instead (LIT-38); the current Salesforce architect page URL is noted there but was not fetched.

---

## A. Relational theory and normalization

**Takeaway.** The relational model (Codd 1970), its normalization theory (Codd 1971, Fagin 1977/1979, Kent 1983) and the ER model (Chen 1976) are the axioms of any schema design framework: tables as relations over domains, keys as the integrity anchor, functional/multivalued/join dependencies as the formal test for redundancy, and entity/relationship/attribute as the conceptual vocabulary. The modern books by Date, Hernandez, Celko, Karwin and Winand translate that theory into design rules, anti-patterns and physical-design (indexing) practice.

### LIT-01. Codd, E. F. (1970). "A Relational Model of Data for Large Shared Data Banks." *Communications of the ACM* 13(6): 377-387.
- DOI: https://doi.org/10.1145/362384.362685 (fetched; 302 -> dl.acm.org record, landing page 403 to bots). Text verified from the CACM reprint hosted at https://www.engineering.upenn.edu/~zives/03f/cis550/codd.pdf (first page extracted: "A Relational Model of Data for Large Shared Data Banks, E. F. Codd, IBM Research Laboratory, San Jose").
- Year/venue: June 1970, CACM; bibliographic record confirmed via DBLP mirror at https://www.vldb.org/dblp/db/indices/a-tree/c/Codd:E=_F=.html.
- Annotation: Codd proposed representing all data as relations (sets of tuples over named domains) and argued for *data independence*: applications must be insulated from changes in internal and even external representation. The paper introduces the first "normal form" (atomic values, no repeating groups), primary and foreign keys as the only way to express connections, and a set-oriented relational algebra/calculus as the access language. For a schema design framework it is the root of everything else: tables with declared keys, no positional or pointer-based access, and the expectation that the schema can evolve without rewriting consumers. It applies equally to OLTP and OLAP designs because both rely on relational closure and declarative query. Authority: 5 (Turing-Award-winning foundational paper).

### LIT-02. Codd, E. F. (1971). "Further Normalization of the Data Base Relational Model." IBM Research Report RJ909, San Jose; presented at Courant Computer Science Symposia 6 ("Data Base Systems"), New York, May 24-25 1971; reprinted in R. Rustin (ed.), *Data Base Systems*, Prentice-Hall, 1972.
- Verified bibliographic record: DBLP mirror https://www.vldb.org/dblp/db/indices/a-tree/c/Codd:E=_F=.html (fetched; lists "IBM Research Report RJ909, San Jose, 1971"). No DOI exists and no publisher-hosted full text could be located; the ACM Turing bibliography page (amturing.acm.org/bib/codd_1000892.cfm) returned 403.
- Annotation: This report introduced functional dependencies and defined second and third normal form, stating the objectives of normalization as removing insertion, update and deletion anomalies and making the schema neutral to query patterns. It is the formal origin of the "depends on the key" discipline used by every logical-design method. In a framework it anchors the integrity/normalization rules applied to OLTP schemas before any deliberate denormalization for OLAP. Authority: 5, but flagged: only a bibliographic record (not full text) could be verified online.

### LIT-03. Chen, P. P.-S. (1976). "The Entity-Relationship Model: Toward a Unified View of Data." *ACM Transactions on Database Systems* 1(1): 9-36.
- DOI: https://doi.org/10.1145/320434.320440 (fetched; 302 -> dl.acm.org). Text verified from the author's LSU copy https://www.csc.lsu.edu/~chen/pdf/erd-5-pages.pdf (first page extracted) and the MIT Sloan working-paper version (WP 839-76) at https://dspace.mit.edu/handle/1721.1/47638 (fetched).
- Annotation: Chen defined entities, relationships, attributes and value sets, introduced the ER diagram, and showed how to translate an ER schema into relations (entity relations and relationship relations with keys drawn from participating entities). He argued the model captures real-world semantics that network, relational and entity-set models each only partly express, and discussed implications for integrity and for mapping to both relational and network databases. For a framework it is the conceptual-modeling layer: cardinality, weak entities, identifying relationships and the conceptual-to-logical mapping step. Authority: 5.

### LIT-04. Fagin, R. (1977). "Multivalued Dependencies and a New Normal Form for Relational Databases." *ACM TODS* 2(3): 262-278.
- DOI: https://doi.org/10.1145/320557.320571 (fetched; 302). Publisher-side record: IBM Research publication page https://www.research.ibm.com/publications/multivalued-dependencies-and-a-new-normal-form-for-relational-databases (fetched; confirms TODS 1977 and DOI).
- Annotation: Fagin generalised functional dependencies to multivalued dependencies (MVDs) and defined fourth normal form, proving every relation schema can be losslessly decomposed into 4NF schemas and that 4NF is strictly stronger than BCNF. The practical rule for designers is to never store two independent multi-valued facts about the same key in one table (e.g., employee skills and employee languages). It anchors the integrity area of the framework for OLTP designs and warns dimensional modellers about "multi-valued dimension" bridge tables. Authority: 5.

### LIT-05. Fagin, R. (1979). "Normal Forms and Relational Database Operators." *Proc. ACM SIGMOD 1979*, pp. 153-160.
- DOI: https://doi.org/10.1145/582095.582120 (fetched; 302 -> portal.acm.org). IBM Research record: https://research.ibm.com/publications/normal-forms-and-relational-database-operators (fetched; "published 30 May 1979", DOI shown).
- Annotation: Fagin introduced projection-join normal form (PJ/NF, now called fifth normal form) as the strongest normal form achievable when the only decomposition operators are projection and join, and noted the Aho-Beeri-Ullman result that some 4NF schemas are still not in PJ/NF. For designers it formalises join dependencies: a table should be split only when it can be reconstructed exactly by joining its projections. The framework uses 5NF as the end-point of dependency-based normalization and as the theoretical basis for 6NF/anchor/temporal decompositions. Authority: 5.

### LIT-06. Kent, W. (1983). "A Simple Guide to Five Normal Forms in Relational Database Theory." *Communications of the ACM* 26(2): 120-125.
- DOI: https://doi.org/10.1145/358024.358054 (fetched; 302). Author-hosted HTML: http://www.bkent.net/Doc/simple5.htm (fetched; confirms CACM Vol. 26 No. 2, Feb 1983).
- Annotation: Kent restated 1NF through 5NF without relational algebra, framing each as a defence against a specific update anomaly, and gave the memorable paraphrase that every non-key field must describe "the key, the whole key, and nothing but the key". His examples (warehouse addresses, employee skills/languages, agent-company-product) remain the standard teaching cases. In a framework it is the practitioner-facing normalization checklist for OLTP review and the explanation given to stakeholders. Authority: 5 (peer-reviewed CACM), practitioner-oriented.

### LIT-07. Date, C. J. (2019). *Database Design and Relational Theory: Normal Forms and All That Jazz*, 2nd ed. Apress.
- Publisher page: https://link.springer.com/book/10.1007/978-1-4842-5540-7 (URL returned verbatim by WebSearch on the publisher domain; direct fetch redirected to a Springer cookie gate). Apress URL https://www.apress.com/gp/book/9781484255391 fetched -> 301 to link.springer.com/book/9781484255391. Springer listing (per search snippet): eBook 12 Dec 2019, softcover 16 Dec 2019, XIX+451 pp. ISBNs as shown in publisher URLs: 978-1-4842-5540-7 (eBook/DOI), 9781484255391 (softcover).
- Annotation: Date gives a rigorous but readable treatment of FDs, BCNF, dependency preservation, MVDs/4NF, JDs/5NF, 6NF, essential tuple normal form and domain-key normal form, plus his Principle of Orthogonal Design (no two base tables should have overlapping meanings) and a closing chapter on "what database design is, anyway". The second edition expands the less familiar normal forms and adds appendices including one on data consistency. For a framework it is the reference for proving a logical model correct and for deciding when 6NF (temporal/anchor) decomposition is justified. Authority: 4.

### LIT-08. Date, C. J. (2015). *SQL and Relational Theory: How to Write Accurate SQL Code*, 3rd ed. O'Reilly Media.
- Publisher page: https://www.oreilly.com/library/view/sql-and-relational/9781491941164/copy.html (URL returned verbatim by WebSearch; oreilly.com returns HTTP 403 to automated fetch, so `url_verified=false`). Edition history per O'Reilly copyright page snippet: 1st Jan 2009, 2nd Dec 2011, 3rd Oct/Nov 2015 (first release 2015-09-30); 582 pp. ISBN in URL: 9781491941164.
- Annotation: Date shows how to use SQL "relationally": no duplicate rows, no NULLs, every table with a key, constraints as the primary expression of business rules, and views as logical data independence. He maps each relational-algebra operator to SQL idioms and explains why departures (bags, three-valued logic) produce wrong answers. In a framework it anchors the DDL/constraint conventions (NOT NULL, UNIQUE, CHECK, assertions emulated by triggers) for OLTP schemas. Authority: 4.

### LIT-09. Hernandez, M. J. (2020). *Database Design for Mere Mortals: 25th Anniversary Edition* (4th ed.). Addison-Wesley Professional.
- Publisher page: https://www.informit.com/store/database-design-for-mere-mortals-25th-anniversary-edition-9780136788041 (fetched). Published 17 Dec 2020 (copyright 2021). ISBN-13 978-0-13-678804-1.
- Annotation: A vendor-neutral, requirements-driven method: interview stakeholders, build a preliminary table list, define fields with field specifications, choose keys, establish relationships and business rules, then define views and integrity. Its strength is the disciplined process (mission statement, field-level specification sheets, relationship diagrams) rather than theory. For a framework it supplies the OLTP logical-design workflow and the artefacts (field specs, business-rule specs) that a design review can check. Authority: 4.

### LIT-10. Celko, J. (2014). *Joe Celko's SQL for Smarties: Advanced SQL Programming*, 5th ed. Morgan Kaufmann/Elsevier.
- Publisher page: https://shop.elsevier.com/books/joe-celkos-sql-for-smarties/celko/978-0-12-800761-7 (fetched). Published Dec 2014. ISBN in publisher URL: 978-0-12-800761-7.
- Annotation: Celko catalogues advanced, standards-based SQL techniques: DDL design flaws, encoding schemes and auxiliary tables, transaction models, temporal/bitemporal modelling (new in the 5th edition), set-based solutions to procedural problems. He insists on ISO SQL and on data-element naming standards (ISO 11179). For a framework it provides the physical/DDL conventions for OLTP and the SQL idioms for reporting layers. Authority: 4.

### LIT-11. Celko, J. (2012). *Joe Celko's Trees and Hierarchies in SQL for Smarties*, 2nd ed. Morgan Kaufmann/Elsevier.
- Publisher page: https://shop.elsevier.com/books/joe-celkos-trees-and-hierarchies-in-sql-for-smarties/celko/978-0-12-387733-8 (fetched). Published Jan 2012. ISBN in publisher URL: 978-0-12-387733-8.
- Annotation: The reference on modelling hierarchies in relational schemas: adjacency list, path enumeration, nested sets and nested intervals, with the trade-offs of each for reads vs. writes, plus graph-theoretic background. It is the standard citation when a framework must choose a hierarchy pattern for org charts, bills of material, categories or ragged dimension hierarchies. Applies to OLTP (adjacency/closure) and OLAP (bridge/flattened hierarchies). Authority: 4.

### LIT-12. Karwin, B. (2022). *SQL Antipatterns, Volume 1: Avoiding the Pitfalls of Database Programming*. Pragmatic Bookshelf.
- Publisher page: https://pragprog.com/titles/bksap1/sql-antipatterns-volume-1/ (fetched). Published Oct 2022. ISBN 9781680508987.
- Annotation: A catalogue of named schema and query anti-patterns with symptoms, legitimate uses and fixes: Jaywalking (comma-separated lists), Naive Trees, ID Required, Keyless Entry, Entity-Attribute-Value, Polymorphic Associations, Multicolumn Attributes, Metadata Tribbles, plus query and application anti-patterns (Fear of the Unknown/NULLs, Ambiguous Groups, SQL Injection, Pseudokey Neat-Freak). It is the most directly usable schema-review checklist in this bibliography. Framework area: integrity/modelling for OLTP; the EAV and Polymorphic Association chapters are also relevant to multitenant and semi-structured designs. Authority: 3 (recognised practitioner work).

### LIT-13. Winand, M. (2012). *SQL Performance Explained*. Self-published (Vienna).
- Author/publisher page: https://sql-performance-explained.com/ (fetched). ISBN shown on site assets: 978-3-9503078-2-5. The page does not print the year; 2012 is the commonly cited first-publication year and is recorded with that caveat.
- Annotation: Explains B-tree indexes from the developer's point of view: concatenated index column order, index-only scans, function-based indexes, how WHERE/JOIN/ORDER BY use indexes, keyset pagination instead of OFFSET, and reading execution plans across Oracle, SQL Server, PostgreSQL and MySQL. For a framework it supplies the physical-design rules (indexing strategy, access-path-aware key design) that follow logical modelling for OLTP. Authority: 3.

---

## B. Transactions and consistency

**Takeaway.** Gray defined the transaction, Haerder and Reuter named ACID and the recovery taxonomy, Berenson et al. exposed the gaps in SQL isolation levels and defined snapshot isolation, Garcia-Molina and Salem supplied the saga pattern for long-running work, and Bailis et al. mapped which guarantees survive partitions. Together they define the transaction/integrity area of the framework: what the schema can rely on the engine for, and what must be designed in (idempotency, compensation, uniqueness under weak isolation).

### LIT-14. Gray, J. (1981). "The Transaction Concept: Virtues and Limitations." *Proc. 7th VLDB*, Cannes, pp. 144-154. Also Tandem Technical Report TR 81.3 (June 1981).
- Verified copy: Jim Gray's archived publication list hosted by Microsoft, https://jimgray.azurewebsites.net/papers/thetransactionconcept.pdf (fetched; first page extracted: "Tandem TR 81.3 ... Jim Gray ... June 1981"). The vldb.org 1981 proceedings PDF (P144.PDF) returned 404.
- Annotation: Gray defined a transaction as a state transformation with atomicity, durability and consistency (isolation was added by Haerder and Reuter), surveyed logging, locking and two-phase commit implementations, and posed open problems: transactions over abstract data types, nested transactions, and long-lived transactions lasting days. For a framework it establishes why schema-level integrity (keys, constraints) can be trusted only inside transaction boundaries and why long business processes need other designs (see Sagas). Applies to OLTP and to the transactional layers of lakehouses. Authority: 5.

### LIT-15. Haerder, T. and Reuter, A. (1983). "Principles of Transaction-Oriented Database Recovery." *ACM Computing Surveys* 15(4): 287-317.
- DOI: https://doi.org/10.1145/289.291 (fetched; 302 -> dl.acm.org, which returns 403 to bots). Full text not fetched (course-hosted copies exist but tool quota was exhausted); bibliographic details confirmed by multiple search records (vol. 15 no. 4, Dec 1983).
- Annotation: This survey coined the ACID acronym and built a vocabulary for recovery: UNDO/REDO, page propagation (ATOMIC vs NOT-ATOMIC), buffer policies (STEAL/NO-STEAL, FORCE/NO-FORCE) and four checkpoint types, allowing any recovery scheme to be classified. For schema designers it explains the durability guarantees under which constraints hold and why write-ahead logging shapes engine choices (and later, Delta Lake's log-based design). Authority: 5.

### LIT-16. Berenson, H., Bernstein, P., Gray, J., Melton, J., O'Neil, E., O'Neil, P. (1995). "A Critique of ANSI SQL Isolation Levels." *Proc. ACM SIGMOD 1995*, pp. 1-10. Also Microsoft Research TR MSR-TR-95-51.
- DOI: https://doi.org/10.1145/223784.223785 (fetched; 302). Open copies: arXiv https://arxiv.org/abs/cs/0701157 (fetched; lists the SIGMOD 1995 journal reference) and Microsoft Research https://www.microsoft.com/en-us/research/publication/a-critique-of-ansi-sql-isolation-levels/ (fetched).
- Annotation: The authors show that SQL-92's phenomenon-based isolation levels are ambiguous and fail to characterise common lock-based implementations, define additional phenomena (dirty write, lost update, read skew, write skew) and formally define Snapshot Isolation, noting it is not serializable. For a framework it determines which uniqueness and referential rules can be enforced by constraints versus application logic under MVCC engines (PostgreSQL, Oracle, Snowflake, Spanner-like systems) and why write-skew-prone invariants need SERIALIZABLE or explicit locks. Authority: 5.

### LIT-17. Garcia-Molina, H. and Salem, K. (1987). "Sagas." *Proc. ACM SIGMOD 1987*, pp. 249-259.
- DOI: https://doi.org/10.1145/38713.38742 (fetched; 302 -> portal.acm.org). The Princeton tech-report page (TR-070-87) returned 404; full text not fetched.
- Annotation: A saga is a long-lived transaction written as a sequence of sub-transactions T1..Tn each with a compensating transaction C1..Cn; the system guarantees either all Ti complete or compensations undo the partial execution, trading isolation for availability. The pattern underlies modern microservice and event-driven consistency designs. In a framework it anchors schema provisions for compensation: idempotency keys, outbox tables, status/state columns and auditable step records in OLTP and streaming systems. Authority: 5.

### LIT-18. Bailis, P., Davidson, A., Fekete, A., Ghodsi, A., Hellerstein, J. M., Stoica, I. (2014). "Highly Available Transactions: Virtues and Limitations." *PVLDB* 7(3): 181-192 (VLDB 2014).
- DOI: https://doi.org/10.14778/2732232.2732237 (fetched; 302). Open copy: https://www.vldb.org/pvldb/vol7/p181-bailis.pdf (fetched; first page extracted).
- Annotation: Surveying 18 databases, the authors show most default to weak isolation, then prove which guarantees can be offered with high availability under partitions (Read Committed, Monotonic Atomic View, causal/session guarantees) and which cannot (Serializability, Snapshot Isolation, Repeatable Read, linearizability). For a framework this is the decision table for distributed OLTP schemas: which invariants (e.g., global uniqueness, foreign-key existence) require coordination and which can be relaxed. Authority: 5.

---

## C. Distributed systems and CAP

**Takeaway.** Brewer's conjecture, its proof (Gilbert and Lynch 2002), the 2012 retrospective, Abadi's PACELC refinement and Kleppmann's critique define how to reason about consistency vs. availability vs. latency. Raft shows how replicated state is kept consistent; Dynamo, Bigtable and Spanner are the three archetypal schema philosophies of distributed stores (schemaless key-value, wide-column with designed row keys, and globally consistent semi-relational with interleaved tables).

### LIT-19. Brewer, E. A. (2000). "Towards Robust Distributed Systems." Keynote, *ACM PODC 2000* (abstract in proceedings).
- DOI (abstract): https://doi.org/10.1145/343477.343502 (fetched; 302). Keynote slides, author-hosted: https://people.eecs.berkeley.edu/~brewer/cs262b-2004/PODC-keynote.pdf (fetched; first page extracted "PODC Keynote, July 19, 2000").
- Annotation: Brewer stated the CAP conjecture (a shared-data system can have at most two of consistency, availability, partition tolerance) and contrasted ACID with BASE, arguing that internet-scale services should trade consistency for availability and reason in terms of harvest and yield. For a framework it is the origin of the C/A trade-off every distributed schema decision (replication factor, quorum, conflict handling) must document. Authority: 5 (invited keynote at a peer-reviewed venue; the formal proof is LIT-20).

### LIT-20. Gilbert, S. and Lynch, N. (2002). "Brewer's Conjecture and the Feasibility of Consistent, Available, Partition-Tolerant Web Services." *ACM SIGACT News* 33(2): 51-59.
- DOI: https://doi.org/10.1145/564585.564601 (fetched; 302). Author copy: https://www.comp.nus.edu.sg/~gilbert/pubs/BrewersConjecture-SigAct.pdf (fetched; first page extracted).
- Annotation: Formal proof of CAP in the asynchronous network model (with atomic/linearizable consistency), followed by a discussion of weaker but achievable guarantees in the partially synchronous model. It fixes the precise meanings of the three terms so that later debates (PACELC, Kleppmann) are well-posed. In a framework it anchors the definitions used when a design declares a consistency model. Authority: 5.

### LIT-21. Gilbert, S. and Lynch, N. (2012). "Perspectives on the CAP Theorem." *IEEE Computer* 45(2): 30-36.
- DOI: https://doi.org/10.1109/MC.2011.389 (fetched; 302 -> ieeexplore document 6122006). Author copy: https://groups.csail.mit.edu/tds/papers/Gilbert/Brewer2.pdf (fetched; first page extracted).
- Annotation: Twelve years on, the authors place CAP within the broader impossibility results of distributed computing and describe practical coping strategies: segmenting data and operations by consistency need, using weaker consistency where safe, and designing for partition recovery. For a framework it motivates classifying each table/aggregate by required consistency rather than choosing one global model. Authority: 5.

### LIT-22. Abadi, D. J. (2012). "Consistency Tradeoffs in Modern Distributed Database System Design: CAP Is Only Part of the Story." *IEEE Computer* 45(2): 37-42.
- DOI: https://doi.org/10.1109/MC.2012.33 (fetched; 302 -> ieeexplore document 6127847). Author copy: https://www.cs.umd.edu/~abadi/papers/abadi-pacelc.pdf (fetched; first page extracted: IEEE Computer cover feature, February 2012).
- Annotation: Abadi argues CAP is widely misapplied because it constrains behaviour only during partitions; the everyday trade-off is latency vs. consistency. PACELC (if Partition: Availability vs Consistency; Else: Latency vs Consistency) classifies systems such as Dynamo/Cassandra/Riak (PA/EL), PNUTS (PC/EL) and VoltDB/Megastore (PC/EC). For a framework it is the vocabulary for documenting replication and read-path decisions of distributed OLTP and streaming stores. Authority: 5.

### LIT-23. Kleppmann, M. (2015). "A Critique of the CAP Theorem." arXiv:1509.05393 [cs.DC].
- URL: https://arxiv.org/abs/1509.05393 (fetched; v1 17 Sep 2015, v2 18 Sep 2015).
- Annotation: Kleppmann documents inconsistent definitions of consistency, availability and partition in the CAP literature, questions the claim that eventually consistent systems are "more available", and proposes delay-sensitivity (how operation latency grows with network delay) as a more useful analytical lens. For a framework it cautions against labelling a schema "AP" or "CP" and recommends stating concrete guarantees per operation. Authority: 4 (influential preprint by a recognised researcher; not peer-reviewed in this form).

### LIT-24. Ongaro, D. and Ousterhout, J. (2014). "In Search of an Understandable Consensus Algorithm." *Proc. USENIX ATC 2014*, pp. 305-319 (Best Paper).
- Official page: https://www.usenix.org/conference/atc14/technical-sessions/presentation/ongaro (fetched). Extended version: https://raft.github.io/raft.pdf (fetched; first page extracted).
- Annotation: Raft decomposes consensus into leader election, log replication and safety, adds joint-consensus membership changes and (extended version) log compaction, producing a replicated log equivalent to multi-Paxos but easier to implement. Raft underlies CockroachDB, TiDB, etcd and many NewSQL engines. In a framework it explains the replication substrate whose properties (leader-based writes, quorum commits) constrain latency-sensitive OLTP schema partitioning. Authority: 5.

### LIT-25. DeCandia, G. et al. (2007). "Dynamo: Amazon's Highly Available Key-value Store." *Proc. ACM SOSP 2007*, pp. 205-220.
- DOI: https://doi.org/10.1145/1294261.1294281 (fetched; 302). Author-hosted copy (Werner Vogels): https://www.allthingsdistributed.com/files/amazon-dynamo-sosp2007.pdf (fetched; first page extracted).
- Annotation: Dynamo combines consistent hashing, vector clocks, sloppy quorums with hinted handoff, Merkle-tree anti-entropy and gossip membership to give an always-writable key-value store with application-resolved conflicts. It is the template for Cassandra, Riak and DynamoDB and for "design the schema around the access key" thinking. In a framework it anchors the schemaless/aggregate-per-key pattern and the need for conflict-resolution and idempotency rules in distributed OLTP. Authority: 5.

### LIT-26. Chang, F., Dean, J., Ghemawat, S. et al. (2006). "Bigtable: A Distributed Storage System for Structured Data." *Proc. OSDI 2006*, pp. 205-218; journal version *ACM TOCS* 26(2), 2008.
- Google Research page: https://research.google/pubs/bigtable-a-distributed-storage-system-for-structured-data/ (fetched). TOCS DOI: https://doi.org/10.1145/1365815.1365816 (fetched; 302).
- Annotation: Bigtable is a sparse, distributed, persistent multidimensional sorted map indexed by (row key, column family, timestamp), stored as SSTables in tablets over GFS with Chubby for coordination. Its design lessons: choose row keys for locality and scan patterns, group columns into families by access, and keep versions by timestamp. For a framework it anchors wide-column modelling (HBase, Cassandra CQL, Bigtable) where the row-key design *is* the schema. Authority: 5.

### LIT-27. Corbett, J. C., Dean, J. et al. (2012). "Spanner: Google's Globally-Distributed Database." *Proc. OSDI 2012* (Best Paper); journal version *ACM TOCS* 31(3), 2013.
- Official page: https://www.usenix.org/conference/osdi12/technical-sessions/presentation/corbett (fetched). TOCS DOI: https://doi.org/10.1145/2491245 (fetched; 302).
- Annotation: Spanner provides externally consistent distributed transactions across datacentres using TrueTime (clock-uncertainty-aware timestamps), Paxos-replicated tablets, lock-free snapshot reads and atomic schema changes; its semi-relational schema lets tables be interleaved in parent tables so related rows are co-located. For a framework it shows that globally consistent OLTP schemas are feasible and introduces interleaving/co-location as a schema-level partitioning decision (now also in Cloud Spanner, CockroachDB). Authority: 5.

---

## D. Storage engines, system architecture and data-platform papers

**Takeaway.** The Stonebraker essays (2005, 2024) argue that the relational model and SQL absorb every challenger; "One Size Fits All" and C-Store justify specialised OLAP engines and columnar storage; Dremel, Snowflake, Delta Lake and Lakehouse define the cloud analytics stack; NewSQL and Force.com cover distributed OLTP and multitenant metadata-driven schemas. These papers determine *which* physical schema patterns (columnar, nested, micro-partitioned, log-structured tables) a framework should prescribe for each workload.

### LIT-28. Stonebraker, M. and Hellerstein, J. M. (2005). "What Goes Around Comes Around." In *Readings in Database Systems*, 4th ed., MIT Press, pp. 2-41.
- Verified copy: CMU 15-721 course reading https://15721.courses.cs.cmu.edu/spring2020/papers/01-intro/whatgoesaround-stonebraker.pdf (fetched; first page extracted: title, authors, abstract "35 years of data model proposals, grouped into 9 different eras"). MIT Press catalog page returned 403; no official full-text page verified.
- Annotation: The essay reviews nine eras of data models (hierarchical/IMS, network/CODASYL, relational, entity-relationship, extended relational, semantic, object-oriented, object-relational, semi-structured/XML) and extracts lessons: physical data independence matters, complex models fail without a killer app, and new proposals usually re-implement old ideas. For a framework it justifies defaulting to the relational model while borrowing selectively (JSON columns, UDTs) and warns against schema-less designs that reintroduce CODASYL-style navigation. Authority: 5 (two leading researchers; published in an MIT Press collection).

### LIT-29. Stonebraker, M. and Pavlo, A. (2024). "What Goes Around Comes Around... And Around..." *ACM SIGMOD Record* 53(2): 21-37 (June 2024).
- Official SIGMOD Record page: https://sigmodrecord.org/2024/06/30/what-goes-around-comes-around-and-around (fetched; PDF download link present). Author copy: https://db.cs.cmu.edu/papers/2024/whatgoesaround-sigmodrec2024.pdf (fetched; first page extracted). DOI not confirmed (a candidate DOI resolved to dl.acm.org but its title could not be checked), so none is recorded.
- Annotation: Twenty years on, the authors review MapReduce, key-value, document, column-family, text-search, array, vector and graph systems and argue that SQL/RM again absorbed the useful ideas (JSON, arrays, vector indexes) while most alternatives converged back to SQL; they then survey architectural shifts (columnar, cloud, data lakes/lakehouses, NewSQL, hardware accelerators, blockchain). For a framework it is the most current authoritative argument for a relational core with multi-model extensions across OLTP and OLAP. Authority: 5.

### LIT-30. Hellerstein, J. M., Stonebraker, M., Hamilton, J. (2007). "Architecture of a Database System." *Foundations and Trends in Databases* 1(2): 141-259.
- DOI: https://doi.org/10.1561/1900000002 (fetched; 302 -> https://www.emerald.com/ftdbs/article/1/2/141/1331441/Architecture-of-a-Database-System, which was fetched and confirms authors, volume, pages and publication date 7 Nov 2007).
- Annotation: A systems-level tour of a relational DBMS "by the life of a query": process models, parallel architectures (shared-nothing/-disk/-memory), storage management, transactions (locking, latching, logging/ARIES), query processing and optimisation, and shared components (catalog, memory, replication). It explains the mechanisms that make schema choices (index type, partitioning, row vs column layout) matter for performance. Framework area: storage/physical design for both OLTP and OLAP. Authority: 5.

### LIT-31. Stonebraker, M. and Cetintemel, U. (2005). "'One Size Fits All': An Idea Whose Time Has Come and Gone." *Proc. IEEE ICDE 2005*, pp. 2-11.
- DOI: https://doi.org/10.1109/ICDE.2005.1 (fetched; 302 -> ieeexplore document 1410100). Author copy: https://cs.brown.edu/~ugur/fits_all.pdf (fetched; first page extracted).
- Annotation: The authors argue that a single general-purpose RDBMS engine cannot serve stream processing, data warehousing, text and scientific workloads competitively, demonstrating one- to two-order-of-magnitude gaps for specialised engines. This is the intellectual charter for separating OLTP and OLAP schemas and engines (row-store transactional systems vs column-store warehouses vs stream processors). Authority: 5.

### LIT-32. Stonebraker, M., Abadi, D. J., Batkin, A. et al. (2005). "C-Store: A Column-oriented DBMS." *Proc. 31st VLDB*, pp. 553-564.
- Official proceedings copy: https://www.vldb.org/archives/website/2005/program/paper/thu/p553-stonebraker.pdf (fetched; first page extracted).
- Annotation: C-Store stores overlapping sorted projections column-wise with heavy compression, splits a write-optimised store from a read-optimised store joined by a tuple mover, and achieves recovery through K-safety replication of projections; it became Vertica. Design lessons for a framework: columnar layout, sort-order/projection design and late materialisation are the physical-schema levers for OLAP and warehouse workloads. Authority: 5.

### LIT-33. Melnik, S., Gubarev, A., Long, J. J. et al. (2010). "Dremel: Interactive Analysis of Web-Scale Datasets." *PVLDB* 3(1-2): 330-339.
- Google Research page: https://research.google/pubs/dremel-interactive-analysis-of-web-scale-datasets-2/ (fetched). DOI: https://doi.org/10.14778/1920841.1920886 (fetched; 302).
- Annotation: Dremel introduced a columnar representation for nested records (repetition and definition levels) and multi-level serving trees, enabling SQL aggregation over trillion-row nested datasets in seconds; it is the ancestor of BigQuery and the Parquet file format. For a framework it legitimises nested/repeated fields in analytical schemas and explains how Parquet/BigQuery store them, which shapes lakehouse and warehouse modelling of semi-structured data. Authority: 5.

### LIT-34. Dageville, B., Cruanes, T., Zukowski, M. et al. (2016). "The Snowflake Elastic Data Warehouse." *Proc. ACM SIGMOD 2016*, pp. 215-226.
- DOI: https://doi.org/10.1145/2882903.2903741 (fetched; 302). Vendor page: https://www.snowflake.com/resource/sigmod-2016-paper-snowflake-elastic-data-warehouse/ (fetched; registration-gated download). Text verified from a course-hosted copy https://www.cs.purdue.edu/homes/csjgwang/CloudNativeDB/SnowflakeSIGMOD16.pdf (fetched; first page extracted with full author list).
- Annotation: Snowflake's multi-cluster shared-data architecture separates storage (immutable micro-partitions in object storage with min/max pruning metadata) from elastic virtual warehouses, automatically columnarises semi-structured VARIANT data, and offers time travel and zero-copy cloning via versioned metadata. For a framework it defines cloud-warehouse physical design: no indexes, clustering keys instead of partitions, schema-on-read for VARIANT, and metadata-driven time travel. Authority: 5.

### LIT-35. Armbrust, M., Das, T., Sun, L. et al. (2020). "Delta Lake: High-Performance ACID Table Storage over Cloud Object Stores." *PVLDB* 13(12): 3411-3424.
- Official copy: https://www.vldb.org/pvldb/vol13/p3411-armbrust.pdf (fetched; first page extracted). DOI: https://doi.org/10.14778/3415478.3415560 (fetched; 302).
- Annotation: Delta Lake adds ACID transactions to Parquet files on object storage through a write-ahead transaction log (JSON actions plus Parquet checkpoints), optimistic concurrency, time travel, schema enforcement and evolution, Z-order clustering and streaming ingestion. For a framework it supplies the data-lake table contract: declared schemas, constraint checks and versioned tables are now available in the lake, enabling warehouse-style modelling on open formats. Authority: 5.

### LIT-36. Armbrust, M., Ghodsi, A., Xin, R., Zaharia, M. (2021). "Lakehouse: A New Generation of Open Platforms that Unify Data Warehousing and Advanced Analytics." *Proc. CIDR 2021*.
- Official copy: https://www.cidrdb.org/cidr2021/papers/cidr2021_paper17.pdf (fetched; first page extracted).
- Annotation: The paper argues the two-tier lake-plus-warehouse architecture is costly and stale and proposes the lakehouse: open direct-access formats, a transactional metadata layer, first-class ML support and warehouse-grade performance via caching, auxiliary data structures and layout optimisation. For a framework it reframes the warehouse/lake split as a layering question (bronze/silver/gold on open tables) and positions dimensional and Data Vault models on top of lakehouse tables. Authority: 5.

### LIT-37. Pavlo, A. and Aslett, M. (2016). "What's Really New with NewSQL?" *ACM SIGMOD Record* 45(2): 45-55.
- DOI: https://doi.org/10.1145/3003665.3003674 (fetched; 302). Author copy: https://db.cs.cmu.edu/papers/2016/pavlo-newsql-sigmodrec2016.pdf (fetched; first page extracted).
- Annotation: Defines NewSQL as systems that scale OLTP with SQL and ACID, classifies them (new architectures, transparent sharding middleware, DBaaS) and compares main-memory storage, partitioning, concurrency control, secondary indexes, replication and recovery. For a framework it is the reference for distributed-OLTP schema concerns: choosing a partitioning key, co-locating related tables, and the cost of global secondary indexes. Authority: 5.

### LIT-38. Weissman, C. D. and Bobrowski, S. (2009). "The Design of the Force.com Multitenant Internet Application Development Platform." *Proc. ACM SIGMOD 2009*, pp. 889-896. (Peer-reviewed version of the Salesforce whitepaper "The Force.com Multitenant Architecture".)
- DOI: https://doi.org/10.1145/1559845.1559942 (fetched; 302 -> dl.acm.org). Salesforce's current architect page URL https://architect.salesforce.com/fundamentals/platform-multitenant-architecture was returned verbatim by WebSearch but not fetched (quota); the original developer-wiki whitepaper URL returned 404.
- Annotation: Force.com stores all tenants in one shared schema driven by metadata: a Universal Data Dictionary describes tenant objects, a wide Data table with generic "flex" value columns holds rows, and pivot tables provide indexes, uniqueness and relationships, with a tenant-aware optimiser using per-tenant statistics. For a framework it is the canonical reference for metadata-driven multitenant schema design and its trade-offs versus schema-per-tenant or database-per-tenant. Authority: 5 for the SIGMOD paper (industry paper, peer-reviewed).

### LIT-39. Petrov, A. (2019). *Database Internals: A Deep Dive into How Distributed Data Systems Work*. O'Reilly Media.
- Publisher page: https://www.oreilly.com/library/view/database-internals/9781492040330/ (URL returned verbatim by WebSearch; direct fetch 403, `url_verified=false`). Released Oct 2019, 370 pp. ISBN in URL: 9781492040330.
- Annotation: Part I covers storage engines (B-trees and variants, LSM trees, page cache, buffer pool, write-ahead log, file formats); Part II covers distributed systems (failure detection, leader election, replication and consistency models, anti-entropy, consensus with Paxos/Raft). For a framework it explains why primary-key choice, row width and write patterns interact with B-tree vs LSM engines, and provides the vocabulary for consistency decisions. Authority: 3-4 (well-regarded practitioner synthesis).

### LIT-40. Silberschatz, A., Korth, H. F., Sudarshan, S. (2019). *Database System Concepts*, 7th ed. McGraw-Hill.
- Publisher page: https://www.mheducation.com/highered/product/database-system-concepts-silberschatz-korth/M9780078022159.html (fetched; ISBN-13 9780078022159, copyright 2020). Author companion site: https://www.db-book.com/ (fetched; "Seventh Edition ... released March 2019").
- Annotation: The standard textbook: relational model and SQL, ER modelling and normalisation, storage and indexing, query processing, transactions and recovery, parallel/distributed databases, and (7th ed.) big-data and blockchain chapters. For a framework it is the citation for textbook definitions (normal forms, ER-to-relational mapping, isolation levels) and classroom-standard notation. Authority: 4.

### LIT-41. Elmasri, R. and Navathe, S. B. (2015). *Fundamentals of Database Systems*, 7th ed. Pearson.
- Publisher page: https://www.pearson.com/en-us/subject-catalog/p/fundamentals-of-database-systems/P200000003546/9780133970777 (fetched; lists the 2015 hardcover ISBN 9780133970777 and a 2021 Pearson+ edition 9780137502523).
- Annotation: Comprehensive coverage of ER and EER modelling (specialisation/generalisation, categories), relational algebra and SQL, functional dependencies and normalisation algorithms, physical design and tuning, transaction processing, distributed and NoSQL databases. Its EER-to-relational mapping algorithm (seven steps) is frequently cited in design frameworks. Authority: 4.

### LIT-42. Garcia-Molina, H., Ullman, J. D., Widom, J. (2008). *Database Systems: The Complete Book*, 2nd ed. Pearson/Prentice Hall.
- Publisher page: https://www.pearson.com/en-us/subject-catalog/p/database-systems-the-complete-book/P200000003515/9780133002010 (URL returned verbatim by WebSearch; fetch not completed due to tool quota, `url_verified=false`). Stanford author page (infolab.stanford.edu/~ullman/dscb.html) refused the connection. 2nd ed. 2008 (ISBN 9780131873254 per Pearson search snippet; 2011 reissue ISBN 9780133002010 in URL).
- Annotation: Divides the subject into design/use (ER, relational, dependency theory, SQL, constraints, views, XML) and implementation (storage, indexes, query execution/optimisation, transactions, concurrency, distributed databases, information integration). Its dependency-theory chapters (closure, minimal basis, chase) give the algorithms a framework can use to verify decompositions. Authority: 4.

---

## E. Data warehousing and data modelling methods

**Takeaway.** Kimball (dimensional), Inmon (normalised EDW/CIF and lakehouse), Linstedt (Data Vault 2.0), Ronnback (Anchor Modeling) and Corr (BEAM) are the competing warehouse modelling schools; Simsion and Witt, Hoberman, Silverston and Hay provide enterprise/conceptual modelling method, quality scoring and reusable pattern libraries. A framework should treat these as selectable modelling styles with explicit criteria.

### LIT-43. Kimball, R. and Ross, M. (2013). *The Data Warehouse Toolkit: The Definitive Guide to Dimensional Modeling*, 3rd ed. Wiley.
- Publisher page: https://www.wiley.com/en-us/-p-9781118530801 (fetched). Published July 2013. ISBN 978-1-118-53080-1 (paperback), 978-1-118-73228-1 (e-book).
- Annotation: The definitive dimensional-modelling text: the four-step design process (business process, grain, dimensions, facts), star schemas, conformed dimensions and the enterprise bus matrix, slowly changing dimension types 0-7, degenerate/junk/role-playing dimensions, factless and accumulating-snapshot facts, bridge tables for many-to-many and ragged hierarchies, with twelve industry case studies and two ETL chapters. It anchors the OLAP/warehouse modelling area of any framework. Authority: 4 (canonical practitioner reference).

### LIT-44. Kimball, R. and Caserta, J. (2004). *The Data Warehouse ETL Toolkit: Practical Techniques for Extracting, Cleaning, Conforming, and Delivering Data*. Wiley.
- Publisher page: https://www.wiley.com/en-us/-p-9780764567575 (fetched). Published Oct 2004. ISBN 978-0-7645-6757-5.
- Annotation: Covers the staging/ETL architecture that feeds dimensional models: extraction and change data capture, data-quality screens and error event schemas, conforming dimensions, the surrogate-key pipeline, SCD processing, late-arriving facts and dimensions, audit dimensions, and real-time ETL. For a framework it specifies the pipeline-side schema objects (staging tables, key maps, audit/error tables) that a warehouse design must include. Authority: 4.

### LIT-45. Inmon, W. H. (2005). *Building the Data Warehouse*, 4th ed. Wiley.
- Publisher page: https://www.wiley.com/en-us/-p-9780764599446 (fetched). Published Oct 2005. ISBN 978-0-7645-9944-6.
- Annotation: Inmon's definition of the warehouse as a subject-oriented, integrated, time-variant, non-volatile collection, the Corporate Information Factory with a normalised enterprise warehouse feeding dependent data marts, granularity and partitioning decisions, and the 4th edition's treatment of unstructured data and multiple storage tiers. For a framework it is the counterpoint to Kimball: a 3NF integration layer with dimensional marts downstream (the hub-and-spoke that Data Vault later formalised). Authority: 4.

### LIT-46. Inmon, W. H., Levins, M., Srivastava, R. (2021). *Building the Data Lakehouse*. Technics Publications.
- Publisher collection page: https://technicspub.com/data-lakehouse-collection/ (URL returned verbatim by WebSearch; fetch not completed due to tool quota, `url_verified=false`). ISBN 9781634629669 per retailer/library records (not confirmed on publisher page). A 2nd edition appeared in 2023 under the title *Rise of the Data Lakehouse*.
- Annotation: Positions the lakehouse as the successor to both the warehouse and the lake, describes the analytical infrastructure required, and introduces a "universal common connector" to integrate structured, textual and analog/IoT data. It is the Inmon-school view of the lakehouse, complementary to the Databricks CIDR paper (LIT-36). Framework area: warehousing/data lake architecture. Authority: 3 (practitioner book from a specialist publisher).

### LIT-47. Linstedt, D. and Olschimke, M. (2015). *Building a Scalable Data Warehouse with Data Vault 2.0*. Morgan Kaufmann/Elsevier.
- Publisher page: https://shop.elsevier.com/books/building-a-scalable-data-warehouse-with-data-vault-20/linstedt/978-0-12-802510-9 (fetched). Published Sept 2015. ISBN 9780128025109.
- Annotation: The reference for Data Vault 2.0: hubs (business keys), links (relationships) and satellites (descriptive, historised attributes) with hash keys, load dates and record sources; raw vault vs business vault; point-in-time and bridge tables for query performance; and an agile delivery methodology with SQL Server Integration Services, Data Quality Services and Master Data Services examples. For a framework it defines the integration-layer pattern optimised for auditability and parallel loading. Authority: 4.

### LIT-48. Ronnback, L., Regardt, O., Bergholtz, M., Johannesson, P., Wohed, P. (2010). "Anchor Modeling: Agile Information Modeling in Evolving Data Environments." *Data & Knowledge Engineering* 69(12): 1229-1253.
- DOI: https://doi.org/10.1016/j.datak.2010.09.002 (fetched; 302 -> linkinghub.elsevier.com record S0169023X1000114X; ScienceDirect returns 403 to bots). Author publications page listing the preprint: https://www.anchormodeling.com/publications/ (fetched; preprint link https://www.anchormodeling.com/wp-content/uploads/2011/05/Anchor-Modeling.pdf).
- Annotation: Anchor Modeling decomposes information into anchors (entities), attributes, ties (relationships) and knots (shared values) in sixth normal form, so schema evolution happens only by adding tables, history is captured per attribute, and views plus table-elimination in the optimiser hide the decomposition. For a framework it is the peer-reviewed basis for 6NF/ensemble modelling and for evaluating Data Vault-style approaches. Authority: 5.

### LIT-49. Corr, L. with Stagnitto, J. (2011). *Agile Data Warehouse Design: Collaborative Dimensional Modeling, from Whiteboard to Star Schema*. DecisionOne Press.
- Publisher/author pages: http://www.decisionone.co.uk/ and sampler http://www.decisionone.co.uk/press/agile-data-warehouse-design-sampler.pdf (URLs returned verbatim by WebSearch; fetch failed with a TLS certificate error, `url_verified=false`). ISBN 978-0-9568172-0-4 and first edition Nov 2011 per the sampler snippet.
- Annotation: Introduces BEAM (Business Event Analysis and Modeling): capture business events as "7W" stories (who, what, when, where, how many, why, how), modelstorm them with stakeholders using example data tables, then translate to star schemas using a catalogue of dimensional design patterns. For a framework it supplies the requirements-to-star-schema workflow and collaborative modelling practice. Authority: 3.

### LIT-50. Simsion, G. and Witt, G. (2004). *Data Modeling Essentials*, 3rd ed. Morgan Kaufmann/Elsevier.
- Publisher page: https://shop.elsevier.com/books/data-modeling-essentials/simsion/978-0-12-644551-0 (fetched). Published 3 Dec 2004. ISBN in publisher URL: 978-0-12-644551-0.
- Annotation: Treats data modelling as design (choices among valid alternatives) rather than description, covering conceptual/logical/physical stages, normalisation, subtypes and generalisation, business rules, time-dependent data, and warehouse and enterprise models. Its emphasis on evaluating alternative models against criteria (stability, flexibility, communication) is directly reusable as framework review criteria. Authority: 4.

### LIT-51. Hoberman, S. (2009). *Data Modeling Made Simple: A Practical Guide for Business and IT Professionals*, 2nd ed. Technics Publications.
- Publisher page: https://technicspub.com/data-modeling-made-simple/ (URL returned verbatim by WebSearch; fetch not completed due to tool quota, `url_verified=false`). 2nd ed. 2009, ISBN 9780977140060 per library catalogue (not confirmed on publisher page).
- Annotation: An accessible introduction organised from conceptual to logical to physical models, covering entities, attributes, relationships, keys, normalisation, abstraction, subject-area models and dimensional models, with templates for model reviews. For a framework it provides the vocabulary and the "levels of model" structure used by DAMA and most enterprise modelling practices. Authority: 3.

### LIT-52. Hoberman, S. (2015). *Data Model Scorecard: Applying the Industry Standard on Data Model Quality*. Technics Publications.
- Publisher page: https://technicspub.com/data-model-scorecard/ (fetched; lists the ten categories). ISBN 9781634620826 appears in the publisher's cover-image filename and retailer listings; year 2015 per library records.
- Annotation: Defines a ten-category quality scorecard for data models (Correctness, Completeness, Scheme, Structure, Abstraction, Standards, Readability, Definitions, Consistency, Data) with examples, review preparation, and a case study. It is the most directly adoptable model-governance instrument in this bibliography and maps naturally to a framework's review gate. Framework area: governance/modelling quality. Authority: 3.

### LIT-53. Silverston, L. (2001). *The Data Model Resource Book, Volume 1: A Library of Universal Data Models for All Enterprises*, revised ed. Wiley.
- Publisher page: https://www.wiley.com/en-us/-p-9780471380238 (fetched). Published March 2001. ISBN 978-0-471-38023-8.
- Annotation: Reusable logical models for the functions common to most enterprises: party and party roles/relationships, products, orders, shipments, invoicing and accounting, work effort and human resources, plus star-schema versions of each. For a framework it offers vetted starting points for ERP-style OLTP domains and shows how universal models become warehouse marts. Authority: 4.

### LIT-54. Silverston, L. (2001). *The Data Model Resource Book, Volume 2: A Library of Universal Data Models by Industry Types*, revised ed. Wiley.
- Publisher page: https://www.wiley.com/en-us/-p-9780471353485 (fetched). Published March 2001. ISBN 978-0-471-35348-5.
- Annotation: Extends Volume 1 with industry models (manufacturing, telecommunications, health care, insurance, financial services, professional services, travel, e-commerce), each adapting the universal party/product/agreement structures. For a framework it shows how to specialise generic patterns without breaking the shared core. Authority: 4.

### LIT-55. Silverston, L. and Agnew, P. (2009). *The Data Model Resource Book, Volume 3: Universal Patterns for Data Modeling*. Wiley.
- Publisher page: https://www.wiley.com/en-us/-p-9780470178454 (fetched). Published Jan 2009. ISBN 978-0-470-17845-4.
- Annotation: Abstracts the earlier volumes into pattern levels (specific, generalised, universal) for roles, hierarchies and classifications, statuses, contact mechanisms, business rules and recursive relationships, and discusses when to apply each level of abstraction. For a framework it is the guide to choosing the abstraction level of an OLTP model (and avoiding over-generalised EAV designs). Authority: 4.

### LIT-56. Hay, D. C. (1996). *Data Model Patterns: Conventions of Thought*. Dorset House Publishing.
- Publisher page: https://www.dorsethouse.com/books/dmp.html (fetched). Published 1996. ISBN 978-0-932633-74-3.
- Annotation: The original data-model pattern book: party/organisation, products and materials, activities and procedures, contracts, accounting, laboratory, documents, MRP and process manufacturing, drawn with consistent conventions so analysts recognise recurring structures. For a framework it provides the conceptual patterns that both Silverston's models and DDD aggregates later elaborate. Authority: 4.

---

## F. Temporal data

**Takeaway.** Snodgrass defined valid/transaction/bitemporal time for SQL practitioners; SQL:2011 (Kulkarni and Michels) standardised application-time and system-versioned tables; Date, Darwen and Lorentzos supply the relational theory (intervals, PACK/UNPACK, 6NF); Johnston gives the bitemporal practice. Together they define the framework's temporal/historisation rules for both OLTP audit and warehouse SCD/time-travel designs.

### LIT-57. Kulkarni, K. and Michels, J.-E. (2012). "Temporal Features in SQL:2011." *ACM SIGMOD Record* 41(3): 34-43.
- DOI: https://doi.org/10.1145/2380776.2380786 (fetched; 302). Official SIGMOD Record PDF: https://sigmodrecord.org/publications/sigmodRecord/1209/pdfs/07.industry.kulkarni.pdf (fetched; first page extracted).
- Annotation: Describes SQL:2011's application-time period tables (PERIOD FOR, primary keys WITHOUT OVERLAPS, period predicates), system-versioned tables (FOR SYSTEM_TIME AS OF / BETWEEN) and bitemporal tables combining both. It is the standards reference for implementing valid-time and transaction-time in Db2, SQL Server, MariaDB, Oracle and PostgreSQL extensions. Framework area: temporal/integrity for OLTP; informs warehouse SCD and time-travel design. Authority: 5.

### LIT-58. Date, C. J., Darwen, H., Lorentzos, N. A. (2014). *Time and Relational Theory: Temporal Databases in the Relational Model and SQL*, 2nd ed. Morgan Kaufmann/Elsevier.
- Publisher page: https://shop.elsevier.com/books/time-and-relational-theory/date/978-0-12-800631-3 (fetched). Published July/Aug 2014. ISBN 9780128006313.
- Annotation: Develops a rigorous theory of interval-valued attributes (PACK/UNPACK, U_ operators), temporal keys and constraints, sixth normal form for historised data, and the distinction between stated (valid) and logged (transaction) time, then critiques SQL:2011's temporal support against that theory. For a framework it is the theoretical justification for 6NF temporal decomposition and for constraint design on history tables. Authority: 4.

### LIT-59. Snodgrass, R. T. (1999). *Developing Time-Oriented Database Applications in SQL*. Morgan Kaufmann.
- Author page with free PDF: https://www2.cs.arizona.edu/~rts/publications.html (fetched; lists Morgan Kaufmann, July 1999, ISBN 1-55860-436-7, and links tdbbook.pdf).
- Annotation: The practitioner's guide to valid time, transaction time and bitemporal tables in SQL-92, covering state vs event tables, period representations, sequenced/non-sequenced/current modifications and queries, coalescing, and vendor-specific implementations. The book is freely available from the author and remains the most complete worked treatment. For a framework it is the source of temporal table patterns and the "sequenced primary key" and "temporal referential integrity" constraints. Authority: 4.

### LIT-60. Johnston, T. (2014). *Bitemporal Data: Theory and Practice*. Morgan Kaufmann/Elsevier.
- Publisher page: https://shop.elsevier.com/books/bitemporal-data/johnston/978-0-12-408067-6 (fetched). Published 19 Aug 2014. ISBN 9780124080676.
- Annotation: Explains the business value and relational theory of bitemporal data, shows how to design bitemporal tables and write their transactions and queries, and identifies a flaw in the ISO SQL:2011 bitemporal model with proposed extensions. For a framework it is the applied companion to LIT-57/58 for audit-grade OLTP history and for warehouses that must answer "what did we believe on date X about period Y". Authority: 4.

---

## G. Data engineering, pipelines and streaming

**Takeaway.** Spark/RDDs (batch), Kafka (log-based messaging) and the Dataflow Model (unified streaming semantics) define the processing substrate; Kleppmann's DDIA, Reis and Housley's lifecycle, and Campbell and Majors' reliability engineering define how schemas live inside pipelines (encoding and evolution, derived data, SLOs). The framework's pipeline area draws its schema-evolution, event-time and contract rules from these.

### LIT-61. Zaharia, M., Chowdhury, M., Das, T. et al. (2012). "Resilient Distributed Datasets: A Fault-Tolerant Abstraction for In-Memory Cluster Computing." *Proc. USENIX NSDI 2012*.
- Official page: https://www.usenix.org/conference/nsdi12/technical-sessions/presentation/zaharia (fetched).
- Annotation: RDDs are immutable, partitioned collections built by coarse-grained transformations whose lineage allows recomputation instead of replication, enabling in-memory iterative and interactive workloads; the implementation is Spark. For a framework it is the origin of the transformation-graph model behind Spark SQL and lakehouse pipelines, and of the "immutable derived datasets" principle in medallion-style schema layers. Authority: 5.

### LIT-62. Kreps, J., Narkhede, N., Rao, J. (2011). "Kafka: a Distributed Messaging System for Log Processing." *Proc. NetDB 2011*, Athens.
- Verified copy: https://people.csail.mit.edu/matei/courses/2015/6.S897/readings/kafka.pdf (fetched; first page extracted). Bibliographic listing: https://www.odbms.org/2011/01/kafka-a-distributed-messaging-system-for-log-processing/ (fetched; its Microsoft Research PDF link is now a dead redirect). No official NetDB proceedings page survives.
- Annotation: Kafka models messaging as partitioned, append-only logs with stateless brokers, pull-based consumers that track their own offsets, sequential disk I/O and zero-copy transfer, supporting both offline and real-time consumers. For a framework it establishes the event-log as a first-class data structure: topic/partition key design, event schemas and schema registries, and log-compacted topics as change-data-capture feeds into warehouses. Authority: 4 (workshop paper, highly influential; official page unavailable).

### LIT-63. Akidau, T., Bradshaw, R., Chambers, C. et al. (2015). "The Dataflow Model: A Practical Approach to Balancing Correctness, Latency, and Cost in Massive-Scale, Unbounded, Out-of-Order Data Processing." *PVLDB* 8(12): 1792-1803.
- Google Research page: https://research.google/pubs/the-dataflow-model-a-practical-approach-to-balancing-correctness-latency-and-cost-in-massive-scale-unbounded-out-of-order-data-processing/ (fetched). Official PDF: https://www.vldb.org/pvldb/vol8/p1792-Akidau.pdf (fetched; first page extracted). DOI: https://doi.org/10.14778/2824032.2824076 (fetched; 302).
- Annotation: Separates what is computed (transformations), where in event time (windowing: fixed, sliding, sessions), when in processing time (triggers and watermarks) and how refinements relate (accumulation modes), treating batch as a special case of streaming; it became Apache Beam. For a framework it dictates that streaming schemas carry event time, late-data policies and idempotent keys so that materialised tables are correct under out-of-order arrival. Authority: 5.

### LIT-64. Kleppmann, M. (2017). *Designing Data-Intensive Applications: The Big Ideas Behind Reliable, Scalable, and Maintainable Systems*. O'Reilly Media.
- Author site: https://dataintensive.net/ (fetched; links the O'Reilly listing 9781491903063). Publisher page https://www.oreilly.com/library/view/designing-data-intensive-applications/9781491903063/ returned verbatim by WebSearch (direct fetch 403). ISBN in publisher URL: 9781491903063.
- Annotation: Covers data models and query languages, storage engines (B-trees vs LSM), encoding and schema evolution (Avro/Protobuf/Thrift compatibility rules), replication, partitioning, transactions and isolation, consistency and consensus, batch and stream processing, and derived data. It is the single best bridge between the papers in sections B-D and day-to-day schema decisions, especially its schema-evolution and derived-data chapters. Framework areas: modelling, transactions, pipelines. Authority: 4.

### LIT-65. Kleppmann, M. and Riccomini, C. (2026). *Designing Data-Intensive Applications*, 2nd ed. O'Reilly Media.
- Publisher page: https://www.oreilly.com/library/view/designing-data-intensive-applications/9781098119058/ (URL returned verbatim by WebSearch; direct fetch 403, `url_verified=false`). O'Reilly catalogue lists February 2026 and 672 pages; retailers list print ISBN 9781098119065 with dates from late Feb to Mar 2026. ISBN in publisher URL: 9781098119058.
- Annotation: The second edition adds coverage of cloud services and the build-vs-buy trade-off, sharding, event sourcing, vector embeddings and durable execution, while retaining the first edition's structure. For a framework it updates the data-model and storage guidance for lakehouse, cloud-native and AI-era (vector) workloads. Authority: 4 (recently published; details should be re-checked against the O'Reilly colophon).

### LIT-66. Reis, J. and Housley, M. (2022). *Fundamentals of Data Engineering: Plan and Build Robust Data Systems*. O'Reilly Media.
- Publisher page: https://www.oreilly.com/library/view/fundamentals-of-data/9781098108298/ (URL returned verbatim by WebSearch; direct fetch 403, `url_verified=false`). Published June 2022, 450 pp; ISBN in URL 9781098108298 (search snippet also lists 9781098108304).
- Annotation: Defines the data engineering lifecycle (generation, storage, ingestion, transformation, serving) and its undercurrents (security, data management, DataOps, data architecture, orchestration, software engineering), with technology-agnostic guidance on choosing tools and on modelling for analytics (Inmon, Kimball, Data Vault, wide tables). For a framework it provides the end-to-end context in which schema design decisions sit and a vendor-neutral checklist for storage and serving layers. Authority: 3.

### LIT-67. Campbell, L. and Majors, C. (2017). *Database Reliability Engineering: Designing and Operating Resilient Database Systems*. O'Reilly Media.
- Publisher page: https://www.oreilly.com/library/view/database-reliability-engineering/9781491925935/ (URL returned verbatim by WebSearch; direct fetch 403, `url_verified=false`). First release 26 Oct 2017; ISBN in URL 9781491925935.
- Annotation: Applies SRE practice to databases: service-level objectives and risk management, operational visibility, infrastructure as code, release management for schema changes, data storage/indexing/replication choices, and data-driven architectures. For a framework it supplies the operability requirements a schema must satisfy (migratability, observability, backup/restore testability) and the change-management process for DDL. Authority: 3.

---

## H. Application architecture and Domain-Driven Design

**Takeaway.** Fowler's PoEAA catalogues object-relational mapping patterns; Evans and Vernon define aggregates and bounded contexts, which map onto transaction boundaries and service-owned schemas; Ambler and Sadalage give the refactoring catalogue for evolving live schemas; Sadalage and Fowler explain aggregate-oriented NoSQL models and polyglot persistence. These anchor the framework's modelling and schema-evolution areas for OLTP services.

### LIT-68. Fowler, M. (2002). *Patterns of Enterprise Application Architecture*. Addison-Wesley Professional.
- Publisher page: https://www.informit.com/store/patterns-of-enterprise-application-architecture-9780321127426 (fetched). Published 5 Nov 2002. ISBN 978-0-321-12742-6.
- Annotation: Catalogues data-source and object-relational patterns: Table/Row Data Gateway, Active Record, Data Mapper, Unit of Work, Identity Map, Lazy Load, Identity Field, Foreign Key and Association Table Mapping, Embedded Value, Serialized LOB, the three inheritance mappings (Single Table, Class Table, Concrete Table) and Optimistic/Pessimistic Offline Lock. For a framework it is the vocabulary for how application code will consume the schema and for choosing inheritance and locking strategies. Authority: 4.

### LIT-69. Evans, E. (2003). *Domain-Driven Design: Tackling Complexity in the Heart of Software*. Addison-Wesley Professional.
- Publisher page: https://www.informit.com/store/domain-driven-design-tackling-complexity-in-the-heart-9780321125217 (fetched). Published 20 Aug 2003. ISBN 978-0-321-12521-7.
- Annotation: Introduces ubiquitous language, bounded contexts and context maps, and the tactical patterns entities, value objects, aggregates, repositories and factories. Aggregates define consistency boundaries that should coincide with transactional boundaries, and bounded contexts define which service owns which schema. For a framework it informs table grouping, ownership and the decision of what must be transactionally consistent in OLTP. Authority: 4.

### LIT-70. Vernon, V. (2013). *Implementing Domain-Driven Design*. Addison-Wesley Professional.
- Publisher page: https://www.informit.com/store/implementing-domain-driven-design-9780321834577 (fetched). Published 6 Feb 2013. ISBN 978-0-321-83457-7.
- Annotation: Makes DDD concrete with a multitenant SaaS case study, rules for aggregate design (keep aggregates small, reference other aggregates by identity, use eventual consistency across aggregates), domain events, repositories and context-mapping integration patterns. For a framework it provides the aggregate-to-table mapping guidance and the event-driven consistency model that pairs with Sagas (LIT-17) and Kafka (LIT-62). Authority: 4.

### LIT-71. Ambler, S. W. and Sadalage, P. J. (2006). *Refactoring Databases: Evolutionary Database Design*. Addison-Wesley Professional.
- Publisher page: https://www.informit.com/store/refactoring-databases-evolutionary-database-design-9780321293534 (fetched). Published 3 Mar 2006. ISBN 978-0-321-29353-4.
- Annotation: Defines database refactoring (behaviour-preserving schema change with a transition period for old and new structures) and catalogues refactorings by category: structural (rename/split/merge), data quality (introduce constraints, standardise codes), referential integrity (add foreign key, cascade), architectural (encapsulate table with view, introduce calculation method) and transformations. For a framework it is the schema-evolution playbook and the basis for migration tooling conventions. Authority: 4.

### LIT-72. Sadalage, P. J. and Fowler, M. (2012). *NoSQL Distilled: A Brief Guide to the Emerging World of Polyglot Persistence*. Addison-Wesley Professional.
- Publisher page: https://www.informit.com/store/nosql-distilled-a-brief-guide-to-the-emerging-world-9780321826626 (fetched). Published 8 Aug 2012. ISBN 978-0-321-82662-6.
- Annotation: Explains aggregate-oriented data models (key-value, document, column-family) versus graph models, the meaning of "schemaless", distribution models (sharding, master-slave and peer-to-peer replication), consistency and quorums, map-reduce, schema migration in NoSQL stores and polyglot persistence. For a framework it is the concise decision guide for when to leave the relational model and how aggregates map to document/column-family schemas. Authority: 4.

---

## I. Governance, quality and delivery performance

**Takeaway.** DAMA-DMBOK defines the data-management functions a schema design must satisfy (governance, architecture, modelling, metadata, quality, security); Hoberman's Scorecard (LIT-52) operationalises model quality; Dehghani's Data Mesh federates ownership; Accelerate ties database change management to delivery performance.

### LIT-73. DAMA International (2017). *DAMA-DMBOK: Data Management Body of Knowledge*, 2nd ed. Technics Publications.
- Publisher page: https://technicspub.com/?p=3334 (fetched; Technics' DMBOK2 page describing the guide and its translations: "17 data management topics" and 13 guiding principles). ISBN 9781634622349 and 2017 per library records; a revised printing and the 2024 "DMBOK 2.0 Revision" are noted on DAMA's site per search results.
- Annotation: The reference framework for data management: governance, architecture, modelling and design, storage and operations, security, integration, documents and content, reference and master data, warehousing and BI, metadata, and quality, plus chapters on ethics, big data, maturity and organisational change. For a schema design framework it supplies the governance context (standards, stewardship, metadata capture, quality dimensions) and the modelling chapter's expectations for conceptual/logical/physical deliverables. Authority: 4 (professional body of knowledge).

### LIT-74. Dehghani, Z. (2022). *Data Mesh: Delivering Data-Driven Value at Scale*. O'Reilly Media.
- Publisher page: https://www.oreilly.com/library/view/data-mesh/9781492092384/ (URL returned verbatim by WebSearch; direct fetch 403, `url_verified=false`). Published March 2022; ISBN in URL 9781492092384.
- Annotation: Defines data mesh through four principles: domain-oriented ownership of analytical data, data as a product (with discoverability, addressability, trustworthiness and interoperability), a self-serve data platform, and federated computational governance (policies enforced as code). For a framework it shifts warehouse schema ownership to domains and makes data-product contracts and shared polysemes (conformed concepts) the governance objects. Authority: 3.

### LIT-75. Forsgren, N., Humble, J., Kim, G. (2018). *Accelerate: The Science of Lean Software and DevOps*. IT Revolution Press.
- Publisher page: https://itrevolution.com/product/accelerate/ (fetched). Published 27 Mar 2018. ISBN 9781942788331 (paperback).
- Annotation: Reports four years of State of DevOps research identifying four delivery metrics (lead time, deployment frequency, time to restore, change failure rate) and 24 capabilities that predict performance, including version control for all production artefacts, trunk-based development and database change management integrated into the delivery process. For a framework it is the evidence base for treating schema migrations as versioned, automated, small-batch changes. Authority: 3 (research-based practitioner book).

---

## Cross-cutting inferences for the framework

- Relational theory (A) and transaction theory (B) are stable; every later paper (C, D) that departs from them either re-derives relational ideas (Spanner's interleaved tables, Delta Lake's ACID log, NewSQL) or explicitly trades them for availability (Dynamo, HAT). A framework should therefore make the relational model the default and document any departure using the vocabulary of PACELC/HAT.
- The OLAP branch (Kimball, Inmon, Data Vault, Anchor) is converging on open lakehouse tables (Delta Lake, Lakehouse, Dremel/Parquet) as the physical substrate, so modelling style and storage format are now independent decisions.
- Temporal modelling (F) is the one area where theory (Date et al.), standard (SQL:2011) and practice (Snodgrass, Johnston) all agree on valid-time/transaction-time separation; the framework can specify it uniformly for OLTP audit and warehouse SCD/time-travel.
- Governance literature (I) supplies review instruments (Scorecard) and ownership models (Data Mesh) but little schema-level detail; the framework must bridge by mapping DMBOK functions to concrete DDL/metadata deliverables.

## Gaps
- No official full text for Codd 1971 (RJ909) or an archived NetDB 2011 page for Kafka; both are catalogued via bibliographic records and course-hosted copies.
- DOI for Stonebraker and Pavlo 2024 not confirmed; SIGMOD Record page used instead.
- O'Reilly, ACM DL, IEEE Xplore, ScienceDirect and MIT Press landing pages block automated fetches; DOI resolution and search-verbatim URLs were used, as flagged per entry.
- Date's *An Introduction to Database Systems* 8th ed. omitted (no reachable publisher page).
