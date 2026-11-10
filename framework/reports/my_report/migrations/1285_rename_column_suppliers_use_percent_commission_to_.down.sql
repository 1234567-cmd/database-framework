-- Step M1285: Rename column suppliers.use_percent_commission to is_use_percent_commission
-- Direction: down
-- Findings: SCH-060-1b7d68e7
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Column suppliers.use_percent_commission exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'suppliers' AND table_schema = DATABASE() AND column_name = 'use_percent_commission'
-- Precheck: Column suppliers.is_use_percent_commission does not exist. Expect 0: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'suppliers' AND table_schema = DATABASE() AND column_name = 'is_use_percent_commission'
-- Note: Renames break every reader that uses the old name. On live systems add a compatible column and migrate callers first (MIG-004).
-- Note: RENAME COLUMN needs MySQL 8.0 or later; earlier versions need CHANGE with the full column definition.
-- Dependency risk: Application code, ORM mappings, reports and ETL jobs outside the database are not analyzed by the migration generator and may use this name.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `suppliers` RENAME COLUMN `is_use_percent_commission` TO `use_percent_commission`, ALGORITHM=INPLACE, LOCK=NONE;
