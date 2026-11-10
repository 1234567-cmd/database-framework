-- Step M073: Add surrogate primary key id to order_items
-- Direction: up
-- Findings: SCH-001-3e750629
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: high.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Table order_items exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'order_items' AND table_schema = DATABASE()
-- Precheck: Column order_items.id does not exist. Expect 0: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'order_items' AND table_schema = DATABASE() AND column_name = 'id'
-- Note: Adding an AUTO_INCREMENT column rebuilds the table and blocks concurrent DML in MySQL; use an online schema change tool on large tables.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `order_items` ADD COLUMN `id` BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY FIRST, ALGORITHM=INPLACE, LOCK=SHARED;
