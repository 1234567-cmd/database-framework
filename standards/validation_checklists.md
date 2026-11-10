# Validation Checklists by Lifecycle Stage

Generated from `rule_registry.json`. Do not edit by hand. Use each checklist at the matching stage of a project.

- **MANDATORY** items must pass, or have an approved exception.
- **Provisional** items rest on incomplete evidence or need legal review.

## Data Modeling (46 checks)

| Done | Rule | Level | Status | Scope | Check | Method |
|---|---|---|---|---|---|---|
| [ ] | ARC-001 | RECOMMENDED | active | all | The design record names the store type and addresses each of the five assessment factors. | manual_review |
| [ ] | ARC-002 | RECOMMENDED | active | OLTP, OLAP | The architecture record shows where analytical queries run and, if they share or replicate the system of record, which permitted exception applies. | manual_review |
| [ ] | AUD-016 | RECOMMENDED | provisional | OLTP | Financial change history shows prior values. | manual_review |
| [ ] | AUD-017 | RECOMMENDED | active | all | Each history object's design record names its time dimension. | manual_review |
| [ ] | AUD-024 | RECOMMENDED | active | OLTP | The design records the rule, and tests cover a backdated correction. | manual_review |
| [ ] | ERD-001 | RECOMMENDED | active | all | Every relationship in the model shows cardinality and optionality. | manual_review |
| [ ] | ERD-008 | RECOMMENDED | provisional | all | Amended code lists are held in reference tables with validity dates. | manual_review |
| [ ] | FIN-019 | RECOMMENDED | active | OLTP | Check the chart of accounts distinguishes the two. | manual_review |
| [ ] | FIN-042 | RECOMMENDED | active | OLTP, OLAP | Confirm the model distinguishes the three concepts. | manual_review |
| [ ] | IDX-024 | RECOMMENDED | active | data_warehouse, lakehouse | Each analytical model records its key type and, if not the default, the reason. | manual_review |
| [ ] | MOD-001 | RECOMMENDED | active | all | Design records exist for each level and the physical model traces back to the logical one. | manual_review |
| [ ] | MOD-002 | RECOMMENDED | active | OLTP | The design states the paradigm and shows entities or a list of access patterns accordingly. | manual_review |
| [ ] | MOD-003 | RECOMMENDED | active | OLTP, data_warehouse | Each departure between logical and physical models has a recorded reason and a stated dependency. | manual_review |
| [ ] | NAM-003 | RECOMMENDED | active | OLTP | Sample table and column names and confirm each business term appears in the context glossary. | manual_review |
| [ ] | NAM-013 | RECOMMENDED | active | all | Check table names for grammatical number using a configurable inflection rule. | schema_lint |
| [ ] | NRM-002 | RECOMMENDED | active | OLTP | Reviewers confirm that no non-key field depends on part of a key or on another non-key field, or that a recorded deviation exists. | manual_review |
| [ ] | NRM-003 | RECOMMENDED | active | OLTP | Tables with several multivalued facts have a recorded 4NF and 5NF review. | manual_review |
| [ ] | SCL-001 | RECOMMENDED | provisional | OLTP | A sharding proposal records the simpler options tried and why they fell short. | manual_review |
| [ ] | SCL-002 | RECOMMENDED | active | OLTP | The shard key is shown against the top transactions, cardinality and value distribution. | manual_review |
| [ ] | SCL-003 | RECOMMENDED | active | OLTP | Models expected to distribute carry a chosen candidate key. | manual_review |
| [ ] | SCL-004 | RECOMMENDED | provisional | OLTP | The sharding design records the logical to physical mapping. | manual_review |
| [ ] | SCL-009 | RECOMMENDED | active | OLTP | Read-your-writes paths name the endpoint or guarantee used. | manual_review |
| [ ] | SCL-015 | RECOMMENDED | provisional | OLTP | A replacement proposal records why the incumbent cannot meet the need. | manual_review |
| [ ] | SCL-019 | RECOMMENDED | provisional | OLTP | Cross-domain joins and transactions are detected and cleared before the move. | manual_review |
| [ ] | TEN-018 | RECOMMENDED | provisional | OLTP | Company-scoped tables carry the company identifier as well as the tenant identifier where the tenant scope applies. | schema_lint |
| [ ] | TXN-023 | RECOMMENDED | active | OLTP | Design documents state the trade-off in both conditions. | manual_review |
| [ ] | TXN-024 | RECOMMENDED | provisional | OLTP | Processes that depend on order name an ordering column that is not a timestamp. | manual_review |
| [ ] | TYP-014 | RECOMMENDED | provisional | OLTP | Review requirements for local-time semantics and confirm a separate column exists where they apply. | manual_review |
| [ ] | ARC-007 | OPTIONAL | active | OLTP | Where a server split exists, the record states which of the three reasons applies. | manual_review |
| [ ] | AUD-018 | OPTIONAL | active | all | The design records which dimensions are used and why. | manual_review |
| [ ] | ERD-002 | OPTIONAL | provisional | all | Each diagram uses a single named notation. | manual_review |
| [ ] | ERD-009 | OPTIONAL | active | OLTP | Models claiming IDEF1X conformance have required discriminators on complete clusters. | manual_review |
| [ ] | FIN-007 | OPTIONAL | active | OLTP, data_warehouse | Confirm the decision to use or not use adjustment periods is recorded. | manual_review |
| [ ] | FIN-010 | OPTIONAL | active | OLTP | Confirm whether fiscal-year status exists and how it affects reversal. | manual_review |
| [ ] | FIN-011 | OPTIONAL | active | OLTP | Confirm how year-end profit or loss transfer is represented. | manual_review |
| [ ] | FIN-024 | OPTIONAL | provisional | OLTP | Confirm the owner has recorded a decision and any method is documented. | manual_review |
| [ ] | NRM-008 | OPTIONAL | active | data_warehouse | Use of 6NF structures has a recorded volatility and sparsity reason. | manual_review |
| [ ] | SCL-008 | OPTIONAL | active | OLTP | The sharding choice and reason are recorded. | manual_review |
| [ ] | SCL-010 | OPTIONAL | provisional | OLAP | Replica-based reports are not inputs to transactional processes. | manual_review |
| [ ] | SCL-011 | OPTIONAL | active | OLTP | The pooling mode is recorded and no session-level feature relies on it. | manual_review |
| [ ] | SCL-012 | OPTIONAL | active | OLTP | Cached entities name their invalidation approach. | manual_review |
| [ ] | SCL-013 | OPTIONAL | active | OLTP | A proposed read store states the scale or storage need. | manual_review |
| [ ] | SCL-014 | OPTIONAL | active | OLTP | The engine family choice records the workload and compaction trade-off. | manual_review |
| [ ] | SEC-025 | OPTIONAL | provisional | OLTP | Where used, the design records which attributes are separated and why. | manual_review |
| [ ] | TEN-017 | OPTIONAL | active | data_warehouse, lakehouse | The analytical design records the chosen pattern and the tenant-count assumption. | manual_review |
| [ ] | TEN-022 | OPTIONAL | active | OLTP | Each master data class has a recorded scope. | manual_review |

## Schema Design (136 checks)

