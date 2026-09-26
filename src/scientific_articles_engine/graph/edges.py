"""Conditional edge functions for routing in the LangGraph workflow."""

from typing import Literal

from ..core.state import AgentState
from ..utils.logger import get_logger

logger = get_logger(__name__)


def route_after_searcher(
    state: AgentState,
) -> Literal["human_review_sources", "searcher"]:
    """Route after Searcher node.

    If this is the first run, go to human review.
    Otherwise, this means human rejected and we're re-searching.

    Args:
        state: Current workflow state

    Returns:
        Next node name
    """
    # Always go to human review after searcher completes
    return "human_review_sources"


def route_after_human_sources(
    state: AgentState,
) -> Literal["writer", "searcher"]:
    """Route after human reviews sources.

    Args:
        state: Current workflow state

    Returns:
        Next node name: "writer" if approved, "searcher" if rejected
    """
    if state.get("searcher_approved", False):
        logger.info("Sources approved by human → proceeding to Writer")
        return "writer"
    else:
        logger.info("Sources rejected by human → returning to Searcher")
        return "searcher"


def route_after_reviewer(
    state: AgentState,
) -> Literal["writer", "human_review_final", "__end__"]:
    """Route after Reviewer node.

    Implements the Writer-Reviewer feedback loop with max revision limit.

    Args:
        state: Current workflow state

    Returns:
        Next node name:
        - "writer": If revision needed and attempts remaining
        - "human_review_final": If quality passed
        - "__end__": If max revisions exceeded
    """
    max_revisions = 3  # This should come from config, but hardcoded for now
    revision_count = state.get("revision_count", 0)

    if state.get("error_message"):
        logger.error("Stopping workflow after node failure: %s", state["error_message"])
        return "__end__"

    if state.get("quality_passed", False):
        logger.info("Article passed quality review → Human review")
        return "human_review_final"

    # Check if we've exceeded max revisions
    if revision_count >= max_revisions:
        logger.warning(
            f"Max revisions ({max_revisions}) exceeded → Ending workflow"
        )
        return "__end__"

    # Need revision and have attempts remaining
    logger.info(
        f"Article needs revision (attempt {revision_count + 1}/{max_revisions}) → Writer"
    )
    return "writer"


def route_after_human_final(
    state: AgentState,
) -> Literal["visualizer", "__end__"]:
    """Route after human reviews final article.

    Args:
        state: Current workflow state

    Returns:
        Next node name: "visualizer" if approved, "__end__" if rejected
    """
    if state.get("final_approved", False):
        logger.info("Final article approved → Proceeding to Visualizer")
        return "visualizer"
    else:
        logger.info("Final article rejected → Ending workflow")
        return "__end__"


def increment_revision_count(state: AgentState) -> AgentState:
    """Increment revision count before routing back to writer.

    This is called as a transform on the edge from reviewer to writer.

    Args:
        state: Current workflow state

    Returns:
        Updated state with incremented revision count
    """
    state["revision_count"] = state.get("revision_count", 0) + 1
    return state
