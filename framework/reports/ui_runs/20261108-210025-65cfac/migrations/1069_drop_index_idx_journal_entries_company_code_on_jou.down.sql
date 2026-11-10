-- Step M1069: Drop index idx_journal_entries_company_code on journal_entries
-- Direction: down
-- Findings: PERF-006-067ab8e6
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Table journal_entries exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'journal_entries' AND table_schema = DATABASE()
-- Precheck: Index idx_journal_entries_company_code exists. Expect 1: SELECT COUNT(DISTINCT index_name) FROM information_schema.statistics WHERE table_name = 'journal_entries' AND table_schema = DATABASE() AND index_name = 'idx_journal_entries_company_code'
-- Note: Queries that use this index will degrade after it is dropped. Confirm with usage statistics first.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `journal_entries` ADD INDEX `idx_journal_entries_company_code` (`company_code`), ALGORITHM=INPLACE, LOCK=NONE;
