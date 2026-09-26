# Architecture Documentation

## Overview

The Scientific Articles Engine is a multi-agent system built on LangGraph that generates comprehensive scientific articles through collaborative agent workflows with human oversight.

## Design Principles

### SOLID Principles

#### 1. Single Responsibility Principle (SRP)

Each component has one well-defined responsibility:

- **SearcherAgent**: Only searches papers and generates outlines
- **WriterAgent**: Only writes and revises articles
- **ReviewerAgent**: Only evaluates article quality
- **VisualizerAgent**: Only generates visualizations

Each service handles one external integration:
- **LLMService**: LLM interactions
- **ArxivService**: arXiv API
- **SemanticScholarService**: Semantic Scholar API

#### 2. Open/Closed Principle (OCP)

The system is open for extension but closed for modification:

```python
# Adding a new agent doesn't require modifying existing code
class SummarizerAgent(BaseAgent[Summary]):
    async def execute(self, state: AgentState) -> Summary:
        # New functionality
        pass

# Add to workflow without changing existing agents
workflow.add_node("summarizer", summarizer_node)
```

#### 3. Liskov Substitution Principle (LSP)

All agents implement the `BaseAgent[T]` interface and are interchangeable:

```python
def process_agent(agent: BaseAgent, state: AgentState):
    return agent.execute(state)

# Works with any agent
process_agent(searcher_agent, state)
process_agent(writer_agent, state)
process_agent(reviewer_agent, state)
```

#### 4. Interface Segregation Principle (ISP)

Services implement focused protocols:

```python
# Clients only depend on methods they use
class LLMServiceProtocol(Protocol):
    async def generate(self, prompt: str) -> str: ...
    async def generate_with_structure(self, prompt: str, schema: Dict) -> Dict: ...

class PaperSearchServiceProtocol(Protocol):
    async def search(self, query: str, max_results: int) -> List[Paper]: ...
    def get_service_name(self) -> str: ...
```

#### 5. Dependency Inversion Principle (DIP)

High-level agents depend on abstractions (protocols), not concrete implementations:

```python
class WriterAgent(BaseAgent[Article]):
    def __init__(self, llm_service: LLMServiceProtocol, ...):
        # Depends on protocol, not concrete LLMService
        self.llm_service = llm_service

# Factory injects dependencies
factory = AgentFactory(config)
writer = factory.create_writer()  # Injects concrete LLMService
```

## System Architecture

### Component Diagram

```
┌─────────────────────────────────────────────────────┐
│                   CLI (main.py)                      │
└─────────────────────┬───────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────┐
│              Workflow (workflow.py)                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐          │
│  │ Searcher │→→│  Writer  │←→│ Reviewer │          │
│  └──────────┘  └──────────┘  └──────────┘          │
│       ↓             ↓              ↓                 │
│  ┌─────────────────────────────────────┐            │
│  │      Visualizer                     │            │
│  └─────────────────────────────────────┘            │
└───────────┬─────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────┐
│           AgentFactory (DI Container)                │
└─────────────┬───────────────────────────────────────┘
              │
    ┌─────────┴─────────┬─────────────┐
    ▼                   ▼             ▼
┌──────────┐      ┌──────────┐  ┌──────────┐
│LLMService│      │  arXiv   │  │ Semantic │
│          │      │ Service  │  │ Scholar  │
└──────────┘      └──────────┘  └──────────┘
```

### Data Flow

```
1. User Input (topic)
   ↓
2. SearcherAgent
   ├─→ ArxivService.search()
   ├─→ SemanticScholarService.search()
    ├─→ PaperCacheService (PostgreSQL, normalized exact-query match; 30-day freshness)
   ├─→ Deduplicate papers
   └─→ LLMService.generate(outline)
   ↓
3. HITL Checkpoint #1 (Review Sources)
   ↓ (if approved)
4. WriterAgent
   └─→ LLMService.generate(article)
   ↓
5. ReviewerAgent
   └─→ LLMService.generate_with_structure(review)
   ↓
6. Decision:
   ├─→ If passed: HITL Checkpoint #2
   └─→ If failed: Return to WriterAgent (max 3 times)
   ↓
7. HITL Checkpoint #2 (Review Final)
   ↓ (if approved)
8. VisualizerAgent
   └─→ LLMService.generate(visualizations)
   ↓
9. Output (article + visualizations)
```

