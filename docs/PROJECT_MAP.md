# Visual Project Map

## 📂 Complete Project Structure

```
Talk2doc&Talk2API/
│
├── 🚀 QUICK START FILES
│   ├── launch.bat                    # Double-click to start (Windows)
│   ├── launch.ps1                    # PowerShell launcher script
│   ├── README.md                     # Main project documentation
│   └── PROJECT_SUMMARY.md            # This reorganization summary
│
├── ⚙️ CONFIGURATION
│   ├── .env                          # Your environment variables (DO NOT COMMIT)
│   ├── .env.example                  # Template for environment variables
│   ├── .gitignore                    # Git ignore rules
│   └── requirements.txt              # Python dependencies
│
├── 📂 src/                           # SOURCE CODE
│   │
│   ├── orchestration.py              # 🎯 Main orchestrator (CrewAI routing)
│   │   └── Routes queries to RAG or MCP pipeline
│   │
│   ├── 📂 adapters/                  # DATA PROCESSING
│   │   ├── __init__.py
│   │   └── rag_chat.py              # 📚 RAG implementation
│   │       ├── retrieve_context()    # Azure AI Search retrieval
│   │       ├── build_context_text()  # Context formatting
│   │       └── ask_llm()            # Azure OpenAI completion
│   │
│   ├── 📂 clients/                   # CLIENT IMPLEMENTATIONS
│   │   ├── __init__.py
│   │   ├── mcp_client.py            # 🔧 MCP client tools
│   │   │   ├── TOOLS_SPEC           # Tool definitions
│   │   │   └── call_fastapi_tool()  # API caller
│   │   └── mcp_chatbot.py           # 💬 Terminal chatbot
│   │       └── Interactive CLI interface
│   │
│   ├── 📂 server/                    # SERVER IMPLEMENTATIONS
│   │   ├── __init__.py
│   │   ├── mcp_server.py            # 🌐 FastAPI server (Database)
│   │   │   ├── /patients            # Patient endpoints
│   │   │   ├── /doctors             # Doctor endpoints
│   │   │   └── /studies             # Study endpoints
│   │   └── main.py                  # 📤 FastAPI server (Upload)
│   │       ├── /upload/             # PDF upload endpoint
│   │       ├── /delete-file/        # File deletion endpoint
│   │       └── /trigger-indexer     # Indexer trigger endpoint
│   │
│   └── 📂 ui/                        # USER INTERFACES
│       ├── __init__.py
│       └── app-ui1.py               # 🎨 Streamlit web UI
│           ├── Chat interface
│           ├── PDF upload
│           └── Conversation management
│
├── 📂 data/                          # DATA FILES
│   │
│   ├── 📂 excel/                     # Excel Spreadsheets
│   │   ├── doctors.xlsx             # Doctor information
│   │   ├── patients.xlsx            # Patient records
│   │   └── studies.xlsx             # Medical studies
│   │
│   └── 📂 pdfs/                      # PDF Documents
│       ├── Guideline for HIV.pdf
│       ├── Guideline for mental health at work.pdf
│       ├── Guidelines for Malaria.pdf
│       ├── Guidelines for pharma company.pdf
│       └── Guidelines for Right to health in India.pdf
│
├── 📂 docs/                          # DOCUMENTATION
│   ├── SETUP.md                     # 📖 Setup instructions
│   ├── COMMANDS.md                   # 📝 Command reference
│   ├── ARCHITECTURE.md               # 🏗️ System architecture
│   └── MIGRATION.md                  # 🔄 Migration guide
│
└── 📂 config/                        # CONFIGURATION FILES
    └── (Future: app configs, logging configs, etc.)
```

## 🎯 File Purposes

### Entry Points
| File | Purpose | How to Run |
|------|---------|------------|
| `launch.bat` | Quick launcher (double-click) | Double-click file |
| `launch.ps1` | PowerShell launcher menu | `.\launch.ps1` |
| `src/server/mcp_server.py` | FastAPI server (Database) | `python src\server\mcp_server.py` |
| `src/server/main.py` | FastAPI server (Upload) | `uvicorn src.server.main:app --reload --host 127.0.0.1 --port 8080` |
| `src/ui/app-ui1.py` | Streamlit web UI | `streamlit run src\ui\app-ui1.py` |
| `src/clients/mcp_chatbot.py` | Terminal chatbot | `python src\clients\mcp_chatbot.py` |

### Core Components
| File | Responsibility |
|------|---------------|
| `src/orchestration.py` | Routes queries between RAG and MCP using CrewAI |
| `src/adapters/rag_chat.py` | Handles document search and retrieval |
| `src/clients/mcp_client.py` | Defines MCP tools and API calls |
| `src/server/mcp_server.py` | Provides REST API for patient/doctor data |
| `src/server/main.py` | Provides REST API for PDF upload and indexing |

