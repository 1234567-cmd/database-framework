-- Step M961: Set documents.user_id NOT NULL
-- Direction: down
-- Findings: SCH-006-5e2b13ba
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: No NULLs in documents.user_id (NOT NULL would fail)
-- Precheck: Table documents exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'documents' AND table_schema = DATABASE()
-- Precheck: Column documents.user_id exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'documents' AND table_schema = DATABASE() AND column_name = 'user_id'
-- Precheck: No NULLs in documents.user_id (NOT NULL would fail). Expect 0: SELECT COUNT(*) FROM `documents` WHERE `user_id` IS NULL
-- Note: MySQL needs STRICT_ALL_TABLES or STRICT_TRANS_TABLES for INPLACE and rejects NULLs instead of converting them.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `documents` MODIFY COLUMN `user_id` int NULL, ALGORITHM=INPLACE, LOCK=NONE;
