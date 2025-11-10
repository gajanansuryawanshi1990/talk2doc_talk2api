# import os, sys
# import json
# import time
# import asyncio
# from typing import Dict, Any, List, Optional
# from dotenv import load_dotenv
# from openai import AzureOpenAI
# from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings
# from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
# from langchain_core.output_parsers import StrOutputParser
# from pydantic import BaseModel
 
# # Import your existing components
# ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
# if ROOT_DIR not in sys.path:
#     sys.path.insert(0, ROOT_DIR)

# from src.adapters.rag_chat import retrieve_context, build_context_text, ask_llm
# from src.clients.mcp_client import TOOLS_SPEC, call_fastapi_tool
 
# load_dotenv()
 
# def get_env_var(key, default=None, required=False):
#     val = os.getenv(key, default)
#     if val is not None:
#         val = val.strip().replace('"', '').replace("'", "")
#     if required and not val:
#         raise ValueError(f"Missing required environment variable: {key}")
#     return val
 
# AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
# AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
# AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
# AZURE_OPENAI_CHAT_MODEL = os.getenv("AZURE_OPENAI_CHAT_MODEL")
# AZURE_OPENAI_EMBED_MODEL = os.getenv("AZURE_OPENAI_EMBED_MODEL")
 
# class PipelineResult(BaseModel):
#     answer: str
#     tools_used: List[str] = []
#     sources: Optional[List[Dict[str, Any]]] = []
#     debug: Optional[Dict[str, Any]] = {}
#     latency_ms: Optional[int] = None
 
# class LangChainOrchestrator:
#     def __init__(self):
#         # Initialize Azure OpenAI client for agent with tool-calling
#         self.agent_client = AzureOpenAI(
#             api_key=AZURE_OPENAI_API_KEY,
#             azure_endpoint=AZURE_OPENAI_ENDPOINT,
#             api_version=AZURE_OPENAI_API_VERSION
#         )
        
#         self.embeddings = AzureOpenAIEmbeddings(
#             azure_deployment=AZURE_OPENAI_EMBED_MODEL,
#             openai_api_version=AZURE_OPENAI_API_VERSION,
#             azure_endpoint=AZURE_OPENAI_ENDPOINT,
#             openai_api_key=AZURE_OPENAI_API_KEY,
#         )
        
#         # Define RAG as a tool for the agent
#         self.rag_tool = {
#             "type": "function",
#             "function": {
#                 "name": "search_documents",
#                 "description": "Search through uploaded documents and PDFs to find relevant information. Use this when the user asks about document content, wants information from PDFs, or asks questions that require document-based knowledge.",
#                 "parameters": {
#                     "type": "object",
#                     "properties": {
#                         "query": {
#                             "type": "string",
#                             "description": "The search query to find relevant information in documents"
#                         },
#                         "top_k": {
#                             "type": "integer",
#                             "description": "Number of top results to retrieve (default: 5)",
#                             "default": 5
#                         }
#                     },
#                     "required": ["query"]
#                 }
#             }
#         }
        
#         # Combine RAG tool with MCP tools from mcp_client
#         self.agent_tools = [self.rag_tool] + (TOOLS_SPEC or [])
    
#     async def _execute_rag_tool(self, query: str, top_k: int = 5) -> Dict[str, Any]:
#         """Execute RAG search tool"""
#         try:
#             print(f"\n[RAG Tool] Searching documents for: {query}")
#             chunks = retrieve_context(query, k=top_k)
#             context_text = build_context_text(chunks)
            
#             # Get answer from LLM with context
#             answer = ask_llm(query, context_text, [])
            
#             return {
#                 "success": True,
#                 "answer": answer,
#                 "sources": chunks,
#                 "num_sources": len(chunks)
#             }
#         except Exception as e:
#             return {
#                 "success": False,
#                 "error": f"Error searching documents: {str(e)}",
#                 "answer": "Failed to search documents.",
#                 "sources": []
#             }
 
