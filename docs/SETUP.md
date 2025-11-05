# Setup Guide

## Quick Start

### 1. Clone and Navigate
```bash
cd "c:\Users\36385\Desktop\Talk2doc&Talk2API"
```

### 2. Create Virtual Environment
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 4. Configure Environment
```powershell
# Copy the example environment file
Copy-Item .env.example .env

# Edit .env with your actual credentials
notepad .env
```

### 5. Start the Services

#### Option A: Run All Services

**Terminal 1 - MCP Server:**
```powershell
python src\server\mcp_server.py
```

**Terminal 2 - Web UI:**
```powershell
streamlit run src\ui\app-ui1.py
```

#### Option B: Run Chatbot Only

**Terminal 1 - MCP Server:**
```powershell
python src\server\mcp_server.py
```

**Terminal 2 - Chatbot:**
```powershell
python src\clients\mcp_chatbot.py
```

## Configuration Details

### Azure OpenAI Setup
1. Create Azure OpenAI resource
2. Deploy chat model (e.g., gpt-4, gpt-35-turbo)
3. Deploy embedding model (e.g., text-embedding-ada-002)
4. Copy endpoint and key to .env

### Azure AI Search Setup
1. Create Azure AI Search service
2. Create an index for your documents
3. Copy endpoint, index name, and admin key to .env

### SQL Server Setup
1. Ensure SQL Server is running
2. Update connection string in `src/server/mcp_server.py`:
   ```python
   server = 'YOUR_SERVER\\INSTANCE'
   database = 'YOUR_DATABASE'
   username = 'YOUR_USERNAME'
   password = 'YOUR_PASSWORD'
   ```

## Verification

### Test MCP Server
```powershell
# In browser or PowerShell
Invoke-WebRequest http://127.0.0.1:8001/patients
```

### Test Web UI
```
Open browser: http://localhost:8501
```

## Troubleshooting

### Import Errors
If you see import errors, ensure you're running from the project root:
```powershell
cd "c:\Users\36385\Desktop\Talk2doc&Talk2API"
python src\ui\app-ui1.py
```

### Database Connection Errors
- Verify SQL Server is running
- Check Windows Authentication or SQL Server Authentication
- Ensure ODBC Driver 17 is installed

### Azure Service Errors
- Verify all endpoints start with https://
- Check API keys are valid
- Ensure deployments are active

## Data Loading

### Load Excel Data
The Excel files in `data/excel/` contain patient, doctor, and study information.
You can load this data into SQL Server using a separate script or SQL Server Import/Export Wizard.

### Upload PDFs
Use the web UI to upload PDFs to the RAG system:
1. Start the web UI
2. Use the sidebar file uploader
3. Click "Upload and Trigger Indexer"

## Development

### Project Structure
```
src/
├── adapters/       # RAG and data processing
├── clients/        # MCP client and chatbot
├── server/         # FastAPI server
├── ui/             # Streamlit interface
└── orchestration.py # CrewAI routing
```

### Adding New Features
1. **New MCP endpoint**: Edit `src/server/mcp_server.py`
2. **New tool**: Update `src/clients/mcp_client.py`
3. **UI changes**: Edit `src/ui/app-ui1.py`
4. **RAG improvements**: Modify `src/adapters/rag_chat.py`

## Running Tests
```powershell
# TODO: Add test suite
pytest tests/
```

## Production Deployment

### Using Azure App Service
1. Deploy FastAPI server to Azure App Service
2. Deploy Streamlit to Azure Container Apps
3. Update endpoints in .env

### Using Docker
```powershell
# TODO: Add Dockerfile
docker build -t talk2doc .
docker run -p 8501:8501 talk2doc
```

## Support

For issues or questions, please check:
- README.md for detailed documentation
- Azure OpenAI documentation
- Azure AI Search documentation
- CrewAI documentation
