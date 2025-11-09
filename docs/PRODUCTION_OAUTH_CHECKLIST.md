# Production OAuth Checklist

Complete this checklist to enable Google account connection for all users in production.

## ✅ Google Cloud Console Setup

### OAuth Consent Screen
- [ ] **App is PUBLISHED** (not in Testing mode) ⚠️ CRITICAL
  - Go to OAuth consent screen
  - Click "PUBLISH APP" button
  - Confirm publishing
  - Status should show "In production"

- [ ] App information completed:
  - [ ] App name
  - [ ] User support email
  - [ ] Application home page URL
  - [ ] **Privacy policy URL** (required)
  - [ ] **Terms of service URL** (required)
  - [ ] Authorized domains added

- [ ] Scopes added:
  - [ ] `https://www.googleapis.com/auth/gmail.modify`
  - [ ] `https://www.googleapis.com/auth/calendar`
  - [ ] `https://www.googleapis.com/auth/userinfo.email`

- [ ] Test users removed (not needed when published)

### OAuth Credentials
- [ ] OAuth 2.0 Client ID created (Web application type)
- [ ] Production redirect URI added:
  - [ ] `https://your-backend.onrender.com/auth/google/callback`
- [ ] Client ID and Secret copied securely

### APIs Enabled
- [ ] Gmail API enabled
- [ ] Google Calendar API enabled
- [ ] Google+ API enabled (for user email)

## ✅ Render Environment Variables

Add these in Render Dashboard → Environment:

- [ ] `GOOGLE_CLIENT_ID` = your_client_id.apps.googleusercontent.com
- [ ] `GOOGLE_CLIENT_SECRET` = your_client_secret
- [ ] `GOOGLE_REDIRECT_URI` = https://your-backend.onrender.com/auth/google/callback
- [ ] `BASE_URL` = https://your-backend.onrender.com
- [ ] `FRONTEND_URL` = https://your-app.streamlit.app
- [ ] `STREAMLIT_URL` = https://your-app.streamlit.app
- [ ] `GOOGLE_OAUTH_PROMPT` = select_account (optional, default)

## ✅ Supabase Setup

- [ ] Supabase project created
- [ ] Database schema created (run `config/supabase_schema.sql`)
- [ ] `SUPABASE_URL` set in Render
- [ ] `SUPABASE_KEY` set in Render
- [ ] RLS policies enabled
- [ ] Service role access configured

## ✅ Frontend Setup

- [ ] Privacy Policy page created (`frontend/pages/3_Privacy_Policy.py`)
- [ ] Terms of Service page created (`frontend/pages/4_Terms_of_Service.py`)
- [ ] Privacy policy URL added to Google Cloud Console
- [ ] Terms of service URL added to Google Cloud Console
- [ ] Settings page has "Connect Google Account" button
- [ ] OAuth success redirect handling works

## ✅ Testing

### Local Testing
- [ ] OAuth flow works locally
- [ ] Credentials are stored in Supabase
- [ ] Gmail integration works
- [ ] Calendar integration works

### Production Testing
- [ ] App is published (not in Testing mode)
- [ ] Tested with a non-test-user Google account
- [ ] OAuth flow completes successfully
- [ ] User can connect Google account
- [ ] User can use Gmail features
- [ ] User can use Calendar features
- [ ] User can disconnect Google account

## ✅ Security

- [ ] `.env` file is in `.gitignore`
- [ ] No secrets committed to git
- [ ] Environment variables set securely in Render
- [ ] HTTPS enabled (Render provides this)
- [ ] CORS configured correctly
- [ ] RLS policies enabled in Supabase

## ✅ Documentation

- [ ] Privacy policy URL is accessible
- [ ] Terms of service URL is accessible
- [ ] User documentation updated
- [ ] Support contact information added

## 🚨 Critical Steps for Production

1. **PUBLISH YOUR APP** in Google Cloud Console
   - This is the most important step!
   - Without publishing, only test users can connect
   - Go to OAuth consent screen → Click "PUBLISH APP"

2. **Add Privacy Policy and Terms URLs**
   - Required by Google for production apps
   - Can be hosted in your Streamlit app or externally
   - Must be publicly accessible

3. **Set Environment Variables on Render**
   - `GOOGLE_CLIENT_ID`
   - `GOOGLE_CLIENT_SECRET`
   - `GOOGLE_REDIRECT_URI` (must match your backend URL exactly)

4. **Test with Real User**
   - Use a Google account that's NOT in test users list
   - Verify OAuth flow works
   - Verify credentials are stored
   - Verify Gmail/Calendar features work

## Verification Status

After completing the checklist:

- **App Status**: [ ] Testing [ ] In Production ✅
- **Can Any User Connect?**: [ ] Yes ✅ [ ] No
- **Verification Status**: [ ] Verified [ ] Unverified (users see warning)
- **All Tests Pass**: [ ] Yes ✅ [ ] No

## Next Steps

- [ ] Monitor OAuth usage in Google Cloud Console
- [ ] Collect user feedback
- [ ] Submit for verification (optional, recommended)
- [ ] Set up monitoring and alerts
- [ ] Document common issues and solutions

---

**Remember**: The app MUST be published (not in Testing mode) for any user to connect their Google account!

