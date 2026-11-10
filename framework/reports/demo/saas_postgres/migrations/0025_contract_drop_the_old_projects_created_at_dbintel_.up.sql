-- Step M025: Contract: drop the old projects.created_at__dbintel_old
-- Direction: up
-- Findings: SCH-030-85b4ef80
-- Destructive: True. Reversible: False. Data loss risk: high. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Requires a verified backup first.
-- Precheck: Column projects.created_at__dbintel_old exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'projects' AND table_schema = 'public' AND column_name = 'created_at__dbintel_old'
-- Note: Run only after the new column has been verified in production through at least one release (MIG-004).
SET lock_timeout = '5s';
ALTER TABLE "public"."projects" DROP COLUMN "created_at__dbintel_old";