## Core Components

The searcher runs arXiv and Semantic Scholar independently. Successful live
results are cached in PostgreSQL. If a provider fails or live searches return
no papers, the searcher supplements results from the cache; cache read/write
errors are non-fatal. Queries are matched after case and whitespace
normalization, and entries older than 30 days are ignored.

### 1. State Management

**File**: `core/state.py`

```python
class AgentState(TypedDict):
    # Core data
    topic: str
    papers: List[Paper]
    outline: Optional[str]
    article: Optional[Article]
    review: Optional[ReviewResult]
    visualizations: List[Visualization]

    # Control flow
    revision_count: int
    quality_passed: bool
    searcher_approved: bool  # HITL flag
    final_approved: bool     # HITL flag

    # Error handling
    error_message: Optional[str]

    # LangGraph messages
    messages: Annotated[List[BaseMessage], add_messages]
```

State flows through the workflow and is modified by each agent.

### 2. Agent Base Class

**File**: `core/agent_base.py`

```python
class BaseAgent(ABC, Generic[T]):
    def __init__(self, llm_service: LLMServiceProtocol, config: Dict, agent_name: str):
        self.llm_service = llm_service
        self.config = config
        self.agent_name = agent_name

    @abstractmethod
    async def execute(self, state: AgentState) -> T:
        """Execute agent task, return agent-specific output"""
        pass

    @abstractmethod
    def get_prompt_template(self) -> str:
        """Get agent's prompt template"""
        pass
```

All agents inherit from `BaseAgent` and implement `execute()`.

### 3. Agent Implementations

#### SearcherAgent

**Responsibilities**:
- Search arXiv and Semantic Scholar in parallel
- Deduplicate papers by title
- Generate article outline using LLM

**Output**: `Tuple[List[Paper], str]` (papers and outline)

**Key Methods**:
- `_search_all_sources()`: Parallel API calls
- `_deduplicate_papers()`: Remove duplicates
- `_generate_outline()`: LLM-based outline generation

#### WriterAgent

**Responsibilities**:
- Create initial article draft from outline
- Revise articles based on reviewer feedback
- Parse LLM output into structured Article objects

**Output**: `Article`

**Modes**:
1. **Draft mode**: No review in state → create new article
2. **Revision mode**: Review exists → revise based on feedback

**Key Methods**:
- `_create_draft()`: Generate initial article
- `_revise_article()`: Apply reviewer feedback
- `_parse_article()`: Convert text to structured Article

#### ReviewerAgent

**Responsibilities**:
- Evaluate articles across 4 criteria
- Provide structured feedback and scores
- Determine pass/fail based on threshold

**Output**: `ReviewResult`

**Criteria**:
1. Scientific Rigor (accuracy, depth)
2. Citation Quality (appropriate references)
3. Coherence (logical flow)
4. Writing Quality (clarity, style)

**Key Methods**:
- `_review_article()`: Generate structured review
- Uses `generate_with_structure()` for consistent JSON output

#### VisualizerAgent

**Responsibilities**:
- Identify visualization opportunities
- Generate tables (Markdown)
- Generate diagrams (Mermaid)

**Output**: `List[Visualization]`

**Process**:
1. Analyze article for viz opportunities
2. Generate each visualization
3. Format in appropriate markup (Markdown/Mermaid)

### 4. Services Layer

#### LLMService

Abstracts LLM interactions using LangChain:

```python
class LLMService(BaseService, LLMServiceProtocol):
    async def generate(self, prompt: str) -> str:
        # Simple text generation
        pass

    async def generate_with_structure(self, prompt: str, schema: Dict) -> Dict:
        # Structured JSON output
        pass

    async def generate_with_system_message(self, system: str, prompt: str) -> str:
        # With system message
        pass
```

