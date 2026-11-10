-- Step M1075: Rename column branch_document_template_pins.template_id to branch_document_template_id
-- Direction: down
-- Findings: SCH-058-5bea978b
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Column branch_document_template_pins.template_id exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'branch_document_template_pins' AND table_schema = DATABASE() AND column_name = 'template_id'
-- Precheck: Column branch_document_template_pins.branch_document_template_id does not exist. Expect 0: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'branch_document_template_pins' AND table_schema = DATABASE() AND column_name = 'branch_document_template_id'
-- Note: Renames break every reader that uses the old name. On live systems add a compatible column and migrate callers first (MIG-004).
-- Note: RENAME COLUMN needs MySQL 8.0 or later; earlier versions need CHANGE with the full column definition.
-- Dependency risk: Application code, ORM mappings, reports and ETL jobs outside the database are not analyzed by the migration generator and may use this name.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `branch_document_template_pins` RENAME COLUMN `branch_document_template_id` TO `template_id`, ALGORITHM=INPLACE, LOCK=NONE;
