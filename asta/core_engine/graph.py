from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Protocol, Union
from loguru import logger


@dataclass
class AstaState:
    """
    Mathematical State representation of the ASTA engine.
    This corresponds to S_t = (M_active, E_docker, T_pending, O_visual, P_mcp)
    """
    m_active: Dict[str, Any] = field(default_factory=dict)     # Paged context loaded in LLM prompt
    e_docker: Dict[str, Any] = field(default_factory=dict)     # Status of dev container
    t_pending: Dict[str, Any] = field(default_factory=dict)    # Pending sub-tasks
    o_visual: Dict[str, Any] = field(default_factory=dict)     # Visual bounding boxes
    p_mcp: Dict[str, Any] = field(default_factory=dict)        # Active MCP connections

    # Internal variables for routing and tracking
    current_node: str = "start"
    error_context: Optional[str] = None
    messages: list[Dict[str, str]] = field(default_factory=list)
    pending_approval: Optional[Dict[str, Any]] = None


class NodeFunc(Protocol):
    """Protocol defining the signature of a Node execution function."""
    async def __call__(self, state: AstaState) -> AstaState: ...


class ApprovalNode:
    """
    Halts graph execution to request explicit Human-In-The-Loop approval.
    Useful for abstract graph-level decisions (e.g., permanently saving a new skill).
    Note: Lower-level system approvals (like Docker shell commands) are handled
    directly via the SandboxExecutor and EventBus.
    """

    async def __call__(self, state: AstaState) -> AstaState:
        # Check if the node is already waiting on approval
        if state.pending_approval and state.pending_approval.get("status") == "WAITING":
            logger.info("Graph is waiting for Human-In-The-Loop approval...")
            # In a fully asynchronous graph engine, this node would return the state
            # and the Orchestrator would suspend graph execution until the EventBus
            # wakes it back up. For MVP, we mark the status.
            return state

        # Initialize an approval request
        action_to_approve = state.m_active.get("action_to_approve", "Unknown Action")
        logger.warning(f"ACTION APPROVAL REQUIRED: {action_to_approve}")

        state.pending_approval = {
            "action": action_to_approve,
            "status": "WAITING"
        }

        # Inject the request into the user conversation state
        state.messages.append({
            "role": "agent",
            "content": f"[APPROVAL REQUIRED]: Are you sure you want to execute '{action_to_approve}'? (Y/N)"
        })

        return state


class EdgeFunc(Protocol):
    """Protocol defining the signature of a Conditional Edge routing function."""
    def __call__(self, state: AstaState) -> str: ...


class AstaGraph:
    """
    A localized, high-performance Directed Acyclic Graph executor
    for Asta's state machine.
    """

    def __init__(self, event_bus: Optional[Any] = None) -> None:
        self.nodes: Dict[str, NodeFunc] = {}
        self.edges: Dict[str, Union[str, EdgeFunc]] = {}
        self.entry_point: str = ""
        self.event_bus = event_bus

    def add_node(self, name: str, action: NodeFunc) -> None:
        """Register a node logic function."""
        if name in self.nodes:
            raise ValueError(f"Node '{name}' already exists.")
        self.nodes[name] = action

    def add_edge(self, source: str, target: str) -> None:
        """Register a strict edge from source to target."""
        self.edges[source] = target

    def add_conditional_edge(self, source: str, condition: EdgeFunc) -> None:
        """Register a conditional edge based on a routing function."""
        self.edges[source] = condition

    def set_entry_point(self, name: str) -> None:
        """Set the starting node for the graph execution."""
        if name not in self.nodes:
            raise ValueError(f"Entry point '{name}' is not a registered node.")
        self.entry_point = name

    async def execute(self, initial_state: AstaState, max_steps: int = 50) -> AstaState:
        """
        Execute the DAG continuously until a terminal node or step limit is reached.
        """
        if not self.entry_point:
            raise ValueError("Entry point not set for AstaGraph.")

        state = initial_state
        state.current_node = self.entry_point
        steps = 0

        logger.info(f"Starting AstaGraph execution at node: {self.entry_point}")

        while steps < max_steps:
            current_name = state.current_node

            if current_name == "END":
                logger.info("Graph execution reached END state.")
                break

            if current_name not in self.nodes:
                raise ValueError(f"Graph routed to unknown node: '{current_name}'")

            # Execute Node Action
            action = self.nodes[current_name]
            logger.debug(f"Executing node: {current_name}")

            # Emit execution telemetry if requested by Orchestrator
            agent_id = state.m_active.get("sub_agent_id")
            if agent_id and hasattr(self, 'event_bus') and self.event_bus:
                await self.event_bus.publish(
                    __import__('asta.core_engine.event_bus', fromlist=['Event']).Event(
                        type="AGENT_LOG",
                        payload={"agent_id": agent_id, "log": f"Executing node: {current_name}"}
                    )
                )

            state = await action(state)

            # Determine Next Node (Routing)
            if current_name not in self.edges:
                logger.warning(f"Node '{current_name}' has no outgoing edge. Terminating.")
                break

            route = self.edges[current_name]
            if callable(route):
                next_node = route(state)
                logger.debug(f"Conditional edge routed from '{current_name}' to '{next_node}'")
            else:
                next_node = route
                logger.debug(f"Strict edge routed from '{current_name}' to '{next_node}'")

            state.current_node = next_node
            steps += 1

        if steps >= max_steps:
            logger.warning(f"Graph execution hit max steps limit ({max_steps}).")

        return state
