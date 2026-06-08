from pathlib import Path
from loguru import logger

from asta.core_engine.graph import AstaState
from asta.security_isolation.executor import SandboxExecutor
from asta.core_engine.llm_gateway import LLMGateway


class SkillForgeNode:
    """
    Self-Programming Engine.
    When ASTA lacks a tool, it writes a custom Python script, tests it in the
    Docker sandbox, and saves it permanently to the Skill Library if successful.
    """

    def __init__(self, sandbox: SandboxExecutor, llm: LLMGateway, skills_dir: str = "~/.asta/skills") -> None:
        self.sandbox = sandbox
        self.llm = llm
        self.skills_dir = Path(skills_dir).expanduser()
        self.skills_dir.mkdir(parents=True, exist_ok=True)

    async def _generate_python_script(self, task_description: str) -> str:
        """Uses the LLM Gateway to write a Python script for a novel task."""
        logger.info(f"Skill Forge generating code for task: '{task_description}'")

        prompt = (
            f"You are the ASTA Skill Forge. Your task is to write a self-contained, standalone Python script "
            f"to solve the following task: '{task_description}'.\n"
            f"Requirements:\n"
            f"1. The script must execute successfully when run via `python3 script.py`.\n"
            f"2. Output the result clearly via print().\n"
            f"3. Do NOT include markdown blocks like ```python. Return ONLY the raw Python code."
        )

        response = await self.llm.generate_completion(
            messages=[{"role": "system", "content": prompt}],
            task_type="skill_forge"
        )
        return response.strip()

    async def __call__(self, state: AstaState) -> AstaState:
        missing_tool_task = state.m_active.get("missing_tool_task")

        if not missing_tool_task:
            logger.debug("Skill Forge triggered but no missing task specified.")
            return state

        logger.warning(f"ASTA lacks tool for: '{missing_tool_task}'. Triggering Skill Forge.")

        # 1. Write the script
        script_content = await self._generate_python_script(missing_tool_task)

        # Save it to the Docker workspace for execution
        # Since SandboxExecutor binds ~/.asta/workspace to /workspace, we write it to the host side
        workspace_dir = Path("~/.asta/workspace").expanduser()
        workspace_dir.mkdir(parents=True, exist_ok=True)

        skill_name = missing_tool_task.replace(" ", "_").lower()
        test_script_path = workspace_dir / f"test_{skill_name}.py"
        test_script_path.write_text(script_content)

        # 2. Test in Docker Sandbox
        logger.info(f"Testing newly forged skill '{skill_name}' in Docker sandbox...")
        exit_code, output = await self.sandbox.run_command(f"python3 /workspace/test_{skill_name}.py")

        # 3. Evaluate and Save
        if exit_code == 0:
            logger.info(f"Skill test PASSED. Output: {output}")

            # Save permanently to the skills library
            permanent_path = self.skills_dir / f"{skill_name}.py"
            permanent_path.write_text(script_content)
            logger.info(f"Skill permanently saved to {permanent_path}")

            state.m_active["skill_forge_result"] = f"Success: {output}"
            state.m_active["new_skill_path"] = str(permanent_path)

            # Cleanup test file
            test_script_path.unlink(missing_ok=True)
        else:
            logger.error(f"Skill test FAILED. Exit code {exit_code}. Output: {output}")
            state.error_context = "skill_forge_failed"
            state.m_active["skill_forge_result"] = f"Failed: {output}"

        return state
