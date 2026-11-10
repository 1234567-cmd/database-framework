-- Step M034: Contract: drop the old users.created_at__dbintel_old
-- Direction: up
-- Findings: SCH-030-63750fad
-- Destructive: True. Reversible: False. Data loss risk: high. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Requires a verified backup first.
-- Precheck: Column users.created_at__dbintel_old exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'users' AND table_schema = 'public' AND column_name = 'created_at__dbintel_old'
-- Note: Run only after the new column has been verified in production through at least one release (MIG-004).
SET lock_timeout = '5s';
ALTER TABLE "public"."users" DROP COLUMN "created_at__dbintel_old";