| Done | Rule | Level | Status | Scope | Check | Method |
|---|---|---|---|---|---|---|
| [ ] | ARC-003 | MANDATORY | active | OLTP | Each business invariant listed for the model is traced to an engine constraint, or to an approved infrastructure exception. | manual_review |
| [ ] | ARC-004 | MANDATORY | active | data_warehouse, lakehouse | A per-platform enforcement record exists, and every declared but unenforced key has a substitute test (see DQA-004). | catalog_query |
| [ ] | AUD-021 | MANDATORY | provisional | OLTP | Period columns are confirmed system-generated. | manual_review |
| [ ] | ERD-003 | MANDATORY | active | OLTP, data_warehouse | No many-to-many relationship in the logical model lacks an association table in the physical model. | manual_review |
| [ ] | IDX-014 | MANDATORY | active | OLTP, OLAP, data_warehouse | Primary and unique keys on partitioned tables include the partition columns, or the alternative is recorded. | schema_lint |
| [ ] | INT-001 | MANDATORY | active | OLTP | No system-of-record base table lacks a declared primary key. | schema_lint |
| [ ] | INT-002 | MANDATORY | active | OLTP | Each referencing column on a non-sharded system has a foreign key or a recorded INT-003 exception. | schema_lint |
| [ ] | INT-009 | MANDATORY | active | all | Columns under an always-true CHECK are NOT NULL, including for composite conditions. | schema_lint |
| [ ] | NAM-006 | MANDATORY | active | all | Test every identifier against the allowed character set and first-character rule. | schema_lint |
| [ ] | NAM-009 | MANDATORY | active | all | Compare each identifier's byte length with the lowest limit of its declared target engines. | schema_lint |
| [ ] | NAM-011 | MANDATORY | active | all | Compare identifiers with the union of the reserved-word and prefix lists for declared target engines. | schema_lint |
| [ ] | NRM-001 | MANDATORY | active | OLTP | No base-table column holds a delimited list, and no table has numbered columns for one repeating fact. | schema_lint |
| [ ] | SCL-006 | MANDATORY | active | OLTP | On such engines, keys include the distribution column. | schema_lint |
| [ ] | SCL-017 | MANDATORY | active | all | Schema objects are checked against the published limits for the target engine. | schema_lint |
| [ ] | SEC-027 | MANDATORY | active | all | Password storage is confirmed to use a password-hashing algorithm. | manual_review |
| [ ] | TEN-006 | MANDATORY | active | OLTP | Every table marked tenant-scoped has a required tenant identifier. | schema_lint |
| [ ] | TYP-001 | MANDATORY | active | all | Flag floating-type columns registered as money or matching the measure patterns; test pipelines for casts to float. | schema_lint |
| [ ] | ARC-010 | RECOMMENDED | provisional | all | Vendor-specific constructs in the design are identified and each has a stated reason. | manual_review |
| [ ] | AUD-001 | RECOMMENDED | active | OLTP | Business tables have the four attribution values or a recorded exception. | schema_lint |
| [ ] | AUD-002 | RECOMMENDED | active | OLTP | The capture mechanism commits with the change for each in-scope table. | manual_review |
| [ ] | AUD-004 | RECOMMENDED | active | all | A change made through the application is recorded with the acting user. | pipeline_test |
| [ ] | AUD-010 | RECOMMENDED | active | all | The capture configuration lists excluded columns and the reason for any sensitive column retained. | manual_review |
| [ ] | AUD-020 | RECOMMENDED | active | OLTP | Period columns are not writable by application roles. | manual_review |
| [ ] | AUD-023 | RECOMMENDED | active | all | Period timestamps are stored in UTC. | schema_lint |
| [ ] | AUD-025 | RECOMMENDED | active | OLTP | Tables with a deleted flag have a recorded reason and purge path, and the purge checks RET-021 and RET-022. | schema_lint |
| [ ] | ERD-004 | RECOMMENDED | provisional | OLTP | Association tables have a composite key of both foreign keys, or a recorded reason for a surrogate. | schema_lint |
| [ ] | ERD-005 | RECOMMENDED | active | OLTP | Each dependent table has a key or unique constraint that includes the parent key. | schema_lint |
| [ ] | ERD-006 | RECOMMENDED | provisional | OLTP | No table has a type and identifier column pair acting as a reference without an approved deviation. | schema_lint |
| [ ] | ERD-007 | RECOMMENDED | active | OLTP | Each cross-context reference is recorded as identifier or foreign key, with the boundary status. | manual_review |
| [ ] | FIN-001 | RECOMMENDED | active | OLTP | Confirm that period status can differ below company level, at the grain chosen under FIN-002. | manual_review |
| [ ] | FIN-002 | RECOMMENDED | active | OLTP | Confirm the approved grain is recorded and every period status record uses it. | manual_review |
| [ ] | FIN-003 | RECOMMENDED | active | OLTP | Check that calendar periods and per-entity period status are distinct records. | schema_lint |
| [ ] | FIN-013 | RECOMMENDED | active | OLTP, OLAP | Check that rate type or role is part of the rate data. | schema_lint |
| [ ] | FIN-014 | RECOMMENDED | active | OLTP, data_warehouse | Check that rates are unique on pair, date and rate type. | schema_lint |
| [ ] | FIN-017 | RECOMMENDED | active | OLTP | Check that lines hold both transaction and entity amounts with their currencies. | schema_lint |
| [ ] | FIN-029 | RECOMMENDED | active | OLTP | Check that posted documents carry a state and that financial fields are protected after posting. | schema_lint |
| [ ] | FIN-037 | RECOMMENDED | active | OLTP | Check that reversal records carry date, method and reason. | schema_lint |
| [ ] | FIN-043 | RECOMMENDED | active | OLTP | Check that every posting carries exactly one legal entity. | schema_lint |
| [ ] | IDX-001 | RECOMMENDED | active | OLTP | Each secondary index is traceable to a recorded query, join or constraint. | manual_review |
| [ ] | IDX-004 | RECOMMENDED | active | OLTP | Attributes documented as unique have a matching unique constraint or index. | schema_lint |
| [ ] | IDX-005 | RECOMMENDED | active | OLTP | Composite index column order is compared with the predicates of the queries it serves. | manual_review |
| [ ] | IDX-006 | RECOMMENDED | active | OLTP | Foreign keys without a leading-column index are listed and each is indexed or has a recorded exemption. | schema_lint |
| [ ] | IDX-010 | RECOMMENDED | active | OLAP, data_warehouse | Each large analytical table records the platform access path chosen and why. | manual_review |
| [ ] | IDX-013 | RECOMMENDED | active | OLTP, data_warehouse | Each partitioned table records its reason, and the reason is not point lookup speed alone. | manual_review |
| [ ] | IDX-015 | RECOMMENDED | active | OLTP, OLAP, data_warehouse | Partition counts per table are listed and compared with the recorded bound. | catalog_query |
| [ ] | IDX-016 | RECOMMENDED | active | OLTP | Foreign keys touching partitioned tables are confirmed against the engine documentation for the target version. | manual_review |
| [ ] | IDX-017 | RECOMMENDED | active | all | Reviewed queries have type-matched predicates and no unindexed function on a filtered column. | manual_review |
| [ ] | IDX-019 | RECOMMENDED | provisional | OLTP | Each hint has a recorded reason and a review date. | manual_review |
| [ ] | IDX-020 | RECOMMENDED | provisional | all | Maintained queries name their columns. | manual_review |
| [ ] | IDX-021 | RECOMMENDED | active | OLTP | Deep paging endpoints use a keyset with a deterministic sort. | manual_review |
| [ ] | IDX-022 | RECOMMENDED | active | OLTP | Query logs are checked for repeated single-row statements within one request. | runtime_monitor |
| [ ] | IDX-023 | RECOMMENDED | active | OLTP | Generated key columns use the approved default type, or carry a recorded reason for another type. | schema_lint |
| [ ] | INT-004 | RECOMMENDED | active | OLTP | Reference columns match the type and width of the referenced key. | schema_lint |
| [ ] | INT-005 | RECOMMENDED | active | OLTP | Every foreign key has reviewed delete and update actions stated. | schema_lint |
| [ ] | INT-006 | RECOMMENDED | active | OLTP | Each CASCADE is justified as composition, and each other action fits the stated relationship type. | manual_review |
| [ ] | INT-008 | RECOMMENDED | active | all | Each nullable column has a documented meaning for NULL. | schema_lint |
| [ ] | INT-011 | RECOMMENDED | active | OLTP | Effective-dated tables on supporting engines declare the no-overlap rule. | schema_lint |
| [ ] | INT-017 | RECOMMENDED | provisional | OLTP | No process renumbers keys or assigns retired values. | manual_review |
| [ ] | MIG-009 | RECOMMENDED | active | OLTP | Confirm each migration touching an existing table sets a lock timeout and has a defined retry. | migration_lint |
| [ ] | MIG-010 | RECOMMENDED | active | OLTP | Flag blocking forms of index, constraint and type-change operations on tables above the system's size threshold, allowing recorded waivers. | migration_lint |
| [ ] | MIG-012 | RECOMMENDED | active | OLTP | Flag data modification statements inside a migration that also performs DDL, and confirm large backfills have batch size and throttle settings. | migration_lint |
| [ ] | MIG-013 | RECOMMENDED | active | OLTP | Confirm that data changes follow the approved placement and are reviewed like schema changes. | manual_review |
| [ ] | MIG-014 | RECOMMENDED | active | OLTP | Flag migrations that put several DDL statements in one transaction on systems marked high-traffic. | migration_lint |
| [ ] | MIG-015 | RECOMMENDED | active | all | Confirm each engine-specific migration rule or lint configuration records its version range. | manual_review |
| [ ] | MIG-016 | RECOMMENDED | active | OLTP | Confirm the migration plan names a comparison method and that mismatch results were reviewed before cutover. | pipeline_test |
| [ ] | MOD-008 | RECOMMENDED | active | OLAP, data_warehouse | Each large analytical table has its chosen physical keys recorded, or a stated reason for none. | catalog_query |
| [ ] | MOD-009 | RECOMMENDED | active | lakehouse | Tables on supporting platforms use the mutable layout, or have a recorded reason for a fixed one. | catalog_query |
| [ ] | NAM-004 | RECOMMENDED | active | all | Query the catalog for columns with the same domain or foreign key target but different names. | catalog_query |
| [ ] | NAM-008 | RECOMMENDED | active | all | Flag quoted identifiers in migrations, and names in one namespace that differ only by case. | schema_lint |
| [ ] | NAM-010 | RECOMMENDED | active | all | Fail any identifier longer than the approved ceiling. | schema_lint |
| [ ] | NAM-012 | RECOMMENDED | active | all | Test written identifiers in migration and model source against the lowercase, single-underscore form. | schema_lint |
| [ ] | NAM-014 | RECOMMENDED | active | all | Split identifiers into words and flag any word in neither the dictionary nor the register. | schema_lint |
| [ ] | NAM-015 | RECOMMENDED | active | all | Flag table names beginning with a table marker and columns beginning with a data-type marker. | schema_lint |
| [ ] | NAM-017 | RECOMMENDED | active | all | Check that the single-column primary key of each table matches the pattern. | schema_lint |
| [ ] | NAM-018 | RECOMMENDED | active | all | Compare each foreign key column name with the parent key name and the pattern. | catalog_query |
| [ ] | NAM-019 | RECOMMENDED | active | all | List columns carrying the key suffix with no primary, unique or foreign key, and review them. | catalog_query |
| [ ] | NAM-020 | RECOMMENDED | active | all | Check that columns of boolean type match the pattern and that pattern-matching columns have boolean type. | schema_lint |
| [ ] | NAM-021 | RECOMMENDED | active | all | Check that instant-typed and date-typed columns match their patterns. | schema_lint |
| [ ] | NAM-022 | RECOMMENDED | active | all | Check that columns registered as status match the pattern, and that stored codes are lowercase. | schema_lint |
| [ ] | NAM-023 | RECOMMENDED | active | all | Flag constraints and indexes created without a name or with a name not matching the pattern table. | migration_lint |
| [ ] | NAM-024 | RECOMMENDED | active | OLTP | Review schema names against the domain list. | manual_review |
| [ ] | NAM-025 | RECOMMENDED | active | data_warehouse, lakehouse | List schemas in the analytical platform and confirm each maps to one approved layer. | catalog_query |
| [ ] | NAM-026 | RECOMMENDED | active | data_warehouse, lakehouse | Confirm snapshot objects sit only in the snapshot schema. | catalog_query |
| [ ] | NAM-028 | RECOMMENDED | active | all | Check that decimal or integer columns registered as measures match their patterns. | schema_lint |
| [ ] | NRM-005 | RECOMMENDED | active | OLTP | Any redundant column in a base table has a measured need and a named maintaining path. | manual_review |
| [ ] | NRM-009 | RECOMMENDED | active | OLTP | Embedded collections have a stated growth bound, and referenced data is identified. | manual_review |
| [ ] | NRM-010 | RECOMMENDED | provisional | all | Each derived column names exactly one maintaining mechanism. | manual_review |
| [ ] | NUM-016 | RECOMMENDED | provisional | OLTP | Flag any legal document number column sourced from a sequence object. | migration_lint |
| [ ] | NUM-017 | RECOMMENDED | provisional | OLTP | Check each numbered document type has a series scoped to its legal entity. | schema_lint |
| [ ] | NUM-020 | RECOMMENDED | provisional | OLTP | Check that each regime's items are distinct attributes. | schema_lint |
| [ ] | RET-039 | RECOMMENDED | provisional | all | Sample immutable logs for direct identifiers. | manual_review |
| [ ] | SCL-005 | RECOMMENDED | active | OLTP | On range-sharded engines, no high-write table leads its key with a monotonic column. | schema_lint |
| [ ] | SCL-018 | RECOMMENDED | provisional | OLTP | The partition key design states how partition size is bounded. | manual_review |
| [ ] | TEN-007 | RECOMMENDED | active | OLTP | Tenant-scoped tables in dedicated databases carry the same identifier as pooled tables. | schema_lint |
| [ ] | TEN-013 | RECOMMENDED | provisional | OLTP | Unique constraints on tenant-scoped tables include the tenant identifier or have a recorded exception. | schema_lint |
| [ ] | TEN-014 | RECOMMENDED | active | OLTP | Primary keys of sharded tenant-scoped tables begin with the tenant identifier. | schema_lint |
| [ ] | TEN-015 | RECOMMENDED | active | OLTP | No table or column name is specific to one tenant in a shared schema. | schema_lint |
| [ ] | TEN-019 | RECOMMENDED | active | OLTP | Transactional and company-scoped setup tables carry the company identifier. | schema_lint |
| [ ] | TYP-002 | RECOMMENDED | active | all | Flag columns of a proprietary money type. | schema_lint |
| [ ] | TYP-003 | RECOMMENDED | active | all | Compare declared scales with the largest minor unit among the currencies permitted for the column. | catalog_query |
| [ ] | TYP-004 | RECOMMENDED | active | all | List multi-currency monetary columns with scale below 4. | catalog_query |
| [ ] | TYP-005 | RECOMMENDED | active | OLTP, data_warehouse | Confirm each monetary column has a registered currency column or a documented fixed currency. | schema_lint |
| [ ] | TYP-008 | RECOMMENDED | active | all | Flag floating-type columns registered as reconciling quantities. | schema_lint |
| [ ] | TYP-009 | RECOMMENDED | active | OLTP, data_warehouse | Confirm each quantity column has a unit column or a documented fixed unit, and a declared scale. | manual_review |
| [ ] | TYP-010 | RECOMMENDED | provisional | OLTP, data_warehouse | Flag floating-type columns registered as exchange rates. | schema_lint |
| [ ] | TYP-011 | RECOMMENDED | provisional | OLTP, data_warehouse | Confirm the design record states the rate precision and that it covers the provider's delivered precision. | manual_review |
| [ ] | TYP-012 | RECOMMENDED | active | all | Flag instant-named columns with a zone-less type that lack a documented UTC convention. | schema_lint |
| [ ] | TYP-013 | RECOMMENDED | active | all | Flag date-named columns with an instant type, and on Oracle test for non-midnight values. | schema_lint |
| [ ] | TYP-017 | RECOMMENDED | active | OLTP | Review declared lengths against the design record's business limits and the engine annex. | manual_review |
| [ ] | TYP-018 | RECOMMENDED | active | OLTP, data_warehouse | Confirm registered code columns have a content rule. | schema_lint |
| [ ] | TYP-019 | RECOMMENDED | active | all | Query the catalog for database, table and column encodings. | catalog_query |
| [ ] | TYP-020 | RECOMMENDED | active | OLTP, data_warehouse | Compare type, width, character set and collation across each foreign key and registered join. | catalog_query |
| [ ] | TYP-021 | RECOMMENDED | active | OLTP | Flag NP-06 columns that do not have the native boolean type on engines offering one. | schema_lint |
| [ ] | TYP-022 | RECOMMENDED | active | OLTP | Flag native enum columns and long CHECK lists for review against the approved option. | schema_lint |
| [ ] | TYP-024 | RECOMMENDED | active | OLTP | Review JSON columns and generic attribute tables for embedded keys, money or fields used in filters. | manual_review |
| [ ] | TYP-025 | RECOMMENDED | active | OLTP, lakehouse | Flag text columns registered as JSON on engines with a native type. | schema_lint |
| [ ] | TYP-028 | RECOMMENDED | active | all | Review numeric columns whose names suggest codes. | manual_review |
| [ ] | TYP-029 | RECOMMENDED | active | OLTP | Flag 32-bit generated keys on tables not registered as bounded lookups. | schema_lint |
| [ ] | TYP-030 | RECOMMENDED | active | OLTP | Flag columns registered as UUID with a text type. | schema_lint |
| [ ] | TYP-039 | RECOMMENDED | provisional | all | List country and language columns and confirm each reconciles to the ISO list or records its proprietary list. | catalog_query |
| [ ] | FIN-016 | OPTIONAL | active | OLTP, data_warehouse | Confirm the approved approach and test round-trip differences. | manual_review |
| [ ] | IDX-003 | OPTIONAL | active | OLTP | Where a trial was used, its result is recorded with the removal. | manual_review |
| [ ] | IDX-007 | OPTIONAL | active | OLTP | Each covering index names its query and notes the table's update profile. | manual_review |
| [ ] | IDX-008 | OPTIONAL | active | OLTP | Each partial or expression index names its query, and no group of them stands in for partitioning. | manual_review |
| [ ] | IDX-009 | OPTIONAL | active | all | A specialized index records the operator or query that requires it. | manual_review |
| [ ] | IDX-011 | OPTIONAL | active | lakehouse | The clustering or partitioning choice is recorded and matches the current guidance for the table format. | manual_review |
| [ ] | IDX-012 | OPTIONAL | active | OLTP | A proposed OLTP materialized view has a recorded write-cost assessment. | manual_review |
| [ ] | INT-016 | OPTIONAL | active | OLTP | Tables with a surrogate key and a known natural key also have a unique constraint on the natural key. | schema_lint |
| [ ] | MIG-011 | OPTIONAL | active | OLTP | Confirm the migration plan names the tool and the reason, and that the table meets the tool's documented conditions. | manual_review |
| [ ] | MOD-004 | OPTIONAL | active | OLTP | Each hierarchy has a recorded mapping and reason, and required subtype attributes are enforced under the mapping chosen. | manual_review |
| [ ] | MOD-005 | OPTIONAL | active | OLTP | Each hierarchy records its pattern, the read and write reason, and its cycle handling. | manual_review |
| [ ] | MOD-007 | OPTIONAL | provisional | OLTP | The design records the placement and the size and lifecycle reason. | manual_review |
| [ ] | SEC-012 | OPTIONAL | active | all | The chosen layer for each protected store is recorded against its threat. | manual_review |
| [ ] | TEN-009 | OPTIONAL | active | OLTP | The design record names the enforcement point and, where it differs from the accepted default, the recorded reason. | manual_review |
| [ ] | TYP-007 | OPTIONAL | active | all | Confirm integer columns registered as money carry the unit marker and a resolvable currency. | schema_lint |
| [ ] | TYP-023 | OPTIONAL | active | OLTP | Review each native enum for evidence that the set is static. | manual_review |

