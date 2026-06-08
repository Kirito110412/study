import pytest
from asta.core_engine.graph import AstaState, AstaGraph


@pytest.mark.asyncio
async def test_hello_world_graph() -> None:
    """Verify strict edges and state mutation in a linear graph."""
    graph = AstaGraph()

    # Define Node logic
    async def start_node(state: AstaState) -> AstaState:
        state.messages.append({"role": "system", "content": "started"})
        return state

    async def process_node(state: AstaState) -> AstaState:
        state.messages.append({"role": "agent", "content": "processed"})
        state.t_pending["task_1"] = "done"
        return state

    # Build Graph
    graph.add_node("start", start_node)
    graph.add_node("process", process_node)

    graph.add_edge("start", "process")
    graph.add_edge("process", "END")

    graph.set_entry_point("start")

    # Execute
    initial_state = AstaState()
    final_state = await graph.execute(initial_state)

    # Assertions
    assert final_state.current_node == "END"
    assert len(final_state.messages) == 2
    assert final_state.messages[0]["content"] == "started"
    assert final_state.messages[1]["content"] == "processed"
    assert final_state.t_pending["task_1"] == "done"


@pytest.mark.asyncio
async def test_conditional_edges() -> None:
    """Verify conditional edges route correctly based on state variables."""
    graph = AstaGraph()

    async def evaluate_node(state: AstaState) -> AstaState:
        # Simulate logic that determines an error occurred
        if state.m_active.get("input") == "bad_input":
            state.error_context = "invalid_data"
        return state

    async def error_node(state: AstaState) -> AstaState:
        state.m_active["fixed"] = True
        return state

    async def success_node(state: AstaState) -> AstaState:
        state.m_active["success"] = True
        return state

    # Routing Function
    def error_router(state: AstaState) -> str:
        if state.error_context:
            return "error_handler"
        return "success_handler"

    # Build Graph
    graph.add_node("eval", evaluate_node)
    graph.add_node("error_handler", error_node)
    graph.add_node("success_handler", success_node)

    graph.add_conditional_edge("eval", error_router)
    graph.add_edge("error_handler", "END")
    graph.add_edge("success_handler", "END")

    graph.set_entry_point("eval")

    # Test Error Route
    bad_state = AstaState(m_active={"input": "bad_input"})
    final_bad_state = await graph.execute(bad_state)
    assert final_bad_state.m_active.get("fixed") is True

    # Test Success Route
    good_state = AstaState(m_active={"input": "good_input"})
    final_good_state = await graph.execute(good_state)
    assert final_good_state.m_active.get("success") is True
