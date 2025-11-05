# Talk2Doc & Talk2API

A unified application combining RAG (Retrieval-Augmented Generation) for document search and MCP (Model Context Protocol) for API interactions with patient and doctor management systems.

## Project Structure

```
Talk2doc&Talk2API/
├── src/                          # Source code
│   ├── adapters/                 # Data processing adapters
│   │   └── rag_chat.py          # RAG adapter for document search
│   ├── clients/                  # Client implementations
│   │   ├── mcp_client.py        # MCP client for API tools
│   │   └── mcp_chatbot.py       # Chatbot client interface
│   ├── server/                   # Server implementations
│   │   └── mcp_server.py        # FastAPI server for patient/doctor management
│   ├── ui/                       # User interface
│   │   └── app-ui1.py           # Streamlit web UI
│   └── orchestration.py          # CrewAI orchestration between RAG and MCP
│
├── data/                         # Data files
│   ├── excel/                    # Excel spreadsheets
│   │   ├── doctors.xlsx
│   │   ├── patients.xlsx
│   │   └── studies.xlsx
│   └── pdfs/                     # PDF documents
│       ├── Guideline for HIV.pdf
│       ├── Guideline for mental health at work.pdf
│       ├── Guidelines for Malaria.pdf
│       ├── Guidelines for pharma company.pdf
│       └── Guidelines for Right to health in India.pdf
│
├── docs/                         # Documentation
├── config/                       # Configuration files
└── README.md                     # This file

```

## Components

### 1. Orchestration Layer (`src/orchestration.py`)
- **CrewAI-based routing** between RAG and MCP pipelines
- Intelligent query analysis to determine appropriate pipeline
- Supports explicit overrides with `force:rag` or `force:mcp`

### 2. RAG Pipeline (`src/adapters/rag_chat.py`)
- Azure AI Search integration for document retrieval
- Azure OpenAI embeddings and chat completion
- Context building from PDF documents
- Best for: Questions, explanations, summaries, comparisons

### 3. MCP Pipeline
- **MCP Server** (`src/server/mcp_server.py`): FastAPI server with SQL Server backend
  - Patient, Doctor, and Study management endpoints
  - RESTful API design
- **Upload Server** (`src/server/main.py`): FastAPI server for document management
  - PDF upload to Azure Blob Storage
  - Azure AI Search indexer triggering
  - File deletion and cleanup endpoints
- **Client** (`src/clients/mcp_client.py`): Tool specifications and API caller
- **Chatbot** (`src/clients/mcp_chatbot.py`): Terminal-based chatbot interface
- Best for: Creating, updating, deleting records, listing data

### 4. Web UI (`src/ui/app-ui1.py`)
- **Streamlit-based** interactive web interface
- PDF upload and indexing
- Multi-conversation management
- Debug information display
- Automatic routing between RAG and MCP

## Setup

### Prerequisites
- Python 3.8+
- SQL Server (SQLEXPRESS22 or similar)
- Azure OpenAI account
- Azure AI Search account

### Environment Variables
Create a `.env` file in the root directory:

```env
# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT=<your-endpoint>
AZURE_OPENAI_API_KEY=<your-key>
AZURE_OPENAI_API_VERSION=2024-06-01
AZURE_OPENAI_CHAT_DEPLOYMENT=<your-chat-model>
AZURE_OPENAI_EMBED_DEPLOYMENT=<your-embedding-model>

# Azure OpenAI for Orchestration
AZURE_OPENAI_ORCH_ENDPOINT=<your-endpoint>
AZURE_OPENAI_API_ORCH_KEY=<your-key>
AZURE_OPENAI_API_ORCH_VERSION=2024-06-01
AZURE_OPENAI_CHAT_ORCH_DEPLOYMENT=<your-chat-model>

# Azure AI Search
AZURE_SEARCH_ENDPOINT=<your-search-endpoint>
AZURE_SEARCH_INDEX=<your-index-name>
AZURE_SEARCH_KEY=<your-search-key>

# Optional
USER_ID=mayur
SESSION_ID=local-session
```

### Installation

```bash
pip install -r requirements.txt
```

## Usage

### 1. Start the MCP Server (Database API)
```bash
python src/server/mcp_server.py
```
Server runs on: `http://127.0.0.1:8001`

### 2. Start the Upload Server (Document Management)
```bash
uvicorn src.server.main:app --reload --host 127.0.0.1 --port 8080
```
Server runs on: `http://127.0.0.1:8080`

### 3. Run the Web UI
```bash
streamlit run src/ui/app-ui1.py
```

### 4. Use the Chatbot (Terminal)
```bash
python src/clients/mcp_chatbot.py
```

## Features

### RAG Features
- Vector search across PDF documents
- Azure AI Search integration
- Contextual answers with source citations
- Support for multiple document types

### MCP Features
- Patient management (CRUD operations)
- Doctor management (CRUD operations)
- Study tracking
- Relational data queries
- SQL Server backend

### Orchestration Features
- Automatic pipeline selection
- CrewAI agent-based routing
- Support for manual override
- Detailed debug information
- Conversation context management

## API Endpoints

### Upload Server (`http://127.0.0.1:8080`)

#### Document Management
- `POST /upload/` - Upload PDF to Azure Blob Storage and trigger indexer
- `DELETE /delete-file/{filename}` - Delete a specific file (protected files cannot be deleted)
- `DELETE /cleanup-temporary-pdfs` - Clean up all temporary PDFs (keeps protected files)
- `POST /trigger-indexer` - Manually trigger Azure AI Search indexer
- `GET /` - Server status and information

### MCP Server (`http://127.0.0.1:8001`)

#### Patients
- `GET /patients` - List all patients
- `GET /patient/{patient_id}` - Get patient by ID
- `GET /patient/{patient_id}/doctors` - Get doctors for a patient
- `GET /patient/{patient_id}/studies` - Get studies for a patient

#### Doctors
- `GET /doctors` - List all doctors
- `GET /doctor/{doctor_id}` - Get doctor by ID
- `GET /doctor/{doctor_id}/studies` - Get studies for a doctor

#### Studies
- `GET /studies` - List all studies
- `GET /study/{study_id}` - Get study by ID

## Tips

### Query Routing
- Use **RAG** for: "What is...", "Explain...", "How to...", "Summarize..."
- Use **MCP** for: "Get patient 123", "List all doctors", "Create appointment..."
- Force routing: Add `force:rag` or `force:mcp` to your query

### Debug Mode
Enable debug mode in the web UI settings to see:
- Selected route (RAG/MCP)
- Latency information
- Sources/Tools used
- Router decision details

## Development

### Adding New Features
1. **New RAG features**: Modify `src/adapters/rag_chat.py`
2. **New MCP endpoints**: Add to `src/server/mcp_server.py`
3. **New tools**: Update `src/clients/mcp_client.py`
4. **UI changes**: Modify `src/ui/app-ui1.py`

### Project Structure Benefits
- **Modular**: Clear separation of concerns
- **Scalable**: Easy to add new components
- **Maintainable**: Organized by functionality
- **Testable**: Each component can be tested independently

## Troubleshooting

### Database Connection Issues
- Verify SQL Server is running
- Check connection string in `src/server/mcp_server.py`
- Ensure firewall allows connections

### Azure Services Issues
- Verify all environment variables are set
- Check endpoint URLs don't contain placeholders
- Ensure API keys are valid

### Import Errors
- Ensure all `__init__.py` files exist
- Verify PYTHONPATH includes project root
- Check virtual environment is activated

## License

[Your License Here]

## Contributors

[Your Name]
