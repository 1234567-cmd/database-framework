-- Step M1055: Add check constraint check_visa_status_history_previous_status on visa_status_history
-- Direction: up
-- Findings: SCH-046-56235554
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: No rows violate previous_status IN ('Document not Received', 'Documents Received', 'Documents Submitted To Embassy', 'Visa Approved')
-- Precheck: Table visa_status_history exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'visa_status_history' AND table_schema = DATABASE()
-- Precheck: No rows violate previous_status IN ('Document not Received', 'Documents Received', 'Documents Submitted To Embassy', 'Visa Approved'). Expect 0: SELECT COUNT(*) FROM `visa_status_history` WHERE NOT (previous_status IN ('Document not Received', 'Documents Received', 'Documents Submitted To Embassy', 'Visa Approved'))
-- Note: MySQL enforces CHECK from 8.0.16; earlier versions parse and ignore it.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `visa_status_history` ADD CONSTRAINT `check_visa_status_history_previous_status` CHECK (previous_status IN ('Document not Received', 'Documents Received', 'Documents Submitted To Embassy', 'Visa Approved'));
