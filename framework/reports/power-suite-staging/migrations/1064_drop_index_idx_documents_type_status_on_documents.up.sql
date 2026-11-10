-- Step M1064: Drop index idx_documents_type_status on documents
-- Direction: up
-- Findings: PERF-002-22cae3f0
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Table documents exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'documents' AND table_schema = DATABASE()
-- Precheck: Index idx_documents_type_status exists. Expect 1: SELECT COUNT(DISTINCT index_name) FROM information_schema.statistics WHERE table_name = 'documents' AND table_schema = DATABASE() AND index_name = 'idx_documents_type_status'
-- Note: Queries that use this index will degrade after it is dropped. Confirm with usage statistics first.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `documents` DROP INDEX `idx_documents_type_status`, ALGORITHM=INPLACE, LOCK=NONE;
