# Production OAuth Setup - For Public Users

This guide explains how to configure Google OAuth so **any user** can connect their Google account to your production app.

## ⚠️ Critical Requirements

For average users to connect their Google accounts, you **MUST**:

1. ✅ **Publish your OAuth consent screen** (not just in testing mode)
2. ✅ **Add required app information** (privacy policy, terms of service)
3. ✅ **Configure production redirect URIs**
4. ✅ **Set environment variables on Render**
5. ✅ **Verify your app** (recommended, but not required immediately)

## Step-by-Step Production Setup

### Step 1: Complete OAuth Consent Screen Configuration

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Select your project
3. Navigate to **APIs & Services** → **OAuth consent screen**

#### 1.1 App Information (REQUIRED)

Fill in **all required fields**:

- **App name**: `Canvas MPC` (or your app name)
- **User support email**: Your support email
- **App logo**: (Recommended) Upload a 120x120px logo
- **Application home page**: `https://your-app.streamlit.app`
- **Application privacy policy link**: **REQUIRED** - Link to your privacy policy
  - Example: `https://your-app.streamlit.app/privacy`
  - You can host this as a Streamlit page or external site
- **Application terms of service link**: **REQUIRED** - Link to your terms
  - Example: `https://your-app.streamlit.app/terms`
- **Authorized domains**: Add domains like:
  - `streamlit.app`
  - `onrender.com`
  - Your custom domain if you have one
- **Developer contact information**: Your email

#### 1.2 Scopes (REQUIRED)

Add these scopes:
- `https://www.googleapis.com/auth/gmail.modify`
- `https://www.googleapis.com/auth/calendar`
- `https://www.googleapis.com/auth/userinfo.email`

#### 1.3 Test Users (OPTIONAL - Only for Testing)

- Add test users only if you want to test before publishing
- **Once published, you can remove test users** - they're not needed
- Test users are only required when app is in "Testing" mode

### Step 2: PUBLISH YOUR APP ⚠️ CRITICAL

**This is the most important step!**

1. On the OAuth consent screen page, look at the top
2. You'll see one of these statuses:
   - **"Testing"** - Only test users can connect ❌
   - **"In production"** - Any user can connect ✅

3. If it shows "Testing":
   - Scroll down and click **"PUBLISH APP"** button
   - Read the warning carefully
   - Click **"Confirm"** to publish
   - Your app status will change to "In production"

4. **What happens after publishing:**
   - Any Google user can now connect their account
   - No test user list needed
   - Users may see "Unverified app" warning (if not verified)
   - Users can still proceed by clicking "Advanced" → "Go to [Your App]"

### Step 3: OAuth Verification (Recommended)

For sensitive scopes (Gmail, Calendar), Google recommends verification:

1. **Why verify?**
   - Removes "Unverified app" warning for users
   - Builds trust with users
   - Required for some sensitive scopes

2. **When to verify:**
   - Before launch (ideal)
   - After publishing (you can verify later)

3. **Verification process:**
   - Click **"Submit for verification"** in the OAuth consent screen
   - Fill out the OAuth verification form:
     - App description
     - Video demonstration (screencast)
     - Privacy policy URL (required)
     - Terms of service URL (required)
     - Scopes justification
   - Submit for review
   - Verification typically takes 4-6 weeks

4. **Testing without verification:**
   - You can publish and use the app without verification
   - Users will see an "Unverified app" warning
   - They can click "Advanced" → "Go to [Your App] (unsafe)" to proceed
   - This is acceptable for MVP/testing phase

### Step 4: Configure OAuth Credentials

1. Go to **APIs & Services** → **Credentials**
2. Click on your OAuth 2.0 Client ID
3. **Authorized JavaScript origins**:
   - `https://your-backend.onrender.com`
   - `http://localhost:8000` (for local development)

4. **Authorized redirect URIs**:
   - `https://your-backend.onrender.com/auth/google/callback` (production)
   - `http://localhost:8000/auth/google/callback` (local development)

5. Click **Save**

### Step 5: Set Environment Variables on Render

1. Go to your Render dashboard
2. Select your backend service
3. Go to **Environment** tab
4. Add/update these variables:

```bash
# Google OAuth (REQUIRED)
GOOGLE_CLIENT_ID=your_client_id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_client_secret
GOOGLE_REDIRECT_URI=https://your-actual-backend-url.onrender.com/auth/google/callback

# Backend URL
BASE_URL=https://your-actual-backend-url.onrender.com

# Frontend URLs
FRONTEND_URL=https://your-app.streamlit.app
STREAMLIT_URL=https://your-app.streamlit.app

# Optional: Control OAuth prompt behavior
# Use 'select_account' for better UX (default)
# Use 'consent' to force consent screen every time
GOOGLE_OAUTH_PROMPT=select_account
```

