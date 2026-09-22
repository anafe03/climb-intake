"""OpenAI-backed extraction. Same contract as llm.classify: (Extraction, meta)."""
from __future__ import annotations

import os
import time

import openai

from .llm import SYSTEM_PROMPT, max_retries, timeout_s
from .models import Extraction


def model_name() -> str:
    return os.environ.get("OPENAI_MODEL", "gpt-5")


def classify(text: str) -> tuple[Extraction, dict]:
    started = time.perf_counter()
    client = openai.OpenAI(timeout=timeout_s(), max_retries=max_retries())
    response = client.responses.parse(
        model=model_name(),
        instructions=SYSTEM_PROMPT,
        input=f"<ticket>\n{text}\n</ticket>",
        text_format=Extraction,
        max_output_tokens=4096,
    )
    parsed = response.output_parsed
    if parsed is None:
        raise ValueError(f"no parsed output (status={getattr(response, 'status', None)})")
    usage = getattr(response, "usage", None)
    meta = {
        "model": response.model,
        "stop_reason": getattr(response, "status", None),
        "input_tokens": getattr(usage, "input_tokens", 0) or 0,
        "output_tokens": getattr(usage, "output_tokens", 0) or 0,
        "cache_read_input_tokens": getattr(getattr(usage, "input_tokens_details", None), "cached_tokens", 0) or 0,
        "llm_ms": int((time.perf_counter() - started) * 1000),
    }
    return parsed, meta
