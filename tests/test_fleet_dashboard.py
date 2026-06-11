import pytest
import json
import asyncio
from fastapi.testclient import TestClient
from asta.core_engine.event_bus import EventBus, Event
from asta.interfaces.dashboard_api import app, inject_dashboard_dependencies


@pytest.fixture
def mock_dashboard_client() -> tuple[TestClient, EventBus]:
    bus = EventBus()
    inject_dashboard_dependencies(bus)
    client = TestClient(app)
    return client, bus


@pytest.mark.asyncio
async def test_dashboard_html_serve(mock_dashboard_client: tuple[TestClient, EventBus]) -> None:
    client, _ = mock_dashboard_client
    response = client.get("/")
    assert response.status_code == 200
    assert "ASTA: Enterprise Fleet Management" in response.text
    assert "WebSocket" in response.text


@pytest.mark.asyncio
async def test_websocket_telemetry_streaming(mock_dashboard_client: tuple[TestClient, EventBus]) -> None:
    """Verify that events published to the EventBus are successfully streamed down the websocket."""
    client, bus = mock_dashboard_client

    # Start the bus inside the async test to grab the proper running loop
    bus.start()

    # We use the test client's websocket context manager
    with client.websocket_connect("/ws/fleet") as websocket:

        # 1. Publish a mock Orchestrator event
        await bus.publish(Event(
            type="AGENT_SPAWNED",
            payload={"agent_id": "Agent_1", "task": "Build SaaS"}
        ))

        # We need to give the asyncio event loop a chance to process the queue
        # Since TestClient runs synchronous websockets, we use asyncio.sleep
        await asyncio.sleep(0.2)

        # Now read the websocket
        received_types = []
        # Expecting at least 1 real event before heartbeat flood
        for _ in range(10):
            data = websocket.receive_text()
            parsed = json.loads(data)
            received_types.append(parsed.get("type"))
            if parsed.get("type") == "AGENT_SPAWNED":
                assert parsed["payload"]["agent_id"] == "Agent_1"
                assert parsed["payload"]["task"] == "Build SaaS"
                break

        assert "AGENT_SPAWNED" in received_types

        # 3. Publish Agent Log and MCP Approval Event
        await bus.publish(Event(
            type="AGENT_LOG",
            payload={"agent_id": "Agent_1", "log": "Connecting to GitHub..."}
        ))

        await bus.publish(Event(
            type="AGENT_MCP_APPROVAL_REQUIRED",
            payload={"agent_id": "Agent_1", "tool": "github_read"}
        ))

        await asyncio.sleep(0.2)

        received_types.clear()
        for _ in range(10):
            data2 = websocket.receive_text()
            parsed2 = json.loads(data2)
            received_types.append(parsed2.get("type"))
            if parsed2.get("type") == "AGENT_MCP_APPROVAL_REQUIRED":
                assert parsed2["payload"]["agent_id"] == "Agent_1"
                assert parsed2["payload"]["tool"] == "github_read"
                break

        assert "AGENT_LOG" in received_types
        assert "AGENT_MCP_APPROVAL_REQUIRED" in received_types

        # 4. Simulate CEO clicking "Approve" on the frontend
        websocket.send_text(json.dumps({
            "action": "APPROVE_MCP",
            "agent_id": "Agent_1",
            "tool": "github_read"
        }))

        await asyncio.sleep(0.2)

    await bus.stop()
