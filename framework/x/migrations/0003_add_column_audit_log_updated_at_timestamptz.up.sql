-- Step M003: Add column audit_log.updated_at timestamptz
-- Direction: up
-- Findings: SCH-044-79f1bf6e
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Table public.audit_log exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'audit_log' AND table_schema = 'public'
-- Precheck: Column audit_log.updated_at does not exist. Expect 0: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'audit_log' AND table_schema = 'public' AND column_name = 'updated_at'
-- Note: Rollback drops the column and discards any values written to it after the change.
-- Note: On PostgreSQL 11 and later a constant default does not rewrite the table; the brief ACCESS EXCLUSIVE lock is bounded by lock_timeout.
SET lock_timeout = '5s';
ALTER TABLE "public"."audit_log" ADD COLUMN "updated_at" timestamptz DEFAULT CURRENT_TIMESTAMP;
