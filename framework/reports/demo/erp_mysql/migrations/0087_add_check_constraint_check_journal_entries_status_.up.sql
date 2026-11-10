-- Step M087: Add check constraint check_journal_entries_status on journal_entries
-- Direction: up
-- Findings: SCH-046-563ab064
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: No rows violate status IN ('posted')
-- Precheck: Table journal_entries exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'journal_entries' AND table_schema = DATABASE()
-- Precheck: No rows violate status IN ('posted'). Expect 0: SELECT COUNT(*) FROM `journal_entries` WHERE NOT (status IN ('posted'))
-- Note: MySQL enforces CHECK from 8.0.16; earlier versions parse and ignore it.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `journal_entries` ADD CONSTRAINT `check_journal_entries_status` CHECK (status IN ('posted'));