## Data Validation (24 checks)

| Done | Rule | Level | Status | Scope | Check | Method |
|---|---|---|---|---|---|---|
| [ ] | DQA-002 | MANDATORY | active | OLTP | Tables in the system of record declare their key, reference and value constraints. | schema_lint |
| [ ] | DQA-003 | MANDATORY | active | data_warehouse, lakehouse, OLAP | For each analytical table type in use, the record states which constraints the platform enforces. | catalog_query |
| [ ] | FIN-025 | MANDATORY | active | OLTP | Sum entries per journal in the posting test and in a periodic reconciliation and confirm zero. | pipeline_test |
| [ ] | TEN-002 | MANDATORY | active | OLTP | Tests run the same request under two tenants and confirm no row from the other tenant is returned on each access path. | pipeline_test |
| [ ] | TYP-032 | MANDATORY | active | all | Confirm all primary key columns are NOT NULL in the catalog. | schema_lint |
| [ ] | DQA-001 | RECOMMENDED | active | all | The dataset's validation plan names the layer covering each failure class. | manual_review |
| [ ] | DQA-004 | RECOMMENDED | active | data_warehouse, lakehouse | Each model has passing unique and not-null tests on its declared key. | pipeline_test |
| [ ] | DQA-005 | RECOMMENDED | active | data_warehouse, lakehouse | Relationship tests or lookup orphan counts exist for each declared foreign key. | pipeline_test |
| [ ] | DQA-006 | RECOMMENDED | active | data_warehouse, lakehouse | Constraints with trust enabled have corresponding passing tests. | catalog_query |
| [ ] | DQA-007 | RECOMMENDED | active | data_warehouse, lakehouse | A failed audit leaves the published dataset unchanged. | pipeline_test |
| [ ] | DQA-020 | RECOMMENDED | active | data_warehouse, lakehouse, streaming | Each cross-team dataset has a versioned contract with the listed sections. | catalog_query |
| [ ] | DQA-023 | RECOMMENDED | active | streaming | Each cross-team topic has a registered schema and a mode other than NONE. | catalog_query |
| [ ] | DQA-024 | RECOMMENDED | active | streaming | Long-retention topics are configured with a transitive mode. | catalog_query |
| [ ] | DQA-025 | RECOMMENDED | active | streaming | The change plan states an order consistent with the mode. | manual_review |
| [ ] | FIN-015 | RECOMMENDED | active | OLTP, data_warehouse | Confirm the approved lookup pattern and any staleness limit are documented and tested. | manual_review |
| [ ] | FIN-026 | RECOMMENDED | provisional | OLTP | Sum entries per journal and currency and confirm zero. | pipeline_test |
| [ ] | FIN-047 | RECOMMENDED | active | OLTP, OLAP | Confirm each intercompany entry balances per entity and is linked to its counterpart. | pipeline_test |
| [ ] | TEN-008 | RECOMMENDED | active | OLTP | Requests without tenant context are rejected on each access path. | pipeline_test |
| [ ] | TEN-011 | RECOMMENDED | active | OLTP | Isolation tests execute under the application runtime role and fail if another tenant's row is returned. | pipeline_test |
| [ ] | TST-003 | RECOMMENDED | active | OLTP | Existing tool coverage. Confirm assertions run for critical objects and that constraint tests are not run against faked tables. | pipeline_test |
| [ ] | TYP-034 | RECOMMENDED | active | OLTP, data_warehouse | List unique constraints with nullable columns and confirm the design record states behaviour per engine. | manual_review |
| [ ] | DQA-021 | OPTIONAL | active | data_warehouse, lakehouse, streaming | The contract states where it is enforced. | manual_review |
| [ ] | FIN-021 | OPTIONAL | active | OLTP | Confirm the chosen treatment is documented. | manual_review |
| [ ] | INT-012 | OPTIONAL | active | OLTP | Each cross-table invariant names its enforcement mechanism and known bypasses. | manual_review |

