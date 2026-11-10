-- Step M002: Add column comments.tenant_id bigint
-- Direction: down
-- Findings: TENA-001-943cd663
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Table public.comments exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'comments' AND table_schema = 'public'
-- Precheck: Column comments.tenant_id does not exist. Expect 0: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'comments' AND table_schema = 'public' AND column_name = 'tenant_id'
-- Note: Rollback drops the column and discards any values written to it after the change.
-- Note: On PostgreSQL 11 and later a constant default does not rewrite the table; the brief ACCESS EXCLUSIVE lock is bounded by lock_timeout.
SET lock_timeout = '5s';
ALTER TABLE "public"."comments" DROP COLUMN "tenant_id";
