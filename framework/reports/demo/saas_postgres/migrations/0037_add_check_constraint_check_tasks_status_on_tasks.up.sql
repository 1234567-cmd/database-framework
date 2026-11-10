-- Step M037: Add check constraint check_tasks_status on tasks
-- Direction: up
-- Findings: SCH-046-d531e8ef
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: No rows violate status IN ('done', 'open')
-- Precheck: Table public.tasks exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'tasks' AND table_schema = 'public'
-- Precheck: No rows violate status IN ('done', 'open'). Expect 0: SELECT COUNT(*) FROM "public"."tasks" WHERE NOT (status IN ('done', 'open'))
-- Note: NOT VALID then VALIDATE avoids scanning under a write-blocking lock.
SET lock_timeout = '5s';
ALTER TABLE "public"."tasks" ADD CONSTRAINT "check_tasks_status" CHECK (status IN ('done', 'open')) NOT VALID;
ALTER TABLE "public"."tasks" VALIDATE CONSTRAINT "check_tasks_status";
