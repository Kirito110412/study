# ASTA: Domain Analysis & Ecosystem Research

To build the Advanced Sentient Task Architecture (ASTA), we must evaluate the current state of AI frameworks across all relevant domains and define exactly how ASTA surpasses or integrates them.

## 1. Orchestration & DAG Routing (The Core Engine)

**The Goal:** Asta requires a localized, continuous, stateful execution loop that does not rely on nested `if/else` statements, but rather mathematical state machines (Markov Decision Processes) and Directed Acyclic Graphs (DAGs).

### State-of-the-Art Frameworks (2026)
*   **LangGraph:** The industry standard for stateful, graph-based agent orchestration. It models workflows natively as graphs (State, Nodes, Edges) and supports checkpoint persistence.
*   **CrewAI:** Focuses on role-based multi-agent collaboration. Great for defining specific "employees" (e.g., Researcher, Coder) but lacks the low-level mathematical rigor and exact state control required by Asta's core loop.
*   **AutoGen (AG2):** Excellent for dialogue-based collaboration rather than strict graph traversal. Heavily used in research, but can be non-deterministic compared to a strict DAG.
*   **Pydantic AI / SmolAgents:** Lightweight, type-safe frameworks meant to reduce bloat.

### ASTA's Implementation Strategy
**Decision:** We will build a custom **AstaGraph** heavily inspired by **LangGraph's mathematical rigor**, but tailored for zero-abstraction local inference.
*   **Why:** ASTA needs absolute control over the $S_t$ (State) object containing Paged Memory, Docker Status, and Screen Coordinates. Standard LangGraph introduces overhead we want to avoid for a pure 3B local model, but its conceptual framework (Nodes as functions, Edges as conditional probabilities) is perfect.
*   **Implementation:** We will use native Python `asyncio` and `NetworkX` to build a localized event bus. The DAG will route failure nodes explicitly to error-correction modules rather than catching generic exceptions.

---

## 2. Memory & Context Paging (The Memory Domain)

**The Goal:** Run 3B to 8B models without Out-Of-Memory (OOM) errors via Virtual Memory. Implement L1 (Context), L2 (Vector), and L3 (Obsidian Graph) memory.

### State-of-the-Art Frameworks (2026)
*   **Mem0:** Top-tier for overall agent memory, combining Vector, Graph, and KV stores. API-heavy but very capable.
*   **Letta (formerly MemGPT):** Designed explicitly for OS-level paging. It treats the context window like RAM and external storage like a hard drive, letting the agent decide when to swap context.
*   **Zep / Graphiti:** Focuses heavily on temporal relationships (tracking how facts change over time).

### ASTA's Implementation Strategy
**Decision:** We will combine the **Letta (OS Paging)** paradigm with a **Zero-VRAM Obsidian-style Markdown Vault**.
*   **Why:** ASTA emphasizes absolute local sovereignty and minimal resource bloat. Standard vector DBs (like Pinecone) require overhead. We will use local Markdown files (`.md`) linked via bidirectional references.
*   **Implementation:**
    *   **L1:** The strict 4k/8k token prompt.
    *   **L2:** A local `BM25` (Lexical) + `FastEmbed` (Semantic) search over the active workspace.
    *   **L3:** An Obsidian-compatible directory structure. We will implement Letta's "Eviction Protocol" natively: when L1 hits 90% capacity, the agent triggers a function to compress the oldest context and append it to the relevant `.md` file in L3.

---

## 3. Vision & Physical Actuation (Actuation Sensory)

**The Goal:** ASTA must interact with the host OS visually, calculating bounding boxes for UI elements and driving the mouse/keyboard using human-like Bezier curves. Zero API mocking.

### State-of-the-Art Frameworks (2026)
*   **Browser-Use:** The bleeding edge for web actuation. It uses DOM extraction alongside vision models to generate interactable bounding boxes over screenshots.
*   **OS-Copilot / UI-TARS:** Research frameworks focused on general desktop GUI interaction via Vision-Language Models (VLMs).
*   **PyAutoGUI / MacoOS Native:** The raw execution layer for physical mouse movement.

### ASTA's Implementation Strategy
**Decision:** A custom **Physical Surrogate Reality** pipeline fusing DOM/UI-Tree extraction with VLM coordinates.
*   **Why:** Relying on APIs defeats the purpose of an autonomous physical surrogate.
*   **Implementation:**
    1. Capture screen via native OS APIs (e.g., `mss` or `screencapture`).
    2. Pass the image to a lightweight local VLM (like LLaVA or Qwen-VL) to extract semantic bounding boxes.
    3. Calculate the center coordinate $C_{target} = ((x_1+x_2)/2, (y_1+y_2)/2)$.
    4. Execute movement using PyAutoGUI with randomized bezier curves to avoid anti-bot detection.

---

## 4. Security & Isolation (The OpenHands Paradigm)

**The Goal:** Complete sandboxing of AI-generated code. The agent must write, execute, and debug code without risking the host system.

### State-of-the-Art Frameworks (2026)
*   **OpenHands (OpenDevin):** Enterprise-grade platform that spins up isolated Docker containers accessible via SSH and websockets. Incredible for streaming PTY (terminal) output back to the agent.
*   **SWE-Agent:** Research-focused, features an innovative Agent-Computer Interface, but highly tailored to specific Ubuntu setups.

### ASTA's Implementation Strategy
**Decision:** We will adopt the **OpenHands Docker Sandboxing Architecture**.
*   **Why:** The `PTY Streaming` (WebSockets) feature is critical. ASTA needs to read terminal output in real-time to answer interactive prompts (like `[Y/n]`).
*   **Implementation:** We will use the native Python `docker` SDK to spin up ephemeral `asta_devenv` containers. Volumes will be strictly bound to a `/workspace` directory, and any path traversal will be blocked at the Python execution level.

---

## 5. Domain Specialization (The Capability Matrix)

Asta is not just a coder; it spans multiple domains:

*   **The Employee Surrogate:** Automating repetitive corporate tasks (data entry, CRM updates) via the physical VLM actuation module. It doesn't need API keys; it logs in like a human.
*   **The PhD Researcher:** Using the `EventBus`, it can spawn sub-agents that scour ArXiv, download PDFs, compress them into the Obsidian L3 memory, and synthesize novel hypotheses over a multi-day timeline.
*   **The Content Creator:** Interfacing with video/audio generation APIs to manage YouTube/Instagram channels autonomously.
*   **The Anti-Atrophy Tutor:** Monitoring user interactions and proactively generating Socratic thought experiments to challenge the human, preventing reliance on the AI.

These are not separate apps; they are **Skills** (Python scripts) dynamically loaded into the AstaGraph execution loop as nodes, running concurrently via the Async Task Queue.