from asta.feature_architecture.skill_base import BaseSkill
from asta.core_engine.graph import AstaState
from loguru import logger


class TutorSkill(BaseSkill):
    """
    Simulates the Anti-Atrophy Engine.
    Generates complex thought experiments to prevent user reliance on AI.
    """

    @property
    def name(self) -> str:
        return "anti_atrophy_tutor"

    @property
    def description(self) -> str:
        return "Generates Socratic thought experiments to challenge human cognition."

    async def execute(self, state: AstaState) -> AstaState:
        recent_activity = state.m_active.get("user_activity", "general inquiry")

        logger.info(f"Analyzing user activity ('{recent_activity}') to generate cognitive challenge...")

        # Simulate LLM Socratic generation based on the IdentityProfile axioms
        thought_experiment = (
            f"You asked me to solve '{recent_activity}'. I can do that, but first, "
            f"if you were forced to solve this using only first principles, "
            f"what is the immediate failing point of your current mental model?"
        )

        # Inject the challenge into the agent's message queue to prompt the user
        state.messages.append({"role": "agent", "content": thought_experiment})

        logger.debug("Socratic challenge injected into conversation state.")

        return state
