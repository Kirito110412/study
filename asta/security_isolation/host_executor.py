import asyncio
from typing import Tuple, Optional
from loguru import logger
from asta.core_engine.event_bus import EventBus, Event

class HostExecutor:
    """
    Executes commands directly on the host operating system.
    Forms the 'Omnipotent' branch of the Dual-Pathway architecture.
    """

    DESTRUCTIVE_COMMANDS = ["rm", "mv", "dd", "mkfs", "format", "del", "rd"]

    def __init__(self, event_bus: Optional[EventBus] = None) -> None:
        self.event_bus = event_bus

    def _is_destructive(self, command: str) -> bool:
        """Checks if a command modifies or deletes host files."""
        # Simple heuristic for MVP
        parts = command.strip().split()
        if not parts:
            return False

        base_cmd = parts[0].lower()
        if base_cmd in self.DESTRUCTIVE_COMMANDS:
            return True

        # Check for output redirection
        if ">" in command or ">>" in command:
            return True

        return False

    async def run_command(self, command: str) -> Tuple[int, str]:
        """
        Runs a shell command on the host.
        Intercepts destructive commands to enforce HIL approval.
        """
        if self._is_destructive(command) and self.event_bus:
            logger.warning(f"Destructive host command detected: '{command}'. Requesting HIL approval.")

            approval_future: asyncio.Future[bool] = asyncio.Future()

            async def _approval_handler(event: Event) -> None:
                if event.type == "APPROVAL_GRANTED" and not approval_future.done():
                    approval_future.set_result(True)
                elif event.type == "APPROVAL_DENIED" and not approval_future.done():
                    approval_future.set_result(False)

            self.event_bus.subscribe("APPROVAL_GRANTED", _approval_handler)
            self.event_bus.subscribe("APPROVAL_DENIED", _approval_handler)

            await self.event_bus.publish(Event(
                type="APPROVAL_REQUIRED",
                payload={"command": command, "context": "HOST_OS"}
            ))

            approved = await approval_future

            self.event_bus.unsubscribe("APPROVAL_GRANTED", _approval_handler)
            self.event_bus.unsubscribe("APPROVAL_DENIED", _approval_handler)

            if not approved:
                logger.warning("Host command execution DENIED by user.")
                return 1, "Execution aborted by user."

            logger.info("Host command execution APPROVED. Proceeding.")

        logger.debug(f"Executing command on host OS: {command}")

        try:
            # Run using asyncio subprocess to prevent blocking the event loop
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()

            output_str = stdout.decode('utf-8')
            error_str = stderr.decode('utf-8')
            exit_code = process.returncode if process.returncode is not None else 1

            combined_output = output_str
            if error_str:
                combined_output += f"\n[STDERR]:\n{error_str}"

            if exit_code != 0:
                logger.warning(f"Host command failed with exit code {exit_code}")

            return exit_code, combined_output.strip()

        except Exception as e:
            logger.error(f"Host execution crashed: {e}")
            return 1, str(e)
