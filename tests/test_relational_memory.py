import pytest
import shutil
from typing import Generator
from unittest.mock import MagicMock, AsyncMock

from asta.memory_domain.l3_obsidian import L3ObsidianVault
from asta.memory_domain.relational_graph import KnowledgeGraphBuilder
from asta.core_engine.llm_gateway import LLMGateway


@pytest.fixture
def temp_vault() -> Generator[str, None, None]:
    path = "/tmp/asta_relational_vault"
    yield path
    shutil.rmtree(path, ignore_errors=True)

@pytest.fixture
def mock_llm() -> LLMGateway:
    llm = MagicMock(spec=LLMGateway)
    # Return a clean JSON matching the forced schema
    mock_json = '{"subject": "User", "action": "Moved to", "object": "New York", "date": "2026"}'
    llm.generate_completion = AsyncMock(return_value=mock_json)
    return llm

@pytest.mark.asyncio
async def test_relational_extraction_and_storage(temp_vault: str, mock_llm: LLMGateway) -> None:
    """
    Verify that the KnowledgeGraphBuilder uses the LLM to parse a raw string,
    populates the NetworkX graph, and saves a formatted metadata block to L3.
    """
    vault = L3ObsidianVault(vault_path=temp_vault)
    builder = KnowledgeGraphBuilder(llm=mock_llm, vault=vault)

    raw_text = "In the year 2026, the user packed up their bags and moved to New York."

    result = await builder.extract_and_store(raw_text)

    # 1. Verify Dictionary Return
    assert result is not None
    assert result["subject"] == "User"
    assert result["action"] == "Moved to"
    assert result["object"] == "New York"

    # 2. Verify NetworkX Graph State
    assert "User" in builder.graph.nodes
    assert "New York" in builder.graph.nodes
    assert builder.graph.has_edge("User", "New York")

    edge_data = builder.graph.get_edge_data("User", "New York")
    assert edge_data["action"] == "Moved to"
    assert edge_data["date"] == "2026"

    # 3. Verify Obsidian Vault Storage
    saved_content = vault.read_entity("User")
    assert "type: relationship" in saved_content
    assert "subject: User" in saved_content
    assert "object: New York" in saved_content
    assert "Original Text: In the year 2026" in saved_content


@pytest.mark.asyncio
async def test_relational_extraction_failure(temp_vault: str) -> None:
    """Verify system handles bad LLM output gracefully."""
    bad_llm = MagicMock(spec=LLMGateway)
    bad_llm.generate_completion = AsyncMock(return_value='{"subject": "User"}') # Missing required keys

    vault = L3ObsidianVault(vault_path=temp_vault)
    builder = KnowledgeGraphBuilder(llm=bad_llm, vault=vault)

    result = await builder.extract_and_store("Some random text")

    assert result is None
    # Graph should be empty
    assert len(builder.graph.nodes) == 0
