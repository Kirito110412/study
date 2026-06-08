from typing import Tuple
from loguru import logger
from asta.security_isolation.docker_env import DockerEnvironment


class SandboxExecutor:
    """Executes code securely inside the isolated Docker environment."""

    def __init__(self, env: DockerEnvironment) -> None:
        self.env = env

    def run_command(self, command: str) -> Tuple[int, str]:
        """
        Runs a shell command inside the container and returns the exit code and output.
        Uses tty=True to allow capturing formatted output or dealing with basic prompts.
        """
        if not self.env.container:
            raise RuntimeError("Cannot run command: Docker container is not running.")

        logger.debug(f"Executing command in sandbox: {command}")

        # Exec run in docker SDK handles the stream and returns ExecResult (exit_code, output)
        result = self.env.container.exec_run(
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
