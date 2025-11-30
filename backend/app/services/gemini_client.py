import asyncio
import json
import logging
import re
from typing import Any

from google import genai

from app.core.config import settings

_client: genai.Client | None = None


def get_gemini_client() -> genai.Client:
    """Lazily initialize a Gemini client using the configured API key."""
    global _client
    if _client is None:
        if not settings.gemini_api_key:
            raise RuntimeError("GEMINI_API_KEY is not configured")
        _client = genai.Client(api_key=settings.gemini_api_key)
    return _client


async def generate_text(system: str | None, prompt: str, temperature: float | None = None) -> str:
    """
    Generate a text completion using Gemini.

    The call is executed in a thread to avoid blocking the event loop because the SDK is sync.
    """
    client = get_gemini_client()
    full_prompt = f"{system}\n\n{prompt}" if system else prompt

    def _call() -> str:
        kwargs: dict[str, Any] = {
            "model": settings.gemini_model,
            "contents": full_prompt,
        }
        # Try the older generation_config signature first, fall back to config for newer SDKs.
        try:
            response = (
                client.models.generate_content(
                    **kwargs,
                    generation_config={"temperature": temperature} if temperature is not None else None,
                )
                if temperature is not None
                else client.models.generate_content(**kwargs)
            )
        except TypeError:
            response = (
                client.models.generate_content(
                    **kwargs,
                    config={"temperature": temperature} if temperature is not None else None,
                )
                if temperature is not None
                else client.models.generate_content(**kwargs)
            )
        return getattr(response, "text", "") or ""

    return await asyncio.to_thread(_call)


def _extract_json(text: str) -> str:
    """Extract the first JSON object or array from the model text response."""
    match = re.search(r"({.*}|\\[.*\\])", text, re.DOTALL)
    return match.group(0) if match else text


async def generate_json(system: str | None, prompt: str, temperature: float | None = None) -> dict[str, Any]:
    """Ask Gemini to return JSON and parse it into a dict."""
    raw = await generate_text(system=system, prompt=prompt, temperature=temperature)
    cleaned = _extract_json(raw).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        logging.getLogger(__name__).warning("Failed to parse Gemini JSON response, returning empty dict")
        return {}
