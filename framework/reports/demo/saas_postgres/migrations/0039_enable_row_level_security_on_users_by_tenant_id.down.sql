-- Step M039: Enable row level security on users by tenant_id
-- Direction: down
-- Findings: TENA-007-21a82e8b
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: No NULLs in users.tenant_id (tenant isolation would fail)
-- Precheck: Table public.users exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'users' AND table_schema = 'public'
-- Precheck: Column users.tenant_id exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'users' AND table_schema = 'public' AND column_name = 'tenant_id'
-- Precheck: No NULLs in users.tenant_id (tenant isolation would fail). Expect 0: SELECT COUNT(*) FROM "public"."users" WHERE "tenant_id" IS NULL
-- Note: The session setting app.tenant_id is a placeholder convention; confirm how the application sets tenant context before use.
-- Note: Table owners and BYPASSRLS roles are exempt unless FORCE ROW LEVEL SECURITY is added; confirm application roles.
-- Dependency risk: Foreign key from public.projects references users.
-- Dependency risk: Foreign key from public.tasks references users.
-- Dependency risk: Foreign key from public.comments references users.
-- Dependency risk: Application code, ORM mappings, reports and ETL jobs outside the database are not analyzed by the migration generator and may use this name.
SET lock_timeout = '5s';
ALTER TABLE "public"."users" DISABLE ROW LEVEL SECURITY;
DROP POLICY "rls_users_tenant_id" ON "public"."users";
