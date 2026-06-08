from loguru import logger
from asta.core_engine.graph import AstaState
from asta.identity_domain.profile import IdentityManager
from asta.core_engine.llm_gateway import LLMGateway


class AxiomVerificationNode:
    """
    The Radically Honest Validator.
    Acts as an adversary to test proposed actions against core Identity axioms.
    """

    def __init__(self, identity_manager: IdentityManager, llm: LLMGateway) -> None:
        self.identity = identity_manager
        self.llm = llm

    async def __call__(self, state: AstaState) -> AstaState:
        """Executes the validation check on the proposed action."""

        proposed_action = state.m_active.get("proposed_action")

        if not proposed_action:
            logger.debug("No proposed action found. Bypassing validation.")
            state.m_active["validation_status"] = "PASSED"
            return state

        logger.info(f"Validating proposed action against core axioms: '{proposed_action}'")

        prompt = (
            f"You are the ASTA Radically Honest Validator.\n"
            f"Evaluate this proposed action: '{proposed_action}'\n"
            f"Against these axioms:\n"
            f"{self.identity.get_system_prompt_header()}\n"
            f"If the action is logically sound, mathematically correct, and non-sycophantic, reply ONLY with 'PASS'. "
            f"If it violates axioms (e.g. flawed math, blindly agreeing with the user), reply with 'REJECT:' followed by a radically honest explanation."
        )

        response = await self.llm.generate_completion([{"role": "system", "content": prompt}], task_type="validation")

        if response.startswith("REJECT:"):
            rejection_reason = response.replace("REJECT:", "").strip()
            logger.warning(f"Action REJECTED by Validator: {rejection_reason}")
            state.m_active["validation_status"] = "REJECTED"
            state.error_context = "axiom_violation"
            state.messages.append({"role": "agent", "content": f"[Radical Honesty Intercept]: {rejection_reason}"})
            # Clear the proposed action to force a replan
            state.m_active.pop("proposed_action", None)
        else:
            logger.debug("Action passed axiomatic validation.")
            state.m_active["validation_status"] = "PASSED"

        return state
