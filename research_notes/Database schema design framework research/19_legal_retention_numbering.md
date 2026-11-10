# 19. Legal requirements affecting ERP and SaaS data design

Research input only. This is not legal advice and not framework rules. Researched 2026-11-08.
Catalog: `catalog_19_legal_retention.json` (IDs LEG-01 onward).

## How to read these notes

- Text inside "quotation marks" was extracted directly with curl or pdftotext from the cited source.
- Text without quotation marks marked (WebFetch) is a paraphrase of a model summary of the page.
- Text marked (search snippet) came from a search result and the page itself could not be opened. Its catalog entry has `url_verified: false`.
- Labels: **MANDATORY**, **RECOMMENDED**, **OPTIONAL/CONTEXTUAL**, each with a workload scope. MANDATORY means the cited text imposes it on the stated regulated population. It does not mean every system is in scope.
- "Design note" lines are this researcher's inference from the law. They are not statements of law.
- Wayback Machine copies were used where the live regulator site refused automated access. The capture timestamp is given. Those copies may not reflect changes after capture.

## 1. Summary of findings

| Topic | Position | Status |
|---|---|---|
| EU invoice number | Must be sequential, based on one or more series, and uniquely identify the invoice (Art. 226(2)) | Settled text |
| Gaps in invoice numbers | The Directive does not address gaps. National positions differ. | **Not settled across jurisdictions** (section 2.8) |
| ViDA (Directive 2025/516) | In force. Phases run to 1 July 2030. Art. 226(2) is not rewritten by any Art. 226 amendment seen. | Settled text, national transposition pending |
| Retention periods | 5 to 10 years typical. Longer for real estate and capital assets. Extended by disputes or audits. | Settled per jurisdiction, but differs by record class and start date |
| GDPR erasure against statutory retention | Art. 17(3)(b) disapplies erasure where processing is necessary for a legal obligation | Settled text |
| Erasure from backups | Regulators expect it to be addressed, and accept delay in some cases. EDPB has flagged further guidance as a possible action. | **Not settled in the EU** |
| Key destruction as erasure | No regulator text found that accepts it as erasure | **Not settled** |
| Soft deletion | No regulator text found that addresses it by name | **Not settled** |

## 2. Invoice numbering

### 2.1 EU VAT Directive 2006/112/EC (LEG-01)

Consolidated text dated 14 April 2025, Article 226: "only the following details are required for VAT purposes on invoices issued pursuant to Articles 220 and 221", including at point (2) "a sequential number, based on one or more series, which uniquely identifies the invoice".

Article 233(1): "The authenticity of the origin, the integrity of the content and the legibility of an invoice, whether on paper or in electronic form, shall be ensured from the point in time of issue until the end of the period for storage of the invoice." It also says this "may be achieved by any business controls which create a reliable audit trail between an invoice and a supply of goods or services."

Article 244 requires storage of copies of invoices issued and all invoices received. Article 247(1): "Each Member State shall determine the period throughout which taxable persons must ensure the storage of invoices". So the Directive sets no retention period.

- **MANDATORY** (OLTP, invoicing; EU VAT-registered suppliers): a per-series sequential, unique invoice number.
- **MANDATORY** (OLTP and archive; same scope): integrity and legibility for the whole storage period.
- Gap: the text does not say whether "sequential" excludes gaps.
- Design note: "one or more series" suggests the series is a modelled attribute and uniqueness is scoped to the taxable person and series.

### 2.2 Directive (EU) 2025/516, ViDA (LEG-02)

Published in the OJ on 25.3.2025. Article 7: it "shall enter into force on the twentieth day following that of its publication". Article 6(1) refers to application from 14 April 2025. Phases from the text:

| Article | Effect from | Transposition deadline (Art. 6) |
|---|---|---|
| Art. 1 | Entry into force | Art. 1 points 2 and 3 may be applied from 14 April 2025 |
| Art. 2 | 1 January 2027 | 31 December 2026 |
| Art. 3 | 1 July 2028 (Art. 3 point 1: at earliest 1 July 2028, at latest 1 January 2030) | 30 June 2028 |
| Art. 4 | 1 July 2029 | 30 June 2029 |
| Art. 5 (e-invoicing and digital reporting) | 1 July 2030 | 30 June 2030 |

