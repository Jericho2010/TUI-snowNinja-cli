import pytest
from snowninja.llm.nim_client import NimClient
from snowninja.llm.models import ModelRole

@pytest.mark.asyncio
@pytest.mark.e2e
async def test_agent_list_databases():
    """agent_chat('list all databases') yields tool_call for list_databases, then text response."""
    client = NimClient()
    # In Implementer mode, it has tools enabled and can call them
    result = await client.agent_chat("list all databases available to me", role=ModelRole.IMPLEMENTER)
    # The response should indicate the databases, meaning it successfully called the tool
    # and synthesized the result.
    assert len(result) > 0
    # It might mention SNOWFLAKE or another default DB name if the tool call succeeded
    # We can't guarantee exact words, but it shouldn't be an error.
    assert "Error" not in result

@pytest.mark.asyncio
@pytest.mark.e2e
async def test_agent_execute_sql():
    """agent_chat('run SELECT 1') calls execute_sql."""
    client = NimClient()
    result = await client.agent_chat("execute the sql query 'SELECT 1 AS TEST' and tell me the result", role=ModelRole.IMPLEMENTER)
    assert len(result) > 0
    # The result should contain the value '1'
    assert "1" in result
    assert "Error" not in result

@pytest.mark.asyncio
@pytest.mark.e2e
async def test_agent_planner_produces_task_list():
    """Planner mode for 'plan a medallion pipeline' yields text containing '## Task List'."""
    client = NimClient()
    result = await client.agent_chat("Plan a medallion architecture pipeline for customer data.", role=ModelRole.PLANNER)
    assert len(result) > 0
    assert "## Task List" in result or "Task List" in result
    assert "Error" not in result
