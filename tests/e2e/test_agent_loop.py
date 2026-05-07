import pytest
from snowninja.llm.nim_client import NimClient
from snowninja.llm.models import ModelRole

async def _gather_text(client_gen):
    """Helper to collect all 'text' events from the agent_chat generator."""
    text_parts = []
    async for event_type, data in client_gen:
        if event_type == "text":
            text_parts.append(data)
    return "".join(text_parts)

@pytest.mark.asyncio
@pytest.mark.e2e
async def test_agent_list_databases():
    """agent_chat('list all databases') yields tool_call for list_databases, then text response."""
    client = NimClient()
    gen = client.agent_chat("list all databases available to me", role=ModelRole.IMPLEMENTER)
    result = await _gather_text(gen)
    assert len(result) > 0
    assert "Error" not in result

@pytest.mark.asyncio
@pytest.mark.e2e
async def test_agent_execute_sql():
    """agent_chat('run SELECT 1') calls execute_sql."""
    client = NimClient()
    gen = client.agent_chat("execute the sql query 'SELECT 1 AS TEST' and tell me the result", role=ModelRole.IMPLEMENTER)
    result = await _gather_text(gen)
    assert len(result) > 0
    assert "1" in result
    assert "Error" not in result

@pytest.mark.asyncio
@pytest.mark.e2e
async def test_agent_planner_produces_task_list():
    """Planner mode for 'plan a medallion pipeline' yields text containing '## Task List'."""
    client = NimClient()
    gen = client.agent_chat("Plan a medallion architecture pipeline for customer data.", role=ModelRole.PLANNER)
    result = await _gather_text(gen)
    assert len(result) > 0
    assert "Task List" in result
    assert "Error" not in result
