"""
tests/unit/test_connection_pool.py

Tests for the ToolsCore connection caching behaviour.
No real Snowflake connection required — uses mocks.
"""
import pytest
from unittest import mock
from snowninja.actions.tools_core import ToolsCore


def _make_mock_conn(is_closed: bool = False):
    """Build a mock Snowflake connection."""
    conn = mock.MagicMock()
    conn.is_closed.return_value = is_closed

    cursor = mock.MagicMock()
    cursor.__enter__ = mock.Mock(return_value=cursor)
    cursor.__exit__ = mock.Mock(return_value=False)
    cursor.description = None  # no columns → triggers the "success" branch
    conn.cursor.return_value = cursor
    return conn


@mock.patch("snowninja.actions.tools_core.get_connection")
def test_connection_cached_on_second_call(mock_get_conn):
    """get_connection() is called only once when the connection stays alive."""
    conn = _make_mock_conn(is_closed=False)
    mock_get_conn.return_value = conn

    core = ToolsCore(profile=None)
    # Trigger two queries
    core._get_conn()
    core._get_conn()

    assert mock_get_conn.call_count == 1


@mock.patch("snowninja.actions.tools_core.get_connection")
def test_connection_reopened_when_closed(mock_get_conn):
    """A closed connection is discarded and a fresh one is fetched."""
    alive_conn = _make_mock_conn(is_closed=False)
    dead_conn = _make_mock_conn(is_closed=True)

    # Sequence: first call returns alive (for the initial _get_conn()),
    # but we override _conn with dead_conn after that to simulate it going dead.
    mock_get_conn.return_value = alive_conn

    core = ToolsCore(profile=None)
    # Force-inject a dead connection to simulate it going stale
    core._conn = dead_conn

    # Now calling _get_conn() should detect dead_conn.is_closed() == True
    # and call get_connection() again to get a fresh one
    result = core._get_conn()
    assert result is alive_conn
    # get_connection was called once (to get the fresh connection after detecting stale)
    assert mock_get_conn.call_count == 1


@mock.patch("snowninja.actions.tools_core.get_connection")
def test_cursor_closed_after_query(mock_get_conn):
    """The cursor (not the connection) is closed after every _execute_query call."""
    conn = _make_mock_conn(is_closed=False)
    mock_get_conn.return_value = conn

    from snowninja.governance.policies import check_query_safety
    with mock.patch("snowninja.governance.policies.check_query_safety", return_value=True):
        core = ToolsCore(profile=None)
        core._execute_query("SELECT 1")

    conn.cursor.return_value.close.assert_called_once()
    conn.close.assert_not_called()  # connection NOT closed between queries


@mock.patch("snowninja.actions.tools_core.get_connection")
def test_connection_not_closed_between_queries(mock_get_conn):
    """Connection object is reused across multiple _execute_query calls."""
    conn = _make_mock_conn(is_closed=False)
    mock_get_conn.return_value = conn

    with mock.patch("snowninja.governance.policies.check_query_safety", return_value=True):
        core = ToolsCore(profile=None)
        core._execute_query("SELECT 1")
        core._execute_query("SELECT 2")

    # Still only one connection
    assert mock_get_conn.call_count == 1
    conn.close.assert_not_called()
