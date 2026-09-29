"""Regression test for resuming LangGraph at an HITL checkpoint."""

from typing import TypedDict

import pytest
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph


class ResumeState(TypedDict, total=False):
    approved: bool
    final_approved: bool
    prepared: bool
    writer_runs: int
    reviewed: bool
    completed: bool


@pytest.mark.asyncio
async def test_resume_after_approval_continues_from_checkpoint():
    graph = StateGraph(ResumeState)
    graph.add_node("prepare", lambda state: {"prepared": True})
    graph.add_node("sources_review", lambda state: {})
    graph.add_node("write", lambda state: {"writer_runs": state.get("writer_runs", 0) + 1})
    graph.add_node("final_review", lambda state: {"reviewed": True})
    graph.add_node("visualize", lambda state: {"completed": True})
    graph.add_edge(START, "prepare")
    graph.add_edge("prepare", "sources_review")
    graph.add_edge("sources_review", "write")
    graph.add_edge("write", "final_review")
    graph.add_edge("final_review", "visualize")
    graph.add_edge("visualize", END)
    app = graph.compile(
        checkpointer=MemorySaver(),
        interrupt_before=["sources_review", "final_review"],
    )
    config = {"configurable": {"thread_id": "hitl-resume-test"}}

    state = None
    async for state in app.astream({"approved": False}, config, stream_mode="values"):
        pass

    assert state is not None
    assert state["prepared"] is True
    assert "completed" not in state

    config = await app.aupdate_state(config, {"approved": True})
    state = None
    async for state in app.astream(None, config, stream_mode="values"):
        pass

    assert state is not None
    assert state["writer_runs"] == 1
    assert "reviewed" not in state
    assert "completed" not in state

    thread_config = {"configurable": {"thread_id": "hitl-resume-test"}}
    latest_config = (await app.aget_state(thread_config)).config
    config = await app.aupdate_state(latest_config, {"final_approved": True})
    final_state = None
    async for final_state in app.astream(None, config, stream_mode="values"):
        pass

    assert final_state is not None
    assert final_state["approved"] is True
    assert final_state["final_approved"] is True
    assert final_state["prepared"] is True
    assert final_state["writer_runs"] == 1
    assert final_state.get("completed") is True, (
        final_state,
        (await app.aget_state(config)).next,
    )
