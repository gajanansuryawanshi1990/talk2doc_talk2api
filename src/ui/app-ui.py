import streamlit as st
import asyncio
import os, sys

# Make src importable
SRC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)
 
from orchestration import LangChainOrchestrator
import requests
 
 
# Page config
st.set_page_config(page_title="AI Agent Chatbot", page_icon="🤖", layout="centered")
 
# Initialize session state
if "orchestrator" not in st.session_state:
    st.session_state["orchestrator"] = LangChainOrchestrator()
 
if "history" not in st.session_state:
    st.session_state["history"] = []
 
if "conversations" not in st.session_state:
    st.session_state["conversations"] = {}
    st.session_state["chat_titles"] = {}
    st.session_state["next_chat_num"] = 1
 
if "active_chat_id" not in st.session_state:
    cid = f"chat-{st.session_state['next_chat_num']}"
    st.session_state["next_chat_num"] += 1
    st.session_state["conversations"][cid] = []
    st.session_state["chat_titles"][cid] = f"New chat {st.session_state['next_chat_num']}"
    st.session_state["active_chat_id"] = cid
    st.session_state["history"] = st.session_state["conversations"][cid]
 
# ---------------- SIDEBAR ----------------
with st.sidebar:
   
    st.title("Upload PDF and Trigger Indexer")
 
    uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")
 
    if uploaded_file is not None:
        if st.button("Upload and Trigger Indexer"):
            files = {"file": (uploaded_file.name, uploaded_file, "application/pdf")}
            try:
                response = requests.post("http://localhost:8000/upload/", files=files)
                if response.status_code == 200:
                    st.success("✅ File uploaded and indexer triggered!")
                else:
                    st.error(f"❌ Error: {response.text}")
            except Exception as e:
                st.error(f"❌ Connection error: {str(e)}")
 
 
    st.markdown("---")
    st.markdown("### 💬 Conversations")
 
    chat_ids = list(st.session_state["conversations"].keys())
    titles = [st.session_state["chat_titles"].get(cid, "Untitled") for cid in chat_ids]
 
    if chat_ids:
        try:
            current_index = chat_ids.index(st.session_state["active_chat_id"])
        except ValueError:
            current_index = 0
 
        selected_title = st.radio("Switch conversation", titles, index=current_index, label_visibility="collapsed")
        sel_idx = titles.index(selected_title)
        st.session_state["active_chat_id"] = chat_ids[sel_idx]
        st.session_state["history"] = st.session_state["conversations"][st.session_state["active_chat_id"]]
    else:
        st.info("No conversations yet")
 
    if st.button("＋ New chat", type="primary", use_container_width=True, key="new_chat_sidebar"):
        n = st.session_state["next_chat_num"]
        cid = f"chat-{n}"
        st.session_state["next_chat_num"] += 1
        st.session_state["conversations"][cid] = []
        st.session_state["chat_titles"][cid] = f"New chat {n}"
        st.session_state["active_chat_id"] = cid
        st.session_state["history"] = st.session_state["conversations"][cid]
        st.rerun()
 
    st.write("")
 
    if st.button("🗑️ Delete current chat", use_container_width=True, key="delete_chat_sidebar"):
        cid = st.session_state.get("active_chat_id")
        if cid:
            st.session_state["conversations"].pop(cid, None)
            st.session_state["chat_titles"].pop(cid, None)
            remaining = list(st.session_state["conversations"].keys())
            if remaining:
                st.session_state["active_chat_id"] = remaining[0]
            else:
                new_cid = f"chat-{st.session_state['next_chat_num']}"
                st.session_state["next_chat_num"] += 1
                st.session_state["conversations"][new_cid] = []
                st.session_state["chat_titles"][new_cid] = f"New chat {st.session_state['next_chat_num']}"
                st.session_state["active_chat_id"] = new_cid
            st.session_state["history"] = st.session_state["conversations"][st.session_state["active_chat_id"]]
        st.rerun()
 
    # st.markdown("---")
    # st.markdown("### ℹ️ About")
    # st.markdown("""
    # **AI Agent with Tools:**
    # - 🔍 Document Search (RAG)
    # - 🏥 Healthcare Database (MCP)
    # - 💭 Natural Conversation
    
    # The agent decides which tools to use based on your query.
    # """)

