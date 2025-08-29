import os
from typing import Optional

from app.utils.validation import sanitize_string

DEFAULT_SYSTEM_PROMPT = (
    "You are a DevOps assistant. Provide precise, actionable answers."
)
DEFAULT_MODEL = os.getenv("CHATOPS_MODEL", "gpt-4o-mini")


def chat(
    user_query: str, system_prompt: Optional[str] = None, model: Optional[str] = None
) -> str:
    """Get a chat response from the AI provider with safe defaults.

    This function intentionally uses the OpenAI SDK signature that tests mock:
    - from openai import OpenAI
    - client.chat.completions.create(...)
    """

    cleaned_query = sanitize_string(user_query, max_len=2048)
    if not cleaned_query:
        raise ValueError("Invalid query")

    # Lazy import to make tests lighter and allow patching
    from openai import OpenAI  # type: ignore

    client = OpenAI()
    completion = client.chat.completions.create(
        model=(model or DEFAULT_MODEL),
        messages=[
            {"role": "system", "content": (system_prompt or DEFAULT_SYSTEM_PROMPT)},
            {"role": "user", "content": cleaned_query},
        ],
    )

    return completion.choices[0].message.content
