#orchestrator with QnT metrics
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
import re
from qnteval.qnt import evaluate_task
import uuid
 
# Import your existing components
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
 
from src.adapters.rag_chat import retrieve_context, build_context_text, ask_llm, get_unique_sources, format_sources_list
from src.clients.mcp_client import TOOLS_SPEC, call_fastapi_tool
 
# Import QnT metrics
try:
    from QNT.qnt import QnTMetrics
    QNT_AVAILABLE = True
except ImportError:
        QNT_AVAILABLE = False
        print("Warning: QnT metrics not available.")
 
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
    qnt_metrics: Optional[Dict[str, Any]] = None  # Added QnT metrics
 
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
       
        # Initialize QnT metrics evaluator
        self.qnt_evaluator = QnTMetrics() if QNT_AVAILABLE else None
       
        # Define high-level tools for the orchestrator agent
        self.orchestrator_tools = [
            {
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
           
            # Get answer from LLM with context - pass chunks for source formatting
            # Note: For sub-queries, we might want a simpler answer without full source formatting here,
            # and let the orchestrator format the final sources.
            # However, for consistency, we'll keep ask_llm's full behavior.
            answer = ask_llm(query, context_text, [], chunks)
            #==================================================
            case_id = str(uuid.uuid4())
            session_id = str(uuid.uuid4())
            task = "Q & A"
            query = query
            response = answer
            context = context_text
            latency = 0 # Latency is not applicable for this pipeline
            cost = 0
            res = evaluate_task(case_id, session_id, task, query, response, context, latency, cost)
            print(f"[RAG Pipeline] QnT Evaluation: {res}")
            #==================================================
           
            # Extract just the answer part if ask_llm adds source formatting.
            # The orchestrator will handle final source aggregation.
            answer_lines = answer.split('\n')
            final_rag_answer = []
            rag_sources_extracted = []
            for line in answer_lines:
                if line.lower().startswith("sources:") or line.lower().startswith("source:"):
                    # Extract sources from the RAG answer for aggregation by orchestrator
                    source_match = re.search(r'(?i)(?:Sources:|Source:)\s*(.*)', line)
                    if source_match:
                        # Split by newline and then by number for multi-line sources
                        raw_sources = source_match.group(1).strip()
                        if "\n" in raw_sources: # Multiple sources formatted with numbers
                            for src_line in raw_sources.split('\n'):
                                num_src_match = re.search(r'^\d+\.\s*(.+\.pdf)', src_line.strip(), re.IGNORECASE)
                                if num_src_match:
                                    rag_sources_extracted.append(num_src_match.group(1).strip())
                        elif raw_sources.lower().endswith('.pdf'): # Single source
                            rag_sources_extracted.append(raw_sources)
                    break # Stop processing lines after finding sources
                final_rag_answer.append(line)
           
            return {
                "success": True,
                "answer": "\n".join(final_rag_answer).strip(), # Only the answer part
                "sources": chunks, # Raw chunks for source processing by orchestrator
                "identified_sources": rag_sources_extracted, # Sources identified by RAG LLM
                "num_chunks": len(chunks),
                "context_text": context_text,
                "qnt_eval": res, 
            }
        except Exception as e:
            print(f"[RAG Pipeline Error] {str(e)}")
            return {
                "success": False,
                "error": f"Error in RAG pipeline: {str(e)}",
                "answer": "Failed to search documents.",
                "sources": [],
                "identified_sources": [],
                "context_text": "",
                "qnt_eval": None,
            }
   
    async def _execute_mcp_pipeline(self, query: str, history: List[Dict[str, str]], user_id: Optional[str] = None, user_role: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute MCP pipeline - similar to mcp_chatbot.py
        This handles the full MCP conversation with tool calls
        """
        try:
            print(f"\n[MCP Pipeline] Processing healthcare query: {query}")
           
            # Build messages for MCP system and include user context for access control
            messages: List[Dict[str, Any]] = [
                {
                    "role": "system",
                    "content": "You are a helpful assistant that can manage patient and employee information. Use the available tools to answer questions and fulfill requests. Enforce role-based access: admins can access any employee data; users may only access their own data (use provided user_id)."
                }
            ]
           
            if user_id:
                messages.append({"role": "system", "content": f"Requesting user_id: {user_id}, role: {user_role}"})

            # Add relevant history (filter to keep it focused)
            # For sub-queries, we generally don't pass history to this inner call to avoid confusion.
            # The orchestrator manages overall history.
           
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
                   
                    try:
                        args = json.loads(tool_call.function.arguments) if isinstance(tool_call.function.arguments, str) else tool_call.function.arguments
                    except json.JSONDecodeError:
                        args = tool_call.function.arguments # Keep as string if not valid JSON
                   
                    # Execute the tool and pass user context to enforce access control
                    tool_output = await call_fastapi_tool(tool_call, user_id=user_id, user_role=user_role)
                   
                    tools_called.append({
                        "name": func_name,
                        "args": args,
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
 
    async def process_query(self, query: str, history: List[Dict[str, str]], user_id: Optional[str] = None, user_role: Optional[str] = None, top_k: int = 5, uploaded_pdf_path: Optional[str] = None, enable_qnt: bool = True) -> PipelineResult:
        start = time.time()

        # Initialize lists to accumulate results
        all_tools_used = []
        all_sources_for_ui = [] # For displaying individual chunks and their sources
        all_unique_final_sources = set() # For the final formatted sources list
        all_debug_info = {}
        all_context_texts = [] # For QnT evaluation

        try:
            # Build conversation messages for orchestrator
            messages: List[Dict[str, Any]] = [
                {
                    "role": "system",
                    "content": (
                       "You are an intelligent orchestrator agent that routes queries to specialized systems. "
                       "Your primary goal is to answer the user's question comprehensively and accurately. "
                       "Carefully analyze the user's query to determine if it is a multi-part question or if it requires information from different domains. "
                       "If a query can be broken down, you MUST break it down into smaller, distinct sub-queries and call the appropriate tools for each part. "
                       "After calling tools and getting their outputs, you MUST synthesize all information into a single, coherent, and complete answer. "
                       "For casual conversation ONLY (greetings like 'hi', 'hello', 'thanks', 'how are you'), respond naturally without using tools. "
                       "For document-related questions, use the 'search_documents' tool to access the RAG system. "
                       "For healthcare operations (employee queries, employee info, employee id, date of joinging of employee), use the 'query_healthcare_system' tool to access the MCP system. "
                       "CRITICAL RULES: "
                       "1. ONLY answer using the information returned by the tools for factual questions. "
                       "2. For casual greetings and pleasantries, respond briefly and naturally. "
                       "3. For ANY factual question (healthcare, employee details, employee id, general knowledge, trivia, people, events, etc.), you MUST use the available tools. "
                       "4. If the tools do not return relevant information for a factual question, respond with: 'I cannot help you with that query.' "
                       "5. DO NOT use your own knowledge base to answer ANY factual questions. "
                    #    "6. Examples of what to REJECT without tools: 'Who is Michael Jordan?', 'What is diabetes?', 'Tell me about history', etc. "
                       "6. Examples of what to ALLOW: 'Hi', 'Hello', 'Thank you', 'How are you?', 'Good morning'. "
                       "If a query is not a simple greeting AND the tools don't have relevant data, always respond: 'I cannot help you with that query.' "
                       "At the end of your final synthesized answer, include a 'Sources' section. "
                       "List ONLY the unique document names (e.g., 'document1.pdf') that were actually used from the 'search_documents' tool output. "
                       "Format sources as a numbered list if more than one, or 'Source: document1.pdf' if only one. If no documents were used, omit the Sources section."
                    ),
                }
            ]

            # If a user_id is provided, make it available to the orchestrator and tools
            if user_id or user_role:
                messages.append({
                    "role": "system",
                    "content": f"Current user_id: {user_id}, role: {user_role}. Use this context when calling healthcare or employee-related tools."
                })

            # Add conversation history (last few exchanges)
            for m in history[-10:]:  # Keep last 5 exchanges
                messages.append({
                    "role": m.get("role", "user"),
                    "content": m.get("content", "")
                })

            # Add current query
            messages.append({"role": "user", "content": query})
           
            print(f"\n[Orchestrator] Processing query: {query}")
           
            # Orchestrator Loop for multi-tool execution
            max_tool_iterations = 5 # Limit to prevent infinite loops
           
            for i in range(max_tool_iterations):
                response = self.agent_client.chat.completions.create(
                    model=AZURE_OPENAI_CHAT_MODEL,
                    messages=messages,
                    tools=self.orchestrator_tools,
                    tool_choice="auto", # Allow the model to decide if it needs a tool
                )
               
                response_message = response.choices[0].message
                tool_calls = getattr(response_message, "tool_calls", None)
               
                if tool_calls:
                    print(f"[Orchestrator] Tool calls detected (Iteration {i+1}): {len(tool_calls)}")
                    messages.append(response_message) # Add assistant's tool call message
                   
                    for tc in tool_calls:
                        func_name = tc.function.name
                        all_tools_used.append(func_name)
                       
                        print(f"[Orchestrator] Routing to: {func_name}")
                       
                        try:
                            args = json.loads(tc.function.arguments) if isinstance(tc.function.arguments, str) else tc.function.arguments
                        except json.JSONDecodeError:
                            args = tc.function.arguments # Keep as string if not valid JSON
                       
                        tool_output_content = None # To store output for tool message
                       
                        if func_name == "search_documents":
                            rag_result = await self._execute_rag_pipeline(
                                query=args.get("query", ""), # Ensure query is passed
                                top_k=args.get("top_k", top_k)
                            )
                            if rag_result.get("qnt_eval") is not None:
                               all_debug_info.setdefault("rag_qnt_evals", []).append(rag_result.get("qnt_eval"))
                               all_debug_info.setdefault("qnt_eval", []).append(rag_result.get("qnt_eval"))
                            
                            tool_output_content = json.dumps({
                                "answer": rag_result.get("answer"),
                                "identified_sources": rag_result.get("identified_sources"),
                                "error": rag_result.get("error")
                            })
 
                            if rag_result.get("success"):
                                # Accumulate all chunks for UI display
                                all_sources_for_ui.extend(rag_result.get("sources", []))
                                # Accumulate unique sources identified by RAG LLM for final formatting
                                for s in rag_result.get("identified_sources", []):
                                    all_unique_final_sources.add(s)
                                all_context_texts.append(rag_result.get("context_text", ""))
                               
                                if "rag_executions" not in all_debug_info:
                                    all_debug_info["rag_executions"] = []
                                all_debug_info["rag_executions"].append({
                                    "query": args.get("query", ""),
                                    "num_chunks": rag_result.get("num_chunks", 0),
                                    "identified_sources": rag_result.get("identified_sources", [])
                                })
                            else:
                                if "rag_errors" not in all_debug_info:
                                    all_debug_info["rag_errors"] = []
                                all_debug_info["rag_errors"].append(rag_result.get("error"))
                       
                        elif func_name == "query_healthcare_system":
                            mcp_result = await self._execute_mcp_pipeline(
                                query=args.get("query", ""), # Ensure query is passed
                                history=[], # Don't pass history to sub-pipeline, orchestrator manages overall
                                user_id=user_id,
                                user_role=user_role
                            )
                            tool_output_content = json.dumps({
                                "answer": mcp_result.get("answer"),
                                "tools_called": [t["name"] for t in mcp_result.get("tools_called", [])],
                                "error": mcp_result.get("error")
                            })
 
                            if mcp_result.get("success"):
                                mcp_tools_used = [tool["name"] for tool in mcp_result.get("tools_called", [])]
                                all_tools_used.extend(mcp_tools_used) # Accumulate MCP tools
                               
                                if "mcp_operations_results" not in all_debug_info:
                                    all_debug_info["mcp_operations_results"] = []
                                all_debug_info["mcp_operations_results"].append({
                                    "query": args.get("query", ""),
                                    "result_answer": mcp_result.get("answer"),
                                    "mcp_tools_used": mcp_tools_used
                                })
                            else:
                                if "mcp_errors" not in all_debug_info:
                                    all_debug_info["mcp_errors"] = []
                                all_debug_info["mcp_errors"].append(mcp_result.get("error"))
                       
                        else:
                            tool_output_content = json.dumps({"error": f"Unknown tool: {func_name}"})
                            if "orchestrator_errors" not in all_debug_info:
                                all_debug_info["orchestrator_errors"] = []
                            all_debug_info["orchestrator_errors"].append(f"Unknown tool called: {func_name}")
 
                        messages.append({
                            "tool_call_id": tc.id,
                            "role": "tool",
                            "name": func_name,
                            "content": tool_output_content, # Add the actual tool output
                        })
                   
                    # After executing all tool calls, loop again to potentially call more tools or get a final answer
                    # continue
                else:
                    # No tool calls detected, meaning the model is ready to give a final answer
                    break # Exit the loop, the next call will be for final synthesis
           
            # Final step: Get the synthesized answer from the orchestrator
            final_response = self.agent_client.chat.completions.create(
                model=AZURE_OPENAI_CHAT_MODEL,
                messages=messages,
            )
            final_answer_raw = final_response.choices[0].message.content or ""
           
            # Format unique sources
            final_formatted_sources = ""
            if all_unique_final_sources:
                sources_list = format_sources_list(list(all_unique_final_sources))
                if len(all_unique_final_sources) == 1:
                    final_formatted_sources = f"\n\nSource: {sources_list}"
                else:
                    final_formatted_sources = f"\n\nSources:\n{sources_list}"
           
            # Append final sources to the answer, ensuring it's not duplicated if LLM already added it
            if all_unique_final_sources and not (
                "sources:" in final_answer_raw.lower() or "source:" in final_answer_raw.lower()
            ):
                final_answer = final_answer_raw + final_formatted_sources
            else:
                final_answer = final_answer_raw
 
 
            # Calculate QnT metrics if enabled and we have context
            qnt_metrics = None
            if enable_qnt and self.qnt_evaluator and all_context_texts:
                try:
                    print("[Orchestrator] Calculating QnT metrics...")
                    # Combine all context texts for overall QnT evaluation
                    combined_context = "\n\n".join(all_context_texts)
                    evaluation = self.qnt_evaluator.evaluate_response(
                        query=query,
                        answer=final_answer,
                        context=combined_context, # Use combined context
                        reference_answer=None
                    )
                    qnt_metrics = self.qnt_evaluator.get_summary_metrics(evaluation)
                    qnt_metrics["full_evaluation"] = evaluation  # Store full results
                    all_debug_info["qnt_calculated"] = True
                except Exception as e:
                    print(f"[Orchestrator] QnT calculation error: {e}")
                    all_debug_info["qnt_error"] = str(e)
           
            latency = int((time.time() - start) * 1000)
           
            return PipelineResult(
                answer=final_answer,
                tools_used=all_tools_used,
                sources=all_sources_for_ui, # Pass all retrieved chunks for UI display
                debug={
                    **all_debug_info,
                    "tool_calls_made": len(all_tools_used),
                    "direct_response": len(all_tools_used) == 0
                },
                latency_ms=latency,
                qnt_metrics=qnt_metrics
            )
           
        except Exception as e:
            error_msg = f"Error processing query: {str(e)}"
            print(f"\n[Orchestrator Error] {error_msg}")
            import traceback
            traceback.print_exc()
           
            latency = int((time.time() - start) * 1000)
           
            return PipelineResult(
                answer="I apologize, but I encountered an error processing your request. Please try again.",
                tools_used=all_tools_used,
                sources=[],
                debug={"error": error_msg, "traceback": traceback.format_exc()},
                latency_ms=latency,
                qnt_metrics=None
            )
