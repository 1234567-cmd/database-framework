-- Step M1003: Add foreign key customers (trade_group_id) -> trade_groups
-- Direction: down
-- Findings: SCH-002-d7ed32de
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: high.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: No orphan rows in customers (trade_group_id) referencing trade_groups (FK would fail)
-- Precheck: Table customers exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'customers' AND table_schema = DATABASE()
-- Precheck: Table trade_groups exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'trade_groups' AND table_schema = DATABASE()
-- Precheck: No orphan rows in customers (trade_group_id) referencing trade_groups (FK would fail). Expect 0: SELECT COUNT(*) FROM `customers` c LEFT JOIN `trade_groups` p ON c.`trade_group_id` = p.`id` WHERE c.`trade_group_id` IS NOT NULL AND p.`id` IS NULL
-- Note: MySQL only allows INPLACE when foreign_key_checks is off, which would skip validation, so COPY with LOCK=SHARED is used. It blocks writes while running; schedule accordingly.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `customers` DROP FOREIGN KEY `fk_customers_trade_group_id`;
