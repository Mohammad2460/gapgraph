"""Thin LLM wrapper: prompt in, validated Pydantic object out.  [Pillar A]

Uses OpenAI structured outputs (`responses.parse(text_format=...)`) so the
response is guaranteed to match the schema — no JSON regex hacks.
"""

from typing import TypeVar

import openai
from pydantic import BaseModel

from app.config import settings

T = TypeVar("T", bound=BaseModel)

_client: openai.AsyncOpenAI | None = None


def client() -> openai.AsyncOpenAI:
    global _client
    if _client is None:
        # Falls back to the OPENAI_API_KEY env var when the key is None.
        _client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
    return _client


class LLMRefusal(RuntimeError):
    pass


async def structured(system: str, user: str, schema: type[T], max_tokens: int = 16000) -> T:
    """Call the model and return an instance of `schema`."""
    response = await client().responses.parse(
        model=settings.openai_model,
        instructions=system,
        input=user,
        text_format=schema,
        max_output_tokens=max_tokens,
        reasoning={"effort": settings.openai_effort},
    )
    for item in response.output:
        for part in getattr(item, "content", None) or []:
            if getattr(part, "type", None) == "refusal":
                raise LLMRefusal(part.refusal)
    if response.output_parsed is None:
        reason = response.incomplete_details.reason if response.incomplete_details else None
        raise RuntimeError(f"No parsed output (status={response.status}, reason={reason})")
    return response.output_parsed
