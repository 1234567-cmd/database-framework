"""Proposed migrations. This package writes files and runs isolated tests; it never applies a plan to a source."""
from .generator import Check, MigrationPlan, MigrationStep, generate_plan
from .safety import ApprovalRequired, backup_recommendation, detect_destructive, is_destructive, plan_hash, require_approval
from .sandbox import SandboxRefused, SandboxReport, StepResult, test_plan_in_sandbox
from .writer import write_migration_files

__all__ = ["ApprovalRequired", "Check", "MigrationPlan", "MigrationStep", "SandboxRefused", "SandboxReport", "StepResult",
           "backup_recommendation", "detect_destructive", "generate_plan", "is_destructive", "plan_hash", "require_approval",
           "test_plan_in_sandbox", "write_migration_files"]
