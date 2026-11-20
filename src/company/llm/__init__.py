"""LLM module — unified client and prompt templates."""

from company.llm.client import LLMClient, LLMConfig, get_client
from company.llm import prompts

__all__ = ["LLMClient", "LLMConfig", "get_client", "prompts"]
