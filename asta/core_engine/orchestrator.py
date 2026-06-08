import asyncio
import copy
from typing import List
from loguru import logger

from asta.core_engine.graph import AstaGraph, AstaState


class Orchestrator:
    """
    Manages the 'Jarvis' level Multi-Agent Spawning capability.
    Splits massive tasks into parallel sub-graphs and synthesizes their outputs.
    """

    def __init__(self, base_graph: AstaGraph) -> None:
        self.base_graph = base_graph

    def _clone_graph_for_subtask(self, subtask_name: str) -> AstaGraph:
        """
        Creates a lightweight instance of the graph tailored for a sub-agent.
        In a full implementation, this might strip out unrelated skills/nodes.
        For now, we use the base graph.
        """
        # Shallow copy is fine since nodes/edges are stateless protocols
        sub_graph = copy.copy(self.base_graph)
        return sub_graph

    async def execute_sub_task(self, task_desc: str, initial_state: AstaState, task_id: str) -> AstaState:
        """Executes a single sub-task on an isolated graph instance."""
        logger.info(f"Sub-Agent '{task_id}' started: {task_desc}")

        sub_graph = self._clone_graph_for_subtask(task_id)

        # Isolate the state for this sub-agent
        # Deepcopy ensures parallel modifications don't cause race conditions
        sub_state = copy.deepcopy(initial_state)
        sub_state.m_active["current_sub_task"] = task_desc
        sub_state.m_active["sub_agent_id"] = task_id

        # Execute the isolated graph
        try:
            final_sub_state = await sub_graph.execute(sub_state)
            logger.info(f"Sub-Agent '{task_id}' finished successfully.")
            return final_sub_state
        except Exception as e:
            logger.error(f"Sub-Agent '{task_id}' failed: {e}")
            sub_state.error_context = f"sub_agent_failure: {e}"
            return sub_state

    async def delegate_massive_task(self, main_task: str, sub_tasks: List[str], base_state: AstaState) -> AstaState:
        """
        Splits a massive task into multiple sub-tasks and executes them concurrently.
        """
        logger.warning(f"Massive Task Detected: '{main_task}'. Spawning {len(sub_tasks)} Sub-Agents...")

        # Create asynchronous tasks for all sub-agents
        coroutines = []
        for i, sub_task in enumerate(sub_tasks):
            agent_id = f"Agent_{i+1}"
            coro = self.execute_sub_task(sub_task, base_state, agent_id)
            coroutines.append(coro)

        # Execute all sub-agents concurrently
        results: List[AstaState] = await asyncio.gather(*coroutines, return_exceptions=False)

        logger.info("All Sub-Agents have completed their tasks. Synthesizing results...")

        # Synthesize results into the master state
        synthesized_state = copy.deepcopy(base_state)
        synthesized_findings = []

        for idx, result_state in enumerate(results):
            agent_id = f"Agent_{idx+1}"

            if result_state.error_context:
                synthesized_findings.append(f"[{agent_id}] Failed: {result_state.error_context}")
                continue

            # Extract whatever 'result' the sub-agent placed in its active memory
            # For MVP, we look for a generic 'sub_task_result' key
            sub_result = result_state.m_active.get("sub_task_result", "Completed without explicit output.")
            synthesized_findings.append(f"[{agent_id}] Output: {sub_result}")

            # Combine messages from sub-agents
            for msg in result_state.messages:
                # Tag messages so the user knows which sub-agent produced it
                if not msg["content"].startswith(f"[{agent_id}]"):
                    msg["content"] = f"[{agent_id}] {msg['content']}"
                synthesized_state.messages.append(msg)

        synthesized_state.m_active["synthesized_output"] = "\n".join(synthesized_findings)
        logger.info("Synthesis complete. Handing control back to main thread.")

        return synthesized_state
