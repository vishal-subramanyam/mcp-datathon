# Canvas MPC - Project Structure

This document explains the organization of the Canvas MPC codebase and how each component should be used during deployment.

## Directory Structure

```
CanvasMPC/
├── backend/                      # Backend application (Deploy to Render)
│   ├── main.py                  # FastAPI application entry point
│   ├── api/                     # API routes and endpoints
│   │   ├── __init__.py
│   │   └── routes.py            # Chat, tools, and auth endpoints
│   ├── services/                # Business logic services
│   │   ├── __init__.py
│   │   ├── auth_service.py      # Supabase authentication
│   │   └── mcp_service.py       # MCP server coordination
│   ├── mcp_servers/             # MCP server modules (placeholder)
│   │   └── __init__.py
│   └── utils/                   # Utility functions
│       └── __init__.py
│
├── frontend/                     # Frontend application (Deploy to Streamlit Cloud)
│   ├── app.py                   # Main Streamlit application
│   ├── pages/                   # Streamlit pages
│   │   └── 1_⚙️_Settings.py    # User settings and credentials
│   └── utils/                   # Frontend utilities
│       ├── __init__.py
│       └── api.py               # Backend API communication
│
├── config/                       # Configuration files
│   └── supabase_schema.sql      # Database schema for Supabase
│
├── docs/                         # Documentation
│   ├── DEPLOYMENT_GUIDE.md      # Comprehensive deployment guide
│   └── PROJECT_STRUCTURE.md     # This file
│
├── scripts/                      # Helper scripts (keep locally)
│   ├── authenticate_calendar.py # Google Calendar OAuth
│   └── authenticate_gmail.py    # Gmail OAuth
│
├── shared/                       # Shared utilities (if needed)
│
├── flashcard_data/              # Flashcard storage (gitignored)
│   ├── flashcards.json
│   └── progress.json
│
├── requirements-backend.txt      # Backend dependencies
├── requirements-frontend.txt     # Frontend dependencies
├── requirements.txt             # Combined dependencies (local dev)
│
├── render.yaml                  # Render deployment configuration
│
├── env.example                  # Environment variables template
├── env.backend.example          # Backend-specific env vars
├── env.frontend.example         # Frontend-specific env vars
│
├── README.md                    # Project overview
└── .gitignore                   # Git ignore rules
```

## Component Descriptions

### Backend (`backend/`)

**Purpose**: Handles all server-side logic, API requests, MCP server coordination, and database interactions.

**Deployment Target**: Render (or any Python hosting service)

**Key Files**:
- `main.py`: FastAPI application initialization and CORS configuration
- `api/routes.py`: REST API endpoints for chat, tools, and authentication
- `services/auth_service.py`: Manages user sessions and credentials via Supabase
- `services/mcp_service.py`: Coordinates calls to various MCP servers (Canvas, Calendar, Gmail, Flashcards)

**Dependencies**: `requirements-backend.txt`

**Environment Variables** (from `env.backend.example`):
- `ENVIRONMENT`: production/development
- `PORT`: Server port (set by Render)
- `OPENROUTER_API_KEY`: AI model API key
- `SUPABASE_URL`: Supabase project URL
- `SUPABASE_KEY`: Supabase API key
- `FRONTEND_URL`: Frontend URL for CORS
- Canvas, Calendar, Gmail credentials

### Frontend (`frontend/`)

**Purpose**: User interface built with Streamlit for interacting with the backend.

**Deployment Target**: Streamlit Cloud (or Vercel with custom setup)

**Key Files**:
- `app.py`: Main chat interface
- `pages/1_⚙️_Settings.py`: Credential management page
- `utils/api.py`: Helper functions for backend communication

**Dependencies**: `requirements-frontend.txt`

**Environment Variables** (from `env.frontend.example`):
- `API_URL`: Backend API URL

