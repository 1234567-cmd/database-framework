-- Step M1085: Rename column coa_template_rows.template_id to coa_template_id
-- Direction: up
-- Findings: SCH-058-d1c93b91
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Column coa_template_rows.template_id exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'coa_template_rows' AND table_schema = DATABASE() AND column_name = 'template_id'
-- Precheck: Column coa_template_rows.coa_template_id does not exist. Expect 0: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'coa_template_rows' AND table_schema = DATABASE() AND column_name = 'coa_template_id'
-- Note: Renames break every reader that uses the old name. On live systems add a compatible column and migrate callers first (MIG-004).
-- Note: RENAME COLUMN needs MySQL 8.0 or later; earlier versions need CHANGE with the full column definition.
-- Dependency risk: Application code, ORM mappings, reports and ETL jobs outside the database are not analyzed by the migration generator and may use this name.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `coa_template_rows` RENAME COLUMN `template_id` TO `coa_template_id`, ALGORITHM=INPLACE, LOCK=NONE;
