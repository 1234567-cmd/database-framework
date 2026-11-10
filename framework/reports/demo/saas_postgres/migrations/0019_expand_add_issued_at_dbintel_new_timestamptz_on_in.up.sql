-- Step M019: Expand: add issued_at__dbintel_new timestamptz on invoices and backfill
-- Direction: up
-- Findings: SCH-030-bbf7e5c3
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Table public.invoices exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'invoices' AND table_schema = 'public'
-- Precheck: Column invoices.issued_at exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'invoices' AND table_schema = 'public' AND column_name = 'issued_at'
-- Note: The backfill is one batch; run it repeatedly, throttled, outside any DDL transaction until it updates no rows (MIG-012).
-- Note: The application must write both columns, or a sync trigger must exist, from this step until the swap; otherwise later writes are missed and the swap precheck fails (MIG-004, MIG-016).
SET lock_timeout = '5s';
ALTER TABLE "public"."invoices" ADD COLUMN "issued_at__dbintel_new" timestamptz;
UPDATE "public"."invoices" SET "issued_at__dbintel_new" = CAST("issued_at" AS timestamptz) WHERE ("id") IN (SELECT "id" FROM "public"."invoices" WHERE "issued_at__dbintel_new" IS NULL AND "issued_at" IS NOT NULL LIMIT 1000);
