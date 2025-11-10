# Architecture Overview

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Web UI (Streamlit)                    │
│                     src/ui/app-ui1.py                        │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  Orchestrator (CrewAI)                       │
│                  src/orchestration.py                        │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Router Agent                                         │  │
│  │  - Analyzes user intent                              │  │
│  │  - Selects appropriate pipeline                      │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────┬───────────────────────────────┬────────────────┘
             │                               │
             ▼                               ▼
┌────────────────────────┐    ┌──────────────────────────────┐
│   RAG Pipeline         │    │   MCP Pipeline               │
│   src/adapters/        │    │   src/clients/               │
│                        │    │                              │
│  ┌──────────────────┐ │    │  ┌────────────────────────┐ │
│  │ Query Embedding  │ │    │  │ Tool Selection         │ │
│  └──────────────────┘ │    │  └────────────────────────┘ │
│           │            │    │            │                 │
│           ▼            │    │            ▼                 │
│  ┌──────────────────┐ │    │  ┌────────────────────────┐ │
│  │ Azure AI Search  │ │    │  │ FastAPI MCP Server     │ │
│  │ Vector Retrieval │ │    │  │ src/server/            │ │
│  └──────────────────┘ │    │  └────────────────────────┘ │
│           │            │    │            │                 │
│           ▼            │    │            ▼                 │
│  ┌──────────────────┐ │    │  ┌────────────────────────┐ │
│  │ Context Builder  │ │    │  │ SQL Server Database    │ │
│  └──────────────────┘ │    │  └────────────────────────┘ │
│           │            │    │            │                 │
│           ▼            │    │            ▼                 │
│  ┌──────────────────┐ │    │  ┌────────────────────────┐ │
│  │ Azure OpenAI LLM │ │    │  │ Response Formatter     │ │
│  └──────────────────┘ │    │  └────────────────────────┘ │
└────────────────────────┘    └──────────────────────────────┘
```

## Component Details

### 1. Web UI Layer
**File:** `src/ui/app-ui1.py`
- Built with Streamlit
- Provides interactive chat interface
- Handles PDF uploads
- Manages conversation history
- Displays sources and debug information

### 2. Orchestration Layer
**File:** `src/orchestration.py`
- Uses CrewAI for intelligent routing
- Analyzes query intent
- Routes to RAG or MCP pipeline
- Handles explicit overrides
- Manages timeouts and error handling

### 3. RAG Pipeline
**File:** `src/adapters/rag_chat.py`

**Flow:**
1. **Query Embedding**: Converts user query to vector
2. **Vector Search**: Searches Azure AI Search index
3. **Context Retrieval**: Fetches relevant document chunks
4. **Context Building**: Formats chunks for LLM
5. **LLM Generation**: Azure OpenAI generates answer
6. **Source Attribution**: Returns answer with sources

**Best For:**
- Information retrieval
- Document question answering
- Summarization
- Comparison tasks

### 4. MCP Pipeline
**Files:** 
- `src/clients/mcp_client.py` (client)
- `src/server/mcp_server.py` (server)

**Flow:**
1. **Tool Selection**: Identifies required API endpoint
2. **API Call**: Executes FastAPI request
3. **Database Query**: SQL Server retrieval
4. **Response Processing**: Formats data
5. **LLM Integration**: Natural language response

**Best For:**
- CRUD operations
- Database queries
- Structured data retrieval
- Action execution

## Data Flow

### RAG Query Example
```
User: "What is the HIV treatment guideline?"
  │
  ▼
Orchestrator → Analyzes → Routes to RAG
  │
  ▼
RAG Pipeline:
  1. Embed: "HIV treatment guideline" → [vector]
  2. Search: Azure AI Search → finds relevant chunks
  3. Build: Combines chunks into context
  4. Generate: Azure OpenAI → "According to the guideline..."
  5. Return: Answer + Sources
```

### MCP Query Example
```
User: "Get patient with ID 5"
  │
  ▼
Orchestrator → Analyzes → Routes to MCP
  │
  ▼
MCP Pipeline:
  1. Tool: "get_patient_by_id"
  2. API: GET /patient/5
  3. SQL: SELECT * FROM patients WHERE id = 5
  4. Format: JSON → Natural language
  5. Return: "Patient John Doe, age 45..."
```

## Technology Stack

### Backend
- **Python 3.8+**: Core language
- **FastAPI**: REST API framework
- **SQLAlchemy**: ORM for database
- **pyodbc**: SQL Server connector

### AI/ML
- **Azure OpenAI**: LLM and embeddings
- **Azure AI Search**: Vector search
- **CrewAI**: Agent orchestration
- **LangChain**: OpenAI integration

### Frontend
- **Streamlit**: Web UI framework
- **Requests**: HTTP client

### Data
- **pandas**: Excel file processing
- **openpyxl**: Excel file reading
- **SQLite/SQL Server**: Database

## Database Schema

### Patients Table
```sql
CREATE TABLE patients (
    id INT PRIMARY KEY,
    name VARCHAR(255),
    age INT,
    gender VARCHAR(50),
    diagnosis VARCHAR(255),
    contact_number VARCHAR(50),
    email VARCHAR(255),
    admission_date VARCHAR(50),
    discharge_date VARCHAR(50)
)
```

### Doctors Table
```sql
CREATE TABLE doctors (
    id INT PRIMARY KEY,
    doctor_name VARCHAR(255),
    designation VARCHAR(255),
    specialization VARCHAR(255),
    title VARCHAR(255),
    description TEXT,
    patient_id INT FOREIGN KEY REFERENCES patients(id)
)
```

### Studies Table
```sql
CREATE TABLE studies (
    study_id INT PRIMARY KEY,
    patient_id INT FOREIGN KEY REFERENCES patients(id),
    doctor_id INT FOREIGN KEY REFERENCES doctors(id),
    study_type VARCHAR(255),
    study_date VARCHAR(50),
    findings TEXT
)
```

## Configuration

### Environment Variables
- **Azure OpenAI**: Endpoint, key, deployments
- **Azure AI Search**: Endpoint, index, key
- **Database**: Connection string
- **App Settings**: User ID, session ID

### Configuration Files
- `.env`: Environment variables
- `.env.example`: Template
- `requirements.txt`: Python dependencies

## Security Considerations

1. **API Keys**: Stored in .env (not in version control)
2. **Database**: Use parameterized queries (SQLAlchemy)
3. **Input Validation**: Pydantic models
4. **Error Handling**: Try-catch blocks throughout
5. **HTTPS**: Use in production

## Scalability

### Current Design
- Single instance
- Local SQL Server
- Synchronous processing

### Future Enhancements
- **Load Balancing**: Multiple UI instances
- **Async Processing**: Queue-based task handling
- **Database Clustering**: Distributed SQL Server
- **Caching**: Redis for frequent queries
- **CDN**: Static assets delivery

## Monitoring and Logging

### Current Logging
- Console output
- Debug info in UI
- Latency tracking

### Recommended Additions
- **Application Insights**: Azure monitoring
- **Structured Logging**: JSON logs
- **Metrics**: Query performance, error rates
- **Alerts**: Service health checks

## Testing Strategy

### Unit Tests
- Individual components
- Mock external services
- Test utilities

### Integration Tests
- End-to-end flows
- Database operations
- API endpoints

### Performance Tests
- Load testing
- Latency benchmarks
- Concurrency tests
