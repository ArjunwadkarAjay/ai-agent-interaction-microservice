import streamlit as st
import requests
import json
import asyncio
import websockets
from datetime import datetime

# Page config
st.set_page_config(page_title="AI Agent Chat", page_icon="🤖", layout="wide")

# Constants
API_BASE_URL = "http://localhost:8000/api/v1"
WS_BASE_URL = "ws://localhost:8000/api/v1"

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "summary" not in st.session_state:
    st.session_state.summary = None
if "history_for_api" not in st.session_state:
    st.session_state.history_for_api = []
if "page" not in st.session_state:
    st.session_state.page = "chat"

def navigate_to(page):
    st.session_state.page = page
    st.rerun()

# --- CHAT PAGE ---
if st.session_state.page == "chat":
    # Fetc available domains for selection
    available_domains = ["No Context", "All"]
    try:
        response = requests.get(f"{API_BASE_URL}/documents")
        if response.status_code == 200:
            documents = response.json()
            if documents:
                domains = set(doc['domain'] for doc in documents)
                available_domains.extend(sorted(list(domains)))
    except:
        pass

    # Sidebar settings
    with st.sidebar:
        st.header("Settings")
        
        # Domain Selection
        selected_domain = st.selectbox("Search Domain", available_domains, index=0)
        
        # Map selection to API payload
        # No Context -> None (API skips RAG)
        # All -> "all" (API searches everything)
        # Specific -> "specific" (API filters)
        api_domain = None
        if selected_domain == "All":
            api_domain = "all"
        elif selected_domain != "No Context":
            api_domain = selected_domain
        
        enable_streaming = st.checkbox("Enable Streaming", value=True)
        
        model_name = st.text_input("Model Name", value="hf.co/liquidai/lfm2.5-1.2b-instruct-gguf:Q4_K_M")
        
        system_prompt = st.text_area("System Prompt", value="", help="Optional: Override the default system prompt.")

        st.subheader("Parameters")
        temperature = st.slider("Temperature", 0.0, 2.0, 0.7, 0.1)
        top_p = st.slider("Top P", 0.0, 1.0, 1.0, 0.05)
        max_tokens = st.number_input("Max Tokens", min_value=1, max_value=4096, value=None, step=1)
        presence_penalty = st.slider("Presence Penalty", -2.0, 2.0, 0.0, 0.1)
        frequency_penalty = st.slider("Frequency Penalty", -2.0, 2.0, 0.0, 0.1)

        if st.button("Clear Conversation"):
            st.session_state.messages = []
            st.session_state.summary = None
            st.session_state.history_for_api = []
            st.rerun()

        st.markdown("---")
        st.subheader("Current Summary")
        if st.session_state.summary:
            st.info(st.session_state.summary)
        else:
            st.text("No summary yet.")

    # Main chat interface
    col1, col2 = st.columns([0.8, 0.2])
    with col1:
        st.title("🤖 Local AI Agent")
    with col2:
        if st.button("Manage Documents"):
            navigate_to("uploads")

    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    if prompt := st.chat_input("What is on your mind?"):
        # Add user message to UI state
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Prepare payload
        payload = {
            "message": prompt,
            "messages": st.session_state.history_for_api, # Send previous history
            "summary": st.session_state.summary,
            "domain": api_domain,
            "model": model_name,
            "system_prompt": system_prompt if system_prompt else None,
            "temperature": temperature,
            "top_p": top_p,
            "max_tokens": max_tokens if max_tokens and max_tokens > 0 else None,
            "presence_penalty": presence_penalty,
            "frequency_penalty": frequency_penalty,
            "stream": enable_streaming # API ignores this for WS, POST ignores it too now
        }
        
        # Filter out None values
        payload = {k: v for k, v in payload.items() if v is not None}

        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""

            if enable_streaming:
                async def run_websocket():
                    uri = f"{WS_BASE_URL}/ws/chat"
                    current_text = ""
                    try:
                        async with websockets.connect(uri) as websocket:
                            await websocket.send(json.dumps(payload))
                            
                            while True:
                                try:
                                    response = await websocket.recv()
                                    data = json.loads(response)
                                    
                                    if "content" in data:
                                        content = data["content"]
                                        current_text += content
                                        message_placeholder.markdown(current_text + "▌")
                                    
                                    elif "metadata" in data:
                                        message_placeholder.markdown(current_text)
                                        return current_text, data["metadata"]
                                    
                                    elif "error" in data:
                                        st.error(f"Error: {data['error']}")
                                        return None, None
                                        
                                except websockets.exceptions.ConnectionClosed:
                                    break
                    except Exception as e:
                        st.error(f"Connection failed: {e}")
                        return None, None
                    return current_text, None

                # Run async loop
                result_text, metadata = asyncio.run(run_websocket())
                
                if result_text:
                    full_response = result_text
                    # Update state from metadata if available
                    if metadata:
                        new_summary = metadata.get("updated_summary")
                        if new_summary and new_summary != st.session_state.summary:
                            st.session_state.summary = new_summary
                            st.toast("Conversation summarized!", icon="📝")
                        # We could update history from API, but for UI consistency let's just append our local assistant msg
                        # Actually, API returns the FULL updated history including the new assistant message.
                        # It's safer to use that for the next request context.
                        api_history = metadata.get("updated_history", [])
                        # Convert dicts back to clean format if needed, primarily we just need the list of dicts/objects
                        # Pydantic models dump to dicts in api response
                        
                        # We need to construct the list of Message objects (or dicts matching schema) for the next call
                        # The schemas.Message has 'role' and 'content'.
                        # api_history is list of dicts.
                        st.session_state.history_for_api = []
                        for msg in api_history:
                            st.session_state.history_for_api.append({"role": msg["role"], "content": msg["content"]})
            
            else:
                # Non-streaming HTTP
                try:
                    response = requests.post(f"{API_BASE_URL}/chat", json=payload)
                    response.raise_for_status()
                    data = response.json()
                    
                    full_response = data["response"]
                    message_placeholder.markdown(full_response)
                    
                    # Update state
                    new_summary = data.get("updated_summary")
                    if new_summary and new_summary != st.session_state.summary:
                         st.session_state.summary = new_summary
                         st.toast("Conversation summarized!", icon="📝")
                    api_history = data.get("updated_history", [])
                    st.session_state.history_for_api = []
                    for msg in api_history:
                         st.session_state.history_for_api.append({"role": msg["role"], "content": msg["content"]})

                except Exception as e:
                     st.error(f"API Error: {e}")

        # Append assistant response to UI history
        if full_response:
            st.session_state.messages.append({"role": "assistant", "content": full_response})

