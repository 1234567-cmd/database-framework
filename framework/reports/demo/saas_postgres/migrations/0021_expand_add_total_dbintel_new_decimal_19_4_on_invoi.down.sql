-- Step M021: Expand: add total__dbintel_new decimal(19,4) on invoices and backfill
-- Direction: down
-- Findings: SCH-020-f15a2d57
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: Could not write a generic check that invoices.total converts from double precision to decimal(19,4). Verify conversion by hand before running.
-- Precheck: Table public.invoices exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'invoices' AND table_schema = 'public'
-- Precheck: Column invoices.total exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'invoices' AND table_schema = 'public' AND column_name = 'total'
-- Note: The backfill is one batch; run it repeatedly, throttled, outside any DDL transaction until it updates no rows (MIG-012).
-- Note: The application must write both columns, or a sync trigger must exist, from this step until the swap; otherwise later writes are missed and the swap precheck fails (MIG-004, MIG-016).
SET lock_timeout = '5s';
ALTER TABLE "public"."invoices" DROP COLUMN "total__dbintel_new";