5. **Important**: Replace `your-actual-backend-url.onrender.com` with your real Render URL
6. Click **Save Changes**
7. Render will automatically redeploy

### Step 6: Test with a Real User

1. Open your production app: `https://your-app.streamlit.app`
2. Go to Settings page
3. Enter a User ID (or use email)
4. Click "🔗 Connect Google Account"
5. You should be redirected to Google login
6. Sign in with any Google account (not just test users)
7. Grant permissions
8. You should be redirected back with success message

## Understanding App Status

### Testing Mode
- ✅ Good for: Development and testing
- ❌ Limitation: Only test users can connect
- 📝 Test users: Must be added manually in Google Cloud Console
- 🚫 Not suitable for: Production use with real users

### In Production Mode
- ✅ Good for: Production apps with real users
- ✅ Advantage: Any Google user can connect
- 📝 Test users: Not needed (can be removed)
- ⚠️ Warning: Users may see "Unverified app" warning if not verified
- ✅ Suitable for: Public-facing applications

## Privacy Policy & Terms of Service

Google requires these for production apps. You have options:

### Option 1: Create Simple Pages in Your App

Create these files in your frontend:

```python
# frontend/pages/2_Privacy_Policy.py
st.title("Privacy Policy")
st.markdown("""
# Privacy Policy

[Your privacy policy content]
""")
```

### Option 2: External Hosting

Host privacy policy and terms on:
- GitHub Pages
- Your website
- A free hosting service

### Option 3: Use a Generator

Use services like:
- [Privacy Policy Generator](https://www.privacypolicygenerator.info/)
- [Terms of Service Generator](https://www.termsofservicegenerator.net/)

## Common Issues & Solutions

### Issue: "Access blocked: This app's request is invalid"

**Cause**: App is still in Testing mode

**Solution**:
1. Go to OAuth consent screen
2. Click "PUBLISH APP"
3. Confirm publishing
4. Wait a few minutes for changes to propagate

### Issue: Users see "Unverified app" warning

**Cause**: App is not verified by Google

**Solution**:
1. This is normal for unverified apps
2. Users can still proceed: "Advanced" → "Go to [Your App]"
3. To remove warning: Submit for verification (takes 4-6 weeks)

### Issue: "redirect_uri_mismatch" error

**Cause**: Redirect URI doesn't match exactly

**Solution**:
1. Check `GOOGLE_REDIRECT_URI` in Render environment variables
2. Verify it matches exactly in Google Cloud Console
3. Include protocol (https://) and trailing path
4. Wait a few minutes after changes

### Issue: Only test users can connect

**Cause**: App is still in Testing mode

**Solution**:
1. Publish the app (Step 2 above)
2. Remove test user requirement
3. Wait for status to change to "In production"

## Security Best Practices

1. **Never commit secrets to git**
   - Use `.gitignore` for `.env` files
   - Use environment variables on Render
   - Rotate secrets if exposed

2. **Use HTTPS in production**
   - Render provides HTTPS automatically
   - Never use HTTP for OAuth in production

3. **Monitor OAuth usage**
   - Check Google Cloud Console for API usage
   - Set up alerts for unusual activity
   - Review OAuth consent screen regularly

4. **Handle token refresh**
   - Tokens expire and need refresh
   - Your code handles this automatically
   - Monitor for refresh failures

## Testing Checklist

Before launching to users:

- [ ] OAuth consent screen published (not in Testing mode)
- [ ] Privacy policy URL added and accessible
- [ ] Terms of service URL added and accessible
- [ ] Production redirect URI configured
- [ ] Environment variables set on Render
- [ ] Tested with a non-test-user Google account
- [ ] Verified OAuth flow works end-to-end
- [ ] Checked that credentials are stored in Supabase
- [ ] Tested Gmail integration
- [ ] Tested Calendar integration

## Next Steps

After setup:

1. **Monitor usage**: Check Google Cloud Console for API usage
2. **User feedback**: Collect feedback on OAuth experience
3. **Verification**: Consider submitting for verification
4. **Documentation**: Update user docs with connection steps
5. **Support**: Be ready to help users with connection issues

## Support

If users have issues:

1. Check Google Cloud Console for errors
2. Verify app is published (not in Testing)
3. Check Render logs for OAuth errors
4. Verify environment variables are set correctly
5. Test OAuth flow yourself

---

**Last Updated**: January 2025

