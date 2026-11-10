-- Step M1061: Drop index idx_credit_notes_company_code on credit_notes
-- Direction: up
-- Findings: PERF-002-c866d797
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Table credit_notes exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'credit_notes' AND table_schema = DATABASE()
-- Precheck: Index idx_credit_notes_company_code exists. Expect 1: SELECT COUNT(DISTINCT index_name) FROM information_schema.statistics WHERE table_name = 'credit_notes' AND table_schema = DATABASE() AND index_name = 'idx_credit_notes_company_code'
-- Note: Queries that use this index will degrade after it is dropped. Confirm with usage statistics first.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `credit_notes` DROP INDEX `idx_credit_notes_company_code`, ALGORITHM=INPLACE, LOCK=NONE;
