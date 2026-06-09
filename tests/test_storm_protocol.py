import pytest
from unittest.mock import MagicMock, AsyncMock
from pathlib import Path

from asta.core_engine.graph import AstaState
from asta.core_engine.llm_gateway import LLMGateway
from asta.feature_architecture.storm_protocol import build_storm_protocol_graph

@pytest.fixture
def mock_storm_llm() -> LLMGateway:
    llm = MagicMock(spec=LLMGateway)

    # Mock behavior to handle different stages based on task_type or prompt content
    async def dynamic_completion(messages: list, task_type: str = "general") -> str:
        prompt = messages[0]["content"]

        if "outline" in prompt.lower():
            return '{"sections": ["Intro", "Body", "Conclusion"]}'
        elif "draft" in prompt.lower():
            return "This is a comprehensive academic draft with citations [1]."
        elif "review" in prompt.lower():
            # Pass on the first attempt
            return "PASS"

        return "Unknown Task"

    llm.generate_completion = AsyncMock(side_effect=dynamic_completion)
    return llm

@pytest.mark.asyncio
async def test_storm_protocol_successful_pipeline(mock_storm_llm: LLMGateway) -> None:
    """Verify the STORM protocol successfully routes through all compilation phases."""

    graph = build_storm_protocol_graph(mock_storm_llm)
    state = AstaState()
    state.m_active["research_topic"] = "Quantum Mechanics"

    final_state = await graph.execute(state, max_steps=15)

    # Assert execution completed
    assert final_state.current_node == "END"

    # Assert Outline Generation
    assert "storm_outline" in final_state.m_active
    assert len(final_state.m_active["storm_outline"]) == 3
    assert final_state.m_active["storm_outline"][0] == "Intro"

    # Assert Source Scraping
    assert "sources_Intro" in final_state.m_active
    assert "Raw scraped academic data" in final_state.m_active["sources_Intro"]

    # Assert Drafting
    assert "storm_drafts" in final_state.m_active
    assert "Intro" in final_state.m_active["storm_drafts"]
    assert "academic draft with citations" in final_state.m_active["storm_drafts"]["Intro"]

    # Assert Compilation
    assert "storm_final_pdf" in final_state.m_active
    pdf_path = final_state.m_active["storm_final_pdf"]
    assert "Quantum_Mechanics_Final_Research.pdf" in pdf_path

    # Assert PDF actually exists on disk
    assert Path(pdf_path).exists()

    # Cleanup
    Path(pdf_path).unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_storm_protocol_self_correction_loop(mock_storm_llm: LLMGateway) -> None:
    """Verify that a rejected draft correctly loops back to re-drafting."""

    # Override mock to reject on first attempt, then pass on second
    call_count = {"review": 0}

    async def dynamic_completion(messages: list, task_type: str = "general") -> str:
        prompt = messages[0]["content"]
        if "outline" in prompt.lower():
            return '{"sections": ["OnlySection"]}'
        elif "review" in prompt.lower():
            call_count["review"] += 1
            if call_count["review"] == 1:
                return "REJECT"
            return "PASS"
        elif "draft" in prompt.lower():
            return "Draft content."
        return ""

    mock_storm_llm.generate_completion = AsyncMock(side_effect=dynamic_completion) # type: ignore

    graph = build_storm_protocol_graph(mock_storm_llm)
    state = AstaState()
    state.m_active["research_topic"] = "Loop Test"

    final_state = await graph.execute(state, max_steps=10)

    assert final_state.current_node == "END"

    # Since there was 1 section, but it failed once, the review count must be 2
    assert call_count["review"] == 2
