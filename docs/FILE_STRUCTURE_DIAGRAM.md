# Canvas MPC - Visual File Structure

This document provides a visual representation of how files should be used during deployment.

## Deployment View

```
┌─────────────────────────────────────────────────────────────────────┐
│                         GITHUB REPOSITORY                            │
│                       (Version Control)                              │
└───────────┬──────────────────┬──────────────────┬───────────────────┘
            │                  │                  │
            ▼                  ▼                  ▼
┌───────────────────┐  ┌──────────────┐  ┌──────────────────┐
│   RENDER          │  │  STREAMLIT   │  │    SUPABASE      │
│   (Backend)       │  │  CLOUD       │  │    (Database)    │
│                   │  │  (Frontend)  │  │                  │
│ Reads:            │  │              │  │ Setup Once:      │
│ • backend/        │  │ Reads:       │  │ • config/        │
│ • requirements-   │  │ • frontend/  │  │   supabase_      │
│   backend.txt     │  │ • requirements│  │   schema.sql     │
│ • render.yaml     │  │   -frontend  │  │                  │
│ • MCP servers     │  │   .txt       │  │ Stores:          │
│   (root *.py)     │  │              │  │ • User sessions  │
│ • flashcard_*     │  │ Secrets:     │  │ • User creds     │
│   (root *.py)     │  │ • API_URL    │  │                  │
│                   │  │              │  │                  │
│ Env Vars:         │  │              │  │                  │
│ • OPENROUTER_*    │  │              │  │                  │
│ • SUPABASE_*      │  │              │  │                  │
│ • FRONTEND_URL    │  │              │  │                  │
│ • CANVAS_*        │  │              │  │                  │
└───────────────────┘  └──────────────┘  └──────────────────┘
```

## Directory-Level View

```
CanvasMPC/
│
├── 📦 BACKEND (Deploy to Render)
│   ├── backend/
│   │   ├── main.py ⭐ [Entry Point]
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   └── routes.py [REST API endpoints]
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── auth_service.py [Supabase integration]
│   │   │   └── mcp_service.py [MCP coordination]
│   │   ├── mcp_servers/
│   │   │   └── __init__.py
│   │   └── utils/
│   │       └── __init__.py
│   │
│   ├── requirements-backend.txt ⭐ [Render dependencies]
│   └── render.yaml ⭐ [Render configuration]
│
├── 🎨 FRONTEND (Deploy to Streamlit Cloud)
│   ├── frontend/
│   │   ├── app.py ⭐ [Entry Point]
│   │   ├── __init__.py
│   │   ├── pages/
│   │   │   └── 1_⚙️_Settings.py [Credential management]
│   │   └── utils/
│   │       ├── __init__.py
│   │       └── api.py [Backend communication]
│   │
│   └── requirements-frontend.txt ⭐ [Streamlit dependencies]
│
├── 🗄️ DATABASE (Setup in Supabase)
│   └── config/
│       └── supabase_schema.sql ⭐ [Run once in Supabase SQL Editor]
│
├── 🔧 MCP SERVERS (Used by Backend)
│   ├── mcp_server.py [Canvas MCP]
│   ├── calendar_mcp_server.py [Google Calendar MCP]
│   ├── gmail_mcp_server.py [Gmail MCP]
│   ├── flashcard_mcp_server.py [Flashcard MCP]
│   ├── flashcard_generator.py [AI flashcard generation]
│   └── flashcard_storage.py [Flashcard data management]
│
├── 📝 DOCUMENTATION
│   └── docs/
│       ├── DEPLOYMENT_GUIDE.md [Complete deployment guide]
│       ├── PROJECT_STRUCTURE.md [File organization]
│       ├── QUICK_START.md [15-min setup]
│       └── FILE_STRUCTURE_DIAGRAM.md [This file]
│
├── ⚙️ CONFIGURATION
│   ├── env.example ⭐ [Local development template]
│   ├── env.backend.example ⭐ [Render env vars]
│   └── env.frontend.example ⭐ [Streamlit secrets]
│
├── 🛠️ SCRIPTS (Local use only - not deployed)
│   ├── scripts/
│   │   ├── authenticate_calendar.py [OAuth for Calendar]
│   │   └── authenticate_gmail.py [OAuth for Gmail]
│   │
│   └── Legacy setup files:
│       ├── authenticate_calendar.py
│       └── authenticate_gmail.py
│
├── 📦 DEPENDENCIES
│   ├── requirements-backend.txt ⭐ [Backend only]
│   ├── requirements-frontend.txt ⭐ [Frontend only]
│   └── requirements.txt [Local dev - includes both]
│
├── 💾 DATA (Git-ignored)
│   ├── flashcard_data/
│   │   ├── flashcards.json
│   │   └── progress.json
│   ├── .env
│   ├── credentials.json
│   ├── calendar_token.json
│   └── token.json
│
└── 📄 ROOT FILES
    ├── DEPLOYMENT_README.md ⭐ [Start here]
    ├── README.md [Project overview]
    ├── .gitignore
    └── Legacy docs:
        ├── CALENDAR_SETUP.md
        ├── GMAIL_SETUP.md
        ├── FRONTEND_SETUP.md
        ├── RENDER_DEPLOYMENT.md
        └── [other *.md files]

⭐ = Critical deployment files
```

## File Usage by Stage

### Stage 1: Initial Setup (Local)

```
Files Used:
├── env.example              → Copy to .env
├── requirements.txt         → pip install
├── scripts/
│   ├── authenticate_calendar.py  → Run for Google Calendar
│   └── authenticate_gmail.py     → Run for Gmail
└── Test locally before deploying
```

