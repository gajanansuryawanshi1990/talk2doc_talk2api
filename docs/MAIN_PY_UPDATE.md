# Additional File - main.py Update

## ✅ File Successfully Moved

**File:** `main.py`  
**Old Location:** Root directory  
**New Location:** `src/server/main.py`

## 📄 What is main.py?

This is a **FastAPI server** that handles document management and Azure AI Search integration:

### Features:
- **PDF Upload** - Upload PDFs to Azure Blob Storage
- **Indexer Triggering** - Automatically triggers Azure AI Search indexer after upload
- **File Deletion** - Delete specific PDFs (with protection for critical files)
- **Bulk Cleanup** - Clean up temporary PDFs while preserving protected documents
- **Protected Files List** - Maintains a list of files that cannot be deleted (e.g., `A77_ACONF14-en.pdf`)

### Endpoints:
- `POST /upload/` - Upload a PDF file
- `DELETE /delete-file/{filename}` - Delete a specific file
- `DELETE /cleanup-temporary-pdfs` - Clean up all temporary PDFs
- `POST /trigger-indexer` - Manually trigger the indexer
- `GET /` - Server status

## 🚀 How to Run

```powershell
uvicorn src.server.main:app --reload --host 127.0.0.1 --port 8080
```

Or use the launcher:
```powershell
.\launch.ps1
# Choose option 2: Start Upload Server
```

Or to run all servers at once:
```powershell
.\launch.ps1
# Choose option 5: Start All Servers
```

## 🔧 Configuration Required

Add these to your `.env` file:

```env
# Azure Blob Storage
AZURE_CONNECTION_STRING=<your-storage-connection-string>
CONTAINER_NAME=<your-container-name>

# Azure AI Search (for indexer)
AZURE_SEARCH_ENDPOINT=https://<your-search-service>.search.windows.net
AZURE_SEARCH_API_KEY=<your-search-admin-key>
AZURE_SEARCH_INDEXER_NAME=talk2doc-indexer
```

## 📊 Server Ports

Now you have **two FastAPI servers**:

| Server | Port | Purpose | Command |
|--------|------|---------|---------|
| **MCP Server** | 8001 | Patient/Doctor database operations | `python src\server\mcp_server.py` |
| **Upload Server** | 8080 | PDF upload and indexing | `uvicorn src.server.main:app --reload --host 127.0.0.1 --port 8080` |

## 🔄 Updated Workflow

### Full Application Startup:

1. **Terminal 1 - MCP Server:**
   ```powershell
   python src\server\mcp_server.py
   ```
   Running on: http://127.0.0.1:8001

2. **Terminal 2 - Upload Server:**
   ```powershell
   uvicorn src.server.main:app --reload --host 127.0.0.1 --port 8080
   ```
   Running on: http://127.0.0.1:8080

3. **Terminal 3 - Web UI:**
   ```powershell
   streamlit run src\ui\app-ui1.py
   ```
   Running on: http://localhost:8501

### Or Use the Launcher (Easiest!):
```powershell
.\launch.ps1
# Choose option 5: Start All Servers
```

## 📝 Usage Examples

### Upload a PDF:
```powershell
# Using PowerShell
$file = "data\pdfs\Guideline for HIV.pdf"
Invoke-WebRequest -Uri "http://127.0.0.1:8080/upload/" -Method POST -InFile $file
```

### Delete a temporary PDF:
```powershell
Invoke-WebRequest -Uri "http://127.0.0.1:8080/delete-file/mytemp.pdf" -Method DELETE
```

### Clean up all temporary PDFs:
```powershell
Invoke-WebRequest -Uri "http://127.0.0.1:8080/cleanup-temporary-pdfs" -Method DELETE
```

### Trigger indexer manually:
```powershell
Invoke-WebRequest -Uri "http://127.0.0.1:8080/trigger-indexer" -Method POST
```

## 🛡️ Protected Files

The server maintains a list of protected PDFs that cannot be deleted:
- `A77_ACONF14-en.pdf`

You can modify this list in `src/server/main.py` by editing the `FIXED_PDF_NAMES` variable.

## 📚 Integration with Web UI

The Streamlit web UI (`src/ui/app-ui1.py`) already has a PDF upload feature in the sidebar that calls this upload server at `http://127.0.0.1:8080/upload/`.

## ✅ Updated Documentation

All documentation has been updated to include the upload server:
- ✅ `README.md` - Added upload server information
- ✅ `docs/COMMANDS.md` - Added upload server commands
- ✅ `docs/PROJECT_MAP.md` - Added to project structure
- ✅ `.env.example` - Added required environment variables
- ✅ `launch.ps1` - Added upload server options

## 🎯 Complete Server List

Your project now has **3 servers**:

1. **MCP Server** (`src/server/mcp_server.py`) - Port 8001
   - Database operations (patients, doctors, studies)
   
2. **Upload Server** (`src/server/main.py`) - Port 8080
   - PDF upload and management
   - Azure AI Search indexing
   
3. **Web UI** (`src/ui/app-ui1.py`) - Port 8501
   - User interface
   - Chat functionality
   - Orchestration between RAG and MCP

## 🎉 All Set!

Your `main.py` file has been successfully integrated into the organized project structure. The project is now complete with all servers properly organized!
