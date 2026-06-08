import pytest
import shutil
from pathlib import Path
from asta.memory_domain.l1_context import L1ContextWindow
from asta.memory_domain.l3_obsidian import L3ObsidianVault
from asta.memory_domain.pager import MemoryPager


from typing import Generator

@pytest.fixture
def temp_vault() -> Generator[str, None, None]:
    path = "/tmp/asta_test_vault"
    yield path
    shutil.rmtree(path, ignore_errors=True)


def test_l1_context_token_limits() -> None:
    l1 = L1ContextWindow(max_tokens=10)

    # 40 chars ~= 10 tokens
    l1.add_message("user", "a" * 20)
    assert not l1.is_overflowing()

    l1.add_message("agent", "b" * 25)
    assert l1.is_overflowing()


def test_l3_obsidian_storage(temp_vault: str) -> None:
    l3 = L3ObsidianVault(vault_path=temp_vault)

    l3.append_fact("User Preferences", "Loves Python")
    content = l3.read_entity("User Preferences")

    assert "User Preferences" in content
    assert "Loves Python" in content

    # Check Index
    index_content = Path(f"{temp_vault}/Index.md").read_text()
    assert "[[User Preferences]]" in index_content


def test_memory_eviction_protocol(temp_vault: str) -> None:
    l1 = L1ContextWindow(max_tokens=20) # Very small limit for testing
    l3 = L3ObsidianVault(vault_path=temp_vault)
    pager = MemoryPager(l1, l3)

    # Add 4 messages (approx 10 tokens each, total 40 tokens -> highly overflowing)
    for i in range(4):
        l1.add_message("user", f"message_number_{i} " * 5)

    assert l1.is_overflowing()
    assert len(l1.messages) == 4

    # Trigger pager
    evicted = pager.check_and_evict(threshold_ratio=0.9)

    assert evicted is True
    # 50% of messages should be removed
    assert len(l1.messages) == 2
    # Oldest messages are gone
    assert "message_number_0" not in l1.messages[0]["content"]

    # Check if they went to L3
    archived = l3.read_entity("Archived Logs")
    assert "Archived conversation segment" in archived
