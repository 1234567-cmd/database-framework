-- Step M1071: Drop index idx_tcid_users_company on tcid_users
-- Direction: down
-- Findings: PERF-002-090cfac1
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Table tcid_users exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'tcid_users' AND table_schema = DATABASE()
-- Precheck: Index idx_tcid_users_company exists. Expect 1: SELECT COUNT(DISTINCT index_name) FROM information_schema.statistics WHERE table_name = 'tcid_users' AND table_schema = DATABASE() AND index_name = 'idx_tcid_users_company'
-- Note: Queries that use this index will degrade after it is dropped. Confirm with usage statistics first.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `tcid_users` ADD INDEX `idx_tcid_users_company` (`company_code`), ALGORITHM=INPLACE, LOCK=NONE;