## Transactions (29 checks)

| Done | Rule | Level | Status | Scope | Check | Method |
|---|---|---|---|---|---|---|
| [ ] | FIN-012 | MANDATORY | provisional | OLTP | Review that foreign-currency measurement uses a rate attributable to the transaction date. | manual_review |
| [ ] | NUM-013 | MANDATORY | provisional | OLTP | Confirm counter values are not reused and chain continuity holds, including rejected documents. | pipeline_test |
| [ ] | TXN-001 | MANDATORY | active | OLTP | Each transaction class records engine, level, configuration and the guarantee it depends on. | manual_review |
| [ ] | TXN-003 | MANDATORY | active | OLTP | Each cross-row invariant names the mechanism that protects it. | manual_review |
| [ ] | TXN-004 | MANDATORY | active | OLTP | A test forces a concurrency failure and confirms the whole transaction is retried. | pipeline_test |
| [ ] | TXN-012 | MANDATORY | active | streaming, OLTP | A test replays messages or runs and confirms the result is unchanged. | pipeline_test |
| [ ] | TXN-019 | MANDATORY | active | OLTP | Transaction code on affected engines sets both concerns explicitly. | manual_review |
| [ ] | ARC-005 | RECOMMENDED | active | OLTP | The design lists invariants that need coordination and states how each is protected. | manual_review |
| [ ] | FIN-004 | RECOMMENDED | active | OLTP | Attempt a posting to a closed period and confirm it is refused. | pipeline_test |
| [ ] | FIN-027 | RECOMMENDED | active | OLTP | Inject a failure during posting and confirm no partial journal remains. | pipeline_test |
| [ ] | FIN-034 | RECOMMENDED | active | OLTP | Check that posted financial entry tables do not permit ordinary updates or deletes of financial fields. | schema_lint |
| [ ] | FIN-038 | RECOMMENDED | active | OLTP | Attempt to reverse a settled or transferred item and confirm the block. | pipeline_test |
| [ ] | NUM-019 | RECOMMENDED | provisional | OLTP | Run concurrent postings with failures and confirm no number is lost or duplicated within a series. | pipeline_test |
| [ ] | SCL-007 | RECOMMENDED | active | OLTP | Cross-shard transactions are listed and justified. | manual_review |
| [ ] | TXN-002 | RECOMMENDED | active | OLAP, data_warehouse, lakehouse | Pipelines depending on concurrency record the platform guarantee they use. | manual_review |
| [ ] | TXN-005 | RECOMMENDED | active | OLTP | Transactions touching more than one aggregate are listed and justified. | manual_review |
| [ ] | TXN-007 | RECOMMENDED | active | OLTP | Multi-step edits use a version check and handle a lost compare. | manual_review |
| [ ] | TXN-008 | RECOMMENDED | active | OLTP | Code paths taking multiple locks follow a documented order. | manual_review |
| [ ] | TXN-009 | RECOMMENDED | provisional | OLTP | A duplicate request with the same key returns the recorded outcome and applies no second effect. | pipeline_test |
| [ ] | TXN-010 | RECOMMENDED | active | OLTP | Replay behaviour and key expiry match the approved policy. | pipeline_test |
| [ ] | TXN-011 | RECOMMENDED | active | OLTP, streaming | Events are written in the same transaction as the change, and no separate dual write exists. | manual_review |
| [ ] | TXN-020 | RECOMMENDED | provisional | OLTP | Safety-critical reads are listed with the endpoint or guarantee used. | manual_review |
| [ ] | TXN-021 | RECOMMENDED | provisional | OLTP | Upgrade plans include a recheck of the recorded isolation guarantees. | manual_review |
| [ ] | TXN-022 | RECOMMENDED | provisional | OLTP | Designs of distributed systems of record identify coordinated invariants and how they are preserved. | manual_review |
| [ ] | FIN-035 | OPTIONAL | active | OLTP | Confirm the method and its effect on activity totals are documented. | manual_review |
| [ ] | FIN-036 | OPTIONAL | active | OLTP | Confirm the behaviour matches the approved decision. | manual_review |
| [ ] | INT-007 | OPTIONAL | active | OLTP | Deferrable constraints have a recorded cycle or load-order reason and a supporting engine. | manual_review |
| [ ] | TST-010 | OPTIONAL | active | OLTP | Confirm any such test records the engine, version and isolation level tested. | pipeline_test |
| [ ] | TXN-013 | OPTIONAL | active | OLTP | Multi-service workflows record their compensation steps and where two-phase commit is used. | manual_review |

## ETL/ELT (41 checks)

| Done | Rule | Level | Status | Scope | Check | Method |
|---|---|---|---|---|---|---|
| [ ] | PIP-001 | MANDATORY | active | data_warehouse, lakehouse, streaming | Re-run a step for a fixed interval or offset range and confirm row counts and aggregates in the target do not change. | pipeline_test |
| [ ] | PIP-006 | MANDATORY | active | OLTP, streaming | Every captured table has a primary key or a replica identity that identifies rows. | catalog_query |
| [ ] | PIP-009 | MANDATORY | active | streaming | Delete a source record and confirm a keyed tombstone reaches the compacted topic. | pipeline_test |
| [ ] | PIP-011 | MANDATORY | active | streaming | Each ordering requirement names the key that delivers it and the key is set at production time. | manual_review |
| [ ] | PIP-014 | MANDATORY | active | streaming | Consumer logic has a defined outcome for records arriving after the watermark. | manual_review |
| [ ] | PIP-018 | MANDATORY | active | data_warehouse, lakehouse, OLAP | No monetary column in a typed layer uses a binary floating-point type. | schema_lint |
| [ ] | INT-015 | RECOMMENDED | active | data_warehouse | Each trusted key has a passing compliance test, and loads validate references by lookup. | pipeline_test |
| [ ] | MIG-017 | RECOMMENDED | active | lakehouse | Compare the proposed schema change against the supported set for every format that reads the table. | pipeline_test |
| [ ] | MIG-018 | RECOMMENDED | active | streaming | Run the registry's compatibility check against the proposed schema and confirm that breaking changes have a versioned topic and consumer migration plan. | pipeline_test |
| [ ] | PIP-002 | RECOMMENDED | provisional | data_warehouse, lakehouse, streaming | Each pipeline target has a recorded merge key or partition and interval definition. | catalog_query |
| [ ] | PIP-003 | RECOMMENDED | active | data_warehouse, lakehouse | Re-run a past interval and confirm the step reads only that interval's input and contains no wall-clock logic. | pipeline_test |
| [ ] | PIP-004 | RECOMMENDED | active | streaming | Each event schema names a field or envelope element usable for deduplication. | schema_lint |
| [ ] | PIP-005 | RECOMMENDED | active | streaming | Inject a consumer restart and confirm the sink has no duplicated or missing records. | pipeline_test |
| [ ] | PIP-007 | RECOMMENDED | active | OLTP, streaming | The capture method is recorded per source, and any query-based source states why log access is unavailable. | manual_review |
| [ ] | PIP-008 | RECOMMENDED | provisional | OLTP | Query-extracted tables have a change column that is maintained on every write, and a recorded delete-detection method. | schema_lint |
| [ ] | PIP-010 | RECOMMENDED | active | streaming | Measured rebuild time is below the configured tombstone retention. | runtime_monitor |
| [ ] | PIP-012 | RECOMMENDED | active | streaming | Each event schema has an event-time field separate from processing and ingest timestamps. | schema_lint |
| [ ] | PIP-013 | RECOMMENDED | active | streaming | Each streaming aggregate records its window type, and processing-time windows state why they are acceptable. | manual_review |
| [ ] | PIP-015 | RECOMMENDED | active | streaming, OLAP | Each streaming aggregate table records allowed lateness and post-lateness handling. | manual_review |
| [ ] | PIP-016 | RECOMMENDED | provisional | streaming, OLAP | Each streaming aggregate names a refinement mode consistent with its sink. | manual_review |
| [ ] | PIP-017 | RECOMMENDED | active | lakehouse, streaming | The ingestion configuration declares a schema, and malformed input is captured rather than becoming nulls. | pipeline_test |
| [ ] | PIP-020 | RECOMMENDED | active | lakehouse, data_warehouse | Raw stores appear in access, classification and retention inventories. | catalog_query |
| [ ] | PIP-022 | RECOMMENDED | active | data_warehouse | Staging models have one source and contain no joins or aggregations. | manual_review |
| [ ] | PIP-025 | RECOMMENDED | active | streaming | Topic retention is at least the recorded reprocessing window. | catalog_query |
| [ ] | PIP-026 | RECOMMENDED | active | lakehouse | Multi-table publications define consumer behaviour during partial completion, or cite platform confirmation. | manual_review |
| [ ] | PIP-027 | RECOMMENDED | provisional | data_warehouse, lakehouse, streaming | Each loaded interval has one record with run, position, version and outcome. | catalog_query |
| [ ] | PIP-028 | RECOMMENDED | provisional | data_warehouse, lakehouse | A backfill run names its interval and passes the same promotion gate. | pipeline_test |
| [ ] | PIP-029 | RECOMMENDED | provisional | data_warehouse, lakehouse | A reconciliation result exists for each financial backfill interval. | pipeline_test |
| [ ] | RPT-019 | RECOMMENDED | provisional | data_warehouse | Load a fact before its dimension, then confirm a placeholder member exists and is updated when the dimension arrives. | pipeline_test |
| [ ] | TYP-016 | RECOMMENDED | active | all | Test interface payloads against the ISO 8601 profile. | pipeline_test |
| [ ] | TYP-027 | RECOMMENDED | active | lakehouse, streaming | Compare inferred output types with the contract's declared decimals. | pipeline_test |
| [ ] | ARC-008 | OPTIONAL | active | data_warehouse, lakehouse | The layer list states the purpose of each layer. | manual_review |
| [ ] | NAM-007 | OPTIONAL | active | data_warehouse, lakehouse | Confirm no object outside the raw layer fails the identifier rules. | pipeline_test |
| [ ] | PIP-019 | OPTIONAL | active | lakehouse, data_warehouse | If a raw layer exists, its envelope fields are declared and consumers do not read it directly. | manual_review |
| [ ] | PIP-021 | OPTIONAL | active | data_warehouse, lakehouse | The design record states the pattern chosen and why. | manual_review |
| [ ] | PIP-023 | OPTIONAL | active | data_warehouse, lakehouse, streaming | The design record states the processing mode and the freshness need it meets. | manual_review |
| [ ] | PIP-024 | OPTIONAL | active | streaming, OLAP | A dual path has a recorded justification and one authoritative metric definition. | manual_review |
| [ ] | PIP-030 | OPTIONAL | active | OLAP, streaming | Reprocessing plans state whether output is swapped or overwritten. | manual_review |
| [ ] | PIP-031 | OPTIONAL | active | data_warehouse, lakehouse | The orchestration model is recorded and PIP-001 holds under it. | manual_review |
| [ ] | PIP-032 | OPTIONAL | active | streaming | Each applied transform is listed in the dataset's documentation. | manual_review |
| [ ] | TYP-026 | OPTIONAL | active | lakehouse, data_warehouse | Confirm conformed tables have no semi-structured columns for fields declared in the contract. | pipeline_test |

