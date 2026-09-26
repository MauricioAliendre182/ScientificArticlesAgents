# Change Summary

## CLI Installation and Environment

- Confirmed `scientific-articles-engine` is the project's custom console script defined in `pyproject.toml`.
- Installed the project and all Python dependencies into `myenv`, not the global Python environment.
- Updated the setup scripts to create and activate `myenv`:
  - `setup.ps1`
  - `setup.sh`
- The CLI can be run explicitly with:

```powershell
.\myenv\Scripts\scientific-articles-engine.exe generate "Transformer Architectures in NLP"
```

## PostgreSQL Dependencies

- Added `langgraph-checkpoint-postgres` to the project dependencies.
- Added `psycopg[binary]` for Windows-compatible PostgreSQL client support.
- Kept the existing Docker PostgreSQL database and persistent volume.

## Docker PostgreSQL Port

- The host's Windows PostgreSQL process was already using port `5432`.
- Docker PostgreSQL is now published on host port `5433` while remaining on port `5432` inside the container.
- Updated `config.yaml` to connect to Docker PostgreSQL through `localhost:5433`.
- The Docker application services continue to use the internal Compose address `postgres:5432`.

## LangGraph Checkpointing

- Replaced the incorrect use of the context manager returned by `PostgresSaver.from_conn_string()`.
- Added a persistent synchronous PostgreSQL saver for synchronous workflows.
- Added `AsyncPostgresSaver` support for the CLI's `workflow.astream()` execution.
- Added PostgreSQL checkpoint setup and migrations during workflow creation.
- Added the Windows Selector event loop required by psycopg asynchronous connections.

## Agent and CLI Error Handling

- Added a shared logger to `BaseAgent`, fixing the missing `SearcherAgent.logger` error.
- Added an explicit search-phase error check in the CLI so failed workflow state is reported clearly instead of producing `KeyError: 'papers'`.

## Validation

The following checks passed:

- PostgreSQL connection from the application to Docker.
- PostgreSQL checkpoint setup.
- Async workflow creation.
- Workflow compilation with `AsyncPostgresSaver`.
- Custom CLI startup and help output.
- Searcher node startup during an end-to-end generation run.

## Known External Limitation

The end-to-end run reached the Searcher successfully, but arXiv returned:

```text
HTTP 429 Too Many Requests
```

This is an external arXiv rate-limit response, not a PostgreSQL or LangGraph checkpointing error. Retrying after a delay or reducing request frequency is required.

## Security Note

The OpenAI API key was exposed in terminal output during debugging. It should be revoked and replaced, and the replacement should be stored only in `.env` or another secure secret manager.
