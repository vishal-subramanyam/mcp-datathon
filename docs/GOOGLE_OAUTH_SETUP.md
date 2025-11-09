# Google OAuth Setup Guide

Complete guide for setting up Google account connection for Gmail and Calendar integration.

## Prerequisites

- Google Cloud account
- Backend deployed on Render (or running locally)
- Supabase configured for credential storage

## Step 1: Google Cloud Console Setup

### 1.1 Create a Project

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Click on the project dropdown at the top
3. Click "New Project"
4. Enter project name: `Canvas MPC` (or your choice)
5. Click "Create"
6. Wait for project creation (~30 seconds)

### 1.2 Enable Required APIs

1. Navigate to **APIs & Services** → **Library**
2. Search for and enable:
   - **Gmail API**
   - **Google Calendar API**
   - **Google+ API** (for user email)

### 1.3 Configure OAuth Consent Screen

1. Go to **APIs & Services** → **OAuth consent screen**
2. Choose **External** user type (unless you have Google Workspace)
   - **External**: Any Google user can connect (required for production)
   - **Internal**: Only users in your Google Workspace organization
3. Fill in app information:
   - **App name**: `Canvas MPC` (or your app name)
   - **User support email**: Your email
   - **App logo**: (Optional) Upload a logo
   - **App domain**: (Optional) Your app domain
   - **Application home page**: Your app URL (e.g., `https://your-app.streamlit.app`)
   - **Application privacy policy link**: (Required for production) Link to your privacy policy
   - **Application terms of service link**: (Required for production) Link to your terms of service
   - **Authorized domains**: Add your domain (e.g., `streamlit.app`, `onrender.com`)
   - **Developer contact information**: Your email
4. Click **Save and Continue**
5. Add scopes:
   - Click **Add or Remove Scopes**
   - Add these scopes:
     - `https://www.googleapis.com/auth/gmail.modify`
     - `https://www.googleapis.com/auth/calendar`
     - `https://www.googleapis.com/auth/userinfo.email` (for getting user email)
   - Click **Update** then **Save and Continue**
6. **Test users** (Optional - only needed during testing):
   - Add test user emails if you want to test before publishing
   - Once published, this step is not needed
   - Click **Save and Continue**
7. Review your configuration
8. **IMPORTANT FOR PRODUCTION**: Click **Back to Dashboard**

### 1.3.1 Publish Your App (REQUIRED for Production)

**⚠️ CRITICAL STEP**: Your app must be PUBLISHED for any user to connect their Google account.

1. Go to **APIs & Services** → **OAuth consent screen**
2. You'll see your app status at the top:
   - **Testing**: Only test users can connect ❌
   - **In production**: Any Google user can connect ✅
3. If status shows "Testing":
   - Click **PUBLISH APP** button
   - Confirm the warning about making your app available to all users
   - Wait for Google to review (usually instant for verified apps, or up to 7 days for unverified)
4. **Verification** (Recommended):
   - For sensitive scopes (Gmail, Calendar), Google may require verification
   - You'll see a warning banner if verification is needed
   - Click "Submit for verification" if prompted
   - Fill out the OAuth verification form
   - Provide app description, video demo, privacy policy, etc.
   - Verification typically takes 4-6 weeks
5. **For immediate testing while verification is pending**:
   - You can publish the app without verification
   - Users will see an "Unverified app" warning
   - They can click "Advanced" → "Go to [Your App] (unsafe)" to proceed
   - Once verified, the warning disappears

### 1.4 Create OAuth 2.0 Credentials

1. Go to **APIs & Services** → **Credentials**
2. Click **Create Credentials** → **OAuth client ID**
3. Select **Web application** as application type
4. Fill in:
   - **Name**: `Canvas MPC Web Client`
   - **Authorized JavaScript origins**: 
     - `https://your-backend.onrender.com` (production)
     - `http://localhost:8000` (local development)
   - **Authorized redirect URIs**:
     - `https://your-backend.onrender.com/auth/google/callback` (production)
     - `http://localhost:8000/auth/google/callback` (local development)
5. Click **Create**
6. **Important**: Copy the **Client ID** and **Client Secret**
   - Client ID: `xxxxx-xxxxx.apps.googleusercontent.com`
   - Client Secret: `GOCSPX-xxxxx`

