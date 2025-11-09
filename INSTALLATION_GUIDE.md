# Installation Guide

## Quick Install

```powershell
pip install -r requirements.txt
```

## Step-by-Step Installation

### 1. Core Dependencies (Required)

```powershell
pip install mcp>=1.0.0 canvasapi>=2.0.0 python-dotenv>=1.0.0
```

### 2. Backend Dependencies (Required for API)

```powershell
pip install fastapi>=0.104.0 uvicorn[standard]>=0.24.0 httpx>=0.25.0 pydantic>=2.0.0
```

### 3. Frontend Dependencies (Required for UI)

```powershell
pip install streamlit>=1.28.0 streamlit-option-menu>=0.3.6 requests>=2.31.0
```

### 4. Google APIs (Optional - for Calendar/Gmail features)

```powershell
pip install google-api-python-client>=2.0.0 google-auth-httplib2>=0.1.0 google-auth-oauthlib>=1.0.0
```

### 5. Authentication (Optional - for Supabase auth)

```powershell
pip install supabase>=2.0.0
```

## Minimal Installation

If you only want core Canvas functionality without Calendar/Gmail/Auth:

```powershell
# Minimal backend + frontend
pip install mcp canvasapi python-dotenv fastapi uvicorn[standard] httpx pydantic streamlit requests
```

## Installation Issues

### Issue: "Could not find a version that satisfies the requirement"

**Solution:** Update pip first
```powershell
python -m pip install --upgrade pip
```

### Issue: "uvicorn[standard] failed to install"

**Solution:** Install without extras, then add manually
```powershell
pip install uvicorn
pip install uvloop httptools websockets
```

### Issue: "mcp not found"

**Solution:** Install from source if package not available
```powershell
pip install git+https://github.com/modelcontextprotocol/python-sdk.git
```

### Issue: Supabase import error (optional)

If you don't need authentication features, you can skip supabase:
- Comment out the import in `backend/services/auth_service.py`
- Or install it: `pip install supabase`

## Verify Installation

```powershell
# Test imports
python -c "import fastapi; import streamlit; import canvasapi; print('✓ All core packages installed')"

# Test backend modules
python -c "from backend.services.mcp_service import MCPService; print('✓ Backend imports work')"

# Test MCP servers
python -c "from backend.mcp_servers.canvas_server import fetch_courses; print('✓ MCP servers work')"
```

## Virtual Environment (Recommended)

### Create virtual environment:
```powershell
python -m venv venv
```

### Activate:
```powershell
# PowerShell
.\venv\Scripts\Activate.ps1

# CMD
.\venv\Scripts\activate.bat
```

### Install in virtual environment:
```powershell
pip install -r requirements.txt
```

## Package Versions

### Tested Versions:
- Python: 3.9, 3.10, 3.11, 3.12
- FastAPI: 0.104.0+
- Streamlit: 1.28.0+
- Canvas API: 2.0.0+

### Minimum Python Version:
- **Python 3.9+** (required for `zoneinfo` module)

## Production Installation

For production, install with specific versions:

```powershell
pip install -r requirements.txt --no-cache-dir
```

## Development Installation

For development with testing tools:

```powershell
pip install -r requirements.txt
pip install pytest pytest-asyncio flake8 black mypy
```

## Troubleshooting

### Windows-Specific Issues

**Issue:** PowerShell execution policy error

**Solution:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Mac/Linux-Specific Issues

Use `pip3` and `python3` instead of `pip` and `python`:
```bash
pip3 install -r requirements.txt
```

## Next Steps

After successful installation:
1. ✅ Set up environment variables (see `LOCAL_SETUP_GUIDE.md`)
2. ✅ Configure Canvas API key
3. ✅ Run backend: `python -m backend.main`
4. ✅ Run frontend: `streamlit run frontend/app.py`

## Optional Features

| Feature | Required Package | Install Command |
|---------|-----------------|-----------------|
| Google Calendar | `google-api-python-client` | `pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib` |
| Gmail | `google-api-python-client` | Same as Calendar |
| Authentication | `supabase` | `pip install supabase` |
| Development Tools | `pytest`, `flake8` | `pip install pytest flake8` |

## Dependency Tree

```
Canvas MPC
├── Core Framework
│   ├── mcp (MCP server protocol)
│   ├── canvasapi (Canvas LMS API)
│   └── python-dotenv (environment config)
├── Backend
│   ├── fastapi (API framework)
│   ├── uvicorn (ASGI server)
│   ├── httpx (async HTTP client)
│   └── pydantic (data validation)
├── Frontend
│   ├── streamlit (web framework)
│   ├── streamlit-option-menu (UI component)
│   └── requests (HTTP client)
└── Optional
    ├── google-api-python-client (Calendar/Gmail)
    └── supabase (authentication)
```

## Success!

If you see no errors, you're ready to run the application:

```powershell
# Terminal 1
python -m backend.main

# Terminal 2
streamlit run frontend/app.py
```

