-- Step M1324: Rename table special_seat to special_seats
-- Direction: up
-- Findings: SCH-055-dcc3e2dc
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Table special_seat exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'special_seat' AND table_schema = DATABASE()
-- Note: Renaming a table breaks every reader that uses the old name. Consider a compatibility view for one release.
-- Dependency risk: Application code, ORM mappings, reports and ETL jobs outside the database are not analyzed by the migration generator and may use this name.
SET SESSION lock_wait_timeout = 5;
RENAME TABLE `special_seat` TO `special_seats`;
