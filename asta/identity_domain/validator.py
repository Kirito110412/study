from loguru import logger
from asta.core_engine.graph import AstaState
from asta.identity_domain.profile import IdentityManager


class AxiomVerificationNode:
    """
    The Radically Honest Validator.
    Acts as an adversary to test proposed actions against core Identity axioms.
    """

    def __init__(self, identity_manager: IdentityManager) -> None:
        self.identity = identity_manager

    async def __call__(self, state: AstaState) -> AstaState:
        """Executes the validation check on the proposed action."""

        proposed_action = state.m_active.get("proposed_action")

        if not proposed_action:
            logger.debug("No proposed action found. Bypassing validation.")
            state.m_active["validation_status"] = "PASSED"
            return state

        logger.info(f"Validating proposed action against core axioms: '{proposed_action}'")

        # Simulate LLM logic evaluating the action against the axioms
        # Specifically targeting the "Radically Honest" verification test
        is_flawed = False
        rejection_reason = ""

        # Mock LLM detecting flawed mathematics or sycophancy
        if "2 + 2 = 5" in proposed_action or "agree with" in proposed_action.lower():
            is_flawed = True
            rejection_reason = (
                "No, that will not work. 2 + 2 = 4 based on foundational arithmetic axioms. "
                "I will not agree with a flawed mathematical concept simply to placate you."
            )

        if is_flawed:
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
