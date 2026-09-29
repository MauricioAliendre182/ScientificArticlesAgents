"""Tests for serializing application models in LangGraph checkpoints."""

from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer

from src.scientific_articles_engine.graph.checkpoints import checkpoint_serializer
from src.scientific_articles_engine.models.visualization import (
    Visualization,
    VisualizationType,
)


def test_checkpoint_serializer_round_trips_paper(sample_papers):
    serializer = JsonPlusSerializer(pickle_fallback=True)

    serialized = serializer.dumps_typed({"papers": sample_papers})
    restored = serializer.loads_typed(serialized)

    assert restored["papers"] == sample_papers
    assert type(restored["papers"][0]) is type(sample_papers[0])


def test_checkpoint_serializer_allows_application_models(
    sample_article,
    sample_review,
    sample_papers,
    caplog,
):
    visualization = Visualization(
        type=VisualizationType.DIAGRAM,
        title="Test diagram",
        content="A --> B",
        format="mermaid",
    )
    payload = {
        "article": sample_article,
        "review": sample_review,
        "papers": sample_papers,
        "visualizations": [visualization],
    }

    with caplog.at_level("WARNING", logger="langgraph.checkpoint.serde.jsonplus"):
        serialized = checkpoint_serializer.dumps_typed(payload)
        restored = checkpoint_serializer.loads_typed(serialized)

    assert restored["article"] == sample_article
    assert restored["review"] == sample_review
    assert restored["papers"] == sample_papers
    assert restored["visualizations"] == [visualization]
    assert "unregistered type" not in caplog.text
