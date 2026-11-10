-- Step M035: Set users.tenant_id NOT NULL
-- Direction: up
-- Findings: TENA-003-a7fc303f
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: No NULLs in users.tenant_id (NOT NULL would fail)
-- Precheck: Table public.users exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'users' AND table_schema = 'public'
-- Precheck: Column users.tenant_id exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'users' AND table_schema = 'public' AND column_name = 'tenant_id'
-- Precheck: No NULLs in users.tenant_id (NOT NULL would fail). Expect 0: SELECT COUNT(*) FROM "public"."users" WHERE "tenant_id" IS NULL
-- Note: PostgreSQL 12 and later use the validated CHECK to skip the full scan under ACCESS EXCLUSIVE.
SET lock_timeout = '5s';
ALTER TABLE "public"."users" ADD CONSTRAINT "nn_users_tenant_id" CHECK ("tenant_id" IS NOT NULL) NOT VALID;
ALTER TABLE "public"."users" VALIDATE CONSTRAINT "nn_users_tenant_id";
ALTER TABLE "public"."users" ALTER COLUMN "tenant_id" SET NOT NULL;
ALTER TABLE "public"."users" DROP CONSTRAINT "nn_users_tenant_id";
