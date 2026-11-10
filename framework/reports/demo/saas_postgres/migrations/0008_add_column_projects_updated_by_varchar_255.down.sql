-- Step M008: Add column projects.updated_by varchar(255)
-- Direction: down
-- Findings: SCH-044-5e6da280
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Table public.projects exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'projects' AND table_schema = 'public'
-- Precheck: Column projects.updated_by does not exist. Expect 0: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'projects' AND table_schema = 'public' AND column_name = 'updated_by'
-- Note: Rollback drops the column and discards any values written to it after the change.
-- Note: On PostgreSQL 11 and later a constant default does not rewrite the table; the brief ACCESS EXCLUSIVE lock is bounded by lock_timeout.
SET lock_timeout = '5s';
ALTER TABLE "public"."projects" DROP COLUMN "updated_by";
