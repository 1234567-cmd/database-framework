-- Step M1058: Drop index idx_debit_notes_company_code on debit_notes
-- Direction: down
-- Findings: PERF-002-7d2d06db
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Table debit_notes exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'debit_notes' AND table_schema = DATABASE()
-- Precheck: Index idx_debit_notes_company_code exists. Expect 1: SELECT COUNT(DISTINCT index_name) FROM information_schema.statistics WHERE table_name = 'debit_notes' AND table_schema = DATABASE() AND index_name = 'idx_debit_notes_company_code'
-- Note: Queries that use this index will degrade after it is dropped. Confirm with usage statistics first.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `debit_notes` ADD INDEX `idx_debit_notes_company_code` (`company_code`), ALGORITHM=INPLACE, LOCK=NONE;
