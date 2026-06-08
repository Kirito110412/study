import pytest
from pathlib import Path
from typing import Generator
import shutil

from asta.memory_domain.l2_search import L2SearchEngine
from asta.feature_architecture.retrieval_skill import RetrievalSkill
from asta.core_engine.graph import AstaState

@pytest.fixture
def search_vault() -> Generator[str, None, None]:
    path = "/tmp/asta_search_vault"
    vault_dir = Path(path)
    vault_dir.mkdir(parents=True, exist_ok=True)

    # Create mock markdown files with distinct facts
    (vault_dir / "Protocol_73.md").write_text(
        "# Protocol 73\n\n"
        "Protocol 73 dictates that the hyperspace actuator must be primed "
        "before engaging the flux capacitor. It was established in 2042."
    )

    (vault_dir / "User_Prefs.md").write_text(
        "# User Preferences\n\n"
        "The user absolutely hates the color orange, but loves deep sea blue."
    )

    yield path
    shutil.rmtree(path, ignore_errors=True)


def test_l2_search_engine_hybrid(search_vault: str) -> None:
    """Verify hybrid BM25 + Semantic search can find exact and semantic matches."""
    engine = L2SearchEngine(vault_path=search_vault)

    # 1. Test Semantic Match (No exact keyword overlap for 'orange')
    # Query: "What colors does the user dislike?" -> Matches "hates the color orange"
    results = engine.search("What colors does the user dislike?", top_k=1)

    assert len(results) == 1
    assert "hates the color orange" in results[0]["content"]
    assert results[0]["metadata"]["file"] == "User_Prefs.md"

    # 2. Test Lexical/Exact Match
    # Query exact specific ID
    results2 = engine.search("Protocol 73 actuator", top_k=1)
    assert len(results2) == 1
    assert "hyperspace actuator must be primed" in results2[0]["content"]


@pytest.mark.asyncio
async def test_retrieval_skill_integration(search_vault: str) -> None:
    """Verify the RetrievalSkill injects the search results into the Graph State."""
    engine = L2SearchEngine(vault_path=search_vault)
    skill = RetrievalSkill(search_engine=engine)

    state = AstaState()
    state.m_active["search_query"] = "When was the hyperspace protocol established?"

    final_state = await skill.execute(state)

    assert "retrieved_context" in final_state.m_active
    assert "2042" in final_state.m_active["retrieved_context"]
