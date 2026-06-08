import docker
from docker.models.containers import Container
from docker.errors import DockerException
from loguru import logger
from pathlib import Path


class DockerEnvironment:
    """Manages the isolated ASTA dev environment (OpenHands paradigm)."""

    IMAGE_NAME = "public.ecr.aws/docker/library/python:3.10-slim"
    CONTAINER_NAME = "asta_devenv_core"

    def __init__(self) -> None:
        try:
            self.client = docker.from_env()
        except DockerException as e:
            logger.error(f"Failed to connect to Docker daemon: {e}")
            raise

        self.workspace_dir = Path.home() / ".asta" / "workspace"
        self.workspace_dir.mkdir(parents=True, exist_ok=True)
        self.container: Container | None = None

    def start(self) -> None:
        """Start or attach to the isolated container."""
        # Check if container already exists
        try:
            self.container = self.client.containers.get(self.CONTAINER_NAME)
            if self.container.status != "running":
                self.container.start()
                logger.info(f"Started existing container: {self.CONTAINER_NAME}")
            else:
                logger.info(f"Attached to running container: {self.CONTAINER_NAME}")
            return
        except docker.errors.NotFound:
            pass # We need to create it

        # Pull image and create
        logger.info(f"Pulling image {self.IMAGE_NAME}...")
        self.client.images.pull(self.IMAGE_NAME)

        logger.info(f"Creating persistent container {self.CONTAINER_NAME}...")
        self.container = self.client.containers.run(
            self.IMAGE_NAME,
            command="tail -f /dev/null",  # Keep alive
            name=self.CONTAINER_NAME,
            detach=True,
            volumes={
                str(self.workspace_dir.absolute()): {
                    'bind': '/workspace',
                    'mode': 'rw'
                }
            },
            working_dir='/workspace'
        )

    def stop(self) -> None:
        """Stop and remove the container."""
        if self.container:
            logger.info(f"Stopping container {self.CONTAINER_NAME}...")
            self.container.stop()
            self.container.remove()
            self.container = None
