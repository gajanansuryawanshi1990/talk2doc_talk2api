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
        
        # Define RAG as a tool for the agent
        self.rag_tool = {
            "type": "function",
            "function": {
                "name": "search_documents",
                "description": "Search through uploaded documents and PDFs to find relevant information. Use this when the user asks about document content, wants information from PDFs, or asks questions that require document-based knowledge.",
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
        }
        
        # Combine RAG tool with MCP tools from mcp_client
        self.agent_tools = [self.rag_tool] + (TOOLS_SPEC or [])
    
    async def _execute_rag_tool(self, query: str, top_k: int = 5) -> Dict[str, Any]:
        """Execute RAG search tool"""
        try:
            print(f"\n[RAG Tool] Searching documents for: {query}")
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
                "error": f"Error searching documents: {str(e)}",
                "answer": "Failed to search documents.",
                "sources": []
            }
 
    async def process_query(self, query: str, history: List[Dict[str, str]], top_k: int = 5, uploaded_pdf_path: Optional[str] = None) -> PipelineResult:
        start = time.time()
        tools_used = []
        sources = []
        debug = {}
        
        try:
            # Build conversation messages
            messages: List[Dict[str, Any]] = [
                {
                    "role": "system",
                    "content": (
                        "You are a helpful AI assistant with access to document search and healthcare database tools. "
                        "For casual conversation (greetings, thanks, general chat), respond naturally without using tools. "
                        "For document-related questions, use the search_documents tool. "
                        "For healthcare operations (patient queries, doctor information, studies), use the appropriate healthcare tools like get_patient_by_id, get_all_patients, get_doctor_by_id, etc. "
                        "You can use tools when needed, but respond directly for simple conversational queries."
                    ),
                }
            ]
            
            # Add conversation history
            for m in history:
                messages.append({
                    "role": m.get("role", "user"),
                    "content": m.get("content", "")
                })
            
            # Add current query
            messages.append({"role": "user", "content": query})
            
            print(f"\n[Agent] Processing query: {query}")
            
            # Call agent with tools
            response = self.agent_client.chat.completions.create(
                model=AZURE_OPENAI_CHAT_MODEL,
                messages=messages,
                tools=self.agent_tools,
                tool_choice="auto",
            )
            
            response_message = response.choices[0].message
            tool_calls = getattr(response_message, "tool_calls", None)
            
            if tool_calls:
                print(f"[Agent] Tool calls detected: {len(tool_calls)}")
                messages.append(response_message)
                
                # Execute each tool call
                for tc in tool_calls:
                    func_name = tc.function.name
                    tools_used.append(func_name)
                    
                    print(f"[Agent] Executing tool: {func_name}")
                    
                    try:
                        args = json.loads(tc.function.arguments) if isinstance(tc.function.arguments, str) else tc.function.arguments
                    except Exception:
                        args = tc.function.arguments
                    
                    tool_result = None
                    
                    # Execute appropriate tool
                    if func_name == "search_documents":
                        # RAG tool execution
                        tool_result = await self._execute_rag_tool(
                            query=args.get("query", query),
                            top_k=args.get("top_k", top_k)
                        )
                        if tool_result.get("success"):
                            sources = tool_result.get("sources", [])
                    
                    else:
                        # MCP tool execution - use call_fastapi_tool from mcp_client
                        try:
                            print(f"[MCP Tool] Calling {func_name} with args: {args}")
                            mcp_output = await call_fastapi_tool(tc)
                            
                            tool_result = {
                                "success": True,
                                "data": mcp_output,
                                "tool": func_name
                            }
                            
                            # Log MCP operations
                            if "mcp_operations" not in debug:
                                debug["mcp_operations"] = []
                            debug["mcp_operations"].append({
                                "tool": func_name,
                                "args": args,
                                "result": mcp_output
                            })
                            
                            print(f"[MCP Tool] Result: {mcp_output}")
                            
                        except Exception as mcp_err:
                            print(f"[MCP Tool Error] {str(mcp_err)}")
                            tool_result = {
                                "success": False,
                                "error": f"MCP tool error: {str(mcp_err)}",
                                "tool": func_name
                            }
                    
                    # Add tool result to messages
                    if tool_result:
                        messages.append({
                            "tool_call_id": tc.id,
                            "role": "tool",
                            "name": func_name,
                            "content": json.dumps(tool_result),
                        })
                
                # Get final response from agent
                print("[Agent] Getting final response with tool results...")
                final_response = self.agent_client.chat.completions.create(
                    model=AZURE_OPENAI_CHAT_MODEL,
                    messages=messages
                )
                final_answer = final_response.choices[0].message.content or ""
            else:
                # No tool calls - direct conversational response
                print("[Agent] No tools needed - direct response")
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
            print(f"\n[Agent Error] {error_msg}")
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
    
    print("AI Agent with RAG and MCP Tools")
    print("=" * 60)
    print("Try different types of queries:")
    print("  Conversational: 'Hi', 'Thank you', 'How are you?'")
    print("  Document Search: 'What does the document say about X?'")
    print("  Healthcare: 'Get patient details for ID 1'")
    print("  Healthcare: 'Show me all patients'")
    print("  Healthcare: 'Get doctor information for ID 1'")
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
                print(f"📊 MCP Operations:")
                for op in result.debug["mcp_operations"]:
                    print(f"   - {op['tool']}: {op['args']}")
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