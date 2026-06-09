from loguru import logger
from asta.core_engine.graph import AstaGraph, AstaState
from asta.core_engine.llm_gateway import LLMGateway
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
import json


class GenerateOutlineNode:
    def __init__(self, llm: LLMGateway):
        self.llm = llm

    async def __call__(self, state: AstaState) -> AstaState:
        topic = state.m_active.get("research_topic", "Unknown")
        logger.info(f"[STORM] Generating Outline for: {topic}")

        prompt = (
            f"You are the ASTA Academic Synthesizer. Generate a strict JSON outline for a comprehensive "
            f"academic research paper on '{topic}'. Return ONLY JSON in the format: "
            f"{{\"sections\": [\"Introduction\", \"Methodology\", \"Results\", \"Conclusion\"]}}"
        )
        response = await self.llm.generate_completion([{"role": "system", "content": prompt}], task_type="deep_research")

        try:
            json_str = response.strip().strip("```json").strip("```")
            outline = json.loads(json_str)
            state.m_active["storm_outline"] = outline.get("sections", [])
            state.m_active["storm_current_section_idx"] = 0
            state.m_active["storm_drafts"] = {}
            logger.debug(f"Outline generated: {state.m_active['storm_outline']}")
        except Exception as e:
            logger.error(f"Failed to parse outline JSON: {e}")
            state.error_context = "storm_outline_failure"

        return state


class SourceScraperNode:
    """Mock node simulating the scraping of 50 URLs via MCP or VLM Actuation."""
    async def __call__(self, state: AstaState) -> AstaState:
        idx = state.m_active.get("storm_current_section_idx", 0)
        sections = state.m_active.get("storm_outline", [])

        if idx < len(sections):
            current_section = sections[idx]
            logger.info(f"[STORM] Actuating browser to scrape sources for: {current_section}")
            # Mock the scraping process
            state.m_active[f"sources_{current_section}"] = f"Raw scraped academic data regarding {current_section}..."

        return state


class DraftSectionsNode:
    def __init__(self, llm: LLMGateway):
        self.llm = llm

    async def __call__(self, state: AstaState) -> AstaState:
        idx = state.m_active.get("storm_current_section_idx", 0)
        sections = state.m_active.get("storm_outline", [])

        if idx < len(sections):
            current_section = sections[idx]
            sources = state.m_active.get(f"sources_{current_section}", "")
            logger.info(f"[STORM] Drafting section: {current_section}")

            prompt = (
                f"Draft the '{current_section}' section of an academic paper using this source data: {sources}. "
                f"Include formal citations."
            )
            draft = await self.llm.generate_completion([{"role": "system", "content": prompt}], task_type="deep_research")

            drafts = state.m_active.get("storm_drafts", {})
            drafts[current_section] = draft
            state.m_active["storm_drafts"] = drafts

            # Reset correction attempts for the new section
            state.m_active["storm_correction_attempts"] = 0

        return state


class SelfCorrectionNode:
    def __init__(self, llm: LLMGateway):
        self.llm = llm

    async def __call__(self, state: AstaState) -> AstaState:
        idx = state.m_active.get("storm_current_section_idx", 0)
        sections = state.m_active.get("storm_outline", [])

        if idx < len(sections):
            current_section = sections[idx]
            drafts = state.m_active.get("storm_drafts", {})
            current_draft = drafts.get(current_section, "")

            attempts = state.m_active.get("storm_correction_attempts", 0)

            logger.info(f"[STORM] Self-Correcting section: {current_section} (Attempt {attempts + 1})")

            prompt = (
                f"Review this academic draft for '{current_section}':\n{current_draft}\n"
                f"Does it have hallucinations or lack citations? Reply 'PASS' if perfect, or 'REJECT' if flawed."
            )
            eval_response = await self.llm.generate_completion([{"role": "system", "content": prompt}], task_type="deep_research")

            if "REJECT" in eval_response.upper():
                if attempts < 2:
                    logger.warning("Draft rejected by Self-Correction. Looping back.")
                    state.m_active["storm_needs_rewrite"] = True
                    state.m_active["storm_correction_attempts"] = attempts + 1
                else:
                    logger.error("Draft rejected, but maximum correction attempts reached. Forcing progression.")
                    state.m_active["storm_needs_rewrite"] = False
                    state.m_active["storm_current_section_idx"] = idx + 1 # Move to next section
            else:
                logger.debug("Draft passed self-correction.")
                state.m_active["storm_needs_rewrite"] = False
                state.m_active["storm_current_section_idx"] = idx + 1 # Move to next section

        return state


class CompilePDFNode:
    """Compiles the drafted sections into a formatted PDF using reportlab."""
    async def __call__(self, state: AstaState) -> AstaState:
        topic = state.m_active.get("research_topic", "Unknown")
        safe_topic = topic.replace(" ", "_")

        pdf_path = f"/tmp/{safe_topic}_Final_Research.pdf"
        logger.info(f"[STORM] Compiling final academic PDF to {pdf_path}...")

        c = canvas.Canvas(pdf_path, pagesize=letter)
        width, height = letter

        c.setFont("Helvetica-Bold", 16)
        c.drawString(inch, height - inch, f"Research Report: {topic}")

        c.setFont("Helvetica", 12)
        y_position = height - (inch * 1.5)

        sections = state.m_active.get("storm_outline", [])
        drafts = state.m_active.get("storm_drafts", {})

        for section in sections:
            if y_position < inch * 2:
                c.showPage()
                y_position = height - inch

            c.setFont("Helvetica-Bold", 14)
            c.drawString(inch, y_position, section)
            y_position -= 20

            c.setFont("Helvetica", 11)
            content = drafts.get(section, "No content drafted.")
            # Simple text wrapping simulation
            lines = content.split('\n')
            for line in lines:
                if y_position < inch * 1.5:
                    c.showPage()
                    y_position = height - inch
                c.drawString(inch, y_position, line[:80]) # Hard cutoff for MVP
                y_position -= 15

            y_position -= 20

        c.save()
        state.m_active["storm_final_pdf"] = pdf_path
        return state


def build_storm_protocol_graph(llm: LLMGateway) -> AstaGraph:
    """
    Builds the specialized multi-stage graph for the Academic Synthesizer.
    """
    graph = AstaGraph()

    # Add Nodes
    graph.add_node("generate_outline", GenerateOutlineNode(llm))
    graph.add_node("scrape_sources", SourceScraperNode())
    graph.add_node("draft_section", DraftSectionsNode(llm))
    graph.add_node("self_correction", SelfCorrectionNode(llm))
    graph.add_node("compile_pdf", CompilePDFNode())

    # Conditional Router for the Drafting Loop
    def drafting_router(state: AstaState) -> str:
        idx = state.m_active.get("storm_current_section_idx", 0)
        sections = state.m_active.get("storm_outline", [])
        needs_rewrite = state.m_active.get("storm_needs_rewrite", False)

        if needs_rewrite:
            return "draft_section" # Loop back and rewrite

        if idx < len(sections):
            return "scrape_sources" # Loop to next section

        return "compile_pdf" # All sections done, compile

    # Wire Edges
    graph.add_edge("generate_outline", "scrape_sources")
    graph.add_edge("scrape_sources", "draft_section")
    graph.add_edge("draft_section", "self_correction")
    graph.add_conditional_edge("self_correction", drafting_router)
    graph.add_edge("compile_pdf", "END")

    graph.set_entry_point("generate_outline")

    return graph
