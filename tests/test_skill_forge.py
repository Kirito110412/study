import pytest
import shutil
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

from asta.core_engine.graph import AstaGraph, AstaState
from asta.security_isolation.executor import SandboxExecutor
from asta.feature_architecture.skill_forge import SkillForgeNode
from asta.core_engine.llm_gateway import LLMGateway


from typing import Generator

@pytest.fixture
def temp_skills_dir() -> Generator[str, None, None]:
    path = "/tmp/asta_test_skills"
    yield path
    shutil.rmtree(path, ignore_errors=True)

@pytest.fixture
def mock_sandbox() -> SandboxExecutor:
    sandbox = MagicMock(spec=SandboxExecutor)
    # Mock the run_command to simulate a successful Python execution
    sandbox.run_command = AsyncMock(return_value=(0, "Result: 6765"))
    return sandbox

@pytest.fixture
def mock_llm() -> LLMGateway:
    llm = MagicMock(spec=LLMGateway)
    llm.generate_completion = AsyncMock(return_value="def calculate_complex_math():\n    print('Result: 6765')")
    return llm


@pytest.mark.asyncio
async def test_skill_forge_generation_and_testing(mock_sandbox: SandboxExecutor, mock_llm: LLMGateway, temp_skills_dir: str) -> None:
    """
    Verify that the Skill Forge writes a script, tests it in the sandbox,
    and permanently saves it if the exit code is 0.
    """
    graph = AstaGraph()
    forge_node = SkillForgeNode(sandbox=mock_sandbox, llm=mock_llm, skills_dir=temp_skills_dir)

    # Build Graph
    graph.add_node("forge", forge_node) # type: ignore
    graph.add_edge("forge", "END")
    graph.set_entry_point("forge")

    # Create state indicating a missing tool
    state = AstaState()
    state.m_active["missing_tool_task"] = "Complex Math Calculation"

    # Execute Graph
    final_state = await graph.execute(state)

    # 1. Verify Sandbox was called
    mock_sandbox.run_command.assert_called_once() # type: ignore
    call_arg = mock_sandbox.run_command.call_args[0][0] # type: ignore
    assert "python3 /workspace/test_complex_math_calculation.py" in call_arg

    # 2. Verify State was mutated with success
    assert "skill_forge_result" in final_state.m_active
    assert "Result: 6765" in final_state.m_active["skill_forge_result"]
    assert final_state.error_context is None

    # 3. Verify File was saved permanently
    assert "new_skill_path" in final_state.m_active
    saved_path = Path(final_state.m_active["new_skill_path"])
    assert saved_path.exists()
    assert saved_path.name == "complex_math_calculation.py"

    # Read the file to ensure the script content is there
    content = saved_path.read_text()
    assert "def calculate_complex_math" in content


@pytest.mark.asyncio
async def test_skill_forge_failure(mock_sandbox: SandboxExecutor, mock_llm: LLMGateway, temp_skills_dir: str) -> None:
    """Verify that a failed script is NOT saved permanently and errors are logged."""
    # Mock failure
    mock_sandbox.run_command = AsyncMock(return_value=(1, "SyntaxError: invalid syntax")) # type: ignore

    forge_node = SkillForgeNode(sandbox=mock_sandbox, llm=mock_llm, skills_dir=temp_skills_dir)

    state = AstaState()
    state.m_active["missing_tool_task"] = "Bad Script"

    final_state = await forge_node(state)

    # State should flag the error
    assert final_state.error_context == "skill_forge_failed"
    assert "Failed: SyntaxError" in final_state.m_active["skill_forge_result"]

    # File should NOT be saved permanently
    assert "new_skill_path" not in final_state.m_active
    saved_path = Path(temp_skills_dir) / "bad_script.py"
    assert not saved_path.exists()
