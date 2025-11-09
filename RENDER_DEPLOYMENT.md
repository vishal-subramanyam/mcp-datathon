# Render Deployment Guide

This guide will help you deploy the MCP Datathon backend to Render.

## Prerequisites

1. GitHub account
2. Render account (sign up at https://render.com)
3. All API keys ready:
   - OpenRouter API key
   - Canvas API key
   - Google OAuth credentials (for Gmail/Calendar)

## Step 1: Push Code to GitHub

1. Initialize git (if not already done):
   ```bash
   git init
   git add .
   git commit -m "Initial commit for Render deployment"
   ```

2. Create a GitHub repository and push:
   ```bash
   git remote add origin https://github.com/yourusername/mcp-datathon.git
   git branch -M main
   git push -u origin main
   ```

## Step 2: Create Render Web Service

1. Go to https://render.com and sign in
2. Click "New +" → "Web Service"
3. Connect your GitHub account (if not already connected)
4. Select your repository: `mcp-datathon`
5. Click "Connect"

## Step 3: Configure the Service

### Basic Settings:
- **Name**: `mcp-datathon-backend` (or your preferred name)
- **Region**: Choose closest to you
- **Branch**: `main`
- **Root Directory**: Leave empty

### Build & Deploy:
- **Environment**: `Python 3`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `uvicorn backend.api:app --host 0.0.0.0 --port $PORT`

### Advanced Settings:
- **Auto-Deploy**: `Yes` (optional, deploys on every push)

## Step 4: Set Environment Variables

In the Render dashboard, go to the "Environment" section and add:

### Required Variables:
```
OPENROUTER_API_KEY=your_openrouter_api_key
CANVAS_API_KEY=your_canvas_api_key
```

### Google OAuth (if using Gmail/Calendar):
```
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REDIRECT_URI=https://your-app-name.onrender.com/auth/google/callback
```

### Optional Variables:
```
FRONTEND_URL=https://your-streamlit-app.streamlit.app
STREAMLIT_URL=https://your-streamlit-app.streamlit.app
BASE_URL=https://your-app-name.onrender.com
ENVIRONMENT=production
USER_TIMEZONE=UTC
```

**Important**: Replace `your-app-name` with your actual Render service name.

## Step 5: Deploy

1. Click "Create Web Service"
2. Render will automatically:
   - Clone your repository
   - Install dependencies from `requirements.txt`
   - Start your FastAPI application
3. Wait 5-10 minutes for the first deployment
4. Your application will be available at:
   `https://your-app-name.onrender.com`

## Step 6: Update Google Cloud Console

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Navigate to: **APIs & Services** → **Credentials**
3. Edit your OAuth 2.0 Client ID
4. Add **Authorized redirect URI**:
   ```
   https://your-app-name.onrender.com/auth/google/callback
   ```
5. Save changes

## Step 7: Test Your Deployment

1. **Health Check**:
   Visit: `https://your-app-name.onrender.com/health`
   Should return: `{"status": "healthy", ...}`

2. **Tools Endpoint**:
   Visit: `https://your-app-name.onrender.com/tools`
   Should return list of available tools

3. **Update Frontend**:
   In your Streamlit app (`frontend.py`), update:
   ```python
   API_URL = os.getenv("API_URL", "https://your-app-name.onrender.com")
   ```

## Step 8: (Optional) Add PostgreSQL Database

If you need a database for user sessions/credentials:

1. In Render dashboard: "New +" → "PostgreSQL"
2. Name: `mcp-datathon-db`
3. Plan: **Free** (or choose paid for production)
4. Copy the **Internal Database URL**
5. Add to environment variables:
   ```
   DATABASE_URL=postgresql://... (auto-filled by Render)
   ```

## Troubleshooting

### Build Fails
- Check the "Logs" tab in Render dashboard
- Ensure all dependencies are in `requirements.txt`
- Verify Python version compatibility

### App Crashes
- Check logs for Python errors
- Verify all required environment variables are set
- Test locally first: `uvicorn backend.api:app --reload`

### Slow First Request
- Normal on free tier (cold start after 15 min inactivity)
- First request may take 30-60 seconds
- Consider upgrading to paid plan for always-on service

### CORS Errors
- Update `FRONTEND_URL` or `STREAMLIT_URL` environment variable
- Ensure your frontend URL matches exactly
- Check browser console for specific CORS error

### Port Issues
- Render automatically provides `$PORT` environment variable
- The start command uses `$PORT` correctly
- No manual port configuration needed

## Environment Variables Reference

See `.env.example` for a complete list of all environment variables.

## Monitoring

- **Logs**: View real-time logs in Render dashboard
- **Metrics**: Basic metrics available on free tier
- **Health Checks**: Automatic health checks via `/health` endpoint

## Next Steps

1. Set up monitoring and alerts
2. Configure custom domain (paid feature)
3. Set up auto-deploy from GitHub
4. Add database for user credential storage
5. Implement proper authentication flow

## Support

- Render Documentation: https://render.com/docs
- Render Status: https://status.render.com
- FastAPI Documentation: https://fastapi.tiangolo.com

