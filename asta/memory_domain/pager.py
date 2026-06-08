from loguru import logger
from asta.memory_domain.l1_context import L1ContextWindow
from asta.memory_domain.l3_obsidian import L3ObsidianVault


class MemoryPager:
    """Implements the Letta-style Eviction Protocol to manage context size."""

    def __init__(self, l1: L1ContextWindow, l3: L3ObsidianVault) -> None:
        self.l1 = l1
        self.l3 = l3

    def check_and_evict(self, threshold_ratio: float = 0.9) -> bool:
        """
        Check if L1 context is above the threshold. If so, trigger eviction.
        Returns True if an eviction occurred.
        """
        current_tokens = self.l1.get_token_count()
        threshold_tokens = self.l1.max_tokens * threshold_ratio

        if current_tokens > threshold_tokens:
            logger.info(f"Context window reaching capacity ({current_tokens}/{self.l1.max_tokens} tokens). Triggering Eviction Protocol.")
            self._evict_oldest()
            return True
        return False

    def _evict_oldest(self) -> None:
        """
        Extract the oldest messages from L1, summarize them, and move them to L3.
        """
        # Keep at least the last 2 messages for immediate context continuity
        if len(self.l1.messages) <= 2:
            logger.warning("Cannot evict: Context window is overflowing but has too few messages.")
            return

        # Evict the oldest 50% of the messages
        evict_count = len(self.l1.messages) // 2
        evicted_messages = self.l1.messages[:evict_count]

        # Remove from L1
        self.l1.messages = self.l1.messages[evict_count:]

        # Summarization simulation (In a real scenario, this calls a lightweight LLM)
        # Here we do a crude concatenation for the POC
        combined_text = " ".join([m["content"] for m in evicted_messages])
        summary = f"Archived conversation segment: {combined_text[:100]}..."

        # Append to L3
        self.l3.append_fact("Archived_Logs", summary)

        logger.debug(f"Evicted {evict_count} messages. New L1 token count: {self.l1.get_token_count()}")
