from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List
from loguru import logger

from asta.core_engine.graph import AstaGraph, AstaState
from asta.core_engine.event_bus import EventBus, Event

app = FastAPI(title="ASTA OS Gateway API")


class ChatRequest(BaseModel):
    command: str
    source: str = "web"


class ChatResponse(BaseModel):
    status: str
    responses: List[str]
    mutated_state_keys: List[str]


# In a real deployment, these would be bound to the app state lifecycle.
# We create placeholders here that must be injected when running the server.
_GLOBAL_GRAPH: AstaGraph | None = None
_GLOBAL_EVENT_BUS: EventBus | None = None


def inject_core_engine(graph: AstaGraph, event_bus: EventBus) -> None:
    """Injects the initialized singletons into the FastAPI app."""
    global _GLOBAL_GRAPH, _GLOBAL_EVENT_BUS
    _GLOBAL_GRAPH = graph
    _GLOBAL_EVENT_BUS = event_bus


@app.post("/v1/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest) -> Dict[str, Any]:
    """
    Omni-Channel Gateway endpoint.
    Accepts incoming requests (e.g. from WhatsApp/Telegram webhooks),
    and routes them into the AstaGraph.
    """
    if _GLOBAL_GRAPH is None or _GLOBAL_EVENT_BUS is None:
        raise HTTPException(status_code=500, detail="ASTA Core Engine not initialized.")

    logger.info(f"API received command from {request.source}: '{request.command}'")

    # Broadcast reception
    await _GLOBAL_EVENT_BUS.publish(Event(
        type="USER_INPUT_RECEIVED",
        payload={"source": request.source, "command": request.command}
    ))

    # Initialize State
    state = AstaState()
    state.m_active["user_activity"] = request.command

    try:
        # Route through Graph
        final_state = await _GLOBAL_GRAPH.execute(state)

        # Extract agent text responses
        responses = [msg["content"] for msg in final_state.messages if msg.get("role") == "agent"]

        return {
            "status": "success",
            "responses": responses,
            "mutated_state_keys": list(final_state.m_active.keys())
        }

    except Exception as e:
        logger.error(f"API Graph execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