Article 6(5) derogation: Member States with a domestic digital real-time reporting obligation in place on 1 January 2024 (or authorised before that date) apply specified measures relating to Articles 218, 271a and 271b "by 1 January 2035" for domestic e-invoicing and reporting.

Article 226 amendments found: point (7a) (Art. 2), point (4) (Art. 3), point (11a) and new points (16) and (17) (Art. 5). New point (16): "in the case of a corrective invoice as referred to in Article 219, the sequential number which identifies the corrected invoice, as referred to in point (2) of this paragraph". New point (17) adds supplier bank account numbers or other identifiers.

- **MANDATORY from 1 July 2030 where transposed** (OLTP, invoicing; EU scope per national law): corrective invoices carry the corrected invoice's sequential number.
- Design note: a self-referencing link from corrective invoice to corrected invoice is the natural structure.
- Gap: current national transposition status was not researched. No statement is made about any Member State.

### 2.3 Germany (LEG-04, LEG-06)

UStG section 14(4) point 4: "eine fortlaufende Nummer mit einer oder mehreren Zahlenreihen, die zur Identifizierung der Rechnung vom Rechnungsaussteller einmalig vergeben wird (Rechnungsnummer)".

Gaps: UStAE section 14.5(10). The BMF handbook pages could not be opened (HTTP 503 at the time of research, also for the mirror host). A search over BMF domains reported (search snippet) that the handbook versions 2019-2020, 2022 and 2023 say a gap-free sequence of issued invoice numbers is not mandatory, that the number must be issued once only, and that multiple number ranges are permitted.

Vendor commentary conflicts on this point and should not be used. The 2026 UStAE wording was not checked.

- **MANDATORY** (OLTP, invoicing; German scope): number issued once only, one or more number series.
- **Gaps: probably tolerated, but only secondary confirmation here.** Reopen UStAE 14.5(10) before relying on it.

### 2.4 France (LEG-07, LEG-08)

BOFiP BOI-TVA-DECLA-30-20-20-10 (version identifier 20121231) says the invoice must carry "un numéro unique basé sur une séquence chronologique et continue". For separate series, BOFiP requires:

- "que la numérotation soit effectuée chronologiquement au fur et à mesure de l'émission des factures"
- "qu'elle soit continue"
- and that the system guarantees "que deux factures émises la même année ne puissent pas porter le même numéro".

Series may be used where the conditions of activity justify them. BOFiP lists as examples several billing sites, customer categories with different rules, and several issuing methods, and advises a separate prefix for each series.

Service-Public (official French government information site): "Each invoice must include a unique number based on a continuous chronological sequence , without rupture. Therefore, two invoices cannot have the same number."

- **MANDATORY** (OLTP, invoicing; French scope): chronological, continuous numbering per series, no duplicates.
- **Gaps: the strictest wording found.** No official French text was found that tolerates a gap, or that says how to treat a spoiled number. A dedicated search of BOFiP did not surface one.
- Legal-text status: Article 242 nonies A annexe II CGI on Legifrance could not be opened. A search result reports (search snippet) it was amended by Decree 2024-1195.

### 2.5 Italy (LEG-10)

Risoluzione 1/E of 10 January 2013, quoting Art. 21(2)(b) DPR 633/1972: the invoice must contain a "numero progressivo che la identifichi in modo univoco". The Agency states: "è compatibile con l'identificazione univoca prevista dalla formulazione attuale della norma qualsiasi tipologia di numerazione progressiva che garantisca l'identificazione univoca della fattura, se del caso, anche mediante riferimento alla data della fattura stessa."

The resolution permits a sequence that runs across all years, or one continuing from the last 2012 number. It records that the European Commission objected to requiring a new sequence each year.

- **MANDATORY** (OLTP, invoicing; Italian scope): progressive number with unique identification. Date may contribute to uniqueness.
- **Gaps: not addressed by the text read.** Not settled from this source.

### 2.6 Spain (LEG-11, LEG-12)

Real Decreto 1619/2012 (BOE consolidated text, last update 31 March 2026, WebFetch). Article 6.1.a: every invoice carries a number and where applicable a series, and numbering is sequential within each series. Separate series are allowed where justified, for example several establishments or different kinds of operation. Separate series are required for invoices issued by the customer or a third party, for corrective invoices, and for certain other cases. Article 19 ties retention to the period under Ley 58/2003.

