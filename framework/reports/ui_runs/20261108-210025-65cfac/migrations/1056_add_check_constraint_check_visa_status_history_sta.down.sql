-- Step M1056: Add check constraint check_visa_status_history_status on visa_status_history
-- Direction: down
-- Findings: SCH-046-4e4eaf0a
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: No rows violate status IN ('Document not Received', 'Documents Received', 'Documents Submitted To Embassy', 'Visa Approved', 'Visa Objection More Document Required', 'Visa Rejected')
-- Precheck: Table visa_status_history exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'visa_status_history' AND table_schema = DATABASE()
-- Precheck: No rows violate status IN ('Document not Received', 'Documents Received', 'Documents Submitted To Embassy', 'Visa Approved', 'Visa Objection More Document Required', 'Visa Rejected'). Expect 0: SELECT COUNT(*) FROM `visa_status_history` WHERE NOT (status IN ('Document not Received', 'Documents Received', 'Documents Submitted To Embassy', 'Visa Approved', 'Visa Objection More Document Required', 'Visa Rejected'))
-- Note: MySQL enforces CHECK from 8.0.16; earlier versions parse and ignore it.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `visa_status_history` DROP CHECK `check_visa_status_history_status`;
