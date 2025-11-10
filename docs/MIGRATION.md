# Migration Guide

## File Location Changes

This guide helps you update any existing scripts, imports, or references after the project reorganization.

## File Moves

### Python Source Files

| Old Location | New Location |
|-------------|--------------|
| `orchestration.py` | `src/orchestration.py` |
| `rag_chat.py` | `src/adapters/rag_chat.py` |
| `mcp_client.py` | `src/clients/mcp_client.py` |
| `mcp_chatbot.py` | `src/clients/mcp_chatbot.py` |
| `mcp_server.py` | `src/server/mcp_server.py` |
| `app-ui1.py` | `src/ui/app-ui1.py` |

### Data Files

| Old Location | New Location |
|-------------|--------------|
| `doctors.xlsx` | `data/excel/doctors.xlsx` |
| `patients.xlsx` | `data/excel/patients.xlsx` |
| `studies.xlsx` | `data/excel/studies.xlsx` |
| `Guideline for HIV.pdf` | `data/pdfs/Guideline for HIV.pdf` |
| `Guideline for mental health at work.pdf` | `data/pdfs/Guideline for mental health at work.pdf` |
| `Guidelines for Malaria.pdf` | `data/pdfs/Guidelines for Malaria.pdf` |
| `Guidelines for pharma company.pdf` | `data/pdfs/Guidelines for pharma company.pdf` |
| `Guidelines for Right to health in India.pdf` | `data/pdfs/Guidelines for Right to health in India.pdf` |

## Import Statement Changes

### Updated Imports

**In `src/ui/app-ui1.py`:**
```python
# OLD:
from orchestration import Orchestrator, OrchestratorConfig, _rag_adapter_impl, _mcp_adapter_impl

# NEW:
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from src.orchestration import Orchestrator, OrchestratorConfig, _rag_adapter_impl, _mcp_adapter_impl
```

**In `src/clients/mcp_chatbot.py`:**
```python
# OLD:
from mcp_client import TOOLS_SPEC, call_fastapi_tool

# NEW:
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from src.clients.mcp_client import TOOLS_SPEC, call_fastapi_tool
```

**In `src/orchestration.py`:**
```python
# OLD (RAG adapter):
from rag_chat import retrieve_context, build_context_text, ask_llm

# NEW:
from src.adapters.rag_chat import retrieve_context, build_context_text, ask_llm

# OLD (MCP adapter):
from mcp_client import TOOLS_SPEC, call_fastapi_tool

# NEW:
from src.clients.mcp_client import TOOLS_SPEC, call_fastapi_tool
```

## Command Updates

### Running Scripts

**OLD Commands:**
```powershell
# MCP Server
python mcp_server.py

# Web UI
streamlit run app-ui1.py

# Chatbot
python mcp_chatbot.py
```

**NEW Commands:**
```powershell
# MCP Server
python src\server\mcp_server.py

# Web UI
streamlit run src\ui\app-ui1.py

# Chatbot
python src\clients\mcp_chatbot.py
```

## Custom Scripts Update

If you have any custom scripts that import these modules, update them as follows:

### Example 1: Custom Test Script

**OLD:**
```python
# test_rag.py (root directory)
from rag_chat import retrieve_context

query = "test query"
results = retrieve_context(query)
print(results)
```

**NEW:**
```python
# test_rag.py (root directory)
from src.adapters.rag_chat import retrieve_context

query = "test query"
results = retrieve_context(query)
print(results)
```

### Example 2: Custom Integration Script

**OLD:**
```python
# integration.py
from orchestration import Orchestrator
from mcp_client import TOOLS_SPEC

orchestrator = Orchestrator(...)
```

**NEW:**
```python
# integration.py
from src.orchestration import Orchestrator
from src.clients.mcp_client import TOOLS_SPEC

orchestrator = Orchestrator(...)
```

## Path References Update

### Excel File References

If you have scripts that load Excel files:

**OLD:**
```python
import pandas as pd
df = pd.read_excel("patients.xlsx")
```

**NEW:**
```python
import pandas as pd
df = pd.read_excel("data/excel/patients.xlsx")
```

### PDF File References

**OLD:**
```python
pdf_path = "Guideline for HIV.pdf"
```

**NEW:**
```python
pdf_path = "data/pdfs/Guideline for HIV.pdf"
```

## Environment Setup

### Virtual Environment

No changes needed, but if you want a fresh start:

```powershell
# Deactivate current environment
deactivate

# Remove old environment
Remove-Item -Recurse -Force venv

# Create new environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

## Verification Steps

After migration, verify everything works:

### 1. Test Imports
```powershell
python -c "from src.orchestration import Orchestrator; print('✓ Orchestrator')"
python -c "from src.adapters.rag_chat import retrieve_context; print('✓ RAG Chat')"
python -c "from src.clients.mcp_client import TOOLS_SPEC; print('✓ MCP Client')"
python -c "from src.server.mcp_server import app; print('✓ MCP Server')"
```

### 2. Test Services
```powershell
# Terminal 1: Start MCP Server
python src\server\mcp_server.py

# Terminal 2: Test API
Invoke-WebRequest http://127.0.0.1:8001/patients
```

### 3. Test Web UI
```powershell
streamlit run src\ui\app-ui1.py
# Open browser to http://localhost:8501
```

## Common Issues and Solutions

### Issue 1: Import Errors
**Error:** `ModuleNotFoundError: No module named 'orchestration'`

**Solution:** Update import to `from src.orchestration import ...`

### Issue 2: File Not Found
**Error:** `FileNotFoundError: [Errno 2] No such file or directory: 'patients.xlsx'`

**Solution:** Update path to `data/excel/patients.xlsx`

### Issue 3: Running from Wrong Directory
**Error:** Various import errors

**Solution:** Always run from project root:
```powershell
cd "c:\Users\36385\Desktop\Talk2doc&Talk2API"
python src\ui\app-ui1.py
```

### Issue 4: Sys.path Issues
**Error:** `ModuleNotFoundError: No module named 'src'`

**Solution:** Ensure sys.path is configured correctly:
```python
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
```

## Rollback Instructions

If you need to revert to the old structure:

```powershell
# Move files back to root
Move-Item src\orchestration.py orchestration.py
Move-Item src\adapters\rag_chat.py rag_chat.py
Move-Item src\clients\mcp_client.py mcp_client.py
Move-Item src\clients\mcp_chatbot.py mcp_chatbot.py
Move-Item src\server\mcp_server.py mcp_server.py
Move-Item src\ui\app-ui1.py app-ui1.py

# Move data files back
Move-Item data\excel\*.xlsx .
Move-Item data\pdfs\*.pdf .

# Remove new directories
Remove-Item -Recurse src
Remove-Item -Recurse data
Remove-Item -Recurse docs
Remove-Item -Recurse config
```

## Next Steps

1. ✅ Files have been reorganized
2. ✅ Imports have been updated
3. ✅ Documentation created
4. 🔄 Test all functionality
5. 🔄 Update any custom scripts
6. 🔄 Commit to version control (if using Git)

## Benefits of New Structure

- **✓ Better Organization:** Clear separation of concerns
- **✓ Easier Navigation:** Logical folder hierarchy
- **✓ Scalability:** Easy to add new components
- **✓ Professional:** Follows Python project best practices
- **✓ Maintainable:** Easier to locate and update code
- **✓ Testable:** Better structure for unit tests