AEAT VERI*FACTU FAQ on traceability (updated 21 October 2026, WebFetch): the billing records must have no gaps or jumps in their generation sequence, by chaining each record to the one before. This concerns the chain of billing records, and the page says a change of invoice numbering at year end does not affect traceability.

AEAT invoice numbering recommendations (WebFetch) cover format only and do not address gaps.

- **MANDATORY** (OLTP, invoicing; Spanish scope): sequential numbering within a series; separate series for corrective invoices.
- **MANDATORY** (billing software in scope of RD 1007/2023): chained billing records. Scope and start dates were not researched.
- **Invoice number gaps: not addressed by the sources read.** The chain requirement is about records, so it should not be read as a rule about invoice number gaps.

### 2.7 United Kingdom (LEG-13, LEG-14)

VAT Notice 700/21: "a sequential number based on one or more series which uniquely identifies the document". HMRC VATREC5010 notes the same wording in regulation 14(1)(a) and gives direct guidance:

- Question on starting at a higher number: "Yes, as long as the invoice series runs consecutively from that point."
- "Yes, it is acceptable to operate more than one sequence at the same time."
- Question on a service centre issuing from one series across group companies: "Yes, this satisfies the requirement for invoices to be issued sequentially from one or more series."
- Question on a break "where I cancel an invoice or it is spoiled and never issued to a customer": "As long as you retain the cancelled or spoiled invoice in your accounting records, or you can provide an explanation for the break in sequence, this is acceptable."

- **MANDATORY** (OLTP, invoicing; UK VAT scope): sequential number, one or more series, unique.
- **Gaps: tolerated by HMRC guidance if explained or the spoiled invoice is retained.** This is the clearest gap statement found.
- Caveat: VATREC is an internal manual, so it records HMRC's view, not legislation.

### 2.8 Gap positions compared

| Jurisdiction | Requirement | Gaps | Evidence quality |
|---|---|---|---|
| EU Directive | Sequential, unique, one or more series | Silent | Direct text |
| Germany | Number issued once, one or more series | Reported not mandatory | Search snippet of BMF pages only |
| France | Chronological and continuous, "without rupture" | No tolerance found | Direct text |
| Italy | Progressive, unique | Not addressed | Direct text |
| Spain | Sequential within series | Not addressed | WebFetch of BOE |
| UK | Sequential, unique, one or more series | Tolerated with explanation or retained copy | Direct HMRC text |
| Pakistan | Serially numbered; FBR number on e-invoices | Not found | Direct text |
| UAE | Sequential, or unique number showing order | Not found | Direct text |
| Saudi Arabia | Sequential, unique; ICV never reused | Rejected documents consume ICV | Direct text |

**Conflict:** a single gap-free rule cannot be derived from these sources. France is the strictest wording and the UK is the clearest tolerance. Design note: a system built for several jurisdictions would need to meet the strictest applicable rule per legal entity and keep an explanation record for any number not used. A plain database sequence can skip values on rollback. See the transaction research notes for that mechanism.

### 2.9 Pakistan (LEG-18, LEG-19)

Sales Tax Act 1990 (FBR consolidation to 2025-26), section 23(1): "A registered person making a taxable supply shall issue a serially numbered tax invoice at the time of supply of goods".

Sales Tax Rules 2006, Chapter XIV (rules 150Q onward) on electronic invoicing:

- Particulars include "unique FBR invoice number (XXXXXX-DDMMYYHHMMSS-0001)" and a unique QR code.
- Integrated systems must "receive the unique FBR invoice number", "encrypt and preserve the reported sales tax invoice data in an irrevocable and secure manner", and "every adjustment, modification or cancellation must be recorded".
- Rule 150S(1): "The integrated person shall issue a real-time verifiable electronic sales tax invoice for every taxable supply and service. The invoice so issued shall be retained as record for a period of six years on electronic media as provided under section 24 of the Act."

Rule 150S(2) applies the same retention to debit and credit notes.

- **MANDATORY** (OLTP, invoicing; Pakistani registered persons): serially numbered tax invoices.
- **MANDATORY** (integrated persons notified by FBR): store the FBR-assigned invoice number and QR data alongside the local number; log adjustments and cancellations.
- Design note: the local serial and the authority-assigned number are separate attributes.

