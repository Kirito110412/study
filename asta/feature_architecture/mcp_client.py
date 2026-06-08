from typing import Dict, Any, List, Optional
from loguru import logger
import asyncio

from asta.feature_architecture.skill_base import BaseSkill
from asta.core_engine.graph import AstaState


class DynamicMCPSkill(BaseSkill):
    """
    A dynamic wrapper that maps an MCP-discovered tool into a native AstaGraph Node.
    """

    def __init__(self, mcp_client: Any, tool_name: str, tool_description: str):
        self._mcp_client = mcp_client
        self._name = tool_name
        self._description = tool_description

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    async def execute(self, state: AstaState) -> AstaState:
        # Extract arguments for the tool from the active state
        # In a full implementation, an LLM router node maps the user request to these args.
        args = state.m_active.get(f"{self.name}_args", {})

        logger.info(f"Executing MCP Tool '{self.name}' with args: {args}")

        try:
            # Note: Assuming self._mcp_client has an async `call_tool` method
            result = await self._mcp_client.call_tool(self.name, arguments=args)

            # Store the result in the active state
            state.m_active[f"{self.name}_result"] = result
            logger.debug(f"MCP Tool '{self.name}' returned successfully.")

        except Exception as e:
            logger.error(f"Failed to execute MCP Tool '{self.name}': {e}")
            state.error_context = f"mcp_tool_failure_{self.name}"

        return state


class MCPToolClient:
    """
    Manages connections to MCP (Model Context Protocol) servers
    and dynamically converts their tools into ASTA Skills.
    """

    def __init__(self) -> None:
        self.connected_servers: Dict[str, Any] = {}
        # In a real implementation we would hold actual `mcp.client.session.ClientSession`s
        # For this prototype we will use duck-typed mock interfaces to demonstrate the architecture

    async def connect_server(self, server_id: str, server_url_or_cmd: str) -> bool:
        """
        Establish a connection to an MCP server via stdio or SSE.
        """
        logger.info(f"Connecting to MCP server '{server_id}' at {server_url_or_cmd}...")
        # Simulate connection delay
        await asyncio.sleep(0.1)
        self.connected_servers[server_id] = "CONNECTED_MOCK_SESSION"
        return True

    async def discover_and_wrap_tools(self, server_id: str, mock_tools: Optional[List[Dict[str, Any]]] = None) -> List[DynamicMCPSkill]:
        """
        Queries the MCP server for available tools and returns them as BaseSkill instances
        ready to be injected into the AstaGraph.
        """
        if server_id not in self.connected_servers:
            logger.error(f"Cannot discover tools: Not connected to server '{server_id}'")
            return []

        # Simulate an `await session.list_tools()` call
        tools_data = mock_tools or []

        skills = []
        for t in tools_data:
            skill = DynamicMCPSkill(
                mcp_client=self, # Pass self as the executor proxy for now
                tool_name=t["name"],
                tool_description=t["description"]
            )
            skills.append(skill)

        logger.info(f"Discovered {len(skills)} tools from MCP server '{server_id}'")
        return skills

    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> str:
        """Proxy execution method called by DynamicMCPSkill."""
        # For testing verification, we simulate a web scraper
        if name == "web_scraper":
            url = arguments.get("url", "unknown")
            return f"Simulated scraped content from {url}"

        return f"Simulated execution of {name}"
