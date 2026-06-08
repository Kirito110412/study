import pytest
from asta.feature_architecture.mcp_client import MCPToolClient
from asta.core_engine.graph import AstaGraph, AstaState


@pytest.mark.asyncio
async def test_mcp_dynamic_tool_wrapping_and_execution() -> None:
    """
    Verify that ASTA can connect to an MCP server, discover a tool,
    wrap it as a graph Node, and execute it successfully.
    """
    mcp_client = MCPToolClient()

    # 1. Connect to simulated server
    connected = await mcp_client.connect_server("scraper_server", "stdio://mock")
    assert connected is True

    # 2. Discover tools
    mock_mcp_tools = [
        {"name": "web_scraper", "description": "Extracts text from a URL."}
    ]

    skills = await mcp_client.discover_and_wrap_tools("scraper_server", mock_tools=mock_mcp_tools)

    assert len(skills) == 1
    scraper_skill = skills[0]

    assert scraper_skill.name == "web_scraper"
    assert "Extracts text" in scraper_skill.description

    # 3. Inject into AstaGraph
    graph = AstaGraph()
    graph.add_node(scraper_skill.name, scraper_skill)
    graph.add_edge(scraper_skill.name, "END")
    graph.set_entry_point(scraper_skill.name)

    # 4. Create state mapping the arguments
    state = AstaState()
    state.m_active["web_scraper_args"] = {"url": "https://example.com"}

    # 5. Execute Graph
    final_state = await graph.execute(state)

    # Verify the dynamic node executed the tool and mutated the state
    assert final_state.current_node == "END"

    # The skill saves the result as {tool_name}_result
    assert "web_scraper_result" in final_state.m_active
    assert "Simulated scraped content from https://example.com" in final_state.m_active["web_scraper_result"]
