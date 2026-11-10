-- Step M1205: Rename column orders.trip_deadline to trip_deadline_at
-- Direction: down
-- Findings: SCH-061-c9d3c65c
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Column orders.trip_deadline exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'orders' AND table_schema = DATABASE() AND column_name = 'trip_deadline'
-- Precheck: Column orders.trip_deadline_at does not exist. Expect 0: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'orders' AND table_schema = DATABASE() AND column_name = 'trip_deadline_at'
-- Note: Renames break every reader that uses the old name. On live systems add a compatible column and migrate callers first (MIG-004).
-- Note: RENAME COLUMN needs MySQL 8.0 or later; earlier versions need CHANGE with the full column definition.
-- Dependency risk: Application code, ORM mappings, reports and ETL jobs outside the database are not analyzed by the migration generator and may use this name.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `orders` RENAME COLUMN `trip_deadline_at` TO `trip_deadline`, ALGORITHM=INPLACE, LOCK=NONE;
