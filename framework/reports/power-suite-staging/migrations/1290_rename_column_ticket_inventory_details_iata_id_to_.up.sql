-- Step M1290: Rename column ticket_inventory_details.iata_id to iata_maintenance_id
-- Direction: up
-- Findings: SCH-058-6fd9ec8a
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Column ticket_inventory_details.iata_id exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'ticket_inventory_details' AND table_schema = DATABASE() AND column_name = 'iata_id'
-- Precheck: Column ticket_inventory_details.iata_maintenance_id does not exist. Expect 0: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'ticket_inventory_details' AND table_schema = DATABASE() AND column_name = 'iata_maintenance_id'
-- Note: Renames break every reader that uses the old name. On live systems add a compatible column and migrate callers first (MIG-004).
-- Note: RENAME COLUMN needs MySQL 8.0 or later; earlier versions need CHANGE with the full column definition.
-- Dependency risk: Application code, ORM mappings, reports and ETL jobs outside the database are not analyzed by the migration generator and may use this name.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `ticket_inventory_details` RENAME COLUMN `iata_id` TO `iata_maintenance_id`, ALGORITHM=INPLACE, LOCK=NONE;
