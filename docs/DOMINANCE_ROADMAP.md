# ASTA: The Absolute Dominance Roadmap

This document outlines the comprehensive, end-to-end execution plan for building the Advanced Sentient Task Architecture (ASTA). It is designed to aggressively address the "Brutal Gap Analysis" and elevate ASTA from a foundational Graph-Router into an omnipotent, multi-modal, sci-fi tier AI Operating System that surpasses OpenHands, Mem0, CrewAI, and Browser-Use.

---

## Phase 1: The Central Nervous System (Foundations)
*Status: Complete*

**Session 1: The Asynchronous Event Bus**
*   **Tech:** `asyncio.Queue`, Pub/Sub architecture.
*   **Goal:** Establish decoupled communication between all future domains.

**Session 2: The AstaGraph (DAG State Machine)**
*   **Tech:** Python Async Protocols, Directed Acyclic Graphs.
*   **Goal:** Replace non-deterministic LLM chains with a rigorous mathematical state machine (`AstaState`) tracking memory, Docker status, and active tasks.

---

## Phase 2: The Dual-Pathway Execution Engine
*Status: Complete*

**Session 3: The Persistent DevEnv (OpenHands Paradigm)**
*   **Tech:** Docker Python SDK, WebSockets (PTY).
*   **Goal:** Sandboxed execution of untrusted, AI-generated Python code inside a long-living Docker container (`asta_devenv_core`) bound to a specific workspace.

**Session 4: The Omnipotent Host Executor**
*   **Tech:** `asyncio.create_subprocess_shell`.
*   **Goal:** Direct CRUD access to the native Host OS.

**Session 5: "Ask Me First" (Human-In-The-Loop)**
*   **Tech:** `asyncio.Future`, EventBus interception.
*   **Goal:** Strict interception of destructive commands (`rm -rf`, `format`) in both the Sandbox and Host pathways, halting execution until explicit UI/CLI approval is granted.

---

## Phase 3: Infinite Hierarchical Memory
*Status: Complete*

**Session 6: L1 & L3 Paging (The Letta Paradigm)**
*   **Tech:** Jinja2 Templating, Obsidian Markdown Vault.
*   **Goal:** Treat the LLM context window as L1 RAM and the local filesystem as an L3 Hard Drive, preventing context bloat.

**Session 7: L2 Semantic Search**
*   **Tech:** `fastembed` (Vector Semantic), `rank_bm25` (Lexical).
*   **Goal:** Zero-VRAM hybrid search to instantly page specific facts from L3 back into L1.

**Session 8: The Sleep Cycle**
*   **Tech:** `numpy` cosine similarity matrices, EventBus idle tracking.
*   **Goal:** A background process that scans the memory vault during system idleness, merges duplicate semantic embeddings via LLM consolidation, and maintains a pristine memory graph.

---

## Phase 4: Identity & The "Soul"
*Status: Complete*

**Session 9: The Identity Domain**
*   **Tech:** YAML configurations (`baseline.yaml`, `user.yaml`).
*   **Goal:** Instantiate the "Savage Best Friend" persona, loading core axioms and user proficiencies.

**Session 10: The Radically Honest Validator**
*   **Tech:** LLM prompt engineering, Graph Node interception.
*   **Goal:** An adversary node that tests proposed actions against the core axioms, explicitly rejecting sycophancy or flawed logic (e.g., agreeing that 2+2=5) and forcing a replan.

**Session 11: Adaptive Socratic Tutoring**
*   **Tech:** `L2SearchEngine` queries, dynamic prompt adjustment.
*   **Goal:** The Anti-Atrophy engine dynamically scales responses. If the user is an "Expert", it issues Big-O complexity challenges. If a "Novice", it issues analogy-based foundational questions.

---

## Phase 5: The Extensibility Update (Destroying OpenHuman/Hermes)
*Status: Architecture Base Complete. Next steps focus on deep implementation.*

**Session 12: Model Context Protocol (MCP) Integration**
*   **Tech:** `mcp-python` SDK.
*   **Goal:** Instead of writing every tool from scratch, allow ASTA to connect to standard MCP servers (GitHub, Postgres, Slack), wrap their endpoints into dynamic `BaseSkill` Graph Nodes, and execute them natively.

**Session 13: The Skill Forge (Self-Programming)**
*   **Tech:** `litellm` code generation, Docker Sandboxing.
*   **Goal:** When ASTA lacks a tool, it writes a `.py` script, tests it in the isolated container, and upon returning exit code 0, permanently saves it to `~/.asta/skills/` for future graph usage.

---

## Phase 6: Physical Surrogate Reality (Destroying Browser-Use)

**Session 14: Native Screen Vision (The Eyes)**
*   **Tech:** `mss` (Screen Capture), Local VLM (LLaVA/Qwen-VL via `llama.cpp`).
*   **Goal:** Bypass DOM scraping. ASTA takes a screenshot, and the VLM returns an array of interactive bounding boxes (`[id, class, x1, y1, x2, y2]`).

**Session 15: Precision Application Actuation (The Hands)**
*   **Tech:** `PyAutoGUI`, `numpy` Bezier Curves.
*   **Goal:** Generate randomized, human-like mouse movements to the center of bounding boxes to bypass CAPTCHAs. Implement high-frequency keybinding sequences to literally "play" Minecraft or type in WhatsApp.

---

## Phase 7: The OpenHands DevEnv Overhaul (Destroying OpenHands)

**Session 16: The Stateful PTY Terminal**
*   **Tech:** Docker Exec API with streaming WebSockets.
*   **Goal:** Upgrade the Sandbox Executor from a "fire-and-forget" script runner into a persistent interactive session. ASTA must be able to run `npm install`, see the streaming output, respond to prompts (`[Y/n]`), and start local localhost web servers that the human can preview.

---

## Phase 8: Graph-Relational Memory (Destroying Mem0)

**Session 17: Entity-Relational Extraction**
*   **Tech:** Strict JSON schema forcing (`litellm` structured outputs), NetworkX/Neo4j.
*   **Goal:** Before writing to the Obsidian L3 vault, ASTA runs an NLP pipeline to extract rigid entities (`{Subject: User, Action: Moved, Object: NYC, Date: 2026}`). This builds an exact relational knowledge graph to resolve temporal contradictions over decades of use without hallucination.

---

## Phase 9: The STORM Protocol (Destroying AutoResearch)

**Session 18: Academic Synthesizer Sub-Agent**
*   **Tech:** Multi-stage specialized AstaGraphs.
*   **Goal:** When triggered for "Deep Research", ASTA shifts from conversational mode to a rigorous pipeline: Generate Outline -> Actuate Browser to Scrape 50 Sources -> Draft Sections -> Self-Correct -> Compile PDF with Citations.

---

## Phase 10: Enterprise Fleet Management (Destroying CrewAI/Paperclip)

**Session 19: The "Jarvis" Orchestrator Dashboard**
*   **Tech:** FastAPI, React/Next.js UI.
*   **Goal:** When the user issues a massive prompt ("Build a SaaS"), the Web UI visualizes the Orchestrator spawning sub-agents (CTO, Coder, QA). The user acts as the "CEO", viewing individual console logs for each agent, approving their MCP tool usage, and managing the parallel execution fleet.