# ASTA: Comprehensive Execution Plan & Roadmap

This document outlines the strict, session-by-session execution strategy to build the Advanced Sentient Task Architecture (ASTA). Based on the Comprehensive Profile, ASTA requires distinct, decoupled layers spanning Identity, Logic, Memory, Actuation, and Security.

> **Note:** Phases 1 through 5 (Foundations, DAG Graph, L1/L3 Memory, VLM Actuation, and Core Identity/Skills) have already been initialized in the current repository. This roadmap focuses on evolving the existing architecture to fulfill the massive Sci-Fi capabilities defined in the Master Profile.

---

## Phase 6: The "Soul" Integration & Human-In-The-Loop (HIL)

### Session 9: The Radically Honest Validator Node
**Goal:** Implement the verification engine that tests logic against foundational axioms before acting.
**Tasks:**
1. Create `asta/identity_domain/validator.py`.
2. Implement an `AxiomVerificationNode` in the `AstaGraph`. Before the agent executes an external action, this node cross-references the proposed action against the `baseline.yaml` axioms.
3. If an action violates an axiom (e.g., "syophancy" instead of truth), the node rejects the action and forces a re-plan.
4. **Verification:** Pass a prompt asking the agent to "agree with a flawed mathematical concept." Ensure the Validator Node intercepts and forces the agent to output the "Radically Honest" rejection.

### Session 10: "Ask Me First" (HIL Execution)
**Goal:** Prevent destructive commands by enforcing a strict terminal/UI approval loop.
**Tasks:**
1. Implement an `ApprovalNode` inside `asta/core_engine/graph.py`.
2. Define a list of high-risk shell commands (e.g., `rm -rf`, `format`).
3. When the `SandboxExecutor` detects a high-risk command, it halts execution, emits an `APPROVAL_REQUIRED` event to the `EventBus`, and waits for an asynchronous `APPROVAL_GRANTED` event.
4. **Verification:** Ask the agent to delete a folder in the Docker container. Verify execution pauses until a manual `Y` is submitted via the CLI.

---

## Phase 7: Advanced Memory Operations

### Session 11: The "Sleep Cycle" (Background Pruning)
**Goal:** Implement the idle background process to merge duplicates and build relational graphs.
**Tasks:**
1. Create `asta/memory_domain/sleep_cycle.py`.
2. Implement an `asyncio` background task that triggers when the `EventBus` has been silent for $X$ minutes.
3. The sleep cycle scans `~/.asta/vault/`, identifies duplicate semantic embeddings via the `L2SearchEngine`, and uses a lightweight LLM prompt to merge them into a single, cohesive Markdown document.
4. **Verification:** Inject 5 slightly different variations of the same fact into the vault. Trigger the sleep cycle and verify they are consolidated into one clean entry.

### Session 12: Adaptive Socratic Tutoring
**Goal:** Implement knowledge density tracking.
**Tasks:**
1. Expand `IdentityProfile` to track user proficiency levels across topics (e.g., `Python: Expert`, `Biochemistry: Novice`).
2. Update the `TutorSkill` to query the `L2SearchEngine` for the user's proficiency before generating a response.
3. **Verification:** Ask a question about Python. Verify the response is highly technical. Ask a question about Biochemistry. Verify the response uses analogies.

---

## Phase 8: Autonomous Growth & Tool Spawning

### Session 13: Model Context Protocol (MCP) Integration
**Goal:** Abstract all standard tool usage via MCP.
**Tasks:**
1. Integrate an MCP Client (e.g., `mcp-python`) into `asta/feature_architecture/mcp_client.py`.
2. Map MCP-discovered tools dynamically into `BaseSkill` wrappers so they can be injected as `AstaGraph` nodes.
3. **Verification:** Connect a standard MCP web-scraping server. Command ASTA to scrape a page, verifying it uses the MCP tool rather than a hardcoded script.

### Session 14: The Skill Forge (Self-Programming)
**Goal:** Asta writes, tests, and saves its own Python tools.
**Tasks:**
1. Create `asta/feature_architecture/skill_forge.py`.
2. If Asta lacks a tool, it routes to the `SkillForgeNode`. It writes a Python script, pushes it to the `SandboxExecutor` (Docker), and runs a test.
3. If it passes, it saves the script to `~/.asta/skills/` and dynamically loads it into its available graph nodes.
4. **Verification:** Ask ASTA to perform a highly specific math calculation it has no tool for. Verify it writes a `.py` script, tests it in Docker, and returns the correct answer.

---

## Phase 9: "Jarvis" Level Multi-Agent Orchestration

### Session 15: Sub-Agent Spawning
**Goal:** Delegate massive tasks to parallel sub-agents.
**Tasks:**
1. Implement `asta/core_engine/orchestrator.py`.
2. When a massive task is detected, the Orchestrator splits the task into sub-graphs (e.g., Graph A: Researcher, Graph B: Coder).
3. Each sub-graph is executed concurrently via `asyncio.gather`. The Orchestrator waits for all sub-graphs to reach `END` before synthesizing the final output.
4. **Verification:** Command ASTA to "Research quantum computing and simultaneously write a Python script calculating gravity." Verify both tasks run in parallel and their outputs are combined at the end.

---

## Phase 10: Omnipotent Host Operations & Precision Application Control

### Session 16: The Dual-Pathway Host Executor
**Goal:** Break out of the sandbox to perform direct CRUD operations on the user's host OS while maintaining strict safety boundaries.
**Tasks:**
1. Implement `asta/security_isolation/host_executor.py`.
2. Establish a **Dual-Pathway Architecture**:
   - Untrusted code (Skill Forge) runs in Docker.
   - Explicit user requests (e.g., "Delete this file", "Move my documents") run via the `HostExecutor` on the native machine.
3. Hook the `HostExecutor` into the HIL EventBus. Any destructive command (`rm`, `mv`, overwrite) outside of the immediate ASTA workspace must trigger an `APPROVAL_REQUIRED` event.
4. **Verification:** Ask the agent to delete a local file on the host OS. Verify the system pauses and demands explicit terminal confirmation before acting.

### Session 17: Precision Application Actuation (WhatsApp & Minecraft)
**Goal:** Enable ASTA to natively hook into and physically operate high-precision host applications.
**Tasks:**
1. Implement `asta/actuation_sensory/precision_controller.py`.
2. Build OS-level window focus hooks to bring specific applications (e.g., WhatsApp, Minecraft) to the foreground.
3. Develop hybrid actuation routines:
   - **Programmatic (MCP):** Connect to APIs where applicable for fast data retrieval.
   - **Physical (VLM + Motor):** Read the screen and generate high-frequency keybinds and mouse movements. For Minecraft, this allows Asta to "play" the game alongside the user, placing blocks physically to create structures.
4. **Verification:** Test the system's ability to focus a mock application window and stream a sequence of precision keyboard inputs (e.g., WASD movements and block placements) seamlessly.