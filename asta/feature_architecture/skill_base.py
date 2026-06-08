from abc import ABC, abstractmethod
from asta.core_engine.graph import AstaState


class BaseSkill(ABC):
    """
    Abstract base class for all ASTA Specialized Skills.
    A Skill is designed to be injected as a Node into the AstaGraph.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """The name of the skill (used as the Node ID)."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """A description of what the skill does."""
        pass

    @abstractmethod
    async def execute(self, state: AstaState) -> AstaState:
        """
        The core execution logic of the skill.
        Takes the global AstaState, mutates it, and returns it.
        """
        pass

    async def __call__(self, state: AstaState) -> AstaState:
        """Allows the skill instance to be called directly as a NodeFunc."""
        return await self.execute(state)
