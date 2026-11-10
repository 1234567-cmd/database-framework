"""The command line: exit codes, reports, rules, standards, sandbox approval and profile scaffolding."""
import json
import re
from pathlib import Path

import pytest
import yaml

from dbintel import cli
from dbintel.cli import EXIT_FAIL_ON, EXIT_OK, EXIT_USAGE, main

SAMPLES = Path(__file__).resolve().parent.parent / "samples"
CLEAN = str(SAMPLES / "clean_postgres.sql")
ERP = str(SAMPLES / "erp_mysql.sql")


def run(*args):
    return main(list(args))


def test_assess_writes_reports_and_prints_plan_hash(tmp_path, capsys):
    out = tmp_path / "r"
    assert run("assess", CLEAN, "--profile", str(SAMPLES / "profiles" / "clean.yaml"), "--out", str(out)) == EXIT_OK
    stdout = capsys.readouterr().out
    assert re.search(r"Plan hash \(approval token for migrate test\): [0-9a-f]{64}", stdout)
    assert (out / "report.html").is_file() and (out / "report.md").is_file() and (out / "report.json").is_file() and (out / "migrations" / "README.md").is_file()


def test_assess_format_selection(tmp_path, capsys):
    out = tmp_path / "r"
    assert run("assess", CLEAN, "--out", str(out), "--format", "json") == EXIT_OK
    assert (out / "report.json").is_file() and not (out / "report.html").exists()


@pytest.mark.parametrize("severity,code", [("critical", EXIT_FAIL_ON), ("informational", EXIT_FAIL_ON)])
def test_fail_on_gives_nonzero_for_erp(tmp_path, capsys, severity, code):
    assert run("assess", ERP, "--profile", str(SAMPLES / "profiles" / "erp.yaml"), "--out", str(tmp_path / "x"), "--fail-on", severity) == code
    assert "FAIL" in capsys.readouterr().err


def test_fail_on_passes_for_clean_at_high(tmp_path, capsys):
    assert run("assess", CLEAN, "--profile", str(SAMPLES / "profiles" / "clean.yaml"), "--out", str(tmp_path / "x"), "--fail-on", "high") == EXIT_OK
    capsys.readouterr()


def test_fail_kind_limits_the_gate(tmp_path, capsys):
    clean_profile = str(SAMPLES / "profiles" / "clean.yaml")
    assert run("assess", CLEAN, "--profile", clean_profile, "--out", str(tmp_path / "x"), "--fail-on", "low") == EXIT_FAIL_ON
    assert run("assess", CLEAN, "--profile", clean_profile, "--out", str(tmp_path / "y"), "--fail-on", "low", "--fail-kind", "confirmed_defect") == EXIT_OK
    capsys.readouterr()


def test_missing_source_is_an_error_not_a_traceback(tmp_path, capsys):
    assert run("assess", str(tmp_path / "nope.sql"), "--out", str(tmp_path / "x")) == cli.EXIT_ERROR
    assert "no such file" in capsys.readouterr().err


def test_no_password_argument_exists(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["assess", CLEAN, "--out", "x", "--password", "secret"])
    assert exc.value.code == EXIT_USAGE
    capsys.readouterr()
    help_text = cli.build_parser().format_help()
    assert "--password " not in help_text


def test_password_env_is_only_a_variable_name():
    parser = cli.build_parser()
    args = parser.parse_args(["assess", CLEAN, "--out", "x", "--password-env", "DB_PW"])
    assert args.password_env == "DB_PW"


def test_rules_list_and_filters(capsys):
    assert run("rules", "list") == EXIT_OK
    assert "131 rules" in capsys.readouterr().out
    assert run("rules", "list", "--severity", "critical", "--json") == EXIT_OK
    rows = json.loads(capsys.readouterr().out)
    assert rows and all(r["severity"] == "critical" for r in rows)


def test_rules_show(capsys):
    assert run("rules", "show", "sch-020") == EXIT_OK
    out = capsys.readouterr().out
    assert "SCH-020" in out and "standards_detail:" in out
    assert run("rules", "show", "NOPE") == cli.EXIT_ERROR
    capsys.readouterr()


def test_standards_coverage_counts_add_up(capsys):
    assert run("standards", "coverage", "--json") == EXIT_OK
    data = json.loads(capsys.readouterr().out)
    assert data["total_active_or_provisional"] == 517
    assert data["executable"] + data["manual_review"] + data["out_of_scope"] == 517
    assert len(data["executable_map"]) == data["executable"]
    assert run("standards", "coverage") == EXIT_OK
    assert "Active or provisional standards: 517" in capsys.readouterr().out


