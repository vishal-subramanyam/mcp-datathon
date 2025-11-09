# Canvas MPC - Quick Start Guide

Get Canvas MPC up and running in 15 minutes.

## Prerequisites

- Python 3.11+
- Git
- Accounts on: Render, Streamlit Cloud, Supabase (all have free tiers)

## Step-by-Step Setup

### 1. Clone and Setup (2 minutes)

```bash
git clone <your-repository-url>
cd CanvasMPC
cp env.example .env
```

### 2. Supabase Setup (3 minutes)

1. Go to [supabase.com](https://supabase.com) → Create new project
2. Wait for provisioning
3. Go to SQL Editor → New Query
4. Copy contents of `config/supabase_schema.sql` → Run
5. Go to Settings → API → Copy:
   - **Project URL**
   - **Anon key**

### 3. Backend Deploy to Render (5 minutes)

1. Push code to GitHub (if not already):
   ```bash
   git add .
   git commit -m "Initial commit"
   git push origin main
   ```

2. Go to [render.com](https://render.com) → New → Web Service
3. Connect GitHub repository
4. Configure:
   - **Build Command**: `pip install -r requirements-backend.txt`
   - **Start Command**: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`

5. Add environment variables:
   ```
   ENVIRONMENT=production
   OPENROUTER_API_KEY=your_key
   SUPABASE_URL=your_url
   SUPABASE_KEY=your_key
   ```

6. Click "Create Web Service"
7. Wait for deployment → Copy your backend URL

### 4. Frontend Deploy to Streamlit Cloud (3 minutes)

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. New app → Select repository
3. Configure:
   - **Main file**: `frontend/app.py`
   - **Python version**: 3.11

4. Add secrets:
   ```toml
   API_URL = "https://your-backend.onrender.com"
   ```

5. Click "Deploy"
6. Copy your frontend URL

### 5. Update Backend CORS (2 minutes)

1. Go back to Render dashboard
2. Add/Update environment variables:
   ```
   FRONTEND_URL=https://your-app.streamlit.app
   STREAMLIT_URL=https://your-app.streamlit.app
   ```

3. Save → Backend will redeploy automatically

## Test Your Deployment

1. Open your Streamlit app URL
2. Check backend connection status (should show ✅)
3. Try a test query: "Hello, are you working?"
4. If you get a response, everything is working!

## Add Your Credentials

### Canvas API

1. Get your Canvas API token:
   - Go to Canvas → Account → Settings
   - Scroll to "Approved Integrations"
   - Click "+ New Access Token"
   - Copy the token

2. In Streamlit app:
   - Go to Settings page (sidebar)
   - Enter a User ID
   - Expand "Canvas Settings"
   - Enter your Canvas URL and token
   - Click "Save"

### Google Calendar/Gmail (Optional)

1. Create Google Cloud project:
   - Go to [console.cloud.google.com](https://console.cloud.google.com)
   - Create new project
   - Enable Calendar API and/or Gmail API
   - Create OAuth 2.0 credentials
   - Download credentials.json

2. Run locally to get tokens:
   ```bash
   pip install -r requirements-backend.txt
   python scripts/authenticate_calendar.py
   python scripts/authenticate_gmail.py
   ```

3. Upload tokens in Streamlit Settings page

## Common Issues

### Backend Not Connecting

**Symptom**: Frontend shows ❌ Cannot connect to backend

**Fix**:
1. Check backend URL is correct in Streamlit secrets
2. Visit backend URL + `/health` in browser
3. Check Render logs for errors
4. Verify all required env vars are set

### CORS Errors

**Symptom**: Browser console shows CORS errors

**Fix**:
1. Ensure `FRONTEND_URL` in Render matches your Streamlit URL exactly
2. Redeploy backend after changing CORS settings

### OpenRouter API Errors

**Symptom**: Chat returns API errors

**Fix**:
1. Verify `OPENROUTER_API_KEY` is correct
2. Check you have credits in OpenRouter account
3. Try a different model if current one is unavailable

## Next Steps

1. **Read Full Documentation**: Check `docs/DEPLOYMENT_GUIDE.md`
2. **Configure Additional Services**: Set up Calendar, Gmail, Canvas
3. **Customize**: Modify prompts, add features
4. **Monitor**: Check logs and usage
5. **Scale**: Upgrade plans as needed

## Getting Help

- **Documentation**: See `docs/` directory
- **Issues**: Check GitHub Issues
- **Logs**: 
  - Render: Dashboard → Logs
  - Streamlit: Dashboard → Logs
  - Supabase: Dashboard → Logs

## Development Mode

To run locally:

```bash
# Terminal 1 - Backend
pip install -r requirements.txt
uvicorn backend.main:app --reload --port 8000

# Terminal 2 - Frontend
streamlit run frontend/app.py
```

Access at:
- Frontend: http://localhost:8501
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

**Deployment Time**: ~15 minutes
**Cost**: $0 (free tiers)
**Maintenance**: Minimal (auto-deploys on git push)

