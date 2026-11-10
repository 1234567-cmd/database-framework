-- Step M1058: Drop index idx_costs_company_code on costs
-- Direction: up
-- Findings: PERF-002-101596b8
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Table costs exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'costs' AND table_schema = DATABASE()
-- Precheck: Index idx_costs_company_code exists. Expect 1: SELECT COUNT(DISTINCT index_name) FROM information_schema.statistics WHERE table_name = 'costs' AND table_schema = DATABASE() AND index_name = 'idx_costs_company_code'
-- Note: Queries that use this index will degrade after it is dropped. Confirm with usage statistics first.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `costs` DROP INDEX `idx_costs_company_code`, ALGORITHM=INPLACE, LOCK=NONE;