**Conflict on start dates:** SRO 709(I)/2025 of 22 April 2025 reportedly lists 1 May 2025 for corporates (search snippet). FBR's FAQ, which was opened, says June 1st 2025 for corporate and July 1st 2025 for non-corporate registered persons. A later FBR extension notice was surfaced but not opened. Current mandatory dates are unresolved here.

Gap: no FBR text on gaps in the serial was found.

### 2.10 United Arab Emirates (LEG-22, LEG-24)

VAT Executive Regulation (Cabinet Decision 52 of 2017, MoF compilation), Article 59(1)(d): "A sequential Tax Invoice number or a unique number which enables identification of the Tax Invoice and the order of the Tax Invoice in any sequence of invoices."

UAE Electronic Invoicing Guidelines V2.0 (26 October 2026): a UUID is "generated in addition to the Electronic Invoice sequential number".

- **MANDATORY** (OLTP, invoicing; UAE VAT registrants): sequential or unique number that also shows order in the sequence.
- **MANDATORY where the e-invoicing system applies**: UUID in addition to the sequential number.
- Design note: a random identifier alone does not show order, so it would not meet Article 59(1)(d) by itself.

**Conflict on the amendment citation:** the MoF compilation footnote on Article 59 reads "Article amended as per Cabinet Decision No. 100 of 2024", while secondary commentary refers to Cabinet Decision No. 100 of 2025. The compilation read is an October 2024 upload and may not include later changes. Gap: no gap tolerance text found.

### 2.11 Saudi Arabia, ZATCA (LEG-25 to LEG-27)

ZATCA Guideline for Tax Invoicing and Records: "The tax invoice must include a sequential number that distinguishes it from other invoices", citing Article 53(5)(b) of the Implementing Regulations, and the number "must comply with the conditions stipulated in the Electronic Invoicing Regulations". Invoice numbers may mix numerals and letters "provided that the number is sequential and uniquely identifies the invoice".

E-invoicing Detailed Technical Guidelines v2 (November 2022, FAQ section):

- "Invoice counter value should not be re-used. Once a document is generated with an Invoice Counter Value (ICV), then that ICV cannot be mentioned on another document."
- "every document shall have its own hash and counter value. Rejected document's hash and counter value should not be changed or updated."
- ZATCA's platform tracks rejected document hashes, and the next document's Previous Invoice Hash links to the rejected document. In the guideline's example: "Document 3 should have its Previous Invoice Hash as the hash of Document 2 even though it was rejected."

XML Implementation Standard v1.2: "Each invoice must have an invoice counter value (KSA-16)" and "the previous invoice hash (KSA-13), this hash must be base64 encoded SHA256".

- **MANDATORY** (OLTP, invoicing; KSA e-invoicing scope): monotonic counter that is never reused, plus a previous-invoice hash chain that includes rejected documents.
- Design note: ICV and invoice number are distinct fields. A rejected attempt consumes a counter value, so the counter behaves as an append-only event series.
- Caveat: the technical guideline read is dated November 2022, and the XML standard is v1.2 (2023). Later versions may exist.

## 3. Retention periods

All entries are **MANDATORY** for the stated records and population, unless noted. Scope is mainly OLTP and archive. Warehouse copies may hold the same records, but the legal retention duty attaches to the records rather than to any one store.

