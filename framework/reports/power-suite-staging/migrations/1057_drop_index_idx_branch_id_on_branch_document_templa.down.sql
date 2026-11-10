-- Step M1057: Drop index idx_branch_id on branch_document_template
-- Direction: down
-- Findings: PERF-002-b376801e
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Table branch_document_template exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'branch_document_template' AND table_schema = DATABASE()
-- Precheck: Index idx_branch_id exists. Expect 1: SELECT COUNT(DISTINCT index_name) FROM information_schema.statistics WHERE table_name = 'branch_document_template' AND table_schema = DATABASE() AND index_name = 'idx_branch_id'
-- Note: Queries that use this index will degrade after it is dropped. Confirm with usage statistics first.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `branch_document_template` ADD INDEX `idx_branch_id` (`branch_id`), ALGORITHM=INPLACE, LOCK=NONE;
