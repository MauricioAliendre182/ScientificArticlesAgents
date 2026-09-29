"""Main LangGraph workflow for the Scientific Articles Engine.

This module defines the complete multi-agent workflow with HITL capabilities.

Workflow structure:
[Start] → Searcher → HITL(1) → Writer ⇄ Reviewer → HITL(2) → Visualizer → [End]
                                     ↑        ↓
                                     └────────┘
                               (feedback loop, max 3 attempts)
"""

from functools import partial
from typing import Any, Dict

from langgraph.graph import END, START, StateGraph

from ..config import EngineConfig
from ..core.state import AgentState
from ..services import AgentFactory
from ..utils.logger import get_logger
from .checkpoints import get_async_checkpointer_from_config, get_checkpointer_from_config
from .edges import (
    increment_revision_count,
    route_after_human_final,
    route_after_human_sources,
    route_after_reviewer,
    route_after_searcher,
)
from .nodes import (
    human_review_final_node,
    human_review_sources_node,
    reviewer_node,
    searcher_node,
    visualizer_node,
    writer_node,
)

logger = get_logger(__name__)


def create_workflow(config: EngineConfig, checkpointer=None) -> StateGraph:
    """Create the complete LangGraph workflow with HITL.

    Args:
        config: Engine configuration

    Returns:
        Compiled StateGraph ready for execution
    """
    logger.info("Creating Scientific Articles Engine workflow")

    # Create agent factory
    factory = AgentFactory(config)

    # Create agents
    searcher = factory.create_searcher()
    writer = factory.create_writer()
    reviewer = factory.create_reviewer()
    visualizer = factory.create_visualizer()

    # Create workflow graph
    workflow = StateGraph(AgentState)

    # Add nodes with partial functions to inject agents
    workflow.add_node("searcher", partial(searcher_node, searcher_agent=searcher))
    workflow.add_node("human_review_sources", human_review_sources_node)
    workflow.add_node("writer", partial(writer_node, writer_agent=writer))
    workflow.add_node("reviewer", partial(reviewer_node, reviewer_agent=reviewer))
    workflow.add_node("increment_revision", increment_revision_count)
    workflow.add_node("human_review_final", human_review_final_node)
    workflow.add_node("visualizer", partial(visualizer_node, visualizer_agent=visualizer))

    # Define edges
    # Start → Searcher
    workflow.add_edge(START, "searcher")

    # Searcher → Human Review (HITL 1)
    workflow.add_conditional_edges(
        "searcher",
        route_after_searcher,
        {
            "human_review_sources": "human_review_sources",
            "searcher": "searcher",  # In case of re-search
        },
    )

    # Human Review Sources → Writer or back to Searcher
    workflow.add_conditional_edges(
        "human_review_sources",
        route_after_human_sources,
        {
            "writer": "writer",
            "searcher": "searcher",
        },
    )

    # Writer → Reviewer
    workflow.add_edge("writer", "reviewer")

    # Reviewer → Writer (revision) or Human Review (passed) or END (max revisions)
    workflow.add_conditional_edges(
        "reviewer",
        partial(route_after_reviewer, max_revisions=config.agents.max_revisions),
        {
            "writer": "increment_revision",
            "human_review_final": "human_review_final",
            "__end__": END,
        },
    )

    # Increment revision count → Writer (closes the feedback loop)
    workflow.add_edge("increment_revision", "writer")

    # Human Review Final → Visualizer or END
    workflow.add_conditional_edges(
        "human_review_final",
        route_after_human_final,
        {
            "visualizer": "visualizer",
            "__end__": END,
        },
    )

    # Visualizer → END
    workflow.add_edge("visualizer", END)

    # Create checkpointer
    if checkpointer is None:
        checkpointer = get_checkpointer_from_config(config.to_dict())

    # Compile workflow with HITL interruption points
    compiled_workflow = workflow.compile(
        checkpointer=checkpointer,
        interrupt_before=["human_review_sources", "human_review_final"],
    )

    logger.info("Workflow created successfully with HITL interruption points")

    return compiled_workflow


async def create_async_workflow(config: EngineConfig) -> StateGraph:
    """Create a workflow with an async PostgreSQL checkpointer."""
    checkpointer = await get_async_checkpointer_from_config(config.to_dict())
    return create_workflow(config, checkpointer=checkpointer)


def create_workflow_for_testing() -> StateGraph:
    """Create a simplified workflow for testing without database.

    Returns:
        Compiled StateGraph with in-memory checkpointing
    """
    from ..config import AgentConfig, DatabaseConfig, EngineConfig, LLMConfig

    # Create minimal config for testing
    config = EngineConfig(
        llm=LLMConfig(
            provider="openai",
            model="gpt-4",
            api_key="test_key",
        ),
        agents=AgentConfig(),
        database=DatabaseConfig(enabled=False),
    )

    return create_workflow(config)


async def run_workflow_with_hitl(
    workflow: StateGraph,
    topic: str,
    config_dict: Dict[str, Any],
) -> Dict:
    """Run the workflow with Human-in-the-Loop interactions.

    This is a helper function demonstrating HITL workflow execution.

    Args:
        workflow: Compiled workflow graph
        topic: Research topic
        config_dict: Configuration dictionary with thread_id for checkpointing

    Returns:
        Final state after workflow completion

    Example:
        >>> workflow = create_workflow(config)
        >>> final_state = await run_workflow_with_hitl(
        ...     workflow, "Transformer Architectures", {"thread_id": "run_1"}
        ... )
    """
    from ..core.state import create_initial_state

    # Create initial state
    initial_state = create_initial_state(topic)

    # Run until first interruption (human_review_sources)
    logger.info("Starting workflow (will pause at HITL points)...")
    state = None
    async for s in workflow.astream(initial_state, config_dict):
        state = s
        logger.info(f"Current node: {list(s.keys())}")

    # At this point, workflow is paused at human_review_sources
    # In a real application, you would:
    # 1. Display papers and outline to user
    # 2. Get user approval
    # 3. Resume with updated state

    # For demonstration, we'll auto-approve
    logger.info("HITL Point 1: Reviewing sources...")
    logger.info("Auto-approving sources for demonstration")

    # Resume with approval
    state["searcher_approved"] = True
    async for s in workflow.astream(state, config_dict):
        state = s
        logger.info(f"Current node: {list(s.keys())}")

    # Workflow will run through Writer-Reviewer loop and pause at human_review_final
    logger.info("HITL Point 2: Reviewing final article...")
    logger.info("Auto-approving final article for demonstration")

    # Resume with final approval
    state["final_approved"] = True
    async for s in workflow.astream(state, config_dict):
        state = s
        logger.info(f"Current node: {list(s.keys())}")

    logger.info("Workflow completed!")
    return state
