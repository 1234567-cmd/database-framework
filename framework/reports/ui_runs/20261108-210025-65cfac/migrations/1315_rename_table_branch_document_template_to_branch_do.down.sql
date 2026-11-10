-- Step M1315: Rename table branch_document_template to branch_document_templates
-- Direction: down
-- Findings: SCH-055-9e354641
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Table branch_document_template exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'branch_document_template' AND table_schema = DATABASE()
-- Note: Renaming a table breaks every reader that uses the old name. Consider a compatibility view for one release.
-- Dependency risk: Foreign key from branch_document_template_pins references branch_document_template.
-- Dependency risk: Foreign key from branch_document_template_versions references branch_document_template.
-- Dependency risk: Application code, ORM mappings, reports and ETL jobs outside the database are not analyzed by the migration generator and may use this name.
SET SESSION lock_wait_timeout = 5;
RENAME TABLE `branch_document_templates` TO `branch_document_template`;