### Stage 2: Database Setup (Supabase)

```
Files Used:
└── config/
    └── supabase_schema.sql  → Run in Supabase SQL Editor

Actions:
1. Create Supabase project
2. Copy schema SQL
3. Execute in SQL Editor
4. Save URL and API key
```

### Stage 3: Backend Deployment (Render)

```
Files Used:
├── backend/                 → All backend code
├── requirements-backend.txt → Dependencies
├── render.yaml             → Configuration
├── env.backend.example     → Env vars reference
└── MCP servers (*.py)      → Imported by backend

Environment Variables (set in Render):
- ENVIRONMENT=production
- OPENROUTER_API_KEY=...
- SUPABASE_URL=...
- SUPABASE_KEY=...
- FRONTEND_URL=... (add after frontend deploy)
```

### Stage 4: Frontend Deployment (Streamlit Cloud)

```
Files Used:
├── frontend/                → All frontend code
├── requirements-frontend.txt → Dependencies
└── env.frontend.example     → Secrets reference

Streamlit Secrets (set in dashboard):
API_URL = "https://your-backend.onrender.com"
```

### Stage 5: Post-Deployment (Updates)

```
Update in Render (Backend):
- FRONTEND_URL=https://your-app.streamlit.app
- BASE_URL=https://your-backend.onrender.com

Test:
- Backend health: /health
- Frontend connection
- End-to-end chat
```

## Import Flow

### Backend Import Structure

```
backend/main.py
└── imports backend.api.routes
    └── imports backend.services.mcp_service
        └── imports backend.services.auth_service
            └── imports supabase

backend/services/mcp_service.py
├── imports mcp_server (Canvas)
├── imports calendar_mcp_server
├── imports gmail_mcp_server
├── imports flashcard_mcp_server
└── imports flashcard_generator
```

### Frontend Import Structure

```
frontend/app.py
└── imports frontend.utils.api
    └── uses requests to call backend

frontend/pages/1_⚙️_Settings.py
└── imports frontend.utils.api
    └── uses requests for credential management
```

## Data Flow

### Request Flow

```
1. User Input (Frontend)
   │
   ├─→ frontend/app.py
   │   └─→ frontend/utils/api.py
   │       └─→ POST /chat (Backend)
   │
2. Backend Processing
   │
   ├─→ backend/api/routes.py
   │   ├─→ backend/services/auth_service.py (get user creds from Supabase)
   │   └─→ backend/services/mcp_service.py
   │       ├─→ mcp_server.py (Canvas)
   │       ├─→ calendar_mcp_server.py
   │       ├─→ gmail_mcp_server.py
   │       └─→ flashcard_mcp_server.py
   │
3. External APIs
   │
   ├─→ OpenRouter (AI)
   ├─→ Canvas LMS
   ├─→ Google Calendar
   └─→ Gmail
   │
4. Response
   │
   └─→ Backend → Frontend → User
```

### Credential Storage Flow

```
1. User enters credentials in Settings
   │
2. Frontend sends to backend
   │
3. Backend stores in Supabase
   │
   Supabase:
   user_credentials table
   ├─ user_id
   ├─ service (canvas/calendar/gmail)
   └─ credentials (encrypted JSON)
   │
4. On subsequent requests:
   │
   Backend retrieves from Supabase
   └─→ Uses for that user's API calls
```

## Deployment Dependency Graph

```
┌─────────────┐
│   GitHub    │
│  Repository │
└──────┬──────┘
       │
       ├──────────────────────────────┐
       │                              │
       ▼                              ▼
┌──────────────┐              ┌──────────────┐
│   Supabase   │              │    Render    │
│   Database   │◄─────────────│   Backend    │
└──────────────┘   queries    └──────┬───────┘
       ▲                              │
       │                              │ API_URL
       │                              │
       │                              ▼
       │                      ┌──────────────┐
       │                      │  Streamlit   │
       └──────────────────────│   Frontend   │
            user_id +         └──────────────┘
            credentials
```

**Deployment Order**:
1. Supabase (independent)
2. Backend (needs Supabase URL)
3. Frontend (needs Backend URL)
4. Update Backend (with Frontend URL for CORS)

## File Modification Guidelines

### Never Modify in Production

- MCP server files (mcp_server.py, calendar_mcp_server.py, etc.)
- Supabase schema (after initial setup)
- render.yaml (after initial deployment)

### Modify Through Dashboard

- Environment variables (Render dashboard)
- Secrets (Streamlit Cloud dashboard)
- Database settings (Supabase dashboard)

### Modify Through Git

- Backend code (backend/)
- Frontend code (frontend/)
- Documentation (docs/)
- Configuration templates (env.*.example)

### Auto-Deploy on Git Push

- Render: Watches main branch → Auto-redeploys backend
- Streamlit Cloud: Watches main branch → Auto-redeploys frontend

## Quick Reference

| Task | Files to Use | Where |
|------|-------------|-------|
| Local development | requirements.txt, env.example | Local machine |
| Backend deploy | backend/, requirements-backend.txt, render.yaml | Render |
| Frontend deploy | frontend/, requirements-frontend.txt | Streamlit Cloud |
| Database setup | config/supabase_schema.sql | Supabase SQL Editor |
| Configure backend | env.backend.example | Render env vars |
| Configure frontend | env.frontend.example | Streamlit secrets |
| OAuth setup | scripts/authenticate_*.py | Local machine |

---

**Legend**:
- 📦 Backend
- 🎨 Frontend
- 🗄️ Database
- 🔧 Tools
- 📝 Documentation
- ⚙️ Configuration
- 🛠️ Scripts
- 💾 Data
- ⭐ Critical file

