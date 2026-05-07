import pytest
from snowninja.actions.tools_core import ToolsCore

@pytest.fixture(scope="module")
def tools():
    return ToolsCore()

@pytest.mark.integration
def test_get_current_user(tools):
    """Returns dict with user, role, warehouse keys."""
    res = tools.get_current_user()
    # Snowflake returns uppercase keys usually, but let's check ignoring case if possible,
    # or just check the keys exist in uppercase since our helper dict(zip(columns, row))
    # preserves the cursor description which is typically uppercase in Snowflake.
    keys = [k.lower() for k in res.keys()]
    assert "user" in keys
    assert "role" in keys
    assert "warehouse" in keys

@pytest.mark.integration
def test_get_account_info(tools):
    """Returns dict with account, region keys."""
    res = tools.get_account_info()
    keys = [k.lower() for k in res.keys()]
    assert "account" in keys
    assert "region" in keys

@pytest.mark.integration
def test_list_databases(tools):
    """Returns list of dicts, each with 'name' key."""
    res = tools.list_databases()
    assert len(res) > 0
    keys = [k.lower() for k in res[0].keys()]
    assert "name" in keys

@pytest.mark.integration
def test_list_warehouses(tools):
    """Returns list with at least one warehouse."""
    res = tools.list_warehouses()
    assert len(res) > 0
    keys = [k.lower() for k in res[0].keys()]
    assert "name" in keys

@pytest.mark.integration
def test_execute_sql(tools):
    """SELECT 1 AS test returns rows=[{'TEST': '1'}]."""
    res = tools.execute_sql("SELECT 1 AS test")
    assert len(res) == 1
    # Number types might come back as int, handle string or int comparison
    assert res[0].get("TEST") in (1, "1")

@pytest.mark.integration
def test_validate_sql(tools):
    """EXPLAIN SELECT 1 succeeds; EXPLAIN INVALID_SQL fails gracefully."""
    # Valid
    res_valid = tools.validate_sql("SELECT 1")
    assert res_valid["status"] == "valid"
    
    # Invalid
    res_invalid = tools.validate_sql("SELECT * FROM non_existent_table_12345")
    assert res_invalid["status"] == "invalid"
    assert "error" in res_invalid

@pytest.mark.integration
def test_list_roles(tools):
    """Returns list with at least ACCOUNTADMIN."""
    res = tools.list_roles()
    assert len(res) > 0
    roles = [r.get("name", r.get("NAME", "")) for r in res]
    assert "ACCOUNTADMIN" in roles
