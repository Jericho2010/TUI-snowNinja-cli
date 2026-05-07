import pytest
from snowninja.llm.nim_client import NimClient
from snowninja.llm.models import ModelRole

@pytest.mark.asyncio
@pytest.mark.integration
async def test_nim_api_reachable():
    """Probe NIM API with default planner model — expect 200 response."""
    client = NimClient()
    # To just probe reachable, we do a minimal request
    # If the API key is invalid or network is down, this will throw an exception
    # which pytest will catch and fail the test.
    result = await client.agent_chat("ping", role=ModelRole.PLANNER)
    assert result is not None
    assert isinstance(result, str)
    assert len(result) > 0
    assert "Error: All models in the fallback chain failed." not in result

@pytest.mark.asyncio
@pytest.mark.integration
async def test_nim_planner_text_response():
    """Send 'ping' to planner model, get non-empty text back."""
    client = NimClient()
    result = await client.agent_chat("ping", role=ModelRole.PLANNER)
    assert len(result) > 0