## Data Quality (28 checks)

| Done | Rule | Level | Status | Scope | Check | Method |
|---|---|---|---|---|---|---|
| [ ] | DQA-008 | MANDATORY | active | data_warehouse, lakehouse | Force a blocking check to fail and confirm downstream publication does not occur. | pipeline_test |
| [ ] | DQA-009 | RECOMMENDED | active | data_warehouse, lakehouse | Each check has a recorded severity. | catalog_query |
| [ ] | DQA-010 | RECOMMENDED | active | data_warehouse, lakehouse | Failing amount or completeness checks on financial datasets stop publication. | pipeline_test |
| [ ] | DQA-011 | RECOMMENDED | active | lakehouse, streaming | Input count equals accepted plus quarantined count for each batch. | runtime_monitor |
| [ ] | DQA-012 | RECOMMENDED | active | all | Quality rules each map to one dimension in the adopted vocabulary. | manual_review |
| [ ] | DQA-013 | RECOMMENDED | provisional | OLTP, data_warehouse, lakehouse | A mapping exists for each dimension, separately for OLTP and analytical layers. | manual_review |
| [ ] | DQA-014 | RECOMMENDED | provisional | all | A list of critical data elements exists and each has quality rules. | manual_review |
| [ ] | DQA-015 | RECOMMENDED | active | data_warehouse, lakehouse | Each batch has a recorded count and aggregate comparison. | pipeline_test |
| [ ] | DQA-016 | RECOMMENDED | provisional | data_warehouse, lakehouse | Financial reconciliation records include amount totals by currency. | pipeline_test |
| [ ] | DQA-017 | RECOMMENDED | active | data_warehouse | Each closed period has a reconciliation with differences classified. | manual_review |
| [ ] | DQA-019 | RECOMMENDED | active | data_warehouse | Fact tables reference an audit dimension or equivalent load context. | schema_lint |
| [ ] | DQA-022 | RECOMMENDED | provisional | all | Standards text states the required capability, and any tool reference is an example. | manual_review |
| [ ] | FIN-028 | RECOMMENDED | active | OLTP | Compare stored balances to the sum of entries and report differences. | catalog_query |
| [ ] | FIN-040 | RECOMMENDED | active | OLTP | List subledger entries not yet transferred and confirm close reports them. | catalog_query |
| [ ] | INT-003 | RECOMMENDED | active | OLTP | Each exception has an indexed reference column, a scheduled orphan audit and a recorded risk acceptance. | pipeline_test |
| [ ] | INT-013 | RECOMMENDED | active | data_warehouse | Fact references resolve to a real or default dimension row, and no undeclared literal stands in for unknown. | pipeline_test |
| [ ] | NUM-015 | RECOMMENDED | provisional | OLTP | List gaps in each series and confirm each has a recorded reason. | catalog_query |
| [ ] | TST-007 | RECOMMENDED | active | OLTP | Stage 3 custom validators required for tenant keys (TST-016), money types (TST-015) and audit columns (TST-017). Confirm each is implemented or waived. | schema_lint |
| [ ] | TST-008 | RECOMMENDED | active | data_warehouse, lakehouse | Existing tool coverage. Confirm each model has key tests and that failures are reported or block as the dataset's tier requires. | pipeline_test |
| [ ] | TST-012 | RECOMMENDED | active | OLTP | Existing tool coverage. Report foreign keys lacking a supporting index where the indexing standard requires one. | catalog_query |
| [ ] | TST-013 | RECOMMENDED | active | OLTP | Existing tool coverage. Report tables lacking a primary key or a framework-required column. | catalog_query |
| [ ] | TST-015 | RECOMMENDED | active | OLTP | Stage 3 custom validator required, built as an engine-neutral catalog query. Identify money columns from metadata or convention and report any column not using an approved type. | catalog_query |
| [ ] | TST-016 | RECOMMENDED | active | OLTP | Stage 3 custom validator required, built as an engine-neutral catalog query. Report tenant-scoped tables lacking the tenant key, excluding approved global tables. | catalog_query |
| [ ] | TST-017 | RECOMMENDED | active | OLTP | Stage 3 custom validator required, built as an engine-neutral catalog query. Report tables in audit scope lacking a required audit column. | catalog_query |
| [ ] | TYP-006 | RECOMMENDED | provisional | OLTP, data_warehouse | Reconcile the reference data with the latest SIX lists and confirm retired codes keep their end dates. | pipeline_test |
| [ ] | TYP-036 | RECOMMENDED | active | all | Profile columns for high-frequency placeholder values. | pipeline_test |
| [ ] | DQA-018 | OPTIONAL | active | all | If used, the difference report is retained with the migration record. | pipeline_test |
| [ ] | TST-014 | OPTIONAL | active | all | Partial tool coverage; Stage 3 custom validator needed for full coverage. Compare identifiers with reserved word lists for each target engine. | schema_lint |

## Governance (151 checks)

