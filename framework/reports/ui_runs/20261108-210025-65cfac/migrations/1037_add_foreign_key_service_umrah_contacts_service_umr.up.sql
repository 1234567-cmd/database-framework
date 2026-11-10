-- Step M1037: Add foreign key service_umrah_contacts (service_umrah_id) -> service_umrahs
-- Direction: up
-- Findings: SCH-002-8cf0a142
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: high.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: No orphan rows in service_umrah_contacts (service_umrah_id) referencing service_umrahs (FK would fail)
-- Precheck: Table service_umrah_contacts exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'service_umrah_contacts' AND table_schema = DATABASE()
-- Precheck: Table service_umrahs exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'service_umrahs' AND table_schema = DATABASE()
-- Precheck: No orphan rows in service_umrah_contacts (service_umrah_id) referencing service_umrahs (FK would fail). Expect 0: SELECT COUNT(*) FROM `service_umrah_contacts` c LEFT JOIN `service_umrahs` p ON c.`service_umrah_id` = p.`id` WHERE c.`service_umrah_id` IS NOT NULL AND p.`id` IS NULL
-- Note: MySQL only allows INPLACE when foreign_key_checks is off, which would skip validation, so COPY with LOCK=SHARED is used. It blocks writes while running; schedule accordingly.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `service_umrah_contacts` ADD CONSTRAINT `fk_service_umrah_contacts_service_umrah_id` FOREIGN KEY (`service_umrah_id`) REFERENCES `service_umrahs` (`id`), ALGORITHM=COPY, LOCK=SHARED;