## Step 2: Configure Environment Variables

### For Local Development

Create or update `.env` file in project root:

```bash
# Google OAuth
GOOGLE_CLIENT_ID=your_client_id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_client_secret
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/google/callback

# Backend URL
BASE_URL=http://localhost:8000

# Frontend URL
FRONTEND_URL=http://localhost:8501
STREAMLIT_URL=http://localhost:8501
```

### For Render Deployment

1. Go to your Render dashboard
2. Select your backend service
3. Go to **Environment** tab
4. Add these environment variables:

```bash
GOOGLE_CLIENT_ID=your_client_id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_client_secret
GOOGLE_REDIRECT_URI=https://your-backend.onrender.com/auth/google/callback
BASE_URL=https://your-backend.onrender.com
FRONTEND_URL=https://your-app.streamlit.app
STREAMLIT_URL=https://your-app.streamlit.app
```

**Important**: Replace `your-backend.onrender.com` with your actual Render backend URL.

## Step 3: Update Google Cloud Console Redirect URI

After deploying to Render:

1. Go back to Google Cloud Console
2. **APIs & Services** → **Credentials**
3. Click on your OAuth 2.0 Client ID
4. Add your production redirect URI:
   - `https://your-actual-backend-url.onrender.com/auth/google/callback`
5. Click **Save**

## Step 4: Test the Connection

### Local Testing

1. Start your backend:
   ```bash
   uvicorn backend.main:app --reload --port 8000
   ```

2. Start your frontend:
   ```bash
   streamlit run frontend/app.py
   ```

3. In the Streamlit app:
   - Go to Settings page (⚙️ in sidebar)
   - Enter a User ID (e.g., your email)
   - Click "🔗 Connect Google Account"
   - You'll be redirected to Google login
   - Grant permissions
   - You'll be redirected back with success message

### Production Testing

1. Open your deployed Streamlit app
2. Go to Settings page
3. Enter User ID
4. Click "🔗 Connect Google Account"
5. Complete OAuth flow
6. Verify success message

## Step 5: Verify Connection

After connecting:

1. Check Settings page shows "✅ Google account linked!"
2. Try asking in chat:
   - "List my upcoming calendar events"
   - "Show me my recent emails"
   - "Send an email to..."

## Troubleshooting

### Error: "redirect_uri_mismatch"

**Cause**: Redirect URI in Google Cloud Console doesn't match your backend URL.

**Solution**:
1. Check your `GOOGLE_REDIRECT_URI` environment variable
2. Ensure it matches exactly in Google Cloud Console
3. Include both `http://localhost:8000` (dev) and `https://your-backend.onrender.com` (prod)

### Error: "Google OAuth not configured"

**Cause**: Environment variables not set.

**Solution**:
1. Verify `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` are set
2. Check Render environment variables (if deployed)
3. Restart backend after setting variables

### Error: "Invalid state parameter"

**Cause**: OAuth state expired or invalid.

**Solution**:
1. Try connecting again
2. Ensure backend is running
3. Check backend logs for errors

### OAuth Button Doesn't Work

**Cause**: Backend not accessible or CORS issues.

**Solution**:
1. Verify backend is running
2. Check `API_URL` in frontend matches backend URL
3. Test backend health: `curl https://your-backend.onrender.com/health`

### Credentials Not Saving

**Cause**: Supabase not configured or RLS policies blocking.

**Solution**:
1. Verify `SUPABASE_URL` and `SUPABASE_KEY` are set
2. Check Supabase database schema is created
3. Review Supabase logs for errors

## Security Notes

1. **Never commit** `GOOGLE_CLIENT_SECRET` to git
2. Use environment variables for all sensitive data
3. Keep your Client Secret secure
4. Regularly rotate credentials if compromised
5. Use HTTPS in production (Render provides this)

## Next Steps

After successful setup:

1. Test Gmail integration: "Send an email to..."
2. Test Calendar integration: "Create a calendar event..."
3. Verify credentials are stored in Supabase
4. Test with multiple users (different User IDs)

## Support

If you encounter issues:

1. Check backend logs on Render
2. Check Supabase logs
3. Verify all environment variables are set
4. Test OAuth flow step by step
5. Review Google Cloud Console for API quotas/limits

---

**Last Updated**: January 2025

