import pytest
import asyncio
from unittest.mock import MagicMock
from asta.security_isolation.executor import SandboxExecutor
from asta.security_isolation.docker_env import DockerEnvironment
from asta.core_engine.event_bus import EventBus, Event


@pytest.fixture
def mock_env() -> DockerEnvironment:
    env = MagicMock(spec=DockerEnvironment)

    class MockExecResult:
        def __init__(self, exit_code: int, output: bytes):
            self.exit_code = exit_code
            self.output = output

    env.container = MagicMock()
    env.container.exec_run.return_value = MockExecResult(0, b"mock output\n")
    return env


@pytest.mark.asyncio
async def test_hil_high_risk_approval(mock_env: DockerEnvironment) -> None:
    """Verify that a high-risk command halts execution and resumes upon approval."""
    bus = EventBus()
    bus.start()
    executor = SandboxExecutor(mock_env, event_bus=bus)

    # We need to simulate the user responding to the approval request
    async def simulate_user_approval(event: Event) -> None:
        if event.type == "APPROVAL_REQUIRED":
            # User sees the request and says YES
            await asyncio.sleep(0.01) # Simulate think time
            await bus.publish(Event(type="APPROVAL_GRANTED"))

    bus.subscribe("APPROVAL_REQUIRED", simulate_user_approval)

    # Attempt to run a high risk command
    exit_code, output = await executor.run_command("rm -rf /workspace/data")

    # Verify execution proceeded and succeeded
    assert exit_code == 0
    assert "mock output" in output

    await bus.stop()


@pytest.mark.asyncio
async def test_hil_high_risk_denial(mock_env: DockerEnvironment) -> None:
    """Verify that a high-risk command halts execution and aborts upon denial."""
    bus = EventBus()
    bus.start()
    executor = SandboxExecutor(mock_env, event_bus=bus)

    # We need to simulate the user responding to the approval request
    async def simulate_user_denial(event: Event) -> None:
        if event.type == "APPROVAL_REQUIRED":
            # User sees the request and says NO
            await asyncio.sleep(0.01)
            await bus.publish(Event(type="APPROVAL_DENIED"))

    bus.subscribe("APPROVAL_REQUIRED", simulate_user_denial)

    # Attempt to run a high risk command
    exit_code, output = await executor.run_command("format C:")

    # Verify execution aborted
    assert exit_code == 1
    assert "aborted by user" in output

    # Verify Docker exec_run was NEVER called
    mock_env.container.exec_run.assert_not_called() # type: ignore

    await bus.stop()