**Features**:
- Real-time chat interface
- Backend connection monitoring
- Per-user credential management
- Multi-page navigation (chat, settings)

### Configuration (`config/`)

**Purpose**: Configuration files and database schemas.

**Files**:
- `supabase_schema.sql`: PostgreSQL schema for Supabase
  - Creates `user_sessions` and `user_credentials` tables
  - Sets up Row Level Security (RLS) policies
  - Configures indexes and triggers

**Usage**: Run in Supabase SQL Editor during initial setup

### Documentation (`docs/`)

**Purpose**: Comprehensive guides and documentation.

**Files**:
- `DEPLOYMENT_GUIDE.md`: Step-by-step deployment instructions
- `PROJECT_STRUCTURE.md`: This file - explains project organization

### Scripts (`scripts/`)

**Purpose**: Helper scripts for local development and authentication.

**Files**:
- `authenticate_calendar.py`: Google Calendar OAuth flow
- `authenticate_gmail.py`: Gmail OAuth flow

**Note**: These scripts should be run locally, not deployed. They generate token files that can be uploaded via the Settings page.

### Root Files

**Configuration Files**:
- `render.yaml`: Render deployment configuration
  - Defines web service
  - Sets environment variables
  - Configures persistent disk for flashcards

**Dependency Files**:
- `requirements-backend.txt`: Backend-only dependencies (for Render)
- `requirements-frontend.txt`: Frontend-only dependencies (for Streamlit)
- `requirements.txt`: Combined dependencies (for local development)

**Environment Templates**:
- `env.example`: Complete environment variable template
- `env.backend.example`: Backend-specific variables
- `env.frontend.example`: Frontend-specific variables

## MCP Servers

The original MCP server files are in the root directory:
- `mcp_server.py` (Canvas)
- `calendar_mcp_server.py`
- `gmail_mcp_server.py`
- `flashcard_mcp_server.py`

These are imported by `backend/services/mcp_service.py` to provide tool functionality.

**Note**: In the reorganized structure, these remain in the root to avoid breaking imports. In a future refactor, they could be moved to `backend/mcp_servers/` with updated import paths.

## Data Storage

### Flashcard Data (`flashcard_data/`)

**Purpose**: Stores flashcard sets and progress data.

**Deployment Considerations**:
- On Render: Use persistent disk (configured in `render.yaml`)
- Locally: Standard directory
- Data format: JSON files

**Files**:
- `flashcards.json`: Flashcard set definitions
- `progress.json`: User progress tracking

### User Credentials (Supabase)

**Purpose**: Securely stores per-user API credentials.

**Storage**: Supabase `user_credentials` table

**Security**: Row Level Security (RLS) policies ensure users can only access their own credentials

## Deployment Workflow

### 1. Local Development

```bash
# Setup
git clone <repository>
cd CanvasMPC
cp env.example .env
# Edit .env with your credentials
pip install -r requirements.txt

# Run backend
uvicorn backend.main:app --reload --port 8000

# Run frontend (in another terminal)
streamlit run frontend/app.py
```

### 2. Backend Deployment (Render)

```bash
# Prerequisites
- Push code to GitHub
- Create Supabase project and run schema

# Render Setup
1. Create new Web Service
2. Connect GitHub repository
3. Use settings from render.yaml
4. Set environment variables (see env.backend.example)
5. Deploy

# Post-deployment
- Test health endpoint
- Update BASE_URL env var
- Update FRONTEND_URL after frontend deploy
```

### 3. Frontend Deployment (Streamlit Cloud)

```bash
# Prerequisites
- Backend must be deployed and healthy
- Have backend URL ready

# Streamlit Cloud Setup
1. Login to share.streamlit.io
2. Create new app
3. Point to frontend/app.py
4. Set secrets (API_URL)
5. Deploy

# Post-deployment
- Test connection to backend
- Update backend CORS settings
```

### 4. Supabase Setup

