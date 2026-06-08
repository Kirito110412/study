from typing import Dict, Any, List
from loguru import logger
import litellm

# Litellm handles retries, load balancing, and routing seamlessly.
# By default, it will check environment variables for API keys (e.g. OPENAI_API_KEY).

class LLMGateway:
    """
    Unified router for LLM generation.
    Handles switching between "local" (e.g., Ollama), "cloud" (e.g., OpenAI),
    or "hybrid" modes based on the ASTA configuration.
    """

    def __init__(self, config: Dict[str, Any]) -> None:
        self.mode = config.get("mode", "cloud").lower()
        self.local_model = config.get("local_model", "ollama/llama3")
        self.cloud_model = config.get("cloud_model", "gpt-4o")

    def _determine_model(self, task_type: str) -> str:
        """
        Determines which model to use based on the global mode and the specific task.
        In 'hybrid' mode, simple reasoning uses local, complex generation uses cloud.
        """
        if self.mode == "local":
            return str(self.local_model)
        elif self.mode == "cloud":
            return str(self.cloud_model)
        else: # hybrid
            complex_tasks = ["skill_forge", "deep_research"]
            if task_type in complex_tasks:
                return str(self.cloud_model)
            return str(self.local_model)

    async def generate_completion(self, messages: List[Dict[str, str]], task_type: str = "general") -> str:
        """
        Executes a chat completion call using litellm.
        """
        model = self._determine_model(task_type)
        logger.debug(f"LLM Gateway routing '{task_type}' task to model: {model}")

        try:
            # We use litellm.acompletion for async non-blocking execution
            response = await litellm.acompletion(
                model=model,
                messages=messages,
                temperature=0.2, # Low temp for operating system predictability
            )
            content = response.choices[0].message.content
            return content or ""

        except Exception as e:
            logger.error(f"LLM Generation failed for model {model}: {e}")
            raise RuntimeError(f"LLM Generation Failed: {e}")
