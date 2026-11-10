-- Step M1046: Add foreign key visa_documents (service_id) -> services
-- Direction: down
-- Findings: SCH-002-a3d23fb3
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: high.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: No orphan rows in visa_documents (service_id) referencing services (FK would fail)
-- Precheck: Table visa_documents exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'visa_documents' AND table_schema = DATABASE()
-- Precheck: Table services exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'services' AND table_schema = DATABASE()
-- Precheck: No orphan rows in visa_documents (service_id) referencing services (FK would fail). Expect 0: SELECT COUNT(*) FROM `visa_documents` c LEFT JOIN `services` p ON c.`service_id` = p.`id` WHERE c.`service_id` IS NOT NULL AND p.`id` IS NULL
-- Note: MySQL only allows INPLACE when foreign_key_checks is off, which would skip validation, so COPY with LOCK=SHARED is used. It blocks writes while running; schedule accordingly.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `visa_documents` DROP FOREIGN KEY `fk_visa_documents_service_id`;
