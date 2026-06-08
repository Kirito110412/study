from asta.feature_architecture.skill_base import BaseSkill
from asta.core_engine.graph import AstaState
from asta.memory_domain.l2_search import L2SearchEngine
from loguru import logger


class RetrievalSkill(BaseSkill):
    """
    Skill to retrieve facts from the L3 Obsidian Vault using L2 Semantic Search.
    Injects the findings into the L1 active state.
    """

    def __init__(self, search_engine: L2SearchEngine) -> None:
        self.search_engine = search_engine

    @property
    def name(self) -> str:
        return "memory_retrieval"

    @property
    def description(self) -> str:
        return "Searches the long-term Obsidian memory vault for contextual facts."

    async def execute(self, state: AstaState) -> AstaState:
        query = state.m_active.get("search_query")

        if not query:
            logger.warning("RetrievalSkill called without a 'search_query' in state.")
            return state

        logger.info(f"Retrieving memory for query: '{query}'")

        results = self.search_engine.search(query, top_k=2)

        if results:
            retrieved_facts = "\n".join([r["content"] for r in results])
            state.m_active["retrieved_context"] = retrieved_facts
            logger.debug(f"Retrieved {len(results)} relevant chunks from memory.")
        else:
            state.m_active["retrieved_context"] = "No relevant memory found."
            logger.debug("No relevant memory found.")

        return state
