-- Step M1068: Drop index idx_invoices_service_id on invoices
-- Direction: up
-- Findings: PERF-002-cf89df4f
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Table invoices exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'invoices' AND table_schema = DATABASE()
-- Precheck: Index idx_invoices_service_id exists. Expect 1: SELECT COUNT(DISTINCT index_name) FROM information_schema.statistics WHERE table_name = 'invoices' AND table_schema = DATABASE() AND index_name = 'idx_invoices_service_id'
-- Note: Queries that use this index will degrade after it is dropped. Confirm with usage statistics first.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `invoices` DROP INDEX `idx_invoices_service_id`, ALGORITHM=INPLACE, LOCK=NONE;