#     async def process_query(self, query: str, history: List[Dict[str, str]], top_k: int = 5, uploaded_pdf_path: Optional[str] = None) -> PipelineResult:
#         start = time.time()
#         tools_used = []
#         sources = []
#         debug = {}
        
#         try:
#             # Build conversation messages
#             messages: List[Dict[str, Any]] = [
#                 {
#                     "role": "system",
#                     "content": (
#                         "You are a helpful AI assistant with access to document search and healthcare database tools. "
#                         "For casual conversation (greetings, thanks, general chat), respond naturally without using tools. "
#                         "For document-related questions, use the search_documents tool. "
#                         "For healthcare operations (patient queries, doctor information, studies), use the appropriate healthcare tools like get_patient_by_id, get_all_patients, get_doctor_by_id, etc. "
#                         "You can use tools when needed, but respond directly for simple conversational queries."
#                     ),
#                 }
#             ]
            
#             # Add conversation history
#             for m in history:
#                 messages.append({
#                     "role": m.get("role", "user"),
#                     "content": m.get("content", "")
#                 })
            
#             # Add current query
#             messages.append({"role": "user", "content": query})
            
#             print(f"\n[Agent] Processing query: {query}")
            
#             # Call agent with tools
#             response = self.agent_client.chat.completions.create(
#                 model=AZURE_OPENAI_CHAT_MODEL,
#                 messages=messages,
#                 tools=self.agent_tools,
#                 tool_choice="auto",
#             )
            
#             response_message = response.choices[0].message
#             tool_calls = getattr(response_message, "tool_calls", None)
            
#             if tool_calls:
#                 print(f"[Agent] Tool calls detected: {len(tool_calls)}")
#                 messages.append(response_message)
                
#                 # Execute each tool call
#                 for tc in tool_calls:
#                     func_name = tc.function.name
#                     tools_used.append(func_name)
                    
#                     print(f"[Agent] Executing tool: {func_name}")
                    
#                     try:
#                         args = json.loads(tc.function.arguments) if isinstance(tc.function.arguments, str) else tc.function.arguments
#                     except Exception:
#                         args = tc.function.arguments
                    
#                     tool_result = None
                    
#                     # Execute appropriate tool
#                     if func_name == "search_documents":
#                         # RAG tool execution
#                         tool_result = await self._execute_rag_tool(
#                             query=args.get("query", query),
#                             top_k=args.get("top_k", top_k)
#                         )
#                         if tool_result.get("success"):
#                             sources = tool_result.get("sources", [])
                    
#                     else:
#                         # MCP tool execution - use call_fastapi_tool from mcp_client
#                         try:
#                             print(f"[MCP Tool] Calling {func_name} with args: {args}")
#                             mcp_output = await call_fastapi_tool(tc)
                            
#                             tool_result = {
#                                 "success": True,
#                                 "data": mcp_output,
#                                 "tool": func_name
#                             }
                            
#                             # Log MCP operations
#                             if "mcp_operations" not in debug:
#                                 debug["mcp_operations"] = []
#                             debug["mcp_operations"].append({
#                                 "tool": func_name,
#                                 "args": args,
#                                 "result": mcp_output
#                             })
                            
#                             print(f"[MCP Tool] Result: {mcp_output}")
                            
#                         except Exception as mcp_err:
#                             print(f"[MCP Tool Error] {str(mcp_err)}")
#                             tool_result = {
#                                 "success": False,
#                                 "error": f"MCP tool error: {str(mcp_err)}",
#                                 "tool": func_name
#                             }
                    
#                     # Add tool result to messages
#                     if tool_result:
#                         messages.append({
#                             "tool_call_id": tc.id,
#                             "role": "tool",
#                             "name": func_name,
#                             "content": json.dumps(tool_result),
#                         })
                
#                 # Get final response from agent
#                 print("[Agent] Getting final response with tool results...")
#                 final_response = self.agent_client.chat.completions.create(
#                     model=AZURE_OPENAI_CHAT_MODEL,
#                     messages=messages
#                 )
#                 final_answer = final_response.choices[0].message.content or ""
#             else:
#                 # No tool calls - direct conversational response
#                 print("[Agent] No tools needed - direct response")
#                 final_answer = response_message.content or ""
            
