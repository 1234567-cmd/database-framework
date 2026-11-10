-- Step M1157: Rename column hotel_allotments.currency_id to currency_code_id
-- Direction: down
-- Findings: SCH-058-d96b6257
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Column hotel_allotments.currency_id exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'hotel_allotments' AND table_schema = DATABASE() AND column_name = 'currency_id'
-- Precheck: Column hotel_allotments.currency_code_id does not exist. Expect 0: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'hotel_allotments' AND table_schema = DATABASE() AND column_name = 'currency_code_id'
-- Note: Renames break every reader that uses the old name. On live systems add a compatible column and migrate callers first (MIG-004).
-- Note: RENAME COLUMN needs MySQL 8.0 or later; earlier versions need CHANGE with the full column definition.
-- Dependency risk: Application code, ORM mappings, reports and ETL jobs outside the database are not analyzed by the migration generator and may use this name.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `hotel_allotments` RENAME COLUMN `currency_code_id` TO `currency_id`, ALGORITHM=INPLACE, LOCK=NONE;
