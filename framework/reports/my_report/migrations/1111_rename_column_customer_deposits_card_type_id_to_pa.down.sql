-- Step M1111: Rename column customer_deposits.card_type_id to pay_card_type_id
-- Direction: down
-- Findings: SCH-058-7e00035f
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Column customer_deposits.card_type_id exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'customer_deposits' AND table_schema = DATABASE() AND column_name = 'card_type_id'
-- Precheck: Column customer_deposits.pay_card_type_id does not exist. Expect 0: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'customer_deposits' AND table_schema = DATABASE() AND column_name = 'pay_card_type_id'
-- Note: Renames break every reader that uses the old name. On live systems add a compatible column and migrate callers first (MIG-004).
-- Note: RENAME COLUMN needs MySQL 8.0 or later; earlier versions need CHANGE with the full column definition.
-- Dependency risk: Application code, ORM mappings, reports and ETL jobs outside the database are not analyzed by the migration generator and may use this name.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `customer_deposits` RENAME COLUMN `pay_card_type_id` TO `card_type_id`, ALGORITHM=INPLACE, LOCK=NONE;
