# ASTA: Step-by-Step Execution Plan

To prevent scope creep, context overflow, or "freezing" during development, the ASTA Operating System will be built over a series of strict, single-focus sessions. Each session MUST complete one isolated module before moving to the next.

---

## Session 1: Project Scaffolding & The Event Bus (The Nervous System)
**Goal:** Establish the foundational topology and communication layer.
**Tasks:**
1. Initialize standard `pyproject.toml` with `asyncio`, `loguru`, and strict linting (Ruff/MyPy).
2. Create the exact folder hierarchy defined in `ARCHITECTURE_DECISIONS.md` (`core_engine`, `memory_domain`, etc.).
3. Implement `asta/core_engine/event_bus.py`.
   - Must use `asyncio.Queue` or a lightweight pub/sub model.
   - Must define standard Event classes (e.g., `Event(type="Log", payload={...})`).
4. **Verification:** Write `tests/test_event_bus.py` demonstrating two decoupled domains (e.g., dummy Vision and dummy Memory) communicating asynchronously without blocking.

---

## Session 2: The AstaGraph (The Brain/Router)
**Goal:** Build the strict Directed Acyclic Graph (DAG) state machine.
**Tasks:**
1. Implement `asta/core_engine/graph.py` using pure Python `asyncio` (and optionally `NetworkX` for visualization/validation).
2. Define the global $S_t$ `State` dictionary schema.
3. Create the `Node` protocol (async functions returning mutated state) and `Edge` protocol (functions returning the string name of the next node).
4. **Verification:** Build a simple "Hello World" graph with 3 nodes (Start -> Process -> End) and prove state mutations pass through correctly.

---

## Session 3: Security & Isolation (The OpenHands Sandbox)
**Goal:** Ensure the AI can run shell commands/code safely.
**Tasks:**
1. Integrate the `docker` Python SDK.
2. Implement `asta/security_isolation/docker_env.py`.
   - Automatically pull a base image (e.g., Ubuntu + Python).
   - Spin up a persistent container `asta_devenv_core` bound to `~/.asta/workspace`.
3. Implement `asta/security_isolation/executor.py` utilizing Docker Exec with `tty=True` to stream stdout/stderr over websockets or async queues.
4. **Verification:** The agent must be able to send `ls -la` to the container and receive the directory contents back.

---

## Session 4: Hierarchical Memory - L1 & L3 (The Letta Pager)
**Goal:** Implement infinite memory through local Markdown vaulting.
**Tasks:**
1. Implement `asta/memory_domain/l1_context.py` using Jinja2 to enforce strict token limits on prompts.
2. Implement `asta/memory_domain/l3_obsidian.py` to handle read/write of `.md` files in `~/.asta/vault/`.
3. Implement `asta/memory_domain/pager.py`.
   - Write the eviction logic: when L1 exceeds threshold, extract the oldest messages, summarize them, append to L3 Markdown, and prune L1.
4. **Verification:** Feed a mock conversation loop >8000 tokens and verify that L1 stays under 4000 tokens while L3 Markdown files are populated with summarized facts.

---

## Session 5: Hierarchical Memory - L2 (Semantic Search)
**Goal:** Fast retrieval of L3 Vault data to inject into L1.
**Tasks:**
1. Integrate `FastEmbed` and `BM25` for local, zero-VRAM search.
2. Implement a background indexer that scans `~/.asta/vault/` and updates the lexical/semantic indexes.
3. Create a retrieval tool that the graph can call to pull relevant markdown sections based on the current prompt.
4. **Verification:** Search for an obscure entity mentioned in a deep `.md` file and verify it is successfully loaded into the L1 prompt.

---

## Session 6: Actuation Sensory (The VLM & PyAutoGUI Layer)
**Goal:** Enable physical OS interaction based on vision.
**Tasks:**
1. Implement `asta/actuation_sensory/vision.py` using `mss` to grab screenshots.
2. Integrate a mock/local VLM (e.g., LLaVA) prompt to return bounding boxes of UI elements.
3. Implement `asta/actuation_sensory/motor.py` using `PyAutoGUI` with randomized Bezier curve math to move the mouse.
4. **Verification:** The system takes a screenshot, identifies a specific "test button", calculates the center coordinates, and physically moves the mouse to click it.

---

## Session 7: Interfaces & The Omni-Channel Gateway
**Goal:** Connect the core engine to human inputs.
**Tasks:**
1. Implement `asta/interfaces/cli.py` for rich terminal output (using `Rich`).
2. Implement a basic FastAPI endpoint `asta/interfaces/web_api.py` to allow future connection to WhatsApp/Telegram gateways.
3. **Verification:** Send a command via CLI, route it through the Event Bus to the AstaGraph, and return a "task received" acknowledgment.

---

## Session 8: Domain Specialization (The "Soul" & Skills)
**Goal:** Instantiate the actual agent identity and the Dynamic Skill generation.
**Tasks:**
1. Create `asta/identity_domain/baseline.yaml` defining the default "Savage Best Friend" axioms and cultural mastery configs.
2. Setup the Model Context Protocol (MCP) client to allow dynamic loading of custom Python tools.
3. **Verification:** The agent uses an MCP-loaded tool to scrape a webpage, strictly adhering to its defined personality in its response.