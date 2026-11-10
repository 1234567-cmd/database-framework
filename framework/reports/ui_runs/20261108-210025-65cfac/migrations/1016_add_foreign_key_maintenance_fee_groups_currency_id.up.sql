-- Step M1016: Add foreign key maintenance_fee_groups (currency_id) -> currencies
-- Direction: up
-- Findings: SCH-002-1e7aeb09
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: high.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: No orphan rows in maintenance_fee_groups (currency_id) referencing currencies (FK would fail)
-- Precheck: Table maintenance_fee_groups exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'maintenance_fee_groups' AND table_schema = DATABASE()
-- Precheck: Table currencies exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'currencies' AND table_schema = DATABASE()
-- Precheck: No orphan rows in maintenance_fee_groups (currency_id) referencing currencies (FK would fail). Expect 0: SELECT COUNT(*) FROM `maintenance_fee_groups` c LEFT JOIN `currencies` p ON c.`currency_id` = p.`id` WHERE c.`currency_id` IS NOT NULL AND p.`id` IS NULL
-- Note: MySQL only allows INPLACE when foreign_key_checks is off, which would skip validation, so COPY with LOCK=SHARED is used. It blocks writes while running; schedule accordingly.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `maintenance_fee_groups` ADD CONSTRAINT `fk_maintenance_fee_groups_currency_id` FOREIGN KEY (`currency_id`) REFERENCES `currencies` (`id`), ALGORITHM=COPY, LOCK=SHARED;
