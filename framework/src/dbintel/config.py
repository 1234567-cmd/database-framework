"""Run configuration. Defaults follow the owner-approved Stage 2 decisions."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import yaml


@dataclass
class Profile:
    workload: str = "OLTP"  # OLTP | OLAP | data_warehouse | lakehouse
    tenancy: str = "none"  # none | pool | bridge | silo
    tenant_column: str = "tenant_id"
    company_column: str = "company_id"
    multi_company: bool = False
    system_of_record: bool = True
    audit_columns: list[list[str]] = field(default_factory=lambda: [["created_at", "created_on"], ["updated_at", "updated_on"], ["created_by"], ["updated_by"]])
    tenant_exempt_tables: list[str] = field(default_factory=lambda: ["tenants", "countries", "currencies", "languages", "schema_migrations", "flyway_schema_history"])
    audit_exempt_tables: list[str] = field(default_factory=lambda: ["schema_migrations", "flyway_schema_history", "countries", "currencies", "languages"])
    exclude_tables: list[str] = field(default_factory=list)
    money_name_patterns: list[str] = field(default_factory=lambda: ["amount", "amt", "price", "cost", "total", "balance", "salary", "fee", "tax", "debit", "credit", "subtotal", "payment"])
    identifier_limit: int = 63
    target_engines: list[str] = field(default_factory=lambda: ["postgres", "mysql"])
    table_plural: bool = True
    data_sample_limit: int = 100000
    financial_table_patterns: list[str] = field(default_factory=list)  # regexes added to the migration safety defaults
    rules: dict[str, dict[str, Any]] = field(default_factory=dict)  # per rule: enabled, severity, kind, params

    def rule_override(self, rule_id: str) -> dict[str, Any]:
        return self.rules.get(rule_id, {})

    def is_tenant_exempt(self, table: str) -> bool:
        return table.lower() in {t.lower() for t in self.tenant_exempt_tables}

    def is_audit_exempt(self, table: str) -> bool:
        return table.lower() in {t.lower() for t in self.audit_exempt_tables}

    def is_excluded(self, table: str) -> bool:
        return table.lower() in {t.lower() for t in self.exclude_tables}

    @property
    def analytical(self) -> bool:
        return self.workload != "OLTP"


def load_profile(path: Optional[str | Path]) -> Profile:
    if not path:
        return Profile()
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    unknown = set(raw) - set(Profile.__dataclass_fields__)
    if unknown:
        raise ValueError(f"Unknown profile keys: {sorted(unknown)}")
    return Profile(**raw)
