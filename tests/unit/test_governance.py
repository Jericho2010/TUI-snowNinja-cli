import pytest
from snowninja.governance.policies import check_query_safety

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
    assert check_query_safety("CREATE WAREHOUSE my_wh WITH TAG (cost_center='sales');") is True
    assert check_query_safety("CREATE WAREHOUSE my_wh TAG (cost_center='sales');") is True

def test_policy_drop_account():
    """'DROP ACCOUNT my_acc;' returns False."""
    assert check_query_safety("DROP ACCOUNT my_acc;") is False

def test_policy_safe_query():
    """'SELECT * FROM users;' returns True."""
    assert check_query_safety("SELECT * FROM users;") is True
    assert check_query_safety("CREATE TABLE my_table (id INT);") is True
