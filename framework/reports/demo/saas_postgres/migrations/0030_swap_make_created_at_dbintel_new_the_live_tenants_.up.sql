-- Step M030: Swap: make created_at__dbintel_new the live tenants.created_at
-- Direction: up
-- Findings: SCH-030-3206b2be
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: Backfill of created_at__dbintel_new is complete; created_at__dbintel_new matches created_at
-- Precheck: Backfill of created_at__dbintel_new is complete. Expect 0: SELECT COUNT(*) FROM "public"."tenants" WHERE "created_at__dbintel_new" IS NULL AND "created_at" IS NOT NULL
-- Precheck: created_at__dbintel_new matches created_at. Expect 0: SELECT COUNT(*) FROM "public"."tenants" WHERE CAST("created_at" AS timestamptz) IS DISTINCT FROM "created_at__dbintel_new"
-- Note: The application should tolerate both types before this step and deploy between expand and swap (MIG-004).
SET lock_timeout = '5s';
ALTER TABLE "public"."tenants" RENAME COLUMN "created_at" TO "created_at__dbintel_old";
ALTER TABLE "public"."tenants" RENAME COLUMN "created_at__dbintel_new" TO "created_at";
