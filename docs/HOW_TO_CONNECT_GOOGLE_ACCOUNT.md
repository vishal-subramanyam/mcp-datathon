# How to Connect Your Google Account

Step-by-step guide on where to click and how to connect your Google account to Canvas MPC.

## 📍 Where to Find the "Connect Google Account" Button

### Step 1: Open the Settings Page

1. **Start your application:**
   - Open your browser
   - Go to `http://localhost:8501` (local) or your deployed URL
   - The Canvas MPC Assistant should be running

2. **Navigate to Settings:**
   - Look at the **sidebar** on the left
   - Find the **⚙️ Settings** page (gear icon)
   - Click on it to open the Settings page

   **OR**

   - You can also access it directly at: `http://localhost:8501/Settings`

### Step 2: Enter Your User ID

1. On the Settings page, you'll see a section called **"User Identification"**
2. Enter a **User ID** in the text box
   - You can use your email address: `your.email@example.com`
   - Or any unique identifier: `user123`, `john_doe`, etc.
3. Press **Enter** or click outside the box
4. You should see: `✅ Using user ID: your_user_id`

### Step 3: Find the Google Account Section

1. Scroll down on the Settings page
2. Look for the section titled: **"🔗 Google Account"**
3. You should see text that says: `🔗 Link your Google account to enable Gmail and Calendar features`

### Step 4: Click "Connect Google Account"

1. **Look for a blue button** that says: **"🔗 Connect Google Account"**
   - It's a prominent button in the middle of the Google Account section
   - The button should be clearly visible

2. **Click the button**
   - You'll be automatically redirected to Google's login page
   - Don't worry if the page seems to change - this is normal!

## 🔄 What Happens Next (The OAuth Flow)

### Step 5: Google Login Page

1. **You'll see Google's login page**
   - Enter your **Google account email**
   - Enter your **password**
   - Click **Next** or **Sign in**

2. **If you're already signed in:**
   - Google may skip this step
   - You'll go directly to the permissions screen

### Step 6: Grant Permissions

1. **Google will show you what permissions are requested:**
   - ✅ **Gmail**: Read, compose, send, and permanently delete emails
   - ✅ **Google Calendar**: View and manage your calendar events

2. **Review the permissions:**
   - Make sure you're comfortable with these permissions
   - These are necessary for the app to work with Gmail and Calendar

3. **Click "Allow" or "Continue"**
   - This grants permission to access your Google account

### Step 7: Return to Settings Page

1. **You'll be automatically redirected back**
   - Google will send you back to the Settings page
   - You should see: `✅ Google account linked successfully!`

2. **Success message:**
   - The page will show: `✅ Google account linked! Gmail and Calendar are ready to use.`
   - You now have two options:
     - **🔗 Re-link Google Account**: To connect a different account
     - **❌ Unlink Google Account**: To disconnect

### Step 8: Verify Connection

1. **Scroll down to "Current Credentials" section**
2. **Click "Check Calendar" button**
   - Should show: `✅ Calendar credentials found`

3. **Click "Check Gmail" button**
   - Should show: `✅ Gmail credentials found`

## ✅ You're Done!

Now you can use Gmail and Calendar features in the chat:

- **Ask about emails:** "Show me my recent emails"
- **Send emails:** "Send an email to john@example.com"
- **Calendar events:** "What's on my calendar today?"
- **Create events:** "Create a calendar event for tomorrow at 3 PM"

## 🎯 Visual Guide

