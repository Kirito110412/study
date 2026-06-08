import pytest
from unittest.mock import AsyncMock
from fastapi.testclient import TestClient

from asta.core_engine.graph import AstaGraph, AstaState
from asta.core_engine.event_bus import EventBus
from asta.interfaces.cli import CLIGateway
from asta.interfaces.web_api import app, inject_core_engine


@pytest.fixture
def mock_engine() -> tuple[AstaGraph, EventBus]:
    # Mock EventBus
    bus = EventBus()
    bus.publish = AsyncMock()  # type: ignore

    # Mock Graph
    graph = AstaGraph()
    # Create a dummy execute that just appends a response
    async def dummy_execute(state: AstaState, max_steps: int = 50) -> AstaState:
        state.messages.append({"role": "agent", "content": "Acknowledged: " + state.m_active.get("user_activity", "")})
        state.m_active["processed"] = True
        return state

    graph.execute = AsyncMock(side_effect=dummy_execute) # type: ignore

    return graph, bus


@pytest.mark.asyncio
async def test_cli_command_processing(mock_engine: tuple[AstaGraph, EventBus]) -> None:
    """Verify that CLI input correctly constructs the state and calls the graph."""
    graph, bus = mock_engine
    cli = CLIGateway(graph, bus)

    # Send a command to the processor
    await cli.process_command("launch protocol alpha")

    # Verify EventBus publish was called
    bus.publish.assert_called_once() # type: ignore

    # Verify Graph execute was called
    graph.execute.assert_called_once() # type: ignore

    # Grab the state that was passed to execute
    call_args = graph.execute.call_args # type: ignore
    state_arg = call_args[0][0]

    assert isinstance(state_arg, AstaState)
    assert state_arg.m_active["user_activity"] == "launch protocol alpha"


def test_web_api_endpoint(mock_engine: tuple[AstaGraph, EventBus]) -> None:
    """Verify the FastAPI endpoint correctly wraps the request and returns mutated state keys."""
    graph, bus = mock_engine

    # Inject our mocks into the FastAPI global state
    inject_core_engine(graph, bus)

    client = TestClient(app)

    # Send HTTP request
    payload = {
        "command": "analyze data metrics",
        "source": "telegram"
    }
    response = client.post("/v1/chat", json=payload)

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "success"
    assert "Acknowledged: analyze data metrics" in data["responses"][0]
    assert "processed" in data["mutated_state_keys"]
