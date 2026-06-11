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
        args = state.m_active.get(f"{self.name}_args", {})

        # Check if the node is already waiting on approval
        if state.pending_approval and state.pending_approval.get("status") == "WAITING":
            logger.info(f"MCP Tool '{self.name}' is waiting for CEO approval...")
            return state

        logger.info(f"Requesting MCP Tool execution approval for '{self.name}' with args: {args}")

        # Suspend graph and request UI approval
        state.pending_approval = {
            "action": f"MCP_TOOL:{self.name}",
            "args": args,
            "status": "WAITING"
        }

        # If we have an event bus, broadcast the need for approval
        if hasattr(self._mcp_client, "event_bus") and self._mcp_client.event_bus:
            # We don't block locally here. The orchestrator will catch the state return
            # and re-execute once approval is granted by the dashboard via event.
            await self._mcp_client.event_bus.publish(
                # Use a specific event type that the dashboard listens to
                # We mock the Event import for simplicity in this file
                __import__('asta.core_engine.event_bus', fromlist=['Event']).Event(
                    type="AGENT_MCP_APPROVAL_REQUIRED",
                    payload={
                        "agent_id": state.m_active.get("sub_agent_id", "Main"),
                        "tool": self.name,
                        "args": args
                    }
                )
            )
            return state

        # If no event bus is present (e.g. basic CLI test), execute instantly
        await self._execute_tool(state, args)
        return state

    async def _execute_tool(self, state: AstaState, args: Dict[str, Any]) -> None:
        try:
            result = await self._mcp_client.call_tool(self.name, arguments=args)

            # Store the result in the active state
            state.m_active[f"{self.name}_result"] = result
            logger.debug(f"MCP Tool '{self.name}' returned successfully.")

        except Exception as e:
            logger.error(f"Failed to execute MCP Tool '{self.name}': {e}")
            state.error_context = f"mcp_tool_failure_{self.name}"


class MCPToolClient:
    """
    Manages connections to MCP (Model Context Protocol) servers
    and dynamically converts their tools into ASTA Skills.
    """

    def __init__(self, event_bus: Optional[Any] = None) -> None:
        self.connected_servers: Dict[str, Any] = {}
        self.event_bus = event_bus
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
