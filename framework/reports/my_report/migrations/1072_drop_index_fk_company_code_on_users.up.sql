-- Step M1072: Drop index fk_company_code on users
-- Direction: up
-- Findings: PERF-002-81ca3075
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Table users exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'users' AND table_schema = DATABASE()
-- Precheck: Index fk_company_code exists. Expect 1: SELECT COUNT(DISTINCT index_name) FROM information_schema.statistics WHERE table_name = 'users' AND table_schema = DATABASE() AND index_name = 'fk_company_code'
-- Note: Queries that use this index will degrade after it is dropped. Confirm with usage statistics first.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `users` DROP INDEX `fk_company_code`, ALGORITHM=INPLACE, LOCK=NONE;
