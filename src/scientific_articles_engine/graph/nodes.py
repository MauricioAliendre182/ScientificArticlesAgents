"""Node functions for the LangGraph workflow.

Each node function wraps an agent execution and updates the state.
"""

from typing import Dict

from ..agents.reviewer_agent import ReviewerAgent
from ..agents.searcher_agent import SearcherAgent
from ..agents.visualizer_agent import VisualizerAgent
from ..agents.writer_agent import WriterAgent
from ..core.state import AgentState
from ..utils.logger import get_logger

logger = get_logger(__name__)


async def searcher_node(
    state: AgentState, searcher_agent: SearcherAgent
) -> Dict:
    """Execute the Searcher agent node.

    Args:
        state: Current workflow state
        searcher_agent: Searcher agent instance

    Returns:
        State updates
    """
    logger.info("=== SEARCHER NODE ===")

    try:
        papers, outline = await searcher_agent.execute(state)

        return {
            "papers": papers,
            "outline": outline,
        }

    except Exception as e:
        logger.error(f"Searcher node failed: {e}")
        return {"error_message": str(e)}


async def writer_node(
    state: AgentState, writer_agent: WriterAgent
) -> Dict:
    """Execute the Writer agent node.

    Args:
        state: Current workflow state
        writer_agent: Writer agent instance

    Returns:
        State updates
    """
    logger.info("=== WRITER NODE ===")

    try:
        article = await writer_agent.execute(state)
        if article is None:
            raise RuntimeError("WriterAgent returned no article")

        return {
            "article": article,
        }

    except Exception as e:
        logger.error(f"Writer node failed: {e}")
        return {"error_message": str(e)}


async def reviewer_node(
    state: AgentState, reviewer_agent: ReviewerAgent
) -> Dict:
    """Execute the Reviewer agent node.

    Args:
        state: Current workflow state
        reviewer_agent: Reviewer agent instance

    Returns:
        State updates
    """
    logger.info("=== REVIEWER NODE ===")

    if state.get("error_message"):
        logger.warning("Skipping reviewer because an earlier workflow node failed")
        return {"error_message": state["error_message"]}

    try:
        review = await reviewer_agent.execute(state)

        return {
            "review": review,
            "quality_passed": review.passed,
        }

    except Exception as e:
        logger.error(f"Reviewer node failed: {e}")
        return {"error_message": str(e)}


async def visualizer_node(
    state: AgentState, visualizer_agent: VisualizerAgent
) -> Dict:
    """Execute the Visualizer agent node.

    Args:
        state: Current workflow state
        visualizer_agent: Visualizer agent instance

    Returns:
        State updates
    """
    logger.info("=== VISUALIZER NODE ===")

    try:
        visualizations = await visualizer_agent.execute(state)

        return {
            "visualizations": visualizations,
        }

    except Exception as e:
        logger.error(f"Visualizer node failed: {e}")
        return {"error_message": str(e)}


def human_review_sources_node(state: AgentState) -> Dict:
    """Human-in-the-loop node for reviewing sources and outline.

    This is an interruption point. The workflow will pause here
    and wait for human approval before continuing.

    Args:
        state: Current workflow state

    Returns:
        State updates (usually none, approval comes from external update)
    """
    logger.info("=== HUMAN REVIEW SOURCES (HITL) ===")
    logger.info(f"Found {len(state['papers'])} papers")
    logger.info("Outline generated")
    logger.info("Waiting for human approval...")

    # This node doesn't update state directly
    # The human will update searcher_approved via the workflow API
    return {}


def human_review_final_node(state: AgentState) -> Dict:
    """Human-in-the-loop node for reviewing final article.

    This is an interruption point. The workflow will pause here
    and wait for human approval before continuing.

    Args:
        state: Current workflow state

    Returns:
        State updates (usually none, approval comes from external update)
    """
    logger.info("=== HUMAN REVIEW FINAL (HITL) ===")
    logger.info(
        f"Article ready for review: {state['article'].title} "
        f"({state['article'].word_count} words)"
    )
    logger.info("Waiting for human approval...")

    # This node doesn't update state directly
    # The human will update final_approved via the workflow API
    return {}
