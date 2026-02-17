from openai import AsyncOpenAI
from app.config import settings

client = AsyncOpenAI(
    api_key=settings.OPENAI_API_KEY,
    base_url=settings.OPENAI_BASE_URL
)

async def generate_chat_response(messages: list[dict], stream: bool = False, **kwargs):
    api_kwargs = {
        "messages": messages,
        "stream": stream,
    }
    # Update with additional parameters (model, temperature, etc.)
    api_kwargs.update(kwargs)

    if not api_kwargs.get("model") and settings.MODEL_NAME:
        api_kwargs["model"] = settings.MODEL_NAME

    # Remove keys with None values (e.g. max_tokens if not set)
    api_kwargs = {k: v for k, v in api_kwargs.items() if v is not None}

    response = await client.chat.completions.create(**api_kwargs)
    return response

async def summarize_conversation(history_text: str):
    prompt = f"Summarize the following conversation concisely to retain key context for future interactions:\n\n{history_text}"
    response = await client.chat.completions.create(
        model=settings.MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
        stream=False
    )
    return response.choices[0].message.content
