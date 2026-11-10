-- Step M987: Set ticket_inventory_details.service_passenger_id NOT NULL
-- Direction: down
-- Findings: SCH-006-d9f92ae0
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: No NULLs in ticket_inventory_details.service_passenger_id (NOT NULL would fail)
-- Precheck: Table ticket_inventory_details exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'ticket_inventory_details' AND table_schema = DATABASE()
-- Precheck: Column ticket_inventory_details.service_passenger_id exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'ticket_inventory_details' AND table_schema = DATABASE() AND column_name = 'service_passenger_id'
-- Precheck: No NULLs in ticket_inventory_details.service_passenger_id (NOT NULL would fail). Expect 0: SELECT COUNT(*) FROM `ticket_inventory_details` WHERE `service_passenger_id` IS NULL
-- Note: MySQL needs STRICT_ALL_TABLES or STRICT_TRANS_TABLES for INPLACE and rejects NULLs instead of converting them.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `ticket_inventory_details` MODIFY COLUMN `service_passenger_id` int NULL, ALGORITHM=INPLACE, LOCK=NONE;
