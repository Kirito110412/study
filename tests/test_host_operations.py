import pytest
import asyncio
from typing import Generator
from unittest.mock import patch

from asta.security_isolation.host_executor import HostExecutor
from asta.actuation_sensory.motor import MotorController
from asta.actuation_sensory.precision_controller import PrecisionAppController
from asta.core_engine.event_bus import EventBus, Event

@pytest.fixture
def mock_bus() -> Generator[EventBus, None, None]:
    bus = EventBus()
    bus.start()
    yield bus

    # Must wait for task cleanup before test finishes
    async def cleanup() -> None:
        await bus.stop()

    try:
        loop = asyncio.get_running_loop()
        loop.run_until_complete(cleanup())
    except RuntimeError:
        asyncio.run(cleanup())


@pytest.mark.asyncio
async def test_host_executor_safe_command() -> None:
    """Verify standard host commands execute successfully without HIL interruption."""
    executor = HostExecutor()
    exit_code, output = await executor.run_command("echo 'host system operational'")

    assert exit_code == 0
    assert "host system operational" in output


@pytest.mark.asyncio
async def test_host_executor_destructive_interception() -> None:
    """Verify destructive host commands correctly halt and require approval."""
    bus = EventBus()
    bus.start()
    executor = HostExecutor(event_bus=bus)

    # Simulate User Denying the request
    async def simulate_user_denial(event: Event) -> None:
        if event.type == "APPROVAL_REQUIRED":
            assert event.payload["context"] == "HOST_OS"
            await asyncio.sleep(0.01)
            await bus.publish(Event(type="APPROVAL_DENIED"))

    bus.subscribe("APPROVAL_REQUIRED", simulate_user_denial)

    # Run dangerous command
    exit_code, output = await executor.run_command("rm -rf /some/important/dir")

    # Assert execution was aborted by the HIL safety net
    assert exit_code == 1
    assert "aborted by user" in output

    await bus.stop()


def test_precision_controller_focus_and_keybinds() -> None:
    """Verify the precision controller can target an app and parse a sequence."""
    motor = MotorController(debug_mode=True)
    app_controller = PrecisionAppController(motor)

    # Test focus
    assert app_controller.focus_application("Minecraft") is True
    assert app_controller.focus_application("UnknownApp") is False

    # Test sequence parser routing (since we are in debug mode, it won't crash headless)
    with patch.object(app_controller.motor, 'debug_mode', True):
        # This shouldn't throw any exceptions
        app_controller.build_minecraft_structure()
