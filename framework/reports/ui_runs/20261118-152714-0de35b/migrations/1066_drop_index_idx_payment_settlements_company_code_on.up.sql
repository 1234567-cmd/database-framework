-- Step M1066: Drop index idx_payment_settlements_company_code on payment_settlements
-- Direction: up
-- Findings: PERF-002-8fd5e2dd
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Table payment_settlements exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'payment_settlements' AND table_schema = DATABASE()
-- Precheck: Index idx_payment_settlements_company_code exists. Expect 1: SELECT COUNT(DISTINCT index_name) FROM information_schema.statistics WHERE table_name = 'payment_settlements' AND table_schema = DATABASE() AND index_name = 'idx_payment_settlements_company_code'
-- Note: Queries that use this index will degrade after it is dropped. Confirm with usage statistics first.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `payment_settlements` DROP INDEX `idx_payment_settlements_company_code`, ALGORITHM=INPLACE, LOCK=NONE;
