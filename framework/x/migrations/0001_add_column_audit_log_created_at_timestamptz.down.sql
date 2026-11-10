-- Step M001: Add column audit_log.created_at timestamptz
-- Direction: down
-- Findings: SCH-044-0caedc85
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Table public.audit_log exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'audit_log' AND table_schema = 'public'
-- Precheck: Column audit_log.created_at does not exist. Expect 0: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'audit_log' AND table_schema = 'public' AND column_name = 'created_at'
-- Note: Rollback drops the column and discards any values written to it after the change.
-- Note: On PostgreSQL 11 and later a constant default does not rewrite the table; the brief ACCESS EXCLUSIVE lock is bounded by lock_timeout.
SET lock_timeout = '5s';
ALTER TABLE "public"."audit_log" DROP COLUMN "created_at";
