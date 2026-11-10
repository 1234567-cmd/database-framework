-- Step M1086: Rename column coa_templates.created_by to admin_user_id
-- Direction: up
-- Findings: SCH-058-3a26cba3
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Column coa_templates.created_by exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'coa_templates' AND table_schema = DATABASE() AND column_name = 'created_by'
-- Precheck: Column coa_templates.admin_user_id does not exist. Expect 0: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'coa_templates' AND table_schema = DATABASE() AND column_name = 'admin_user_id'
-- Note: Renames break every reader that uses the old name. On live systems add a compatible column and migrate callers first (MIG-004).
-- Note: RENAME COLUMN needs MySQL 8.0 or later; earlier versions need CHANGE with the full column definition.
-- Dependency risk: Application code, ORM mappings, reports and ETL jobs outside the database are not analyzed by the migration generator and may use this name.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `coa_templates` RENAME COLUMN `created_by` TO `admin_user_id`, ALGORITHM=INPLACE, LOCK=NONE;
