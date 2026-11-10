# Database Security and Privacy Standards as They Affect Schema Design
Research deliverable for the Database Schema Design and Data Engineering Standards Framework (ERP, financial, SaaS and data engineering systems). Research phase only: this file contains no schemas and no implementation. Compiled 2026-11-08 from existing project notes. No new web research was done and no source outside the notes was added.

> **Not legal advice.** This is engineering research. Nothing here is a legal conclusion, and none should be drawn from it without qualified counsel. Whether a regime applies, what a retention period is for a specific record class, whether an erasure exception is available and whether a technique amounts to erasure are all questions for counsel in the relevant jurisdiction. Payment-scope questions also belong with the organization's PCI assessor.

> **Open points to keep in view (notes 19 and 22).**
> - **Key destruction as erasure is not settled, and soft deletion is not settled.** No regulator text found accepts the first or addresses the second by name (sections 12.5, 12.7).
> - **ICO and Dutch AP text was read from Wayback captures because the live sites refused access.** Each needs confirmation on the live site before reliance (section 12.7).
> - **The German invoice-gap rule rests on search snippets**, because UStAE 14.5(10) could not be opened. See section 15 and `industry_best_practices.md`, section 5.
> - **Citation conflicts remain open** for Pakistan (e-invoicing start dates) and the UAE (Article 59 amendment, Cabinet Decision No. 100 of 2024 against 2025). See section 15.

## 0. How to read this document
### 0.1 Label definitions
| Label | Meaning here |
|---|---|
| **MANDATORY (legal)** | A statute or regulation states it, for entities within that regime's scope. Scope is always named. |
| **MANDATORY (standard)** | A binding condition of a non-statutory scheme, for those inside it: PCI DSS for in-scope entities, ISO/IEC 27001 Clauses 4-10 when conformity is claimed, NIST controls for US federal systems. |
| **MANDATORY (correctness)** | The design is wrong or its stated guarantee is false without it, regardless of any law. |
| **RECOMMENDED** | An authoritative source advises it with reasoning; viable alternatives may exist. |
| **OPTIONAL/CONTEXTUAL** | Depends on threat model, scale or regime. |
| **INFERENCE** | An engineering conclusion drawn from sources that do not state it directly. It can be combined with any label above and lowers the confidence of that label. |
### 0.2 Workload scope codes
Every principle names one or more scopes.

| Code | Workload |
|---|---|
| ALL | All relational and document operational systems and analytical platforms |
| OLTP | Operational transactional databases |
| ERP | Multi-company ERP and financial-posting systems |
| FIN | Financial ledgers and records subject to audit |
| SAAS | Multi-tenant SaaS |
| DE | Data engineering: pipelines, warehouses, lakehouses, CDC consumers |
| PCI | Systems storing, processing or transmitting account data |
| PHI | Systems holding ePHI under HIPAA |
| PD | Systems holding personal data under GDPR or CCPA/CPRA |
| FDA | Electronic records under 21 CFR Part 11 |
### 0.3 Evidence and quotation conventions
- **Quotation marks are used only for raw-extracted text**, as recorded in the notes: PDFs (NIST publications, the EDPB guidelines and the PCI SSC SAQ D) and the legal and regulator text note 19 extracted with curl or pdftotext (LEG IDs). All other source wording, including regulation text read through a fetch tool and vendor documentation, is **paraphrased**. The project's corrections file warns that most web pages were read through a summarizing fetch tool. Regulation paraphrases must be checked against the official text before they are relied on.
- Citation form is [Title](URL) (date or n.d.), followed by the catalog ID where one exists. A citation with no ID means the source appears in the notes but has no separate catalog entry.
- **PCI DSS wording comes from the v4.0 SAQ D for Merchants** (April 2022), not the license-gated v4.0.1 standard. PCI SSC says v4.0.1 added no requirements, but v4.0.1 clause numbering, notably 6.5.x, was not re-verified. Note 19 records the PCI SSC library page timing out (HTTP 504) and the v4.0.1 SAQ D refusing access (HTTP 403), so all PCI wording here stands as v4.0 SAQ D wording pending a check against v4.0.1.
- **Paywalled or gated standards** (ISO/IEC 27001, ISO 15489-1, CIS Benchmark PDFs) are described only at the scope level the notes support. No control or recommendation numbers are given for them.
- Unverified sources are flagged where used and collected in section 15. Departures from the notes are listed in section 14.

## 1. Principal findings
1. **Regulations constrain outcomes, not schema structures.** None of the instruments reviewed prescribes a table design. They create column-level consequences: which data may exist at all, how it must be rendered, who may read it, how long it stays and how changes are evidenced.
2. **The most prescriptive column-level rules found are in PCI DSS.** Sensitive authentication data may not persist after authorization, even encrypted, and PAN must be rendered unreadable by one of four listed approaches.
3. **At-rest encryption answers a narrow threat.** Microsoft scopes TDE to data and log files against stolen media; OWASP says the layer depends on the threat model. Encryption claims should name the attacker they address.
4. **No relational engine reviewed prevents privileged tampering.** PostgreSQL trigger audit, pgAudit and SQL Server Audit each acknowledge the limit. SQL Server ledger offers detection on verification, not prevention, and depends on digests kept outside the database.
5. **Masking is not a security boundary.** Microsoft and Oracle both document inference attacks on their dynamic masking features.
6. **RLS is an enforcement mechanism, not a tenancy model.** It sits on top of the pool model and has documented bypasses and side channels.
7. **Schema-per-tenant has no support in the fetched sources.** It is assessed here only by inference.
8. **Retention and erasure must be modeled per record class.** Regulatory floors differ by what they cover, and several commonly quoted figures apply to narrower records than the shorthand suggests (section 12.3). Tax and commercial periods by jurisdiction are now in section 12.6.
9. **The GDPR legal-obligation exception refers to Union or Member State law.** A US statute or an industry standard does not obviously satisfy it. The notes' suggestion otherwise is not adopted (section 13, C1).
10. **Crypto-shredding as GDPR erasure is not settled law.** No regulator text found accepts it as erasure. It is an engineering inference with strict preconditions (section 12.5).
11. **Regulators now speak to backups, but the position is not settled.** The EDPB, ICO, Dutch AP and California text share one element: keep track of erasure requests and re-apply them on restore. How long "without undue delay" lasts for backups in the EU is open (section 12.7).

## 2. Legal requirements versus engineering recommendations
| Instrument | Nature | Who is bound | What the notes actually read | Force in this document |
|---|---|---|---|---|
| GDPR (Reg. (EU) 2016/679) | Legislation | Controllers and processors in scope | EUR-Lex: Arts 9, 17 and 30(5) raw-extracted (LEG-03); other articles via fetch and paraphrased | MANDATORY (legal) |
| CCPA/CPRA | Legislation and regulations | Covered businesses | CPPA-hosted statute copy for Civil Code 1798.105 (effective 01/01/2025) and Regulations section 7022 (effective 1/1/2026), raw-extracted (LEG-28, LEG-29); leginfo not opened; CPPA FAQ for the rest | MANDATORY (legal); summary level outside those sections |
| HIPAA Security Rule | Regulation | Regulated entities | 45 CFR 164.312 and 164.316; 2025 NPRM partly | MANDATORY (legal); NPRM is **proposed only** |
| SOX (Pub. L. 107-204) | Legislation | SEC issuers, auditors; obstruction offences are general | Statute text | MANDATORY (legal), for what it says; it contains no database design rule |
| 21 CFR Part 11 | Regulation | FDA-regulated electronic records | §11.10 via LII mirror | MANDATORY (legal), FDA scope only |
| VAT, tax, commercial and companies law | Legislation and tax-authority guidance | Stated population per jurisdiction | Note 19, section 12.6 here; quality varies per row | MANDATORY (legal) for the stated records and population |
| Regulator guidance on erasure (EDPB, ICO, Dutch AP) | Guidance, some consultation-stage | Interprets GDPR or UK GDPR | Note 19, section 12.7 here; ICO and AP through Wayback captures | RECOMMENDED; does not settle key destruction or soft deletion |
| PCI DSS | Industry standard from PCI SSC, not legislation | Entities storing, processing or transmitting account data | v4.0 SAQ D PDF; v4.0.1 announcement | MANDATORY (standard). The notes do not record how it is enforced; confirm with counsel or assessor |
| ISO/IEC 27001:2022 | Voluntary certifiable standard | Organizations claiming conformity | IEC catalogue abstract | MANDATORY (standard), Clauses 4-10 when claiming conformity |
| NIST SP 800 series, FIPS 140-3 | Government guidance and standards | US federal systems; voluntary elsewhere | PDFs for 800-53, 800-122, 800-57, 800-88r2; abstract pages for 800-209, 800-188 | MANDATORY (standard) federal; RECOMMENDED elsewhere |
| NIST Privacy Framework | Voluntary tool | None | v1.0 PDF | OPTIONAL/CONTEXTUAL |
| OWASP Top 10, ASVS, cheat sheets | Community guidance | None | Web pages; ASVS V14 only | RECOMMENDED |
| CIS Benchmarks | Consensus hardening guidance | None | Public index page only | RECOMMENDED |
| Vendor documentation | Product behavior | Users of the product | Web pages | MANDATORY (correctness) for stated restrictions; otherwise RECOMMENDED |

The rule for the eventual framework: **a law may force an outcome, while the mechanism remains an engineering choice.** Art. 32 GDPR makes encryption appropriate-to-risk rather than absolute. PCI DSS 3.5.1 offers a menu of four approaches. HIPAA encryption is currently an addressable specification. A framework that turns these into one fixed mechanism should mark that as an engineering decision, not a legal requirement.

## 3. What each framework contributes to schema decisions
### 3.1 OWASP
Sources are recommendations for all workloads; no legal force.

