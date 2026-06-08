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


class NodeFunc(Protocol):
    """Protocol defining the signature of a Node execution function."""
    async def __call__(self, state: AstaState) -> AstaState: ...


class EdgeFunc(Protocol):
    """Protocol defining the signature of a Conditional Edge routing function."""
    def __call__(self, state: AstaState) -> str: ...


class AstaGraph:
    """
    A localized, high-performance Directed Acyclic Graph executor
    for Asta's state machine.
    """

    def __init__(self) -> None:
        self.nodes: Dict[str, NodeFunc] = {}
        self.edges: Dict[str, Union[str, EdgeFunc]] = {}
        self.entry_point: str = ""

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
