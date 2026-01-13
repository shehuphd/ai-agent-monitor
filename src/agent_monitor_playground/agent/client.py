# src/agent_monitor_playground/agent/client.py
"""
OpenAI API client wrapper. This module talks to OpenAI.
All agent logic treats this class as a black box that:
- Sends a prompt to a model.
- Returns generated text.
- Returns basic execution metadata.

No other file should import the OpenAI SDK directly.
That separation makes it easy to:
- Swap providers later.
- Mock model calls in tests.
- Audit all external calls in one place.
"""

import os
import time
from typing import Dict, Any

from openai import OpenAI


class OpenAIClient:
    """
    Thin wrapper around the OpenAI Responses API.

    Responsibilities:
    - Validate that the API key exists.
    - Execute one model call.
    - Normalize the response into a simple dictionary.
    """

    def __init__(self) -> None:
        """
        Initializes the client and checks that the API key is available.

        The OpenAI SDK reads the API key automatically from the environment,
        so the code only verifies that it exists.
        """
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is not set in the environment")

        self.client = OpenAI()

    def run_one_shot(
        self,
        *,
        prompt: str,
        model: str,
        max_output_tokens: int,
    ) -> Dict[str, Any]:
        """
        Executes a single prompt → single response interaction.

        Inputs:
        - prompt: The text prompt to send to the model.
        - model: Model identifier (e.g. "gpt-4o-mini").
        - max_output_tokens: Maximum number of tokens the model may generate.

        Returns a dictionary with:
        - text: Final output text produced by the model.
        - latency_ms: Wall-clock latency of the API call in milliseconds.
        - model: The model used for the request.

        The return type is intentionally a plain dict so higher layers
        can easily add fields without changing this interface.
        """

        # Capture start time for latency measurement.
        start = time.time()

        # Execute the request using the OpenAI Responses API.
        response = self.client.responses.create(
            model=model,
            input=prompt,
            max_output_tokens=max_output_tokens,
        )

        # Compute latency in milliseconds.
        latency_ms = int((time.time() - start) * 1000)

        # The Responses API exposes a convenience property `output_text`
        # which concatenates all generated text segments into one string.
        # This is safer and simpler than manually walking the response tree.
        output_text = response.output_text or ""

        return {
            "text": output_text.strip(),
            "latency_ms": latency_ms,
            "model": model,
        }
