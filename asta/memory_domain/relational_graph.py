import json
import networkx as nx
from loguru import logger
from typing import Dict, Any, Optional

from asta.core_engine.llm_gateway import LLMGateway
from asta.memory_domain.l3_obsidian import L3ObsidianVault

class KnowledgeGraphBuilder:
    """
    Builds strict JSON entity relationships from raw text to prevent temporal
    hallucinations across long-term memory operations.
    """

    def __init__(self, llm: LLMGateway, vault: L3ObsidianVault) -> None:
        self.llm = llm
        self.vault = vault
        self.graph: nx.DiGraph = nx.DiGraph()

    async def extract_and_store(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Extracts {Subject, Action, Object, Date} from raw text using the LLMGateway
        and stores it physically as metadata inside the Obsidian L3 vault.
        """
        logger.info("Extracting relational entities from memory text...")

        prompt = (
            "You are the ASTA Relational Extraction Engine.\n"
            "Extract the primary factual relationship from the following text into a strict JSON schema.\n"
            "The JSON must have EXACTLY these keys: 'subject', 'action', 'object', 'date'.\n"
            "If the date is unknown, output 'UNKNOWN'.\n"
            "Return ONLY the raw JSON.\n\n"
            f"Text: {text}"
        )

        try:
            response = await self.llm.generate_completion(
                messages=[{"role": "system", "content": prompt}],
                task_type="relational_extraction"
            )

            # Clean possible markdown formatting from LLM response
            json_str = response.strip().strip("```json").strip("```")
            relation = json.loads(json_str)

            # Validate schema
            required_keys = {"subject", "action", "object", "date"}
            if not all(k in relation for k in required_keys):
                raise ValueError("LLM returned incomplete relational schema.")

            subject = relation["subject"]
            action = relation["action"]
            obj = relation["object"]
            date = relation["date"]

            # Update local NetworkX graph representation
            self.graph.add_node(subject)
            self.graph.add_node(obj)
            self.graph.add_edge(subject, obj, action=action, date=date)

            # Formulate the metadata block
            metadata_block = (
                f"---\n"
                f"type: relationship\n"
                f"subject: {subject}\n"
                f"action: {action}\n"
                f"object: {obj}\n"
                f"date: {date}\n"
                f"---\n"
            )

            # Append it to the relevant entity file in L3
            self.vault.append_fact(subject, f"{metadata_block}\nOriginal Text: {text}")
            logger.debug(f"Stored relationship: {subject} -[{action}]-> {obj}")

            return dict(relation)

        except Exception as e:
            logger.error(f"Relational extraction failed: {e}")
            return None
