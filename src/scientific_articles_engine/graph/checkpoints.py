"""Checkpoint configuration for state persistence.

Supports both PostgreSQL (production) and in-memory (testing) checkpointing.
"""

import os

from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer
from psycopg import AsyncConnection, Connection
from psycopg.rows import dict_row

from ..utils.logger import get_logger

logger = get_logger(__name__)
# This serializer is used for serializing and deserializing checkpoint data.
# It uses JsonPlusSerializer with pickle fallback enabled.
# pickle fallback: it is to ensure that objects not natively supported by
# JsonPlus can still be serialized using Python's pickle mechanism.
# For postgresql checkpointing, this serializer will be used to serialize
# and deserialize the checkpoint data.
# IMPORTANT: pickle fallback is appropriate only while the checkpoint
# database contains trusted data.
# Don’t load checkpoints that an untrusted party could modify.
checkpoint_serializer = JsonPlusSerializer(
    pickle_fallback=True,
    allowed_msgpack_modules=[
        ("scientific_articles_engine.models.article", "Article"),
        ("scientific_articles_engine.models.article", "ArticleSection"),
        ("scientific_articles_engine.models.paper", "Paper"),
        ("scientific_articles_engine.models.paper", "PaperAuthor"),
        ("scientific_articles_engine.models.review", "ReviewCriteria"),
        ("scientific_articles_engine.models.review", "ReviewResult"),
        ("scientific_articles_engine.models.visualization", "Visualization"),
        ("scientific_articles_engine.models.visualization", "VisualizationType"),
    ],
)


def create_checkpointer(
    use_postgres: bool = True,
    connection_string: str | None = None,
) -> PostgresSaver | MemorySaver:
    """Create a checkpointer for LangGraph state persistence.

    Args:
        use_postgres: Whether to use PostgreSQL (True) or in-memory (False)
        connection_string: PostgreSQL connection string (if use_postgres=True)

    Returns:
        Checkpointer instance (PostgresSaver or MemorySaver)

    Raises:
        ValueError: If PostgreSQL is requested but connection string is missing
    """
    if use_postgres:
        if not connection_string:
            # Try to build from environment variables
            connection_string = _build_connection_string_from_env()

        if not connection_string:
            raise ValueError(
                "PostgreSQL checkpointing requested but no connection string provided. "
                "Either pass connection_string or set DATABASE_* environment variables."
            )

        logger.info("Creating PostgreSQL checkpointer")
        connection = Connection.connect(
            connection_string,
            autocommit=True,
            prepare_threshold=0,
            row_factory=dict_row,
        )
        checkpointer = PostgresSaver(connection, serde=checkpoint_serializer)
        checkpointer.setup()
        return checkpointer

    else:
        logger.info("Creating in-memory checkpointer (for testing)")
        return MemorySaver()


def _build_connection_string_from_env() -> str | None:
    """Build PostgreSQL connection string from environment variables.

    Expected environment variables:
    - DATABASE_HOST (default: localhost)
    - DATABASE_PORT (default: 5432)
    - DATABASE_NAME (default: scientific_articles_engine)
    - DATABASE_USER (default: postgres)
    - DATABASE_PASSWORD (required)

    Returns:
        Connection string or None if password is missing
    """
    host = os.getenv("DATABASE_HOST", "localhost")
    port = os.getenv("DATABASE_PORT", "5432")
    database = os.getenv("DATABASE_NAME", "scientific_articles_engine")
    user = os.getenv("DATABASE_USER", "postgres")
    password = os.getenv("DATABASE_PASSWORD")

    if not password:
        logger.warning("DATABASE_PASSWORD not set, cannot build connection string")
        return None

    return f"postgresql://{user}:{password}@{host}:{port}/{database}"


def get_checkpointer_from_config(config: dict) -> PostgresSaver | MemorySaver:
    """Create checkpointer from configuration dictionary.

    Args:
        config: Configuration dictionary with database settings

    Returns:
        Checkpointer instance
    """
    db_config = config.get("database", {})

    if not db_config.get("enabled", True):
        logger.info("Database checkpointing disabled in config")
        return MemorySaver()

    # Build connection string from config
    connection_string = (
        f"postgresql://{db_config['user']}:{db_config['password']}@"
        f"{db_config['host']}:{db_config['port']}/{db_config['database']}"
    )

    return create_checkpointer(use_postgres=True, connection_string=connection_string)


async def get_async_checkpointer_from_config(
    config: dict,
) -> AsyncPostgresSaver | MemorySaver:
    """Create an async checkpointer for workflows executed with astream."""
    db_config = config.get("database", {})

    if not db_config.get("enabled", True):
        logger.info("Database checkpointing disabled in config")
        return MemorySaver()

    connection_string = (
        f"postgresql://{db_config['user']}:{db_config['password']}@"
        f"{db_config['host']}:{db_config['port']}/{db_config['database']}"
    )
    connection = await AsyncConnection.connect(
        connection_string,
        autocommit=True,
        prepare_threshold=0,
    )
    # serde: serializer/deserializer for checkpoint data
    # checkpoint_serializer is an instance of JsonPlusSerializer with pickle fallback enabled
    checkpointer = AsyncPostgresSaver(connection, serde=checkpoint_serializer)
    await checkpointer.setup()
    return checkpointer
