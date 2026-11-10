-- Step M004: Add column invoices.created_at timestamptz
-- Direction: down
-- Findings: SCH-044-4be16234
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Table public.invoices exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'invoices' AND table_schema = 'public'
-- Precheck: Column invoices.created_at does not exist. Expect 0: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'invoices' AND table_schema = 'public' AND column_name = 'created_at'
-- Note: Rollback drops the column and discards any values written to it after the change.
-- Note: On PostgreSQL 11 and later a constant default does not rewrite the table; the brief ACCESS EXCLUSIVE lock is bounded by lock_timeout.
SET lock_timeout = '5s';
ALTER TABLE "public"."invoices" DROP COLUMN "created_at";
