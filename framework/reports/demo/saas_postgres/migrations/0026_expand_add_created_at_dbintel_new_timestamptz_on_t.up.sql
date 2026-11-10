-- Step M026: Expand: add created_at__dbintel_new timestamptz on tasks and backfill
-- Direction: up
-- Findings: SCH-030-c8978150
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Table public.tasks exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'tasks' AND table_schema = 'public'
-- Precheck: Column tasks.created_at exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'tasks' AND table_schema = 'public' AND column_name = 'created_at'
-- Note: The backfill is one batch; run it repeatedly, throttled, outside any DDL transaction until it updates no rows (MIG-012).
-- Note: The application must write both columns, or a sync trigger must exist, from this step until the swap; otherwise later writes are missed and the swap precheck fails (MIG-004, MIG-016).
SET lock_timeout = '5s';
ALTER TABLE "public"."tasks" ADD COLUMN "created_at__dbintel_new" timestamptz;
UPDATE "public"."tasks" SET "created_at__dbintel_new" = CAST("created_at" AS timestamptz) WHERE ("id") IN (SELECT "id" FROM "public"."tasks" WHERE "created_at__dbintel_new" IS NULL AND "created_at" IS NOT NULL LIMIT 1000);
