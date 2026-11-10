# Stage 2 Rule Format

Stage 2 converts the research in `../research/` into standards. It contains no schemas, DDL templates or validator code.

## Rule fields

| Field | Meaning |
|---|---|
| id | `<PREFIX>-NNN`, stable and never reused |
| title | Short name |
| statement | One testable sentence using MUST, SHOULD or MAY |
| level | MANDATORY, RECOMMENDED or OPTIONAL |
| scope | Array of: OLTP, OLAP, data_warehouse, lakehouse, streaming, all |
| applies_when | Conditions, or "always" |
| rationale | What goes wrong otherwise, in one or two sentences |
| exceptions | Permitted exceptions and who approves them, or "none" |
| engine_notes | Engine-specific implementation differences, or "none" |
| evidence | Array of catalog IDs or research file sections |
| evidence_strength | standard, multi_vendor, single_vendor, case_study, inference |
| status | active, provisional, needs_decision, or superseded |
| decision_ref | Decision number from `DECISIONS_TO_APPROVE.md`, comma-separated if there are several, or null |
| superseded_by | Canonical rule ID. Present only when status is superseded, and the target must not itself be superseded |
| check_method | schema_lint, migration_lint, catalog_query, pipeline_test, runtime_monitor, manual_review |
| check_description | What a reviewer or future validator would check, in plain words |
| lifecycle_stage | One of: Data Modeling, Schema Design, Data Validation, Transactions, ETL/ELT, Data Quality, Governance, Reporting, Monitoring |

## Level rules

- MUST and MANDATORY require an authoritative source: a standard, regulation, engine-enforced behaviour, or agreement across independent vendors. Follow `../research/design_decision_matrix.md` classifications, and record any change.
- An organizational choice with no universal answer, such as naming style, may be MANDATORY within this framework only with status `needs_decision`, until the owner approves it.
- Inference-only rules cannot be MANDATORY and must be `provisional`.
- Statutes bind only in their jurisdiction. State it in applies_when.
- Legal rules are `provisional` and carry "requires legal review" in exceptions or rationale.
- Claims listed as unconfirmed in `research_gaps.md` must not support a rule. Text marked [WF] needs a re-check note in engine_notes.

## Owner decisions

Rules decided by the owner are organizational decisions. They may be active or MANDATORY within this framework, and evidence_strength stays unchanged: approval makes a choice binding but does not create evidence or a benchmark. Rules that need counsel, or where no value could be set because no source exists, stay provisional.

A superseded rule keeps its ID and text, and its requirement is carried by `superseded_by`.

**H1:** the "framework exception approver" is the one role for framework-level exceptions, replacing framework owner, schema owner and data architecture owner. Dataset, system and finance owner remain per-asset roles. No person has been named yet.

**H2:** method-scoped rules that bind only teams using a named method (RPT-003, RPT-004, RPT-006, RPT-015) stay MANDATORY on a single method owner's evidence, and are a recorded exception to the MUST rule above.

## Conflicts

Where sources disagree, propose one default, list alternatives, and set status `needs_decision`. Do not hide the disagreement. Where no independent benchmark exists, say the choice is a judgment.

## Technology independence

State rules in engine-neutral terms. Put engine differences in engine_notes. Never apply OLTP rules to analytical systems, or the reverse, without saying so.

## Output

Each group writes one Markdown file in `rules/` and one JSON array of rule objects in `registry/`, using the field names above. Coverage must be complete but not padded: one rule per distinct requirement. Each Markdown file ends with "Decisions needing owner approval": question, proposed default, alternatives, consequence of each.
