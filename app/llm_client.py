from openai import AsyncOpenAI
from app.config import settings

client = AsyncOpenAI(
    api_key=settings.OPENAI_API_KEY,
    base_url=settings.OPENAI_BASE_URL
)

async def generate_chat_response(messages: list[dict], stream: bool = False, model: str = None):
    response = await client.chat.completions.create(
        model=model or settings.MODEL_NAME,
        messages=messages,
        stream=stream
    )
    return response

async def summarize_conversation(history_text: str):
    prompt = f"Summarize the following conversation concisely to retain key context for future interactions:\n\n{history_text}"
    response = await client.chat.completions.create(
        model=settings.MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
        stream=False
    )
    return response.choices[0].message.content
