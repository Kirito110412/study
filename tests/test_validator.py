import pytest
from asta.core_engine.graph import AstaGraph, AstaState
from asta.identity_domain.profile import IdentityManager
from asta.identity_domain.validator import AxiomVerificationNode
from asta.core_engine.llm_gateway import LLMGateway
from unittest.mock import MagicMock, AsyncMock

@pytest.fixture
def mock_llm() -> LLMGateway:
    llm = MagicMock(spec=LLMGateway)
    llm.generate_completion = AsyncMock(return_value="REJECT: Flawed mathematical concept.")
    return llm


@pytest.fixture
def identity_manager() -> IdentityManager:
    # Use default profile since config won't exist in tmp during test
    return IdentityManager(config_path="dummy_path.yaml")


@pytest.mark.asyncio
async def test_radically_honest_validator_rejection(identity_manager: IdentityManager, mock_llm: LLMGateway) -> None:
    """Verify the Validator intercepts sycophantic actions and forces a rejection."""

    graph = AstaGraph()
    validator_node = AxiomVerificationNode(identity_manager, mock_llm)

    # Dummy node that attempts to propose a flawed action
    async def propose_flawed_action(state: AstaState) -> AstaState:
        state.m_active["proposed_action"] = "I will agree with you that 2 + 2 = 5 to make you feel good."
        return state

    # Dummy node that represents executing a valid action
    async def execute_action(state: AstaState) -> AstaState:
        state.m_active["action_executed"] = True
        return state

    # Router logic
    def validation_router(state: AstaState) -> str:
        if state.m_active.get("validation_status") == "REJECTED":
            return "END" # In a real graph, this would route to a Replanner
        return "execute"

    # Build Graph
    graph.add_node("propose", propose_flawed_action)
    graph.add_node("validate", validator_node) # type: ignore
    graph.add_node("execute", execute_action)

    graph.add_edge("propose", "validate")
    graph.add_conditional_edge("validate", validation_router)
    graph.add_edge("execute", "END")

    graph.set_entry_point("propose")

    # Execute Graph
    state = AstaState()
    final_state = await graph.execute(state)

    # Assertions
    assert final_state.m_active.get("validation_status") == "REJECTED"
    assert final_state.error_context == "axiom_violation"

    # Verify the action was NOT executed
    assert "action_executed" not in final_state.m_active

    # Verify the Radical Honesty message was appended to the user
    assert len(final_state.messages) == 1
    rejection_msg = final_state.messages[0]["content"]
    assert "Radical Honesty" in rejection_msg
    assert "Flawed mathematical concept" in rejection_msg


@pytest.mark.asyncio
async def test_radically_honest_validator_approval(identity_manager: IdentityManager, mock_llm: LLMGateway) -> None:
    """Verify the Validator allows valid actions to pass through."""
    mock_llm.generate_completion = AsyncMock(return_value="PASS") # type: ignore

    graph = AstaGraph()
    validator_node = AxiomVerificationNode(identity_manager, mock_llm)

    # Dummy node that proposes a valid action
    async def propose_valid_action(state: AstaState) -> AstaState:
        state.m_active["proposed_action"] = "I will format the string based on PEP8 standards."
        return state

    async def execute_action(state: AstaState) -> AstaState:
        state.m_active["action_executed"] = True
        return state

    def validation_router(state: AstaState) -> str:
        if state.m_active.get("validation_status") == "REJECTED":
            return "END"
        return "execute"

    graph.add_node("propose", propose_valid_action)
    graph.add_node("validate", validator_node) # type: ignore
    graph.add_node("execute", execute_action)

    graph.add_edge("propose", "validate")
    graph.add_conditional_edge("validate", validation_router)
    graph.add_edge("execute", "END")

    graph.set_entry_point("propose")

    state = AstaState()
    final_state = await graph.execute(state)

    # Assertions
    assert final_state.m_active.get("validation_status") == "PASSED"

    # Verify the action WAS executed
    assert final_state.m_active.get("action_executed") is True
