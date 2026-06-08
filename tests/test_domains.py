import pytest
from pathlib import Path
from asta.identity_domain.profile import IdentityManager
from asta.core_engine.graph import AstaGraph, AstaState
from asta.feature_architecture.research_skill import ResearchSkill
from asta.feature_architecture.tutor_skill import TutorSkill


def test_identity_manager_loading(tmp_path: Path) -> None:
    """Verify that the Identity Profile loads YAML config and builds the header correctly."""

    # Create a mock yaml config
    yaml_content = """
    name: "TestBot"
    role: "Tester"
    core_axioms:
      - "Axiom 1"
      - "Axiom 2"
    linguistic_mastery:
      style: "sarcastic"
    """
    config_file = tmp_path / "test_baseline.yaml"
    config_file.write_text(yaml_content)

    manager = IdentityManager(config_path=str(config_file))

    assert manager.profile.name == "TestBot"
    assert manager.profile.role == "Tester"
    assert len(manager.profile.core_axioms) == 2

    header = manager.get_system_prompt_header()
    assert "You are TestBot, Tester." in header
    assert "Style: sarcastic" in header
    assert "- Axiom 1" in header


@pytest.mark.asyncio
async def test_feature_architecture_graph_integration() -> None:
    """Verify that Specialized Skills can be routed seamlessly as Nodes in the AstaGraph."""

    graph = AstaGraph()

    # Instantiate Skills
    research_skill = ResearchSkill()
    tutor_skill = TutorSkill()

    # Add skills as nodes
    graph.add_node(research_skill.name, research_skill)
    graph.add_node(tutor_skill.name, tutor_skill)

    # Setup routing: Research -> Tutor -> END
    graph.add_edge(research_skill.name, tutor_skill.name)
    graph.add_edge(tutor_skill.name, "END")

    graph.set_entry_point(research_skill.name)

    # Initialize State
    state = AstaState()
    state.m_active["research_target"] = "Quantum Gravity"
    state.m_active["user_activity"] = "calculate gravity"

    # Execute Graph
    final_state = await graph.execute(state)

    # Verify Research Skill Mutations
    assert final_state.current_node == "END"
    assert "research_findings" in final_state.m_active
    assert "Quantum Gravity" in final_state.m_active["research_findings"]
    assert final_state.t_pending.get("verify_Quantum Gravity") == "pending"

    # Verify Tutor Skill Mutations
    assert len(final_state.messages) == 1
    assert "calculate gravity" in final_state.messages[0]["content"]
    assert "first principles" in final_state.messages[0]["content"]
