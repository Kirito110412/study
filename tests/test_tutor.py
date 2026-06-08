import pytest
from unittest.mock import MagicMock
from asta.core_engine.graph import AstaState
from asta.identity_domain.profile import IdentityManager
from asta.feature_architecture.tutor_skill import TutorSkill


@pytest.fixture
def identity_manager() -> IdentityManager:
    manager = IdentityManager(config_path="dummy_path.yaml")
    # Manually inject the baseline proficiencies that would normally load from YAML
    manager.profile.user_proficiencies = {
        "Python": "Expert",
        "Biochemistry": "Novice"
    }
    return manager


@pytest.mark.asyncio
async def test_adaptive_socratic_tutor_expert(identity_manager: IdentityManager) -> None:
    """Verify the TutorSkill outputs a technical challenge for 'Expert' topics."""
    tutor_skill = TutorSkill(identity_manager)

    state = AstaState()
    state.m_active["user_activity"] = "Write a Python script for binary trees."

    final_state = await tutor_skill.execute(state)

    assert len(final_state.messages) == 1
    response = final_state.messages[0]["content"]
    assert "[TECHNICAL Socratic Challenge]" in response
    assert "memory address allocation flaw" in response


@pytest.mark.asyncio
async def test_adaptive_socratic_tutor_novice(identity_manager: IdentityManager) -> None:
    """Verify the TutorSkill outputs an analogy-based challenge for 'Novice' topics."""
    tutor_skill = TutorSkill(identity_manager)

    state = AstaState()
    state.m_active["user_activity"] = "Explain Biochemistry ATP synthesis."

    final_state = await tutor_skill.execute(state)

    assert len(final_state.messages) == 1
    response = final_state.messages[0]["content"]
    assert "[ANALOGY Socratic Challenge]" in response
    assert "building a house" in response


@pytest.mark.asyncio
async def test_adaptive_socratic_tutor_l2_override(identity_manager: IdentityManager) -> None:
    """Verify L2 Search Engine memory overrides the baseline profile."""
    # Create a mock search engine that returns an 'Expert' finding for Biochemistry
    mock_engine = MagicMock()
    mock_engine.search.return_value = [{"score": 0.95, "content": "User is now an Expert in Biochemistry."}]

    tutor_skill = TutorSkill(identity_manager, search_engine=mock_engine)

    state = AstaState()
    state.m_active["user_activity"] = "Explain Biochemistry ATP synthesis."

    # Even though baseline says Novice, the L2 search says Expert
    final_state = await tutor_skill.execute(state)

    assert len(final_state.messages) == 1
    response = final_state.messages[0]["content"]
    # Should be the technical response now
    assert "[TECHNICAL Socratic Challenge]" in response
