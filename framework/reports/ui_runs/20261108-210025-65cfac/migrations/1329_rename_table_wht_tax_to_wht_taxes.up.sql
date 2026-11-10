-- Step M1329: Rename table wht_tax to wht_taxes
-- Direction: up
-- Findings: SCH-055-cec52c31
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Table wht_tax exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'wht_tax' AND table_schema = DATABASE()
-- Note: Renaming a table breaks every reader that uses the old name. Consider a compatibility view for one release.
-- Dependency risk: Application code, ORM mappings, reports and ETL jobs outside the database are not analyzed by the migration generator and may use this name.
SET SESSION lock_wait_timeout = 5;
RENAME TABLE `wht_tax` TO `wht_taxes`;