def plan_hash_from(tmp_path, capsys, *assess_args):
    out = tmp_path / "plan"
    assert run("assess", *assess_args, "--out", str(out)) == EXIT_OK
    m = re.search(r"migrate test\): ([0-9a-f]{64})", capsys.readouterr().out)
    return m.group(1)


def test_migrate_test_requires_approve_flag(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["migrate", "test", CLEAN])
    assert exc.value.code == EXIT_USAGE
    assert "--approve" in capsys.readouterr().err


def test_migrate_test_rejects_a_wrong_token(capsys):
    assert run("migrate", "test", CLEAN, "--approve", "deadbeef") == EXIT_USAGE
    assert "Refused" in capsys.readouterr().err


def test_migrate_test_runs_with_the_printed_token(tmp_path, capsys):
    args = [CLEAN, "--profile", str(SAMPLES / "profiles" / "clean.yaml")]
    token = plan_hash_from(tmp_path, capsys, *args)
    code = run("migrate", "test", *args, "--approve", token, "--json")
    out = capsys.readouterr().out
    assert code == EXIT_OK and json.loads(out)["plan_hash"] == token


def test_migrate_test_token_depends_on_inputs(tmp_path, capsys):
    plain = [ERP, "--profile", str(SAMPLES / "profiles" / "erp.yaml")]
    other = [*plain, "--target-dialect", "postgres"]
    assert plan_hash_from(tmp_path, capsys, *plain) != plan_hash_from(tmp_path, capsys, *other)


def test_migrate_test_scratch_url_needs_allow_host_and_prefix(tmp_path, capsys):
    token = plan_hash_from(tmp_path, capsys, CLEAN)
    assert run("migrate", "test", CLEAN, "--approve", token, "--scratch-url", "postgresql://u@db.example/dbintel_sandbox_x") == EXIT_USAGE
    assert run("migrate", "test", CLEAN, "--approve", token, "--scratch-url", "postgresql://u@127.0.0.1/production", "--allow-host", "127.0.0.1") == EXIT_USAGE
    assert "Refused" in capsys.readouterr().err


def test_no_apply_command_exists():
    choices = cli.build_parser()._subparsers._group_actions[0].choices
    assert set(choices) == {"assess", "rules", "standards", "migrate", "init-profile", "ui"}
    migrate_cmds = choices["migrate"]._subparsers._group_actions[0].choices
    assert set(migrate_cmds) == {"test"}


def test_init_profile_writes_a_loadable_profile_and_refuses_overwrite(tmp_path, capsys):
    from dbintel.config import load_profile
    path = tmp_path / "p" / "profile.yaml"
    assert run("init-profile", str(path)) == EXIT_OK
    assert load_profile(path).workload == "OLTP"
    assert run("init-profile", str(path)) == cli.EXIT_ERROR
    assert run("init-profile", str(path), "--force") == EXIT_OK
    assert yaml.safe_load(path.read_text(encoding="utf-8"))["rules"]["SCH-047"]["enabled"] is False
    capsys.readouterr()


def test_profile_financial_table_patterns_are_honored(tmp_path):
    from dbintel.config import load_profile
    path = tmp_path / "p.yaml"
    path.write_text("financial_table_patterns: ['^revenue']\n", encoding="utf-8")
    profile = load_profile(path)
    assert profile.financial_table_patterns == ["^revenue"]
    from dbintel.migrate.safety import financial_patterns_from, is_financial_table
    assert is_financial_table("revenue_2025", financial_patterns_from(profile))


def test_migrate_module_fallback_for_financial_patterns_still_works():
    from types import SimpleNamespace

    from dbintel.migrate.safety import financial_patterns_from
    profile = SimpleNamespace(rules={"migration.financial": {"patterns": ["^bank"]}})
    assert "^bank" in financial_patterns_from(profile)


def test_main_module_runs(capsys):
    from dbintel.cli import build_parser
    with pytest.raises(SystemExit):
        build_parser().parse_args(["--version"])
    assert "dbintel" in capsys.readouterr().out


def test_rules_doc_is_current():
    import sys
    sys.path.insert(0, str(SAMPLES.parent / "scripts"))
    try:
        import generate_rules_doc
    finally:
        sys.path.pop(0)
    assert (SAMPLES.parent / "docs" / "RULES.md").read_text(encoding="utf-8") == generate_rules_doc.render(), "regenerate docs/RULES.md"
