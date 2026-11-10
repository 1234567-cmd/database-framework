-- Step M1052: Add check constraint check_service_car_transfers_status on service_car_transfers
-- Direction: down
-- Findings: SCH-046-3edb233a
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: No rows violate status IN ('19', '28', '5', '6', '9')
-- Precheck: Table service_car_transfers exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'service_car_transfers' AND table_schema = DATABASE()
-- Precheck: No rows violate status IN ('19', '28', '5', '6', '9'). Expect 0: SELECT COUNT(*) FROM `service_car_transfers` WHERE NOT (status IN ('19', '28', '5', '6', '9'))
-- Note: MySQL enforces CHECK from 8.0.16; earlier versions parse and ignore it.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `service_car_transfers` DROP CHECK `check_service_car_transfers_status`;
