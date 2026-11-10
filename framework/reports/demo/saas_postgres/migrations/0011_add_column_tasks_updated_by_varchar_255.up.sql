-- Step M011: Add column tasks.updated_by varchar(255)
-- Direction: up
-- Findings: SCH-044-24ac9296
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Table public.tasks exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'tasks' AND table_schema = 'public'
-- Precheck: Column tasks.updated_by does not exist. Expect 0: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'tasks' AND table_schema = 'public' AND column_name = 'updated_by'
-- Note: Rollback drops the column and discards any values written to it after the change.
-- Note: On PostgreSQL 11 and later a constant default does not rewrite the table; the brief ACCESS EXCLUSIVE lock is bounded by lock_timeout.
SET lock_timeout = '5s';
ALTER TABLE "public"."tasks" ADD COLUMN "updated_by" varchar(255);
