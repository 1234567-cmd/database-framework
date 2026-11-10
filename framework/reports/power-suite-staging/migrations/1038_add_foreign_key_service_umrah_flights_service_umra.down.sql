-- Step M1038: Add foreign key service_umrah_flights (service_umrah_id) -> service_umrahs
-- Direction: down
-- Findings: SCH-002-c16df637
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: high.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: No orphan rows in service_umrah_flights (service_umrah_id) referencing service_umrahs (FK would fail)
-- Precheck: Table service_umrah_flights exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'service_umrah_flights' AND table_schema = DATABASE()
-- Precheck: Table service_umrahs exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'service_umrahs' AND table_schema = DATABASE()
-- Precheck: No orphan rows in service_umrah_flights (service_umrah_id) referencing service_umrahs (FK would fail). Expect 0: SELECT COUNT(*) FROM `service_umrah_flights` c LEFT JOIN `service_umrahs` p ON c.`service_umrah_id` = p.`id` WHERE c.`service_umrah_id` IS NOT NULL AND p.`id` IS NULL
-- Note: MySQL only allows INPLACE when foreign_key_checks is off, which would skip validation, so COPY with LOCK=SHARED is used. It blocks writes while running; schedule accordingly.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `service_umrah_flights` DROP FOREIGN KEY `fk_service_umrah_flights_service_umrah_id`;
