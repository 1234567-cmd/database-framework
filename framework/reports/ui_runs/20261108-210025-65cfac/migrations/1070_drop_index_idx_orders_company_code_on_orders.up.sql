-- Step M1070: Drop index idx_orders_company_code on orders
-- Direction: up
-- Findings: PERF-002-8e91bde5
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Table orders exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'orders' AND table_schema = DATABASE()
-- Precheck: Index idx_orders_company_code exists. Expect 1: SELECT COUNT(DISTINCT index_name) FROM information_schema.statistics WHERE table_name = 'orders' AND table_schema = DATABASE() AND index_name = 'idx_orders_company_code'
-- Note: Queries that use this index will degrade after it is dropped. Confirm with usage statistics first.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `orders` DROP INDEX `idx_orders_company_code`, ALGORITHM=INPLACE, LOCK=NONE;
