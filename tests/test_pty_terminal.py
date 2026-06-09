import pytest
from unittest.mock import MagicMock
from asta.security_isolation.docker_env import DockerEnvironment
from asta.security_isolation.pty_terminal import StatefulPTYTerminal


@pytest.fixture
def mock_pty_env() -> DockerEnvironment:
    """Mocks the Docker SDK API to simulate a bidirectional socket."""
    env = MagicMock(spec=DockerEnvironment)
    env.client = MagicMock()
    env.container = MagicMock()
    env.container.id = "mock_container_id"

    # Mock the exec creation
    env.client.api.exec_create.return_value = {"Id": "mock_exec_id"}

    # Mock the socket returned by exec_start
    mock_docker_socketWrapper = MagicMock()
    mock_socket = MagicMock()

    # Simulate a stream of chunks.
    # First chunk is an output, second chunk is an interactive prompt, third is empty (EOF)
    stream_chunks = [
        b"Starting installation...\n",
        b"Do you wish to continue? [y/N] ",
        b""
    ]

    # Stateful side-effect to yield chunks sequentially
    def mock_recv(size: int) -> bytes:
        if stream_chunks:
            return stream_chunks.pop(0)
        return b""

    mock_socket.recv.side_effect = mock_recv
    mock_docker_socketWrapper._sock = mock_socket

    env.client.api.exec_start.return_value = mock_docker_socketWrapper

    return env


@pytest.mark.asyncio
async def test_stateful_pty_interaction(mock_pty_env: DockerEnvironment) -> None:
    """
    Verify the terminal can start a session, asynchronously read streamed chunks,
    detect a prompt, and write an interactive response.
    """
    terminal = StatefulPTYTerminal(mock_pty_env)

    # 1. Start the session
    await terminal.start_interactive_session("/bin/bash")
    assert terminal.is_running is True
    assert terminal._exec_id == "mock_exec_id"

    # Collect streamed output
    received_output = []

    # 2. Read the stream and respond
    async for chunk in terminal.read_stream():
        received_output.append(chunk)

        # If we see the interactive prompt, send a 'y' response
        if "[y/N]" in chunk:
            await terminal.write_input("y")

    # Verify we received both text chunks before EOF
    assert len(received_output) == 2
    assert "Starting installation" in received_output[0]
    assert "[y/N]" in received_output[1]

    # Verify the write_input command successfully wrote to the underlying mock socket
    mock_socket = terminal._socket._sock
    mock_socket.sendall.assert_called_once_with(b"y\n")

    # Session should naturally close when EOF chunk (b"") is reached
    assert terminal.is_running is False

    await terminal.close()
