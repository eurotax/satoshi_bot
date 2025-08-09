# ai_service.py
import os
from anthropic import APIError
from anthropic_client import client

MODEL = os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-latest")

def generate_ai_reply(user_text: str, system_prompt: str | None = None, max_tokens: int = 4000) -> str:
    """
    Calls Anthropic Messages API and returns plain text.
    Costs money when executed (API usage). Safe to import; no call happens until you call this function.
    """
    messages = [{"role": "user", "content": user_text}]
    try:
        resp = client.messages.create(
            model=MODEL,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=messages,
        )
        # Extract first text block
        for block in resp.content:
            if getattr(block, "type", None) == "text":
                return block.text
        return ""
    except APIError as e:
        # Bubble up a concise error string for logs
        raise RuntimeError(f"Anthropic API error: {e}") from e
