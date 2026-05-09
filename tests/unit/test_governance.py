from snowninja.governance.policies import (
    ActionClass,
    check_query_safety,
    evaluate_query_policy,
)


def test_policy_drop_db():
    """'DROP DATABASE prod;' returns False."""
    assert check_query_safety("DROP DATABASE prod;") is False
    assert check_query_safety("drop database prod;") is False


def test_policy_untagged_warehouse():
    """'CREATE WAREHOUSE my_wh;' returns False."""
    assert check_query_safety("CREATE WAREHOUSE my_wh;") is False
    assert check_query_safety("CREATE OR REPLACE WAREHOUSE my_wh;") is False


def test_policy_tagged_warehouse():
    """'CREATE WAREHOUSE my_wh WITH TAG (cost_center='sales');' returns True."""
    assert (
        check_query_safety("CREATE WAREHOUSE my_wh WITH TAG (cost_center='sales');")
        is True
    )
    assert (
        check_query_safety("CREATE WAREHOUSE my_wh TAG (cost_center='sales');") is True
    )


def test_policy_drop_account():
    """'DROP ACCOUNT my_acc;' returns False."""
    assert check_query_safety("DROP ACCOUNT my_acc;") is False


def test_policy_safe_query():
    """'SELECT * FROM users;' returns True."""
    assert check_query_safety("SELECT * FROM users;") is True
    assert check_query_safety("CREATE TABLE my_table (id INT);") is True


def test_observe_queries_classified_as_observe():
    decision = evaluate_query_policy("SELECT * FROM users")
    assert decision.allowed is True
    assert decision.action_class is ActionClass.OBSERVE


def test_create_warehouse_tool_sql_passes_policy():
    """
    The SQL actually emitted by ToolsCore.create_warehouse (WITH TAG included)
    must pass the governance policy check.
    """
    from snowninja.actions.tools_core import _quote_id

    name = "MY_WH"
    size = "X-SMALL"
    tag = "snowninja"
    # Reconstruct the SQL the tool builds
    sql = (
        f"CREATE WAREHOUSE {_quote_id(name)} "
        f"WAREHOUSE_SIZE = '{size}' "
        f"WITH TAG (snowninja_tag = '{tag}')"
    )
    assert check_query_safety(sql) is True, (
        "create_warehouse tool SQL was blocked by governance policy — tool/policy mismatch"
    )


def test_drop_database_blocked_regardless_of_case():
    """Policy blocks DROP DATABASE in all capitalisation forms."""
    for sql in [
        "DROP DATABASE prod",
        "drop database PROD",
        "Drop Database Prod",
    ]:
        assert check_query_safety(sql) is False, f"Policy should have blocked: {sql!r}"


def test_policy_blocks_drop_share():
    decision = evaluate_query_policy("DROP SHARE partner_feed")
    assert decision.allowed is False
    assert decision.action_class is ActionClass.MUTATE_CRITICAL
    assert "DROP SHARE" in decision.reason


def test_policy_blocks_alter_table_drop_column():
    decision = evaluate_query_policy("ALTER TABLE dim_customer DROP COLUMN legacy_code")
    assert decision.allowed is False
    assert decision.action_class is ActionClass.MUTATE_CRITICAL


def test_policy_blocks_revoke_all():
    decision = evaluate_query_policy(
        "REVOKE ALL PRIVILEGES ON TABLE dim_customer FROM ROLE analyst"
    )
    assert decision.allowed is False
    assert decision.action_class is ActionClass.MUTATE_CRITICAL


def test_policy_blocks_oversized_create_warehouse():
    decision = evaluate_query_policy(
        "CREATE WAREHOUSE big_wh WAREHOUSE_SIZE = '2X-LARGE' WITH TAG (cost_center='sales')"
    )
    assert decision.allowed is False
    assert decision.action_class is ActionClass.MUTATE_CRITICAL


def test_policy_blocks_oversized_resize_warehouse():
    decision = evaluate_query_policy(
        "ALTER WAREHOUSE \"big_wh\" SET WAREHOUSE_SIZE = '3X-LARGE'"
    )
    assert decision.allowed is False
    assert decision.action_class is ActionClass.MUTATE_CRITICAL


def test_policy_allows_bounded_resize_warehouse():
    decision = evaluate_query_policy(
        "ALTER WAREHOUSE \"etl_wh\" SET WAREHOUSE_SIZE = 'X-LARGE'"
    )
    assert decision.allowed is True
    assert decision.action_class is ActionClass.MUTATE_BOUNDED