# --- UPLOADS PAGE ---
elif st.session_state.page == "uploads":
    col1, col2 = st.columns([0.8, 0.2])
    with col1:
        st.title("📂 Document Management")
    with col2:
        if st.button("Back to Chat"):
            navigate_to("chat")
    
    st.subheader("Upload New Document")
    with st.form("upload_form"):
        uploaded_file = st.file_uploader("Choose a file")
        domain = st.text_input("Domain (Folder Name)", value="general", help="Creates a subfolder in uploads/ with this name.")
        submit_button = st.form_submit_button("Upload")
        
        if submit_button and uploaded_file:
            files = {"file": (uploaded_file.name, uploaded_file, uploaded_file.type)}
            data = {"domain": domain}
            try:
                response = requests.post(f"{API_BASE_URL}/upload", files=files, data=data)
                if response.status_code == 200:
                    st.success(f"Uploaded {uploaded_file.name} to domain '{domain}' successfully!")
                else:
                    st.error(f"Upload failed: {response.text}")
            except Exception as e:
                st.error(f"Error: {e}")

    st.markdown("---")
    st.subheader("Existing Documents")
    
    try:
        response = requests.get(f"{API_BASE_URL}/documents")
        if response.status_code == 200:
            documents = response.json()
            if documents:
                # Group by domain
                domains = {}
                for doc in documents:
                    domain = doc['domain']
                    if domain not in domains:
                        domains[domain] = []
                    domains[domain].append(doc)
                
                for domain, docs in domains.items():
                    with st.expander(f"📁 {domain}", expanded=True):
                        for doc in docs:
                            st.text(f"📄 {doc['filename']} ({doc['size']} bytes) - {doc['created_at']}")
            else:
                st.info("No documents found.")
        else:
            st.error("Failed to fetch documents.")
    except Exception as e:
        st.error(f"Error: {e}")
