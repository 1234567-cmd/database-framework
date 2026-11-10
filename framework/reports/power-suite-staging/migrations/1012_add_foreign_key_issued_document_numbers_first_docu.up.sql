-- Step M1012: Add foreign key issued_document_numbers (first_document_id) -> documents
-- Direction: up
-- Findings: SCH-002-572e3695
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: high.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: No orphan rows in issued_document_numbers (first_document_id) referencing documents (FK would fail)
-- Precheck: Table issued_document_numbers exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'issued_document_numbers' AND table_schema = DATABASE()
-- Precheck: Table documents exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'documents' AND table_schema = DATABASE()
-- Precheck: No orphan rows in issued_document_numbers (first_document_id) referencing documents (FK would fail). Expect 0: SELECT COUNT(*) FROM `issued_document_numbers` c LEFT JOIN `documents` p ON c.`first_document_id` = p.`id` WHERE c.`first_document_id` IS NOT NULL AND p.`id` IS NULL
-- Note: MySQL only allows INPLACE when foreign_key_checks is off, which would skip validation, so COPY with LOCK=SHARED is used. It blocks writes while running; schedule accordingly.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `issued_document_numbers` ADD CONSTRAINT `fk_issued_document_numbers_first_document_id` FOREIGN KEY (`first_document_id`) REFERENCES `documents` (`id`), ALGORITHM=COPY, LOCK=SHARED;
