-- Step M1292: Rename column user_other_ids.source_id to integration_source_id
-- Direction: down
-- Findings: SCH-058-14f7699b
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Column user_other_ids.source_id exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'user_other_ids' AND table_schema = DATABASE() AND column_name = 'source_id'
-- Precheck: Column user_other_ids.integration_source_id does not exist. Expect 0: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'user_other_ids' AND table_schema = DATABASE() AND column_name = 'integration_source_id'
-- Note: Renames break every reader that uses the old name. On live systems add a compatible column and migrate callers first (MIG-004).
-- Note: RENAME COLUMN needs MySQL 8.0 or later; earlier versions need CHANGE with the full column definition.
-- Dependency risk: Application code, ORM mappings, reports and ETL jobs outside the database are not analyzed by the migration generator and may use this name.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `user_other_ids` RENAME COLUMN `integration_source_id` TO `source_id`, ALGORITHM=INPLACE, LOCK=NONE;