```bash
# One-time setup
1. Create project on supabase.com
2. Run config/supabase_schema.sql in SQL Editor
3. Get credentials (URL and Key)
4. Add to backend environment variables
```

## Environment-Specific Configurations

### Development

- All services run locally
- Use `requirements.txt` for combined dependencies
- Backend on `localhost:8000`
- Frontend on `localhost:8501`
- Environment variables from `.env`

### Production

**Backend (Render)**:
- Use `requirements-backend.txt`
- Environment variables from Render dashboard
- HTTPS enabled automatically
- Health checks at `/health`

**Frontend (Streamlit Cloud)**:
- Use `requirements-frontend.txt`
- Secrets from Streamlit Cloud dashboard
- HTTPS enabled automatically
- Automatic redeployment on git push

**Database (Supabase)**:
- Managed PostgreSQL database
- RLS policies for security
- Automatic backups
- Connection pooling

## Security Considerations

### API Keys and Secrets

**Never commit**:
- `.env` files
- Token files (`.json`)
- API keys
- Passwords

**Storage**:
- Backend: Render environment variables
- Frontend: Streamlit secrets
- User credentials: Supabase (encrypted)

### Per-User Credentials

Users can store their own API credentials via the Settings page:
1. User enters credentials in frontend
2. Frontend sends to backend `/auth/credentials` endpoint
3. Backend stores in Supabase with user_id
4. Credentials used for that user's requests only

### CORS

Backend CORS is configured to allow:
- Frontend URL (from `FRONTEND_URL` env var)
- Local development (`localhost:8501`)
- Additional URLs from `STREAMLIT_URL`, `VERCEL_URL`

## Troubleshooting

### Import Errors

**Issue**: Module not found errors

**Solution**:
- Check Python path includes correct directories
- Verify `__init__.py` files exist in all packages
- Use absolute imports from project root

### Deployment Failures

**Backend**:
- Check build logs in Render
- Verify all dependencies in `requirements-backend.txt`
- Test locally first with same Python version

**Frontend**:
- Check logs in Streamlit Cloud
- Verify `app.py` path is correct
- Ensure all dependencies in `requirements-frontend.txt`

### Connection Issues

**Frontend can't reach backend**:
- Verify `API_URL` in Streamlit secrets
- Check backend health endpoint
- Ensure CORS allows frontend URL
- Test backend directly with curl

### Database Issues

**Credentials not saving**:
- Verify Supabase schema is created
- Check RLS policies
- Review backend logs for errors
- Test Supabase connection directly

## Best Practices

### Development

1. Always work on a feature branch
2. Test locally before pushing
3. Keep dependencies updated
4. Document new features

### Deployment

1. Test in development environment first
2. Use staging environment when possible
3. Deploy backend before frontend
4. Verify health checks pass
5. Monitor logs after deployment

### Security

1. Never commit secrets
2. Use environment variables
3. Enable RLS in Supabase
4. Implement proper authentication
5. Regular security audits

### Maintenance

1. Monitor resource usage
2. Review logs regularly
3. Keep dependencies updated
4. Backup Supabase data
5. Document changes

## Future Improvements

### Potential Enhancements

1. **Move MCP servers**: Relocate to `backend/mcp_servers/` with updated imports
2. **Add CI/CD**: GitHub Actions for automated testing and deployment
3. **Enhance authentication**: Implement proper user authentication with JWT
4. **Add monitoring**: Integrate logging and monitoring services
5. **Optimize performance**: Caching, connection pooling, async optimizations
6. **Add tests**: Unit tests, integration tests, E2E tests

### Scalability Considerations

- **Backend**: Can scale horizontally with load balancer
- **Frontend**: Streamlit Cloud handles scaling automatically
- **Database**: Supabase can upgrade to larger plans
- **Caching**: Add Redis for session and response caching
- **Queue**: Add job queue for long-running tasks

---

**Last Updated**: November 2025

