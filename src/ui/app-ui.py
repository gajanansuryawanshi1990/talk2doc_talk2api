# app-ui.py
import streamlit as st
import asyncio
import os, sys
import time
import base64
from urllib.parse import urlparse
 

# Make src importable
SRC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)
 
from orchestration import LangChainOrchestrator
import requests
 
 
# Page config
st.set_page_config(page_title="AI Chatbot", page_icon="🤖", layout="centered")

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
   
    # Clear Chat Section
    st.markdown("### 💬 Chat Management")
    if st.button("🗑️ Clear Current Chat", use_container_width=True, type="secondary"):
        # Clear the current chat history
        st.session_state["history"] = []
        st.session_state["conversations"][st.session_state["active_chat_id"]] = []
        st.success("✅ Chat cleared!")
        time.sleep(1)
        st.rerun()
    
    st.markdown("---")
 
    # Upload Section
    st.markdown("### 📄 Upload your data")
    uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")
 
    if uploaded_file is not None:
        if st.button("📤 Upload and Index", use_container_width=True):
            files = {"file": (uploaded_file.name, uploaded_file, "application/pdf")}
            try:
                # Create a placeholder for the loading animation
                loading_placeholder = st.empty()
                
                with loading_placeholder.container():
                    st.info("⏳ Step 1/2: Uploading file...")
                    progress_bar = st.progress(0)
                    
                response = requests.post("http://localhost:8000/upload/", files=files)
                
                if response.status_code == 200:
                    with loading_placeholder.container():
                        st.info("⚙️ Step 2/2: Indexing document (this takes ~35 seconds)...")
                        progress_bar = st.progress(0)
                        
                        # Simulate progress over 35 seconds
                        for percent in range(0, 101, 5):
                            time.sleep(1.75)  # 35 seconds / 20 steps = 1.75 seconds per step
                            progress_bar.progress(percent)
                    
                    loading_placeholder.empty()
                    st.success("✅ File uploaded and indexed successfully!")
                    time.sleep(2)  # Show success message briefly
                    st.rerun()  # Refresh the page
                else:
                    loading_placeholder.empty()
                    st.error(f"❌ Error: {response.text}")
            except Exception as e:
                st.error(f"❌ Connection error: {str(e)}")
    
    st.markdown("---")
    
    # Cleanup Section
    st.markdown("### ☠️ Clean your data!!! ")
    st.caption("Remove all uploaded PDFs for data privacy")
    
    if st.button("🧹 Reset & Cleanup Index", use_container_width=True, type="secondary"):
        try:
            # Create a placeholder for the loading animation
            loading_placeholder = st.empty()
            
            with loading_placeholder.container():
                st.warning("⏳ Step 1/2: Deleting files and clearing index...")
                progress_bar = st.progress(0)
                
            response = requests.post("http://localhost:8000/reset-index-and-cleanup")
            
            if response.status_code == 200:
                result = response.json()
                summary = result.get("summary", {})
                
                with loading_placeholder.container():
                    st.info("⚙️ Step 2/2: Rebuilding index (this takes ~35 seconds)...")
                    progress_bar = st.progress(0)
                    
                    # Simulate progress over 35 seconds
                    for percent in range(0, 101, 5):
                        time.sleep(1.75)  # 35 seconds / 20 steps = 1.75 seconds per step
                        progress_bar.progress(percent)
                
                loading_placeholder.empty()
                st.success("✅ Cleanup completed successfully!")
                
                # Show detailed results
                with st.expander("📊 Cleanup Details", expanded=True):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Blobs Deleted", summary.get("blobs_deleted", 0))
                        st.metric("Index Docs Cleared", summary.get("index_cleared", 0))
                    with col2:
                        st.metric("Blobs Kept", summary.get("blobs_kept", 0))
                        st.metric("Indexer Triggered", "✅" if summary.get("indexer_triggered") else "❌")
                    
                    # Show deleted files
                    blob_cleanup = result.get("results", {}).get("blob_cleanup", {})
                    deleted_files = blob_cleanup.get("deleted_files", [])
                    if deleted_files:
                        st.markdown("**Deleted Files:**")
                        for f in deleted_files:
                            st.text(f"• {f}")
                
                time.sleep(2)  # Show success message briefly
                st.rerun()  # Refresh the page
            else:
                loading_placeholder.empty()
                st.error(f"❌ Error: {response.text}")
        except Exception as e:
            st.error(f"❌ Connection error: {str(e)}")
             
