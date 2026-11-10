-- Step M1054: Add check constraint check_service_visas_status on service_visas
-- Direction: down
-- Findings: SCH-046-d6f53adb
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: No rows violate status IN ('Document not Received', 'Documents Received', 'Documents Submitted To Embassy', 'Visa Approved', 'Visa Objection More Document Required', 'Visa Rejected')
-- Precheck: Table service_visas exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'service_visas' AND table_schema = DATABASE()
-- Precheck: No rows violate status IN ('Document not Received', 'Documents Received', 'Documents Submitted To Embassy', 'Visa Approved', 'Visa Objection More Document Required', 'Visa Rejected'). Expect 0: SELECT COUNT(*) FROM `service_visas` WHERE NOT (status IN ('Document not Received', 'Documents Received', 'Documents Submitted To Embassy', 'Visa Approved', 'Visa Objection More Document Required', 'Visa Rejected'))
-- Note: MySQL enforces CHECK from 8.0.16; earlier versions parse and ignore it.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `service_visas` DROP CHECK `check_service_visas_status`;
