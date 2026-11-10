-- Step M1214: Rename column refunds.debit_note_generated to is_debit_note_generated
-- Direction: up
-- Findings: SCH-060-cc348414
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Column refunds.debit_note_generated exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'refunds' AND table_schema = DATABASE() AND column_name = 'debit_note_generated'
-- Precheck: Column refunds.is_debit_note_generated does not exist. Expect 0: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'refunds' AND table_schema = DATABASE() AND column_name = 'is_debit_note_generated'
-- Note: Renames break every reader that uses the old name. On live systems add a compatible column and migrate callers first (MIG-004).
-- Note: RENAME COLUMN needs MySQL 8.0 or later; earlier versions need CHANGE with the full column definition.
-- Dependency risk: View refunds_with_conversion references refunds.debit_note_generated; check its definition.
-- Dependency risk: Application code, ORM mappings, reports and ETL jobs outside the database are not analyzed by the migration generator and may use this name.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `refunds` RENAME COLUMN `debit_note_generated` TO `is_debit_note_generated`, ALGORITHM=INPLACE, LOCK=NONE;
