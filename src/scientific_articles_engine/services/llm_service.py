"""LLM service for text generation using LangChain abstractions."""

import json
from typing import Any

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from ..core.exceptions import ServiceError
from ..core.protocols import LLMServiceProtocol
from .base_service import BaseService


class LLMService(BaseService, LLMServiceProtocol):
    """Language Model service using LangChain.

    Supports multiple LLM providers (OpenAI, Anthropic) through LangChain's
    unified interface. Implements LLMServiceProtocol for dependency injection.

    Attributes:
        provider: LLM provider name (openai, anthropic)
        model: Model name
        llm: LangChain ChatModel instance
    """

    def __init__(self, config: dict[str, Any]):
        """Initialize the LLM service.

        Args:
            config: Configuration dictionary with keys:
                - provider: 'openai' or 'anthropic'
                - model: Model name
                - api_key: API key for the provider
                - temperature: Sampling temperature (default: 0.7)
                - max_tokens: Maximum tokens to generate (default: 4000)

        Raises:
            ServiceException: If provider is not supported or initialization fails
        """
        super().__init__(service_name="llm", config=config)

        self.provider = config.get("provider", "openai")
        self.model = config.get("model", "gpt-4")
        self.api_key = config.get("api_key")

        if not self.api_key:
            raise ServiceError(
                service_name=self.service_name,
                message=f"API key not provided for {self.provider}",
            )

        # Initialize LangChain LLM
        try:
            if self.provider == "openai":
                self.llm = ChatOpenAI(
                    model=self.model,
                    api_key=self.api_key,
                    temperature=config.get("temperature", 0.7),
                    max_tokens=config.get("max_tokens", 4000),
                )
            elif self.provider == "anthropic":
                self.llm = ChatAnthropic(
                    model=self.model,
                    api_key=self.api_key,
                    temperature=config.get("temperature", 0.7),
                    max_tokens=config.get("max_tokens", 4000),
                )
            else:
                raise ServiceError(
                    service_name=self.service_name,
                    message=f"Unsupported provider: {self.provider}",
                )

            self.logger.info(f"Initialized LLM service with {self.provider}/{self.model}")
        except Exception as e:
            self._handle_error(e, "Failed to initialize LLM")

    async def generate(self, prompt: str, **kwargs: dict) -> str:
        """Generate text completion from a prompt.

        Args:
            prompt: The input prompt for the LLM
            **kwargs: Additional generation parameters

        Returns:
            Generated text response

        Raises:
            ServiceException: If generation fails
        """
        try:
            messages = [HumanMessage(content=prompt)]
            response = await self.llm.ainvoke(messages, **kwargs)
            return response.content
        except Exception as e:
            self._handle_error(e, "Text generation failed")
            return ""  # For type checking; exception is always raised

    async def generate_with_structure(
        self, prompt: str, schema: dict, **kwargs: dict
    ) -> dict:
        """Generate structured output conforming to a schema.

        Uses function calling / structured output features of the LLM.

        Args:
            prompt: The input prompt for the LLM
            schema: JSON schema or Pydantic model for structured output
            **kwargs: Additional generation parameters

        Returns:
            Dictionary conforming to the provided schema

        Raises:
            ServiceException: If generation or parsing fails
        """
        try:
            # Add instructions for structured output
            structured_prompt = f"""{prompt}

Please provide your response as a valid JSON object conforming to this schema:
{json.dumps(schema, indent=2)}

Return ONLY the JSON object, no additional text."""

            messages = [HumanMessage(content=structured_prompt)]
            response = await self.llm.ainvoke(messages, **kwargs)

            # Parse JSON response
            content = response.content.strip()

            # Remove markdown code blocks if present
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:].strip()

            return json.loads(content)
        except json.JSONDecodeError as e:
            self._handle_error(e, "Failed to parse structured output")
            return {}  # For type checking
        except Exception as e:
            self._handle_error(e, "Structured generation failed")
            return {}  # For type checking

    async def generate_with_system_message(
        self, system: str, prompt: str, **kwargs: dict
    ) -> str:
        """Generate text with a system message.

        Args:
            system: System message for the LLM
            prompt: User prompt
            **kwargs: Additional generation parameters

        Returns:
            Generated text response

        Raises:
            ServiceException: If generation fails
        """
        try:
            messages = [SystemMessage(content=system), HumanMessage(content=prompt)]
            response = await self.llm.ainvoke(messages, **kwargs)
            return response.content
        except Exception as e:
            self._handle_error(e, "Text generation with system message failed")
            return ""  # For type checking