#             latency = int((time.time() - start) * 1000)
            
#             return PipelineResult(
#                 answer=final_answer,
#                 tools_used=tools_used,
#                 sources=sources,
#                 debug={
#                     **debug,
#                     "tool_calls_made": len(tools_used),
#                     "direct_response": len(tools_used) == 0
#                 },
#                 latency_ms=latency
#             )
            
#         except Exception as e:
#             error_msg = f"Error processing query: {str(e)}"
#             print(f"\n[Agent Error] {error_msg}")
#             import traceback
#             traceback.print_exc()
            
#             latency = int((time.time() - start) * 1000)
            
#             return PipelineResult(
#                 answer="I apologize, but I encountered an error processing your request. Please try again.",
#                 tools_used=tools_used,
#                 sources=[],
#                 debug={"error": error_msg, "traceback": traceback.format_exc()},
#                 latency_ms=latency
#             )
 
# # For testing (CLI)
# if __name__ == "__main__":
#     import asyncio
#     orchestrator = LangChainOrchestrator()
#     history = []
    
#     print("AI Agent with RAG and MCP Tools")
#     print("=" * 60)
#     print("Try different types of queries:")
#     print("  Conversational: 'Hi', 'Thank you', 'How are you?'")
#     print("  Document Search: 'What does the document say about X?'")
#     print("  Healthcare: 'Get patient details for ID 1'")
#     print("  Healthcare: 'Show me all patients'")
#     print("  Healthcare: 'Get doctor information for ID 1'")
#     print("=" * 60)
    
#     while True:
#         query = input("\n💬 You: ")
#         if query.lower() in ['exit', 'quit', 'bye']:
#             print("Goodbye!")
#             break
        
#         result = asyncio.run(orchestrator.process_query(query, history))
        
#         print("\n" + "=" * 60)
#         print(f"🤖 Assistant: {result.answer}")
#         print("-" * 60)
#         print(f"⚡ Latency: {result.latency_ms}ms")
        
#         if result.tools_used:
#             print(f"🔧 Tools Used: {', '.join(result.tools_used)}")
#             if result.debug.get("mcp_operations"):
#                 print(f"📊 MCP Operations:")
#                 for op in result.debug["mcp_operations"]:
#                     print(f"   - {op['tool']}: {op['args']}")
#         else:
#             print("💭 Direct Response (No tools used)")
        
#         if result.sources:
#             print(f"📚 Sources Found: {len(result.sources)}")
        
#         if result.debug.get("error"):
#             print(f"❌ Error: {result.debug['error']}")
        
#         print("=" * 60)
        
#         # Add to history
#         history.append({"role": "user", "content": query})
#         history.append({"role": "assistant", "content": result.answer})

#orchestrator 
import os, sys
import json
import time
import asyncio
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
from openai import AzureOpenAI
from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from pydantic import BaseModel
 
# Import your existing components
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from src.adapters.rag_chat import retrieve_context, build_context_text, ask_llm
from src.clients.mcp_client import TOOLS_SPEC, call_fastapi_tool
 
load_dotenv()
 
def get_env_var(key, default=None, required=False):
    val = os.getenv(key, default)
    if val is not None:
        val = val.strip().replace('"', '').replace("'", "")
    if required and not val:
        raise ValueError(f"Missing required environment variable: {key}")
    return val
 
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
AZURE_OPENAI_CHAT_MODEL = os.getenv("AZURE_OPENAI_CHAT_MODEL")
AZURE_OPENAI_EMBED_MODEL = os.getenv("AZURE_OPENAI_EMBED_MODEL")
 
class PipelineResult(BaseModel):
    answer: str
    tools_used: List[str] = []
    sources: Optional[List[Dict[str, Any]]] = []
    debug: Optional[Dict[str, Any]] = {}
    latency_ms: Optional[int] = None
 
