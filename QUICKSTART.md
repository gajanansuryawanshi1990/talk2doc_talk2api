# 🚀 Quick Start Guide

**Never used this project before? Start here!**

## ⚡ Fastest Way to Start

### Option 1: Double-Click Launcher (Easiest!)

1. **Find the file:** `launch.bat` in the project folder
2. **Double-click it**
3. **Choose an option** from the menu
4. **Done!** 🎉

### Option 2: Manual Start (2 Steps)

**Step 1:** Open PowerShell in project folder
```powershell
cd "c:\Users\36385\Desktop\Talk2doc&Talk2API"
```

**Step 2:** Start the server
```powershell
python src\server\mcp_server.py
```

**Step 3:** In a NEW PowerShell window, start the UI
```powershell
cd "c:\Users\36385\Desktop\Talk2doc&Talk2API"
streamlit run src\ui\app-ui1.py
```

**Step 4:** Open browser to `http://localhost:8501`

## 🎯 What Can I Do?

### Ask About Documents (RAG)
```
"What is the HIV treatment guideline?"
"Explain mental health at work policy"
"Summarize the malaria guidelines"
```

### Query Database (MCP)
```
"Get patient with ID 1"
"List all doctors"
"Show me all patients"
"Find studies for patient 3"
```

## 🛠️ First Time Setup

### Do This Once:

1. **Install Python** (if not installed)
   - Download from: https://www.python.org/downloads/
   - Version 3.8 or higher

2. **Open PowerShell in project folder**
   - Navigate to: `C:\Users\36385\Desktop\Talk2doc&Talk2API`
   - Right-click → "Open PowerShell here"

3. **Create virtual environment** (recommended)
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

4. **Install dependencies**
   ```powershell
   pip install -r requirements.txt
   ```

5. **Configure environment variables**
   ```powershell
   # Copy the example file
   Copy-Item .env.example .env
   
   # Edit .env with your credentials
   notepad .env
   ```

6. **You're ready!** Use the launcher or manual commands above

## 📝 What You Need

### Required:
- ✅ Python 3.8+
- ✅ Azure OpenAI account
- ✅ Azure AI Search account
- ✅ SQL Server (for database features)

### Nice to Have:
- PowerShell (comes with Windows)
- Modern web browser
- Text editor (VS Code, Notepad++, etc.)

## 🎓 Learning Path

### Day 1: Get It Running
1. ✅ Install dependencies
2. ✅ Configure .env file
3. ✅ Start the server
4. ✅ Open the UI
5. ✅ Try a simple query

### Day 2: Understand the Structure
1. 📖 Read `README.md`
2. 📖 Browse `docs/PROJECT_MAP.md`
3. 🔍 Explore `src/` folder
4. 📊 Check `data/` folder

### Day 3: Customize
1. ⚙️ Modify settings
2. 🎨 Customize UI
3. 📝 Add your own documents
4. 🔧 Test new features

## 🆘 Common Issues

### "Python is not recognized"
**Fix:** Install Python from https://www.python.org/downloads/
Make sure to check "Add Python to PATH" during installation

### "No module named 'streamlit'"
**Fix:** Install dependencies
```powershell
pip install -r requirements.txt
```

### "Cannot connect to database"
**Fix:** Update SQL Server connection in `src/server/mcp_server.py`
Check that SQL Server is running

### "Import errors"
**Fix:** Make sure you're in the project root
```powershell
cd "c:\Users\36385\Desktop\Talk2doc&Talk2API"
```

### "Azure OpenAI error"
**Fix:** Check your .env file has correct:
- AZURE_OPENAI_ENDPOINT
- AZURE_OPENAI_API_KEY
- AZURE_OPENAI_CHAT_DEPLOYMENT

## 🎯 Quick Commands Cheat Sheet

```powershell
# Navigate to project
cd "c:\Users\36385\Desktop\Talk2doc&Talk2API"

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Start MCP Server
python src\server\mcp_server.py

# Start Web UI (new window)
streamlit run src\ui\app-ui1.py

# Start Chatbot
python src\clients\mcp_chatbot.py

# Install dependencies
pip install -r requirements.txt

# Run launcher menu
.\launch.ps1
```

## 📚 Where to Learn More

| Topic | File to Read |
|-------|-------------|
| Complete overview | `README.md` |
| Setup instructions | `docs/SETUP.md` |
| Commands reference | `docs/COMMANDS.md` |
| System architecture | `docs/ARCHITECTURE.md` |
| Project structure | `docs/PROJECT_MAP.md` |

## ✅ Success Checklist

After setup, you should be able to:

- [ ] Start the MCP server without errors
- [ ] Open the web UI in browser
- [ ] See the chat interface
- [ ] Upload a PDF document
- [ ] Ask a question about the document
- [ ] Query the database (e.g., "list all patients")
- [ ] See the response with sources

## 🎉 You're All Set!

Once everything is running:
1. **Open browser** → `http://localhost:8501`
2. **Type a question** in the chat box
3. **Watch the magic happen!** ✨

### Example First Questions to Try:
1. "What is in the uploaded documents?"
2. "force:mcp List all patients"
3. "force:rag Explain the HIV guidelines"

## 🚀 Ready for More?

### Explore:
- Try uploading your own PDF
- Experiment with different queries
- Check the debug information
- Browse the source code
- Customize the UI

### Next Steps:
- Read `docs/ARCHITECTURE.md` to understand how it works
- Modify `src/ui/app-ui1.py` to customize the interface
- Add new endpoints in `src/server/mcp_server.py`
- Explore `src/orchestration.py` to see the routing logic

---

**Need Help?**
- Check `docs/` folder for detailed guides
- Review error messages carefully
- Ensure all services are running
- Verify .env configuration

**Happy Exploring! 🎊**
