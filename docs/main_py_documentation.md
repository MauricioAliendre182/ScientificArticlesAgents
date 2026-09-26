# main.py Documentation

## Overview

`main.py` serves as the primary entry point for the Scientific Articles Engine CLI. It orchestrates a multi-agent system that automatically generates scientific articles through a three-phase workflow with built-in Human-in-the-Loop (HITL) approval points.

## Architecture

The application uses:
- **Click**: Command-line interface framework
- **Rich**: Terminal UI for beautiful console output
- **AsyncIO**: Asynchronous execution for workflow operations
- **LangGraph**: State machine workflow orchestration

## CLI Structure

### Main CLI Group

```python
@click.group()
@click.option("--config", "-c", default="config.yaml")
@click.option("--log-level", default="INFO")
def cli(ctx, config, log_level)
```

The root CLI command group that:
- Loads configuration from a YAML file (default: `config.yaml`)
- Sets up logging with configurable log level
- Stores configuration path in Click context for subcommands

### Available Commands

#### 1. `generate` Command (Lines 44-62)

**Purpose**: Generate a scientific article on a specified topic

**Usage**:
```bash
scientific-articles-engine generate "Transformer Architectures in NLP"
```

**Parameters**:
- `topic` (required): The subject of the article to generate
- `--output, -o`: Output file path (default: `{topic}.md`)
- `--thread-id`: Thread ID for checkpointing and state persistence (default: "default")
- `--auto-approve`: Flag to skip HITL approval points for testing

**Flow**: Delegates to `_generate_article()` async function

#### 2. `validate-config` Command (Lines 202-218)

**Purpose**: Validate a configuration file

**Usage**:
```bash
scientific-articles-engine validate-config config.yaml
```

**Output**: Confirms validity and displays key configuration settings (provider, model, database status)

#### 3. `version` Command (Lines 221-226)

**Purpose**: Display version information

**Usage**:
```bash
scientific-articles-engine version
```

## Article Generation Workflow

The `_generate_article()` function (lines 65-180) implements the core workflow in three distinct phases:

### Phase 1: Search and Outline (Lines 98-118)

**What Happens**:
1. Workflow searches for relevant academic papers
2. Generates an article outline based on found sources
3. Streams state updates asynchronously

**HITL Checkpoint 1** (Lines 105-118):
- Displays number of papers found
- Shows generated outline in a panel
- Prompts user to approve sources and outline
- If rejected, generation stops immediately

**Key State Variables**:
- `state['papers']`: List of found academic papers
- `state['outline']`: Generated article structure
- `state['searcher_approved']`: Approval flag to continue workflow

### Phase 2: Writing and Reviewing (Lines 123-143)

**What Happens**:
1. AI agents write article content based on approved outline
2. Reviewer agent evaluates quality iteratively
3. Writer revises based on feedback
4. Progress bar shows current revision number and quality score

**Visual Feedback**:
```
Writing and reviewing... Revision 3: Score 8.5/10
```

**Key State Variables**:
- `state['article']`: Generated article object
- `state['review']`: Review feedback with quality scores
- `state['revision_count']`: Number of revision iterations

### Phase 3: Visualization Generation (Lines 166-169)

**HITL Checkpoint 2** (Lines 146-161):
- Displays article metadata (title, word count, version)
- Shows abstract preview
- Prompts user to approve final article
- If rejected, workflow terminates without generating visualizations

**What Happens After Approval**:
1. Sets `state['final_approved'] = True`
2. Visualization agent generates charts/figures
3. Saves complete article with visualizations

## Key Functions

### `_generate_article()` (Lines 65-180)

**Async Function**: Core orchestration logic

**Responsibilities**:
1. Load configuration from file
2. Create and initialize workflow with initial state
3. Execute three-phase workflow with HITL gates
4. Handle state streaming and updates
5. Save final output
6. Error handling and user feedback

**Configuration Setup**:
```python
workflow_config = {"configurable": {"thread_id": thread_id}}
```
Enables checkpointing for workflow state persistence and resumption.

### `_save_article()` (Lines 183-199)

**Purpose**: Persist article to filesystem

**Process**:
1. Convert article object to Markdown format
2. Append visualization section if visualizations exist
3. Write combined content to output file

**Output Structure**:
```
[Article Content in Markdown]

---

# Visualizations

[Visualization 1]
[Visualization 2]
...
```

## State Management

The workflow uses a stateful graph where:
- **Initial State**: Created by `create_initial_state(topic)` with just the topic
- **State Updates**: Streamed asynchronously through `workflow.astream()`
- **Checkpointing**: Thread ID enables workflow pause/resume functionality
- **Approval Gates**: State updated with approval flags (`searcher_approved`, `final_approved`)

## Error Handling

**Try-Catch Block** (Lines 73-180):
- Catches all exceptions during generation
- Displays formatted error message in red
- Re-raises exception for proper exit codes

## UI/UX Features

### Rich Console Components

1. **Panel**: Used for title cards and outlined content
2. **Progress**: Spinner-based progress indicators
3. **Color Coding**:
   - Cyan: Informational messages
   - Yellow: HITL checkpoints
   - Green: Success messages
   - Red: Errors and rejections
   - Dim: Auto-approve notifications

### User Interaction

- **Confirmation Prompts**: `click.confirm()` for HITL approval
- **Auto-Approve Mode**: Bypasses prompts for automated testing
- **Real-time Updates**: Progress indicators show current revision and quality score

## Workflow Configuration

The workflow is created with configuration that includes:
- LLM provider and model settings
- Database connection settings (for paper storage)
- Agent-specific parameters
- Checkpointing configuration

## Dependencies

### Internal Modules

- `config.load_config`: Configuration file loading
- `core.state.create_initial_state`: Initial workflow state creation
- `graph.workflow.create_workflow`: Workflow graph construction
- `utils.logger.setup_logging`: Logging configuration

### External Libraries

- `click`: CLI framework
- `rich`: Terminal formatting
- `asyncio`: Async execution
- `pathlib`: File path handling

## Entry Point

```python
if __name__ == "__main__":
    cli()
```

Enables direct execution: `python -m scientific_articles_engine.main`

## Typical Execution Flow

1. User runs: `scientific-articles-engine generate "Topic"`
2. CLI parses arguments and loads config
3. Workflow initializes with topic
4. Phase 1: Search → User approves sources/outline
5. Phase 2: Write/Review → User approves final article
6. Phase 3: Generate visualizations
7. Save complete article to file
8. Display success message with output path

## Configuration via Environment

The workflow relies on:
- Configuration file path (default: `config.yaml`)
- Log level for debugging
- Thread ID for state management
- Auto-approve flag for testing automation
