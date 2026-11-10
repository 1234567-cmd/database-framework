-- Step M1172: Rename column hotel_allotments.pr_1_star to is_pr_1_star
-- Direction: up
-- Findings: SCH-060-5ce06b0d
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Column hotel_allotments.pr_1_star exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'hotel_allotments' AND table_schema = DATABASE() AND column_name = 'pr_1_star'
-- Precheck: Column hotel_allotments.is_pr_1_star does not exist. Expect 0: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'hotel_allotments' AND table_schema = DATABASE() AND column_name = 'is_pr_1_star'
-- Note: Renames break every reader that uses the old name. On live systems add a compatible column and migrate callers first (MIG-004).
-- Note: RENAME COLUMN needs MySQL 8.0 or later; earlier versions need CHANGE with the full column definition.
-- Dependency risk: Application code, ORM mappings, reports and ETL jobs outside the database are not analyzed by the migration generator and may use this name.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `hotel_allotments` RENAME COLUMN `pr_1_star` TO `is_pr_1_star`, ALGORITHM=INPLACE, LOCK=NONE;
