# ASTA: Master Architecture & Engineering Implementation Guide

This document is the single source of truth for developing the Advanced Sentient Task Architecture (ASTA). It translates the philosophical Master Blueprint into concrete engineering decisions, protocols, and implementation roadmaps.

## 1. System Topology

ASTA is built entirely on an **Isolated Functional Module** pattern. Components communicate strictly via an Asynchronous Event Bus.

### Directory Structure
```text
asta/
├── core_engine/          # The Graph Router, Event Bus, and Orchestrator
├── memory_domain/        # Hierarchical Paging (L1, L2, L3) and Obsidian integration
├── actuation_sensory/    # VLM bounding box extraction, PyAutoGUI Bezier curves
├── security_isolation/   # Docker container management and PTY streaming
├── identity_domain/      # Axioms, personality profiles, and user tracking
├── feature_architecture/ # Dynamic Skills (Tools) loaded via MCP
├── interfaces/           # Web UI, CLI, and Voice Transceivers
└── docs/                 # Architecture and specifications
```

---

## 2. Core Engine: The Graph Router & Event Bus

We bypass complex frameworks like LangGraph in favor of a raw, localized, high-performance graph executor.

### The AstaGraph (DAG Executor)
*   **Concept:** A mathematical state machine handling the `(M_active, E_docker, T_pending, O_visual, P_mcp)` tuple.
*   **Implementation:**
    *   Build `asta/core_engine/graph.py` using standard Python `asyncio`.
    *   Define `Nodes` as async functions that take the `State` dictionary and return a mutated `State`.
    *   Define `Edges` as synchronous routing functions that evaluate `State` variables and return the string name of the next `Node`.
    *   **Crucial Pattern:** No generic `try/except: pass`. All failures route to an explicit `ErrorAnalysisNode` which uses the LLM to diagnose the issue before retrying.

### The Event Bus
*   **Implementation:** Build `asta/core_engine/event_bus.py` using `asyncio.Queue` or `Redis PubSub` (if scaling). All domains emit events (e.g., `MemoryEvicted`, `ScreenCaptured`, `DockerError`).

---

## 3. Memory Domain: Hierarchical Paged Memory

We adopt the Letta/MemGPT paradigm to manage infinite context with limited VRAM.

### Implementation Steps
1.  **L1 (Prompt Builder):** `asta/memory_domain/l1_context.py`. A strict Jinja2 template that assembles system prompts, active task data, and recent dialogue. It enforces a strict token limit (e.g., 4000).
2.  **L3 (Obsidian Vault):** `asta/memory_domain/l3_obsidian.py`.
    *   All long-term knowledge is stored as `.md` files in a local `~/.asta/vault/` folder.
    *   Files use strict YAML frontmatter for metadata (tags, dates, entities).
3.  **The Pager (The Eviction Protocol):** `asta/memory_domain/pager.py`.
    *   When an interaction happens, token count is checked.
    *   If `tokens > threshold`, the pager extracts the oldest 5 messages, passes them to a lightweight local model to summarize as a "Fact" or "Event".
    *   The summary is appended to the relevant `.md` file in L3, and the raw messages are wiped from L1.

---

## 4. Actuation Sensory: Physical Surrogate

ASTA must physically control the mouse and keyboard based on visual input.

### Implementation Steps
1.  **Screen Capture:** `asta/actuation_sensory/vision.py`. Use `mss` for fast, cross-platform screenshots.
2.  **VLM Bounding Box Parser:**
    *   Integrate a local model (e.g., Qwen-VL or LLaVA via Ollama/llama.cpp).
    *   Prompt: *"Identify all interactive UI elements in this image. Return a JSON list of [id, name, type, x_min, y_min, x_max, y_max]."*
3.  **Motor Control:** `asta/actuation_sensory/motor.py`.
    *   Use `pyautogui`.
    *   Implement `pytweening` and custom Bezier curve math to move the mouse cursor organically to the calculated center of the bounding boxes.

---

## 5. Security Isolation: OpenHands Docker Sandboxing

Every skill or generated script MUST run in isolation.

### Implementation Steps
1.  **Container Manager:** `asta/security_isolation/docker_env.py`.
    *   Use the `docker` pip library.
    *   On startup, pull a base Ubuntu/Python image and create a long-living container named `asta_devenv_core`.
    *   Mount `~/.asta/workspace/` from the host to `/workspace/` in the container.
2.  **PTY Execution:** `asta/security_isolation/executor.py`.
    *   Use Docker Exec API with `tty=True` to stream input/output.
    *   This allows ASTA to see terminal prompts (e.g., "Press Y to continue") and send the corresponding keystrokes back via the Event Bus.

---

## 6. Development Phasing

To bring this architecture to life without getting overwhelmed, development must occur in strict phases:

*   **Phase 1: Foundation:** `pyproject.toml`, folder structure, Event Bus, and dummy Nodes.
*   **Phase 2: Isolation:** Implement the Docker sandbox. The agent must be able to run `ls` in the container and read the output.
*   **Phase 3: Memory:** Implement the L1/L3 paging system. The agent must successfully archive old context to markdown.
*   **Phase 4: Actuation:** Implement the screenshot -> VLM -> PyAutoGUI pipeline.
*   **Phase 5: Domains:** Implement specialized skills (Research, Anti-Atrophy Tutor).