| Jurisdiction | Record | Period | Starts | Source |
|---|---|---|---|---|
| Germany (tax) | Books, records, annual accounts | 10 years | End of calendar year of last entry or creation | AO 147(3),(4) (LEG-05) |
| Germany (tax) | Booking vouchers | 8 years | As above | AO 147(3),(4) |
| Germany (tax) | Other listed documents | 6 years | As above | AO 147(3),(4) |
| Germany (VAT) | Invoice copies issued and invoices received | 8 years | End of calendar year of invoice issue | UStG 14b(1) |
| Germany (commercial) | Books 10; booking vouchers 8; others 6 | Institutions under KWG and listed categories: booking vouchers 10 | End of calendar year | HGB 257(4),(5) |
| France (tax) | Books, records, documents | 6 years | Date of last transaction or document | LPF L102 B via BOFiP (LEG-09) |
| France (commercial) | Accounting documents | 10 years | See source | Code de commerce L123-22 (search snippet; CNIL also cites 10 years for billing data) |
| UK (VAT) | Business records for VAT | At least 6 years | See source | Notice 700/21 (LEG-13) |
| UK (Companies Act) | Accounting records | Private 3 years; public 6 years | "from the date on which they are made" | CA 2006 s388(4) (LEG-15) |
| US (IRS, income tax) | Records supporting return | 3 years generally; 3 from filing or 2 from payment if refund claim, whichever is later; 7 for worthless securities or bad debt; 6 if income under-reported by more than 25%; indefinitely if no return or fraudulent return | Generally after return filed | IRS page (LEG-16) |
| US (IRS, employment) | Employment tax records | At least 4 years | After tax due or paid, whichever is later | IRS page |
| US (broker-dealers only) | 17a-3(a)(1)-(3),(5),(21),(22) records | 6 years, first 2 easily accessible | See rule | 17 CFR 240.17a-4(a) (LEG-17) |
| US (broker-dealers only) | Listed 17a-3 records | 3 years, first 2 easily accessible | See rule | 17a-4(b) |
| US (broker-dealers only) | Account opening and terms records | 6 years | After account closing | 17a-4(c) |
| Pakistan (sales tax) | Records and documents | 6 years, or until proceedings are finally decided | After end of tax period | STA s24 (LEG-18) |
| Pakistan (income tax) | Prescribed accounts and documents | 6 years, or until proceedings end | After end of tax year | ITO s174(3) (LEG-20) |
| Pakistan (companies) | Books of account with vouchers | "not less than ten financial years immediately preceding a financial year" | See text | Companies Act 2017 s220(5) (LEG-21) |
| UAE (tax) | Accounting records, books, information | Taxable persons 5 years; others 5 years | After tax period; others from end of calendar year of creation | Cabinet Decision 74/2023 Art 3 (LEG-23) |
| UAE (tax) | Real estate records | 7 years | End of calendar year of creation | Art 3(1)(c) |
| UAE (tax) | Extensions | 4 more years for disputes (or until settled, whichever later), audits, or audit notice; 1 year for voluntary disclosure in fifth year | | Art 3(2) |
| Saudi Arabia (VAT) | All records | At least 6 years | End of related tax period | ZATCA guide 8.3.3 (LEG-25) |
| Saudi Arabia (VAT) | Movable capital assets | Adjustment period plus 5 years | Date of acquisition | ZATCA guide |
| Saudi Arabia (VAT) | Real estate | At least 15 years | | ZATCA guide |

Further points:

- Germany: AO 147(3): the period "läuft jedoch nicht ab, soweit und solange die Unterlagen für Steuern von Bedeutung sind, für welche die Festsetzungsfrist noch nicht abgelaufen ist". So a fixed schedule alone is not enough. A legal hold or tax-assessment check is needed before disposal.
- Germany: section 147 contains a rule that after a system change or migration out of the production system, data may, once the fifth following calendar year has ended, be held only on a machine-readable data carrier. Design note: this affects archive design for ERP migrations.
- UK: Notice 700/21 says HMRC may allow a shorter period for some records on request, and other taxes may need longer.
- Pakistan: ITO s174(3) final proviso says the limit "shall not apply to the records pertaining to income, assets, expenses or transactions to which clause (ii) of sub-section (2) of section 111 applies."
- Pakistan: Companies Act section 151 (resolution records) has a 20-year physical and permanent electronic rule and another provision has a 10-year physical and permanent electronic rule. These were read in text without confirming each section number, so check before use.
- UAE e-invoicing: Guidelines V2.0 section 5.4 apply the same periods to data on issue, transmission and receipt of e-invoices, and describe compliance with Article 11 of MD 243/2025 as retention "in an electronic system that preserves their integrity".
- Saudi Arabia: Records "must be retained within the Kingdom", with a workstation exception for permanent establishments with centralised systems abroad. This is a data-location constraint. Language: "records must be retained in the Arabic language". **MANDATORY** for KSA VAT scope.

**Conflicts:**

- France: tax rule 6 years and commercial rule 10 years. BOFiP (per search snippet) says tax provisions are independent of L123-22. The longer period would apply where both apply.
- Germany: 8 years for vouchers replaced the former 10 years. A search snippet reports this applies only to vouchers whose period had not ended before 1 January 2025. The transitional provision itself was not read.
- US IRS periods are limitation-driven and are not a flat retention rule.
- 17a-4 applies only to broker-dealers. Its period and format rules should not be applied to general SaaS.

