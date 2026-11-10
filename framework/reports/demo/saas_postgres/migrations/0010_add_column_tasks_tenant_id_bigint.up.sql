-- Step M010: Add column tasks.tenant_id bigint
-- Direction: up
-- Findings: TENA-001-2d71408c
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Table public.tasks exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'tasks' AND table_schema = 'public'
-- Precheck: Column tasks.tenant_id does not exist. Expect 0: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'tasks' AND table_schema = 'public' AND column_name = 'tenant_id'
-- Note: Rollback drops the column and discards any values written to it after the change.
-- Note: On PostgreSQL 11 and later a constant default does not rewrite the table; the brief ACCESS EXCLUSIVE lock is bounded by lock_timeout.
SET lock_timeout = '5s';
ALTER TABLE "public"."tasks" ADD COLUMN "tenant_id" bigint;
