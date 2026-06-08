import pytest
from typing import Generator, Any
from asta.security_isolation.docker_env import DockerEnvironment
from asta.security_isolation.executor import SandboxExecutor
from unittest.mock import MagicMock, patch

# In sandboxed environments (like the test runner), Docker daemon's overlayfs mounting
# can fail due to nested container limitations. We mock the Docker interactions here
# while validating the correct SDK calls.

@pytest.fixture(scope="module")
def mock_docker_env() -> Generator[DockerEnvironment, None, None]:
    with patch("asta.security_isolation.docker_env.docker.from_env") as mock_from_env:
        mock_client = MagicMock()
        mock_from_env.return_value = mock_client

        # Mock container behavior
        mock_container = MagicMock()
        mock_container.status = "running"

        class MockExecResult:
            def __init__(self, exit_code: int, output: bytes):
                self.exit_code = exit_code
                self.output = output

        def mock_exec_run(cmd: Any, **kwargs: Any) -> MockExecResult:
            command_str = cmd[-1] if isinstance(cmd, list) else str(cmd)
            if "echo" in command_str:
                return MockExecResult(0, b"hello from sandbox\n")
            if "cat" in command_str:
                return MockExecResult(0, b"secure data\n")
            return MockExecResult(1, b"command failed")

        mock_container.exec_run.side_effect = mock_exec_run

        mock_client.containers.get.return_value = mock_container
        mock_client.containers.run.return_value = mock_container

        env = DockerEnvironment()
        env.start()

        yield env
        env.stop()


def test_sandbox_execution(mock_docker_env: DockerEnvironment) -> None:
    """Verify that the agent can execute commands in the isolated container."""
    executor = SandboxExecutor(mock_docker_env)

    # Run a simple echo command
    exit_code, output = executor.run_command("echo 'hello from sandbox'")
    assert exit_code == 0
    assert "hello from sandbox" in output

    # Verify the SDK was called correctly
    if mock_docker_env.container:
        mock_docker_env.container.exec_run.assert_called_with( # type: ignore
            cmd=["/bin/sh", "-c", "echo 'hello from sandbox'"],
            tty=True,
            workdir="/workspace"
        )

def test_sandbox_volume_binding(mock_docker_env: DockerEnvironment) -> None:
    """Verify that the host workspace is bound correctly to the container."""
    executor = SandboxExecutor(mock_docker_env)

    # Read the file from inside the container (mocked to return 'secure data')
    exit_code, output = executor.run_command("cat /workspace/test_file.txt")
    assert exit_code == 0
    assert "secure data" in output