Electronic storage rule: 17a-4(f)(2)(i): a system must either "(A) Preserve a record for the duration of its applicable retention period in a manner that maintains a complete time-stamped audit trail" of modifications and deletions, or "(B) Preserve the records exclusively in a non-rewriteable, non-erasable format". **MANDATORY** only for broker-dealers using an electronic recordkeeping system.

## 4. Official wording on privacy and card data

### 4.1 GDPR (LEG-03, EUR-Lex)

Article 9(1): "Processing of personal data revealing racial or ethnic origin, political opinions, religious or philosophical beliefs, or trade union membership, and the processing of genetic data, biometric data for the purpose of uniquely identifying a natural person, data concerning health or data concerning a natural person's sex life or sexual orientation shall be prohibited." Article 9(2) sets exceptions, starting with explicit consent at point (a), with point (b) on employment and social security law.

Article 17(1): "The data subject shall have the right to obtain from the controller the erasure of personal data concerning him or her without undue delay and the controller shall have the obligation to erase personal data without undue delay where one of the following grounds applies:" The grounds at (a) to (f) are: no longer necessary; consent withdrawn with no other legal ground; objection under Art. 21; unlawful processing; erasure needed for a legal obligation; and data collected for information society services offered under Art. 8(1).

Article 17(3): "Paragraphs 1 and 2 shall not apply to the extent that processing is necessary:" including "(b) for compliance with a legal obligation which requires processing by Union or Member State law to which the controller is subject or for the performance of a task carried out in the public interest or in the exercise of official authority vested in the controller;" and "(e) for the establishment, exercise or defence of legal claims."

Article 30(5): "The obligations referred to in paragraphs 1 and 2 shall not apply to an enterprise or an organisation employing fewer than 250 persons unless the processing it carries out is likely to result in a risk to the rights and freedoms of data subjects, the processing is not occasional, or the processing includes special categories of data as referred to in Article 9(1) or personal data relating to criminal convictions and offences referred to in Article 10."

- **MANDATORY** (all workloads holding personal data; GDPR scope): erasure capability across stores, subject to exceptions.
- Design note: "to the extent that" points to field-level or record-level treatment. An invoice's retained fields can stay under 17(3)(b) while other profile data is erased. Exactly which fields is a legal judgment.
- Limit on 17(3)(b): it refers to Union or Member State law. A retention rule from a non-EU law is not clearly covered by it. Not settled here.
- Design note on Art. 30(5): the exemption is narrow. Processing that is not occasional, which regular SaaS processing would be, falls outside it.

### 4.2 California (LEG-28, LEG-29)

Civil Code 1798.105 was read from the CPPA-hosted copy of the statute (effective 01/01/2025 update). The leginfo page itself could not be opened: direct access failed and the Wayback copy held only navigation.

- (c)(1): the business "shall delete the consumer's personal information from its records, notify any service providers or contractors to delete the consumer's personal information from their records, and notify all third parties to whom the business has sold or shared the personal information to delete the consumer's personal information unless this proves impossible or involves disproportionate effort."
- (c)(2): "The business may maintain a confidential record of deletion requests solely for the purpose of preventing the personal information of a consumer who has submitted a deletion request from being sold, for compliance with laws or for other purposes, solely to the extent permissible under this title."
- (d): exceptions include completing the transaction, security and integrity, debugging, internal uses aligned with expectations, and "(8) Comply with a legal obligation."

The statute section does not mention backups. CCPA Regulations section 7022 (CPPA text effective 1/1/2026) does: "If a business, service provider, or contractor stores any personal information on archived or backup systems, it may delay compliance with the consumer's request to delete, with respect to data stored on the archived or backup system, until the archived or backup system relating to that data is restored to an active system or is next accessed or used for a sale, disclosure, or commercial purpose."

- **MANDATORY** (CCPA scope): deletion down the service provider chain, and re-application of deletion on restore or next use.
- Oddity: the file at the URL named `ccpa_statute_eff_20260101.pdf` contained the Regulations effective 1/1/2026 when read. The 1 January 2025 file was used for the statute. Any statutory change after that was not checked.

