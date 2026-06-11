import pytest
import asyncio
import time
from asta.core_engine.graph import AstaGraph, AstaState
from asta.core_engine.orchestrator import Orchestrator

@pytest.mark.asyncio
async def test_sub_agent_concurrent_spawning() -> None:
    """
    Verify that the Orchestrator runs sub-tasks in parallel and synthesizes
    the outputs correctly.
    """

    # 1. Setup a Base Graph with mock skills
    graph = AstaGraph()

    async def mock_router_node(state: AstaState) -> AstaState:
        # A generic node that looks at the current sub_task and performs the work
        task = state.m_active.get("current_sub_task", "").lower()

        if "research" in task:
            await asyncio.sleep(0.2) # Simulate slow network research
            state.m_active["sub_task_result"] = "Quantum computing relies on superposition."
            state.messages.append({"role": "agent", "content": "Research completed."})

        elif "python" in task or "code" in task:
            await asyncio.sleep(0.3) # Simulate coding time
            state.m_active["sub_task_result"] = "def calc_gravity(m1, m2, r): return G * (m1*m2)/(r**2)"
            state.messages.append({"role": "agent", "content": "Code written."})

        return state

    graph.add_node("process", mock_router_node)
    graph.add_edge("process", "END")
    graph.set_entry_point("process")

    from asta.core_engine.event_bus import EventBus
    bus = EventBus()
    orchestrator = Orchestrator(graph, event_bus=bus)
    base_state = AstaState()

    # 2. Delegate the massive task
    main_task = "Research quantum computing and simultaneously write a Python script calculating gravity."
    sub_tasks = [
        "Research quantum computing",
        "Write a Python script calculating gravity"
    ]

    start_time = time.time()

    final_state = await orchestrator.delegate_massive_task(main_task, sub_tasks, base_state)

    end_time = time.time()
    execution_time = end_time - start_time

    # 3. Verify Concurrency
    # If they ran sequentially, time would be 0.2 + 0.3 = 0.5s minimum
    # If they ran in parallel, time should be ~0.3s (the longest task)
    assert execution_time < 0.45, f"Execution took {execution_time}s, tasks did not run in parallel!"

    # 4. Verify Synthesis
    assert "synthesized_output" in final_state.m_active
    synth_text = final_state.m_active["synthesized_output"]

    # Both Agent 1 and Agent 2 results should be in the synthesized output
    assert "Quantum computing relies on superposition." in synth_text
    assert "def calc_gravity" in synth_text

    # 5. Verify Message Tagging
    assert len(final_state.messages) == 2
    # Ensure they were tagged with the sub-agent ID
    assert any("[Agent_1]" in msg["content"] for msg in final_state.messages)
    assert any("[Agent_2]" in msg["content"] for msg in final_state.messages)