| Done | Rule | Level | Status | Scope | Check | Method |
|---|---|---|---|---|---|---|
| [ ] | AUD-005 | MANDATORY | active | OLTP | The runtime role has no write, delete or configuration rights on audit objects. | catalog_query |
| [ ] | AUD-008 | MANDATORY | active | OLTP | Design records state resistance or evidence and make no claim of prevention. | manual_review |
| [ ] | AUD-012 | MANDATORY | active | all | History objects are compared to base tables for protection parity. | catalog_query |
| [ ] | AUD-013 | MANDATORY | provisional | OLTP | The trail is confirmed secure, computer-generated, time-stamped and non-obscuring. | manual_review |
| [ ] | BDR-001 | MANDATORY | provisional | all | Confirm a current BIA exists and that RTO is shorter than MTD. | manual_review |
| [ ] | FIN-031 | MANDATORY | provisional | OLTP | Review that a posted entry's original content and the timing of any change remain ascertainable. | manual_review |
| [ ] | FIN-032 | MANDATORY | provisional | OLTP | Review that controls exist and that records can show transactions accurately. | manual_review |
| [ ] | GOV-014 | MANDATORY | provisional | all | A statement of applicability and clause evidence exist for the claim. | manual_review |
| [ ] | NAM-002 | MANDATORY | active | all | Lint all new or changed identifiers against the approved pattern table; report the share of objects that fail. | schema_lint |
| [ ] | NUM-001 | MANDATORY | provisional | OLTP | Confirm series exist per supplier and numbers are unique and sequential. | manual_review |
| [ ] | NUM-002 | MANDATORY | provisional | OLTP | Confirm one-time issue within each series. | manual_review |
| [ ] | NUM-003 | MANDATORY | provisional | OLTP | Confirm continuity within each series and reasons for any break. | manual_review |
| [ ] | NUM-004 | MANDATORY | provisional | OLTP | Confirm progressive numbering and uniqueness. | manual_review |
| [ ] | NUM-005 | MANDATORY | provisional | OLTP | Confirm series design, including a separate corrective series. | manual_review |
| [ ] | NUM-006 | MANDATORY | provisional | OLTP | Confirm whether the software is in scope and, if so, that records are chained. | manual_review |
| [ ] | NUM-007 | MANDATORY | provisional | OLTP | Confirm sequential numbering and retained explanations for any break. | manual_review |
| [ ] | NUM-008 | MANDATORY | provisional | OLTP | Confirm serial numbering per registered person. | manual_review |
| [ ] | NUM-009 | MANDATORY | provisional | OLTP | Confirm the FBR number, QR and adjustment records for integrated persons. | manual_review |
| [ ] | NUM-010 | MANDATORY | provisional | OLTP | Confirm the number shows order within a sequence. | manual_review |
| [ ] | NUM-011 | MANDATORY | provisional | OLTP | Confirm UUID and sequential number are both present. | manual_review |
| [ ] | NUM-012 | MANDATORY | provisional | OLTP | Confirm sequential numbering per taxpayer. | manual_review |
| [ ] | NUM-014 | MANDATORY | provisional | OLTP | Check national transposition and confirm corrective invoices can cite the corrected number. | manual_review |
| [ ] | RET-001 | MANDATORY | provisional | OLTP, data_warehouse, lakehouse | Check the retention schedule against AO 147 and confirm disposal checks open assessments. | manual_review |
| [ ] | RET-002 | MANDATORY | provisional | OLTP, data_warehouse, lakehouse | Check the schedule entry for German VAT invoices. | manual_review |
| [ ] | RET-003 | MANDATORY | provisional | OLTP, data_warehouse, lakehouse | Check the schedule entry for German commercial records. | manual_review |
| [ ] | RET-004 | MANDATORY | provisional | OLTP, data_warehouse, lakehouse | Confirm archive plans for retired systems follow this timing. | manual_review |
| [ ] | RET-005 | MANDATORY | provisional | OLTP, data_warehouse, lakehouse | Check the schedule entry for French tax records against the current BOFiP. | manual_review |
| [ ] | RET-007 | MANDATORY | provisional | OLTP, data_warehouse, lakehouse | Check the schedule entry for UK VAT records. | manual_review |
| [ ] | RET-008 | MANDATORY | provisional | OLTP, data_warehouse, lakehouse | Check the schedule entry for UK company accounting records. | manual_review |
| [ ] | RET-010 | MANDATORY | provisional | OLTP, data_warehouse, lakehouse | For broker-dealers only, confirm the storage mode and schedule against the rule. | manual_review |
| [ ] | RET-011 | MANDATORY | provisional | OLTP, data_warehouse, lakehouse | Check the schedule entry and that disposal checks open proceedings. | manual_review |
| [ ] | RET-012 | MANDATORY | provisional | OLTP, data_warehouse, lakehouse | Check the schedule entry for integrated persons. | manual_review |
| [ ] | RET-013 | MANDATORY | provisional | OLTP, data_warehouse, lakehouse | Check the schedule entry and the treatment of records under the proviso. | manual_review |
| [ ] | RET-014 | MANDATORY | provisional | OLTP, data_warehouse, lakehouse | Check the schedule entry for Pakistani company books. | manual_review |
| [ ] | RET-015 | MANDATORY | provisional | OLTP, data_warehouse, lakehouse | Check the schedule includes the periods and extension triggers. | manual_review |
| [ ] | RET-016 | MANDATORY | provisional | OLTP, data_warehouse, lakehouse | Check that e-invoice data is under the retention schedule and integrity control. | manual_review |
| [ ] | RET-017 | MANDATORY | provisional | OLTP, data_warehouse, lakehouse | Check the schedule entry for KSA VAT records. | manual_review |
| [ ] | RET-018 | MANDATORY | provisional | OLTP, data_warehouse, lakehouse | Confirm data location and language for KSA VAT records. | manual_review |
| [ ] | RET-019 | MANDATORY | provisional | OLTP, data_warehouse, lakehouse | Confirm stored invoices have integrity and legibility controls for the whole storage period. | manual_review |
| [ ] | RET-020 | MANDATORY | provisional | OLTP, data_warehouse, lakehouse | Scan schemas, logs and backups for stored authentication data. | manual_review |
| [ ] | RET-023 | MANDATORY | provisional | all | Confirm the deletion workflow reaches each downstream recipient. | manual_review |
| [ ] | RET-024 | MANDATORY | provisional | all | Restore a test backup and confirm deletion is re-applied before use. | pipeline_test |
| [ ] | RET-031 | MANDATORY | provisional | all | Confirm log retention and immediate availability for in-scope systems. | manual_review |
| [ ] | RET-032 | MANDATORY | provisional | OLTP | For FDA-regulated records only, confirm trail retention matches the subject record. | manual_review |
| [ ] | RET-034 | MANDATORY | provisional | all | Check that in-scope record classes have a schedule entry with a basis. | catalog_query |
| [ ] | RET-035 | MANDATORY | provisional | all | Sample erasure requests and confirm timely completion or a recorded exception. | manual_review |
| [ ] | RET-036 | MANDATORY | provisional | all | Confirm each retained class under an exception has a recorded basis and extent. | manual_review |
| [ ] | SEC-001 | MANDATORY | active | all | Runtime role owns no objects and holds no administrative or bypass rights. | catalog_query |
| [ ] | SEC-002 | MANDATORY | active | all | Reviewers confirm no value is concatenated into SQL on any access path, including dynamic SQL. | manual_review |
| [ ] | SEC-005 | MANDATORY | provisional | all | Access grants and unique user identification are demonstrated for ePHI stores. | manual_review |
| [ ] | SEC-006 | MANDATORY | provisional | all | A documented emergency procedure exists and its use is recorded. | manual_review |
| [ ] | SEC-010 | MANDATORY | provisional | all | The inventory covers all attributes in in-scope stores. | catalog_query |
| [ ] | SEC-011 | MANDATORY | provisional | all | Each personal data attribute has a recorded purpose. | manual_review |
| [ ] | SEC-015 | MANDATORY | provisional | all | Each stored PAN column maps to a listed approach, confirmed by the assessor. | manual_review |
| [ ] | SEC-017 | MANDATORY | active | all | Each masked column has an additional control recorded. | manual_review |
| [ ] | SEC-019 | MANDATORY | active | all | Key management records match the stated controls. | manual_review |
| [ ] | SEC-021 | MANDATORY | provisional | all | Pre-production stores are confirmed to hold no live PAN. | manual_review |
| [ ] | SEC-022 | MANDATORY | active | all | Test datasets are reviewed for PII. | manual_review |
| [ ] | SEC-026 | MANDATORY | provisional | all | The location and access of pseudonym maps are confirmed separate. | manual_review |
| [ ] | TEN-001 | MANDATORY | active | OLTP | Design record names the isolation mechanism for every tenant data store. | manual_review |
| [ ] | TEN-004 | MANDATORY | active | OLTP | ASTRA design records show the shared pool with tenant identifiers, each dedicated database names its trigger under TEN-005, and any Saudi deployment carries counsel's recorded position. | manual_review |
| [ ] | TEN-010 | MANDATORY | active | OLTP | Compare roles holding bypass or policy-alter rights with the listed set, and confirm the runtime role is absent. | catalog_query |
| [ ] | TEN-012 | MANDATORY | active | OLTP | Each derived store of an isolated table is listed with its tenant restriction. | manual_review |
| [ ] | ARC-006 | RECOMMENDED | active | OLTP | Every schema has one recorded owning context, and shared schemas are recorded as Shared Kernel. | catalog_query |
| [ ] | AUD-006 | RECOMMENDED | active | all | No role holds both audit administration and audit viewing rights. | catalog_query |
| [ ] | AUD-011 | RECOMMENDED | provisional | all | Audit and history stores have a recorded classification. | catalog_query |
| [ ] | AUD-027 | RECOMMENDED | active | OLTP, data_warehouse | Each retained table or store records its expiry mechanism, and disposal jobs check RET-021 and RET-022. | manual_review |
| [ ] | BDR-002 | RECOMMENDED | active | all | Confirm RTO, RPO and MTD are recorded per system with their BIA basis. | manual_review |
| [ ] | BDR-011 | RECOMMENDED | active | all | Confirm each system records an owner for restore capability. | manual_review |
| [ ] | FIN-005 | RECOMMENDED | active | OLTP | Confirm the close procedure has ordered steps and that a failed gate stops the close. | manual_review |
| [ ] | FIN-006 | RECOMMENDED | active | OLTP | Reopen a period and confirm later close results are flagged or rerun and a justification exists. | pipeline_test |
| [ ] | FIN-018 | RECOMMENDED | active | OLTP | Confirm each revaluation can be traced to a run with a rate date. | manual_review |
| [ ] | FIN-033 | RECOMMENDED | provisional | OLTP | Confirm a complete journal population can be produced for a period. | manual_review |
| [ ] | GOV-002 | RECOMMENDED | provisional | all | Every dataset resolves to a named owner. | catalog_query |
| [ ] | GOV-003 | RECOMMENDED | provisional | all | Description coverage on tables and columns meets the adopted threshold. | catalog_query |
| [ ] | GOV-004 | RECOMMENDED | provisional | all | Every column in scope has a classification value. | catalog_query |
| [ ] | GOV-005 | RECOMMENDED | provisional | all | Naming guidance references the adopted alignment. | manual_review |
| [ ] | GOV-006 | RECOMMENDED | active | data_warehouse, lakehouse, streaming | A contract or registry diff in CI produces the classification. | pipeline_test |
| [ ] | GOV-007 | RECOMMENDED | active | data_warehouse, lakehouse, streaming | Each published dataset has upstream lineage available. | catalog_query |
| [ ] | GOV-008 | RECOMMENDED | active | data_warehouse, lakehouse | Lineage retention meets the recorded audit need. | catalog_query |
| [ ] | GOV-009 | RECOMMENDED | active | data_warehouse, lakehouse | Renames in change records state how lineage is preserved. | manual_review |
| [ ] | GOV-010 | RECOMMENDED | active | data_warehouse, lakehouse | Dataset identifiers are unique and unchanged across runs. | catalog_query |
| [ ] | GOV-011 | RECOMMENDED | provisional | all | Glossary terms have owners and link to datasets. | manual_review |
| [ ] | GOV-012 | RECOMMENDED | active | all | Published catalogs expose DCAT 3 terms. | manual_review |
| [ ] | GOV-015 | RECOMMENDED | provisional | all | Datasets designated as records are identified. | manual_review |
| [ ] | GOV-018 | RECOMMENDED | provisional | all | Regulated reports carry an LEI where the confirmed mandate applies. | manual_review |
| [ ] | MIG-001 | RECOMMENDED | active | all | Confirm each environment has a migration history and that every applied entry matches a script in version control. | manual_review |
| [ ] | MIG-002 | RECOMMENDED | active | OLTP, data_warehouse | Compare stored checksums or file hashes of applied migrations with the repository and fail on any change. | migration_lint |
| [ ] | MIG-004 | RECOMMENDED | active | OLTP | For each rename, type change or drop, confirm the release plan shows the expand, migrate and contract steps in separate releases. | manual_review |
| [ ] | MIG-005 | RECOMMENDED | active | OLTP | Confirm the migration policy states the rollback stance and that each release plan names its recovery route. | manual_review |
| [ ] | MIG-006 | RECOMMENDED | active | all | Confirm each merged migration has a review from a named production database owner. | manual_review |
| [ ] | MIG-007 | RECOMMENDED | active | all | Confirm generated migrations show review, and that any drop-plus-add pair was checked for being a rename. | manual_review |
| [ ] | MIG-008 | RECOMMENDED | provisional | OLTP | Confirm both budgets are stated and compare rehearsal lock and duration measurements against them. | pipeline_test |
| [ ] | MIG-019 | RECOMMENDED | active | data_warehouse, lakehouse | Diff the proposed contract against the published one and fail on breaking changes with no new version. | pipeline_test |
| [ ] | MOD-010 | RECOMMENDED | provisional | OLTP, data_warehouse | External consumers are listed against a published interface, and none reads internal tables directly. | manual_review |
| [ ] | NAM-001 | RECOMMENDED | active | all | Confirm a convention document exists, names its owner and states which systems it covers. | manual_review |
| [ ] | NAM-005 | RECOMMENDED | provisional | all | Compare each added name with the history of dropped names and flag matches for review. | migration_lint |
| [ ] | NUM-018 | RECOMMENDED | provisional | OLTP | Confirm the gap rule recorded for each legal entity and series. | manual_review |
| [ ] | RET-009 | RECOMMENDED | provisional | OLTP, data_warehouse, lakehouse | Check the schedule includes the limitation cases and the employment-tax period. | manual_review |
| [ ] | RET-021 | RECOMMENDED | provisional | OLTP, data_warehouse, lakehouse | Check every governed record class has jurisdiction, period, start event and hold status. | catalog_query |
| [ ] | RET-022 | RECOMMENDED | provisional | OLTP, data_warehouse, lakehouse | Attempt disposal of a held record and confirm the block. | pipeline_test |
| [ ] | RET-025 | RECOMMENDED | provisional | all | Restore a test backup and confirm register entries are re-applied. | pipeline_test |
| [ ] | RET-026 | RECOMMENDED | provisional | all | Confirm counsel's position and that backup handling follows it. | manual_review |
| [ ] | RET-027 | RECOMMENDED | provisional | all | Confirm backup retention periods exist and are documented. | manual_review |
| [ ] | RET-028 | RECOMMENDED | provisional | OLTP, data_warehouse, lakehouse | Confirm a field-level retention basis is recorded for retained records. | manual_review |
| [ ] | RET-029 | RECOMMENDED | provisional | all | Confirm erasure evidence exists for a sampled request. | manual_review |
| [ ] | RET-033 | RECOMMENDED | active | all | Check every audit log class has a recorded retention period and basis. | catalog_query |
| [ ] | RET-037 | RECOMMENDED | provisional | all | Confirm erasure is only marked complete after purge or anonymization. | manual_review |
| [ ] | RET-038 | RECOMMENDED | provisional | all | Trace a sampled erasure through each listed store. | manual_review |
| [ ] | RET-040 | RECOMMENDED | provisional | all | Confirm the retention schedule records counsel's determination for ePHI activity logs. | manual_review |
| [ ] | SEC-003 | RECOMMENDED | provisional | all | Each duty maps to a distinct role, and no role combines runtime data access with policy or audit administration. | catalog_query |
| [ ] | SEC-004 | RECOMMENDED | active | all | No shared human accounts exist, and accounts are reviewed on a schedule. | catalog_query |
| [ ] | SEC-007 | RECOMMENDED | active | all | No account is valid in more than one environment. | manual_review |
| [ ] | SEC-008 | RECOMMENDED | active | all | Repositories and deployment definitions contain no credentials. | migration_lint |
| [ ] | SEC-009 | RECOMMENDED | active | all | Attributes holding sensitive data have a recorded classification and required treatment. | catalog_query |
| [ ] | SEC-013 | RECOMMENDED | provisional | all | Each encryption record lists addressed and unaddressed threats. | manual_review |
| [ ] | SEC-014 | RECOMMENDED | active | all | Connections are confirmed to use verified TLS. | runtime_monitor |
| [ ] | SEC-016 | RECOMMENDED | provisional | all | ePHI stores are encrypted, or an equivalent and reasoning are documented. | manual_review |
| [ ] | SEC-018 | RECOMMENDED | active | all | Key storage, rotation triggers and cipher modes are documented. | manual_review |
| [ ] | SEC-020 | RECOMMENDED | active | all | Non-production data sources are confirmed masked or synthetic. | manual_review |
| [ ] | SEC-024 | RECOMMENDED | active | data_warehouse, lakehouse | Sensitive columns carry a tag or policy with an enforced control. | catalog_query |
| [ ] | SEC-028 | RECOMMENDED | active | data_warehouse, lakehouse, OLTP | Datasets described as de-identified have an assessment on record. | manual_review |
| [ ] | SEC-029 | RECOMMENDED | active | data_warehouse, lakehouse | Tag values are scanned for personal data. | catalog_query |
| [ ] | TEN-003 | RECOMMENDED | active | OLTP | A design record states the model, the tenant-count and compliance assumptions and the alternatives rejected. | manual_review |
| [ ] | TEN-016 | RECOMMENDED | active | OLTP | A catalog maps each tenant to its placement, and onboarding and restore runbooks are automated. | manual_review |
| [ ] | TST-001 | RECOMMENDED | provisional | all | Confirm the delivery pipeline runs all three tiers in order and blocks promotion on failure. | pipeline_test |
| [ ] | TST-002 | RECOMMENDED | active | OLTP | Existing tool coverage. Run the linter on every migration; failures block merge unless a waiver is recorded. | migration_lint |
| [ ] | TST-004 | RECOMMENDED | active | OLTP | Confirm the pipeline's test engine and version match production. | pipeline_test |
| [ ] | TST-005 | RECOMMENDED | active | OLTP | Confirm the rehearsal uses masked or synthetic production-like data, and record duration and lock measurements against thresholds. | pipeline_test |
| [ ] | TST-009 | RECOMMENDED | active | OLTP | Confirm the pipeline applies, reverts and re-applies migrations that declare a down path. | pipeline_test |
| [ ] | TST-011 | RECOMMENDED | active | all | Compare production migration history with pipeline runs and report changes with no pipeline record. | manual_review |
| [ ] | ARC-009 | OPTIONAL | active | data_warehouse, lakehouse | The governance record names the ownership model and an owner for each analytical dataset. | manual_review |
| [ ] | AUD-009 | OPTIONAL | active | OLTP | Where used, digests are stored outside the database and verified on a schedule. | manual_review |
| [ ] | BDR-016 | OPTIONAL | active | all | Confirm the chosen tier is recorded and traced to the objectives. | manual_review |
| [ ] | FIN-009 | OPTIONAL | active | OLTP | Confirm the decision is recorded and the system behaves accordingly. | manual_review |
| [ ] | FIN-020 | OPTIONAL | active | OLTP | Confirm the approved method is applied consistently. | manual_review |
| [ ] | FIN-039 | OPTIONAL | provisional | OLTP | Confirm counsel's position is recorded and the behaviour matches it. | manual_review |
| [ ] | FIN-041 | OPTIONAL | active | OLTP | Record whether tamper evidence is used and how it is verified. | manual_review |
| [ ] | GOV-001 | OPTIONAL | provisional | all | Any adopted framework is recorded with the areas it covers. | manual_review |
| [ ] | GOV-013 | OPTIONAL | provisional | all | If used, the scorecard is retained with the design record. | manual_review |
| [ ] | GOV-016 | OPTIONAL | provisional | all | Any use cites the current edition. | manual_review |
| [ ] | GOV-017 | OPTIONAL | provisional | all | The metadata ingestion model is recorded. | manual_review |
| [ ] | MIG-003 | OPTIONAL | active | all | Confirm the system's design record names its authoring model and that any generated plan is committed before it is applied. | manual_review |
| [ ] | MIG-020 | OPTIONAL | active | OLTP | Confirm each tenant has a recorded schema version and report tenants behind the current one. | catalog_query |
| [ ] | NAM-016 | OPTIONAL | provisional | all | Where a registry applies, confirm registered names follow its rule set. | manual_review |
| [ ] | RET-006 | OPTIONAL | provisional | OLTP, data_warehouse, lakehouse | Confirm counsel has confirmed the period before configuration. | manual_review |
| [ ] | RET-030 | OPTIONAL | provisional | all | Confirm preconditions and counsel's position before any claim of erasure by key destruction. | manual_review |
| [ ] | SEC-023 | OPTIONAL | active | all | The benchmark and version in use are recorded per engine. | manual_review |
| [ ] | SEC-030 | OPTIONAL | active | OLTP, data_warehouse | Direct table grants on security-critical tables are limited to the views or permissions recorded. | catalog_query |
| [ ] | TEN-005 | OPTIONAL | active | OLTP | Each dedicated placement records which trigger applied. | manual_review |
| [ ] | TEN-023 | OPTIONAL | active | OLTP | Role definitions state which companies each role can reach. | manual_review |