# ---------------- MAIN UI ----------------
cols = st.columns([1, 5, 1])
with cols[1]:
    st.markdown("""
        <div style="text-align:center;">
            <h1 style="margin-bottom:0;">🤖 AI Agent Chatbot</h1>
        </div>
    """, unsafe_allow_html=True)
 
# Display chat history
if st.session_state["history"]:
    for msg in st.session_state["history"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
 
# Chat input
prompt = st.chat_input("Ask about documents, healthcare data, or just say hi...")
if prompt:
    st.session_state["history"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
 
    try:
        with st.spinner("🤔 Thinking..."):
            # Run async process_query
            result = asyncio.run(
                st.session_state["orchestrator"].process_query(
                    query=prompt,
                    history=st.session_state["history"][:-1],  # Exclude the current user message
                )
            )
 
        # Render assistant answer
        answer = result.answer
        with st.chat_message("assistant"):
            st.markdown(answer)
        st.session_state["history"].append({"role": "assistant", "content": answer})
 
        # Show tool usage and additional info
        tools_used = result.tools_used
        sources = result.sources
        debug = result.debug
        latency_ms = result.latency_ms
        
        # Create metrics row
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("⚡ Latency", f"{latency_ms}ms")
        with col2:
            if tools_used:
                st.metric("🔧 Tools Used", len(tools_used))
            else:
                st.metric("💭 Response Type", "Direct")
        with col3:
            if sources:
                st.metric("📚 Sources", len(sources))
            else:
                st.metric("📚 Sources", "0")
        
        # Show tools used
        if tools_used:
            with st.expander(f"🔧 Tools Used: {', '.join(tools_used)}", expanded=False):
                for tool in tools_used:
                    if tool == "search_documents":
                        st.markdown("**📄 Document Search Tool**")
                        st.caption("Searched through uploaded documents")
                    else:
                        st.markdown(f"**🏥 Healthcare Tool: `{tool}`**")
                        st.caption("Queried healthcare database")
        
        # Show RAG sources if available
        if sources:
            with st.expander(f"🔎 Retrieved Document Context ({len(sources)} chunks)", expanded=False):
                for i, chunk in enumerate(sources, 1):
                    st.markdown(f"**Chunk {i}** — *{chunk.get('source', 'Unknown Source')}*")
                    with st.container():
                        st.text_area(
                            f"Content {i}",
                            chunk.get("content", ""),
                            height=100,
                            key=f"chunk_{i}_{st.session_state['active_chat_id']}_{len(st.session_state['history'])}",
                            label_visibility="collapsed"
                        )
                    st.markdown("---")
        
        # Show MCP operations if available
        if debug.get("mcp_operations"):
            with st.expander("🏥 Healthcare Database Operations", expanded=False):
                mcp_ops = debug["mcp_operations"]
                st.markdown(f"**Total Operations:** {len(mcp_ops)}")
                for i, op in enumerate(mcp_ops, 1):
                    st.markdown(f"### Operation {i}: `{op['tool']}`")
                    
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.markdown("**Arguments:**")
                        st.json(op.get("args", {}))
                    with col_b:
                        st.markdown("**Result:**")
                        st.json(op.get("result", {}))
                    
                    if i < len(mcp_ops):
                        st.markdown("---")
        
        # Show debug info if there are errors
        if debug.get("error"):
            with st.expander("⚠️ Debug Information", expanded=True):
                st.error(debug["error"])
                if debug.get("traceback"):
                    st.code(debug["traceback"], language="text")
        
        # Show all debug info in collapsed expander
        if debug and not debug.get("error"):
            with st.expander("🔍 Debug Information", expanded=False):
                st.json(debug)
 
    except Exception as e:
        with st.chat_message("assistant"):
            st.error(f"❌ Something went wrong: {e}")
            import traceback
            with st.expander("Error Details"):
                st.code(traceback.format_exc())