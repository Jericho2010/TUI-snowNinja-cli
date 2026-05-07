import pytest
from snowninja.core.connections import test_connection, list_profiles, CONNECTIONS_FILE

@pytest.mark.integration
def test_live_connection():
    """test_connection(profile) returns account, user, role from live Snowflake."""
    result = test_connection()
    assert result.get("status") == "success"
    assert "account" in result
    assert "user" in result
    assert "role" in result
    assert "warehouse" in result

@pytest.mark.integration
def test_list_profiles_finds_real_profile():
    """list_profiles() finds at least one profile from ~/.snowflake/connections.toml."""
    # This test might skip if the user isn't using connections.toml yet,
    # but the logic should return an empty list at worst, not fail
    if CONNECTIONS_FILE.exists():
        profiles = list_profiles()
        assert len(profiles) > 0
    else:
        pytest.skip("~/.snowflake/connections.toml does not exist")
