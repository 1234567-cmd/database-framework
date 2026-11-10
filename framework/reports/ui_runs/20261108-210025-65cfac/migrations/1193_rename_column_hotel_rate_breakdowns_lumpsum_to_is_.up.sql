-- Step M1193: Rename column hotel_rate_breakdowns.lumpsum to is_lumpsum
-- Direction: up
-- Findings: SCH-060-73eb8a5d
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Column hotel_rate_breakdowns.lumpsum exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'hotel_rate_breakdowns' AND table_schema = DATABASE() AND column_name = 'lumpsum'
-- Precheck: Column hotel_rate_breakdowns.is_lumpsum does not exist. Expect 0: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'hotel_rate_breakdowns' AND table_schema = DATABASE() AND column_name = 'is_lumpsum'
-- Note: Renames break every reader that uses the old name. On live systems add a compatible column and migrate callers first (MIG-004).
-- Note: RENAME COLUMN needs MySQL 8.0 or later; earlier versions need CHANGE with the full column definition.
-- Dependency risk: Application code, ORM mappings, reports and ETL jobs outside the database are not analyzed by the migration generator and may use this name.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `hotel_rate_breakdowns` RENAME COLUMN `lumpsum` TO `is_lumpsum`, ALGORITHM=INPLACE, LOCK=NONE;
