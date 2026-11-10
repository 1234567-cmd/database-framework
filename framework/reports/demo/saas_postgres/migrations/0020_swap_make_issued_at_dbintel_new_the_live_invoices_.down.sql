-- Step M020: Swap: make issued_at__dbintel_new the live invoices.issued_at
-- Direction: down
-- Findings: SCH-030-bbf7e5c3
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: Backfill of issued_at__dbintel_new is complete; issued_at__dbintel_new matches issued_at
-- Precheck: Backfill of issued_at__dbintel_new is complete. Expect 0: SELECT COUNT(*) FROM "public"."invoices" WHERE "issued_at__dbintel_new" IS NULL AND "issued_at" IS NOT NULL
-- Precheck: issued_at__dbintel_new matches issued_at. Expect 0: SELECT COUNT(*) FROM "public"."invoices" WHERE CAST("issued_at" AS timestamptz) IS DISTINCT FROM "issued_at__dbintel_new"
-- Note: The application should tolerate both types before this step and deploy between expand and swap (MIG-004).
SET lock_timeout = '5s';
ALTER TABLE "public"."invoices" RENAME COLUMN "issued_at" TO "issued_at__dbintel_new";
ALTER TABLE "public"."invoices" RENAME COLUMN "issued_at__dbintel_old" TO "issued_at";
