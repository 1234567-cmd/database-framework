-- Step M1053: Add check constraint check_service_umrahs_status on service_umrahs
-- Direction: down
-- Findings: SCH-046-96694dde
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: No rows violate status IN ('ACTIVE', 'Booked', 'CONFIRM', 'Confirm', 'NA')
-- Precheck: Table service_umrahs exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'service_umrahs' AND table_schema = DATABASE()
-- Precheck: No rows violate status IN ('ACTIVE', 'Booked', 'CONFIRM', 'Confirm', 'NA'). Expect 0: SELECT COUNT(*) FROM `service_umrahs` WHERE NOT (status IN ('ACTIVE', 'Booked', 'CONFIRM', 'Confirm', 'NA'))
-- Note: MySQL enforces CHECK from 8.0.16; earlier versions parse and ignore it.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `service_umrahs` DROP CHECK `check_service_umrahs_status`;
