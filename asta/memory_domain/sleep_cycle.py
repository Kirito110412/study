import asyncio
import time
import numpy as np
from typing import List, Set
from loguru import logger

from asta.core_engine.event_bus import EventBus, Event
from asta.memory_domain.l2_search import L2SearchEngine
from asta.memory_domain.l3_obsidian import L3ObsidianVault


class SleepCycleManager:
    """
    Background process that runs when the ASTA EventBus is idle.
    Merges duplicate memory chunks and builds relational knowledge graphs.
    """

    def __init__(self,
                 event_bus: EventBus,
                 search_engine: L2SearchEngine,
                 vault: L3ObsidianVault,
                 idle_threshold_minutes: float = 5.0) -> None:
        self.event_bus = event_bus
        self.search_engine = search_engine
        self.vault = vault
        self.idle_threshold_seconds = idle_threshold_minutes * 60
        self._running = False
        self._task: asyncio.Task[None] | None = None

    def start(self) -> None:
        if not self._running:
            self._running = True
            self._task = asyncio.create_task(self._sleep_loop())
            logger.info(f"Sleep Cycle Manager started (Threshold: {self.idle_threshold_seconds}s)")

    async def stop(self) -> None:
        if self._running:
            self._running = False
            if self._task:
                self._task.cancel()
                try:
                    await self._task
                except asyncio.CancelledError:
                    pass
            logger.info("Sleep Cycle Manager stopped.")

    async def _sleep_loop(self) -> None:
        """Continuously polls for system idleness."""
        while self._running:
            await asyncio.sleep(10) # Check every 10 seconds

            idle_time = time.time() - self.event_bus.last_activity_time
            if idle_time > self.idle_threshold_seconds:
                logger.info(f"System idle for {idle_time:.1f}s. Initiating Sleep Cycle Memory Pruning...")
                await self.prune_memory()
                # Publish heartbeat so we don't spam sleep cycles continuously
                await self.event_bus.publish(Event(type="SLEEP_CYCLE_HEARTBEAT"))
                # Force reset the timer so it waits the full threshold again before next run
                self.event_bus.last_activity_time = time.time()

    async def prune_memory(self) -> None:
        """
        Scans L2 semantic embeddings for high-similarity duplicates
        and consolidates them in L3 Markdown.
        """
        engine = self.search_engine
        if not engine.documents or engine.document_embeddings is None:
            logger.debug("Vault is empty. Skipping prune.")
            return

        logger.debug(f"Sleep cycle scanning {len(engine.documents)} memory chunks for duplicates...")

        # O(N^2) similarity matrix calculation
        # Since this runs in the background while idle, we can afford heavy ops
        norms = np.linalg.norm(engine.document_embeddings, axis=1)
        valid_mask = norms != 0

        embeddings = engine.document_embeddings[valid_mask]
        docs = [engine.documents[i] for i in range(len(engine.documents)) if valid_mask[i]]
        metadata = [engine.doc_metadata[i] for i in range(len(engine.documents)) if valid_mask[i]]

        if len(embeddings) < 2:
            return

        # Calculate cosine similarity matrix
        sim_matrix = np.dot(embeddings, embeddings.T) / np.outer(norms[valid_mask], norms[valid_mask])

        # Find pairs with similarity > 0.90
        # We only care about upper triangle to avoid duplicate pairs and self-matches
        high_sim_indices = np.where(np.triu(sim_matrix, k=1) > 0.90)

        pairs = list(zip(high_sim_indices[0], high_sim_indices[1]))

        if not pairs:
            logger.info("Sleep cycle complete. No duplicates found.")
            return

        logger.info(f"Found {len(pairs)} highly similar memory pairs. Initiating consolidation.")

        # Group overlapping duplicates
        clusters: List[Set[int]] = []
        for i, j in pairs:
            added = False
            for cluster in clusters:
                if i in cluster or j in cluster:
                    cluster.add(i)
                    cluster.add(j)
                    added = True
                    break
            if not added:
                clusters.append({i, j})

        # Consolidate each cluster
        for cluster in clusters:
            indices = list(cluster)
            target_file = metadata[indices[0]]["file"]

            # Combine the texts
            texts_to_merge = [docs[i] for i in indices]

            # Simulate LLM summarization of duplicates
            merged_fact = self._simulate_llm_merge(texts_to_merge)

            # Write to Vault
            entity_name = target_file.replace('.md', '').replace('_', ' ')
            self.vault.append_fact(entity_name, merged_fact)

            # Note: For MVP we just append the merged fact. A full implementation
            # would rewrite the file to remove the old lines.
            logger.debug(f"Consolidated {len(texts_to_merge)} chunks into {target_file}")

        # Re-index the L2 search engine
        await asyncio.to_thread(engine._build_index)
        logger.info("Sleep cycle consolidation and re-indexing complete.")

    def _simulate_llm_merge(self, texts: List[str]) -> str:
        """Mocks an LLM consolidating multiple similar facts into one."""
        return f"[CONSOLIDATED FACT]: {texts[0]} (and {len(texts)-1} similar entries merged)"