```
┌─────────────────────────────────────────┐
│  Canvas MPC Assistant                   │
├─────────────────────────────────────────┤
│  Sidebar:                               │
│  ├─ 🎓 Main Chat                        │
│  ├─ ⚙️ Settings  ← CLICK HERE          │
│  ├─ 🔒 Privacy Policy                   │
│  └─ 📜 Terms of Service                 │
└─────────────────────────────────────────┘

          ↓

┌─────────────────────────────────────────┐
│  ⚙️ Settings                            │
├─────────────────────────────────────────┤
│  User Identification                    │
│  User ID: [your_email@example.com]     │
│  ✅ Using user ID: your_email@...      │
│                                         │
│  🔗 Google Account                      │
│  Link your Google account to enable... │
│                                         │
│  ┌───────────────────────────────────┐ │
│  │  🔗 Connect Google Account        │ │ ← CLICK THIS BUTTON
│  └───────────────────────────────────┘ │
│                                         │
│  ℹ️ What happens when I click?          │
│  [Expandable info box]                  │
└─────────────────────────────────────────┘

          ↓

┌─────────────────────────────────────────┐
│  Google Sign-In                         │
│  Enter your email: [________]           │
│  Enter password: [________]             │
│  [Sign in]                              │
└─────────────────────────────────────────┘

          ↓

┌─────────────────────────────────────────┐
│  Google Permissions                     │
│  Canvas MPC wants to:                   │
│  ✅ Access your Gmail                   │
│  ✅ Access your Calendar                │
│                                         │
│  [Allow] [Cancel]                       │
└─────────────────────────────────────────┘

          ↓

┌─────────────────────────────────────────┐
│  ⚙️ Settings                            │
│  ✅ Google account linked successfully! │
│  ✅ Google account linked! Gmail and    │
│     Calendar are ready to use.          │
│                                         │
│  [🔗 Re-link] [❌ Unlink]               │
└─────────────────────────────────────────┘
```

## 🐛 Troubleshooting

### Button Not Showing?

1. **Make sure you entered a User ID:**
   - The button only appears after you enter a User ID
   - Check that you see: `✅ Using user ID: ...`

2. **Check if already connected:**
   - If you see "✅ Google account linked!", you're already connected
   - You can click "Re-link" if you want to reconnect

3. **Refresh the page:**
   - Sometimes the page needs a refresh
   - Press `F5` or click the refresh button

### Redirect Not Working?

1. **Check backend is running:**
   - Make sure backend is running on port 8000
   - Check terminal for: `Application startup complete`

2. **Check environment variables:**
   - Verify `GOOGLE_CLIENT_ID` is set
   - Verify `GOOGLE_CLIENT_SECRET` is set
   - Verify `GOOGLE_REDIRECT_URI` is set correctly

3. **Check Google Cloud Console:**
   - Verify redirect URI is added: `http://localhost:8000/auth/google/callback`
   - Make sure it matches exactly (including `http://`)

### Error Messages?

1. **"Google OAuth not configured":**
   - Backend environment variables are missing
   - Check `.env` file or Render environment variables

2. **"redirect_uri_mismatch":**
   - Redirect URI doesn't match Google Cloud Console
   - Update Google Cloud Console with correct redirect URI

3. **"Access blocked":**
   - App might be in Testing mode
   - Publish the app in Google Cloud Console
   - Or add your email as a test user

## 📱 Quick Reference

**Where to click:**
1. Sidebar → ⚙️ Settings
2. Enter User ID
3. Scroll to "🔗 Google Account" section
4. Click "🔗 Connect Google Account" button

**What happens:**
1. Redirected to Google login
2. Sign in with Google
3. Grant permissions
4. Redirected back to Settings
5. See success message

**Time needed:**
- About 30 seconds to 1 minute

## 🎓 Video Tutorial (Text Version)

1. **Open app** → `http://localhost:8501`
2. **Click Settings** → Sidebar → ⚙️ Settings
3. **Enter User ID** → Type your email or ID
4. **Find Google section** → Scroll to "🔗 Google Account"
5. **Click button** → "🔗 Connect Google Account"
6. **Sign in Google** → Enter email and password
7. **Allow permissions** → Click "Allow"
8. **See success** → "✅ Google account linked!"
9. **Start using** → Ask about emails or calendar!

---

**Need help?** Check the troubleshooting section or review the Google OAuth setup guide.

