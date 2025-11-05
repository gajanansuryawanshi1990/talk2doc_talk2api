# Talk2Doc & Talk2API Launcher
# Easy menu-driven startup script

$ErrorActionPreference = "Stop"

function Show-Menu {
    Clear-Host
    Write-Host "================================" -ForegroundColor Cyan
    Write-Host " Talk2Doc & Talk2API Launcher" -ForegroundColor Cyan
    Write-Host "================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "1. Start MCP Server (Database API)" -ForegroundColor Green
    Write-Host "2. Start Upload Server (PDF Upload)" -ForegroundColor Green
    Write-Host "3. Start Web UI (Streamlit)" -ForegroundColor Green
    Write-Host "4. Install Dependencies" -ForegroundColor Yellow
    Write-Host "5. Start All Servers" -ForegroundColor Magenta
    Write-Host "6. Exit" -ForegroundColor Red
    Write-Host ""
}

function Start-MCPServer {
    Write-Host ""
    Write-Host "Starting MCP Server on port 8001..." -ForegroundColor Cyan
    python src\server\mcp_server.py
}

function Start-UploadServer {
    Write-Host ""
    Write-Host "Starting Upload Server on port 8080..." -ForegroundColor Cyan
    uvicorn src.server.main:app --reload --host 127.0.0.1 --port 8080
}

function Start-WebUI {
    Write-Host ""
    Write-Host "Starting Web UI on port 8501..." -ForegroundColor Cyan
    streamlit run src\ui\app-ui1.py
}

function Install-Dependencies {
    Write-Host ""
    Write-Host "Installing dependencies..." -ForegroundColor Yellow
    
    if (Test-Path "venv\Scripts\Activate.ps1") {
        Write-Host "Activating virtual environment..." -ForegroundColor Green
        & .\venv\Scripts\Activate.ps1
    }
    
    pip install -r requirements.txt
    Write-Host ""
    Write-Host "Dependencies installed successfully!" -ForegroundColor Green
    Write-Host ""
    Read-Host "Press Enter to continue"
}

function Start-AllServers {
    Write-Host ""
    Write-Host "Starting all servers..." -ForegroundColor Magenta
    Write-Host "This will open 3 new terminal windows." -ForegroundColor Yellow
    Write-Host ""
    
    $currentPath = $PWD.Path
    
    # Start MCP Server
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$currentPath'; Write-Host 'MCP Server (Port 8001)' -ForegroundColor Cyan; python src\server\mcp_server.py"
    
    Start-Sleep -Seconds 2
    
    # Start Upload Server
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$currentPath'; Write-Host 'Upload Server (Port 8080)' -ForegroundColor Green; uvicorn src.server.main:app --reload --host 127.0.0.1 --port 8080"
    
    Start-Sleep -Seconds 2
    
    # Start Web UI
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$currentPath'; Write-Host 'Web UI (Port 8501)' -ForegroundColor Magenta; streamlit run src\ui\app-ui1.py"
    
    Write-Host ""
    Write-Host "All servers started!" -ForegroundColor Green
    Write-Host "Web UI will open at: http://localhost:8501" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Close the terminal windows to stop the servers." -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter to return to menu"
}

# Main loop
do {
    Show-Menu
    $choice = Read-Host "Enter your choice (1-6)"
    
    switch ($choice) {
        "1" { Start-MCPServer }
        "2" { Start-UploadServer }
        "3" { Start-WebUI }
        "4" { Install-Dependencies }
        "5" { Start-AllServers }
        "6" { 
            Write-Host ""
            Write-Host "Goodbye!" -ForegroundColor Cyan
            exit 
        }
        default { 
            Write-Host ""
            Write-Host "Invalid choice. Please select 1-6." -ForegroundColor Red
            Start-Sleep -Seconds 2
        }
    }
} while ($choice -ne "6")