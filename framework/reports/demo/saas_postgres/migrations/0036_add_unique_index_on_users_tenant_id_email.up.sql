-- Step M036: Add unique index on users (tenant_id, email)
-- Direction: up
-- Findings: TENA-005-5720c9a7
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Run statements individually, outside a transaction: this step contains non-transactional DDL.
-- Requires data repair if the prechecks fail: No duplicate values in users (tenant_id, email) (UNIQUE would fail)
-- Precheck: Table public.users exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'users' AND table_schema = 'public'
-- Precheck: Column users.tenant_id exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'users' AND table_schema = 'public' AND column_name = 'tenant_id'
-- Precheck: Column users.email exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'users' AND table_schema = 'public' AND column_name = 'email'
-- Precheck: No duplicate values in users (tenant_id, email) (UNIQUE would fail). Expect 0: SELECT COUNT(*) FROM (SELECT "tenant_id", "email" FROM "public"."users" WHERE "tenant_id" IS NOT NULL AND "email" IS NOT NULL GROUP BY "tenant_id", "email" HAVING COUNT(*) > 1) d
-- Note: CREATE INDEX CONCURRENTLY must run outside a transaction. If it fails it leaves an INVALID index to drop before retrying.
SET lock_timeout = '5s';
CREATE UNIQUE INDEX CONCURRENTLY "uq_users_tenant_id_email" ON "public"."users" ("tenant_id", "email");
