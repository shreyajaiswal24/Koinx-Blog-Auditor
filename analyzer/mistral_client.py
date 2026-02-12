"""Mistral AI API wrapper with rate limiting and retry logic."""

import json
import logging
import time
from typing import Dict, Any, Optional

from mistralai import Mistral

from config.settings import (
    MISTRAL_API_KEY,
    MISTRAL_MODEL,
    MISTRAL_TEMPERATURE,
    MISTRAL_MAX_TOKENS,
    MISTRAL_RPM_LIMIT,
)

logger = logging.getLogger(__name__)


class MistralClient:
    """Wrapper around Mistral API with rate limiting and structured output."""

    def __init__(self):
        if not MISTRAL_API_KEY:
            raise ValueError("MISTRAL_API_KEY not set. Add it to .env file.")
        self.client = Mistral(api_key=MISTRAL_API_KEY)
        self.model = MISTRAL_MODEL

        # Token bucket rate limiter
        self._min_interval = 60.0 / MISTRAL_RPM_LIMIT
        self._last_request_time = 0.0

        # Usage tracking
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_requests = 0

    def analyze(
        self, system_prompt: str, user_prompt: str, max_retries: int = 3
    ) -> Optional[Dict[str, Any]]:
        """Send a prompt to Mistral and parse JSON response.

        Returns parsed JSON dict, or None on failure.
        """
        self._rate_limit()

        for attempt in range(1, max_retries + 1):
            try:
                response = self.client.chat.complete(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=MISTRAL_TEMPERATURE,
                    max_tokens=MISTRAL_MAX_TOKENS,
                    response_format={"type": "json_object"},
                )

                self.total_requests += 1

                # Track token usage
                if response.usage:
                    self.total_input_tokens += response.usage.prompt_tokens
                    self.total_output_tokens += response.usage.completion_tokens

                content = response.choices[0].message.content
                return self._parse_json(content)

            except Exception as e:
                error_str = str(e)
                logger.warning(
                    f"Mistral API attempt {attempt}/{max_retries} failed: {error_str}"
                )

                if attempt < max_retries:
                    # Exponential backoff: 2s, 4s, 8s
                    wait = 2 ** attempt
                    if "429" in error_str or "rate" in error_str.lower():
                        wait = wait * 2  # extra wait for rate limits
                    logger.info(f"Retrying in {wait}s...")
                    time.sleep(wait)
                else:
                    logger.error(f"All {max_retries} attempts failed")
                    return None

    def _rate_limit(self):
        """Token-bucket rate limiter to stay under RPM limit."""
        now = time.time()
        elapsed = now - self._last_request_time
        if elapsed < self._min_interval:
            sleep_time = self._min_interval - elapsed
            time.sleep(sleep_time)
        self._last_request_time = time.time()

    def _parse_json(self, content: str) -> Optional[Dict[str, Any]]:
        """Parse JSON from Mistral response, handling common formatting issues."""
        if not content:
            return None

        content = content.strip()

        # Remove markdown code fences if present
        if content.startswith("```"):
            lines = content.split("\n")
            lines = [l for l in lines if not l.strip().startswith("```")]
            content = "\n".join(lines)

        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.warning(f"JSON parse error: {e}. Raw content: {content[:200]}")
            return None

    def get_usage_stats(self) -> Dict[str, int]:
        """Return cumulative token usage statistics."""
        return {
            "total_requests": self.total_requests,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_tokens": self.total_input_tokens + self.total_output_tokens,
        }