### Configuration
| File | Purpose |
|------|---------|
| `.env` | Your actual credentials (NEVER commit) |
| `.env.example` | Template for required variables |
| `requirements.txt` | Python package dependencies |
| `.gitignore` | Files to exclude from git |

### Documentation
| File | Content |
|------|---------|
| `README.md` | Complete project overview |
| `PROJECT_SUMMARY.md` | Reorganization summary |
| `docs/SETUP.md` | Installation and setup |
| `docs/COMMANDS.md` | Quick command reference |
| `docs/ARCHITECTURE.md` | Technical architecture |
| `docs/MIGRATION.md` | Migration from old structure |

## 🔄 Data Flow Diagram

### RAG Flow (Document Queries)
```
User Query
    ↓
Streamlit UI (src/ui/app-ui1.py)
    ↓
Orchestrator (src/orchestration.py)
    ↓ [Routes to RAG]
RAG Adapter (src/adapters/rag_chat.py)
    ↓
1. Embed Query
    ↓
2. Azure AI Search (Vector Search)
    ↓
3. Build Context
    ↓
4. Azure OpenAI LLM
    ↓
Answer + Sources
```

### MCP Flow (Database Queries)
```
User Query
    ↓
Streamlit UI (src/ui/app-ui1.py)
    ↓
Orchestrator (src/orchestration.py)
    ↓ [Routes to MCP]
MCP Client (src/clients/mcp_client.py)
    ↓
FastAPI Server (src/server/mcp_server.py)
    ↓
SQL Server Database
    ↓
1. Execute Query
    ↓
2. Format Response
    ↓
3. Azure OpenAI (Natural Language)
    ↓
Answer + Tool Results
```

## 📊 Component Relationships

```
┌─────────────────────────────────────────────┐
│           User Interfaces                   │
│  ┌──────────────┐      ┌─────────────┐     │
│  │ Streamlit UI │      │  Chatbot    │     │
│  └──────────────┘      └─────────────┘     │
└──────────────┬────────────────┬─────────────┘
               │                │
               └────────┬───────┘
                        ↓
            ┌───────────────────────┐
            │   Orchestrator        │
            │   (CrewAI Routing)    │
            └───────────────────────┘
                        │
            ┌───────────┴───────────┐
            ↓                       ↓
    ┌──────────────┐        ┌─────────────┐
    │ RAG Pipeline │        │ MCP Pipeline│
    └──────────────┘        └─────────────┘
            │                       │
            ↓                       ↓
    ┌──────────────┐        ┌─────────────┐
    │ Azure AI     │        │ FastAPI     │
    │ Search +     │        │ Server +    │
    │ OpenAI       │        │ SQL Server  │
    └──────────────┘        └─────────────┘
```

## 🎨 Color Coding

- 🚀 **Entry Points** - Files you run directly
- ⚙️ **Configuration** - Settings and dependencies
- 📂 **Source Code** - Python modules
- 📊 **Data** - Excel and PDF files
- 📖 **Documentation** - Guides and references
- 🎯 **Core Logic** - Main business logic
- 🔧 **Tools** - Utility functions
- 💬 **Interfaces** - User interaction
- 🌐 **APIs** - REST endpoints
- 📚 **RAG** - Document search
- 🎨 **UI** - Visual interfaces

## 🔍 Finding What You Need

### To modify UI:
→ `src/ui/app-ui1.py`

### To add new API endpoint:
→ `src/server/mcp_server.py`

### To change routing logic:
→ `src/orchestration.py`

### To improve RAG:
→ `src/adapters/rag_chat.py`

### To add new tools:
→ `src/clients/mcp_client.py`

### To update data:
→ `data/excel/` or `data/pdfs/`

### To read documentation:
→ `docs/` folder or `README.md`

## 📈 Size Overview

```
Total Files: ~25
Total Directories: 10
Python Files: ~8
Data Files: 8 (3 Excel + 5 PDF)
Documentation Files: 6
Configuration Files: 4
```

## ✨ Benefits of This Structure

### Before (Flat Structure)
❌ All files mixed together  
❌ Hard to navigate  
❌ No clear organization  
❌ Difficult to maintain  
❌ Poor scalability  

### After (Organized Structure)
✅ Clear separation of concerns  
✅ Easy to find files  
✅ Professional layout  
✅ Easy to maintain  
✅ Highly scalable  
✅ Beginner-friendly  
✅ IDE-friendly  
✅ Version control ready  

---

**Your project is now professionally organized and ready for development!** 🎉
