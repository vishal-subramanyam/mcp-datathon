# Canvas MPC - Deployment Guide

This guide covers the complete deployment process for Canvas MPC, including backend (Render), frontend (Streamlit Cloud), and database (Supabase) setup.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Prerequisites](#prerequisites)
3. [Supabase Setup](#supabase-setup)
4. [Backend Deployment (Render)](#backend-deployment-render)
5. [Frontend Deployment (Streamlit Cloud)](#frontend-deployment-streamlit-cloud)
6. [Configuration](#configuration)
7. [Testing](#testing)
8. [Troubleshooting](#troubleshooting)

## Architecture Overview

```
┌─────────────────┐
│   User Browser  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    Frontend     │
│  (Streamlit)    │ ← Deployed on Streamlit Cloud
└────────┬────────┘
         │ HTTPS
         ▼
┌─────────────────┐
│    Backend      │
│   (FastAPI)     │ ← Deployed on Render
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌──────┐  ┌──────────┐
│ MCP  │  │ Supabase │
│Servers│  │ Database │
└──────┘  └──────────┘
    │
    ├─→ Canvas API
    ├─→ Google Calendar API
    ├─→ Gmail API
    └─→ OpenRouter API (Claude)
```

## Prerequisites

Before deploying, ensure you have:

1. **GitHub Account** - for version control and deployments
2. **Render Account** - for backend hosting (free tier available)
3. **Streamlit Cloud Account** - for frontend hosting (free tier available)
4. **Supabase Account** - for database (free tier available)
5. **OpenRouter API Key** - for AI features
6. **Canvas API Key** - for Canvas integration
7. **Google Cloud Project** - for Calendar and Gmail APIs (optional)

## Supabase Setup

### 1. Create a Supabase Project

1. Go to [supabase.com](https://supabase.com)
2. Click "Start your project"
3. Create a new organization (if needed)
4. Click "New Project"
5. Choose a name, database password, and region
6. Wait for the project to be provisioned (~2 minutes)

### 2. Set Up Database Schema

1. In your Supabase dashboard, go to "SQL Editor"
2. Click "New Query"
3. Copy the contents of `config/supabase_schema.sql`
4. Paste into the SQL Editor
5. Click "Run" to execute

This creates:
- `user_sessions` table - for managing user sessions
- `user_credentials` table - for storing per-user API credentials
- Row Level Security (RLS) policies for data protection
- Triggers for automatic timestamp updates

### 3. Get Your Credentials

1. Go to "Settings" → "API" in your Supabase dashboard
2. Copy these values:
   - **Project URL** (e.g., `https://xxxxx.supabase.co`)
   - **Anon/Public Key** (starts with `eyJ...`)
3. Save these for later use in environment variables

## Backend Deployment (Render)

### 1. Prepare Your Repository

Ensure your code is pushed to GitHub with the following structure:

```
CanvasMPC/
├── backend/
│   ├── main.py
│   ├── api/
│   ├── services/
│   └── ...
├── requirements-backend.txt
├── render.yaml
└── ...
```

### 2. Create a New Web Service on Render

1. Go to [render.com](https://render.com)
2. Click "New" → "Web Service"
3. Connect your GitHub repository
4. Select the repository containing your code

### 3. Configure the Service

**Basic Settings:**
- **Name**: `canvas-mpc-backend`
- **Region**: Choose closest to your users
- **Branch**: `main` (or your default branch)
- **Root Directory**: Leave empty
- **Environment**: `Python 3`
- **Build Command**: `pip install -r requirements-backend.txt`
- **Start Command**: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`

**Plan:**
- Choose "Starter" or "Free" tier

### 4. Set Environment Variables

In Render dashboard, go to "Environment" and add:

```bash
# Required
ENVIRONMENT=production
OPENROUTER_API_KEY=your_openrouter_api_key
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=your_supabase_anon_key

# Update after first deploy
BASE_URL=https://canvas-mpc-backend.onrender.com

# Update after frontend deploy
FRONTEND_URL=https://your-app.streamlit.app
STREAMLIT_URL=https://your-app.streamlit.app

# Optional: Default Canvas credentials
CANVAS_API_URL=https://canvas.instructure.com
CANVAS_API_KEY=your_canvas_api_token
```

### 5. Deploy

1. Click "Create Web Service"
2. Wait for deployment (~5-10 minutes)
3. Once deployed, note your backend URL (e.g., `https://canvas-mpc-backend.onrender.com`)
4. Test the health endpoint: `https://your-backend-url.onrender.com/health`

### 6. Configure Persistent Storage (Optional)

If you want flashcard data to persist:

1. In Render dashboard, go to "Disks"
2. Click "Add Disk"
3. Name: `flashcard-data`
4. Mount Path: `/opt/render/project/flashcard_data`
5. Size: 1 GB
6. Click "Create"

## Frontend Deployment (Streamlit Cloud)

### 1. Prepare Frontend Files

Ensure your repository has:

```
CanvasMPC/
├── frontend/
│   ├── app.py
│   ├── pages/
│   └── utils/
└── requirements-frontend.txt
```

### 2. Deploy to Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with GitHub
3. Click "New app"
4. Select your repository
5. Configure deployment:
   - **Main file path**: `frontend/app.py`
   - **Python version**: 3.11
   - **App URL**: Choose your subdomain

### 3. Configure Secrets

In Streamlit Cloud, go to "Settings" → "Secrets" and add:

```toml
API_URL = "https://canvas-mpc-backend.onrender.com"
```

### 4. Deploy

1. Click "Deploy"
2. Wait for deployment (~2-5 minutes)
3. Once deployed, note your frontend URL (e.g., `https://your-app.streamlit.app`)

### 5. Update Backend CORS

Go back to Render and update the environment variables:

```bash
FRONTEND_URL=https://your-app.streamlit.app
STREAMLIT_URL=https://your-app.streamlit.app
```

Redeploy the backend for changes to take effect.

## Configuration

### Per-User Credentials

Users can configure their own API credentials through the Settings page in the frontend:

1. Navigate to Settings (sidebar)
2. Enter a unique User ID
3. Add credentials for:
   - Canvas API
   - Google Calendar (OAuth token)
   - Gmail (OAuth token)

These credentials are securely stored in Supabase and used for that user's requests.

### Google OAuth Setup

For Calendar and Gmail integration:

1. Create a project in [Google Cloud Console](https://console.cloud.google.com)
2. Enable Calendar API and Gmail API
3. Create OAuth 2.0 credentials
4. Download `credentials.json`
5. Run authentication scripts locally:
   ```bash
   python scripts/authenticate_calendar.py
   python scripts/authenticate_gmail.py
   ```
6. Upload the generated tokens via the Settings page

## Testing

### Backend Tests

```bash
# Health check
curl https://your-backend.onrender.com/health

# List available tools
curl https://your-backend.onrender.com/tools

# Test chat endpoint (requires auth)
curl -X POST https://your-backend.onrender.com/chat \
  -H "Content-Type: application/json" \
  -d '{
    "query": "List my courses",
    "conversation_history": []
  }'
```

### Frontend Tests

1. Open your Streamlit app
2. Check backend connection status
3. Try a simple query: "What courses do I have?"
4. Verify responses are working

### Integration Tests

1. **Canvas**: "Show me my upcoming assignments"
2. **Calendar**: "Create a calendar event for tomorrow at 2pm"
3. **Gmail**: "Show me my recent emails"
4. **Flashcards**: "Create flashcards from my Computer Science course"

## Troubleshooting

### Backend Issues

**Build Fails:**
- Check `requirements-backend.txt` for correct package versions
- Ensure Python 3.11 is specified
- Review build logs in Render dashboard

**Runtime Errors:**
- Check environment variables are set correctly
- Review application logs in Render
- Verify health endpoint returns 200

**CORS Errors:**
- Ensure `FRONTEND_URL` matches your Streamlit app URL
- Check CORS middleware configuration in `backend/main.py`

### Frontend Issues

**Cannot Connect to Backend:**
- Verify `API_URL` in Streamlit secrets
- Check backend health endpoint
- Ensure backend CORS allows frontend URL

**Import Errors:**
- Check `requirements-frontend.txt` includes all dependencies
- Verify file structure matches import paths

### Supabase Issues

**Connection Errors:**
- Verify `SUPABASE_URL` and `SUPABASE_KEY` are correct
- Check Supabase project is active
- Review RLS policies if getting permission errors

**Credentials Not Saving:**
- Check database schema is created correctly
- Verify RLS policies allow service role access
- Review backend logs for error messages

### Performance Issues

**Slow Response Times:**
- Check OpenRouter API status
- Review timeout settings (default: 90s)
- Consider upgrading Render plan

**Free Tier Limitations:**
- Render free tier spins down after 15 minutes of inactivity
- First request after spin-down takes ~30-60 seconds
- Consider upgrading to paid tier for production use

## Next Steps

1. **Custom Domain**: Configure custom domains in Render and Streamlit
2. **Monitoring**: Set up logging and monitoring (e.g., Sentry)
3. **CI/CD**: Configure GitHub Actions for automated testing
4. **Security**: Review and enhance security settings
5. **Scaling**: Monitor usage and scale resources as needed

## Support

For issues or questions:
- Check the [GitHub Issues](https://github.com/yourusername/CanvasMPC/issues)
- Review documentation in the `docs/` directory
- Contact the development team

---

**Last Updated**: November 2025

