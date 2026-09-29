"""
Groq LLM Client for Northwind Pay OnCall Memory.
Strictly calls Groq API using model 'openai/gpt-oss-120b' with fallback to 'qwen/qwen3.8-27b'
and 'openai/gpt-oss-20b', with exponential retry handling.
"""

import time
import logging
from typing import Optional, List, Dict, Any
from groq import Groq

from backend.config import (
    GROQ_API_KEY,
    PRIMARY_MODEL,
    FALLBACK_MODEL,
    FAST_MODEL,
    is_groq_configured
)

logger = logging.getLogger(__name__)


class GroqLLMClient:
    def __init__(self):
        if not is_groq_configured():
            raise RuntimeError("GROQ_API_KEY is missing or invalid in .env")
        self.client = Groq(api_key=GROQ_API_KEY)
        logger.info("Live Groq client initialized with model tier: openai/gpt-oss-120b -> qwen/qwen3.8-27b -> openai/gpt-oss-20b")

    def generate_chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.2,
        max_tokens: int = 1500,
        max_retries: int = 3
    ) -> str:
        """
        Generates chat completion using live Groq API with retries:
        1. openai/gpt-oss-120b (Primary)
        2. qwen/qwen3.8-27b (Fallback)
        3. openai/gpt-oss-20b (Fast emergency)
        """
        models_to_try = [PRIMARY_MODEL, "qwen/qwen3-32b", FALLBACK_MODEL, FAST_MODEL]
        last_error = None

        for model in models_to_try:
            for attempt in range(max_retries):
                try:
                    logger.info(f"Calling live Groq API with model '{model}' (attempt {attempt + 1})...")
                    chat_completion = self.client.chat.completions.create(
                        messages=messages,
                        model=model,
                        temperature=temperature,
                        max_tokens=max_tokens,
                    )
                    choice = chat_completion.choices[0]
                    content = choice.message.content
                    if content and content.strip():
                        return content.strip()
                except Exception as e:
                    last_error = e
                    logger.warning(f"Groq API error on model {model} (attempt {attempt + 1}): {e}")
                    time.sleep(1.0 * (attempt + 1))
            logger.info(f"Model '{model}' failed or unavailable, moving to next model...")

        raise RuntimeError(f"All Groq models failed. Last error: {last_error}")


llm_client = GroqLLMClient()
