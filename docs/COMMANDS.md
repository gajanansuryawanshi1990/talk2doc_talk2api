# Quick Reference Guide

## Common Commands

### Starting Services

#### MCP Server (Port 8001)
```powershell
python src\server\mcp_server.py
```

#### Upload Server (Port 8080)
```powershell
uvicorn src.server.main:app --reload --host 127.0.0.1 --port 8080
```

#### Web UI (Port 8501)
```powershell
streamlit run src\ui\app-ui1.py
```

#### Chatbot (Terminal)
```powershell
python src\clients\mcp_chatbot.py
```

## Example Queries

### RAG Queries (Document Search)
- "What is the guideline for treating HIV?"
- "Explain the mental health at work policy"
- "Summarize the malaria treatment guidelines"
- "Compare HIV and Malaria treatment approaches"
- "What are the steps for pharmaceutical compliance?"

### MCP Queries (Database Operations)
- "Get patient with ID 1"
- "List all doctors"
- "Show me all patients"
- "Find doctors for patient ID 3"
- "Get studies for doctor ID 2"
- "Show me patient 5's medical studies"

### Forced Routing
- "force:rag What is the HIV guideline?"
- "force:mcp List all patients"

## API Endpoints

### Upload Server (http://127.0.0.1:8080)
```
POST   http://127.0.0.1:8080/upload/
DELETE http://127.0.0.1:8080/delete-file/{filename}
DELETE http://127.0.0.1:8080/cleanup-temporary-pdfs
POST   http://127.0.0.1:8080/trigger-indexer
GET    http://127.0.0.1:8080/
```

### Patients
```
GET  http://127.0.0.1:8001/patients
GET  http://127.0.0.1:8001/patient/{id}
GET  http://127.0.0.1:8001/patient/{id}/doctors
GET  http://127.0.0.1:8001/patient/{id}/studies
```

### Doctors
```
GET  http://127.0.0.1:8001/doctors
GET  http://127.0.0.1:8001/doctor/{id}
GET  http://127.0.0.1:8001/doctor/{id}/studies
```

### Studies
```
GET  http://127.0.0.1:8001/studies
GET  http://127.0.0.1:8001/study/{id}
```

## File Locations

### Source Code
- Orchestration: `src/orchestration.py`
- RAG Adapter: `src/adapters/rag_chat.py`
- MCP Client: `src/clients/mcp_client.py`
- MCP Server: `src/server/mcp_server.py`
- Web UI: `src/ui/app-ui1.py`
- Chatbot: `src/clients/mcp_chatbot.py`

### Data Files
- Excel files: `data/excel/`
- PDF documents: `data/pdfs/`

### Configuration
- Environment: `.env`
- Requirements: `requirements.txt`

## Troubleshooting

### Reset Virtual Environment
```powershell
deactivate
Remove-Item -Recurse -Force venv
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Check Service Status
```powershell
# Test MCP Server
Invoke-WebRequest http://127.0.0.1:8001/

# Check Streamlit
# Open browser to http://localhost:8501
```

### View Logs
- Streamlit logs: Terminal output
- Server logs: Terminal output
- Check console for errors

## Development Tips

### Testing Imports
```powershell
python -c "from src.orchestration import Orchestrator; print('OK')"
python -c "from src.adapters.rag_chat import retrieve_context; print('OK')"
python -c "from src.clients.mcp_client import TOOLS_SPEC; print('OK')"
```

### Running Individual Components
```powershell
# Test RAG only
python -c "from src.adapters.rag_chat import retrieve_context; print(retrieve_context('test query'))"

# Test orchestration
python -c "from src.orchestration import Orchestrator, OrchestratorConfig; print('Orchestrator loaded')"
```

## Environment Variables Quick Check
```powershell
# List all env vars
Get-Content .env

# Check specific variable
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(os.getenv('AZURE_OPENAI_ENDPOINT'))"
```

## Git Commands (if using version control)

```bash
# Initialize repository
git init

# Add all files
git add .

# Commit
git commit -m "Organized project structure"

# Add remote
git remote add origin <your-repo-url>

# Push
git push -u origin main
```
