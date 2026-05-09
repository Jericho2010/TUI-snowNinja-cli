import pytest
from snowninja.session import session
from snowninja.llm.nim_client import NimClient

def test_session_budget_default():
    """Session has a default max_iterations of 20."""
    assert session.max_iterations == 20

@pytest.mark.asyncio
async def test_agent_chat_respects_limit():
    """agent_chat respects the limit provided."""
    client = NimClient()
    # Mocking _resolve_model and _chat_with_retry to simulate a loop
    import unittest.mock as mock
    
    with mock.patch.object(NimClient, "_resolve_model", return_value="mock-model"):
        with mock.patch.object(NimClient, "_chat_with_retry") as mock_chat:
            # Simulate a model that always wants to call a tool
            mock_chat.return_value.choices = [
                mock.Mock(message=mock.Mock(content="thinking", tool_calls=[
                    mock.Mock(id="1", function=mock.Mock(name="get_current_user", arguments="{}"))
                ]))
            ]
            
            # Run with a small limit of 3
            results = []
            async for event_type, data in client.agent_chat("test", max_iterations=3):
                results.append((event_type, data))
            
            # Should have error after 3 iterations
            event_types = [r[0] for r in results]
            assert "error" in event_types
            
            # Find the error event
            error_event = next(r for r in results if r[0] == "error")
            assert "Exceeded maximum tool iterations (3)" in error_event[1]
            # The loop should have run exactly 3 times before error
            assert mock_chat.call_count == 3