### 4.3 PCI DSS (LEG-30, LEG-31)

**Access limitation.** The full PCI DSS v4.0.1 standard is distributed through the PCI SSC document library. The library page timed out (HTTP 504) and the v4.0.1 SAQ D PDF refused access (HTTP 403) during this research. The wording below is from the public **SAQ D for Merchants for v4.0 (April 2022)**, not v4.0.1. Requirement text may differ in v4.0.1 and must be checked against the v4.0.1 document.

- 3.2.1: "Account data storage is kept to a minimum through implementation of data retention and disposal policies, procedures, and processes".
- 3.3.1: "SAD is not retained after authorization, even if encrypted. All sensitive authentication data received is rendered unrecoverable upon completion of the authorization process."
- 10.5.1: "Retain audit log history for at least 12 months, with at least the most recent three months immediately available for analysis."

PCI SSC FAQ 1280 (WebFetch): card verification codes may not be stored after authorization, even encrypted, and customer permission does not change this. Issuers and companies supporting issuing with a legitimate need are the exception.

- **MANDATORY** (entities in PCI DSS scope; OLTP, logs): no SAD after authorization; audit log retention at the stated level.
- Design note: log and backup paths are in scope as much as tables. A column that stores CVV is not compliant even if encrypted.

## 5. Regulator guidance on erasure mechanics

### 5.1 Backups

**EDPB CEF report on the right to erasure, adopted 10 February 2026 (LEG-32).** Key text:

- "It is therefore important to protect the integrity of the back-up. Depending on the technical settings and risks, it might not always be advisable to modify or delete information from back-ups. But, in that case, organisations should have appropriate procedures to keep track of erasure requests and comply with them on restored systems, as much as possible, in case of a data breach affecting the integrity of the organisation's system."
- Possible EDPB action: "Providing more guidance and recommendations to explain how controllers should practically deal with erasure in back-ups and what is meant by "without undue delay" in this context."
- Recommendations for controllers: "Follow established standards to erase and destroy data in a secure and structured manner." and "Verify that erasure has been carried out and be able to demonstrate such erasure."
- Practices noted: replacing personal data with strings of random characters, and tools that move data out of employee reach for later deletion. One SA found incremental deletion over long periods made it hard to conclude deletion happened without undue delay.

**ICO (LEG-33, Wayback capture 2026-10-29).** "If a valid erasure request is received and no exemption applies then you will have to take steps to ensure erasure from backup systems as well as live systems." "The key issue is to put the backup data 'beyond use', even if it cannot be immediately overwritten." The ICO adds "You must be absolutely clear with individuals as to what will happen to their data when their erasure request is fulfilled, including in respect of backup systems."

**Dutch AP (LEG-35, Wayback capture 2026-03-21).** "Backups also fall under the right to erasure." "Do you have backups that cannot or cannot easily be overwritten, such as tapes? Then you cannot erase the personal data from the backups. Make sure that you keep proper records of which personal data you should have erased. Is restoring a backup necessary? Then you will have to erase these data when you do this."

**California:** delay until restored or next used (section 4.2).

- **RECOMMENDED** (all workloads with backups; EU and UK): keep a durable record of erasure requests outside the backups and re-apply erasure after any restore. This is the common element in EDPB, AP and California text, and the ICO is consistent with it.
- **RECOMMENDED** (backup policy): defined backup retention, so that expiry of data is predictable. ICO links this to the retention schedule. EDPB shows retention alone is not always seen as adequate.
- **Not settled:** how long is "without undue delay" for backups in the EU. EDPB itself lists this as an issue for possible guidance.

**Conflict:** the AP says erase from backups "as soon as possible", which reads stricter than the ICO's beyond-use approach or California's delay. These bodies apply different legal regimes or national readings.

### 5.2 Encryption key destruction (crypto-shredding)

**EDPB Guidelines 02/2025 on blockchain, version for public consultation, adopted 8 April 2025 (LEG-34).** "upon deletion of this decryption key, the encrypted data will be unintelligible, at least until the algorithm is broken, the decryption techniques advance sufficiently to allow the decryption of the cipher text, or if the key had already been compromised or leaked. The EDPB recalls that encrypted personal data is still personal data and encryption does not remove the need for GDPR compliance."

