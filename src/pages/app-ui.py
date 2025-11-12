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

# Authentication check

if 'authenticated' not in st.session_state or not st.session_state.authenticated:
    st.error("🚫 Access Denied! Please login first.")
    st.info("🔄 Redirecting to login page...")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🔐 Go to Login", type="primary", use_container_width=True):
            st.switch_page("login.py")
    
    st.stop()
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
    
    # User info and logout
    st.markdown("### 👤 User Info")
    st.markdown(f"**Logged in as:** {st.session_state.get('username', 'Unknown User')}")
    
    if st.button("🚪 Logout", use_container_width=True, type="secondary"):
        st.session_state.authenticated = False
        st.session_state.username = ""
        # Clear all session data
        for key in list(st.session_state.keys()):
            if key not in ['authenticated', 'username']:
                del st.session_state[key]
        st.success("✅ Logged out successfully!")
        time.sleep(1)
        st.switch_page("login.py")
    
    st.markdown("---")
    
    # Clear Chat Section
    st.markdown("### 💬 Chat Management")
    if st.button("🗑️ Clear Current Chat", use_container_width=True, type="secondary"):
        # Clear the current chat history
        st.session_state["history"] = []
        st.session_state["conversations"][st.session_state["active_chat_id"]] = []
        st.success("✅ Chat cleared!")
        time.sleep(1)
        st.rerun()
    
    
    role = st.session_state.role

    if role == "admin":

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
        # with col3:
        #     if sources:
        #         st.metric("📚 Sources", len(sources))
        #     else:
        #         st.metric("📚 Sources", "0")
       
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
        # if sources:
        #     with st.expander(f"🔎 Retrieved Document Context ({len(sources)} chunks)", expanded=False):
        #         for i, chunk in enumerate(sources, 1):
        #             st.markdown(f"**Chunk {i}** — *{chunk.get('source', 'Unknown Source')}*")
        #             with st.container():
        #                 st.text_area(
        #                     f"Content {i}",
        #                     chunk.get("content", ""),
        #                     height=100,
        #                     key=f"chunk_{i}_{st.session_state['active_chat_id']}_{len(st.session_state['history'])}",
        #                     label_visibility="collapsed"
        #                 )
        #             st.markdown("---")
       
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
       
        # Show QnT Metrics if available
        if result.qnt_metrics:
            with st.expander("📊 Quality & Trust (QnT) Metrics", expanded=True):
                qnt = result.qnt_metrics
               
                # Create metrics display
                col_qnt1, col_qnt2, col_qnt3, col_qnt4 = st.columns(4)
               
                with col_qnt1:
                    rouge_score = qnt.get("rouge_avg", 0.0)
                    st.metric(
                        "📝 ROUGE Score",
                        f"{rouge_score:.3f}",
                        help="Measures overlap with source content (0-1, higher is better)"
                    )
                    # Color indicator
                    if rouge_score >= 0.5:
                        st.success("✓ Good overlap")
                    elif rouge_score >= 0.3:
                        st.warning("⚠ Moderate overlap")
                    else:
                        st.error("✗ Low overlap")
               
                with col_qnt2:
                    bleu_score = qnt.get("bleu", 0.0)
                    st.metric(
                        "🎯 BLEU Score",
                        f"{bleu_score:.3f}",
                        help="Measures n-gram precision (0-1, higher is better)"
                    )
                    if bleu_score >= 0.3:
                        st.success("✓ Good precision")
                    elif bleu_score >= 0.15:
                        st.warning("⚠ Moderate precision")
                    else:
                        st.error("✗ Low precision")
               
                with col_qnt3:
                    faithfulness_score = qnt.get("faithfulness", 0.0)
                    st.metric(
                        "✅ Faithfulness",
                        f"{faithfulness_score:.3f}",
                        help="Measures factual grounding in context (0-1, higher is better)"
                    )
                    if faithfulness_score >= 0.7:
                        st.success("✓ Highly faithful")
                    elif faithfulness_score >= 0.4:
                        st.warning("⚠ Moderately faithful")
                    else:
                        st.error("✗ Low faithfulness")
               
                with col_qnt4:
                    toxicity_score = qnt.get("toxicity", 0.0)
                    st.metric(
                        "🛡️ Toxicity",
                        f"{toxicity_score:.3f}",
                        help="Measures harmful content (0-1, lower is better)"
                    )
                    if toxicity_score <= 0.2:
                        st.success("✓ Safe content")
                    elif toxicity_score <= 0.5:
                        st.warning("⚠ Moderate toxicity")
                    else:
                        st.error("✗ High toxicity")
               
                # Show faithfulness reasoning if available
                if qnt.get("faithfulness_reasoning"):
                    st.markdown("**Faithfulness Analysis:**")
                    st.info(qnt["faithfulness_reasoning"])
               
                # Show detailed metrics in collapsible section
                if qnt.get("full_evaluation"):
                    with st.expander("🔬 Detailed QnT Analysis", expanded=False):
                        full_eval = qnt["full_evaluation"]
                       
                        # ROUGE details
                        if "rouge" in full_eval:
                            st.markdown("**ROUGE Breakdown:**")
                            rouge_data = full_eval["rouge"]
                            col_r1, col_r2, col_r3 = st.columns(3)
                            with col_r1:
                                st.metric("ROUGE-1", f"{rouge_data.get('rouge1', 0):.4f}")
                            with col_r2:
                                st.metric("ROUGE-2", f"{rouge_data.get('rouge2', 0):.4f}")
                            with col_r3:
                                st.metric("ROUGE-L", f"{rouge_data.get('rougeL', 0):.4f}")
                       
                        # Toxicity details
                        if "toxicity" in full_eval and isinstance(full_eval["toxicity"], dict):
                            st.markdown("**Toxicity Breakdown:**")
                            tox_data = full_eval["toxicity"]
                            col_t1, col_t2, col_t3 = st.columns(3)
                            with col_t1:
                                st.metric("Severe Toxicity", f"{tox_data.get('severe_toxicity', 0):.4f}")
                                st.metric("Obscene", f"{tox_data.get('obscene', 0):.4f}")
                            with col_t2:
                                st.metric("Threat", f"{tox_data.get('threat', 0):.4f}")
                                st.metric("Insult", f"{tox_data.get('insult', 0):.4f}")
                            with col_t3:
                                st.metric("Identity Attack", f"{tox_data.get('identity_attack', 0):.4f}")
       
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
 