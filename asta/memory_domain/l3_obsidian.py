from pathlib import Path
from datetime import datetime
from loguru import logger


class L3ObsidianVault:
    """Manages long-term disk storage using bidirectional Markdown files."""

    def __init__(self, vault_path: str = "~/.asta/vault") -> None:
        self.vault_path = Path(vault_path).expanduser()
        self.vault_path.mkdir(parents=True, exist_ok=True)

        # Ensure an index file exists
        self.index_file = self.vault_path / "Index.md"
        if not self.index_file.exists():
            self.index_file.write_text("# ASTA Memory Index\n\n")

    def append_fact(self, entity_name: str, fact: str) -> None:
        """
        Append a summarized fact to an entity's markdown file.
        Creates the file if it doesn't exist.
        """
        filename = f"{entity_name.replace(' ', '_')}.md"
        filepath = self.vault_path / filename

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = f"\n- **[{timestamp}]**: {fact}"

        is_new = not filepath.exists()

        with open(filepath, "a", encoding="utf-8") as f:
            if is_new:
                f.write(f"# {entity_name}\n")
                # Update Index
                with open(self.index_file, "a", encoding="utf-8") as idx:
                    idx.write(f"- [[{entity_name}]]\n")

            f.write(entry)

        logger.debug(f"Archived fact to L3 Vault: {filename}")

    def read_entity(self, entity_name: str) -> str:
        """Read all facts associated with an entity."""
        filename = f"{entity_name.replace(' ', '_')}.md"
        filepath = self.vault_path / filename
        if filepath.exists():
            return filepath.read_text(encoding="utf-8")
        return ""
