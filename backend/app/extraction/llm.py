"""Thin Claude wrapper: prompt in, validated Pydantic object out.  [Pillar A]

Uses structured outputs (`messages.parse`) so the response is guaranteed to
match the schema — no JSON regex hacks.
"""

from typing import TypeVar

import anthropic
from pydantic import BaseModel

from app.config import settings

T = TypeVar("T", bound=BaseModel)

_client: anthropic.AsyncAnthropic | None = None


def client() -> anthropic.AsyncAnthropic:
    global _client
    if _client is None:
        # Falls back to ANTHROPIC_API_KEY / `ant auth login` profile when key is None.
        _client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    return _client


class LLMRefusal(RuntimeError):
    pass


async def structured(system: str, user: str, schema: type[T], max_tokens: int = 16000) -> T:
    """Call Claude and return an instance of `schema`."""
    response = await client().messages.parse(
        model=settings.claude_model,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}],
        output_format=schema,
        output_config={"effort": settings.claude_effort},
    )
    if response.stop_reason == "refusal":
        raise LLMRefusal(str(response.stop_details))
    if response.parsed_output is None:
        raise RuntimeError(f"No parsed output (stop_reason={response.stop_reason})")
    return response.parsed_output
