-- Step M1267: Rename column services.ticket_issue_date to ticket_issue_at
-- Direction: up
-- Findings: SCH-061-8d8547be
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Column services.ticket_issue_date exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'services' AND table_schema = DATABASE() AND column_name = 'ticket_issue_date'
-- Precheck: Column services.ticket_issue_at does not exist. Expect 0: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'services' AND table_schema = DATABASE() AND column_name = 'ticket_issue_at'
-- Note: Renames break every reader that uses the old name. On live systems add a compatible column and migrate callers first (MIG-004).
-- Note: RENAME COLUMN needs MySQL 8.0 or later; earlier versions need CHANGE with the full column definition.
-- Dependency risk: Application code, ORM mappings, reports and ETL jobs outside the database are not analyzed by the migration generator and may use this name.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `services` RENAME COLUMN `ticket_issue_date` TO `ticket_issue_at`, ALGORITHM=INPLACE, LOCK=NONE;
