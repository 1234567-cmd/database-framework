-- Step M962: Set fee_main_product_codes.product_code_id NOT NULL
-- Direction: down
-- Findings: SCH-006-d841819b
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: No NULLs in fee_main_product_codes.product_code_id (NOT NULL would fail)
-- Precheck: Table fee_main_product_codes exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'fee_main_product_codes' AND table_schema = DATABASE()
-- Precheck: Column fee_main_product_codes.product_code_id exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'fee_main_product_codes' AND table_schema = DATABASE() AND column_name = 'product_code_id'
-- Precheck: No NULLs in fee_main_product_codes.product_code_id (NOT NULL would fail). Expect 0: SELECT COUNT(*) FROM `fee_main_product_codes` WHERE `product_code_id` IS NULL
-- Note: MySQL needs STRICT_ALL_TABLES or STRICT_TRANS_TABLES for INPLACE and rejects NULLs instead of converting them.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `fee_main_product_codes` MODIFY COLUMN `product_code_id` int NULL, ALGORITHM=INPLACE, LOCK=NONE;
