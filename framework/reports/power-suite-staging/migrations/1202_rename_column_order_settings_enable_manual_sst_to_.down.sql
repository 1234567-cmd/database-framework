-- Step M1202: Rename column order_settings.enable_manual_sst to is_enable_manual_sst
-- Direction: down
-- Findings: SCH-060-d6c8201b
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Column order_settings.enable_manual_sst exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'order_settings' AND table_schema = DATABASE() AND column_name = 'enable_manual_sst'
-- Precheck: Column order_settings.is_enable_manual_sst does not exist. Expect 0: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'order_settings' AND table_schema = DATABASE() AND column_name = 'is_enable_manual_sst'
-- Note: Renames break every reader that uses the old name. On live systems add a compatible column and migrate callers first (MIG-004).
-- Note: RENAME COLUMN needs MySQL 8.0 or later; earlier versions need CHANGE with the full column definition.
-- Dependency risk: Application code, ORM mappings, reports and ETL jobs outside the database are not analyzed by the migration generator and may use this name.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `order_settings` RENAME COLUMN `is_enable_manual_sst` TO `enable_manual_sst`, ALGORITHM=INPLACE, LOCK=NONE;
