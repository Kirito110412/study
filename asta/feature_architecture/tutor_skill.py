from typing import Optional
from asta.feature_architecture.skill_base import BaseSkill
from asta.core_engine.graph import AstaState
from asta.memory_domain.l2_search import L2SearchEngine
from asta.identity_domain.profile import IdentityManager
from loguru import logger


class TutorSkill(BaseSkill):
    """
    Simulates the Anti-Atrophy Engine (Adaptive Socratic Tutoring).
    Generates complex thought experiments to prevent user reliance on AI.
    Adapts the complexity of the response based on the user's proficiency level.
    """

    def __init__(self, identity_manager: IdentityManager, search_engine: Optional[L2SearchEngine] = None):
        self.identity = identity_manager
        self.search_engine = search_engine

    @property
    def name(self) -> str:
        return "anti_atrophy_tutor"

    @property
    def description(self) -> str:
        return "Generates Socratic thought experiments adapted to user proficiency to challenge cognition."

    def _determine_proficiency(self, topic: str) -> str:
        """Determines user proficiency using L2 Semantic Memory or baseline configs."""

        # 1. Check dynamic L2 Memory first (if available)
        if self.search_engine:
            query = f"User proficiency level for {topic}"
            results = self.search_engine.search(query, top_k=1)
            if results and results[0]["score"] > 0.8:
                # Mock semantic parsing of the retrieved fact
                content = results[0]["content"].lower()
                if "expert" in content:
                    return "Expert"
                elif "novice" in content:
                    return "Novice"

        # 2. Fallback to Baseline Identity Profile
        proficiencies = self.identity.profile.user_proficiencies
        for key, level in proficiencies.items():
            if key.lower() in topic.lower():
                return level

        return "Novice" # Default assumption for unknown topics

    async def execute(self, state: AstaState) -> AstaState:
        recent_activity = state.m_active.get("user_activity", "general inquiry")

        # Naive topic extraction for MVP
        topic = "general"
        if "python" in recent_activity.lower():
            topic = "Python"
        elif "biochemistry" in recent_activity.lower():
            topic = "Biochemistry"

        proficiency = self._determine_proficiency(topic)

        logger.info(f"Generating cognitive challenge for '{topic}' (User Proficiency: {proficiency})")

        # Adapt output based on proficiency
        if proficiency == "Expert":
            thought_experiment = (
                f"[TECHNICAL Socratic Challenge]: Before I execute '{recent_activity}', identify "
                f"the memory address allocation flaw or Big-O complexity bottleneck in your proposed architecture."
            )
        else:
            thought_experiment = (
                f"[ANALOGY Socratic Challenge]: Before I help with '{recent_activity}', think of it like "
                f"building a house. If the foundation is missing, the roof collapses. "
                f"What is the missing 'foundation' in your current understanding?"
            )

        # Inject the challenge into the agent's message queue to prompt the user
        state.messages.append({"role": "agent", "content": thought_experiment})

        logger.debug(f"Adaptive Socratic challenge ({proficiency}) injected into conversation state.")

        return state
