# Local Setup Guide - Canvas MPC

## Prerequisites

- Python 3.9 or higher
- pip (Python package installer)
- Canvas API key
- (Optional) Google Calendar API credentials
- (Optional) Gmail API credentials

## Step 1: Install Dependencies

```powershell
# Install all dependencies
pip install -r requirements.txt
```

## Step 2: Set Up Environment Variables

### Option A: Create a `.env` file (Recommended)

Create a `.env` file in the project root:

```bash
# Canvas Configuration
CANVAS_API_KEY=your_canvas_api_key_here
CANVAS_API_URL=https://canvas.instructure.com

# OpenRouter (for AI features)
OPENROUTER_API_KEY=your_openrouter_api_key_here

# Backend Configuration
PORT=8000
ENVIRONMENT=development

# Frontend Configuration
API_URL=http://127.0.0.1:8000

# Timezone (optional)
USER_TIMEZONE=America/New_York

# Supabase (optional - for authentication)
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
```

### Option B: Use Environment-Specific Files

Copy the example files and edit them:

```powershell
# Copy example configs
Copy-Item config\.env.backend.example .env.backend
Copy-Item config\.env.frontend.example .env.frontend

# Edit the files with your actual credentials
notepad .env.backend
notepad .env.frontend
```

## Step 3: Set Up Canvas API Key

1. Log into your Canvas instance
2. Go to **Account → Settings**
3. Scroll to **Approved Integrations**
4. Click **+ New Access Token**
5. Give it a purpose (e.g., "Canvas MPC")
6. Copy the token
7. Add it to your `.env` file as `CANVAS_API_KEY`

## Step 4: (Optional) Set Up Google API Credentials

### For Calendar and Gmail Features:

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project or select existing
3. Enable **Google Calendar API** and **Gmail API**
4. Create OAuth 2.0 credentials
5. Download the credentials JSON file
6. Save as `credentials.json` in project root

### Authenticate:

```powershell
# Authenticate Google Calendar
python backend\services\calendar_auth.py

# Authenticate Gmail
python backend\services\gmail_auth.py
```

This will create token files in `data/tokens/`

## Step 5: Run the Backend

### Method 1: Using Python Module (Recommended for Development)

```powershell
# From project root
python -m backend.main
```

### Method 2: Using Uvicorn Directly

```powershell
# Basic
uvicorn backend.main:app --reload

# With specific host and port
uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload

# For production
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --workers 4
```

**Expected Output:**
```
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

## Step 6: Run the Frontend

Open a **new terminal** and run:

```powershell
# From project root
streamlit run frontend/app.py
```

**Expected Output:**
```
  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://192.168.x.x:8501
```

## Step 7: Access the Application

1. **Backend API**: http://127.0.0.1:8000
   - Health Check: http://127.0.0.1:8000/health
   - API Docs: http://127.0.0.1:8000/docs

2. **Frontend**: http://localhost:8501

## Common Issues & Solutions

### Issue 1: "ModuleNotFoundError: No module named 'X'"

**Solution:**
```powershell
pip install -r requirements.txt
```

### Issue 2: "ImportError: cannot import name..."

**Solution:** Make sure you're in the project root directory when running commands.

### Issue 3: Backend can't connect to Canvas

**Solution:**
- Verify your `CANVAS_API_KEY` is correct
- Check that `CANVAS_API_URL` points to your Canvas instance
- Test your API key manually:
  ```powershell
  python -c "from backend.mcp_servers.canvas_server import get_canvas_client; print(get_canvas_client())"
  ```

### Issue 4: Frontend can't connect to Backend

**Solution:**
- Make sure backend is running first
- Check that `API_URL` in frontend matches backend URL (default: http://127.0.0.1:8000)
- Verify CORS settings allow frontend access

### Issue 5: "supabase module not found" (Optional Feature)

If you don't need authentication, you can skip Supabase:

**Option 1:** Install supabase
```powershell
pip install supabase
```

**Option 2:** Comment out auth features in `backend/api/routes.py`

### Issue 6: Token files not found

**Solution:**
```powershell
# Create token directories
New-Item -ItemType Directory -Force -Path "data\tokens"
New-Item -ItemType File -Force -Path "data\tokens\.gitkeep"
```

## Development Workflow

### Terminal 1: Backend
```powershell
# Run with auto-reload for development
uvicorn backend.main:app --reload --port 8000
```

### Terminal 2: Frontend
```powershell
# Streamlit auto-reloads on file changes
streamlit run frontend/app.py
```

### Terminal 3: Testing/Commands
```powershell
# Test imports
python -c "from backend.services.mcp_service import MCPService; print('✓ OK')"

# Run tests
pytest tests/

# Check linting
flake8 backend/ frontend/
```

## Quick Start Commands

```powershell
# Full startup (run each in separate terminal)
# Terminal 1 - Backend
python -m backend.main

# Terminal 2 - Frontend  
streamlit run frontend/app.py

# Terminal 3 - Open in browser
start http://localhost:8501
```

## Production Deployment

For production deployment, see:
- `docs/deployment/DEPLOYMENT_GUIDE.md`
- `docs/deployment/RENDER_DEPLOYMENT.md`
- `render.yaml` configuration

## Testing the Setup

### 1. Test Backend Health
```powershell
curl http://127.0.0.1:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "Canvas MPC API",
  "version": "1.0.0"
}
```

### 2. Test Canvas Connection
```powershell
curl http://127.0.0.1:8000/tools
```

Should return list of available tools.

### 3. Test Frontend
1. Open http://localhost:8501
2. Check if backend status shows "Connected" (green dot)
3. Try sending a message: "List my Canvas courses"

## Directory Structure After Setup

```
CanvasMPC/
├── .env                          # Your environment variables
├── credentials.json              # Google API credentials (optional)
├── data/
│   ├── tokens/
│   │   ├── gmail_token.json     # Created after Gmail auth
│   │   └── calendar_token.json  # Created after Calendar auth
│   └── flashcards/
│       ├── flashcards.json      # Auto-created on first use
│       └── progress.json        # Auto-created on first use
├── backend/                      # Backend is running
├── frontend/                     # Frontend is running
└── ...
```

## Next Steps

1. ✅ **Verify Installation**: Run health checks above
2. 📚 **Read Documentation**: Check `docs/` for detailed guides
3. 🧪 **Test Features**: Try creating flashcards, viewing courses
4. 🔧 **Customize**: Modify settings, add custom tools
5. 🚀 **Deploy**: Follow deployment guides when ready

## Getting Help

- **Documentation**: Check `docs/` directory
- **Logs**: Backend logs appear in terminal
- **API Docs**: http://127.0.0.1:8000/docs (when backend is running)
- **Issues**: Check for import errors or missing dependencies

## Quick Reference

| Service | Command | URL |
|---------|---------|-----|
| Backend | `python -m backend.main` | http://127.0.0.1:8000 |
| Frontend | `streamlit run frontend/app.py` | http://localhost:8501 |
| API Docs | (backend running) | http://127.0.0.1:8000/docs |
| Health Check | (backend running) | http://127.0.0.1:8000/health |

---

**Ready to start!** Run the backend and frontend in separate terminals, then access the app at http://localhost:8501

