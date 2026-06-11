import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from loguru import logger
import json

from asta.core_engine.event_bus import EventBus, Event

app = FastAPI(title="ASTA Fleet Management Dashboard")

# Global reference
_GLOBAL_EVENT_BUS: EventBus | None = None

def inject_dashboard_dependencies(event_bus: EventBus) -> None:
    global _GLOBAL_EVENT_BUS
    _GLOBAL_EVENT_BUS = event_bus


# A highly lightweight vanilla JS client to visualize the Fleet Orchestration
DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
    <head>
        <title>ASTA Fleet Dashboard</title>
        <style>
            body { font-family: monospace; background: #1e1e1e; color: #00ff00; padding: 20px; }
            h1 { color: #fff; }
            .agent-box { border: 1px solid #00ff00; padding: 10px; margin-bottom: 10px; }
            .agent-title { font-weight: bold; color: #ff00ff; }
            .status-running { color: #ffff00; }
            .status-success { color: #00ffff; }
            .status-failed { color: #ff0000; }
            .terminal-log { background: #000; padding: 5px; margin-top: 5px; font-size: 12px; max-height: 100px; overflow-y: auto; color: #ddd; }
            .approval-btn { background: #ff00ff; color: #000; border: none; padding: 5px 10px; cursor: pointer; margin-right: 10px; font-weight: bold; }
        </style>
    </head>
    <body>
        <h1>ASTA: Enterprise Fleet Management</h1>
        <div id="fleet"></div>
        <script>
            // MVP Frontend Architecture
            // Uses standard WebSockets to communicate with FastAPI Gateway
            var ws = new WebSocket("ws://" + window.location.host + "/ws/fleet");

            function approveAction(agentId, tool) {
                // Send approval payload back to the backend
                var payload = {
                    action: "APPROVE_MCP",
                    agent_id: agentId,
                    tool: tool
                };
                ws.send(JSON.stringify(payload));
                document.getElementById('approval-' + agentId).innerHTML = "<span class='status-success'>[MCP APPROVED]</span>";
            }

            ws.onmessage = function(event) {
                var data = JSON.parse(event.data);
                var fleetDiv = document.getElementById('fleet');

                if (data.type === 'AGENT_SPAWNED') {
                    var box = document.createElement('div');
                    box.className = 'agent-box';
                    box.id = data.payload.agent_id;
                    box.innerHTML = "<span class='agent-title'>" + data.payload.agent_id + "</span>: " +
                                    data.payload.task + " <br/><span class='status-running' id='status-" + data.payload.agent_id + "'>[RUNNING]</span>" +
                                    "<div class='terminal-log' id='log-" + data.payload.agent_id + "'></div>" +
                                    "<div id='approval-" + data.payload.agent_id + "'></div>";
                    fleetDiv.appendChild(box);
                }
                else if (data.type === 'AGENT_LOG') {
                    var logDiv = document.getElementById('log-' + data.payload.agent_id);
                    if (logDiv) {
                        logDiv.innerHTML += "> " + data.payload.log + "<br/>";
                        logDiv.scrollTop = logDiv.scrollHeight;
                    }
                }
                else if (data.type === 'AGENT_MCP_APPROVAL_REQUIRED') {
                    var appDiv = document.getElementById('approval-' + data.payload.agent_id);
                    if (appDiv) {
                        var btn = "<button class='approval-btn' onclick='approveAction(\\"" + data.payload.agent_id + "\\", \\"" + data.payload.tool + "\\")'>AUTHORIZE: " + data.payload.tool + "</button>";
                        appDiv.innerHTML = btn;
                    }
                }
                else if (data.type === 'AGENT_COMPLETED') {
                    var statusSpan = document.getElementById('status-' + data.payload.agent_id);
                    if (statusSpan) {
                        if (data.payload.status === 'success') {
                            statusSpan.className = 'status-success';
                            statusSpan.innerHTML = "[COMPLETED]";
                        } else {
                            statusSpan.className = 'status-failed';
                            statusSpan.innerHTML = "[FAILED: " + data.payload.error + "]";
                        }
                    }
                }
            };
        </script>
    </body>
</html>
"""

@app.get("/")
async def get_dashboard() -> HTMLResponse:
    """Serve the MVP Fleet Dashboard UI."""
    return HTMLResponse(DASHBOARD_HTML)


@app.websocket("/ws/fleet")
async def websocket_fleet_endpoint(websocket: WebSocket) -> None:
    """Streams Orchestrator telemetry to the dashboard client."""
    await websocket.accept()
    logger.info("Dashboard client connected to telemetry stream.")

    if _GLOBAL_EVENT_BUS is None:
        await websocket.close(code=1011)
        return

    # Create an async queue specific to this websocket connection
    client_queue: asyncio.Queue[Event] = asyncio.Queue()

    async def _telemetry_handler(event: Event) -> None:
        # We can't await put() safely inside the background event processor
        # Instead, we just put_nowait and log
        try:
            client_queue.put_nowait(event)
        except Exception as e:
            logger.error(f"Failed to queue telemetry event: {e}")

    # Subscribe to Orchestrator events
    _GLOBAL_EVENT_BUS.subscribe("AGENT_SPAWNED", _telemetry_handler)
    _GLOBAL_EVENT_BUS.subscribe("AGENT_COMPLETED", _telemetry_handler)
    _GLOBAL_EVENT_BUS.subscribe("AGENT_LOG", _telemetry_handler)
    _GLOBAL_EVENT_BUS.subscribe("AGENT_MCP_APPROVAL_REQUIRED", _telemetry_handler)

    # Listen for approval messages from the client
    async def listen_for_approvals() -> None:
        try:
            while True:
                data = await websocket.receive_text()
                payload = json.loads(data)
                if payload.get("action") == "APPROVE_MCP":
                    # Broadcast the approval back out to the internal systems
                    if _GLOBAL_EVENT_BUS:
                        await _GLOBAL_EVENT_BUS.publish(Event(
                            type="MCP_APPROVAL_GRANTED",
                            payload={"agent_id": payload.get("agent_id"), "tool": payload.get("tool")}
                        ))
        except WebSocketDisconnect:
            pass

    # Run the listener concurrently
    approval_task = asyncio.create_task(listen_for_approvals())

    try:
        while True:
            # Wait for events from the bus or websocket disconnection
            try:
                # We add a small timeout so we can check if the client disconnected
                # TestClient websocket_connect blocks cleanly but we need to poll
                event = await asyncio.wait_for(client_queue.get(), timeout=0.1)

                # Send to websocket client
                payload = {
                    "type": event.type,
                    "payload": event.payload,
                    "timestamp": event.timestamp
                }
                await websocket.send_text(json.dumps(payload))

            except asyncio.TimeoutError:
                # Keep alive check
                await websocket.send_text(json.dumps({"type": "HEARTBEAT"}))

            # Yield control back to loop to process incoming socket close frames
            await asyncio.sleep(0.01)

    except WebSocketDisconnect:
        logger.info("Dashboard client disconnected.")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        # Cleanup
        approval_task.cancel()
        if _GLOBAL_EVENT_BUS:
            _GLOBAL_EVENT_BUS.unsubscribe("AGENT_SPAWNED", _telemetry_handler)
            _GLOBAL_EVENT_BUS.unsubscribe("AGENT_COMPLETED", _telemetry_handler)
            _GLOBAL_EVENT_BUS.unsubscribe("AGENT_LOG", _telemetry_handler)
            _GLOBAL_EVENT_BUS.unsubscribe("AGENT_MCP_APPROVAL_REQUIRED", _telemetry_handler)
