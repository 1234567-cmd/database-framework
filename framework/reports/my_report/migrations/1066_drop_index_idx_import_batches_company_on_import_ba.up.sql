-- Step M1066: Drop index idx_import_batches_company on import_batches
-- Direction: up
-- Findings: PERF-002-7af86964
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Table import_batches exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'import_batches' AND table_schema = DATABASE()
-- Precheck: Index idx_import_batches_company exists. Expect 1: SELECT COUNT(DISTINCT index_name) FROM information_schema.statistics WHERE table_name = 'import_batches' AND table_schema = DATABASE() AND index_name = 'idx_import_batches_company'
-- Note: Queries that use this index will degrade after it is dropped. Confirm with usage statistics first.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `import_batches` DROP INDEX `idx_import_batches_company`, ALGORITHM=INPLACE, LOCK=NONE;