Supports:
- OpenAI (GPT-4, GPT-3.5)
- Anthropic (Claude)

#### ArxivService / SemanticScholarService

Wrap API clients and convert to `Paper` model:

```python
class ArxivService(BaseService, PaperSearchServiceProtocol):
    async def search(self, query: str, max_results: int) -> List[Paper]:
        # Search arXiv
        # Convert results to Paper objects
        pass
```

### 5. LangGraph Workflow

**File**: `graph/workflow.py`

#### Graph Structure

```python
workflow = StateGraph(AgentState)

# Nodes
workflow.add_node("searcher", searcher_node)
workflow.add_node("human_review_sources", human_review_sources_node)
workflow.add_node("writer", writer_node)
workflow.add_node("reviewer", reviewer_node)
workflow.add_node("human_review_final", human_review_final_node)
workflow.add_node("visualizer", visualizer_node)

# Edges
workflow.add_edge(START, "searcher")
workflow.add_conditional_edges("searcher", route_after_searcher, ...)
workflow.add_conditional_edges("reviewer", route_after_reviewer, ...)
workflow.add_edge("visualizer", END)

# HITL interruption points
compiled = workflow.compile(
    checkpointer=checkpointer,
    interrupt_before=["human_review_sources", "human_review_final"]
)
```

#### Routing Logic

**File**: `graph/edges.py`

1. **After Searcher**: Always → human_review_sources
2. **After Human Sources**:
   - Approved → writer
   - Rejected → searcher (re-search)
3. **After Reviewer**:
   - Passed → human_review_final
   - Failed (attempts < max) → writer (revision)
   - Failed (attempts >= max) → END
4. **After Human Final**:
   - Approved → visualizer
   - Rejected → END

#### Writer-Reviewer Loop

```python
def route_after_reviewer(state: AgentState) -> Literal["writer", "human_review_final", "__end__"]:
    if state["quality_passed"]:
        return "human_review_final"

    if state["revision_count"] >= 3:
        return "__end__"  # Max revisions exceeded

    return "writer"  # Revise again
```

Each revision increments `revision_count` in state.

### 6. Human-in-the-Loop (HITL)

#### Implementation

HITL is implemented using LangGraph's `interrupt_before`:

```python
compiled = workflow.compile(
    interrupt_before=["human_review_sources", "human_review_final"]
)
```

#### HITL Flow

```python
# Run until interruption
async for state in workflow.astream(initial_state, config):
    pass  # Pauses at interrupt point

# Display to human, get approval
approval = get_human_approval()

# Update state and resume
state["searcher_approved"] = approval
async for state in workflow.astream(state, config):
    pass  # Continues from checkpoint
```

#### Checkpointing

Uses PostgreSQL for production:

```python
from langgraph.checkpoint.postgres import PostgresSaver

checkpointer = PostgresSaver.from_conn_string(connection_string)
```

Or in-memory for testing:

```python
from langgraph.checkpoint.memory import MemorySaver

checkpointer = MemorySaver()
```

## Configuration Management

**File**: `config.py`

Uses Pydantic for validation:

```python
class EngineConfig(BaseModel):
    llm: LLMConfig
    agents: AgentConfig
    database: DatabaseConfig

    @classmethod
    def from_yaml(cls, path: str) -> "EngineConfig":
        # Load and validate YAML
        pass
```

Configuration sources (priority order):
1. Environment variables (API keys, passwords)
2. config.yaml (structure and defaults)
3. Code defaults (fallback values)

## Error Handling

### Exception Hierarchy

```
EngineException (base)
├── AgentExecutionException
├── ServiceException
├── ValidationException
├── ConfigurationException
└── MaxRevisionsExceededException
```

### Error Flow

1. **Service Level**: Catch API errors, wrap in `ServiceException`
2. **Agent Level**: Catch execution errors, wrap in `AgentExecutionException`
3. **Workflow Level**: Log errors, optionally retry or terminate
4. **CLI Level**: Display user-friendly error messages

