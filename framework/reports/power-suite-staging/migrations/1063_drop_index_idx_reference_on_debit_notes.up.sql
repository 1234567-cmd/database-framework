-- Step M1063: Drop index idx_reference on debit_notes
-- Direction: up
-- Findings: PERF-002-4d324b47
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Table debit_notes exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'debit_notes' AND table_schema = DATABASE()
-- Precheck: Index idx_reference exists. Expect 1: SELECT COUNT(DISTINCT index_name) FROM information_schema.statistics WHERE table_name = 'debit_notes' AND table_schema = DATABASE() AND index_name = 'idx_reference'
-- Note: Queries that use this index will degrade after it is dropped. Confirm with usage statistics first.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `debit_notes` DROP INDEX `idx_reference`, ALGORITHM=INPLACE, LOCK=NONE;
