-- Step M1076: Rename column branch_document_template_pins.version_id to branch_document_template_version_id
-- Direction: up
-- Findings: SCH-058-8ab4887f
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Column branch_document_template_pins.version_id exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'branch_document_template_pins' AND table_schema = DATABASE() AND column_name = 'version_id'
-- Precheck: Column branch_document_template_pins.branch_document_template_version_id does not exist. Expect 0: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'branch_document_template_pins' AND table_schema = DATABASE() AND column_name = 'branch_document_template_version_id'
-- Note: Renames break every reader that uses the old name. On live systems add a compatible column and migrate callers first (MIG-004).
-- Note: RENAME COLUMN needs MySQL 8.0 or later; earlier versions need CHANGE with the full column definition.
-- Dependency risk: Application code, ORM mappings, reports and ETL jobs outside the database are not analyzed by the migration generator and may use this name.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `branch_document_template_pins` RENAME COLUMN `version_id` TO `branch_document_template_version_id`, ALGORITHM=INPLACE, LOCK=NONE;
