-- Step M040: Rename column comments.author_id to user_id
-- Direction: up
-- Findings: SCH-058-e7dee54b
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Column comments.author_id exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'comments' AND table_schema = 'public' AND column_name = 'author_id'
-- Precheck: Column comments.user_id does not exist. Expect 0: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'comments' AND table_schema = 'public' AND column_name = 'user_id'
-- Note: Renames break every reader that uses the old name. On live systems add a compatible column and migrate callers first (MIG-004).
-- Dependency risk: Application code, ORM mappings, reports and ETL jobs outside the database are not analyzed by the migration generator and may use this name.
SET lock_timeout = '5s';
ALTER TABLE "public"."comments" RENAME COLUMN "author_id" TO "user_id";
