import os
import sys
import json
from dotenv import load_dotenv
import asyncio
 
# Load environment variables from .env file
load_dotenv()

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
 
from openai import AzureOpenAI
# Import the tools specification and the tool execution function from mcp_client.py
from src.clients.mcp_client import TOOLS_SPEC, call_fastapi_tool
 
# Azure OpenAI Configuration
AOAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AOAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AOAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT")
AOAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION")
AOAI_CHAT_MODEL = os.getenv("AZURE_OPENAI_CHAT_MODEL")
 
# You can still define FASTAPI_BASE_URL here if you prefer, or rely on mcp_client.py's default
# FASTAPI_BASE_URL = os.getenv("FASTAPI_BASE_URL", "http://127.0.0.1:8000")
 
 
# Initialize Azure OpenAI Client
client = AzureOpenAI(
    api_key=AOAI_API_KEY,
    azure_endpoint=AOAI_ENDPOINT,
    api_version=AOAI_API_VERSION
)
 
async def run_chatbot():
    print("Welcome to the Patient Management Chatbot!")
    print("Type 'exit' to quit.")
 
    messages = [
        {"role": "system", "content": "You are a helpful assistant that can manage patient and doctor information. Use the available tools to answer questions and fulfill requests."},
    ]
 
    while True:
        user_input = input("\nYou: ")
        if user_input.lower() == 'exit':
            break
 
        messages.append({"role": "user", "content": user_input})
 
        try:
            # Step 1: Send user input and conversation history to the model
            response = client.chat.completions.create(
                model=AOAI_CHAT_MODEL,
                messages=messages,
                tools=TOOLS_SPEC, # Use the imported TOOLS_SPEC
                tool_choice="auto",
            )
 
            response_message = response.choices[0].message
            tool_calls = response_message.tool_calls
 
            # Step 2: Check if the model wants to call a tool
            if tool_calls:
                print("Bot: Calling a tool...")
                messages.append(response_message)  # Add assistant's tool call to conversation
 
                # Step 3: Execute the tool calls using our custom function from mcp_client
                for tool_call in tool_calls:
                    print(f"Executing tool: {tool_call.function.name} with args: {tool_call.function.arguments}")
 
                    # Call the tool execution function imported from mcp_client.py
                    # You can pass base_url here if you want to override the default in mcp_client.py
                    tool_output = await call_fastapi_tool(tool_call)
 
                    print(f"Tool output: {tool_output}")
 
                    messages.append(
                        {
                            "tool_call_id": tool_call.id,
                            "role": "tool",
                            "name": tool_call.function.name,
                            "content": json.dumps(tool_output),
                        }
                    )
 
                # Step 4: Send tool output back to the model for final response
                final_response = client.chat.completions.create(
                    model=AOAI_CHAT_MODEL,
                    messages=messages,
                )
                print(f"Bot: {final_response.choices[0].message.content}")
                messages.append(final_response.choices[0].message)
 
            else:
                # If no tool call, just print the model's direct response
                print(f"Bot: {response_message.content}")
                messages.append(response_message)
 
        except Exception as e:
            print(f"An error occurred: {e}")
            messages.append({"role": "assistant", "content": "I encountered an error. Please try again."})
 
if __name__ == "__main__":
    asyncio.run(run_chatbot())