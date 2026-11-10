-- Step M038: Enable row level security on projects by tenant_id
-- Direction: down
-- Findings: TENA-007-c6f5ed6c
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: No NULLs in projects.tenant_id (tenant isolation would fail)
-- Precheck: Table public.projects exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'projects' AND table_schema = 'public'
-- Precheck: Column projects.tenant_id exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'projects' AND table_schema = 'public' AND column_name = 'tenant_id'
-- Precheck: No NULLs in projects.tenant_id (tenant isolation would fail). Expect 0: SELECT COUNT(*) FROM "public"."projects" WHERE "tenant_id" IS NULL
-- Note: The session setting app.tenant_id is a placeholder convention; confirm how the application sets tenant context before use.
-- Note: Table owners and BYPASSRLS roles are exempt unless FORCE ROW LEVEL SECURITY is added; confirm application roles.
-- Dependency risk: Foreign key from public.tasks references projects.
-- Dependency risk: Application code, ORM mappings, reports and ETL jobs outside the database are not analyzed by the migration generator and may use this name.
SET lock_timeout = '5s';
ALTER TABLE "public"."projects" DISABLE ROW LEVEL SECURITY;
DROP POLICY "rls_projects_tenant_id" ON "public"."projects";
