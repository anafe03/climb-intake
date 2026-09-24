"""OpenAI-backed extraction. Same contract as llm.classify: (Extraction, meta)."""
from __future__ import annotations

import os
import time
from functools import lru_cache

import openai

from .llm import SYSTEM_PROMPT, max_retries, timeout_s
from .models import Extraction


@lru_cache(maxsize=4)
def _client(timeout: float, retries: int) -> openai.OpenAI:
    """Shared client, so concurrent tickets reuse connections instead of each opening a new one."""
    return openai.OpenAI(timeout=timeout, max_retries=retries)


def model_name() -> str:
    """`gpt-5` by default. Override with OPENAI_MODEL.

    A bake-off over the 10 Climb samples said `gpt-5-mini` was equal-or-better at a fifth of the
    cost. That bake-off was wrong, because those 10 tickets contain no false-positive traps — every
    one of them has a correct answer of "escalate" or "don't", but none is designed to *tempt* a
    spurious escalation. Measured against the traps in the edge set, mini escalates a SOC 2 document
    request and an RCA request, and is unstable between runs. gpt-5 gets both right, twice. D52.
    """
    return os.environ.get("OPENAI_MODEL", "gpt-5")


def classify(text: str) -> tuple[Extraction, dict]:
    started = time.perf_counter()
    client = _client(timeout_s(), max_retries())
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