# ---------------- MAIN UI ----------------
cols = st.columns([1, 5, 1])
with cols[1]:
    st.markdown("""
        <div style="text-align:center;">
            <h1 style="margin-bottom:0;">🤖 AI Chatbot</h1>
            <p style="color:#6b7280;margin-top:4px;">Ask me about documents, healthcare data, or just chat!</p>
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
        # import pdb; pdb.set_trace()
        answer = result.answer
        with st.chat_message("assistant"):
            st.markdown(answer) 
        st.session_state["history"].append({"role": "assistant", "content": answer})
 
        # Show tool usage and additional info
        tools_used = result.tools_used
        sources = result.sources
        debug = result.debug
        latency_ms = result.latency_ms
        if len(sources) > 0:
            encoded_source = sources[0].get('source')


            if len(encoded_source) % 4 == 1:
                encoded_source = encoded_source[:-1]

            # Add padding if needed
            missing_padding = len(encoded_source) % 4
            if missing_padding:
                encoded_source += '=' * (4 - missing_padding)

            # Decode and extract file name
            decoded_url = base64.b64decode(encoded_source).decode('utf-8')
            file_name = os.path.basename(urlparse(decoded_url).path)

            print("File name:", file_name)
 
        
        # Create metrics row with better source display
        col1, col2, col3 = st.columns([1, 1, 1.5])  # Give more space to sources column
        
        with col1:
            st.markdown(
                f"""<div style='text-align: center;'>
                    <p style='font-weight: bold; margin-bottom: 5px; font-size: 14px;'>⚡ Latency</p>
                    <p style='
                        font-size: 12px; 
                        color: #666; 
                        margin: 0;
                        background-color: #f0f2f6;
                        padding: 4px 8px;
                        border-radius: 4px;
                    '>{latency_ms}ms</p>
                </div>""", 
                unsafe_allow_html=True
            )
            
        with col2:
            if tools_used:
                st.markdown(
                    f"""<div style='text-align: center;'>
                        <p style='font-weight: bold; margin-bottom: 5px; font-size: 14px;'>🔧 Tools Used</p>
                        <p style='
                            font-size: 12px; 
                            color: #666; 
                            margin: 0;
                            background-color: #f0f2f6;
                            padding: 4px 8px;
                            border-radius: 4px;
                        '>{len(tools_used)}</p>
                    </div>""", 
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    f"""<div style='text-align: center;'>
                        <p style='font-weight: bold; margin-bottom: 5px; font-size: 14px;'>💭 Response Type</p>
                        <p style='
                            font-size: 12px; 
                            color: #666; 
                            margin: 0;
                            background-color: #f0f2f6;
                            padding: 4px 8px;
                            border-radius: 4px;
                        '>Direct</p>
                    </div>""", 
                    unsafe_allow_html=True
                )
                
        with col3:
            if sources:
                st.markdown(
                    f"""<div>
                        <p style='font-weight: bold; margin-bottom: 5px; font-size: 14px; text-align: center;'>📚 Document Source</p>
                        <div style='
                            background-color: #e8f4f8; 
                            padding: 8px 10px; 
                            border-radius: 6px; 
                            border-left: 3px solid #0066cc;
                            font-size: 11px;
                            word-wrap: break-word;
                            overflow-wrap: break-word;
                            line-height: 1.3;
                        '>
                            📄 {file_name}
                        </div>
                    </div>""", 
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    f"""<div style='text-align: center;'>
                        <p style='font-weight: bold; margin-bottom: 5px; font-size: 14px;'>📚 Sources</p>
                        <p style='
                            font-size: 12px; 
                            color: #666; 
                            margin: 0;
                            background-color: #f0f2f6;
                            padding: 4px 8px;
                            border-radius: 4px;
                        '>0</p>
                    </div>""", 
                    unsafe_allow_html=True
                )
        
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
                    st.markdown(f"**Chunk {file_name}** — *{chunk.get('source', 'Unknown Source')}*")
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
                    tool_name = op.get('tool', op.get('name', 'Unknown Tool'))
                    st.markdown(f"### Operation {i}: `{tool_name}`")
                    
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.markdown("**Arguments:**")
                        st.json(op.get("args", op.get("arguments", {})))
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