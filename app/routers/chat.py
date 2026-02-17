from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
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

async def prepare_chat_context(request: ChatRequest):
    # 1. Prepare Context & History
    messages = request.messages
    current_summary = request.summary
    
    # Add the new user message to the history for processing
    user_message = Message(role="user", content=request.message)
    messages.append(user_message)

    # 2. Check for Summarization Trigger
    updated_summary = current_summary
    active_history = messages # The history we will use for generation
    
    if len(messages) > settings.SUMMARY_THRESHOLD:
        # Let's keep the last 6 messages raw, and summarize the rest including previous summary
        retention_count = 6
        to_summarize = messages[:-retention_count]
        active_history = messages[-retention_count:]
        
        updated_summary = await process_summary(current_summary, to_summarize)
        
    # 3. Build Context from Vector Store
    context_text = ""
    # 3. Build Context from Vector Store
    context_text = ""
    # Logic:
    # - None or "none": Pure LLM (No RAG)
    # - "all": Search ALL documents (RAG with no filter)
    # - "specific": Search specific domain (RAG with filter)
    
    domain_req = request.domain
    if domain_req and domain_req.lower() != "none":
        search_domain = None # Default to None (All) if "all"
        if domain_req.lower() != "all":
            search_domain = domain_req
            
        documents = vector_store.query_documents(search_domain, request.message)
        if documents:
            context_text = "\n\nRelevant Context:\n" + "\n".join(documents)

    # 4. Construct System Prompt
    # Use custom system prompt if provided, otherwise default
    base_system_prompt = request.system_prompt if request.system_prompt else "You are a helpful AI assistant."
    
    system_content = base_system_prompt
    if updated_summary:
        system_content += f"\n\nPrevious Conversation Summary:\n{updated_summary}"
    if context_text:
        system_content += context_text

    llm_messages = [{"role": "system", "content": system_content}]
    for msg in active_history:
        llm_messages.append({"role": msg.role, "content": msg.content})
    
    # 5. Prepare Generation Args
    gen_kwargs = {
        "model": request.model,
        "temperature": request.temperature,
        "top_p": request.top_p,
        "max_tokens": request.max_tokens,
        "presence_penalty": request.presence_penalty,
        "frequency_penalty": request.frequency_penalty,
    }
    
    return llm_messages, active_history, updated_summary, gen_kwargs

@router.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        data = await websocket.receive_json()
        # Parse into ChatRequest
        request = ChatRequest(**data)
        
        llm_messages, active_history, updated_summary, gen_kwargs = await prepare_chat_context(request)
        
        full_response = ""
        async for chunk in await llm_client.generate_chat_response(llm_messages, stream=True, **gen_kwargs):
            content = chunk.choices[0].delta.content
            if content:
                full_response += content
                await websocket.send_json({"content": content})
        
        # Final packet with metadata
        assistant_message = Message(role="assistant", content=full_response)
        final_history = active_history + [assistant_message]
        
        metadata = {
            "updated_summary": updated_summary,
            "updated_history": [m.model_dump() for m in final_history]
        }
        await websocket.send_json({"metadata": metadata})
        # Optional: verify if we need to send a close frame or keep connection open for next message
        # Typically chat WS might stay open, but here we treat it as request-response stream
        # Verify user preference. For now, we just finish this generation. 
        # Waiting for next message or closing? 
        # LLM streaming usually ends here for one turn.
        
    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        await websocket.send_json({"error": str(e)})

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    llm_messages, active_history, updated_summary, gen_kwargs = await prepare_chat_context(request)
    
    # Non-streaming only
    response = await llm_client.generate_chat_response(llm_messages, stream=False, **gen_kwargs)
    content = response.choices[0].message.content
    
    assistant_message = Message(role="assistant", content=content)
    final_history = active_history + [assistant_message]
    
    return ChatResponse(
        response=content,
        updated_summary=updated_summary,
        updated_history=final_history
    )
