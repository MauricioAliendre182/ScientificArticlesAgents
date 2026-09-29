# Scientific Articles Engine

A multi-agent system for generating comprehensive scientific articles using LangGraph and Python, with Human-in-the-Loop (HITL) capabilities.

## Features

- **Multi-Agent Architecture**: Four specialized agents (Searcher, Writer, Reviewer, Visualizer) collaborate to create high-quality articles
- **Human-in-the-Loop (HITL)**: Two approval points for quality control
- **Automatic Paper Search**: Searches arXiv and Semantic Scholar for relevant papers
- **Iterative Refinement**: Writer-Reviewer feedback loop (up to 3 revisions)
- **Visualization Generation**: Automatic creation of tables, diagrams, and flowcharts
- **SOLID Principles**: Clean, maintainable, extensible architecture
- **State Persistence**: PostgreSQL checkpointing for resumable workflows

## Architecture

```
[Start] → Searcher → HITL(1) → Writer ⇄ Reviewer → HITL(2) → Visualizer → [End]
                                    ↑        ↓
                                    └────────┘
                              (feedback loop, max 3 attempts)
```

### Agents

1. **SearcherAgent**: Searches academic databases and generates article outline
2. **WriterAgent**: Drafts articles and handles revisions
3. **ReviewerAgent**: Evaluates articles across 4 criteria (rigor, citations, coherence, writing)
4. **VisualizerAgent**: Generates tables, diagrams, and visualizations

## Installation

### Requirements

- Python 3.10+
- PostgreSQL (optional, for production checkpointing)
- OpenAI or Anthropic API key

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd scientific-articles-engine
```

2. Install dependencies:
```bash
pip install -e .
# or for development:
pip install -e ".[dev]"
```

3. Configure environment:
```bash
cp .env.example .env
# Edit .env with your API keys
```

`SEMANTIC_SCHOLAR_API_KEY` is optional, but recommended if unauthenticated
requests are throttled. Request a key from Semantic Scholar and place it in
`.env`; do not commit the key.

4. Configure settings:
```bash
# Edit config.yaml with your preferences
```

## Usage

### Basic Usage

Generate an article on a topic:
```bash
scientific-articles-engine generate "Transformer Architectures in NLP"
```

### Advanced Options

```bash
# Specify output file
scientific-articles-engine generate "Neural Networks" --output my_article.md

# Use custom config
scientific-articles-engine --config custom_config.yaml generate "Deep Learning"

# Auto-approve HITL points (for testing)
scientific-articles-engine generate "Machine Learning" --auto-approve

# Custom thread ID for checkpointing
scientific-articles-engine generate "AI Ethics" --thread-id run_001
```

### Validate Configuration

```bash
scientific-articles-engine validate-config config.yaml
```

## Configuration

Edit `config.yaml` to customize:

```yaml
llm:
  provider: "openai"  # or "anthropic"
  model: "gpt-4"
  temperature: 0.7

agents:
  max_papers_per_source: 10
  min_word_count: 1000
  max_word_count: 5000
  quality_threshold: 7.0
  max_revisions: 3

database:
  enabled: true
  host: "localhost"
  port: 5432
```

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run unit tests only
pytest tests/unit/

# Run with coverage
pytest --cov=src/scientific_articles_engine --cov-report=html

# Run specific test file
pytest tests/unit/test_agents/test_writer_agent.py
```

### Code Quality

```bash
# Format code
black src/ tests/

# Lint code
ruff check src/

# Type checking
mypy src/
```

## SOLID Principles

This project follows SOLID principles:

- **Single Responsibility**: Each agent has one job
- **Open/Closed**: Extend via inheritance without modifying existing code
- **Liskov Substitution**: All agents implement common `BaseAgent` interface
- **Interface Segregation**: Protocols define minimal service contracts
- **Dependency Inversion**: Agents depend on abstractions via `AgentFactory`

See [ARCHITECTURE.md](docs/ARCHITECTURE.md) for detailed documentation.

## Human-in-the-Loop (HITL)

The workflow includes two HITL checkpoints:

1. **After Search**: Review papers and outline before writing
2. **After Review**: Approve final article before visualization

At each checkpoint, the workflow pauses and waits for approval. You can:
- Approve and continue
- Reject and restart (first checkpoint)
- Reject and terminate (second checkpoint)

## Examples

### Example 1: Generate Article on Transformers

```bash
scientific-articles-engine generate "Attention Mechanisms in Transformers"
```

Output:
- Searches arXiv and Semantic Scholar
- Finds relevant papers
- Generates outline
- **HITL Checkpoint**: You review and approve
- Writes article draft
- Reviews and revises (up to 3 times)
- **HITL Checkpoint**: You review final article
- Generates visualizations
- Saves to `Attention_Mechanisms_in_Transformers.md`

### Example 2: Custom Configuration

```python
# Python API usage
from scientific_articles_engine.config import load_config
from scientific_articles_engine.graph.workflow import create_workflow
from scientific_articles_engine.core.state import create_initial_state

config = load_config("custom_config.yaml")
workflow = create_workflow(config)

initial_state = create_initial_state("Machine Learning Basics")
workflow_config = {"configurable": {"thread_id": "run_001"}}

async for state in workflow.astream(initial_state, workflow_config):
    # Handle HITL checkpoints
    if "papers" in state and not state.get("searcher_approved"):
        # Review papers and approve
        state["searcher_approved"] = True
```

## Troubleshooting

### API Key Issues

```bash
# Check if API key is set
echo $OPENAI_API_KEY

# Set API key
export OPENAI_API_KEY=your_key_here
```

### Database Connection

```bash
# Test PostgreSQL connection
psql -h localhost -U postgres -d scientific_articles_engine

# Create database if needed
createdb scientific_articles_engine
```

### Import Errors

```bash
# Reinstall in editable mode
pip install -e .
```

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Ensure all tests pass
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Citation

If you use this project in your research, please cite:

```bibtex
@software{scientific_articles_engine,
  title={Scientific Articles Engine: Multi-Agent Article Generation},
  author={Your Name},
  year={2024},
  url={https://github.com/yourusername/scientific-articles-engine}
}
```

## Acknowledgments

- Built with [LangGraph](https://github.com/langchain-ai/langgraph)
- Paper search via [arXiv](https://arxiv.org/) and [Semantic Scholar](https://www.semanticscholar.org/)
- LLM integration via [LangChain](https://github.com/langchain-ai/langchain)
