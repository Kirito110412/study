import asyncio
from typing import Optional, AsyncGenerator, Any
from loguru import logger
from asta.security_isolation.docker_env import DockerEnvironment


class StatefulPTYTerminal:
    """
    Upgrades the Sandbox Executor to a Persistent Interactive Terminal.
    Instead of fire-and-forget, this streams output and allows interactive input (e.g. [y/N]).
    """

    def __init__(self, env: DockerEnvironment) -> None:
        self.env = env
        self._socket: Any = None
        self._exec_id: Optional[str] = None
        self.is_running: bool = False

    async def start_interactive_session(self, command: str = "/bin/bash") -> None:
        """Starts a persistent, interactive bash session in the container."""
        if not self.env.container:
            raise RuntimeError("Cannot start PTY: Docker container is not running.")

        logger.info(f"Starting persistent PTY session with command: {command}")

        # We must use low-level API to get the socket for true bidirectional streaming
        client_api = self.env.client.api

        exec_create = client_api.exec_create(
            self.env.container.id,
            cmd=[command],
            stdin=True,
            stdout=True,
            stderr=True,
            tty=True, # Critical for interactive prompts
            workdir="/workspace"
        )
        self._exec_id = exec_create['Id']

        # Open the socket attached to the exec instance
        self._socket = client_api.exec_start(
            exec_id=self._exec_id,
            detach=False,
            tty=True,
            stream=True,
            socket=True
        )
        self.is_running = True
        logger.debug("PTY Socket attached successfully.")

    async def read_stream(self, chunk_size: int = 4096) -> AsyncGenerator[str, None]:
        """Asynchronously yields chunks of streaming output from the terminal."""
        if not self._socket or not self.is_running:
            raise RuntimeError("PTY session is not running.")

        logger.debug("Listening to PTY stream...")

        while self.is_running:
            try:
                # Docker socket read is blocking in the standard library.
                # We offload it to a thread to keep the asyncio loop unblocked.
                # Use _sock.recv directly since Docker wraps the socket
                data = await asyncio.to_thread(self._socket._sock.recv, chunk_size)

                if not data:
                    # Stream closed naturally
                    logger.debug("PTY stream closed.")
                    self.is_running = False
                    break

                yield data.decode('utf-8', errors='replace')

            except Exception as e:
                logger.error(f"Error reading PTY stream: {e}")
                self.is_running = False
                break

    async def write_input(self, text: str) -> None:
        """Writes text directly to the STDIN of the running terminal session."""
        if not self._socket or not self.is_running:
            raise RuntimeError("PTY session is not running.")

        if not text.endswith("\n"):
            text += "\n"

        try:
            # Write to the underlying socket
            await asyncio.to_thread(self._socket._sock.sendall, text.encode('utf-8'))
            logger.debug(f"Sent input to PTY: '{text.strip()}'")
        except Exception as e:
            logger.error(f"Failed to write to PTY: {e}")
            self.is_running = False

    async def close(self) -> None:
        """Closes the interactive session."""
        self.is_running = False
        if self._socket:
            try:
                self._socket.close()
            except Exception:
                pass
        self._socket = None
        logger.info("PTY Terminal Session closed.")