## Reporting (28 checks)

| Done | Rule | Level | Status | Scope | Check | Method |
|---|---|---|---|---|---|---|
| [ ] | FIN-051 | MANDATORY | provisional | OLTP, OLAP | Confirm consolidated statements can be produced for the parent. | manual_review |
| [ ] | RPT-003 | MANDATORY | active | OLAP, data_warehouse | Each fact table has a one-sentence grain statement and contains only that grain. | manual_review |
| [ ] | RPT-004 | MANDATORY | active | data_warehouse | Shared dimensions appear once on the bus matrix and are reused across facts. | manual_review |
| [ ] | RPT-006 | MANDATORY | active | data_warehouse | No fact foreign key column contains a null, and default rows exist. | pipeline_test |
| [ ] | RPT-015 | MANDATORY | active | data_warehouse | Consumer roles have no direct grant on vault tables. | catalog_query |
| [ ] | FIN-008 | RECOMMENDED | provisional | data_warehouse, lakehouse, OLAP | Check that warehouse period totals reconcile to source period totals including adjustment periods. | pipeline_test |
| [ ] | FIN-049 | RECOMMENDED | active | OLTP, OLAP | Confirm a defined account exists and reconciliation handles differences. | manual_review |
| [ ] | FIN-050 | RECOMMENDED | active | OLTP, OLAP, data_warehouse | Confirm the hierarchy is maintained and used by consolidation. | manual_review |
| [ ] | NAM-027 | RECOMMENDED | active | data_warehouse, lakehouse | Check mart and staging object names against the patterns. | catalog_query |
| [ ] | NRM-007 | RECOMMENDED | active | OLAP, data_warehouse | Snowflaked dimensions in presentation layers have a recorded reason. | manual_review |
| [ ] | RPT-001 | RECOMMENDED | active | OLAP, data_warehouse, lakehouse | Each consumption model records its shape, and wide tables identify the model they derive from. | manual_review |
| [ ] | RPT-005 | RECOMMENDED | active | data_warehouse | Shared entities across marts have a common definition. | manual_review |
| [ ] | RPT-009 | RECOMMENDED | active | data_warehouse | The snapshot key has a passing uniqueness test and the snapshot is excluded from full-refresh rebuilds. | pipeline_test |
| [ ] | RPT-010 | RECOMMENDED | active | data_warehouse | A late fact joins to the dimension version effective on its event date. | pipeline_test |
| [ ] | RPT-011 | RECOMMENDED | active | OLAP, data_warehouse | Each aggregate records its refresh method and source. | manual_review |
| [ ] | RPT-013 | RECOMMENDED | provisional | OLAP, data_warehouse | Each metric has one definition, and dual-path results carry a label. | manual_review |
| [ ] | RPT-014 | RECOMMENDED | active | OLTP, OLAP | Each operational report records its endpoint and why. | manual_review |
| [ ] | RPT-017 | RECOMMENDED | active | data_warehouse | Financial facts state their grain, currency treatment and reconciliation source. | manual_review |
| [ ] | RPT-018 | RECOMMENDED | provisional | data_warehouse | Report output shows freshness and period status. | manual_review |
| [ ] | TYP-015 | RECOMMENDED | active | all | Review range definitions and search query code for BETWEEN on instant columns. | manual_review |
| [ ] | TYP-038 | RECOMMENDED | active | all | Search query and model code for NOT IN over nullable columns. | manual_review |
| [ ] | FIN-022 | OPTIONAL | active | OLTP, OLAP | Confirm the translation path for each consolidation chain. | manual_review |
| [ ] | FIN-048 | OPTIONAL | active | OLTP, OLAP | Record the chosen elimination location and how eliminations are traced. | manual_review |
| [ ] | NRM-004 | OPTIONAL | provisional | OLAP, data_warehouse, lakehouse | Each denormalized structure names its write path and source dependency. | manual_review |
| [ ] | RPT-002 | OPTIONAL | active | data_warehouse, lakehouse | The design record states whether an integration layer exists and why. | manual_review |
| [ ] | RPT-008 | OPTIONAL | active | data_warehouse, lakehouse | Each changing attribute has a recorded history type. | manual_review |
| [ ] | RPT-012 | OPTIONAL | active | OLAP, data_warehouse | If used, metrics resolve to the semantic layer. | manual_review |
| [ ] | RPT-016 | OPTIONAL | active | OLAP | The design record shows the use is single-entity. | manual_review |