**ICO, encryption scenarios (recorded in the notes field of LEG-33; Wayback capture 2026-03-05).** "If you encrypt your backups, you should have good key management in place" and "You must consider the right to erasure under Article 17 of the UK GDPR, and how this may apply, when determining both your use of encryption and the retention period of your backups."

- **Not settled.** No regulator text found says that destroying a key counts as erasure under Art. 17. The EDPB's blockchain passage describes the effect and warns of limits. It is a draft-stage document on a different technology.
- **OPTIONAL/CONTEXTUAL** (backups, event logs, immutable stores): per-subject key designs may reduce exposure but should not be presented as settled legal erasure.
- Gaps: CNIL, AEPD and Datatilsynet positions on this point were searched for and not found. The search result pointing to an AEPD note on blockchain was not read. NIST SP 800-88 was not reviewed for this file.

### 5.3 Soft deletion

- No regulator text found addresses soft deletion or a "deleted" flag by name.
- Indirect sources: the CNIL retention page (LEG-36, WebFetch) says intermediate archives must be separated from the active base either physically or logically by restricted access. That is about retention, not about honouring erasure. The ICO's beyond-use concept is stated in relation to backups, and it does not extend to live tables in the text read. The EDPB CEF report also records a concern about weak anonymisation substituting for deletion (reported by secondary sources; not independently confirmed in the report).
- **Not settled.** Design note: a flag leaves the personal data present and processable. On the text of Art. 17 alone it is hard to see this as erasure. Treat it as a workflow step before real erasure or anonymisation.

## 6. Design implications (inference, not law)

| Implication | Basis | Label | Scope |
|---|---|---|---|
| Model numbering series per legal entity and document type | EU, UK, France, Spain, Germany | MANDATORY in effect where those rules apply | OLTP, invoicing |
| Record every unused or cancelled invoice number with a reason | UK guidance; French continuity rule; ZATCA counter rule | RECOMMENDED | OLTP, invoicing |
| Avoid relying on a plain DB sequence for legal numbers | Gapless wording in France; sequence skip behaviour | RECOMMENDED | OLTP, invoicing |
| Separate attributes for local number, authority number, UUID, counter, previous hash | Pakistan, UAE, KSA | MANDATORY where the regime applies | OLTP, invoicing |
| Link corrective invoices to the originals | ViDA Art. 226(16), Spain series rule | MANDATORY from 2030 in EU, per law | OLTP, invoicing |
| Retention by record class, jurisdiction and start event, with hold override | All of section 3 | RECOMMENDED | OLTP, archive, warehouse |
| Keep an erasure ledger outside backups, re-run on restore | EDPB, AP, California | RECOMMENDED | general, backup |
| Field-level split of retained financial data and erasable profile data | Art. 17(3)(b) | RECOMMENDED | OLTP, data_warehouse, data_lake |
| Propagate deletion to processors, copies and replicas | CCPA 1798.105(c) | MANDATORY in CCPA scope | general, streaming |

## 7. Unresolved gaps

1. UStAE 14.5(10): BMF site returned 503. The no-gap reading rests on a search snippet of BMF pages. GoBD BMF letter was not retrieved.
2. France: no official text on how to handle a spoiled or cancelled number. Article 242 nonies A and L123-22 were not opened on Legifrance. The BOFiP conservation version read is marked as in force until 28/05/2014 and may have been replaced.
3. Italy and Spain: no direct official statement on gaps was found. Italian and Spanish retention periods were not researched in depth (not in the brief's required list).
4. ViDA: national transposition status not researched.
5. Pakistan: gap treatment in the serial not found. E-invoicing start dates conflict. Extension notice not opened.
6. UAE: Article 59 amendment citation conflict (2024 against 2025). Latest post-2024 compilation not read. Gap treatment not found. UAE corporate tax retention not researched.
7. Saudi Arabia: income tax and companies law retention not researched. ZATCA technical documents may have later versions.
8. PCI DSS v4.0.1: text not accessible. Requirement wording here is from v4.0 SAQ D.
9. California: leginfo not opened. Statute read from the CPPA copy of January 2025.
10. Key destruction and soft deletion: no regulator position found. CNIL, AEPD and Datatilsynet not found on key destruction.
11. ICO and AP are cited from Wayback captures because the live sites refused automated access.
