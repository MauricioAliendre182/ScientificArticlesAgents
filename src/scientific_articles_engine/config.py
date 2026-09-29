"""Configuration management for the Scientific Articles Engine."""

import os
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, Field

from .core.exceptions import ConfigurationException

# Load environment variables from .env file
load_dotenv()


class LLMConfig(BaseModel):
    """LLM service configuration.

    Attributes:
        provider: LLM provider (openai, anthropic)
        model: Model name (gpt-4, claude-3-opus, etc.)
        temperature: Sampling temperature (0.0-1.0)
        max_tokens: Maximum tokens to generate
        api_key: API key for the LLM service
    """

    provider: str = Field(..., description="LLM provider (openai, anthropic)")
    model: str = Field(..., description="Model name")
    temperature: float = Field(0.7, ge=0.0, le=1.0, description="Sampling temperature")
    max_tokens: int = Field(4000, gt=0, description="Maximum tokens to generate")
    api_key: str | None = Field(None, description="API key (from env)")


class AgentConfig(BaseModel):
    """Configuration for individual agents.

    Attributes:
        max_papers_per_source: Maximum papers to fetch per source (Searcher)
        search_timeout: Search timeout in seconds (Searcher)
        min_word_count: Minimum article word count (Writer)
        max_word_count: Maximum article word count (Writer)
        style_guide: Writing style guide (Writer)
        quality_threshold: Minimum score for passing review (Reviewer)
        max_revisions: Maximum revision attempts (Reviewer)
        max_visualizations: Maximum visualizations to generate (Visualizer)
        supported_types: Supported visualization types (Visualizer)
    """

    # Searcher
    max_papers_per_source: int = Field(10, gt=0)
    search_timeout: int = Field(30, gt=0)

    # Writer
    min_word_count: int = Field(1000, gt=0)
    max_word_count: int = Field(5000, gt=0)
    style_guide: str = Field("academic")

    # Reviewer
    quality_threshold: float = Field(7.0, ge=0.0, le=10.0)
    max_revisions: int = Field(3, gt=0)

    # Visualizer
    max_visualizations: int = Field(5, gt=0)
    supported_types: list = Field(
        default_factory=lambda: ["table", "diagram", "flowchart"]
    )


class DatabaseConfig(BaseModel):
    """Database configuration for checkpointing.

    Attributes:
        host: Database host
        port: Database port
        database: Database name
        user: Database user
        password: Database password
        enabled: Whether to use database checkpointing
    """

    host: str = Field("localhost")
    port: int = Field(5432, gt=0, lt=65536)
    database: str = Field("scientific_articles_engine")
    user: str = Field("postgres")
    password: str | None = Field(None, description="Password (from env)")
    enabled: bool = Field(True)


class EngineConfig(BaseModel):
    """Main configuration for the Scientific Articles Engine.

    Attributes:
        llm: LLM service configuration
        agents: Agent-specific configurations
        database: Database configuration
    """

    llm: LLMConfig
    agents: AgentConfig
    database: DatabaseConfig

    @classmethod
    def from_yaml(cls, config_path: str) -> "EngineConfig":
        """Load configuration from YAML file.

        Args:
            config_path: Path to YAML configuration file

        Returns:
            EngineConfig instance

        Raises:
            ConfigurationException: If config file is invalid or missing
        """
        path = Path(config_path)
        if not path.exists():
            raise ConfigurationException(f"Configuration file not found: {config_path}")

        try:
            with open(path) as f:
                config_data = yaml.safe_load(f)
        except Exception as e:
            raise ConfigurationException(
                f"Failed to load configuration from {config_path}: {e}"
            )

        # Inject environment variables
        config_data = cls._inject_env_vars(config_data)

        try:
            return cls(**config_data)
        except Exception as e:
            raise ConfigurationException(f"Invalid configuration: {e}")

    @staticmethod
    def _inject_env_vars(config_data: dict[str, Any]) -> dict[str, Any]:
        """Inject environment variables into configuration.

        Args:
            config_data: Configuration dictionary from YAML

        Returns:
            Configuration with environment variables injected
        """
        # Inject LLM API key
        if "llm" in config_data:
            provider = config_data["llm"].get("provider", "openai")
            if provider == "openai":
                config_data["llm"]["api_key"] = os.getenv("OPENAI_API_KEY")
            elif provider == "anthropic":
                config_data["llm"]["api_key"] = os.getenv("ANTHROPIC_API_KEY")

        # Inject database password
        if "database" in config_data:
            config_data["database"]["password"] = os.getenv("DATABASE_PASSWORD")

        return config_data

    def to_dict(self) -> dict[str, Any]:
        """Convert configuration to dictionary.

        Returns:
            Configuration as dictionary
        """
        return self.model_dump()


def load_config(config_path: str | None = None) -> EngineConfig:
    """Load configuration from file or use default path.

    Args:
        config_path: Optional path to config file. If None, uses ./config.yaml

    Returns:
        EngineConfig instance

    Raises:
        ConfigurationException: If configuration is invalid
    """
    if config_path is None:
        config_path = "config.yaml"

    return EngineConfig.from_yaml(config_path)
