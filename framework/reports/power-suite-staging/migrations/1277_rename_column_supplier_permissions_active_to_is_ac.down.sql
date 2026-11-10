-- Step M1277: Rename column supplier_permissions.active to is_active
-- Direction: down
-- Findings: SCH-060-d3222fdc
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Column supplier_permissions.active exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'supplier_permissions' AND table_schema = DATABASE() AND column_name = 'active'
-- Precheck: Column supplier_permissions.is_active does not exist. Expect 0: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'supplier_permissions' AND table_schema = DATABASE() AND column_name = 'is_active'
-- Note: Renames break every reader that uses the old name. On live systems add a compatible column and migrate callers first (MIG-004).
-- Note: RENAME COLUMN needs MySQL 8.0 or later; earlier versions need CHANGE with the full column definition.
-- Dependency risk: Application code, ORM mappings, reports and ETL jobs outside the database are not analyzed by the migration generator and may use this name.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `supplier_permissions` RENAME COLUMN `is_active` TO `active`, ALGORITHM=INPLACE, LOCK=NONE;
