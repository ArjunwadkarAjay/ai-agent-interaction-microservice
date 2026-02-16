from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from app.schemas import ChatRequest, ChatResponse, Message
from app import llm_client
from app.vector_store import vector_store
from app.config import settings
import json

router = APIRouter()

async def process_summary(current_summary: str | None, messages: list[Message]) -> str:
    # Summarize the conversation history
    text_to_summarize = ""
    if current_summary:
        text_to_summarize += f"Previous Summary: {current_summary}\n"
    text_to_summarize += "\n".join([f"{m.role}: {m.content}" for m in messages])
    
    new_summary = await llm_client.summarize_conversation(text_to_summarize)
    return new_summary

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    # 1. Prepare Context & History
    # We use the messages provided in the request
    messages = request.messages
    current_summary = request.summary
    
    # Add the new user message to the history for processing
    user_message = Message(role="user", content=request.message)
    messages.append(user_message)

    # 2. Check for Summarization Trigger
    # If history is too long, we summarize the older part
    # Strategy: If count > threshold, summarize everything and keep only the last few messages + summary
    # But for a stateless "smart" client, maybe we just update the summary and return a shorter list?
    # User requirement: "summary + chats ... if threshold reach then send back summary & response"
    
    updated_summary = current_summary
    active_history = messages # The history we will use for generation
    
    if len(messages) > settings.SUMMARY_THRESHOLD:
        # Trigger summarization
        # We summarize the entire current context (summary + messages)
        # And we might want to keep only the last N messages for the next turn to keep payload small
        # For this turn, we ideally use full context to generate response, THEN summarize for return?
        # OR we summarize FIRST, and use (New Summary + Last N Messages) for generation?
        # Using (New Summary + Last N) is better for token efficiency.
        
        # Let's keep the last 5 messages raw, and summarize the rest including previous summary
        retention_count = 6
        to_summarize = messages[:-retention_count]
        active_history = messages[-retention_count:]
        
        updated_summary = await process_summary(current_summary, to_summarize)
        
    # 3. Build Context from Vector Store
    context_text = ""
    if request.domain:
        documents = vector_store.query_documents(request.domain, request.message)
        if documents:
            context_text = "\n\nRelevant Domain Context:\n" + "\n".join(documents)

    # 4. Construct System Prompt
    system_content = f"You are a helpful AI assistant."
    if updated_summary:
        system_content += f"\n\nPrevious Conversation Summary:\n{updated_summary}"
    if context_text:
        system_content += context_text

    llm_messages = [{"role": "system", "content": system_content}]
    for msg in active_history:
        llm_messages.append({"role": msg.role, "content": msg.content})
    
    # 5. Generate Response
    if request.stream:
        async def response_generator():
            full_response = ""
            async for chunk in await llm_client.generate_chat_response(llm_messages, stream=True, model=request.model):
                content = chunk.choices[0].delta.content
                if content:
                    full_response += content
                    # We stream the content. We also need to send the final updated summary/history at the end?
                    # SSE usually sends data chunks. 
                    # We can send a special event for metadata or just rely on client not needing it immediately?
                    # The client needs the updated history (user msg + ai msg) and updated summary for NEXT request.
                    # We will send it as a final data packet.
                    yield f"data: {json.dumps({'content': content})}\n\n"
            
            # Final packet with metadata
            assistant_message = Message(role="assistant", content=full_response)
            final_history = active_history + [assistant_message]
            
            metadata = {
                "updated_summary": updated_summary,
                "updated_history": [m.model_dump() for m in final_history]
            }
            yield f"data: {json.dumps({'metadata': metadata})}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(response_generator(), media_type="text/event-stream")
    else:
        response = await llm_client.generate_chat_response(llm_messages, stream=False, model=request.model)
        content = response.choices[0].message.content
        
        assistant_message = Message(role="assistant", content=content)
        final_history = active_history + [assistant_message]
        
        return ChatResponse(
            response=content,
            updated_summary=updated_summary,
            updated_history=final_history
        )
