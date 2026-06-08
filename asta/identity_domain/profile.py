import yaml
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Any
from loguru import logger

@dataclass
class IdentityProfile:
    name: str = "Asta"
    role: str = "Autonomous OS"
    core_axioms: List[str] = field(default_factory=list)
    linguistic_mastery: Dict[str, Any] = field(default_factory=dict)
    directives: Dict[str, bool] = field(default_factory=dict)

class IdentityManager:
    """Loads and manages the baseline personality and axioms of the ASTA OS."""

    def __init__(self, config_path: str = "asta/identity_domain/baseline.yaml") -> None:
        self.config_path = Path(config_path)
        self.profile = self._load_profile()

    def _load_profile(self) -> IdentityProfile:
        """Parses the YAML configuration into the IdentityProfile dataclass."""
        if not self.config_path.exists():
            logger.warning(f"Identity baseline not found at {self.config_path}. Using defaults.")
            return IdentityProfile()

        with open(self.config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        profile = IdentityProfile(
            name=data.get("name", "Asta"),
            role=data.get("role", "Autonomous OS"),
            core_axioms=data.get("core_axioms", []),
            linguistic_mastery=data.get("linguistic_mastery", {}),
            directives=data.get("directives", {})
        )
        logger.info(f"Loaded identity profile for '{profile.name}' ({profile.role})")
        return profile

    def get_system_prompt_header(self) -> str:
        """Generates the axiomatic header to be injected into the L1 context."""
        axioms = "\n- ".join(self.profile.core_axioms)
        return (
            f"You are {self.profile.name}, {self.profile.role}.\n"
            f"Style: {self.profile.linguistic_mastery.get('style', 'direct')}\n\n"
            f"CORE AXIOMS:\n- {axioms}\n"
        )