class LangChainOrchestrator:
    def __init__(self):
        # Initialize Azure OpenAI client for agent with tool-calling
        self.agent_client = AzureOpenAI(
            api_key=AZURE_OPENAI_API_KEY,
            azure_endpoint=AZURE_OPENAI_ENDPOINT,
            api_version=AZURE_OPENAI_API_VERSION
        )
        
        self.embeddings = AzureOpenAIEmbeddings(
            azure_deployment=AZURE_OPENAI_EMBED_MODEL,
            openai_api_version=AZURE_OPENAI_API_VERSION,
            azure_endpoint=AZURE_OPENAI_ENDPOINT,
            openai_api_key=AZURE_OPENAI_API_KEY,
        )
        
        # Define high-level tools for the orchestrator agent
        self.orchestrator_tools = [
            {
                "type": "function",
                "function": {
                    "name": "search_documents",
                    "description": "Search through uploaded documents and PDFs to find relevant information. Use this when the user asks about document content, wants information from PDFs, or asks questions that require document-based knowledge. Do not include source links or citations in your responses.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The search query to find relevant information in documents"
                            },
                            "top_k": {
                                "type": "integer",
                                "description": "Number of top results to retrieve (default: 5)",
                                "default": 5
                            }
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "query_healthcare_system",
                    "description": "Query the healthcare database system for patient data, doctor information, or study records. Use this for any healthcare-related queries like getting patient details, listing doctors, finding studies, etc.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The healthcare query (e.g., 'Get patient details for ID 1', 'List all doctors', 'Show studies for patient 2')"
                            }
                        },
                        "required": ["query"]
                    }
                }
            }
        ]
    
    async def _execute_rag_pipeline(self, query: str, top_k: int = 5) -> Dict[str, Any]:
        """Execute RAG pipeline - similar to rag_chatbot"""
        try:
            print(f"\n[RAG Pipeline] Searching documents for: {query}")
            chunks = retrieve_context(query, k=top_k)
            context_text = build_context_text(chunks)
            
            # Get answer from LLM with context
            answer = ask_llm(query, context_text, [])
            return {
                "success": True,
                "answer": answer,
                "sources": chunks,
                "num_sources": len(chunks)
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error in RAG pipeline: {str(e)}",
                "answer": "Failed to search documents.",
                "sources": []
            }
    
    async def _execute_mcp_pipeline(self, query: str, history: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Execute MCP pipeline - similar to mcp_chatbot.py
        This handles the full MCP conversation with tool calls
        """
        try:
            print(f"\n[MCP Pipeline] Processing healthcare query: {query}")
            
            # Build messages for MCP system
            messages: List[Dict[str, Any]] = [
                {
                    "role": "system",
                    "content": "You are a helpful assistant that can manage patient and doctor information. Use the available tools to answer questions and fulfill requests."
                }
            ]
            
            # Add relevant history (filter to keep it focused)
            for m in history[-6:]:  # Keep last 3 exchanges
                messages.append({
                    "role": m.get("role", "user"),
                    "content": m.get("content", "")
                })
            
            # Add current query
            messages.append({"role": "user", "content": query})
            
            tools_called = []
            
            # Step 1: Send query to model with MCP tools
            response = self.agent_client.chat.completions.create(
                model=AZURE_OPENAI_CHAT_MODEL,
                messages=messages,
                tools=TOOLS_SPEC,  # Use MCP tools from mcp_client
                tool_choice="auto",
            )
            
            response_message = response.choices[0].message
            tool_calls = response_message.tool_calls
            
            # Step 2: Execute tool calls if any
            if tool_calls:
                print(f"[MCP Pipeline] Tool calls detected: {len(tool_calls)}")
                messages.append(response_message)
                
                for tool_call in tool_calls:
                    func_name = tool_call.function.name
                    print(f"[MCP Pipeline] Executing tool: {func_name}")
                    
                    # Execute the tool
                    tool_output = await call_fastapi_tool(tool_call)
                    
                    tools_called.append({
                        "name": func_name,
                        "args": json.loads(tool_call.function.arguments) if isinstance(tool_call.function.arguments, str) else tool_call.function.arguments,
                        "output": tool_output
                    })
                    
                    print(f"[MCP Pipeline] Tool output: {tool_output}")
                    
                    messages.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": func_name,
                        "content": json.dumps(tool_output),
                    })
                
                # Step 3: Get final response after tool execution
                final_response = self.agent_client.chat.completions.create(
                    model=AZURE_OPENAI_CHAT_MODEL,
                    messages=messages,
                )
                final_answer = final_response.choices[0].message.content or ""
            else:
                # Direct response without tools
                final_answer = response_message.content or ""
            
            return {
                "success": True,
                "answer": final_answer,
                "tools_called": tools_called
            }
            
        except Exception as e:
            print(f"[MCP Pipeline Error] {str(e)}")
            return {
                "success": False,
                "error": f"Error in MCP pipeline: {str(e)}",
                "answer": "Failed to process healthcare query.",
                "tools_called": []
            }
 
    async def process_query(self, query: str, history: List[Dict[str, str]], top_k: int = 5, uploaded_pdf_path: Optional[str] = None) -> PipelineResult:
        start = time.time()
        tools_used = []
        sources = []
        debug = {}
        
        try:
            # Build conversation messages for orchestrator
            messages: List[Dict[str, Any]] = [
                {
                    "role": "system",
                    "content": (
               "You are an intelligent orchestrator agent that routes queries to specialized systems. "
"For casual conversation ONLY (greetings like 'hi', 'hello', 'thanks', 'how are you'), respond naturally without using tools. "
"For document-related questions, use the search_documents tool to access the RAG system. "
"For healthcare operations (patient queries, doctor info, studies), use the query_healthcare_system tool to access the MCP system. "
"CRITICAL RULES: "
"1. ONLY answer using the tools provided for factual questions "
"2. For casual greetings and pleasantries (hi, hello, thanks, how are you), respond briefly and naturally "
"3. For ANY factual question (healthcare, general knowledge, trivia, people, events, etc.), you MUST use the available tools "
"4. If the tools do not return relevant information, respond with: 'I cannot help you with that query.' "
"5. DO NOT use your own knowledge base to answer ANY factual questions "
"6. Examples of what to REJECT without tools: 'Who is Michael Jordan?', 'What is diabetes?', 'Tell me about history', etc. "
"7. Examples of what to ALLOW: 'Hi', 'Hello', 'Thank you', 'How are you?', 'Good morning' "
"If a query is not a simple greeting AND the tools don't have relevant data, always respond: 'I cannot help you with that query.'"
                    ),
                }
            ]
            
            # Add conversation history (last few exchanges)
            for m in history[-10:]:  # Keep last 5 exchanges
                messages.append({
                    "role": m.get("role", "user"),
                    "content": m.get("content", "")
                })
            
            # Add current query
            messages.append({"role": "user", "content": query})
            
            print(f"\n[Orchestrator] Processing query: {query}")
            
            # Call orchestrator agent
            response = self.agent_client.chat.completions.create(
                model=AZURE_OPENAI_CHAT_MODEL,
                messages=messages,
                tools=self.orchestrator_tools,
                tool_choice="auto",
            )
            
            response_message = response.choices[0].message
            tool_calls = getattr(response_message, "tool_calls", None)
            
            if tool_calls:
                print(f"[Orchestrator] Tool calls detected: {len(tool_calls)}")
                
                # Execute each tool call
                for tc in tool_calls:
                    func_name = tc.function.name
                    tools_used.append(func_name)
                    
                    print(f"[Orchestrator] Routing to: {func_name}")
                    
                    try:
                        args = json.loads(tc.function.arguments) if isinstance(tc.function.arguments, str) else tc.function.arguments
                    except Exception:
                        args = tc.function.arguments
                    
                    # Route to appropriate pipeline
                    if func_name == "search_documents":
                        # Execute RAG pipeline
                        rag_result = await self._execute_rag_pipeline(
                            query=args.get("query", query),
                            top_k=args.get("top_k", top_k)
                        )
                        
                        if rag_result.get("success"):
                            sources = rag_result.get("sources", [])
                            final_answer = rag_result.get("answer", "")
                            debug["rag_execution"] = {
                                "num_sources": len(sources),
                                "query": args.get("query", query)
                            }
                        else:
                            final_answer = rag_result.get("answer", "Failed to search documents.")
                            debug["rag_error"] = rag_result.get("error")
                    
                    elif func_name == "query_healthcare_system":
                        # Execute MCP pipeline
                        mcp_result = await self._execute_mcp_pipeline(
                            query=args.get("query", query),
                            history=history
                        )
                        
                        if mcp_result.get("success"):
                            final_answer = mcp_result.get("answer", "")
                            mcp_tools = mcp_result.get("tools_called", [])
                            
                            # Track MCP tools used
                            for tool in mcp_tools:
                                tools_used.append(tool["name"])
                            
                            debug["mcp_operations"] = mcp_tools
                            debug["mcp_execution"] = {
                                "query": args.get("query", query),
                                "tools_count": len(mcp_tools)
                            }
                        else:
                            final_answer = mcp_result.get("answer", "Failed to process healthcare query.")
                            debug["mcp_error"] = mcp_result.get("error")
                    
                    else:
                        final_answer = f"Unknown tool: {func_name}"
            
            else:
                # No tool calls - direct conversational response
                print("[Orchestrator] No tools needed - direct response")
                final_answer = response_message.content or ""
            
            latency = int((time.time() - start) * 1000)
            
            return PipelineResult(
                answer=final_answer,
                tools_used=tools_used,
                sources=sources,
                debug={
                    **debug,
                    "tool_calls_made": len(tools_used),
                    "direct_response": len(tools_used) == 0
                },
                latency_ms=latency
            )
            
        except Exception as e:
            error_msg = f"Error processing query: {str(e)}"
            print(f"\n[Orchestrator Error] {error_msg}")
            import traceback
            traceback.print_exc()
            
            latency = int((time.time() - start) * 1000)
            
            return PipelineResult(
                answer="I apologize, but I encountered an error processing your request. Please try again.",
                tools_used=tools_used,
                sources=[],
                debug={"error": error_msg, "traceback": traceback.format_exc()},
                latency_ms=latency
            )
 
# For testing (CLI)
if __name__ == "__main__":
    import asyncio
    orchestrator = LangChainOrchestrator()
    history = []
    
    print("AI Orchestrator Agent")
    print("=" * 60)
    print("Try different types of queries:")
    print("  Conversational: 'Hi', 'Thank you', 'How are you?'")
    print("  Document Search: 'What does the document say about X?'")
    print("  Healthcare: 'Get patient details for ID 1'")
    print("  Healthcare: 'Show me all patients'")
    print("=" * 60)
    
    while True:
        query = input("\n💬 You: ")
        if query.lower() in ['exit', 'quit', 'bye']:
            print("Goodbye!")
            break
        
        result = asyncio.run(orchestrator.process_query(query, history))
        
        print("\n" + "=" * 60)
        print(f"🤖 Assistant: {result.answer}")
        print("-" * 60)
        print(f"⚡ Latency: {result.latency_ms}ms")
        
        if result.tools_used:
            print(f"🔧 Tools Used: {', '.join(result.tools_used)}")
            if result.debug.get("mcp_operations"):
                print(f"📊 MCP Tools Called:")
                for op in result.debug["mcp_operations"]:
                    print(f"   - {op['name']}: {op['args']}")
        else:
            print("💭 Direct Response (No tools used)")
        
        if result.sources:
            print(f"📚 Sources Found: {len(result.sources)}")
        
        if result.debug.get("error"):
            print(f"❌ Error: {result.debug['error']}")
        
        print("=" * 60)
        
        # Add to history
        history.append({"role": "user", "content": query})
        history.append({"role": "assistant", "content": result.answer})