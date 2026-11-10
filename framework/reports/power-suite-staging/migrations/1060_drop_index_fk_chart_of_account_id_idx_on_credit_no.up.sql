-- Step M1060: Drop index fk_chart_of_account_id_idx on credit_notes
-- Direction: up
-- Findings: PERF-002-8961e731
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Table credit_notes exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'credit_notes' AND table_schema = DATABASE()
-- Precheck: Index fk_chart_of_account_id_idx exists. Expect 1: SELECT COUNT(DISTINCT index_name) FROM information_schema.statistics WHERE table_name = 'credit_notes' AND table_schema = DATABASE() AND index_name = 'fk_chart_of_account_id_idx'
-- Note: Queries that use this index will degrade after it is dropped. Confirm with usage statistics first.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `credit_notes` DROP INDEX `fk_chart_of_account_id_idx`, ALGORITHM=INPLACE, LOCK=NONE;
