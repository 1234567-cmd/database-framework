-- Step M1116: Rename column customer_memberships.expiry_date to expiry_at
-- Direction: up
-- Findings: SCH-061-7b79ac9b
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Column customer_memberships.expiry_date exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'customer_memberships' AND table_schema = DATABASE() AND column_name = 'expiry_date'
-- Precheck: Column customer_memberships.expiry_at does not exist. Expect 0: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'customer_memberships' AND table_schema = DATABASE() AND column_name = 'expiry_at'
-- Note: Renames break every reader that uses the old name. On live systems add a compatible column and migrate callers first (MIG-004).
-- Note: RENAME COLUMN needs MySQL 8.0 or later; earlier versions need CHANGE with the full column definition.
-- Dependency risk: Application code, ORM mappings, reports and ETL jobs outside the database are not analyzed by the migration generator and may use this name.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `customer_memberships` RENAME COLUMN `expiry_date` TO `expiry_at`, ALGORITHM=INPLACE, LOCK=NONE;
