from typing import Tuple, Optional
from loguru import logger
import asyncio
from asta.security_isolation.docker_env import DockerEnvironment
from asta.core_engine.event_bus import EventBus, Event


class SandboxExecutor:
    """Executes code securely inside the isolated Docker environment."""

    HIGH_RISK_COMMANDS = ["rm -rf", "format", "mkfs", "dd", "> /dev/sda", "mkswap"]

    def __init__(self, env: DockerEnvironment, event_bus: Optional[EventBus] = None) -> None:
        self.env = env
        self.event_bus = event_bus

    def _is_high_risk(self, command: str) -> bool:
        """Checks if a command contains known destructive patterns."""
        for risk in self.HIGH_RISK_COMMANDS:
            if risk in command:
                return True
        return False

    async def run_command(self, command: str) -> Tuple[int, str]:
        """
        Runs a shell command inside the container and returns the exit code and output.
        Intercepts high-risk commands to enforce Human-in-the-Loop approval.
        """
        if not self.env.container:
            raise RuntimeError("Cannot run command: Docker container is not running.")

        # HIL Interception
        if self._is_high_risk(command) and self.event_bus:
            logger.warning(f"High-risk command detected: '{command}'. Requesting HIL approval.")

            # We use an asyncio Future to pause this specific execution thread
            # until the EventBus receives a user response.
            approval_future: asyncio.Future[bool] = asyncio.Future()

            async def _approval_handler(event: Event) -> None:
                if event.type == "APPROVAL_GRANTED":
                    if not approval_future.done():
                        approval_future.set_result(True)
                elif event.type == "APPROVAL_DENIED":
                    if not approval_future.done():
                        approval_future.set_result(False)

            self.event_bus.subscribe("APPROVAL_GRANTED", _approval_handler)
            self.event_bus.subscribe("APPROVAL_DENIED", _approval_handler)

            # Emit the request
            await self.event_bus.publish(Event(
                type="APPROVAL_REQUIRED",
                payload={"command": command}
            ))

            # Block until user responds
            approved = await approval_future

            # Cleanup listeners
            self.event_bus.unsubscribe("APPROVAL_GRANTED", _approval_handler)
            self.event_bus.unsubscribe("APPROVAL_DENIED", _approval_handler)

            if not approved:
                logger.warning("High-risk command execution DENIED by user.")
                return 1, "Execution aborted by user."

            logger.info("High-risk command execution APPROVED. Proceeding.")

        logger.debug(f"Executing command in sandbox: {command}")

        # Exec run in docker SDK handles the stream and returns ExecResult (exit_code, output)
        # We run it in a thread pool to prevent blocking the async event loop during execution
        result = await asyncio.to_thread(
            self.env.container.exec_run,
            cmd=["/bin/sh", "-c", command],
            tty=True,
            workdir="/workspace"
        )

        output_bytes = result.output
        output_str = output_bytes.decode("utf-8") if isinstance(output_bytes, bytes) else ""
        exit_code = result.exit_code if result.exit_code is not None else 1

        if exit_code != 0:
            logger.warning(f"Command failed with exit code {exit_code}: {output_str.strip()}")

        return exit_code, output_str
