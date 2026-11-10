"""Command line interface. No command applies a migration to a source database."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Optional, Sequence

import yaml

from . import __version__
from .findings import CATEGORIES, FindingKind, Severity
from .migrate.safety import ApprovalRequired
from .migrate.sandbox import SandboxRefused, test_plan_in_sandbox
from .pipeline import Assessment, assess
from .reporting import DEFAULT_FORMATS, FORMATS, write_reports
from .rules.engine import RuleEngine, load_catalog, load_standards

EXIT_OK = 0
EXIT_ERROR = 1
EXIT_USAGE = 2
EXIT_FAIL_ON = 3
EXIT_SANDBOX_FAILED = 4
_SEVERITY_NAMES = [s.value for s in Severity]
_PROFILE_TEMPLATE = {
    "workload": "OLTP",
    "tenancy": "none",
    "tenant_column": "tenant_id",
    "company_column": "company_id",
    "multi_company": False,
    "system_of_record": True,
    "target_engines": ["postgres", "mysql"],
    "financial_table_patterns": [],
    "exclude_tables": [],
    "rules": {"SCH-047": {"enabled": False}, "GVN-002": {"severity": "informational"}},
}


class _Parser(argparse.ArgumentParser):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        kwargs.setdefault("allow_abbrev", False)  # so that --password cannot be accepted as a shortening of --password-env
        super().__init__(*args, **kwargs)

    def error(self, message: str) -> None:
        self.print_usage(sys.stderr)
        self.exit(EXIT_USAGE, f"{self.prog}: error: {message}\n")


def _add_source_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("source", help="connection URL, or a path to a dump, SQLite, CSV, Excel, JSON metadata file or CSV directory")
    parser.add_argument("--profile", help="profile YAML file")
    parser.add_argument("--dialect", help="dump dialect: postgres, mysql or sqlite (default: detected)")
    parser.add_argument("--name", help="database name to report")
    parser.add_argument("--password-env", help="name of the environment variable holding the password")
    parser.add_argument("--query-log", action="append", help="query log file (repeatable)")
    parser.add_argument("--pipelines", action="append", help="pipeline manifest YAML (repeatable)")
    parser.add_argument("--app-source-dir", help="application source to scan for table and column references")
    parser.add_argument("--target-dialect", help="dialect for the proposed SQL: postgres, mysql or sqlite")


def build_parser() -> argparse.ArgumentParser:
    parser = _Parser(prog="dbintel", description="Assess a database and propose improvements. It never changes the source.")
    parser.add_argument("--version", action="version", version=f"dbintel {__version__}")
    sub = parser.add_subparsers(dest="command", required=True, parser_class=_Parser)

    p = sub.add_parser("assess", help="assess a database and write reports")
    _add_source_args(p)
    p.add_argument("--out", required=True, help="report output directory")
    p.add_argument("--format", action="append", choices=sorted(FORMATS), help="report format (repeatable; default: html, md and json)")
    p.add_argument("--fail-on", choices=_SEVERITY_NAMES, help=f"exit {EXIT_FAIL_ON} if a finding at or above this severity exists (for CI)")
    p.add_argument("--fail-kind", choices=[k.value for k in FindingKind], help="limit --fail-on to one kind of finding")

    rules = sub.add_parser("rules", help="inspect the rule catalog").add_subparsers(dest="rules_command", required=True, parser_class=_Parser)
    p = rules.add_parser("list", help="list rules")
    p.add_argument("--category", choices=CATEGORIES, help="only this category")
    p.add_argument("--severity", choices=_SEVERITY_NAMES, help="only this severity")
    p.add_argument("--json", action="store_true", help="print JSON")
    p = rules.add_parser("show", help="show one rule")
    p.add_argument("rule_id", help="rule id, for example SCH-001")

    standards = sub.add_parser("standards", help="inspect standards").add_subparsers(dest="standards_command", required=True, parser_class=_Parser)
    p = standards.add_parser("coverage", help="show how many active or provisional standards have an executable rule")
    p.add_argument("--json", action="store_true", help="print JSON")

    migrate = sub.add_parser("migrate", help="test proposed migrations").add_subparsers(dest="migrate_command", required=True, parser_class=_Parser)
    p = migrate.add_parser("test", help="test the plan in a sandbox; the source is only read")
    _add_source_args(p)
    p.add_argument("--approve", required=True, metavar="TOKEN", help="plan hash printed by assess")
    p.add_argument("--scratch-url", help="scratch server for the sandbox; its database name must begin with dbintel_sandbox_")
    p.add_argument("--allow-host", action="append", help="host allowed for --scratch-url (repeatable)")
    p.add_argument("--scratch-password-env", help="environment variable with the scratch server password")
    p.add_argument("--json", action="store_true", help="print the sandbox report as JSON")

    p = sub.add_parser("ui", help="open the local web interface (binds to this computer only)")
    p.add_argument("--port", type=int, default=8765, help="port on 127.0.0.1 (default: 8765)")
    p.add_argument("--no-open", action="store_true", help="do not open a browser; print the address instead")
    p.add_argument("--max-upload-mb", type=int, default=2048, help="largest accepted upload in megabytes (default: 2048)")

    p = sub.add_parser("init-profile", help="write a starter profile YAML")
    p.add_argument("path", help="file to create")
    p.add_argument("--force", action="store_true", help="overwrite an existing file")
    return parser


def _assess_args(args: argparse.Namespace) -> dict[str, Any]:
    return {"profile": args.profile, "dialect": args.dialect, "name": args.name, "password_env": args.password_env, "query_log": args.query_log,
            "pipelines": args.pipelines, "app_source_dir": args.app_source_dir, "target_dialect": args.target_dialect}


def _print_summary(a: Assessment, written: dict[str, Path]) -> None:
    health = a.health
    overall = "not assessed" if health.overall is None else f"{health.overall} ({health.grade})"
    print(f"Database: {a.db.name} ({a.db.dialect})")
    print(f"Overall health: {overall}; confidence {health.confidence:.0%}; capped: {'yes' if health.capped else 'no'}")
    print(f"Findings: {len(a.findings)}  severity={json.dumps(health.severity_distribution, sort_keys=True)}  kind={json.dumps(health.kind_distribution, sort_keys=True)}")
    print(f"Rules: {len(a.coverage.executed)} executed, {len(a.coverage.skipped)} skipped, {len(a.coverage.errors)} errors")
    print(f"Migration plan: {len(a.plan.steps)} steps ({len(a.plan.executable_steps)} SQL, {len(a.plan.manual_steps)} manual). Nothing was applied.")
    print(f"Plan hash (approval token for migrate test): {a.plan_hash}")
    for fmt, path in written.items():
        print(f"{fmt}: {path}")


def cmd_assess(args: argparse.Namespace) -> int:
    assessment = assess(args.source, **_assess_args(args))
    written = write_reports(assessment, args.out, args.format or DEFAULT_FORMATS)
    _print_summary(assessment, written)
    if args.fail_on:
        limit = Severity(args.fail_on).rank
        blocking = [f for f in assessment.findings if f.severity.rank <= limit and (not args.fail_kind or f.kind.value == args.fail_kind)]
        if blocking:
            print(f"FAIL: {len(blocking)} finding(s) at or above severity {args.fail_on}"
                  + (f" of kind {args.fail_kind}" if args.fail_kind else "") + ".", file=sys.stderr)
            return EXIT_FAIL_ON
    return EXIT_OK


def cmd_rules_list(args: argparse.Namespace) -> int:
    rules = [r for r in load_catalog() if (not args.category or r["category"] == args.category) and (not args.severity or r["severity"] == args.severity)]
    if args.json:
        print(json.dumps([{k: r[k] for k in ("id", "title", "category", "severity", "kind", "standards")} for r in rules], indent=2))
    else:
        for r in rules:
            print(f"{r['id']:<10} {r['severity']:<14} {r['kind']:<22} {r['category']:<28} {str(r['title']).strip()}")
        print(f"{len(rules)} rules")
    return EXIT_OK


def cmd_rules_show(args: argparse.Namespace) -> int:
    rule = next((r for r in load_catalog() if r["id"].upper() == args.rule_id.upper()), None)
    if rule is None:
        print(f"Unknown rule: {args.rule_id}", file=sys.stderr)
        return EXIT_ERROR
    standards = load_standards()
    print(yaml.safe_dump(rule, sort_keys=False).rstrip())
    print("standards_detail:")
    for sid in rule["standards"]:
        print(f"  {sid} [{standards[sid]['status']}]: {standards[sid]['statement']}")
    return EXIT_OK


def standards_coverage() -> dict[str, Any]:
    """Map active and provisional standards to executable rules, manual review or out of scope."""
    standards = load_standards()
    current = {sid: s for sid, s in standards.items() if s["status"] in ("active", "provisional")}
    executable: dict[str, list[str]] = {}
    for rule in load_catalog():
        for sid in rule["standards"]:
            if sid in current:
                executable.setdefault(sid, []).append(rule["id"])
    manual, out_of_scope = [], []
    for sid, s in sorted(current.items()):
        if sid in executable:
            continue
        # A standard judged by people is manual review. The other check methods need a runtime this tool does not run.
        (manual if s.get("check_method") == "manual_review" else out_of_scope).append(sid)
    return {"total_active_or_provisional": len(current), "executable": len(executable), "manual_review": len(manual), "out_of_scope": len(out_of_scope),
            "executable_map": {k: sorted(v) for k, v in sorted(executable.items())}, "manual_review_ids": manual, "out_of_scope_ids": out_of_scope}


def cmd_standards_coverage(args: argparse.Namespace) -> int:
    report = standards_coverage()
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"Active or provisional standards: {report['total_active_or_provisional']}")
        print(f"Enforced by an executable rule: {report['executable']}")
        print(f"Manual review: {report['manual_review']}")
        print(f"Out of scope for this tool: {report['out_of_scope']}")
    return EXIT_OK


def _sandbox_source(args: argparse.Namespace) -> Any:
    """Re-open the source read-only so that a sandbox built from it can copy sample rows."""
    from .importers import load_source
    return load_source(args.source, dialect=args.dialect, name=args.name, password_env=args.password_env)


def cmd_migrate_test(args: argparse.Namespace) -> int:
    assessment = assess(args.source, **_assess_args(args))
    source_db = assessment.db
    reopened = None
    if source_db.data is None:  # a live source was closed by assess
        source_db = reopened = _sandbox_source(args)
    try:
        report = test_plan_in_sandbox(source_db, assessment.plan, args.approve, scratch_url=args.scratch_url, allow_hosts=args.allow_host,
                                      password_env=args.scratch_password_env)
    finally:
        if reopened is not None and reopened.data is not None:
            reopened.data.close()
    if args.json:
        print(json.dumps(report.to_dict(), indent=2, default=str))
    else:
        print(f"Sandbox engine: {report.engine}. Overall: {report.overall}. Schema restored: {report.schema_restored} ({report.schema_restored_reason})")
        for r in report.results:
            print(f"  {r.step_id} {r.status:<13} {r.title}" + (f" - {r.reason}" if r.reason else ""))
        for w in report.warnings:
            print(f"  warning: {w}")
    return EXIT_SANDBOX_FAILED if report.overall == "failed" else EXIT_OK


def cmd_ui(args: argparse.Namespace) -> int:
    from .ui.server import run_ui

    return run_ui(port=args.port, open_browser=not args.no_open, max_upload_mb=args.max_upload_mb)


def cmd_init_profile(args: argparse.Namespace) -> int:
    target = Path(args.path)
    if target.exists() and not args.force:
        print(f"Refusing to overwrite {target}; use --force.", file=sys.stderr)
        return EXIT_ERROR
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("# dbintel profile. Every key is optional; see docs/CONFIGURATION.md.\n" + yaml.safe_dump(_PROFILE_TEMPLATE, sort_keys=False), encoding="utf-8")
    print(f"Wrote {target}")
    return EXIT_OK


_HANDLERS = {("assess",): cmd_assess, ("rules", "list"): cmd_rules_list, ("rules", "show"): cmd_rules_show,
             ("standards", "coverage"): cmd_standards_coverage, ("migrate", "test"): cmd_migrate_test, ("init-profile",): cmd_init_profile, ("ui",): cmd_ui}


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    sub = {"rules": getattr(args, "rules_command", None), "standards": getattr(args, "standards_command", None), "migrate": getattr(args, "migrate_command", None)}.get(args.command)
    key = (args.command, sub) if sub else (args.command,)
    try:
        return _HANDLERS[key](args)
    except ApprovalRequired as exc:
        print(f"Refused: {exc}", file=sys.stderr)
        return EXIT_USAGE
    except SandboxRefused as exc:
        print(f"Refused: {exc}", file=sys.stderr)
        return EXIT_USAGE
    except (FileNotFoundError, ValueError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return EXIT_ERROR
    except Exception as exc:  # ConnectorError and anything unexpected are already scrubbed of secrets by the connector
        print(f"Error: {type(exc).__name__}: {exc}", file=sys.stderr)
        return EXIT_ERROR


if __name__ == "__main__":
    sys.exit(main())