- **Parameterized queries are the primary injection defense**, and escaping is explicitly discouraged. Binding at a procedure call does not protect dynamic SQL built inside the procedure. Identifiers such as table and column names cannot be bound, so they must be fixed in code or mapped through an allow-list. [OWASP SQL Injection Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html) (n.d.) SEC-02; [OWASP Query Parameterization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Query_Parameterization_Cheat_Sheet.html) (n.d.) SEC-03. **MANDATORY (correctness)**. Scope: ALL, including pipeline code that builds dynamic SQL (extension to DE is INFERENCE).
- **Least privilege limits damage but does not prevent injection.** Application accounts must not hold DBA or admin rights. SEC-02. **RECOMMENDED**. Scope: ALL.
- **Database Security Cheat Sheet:** single-purpose accounts, no built-in admin accounts, separate accounts and databases per environment, application account not the database owner, no credentials in source, encrypted connections only, and table-, column- or row-level permissions or restricted views for security-critical applications. It points to CIS Benchmarks for hardening. [OWASP Database Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Database_Security_Cheat_Sheet.html) (n.d.) SEC-01. **RECOMMENDED**. Scope: ALL.
- **Cryptographic storage:** minimization comes first; prefer authenticated AES modes under formally managed keys kept apart from the data; envelope encryption; passwords hashed, never reversibly encrypted. Layer choice depends on the threat model. [OWASP Cryptographic Storage Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cryptographic_Storage_Cheat_Sheet.html) (n.d.) SEC-04. Password hashing is **MANDATORY (correctness)**; the rest is **RECOMMENDED**. Scope: ALL.
- **Logging:** log authentication, authorization failures, privilege administration, access to sensitive data and key use. Exclude or mask credentials, session identifiers, connection strings, PII and cardholder data. Use a separate write-only database account, structured formats, tamper detection and early copy to read-only media. Do not destroy logs before the required period or keep them beyond it. [OWASP Logging Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html) (n.d.) SEC-05. **RECOMMENDED**, and MANDATORY where a regulation in section 3 requires the same outcome. Scope: ALL.
- **Top 10:2025** keeps Broken Access Control (A01), Cryptographic Failures (A04), Injection (A05) and Security Logging and Alerting Failures (A09). [OWASP Top 10:2025](https://top10.owasp.org/2025/) (2025; exact release date not shown) SEC-06. Context only.
- **ASVS 5.0.0 V14** verifies that sensitive data is identified and classified (14.1.1, L2), that each protection level has documented requirements covering encryption, integrity, retention, logging and database encryption (14.1.2, L2), that those controls are implemented (14.2.4, L2), that only minimum data is returned (14.2.6, L3), and that retention classification drives scheduled deletion (14.2.7, L3). [ASVS V14 Data Protection](https://github.com/OWASP/ASVS/blob/v5.0.0/5.0/en/0x23-V14-Data-Protection.md) (v5.0.0; stable release 2025-05-30), [OWASP ASVS](https://asvs.owasp.org/) SEC-07. **RECOMMENDED** at the stated levels. Scope: ALL. Requirement text for V11 and V16 was not opened.
### 3.2 NIST
Text below was PDF-extracted per the notes. **MANDATORY (standard)** for US federal systems, **RECOMMENDED** elsewhere, unless stated. Scope: ALL.

[NIST SP 800-53 Rev. 5](https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final) (September 2020; updates as of 2020-12-10) SEC-08. Release 5.2.0 (2025-08-27) changes were not reviewed.

| Control | Schema or platform consequence |
|---|---|
| AC-3 Access Enforcement | Logical access enforced under policy, which may be at application or service level |
| AC-6 Least Privilege | "allowing only authorized accesses for users (or processes acting on behalf of users) that are necessary to accomplish assigned organizational tasks" |
| AU-2 Event Logging | Define loggable event types |
| AU-9 Protection of Audit Information | "Protect audit information and audit logging tools from unauthorized access, modification, and deletion" |
| AU-11 Audit Record Retention | Organization-defined period consistent with records retention policy |
| SC-12 Key Management | Requirements for generation, distribution, storage, access and destruction |
| SC-28 Protection at Rest | Confidentiality and/or integrity at rest; the discussion names databases |
| MP-6 Media Sanitization | Before disposal or reuse |
| PM-25 PII in Testing | "Limit or minimize the amount of personally identifiable information used for internal testing, training, and research purposes." |
| SI-12 Information Management and Retention | Retain per applicable law, policy and operational need |

- [NIST SP 800-122](https://csrc.nist.gov/pubs/sp/800/122/final) (April 2010) SEC-09: defines PII, sets a separate low/moderate/high PII confidentiality impact level from six factors, and separates de-identified from anonymized data (section 6.1).
- [NIST SP 800-57 Part 1 Rev. 5](https://csrc.nist.gov/pubs/sp/800/57/pt1/r5/final) (May 2020) SEC-11: cryptoperiods limit exposure from a single key compromise.
- [FIPS 140-3](https://csrc.nist.gov/pubs/fips/140-3/final) (2019-03-22), catalogued with SEC-11: four security levels for cryptographic modules. A selection criterion outside federal systems.
- [NIST SP 800-88 Rev. 2](https://csrc.nist.gov/pubs/sp/800/88/r2/final) (September 2025) SEC-12: recognizes cryptographic erase as a purge technique, with preconditions (section 12.5).
- [NIST SP 800-188](https://csrc.nist.gov/pubs/sp/800/188/final) (September 2023) SEC-10: de-identification of government datasets. Abstract-level reading supports the caution in the notes that masking tools do not necessarily perform de-identification.
- [NIST SP 800-209](https://csrc.nist.gov/pubs/sp/800/209/final) (October 2020; no catalog ID found): storage infrastructure security. Abstract only.
- [NIST Privacy Framework](https://www.nist.gov/privacy-framework) (v1.0 2020-01-16) SEC-13: a voluntary tool with five functions. **OPTIONAL/CONTEXTUAL**. A 1.1 initial public draft is reported from search snippets; final status is unverified.
### 3.3 CIS Benchmarks
[CIS Benchmarks](https://www.cisecurity.org/cis-benchmarks) (n.d.) SEC-14 publishes consensus, version-specific hardening guides. The public index lists, among others, PostgreSQL 18 v1.0.0, SQL Server 2025 v1.0.0, Oracle 26ai v1.0.0, MongoDB 8 v2.0.0, MySQL 9.7 v1.0.0 and Snowflake Foundations v2.0.1.

- **The PDFs are gated and were not opened.** Profile levels, section structure and individual recommendations are outside what the notes support, so none is cited.
- **RECOMMENDED** (Scope: ALL): adopt the benchmark for each engine major version as the hardening baseline.
- **INFERENCE, RECOMMENDED:** pin the benchmark version beside the engine version, because benchmarks are versioned per engine release.
- CIS mostly affects platform configuration. Its direct effect on schema design could not be assessed.
### 3.4 GDPR
Paraphrased from [Regulation (EU) 2016/679](https://eur-lex.europa.eu/eli/reg/2016/679/oj) (2016-04-27) SEC-15. **MANDATORY (legal)**. Scope: PD.

| Provision | Requirement (paraphrase) | Schema consequence (INFERENCE unless cited) |
|---|---|---|
| Art. 4(1) | Personal data is information relating to an identified or identifiable person | Classification cannot stop at direct identifiers |
| Art. 4(5) | Pseudonymisation requires additional information kept separately under safeguards; pseudonymised data remains personal data | Pseudonym maps belong in a separately controlled store |
| Art. 5(1)(c), Art. 25 | Minimisation; data protection by design and by default | Each collected attribute needs a purpose |
| Art. 5(1)(e) | Identifiable form kept no longer than necessary | Retention must be enforceable, not just documented |
| Art. 5(1)(f), Art. 32 | Security appropriate to risk, including pseudonymisation and encryption as appropriate, plus restore capability and testing | Encryption is risk-based, not absolute |
| Art. 5(2) | Controller must be able to demonstrate compliance | Retention basis and controls must be evidenced |
| Art. 17(1) | Erasure without undue delay where a listed ground applies | Erasure must reach every copy in scope |
| Art. 17(3) | Exceptions include legal obligation under Union or Member State law, public-interest tasks and legal claims | Exception and basis should be recorded per record class |
| Art. 30(1) | Records of processing, including erasure time limits where possible and security measures | Metadata should support these records |
| Art. 30(5) | Limited exemption for organizations under 250 employees, with exclusions. See [Art. 30 GDPR](https://gdpr-info.eu/art-30-gdpr/) (n.d.), catalogued with TEN-34 | Do not rely on it without counsel |
| Recital 26 | Principles do not apply to truly anonymous information | Anonymization is a high bar; pseudonymisation does not meet it |

Interpretive guidance: [EDPB Guidelines 01/2025 on Pseudonymisation](https://www.edpb.europa.eu/our-work-tools/documents/public-consultations/2025/guidelines-012025-pseudonymisation_en) (adopted 2025-01-16; **consultation version, final not confirmed**) SEC-16. PDF-extracted: additional information "may consist of tables matching pseudonyms with the identifying attributes they replace. It may also consist of cryptographic keys." It also says such information may itself be personal data. The pseudonymisation domain concept means effectiveness depends on isolation from that additional information.

**Official wording obtained** ([Regulation (EU) 2016/679, EUR-Lex HTML](https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32016R0679), 2016-04-27, LEG-03; raw-extracted). **MANDATORY (legal)**. Scope: PD.
- Art. 9(1): "Processing of personal data revealing racial or ethnic origin, political opinions, religious or philosophical beliefs, or trade union membership, and the processing of genetic data, biometric data for the purpose of uniquely identifying a natural person, data concerning health or data concerning a natural person's sex life or sexual orientation shall be prohibited." Art. 9(2) sets exceptions, starting with explicit consent at point (a). Counsel should review these before the classification model is finalized.
- Art. 17(1): "The data subject shall have the right to obtain from the controller the erasure of personal data concerning him or her without undue delay and the controller shall have the obligation to erase personal data without undue delay where one of the following grounds applies:" The grounds at (a) to (f), paraphrased: no longer necessary; consent withdrawn with no other legal ground; objection under Art. 21; unlawful processing; erasure needed for a legal obligation; data collected for information society services under Art. 8(1).
- Art. 17(3): "Paragraphs 1 and 2 shall not apply to the extent that processing is necessary:" including "(b) for compliance with a legal obligation which requires processing by Union or Member State law to which the controller is subject or for the performance of a task carried out in the public interest or in the exercise of official authority vested in the controller;" and "(e) for the establishment, exercise or defence of legal claims."
- Art. 30(5): "The obligations referred to in paragraphs 1 and 2 shall not apply to an enterprise or an organisation employing fewer than 250 persons unless the processing it carries out is likely to result in a risk to the rights and freedoms of data subjects, the processing is not occasional, or the processing includes special categories of data as referred to in Article 9(1) or personal data relating to criminal convictions and offences referred to in Article 10."
- **INFERENCE:** "to the extent that" points to field-level or record-level treatment, so an invoice's retained fields can stay under 17(3)(b) while other profile data is erased. Which fields is a legal judgment. RECOMMENDED. Scope: PD, ERP, DE.
- **INFERENCE:** regular SaaS processing is not occasional, so the Art. 30(5) exemption is narrow.
### 3.5 CCPA/CPRA
Summary level only, from [CPPA FAQ](https://cppa.ca.gov/faq.html) (n.d.) SEC-20 and [CPPA Regulations](https://cppa.ca.gov/regulations/) (lists regulations effective 2026-01-01). **MANDATORY (legal)** for covered businesses. Scope: PD.

- Consumer rights cover knowing, deleting (subject to exceptions), correcting, opting out of sale and sharing, limiting use of sensitive personal information and equal treatment.
- Personal information includes information reasonably linkable to a consumer or household, so **household-level linkage** belongs in classification.
- Sensitive personal information includes items such as social security and driver's license numbers, precise geolocation, genetic and health data.
- Thresholds in the FAQ include annual gross revenue of $26.625 million or more (as stated effective 2025-01-01), or 100,000 or more residents or households, or 50% or more of revenue from selling or sharing. The figure may be adjusted, so verify before use.
- **Official wording obtained** ([CPPA copy of the CCPA statute](https://cppa.ca.gov/regulations/pdf/ccpa_statute.pdf), effective 01/01/2025, LEG-28; raw-extracted). The leginfo page could not be opened, and later statutory change was not checked. **MANDATORY (legal)**. Scope: PD, including processors and downstream copies (INFERENCE for DE).
  - 1798.105(c)(1): the business "shall delete the consumer's personal information from its records, notify any service providers or contractors to delete the consumer's personal information from their records, and notify all third parties to whom the business has sold or shared the personal information to delete the consumer's personal information unless this proves impossible or involves disproportionate effort."
  - (c)(2): "The business may maintain a confidential record of deletion requests solely for the purpose of preventing the personal information of a consumer who has submitted a deletion request from being sold, for compliance with laws or for other purposes, solely to the extent permissible under this title."
  - (d): exceptions include completing the transaction, security and integrity, debugging, internal uses aligned with expectations, and "(8) Comply with a legal obligation."
- The statute section does not mention backups. Regulations section 7022 does; see section 12.7. A schema can now be mapped to these exceptions at section level, but which one applies to a given record is for counsel.

**INFERENCE, RECOMMENDED:** opt-out and limit-use rights imply per-consumer preference state that downstream data flows must honor.
### 3.6 HIPAA
[45 CFR 164.312](https://www.govinfo.gov/content/pkg/CFR-2024-title45-vol2/xml/CFR-2024-title45-vol2-sec164-312.xml) (68 FR 8376, 2003-02-20, as amended 78 FR 5694, 2013-01-25) SEC-18. Paraphrased. Scope: PHI.

| Provision | Status | Schema consequence |
|---|---|---|
| (a)(1) Access control | **MANDATORY (legal)** | Access only for those granted rights |
| Unique user identification | Required | INFERENCE: shared application logins need per-user attribution in audit data |
| Emergency access procedure | Required | INFERENCE: a controlled and audited break-glass path |
| Encryption and decryption | Addressable | Implement, or document an equivalent and the reasoning |
| (b) Audit controls | **MANDATORY (legal)** | Mechanisms must record and examine activity |
| (c) Integrity; authentication of ePHI | Standard; (c)(2) Addressable | Detect improper alteration or destruction |
| (e) Transmission security | Addressable specifications | Encryption whenever deemed appropriate |

The [2025 NPRM](https://www.govinfo.gov/content/pkg/FR-2025-01-06/html/2024-30983.htm) (2025-01-06), catalogued with SEC-18, proposes removing the addressable/required distinction and expressly requiring ePHI encryption with limited exceptions. **Proposed only as of the text read; final-rule status is unverified.** **RECOMMENDED (INFERENCE):** design as if encryption were required.
### 3.7 PCI DSS
Requirement text PDF-extracted from [PCI DSS v4.0 SAQ D for Merchants](https://listings.pcisecuritystandards.org/documents/PCI-DSS-v4-0-SAQ-D-Merchant.pdf) (April 2022); status from [Just Published: PCI DSS v4.0.1](https://blog.pcisecuritystandards.org/just-published-pci-dss-v4-0-1) (2024-06-11), both SEC-17. **MANDATORY (standard)**. Scope: PCI.

| Req. | Text or summary | Schema consequence |
|---|---|---|
| 3.2.1 | "Account data storage is kept to a minimum through implementation of data retention and disposal policies, procedures, and processes" (v4.0 SAQ D wording) | Retention and disposal must exist for account data |
| 3.3 / 3.3.1 | "SAD is not retained after authorization, even if encrypted. All sensitive authentication data received is rendered unrecoverable upon completion of the authorization process." (v4.0 SAQ D wording) | No column, log, cache or staging table may persist it afterwards |
| 3.4.1 | PAN masked on display; BIN and last four are the maximum | Display forms must be derived, with authorization for more |
| 3.5.1 | PAN unreadable wherever stored, by one-way hashes of the entire PAN, truncation, index tokens or strong cryptography with key management | A per-column decision. Hashed and truncated forms of the same PAN need controls against correlation |
| 3.5.1.2 | "If disk-level or partition-level encryption (rather than file-, column-, or field-level database encryption) is used", PAN must be "also rendered unreadable via another mechanism" (future-dated in v4.0; effective 2025-03-31) | Volume encryption alone is insufficient for PAN. See section 13, C4 for TDE |
| 6.5.6 (v4.0 numbering) | "Live PANs are not used in pre-production environments, except where those environments are included in the CDE and protected in accordance with all applicable PCI DSS requirements." | Non-production copies need PAN removed or full CDE controls |
| 10.2.1, 10.2.1.1 | Audit logs enabled; capture all individual user access to cardholder data | User attribution is required, not only service-account activity |
| 10.3 | "Audit log files are protected to prevent modifications by individuals." | Separation from those who can alter logs |
| 10.5.1 | "Retain audit log history for at least 12 months, with at least the most recent three months immediately available for analysis." | Two-tier log retention |

**Status of this wording.** Everything in this table is v4.0 SAQ D wording, pending a check against v4.0.1, whose standard and SAQ D could not be opened (section 15). [PCI SSC FAQ 1280](https://www.pcisecuritystandards.org/faqs/1280/) (n.d.) LEG-31, read through a fetch tool and paraphrased: card verification codes may not be stored after authorization, even encrypted, and customer permission does not change this; issuers and companies supporting issuing with a legitimate need are the exception. The same SAQ D is catalogued as LEG-30.
### 3.8 SOX
[Sarbanes-Oxley Act of 2002](https://www.govinfo.gov/content/pkg/PLAW-107publ204/html/PLAW-107publ204.htm) (2002) SEC-19. Paraphrased. **MANDATORY (legal)** for those covered. Scope: FIN.

- §302 and §404: officers and management are responsible for internal controls and their assessment; the issuer's auditor attests.
- §802 creates 18 U.S.C. §1519 (knowing alteration, destruction or falsification of records with intent to obstruct federal matters) and §1520 (auditors retain audit or review workpapers for 5 years; SEC rulemaking authority). See also [18 U.S.C. 1520](https://www.law.cornell.edu/uscode/text/18/1520) (n.d.) TEN-36.
- §103 separately requires registered firms to retain audit work papers for not less than 7 years. §1102 adds 18 U.S.C. §1512(c).

**SOX contains no database, audit-trail or schema requirement in the text read.** The link from §404 to immutable ledgers and change history is an **INFERENCE** about how adequate internal control is demonstrated. It should be validated with auditors. Also, §1519 is an intent-based offence, not a general retention schedule. Routine, policy-driven deletion and obstruction are different things, but when a matter is pending counsel must decide. This supports a legal-hold capability (section 12).
### 3.9 ISO/IEC 27001:2022
[ISO/IEC 27001:2022](https://webstore.iec.ch/en/publication/79694) (Edition 3.0, 2022-10-25; Amd 1:2024) GOV-15. Scope level only, because the standard is paywalled.

- It specifies requirements for establishing, implementing, maintaining and continually improving an information security management system and for assessing and treating risk.
- Excluding Clauses 4-10 is not acceptable when claiming conformity. **MANDATORY (standard)** on that condition.
- Annex A control selection is reported as risk-based. The reported count of 93 controls comes **only from low-authority vendor summaries**. Annex A control titles and ISO/IEC 27002 were not consulted.
- ISO/IEC 27001 sets management-system obligations, not schema structures. A claim that column classification implements a specific Annex A control is **not supported by the notes**.

Adjacent: [ISO 15489-1:2016](https://www.evs.ee/en/iso-15489-1-2016) (valid from 2016-04-07) GOV-16 covers records, their metadata and records systems. The abstract read does not mention retention or disposition explicitly, so it is cited here only for records metadata. **RECOMMENDED** where data constitutes records.

## 4. Access control and least-privilege roles
**Source basis:** OWASP (SEC-01, SEC-02), NIST AC-3/AC-6 (SEC-08), HIPAA (SEC-18), and vendor documentation below.

| ID | Principle | Label | Scope | Basis |
|---|---|---|---|---|
| AC-1 | Bind all values; never concatenate them into SQL | MANDATORY (correctness) | ALL | SEC-02, SEC-03 |
| AC-2 | The application does not connect as superuser or object owner | MANDATORY (correctness) wherever audit or RLS guarantees are claimed; RECOMMENDED otherwise | ALL | SEC-01; [PostgreSQL wiki: Audit trigger 91plus](https://wiki.postgresql.org/wiki/Audit_trigger_91plus) (2017-11-04) TEN-11 |
| AC-3 | Unique identity per person or service; review and remove accounts | MANDATORY (legal) for PHI; RECOMMENDED otherwise | ALL, PHI | SEC-18, SEC-01, [MongoDB Security Checklist](https://www.mongodb.com/docs/manual/administration/security-checklist/) (9.0 docs, n.d.) SEC-30 |
| AC-4 | Separate accounts and databases per environment | RECOMMENDED | ALL | SEC-01 |
| AC-5 | Credentials never in source or repositories; keys and secrets in a vault, KMS or HSM | RECOMMENDED | ALL | SEC-01, SEC-04 |
| AC-6 | Security-critical tables are exposed through views or column and row permissions | OPTIONAL/CONTEXTUAL | OLTP, ERP, DE | SEC-01, SEC-02 |
| AC-7 | Separate policy administration from data access | RECOMMENDED | ALL | [SQL Server Row-Level Security](https://learn.microsoft.com/en-us/sql/relational-databases/security/row-level-security) (2025-09-11) MSOM-05; [Snowflake Object Tagging](https://docs.snowflake.com/en/user-guide/object-tagging) (n.d.) SEC-31 |
| AC-8 | Separate audit administration from audit viewing | RECOMMENDED | ALL | [Oracle 19c Introduction to Auditing](https://docs.oracle.com/en/database/oracle/oracle-database/19/dbseg/introduction-to-auditing.html) (n.d.) SEC-28 |

**Reference role separation (INFERENCE from the sources above; RECOMMENDED; role names are descriptive only):**
| Duty | Permitted | Denied | Source hooks |
|---|---|---|---|
| Application runtime | Required DML on application objects | Ownership, DDL, admin, RLS bypass | SEC-01, SEC-02 |
| Migration or deployment | DDL, through an automated pipeline only | Interactive business use | [Azure: storage and data in multitenant solutions](https://learn.microsoft.com/en-us/azure/architecture/guide/multitenant/approaches/storage-data) (2026-08-21) CLOUD-18 |
| Analyst | Read through views, masked columns or policy tags | Direct access to raw sensitive columns | SEC-02, [BigQuery column-level access control](https://docs.cloud.google.com/bigquery/docs/column-level-security-intro) (n.d.) SEC-33 |
| Audit writer | Append only to audit objects | Read-back, update, delete | SEC-05 |
| Audit reader | Read audit data, ideally on a separate instance | Change audit configuration | SEC-26, SEC-28 |
| Security policy manager | Manage policies and tags | Routine reading of protected data | MSOM-05, SEC-31 |

**Vendor limits a framework must account for:**
- SQL Server: sysadmin can tamper with any audit component and db_owner with database audit specifications. [SQL Server Audit](https://learn.microsoft.com/en-us/sql/relational-databases/security/auditing/sql-server-audit-database-engine) (2026-04-15) SEC-26.
- PostgreSQL: superusers and BYPASSRLS roles always bypass RLS, and owners do unless FORCE ROW LEVEL SECURITY is set. [PostgreSQL: Row Security Policies](https://www.postgresql.org/docs/current/ddl-rowsecurity.html) (n.d.) PGMY-07.
- Oracle: VPD does not protect against SYS or users with the default DBA role, and Oracle recommends Real Application Security over VPD for new projects. [About Oracle Virtual Private Database](https://docs.oracle.com/en/database/oracle/oracle-database/26/dbseg/oracle-virtual-private-database.html) (26ai, n.d.) MSOM-13.

**A note on OWASP's DML example.** The cheat sheet says most applications need only SELECT, UPDATE and DELETE. The list omits INSERT, which ordinary applications require. Read it as an illustration that DML is enough, not as a literal grant list.

## 5. Encryption choices and real threat models
### 5.1 What each option is
| Option | Mechanism | Where plaintext is visible | Principal sources |
|---|---|---|---|
| Disk or volume encryption | Storage layer below the database | Host and all database sessions | SEC-04 |
| TDE, file or tablespace scope | Engine encrypts pages or tablespaces on I/O | Engine memory and every authorized session | [SQL Server TDE](https://learn.microsoft.com/en-us/sql/relational-databases/security/encryption/transparent-data-encryption) (2025-09-07) SEC-24; [Oracle TDE introduction](https://docs.oracle.com/en/database/oracle/oracle-database/26/dbtde/introduction-to-transparent-data-encryption.html) (26ai, n.d.) MSOM-13 |
| Engine column encryption | Engine encrypts named columns, e.g. Oracle TDE column encryption | Authorized sessions | MSOM-13 |
| Always Encrypted | Client driver encrypts; keys never exposed to the engine | Trusted client only, unless enclaves are used | [SQL Server Always Encrypted](https://learn.microsoft.com/en-us/sql/relational-databases/security/encryption/always-encrypted-database-engine) (2026-01-28) SEC-23 |
| MongoDB CSFLE or Queryable Encryption | Application-side encryption before sending to the server | Application | SEC-30 (checklist level only; feature limits not read) |
| Application-level encryption | Application encrypts before SQL | Application | SEC-04 |
| TLS | Protects data in transit | Endpoints | SEC-01. TDE does not cover channels (SEC-24) |
### 5.2 Threat matrix
Cells are **INFERENCE** from the scope statements of the cited sources, except the TDE media-theft row (stated by Microsoft) and the DBA row for Always Encrypted (stated by Microsoft). Yes means the option addresses the threat by design; it does not mean complete protection.

| Threat | Volume | TDE | Engine column | Always Encrypted or app-level |
|---|---|---|---|---|
| Stolen drives or backup media | Yes for volumes; backups depend on where they are written | Yes (SEC-24), and TDE backups are encrypted with the DEK | Yes, for those columns | Yes, for those columns |
| Remote compromise of a running host | No (SEC-04) | No, if the attacker can act through the engine | Limited | Yes for ciphertext at the engine; No if the client or its keys are compromised |
| SQL injection through the application account | No | No | No, if the session is authorized | Reduced: the engine holds only ciphertext. The application remains an oracle for what it decrypts |
| Curious DBA or cloud operator | No | No claim made by the vendor (SEC-24) | No, in general | Yes, the stated purpose (SEC-23) |
| Over-privileged analyst | No | No | No, if authorized | Yes, if the analyst lacks key access |
| Network interception | No | No (SEC-24) | No | Partly, for encrypted columns. TLS still required |
| Compromised key store | Fails | Fails | Fails | Fails |
### 5.3 Query and schema consequences
- **Always Encrypted schema restrictions are MANDATORY (correctness) if the feature is used.** String columns need `_BIN2` collations. It is unsupported on IDENTITY, computed, sparse, partitioning columns, columns with default or CHECK constraints, DDM-masked columns and CDC-tracked columns, among others. PK, unique and FK columns are possible only under deterministic encryption. SEC-23. Scope: OLTP on SQL Server and Azure SQL.
- **Deterministic versus randomized:** deterministic allows equality lookups, joins, grouping and indexing but leaks patterns, especially for low-cardinality values. Randomized supports none of these without enclaves. SEC-23.
- **Secure enclaves** add in-place encryption, pattern matching and range comparison, on SQL Server 2019+ and Azure SQL. SEC-23. **OPTIONAL/CONTEXTUAL**.
- **Oracle:** column encryption restricts index range scans, tablespace encryption allows them, and salt cannot be used on indexed columns. MSOM-13.
- **TDE operations:** losing certificates means losing data. Backup files are encrypted with the DEK, FILESTREAM and buffer pool extension files are not encrypted, and replication does not automatically carry encryption. SEC-24. **MANDATORY (correctness)** to manage certificates accordingly.
### 5.4 Encryption principles
| ID | Principle | Label | Scope |
|---|---|---|---|
| EN-1 | Every encryption decision records the threat it addresses and those it does not | RECOMMENDED (INFERENCE from SEC-04, SEC-24) | ALL |
| EN-2 | Minimize first: do not store what is not needed | RECOMMENDED (SEC-04); MANDATORY (standard) for SAD (SEC-17) | ALL, PCI |
| EN-3 | TLS on all database connections, with certificate verification | RECOMMENDED (SEC-01) | ALL |
| EN-4 | At-rest encryption (volume or TDE) as a baseline where media or backup theft is in scope | OPTIONAL/CONTEXTUAL (SEC-24, SEC-04) | ALL |
| EN-5 | Field-level protection where privileged insiders are in scope | OPTIONAL/CONTEXTUAL (SEC-23) | FIN, PD, PHI |
| EN-6 | PAN made unreadable by a PCI-listed approach | MANDATORY (standard) (SEC-17) | PCI |
| EN-7 | Authenticated modes, AES of at least 128 bits and ideally 256, no ECB | RECOMMENDED (SEC-04) | ALL |
| EN-8 | Passwords hashed with a password-hashing algorithm, not encrypted | MANDATORY (correctness) (SEC-04) | ALL |
| EN-9 | Decide encrypted columns at design time, since features impose collation, type and constraint limits | RECOMMENDED (INFERENCE from SEC-23, MSOM-05) | OLTP |
### 5.5 Key management
- Formal lifecycle; CSPRNG generation; rotation on compromise, staff departure with access, end of cryptoperiod, usage limits or algorithm weakening. SEC-04, SEC-11. **RECOMMENDED**. Scope: ALL.
- Keep keys separate from the data so a single foothold cannot reach both. Use HSM, KMS or a secrets manager; avoid environment variables. Use envelope encryption with a separately held KEK. SEC-04. **RECOMMENDED**.
- Tagging ciphertext with a key identifier allows multiple live keys. SEC-04. **INFERENCE:** where this approach is used, the key identifier is a schema attribute.
- Tenant-held keys push designs toward isolation or grouping, and sharding makes customer-provided keys harder. CLOUD-18. **OPTIONAL/CONTEXTUAL**. Scope: SAAS.

## 6. Masking and redaction
| Technique | Data changed? | Boundary? | Source and caveat |
|---|---|---|---|
| SQL Server Dynamic Data Masking | No; query results only | **No.** Range predicates can infer values | [Dynamic Data Masking](https://learn.microsoft.com/en-us/sql/relational-databases/security/dynamic-data-masking) (2025-06-30) SEC-25. Suitable against accidental exposure, not malicious inference, and should not be used alone. Cannot be combined with Always Encrypted. Masks do not stop updates. High-privilege users can view originals |
| Oracle Data Redaction | No; query results only | **No.** WHERE clauses can be used iteratively to infer values, and it is not designed against ad hoc users | [Introduction to Oracle Data Redaction](https://docs.oracle.com/en/database/oracle/oracle-database/26/dbred/introduction-to-oracle-data-redaction.html) (26ai, n.d.) MSOM-13. Redacted values can be written back by updating applications |
| Tag-driven masking | Query results | Depends on the platform's access control | SEC-31; [Unity Catalog tags](https://docs.databricks.com/aws/en/data-governance/unity-catalog/tags) (n.d.) SEC-32; SEC-33 |
| Static masking for non-production | Yes; a separate copy | Yes for that copy, if masking is sound | SEC-08 PM-25; SEC-09 |

**Principles**
- **MS-1. Dynamic masking is a display control, never the sole control for sensitive data.** RECOMMENDED per vendor statements (SEC-25, MSOM-13). Scope: ALL.
- **MS-2. Live PANs do not enter pre-production** unless that environment is within the CDE. MANDATORY (standard) (SEC-17). Scope: PCI.
- **MS-3. Reduce PII in test, training and research.** MANDATORY (standard) federal (PM-25); RECOMMENDED otherwise. SP 800-122 says PII in a test environment is "required to be protected at the same level that it is protected in the production" environment. Scope: ALL, DE.
- **MS-4. Do not treat masked output as de-identified.** SP 800-188 warns that "not all tools that merely mask personal information provide sufficient functionality for performing de-identification." RECOMMENDED. Scope: DE, PD.
- **MS-5. Keep personal data out of tag values and metadata.** Databricks warns that tag data is stored as plain text and may be replicated. SEC-32. RECOMMENDED. Scope: DE.
### 6.1 Tokenization, pseudonymisation, anonymization
| Term | Reversible? | Status | Source |
|---|---|---|---|
| Pseudonymisation | Yes, with separately held additional information | Remains personal data | SEC-15, SEC-16 |
| De-identified (NIST) | Possibly, through a separately held code | PII impact can be low under conditions | SEC-09 |
| Anonymized (NIST) | No re-identification association remains | See Recital 26 for the GDPR test | SEC-09, SEC-15 |
| Index token (PCI) | Per scheme | One of four 3.5.1 options | SEC-17 |
| Truncation | No | Listed in 3.5.1, with correlation warning | SEC-17 |
| One-way hash of the entire PAN | No, in principle | Listed in 3.5.1 | SEC-17 |

- SP 800-122 allows a low impact level for de-identified information when, among other conditions, "The re-identification algorithm, code, or pseudonym is maintained in a separate system, with appropriate controls in place to prevent unauthorized access to the re-identification information".
- **TK-1. Hold token or pseudonym maps apart from the pseudonymised data, under separate access.** MANDATORY (legal) as part of meeting Art. 4(5), where pseudonymisation is relied on under GDPR; RECOMMENDED otherwise. Scope: PD, PCI, DE. **INFERENCE:** separating identifying attributes into dedicated tables or schemas operationalizes this at low cost, but same-database placement may not achieve the required separation against all pseudonymisation domains.
- **Gap:** tokenization vault designs were not researched. This document can state only what PCI lists and what the pseudonymisation sources say about separation.

## 7. Data discovery and metadata controls
- **DM-1. Inventory and classify sensitive data, and document required protections per level.** RECOMMENDED (ASVS 14.1.1 and 14.1.2, SEC-07). Scope: ALL.
- **DM-2. Maintain records of processing that cover categories, recipients, transfers, erasure time limits and security measures where possible.** MANDATORY (legal) (GDPR Art. 30, SEC-15), subject to the exemption reviewed by counsel. Scope: PD.
- **DM-3. Prefer machine-enforceable classification over documents.** Snowflake can bind masking policies to tags and propagate tags, Unity Catalog offers governed tags for attribute-based control, and BigQuery enforces access through policy tags. SEC-31, SEC-32, SEC-33. RECOMMENDED. Scope: DE. The notes did not examine automated classification system tags or Unity Catalog row filters.

## 8. PII classification
### 8.1 Definitions differ by regime
| Regime | Protected class | Key feature | Source |
|---|---|---|---|
| NIST SP 800-122 | PII | "any information that can be used to distinguish or trace an individual's identity" and "any other information that is linked or linkable to an individual" (agency-oriented, 2010) | SEC-09 |
| GDPR | Personal data | Any information on an identified or identifiable person | SEC-15 |
| CCPA/CPRA | Personal information; sensitive personal information | Extends to households; public information excluded | SEC-20 |
| HIPAA | ePHI | Sector-specific | SEC-18 |
| PCI DSS | Cardholder data; SAD | Field-specific rules | SEC-17 |
### 8.2 NIST impact factors
SP 800-122 says "Organizations should categorize their PII by the PII confidentiality impact level." Its level is distinct from FIPS 199. The six factors are identifiability, quantity, data field sensitivity, context of use, obligation to protect confidentiality, and access to and location of the PII. On quantity, the level "should only be raised and not lowered based on this factor". SEC-09. **RECOMMENDED**. Scope: ALL.
### 8.3 Suggested classification attributes (INFERENCE, RECOMMENDED)
No source prescribes column-level metadata fields. The set below combines what ASVS 14.1.2, GDPR Art. 30 and Art. 5(2), SP 800-122 and PCI 3.5.1 each require someone to be able to answer.

- Regime classes that apply (personal data, sensitive PI, ePHI, cardholder data, SAD, financial record)
- Identifiability: direct identifier, quasi-identifier, pseudonym, none
- Impact level
- Purpose and retention class, including legal basis
- Required treatment: encrypt, tokenize, truncate, mask, exclude from logs, exclude from non-production
- Owner or steward

A classification must follow the data, so propagation across CTAS targets, views and pipelines needs explicit handling. Snowflake documents propagation; other platforms were not examined at that depth. SEC-31.

**PI-1. Context matters.** The same fields can merit different levels depending on the population. Classify at attribute-and-context level, not by column name alone. SEC-09. RECOMMENDED. Scope: ALL.

## 9. Multi-tenant and multi-company isolation
### 9.1 Terminology
The AWS SaaS Lens defines three models: **silo** (dedicated resources per tenant under a shared onboarding and operational experience), **pool** (shared resources) and **bridge** (a mix, for example by service according to regulatory profile or noisy-neighbor attributes). [SaaS Lens: Silo, Pool, and Bridge Models](https://docs.aws.amazon.com/wellarchitected/latest/saas-lens/silo-pool-and-bridge-models.html) (2023-04-04) CLOUD-03; [SaaS Lens: Tenant Isolation](https://docs.aws.amazon.com/wellarchitected/latest/saas-lens/tenant-isolation.html) (2023-04-04) SEC-35. Microsoft uses standalone, database-per-tenant, multitenant, sharded and hybrid. [Multitenant SaaS Patterns - Azure SQL Database](https://learn.microsoft.com/en-us/azure/azure-sql/database/saas-tenancy-app-design-patterns) (2025-08-21) CLOUD-19.

Note on terms: silo, pool and bridge are **deployment models**. Database-per-tenant and schema-per-tenant are **storage realizations**. RLS is an **enforcement mechanism** applied within a pool. They are compared together below on request, but they are not alternatives on one axis.

The older AWS whitepapers (CLOUD-04) are **unverified**: fetches redirected to the SaaS Lens, and search results marked them historical. They are not used.
### 9.2 Comparison
Bracketed labels: [S] sourced; [I] inference.

| Dimension | Silo (dedicated resources) | Database-per-tenant (silo realization) | Schema-per-tenant | Pool, application filtering | Pool with RLS | Bridge or hybrid |
|---|---|---|---|---|---|---|
| Isolation strength | High [S] | High [S] (CLOUD-19) | Logical within one database; below separate databases [I] | Low; every query must be correct [S] (CLOUD-19) | Low-to-moderate; engine-enforced with documented bypasses [I from PGMY-07, MSOM-05] | Per-tier or per-service [S] |
| Cost per tenant | Highest when sized for peaks [S] | Low with elastic pools [S] | Likely between pool and DB-per-tenant [I] | Lowest for small tenants [S] | As pool, plus predicate cost [I] | Mixed [S] |
| Noisy neighbor | Avoided [S] | Reduced; pools still share [I] | Shared instance [I] | Increased risk [S] | Increased risk [I] | Isolate noisy services [S] |
| Tenants at scale | Medium, 1-100s for standalone [S] | High, 1-100,000s [S] | **No source** | Very high; up to about 1,000,000s when sharded [S] | Same as pool [I] | Mixed |
| Per-tenant restore | Simple [S] | No effect on others [S] | Likely needs selective recovery [I] | Restore to a side copy, then selective recovery [S] (CLOUD-18) | As pool [I] | By placement [S] |
| Tenant-held keys | Natural fit [S] | Natural fit [S] | **No source** | Hard; difficult when sharded [S] | Hard [I] | Silo tenants only [I] |
| Schema customization | Straightforward [S] | Straightforward [S] | Possible, at migration cost [I] | Difficult [S] | Difficult [I] | Silo tenants only [S] |
| Migration burden | Per deployment | Automate; track version per tenant [S] | Many copies to migrate [I] | One schema [I] | One schema, plus policies [I] | Must support both [I] |
| Residency | Natural fit [S] | Natural fit [S] | Not by itself [I] | Needs grouping or sharding [I] | As pool [I] | Group by region [I] |
| Typical trigger | Regulation, own keys, own backups, residency [S] | Same, at larger counts [S] | **Not recommended by any fetched source** | Many small tenants [S] | Pool needing engine-level enforcement [I] | Tiers such as trial and premium [S] |
| Schema implication | Tenant catalog | Tenant catalog; schema version per database [S] | Tenant-to-schema map [I] | Tenant identifier on every tenant-scoped table [S] | Same, plus policy on every such table [I] | Tenant identifier retained even in single-tenant databases [S] |

Microsoft's table-based isolation antipattern refers to per-tenant tables in a single database. Applying it to schema-per-tenant is an **INFERENCE**: the sources do not discuss PostgreSQL-style schemas per tenant.

Comparison sources: CLOUD-03, CLOUD-18, CLOUD-19, SEC-35; [Citus: Multi-tenant Applications](https://docs.citusdata.com/en/stable/use_cases/multi_tenant.html) (n.d.) PERF-44; [Salesforce: Platform Multitenant Architecture](https://architect.salesforce.com/fundamentals/platform-multitenant-architecture) (n.d.) TEN-07.
### 9.3 Tenancy principles
| ID | Principle | Label | Scope | Basis |
|---|---|---|---|---|
| TN-1 | Every tenant-scoped table in a pooled or sharded database carries a tenant identifier | MANDATORY (correctness) | SAAS | CLOUD-19, PERF-44 |
| TN-2 | No query exposes data from more than one tenant unless explicitly designed to | MANDATORY (correctness) | SAAS | CLOUD-19, SEC-35 |
| TN-3 | Tenant identity reaches the data layer on every request | RECOMMENDED where engine enforcement is used; otherwise the application tier must supply an equivalent guarantee | SAAS | CLOUD-18 |
| TN-4 | Tenant identifier leads the primary key on sharded tables; include it in foreign keys where the distribution model requires | MANDATORY (correctness) on platforms that require it (CLOUD-19 split/merge; PERF-44); RECOMMENDED otherwise | SAAS | CLOUD-19, PERF-44 |
| TN-5 | Unique constraints in pooled tables are scoped by tenant | RECOMMENDED (INFERENCE from PGMY-07 covert-channel warning and PERF-44) | SAAS | PGMY-07 |
| TN-6 | Maintain a tenant catalog; automate onboarding, retention, offboarding and restore | RECOMMENDED | SAAS | CLOUD-18, CLOUD-19 |
| TN-7 | Avoid per-tenant tables and per-tenant columns | RECOMMENDED | SAAS | CLOUD-18 |
| TN-8 | Use silo isolation when tenants need their own keys, backup policy, geography or regulatory separation | OPTIONAL/CONTEXTUAL | SAAS | CLOUD-18, CLOUD-03 |
| TN-9 | Choose deliberately, because changing tenancy model later can be costly | RECOMMENDED | SAAS | CLOUD-19 |
### 9.4 RLS engineering notes
- **Defaults:** when PostgreSQL RLS is enabled with no policy, access is default-deny. Permissive policies combine with OR and restrictive ones with AND. PGMY-07.
- **Bypasses:** PostgreSQL superuser, BYPASSRLS and owner unless FORCE is set. SQL Server policies apply to dbo, but dbo can alter them. Oracle VPD does not bind SYS. PGMY-07, MSOM-05, MSOM-13.
- **Side channels:** referential-integrity checks bypass RLS in PostgreSQL, enabling covert-channel leaks, and only leakproof functions run before the policy. SQL Server documents error-based inference, using a divide-by-zero example. PGMY-07, MSOM-05.
- **Cross-feature leaks on SQL Server:** Change Data Capture can leak entire rows, Change Tracking leaks primary keys, statistics access is restricted, indexed views cannot be created over RLS tables, and **temporal history tables need their own predicate**. MSOM-05. History, CDC and analytical copies are therefore within the isolation scope. **MANDATORY (correctness)** where RLS is the isolation control.
- **Middle-tier pattern:** SQL Server documents setting read-only `SESSION_CONTEXT` after connecting. MSOM-05. The common PostgreSQL session-setting approach is **not in the official page read**.
- **Performance:** policies that use only current-row values are the simplest and best-performing case. PGMY-07. No quantitative overhead was found.
- **Operational view:** Azure says identity propagation is complex and that many multitenant solutions avoid RLS for that reason. CLOUD-18.
- **RL-1. FORCE RLS or equivalent for owners, and test with non-privileged roles.** RECOMMENDED. Scope: SAAS, on engines offering it.
- **RL-2. Place RLS objects in a separate schema, and avoid type conversions, recursion and excessive joins in predicates.** RECOMMENDED (MSOM-05). Scope: SAAS on SQL Server, and INFERENCE as a general practice.
### 9.5 Multi-company within a tenant
- ERP systems treat the company or legal entity as a posting, statutory and often security boundary. Dynamics 365 uses DataAreaId as a data-security boundary in some functional areas. [Organizations and organizational hierarchies overview](https://learn.microsoft.com/en-us/dynamics365/fin-ops-core/fin-ops/organization-administration/organizations-organizational-hierarchies) (2026-04-24) TEN-08.
- NetSuite arranges subsidiaries as a tree to a root. A transaction generally posts to one subsidiary, except intercompany transactions, which post to two or more and are eliminated through elimination subsidiaries. [Subsidiaries in OneWorld](https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_N268563.html) (n.d.) TEN-09.
- Odoo separates companies and branches, with products and contacts shared by default but restrictable. [Odoo 18.0: Companies](https://www.odoo.com/documentation/18.0/applications/general/companies.html) (n.d.) TEN-10. Dynamics says shared master data cannot be overridden per organization, so vendors differ here.

| ID | Principle | Label | Scope |
|---|---|---|---|
| MC-1 | Tenant and company are separate identifiers: one is the customer boundary, the other the legal and posting boundary | RECOMMENDED (INFERENCE from TEN-08, TEN-09) | ERP, SAAS |
| MC-2 | Every posting line is attributable to exactly one company; an intercompany document is decomposed per company | RECOMMENDED (INFERENCE; NetSuite allows one transaction to post to two or more, so the decomposition is a modeling choice) | ERP |
| MC-3 | Company is treated as an access-control dimension where users are restricted by entity | OPTIONAL/CONTEXTUAL (TEN-08) | ERP |
| MC-4 | Company hierarchy with elimination entities for consolidation | RECOMMENDED (TEN-08, TEN-09) | ERP |

Company-level filtering is an authorization rule within a tenant and does not replace tenant isolation. That is an **INFERENCE**. Cross-company roles such as group accountants need explicit modeling.

## 10. Audit trails and tamper evidence
### 10.1 Layers
| Layer | Captures | Atomic with the change? | Tamper limit | Sources |
|---|---|---|---|---|
| Audit columns | Last creator or updater and time | Yes | Overwritten by design; not a history | [ActiveRecord::Timestamp](https://api.rubyonrails.org/classes/ActiveRecord/Timestamp.html) (Rails 8.1, n.d.) TEN-45 |
| ORM or application history | Revisions, application user, reason | Yes for ORM writes | Misses changes made outside the application | [Hibernate Envers](https://hibernate.org/orm/envers/) (n.d.) TEN-15; [django-simple-history](https://django-simple-history.readthedocs.io/en/latest/) (2026-07-22), catalogued with TEN-45 |
| Trigger shadow tables | Row-level changes and session details | Yes | No SELECT, DDL or catalog coverage; owner and superuser can tamper | TEN-11 |
| System-versioned history | Prior row versions | Yes, per engine | Period columns not user-editable; engine admins remain a risk (INFERENCE) | section 11 |
| Engine audit logs | Access, DDL and role events | No in pgAudit: best-effort, not transactional | Superusers cannot be reliably audited; sysadmin can tamper | [pgAudit](https://github.com/pgaudit/pgaudit) (n.d.) SEC-27; SEC-26; SEC-28 |
| Cryptographic ledger | Row hashes chained in blocks | Yes, per engine | Detects on verification; does not prevent; digests must be outside | [Ledger overview](https://learn.microsoft.com/en-us/sql/relational-databases/security/ledger/ledger-overview) (2025-08-07) TEN-14 |

Oracle's unified audit table allows INSERT only, and direct truncate, delete or update attempts fail and are themselves audited; mandatory audits cannot be turned off. SEC-28. Default policies differ between 19c and 26ai documentation (MSOM-13), so version must be specified.

Amazon QLDB should not be selected: end of support was reported as 2025-07-31, by a secondary source. [AWS to Kill QLDB](https://www.infoq.com/news/2024/07/aws-kill-qldb) (2024-07-26) TEN-16. AWS's own wording could not be verified.
### 10.2 Audit principles
| ID | Principle | Label | Scope | Basis |
|---|---|---|---|---|
| AU-1 | Mechanisms record and examine activity on ePHI | MANDATORY (legal) | PHI | SEC-18 |
| AU-2 | Audit logs capture all individual user access to cardholder data; protected from modification; 12 months retained with three immediately available | MANDATORY (standard) | PCI | SEC-17 |
| AU-3 | Secure, computer-generated, time-stamped audit trail; changes do not obscure earlier information; retained at least as long as the record | MANDATORY (legal) | FDA only ([21 CFR 11.10](https://www.law.cornell.edu/cfr/text/21/11.10), n.d., TEN-17) | TEN-17 |
| AU-4 | Same non-obscuring pattern for financial records | RECOMMENDED (INFERENCE by analogy; Part 11 does not apply to financial records as such) | FIN, ERP | TEN-17, TEN-42, TEN-43 |
| AU-5 | Posted ledger entries are not updated or deleted; corrections are new entries | MANDATORY (correctness) for ledgers claiming immutability; RECOMMENDED design otherwise | FIN | TEN-41, TEN-42, TEN-43 |
| AU-6 | Audit tables are not writable by the application's business role | MANDATORY (correctness) if the trail is relied on | ALL | TEN-11, SEC-05 |
| AU-7 | Combine same-transaction change capture with engine access logging, because each misses what the other sees | RECOMMENDED (INFERENCE) | OLTP, ERP, FIN | TEN-11, SEC-27 |
| AU-8 | Carry the real user into the audit record | MANDATORY (standard) for PCI individual attribution; RECOMMENDED otherwise | ALL | SEC-17, TEN-15 |
| AU-9 | Exclude secrets and sensitive values from logs; pseudonymize where identity is not needed | RECOMMENDED; MANDATORY (standard) for card data per the notes' reading of PCI scope | ALL | SEC-05 |
| AU-10 | Ship engine audit to storage the DBA cannot alter; report from a separate instance | RECOMMENDED | FIN, PCI | SEC-26, SEC-05 |
| AU-11 | Hash-chained digests held outside DBA control when third-party attestation is needed | OPTIONAL/CONTEXTUAL | FIN | TEN-14 |
| AU-12 | Audit stores are classified themselves, since before-and-after images copy sensitive values | RECOMMENDED (INFERENCE from TEN-11, SEC-05) | ALL | SEC-05 |

**Tamper resistance, tamper evidence and tamper proofing are different claims.** Permissions resist tampering. Hash chains with external digests provide evidence. None of the sources supports claiming that privileged tampering is impossible. Microsoft's ledger documentation itself says tampering is detected on verification, not prevented. TEN-14.

## 11. History and temporal retention
### 11.1 Two time dimensions
[Temporal features in SQL:2011](https://sigmodrecord.org/publications/sigmodRecord/1209/pdfs/07.industry.kulkarni.pdf) (SIGMOD Record, 2012-09) GOV-06 distinguishes application time, set by users, from system time, maintained by the system. A table with both is bitemporal. [Snodgrass, Developing Time-Oriented Database Applications in SQL](https://www2.cs.arizona.edu/~rts/tdbbook.pdf) (2000) TEN-23 prefers closed-open periods.

| Engine | System time | Application time | Security or retention note |
|---|---|---|---|
| SQL Server | Yes: [Temporal tables](https://learn.microsoft.com/en-us/sql/relational-databases/tables/temporal-tables) (2026-08-18) MSOM-04 | Not described on the page read | **RLS predicates are not copied to the history table**, nor are indexes, partitioning or check constraints |
| MariaDB | Yes: [System-Versioned Tables](https://mariadb.com/docs/server/reference/sql-structure/temporal-tables/system-versioned-tables) (n.d.) TEN-20 | Not read | DELETE HISTORY is privileged; dumps need an explicit history option |
| Oracle | Flashback Time Travel: [Using Oracle Flashback Technology](https://docs.oracle.com/en/database/oracle/oracle-database/19/adfns/flashback.html) (19c, n.d.); 26ai in MSOM-14 | Temporal Validity: [12.2 VLDB Guide](https://docs.oracle.com/database/122/VLDBG/control-validity-visibility-data.htm) (n.d.) TEN-21 | Retention setting purges older history. The 12.2 page says Temporal Validity is unsupported in a CDB; since other notes say multitenant is the only supported architecture from 21c, current support must be re-verified |
| PostgreSQL 18 | No native feature in the release notes | WITHOUT OVERLAPS and PERIOD constraints: [PostgreSQL 18 Release Notes](https://www.postgresql.org/docs/18/release-18.html) (2025-09-25) PERF-16 | The absence claim rests on the release notes alone |
### 11.2 Principles
| ID | Principle | Label | Scope | Basis |
|---|---|---|---|---|
| HT-1 | State explicitly which time dimension each history mechanism records | RECOMMENDED | ALL | GOV-06 |
| HT-2 | Where history is relied on as evidence, the system maintains it and users cannot edit period values | MANDATORY (correctness) for that reliance | FIN, FDA | GOV-06, TEN-17 |
| HT-3 | Use closed-open periods | RECOMMENDED | ALL | GOV-06, TEN-23, MSOM-04 |
| HT-4 | Apply non-overlap constraints per business key where the engine supports them | RECOMMENDED | OLTP, ERP | GOV-06, PERF-16 |
| HT-5 | Store period timestamps in UTC where the engine does not fix this | RECOMMENDED | ALL | MSOM-04 |
| HT-6 | Apply access control, masking and classification to history as separately as to current data | MANDATORY (correctness) when the base table is protected | ALL | MSOM-05, MSOM-04 |
| HT-7 | Use bitemporal modeling only where as-known-at reconstruction is required | OPTIONAL/CONTEXTUAL | FIN, ERP | GOV-06, TEN-23 |
| HT-8 | Partition history by system time where retention needs it | OPTIONAL/CONTEXTUAL | OLTP, DE | TEN-20, MSOM-14 |
| HT-9 | Define the backdated-change rule explicitly, since SQL:2011 and Workday behave differently | RECOMMENDED | ERP | GOV-06, [Workday effective dating](https://doc.workday.com/admin-guide/en-us/human-capital-management/compensation/manage-compensation/meq1649709028535.html) (2025-05-02) TEN-25 |

Analytical history: Kimball SCD Type 2 retains prior attribute values as dimension rows. [Design Tip #152](https://www.kimballgroup.com/2013/02/design-tip-152-slowly-changing-dimension-types-0-4-5-6-7/) (2013-02-05) TEN-24. **INFERENCE:** Type 2 dimensions containing personal attributes extend the erasure and retention scope.

**SQL:2011 tamper language.** Kulkarni and Michels describe system-versioned history as protected from tampering because users cannot change period columns. **Do not read this as resistance to privileged operators.** Vendors supply purge paths such as MariaDB DELETE HISTORY and Oracle retention, and section 10 records the privileged-user limit.

## 12. Soft deletes, erasure and retention
### 12.1 Soft delete
Brandur Leach argues that per-row soft deletion is rarely worthwhile: every query must filter, foreign keys stop protecting integrity, and privacy purges become complicated. He proposes hard deletion with a separate deleted-record archive. [Soft Deletion Probably Isn't Worth It](https://brandur.org/soft-deletion) (2022-07-19) TEN-30; [deleted_record_insert](https://brandur.org/fragments/deleted-record-insert) (2022-12-28), catalogued with TEN-30. GitLab prefers mark-for-deletion, at project and group level, with later removal. [GitLab: Data deletion guidelines](https://docs.gitlab.com/development/deleting_data) (n.d.) TEN-31. Both are single-organization engineering views, not standards.

The positions reconcile as a bounded grace period at aggregate roots, followed by true removal (per the notes' synthesis, INFERENCE).

| ID | Principle | Label | Scope |
|---|---|---|---|
| SD-1 | A flag alone does not satisfy an applicable erasure duty | MANDATORY (legal) where such a duty applies, as an **INFERENCE** from Art. 17, Art. 5(1)(e) and Recital 26. No source names soft deletion | PD |
| SD-2 | Avoid pervasive per-row deleted flags; prefer an archive or aggregate-level marking with scheduled purge | RECOMMENDED | OLTP, SAAS |
| SD-3 | A deleted-record archive is itself in retention and erasure scope, since it holds whole rows | RECOMMENDED (INFERENCE) | ALL |
| SD-4 | If a deleted flag is retained, enforce uniqueness on live rows | RECOMMENDED (INFERENCE; no source states the remedy) | OLTP |
### 12.2 What erasure has to reach (INFERENCE, RECOMMENDED; Scope: PD)
No opened source enumerates this. It follows from Art. 17 applying to the personal data rather than a particular table:
- Current tables and soft-delete or archive tables
- History tables, ledger structures and SCD dimensions
- Audit logs, as far as they contain identifiable values
- Search indexes, caches (ASVS 14.2.2), replicas, CDC topics and downstream warehouses
- Non-production copies
- Backups. Regulator text is now in section 12.7. It does not settle timing in the EU, so a policy decision with counsel is still required

CDC can carry deletes downstream: [Debezium Features](https://debezium.io/documentation/reference/stable/features.html) (n.d.) TEN-26. Whether consumers apply those deletes is a design responsibility. Primary keys or replica identity are required for PostgreSQL publications to capture UPDATE and DELETE: [PostgreSQL: Publication](https://www.postgresql.org/docs/current/logical-replication-publication.html) (n.d.) TEN-28.
### 12.3 Retention floors and what they actually cover
| Source | Period | **Actually covers** | Do not assume |
|---|---|---|---|
| SOX, 18 U.S.C. §1520(a)(1), SEC-19, TEN-36 | 5 years from end of the fiscal period of the audit | Auditor workpapers | A general 5-year rule for an issuer's ERP data |
| SOX §103, SEC-19 | Not less than 7 years | Audit work papers of registered firms | Same as above |
| HIPAA 45 CFR 164.316(b)(2)(i), [LII](https://www.law.cornell.edu/cfr/text/45/164.316) (n.d.) TEN-37 | 6 years from creation or last effective date | Documentation required by (b)(1) | A retention period for ePHI itself. Whether specific audit logs fall in scope is for counsel |
| PCI DSS 10.5.1, SEC-17 | 12 months, with three immediately available | Audit log history | A retention basis for other cardholder data |
| 21 CFR 11.10(e), TEN-17 | At least as long as the subject record | Audit trail documentation | Application outside FDA-regulated records |
| GDPR Art. 5(1)(e), SEC-15 | No fixed period; no longer than necessary | Identifiable personal data | That a fixed retention period is lawful automatically |
| SP 800-53 AU-11, SEC-08 | Organization-defined | Audit records | Any specific number |

VAT, tax and accounting-law retention periods by jurisdiction, likely the most important floors for ERP, are in section 12.6. The earlier gov.uk 404 no longer applies: note 19 read VAT Notice 700/21 (LEG-13).

The third-party PCI transcription (TEN-38) is superseded here by the PDF-extracted SAQ D text.
### 12.4 Retention principles
| ID | Principle | Label | Scope |
|---|---|---|---|
| RT-1 | Maintain a retention schedule per record class, with the basis documented and enforcement in place | MANDATORY (legal) where GDPR applies, to the extent of Art. 5(1)(e), 5(2) and 30; RECOMMENDED elsewhere | ALL |
| RT-2 | Honor applicable erasure requests without undue delay, unless an exception applies | MANDATORY (legal) | PD |
| RT-3 | Record the applicable basis at record-class level, not per row unless necessary | RECOMMENDED (INFERENCE) | ALL |
| RT-4 | Support legal hold that suspends purge | OPTIONAL/CONTEXTUAL (INFERENCE; no source covers database legal-hold mechanics). Treat as strongly advisable for FIN | FIN, ERP |
| RT-5 | Date-partition large tables so retention is a partition operation | RECOMMENDED ([PostgreSQL: Table Partitioning](https://www.postgresql.org/docs/current/ddl-partitioning.html), n.d., PGMY-06) | OLTP, DE |
| RT-6 | Keep object-store expirations aligned with the schedule. A bucket policy cannot prevent lifecycle deletion, so lifecycle rules are themselves a risk to retained records | RECOMMENDED ([Managing the lifecycle of objects](https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lifecycle-mgmt.html), n.d., TEN-35) | DE |
### 12.5 Crypto-shredding: status and preconditions
**Crypto-shredding as erasure is not settled law.** No regulator text found says that destroying a key counts as erasure under Art. 17, and no opened source endorses per-subject keys as Art. 17 erasure. Unless a source is quoted, everything below is **INFERENCE**; label it **OPTIONAL/CONTEXTUAL** (backups, event logs, immutable stores), and obtain counsel's view before relying on it.

Regulator text closest to the point:
- [EDPB Guidelines 02/2025 on blockchain](https://www.edpb.europa.eu/system/files/2025-04/edpb_guidelines_202502_blockchain_en.pdf) (2025-04-08, **public consultation version**) LEG-34: "upon deletion of this decryption key, the encrypted data will be unintelligible, at least until the algorithm is broken, the decryption techniques advance sufficiently to allow the decryption of the cipher text, or if the key had already been compromised or leaked. The EDPB recalls that encrypted personal data is still personal data and encryption does not remove the need for GDPR compliance." This describes an effect and its limits, on a different technology. It is not acceptance of key destruction as erasure.
- ICO encryption scenarios ([Wayback capture 2026-03-05](https://web.archive.org/web/20260305151002/https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/security/encryption/encryption-scenarios/), recorded under LEG-33; **needs confirmation on the live site**): "If you encrypt your backups, you should have good key management in place" and "You must consider the right to erasure under Article 17 of the UK GDPR, and how this may apply, when determining both your use of encryption and the retention period of your backups."
- CNIL, AEPD and Datatilsynet positions were searched for and not found. The search result pointing to an AEPD note on blockchain was not read.

SP 800-88 Rev. 2 supports the underlying technique for media sanitization, which is a different question from legal erasure:
- "CE is based on the sanitization of keys used to encrypt data or to prevent access to the keys that encrypt data."
- "As a pre-condition for using CE, ISO/IEC 27040 specifies that no sensitive data has previously been stored on the ISM in plaintext form (i.e., not encrypted) as CE can only sanitize keys related to encrypted data." (ISO/IEC 27040 is known here only through this reference.)
- "Sanitization using CE should not be trusted on ISM that have been backed up or escrowed unless the organization has a high level of confidence regarding how and where the keys were stored and managed outside of the ISM."

Preconditions for engineering credibility:
1. Data was encrypted before first write everywhere it lands, including replicas, CDC streams, logs and caches.
2. Key backups and escrow are governed, so deletion can be shown to be effective. OWASP's advice to retain old keys for backups (SEC-04) works against this and needs reconciling in design.
3. Key destruction is recorded. SP 800-88 calls for traceability.
4. Remaining plaintext such as quasi-identifiers is assessed. Ciphertext with a destroyed key may still sit beside identifying data, and Recital 26 sets a demanding test.
5. Cryptographic-strength expectations over the retention horizon are considered (SP 800-57, SEC-11).
### 12.6 Retention by jurisdiction
Research input only, not legal advice; each row needs review by counsel for the entity concerned. **MANDATORY (legal)** for the stated records and population, unless noted. Scope: ERP, FIN. DE where warehouse or lake copies hold the same records, because the duty attaches to the records and not to one store (note 19). All from note 19.

| Jurisdiction | Record | Period | Starts | Source |
|---|---|---|---|---|
| Germany (tax) | Books, records, annual accounts | 10 years | End of calendar year of last entry or creation | AO 147(3),(4), LEG-05 |
| Germany (tax) | Booking vouchers | 8 years | As above | AO 147(3),(4), LEG-05 |
| Germany (tax) | Other listed documents | 6 years | As above | AO 147(3),(4), LEG-05 |
| Germany (VAT) | Invoice copies issued and invoices received | 8 years | End of calendar year of invoice issue | UStG 14b(1), LEG-04 |
| Germany (commercial) | Books; booking vouchers; other documents | 10; 8; 6 years. Institutions under KWG and listed categories: booking vouchers 10 | End of calendar year | HGB 257(4),(5), LEG-05 |
| France (tax) | Books, records, documents | 6 years | Date of last transaction or document | LPF L102 B via BOFiP, LEG-09 |
| France (commercial) | Accounting documents | 10 years (**search snippet**; CNIL also cites 10 years for billing data) | See source | Code de commerce L123-22, not opened |
| UK (VAT) | Business records for VAT | At least 6 years | See source | Notice 700/21, LEG-13 |
| UK (Companies Act) | Accounting records | Private 3 years; public 6 years | "from the date on which they are made" | CA 2006 s388(4), LEG-15 |
| US (IRS, income tax) | Records supporting return | 3 years generally; 3 from filing or 2 from payment if refund claim, whichever is later; 7 for worthless securities or bad debt; 6 if income under-reported by more than 25%; indefinitely if no return or fraudulent return | Generally after return filed | IRS page, LEG-16 |
| US (IRS, employment) | Employment tax records | At least 4 years | After tax due or paid, whichever is later | IRS page, LEG-16 |
| US (broker-dealers only) | 17a-3(a)(1)-(3),(5),(21),(22) records | 6 years, first 2 easily accessible | See rule | 17 CFR 240.17a-4(a), LEG-17 |
| US (broker-dealers only) | Listed 17a-3 records | 3 years, first 2 easily accessible | See rule | 17a-4(b), LEG-17 |
| US (broker-dealers only) | Account opening and terms records | 6 years | After account closing | 17a-4(c), LEG-17 |
| Pakistan (sales tax) | Records and documents | 6 years, or until proceedings are finally decided | After end of tax period | STA s24, LEG-18 |
| Pakistan (e-invoicing) | Real-time e-invoices, debit and credit notes of integrated persons | "six years" on electronic media | As STA s24 | Rule 150S, LEG-19 |
| Pakistan (income tax) | Prescribed accounts and documents | 6 years, or until proceedings end | After end of tax year | ITO s174(3), LEG-20 |
| Pakistan (companies) | Books of account with vouchers | "not less than ten financial years immediately preceding a financial year" | See text | Companies Act 2017 s220(5), LEG-21 |
| UAE (tax) | Accounting records, books, information | Taxable persons 5 years; others 5 years | After tax period; others from end of calendar year of creation | Cabinet Decision 74/2023 Art 3, LEG-23 |
| UAE (tax) | Real estate records | 7 years | End of calendar year of creation | Art 3(1)(c), LEG-23 |
| UAE (tax) | Extensions | 4 more years for disputes (or until settled, whichever later), audits or audit notice; 1 year for voluntary disclosure in fifth year | | Art 3(2), LEG-23 |
| Saudi Arabia (VAT) | All records | At least 6 years | End of related tax period | ZATCA guide 8.3.3, LEG-25 |
| Saudi Arabia (VAT) | Movable capital assets | Adjustment period plus 5 years | Date of acquisition | ZATCA guide, LEG-25 |
| Saudi Arabia (VAT) | Real estate | At least 15 years | | ZATCA guide, LEG-25 |

Sources: [AO s.147](https://www.gesetze-im-internet.de/ao_1977/__147.html) LEG-05; [UStG s.14](https://www.gesetze-im-internet.de/ustg_1980/__14.html) LEG-04, with s.14b; [BOFiP conservation](https://bofip.impots.gouv.fr/bofip/8877-PGP.html/identifiant=BOI-CF-COM-10-10-30-10-20140528) LEG-09 (version in force 2013-10-18 to 2014-05-28, may have been replaced); [VAT Notice 700/21](https://www.gov.uk/guidance/record-keeping-for-vat-notice-70021) LEG-13; [CA 2006 s.388](https://www.legislation.gov.uk/ukpga/2006/46/section/388) LEG-15; [IRS, How long should I keep records](https://www.irs.gov/businesses/small-businesses-self-employed/how-long-should-i-keep-records) LEG-16; [17 CFR 240.17a-4](https://www.law.cornell.edu/cfr/text/17/240.17a-4) LEG-17; [Sales Tax Act 1990](https://download1.fbr.gov.pk/Docs/202586148252375SalesTaxActupdatedupto2025-26.pdf) LEG-18; [Sales Tax Rules 2006](https://download1.fbr.gov.pk/Docs/2025881385446623STR-2006-UpdatedUpto06-08-2025(ver-iv).pdf) LEG-19; [Income Tax Ordinance 2001](https://download1.fbr.gov.pk/Docs/2025881983148210Income-Tax-Ordinance,-2001-Amended-upto-31.07.2025.pdf) LEG-20; [Companies Act 2017](https://pakistancode.gov.pk/pdffiles/administrator89de324eeaa53c96ff701820d2e007e4.pdf) LEG-21; [Cabinet Decision 74 of 2023](https://tax.gov.ae/Datafolder/Files/Legislation/Cabinet%20Decision%20No.%2074%20of%202023%20on%20Executive%20Regulation%20of%20Federal%20Decree-Law%20No.%2028%20of%202022%20on%20Tax%20Procedures%20-%20For%20Publishing.pdf) LEG-23; [ZATCA invoicing guideline](https://zatca.gov.sa/en/HelpCenter/guidelines/Documents/Guideline-for-Tax-Invoicing-and-Records-under-VAT-Provisions.pdf) LEG-25.

- **EU.** Art. 247(1) of the [VAT Directive](https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:02006L0112-20250414) (consolidated 2025-04-14) LEG-01: "Each Member State shall determine the period throughout which taxable persons must ensure the storage of invoices". The Directive sets no period. Art. 233(1) requires that "The authenticity of the origin, the integrity of the content and the legibility of an invoice, whether on paper or in electronic form, shall be ensured from the point in time of issue until the end of the period for storage of the invoice." **MANDATORY (legal)**. Scope: ERP, FIN.
- **Disposal is not a date check alone.** AO 147(3): the period "läuft jedoch nicht ab, soweit und solange die Unterlagen für Steuern von Bedeutung sind, für welche die Festsetzungsfrist noch nicht abgelaufen ist". INFERENCE: a legal-hold or assessment check is needed before disposal. This strengthens RT-4 for German tax records.
- **Germany, migration.** Section 147 has a rule that after a system change, data may be held only on a machine-readable carrier once the fifth following calendar year has ended (note 19). Affects archive design.
- **UK.** Notice 700/21 says HMRC may allow a shorter period for some records on request, and other taxes may need longer.
- **Pakistan.** ITO s174(3) final proviso says the limit "shall not apply to the records pertaining to income, assets, expenses or transactions to which clause (ii) of sub-section (2) of section 111 applies." Companies Act record rules for resolutions (20-year physical, permanent electronic, and a further 10-year rule) were read without confirming each section number. Check before use.
- **UAE.** E-invoicing Guidelines V2.0, section 5.4, apply the same periods to e-invoice issue, transmission and receipt data, retained "in an electronic system that preserves their integrity" ([Guidelines V2.0](https://mof.gov.ae/wp-content/uploads/2026/10/UAE-Electronic-Invoicing-Guidelines_En.pdf), 2026-10-26, LEG-24).
- **Saudi Arabia, data location.** Records "must be retained within the Kingdom", with a workstation exception for permanent establishments with centralised systems abroad, and "records must be retained in the Arabic language". **MANDATORY (legal)**. Scope: ERP, FIN, SAAS deployment; KSA VAT scope only.
- **Broker-dealers only.** 17a-4(f)(2)(i): a system must either "(A) Preserve a record for the duration of its applicable retention period in a manner that maintains a complete time-stamped audit trail" of modifications and deletions, or "(B) Preserve the records exclusively in a non-rewriteable, non-erasable format". Do not apply this to general SaaS.

**Conflicts recorded.**
- France: tax 6 years against commercial 10 years. A search snippet says the BOFiP treats the tax provisions as independent of L123-22. The longer period would apply where both apply.
- Germany: 8 years for vouchers replaced the former 10. A search snippet reports this applies only to vouchers whose period had not ended before 1 January 2025. The transitional provision was not read.
- US IRS periods are limitation-driven, not a flat retention rule.
- Italian and Spanish retention periods were not researched in depth.
### 12.7 Erasure mechanics: regulator and California text
Regulators address these mechanics unevenly and do not agree in detail. All from note 19.

**EDPB** ([CEF report on the right to erasure](https://www.edpb.europa.eu/system/files/2026-02/edpb_cef-report_2025_right-to-erasure_en.pdf), adopted 2026-02-10) LEG-32:
- "It is therefore important to protect the integrity of the back-up. Depending on the technical settings and risks, it might not always be advisable to modify or delete information from back-ups. But, in that case, organisations should have appropriate procedures to keep track of erasure requests and comply with them on restored systems, as much as possible, in case of a data breach affecting the integrity of the organisation's system."
- Possible EDPB action: "Providing more guidance and recommendations to explain how controllers should practically deal with erasure in back-ups and what is meant by "without undue delay" in this context."
- For controllers: "Follow established standards to erase and destroy data in a secure and structured manner." and "Verify that erasure has been carried out and be able to demonstrate such erasure."
- Practices noted: replacing personal data with strings of random characters, and tools that move data out of employee reach for later deletion. One supervisory authority found incremental deletion over long periods made it hard to conclude deletion happened without undue delay.

**ICO** ([Right to erasure, Wayback capture 2026-10-29](https://web.archive.org/web/20261029043746/https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/individual-rights/individual-rights/right-to-erasure/)) LEG-33. **Read from a Wayback capture because the live site refused access (HTTP 403); needs confirmation on the live site.**
- "If a valid erasure request is received and no exemption applies then you will have to take steps to ensure erasure from backup systems as well as live systems."
- "The key issue is to put the backup data 'beyond use', even if it cannot be immediately overwritten."
- "You must be absolutely clear with individuals as to what will happen to their data when their erasure request is fulfilled, including in respect of backup systems."

**Dutch AP** ([Right to erasure, Wayback capture 2026-03-21](https://web.archive.org/web/20260321104218/https://autoriteitpersoonsgegevens.nl/en/themes/basic-gdpr/privacy-rights-under-the-gdpr/right-to-erasure)) LEG-35. **Read from a Wayback capture because the live site refused access; needs confirmation on the live site.**
- "Backups also fall under the right to erasure."
- "Do you have backups that cannot or cannot easily be overwritten, such as tapes? Then you cannot erase the personal data from the backups. Make sure that you keep proper records of which personal data you should have erased. Is restoring a backup necessary? Then you will have to erase these data when you do this."

**California** ([CCPA Regulations, effective 1/1/2026](https://cppa.ca.gov/regulations/pdf/ccpa_statute_eff_20260101.pdf)) LEG-29, section 7022: "If a business, service provider, or contractor stores any personal information on archived or backup systems, it may delay compliance with the consumer's request to delete, with respect to data stored on the archived or backup system, until the archived or backup system relating to that data is restored to an active system or is next accessed or used for a sale, disclosure, or commercial purpose." The file name at that URL suggests a statute, but it held the Regulations when read.

| ID | Principle | Label | Scope | Basis |
|---|---|---|---|---|
| ER-1 | Keep a durable record of erasure requests outside the backups and re-apply erasure after any restore | RECOMMENDED; common element in EDPB, AP and California text, ICO consistent | ALL, PD | LEG-29, LEG-32, LEG-35 |
| ER-2 | Re-apply deletion on restore or next use | MANDATORY (legal) in CCPA scope | PD | LEG-29 |
| ER-3 | Define backup retention so data expiry is predictable | RECOMMENDED. EDPB shows retention alone is not always seen as adequate | ALL, PD | LEG-32, LEG-33 |
| ER-4 | Propagate deletion to service providers, contractors and third parties | MANDATORY (legal) in CCPA scope | PD, DE | LEG-28 |
| ER-5 | Be able to demonstrate that erasure was carried out | RECOMMENDED | PD | LEG-32 |

**Not settled.**
- How long "without undue delay" lasts for backups in the EU. The EDPB itself lists this for possible guidance.
- Key destruction as erasure (section 12.5).
- Soft deletion. No regulator text found addresses soft deletion or a deleted flag by name. Indirect sources only: [CNIL retention page](https://www.cnil.fr/fr/les-durees-de-conservation-des-donnees) (n.d.) LEG-36, paraphrased, says intermediate archives must be separated from the active base physically or logically by restricted access, which is about retention, not erasure. The ICO's beyond-use concept is stated for backups and does not extend to live tables in the text read. SD-1 remains an inference.

**Conflict.** The regimes differ on how far deletion from backups may wait: the ICO uses a beyond-use approach, California permits delay until restore or next use, and the AP passage above expects records and erasure on restore. Note 19 reads the AP as stricter, using a phrase that does not appear in the extracted passage, so that reading is not adopted here (section 14).
### 12.8 ViDA: Directive (EU) 2025/516
[Council Directive (EU) 2025/516](https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=OJ:L_202500516) (OJ 2025-03-25) LEG-02. Article 7: it "shall enter into force on the twentieth day following that of its publication". National transposition status was not researched, and no statement is made about any Member State.

| Article | Effect from | Transposition deadline (Art. 6) |
|---|---|---|
| Art. 1 | Entry into force | Art. 1 points 2 and 3 may be applied from 14 April 2025 |
| Art. 2 | 1 January 2027 | 31 December 2026 |
| Art. 3 | 1 July 2028 (Art. 3 point 1: at earliest 1 July 2028, at latest 1 January 2030) | 30 June 2028 |
| Art. 4 | 1 July 2029 | 30 June 2029 |
| Art. 5 (e-invoicing and digital reporting) | 1 July 2030 | 30 June 2030 |

- Art. 6(5) derogation: Member States with a domestic digital real-time reporting obligation in place on 1 January 2024, or authorised before that date, apply specified measures relating to Articles 218, 271a and 271b "by 1 January 2035" for domestic e-invoicing and reporting.
- Art. 226 amendments found: point (7a) (Art. 2), point (4) (Art. 3), point (11a) and new points (16) and (17) (Art. 5). Art. 226(2) is not rewritten by any amendment seen.
- New point (16): "in the case of a corrective invoice as referred to in Article 219, the sequential number which identifies the corrected invoice, as referred to in point (2) of this paragraph". **MANDATORY (legal) from 1 July 2030 where transposed.** Scope: ERP, FIN; EU per national law.
- New point (17) adds supplier bank account numbers or other identifiers, which are themselves data to classify (INFERENCE).

## 13. Conflicts and their resolution
Legal aspects below are **issues to raise with counsel**, not conclusions.
### C1. Immutable audit logs versus erasure
**The tension.** PCI 10.3 and 10.5.1 require protected logs for a period; OWASP warns against early destruction (SEC-05); SP 800-53 AU-9 protects audit data; 21 CFR 11.10(e) requires non-obscuring trails. GDPR Art. 17 requires erasure when a ground applies. Ledgers and system-versioned history are built not to lose rows.

**Legal position (issues for counsel).**
- Art. 17(3) contains exceptions including legal obligations under **Union or Member State law** and legal claims (official wording in section 3.4). LEG-03, SEC-15, TEN-34.
- **SOX and PCI DSS do not obviously fit the first exception**: SOX is US law, and PCI DSS is an industry standard. Multinationals cannot assume that these retention rules displace erasure for EU data subjects. Whether legal claims or another basis applies is a fact-specific question.
- CCPA deletion is subject to the exceptions in 1798.105(d), including "(8) Comply with a legal obligation." (section 3.5, LEG-28). Whether a given retention duty fits is for counsel.
- SOX §1519 concerns intent to obstruct, not routine deletion.

**Engineering recommendations.**
- **Keep identifying values out of immutable logs from the start**, using stable pseudonymous references. RECOMMENDED (SEC-05; INFERENCE from SEC-16). Scope: ALL.
- **Keep the identifying map in a mutable, separately controlled store**, so it can be erased independently. RECOMMENDED (INFERENCE). A log using pseudonyms remains personal data while re-identification is possible. Removing the map moves toward anonymity but does not guarantee it, since quasi-identifiers may remain.
- **Record the retention basis per record class.** RECOMMENDED (INFERENCE from GDPR Art. 5(2), 30).
- **Use purge paths designed by the vendor** (Oracle retention, MariaDB DELETE HISTORY), under controlled privileges. OPTIONAL/CONTEXTUAL. Row-level redaction in ledger structures was not researched.
### C2. Soft delete versus erasure
**The tension.** A flag preserves identifiable data, while Art. 5(1)(e) and Art. 17 are about identifiable form.

**Legal position (issue for counsel).** **Not settled.** No regulator text read addresses soft deletion by name, including in the later regulator review (section 12.7). That a flag is insufficient is an inference, though a strong one.

**Engineering recommendations.** Treat soft deletion as a recoverability feature with a bounded window, followed by purge or anonymization. See SD-1 to SD-4. Note the distinction: a Recital 26-grade anonymization requires that the person is no longer identifiable, and overwriting a name alone may not achieve that.
### C3. Encryption versus searchability
**The tension.** Stronger confidentiality removes query capability.

**No legal requirement resolves this directly.** GDPR Art. 32 is risk-based and PCI 3.5.1 offers options.

| Required operator | Options in the notes | Cost |
|---|---|---|
| None; retrieve by key | Randomized or application-level encryption | No search on the value |
| Equality, joins, grouping | Deterministic encryption | Pattern leakage, especially low cardinality (SEC-23) |
| Equality on PAN | Index tokens or hash of the entire PAN (SEC-17) | Correlation controls with truncated forms. Hash guessability over a limited PAN space is a concern to raise with the assessor (INFERENCE) |
| Range or pattern | Enclaves (SEC-23); tablespace TDE retains range scans but does not address insiders (MSOM-13) | Added trust assumptions or a weaker threat model |
| Display only | Masking (SEC-25, MSOM-13) | Not a boundary |
| Analytics on sensitive attributes | Tokenized, de-identified or aggregated copies (SEC-09, SEC-10) | Re-identification risk needs assessment |

**Recommendation.** Per-column decision by required operator and threat model. OPTIONAL/CONTEXTUAL. Scope: ALL. Determine the needed operators before choosing encryption, as a design-time step.
### C4. TDE claims versus threat model
**The tension.** Vendor materials associate TDE with regulatory compliance. The Microsoft page, as paraphrased in the notes, suggests TDE helps follow laws and guidelines. Its own scope, however, is data and log files at rest against media theft. It does not cover channels, and nothing on the page claims protection against authorized or privileged users querying data. SEC-24. OWASP makes the layer dependent on the threat model. SEC-04.

**Normative position.**
- PCI 3.5.1.2 says disk-level or partition-level encryption alone needs a further mechanism for PAN. SEC-17.
- **PCI's text does not name TDE.** It contrasts disk and partition encryption with file-, column- or field-level database encryption. Where file-level TDE falls is **unresolved by the notes**, and it may differ by product: SQL Server TDE encrypts data and log files, Oracle offers tablespace and column forms. Ask the assessor.
- GDPR Art. 32 requires encryption only as appropriate to risk.
- HIPAA encryption is addressable today, and the NPRM would change that.

**Engineering recommendations.**
- **EN-1 applies:** do not claim compliance from TDE alone. RECOMMENDED.
- **TDE is OPTIONAL/CONTEXTUAL**, and is a reasonable baseline when media or backup theft is in scope. The notes label it both ways; the threat-dependent label is used here.
- For PAN, satisfy 3.5.1 directly. Field-level encryption is one option but not the only one. MANDATORY (standard).
- For high-impact PII with insiders in scope, add field-level protection. RECOMMENDED (INFERENCE).
### C5. RLS strength versus operational burden
Microsoft and PostgreSQL present RLS as a tenant-scoping mechanism, while the Azure Architecture Center notes many solutions avoid it. CLOUD-19, PGMY-07, CLOUD-18. Both require correct tenant scoping; they differ on where it is enforced. The argument that enforcement should not be left to developers comes from the **unverified** AWS whitepaper (CLOUD-04) and is not relied on. **Recommendation:** TN-1 and TN-2 are mandatory; engine enforcement is OPTIONAL/CONTEXTUAL, and favored where the cost of a cross-tenant leak is high (INFERENCE from SEC-35).
### C6. Key retention versus key destruction
OWASP advises retaining old keys to decrypt backups (SEC-04), and Microsoft warns that lost TDE certificates cause data loss (SEC-24). SP 800-88 says cryptographic erase should not be trusted where keys were backed up without high confidence (SEC-12). **Recommendation (INFERENCE):** separate key classes: recoverable keys for infrastructure encryption and destruction-capable keys for any data intended to be erased cryptographically.
### C7. Audit content versus log minimization
Before-and-after row capture (TEN-11) copies sensitive values, while OWASP excludes PII and cardholder data from logs (SEC-05). **Recommendation (INFERENCE):** exclude or tokenize sensitive columns in change capture where the audit purpose allows. The audit trigger's excluded-column option is an example. Regulated trails that must show prior values need their own classified, access-controlled store.

## 14. Where this document departs from the notes
| Topic | Notes | This document | Why |
|---|---|---|---|
| Art. 17(3)(b) | Treats SOX and PCI DSS retention as resolving erasure | Flagged as an open issue | The exception as recorded refers to Union or Member State law |
| Erasure duty | Erase everything else on request | Only where a ground applies and no exception does | Art. 17(1), 17(3) |
| PCI and TDE | Says PCI explicitly rejects TDE | Says PCI addresses disk and partition level | TDE is not named in the extracted text |
| PAN protection | Column or application layer mandatory | Any 3.5.1 listed approach | Text of 3.5.1 |
| Keyed hashes | One conflict entry says PCI permits keyed one-way hashes | Says one-way hashes of the entire PAN | The word keyed is not in the extracted 3.5.1 text |
| PCI status | Grouped with regulation | Separated as an industry standard | Nature of the instrument |
| TDE label | RECOMMENDED in one place, CONTEXTUAL in another | OPTIONAL/CONTEXTUAL | Follows threat-model reasoning |
| SOX retention | SOX 5 years as a general floor | Auditor workpapers only | §1520(a)(1) text |
| HIPAA retention | 6 years as a general floor | Required documentation only | §164.316(b)(2)(i) text |
| Part 11 | Mandatory for regulated or financial systems | FDA scope only; analogy for finance | Scope of Part 11 |
| Tenant enforcement | Mandatory at the data layer, partly on the AWS tenet | Correct scoping mandatory; engine enforcement contextual | AWS whitepaper unverified; Azure contrary observation |
| AWS on RLS | One takeaway attributes the RLS warning to AWS and Azure | Azure only | Only Azure's statement appears in the findings |
| Crypto-shredding | One note calls it the standard reconciliation | Unsettled inference | The notes' own gaps state no source covers it; note 19 confirms no regulator text accepts it as erasure |
| Dutch AP on backups | Note 19 says the AP requires erasure from backups "as soon as possible" and reads it as stricter than the ICO and California | Phrase not quoted; stricter reading not adopted | The phrase is absent from the AP passage extracted in note 19, which expects records and erasure on restore. Check on the live site |
| German commercial retention row | Note 19 has record and period columns shifted | Columns realigned; content unchanged | Table layout only |
| Key escrow | One inference says keys are never backed up | Governed, high-confidence control | SP 800-88 wording |
| One company per posting | Mandatory | Recommended modeling choice | NetSuite permits multi-subsidiary transactions |
| 27001 and column classification | Links classification to Annex A | Not supported | Annex A was not read beyond vendor summaries |
| Brandur | Described by past employers in the notes | Described by name only | Corrections file excludes one such description |

## 15. Evidence gaps and unverified sources
**Flagged or weak sources**
| Source | Status |
|---|---|
| CLOUD-04 AWS tenant isolation whitepapers | Note 22: no silo, pool or bridge text on the landing page it redirects to. Not used; stop citing |
| LEG-33 ICO right to erasure and encryption scenarios | **Wayback captures only (2026-10-29, 2026-03-05); live site refused access. Needs confirmation on the live site** |
| LEG-35 Dutch AP right to erasure | **Wayback capture only (2026-03-21); live site refused access. Needs confirmation on the live site** |
| LEG-34 EDPB 02/2025 on blockchain | Consultation version; different technology |
| LEG-06 UStAE 14.5 | Not opened (503); search snippets only |
| LEG-28 California statute | CPPA copy of January 2025; leginfo not opened |
| LEG-29 CCPA Regulations | File name suggests the statute; held the Regulations effective 1/1/2026 when read |
| LEG-09 BOFiP conservation | Displayed version in force to 2014-05-28; may have been replaced |
| LEG-11, LEG-12, LEG-31, LEG-36 | Read through a fetch tool; paraphrase only |
| TEN-38 WithPCI | Third party; superseded by SAQ D |
| TEN-16 InfoQ on QLDB | Secondary; AWS wording unverified |
| ISO/IEC 27001 Annex A details | Low-authority vendor summaries only |
| ISO/IEC 27040 | Known only through SP 800-88 |
| NIST Privacy Framework 1.1 status | Search snippets only |
| Oracle EXEMPT ACCESS POLICY | Search snippet; omitted |
| OWASP A05 injection statistics | Search snippet; omitted |
| PCI 51-of-64 future-dated figure | Search snippet; omitted |
| [Art. 17 GDPR](https://gdpr-info.eu/art-17-gdpr/) (n.d.) TEN-34 | Unofficial mirror; EUR-Lex text is now in section 3.4 (LEG-03) |
| EDPB 01/2025 | Consultation version |
| Oracle /23/ URLs | Note 22: served from /26/ and report Release 26; not cited as 23ai |

**Not supported by the notes, requiring further research or counsel**
1. **Not settled:** whether crypto-shredding or destruction of a pseudonym map satisfies Art. 17 or CCPA deletion. No regulator text found accepts it. CNIL, AEPD and Datatilsynet positions were not found.
2. **Not settled:** regulator treatment of soft deletion. No regulator text found addresses it by name.
3. Erasure from backups: regulator text obtained (section 12.7), but timing under "without undue delay" in the EU is open, and the ICO and Dutch AP text needs confirmation on the live sites.
4. California: statute read only from the CPPA copy of January 2025, with leginfo not opened and later change not checked. California-specific retention was not researched.
5. GDPR: whether Art. 17(3)(b) reaches retention rules from non-EU law. Art. 17(1) points (a) to (f) are paraphrased here; the Art. 9 mapping to a classification model is for counsel.
6. HIPAA final-rule status, and how HIPAA retention applies to system activity logs.
7. Retention and numbering gaps left by section 12.6: L123-22 and Art. 242 nonies A not opened on Legifrance; the German voucher transitional rule not read; Italian and Spanish retention not researched in depth; Saudi income tax and companies law, and UAE corporate tax retention, not researched. **The German invoice-gap rule (UStAE 14.5(10)) rests on search snippets.** ViDA national transposition was not researched.
8. PCI DSS v4.0.1 clause text and numbering (library page HTTP 504, v4.0.1 SAQ D HTTP 403), so requirement wording remains v4.0 SAQ D wording pending v4.0.1; how file-level TDE is assessed; PCI hardening requirements.
9. How SOX is applied to database controls in audit practice.
10. CIS Benchmark contents; ISO/IEC 27001 Annex A and ISO/IEC 27002.
11. ASVS V11 and V16 requirement text; SP 800-53 Release 5.2.0 changes.
12. Tokenization vault architecture.
13. Schema-per-tenant in any primary source; quantitative RLS performance.
14. MongoDB Queryable Encryption and field-level encryption limits beyond the security checklist; MongoDB auditing and role details.
15. Database mechanics for legal hold; redaction within SQL Server ledger structures.
16. SAP company-code documentation; IBM Db2 temporal documentation.
17. **Pakistan citation conflict:** e-invoicing start dates. SRO 709(I)/2025 of 22 April 2025 reportedly lists 1 May 2025 for corporates (search snippet), while FBR's FAQ says June 1st 2025 for corporate and July 1st 2025 for non-corporate registered persons. A later extension notice was not opened. Current dates are unresolved.
18. **UAE citation conflict:** the Ministry of Finance compilation footnote on Article 59 reads "Article amended as per Cabinet Decision No. 100 of 2024", while secondary commentary refers to No. 100 of 2025. The compilation read is an October 2024 upload (LEG-22), and later changes were not read.
19. Dutch AP reading on backup timing: see section 14. Confirm against the live page.
20. Weight of regulator guidance: ICO applies UK GDPR, and the EDPB blockchain text is a consultation version. All legal content in this document is research input, not legal advice, and needs review by counsel.