## Monitoring (34 checks)

| Done | Rule | Level | Status | Scope | Check | Method |
|---|---|---|---|---|---|---|
| [ ] | AUD-014 | MANDATORY | provisional | all | Logs show individual access to cardholder data, and only authorised parties can alter them. | manual_review |
| [ ] | AUD-015 | MANDATORY | provisional | all | Activity on ePHI is recorded and examinable. | manual_review |
| [ ] | BDR-003 | MANDATORY | active | OLTP | Confirm base backups and log archiving are running without gaps, and that a recovery to a chosen time has succeeded. | runtime_monitor |
| [ ] | BDR-005 | MANDATORY | active | all | Confirm every system with replicas also has independent backups. | manual_review |
| [ ] | BDR-006 | MANDATORY | active | lakehouse, data_warehouse | Confirm a separate backup or reproducibility record exists for each dataset needing recovery beyond the window. | manual_review |
| [ ] | BDR-007 | MANDATORY | active | all | Report the date and result of the latest verified restore per system and alert when one is overdue. | runtime_monitor |
| [ ] | SCL-016 | MANDATORY | active | OLTP | Instance metrics and table counts are compared with the current vendor guidelines. | runtime_monitor |
| [ ] | AUD-003 | RECOMMENDED | active | OLTP | Audit is enabled for the event classes listed. | catalog_query |
| [ ] | AUD-007 | RECOMMENDED | active | all | Audit storage permissions exclude database administrators. | manual_review |
| [ ] | BDR-004 | RECOMMENDED | active | OLTP | Confirm the backup plan does not rely on logical dumps as its only recovery method. | manual_review |
| [ ] | BDR-008 | RECOMMENDED | active | all | Confirm restore test reports include application-level checks and integrity, RTO and RPO results. | manual_review |
| [ ] | BDR-009 | RECOMMENDED | active | all | Report measured recovery duration from the latest rehearsal against RTO. | runtime_monitor |
| [ ] | BDR-010 | RECOMMENDED | active | all | Compare the actual interval between backups or archived logs with the RPO. | runtime_monitor |
| [ ] | BDR-012 | RECOMMENDED | active | all | Confirm copy count, media or location separation, and the last test of the offline copy. | manual_review |
| [ ] | BDR-014 | RECOMMENDED | active | all | Confirm encryption, separate storage location and access lists for backups. | manual_review |
| [ ] | BDR-015 | RECOMMENDED | active | all | Confirm key location, separation from backups, and inclusion of keys in restore tests. | manual_review |
| [ ] | BDR-017 | RECOMMENDED | active | OLTP | Confirm failover automation documents which promotions it refuses, and that this was tested. | manual_review |
| [ ] | BDR-019 | RECOMMENDED | active | all | Confirm the recovery runbook has a state-check step and a record of its result. | manual_review |
| [ ] | BDR-020 | RECOMMENDED | provisional | OLTP, streaming | Confirm the DR plan lists CDC slots and offsets and the steps to re-establish them. | manual_review |
| [ ] | BDR-021 | RECOMMENDED | provisional | OLTP, streaming | Confirm the recovery procedure has this step, and that a rehearsal shows consumers resume without loss or duplication. | manual_review |
| [ ] | FIN-030 | RECOMMENDED | active | OLTP | Alert when a clearing account stays non-zero past its expected settlement window. | runtime_monitor |
| [ ] | IDX-002 | RECOMMENDED | active | OLTP | Index usage counters are reviewed and indexes with no recorded use are removed or justified. | runtime_monitor |
| [ ] | IDX-018 | RECOMMENDED | active | all | Statistics age is monitored and critical query plans are reviewed after major data or version changes. | runtime_monitor |
| [ ] | MON-001 | RECOMMENDED | active | data_warehouse, lakehouse, streaming | Each signal has an active monitor for published datasets. | runtime_monitor |
| [ ] | MON-002 | RECOMMENDED | active | data_warehouse, lakehouse | Metric history exists for monitored datasets. | catalog_query |
| [ ] | MON-003 | RECOMMENDED | active | OLTP, streaming | Alerts exist for lag, stale events and disconnection. | runtime_monitor |
| [ ] | MON-004 | RECOMMENDED | provisional | streaming | Lag and dead-letter counts have monitors. | runtime_monitor |
| [ ] | MON-005 | RECOMMENDED | provisional | data_warehouse, lakehouse | Each monitored dataset resolves to an alert recipient. | catalog_query |
| [ ] | MON-006 | RECOMMENDED | provisional | data_warehouse, lakehouse, streaming | Thresholds are recorded with their owner. | catalog_query |
| [ ] | TST-006 | RECOMMENDED | active | OLTP, data_warehouse | Existing tool coverage. Compare the live catalog with intended state and report any differences. | catalog_query |
| [ ] | TXN-006 | RECOMMENDED | active | OLTP | Transaction duration and idle-in-transaction time are monitored against a set limit. | runtime_monitor |
| [ ] | BDR-013 | OPTIONAL | active | all | Confirm that any immutable copy has a reviewed retention setting and that its legal effect has been considered. | manual_review |
| [ ] | BDR-018 | OPTIONAL | active | OLTP | Confirm the tenant restore method is documented and has been tested for a sample tenant. | manual_review |
| [ ] | MON-007 | OPTIONAL | active | data_warehouse, lakehouse | The detection method is recorded. | manual_review |