## Testing Strategy

### Unit Tests

Test individual components in isolation:

```python
# tests/unit/test_agents/test_writer_agent.py
async def test_writer_creates_draft(mock_llm_service):
    writer = WriterAgent(llm_service=mock_llm_service, config={})
    article = await writer.execute(state)
    assert article.version == 1
```

### Integration Tests

Test component interactions:

```python
# tests/integration/test_workflow/test_basic_workflow.py
async def test_workflow_creation():
    workflow = create_workflow(config)
    assert workflow is not None
```

### E2E Tests

Test complete workflow with real APIs (optional):

```python
# tests/e2e/test_full_workflow.py
@pytest.mark.e2e
@pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"))
async def test_full_article_generation():
    # Run complete workflow
    pass
```

## Performance Considerations

### Parallel Execution

1. **Paper Search**: arXiv and Semantic Scholar searched in parallel
   ```python
   arxiv_task = arxiv_service.search(query)
   scholar_task = scholar_service.search(query)
   results = await asyncio.gather(arxiv_task, scholar_task)
   ```

2. **Agent Execution**: Agents run sequentially (by design)
3. **LLM Calls**: Sequential within agents, can be optimized

### Caching Opportunities

1. **Paper Search**: Cache search results by query
2. **LLM Responses**: Cache outline/article generation
3. **Checkpoints**: PostgreSQL provides state caching

### Optimization Ideas

1. Use faster models for non-critical tasks (GPT-3.5 for outlines)
2. Implement response streaming for real-time feedback
3. Batch visualization generation
4. Add retry logic with exponential backoff

## Security Considerations

1. **API Keys**: Stored in environment variables, never in code
2. **Input Validation**: Pydantic validates all inputs
3. **SQL Injection**: Using parameterized queries in checkpointer
4. **Prompt Injection**: LLM prompts are templated, not user-controlled

## Extensibility

### Adding a New Agent

1. Create agent class:
   ```python
   class SummarizerAgent(BaseAgent[Summary]):
       async def execute(self, state: AgentState) -> Summary:
           # Implementation
           pass
   ```

2. Add factory method:
   ```python
   def create_summarizer(self) -> SummarizerAgent:
       return SummarizerAgent(self.llm_service, config)
   ```

3. Add to workflow:
   ```python
   workflow.add_node("summarizer", summarizer_node)
   workflow.add_edge("visualizer", "summarizer")
   ```

### Adding a New Service

1. Define protocol:
   ```python
   class TranslationServiceProtocol(Protocol):
       async def translate(self, text: str, target: str) -> str: ...
   ```

2. Implement service:
   ```python
   class TranslationService(BaseService, TranslationServiceProtocol):
       async def translate(self, text: str, target: str) -> str:
           # Implementation
           pass
   ```

3. Inject via factory:
   ```python
   self.translation_service = TranslationService(config)
   ```

### Adding a New LLM Provider

1. Add to LLMService:
   ```python
   elif self.provider == "cohere":
       from langchain_cohere import ChatCohere
       self.llm = ChatCohere(...)
   ```

2. Update config schema:
   ```python
   provider: Literal["openai", "anthropic", "cohere"]
   ```

## Future Enhancements

1. **Streaming Support**: Real-time article generation feedback
2. **Multi-Language**: Support for non-English articles
3. **Custom Agents**: User-defined agents via plugins
4. **Web Interface**: GUI for HITL interactions
5. **Collaborative Editing**: Multiple reviewers
6. **Template System**: Pre-defined article structures
7. **Citation Manager**: Automatic BibTeX generation
8. **Export Formats**: PDF, LaTeX, DOCX output

## References

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [LangChain Documentation](https://python.langchain.com/)
- [SOLID Principles](https://en.wikipedia.org/wiki/SOLID)
- [arXiv API](https://info.arxiv.org/help/api/)
- [Semantic Scholar API](https://api.semanticscholar.org/)
