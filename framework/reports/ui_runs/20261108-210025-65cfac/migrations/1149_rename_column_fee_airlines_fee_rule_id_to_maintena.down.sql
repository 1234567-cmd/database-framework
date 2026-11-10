-- Step M1149: Rename column fee_airlines.fee_rule_id to maintenance_fee_group_id
-- Direction: down
-- Findings: SCH-058-aeefdb4e
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Column fee_airlines.fee_rule_id exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'fee_airlines' AND table_schema = DATABASE() AND column_name = 'fee_rule_id'
-- Precheck: Column fee_airlines.maintenance_fee_group_id does not exist. Expect 0: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'fee_airlines' AND table_schema = DATABASE() AND column_name = 'maintenance_fee_group_id'
-- Note: Renames break every reader that uses the old name. On live systems add a compatible column and migrate callers first (MIG-004).
-- Note: RENAME COLUMN needs MySQL 8.0 or later; earlier versions need CHANGE with the full column definition.
-- Dependency risk: Application code, ORM mappings, reports and ETL jobs outside the database are not analyzed by the migration generator and may use this name.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `fee_airlines` RENAME COLUMN `maintenance_fee_group_id` TO `fee_rule_id`, ALGORITHM=INPLACE, LOCK=NONE;
