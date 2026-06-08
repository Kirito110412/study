from typing import List, Dict
from jinja2 import Template


class L1ContextWindow:
    """Manages the active prompt and enforces strict token limits."""

    # Rough estimation: 1 token ~= 4 chars in English
    CHARS_PER_TOKEN = 4

    # System template enforcing the core axioms
    SYSTEM_TEMPLATE = Template(
        "You are ASTA, an Advanced Sentient Task Architecture.\n"
        "Active Task: {{ active_task }}\n"
        "Docker Env: {{ docker_status }}\n"
        "\n"
        "Recent Memory:\n"
        "{% for msg in recent_messages %}"
        "{{ msg.role }}: {{ msg.content }}\n"
        "{% endfor %}"
    )

    def __init__(self, max_tokens: int = 4000) -> None:
        self.max_tokens = max_tokens
        self.max_chars = max_tokens * self.CHARS_PER_TOKEN
        self.messages: List[Dict[str, str]] = []

    def add_message(self, role: str, content: str) -> None:
        """Add a new message to the L1 context."""
        self.messages.append({"role": role, "content": content})

    def get_token_count(self) -> int:
        """Estimate the current token count of the messages."""
        total_chars = sum(len(m["content"]) for m in self.messages)
        return total_chars // self.CHARS_PER_TOKEN

    def is_overflowing(self) -> bool:
        """Check if the context window is exceeding the max tokens."""
        return self.get_token_count() > self.max_tokens

    def build_prompt(self, active_task: str, docker_status: str) -> str:
        """Build the final string prompt to send to the LLM."""
        return self.SYSTEM_TEMPLATE.render(
            active_task=active_task,
            docker_status=docker_status,
            recent_messages=self.messages
        )
