-- Step M022: Swap: make total__dbintel_new the live invoices.total
-- Direction: up
-- Findings: SCH-020-f15a2d57
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: Backfill of total__dbintel_new is complete; total__dbintel_new matches total
-- Precheck: Backfill of total__dbintel_new is complete. Expect 0: SELECT COUNT(*) FROM "public"."invoices" WHERE "total__dbintel_new" IS NULL AND "total" IS NOT NULL
-- Precheck: total__dbintel_new matches total. Expect 0: SELECT COUNT(*) FROM "public"."invoices" WHERE CAST("total" AS decimal(19,4)) IS DISTINCT FROM "total__dbintel_new"
-- Note: The application should tolerate both types before this step and deploy between expand and swap (MIG-004).
SET lock_timeout = '5s';
ALTER TABLE "public"."invoices" RENAME COLUMN "total" TO "total__dbintel_old";
ALTER TABLE "public"."invoices" RENAME COLUMN "total__dbintel_new" TO "total";
